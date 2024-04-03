.. _sdk_jobs:

Jobs
=====

In this module, you will learn how to use the qBraid SDK to manage
your quantum jobs.

Submit Jobs
------------

The `device module <./devices.html>`_ illustrated how qBraid device wrappers can
be used execute circuits on quantum backends. Using the OQC Lucy QPU as our example
target backend, the procedure was as follows:

.. code-block:: python

    >>> from qbraid.providers import QbraidProvider
    >>> qbraid_id = 'aws_oqc_lucy'
    >>> provider = QbraidProvider()
    >>> qdevice = provider.get_device(qbraid_id)
    >>> qjob = qdevice.run(circuit)
    >>> type(qjob)
    qbraid.providers.aws.job.BraketQuantumTaskWrapper

Invoking the ``run`` method of a qBraid ``QuantumDevice`` returns a qBraid
``QuantumJob``. Through a unified set of methods and attributes, this class
provides access to data about the quantum jobs executed across any qBraid supported
backend. You can also directly access the wrapped "job-like" object using the
``_job`` attribute.

.. code-block:: python

    >>> type(qjob._job)
    braket.aws.aws_quantum_task.AwsQuantumTask

Check the status of your quantum job using the ``status`` method:

.. code-block:: python

    >>> qjob.status()
    <JobStatus.QUEUED: 1>
    
Each quantum job executed through the qBraid SDK is assigned its own
unique job ID.

.. code-block:: python

    >>> qjob.id
    aws_oqc_lucy-exampleuser-qjob-xxxxxxxxxxxxxxxxxxxx


Batch Jobs
------------

For AWS devices, ``run_batch`` will create a list of quantum job objects:

.. code-block:: python

    >>> aws_device = provider.get_device('aws_ionq_harmony')
    >>> batch_jobs = aws_device.run_batch([circuit1, circuit2, circuit3], shots=1000)
    >>> batch_results = [job.result() for job in batch_jobs]


For IBM devices, ``run_batch`` will create a single object that contains all batch jobs:

.. code-block:: python

    >>> ibm_device = provider.get_device('ibm_q_kyoto')
    >>> batch_job = ibm_device.run_batch([circuit1, circuit2, circuit3], shots=1000)
    >>> batch_result = batch_job.result()


Retrieve Jobs
--------------

You can use the ``get_jobs`` function to a return a list of your previously
submitted quantum jobs, along with the status of each. A number of filtering options
are available to help narrow your search. Query syntax is equivalent to that
of the ``get_devices`` `unified device search <./devices.html#unified-device-search>`_.
By default, ``get_jobs`` returns the 10 most recently submitted jobs matching your search.


.. code-block:: python

    >>> from qbraid import get_jobs
    >>> get_jobs(filters={"qbraidDeviceId": "aws_oqc_lucy"})
    Displaying 10 most recent jobs matching query:

    Job ID                                                  Submitted                 Status
    ------                                                  ---------                 ------
    aws_oqc_lucy-exampleuser-qjob-xxxxxxxxxxxxxxxxxxxx      2023-05-21T21:13:48.220Z  RUNNING
    aws_oqc_lucy-exampleuser-qjob-yyyyyyyyyyyyyyyyyyyy      2023-04-15T11:09:56.783Z  COMPLETED
    ...


This job ID can be used to reinstantiate a qBraid ``QuantumJob`` object at any
time, and even in a seperate program, with no loss of information.

.. code-block:: python

    >>> from qbraid.providers import QuantumJob
    >>> saved_job_id = 'aws_oqc_lucy-exampleuser-qjob-xxxxxxxxxxxxxxxxxxxx'
    >>> qjob = QuantumJob.retrieve(saved_job_id)


You can also load a previously submitted jobs directly through the corresponding provider class:

.. code-block:: python

    >>> from qbraid.providers.aws import BraketQuantumTask
    >>> qjob = BraketQuantumTask(saved_job_id)


Jobs submitted through the SDK are organized in the qBraid Lab Quantum Jobs Sidebar:

.. image:: ../_static/sdk-files/lab_jobs.png
    :width: 90%
    :alt: Quantum Jobs sidebar
    :target: javascript:void(0);


Tagged Jobs
------------

Use the ``tags`` kwarg in ``run`` and ``run_batch`` methods to organize your jobs so they can easily be found later.
AWS devices support tags passed as key/value pairs, while IBM devices support tags as individual values in a list.

.. code-block:: python

    >>> aws_job = aws_device.run(circuit, tags={'my_tag': '*'})
    >>> ibm_job = ibm_device.run(circuit, tags=['my_tag'])

Due to this difference in convention, tagged IBM jobs are searchable using the ``*`` wildcard character as a tag value:

.. code-block:: python

    >>> qbraid.get_jobs(filters={"tags": "my_tag", "*"})
    Displaying 2/2 most recent jobs matching query:

    Job ID                                                   Submitted              Status
    ------                                                   ---------              ------
    aws_ionq_harmony-exampleuser-qjob-xxxxxxxxxxxxxxxxxxxx   2024-01-04T19:20:49Z   QUEUED
    ibm_q_kyoto-exampleuser-qjob-yyyyyyyyyyyyyyyyyyyy        2024-01-04T19:22:10Z   QUEUED


Cost Tracker
-------------

Retrieve the cost of a quantum task submitted to an AWS device:

.. code-block:: python

    >>> aws_job.get_cost() # returns cost in USD
    0.00375


Job Results
------------

Once a quantum job is complete, use the ``result`` method to gather the result:

.. code-block:: python

    >>> qjob.wait_for_final_state()
    >>> qjob.status()
    <JobStatus.COMPLETED: 6>
    >>> qresult = qjob.result()

The next module will go in depth on qBraid SDK quantum results.