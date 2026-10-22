from __future__ import annotations

import math

from src.cvrp import Instance, Solution
from src.heuristic import heuristic
from src.utils import Constructive, Improvement, RandomManager, check_deadline


class GraspPfi(Constructive):
    """Priority-First Insertion con RCL (alpha)."""

    def __init__(self, score_fn=heuristic):
        self.score_fn = score_fn

    def construct(self, instance: Instance, deadline: float | None = None) -> Solution:
        solution = Solution(instance)
        unrouted = set(instance.customers())

        while unrouted:
            check_deadline(deadline)
            route = []
            load = 0

            while unrouted:
                candidates = []
                for customer in unrouted:
                    check_deadline(deadline)

                    if load + instance.demands[customer] > instance.capacity:
                        continue

                    best_position = 0
                    best_score = None
                    for position in range(len(route) + 1):
                        check_deadline(deadline)
                        score = self.score_fn(
                            instance=instance,
                            solution=solution.routes + [route],
                            unassigned=list(unrouted),
                            route_index=len(solution.routes),
                            customer=customer,
                            position=position,
                        )
                        if not math.isfinite(score):
                            raise ValueError("score_fn must return a finite score")
                        if best_score is None or score < best_score:
                            best_score = score
                            best_position = position

                    candidates.append((best_score, customer, best_position))

                if not candidates:
                    if not route:
                        raise ValueError("invalid instance: no unassigned customer fits an empty route")
                    break

                customer, position = select_rcl_candidate(candidates, instance.alpha)
                route.insert(position, customer)
                load += instance.demands[customer]
                unrouted.remove(customer)

            solution.routes.append(route)

        return solution


def select_rcl_candidate(
    candidates: list[tuple[float, int, int]],
    alpha: float,
) -> tuple[int, int]:

    """RCL: ordena por score (heuristic) y elige uno entre los mejores."""
    ordered = sorted(candidates, key=lambda candidate: candidate[0])
    min_cost = ordered[0][0]
    max_cost = ordered[-1][0]
    threshold = min_cost + alpha * (max_cost - min_cost)
    rcl = [candidate for candidate in ordered if candidate[0] <= threshold]
    _, customer, position = rcl[RandomManager.integers(0, len(rcl))]
    return customer, position


class TwoOpt(Improvement):
    """2-opt intra-ruta, first improvement."""

    def improve(self, solution: Solution) -> None:
        self.improve_anytime(solution)

    def improve_anytime(self, solution, deadline=None, on_improvement=None):
        improved = True
        while improved:
            improved = False
            for route in solution.routes:
                check_deadline(deadline)
                if _improve_route(solution.instance, route, deadline):
                    improved = True
                    if on_improvement is not None:
                        on_improvement(solution)


def _improve_route(instance: Instance, route: list[int], deadline: float | None = None) -> bool:
    matrix = instance.distance_matrix
    depot = instance.depot
    for i in range(len(route)):
        for j in range(i + 1, len(route)):
            check_deadline(deadline)
            prev_node = depot if i == 0 else route[i - 1]
            next_node = depot if j == len(route) - 1 else route[j + 1]
            delta = (
                matrix[prev_node][route[j]]
                + matrix[route[i]][next_node]
                - matrix[prev_node][route[i]]
                - matrix[route[j]][next_node]
            )
            if delta < -1e-9:
                route[i : j + 1] = reversed(route[i : j + 1])
                return True
    return False
