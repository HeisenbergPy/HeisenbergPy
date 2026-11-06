"""Encabezado animado del perfil (encabezado.svg).

Toma la imagen fija del encabezado (encabezado.png, exportada de encabezado.html) y le superpone, en SVG, pulsos de luz
que recorren las curvas de nivel índice del panel oscuro (las mismas curvas del DEM de San Ramón que dibuja
recursos/marco.py del repositorio Prospectivity-for-U-REE-Peru-Central) y un brillo lento en la esquina morada.
GitHub muestra el SVG animado dentro del README; con «reducir movimiento» activado, queda fijo.

Uso, con el entorno del repositorio del proyecto:
    ..\\Geocomputacion_U_Peru_Central\\.venv\\Scripts\\python.exe diseno\\animar_encabezado.py
"""

import base64
import importlib.util
import io
import pathlib
import random

from PIL import Image
from shapely.geometry import LineString, Polygon, box

AQUI = pathlib.Path(__file__).resolve().parent
PERFIL = AQUI.parent
PROYECTO = PERFIL.parent / 'Geocomputacion_U_Peru_Central'
E = 2                                                     # la imagen fija está a resolución 2x
ANCHO, ALTO = 1600 * E, 400 * E
BORDE = [(720, -10), (760, 230), (735, 290), (800, 350), (1380, 390), (1610, 318)]   # el de marco_perfil.png
ESQUINA_X = 1380
TEXTO = box(100, 80, 1340, 560)                           # nombre y descripción (px 2x): sin pulsos encima


def curvas():
    spec = importlib.util.spec_from_file_location('marco', PROYECTO / 'recursos' / 'marco.py')
    marco = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(marco)
    return marco.curvas(ANCHO, ALTO), marco.INDICE


def main():
    random.seed(7)
    lineas, indice = curvas()
    oscuro = Polygon([(x * E, y * E) for x, y in BORDE] + [(ANCHO + 40, ALTO + 40), (-40, ALTO + 40), (-40, -40)])
    zona = oscuro.difference(TEXTO.buffer(30))
    '''Curvas largas dentro del panel oscuro (las índice primero), simplificadas para que el SVG pese poco'''
    elegidas = []
    for nivel, pts in lineas:
        if len(pts) < 2:
            continue
        linea = LineString(pts)
        if linea.intersection(zona).length < 360:              # recorrido visible fuera del texto
            continue
        elegidas.append((nivel % indice == 0, linea.simplify(1.2)))
    elegidas.sort(key=lambda t: (not t[0], -t[1].length))
    elegidas = [l for _, l in elegidas[:30]]

    rutas, usos = [], []
    for i, l in enumerate(elegidas):
        d = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in l.coords)
        rutas.append(f'<path id="c{i}" d="{d}" pathLength="1000"/>')
        dur = random.uniform(7, 13)
        retraso = -random.uniform(0, dur)
        tramo = random.choice([30, 40, 55])
        estilo = f'stroke-dasharray:{tramo} {1000 - tramo};animation-duration:{dur:.1f}s;animation-delay:{retraso:.1f}s'
        usos.append(f'<use href="#c{i}" class="brillo" style="{estilo}"/><use href="#c{i}" class="pulso" style="{estilo}"/>')

    '''Imagen fija incrustada (JPEG) para que el SVG sea un solo archivo'''
    buf = io.BytesIO()
    Image.open(PERFIL / 'encabezado.png').convert('RGB').save(buf, 'JPEG', quality=86, optimize=True, progressive=True)
    fondo = base64.b64encode(buf.getvalue()).decode()

    x0 = ESQUINA_X * E
    puntos_esquina = f'{x0},{ALTO} {x0},{(390 * E)} {1610 * E},{318 * E} {ANCHO},{ALTO}'
    anillos = [zona.exterior, *zona.interiors]
    contorno = ' '.join('M' + ' L'.join(f'{x:.0f} {y:.0f}' for x, y in a.coords) + ' Z' for a in anillos)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {ANCHO} {ALTO}" width="1600" height="400" role="img" aria-label="Carlos Manuel Gutiérrez Cruzado">
<style>
.brillo, .pulso {{ fill: none; stroke-linecap: round; animation-name: fluir; animation-timing-function: linear;
  animation-iteration-count: infinite; }}
.brillo {{ stroke: #b46cff; stroke-width: 9; opacity: 0.55; filter: url(#difuso); }}
.pulso {{ stroke: #f1e6ff; stroke-width: 2.6; opacity: 0.9; }}
@keyframes fluir {{ from {{ stroke-dashoffset: 1000; }} to {{ stroke-dashoffset: 0; }} }}
.esquina {{ fill: #e2c8ff; animation: respirar 6s ease-in-out infinite; }}
@keyframes respirar {{ 0%, 100% {{ opacity: 0; }} 50% {{ opacity: 0.22; }} }}
@media (prefers-reduced-motion: reduce) {{ .brillo, .pulso, .esquina {{ animation: none; opacity: 0; }} }}
</style>
<defs>
<filter id="difuso" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="6"/></filter>
<clipPath id="panel"><path clip-rule="evenodd" d="{contorno}"/></clipPath>
{''.join(rutas)}
</defs>
<image width="{ANCHO}" height="{ALTO}" href="data:image/jpeg;base64,{fondo}"/>
<g clip-path="url(#panel)">
{''.join(usos)}
</g>
<polygon class="esquina" points="{puntos_esquina}"/>
</svg>
'''
    salida = PERFIL / 'encabezado.svg'
    salida.write_text(svg, encoding='utf-8')
    print(f'{len(elegidas)} curvas animadas; {salida.stat().st_size / 1e6:.2f} MB')


if __name__ == '__main__':
    main()
