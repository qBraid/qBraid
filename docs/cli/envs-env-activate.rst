.. _cli_envs_activate:

qbraid envs <environment> activate
===================================

Activate qBraid environment.

.. code-block:: bash

    qbraid envs <environment> activate


Examples
---------

.. code-block:: console

    $ which python
    /opt/conda/bin/python
    $ qbraid envs qbraid_sdk activate
    Activating qbraid_sdk environment... 

    Once active, use `deactivate` to deactivate the environment.
    $ which python
    /home/jovyan/.qbraid/environments/qbraid_sdk_9j9sjy/pyenv/bin/python


.. seealso::

    - :ref:`qbraid envs list<cli_envs_list>`