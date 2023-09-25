.. _guide_circuits:

Circuits
=========

In this module, you will learn how to use the qBraid SDK to interface with
quantum circuit objects accross various frontends. We will demonstrate how to
use the transpiler to convert circuits between packages, and highlight a few
other circuit-based convenience features.

Program Types
--------------

Supported frontend program types include `Qiskit <QiskitQuantumCircuit>`_,
`Amazon Braket <BraketCircuit>`_, `Cirq <CirqCircuit>`_, `PyQuil <PyQuilProgram>`_,
`PyTKET <PyTKETCircuit>`_, and `OpenQASM <OpenQASMString>`_:

.. code-block:: python
    
    >>> from qbraid import QPROGRAM_TYPES
    >>> for k in QPROGRAM_TYPES:
    ...     print(k)
    ...
    braket.circuits.circuit.Circuit
    cirq.circuits.circuit.Circuit
    qiskit.circuit.quantumcircuit.QuantumCircuit
    pyquil.quil.Program
    pytket._tket.circuit.Circuit
    qasm2
    qasm3


.. _QiskitQuantumCircuit: https://qiskit.org/documentation/stubs/qiskit.circuit.QuantumCircuit.html
.. _BraketCircuit: https://docs.aws.amazon.com/braket/latest/developerguide/braket-constructing-circuit.html
.. _CirqCircuit: https://quantumai.google/reference/python/cirq/circuits/Circuit
.. _PyQuilProgram: https://pyquil-docs.rigetti.com/en/stable/basics.html
.. _PyTKETCircuit: https://cqcl.github.io/tket/pytket/api/circuit_class.html
.. _OpenQASMString: https://openqasm.com/language/index.html


Circuit Wrapper
----------------

We'll start with a simple qiskit circuit that creates the bell state.

.. code-block:: python
    
    from qiskit import QuantumCircuit
    
    def bell():
        circuit = QuantumCircuit(2)
        circuit.h(0)
        circuit.cx(0,1)
        return circuit


.. code-block:: python

    >>> qiskit_circuit = bell()
    >>> qiskit_circuit.draw()
         ┌───┐     
    q_0: ┤ H ├──■──
         └───┘┌─┴─┐
    q_1: ─────┤ X ├
              └───┘


Next, we'll apply the qbraid circuit wrapper.

.. code-block:: python

    from qbraid import circuit_wrapper

    qprogram = circuit_wrapper(qiskit_circuit)


Each circuit wrapper object has ``num_qubits`` and ``depth`` attributes, regardless of the input circuit type.
The underlying "wrapped" circuit can be accessed using the circuit wrapper's ``program`` attribute.

.. code-block:: python

    >>> qprogram.num_qubits
    2
    >>> qprogram.depth
    2
    >>> type(qprogram.program)
    qiskit.circuit.quantumcircuit.QuantumCircuit


Transpiler
-----------

Now, we can use the ``qbraid.transpiler.QuantumProgram.transpile`` method to convert to wrapped circuit into
any other supported program type. Simply pass in the name of the target package from one of ``qbraid.QPROGRAM_LIBS``.
For example, use input ``"braket"`` to return a ``braket.circuits.Circuit``:

.. code-block:: python

    >>> braket_circuit = qprogram.transpile("braket")
    >>> print(braket_circuit)
    T  : |0|1|
            
    q0 : -H-C-
            |   
    q1 : ---X-

    T  : |0|1|


This time, using the same origin circuit wrapper, we'll input ``"pyquil"`` to return a ``pyquil.quil.Program``:

.. code-block:: python

    >>> pyquil_program = qprogram.transpile("pyquil")
    >>> print(pyquil_program)
    H 0
    CNOT 0 1


Interface
-----------

The ``qbraid.interface`` module contains a number of functions that can be helpful for testing, quick calculations,
verification, or other general use.

Random circuits
^^^^^^^^^^^^^^^^^

