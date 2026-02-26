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
Module defining CudaQKernel Class

"""
from __future__ import annotations

import base64
from typing import Literal, Optional, Sequence

import cudaq
from qbraid_core.services.runtime.schemas import Program

from qbraid.programs.exceptions import ProgramTypeError

from ._model import GateModelProgram

#: Supported ``output_format`` values for :meth:`CudaQKernel.serialize`.
OutputFormat = Literal["qir", "openqasm2"]

# Internal mapping from output_format → cudaq.translate format string and
# the corresponding ``Program.format`` value accepted by the qBraid API.
_SERIALIZE_FORMATS: dict[str, dict[str, str]] = {
    "qir": {"cudaq_format": "qir-base", "program_format": "qir.ll"},
    "openqasm2": {"cudaq_format": "openqasm2", "program_format": "qasm2"},
}


class CudaQKernel(GateModelProgram):
    """Wrapper class for ``cudaq.PyKernel`` objects.

    Supports both zero-argument kernels and parameterized kernels that require
    concrete argument values for simulation, state inspection, or translation.

    Args:
        program: A ``cudaq.PyKernel`` instance.
        args: Optional concrete arguments to bind to a parameterized kernel.
            When provided, these are forwarded to ``cudaq.synthesize`` before
            any operation that requires a fully-bound kernel (e.g.
            ``get_state``, ``translate``).
    """

    def __init__(
        self,
        program: cudaq.PyKernel,
        args: Optional[Sequence] = None,
    ):
        super().__init__(program)
        if not isinstance(program, cudaq.PyKernel):
            raise ProgramTypeError(
                message=f"Expected 'cudaq.PyKernel' object, got '{type(program)}'."
            )
        self._args: Optional[tuple] = tuple(args) if args is not None else None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_synthesized_kernel(self) -> cudaq.PyKernel:
        """Return a kernel suitable for operations that need a fully-bound circuit.

        If the kernel is zero-argument, it is returned as-is. Otherwise
        ``cudaq.synthesize`` is called with the stored arguments to produce a
        concrete (argument-free) kernel.

        Raises:
            RuntimeError: If the kernel requires arguments but none were provided.
        """
        if self._args is not None:
            return cudaq.synthesize(self.program, *self._args)
        return self.program

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def with_args(self, *args) -> CudaQKernel:
        """Return a **new** ``CudaQKernel`` with the given arguments bound.

        This follows an immutable pattern — the original wrapper is left
        unchanged.

        Args:
            *args: Concrete argument values matching the kernel's signature.

        Returns:
            A new ``CudaQKernel`` instance with arguments stored.
        """
        return CudaQKernel(self.program, args=args)

    # ------------------------------------------------------------------
    # GateModelProgram interface
    # ------------------------------------------------------------------

    @property
    def qubits(self) -> list[int]:
        """Return the qubits acted upon by the operations in this circuit."""
        return list(range(self.num_qubits))

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits in the circuit.

        For zero-argument kernels this queries ``cudaq.get_state`` directly.
        If that fails (e.g. the kernel expects arguments), a synthesized
        kernel is used instead, provided ``args`` were supplied at
        construction time.
        """
        try:
            state = cudaq.get_state(self.program)
            return state.num_qubits()
        except Exception:  # noqa: BLE001
            # Kernel likely requires arguments — fall back to synthesized kernel.
            synthesized = self._get_synthesized_kernel()
            state = cudaq.get_state(synthesized)
            return state.num_qubits()

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return 0

    def serialize(self, output_format: OutputFormat = "qir") -> Program:
        """Return the program in a format suitable for submission to the qBraid API.

        Args:
            output_format: One of ``"qir"`` (default) or ``"openqasm2"``.

        Returns:
            A ``Program`` object whose ``format`` and ``data`` fields are
            populated according to the chosen output format.

        Raises:
            ValueError: If *output_format* is not recognised.
        """
        if output_format not in _SERIALIZE_FORMATS:
            raise ValueError(
                f"Unsupported output_format '{output_format}'. "
                f"Choose from: {sorted(_SERIALIZE_FORMATS)}"
            )

        kernel = self._get_synthesized_kernel()

        if output_format == "openqasm2":
            qasm: str = cudaq.translate(kernel, format="openqasm2")
            return Program(format="qasm2", data=qasm)

        # Default: QIR
        qir: str = cudaq.translate(kernel, format="qir-base")
        return Program(
            format="qir.ll",
            data=base64.b64encode(qir.encode("utf-8")).decode("utf-8"),
        )
