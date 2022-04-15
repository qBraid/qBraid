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

- *Benchmark, compare, interpret results*. Built-in **compatable** post-processing enables comparing results between runs and **across backends**.


Installation
-------------

The qBraid-SDK is available exclusively through `qBraid Lab <https://lab.qbraid.com>`_.
Login (or create an account) and then follow the steps in `Installing an environment <../lab/environments.html#installing-an-environment>`_ to
get started using the SDK.


Usage
------

.. code-block:: python

    import qbraid



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
