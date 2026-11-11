#!/usr/bin/env python3
"""Draw the profile README as SVG cards.

A GitHub README cannot run scripts or load a stylesheet, but it can show an
image, and an SVG image carries its own CSS and fonts. So the layout lives in
README.md and everything visual lives in cards/*.svg, drawn here.

    python scripts/render_cards.py            animated cards
    STATIC=1 python scripts/render_cards.py   final frame, for screenshots

Standard library only, so the daily Action needs no install step. Text is
measured with the advance widths in fonts/metrics.json, which is what lets
lines wrap and names fit without a browser in the loop.
"""
from __future__ import annotations

import base64
import json
import os
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
STATIC = os.environ.get("STATIC") == "1"

DATA = json.loads((ROOT / "data" / "github.json").read_text())
METRICS = json.loads((ROOT / "fonts" / "metrics.json").read_text())

# ---------------------------------------------------------------- the palette
# Matte charcoal ground with warm amber-gold accents matching the avatar logo.

OBSIDIAN = "#181715"  # dark charcoal edge
UMBER = "#292216"     # warm dark bronze across the sweep
AMBER = "#F5A623"     # vibrant amber-gold highlight
INK = "#16120B"       # dark text on amber
SOFT = "#DDD5C7"      # secondary text on charcoal ground

THEMES = {
    "light": {
        "bg": "#F6F3EC",
        "panel": "#EAE3D5",
        "title": INK,
        "body": "#5C5242",
        "mark": "#B4690E",
        "pill_bg": "#EFE3CC",
        "pill_fg": "#8A4F08",
    },
    "dark": {
        "bg": "#1B1916",
        "panel": "#26221C",
        "title": "#F7F4EE",
        "body": "#BFB5A4",
        "mark": AMBER,
        "pill_bg": "#2E261A",
        "pill_fg": AMBER,
    },
}

LANG = {
    "TypeScript": "#3178C6",
    "JavaScript": "#F1E05A",
    "Python": "#3572A5",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
}

# ------------------------------------------------------------- service cards

SERVICES = [
    {
        "key": "seo",
        "tag": "01 / GROWTH",
        "title": "SEO & Digital Growth",
        "blurb": "Off-page SEO campaigns covering link building, guest posting, "
                 "blogger outreach, business citations, and white-hat authority growth.",
        "foot": "Red Vision LLC",
    },
    {
        "key": "web",
        "tag": "02 / ENGINEERING",
        "title": "Full-Stack Web Dev",
        "blurb": "Modern web platforms, dynamic page builders, and responsive "
                 "storefronts engineered with clean architecture and performance.",
        "foot": "SecureSite Studio",
    },
    {
        "key": "ai",
        "tag": "03 / AUTOMATION",
        "title": "AI & Workflow Automation",
        "blurb": "Practical agentic workflows connecting LLM APIs, webhooks, "
                 "WhatsApp ordering flows, and automated lead pipelines.",
        "foot": "OpenAI / Gemini / n8n",
    },
]

START = 2.0
SLOT = 2.6
LAP = SLOT * len(SERVICES)
TURN = 100 / len(SERVICES)
ON = f"0%,{TURN:.3f}%,100%"
HELD = f"1.5%,{TURN - 1.6:.3f}%"


# ------------------------------------------------------------------ type

def font_face(name: str, family: str) -> str:
    raw = (ROOT / "fonts" / f"archivo-{name}.woff").read_bytes()
    b64 = base64.b64encode(raw).decode()
    return (f"@font-face{{font-family:'{family}';"
            f"src:url(data:font/woff;base64,{b64}) format('woff')}}")


FONTS = {"display": "AX", "semi": "A6", "regular": "A4"}


def width(text_str: str, font: str, size: float) -> float:
    m = METRICS[font]
    fallback = m["adv"]["n"]
    return sum(m["adv"].get(ch, fallback) for ch in text_str) * size / m["upm"]


def wrap(text_str: str, font: str, size: float, max_width: float) -> list[str]:
    lines, line = [], ""
    for word in text_str.split():
        trial = f"{line} {word}".strip()
        if width(trial, font, size) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def fit(text_str: str, font: str, max_width: float, ceiling: float) -> float:
    """The largest size, up to `ceiling`, at which `text_str` fits `max_width`."""
    return min(ceiling, ceiling * max_width / width(text_str, font, ceiling))


def text(x: float, y: float, s: str, font: str, size: float, fill: str,
         extra: str = "") -> str:
    return (f'<text x="{x:g}" y="{y:g}" font-family="{FONTS[font]}" '
            f'font-size="{size:g}" fill="{fill}"{extra}>{escape(s)}</text>')


