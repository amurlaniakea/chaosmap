# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
import subprocess
import sys

import pytest

from chaosmap import __version__
from chaosmap.cli import main


def _salida(capsys):
    return capsys.readouterr().out


def test_version(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert __version__ in _salida(capsys)


def test_run_csv(capsys):
    assert main(["run", "lorenz", "--steps", "3", "--dt", "0.01"]) == 0
    lineas = _salida(capsys).splitlines()
    assert lineas[0] == "t,x,y,z"
    assert len(lineas) == 5  # cabecera + 4 puntos
    assert lineas[1] == "0.0,1.0,1.0,1.0"


def test_run_every_y_y0(capsys):
    main(["run", "double_pendulum", "--steps", "10", "--every", "5", "--y0", "0.1,0.2,0,0"])
    lineas = _salida(capsys).splitlines()
    assert lineas[0] == "t,theta1,theta2,omega1,omega2"
    assert len(lineas) == 1 + 3  # pasos 0, 5, 10
    assert lineas[1].startswith("0.0,0.1,0.2,0.0,0.0")


def test_run_determinista(capsys):
    main(["run", "cr3bp", "--steps", "50"])
    a = _salida(capsys)
    main(["run", "cr3bp", "--steps", "50"])
    assert a == _salida(capsys)


@pytest.mark.parametrize("args", [
    ["run", "lorenz", "--y0", "1,2"],
    ["run", "lorenz", "--y0", "a,b,c"],
    ["run", "lorenz", "--every", "0"],
    ["lyapunov", "lorenz", "--steps", "5", "--renorm", "10"],
    ["svg", "no_existe", "--out", "x"],
    ["run", "no_existe"],
])
def test_errores_de_uso(args):
    with pytest.raises(SystemExit) as e:
        main(args)
    assert e.value.code == 2


def test_lyapunov_salida(capsys):
    assert main(["lyapunov", "lorenz", "--steps", "2000", "--transient", "0"]) == 0
    s = _salida(capsys)
    assert "estimación" in s and "exponente máximo" in s
    valor = float(s.split("Benettin): ")[1].split()[0])
    assert 0.0 < valor < 3.0


def test_svg_verify_y_deteccion_de_manipulacion(tmp_path, capsys):
    assert main(["svg", "--out", str(tmp_path)]) == 0
    assert len(_salida(capsys).splitlines()) == 4  # 3 hashes + manifiesto
    assert main(["verify", str(tmp_path)]) == 0
    assert "OK" in _salida(capsys)
    f = tmp_path / "lorenz_x_z.svg"
    f.write_bytes(f.read_bytes() + b"\n")
    assert main(["verify", str(tmp_path)]) == 1
    assert "FALLO" in _salida(capsys)


def test_svg_una_figura_no_escribe_manifiesto(tmp_path, capsys):
    assert main(["svg", "lorenz_x_z", "--out", str(tmp_path)]) == 0
    assert [p.name for p in tmp_path.iterdir()] == ["lorenz_x_z.svg"]
    assert _salida(capsys).strip().endswith("lorenz_x_z.svg")


def test_python_m_chaosmap():
    r = subprocess.run([sys.executable, "-m", "chaosmap", "--version"], capture_output=True, text=True)
    assert r.returncode == 0 and __version__ in r.stdout
