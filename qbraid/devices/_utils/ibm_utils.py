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

IBM_DEVICES = {
    "ibm_aer_default_sim": Aer.get_backend("aer_simulator"),
    "ibm_aer_pulse_sim": Aer.get_backend("pulse_simulator"),
    "ibm_aer_qasm_sim": Aer.get_backend("qasm_simulator"),
    "ibm_aer_sv_sim": Aer.get_backend("statevector_simulator"),
    "ibm_aer_unitary_sim": Aer.get_backend("unitary_simulator"),
    "ibm_basicaer_qasm_sim": BasicAer.get_backend("qasm_simulator"),
    "ibm_basicaer_sv_sim": BasicAer.get_backend("statevector_simulator"),
    "ibm_basicaer_unitary_sim": BasicAer.get_backend("unitary_simulator"),
    "ibm_q_ext_stabilizer_sim": "simulator_extended_stabilizer",
    "ibm_q_stabilizer_sim": "simulator_stabilizer",
    "ibm_q_mps_sim": "simulator_mps",
    "ibm_q_qasm_sim": "ibmq_qasm_simulator",
    "ibm_q_sv_sim": "simulator_statevector",
    "ibm_q_armonk": "ibmq_armonk",
    "ibm_q_belem": "ibmq_belem",
    "ibm_q_bogota": "ibmq_bogota",
    "ibm_q_lima": "ibmq_lima",
    "ibm_q_quito": "ibmq_quito",
    "ibm_q_manila": "ibmq_manila",
    "ibm_q_santiago": "ibmq_santiago",
    "ibm_q_least_busy_qpu": "least_busy",
    # "yorktown": "ibmq_5_yorktown",  # not available
}

# RUNTIME = {
#     "coming_soon": None,  # https://qiskit.org/documentation/partners/qiskit_runtime/
# }
