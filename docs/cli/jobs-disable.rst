.. _cli_jobs_disable:

qbraid jobs disable
====================

Disable qBraid Quantum Jobs.

.. code-block:: bash

    qbraid jobs disable [env_name]


Positional Arguments
---------------------

``env_name`` : Name of environment. Values from: ``qbraid envs list``.


Examples
---------

.. code-block:: console

    $ qbraid jobs disable qbraid_sdk
    Disable successful. You are now submitting quantum jobs with your own AWS + IBM credentials.

    To re-enable, run: `qbraid jobs enable qbraid_sdk`


qBraid environments with support for quantum jobs include ``amazon_braket``, ``qiskit``, and ``qbraid_sdk``.


.. seealso::

    - :ref:`qbraid jobs enable<cli_jobs_enable>`
    - :ref:`qbraid envs list<cli_envs_list>`