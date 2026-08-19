# Transpiler design: representation translation as routing

*Design notes for contributors. Companion to the API reference; the user-facing
guide lives at [docs.qbraid.com](https://docs.qbraid.com/v2/sdk/user-guide/transpiler).*

Sections 1, 2, 4 and 5 are the overview: what the transpiler is, how it picks a
path, and what that demands of a conversion. Section 3 is the deeper argument for
why the fast algorithms are exact, and can be skipped on a first read.

## 1. The problem

The quantum software ecosystem has no common intermediate representation.
Programs exist as Qiskit `QuantumCircuit`s, Cirq `Circuit`s, Braket circuits,
pyQuil `Program`s, pytket circuits, OpenQASM 2/3 source, QIR, and a long tail of
vendor-native formats. A platform that submits user programs to arbitrary
hardware has to translate between them.

Two obvious architectures both fail:

- **Pairwise converters** need `O(n²)` implementations for `n` representations,
  and each new format costs `2(n-1)` converters.
- **Hub-and-spoke**, with one canonical IR, needs only `O(n)` converters but
  forces every conversion through the hub, so the hub's expressiveness gaps
  propagate to *every* pair. An IR that cannot express mid-circuit measurement
  loses it even between two formats that both support it.

qBraid generalizes both. Conversions form a **directed weighted graph**, and
translating between representations is **routing**: the composition of
converters along a chosen path. Pairwise and hub topologies are special cases.
In practice the graph is a sparse hybrid — dense around the QASM dialects and
Cirq, sparse at the periphery.

This is a different layer from what Qiskit or TKET call transpilation. There,
the object transformed is the gate content, for a target device. Here it is the
*representation*; device compilation happens downstream in the runtime layer.

## 2. Model

Let `G = (V, E)` be a directed graph.

- `V` — registered program type aliases (`qiskit`, `cirq`, `qasm2`, …), declared
  through setuptools entry points, so third-party packages add representations
  without modifying qBraid.
- `E` — conversion functions `f: P_u → P_v`, discovered by naming convention
  (`<source>_to_<target>`) and filtered by whether their required extras are
  importable.

Conversions are **partial**: a converter may raise on programs it cannot express
(mid-circuit measurement into Braket, confusion maps into Quil). That partiality
is load-bearing for the routing semantics in §4.

### Weights and cost

Each edge carries a weight `w ∈ [0,1]`, interpreted as empirical conversion
fidelity — the measured fraction of benchmark constructs the converter
translates correctly. With a global bias `β ≥ 0` (default `0.25`), the stored
cost is

```
c(e) = -ln(w) + β
```

Path cost is additive, so minimizing it maximizes hop-discounted fidelity:

```
argmin_P c(P) = argmax_P  e^(-βk) · Π w_e        (k = hop count)
```

This is the standard log-transform reducing "most reliable path" to shortest
path. The bias is a per-hop discount: each extra conversion must be paid for in
fidelity. It yields a usable rule of thumb — a direct edge beats a two-hop route
of perfect converters exactly when `w > e^(-β)`, i.e. **0.7788** at the default
bias. `cirq_to_pyquil` carries weight `0.74`, just under that line, which is
why measured circuits route to pyQuil through `qasm2` instead of directly.

As `β → 0` routing becomes purely fidelity-greedy, tolerating arbitrarily long
paths for negligible gains; as `β → ∞` it degenerates to hop counting. Negative
bias would make costs negative and void the search's correctness, so it is
rejected at construction.

Weight `0` maps to a large *finite* cost (`1e6`), not infinity — see §3.

### The ranking key

Paths are ordered by a lexicographic composite key, not by cost alone:

```
κ(P) = ( cost(P), hops(P), (alias₀, alias₁, …) )
```

Each component earns its place. Cost carries the semantics. Hop count breaks
cost ties toward fewer failure surfaces. The alias tuple makes the order
**total**: without it, exact ties were resolved by whatever order the path
enumerator produced — effectively by conversion registration order — so
installing an unrelated plugin could silently reroute an existing pair. With it,
routing is a pure function of the graph's content.

## 3. Why the fast algorithms are exact

*Deeper section; skip on a first read.*

The *definition* of correct routing is: enumerate all simple paths, sort by `κ`,
take the prefix. That is executable, and the test suite uses it as an oracle,
but it is factorial in graph density — intractable past ~14 nodes. Since
`ConversionGraph` accepts arbitrary user-supplied conversions, the production
implementation must be output-equivalent to that definition at polynomial cost.

It uses Dijkstra for the single best path and Yen's algorithm for top-`N`, both
ranking by `κ` rather than a scalar. Their exactness rests on two properties of
the key under edge-append:

- **Monotonicity** — `κ(P·e) > κ(P)`. Costs are non-negative (guaranteed by
  `β ≥ 0`) and hop count strictly grows.
- **Isotonicity** — appending a common edge preserves order. This is what lets
  Dijkstra discard all but the best label per node.

Together these make `(cost, hops, aliases)` a totally ordered monoid under
append, and Dijkstra is exact precisely when append is an order-embedding.

That framing is worth stating because it converts implementation choices into
consequences. Saturating a zero weight at `+∞` would break isotonicity, since
`∞ + x = ∞` is not injective: two labels that differ at an intermediate node
become indistinguishable after passing through a shared zero-weight edge. The
finite `1e6` cost preserves the embedding, and paths then rank by number of
zero-weight edges first.

## 4. Runtime semantics

`transpile()` does not commit to the single best path. It takes the top `N`
(`max_path_attempts`, default 3) and attempts them **in order**, deep-copying
the program per attempt and falling through on any exception. Only if all `N`
fail does it raise, reporting the accumulated per-path errors.

The static ranking is therefore a **prior**, and execution the posterior: a
weight records expected fidelity over a benchmark distribution, but a converter
may still reject a specific program.

This has a hard consequence for anyone writing a conversion:

> **Converters must fail loudly rather than approximate.** Dropping
> measurements, discarding a confusion map, or fragmenting a readout register
> produces a program the router believes is correct. The error model assumes a
> raised exception means "try the next path" and a returned program means
> "correct". Silent degradation is the one failure the architecture cannot
> absorb.

## 5. Structure

```
qbraid/transpiler/
├── edge.py        Conversion: aliases, function, weight→cost transform,
│                  supportedness (extras importable), nativeness
├── graph.py       ConversionGraph: nodes/edges from entry points, Dijkstra and
│                  Yen's over the ranking key, path-finding APIs, typed subgraphs
├── converter.py   transpile(): resolve aliases → top-N paths → ranked fallback
└── conversions/   edge implementations, <source>/<source>_to_<target>.py
```

Three properties follow from the model and are worth naming:

- **Open-world extensibility.** Nodes and edges arrive via entry points. The
  deterministic tie-break is what makes this safe: a plugin cannot perturb
  existing routes except by winning on cost.
- **Environment-adaptive topology.** An edge exists only if its dependencies are
  importable, so the same program and call site can route differently — but
  deterministically — in different environments.
- **Typed subgraphs.** Nodes carry an `ExperimentType` (gate-model, AHS, …), and
  routing never crosses types.
