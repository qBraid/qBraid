from ..result import Result
from collections import Counter


class GoogleResult(Result):
    def __init__(self, result):

        super().__init__()
        self.result = result

    def measurements(self):
        return self.result.measurements

    def get_counts(self):
        meas = self.measurements()
        repetitions = len(list(meas.values())[0][0])
        outcomes = [[meas[x][y][0] for x in meas.keys()] for y in range(repetitions)]

        # convert bit list to bit strings
        out = ["".join(str(_) for _ in bit_list) for bit_list in outcomes]

        return Counter(out)
