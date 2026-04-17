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
Remote tests for QIR simulator device via qBraid native runtime.

"""

import pyqir
import pytest
from qiskit import QuantumCircuit

from qbraid.runtime import DeviceStatus, JobStatus, QbraidProvider

DEFAULT_TIMEOUT = 120
DEVICE_ID = "qbraid:qbraid:sim:qir-sv"
SHOTS = 10


@pytest.fixture
def bell_qasm_circuit():
    """Create a Bell state circuit using Qiskit."""
    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])
    return circuit


@pytest.fixture
def bell_qir_module():
    """Create a Bell state circuit as a QIR module."""
    ctx = pyqir.Context()
    mod = pyqir.Module(ctx, "bell_pair")

    entry = pyqir.entry_point(mod, "main", required_num_qubits=2, required_num_results=2)
    builder = pyqir.Builder(ctx)
    builder.insert_at_end(pyqir.BasicBlock(ctx, "entry", entry))

    qis = pyqir.BasicQisBuilder(builder)
    q0 = pyqir.qubit(ctx, 0)
    q1 = pyqir.qubit(ctx, 1)
    r0 = pyqir.result(ctx, 0)
    r1 = pyqir.result(ctx, 1)

    qis.h(q0)
    qis.cx(q0, q1)
    qis.mz(q0, r0)
    qis.mz(q1, r1)

    i8_ptr = pyqir.PointerType(pyqir.IntType(ctx, 8))
    rt_type = pyqir.FunctionType(pyqir.Type.void(ctx), [pyqir.result_type(ctx), i8_ptr])
    rt_fn = pyqir.Function(
        rt_type, pyqir.Linkage.EXTERNAL, "__quantum__rt__result_record_output", mod
    )
    null_i8ptr = pyqir.Constant.null(i8_ptr)
    builder.call(rt_fn, [r0, null_i8ptr])
    builder.call(rt_fn, [r1, null_i8ptr])

    builder.ret(None)
    mod.verify()
    return mod


@pytest.mark.remote
def test_qir_simulator_qasm_circuit(bell_qasm_circuit):
    """Test submitting a QASM circuit to the QIR simulator device."""
    provider = QbraidProvider()
    device = provider.get_device(DEVICE_ID)

    device_status = device.status()
    if device_status != DeviceStatus.ONLINE:
        pytest.skip(f"{device.id} is {device_status.value}")

    job = device.run(bell_qasm_circuit, shots=SHOTS)

    try:
        job.wait_for_final_state(timeout=DEFAULT_TIMEOUT)
    except TimeoutError:
        try:
            job.cancel()
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        pytest.skip(f"Job did not complete within {DEFAULT_TIMEOUT} seconds")

    assert job.status() == JobStatus.COMPLETED


@pytest.mark.remote
def test_qir_simulator_qir_module(bell_qir_module):
    """Test submitting a QIR module to the QIR simulator device."""
    provider = QbraidProvider()
    device = provider.get_device(DEVICE_ID)

    device_status = device.status()
    if device_status != DeviceStatus.ONLINE:
        pytest.skip(f"{device.id} is {device_status.value}")

    job = device.run(bell_qir_module, shots=SHOTS)

    try:
        job.wait_for_final_state(timeout=DEFAULT_TIMEOUT)
    except TimeoutError:
        try:
            job.cancel()
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        pytest.skip(f"Job did not complete within {DEFAULT_TIMEOUT} seconds")

    assert job.status() == JobStatus.COMPLETED
