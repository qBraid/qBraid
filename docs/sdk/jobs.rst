.. _sdk_jobs:

Jobs
=====

In this module, you will learn how to use the qBraid SDK to manage
your quantum jobs.

The `device module <./devices.html>`_ illustrated how qBraid
device wrappers can be used execute circuits on quantum backends.
Using the IBMQ Armonk QPU as an example, the procedure was as follows:

.. code-block:: python

    >>> from qbraid import device_wrapper
    >>> qbraid_id = 'ibm_q_armonk'
    >>> qdevice = device_wrapper(qbraid_id)
    >>> qjob = qdevice.run(circuit)
    >>> type(qjob)
    qbraid.devices.ibm.job.QiskitJobWrapper

Invoking the ``run`` method of a qBraid ``DeviceLikeWrapper`` returns a qBraid
``JobLikeWrapper``. Through a unified set of methods and attributes, this class
provides access to data about the quantum jobs executed across any qBraid supported
backend. You can also directly access the wrapped "job-like" object using the
``vendor_jlo`` attribute.

.. code-block:: python

    >>> type(qjob.vendor_jlo)
    qiskit.providers.ibmq.job.ibmqjob.IBMQJob

Each quantum job executed through the qBraid SDK is assigned its own
unique job ID.

.. code-block:: python

    >>> qjob.id
    ibm_q_armonk-exampleuser-qjob-xxxxxxxxxxxxxxxxxxxx

This job ID can be used to reinstantiate a qBraid ``JobLikeWrapper``
object at a later time or in a seperate program, with no loss of
information.

.. code-block:: python

    >>> from qbraid import retrieve_job
    >>> saved_job_id = 'ibm_q_armonk-exampleuser-qjob-xxxxxxxxxxxxxxxxxxxx'
    >>> qjob = retrieve_job(saved_job_id)

Once the quantum job is complete, you can gather the result:

.. code-block:: python

    >>> qjob.status()
    <JobStatus.COMPLETED: 6>
    >>> qresult = qjob.result()

The next module will go in depth on qBraid SDK quantum results.