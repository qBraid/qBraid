from qiskit import IBMQ, BasicAer, Aer
from qiskit.ignis.mitigation.measurement import CompleteMeasFitter
from qiskit.providers.aer.noise import NoiseModel
from qiskit.aqua import QuantumInstance
import numpy as np


def run_config_qiskit_run(
    quantum_calc_output,
    run_on_hardware=False,
    hardware_cofig=None,
    simulation_config=None,
):
    if run_on_hardware:
        pass
    else:
        if simulation_config is None:
            print("Please pass valid simulation configuration")
        else:
            if simulation_config["Noisy"]:
                if simulation_config["simulator"] == "qasm_simulator":
                    quantum_instance = get_ibm_device_quantum_instance(
                        simulation_config["device_name"]
                    )
                    if quantum_calc_output.algo_name == "vqe":
                        vqe = quantum_calc_output.vqe_qiskit_obj
                        ret = vqe.run(quantum_instance)
                        vqe_result = np.real(ret["eigenvalue"])

                        print("VQE Result:", vqe_result)
                else:
                    raise TypeError(
                        "Noisy simulation is only supported in qasm simulator"
                    )
            else:
                simulator = simulation_config["simulator"]
                backend = BasicAer.get_backend(simulator)
                if simulator == "qasm_simulator":
                    quantum_instance = QuantumInstance(backend=backend, shots=1000)
                else:
                    quantum_instance = backend

                if quantum_calc_output.algo_name == "vqe":
                    vqe = quantum_calc_output.vqe_qiskit_obj
                    ret = vqe.run(quantum_instance)
                    vqe_result = np.real(ret["eigenvalue"])
                    print("VQE Result:", vqe_result)


def get_ibm_device_quantum_instance(device_name):
    if device_name == "vigo":
        from qiskit.test.mock import FakeVigo

        backend = FakeVigo()
        device = FakeVigo()
    elif device_name == "melbourne":
        from qiskit.test.mock import FakeMelbourne

        backend = FakeMelbourne()
        device = FakeMelbourne()
    elif device_name == "montreal":
        from qiskit.test.mock import FakeMontreal

        backend = FakeMontreal()
        device = FakeMontreal()
    elif device_name == "fakeqasm":
        from qiskit.test.mock import FakeQasmSimulator

        backend = FakeQasmSimulator()
        device = FakeQasmSimulator()
    coupling_map = device.configuration().coupling_map
    # noise_model = NoiseModel.from_backend(device.properties())

    noise_model = NoiseModel.from_backend(backend)
    backend = Aer.get_backend("qasm_simulator")

    quantum_instance = QuantumInstance(
        backend=backend,
        shots=1000,
        noise_model=noise_model,
        coupling_map=coupling_map,
        measurement_error_mitigation_cls=CompleteMeasFitter,
        cals_matrix_refresh_period=30,
    )
    return quantum_instance
