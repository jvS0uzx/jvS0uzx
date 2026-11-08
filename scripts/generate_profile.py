#!/usr/bin/env python3
import base64
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape as xml_escape

LOGIN = os.environ.get("GITHUB_LOGIN", "jvS0uzx")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT_DIR = os.environ.get("OUT_DIR", "assets")

# Corta o que não é projeto de terceiro com público de verdade: README de perfil de amigo
# e o repositório .github da empresa, que também são públicos.
MIN_STARS = 100

# Catppuccin Mocha, o mesmo tema do kitty e do fastfetch.
MANTLE, BASE = "#181825", "#1e1e2e"
SURFACE0, SURFACE1 = "#313244", "#45475a"
OVERLAY0, OVERLAY1 = "#6c7086", "#7f849c"
SUBTEXT0, SUBTEXT1, TEXT = "#a6adc8", "#bac2de", "#cdd6f4"
LAVENDER, MAUVE, BLUE, GREEN = "#b4befe", "#cba6f7", "#89b4fa", "#a6e3a1"
RED, YELLOW, PINK, TEAL, ROSEWATER = "#f38ba8", "#f9e2af", "#f5c2e7", "#94e2d5", "#f5e0dc"
TERMINAL_COLORS = [SURFACE1, RED, GREEN, YELLOW, BLUE, PINK, TEAL, SUBTEXT1]

MONO = "'JetBrains Mono', 'Cascadia Code', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"
SANS = "'Segoe UI', Helvetica, Arial, sans-serif"

# O logo fedora_small do fastfetch, sem o padding.
FEDORA_LOGO = [
    "        ,'''''.",
    "       |   ,.  |",
    "       |  |  '_'",
    "  ,....|  |..",
    ".'  ,_;|   ..'",
    "|  |   |  |",
    "|  ',_,'  |",
    " '.     ,'",
    "   '''''",
]

MACHINE = [
    ("sistema", "Fedora Linux 44"),
    ("desktop", "KDE Plasma · Wayland"),
    ("terminal", "kitty · zsh"),
    ("editor", "nvim"),
]
ABOUT = [
    ("cargo", "desenvolvedor full stack"),
    ("foco", "backend, automação e infra self-hosted"),
    ("stack", "go, python, typescript, postgres, docker, aws"),
]

MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

