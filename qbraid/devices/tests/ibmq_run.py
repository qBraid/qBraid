import numpy as np
from qiskit import QuantumCircuit, transpile

from qbraid.api.ibmq_api import ibmq_get_provider

if __name__ == "__main__":

    qc = QuantumCircuit(1, 1)

    qc.h(0)
    qc.ry(np.pi / 4, 0)
    qc.rz(np.pi / 2, 0)
    qc.measure(0, 0)

    provider = ibmq_get_provider()
    backend = provider.get_backend("ibmq_armonk")
    transpiled = transpile(qc, backend=backend)
    job = backend.run(transpiled)
    print(job.status())
