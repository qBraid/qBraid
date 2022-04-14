.. _cmds_activate:

qbraid activate
================

Activate a virtual environment.

.. code-block:: bash
    
    qbraid activate <environment>


Positional arguments
---------------------

``<environment>`` : Name of qBraid virtual environment.


Examples
---------

.. code-block:: console

    $ which python
    /opt/conda/bin/python
    $ qbraid activate aws_braket
    $ which python
    /home/jovyan/.qbraid/environments/aws_braket_kwx6dl/pyenv/bin/python
    $ deactivate
    $ which python
    /opt/conda/bin/python



.. seealso::

    - :ref:`qbraid envs<cmds_envs>`