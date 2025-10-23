# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module for drawing quantum circuit diagrams

"""
from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING, Any, Optional

from pyqasm.printer import draw

from qbraid.programs import QPROGRAM_ALIASES, ProgramTypeError, get_program_type_alias
from qbraid.transpiler.converter import transpile
from qbraid.transpiler.exceptions import ConversionPathNotFoundError

from .exceptions import VisualizationError

if TYPE_CHECKING:
    import qbraid.programs


def circuit_drawer(
    program: qbraid.programs.QPROGRAM,
    as_package: Optional[str] = None,
    output: Optional[str] = None,
    **kwargs,
) -> Any:
    """Draws circuit diagram.

    Args:
        program: Supported quantum program
        as_package: The package to convert the program to before drawing
        output: The output format for the circuit diagram

    Raises:
        ProgramTypeError: If quantum program is not of a supported type
        ValueError: If an invalid output option is provided
    """
    package = get_program_type_alias(program)

    if as_package and as_package != package:
        if as_package not in QPROGRAM_ALIASES:
            raise ValueError(
                f"Invalid package '{as_package}'. "
                "Make sure the desired output package is installed."
            )
        program = transpile(program, as_package)
        package = as_package

    # pylint: disable=import-outside-toplevel

    if package == "qiskit":
        from qiskit.visualization import circuit_drawer as qiskit_drawer

        return qiskit_drawer(program, output=output, **kwargs)

    if package == "braket":
        if output in {None, "ascii"}:
            from braket.circuits.ascii_circuit_diagram import AsciiCircuitDiagram

            return print(AsciiCircuitDiagram.build_diagram(program))
        raise ValueError('The only valid option for braket are "ascii"')

    if package == "cirq":
        if output in {None, "text"}:
            return print(program.to_text_diagram(**kwargs))  # type: ignore[attr-defined]
        if output == "svg":
            from cirq.contrib.svg import SVGCircuit

            # pragma: no cover
            return SVGCircuit(program)
        if output == "svg_source":
            from cirq.contrib.svg import circuit_to_svg

            return circuit_to_svg(program)
        raise ValueError('The only valid options for cirq are "text", "svg", "svg_source"')

    if package == "pyquil":
        if output is None or output == "text":
            return print(program)
        if output == "latex":
            from pyquil.latex import display

            return display(program, **kwargs)  # pragma: no cover
        raise ValueError('The only valid options for pyquil are "text", "latex"')

    if package == "pytket":
        if output in {None, "jupyter"}:
            from pytket.circuit.display import render_circuit_jupyter

            return render_circuit_jupyter(program)  # pragma: no cover
        if output == "view_browser":
            from pytket.circuit.display import view_browser

            return view_browser(program, **kwargs)  # pragma: no cover
        if output == "html":
            from pytket.circuit.display import render_circuit_as_html

            return render_circuit_as_html(program, **kwargs)  # pragma: no cover
        raise ValueError('The only valid options for pytket are "jupyter", "view_browser", "html"')

    if package in {"qasm2", "qasm3"}:
        if output == "mpl" or (
            output is None and importlib.util.find_spec("matplotlib") is not None
        ):
            return draw(program, output="mpl", **kwargs)

        try:
            if package == "qasm2" and "cirq" in QPROGRAM_ALIASES:
                program = transpile(program, "cirq")
            elif "qiskit" in QPROGRAM_ALIASES:
                program = transpile(program, "qiskit")
            elif "braket" in QPROGRAM_ALIASES:
                program = transpile(program, "braket")
            else:
                raise ValueError("No supported package found for drawing circuit")
        except ConversionPathNotFoundError as err:
            raise VisualizationError(
                "Unable to convert program to a supported package for drawing"
            ) from err

        return circuit_drawer(program, output=output, **kwargs)

    if package == "pennylane":
        program = transpile(program, "qasm2")

        return circuit_drawer(program, output=output, **kwargs)

    raise ProgramTypeError(package)
