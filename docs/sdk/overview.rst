.. _sdk_overview:

Overview
=========

.. raw:: html
   
   <h1 style="text-align: center">
      <img src="../_static/logo.png" alt="qbraid logo" style="width:50px;height:50px;">
      <span> qBraid</span>
      <span style="color:#808080"> | SDK</span>
   </h1>
   <p style="text-align:center;font-style:italic;color:#808080">
      A Python toolkit for building and executing quantum programs.
   </p>

:Release: |release|

Features
---------

- *Unified quantum frontend interface*. **Transpile** quantum circuits between supported packages. Leverage the capabilities of multiple frontends through **simple, consistent protocols**.

..

- *Build once, target many*. **Create** quantum programs using your preferred circuit-building package, and **execute** on any backend that interfaces with a supported frontend.

..

- *Benchmark, compare, interpret results*. Built-in **compatible** post-processing enables comparing results between runs and **across backends**.


Installation
-------------

The qBraid SDK is available exclusively through `qBraid Lab <https://lab.qbraid.com>`_.
Login (or create an account) and then follow the steps in `Installing an environment <../lab/environments.html#installing-an-environment>`_ to
get started using the SDK.


Usage
------

Construct a quantum program of any supported program type:

.. code-block:: python
   
   >>> from qbraid import SUPPORTED_PROGRAM_TYPES
   >>> from qbraid.interface import random_circuit
   >>> SUPPORTED_PROGRAM_TYPES
   {'cirq': 'Circuit',
    'pyquil': 'Program',
    'qiskit': 'QuantumCircuit',
    'braket': 'Circuit',
    'pennylane': 'QuantumTape'}
   >>> circuit = random_circuit("qiskit", num_qubits=2, measure=True)

Search for quantum backend(s) on which to execute your program:

.. code-block:: python

   >>> from qbraid import get_devices
   >>> from qbraid.api import ibmq_least_busy_qpu
   >>> get_devices(filters={"name": {"$regex": "Density Matrix"}})
   Device status updated 0 minutes ago

   Device ID                           Status     
   ---------                           ------    
   aws_dm_sim                          ONLINE    
   google_cirq_dm_sim                  ONLINE
   
   >>> ibmq_least_busy_qpu()
   ibm_q_armonk

Apply the device wrapper and send your quantum jobs:

.. code-block:: python

   >>> from qbraid import device_wrapper
   >>> jobs  = []
   >>> qbraid_ids = ['aws_dm_sim', 'google_cirq_dm_sim', 'ibm_q_armonk']
   >>> for device in qbraid_ids:
   ... qdevice = device_wrapper(device)
   ... qjob = qdevice.run(circuit, shots=1024)
   ... jobs.append(qjob)

List your submitted jobs and view their status:

.. code-block:: python

   >>> from qbraid import get_jobs
   >>> get_jobs(filters={"numResults": 3})
   Displaying 3 most recent jobs matching query:

   Job ID                                              Submitted                  Status
   ------                                              ---------                  ------
   ibm_q_armonk-exampleuser-qjob-xxxxxxx...            2023-05-21T21:13:48.220Z   RUNNING
   google_cirq_dm_sim-exampleuser-qjob-yyyyyyy...      2023-05-21T21:13:47.220Z   COMPLETED
   aws_dm_sim-exampleuser-qjob-zzzzzzz...              2023-05-21T21:13:47.220Z   COMPLETED

Compare the results:

.. code-block:: python

   >>> print("{:<20} {:<20}".format('Device','Counts'))
   >>> for i, job in enumerate(jobs):
   ... result = job.result()
   ... counts = result.measurement_counts()
   ... print("{:<20} {:<20}".format(qbraid_ids[i],str(counts)))
   Device               Counts              
   aws_dm_sim           {'0': 477, '1': 547}
   google_cirq_dm_sim   {'0': 534, '1': 490}
   ibm_q_armonk         {'0': 550, '1': 474}


Supported Frontends
^^^^^^^^^^^^^^^^^^^^

+-------------+-------------+------------+-------------+-------------+
|  Cirq_      |  Braket_    |  Qiskit_   |  pyQuil_    |  Pennylane_ |
+=============+=============+============+=============+=============+
| |cirq|      | |braket|    | |qiskit|   | |pyquil|    | |pennylane| |
+-------------+-------------+------------+-------------+-------------+


.. |cirq| image:: ../_static/pkg-logos/cirq.png
   :align: middle
   :width: 90%
   :target: Cirq_

.. |braket| image:: ../_static/pkg-logos/braket.png
   :align: middle
   :width: 90%
   :target: Braket_

.. |qiskit| image:: ../_static/pkg-logos/qiskit.png
   :align: middle
   :width: 90%
   :target: Qiskit_

.. |pyquil| image:: ../_static/pkg-logos/pyquil.png
   :align: middle
   :width: 90%
   :target: pyQuil_

.. |pennylane| image:: ../_static/pkg-logos/xanadu.png
   :align: middle
   :width: 90%
   :target: Pennylane_

.. _Cirq: https://quantumai.google/cirq
.. _Braket: https://aws.amazon.com/braket
.. _Qiskit: https://qiskit.org
.. _pyQuil: https://www.rigetti.com/applications/pyquil
.. _Pennylane: https://pennylane.ai
.. _qBraid: https://qbraid.com/home.html
