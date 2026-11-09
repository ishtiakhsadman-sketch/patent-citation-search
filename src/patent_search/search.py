"""List-frontier graph searches with the original route and counter semantics."""

import math
from collections.abc import Callable, Mapping, Sequence

Graph = Mapping[int, Sequence[int]]
EdgeCost = Callable[[int, int], int | float]
SearchResult = tuple[list[int] | None, int, int]


def path_cost(path: Sequence[int] | None) -> int | None:
    """Return the number of unit-cost hops, or None for a missing route."""
    return len(path) - 1 if path else None


def is_valid_path(graph: Graph, path: Sequence[int] | None, start: int, goal: int) -> bool:
    """Check nonempty endpoints and each consecutive directed edge."""
    return bool(path) and path[0] == start and path[-1] == goal and all(
        target in graph.get(source, ()) for source, target in zip(path, path[1:])
    )


def heuristic(node: int, goal: int) -> int:
    """Rank a patent by its absolute identifier gap to the goal."""
    return abs(node - goal)


def ucs_search(
    graph: Graph, start: int, goal: int, edge_cost: EdgeCost | None = None,
    trace: bool = False, order_log: list[int] | None = None,
    path_log: dict[int, list[int]] | None = None,
) -> SearchResult:
    """Return route, selected-state count and maximum frontier size.

    The supplied edge costs must be finite and nonnegative. An invalid cost
    raises when its edge is examined. Each entry carries its own route so that
    a later cost improvement preserves the correct path to the selected goal.
    """
    frontier = [(0, start, [start])]
    best_cost = {start: 0}
    explored: set[int] = set()
    selected = 0
    max_frontier = 1

    while frontier:
        entry = min(frontier)
        frontier.remove(entry)
        cost, node, route = entry

        if node in explored:
            continue
        explored.add(node)
        selected += 1
        if order_log is not None:
            order_log.append(node)
        if path_log is not None:
            path_log[node] = route

        if node == goal:
            if trace:
                print(f"step {selected}: select {node} (g={cost}) -> goal, path={route}")
            return route, selected, max_frontier

        for neighbor in graph.get(node, ()):
            step = 1 if edge_cost is None else edge_cost(node, neighbor)
            if not isinstance(step, (int, float)) or step < 0 or (isinstance(step, float) and not math.isfinite(step)):
                raise ValueError("UCS requires finite nonnegative edge costs")
            new_cost = cost + step
            if isinstance(new_cost, float) and not math.isfinite(new_cost):
                raise ValueError("UCS accumulated path cost must be finite")
            if neighbor not in best_cost or new_cost < best_cost[neighbor]:
                best_cost[neighbor] = new_cost
                frontier.append((new_cost, neighbor, route + [neighbor]))

        if trace:
            print(f"step {selected}: select {node} (g={cost}) -> frontier",
                  sorted((key, state) for key, state, _ in frontier))
        max_frontier = max(max_frontier, len(frontier))

    return None, selected, max_frontier


def greedy_search(
    graph: Graph, start: int, goal: int, trace: bool = False,
    order_log: list[int] | None = None, path_log: dict[int, list[int]] | None = None,
) -> SearchResult:
    """Return the first GBFS route, selected-state count and maximum frontier."""
    frontier = [(heuristic(start, goal), start, [start])]
    seen = {start}
    selected = 0
    max_frontier = 1

    while frontier:
        entry = min(frontier)
        frontier.remove(entry)
        score, node, route = entry
        selected += 1
        if order_log is not None:
            order_log.append(node)
        if path_log is not None:
            path_log[node] = route

        if node == goal:
            if trace:
                print(f"step {selected}: select {node} (h={score}) -> goal, path={route}")
            return route, selected, max_frontier

        for neighbor in graph.get(node, ()):
            if neighbor not in seen:
                seen.add(neighbor)
                frontier.append((heuristic(neighbor, goal), neighbor, route + [neighbor]))

        if trace:
            print(f"step {selected}: select {node} (h={score}) -> frontier",
                  sorted((key, state) for key, state, _ in frontier))
        max_frontier = max(max_frontier, len(frontier))

    return None, selected, max_frontier
