# Copyright 2025 qBraid
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
Module providing calibration-based qubit selection helpers for QbraidDevice

"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qbraid_core.services.runtime.schemas import DeviceCalibration


def qubit_costs(calibration: DeviceCalibration) -> dict[int, float]:
    """Per-qubit cost as ``-log(fidelity)``, folding readout and gate errors.

    Metrics that are unpublished (``None``) contribute nothing, so a qubit is
    never penalized for data the provider does not report.
    """
    costs: dict[int, float] = {}
    for qubit_id, qubit in calibration.qubits.items():
        fidelity = 1.0
        if qubit.readout_error is not None:
            fidelity *= 1.0 - qubit.readout_error
        for error in (qubit.gate_error or {}).values():
            if error is not None:
                fidelity *= 1.0 - error
        costs[int(qubit_id)] = -math.log(fidelity) if fidelity > 0 else math.inf
    return costs


def edge_costs(
    calibration: DeviceCalibration, gate: str | None = None
) -> dict[tuple[int, int], float]:
    """Per-edge cost as ``-log(1 - error)``, keyed by normalized qubit pair.

    When ``gate`` is None, each edge takes the lowest error among its
    calibrated two-qubit gates (the best gate available on that pair).
    """
    available: set[str] = set()
    errors: dict[tuple[int, int], float] = {}
    for gate_map in calibration.edges.values():
        for gate_name, entries in gate_map.items():
            available.add(gate_name)
            if gate is not None and gate_name != gate:
                continue
            for entry in entries:
                if entry.value is None:
                    continue
                pair = (min(entry.source, entry.target), max(entry.source, entry.target))
                if pair not in errors or entry.value < errors[pair]:
                    errors[pair] = entry.value
    if gate is not None and gate not in available:
        raise ValueError(
            f"Gate '{gate}' has no calibrated edges on this device. "
            f"Available gates: {sorted(available)}"
        )
    return {
        pair: -math.log(1.0 - error) if error < 1 else math.inf for pair, error in errors.items()
    }


def best_chain(
    node_costs: dict[int, float],
    edge_costs_map: dict[tuple[int, int], float],
    length: int,
) -> list[int] | None:
    """Simple path of ``length`` qubits minimizing summed node and edge costs.

    Exhaustive depth-first search with branch-and-bound pruning. On sparse
    hardware lattices this is fast for the chain lengths circuits use in
    practice; it is not intended for lengths approaching the full device.
    """
    adjacency: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for (node_a, node_b), cost in edge_costs_map.items():
        if math.isfinite(cost):
            adjacency[node_a].append((node_b, cost))
            adjacency[node_b].append((node_a, cost))
    for neighbors in adjacency.values():
        neighbors.sort(key=lambda item: (item[1], item[0]))

    best_cost = math.inf
    best_path: list[int] = []

    def extend(path: list[int], in_path: set[int], cost: float) -> None:
        nonlocal best_cost, best_path
        if cost >= best_cost:
            return
        if len(path) == length:
            best_cost, best_path = cost, list(path)
            return
        for neighbor, edge_cost in adjacency[path[-1]]:
            if neighbor in in_path:
                continue
            in_path.add(neighbor)
            path.append(neighbor)
            extend(path, in_path, cost + edge_cost + node_costs.get(neighbor, 0.0))
            path.pop()
            in_path.remove(neighbor)

    for start in sorted(adjacency):
        extend([start], {start}, node_costs.get(start, 0.0))

    if not best_path:
        return None
    if best_path[0] > best_path[-1]:
        best_path.reverse()
    return best_path
