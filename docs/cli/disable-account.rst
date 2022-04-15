.. _cmds_disable_account:

qbraid disable account
=======================

Disable quantum jobs through qBraid.

.. code-block:: bash

    qbraid disable account <environment>


Positional arguments
---------------------

``<environment>`` : Name of qBraid virtual environment.


Examples
---------

.. code-block:: console

    $ qbraid disable account qbraid_sdk
    You are now disabling quantum jobs with qBraid Quantum Jobs.
    Disable successful. You are now submitting jobs with your own AWS credentials.
    To re-enable run the command:  qbraid enable account qbraid_sdk
    $ qbraid disable account qbraid_sdk
    You have already disabled qBraid quantum jobs.


.. seealso::

    - :ref:`qbraid envs<cmds_envs>`
    - :ref:`qbraid enable account<cmds_enable_account>`