# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from chaosmap.rk4 import integrate
from chaosmap.systems.double_pendulum import deriv, energy

WEB = Path(__file__).resolve().parent.parent / "web"
ARCHIVOS = ["index.html", "style.css", "pendulum.js", "app.js"]


@pytest.mark.parametrize("nombre", ARCHIVOS)
def test_cabecera_spdx_y_copyright(nombre):
    cabecera = (WEB / nombre).read_text(encoding="utf-8")[:400]
    assert "SPDX-License-Identifier: AGPL-3.0-or-later" in cabecera
    assert "Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>" in cabecera


def test_sin_recursos_externos():
    for nombre in ARCHIVOS:
        texto = (WEB / nombre).read_text(encoding="utf-8")
        assert not re.search(r"""(src|href)\s*=\s*["']?(https?:)?//""", texto), nombre
        assert "@import" not in texto and "url(http" not in texto, nombre


def test_js_sin_apis_peligrosas_ni_red():
    for nombre in ("pendulum.js", "app.js"):
        texto = (WEB / nombre).read_text(encoding="utf-8")
        for prohibido in ("eval(", "new Function", "fetch(", "XMLHttpRequest", "WebSocket",
                          "innerHTML", "document.write", "localStorage", "sessionStorage"):
            assert prohibido not in texto, f"{nombre}: {prohibido}"


def test_modo_oscuro_por_defecto_e_interruptor():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert '<html lang="es" data-theme="dark">' in html
    assert 'id="theme"' in html
    assert html.index('id="theme"') < html.index("<h1>")  # arriba a la izquierda


def test_scripts_locales_en_orden():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert html.index('src="pendulum.js"') < html.index('src="app.js"')


@pytest.mark.skipif(shutil.which("node") is None, reason="node no está instalado")
def test_js_coincide_con_python():
    # Misma física en JS y Python: tras 2 s (2000 pasos RK4) coinciden salvo
    # diferencias de libm (~1e-15 amplificadas); tolerancia 1e-9.
    guion = (
        "const P=require(process.argv[1]);let y=[2.0,2.5,0,0];"
        "for(let i=0;i<2000;i++)y=P.step(y,0.001);"
        "console.log(JSON.stringify({y:y,e:P.energy(y)}));"
    )
    r = subprocess.run(["node", "-e", guion, str(WEB / "pendulum.js")],
                       capture_output=True, text=True, check=True)
    js = json.loads(r.stdout)
    _, y_py = integrate(deriv, [2.0, 2.5, 0.0, 0.0], 0.0, 0.001, 2000)[-1]
    assert all(abs(a - b) < 1e-9 for a, b in zip(js["y"], y_py))
    assert abs(js["e"] - energy(y_py)) < 1e-9
