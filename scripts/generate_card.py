#!/usr/bin/env python3
import os
import sys
from xml.sax.saxutils import escape as xml_escape

LOGIN = os.environ.get("GITHUB_LOGIN", "jvS0uzx")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
SPRITE_PATH = os.environ.get("SPRITE_PATH", "assets/snorlax.png")
OUT_PATH = os.environ.get("OUT_PATH", "assets/profile.svg")

PROFILE_FIELDS = [
    ("Nome", "João Vitor Souza"),
    ("Cargo", "desenvolvedor full stack"),
    ("Foco", "backend, automação e infra self-hosted"),
    ("Stack.Backend", "python, django, go, node.js"),
    ("Stack.Frontend", "typescript, react"),
    ("Stack.Banco", "postgresql, redis"),
    ("Stack.Infra", "docker, nginx, github actions"),
    ("Stack.IA", "claude code, ollama"),
    ("Ambiente", "arch linux, ubuntu, debian, git"),
    ("Ferramentas", "postman, notion, obsidian, telegram"),
    ("Contato.GitHub", f"github.com/{LOGIN}"),
    ("Contato.Email", "joaovitordev.py@gmail.com"),
]

BG_COLOR = "#0b1120"
TITLEBAR_COLOR = "#141c30"
TITLE_TEXT_COLOR = "#7f8aa6"
ACCENT = "#5dc9f2"
HEADER_COLOR = "#e8384f"
LABEL_COLOR = "#ffffff"
VALUE_COLOR = "#5dc9f2"
PALETTE = ["#0b1120", "#e8384f", "#3ddc84", "#ffd166", "#4d8cff",
           "#b16cff", "#39e0d0", "#e8e8e8"]

PROMPT_COMMANDS = [
    "desenvolvedor full stack",
    "backend e automação",
    "infra self-hosted",
]
PROMPT_TYPE_SPEED = 0.08
PROMPT_DELETE_SPEED = 0.045
PROMPT_HOLD_TIME = 1.1
PROMPT_GAP_TIME = 0.4
PROMPT_CHAR_W = 9.0

PIXEL = 5
TITLEBAR_H = 34


def pixel_runs_from_sprite(path):
    from PIL import Image

    img = Image.open(path).convert("RGBA")
    img = img.crop(img.getbbox())
    w, h = img.size
    px = img.load()

    rows = []
    for y in range(h):
        runs = []
        x = 0
        while x < w:
            r, g, b, a = px[x, y]
            if a < 128:
                x += 1
                continue
            color = f"#{r:02x}{g:02x}{b:02x}"
            start = x
            while x < w and px[x, y][3] >= 128 and f"#{px[x, y][0]:02x}{px[x, y][1]:02x}{px[x, y][2]:02x}" == color:
                x += 1
            runs.append((start, x - start, color))
        rows.append(runs)
    return rows, w, h


def build_prompt_typing_svg(commands, x, y):
    durations = []
    for cmd in commands:
        n = max(1, len(cmd))
        durations.append(n * PROMPT_TYPE_SPEED + PROMPT_HOLD_TIME + n * PROMPT_DELETE_SPEED + PROMPT_GAP_TIME)
    total = sum(durations)

    max_w = max(len(c) for c in commands) * PROMPT_CHAR_W

    keyframes_css = []
    cursor_stops = []
    groups_svg = []
    t = 0.0
    for i, cmd in enumerate(commands):
        n = max(1, len(cmd))
        full_w = n * PROMPT_CHAR_W
        type_dur = n * PROMPT_TYPE_SPEED
        delete_dur = n * PROMPT_DELETE_SPEED

        t_start = t
        t_type_end = t_start + type_dur
        t_hold_end = t_type_end + PROMPT_HOLD_TIME
        t_delete_end = t_hold_end + delete_dur
        t = t_delete_end + PROMPT_GAP_TIME

        def pct(sec):
            return round(max(0.0, min(100.0, sec / total * 100)), 3)

        stops = [
            (0, 0, "steps(1, jump-end)"),
            (pct(t_start), 0, f"steps({n}, jump-end)"),
            (pct(t_type_end), full_w, "steps(1, jump-end)"),
            (pct(t_hold_end), full_w, f"steps({n}, jump-end)"),
            (pct(t_delete_end), 0, "steps(1, jump-end)"),
            (100, 0, "steps(1, jump-end)"),
        ]
        seen = []
        for p, w, tf in stops:
            if seen and seen[-1][0] == p:
                seen[-1] = (p, w, tf)
            else:
                seen.append((p, w, tf))

        body = " ".join(
            f"{p}% {{ width: {w:.1f}px; animation-timing-function: {tf}; }}" for p, w, tf in seen
        )
        keyframes_css.append(f"@keyframes promptClip{i} {{ {body} }}")
        cursor_stops.extend(seen)

        groups_svg.append(f'''
      <clipPath id="promptClip{i}">
        <rect x="{x}" y="{y-14}" width="{full_w:.1f}" height="20" class="promptClipRect{i}" />
      </clipPath>''')

    text_svg = []
    for i, cmd in enumerate(commands):
        full_w = max(1, len(cmd)) * PROMPT_CHAR_W
        text_svg.append(
            f'\n      <text x="{x}" y="{y}" class="promptcmd" clip-path="url(#promptClip{i})" '
            f'textLength="{full_w:.1f}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{xml_escape(cmd)}</text>'
        )

    clip_anim_css = "\n".join(
        f".promptClipRect{i} {{ animation: promptClip{i} {total:.3f}s infinite; }}"
        for i in range(len(commands))
    )

    cursor_body = " ".join(
        f"{p}% {{ transform: translateX({w:.1f}px); animation-timing-function: {tf}; }}"
        for p, w, tf in cursor_stops
    )
    cursor_css = (
        f"@keyframes promptCursorMove {{ {cursor_body} }}\n      "
        f".promptcursor {{ animation: promptCursorMove {total:.3f}s infinite, blink 1s steps(1) infinite; }}"
    )

    cursor_svg = f'<rect x="{x:.1f}" y="{y-14:.1f}" width="8" height="16" class="promptcursor" />'

    style = "\n      ".join(keyframes_css) + "\n      " + clip_anim_css + "\n      " + cursor_css
    defs = "".join(groups_svg)
    return style, defs, "".join(text_svg), cursor_svg, max_w


