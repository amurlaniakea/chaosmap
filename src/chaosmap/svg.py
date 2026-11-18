# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
"""Exportación determinista de mapas de fases a SVG y hash SHA-256.

Reglas de determinismo: ventana de vista FIJA (nunca derivada de los datos),
coordenadas con formato fijo de 2 decimales en píxeles, "-0.00" normalizado,
orden de atributos fijo, sin fechas ni metadatos variables, salida UTF-8 con
saltos de línea "\\n"."""

import hashlib
from collections.abc import Sequence
from xml.sax.saxutils import escape

WIDTH, HEIGHT = 640, 480
MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B = 60, 20, 40, 50
PLOT_W = WIDTH - MARGIN_L - MARGIN_R
PLOT_H = HEIGHT - MARGIN_T - MARGIN_B
DECIMALS = 2

View = tuple[float, float, float, float]  # xmin, xmax, ymin, ymax


def _fmt(v: float) -> str:
    s = f"{v:.{DECIMALS}f}"
    return "0." + "0" * DECIMALS if s == "-0." + "0" * DECIMALS else s


def to_pixels(x: float, y: float, view: View) -> tuple[float, float]:
    xmin, xmax, ymin, ymax = view
    px = MARGIN_L + (x - xmin) / (xmax - xmin) * PLOT_W
    py = MARGIN_T + (1.0 - (y - ymin) / (ymax - ymin)) * PLOT_H
    return px, py


def render_svg(
    points: Sequence[tuple[float, float]],
    view: View,
    title: str,
    xlabel: str,
    ylabel: str,
) -> str:
    xmin, xmax, ymin, ymax = view
    coords = " ".join(
        f"{_fmt(px)},{_fmt(py)}" for px, py in (to_pixels(x, y, view) for x, y in points)
    )
    t = escape(title)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" '
        f'role="img" aria-label="{escape(title, {chr(34): "&quot;"})}">',
        f"<title>{t}</title>",
        f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>',
        f'<rect x="{MARGIN_L}" y="{MARGIN_T}" width="{PLOT_W}" height="{PLOT_H}" '
        'fill="none" stroke="#999999" stroke-width="1"/>',
        f'<polyline fill="none" stroke="#1f77b4" stroke-width="0.6" '
        f'stroke-linejoin="round" points="{coords}"/>',
        f'<text x="{WIDTH // 2}" y="24" font-family="sans-serif" font-size="14" '
        f'text-anchor="middle">{t}</text>',
        f'<text x="{MARGIN_L + PLOT_W // 2}" y="{HEIGHT - 12}" font-family="sans-serif" '
        f'font-size="12" text-anchor="middle">{escape(xlabel)}</text>',
        f'<text x="14" y="{MARGIN_T + PLOT_H // 2}" font-family="sans-serif" '
        f'font-size="12" text-anchor="middle" '
        f'transform="rotate(-90 14 {MARGIN_T + PLOT_H // 2})">{escape(ylabel)}</text>',
        f'<text x="{MARGIN_L}" y="{MARGIN_T + PLOT_H + 14}" font-family="sans-serif" '
        f'font-size="10" text-anchor="start">{xmin:g}</text>',
        f'<text x="{MARGIN_L + PLOT_W}" y="{MARGIN_T + PLOT_H + 14}" '
        f'font-family="sans-serif" font-size="10" text-anchor="end">{xmax:g}</text>',
        f'<text x="{MARGIN_L - 6}" y="{MARGIN_T + PLOT_H}" font-family="sans-serif" '
        f'font-size="10" text-anchor="end">{ymin:g}</text>',
        f'<text x="{MARGIN_L - 6}" y="{MARGIN_T + 10}" font-family="sans-serif" '
        f'font-size="10" text-anchor="end">{ymax:g}</text>',
        "</svg>",
    ]
    return "\n".join(lines) + "\n"


def sha256_hex(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()
