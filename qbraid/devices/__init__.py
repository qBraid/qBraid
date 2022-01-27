"""
====================================
 Devices (:mod:`qbraid.devices`)
====================================

.. currentmodule:: qbraid.devices

Overview
---------
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus viverra auctor euismod.
Nullam feugiat ante eget diam ultrices imperdiet. In bibendum lorem tincidunt tincidunt feugiat.
Phasellus ac nibh non massa tincidunt consectetur eget ultrices massa. Sed pulvinar gravida odio
quis posuere. Sed nibh leo, egestas vitae iaculis id, dignissim eget massa. Nullam bibendum cursus
elit a efficitur. Maecenas dignissim, justo id tincidunt feugiat, quam est bibendum velit, ultrices
sagittis nibh magna quis nunc. Fusce ullamcorper dictum nibh, sit amet molestie dolor semper vel.

Example Usage
--------------

    .. code-block:: python

        import cirq
        import qbraid

        # Create a cirq circuit
        q0, q1 = [cirq.LineQubit(i) for i in range(2)]
        cirq_circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))

        # Run circuit on any supported device using the qraid device wrapper
        qbraid_device = qbraid.device_wrapper("ibm_aer_default_sim")
        qbraid_job = qbraid_device.run(cirq_circuit)  # run cirq circuit on IBM Aer simulator
        qbraid_result = qbraid_job.result
        print(qbraid_result.data)  # view the raw data from the run
        ...

Devices API
------------

.. autosummary::
   :toctree: ../stubs/

   DeviceLikeWrapper
   JobLikeWrapper
   LocalJobWrapper
   ResultWrapper
   get_devices
   update_config
   ibmq_least_busy_qpu
   DeviceStatus
   JobStatus
   DeviceError
   JobError
   ConfigError

"""
from ._utils import get_devices, ibmq_least_busy_qpu, update_config
from .device import DeviceLikeWrapper
from .enums import DeviceStatus, JobStatus
from .exceptions import ConfigError, DeviceError, JobError
from .job import JobLikeWrapper
from .localjob import LocalJobWrapper
from .result import ResultWrapper
