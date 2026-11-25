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

# pylint: disable=redefined-outer-name

"""
Unit tests for submitting OpenQASM 3 programs to IonQ as ``ionq.qasm3.v1`` jobs.

"""

import json
import logging
import re
import warnings
from unittest.mock import Mock

import pytest

from qbraid.programs.gate_model.ionq import GateSet
from qbraid.runtime.exceptions import ProgramValidationError
from qbraid.runtime.ionq import IonQDevice, IonQJob, IonQProvider, IonQSession
from qbraid.runtime.ionq import qasm3 as ionq_qasm3
from qbraid.runtime.ionq.qasm3 import _normalize_angles, find_unsupported, to_ionq_qasm3
from qbraid.transpiler import ProgramConversionError

SIMULATOR_DATA = {
    "backend": "simulator",
    "status": "available",
    "qubits": 29,
    "average_queue_time": 0,
    "last_updated": 1717253790,
    "has_access": True,
    "noise_models": ["forte-1", "ideal"],
    "degraded": False,
}

# Measures q[0], then keeps working on q[1]. From IonQ's public OpenQASM 3 guide
# (docs.ionq.com/api-reference/v0.4/openqasm3, "Mid-circuit measurement").
MCM_PROGRAM = """OPENQASM 3.0;
qubit[2] q;
bit[1] m;
bit[2] c;
x q[0];
m[0] = measure q[0];
h q[1];
c[0] = measure q[0];
c[1] = measure q[1];
"""


@pytest.fixture
def session():
    """IonQ session that records created jobs instead of calling the API."""
    mock_session = Mock(spec=IonQSession)
    mock_session.get_device.return_value = SIMULATOR_DATA
    mock_session.create_job.side_effect = [{"id": f"job-{i}"} for i in range(10)]
    return mock_session


@pytest.fixture
def device(session):
    """IonQ simulator device built from the provider's real profile."""
    profile = IonQProvider(api_key="fake_api_key")._build_profile(SIMULATOR_DATA)
    return IonQDevice(profile, session)


def _sent_jobs(session) -> list[dict]:
    return [json.loads(call.args[0]) for call in session.create_job.call_args_list]


def test_submit_string_sends_qasm3_job(device, session):
    """A string passed to submit is sent as an ionq.qasm3.v1 job, exactly as written."""
    job = device.submit(MCM_PROGRAM, shots=100, noise={"model": "forte-1"})

    assert isinstance(job, IonQJob)
    assert job.id == "job-0"
    (sent,) = _sent_jobs(session)
    assert sent["type"] == "ionq.qasm3.v1"
    assert sent["input"] == {"data": MCM_PROGRAM}
    assert sent["backend"] == "simulator"
    assert sent["shots"] == 100
    assert sent["noise"] == {"model": "forte-1"}


def test_submit_rejects_list_with_qasm3_program(device, session):
    """submit() takes one OpenQASM 3 program per job, so a list of them is refused."""
    with pytest.raises(ValueError, match="one OpenQASM 3 program per job"):
        device.submit([MCM_PROGRAM, MCM_PROGRAM], shots=10)
    session.create_job.assert_not_called()


def test_run_qasm3_sends_program_unchanged(device, session):
    """With submit_as='qasm3', an OpenQASM 3 string keeps its mid-circuit measurement."""
    job = device.run(MCM_PROGRAM, shots=10, submit_as="qasm3")

    assert isinstance(job, IonQJob)
    (sent,) = _sent_jobs(session)
    assert sent["type"] == "ionq.qasm3.v1"
    assert sent["input"]["data"] == MCM_PROGRAM


def test_run_qasm3_converts_other_programs(device, session):
    """A program in another format is converted to OpenQASM 3, keeping its measurements."""
    qiskit = pytest.importorskip("qiskit")
    circuit = qiskit.QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.measure(0, 0)
    circuit.x(1)
    circuit.measure(1, 1)

    device.run(circuit, shots=10, submit_as="qasm3")

    (sent,) = _sent_jobs(session)
    assert sent["type"] == "ionq.qasm3.v1"
    data = sent["input"]["data"]
    assert data.startswith("OPENQASM 3")
    assert data.count("measure") == 2


