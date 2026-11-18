// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
// Péndulo doble plano con RK4 de paso fijo. Estado y = [theta1, theta2, omega1, omega2].
// Las fórmulas y el orden de las operaciones reflejan src/chaosmap/systems/double_pendulum.py
// y src/chaosmap/rk4.py. Esta demo NO reproduce los hashes del repo (solo cubren la salida Python).
(function (root) {
  'use strict';

  var G = 9.81, M1 = 1.0, M2 = 1.0, L1 = 1.0, L2 = 1.0;

  function deriv(y) {
    var th1 = y[0], th2 = y[1], w1 = y[2], w2 = y[3];
    var d = th1 - th2;
    var sd = Math.sin(d), cd = Math.cos(d);
    var den = 2.0 * M1 + M2 - M2 * Math.cos(2.0 * d);
    var a1 = (
      -G * (2.0 * M1 + M2) * Math.sin(th1)
      - M2 * G * Math.sin(th1 - 2.0 * th2)
      - 2.0 * sd * M2 * (w2 * w2 * L2 + w1 * w1 * L1 * cd)
    ) / (L1 * den);
    var a2 = (
      2.0 * sd * (
        w1 * w1 * L1 * (M1 + M2)
        + G * (M1 + M2) * Math.cos(th1)
        + w2 * w2 * L2 * M2 * cd
      )
    ) / (L2 * den);
    return [w1, w2, a1, a2];
  }

  function step(y, dt) {
    var k1 = deriv(y);
    var k2 = deriv([y[0] + 0.5 * dt * k1[0], y[1] + 0.5 * dt * k1[1], y[2] + 0.5 * dt * k1[2], y[3] + 0.5 * dt * k1[3]]);
    var k3 = deriv([y[0] + 0.5 * dt * k2[0], y[1] + 0.5 * dt * k2[1], y[2] + 0.5 * dt * k2[2], y[3] + 0.5 * dt * k2[3]]);
    var k4 = deriv([y[0] + dt * k3[0], y[1] + dt * k3[1], y[2] + dt * k3[2], y[3] + dt * k3[3]]);
    var out = [0, 0, 0, 0];
    for (var i = 0; i < 4; i++) {
      out[i] = y[i] + (dt / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]);
    }
    return out;
  }

  function energy(y) {
    var th1 = y[0], th2 = y[1], w1 = y[2], w2 = y[3];
    var kin = 0.5 * M1 * Math.pow(L1 * w1, 2) + 0.5 * M2 * (
      Math.pow(L1 * w1, 2) + Math.pow(L2 * w2, 2) + 2.0 * L1 * L2 * w1 * w2 * Math.cos(th1 - th2)
    );
    var pot = -(M1 + M2) * G * L1 * Math.cos(th1) - M2 * G * L2 * Math.cos(th2);
    return kin + pot;
  }

  var api = { G: G, deriv: deriv, step: step, energy: energy };
  if (typeof module === 'object' && module.exports) { module.exports = api; } else { root.Pendulum = api; }
})(typeof globalThis !== 'undefined' ? globalThis : this);
