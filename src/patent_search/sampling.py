"""Reachable pair sampling in original BFS discovery and source-file order."""

import random
from collections import deque

from .search import Graph

Pair = tuple[int, int]


def _sample(graph: Graph, count: int, min_hops: int, max_hops: int,
            rng: random.Random, budget: int) -> tuple[list[Pair], int]:
    if count < 1 or budget < 1 or not 0 <= min_hops <= max_hops:
        raise ValueError("Expected positive count and budget and an ordered hop range")
    starts = list(graph)
    if not starts:
        raise ValueError("Cannot sample pairs from an empty graph")
    pairs: list[Pair] = []
    seen: set[Pair] = set()
    for attempt in range(1, budget + 1):
        start = rng.choice(starts)
        distance = {start: 0}
        queue = deque([start])
        candidates = [start] if min_hops == 0 else []
        while queue:
            node = queue.popleft()
            depth = distance[node]
            if depth == max_hops:
                continue
            for neighbor in graph.get(node, ()):
                if neighbor not in distance:
                    distance[neighbor] = depth + 1
                    queue.append(neighbor)
                    if depth + 1 >= min_hops:
                        candidates.append(neighbor)
        if candidates:
            pair = (start, rng.choice(candidates))
            if pair not in seen:
                pairs.append(pair)
                seen.add(pair)
        if len(pairs) == count:
            return pairs, attempt
    return pairs, budget


def find_pairs(graph: Graph, count: int = 50, min_hops: int = 8,
               max_hops: int = 14, seed: int = 7, max_attempts: int = 100_000) -> list[Pair]:
    """Sample distinct reachable ordered pairs or report a budget shortfall."""
    pairs, attempts = _sample(graph, count, min_hops, max_hops, random.Random(seed), max_attempts)
    if len(pairs) != count:
        raise RuntimeError(f"Only {len(pairs)} distinct pairs found after {attempts} attempts")
    return pairs


def find_pairs_at_distance(graph: Graph, count: int, hops: int,
                           rng: random.Random, max_attempts: int = 2_000) -> tuple[list[Pair], int]:
    """Sample one exact distance, retaining partial and empty samples."""
    return _sample(graph, count, hops, hops, rng, max_attempts)


def bfs_distance(graph: Graph, start: int, goal: int) -> int | None:
    """Independent unit-hop shortest distance used to check UCS routes."""
    queue = deque([(start, 0)])
    seen = {start}
    while queue:
        node, depth = queue.popleft()
        if node == goal:
            return depth
        for neighbor in graph.get(node, ()):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, depth + 1))
    return None
