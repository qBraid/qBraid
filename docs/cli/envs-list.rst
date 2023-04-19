.. _cli_envs_list:

qbraid envs list
=================

Get list of installed qBraid environments.

.. code-block:: bash

    qbraid envs list


Examples
---------

.. code-block:: console

    $ qbraid envs list
    # installed environments:
    #
    qsharp                         /opt/.qbraid/environments/qsharp_b54crn
    default                  jobs  /opt/.qbraid/environments/qbraid_000000
    amazon_braket            jobs  /home/jovyan/.qbraid/environments/aws_braket_kwx6dl
    qiskit                   jobs  /home/jovyan/.qbraid/environments/qiskit_9y9siy
    qbraid_sdk               jobs  /home/jovyan/.qbraid/environments/qbraid_sdk_9j9sjy


Environments with the ``jobs`` keyword listed before the path support qBraid Quantum Jobs.
The color of the ``jobs`` keyword (green or red) indicates whether qBraid Quantum Jobs are
currently :ref:`enabled<cli_jobs_enable>` or :ref:`disabled<cli_jobs_disable>` for that environment.
Quantum jobs can be added to an environment using the command ``qbraid jobs add``.


.. seealso::

    - :ref:`qbraid jobs<cli_jobs>`

