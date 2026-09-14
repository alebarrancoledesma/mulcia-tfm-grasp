from __future__ import annotations

from src.utils import build_distance_matrix


class Instance:
    def __init__(
        self,
        name: str,
        coords: list[tuple[float, float]],
        demands: list[int],
        capacity: int,
        depot: int = 0,
        alpha: float = 0.3,
    ) -> None:
        self.name = name
        self.coords = coords
        self.demands = demands
        self.capacity = capacity
        self.depot = depot
        self.alpha = alpha
        self.n = len(coords)
        self.distance_matrix = build_distance_matrix(coords)

    def customers(self) -> list[int]:
        return [i for i in range(self.n) if i != self.depot]


class Solution:
    def __init__(self, instance: Instance) -> None:
        self.instance = instance
        self.routes: list[list[int]] = []

    def route_load(self, route: list[int]) -> int:
        return sum(self.instance.demands[node] for node in route)

    def route_distance(self, route: list[int]) -> float:
        if not route:
            return 0.0
        depot = self.instance.depot
        matrix = self.instance.distance_matrix
        dist = matrix[depot][route[0]]
        for i in range(len(route) - 1):
            dist += matrix[route[i]][route[i + 1]]
        dist += matrix[route[-1]][depot]
        return dist

    def get_quality(self) -> float:
        return sum(self.route_distance(route) for route in self.routes)

    def is_better(self, other: "Solution") -> bool:
        return self.get_quality() < other.get_quality()

    def is_feasible(self) -> bool:
        visited: list[int] = []
        for route in self.routes:
            if self.route_load(route) > self.instance.capacity:
                return False
            visited.extend(route)
        return sorted(visited) == self.instance.customers()

    def copy_solution(self) -> "Solution":
        cloned = Solution(self.instance)
        cloned.routes = [route[:] for route in self.routes]
        return cloned

    def __str__(self) -> str:
        lines = [f"quality={self.get_quality():.2f}  feasible={self.is_feasible()}"]
        for idx, route in enumerate(self.routes, start=1):
            path = "-".join(["0"] + [str(n) for n in route] + ["0"])
            lines.append(
                f"  ruta {idx}: {path}  load={self.route_load(route)}  "
                f"dist={self.route_distance(route):.2f}"
            )
        return "\n".join(lines)


def read_vrp(path: str, alpha: float = 0.3) -> Instance:
    name = "instance"
    dimension = 0
    capacity = 0
    coords: dict[int, tuple[float, float]] = {}
    demands: dict[int, int] = {}
    depot = 1
    section = None

    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line == "EOF":
                continue
            if line.startswith("NAME"):
                name = line.split(":")[1].strip()
            elif line.startswith("DIMENSION"):
                dimension = int(line.split(":")[1])
            elif line.startswith("CAPACITY"):
                capacity = int(line.split(":")[1])
            elif line.startswith("NODE_COORD_SECTION"):
                section = "coords"
            elif line.startswith("DEMAND_SECTION"):
                section = "demands"
            elif line.startswith("DEPOT_SECTION"):
                section = "depot"
            elif section == "coords":
                parts = line.split()
                coords[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif section == "demands":
                parts = line.split()
                demands[int(parts[0])] = int(parts[1])
            elif section == "depot":
                value = int(line.split()[0])
                if value > 0:
                    depot = value

    nodes = list(range(1, dimension + 1))
    coord_list = [coords[i] for i in nodes]
    demand_list = [demands[i] for i in nodes]
    return Instance(
        name=name,
        coords=coord_list,
        demands=demand_list,
        capacity=capacity,
        depot=nodes.index(depot),
        alpha=alpha,
    )
