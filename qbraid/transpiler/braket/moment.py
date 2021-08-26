"""BraketMomentWrapper Class"""

from braket.circuits.moments import Moments as BraketMoment

from qbraid.transpiler.moment import MomentWrapper
from qbraid.transpiler.braket.instruction import BraketInstructionWrapper


class BraketMomentWrapper(MomentWrapper):
    """Wrapper class for Amazon Braket ``Moment`` objects."""

    def __init__(self, moment: BraketMoment):
        """Create a BraketMomentWrapper

        Args:
            moment: the Braket ``Moment`` object to be wrapped.

        """
        super().__init__()
        self.moment = moment
        # No value for 'qubits' argument in constructor call
        self._instructions = [BraketInstructionWrapper(i) for i in moment.instructions]
