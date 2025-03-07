# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for submissions to IonQ devices via qBraid native runtime.

"""
import os
import warnings

import pytest

from qbraid import GateModelResultData, QbraidProvider


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
        job = device.run(qiskit_circuit_transpiled, shots=shots)
        job.wait_for_final_state()

        result = job.result()
        assert result.success
        assert isinstance(result.data, GateModelResultData)

        counts: dict[str, int] = result.data.get_counts()
        assert sum(counts.values()) == shots
    except ImportError as err:
        pytest.skip(f"Skipped test due to import error: {err}")
