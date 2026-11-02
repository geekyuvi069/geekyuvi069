"""Neon graphics for the profile README.

  python3 scripts/neon.py                  rebuild assets/*.svg (fetches icons from jsDelivr)
  python3 scripts/neon.py --stats OUT.svg  live activity card; needs GITHUB_TOKEN and USERNAME
"""
import base64
import datetime
import html
import json
import math
import os
import pathlib
import random
import re
import sys
import textwrap
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ICON_URL = "https://cdn.jsdelivr.net/npm/simple-icons@16.36.0/icons/{}.svg"
# simple-icons dropped LinkedIn; this is its last published path
LINKEDIN = ("M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046"
            "c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 1 1 0-4.125 2.062 2.062 0 0 1 0 4.125z"
            "M7.119 20.452H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 "
            "24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z")

BG, PANEL = "#070512", "#0d0a22"
CYAN, VIOLET, MAGENTA, GREEN = "#22d3ee", "#a78bfa", "#e879f9", "#4ade80"
TEXT, MUTED = "#ecebff", "#a5a3c9"
MONO = "'JetBrains Mono',ui-monospace,Menlo,Consolas,monospace"
SANS = "Inter,'Segoe UI',Helvetica,Arial,sans-serif"
DISPLAY = "Orbitron,'Segoe UI',Helvetica,Arial,sans-serif"


def mw(s, size):
    """Width of JetBrains Mono text: every glyph advances .6em, so mono text can be laid out exactly."""
    return len(s) * size * .6


def dot_w(s):
    """Width of a live_dot label (13px mono with 2px letter-spacing)."""
    return mw(s, 13) + 2 * len(s)


def _font(family, weight, file):
    data = base64.b64encode((ASSETS / "fonts" / file).read_bytes()).decode()
    return f"@font-face{{font-family:'{family}';font-weight:{weight};src:url(data:font/woff2;base64,{data}) format('woff2')}}"


FONTS = {
    "display": lambda: _font("Orbitron", 700, "orbitron-latin-700-normal.woff2") + _font("Orbitron", 900, "orbitron-latin-900-normal.woff2"),
    "sans": lambda: _font("Inter", 400, "inter-latin-400-normal.woff2"),
    "mono": lambda: _font("JetBrains Mono", 400, "jetbrains-mono-latin-400-normal.woff2"),
}

CSS = f"""
.num{{font:400 15px {MONO};fill:{MAGENTA};letter-spacing:2px}}
.h{{font:700 24px {DISPLAY};letter-spacing:3px}}
.body{{font:400 16px {MONO};fill:{MUTED}}}
.small{{font:400 13px {MONO}}}
.pulse{{animation:pulse 2s ease-in-out infinite}}
.orbit{{fill:none;stroke:{VIOLET};stroke-opacity:.35;stroke-dasharray:3 9;transform-box:fill-box;transform-origin:center;animation:spin 40s linear infinite}}
.scan{{animation:scan 5s linear infinite}}
@keyframes pulse{{50%{{opacity:.3}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@keyframes scan{{from{{transform:translateY(-90px)}}to{{transform:translateY(var(--h,400px))}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""


def svg(w, h, title, body, css="", fonts=("mono", "display")):
    defs = f"""<defs>
