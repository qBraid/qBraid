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
Module for generating dictionary of all qiskit gates for testing/benchmarking

"""

import string
from typing import Optional

import numpy as np
from qiskit.circuit.library import standard_gates as sg
from qiskit.circuit.library.standard_gates import *  # noqa: F403

qiskit_gates = {
    "H": sg.h.HGate,
    "X": sg.x.XGate,
    "Y": sg.y.YGate,
    "Z": sg.z.ZGate,
    "S": sg.s.SGate,
    "Sdg": sg.s.SdgGate,
    "T": sg.t.TGate,
    "Tdg": sg.t.TdgGate,
    "I": sg.i.IGate,
    "SX": sg.sx.SXGate,
    "SXdg": sg.sx.SXdgGate,
    "Phase": sg.p.PhaseGate,
    "RX": sg.rx.RXGate,
    "RY": sg.ry.RYGate,
    "RZ": sg.rz.RZGate,
    "U1": sg.U1Gate,
    "R": sg.r.RGate,
    "U2": sg.u2.U2Gate,
    "U": sg.u.UGate,
    "U3": sg.u3.U3Gate,
    "CH": sg.h.CHGate,
    "CX": sg.x.CXGate,
    "Swap": sg.swap.SwapGate,
    "iSwap": sg.iswap.iSwapGate,
    "CSX": sg.sx.CSXGate,
    "DCX": sg.dcx.DCXGate,
    "CY": sg.y.CYGate,
    "CZ": sg.z.CZGate,
    "CPhase": sg.p.CPhaseGate,
    "CRX": sg.rx.CRXGate,
    "RXX": sg.rxx.RXXGate,
    "CRY": sg.ry.CRYGate,
    "RYY": sg.ryy.RYYGate,
    "CRZ": sg.rz.CRZGate,
    "RZX": sg.rzx.RZXGate,
    "RZZ": sg.rzz.RZZGate,
    "CU1": sg.u1.CU1Gate,
    "RCCX": sg.x.RCCXGate,
    "CCX": sg.x.CCXGate,
}


def generate_params(varnames: list[str], seed: Optional[int] = None):
    """Returns a dictionary of random parameters for a given list of variable names"""
    if seed is not None:
        np.random.seed(seed)
    params = {
        ra: np.random.rand() * 2 * np.pi
        for ra in ["theta", "phi", "lam", "gamma"]
        if ra in varnames
    }
    if "num_ctrl_qubits" in varnames:
        params["num_ctrl_qubits"] = np.random.randint(1, 7)
    if "phase" in varnames:
        params["phase"] = np.random.rand() * 2 * np.pi
    return params


def get_qiskit_gates(seed: Optional[int] = None, exclude: list[str] = []):
    """Returns a dictionary of all qiskit gates with random parameters"""
    qiskit_gates = {attr: None for attr in dir(sg) if attr[0] in string.ascii_uppercase}
    gate_varnames = {}
    gate_equivs = {"MCXGrayCode": "MCXGate"}
    for gate in qiskit_gates:
        varnames = [v for v in getattr(sg, gate).__init__.__code__.co_varnames if v != "self"]
        if set(varnames).issubset({"args", "kwargs"}):
            if gate in gate_equivs and gate_equivs[gate] in gate_varnames:
                varnames = gate_varnames[gate_equivs[gate]]
            else:
                continue
        elif gate == "MCXGate":
            gate_varnames[gate] = varnames
        params = generate_params(varnames, seed=seed)
        qiskit_gates[gate] = getattr(sg, gate)(**params)
    return {k: v for k, v in qiskit_gates.items() if v is not None and k not in exclude}
