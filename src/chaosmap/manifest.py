# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
"""Manifiesto de figuras oficiales: generación y verificación."""

import json
from pathlib import Path

from . import figures, svg

MANIFEST_NAME = "manifest.json"
FORMAT = 1


def _entrada(spec: figures.FigureSpec, sha: str) -> dict:
    return {
        "id": spec.id,
        "file": f"{spec.id}.svg",
        "sha256": sha,
        "system": spec.system,
        "y0": list(spec.y0),
        "dt": spec.dt,
        "n_steps": spec.n_steps,
        "stride": spec.stride,
        "view": list(spec.view),
    }


def _escribir(path: Path, texto: str) -> None:
    path.write_bytes(texto.encode("utf-8"))  # sin conversión de saltos de línea


def build(out_dir: Path) -> dict:
    """Genera los SVG oficiales y el manifiesto en out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    entradas = []
    for spec in figures.FIGURES:
        texto = figures.generate_svg(spec)
        _escribir(out_dir / f"{spec.id}.svg", texto)
        entradas.append(_entrada(spec, svg.sha256_hex(texto)))
    manifiesto = {
        "format": FORMAT,
        "rounding_decimals": svg.DECIMALS,
        "figures": entradas,
    }
    _escribir(
        out_dir / MANIFEST_NAME,
        json.dumps(manifiesto, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    )
    return manifiesto


def verify(out_dir: Path) -> list[str]:
    """Devuelve la lista de problemas (vacía si todo cuadra).

    Comprueba dos cosas por figura: (a) integridad: el archivo SVG en disco
    tiene el hash del manifiesto; (b) reproducibilidad: regenerarlo aquí da
    ese mismo hash."""
    out_dir = Path(out_dir)
    ruta = out_dir / MANIFEST_NAME
    if not ruta.is_file():
        return [f"falta {MANIFEST_NAME}"]
    man = json.loads(ruta.read_text(encoding="utf-8"))
    problemas: list[str] = []
    if man.get("format") != FORMAT:
        problemas.append(f"formato de manifiesto no soportado: {man.get('format')!r}")
    for e in man.get("figures", []):
        fid = e.get("id")
        try:
            spec = figures.get(fid)
        except KeyError:
            problemas.append(f"{fid}: figura desconocida")
            continue
        archivo = out_dir / e["file"]
        if not archivo.is_file():
            problemas.append(f"{fid}: falta {e['file']}")
        elif svg.sha256_hex(archivo.read_bytes().decode("utf-8")) != e["sha256"]:
            problemas.append(f"{fid}: integridad: el SVG en disco no coincide con el manifiesto")
        regenerado = svg.sha256_hex(figures.generate_svg(spec))
        if regenerado != e["sha256"]:
            problemas.append(
                f"{fid}: reproducibilidad: regenerado {regenerado[:12]}… != manifiesto {e['sha256'][:12]}…"
            )
    conocidos = {e.get("id") for e in man.get("figures", [])}
    for spec in figures.FIGURES:
        if spec.id not in conocidos:
            problemas.append(f"{spec.id}: no figura en el manifiesto")
    return problemas
