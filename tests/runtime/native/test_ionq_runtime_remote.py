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
Unit tests for submissions to IonQ devices via qBraid native runtime.

"""
import os
import warnings

import pytest

from qbraid import GateModelResultData, QbraidJob, QbraidProvider


@pytest.mark.remote
def test_qiskit_ionq_workflow():
    """Test the workflow of running a Qiskit circuit on an IonQ device via qBraid."""
    try:
        # pylint: disable=import-outside-toplevel
        import qiskit
        import qiskit.qasm2
        import qiskit_ionq

        # pylint: enable=import-outside-toplevel

        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        path_to_qasm_file = os.path.join(current_file_directory, "test.qasm")
        qiskit_circuit = qiskit.qasm2.load(path_to_qasm_file)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            qiskit_ionq_provider = qiskit_ionq.IonQProvider()
            qiskit_ionq_backend = qiskit_ionq_provider.get_backend("ionq_simulator")

            qiskit_circuit_transpiled = qiskit.transpile(qiskit_circuit, qiskit_ionq_backend)

        provider = QbraidProvider()
        device = provider.get_device("ionq_simulator")

        shots = 10
        job: QbraidJob = device.run(qiskit_circuit_transpiled, shots=shots)

        # pylint: disable=no-member
        job.wait_for_final_state()
        result = job.result()
        # pylint: enable=no-member

        assert result.success
        assert isinstance(result.data, GateModelResultData)

        counts: dict[str, int] = result.data.get_counts()
        assert sum(counts.values()) == shots
    except ImportError as err:
        pytest.skip(f"Skipped test due to import error: {err}")
