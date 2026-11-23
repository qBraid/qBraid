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
Unit tests for checking Pulser sequences against Pasqal's QPU before submitting them.

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

from qbraid.programs import ExperimentType
from qbraid.runtime import DeviceStatus, TargetProfile
from qbraid.runtime.exceptions import ProgramValidationError
from qbraid.runtime.native import QbraidDevice, QbraidProvider
from qbraid.runtime.native import pasqal as pasqal_check
from qbraid.runtime.native.provider import get_program_spec_lambdas

# pylint: enable=wrong-import-position,wrong-import-order

QPU_ID = "pasqal:pasqal:qpu:fresnel-can1"
EMU_ID = "pasqal:pasqal:sim:emu-free"
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
    pasqal_check.validate_pulser_for_pasqal_qpu(
        _sequence(_calibrated_register(fresnel), fresnel), QPU_ID
    )


def test_free_coordinates_are_rejected():
    """Pasqal's reason: 'FRESNEL_CAN1' requires the sequence's register to be defined from a
    RegisterLayout."""
    register = Register.from_coordinates([(0, 0), (10, 0)], prefix="q")
    with pytest.raises(
        ValueError, match="requires the sequence's register to be defined from a RegisterLayout"
    ):
        pasqal_check.validate_pulser_for_pasqal_qpu(_sequence(register, AnalogDevice), QPU_ID)


def test_uncalibrated_underfilled_layout_is_rejected():
    """Pasqal: 'The existing register is incompatible with the new device.'"""
    layout = next(iter(AnalogDevice.pre_calibrated_layouts))
    register = layout.define_register(0, 10, qubit_ids=["q0", "q1"])
    with pytest.raises(ValueError, match="register is not valid on FRESNEL_CAN1"):
        pasqal_check.validate_pulser_for_pasqal_qpu(_sequence(register, AnalogDevice), QPU_ID)


@pytest.mark.parametrize(
    "duration, amplitude, message",
    [(7000, np.pi, "at most 6000 ns"), (500, 20.0, "amplitude")],
)
def test_pulses_outside_fresnel_limits_are_rejected(fresnel, duration, amplitude, message):
    """A calibrated register on a permissive device must still fit FRESNEL_CAN1's channels."""
    seq = _sequence(_calibrated_register(fresnel), MockDevice, duration, amplitude)
    with pytest.raises(ValueError, match=message):
        pasqal_check.validate_pulser_for_pasqal_qpu(seq, QPU_ID)


def test_total_duration_over_the_limit_is_rejected(fresnel):
    """Pulses each within the limit can still add up to more than FRESNEL_CAN1 allows."""
    seq = Sequence(_calibrated_register(fresnel), MockDevice)
    seq.declare_channel("ryd", "rydberg_global")
    seq.add(Pulse.ConstantPulse(4000, np.pi, 0.0, 0.0), "ryd")
    seq.add(Pulse.ConstantPulse(4000, np.pi, 0.0, 0.0), "ryd")
    seq.measure("ground-rydberg")
    with pytest.raises(ValueError, match="maximum duration allowed by the device"):
        pasqal_check.validate_pulser_for_pasqal_qpu(seq, QPU_ID)


def test_errors_say_how_to_fix_it():
    """The message points to building on FRESNEL_CAN1 with a calibrated layout."""
    register = Register.from_coordinates([(0, 0), (10, 0)], prefix="q")
    with pytest.raises(ValueError, match="calibrated layouts"):
        pasqal_check.validate_pulser_for_pasqal_qpu(_sequence(register, AnalogDevice), QPU_ID)


def test_unreachable_specs_do_not_block_submission(specs_endpoint):
    """If Pasqal's specs cannot be read, the check is skipped rather than failing the job."""
    specs_endpoint.side_effect = requests.ConnectionError("offline")
    register = Register.from_coordinates([(0, 0), (10, 0)], prefix="q")
    pasqal_check.validate_pulser_for_pasqal_qpu(_sequence(register, AnalogDevice), QPU_ID)


