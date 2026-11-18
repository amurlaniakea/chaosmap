# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
import math

import pytest

from chaosmap.lyapunov import max_lyapunov
from chaosmap.systems import double_pendulum as dp
from chaosmap.systems import lorenz

# Valor analítico: en el origen (rho = 0.5) el autovalor mayor del Jacobiano
# cumple l^2 + (sigma + 1) l + sigma (1 - rho) = 0.
_P05 = lorenz.Params(rho=0.5)
_ANALITICO = (-(_P05.sigma + 1.0) + math.sqrt((_P05.sigma + 1.0) ** 2 - 4.0 * _P05.sigma * (1.0 - _P05.rho))) / 2.0


def _f05(t, y):
    return lorenz.deriv(t, y, _P05)


def _error_origen(n_steps):
    r = max_lyapunov(_f05, [1e-3, 1e-3, 1e-3], 0.01, n_steps)
    return abs(r.exponent - _ANALITICO)


def test_valor_analitico_en_origen():
    assert _error_origen(10000) < 5e-3  # T = 100; medido: ~1.8e-3


def test_sesgo_de_tiempo_finito_decae_como_1_sobre_T():
    # Duplicar T debe reducir el error ~2x (medido: ~1.9x).
    razon = _error_origen(5000) / _error_origen(10000)
    assert 1.5 < razon < 2.5


def test_lorenz_valor_de_referencia():
    r = max_lyapunov(lorenz.deriv, [1.0, 1.0, 1.0], 0.01, 100000, transient_steps=1000)
    assert abs(r.exponent - 0.9056) < 0.02  # medido: 0.9041 (T = 1000)


def test_pendulo_doble_caotico_vs_regular():
    caotico = max_lyapunov(dp.deriv, [2.0, 2.5, 0.0, 0.0], 0.001, 50000, renorm_every=100)
    regular = max_lyapunov(dp.deriv, [0.05, 0.07, 0.0, 0.0], 0.001, 50000, renorm_every=100)
    assert caotico.exponent > 1.0  # medido: ~1.44
    assert abs(regular.exponent) < 0.02  # medido: ~-0.0045


def test_serie_y_determinismo():
    a = max_lyapunov(lorenz.deriv, [1.0, 1.0, 1.0], 0.01, 1000)
    b = max_lyapunov(lorenz.deriv, [1.0, 1.0, 1.0], 0.01, 1000)
    assert a == b
    assert a.series[-1][1] == a.exponent
    assert len(a.series) == 100


def test_parametros_invalidos():
    with pytest.raises(ValueError):
        max_lyapunov(lorenz.deriv, [1.0, 1.0, 1.0], 0.01, 5, renorm_every=10)
