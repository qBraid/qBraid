import matplotlib.pyplot as plt
from ..result import Result


class IBMAerResult(Result):
    def __init__(self, result, circuit=None):

        super().__init__()
        self.result = result
        self.circuit = circuit

    def get_counts(self):

        return self.result.get_counts()

    def plot_histogram(self):

        rdict = self.get_counts()

        return plt.bar(rdict.keys(), rdict.values(), 0.5)

    def get_statevector(self):

        return self.result.get_statevector(self.circuit.circuit)
