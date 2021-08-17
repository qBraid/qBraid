"""
====================================
 Circuits (:mod:`qbraid.circuits`)
====================================

.. currentmodule:: qbraid.circuits

Overview
---------
The qbraid circuit layer is designed as a lightweight infrastructure for creating
circuits. Without the machinery to interface with devices directly, the qBraid circuit
layer is built primarily for interfacing with the qBraid transpiler. For this reason,
the structure of this circuit layer mirrors that of the transpiler
wrapper classes closely.

The circuit layer also mirrors cirq in its use of moments and instructions. However,
parameters are stored globally. Qubits are simply integers.

Example Usage
--------------

To create a circuit simply, the following code will suffice.

    .. code-block:: python

        import numpy as np
        from qbraid.circuits import Circuit, RX, drawer

        circuit = Circuit(3) #create a circuit with 3 qubits
        circuit.add_instruction('H',0)
        circuit.add_instruction('RX',np.pi/2,2)
        circuit.add_instruction('CX',[1,2])

        crx_gate = RX(np.pi/4).control()
        circuit.append(crx_gate([0,1]))

        drawer(circuit)
        ...

The string passed to the ``add_instruction`` argument follows the convention of the
transpiler, which is documented here.

For more explicit control over Moments, Instructions, and Gates, the following code shows
how circuits can be created more directly.

    .. code-block:: python

        from qbraid.circuits import Circuit, Instruction, Moment, H, RX, drawer
        from numpy import pi

        circuit = Circuit(3)

        h = H()
        instr_h0 = Instruction(h,0)
        instr_h1 = Instruction(h,1)

        moment = Moment([instr_h0,instr_h1])

        instr_rx0 = RX(pi/2)(0)
        instr_rx2 = RX(pi/4)(2)
        circuit.append(moment)
        circuit.append(instr_rx0)
        circuit.append(instr_rx2)

        drawer(circuit)

Circuits API
-------------

.. autosummary::
   :toctree: ../stubs/

   Circuit
   Gate
   Instruction
   Moment
   Qubit
   UpdateRule
   Parameter
   CircuitError
   drawer

"""
from .circuit import Circuit
from .gate import Gate
from .instruction import Instruction
from .moment import Moment
from .qubit import Qubit
from .update_rule import UpdateRule
from .parameter import Parameter
from .exceptions import CircuitError
from .drawer import drawer

from .instruction import (
    Instruction,
)

from .moment import (
    Moment,
)

from .update_rule import (
    UpdateRule,
)

from .library.standard_gates import (
    DCX,
    H,
    CH,
    HPow,
    I,
    iSwap,
    Measure,
    Phase,
    CPhase,
    pSwap,
    R,
    RX,
    RXX,
    RXY,
    RY,
    RYY,
    RZ,
    RZZ,
    RZX,
    S,
    Sdg,
    Swap,
    SX,
    SXdg,
    T,
    Tdg,
    U,
    U1,
    U2,
    U3,
    X,
    CX,
    XPow,
    Y,
    CY,
    YPow,
    CZ,
    Z,
    ZPow,
)

from .parameter import Parameter
from .parametertable import ParameterTable
