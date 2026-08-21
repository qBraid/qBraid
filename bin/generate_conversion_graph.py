# Copyright 2026 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Generate the conversion-graph diagram as light and dark SVG variants.

Edges are read out of ``qbraid/transpiler/conversions/`` with ``ast`` rather than from a
live ``ConversionGraph``, because that graph only holds conversions whose endpoints are
installed -- a machine without ``qat`` or ``aqt-connector`` silently draws a smaller SDK.
Parsing the source keeps the diagram tied to what the SDK ships. Run after adding or
removing a conversion::

    python bin/generate_conversion_graph.py

Layout is force-directed, so the seed decides whether the result is readable. The default
was chosen by ``--search``, which scores candidates on node spacing, node-to-edge
clearance, and edge crossings; re-run it after the graph changes.
"""
from __future__ import annotations

import argparse
import ast
import itertools
import math
import pathlib
import sys

import rustworkx as rx

REPO = pathlib.Path(__file__).resolve().parent.parent
CONVERSIONS = REPO / "qbraid" / "transpiler" / "conversions"
OUT_DIR = REPO / "docs" / "_static"

# Seed chosen by --search over 0..6000. See module docstring.
DEFAULT_SEED = 1906

FONT = "Space Grotesk, Inter, system-ui, -apple-system, Segoe UI, Helvetica, Arial, sans-serif"

THEMES = {
    "light": {
        "ink": "#171717",
        "muted": "#6B6B6B",
        "fill": "#FFFFFF",
        "native_fill": "#EDE7FE",
        "native_stroke": "#8B5CF6",
        "native_ink": "#3B2A6B",
        "ext_fill": "#F1F1F4",
        "ext_stroke": "#B8B4C4",
        "ext_ink": "#4A4A55",
        "native_edge": "#A78BFA",
        "ext_edge": "#C3C0CC",
    },
    "dark": {
        "ink": "#EDEDED",
        "muted": "#9A94A8",
        "fill": "#18141F",
        "native_fill": "#2E2445",
        "native_stroke": "#A855F7",
        "native_ink": "#E5DBFF",
        "ext_fill": "#242030",
        "ext_stroke": "#4A4358",
        "ext_ink": "#BDB8CA",
        "native_edge": "#7C5BC7",
        "ext_edge": "#403A4E",
    },
}

# Program types the SDK ships that carry no conversion edge. Without these the diagram
# would imply the SDK cannot represent them at all.
ISOLATED_TYPES = {
    "qubo": "annealing",
    "cpp_pyqubo": "annealing",
    "pulser": "analog",
    "qasm2_kirin": "gate-model",
}

# Aliases reachable only through an extras package, so they never appear in entry points.
EXTERNAL_ALIASES = {
    "stim",
    "pyqir",
    "qat",
    "qibo",
    "pyqpanda3",
    "autoqasm",
    "bloqade",
    "openqasm3",
}

CANVAS_W, CANVAS_H = 1180, 720
MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM = 96, 52, 96
STRIP_H = 74  # band below the graph holding program types that have no conversions
NODE_H = 30
FONT_SIZE = 14.5
CHAR_W = 7.5  # advance width of the label font at FONT_SIZE, measured empirically
PAD_X = 13


def native_aliases() -> set[str]:
    """Return program-type aliases registered by qBraid's own entry points."""
    text = (REPO / "pyproject.toml").read_text()
    block = text.split('[project.entry-points."qbraid.programs"]', 1)[1].split("\n[", 1)[0]
    return {line.split("=", 1)[0].strip() for line in block.splitlines() if "=" in line}


def parse_conversions(aliases: set[str]) -> list[tuple[str, str, bool]]:
    """Return ``(source, target, is_native)`` for every conversion the SDK declares.

    A module-level ``<source>_to_<target>`` function is a conversion when both halves name
    a known alias; that check is what separates the real edges from helpers like
    ``braket_gate_to_matrix``. ``@requires_extras`` marks an edge as needing a third-party
    bridge package.
    """
    edges: list[tuple[str, str, bool]] = []
    for path in sorted(CONVERSIONS.rglob("*.py")):
        if path.name == "__init__.py" or "__pycache__" in str(path):
            continue
        for node in ast.parse(path.read_text()).body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_") or "_to_" not in node.name:
                continue
            source, _, target = node.name.partition("_to_")
            if source not in aliases or target not in aliases:
                continue
            extras = any(
                getattr(dec, "id", "") == "requires_extras"
                or getattr(getattr(dec, "func", None), "id", "") == "requires_extras"
                for dec in node.decorator_list
            )
            edges.append((source, target, not extras))
    return edges