def count_up(x: float, y: float, n: int, font: str, size: float, fill: str,
             start: float, dur: float = 1.0) -> str:
    """A number that counts up from zero to `n`."""
    final = text(x, y, str(n), font, size, fill)
    if STATIC or n < 2:
        return final
    steps = min(n, 14)
    values = sorted({round(n * (1 - (1 - i / steps) ** 2)) for i in range(steps)} - {n})
    each = dur / len(values)
    frames = "".join(
        text(x, y, str(v), font, size, fill,
             f' opacity="0" style="animation:show {each:.3f}s steps(1) '
             f'{start + i * each:.3f}s 1"')
        for i, v in enumerate(values))
    final = text(x, y, str(n), font, size, fill,
                 f' style="animation:wait {start + dur:.3f}s linear 1"')
    return frames + final


COUNT_CSS = ("@keyframes show{from,to{opacity:1}}"
             "@keyframes wait{from,to{opacity:0}}")


def style(fonts: list[str], css: str) -> str:
    faces = "".join(font_face(f, FONTS[f]) for f in fonts)
    motion = "" if STATIC else COUNT_CSS + css
    return (f"<style>{faces}text{{font-kerning:normal}}{motion}"
            "@media (prefers-reduced-motion:reduce){"
            "*{animation:none!important}.shine{fill:#fff!important}}"
            "</style>")


def load_avatar() -> tuple[str, str]:
    png = ROOT / "assets" / "avatar.png"
    if png.exists():
        return "image/png", base64.b64encode(png.read_bytes()).decode()
    jpg = ROOT / "assets" / "avatar.jpg"
    return "image/jpeg", base64.b64encode(jpg.read_bytes()).decode()


def load_days() -> list[dict]:
    path = ROOT / "data" / "contributions.json"
    return json.loads(path.read_text()) if path.exists() else []


def compute_streaks(days: list[dict]) -> tuple[int, int]:
    longest = cur = 0
    for d in days:
        if d["count"] > 0:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0
    rev = list(reversed(days))
    start_idx = 1 if rev and rev[0]["count"] == 0 else 0
    current = 0
    for d in rev[start_idx:]:
        if d["count"] > 0:
            current += 1
        else:
            break
    return current, longest


# ------------------------------------------------------------------ 1. hero

def hero() -> str:
    W, H = 1200, 396
    avatar_mime, avatar = load_avatar()

    full_name = "Muhammad Mubasher"
    size = fit(full_name, "display", 1080, 68)
    intro = wrap(
        "Building modern web applications and exploring practical agentic AI "
        "systems that connect models, APIs, and business workflows.",
        "regular", 24, 1020)

    ring = 2 * 3.14159 * 54
    css = f"""
@keyframes pop{{from{{transform:scale(.6);opacity:0}}}}
@keyframes draw{{from{{stroke-dashoffset:{ring:.0f}}}}}
@keyframes pulse{{0%{{transform:scale(1);opacity:.75}}70%,100%{{transform:scale(1.48);opacity:0}}}}
@keyframes drift{{from{{transform:translate(0,0)}}to{{transform:translate(-180px,70px)}}}}
@keyframes rise{{from{{transform:translateY({size * 1.15:.0f}px)}}}}
@keyframes fade{{from{{opacity:0}}}}
.pop{{transform-box:fill-box;transform-origin:center;animation:pop .6s cubic-bezier(.2,1.4,.4,1) both}}
.draw{{animation:draw 1.1s cubic-bezier(.6,0,.2,1) .15s both}}
.pulse{{transform-box:fill-box;transform-origin:center;animation:pulse 3.2s ease-out 1.5s infinite}}
.glow{{animation:drift 16s ease-in-out infinite alternate}}
.rise{{animation:rise .8s cubic-bezier(.2,.8,.2,1) both}}
.fade{{animation:fade .7s ease both}}
"""
    sweep = "" if STATIC else (
        '<animateTransform attributeName="gradientTransform" type="translate" '
        'values="-0.75 0;0.75 0;0.75 0" keyTimes="0;0.2;1" dur="6.5s" '
        'begin="2.0s" repeatCount="indefinite"/>')

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'aria-label="Muhammad Mubasher - Full-Stack Developer and Agentic AI Developer">',
        style(["display", "semi", "regular"], css),
        "<defs>"
        f'<linearGradient id="ground" x1="0" x2="1" y1="0" y2="0.4">'
        f'<stop offset="0" stop-color="{OBSIDIAN}"/><stop offset="1" stop-color="{UMBER}"/></linearGradient>'
        f'<radialGradient id="glow"><stop offset="0" stop-color="{AMBER}" stop-opacity=".28"/>'
        f'<stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="shine" x1="0" x2="1" gradientTransform="translate(-0.75 0)">'
        '<stop offset=".38" stop-color="#fff"/>'
        f'<stop offset=".5" stop-color="{AMBER}"/>'
        f'<stop offset=".62" stop-color="#fff"/>{sweep}</linearGradient>'
        f'<clipPath id="card"><rect width="{W}" height="{H}" rx="28"/></clipPath>'
        '<clipPath id="face"><circle cx="110" cy="108" r="46"/></clipPath>'
        f'<clipPath id="nameclip"><rect x="50" y="{252 - size:.0f}" width="1100" height="{size + 14:.0f}"/></clipPath>'
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="28" fill="url(#ground)"/>',
        '<g clip-path="url(#card)">'
        '<circle class="glow" cx="1160" cy="40" r="420" fill="url(#glow)"/></g>',

        # Avatar + animated amber ring
        f'<circle class="pulse" cx="110" cy="108" r="54" fill="none" stroke="{AMBER}" stroke-width="2" opacity="0"/>',
        '<g class="pop">'
        f'<image x="60" y="58" width="100" height="100" clip-path="url(#face)" '
        f'xlink:href="data:{avatar_mime};base64,{avatar}" href="data:{avatar_mime};base64,{avatar}"/>'
        "</g>",
        f'<circle class="draw" cx="110" cy="108" r="54" fill="none" stroke="{AMBER}" '
        f'stroke-width="3" stroke-linecap="round" stroke-dasharray="{ring:.0f}" '
        f'transform="rotate(-90 110 108)"/>',

        # Username & role header
        '<g class="fade" style="animation-delay:.25s">',
        text(186, 98, "@mubasherdevv", "semi", 23, "#fff"),
        text(186, 128, "Full-Stack Developer  |  Agentic AI Developer", "semi", 19, AMBER),
        text(186, 154, "Lahore, Pakistan", "regular", 16.5, SOFT),
        "</g>",

        # Full-width sweeping name
        f'<g clip-path="url(#nameclip)"><g class="rise" style="animation-delay:.2s">'
        + text(58, 252, full_name, "display", size, "url(#shine)", ' class="shine"')
        + "</g></g>",

        # Short professional intro
        '<g class="fade" style="animation-delay:.6s">',
    ]
    for i, line in enumerate(intro):
        out.append(text(60, 298 + i * 34, line, "regular", 24, "#F5EFE4"))
    out.append("</g></svg>")
    return "".join(out)


