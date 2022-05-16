"""BraketQuantumtaskWrapper Class"""

from typing import TYPE_CHECKING

from qbraid.devices.localjob import LocalJobWrapper

from .result import BraketResultWrapper

if TYPE_CHECKING:
    import qbraid


class BraketLocalQuantumTaskWrapper(LocalJobWrapper):
    """Wrapper class for Amazon Braket ``LocalQuantumTask`` objects."""

    @property
    def id(self) -> str:
        """Return a unique id identifying the job."""
        return self.vendor_jlo.id

    def metadata(self) -> dict:
        """Return the metadata regarding the job."""
        return dict(self.vendor_jlo.result().task_metadata)

    def result(self) -> "qbraid.devices.aws.BraketResultWrapper":
        """Return the results of the job."""
        return BraketResultWrapper(self.vendor_jlo.result())
