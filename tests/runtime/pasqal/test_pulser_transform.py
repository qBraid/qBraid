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
Unit tests for moving Pulser sequences onto a Pasqal QPU's Pulser device before submitting.

The FRESNEL_CAN1 specs fixture is Pasqal's public specs entry, saved so no test reaches
the network.

"""
# pylint: disable=redefined-outer-name

import json
import pathlib
import threading
import warnings
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import requests

pulser = pytest.importorskip("pulser")

# pylint: disable=wrong-import-position,wrong-import-order
from pulser import Pulse, Register, Sequence
from pulser.devices import AnalogDevice, MockDevice
from pulser.json.abstract_repr.deserializer import deserialize_device
from qbraid_core.services.runtime.schemas import Program

from qbraid.programs import ExperimentType, load_program, unregister_program_type
from qbraid.programs.analog.pulser import PulserSequence
from qbraid.programs.exceptions import ProgramTypeError, TransformError
from qbraid.runtime import DeviceStatus, TargetProfile
from qbraid.runtime.native import QbraidDevice, QbraidProvider
from qbraid.runtime.pasqal import PasqalDevice
from qbraid.runtime.pasqal import specs as pasqal_check
from qbraid.runtime.pasqal.device import PasqalDeviceError
from qbraid.runtime.pasqal.provider import _build_profile

# pylint: enable=wrong-import-position,wrong-import-order

QPU_ID = "pasqal:pasqal:qpu:fresnel-can1"
SPECS = json.loads(
    (pathlib.Path(__file__).parent / "pasqal_fresnel_can1_public_specs.json").read_text()
)


@pytest.fixture(autouse=True)
def specs_endpoint():
    """Serve the saved public specs, and start each test with no specs cached."""
    response = MagicMock()
    response.json.return_value = SPECS
    pasqal_check._reset_cache()  # pylint: disable=protected-access
    with patch.object(pasqal_check.requests, "get", return_value=response) as get:
        yield get
    pasqal_check._reset_cache()  # pylint: disable=protected-access


@pytest.fixture
def fresnel():
    """Pasqal's FRESNEL_CAN1 Pulser device."""
    return deserialize_device(SPECS["data"][0]["specs"])


def _sequence(register, device, duration=500, amplitude=np.pi):
    seq = Sequence(register, device)
    seq.declare_channel("ryd", "rydberg_global")
    seq.add(Pulse.ConstantPulse(duration, amplitude, 0.0, 0.0), "ryd")
    seq.measure("ground-rydberg")
    return seq


def _qpu(device_id=QPU_ID, simulator=False):
    """A stand-in for the device a sequence is transformed for."""
    return MagicMock(id=device_id, simulator=simulator)


def _transform(sequence, device_id=QPU_ID):
    """Transform ``sequence`` for ``device_id`` and return the transformed sequence."""
    program = load_program(sequence)
    program.transform(_qpu(device_id))
    return program.program


def _calibrated_register(device):
    layout = next(
        lay for lay in device.calibrated_register_layouts.values() if lay.number_of_traps == 60
    )
    return layout.define_register(29, 11, 47, qubit_ids=["q0", "q1", "q2"])


def test_device_type_from_qbraid_id():
    """The qBraid device ID maps to Pasqal's device type."""
    assert pasqal_check.pasqal_device_type(QPU_ID) == "FRESNEL_CAN1"


def test_sequence_built_on_fresnel_passes(fresnel):
    """A sequence on FRESNEL_CAN1 with a calibrated-layout register is accepted."""
    _transform(_sequence(_calibrated_register(fresnel), fresnel), QPU_ID)


def test_free_coordinates_are_rejected():
    """Pasqal's reason: 'FRESNEL_CAN1' requires the sequence's register to be defined from a
    RegisterLayout."""
    register = Register.from_coordinates([(0, 0), (10, 0)], prefix="q")
    with pytest.raises(
        TransformError, match="requires the sequence's register to be defined from a RegisterLayout"
    ):
        _transform(_sequence(register, AnalogDevice))


def test_uncalibrated_underfilled_layout_is_rejected():
    """Pasqal: 'The existing register is incompatible with the new device.'"""
    layout = next(iter(AnalogDevice.pre_calibrated_layouts))
    register = layout.define_register(0, 10, qubit_ids=["q0", "q1"])
    with pytest.raises(TransformError, match="register is not valid on FRESNEL_CAN1"):
        _transform(_sequence(register, AnalogDevice))


