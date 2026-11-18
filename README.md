# chaosmap

Mapa de fases de sistemas caóticos deterministas, en **Python puro** (sin dependencias en el núcleo).

Integra con Runge-Kutta de orden 4 el **péndulo doble**, el **atractor de Lorenz** y el **problema restringido de tres cuerpos** (plano y circular), estima el **exponente de Lyapunov** y exporta **SVG deterministas con hash SHA-256** verificable.

**[Demo en vivo](https://amurlaniakea.github.io/chaosmap/)**: dos péndulos dobles idénticos, separados por 10⁻⁶ rad, que divergen ante tus ojos.

## Qué incluye

| Módulo | Qué hace |
|---|---|
| `rk4` | Integrador RK4 de paso fijo, tiempo calculado como `t0 + i·dt` (sin acumular error) |
| `systems/double_pendulum` | Péndulo doble con energía como invariante |
| `systems/lorenz` | Lorenz con puntos fijos |
| `systems/cr3bp` | CR3BP plano: puntos de Lagrange, constante de Jacobi, órbita de Arenstorf |
| `lyapunov` | Exponente máximo por el método de Benettin (estimación de tiempo finito) |
| `svg`, `figures`, `manifest` | SVG deterministas, figuras oficiales y manifiesto con SHA-256 |
| `cli` | `run`, `lyapunov`, `svg`, `verify` |
| `web/` | Demo estática (HTML, CSS y JavaScript, sin librerías ni red) |

## Instalación

```bash
git clone https://github.com/amurlaniakea/chaosmap.git
cd chaosmap
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

Requiere Python ≥ 3.10. El paquete no tiene dependencias en ejecución; `pytest` solo se usa para desarrollo.

## Uso

```bash
# Trayectoria en CSV (1 de cada 10 puntos)
chaosmap run lorenz --steps 10000 --every 10 > lorenz.csv

# Exponente máximo de Lyapunov (estimación)
chaosmap lyapunov lorenz

# Regenerar los SVG oficiales y el manifiesto
chaosmap svg --out figures

# Verificar integridad y reproducibilidad de las figuras
chaosmap verify
```

Sistemas: `double_pendulum`, `lorenz`, `cr3bp` (por defecto, la órbita de Arenstorf, que es la única validada). También funciona `python -m chaosmap`.

## Cómo se valida

Cada sistema se contrasta con algo conocido, no solo consigo mismo:

| Sistema | Comprobación | Resultado medido |
|---|---|---|
| RK4 | Error de `y' = -y` al reducir `dt` a la mitad | Se divide por ~16 (orden 4) |
| Péndulo doble | Deriva de energía, 10 s con `dt = 0,001` | 1,4·10⁻⁷ |
| Péndulo doble | Modo normal lineal: vuelve al estado inicial tras un periodo | Error ~10⁻⁹ |
| Lorenz | Puntos fijos: derivada nula | < 10⁻¹² |
| Lorenz | Exponente máximo, T = 1000 | 0,9041 (referencia: 0,9056) |
| Lyapunov | Valor analítico en el origen de Lorenz con ρ = 0,5 | −0,4769 frente a −0,4751 con T = 100 |
| CR3BP (Tierra–Luna) | L1, L2, L3 | 0,83692, 1,15568, −1,00506 |
| CR3BP | Constante de Jacobi en L4 frente a 3 − μ(1 − μ) | Coincide a 10⁻¹² |
| CR3BP | Órbita de Arenstorf tras un periodo, 100 000 pasos | Cierra con error 5·10⁻⁴; deriva de Jacobi 9·10⁻⁸ |
| CR3BP | Orden del integrador en esa órbita | El error de cierre cae ×17 al duplicar los pasos |

Los umbrales de los tests están fijados con margen sobre estos valores medidos.

## Determinismo y SVG con hash

Misma entrada, mismos bytes. Para que el hash sea estable:

- la ventana de vista de cada figura es **fija** (no depende de los datos);
- las coordenadas se escriben con **2 decimales** (0,01 px), con `-0.00` normalizado;
- no hay fechas, aleatoriedad ni metadatos variables, y la salida es UTF-8 con `\n`.

El caos amplifica los errores de coma flotante (por ejemplo, 1 ulp de la `libm` entre plataformas) como ~exp(λ·T). Por eso los SVG oficiales usan **horizontes acotados**: 8 s para el péndulo doble, t = 15 para Lorenz y un periodo para Arenstorf. Así el error amplificado queda muy por debajo del paso de redondeo. Un test perturba el estado inicial en 10⁻¹⁵ y comprueba que los hashes no cambian.

`chaosmap verify` hace dos comprobaciones por figura: **integridad** (el SVG en disco coincide con `figures/manifest.json`) y **reproducibilidad** (regenerarlo da el mismo hash).

**Evidencia entre entornos:** las figuras se generaron en un entorno Linux con Python 3.12.3 y se reprodujeron bit a bit en otro (Ubuntu 24.04 sobre WSL2, también Python 3.12.3). No se ha probado en macOS, Windows nativo ni otras versiones de Python. La garantía es probabilística: si un valor cayera justo en un límite de redondeo en otra plataforma, `verify` lo señalaría y habría que ajustar el horizonte.

## Demo web

`web/` es una página estática: dos péndulos dobles que difieren en δ de θ1, con estelas, una gráfica de la separación en escala logarítmica y control de condición inicial (caótica o regular), de δ (10⁻³ a 10⁻¹² rad) y de velocidad. Modo oscuro por defecto, con interruptor.

Para verla en local, abre `web/index.html` en el navegador. La demo integra en JavaScript con la misma física que el código Python (un test las compara con tolerancia 10⁻⁹ tras 2 s), pero **sus resultados no tienen hash oficial**: los hashes del repositorio cubren solo la salida de Python.

## Límites

- **Lyapunov es una estimación** de tiempo finito: depende de `dt`, `delta0` y T, y su sesgo decae como 1/T. No es una cota ni un valor exacto.
- RK4 de paso fijo **no conserva** energía ni la constante de Jacobi: la deriva está medida, no eliminada. Con encuentros cercanos (Arenstorf) el cierre exige que `dt` divida exactamente el periodo.
- El CR3BP es **plano y circular**; no hay paso adaptativo, N cuerpos general ni espectro completo de Lyapunov.
- Los ángulos del péndulo doble no se envuelven al dibujar el espacio de fases.

## Estructura

```
src/chaosmap/   rk4, lyapunov, svg, figures, manifest, cli, systems/
tests/          pruebas de cada módulo, de las figuras y de la demo web
figures/        SVG oficiales y manifest.json
web/            demo estática
```

## Licencia

Copyright (C) 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>

Licencia: [AGPL-3.0-or-later](LICENSE).