# ----------------------------------------------------------- 2. service cards

def service_card(index: int, svc: dict, theme: str) -> str:
    # Three cards side by side inside "What I Do": 3 * 400 = 1200 full width.
    FULL_W, FULL_H = 400, 260
    W, H = 388, 248
    x0 = (0, 6, 12)[index]
    t = THEMES[theme]
    arrive = 0.25 + index * 0.12
    turn = START + index * SLOT
    lit = STATIC and index == 0

    css = f"""
@keyframes in{{from{{opacity:0;transform:translateY(22px) scale(.97)}}}}
@keyframes on{{{ON}{{opacity:0}}{HELD}{{opacity:1}}}}
@keyframes sweep{{0%{{transform:translateX(0);opacity:1}}{TURN * .55:.3f}%{{transform:translateX({W + 220}px);opacity:1}}{TURN * .56:.3f}%,100%{{transform:translateX({W + 220}px);opacity:0}}}}
@keyframes work{{0%{{transform:scaleX(0);opacity:1}}{TURN - 1.6:.3f}%{{transform:scaleX(1);opacity:1}}{TURN:.3f}%,100%{{transform:scaleX(1);opacity:0}}}}
.in{{transform-box:fill-box;transform-origin:center;animation:in .65s cubic-bezier(.2,.9,.3,1) {arrive:g}s both}}
.hl{{animation:on {LAP:g}s linear {turn:g}s infinite}}
.sw{{animation:sweep {LAP:g}s linear {turn:g}s infinite}}
.wk{{transform-box:fill-box;transform-origin:left;animation:work {LAP:g}s linear {turn:g}s infinite}}
"""
    tag_w = width(svc["tag"], "semi", 12.5) + 22
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FULL_W} {FULL_H}" '
        f'width="{FULL_W}" height="{FULL_H}" role="img" aria-label="{escape(svc["title"])}">',
        style(["semi", "regular"], css),
        "<defs>"
        f'<clipPath id="c"><rect width="{W}" height="{H}" rx="18"/></clipPath>'
        f'<linearGradient id="band" x1="0" x2="1">'
        f'<stop offset="0" stop-color="{t["mark"]}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{t["mark"]}" stop-opacity=".18"/>'
        f'<stop offset="1" stop-color="{t["mark"]}" stop-opacity="0"/></linearGradient>'
        "</defs>",
        f'<g transform="translate({x0} 6)"><g class="in">',
        f'<rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>',
        f'<g clip-path="url(#c)">'
        f'<g transform="skewX(-18)"><rect class="sw" x="-180" y="-10" width="140" '
        f'height="{H + 20}" fill="url(#band)" opacity="0"/></g>'
        f'<rect class="wk" x="0" y="{H - 4}" width="{W}" height="4" fill="{t["mark"]}" opacity="0"/>'
        "</g>",
        f'<rect class="hl" x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" rx="16.5" '
        f'fill="none" stroke="{t["mark"]}" stroke-width="2.5" opacity="{1 if lit else 0}"/>',
        f'<rect x="26" y="24" width="{tag_w:.0f}" height="24" rx="12" fill="{t["pill_bg"]}"/>',
        text(37, 40, svc["tag"], "semi", 12.5, t["pill_fg"]),
        text(26, 82, svc["title"], "semi", 22, t["title"]),
    ]
    for i, line in enumerate(wrap(svc["blurb"], "regular", 16.5, W - 52)):
        out.append(text(26, 114 + i * 24, line, "regular", 16.5, t["body"]))

    out.append(f'<circle cx="32" cy="{H - 28}" r="4.5" fill="{t["mark"]}"/>')
    out.append(text(45, H - 23, svc["foot"], "semi", 14, t["body"]))
    out.append("</g></g></svg>")
    return "".join(out)


