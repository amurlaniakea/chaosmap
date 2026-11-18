# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
"""Problema restringido circular de tres cuerpos (CR3BP) plano.

Sistema rotante normalizado: distancia entre primarios = 1, n = 1,
masa total = 1. El primario mayor (1-mu) está en (-mu, 0) y el menor (mu)
en (1-mu, 0). Estado y = (x, y, vx, vy)."""

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Params:
    mu: float = 0.012150585609624  # Tierra-Luna


DEFAULT = Params()

# Órbita periódica clásica de Arenstorf (Hairer et al.), con su periodo.
ARENSTORF_MU = 0.012277471
ARENSTORF_Y0 = (0.994, 0.0, 0.0, -2.00158510637908252240537862224)
ARENSTORF_T = 17.0652165601579625588917206249


def _radios(x: float, y: float, mu: float) -> tuple[float, float]:
    r1 = math.sqrt((x + mu) ** 2 + y * y)
    r2 = math.sqrt((x - 1.0 + mu) ** 2 + y * y)
    return r1, r2


def deriv(t: float, y: Sequence[float], p: Params = DEFAULT) -> list[float]:
    x, yy, vx, vy = y
    mu = p.mu
    r1, r2 = _radios(x, yy, mu)
    c1 = (1.0 - mu) / (r1 * r1 * r1)
    c2 = mu / (r2 * r2 * r2)
    ax = 2.0 * vy + x - c1 * (x + mu) - c2 * (x - 1.0 + mu)
    ay = -2.0 * vx + yy - c1 * yy - c2 * yy
    return [vx, vy, ax, ay]


def jacobi(y: Sequence[float], p: Params = DEFAULT) -> float:
    """Constante de Jacobi C = 2*Omega - v^2 (invariante del sistema)."""
    x, yy, vx, vy = y
    r1, r2 = _radios(x, yy, p.mu)
    omega2 = x * x + yy * yy + 2.0 * (1.0 - p.mu) / r1 + 2.0 * p.mu / r2
    return omega2 - (vx * vx + vy * vy)


def _f_colineal(x: float, mu: float) -> float:
    return (
        x
        - (1.0 - mu) * (x + mu) / abs(x + mu) ** 3
        - mu * (x - 1.0 + mu) / abs(x - 1.0 + mu) ** 3
    )


def _biseccion(f, a: float, b: float) -> float:
    fa = f(a)
    for _ in range(200):
        m = 0.5 * (a + b)
        fm = f(m)
        if (fm > 0.0) == (fa > 0.0):
            a, fa = m, fm
        else:
            b = m
    return 0.5 * (a + b)


def lagrange_points(p: Params = DEFAULT) -> dict[str, tuple[float, float]]:
    """Los cinco puntos de equilibrio, por bisección (colineales) y
    forma cerrada (triangulares)."""
    mu = p.mu
    e = 1e-9
    f = lambda x: _f_colineal(x, mu)
    l1 = _biseccion(f, -mu + e, 1.0 - mu - e)
    l2 = _biseccion(f, 1.0 - mu + e, 2.0)
    l3 = _biseccion(f, -2.0, -mu - e)
    h = math.sqrt(3.0) / 2.0
    return {
        "L1": (l1, 0.0),
        "L2": (l2, 0.0),
        "L3": (l3, 0.0),
        "L4": (0.5 - mu, h),
        "L5": (0.5 - mu, -h),
    }