def test_unknown_device_type_is_not_checked():
    """A Pasqal QPU without public specs is left to Pasqal's own validation."""
    register = Register.from_coordinates([(0, 0), (10, 0)], prefix="q")
    seq = _sequence(register, AnalogDevice)
    pasqal_check.validate_pulser_for_pasqal_qpu(seq, "pasqal:pasqal:qpu:some-future-qpu")


def test_specs_are_fetched_once_within_the_ttl(specs_endpoint, fresnel):
    """Repeated submissions reuse the fetched specs."""
    seq = _sequence(_calibrated_register(fresnel), fresnel)
    for _ in range(3):
        pasqal_check.validate_pulser_for_pasqal_qpu(seq, QPU_ID)
    specs_endpoint.assert_called_once()


def test_specs_are_refetched_after_the_ttl(specs_endpoint, fresnel):
    """Recalibrations reach the check once the cached specs expire."""
    seq = _sequence(_calibrated_register(fresnel), fresnel)
    with patch.object(pasqal_check.time, "monotonic", return_value=1_000.0):
        pasqal_check.validate_pulser_for_pasqal_qpu(seq, QPU_ID)
    with patch.object(
        pasqal_check.time,
        "monotonic",
        return_value=1_000.0 + pasqal_check._SPECS_TTL_S + 1,  # pylint: disable=protected-access
    ):
        pasqal_check.validate_pulser_for_pasqal_qpu(seq, QPU_ID)
    assert specs_endpoint.call_count == 2


def _free_register_sequence():
    return _sequence(Register.from_coordinates([(0, 0), (10, 0)], prefix="q"), AnalogDevice)


@pytest.mark.parametrize("device", [AnalogDevice, MockDevice])
def test_valid_sequences_pass_with_warnings_as_errors(fresnel, device):
    """Pulser's deprecation and Rydberg-level warnings never turn into a rejection."""
    seq = _sequence(_calibrated_register(fresnel), device)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        pasqal_check.validate_pulser_for_pasqal_qpu(seq, QPU_ID)


