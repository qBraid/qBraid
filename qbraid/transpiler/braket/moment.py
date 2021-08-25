from braket.circuits.moments import Moments as BraketMoment

from ..moment import MomentWrapper
from .instruction import BraketInstructionWrapper


class BraketMomentWrapper(MomentWrapper):
    def __init__(self, moment: BraketMoment):
        super().__init__()
        self.moment = moment
        self._instructions = [BraketInstructionWrapper(i) for i in moment.instructions]