@pytest.mark.parametrize(
    "duration, amplitude, message",
    [(7000, np.pi, "at most 6000 ns"), (500, 20.0, "amplitude")],
)
def test_pulses_outside_fresnel_limits_are_rejected(fresnel, duration, amplitude, message):
    """A calibrated register on a permissive device must still fit FRESNEL_CAN1's channels."""
    seq = _sequence(_calibrated_register(fresnel), MockDevice, duration, amplitude)
    with pytest.raises(TransformError, match=message):
        _transform(seq)


def test_total_duration_over_the_limit_is_rejected(fresnel):
    """Pulses each within the limit can still add up to more than FRESNEL_CAN1 allows."""
    seq = Sequence(_calibrated_register(fresnel), MockDevice)
    seq.declare_channel("ryd", "rydberg_global")
    seq.add(Pulse.ConstantPulse(4000, np.pi, 0.0, 0.0), "ryd")
    seq.add(Pulse.ConstantPulse(4000, np.pi, 0.0, 0.0), "ryd")
    seq.measure("ground-rydberg")
    with pytest.raises(TransformError, match="maximum duration allowed by the device"):
        _transform(seq)


def test_errors_say_how_to_fix_it():
    """The message points to building on FRESNEL_CAN1 with a calibrated layout."""
    register = Register.from_coordinates([(0, 0), (10, 0)], prefix="q")
    with pytest.raises(TransformError, match="calibrated layouts"):
        _transform(_sequence(register, AnalogDevice))


def test_unreachable_specs_do_not_block_submission(specs_endpoint):
    """If Pasqal's specs cannot be read, the check is skipped rather than failing the job."""
    specs_endpoint.side_effect = requests.ConnectionError("offline")
    register = Register.from_coordinates([(0, 0), (10, 0)], prefix="q")
    _transform(_sequence(register, AnalogDevice))


def test_unknown_device_type_is_not_checked():
    """A Pasqal QPU without public specs is left to Pasqal's own validation."""
    register = Register.from_coordinates([(0, 0), (10, 0)], prefix="q")
    seq = _sequence(register, AnalogDevice)
    _transform(seq, "pasqal:pasqal:qpu:some-future-qpu")


def test_specs_are_fetched_once_within_the_ttl(specs_endpoint, fresnel):
    """Repeated submissions reuse the fetched specs."""
    seq = _sequence(_calibrated_register(fresnel), fresnel)
    for _ in range(3):
        _transform(seq)
    specs_endpoint.assert_called_once()


def test_specs_are_refetched_after_the_ttl(specs_endpoint, fresnel):
    """Recalibrations reach the check once the cached specs expire."""
    seq = _sequence(_calibrated_register(fresnel), fresnel)
    with patch.object(pasqal_check.time, "monotonic", return_value=1_000.0):
        _transform(seq)
    with patch.object(
        pasqal_check.time,
        "monotonic",
        return_value=1_000.0 + pasqal_check._SPECS_TTL_S + 1,  # pylint: disable=protected-access
    ):
        _transform(seq)
    assert specs_endpoint.call_count == 2


def _free_register_sequence():
    return _sequence(Register.from_coordinates([(0, 0), (10, 0)], prefix="q"), AnalogDevice)


@pytest.mark.parametrize("device", [AnalogDevice, MockDevice])
def test_valid_sequences_pass_with_warnings_as_errors(fresnel, device):
    """Pulser's deprecation and Rydberg-level warnings never turn into a rejection."""
    seq = _sequence(_calibrated_register(fresnel), device)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _transform(seq)


