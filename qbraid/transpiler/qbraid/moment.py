"""QbraidMomentWrapper Class"""

from qbraid.circuits.moment import Moment as QbraidMoment
from qbraid.transpiler.moment import MomentWrapper
from qbraid.transpiler.qbraid.instruction import QbraidInstructionWrapper


class QbraidMomentWrapper(MomentWrapper):
    """Wrapper class for qBraid ``Moment`` objects."""

    def __init__(self, moment: QbraidMoment):
        """Create a QbraidMomentWrapper

        Args:
            moment: the qbraid ``Moment`` to be wrapped

        """
        super().__init__()
        self.moment = moment
        self._instructions = [QbraidInstructionWrapper(i) for i in moment.instructions]
