# Copyright 2026 qBraid
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

# pylint: disable=no-name-in-module

# The above disable is necessary because the qcs_sdk.* modules load from Rust extension bindings
# (__file__ is None for submodules), so pylint/astroid can’t reliably introspect exported names
# and emits E0611 false positives.
"""
Module defining Rigetti device class
"""

from __future__ import annotations

import inspect
import socket
from contextvars import ContextVar
from multiprocessing.pool import ThreadPool
from typing import TYPE_CHECKING, Any, NamedTuple, cast
from urllib.parse import urlparse

import pyquil
import requests
from pyquil.quilbase import Gate, Pragma
from qcs_sdk.client import QCSClient
from qcs_sdk.compiler.quilc import (
    CompilerOpts,
    QuilcClient,
    TargetDevice,
    compile_program,
)
from qcs_sdk.qpu import ListQuantumProcessorsError, list_quantum_processors
from qcs_sdk.qpu.api import ExecutionOptions, SubmissionError
from qcs_sdk.qpu.api import submit as qpu_submit
from qcs_sdk.qpu.isa import (
    GetISAError,
    InstructionSetArchitecture,
    get_instruction_set_architecture,
)
from qcs_sdk.qpu.translation import TranslationOptions, translate

from qbraid._logging import logger
from qbraid.runtime import QuantumDevice, TargetProfile
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.exceptions import QbraidRuntimeError

from . import availability
from .job import RigettiJob, RigettiJobError

if TYPE_CHECKING:
    import datetime

    import qbraid.programs

# Short timeout (seconds) for the quilc TCP reachability probe so that
# transform() fails fast instead of hanging when the quilc server is down.
_QUILC_PROBE_TIMEOUT_S = 2.0

# Timeout (seconds) for the QCS REST call that fetches the maintenance calendar.
_QCS_CALENDAR_TIMEOUT_S = 10.0

# Default quilc compilation timeout (seconds).
#
# qcs_sdk's own default (``qcs_sdk.compiler.quilc.DEFAULT_COMPILER_TIMEOUT``) is 30s,
# which is a client-side deadline, not a quilc capability limit -- the quilc server's
# own ``--time-limit`` is unlimited by default. Compiling real user programs against a
# 100+ qubit ISA routinely takes 20-230s, and programs on that boundary were observed
# to succeed and fail non-deterministically with byte-identical input. 180s keeps the
# guard against a genuinely runaway compile while no longer failing ordinary work.
DEFAULT_COMPILER_TIMEOUT_S = 180.0

# runtime_options keys understood by _parse_runtime_options / _parse_compiler_options.
_TRANSLATION_OPTION_KEYS = frozenset(
    {
        "prepend_default_calibrations",
        "passive_reset_delay_seconds",
        "allow_unchecked_pointer_arithmetic",
        "allow_frame_redefinition",
    }
)
# runtime_options keys that map onto qcs_sdk's ``CompilerOpts``.
_COMPILER_OPTS_KEYS = frozenset({"compiler_timeout", "protoquil"})
# Every runtime_options key consumed during quilc compilation; membership is what makes
# run() publish a key and keeps _warn_unknown_runtime_options quiet about it.
# ``initial_rewiring`` is applied to the program text rather than to ``CompilerOpts``.
_COMPILER_OPTION_KEYS = _COMPILER_OPTS_KEYS | frozenset({"initial_rewiring"})

# Quil-T instruction names that a gate-model program can acquire by accident: OpenQASM
# ``barrier`` lowers to ``FENCE`` (and qiskit's ``measure_all()`` inserts a barrier for
# you). Unlike DELAY / DEFCAL / pulse instructions, a FENCE carries no pulse-level
# information that quilc would destroy.
_FENCE_INSTRUCTION_NAMES = frozenset({"FENCE"})

# quilc's INITIAL_REWIRING strategy is a Quil PRAGMA, not a quilc server flag, so
# the only way to select one is to rewrite the program being compiled.
_INITIAL_REWIRING_PRAGMA = "INITIAL_REWIRING"
_INITIAL_REWIRING_STRATEGIES = frozenset({"NAIVE", "PARTIAL", "GREEDY", "RANDOM"})

# Substrings identifying a quilc compilation *timeout* (as opposed to any other
# compilation failure) in the error text returned by the RPCQ server.
_QUILC_TIMEOUT_MARKERS = ("time limit", "timed out", "timeout")


class _ResolvedCompilerOptions(NamedTuple):
    """quilc options for one ``run()``, plus the timeout they encode.

    ``CompilerOpts`` is a Rust binding with no attribute getters, so the timeout is
    carried alongside purely so a compilation timeout can name the deadline exceeded.
    ``initial_rewiring`` rides here because it resolves from the same runtime_options,
    though it is applied to the program text rather than passed to quilc.
    """

    options: CompilerOpts | None
    timeout: float | None
    initial_rewiring: str | None = None


