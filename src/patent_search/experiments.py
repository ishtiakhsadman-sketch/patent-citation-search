"""Run the original main, depth-sensitivity and expansion-order experiments."""

import json
import platform
import random
import time
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from .data import LOWEST_PATENT, build_graph, ensure_dataset, load_edges
from .evaluation import TIMED_REPEATS, compare_pairs, make_summary, run_algorithm
from .sampling import bfs_distance, find_pairs, find_pairs_at_distance
from .search import Graph, greedy_search, heuristic, ucs_search
from .visualization import plot_depth, plot_expansion_order, plot_main

MAIN_PAIRS = 50
MAIN_SEED = 7
MAIN_MIN_HOPS = 8
MAIN_MAX_HOPS = 14
MAIN_BUDGET = 100_000
DEPTHS = (2, 4, 6, 8, 10, 12)
DEPTH_PAIRS = 20
DEPTH_SEED = 11
DEPTH_BUDGET = 2_000


def depth_sensitivity(graph: Graph) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = random.Random(DEPTH_SEED)
    rows = []
    details = []
    for hops in DEPTHS:
        pairs, attempts = find_pairs_at_distance(graph, DEPTH_PAIRS, hops, rng, DEPTH_BUDGET)
        row = {"exact depth": hops, "pairs": len(pairs), "source attempts": attempts}
        if pairs:
            ucs = run_algorithm(ucs_search, graph, pairs)
            gbfs = run_algorithm(greedy_search, graph, pairs)
            if not (ucs.path_cost.eq(hops).all() and ucs.valid_path.all() and gbfs.valid_path.all()):
                raise RuntimeError(f"Search validation failed at exact depth {hops}")
            row.update({
                "UCS avg cost": round(ucs.path_cost.mean(), 2),
                "GBFS avg cost": round(gbfs.path_cost.mean(), 2),
                "GBFS optimal (%)": round(100 * gbfs.path_cost.eq(ucs.path_cost).mean(), 1),
                "UCS avg nodes": round(ucs.nodes_expanded.mean(), 1),
                "GBFS avg nodes": round(gbfs.nodes_expanded.mean(), 1),
            })
            joined = compare_pairs(ucs, gbfs)
            joined.insert(0, "exact_depth", hops)
            details.append(joined.drop(columns="extra_hops_gbfs"))
        rows.append(row)
    columns = [
        "exact depth", "pairs", "source attempts", "UCS avg cost", "GBFS avg cost",
        "GBFS optimal (%)", "UCS avg nodes", "GBFS avg nodes",
    ]
    return pd.DataFrame(rows, columns=columns), pd.concat(details, ignore_index=True) if details else pd.DataFrame()


def expansion_analysis(graph: Graph, start: int, goal: int, routes: dict[str, list[int]]):
    orders: dict[str, list[int]] = {"UCS": [], "GBFS": []}
    rows = []
    for name, search in [("UCS", ucs_search), ("GBFS", greedy_search)]:
        order = orders[name]
        route, _, _ = search(graph, start, goal, order_log=order)
        if route is None or route != routes[name]:
            raise RuntimeError(f"{name} expansion trace differs from benchmark route")
        h_values = [heuristic(node, goal) for node in order]
        rows.append({
            "algorithm": name,
            "selected states": len(order),
            "states outside final route": len(set(order).difference(route)),
            "heuristic increases": sum(b > a for a, b in zip(h_values, h_values[1:])),
            "goal selection step": order.index(goal) + 1,
        })
    return pd.DataFrame(rows), orders