# --------------------------------------------------------- 4. education card

def education_card(theme: str) -> str:
    W, H = 1200, 206
    t = THEMES[theme]
    items = [
        {
            "degree": "DAE, Computer Information Technology",
            "school": "Malaysian Institute of Technology",
            "years": "2022 - 2025",
        },
        {
            "degree": "Matric, Computer Science",
            "school": "Govt. Farooqi Islamia Boys High School",
            "years": "2019 - 2022",
        },
    ]

    css = """
@keyframes fade{from{opacity:0;transform:translateY(10px)}}
.ed{animation:fade .6s ease both}
"""
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" aria-label="Education timeline">',
        style(["semi", "regular"], css),
        f'<rect width="{W}" height="{H}" rx="20" fill="{t["bg"]}"/>',
        f'<line x1="64" y1="54" x2="64" y2="144" stroke="{t["mark"]}" stroke-width="2.5" stroke-opacity=".45"/>',
    ]
    for i, item in enumerate(items):
        y = 58 + i * 86
        pill_w = width(item["years"], "semi", 15) + 28
        out.append(f'<g class="ed" style="animation-delay:{0.15 + i * 0.18:.2f}s">')
        out.append(f'<circle cx="64" cy="{y}" r="8" fill="{t["bg"]}" stroke="{t["mark"]}" stroke-width="3"/>')
        out.append(f'<circle cx="64" cy="{y}" r="3.5" fill="{t["mark"]}"/>')
        out.append(text(94, y + 2, item["degree"], "semi", 22, t["title"]))
        out.append(text(94, y + 30, item["school"], "regular", 17.5, t["body"]))
        px = W - 44 - pill_w
        out.append(f'<rect x="{px:.0f}" y="{y - 16}" width="{pill_w:.0f}" height="30" rx="15" fill="{t["pill_bg"]}"/>')
        out.append(text(px + 14, y + 4, item["years"], "semi", 15, t["pill_fg"]))
        out.append("</g>")
    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------------ 5. stats card

