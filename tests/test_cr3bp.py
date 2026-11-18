# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
from chaosmap.rk4 import integrate
from chaosmap.systems import cr3bp as c


def test_puntos_de_lagrange_son_equilibrios():
    for x, y in c.lagrange_points().values():
        assert all(abs(v) < 1e-12 for v in c.deriv(0.0, [x, y, 0.0, 0.0]))


def test_puntos_colineales_tierra_luna():
    pts = c.lagrange_points()
    assert abs(pts["L1"][0] - 0.83692) < 1e-4
    assert abs(pts["L2"][0] - 1.15568) < 1e-4
    assert abs(pts["L3"][0] + 1.00506) < 1e-4


def test_jacobi_en_L4():
    # Valor analítico en los puntos triangulares: C = 3 - mu (1 - mu).
    mu = c.DEFAULT.mu
    x, y = c.lagrange_points()["L4"]
    assert abs(c.jacobi([x, y, 0.0, 0.0]) - (3.0 - mu * (1.0 - mu))) < 1e-12


def _arenstorf(n):
    pa = c.Params(mu=c.ARENSTORF_MU)
    y0 = list(c.ARENSTORF_Y0)
    dt = c.ARENSTORF_T / n  # n pasos exactos por periodo
    tray = integrate(lambda t, y: c.deriv(t, y, pa), y0, 0.0, dt, n)
    cierre = max(abs(a - b) for a, b in zip(tray[-1][1], y0))
    j0 = c.jacobi(y0, pa)
    deriva = max(abs(c.jacobi(s, pa) - j0) for _, s in tray)
    return cierre, deriva


def test_orbita_de_arenstorf_cierra_y_conserva_jacobi():
    cierre_a, _ = _arenstorf(50000)
    cierre_b, deriva_b = _arenstorf(100000)
    assert cierre_b < 2e-3  # medido: ~5.3e-4
    assert deriva_b < 5e-7  # medido: ~8.8e-8
    # Orden 4: al duplicar los pasos el error cae ~16x (medido: ~17).
    assert 10.0 < cierre_a / cierre_b < 25.0


def test_determinismo():
    y0 = list(c.ARENSTORF_Y0)
    a = integrate(c.deriv, y0, 0.0, 0.001, 500)
    assert a == integrate(c.deriv, y0, 0.0, 0.001, 500)
