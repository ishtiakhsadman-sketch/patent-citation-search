"""Compare fresh outputs with the recorded snapshot, excluding machine-sensitive metrics."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

TABLES = [
    "ucs_results", "gbfs_results", "pair_optimality", "depth_sensitivity",
    "depth_pair_results", "expansion_analysis", "expansion_orders",
]
GRAPH_FIELDS = [
    "raw_rows", "self_citations", "duplicate_edges", "nodes", "edges", "citing_nodes",
    "dead_ends", "branching_factor", "max_branching", "smaller_number_pct",
]


def stable_columns(table: pd.DataFrame) -> pd.DataFrame:
    return table.loc[:, [not name.startswith(("time_ms", "peak_memory_kb")) for name in table.columns]]


def verify(fresh: Path, recorded: Path) -> dict:
    checked = {}
    for name in TABLES:
        before = stable_columns(pd.read_csv(recorded / f"{name}.csv"))
        after = stable_columns(pd.read_csv(fresh / f"{name}.csv"))
        try:
            assert_frame_equal(before, after, check_dtype=False, check_exact=True)
        except AssertionError as exc:
            raise ValueError(f"{name}.csv differs: {exc}") from exc
        checked[f"{name}.csv"] = {"rows": len(before), "columns_compared": len(before.columns)}

    baseline = json.loads((recorded / "report_data.json").read_text(encoding="utf-8"))
    observed = json.loads((fresh / "run_metadata.json").read_text(encoding="utf-8"))
    for field in GRAPH_FIELDS:
        if baseline[field] != observed[field]:
            raise ValueError(f"Graph metric {field} differs from the recorded value")
    return {
        "status": "pass", "tables": checked, "graph_fields": GRAPH_FIELDS,
        "independent_bfs_checks": len(pd.read_csv(fresh / "ucs_results.csv")),
        "excluded_measurements": ["runtime", "traced memory", "elapsed wall time"],
        "fresh_environment": observed["environment"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fresh", type=Path)
    parser.add_argument("--recorded", type=Path, default=Path("results/recorded"))
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.fresh, args.recorded), indent=2))
    except (OSError, ValueError) as exc:
        print(f"Verification failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
