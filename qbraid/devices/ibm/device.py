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

from qbraid.devices.device import DeviceLikeWrapper
from .job import QiskitJobWrapper
from .._utils import QISKIT_PROVIDERS, QiskitRunInput


class QiskitBackendWrapper(DeviceLikeWrapper):
    def __init__(self, name, provider, **fields):
        """Qiskit ``Backend`` wrapper class

        Args:
            name (str): a Qiskit supported device
            provider (str): the provider that this device comes from
            fields: kwargs for the values to use to override the default options.

        Raises:
            AttributeError: if input field not a valid options

        """
        super().__init__(name, provider, **fields)
        self._vendor = "IBM"
        self.vendor_dlo = self._get_device_obj(QISKIT_PROVIDERS)

    @classmethod
    def _default_options(cls):
        """Return the default options

        This method will return a :class:`qiskit.providers.Options` subclass object that will be
        used for the default options. These should be the default parameters to use for the
        options of the backend.

        Returns:
            qiskit.providers.Options: A options object with default values set

        """
        pass

    def run(self, run_input: QiskitRunInput, **options) -> QiskitJobWrapper:
        """Run on the qiskit backend.

        This method that will return a :class:`~qiskit.providers.Job` object that run circuits.
        Depending on the backend this may be either an async or sync call. It is the discretion of
        the provider to decide whether running should  block until the execution is finished or not.
        The Job class can handle either situation.

        Args:
            run_input (QuantumCircuit or Schedule or list): An individual or a list of
                :class:`~qiskit.circuits.QuantumCircuit` or :class:`~qiskit.pulse.Schedule` objects
                to run on the backend.
            options: Any kwarg options to pass to the backend for running the config. If a key is
                also present in the options attribute/object then the expectation is that the value
                specified will be used instead of what's set in the options object.

        Returns:
            QiskitJobWrapper: The :class:`~qbraid.devices.ibm.job.QiskitJobWrapper` job object for
            the run.

        """
        qiskit_device = self.vendor_dlo
        qiskit_job = qiskit_device.run(run_input, **options)
        qbraid_job = QiskitJobWrapper(self, qiskit_job)
        return qbraid_job
