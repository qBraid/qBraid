"""QbraidTranspiler Class"""

from abc import ABC, abstractmethod


class QbraidTranspiler(ABC):
    """Abstract class for all wrapper objects used to build the qbraid transpiler."""

    @abstractmethod
    def transpile(self, package: str, *args, **kwargs):
        """Transpile a qbraid circuit, instruction, or gate wrapper object to an equivalent object
        of type specified by ``package``."""