def stats_card(theme: str) -> str:
    W, H = 1200, 246
    t = THEMES[theme]
    days = load_days()
    total_contribs = sum(d["count"] for d in days)
    active_days = sum(1 for d in days if d["count"] > 0)
    cur_streak, best_streak = compute_streaks(days)
    best_day = max(days, key=lambda d: d["count"]) if days else None

    stars = DATA.get("total_stars", 0)
    repos = DATA.get("public_repos", 0)

    lang_counts: dict[str, int] = {}
    for info in DATA.get("repos", {}).values():
        lg = info.get("language")
        if lg:
            lang_counts[lg] = lang_counts.get(lg, 0) + 1
    total_lang = sum(lang_counts.values()) or 1
    top_langs = sorted(lang_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:4]

    MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    best_label = "N/A"
    if best_day and best_day["count"]:
        dt = date.fromisoformat(best_day["date"])
        best_label = f"{best_day['count']} on {dt.day} {MONTHS[dt.month - 1]}"

    css = """
@keyframes fade{from{opacity:0;transform:translateY(10px)}}
@keyframes bar{from{transform:scaleX(0)}}
.st{animation:fade .6s ease both}
.br{transform-box:fill-box;transform-origin:left;animation:bar .8s cubic-bezier(.2,.8,.2,1) .3s both}
"""
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" aria-label="GitHub profile statistics, streak, and top languages">',
        style(["semi", "regular"], css),
        f'<rect width="{W}" height="{H}" rx="20" fill="{t["bg"]}"/>',
        f'<line x1="400" y1="32" x2="400" y2="{H - 32}" stroke="{t["panel"]}" stroke-width="2"/>',
        f'<line x1="800" y1="32" x2="800" y2="{H - 32}" stroke="{t["panel"]}" stroke-width="2"/>',
    ]

    # Column 1: Profile Statistics
    out.append('<g class="st" style="animation-delay:.1s">')
    out.append(text(38, 48, "PROFILE STATISTICS", "semi", 13.5, t["mark"]))
    out.append(count_up(38, 96, total_contribs, "semi", 34, t["title"], start=0.25))
    out.append(text(38, 122, "contributions in the last year", "regular", 16, t["body"]))
    out.append(text(38, 166, f"Public Repositories: {repos}", "semi", 17.5, t["title"]))
    out.append(text(38, 198, f"Total Stars Earned: {stars}   |   Active Days: {active_days}", "regular", 15.5, t["body"]))
    out.append("</g>")

    # Column 2: Contribution Streak
    out.append('<g class="st" style="animation-delay:.22s">')
    out.append(text(436, 48, "CONTRIBUTION STREAK", "semi", 13.5, t["mark"]))
    out.append(count_up(436, 96, cur_streak, "semi", 34, t["mark"], start=0.35))
    cw = width(str(cur_streak), "semi", 34)
    out.append(text(436 + cw + 10, 96, "days", "semi", 22, t["title"]))
    out.append(text(436, 122, "current active streak", "regular", 16, t["body"]))
    out.append(text(436, 166, f"Longest Streak: {best_streak} days", "semi", 17.5, t["title"]))
    out.append(text(436, 198, f"Busiest Day: {best_label}", "regular", 15.5, t["body"]))
    out.append("</g>")

    # Column 3: Most-Used Languages
    out.append('<g class="st" style="animation-delay:.34s">')
    out.append(text(836, 48, "MOST-USED LANGUAGES", "semi", 13.5, t["mark"]))
    bar_x, bar_y, bar_w, bar_h = 836, 74, 326, 14
    out.append(f'<clipPath id="lbar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="7"/></clipPath>')
    out.append(f'<g clip-path="url(#lbar)"><g class="br">')
    cx = float(bar_x)
    for lg, cnt in top_langs:
        seg = bar_w * cnt / total_lang
        col = LANG.get(lg, t["body"])
        out.append(f'<rect x="{cx:.1f}" y="{bar_y}" width="{seg + 1:.1f}" height="{bar_h}" fill="{col}"/>')
        cx += seg
    out.append("</g></g>")

    for idx, (lg, cnt) in enumerate(top_langs):
        pct = round(100 * cnt / total_lang)
        col = LANG.get(lg, t["body"])
        ly = 122 + idx * 30
        out.append(f'<circle cx="843" cy="{ly - 5}" r="5.5" fill="{col}"/>')
        out.append(text(858, ly, lg, "semi", 16.5, t["title"]))
        pct_str = f"{pct}%"
        pw = width(pct_str, "regular", 16)
        out.append(text(1162 - pw, ly, pct_str, "regular", 16, t["body"]))
    out.append("</g>")

    out.append("</svg>")
    return "".join(out)


# --------------------------------------------------------- 3. tech stack card

TECH_ICONS = {
    "code": '<path d="M8 7l-5 5 5 5M16 7l5 5-5 5M13 5l-2 14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    "web": '<path d="M4 5h16l-1.5 13-6.5 2-6.5-2z" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/><path d="M8 10h8M9 14h6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
    "react": '<circle cx="12" cy="12" r="2.2" fill="currentColor"/><ellipse cx="12" cy="12" rx="9" ry="3.8" stroke="currentColor" stroke-width="1.7" fill="none"/><ellipse cx="12" cy="12" rx="9" ry="3.8" transform="rotate(60 12 12)" stroke="currentColor" stroke-width="1.7" fill="none"/><ellipse cx="12" cy="12" rx="9" ry="3.8" transform="rotate(120 12 12)" stroke="currentColor" stroke-width="1.7" fill="none"/>',
    "next": '<circle cx="12" cy="12" r="8.5" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M9 16V8l7 9V8" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    "style": '<path d="M3 13c1.5-3 3.5-4 5.5-2.5 2 1.5 3.5 1 4.5-1.5 1.5-2.5 3.5-3 5.5-1.5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/><path d="M5 17c1.5-3 3.5-4 5.5-2.5 2 1.5 3.5 1 4.5-1.5 1.5-2.5 3.5-3 5.5-1.5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>',
    "node": '<polygon points="12,3 20,7.5 20,16.5 12,21 4,16.5 4,7.5" stroke="currentColor" stroke-width="1.9" fill="none" stroke-linejoin="round"/><circle cx="12" cy="12" r="2.2" fill="currentColor"/>',
    "bolt": '<polygon points="13,2 5,13 11,13 10,22 19,10 13,10" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linejoin="round"/>',
    "db": '<ellipse cx="12" cy="6" rx="7" ry="2.8" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M5 6v12c0 1.6 3.1 2.8 7 2.8s7-1.2 7-2.8V6" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M5 12c0 1.6 3.1 2.8 7 2.8s7-1.2 7-2.8" stroke="currentColor" stroke-width="1.8" fill="none"/>',
    "api": '<path d="M9 7H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h3M15 7h3a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-3M9 12h6" stroke="currentColor" stroke-width="1.9" fill="none" stroke-linecap="round"/>',
    "ai": '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linejoin="round"/><circle cx="18.5" cy="5.5" r="1.3" fill="currentColor"/>',
    "flow": '<circle cx="5.5" cy="12" r="2.3" stroke="currentColor" stroke-width="1.8" fill="none"/><circle cx="18.5" cy="7" r="2.3" stroke="currentColor" stroke-width="1.8" fill="none"/><circle cx="18.5" cy="17" r="2.3" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M8 12h4l4-4M12 12l4 4" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/>',
    "sheet": '<rect x="4" y="4" width="16" height="16" rx="2.5" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M4 10h16M4 15h16M10 4v16" stroke="currentColor" stroke-width="1.7"/>',
    "cms": '<circle cx="12" cy="12" r="8.5" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M7 9l2.5 7 2.5-6 2.5 6L17 9" stroke="currentColor" stroke-width="1.7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    "layout": '<rect x="4" y="4" width="16" height="16" rx="2.5" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M8 8h8M8 12h5M8 16h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "git": '<circle cx="6.5" cy="6.5" r="2.2" stroke="currentColor" stroke-width="1.8" fill="none"/><circle cx="6.5" cy="17.5" r="2.2" stroke="currentColor" stroke-width="1.8" fill="none"/><circle cx="17.5" cy="9.5" r="2.2" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M6.5 8.7v6.6M6.5 14c0-3 11-1 11-2.3" stroke="currentColor" stroke-width="1.8" fill="none"/>',
    "box": '<rect x="3" y="11" width="18" height="7" rx="2" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M7 11V7h4v4M11 7h4v4M7 7V4" stroke="currentColor" stroke-width="1.7" fill="none" stroke-linejoin="round"/>',
}

