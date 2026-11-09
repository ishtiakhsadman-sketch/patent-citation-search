"""Command-line entry point for the full benchmark."""

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reproduce the UCS and GBFS patent citation experiments.")
    parser.add_argument("--dataset", type=Path, help="Local SNAP edge list (.txt or .txt.gz)")
    parser.add_argument("--cache", type=Path, default=Path("data"), help="Dataset cache (default: data)")
    parser.add_argument("--output", type=Path, default=Path("runs/reproduction"),
                        help="New output directory (default: runs/reproduction)")
    args = parser.parse_args(argv)

    import matplotlib
    matplotlib.use("Agg")
    from .experiments import run_experiment

    try:
        tables = run_experiment(args.output, dataset=args.dataset, cache=args.cache)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"Experiment failed: {exc}", file=sys.stderr)
        return 1
    print(tables["comparison"].to_string(index=False))
    print(f"Saved fresh measurements and figures to {args.output}")
    return 0