STATS_QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(privacy: PUBLIC, ownerAffiliations: OWNER, isFork: false, first: 5,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes { name pushedAt }
    }
    contributionsCollection { contributionCalendar { totalContributions } }
  }
}"""

W = 880
FONT = 14
# Avanço de 0,6 em, o das fontes mono comuns; o textLength força esse valor nas linhas
# que precisam ficar no grid, então a fonte que o visitante tiver não desalinha nada.
CHAR_W = FONT * 0.6
LINE_H = 22
TITLEBAR_H = 36
PAD_X = 28


def request(url, data=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": f"{LOGIN}-profile-assets"}
    if TOKEN and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {TOKEN}"
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read(), resp.headers.get_content_type()


def api(path):
    body, _ = request(f"https://api.github.com/{path}")
    return json.loads(body)


def graphql(query, **variables):
    body, _ = request("https://api.github.com/graphql", json.dumps({"query": query, "variables": variables}).encode())
    payload = json.loads(body)
    if payload.get("errors"):
        raise RuntimeError(f"GitHub GraphQL error: {payload['errors'][0]['message']}")
    return payload["data"]


def parse_time(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def fmt_int(n):
    return f"{n:,}".replace(",", ".")


def fmt_stars(n):
    return f"{n / 1000:.1f} mil".replace(".", ",") if n >= 1000 else str(n)


def fmt_date(iso):
    d = parse_time(iso)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def since(iso, now):
    days = (now - parse_time(iso)).days
    if days <= 0:
        return "hoje"
    if days == 1:
        return "ontem"
    if days < 60:
        return f"há {days} dias"
    return f"há {days // 30} meses"


def upstream_prs():
    query = f"is:pr is:merged is:public author:{LOGIN} -user:{LOGIN}"
    items = api("search/issues?" + urllib.parse.urlencode({"q": query, "per_page": 100}))["items"]
    repos = {}
    prs = []
    for item in items:
        full_name = item["repository_url"].removeprefix("https://api.github.com/repos/")
        if full_name not in repos:
            repos[full_name] = api(f"repos/{full_name}")
        repo = repos[full_name]
        if repo["stargazers_count"] < MIN_STARS:
            continue
        prs.append(
            {
                "repo": full_name,
                "owner": repo["owner"]["login"],
                "avatar": repo["owner"]["avatar_url"],
                "stars": repo["stargazers_count"],
                "number": item["number"],
                "title": item["title"],
                "merged_at": item["pull_request"]["merged_at"],
            }
        )
    prs.sort(key=lambda pr: pr["merged_at"], reverse=True)
    return prs


def avatar_data_uri(url):
    sep = "&" if "?" in url else "?"
    body, content_type = request(f"{url}{sep}s=72")
    return f"data:{content_type};base64,{base64.b64encode(body).decode()}"


def mono_text(x, y, content, fill, extra=""):
    return f'<text x="{x:.1f}" y="{y}" fill="{fill}"{extra}>{xml_escape(content)}</text>'


def grid_text(x, y, content, fill, extra=""):
    length = len(content) * CHAR_W
    return mono_text(x, y, content, fill, f' textLength="{length:.1f}" lengthAdjust="spacingAndGlyphs"{extra}')


def build_hero(stats, prs, now):
    user = stats["user"]
    repos = user["repositories"]
    recent = next((r for r in repos["nodes"] if r["name"] != LOGIN), None)

    github_rows = [
        ("repos", f"{repos['totalCount']} públicos", ""),
        ("contrib", f"{fmt_int(user['contributionsCollection']['contributionCalendar']['totalContributions'])} no último ano", ""),
    ]
    if prs:
        owners = list(dict.fromkeys(pr["owner"] for pr in prs))
        label = "PR aceito" if len(prs) == 1 else "PRs aceitos"
        github_rows.append(("upstream", ", ".join(owners), f"  {len(prs)} {label}"))
    if recent:
        github_rows.append(("ativo", recent["name"], f"  {since(recent['pushedAt'], now)}"))

    rows = [("title",), ("sep",)]
    rows += [("kv", k, v, "", LAVENDER) for k, v in MACHINE]
    rows += [("blank",)]
    rows += [("kv", k, v, "", MAUVE) for k, v in ABOUT]
    rows += [("blank",)]
    rows += [("kv", k, v, dim, BLUE) for k, v, dim in github_rows]
    rows += [("blank",), ("colors",)]

    cmd_y = TITLEBAR_H + 34
    out_y = cmd_y + 2 * LINE_H
    prompt_y = out_y + (len(rows) + 1) * LINE_H
    H = prompt_y + 30

    info_x = PAD_X + 15 * CHAR_W + 44
    value_x = info_x + 10 * CHAR_W
    reveal = 1.45
    step = 0.035

    def out(delay, inner):
        return f'<g class="out" style="animation-delay:{delay:.2f}s">{inner}</g>'

    parts = []
    for i, line in enumerate(FEDORA_LOGO):
        y = out_y + (i + 1) * LINE_H
        parts.append(out(reveal + (i + 1) * step, grid_text(PAD_X, y, line, LAVENDER, ' font-weight="700" xml:space="preserve"')))

    for i, row in enumerate(rows):
        y = out_y + i * LINE_H
        delay = reveal + i * step
        kind = row[0]
        if kind == "title":
            inner = (
                f'<text x="{info_x:.1f}" y="{y}" font-weight="700">'
                f'<tspan fill="{MAUVE}">joao</tspan><tspan fill="{TEXT}">@</tspan><tspan fill="{MAUVE}">fedora</tspan></text>'
            )
        elif kind == "sep":
            inner = grid_text(info_x, y, "─" * 34, OVERLAY0)
        elif kind == "kv":
            _, key, value, dim, color = row
            inner = mono_text(info_x, y, key, color, ' font-weight="700"')
            inner += (
                f'<text x="{value_x:.1f}" y="{y}" fill="{TEXT}" xml:space="preserve">{xml_escape(value)}'
                f'<tspan fill="{OVERLAY1}">{xml_escape(dim)}</tspan></text>'
            )
        elif kind == "colors":
            inner = "".join(
                f'<circle cx="{info_x + 6 + j * 22:.1f}" cy="{y - 5}" r="6" fill="{c}"/>' for j, c in enumerate(TERMINAL_COLORS)
            )
        else:
            continue
        parts.append(out(delay, inner))

    def prompt(y):
        return f'<text x="{PAD_X}" y="{y}" font-weight="700"><tspan fill="{BLUE}">~</tspan><tspan fill="{GREEN}"> ❯</tspan></text>'

    cmd_x = PAD_X + 4 * CHAR_W
    cmd = "fastfetch"
    typing = len(cmd) * CHAR_W
    key_interval = 0.09
    # Uma letra por elemento, revelada por opacidade: clip-path em <text> não anima no Safari.
    typed = "".join(
        out(0.5 + (i + 1) * key_interval, mono_text(cmd_x + i * CHAR_W, cmd_y, ch, TEXT)) for i, ch in enumerate(cmd)
    )
    final_delay = reveal + (len(rows) + 1) * step

    title = "joao@fedora: ~"
    controls_y = TITLEBAR_H / 2
    controls = (
        f'<path d="M{W - 82} {controls_y - 2} l4 4 l4 -4" />'
        f'<path d="M{W - 56} {controls_y + 2} l4 -4 l4 4" />'
        f'<path d="M{W - 30} {controls_y - 4} l8 8 M{W - 22} {controls_y - 4} l-8 8" />'
    )
    body = "\n  ".join(parts)

    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Terminal com fastfetch: Fedora Linux 44, KDE Plasma, desenvolvedor full stack com foco em backend, automação e infra self-hosted">
  <defs>
    <clipPath id="window"><rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12"/></clipPath>
    <linearGradient id="border" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{LAVENDER}" stop-opacity="0.65"/>
      <stop offset="1" stop-color="{MAUVE}" stop-opacity="0.35"/>
    </linearGradient>
  </defs>
  <style>
    text {{ font-family: {MONO}; font-size: {FONT}px; }}
    .title {{ font-family: {SANS}; font-size: 13px; }}
    .controls path {{ fill: none; stroke: {OVERLAY1}; stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; }}
    .caret {{ animation: move {len(cmd) * key_interval:.2f}s steps({len(cmd)}, end) 0.5s forwards, gone 0.01s linear {reveal - 0.05:.2f}s forwards; }}
    .out {{ opacity: 0; animation: show 0.01s linear forwards; }}
    .blink {{ animation: blink 1.1s steps(1) infinite; }}
    @keyframes move {{ to {{ transform: translateX({typing:.1f}px); }} }}
    @keyframes gone {{ to {{ opacity: 0; }} }}
    @keyframes show {{ to {{ opacity: 1; }} }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .out {{ animation: none; opacity: 1; }}
      .caret {{ animation: none; opacity: 0; }}
      .blink {{ animation: none; }}
    }}
  </style>
  <g clip-path="url(#window)">
    <rect width="{W}" height="{H}" fill="{BASE}"/>
    <rect width="{W}" height="{TITLEBAR_H}" fill="{MANTLE}"/>
    <line x1="0" y1="{TITLEBAR_H - 0.5}" x2="{W}" y2="{TITLEBAR_H - 0.5}" stroke="{SURFACE0}"/>
  </g>
  <text x="{W / 2}" y="{TITLEBAR_H / 2 + 4.5}" class="title" fill="{SUBTEXT0}" text-anchor="middle">{title}</text>
  <g class="controls">{controls}</g>
  {prompt(cmd_y)}
  {typed}
  <rect class="caret" x="{cmd_x:.1f}" y="{cmd_y - 14}" width="{CHAR_W:.1f}" height="18" fill="{ROSEWATER}"/>
  {body}
  {out(final_delay, prompt(prompt_y) + f'<rect class="blink" x="{cmd_x:.1f}" y="{prompt_y - 14}" width="{CHAR_W:.1f}" height="18" fill="{ROSEWATER}"/>')}
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="url(#border)"/>
</svg>
'''


def build_upstream(prs):
    row_h = 66
    header_h = 54
    footer_h = 40
    H = header_h + max(len(prs), 1) * row_h + footer_h
    count = f"{len(prs)} PR aceito" if len(prs) == 1 else f"{len(prs)} PRs aceitos"

    rows = []
    for i, pr in enumerate(prs):
        y = header_h + i * row_h
        title = pr["title"] if len(pr["title"]) <= 78 else pr["title"][:77] + "…"
        rows.append(
            f'<clipPath id="av{i}"><rect x="24" y="{y + 8}" width="36" height="36" rx="9"/></clipPath>'
            f'<image href="{avatar_data_uri(pr["avatar"])}" x="24" y="{y + 8}" width="36" height="36" clip-path="url(#av{i})"/>'
            f'<rect x="24" y="{y + 8}" width="36" height="36" rx="9" fill="none" stroke="{SURFACE1}"/>'
            f'<text x="76" y="{y + 22}" class="repo" fill="{TEXT}">{xml_escape(pr["repo"])}</text>'
            f'<text x="{W - 150}" y="{y + 22}" class="meta" fill="{YELLOW}" text-anchor="end">★ <tspan fill="{SUBTEXT0}">{fmt_stars(pr["stars"])}</tspan></text>'
            f'<text x="{W - 24}" y="{y + 22}" class="meta" fill="{OVERLAY1}" text-anchor="end">{fmt_date(pr["merged_at"])}</text>'
            f'<svg x="76" y="{y + 32}" width="14" height="14" viewBox="0 0 16 16"><path fill="{MAUVE}" d="{MERGE_ICON}"/></svg>'
            f'<text x="96" y="{y + 44}" class="pr" fill="{SUBTEXT1}">{xml_escape(title)}'
            f'<tspan fill="{MAUVE}">  #{pr["number"]}</tspan></text>'
        )
        if i < len(prs) - 1:
            rows.append(f'<line x1="76" y1="{y + row_h - 4}" x2="{W - 24}" y2="{y + row_h - 4}" stroke="{SURFACE0}"/>')
    if not prs:
        rows.append(f'<text x="24" y="{header_h + 30}" class="pr" fill="{OVERLAY1}">nenhum PR aceito ainda</text>')

    body = "\n  ".join(rows)
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{count} em projetos open source de terceiros">
  <style>
    .label {{ font-family: {SANS}; font-size: 12px; font-weight: 600; letter-spacing: 1.6px; }}
    .repo {{ font-family: {SANS}; font-size: 15px; font-weight: 600; }}
    .meta {{ font-family: {MONO}; font-size: 12.5px; }}
    .pr {{ font-family: {MONO}; font-size: 12.5px; }}
    .note {{ font-family: {SANS}; font-size: 12px; }}
  </style>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="{MANTLE}" stroke="{SURFACE0}"/>
  <rect x="0.5" y="14" width="3" height="{H - 28}" rx="1.5" fill="{MAUVE}"/>
  <text x="24" y="32" class="label" fill="{SUBTEXT0}">UPSTREAM</text>
  <circle cx="{W - 24 - len(count) * 6.6 - 12}" cy="28" r="4" fill="{GREEN}"/>
  <text x="{W - 24}" y="32" class="note" fill="{SUBTEXT0}" text-anchor="end">{count}</text>
  {body}
  <text x="24" y="{H - 16}" class="note" fill="{OVERLAY0}">pull requests aceitos em projetos de terceiros com {MIN_STARS}+ estrelas</text>
</svg>
'''


# Octicon git-merge-16 (MIT).
MERGE_ICON = (
    "M5.45 5.154A4.25 4.25 0 0 0 9.25 7.5h1.378a2.251 2.251 0 1 1 0 1.5H9.25A5.734 5.734 0 0 1 5 7.123v3.505"
    "a2.25 2.25 0 1 1-1.5 0V5.372a2.25 2.25 0 1 1 1.95-.218ZM4.25 13.5a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z"
    "m8.5-4.5a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5ZM5 3.25a.75.75 0 1 0 0 .005V3.25Z"
)


def main():
    if not TOKEN:
        raise SystemExit("GITHUB_TOKEN ausente: a API GraphQL exige autenticação")
    now = datetime.now(timezone.utc)
    stats = graphql(STATS_QUERY, login=LOGIN)
    prs = upstream_prs()

    os.makedirs(OUT_DIR, exist_ok=True)
    for name, svg in (("hero.svg", build_hero(stats, prs, now)), ("upstream.svg", build_upstream(prs))):
        path = os.path.join(OUT_DIR, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
