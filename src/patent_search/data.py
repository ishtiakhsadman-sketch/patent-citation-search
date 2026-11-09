"""Dataset retrieval, parsing and graph construction in edge-file order."""

import gzip
import shutil
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

import pandas as pd

DATASET_URL = "https://snap.stanford.edu/data/cit-Patents.txt.gz"
DATASET_FILENAME = "cit-Patents.txt"
LOWEST_PATENT = 5_000_000


@dataclass
class CitationGraph:
    adjacency: dict[int, list[int]]
    retained_edges: pd.DataFrame
    stats: dict[str, int | float]


def ensure_dataset(cache: Path) -> Path:
    """Reuse the plain file or unpack a local archive, downloading on first use."""
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    plain = cache / DATASET_FILENAME
    if plain.is_file() and plain.stat().st_size:
        return plain

    archive = cache / f"{DATASET_FILENAME}.gz"
    if not archive.is_file() or not archive.stat().st_size:
        _transfer(archive, lambda: urlopen(DATASET_URL, timeout=60))
    try:
        _transfer(plain, lambda: gzip.open(archive, "rb"))
    except (OSError, EOFError) as exc:
        raise ValueError(f"Could not unpack {archive}. Check the gzip file.") from exc
    return plain


def _transfer(destination, open_source):
    """Publish only complete transfers and remove failed partial copies."""
    with NamedTemporaryFile(
        dir=destination.parent, prefix=destination.name + ".", suffix=".part",
        delete=False,
    ) as target:
        temporary = Path(target.name)
        try:
            with open_source() as source:
                shutil.copyfileobj(source, target)
            target.close()
            if not temporary.stat().st_size:
                raise ValueError(f"Empty download or extraction for {destination}")
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)


def load_edges(path: Path) -> pd.DataFrame:
    """Read the two integer endpoint columns from a SNAP text or gzip file."""
    edges = pd.read_csv(
        path, sep="\t", comment="#", header=None, dtype="int64",
    )
    if edges.shape[1] != 2 or edges.empty or edges.isna().any().any():
        raise ValueError("Expected a nonempty two-column citation edge list")
    edges.columns = ["citing", "cited"]
    return edges


def build_graph(edges: pd.DataFrame, threshold: int = LOWEST_PATENT) -> CitationGraph:
    """Retain unique directed edges with both endpoints at or above threshold."""
    different = edges.citing.ne(edges.cited)
    keep = different & edges.citing.ge(threshold) & edges.cited.ge(threshold)
    filtered = edges.loc[keep]
    unique = filtered.drop_duplicates()
    if unique.empty:
        raise ValueError(f"No citation edges remain at threshold {threshold}")

    adjacency: dict[int, list[int]] = {}
    for source, target in zip(unique.citing, unique.cited):
        adjacency.setdefault(source, []).append(target)
    nodes = len(set(adjacency).union(unique.cited))
    count = len(unique)
    stats = {
        "raw_rows": len(edges),
        "self_citations": len(edges) - int(different.sum()),
        "duplicate_edges": len(filtered) - count,
        "nodes": nodes,
        "edges": count,
        "citing_nodes": len(adjacency),
        "dead_ends": nodes - len(adjacency),
        "branching_factor": count / len(adjacency),
        "max_branching": max(map(len, adjacency.values())),
        "smaller_number_pct": float(unique.citing.gt(unique.cited).mean() * 100),
    }
    return CitationGraph(adjacency, unique, stats)
