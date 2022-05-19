.. _sdk_jobs:

Jobs
=====

In this module, you will learn how to use the qBraid SDK to manage
your quantum jobs.

The `device module <./devices.html>`_ illustrated how qBraid device wrappers can
be used execute circuits on quantum backends. Using the OQC Lucy QPU as our example
target backend, the procedure was as follows:

.. code-block:: python

    >>> from qbraid import device_wrapper
    >>> qbraid_id = 'aws_oqc_lucy'
    >>> qdevice = device_wrapper(qbraid_id)
    >>> qjob = qdevice.run(circuit)
    >>> type(qjob)
    qbraid.devices.aws.job.BraketQuantumTaskWrapper

Invoking the ``run`` method of a qBraid ``DeviceLikeWrapper`` returns a qBraid
``JobLikeWrapper``. Through a unified set of methods and attributes, this class
provides access to data about the quantum jobs executed across any qBraid supported
backend. You can also directly access the wrapped "job-like" object using the
``vendor_jlo`` attribute.

.. code-block:: python

    >>> type(qjob.vendor_jlo)
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

This job ID can be used to reinstantiate a qBraid ``JobLikeWrapper``
object at a later time or in a seperate program, with no loss of
information.

.. code-block:: python

    >>> from qbraid import job_wrapper
    >>> saved_job_id = 'aws_oqc_lucy-exampleuser-qjob-xxxxxxxxxxxxxxxxxxxx'
    >>> qjob = job_wrapper(saved_job_id)

Once the quantum job is complete, use the ``result`` method to gather the result:

.. code-block:: python

    >>> qjob.wait_for_final_state()
    >>> qjob.status()
    <JobStatus.COMPLETED: 6>
    >>> qresult = qjob.result()

The next module will go in depth on qBraid SDK quantum results.