#!/usr/bin/env python3
import math
import os
from xml.sax.saxutils import escape as xml_escape

from PIL import Image

LOGIN = os.environ.get("GITHUB_LOGIN", "jvS0uzx")
SNORLAX_PATH = os.environ.get("SNORLAX_PATH", "assets/snorlax-back.png")
RAYQUAZA_PATH = os.environ.get("RAYQUAZA_PATH", "assets/rayquaza.png")
OUT_PATH = os.environ.get("OUT_PATH", "assets/battle.svg")

BG_COLOR = "#0b1120"
TITLEBAR_COLOR = "#141c30"
TITLE_TEXT_COLOR = "#7f8aa6"
INK = "#283040"
TEXT = "#383840"
TEXT_SHADOW = "#d0d0d8"
PAPER = "#f8f8f8"
FRAME = "#5dc9f2"
ACCENT = "#e8384f"

SCREEN_W = 256
SCREEN_H = 192
SCALE = 3
PAD = 24
TITLEBAR_H = 34

LOOP = 20.0
TYPE_SPEED = 0.035
HOLD = "steps(1, end)"

SNORLAX_POS = (14, 88)
SNORLAX_CENTER = (48, 30)
RAYQUAZA_POS = (146, 10)
RAYQUAZA_MOUTH = (40, 24)

MESSAGES = [
    (0.4, 3.9, ["UM RAYQUAZA SELVAGEM APARECEU!", "SNORLAX ESTÁ DORMINDO..."]),
    (3.9, 6.2, ["RAYQUAZA USOU HIPER RAIO!"]),
    (6.2, 8.6, ["NÃO FOI MUITO EFETIVO...", "SNORLAX PERDEU 1 HP."]),
    (8.6, 10.6, ["SNORLAX ACORDOU!", "E NÃO GOSTOU NADA DISSO."]),
    (10.6, 13.0, ["SNORLAX USOU MEGA PUSH!"]),
    (13.0, 15.3, ["UM GOLPE SÓ!", "RAYQUAZA SELVAGEM DESMAIOU!"]),
    (15.3, 18.8, ["SNORLAX VOLTOU A DORMIR..."]),
]

FONT = {
    "A": ".###. #...# #...# ##### #...# #...# #...#",
    "B": "####. #...# #...# ####. #...# #...# ####.",
    "C": ".###. #...# #.... #.... #.... #...# .###.",
    "D": "####. #...# #...# #...# #...# #...# ####.",
    "E": "##### #.... #.... ####. #.... #.... #####",
    "F": "##### #.... #.... ####. #.... #.... #....",
    "G": ".###. #...# #.... #.### #...# #...# .###.",
    "H": "#...# #...# #...# ##### #...# #...# #...#",
    "I": ".###. ..#.. ..#.. ..#.. ..#.. ..#.. .###.",
    "J": "..### ...#. ...#. ...#. ...#. #..#. .##..",
    "K": "#...# #..#. #.#.. ##... #.#.. #..#. #...#",
    "L": "#.... #.... #.... #.... #.... #.... #####",
    "M": "#...# ##.## #.#.# #.#.# #...# #...# #...#",
    "N": "#...# #...# ##..# #.#.# #..## #...# #...#",
    "O": ".###. #...# #...# #...# #...# #...# .###.",
    "P": "####. #...# #...# ####. #.... #.... #....",
    "Q": ".###. #...# #...# #...# #.#.# #..#. .##.#",
    "R": "####. #...# #...# ####. #.#.. #..#. #...#",
    "S": ".#### #.... #.... .###. ....# ....# ####.",
    "T": "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    "U": "#...# #...# #...# #...# #...# #...# .###.",
    "V": "#...# #...# #...# #...# #...# .#.#. ..#..",
    "W": "#...# #...# #...# #.#.# #.#.# #.#.# .#.#.",
    "X": "#...# #...# .#.#. ..#.. .#.#. #...# #...#",
    "Y": "#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..",
    "Z": "##### ....# ...#. ..#.. .#... #.... #####",
    "0": ".###. #...# #..## #.#.# ##..# #...# .###.",
    "1": "..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.",
    "2": ".###. #...# ....# ...#. ..#.. .#... #####",
    "3": "##### ...#. ..#.. ...#. ....# #...# .###.",
    "4": "...#. ..##. .#.#. #..#. ##### ...#. ...#.",
    "5": "##### #.... ####. ....# ....# #...# .###.",
    "6": "..##. .#... #.... ####. #...# #...# .###.",
    "7": "##### ....# ...#. ..#.. .#... .#... .#...",
    "8": ".###. #...# #...# .###. #...# #...# .###.",
    "9": ".###. #...# #...# .#### ....# ...#. .##..",
    "!": "..#.. ..#.. ..#.. ..#.. ..#.. ..... ..#..",
    ".": "..... ..... ..... ..... ..... ..... ..#..",
    ",": "..... ..... ..... ..... ..... ..#.. .#...",
    "/": "..... ....# ...#. ..#.. .#... #.... .....",
    "-": "..... ..... ..... .###. ..... ..... .....",
}
MARKS = {"acute": "...#. ..#..", "tilde": ".##.# #.##."}
ACCENTED = {"Á": ("A", "acute"), "É": ("E", "acute"), "Ó": ("O", "acute"), "Ã": ("A", "tilde")}
TINY = {"H": "#.# #.# ### #.# #.#", "P": "##. #.# ##. #.. #.."}

