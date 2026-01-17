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

# pylint: disable=redefined-outer-name,unused-argument,too-many-lines

"""
Unit tests for QbraidDevice and QbraidProvider classes.

"""
import importlib.util
import json
import logging
import time
from typing import Any
from unittest.mock import Mock, patch

import cirq
import numpy as np
import pytest
from qbraid_core.services.runtime.schemas import Program, RuntimeDevice

from qbraid._caching import cache_disabled
from qbraid.programs import ExperimentType, ProgramSpec, unregister_program_type
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.typer import IonQDict
from qbraid.runtime import Result, TargetProfile, ValidationLevel
from qbraid.runtime.exceptions import ProgramValidationError, ResourceNotFoundError
from qbraid.runtime.native import QbraidDevice, QbraidJob, QbraidProvider
from qbraid.runtime.native.provider import (
    _serialize_sequence,
    get_program_spec_lambdas,
    validate_qasm_no_measurements,
)
from qbraid.runtime.noise import NoiseModel
from qbraid.runtime.options import RuntimeOptions
from qbraid.runtime.result_data import AnnealingResultData, GateModelResultData
from qbraid.transpiler import Conversion, ConversionGraph, ConversionScheme, ProgramConversionError

from ._resources import DEVICE_DATA_QIR, JOB_DATA_NEC, JOB_DATA_QIR, RESULTS_DATA_NEC, MockDevice

# Skip pulser tests if not installed
pulser_found = importlib.util.find_spec("pulser") is not None

if pulser_found:
    from .azure.test_azure_remote import (  # pylint: disable=unused-import # noqa: F401
        pulser_sequence,
    )


@pytest.fixture
def mock_nec_va_profile():
    """Mock profile for testing."""
    return TargetProfile(
        device_id="qbraid:nec:sim:vector-annealer",
        simulator=True,
        experiment_type=ExperimentType.ANNEALING,
        program_spec=QbraidProvider._get_program_spec("qubo", "qbraid:nec:sim:vector-annealer"),
    )


@pytest.fixture
def mock_scheme():
    """Mock conversion scheme for testing."""
    conv1 = Conversion("alice", "bob", lambda x: x + 1)
    conv2 = Conversion("bob", "charlie", lambda x: x - 1)
    graph = ConversionGraph(conversions=[conv1, conv2])
    scheme = ConversionScheme(conversion_graph=graph)
    return scheme


@pytest.fixture
def mock_qbraid_device(mock_profile, mock_scheme, mock_client):
    """Mock QbraidDevice for testing."""
    return QbraidDevice(profile=mock_profile, client=mock_client, scheme=mock_scheme)


@pytest.fixture
def mock_nec_va_device(mock_nec_va_profile, mock_client):
    """Mock NEC vector annealer device."""
    return QbraidDevice(profile=mock_nec_va_profile, client=mock_client)


def counts_to_measurements(counts: dict[str, Any]) -> np.ndarray:
    """Convert counts dictionary to measurements array."""
    measurements = []
    for state, count in counts.items():
        measurements.extend([list(map(int, state))] * count)
    return np.array(measurements, dtype=int)


def is_uniform_comput_basis(array: np.ndarray) -> bool:
    """
    Check if each measurement (row) in the array represents a uniform computational basis
    state, i.e., for each shot, that qubit measurements are either all |0⟩s or all |1⟩s.

    Args:
        array (np.ndarray): A 2D numpy array where each row represents a measurement shot,
                            and each column represents a qubit's state in that shot.

    Returns:
        bool: True if every measurement is in a uniform computational basis state
              (all |0⟩s or all |1⟩s). False otherwise.

    Raises:
        ValueError: If the given array is not 2D.
    """
    if array.ndim != 2:
        raise ValueError("The input array must be 2D.")

    for shot in array:
        # Check if all qubits in the shot are measured as |0⟩ or all as |1⟩
        if not (np.all(shot == 0) or np.all(shot == 1)):
            return False
    return True


def test_provider_equality(mock_provider, mock_client):
    """Test equality of provider instances."""
    assert mock_provider == QbraidProvider(client=mock_client)
    assert mock_provider != mock_client


def test_qbraid_device_str_representation(mock_qbraid_device):
    """Test string representation of QbraidDevice."""
    assert str(mock_qbraid_device) == "QbraidDevice('qbraid:qbraid:sim:qir-sv')"


