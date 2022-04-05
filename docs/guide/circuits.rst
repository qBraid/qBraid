.. _guide_circuits:

Circuits
=========

.. code-block:: python
    
    from braket.circuits import Circuit

    def bell():
        circuit = Circuit().h(0).cnot(0, 1)
        return circuit


.. code-block:: python
    
    from cirq import Circuit, LineQubit, ops

    def bell():
        q0, q1 = LineQubit.range(2)
        circuit = Circuit(ops.H(q0), ops.CNOT(q0, q1))
        return circuit


.. code-block:: python
    
    import pennylane as qml

    def bell():
        with qml.tape.QuantumTape() as tape:
            qml.Hadamard(wires=0)
            qml.CNOT(wires=[0, 1])
        return tape


.. code-block:: python
    
    from qiskit import QuantumCircuit

    def bell():
        circuit = QuantumCircuit(2)
        circuit.h(0)
        circuit.cx(0,1)
        return circuit


.. code-block:: python
    
    from pyquil import Program
    from pyquil.gates import H, CNOT

    def bell():
        program = Program()
        program += H(0)
        program += CNOT(0,1)
        return program


.. code-block:: python
    
    from qbraid import circuit_wrapper

    bell_circuit = bell()

    qbraid_circuit = circuit_wrapper(bell_circuit)
