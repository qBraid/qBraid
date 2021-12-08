"""CirqMomentWrapper Class"""

from cirq.ops import Moment as CirqMoment

from qbraid.transpiler.cirq.instruction import CirqInstructionWrapper
from qbraid.transpiler.moment import MomentWrapper


class CirqMomentWrapper(MomentWrapper):
    """Wrapper class for Cirq ``Moment`` objects."""

    def __init__(self, moment: CirqMoment, instructions=None):
        """Create a CirqMomentWrapper

        Args:
            moment: the cirq ``Moment`` object to be wrapped
            instructions (optional, list): the instructions associated with this moment"""

        super().__init__()
        self.moment = moment
        if not instructions:
            # https://github.com/qBraid/qBraid/issues/28
            self._instructions = [CirqInstructionWrapper(i) for i in moment.instructions] # pylint: disable=no-value-for-parameter
        else:
            self._instructions = instructions
