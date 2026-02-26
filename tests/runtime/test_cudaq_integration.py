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

# pylint: disable=redefined-outer-name,import-outside-toplevel

"""
Integration tests for the CUDA-Q -> qBraid SDK pipeline.

Verifies that CUDA-Q kernels can be serialized, transpiled, and integrated
with the qBraid runtime provider.
"""

import base64
from unittest.mock import Mock

import pytest
from qbraid_core.services.runtime.schemas import Program, RuntimeDevice

try:
    import cudaq

    from qbraid import transpile
    from qbraid.programs import ProgramSpec
    from qbraid.programs.gate_model.cudaq import CudaQKernel
    from qbraid.runtime.native import QbraidProvider
    from qbraid.runtime.native.provider import _serialize_cudaq

    cudaq_not_installed = False
except ImportError:
    cudaq_not_installed = True

pytestmark = pytest.mark.skipif(cudaq_not_installed, reason="cudaq not installed")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def bell_kernel():
    """Return a simple 2-qubit Bell-state cudaq kernel (H, CX, MZ)."""
    kernel = cudaq.make_kernel()
    qubits = kernel.qalloc(2)
    kernel.h(qubits[0])
    kernel.cx(qubits[0], qubits[1])
    kernel.mz(qubits)
    return kernel


@pytest.fixture
def bell_cudaq_kernel(bell_kernel):
    """Return a ``CudaQKernel`` wrapper around the Bell-state kernel."""
    return CudaQKernel(bell_kernel)


# ---------------------------------------------------------------------------
# 1. Serialization to QIR
# ---------------------------------------------------------------------------


def test_cudaq_kernel_serializes_to_qir(bell_cudaq_kernel):
    """CudaQKernel.serialize() produces a valid base64-encoded QIR Program."""
    result = bell_cudaq_kernel.serialize()

    assert isinstance(result, Program)
    assert result.format == "qir.ll"
    assert result.data  # non-empty

    # Verify data is valid base64
    decoded = base64.b64decode(result.data.encode("utf-8"))
    assert len(decoded) > 0


# ---------------------------------------------------------------------------
# 2. Serialization to OpenQASM 2
# ---------------------------------------------------------------------------


def test_cudaq_kernel_serializes_to_openqasm2(bell_cudaq_kernel):
    """CudaQKernel.serialize(output_format='openqasm2') returns QASM2."""
    result = bell_cudaq_kernel.serialize(output_format="openqasm2")

    assert isinstance(result, Program)
    assert result.format == "qasm2"
    assert "OPENQASM" in result.data


# ---------------------------------------------------------------------------
# 3. Parameterized kernel with args
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    reason="cudaq.synthesize has a recursion bug in cudaq <= 0.12 with make_kernel(int). "
    "Fixed in newer cudaq versions.",
    raises=(RecursionError, ValueError),
    strict=False,
)
def test_cudaq_kernel_with_args():
    """A parameterized kernel bound via args reports correct num_qubits and serializes."""
    kernel, n = cudaq.make_kernel(int)
    qubits = kernel.qalloc(n)
    kernel.h(qubits[0])

    wrapper = CudaQKernel(kernel, args=(3,))

    assert wrapper.num_qubits == 3
    run_input = wrapper.serialize()
    assert isinstance(run_input, Program)
    assert run_input.data  # non-empty


# ---------------------------------------------------------------------------
# 4. with_args returns a new instance (immutability)
# ---------------------------------------------------------------------------


def test_cudaq_kernel_with_args_immutable(bell_kernel):
    """CudaQKernel.with_args returns a NEW instance, leaving the original unchanged."""
    original = CudaQKernel(bell_kernel)
    clone = original.with_args(3)

    assert clone is not original
    assert isinstance(clone, CudaQKernel)
    # The original should still have no bound args
    assert original._args is None
    assert clone._args == (3,)


# ---------------------------------------------------------------------------
# 5. Invalid serialization format
# ---------------------------------------------------------------------------


def test_cudaq_kernel_serialize_invalid_format(bell_cudaq_kernel):
    """serialize() raises ValueError for an unsupported output_format."""
    with pytest.raises(ValueError, match="Unsupported output_format"):
        bell_cudaq_kernel.serialize(output_format="invalid")


# ---------------------------------------------------------------------------
# 6. qbraid.transpile to qasm2
# ---------------------------------------------------------------------------


def test_cudaq_transpile_to_qasm2(bell_kernel):
    """qbraid.transpile(cudaq_kernel, 'qasm2') returns an OpenQASM 2 string."""
    result = transpile(bell_kernel, "qasm2")

    assert isinstance(result, str)
    assert "OPENQASM" in result


# ---------------------------------------------------------------------------
# 7. _serialize_cudaq provider helper
# ---------------------------------------------------------------------------


def test_serialize_cudaq_provider_lambda(bell_kernel):
    """_serialize_cudaq wraps a raw cudaq kernel and returns a QIR Program."""
    program = _serialize_cudaq(bell_kernel)

    assert isinstance(program, Program)
    assert program.format == "qir.ll"
    assert program.data  # non-empty


# ---------------------------------------------------------------------------
# 8. QbraidProvider builds a profile with cudaq ProgramSpec (mocked)
# ---------------------------------------------------------------------------


def test_qbraid_provider_builds_cudaq_profile():
    """QbraidProvider._build_runtime_profile includes cudaq in the ProgramSpec
    when the device advertises 'cudaq' in its runInputTypes."""
    device_data = {
        "_id": "mock_cudaq_device_id",
        "vrn": "cudaq_mock_sim",
        "runInputTypes": ["cudaq", "qasm2"],
        "numberQubits": 32,
        "noiseModels": [],
        "statusMsg": None,
        "nextAvailable": None,
        "avgQueueTime": None,
        "visibility": "public",
        "verified": "verified",
        "activeVersion": "v1",
        "providerId": "mock_provider_id",
        "qrn": "qbraid:mock:sim:cudaq-sv",
        "__v": 0,
        "createdAt": "2025-08-15T21:37:29.555Z",
        "modality": None,
        "name": "Mock CUDA-Q Simulator",
        "paradigm": "gate_model",
        "pricing": {"perTask": 0, "perShot": 0, "perMinute": 0},
        "status": "ONLINE",
        "updatedAt": "2025-08-15T21:37:29.555Z",
        "vendor": "qbraid",
        "image": None,
        "description": "Mock simulator supporting CUDA-Q kernels",
        "deviceType": "SIMULATOR",
        "queueDepth": 0,
        "directAccess": True,
        "pricingModel": "fixed",
        "notes": None,
    }

    device_model = RuntimeDevice.model_validate(device_data)

    mock_client = Mock()
    provider = QbraidProvider(client=mock_client)
    profile = provider._build_runtime_profile(device_model)

    # The device lists two runInputTypes → profile.program_spec should be a list
    specs = profile.program_spec
    assert isinstance(specs, list)

    aliases = [s.alias for s in specs]
    assert "cudaq" in aliases

    # Find the cudaq spec and verify it has a serialize callable
    cudaq_spec = next(s for s in specs if s.alias == "cudaq")
    assert cudaq_spec.serialize is not None
