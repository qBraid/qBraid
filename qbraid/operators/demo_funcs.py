from qiskit import QuantumCircuit, Aer, execute


def quantum_hello_bye_world():
    circ = QuantumCircuit(1, 1)
    circ.measure([0], [0])
    backend_sim = Aer.get_backend("qasm_simulator")
    sim = execute(circ, backend_sim, shots=1)
    sim_result = sim.result()
    counts = sim_result.get_counts(circ)
    for key in counts:
        if key == "0":
            print("Hello World!")
        elif key == "1":
            print("Bye World!")


def aloha_quantum_world(input_str="classical"):
    circ = QuantumCircuit(1, 1)
    if input_str == "quantum":
        circ.h(0)

    circ.measure([0], [0])

    backend_sim = Aer.get_backend("qasm_simulator")
    sim = execute(circ, backend_sim, shots=1)
    sim_result = sim.result()
    counts = sim_result.get_counts(circ)
    for key in counts:
        if key == "0":
            print("Hello World!")
        elif key == "1":
            print("Bye World!")

# defining a desired qubit state with a circuit
