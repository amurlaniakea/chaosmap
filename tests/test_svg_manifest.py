# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
import json
from pathlib import Path

import pytest

from chaosmap import figures, manifest, svg

FIGURAS_DIR = Path(__file__).resolve().parent.parent / "figures"


@pytest.fixture(scope="module")
def svgs():
    return {s.id: figures.generate_svg(s) for s in figures.FIGURES}


def test_formato_de_coordenadas():
    assert svg._fmt(-0.0001) == "0.00"  # sin "-0.00"
    assert svg._fmt(1.005) in ("1.00", "1.01")
    assert svg._fmt(12.3456) == "12.35"


def test_svg_dorado_minimo():
    s = svg.render_svg([(0.0, 0.0), (1.0, 1.0)], (0.0, 1.0, 0.0, 1.0), "T", "x", "y")
    assert 'points="60.00,430.00 620.00,40.00"' in s
    assert s.startswith("<svg ") and s.endswith("</svg>\n")


def test_escape_del_titulo():
    s = svg.render_svg([(0.0, 0.0)], (0.0, 1.0, 0.0, 1.0), 'a<b&"c"', "x", "y")
    assert "a<b" not in s and "a&lt;b&amp;" in s


@pytest.mark.parametrize("spec", figures.FIGURES, ids=lambda s: s.id)
def test_trayectoria_dentro_de_la_vista(spec):
    # Auditoría de la ventana fija: ningún punto queda fuera.
    xmin, xmax, ymin, ymax = spec.view
    for x, y in figures.trajectory_points(spec):
        assert xmin <= x <= xmax and ymin <= y <= ymax


def test_determinismo(svgs):
    for s in figures.FIGURES:
        assert figures.generate_svg(s) == svgs[s.id]


def test_robustez_ante_perturbacion_de_ulps(svgs):
    # Perturbar el estado inicial ~ unos ulps (1e-15) simula diferencias de
    # libm entre plataformas: el hash no debe cambiar (el redondeo del SVG
    # absorbe el error amplificado dentro de los horizontes acotados).
    for s in figures.FIGURES:
        y0 = list(s.y0)
        y0[0] += 1e-15
        assert svg.sha256_hex(figures.generate_svg(s, y0)) == svg.sha256_hex(svgs[s.id])


def test_manifiesto_build_y_verify(tmp_path):
    man = manifest.build(tmp_path)
    assert [e["id"] for e in man["figures"]] == [s.id for s in figures.FIGURES]
    assert manifest.verify(tmp_path) == []
    crudo = (tmp_path / "manifest.json").read_text(encoding="utf-8")
    assert crudo.endswith("\n") and json.loads(crudo) == man


def test_verify_detecta_svg_alterado(tmp_path):
    manifest.build(tmp_path)
    f = tmp_path / "lorenz_x_z.svg"
    f.write_bytes(f.read_bytes() + b" ")
    problemas = manifest.verify(tmp_path)
    assert any("lorenz_x_z" in p and "integridad" in p for p in problemas)


def test_verify_detecta_hash_manipulado_y_archivo_ausente(tmp_path):
    manifest.build(tmp_path)
    ruta = tmp_path / "manifest.json"
    man = json.loads(ruta.read_text(encoding="utf-8"))
    man["figures"][0]["sha256"] = "0" * 64
    ruta.write_text(json.dumps(man), encoding="utf-8")
    (tmp_path / "lorenz_x_z.svg").unlink()
    problemas = manifest.verify(tmp_path)
    assert any("reproducibilidad" in p for p in problemas)
    assert any("falta lorenz_x_z.svg" in p for p in problemas)


def test_verify_sin_manifiesto(tmp_path):
    assert manifest.verify(tmp_path) == ["falta manifest.json"]


def test_figuras_oficiales_del_repo_verifican():
    # Comprobación entre plataformas: los SVG y hashes versionados en
    # figures/ deben reproducirse bit a bit en esta máquina.
    assert manifest.verify(FIGURAS_DIR) == []