Z_GLYPH = "##### ...#. ..#.. .#... #####"
ARROW = "##### .###. ..#.."
BURST = (
    "....#.... .#..#..#. ..#.#.#.. ...###... ######### "
    "...###... ..#.#.#.. .#..#..#. ....#...."
)
CLOUD = (
    "......####........ ....########..##.. ..##############.. "
    ".################. ################## .----------------."
)

SHADOW = ((1, 0), (0, 1), (1, 1))
OUTLINE = tuple((dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)


def runs_path(pixels):
    rows = {}
    for x, y in pixels:
        rows.setdefault(y, []).append(x)
    parts = []
    for y in sorted(rows):
        xs = sorted(rows[y])
        start = prev = xs[0]
        for x in xs[1:] + [None]:
            if x is not None and x == prev + 1:
                prev = x
                continue
            w = prev - start + 1
            parts.append(f"M{start} {y}h{w}v1h-{w}z")
            if x is not None:
                start = prev = x
    return "".join(parts)


def path(pixels, color, cls=""):
    if not pixels:
        return ""
    cls_attr = f' class="{cls}"' if cls else ""
    return f'<path{cls_attr} fill="{color}" d="{runs_path(pixels)}"/>'


def rect(x, y, w, h, fill, cls=""):
    cls_attr = f' class="{cls}"' if cls else ""
    return f'<rect{cls_attr} x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'


def grid_pixels(rows, x, y, char="#", scale=1):
    return {
        (x + cx * scale + dx, y + cy * scale + dy)
        for cy, row in enumerate(rows.split())
        for cx, c in enumerate(row)
        if c == char
        for dx in range(scale)
        for dy in range(scale)
    }


def text_pixels(text, x, y):
    pixels = set()
    for i, ch in enumerate(text):
        base, mark = ACCENTED.get(ch, (ch, None))
        gx = x + i * 6
        if base != " ":
            pixels |= grid_pixels(FONT[base], gx, y)
        if mark:
            pixels |= grid_pixels(MARKS[mark], gx, y - 3)
    return pixels


def edged(body, color, edge, offsets):
    rim = {(x + dx, y + dy) for x, y in body for dx, dy in offsets} - body
    return path(rim, edge) + path(body, color)


def text_svg(text, x, y, color=TEXT, edge=TEXT_SHADOW, offsets=SHADOW):
    return edged(text_pixels(text, x, y), color, edge, offsets)


def tiny_svg(text, x, y, color):
    pixels = set()
    for i, ch in enumerate(text):
        pixels |= grid_pixels(TINY[ch], x + i * 4, y)
    return path(pixels, color)


def panel(x, y, w, h, border, fill):
    return (
        rect(x + 1, y, w - 2, h, border) + rect(x, y + 1, w, h - 2, border)
        + rect(x + 2, y + 1, w - 4, h - 2, fill) + rect(x + 1, y + 2, w - 2, h - 4, fill)
    )


def ellipse_pixels(cx, cy, rx, ry):
    pixels = set()
    for dy in range(-ry, ry + 1):
        half = round(rx * math.sqrt(1 - (dy / ry) ** 2))
        pixels |= {(cx + dx, cy + dy) for dx in range(-half, half + 1)}
    return pixels


def sprite_svg(sprite_path, ox, oy):
    img = Image.open(sprite_path).convert("RGBA")
    px = img.load()
    by_color = {}
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a >= 128:
                by_color.setdefault(f"#{r:02x}{g:02x}{b:02x}", set()).add((ox + x, oy + y))
    return "".join(path(pixels, color) for color, pixels in by_color.items())


def ring_pixels(cx, cy, r, width=2):
    return ellipse_pixels(cx, cy, r, r) - ellipse_pixels(cx, cy, r - width, r - width)


def paw_layers():
    """Mega Push hand, modeled on Snorlax's feet: cream palm, brown pad, clawed fingers."""
    fingers = [(4, 6), (10, 4), (16, 6)]
    body = ellipse_pixels(10, 14, 9, 7)
    for cx, cy in fingers:
        body |= ellipse_pixels(cx, cy, 2, 3)
    claws = {(cx, cy - d) for cx, cy in fingers for d in (3, 4)}
    shape = body | claws
    outline = {(x + dx, y + dy) for x, y in shape for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - shape
    shade = {(x, y) for x, y in body if (x + 1, y) not in body or (x, y + 1) not in body}
    pad = ellipse_pixels(10, 15, 4, 3)
    return [
        (outline, INK),
        (body - shade, "#f8e8c0"),
        (shade, "#d8b888"),
        (pad, "#8a5432"),
        (ellipse_pixels(10, 14, 3, 2), "#b8784a"),
        (claws, PAPER),
        ({(7, 8), (13, 8)}, INK),
    ]


def paw_svg(cx, cy, scale):
    layers = paw_layers()
    every = set().union(*(pixels for pixels, _ in layers))
    xs, ys = [x for x, _ in every], [y for _, y in every]
    ox = cx - (min(xs) + (max(xs) - min(xs) + 1) / 2) * scale
    oy = cy - (min(ys) + (max(ys) - min(ys) + 1) / 2) * scale
    ox, oy = round(ox), round(oy)
    return "".join(
        path({(ox + x * scale + dx, oy + y * scale + dy) for x, y in pixels
              for dx in range(scale) for dy in range(scale)}, color)
        for pixels, color in layers
    )


def tr(x, y):
    return f"translate({x}px, {y}px)"


def track(name, prop, stops, fmt=str):
    """Keyframes over the whole loop. Each stop is (second, value[, timing]); the
    timing shapes the segment that leaves the stop, and the default holds the value
    until the next stop."""
    stops = [s if len(s) == 3 else (s[0], s[1], HOLD) for s in stops]
    if stops[0][0] > 0:
        stops.insert(0, (0, stops[0][1], HOLD))
    if stops[-1][0] < LOOP:
        stops.append((LOOP, stops[-1][1], HOLD))
    merged = []
    for stop in stops:
        if merged and merged[-1][0] == stop[0]:
            merged[-1] = stop
        else:
            merged.append(stop)
    body = " ".join(
        f"{round(sec / LOOP * 100, 3)}% {{ {prop}: {fmt(value)}; animation-timing-function: {timing}; }}"
        for sec, value, timing in merged
    )
    return f"@keyframes {name} {{ {body} }}\n      .{name} {{ animation: {name} {LOOP}s infinite; }}"


def move(name, stops):
    return track(name, "transform", stops, fmt=lambda v: tr(*v))


def shown(name, *windows):
    stops = [(0, 0)]
    for start, end in windows:
        stops += [(start, 1), (end, 0)]
    return track(name, "opacity", stops)


def build_background():
    parts = []
    sky = ["#4f9fd8", "#5aa9de", "#66b3e4", "#73bdea", "#81c7ee", "#90d1f2", "#a2daf5", "#b5e3f7"]
    for i, color in enumerate(sky):
        parts.append(rect(0, i * 9, SCREEN_W, 9, color))
        if i:
            parts.append(rect(0, i * 9, SCREEN_W, 1, f"url(#dither{i})"))

    far = {(x, y) for x in range(SCREEN_W)
           for y in range(round(62 - 4 * math.sin(x / 15) - 2 * math.sin(x / 6 + 1)), 74)}
    near = {(x, y) for x in range(SCREEN_W)
            for y in range(round(70 - 2 * abs(math.sin(x / 5)) - math.sin(x / 13)), 76)}
    parts.append(path(far, "#7cbf86"))
    parts.append(path(near, "#4f9a5a"))

    field = ["#a8d878", "#9cd270", "#92cc6a", "#88c664", "#80c060"]
    for i, color in enumerate(field):
        y = 76 + i * 14
        parts.append(rect(0, y, SCREEN_W, SCREEN_H - y, color))
        parts.append(rect(0, y + 7, SCREEN_W, 1, "#b4de86" if i < 2 else "#7ab85a"))

    for cx, cy in ((124, 6), (228, 30), (12, 48)):
        parts.append(path(grid_pixels(CLOUD, cx, cy), "#f8fcff"))
        parts.append(path(grid_pixels(CLOUD, cx, cy, char="-"), "#d4ecf8"))

    for cx, cy, rx, ry in ((186, 86, 46, 11), (62, 140, 58, 12)):
        parts.append(path(ellipse_pixels(cx, cy, rx, ry), "#5c9848"))
        parts.append(path(ellipse_pixels(cx, cy - 1, rx - 2, ry - 2), "#b0e088"))
        parts.append(path(ellipse_pixels(cx - 6, cy - 3, rx - 16, ry - 6), "#c8f0a0"))

    defs = "".join(
        f'<pattern id="dither{i}" width="2" height="1" patternUnits="userSpaceOnUse">'
        f'<rect width="1" height="1" fill="{sky[i - 1]}"/></pattern>'
        for i in range(1, len(sky))
    )
    return defs, "".join(parts)


def build_hp_box(name, x, y, w, h, drains):
    parts = [panel(x, y, w, h, INK, "#f8f8e0")]
    parts.append(text_svg(name, x + 6, y + 5, edge="#d8d8c0"))
    parts.append(text_svg("LV100", x + w - 36, y + 5, edge="#d8d8c0"))
    bar_x, bar_y = x + 22, y + 17
    parts.append(panel(bar_x, bar_y, 82, 7, INK, INK))
    parts.append(tiny_svg("HP", bar_x + 3, bar_y + 1, "#f8c040"))
    parts.append(rect(bar_x + 17, bar_y + 2, 60, 3, "#58e080", cls="hpfill" if drains else ""))
    parts.append(rect(bar_x + 17, bar_y + 2, 60, 1, "#a8f8b8", cls="hpshine" if drains else ""))
    return parts, (bar_x + 17, bar_y + 2)


def build_scene():
    css = []
    defs = []
    field = []

    bg_defs, bg_svg = build_background()
    defs.append(bg_defs)
    field.append(bg_svg)

    # Like the games, the field darkens while the big move plays and the sprites stay lit.
    css.append(track("dim", "opacity", [
        (0, 0), (11.5, 0, "steps(2, end)"), (11.6, 0.55), (12.7, 0.55, "steps(2, end)"), (12.8, 0),
    ]))
    field.append(rect(0, 0, SCREEN_W, SCREEN_H, BG_COLOR, cls="dim"))

    rx, ry = RAYQUAZA_POS
    css.append(move("rayquaza", [
        (0, (0, 0)), (4.9, (-4, 3)), (5.6, (0, 0)),
        (12.3, (0, 0), "steps(4, end)"), (12.65, (130, -110)),
    ]))
    field.append(f'<g class="rayquaza">{sprite_svg(RAYQUAZA_PATH, rx, ry)}</g>')

    sx, sy = SNORLAX_POS
    css.append(move("snorlax", [
        (0, (0, 0)),
        (8.7, (0, -4)), (8.8, (0, 0)), (8.9, (0, -4)), (9.0, (0, 0)),
        (11.98, (0, 0), "steps(2, end)"), (12.06, (4, -3)),
        (12.3, (4, -3), "steps(2, end)"), (12.45, (0, 0)),
    ]))
    css.append(track("snorlaxhit", "opacity", [
        (0, 1), (5.6, 0), (5.7, 1), (5.8, 0), (5.9, 1), (6.0, 0), (6.1, 1),
    ]))
    field.append(
        f'<g class="snorlax"><g class="snorlaxhit">{sprite_svg(SNORLAX_PATH, sx, sy)}</g></g>'
    )

    # Each Z floats on its own short loop; the group only decides when Snorlax sleeps.
    css.append(shown("zzz", (0, 8.6), (15.8, LOOP)))
    css.append(
        "@keyframes zfloat { 0% { transform: translate(0px, 0px); opacity: 0; } 15% { opacity: 1; } "
        "85% { opacity: 1; } 100% { transform: translate(8px, -16px); opacity: 0; } }\n"
        "      .z { animation: zfloat 2.4s steps(8, end) infinite; }"
    )
    zs = "".join(
        f'<g class="z" style="animation-delay:-{i * 0.8:.1f}s">'
        f'{edged(grid_pixels(Z_GLYPH, 82, 96), PAPER, INK, OUTLINE)}</g>'
        for i in range(3)
    )
    field.append(f'<g class="zzz">{zs}</g>')

    css.append(shown("alert", (8.7, 10.4)))
    field.append(
        f'<g class="alert">{panel(76, 84, 11, 13, INK, PAPER)}{text_svg("!", 79, 87, ACCENT, PAPER)}</g>'
    )

    css.append(shown("minusone", (6.0, 7.4)))
    css.append(move("minusonerise", [(0, (0, 0)), (6.0, (0, 0), "steps(6, end)"), (6.3, (0, -6))]))
    field.append(
        f'<g class="minusone"><g class="minusonerise">'
        f'{text_svg("-1", 40, 94, ACCENT, PAPER, OUTLINE)}</g></g>'
    )

    mx, my = rx + RAYQUAZA_MOUTH[0] - 4, ry + RAYQUAZA_MOUTH[1] + 3
    tx, ty = sx + SNORLAX_CENTER[0], sy + SNORLAX_CENTER[1]
    css.append(shown("orb", (4.95, 5.1)))
    field.append(
        f'<g class="orb">{path(ellipse_pixels(mx, my, 3, 3), "#f8e858")}'
        f'{path(ellipse_pixels(mx, my, 1, 1), PAPER)}</g>'
    )
    segments = 8
    beam_xs = list(range(mx, tx, 1 if tx > mx else -1))
    for i in range(segments):
        xs = beam_xs[len(beam_xs) * i // segments:len(beam_xs) * (i + 1) // segments]
        layers = []
        for half, color in ((3, "#f89838"), (2, "#f8e858"), (1, PAPER)):
            pixels = set()
            for x in xs:
                y = round(my + (x - mx) * (ty - my) / (tx - mx))
                pixels |= {(x, y + d) for d in range(-half, half + 1)}
            layers.append(path(pixels, color))
        css.append(shown(f"beam{i}", (5.1 + i * 0.03, 5.6)))
        field.append(f'<g class="beam{i}">{"".join(layers)}</g>')

    css.append(shown("hitsmall", (5.3, 5.45)))
    css.append(shown("hitbig", (5.45, 5.6)))
    field.append(f'<g class="hitsmall">{path(grid_pixels(BURST, tx - 4, ty - 4), "#f8e858")}</g>')
    field.append(f'<g class="hitbig">{path(grid_pixels(BURST, tx - 9, ty - 9, scale=2), PAPER)}</g>')

    for cycle in range(2):
        for i, r in enumerate((30, 22, 14, 6)):
            t = 11.5 + cycle * 0.24 + i * 0.06
            css.append(shown(f"charge{cycle}_{i}", (t, t + 0.06)))
            field.append(f'<g class="charge{cycle}_{i}">{path(ring_pixels(tx, ty, r), "#f8e858")}</g>')

    # The paw flies away from the camera, shrinking from the Snorlax side onto Rayquaza.
    hx, hy = rx + 40, ry + 38
    for i, (cx, cy, scale, start, end) in enumerate([
        (100, 96, 4, 12.0, 12.08), (140, 72, 3, 12.08, 12.16),
        (170, 56, 2, 12.16, 12.24), (hx, hy, 2, 12.24, 12.5),
    ]):
        css.append(shown(f"paw{i}", (start, end)))
        field.append(f'<g class="paw{i}">{paw_svg(cx, cy, scale)}</g>')

    css.append(shown("pushsmall", (12.24, 12.34)))
    css.append(shown("pushbig", (12.34, 12.44)))
    field.append(
        f'<g class="pushsmall">{path(grid_pixels(BURST, hx - 9, hy - 9, scale=2), "#f8e858")}</g>'
    )
    field.append(
        f'<g class="pushbig">{path(grid_pixels(BURST, hx - 18, hy - 18, scale=4), PAPER)}</g>'
    )
    for i, r in enumerate((12, 22, 32, 44)):
        t = 12.24 + i * 0.06
        css.append(shown(f"shock{i}", (t, t + 0.06)))
        field.append(f'<g class="shock{i}">{path(ring_pixels(hx, hy, r), PAPER)}</g>')

    enemy_box, (fx, fy) = build_hp_box("RAYQUAZA", 6, 10, 112, 30, drains=True)
    field.extend(enemy_box)
    player_box, _ = build_hp_box("SNORLAX", 136, 100, 116, 40, drains=False)
    field.extend(player_box)

    # The empty part of the bar slides in from the right under a fixed clip, which
    # drains it pixel by pixel without animating width (Firefox ignores CSS width on rect).
    defs.append(f'<clipPath id="hpclip"><rect x="{fx}" y="{fy}" width="60" height="3"/></clipPath>')
    css.append(move("hpdrain", [(0, (0, 0)), (12.3, (0, 0), "steps(60, end)"), (12.9, (-60, 0))]))
    hp_colors = [(0, "#58e080"), (12.6, "#f8c030"), (12.78, "#f85838")]
    shine_colors = [(0, "#a8f8b8"), (12.6, "#f8e8a0"), (12.78, "#f8a890")]
    css.append(track("hpfill", "fill", hp_colors))
    css.append(track("hpshine", "fill", shine_colors))
    field.append(
        f'<g clip-path="url(#hpclip)"><g class="hpdrain">{rect(fx + 60, fy, 60, 3, INK)}</g></g>'
    )

    # 1/524 of a 60 px bar rounds to zero pixels, so only the number shows the damage.
    for i, (value, start, end) in enumerate([("524", 0, 6.0), ("523", 6.0, LOOP)]):
        css.append(shown(f"hpnum{i}", (start, end)))
        field.append(f'<g class="hpnum{i}">{text_svg(value, 204, 127, edge="#d8d8c0")}</g>')
    field.append(text_svg("/524", 222, 127, edge="#d8d8c0"))

    css.append(track("flash", "opacity", [
        (0, 0), (5.3, 0.5), (5.36, 0), (12.24, 0.8), (12.28, 0), (12.36, 0.5), (12.39, 0),
    ]))
    field.append(rect(0, 0, SCREEN_W, SCREEN_H, PAPER, cls="flash"))

    css.append(move("shake", [
        (0, (0, 0)), (12.24, (3, 0)), (12.29, (-3, 1)), (12.34, (2, -1)),
        (12.39, (-2, 0)), (12.44, (1, 1)), (12.5, (0, 0)),
    ]))

    box = [panel(2, 146, 252, 44, INK, FRAME), panel(5, 149, 246, 38, INK, PAPER)]
    defs.append('<clipPath id="textclip"><rect x="7" y="150" width="242" height="36"/></clipPath>')
    messages = []
    for k, (start, end, lines) in enumerate(MESSAGES):
        css.append(shown(f"msg{k}", (start, end)))
        typed = start + 0.1
        body = []
        for j, line in enumerate(lines):
            lx, ly = 12, 156 + j * 12
            n = len(line)
            css.append(move(f"type{k}_{j}", [
                (0, (0, 0)), (typed, (0, 0), f"steps({n}, end)"), (typed + n * TYPE_SPEED, (n * 6, 0)),
            ]))
            typed += n * TYPE_SPEED
            body.append(text_svg(line, lx, ly))
            body.append(rect(lx - 1, ly - 3, n * 6 + 2, 11, PAPER, cls=f"type{k}_{j}"))
        messages.append(f'<g class="msg{k}">{"".join(body)}</g>')
    box.append(f'<g clip-path="url(#textclip)">{"".join(messages)}</g>')
    box.append(f'<g class="arrow">{path(grid_pixels(ARROW, 238, 179), ACCENT)}</g>')
    css.append(
        "@keyframes blink { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }\n"
        "      .arrow { animation: blink 0.8s infinite; }"
    )

    css.append(track("fade", "opacity", [(0, 1, "steps(4, end)"), (0.4, 0), (18.8, 0, "steps(4, end)"), (19.4, 1)]))
    overlay = rect(0, 0, SCREEN_W, SCREEN_H, BG_COLOR, cls="fade")

    scene = (
        f'<g class="shake">{"".join(field)}</g>'
        f'{"".join(box)}'
        f'{overlay}'
    )
    return css, defs, scene


def build_svg(css, defs, scene):
    W = SCREEN_W * SCALE + PAD * 2
    H = TITLEBAR_H + PAD * 2 + SCREEN_H * SCALE
    screen_x, screen_y = PAD, TITLEBAR_H + PAD
    title_text = f"{LOGIN}@github: ~/batalha"
    css_body = "\n      ".join(css)
    defs_body = "\n    ".join(defs)
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .titletext {{ font-family: 'Courier New', monospace; font-size: 13px; fill: {TITLE_TEXT_COLOR}; }}
      {css_body}
    </style>
    <clipPath id="screen"><rect width="{SCREEN_W}" height="{SCREEN_H}"/></clipPath>
    {defs_body}
  </defs>
  <rect x="0" y="0" width="{W}" height="{H}" rx="10" fill="{BG_COLOR}" />
  <path d="M0,10 a10,10 0 0 1 10,-10 h{W - 20} a10,10 0 0 1 10,10 v{TITLEBAR_H - 10} h-{W} z"
        fill="{TITLEBAR_COLOR}" />
  <circle cx="24" cy="{TITLEBAR_H // 2}" r="6" fill="#ff5f57" />
  <circle cx="46" cy="{TITLEBAR_H // 2}" r="6" fill="#febc2e" />
  <circle cx="68" cy="{TITLEBAR_H // 2}" r="6" fill="#28c840" />
  <text x="{W // 2}" y="{TITLEBAR_H // 2 + 5}" text-anchor="middle" class="titletext">{xml_escape(title_text)}</text>
  <line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="#1f2740" stroke-width="1" />
  <g transform="translate({screen_x} {screen_y}) scale({SCALE})" shape-rendering="crispEdges">
    <g clip-path="url(#screen)">
      <rect width="{SCREEN_W}" height="{SCREEN_H}" fill="{BG_COLOR}"/>
      {scene}
    </g>
  </g>
</svg>
'''


def main():
    css, defs, scene = build_scene()
    svg = build_svg(css, defs, scene)
    os.makedirs(os.path.dirname(OUT_PATH) or ".", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
