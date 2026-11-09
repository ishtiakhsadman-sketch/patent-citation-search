"""The academic report's unit-cost and weighted toy graphs."""

TINY_GRAPH = {1: [2, 3], 2: [4], 3: [4, 5], 4: [6], 5: [6]}
WEIGHTED_GRAPH = {1: [8, 2], 2: [3], 3: [4], 4: [10], 8: [10]}
STEP_COSTS = {(1, 8): 10, (8, 10): 10, (1, 2): 1, (2, 3): 1, (3, 4): 1, (4, 10): 1}


def weighted_step(source: int, target: int) -> int:
    return STEP_COSTS[source, target]
