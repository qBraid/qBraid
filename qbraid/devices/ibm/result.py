# This code is part of Qiskit.
#
# (C) Copyright IBM 2017.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of the source tree https://github.com/Qiskit/qiskit-terra/blob/main/LICENSE.txt
# or at http://www.apache.org/licenses/LICENSE-2.0.
#
# NOTICE: This file has been modified from the original:
# https://github.com/Qiskit/qiskit-terra/blob/main/qiskit/result/result.py

"""QiskitResultWrapper Class"""

from __future__ import annotations

from typing import Dict

from qiskit.result.result import Result

from qbraid.devices.result import ResultWrapper


class QiskitResultWrapper(ResultWrapper):
    """Qiskit ``Result`` wrapper class."""

    # pylint: disable=too-few-public-methods
    def __init__(self, vendor_rlo: Result):
        """Create a QiskitResultWrapper

        Args:
            vendor_rlo (Result): a Qiskit ``Result`` object

        """
        super().__init__(vendor_rlo)
        self.vendor_rlo = vendor_rlo

    def data(self, **kwargs) -> Dict:
        """Get the raw data for an experiment.

        Note this data will be a single classical and quantum register and in a format required by
        the results schema. We recommend that most users use the get_xxx method, and the data will
        be post-processed for the data type.

        Args:
            kwargs:
                experiment (str or QuantumCircuit or Schedule or int or None): the index of the
                    experiment. Several types are accepted for convenience::
                    * str: the name of the experiment.
                    * QuantumCircuit: the name of the circuit instance will be used.
                    * Schedule: the name of the schedule instance will be used.
                    * int: the position of the experiment.
                    * None: if there is only one experiment, returns it.

        Returns:
            dict: A dictionary of results data for an experiment. The data depends on the backend
                it ran on and the settings of `meas_level`, `meas_return` and `memory`. QASM
                backends return a dictionary of dictionary with the key 'counts' and  with the
                counts, with the second dictionary keys containing a string in hex format
                (``0x123``) and values equal to the number of times this outcome was measured.
                Statevector backends return a dictionary with key 'statevector' and values being a
                list[list[complex components]] list of 2^num_qubits complex amplitudes. Where each
                complex number is represented as a 2 entry list for each component. For example, a
                list of [0.5+1j, 0-1j] would be represented as [[0.5, 1], [0, -1]].
                Unitary backends return a dictionary with key 'unitary' and values being a
                list[list[list[complex components]]] list of 2^num_qubits x 2^num_qubits complex
                amplitudes in a two entry list for each component. For example if the amplitude is
                [[0.5+0j, 0-1j], ...] the value returned will be [[[0.5, 0], [0, -1]], ...].
                The simulator backends also have an optional key 'snapshots' which returns a dict
                of snapshots specified by the simulator backend. The value is of the form
                dict[slot: dict[str: array]] where the keys are the requested snapshot slots, and
                the values are a dictionary of the snapshots.

        Raises:
            QiskitError: if data for the experiment could not be retrieved.

        """
        return self.vendor_rlo.data(**kwargs)