def test_concurrent_checks_leave_the_warning_filters_as_they_were(fresnel):
    """Checks run in parallel threads never leave a warning filter behind."""
    seq = _sequence(_calibrated_register(fresnel), AnalogDevice)
    pasqal_check.validate_pulser_for_pasqal_qpu(seq, QPU_ID)  # fetch the specs first
    before = list(warnings.filters)

    def _check():
        for _ in range(20):
            pasqal_check.validate_pulser_for_pasqal_qpu(seq, QPU_ID)

    threads = [threading.Thread(target=_check) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert list(warnings.filters) == before


def test_very_old_specs_are_not_reused_during_an_outage(specs_endpoint):
    """Specs past twice their lifetime are dropped while Pasqal is unreachable."""
    with patch.object(pasqal_check.time, "monotonic", return_value=1_000.0):
        with pytest.raises(ValueError, match="RegisterLayout"):
            pasqal_check.validate_pulser_for_pasqal_qpu(_free_register_sequence(), QPU_ID)
    specs_endpoint.side_effect = requests.ConnectionError("offline")
    much_later = 1_000.0 + pasqal_check._MAX_STALE_S + 1  # pylint: disable=protected-access
    with patch.object(pasqal_check.time, "monotonic", return_value=much_later):
        pasqal_check.validate_pulser_for_pasqal_qpu(_free_register_sequence(), QPU_ID)


def test_the_users_sequence_is_not_modified(fresnel):
    """Checking a sequence leaves it on the device it was built on."""
    seq = _sequence(_calibrated_register(fresnel), AnalogDevice)
    pasqal_check.validate_pulser_for_pasqal_qpu(seq, QPU_ID)
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
    pasqal_check.validate_pulser_for_pasqal_qpu(seq, QPU_ID)


def test_a_failed_fetch_is_not_retried_on_every_submit(specs_endpoint):
    """An unreachable endpoint costs one attempt per failure window, not one per program."""
    specs_endpoint.side_effect = requests.ConnectionError("offline")
    for _ in range(3):
        pasqal_check.validate_pulser_for_pasqal_qpu(_free_register_sequence(), QPU_ID)
    specs_endpoint.assert_called_once()


def test_last_good_specs_are_used_when_a_refresh_fails(specs_endpoint):
    """After the specs expire, a failed refresh falls back to the last specs read."""
    with patch.object(pasqal_check.time, "monotonic", return_value=1_000.0):
        with pytest.raises(ValueError, match="RegisterLayout"):
            pasqal_check.validate_pulser_for_pasqal_qpu(_free_register_sequence(), QPU_ID)
    specs_endpoint.side_effect = requests.ConnectionError("offline")
    later = 1_000.0 + pasqal_check._SPECS_TTL_S + 1  # pylint: disable=protected-access
    with patch.object(pasqal_check.time, "monotonic", return_value=later):
        with pytest.raises(ValueError, match="RegisterLayout"):
            pasqal_check.validate_pulser_for_pasqal_qpu(_free_register_sequence(), QPU_ID)
    assert specs_endpoint.call_count == 2


def test_an_unreadable_entry_does_not_drop_the_others(specs_endpoint):
    """A specs entry Pulser cannot read is skipped; FRESNEL_CAN1 is still checked."""
    bad = {"device_type": "FUTURE_QPU", "specs": "{not json"}
    specs_endpoint.return_value.json.return_value = {"data": [bad] + SPECS["data"]}
    with pytest.raises(ValueError, match="RegisterLayout"):
        pasqal_check.validate_pulser_for_pasqal_qpu(_free_register_sequence(), QPU_ID)


def test_an_error_without_a_message_still_says_what_failed(fresnel):
    """Pulser raises some errors with no message; the rejection names the error instead."""
    seq = _sequence(_calibrated_register(fresnel), AnalogDevice)
    with patch.object(Sequence, "with_new_device", side_effect=TypeError()):
        with pytest.raises(ValueError, match="not valid on FRESNEL_CAN1: TypeError"):
            pasqal_check.validate_pulser_for_pasqal_qpu(seq, QPU_ID)


def test_only_pasqal_qpus_get_the_check():
    """Emulators accept any valid sequence, and other vendors' devices are untouched."""
    assert get_program_spec_lambdas("pulser", QPU_ID)["validate"] is not None
    assert get_program_spec_lambdas("pulser", EMU_ID)["validate"] is None
    assert get_program_spec_lambdas("pulser", "qbraid:qbraid:sim:x")["validate"] is None
    assert get_program_spec_lambdas("pulser", "local_device")["validate"] is None


def _pasqal_qpu(client: MagicMock) -> QbraidDevice:
    specs = QbraidProvider._get_program_specs(
        ["pulser"], QPU_ID
    )  # pylint: disable=protected-access
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
    register = Register.from_coordinates([(0, 0), (10, 0)], prefix="q")
    with pytest.raises(ProgramValidationError, match="RegisterLayout"):
        device.run(_sequence(register, AnalogDevice), shots=10)
    client.create_job.assert_not_called()


def test_device_run_submits_a_valid_sequence(fresnel):
    """A sequence FRESNEL_CAN1 accepts is submitted as a pulser.sequence Program."""
    client = MagicMock()
    client.create_job.side_effect = _Submitted
    device = _pasqal_qpu(client)
    with pytest.raises(_Submitted):
        device.run(_sequence(_calibrated_register(fresnel), fresnel), shots=10)
    request = client.create_job.call_args.args[0]
    assert isinstance(request.program, Program)
    assert request.program.format == "pulser.sequence"
