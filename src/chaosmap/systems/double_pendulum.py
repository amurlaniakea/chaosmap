# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
"""Péndulo doble plano. Estado y = (theta1, theta2, omega1, omega2).

Los ángulos se miden desde la vertical hacia abajo (rad)."""

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Params:
    m1: float = 1.0
    m2: float = 1.0
    l1: float = 1.0
    l2: float = 1.0
    g: float = 9.81


DEFAULT = Params()


def deriv(t: float, y: Sequence[float], p: Params = DEFAULT) -> list[float]:
    th1, th2, w1, w2 = y
    d = th1 - th2
    sd, cd = math.sin(d), math.cos(d)
    den = 2.0 * p.m1 + p.m2 - p.m2 * math.cos(2.0 * d)
    a1 = (
        -p.g * (2.0 * p.m1 + p.m2) * math.sin(th1)
        - p.m2 * p.g * math.sin(th1 - 2.0 * th2)
        - 2.0 * sd * p.m2 * (w2 * w2 * p.l2 + w1 * w1 * p.l1 * cd)
    ) / (p.l1 * den)
    a2 = (
        2.0
        * sd
        * (
            w1 * w1 * p.l1 * (p.m1 + p.m2)
            + p.g * (p.m1 + p.m2) * math.cos(th1)
            + w2 * w2 * p.l2 * p.m2 * cd
        )
    ) / (p.l2 * den)
    return [w1, w2, a1, a2]


def energy(y: Sequence[float], p: Params = DEFAULT) -> float:
    """Energía mecánica total (invariante del sistema)."""
    th1, th2, w1, w2 = y
    kin = 0.5 * p.m1 * (p.l1 * w1) ** 2 + 0.5 * p.m2 * (
        (p.l1 * w1) ** 2
        + (p.l2 * w2) ** 2
        + 2.0 * p.l1 * p.l2 * w1 * w2 * math.cos(th1 - th2)
    )
    pot = -(p.m1 + p.m2) * p.g * p.l1 * math.cos(th1) - p.m2 * p.g * p.l2 * math.cos(th2)
    return kin + pot