def build_graph(edges: list[tuple[str, str, bool]]) -> tuple[rx.PyDiGraph, list[str]]:
    """Return a rustworkx digraph over every node the diagram shows, and its node order."""
    nodes = sorted({n for src, tgt, _ in edges for n in (src, tgt)} | set(ISOLATED_TYPES))
    graph = rx.PyDiGraph()
    index = {name: graph.add_node(name) for name in nodes}
    for src, tgt, native in edges:
        graph.add_edge(index[src], index[tgt], native)
    return graph, nodes


def normalize(pos: dict[int, tuple[float, float]]) -> dict[int, tuple[float, float]]:
    """Rescale a layout so each axis spans [0, 1].

    Stretching the axes independently is deliberate: the canvas is much wider than it is
    tall, and preserving the layout's own aspect ratio would waste most of that width.
    """
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    span_x = (max(xs) - min(xs)) or 1.0
    span_y = (max(ys) - min(ys)) or 1.0
    return {i: ((x - min(xs)) / span_x, (y - min(ys)) / span_y) for i, (x, y) in pos.items()}


def _segments_cross(a, b, c, d) -> bool:
    """True when segment ab properly crosses segment cd."""

    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    d1, d2 = orient(c, d, a), orient(c, d, b)
    d3, d4 = orient(a, b, c), orient(a, b, d)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _point_segment_distance(p, a, b) -> float:
    """Distance from point p to segment ab."""
    ax, ay, bx, by = *a, *b
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    if denom == 0:
        return math.dist(p, a)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / denom))
    return math.dist(p, (ax + t * dx, ay + t * dy))


def score_layout(pos: dict[int, tuple[float, float]], graph: rx.PyDiGraph) -> float:
    """Rate a layout on how readable it is; higher is better.

    Three things make a force-directed graph unreadable at README size: nodes sitting on
    top of each other, a node label landing on an unrelated edge, and edges crossing. The
    first two dominate, so they carry the weight; crossings are unavoidable at this density
    and only break ties.
    """
    points = [pos[i] for i in pos]
    min_pair = min(math.dist(p, q) for p, q in itertools.combinations(points, 2))

    undirected = {tuple(sorted(e)) for e in graph.edge_list() if e[0] in pos and e[1] in pos}
    segments = [(pos[u], pos[v]) for u, v in undirected]

    min_clearance = 1.0
    for idx in pos:
        for (u, v), (a, b) in zip(undirected, segments):
            if idx in (u, v):
                continue
            min_clearance = min(min_clearance, _point_segment_distance(pos[idx], a, b))

    crossings = sum(
        _segments_cross(*s1, *s2)
        for s1, s2 in itertools.combinations(segments, 2)
        if not set(s1) & set(s2)
    )
    return 140 * min_pair + 90 * min_clearance - 0.08 * crossings


def components(graph: rx.PyDiGraph) -> list[list[int]]:
    """Return weakly connected components, largest first."""
    return sorted((sorted(c) for c in rx.weakly_connected_components(graph)), key=len, reverse=True)


def layout(graph: rx.PyDiGraph, seed: int) -> dict[int, tuple[float, float]]:
    """Return a normalized spring layout over the largest connected component only.

    Everything else -- the two-node analog pathway and the program types with no conversions
    at all -- is placed in a strip by ``render``. A force-directed layout has no force
    between disconnected components, so left in they drift to arbitrary corners and squeeze
    the part of the graph that carries the real structure into an unreadable knot.
    """
    main = components(graph)[0]
    sub = graph.subgraph(main)
    raw = rx.spring_layout(sub, seed=seed, k=1.15, num_iter=1200, repulsive_exponent=2)
    local = normalize({i: tuple(p) for i, p in raw.items()})
    return {main[i]: xy for i, xy in local.items()}


