# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Benchmarking transpiler QAPS metric (Quantum Area Per Second)

"""
from time import time

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import zscore

from qbraid import circuit_wrapper
from qbraid.interface import random_circuit

# Step 1: Collecting the data
quantum_area_data = {}
values = list(range(25, 201, 25))
depth = 5

for num_qubits in values:
    quantum_area = num_qubits * depth

    if quantum_area not in quantum_area_data:
        quantum_area_data[quantum_area] = []

    cirq_circuit = random_circuit("cirq", num_qubits=num_qubits, depth=depth)
    qbraid_circuit = circuit_wrapper(cirq_circuit)

    start = time()
    qbraid_circuit.transpile("qiskit")
    stop = time()

    quantum_area_data[quantum_area].append(stop - start)

# Step 2: Calculating average execution times and performing linear regression
quantum_areas = []
avg_execution_times = []

for quantum_area, execution_times in quantum_area_data.items():
    avg_execution_time = np.mean(execution_times)
    quantum_areas.append(quantum_area)
    avg_execution_times.append(avg_execution_time)

x = np.array(quantum_areas)
y = np.array(avg_execution_times)
coefficients = np.polyfit(x, y, 1)

polynomial = np.poly1d(coefficients)
ys = polynomial(x)
z_scores = zscore(y - ys)

filtered_indices = np.where(np.abs(z_scores) < 2)
filtered_x = x[filtered_indices]
filtered_y = y[filtered_indices]

print(f"Linear Regression Equation: y = {coefficients[0]:.5f}x + {coefficients[1]:.5f}")
print(f"Quantum Area Per Second (QAPS): {1/coefficients[0]:.5f}")

plt.figure()
plt.scatter(filtered_x, filtered_y, label="Data Points")
plt.plot(x, ys, color="red", label="Linear Regression")
plt.xlabel("Quantum Area (num_qubits * depth)")
plt.ylabel("Average Execution Time (s)")
plt.title("Average Execution Time vs Quantum Area")
plt.grid(True)
plt.legend()
plt.show()