def run_experiment(output_dir: Path, dataset: Path | None = None,
                   cache: Path = Path("data")) -> dict[str, pd.DataFrame]:
    """Run the original configuration and export it into a new directory."""
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"Choose a new output directory: {output_dir}")

    program_start = time.perf_counter()
    path = ensure_dataset(cache) if dataset is None else Path(dataset)
    raw = load_edges(path)
    load_time = time.perf_counter() - program_start
    tick = time.perf_counter()
    citation_graph = build_graph(raw, LOWEST_PATENT)
    graph = citation_graph.adjacency
    del raw
    processing_time = time.perf_counter() - tick

    tick = time.perf_counter()
    pairs = find_pairs(graph, MAIN_PAIRS, MAIN_MIN_HOPS, MAIN_MAX_HOPS, MAIN_SEED, MAIN_BUDGET)
    pair_time = time.perf_counter() - tick
    tick = time.perf_counter()
    ucs = run_algorithm(ucs_search, graph, pairs)
    ucs_time = time.perf_counter() - tick
    tick = time.perf_counter()
    gbfs = run_algorithm(greedy_search, graph, pairs)
    gbfs_time = time.perf_counter() - tick

    ucs_summary = make_summary(ucs, ucs_time)
    gbfs_summary = make_summary(gbfs, gbfs_time)
    comparison = ucs_summary.merge(gbfs_summary, on="Measure", suffixes=("_ucs", "_gbfs"))
    comparison = comparison.iloc[1:].rename(columns={"Value_ucs": "UCS", "Value_gbfs": "GBFS"})

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output_dir.parent, prefix=".experiment-") as stage:
        staging = Path(stage) / "results"
        figures = staging / "figures"
        plot_main(figures, citation_graph, ucs, gbfs)
        elapsed_main = time.perf_counter() - program_start
        timing = pd.DataFrame({
            "Step": ["Load dataset", "Data processing and graph build", "Choose pairs",
                     "Run UCS", "Run GBFS", "Elapsed through main charts"],
            "Seconds": [load_time, processing_time, pair_time, ucs_time, gbfs_time, elapsed_main],
        }).round(2)

        joined = compare_pairs(ucs, gbfs)
        if not (ucs.valid_path.all() and gbfs.valid_path.all()
                and joined.extra_hops_gbfs.ge(0).all()
                and all(row.path_cost == bfs_distance(graph, row.source, row.goal)
                        for row in ucs.itertuples())):
            raise RuntimeError("Main benchmark route or independent shortest-distance validation failed")

        depth_table, depth_results = depth_sensitivity(graph)
        start, goal = pairs[0]
        routes = {"UCS": ucs.iloc[0].path, "GBFS": gbfs.iloc[0].path}
        expansion, orders = expansion_analysis(graph, start, goal, routes)
        plot_depth(figures, depth_table)
        plot_expansion_order(figures, orders, routes, goal)

        tables = {
            "ucs_results": ucs, "gbfs_results": gbfs,
            "ucs_summary": ucs_summary, "gbfs_summary": gbfs_summary,
            "comparison": comparison, "time_taken": timing,
            "pair_optimality": joined, "depth_sensitivity": depth_table,
            "depth_pair_results": depth_results, "expansion_analysis": expansion,
            "expansion_orders": pd.DataFrame({name: pd.Series(order, dtype="Int64")
                                              for name, order in orders.items()}),
        }
        for name, frame in tables.items():
            frame.to_csv(staging / f"{name}.csv", index=False)
        metadata = {
            **citation_graph.stats,
            "environment": {"Python": platform.python_version(),
                            **{name: version(name) for name in ("numpy", "pandas", "matplotlib")},
                            "system": platform.system(), "architecture": platform.machine()},
            "settings": {
                "threshold": LOWEST_PATENT, "main_seed": MAIN_SEED, "main_pairs": MAIN_PAIRS,
                "main_hop_range": [MAIN_MIN_HOPS, MAIN_MAX_HOPS], "main_attempts": MAIN_BUDGET,
                "depth_seed": DEPTH_SEED, "depths": DEPTHS, "depth_pairs": DEPTH_PAIRS,
                "depth_attempts_per_distance": DEPTH_BUDGET, "timed_repeats": TIMED_REPEATS,
            },
        }
        (staging / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        staging.rename(output_dir)
    return tables
