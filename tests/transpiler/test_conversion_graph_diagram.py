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
Tests that the README conversion-graph diagram still describes the real graph.

"""
from __future__ import annotations

import importlib.util
import pathlib

import pytest

from qbraid.transpiler import ConversionGraph

SCRIPT = pathlib.Path(__file__).parents[2] / "bin" / "generate_conversion_graph.py"


@pytest.fixture(scope="module")
def diagram():
    """Load the generator script as a module."""
    spec = importlib.util.spec_from_file_location("generate_conversion_graph", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def parsed_edges(diagram):
    """Return ``{(source, target): is_native}`` as the diagram sees it."""
    aliases = diagram.native_aliases() | diagram.EXTERNAL_ALIASES | set(diagram.ISOLATED_TYPES)
    return {(src, tgt): native for src, tgt, native in diagram.parse_conversions(aliases)}


def test_diagram_covers_every_live_conversion(parsed_edges):
    """The diagram draws every conversion the graph actually offers.

    It reads the source with ``ast`` instead of importing, so a conversion whose naming or
    decorators drift from the pattern would silently vanish from the README picture. The
    reverse containment does not hold: the diagram also draws edges whose endpoints are not
    installed here, which is the entire reason it parses rather than introspects.
    """
    live = {(c.source, c.target) for c in ConversionGraph().conversions()}
    assert live - set(parsed_edges) == set()


def test_diagram_agrees_on_which_conversions_are_native(parsed_edges):
    """``@requires_extras`` is what the diagram styles an edge on; check it matches."""
    mismatched = {
        (c.source, c.target)
        for c in ConversionGraph().conversions()
        if parsed_edges[(c.source, c.target)] != c.native
    }
    assert mismatched == set()


def test_diagram_helpers_are_not_mistaken_for_conversions(parsed_edges):
    """``braket_gate_to_matrix`` and friends match ``*_to_*`` but convert nothing."""
    for helper in [("braket_gate", "matrix"), ("matrix", "cirq_gate"), ("exponent", "pi_string")]:
        assert helper not in parsed_edges


def test_committed_svgs_match_the_current_graph(diagram, parsed_edges):
    """The checked-in SVGs are regenerated whenever the graph changes.

    Guards against a conversion being added without re-running the generator, which would
    leave the README advertising a graph the SDK no longer has.
    """
    graph, names = diagram.build_graph(
        [(src, tgt, native) for (src, tgt), native in parsed_edges.items()]
    )
    pos = diagram.layout(graph, diagram.DEFAULT_SEED)
    for theme in diagram.THEMES:
        path = diagram.OUT_DIR / f"qbraid_conversion_graph_{theme}.svg"
        expected = diagram.render(graph, names, pos, theme)
        assert (
            path.read_text() == expected
        ), f"{path.name} is stale -- run `python bin/generate_conversion_graph.py`"
