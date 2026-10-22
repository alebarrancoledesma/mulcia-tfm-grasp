"""Piezas de metaheuristica que no estan en ogatools (o que usamos en local)."""

from __future__ import annotations

import math
import random
import time
from abc import ABC, abstractmethod


class DeadlineExceeded(Exception):
    """Cooperative cancellation; a construction may be incomplete."""


def check_deadline(deadline: float | None) -> None:
    if deadline is not None and time.perf_counter() >= deadline:
        raise DeadlineExceeded


class RandomManager:
    rng = random.Random(1)

    @staticmethod
    def set_seed(seed: int) -> None:
        RandomManager.rng.seed(seed)

    @staticmethod
    def random() -> float:
        return RandomManager.rng.random()

    @staticmethod
    def integers(low: int, high: int) -> int:
        return RandomManager.rng.randrange(low, high)


def euclidean(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x1 - x2, y1 - y2)


def build_distance_matrix(coords: list[tuple[float, float]]) -> list[list[float]]:
    n = len(coords)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dist = euclidean(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
            matrix[i][j] = dist
            matrix[j][i] = dist
    return matrix


class Constructive(ABC):
    @abstractmethod
    def construct(self, instance: object) -> object:
        raise NotImplementedError


class Improvement(ABC):
    def improve_anytime(self, solution, deadline=None, on_improvement=None):
        check_deadline(deadline)
        self.improve(solution)
        if on_improvement is not None:
            on_improvement(solution)

    @abstractmethod
    def improve(self, solution: object) -> None:
        raise NotImplementedError


class Grasp:
    """GRASP minimo: construir -> mejorar -> guardar la mejor."""

    def __init__(
        self,
        constructive: Constructive,
        improvement: Improvement | None = None,
        iterations: int | None = 50,
        time_limit: float | None = None,
    ) -> None:
        self.constructive = constructive
        self.improvement = improvement
        self.iterations = iterations
        self.time_limit = time_limit
        if iterations is not None and iterations <= 0:
            raise ValueError("iterations must be positive")
        if time_limit is not None and (not math.isfinite(time_limit) or time_limit <= 0):
            raise ValueError("time_limit must be finite and positive")
        if iterations is None and time_limit is None:
            raise ValueError("a stopping limit is required")

    def execute(self, instance: object) -> object:
        best = None
        start = time.perf_counter()
        deadline = None if self.time_limit is None else start + self.time_limit
        self.metrics = dict(first_solution_time=None, first_solution_cost=None,
                            best_cost=None, time_to_best=None, elapsed=0.0,
                            iterations=0, feasible=False, routes=[], improvements=[])

        def record(solution):
            nonlocal best
            if not solution.is_feasible():
                return
            cost = solution.get_quality()
            if not math.isfinite(cost):
                return
            now = time.perf_counter() - start
            if self.metrics['first_solution_time'] is None:
                self.metrics.update(first_solution_time=now, first_solution_cost=cost)
            if best is None or cost < self.metrics['best_cost']:
                best = solution.copy_solution()
                self.metrics.update(best_cost=cost, time_to_best=now)
                self.metrics['improvements'].append(dict(time=now, cost=cost))

        while self.iterations is None or self.metrics['iterations'] < self.iterations:
            try:
                check_deadline(deadline)
                if deadline is None:
                    solution = self.constructive.construct(instance)
                else:
                    solution = self.constructive.construct(instance, deadline=deadline)
                self.metrics['iterations'] += 1
                record(solution)  # First feasible construction, BEFORE local search.
                if solution.is_feasible() and self.improvement is not None:
                    self.improvement.improve_anytime(solution, deadline, record)
                    record(solution)
            except DeadlineExceeded:
                break
        self.metrics.update(elapsed=time.perf_counter() - start,
                            feasible=best is not None,
                            routes=[] if best is None else [r[:] for r in best.routes])
        return best


def ranking_key(metrics: dict) -> tuple:
    """Feasible first, then final cost, then earliest best (ascending)."""
    if not metrics['feasible']:
        return (1, math.inf, math.inf)
    return (0, metrics['best_cost'], metrics['time_to_best'])
