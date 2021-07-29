from ..moment import MomentWrapper
from .instruction import BraketInstructionWrapper

from braket.circuits.moments import Moments as BraketMoment

class BraketMomentWrapper(MomentWrapper):

    def __init__(self, moment: BraketMoment):
        
        self.instructions = [BraketInstructionWrapper(i) for i in \
            moment.instructions]

        self.moment = moment