.. _sdk_results:

Results
========

Let's start by defining a simple qiskit quantum circuit that we wish to execute.

.. code-block:: python
    
    import numpy as np
    from qiskit import QuantumCircuit

    circuit = QuantumCircuit(1, 1)

    circuit.h(0)
    circuit.ry(np.pi / 4, 0)
    circuit.rz(np.pi / 2, 0)
    circuit.measure(0, 0)

This time, we'll run our quantum program on the IBMQ Armonk QPU. After
the job has completed, we'll gather the result, and plot a histogram of the
measurement counts.

.. code-block:: python

    from qbraid import device_wrapper

    shots = 2**10
    
    qdevice = device_wrapper('ibm_q_belem')
    qjob = ibmq_device.run(circuit, shots=shots)
    qjob.wait_for_final_state()
    
    qresult_ibmq = qjob.result()
    qresult.ibmq.plot_counts()

.. raw:: html
    
    <p>
        <img src="../_static/sdk-files/plot_counts.png" alt="plot_counts" style="width: 60%">
    </p>

The results layer follows the same wrapper abstraction as the circuit, device
and job layers. You can access the underlying "result-like" object using
the ``vendor_rlo`` attribute:

.. code-block:: python

    >>> type(qresult_ibmq)
    qbraid.providers.ibm.result.IBMResultWrapper
    >>> type(qresult_ibmq.vendor_rlo)
    qiskit.result.result.Result


Now, let's execute the same one-qubit qiskit circuit on a density-matrix simulator
provided AWS:

.. code-block:: python

    aws_device = device_wrapper('aws_dm_sim')

    aws_job = aws_device.run(circuit, shots=shots)

    qresult_aws = aws_job.result()

Using the qBraid quantum wrapper flow, result data will be returned with consistent
typing, formatting, and qubit indexing for every supported backend.

.. code-block:: python

    >>> qresult_ibmq.measurement_counts()
    {'0': 139, '1': 885}
    >>> qresult_aws.measurement_counts()
    {'0': 136, '1': 888}


The qBraid SDK not only allows executing your quantum programs on a range of quantum
backends, but also has built-in protocols that enable seemless comparisson of results.
As shown above, we can now easily compare the measurement counts across all three runs,
perfect for benchmarking and countless other applications.