@pytest.mark.skipif(importlib.util.find_spec("pyqir") is None, reason="pyqir is not installed")
def test_qir_simulator_workflow(mock_provider, cirq_uniform):
    """Test qir simulator qbraid device job submission and result retrieval."""
    circuit = cirq_uniform(num_qubits=5)

    provider = mock_provider
    device = provider.get_device("qbraid:qbraid:sim:qir-sv")

    shots = 10
    job = device.run(circuit, shots=shots)
    assert isinstance(job, QbraidJob)
    assert job.is_terminal_state()

    batch_job = device.run([circuit], shots=shots)
    assert isinstance(batch_job, list)
    assert all(isinstance(job, QbraidJob) for job in batch_job)

    result = job.result()
    assert isinstance(result, Result)
    assert isinstance(result.data, GateModelResultData)
    assert repr(result.data).startswith("GateModelResultData")
    assert result.success
    assert result.job_id == JOB_DATA_QIR["jobQrn"]
    assert result.device_id == JOB_DATA_QIR["deviceQrn"]

    counts = result.data.get_counts()
    probabilities = result.data.get_probabilities()
    assert len(counts) == len(probabilities) == 2
    assert sum(probabilities.values()) == 1.0
    assert is_uniform_comput_basis(result.data.measurements)

    # Note: result.details structure may vary by result format
    # These assertions check for optional fields that may or may not be present
    if "shots" in result.details:
        assert result.details["shots"] == shots
    if "timeStamps" in result.details:
        assert isinstance(result.details["timeStamps"].get("executionDuration"), (int, type(None)))

    with pytest.warns(DeprecationWarning, match=r"Call to deprecated function measurement_counts*"):
        assert result.measurement_counts() == counts

    with pytest.warns(DeprecationWarning, match=r"Call to deprecated function measurements*"):
        assert is_uniform_comput_basis(result.measurements())


def test_nec_vector_annealer_workflow(mock_provider):
    """Test NEC Vector Annealer job submission and result retrieval."""
    provider = mock_provider
    device = provider.get_device("qbraid:nec:sim:vector-annealer")
    coefficients = {("x1", "x1"): 3.0, ("x1", "x2"): 2.0}
    quadratic = {json.dumps(key): value for key, value in coefficients.items()}
    payload_data = {"quadratic": quadratic, "offset": 0.0}
    # Create Program object for NEC annealing
    program = Program(format="problem", data=json.dumps(payload_data))
    job = device.submit(program, shots=100)
    assert isinstance(job, QbraidJob)
    assert job.is_terminal_state()

    result = job.result()
    assert isinstance(result, Result)
    assert isinstance(result.data, AnnealingResultData)
    assert result.success
    assert result.job_id == JOB_DATA_NEC["jobQrn"]
    assert result.device_id == JOB_DATA_NEC["deviceQrn"]
    assert result.data._solutions == RESULTS_DATA_NEC["solutions"]


@pytest.mark.skipif(importlib.util.find_spec("pyqir") is None, reason="pyqir is not installed")
def test_run_forbidden_kwarg(mock_provider):
    """Test that invoking run method with forbidden kwarg raises value error."""
    circuit = Mock()
    provider = mock_provider
    device = provider.get_device("qbraid:qbraid:sim:qir-sv")

    device.update_scheme(conversion_graph=ConversionGraph())

    with pytest.raises(ValueError):
        device.run(circuit, shots=10, num_qubits=5)


def test_device_update_scheme(mock_qbraid_device):
    """Test updating ConversionScheme."""
    graph = mock_qbraid_device.scheme.conversion_graph.copy()
    new_conversion = Conversion("charlie", "alice", lambda x: x)
    graph.add_conversion(new_conversion)

    assert graph != mock_qbraid_device.scheme.conversion_graph

    mock_qbraid_device.update_scheme(conversion_graph=graph)

    assert graph == mock_qbraid_device.scheme.conversion_graph


def test_device_noisey_run_raises_for_unsupported(mock_qbraid_device):
    """Test raising exception when noise model is not supported."""
    with pytest.raises(ValueError):
        mock_qbraid_device.run(Mock(), noise_model=NoiseModel("amplitude_damping"))


def test_provider_initialize_client_raises_for_multiple_auth_params(mock_client):
    """Test raising exception when initializing client if provided
    both an api key and a client object."""
    with pytest.raises(ValueError):
        QbraidProvider(api_key="abc123", client=mock_client)


def test_provider_resource_not_found_error_for_bad_api_key():
    """Test raising ResourceNotFoundError when the client fails to authenticate."""
    provider = QbraidProvider(api_key="abc123")
    with pytest.raises(ResourceNotFoundError):
        _ = provider.client


