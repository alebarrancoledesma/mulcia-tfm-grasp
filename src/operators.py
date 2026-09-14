from __future__ import annotations

from src.cvrp import Instance, Solution
from src.heuristic import heuristic
from src.utils import Constructive, Improvement, RandomManager


class GraspPfi(Constructive):
    """Priority-First Insertion con RCL (alpha)."""

    def construct(self, instance: Instance) -> Solution:
        solution = Solution(instance)
        unrouted = set(instance.customers())

        while unrouted:
            seed = max(unrouted, key=lambda c: instance.distance_matrix[instance.depot][c])
            route = [seed]
            load = instance.demands[seed]
            unrouted.remove(seed)

            while unrouted:
                candidates = []
                for customer in unrouted:

                    if load + instance.demands[customer] > instance.capacity:
                        continue

                    position, _cost = _best_insertion(instance, route, customer)

                    score = heuristic(
                        instance=instance,
                        solution=solution.routes + [route],
                        unassigned=list(unrouted),
                        route_index=len(solution.routes),
                        customer=customer,
                        position=position,
                    )

                    candidates.append((score, customer, position))

                if not candidates:
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
        improved = True
        while improved:
            improved = False
            for route in solution.routes:
                if _improve_route(solution.instance, route):
                    improved = True


def _best_insertion(instance: Instance, route: list[int], customer: int) -> tuple[int, float]:
    best_pos = 0
    best_cost = _insertion_cost(instance, route, customer, 0)
    for pos in range(1, len(route) + 1):
        cost = _insertion_cost(instance, route, customer, pos)
        if cost < best_cost:
            best_pos = pos
            best_cost = cost
    return best_pos, best_cost


def _insertion_cost(instance: Instance, route: list[int], customer: int, pos: int) -> float:
    depot = instance.depot
    matrix = instance.distance_matrix
    prev_node = depot if pos == 0 else route[pos - 1]
    next_node = depot if pos == len(route) else route[pos]
    return matrix[prev_node][customer] + matrix[customer][next_node] - matrix[prev_node][next_node]


def _improve_route(instance: Instance, route: list[int]) -> bool:
    matrix = instance.distance_matrix
    depot = instance.depot
    for i in range(len(route)):
        for j in range(i + 1, len(route)):
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
