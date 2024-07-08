# Copyright (C) 2024 qBraid
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
from typing import TYPE_CHECKING, Optional

from cirq.contrib.svg import SVGCircuit
from IPython.display import Image

from qbraid.programs import QPROGRAM_ALIASES, ProgramTypeError, get_program_type_alias
from qbraid.transpiler.converter import transpile

from .draw_qasm3 import qasm3_drawer
from .exceptions import VisualizationError

if TYPE_CHECKING:
    import qbraid.programs


def circuit_drawer(
    program: "qbraid.programs.QPROGRAM",
    as_package: Optional[str] = None,
    output: Optional[str] = None,
    **kwargs,
) -> str | SVGCircuit | Image | None:
    """Draws circuit diagram.

    Args:
        :data:`~.qbraid.programs.QPROGRAM`: Supported quantum program

    Raises:
        ProgramTypeError: If quantum program is not of a supported type
    """
    package = get_program_type_alias(program)

    if as_package and as_package != package and as_package in QPROGRAM_ALIASES:
        program = transpile(program, as_package)
        package = as_package

    # pylint: disable=import-outside-toplevel

    if package == "qiskit":
        from qiskit.visualization import circuit_drawer as qiskit_drawer

        return qiskit_drawer(program, output=output, **kwargs)

    if package == "braket":
        if output in (None, "ascii"):
            from braket.circuits.ascii_circuit_diagram import AsciiCircuitDiagram

            print(AsciiCircuitDiagram.build_diagram(program))
            return None
        raise VisualizationError('The only valid option for braket are "ascii"')

    if package == "cirq":
        if output in (None, "text"):
            print(program.to_text_diagram(**kwargs))
            return None
        if output == "svg":
            # coverage: ignore
            return SVGCircuit(program)
        if output == "svg_source":
            from cirq.contrib.svg import circuit_to_svg

            return circuit_to_svg(program)
        raise VisualizationError('The only valid option for cirq are "text", "svg", "svg_source"')

    if package == "pyquil":
        if output is None or output == "text":
            print(program)
            return None
        if output == "latex":
            from pyquil.latex import display

            # coverage: ignore
            return display(program, **kwargs)
        raise VisualizationError('The only valid option for pyquil are "text", "latex"')

    if package == "pytket":
        if output in (None, "jupyter"):
            from pytket.circuit.display import render_circuit_jupyter

            # coverage: ignore
            render_circuit_jupyter(program)
            return None
        if output == "view_browser":
            from pytket.circuit.display import view_browser

            # coverage: ignore
            view_browser(program, **kwargs)
            return None
        if output == "html":
            from pytket.circuit.display import render_circuit_as_html

            # coverage: ignore
            return render_circuit_as_html(program, **kwargs)
        raise VisualizationError(
            'The only valid option for pytket are "jupyter", "view_browser", "html"'
        )

    if package == "qasm3":
        qasm3_drawer(program)
        return None

    if package == "qasm2":
        # coverage: ignore
        if "cirq" in QPROGRAM_ALIASES:
            program = transpile(program, "cirq")
        elif "qiskit" in QPROGRAM_ALIASES:
            program = transpile(program, "qiskit")
        else:
            program = transpile(program, "qasm3")

        return circuit_drawer(program, output=output, **kwargs)

    if package == "pennylane":
        program = transpile(program, "qasm2")

        return circuit_drawer(program, output=output, **kwargs)

    raise ProgramTypeError(package)