@patch("qbraid.runtime.native.provider.QuantumRuntimeClient")
def test_provider_client_from_valid_api_key(client, mock_client):
    """Test a valid API key."""
    client.return_value = mock_client
    provider = QbraidProvider(api_key="abc123")
    assert provider.client == mock_client


def test_provider_get_devices(mock_client):
    """Test getting devices from the client."""
    client = mock_client
    provider = QbraidProvider(client=client)
    devices = provider.get_devices()
    assert len(devices) >= 1
    # Filter for the QIR simulator device
    qir_device = next((d for d in devices if d.id == "qbraid:qbraid:sim:qir-sv"), None)
    assert qir_device is not None
    assert qir_device.id == "qbraid:qbraid:sim:qir-sv"


def test_provider_get_devices_raises_for_no_results(mock_client):
    """Test raising ResourceNotFoundError when no devices are found."""
    # This test checks that get_device raises an error for a non-existent device
    client = mock_client
    provider = QbraidProvider(client=client)
    with pytest.raises(ResourceNotFoundError, match="Device .* not found"):
        provider.get_device("nonexistent:device:id")


def test_provider_get_cached_devices(mock_client, device_data_qir, monkeypatch):
    """Test getting devices from the cache."""
    monkeypatch.setenv("DISABLE_CACHE", "0")

    data = device_data_qir.copy()

    client = mock_client
    provider = QbraidProvider(client=client)
    client.list_devices = Mock()
    client.list_devices.return_value = [RuntimeDevice.model_validate(data["data"])]

    _ = provider.get_devices()

    # second call should be from cache
    _ = provider.get_devices()
    client.list_devices.assert_called_once()

    provider.get_devices.cache_clear()


def test_provider_get_devices_post_cache_expiry(mock_client, device_data_qir, monkeypatch):
    """Test that the cache entry is invalidated when the cache is too old."""
    monkeypatch.setenv("DISABLE_CACHE", "0")
    monkeypatch.setenv("_QBRAID_TEST_CACHE_CALLS", "1")

    data = device_data_qir.copy()

    client = mock_client
    provider = QbraidProvider(client=client)
    client.list_devices = Mock()
    client.list_devices.return_value = [RuntimeDevice.model_validate(data["data"])]

    init_time = time.time()
    device_ttl = 120
    _ = provider.get_devices()

    # second call should not come from cache
    with patch("time.time", return_value=init_time + device_ttl + 5):
        _ = provider.get_devices()
    assert client.list_devices.call_count == 2


def test_provider_get_devices_bypass_cache(mock_client, device_data_qir, monkeypatch):
    """Test that the cache is bypassed when the bypass_cache flag is set."""
    monkeypatch.setenv("DISABLE_CACHE", "0")
    monkeypatch.setenv("_QBRAID_TEST_CACHE_CALLS", "1")

    data = device_data_qir.copy()

    client = mock_client
    provider = QbraidProvider(client=client)
    client.list_devices = Mock()
    client.list_devices.return_value = [RuntimeDevice.model_validate(data["data"])]

    with cache_disabled(provider):
        assert provider.__cache_disabled is True  # pylint: disable=no-member
        _ = provider.get_devices()

    assert provider.__cache_disabled is False  # pylint: disable=no-member
    assert client.list_devices.call_count == 1
    provider.get_devices.cache_clear()


def test_provider_search_devices_raises_for_bad_client(mock_client):
    """Test raising ResourceNotFoundError when the client fails to authenticate."""
    provider = QbraidProvider(client=mock_client)
    # Mock client.list_devices to raise an error
    mock_client.list_devices = Mock(side_effect=ValueError("Invalid status"))
    with pytest.raises(ResourceNotFoundError, match="No devices found matching given criteria"):
        provider.get_devices()


def test_provider_program_spec_none():
    """Test getting program spec when it is None."""
    assert QbraidProvider._get_program_spec(None, "device_id") is None


def test_device_queue_depth_raises(mock_basic_device):
    """Test raising exception when queue depth is unavailable."""
    with pytest.raises(ResourceNotFoundError):
        mock_basic_device.queue_depth()


def test_device_queue_depth(mock_qbraid_device):
    """Test getting queue depth."""
    assert mock_qbraid_device.queue_depth() == 0


def test_device_metadata(mock_basic_device):
    """Test getting device metadata."""
    metadata = mock_basic_device.metadata()
    assert metadata["device_id"] == "qbraid:qbraid:sim:qir-sv"
    assert metadata["simulator"] is True
    assert metadata["num_qubits"] == 64


