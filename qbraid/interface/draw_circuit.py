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
Module for drawing quantum circuit diagrams

"""
from typing import TYPE_CHECKING

from qbraid.exceptions import ProgramTypeError, VisualizationError

if TYPE_CHECKING:
    import qbraid


def circuit_drawer(program: "qbraid.QPROGRAM", output=None, **kwargs) -> None:
    """Draws circuit diagram.

    Args:
        :data:`~.qbraid.QPROGRAM`: Supported quantum program

    Raises:
        ProgramTypeError: If quantum program is not of a supported type
    """
    # todo: visualization from supportive framework
    if isinstance(program, str):
        package = "qasm"
    else:
        try:
            package = program.__module__
        except AttributeError as err:
            raise ProgramTypeError(program) from err

    if "qiskit" in package:
        from qiskit.visualization import circuit_drawer as qiskit_drawer

        return qiskit_drawer(program, output=output, **kwargs)

    elif "braket" in package:
        if output == None or output == "ascii":
            from braket.circuits.ascii_circuit_diagram import AsciiCircuitDiagram

            return print(AsciiCircuitDiagram.build_diagram(program))
        else:
            raise VisualizationError("The only valid option for braket are" "ascii")

    elif "cirq" in package:
        if output == None or output == "text":
            print(program.to_text_diagram(**kwargs))
        elif output == "svg":
            from cirq.contrib.svg import SVGCircuit

            return SVGCircuit(program)
        elif output == "svg_source":
            from cirq.contrib.svg import circuit_to_svg

            return circuit_to_svg(program)
        else:
            raise VisualizationError("The only valid option for cirq are" "text, svg, svf_source")

    elif "pyquil" in package:
        if output == None or output == "text":
            return print(program)
        elif output == "latex":
            from pyquil.latex import display

            return display(program, **kwargs)
        else:
            raise VisualizationError("The only valid option for pyquil are" "text, latex")

    elif "pytket" in package:
        if output == None or output == "jupyter":
            from pytket.circuit.display import render_circuit_jupyter

            return render_circuit_jupyter(program)  # Render interactive display
        elif output == "view_browser":
            from pytket.circuit.display import view_browser

            return view_browser(program, **kwargs)
        elif output == "html":
            from pytket.circuit.display import render_circuit_as_html

            return render_circuit_as_html(program, **kwargs)
        else:
            raise VisualizationError(
                "The only valid option for pytket are" "jupyter, view_browser, html"
            )

    else:
        raise ProgramTypeError(program)


# todo: plot_histogram, plot_state, device_drawer