TECH_STACK = [
    ("Programming Languages", [
        ("JavaScript", "code"), ("TypeScript", "code"), ("Python", "code"),
        ("HTML", "web"), ("CSS", "style"), ("PHP", "code"),
    ]),
    ("Frontend Technologies", [
        ("React", "react"), ("Next.js", "next"),
        ("Tailwind CSS", "style"), ("Bootstrap", "layout"),
    ]),
    ("Backend & Databases", [
        ("Node.js", "node"), ("Supabase", "bolt"), ("MySQL", "db"),
        ("MongoDB", "db"), ("REST APIs", "api"), ("JSON", "code"),
    ]),
    ("AI & Automation", [
        ("OpenAI API", "ai"), ("Gemini API", "ai"), ("n8n", "flow"),
        ("Webhooks", "api"), ("Google Sheets", "sheet"),
    ]),
    ("CMS", [
        ("WordPress", "cms"), ("Elementor", "layout"),
    ]),
    ("Tools & DevOps", [
        ("Git", "git"), ("GitHub", "git"), ("VS Code", "code"), ("Docker", "box"),
    ]),
]


def techstack_card(theme: str) -> str:
    W, row_h = 1200, 58
    H = 44 + len(TECH_STACK) * row_h + 16
    t = THEMES[theme]

    css = """
@keyframes fade{from{opacity:0;transform:translateY(8px)}}
.ts{animation:fade .55s ease both}
"""
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" aria-label="Technical stack and tools">',
        style(["semi", "regular"], css),
        f'<rect width="{W}" height="{H}" rx="20" fill="{t["bg"]}"/>',
    ]

    for idx, (category, items) in enumerate(TECH_STACK):
        ry = 34 + idx * row_h
        if idx > 0:
            out.append(f'<line x1="36" y1="{ry - 10}" x2="{W - 36}" y2="{ry - 10}" stroke="{t["panel"]}" stroke-width="1.5"/>')
        out.append(f'<g class="ts" style="animation-delay:{0.08 + idx * 0.08:.2f}s">')
        out.append(text(40, ry + 25, category, "semi", 16.5, t["title"]))

        px = 296.0
        for label, icon_key in items:
            lw = width(label, "semi", 14.5)
            pw = 12 + 16 + 8 + lw + 14
            out.append(
                f'<rect x="{px:.1f}" y="{ry + 2}" width="{pw:.1f}" height="34" '
                f'rx="10" fill="{t["panel"]}"/>')
            out.append(
                f'<svg x="{px + 11:.1f}" y="{ry + 11}" width="16" height="16" '
                f'viewBox="0 0 24 24" color="{t["mark"]}">{TECH_ICONS[icon_key]}</svg>')
            out.append(text(px + 34, ry + 24, label, "semi", 14.5, t["title"]))
            px += pw + 10
        out.append("</g>")

    out.append("</svg>")
    return "".join(out)


# ----------------------------------------------------------- projects cards

STAR = ("M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 "
        ".416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347"
        "l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 "
        "0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z")