def search_seeds(graph: rx.PyDiGraph, limit: int) -> None:
    """Print the best-scoring seeds in ``range(limit)``."""
    ranked = sorted(
        ((score_layout(layout(graph, s), graph), s) for s in range(limit)), reverse=True
    )
    print(f"top seeds over 0..{limit}:")
    for score, seed in ranked[:12]:
        print(f"  seed={seed:<7} score={score:.3f}")


def node_width(name: str) -> float:
    """Pill width for a label, wide enough that text never touches the border."""
    return len(name) * CHAR_W + 2 * PAD_X


def _anchor(cx, cy, w, other_x, other_y) -> tuple[float, float]:
    """Point where the line toward (other_x, other_y) leaves a node's pill."""
    dx, dy = other_x - cx, other_y - cy
    if dx == 0 and dy == 0:
        return cx, cy
    half_w, half_h = w / 2 + 3, NODE_H / 2 + 3
    scale = min(
        half_w / abs(dx) if dx else math.inf,
        half_h / abs(dy) if dy else math.inf,
    )
    return cx + dx * scale, cy + dy * scale


def strip_positions(graph, names) -> dict[int, tuple[float, float]]:
    """Place everything outside the main component in an evenly spaced strip.

    Components stay contiguous, so the two-node analog pathway renders as one short arrow
    rather than a line across the whole figure.
    """
    strip = [i for comp in components(graph)[1:] for i in comp]
    if not strip:
        return {}
    y = CANVAS_H - MARGIN_BOTTOM - STRIP_H * 0.42
    available = CANVAS_W - 2 * MARGIN_X
    widths = [node_width(names[i]) for i in strip]
    gap = (available - sum(widths)) / (len(strip) - 1) if len(strip) > 1 else 0
    placed, cursor = {}, MARGIN_X
    for i, w in zip(strip, widths):
        placed[i] = (cursor + w / 2, y)
        cursor += w + gap
    return placed


def render(graph, names, pos, theme_name: str) -> str:
    """Return the SVG for one theme."""
    c = THEMES[theme_name]
    inset = max(node_width(names[i]) for i in pos) / 2
    width = CANVAS_W - 2 * MARGIN_X - 2 * inset
    height = CANVAS_H - MARGIN_TOP - MARGIN_BOTTOM - STRIP_H - NODE_H
    screen = {
        i: (MARGIN_X + inset + x * width, MARGIN_TOP + NODE_H / 2 + (1 - y) * height)
        for i, (x, y) in pos.items()
    }
    screen.update(strip_positions(graph, names))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" '
        f'width="{CANVAS_W}" height="{CANVAS_H}" role="img" '
        f'aria-label="qBraid SDK conversion graph">',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="{c["fill"]}"/>',
        "<defs>",
    ]
    for kind in ("native", "ext"):
        parts.append(
            f'<marker id="arrow-{kind}-{theme_name}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M 0 1 L 10 5 L 0 9 z" fill="{c[kind + "_edge"]}"/></marker>'
        )
    parts.append("</defs>")

    # Pairs that convert both ways get mirrored curves so neither hides the other.
    both_ways = {(u, v) for u, v in graph.edge_list() if graph.has_edge(v, u)}

    parts.append('<g fill="none">')
    for u, v in graph.edge_list():
        native = graph.get_edge_data(u, v)
        kind = "native" if native else "ext"
        ux, uy = screen[u]
        vx, vy = screen[v]
        sx, sy = _anchor(ux, uy, node_width(names[u]), vx, vy)
        ex, ey = _anchor(vx, vy, node_width(names[v]), ux, uy)
        if (u, v) in both_ways:
            mx, my = (sx + ex) / 2, (sy + ey) / 2
            dx, dy = ex - sx, ey - sy
            norm = math.hypot(dx, dy) or 1.0
            bow = 13 if u < v else -13
            cx, cy = mx - dy / norm * bow, my + dx / norm * bow
            path = f"M {sx:.1f} {sy:.1f} Q {cx:.1f} {cy:.1f} {ex:.1f} {ey:.1f}"
        else:
            path = f"M {sx:.1f} {sy:.1f} L {ex:.1f} {ey:.1f}"
        dashed = "" if native else 'stroke-dasharray="5 4" '
        parts.append(
            f'<path d="{path}" stroke="{c[kind + "_edge"]}" stroke-width="1.5" '
            f'{dashed}marker-end="url(#arrow-{kind}-{theme_name})" opacity="0.9"/>'
        )
    parts.append("</g>")

    native = native_aliases()
    for i in graph.node_indices():
        name = names[i]
        cx, cy = screen[i]
        w = node_width(name)
        is_native = name in native
        fill = c["native_fill"] if is_native else c["ext_fill"]
        stroke = c["native_stroke"] if is_native else c["ext_stroke"]
        ink = c["native_ink"] if is_native else c["ext_ink"]
        no_edges = not (graph.in_degree(i) or graph.out_degree(i))
        dash = ' stroke-dasharray="4 3"' if no_edges else ""
        parts.append(
            f'<g><rect x="{cx - w / 2:.1f}" y="{cy - NODE_H / 2:.1f}" width="{w:.1f}" '
            f'height="{NODE_H}" rx="{NODE_H / 2}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="1.4"{dash}/>'
            f'<text x="{cx:.1f}" y="{cy + 5:.1f}" text-anchor="middle" font-family="{FONT}" '
            f'font-size="{FONT_SIZE}" font-weight="500" fill="{ink}">{name}</text></g>'
        )

    parts.append(_legend(c, graph))
    parts.append("</svg>")
    return "\n".join(parts)


