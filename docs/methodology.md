# Methodology

## Problem definition

The state is a numeric patent ID. Start and goal identify an ordered query. The action from patent A to patent B is available exactly when A cites B in the filtered edge list. A citation chain shows directed connectivity under this representation. Every real-data citation costs one. The weighted toy graph isolates the distinction between minimum cost and minimum depth.

The graph builder removes self-loops and filters on both endpoints. It retains unique edges in input order. Source keys and successor lists retain their original insertion order, which is required for the seeded experiment. A cited-only vertex may appear as a goal or dead end. The retained graph has 250,167 states with no outgoing retained edge. Mean out-degree is 3.04 across all retained states and 4.22 across citing states. Maximum out-degree is 332.

## Priorities and route management

UCS chooses by cumulative cost $g(n)$. When a candidate reaches an already generated state at lower cost, it appends a new entry with that candidate route. The old entry may remain in the frontier until selected and skipped. Once a state is selected for the first time, its cost is final under the nonnegative-weight assumption. The goal test occurs at that point. With all edge costs one, selected cost layers are hop layers, although ties follow patent ID order.

GBFS chooses solely by the absolute difference between the state's ID and the target ID. It marks states on insertion. A later path to a seen state cannot replace its recorded route. Because each finite state is inserted at most once, GBFS terminates on finite graphs with duplicate detection and finds a route if a reachable goal exists. It can commit to a more expensive route. The weighted toy comparison yields 4 for UCS over four edges and 20 for GBFS over two edges.

UCS is complete on this finite graph and optimal for finite nonnegative weights. With finite branching and a positive lower bound on edge cost, the usual infinite-tree completeness argument also applies. The implementation checks encountered weights and rejects invalid or nonfinite cumulative costs. Its weighted optimality assumption applies to the entire searched graph.

A patent-number gap is an ordering signal. Numerical proximity does not imply short graph distance. A direct citation with an ID gap greater than 1 witnesses an overestimate of a one-hop distance. Greedy search may also select a larger heuristic after lower-scoring alternatives leave the frontier. The expansion experiment counts increases between selected states, which can belong to different paths.

## Evaluation protocol

1. Sample 50 distinct ordered pairs with a BFS sweep to shortest-hop distance 14. Candidate goals must be at least 8 hops away. Use local seed 7 and at most 100,000 source draws.
2. Benchmark UCS on all pairs, then GBFS on the same sequence. For each pair, perform one warm-up and five untraced runs. Record the median of the five wall times. Run one separate search with `tracemalloc` to capture peak bytes, and divide by 1,024 for KiB.
3. Validate endpoints and all directed edges for each returned route. Check UCS against independent BFS distances. Join by pair ID and both endpoints to compute excess GBFS hops and compare selected counts.
4. For exact depths 2, 4, 6, 8, 10, and 12, use a single separate RNG seeded at 11 across the depth loop. Seek 20 distinct pairs at each depth within 2,000 source draws. Apply the same measurement protocol to all pairs obtained. Record missing metrics for zero pairs.
5. Trace the first main pair. Confirm that tracing returns the same routes. Count shared selections, states outside the final route, heuristic increases between consecutive selections, and the step at which the goal was selected.

The selected-state count includes the goal and excludes skipped stale entries. The maximum frontier starts at one and includes queued stale entries. The benchmark considers a valid singleton a zero-hop route when start equals goal. An unreachable query returns no route. Validity among found routes and success rate use different denominators.

## Computational effort

Textbook UCS tree-search bounds under a positive step-cost lower bound use $O(b^{1+\lfloor C^*/\epsilon \rfloor})$, where $b$ is branching factor, $C^*$ is optimal cost, and $\epsilon$ is the lower bound. The corresponding worst-case tree bound for greedy search is $O(b^m)$ for maximum depth $m$. These describe abstract tree search. Mean out-degree alone cannot give a rigorous worst-case bound for the retained graph.

In the implemented graph search, both `min(frontier)` and removal can scan a list of length $F$. On the unit-cost benchmark, each state enters the frontier at most once. Across $V$ selected states, list work is bounded by $O(VF)$, plus successor inspection and route copying. On weighted UCS runs, stale entries can add extra removals. Each stored route consumes space proportional to its length, alongside the frontier, state sets, and UCS best-cost dictionary. A heap or parent-pointer representation would change this cost profile and belongs in a separately measured comparison.

## Interpretation

GBFS found a shortest route on every main query, with a smaller average frontier and fewer selected states. This is an observation on the reachable sampled pairs. The depth-two sample and weighted example demonstrate two different failure modes: greater search effort and higher path cost. The depth-eight follow-up and empty deeper samples limit depth comparisons. Hardware, load, Python builds, and timing and allocation boundaries affect resource measurements.