def test_run_qasm3_splits_register_measurement_of_converted_program(device, session):
    """A converted whole-register measurement, which IonQ rejects, becomes one per bit."""
    qasm2 = (
        'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh q[0];\nmeasure q -> c;\n'
    )

    device.run(qasm2, shots=10, submit_as="qasm3")

    (sent,) = _sent_jobs(session)
    data = sent["input"]["data"]
    assert "c = measure q;" not in data
    assert "c[0] = measure q[0];" in data
    assert "c[1] = measure q[1];" in data


def test_run_qasm3_sends_clean_program_byte_identical(device, session):
    """A program IonQ runs as written is sent unchanged, whitespace and comments included."""
    program = (
        'OPENQASM 3.0;\n// keep me\ninclude "stdgates.inc";\n'
        "gate bell a, b { h a; cx a, b; }\nqubit[3] q;\nbit[3] c;\n"
        "bell q[0], q[1];\nctrl @ x q[1], q[2];\nrz(-0.5) q[2];\n"
        "c[0] = measure q[0];\nreset q[0];\nmeasure q[1] -> c[1];\nc[2] = measure q[2];\n"
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        device.run(program, shots=10, submit_as="qasm3")

    (sent,) = _sent_jobs(session)
    assert sent["input"]["data"] == program


@pytest.mark.parametrize(
    "statement, problem",
    [
        ("ccx q[0], q[1], q[2];", "gate 'ccx'"),
        ("ctrl(2) @ x q[0], q[1], q[2];", "'ctrl(2) @ x'"),
        ("U(0.1, 0.2, 0.3) q[0];", "gate 'U'"),
        ("c = measure q;", "whole-register measurement"),
        ("reset q;", "whole-register reset"),
        ("for int i in [0:1] { x q[0]; }", "for loop"),
    ],
)
def test_run_qasm3_rewrites_program_ionq_cannot_run(device, session, statement, problem):
    """A program with a construct IonQ rejects or misruns is rewritten, with a warning."""
    program = f'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[3] q;\nbit[3] c;\n{statement}\n'

    with pytest.warns(UserWarning, match=re.escape(problem)):
        device.run(program, shots=10, submit_as="qasm3")

    (sent,) = _sent_jobs(session)
    data = sent["input"]["data"]
    assert data != program
    assert not find_unsupported(data)


def test_run_qasm3_rewrites_ctrl2_inside_gate_definition(device, session):
    """ctrl(2) @ x inside a gate body is rewritten too."""
    program = (
        "OPENQASM 3.0;\nqubit[3] q;\nbit[1] c;\n"
        "gate tof a, b, t { ctrl(2) @ x a, b, t; }\ntof q[0], q[1], q[2];\nc[0] = measure q[2];\n"
    )

    with pytest.warns(UserWarning, match=re.escape("'ctrl(2) @ x'")):
        device.run(program, shots=10, submit_as="qasm3")

    data = _sent_jobs(session)[0]["input"]["data"]
    assert "ctrl" not in data
    assert "ccx" not in data
    assert not find_unsupported(data)


def test_run_qasm3_refuses_rewrite_with_transpile_off(device, session):
    """With transpile off, a program IonQ cannot run as written is refused, not rewritten."""
    device.set_options(transpile=False)
    program = 'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[3] q;\nccx q[0], q[1], q[2];\n'

    with pytest.raises(ProgramConversionError, match="transpile option is off"):
        device.run(program, shots=10, submit_as="qasm3")
    session.create_job.assert_not_called()


def test_run_qasm3_raises_when_rewrite_fails(device, session):
    """A program pyqasm cannot rewrite raises before submit, instead of being sent."""
    program = "OPENQASM 3.0;\nqubit[1] q;\nbit[1] c;\nfoo q[0];\nc[0] = measure q[0];\n"

    with pytest.warns(UserWarning, match="gate 'foo'"):
        with pytest.raises(ProgramConversionError, match="IonQ supports"):
            device.run(program, shots=10, submit_as="qasm3")
    session.create_job.assert_not_called()


def _assert_ionq_ready(data: str) -> None:
    """Assert IonQ runs ``data`` as written: supported gates only and no negative angles."""
    assert not find_unsupported(data)
    assert "ctrl" not in data
    assert not re.search(r"\(\s*-", data), "negative gate argument"
    assert "measure q;" not in data


def test_run_qasm3_rewrites_converted_qiskit_gates(device, session):
    """Qiskit gates IonQ rejects (ccx, u, cp, cswap, ch, crz) are rewritten before submit."""
    qiskit = pytest.importorskip("qiskit")
    circuit = qiskit.QuantumCircuit(3, 3)
    circuit.ccx(0, 1, 2)
    circuit.u(0.1, -0.2, 0.3, 0)
    circuit.cp(-0.4, 0, 1)
    circuit.cswap(0, 1, 2)
    circuit.ch(0, 1)
    circuit.crz(-0.5, 1, 2)
    circuit.measure(0, 0)
    circuit.h(1)
    circuit.measure([1, 2], [1, 2])

    device.run(circuit, shots=10, submit_as="qasm3")

    data = _sent_jobs(session)[0]["input"]["data"]
    _assert_ionq_ready(data)
    assert data.count("measure") == 3


def test_run_qasm3_rewrites_converted_cirq_circuit(device, session):
    """A Cirq circuit with a Toffoli is converted and rewritten into supported gates."""
    cirq = pytest.importorskip("cirq")
    q0, q1, q2 = cirq.LineQubit.range(3)
    circuit = cirq.Circuit(cirq.H(q0), cirq.CCX(q0, q1, q2), cirq.measure(q0, q1, q2, key="m"))

    device.run(circuit, shots=10, submit_as="qasm3")

    data = _sent_jobs(session)[0]["input"]["data"]
    _assert_ionq_ready(data)
    assert data.count("measure") == 3


def test_ccx_rewrite_is_exact():
    """The Toffoli decomposition sent to IonQ has the same unitary as ccx."""
    qiskit = pytest.importorskip("qiskit")
    pytest.importorskip("qiskit_qasm3_import")
    from qiskit.quantum_info import Operator  # pylint: disable=import-outside-toplevel

    program = 'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[3] q;\nccx q[0], q[1], q[2];\n'
    rewritten = to_ionq_qasm3(program)
    assert "ccx" not in rewritten

    expected = qiskit.QuantumCircuit(3)
    expected.ccx(0, 1, 2)
    assert Operator(qiskit.qasm3.loads(rewritten)).equiv(Operator(expected))


def test_rewrite_keeps_rotation_unitaries_up_to_phase():
    """Angles are written in [0, 2π), which changes only the global phase."""
    qiskit = pytest.importorskip("qiskit")
    pytest.importorskip("qiskit_qasm3_import")
    from qiskit.quantum_info import Operator  # pylint: disable=import-outside-toplevel

    program = (
        'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[2] q;\n'
        "rx(-0.3) q[0];\nry(-7.0) q[1];\nrz(-1.2) q[0];\np(-0.4) q[1];\ncx q[0], q[1];\n"
    )
    rewritten = to_ionq_qasm3(program)
    assert not re.search(r"\(\s*-", rewritten)
    assert Operator(qiskit.qasm3.loads(rewritten)).equiv(Operator(qiskit.qasm3.loads(program)))


def test_run_qasm3_batch_makes_one_job_per_program(device, session):
    """A list of programs becomes one job each, and the device status is checked once."""
    jobs = device.run([MCM_PROGRAM, MCM_PROGRAM], shots=10, submit_as="qasm3")

    assert [job.id for job in jobs] == ["job-0", "job-1"]
    assert [sent["type"] for sent in _sent_jobs(session)] == ["ionq.qasm3.v1"] * 2
    session.get_device.assert_called_once()


def test_run_default_still_sends_json_circuit(device, session):
    """Without submit_as, programs are still converted to IonQ's JSON circuit format."""
    program = 'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[2] q;\nh q[0];\ncx q[0], q[1];\n'

    device.run(program, shots=10)

    (sent,) = _sent_jobs(session)
    assert sent["type"] == "ionq.circuit.v1"
    assert "circuit" in sent["input"]


def test_run_qasm3_checks_qubit_count(device, session):
    """A program wider than the device is refused before anything is submitted."""
    wide = 'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[40] q;\nh q[39];\n'

    with pytest.raises(ProgramValidationError, match="exceeds"):
        device.run(wide, shots=10, submit_as="qasm3")
    session.create_job.assert_not_called()


def test_run_qasm3_needs_transpile_for_non_qasm3_input(device, session):
    """With transpile off, only an OpenQASM 3 string can be submitted as OpenQASM 3."""
    device.set_options(transpile=False)
    qasm2 = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\nh q[0];\n'

    with pytest.raises(ProgramConversionError, match="transpile option is off"):
        device.run(qasm2, shots=10, submit_as="qasm3")
    session.create_job.assert_not_called()


def test_run_rejects_unknown_submit_as(device, session):
    """An unknown submit_as value raises before any request."""
    with pytest.raises(ValueError, match="Invalid submit_as"):
        device.run(MCM_PROGRAM, shots=10, submit_as="qasm2")
    session.create_job.assert_not_called()
    session.get_device.assert_not_called()


def test_run_qasm3_warns_about_qiskit_ionq_options(device):
    """qiskit-ionq options do not apply to OpenQASM 3 submissions."""
    with pytest.warns(UserWarning, match="GateSet argument"):
        device.run(MCM_PROGRAM, shots=10, submit_as="qasm3", gateset=GateSet.NATIVE)


# A completed run of MCM_PROGRAM on IonQ's ideal simulator, with made-up ids. IonQ lists
# bit 0 of each register first: x q[0] sets c[0] and m[0], and h q[1] splits c[1].
SHOTS_ARTIFACT_ID = "00000000-0000-0000-0000-00000000a001"
QASM3_JOB = {
    "id": "job-qasm3",
    "type": "ionq.qasm3.v1",
    "status": "completed",
    "backend": "simulator",
    "noise": {"model": "ideal"},
    "stats": {"qubits": 2, "circuits": 1},
    "results": {
        "probabilities": {"url": "/v0.4/jobs/job-qasm3/results/probabilities"},
        "ionq.result.shots.json.v2": {
            "id": SHOTS_ARTIFACT_ID,
            "format": "ionq.result.shots.json.v2",
            "media_type": "application/json",
        },
    },
}
SHOTS = [{"registers": {"output_all": [1, bit], "c": [1, bit], "m": [1]}} for bit in [1, 0, 1, 0]]
# Legacy probabilities key on the state index, with qubit 0 as the least significant bit.
LEGACY_PROBABILITIES = {"1": 0.5, "3": 0.5}


def _job_with_responses(job_data: dict, artifact: object) -> tuple[IonQJob, Mock]:
    """Return an IonQJob whose session serves ``job_data`` and the given artifact."""
    session = Mock(spec=IonQSession)
    session.get_job.return_value = json.loads(json.dumps(job_data))

    def get(path, **_kwargs):
        response = Mock()
        if path.endswith("/results/probabilities"):
            response.json.return_value = LEGACY_PROBABILITIES
        elif path == f"/jobs/{job_data['id']}/artifacts/{SHOTS_ARTIFACT_ID}":
            if isinstance(artifact, Exception):
                raise artifact
            response.json.return_value = artifact
        else:
            raise AssertionError(f"unexpected GET {path}")
        return response

    session.get.side_effect = get
    job = IonQJob(job_data["id"], session=session, shots=len(SHOTS))
    job._cache_metadata["shots"] = len(SHOTS)
    return job, session


def test_result_reads_registers_from_shots_artifact():
    """Each register's bitstrings put bit 0 last, and counts stay as before."""
    job, session = _job_with_responses(QASM3_JOB, {"shots": SHOTS})

    result = job.result()

    assert result.data.get_counts() == {"01": 2, "11": 2}
    extra = result.data.extra
    assert extra["register_memory"] == {
        "output_all": ["11", "01", "11", "01"],
        "c": ["11", "01", "11", "01"],
        "m": ["1", "1", "1", "1"],
    }
    assert extra["register_counts"] == {
        "output_all": {"01": 2, "11": 2},
        "c": {"01": 2, "11": 2},
        "m": {"1": 4},
    }
    session.get.assert_any_call(f"/jobs/job-qasm3/artifacts/{SHOTS_ARTIFACT_ID}")


def test_output_all_register_matches_legacy_counts():
    """The final-readout register and the legacy histogram use the same bit order."""
    job, _ = _job_with_responses(QASM3_JOB, {"shots": SHOTS})

    result = job.result()

    assert result.data.extra["register_counts"]["output_all"] == result.data.get_counts()


def test_result_reads_output_all_beside_registers():
    """output_all is read whether IonQ nests it in registers or sets it on the shot."""
    shots = [
        {"registers": {"c": [1, 0]}, "output_all": [1, 0]},
        {"registers": {"c": [0, 1]}, "output_all": [0, 1]},
    ]
    job, _ = _job_with_responses(QASM3_JOB, {"shots": shots})

    memory = job.result().data.extra["register_memory"]

    assert memory == {"c": ["01", "10"], "output_all": ["01", "10"]}


def test_result_keeps_counts_when_artifact_fetch_fails(caplog):
    """A failed artifact fetch logs a warning and still returns the counts."""
    job, _ = _job_with_responses(QASM3_JOB, ConnectionError("artifact unavailable"))

    with caplog.at_level(logging.WARNING):
        result = job.result()

    assert result.data.get_counts() == {"01": 2, "11": 2}
    assert "register_counts" not in result.data.extra
    assert "artifact unavailable" in caplog.text


@pytest.mark.parametrize(
    "artifact",
    [{"shots": "nope"}, {"shots": [{"registers": None}]}, {"shots": [{"registers": {"c": [2]}}]}],
)
def test_result_ignores_malformed_artifact(artifact):
    """A shots artifact with an unexpected shape is skipped, and counts are returned."""
    job, _ = _job_with_responses(QASM3_JOB, artifact)

    result = job.result()

    assert result.data.get_counts() == {"01": 2, "11": 2}
    assert "register_memory" not in result.data.extra


def test_circuit_job_makes_no_artifact_request():
    """A JSON circuit job lists no shots artifact, so only the legacy histogram is read."""
    circuit_job = {**QASM3_JOB, "type": "ionq.circuit.v1"}
    circuit_job["results"] = {"probabilities": QASM3_JOB["results"]["probabilities"]}
    job, session = _job_with_responses(circuit_job, AssertionError("not fetched"))

    result = job.result()

    assert result.data.get_counts() == {"01": 2, "11": 2}
    assert "register_counts" not in result.data.extra
    paths = [call.args[0] for call in session.get.call_args_list]
    assert paths == ["/jobs/job-qasm3/results/probabilities"]


@pytest.mark.parametrize(
    "statement, problem",
    [
        ("inv @ h q[0];", "'inv @' modifier"),
        ("ctrl @ inv @ x q[0], q[1];", "more than one modifier on 'x'"),
        ("ctrl @ h q[0], q[1];", "'ctrl @ h'"),
        ("ctrl(n) @ x q[0], q[1];", "'ctrl(...) @ x'"),
        ("measure q[0];", "measurement without a target bit"),
    ],
)
def test_find_unsupported_names_each_construct(statement, problem):
    """Each construct IonQ rejects is reported once, by name."""
    program = f"OPENQASM 3.0;\nqubit[2] q;\nbit[2] c;\n{statement}\n{statement}\n"

    assert find_unsupported(program) == [problem]


def test_find_unsupported_passes_unparseable_program_through():
    """A program that does not parse is left for IonQ to report."""
    assert not find_unsupported("OPENQASM 3.0;\nqubit[2 q;\n")


def test_normalize_angles_edge_cases():
    """Symbolic angles are left alone, and an angle of exactly -0.0 or 2π becomes 0."""
    program = "rz(pi) q[0];\nrx(-2e-17) q[0];\nry(6.283185307179586) q[0];\n"

    assert _normalize_angles(program) == "rz(pi) q[0];\nrx(0.0) q[0];\nry(0.0) q[0];\n"


def test_rewrite_rebases_gates_left_after_unroll(monkeypatch):
    """A gate still unsupported after unrolling is rebased into rotations and cx."""
    monkeypatch.setattr(ionq_qasm3, "_expand_ccx", lambda qasm: qasm)
    program = 'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[3] q;\nccx q[0], q[1], q[2];\n'

    rewritten = to_ionq_qasm3(program)

    assert "ccx" not in rewritten
    assert not find_unsupported(rewritten)


def test_rewrite_raises_when_output_is_still_unsupported(monkeypatch):
    """The rewritten program is checked again, and a leftover construct raises."""
    monkeypatch.setattr(ionq_qasm3, "_normalize_angles", lambda qasm: qasm + "U(0, 0, 0) q[0];\n")
    program = 'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[1] q;\nh q[0];\n'

    with pytest.raises(ProgramConversionError, match="Still unsupported: gate 'U'"):
        to_ionq_qasm3(program)


def test_result_ignores_artifact_with_uneven_registers():
    """A register missing from some shots makes the artifact unreadable, not misaligned."""
    shots = [{"registers": {"c": [1], "m": [0]}}, {"registers": {"c": [0]}}]
    job, _ = _job_with_responses(QASM3_JOB, {"shots": shots})

    assert "register_memory" not in job.result().data.extra
