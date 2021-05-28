from typing import Iterable, Union
from braket.circuits.moments import Moments as BraketMoments
from cirq.ops.moment import Moment as CirqMoment

# from .instruction import Instruction

Instruction = None

qB_MomentInput = Union["BraketMoments", "CirqMoment", Iterable[Instruction]]


class Moment:
    def __init__(self, moment: qB_MomentInput = None, time_slice: int = None):

        self.moment = moment

        if isinstance(moment, BraketMoments):
            pass
        elif isinstance(moment, CirqMoment):
            self.instructions = [Instruction(i) for i in moment.operations]
            self.qubits = moment.qubits

        """
        self._holding = True
        if type(moment) == Iterable[qB_Instruction]:
            self._holding = False
            
            if time_slice == None:
                print("Error: pass time_slice integer when attempting to define new moment with 
                Instruction set")
                raise # TODO: implement exceptions
                
            self.instruction_set = moment
            self.time_slice = time_slice
            
            self._moment = self
         
        if self._holding:
            self._moment = moment
       """

    def __str__(self):
        if self._holding:
            return str(self._moment)
        return (
            "At time step = " + str(self.time_slice) + ": " + str(self.instruction_set)
        )
