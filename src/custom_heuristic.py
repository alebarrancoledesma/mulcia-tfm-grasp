"""Puntuación de inserción para este experimento, sin llamada a la API ni ajuste empírico.
Lower is better. Distance increment remains dominant; relative demand rewards
serving larger customers early, and endpoint proximity promotes compact routes.
Pure function with the same contract as heuristic.py, for valid CVRP inputs.
"""

from src.cvrp import Instance


def heuristic(
    instance: Instance,
    solution: list[list[int]],
    unassigned: list[int],
    route_index: int,
    customer: int,
    position: int,
) -> float:
    route = solution[route_index]
    matrix = instance.distance_matrix
    prev_node = instance.depot if position == 0 else route[position - 1]
    next_node = instance.depot if position == len(route) else route[position]
    left = matrix[prev_node][customer]
    right = matrix[customer][next_node]
    delta = left + right - matrix[prev_node][next_node]
    demand_fraction = instance.demands[customer] / max(1, instance.capacity)
    proximity = min(left, right)
    return delta / (1.0 + demand_fraction) + 0.2 * proximity