def test_failed_circuit_conversion(mock_basic_device, mock_scheme):
    """Test raising exception when circuit conversion fails."""

    class FailMockTypeA:
        """Mock type for testing."""

    class FailMockTypeB:
        """Mock type for testing."""

    fake_spec = ProgramSpec(FailMockTypeA, alias="alice")
    mock_basic_device._target_spec = ProgramSpec(FailMockTypeB, alias="charlie")
    mock_basic_device._scheme = mock_scheme
    mock_input = FailMockTypeA()
    with pytest.raises(ProgramConversionError):
        mock_basic_device.transpile(mock_input, fake_spec)

    mock_basic_device._target_spec = None
    assert mock_basic_device.transpile(mock_input, fake_spec) == mock_input

    unregister_program_type("alice")
    unregister_program_type("charlie")


def test_wrong_type_conversion(mock_basic_device):
    """Test raising exception when circuit conversion fails due to wrong type."""

    class MockTypeA:
        """Mock type for testing."""

        def __init__(self, x):
            self.x = x

        def __add__(self, other):
            return MockTypeA(self.x + other.x)

        def __eq__(self, other):
            return self.x == other.x

    class MockTypeB:
        """Mock type for testing."""

        def __init__(self, x):
            self.x = x

        def __add__(self, other):
            return MockTypeB(self.x + other.x)

        def __eq__(self, other):
            return self.x == other.x

    conv1 = Conversion("alice", "charlie", lambda x: x + MockTypeA(1))
    graph = ConversionGraph(conversions=[conv1])
    scheme = ConversionScheme(conversion_graph=graph)

    fake_spec = ProgramSpec(MockTypeA, alias="alice", overwrite=True)
    mock_basic_device._target_spec = ProgramSpec(MockTypeB, alias="charlie", overwrite=True)
    mock_basic_device._scheme = scheme
    mock_input = MockTypeA(1)
    with pytest.raises(ProgramConversionError):
        mock_basic_device.transpile(mock_input, fake_spec)

    unregister_program_type("alice")
    unregister_program_type("charlie")


class FakeSession:
    """Mock session for testing."""

    def save_config(self, **kwargs):  # pylint: disable=unused-argument
        """Mock save configuration."""
        return None


class FakeClient:
    """Mock client for testing."""

    def __init__(self, api_key=None):  # pylint: disable=unused-argument
        self.session = FakeSession()

    def get_device(self, qbraid_id):
        """Mock get device."""
        raise ValueError("Device not found")


def test_save_config():
    """Test saving configuration."""
    provider = QbraidProvider(client=FakeClient())
    try:
        provider.save_config(param1="value1", param2="value2")
    except Exception:  # pylint: disable=broad-except
        pytest.fail("save_config raised an exception unexpectedly")


def test_get_device_fail():
    """Test raising exception when device is not found."""
    provider = QbraidProvider(client=FakeClient())
    with pytest.raises(ResourceNotFoundError):
        provider.get_device("qbraid:qbraid:sim:qir-sv")


def test_set_options(mock_qbraid_device: QbraidDevice):
    """Test updating the default runtime options."""
    default_options = {"transpile": True, "transform": True, "validate": 2, "prepare": True}
    assert dict(mock_qbraid_device._options) == default_options

    mock_qbraid_device.set_options(transform=False)
    updated_options = default_options.copy()
    updated_options["transform"] = False
    assert dict(mock_qbraid_device._options) == updated_options

    mock_qbraid_device.set_options(validate=False)
    assert mock_qbraid_device._options["validate"] == ValidationLevel.NONE


def test_set_options_raises_for_bad_key(mock_basic_device: MockDevice):
    """Test that the set options method raises AttributeError for key
    not already included in options."""
    with pytest.raises(AttributeError):
        mock_basic_device.set_options(bad_key=True)


@pytest.fixture
def mock_qbraid_client():
    """Mock client for testing."""
    client = Mock()
    client._user_metadata = {
        "valid": True,
        "userId": "6229769a21fff74352121c46",
        "userName": "jovyan",
        "userEmail": "jovyan@example.com",
        "metadata": {
            "acknowledgedTerms": "accepted",
            "tourUser": "completed",
            "acceptedIntelTerms": "accepted",
            "miningDetected": "not_detected",
        },
        "userRoles": ["organization_admin"],
        "userPermissions": [
            "global|organization|organization|manage",
            "global|organization|members|manage",
            "global|organization|billing|manage",
            "global|organization|device|manage",
            "global|organization|jobs|manage",
            "global|organization|projects|manage",
            "global|organization|users|view",
            "global|organization|users|create",
            "global|organization|users|update",
            "global|organization|users|delete",
            "global|organization|*|*",
            "global|organization|members|view",
            "global|organization|billing|view",
            "global|organization|resources|access",
            "global|organization|projects|view",
            "global|organization|jobs|submit",
            "global|labs|environments|install",
            "global|labs|environments|create",
            "global|organization|self|*",
            "global|*|provider|view",
            "custom|qbraid|organizations|create",
            "custom|qbraid|organizations|delete",
            "global|*|organization|update",
        ],
        "organizationId": "507f1f77bcf86cd799439011",
        "organizationUserId": "68f94f8e0c6d3502fd4c37f5",
    }
    client.session.api_key = "mock_api_key"
    return client


