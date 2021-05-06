# execute google
from .result import GoogleResult


def _execute_google(circuit, device, shots=1):
    
    results = device.device.run(circuit, repetitions=shots)
    
    return GoogleResult(results)