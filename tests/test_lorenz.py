# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
from chaosmap.rk4 import integrate
from chaosmap.systems.lorenz import DEFAULT, Params, deriv, fixed_points


def test_puntos_fijos():
    pts = fixed_points()
    assert len(pts) == 3
    for pt in pts:
        assert all(abs(v) < 1e-12 for v in deriv(0.0, pt))


def test_solo_origen_si_rho_menor_que_uno():
    assert fixed_points(Params(rho=0.5)) == [[0.0, 0.0, 0.0]]


def test_decaimiento_al_origen_con_rho_menor_que_uno():
    p = Params(rho=0.5)
    tray = integrate(lambda t, y: deriv(t, y, p), [1.0, 1.0, 1.0], 0.0, 0.01, 3000)
    assert all(abs(v) < 1e-5 for v in tray[-1][1])  # medido: ~4e-7


def test_atractor_acotado():
    # Pasado el transitorio (t >= 5), la órbita queda en una región acotada.
    tray = integrate(deriv, [1.0, 1.0, 1.0], 0.0, 0.01, 10000)  # t = 100
    for _, (x, _y, z) in tray[500:]:
        assert abs(x) < 25.0 and 0.0 < z < 50.0  # medido: |x|<18.5, z en [4.5, 45.6]


def test_sensibilidad_a_condiciones_iniciales():
    a = integrate(deriv, [1.0, 1.0, 1.0], 0.0, 0.01, 3000)
    b = integrate(deriv, [1.0 + 1e-6, 1.0, 1.0], 0.0, 0.01, 3000)
    sep = lambda k: abs(a[k][1][0] - b[k][1][0])
    assert sep(1000) < 1e-4  # t = 10 s (medido: ~6e-7)
    assert sep(3000) > 1.0  # t = 30 s (medido: ~26)


def test_determinismo():
    y0 = [1.0, 1.0, 1.0]
    assert integrate(deriv, y0, 0.0, 0.01, 1000) == integrate(deriv, y0, 0.0, 0.01, 1000)


def test_parametros_por_defecto():
    assert (DEFAULT.sigma, DEFAULT.rho) == (10.0, 28.0)
    assert abs(DEFAULT.beta - 8.0 / 3.0) < 1e-15