@patch("builtins.hash", autospec=True)
def test_hash_method_creates_and_returns_hash(mock_hash, mock_qbraid_client):
    """Test that the hash method creates and returns a hash."""
    mock_hash.return_value = 8888
    provider_instance = QbraidProvider(client=mock_qbraid_client)
    result = provider_instance.__hash__()  # pylint:disable=unnecessary-dunder-call
    org_user_id = "68f94f8e0c6d3502fd4c37f5"
    mock_hash.assert_called_once_with(("QbraidProvider", "mock_api_key", org_user_id))
    assert result == 8888
    assert provider_instance._hash == 8888


def test_hash_method_returns_existing_hash(mock_qbraid_client):
    """Test that the hash method returns an existing hash."""
    provider_instance = QbraidProvider(client=mock_qbraid_client)
    provider_instance._hash = 5678
    result = provider_instance.__hash__()  # pylint:disable=unnecessary-dunder-call
    assert result == 5678


def test_device_merge_options(mock_profile, mock_client):
    """ "Test merging default and custom options for a device."""
    options = RuntimeOptions(validate=0)
    device = QbraidDevice(profile=mock_profile, client=mock_client, options=options)

    default_options = device._default_options()
    assert device._options != default_options
    assert device._options != options
    assert default_options["validate"] == 2
    assert device._options["validate"] == 0

    device.set_options(validate=2)
    assert device._options == default_options


def test_device_validate_non_native_type_logs(mock_qbraid_device, caplog):
    """Test that validate method skips qubit count validation for non-native types."""
    mock_qbraid_device._target_spec = None

    with caplog.at_level(logging.INFO):
        mock_qbraid_device.validate([123])

    assert (
        "Skipping qubit count validation: program type 'int' not supported natively." in caplog.text
    )


def test_device_validate_level_none(mock_qbraid_device):
    """Test that validate returns immediately if validate level set to 0."""
    mock_qbraid_device.set_options(validate=0)

    with patch.object(mock_qbraid_device, "status") as mock_status:
        result = mock_qbraid_device.validate(["abc123"])
        assert result is None
        mock_status.assert_not_called()


def test_resolve_noise_model_raises_for_bad_input_type(mock_qbraid_device):
    """Test raising exception when given noise model is not a valid type."""
    with pytest.raises(ValueError) as excinfo:
        mock_qbraid_device._resolve_noise_model(10)
    assert "Invalid type for noise model" in str(excinfo)


def test_get_program_spec_not_registered_warning():
    """Test that a warning is emitted when the program type is not registered."""
    run_package = "not_registered"
    device_id = "fake_device"
    with pytest.warns(
        RuntimeWarning,
        match=(
            f"The default runtime configuration for device '{device_id}' includes "
            f"transpilation to program type '{run_package}', which is not registered."
        ),
    ):
        QbraidProvider._get_program_spec(run_package, device_id)


def test_get_program_spec_lambdas_validate_qasm_to_ionq():
    """Test that the validate lambda for qasm3 programs raises exception
    for CircuitConversion error though validate_qasm_to_ionq."""
    program_type_alias = "qasm3"
    device_id = "ionq_simulator"
    invalid_program = "invalid qasm3 code"

    lambdas = get_program_spec_lambdas(program_type_alias, device_id)
    validate = lambdas["validate"]

    with patch("qbraid.runtime.native.provider.transpile") as mock_convert:
        mock_convert.side_effect = ProgramConversionError("Invalid QASM3 code")

        with pytest.raises(
            ValueError,
            match=(
                f"OpenQASM programs submitted to the {device_id} "
                "must be compatible with IonQ JSON format."
            ),
        ):
            validate(invalid_program)

        mock_convert.assert_called_once_with(invalid_program, "ionq", max_path_depth=1)


