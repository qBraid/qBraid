qBraid-SDK Documentation
=========================

:Release: |release|

A Python toolkit for building and executing quantum programs.

Features
--------

.. image:: _static/logo.png
   :align: left
   :width: 280px
   :target: qBraid_

- *Unified quantum frontend interface*
   Transpile quantum circuits between supported packages. Leverage capabilities
   of multiple frontends through simple, consistent protocols.

- *Build once, execute anywhere*
   Create quantum programs using your preferred circuit-building package and
   execute it on any backend that interfaces with a supported frontend.

- *Benchmark, compare, interpret results*
   Compatable post-processing simplifies comparing results between runs and across backends.


Supported Frontends
--------------------

+-------------+-------------+------------+-------------+-------------+
|  Cirq_      |  Braket_    |  Qiskit_   |  PyQuil_    |  Pennylane_ |
+=============+=============+============+=============+=============+
| |cirq|      | |braket|    | |qiskit|   | |pyquil|    | |pennylane| |
+-------------+-------------+------------+-------------+-------------+


.. |cirq| image:: _static/frontends/cirq.png
   :align: middle
   :width: 90%
   :target: Cirq_

.. |braket| image:: _static/frontends/braket.png
   :align: middle
   :width: 90%
   :target: Braket_

.. |qiskit| image:: _static/frontends/qiskit.png
   :align: middle
   :width: 90%
   :target: Qiskit_

.. |pyquil| image:: _static/frontends/pyquil.png
   :align: middle
   :width: 90%
   :target: PyQuil_

.. |pennylane| image:: _static/frontends/xanadu.png
   :align: middle
   :width: 90%
   :target: Pennylane_


.. _Cirq: https://quantumai.google/cirq
.. _Braket: https://aws.amazon.com/braket
.. _Qiskit: https://qiskit.org
.. _PyQuil: https://www.rigetti.com/applications/pyquil
.. _Pennylane: https://pennylane.ai
.. _qBraid: https://qbraid.com/home.html


.. toctree::
   :maxdepth: 1
   :caption: Getting Started
   :hidden:

   getstart/setup

.. toctree::
   :maxdepth: 1
   :caption: API Reference
   :hidden:

   api/qbraid
   api/qbraid.api
   api/qbraid.interface
   api/qbraid.transpiler
   api/qbraid.devices
   api/qbraid.testing


Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
