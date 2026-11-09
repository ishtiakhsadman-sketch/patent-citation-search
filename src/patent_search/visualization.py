"""Plots for a fresh experiment, using measured tables as input."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .data import CitationGraph

COLORS = {"UCS": "#275578", "GBFS": "#b05a23"}


def _save(fig, path: Path) -> None:
    fig.savefig(path, dpi=160, bbox_inches="tight", metadata={"Software": "patent-citation-search"})
    plt.close(fig)


def plot_main(directory: Path, citation_graph: CitationGraph,
              ucs: pd.DataFrame, gbfs: pd.DataFrame) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    panels = (
        ("nodes_expanded", "Selected states"), ("max_frontier", "Maximum frontier"),
        ("time_ms", "Median search time (ms)"), ("peak_memory_kb", "Peak traced memory (KiB)"),
    )
    fig, axes = plt.subplots(2, 2, figsize=(8, 5), layout="constrained")
    for ax, (column, label) in zip(axes.flat, panels):
        ax.bar(["UCS", "GBFS"], [ucs[column].mean(), gbfs[column].mean()], color=list(COLORS.values()))
        ax.set_title(label)
        ax.set_ylim(bottom=0)
    fig.suptitle("Fresh run: mean across all benchmark pairs")
    _save(fig, directory / "performance.png")

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True, layout="constrained")
    for name, frame in [("UCS", ucs), ("GBFS", gbfs)]:
        for ax, column in zip(axes, ["nodes_expanded", "time_ms"]):
            ax.plot(frame.pair, frame[column], marker=".", label=name, color=COLORS[name])
    axes[0].set_ylabel("Selected states")
    axes[1].set_ylabel("Median time (ms)")
    axes[1].set_xlabel("Pair number")
    axes[0].legend()
    _save(fig, directory / "per_pair.png")

    fig, ax = plt.subplots(figsize=(6, 3), layout="constrained")
    depths = pd.DataFrame({
        "UCS": ucs.solution_depth.value_counts(),
        "GBFS": gbfs.solution_depth.value_counts(),
    }).fillna(0).sort_index()
    depths.plot.bar(ax=ax, color=list(COLORS.values()), rot=0)
    ax.set(xlabel="Route depth (hops)", ylabel="Pairs")
    _save(fig, directory / "solution_depth.png")

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), layout="constrained")
    outgoing = [len(targets) for targets in citation_graph.adjacency.values()]
    incoming = citation_graph.retained_edges.cited.value_counts()
    for ax, values, title in zip(axes, (outgoing, incoming), ("Outgoing citations", "Incoming citations")):
        ax.hist(values, bins=[i + 0.5 for i in range(31)], color=COLORS["UCS"])
        ax.set(title=title, xlabel="Degree (1–30 shown)", ylabel="Patents")
    _save(fig, directory / "degree_distributions.png")


def plot_depth(directory: Path, table: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 4), layout="constrained")
    for name in COLORS:
        ax.plot(table["exact depth"], table[f"{name} avg nodes"], marker="o",
                label=name, color=COLORS[name])
    ax.set_xticks(table["exact depth"])
    ax.set(xlabel="Exact shortest distance (hops)", ylabel="Mean selected states")
    ax.legend()
    _save(fig, directory / "depth_sensitivity.png")


def plot_expansion_order(directory: Path, orders: dict[str, list[int]],
                         paths: dict[str, list[int]], goal: int) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True, layout="constrained")
    for ax, (name, order) in zip(axes, orders.items()):
        steps = {node: step for step, node in enumerate(order, start=1)}
        route = paths[name]
        ax.scatter(list(steps.values()), order, s=20, color=COLORS[name], label="Selected")
        ax.scatter([steps[node] for node in route], route, marker="*", s=85, color="#2f7937", label="Route")
        ax.axhline(goal, linestyle="--", color="#777777", label="Goal")
        ax.axhline(order[0], linestyle=":", color="#333333", label="Source")
        ax.set(title=f"{name} ({len(order)} selected)", xlabel="Selection step")
    axes[0].set_ylabel("Patent number")
    axes[0].legend(fontsize=8)
    _save(fig, directory / "expansion_order.png")
