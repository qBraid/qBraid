# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=too-many-arguments

"""
Plot atomic register of AHS program.

"""
from typing import Optional

import matplotlib.pyplot as plt


def plot_atomic_register(
    sites: list[tuple[float, float]],
    filling: list[bool],
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    save_path: Optional[str] = None,
    show: bool = True,
) -> None:
    """
    Plots atomic register given site coordinates and filling.

    Args:
        sites (list[tuple[float, float]]):list of tuples represents (x, y) coordinates.
        filling (list[bool]): A list of booleans indicating the filling status at each site.
        title (Optional[str]): The title of the plot. Defaults to "Atomic Register".
        xlabel (Optional[str]): The label for the x-axis. Defaults to "X (meters)".
        ylabel (Optional[str]): The label for the y-axis. Defaults to "Y (meters)".
        save_path (Optional[str]): Path to save plot. Plot is not saved unless specified.
        show (bool): If True, display the figure. Defaults to True.

    """
    if not len(sites) == len(filling):
        raise ValueError("sites and filling must be of equal length.")

    xData = [x[0] for x in sites]
    yData = [x[1] for x in sites]

    plt.figure(figsize=(10, 10))
    facecolors = ["purple" if fill else "none" for fill in filling]
    plt.scatter(xData, yData, edgecolors="pink", facecolors=facecolors, s=100, zorder=5)

    plt.scatter([], [], edgecolor="pink", label="Atom", s=100, facecolors="purple")
    plt.scatter([], [], edgecolor="pink", label="No Atom", s=100, facecolors="none")

    plt.legend(loc="upper left")

    if title:
        plt.title(title, fontsize=16)
    if xlabel:
        plt.xlabel(xlabel, fontsize=14)
    if ylabel:
        plt.ylabel(ylabel, fontsize=14)

    plt.grid(False)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)

    if show:
        plt.show()
