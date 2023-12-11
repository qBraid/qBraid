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
Module for finding shortest converion paths between circuits.

"""
# import matplotlib.pyplot as plt
# import networkx as nx

# # List of conversion functions
# conversion_functions = [
#     "cirq_to_qasm22",
#     "cirq_to_braket",
#     "cirq_to_pyquil",
#     "braket_to_cirq",
#     "braket_to_qasm3",
#     "qiskit_to_qasm2",
#     "qiskit_to_qasm3",
#     "pyquil_to_cirq",
#     "pytket_to_qasm2",
#     "qasm2_to_qasm3",
#     "qasm2_to_cirq",
#     "qasm2_to_qiskit",
#     "qasm2_to_pytket",
#     "qasm3_to_braket",
#     "qasm3_to_qiskit",
# ]


# def find_shortest_conversion_path(source, target):
#     try:
#         path = nx.shortest_path(G, source, target)
#         conversion_steps = []
#         for i in range(len(path) - 1):
#             conversion_steps.append(f"{path[i]}_to_{path[i+1]}")
#         return conversion_steps
#     except nx.NetworkXNoPath:
#         return "No conversion path available"


# def add_new_conversion(conversion_func):
#     source, target = conversion_func.split("_to_")
#     G.add_edge(source, target)


# # Create a directed graph
# G = nx.DiGraph()

# # Add edges to the graph
# for func in conversion_functions:
#     source, target = func.split("_to_")
#     G.add_edge(source, target)


# # Example: Adding a new conversion
# # add_new_conversion('newsource_to_newtarget')


# # Example usage
# # print(find_shortest_conversion_path('cirq', 'qasm3'))


# # # Assuming G is your graph created as before

# # Position nodes using a layout algorithm - for example, spring layout
# pos = nx.spring_layout(G)

# # Draw the nodes (you can also customize the node size, color, etc.)
# nx.draw_networkx_nodes(G, pos, node_color="lightblue", node_size=500)

# # Draw the edges (you can also customize edge width, style, etc.)
# nx.draw_networkx_edges(G, pos, edge_color="gray")

# # Draw the node labels
# nx.draw_networkx_labels(G, pos)

# # Show the matplotlib plot
# plt.title("Program Conversion Graph")
# plt.axis("off")  # Turn off the axis
# plt.show()