The ``random_circuit`` function creates a random circuit of any supported frontend program type. Here, we've created a
random ``cirq.Circuit`` with four qubits and depth four.

.. code-block:: python

    >>> from qbraid.interface import random_circuit
    >>> cirq_circuit = random_circuit("cirq", num_qubits=4, depth=4)
    >>> print(cirq_circuit)
          ┌──────┐   ┌──┐           ┌──┐
    0: ────iSwap───────@────@───Z──────────
           │           │    │
    1: ────┼──────────X┼────@───@────@─────
           │          ││        │    │
    2: ────┼────Z─────┼@────────X────┼H────
           │          │              │
    3: ────iSwap──────@─────H────────X─────
          └──────┘   └──┘           └──┘


Unitary calculations
^^^^^^^^^^^^^^^^^^^^^

The ``unitary`` method will calculate the matrix representation of an input circuit of any
supported program type.

.. code-block:: python

    >>> from qbraid import circuit_wrapper
    >>> cirq_unitary = circuit_wrapper(cirq_circuit).unitary()
    >>> cirq_unitary.shape
    (16, 16)

We can now apply the circuit wrapper to the random Cirq circuit above, and use the transpiler to return the equivalent ``pyquil.Program``:

.. code-block:: python
    
    >>> pyquil_circuit = circuit_wrapper(cirq_circuit).transpile("pyquil")
    >>> print(pyquil_circuit)
    ISWAP 0 3
    Z 1
    CNOT 0 2
    CZ 3 1
    CZ 2 3
    H 0
    Z 3
    CNOT 2 1
    CNOT 2 0
    H 1


To verify the equivalence of the two circuits, we can use the ``circuits_allclose`` method.
It applies the ``unitary`` method to both input circuits, compares the outputs via ``numpy.allclose``, and returns the result.

.. code-block:: python

    >>> from qbraid.interface import circuits_allclose
    >>> circuits_allclose(cirq_circuit, pyquil_circuit)
    True


Qubit Indexing
^^^^^^^^^^^^^^^

As a tool for interfacing between frontend modules, the qBrad SDK has a number of
methods and functions dedicated to resolving any potential compatibility issues. For
instance, each frontend has slightly different rules and standard conventions when it
comes to qubit indexing. Functions and/or methods in some modules require that circuits
are constructed using contiguous qubits i.e. sequential qubit indexing, while others
do not. The ``convert_to_contiguous`` method can be used to map qubit indicies accordingly,
and address compatibility issues without re-constructing each circuit.

For example, let's look at a Braket circuit that creates a GHZ state.

.. code-block:: python

    from braket.circuits import Circuit

    def ghz():
        circuit = Circuit()
        circuit.h(0)
        circuit.cnot(0, 2)
        circuit.cnot(2, 4)
        return circuit

Notice, our three-qubit circuit uses qubit indicies ``[0,2,4]``:

.. code-block:: python

    >>> braket_circuit = ghz()
    >>> print(braket_circuit)
    T  : |0|1|2|
            
    q0 : -H-C---
            |   
    q2 : ---X-C-
              | 
    q4 : -----X-

    T  : |0|1|2|


From here, we can use ``convert_to_contiguous`` to map the circuit to the ``[0,1,2]`` convention.
If the use-case requires using the dimensionality of the maximally indexed qubit, you
can set ``expansion=True`` to append identity gates to "vacant" registers instead of
performing the qubit mapping.

.. code-block:: python

    >>> from qbraid.interface import convert_to_contiguous
    >>> print(convert_to_contiguous(braket_circuit))
    T  : |0|1|2|
            
    q0 : -H-C---
            |   
    q1 : ---X-C-
              | 
    q2 : -----X-

    T  : |0|1|2|
    >>> print(convert_to_contiguous(braket_circuit, expansion=True))
    T  : |0|1|2|
            
    q0 : -H-C---
            |   
    q1 : -I-|---
            |   
    q2 : ---X-C-
              | 
    q3 : -I---|-
              | 
    q4 : -----X-

    T  : |0|1|2|
