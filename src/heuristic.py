"""Criterio de ordenacion de candidatos. Sustituye esta funcion para experimentos."""

from __future__ import annotations

from src.cvrp import Instance


def heuristic(
    instance: Instance,
    solution: list[list[int]],
    unassigned: list[int],
    route_index: int,
    customer: int,
    position: int,
) -> float:
    """Valor mas bajo = mejor candidato."""
    route = solution[route_index]
    depot = instance.depot
    prev_node = depot if position == 0 else route[position - 1]
    next_node = depot if position == len(route) else route[position]
    return (
        instance.distance_matrix[prev_node][customer]
        + instance.distance_matrix[customer][next_node]
        - instance.distance_matrix[prev_node][next_node]
    )
