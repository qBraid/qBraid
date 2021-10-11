"""Module for Cirq device-like object wrappers."""

import warnings

from cirq import DensityMatrixSimulator, Simulator, measure

from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.enums import DeviceStatus
from qbraid.devices.exceptions import DeviceError
from qbraid.devices.google.result import CirqResultWrapper


class CirqSimulatorWrapper(DeviceLikeWrapper):
    """Wrapper class for Google Cirq ``Simulator`` objects."""

    def __init__(self, device_info, **kwargs):
        """Create CirqSimulatorWrapper."""

        super().__init__(device_info, **kwargs)

    def _get_device(self):
        """Initialize a Google device."""
        if self._obj_ref == "Simulator":
            return Simulator()
        elif self._obj_ref == "DensityMatrixSimulator":
            return DensityMatrixSimulator()
        else:
            raise DeviceError(f"obj_ref {self._obj_ref} not found.")

    @property
    def status(self):
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        return DeviceStatus.ONLINE

    def run(self, run_input, *args, **kwargs):
        """Samples from the given Circuit.

        Args:
            run_input: The circuit, i.e. program, to sample from.

        Keyword Args:
            shots (int): The number of times to sample. Default is 1.

        Returns:
            qbraid.devices.google.CirqResultWrapper: The result like object for the run.

        """
        if "shots" in kwargs:
            kwargs["repetitions"] = kwargs.pop("shots")
        run_input, qbraid_circuit = self._compat_run_input(run_input)
        if not run_input.has_measurements():
            warnings.warn(
                "Circuit has no measurements to sample. Applying measurement gate to all qubits "
                "and continuing run.",
                UserWarning,
            )
            qubits = list(run_input.all_qubits())
            measure_all = [measure(q, key=str(q.x)) for q in qubits]
            run_input.append(measure_all)
        cirq_result = self.vendor_dlo.run(run_input, *args, **kwargs)
        return CirqResultWrapper(cirq_result)
