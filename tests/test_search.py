import math
import unittest

from patent_search.examples import TINY_GRAPH, WEIGHTED_GRAPH, weighted_step
from patent_search.sampling import bfs_distance
from patent_search.search import greedy_search, heuristic, is_valid_path, path_cost, ucs_search


class SearchTests(unittest.TestCase):
    def test_original_unit_routes_and_counters(self):
        self.assertEqual(ucs_search(TINY_GRAPH, 1, 6), ([1, 2, 4, 6], 6, 2))
        self.assertEqual(greedy_search(TINY_GRAPH, 1, 6), ([1, 3, 5, 6], 4, 3))
        self.assertEqual(bfs_distance(TINY_GRAPH, 1, 6), 3)

    def test_original_weighted_counterexample(self):
        ucs, u_count, _ = ucs_search(WEIGHTED_GRAPH, 1, 10, edge_cost=weighted_step)
        gbfs, g_count, _ = greedy_search(WEIGHTED_GRAPH, 1, 10)
        self.assertEqual((ucs, u_count), ([1, 2, 3, 4, 10], 5))
        self.assertEqual((gbfs, g_count), ([1, 8, 10], 3))
        self.assertEqual(sum(weighted_step(a, b) for a, b in zip(ucs, ucs[1:])), 4)
        self.assertEqual(sum(weighted_step(a, b) for a, b in zip(gbfs, gbfs[1:])), 20)

    def test_later_improvement_replaces_route_and_skips_stale_entry(self):
        graph = {1: [2, 3], 3: [2], 2: [4]}
        costs = {(1, 2): 9, (1, 3): 1, (3, 2): 1, (2, 4): 10}
        order, routes = [], {}
        result = ucs_search(graph, 1, 4, lambda a, b: costs[a, b],
                            order_log=order, path_log=routes)
        self.assertEqual(result, ([1, 3, 2, 4], 4, 2))
        self.assertEqual(order, [1, 3, 2, 4])
        self.assertEqual(routes[2], [1, 3, 2])

    def test_cycle_with_reachable_and_unreachable_goals(self):
        graph = {1: [2], 2: [1, 3], 3: [2]}
        for search in (ucs_search, greedy_search):
            with self.subTest(search=search.__name__):
                self.assertEqual(search(graph, 1, 3), ([1, 2, 3], 3, 1))
                self.assertEqual(search(graph, 1, 99), (None, 3, 1))

    def test_source_equals_goal(self):
        for search in (ucs_search, greedy_search):
            self.assertEqual(search({}, 7, 7), ([7], 1, 1))
        self.assertTrue(is_valid_path({}, [7], 7, 7))
        self.assertEqual(path_cost([7]), 0)

    def test_invalid_routes_and_wrong_direction(self):
        graph = {1: [2], 2: [3]}
        for route in (None, [], [2, 3], [1, 2], [1, 3], [1, 3, 2, 3]):
            with self.subTest(route=route):
                self.assertFalse(is_valid_path(graph, route, 1, 3))
        self.assertFalse(is_valid_path(graph, [3, 2, 1], 3, 1))
        self.assertTrue(is_valid_path(graph, [1, 2, 3], 1, 3))

    def test_ties_prefer_smaller_state_identifier(self):
        graph = {1: [12, 8], 8: [10], 12: [10]}
        for search in (ucs_search, greedy_search):
            self.assertEqual(search(graph, 1, 10)[0], [1, 8, 10])
        self.assertEqual(heuristic(12, 10), heuristic(8, 10))

    def test_greedy_can_choose_a_longer_unit_cost_route(self):
        graph = {1: [9, 2], 9: [8], 8: [10], 2: [10]}
        self.assertEqual(ucs_search(graph, 1, 10)[0], [1, 2, 10])
        self.assertEqual(greedy_search(graph, 1, 10)[0], [1, 9, 8, 10])

    def test_zero_weight_cycle_and_nonnegative_costs(self):
        graph = {1: [2, 3], 2: [1, 3]}
        costs = {(1, 2): 0, (2, 1): 0, (2, 3): 1, (1, 3): 2}
        self.assertEqual(ucs_search(graph, 1, 3, lambda a, b: costs[a, b])[0], [1, 2, 3])

    def test_rejects_invalid_encountered_weights(self):
        for step in (-1, math.inf, math.nan, "1"):
            with self.subTest(step=step):
                with self.assertRaisesRegex(ValueError, "finite nonnegative"):
                    ucs_search({1: [2]}, 1, 2, lambda a, b: step)
