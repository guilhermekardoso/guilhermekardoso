#!/usr/bin/env python3
"""Generates the career trace. Usage: python tools/build_assets.py <font-dir>

All text becomes vector paths, so the SVG needs no web font and no foreignObject.
Fonts (OFL, from google/fonts): InterTight[wght].ttf, Inter[opsz,wght].ttf,
JetBrainsMono[wght].ttf. To update the career, edit SPANS and run this again.
"""
import pathlib
import sys

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FONTS = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)

BG, LINE, PANEL, TRACK = "#0a0d12", "#2b323b", "#141a22", "#12171e"
WHITE, TEXT, MUTED, SOFT = "#f5f7fa", "#c7ced6", "#a3adb9", "#b4bdc8"
DATA, FULL, ML, AI, LIVE = "#8f9db5", "#e9c46a", "#57c7d4", "#ff8a65", "#7ee2a8"

START = 2019 * 12 + 2  # March 2019
NOW = 2026 * 12 + 10  # November 2026
YEARS = range(2020, 2027)


def month(year, number):
    return year * 12 + number - 1


# Newest first: name, short and long description, start, end, color. Source: kardoso.dev/experiencias
SPANS = [
    ("trinks", "agentes no WhatsApp", "agentes no WhatsApp", month(2025, 11), month(2026, 3), AI),
    ("tce-ro", "LIDIA", "LIDIA, análise de editais", month(2025, 3), month(2025, 11), AI),
    ("ids-software", "GraphRAG", "GraphRAG na saúde", month(2024, 9), month(2025, 3), AI),
    ("datarisk", "MLOps", "plataforma de MLOps", month(2023, 7), month(2024, 9), ML),
    ("eemovel.ml", "modelos e AWS", "modelos e pipelines AWS", month(2022, 3), month(2023, 7), ML),
    ("ressoar", "2 mil+ usuários", "plataforma, 2 mil+ usuários", month(2020, 3), month(2022, 3), FULL),
    ("eemovel.dados", "18 mi+ registros", "18 mi+ registros, OCR", month(2019, 3), month(2020, 2), DATA),
]
ROTTUS_START = month(2026, 4)
DETAILS = [("produto", "Rottus Cargas"), ("entrada", "mensagens e áudios no WhatsApp"),
           ("saída", "status, alertas e relatórios"), ("próximo", "Rottus Barber")]
LEGEND = [("dados", DATA), ("full-stack", FULL), ("ML", ML), ("IA aplicada", AI)]


def variable(name, **axes):
    return instancer.instantiateVariableFont(TTFont(FONTS / name), axes)


TIGHT = variable("InterTight[wght].ttf", wght=700)
SANS = variable("Inter[opsz,wght].ttf", wght=400, opsz=14)
MONO = variable("JetBrainsMono[wght].ttf", wght=400)
MONO_B = variable("JetBrainsMono[wght].ttf", wght=600)


def width(text, font, size, track=0):
    cmap, hmtx = font.getBestCmap(), font["hmtx"]
    scale = size / font["head"].unitsPerEm
    return sum(hmtx[cmap[ord(c)]][0] * scale + track for c in text) - track


def text(content, font, size, x, y, fill, track=0, anchor="start"):
    glyphs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
    scale = size / font["head"].unitsPerEm
    if anchor == "end":
        x -= width(content, font, size, track)
    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    for char in content:
        name = cmap[ord(char)]
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
        x += hmtx[name][0] * scale + track
    return f'<path fill="{fill}" d="{pen.getCommands()}"/>'


def bar(x, y, w, h, color, order):
    return f'<rect class="s" style="animation-delay:{order * 0.22 + 0.15:.2f}s" x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" fill="{color}"/>'


def live_bar(x, y, w, h):
    return bar(x, y, w, h, AI, 0) + f'<rect class="l" x="{x + w - 5:.1f}" y="{y}" width="5" height="{h}" fill="#fff"/>'


