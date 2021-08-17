# This code is part of Qiskit.
#
# (C) Copyright IBM 2017.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of the source tree https://github.com/Qiskit/qiskit-terra/blob/main/LICENSE.txt
# or at http://www.apache.org/licenses/LICENSE-2.0.
#
# NOTICE: This file has been modified from the original:
# https://github.com/Qiskit/qiskit-terra/blob/main/qiskit/providers/backend.py

"""QiskitBackendWrapper Class"""

from qiskit import IBMQ
from qiskit import execute
from qiskit.providers.ibmq import least_busy
from qiskit.utils.quantum_instance import QuantumInstance

from qbraid.devices._utils import get_config
from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.ibm.job import QiskitJobWrapper


class QiskitBackendWrapper(DeviceLikeWrapper):
    """Wrapper class for IBM Qiskit ``Backend`` objects."""

    def __init__(self, name, provider, **fields):
        """Create a QiskitBackendWrapper

        Args:
            name (str): a Qiskit supported device
            provider (str): the provider that this device comes from
            fields: kwargs for the values to use to override the default options.

        Raises:
            DeviceError: if input field not a valid options

        """
        super().__init__(name, provider, vendor="ibm", **fields)
        self.quantum_instance = QuantumInstance(self.vendor_dlo)

    def _init_cred_device(self, device_ref):
        """Initialize an IBM credentialed device."""
        if IBMQ.active_account() is None:
            IBMQ.load_account()
        group = get_config("group", "IBM")
        project = get_config("project", "IBM")
        provider = IBMQ.get_provider(hub="ibm-q", group=group, project=project)
        if device_ref == "least_busy":
            backends = provider.backends(filters=lambda x: not x.configuration().simulator)
            return least_busy(backends)
        return provider.get_backend(device_ref)

    @classmethod
    def _default_options(cls):
        """Return the default options

        This method will return a :class:`qiskit.providers.Options` subclass object that will be
        used for the default options. These should be the default parameters to use for the
        options of the backend.

        Returns:
            qiskit.providers.Options: A options object with default values set

        """

    def run(self, run_input, *args, **kwargs) -> QiskitJobWrapper:
        """Run on the qiskit backend.

        This method that will return a :class:`~qiskit.providers.Job` object that run circuits.
        Depending on the backend this may be either an async or sync call. It is the discretion of
        the provider to decide whether running should  block until the execution is finished or not.
        The Job class can handle either situation.

        Args:
            run_input (QuantumCircuit or Schedule or list): An individual or a list of
                :class:`~qiskit.circuits.QuantumCircuit` or :class:`~qiskit.pulse.Schedule` objects
                to run on the backend.
            kwargs: Any kwarg options to pass to the backend for running the config. If a key is
                also present in the options attribute/object then the expectation is that the value
                specified will be used instead of what's set in the options object.

        Returns:
            :class:`~qbraid.devices.ibm.job.QiskitJobWrapper`: The job like object for the run.

        """
        run_input = self._compat_run_input(run_input)
        qiskit_device = self.vendor_dlo
        qiskit_job = execute(run_input, qiskit_device, *args, **kwargs)
        qbraid_job = QiskitJobWrapper(self, qiskit_job)
        return qbraid_job
