# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
import math

from chaosmap.rk4 import integrate


def _decay(t, y):
    return [-y[0]]


def _err(dt):
    n = round(1.0 / dt)
    _, y = integrate(_decay, [1.0], 0.0, dt, n)[-1]
    return abs(y[0] - math.exp(-1.0))


def test_orden_cuatro():
    # Al reducir dt a la mitad, el error debe dividirse por ~2^4 = 16.
    ratio = _err(0.1) / _err(0.05)
    assert 14.0 < ratio < 18.0


def test_determinismo():
    a = integrate(_decay, [1.0], 0.0, 0.01, 100)
    b = integrate(_decay, [1.0], 0.0, 0.01, 100)
    assert a == b
