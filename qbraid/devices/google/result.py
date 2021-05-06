# result
from ..result import Result
from collections import Counter

class GoogleResult(Result):
    
    def __init__(self, results):
        self.results = results
    
    def measurements(self):
        return self.results.measurements
    
    def get_counts(self):
        meas = self.measurements()
        repetitions = len(meas[0])
        
        outcomes = [[meas[x][y][0] for x in meas.keys()] for y in range(repetitions)]

        #convert bit list to bit strings
        out = [''.join(str(_) for _ in bit_list) for bit_list in outcomes]
        
        return Counter(out)