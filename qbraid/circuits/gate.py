from abc import ABC
from typing import Union

from braket.circuits.gate import Gate as BraketGate

from cirq.ops.gate_features import SingleQubitGate as CirqSingleQubitGate
from cirq.ops.gate_features import ThreeQubitGate as CirqThreeQubitGate
from cirq.ops.gate_features import TwoQubitGate as CirqTwoQubitGate
from cirq.ops.measurement_gate import MeasurementGate as CirqMeasure

import numpy as np

from qiskit.circuit.controlledgate import ControlledGate as QiskitControlledGate
from qiskit.circuit.gate import Gate as QiskitGate
from qiskit.circuit.measure import Measure as QiskitMeasurementGate

from .braket.utils import create_braket_gate
from .cirq.utils import create_cirq_gate, cirq_gates
from .parameter import AbstractParameterWrapper
from .qiskit.utils import create_qiskit_gate, qiskit_gates

# types
CirqGate = Union[CirqSingleQubitGate, CirqTwoQubitGate, CirqThreeQubitGate, CirqMeasure]
CirqGateTypes = (CirqSingleQubitGate, CirqTwoQubitGate, CirqThreeQubitGate, CirqMeasure)
QiskitGateTypes = (QiskitGate, QiskitControlledGate, QiskitMeasurementGate)
BraketGateTypes = BraketGate

GateInputType = Union[
    "BraketGate",
    "CirqSingleQubitGate",
    "CirqTwoQubitGate",
    "CirqThreeQubitGate",
    "QiskitGate",
    "QiskitControlledGate",
    np.array,
]


class GateError(Exception):
    """Exception raised by a :class:`~.qbraid.circuits.gate.AbstractGate` object when it is
    unable to process a gate."""


class AbstractGate(ABC):
    """Abstract Gate wrapper object. Extended by 'QiskitGateWrapper', etc."""

    def __init__(self):

        self.gate = None
        self.name = None
        self.package = None

        self.params = None
        self.matrix = None

        self.num_controls = 0
        self.base_gate = None

        self._gate_type = None
        self._outputs = {}

    # =============================================================================
    #     def get_data(self):
    #
    #         data = {'name':self.name,
    #                 'type': self._gate_type,
    #                 'package': self.package,
    #                 'params': self.params,
    #                 'matrix': self.matrix,
    #                 }
    #         if self.base_gate:
    #             data['num_controls'] = self.num_controls
    #             data['base_gate'] = self.base_gate
    # =============================================================================

    def transpile(self, package: str):

        """If transpiled object not created, create it. Then return."""

        if package not in self._outputs.keys():
            self._create_output(package)
        return self._outputs[package]

    def _create_output(self, package: str):

        if package == "qiskit":
            self._create_qiskit()
        elif package == "braket":
            self._create_braket()
        elif package == "cirq":
            self._create_cirq()
        else:
            raise ValueError("Package not supported")

    def _create_qiskit(self):

        """Create qiskit gate from a qbraid gate wrapper object."""

        qiskit_params = self.params.copy()
        for i, param in enumerate(qiskit_params):
            if isinstance(param, AbstractParameterWrapper):
                qiskit_params[i] = param.transpile("qiskit")

        data = {
            "type": self._gate_type,
            "matrix": self.matrix,
            "name": self.name,
            "params": qiskit_params,
        }

        if self._gate_type in qiskit_gates.keys():
            self._outputs["qiskit"] = create_qiskit_gate(data)

        elif self.base_gate:
            self._outputs["qiskit"] = self.base_gate.transpile("qiskit").control(self.num_controls)

        elif not (self.matrix is None):
            data["type"] = "Unitary"
            self._outputs["qiskit"] = create_qiskit_gate(data)

    def _create_cirq(self):

        """Create cirq gate from a qbraid gate wrapper object."""

        cirq_params = self.params.copy()
        for i, param in enumerate(cirq_params):
            if isinstance(param, AbstractParameterWrapper):
                cirq_params[i] = param.transpile("cirq")

        data = {
            "type": self._gate_type,
            "matrix": self.matrix,
            "name": self.name,
            "params": cirq_params,
        }

        if self._gate_type in cirq_gates.keys():
            self._outputs["cirq"] = create_cirq_gate(data)

        elif self.base_gate:
            self._outputs["cirq"] = self.base_gate.transpile("cirq").controlled(self.num_controls)

        elif not (self.matrix is None):
            data["name"] = data["type"]
            data["type"] = "Unitary"
            self._outputs["cirq"] = create_cirq_gate(data)

    def _create_braket(self):

        """Create braket gate from a qbraid gate wrapper object."""

        self._outputs["braket"] = create_braket_gate(self._gate_type, self.params)
