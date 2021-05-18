import matplotlib.pyplot as plt

from ..result import Result
from ..visualization import plot_histogram as visualize_histogram


from .devices import IBMAerDevice, IBMQDevice


def get_ibm_result(device, job):

    if isinstance(device, IBMAerDevice):
        return IBMAerResult(job)

    elif isinstance(device, IBMQDevice):
        pass


class IBMAerResult(Result):
    def __init__(self, job, circuit=None):

        self.job = job
        self.result = job.result()
        self.circuit = circuit

    def get_counts(self):
        return self.result.get_counts()

    def plot_histogram(self):

        rdict = self.get_counts()

        return plt.bar(rdict.keys(), rdict.values(), 0.5)

    def get_statevector(self, decimals=3):

        return self.result.get_statevector(self.circuit.circuit)
