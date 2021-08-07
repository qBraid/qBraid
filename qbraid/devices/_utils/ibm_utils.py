# pylint: skip-file

import os

from qiskit import QuantumCircuit
from qiskit.providers.aer import (
    AerSimulator,
    PulseSimulator,
    QasmSimulator,
    StatevectorSimulator,
    UnitarySimulator,
)
from qiskit.providers.basicaer import (
    QasmSimulatorPy,
    StatevectorSimulatorPy,
    UnitarySimulatorPy,
)

from qiskit.pulse import Schedule
from typing import Union, List

QiskitRunInput = Union[QuantumCircuit, Schedule, List]

ibmq_config_path = os.path.join(os.path.expanduser("~"), ".qiskit", "qiskitrc")
account_url = "https://auth.quantum-computing.ibm.com/api"

IBMQ_CONFIG_PROMPT = [
    # (config_name, prompt_text, default_value, is_secret, section, filepath)
    ("token", "IBMQ API Token", None, True, "ibmq", ibmq_config_path),
    ("url", "", account_url, False, "ibmq", ibmq_config_path),
    ("verify", "", "True", False, "ibmq", ibmq_config_path),
]

IBMQ_DEVICES = {
    "Armonk": "ibmq_armonk",
    "Belem": "ibmq_belem",
    "Bogota": "ibmq_bogota",
    "Clifford Simulator": "simulator_stabilizer",
    "Extended Clifford Simulator": "simulator_extended_stabilizer",
    "Lima": "ibmq_lima",
    "Manila": "ibmq_manila",
    "MPS Simulator": "simulator_mps",
    "QASM Simulator": "ibmq_qasm_simulator",
    "Quito": "ibmq_quito",
    "Santiago": "ibmq_santiago",
    "Statevector Simulator": "simulator_statevector",
    "Yorktown": "ibmq_5_yorktown",
}


AER_DEVICES = {
    "AerSimulator": AerSimulator(),
    "PulseSimulator": PulseSimulator(),
    "QasmSimulator": QasmSimulator(),  # Aer.getbackend('qasm_simulator') also works
    "StatevectorSimulator": StatevectorSimulator(),
    "UnitarySimulator": UnitarySimulator(),
    "BasicAer StatevectorSimulator": StatevectorSimulatorPy(),
    "BasicAer UnitarySimulator": UnitarySimulatorPy(),
    "BasicAer QasmSimulator": QasmSimulatorPy(),
}

QISKIT_PROVIDERS = {
    "IBMQ": IBMQ_DEVICES,
    "AER": AER_DEVICES,
}
