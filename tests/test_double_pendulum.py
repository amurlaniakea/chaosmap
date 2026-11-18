# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
import math

from chaosmap.rk4 import integrate
from chaosmap.systems.double_pendulum import DEFAULT, deriv, energy


def test_reposo_estable():
    # Colgando en equilibrio: aceleraciones nulas.
    assert deriv(0.0, [0.0, 0.0, 0.0, 0.0]) == [0.0, 0.0, 0.0, 0.0]


def test_deriva_de_energia():
    y0 = [2.0, 2.5, 0.0, 0.0]
    e0 = energy(y0)
    dt = 0.001
    tray = integrate(deriv, y0, 0.0, dt, 10000)  # t = 10 s
    deriva = max(abs(energy(y) - e0) for _, y in tray)
    assert deriva < 1e-6  # medido: ~1.4e-7


def test_modo_normal_lineal():
    # Con m1=m2, l1=l2, el modo lento tiene w^2 = (2 - sqrt(2)) g/l y
    # theta2/theta1 = sqrt(2). Tras un periodo el estado vuelve al inicial.
    w = math.sqrt((2.0 - math.sqrt(2.0)) * DEFAULT.g / DEFAULT.l1)
    periodo = 2.0 * math.pi / w
    a = 1e-3
    y0 = [a, math.sqrt(2.0) * a, 0.0, 0.0]
    n = 4000
    _, y = integrate(deriv, y0, 0.0, periodo / n, n)[-1]
    assert all(abs(u - v) < 1e-8 for u, v in zip(y, y0))  # medido: ~1e-9


def test_sensibilidad_a_condiciones_iniciales():
    y0 = [2.0, 2.5, 0.0, 0.0]
    y1 = [2.0 + 1e-6, 2.5, 0.0, 0.0]
    a = integrate(deriv, y0, 0.0, 0.001, 10000)
    b = integrate(deriv, y1, 0.0, 0.001, 10000)
    sep = lambda k: abs(a[k][1][0] - b[k][1][0])
    assert sep(2000) < 1e-4  # t = 2 s: aún cercanas (medido: ~3e-6)
    assert sep(10000) > 0.1  # t = 10 s: divergen (medido: ~4)


def test_determinismo():
    y0 = [2.0, 2.5, 0.0, 0.0]
    assert integrate(deriv, y0, 0.0, 0.001, 500) == integrate(deriv, y0, 0.0, 0.001, 500)
