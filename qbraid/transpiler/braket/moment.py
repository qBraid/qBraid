"""BraketMomentWrapper Class"""

from braket.circuits.moments import Moments as BraketMoment

from qbraid.transpiler.braket.instruction import BraketInstructionWrapper
from qbraid.transpiler.moment import MomentWrapper


class BraketMomentWrapper(MomentWrapper):
    """Wrapper class for Amazon Braket ``Moment`` objects."""

    def __init__(self, moment: BraketMoment):
        """Create a BraketMomentWrapper

        Args:
            moment: the Braket ``Moment`` object to be wrapped.

        """
        super().__init__()
        self.moment = moment
        # https://github.com/qBraid/qBraid/issues/28
        self._instructions = [BraketInstructionWrapper(i) for i in moment.instructions] # pylint: disable=no-value-for-parameter
