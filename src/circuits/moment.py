from typing import Any, Sequence, Dict, Iterable, Union

###################################

from circuits.instruction import qB_Instruction

from braket.circuits.moments import Moments as aws_Moments
from cirq.ops.moment import Moment as cirq_Moment

###################################

qB_MomentInput = Union["aws_Moments", "cirq_Moment", Iterable[qB_Instruction]]

class qB_Moment():
    def __init__(self, moment: qB_MomentInput = None, time_slice: int = None):
        
        self._holding = True
        if type(moment) == Iterable[qB_Instruction]:
            self._holding = False
            
            if time_slice == None:
                print("Error: pass time_slice integer when attempting to define new moment with Instruction set")
                raise # TODO: implement exceptions
                
            self.instruction_set = moment
            self.time_slice = time_slice
            
            self._moment = self
         
        if self._holding:
            self._moment = moment
            
    def __str__(self):
        if self._holding:
            return str(self._moment)
        return 'At time step = '+ str(self.time_slice) + ': ' + str(self.instruction_set)