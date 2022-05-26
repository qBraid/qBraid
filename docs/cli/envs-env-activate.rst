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
    Activate qbraid_sdk in your shell using:

    source /home/jovyan/.qbraid/environments/qbraid_sdk_9j9sjy/pyenv/bin/activate

    Once activated (pyenv), use `deactivate` to deactivate the enviornment.
    $ source /home/jovyan/.qbraid/environments/qbraid_sdk_9j9sjy/pyenv/bin/activate
    $ which python
    /home/jovyan/.qbraid/environments/qbraid_sdk_9j9sjy/pyenv/bin/python


.. seealso::

    - :ref:`qbraid envs list<cli_envs_list>`