PROJECTS = [
    {
        "key": "securesite",
        "repo": "website_builder",
        "title": "SecureSite Studio - Website Builder",
        "tag": "Next.js / Supabase",
        "desc": "Website-builder platform with Next.js, TypeScript, Tailwind CSS, Zod schemas, dynamic page renderer, and Supabase.",
    },
    {
        "key": "snapbite",
        "repo": "snap-bite",
        "title": "Snap Bite - AI Calorie Tracker",
        "tag": "AI / TypeScript",
        "desc": "AI-powered calorie and nutrition tracking web application built with TypeScript and LLM integrations.",
    },
    {
        "key": "n8n",
        "repo": "emailautomation",
        "title": "AI & Workflow Automation",
        "tag": "n8n / OpenAI & Gemini",
        "desc": "Automated workflows integrating OpenAI and Gemini APIs, webhooks, email pipelines, and business processes.",
    },
    {
        "key": "whatsapp",
        "repo": "",
        "title": "WhatsApp Restaurant Ordering Workflow",
        "tag": "WhatsApp / Google Sheets",
        "desc": "Automation concept connecting WhatsApp customer ordering with Google Sheets menu/inventory and interactive options.",
    },
    {
        "key": "leads",
        "repo": "auto-dm-insta",
        "title": "Lead Collection & Outreach Workflow",
        "tag": "n8n / Automation",
        "desc": "Workflow automation to collect business contact details from websites, automate outreach, and organize results in Sheets.",
    },
    {
        "key": "seo",
        "repo": "seo-auto-filler",
        "title": "SEO Auto-Filler & Citation Tool",
        "tag": "SEO Automation",
        "desc": "Streamlines off-page SEO form filling, business directory submissions, and citation workflows.",
    },
]

PROJ_LAP = SLOT * len(PROJECTS)
PROJ_TURN = 100 / len(PROJECTS)
PROJ_ON = f"0%,{PROJ_TURN:.3f}%,100%"
PROJ_HELD = f"1.5%,{PROJ_TURN - 1.6:.3f}%"


def project_card(index: int, proj: dict, theme: str) -> str:
    FULL_W, FULL_H = 1200, 118
    W, H = 1200, 108
    t = THEMES[theme]
    repo = DATA.get("repos", {}).get(proj["repo"], {})
    stars = repo.get("stars", 0)
    lang = repo.get("language") or ""

    arrive = 0.1 + index * 0.08
    turn = START + index * SLOT
    lit = STATIC and index == 0

    css = f"""
@keyframes in{{from{{opacity:0;transform:translateY(14px)}}}}
@keyframes on{{{PROJ_ON}{{opacity:0}}{PROJ_HELD}{{opacity:1}}}}
@keyframes work{{0%{{transform:scaleX(0);opacity:1}}{PROJ_TURN - 1.6:.3f}%{{transform:scaleX(1);opacity:1}}{PROJ_TURN:.3f}%,100%{{transform:scaleX(1);opacity:0}}}}
.in{{animation:in .55s ease {arrive:g}s both}}
.hl{{animation:on {PROJ_LAP:g}s linear {turn:g}s infinite}}
.wk{{transform-box:fill-box;transform-origin:left;animation:work {PROJ_LAP:g}s linear {turn:g}s infinite}}
"""
    title_w = width(proj["title"], "semi", 21)
    pill_x = 34 + title_w + 14
    pill_w = width(proj["tag"], "semi", 12.5) + 20

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FULL_W} {FULL_H}" '
        f'width="{FULL_W}" height="{FULL_H}" role="img" aria-label="{escape(proj["title"])}">',
        style(["semi", "regular"], css),
        "<defs>"
        f'<clipPath id="pc"><rect width="{W}" height="{H}" rx="16"/></clipPath>'
        "</defs>",
        '<g class="in">',
        f'<rect width="{W}" height="{H}" rx="16" fill="{t["bg"]}"/>',
        f'<g clip-path="url(#pc)">'
        f'<rect class="wk" x="0" y="{H - 3.5}" width="{W}" height="3.5" fill="{t["mark"]}" opacity="0"/>'
        "</g>",
        f'<rect class="hl" x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" rx="14.5" '
        f'fill="none" stroke="{t["mark"]}" stroke-width="2.5" opacity="{1 if lit else 0}"/>',
        text(34, 44, proj["title"], "semi", 21, t["title"]),
        f'<rect x="{pill_x:.0f}" y="25" width="{pill_w:.0f}" height="24" rx="12" fill="{t["pill_bg"]}"/>',
        text(pill_x + 10, 41, proj["tag"], "semi", 12.5, t["pill_fg"]),
        text(34, 78, proj["desc"], "regular", 16, t["body"]),
    ]

    rx = 1164.0
    if stars:
        s_txt = str(stars)
        sw = width(s_txt, "semi", 16)
        rx -= sw
        out.append(text(rx, 44, s_txt, "semi", 16, t["title"]))
        rx -= 22
        out.append(f'<g transform="translate({rx:g} 30) scale(1.02)">'
                   f'<path fill="{t["mark"]}" d="{STAR}"/></g>')
        rx -= 22
    if lang:
        lw = width(lang, "regular", 15.5)
        rx -= lw
        out.append(text(rx, 44, lang, "regular", 15.5, t["body"]))
        rx -= 16
        out.append(f'<circle cx="{rx:g}" cy="38.5" r="5.5" fill="{LANG.get(lang, t["body"])}"/>')

    out.append("</g></svg>")
    return "".join(out)


