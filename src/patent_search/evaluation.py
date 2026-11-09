"""Sequential measurement protocol and tabular evaluation."""

import statistics
import time
import tracemalloc
from collections.abc import Callable, Sequence

import pandas as pd

from .sampling import Pair
from .search import Graph, SearchResult, is_valid_path, path_cost

Search = Callable[[Graph, int, int], SearchResult]
TIMED_REPEATS = 5


def run_algorithm(search: Search, graph: Graph, pairs: Sequence[Pair]) -> pd.DataFrame:
    """Warm up once, time five searches, then measure peak traced allocation."""
    if tracemalloc.is_tracing():
        raise RuntimeError("Stop external tracemalloc tracing before benchmarking")

    rows = []
    for number, (start, goal) in enumerate(pairs, start=1):
        search(graph, start, goal)
        samples = []
        for _ in range(TIMED_REPEATS):
            tick = time.perf_counter()
            path, expanded, max_frontier = search(graph, start, goal)
            samples.append(time.perf_counter() - tick)
        seconds = statistics.median(samples)

        tracemalloc.start()
        try:
            measured = search(graph, start, goal)
            _, peak_bytes = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        if measured != (path, expanded, max_frontier):
            raise RuntimeError(f"Search returned different results for pair {number}")

        hops = path_cost(path)
        rows.append({
            "pair": number,
            "source": start,
            "path": path,
            "goal": goal,
            "found": path is not None,
            "valid_path": is_valid_path(graph, path, start, goal),
            "path_cost": hops,
            "solution_depth": hops,
            "nodes_expanded": expanded,
            "max_frontier": max_frontier,
            "time_ms": seconds * 1000,
            "peak_memory_kb": peak_bytes / 1024,  # Historical field name, unit KiB.
        })
    return pd.DataFrame(rows)


def make_summary(table: pd.DataFrame, elapsed: float) -> pd.DataFrame:
    found = table.loc[table.found]
    metrics = {
        "Pairs tested": len(table),
        "Success rate (%)": round(100 * table.found.mean(), 1),
        "Valid paths among found paths (%)": round(100 * found.valid_path.mean(), 1),
        "Average path cost": round(table.path_cost.mean(), 2),
        "Average solution depth": round(table.solution_depth.mean(), 2),
        "Average nodes expanded": round(table.nodes_expanded.mean(), 1),
        "Average max frontier size": round(table.max_frontier.mean(), 1),
        "Average time per pair (ms)": round(table.time_ms.mean(), 3),
        "Average peak traced memory (KiB)": round(table.peak_memory_kb.mean(), 1),
        "Total time for all pairs (s)": round(elapsed, 3),
    }
    return pd.DataFrame({"Measure": metrics.keys(), "Value": metrics.values()})


def compare_pairs(ucs: pd.DataFrame, gbfs: pd.DataFrame) -> pd.DataFrame:
    """Join on the shared ordered pair identity and calculate excess GBFS hops."""
    comparison = ucs.merge(gbfs, on=["pair", "source", "goal"],
                           suffixes=("_ucs", "_gbfs"), validate="one_to_one")
    if len(comparison) != len(ucs) or len(comparison) != len(gbfs):
        raise ValueError("UCS and GBFS benchmark pairs differ")
    comparison["extra_hops_gbfs"] = comparison.path_cost_gbfs - comparison.path_cost_ucs
    return comparison
