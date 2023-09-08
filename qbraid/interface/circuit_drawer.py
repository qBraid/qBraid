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

from qbraid.exceptions import ProgramTypeError, QasmError, VisualizationError
from qbraid.qasm_checks import get_qasm_version

if TYPE_CHECKING:
    import qbraid


def circuit_drawer(program: "qbraid.QPROGRAM", output=None, **kwargs) -> None:
    """Draws circuit diagram.

    Args:
        :data:`~.qbraid.QPROGRAM`: Supported quantum program

    Raises:
        ProgramTypeError: If quantum program is not of a supported type
    """
    if isinstance(program, str):
        try:
            package = get_qasm_version(program)
        except QasmError as err:
            raise ProgramTypeError(
                "Input of type string must represent a valid OpenQASM program."
            ) from err
    else:
        try:
            package = program.__module__
        except AttributeError as err:
            raise ProgramTypeError(program) from err

    # pylint: disable=import-outside-toplevel

    if "qiskit" in package:
        from qiskit.visualization import circuit_drawer as qiskit_drawer

        return qiskit_drawer(program, output=output, **kwargs)

    if "braket" in package:
        if output in (None, "ascii"):
            from braket.circuits.ascii_circuit_diagram import AsciiCircuitDiagram

            return print(AsciiCircuitDiagram.build_diagram(program))
        raise VisualizationError('The only valid option for braket are "ascii"')

    if "cirq" in package:
        if output in (None, "text"):
            return print(program.to_text_diagram(**kwargs))
        if output == "svg":
            from cirq.contrib.svg import SVGCircuit

            # coverage: ignore
            return SVGCircuit(program)
        if output == "svg_source":
            from cirq.contrib.svg import circuit_to_svg

            return circuit_to_svg(program)
        raise VisualizationError('The only valid option for cirq are "text", "svg", "svf_source"')

    if "pyquil" in package:
        if output is None or output == "text":
            return print(program)
        if output == "latex":
            from pyquil.latex import display

            # coverage: ignore
            return display(program, **kwargs)
        raise VisualizationError('The only valid option for pyquil are "text", "latex"')

    if "pytket" in package:
        if output in (None, "jupyter"):
            from pytket.circuit.display import render_circuit_jupyter

            # coverage: ignore
            return render_circuit_jupyter(program)  # Render interactive display
        if output == "view_browser":
            from pytket.circuit.display import view_browser

            # coverage: ignore
            return view_browser(program, **kwargs)
        if output == "html":
            from pytket.circuit.display import render_circuit_as_html

            # coverage: ignore
            return render_circuit_as_html(program, **kwargs)
        raise VisualizationError(
            'The only valid option for pytket are "jupyter", "view_browser", "html"'
        )

    if package == "qasm3":
        from qbraid.interface.qbraid_qasm3.circuit_drawer import draw_circuit

        # coverage: ignore
        return print(draw_circuit(program))

    if package == "qasm2":
        from qbraid.interface.qbraid_qasm3.tools import convert_to_qasm3

        # coverage: ignore
        qasm3_str = convert_to_qasm3(program)
        return print(draw_circuit(qasm3_str))

    raise ProgramTypeError(package)
