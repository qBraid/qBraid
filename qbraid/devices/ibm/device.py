"""QiskitBackendWrapper Class"""

from qiskit import IBMQ, Aer, assemble
from qiskit import transpile as qiskit_transpile
from qiskit.providers.backend import Backend as QiskitBackend
from qiskit.providers.ibmq import IBMQProviderError
from qiskit.providers.ibmq.managed import IBMQJobManager
from qiskit.utils.quantum_instance import QuantumInstance

from qbraid.api import config_user, job_api
from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.enums import DeviceStatus
from qbraid.devices.exceptions import DeviceError
from qbraid.devices.ibm.job import QiskitJobWrapper
from qbraid.devices.ibm.result import QiskitResultWrapper


class QiskitBackendWrapper(DeviceLikeWrapper):
    """Wrapper class for IBM Qiskit ``Backend`` objects."""

    def _get_device(self) -> QiskitBackend:
        """Initialize an IBM device."""
        if self._obj_ref == "IBMQ":
            if not IBMQ.active_account():
                token = config_user.get_config("token", "sdk", qbraidrc=True)
                base_url = config_user.get_config("url", "QBRAID")
                api_url = f"{base_url}/ibm-routes?route="
                IBMQ.enable_account(token, api_url)
            provider = IBMQ.get_provider(hub="ibm-q", group="open", project="main")
            return provider.get_backend(self._obj_arg)
        if self._obj_ref == "Aer":
            return Aer.get_backend(self._obj_arg)
        IBMQ.disable_account()
        raise DeviceError(f"obj_ref {self._obj_ref} not found.")

    def _vendor_compat_run_input(self, run_input):
        return qiskit_transpile(run_input, self.vendor_dlo)

    @property
    def status(self):
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        if self.id == "ibm_q_bogota":
            return DeviceStatus.OFFLINE
        backend_status = self.vendor_dlo.status()
        if not backend_status.operational:
            return DeviceStatus.OFFLINE
        return DeviceStatus.ONLINE

    def pending_jobs(self):
        """Return the number of jobs in the queue for the ibm backend"""
        return self.vendor_dlo.status().to_dict()["pending_jobs"]

    def execute(self, run_input, *args, **kwargs):
        """Runs circuit(s) on qiskit backend via :meth:`~qiskit.utils.QuantumInstance.execute`.

        Creates a :class:`~qiskit.utils.QuantumInstance`, invokes its ``execute`` method,
        applies a QiskitResultWrapper, and returns the result.

        Args:
            run_input: An individual or a list of circuit objects to run on the wrapped device.
            kwargs: Any kwarg options to pass to the device for the run.

        Returns:
            qbraid.devices.ibm.QiskitResultWrapper: The result like object for the run.

        """
        run_input, _ = self._compat_run_input(run_input)
        quantum_instance = QuantumInstance(self.vendor_dlo, *args, **kwargs)
        qiskit_result = quantum_instance.execute(run_input)
        qbraid_result = QiskitResultWrapper(qiskit_result)
        return qbraid_result

    def run(self, run_input, *args, **kwargs):
        """Runs circuit(s) on qiskit backend via :meth:`~qiskit.execute`

        Uses the :meth:`~qiskit.execute` method to create a :class:`~qiskit.providers.Job` object,
        applies a :class:`~qbraid.devices.ibm.QiskitJobWrapper`, and return the result.

        Args:
            run_input: A circuit object to run on the wrapped device.

        Keyword Args:
            shots (int): The number of times to run the task on the device. Default is 1024.


        Returns:
            qbraid.devices.ibm.QiskitJobWrapper: The job like object for the run.

        """
        run_input, qbraid_circuit = self._compat_run_input(run_input)
        if "shots" in kwargs:
            shots = kwargs.get("shots")
        else:
            shots = self.vendor_dlo.options.get("shots")
        if self._obj_ref == "Aer":
            qobj = assemble(run_input, memory=True, **kwargs)
            qiskit_job = self.vendor_dlo.run(qobj)
            qiskit_job_id = qiskit_job.job_id()
        else:
            memory = True if "memory" not in kwargs else kwargs.pop("memory")
            job_manager = IBMQJobManager()  # assemble included in run method
            job_set = job_manager.run([run_input], backend=self.vendor_dlo, memory=memory, **kwargs)
            qiskit_job = job_set.jobs()[0]
            qiskit_job_id = job_set.job_set_id()
        qbraid_job_id = job_api.init_job(qiskit_job_id, self, qbraid_circuit, shots)
        qbraid_job = QiskitJobWrapper(
            qbraid_job_id, vendor_job_id=qiskit_job_id, device=self, vendor_jlo=qiskit_job
        )
        return qbraid_job

    def estimate_cost(self, circuit, shots=1024):
        """Estimate the cost of running a circuit on the device."""
        # print("qBraid currently offers only free devices.")
        # print("Please contact rickyyoung@qbraid.com for more information.")
        raise NotImplementedError
