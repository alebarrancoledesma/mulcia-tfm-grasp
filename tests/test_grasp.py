import contextlib
import copy
import hashlib
import io
import math
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from src.__main__ import build_parser
from src.cvrp import Instance, Solution, read_vrp
from src.custom_heuristic import heuristic as custom
from src.heuristic import heuristic as basic
from src.operators import GraspPfi, TwoOpt
from src.utils import DeadlineExceeded, Grasp, RandomManager, ranking_key

ROOT = Path(__file__).resolve().parents[1]


class Contracts(unittest.TestCase):
    def test_basic_hash_and_regression(self):
        self.assertEqual(hashlib.sha256((ROOT / 'src/heuristic.py').read_bytes()).hexdigest(),
                         'fb28997aaf3b251e947ac0b57cd00f7a9341d607af686e5282d1447ab579217a')
        instance = read_vrp(str(ROOT / 'src/input/E-n22-k4.vrp'))
        RandomManager.set_seed(7)
        result = Grasp(GraspPfi(), TwoOpt(), iterations=5).execute(instance)
        RandomManager.set_seed(7)
        repeated = Grasp(GraspPfi(), TwoOpt(), iterations=5).execute(instance)
        self.assertEqual(result.routes, repeated.routes)
        self.assertEqual(result.get_quality(), repeated.get_quality())
        self.assertTrue(result.is_feasible())

    def test_empty_route_uses_same_keyword_scoring_and_rng(self):
        instance = Instance('seeds', [(0, 0), (1, 0), (2, 0), (9, 0)], [0, 1, 1, 1], 2, alpha=0)
        before = copy.deepcopy(instance.__dict__)
        calls = []
        def score(*, instance, solution, unassigned, route_index, customer, position):
            calls.append(copy.deepcopy((solution, unassigned, route_index, customer, position)))
            return customer
        with patch.object(RandomManager, 'integers', return_value=0) as rng:
            result = GraspPfi(score).construct(instance)
        self.assertEqual(rng.call_count, 3)
        self.assertEqual(calls[:3], [([[]], [1, 2, 3], 0, c, 0) for c in (1, 2, 3)])
        self.assertEqual(calls[3:7], [([[1]], [2, 3], 0, c, p) for c in (2, 3) for p in (0, 1)])
        self.assertEqual(calls[-1], ([[2, 1], []], [3], 1, 3, 0))
        self.assertTrue(result.is_feasible())
        self.assertEqual(before, instance.__dict__)

    def test_alpha_endpoints_select_seed(self):
        instance = Instance('seeds', [(0, 0), (1, 0), (2, 0), (9, 0)], [0, 1, 1, 1], 1, alpha=0)
        with patch.object(RandomManager, 'integers', return_value=0) as rng:
            result = GraspPfi(lambda **kw: kw['customer']).construct(instance)
        self.assertEqual(result.routes[0], [1])
        self.assertEqual(rng.call_args_list[0].args, (0, 1))
        instance.alpha = 1
        for choice in range(3):
            with patch.object(RandomManager, 'integers', side_effect=[choice, 0, 0]) as rng:
                result = GraspPfi(lambda **kw: kw['customer']).construct(instance)
            self.assertEqual(rng.call_args_list[0].args, (0, 3))
            self.assertEqual(result.routes[0], [choice + 1])
            self.assertTrue(result.is_feasible())

    def test_invalid_seed_and_singleton_exact_capacity(self):
        instance = Instance('singleton', [(0, 0), (1, 0)], [0, 2], 2)
        self.assertEqual(GraspPfi().construct(instance).routes, [[1]])
        instance.capacity = 1
        with self.assertRaisesRegex(ValueError, 'no unassigned customer fits an empty route'):
            GraspPfi().construct(instance)

    def test_score_contract_and_injection(self):
        instance = Instance('arbitrary', [(0, 0), (1, 2), (3, 0)], [0, 2, 3], 5)
        routes, unassigned = [[1]], [2]
        before = copy.deepcopy((instance.__dict__, routes, unassigned))
        for score in (basic, custom):
            for pos in (0, 1):
                value = score(instance, routes, unassigned, 0, 2, pos)
                self.assertTrue(math.isfinite(value))
                self.assertEqual(value, score(instance, routes, unassigned, 0, 2, pos))
        self.assertEqual(before, (instance.__dict__, routes, unassigned))
        calls = []
        def spy(**kwargs):
            calls.append(kwargs['customer'])
            return custom(**kwargs)
        self.assertTrue(GraspPfi(spy).construct(instance).is_feasible())
        self.assertTrue(calls)
        with self.assertRaises(ValueError):
            GraspPfi(lambda **kw: math.nan).construct(instance)

    def test_deadline_discards_partial_construction(self):
        instance = Instance('small', [(0, 0), (1, 0), (2, 0)], [0, 1, 1], 2)
        # start, outer check, construction check, candidate check expires.
        with patch('src.utils.time.perf_counter', side_effect=[0, 0, 0, 2, 2]):
            grasp = Grasp(GraspPfi(), TwoOpt(), iterations=None, time_limit=1)
            self.assertIsNone(grasp.execute(instance))
        self.assertFalse(grasp.metrics['feasible'])
        self.assertEqual(grasp.metrics['routes'], [])
        self.assertIsNone(grasp.metrics['first_solution_cost'])

    def test_first_before_ls_and_interrupted_best_retained(self):
        instance = Instance('crossing', [(0, 0), (1, 1), (0, 1), (1, 0)], [0, 1, 1, 1], 3)
        initial = Solution(instance)
        initial.routes = [[1, 2, 3]]
        class Fixed:
            def construct(self, instance, deadline=None):
                return initial.copy_solution()
        class Interrupted(TwoOpt):
            def improve_anytime(self, solution, deadline=None, on_improvement=None):
                super().improve_anytime(solution, deadline, on_improvement)
                solution.routes.clear()  # incumbent must be an independent copy
                raise DeadlineExceeded
        grasp = Grasp(Fixed(), Interrupted(), iterations=1)
        result = grasp.execute(instance)
        m = grasp.metrics
        self.assertEqual(m['first_solution_cost'], initial.get_quality())
        self.assertLess(m['best_cost'], m['first_solution_cost'])
        self.assertTrue(result.is_feasible())
        self.assertEqual(result.get_quality(), m['best_cost'])
        self.assertGreaterEqual(m['time_to_best'], m['first_solution_time'])
        self.assertEqual(len(m['improvements']), 2)
        with self.assertRaises(DeadlineExceeded):
            TwoOpt().improve_anytime(initial, deadline=time.perf_counter() - 1)

    def test_short_real_deadline(self):
        instance = read_vrp(str(ROOT / 'src/input/E-n22-k4.vrp'))
        grasp = Grasp(GraspPfi(custom), TwoOpt(), iterations=None, time_limit=0.02)
        result = grasp.execute(instance)
        self.assertLess(grasp.metrics['elapsed'], 1)
        self.assertTrue(result is None or result.is_feasible())

    def test_invalid_flags_and_ranking(self):
        for args in (['--heuristic', 'bad'], ['--alpha', 'nan'], ['--alpha', '1.1'],
                     ['--time-limit', '0'], ['--time-limit', 'inf'],
                     ['--iterations', '-1'], ['--seed', 'x']):
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    build_parser().parse_args(args)
                self.assertEqual(error.exception.code, 2)
        self.assertLess(ranking_key(dict(feasible=True, best_cost=10, time_to_best=2)),
                        ranking_key(dict(feasible=False)))
        self.assertLess(ranking_key(dict(feasible=True, best_cost=10, time_to_best=2)),
                        ranking_key(dict(feasible=True, best_cost=10, time_to_best=3)))


if __name__ == '__main__':
    unittest.main()
