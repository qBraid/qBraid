from ..device import Device

import cirq

Simulators = (cirq.Simulator)

class GoogleSimulatorDevice(Device):

    def __init__(self, device):
        
        super().__init__()
        
        self._name = "cirq Simulator"
        self._vendor_name = 'Google'
        self.device = device

    def validate_circuit(self):
        #check if a qbraid circuit can be run on this device
        pass    

def _get_google_device(device):
    
    if isinstance(device, Simulators):
        return GoogleSimulatorDevice(device)
    else:
        pass
