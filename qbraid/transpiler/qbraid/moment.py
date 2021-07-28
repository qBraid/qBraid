from .instruction import QbraidInstructionWrapper
from ..moment import MomentWrapper

from qbraid.circuits.moment import Moment as QbraidMoment

class QbraidMomentWrapper(MomentWrapper):

    def __init__(self, moment: QbraidMoment):
        
        self.instructions = [QbraidInstructionWrapper(i) for i in \
            moment.instructions]

        self.moment = moment


