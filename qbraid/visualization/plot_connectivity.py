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
Module for plotting device connectivity graphs colored by calibration data.

"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Optional

from qbraid_core._import import LazyLoader

from .exceptions import VisualizationError

if TYPE_CHECKING:
    import matplotlib.pyplot
    from qbraid_core.services.runtime.schemas import DeviceCalibration

    import qbraid.runtime

plt: matplotlib.pyplot = LazyLoader("plt", globals(), "matplotlib.pyplot")


def lattice_positions(topology: Optional[dict], qubits: Iterable[int]) -> Optional[dict]:
    """Map qubit ids to (x, y) plot positions using a device topology config.

    Supports the ``square-lattice`` (row-major ids, e.g. Rigetti Cepheus) and
    ``square-lattice-clipped`` (ids numbered sequentially across populated
    cells, e.g. IQM Crystal) topology types served on qBraid device documents.

    Args:
        topology: The device document's ``topology`` config, or None.
        qubits: Qubit ids to place.

    Returns:
        Mapping of qubit id to (x, y), or None when the topology type is
        unknown (callers should fall back to a force-directed layout).
    """
    kind = (topology or {}).get("type")
    if kind == "square-lattice":
        cols = topology["cols"]
        return {q: (q % cols, -(q // cols)) for q in qubits}
    if kind == "square-lattice-clipped":
        pos: dict[int, tuple[int, int]] = {}
        index = 0
        for row, (start, end) in enumerate(topology["rowSpans"]):
            for col in range(start, end + 1):
                pos[index] = (col, -row)
                index += 1
        requested = set(qubits)
        return {q: xy for q, xy in pos.items() if q in requested}
    return None


def _fallback_positions(coupling_map) -> dict:
    """Force-directed layout via rustworkx for devices without a lattice config."""
    import rustworkx as rx  # pylint: disable=import-outside-toplevel

    nodes = sorted({q for edge in coupling_map for q in edge})
    graph = rx.PyGraph()
    indices = {q: graph.add_node(q) for q in nodes}
    graph.add_edges_from([(indices[a], indices[b], None) for a, b in coupling_map])
    layout = rx.spring_layout(graph, seed=42)
    return {q: tuple(layout[indices[q]]) for q in nodes}


# pylint: disable-next=too-many-locals,too-many-statements,too-many-arguments
def plot_connectivity_graph(
    device: Optional[qbraid.runtime.QbraidDevice] = None,
    *,
    coupling_map: Optional[Iterable[tuple[int, int]]] = None,
    calibration: Optional[DeviceCalibration] = None,
    topology: Optional[dict] = None,
    edge_gate: Optional[str] = None,
    title: Optional[str] = None,
    show: bool = True,
    save_path: Optional[str | Path] = None,
) -> None:
    """Plot a device's connectivity graph colored by live calibration data.

    Edges are colored by two-qubit gate error and nodes by readout error,
    both on a single-hue scale where darker is better, matching the qBraid
    Lab topology view. Qubits present in the lattice footprint but without
    any working couplings (e.g. dead qubits) are drawn as dotted outlines.

    Args:
        device: A ``QbraidDevice`` to fetch coupling map, calibrations, and
            topology from. Optional if the keyword overrides are given.
        coupling_map: Physical qubit pairs. Defaults to ``device.coupling_map``.
        calibration: A ``DeviceCalibration`` snapshot. Defaults to
            ``device.get_calibrations()``.
        topology: Device topology config for lattice layout. Defaults to the
            device document's ``topology`` field; unknown types fall back to
            a force-directed layout.
        edge_gate: Which gate's error entries to color edges by (e.g. ``"cz"``).
            Defaults to the first gate in the calibration data.
        title: Plot title. Defaults to the device id and calibration time.
        show: If True, display the figure. Defaults to True.
        save_path: Path to save the figure. If None, figure is not saved.

    Raises:
        VisualizationError: If no calibration data is available, the coupling
            map is empty (e.g. all-to-all trapped-ion devices), or
            ``edge_gate`` is not present in the calibration data.
    """
    # pylint: disable=import-outside-toplevel
    from matplotlib.cm import ScalarMappable
    from matplotlib.collections import LineCollection
    from matplotlib.colors import Normalize

    if calibration is None and device is not None:
        calibration = device.get_calibrations()
    if calibration is None:
        raise VisualizationError(
            "No calibration data available for this device. Calibration-based "
            "plotting requires a QPU with published calibrations."
        )

    if coupling_map is None and device is not None:
        coupling_map = device.coupling_map
    coupling_map = tuple(coupling_map or ())
    if not coupling_map:
        raise VisualizationError(
            "The device reports no coupling edges. Trapped-ion and other "
            "all-to-all devices have no discrete connectivity graph to plot."
        )

    if topology is None and device is not None:
        try:
            topology = device.client.get_device(device.id).topology
        except Exception:  # pylint: disable=broad-exception-caught
            topology = None

    gate_errors = calibration.edges.get("gateError", {})
    gate = edge_gate or next(iter(gate_errors), None)
    if gate not in gate_errors:
        raise VisualizationError(
            f"Gate '{gate}' not found in calibration data. "
            f"Available gates: {sorted(gate_errors)}"
        )
    edge_error = {(e.source, e.target): e.value for e in gate_errors[gate]}
    readout_error = {
        int(q): m.readout_error
        for q, m in calibration.qubits.items()
        if m.readout_error is not None
    }

    nodes = sorted({q for edge in coupling_map for q in edge})
    pos = lattice_positions(topology, nodes) or _fallback_positions(coupling_map)

    edge_vals = [edge_error.get((a, b), edge_error.get((b, a), 0.0)) for a, b in coupling_map]
    node_vals = [readout_error.get(q, 0.0) for q in nodes]
    edge_norm = Normalize(min(edge_vals), max(edge_vals))
    node_norm = Normalize(min(node_vals), max(node_vals))
    cmap = plt.cm.Purples_r

    xs = [xy[0] for xy in pos.values()]
    ys = [xy[1] for xy in pos.values()]
    width = max(xs) - min(xs) + 1
    height = max(ys) - min(ys) + 1
    fig, ax = plt.subplots(figsize=(width * 0.72 + 2.6, height * 0.72 + 1.2))

    segments = [(pos[a], pos[b]) for a, b in coupling_map]
    lines = LineCollection(segments, colors=cmap(edge_norm(edge_vals)), linewidths=3.4)
    ax.add_collection(lines)
    ax.scatter(
        [pos[q][0] for q in nodes],
        [pos[q][1] for q in nodes],
        s=330,
        c=cmap(node_norm(node_vals)),
        edgecolors="#581c87",
        linewidths=1.1,
        zorder=2,
    )
    for q in nodes:
        ax.annotate(
            str(q),
            pos[q],
            ha="center",
            va="center",
            fontsize=6.5,
            color="#f3e8ff",
            zorder=3,
        )

    # Qubits in the lattice footprint with no couplings (e.g. dead qubits)
    footprint = lattice_positions(topology, range(max(nodes) + 1)) or {}
    for q in sorted(set(footprint) - set(nodes)):
        ax.scatter(
            *footprint[q],
            s=330,
            facecolors="none",
            edgecolors="#c084fc",
            linestyle=":",
            linewidths=1.4,
            zorder=2,
        )
        ax.annotate(
            str(q),
            footprint[q],
            ha="center",
            va="center",
            fontsize=6.5,
            color="#c084fc",
            zorder=3,
        )

    fig.colorbar(
        ScalarMappable(edge_norm, cmap),
        ax=ax,
        shrink=0.7,
        label=f"{gate.upper()} error (darker is better)",
    )
    fig.colorbar(
        ScalarMappable(node_norm, cmap),
        ax=ax,
        shrink=0.7,
        label="Readout error (darker is better)",
    )

    if title is None:
        device_id = getattr(device, "id", None) or calibration.physical_device_id
        title = f"{device_id}\ncalibrated {calibration.last_calibrated}"
    ax.set_title(title)
    ax.set_axis_off()
    ax.autoscale_view()
    fig.tight_layout()

    if save_path is not None:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
