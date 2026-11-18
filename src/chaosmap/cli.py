# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
"""Interfaz de línea de comandos de chaosmap (solo biblioteca estándar)."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__, figures, manifest, svg
from .lyapunov import max_lyapunov
from .rk4 import integrate
from .systems import cr3bp, double_pendulum, lorenz


def _arenstorf(t, y):
    return cr3bp.deriv(t, y, cr3bp.Params(mu=cr3bp.ARENSTORF_MU))


_N_ARENSTORF = 100000

# nombre -> (deriv, y0 por defecto, columnas, dt, pasos de `run`,
#            pasos de `lyapunov`, renormalización, transitorio)
SYSTEMS = {
    "double_pendulum": (
        double_pendulum.deriv, (2.0, 2.5, 0.0, 0.0),
        ("t", "theta1", "theta2", "omega1", "omega2"), 0.001, 10000, 50000, 100, 0,
    ),
    "lorenz": (
        lorenz.deriv, (1.0, 1.0, 1.0),
        ("t", "x", "y", "z"), 0.01, 10000, 100000, 10, 1000,
    ),
    # CR3BP: solo la órbita de Arenstorf está validada (cierra tras un periodo).
    "cr3bp": (
        _arenstorf, tuple(cr3bp.ARENSTORF_Y0),
        ("t", "x", "y", "vx", "vy"), cr3bp.ARENSTORF_T / _N_ARENSTORF,
        _N_ARENSTORF, _N_ARENSTORF, 100, 0,
    ),
}


def _y0(texto: str | None, por_defecto: tuple[float, ...], parser) -> list[float]:
    if texto is None:
        return list(por_defecto)
    try:
        y0 = [float(v) for v in texto.split(",")]
    except ValueError:
        parser.error(f"--y0 no es una lista de números separados por comas: {texto!r}")
    if len(y0) != len(por_defecto):
        parser.error(f"--y0 necesita {len(por_defecto)} valores, recibió {len(y0)}")
    return y0


def _cmd_run(a, parser) -> int:
    f, y0d, cols, dt0, n0, *_ = SYSTEMS[a.system]
    dt = a.dt if a.dt is not None else dt0
    n = a.steps if a.steps is not None else n0
    y0 = _y0(a.y0, y0d, parser)
    tray = integrate(f, y0, 0.0, dt, n)
    print(",".join(cols))
    for k in range(0, len(tray), a.every):
        t, y = tray[k]
        print(",".join(repr(v) for v in (t, *y)))
    return 0


def _cmd_lyapunov(a, parser) -> int:
    f, y0d, _c, dt0, _n, nl, renorm0, trans0 = SYSTEMS[a.system]
    dt = a.dt if a.dt is not None else dt0
    n = a.steps if a.steps is not None else nl
    renorm = a.renorm if a.renorm is not None else renorm0
    trans = a.transient if a.transient is not None else trans0
    y0 = _y0(a.y0, y0d, parser)
    try:
        r = max_lyapunov(f, y0, dt, n, renorm_every=renorm, delta0=a.delta0, transient_steps=trans)
    except ValueError as e:
        parser.error(str(e))
    print(f"sistema: {a.system}")
    print(f"exponente máximo de Lyapunov (estimación de tiempo finito, Benettin): {r.exponent:.4f}")
    print(
        f"T = {n * dt:g}, dt = {dt:g}, renormalización cada {renorm} pasos, "
        f"delta0 = {a.delta0:g}, transitorio = {trans} pasos"
    )
    print("Es una estimación: depende de dt, delta0 y T (el sesgo decae como 1/T).")
    return 0


def _cmd_svg(a, parser) -> int:
    out = Path(a.out)
    if not a.ids:
        man = manifest.build(out)
        for e in man["figures"]:
            print(f"{e['sha256']}  {e['file']}")
        print(f"{manifest.MANIFEST_NAME} escrito en {out}")
        return 0
    specs = []
    for i in a.ids:
        try:
            specs.append(figures.get(i))
        except KeyError:
            parser.error(f"figura desconocida: {i!r} (disponibles: {', '.join(s.id for s in figures.FIGURES)})")
    out.mkdir(parents=True, exist_ok=True)
    for s in specs:
        texto = figures.generate_svg(s)
        (out / f"{s.id}.svg").write_bytes(texto.encode("utf-8"))
        print(f"{svg.sha256_hex(texto)}  {s.id}.svg")
    return 0


def _cmd_verify(a, parser) -> int:
    problemas = manifest.verify(Path(a.dir))
    if problemas:
        for p in problemas:
            print(f"FALLO: {p}")
        return 1
    print(f"OK: {len(figures.FIGURES)} figuras verificadas (integridad y reproducibilidad)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="chaosmap",
        description="Mapa de fases de sistemas caóticos deterministas (RK4 en Python puro).",
    )
    p.add_argument("--version", action="version", version=f"chaosmap {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    nombres = sorted(SYSTEMS)

    r = sub.add_parser("run", help="integra un sistema y escribe la trayectoria en CSV")
    r.add_argument("system", choices=nombres)
    r.add_argument("--dt", type=float)
    r.add_argument("--steps", type=int)
    r.add_argument("--y0", help="estado inicial separado por comas")
    r.add_argument("--every", type=int, default=1, help="escribe 1 de cada N puntos")
    r.set_defaults(func=_cmd_run)

    ly = sub.add_parser("lyapunov", help="estima el exponente máximo de Lyapunov")
    ly.add_argument("system", choices=nombres)
    ly.add_argument("--dt", type=float)
    ly.add_argument("--steps", type=int)
    ly.add_argument("--y0")
    ly.add_argument("--renorm", type=int, help="pasos entre renormalizaciones")
    ly.add_argument("--delta0", type=float, default=1e-8)
    ly.add_argument("--transient", type=int, help="pasos previos sin medir")
    ly.set_defaults(func=_cmd_lyapunov)

    s = sub.add_parser("svg", help="genera los SVG oficiales (todos y manifiesto, o los ids dados)")
    s.add_argument("ids", nargs="*", metavar="FIGURA")
    s.add_argument("--out", required=True, help="directorio de salida")
    s.set_defaults(func=_cmd_svg)

    v = sub.add_parser("verify", help="verifica integridad y reproducibilidad de las figuras")
    v.add_argument("dir", nargs="?", default="figures")
    v.set_defaults(func=_cmd_verify)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    a = parser.parse_args(argv)
    if getattr(a, "every", 1) is not None and getattr(a, "every", 1) < 1:
        parser.error("--every debe ser >= 1")
    return a.func(a, parser)


if __name__ == "__main__":
    sys.exit(main())