def test_get_program_spec_lambdas_pulser():
    """Test that the validate lambda for pulser programs."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")
    program_type_alias = "pulser"
    device_id = "pasqal.sim.emu-tn"

    lambdas = get_program_spec_lambdas(program_type_alias, device_id)

    assert lambdas["validate"] is None
    assert lambdas["serialize"] is _serialize_sequence


@pytest.mark.skipif(not pulser_found, reason="pulser not installed")
def test_sequence_serializer(pulser_sequence):
    """Test the serialization of a Pasqal Pulser sequence."""
    pytest.importorskip("pulser", reason="Pasqal pulser package is not installed.")

    program = _serialize_sequence(pulser_sequence)

    assert program.format == "pulser.sequence"
    assert "sequence_builder" in program.data
    assert program.data["sequence_builder"] == json.loads(pulser_sequence.to_abstract_repr())


def test_provider_get_basis_gates_ionq():
    """Test getting basis gates for IonQ device."""
    basis_gates = QbraidProvider._get_basis_gates("ionq:ionq:sim:simulator")
    native = {"gpi", "gpi2", "ms", "zz"}
    unique = set(basis_gates)
    assert len(unique) == len(basis_gates) == 35
    assert native.issubset(unique)


@pytest.mark.parametrize(
    "program_spec, target_program_type_expected",
    [
        (None, None),
        (ProgramSpec(str, "qasm2"), "qasm2"),
        ([ProgramSpec(str, "qasm2"), ProgramSpec(str, "qasm3")], ["qasm2", "qasm3"]),
    ],
)
def test_device_metadata_for_different_program_specs(program_spec, target_program_type_expected):
    """Test getting device metadata for different program specs types: none, single and multiple."""
    profile = TargetProfile(
        device_id="fake_device",
        simulator=True,
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=42,
        program_spec=program_spec,
    )

    device = MockDevice(profile=profile)

    metadata = device.metadata()

    target_program_type = metadata["runtime_config"]["target_program_type"]
    assert (
        target_program_type is None
        if target_program_type_expected is None
        else set(target_program_type) == set(target_program_type_expected)
    )

    with pytest.raises(ProgramTypeError) as excinfo:
        device._get_target_spec(cirq.Circuit())
    assert "Could not find a target ProgramSpec matching the alias" in str(excinfo.value)


def test_device_transpile_program_conversion_error():
    """Test that transpile method handles program conversion error
    correctly for device with multiple program specs."""
    circuit = {
        "qubits": 3,
        "gateset": "qis",
        "circuit": [
            {"gate": "h", "target": 0},
            {"gate": "cnot", "control": 0, "target": 1},
            {"gate": "cnot", "control": 0, "target": 2},
        ],
    }

    profile = TargetProfile(
        device_id="fake_device",
        simulator=True,
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=42,
        program_spec=[ProgramSpec(str, "qasm2"), ProgramSpec(str, "qasm3")],
    )

    device = MockDevice(profile=profile)
    with pytest.raises(ProgramConversionError) as excinfo:
        device.transpile(circuit, ProgramSpec(IonQDict, "ionq"))
    assert "Transpile step failed after multiple attempts." in str(excinfo.value)


@pytest.fixture
def mock_qasm_profile():
    """Mock profile for testing."""
    return TargetProfile(
        device_id="mock_device",
        simulator=True,
        experiment_type=ExperimentType.GATE_MODEL,
        program_spec=[ProgramSpec(str, "qasm2"), ProgramSpec(str, "qasm3")],
    )


@pytest.fixture
def mock_qasm_device(mock_qasm_profile, mock_scheme, mock_client):
    """Mock QbraidDevice for testing."""
    return QbraidDevice(profile=mock_qasm_profile, client=mock_client, scheme=mock_scheme)


def test_set_target_program_type(mock_qbraid_device: QbraidDevice):
    """Test setting target spec."""
    target_spec = mock_qbraid_device._target_spec
    assert isinstance(target_spec, ProgramSpec)
    mock_qbraid_device.set_target_program_type(None)
    assert mock_qbraid_device._target_spec is None
    mock_qbraid_device.set_target_program_type(target_spec.alias)
    assert mock_qbraid_device._target_spec == target_spec


def test_set_target_program_type_multi_program_spec(mock_qasm_device: QbraidDevice):
    """Test setting target spec with multiple program specs."""
    target_spec = mock_qasm_device._target_spec
    assert isinstance(target_spec, list)
    assert all(isinstance(spec, ProgramSpec) for spec in target_spec)
    mock_qasm_device.set_target_program_type("qasm2")
    assert mock_qasm_device._target_spec.alias == "qasm2"
    mock_qasm_device.set_target_program_type("qasm3")
    assert mock_qasm_device._target_spec.alias == "qasm3"
    mock_qasm_device.set_target_program_type(["qasm2", "qasm3"])
    assert isinstance(mock_qasm_device._target_spec, list)
    assert all(isinstance(spec, ProgramSpec) for spec in mock_qasm_device._target_spec)
    assert len(mock_qasm_device._target_spec) == 2


def test_set_target_program_type_raises_for_multiple(mock_qasm_device: QbraidDevice):
    """Test setting target spec with multiple program specs."""
    with pytest.raises(ValueError):
        mock_qasm_device.set_target_program_type("qasm4")


def test_set_target_program_type_raises_for_single_invalid(mock_qbraid_device: QbraidDevice):
    """Test setting target spec raises ValueError for invalid alias."""
    with pytest.raises(ValueError):
        mock_qbraid_device.set_target_program_type("qasm4")


def test_set_target_program_type_raises_for_list_invalid(mock_qasm_device: QbraidDevice):
    """Test setting target spec raises if any alias in list is not in original spec."""
    with pytest.raises(ValueError):
        mock_qasm_device.set_target_program_type(["qasm2", "qasm4"])


def test_set_target_program_type_raises_for_list_if_spec_single(mock_qbraid_device: QbraidDevice):
    """Test setting target spec raises if list is given but spec expects single alias."""
    with pytest.raises(ValueError):
        mock_qbraid_device.set_target_program_type(["qasm2", "qasm4"])


def test_set_target_program_type_raises_for_duplicate(mock_qbraid_device: QbraidDevice):
    """Test setting target spec raises ValueError for duplicate alias input."""
    with pytest.raises(ValueError):
        mock_qbraid_device.set_target_program_type(["qasm3", "qasm3"])


@pytest.fixture
def mock_profile_program_spec_none():
    """Mock profile for testing with program_spec set to none"""
    return TargetProfile(
        device_id="mock_device",
        simulator=True,
        experiment_type=ExperimentType.GATE_MODEL,
        program_spec=None,
    )


@pytest.fixture
def mock_device_program_spec_none(mock_profile_program_spec_none, mock_client):
    """Mock QbraidDevice for testing with target profile program_spec set to None."""
    return QbraidDevice(profile=mock_profile_program_spec_none, client=mock_client)


def test_set_target_spec_raises_if_none(mock_device_program_spec_none: QbraidDevice):
    """Test setting target spec raises ValueError if program_spec is None."""
    with pytest.raises(ValueError):
        mock_device_program_spec_none.set_target_program_type("qasm2")


def test_device_validate_warns_for_too_many_qubits(mock_basic_device, cirq_uniform):
    """Test that validate warns when circuit has too many qubits with ValidationLevel.WARN."""
    circuit = cirq_uniform(num_qubits=100)  # More than device capacity
    mock_basic_device.set_options(validate=ValidationLevel.WARN)
    # Set target_spec to None to skip program spec validation
    mock_basic_device._target_spec = None

    with pytest.warns(
        UserWarning, match="Number of qubits in the circuit.*exceeds.*device's capacity"
    ):
        mock_basic_device.validate([circuit])


def test_device_validate_warns_for_invalid_program_spec(mock_qbraid_device, cirq_uniform):
    """Test that validate warns when program spec validation fails with ValidationLevel.WARN."""
    circuit = cirq_uniform(num_qubits=3)
    mock_qbraid_device.set_options(validate=ValidationLevel.WARN)

    # Mock a program spec that matches cirq but will fail validation
    # Set target_spec to match cirq so _get_target_spec doesn't raise
    mock_qbraid_device._target_spec = ProgramSpec(cirq.Circuit, alias="cirq")

    # Mock validate to raise ValueError to trigger warning
    with patch.object(
        mock_qbraid_device._target_spec, "validate", side_effect=ValueError("Invalid circuit")
    ):
        with pytest.warns(UserWarning, match="Invalid circuit"):
            mock_qbraid_device.validate([circuit])


def test_device_validate_raises_for_invalid_program_spec(mock_qbraid_device, cirq_uniform):
    """Test that validate raises ProgramValidationError when validation fails with RAISE level."""
    circuit = cirq_uniform(num_qubits=3)
    mock_qbraid_device.set_options(validate=ValidationLevel.RAISE)

    # Mock a program spec that matches cirq but will fail validation
    mock_qbraid_device._target_spec = ProgramSpec(cirq.Circuit, alias="cirq")

    # Mock validate to raise ValueError which should be wrapped in ProgramValidationError
    with patch.object(
        mock_qbraid_device._target_spec, "validate", side_effect=ValueError("Invalid circuit")
    ):
        with pytest.raises(ProgramValidationError, match="Invalid circuit"):
            mock_qbraid_device.validate([circuit])


def test_resolve_noise_model_raises_when_noise_models_not_supported(mock_client):
    """Test that _resolve_noise_model raises when device doesn't support noise models."""
    profile_no_noise = TargetProfile(
        device_id="test_device",
        simulator=True,
        noise_models=None,  # No noise models supported
    )
    device = QbraidDevice(profile=profile_no_noise, client=mock_client)

    with pytest.raises(ValueError, match="Noise models are not supported by this device"):
        device._resolve_noise_model("ideal")