# Per-run quilc options. A ContextVar rather than instance state because a single device
# is routinely shared: two concurrent run() calls with different compiler_timeout values
# must not clobber each other, and the loser would silently compile under the wrong
# deadline.
#
# This is safe only because transform() runs in the same context as the run() that set
# the value: QuantumDevice.run calls apply_runtime_profile (and therefore transform)
# inline, and only then hands the compiled programs to submit(). A ContextVar is *not*
# visible in threads started by submit()'s ThreadPool, so nothing downstream of submit()
# may read this.
#
# ``None`` means "no enclosing run()", which submit() uses to tell a direct call apart
# from one made on its behalf.
_COMPILER_OPTIONS: ContextVar[_ResolvedCompilerOptions | None] = ContextVar(
    "rigetti_compiler_options", default=None
)


def quil_t_instruction_counts(program: pyquil.Program) -> dict[str, int]:
    """Count the Quil-T (pulse/timing) instructions in a Quil program by name.

    Classification defers to quil-rs's own ``Instruction.is_quil_t`` -- the same
    predicate behind pyquil's ``Program.remove_quil_t_instructions`` -- so what counts
    as Quil-T stays in sync with pyquil instead of a hand-maintained list. Names are the
    leading Quil token, e.g. ``FENCE``, ``DELAY``, ``PULSE``, ``DEFCAL``, ``DEFFRAME``.

    Reaching through ``Program._program`` is deliberate: ``is_quil_t`` lives on the
    quil-rs instruction, and pyquil's public wrappers do not expose it. The only public
    alternative is differencing against ``remove_quil_t_instructions()``, which yields a
    boolean rather than the per-name counts the error messages need.

    Args:
        program: The Quil program to inspect.

    Returns:
        A mapping of Quil-T instruction name to the number of occurrences. Empty when
        the program is pure gate model.
    """
    counts: dict[str, int] = {}
    for instruction in program._program.to_instructions():  # pylint: disable=protected-access
        if not instruction.is_quil_t():
            continue
        # Every Quil instruction begins with its keyword, so this cannot come up empty;
        # if it ever does, the IndexError is a real bug and should surface as one.
        name = instruction.to_quil().split("\n", 1)[0].split(maxsplit=1)[0]
        counts[name] = counts.get(name, 0) + 1
    return counts


def contains_quil_t(program: pyquil.Program) -> bool:
    """Check whether a Quil program uses any Quil-T (pulse/timing) features.

    quilc is a gate-model compiler and, per Rigetti's docs, "Quil-T instructions are not
    supported by quilc or the QVM": it raises a type error on ``DELAY`` (binding the
    duration into a qubit slot) and cannot rewire ``FENCE``. Such programs must skip
    quilc and go straight to the QCS translation service, which accepts both gate-model
    and pulse-model instructions -- at the cost of requiring native gates, since
    nativization is what quilc would otherwise have done.

    Detection defers to pyquil's own ``Program.remove_quil_t_instructions``, so what
    counts as Quil-T stays in sync with pyquil instead of a hand-maintained list. This
    also covers ``DEFFRAME`` / ``DEFCAL`` / ``DEFWAVEFORM`` definitions.

    Args:
        program: The Quil program to inspect.

    Returns:
        True if the program contains any Quil-T instructions or definitions.
    """
    return program != program.remove_quil_t_instructions()


def non_native_gate_counts(program: pyquil.Program, native_gates: set[str]) -> dict[str, int]:
    """Count gates in a program that the device cannot execute without quilc.

    The check is by instruction *name* against the device ISA, plus any gate carrying a
    modifier (``CONTROLLED`` / ``DAGGER`` / ``FORKED``), which no Rigetti QPU executes
    directly. A gate the program defines its own ``DEFCAL`` for counts as executable
    too: QCS translation runs the supplied calibration, so such a gate never needed
    quilc.

    The check is deliberately one-sided: a gate is reported only when its name is
    absent from both sets, so a name that is present but parameterised outside the
    native range (``RX(0.3)``, say, where only multiples of pi/2 are native) is not
    flagged. That keeps the check from ever turning a program that runs today into an
    error; it only recognises the unambiguous cases (``H``, ``CNOT``, ``T``, ...).

    Args:
        program: The Quil program to inspect.
        native_gates: Uppercase instruction names from the device ISA.

    Returns:
        A mapping of gate label to the number of occurrences, ordered by first
        appearance. Empty when every gate is (nominally) executable as written.
    """
    # DEFCAL is qubit-specific, but matching on name alone keeps the permissive
    # direction consistent with the rest of the check.
    calibrated = {calibration.name.upper() for calibration in program.calibrations}
    executable = native_gates | calibrated

    counts: dict[str, int] = {}
    for instruction in program.instructions:
        if not isinstance(instruction, Gate):
            continue
        modifiers = [str(modifier) for modifier in instruction.modifiers]
        if not modifiers and instruction.name.upper() in executable:
            continue
        label = " ".join([*modifiers, instruction.name])
        counts[label] = counts.get(label, 0) + 1
    return counts


