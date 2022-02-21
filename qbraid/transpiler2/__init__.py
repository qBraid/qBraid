"""
==================================================
Transpiler (:mod:`qbraid.transpiler2`)
==================================================

.. currentmodule:: qbraid.transpiler2

Overview
---------
The qBraid transpiler accepts circuit objects constructed using one of the 
standard quantum computing packages, and produces a circuit object of the 
same circuit constructed using a different package. 

The transpiler maintains as much abstract information as possible during 
the transpilation process, though the result will not necessarily be identical.
For example, a particular two-qubit rotation gate might be implemented in one package
abstractly, but only constructable as an arbitrary unitary gate in another. See
this mapping page for more information about gate equivalences in various packages.

The transpiler layer eliminates the need for implementing a circuit multiple times 
in various packages for the purposing of using the devices associate with that pacakge.
In conjunction with the qBraid device layer, it is possible to execute a single circuit 
on multiple families of devices without calling this transpiler directly.

Example Usage
--------------

    .. code-block:: python

        from braket.circuits import Circuit
        from qbraid import circuit_wrapper

        # Create a braket circuit
        braket_circuit = Circuit().h(0).cnot(0, 1)

        # Transpile to circuit of any supported package using qbraid circuit wrapper
        qbraid_circuit = circuit_wrapper(braket_circuit)
        qiskit_circuit = qbraid_circuit.transpile("qiskit")
        qiskit_circuit.draw()
        ...

Transpiler2 API
---------------

.. autosummary::
   :toctree: ../stubs/

   SUPPORTED_PROGRAM_TYPES
   QPROGRAM
   QuantumResult
   CircuitWrapper
   MeasurementResult
   Executor
   PauliString
   Observable
   interface
   
"""

# Interface between Cirq circuits and supported frontends.
from qbraid.transpiler2 import interface
# About and version.
from qbraid.transpiler2._about import about
# Quantum computer input/output.
from qbraid.transpiler2._typing import QPROGRAM, SUPPORTED_PROGRAM_TYPES, QuantumResult
from qbraid.transpiler2.circuit_wrapper import CircuitWrapper
# Executors and observables.
from qbraid.transpiler2.executor import Executor
from qbraid.transpiler2.observable import Observable, PauliString
from qbraid.transpiler2.rem.measurement_result import MeasurementResult

# from qbraid.transpiler2._version import __version__