def test_resolve_noise_model_with_noise_model_instance(mock_qbraid_device):
    """Test that _resolve_noise_model works with NoiseModel instance."""
    noise_model_str = mock_qbraid_device._resolve_noise_model(NoiseModel("ideal"))
    assert isinstance(noise_model_str, str)


def test_resolve_noise_model_raises_for_unsupported_model(mock_qbraid_device):
    """Test that _resolve_noise_model raises when noise model not in device's supported models."""
    with pytest.raises(ValueError, match="Noise model 'depolarizing' not supported by device"):
        mock_qbraid_device._resolve_noise_model("depolarizing")


def test_provider_get_devices_raises_when_no_direct_access_devices(mock_client):
    """Test that get_devices raises ResourceNotFoundError when no directAccess devices found."""
    provider = QbraidProvider(client=mock_client)
    # Mock client to return devices without directAccess
    device_data_no_direct = DEVICE_DATA_QIR.copy()
    device_data_no_direct["data"]["directAccess"] = False
    mock_client.list_devices = Mock()
    mock_client.list_devices.return_value = [
        RuntimeDevice.model_validate(device_data_no_direct["data"])
    ]

    with pytest.raises(ResourceNotFoundError, match="No devices found matching given criteria"):
        provider.get_devices()


def test_provider_get_device_raises_when_no_direct_access(mock_client):
    """Test that get_device raises ValueError when device doesn't support direct access."""
    provider = QbraidProvider(client=mock_client)
    # Mock client to return device without directAccess
    device_data_no_direct = DEVICE_DATA_QIR.copy()
    device_data_no_direct["data"]["directAccess"] = False
    mock_client.get_device = Mock()
    mock_client.get_device.return_value = RuntimeDevice.model_validate(
        device_data_no_direct["data"]
    )

    with pytest.raises(
        ValueError,
        match=(
            "qBraid does not currently support direct access to device 'qbraid:qbraid:sim:qir-sv'"
        ),
    ):
        provider.get_device("qbraid:qbraid:sim:qir-sv")


