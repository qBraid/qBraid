
def get_package_type(obj):
    
    package_name = obj.__module__.split('.')[0]
    
    if package_name in ['qiskit','cirq','braket','qbraid']:
        return package_name
    else:
        print("Could not determine package for obj of type {}".format(type(obj)))