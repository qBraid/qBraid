# Transpiler routing: model, invariants, and contracts

Read this before modifying `qbraid/transpiler/graph.py`, `qbraid/transpiler/edge.py`,
or anything under `qbraid/transpiler/conversions/`. It states the semantic model the
transpiler's path selection is built on, the invariants that model depends on, and the
tests that enforce each one. Several of these invariants are load-bearing but invisible
from a local diff — changes that look like harmless cleanups (swapping a constant for
`float("inf")`, reordering a summation, filtering results instead of bounding a search)
have each produced provably wrong routing. If a change here alters routing semantics,
update this file in the same PR.

## The model

The transpiler is a directed weighted graph: nodes are registered program type aliases
(`qiskit`, `cirq`, `qasm2`, ...), edges are conversion functions. Each edge carries a
weight `w ∈ [0, 1]` — measured conversion fidelity — stored as the cost

```
cost(e) = -ln(w) + bias        # bias ≥ 0, default 0.25
```

Path cost is the sum of edge costs, so minimizing cost maximizes hop-discounted path
fidelity `e^(-bias·k) · Π w_i` over `k` hops. A direct edge of weight `w` beats two
perfect hops iff `w > e^(-bias)` (≈ 0.7788 at bias 0.25).

Paths are ranked by the lexicographic key **(total cost, hop count, node-alias tuple)**.
Cost is the semantics; hops break cost ties; the alias tuple makes ranking a pure
function of the graph's content, independent of conversion registration order.

The *definition* of correct ranking is: enumerate every simple path, sort by this key,
truncate. The production search (Dijkstra for the best path, Yen's algorithm for top-N)
must be indistinguishable from that definition — `_brute_force_ranking` in
`tests/transpiler/test_conversion_graph.py` is the executable oracle, and the fuzz
tests compare against it on generated graphs.

`transpile()` takes the top `max_path_attempts` paths and tries them in ranked order,
falling through on any exception. The ranking is a prior; execution is the posterior.

## Invariants

Each of these has been violated once. The named tests fail if it is violated again.

1. **Edge costs are finite and non-negative.** The search algorithms are exact only
   while cost addition is translation-invariant (`a < b ⟹ a + c < b + c`, strictly).
   `float("inf")` breaks this — `inf + x == inf` collapses distinctions the tie-breaks
   depend on, and even single-path Dijkstra then returns wrong routes. Weight 0 maps to
   the finite `_ZERO_WEIGHT_COST` (1e6), so paths rank by fewest zero-weight edges
   first. Negative bias makes costs negative and is rejected at construction. Weights
   are transformed with `-log(w)`, never `log(1/w)` — the reciprocal overflows to inf
   for subnormal weights.
   → `test_zero_weight_ties_rank_by_fewest_zero_weight_edges`,
   `test_negative_bias_raises`,
   `test_subnormal_weight_cost_stays_finite_and_below_zero_weight_cost`

2. **Every cost is the same left-to-right float sum.** Two paths whose costs are equal
   in exact arithmetic can differ in the last ulp if summed in different orders, making
   two parts of the code disagree about a tie. Yen's spur searches are therefore seeded
   with their deviation root's ranking key, so all sums are the fold `_rank_key`
   computes. Do not introduce a second summation order.
   → `test_ranking_matches_enumeration_near_float_cost_ties`

3. **The fast search matches full enumeration, always.** Any change to ranking or
   search must keep the oracle comparisons green, and a new cost feature (weight range,
   key component) must be added to the fuzz generator's pool — the hand-written cases
   only cover shapes someone thought of.
   → `test_top_paths_match_full_enumeration` (every reachable native-graph pair),
   `test_ranking_matches_enumeration_on_generated_graphs`

4. **`max_depth` bounds the search; it is not a filter.** The cap travels into every
   Dijkstra call as a node-count budget (capped searches settle per `(node, hops)`
   state). Filtering after selection reported "no path" while a qualifying path
   existed; filtering after Yen's made an unsatisfiable cap enumerate every simple
   path in the graph.
   → `test_max_depth_finds_path_ranked_below_top_n`,
   `test_unsatisfiable_depth_cap_stays_polynomial`

5. **The two public finders cannot disagree.** `find_shortest_conversion_path` and
   `find_top_shortest_conversion_paths` rank by the same key, so `shortest_path()`
   never reports a route `transpile()` would not take. They were once separate
   implementations, which is what made production routing failures hard to diagnose.
   → `test_native_graph_shortest_path_agrees_with_top_paths`,
   `test_routing_is_independent_of_conversion_order`

## The converter contract

`transpile()`'s fallback model assumes: a raised exception means "try the next path";
a returned program means "correct". Therefore:

- **Fail loudly; never approximate.** A converter that cannot represent a construct
  (mid-circuit measurement into Braket, confusion maps into Quil, two qubits measured
  into one classical bit) raises `ProgramConversionError`. Silently dropping or
  restructuring the construct corrupts every route through that edge.
- **Readout order follows the classical bit, not encounter order.** Braket orders
  results by each `Measure`'s classical bit index; cirq QASM-derived keys encode the
  bit in the `c_N` suffix; pytket maps qubits to bits explicitly. Converters that
  merge or re-append measurements must preserve that mapping — ordering by instruction
  or moment order has shipped transposed readouts more than once.
  → `tests/transpiler/test_measurement_semantics.py` executes converted circuits with
  an asymmetric bit pattern so any permutation changes the result;
  `tests/transpiler/test_measurement_coverage.py` sweeps every reachable pair with a
  measured GHZ circuit and asserts the qubit-to-bit mapping is the identity.

## Weight governance

- Every weight below 1.0 must trace to a benchmark result or a rationale recorded in a
  comment at the `@weight` declaration. An unexplained value acts as a hidden tie-break
  that reroutes pairs silently.
- `cirq_to_pyquil` must stay below `e^(-0.25) ≈ 0.7788`, or `cirq -> pyquil` reroutes
  back onto the direct edge (lower gate fidelity than the `qasm2` route).
- Changing any weight changes routing. Re-run the measurement coverage sweep and diff
  `shortest_path` for every reachable pair against the base branch before and after.

## If you touch X, run Y

| Change | Minimum verification |
| --- | --- |
| `graph.py`, `edge.py` | `pytest tests/transpiler/test_conversion_graph.py tests/transpiler/test_conversion_edge.py` |
| Any converter in `conversions/` | `pytest tests/transpiler/test_measurement_coverage.py tests/transpiler/test_measurement_semantics.py` plus that converter's module tests |
| Any `@weight` value | Both of the above, plus a per-pair route diff against the base branch |

History: the design and each invariant's origin are in PRs
[#1312](https://github.com/qBraid/qBraid/pull/1312) /
[#1313](https://github.com/qBraid/qBraid/pull/1313) and issue
[#1307](https://github.com/qBraid/qBraid/issues/1307).
