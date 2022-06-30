.. _cli_jobs_enable:

qbraid jobs enable
====================

Enable qBraid Quantum Jobs.

.. code-block:: bash

    qbraid jobs enable --name


Required Parameters
--------------------

``--name -n`` : Name of qBraid virtual environment.


Examples
---------

.. code-block:: console

    $ qbraid jobs enable -n qbraid_sdk
    Successfully enabled qBraid Quantum Jobs in the qbraid_sdk environment.
    Every AWS job you run will now be submitted through the qBraid API, so no access keys/tokens are necessary. 

    To disable, run: `qbraid jobs disable -n qbraid_sdk`


qBraid environments with support for quantum jobs include ``amazon_braket`` and ``qbraid_sdk``.

.. seealso::

    - :ref:`qbraid envs list<cli_envs_list>`
    - :ref:`qbraid jobs disable<cli_jobs_disable>`