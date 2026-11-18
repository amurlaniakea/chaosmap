# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
"""Atractor de Lorenz. Estado y = (x, y, z)."""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Params:
    sigma: float = 10.0
    rho: float = 28.0
    beta: float = 8.0 / 3.0


DEFAULT = Params()


def deriv(t: float, y: Sequence[float], p: Params = DEFAULT) -> list[float]:
    x, yy, z = y
    return [
        p.sigma * (yy - x),
        x * (p.rho - z) - yy,
        x * yy - p.beta * z,
    ]


def fixed_points(p: Params = DEFAULT) -> list[list[float]]:
    """Puntos fijos: el origen y, si rho > 1, los dos puntos C+ y C-."""
    pts = [[0.0, 0.0, 0.0]]
    if p.rho > 1.0:
        c = (p.beta * (p.rho - 1.0)) ** 0.5
        pts += [[c, c, p.rho - 1.0], [-c, -c, p.rho - 1.0]]
    return pts