<linearGradient id="ng" x1="0" x2="1" spreadMethod="reflect"><stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{MAGENTA}"/><animateTransform attributeName="gradientTransform" type="translate" values="0 0;1 0;0 0" dur="8s" repeatCount="indefinite"/></linearGradient>
<linearGradient id="ngu" gradientUnits="userSpaceOnUse" x1="0" x2="{w}"><stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{MAGENTA}"/></linearGradient>
<linearGradient id="scanfill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset=".5" stop-color="{CYAN}" stop-opacity=".07"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>
<filter id="glow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="3.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="soft" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="12"/></filter>
<filter id="blur" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="40"/></filter>
<pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="{VIOLET}" stroke-opacity=".08"/></pattern>
</defs>"""
    style = "".join(FONTS[f]() for f in fonts) + CSS + css
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t" style="--h:{h}px">'
            f'<title id="t">{html.escape(title)}</title>{defs}<style>{style}</style>{body}</svg>')


def panel(w, h, inner="", rx=22):
    return (f'<clipPath id="clip"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{rx}"/></clipPath>'
            f'<g clip-path="url(#clip)"><rect width="{w}" height="{h}" fill="{BG}"/><rect width="{w}" height="{h}" fill="url(#grid)"/>'
            f'<rect class="scan" width="{w}" height="90" fill="url(#scanfill)"/>{inner}</g>'
            f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{rx}" fill="none" stroke="url(#ng)" stroke-opacity=".7" stroke-width="1.5"/>')


def heading(w, num, label, y=56, right=None):
    start = 76 + len(label) * 24 * .95 + 24  # Orbitron caps run ~.95em
    end = right or w - 32
    return (f'<text class="num" x="32" y="{y}">{num:02d}</text>'
            f'<text class="h" x="76" y="{y + 1}" fill="url(#ng)" filter="url(#glow)">{label}</text>'
            f'<line x1="{start:.0f}" y1="{y - 8}" x2="{end}" y2="{y - 8}" stroke="url(#ngu)" stroke-opacity=".35"/>'
            f'<circle r="3" cx="{start:.0f}" cy="{y - 8}" fill="{CYAN}" filter="url(#glow)">'
            f'<animate attributeName="cx" values="{start:.0f};{end}" dur="3s" repeatCount="indefinite"/></circle>')


def chip(x, y, label, color, size=13):
    w = mw(label, size) + 24
    return (f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="28" rx="14" fill="{color}" fill-opacity=".08" stroke="{color}" stroke-opacity=".55"/>'
            f'<text class="small" x="{x + w / 2:.0f}" y="{y + 19}" text-anchor="middle" font-size="{size}" fill="{color}">{html.escape(label)}</text>'), w


def live_dot(x, y, label, color=GREEN):
    return (f'<circle class="pulse" cx="{x}" cy="{y}" r="9" fill="{color}" fill-opacity=".25"/><circle cx="{x}" cy="{y}" r="4" fill="{color}"/>'
            f'<text class="small" x="{x + 14}" y="{y + 5}" fill="{color}" letter-spacing="2">{label}</text>')


# ---------------------------------------------------------------- static graphics

TAGLINES = ["I build multi-agent LLM systems that show their work.",
            "R&amp;D Intern at Fortinet, building agents for Kubernetes incidents.",
            "LangGraph · MCP · RAG · evals · OpenTelemetry"]


def hero():
    w, h, horizon = 1200, 440, 305
    rnd = random.Random(7)
    stars = "".join(f'<circle class="star" cx="{rnd.uniform(20, w - 20):.0f}" cy="{rnd.uniform(15, horizon - 10):.0f}" '
                    f'r="{rnd.choice((.7, 1, 1.4))}" style="animation-delay:{rnd.uniform(0, 4):.1f}s"/>' for _ in range(70))
    verts = "".join(f'<line x1="{w // 2}" y1="{horizon}" x2="{x}" y2="{h}"/>' for x in range(-1800, 3001, 150))

    def depth(t):  # perspective: floor lines bunch up near the horizon
        return horizon + (h - horizon) * t * t
    floor = "".join(
        f'<line x1="0" x2="{w}" y1="{depth(i / 8):.1f}" y2="{depth(i / 8):.1f}">'
        + "".join(f'<animate attributeName="{a}" values="{";".join(f"{depth((i + k / 10) / 8):.1f}" for k in range(11))}" '
                  f'dur="1.6s" repeatCount="indefinite"/>' for a in ("y1", "y2"))
        + "</line>" for i in range(8))
    tags = "".join(f'<text class="tag t{i + 1}" x="{w // 2}" y="234" text-anchor="middle">{t}</text>' for i, t in enumerate(TAGLINES))
    status = "OPEN TO FULL-TIME AI/ML ROLES"
    cw = dot_w(status) + 48
    css = f"""