def test_concurrent_checks_leave_the_warning_filters_as_they_were(fresnel):
    """Checks run in parallel threads never leave a warning filter behind."""
    seq = _sequence(_calibrated_register(fresnel), AnalogDevice)
    _transform(seq)  # fetch the specs first
    before = list(warnings.filters)

    def _check():
        for _ in range(20):
            _transform(seq)

    threads = [threading.Thread(target=_check) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert list(warnings.filters) == before


def test_very_old_specs_are_not_reused_during_an_outage(specs_endpoint):
    """Specs past twice their lifetime are dropped while Pasqal is unreachable."""
    with patch.object(pasqal_check.time, "monotonic", return_value=1_000.0):
        with pytest.raises(TransformError, match="RegisterLayout"):
            _transform(_free_register_sequence())
    specs_endpoint.side_effect = requests.ConnectionError("offline")
    much_later = 1_000.0 + pasqal_check._MAX_STALE_S + 1  # pylint: disable=protected-access
    with patch.object(pasqal_check.time, "monotonic", return_value=much_later):
        _transform(_free_register_sequence())


def test_the_users_sequence_is_not_modified(fresnel):
    """Checking a sequence leaves it on the device it was built on."""
    seq = _sequence(_calibrated_register(fresnel), AnalogDevice)
    _transform(seq)
    assert seq.device is AnalogDevice


def test_mappable_and_parametrized_sequences_pass(fresnel):
    """A mappable register and declared variables are checked without being built."""
    layout = next(
        lay for lay in fresnel.calibrated_register_layouts.values() if lay.number_of_traps == 60
    )
    seq = Sequence(layout.make_mappable_register(3), fresnel)
    amp = seq.declare_variable("amp")
    seq.declare_channel("ryd", "rydberg_global")
    seq.add(Pulse.ConstantPulse(500, amp, 0.0, 0.0), "ryd")
    seq.measure("ground-rydberg")
    _transform(seq)


def test_a_failed_fetch_is_not_retried_on_every_submit(specs_endpoint):
    """An unreachable endpoint costs one attempt per failure window, not one per program."""
    specs_endpoint.side_effect = requests.ConnectionError("offline")
    for _ in range(3):
        _transform(_free_register_sequence())
    specs_endpoint.assert_called_once()


def test_last_good_specs_are_used_when_a_refresh_fails(specs_endpoint):
    """After the specs expire, a failed refresh falls back to the last specs read."""
    with patch.object(pasqal_check.time, "monotonic", return_value=1_000.0):
        with pytest.raises(TransformError, match="RegisterLayout"):
            _transform(_free_register_sequence())
    specs_endpoint.side_effect = requests.ConnectionError("offline")
    later = 1_000.0 + pasqal_check._SPECS_TTL_S + 1  # pylint: disable=protected-access
    with patch.object(pasqal_check.time, "monotonic", return_value=later):
        with pytest.raises(TransformError, match="RegisterLayout"):
            _transform(_free_register_sequence())
    assert specs_endpoint.call_count == 2


def test_an_unreadable_entry_does_not_drop_the_others(specs_endpoint):
    """A specs entry Pulser cannot read is skipped; FRESNEL_CAN1 is still checked."""
    bad = {"device_type": "FUTURE_QPU", "specs": "{not json"}
    specs_endpoint.return_value.json.return_value = {"data": [bad] + SPECS["data"]}
    with pytest.raises(TransformError, match="RegisterLayout"):
        _transform(_free_register_sequence())


def test_an_error_without_a_message_still_says_what_failed(fresnel):
    """Pulser raises some errors with no message; the rejection names the error instead."""
    seq = _sequence(_calibrated_register(fresnel), AnalogDevice)
    with patch.object(Sequence, "with_new_device", side_effect=TypeError()):
        with pytest.raises(TransformError, match="not valid on FRESNEL_CAN1: TypeError"):
            _transform(seq)


def test_the_sequence_is_moved_onto_the_qpu_device(fresnel):
    """The transformed sequence is built on FRESNEL_CAN1, as Pasqal will run it."""
    moved = _transform(_sequence(_calibrated_register(fresnel), AnalogDevice))
    assert moved.device.name == fresnel.name


def test_emulators_are_not_transformed():
    """Emulators accept any valid sequence, so the sequence is left as it is."""
    seq = _free_register_sequence()
    program = load_program(seq)
    program.transform(_qpu("pasqal:pasqal:sim:fresnel-can1", simulator=True))
    assert program.program is seq


def test_wrapper_rejects_other_types():
    """Only Pulser sequences are wrapped."""
    try:
        with pytest.raises(ProgramTypeError):
            PulserSequence(("invalid", "program"))
    finally:
        unregister_program_type("tuple")


def test_wrapper_counts_atoms_and_serializes(fresnel):
    """The atom count includes mappable registers; serialize gives the platform payload."""
    seq = _sequence(_calibrated_register(fresnel), fresnel)
    program = load_program(seq)
    assert program.num_qubits == 3
    payload = program.serialize()
    assert payload.format == "pulser.sequence"
    assert payload.data["sequence_builder"] == json.loads(seq.to_abstract_repr())

    layout = next(iter(fresnel.calibrated_register_layouts.values()))
    assert load_program(Sequence(layout.make_mappable_register(5), fresnel)).num_qubits == 5


def _pasqal_qpu(client: MagicMock) -> QbraidDevice:
    specs = QbraidProvider._get_program_specs(  # pylint: disable=protected-access
        ["pulser"], QPU_ID
    )
    profile = TargetProfile(
        device_id=QPU_ID,
        simulator=False,
        experiment_type=ExperimentType.ANALOG,
        num_qubits=100,
        program_spec=specs,
        provider_name="pasqal",
    )
    device = QbraidDevice(profile, client=client)
    device.status = MagicMock(return_value=DeviceStatus.ONLINE)
    return device


class _Submitted(Exception):
    """Raised by the mock client to stop after the job request is built."""


def test_device_run_rejects_before_submitting():
    """A sequence FRESNEL_CAN1 would reject never reaches the job request."""
    client = MagicMock()
    device = _pasqal_qpu(client)
    with pytest.raises(TransformError, match="RegisterLayout"):
        device.run(_free_register_sequence(), shots=10)
    client.create_job.assert_not_called()


def test_device_run_submits_the_sequence_on_the_qpu_device(fresnel):
    """A sequence built on AnalogDevice is submitted moved onto FRESNEL_CAN1."""
    client = MagicMock()
    client.create_job.side_effect = _Submitted
    device = _pasqal_qpu(client)
    with pytest.raises(_Submitted):
        device.run(_sequence(_calibrated_register(fresnel), AnalogDevice), shots=10)
    request = client.create_job.call_args.args[0]
    assert isinstance(request.program, Program)
    assert request.program.format == "pulser.sequence"
    assert request.program.data["sequence_builder"]["device"]["name"] == fresnel.name


def test_device_run_skips_the_transform_when_disabled():
    """``set_options(transform=False)`` submits the sequence as built."""
    client = MagicMock()
    client.create_job.side_effect = _Submitted
    device = _pasqal_qpu(client)
    device.set_options(transform=False)
    with pytest.raises(_Submitted):
        device.run(_free_register_sequence(), shots=10)


@pytest.mark.parametrize(
    "device_id", ["qbraid:qbraid:qpu:fresnel-can1", "azure:pasqal:qpu:fresnel-can1"]
)
def test_other_vendors_devices_are_not_transformed(device_id):
    """Only devices Pasqal runs through qBraid's own integration move the sequence."""
    device = QbraidDevice(
        TargetProfile(
            device_id=device_id,
            simulator=False,
            experiment_type=ExperimentType.ANALOG,
            provider_name="pasqal",
        ),
        client=MagicMock(),
    )
    seq = _free_register_sequence()
    assert device.transform(seq) is seq


def _pasqal_device(device_id: str, is_emulator: bool) -> tuple[PasqalDevice, MagicMock]:
    client = MagicMock()
    client.create_batch.side_effect = _Submitted
    session = MagicMock()
    session.get_device_records.return_value = {
        device_id: {"status": "UP", "active": True, "availability": "ACTIVE"}
    }
    profile = _build_profile(device_id, {"is_emulator": is_emulator})
    return PasqalDevice(profile, client=client, session=session), client


def test_pasqal_device_run_moves_the_sequence_onto_the_qpu(fresnel):
    """The self-managed path submits the sequence moved onto FRESNEL_CAN1."""
    device, client = _pasqal_device("FRESNEL_CAN1", is_emulator=False)
    with pytest.raises(PasqalDeviceError):
        device.run(_sequence(_calibrated_register(fresnel), AnalogDevice), shots=10)
    sent = json.loads(client.create_batch.call_args.kwargs["jobs"][0]["serialized_sequence"])
    assert sent["device"]["name"] == fresnel.name


def test_pasqal_device_run_rejects_before_submitting():
    """The self-managed path stops a sequence FRESNEL_CAN1 would reject."""
    device, client = _pasqal_device("FRESNEL_CAN1", is_emulator=False)
    with pytest.raises(TransformError, match="RegisterLayout"):
        device.run(_free_register_sequence(), shots=10)
    client.create_batch.assert_not_called()


def test_pasqal_device_passes_abstract_repr_strings_through():
    """A sequence already serialized is not something the transform can read."""
    device, _ = _pasqal_device("FRESNEL_CAN1", is_emulator=False)
    assert device.transform('{"name": "seq"}') == '{"name": "seq"}'
