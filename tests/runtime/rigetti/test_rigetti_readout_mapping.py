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

# pylint: disable=no-name-in-module,possibly-used-before-assignment

"""
Cross-layer tests tying the OpenQASM 2 -> pyQuil conversion to the bitstring
``RigettiJob`` ultimately returns.

"""

from __future__ import annotations

import importlib.util
import re
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from .conftest import DUMMY_JOB_ID

rigetti_deps_found = (
    importlib.util.find_spec("pyquil") is not None
    and importlib.util.find_spec("qcs_sdk") is not None
)
pytestmark = pytest.mark.skipif(not rigetti_deps_found, reason="Rigetti dependencies not installed")

if rigetti_deps_found:
    from qbraid.runtime.rigetti.job import RigettiJob
    from qbraid.transpiler.conversions.qasm2 import qasm2_to_pyquil

if TYPE_CHECKING:
    from qbraid.runtime.rigetti.device import RigettiDevice


def _make_execution_results(readout_data: dict[str, list[int]]) -> MagicMock:
    """Build a mock ExecutionResults exposing ``buffers`` and ``memory``."""
    buffers = {}
    for readout_key, values in readout_data.items():
        buf = MagicMock()
        buf.data = values
        buffers[readout_key] = buf

    exec_results = MagicMock()
    exec_results.buffers = buffers
    exec_results.memory = {}
    return exec_results


def test_qasm2_creg_bit_lands_at_the_matching_bitstring_position(
    rigetti_device: RigettiDevice,
) -> None:
    """A QASM2 creg bit ends up at that same position in the returned bitstring.

    Spans the whole chain the Rigetti path depends on: ``qasm2_to_pyquil`` assigns the
    ``ro`` indices, QCS reports one readout buffer per ``ro[k]``, and
    ``RigettiJob._parse_results`` concatenates them into a bitstring. A wrong index
    anywhere along that chain returns confidently wrong counts rather than raising,
    which is why this is asserted end to end and not on the converter's output alone.

    Measurements are deliberately written out of order and across two cregs, since the
    ordering is exactly what the previous Cirq-routed conversion lost.
    """
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[5];
    creg a[2];
    creg b[3];
    measure q[2] -> b[0];
    measure q[0] -> a[1];
    measure q[4] -> b[2];
    measure q[1] -> a[0];
    measure q[3] -> b[1];
    """
    # read straight off the source: a[0:2] -> ro[0:2], b[0:3] -> ro[2:5]
    source_bit_of_qubit = {2: 2, 0: 1, 4: 4, 1: 0, 3: 3}
    qubit_value = {0: 1, 1: 0, 2: 0, 3: 1, 4: 1}

    program = qasm2_to_pyquil(qasm)
    converted = {
        int(qubit): int(bit)
        for qubit, bit in re.findall(r"^MEASURE (\d+) ro\[(\d+)\]$", program.out(), re.MULTILINE)
    }
    assert converted == source_bit_of_qubit

    # one readout buffer per ro[k], exactly as the QCS translation service reports them
    ro_sources = {f"ro[{bit}]": f"buf{bit}" for bit in converted.values()}
    readout_data = {f"buf{bit}": [qubit_value[qubit]] for qubit, bit in converted.items()}

    job = RigettiJob(
        job_id=DUMMY_JOB_ID,
        device=rigetti_device,
        num_shots=1,
        ro_sources=ro_sources,
    )
    # pylint: disable-next=protected-access
    result = job._parse_results(_make_execution_results(readout_data))

    # position k of the bitstring is the qubit the source measured into flat bit k
    expected = "".join(
        str(qubit_value[qubit])
        for bit in range(5)
        for qubit, mapped in source_bit_of_qubit.items()
        if mapped == bit
    )
    assert expected == "01011"
    assert result.measurement_counts == {expected: 1}