def fetch_github_stats(login, token):
    stats = {"repos": "N/A", "stars": "N/A", "followers": "N/A"}
    if not token:
        return stats
    try:
        import requests

        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

        user_resp = requests.get(f"https://api.github.com/users/{login}", headers=headers, timeout=15)
        user_resp.raise_for_status()
        user = user_resp.json()
        stats["followers"] = str(user.get("followers", "N/A"))
        stats["repos"] = str(user.get("public_repos", "N/A"))

        repos_resp = requests.get(
            f"https://api.github.com/users/{login}/repos?per_page=100&type=owner",
            headers=headers, timeout=15,
        )
        repos_resp.raise_for_status()
        repos = repos_resp.json()
        stats["stars"] = str(sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork")))
    except Exception as e:
        print(f"warning: failed to fetch live stats: {e}", file=sys.stderr)
    return stats


def build_svg(pixel_rows, sprite_w, sprite_h, fields):
    PAD = 34
    ART_W = sprite_w * PIXEL
    ART_H = sprite_h * PIXEL
    GAP = 46
    FIELD_LINE_H = 22
    HEADER_H = 26
    RULE_GAP = 10
    SWATCH = 20
    SWATCH_GAP = 8
    PROMPT_H = 62

    info_x = PAD + ART_W + GAP
    header_y = TITLEBAR_H + PAD + HEADER_H
    rule_y = header_y + RULE_GAP
    fields_start_y = rule_y + 30

    fields_h = len(fields) * FIELD_LINE_H
    swatch_y = fields_start_y + fields_h + 14
    info_bottom = swatch_y + SWATCH + 10

    art_top = header_y - HEADER_H + max(0, (info_bottom - header_y + HEADER_H - ART_H) / 2)
    art_bottom = art_top + ART_H
    content_bottom = max(info_bottom, art_bottom)

    prompt_y = content_bottom + 40
    H = prompt_y + PROMPT_H + 20
    header_text = f"{LOGIN}@github"
    rule_len = max(len(header_text) + 2, 36)
    W = info_x + max(360, len(max([f"{k}: {v}" for k, v in fields], key=len)) * 8.2) + PAD

    art_lines = []
    for i, runs in enumerate(pixel_rows):
        if not runs:
            continue
        y = art_top + i * PIXEL
        delay = round(i * 0.03, 3)
        rects = "".join(
            f'<rect x="{PAD + x * PIXEL}" y="{y:.0f}" width="{w * PIXEL}" height="{PIXEL}" fill="{color}"/>'
            for x, w, color in runs
        )
        art_lines.append(f'\n      <g class="fadein" style="animation-delay:{delay}s">{rects}</g>')
    art_svg = f'<g shape-rendering="crispEdges">{"".join(art_lines)}\n  </g>'

    header_svg = (
        f'<text x="{info_x}" y="{header_y}" class="header">{xml_escape(header_text)}</text>'
        f'\n  <line x1="{info_x}" y1="{rule_y}" x2="{info_x + rule_len * 9.4}" y2="{rule_y}" class="rule" />'
    )

    field_lines = []
    for i, (label, value) in enumerate(fields):
        y = fields_start_y + i * FIELD_LINE_H
        delay = 0.5 + i * 0.06
        field_lines.append(
            f'\n      <text x="{info_x}" y="{y}" class="fieldline typewriter" style="animation-delay:{delay:.2f}s">'
            f'<tspan class="label">{xml_escape(label)}:</tspan> '
            f'<tspan class="value">{xml_escape(value)}</tspan></text>'
        )
    fields_svg = "".join(field_lines)

    swatch_lines = []
    for i, color in enumerate(PALETTE):
        x = info_x + i * (SWATCH + SWATCH_GAP)
        delay = 0.5 + len(fields) * 0.06 + i * 0.05
        swatch_lines.append(
            f'\n      <rect x="{x:.1f}" y="{swatch_y:.1f}" width="{SWATCH}" height="{SWATCH}" rx="3" '
            f'fill="{color}" stroke="#2a3350" stroke-width="1" class="swatch" style="animation-delay:{delay:.2f}s" />'
        )
    swatch_svg = "".join(swatch_lines)

    prompt_line1 = f"┌──({LOGIN}@github)-[~]"
    prompt_line2 = "└─$ "

    typed_x = PAD + (len(prompt_line2) + 1) * 9.0
    typed_y = prompt_y + 24
    prompt_style, prompt_defs, prompt_cmd_svg, prompt_cursor_svg, cmd_max_w = build_prompt_typing_svg(
        PROMPT_COMMANDS, typed_x, typed_y
    )

    prompt_svg = (
        f'<text x="{PAD}" y="{prompt_y}" class="prompt">{xml_escape(prompt_line1)}</text>'
        f'\n  <text x="{PAD}" y="{typed_y}" class="prompt">{xml_escape(prompt_line2)}</text>'
        f'\n  {prompt_cmd_svg}'
        f'\n  {prompt_cursor_svg}'
    )

    W = max(W, typed_x + cmd_max_w + PAD)

    title_text = f"{LOGIN}@github: ~"
    chrome_svg = f'''
  <rect x="0" y="0" width="{W:.0f}" height="{H:.0f}" rx="10" fill="{BG_COLOR}" />
  <path d="M0,10 a10,10 0 0 1 10,-10 h{W-20:.0f} a10,10 0 0 1 10,10 v{TITLEBAR_H-10:.0f} h-{W:.0f} z"
        fill="{TITLEBAR_COLOR}" />
  <circle cx="24" cy="{TITLEBAR_H/2:.0f}" r="6" fill="#ff5f57" />
  <circle cx="46" cy="{TITLEBAR_H/2:.0f}" r="6" fill="#febc2e" />
  <circle cx="68" cy="{TITLEBAR_H/2:.0f}" r="6" fill="#28c840" />
  <text x="{W/2:.0f}" y="{TITLEBAR_H/2 + 5:.0f}" text-anchor="middle" class="titletext">{xml_escape(title_text)}</text>
  <line x1="0" y1="{TITLEBAR_H}" x2="{W:.0f}" y2="{TITLEBAR_H}" stroke="#1f2740" stroke-width="1" />'''

    return f'''<svg width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .header {{ font-family: 'Courier New', monospace; font-size: 18px; font-weight: bold; fill: {HEADER_COLOR}; }}
      .rule {{ stroke: {HEADER_COLOR}; stroke-width: 1.4; opacity: 0.85; }}
      .fieldline {{ font-family: 'Courier New', monospace; font-size: 13px; }}
      .label {{ fill: {LABEL_COLOR}; font-weight: bold; }}
      .value {{ fill: {VALUE_COLOR}; }}
      .prompt {{ font-family: 'Courier New', monospace; font-size: 15px; font-weight: bold; fill: {HEADER_COLOR}; }}
      .titletext {{ font-family: 'Courier New', monospace; font-size: 13px; fill: {TITLE_TEXT_COLOR}; }}
      .promptcmd {{ font-family: 'Courier New', monospace; font-size: 15px; fill: {VALUE_COLOR}; white-space: pre; }}
      .promptcursor {{ fill: {ACCENT}; }}
      {prompt_style}
      .fadein, .typewriter, .swatch {{ animation-name: reveal; animation-duration: 0.35s; animation-fill-mode: both; animation-timing-function: steps(1); }}
      @keyframes reveal {{ 0% {{ opacity: 0; }} 1%, 100% {{ opacity: 1; }} }}
      @keyframes blink {{ 0%, 49% {{ opacity: 1; }} 50%, 100% {{ opacity: 0; }} }}
    </style>
    {prompt_defs}
  </defs>
  {chrome_svg}

  {art_svg}

  {header_svg}
  {fields_svg}
  {swatch_svg}

  {prompt_svg}
</svg>
'''


def main():
    pixel_rows, sprite_w, sprite_h = pixel_runs_from_sprite(SPRITE_PATH)
    stats = fetch_github_stats(LOGIN, TOKEN)

    fields = list(PROFILE_FIELDS)
    fields.extend([
        ("GitHub.Repositórios", stats["repos"]),
        ("GitHub.Estrelas", stats["stars"]),
        ("GitHub.Seguidores", stats["followers"]),
    ])

    svg = build_svg(pixel_rows, sprite_w, sprite_h, fields)
    os.makedirs(os.path.dirname(OUT_PATH) or ".", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