def page(w, h, title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{title}">
<title>{title}</title>
<style>
.s{{transform-box:fill-box;transform-origin:left center;animation:g .6s cubic-bezier(.2,.7,.2,1) both}}
@keyframes g{{from{{transform:scaleX(0)}}}}
.l{{animation:p 1.4s ease-in-out 6}}
@keyframes p{{50%{{opacity:.2}}}}
@media (prefers-reduced-motion:reduce){{.s,.l{{animation:none}}}}
</style>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="8" fill="{BG}" stroke="{LINE}"/>
{body}
</svg>
"""


TITLE = "Guilherme Cardoso, engenheiro de software e cofundador da Rottus: trajetória de 2019 até hoje em forma de trace"


def desktop():
    w, x0, tx, tw = 846, 32, 240, 552
    px = tw / (NOW - START)
    pos = lambda m: tx + (m - START) * px
    out = [
        text("Guilherme Cardoso", TIGHT, 54, x0 - 2, 78, WHITE, track=-1),
        text("Engenheiro de software e cofundador da Rottus. Construo IA para operações que não podem parar.", SANS, 16, x0, 112, SOFT),
        text("trace guilherme.carreira", MONO, 11, x0, 156, MUTED),
    ]
    for year in YEARS:
        out.append(text(str(year), MONO, 11, pos(month(year, 1)), 156, MUTED))
    y = 166
    out.append(f'<rect x="{x0}" y="{y}" width="782" height="110" fill="{PANEL}"/>')
    out += [text("rottus", MONO_B, 14, x0 + 12, y + 20, "#fff"), text("cofundador", MONO, 11, x0 + 12, y + 36, MUTED), text("em execução", MONO, 11, x0 + 74, y + 20, LIVE),
            f'<rect x="{tx}" y="{y + 14}" width="{tw}" height="18" fill="{TRACK}"/>']
    out.append(live_bar(pos(ROTTUS_START), y + 14, tx + tw - pos(ROTTUS_START), 18))
    for i, (key, value) in enumerate(DETAILS):
        dx, dy = x0 + 12 + (i % 2) * 391, y + 68 + (i // 2) * 22
        out += [text(key, MONO, 12, dx, dy, MUTED), text(value, MONO, 12, dx + width(key, MONO, 12) + 8, dy, TEXT)]
    y += 118
    for i, (name, _, long, start, end, color) in enumerate(SPANS):
        out += [text(name, MONO_B, 13, x0 + 12, y + 18, WHITE), text(long, MONO, 11, x0 + 12, y + 34, MUTED),
                f'<rect x="{tx}" y="{y + 13}" width="{tw}" height="16" fill="{TRACK}"/>',
                bar(pos(start), y + 13, (end - start) * px, 16, color, i + 1)]
        y += 42
    y += 22
    x = x0
    for label, color in LEGEND:
        out += [f'<rect x="{x}" y="{y - 9}" width="10" height="10" fill="{color}"/>', text(label, MONO, 11, x + 16, y, MUTED)]
        x += 16 + width(label, MONO, 11) + 18
    out.append(text("2019 a 2026, em escala", MONO, 11, x0 + 782, y, MUTED, anchor="end"))
    return page(w, y + 24, TITLE, "\n".join(out))


def narrow():
    w, x0, tw = 358, 24, 310
    px = tw / (NOW - START)
    pos = lambda m: x0 + (m - START) * px
    out = [
        text("Guilherme", TIGHT, 40, x0 - 1, 56, WHITE, track=-.5),
        text("Cardoso", TIGHT, 40, x0 - 1, 98, WHITE, track=-.5),
        text("Engenheiro de software e cofundador", SANS, 15, x0, 130, SOFT),
        text("da Rottus. Construo IA para operações", SANS, 15, x0, 151, SOFT),
        text("que não podem parar.", SANS, 15, x0, 172, SOFT),
    ]
    for year in (2019, 2022, 2026):
        out.append(text(str(year), MONO, 11, x0 + (max(month(year, 1), START) - START) * px, 204, MUTED))
    y = 214
    out.append(f'<rect x="{x0 - 8}" y="{y}" width="{tw + 16}" height="138" fill="{PANEL}"/>')
    out += [text("rottus", MONO_B, 13, x0, y + 17, "#fff"), text("em execução", MONO, 11, x0 + 56, y + 17, LIVE)]
    out.append(f'<rect x="{x0}" y="{y + 25}" width="{tw}" height="12" fill="{TRACK}"/>')
    out.append(live_bar(pos(ROTTUS_START), y + 25, x0 + tw - pos(ROTTUS_START), 12))
    short = [("produto", "Rottus Cargas"), ("entrada", "mensagens e áudios"), ("saída", "status, alertas, relatórios"), ("próximo", "Rottus Barber")]
    for i, (key, value) in enumerate(short):
        dy = y + 60 + i * 20
        out += [text(key, MONO, 12, x0, dy, MUTED), text(value, MONO, 12, x0 + width(key, MONO, 12) + 8, dy, TEXT)]
    y += 150
    for i, (name, short_text, _, start, end, color) in enumerate(SPANS):
        out += [text(name, MONO_B, 12, x0, y + 12, WHITE), text(short_text, MONO, 11, x0 + width(name, MONO_B, 12) + 8, y + 12, MUTED),
                f'<rect x="{x0}" y="{y + 18}" width="{tw}" height="12" fill="{TRACK}"/>',
                bar(pos(start), y + 18, (end - start) * px, 12, color, i + 1)]
        y += 40
    return page(w, y + 12, TITLE, "\n".join(out))


for old in OUT.glob("*.svg"):
    old.unlink()
for name, svg in (("trace.svg", desktop()), ("trace-narrow.svg", narrow())):
    (OUT / name).write_text(svg, encoding="utf8", newline="\n")
    print(name, len(svg) // 1024, "KB")
