"""
==================================================
Transpiler (:mod:`qbraid.transpiler`)
==================================================

.. currentmodule:: qbraid.transpiler

Overview
---------
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus viverra auctor euismod.
Nullam feugiat ante eget diam ultrices imperdiet. In bibendum lorem tincidunt tincidunt feugiat.
Phasellus ac nibh non massa tincidunt consectetur eget ultrices massa. Sed pulvinar gravida odio
quis posuere. Sed nibh leo, egestas vitae iaculis id, dignissim eget massa. Nullam bibendum cursus
elit a efficitur. Maecenas dignissim, justo id tincidunt feugiat, quam est bibendum velit, ultrices
sagittis nibh magna quis nunc. Fusce ullamcorper dictum nibh, sit amet molestie dolor semper vel.

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

Transpiler API
---------------

.. autosummary::
   :toctree: ../stubs/

   QbraidTranspiler
   CircuitWrapper
   GateWrapper
   ParamID
   ParameterWrapper
   TranspileError

"""
from .transpiler import QbraidTranspiler
from .circuit import CircuitWrapper
from .gate import GateWrapper
from .parameter import ParamID, ParameterWrapper
from .exceptions import TranspilerError

