# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
"""Estimación del exponente máximo de Lyapunov (método de Benettin).

Es una ESTIMACIÓN en tiempo finito, no una cota ni un valor exacto: depende
de dt, de delta0, del intervalo de renormalización y de la longitud de la
trayectoria. El error típico decrece como 1/T."""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .rk4 import Deriv, step


@dataclass(frozen=True)
class LyapunovResult:
    exponent: float
    series: list[tuple[float, float]]  # (t, estimación acumulada)


def max_lyapunov(
    f: Deriv,
    y0: Sequence[float],
    dt: float,
    n_steps: int,
    renorm_every: int = 10,
    delta0: float = 1e-8,
    transient_steps: int = 0,
) -> LyapunovResult:
    """Integra una trayectoria de referencia y otra perturbada una distancia
    delta0 (dirección (1,...,1)/sqrt(d)); cada `renorm_every` pasos acumula
    ln(d/delta0) y devuelve la perturbación a delta0.

    `transient_steps` avanza antes de medir, para caer sobre el atractor."""
    if renorm_every < 1 or n_steps < renorm_every:
        raise ValueError("n_steps debe ser >= renorm_every >= 1")
    dim = len(y0)
    y = list(y0)
    for i in range(transient_steps):
        y = step(f, i * dt, y, dt)
    t0 = transient_steps * dt
    e = delta0 / math.sqrt(dim)
    z = [v + e for v in y]
    total = 0.0
    series: list[tuple[float, float]] = []
    n_blocks = n_steps // renorm_every
    for b in range(n_blocks):
        for j in range(renorm_every):
            t = t0 + (b * renorm_every + j) * dt
            y = step(f, t, y, dt)
            z = step(f, t, z, dt)
        d = math.sqrt(sum((a - c) ** 2 for a, c in zip(z, y)))
        total += math.log(d / delta0)
        z = [yi + (zi - yi) * (delta0 / d) for yi, zi in zip(y, z)]
        elapsed = (b + 1) * renorm_every * dt
        series.append((elapsed, total / elapsed))
    return LyapunovResult(exponent=series[-1][1], series=series)
