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

This time, we'll run our quantum program on the IBMQ Nairobi QPU. After the
job has completed, we'll gather the result, print the measurement counts,
and plot a histogram of the probabilities.

.. code-block:: python

    from qbraid import device_wrapper
    from qbraid.visualization import plot_histogram

    shots = 2**10
    
    qdevice = device_wrapper('ibm_q_nairobi')
    qjob = ibmq_device.run(circuit, shots=shots)
    qjob.wait_for_final_state()
    
    qresult_ibmq = qjob.result()
    qresult_ibmq.measurement_counts()
    # {'0': 136, '1': 864}

    plot_histogram(qresult_ibmq.measurement_counts())

.. raw:: html
    
    <p>
        <img src="../_static/sdk-files/plot_counts.png" alt="plot_counts" style="width: 40%">
    </p>

The results layer follows the same wrapper abstraction as the circuit, device
and job layers. You can access the underlying "result-like" object using
the ``_result`` attribute:

.. code-block:: python

    >>> type(qresult_ibmq)
    qbraid.providers.ibm.result.QiskitResult
    >>> type(qresult_ibmq._result)
    qiskit.result.result.Result


Now, let's run a batch job using two copies of the one-qubit qiskit circuit
on a density-matrix simulator provided AWS:

.. code-block:: python

    aws_device = device_wrapper('aws_dm_sim')

    batch_jobs = aws_device.run_batch([circuit, circuit], shots=shots)

    batch_results = [job.result() for job in batch_jobs]

    batch_counts = [result.measurement_counts() for result in batch_results]

Using the qBraid quantum wrapper flow, result data will be returned with consistent
typing, formatting, and qubit indexing for every supported backend.

.. code-block:: python

    >>> batch_counts[0]
    {'0': 136, '1': 864}
    >>> batch_counts[1]
    {'0': 166, '1': 834}
    >>> plot_histogram(batch_counts)

.. raw:: html
    
    <p>
        <img src="../_static/sdk-files/batch_counts.png" alt="plot_counts" style="width: 40%">
    </p>

The qBraid SDK not only allows executing your quantum programs on a range of quantum
backends, but also has built-in protocols that enable seemless comparisson of results.
As shown above, we can now easily compare the measurement counts across both runs,
perfect for benchmarking and countless other applications.