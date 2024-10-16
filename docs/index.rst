.. raw:: html
   
   <h1 style="text-align: center">
      <img src="./_static/logo.png" alt="qbraid logo" style="width:60px;height:60px;">
      <span> qBraid</span>
      <span style="color:#808080"> | SDK</span>
   </h1>
   <p style="text-align:center;font-style:italic;color:#808080">
      A platform-agnostic quantum runtime framework
   </p>

:Release: |release|

Overview
---------

The qBraid-SDK is a platform-agnostic quantum runtime framework designed for both quantum software and hardware providers.

This Python-based tool streamlines the full lifecycle management of quantum jobs—from defining program specifications to job
submission and through to the post-processing and visualization of results.
   
Installation
-------------

For the best experience, install the qBraid SDK on `lab.qbraid.com <https://lab.qbraid.com>`_.
Login (or create an account) on `account.qbraid.com <https://account.qbraid.com>`_ and then
follow the steps to `install an environment <https://docs.qbraid.com/lab/user-guide/environments#install-environment>`_.

The qBraid-SDK, and all of its dependencies, can also be installed using `pip <https://pypi.org/project/qbraid/>`_:

.. code-block:: bash

   pip install qbraid


Resources
----------

- `User Guide <https://docs.qbraid.com/sdk/user-guide>`_
- `Example Notebooks <https://github.com/qBraid/qbraid-lab-demo>`_
- `API Reference <https://sdk.qbraid.com/en/latest/api/qbraid.html>`_
- `Source Code <https://github.com/qBraid/qBraid>`_


.. toctree::
   :maxdepth: 1
   :caption: SDK API Reference
   :hidden:

   api/qbraid
   api/qbraid.programs
   api/qbraid.interface
   api/qbraid.transpiler
   api/qbraid.passes
   api/qbraid.runtime
   api/qbraid.visualization

.. toctree::
   :caption: QIR API Reference
   :hidden:

   qbraid_qir <https://sdk.qbraid.com/projects/qir/en/stable/api/qbraid_qir.html>
   qbraid_qir.cirq <https://sdk.qbraid.com/projects/qir/en/stable/api/qbraid_qir.cirq.html>
   qbraid_qir.qasm3 <https://sdk.qbraid.com/projects/qir/en/stable/api/qbraid_qir.qasm3.html>

.. toctree::
   :caption: CORE API Reference
   :hidden:

   qbraid_core <https://sdk.qbraid.com/projects/core/en/stable/api/qbraid_core.html>
   qbraid_core.services <https://sdk.qbraid.com/projects/core/en/stable/api/qbraid_core.services.html>

.. toctree::
   :caption: PYQASM API Reference
   :hidden:

   pyqasm <https://sdk.qbraid.com/projects/pyqasm/en/stable/api/pyqasm.html>