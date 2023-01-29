.. _cli_envs_activate:

qbraid envs activate
======================

Activate qBraid environment.

.. code-block:: bash

    qbraid envs activate [env_name]


Positional Arguments
---------------------

``env_name`` : Name of environment. Values from: ``qbraid envs list``.


Examples
---------

.. code-block:: console

    $ which python
    /opt/conda/bin/python
    $ qbraid envs activate qbraid_sdk
    Activating qbraid_sdk environment...

    Once active, use `deactivate` to deactivate the environment.
    $ which python
    /home/jovyan/.qbraid/environments/qbraid_sdk_9j9sjy/pyenv/bin/python


.. seealso::

    - :ref:`qbraid envs list<cli_envs_list>`