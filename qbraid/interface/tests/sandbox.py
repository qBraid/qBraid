from qbraid.interface._programs import random_circuit

if __name__ == "__main__":

    circuit = random_circuit("braket", 2, 2)

    print(circuit)
