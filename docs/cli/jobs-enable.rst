.. _cli_jobs_enable:

qbraid jobs enable
====================

Enable qBraid Quantum Jobs.

.. code-block:: bash

    qbraid jobs enable [env_name]


Positional Arguments
---------------------

``env_name`` : Name of environment. Values from: ``qbraid envs list``.


Examples
---------

.. code-block:: console

    $ qbraid jobs enable qbraid_sdk
    Successfully enabled qBraid Quantum Jobs in the qbraid_sdk environment.
    Every AWS + IBM job you run will now be submitted through the qBraid API, so no access keys/tokens are necessary. 

    To disable, run: `qbraid jobs disable qbraid_sdk`


.. seealso::

    - :ref:`qbraid jobs disable<cli_jobs_disable>`
    - :ref:`qbraid jobs add<cli_jobs_add>`
    - :ref:`qbraid envs list<cli_envs_list>`