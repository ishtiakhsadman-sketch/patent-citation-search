import hashlib
import json
import tracemalloc
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from patent_search.evaluation import compare_pairs, make_summary, run_algorithm
from patent_search.search import greedy_search, ucs_search


class EvaluationTests(unittest.TestCase):
    def test_timing_protocol_uses_five_runs_and_separate_memory_run(self):
        graph = {2: [1]}
        traced = []

        def search(graph, source, goal):
            traced.append(tracemalloc.is_tracing())
            return ucs_search(graph, source, goal)

        timed = Mock(side_effect=search)
        with patch("patent_search.evaluation.time.perf_counter",
                   side_effect=[0, .004, 1, 1.001, 2, 2.003, 3, 3.002, 4, 4.005]):
            table = run_algorithm(timed, graph, [(2, 1)])
        self.assertEqual(traced, [False] * 6 + [True])
        self.assertEqual(timed.call_count, 7)
        self.assertAlmostEqual(table.iloc[0].time_ms, 3)
        self.assertGreater(table.iloc[0].peak_memory_kb, 0)
        self.assertFalse(tracemalloc.is_tracing())

    def test_missing_routes_do_not_dilute_validity_among_found(self):
        table = run_algorithm(ucs_search, {2: [1]}, [(2, 1), (1, 2)])
        summary = make_summary(table, .1).set_index("Measure").Value
        self.assertEqual(summary["Success rate (%)"], 50)
        self.assertEqual(summary["Valid paths among found paths (%)"], 100)

    def test_pair_join_checks_identity_and_hop_delta(self):
        graph = {1: [9, 2], 9: [8], 8: [10], 2: [10]}
        ucs = run_algorithm(ucs_search, graph, [(1, 10)])
        gbfs = run_algorithm(greedy_search, graph, [(1, 10)])
        self.assertEqual(compare_pairs(ucs, gbfs).extra_hops_gbfs.tolist(), [1])
        with self.assertRaisesRegex(ValueError, "benchmark pairs differ"):
            compare_pairs(ucs, gbfs.assign(goal=99))

    def test_recorded_files_match_provenance(self):
        root = Path(__file__).resolve().parents[1] / "results/recorded"
        manifest = json.loads((root / "provenance.json").read_text(encoding="utf-8"))
        hashes = dict(manifest["export_sha256"])
        hashes.update({name: record["sha256"] for name, record in manifest["recorded_figure_provenance"].items()})
        for name, expected in hashes.items():
            with self.subTest(file=name), (root / name).open("rb") as data:
                self.assertEqual(hashlib.file_digest(data, "sha256").hexdigest(), expected)
