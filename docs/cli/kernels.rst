.. _cli_kernels:

qbraid kernels
===============

Manage qBraid kernel specifications.

.. code-block:: bash

    qbraid kernels <command> [options]


In this context, ``qbraid kernels`` is simply an alias for ``jupyter kernelspec``.
Run ``jupyter kernelspec --help-all`` to get a full list of available commands.


Examples
---------

.. code-block:: console
    
    $ qbraid kernels list
    Available kernels:
        iqsharp                      /home/jovyan/.local/share/jupyter/kernels/iqsharp
        python3_aws_braket_kwx6dl    /home/jovyan/.local/share/jupyter/kernels/python3_aws_braket_kwx6dl
        python3_qbraid_sdk_9j9sjy    /home/jovyan/.local/share/jupyter/kernels/python3_qbraid_sdk_9j9sjy
        python3                      /opt/conda/share/jupyter/kernels/python3

.. seealso::

    - `jupyter_client docs <https://jupyter-client.readthedocs.io/en/stable/api/kernelspec.html>`_