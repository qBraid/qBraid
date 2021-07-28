from ..moment import MomentWrapper
from .instruction import CirqInstructionWrapper

from cirq.ops import Moment as CirqMoment

class CirqMomentWrapper(MomentWrapper):

    def __init__(self, moment: CirqMoment):
        
        self.instructions = [CirqInstructionWrapper(i) for i in \
            moment.instructions]

        self.moment = moment