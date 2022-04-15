.. _sdk_devices:

Devices
=========

In this module, you will learn how to use the qBraid SDK to interface with
quantum backends. We will demonstrate how to construct queries and search
for available devices using the ``qbraid.get_devices`` function, and
an overview how to execute circuits using the ``qbraid.devices`` module.

Unified Device Search
----------------------

The ``get_devices`` function provides a unified quantum device search. It returns a complete list
of all quantum backends available the Qiskit, Cirq, and Amazon Braket, along with the "status" of
each device, i.e. ``ONLINE`` or ``OFFLINE``.

.. code-block:: python

    from qbraid import get_devices

    get_devices()

There a number of query options available to help filter your search. For example, to find
simulators containing keyword "State" available through AWS or IBM:

.. code-block:: python

    get_devices(
        filters={
            "type": "Simulator",
            "name": {"$regex": "State"},
            "vendor": {"$in": ["AWS", "IBM"]},
        }
    )

To search for all gate-based QPUs with at least 5 qubits that are online:

.. code-block:: python

    get_devices(
        filters={
            "paradigm": "gate-based",
            "type": "QPU",
            "numberQubits": {"$gte": 5},
            "status": "ONLINE",
        }
    )

Or to find all backends available through qiskit that don't require a credential:

.. code-block:: python

    get_devices(
        filters={
            "runPackage": "qiskit",
            "requiresCred": "false",
        }
    )

If run in Jupyter, the call above will return a display table similar to the following:

.. raw:: html
    
    <p>
        <img src="../_static/sdk-files/get_devices.png" alt="get_devices" style="width: 80%">
    </p>

In the lower-right of the table is the time ellapsed since the last device status update.
Device status labels can be manually refreshed by setting ``refresh=True``:

.. code-block:: python

    get_devices(refresh=True)


If run in the Python Shell, device data is returned in dictionary format:

.. code-block:: python

    >>> from qbraid import get_devices
    >>> get_devices(filters={"provider": "OQC"})
    {'OQC': {'aws_oqc_lucy': {'name': 'Lucy', 'status': 'ONLINE'}}}


Each supported device is associated with its own qBraid ID. The next section will cover
how this value is used to wrap the quantum backends / device objects of various types.

.. seealso::

    For more on advanced ``filters`` options and syntax, see `Query Selectors`_.
    

.. _Query Selectors: https://docs.mongodb.com/manual/reference/operator/query/#query-selectors


Device Wrapper
----------------

Given a ``qbraid_id`` retrieved from ``get_devices``, a ``qbraid.devices.DeviceLikeWrapper``
object can be created as follows:

.. code-block:: python

    from qbraid import device_wrapper

    qbraid_id = 'aws_oqc_lucy'  # as an example

    qdevice = device_wrapper(qbraid_id)


From here, a number of methods are available: Gather information about the device,
execute quantum programs (to be covered in the next section), or even access the
wrapped device object directly.

.. code-block:: python

    >>> qdevice.info
    {'numberQubits': 8,
    'visibility': 'public',
    'connectivityGraph': [],
    'qbraid_id': 'aws_oqc_lucy',
    'name': 'Lucy',
    'provider': 'OQC',
    'paradigm': 'gate-based',
    'type': 'QPU',
    'typeQubits': 'superconducting',
    'location': 'London, England',
    'vendor': 'AWS',
    'runPackage': 'braket',
    'status': 'ONLINE',
    ...,
    ...}
    >>> type(qdevice.vendor_dlo)
    braket.aws.aws_device.AwsDevice


Executing Circuits
-------------------

Each ``DeviceLikeWrapper`` is equipped with a ``run`` method, which extends the
wrapped object's native ``execute``, ``sample``, ``run``, or equivalent circuit
execution method. This abstraction allows the user to pass a quantum circuit built
using any qbraid-supported frontend to the ``run`` method of the wrapped device.

.. code-block:: python
    
    from qiskit import QuantumCircuit
    
    def circuit0():
        circuit = QuantumCircuit(2)
        circuit.h(0)
        circuit.cx(0,1)
        return circuit

.. code-block:: python

    import pennylane as qml

    def circuit1():
        with qml.tape.QuantumTape() as tape:
            qml.Hadamard(wires=0)
            qml.CNOT(wires=[0, 1])
        return tape


.. code-block:: python

    >>> qiskit_circuit = circuit0()
    >>> pennylane_circuit = circuit1()
    >>> qjob0 = qdevice.run(qiskit_circuit)
    >>> qjob1 = qdevice.run(pennylane_circuit)


Above, I defined two quantum programs, one using qiskit and the other using pennylane,
and executed each on Oxford Quantum Circuit's Lucy QPU, made available through Amazon Braket.


Example Flow: Least Busy QPU
------------------------------

In this section, we'll piece together a workflow example, starting by using the
``ibmq_least_busy_qpu`` function to get the ``qbraid_id`` of the IBMQ QPU with the
least number of queued quantum jobs.

.. code-block:: python

    >>> from qbraid.api import ibmq_least_busy_qpu
    >>> qbraid_id = ibmq_least_busy_qpu()
    >>> qdevice = device_wrapper(qbraid_id)
    >>> qdevice.name
    'IBMQ Belem'
    >>> qdevice.status
    <DeviceStatus.ONLINE: 0>

After applying the device wrapper and verifying the device is online, we're ready
to submit a job. This time, we'll use a Cirq circuit as the ``run`` method input.

.. code-block:: python

    >>> from qbraid.interface import random_circuit
    >>> cirq_circuit = random_circuit("cirq", num_qubits=qdevice.num_qubits)
    >>> qdevice.pending_jobs()
    4
    >>> qjob = qdevice.run(cirq_circuit)
    >>> qjob.status()
    <JobStatus.QUEUED: 1>
    >>> qdevice.pending_jobs()
    5

For fun, we the set number of qubits used in the random circuit equal to the number of
qubits supported by the backend. We then checked the backend's number of pending jobs,
and saw the number increase by one after submitting our job.

Summary
--------

The device layer of the qBraid SDK enables users to execute quantum circuits of
any ``qbraid.SUPPORTED_PROGRAM_TYPES`` on any simulator or QPU returned by
``qbraid.get_devices``. Filter your search to the specifications of your task,
identify a device, and execute your program through a consistent three-step protocol:

1. Get qbraid device ID
2. Apply device wrapper
3. Execute program via ``run`` method
