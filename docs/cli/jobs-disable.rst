.. _cli_jobs_disable:

qbraid jobs disable
====================

Disable qBraid Quantum Jobs.

.. code-block:: bash

    qbraid jobs disable --name


Required Parameters
--------------------

``--name -n`` : Name of qBraid virtual environment.


Examples
---------

.. code-block:: console

    $ qbraid jobs disable -n qbraid_sdk
    Disable successful. You are now submitting quantum jobs with your own AWS credentials.

    To re-enable, run: `qbraid jobs enable -n qbraid_sdk`


qBraid environments with support for quantum jobs include ``aws_braket`` and ``qbraid_sdk``.


.. seealso::

    - :ref:`qbraid jobs enable<cli_jobs_enable>`