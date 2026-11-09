# Reproducing the benchmark

The original report and notebook use the same directed graph, list frontiers, tie-breaking rule, seeds, sampling budgets, and measurement protocol. This release moves their reusable implementation into a Python package. Install from the repository root with Python 3.12.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m patent_search --output runs/reproduction
python scripts/verify_reproduction.py runs/reproduction
```

The CLI's default output is `runs/reproduction`. Choose a new output directory for each run. Its CSVs and plots become visible after the experiment completes. It validates every main route and compares all 50 UCS costs with an independent BFS calculation.

## Dataset cache and offline use

Use a local uncompressed or gzip SNAP edge list.

```bash
python -m patent_search --dataset /path/to/cit-Patents.txt.gz --output runs/from-local
python scripts/verify_reproduction.py runs/from-local
```

The default cache is `data/`. The runner downloads the official gzip only when neither a usable text file nor a nonempty local archive is present. If the archive is corrupt, replace it with a fresh copy before retrying. The two files require roughly 350 MiB of disk space combined. Check the hashes against the recorded dataset manifest if counts or pairs differ. Preserve line order, since sorting or converting the graph can change the seeded samples. [Official download](https://snap.stanford.edu/data/cit-Patents.txt.gz) · [SHA-256 manifest](../results/recorded/provenance.json)

## Notebook execution

```bash
python -m pip install -r requirements-notebook.txt
jupyter lab
```

Open `notebooks/ucs_vs_gbfs.ipynb` with the Python 3 kernel from the same environment. The full benchmark runs when executing the reproduction cell. By default it uses the repository's `data/` cache. Set `PATENT_DATASET` in the environment to an absolute local file path for offline execution. Fresh notebook runs write to a new child of `runs/` each time.

For a headless run using a fresh in-process Jupyter kernel:

```bash
python scripts/execute_notebook.py --dataset /path/to/cit-Patents.txt --output runs/executed_notebook.ipynb
```

## Output files

| File | Meaning |
| --- | --- |
| `ucs_results.csv`, `gbfs_results.csv` | Complete per-pair measurements and routes |
| `ucs_summary.csv`, `gbfs_summary.csv`, `comparison.csv` | Aggregated metrics |
| `pair_optimality.csv` | Joined records and GBFS excess hops |
| `depth_sensitivity.csv`, `depth_pair_results.csv` | Counts and mean results per depth, plus all evaluated depth pairs |
| `expansion_analysis.csv`, `expansion_orders.csv` | First-pair summary and selected IDs in order |
| `time_taken.csv` | Stage wall times |
| `report_data.json` | Archived notebook results and environment, in the recorded directory |
| `run_metadata.json` | Graph statistics, settings, and environment for a fresh run |
| `figures/` | Recorded figures or fresh plots according to the parent directory |

The legacy column name `peak_memory_kb` is retained for compatibility with the archived CSVs. Its values are KiB. Paths in CSVs are lists of integer patent IDs. Empty depth samples have blank metrics. The archived expansion-order CSV represents one numeric column as floats because it pads the shorter sequence with empty rows. The fresh export writes nullable integer IDs.

## What should match

Given the same file bytes and recorded configuration, expect identical graph counts, main and depth pair identities, paths, costs, validity, selections, frontier counts, depth sample attempts, and expansion order. The verification script checks these values against the recorded snapshot. Per-pair timing and traced allocation may vary with hardware, Python, system load, and implementation details. Stage elapsed time also includes surrounding setup and chart work, whose overhead differs between the original notebook and the package.

Tests and recorded-asset checksum checks run without internet access or the large dataset. The full verification uses the dataset and is separate from the CI test job.