def test_qbraid_device_submit_with_noise_model(mock_qbraid_device):
    """Test that submit calls _resolve_noise_model when noise_model is provided."""
    test_program = Program(format="qasm3", data="OPENQASM 3.0; qubit[1] q; h q[0];")

    # Mock the client's create_job to return a job
    job_data_mock = Mock()
    job_data_mock.jobQrn = "test:job:qrn"
    mock_qbraid_device.client.create_job = Mock(return_value=job_data_mock)

    # Resolve noise model to get expected name
    expected_noise_model_name = mock_qbraid_device._resolve_noise_model(NoiseModel("ideal"))

    # Create runtime_options dict that will be modified in submit
    runtime_options_dict = {"noise_model": NoiseModel("ideal")}

    # Submit with noise_model in runtime_options
    job = mock_qbraid_device.submit(test_program, shots=100, runtime_options=runtime_options_dict)

    # Verify create_job was called and _resolve_noise_model path was executed
    assert mock_qbraid_device.client.create_job.called
    # Verify runtime_options dict was modified (noise_model popped, noiseModel added)
    assert "noise_model" not in runtime_options_dict
    assert runtime_options_dict.get("noiseModel") == expected_noise_model_name
    assert isinstance(job, QbraidJob)


def test_validate_qasm_no_measurements_with_measurements():
    """Test that validate_qasm_no_measurements raises ValueError when QASM has measurements."""
    qasm_with_measurements = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c[2];
    h q[0];
    measure q[0] -> c[0];
    """

    device_id = "quera_device"
    with pytest.raises(
        ValueError,
        match=f"OpenQASM programs submitted to the {device_id} cannot contain measurement gates",
    ):
        validate_qasm_no_measurements(qasm_with_measurements, device_id)


def test_validate_qasm_no_measurements_without_measurements():
    """Test that validate_qasm_no_measurements passes when QASM has no measurements."""
    qasm_no_measurements = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    h q[0];
    cx q[0], q[1];
    """

    device_id = "quera_device"
    # Should not raise
    validate_qasm_no_measurements(qasm_no_measurements, device_id)
