from IPython.display import IFrame
from IPython.core.display import display
from cirq import quirk_json_to_circuit

import qbraid

def make_quirk():
    display(IFrame(src='./quirk.html', width=1100, height=600))

def quirk_wrapper(quirk_json):
    cirq_circuit = quirk_json_to_circuit(quirk_json)
    return qbraid.circuit_wrapper(cirq_circuit)

