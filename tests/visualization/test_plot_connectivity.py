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
Unit tests for plotting device connectivity graphs.

"""
from unittest.mock import Mock

import matplotlib
import pytest
from qbraid_core.services.runtime.schemas import DeviceCalibration

from qbraid.visualization import plot_connectivity_graph
from qbraid.visualization.exceptions import VisualizationError
from qbraid.visualization.plot_connectivity import lattice_positions

matplotlib.use("Agg")

CEPHEUS_QRN = "rigetti:rigetti:qpu:cepheus-1-108q"


def _calibration(edges=None, qubits=None) -> DeviceCalibration:
    """Calibration payload modeled on the production Cepheus-1-108Q API response."""
    return DeviceCalibration.model_validate(
        {
            "physicalDeviceId": "rigetti:Cepheus-1-108Q",
            "deviceQRNs": [CEPHEUS_QRN],
            "provider": "rigetti",
            "lastCalibrated": "2026-07-21T18:55:46+00:00",
            "fetchedAt": "2026-07-21T19:00:18.386133+00:00",
            "qubits": qubits
            or {
                "0": {"readoutError": 0.04, "gateError": {"rb": 0.0019}},
                "1": {"readoutError": 0.083, "gateError": {"rb": 0.0021}},
                "2": {"readoutError": 0.05, "gateError": {"rb": 0.002}},
            },
            "edges": {
                "gateError": (
                    edges
                    if edges is not None
                    else {
                        "cz": [
                            {"source": 0, "target": 1, "value": 0.0085},
                            {"source": 1, "target": 2, "value": 0.0246},
                        ]
                    }
                )
            },
        }
    )


def _device(coupling_map=((0, 1), (1, 2)), calibration="default", topology=None) -> Mock:
    device = Mock()
    device.id = CEPHEUS_QRN
    device.coupling_map = coupling_map
    device.get_calibrations.return_value = (
        _calibration() if calibration == "default" else calibration
    )
    device.client.get_device.return_value = Mock(topology=topology)
    return device


class TestLatticePositions:
    """Tests for lattice_positions."""

    def test_square_lattice_row_major(self):
        """square-lattice ids map row-major: id = cols * row + col, y negated."""
        pos = lattice_positions({"type": "square-lattice", "rows": 2, "cols": 3}, range(6))
        assert pos == {0: (0, 0), 1: (1, 0), 2: (2, 0), 3: (0, -1), 4: (1, -1), 5: (2, -1)}

    def test_square_lattice_clipped_sequential_over_spans(self):
        """Clipped lattices number qubits sequentially across populated cells."""
        topology = {"type": "square-lattice-clipped", "gridCols": 3, "rowSpans": [[1, 2], [0, 2]]}
        pos = lattice_positions(topology, range(5))
        assert pos == {0: (1, 0), 1: (2, 0), 2: (0, -1), 3: (1, -1), 4: (2, -1)}

    def test_unknown_topology_returns_none(self):
        """Unknown or missing topology types fall back to None (force-directed)."""
        assert lattice_positions({"type": "heavy-hex"}, range(4)) is None
        assert lattice_positions(None, range(4)) is None

    def test_filters_to_requested_qubits(self):
        """Only requested qubit ids appear in the returned mapping."""
        pos = lattice_positions({"type": "square-lattice", "rows": 2, "cols": 2}, [0, 3])
        assert set(pos) == {0, 3}


class TestPlotConnectivityGraph:
    """Tests for plot_connectivity_graph."""

    def test_saves_figure_from_device(self, tmp_path):
        """The device path produces a non-empty figure file."""
        out = tmp_path / "graph.png"
        device = _device(topology={"type": "square-lattice", "rows": 1, "cols": 3})
        plot_connectivity_graph(device, show=False, save_path=out)
        assert out.exists() and out.stat().st_size > 0

    def test_primitive_overrides_bypass_device(self, tmp_path):
        """coupling_map/calibration/topology kwargs work without a device."""
        out = tmp_path / "graph.png"
        plot_connectivity_graph(
            coupling_map=((0, 1), (1, 2)),
            calibration=_calibration(),
            topology={"type": "square-lattice", "rows": 1, "cols": 3},
            show=False,
            save_path=out,
        )
        assert out.exists() and out.stat().st_size > 0

    def test_no_calibration_raises(self):
        """Devices without calibration data raise VisualizationError."""
        device = _device(calibration=None)
        with pytest.raises(VisualizationError, match="calibration"):
            plot_connectivity_graph(device, show=False)

    def test_empty_coupling_map_raises_with_all_to_all_hint(self):
        """Trapped-ion devices (edges empty) raise with an explanatory message."""
        device = _device(coupling_map=())
        with pytest.raises(VisualizationError, match="all-to-all"):
            plot_connectivity_graph(device, show=False)

    def test_unknown_topology_uses_fallback_layout(self, tmp_path):
        """No lattice config still plots via the force-directed fallback."""
        out = tmp_path / "graph.png"
        device = _device(topology=None)
        plot_connectivity_graph(device, show=False, save_path=out)
        assert out.exists() and out.stat().st_size > 0

    def test_topology_fetch_failure_falls_back(self, tmp_path):
        """A client error while fetching topology degrades to the fallback layout."""
        out = tmp_path / "graph.png"
        device = _device()
        device.client.get_device.side_effect = RuntimeError("api down")
        plot_connectivity_graph(device, show=False, save_path=out)
        assert out.exists() and out.stat().st_size > 0

    def test_edge_gate_selection(self, tmp_path):
        """An explicit edge_gate picks that gate's entries; unknown gate raises."""
        out = tmp_path / "graph.png"
        cal = _calibration(
            edges={
                "cz": [{"source": 0, "target": 1, "value": 0.01}],
                "iswap": [{"source": 1, "target": 2, "value": 0.02}],
            }
        )
        device = _device(calibration=cal, topology={"type": "square-lattice", "rows": 1, "cols": 3})
        plot_connectivity_graph(device, edge_gate="iswap", show=False, save_path=out)
        assert out.exists() and out.stat().st_size > 0

        with pytest.raises(VisualizationError, match="iswapx"):
            plot_connectivity_graph(device, edge_gate="iswapx", show=False)

    def test_dead_qubit_rendered_as_dotted_outline(self, tmp_path):
        """A qubit in the lattice footprint with no couplings is drawn as a ghost."""
        out = tmp_path / "graph.png"
        # Lattice footprint 0..3, but qubit 2 has no working couplings (dead).
        device = _device(
            coupling_map=((0, 1), (1, 3)),
            topology={"type": "square-lattice", "rows": 1, "cols": 4},
        )
        plot_connectivity_graph(device, show=False, save_path=out)
        assert out.exists() and out.stat().st_size > 0

    def test_show_displays_figure(self, monkeypatch):
        """show=True routes to matplotlib's show."""
        # pylint: disable-next=import-outside-toplevel
        import matplotlib.pyplot as mpl_plt

        shown = []
        monkeypatch.setattr(mpl_plt, "show", lambda: shown.append(True))
        device = _device(topology={"type": "square-lattice", "rows": 1, "cols": 3})
        plot_connectivity_graph(device, show=True)
        assert shown == [True]
