#!/usr/bin/env python3
"""Generates one badge per technology. Usage: python tools/build_stack.py <font-dir>

Logos come from tools/stack_icons.json (Simple Icons, CC0). The text becomes vector paths,
so a badge needs no web font. To change the list, edit STACK and README.md.
"""
import json
import pathlib
import sys

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FONTS = pathlib.Path(sys.argv[1])
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "stack"
ICONS = json.loads((ROOT / "tools" / "stack_icons.json").read_text(encoding="utf8"))
MONO = instancer.instantiateVariableFont(TTFont(FONTS / "JetBrainsMono[wght].ttf"), {"wght": 500})

STACK = {"python": "Python", "typescript": "TypeScript", "langgraph": "LangGraph", "langchain": "LangChain", "modelcontextprotocol": "MCP", "langfuse": "Langfuse", "qdrant": "Qdrant", "neo4j": "Neo4j", "fastapi": "FastAPI", "nodedotjs": "Node.js", "postgresql": "PostgreSQL", "mongodb": "MongoDB", "redis": "Redis", "rabbitmq": "RabbitMQ", "apachespark": "Apache Spark", "react": "React", "nextdotjs": "Next.js", "docker": "Docker", "kubernetes": "Kubernetes", "amazonwebservices": "AWS", "prometheus": "Prometheus", "grafana": "Grafana"}
HEIGHT, ICON, PAD, GAP, SIZE = 34, 18, 11, 8, 13


def readable(color):
    """Lightens very dark brand colors so the logo stays visible on the dark badge."""
    r, g, b = (int(color[i:i + 2], 16) for i in (0, 2, 4))
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return f"#{color}" if luminance >= 70 else "#f5f7fa"


def badge(slug, label):
    glyphs, cmap, hmtx = MONO.getGlyphSet(), MONO.getBestCmap(), MONO["hmtx"]
    scale = SIZE / MONO["head"].unitsPerEm
    x = PAD + ICON + GAP
    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    for char in label:
        name = cmap[ord(char)]
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, 22)))
        x += hmtx[name][0] * scale
    width = round(x + PAD)
    icon = ICONS[slug]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{HEIGHT}" viewBox="0 0 {width} {HEIGHT}" role="img" aria-label="{label}">
<title>{label}</title>
<rect x=".5" y=".5" width="{width - 1}" height="{HEIGHT - 1}" rx="6" fill="#0a0d12" stroke="#2b323b"/>
<svg x="{PAD}" y="{(HEIGHT - ICON) / 2}" width="{ICON}" height="{ICON}" viewBox="0 0 24 24"><path fill="{readable(icon['hex'])}" fill-rule="{icon.get('rule', 'nonzero')}" d="{icon['path']}"/></svg>
<path fill="#f5f7fa" d="{pen.getCommands()}"/>
</svg>
"""


OUT.mkdir(parents=True, exist_ok=True)
for old in OUT.glob("*.svg"):
    old.unlink()
for slug, label in STACK.items():
    (OUT / f"{slug}.svg").write_text(badge(slug, label), encoding="utf8", newline="\n")
print(len(STACK), "badges")
