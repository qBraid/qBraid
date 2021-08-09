# pylint: skip-file

import os

from qiskit import Aer, BasicAer

ibmq_config_path = os.path.join(os.path.expanduser("~"), ".qiskit", "qiskitrc")
account_url = "https://auth.quantum-computing.ibm.com/api"

IBMQ_CONFIG_PROMPT = [
    # (config_name, prompt_text, default_value, is_secret, section, filepath)
    ("token", "IBMQ API Token", None, True, "ibmq", ibmq_config_path),
    ("url", "", account_url, False, "ibmq", ibmq_config_path),
    ("verify", "", "True", False, "ibmq", ibmq_config_path),
]

IBMQ_DEVICES = {
    "armonk": "ibmq_armonk",
    "belem": "ibmq_belem",
    "bogota": "ibmq_bogota",
    "lima": "ibmq_lima",
    "manila": "ibmq_manila",
    "quito": "ibmq_quito",
    "santiago": "ibmq_santiago",
    "yorktown": "ibmq_5_yorktown",
    "simulator_stabilizer": "simulator_stabilizer",
    "simulator_stabilizer_ext": "simulator_extended_stabilizer",
    "simulator_mps": "simulator_mps",
    "simulator_qasm": "ibmq_qasm_simulator",
    "simulator_statevector": "simulator_statevector",
}

AER_DEVICES = {
    "simulator_aer": Aer.get_backend("aer_simulator"),
    "simulator_pulse": Aer.get_backend("pulse_simulator"),
    "simulator_qasm": Aer.get_backend("qasm_simulator"),
    "simulator_statevector": Aer.get_backend("statevector_simulator"),
    "simulator_unitary": Aer.get_backend("unitary_simulator"),
    "local_simulator_qasm": BasicAer.get_backend("qasm_simulator"),
    "local_simulator_statevector": BasicAer.get_backend("statevector_simulator"),
    "local_simulator_unitary": BasicAer.get_backend("unitary_simulator"),
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
}
