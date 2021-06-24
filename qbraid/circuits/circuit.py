from typing import Union, Iterable

from .instruction import Instruction
from .moment import Moment
from .qubit import Qubit

class Circuit:
    
    """
    Circuit class for qBraid quantum circuit objects.
    """
    
    def __init__(self, num_qubits, name: str = None):

        self._qubits = [Qubit(i) for i in range(num_qubits)]
        self._moments = []
        self.name = None
        
    @property
    def num_qubits(self):
        return len(self._qubits)
    
    @property
    def num_gates(self):
        raise NotImplementedError

    @property
    def moments(self):
        return self._moments
    
    @property
    def instructions(self):
        
        instructions_list = []
        for moment in self._moments:
            instructions_list.append(moment.instructions)
            
        return instructions_list     
    
    def _update_qubit_list(self, qubit_list: Iterable[Qubit]):
        
        #check if qubits are in global circuit list, add them if not
        for qubit in qubit_list:
            if qubit not in self._qubits:
                self._qubits.append(qubit)
    
    def _append(self, operation: Union[Moment, Instruction]):
        
        #update qubit list
        self._update_qubit_list(operation)    
        
        #TO DO how should we add operations to circuit (whether moments or instructions, or combinations of both)
        #one possible issue occurs if we follow the rule: if it can be added to the most recent moment, do that
        #otherwise create a new moment. then if we have say h(0), then cnot(0,1) creates a new moment.
        #but h(2) would then be added to the first moment not the second. is this bad? does this matter?
        #more research needed
    
    def _append_circuit(self, 
                        operation: Circuit, 
                        mapping: Union[list,dict]) -> None:
        
        """this is for adding subroutines to circuits. so if we have a 3-qubit subroutine,
        the user should specify [2,4,5], implying that qubit 0 on the subroutine is mapped
        to qubit 2 on the circuit, qubit 1 on the subroutine maps to qubit 4 on the circuit, etc.
        
        the user should also be able to specify directly as a dict:
            {0:2,1:4,5:5}
            
        """
        
        # TO DO validate mapping
        
        raise NotImplementedError
        
    
    def append(self, operation: Union[Instruction, Moment, Circuit, Iterable[Instruction, Moment]],
               mapping: Union[list,dict] = None) -> None:
        
        """
        Add an operation (moment or instruction) to the circuit.
        
        TO DO: rules
        """
        
        #TO DO validate instruction given from user
        if isinstance(operation, Circuit):
            self._append_circuit(operation, mapping)
        if isinstance(operation, Iterable):
            for op in operation.moments:
                self._append(op)
        elif isinstance(operation, Iterable):
            for op in operation: 
                self._append(op)
        else:
            self._append(operation)
        
        
    def __len__(self):
        raise NotImplementedError
        
    def __str__(self):
        print(f"Circuit with {self.num_qubits} and {self.num_gates}")
    
