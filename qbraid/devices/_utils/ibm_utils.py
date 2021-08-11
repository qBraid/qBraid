# pylint: skip-file

import os

from qiskit import Aer, BasicAer

from .user_config import qbraid_config_path

ibmq_config_path = os.path.join(os.path.expanduser("~"), ".qiskit", "qiskitrc")
account_url = "https://auth.quantum-computing.ibm.com/api"

IBMQ_CONFIG_PROMPT = [
    # (config_name, prompt_text, default_value, is_secret, section, filepath)
    ("token", "IBMQ API Token", None, True, "ibmq", ibmq_config_path),
    ("url", "", account_url, False, "ibmq", ibmq_config_path),
    ("verify", "", "True", False, "ibmq", ibmq_config_path),
    ("group", "Group name (optional)", "open", False, "IBM", qbraid_config_path),
    ("project", "Project name (optional)", "main", False, "IBM", qbraid_config_path),
    ("verify", "", "True", False, "IBM", qbraid_config_path),
]

IBMQ_DEVICES = {
    "armonk": "ibmq_armonk",
    "belem": "ibmq_belem",
    "bogota": "ibmq_bogota",
    "lima": "ibmq_lima",
    "manila": "ibmq_manila",
    "quito": "ibmq_quito",
    "santiago": "ibmq_santiago",
    # "yorktown": "ibmq_5_yorktown",  # not available
    "simulator_stabilizer": "simulator_stabilizer",
    "simulator_stabilizer_ext": "simulator_extended_stabilizer",
    "simulator_mps": "simulator_mps",
    "simulator_qasm": "ibmq_qasm_simulator",
    "simulator_statevector": "simulator_statevector",
    "least_busy_qpu": "least_busy",
}

AER_DEVICES = {
    "simulator_aer": Aer.get_backend("aer_simulator"),
    "simulator_pulse": Aer.get_backend("pulse_simulator"),
    "simulator_qasm": Aer.get_backend("qasm_simulator"),
    "simulator_statevector": Aer.get_backend("statevector_simulator"),
    "simulator_unitary": Aer.get_backend("unitary_simulator"),
}

BASIC_AER_DEVICES = {
    "simulator_qasm": BasicAer.get_backend("qasm_simulator"),
    "simulator_statevector": BasicAer.get_backend("statevector_simulator"),
    "simulator_unitary": BasicAer.get_backend("unitary_simulator"),
}

# RUNTIME = {
#     "coming_soon": None,  # https://qiskit.org/documentation/partners/qiskit_runtime/
# }
#
# IONQ_DEVICES = {
#     "TO-DO": None,  # https://qiskit.org/documentation/partners/ionq/guides/install.html
# }

QISKIT_PROVIDERS = {
    "IBMQ": IBMQ_DEVICES,
    "Aer": AER_DEVICES,
    "BasicAer": BASIC_AER_DEVICES,
}