# ------------------------------------------------------- contribution graph

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

LEVELS = {
    "light": ["#E6E0D3", "#F6D59B", "#EEB14F", "#D98218", "#9C5409"],
    "dark": ["#2A2620", "#5C3D12", "#8F5F14", "#C8841B", AMBER],
}


def graph(theme: str) -> str:
    days = load_days()
    t = THEMES[theme]
    W, H = 1200, 336
    left, top = 40, 146

    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"])
    best = max(days, key=lambda d: d["count"]) if days else None

    first = date.fromisoformat(days[0]["date"]) if days else date.today()
    offset = (first.weekday() + 1) % 7

    ncols = (len(days) + offset + 6) // 7 or 53
    pitch = (W - 2 * left) / ncols
    gap = pitch * .19
    cell = pitch - gap

    css = f"""
@keyframes pop{{from{{transform:scale(0);opacity:0}}}}
@keyframes now{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.35)}}}}
@keyframes fade{{from{{opacity:0}}}}
.col{{animation:fade .01s both}}
.col rect{{transform-box:fill-box;transform-origin:center;animation:pop .35s cubic-bezier(.2,1.5,.4,1) both;animation-delay:inherit}}
.now{{transform-box:fill-box;transform-origin:center;animation:now 1.8s ease-in-out 3s infinite}}
.fade{{animation:fade .7s ease both}}
"""
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" '
        f'aria-label="{total} contributions in the last year">',
        style(["semi", "regular"], css),
        f'<rect width="{W}" height="{H}" rx="20" fill="{t["bg"]}"/>',
        '<g class="fade">',
        count_up(left, 62, total, "semi", 30, t["title"], start=.3, dur=1.1),
        text(left + width(f"{total} ", "semi", 30), 62,
             "contributions in the last year", "semi", 30, t["title"]),
    ]
    facts = [f"{active} active day{'s' if active != 1 else ''}"]
    if best and best["count"]:
        d = date.fromisoformat(best["date"])
        facts.append(f"busiest day {d.day} {MONTHS[d.month - 1]} "
                     f"with {best['count']}")
    out.append(text(left, 92, ", ".join(facts), "regular", 19, t["body"]))
    out.append("</g>")

    seen = set()
    for i, d in enumerate(days):
        dt = date.fromisoformat(d["date"])
        col = (i + offset) // 7
        if dt.day <= 7 and (dt.year, dt.month) not in seen and col < ncols - 2:
            seen.add((dt.year, dt.month))
            out.append(text(left + col * pitch, top - 12,
                            MONTHS[dt.month - 1], "regular", 15, t["body"]))

    cols: dict[int, list[str]] = {}
    for i, d in enumerate(days):
        col, row = divmod(i + offset, 7)
        last = i == len(days) - 1
        fill = LEVELS[theme][d["level"]]
        cls = ' class="now"' if last and not STATIC else ""
        cols.setdefault(col, []).append(
            f'<rect{cls} x="{left + col * pitch:.1f}" '
            f'y="{top + row * pitch:.1f}" width="{cell:.1f}" height="{cell:.1f}" '
            f'rx="3.5" fill="{fill}"/>')
    for col, rects in cols.items():
        out.append(f'<g class="col" style="animation-delay:{.6 + col * .022:.3f}s">'
                   + "".join(rects) + "</g>")

    kx = W - left - 5 * pitch - 40
    ky = top + 7 * pitch + 12
    out.append(text(kx - 42, ky + 14, "Less", "regular", 15, t["body"]))
    for i, c in enumerate(LEVELS[theme]):
        out.append(f'<rect x="{kx + i * pitch:.1f}" y="{ky:.1f}" width="{cell:.1f}" '
                   f'height="{cell:.1f}" rx="3.5" fill="{c}"/>')
    out.append(text(kx + 5 * pitch + 6, ky + 14, "More", "regular", 15, t["body"]))

    out.append("</svg>")
    return "".join(out)


def main() -> None:
    CARDS.mkdir(exist_ok=True)
    (CARDS / "hero.svg").write_text(hero())
    for theme in THEMES:
        (CARDS / f"techstack-{theme}.svg").write_text(techstack_card(theme))
        (CARDS / f"education-{theme}.svg").write_text(education_card(theme))
        (CARDS / f"stats-{theme}.svg").write_text(stats_card(theme))
        (CARDS / f"graph-{theme}.svg").write_text(graph(theme))
    for i, svc in enumerate(SERVICES):
        for theme in THEMES:
            (CARDS / f"service-{svc['key']}-{theme}.svg").write_text(
                service_card(i, svc, theme))
    for i, proj in enumerate(PROJECTS):
        for theme in THEMES:
            (CARDS / f"project-{proj['key']}-{theme}.svg").write_text(
                project_card(i, proj, theme))
    for f in sorted(CARDS.glob("*.svg")):
        print(f"{f.name:28} {f.stat().st_size / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
