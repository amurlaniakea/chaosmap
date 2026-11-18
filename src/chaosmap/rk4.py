# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
"""Integrador Runge-Kutta de orden 4, paso fijo, solo biblioteca estándar."""

from collections.abc import Callable, Sequence

Deriv = Callable[[float, Sequence[float]], Sequence[float]]


def step(f: Deriv, t: float, y: Sequence[float], dt: float) -> list[float]:
    """Avanza un paso dt de y' = f(t, y)."""
    k1 = f(t, y)
    k2 = f(t + 0.5 * dt, [yi + 0.5 * dt * a for yi, a in zip(y, k1)])
    k3 = f(t + 0.5 * dt, [yi + 0.5 * dt * b for yi, b in zip(y, k2)])
    k4 = f(t + dt, [yi + dt * c for yi, c in zip(y, k3)])
    return [
        yi + (dt / 6.0) * (a + 2.0 * b + 2.0 * c + d)
        for yi, a, b, c, d in zip(y, k1, k2, k3, k4)
    ]


def integrate(
    f: Deriv, y0: Sequence[float], t0: float, dt: float, n: int
) -> list[tuple[float, list[float]]]:
    """Devuelve n+1 puntos (t, y). El tiempo se calcula como t0 + i*dt
    (sin acumular error) para mantener el determinismo."""
    y = list(y0)
    out = [(t0, y)]
    for i in range(n):
        y = step(f, t0 + i * dt, y, dt)
        out.append((t0 + (i + 1) * dt, y))
    return out
