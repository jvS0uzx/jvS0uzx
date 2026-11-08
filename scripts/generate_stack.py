#!/usr/bin/env python3
import json
import os
import re
import urllib.request
from xml.sax.saxutils import escape as xml_escape

OUT_PATH = os.environ.get("OUT_PATH", "assets/tech-stack.svg")
SIMPLE_ICONS = "https://cdn.jsdelivr.net/npm/simple-icons@16.31.0"

CATEGORIES = [
    ("Linguagens e Frameworks", ["python", "django", "go", "typescript", "react", "nodedotjs"]),
    ("Dados e Infraestrutura", ["postgresql", "redis", "docker", "nginx", "githubactions", "amazonaws"]),
    ("Sistemas Operacionais", ["archlinux", "ubuntu", "fedora", "linux"]),
    ("Ferramentas", ["git", "postman", "notion", "obsidian", "telegram"]),
    ("IA e Assistentes", ["claudecode", "ollama"]),
]

# O AWS saiu do simple-icons na v12, a pedido da marca; o glifo vem da última versão que o tinha.
LEGACY_ICONS = {
    "amazonaws": ("AWS", "232F3E", "https://cdn.jsdelivr.net/npm/simple-icons@11.15.0/icons/amazonaws.svg"),
}

TILE = 56
TILE_RX = 16
GLYPH = 30
GAP = 14
LABEL_H = 30
ROW_GAP = 26
PAD_X = 20
PAD_TOP = 14
LABEL_COLOR = "#8b949e"


def fetch(url):
    with urllib.request.urlopen(url, timeout=20) as resp:
        return resp.read().decode("utf-8")


def luminance(hex_color):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def glyph_color(hex_color):
    white_contrast = 1.05 / (luminance(hex_color) + 0.05)
    return "#ffffff" if white_contrast >= 2.5 else "#0d1117"


def build_svg(icons):
    widest = max(len(slugs) for _, slugs in CATEGORIES)
    W = PAD_X * 2 + widest * TILE + (widest - 1) * GAP

    parts = []
    y = PAD_TOP
    for label, slugs in CATEGORIES:
        parts.append(f'<text x="{W / 2:.0f}" y="{y + 16}" class="label">{xml_escape(label)}</text>')
        row_w = len(slugs) * TILE + (len(slugs) - 1) * GAP
        x0 = (W - row_w) / 2
        tile_y = y + LABEL_H
        for i, slug in enumerate(slugs):
            title, hex_color, path = icons[slug]
            x = x0 + i * (TILE + GAP)
            offset = (TILE - GLYPH) / 2
            stroke = ' stroke="#ffffff" stroke-opacity="0.18"' if luminance(hex_color) < 0.02 else ""
            parts.append(
                f'<g class="wave" style="animation-delay:{i * 0.12:.2f}s">'
                f'<title>{xml_escape(title)}</title>'
                f'<rect x="{x:.0f}" y="{tile_y}" width="{TILE}" height="{TILE}" rx="{TILE_RX}" fill="#{hex_color}"{stroke}/>'
                f'<svg x="{x + offset:.0f}" y="{tile_y + offset:.0f}" width="{GLYPH}" height="{GLYPH}" viewBox="0 0 24 24">'
                f'<path d="{path}" fill="{glyph_color(hex_color)}"/></svg></g>'
            )
        y = tile_y + TILE + ROW_GAP

    H = y - ROW_GAP + PAD_TOP
    body = "\n  ".join(parts)
    return f'''<svg width="{W:.0f}" height="{H}" viewBox="0 0 {W:.0f} {H}" xmlns="http://www.w3.org/2000/svg" overflow="visible" role="img" aria-label="Tecnologias">
  <style>
    .label {{ font-family: 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 13px; font-weight: 600; letter-spacing: 0.6px; fill: {LABEL_COLOR}; text-anchor: middle; }}
    .wave {{ animation: wave 1.8s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
    @keyframes wave {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-6px); }} }}
  </style>
  {body}
</svg>
'''


def main():
    brands = {i["slug"]: i for i in json.loads(fetch(f"{SIMPLE_ICONS}/data/simple-icons.json"))}
    icons = {}
    for _, slugs in CATEGORIES:
        for slug in slugs:
            if slug in LEGACY_ICONS:
                title, hex_color, url = LEGACY_ICONS[slug]
            else:
                title, hex_color, url = brands[slug]["title"], brands[slug]["hex"], f"{SIMPLE_ICONS}/icons/{slug}.svg"
            path = re.search(r'<path d="([^"]+)"', fetch(url)).group(1)
            icons[slug] = (title, hex_color, path)

    os.makedirs(os.path.dirname(OUT_PATH) or ".", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(build_svg(icons))
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
