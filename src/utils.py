"""Piezas de metaheuristica que no estan en ogatools (o que usamos en local)."""

from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod


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
    @abstractmethod
    def improve(self, solution: object) -> None:
        raise NotImplementedError


class Grasp:
    """GRASP minimo: construir -> mejorar -> guardar la mejor."""

    def __init__(
        self,
        constructive: Constructive,
        improvement: Improvement | None = None,
        iterations: int = 50,
    ) -> None:
        self.constructive = constructive
        self.improvement = improvement
        self.iterations = iterations

    def execute(self, instance: object) -> object:
        best = None
        for _ in range(self.iterations):
            solution = self.constructive.construct(instance)
            if self.improvement is not None:
                self.improvement.improve(solution)
            if best is None or solution.is_better(best):
                best = solution.copy_solution()
        return best
