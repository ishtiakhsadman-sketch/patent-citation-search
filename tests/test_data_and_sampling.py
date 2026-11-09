import gzip
import io
import random
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from patent_search.data import build_graph, ensure_dataset, load_edges
from patent_search.sampling import bfs_distance, find_pairs, find_pairs_at_distance


class DatasetTests(unittest.TestCase):
    def test_preserves_insertion_order_direction_and_cited_only_nodes(self):
        raw = pd.DataFrame({"citing": [12, 12, 13, 12, 14, 11],
                            "cited": [11, 10, 13, 11, 9, 10]})
        result = build_graph(raw, threshold=10)
        self.assertEqual(list(result.adjacency.items()), [(12, [11, 10]), (11, [10])])
        self.assertEqual(result.stats["raw_rows"], 6)
        self.assertEqual(result.stats["self_citations"], 1)
        self.assertEqual(result.stats["duplicate_edges"], 1)
        self.assertEqual(result.stats["nodes"], 3)
        self.assertEqual(result.stats["dead_ends"], 1)

    def test_download_unpack_and_cache_with_stubbed_snap(self):
        data = b"# directed edges\n20\t19\n19\t18\n"
        with TemporaryDirectory() as directory:
            cache = Path(directory)
            with patch("patent_search.data.urlopen", return_value=io.BytesIO(gzip.compress(data))) as get:
                file = ensure_dataset(cache)
                self.assertEqual(file.read_bytes(), data)
                self.assertEqual(load_edges(file).values.tolist(), [[20, 19], [19, 18]])
                self.assertEqual(ensure_dataset(cache), file)
                get.assert_called_once()
                self.assertEqual(list(cache.glob("*.part")), [])

    def test_corrupt_archive_has_no_published_partial_text(self):
        with TemporaryDirectory() as directory:
            cache = Path(directory)
            (cache / "cit-Patents.txt.gz").write_bytes(b"not a gzip file")
            with self.assertRaisesRegex(ValueError, "Could not unpack"):
                ensure_dataset(cache)
            self.assertFalse((cache / "cit-Patents.txt").exists())
            self.assertEqual(list(cache.glob("*.part")), [])

    def test_rejects_wrong_number_of_columns(self):
        with TemporaryDirectory() as directory:
            file = Path(directory) / "invalid.txt"
            file.write_text("2\t1\t0\n")
            with self.assertRaisesRegex(ValueError, "two-column"):
                load_edges(file)


class SamplingTests(unittest.TestCase):
    def test_main_sample_is_reachable_distinct_and_repeatable(self):
        graph = {9: [8, 7], 8: [7], 7: [6], 6: [5], 5: [4]}
        sample = find_pairs(graph, 4, 2, 4)
        self.assertEqual(sample, find_pairs(graph, 4, 2, 4))
        self.assertEqual(len(set(sample)), 4)
        self.assertTrue(all(2 <= bfs_distance(graph, s, g) <= 4 for s, g in sample))

    def test_exact_sample_and_empty_depth_budget(self):
        graph = {3: [2], 2: [1]}
        self.assertEqual(find_pairs_at_distance(graph, 1, 2, random.Random(7))[0], [(3, 1)])
        self.assertEqual(find_pairs_at_distance(graph, 1, 3, random.Random(7), 9), ([], 9))

    def test_main_budget_shortfall_raises(self):
        with self.assertRaisesRegex(RuntimeError, "0 distinct pairs found after 3 attempts"):
            find_pairs({1: []}, 1, 2, 3, max_attempts=3)
