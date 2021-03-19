from typing import Union

ParameterInput = Union[float,int]

class Parameter():
    
    def __init__(self, parameter: ParameterInput):
    
        if isinstance(parameter,Union[float,int]):
            self.value = parameter
        else:
            self.parameter = parameter