def _format_counts(counts: dict[str, int]) -> str:
    """Render a name -> count mapping as ``NAME (n), OTHER (m)``."""
    return ", ".join(f"{name} ({count})" for name, count in counts.items())


class RigettiDeviceError(QbraidRuntimeError):
    """Class for errors raised while processing a Rigetti device."""


class RigettiDevice(QuantumDevice):
    """Wraps a single Rigetti QCS quantum processor or simulator."""

    def __init__(
        self,
        profile: TargetProfile,
        qcs_client: QCSClient,
    ):
        """Initialize a RigettiDevice.

        Args:
            profile: A TargetProfile object (constructed by RigettiProvider).
            qcs_client: An authenticated QCSClient used for QCS API calls.

        ``ExecutionOptions`` are not stored on the device. Instead, callers
        pass an ``execution_options=`` kwarg to ``run()`` / ``submit()`` so
        each job can use a different connection strategy without forcing
        re-instantiation of the device.

        ``_compiler_options`` is an escape hatch for a ``CompilerOpts`` that should
        apply to every compilation on this device. Prefer the ``compiler_timeout`` /
        ``protoquil`` keys of ``runtime_options`` on :meth:`run`, which scope the
        options to a single call.
        """
        super().__init__(profile=profile)
        self._qcs_client = qcs_client
        self._compiler_options: CompilerOpts | None = None

    @property
    def client(self) -> QCSClient:
        """Return the QCSClient associated with this device."""
        return self._qcs_client

    def __str__(self) -> str:
        """String representation of the RigettiDevice object."""
        return f"{self.__class__.__name__}('{self.id}')"

    def status(self) -> DeviceStatus:
        """Return the current status of the device.

        The status reflects both QCS catalog membership and Rigetti's
        published maintenance schedule:

        - ``OFFLINE`` when the quantum processor is absent from the QCS
          catalog (``list_quantum_processors``).
        - ``UNAVAILABLE`` when the processor is in the catalog but currently
          inside a scheduled maintenance window. During maintenance the QCS
          gateway queues jobs rather than executing them, so the device is
          reachable but not running programs.
        - ``ONLINE`` otherwise.

        Maintenance windows are evaluated by
        :func:`qbraid.runtime.rigetti.availability.is_in_maintenance` against
        the calendar fetched from the QCS REST API (see
        :meth:`maintenance_calendar`). If that fetch or its parsing fails
        (``RigettiDeviceError`` from the QCS request, or a ``ValueError`` /
        ``TypeError`` from malformed calendar data), the device is reported as
        ``ONLINE`` (catalog membership still holds) and a warning is logged, so
        a transient calendar-service issue never makes ``status()`` raise. Any
        other (unexpected) exception is not suppressed and propagates, so
        genuine bugs are not masked as ``ONLINE``.
        """
        try:
            quantum_processor_ids = set(list_quantum_processors(client=self._qcs_client))
        except ListQuantumProcessorsError as e:
            raise RigettiDeviceError(  # pylint: disable=bad-exception-cause
                "Failed to retrieve quantum processor list from Rigetti QCS."
            ) from e

        if self.id not in quantum_processor_ids:
            return DeviceStatus.OFFLINE

        try:
            if availability.is_in_maintenance(self._fetch_maintenance_ical()):
                return DeviceStatus.UNAVAILABLE
        except (RigettiDeviceError, ValueError, TypeError) as e:
            # The device is in the catalog and reachable; maintenance data is
            # supplemental, so a calendar fetch/parse failure must not break
            # status(). Degrade to ONLINE and surface the reason as a warning.
            # RigettiDeviceError covers QCS fetch failures; ValueError/TypeError
            # cover malformed calendar data (icalendar / recurring_ical_events).
            # Unexpected exceptions propagate so real bugs aren't masked.
            logger.warning(
                "Could not determine maintenance status for Rigetti device '%s'; "
                "assuming ONLINE. Reason: %s",
                self.id,
                e,
            )

        return DeviceStatus.ONLINE

    def _fetch_maintenance_ical(self) -> str:
        """Fetch the raw maintenance iCalendar for this processor from QCS.

        ``qcs_sdk`` exposes no calendar/maintenance route (it is
        execution-only), so this issues the REST call directly against
        ``GET {api_url}/v1/calendars/{id}``, reusing the device's
        ``QCSClient`` for the API base URL and the (auto-refreshing) OAuth
        bearer token. The response contains a ``maintenanceICal`` field whose
        value is an RFC 5545 calendar listing the windows during which
        execution on the QPU is unavailable.

        Returns:
            The iCalendar text, or an empty string when no maintenance
            calendar is published for the processor.

        Raises:
            RigettiDeviceError: If the QCS calendar request fails.
        """
        api_url = self._qcs_client.api_url.rstrip("/")
        url = f"{api_url}/v1/calendars/{self.id}"
        try:
            access_token = self._qcs_client.oauth_session.request_access_token().secret
            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                timeout=_QCS_CALENDAR_TIMEOUT_S,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise RigettiDeviceError(
                f"Failed to fetch maintenance calendar for quantum processor '{self.id}' "
                "from the Rigetti QCS API."
            ) from e

        return payload.get("maintenanceICal") or ""

    def maintenance_calendar(self) -> str:
        """Return the raw maintenance iCalendar (RFC 5545) for this processor.

        The returned string lists the scheduled maintenance windows during
        which execution on this device is unavailable. It is empty when no
        maintenance is published for the processor.

        Raises:
            RigettiDeviceError: If the QCS calendar request fails.
        """
        return self._fetch_maintenance_ical()

    def availability_window(self) -> tuple[bool, str, datetime.datetime | None]:
        """Provide device availability based on the QCS maintenance calendar.

        Indicates current availability, the time remaining (``HH:MM:SS``)
        until the next change in availability, and the future UTC datetime of
        that change. Delegates to
        :func:`qbraid.runtime.rigetti.availability.next_available_time`.

        Returns:
            tuple[bool, str, Optional[datetime.datetime]]: Current
                availability, ``HH:MM:SS`` until the availability switch, and
                the future UTC datetime of the switch.

        Raises:
            RigettiDeviceError: If a QCS request fails.
        """
        return availability.next_available_time(self)

    def _probe_quilc_reachable(self) -> None:
        """Verify that the configured quilc endpoint accepts TCP connections.

        ``compile_program`` will hang indefinitely if quilc is not running,
        which makes ``run()`` look frozen. We perform a short TCP connect
        probe (default 2s) against the host:port from
        ``self._qcs_client.quilc_url`` and raise ``RigettiDeviceError`` on
        failure so users get an immediate, actionable error.
        """
        quilc_url = self._qcs_client.quilc_url
        parsed = urlparse(quilc_url)
        host = parsed.hostname
        port = parsed.port
        if not host or not port:
            # Can't introspect a non-standard URL; skip the probe
            return

        try:
            with socket.create_connection((host, port), timeout=_QUILC_PROBE_TIMEOUT_S):
                pass
        except OSError as exc:
            raise RigettiDeviceError(
                f"quilc not reachable at {quilc_url}. "
                "Start a local quilc server or set QCS_QUILC_ENDPOINT to "
                "an available endpoint before calling run()."
            ) from exc

    @staticmethod
    def _warn_unknown_runtime_options(runtime_options: dict[str, Any] | None) -> None:
        """Log a warning naming any ``runtime_options`` key that has no effect.

        Unrecognised keys used to be dropped in silence, which is indistinguishable
        from the option being applied: a user passing ``compiler_timeout`` before it
        was supported got no feedback that it did nothing.
        """
        if not runtime_options:
            return

        unknown = sorted(set(runtime_options) - _TRANSLATION_OPTION_KEYS - _COMPILER_OPTION_KEYS)
        if unknown:
            logger.warning(
                "Ignoring unrecognized runtime_options key(s) for Rigetti: %s. "
                "Recognized keys are: %s.",
                ", ".join(unknown),
                ", ".join(sorted(_TRANSLATION_OPTION_KEYS | _COMPILER_OPTION_KEYS)),
            )

    @staticmethod
    def _warn_compiler_keys_outside_run(runtime_options: dict[str, Any] | None) -> None:
        """Log a warning when quilc keys are handed to ``submit()`` directly.

        Compilation happens in :meth:`transform`, which :meth:`run` invokes before it
        reaches ``submit()``. A bare ``submit()`` never compiles, so the quilc keys have
        nothing to act on -- and dropping them in silence is the failure this whole path
        exists to remove. ``run()`` publishes its resolution on :data:`_COMPILER_OPTIONS`
        first, which is how the two callers are told apart.
        """
        if not runtime_options or _COMPILER_OPTIONS.get() is not None:
            return

        compiler_keys = sorted(_COMPILER_OPTION_KEYS & set(runtime_options))
        if compiler_keys:
            logger.warning(
                "Ignoring quilc runtime_options key(s) %s: they apply during "
                "compilation, which happens in transform() before submit() is reached. "
                "Pass them to run() instead.",
                ", ".join(compiler_keys),
            )

    @staticmethod
    def _parse_runtime_options(
        runtime_options: dict[str, Any] | None,
    ) -> TranslationOptions | None:
        """Extract known translation keys from a runtime_options dict.

        Recognized translation keys are mapped to ``TranslationOptions.v2()``.
        Unrecognized keys are ignored, with a warning naming each one.

        Returns:
            A ``TranslationOptions`` instance, or ``None`` when no recognised
            translation keys are present.
        """
        RigettiDevice._warn_unknown_runtime_options(runtime_options)

        if not runtime_options:
            return None

        translation_kwargs = {
            k: runtime_options[k] for k in _TRANSLATION_OPTION_KEYS if k in runtime_options
        }
        return TranslationOptions.v2(**translation_kwargs) if translation_kwargs else None

    @staticmethod
    def _parse_compiler_options(
        runtime_options: dict[str, Any] | None,
    ) -> CompilerOpts | None:
        """Extract known quilc compiler keys from a runtime_options dict.

        Recognized keys are ``compiler_timeout`` (seconds, or ``None`` for no limit)
        and ``protoquil``. ``initial_rewiring`` is deliberately not read here: building
        a ``CompilerOpts`` from it would override a device-level ``_compiler_options``
        for a caller who only asked to change the rewiring. Unrecognized keys are
        ignored, with a warning naming each one.

        Returns:
            A ``CompilerOpts`` instance, or ``None`` when no recognised compiler keys
            are present, in which case :meth:`transform` applies
            :data:`DEFAULT_COMPILER_TIMEOUT_S`.
        """
        if not runtime_options or not _COMPILER_OPTS_KEYS & set(runtime_options):
            return None

        # qcs_sdk's CompilerOpts default is 30s; ours is DEFAULT_COMPILER_TIMEOUT_S, so
        # the timeout is always set explicitly, even when only `protoquil` was given.
        kwargs: dict[str, Any] = {
            "timeout": runtime_options.get("compiler_timeout", DEFAULT_COMPILER_TIMEOUT_S)
        }
        if "protoquil" in runtime_options:
            kwargs["protoquil"] = runtime_options["protoquil"]
        return CompilerOpts(**kwargs)

    @staticmethod
    def _parse_initial_rewiring(runtime_options: dict[str, Any] | None) -> str | None:
        """Return the validated quilc ``INITIAL_REWIRING`` strategy, or ``None``.

        ``None`` means "leave the program alone": quilc's own default (``PARTIAL``)
        and any pragma the program already carries both survive.

        Raises:
            ValueError: If the strategy is not one quilc recognises -- an unrecognised
                pragma value makes quilc reject the whole program opaquely, so failing
                at parse time with the supported set named is deliberate.
        """
        if not runtime_options:
            return None

        strategy = runtime_options.get("initial_rewiring")
        if strategy is None:
            return None

        normalized = str(strategy).strip().upper()
        if normalized not in _INITIAL_REWIRING_STRATEGIES:
            raise ValueError(
                f"Unsupported initial_rewiring {strategy!r} for quantum processor. "
                f"Expected one of: {', '.join(sorted(_INITIAL_REWIRING_STRATEGIES))}."
            )
        return normalized

    @staticmethod
    def _apply_initial_rewiring(program: pyquil.Program, strategy: str | None) -> pyquil.Program:
        """Prepend an ``INITIAL_REWIRING`` pragma to ``program``.

        A program that already declares the pragma is returned untouched: the author's
        value is more specific than a device-wide option, and quilc applies the pragma
        positionally (it accepts more than one, verified on 1.26.0), so prepending a
        second would silently change which strategy governs their program.

        The pragma need not be the literal first line: pyquil's ``out()`` emits
        ``DECLARE`` before it, and quilc honours it there.
        """
        if strategy is None:
            return program

        if any(
            isinstance(instruction, Pragma) and instruction.command == _INITIAL_REWIRING_PRAGMA
            for instruction in program.instructions
        ):
            logger.warning(
                "Ignoring initial_rewiring=%s: the program already declares a "
                "PRAGMA %s, which takes precedence.",
                strategy,
                _INITIAL_REWIRING_PRAGMA,
            )
            return program

        return pyquil.Program(f'PRAGMA {_INITIAL_REWIRING_PRAGMA} "{strategy}"') + program

    @staticmethod
    def _compiler_timeout(runtime_options: dict[str, Any] | None) -> float | None:
        """Return the quilc timeout (seconds) that ``runtime_options`` resolves to."""
        if not runtime_options:
            return DEFAULT_COMPILER_TIMEOUT_S
        return runtime_options.get("compiler_timeout", DEFAULT_COMPILER_TIMEOUT_S)

    def _resolve_compiler_options(self) -> _ResolvedCompilerOptions:
        """Determine the quilc options in effect for the current compilation.

        Precedence: options set by the enclosing :meth:`run` (from
        ``runtime_options``), then a ``_compiler_options`` attribute set directly on
        the device, then :data:`DEFAULT_COMPILER_TIMEOUT_S`.

        ``initial_rewiring`` is carried across every branch, not only the first: it is
        not a ``CompilerOpts`` field, so ``run()`` publishes it with ``options=None``
        in the common case, and an early return on ``options`` alone would drop it.
        """
        resolved = _COMPILER_OPTIONS.get()
        initial_rewiring = resolved.initial_rewiring if resolved is not None else None

        if resolved is not None and resolved.options is not None:
            return resolved

        if self._compiler_options is not None:
            return _ResolvedCompilerOptions(self._compiler_options, None, initial_rewiring)

        return _ResolvedCompilerOptions(
            CompilerOpts(timeout=DEFAULT_COMPILER_TIMEOUT_S),
            DEFAULT_COMPILER_TIMEOUT_S,
            initial_rewiring,
        )

    def _fetch_isa(self) -> InstructionSetArchitecture | None:
        """Return the device ISA, or ``None`` when the lookup fails.

        The nativity check this feeds is a diagnostic, so a failed lookup must not
        decide the outcome; callers fall back to their previous behaviour. The compile
        path re-fetches and does raise, since quilc genuinely cannot run without it.
        """
        try:
            return get_instruction_set_architecture(
                quantum_processor_id=self.id, client=self._qcs_client
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning(
                "Could not retrieve the ISA for quantum processor '%s' to check gate "
                "nativity; proceeding without the check. Reason: %s",
                self.id,
                e,
            )
            return None

    def transform(self, run_input: pyquil.Program) -> pyquil.Program:
        """Compile a Quil program into the QPU's native gate set via quilc.

        Per the ``QuantumDevice.transform`` contract, the input/output type
        must match: ``Program`` in, ``Program`` out. Quil-string lowering
        is handled by ``ProgramSpec.serialize`` (configured by the provider
        as ``lambda program: program.out()``).

        quilc cannot compile Quil-T (pulse/timing) instructions, so a program
        containing them has to go straight to the QCS translation service, which in
        exchange accepts only native gates. Three cases follow:

        1. **No Quil-T.** Compiled by quilc as usual.
        2. **Quil-T, every gate already native or carrying its own ``DEFCAL``.** Passed
           through untouched, preserving both the Quil-T instructions and the program's
           explicit qubit placement (quilc would rewire it).
        3. **Quil-T plus non-native gates.** Unrunnable as-is. When the only Quil-T is
           ``FENCE``, the fences are dropped and quilc compiles the program (see
           below); otherwise :class:`RigettiDeviceError` is raised naming both the
           Quil-T instructions and the non-native gates.

        The ``FENCE`` carve-out exists because a fence is the one Quil-T instruction a
        gate-model program acquires by accident: OpenQASM ``barrier`` lowers to
        ``FENCE``, and qiskit's ``measure_all()`` inserts a barrier of its own. Dropping
        the fences is not a lossy choice made lightly -- there is simply nowhere to put
        them back. quilc rewrites the program wholesale (rewiring logical to physical
        qubits, decomposing, reordering and merging gates across the fence boundary), so
        a source-position fence has no well-defined image in the compiled output.

        quilc options come from ``runtime_options`` passed to :meth:`run` (see
        :meth:`_parse_compiler_options`), or from a ``_compiler_options`` attribute set
        directly on the device. Absent both, the timeout is
        :data:`DEFAULT_COMPILER_TIMEOUT_S`.

        Raises:
            RigettiDeviceError: If the program mixes Quil-T with non-native gates, or
                if quilc is unreachable or compilation fails.
        """
        quil_t_counts = quil_t_instruction_counts(run_input)
        if not quil_t_counts:
            return self._compile_with_quilc(run_input)

        isa = self._fetch_isa()
        non_native = (
            non_native_gate_counts(run_input, {op.name.upper() for op in isa.instructions})
            if isa is not None
            else {}
        )

        if not non_native:
            logger.info(
                "Program uses Quil-T (pulse/timing) instructions (%s), which quilc cannot "
                "compile; skipping quilc and passing the program to the QCS translation "
                "service unchanged.",
                _format_counts(quil_t_counts),
            )
            return run_input

        if set(quil_t_counts) <= _FENCE_INSTRUCTION_NAMES:
            logger.warning(
                "Program contains %s but also %d non-native gate(s) (%s) that only quilc "
                "can convert. Dropping the fence(s) so the program can be compiled; a "
                "FENCE has no well-defined position in quilc's rewritten output. Note "
                "that OpenQASM `barrier` becomes FENCE, and qiskit's measure_all() "
                "inserts a barrier for you.",
                _format_counts(quil_t_counts),
                sum(non_native.values()),
                _format_counts(non_native),
            )
            return self._compile_with_quilc(run_input.remove_quil_t_instructions(), isa=isa)

        raise RigettiDeviceError(self._quil_t_conflict_message(quil_t_counts, non_native))

    def _quil_t_conflict_message(
        self, quil_t_counts: dict[str, int], non_native: dict[str, int]
    ) -> str:
        """Build the error explaining why a Quil-T program cannot reach the QPU."""
        lines = [
            f"Program cannot be compiled for quantum processor '{self.id}'. It contains "
            "Quil-T (pulse/timing) instructions, so it must bypass the quilc compiler and "
            "go directly to QCS translation, which accepts only native gates. But it also "
            f"contains {sum(non_native.values())} non-native gate(s), which only quilc can "
            "convert.",
            f"  - Quil-T instructions found: {_format_counts(quil_t_counts)}",
            f"  - Non-native gates found: {_format_counts(non_native)}",
            "To fix, either remove the Quil-T instructions so quilc can compile the "
            "program, or rewrite the gates in the device's native set yourself.",
        ]
        if set(quil_t_counts) & _FENCE_INSTRUCTION_NAMES:
            lines.append(
                "Note: `barrier` in OpenQASM becomes Quil-T `FENCE`. If you used "
                "measure_all() in Qiskit it inserted a barrier for you; use explicit "
                "measure(...) or remove the barrier to let quilc compile normally."
            )
        return "\n".join(lines)

    def _compilation_target(self, isa: InstructionSetArchitecture | None) -> TargetDevice:
        """Build quilc's compilation target from the device ISA.

        Kept out of the ``compile_program`` try block so that an ISA lookup failure --
        which is a network call, and can itself report "timed out" -- is never mistaken
        for a quilc compilation timeout and answered with advice about
        ``compiler_timeout``.

        Raises:
            RigettiDeviceError: If the ISA cannot be retrieved or converted.
        """
        try:
            return TargetDevice.from_isa(
                isa
                if isa is not None
                else get_instruction_set_architecture(
                    quantum_processor_id=self.id, client=self._qcs_client
                )
            )
        except Exception as e:
            raise RigettiDeviceError(
                f"quilc failed to compile the program for quantum processor '{self.id}': {e}"
            ) from e

    def _compile_with_quilc(
        self, run_input: pyquil.Program, isa: InstructionSetArchitecture | None = None
    ) -> pyquil.Program:
        """Run quilc over a pure gate-model program and return the native result.

        Args:
            run_input: A Quil program with no Quil-T instructions.
            isa: An already-fetched ISA to compile against, saving a second QCS
                round-trip when the caller has one. ``None`` fetches it here.

        Raises:
            RigettiDeviceError: If quilc is unreachable or compilation fails.
        """
        # Fail fast if quilc isn't running, instead of hanging in compile_program.
        self._probe_quilc_reachable()

        target = self._compilation_target(isa)
        compiler_options, timeout, initial_rewiring = self._resolve_compiler_options()
        run_input = self._apply_initial_rewiring(run_input, initial_rewiring)

        try:
            compilation_result = compile_program(
                quil=run_input.out(),
                target=target,
                client=QuilcClient.new_rpcq(self._qcs_client.quilc_url),
                options=compiler_options,
            )
            compiled_quil = compilation_result.program.to_quil()
        except Exception as e:
            message = str(e)
            if any(marker in message.lower() for marker in _QUILC_TIMEOUT_MARKERS):
                # quilc's raw text here is a lisp-flavoured "time limit: 30.0d0 seconds",
                # which says nothing about the knob that controls it.
                limit = f"within {timeout}s" if timeout is not None else "within its time limit"
                raise RigettiDeviceError(
                    f"quilc could not compile this program for quantum processor "
                    f"'{self.id}' {limit}. Retry with a longer limit, e.g. "
                    "runtime_options={'compiler_timeout': 300}, or reduce the circuit's "
                    f"depth or qubit count. quilc reported: {e}"
                ) from e
            # Surface quilc's own reason: it is the only thing that says *why*. quilc's
            # reachability is already established by the probe above, so the failure is
            # about the program itself.
            raise RigettiDeviceError(
                f"quilc failed to compile the program for quantum processor '{self.id}': {e}"
            ) from e

        return pyquil.Program(compiled_quil)

    def _submit(
        self,
        run_input: str,
        shots: int,
        execution_options: ExecutionOptions | None = None,
        translation_options: TranslationOptions | None = None,
    ) -> RigettiJob:
        """
        Submit a Quil program to the Rigetti QPU.

        Args:
            run_input: A serialized Quil program string (produced by prepare()).
            shots: Number of shots for the job (must be > 0).
            execution_options: Optional ``ExecutionOptions``. ``None`` falls back to
                the qcs_sdk default (Gateway connection strategy).
            translation_options: Optional ``TranslationOptions`` forwarded to
                ``translate()``. ``None`` uses the qcs_sdk default backend.
        """
        if shots is None or shots <= 0:
            raise RigettiJobError(
                f"Shots > 0 must be specified for Rigetti QPU jobs, current value: {shots}."
            )

        try:
            translation_result = translate(
                native_quil=run_input,
                num_shots=shots,
                quantum_processor_id=self.id,
                client=self._qcs_client,
                translation_options=translation_options,
            )
        except Exception as e:
            # Surface the translation service's own reason. It is consistently more
            # precise than any generic hint we can offer: it names the offending
            # instruction (e.g. ``at instruction 0 ("H 0"): this instruction must be
            # replaced or decomposed prior to compilation``), and it distinguishes
            # causes a fixed message cannot -- missing frames from
            # ``prepend_default_calibrations=False``, an out-of-range
            # ``passive_reset_delay_seconds``, or a DEFFRAME that differs from the
            # Rigetti defaults, none of which are gate-nativity problems.
            raise RigettiJobError(
                f"Translation failed for quantum processor '{self.id}': {e}"
            ) from e

        try:
            job_id = qpu_submit(
                program=translation_result.program,
                patch_values={},
                quantum_processor_id=self.id,
                client=self._qcs_client,
                execution_options=execution_options,
            )
        except SubmissionError as e:
            raise RigettiJobError("Failed to submit job to Rigetti QCS.") from e

        return RigettiJob(
            job_id=job_id,
            num_shots=shots,
            device=self,
            qcs_client=self._qcs_client,
            ro_sources=translation_result.ro_sources,
            execution_options=execution_options,
            compiled_program=run_input,
        )

    # pylint: disable-next=arguments-differ
    def submit(
        self,
        run_input: str | list[str],
        shots: int,
        execution_options: ExecutionOptions | None = None,
        runtime_options: dict[str, Any] | None = None,
    ) -> RigettiJob | list[RigettiJob]:
        """
        Submit one or more jobs to the Rigetti device.

        Args:
            run_input: A serialized Quil program string (or a list of them).
            shots: Number of shots per job (must be > 0).
            execution_options: Optional ``ExecutionOptions`` applied to every
                job in this submission. ``None`` falls back to the qcs_sdk
                default (Gateway connection strategy).
            runtime_options: Optional dict of translation options forwarded
                to ``translate()``. Recognised keys are
                ``prepend_default_calibrations``,
                ``passive_reset_delay_seconds``,
                ``allow_unchecked_pointer_arithmetic``, and
                ``allow_frame_redefinition``. Unrecognised keys are ignored,
                with a warning naming each one.

        Note:
            The quilc keys (``compiler_timeout``, ``protoquil``) apply during
            compilation, which happens in :meth:`transform` before ``submit()`` is
            reached. Calling ``submit()`` directly therefore skips compilation
            altogether, and those keys have nothing to act on; passing them here logs
            a warning saying so. Pass them to :meth:`run`.
        """
        self._warn_compiler_keys_outside_run(runtime_options)
        translation_options = self._parse_runtime_options(runtime_options)

        if isinstance(run_input, list):
            with ThreadPool(5) as pool:
                quantum_jobs = pool.map(
                    lambda job: self._submit(
                        job,
                        shots,
                        execution_options=execution_options,
                        translation_options=translation_options,
                    ),
                    run_input,
                )
                return quantum_jobs

        return self._submit(
            run_input,
            shots,
            execution_options=execution_options,
            translation_options=translation_options,
        )

    def run(
        self,
        run_input: qbraid.programs.QPROGRAM | list[qbraid.programs.QPROGRAM],
        *args: Any,
        **kwargs: Any,
    ) -> RigettiJob | list[RigettiJob]:
        """Run one or more programs on this device.

        Identical to :meth:`QuantumDevice.run`, except that the quilc keys in
        ``runtime_options`` (``compiler_timeout``, ``protoquil``, ``initial_rewiring``)
        are published for :meth:`transform` for the duration of the call. ``run()``
        compiles before it submits, so options consumed by quilc cannot be forwarded
        through :meth:`submit` the way the translation options are.

        Args:
            run_input: A program, or list of programs, to run on the device. This is
                any program type the conversion graph can reach ``pyquil`` from, not
                only a ``pyquil.Program``: ``run()`` sits *before* transpilation, and
                raw OpenQASM 2/3 strings are the common case in practice.
                :meth:`transform` is the step that receives a ``pyquil.Program``,
                because it runs after ``apply_runtime_profile`` has transpiled to the
                device's ``ProgramSpec`` type.
            *args: Forwarded to :meth:`submit`.
            **kwargs: Forwarded to :meth:`submit`. See
                :meth:`_parse_compiler_options` and :meth:`_parse_runtime_options` for
                the recognised ``runtime_options`` keys.
        """
        runtime_options = self._runtime_options_from_call(run_input, args, kwargs)
        resolved = _ResolvedCompilerOptions(
            self._parse_compiler_options(runtime_options),
            self._compiler_timeout(runtime_options),
            self._parse_initial_rewiring(runtime_options),
        )
        token = _COMPILER_OPTIONS.set(resolved)
        try:
            return cast("RigettiJob | list[RigettiJob]", super().run(run_input, *args, **kwargs))
        finally:
            _COMPILER_OPTIONS.reset(token)

    def _runtime_options_from_call(
        self, run_input: Any, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Recover ``runtime_options`` from a :meth:`run` call, positional or keyword.

        ``run()`` forwards ``*args`` / ``**kwargs`` verbatim to :meth:`submit`, where
        ``runtime_options`` is the fourth parameter, so it can legitimately arrive
        either way. Reading only ``kwargs`` would silently ignore a positional one --
        exactly the silent drop this class of bug is about. Binding against
        ``submit``'s own signature keeps the two in step if it ever changes.
        """
        try:
            bound = inspect.signature(self.submit).bind_partial(run_input, *args, **kwargs)
        except TypeError:
            # Mismatched arguments; let super().run() -> submit() raise the real error.
            return kwargs.get("runtime_options")
        return bound.arguments.get("runtime_options")

    def live_qubits(self) -> list[int]:
        """
        Returns a list of live qubit IDs for the device.
        """
        try:
            isa = get_instruction_set_architecture(
                quantum_processor_id=self.id,
                client=self._qcs_client,
            )
            return [node.node_id for node in isa.architecture.nodes]
        except GetISAError as e:
            raise RigettiDeviceError(
                f"Failed to retrieve ISA for quantum processor '{self.id}'."
            ) from e
