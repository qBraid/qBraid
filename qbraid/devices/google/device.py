from ..device import DeviceLikeWrapper
from .job import CirqEngineJobWrapper
from .utils import CIRQ_PROVIDERS
from cirq import Circuit


class CirqSamplerWrapper(DeviceLikeWrapper):

    def __init__(self, name, provider, **fields):
        """Cirq ``Sampler`` wrapper class
        Args:
            name (str): a Cirq supported device
            provider (str): the provider that this device comes from
            fields: kwargs for the values to use to override the default options.
        Raises:
            AttributeError: if input field not a valid options
        """
        super().__init__(name, provider, **fields)
        self._vendor = "Google"
        self.vendor_dlo = self._get_device_obj(CIRQ_PROVIDERS)

    @classmethod
    def _default_options(cls):
        """Return the default options for running this device."""
        pass

    def run(self, run_input, **options):
        pass


class CirqEngineWrapper(DeviceLikeWrapper):

    def __init__(self, name, provider, **fields):
        """Cirq ``Engine`` wrapper class
        Args:
            name (str): a Cirq supported device
            provider (str): the provider that this device comes from
            fields: kwargs for the values to use to override the default options.
        Raises:
            AttributeError: if input field not a valid options
        """
        super().__init__(name, provider, **fields)
        self._vendor = "Google"
        self.vendor_dlo = self._get_device_obj(CIRQ_PROVIDERS)

    @classmethod
    def _default_options(cls):
        """Return the default options for running this device."""
        pass

    def run(self, program: Circuit, **kwargs):
        """Runs the supplied Circuit via Quantum Engine.
        Args:
            program: The Circuit to execute. If a circuit is
                provided, a moment by moment schedule will be used.
            program_id: A user-provided identifier for the program. This must
                be unique within the Google Cloud project being used. If this
                parameter is not provided, a random id of the format
                'prog-################YYMMDD' will be generated, where # is
                alphanumeric and YYMMDD is the current year, month, and day.
            job_id: Job identifier to use. If this is not provided, a random id
                of the format 'job-################YYMMDD' will be generated,
                where # is alphanumeric and YYMMDD is the current year, month,
                and day.
            param_resolver: Parameters to run with the program.
            repetitions: The number of repetitions to simulate.
            processor_ids: The engine processors that should be candidates
                to run the program. Only one of these will be scheduled for
                execution.
            gate_set: The gate set used to serialize the circuit. The gate set
                must be supported by the selected processor.
            program_description: An optional description to set on the program.
            program_labels: Optional set of labels to set on the program.
            job_description: An optional description to set on the job.
            job_labels: Optional set of labels to set on the job.
        Returns:
            A single Result for this run.
        """
        return self.vendor_dlo.run(program, **kwargs)

    def run_sweep(self, program: Circuit, **kwargs):
        """Runs the supplied Circuit via Quantum Engine.Creates
         In contrast to run, this runs across multiple parameter sweeps, and
         does not block until a result is returned.
         Args:
             program: The Circuit to execute. If a circuit is
                 provided, a moment by moment schedule will be used.
             program_id: A user-provided identifier for the program. This must
                 be unique within the Google Cloud project being used. If this
                 parameter is not provided, a random id of the format
                 'prog-################YYMMDD' will be generated, where # is
                 alphanumeric and YYMMDD is the current year, month, and day.
             job_id: Job identifier to use. If this is not provided, a random id
                 of the format 'job-################YYMMDD' will be generated,
                 where # is alphanumeric and YYMMDD is the current year, month,
                 and day.
             params: Parameters to run with the program.
             repetitions: The number of circuit repetitions to run.
             processor_ids: The engine processors that should be candidates
                 to run the program. Only one of these will be scheduled for
                 execution.
             gate_set: The gate set used to serialize the circuit. The gate set
                 must be supported by the selected processor.
             program_description: An optional description to set on the program.
             program_labels: Optional set of labels to set on the program.
             job_description: An optional description to set on the job.
             job_labels: Optional set of labels to set on the job.
         Returns:
             An EngineJob. If this is iterated over it returns a list of
             TrialResults, one for each parameter sweep.
         """
        cirq_engine = self.vendor_dlo
        cirq_engine_job = cirq_engine.run_sweep(program, **kwargs)
        qbraid_job = CirqEngineJobWrapper(cirq_engine_job)
        qbraid_job._set_device(self)
        return qbraid_job
