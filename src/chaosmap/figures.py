# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
"""Figuras oficiales: especificación fija de cada SVG con hash verificable.

Los horizontes de integración están acotados a propósito: el caos amplifica
~exp(lambda*T) los errores de coma flotante (p. ej. 1 ulp de la libm entre
plataformas). Con estos horizontes el error amplificado queda varios órdenes
de magnitud por debajo del paso de redondeo del SVG (0.01 px)."""

from collections.abc import Sequence
from dataclasses import dataclass

from . import svg
from .rk4 import integrate
from .systems import cr3bp, double_pendulum, lorenz


def _deriv_arenstorf(t, y):
    return cr3bp.deriv(t, y, cr3bp.Params(mu=cr3bp.ARENSTORF_MU))


_DERIVS = {
    "double_pendulum": double_pendulum.deriv,
    "lorenz": lorenz.deriv,
    "cr3bp_arenstorf": _deriv_arenstorf,
}


@dataclass(frozen=True)
class FigureSpec:
    id: str
    system: str
    title: str
    xlabel: str
    ylabel: str
    y0: tuple[float, ...]
    dt: float
    n_steps: int
    stride: int
    proj: tuple[int, int]
    view: svg.View


_N_ARENSTORF = 100000

FIGURES: tuple[FigureSpec, ...] = (
    FigureSpec(
        id="double_pendulum_theta1_omega1",
        system="double_pendulum",
        title="Péndulo doble: fase (θ1, ω1), t = 0 a 8 s",
        xlabel="θ1 (rad)",
        ylabel="ω1 (rad/s)",
        y0=(2.0, 2.5, 0.0, 0.0),
        dt=0.001,
        n_steps=8000,
        stride=4,
        proj=(0, 2),
        view=(-4.0, 9.0, -8.0, 11.0),
    ),
    FigureSpec(
        id="lorenz_x_z",
        system="lorenz",
        title="Atractor de Lorenz: proyección (x, z), t = 0 a 15",
        xlabel="x",
        ylabel="z",
        y0=(1.0, 1.0, 1.0),
        dt=0.01,
        n_steps=1500,
        stride=1,
        proj=(0, 2),
        view=(-20.0, 25.0, 0.0, 50.0),
    ),
    FigureSpec(
        id="cr3bp_arenstorf_x_y",
        system="cr3bp_arenstorf",
        title="CR3BP: órbita de Arenstorf (x, y), un periodo",
        xlabel="x",
        ylabel="y",
        y0=tuple(cr3bp.ARENSTORF_Y0),
        dt=cr3bp.ARENSTORF_T / _N_ARENSTORF,
        n_steps=_N_ARENSTORF,
        stride=50,
        proj=(0, 1),
        view=(-1.9, 1.6, -1.22, 1.22),
    ),
)

_POR_ID = {f.id: f for f in FIGURES}


def get(figure_id: str) -> FigureSpec:
    return _POR_ID[figure_id]


def trajectory_points(
    spec: FigureSpec, y0: Sequence[float] | None = None
) -> list[tuple[float, float]]:
    """Puntos (x, y) proyectados de la trayectoria, tomando 1 de cada `stride`."""
    tray = integrate(_DERIVS[spec.system], y0 if y0 is not None else spec.y0, 0.0, spec.dt, spec.n_steps)
    i, j = spec.proj
    return [(s[i], s[j]) for _, s in tray[:: spec.stride]]


def generate_svg(spec: FigureSpec, y0: Sequence[float] | None = None) -> str:
    pts = trajectory_points(spec, y0)
    return svg.render_svg(pts, spec.view, spec.title, spec.xlabel, spec.ylabel)