def _legend(c: dict[str, str], graph: rx.PyDiGraph) -> str:
    """Return the legend strip, including live node and edge counts."""
    y = CANVAS_H - 58
    x = MARGIN_X
    items = []

    def swatch(dx, fill, stroke, dash, label):
        items.append(
            f'<rect x="{x + dx}" y="{y - 9}" width="26" height="18" rx="9" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="1.4"{dash}/>'
            f'<text x="{x + dx + 34}" y="{y + 5}" font-family="{FONT}" font-size="13" '
            f'fill="{c["muted"]}">{label}</text>'
        )

    swatch(0, c["native_fill"], c["native_stroke"], "", "native program type")
    swatch(178, c["ext_fill"], c["ext_stroke"], "", "via extras package")
    swatch(348, "none", c["ext_stroke"], ' stroke-dasharray="4 3"', "no conversions yet")

    line_x = x + 530
    items.append(
        f'<path d="M {line_x} {y} L {line_x + 30} {y}" stroke="{c["native_edge"]}" '
        f'stroke-width="1.5"/>'
        f'<text x="{line_x + 38}" y="{y + 5}" font-family="{FONT}" font-size="13" '
        f'fill="{c["muted"]}">native conversion</text>'
        f'<path d="M {line_x + 168} {y} L {line_x + 198} {y}" stroke="{c["ext_edge"]}" '
        f'stroke-width="1.5" stroke-dasharray="5 4"/>'
        f'<text x="{line_x + 206} " y="{y + 5}" font-family="{FONT}" font-size="13" '
        f'fill="{c["muted"]}">requires extras</text>'
    )

    counts = (
        f"{len(graph.node_indices())} program types &#183; {len(graph.edge_list())} conversions"
    )
    items.append(
        f'<text x="{CANVAS_W - MARGIN_X}" y="{y + 28}" text-anchor="end" font-family="{FONT}" '
        f'font-size="12" fill="{c["muted"]}">{counts}</text>'
    )
    return "<g>" + "".join(items) + "</g>"


def main() -> None:
    """Write both SVG variants, or search for a layout seed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--search",
        type=int,
        metavar="N",
        help="score seeds 0..N and print the best, instead of writing files",
    )
    args = parser.parse_args()

    aliases = native_aliases() | EXTERNAL_ALIASES | set(ISOLATED_TYPES)
    edges = parse_conversions(aliases)
    graph, names = build_graph(edges)

    if args.search:
        search_seeds(graph, args.search)
        return

    pos = layout(graph, args.seed)
    print(
        f"{len(names)} program types, {len(edges)} conversions "
        f"({sum(1 for e in edges if e[2])} native), seed={args.seed}, "
        f"score={score_layout(pos, graph):.3f}"
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        path = OUT_DIR / f"qbraid_conversion_graph_{theme}.svg"
        path.write_text(render(graph, names, pos, theme))
        print(f"  wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    sys.exit(main())