.star{{fill:#fff;animation:tw 3s ease-in-out infinite}} @keyframes tw{{50%{{opacity:.15}}}}
.a1{{animation:d1 14s ease-in-out infinite}} .a2{{animation:d2 16s ease-in-out infinite}} .a3{{animation:d1 18s ease-in-out infinite reverse}}
@keyframes d1{{50%{{transform:translate(90px,25px)}}}} @keyframes d2{{50%{{transform:translate(-110px,30px)}}}}
.eyebrow{{font:400 16px {MONO};letter-spacing:6px;fill:{CYAN}}}
.name{{font:900 74px {DISPLAY};letter-spacing:4px}}
.tag{{font:400 23px {SANS};fill:#d4d3ff;opacity:0;animation:rot 12s infinite}} .t2{{animation-delay:4s}} .t3{{animation-delay:8s}}
@keyframes rot{{0%{{opacity:0;transform:translateY(8px)}}4%,30%{{opacity:1;transform:none}}34%,100%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.t1{{opacity:1}}}}"""
    body = f"""<defs><linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset=".45" stop-color="{BG}" stop-opacity="0"/></linearGradient></defs>
<clipPath id="card"><rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="26"/></clipPath>
<g clip-path="url(#card)">
<rect width="{w}" height="{h}" fill="{BG}"/>
<g filter="url(#blur)" opacity=".6"><ellipse class="a1" cx="260" cy="120" rx="280" ry="110" fill="{CYAN}" fill-opacity=".45"/>
<ellipse class="a2" cx="940" cy="110" rx="300" ry="120" fill="{MAGENTA}" fill-opacity=".45"/><ellipse class="a3" cx="600" cy="40" rx="260" ry="90" fill="{VIOLET}" fill-opacity=".5"/></g>
{stars}
<g stroke="{MAGENTA}" stroke-opacity=".5" stroke-width="1.2">{verts}{floor}</g>
<rect y="{horizon}" width="{w}" height="{h - horizon}" fill="url(#fade)"/>
<line x1="0" y1="{horizon}" x2="{w}" y2="{horizon}" stroke="{MAGENTA}" stroke-width="2" filter="url(#glow)"/>
<rect class="scan" width="{w}" height="90" fill="url(#scanfill)"/>
</g>
<rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="26" fill="none" stroke="url(#ng)" stroke-width="2"/>
<text class="eyebrow" x="{w // 2}" y="98" text-anchor="middle">&lt; AI/ML ENGINEER /&gt;</text>
<text class="name" x="{w // 2}" y="182" text-anchor="middle" fill="url(#ng)" filter="url(#soft)" opacity=".85">YUVRAJ KUMAR</text>
<text class="name" x="{w // 2}" y="182" text-anchor="middle" fill="url(#ng)" filter="url(#glow)">YUVRAJ KUMAR</text>
{tags}
<rect x="{(w - cw) / 2:.0f}" y="252" width="{cw:.0f}" height="30" rx="15" fill="{GREEN}" fill-opacity=".08" stroke="{GREEN}" stroke-opacity=".5"/>
{live_dot((w - cw) / 2 + 20, 267, status)}"""
    return svg(w, h, "Yuvraj Kumar, AI/ML Engineer building multi-agent LLM systems. Open to full-time AI/ML roles.", body, css,
               fonts=("mono", "display", "sans"))


def button(label, icon_d, delay):
    w, h = 260, 64
    css = f"""
.btn{{font:700 15px {DISPLAY};letter-spacing:3px;fill:{TEXT}}}
.shine{{animation:shine 3.5s ease-in-out infinite;animation-delay:{delay}s}} @keyframes shine{{0%{{transform:translateX(0)}}60%,100%{{transform:translateX(420px)}}}}"""
    body = f"""<defs><linearGradient id="sh"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
<clipPath id="pill"><rect x="4" y="4" width="{w - 8}" height="{h - 8}" rx="{(h - 8) // 2}"/></clipPath>
<rect x="4" y="4" width="{w - 8}" height="{h - 8}" rx="{(h - 8) // 2}" fill="{PANEL}"/>
<g clip-path="url(#pill)"><polygon class="shine" points="-90,0 -40,0 -70,{h} -120,{h}" fill="url(#sh)"/></g>
<rect x="4" y="4" width="{w - 8}" height="{h - 8}" rx="{(h - 8) // 2}" fill="none" stroke="url(#ng)" stroke-width="2" filter="url(#glow)"/>
<path transform="translate(32 21) scale(.9167)" d="{icon_d}" fill="url(#ng)"/>
<text class="btn" x="{(66 + w - 24) / 2:.0f}" y="38" text-anchor="middle">{label}</text>"""
    return svg(w, h, label, body, css, fonts=("display",))


def graph(hx, hy, r):
    names = ["llm", "mcp", "evals", "otel", "rag"]
    pts = [(hx + r * math.cos(math.radians(-90 + 72 * i)), hy + r * math.sin(math.radians(-90 + 72 * i))) for i in range(5)]
    out = [f'<circle class="orbit" cx="{hx}" cy="{hy}" r="{r + 24}"/>', f'<circle class="orbit" cx="{hx}" cy="{hy}" r="{r // 2}" style="animation-direction:reverse"/>']
    for i, (x, y) in enumerate(pts):
        out.append(f'<line x1="{hx}" y1="{hy}" x2="{x:.0f}" y2="{y:.0f}" stroke="url(#ngu)" stroke-opacity=".55"/>')
        out.append(f'<circle r="3.5" fill="{(MAGENTA, CYAN)[i % 2]}" filter="url(#glow)"><animateMotion dur="2.2s" begin="-{i * .45:.2f}s" '
                   f'repeatCount="indefinite" path="M{hx},{hy}L{x:.0f},{y:.0f}"/></circle>')
    for i, ((x, y), name) in enumerate(zip(pts, names)):
        a = math.radians(-90 + 72 * i)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="7" fill="{PANEL}" stroke="{CYAN}" stroke-width="2" filter="url(#glow)"/>'
                   f'<text class="small" x="{hx + (r + 28) * math.cos(a):.0f}" y="{hy + (r + 28) * math.sin(a) + 5:.0f}" text-anchor="middle" fill="{MUTED}">{name}</text>')
    out.append(f'<circle class="pulse" cx="{hx}" cy="{hy}" r="26" fill="none" stroke="{MAGENTA}" stroke-opacity=".6"/>'
               f'<circle cx="{hx}" cy="{hy}" r="15" fill="{PANEL}" stroke="url(#ng)" stroke-width="2" filter="url(#glow)"/>'
               f'<circle cx="{hx}" cy="{hy}" r="5" fill="{CYAN}"/>')
    return "".join(out)


ABOUT = ("I build LLM systems that do real work and can show the evidence behind every answer. As an R&D intern at "
         "Fortinet I'm building a multi-agent platform that investigates Kubernetes incidents over live telemetry; "
         "it cut time-to-root-cause from about 10 minutes to under 3.")


def about():
    w, h = 1000, 340
    lines = textwrap.wrap(ABOUT, 52)
    assert 104 + len(lines) * 27 < 270, "about text too long"
    text = "".join(f'<text class="body" x="32" y="{104 + i * 27}">{html.escape(s)}</text>' for i, s in enumerate(lines))
    chips, x = [], 32
    for label in ("B.E. INFO SCIENCE '26", "CGPA 8.5", "BENGALURU"):
        s, cw = chip(x, 278, label, CYAN)
        chips.append(s)
        x += cw + 10
    body = panel(w, h) + heading(w, 1, "ABOUT") + text + "".join(chips) + graph(800, 196, 100)
    return svg(w, h, "About: " + ABOUT, body)


JOBS = [
    ("FORTINET", "R&D Intern", "Mar 2026 – present · Bengaluru",
     "LangGraph orchestrator + five domain agents (Kubernetes, Prometheus, Elasticsearch, Kafka, FortiMonitor) pulling live "
     "evidence over MCP. Every claim is grounded against a ChromaDB knowledge base, the agent graph is traced with "
     "OpenTelemetry, and inference is fully self-hosted on Ollama. Time-to-root-cause: from ~10 min to under 3."),
    ("AI4SEE", "Data Science Intern", "Jan – Mar 2026 · Remote",
     "Built and evaluated ML models end to end and turned experiment notebooks into reproducible, deployable training pipelines."),
    ("INTERNPE", "AI/ML Intern", "Jul – Aug 2025 · Remote",
     "FAISS semantic search and clustering over 500+ QA test cases that flags near-duplicates automatically, cutting manual review by about 70%."),
]


def experience():
    w, y, items, ys = 1000, 116, [], []
    for company, role, when, desc in JOBS:
        lines = textwrap.wrap(desc, 98)
        ys.append(y - 7)
        items.append(f'<circle class="pulse" cx="44" cy="{y - 7}" r="12" fill="{CYAN}" fill-opacity=".2"/>'
                     f'<circle cx="44" cy="{y - 7}" r="6" fill="{CYAN}" filter="url(#glow)"/>'
                     f'<text class="co" x="76" y="{y}">{company}</text>'
                     f'<text class="small" x="76" y="{y + 26}" fill="{CYAN}">{html.escape(f"{role}  ·  {when}")}</text>'
                     + "".join(f'<text class="desc" x="76" y="{y + 54 + i * 23}">{html.escape(s)}</text>' for i, s in enumerate(lines)))
        y += 54 + 23 * len(lines) + 34
    h = y - 14
    rail = (f'<line x1="44" y1="{ys[0]}" x2="44" y2="{ys[-1]}" stroke="{VIOLET}" stroke-opacity=".6" stroke-width="2" filter="url(#glow)"/>'
            f'<circle r="4" cx="44" fill="{MAGENTA}" filter="url(#glow)"><animate attributeName="cy" values="{ys[0]};{ys[-1]}" dur="3.5s" repeatCount="indefinite"/></circle>')
    css = f".co{{font:700 20px {DISPLAY};letter-spacing:2px;fill:{TEXT}}} .desc{{font:400 15px {MONO};fill:{MUTED}}}"
    body = panel(w, h) + heading(w, 2, "EXPERIENCE") + rail + "".join(items)
    return svg(w, h, "Experience: " + "; ".join(f"{r} at {c.title()} ({t}): {d}" for c, r, t, d in JOBS), body, css)


def title(num, label):
    w, h = 1000, 90
    return svg(w, h, label.title(), panel(w, h) + heading(w, num, label, y=52))


PROJECTS = [  # (asset slug, title, description, tech chips, live demo?)
    ("mediassist", "MediAssist", "Agentic appointment assistant: the LLM chooses tools to find doctors, book free slots, "
     "create Google Calendar events and alert doctors on Slack.", ["FASTAPI", "REACT", "POSTGRES", "GEMINI"], False),
    ("llm-evaluator", "LLM Evaluator", "Scores a chatbot's answer against its retrieved context for relevance, completeness "
     "and hallucination risk, plus latency and token cost.", ["PYTHON", "FLASK", "LLM EVALS"], True),
    ("spectacular", "SpecTacular.AI", "Turns requirement documents into traceable test cases, fully offline. Embeddings + "
     "FAISS match requirements; clustering removed 85% of duplicates.", ["FAISS", "TRANSFORMERS", "FLASK"], False),
    ("anchor", "Anchor", "Local AI pair programmer for the terminal. Code never leaves the machine, every diff is validated "
     "before it lands, and undo is one command.", ["PYTHON", "OLLAMA", "CLI"], False),
    ("pingme", "PingMe", "Productivity tracker that auto-categorises your day with Gemini, sends mid-day nudges and weekly "
     "insights, and keeps a reading habit on track.", ["PYTHON", "GEMINI"], False),
    ("wind-forecast", "Wind Forecast", "Day-ahead power buying on Elexon data: compares the wind forecast available at "
     "decision time with actual generation and turns the error into a buying margin.", ["PYTHON", "TIME SERIES"], True),
]


def card(i, name, desc, tech, live):
    w, h = 600, 320
    lines = textwrap.wrap(desc, 48)  # 18px mono: 48 chars fill the 536px text column
    assert len(lines) <= 4, f"{name}: description needs {len(lines)} lines"
    color = (CYAN, MAGENTA)[i % 2]
    chips, x = [], 32
    for t in tech:
        s, cw = chip(x, 262, t, color)
        chips.append(s)
        x += cw + 10
    assert x < w - 22, f"{name}: chips overflow"
    status = live_dot(w - 92, 46, "LIVE") if live else f'<text class="small" x="{w - 32}" y="51" text-anchor="end" fill="{MUTED}" letter-spacing="2">SOURCE</text>'
    inner = f'<circle cx="{w - 40}" cy="40" r="110" fill="{color}" fill-opacity=".25" filter="url(#blur)"/>'
    body = (panel(w, h, inner) + f'<text class="num" x="32" y="51" style="fill:{color}">{i:02d}</text>{status}'
            f'<text class="ttl" x="32" y="100" filter="url(#glow)">{html.escape(name)}</text>'
            f'<rect x="32" y="116" width="56" height="3" rx="1.5" fill="url(#ng)"/>'
            + "".join(f'<text class="cd" x="32" y="{154 + j * 25}">{html.escape(s)}</text>' for j, s in enumerate(lines))
            + "".join(chips))
    css = f".ttl{{font:700 28px {DISPLAY};letter-spacing:1px;fill:{TEXT}}} .cd{{font:400 18px {MONO};fill:{MUTED}}}"
    return svg(w, h, f"{name}: {desc}", body, css)


STACK = [
    ("AGENTS & LLMS", "langgraph:LangGraph langchain:LangChain modelcontextprotocol:MCP ollama:Ollama googlegemini:Gemini huggingface:Hugging Face"),
    ("MACHINE LEARNING", "python:Python pytorch:PyTorch tensorflow:TensorFlow scikitlearn:scikit-learn"),
    ("BACKEND", "fastapi:FastAPI flask:Flask typescript:TypeScript react:React postgresql:PostgreSQL mongodb:MongoDB"),
    ("INFRASTRUCTURE", "docker:Docker kubernetes:Kubernetes apachekafka:Kafka elasticsearch:Elasticsearch linux:Linux"),
    ("OBSERVABILITY", "opentelemetry:OpenTelemetry prometheus:Prometheus grafana:Grafana"),
]
ITEM = re.compile(r"(\w+):(.+?)(?= \w+:|$)")


def stack(icon):
    w, top, row_h, fs = 1000, 100, 54, 17
    rows, n = [], 0
    for r, (label, items) in enumerate(STACK):
        cy = top + r * row_h + row_h // 2
        if r:
            rows.append(f'<line x1="32" y1="{cy - row_h // 2}" x2="{w - 32}" y2="{cy - row_h // 2}" stroke="{VIOLET}" stroke-opacity=".15"/>')
        rows.append(f'<text class="small" x="32" y="{cy + 5}" fill="{MAGENTA}" letter-spacing="2">{html.escape(label)}</text>')
        x = 200
        for slug, name in ITEM.findall(items):
            rows.append(f'<path class="ico" style="animation-delay:{n * .12:.2f}s" transform="translate({x:.0f} {cy - 11}) scale(.9167)" d="{icon(slug)}" fill="url(#ng)" filter="url(#glow)"/>'
                        f'<text class="it" x="{x + 32:.0f}" y="{cy + 6}">{html.escape(name)}</text>')
            x += 32 + len(name) * fs * .56 + 26  # ponytail: average Inter glyph width, not real metrics
            n += 1
        assert x < w + 10, f"{label} row overflows"
    h = top + len(STACK) * row_h + 20
    css = f".it{{font:400 {fs}px {SANS};fill:{TEXT}}} .ico{{animation:wave 3s ease-in-out infinite}} @keyframes wave{{50%{{opacity:.45}}}}"
    names = ", ".join(n for _, it in STACK for _, n in ITEM.findall(it))
    return svg(w, h, "Tech stack: " + names, panel(w, h) + heading(w, 4, "TECH STACK") + "".join(rows), css, fonts=("mono", "display", "sans"))


def build_static():
    cache = {}

    def icon(slug):
        if slug not in cache:
            raw = urllib.request.urlopen(ICON_URL.format(slug), timeout=30).read().decode()
            cache[slug] = re.search(r' d="([^"]+)"', raw).group(1)
        return cache[slug]

    out = {"hero.svg": hero(), "about.svg": about(), "experience.svg": experience(),
           "title-projects.svg": title(3, "SELECTED WORK"), "stack.svg": stack(icon)}
    for k, (label, slug) in enumerate([("PORTFOLIO", "vercel"), ("LINKEDIN", None), ("EMAIL", "gmail"), ("RESUME", "googledrive")]):
        out[f"btn-{label.lower()}.svg"] = button(label, icon(slug) if slug else LINKEDIN, k * .4)
    for i, (slug, *rest) in enumerate(PROJECTS, 1):
        out[f"card-{slug}.svg"] = card(i, *rest)
    for name, text in out.items():
        (ASSETS / name).write_text(text)
    print("wrote", ", ".join(out))


# ---------------------------------------------------------------- live activity card

QUERY = """query($login:String!){user(login:$login){
 repositories(ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC,first:100){totalCount nodes{stargazerCount
  languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}
 contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount}}}}}}"""


def fetch(login, token):
    req = urllib.request.Request("https://api.github.com/graphql", headers={"Authorization": f"bearer {token}"},
                                 data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode())
    data = json.load(urllib.request.urlopen(req, timeout=30))
    if "errors" in data:
        raise SystemExit(f"GitHub API error: {data['errors']}")
    return data["data"]["user"]


def summarize(user):
    repos = user["repositories"]
    langs = {}
    for repo in repos["nodes"]:
        for e in repo["languages"]["edges"]:
            if e["node"]["name"] != "Jupyter Notebook":  # notebook bytes are mostly outputs
                langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:4]
    total = sum(s for _, s in top) or 1
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = [sum(d["contributionCount"] for d in wk["contributionDays"]) for wk in cal["weeks"]][-52:]
    return dict(contributions=cal["totalContributions"], repos=repos["totalCount"],
                stars=sum(r["stargazerCount"] for r in repos["nodes"]),
                langs=[(n, s / total) for n, s in top], weeks=weeks)


def activity(s, today):
    w, h = 1000, 330
    stamp = f"LIVE · UPDATED {today}"
    lx = w - 32 - dot_w(stamp) - 14
    nums = "".join(f'<text class="big r{k}" x="{32 + k * 180}" y="148" fill="url(#ng)" filter="url(#glow)">{n}</text>'
                   f'<text class="small r{k}" x="{32 + k * 180}" y="174" fill="{MUTED}" letter-spacing="1.5">{label}</text>'
                   for k, (n, label) in enumerate([(s["contributions"], "CONTRIBUTIONS / YR"), (s["repos"], "PUBLIC REPOS"), (s["stars"], "STARS EARNED")]))
    colors, bar, legend, x, lx2 = [CYAN, VIOLET, MAGENTA, GREEN], [], [], 32.0, 32.0
    for (name, share), c in zip(s["langs"], colors):
        bar.append(f'<rect x="{x:.1f}" y="214" width="{520 * share:.1f}" height="10" fill="{c}"/>')
        x += 520 * share
        label = f"{name} {share:.0%}"
        legend.append(f'<circle cx="{lx2 + 5:.0f}" cy="251" r="5" fill="{c}"/><text class="small" x="{lx2 + 16:.0f}" y="256" fill="{TEXT}">{html.escape(label)}</text>')
        lx2 += 16 + mw(label, 13) + 22
    x0, x1, y0, y1 = 610, 968, 116, 284
    peak = max(s["weeks"]) or 1
    step = (x1 - x0) / max(len(s["weeks"]) - 1, 1)
    pts = [(x0 + i * step, y1 - (y1 - y0) * v / peak) for i, v in enumerate(s["weeks"])]
    line = "M" + "L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    length = sum(math.dist(a, b) for a, b in zip(pts, pts[1:])) + 1
    css = f"""
.big{{font:900 40px {DISPLAY}}}
.r0,.r1,.r2{{animation:rise .9s ease-out both}} .r1{{animation-delay:.15s}} .r2{{animation-delay:.3s}}
@keyframes rise{{from{{opacity:0;transform:translateY(14px)}}}}
.grow{{transform-box:fill-box;transform-origin:left;animation:grow 1.6s ease-out both}} @keyframes grow{{from{{transform:scaleX(0)}}}}
.draw{{stroke-dasharray:{length:.0f};animation:draw 2.6s ease-out both}} @keyframes draw{{from{{stroke-dashoffset:{length:.0f}}}}}
.fadein{{animation:fadein 2.6s ease-in both}} @keyframes fadein{{from{{opacity:0}}}}"""
    body = (panel(w, h) + heading(w, 5, "LIVE ACTIVITY", right=int(lx - 20)) + live_dot(int(lx), 48, stamp) + nums
            + f'<clipPath id="bar"><rect x="32" y="214" width="520" height="10" rx="5"/></clipPath><g clip-path="url(#bar)"><g class="grow">{"".join(bar)}</g></g>'
            + "".join(legend)
            + f'<defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity=".35"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient></defs>'
            + f'<text class="small" x="{x0}" y="100" fill="{MUTED}" letter-spacing="1.5">CONTRIBUTIONS PER WEEK · 52W</text>'
            + f'<text class="small" x="{x1}" y="100" text-anchor="end" fill="{MUTED}">peak {peak}</text>'
            + f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{VIOLET}" stroke-opacity=".25"/>'
            + f'<path class="fadein" d="{line}L{x1},{y1}L{x0},{y1}Z" fill="url(#area)"/>'
            + f'<path class="draw" d="{line}" fill="none" stroke="url(#ngu)" stroke-width="2.5" stroke-linejoin="round" filter="url(#glow)"/>'
            + f'<circle class="pulse" cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="5" fill="{MAGENTA}" filter="url(#glow)"/>')
    title_text = f"Live activity: {s['contributions']} contributions in the last year, {s['repos']} public repos, {s['stars']} stars. Top languages: " + \
        ", ".join(f"{n} {v:.0%}" for n, v in s["langs"])
    return svg(w, h, title_text, body, css)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--stats"]:
        data = summarize(fetch(os.environ["USERNAME"], os.environ["GITHUB_TOKEN"]))
        pathlib.Path(sys.argv[2]).write_text(activity(data, datetime.date.today().isoformat()))
        print("stats:", {k: v for k, v in data.items() if k != "weeks"})
    else:
        build_static()
