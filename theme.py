"""
theme.py - Design system v5 "Midnight engine" (TURA Pro), after n8n's style: a violet-black void, surfaces one step
lighter each (page -> card -> panel, no drop shadows), light restrained headings, frosted chips with hairlines, a violet glow
behind the page. Two changes from n8n for a trading site: the call-to-action buttons use the logo's blue -> cyan (never red),
and green / red are kept for gains and losses only.
Rule used everywhere: positive = dark-green box + bright-green text, negative = dark-red box + bright-red text.
Fonts: DM Sans (Latin) + Readex Pro (Arabic). Material Symbols icons. No emoji.
"""
import base64
import hashlib
import html
import json
import math
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

import flags
import lightmode as LM
import terms as GL
import mcal

# ---------------------------------------------------------------- palette
BG, CARD, CARD2, BORDER = "#0E0918", "#1A1624", "#221D2F", "#2C2738"
TEXT, MUTED = "#E7E3EB", "#9D97A5"
UP, DOWN = "#22C55E", "#EF4444"                     # chart strokes on dark surfaces
ACCENT, VIOLET, CYAN, GOLD, ORANGE, PURPLE = "#3B8BEB", "#7B45F0", "#2DB6EB", "#F5B94A", "#F97316", "#A78BFA"
POS_BG, POS_FG, POS_BD = "#0F2A1E", "#4ADE80", "#1F5A3B"   # dark green box, bright green text
NEG_BG, NEG_FG, NEG_BD = "#34141C", "#F87171", "#6B2531"   # dark red box, bright red text
ACC_BG, ACC_FG = "#15233F", "#93C5FD"
VIO_BG, VIO_FG = "#231842", "#C4B5FD"
YEL_BG, YEL_FG = "#302410", "#FCD34D"
ORG_BG, ORG_FG = "#341C0F", "#FDBA74"
NEU_BG, NEU_FG = "#26212F", "#C9C3D1"
FONT = "DM Sans, Readex Pro, system-ui, sans-serif"
# n8n's own tokens
PANEL, SMOKE, SHELL = "#1B1728", "#3E3A46", "#2C2834"          # deep panel, nav/container borders, ghost-button fill
FIELD, FIELD_EDGE = "#0F0B1A", "rgba(157,151,165,.42)"         # every input box: a darker well with a visible edge
CTA = "linear-gradient(30deg,#3D68C6,#2DB6EB)"                   # the call to action: the logo's blue -> cyan
CTA_HOVER = "linear-gradient(30deg,#4A78D8,#45C2F0)"
ELECTRIC = "linear-gradient(141deg,#077AC7,#6B21EF)"             # n8n's "electric current": links, focus, connecting lines
GLOW = "inset 0 0 0 1px rgba(255,255,255,.08), inset 0 -26px 36px -30px rgba(123,69,240,.55)"   # "backlit hardware"

# ---------------------------------------------------------------- logo
# The owner's mark: a small pill and a T drawn as glass tubes (bright rims round a deep colour), sky blue at the top right
# turning violet at the foot, glowing like neon, with a soft shadow under the tubes and the blue / violet / teal light behind them.
# Everything is in the pixels of the owner's picture of the logo: the shapes and colours were measured from it.
LOGO_BOX = "1082 546 518 482"                 # the tubes themselves (the shadow and the light spill out of it)
LOGO_GLOW_BOX = (1000, 447, 680, 680)         # the mark with the light around it, a square
_LW, _RIM = 24.5, 3.0                         # tube width; the bright rim on each side of it
_PILL = "M1154 563.5H1199.6A54.9 54.9 0 0 1 1199.6 673.3H1154A54.9 54.9 0 0 1 1154 563.5Z"
_TEE = ("M1294.3 668.1A104.6 104.6 0 0 1 1399 563.5H1526.7A55.3 55.3 0 0 1 1526.7 674H1401.7V956.3"
        "A53.7 53.7 0 0 1 1294.3 956.3Z")
_SHOULDER = "M1401.7 674C1330.6 674 1294.3 723.1 1294.3 766.4"
# the T's colours run from its foot (bottom left) to its bar (top right); the pill's from left to right
_T_LINE = (1229, 921, 1549, 565)
_T_IN = ("#421066", "#4D1677", "#512694", "#393CA8", "#2955B6", "#1D62B5", "#0D6AB4", "#0874BF")
_T_RIM = ("#73319A", "#7D3AA7", "#7F51C2", "#5A5FC9", "#4E7AD1", "#428BCF", "#4199D2", "#48A9DF")
_P_LINE = (1099, 624, 1254, 624)
_P_IN = ("#071B65", "#0B1C6C", "#0F2176", "#0E3591")
_P_RIM = ("#2A3BA1", "#313DA8", "#344AAF", "#3659BD")
# the light behind the mark, layer over layer: (centre x, centre y, spread x, spread y, strength, colour)
_LIGHT = ((1375, 829, 201, 227, .38, "#9608BF"),      # violet round the foot
          (1593, 539, 191, 147, .95, "#20453A"),      # teal past the end of the bar
          (1598, 799, 106, 102, .09, "#C4B9FF"),
          (1387, 590, 248, 157, .88, "#001965"))      # deep blue behind the top of the T
# the coloured halo round the whole mark (on the dark look over that light, and on the light look on its own)
_AURA = ((1340, 787, 205, 195, .55, "#6D4BFF"),       # violet-blue round the whole mark
         (1530, 610, 115, 85, .45, "#22B8F5"),        # sky by the end of the bar
         (1348, 975, 105, 95, .45, "#B026FF"))        # magenta under the foot
# the neon the tubes give off: purer, brighter versions of their colours, blurred round them (foot -> bar; left -> right)
_T_GLOW = ("#B04CFF", "#A050FF", "#8A5CFF", "#6A70FF", "#4C8CFF", "#2EA8FF", "#22BDF5", "#38D2F7")
_P_GLOW = ("#3D5CFF", "#4464FF", "#4C72FF", "#5590FF")
_GAUSS = tuple((i / 8, math.exp(-0.5 * (3 * i / 8) ** 2)) for i in range(9))


def _lin(id_, line, stops):
    x1, y1, x2, y2 = line
    n = len(stops) - 1
    return (f'<linearGradient id="{id_}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
            + "".join(f'<stop offset="{i / n:.3f}" stop-color="{c}"/>' for i, c in enumerate(stops)) + "</linearGradient>")


def _blobs(p, layers, k0, scale=1.0):
    defs, els = [], []
    for k, (cx, cy, sx, sy, a, col) in enumerate(layers, k0):
        defs.append(f'<radialGradient id="{p}g{k}">' + "".join(
            f'<stop offset="{o:.3f}" stop-color="{col}" stop-opacity="{min(1.0, a * scale) * g if o < 1 else 0:.4f}"/>' for o, g in _GAUSS)
            + "</radialGradient>")
        els.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{3 * sx}" ry="{3 * sy}" fill="url(#{p}g{k})"/>')
    return defs, els


def logo_parts(p="lg", light=True, shadow=.45, glow=1.0, aura=.85, spread=1.0):
    """The mark's drawing (ids prefixed with p). light: the deep light of the owner's picture behind it (for dark surfaces);
    aura: how strong the coloured halo round the mark is; glow: how strong the neon round the tubes is; spread: how far the
    neon reaches; shadow: how dark the shadow under the tubes is (0: none). The light and the halo fade out inside LOGO_GLOW_BOX."""
    defs = [_lin(p + "a", _T_LINE, _T_IN), _lin(p + "b", _T_LINE, _T_RIM), _lin(p + "c", _P_LINE, _P_IN), _lin(p + "d", _P_LINE, _P_RIM)]
    out = []
    if light or aura:
        x0, y0, w, h = LOGO_GLOW_BOX
        glows = []
        if light:
            d_, e_ = _blobs(p, _LIGHT, 0)
            defs += d_
            glows += e_
        if aura:
            d_, e_ = _blobs(p, _AURA, 10, aura)
            defs += d_
            glows += e_
        fade = ('<stop offset=".3" stop-color="#fff"/><stop offset=".7" stop-color="#fff" stop-opacity=".45"/>' if aura else
                '<stop offset=".55" stop-color="#fff"/>')              # with the halo, a softer edge; the picture's own light as it was
        defs.append(f'<radialGradient id="{p}f" gradientUnits="userSpaceOnUse" cx="{x0 + w / 2:g}" cy="{y0 + h / 2:g}" r="{w / 2:g}">'
                    f'{fade}<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
                    f'<mask id="{p}m"><rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="url(#{p}f)"/></mask>')
        out.append(f'<g mask="url(#{p}m)">{"".join(glows)}</g>')
    tube = lambda d, stroke, width: f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{width:g}" stroke-linejoin="round"/>'
    if shadow:
        defs.append(f'<filter id="{p}s" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="10.5"/></filter>')
        out.append(f'<g filter="url(#{p}s)" opacity="{shadow:g}" transform="translate(0 14)">'
                   + "".join(tube(d, "#000", _LW + 1) for d in (_PILL, _TEE, _SHOULDER)) + "</g>")
    if glow:                                   # the neon: a wide soft bloom, then a tight bright one, under the tubes
        defs += [_lin(p + "e", _T_LINE, _T_GLOW), _lin(p + "h", _P_LINE, _P_GLOW),
                 f'<filter id="{p}w" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="{24 * spread:g}"/></filter>',
                 f'<filter id="{p}n" x="-35%" y="-35%" width="170%" height="170%"><feGaussianBlur stdDeviation="{7 * spread:g}"/></filter>']
        neon = lambda width: tube(_PILL, f"url(#{p}h)", width) + tube(_TEE, f"url(#{p}e)", width) + tube(_SHOULDER, f"url(#{p}e)", width)
        out.append(f'<g filter="url(#{p}w)" opacity="{min(1.0, .9 * glow):g}">{neon(_LW + 18 * spread)}</g>'
                   f'<g filter="url(#{p}n)" opacity="{min(1.0, .95 * glow):g}">{neon(_LW + 5 * spread)}</g>')
    # the rims first, then every tube's inside over them, so where the tubes meet they join into one
    out.append(tube(_PILL, f"url(#{p}d)", _LW) + tube(_TEE, f"url(#{p}b)", _LW) + tube(_SHOULDER, f"url(#{p}b)", _LW))
    inner = _LW - 2 * _RIM
    out.append(tube(_PILL, f"url(#{p}c)", inner) + tube(_TEE, f"url(#{p}a)", inner) + tube(_SHOULDER, f"url(#{p}a)", inner))
    return f'<defs>{"".join(defs)}</defs>{"".join(out)}'


# the light look: no deep light behind it (it would read as a dark smudge on a pale page), the coloured halo and the neon
# stronger, the shadow faint
LIGHT_LOOK = dict(light=False, shadow=.12, glow=1.25, aura=.75)
# the dark look: the owner's picture as it is (its deep light behind the mark and its shadow; no added neon or halo)
DARK_LOOK = dict(light=True, shadow=.62, glow=0, aura=0)


def logo_mark(p="lg", cls="", light=True):
    """The mark as inline SVG sized by its tubes; the shadow, the neon and the light spill out around it (give each copy on a
    page its own p)."""
    c = f' class="{cls}"' if cls else ""
    parts = logo_parts(p, **DARK_LOOK) if light else logo_parts(p, **LIGHT_LOOK)
    return f'<svg{c} viewBox="{LOGO_BOX}" overflow="visible" style="overflow:visible" aria-hidden="true">{parts}</svg>'


# in the light look the logo at the top of the page also glows past the edges of its picture (these colours are kept as they
# are); the dark look has no such glow
_LOGO_SEL = 'img[data-testid="stLogo"], img.stLogo, [data-testid="stSidebarHeader"] img, [data-testid="stHeaderLogo"] img'


def logo_glow_css(light_look=False):
    if not light_look:
        return ""
    f = "drop-shadow(0 0 2px rgba(56,189,248,.5)) drop-shadow(0 0 8px rgba(124,92,255,.45)) drop-shadow(0 0 16px rgba(176,76,255,.2))"
    return f'<style data-lm="keep">{_LOGO_SEL} {{ filter:{f}; }}</style>'


# ---------------------------------------------------------------- the name, drawn in thin geometric lines (Fenomeno style)
# Each letter is a line drawing on a 100-high grid: (width, path). Drawn, not typed, so it looks the same everywhere without a font file.
_GLYPHS = {
    "A": (84, "M0 100 L42 0 L84 100 M17 60 H52"),         # the bar stops short of the right leg, like Fenomeno's open bars
    "L": (56, "M0 0 V100 H56"),
    "T": (72, "M0 0 H72 M36 0 V100"),
    "U": (72, "M0 0 V64 A36 36 0 0 0 72 64 V0"),
    "R": (66, "M0 100 V0 H38 A25 25 0 0 1 38 50 H0 M26 50 L66 100"),
    "I": (0, "M0 0 V100"),
    "F": (58, "M0 100 V0 H58 M14 50 H48"),
    "P": (64, "M0 100 V0 H38 A25 25 0 0 1 38 50 H0"),
    "O": (100, "M0 50 A50 50 0 1 0 100 50 A50 50 0 1 0 0 50"),
    ".": (7, "M0 97 H7"),
    " ": (30, ""),
}
_TRACK, _SW = 26, 6          # space between letters and line width, in grid units


def _move(d, s, tx, ty):
    """A glyph path scaled by s and moved by (tx, ty), written out in plain coordinates (so a gradient spans the whole word)."""
    tok, out, i = d.replace(",", " ").split(), [], 0
    f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
    cmd = ""
    while i < len(tok):
        t = tok[i]
        if t[0].isalpha():
            cmd, t = t[0], t[1:]
            out.append(cmd)
            if not t:
                i += 1
                continue
            tok[i] = t
        if cmd in "ML":
            out += [f(float(tok[i]) * s + tx), f(float(tok[i + 1]) * s + ty)]
            i += 2
        elif cmd == "H":
            out.append(f(float(tok[i]) * s + tx))
            i += 1
        elif cmd == "V":
            out.append(f(float(tok[i]) * s + ty))
            i += 1
        elif cmd == "A":
            rx, ry, rot, la, sw, x, y = tok[i:i + 7]
            out += [f(float(rx) * s), f(float(ry) * s), rot, la, sw, f(float(x) * s + tx), f(float(y) * s + ty)]
            i += 7
        else:                                   # Z
            i += 1
    return " ".join(out)


def _word(text, x, scale=1.0, y=0.0):
    """The letters of text as one path starting at x (grid units). Returns (path, right edge)."""
    parts = []
    for ch in text.upper():
        w, d = _GLYPHS.get(ch, _GLYPHS[" "])
        if d:
            parts.append(_move(d, scale, x, y))
        x += (w + _TRACK) * scale
    return (f'<path d="{" ".join(parts)}"/>' if parts else ""), x - _TRACK * scale


NAME = "TURA"                # the site's name, drawn by brand() and written in titles as "TURA Pro"


def brand(height="1em", p="bm", dot=False, pro="sup", color="#FFFFFF", cls="brand", label="TURA Pro"):
    """The site's name as line art. pro: 'sup' (small, raised, blue to cyan), 'inline' (same size, blue) or None.
    dot is kept for the callers that asked for the old leading 'A.' (the name is TURA now: nothing is added).
    height is any CSS length; the width follows."""
    x = _SW / 2
    first = ""
    main, x = _word(NAME, x)
    tail = defs = ""
    if pro:
        x += 46 if pro == "sup" else 64
        sc = .46 if pro == "sup" else 1.0
        x0 = x
        tail, x = _word("PRO", x, sc)
        defs = (f'<defs><linearGradient id="{p}g" gradientUnits="userSpaceOnUse" x1="{x0:.0f}" y1="0" x2="{x:.0f}" y2="0">'
                f'<stop offset="0" stop-color="#5B8CFF"/><stop offset=".55" stop-color="#A78BFA"/><stop offset="1" stop-color="#2DB6EB"/>'
                f'</linearGradient></defs>')
        tail = f'<g stroke="url(#{p}g)">{tail}</g>'
    w, h = x + _SW / 2, 100 + _SW
    st_ = f' style="height:{height};width:auto"' if height else ""
    return (f'<svg class="{cls}" viewBox="0 {-_SW / 2:.0f} {w:.0f} {h:.0f}"{st_} role="img" '
            f'aria-label="{label}" fill="none" stroke-width="{_SW}" stroke-linecap="butt" stroke-linejoin="miter" stroke-miterlimit="10">'
            f'{defs}<g stroke="{color}">{first}{main}</g>{tail}</svg>')


def brand_box(p="bw"):
    """(width, height, inner svg) of the name for placing inside another SVG."""
    s = brand(None, p)
    vb = s.split('viewBox="', 1)[1].split('"', 1)[0].split()
    return float(vb[2]), float(vb[3]), s


_GB = " ".join(str(v) for v in LOGO_GLOW_BOX)
# small at the top of the page, in the dark look as in the owner's picture
_MARK = f'<svg x="0" y="0" width="64" height="64" viewBox="{_GB}">{logo_parts("mk", **DARK_LOOK)}</svg>'
LOGO_ICON = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">{_MARK}</svg>'
LOGO_ICON_LIGHT = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">'
                   f'<svg x="0" y="0" width="64" height="64" viewBox="{_GB}">{logo_parts("il", **LIGHT_LOOK)}</svg></svg>')
_bw, _bh, _bs = brand_box("lw")
_BH = 26                                     # height of the name inside the 64-high logo
_BX = 66                                     # where the name starts (the tubes end at about 56)


def logo_wordmark(light_look=False):
    """The mark with its light and the name, for the top of the page. The light look: the mark with its neon and halo but without
    the deep light behind it, a fainter shadow, and the name in dark ink."""
    mark = (f'<svg x="0" y="0" width="64" height="64" viewBox="{_GB}">{logo_parts("ml", **LIGHT_LOOK)}</svg>' if light_look else _MARK)
    name = LM.convert(_bs) if light_look else _bs
    w = _BX + _bw * _BH / _bh + 6
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} 64" width="{w:.0f}" height="64">{mark}'
            + name.replace('<svg class="brand"', f'<svg x="{_BX}" y="{32 - _BH / 2 + 1:.0f}" width="{_bw * _BH / _bh:.0f}" height="{_BH}"', 1)
            + "</svg>")


LOGO_WORDMARK = logo_wordmark()

FONT_LATIN, FONT_AR = "'DM Sans'", "'Readex Pro'"
FLAG_US, FLAG_SA = flags.US, flags.SA


# ---------------------------------------------------------------- the night behind every page
# Every page of the top bar: the owner's picture of a violet night with a dotted globe, market moves floating in the air and
# a grid floor (static/bg_markets.jpg: its title and menu bar taken out, very lightly blurred), under a light veil; fixed
# while the page scrolls, and on a phone the globe stays in view. The landing keeps its own night (landing_bg_css).
BG_FILE = "bg_markets.jpg"
BG_CDN = f"https://cdn.jsdelivr.net/gh/abdulrahmanalturify-boop/trading-bot-v5@main/static/{BG_FILE}"
BG_VEIL = "linear-gradient(180deg, rgba(14,9,24,.20) 0%, rgba(14,9,24,.28) 45%, rgba(14,9,24,.48) 100%)"
# the reading pages (news, tables, calendars...): a deeper veil, so the globe and its numbers stay behind the content
BG_VEIL_CALM = "linear-gradient(180deg, rgba(14,9,24,.58) 0%, rgba(14,9,24,.66) 45%, rgba(14,9,24,.78) 100%)"
BG_GLOWS = ("radial-gradient(1200px 620px at 50% 118%, rgba(107,33,239,.30), transparent 62%), "
            "radial-gradient(900px 520px at 8% -12%, rgba(7,122,199,.20), transparent 60%), "
            "radial-gradient(760px 460px at 96% 4%, rgba(123,69,240,.13), transparent 62%)")
BG_DOTS = "radial-gradient(rgba(255,255,255,.075) 1px, transparent 1.3px) 0 0 / 24px 24px"


def background_css(static_ok=False, calm=False):
    """The page background: the globe picture under its veil (the site's own static file, else the same file on the CDN).
    calm: a reading page, where the picture is toned down behind the content."""
    url = f"app/static/{BG_FILE}" if static_ok else BG_CDN
    return (f'<style>.stApp::before {{ background: {BG_VEIL_CALM if calm else BG_VEIL}, url("{url}") 68% 40% / cover no-repeat, {BG}; }}'
            f'.stApp::after {{ background: none; }}'
            f'@media (max-width: 768px) {{ .stApp::before {{ background-position: 0 0, 72% 30%; }} }}</style>')


def landing_bg_css():
    """The landing keeps the night it was designed on: the glows and the canvas dots, no picture."""
    return (f'<style>.stApp::before {{ background: {BG_GLOWS}, {BG} !important; }}'
            f'.stApp::after {{ background: {BG_DOTS} !important; -webkit-mask-image: linear-gradient(180deg,#000 0%,rgba(0,0,0,.35) 45%,transparent 85%);'
            f' mask-image: linear-gradient(180deg,#000 0%,rgba(0,0,0,.35) 45%,transparent 85%); }}</style>')


# ---------------------------------------------------------------- boxes: flat surfaces, one step lighter than the page
# n8n has no brand line on its boxes: a box stands out through its colour alone. TOP stays an (invisible) first layer so every
# "background: TOP, <colour>" in the modules keeps working.
LINE = ELECTRIC                                                 # the electric current: small accent bars and lines
TOP = "linear-gradient(transparent,transparent) top / 100% 0 no-repeat"
TOP_THIN = TOP
BOX_BG = f"{TOP}, linear-gradient({CARD},{CARD})"             # every plain box: solid, one step above the page
UP_EDGE, DN_EDGE = "rgba(74,222,128,.34)", "rgba(248,113,113,.34)"   # a green box keeps its colour, with soft green edges (red the same)
UP_LINE = TOP
DN_LINE = TOP
UP_TINT = "linear-gradient(180deg, rgba(34,197,94,.16), rgba(34,197,94,.06))"
DN_TINT = "linear-gradient(180deg, rgba(239,68,68,.16), rgba(239,68,68,.06))"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=Readex+Pro:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,300..600,0..1,0&display=block');
html, body, .stApp, .stMarkdown, button, input, textarea, select, label, [data-testid="stMetricValue"], [data-baseweb] {{
  font-family: {FONT_LATIN}, {FONT_AR}, system-ui, sans-serif; }}
/* the void: glows in .stApp::before, the canvas dots in .stApp::after (background_css) */
.stApp {{ background: {BG}; color:{TEXT}; }}
.stApp::before {{ content:""; position:fixed; inset:0; z-index:0; pointer-events:none; background: {BG_GLOWS}, {BG}; }}
.stApp::after {{ content:""; position:fixed; inset:0; z-index:0; pointer-events:none; }}
::selection {{ background: rgba(107,33,239,.45); color:#fff; }}
* {{ scrollbar-color: {SMOKE} transparent; }}
[data-testid="stSidebar"] {{ background: linear-gradient(180deg, rgba(20,15,32,.96), rgba(14,9,24,.97)) !important;
  border-right: 1px solid {SHELL}; }}
[data-testid="stSidebar"] > div {{ background: transparent !important; }}
[data-testid="stAppViewContainer"] {{ z-index: 1; }}
header[data-testid="stHeader"] {{ background: rgba(14,9,24,.78); backdrop-filter: blur(18px) saturate(140%); -webkit-backdrop-filter: blur(18px) saturate(140%);
  border-bottom: 1px solid {SHELL}; box-shadow: none; }}
header[data-testid="stHeader"]::after {{ content:""; position:absolute; left:0; right:0; bottom:-1px; height:1px; pointer-events:none;
  background: linear-gradient(90deg, transparent 8%, rgba(7,122,199,.55), rgba(107,33,239,.55), transparent 92%); }}
[data-testid="stToolbarActions"], [data-testid="stAppDeployButton"], [data-testid="stStatusWidget"], [data-testid="stDecoration"] {{ display:none !important; }}
[data-testid="stElementContainer"]:has(.css-anchor), .element-container:has(.css-anchor) {{ display:none !important; }}
.block-container {{ padding-top: 4.4rem; padding-bottom: 3rem; max-width: 1560px; }}
/* Room between boxes everywhere: Streamlit pulls every markdown block 1rem up (margin-bottom:-1rem, meant for a paragraph's own
   bottom margin). A card, a row of boxes or a table drawn as HTML has no such margin, so the pull made it touch whatever came
   next (a chart, the next card). On the page itself the pull is taken off the blocks whose content is HTML: every box keeps the
   page's 1rem gap (the sidebar keeps its own tight list). */
[data-testid="stMain"] .stMarkdown:has(> [data-testid="stMarkdownContainer"] > :is(div, table, section, ul, ol):last-child),
[data-testid="stMain"] [data-testid="stMarkdownContainer"]:has(> :is(div, table, section, ul, ol):last-child) {{ margin-bottom:0 !important; }}
/* restrained type: large and light, the way n8n "whispers against the dark" */
h1 {{ font-size: 2.1rem !important; font-weight: 300 !important; letter-spacing: -.03em; color:#fff; line-height:1.1 !important; }}
h2 {{ font-weight: 400 !important; letter-spacing: -.02em; color:#fff; }}
h3 {{ font-weight: 500 !important; letter-spacing: -.01em; color:#fff; }}
.ms {{ font-family:'Material Symbols Rounded'; font-weight:400; font-style:normal; font-size:1.15em; line-height:1; display:inline-block;
  vertical-align:-0.2em; letter-spacing:normal; text-transform:none; white-space:nowrap; font-feature-settings:'liga'; }}
[data-testid="stMetric"] {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:16px; padding:14px 18px; }}
[data-testid="stMetricLabel"] {{ color:{MUTED}; }}
[data-testid="stMetricValue"] {{ font-weight:400; letter-spacing:-.02em; color:#fff; }}
[data-testid="stExpander"] details {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:16px; }}
[data-testid="stExpander"] summary:hover {{ color:#fff; }}
[data-testid="stTabs"] [data-baseweb="tab-list"] {{ gap:4px; border-bottom:1px solid {SHELL}; }}
[data-testid="stTabs"] button[role="tab"] {{ font-weight:500; color:{MUTED}; border-radius:8px 8px 0 0; padding:8px 14px; }}
[data-testid="stTabs"] button[role="tab"]:hover {{ color:#fff; background:rgba(255,255,255,.03); }}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{ color:#fff; }}
[data-testid="stTabs"] button[role="tab"] p {{ color:inherit; }}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{ background:{ELECTRIC} !important; height:2px; }}
/* tabs (Streamlit's React Aria tabs): a frosted track; the chosen tab is a lit blue-violet pill that slides over to the tab you
   press (Streamlit's own selection indicator, grown to the tab's full size); the others light up under the pointer */
[data-testid="stTabs"] [role="tablist"] {{ gap:6px; padding:6px; margin:0 0 14px; border-radius:16px; scroll-padding-inline:40px;
  background:linear-gradient(180deg, rgba(30,24,46,.80), rgba(16,12,28,.80)); border:1px solid rgba(157,151,165,.20);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.05), 0 10px 26px -16px rgba(0,0,0,.8); backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px); }}
[data-testid="stTabs"] [role="tablist"]::after {{ display:none !important; }}
[data-testid="stTabs"] [role="tab"] {{ height:44px; padding:0 18px; border-radius:12px; color:#C2BCCD; font-weight:600; font-size:.98rem;
  transition:color .2s, background-color .2s, transform .2s; }}
[data-testid="stTabs"] [role="tab"]:active {{ transform:scale(.97); }}
[data-testid="stTabs"] [role="tab"] p {{ color:inherit; font-size:inherit; font-weight:inherit; margin:0; }}
[data-testid="stTabs"] [role="tab"] [role="img"] {{ color:#79B8F4; font-size:1.15em; margin-inline-end:3px; transition:transform .25s cubic-bezier(.3,1.6,.5,1), color .2s; }}
[data-testid="stTabs"] [role="tab"][data-hovered]:not([data-selected]) {{ color:#fff; background-color:rgba(255,255,255,.06); }}
[data-testid="stTabs"] [role="tab"][data-hovered] [role="img"] {{ transform:translateY(-1px) scale(1.12); }}
[data-testid="stTabs"] [role="tab"][data-selected] {{ color:#fff; font-weight:700; }}
[data-testid="stTabs"] [role="tab"][data-selected] [role="img"] {{ color:#fff; }}
[data-testid="stTabs"] [role="tab"] .react-aria-SelectionIndicator {{ top:0; bottom:0 !important; height:auto !important; border-radius:12px !important; z-index:-1;
  transition:translate .32s cubic-bezier(.3,1.3,.5,1), background-color .2s !important; }}
[data-testid="stTabs"] [role="tab"][data-selected] .react-aria-SelectionIndicator {{ background:linear-gradient(135deg, #3B8BEB, #7B45F0) !important;
  box-shadow:0 8px 20px -8px rgba(91,124,242,.8), inset 0 1px 0 rgba(255,255,255,.25); }}
[data-testid="stTabs"] [role="tab"][data-focus-visible] {{ box-shadow:0 0 0 2px rgba(121,184,244,.75); }}
/* Streamlit's scroll arrows: the end of the track, where the tabs fade out, with the arrow in a small chip */
[data-testid="stTabsScrollLeft"], [data-testid="stTabsScrollRight"] {{ top:1px !important; height:50px !important; width:52px !important; padding:0 !important;
  border:0 !important; color:#E7E3EB !important; }}
[data-testid="stTabsScrollRight"] {{ right:1px !important; justify-content:flex-end !important; padding-right:8px !important; border-radius:0 13px 13px 0 !important;
  background:linear-gradient(to right, rgba(22,17,36,0), rgba(22,17,36,.97) 48%) !important; }}
[data-testid="stTabsScrollLeft"] {{ left:1px !important; justify-content:flex-start !important; padding-left:8px !important; border-radius:13px 0 0 13px !important;
  background:linear-gradient(to left, rgba(22,17,36,0), rgba(22,17,36,.97) 48%) !important; }}
[data-testid="stTabsScrollLeft"] > *, [data-testid="stTabsScrollRight"] > * {{ display:inline-flex; align-items:center; justify-content:center; width:30px; height:30px;
  border-radius:9px; background:rgba(44,36,66,.95); box-shadow:inset 0 0 0 1px rgba(157,151,165,.3), 0 4px 12px rgba(0,0,0,.45); transition:box-shadow .2s, color .2s; }}
[data-testid="stTabsScrollLeft"]:hover > *, [data-testid="stTabsScrollRight"]:hover > * {{ color:#fff; box-shadow:inset 0 0 0 1px rgba(121,184,244,.7), 0 4px 14px rgba(59,139,235,.35); }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius:16px !important; }}
/* buttons: the call to action in the logo's blue -> cyan; everything else frosted glass with a hairline */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button, .stLinkButton > a {{ border-radius:8px; font-weight:500;
  transition: background .18s, border-color .18s, color .18s, box-shadow .18s, filter .18s; }}
button[data-testid="stBaseButton-primary"], button[kind="primary"], [data-testid="stBaseButton-primaryFormSubmit"] {{
  background:{CTA} !important; border:1px solid rgba(255,255,255,.14) !important; color:#fff !important;
  box-shadow: 0 8px 22px -10px rgba(45,182,235,.65), inset 0 1px 0 rgba(255,255,255,.18); }}
button[data-testid="stBaseButton-primary"]:hover, button[kind="primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover {{
  background:{CTA_HOVER} !important; box-shadow: 0 10px 28px -10px rgba(45,182,235,.85), inset 0 1px 0 rgba(255,255,255,.22); }}
button[data-testid="stBaseButton-primary"] p, button[kind="primary"] p, button[data-testid="stBaseButton-primary"] span {{ color:#fff !important; }}
button[data-testid="stBaseButton-secondary"], button[kind="secondary"], [data-testid="stBaseButton-secondaryFormSubmit"], .stDownloadButton > button {{
  background: rgba(13,10,25,.28); border:1px solid rgba(255,255,255,.1); color:#D1CECE; box-shadow: rgba(0,0,0,.26) 0 0 8px; }}
button[data-testid="stBaseButton-secondary"]:hover, button[kind="secondary"]:hover, .stDownloadButton > button:hover {{
  background: rgba(255,255,255,.05); border-color: rgba(255,255,255,.24); color:#fff; }}
button[data-testid="stBaseButton-tertiary"]:hover {{ color:#fff; }}
/* the stock page's actions: three cards in their own colours (watchlist, Opportunity Hunter, paper trade), drawn as HTML with
   an invisible Streamlit button laid over each. A glass card with an edge whose light flows on hover, a gradient icon tile that
   tilts, an arrow that slides, a press that sinks; following a stock pops the star with a ring and a burst. On a phone the three
   sit side by side as tiles. */
.st-key-stkact {{ gap:10px !important; }}
[class*="st-key-stkact_"] {{ position:relative; gap:0 !important; }}
[class*="st-key-stkact_"] [data-testid="stElementContainer"] {{ position:static !important; margin:0 !important; }}
[class*="st-key-stkact_"] .stButton {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; }}
[class*="st-key-stkact_"] .stButton > div, [class*="st-key-stkact_"] [data-testid="stTooltipHoverTarget"] {{ width:100% !important; height:100% !important; }}
[class*="st-key-stkact_"] .stButton button {{ width:100% !important; height:100% !important; min-height:0 !important; padding:0 !important;
  opacity:0; cursor:pointer; border-radius:16px !important; }}
.st-key-stkact_wl, .st-key-stkact_wl_on {{ --acc:#F5B94A; --acc2:#F97316; --tint:rgba(245,185,74,.13); --edge:rgba(245,185,74,.36); --glow:rgba(245,185,74,.5); }}
.st-key-stkact_hn {{ --acc:#2DB6EB; --acc2:#3B8BEB; --tint:rgba(45,182,235,.12); --edge:rgba(45,182,235,.36); --glow:rgba(45,182,235,.5); }}
.st-key-stkact_pf {{ --acc:#A78BFA; --acc2:#7B45F0; --tint:rgba(167,139,250,.13); --edge:rgba(167,139,250,.38); --glow:rgba(123,69,240,.55); }}
.sax {{ position:relative; overflow:hidden; isolation:isolate; display:flex; align-items:center; gap:12px; min-height:66px; padding:10px 12px;
  border-radius:16px; border:1px solid transparent; color:#E9E5F0; box-sizing:border-box;
  background:linear-gradient(135deg, var(--tint), transparent 72%) padding-box, linear-gradient(rgba(17,12,30,.86), rgba(17,12,30,.86)) padding-box,
             linear-gradient(120deg, var(--edge), rgba(255,255,255,.07) 45%, var(--edge) 90%) border-box;
  background-size:100% 100%, 100% 100%, 240% 240%; background-position:0 0, 0 0, 0% 50%;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.06), 0 10px 24px -16px rgba(0,0,0,.75);
  transition:transform .25s cubic-bezier(.2,.8,.2,1), box-shadow .3s, background-position .8s ease; }}
.sax::before {{ content:""; position:absolute; inset:0; z-index:-1; border-radius:inherit; pointer-events:none; opacity:0;
  background:radial-gradient(circle at 26% 50%, var(--glow), transparent 62%); transition:opacity .35s; }}
.sax::after {{ content:""; position:absolute; top:0; bottom:0; left:-60%; width:40%; z-index:-1; pointer-events:none; transform:skewX(-20deg);
  background:linear-gradient(100deg, transparent, rgba(255,255,255,.14), transparent); transition:left .85s ease; }}
.sax .sx-ic {{ position:relative; flex:none; width:42px; height:42px; border-radius:13px; display:flex; align-items:center; justify-content:center;
  background:linear-gradient(140deg, var(--acc), var(--acc2)); color:#fff;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.35), inset 0 -8px 14px -10px rgba(0,0,0,.35), 0 8px 18px -8px var(--glow);
  transition:transform .4s cubic-bezier(.3,1.6,.5,1); }}
.sax .sx-ic .ms {{ font-size:1.35rem; color:#fff; }}
.sax .sx-tx {{ flex:1; min-width:0; display:flex; flex-direction:column; gap:2px; text-align:start; }}
.sax .sx-tx b {{ font-size:.95rem; font-weight:700; color:#F4F1F8; line-height:1.25; }}
.sax .sx-tx span {{ font-size:.74rem; color:#A8A2B3; line-height:1.3; }}
.sax .sx-go {{ position:relative; flex:none; width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center;
  color:var(--acc); background:var(--tint); box-shadow:inset 0 0 0 1px var(--edge); transition:transform .3s cubic-bezier(.3,1.6,.5,1), background .25s, color .25s; }}
.sax .sx-go .ms {{ font-size:1.1rem; }}
.sax .sx-go .h {{ display:none; }}
@media (hover:hover) {{
  [class*="st-key-stkact_"]:hover .sax {{ transform:translateY(-3px); background-position:0 0, 0 0, 100% 50%;
    box-shadow:0 18px 34px -18px var(--glow), inset 0 1px 0 rgba(255,255,255,.09); }}
  [class*="st-key-stkact_"]:hover .sax::before {{ opacity:.55; }}
  [class*="st-key-stkact_"]:hover .sax::after {{ left:130%; }}
  [class*="st-key-stkact_"]:hover .sx-ic {{ transform:rotate(-8deg) scale(1.08); }}
  [class*="st-key-stkact_"]:hover .sx-go {{ transform:translateX(3px); background:var(--acc); color:#140F24; }}
  [class*="st-key-stkact_"]:hover .sax.on .sx-go .a {{ display:none; }}
  [class*="st-key-stkact_"]:hover .sax.on .sx-go .h {{ display:inline; }}
}}
[class*="st-key-stkact_"]:has(button:active) .sax {{ transform:scale(.965); transition-duration:.08s; }}
[class*="st-key-stkact_"]:has(button:active) .sax::before {{ opacity:1; transition-duration:.05s; }}
[class*="st-key-stkact_"]:has(button:focus-visible) .sax {{ box-shadow:0 0 0 3px var(--glow); }}
.sax.on {{ background:linear-gradient(135deg, rgba(245,185,74,.30), rgba(245,185,74,.04) 78%) padding-box,
             linear-gradient(rgba(17,12,30,.86), rgba(17,12,30,.86)) padding-box,
             linear-gradient(120deg, #F5B94A, rgba(249,115,22,.55) 50%, #F5B94A 90%) border-box;
  background-size:100% 100%, 100% 100%, 240% 240%; box-shadow:0 12px 28px -16px rgba(245,185,74,.7), inset 0 1px 0 rgba(255,255,255,.08); }}
.sax.on .sx-tx b {{ color:#FCE3A6; }}
.sax.on .sx-ic .ms {{ font-variation-settings:'FILL' 1; animation:saxpop .65s cubic-bezier(.3,1.6,.5,1); }}
.sax.on .sx-ic::after {{ content:""; position:absolute; inset:-5px; border-radius:17px; border:2px solid #F5B94A; opacity:0; pointer-events:none;
  animation:saxring .9s ease-out; }}
.sax.on .sx-ic::before {{ content:""; position:absolute; left:50%; top:50%; width:6px; height:6px; margin:-3px 0 0 -3px; border-radius:50%;
  pointer-events:none; opacity:0; animation:saxburst .8s ease-out; }}
.sax.on .sx-go {{ background:var(--acc); color:#140F24; }}
@keyframes saxpop {{ 0% {{ transform:scale(.4) rotate(-40deg); }} 60% {{ transform:scale(1.3) rotate(10deg); }} 100% {{ transform:scale(1); }} }}
@keyframes saxring {{ 0% {{ opacity:.9; transform:scale(.8); }} 100% {{ opacity:0; transform:scale(1.5); }} }}
@keyframes saxburst {{
  0% {{ opacity:1; box-shadow:0 0 0 0 #F5B94A, 0 0 0 0 #F97316, 0 0 0 0 #FCD34D, 0 0 0 0 #F5B94A, 0 0 0 0 #F97316, 0 0 0 0 #FCD34D; }}
  100% {{ opacity:0; box-shadow:0 -32px 0 -1px #F5B94A, 28px -16px 0 -1px #F97316, 28px 16px 0 -1px #FCD34D, 0 32px 0 -1px #F5B94A,
    -28px 16px 0 -1px #F97316, -28px -16px 0 -1px #FCD34D; }} }}
@media (max-width: 640px) {{
  .st-key-stkact {{ flex-direction:row !important; flex-wrap:nowrap !important; gap:8px !important; }}
  .st-key-stkact > div {{ flex:1 1 0 !important; min-width:0 !important; width:auto !important; }}
  .sax {{ flex-direction:column; justify-content:flex-start; text-align:center; gap:9px; min-height:108px; padding:16px 6px 12px; }}
  .sax .sx-tx {{ flex:none; text-align:center; }}
  .sax .sx-tx b {{ font-size:.8rem; }}
  .sax .sx-tx span {{ display:none; }}
  .sax .sx-go {{ position:absolute; top:7px; inset-inline-end:7px; width:22px; height:22px; }}
  .sax .sx-go .ms {{ font-size:.85rem; }}
  .sax:not(.on) .sx-go {{ display:none; }}
}}
@media (prefers-reduced-motion: reduce) {{ .sax, .sax *, .sax::before, .sax::after {{ transition:none !important; animation:none !important; }} }}
/* inputs: every box you type in or pick from is clearly a box, a darker well than the card around it with a visible edge,
   a blue edge under the pointer and the electric ring when focused. Streamlit's own boxes (text, number, text area, date,
   selectbox / multiselect groups of the newer versions) and the older base-web ones. */
[data-testid="stTextInputRootElement"], [data-testid="stNumberInputContainer"], [data-testid="stTextAreaRootElement"],
[data-testid="stDateInputField"], [data-testid="stTimeInput"] [role="group"], [data-testid="stSelectbox"] [role="group"],
[data-testid="stMultiSelect"] [role="group"], [data-baseweb="select"] > div, [data-baseweb="textarea"],
div[data-baseweb="input"]:not([data-testid="stTextInputRootElement"] *):not([data-testid="stNumberInputContainer"] *) {{
  background-color:{FIELD} !important; border:1px solid {FIELD_EDGE} !important; border-radius:10px !important;
  box-shadow:inset 0 1px 3px rgba(0,0,0,.35) !important; transition:border-color .15s, box-shadow .15s; }}
[data-testid="stTextInputRootElement"] input, [data-testid="stNumberInputContainer"] input, [data-testid="stTextAreaRootElement"] textarea,
[data-baseweb="base-input"], [data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-testid="stSelectbox"] [role="group"] input,
[data-testid="stMultiSelect"] [role="group"] input {{ background-color:transparent !important; color:#F2EFF6 !important; }}
[data-testid="stTextInputRootElement"] input::placeholder, [data-testid="stNumberInputContainer"] input::placeholder, [data-testid="stTextAreaRootElement"] textarea::placeholder,
[data-testid="stSelectbox"] input::placeholder, [data-testid="stMultiSelect"] input::placeholder {{ color:#8F889B !important; opacity:1; }}
[data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"] {{ background:transparent !important; border-inline-start:1px solid rgba(157,151,165,.22) !important;
  color:#CFC8DA !important; }}
[data-testid="stNumberInputStepUp"]:hover, [data-testid="stNumberInputStepDown"]:hover {{ background:rgba(59,139,235,.16) !important; color:#fff !important; }}
[data-testid="stTextInputRootElement"]:hover, [data-testid="stNumberInputContainer"]:hover, [data-testid="stTextAreaRootElement"]:hover,
[data-testid="stDateInputField"]:hover, [data-testid="stSelectbox"] [role="group"]:hover, [data-testid="stMultiSelect"] [role="group"]:hover,
[data-baseweb="select"] > div:hover, div[data-baseweb="input"]:hover {{ border-color:rgba(121,184,244,.6) !important; }}
[data-testid="stTextInputRootElement"]:focus-within, [data-testid="stNumberInputContainer"]:focus-within, [data-testid="stTextAreaRootElement"]:focus-within,
[data-testid="stDateInputField"]:focus-within, [data-testid="stSelectbox"] [role="group"][data-focus-within], [data-testid="stSelectbox"] [role="group"]:focus-within,
[data-testid="stMultiSelect"] [role="group"]:focus-within, [data-baseweb="select"]:focus-within > div, [data-baseweb="textarea"]:focus-within,
div[data-baseweb="input"]:focus-within {{ border-color:#5B7CF2 !important; box-shadow:0 0 0 3px rgba(107,33,239,.24) !important; }}
[data-baseweb="popover"] ul, [data-baseweb="menu"] {{ background:{PANEL} !important; border:1px solid {SMOKE}; border-radius:12px; }}
[data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover {{ background:rgba(255,255,255,.05) !important; }}
[data-testid="stDialog"] [role="dialog"] {{ background:{CARD} !important; border:1px solid {SHELL}; border-radius:24px !important; box-shadow:{GLOW}, 0 30px 80px rgba(0,0,0,.6); }}
[data-testid="stPopoverBody"] {{ background:{CARD} !important; border:1px solid {SHELL} !important; border-radius:16px !important; }}
[data-testid="stSlider"] [role="slider"] {{ box-shadow:0 0 0 4px rgba(107,33,239,.25); }}
[data-testid="stDataFrame"], [data-testid="stTable"] {{ border-radius:14px; overflow:hidden; border:1px solid {BORDER}; }}
code {{ background:{PANEL}; color:#C4B5FD; border-radius:6px; }}
hr {{ border-color:{SHELL} !important; }}
.muted {{ color:{MUTED}; }} .acc {{ color:#79B8F4; }}
.upt {{ color:{UP}; }} .dnt {{ color:{DOWN}; }}
.num {{ font-variant-numeric: tabular-nums; direction:ltr; display:inline-block; }}
.card {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:16px; padding:16px 18px; margin-bottom:12px; }}
/* section titles and page titles: the icon sits in a workflow "node" (a small dark tile with a hairline and a violet under-glow) */
/* a section's title: big and clear (the page's chapters), its icon in a lit tile, a gradient rule that runs to the edge */
.sec {{ display:flex; align-items:center; gap:12px; font-size:1.2rem; letter-spacing:.005em; text-transform:none; color:#F4F1F8 !important;
  margin:36px 0 16px; font-weight:750; line-height:1.25; }}
.sec > span {{ flex:0 1 auto; min-width:0; }}
.sec::after {{ min-width:32px; }}
.sec .ms {{ color:#fff; background:linear-gradient(140deg,#3B8BEB,#7B45F0 70%,#A855F7); border-radius:12px; padding:7px; font-size:1.25rem;
  box-shadow:0 10px 22px -12px rgba(123,69,240,.9), inset 0 1px 0 rgba(255,255,255,.28); transition:transform .35s cubic-bezier(.3,1.6,.5,1); }}
.sec:hover .ms {{ transform:rotate(-8deg) scale(1.06); }}
.sec::after {{ content:""; flex:1; height:2px; border-radius:2px; background:linear-gradient(90deg, rgba(123,69,240,.7), rgba(45,182,235,.3) 35%, transparent);
  background-size:200% 100%; background-position:100% 0; transition:background-position .8s ease; }}
.sec:hover::after {{ background-position:0 0; }}
.page-title {{ display:flex; align-items:center; gap:14px; margin:4px 0 4px; }}
.page-title .ms {{ font-size:1.8rem; color:#fff; background:{PANEL}; border-radius:12px; padding:9px; box-shadow:{GLOW}; }}
.page-title h1 {{ margin:0 !important; padding:0 !important; }}
.page-sub {{ color:{MUTED}; font-size:.95rem; margin:4px 0 14px; }}
/* ---------- the colour rule: green for gains, red for losses, nothing else ---------- */
.pos {{ background:{POS_BG} !important; color:{POS_FG} !important; }}
.neg {{ background:{NEG_BG} !important; color:{NEG_FG} !important; }}
.pill {{ display:inline-block; min-width:74px; text-align:center; padding:4px 9px; border-radius:8px; font-weight:600; font-size:.82rem;
  font-variant-numeric: tabular-nums; direction:ltr; }}
.pill.pos {{ border:1px solid {POS_BD}; }} .pill.neg {{ border:1px solid {NEG_BD}; }}
.pill.neu {{ background:rgba(157,151,165,.15); color:{MUTED}; }}
.badge {{ display:inline-flex; align-items:center; gap:4px; padding:3px 10px; border-radius:20px; font-size:.76rem; font-weight:600; margin:2px 4px 2px 0; }}
.b-up {{ background:{POS_BG}; color:{POS_FG}; }} .b-down {{ background:{NEG_BG}; color:{NEG_FG}; }}
.b-neu {{ background:rgba(157,151,165,.16); color:#BBB5C3; }} .b-acc {{ background:{ACC_BG}; color:{ACC_FG}; }}
.b-vio {{ background:{VIO_BG}; color:{VIO_FG}; }} .b-gold {{ background:{YEL_BG}; color:{YEL_FG}; }} .b-org {{ background:{ORG_BG}; color:{ORG_FG}; }}
/* tiles */
.tiles {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(196px,1fr)); gap:10px; }}
.tile {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:14px; padding:11px 13px;
  transition: transform .15s, box-shadow .15s; }}
.tile:hover {{ transform: translateY(-2px); box-shadow: 0 10px 24px rgba(0,0,0,.35); }}
.tile.pos {{ background:{UP_TINT}, {CARD} !important; border-color:{UP_EDGE}; }}
.tile.neg {{ background:{DN_TINT}, {CARD} !important; border-color:{DN_EDGE}; }}
.tile.acc {{ background:linear-gradient(180deg, rgba(59,139,235,.18), rgba(59,139,235,.06)), {CARD}; border-color:rgba(59,139,235,.45); color:{ACC_FG}; }}
.t-name {{ color:{MUTED}; font-size:.78rem; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.tile.pos .t-name {{ color:#8FD4A9; }} .tile.neg .t-name {{ color:#E7A2A9; }} .tile.acc .t-name {{ color:#9DB9EE; }}
.t-row {{ display:flex; justify-content:space-between; align-items:flex-end; gap:6px; direction:ltr; }}
.t-val {{ font-size:1.18rem; font-weight:600; margin-top:2px; font-variant-numeric: tabular-nums; }}
.t-chg {{ font-size:.8rem; font-weight:600; margin-top:2px; white-space:nowrap; font-variant-numeric: tabular-nums; }}
.t-sub {{ color:{MUTED}; font-size:.7rem; margin-top:3px; }}
.tile.pos .t-sub {{ color:#72B98E; }} .tile.neg .t-sub {{ color:#C98890; }} .tile.acc .t-sub {{ color:#86A3D8; }}
/* hero */
.hero {{ position:relative; height:290px; border-radius:20px; overflow:hidden; border:1px solid {BORDER}; margin-bottom:14px;
  background: linear-gradient(120deg, #0E0918, #1B1430, #27184A, #130F24); background-size:300% 300%; animation: sky 20s ease-in-out infinite; }}
@keyframes sky {{ 0% {{ background-position:0% 50%; }} 50% {{ background-position:100% 50%; }} 100% {{ background-position:0% 50%; }} }}
.hero svg.city {{ position:absolute; left:0; right:0; bottom:0; width:100%; height:100%; }}
.hero .content {{ position:absolute; inset:0; padding:30px 34px; display:flex; flex-direction:column;
  background: linear-gradient(90deg, rgba(14,9,24,.88) 0%, rgba(14,9,24,.35) 55%, rgba(14,9,24,0) 100%); }}
.rtl .hero .content {{ background: linear-gradient(270deg, rgba(14,9,24,.88) 0%, rgba(14,9,24,.35) 55%, rgba(14,9,24,0) 100%); }}
.hero .eyebrow {{ color:{CYAN}; font-weight:600; letter-spacing:.2em; font-size:.74rem; text-transform:uppercase; }}
.hero .title {{ font-size:2.8rem; font-weight:300; line-height:1.04; margin:8px 0 8px; color:#fff; letter-spacing:-.035em; }}
.hero .title b {{ background: linear-gradient(90deg,{ACCENT},{VIOLET},{CYAN}); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.hero .tagline {{ color:#CAC5D1; max-width:560px; font-size:.98rem; line-height:1.65; }}
.hero .chips {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:16px; direction:ltr; }}
.rtl .hero .chips {{ justify-content:flex-end; }}
.hero .chip {{ background:rgba(26,22,36,.8); border:1px solid {BORDER}; backdrop-filter: blur(6px); border-radius:10px; padding:6px 10px; font-size:.82rem;
  font-variant-numeric: tabular-nums; display:inline-flex; align-items:center; gap:7px; }}
.hero .chip b {{ color:#fff; }} .hero .chip .pill {{ min-width:0; padding:2px 7px; font-size:.75rem; }}
/* ticker tape */
.tape {{ direction:ltr; overflow:hidden; white-space:nowrap; border:1px solid {BORDER}; border-radius:12px; background:{BOX_BG};
  margin-bottom:14px; mask-image: linear-gradient(90deg, transparent, #000 4%, #000 96%, transparent); }}
.tape .track {{ display:inline-flex; gap:26px; padding:8px 0; animation: tape 70s linear infinite; }}
.tape:hover .track {{ animation-play-state: paused; }}
.tape .it {{ font-size:.84rem; font-variant-numeric: tabular-nums; display:inline-flex; align-items:center; gap:7px; }}
.tape .it b {{ color:#fff; }} .tape .it .pill {{ min-width:0; padding:2px 7px; font-size:.74rem; }}
@keyframes tape {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}
/* company logo circle + rows */
.lg {{ position:relative; flex:none; display:inline-flex; align-items:center; justify-content:center; border-radius:50%; overflow:hidden;
  color:#fff; font-weight:600; letter-spacing:-.02em; vertical-align:middle; box-shadow: 0 0 0 1px rgba(255,255,255,.08); }}
.lg img {{ width:100%; height:100%; object-fit:contain; background:#fff; padding:12%; box-sizing:border-box; }}
.co {{ display:flex; align-items:center; gap:10px; min-width:0; }}
.co .nm {{ min-width:0; }} .co .tk {{ font-weight:600; color:#fff; }}
.co .sub {{ color:{MUTED}; font-size:.76rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:190px; }}
a.lnk {{ color:inherit !important; text-decoration:none !important; }} a.lnk:hover .tk {{ color:#79B8F4; text-decoration:underline; }}
.rowlist {{ display:flex; flex-direction:column; }}
.rw {{ display:grid; grid-template-columns: minmax(0,1fr) auto auto; gap:12px; align-items:center; padding:9px 4px; border-bottom:1px solid {BORDER}; direction:ltr; }}
.rw:last-child {{ border-bottom:none; }} .rw:hover {{ background:rgba(59,139,235,.06); border-radius:10px; }}
.px {{ font-variant-numeric: tabular-nums; font-weight:600; text-align:right; }}
.meter {{ height:5px; border-radius:3px; background:{BORDER}; overflow:hidden; margin-top:4px; }}
.meter span {{ display:block; height:100%; background:linear-gradient(90deg,{ACCENT},{VIOLET}); }}
.mcard {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:16px; padding:14px 14px 6px; height:100%; }}
.mcard .hd {{ display:flex; align-items:center; gap:8px; font-weight:600; margin-bottom:6px; }}
.mcard .hd .ms {{ color:#fff; background:{PANEL}; box-shadow:{GLOW}; border-radius:8px; padding:4px; font-size:1.05rem; }}
.mcard .hd .cnt {{ margin-inline-start:auto; color:{MUTED}; font-size:.75rem; font-weight:600; }}
/* Movers at a glance: Streamlit pulls every markdown block 1rem up (margin-bottom:-1rem), so a card stretched to its
   column ran 1rem past it and the two rows of cards touched; without that pull the rows (and the cards stacked on a
   phone) keep the same 1rem gap as the cards side by side */
[class*="st-key-mvrow_"] :is(.stMarkdown, [data-testid="stMarkdownContainer"]) {{ margin-bottom:0 !important; }}
.lead {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:10px; }}
.lc {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:14px; padding:12px; direction:ltr; }}
.lc .top {{ display:flex; justify-content:space-between; align-items:center; gap:8px; }}
.lc .bot {{ display:flex; justify-content:space-between; align-items:flex-end; margin-top:10px; gap:8px; }}
.lc .rank {{ color:{MUTED}; font-size:.75rem; font-weight:600; }}
/* quote */
.q-name {{ color:{MUTED}; font-size:.95rem; }}
.q-price {{ font-size:2.8rem; font-weight:300; line-height:1.15; font-variant-numeric: tabular-nums; direction:ltr; display:inline-block; letter-spacing:-.02em; }}
.q-chg {{ font-size:1rem; font-weight:600; direction:ltr; display:inline-block; padding:4px 10px; border-radius:9px; }}
.q-chg.pos {{ border:1px solid {POS_BD}; }} .q-chg.neg {{ border:1px solid {NEG_BD}; }} .q-chg.neu {{ background:rgba(157,151,165,.15); color:{MUTED}; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(134px,1fr)); gap:8px; margin:8px 0; }}
.stat {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:10px; padding:8px 11px; }}
.stat .l {{ color:{MUTED}; font-size:.72rem; }} .stat .v {{ font-weight:600; font-size:.93rem; }}
.range {{ position:relative; height:6px; background:linear-gradient(90deg,{DOWN},{GOLD},{UP}); border-radius:3px; margin:10px 0 22px; opacity:.85; }}
.range .dot {{ position:absolute; top:-5px; width:16px; height:16px; border-radius:50%; background:#fff; border:3px solid {BG}; }}
.plan {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(160px,1fr)); gap:8px; }}
.plan .p {{ background:{BOX_BG}; border-radius:12px; padding:10px 13px; border:1px solid {BORDER}; }}
.plan .p .l {{ color:{MUTED}; font-size:.72rem; font-weight:600; }} .plan .p .v {{ font-size:1.05rem; font-weight:600; direction:ltr; display:inline-block; }}
.plan .p.pos, .plan .p.neg, .plan .p.acc {{ border-color:transparent; }}
.plan .p.pos .l {{ color:#8FD4A9; }} .plan .p.neg .l {{ color:#E7A2A9; }}
.plan .p.acc {{ background:{TOP}, {ACC_BG}; color:{ACC_FG}; border-color:rgba(59,139,235,.45); }} .plan .p.acc .l {{ color:#9DB9EE; }}
/* profile */
.prof {{ display:grid; grid-template-columns: repeat(auto-fill,minmax(220px,1fr)); gap:10px; }}
.prof .it {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:12px; padding:10px 12px; }}
.prof .it .l {{ color:{MUTED}; font-size:.72rem; display:flex; gap:6px; align-items:center; }}
.prof .it .v {{ font-weight:500; margin-top:3px; }}
.desc {{ line-height:1.9; font-size:.97rem; color:#D7D3DD; }}
/* news */
.news {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:14px; padding:14px 16px; margin-bottom:10px; transition:border-color .15s; }}
.news:hover {{ border-color:{ACCENT}; }}
/* the News page: the "analyse this story" button sits in the card's own foot (the card keeps a strip for it at the bottom) */
[class*="st-key-nwc_"] {{ gap:0 !important; margin-bottom:12px; position:relative; }}
[class*="st-key-nwc_"] .news {{ margin-bottom:0; }}
.news.hasft {{ padding-bottom:58px; }}
[class*="st-key-nwc_"] [data-testid="stElementContainer"]:has(.stButton) {{ position:absolute; bottom:12px; inset-inline-end:16px; width:auto !important; z-index:2; }}
[class*="st-key-nwc_"] .stButton button {{ min-height:34px !important; padding:4px 16px !important; border-radius:999px !important; font-size:.82rem; font-weight:650;
  background:linear-gradient(135deg, rgba(59,139,235,.22), rgba(123,69,240,.30)) !important; border:1px solid rgba(167,139,250,.5) !important;
  color:#E9E3FF !important; box-shadow:0 8px 18px -12px rgba(123,69,240,.9) !important; transition:transform .15s, background .2s; }}
[class*="st-key-nwc_"] .stButton button:hover {{ background:linear-gradient(135deg, #3B8BEB, #7B45F0) !important; color:#fff !important; transform:translateY(-1px); }}
/* What's Trending: the companies the news talks about most (rank, logo, name, stories, today's move, a bar of how much) */
.tktg {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:12px; }}
@media (max-width: 1100px) {{ .tktg {{ grid-template-columns:repeat(2, minmax(0,1fr)); }} }}
@media (max-width: 560px) {{ .tktg {{ grid-template-columns:1fr; }} }}
a.tkt {{ position:relative; display:grid; grid-template-columns:22px 34px minmax(0,1fr) auto; grid-template-rows:auto auto; column-gap:10px;
  row-gap:2px; align-items:center; padding:12px 14px 16px; border-radius:16px; overflow:hidden;
  background:{BOX_BG}; border:1px solid {BORDER}; text-decoration:none !important; color:inherit !important;
  transition:transform .18s, border-color .2s, box-shadow .2s; }}
a.tkt:hover {{ transform:translateY(-2px); border-color:rgba(167,139,250,.55); box-shadow:0 16px 30px -20px rgba(123,69,240,.85); }}
a.tkt .rk {{ grid-row:1 / 3; width:22px; height:22px; border-radius:7px; display:grid; place-items:center; font-size:.72rem; font-weight:800;
  color:#E9E3FF; background:linear-gradient(140deg,#3B8BEB,#7B45F0); }}
a.tkt .lg {{ grid-row:1 / 3; display:grid; place-items:center; }}
a.tkt .nm {{ grid-column:3; min-width:0; color:#fff; font-size:.92rem; font-weight:750; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
a.tkt .mv {{ grid-column:4; grid-row:1; }}
a.tkt .sub {{ grid-column:3 / 5; grid-row:2; color:{MUTED}; font-size:.72rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
a.tkt .bar {{ position:absolute; inset-inline-start:0; bottom:0; height:3px; border-radius:0 3px 3px 0;
  background:linear-gradient(90deg,#5088F2,#DF4E92); box-shadow:0 0 10px rgba(223,78,146,.55); }}
/* the News page's filters: one panel */
.st-key-nwfilt {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:18px; padding:14px 18px 16px; gap:12px !important; margin-bottom:6px; }}
/* the same event told by other outlets: a drawer at the card's foot */
.ncov {{ margin:12px 0 0; border-top:1px dashed rgba(157,151,165,.22); padding-top:10px; }}
.ncov summary {{ list-style:none; cursor:pointer; display:inline-flex; align-items:center; gap:7px; font-size:.8rem; font-weight:650; color:#C4B5FD;
  padding:5px 12px; border-radius:999px; background:rgba(123,69,240,.10); border:1px solid rgba(167,139,250,.28); transition:background .2s; }}
.ncov summary::-webkit-details-marker {{ display:none; }}
.ncov summary:hover {{ background:rgba(123,69,240,.22); color:#fff; }}
.ncov summary .ms {{ font-size:1.05rem; }}
.ncov summary .ms:last-child {{ transition:transform .25s; }}
.ncov[open] summary .ms:last-child {{ transform:rotate(180deg); }}
.ncov ul {{ list-style:none; margin:10px 0 0; padding:0; display:grid; gap:6px; }}
.ncov li {{ display:flex; justify-content:space-between; gap:14px; align-items:baseline; padding:8px 12px; border-radius:10px;
  background:rgba(255,255,255,.03); border:1px solid rgba(157,151,165,.12); }}
.ncov li a {{ color:#E7E3EB !important; text-decoration:none !important; font-size:.86rem; font-weight:550; line-height:1.45; }}
.ncov li a:hover {{ color:#79B8F4 !important; }}
.ncov li span {{ flex:none; color:{MUTED}; font-size:.74rem; white-space:nowrap; }}
@media (max-width: 640px) {{ .ncov li {{ flex-direction:column; gap:2px; }} }}
.news a.t {{ color:{TEXT}; text-decoration:none; font-weight:600; font-size:1rem; line-height:1.65; }}
.news a.t:hover {{ color:#79B8F4; }}
.news .meta {{ color:{MUTED}; font-size:.78rem; margin-top:4px; }}
.news .sum {{ color:{MUTED}; font-size:.88rem; margin-top:6px; line-height:1.75; }}
.news .nh {{ display:flex; gap:14px; align-items:flex-start; }}
.news .nb {{ flex:1; min-width:0; }}
.news.hasiq {{ border-inline-start: 4px solid var(--iqd); }}
.iq {{ flex:none; width:88px; text-align:center; border-radius:12px; padding:7px 6px 6px; background:var(--iqb); color:var(--iqf); border:1px solid var(--iqd); cursor:help; }}
.iq .n {{ font-size:1.35rem; font-weight:600; line-height:1.1; direction:ltr; font-variant-numeric: tabular-nums; }}
.iq .n small {{ font-size:.68rem; font-weight:600; opacity:.7; }}
.iq .l {{ font-size:.64rem; font-weight:600; margin-top:2px; line-height:1.25; }}
.iq .bar {{ height:4px; border-radius:3px; background:rgba(0,0,0,.09); margin-top:5px; overflow:hidden; direction:ltr; }}
.iq .bar i {{ display:block; height:100%; background:var(--iqf); opacity:.55; border-radius:3px; }}
.kw {{ display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; }}
.kwc {{ display:inline-flex; align-items:center; gap:5px; padding:3px 10px 3px 8px; border-radius:20px; font-size:.74rem; font-weight:600;
  background:rgba(59,139,235,.1); color:#BFDDF8; border:1px solid rgba(59,139,235,.26); white-space:nowrap; }}
.kwc .ms {{ font-size:.95rem; color:#79B8F4; }}
.kwc.ent {{ background:rgba(123,69,240,.1); color:#D9CCFC; border-color:rgba(123,69,240,.3); }} .kwc.ent .ms {{ color:#A78BFA; }}
.kwc.op {{ background:rgba(157,151,165,.12); color:#BBB5C3; border-color:rgba(157,151,165,.26); }} .kwc.op .ms {{ color:#9D97A5; }}
.iqleg {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; font-size:.78rem; font-weight:600; }}
.iqleg .sc {{ display:flex; gap:3px; direction:ltr; }}
.iqleg .sc span {{ width:30px; height:24px; border-radius:6px; display:inline-flex; align-items:center; justify-content:center; font-size:.74rem; font-weight:600; }}
.aff {{ margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; align-items:center; }}
.aff .lbl {{ color:{MUTED}; font-size:.74rem; margin-inline-end:4px; }}
.tkc {{ direction:ltr; display:inline-flex; gap:6px; align-items:center; border-radius:20px; padding:3px 10px 3px 3px; font-size:.78rem; font-weight:600;
  border:1px solid {BORDER}; background:{CARD2}; color:{TEXT}; font-variant-numeric: tabular-nums; text-decoration:none !important; }}
.tkc.pos {{ border-color:{POS_BD}; }} .tkc.neg {{ border-color:{NEG_BD}; }}
.story {{ position:relative; background:{BOX_BG}; border:1px solid {BORDER}; border-radius:16px; padding:16px 18px; height:100%; }}
.story .rank {{ position:absolute; top:10px; inset-inline-end:14px; font-size:1.9rem; font-weight:600; color:rgba(59,139,235,.25); }}
.story a.t {{ color:#fff; text-decoration:none; font-weight:600; font-size:1.02rem; line-height:1.6; display:block; margin-inline-end:36px; }}
.story a.t:hover {{ color:#79B8F4; }}
.status {{ display:inline-flex; align-items:center; gap:7px; font-size:.8rem; padding:6px 12px; border-radius:20px; background:{CARD}; border:1px solid {BORDER}; }}
.dot {{ width:8px; height:8px; border-radius:50%; display:inline-block; }}
.dot.live {{ background:{UP}; animation: pulse 1.8s infinite; }} .dot.pre {{ background:{GOLD}; }} .dot.closed {{ background:{DOWN}; }}
@keyframes pulse {{ 0% {{ box-shadow:0 0 0 0 rgba(34,197,94,.6); }} 70% {{ box-shadow:0 0 0 8px rgba(34,197,94,0); }} 100% {{ box-shadow:0 0 0 0 rgba(34,197,94,0); }} }}
.wl {{ font-size:.82rem; text-align:right; padding-top:4px; line-height:1.25; direction:ltr; }}
.check {{ padding:9px 0; border-bottom:1px solid {BORDER}; font-size:.9rem; display:flex; gap:10px; align-items:flex-start; }}
.ico {{ flex:none; width:26px; height:26px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; }}
.ico .ms {{ font-size:1.05rem; vertical-align:0; }}
.summary li {{ margin-bottom:6px; line-height:1.8; }}
/* ---------- the top stories, ranked by size: the first card is the biggest, the second a step smaller, the third smaller again ---------- */
.stories {{ display:grid; grid-template-columns: 1.16fr 1fr .86fr; gap:16px; align-items:stretch; }}
.stories.n2 {{ grid-template-columns: 1.16fr 1fr; }} .stories.n1 {{ grid-template-columns: 1fr; }}
.stories > .story {{ height:auto; min-width:0; }}
.stories > .story.r2 {{ margin-bottom:30px; }}
.stories > .story.r3 {{ margin-bottom:60px; }}
.stories > .story.r1 .nth.big {{ height:176px; }}
.stories > .story.r2 .nth.big {{ height:152px; }}
.stories > .story.r3 .nth.big {{ height:130px; }}
.stories > .story.r1 a.t {{ font-size:1.12rem; }}
.stories > .story.r3 a.t {{ font-size:.96rem; }}
@media (max-width: 900px) {{ .stories, .stories.n2 {{ grid-template-columns:1fr; }} .stories > .story.r2, .stories > .story.r3 {{ margin-bottom:0; }} }}
/* ---------- market summary: the day's tone and breadth, then a tile for each part of the market ---------- */
.msum {{ display:flex; flex-direction:column; gap:14px; }}
.msum .upt {{ color:{POS_FG}; }} .msum .dnt {{ color:{NEG_FG}; }}
.msh {{ display:grid; grid-template-columns: minmax(0,1.1fr) minmax(0,1fr); gap:18px; align-items:center; padding:18px 20px; border-radius:18px;
  background:{BOX_BG}; border:1px solid {BORDER}; position:relative; overflow:hidden; }}
.msh::before {{ content:""; position:absolute; inset:0; pointer-events:none; opacity:.9;
  background: radial-gradient(520px 160px at 0% 0%, rgba(123,69,240,.20), transparent 70%); }}
.msh.t-u::before {{ background: radial-gradient(520px 160px at 0% 0%, rgba(34,197,94,.18), transparent 70%); }}
.msh.t-d::before {{ background: radial-gradient(520px 160px at 0% 0%, rgba(239,68,68,.18), transparent 70%); }}
.msh > * {{ position:relative; }}
.msh .tone {{ display:flex; gap:14px; align-items:center; }}
.msh .ti {{ flex:none; width:52px; height:52px; border-radius:16px; display:flex; align-items:center; justify-content:center; background:{VIO_BG};
  box-shadow:{GLOW}; }}
.msh .ti .ms {{ font-size:28px; color:{VIO_FG}; }}
.msh.t-u .ti {{ background:{POS_BG}; }} .msh.t-u .ti .ms {{ color:{POS_FG}; }}
.msh.t-d .ti {{ background:{NEG_BG}; }} .msh.t-d .ti .ms {{ color:{NEG_FG}; }}
.msh .tt {{ font-size:1.35rem; font-weight:600; letter-spacing:-.01em; color:#fff; }}
.msh .ix {{ margin-top:4px; color:{MUTED}; font-size:.86rem; display:flex; flex-wrap:wrap; gap:4px 10px; }}
.msh .ix b {{ font-weight:600; font-variant-numeric:tabular-nums; }}
.brd .bl {{ display:flex; justify-content:space-between; align-items:baseline; font-size:.8rem; color:{MUTED}; font-weight:600; letter-spacing:.02em; }}
.brd .bl b {{ color:#fff; font-size:1.05rem; }}
.brd .bar {{ display:flex; gap:3px; height:12px; margin:8px 0 7px; border-radius:8px; overflow:hidden; background:rgba(255,255,255,.06); }}
.brd .bar i {{ display:block; height:100%; transform-origin:left; animation: msgrow .9s cubic-bezier(.2,.8,.2,1) both; }}
.brd .bar i.u {{ background:linear-gradient(90deg,#16A34A,{POS_FG}); border-radius:8px; }}
.brd .bar i.d {{ background:linear-gradient(90deg,{NEG_FG},#DC2626); border-radius:8px; margin-inline-start:auto; transform-origin:right; }}
.rtl .brd .bar i.u, .rtl .mst .rows .b i {{ transform-origin:right; }} .rtl .brd .bar i.d {{ transform-origin:left; }}
.brd .bc {{ display:flex; justify-content:space-between; font-size:.78rem; font-weight:600; font-variant-numeric:tabular-nums; }}
@keyframes msgrow {{ from {{ transform:scaleX(0); }} to {{ transform:scaleX(1); }} }}
.msg {{ display:grid; grid-template-columns: minmax(0,1.25fr) repeat(2, minmax(0,1fr)); gap:14px; }}
.mst {{ position:relative; display:flex; flex-direction:column; gap:8px; padding:14px 16px; border-radius:16px; background:{BOX_BG}; border:1px solid {BORDER};
  color:{TEXT} !important; text-decoration:none !important; transition: border-color .2s, transform .2s; min-width:0; }}
a.mst:hover {{ border-color: rgba(123,69,240,.45); }}
.mst.wide {{ grid-row: span 2; }}
.mst .mh {{ display:flex; align-items:center; gap:8px; font-size:.74rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:{MUTED}; }}
.mst .mh .ms {{ font-size:18px; color:{VIO_FG}; }}
.mst .mh .go {{ margin-inline-start:auto; font-size:17px; color:{MUTED}; opacity:0; transform:translate(-4px,4px); transition: opacity .2s, transform .2s; }}
a.mst:hover .mh .go {{ opacity:1; transform:none; color:{VIO_FG}; }}
.rtl .mst .mh .go {{ transform:translate(4px,4px) scaleX(-1); }} .rtl a.mst:hover .mh .go {{ transform:scaleX(-1); }}
.mst .mb {{ flex:1; display:flex; flex-direction:column; gap:6px; }}
.mst .big {{ font-size:1.5rem; font-weight:600; color:#fff; font-variant-numeric:tabular-nums; display:flex; align-items:baseline; gap:8px; flex-wrap:wrap; }}
.mst .big b {{ font-size:.9rem; font-weight:600; }}
.mst .sub {{ font-size:.8rem; color:{MUTED}; }}
.mst .why {{ font-size:.72rem; line-height:1.5; color:{MUTED}; opacity:.85; border-top:1px dashed {BORDER}; padding-top:8px; }}
.mst .gauge {{ position:relative; height:8px; margin-top:6px; border-radius:6px;
  background:linear-gradient(90deg, #16A34A 0%, #84CC16 30%, {GOLD} 55%, #F97316 75%, #DC2626 100%); opacity:.9; }}
.mst .gauge span {{ position:absolute; top:-2px; bottom:-2px; width:1px; background:rgba(255,255,255,.35); }}
.mst .gauge i {{ position:absolute; top:50%; width:16px; height:16px; margin-left:-8px; translate:0 -50%; border-radius:50%; background:#fff;
  box-shadow:0 0 0 3px rgba(14,9,24,.85), 0 2px 10px rgba(0,0,0,.5); transition: left .6s ease; }}
.mst .gl {{ display:flex; justify-content:space-between; font-size:.64rem; color:{MUTED}; font-variant-numeric:tabular-nums; }}
.mst .rows {{ display:flex; flex-direction:column; gap:10px; margin-top:2px; }}
.mst .rows .r, .mst .secs .sr {{ display:grid; grid-template-columns: minmax(0,1fr) minmax(0,1.2fr) auto; gap:10px; align-items:center; font-size:.84rem; }}
.mst .rows .n, .mst .secs .n {{ color:{TEXT}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.mst .rows .b {{ height:8px; border-radius:6px; background:rgba(255,255,255,.06); overflow:hidden; display:flex; }}
.mst .rows .b i {{ display:block; height:100%; border-radius:6px; transform-origin:left; animation: msgrow .9s cubic-bezier(.2,.8,.2,1) both; }}
.mst :is(.rows, .secs) .b i.u {{ background:{POS_FG}; }} .mst :is(.rows, .secs) .b i.d {{ background:{NEG_FG}; }}
.mst :is(.rows, .secs) .b i.z {{ background:{MUTED}; }}
.mst :is(.rows, .secs) b {{ font-size:.82rem; font-variant-numeric:tabular-nums; min-width:58px; text-align:end; }}
.mst .secs {{ flex:1; display:flex; flex-direction:column; justify-content:space-between; gap:3px; }}
.mst .secs .sr {{ grid-template-columns: minmax(0,1.15fr) minmax(0,1fr) auto; padding:5px 8px; border-radius:9px; transition: background .15s; }}
.mst .secs .sr:hover {{ background:rgba(123,69,240,.14); }}
.mst .secs .b {{ position:relative; height:10px; }}
.mst .secs .b::before {{ content:""; position:absolute; inset-inline-start:50%; top:-3px; bottom:-3px; width:1px; background:rgba(255,255,255,.18); }}
.mst .secs .b i {{ position:absolute; top:0; bottom:0; display:block; border-radius:5px; animation: msgrow .9s cubic-bezier(.2,.8,.2,1) both; }}
.mst .secs .b i.u {{ inset-inline-start:50%; transform-origin:left; }}
.mst .secs .b i.d {{ inset-inline-end:50%; transform-origin:right; }}
.rtl .mst .secs .b i.u {{ transform-origin:right; }} .rtl .mst .secs .b i.d {{ transform-origin:left; }}
.mst .mvr {{ display:flex; align-items:center; gap:10px; padding:8px; margin:0 -8px; border-radius:12px; text-decoration:none !important; color:{TEXT} !important;
  transition: background .15s; }}
.mst .mvr:hover {{ background:rgba(123,69,240,.14); }}
.mst .mvr .nm {{ flex:1; min-width:0; display:flex; flex-direction:column; line-height:1.25; }}
.mst .mvr small {{ font-size:.66rem; color:{MUTED}; font-weight:600; text-transform:uppercase; letter-spacing:.05em; }}
.mst .mvr b {{ font-size:.95rem; color:#fff; }}
.mst .mvr em {{ font-style:normal; font-size:.72rem; color:{MUTED}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.mst .chips {{ display:flex; flex-wrap:wrap; gap:6px; }}
.mst .mchip {{ display:inline-flex; gap:6px; align-items:baseline; padding:4px 10px; border-radius:20px; font-size:.78rem; font-weight:600;
  border:1px solid {BORDER}; background:{CARD2}; color:{TEXT} !important; text-decoration:none !important; transition: border-color .15s; }}
.mst .mchip:hover {{ border-color: rgba(123,69,240,.55); }} .mst .mchip b {{ font-size:.74rem; }}
.mst .shl {{ margin-top:6px; font-size:.66rem; color:{MUTED}; font-weight:600; text-transform:uppercase; letter-spacing:.05em; }}
@media (max-width: 1100px) {{ .msg {{ grid-template-columns: repeat(2, minmax(0,1fr)); }} .mst.wide {{ grid-row:auto; }} }}
@media (max-width: 700px) {{ .msh {{ grid-template-columns: 1fr; }} .msg {{ grid-template-columns: 1fr; }} .mst.wide {{ grid-column:auto; grid-row:auto; }} }}
@media (prefers-reduced-motion: reduce) {{ .msum *, .msum *::before {{ animation:none !important; transition:none !important; }} }}
.kpi {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:14px; padding:14px 16px; height:100%; }}
.kpi.pos, .kpi.neg {{ border-color:transparent; }}
.kpi .l {{ color:{MUTED}; font-size:.75rem; font-weight:500; display:flex; gap:6px; align-items:center; }}
.kpi.pos .l {{ color:#8FD4A9; }} .kpi.neg .l {{ color:#E7A2A9; }}
.kpi .v {{ font-size:1.25rem; font-weight:600; margin-top:6px; display:flex; align-items:center; gap:8px; direction:ltr; }}
.kpi .s {{ font-size:.8rem; margin-top:4px; font-weight:500; }}
.kpi:not(.pos):not(.neg):not(.acc) .v {{ color:#fff; }}
.kpi.acc {{ background:linear-gradient(180deg, rgba(59,139,235,.18), rgba(59,139,235,.06)), {CARD}; color:{ACC_FG}; border-color:rgba(59,139,235,.45); }} .kpi.acc .l {{ color:#9DB9EE; }}
/* rating meter (technicals) */
.rmeter {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:16px; padding:16px; }}
.rmeter .rt {{ color:{MUTED}; font-size:.78rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase; }}
.rmeter .rv {{ display:inline-block; margin:8px 0 14px; padding:5px 12px; border-radius:10px; font-weight:600; font-size:1.15rem; }}
.rbar {{ position:relative; display:grid; grid-template-columns:repeat(5,1fr); gap:4px; height:10px; direction:ltr; }}
.rbar span {{ border-radius:6px; }}
.rbar i {{ position:absolute; top:-9px; width:0; height:0; border-left:8px solid transparent; border-right:8px solid transparent; border-top:10px solid #fff;
  filter: drop-shadow(0 2px 3px rgba(0,0,0,.5)); }}
.rlab {{ display:grid; grid-template-columns:repeat(5,1fr); font-size:.66rem; color:{MUTED}; margin-top:6px; text-align:center; direction:ltr; }}
.rcnt {{ display:flex; gap:6px; margin-top:12px; flex-wrap:wrap; }}
/* price ladder */
.ladder {{ display:flex; flex-direction:column; gap:5px; direction:ltr; }}
.lr {{ display:grid; grid-template-columns: 70px 1fr auto; gap:10px; align-items:center; padding:7px 10px; border-radius:10px; background:{BOX_BG};
  border:1px solid {BORDER}; font-variant-numeric: tabular-nums; }}
.lr .ln {{ font-weight:600; font-size:.8rem; }} .lr .lp {{ font-weight:600; color:#E7E3EB; }}
.lr.res .ln {{ color:#F87171; }} .lr.sup .ln {{ color:#4ADE80; }} .lr.piv .ln {{ color:#93C5FD; }}
.lr.now {{ background:{TOP}, linear-gradient(90deg, rgba(59,139,235,.3), rgba(123,69,240,.25)); border-color:{ACCENT}; }}
.lr.now .ln, .lr.now .lp {{ color:#fff; }}
/* sector cards / breadth */
.secgrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(172px,1fr)); gap:10px; }}
.sc {{ border-radius:14px; padding:11px 12px; border:1px solid transparent; }}
.secgrid .sc {{ border-color:{BORDER}; background:{BOX_BG}; }}
.secgrid .sc.pos {{ background:{UP_TINT}, {CARD} !important; border-color:{UP_EDGE}; }} .secgrid .sc.neg {{ background:{DN_TINT}, {CARD} !important; border-color:{DN_EDGE}; }}
.sc .h {{ display:flex; justify-content:space-between; font-weight:600; font-size:.8rem; }} .sc .v {{ font-size:1.25rem; font-weight:600; margin-top:4px; direction:ltr; }}
.sc .f {{ display:flex; gap:8px; font-size:.7rem; font-weight:600; margin-top:4px; direction:ltr; opacity:.85; }}
.bars .b {{ margin:10px 0; }} .bars .b .t {{ display:flex; justify-content:space-between; font-size:.82rem; font-weight:500; }}
.bars .b .trk {{ height:10px; border-radius:6px; background:{BORDER}; overflow:hidden; margin-top:5px; }}
.bars .b .trk span {{ display:block; height:100%; border-radius:6px; }}
.adbar {{ display:flex; height:14px; border-radius:8px; overflow:hidden; gap:3px; direction:ltr; }}
.adbar span {{ display:block; height:100%; }}
/* options chain */
.chain {{ width:100%; border-collapse:separate; border-spacing:0; font-size:.8rem; direction:ltr; font-variant-numeric: tabular-nums; }}
.chain th {{ position:sticky; top:0; background:{CARD2}; color:{MUTED}; font-weight:500; padding:7px 6px; text-align:right; border-bottom:1px solid {BORDER}; }}
.chain th.side {{ text-align:center; font-size:.84rem; }}
.chain td {{ padding:6px 6px; text-align:right; border-bottom:1px solid rgba(44,39,56,.6); }}
.chain td.k {{ text-align:center; font-weight:600; color:#fff; background:{CARD2}; }}
.chain tr:hover td {{ background:rgba(59,139,235,.08); }}
.chain td.itm-c {{ background:rgba(209,231,221,.10); }} .chain td.itm-p {{ background:rgba(248,215,218,.10); }}
.chain tr.atm td {{ border-top:2px solid {ACCENT}; }}
.chain .cp {{ padding:1px 6px; border-radius:6px; font-weight:600; }}
.chainwrap {{ max-height:560px; overflow:auto; border:1px solid {BORDER}; border-radius:14px; }}
/* academy */
.courses {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(270px,1fr)); gap:14px; }}
.course {{ display:block; text-decoration:none !important; color:{TEXT} !important; background:{BOX_BG}; border:1px solid {BORDER}; border-radius:18px; overflow:hidden;
  transition: transform .18s, border-color .18s, box-shadow .18s; border-top:4px solid var(--lv, {ACCENT}); height:100%; }}
.course:hover {{ transform: translateY(-4px); box-shadow: 0 12px 30px rgba(59,139,235,.18); }}
.course .art {{ height:150px; position:relative; overflow:hidden; }} .course .art svg {{ width:100%; height:100%; display:block; }}
.course .body {{ padding:14px 16px 16px; }}
.course .ttl {{ font-weight:600; font-size:1.05rem; line-height:1.4; }}
.course .tag {{ color:{MUTED}; font-size:.85rem; margin-top:6px; line-height:1.6; }}
.course .meta {{ display:flex; gap:6px; margin-top:10px; flex-wrap:wrap; }}
.course .play {{ position:absolute; inset-inline-end:14px; bottom:12px; width:40px; height:40px; border-radius:50%; background:rgba(255,255,255,.95);
  display:flex; align-items:center; justify-content:center; color:{BG}; }}
.course .prog {{ height:6px; background:{BORDER}; border-radius:3px; overflow:hidden; margin-top:10px; }}
.course .prog span {{ display:block; height:100%; background:var(--lv, {ACCENT}); }}
.b-beg {{ background:{POS_BG}; color:{POS_FG}; }} .b-ess {{ background:{YEL_BG}; color:{YEL_FG}; }}
.b-int {{ background:{ORG_BG}; color:{ORG_FG}; }} .b-adv {{ background:{NEG_BG}; color:{NEG_FG}; }}
[class*="st-key-crs_"], [class*="st-key-nxt_"] {{ position:relative; }}
[class*="st-key-crs_"] [data-testid="stElementContainer"], [class*="st-key-nxt_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-crs_"] .stButton, [class*="st-key-nxt_"] .stButton {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; }}
[class*="st-key-crs_"] .stButton button, [class*="st-key-nxt_"] .stButton button {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}
[class*="st-key-crs_"]:hover .course, [class*="st-key-nxt_"]:hover .course {{ transform: translateY(-4px); box-shadow: 0 12px 30px rgba(59,139,235,.18); }}
.dash {{ display:grid; grid-template-columns: 240px 1fr 1fr; gap:14px; }}
.dcard {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:18px; padding:16px 18px; }}
.dcard .dt {{ color:{MUTED}; font-size:.78rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase; margin-bottom:10px; }}
.lvl {{ margin:10px 0; }} .lvl .t {{ display:flex; justify-content:space-between; font-size:.85rem; font-weight:600; }}
.lvl .trk {{ height:10px; border-radius:6px; background:{BORDER}; overflow:hidden; margin-top:6px; }} .lvl .trk span {{ display:block; height:100%; border-radius:6px; }}
.lesson {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:18px; padding:22px 24px; }}
.lesson h3 {{ margin-top:0 !important; }} .lesson p, .lesson li {{ line-height:1.9; font-size:1rem; color:#D7D3DD; }}
.take {{ border-inline-start:3px solid {CYAN}; background:rgba(45,182,235,.07); padding:10px 14px; border-radius:10px; margin-top:12px; }}
.steps {{ display:flex; gap:6px; margin:6px 0 14px; }}
.steps span {{ flex:1; height:6px; border-radius:3px; background:{BORDER}; }} .steps span.on {{ background:linear-gradient(90deg,{ACCENT},{VIOLET}); }}
.gl {{ border-bottom:1px solid {BORDER}; padding:12px 2px; }} .gl b {{ font-size:1rem; }} .gl .d {{ color:#CCC7D3; line-height:1.8; margin-top:4px; }}
.log {{ display:flex; gap:10px; align-items:center; padding:8px 0; border-bottom:1px solid {BORDER}; font-size:.86rem; }}
.foot {{ color:{MUTED}; font-size:.75rem; text-align:center; margin-top:40px; padding-top:14px; border-top:1px solid {BORDER}; }}
/* heatmap (TradingView style) */
.hmwrap {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:16px; padding:8px; overflow:hidden; }}
.hm {{ width:100%; height:auto; display:block; direction:ltr; }}
.hm text {{ font-family:{FONT_LATIN}, {FONT_AR}, sans-serif; pointer-events:none; }}
.hm .tk {{ fill:#fff; font-weight:600; text-anchor:middle; }}
.hm .pc {{ fill:#fff; font-weight:600; text-anchor:middle; opacity:.93; }}
.hm .gh {{ fill:#C9CED8; font-size:12.5px; font-weight:600; }}
.hm .gc {{ font-size:12px; font-weight:600; }}
.hm a:hover .tl {{ stroke:#fff; stroke-width:2; filter:brightness(1.15); }}
.hmlegend {{ display:flex; justify-content:center; gap:3px; margin:8px 0 2px; direction:ltr; flex-wrap:wrap; }}
.hmlegend span {{ min-width:56px; padding:4px 6px; text-align:center; font-size:.74rem; font-weight:600; color:#fff; border-radius:4px; }}
/* trading dashboard (journal style) */
.tdk {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(168px,1fr)); gap:10px; margin-bottom:12px; }}
.tdc {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:14px; padding:12px 14px; display:flex; flex-direction:column; min-height:172px; }}
.tdc .h {{ color:{MUTED}; font-size:.66rem; font-weight:600; letter-spacing:.09em; text-transform:uppercase; }}
.tdc .big {{ font-size:1.45rem; font-weight:600; margin-top:12px; direction:ltr; }}
.tdc svg {{ display:block; margin:6px auto 0; }}
.pbox {{ display:inline-block; padding:3px 10px; border-radius:10px; font-weight:600; direction:ltr; font-variant-numeric:tabular-nums; }}
.pbox.neu {{ background:rgba(157,151,165,.16); color:#CCC7D3; }}
.chip2 {{ display:inline-block; margin-top:8px; padding:2px 9px; border-radius:12px; background:rgba(157,151,165,.16); color:#CCC7D3; font-size:.7rem; font-weight:600; }}
.tdc .foot2 {{ margin-top:auto; padding-top:10px; border-top:1px solid {BORDER}; display:flex; gap:18px; font-size:.66rem; color:{MUTED}; font-weight:600; letter-spacing:.05em; }}
.tdc .foot2 b {{ display:block; font-size:.86rem; letter-spacing:0; margin-top:2px; direction:ltr; }}
.tdc .wl2 {{ display:flex; justify-content:center; gap:8px; font-size:.8rem; font-weight:600; margin-top:2px; direction:ltr; }}
.tdc .goal {{ margin-top:auto; padding-top:8px; }}
.tdc .goal .gt {{ display:flex; justify-content:space-between; font-size:.64rem; color:{MUTED}; font-weight:600; }}
.tdc .goal .gb {{ height:4px; border-radius:3px; background:{BORDER}; margin-top:4px; overflow:hidden; }}
.tdc .goal .gb span {{ display:block; height:100%; background:{CYAN}; border-radius:3px; }}
.tdc .goal.met .gb span {{ background:{UP}; }}
.tdc .split {{ display:flex; height:8px; border-radius:5px; overflow:hidden; gap:3px; margin:12px 0 8px; direction:ltr; }}
.tdc .vals {{ display:flex; justify-content:space-between; gap:6px; font-size:.8rem; font-weight:600; direction:ltr; }}
.tdp {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:16px; padding:14px 16px; margin-bottom:12px; }}
.tdp .tt {{ font-weight:600; font-size:1rem; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; gap:8px; }}
.tdp .tt .muted {{ font-size:.78rem; font-weight:600; }}
.rtab {{ width:100%; border-collapse:collapse; font-size:.84rem; direction:ltr; }}
.rtab th {{ color:{MUTED}; font-size:.66rem; letter-spacing:.08em; text-transform:uppercase; text-align:left; padding:6px 4px; border-bottom:1px solid {BORDER}; }}
.rtab td {{ padding:7px 4px; border-bottom:1px solid rgba(44,39,56,.6); font-weight:600; }}
.rtab td:last-child, .rtab th:last-child {{ text-align:right; }}
.rtab tr:hover td {{ background:rgba(59,139,235,.06); }}
.rtab a {{ color:#fff !important; text-decoration:none !important; }} .rtab a:hover {{ color:#79B8F4 !important; }}
.cal {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)) 124px; gap:6px; direction:ltr; }}
.cal .dh {{ text-align:center; color:{MUTED}; font-size:.72rem; font-weight:600; padding:4px 0; }}
.cal .d {{ position:relative; min-height:80px; border-radius:10px; padding:18px 6px 6px; text-align:center; background:{BOX_BG}; border:1px solid {BORDER}; }}
.cal .d .n {{ position:absolute; top:5px; right:8px; font-size:.66rem; font-weight:600; opacity:.65; }}
.cal .d .p {{ font-weight:600; font-size:1rem; }}
.cal .d .s {{ font-size:.66rem; font-weight:500; opacity:.85; margin-top:2px; }}
.cal .d.pos {{ border-color:{POS_BD}; }} .cal .d.neg {{ border-color:{NEG_BD}; }}
.cal .d.off {{ opacity:.25; }}
.cal .wk {{ border-radius:10px; padding:8px 10px; background:{BOX_BG}; border:1px solid {BORDER}; min-height:80px; }}
.cal .wk .l {{ font-size:.62rem; color:{MUTED}; font-weight:600; letter-spacing:.08em; }}
.cal .wk .p {{ margin-top:6px; }} .cal .wk .s {{ margin-top:6px; font-size:.66rem; color:{MUTED}; font-weight:600; }}
.opos {{ display:flex; flex-direction:column; gap:8px; }}
.opos .o {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:8px; align-items:center; padding:8px 10px; border-radius:12px; background:{BOX_BG}; border:1px solid {BORDER}; direction:ltr; }}
.opos .o .m {{ color:{MUTED}; font-size:.72rem; margin-top:2px; }}
/* financial explorer / misc */
.mx {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:8px; margin:6px 0 10px; }}
.mx .m {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:12px; padding:9px 11px; }}
.mx .m .l {{ color:{MUTED}; font-size:.72rem; font-weight:500; }} .mx .m .v {{ font-weight:600; margin-top:3px; direction:ltr; }}
.mx .m.pos .l, .mx .m.neg .l {{ opacity:.8; color:inherit; }}
.perfrow {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(96px,1fr)); gap:8px; }}
.perfrow .pc2 {{ border-radius:12px; padding:9px 10px; text-align:center; border:1px solid {BORDER}; background:{BOX_BG}; }}
.perfrow .pc2 .l {{ font-size:.72rem; font-weight:600; opacity:.75; }} .perfrow .pc2 .v {{ font-size:1.05rem; font-weight:600; direction:ltr; margin-top:2px; }}
.perfrow .pc2.pos {{ border-color:{POS_BD}; }} .perfrow .pc2.neg {{ border-color:{NEG_BD}; }}
.sigs {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); gap:8px; }}
.sigs .sg {{ display:flex; justify-content:space-between; align-items:center; gap:8px; padding:8px 10px; border-radius:12px; background:{BOX_BG}; border:1px solid {BORDER}; }}
.sigs .sg .n {{ font-weight:600; font-size:.84rem; }} .sigs .sg .v {{ color:{MUTED}; font-size:.74rem; direction:ltr; }}
/* ---------- insight: daily brief ---------- */
.brief {{ position:relative; border-radius:20px; padding:22px 26px 18px; border:1px solid {BORDER}; overflow:hidden; margin-bottom:12px;
  background:{TOP}, radial-gradient(700px 260px at 0% 0%, rgba(59,139,235,.22), transparent 60%), radial-gradient(600px 240px at 100% 0%, rgba(123,69,240,.18), transparent 60%),
  linear-gradient(180deg, {CARD2}, {CARD}); }}
.brief .eyebrow {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; color:{CYAN}; font-weight:600; letter-spacing:.14em; font-size:.72rem; text-transform:uppercase; }}
.brief .hl {{ font-size:1.9rem; font-weight:300; margin:10px 0 8px; line-height:1.3; color:#fff; letter-spacing:-.01em; }}
.brief ul {{ margin:8px 0 0; padding-inline-start:20px; }} .brief li {{ margin:4px 0; line-height:1.75; color:#D7D3DD; }}
.brief .eyebrow .status {{ text-transform:none; letter-spacing:0; font-size:.74rem; padding:4px 10px; }}
.brief .mood {{ display:inline-flex; align-items:center; gap:6px; padding:4px 11px; border-radius:20px; font-weight:600; font-size:.78rem; letter-spacing:0; text-transform:none; }}
.bstory {{ display:flex; gap:12px; align-items:flex-start; padding:10px 4px; border-bottom:1px solid {BORDER}; }}
.bstory:last-child {{ border-bottom:none; }}
.bstory .nth {{ width:112px; height:76px; border-radius:11px; }}
.bstory .nth.fb .ms {{ font-size:32px; }} .bstory .nth.fb em {{ display:none; }}
.bstory .m {{ display:flex; align-items:center; flex-wrap:wrap; gap:6px; }}
.bstory .m .sc {{ width:auto; height:auto; flex-direction:row; gap:1px; padding:1px 7px; border-radius:999px; font-size:.72rem; }}
.bstory .m .sc small {{ margin-top:0; }}
@media (max-width: 640px) {{ .bstory .nth {{ width:92px; height:64px; }} }}
.bstory .sc {{ flex:none; width:46px; height:46px; border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center;
  font-weight:600; font-size:1.08rem; line-height:1; border:1px solid; direction:ltr; }}
.bstory .sc small {{ font-size:.55rem; font-weight:600; opacity:.75; margin-top:3px; }}
.bstory .b {{ min-width:0; flex:1; }}
.bstory a {{ color:#E7E3EB !important; text-decoration:none !important; font-weight:600; line-height:1.55; }} .bstory a:hover {{ color:#79B8F4 !important; }}
.bstory .m {{ color:{MUTED}; font-size:.74rem; margin-top:3px; }}
.bstory .kw {{ margin-top:6px; }} .bstory .kwc {{ font-size:.68rem; padding:2px 8px 2px 6px; }}
.iqs {{ display:inline-block; padding:3px 10px; border-radius:10px; font-size:.74rem; font-weight:600; border:1px solid; }}
.evt {{ display:grid; grid-template-columns: 96px minmax(0,1fr) auto; gap:12px; align-items:center; padding:9px 10px; border-radius:12px; background:{BOX_BG};
  border:1px solid {BORDER}; margin-bottom:6px; }}
.evt .d {{ text-align:center; border-radius:10px; padding:5px 4px; background:rgba(59,139,235,.12); color:#BFDDF8; font-weight:600; font-size:.72rem; line-height:1.4; direction:ltr; }}
.evt .n {{ font-weight:600; }} .evt .x {{ color:{MUTED}; font-size:.74rem; direction:ltr; white-space:nowrap; }}
.evt.key {{ border-color: rgba(245,185,74,.45); }} .evt.key .d {{ background:{YEL_BG}; color:{YEL_FG}; }}
/* ---------- insight: articles ---------- */
.acard {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:18px; overflow:hidden; height:100%; transition: transform .18s, box-shadow .18s, border-color .18s; }}
.acard .aart {{ position:relative; height:176px; overflow:hidden; }} .acard .aart svg {{ width:100%; height:100%; display:block; }}
.acard .aicon {{ position:absolute; left:50%; top:46%; transform:translate(-50%,-50%); width:66px; height:66px; border-radius:50%; display:flex; align-items:center;
  justify-content:center; background:rgba(255,255,255,.16); border:1.5px solid rgba(255,255,255,.45); }}
.acard .aicon .ms {{ font-size:2rem; color:#fff; }}
.acard .abody {{ padding:14px 16px 16px; }}
.acat {{ font-size:.66rem; font-weight:600; letter-spacing:.1em; text-transform:uppercase; color:#93C5FD; }}
.acard .attl {{ font-weight:600; font-size:1.05rem; line-height:1.45; margin-top:6px; color:#fff; }}
.acard .adek {{ color:{MUTED}; font-size:.84rem; line-height:1.6; margin-top:6px; }}
.acard .ameta {{ display:flex; gap:6px; margin-top:10px; flex-wrap:wrap; }}
.acard.feat {{ display:grid; grid-template-columns: minmax(0,1.05fr) minmax(0,1fr); }}
.acard.feat .aart {{ height:100%; min-height:260px; }} .acard.feat .aicon {{ width:92px; height:92px; }} .acard.feat .aicon .ms {{ font-size:2.8rem; }}
.acard.feat .attl {{ font-size:1.6rem; line-height:1.3; }} .acard.feat .adek {{ font-size:.98rem; }}
.acard.feat .abody {{ padding:26px 28px; display:flex; flex-direction:column; justify-content:center; }}
[class*="st-key-art_"] {{ position:relative; height:100%; }}
[class*="st-key-art_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-art_"] .stButton {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; }}
[class*="st-key-art_"] .stButton button {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}
[class*="st-key-art_"]:hover .acard {{ transform: translateY(-4px); box-shadow: 0 14px 32px rgba(59,139,235,.18); border-color: rgba(90,160,240,.5); }}
.article .at {{ font-size:2.4rem; font-weight:300; line-height:1.2; margin:10px 0 8px; color:#fff; letter-spacing:-.03em; }}
.article .dek {{ color:#CAC5D1; font-size:1.1rem; line-height:1.75; }}
.article .ah {{ font-size:1.3rem; font-weight:600; margin:26px 0 6px; color:#fff; }}
.article p, .article li {{ line-height:1.95; color:#D7D3DD; font-size:1.02rem; }}
.article ul {{ padding-inline-start:22px; margin:6px 0; }} .article li {{ margin:5px 0; }}
.acover {{ position:relative; aspect-ratio:16/6; max-height:360px; border-radius:18px; overflow:hidden; margin:6px 0 4px; }} .acover svg {{ width:100%; height:100%; display:block; }}
.tkw {{ background: linear-gradient(135deg, rgba(45,182,235,.1), rgba(59,139,235,.08)); border:1px solid rgba(45,182,235,.28); border-radius:16px; padding:14px 18px; margin:16px 0 8px; }}
.tkw .h {{ font-weight:600; font-size:.78rem; letter-spacing:.1em; text-transform:uppercase; color:{CYAN}; margin-bottom:4px; display:flex; gap:6px; align-items:center; }}
.tkw .t {{ display:flex; gap:10px; align-items:flex-start; margin:6px 0; line-height:1.75; color:#E2E8F0; }} .tkw .t .ms {{ color:#4ADE80; margin-top:4px; }}
.anote {{ border-inline-start:3px solid {ACCENT}; background:rgba(59,139,235,.08); padding:12px 16px; border-radius:12px; margin:16px 0; display:flex; gap:10px; line-height:1.8; }}
.anote .ms {{ color:#79B8F4; margin-top:3px; }}
.acap {{ color:{MUTED}; font-size:.8rem; margin:2px 0 4px; display:flex; gap:6px; align-items:center; }}
.acap .ms {{ color:{CYAN}; }}
/* ---------- insight: fear & greed ---------- */
.fgcmp {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; margin-top:10px; }}
.fgcmp .c {{ border-radius:12px; padding:9px 8px; text-align:center; border:1px solid transparent; }}
.fgcmp .c .l {{ font-size:.66rem; font-weight:600; opacity:.8; }} .fgcmp .c .v {{ font-size:1.3rem; font-weight:600; margin-top:2px; direction:ltr; }}
.fgcmp .c .s {{ font-size:.64rem; font-weight:600; }}
.fgc {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:16px; padding:13px 14px; height:100%; }}
.fgc .h {{ display:flex; justify-content:space-between; gap:8px; align-items:flex-start; }}
.fgc .h b {{ font-size:.92rem; }} .fgc .x {{ color:{MUTED}; font-size:.78rem; line-height:1.65; margin-top:8px; }}
.fgc .r {{ font-size:.78rem; margin-top:8px; font-weight:600; color:#CCC7D3; }}
.fgbar {{ position:relative; height:8px; border-radius:5px; margin-top:12px; background: linear-gradient(90deg, #EF4444, #F97316 30%, #94A3B8 50%, #84CC16 70%, #22C55E); direction:ltr; }}
.fgbar i {{ position:absolute; top:-4px; width:16px; height:16px; border-radius:50%; background:#fff; border:3px solid {BG}; transform:translateX(-50%); box-shadow:0 2px 6px rgba(0,0,0,.5); }}
/* ---------- top navigation: lives in the site's top line (Streamlit header row), hover menus ---------- */
.st-key-topnav {{ container-type: inline-size; container-name: topnav; overflow: visible !important; gap: 10px !important; }}
.st-key-topnav, .st-key-topnav div, .st-key-navleft, .st-key-navright {{ overflow: visible !important; }}
/* Streamlit pulls every markdown block up by 1rem (it expects a paragraph margin under it) and every page link by .25rem.
   Inside the bar and its menus that squeezed buttons and made menu items overlap, so both are cancelled here. */
.st-key-topnav [data-testid="stMarkdownContainer"] {{ margin-bottom: 0 !important; }}
.st-key-topnav [data-testid="stElementContainer"]:has(> .stPageLink), .st-key-topnav .stElementContainer:has(> .stPageLink) {{ margin: 0 !important; }}
.st-key-topnav [data-testid="stMarkdownContainer"] p {{ margin: 0 !important; }}
.st-key-navleft {{ flex-wrap: nowrap !important; gap: 2px !important; }}
.st-key-navright {{ flex-wrap: nowrap !important; gap: 8px !important; }}
[data-testid="stLayoutWrapper"]:has(> .st-key-navsearch), .st-key-topnav > .st-key-navsearch {{ flex: 0 1 520px !important; min-width: 180px !important;
  margin-inline-start: auto; }}
[class*="st-key-navsec_"] {{ position: relative; gap: 0 !important; }}
.navbtn {{ display:flex; align-items:center; gap:7px; height:38px; box-sizing:border-box; padding:0 12px; border-radius:11px; font-weight:600; font-size:.9rem;
  line-height:1; color:#CCC7D5; cursor:pointer; white-space:nowrap; border:1px solid transparent; transition: background .18s, color .18s, border-color .18s;
  user-select:none; outline:none; }}
.navbtn .ms {{ font-size:1.14rem; color:#A39CB4; transition: color .18s; }}
.navbtn .chev {{ font-size:1rem; opacity:.75; transition: transform .22s ease; }}
.navbtn:focus-visible {{ box-shadow: 0 0 0 2px rgba(90,160,240,.7); }}
[class*="st-key-navsec_"]:hover .navbtn {{ color:#fff; background: linear-gradient(135deg, rgba(59,139,235,.24), rgba(123,69,240,.2)); border-color: rgba(90,160,240,.45); }}
[class*="st-key-navsec_"]:hover .navbtn .ms {{ color:#fff; }}
[class*="st-key-navsec_"]:hover .chev {{ transform: rotate(180deg); }}
.navbtn.on {{ color:#fff; background: rgba(59,139,235,.14); border-color: rgba(59,139,235,.34); }}
.navbtn.on .ms {{ color:#79B8F4; }}
/* menus: open on hover (mouse) or keyboard focus only - a clicked menu never stays open over the next one */
[class*="st-key-navdd_"], .st-key-langdd {{ position:absolute !important; top: calc(100% + 8px); left:0; width: 264px !important; min-width: 264px !important;
  max-width: none !important; z-index: 1000; gap: 2px !important; box-sizing: border-box;
  padding: 10px 8px 8px; background: rgba(26,22,36,.985); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
  border: 1px solid #3E3A46; border-radius: 16px; box-shadow: 0 24px 50px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.02) inset;
  opacity: 0; visibility: hidden; transform: translateY(6px); transform-origin: top left; pointer-events: none;
  transition: opacity .1s ease, transform .1s ease, visibility 0s linear .1s; }}
[class*="st-key-navdd_"]::before, .st-key-langdd::before {{ content:""; position:absolute; left:0; right:0; top:-12px; height:12px; }}
[class*="st-key-navsec_"]:hover [class*="st-key-navdd_"], [class*="st-key-navsec_"]:has(:focus-visible) [class*="st-key-navdd_"],
.st-key-langsec:hover .st-key-langdd, .st-key-langsec:has(:focus-visible) .st-key-langdd {{ opacity: 1; visibility: visible; transform: none; pointer-events: auto;
  transition: opacity .16s ease, transform .18s ease, visibility 0s; }}
/* while one menu is hovered, every other menu closes at once (no two menus on top of each other) */
.st-key-topnav:has([class*="st-key-navsec_"]:hover) [class*="st-key-navsec_"]:not(:hover) [class*="st-key-navdd_"],
.st-key-topnav:has([class*="st-key-navsec_"]:hover) .st-key-langdd, .st-key-topnav:has(.st-key-langsec:hover) [class*="st-key-navdd_"] {{
  opacity: 0 !important; visibility: hidden !important; transition: none !important; pointer-events: none !important; }}
[class*="st-key-navsec_"]:hover, .st-key-langsec:hover {{ z-index: 5; }}
@media (hover: none) {{  /* touch screens: a tap opens the menu */
  [class*="st-key-navsec_"]:focus-within [class*="st-key-navdd_"], .st-key-langsec:focus-within .st-key-langdd {{ opacity: 1; visibility: visible; transform: none;
    pointer-events: auto; }} }}
/* a link/option was just chosen in a menu (FX_JS sets the flag on <html>): the menu closes at once, whatever hover or focus says,
   and opens again when a menu button is pressed or hovered */
/* held shut by an animation, not for good: if the flag is ever left behind (the script that clears it was stopped), the menus open
   again on hover after 2.5 seconds */
@keyframes navhold {{ from, to {{ opacity:0; visibility:hidden; pointer-events:none; }} }}
html[data-menu-closed] [class*="st-key-navdd_"], html[data-menu-closed] .st-key-langdd {{ animation: navhold 2.5s steps(1, end) 1; transition: none; }}
.navhd {{ font-size:.64rem; letter-spacing:.14em; text-transform:uppercase; color:{MUTED}; font-weight:600; padding: 0 10px 7px; line-height:1.2;
  border-bottom: 1px solid {BORDER}; margin-bottom: 4px; }}
[class*="st-key-navdd_"] [data-testid="stPageLink"] a {{ border-radius: 11px; padding: 8px 10px; margin: 0; min-height: 38px; box-sizing: border-box;
  transition: background .14s, transform .14s; }}
[class*="st-key-navdd_"] [data-testid="stPageLink"] a:hover {{ background: rgba(59,139,235,.16); transform: translateX(2px); }}
[class*="st-key-navdd_"] [data-testid="stPageLink"] a span {{ font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
[class*="st-key-navon_"] [data-testid="stPageLink"] a {{ background: linear-gradient(90deg, rgba(59,139,235,.3), rgba(123,69,240,.16)) !important;
  box-shadow: inset 3px 0 0 {ACCENT}; }}
[class*="st-key-navon_"] {{ gap: 0 !important; }}
.st-key-navright .status {{ display:inline-flex; align-items:center; height:38px; box-sizing:border-box; padding: 0 12px; font-size: .76rem; white-space: nowrap;
  background: rgba(26,22,36,.75); }}
/* search: wide type-ahead box, same height as the buttons */
.st-key-navsearch [data-testid="stSelectbox"], .st-key-navsearch [data-testid="stTextInput"] {{ position: relative; }}
.st-key-navsearch [data-testid="stSelectbox"]::before, .st-key-navsearch [data-testid="stTextInput"]::before {{ content: "search";
  font-family: 'Material Symbols Rounded'; position: absolute; inset-inline-start: 12px; top: 50%; transform: translateY(-50%); z-index: 3;
  font-size: 1.2rem; line-height: 1; color: #9D97A5; pointer-events: none; }}
.st-key-navsearch input {{ padding-inline-start: 38px !important; font-size: .88rem !important; }}
.st-key-navsearch [role="group"], .st-key-navsearch [data-baseweb="select"] > div, .st-key-navsearch [data-baseweb="input"] {{ height: 38px !important;
  min-height: 38px !important; box-sizing: border-box; border-radius: 12px !important; background: rgba(34,29,47,.92) !important; border-color: #3E3A46 !important;
  transition: border-color .15s, box-shadow .15s; }}
.st-key-navsearch [role="group"]:hover, .st-key-navsearch [data-baseweb="select"] > div:hover, .st-key-navsearch [data-baseweb="input"]:hover {{ border-color: rgba(90,160,240,.55) !important; }}
.st-key-navsearch [role="group"][data-focus-within], .st-key-navsearch [data-baseweb="select"]:focus-within > div, .st-key-navsearch [data-baseweb="input"]:focus-within {{
  border-color: {ACCENT} !important; box-shadow: 0 0 0 3px rgba(59,139,235,.22); }}
.st-key-navsearch button[aria-label="Open"] {{ display: none !important; }}
.st-key-navsearch input::placeholder {{ color: #9D97A5 !important; }}
/* language menu: flags */
.flag {{ display:inline-block; flex:none; width:24px; height:18px; border-radius:4px; background-size:cover; background-position:center;
  box-shadow: 0 0 0 1px rgba(255,255,255,.22), 0 2px 6px rgba(0,0,0,.35); }}
.flag.us {{ background-image:url("{FLAG_US}"); }}
.flag.sa {{ background-image:url("{FLAG_SA}"); }}
/* language button: EN / ع (the flags belong to the market switch) */
.langbtn .lic {{ font-size:1.05rem; color:#A39CB4; }}
.langbtn .lcode, .lopt .lcode {{ font-weight:800; font-size:.86rem; color:#fff; min-width:18px; text-align:center; letter-spacing:.02em; }}
.lopt .lcode {{ display:inline-flex; align-items:center; justify-content:center; width:30px; height:22px; border-radius:6px; background:rgba(255,255,255,.08);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.14); font-size:.8rem; }}
/* market switch: two flags in one pill (the chosen market lit) */
.st-key-mktsw {{ flex-wrap:nowrap !important; gap:2px !important; height:38px; box-sizing:border-box; padding:3px !important; border-radius:11px;
  border:1px solid #3E3A46; background: rgba(34,29,47,.9); }}
.st-key-mktsw [data-testid="stElementContainer"], .st-key-mktsw .stElementContainer {{ width:auto !important; margin:0 !important; }}
[class*="st-key-mkt_"] {{ gap:0 !important; }}
[class*="st-key-mkt_"] button {{ min-height:30px !important; height:30px; padding:0 10px 0 8px !important; border-radius:8px !important; border:1px solid transparent !important;
  background:transparent !important; box-shadow:none !important; gap:7px; transition: background .15s, border-color .15s; }}
[class*="st-key-mkt_"] button::before {{ content:""; width:21px; height:15px; border-radius:3px; flex:none; background-size:cover; background-position:center;
  box-shadow: 0 0 0 1px rgba(255,255,255,.22); filter: saturate(.55) brightness(.8); transition: filter .15s; }}
.st-key-mkt_us button::before, .st-key-mkt_us_on button::before {{ background-image:url("{FLAG_US}"); }}
.st-key-mkt_sa button::before, .st-key-mkt_sa_on button::before {{ background-image:url("{FLAG_SA}"); }}
[class*="st-key-mkt_"] button p {{ font-size:.8rem !important; font-weight:600 !important; color:#A39CB4 !important; white-space:nowrap; }}
[class*="st-key-mkt_"] button:hover {{ background: rgba(59,139,235,.14) !important; }}
[class*="st-key-mkt_"] button:hover::before {{ filter:none; }}
[class*="st-key-mkt_"][class*="_on"] button {{ background: linear-gradient(135deg, rgba(59,139,235,.32), rgba(123,69,240,.26)) !important;
  border-color: rgba(90,160,240,.5) !important; }}
[class*="st-key-mkt_"][class*="_on"] button::before {{ filter:none; }}
[class*="st-key-mkt_"][class*="_on"] button p {{ color:#fff !important; }}
.st-key-langsec {{ position: relative; gap: 0 !important; }}
.langbtn {{ display:flex; align-items:center; gap:7px; height:38px; box-sizing:border-box; padding:0 8px 0 10px; border-radius:11px; border:1px solid #3E3A46;
  background: rgba(34,29,47,.9); color:#E7E3EB; cursor:pointer; white-space:nowrap; user-select:none; outline:none; line-height:1;
  transition: border-color .18s, background .18s; }}
.langbtn .flag {{ width:26px; height:19px; }}
.langbtn .chev {{ font-size:1rem; color:{MUTED}; transition: transform .2s ease; }}
.langbtn:focus-visible {{ box-shadow: 0 0 0 2px rgba(90,160,240,.7); }}
.st-key-langsec:hover .langbtn {{ border-color: rgba(90,160,240,.55); background: linear-gradient(135deg, rgba(59,139,235,.22), rgba(123,69,240,.18)); }}
.st-key-langsec:hover .langbtn .chev {{ transform: rotate(180deg); }}
.st-key-langdd {{ left: auto; right: 0; width: 236px !important; min-width: 236px !important; transform-origin: top right; }}
.lopt {{ display:flex; flex-wrap:nowrap; align-items:center; gap:12px; height:46px; box-sizing:border-box; padding:0 12px; border-radius:12px;
  transition: background .14s; white-space:nowrap; }}
.lopt .flag {{ width:30px; height:22px; border-radius:5px; }}
.lopt .nm {{ display:flex; align-items:baseline; gap:8px; min-width:0; line-height:1.2; }}
.lopt .nm b {{ font-size:.95rem; color:#fff; font-weight:600; }}
.lopt .nm small {{ color:{MUTED}; font-size:.74rem; font-weight:600; }}
.lopt .ck {{ margin-inline-start:auto; color:#4ADE80; font-size:1.2rem; }}
.lopt.on {{ background: rgba(59,139,235,.16); box-shadow: inset 0 0 0 1px rgba(59,139,235,.35); }}
[class*="st-key-langopt_"] {{ position:relative; gap:0 !important; }}
[class*="st-key-langopt_"] [data-testid="stElementContainer"] {{ position:static !important; margin:0 !important; }}
[class*="st-key-langopt_"] .stButton {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; }}
[class*="st-key-langopt_"] .stButton button {{ width:100% !important; height:100% !important; min-height:0 !important; opacity:0; cursor:pointer; }}
[class*="st-key-langopt_"]:hover .lopt:not(.on) {{ background: rgba(59,139,235,.1); }}
/* narrower screens: the bar compacts itself step by step instead of wrapping (8 menus + search + status + language) */
@container topnav (max-width: 1760px) {{ .navbtn .chev {{ display:none; }} }}
@container topnav (max-width: 1560px) {{ .st-key-navright .status .muted {{ display:none; }} .navbtn {{ padding:0 10px; gap:6px; }} }}
@container topnav (max-width: 1400px) {{ .navbtn {{ padding:0 8px; gap:5px; font-size:.85rem; }} .navbtn .ms {{ font-size:1.05rem; }}
  .st-key-navright .status b {{ display:none; }} .st-key-navright .status {{ padding: 0 12px; }} }}
@container topnav (max-width: 1030px) {{ .navbtn > span:not(.ms) {{ display:none; }} .navbtn {{ padding:0 10px; }} .navbtn .ms {{ font-size:1.18rem; }} }}
@container topnav (max-width: 760px) {{ .st-key-navright .status {{ display:none; }} .langbtn .chev {{ display:none; }} }}
@container topnav (max-width: 1250px) {{ [class*="st-key-mkt_"] button p {{ position:absolute !important; width:1px; height:1px; overflow:hidden;
  clip:rect(0 0 0 0); clip-path:inset(50%); white-space:nowrap; margin:0 !important; }} [class*="st-key-mkt_"] button {{ padding:0 7px !important; }} }}
/* (the flag alone on a narrow bar: the name stays for screen readers, only out of sight) */
@container topnav (max-width: 600px) {{ .navbtn {{ padding:0 8px; }} }}      /* eight menus (Portfolio added) keep to one row on phones */
@container topnav (max-width: 440px) {{ .navbtn {{ padding:0 6px; }} .langbtn {{ padding:0 6px; }} }}
@container topnav (max-width: 350px) {{ .navbtn {{ padding:0 4px; }} .navbtn .ms {{ font-size:1.05rem; }} .langbtn {{ padding:0 4px; }} }}
/* desktop: the bar IS the site's top line. It is anchored to the main area's own box (the same box as Streamlit's header),
   so it spans from the sidebar edge to the menu button, follows the sidebar when it is opened/closed/resized and never scrolls away. */
@media (min-width: 1024px) {{
  [data-testid="stMainBlockContainer"]:has(.st-key-topnav) {{ padding-top: 3.75rem !important; }}
  [data-testid="stLayoutWrapper"]:has(> .st-key-topnav) {{ position: static !important; height: 0; min-height: 0; overflow: visible; }}
  .st-key-topnav {{ position: absolute !important; top: 0; left: 1.25rem; right: 4.25rem; width: auto !important; max-width: none !important;
    height: 3.75rem; min-height: 3.75rem; z-index: 999990; flex-wrap: nowrap !important; align-items: center !important; }}
  .stApp:has([data-testid="stExpandSidebarButton"]) .st-key-topnav {{ left: 6.6rem; }}
}}
@container topnav (min-width: 1900px) {{ [data-testid="stLayoutWrapper"]:has(> .st-key-navsearch), .st-key-topnav > .st-key-navsearch {{ flex-basis: 600px !important; }} }}
/* tablets and phones: a card under the top line, menus open full width */
@media (max-width: 1023.98px) {{
  .st-key-topnav {{ position: relative; z-index: 60; flex-wrap: wrap !important; padding: 6px 8px; margin-bottom: 6px; background: rgba(18,13,30,.86);
    border: 1px solid {BORDER}; border-radius: 16px; }}
  .st-key-navleft {{ flex-wrap: wrap !important; }}
  [data-testid="stLayoutWrapper"]:has(> .st-key-navsearch), .st-key-topnav > .st-key-navsearch {{ flex: 1 1 100% !important; order: 3; margin: 0 !important; }}
  [class*="st-key-navsec_"] {{ position: static; }}
  [class*="st-key-navdd_"] {{ left: 8px !important; right: 8px !important; width: auto !important; min-width: 0 !important; top: calc(100% + 4px); }}
  /* the card sits right under the top line and stays there while the page scrolls (Streamlit wraps it in a layout wrapper:
     the wrapper is what sticks; the landing keeps its own layout) */
  .stApp:not(:has(.ixp)) [data-testid="stMainBlockContainer"]:has(.st-key-topnav) {{ padding-top: calc(3.75rem + 6px) !important; }}
  .stApp:not(:has(.ixp)) [data-testid="stLayoutWrapper"]:has(> .st-key-topnav),
  .stApp:not(:has(.ixp)) [data-testid="stVerticalBlock"] > .st-key-topnav {{ position: sticky !important; top: calc(3.75rem + 6px); z-index: 90; }}
  .stApp:not(:has(.ixp)) .st-key-topnav {{ margin-top: 0 !important; background: rgba(18,13,30,.9);
    backdrop-filter: blur(16px) saturate(140%); -webkit-backdrop-filter: blur(16px) saturate(140%);
    box-shadow: 0 10px 28px -12px rgba(0,0,0,.7); }}
}}
/* ---------- sidebar: market pulse + watchlist ---------- */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: .45rem; }}
.pulse {{ background:{TOP}, linear-gradient(160deg, rgba(59,139,235,.16), rgba(123,69,240,.08) 55%, {CARD}); border:1px solid {BORDER};
  border-radius:14px; padding:10px 12px; margin-bottom:6px; }}
.pulse .ph {{ display:flex; align-items:center; gap:6px; font-size:.7rem; font-weight:600; letter-spacing:.09em; text-transform:uppercase;
  color:#CCC7D3; margin-bottom:4px; }}
.pulse .ph .ms {{ color:#79B8F4; }}
/* market pulse: the title on its own line, the market status under it across the whole width */
.pulse .ph {{ flex-wrap:wrap; row-gap:8px; }}
.pulse .ph .status.mini {{ flex:1 0 100%; box-sizing:border-box; justify-content:flex-start; gap:7px; padding:5px 10px; border-radius:10px;
  white-space:nowrap; text-transform:none; letter-spacing:0; font-size:.74rem; font-weight:600; overflow:hidden; }}
.pulse .ph .status.mini b {{ font-weight:600; }} .pulse .ph .status.mini .muted {{ margin-inline-start:auto; }}
.brand {{ display:inline-block; vertical-align:-.08em; overflow:visible; }}
.pr {{ display:grid; grid-template-columns: minmax(0,1fr) 58px auto; gap:8px; align-items:center; padding:5px 0;
  border-bottom:1px dashed rgba(157,151,165,.16); direction:ltr; }}
.pr:last-child {{ border-bottom:none; }}
.pr .n {{ font-size:.78rem; font-weight:600; color:#fff; }} .pr .v {{ font-size:.7rem; color:{MUTED}; font-variant-numeric: tabular-nums; }}
.pr .pill {{ min-width:0; padding:2px 6px; font-size:.68rem; }}
.wlh {{ display:flex; align-items:center; justify-content:space-between; margin: 8px 0 6px; direction:ltr; }}
.wlh .t {{ font-size:.7rem; font-weight:600; letter-spacing:.1em; color:#BBB5C3; text-transform:uppercase; display:flex; gap:6px; align-items:center; }}
.wlh .t .ms {{ color:#fff; background:{PANEL}; box-shadow:{GLOW}; border-radius:7px; padding:3px; font-size:.95rem; }}
.wlr {{ display:grid; grid-template-columns: minmax(0,1fr) 56px auto; gap:8px; align-items:center; padding:8px 10px; border-radius:12px;
  background:{BOX_BG}; border:1px solid {BORDER}; direction:ltr;
  transition: transform .15s, border-color .15s, box-shadow .15s; }}
.wlr .l {{ display:flex; align-items:center; gap:8px; min-width:0; }}
.wlr .nm {{ min-width:0; }} .wlr .nm b {{ display:block; font-size:.84rem; color:#fff; }}
.wlr .nm span {{ display:block; font-size:.64rem; color:{MUTED}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.wlr .r {{ text-align:right; }} .wlr .r .p {{ font-size:.8rem; font-weight:600; font-variant-numeric: tabular-nums; }}
.wlr .r .pill {{ min-width:0; padding:1px 6px; font-size:.66rem; margin-top:2px; }}
[class*="st-key-wlr_"] {{ position:relative; }}
[class*="st-key-wlr_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-wlr_"] .stButton {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; }}
[class*="st-key-wlr_"] .stButton button {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}
[class*="st-key-wlr_"]:hover .wlr {{ border-color: rgba(90,160,240,.6); transform: translateX(3px); box-shadow: 0 8px 18px rgba(0,0,0,.35); }}
@media (max-width: 600px) {{ .iqleg .sc span {{ width:22px; height:22px; font-size:.66rem; }} .iq {{ width:74px; }} }}
@media (max-width: 900px) {{ .acard.feat {{ grid-template-columns: 1fr; }} .fgcmp {{ grid-template-columns: repeat(2,minmax(0,1fr)); }} .dash {{ grid-template-columns: 1fr; }} .cal {{ grid-template-columns:repeat(5,minmax(0,1fr)); }} .cal .wk, .cal .wkh {{ display:none; }} }}
/* ---------- calendar pages ---------- */
.wklbl {{ display:flex; align-items:center; gap:8px; font-size:1rem; color:#fff; flex-wrap:wrap; }}
.wklbl .ms {{ color:#79B8F4; }}
.wklbl .tag, .ehub .hd .now, .evday .dh .now {{ font-size:.66rem; font-weight:600; padding:3px 9px; border-radius:20px; background:{ACCENT}; color:#fff; letter-spacing:.02em; }}
.lgo {{ position:relative; display:inline-block; flex:none; border-radius:11px; overflow:hidden; background:#fff; box-shadow:0 0 0 1px rgba(255,255,255,.1); }}
.lgo object {{ position:absolute; inset:0; width:100%; height:100%; border:0; pointer-events:none; }}
.lgo .ini {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:600; letter-spacing:-.02em; }}
.ehub {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:10px; margin:12px 0 6px; }}
.ehub .day {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:16px; padding:10px 10px 12px; min-width:0;
  display:flex; flex-direction:column; gap:12px; }}
.ehub .day.today {{ border-color:rgba(59,139,235,.65); box-shadow:0 0 0 1px rgba(59,139,235,.3), 0 14px 32px rgba(59,139,235,.14); }}
.ehub .day.past {{ background:{BOX_BG}; border:1px solid {BORDER}; }}
.ehub .hd {{ display:flex; align-items:baseline; gap:6px; padding:2px 4px 9px; border-bottom:1px solid {BORDER}; flex-wrap:wrap; }}
.ehub .hd .dw {{ font-size:.72rem; font-weight:600; letter-spacing:.12em; color:{MUTED}; }}
.ehub .hd .dn {{ font-size:1.55rem; font-weight:600; color:#fff; line-height:1; }}
.ehub .hd .mo {{ font-size:.74rem; color:{MUTED}; font-weight:600; }}
.ehub .hd .cnt {{ margin-inline-start:auto; font-size:.72rem; font-weight:600; color:#BFDDF8; background:rgba(59,139,235,.14); border-radius:10px; padding:2px 8px; }}
.ehub .grp .gh {{ display:flex; align-items:center; gap:6px; font-size:.75rem; font-weight:600; color:#CCC7D5; margin-bottom:8px; }}
.ehub .grp .gh .ms {{ font-size:1.05rem; }}
.ehub .grp.bmo .gh .ms {{ color:{GOLD}; }} .ehub .grp.amc .gh .ms {{ color:{PURPLE}; }} .ehub .grp.tns .gh .ms {{ color:{MUTED}; }} .ehub .grp.ipo .gh .ms {{ color:{CYAN}; }}
.ehub .grp .gh b {{ margin-inline-start:auto; font-size:.7rem; color:{MUTED}; }}
.ehub .tl {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(50px,1fr)); gap:8px 4px; }}
.et {{ position:relative; display:flex; flex-direction:column; align-items:center; gap:5px; text-decoration:none !important; padding:4px 1px; border-radius:10px;
  transition:background .15s, transform .15s; min-width:0; }}
.et:hover {{ background:rgba(59,139,235,.13); transform:translateY(-2px); }}
.et .tk {{ font-size:.66rem; font-weight:600; color:#DEDAE3; max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.rs {{ display:inline-block; width:10px; height:10px; border-radius:50%; }} .rs.b {{ background:#22C55E; }} .rs.m {{ background:#EF4444; }}
.et .rs {{ position:absolute; top:0; inset-inline-end:4px; border:2px solid {CARD2}; }}
.ehub details summary {{ cursor:pointer; font-size:.74rem; font-weight:600; color:#79B8F4; margin-top:8px; list-style:none; }}
.ehub details summary::-webkit-details-marker {{ display:none; }}
.ehub details[open] summary {{ margin-bottom:8px; }}
.ehub .ipr {{ display:flex; align-items:center; gap:6px; font-size:.74rem; padding:5px 7px; border-radius:9px; background:rgba(45,182,235,.08); margin-top:4px; min-width:0; }}
.ehub .ipr .ms {{ color:{CYAN}; font-size:1rem; }} .ehub .ipr b {{ color:#fff; }}
.ehub .ipr span {{ color:{MUTED}; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; min-width:0; flex:1; }}
.ehub .ipr em {{ font-style:normal; color:#BFDDF8; font-weight:600; direction:ltr; white-space:nowrap; }}
.ehub .none {{ color:{MUTED}; font-size:.8rem; text-align:center; padding:18px 4px; }}
.hnote {{ display:inline-flex; align-items:center; gap:6px; font-size:.72rem; font-weight:600; padding:6px 9px; border-radius:10px; }}
.hnote .ms {{ font-size:1rem; }}
.hnote.closed {{ background:{NEG_BG}; color:{NEG_FG}; }} .hnote.early {{ background:{YEL_BG}; color:{YEL_FG}; }}
.elegend {{ display:flex; flex-wrap:wrap; gap:8px 18px; color:{MUTED}; font-size:.76rem; margin:8px 2px 14px; }}
.elegend span {{ display:inline-flex; align-items:center; gap:6px; }}
.elegend .ms {{ font-size:1rem; color:{GOLD}; }} .elegend span:nth-child(2) .ms {{ color:{PURPLE}; }}
.ehit {{ display:flex; flex-wrap:wrap; gap:8px; margin:2px 0 10px; }}
.ehit .chip {{ display:inline-flex; align-items:center; gap:8px; padding:5px 12px 5px 5px; border-radius:14px; background:{CARD2}; border:1px solid rgba(59,139,235,.45);
  text-decoration:none !important; color:#E7E3EB !important; font-size:.84rem; }}
.ehit .chip span {{ color:{MUTED}; }}
.etab {{ border:1px solid {BORDER}; border-radius:16px; overflow:hidden; background:{BOX_BG}; margin:6px 0 10px; }}
.erow {{ display:grid; grid-template-columns:minmax(0,2.3fr) 1.35fr .8fr .85fr .75fr .9fr .95fr; gap:10px; align-items:center; padding:8px 14px;
  border-top:1px solid {BORDER}; font-size:.86rem; }}
.erow.eh {{ border-top:none; background:{CARD2}; font-size:.66rem; font-weight:600; letter-spacing:.07em; text-transform:uppercase; color:{MUTED}; padding:8px 14px; }}
.erow .lnk, .drow .lnk, .sprow .lnk {{ display:flex; align-items:center; gap:10px; min-width:0; text-decoration:none !important; }}
.erow .nm, .drow .nm, .sprow .nm, .iprow .nm {{ display:flex; flex-direction:column; min-width:0; line-height:1.3; }}
.erow .nm b, .drow .nm b, .sprow .nm b, .iprow .nm b {{ color:#fff; font-size:.88rem; }}
.erow .nm small, .drow .nm small, .sprow .nm small, .iprow .nm small {{ color:{MUTED}; font-size:.72rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.erow .v, .drow .v, .iprow .v {{ text-align:center; direction:ltr; font-variant-numeric:tabular-nums; }}
.erow .q {{ color:#CCC7D5; font-size:.8rem; }}
.when {{ display:inline-flex; align-items:center; gap:5px; font-size:.78rem; font-weight:600; color:#CCC7D5; white-space:nowrap; }}
.when .ms {{ font-size:1rem; }} .when.bmo .ms {{ color:{GOLD}; }} .when.amc .ms {{ color:{PURPLE}; }} .when.tns .ms, .when.dmh .ms {{ color:{MUTED}; }}
.egrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:14px; margin:12px 0 8px; }}
.ecard {{ background:{BOX_BG}; border:1px solid {BORDER}; border-inline-start:4px solid #3A3545; border-radius:18px; padding:14px 16px;
  display:flex; flex-direction:column; gap:12px; min-width:0; }}
.ecard.beat {{ background:{UP_LINE}, linear-gradient(180deg, rgba(34,197,94,.13), {CARD} 72%); border-color:{UP_EDGE}; border-inline-start-color:#22C55E; }}
.ecard.miss {{ background:{DN_LINE}, linear-gradient(180deg, rgba(239,68,68,.13), {CARD} 72%); border-color:{DN_EDGE}; border-inline-start-color:#EF4444; }}
.ecard .top {{ display:flex; gap:12px; align-items:flex-start; }}
.ecard .top .lnk {{ flex:none; }}
.ecard .t {{ min-width:0; flex:1; }}
.ecard .t .nm {{ font-weight:600; color:#fff; font-size:1rem; line-height:1.3; }}
.ecard .t .co {{ color:{MUTED}; font-size:.76rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.ecard .t .d {{ display:flex; align-items:center; gap:5px; font-size:.74rem; color:#CCC7D5; margin-top:5px; }}
.ecard .t .d .ms {{ font-size:1rem; color:{GOLD}; }}
.ecard .px {{ text-align:end; flex:none; }}
.ecard .px .p {{ font-weight:600; font-size:1rem; color:#fff; direction:ltr; }}
.ecard .px .pill {{ margin-top:3px; }}
.ecard .rx {{ font-size:.7rem; color:{MUTED}; margin-top:5px; white-space:nowrap; }}
.ecard .rx .pos {{ color:#4ADE80; font-weight:600; }} .ecard .rx .neg {{ color:#F87171; font-weight:600; }}
.ecard table.res {{ display:table; width:100%; margin:0 !important; border-collapse:separate; border-spacing:0; font-size:.84rem; background:rgba(14,9,24,.5);
  border:1px solid {BORDER}; border-radius:12px; overflow:hidden; }}
.ecard table.res tr {{ border:none; }}
.ecard table.res th {{ font-size:.64rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:{MUTED}; padding:7px 8px; text-align:center; border:none; }}
.ecard table.res td {{ padding:8px; text-align:center; border:none; border-top:1px solid {BORDER}; direction:ltr; font-variant-numeric:tabular-nums; color:#CCC7D5; }}
.ecard table.res td.k {{ text-align:start; font-weight:600; direction:inherit; }}
.ecard table.res td.a {{ color:#fff; font-weight:600; }}
.ecard table.res td.pos {{ color:#4ADE80; font-weight:600; }} .ecard table.res td.neg {{ color:#F87171; font-weight:600; }}
.ecard table.res small {{ color:{MUTED}; font-size:.62rem; font-weight:600; }}
.ecard .vd {{ display:flex; align-items:center; gap:6px; font-size:.78rem; font-weight:600; color:{MUTED}; }}
.ecard .vd .ms {{ font-size:1.05rem; }}
.ecard.beat .vd {{ color:#4ADE80; }} .ecard.miss .vd {{ color:#F87171; }}
.evcal {{ display:flex; flex-direction:column; gap:14px; margin:12px 0 8px; }}
.evday {{ background:{BOX_BG}; border:1px solid {BORDER}; border-radius:16px; overflow:hidden; }}
.evday.today {{ border-color:rgba(59,139,235,.6); }}
.evday .dh {{ display:flex; align-items:center; gap:8px; padding:10px 14px; background:linear-gradient(90deg, rgba(59,139,235,.16), transparent); font-weight:600;
  color:#fff; flex-wrap:wrap; }}
.evday .dh .ms {{ color:#79B8F4; }}
.evday .dh .c {{ margin-inline-start:auto; font-size:.72rem; color:#BFDDF8; background:rgba(59,139,235,.16); padding:2px 9px; border-radius:10px; }}
.evday .dh .hnote {{ padding:3px 8px; }}
.evr {{ display:grid; grid-template-columns:78px 58px minmax(0,1fr) 92px 92px 92px; gap:10px; align-items:center; padding:8px 14px; border-top:1px solid {BORDER}; font-size:.86rem; }}
.evr.eh {{ font-size:.64rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:{MUTED}; background:{CARD2}; padding:7px 14px; }}
.evr .tm {{ font-weight:600; color:#CCC7D5; direction:ltr; font-variant-numeric:tabular-nums; }}
.evr.eh .tm {{ direction:inherit; }}
.evr .nm {{ color:#E7E3EB; font-weight:500; min-width:0; }}
.evr .nm small {{ color:{MUTED}; font-weight:600; margin-inline-start:4px; }}
.evr .rg {{ font-size:.62rem; font-weight:600; padding:1px 6px; border-radius:6px; background:rgba(157,151,165,.18); color:#CCC7D5; margin-inline-end:6px; }}
.evr .v {{ text-align:center; direction:ltr; font-variant-numeric:tabular-nums; color:#CCC7D5; }}
.evr .v.a {{ font-weight:600; color:#fff; }} .evr .v.a.pos {{ color:#4ADE80; }} .evr .v.a.neg {{ color:#F87171; }}
.evr.s3 {{ background:rgba(239,68,68,.05); }} .evr.s3 .nm {{ font-weight:600; }}
.stars {{ display:inline-flex; gap:3px; }} .stars i {{ width:11px; height:11px; border-radius:3px; background:#332E3D; display:inline-block; }}
.stars.s1 i.on {{ background:#64748B; }} .stars.s2 i.on {{ background:{GOLD}; }} .stars.s3 i.on {{ background:#EF4444; }}
.hlist {{ display:flex; flex-direction:column; gap:8px; margin:10px 0 6px; }}
.hrow {{ display:grid; grid-template-columns:56px minmax(0,1fr) auto 120px; gap:14px; align-items:center; padding:10px 14px; border-radius:14px;
  background:{BOX_BG}; border:1px solid {BORDER}; }}
.hrow .dt, .iprow .dt {{ width:52px; height:52px; border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center; line-height:1.1;
  background:rgba(239,68,68,.14); color:#FCA5A5; }}
.hrow .dt b, .iprow .dt b {{ font-size:1.25rem; color:#fff; }} .hrow .dt span, .iprow .dt span {{ font-size:.64rem; font-weight:600; text-transform:uppercase; }}
.hrow.early .dt {{ background:rgba(245,185,74,.16); color:{GOLD}; }} .hrow.bonds .dt, .iprow .dt {{ background:rgba(59,139,235,.14); color:#93C5FD; }}
.hrow .nm b {{ display:block; color:#fff; }} .hrow .nm small {{ color:{MUTED}; }}
.hrow .st {{ display:inline-flex; align-items:center; gap:6px; font-size:.76rem; font-weight:600; padding:4px 11px; border-radius:20px; background:{NEG_BG}; color:{NEG_FG};
  white-space:nowrap; }}
.hrow .st .ms {{ font-size:1rem; }}
.hrow.early .st {{ background:{YEL_BG}; color:{YEL_FG}; }} .hrow.bonds .st {{ background:{ACC_BG}; color:{ACC_FG}; }}
.hrow .wh {{ text-align:end; color:{MUTED}; font-size:.8rem; font-weight:600; }}
.hrow.past {{ opacity:.5; }} .hrow.next {{ border-color:rgba(59,139,235,.65); box-shadow:0 10px 26px rgba(59,139,235,.14); }}
.hrow.next .wh {{ color:#BFDDF8; }}
.calnote {{ display:flex; gap:10px; align-items:flex-start; margin:14px 0 6px; line-height:1.85; font-size:.86rem; color:#CCC7D5; }}
.calnote .ms {{ color:#79B8F4; margin-top:3px; }}
.calempty {{ display:flex; flex-direction:column; align-items:center; gap:8px; padding:36px 18px; margin:12px 0; border:1px dashed #3E3A46; border-radius:16px;
  color:{MUTED}; text-align:center; line-height:1.7; }}
.calempty .ms {{ font-size:2.2rem; color:#79B8F4; }}
.drow {{ display:grid; grid-template-columns:minmax(0,2.4fr) 1fr 1fr .9fr 1.1fr; gap:10px; align-items:center; padding:8px 14px; border-top:1px solid {BORDER}; font-size:.86rem; }}
.drow.th {{ font-size:.64rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:{MUTED}; background:{CARD2}; padding:7px 14px; }}
.drow .v.y {{ color:#4ADE80; font-weight:600; }}
.splist {{ display:flex; flex-direction:column; gap:8px; margin:10px 0 6px; }}
.sprow {{ display:grid; grid-template-columns:minmax(0,2fr) 110px 120px minmax(0,1.6fr) 130px; gap:12px; align-items:center; padding:10px 14px; border-radius:14px;
  background:{BOX_BG}; border:1px solid {BORDER}; }}
.sprow .ratio {{ font-weight:600; font-size:1.05rem; color:#fff; direction:ltr; text-align:center; }}
.sprow .k {{ display:inline-flex; gap:6px; align-items:center; font-size:.76rem; font-weight:600; padding:4px 11px; border-radius:20px; justify-self:start; }}
.sprow .k .ms {{ font-size:1rem; }}
.sprow.forward .k {{ background:{POS_BG}; color:{POS_FG}; }} .sprow.reverse .k {{ background:{ORG_BG}; color:{ORG_FG}; }}
.sprow .ex {{ color:{MUTED}; font-size:.8rem; }} .sprow .dt {{ text-align:end; font-weight:600; color:#CCC7D5; }}
.iplist {{ border:1px solid {BORDER}; border-radius:16px; overflow:hidden; background:{BOX_BG}; margin:10px 0 6px; }}
.iprow {{ display:grid; grid-template-columns:52px 36px minmax(0,2fr) 90px 110px 90px 100px 74px 128px; gap:10px; align-items:center; padding:9px 14px;
  border-top:1px solid {BORDER}; font-size:.86rem; }}
.iprow.ih {{ border-top:none; background:{CARD2}; font-size:.64rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:{MUTED}; }}
.iprow .ex {{ color:#CCC7D5; font-size:.78rem; font-weight:600; }}
.iprow .badge {{ justify-self:start; }}
@media (max-width: 1100px) {{ .ehub {{ grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); }} }}
@media (max-width: 900px) {{
  .erow {{ grid-template-columns:minmax(0,1.7fr) 1fr .9fr; }} .erow > :nth-child(3), .erow > :nth-child(4), .erow > :nth-child(5), .erow > :nth-child(7) {{ display:none; }}
  .evr {{ grid-template-columns:52px minmax(0,1fr) 70px 70px; }} .evr > :nth-child(2), .evr > :nth-child(6) {{ display:none; }}
  .drow {{ grid-template-columns:minmax(0,1.8fr) 1fr .9fr; }} .drow > :nth-child(3), .drow > :nth-child(5) {{ display:none; }}
  .sprow {{ grid-template-columns:minmax(0,1fr) auto; }} .sprow .ex, .sprow .k {{ display:none; }}
  .iprow {{ grid-template-columns:44px minmax(0,1fr) 90px auto; }} .iprow > :nth-child(2), .iprow > :nth-child(4), .iprow > :nth-child(6), .iprow > :nth-child(7),
  .iprow > :nth-child(8) {{ display:none; }}
  .hrow {{ grid-template-columns:52px minmax(0,1fr); }} .hrow .st, .hrow .wh {{ grid-column:2; justify-self:start; text-align:start; }}
}}
/* ---------- catalyst pro header: name + chips, with room under them for the gauge title ---------- */
.cathead {{ display:flex; flex-direction:column; gap:10px; margin:4px 0 22px; }}
.cathead h3 {{ margin:0 !important; padding:0 !important; line-height:1.3; }}
.cathead .chips {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
.cathead .chips .badge {{ margin:0; }}
/* ---------- news pictures ---------- */
.news .nwrap {{ display:flex; gap:16px; align-items:flex-start; }}
.news .nbody {{ flex:1; min-width:0; }}
.nth {{ position:relative; flex:none; display:flex; align-items:center; justify-content:center; width:176px; height:118px; border-radius:14px; overflow:hidden;
  background:var(--g); box-shadow:0 8px 20px rgba(0,0,0,.35), inset 0 0 0 1px rgba(255,255,255,.08); }}
.nth::before {{ content:""; position:absolute; inset:0; z-index:0; opacity:.5; background:
  radial-gradient(circle at 18% 22%, rgba(255,255,255,.28), transparent 42%),
  repeating-linear-gradient(90deg, rgba(255,255,255,.07) 0 1px, transparent 1px 22px),
  repeating-linear-gradient(0deg, rgba(255,255,255,.05) 0 1px, transparent 1px 22px); }}
.nth img {{ position:relative; z-index:1; display:block; width:100%; height:100%; object-fit:cover; background:#221D2F; }}
.nth img::after {{ content:attr(data-ic); position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
  font-family:'Material Symbols Rounded'; font-size:48px; color:rgba(255,255,255,.95); background:var(--g); }}
.nth.fb .ms {{ position:relative; z-index:1; font-size:50px; color:#fff; text-shadow:0 6px 18px rgba(0,0,0,.3); }}
.nth.fb em {{ position:absolute; z-index:1; inset-inline-start:10px; bottom:8px; font-style:normal; font-size:.64rem; font-weight:600; letter-spacing:.08em;
  text-transform:uppercase; color:rgba(255,255,255,.9); }}
.nth.fb em::after {{ content:attr(data-en); }}
.nth .nlg {{ position:absolute; z-index:2; inset-inline-end:8px; bottom:8px; display:flex; border-radius:11px; box-shadow:0 4px 12px rgba(0,0,0,.45); }}
.nth.big {{ width:100%; height:150px; border-radius:14px; margin-bottom:12px; }}
.story .nth.big {{ margin:-4px 0 12px; }}
@media (max-width: 640px) {{ .news .nwrap {{ flex-direction:column; }} .news .nth {{ width:100%; height:170px; }} }}
.story:has(.nth) .rank {{ top:24px; inset-inline-end:auto; inset-inline-start:28px; z-index:3; font-size:.9rem; color:#fff; background:rgba(14,9,24,.55);
  padding:2px 10px; border-radius:10px; backdrop-filter:blur(6px); -webkit-backdrop-filter:blur(6px); }}
.story:has(.nth) a.t {{ margin-inline-end:0; }}
/* ---------- news bot ---------- */
.news .meta .also {{ display:inline-block; margin-inline-start:4px; padding:0 6px; border-radius:8px; background:rgba(59,139,235,.18); color:#BFDDF8; font-weight:600;
  font-size:.66rem; cursor:help; }}
.botbar {{ display:flex; align-items:center; gap:10px 16px; flex-wrap:wrap; padding:10px 14px; border-radius:14px; margin:8px 0 10px;
  background:linear-gradient(90deg, rgba(34,197,94,.1), rgba(59,139,235,.08)); border:1px solid rgba(34,197,94,.3); font-size:.84rem; color:#CCC7D5; }}
.botbar .live {{ display:inline-flex; align-items:center; gap:7px; font-weight:600; color:#4ADE80; }}
.botbar .live i {{ width:9px; height:9px; border-radius:50%; background:#22C55E; box-shadow:0 0 0 0 rgba(34,197,94,.6); animation:botpulse 1.8s infinite; }}
@keyframes botpulse {{ 0% {{ box-shadow:0 0 0 0 rgba(34,197,94,.55); }} 70% {{ box-shadow:0 0 0 8px rgba(34,197,94,0); }} 100% {{ box-shadow:0 0 0 0 rgba(34,197,94,0); }} }}
.botbar b {{ color:#fff; }}
.srcgrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); gap:8px; }}
.srcc {{ display:flex; align-items:center; gap:8px; padding:8px 10px; border-radius:12px; background:{BOX_BG}; border:1px solid {BORDER}; font-size:.8rem; min-width:0; }}
.srcc .d {{ width:9px; height:9px; border-radius:50%; flex:none; background:#22C55E; }} .srcc.bad .d {{ background:#EF4444; }} .srcc.wait .d {{ background:#64748B; }}
.srcc b {{ color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.srcc span {{ margin-inline-start:auto; color:{MUTED}; white-space:nowrap; font-size:.72rem; }}
/* ---------- one table look everywhere (the Recent-trades panel): rounded rows, muted header, numbers on the right ---------- */
.xtp {{ position:relative; overflow:hidden; background:{BOX_BG}; border:1px solid {BORDER}; border-radius:18px; padding:12px 14px 8px 18px; margin:4px 0 12px; }}
.xtp::before {{ content:""; position:absolute; top:0; bottom:0; left:0; width:2px; background:{ELECTRIC}; }}
.xtp .hd {{ display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; margin:2px 0 8px; }}
.xtp .tt {{ display:flex; align-items:center; gap:8px; font-weight:600; font-size:1.02rem; color:#fff; }}
.xtp .tt .ms {{ color:#fff; background:{PANEL}; box-shadow:{GLOW}; border-radius:8px; padding:4px; font-size:1rem; }}
.xtp .sum {{ display:flex; flex-wrap:wrap; gap:7px; align-items:center; }}
.xtp .sum .c {{ display:inline-flex; align-items:center; gap:7px; background:rgba(157,151,165,.10); border:1px solid {BORDER}; border-radius:999px;
  padding:4px 12px; font-size:.75rem; font-weight:600; color:#B1ABBA; line-height:1.4; white-space:nowrap; }}
.xtp .sum .c b {{ color:#fff; direction:ltr; unicode-bidi:isolate; }}
.xtsc {{ overflow:auto; scrollbar-width:thin; }}
.xtbl {{ width:100%; border-collapse:separate !important; border-spacing:0 4px !important; font-size:.8rem; direction:ltr;
  border:none !important; margin:-4px 0 0 !important; background:none !important; display:table !important; }}
.xtbl thead tr, .xtbl tbody tr {{ background:none !important; border:none !important; }}
.xtbl th {{ position:sticky; top:0; z-index:1; background:#1D1829 !important; color:{MUTED}; font-size:.6rem; letter-spacing:.09em; text-transform:uppercase;
  text-align:left; padding:8px 12px 5px !important; font-weight:600; white-space:nowrap; border:none !important; }}
.xtbl td {{ padding:7px 12px !important; white-space:nowrap; vertical-align:middle; text-align:left; line-height:1.35; color:#DDD9E2;
  background:rgba(255,255,255,.028) !important; border:none !important; border-top:1px solid rgba(255,255,255,.045) !important;
  border-bottom:1px solid rgba(255,255,255,.045) !important; transition:background .15s ease; }}
.xtbl td:first-child {{ border-left:1px solid rgba(255,255,255,.045) !important; border-radius:10px 0 0 10px; }}
.xtbl td:last-child {{ border-right:1px solid rgba(255,255,255,.045) !important; border-radius:0 10px 10px 0; }}
.xtbl tbody tr:hover td {{ background:rgba(59,139,235,.10) !important; }}
.xtbl .r {{ text-align:right; font-variant-numeric:tabular-nums; }}
.xtbl td.w {{ white-space:normal; min-width:180px; max-width:420px; }}
.xtp .xtsc {{ direction:ltr; }}   /* the table reads left to right in Arabic too: start the scroll at its first column */
.xtbl b {{ color:#fff; font-weight:600; }}
.xtbl .as {{ display:inline-flex; align-items:center; gap:8px; color:#fff !important; text-decoration:none !important; }}
.xtbl .as .lg {{ width:22px !important; height:22px !important; font-size:9px !important; }}
.xtbl .as:hover b {{ color:#79B8F4; }}
.xtbl .m {{ color:{MUTED}; font-size:.72rem; font-weight:600; }}
.xtbl .up {{ color:#4ADE80; font-weight:600; }} .xtbl .dn {{ color:#F87171; font-weight:600; }}
.xtbl .pbox {{ padding:1px 9px; font-size:.76rem; border-radius:999px; }}
.xtbl a {{ color:#79B8F4; }}
.xtbl .xbar {{ display:inline-block; width:64px; height:6px; border-radius:6px; background:rgba(157,151,165,.18); overflow:hidden;
  vertical-align:middle; margin-right:8px; }}
.xtbl .xbar i {{ display:block; height:100%; border-radius:6px; background:linear-gradient(90deg,{ACCENT},{VIOLET},{CYAN}); }}
.xtbl .xgr {{ display:inline-block; min-width:30px; text-align:center; padding:1px 8px; border-radius:999px; font-weight:600; font-size:.74rem;
  color:var(--g); border:1px solid var(--g); background:rgba(255,255,255,.04); }}
/* ---------- every table is interactive (theme.FX_JS): press a column's name to sort by it (again: the other way, a third time: the
   original order), long tables get a filter box with a count, the column under the pointer lights its name, a pressed row stays lit ---------- */
th.tx-s {{ cursor:pointer; user-select:none; transition: color .15s, background .15s; }}
th.tx-s:hover, th.tx-s:focus-visible, th.tx-hc {{ color:#fff !important; }}
th.tx-s:focus-visible {{ outline:2px solid rgba(123,69,240,.6); outline-offset:-2px; border-radius:6px; }}
th.tx-s::after {{ content:"↕"; display:inline-block; margin-inline-start:5px; font-size:.95em; opacity:0; transition: opacity .15s; }}
th.tx-s:hover::after, th.tx-hc::after {{ opacity:.45; }}
th.tx-s[aria-sort="ascending"]::after {{ content:"▲"; opacity:1; color:{VIO_FG}; font-size:.8em; }}
th.tx-s[aria-sort="descending"]::after {{ content:"▼"; opacity:1; color:{VIO_FG}; font-size:.8em; }}
th.tx-s:is([aria-sort="ascending"], [aria-sort="descending"]) {{ color:#fff !important; }}
table[data-tx] tbody tr {{ transition: opacity .15s; }}
table[data-tx] tbody tr:hover td:first-child {{ box-shadow: inset 3px 0 0 {ACCENT}; }}
table[data-tx] tbody tr.tx-pin td {{ background: rgba(123,69,240,.18) !important; }}
table[data-tx] tbody tr.tx-pin td:first-child {{ box-shadow: inset 3px 0 0 {VIOLET}; }}
table[data-tx] tbody tr.tx-hide {{ display:none; }}
.tx-tools {{ display:flex; align-items:center; gap:10px; margin:0 0 8px; direction:inherit; }}
.tx-q {{ flex:1; max-width:340px; display:flex; align-items:center; gap:7px; height:34px; padding:0 11px; border-radius:11px; box-sizing:border-box;
  background:rgba(255,255,255,.04); border:1px solid {BORDER}; transition: border-color .15s, box-shadow .15s; cursor:text; }}
.tx-q:focus-within {{ border-color: rgba(123,69,240,.6); box-shadow: 0 0 0 3px rgba(123,69,240,.18); }}
.tx-q .ms {{ font-size:18px; color:{MUTED}; }}
.tx-q input {{ flex:1; min-width:0; height:100%; background:none !important; border:0 !important; outline:0 !important; box-shadow:none !important;
  color:{TEXT}; font:inherit; font-size:.82rem; padding:0; }}
.tx-q input::placeholder {{ color:{MUTED}; opacity:1; }}
.tx-n {{ font-size:.74rem; color:{MUTED}; font-weight:600; font-variant-numeric:tabular-nums; white-space:nowrap; }}
/* ---------- the "?" next to every trading term (terms.py) and the box that explains it in Arabic and English (theme.FX_JS) ---------- */
.gq {{ display:inline-flex !important; align-items:center; justify-content:center; flex:none; width:15px; height:15px; box-sizing:border-box;
  margin-inline-start:4px; padding:0 !important; border-radius:50%; vertical-align:1px; position:relative; z-index:3;
  font:700 10px/1 {FONT_LATIN}, system-ui, sans-serif !important; letter-spacing:0 !important; text-transform:none !important; font-style:normal;
  text-decoration:none !important; color:#C4B5FD !important; background:rgba(123,69,240,.16); border:1px solid rgba(167,139,250,.38);
  cursor:pointer; user-select:none; -webkit-user-select:none; transition: background .15s, color .15s, border-color .15s, transform .15s; }}
.gq:hover, .gq:focus-visible, .gq.on {{ background:#7B45F0; border-color:#A78BFA; color:#FFFFFF !important; transform:scale(1.15); outline:none; }}
.gqpop {{ position:fixed; z-index:1000300; width:min(340px, calc(100vw - 24px)); box-sizing:border-box; padding:14px 16px 12px; border-radius:16px;
  background:#1A1624; border:1px solid rgba(167,139,250,.38); color:#E7E3EB; box-shadow:0 22px 56px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.03);
  font-family:{FONT_LATIN}, {FONT_AR}, system-ui, sans-serif; animation: gqin .16s ease-out both; }}
.gqpop::before {{ content:""; position:absolute; top:-6px; left:var(--ax, 50%); width:10px; height:10px; margin-left:-5px; transform:rotate(45deg);
  background:#1A1624; border-left:1px solid rgba(167,139,250,.38); border-top:1px solid rgba(167,139,250,.38); }}
.gqpop.up::before {{ top:auto; bottom:-6px; transform:rotate(225deg); }}
.gqpop.up {{ animation-name: gqup; }}
@keyframes gqin {{ from {{ opacity:0; transform:translateY(-4px); }} to {{ opacity:1; transform:none; }} }}
@keyframes gqup {{ from {{ opacity:0; transform:translateY(4px); }} to {{ opacity:1; transform:none; }} }}
.gqpop .gqx {{ position:absolute; top:8px; inset-inline-end:8px; width:26px; height:26px; border-radius:8px; border:0; cursor:pointer; padding:0;
  background:rgba(255,255,255,.06); color:#9D97A5; font-size:17px; line-height:26px; }}
.gqpop .gqx:hover {{ background:rgba(255,255,255,.12); color:#FFFFFF; }}
.gqpop .gqb {{ padding:2px 0; }}
.gqpop .gqb + .gqb {{ margin-top:10px; padding-top:10px; border-top:1px dashed rgba(255,255,255,.12); }}
.gqpop .gql {{ display:inline-block; font-size:.62rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:#C4B5FD;
  background:rgba(123,69,240,.16); border-radius:6px; padding:2px 7px; margin-bottom:6px; }}
.gqpop .gqb[dir="rtl"] .gql {{ letter-spacing:0; }}
.gqpop b {{ display:block; font-size:.98rem; font-weight:700; color:#FFFFFF; margin:0 30px 4px 0; line-height:1.35; }}
.gqpop .gqb[dir="rtl"] b {{ margin:0 0 4px 30px; }}
.gqpop .gqb + .gqb b {{ margin-left:0; margin-right:0; }}
.gqpop .gqb:first-of-type .gql {{ margin-inline-end:30px; }}
.gqpop p {{ margin:0; font-size:.86rem; line-height:1.65; color:#CFCAD6; }}
.gqpop .gqb[dir="rtl"] {{ text-align:right; font-family:{FONT_AR}, {FONT_LATIN}, system-ui, sans-serif; }}
.gqpop .gqb[dir="ltr"] {{ text-align:left; }}
@media (prefers-reduced-motion: reduce) {{ .gqpop {{ animation:none; }} .gq {{ transition:none; }} }}
/* ---------- the hand-built tables in the same look: a box with the brand bar on its left, rounded rows, muted header ---------- */
.chainwrap, .etab, .iplist {{ position:relative; background:{BOX_BG} !important; border:1px solid {BORDER}; border-radius:18px; padding:8px 12px 8px 17px; }}
.chainwrap::before, .etab::before, .iplist::before, .evday::before {{ content:""; position:absolute; top:0; bottom:0; left:0; width:3px; z-index:2;
  background:linear-gradient(180deg,{ACCENT},{VIOLET},{CYAN}); }}
.evday {{ position:relative; }}
.chain {{ border-collapse:separate !important; border-spacing:0 4px !important; margin:-4px 0 0 !important; }}
.chain th {{ background:#1D1829 !important; border:none !important; font-size:.62rem; font-weight:600; letter-spacing:.07em; text-transform:uppercase; padding:8px 8px 5px; }}
.chain td {{ color:#DDD9E2; background:rgba(255,255,255,.028); border:none !important; border-top:1px solid rgba(255,255,255,.045) !important;
  border-bottom:1px solid rgba(255,255,255,.045) !important; padding:7px 8px; }}
.chain td:first-child {{ border-left:1px solid rgba(255,255,255,.045) !important; border-radius:10px 0 0 10px; }}
.chain td:last-child {{ border-right:1px solid rgba(255,255,255,.045) !important; border-radius:0 10px 10px 0; }}
.chain td.k {{ background:rgba(59,139,235,.12) !important; }}
.chain tr.atm td {{ border-top:2px solid {ACCENT} !important; }}
.chain td.itm-c {{ background:rgba(34,197,94,.09); }} .chain td.itm-p {{ background:rgba(239,68,68,.09); }}
.chain tr:hover td {{ background:rgba(59,139,235,.10); }}
.erow:not(.eh), .drow:not(.th), .iprow:not(.ih) {{ border:1px solid rgba(255,255,255,.045) !important; border-radius:10px; background:rgba(255,255,255,.028);
  margin:4px 0; transition:background .15s ease; }}
.erow:not(.eh):hover, .drow:not(.th):hover, .iprow:not(.ih):hover, .evr:not(.eh):hover {{ background:rgba(59,139,235,.10); }}
.erow.eh, .drow.th, .iprow.ih {{ background:transparent !important; border:none !important; padding-top:6px; padding-bottom:4px; }}
.evday .evr {{ margin:4px 10px 4px 14px; border:1px solid rgba(255,255,255,.045); border-radius:10px; background:rgba(255,255,255,.028); }}
.evday .evr.eh {{ background:transparent; border:none; margin-top:6px; margin-bottom:0; }}
.evday .evr.s3 {{ background:rgba(239,68,68,.07); border-color:rgba(239,68,68,.25); }}
.evday > :last-child {{ margin-bottom:10px; }}
.rtab {{ border-collapse:separate !important; border-spacing:0 4px !important; }}
.rtab th {{ border:none !important; font-size:.6rem; font-weight:600; padding:6px 10px 3px; }}
.rtab td {{ background:rgba(255,255,255,.028); border:none !important; border-top:1px solid rgba(255,255,255,.045) !important;
  border-bottom:1px solid rgba(255,255,255,.045) !important; padding:7px 10px; }}
.rtab td:first-child {{ border-left:1px solid rgba(255,255,255,.045) !important; border-radius:10px 0 0 10px; }}
.rtab td:last-child {{ border-right:1px solid rgba(255,255,255,.045) !important; border-radius:0 10px 10px 0; }}
.rtab tr:hover td {{ background:rgba(59,139,235,.10); }}
/* ---------- every chart sits in a box (never straight on the night sky); boxes in one row share one height ---------- */
/* Streamlit draws the chart exactly as wide and as tall as this box, so the box takes no padding (it used to cut the chart's
   bottom and right edge: axis titles, colour-bar titles); its line is drawn inside it and the chart's own margins give the air */
[data-testid="stPlotlyChart"] {{ background:{BOX_BG}; border:0 !important; box-shadow: inset 0 0 0 1px {BORDER}; border-radius:18px; padding:0 !important;
  box-sizing:border-box; overflow:hidden; transition:box-shadow .25s ease; }}
@media (hover:hover) {{ [data-testid="stPlotlyChart"]:hover {{ box-shadow: inset 0 0 0 1px rgba(167,139,250,.38), 0 22px 44px -30px rgba(123,69,240,.75); }} }}
:is([class*="st-key-pbcalbox_"], [class*="st-key-pbf_"], [class*="st-key-hnbar"], [class*="st-key-pbmg_"], .st-key-czhero) [data-testid="stPlotlyChart"]
  {{ background:none; box-shadow:none; }}
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:only-child,
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:only-child > .stMarkdown,
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:only-child [data-testid="stMarkdownContainer"],
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:only-child [data-testid="stMarkdownContainer"] > div:only-child
  {{ height:100%; }}
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:only-child [data-testid="stMarkdownContainer"] > div:only-child
  > :is(.card,.kpi,.tile,.mcard,.story,.fgc,.dcard,.tdc,.tdp,.lc,.rmeter):only-child {{ height:100%; box-sizing:border-box; }}
/* ---------- boxes with a see-through tint get a solid dark base, so the background photo never shows through them ---------- */
:is(.pulse,.brief,.hnbox,.hnrate,.hntgt,.hnkt,.hnplan .p,.tkw,.botbar,.ecard,.ac-hero,.ac-note,.lr.now,.hndh,.hnnote,.pbrl,.story,.news)
  {{ background-color:{CARD} !important; }}
/* ---------- indicator signals: three columns, each with its name and its column headings on top ---------- */
.sgcols {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }}
@media (max-width: 1100px) {{ .sgcols {{ grid-template-columns:minmax(0,1fr); }} }}
.sgcol {{ position:relative; overflow:hidden; background:{BOX_BG}; border:1px solid {BORDER}; border-radius:18px; padding:12px 12px 10px 16px; }}
.sgcol::before {{ content:""; position:absolute; top:0; bottom:0; left:0; width:2px; background:{ELECTRIC}; }}
.sgh {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin:2px 0 8px; }}
.sgh .ms {{ color:#fff; background:{PANEL}; box-shadow:{GLOW}; border-radius:8px; padding:4px; font-size:1rem; }}
.sgh b {{ color:#fff; font-size:.95rem; font-weight:600; }}
.sgh .ct {{ margin-inline-start:auto; display:flex; gap:6px; }}
.sgh .ct i {{ font-style:normal; font-size:.7rem; font-weight:600; padding:2px 8px; border-radius:999px; }}
.sgh .ct i.up {{ background:{POS_BG}; color:{POS_FG}; }} .sgh .ct i.dn {{ background:{NEG_BG}; color:{NEG_FG}; }}
.sgth, .sgr {{ display:grid; grid-template-columns:minmax(0,1fr) 84px 80px; gap:8px; align-items:center; }}
.sgth {{ padding:4px 10px 2px; font-size:.6rem; font-weight:600; letter-spacing:.09em; text-transform:uppercase; color:{MUTED}; }}
.sgth span:nth-child(2), .sgr .v {{ text-align:right; }} .sgth span:nth-child(3), .sgr .pill {{ justify-self:end; }}
.sgr {{ margin-top:4px; padding:7px 10px; border-radius:10px; background:rgba(255,255,255,.028); border:1px solid rgba(255,255,255,.045);
  font-size:.82rem; transition:background .15s ease; }}
.sgr:hover {{ background:rgba(59,139,235,.10); }}
.sgr .n {{ color:#fff; font-weight:600; line-height:1.3; }}
.sgr .v {{ color:#CCC7D8; direction:ltr; font-variant-numeric:tabular-nums; }}
.sgr .pill {{ min-width:64px; text-align:center; }}
/* ---------- quiet text on the void (no photo behind it any more, so no shadows) ---------- */
[data-testid="stCaptionContainer"] {{ color:#A9A3B2 !important; }}
[data-testid="stWidgetLabel"] p {{ color:#CFCAD6; }}
/* ---------- coloured boxes keep their colour: a green wash with soft green edges, red the same ---------- */
.botbar {{ background:linear-gradient(90deg, rgba(34,197,94,.1), rgba(59,139,235,.06)), {CARD}; border-color:{UP_EDGE}; }}
:is(.card,.tile,.kpi,.stat,.mx .m,.opos .o,.perfrow .pc2,.sigs .sg,.lr,.evt,.fgc,.prof .it,.plan .p,.mcard,.lc,.tdc,.tdp,.dcard,.cal .d,.story,.news).pos
  {{ background:{UP_TINT}, {CARD} !important; border-color:{UP_EDGE} !important; }}
:is(.card,.tile,.kpi,.stat,.mx .m,.opos .o,.perfrow .pc2,.sigs .sg,.lr,.evt,.fgc,.prof .it,.plan .p,.mcard,.lc,.tdc,.tdp,.dcard,.cal .d,.story,.news).neg
  {{ background:{DN_TINT}, {CARD} !important; border-color:{DN_EDGE} !important; }}
.acard .aart::after {{ content:""; position:absolute; left:0; right:0; top:0; height:1px; background:linear-gradient(90deg,transparent,rgba(196,181,253,.5),transparent); z-index:2; }}
/* Streamlit's message boxes: a dark wash of their colour and a hairline edge */
[data-testid="stAlertContainer"] {{ border:1px solid rgba(59,139,235,.35); background:rgba(59,139,235,.08) !important; border-radius:14px; }}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) {{ border-color:{UP_EDGE}; background:rgba(34,197,94,.08) !important; }}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {{ border-color:{DN_EDGE}; background:rgba(239,68,68,.08) !important; }}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {{ border-color:rgba(245,185,74,.4); background:rgba(245,185,74,.07) !important; }}
/* ---------- n8n's signature pieces ---------- */
/* hover: a box lifts its hairline, never floats on a shadow */
:is(.card,.tile,.mcard,.kpi,.story,.news,.lc,.tdc,.tdp,.dcard,.fgc,.acard):hover {{ border-color:rgba(255,255,255,.16); }}
.tile:hover {{ box-shadow:none; }}
/* the big boxes are "backlit hardware": a white hairline inside and a violet glow from below */
:is(.brief,.pulse,.rmeter,.xtp,.sgcol) {{ box-shadow:{GLOW}; }}
/* the page heroes: a strong violet light rising from under them, as on n8n's home page */
:is(.hero,.pbhero,.hnhero) {{ border-color:{SHELL} !important; box-shadow:inset 0 0 0 1px rgba(255,255,255,.06), inset 0 -110px 120px -80px rgba(107,33,239,.65), inset 0 90px 110px -90px rgba(7,122,199,.35) !important; }}
.pulse {{ background:{PANEL} !important; border-color:{SHELL}; }}
.brief {{ background:radial-gradient(700px 260px at 0% 0%, rgba(7,122,199,.18), transparent 60%), radial-gradient(600px 240px at 100% 0%, rgba(107,33,239,.2), transparent 60%), {CARD} !important; }}
/* small numbers and chips: the frosted ghost look */
.badge, .kwc, .tkc, .chip2, .xtp .sum .c, .pbrec .c {{ backdrop-filter:blur(6px); -webkit-backdrop-filter:blur(6px); }}
/* links in the electric blue */
.stMarkdown a:not(.lnk):not(.as):not(.t):not(.czn):not(.et) {{ color:#79B8F4; }}
/* the navigation: the active page carries the electric line */
[class*="st-key-navon_"] [data-testid="stPageLink"] a {{ background: linear-gradient(90deg, rgba(7,122,199,.22), rgba(107,33,239,.14)) !important; }}
.navbtn.on {{ background: rgba(107,33,239,.14); border-color: rgba(123,69,240,.4); }}
[class*="st-key-navsec_"]:hover .navbtn {{ background: rgba(255,255,255,.05); border-color: rgba(255,255,255,.16); }}
[class*="st-key-navdd_"], .st-key-langdd {{ background: rgba(26,22,36,.97) !important; border-color:{SMOKE} !important; box-shadow:{GLOW}, 0 24px 50px rgba(0,0,0,.6) !important; }}
/* charts sit on the card surface with a hairline */

/* the big light headlines: the highlighted words stay light too, in the electric colours */
:is(.pbhero .t, .hnhero .t, .hero .title, .article .at, .brief .hl) b {{ font-weight:400; }}
/* motion: nothing moves for people who ask for less */
@media (prefers-reduced-motion: reduce) {{ .hero, .tape .track {{ animation:none !important; }} }}
</style>
"""

RTL_CSS = f"""
<style>
.block-container, [data-testid="stMainBlockContainer"], [data-testid="stSidebarContent"] {{ direction: rtl; }}
[data-testid="stSidebarHeader"] {{ direction: ltr; }}   /* the logo stays on the left, as in English */
[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"], h1, h2, h3, h4, label, .stMarkdown {{ text-align: right; }}
.stPlotlyChart, .js-plotly-plot, [data-testid="stDataFrame"], .tape, .t-row, [data-testid="stMetricValue"], [data-testid="stMetricDelta"] {{ direction: ltr; }}
.stPlotlyChart *, .js-plotly-plot *, [data-testid="stPlotlyChart"] *, .hm, .hm * {{ direction: ltr !important; }}
[data-testid="stMetricValue"] {{ text-align: right; }}
[data-testid="stTabsScrollLeft"], [data-testid="stTabsScrollRight"] {{ display:none !important; }}   /* they read the scroll the left-to-right way: in Arabic the strip is swiped */
@media (hover:hover) {{ [class*="st-key-stkact_"]:hover .sx-go {{ transform:translateX(-3px); }} }}
input, textarea {{ text-align: right; }}
html, body, .stApp, .stMarkdown, button, input, textarea, select, label, [data-baseweb] {{ font-family: {FONT_AR}, {FONT_LATIN}, system-ui, sans-serif; }}
.sec::after {{ background: linear-gradient(270deg, rgba(107,33,239,.45), rgba(7,122,199,.18) 30%, transparent); }}
h1 {{ font-weight: 400 !important; letter-spacing: 0; line-height:1.35 !important; }}
:is(.pbhero .t, .hnhero .t, .hero .title, .article .at, .brief .hl) {{ font-weight:400; letter-spacing:0; line-height:1.3; }} h2, h3 {{ letter-spacing: 0; }} .sec {{ letter-spacing: 0; font-size:1.2rem; }}
[class*="st-key-navdd_"] {{ left:auto; right:0; transform-origin: top right; }}
[class*="st-key-navon_"] [data-testid="stPageLink"] a {{ box-shadow: inset -3px 0 0 {ACCENT}; }}
[class*="st-key-navdd_"] [data-testid="stPageLink"] a:hover {{ transform: translateX(-2px); }}
.st-key-langdd {{ right:auto; left:0; transform-origin: top left; }}
.nth.fb em::after {{ content:attr(data-ar); }} .nth.fb em {{ letter-spacing:0; font-size:.72rem; }}
.xtbl th {{ letter-spacing:0; font-size:.7rem; }}
.sgth {{ letter-spacing:0; font-size:.7rem; }}
</style>
"""


# ---------------------------------------------------------------- interactive cards
# The light follows the pointer: over a card, a violet spotlight glows inside it and its edge lights up where the pointer
# is; the card lifts a little and presses in when clicked. FX_JS (run once per browser tab from app.py) finds the card under
# the pointer - also under the invisible buttons that make whole cards clickable - and hands it the pointer position.
FX_CARDS = (
    # every card, tile and panel of the site (theme)
    ".card", ".tile", ".kpi", ".mcard", ".lc", ".stat", ".plan .p", ".prof .it", ".news", ".story", ".rmeter", ".lr", ".secgrid .sc",
    ".course", ".dcard", ".lesson", ".hmwrap", ".tdc", ".tdp", ".cal .d", ".cal .wk", ".opos .o", ".mx .m", ".perfrow .pc2", ".sigs .sg",
    ".brief", ".evt", ".acard", ".tkw", ".fgc", ".pulse", ".wlr", ".ehub .day", ".etab", ".ecard", ".evday", ".hrow", ".sprow", ".iplist",
    ".botbar", ".srcc", ".xtp", ".chainwrap", ".sgcol", ".msh", ".mst", '[data-testid="stMetric"]', '[data-testid="stPlotlyChart"]',
    '[data-testid="stExpander"] details',
    # home page
    ".czcard", ".czn",
    # Paper Bots
    ".pbph", ".pbkd", ".pbmode", ".wwc", ".pbp", ".pbid", ".pbrl", ".aic", '[class*="st-key-aicard_"]', '[class*="st-key-pbmg_"]',
    '[class*="st-key-pbcalbox_"]',
    # Opportunity Hunter
    ".hnbox", ".hnrate", ".hntgt", ".hnkt", ".hnplan .p", ".hndh", '[class*="st-key-hnbar"]', '[class*="st-key-hnfilt"]',
    # Sharia check
    ".shc", ".shbn")
FX_NO_RING = (".hnkt", ".hnplan .p")                                  # their ::after is taken: the spotlight only
FX_NO_GLOW = (".pbc", ".hnc", ".msh", ".xtp", ".sgcol", ".pbid", ".pbp", ".hnrate", ".hndh", ".etab", ".iplist", ".chainwrap", ".evday",
              '[class*="st-key-hnbar"]', '[class*="st-key-hnfilt"]')   # their ::before is taken: the edge light only (.pbc draws its own)
FX_LIFT = (".kpi", ".mcard", ".story", ".news", ".lc", ".tdc", ".dcard", ".fgc", ".stat", ".ecard", ".shc", ".secgrid .sc", ".sprow", ".hrow",
           ".evt", ".prof .it", ".plan .p", ".mx .m", ".pbph", ".pbkd", ".pbmode", ".lr", ".opos .o", ".perfrow .pc2", ".sigs .sg", ".srcc",
           ".cal .d", ".czn", ".aic", ".mst", '[data-testid="stMetric"]')
_fx = ",".join(FX_CARDS)
_lift = ",".join(FX_LIFT)
_ring = f":is({_fx}):not({','.join(FX_NO_RING)})"
_glow = f":is({_fx}):not({','.join(FX_NO_GLOW)})"
FX_CSS = f"""<style>
:is({_fx}) {{ position:relative; isolation:isolate; transition: transform .22s cubic-bezier(.2,.8,.2,1), border-color .22s, box-shadow .22s; }}
/* the edge light: a 1px ring that shows only near the pointer */
{_ring}::after {{ content:""; position:absolute; inset:0; border-radius:inherit; pointer-events:none; z-index:3; padding:1px;
  background: radial-gradient(240px circle at var(--mx,50%) var(--my,50%), rgba(196,181,253,.95), rgba(121,184,244,.45) 38%, transparent 62%);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor;
  mask: linear-gradient(#000 0 0) content-box exclude, linear-gradient(#000 0 0);
  opacity:0; transition: opacity .3s ease; }}
/* the spotlight inside the card: over its background, under its text (each card is its own stacking layer) */
{_glow}::before {{ content:""; position:absolute; inset:0; border-radius:inherit; pointer-events:none; z-index:-1;
  background: radial-gradient(420px circle at var(--mx,50%) var(--my,50%), rgba(123,69,240,.16), rgba(7,122,199,.06) 40%, transparent 65%);
  opacity:0; transition: opacity .3s ease; }}
.fx-on::after, .fx-on::before {{ opacity:1 !important; }}
.fx-on {{ border-color: rgba(196,181,253,.28) !important; }}
/* lift and press */
:is({_lift}).fx-on {{ transform: translateY(-3px); box-shadow: 0 14px 30px -12px rgba(0,0,0,.7), 0 0 0 1px rgba(123,69,240,.12); }}
:is({_lift}).fx-on:active {{ transform: translateY(-1px) scale(.99); }}
/* the logo takes you home (FX_JS presses the hidden button) */
[data-testid="stLogo"], img.stLogo, [data-testid="stLogoLink"], [data-testid="stSidebarHeader"] img, [data-testid="stHeaderLogo"] img {{ cursor:pointer; }}
.st-key-logohome, .st-key-lmsync {{ position:absolute !important; width:1px !important; height:1px !important; overflow:hidden !important; opacity:0 !important;
  pointer-events:none !important; margin:0 !important; }}
/* the invisible frame that runs the script takes no room */
[data-testid="stElementContainer"]:has(iframe[height="0"]), .element-container:has(iframe[height="0"]) {{ position:absolute !important; width:0 !important;
  height:0 !important; overflow:hidden !important; margin:0 !important; padding:0 !important; }}
@media (prefers-reduced-motion: reduce) {{ :is({_lift}).fx-on {{ transform:none; }} }}
@media (hover: none) {{ {_ring}::after, {_glow}::before {{ display:none; }} }}
</style>"""
FX_JS = """<script>
(function () {
  var w = window.parent, d = w.document;
  var VER = '__VER__', KEY = '__alturaifiCards';
  var OLD = w[KEY + 'Frame'];                      // the frame that started the running copy: if Streamlit has re-created it,
  if (w[KEY] === VER && OLD && OLD.isConnected) return;   // that copy's listeners died with it and this one takes over
  if (typeof w[KEY + 'Off'] === 'function') { try { w[KEY + 'Off'](); } catch (e) {} }   // an older one stops first
  w[KEY] = VER;
  w[KEY + 'Frame'] = window.frameElement;
  var offs = [];
  w[KEY + 'Off'] = function () { offs.forEach(function (f) { try { f(); } catch (e) {} }); offs = []; };
  function on(t, ev, fn, o) { t.addEventListener(ev, fn, o); offs.push(function () { t.removeEventListener(ev, fn, o); }); }
  function every(fn, ms) { var id = w.setInterval(fn, ms); offs.push(function () { w.clearInterval(id); }); }
  var SEL = __SEL__;
  var cur = null, raf = 0, x = 0, y = 0;
  function set(el) {
    if (el === cur) return;
    if (cur) cur.classList.remove('fx-on');
    cur = el;
    if (el) el.classList.add('fx-on');
  }
  function pick() {
    raf = 0;
    var el = null, stack = d.elementsFromPoint(x, y);
    for (var i = 0; i < stack.length; i++) { var n = stack[i]; if (n.matches && n.matches(SEL)) { el = n; break; } }
    set(el);
    if (el) {
      var r = el.getBoundingClientRect();
      el.style.setProperty('--mx', (x - r.left) + 'px');
      el.style.setProperty('--my', (y - r.top) + 'px');
    }
  }
  on(d, 'pointermove', function (e) {
    if (e.pointerType && e.pointerType !== 'mouse') return;
    x = e.clientX; y = e.clientY;
    if (!raf) raf = w.requestAnimationFrame(pick);
  }, {passive: true});
  on(d.documentElement, 'mouseleave', function () { set(null); });
  on(w, 'scroll', function () { if (cur && !raf) raf = w.requestAnimationFrame(pick); }, {passive: true, capture: true});
  // top menus: choosing a page (or a language) closes the menu at once. Hover and keyboard focus would keep it open over the
  // page that is loading, so the flag on <html> forces it shut until a menu button is hovered or pressed again.
  var ROOT = d.documentElement, MENU_ITEM = '[class*="st-key-navdd_"] a, .st-key-langdd button, .st-key-langdd [class*="st-key-langopt_"]';
  ROOT.removeAttribute('data-menu-closed');        // a flag left by a copy of this script that has stopped
  on(d, 'click', function (e) {
    var t = e.target;
    if (!t || !t.closest || !t.closest(MENU_ITEM)) return;
    ROOT.setAttribute('data-menu-closed', '1');
    var a = d.activeElement;
    if (a && a.blur && a.closest && a.closest('[class*="st-key-navdd_"], .st-key-langdd')) a.blur();
  }, true);
  function reopen(e) {
    if (!ROOT.hasAttribute('data-menu-closed')) return;
    var t = e.target;
    if (t && t.closest && t.closest('.navbtn, .langbtn')) ROOT.removeAttribute('data-menu-closed');
  }
  on(d, 'pointerdown', reopen, true);
  on(d, 'pointerover', function (e) { if (!e.pointerType || e.pointerType === 'mouse') reopen(e); }, true);
})();
(function () {                                   // the landing: parallax, spotlight, typing line, reveals, tilting cards
  var w = window.parent, d = w.document, de = d.documentElement;
  var VER = '__VER__', KEY = '__alturaifiLanding';
  var OLD = w[KEY + 'Frame'];                      // the frame that started the running copy: if Streamlit has re-created it,
  if (w[KEY] === VER && OLD && OLD.isConnected) return;   // that copy's listeners died with it and this one takes over
  if (typeof w[KEY + 'Off'] === 'function') { try { w[KEY + 'Off'](); } catch (e) {} }   // an older one stops first
  w[KEY] = VER;
  w[KEY + 'Frame'] = window.frameElement;
  var offs = [];
  w[KEY + 'Off'] = function () { offs.forEach(function (f) { try { f(); } catch (e) {} }); offs = []; };
  function on(t, ev, fn, o) { t.addEventListener(ev, fn, o); offs.push(function () { t.removeEventListener(ev, fn, o); }); }
  function every(fn, ms) { var id = w.setInterval(fn, ms); offs.push(function () { w.clearInterval(id); }); }
  de.classList.add('ix-js');
  var raf = 0, x = 0, y = 0, tilt = null;
  function frame() {
    raf = 0;
    var ix = d.querySelector('.ix');
    if (ix) {
      var r = ix.getBoundingClientRect();
      if (y >= r.top && y <= r.bottom) {
        ix.style.setProperty('--px', ((x / w.innerWidth) * 2 - 1).toFixed(3));
        ix.style.setProperty('--py', (((y - r.top) / r.height) * 2 - 1).toFixed(3));
      }
    }
    var el = null, stack = d.elementsFromPoint(x, y);
    for (var i = 0; i < stack.length; i++) { if (stack[i].matches && stack[i].matches('.ixc, .ixm')) { el = stack[i]; break; } }
    if (tilt && tilt !== el) { tilt.classList.remove('tilt'); tilt.style.setProperty('--tx', 0); tilt.style.setProperty('--ty', 0); }
    tilt = el;
    if (el) {
      var b = el.getBoundingClientRect();
      el.classList.add('tilt');
      el.style.setProperty('--tx', (((x - b.left) / b.width) * 2 - 1).toFixed(3));
      el.style.setProperty('--ty', (((y - b.top) / b.height) * 2 - 1).toFixed(3));
      el.style.setProperty('--gx', (x - b.left) + 'px'); el.style.setProperty('--gy', (y - b.top) + 'px');
    }
  }
  on(d, 'pointermove', function (e) {
    if (e.pointerType && e.pointerType !== 'mouse') return;
    x = e.clientX; y = e.clientY;
    if (!raf && d.querySelector('.ixp')) raf = w.requestAnimationFrame(frame);
  }, {passive: true});
  // the top bar gets a light glass once the page has scrolled
  on(d, 'scroll', function (e) {
    var t = e.target, page = d.querySelector('.ixp');
    if (!page) return;
    if (t !== d && t !== de && !(t.contains && t.contains(page))) return;       // only the page's own scrolling
    var top = (t === d || t === de) ? (w.scrollY || 0) : (t.scrollTop || 0);
    de.classList.toggle('ix-scrolled', top > 40);
    past();
  }, {passive: true, capture: true});
  // "Get started" comes in once the first screen is scrolled past
  function past() {
    var ix = d.querySelector('.ix');
    de.classList.toggle('ix-past', !!ix && ix.getBoundingClientRect().bottom < w.innerHeight * .55);
  }
  // "Get started" and the logo: back to the top of the page
  var leaving = 0;
  function toTop() {
    var m = d.querySelector('[data-testid="stMain"]') || d.querySelector('section.stMain') || d.querySelector('[data-testid="stAppViewContainer"]');
    if (m && m.scrollTo) m.scrollTo({top: 0}); w.scrollTo(0, 0); de.classList.remove('ix-scrolled');
  }
  on(d, 'click', function (e) {
    var t = e.target;
    if (t && t.closest && t.closest('.st-key-introgo button')) {
      // "Get started": the landing fades out at once, the jump back to the top happens while it is hidden, and the main
      // page then opens at its top (no visible scroll up the landing first)
      de.classList.add('ix-leaving'); leaving = Date.now();
      w.setTimeout(toTop, 170); w.setTimeout(toTop, 600); w.setTimeout(toTop, 1300);
    } else if (t && t.closest && t.closest('.st-key-logohome button')) { toTop(); w.setTimeout(toTop, 450); w.setTimeout(toTop, 1200); }
    if (t && t.closest && t.closest('.ix-scroll')) {                       // "Scroll down": to the first section
      var nx = d.querySelector('.ixp .ixs');
      if (nx) nx.scrollIntoView({behavior: 'smooth', block: 'start'});
    }
  }, true);
  every(function () {
    // reveals: a section shows as it comes into view
    var rv = d.querySelectorAll('.rv:not(.in)');
    for (var i = 0; i < rv.length; i++) { if (rv[i].getBoundingClientRect().top < w.innerHeight * .9) rv[i].classList.add('in'); }
    if (!d.querySelector('.ixp')) { de.classList.remove('ix-scrolled'); de.classList.remove('ix-past'); de.classList.remove('ix-leaving'); } else past();
    if (leaving && d.querySelector('.ixp') && Date.now() - leaving > 8000) { de.classList.remove('ix-leaving'); leaving = 0; }   // it did not leave
    var pg0 = d.querySelector('.ixp');
    if (pg0) {
      var pr = pg0.getBoundingClientRect();
      de.classList.toggle('ix-scrolled', pr.top < -40);                   // measured, so the top bar never stays dark at the top
      if (pr.top > .5 && pr.top < 200) {                                  // the landing starts at the very top, under the see-through bar
        pg0.style.marginTop = (parseFloat(w.getComputedStyle(pg0).marginTop) - pr.top) + 'px';
      }
      // phones: the menu card sits clear under the top line (Streamlit's bar with the logo), a little gap between them,
      // whatever comes before it on the page; measured at the top of the page only
      var nav = d.querySelector('.st-key-topnav'), hd = d.querySelector('header[data-testid="stHeader"]');
      var mm = d.querySelector('[data-testid="stMain"]') || d.querySelector('section.stMain');
      var atTop = ((mm && mm.scrollTop) || 0) < 2 && (w.scrollY || 0) < 2;
      if (nav && hd && w.innerWidth < 1024 && atTop) {
        var gapNow = nav.getBoundingClientRect().top - hd.getBoundingClientRect().bottom, want = 14;
        if (Math.abs(gapNow - want) > 1) {
          var mt = parseFloat(w.getComputedStyle(nav).marginTop) || 0;
          nav.style.setProperty('margin-top', Math.max(0, mt + want - gapNow).toFixed(1) + 'px', 'important');
          nav.dataset.ixmt = '1';
        }
        // ... and the landing's words start under the card, never behind it (measured from where they would be without it)
        var ctr = pg0.querySelector('.ix-center');
        if (ctr) {
          var drop = parseFloat(pg0.style.getPropertyValue('--ixdrop')) || 0;
          var need = Math.max(0, Math.round(nav.getBoundingClientRect().bottom + 22 - (ctr.getBoundingClientRect().top - drop)));
          if (Math.abs(need - drop) > 1) pg0.style.setProperty('--ixdrop', need + 'px');
        }
      } else if (w.innerWidth >= 1024 && pg0.style.getPropertyValue('--ixdrop')) {
        pg0.style.removeProperty('--ixdrop');
      }
    } else {
      // another page: the menu card is the same element as on the landing, so the landing's gap must not follow it
      var nv = d.querySelector('.st-key-topnav');
      if (nv && nv.dataset.ixmt) { nv.style.removeProperty('margin-top'); delete nv.dataset.ixmt; }
    }
  }, 180);
})();
(function () {                                   // the landing's sculpture: a cut amethyst, drawn with WebGL
  var w = window.parent, d = w.document;
  var VER = '__VER__', KEY = '__alturaifiSculpture';
  var OLD = w[KEY + 'Frame'];                      // the frame that started the running copy: if Streamlit has re-created it,
  if (w[KEY] === VER && OLD && OLD.isConnected) return;   // that copy's listeners died with it and this one takes over
  if (typeof w[KEY + 'Off'] === 'function') { try { w[KEY + 'Off'](); } catch (e) {} }   // an older one stops first
  w[KEY] = VER;
  w[KEY + 'Frame'] = window.frameElement;
  var offs = [];
  w[KEY + 'Off'] = function () { offs.forEach(function (f) { try { f(); } catch (e) {} }); offs = []; };
  function on(t, ev, fn, o) { t.addEventListener(ev, fn, o); offs.push(function () { t.removeEventListener(ev, fn, o); }); }
  function every(fn, ms) { var id = w.setInterval(fn, ms); offs.push(function () { w.clearInterval(id); }); }
  function mat4() { return new Float32Array(16); }
  function persp(fov, asp, n, f) { var m = mat4(), t = 1 / Math.tan(fov / 2); m[0] = t / asp; m[5] = t; m[10] = (f + n) / (n - f); m[11] = -1; m[14] = 2 * f * n / (n - f); return m; }
  function mul(a, b) { var o = mat4(); for (var i = 0; i < 4; i++) for (var j = 0; j < 4; j++) { var s = 0; for (var k = 0; k < 4; k++) s += a[k * 4 + j] * b[i * 4 + k]; o[i * 4 + j] = s; } return o; }
  function rot(ax, ay, az) {
    var cx = Math.cos(ax), sx = Math.sin(ax), cy = Math.cos(ay), sy = Math.sin(ay), cz = Math.cos(az), sz = Math.sin(az), m = mat4();
    m[0] = cy * cz; m[1] = cy * sz; m[2] = -sy;
    m[4] = sx * sy * cz - cx * sz; m[5] = sx * sy * sz + cx * cz; m[6] = sx * cy;
    m[8] = cx * sy * cz + sx * sz; m[9] = cx * sy * sz - sx * cz; m[10] = cx * cy; m[15] = 1; return m;
  }
  function trans(x, y, z) { var m = mat4(); m[0] = m[5] = m[10] = m[15] = 1; m[12] = x; m[13] = y; m[14] = z; return m; }
  // a black sculpture of cut panels (after Letter's render): the hull of points scattered over a wide, low dome - big
  // irregular flat facets with crisp creases, a rounded crown, a flat base. Each crease knows how sharp it is.
  function geometry() {
    var seed = 29; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
    function norm(v) { var l = Math.hypot(v[0], v[1], v[2]); return [v[0] / l, v[1] / l, v[2] / l]; }
    function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
    function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
    function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
    var Q = [];
    for (var i = 0; i < 64; i++) {
      var u = 2 * rnd() - 1, a = rnd() * 6.2832, q = Math.sqrt(1 - u * u), r = .9 + rnd() * .14, y = u;
      if (y < -.3) y = -.3 - (y + .3) * .15;                               // pressed flat underneath
      Q.push([q * Math.cos(a) * r * 1.42, y * r * 1.08, q * Math.sin(a) * r * 1.12]);
    }
    var F = [], n = Q.length;
    for (var i = 0; i < n; i++) for (var j = i + 1; j < n; j++) for (var k = j + 1; k < n; k++) {
      var nr = cross(sub(Q[j], Q[i]), sub(Q[k], Q[i]));
      if (dot(nr, nr) < 1e-10) continue;
      var pos = 0, neg = 0;
      for (var l = 0; l < n && !(pos && neg); l++) { if (l === i || l === j || l === k) continue; var sd = dot(nr, sub(Q[l], Q[i])); if (sd > 1e-9) pos++; else if (sd < -1e-9) neg++; }
      if (pos && neg) continue;
      F.push(pos ? [i, k, j] : [i, j, k]);                                  // corners in order, the normal outwards
    }
    var FN = F.map(function (f) { return norm(cross(sub(Q[f[1]], Q[f[0]]), sub(Q[f[2]], Q[f[0]]))); });
    var EDGE = {};
    F.forEach(function (f, i) { for (var j = 0; j < 3; j++) { var a = f[(j + 1) % 3], b = f[(j + 2) % 3], key = a < b ? a + '_' + b : b + '_' + a; (EDGE[key] = EDGE[key] || []).push(i); } });
    var P = [], N = [], B = [], M = [];
    F.forEach(function (f, i) {
      var m = [0, 0, 0];
      for (var j = 0; j < 3; j++) {
        var a = f[(j + 1) % 3], b = f[(j + 2) % 3], key = a < b ? a + '_' + b : b + '_' + a, tris = EDGE[key];
        var other = tris[0] === i ? tris[1] : tris[0];
        if (other !== undefined) m[j] = Math.max(.25, Math.min(1, (1 - dot(FN[i], FN[other])) / .35));
      }
      f.forEach(function (k, j) { var p = Q[k], nn = FN[i]; P.push(p[0], p[1], p[2]); N.push(nn[0], nn[1], nn[2]); B.push(j === 0 ? 1 : 0, j === 1 ? 1 : 0, j === 2 ? 1 : 0); M.push(m[0], m[1], m[2]); });
    });
    return {p: new Float32Array(P), n: new Float32Array(N), b: new Float32Array(B), m: new Float32Array(M), count: P.length / 3};
  }
  var VS = 'attribute vec3 p;attribute vec3 n;attribute vec3 b;attribute vec3 m;uniform mat4 mvp;uniform mat4 model;uniform mat3 nm;varying vec3 vN;varying vec3 vP;varying vec3 vB;varying vec3 vM;varying vec3 vO;' +
    'void main(){vN=nm*n;vO=n;vB=b;vM=m;vP=(model*vec4(p,1.)).xyz;gl_Position=mvp*vec4(p,1.);}';
  // a cut amethyst in a dark studio: the stone's own violet, each facet a little lighter or deeper (as light travels a
  // different way through a real cut gem), lighter where it faces the eye and deeper towards the edges; on it the same shine
  // as before - two softboxes that flash across the panels, a white key light, an orange and a blue glint, a cool rim, and
  // the panel edges catching the light
  var FS = 'precision highp float;varying vec3 vN;varying vec3 vP;varying vec3 vB;varying vec3 vM;varying vec3 vO;uniform vec3 eye;uniform float t;' +
    'void main(){vec3 N=normalize(vN);vec3 V=normalize(eye-vP);float ndv=max(dot(N,V),0.);float fr=pow(1.-ndv,4.);vec3 R=reflect(-V,N);' +
    'vec3 q=floor(normalize(vO)*40.+.5);float h=fract(sin(dot(q,vec3(12.9898,78.233,37.719)))*43758.5453);' +
    'vec3 gem=mix(vec3(.17,.035,.40),vec3(.60,.26,.98),h*h);float lt=pow(max(dot(N,normalize(vec3(cos(t*.4)*1.8,1.2,1.6))),0.),2.);' +
    'vec3 body=mix(vec3(.028,.004,.075),gem,.12+.88*pow(ndv,1.1))*(.48+.62*h)+gem*lt*.22;' +
    'vec3 B1=normalize(vec3(-.75+.25*sin(t*.3),.45,.55));vec3 B2=normalize(vec3(.85,.05+.15*cos(t*.25),.5));' +
    'float box=smoothstep(.86,.985,dot(R,B1))*2.2+smoothstep(.9,.99,dot(R,B2))*1.5;float sky=pow(max(R.y,0.),4.)*.3;' +
    'vec3 env=vec3(.006,.006,.009)+box*vec3(1.)+sky*vec3(.7,.7,.85);' +
    'vec3 K=normalize(vec3(cos(t*.4)*1.8,1.2,1.6));vec3 O=normalize(vec3(1.6,-.5,sin(t*.33)*1.4+.6));vec3 C=normalize(vec3(-1.8,-.2,cos(t*.29)*1.2+.4));' +
    'float k=pow(max(dot(N,normalize(K+V)),0.),420.);float o=pow(max(dot(N,normalize(O+V)),0.),1400.);float c=pow(max(dot(N,normalize(C+V)),0.),1200.);' +
    'vec3 ed=(1.-smoothstep(vec3(0.),vec3(.022),vB))*vM;float edge=max(max(ed.x,ed.y),ed.z);' +
    'float lit=pow(max(dot(N,normalize(K+V)),0.),10.)*4.+pow(max(dot(N,normalize(B1+V)),0.),14.)*3.+pow(fr,1.3)*2.4;' +
    'vec3 col=body+env*(.3+.7*fr)+k*vec3(1.)*4.6+o*vec3(1.,.62,.25)*3.6+c*vec3(.35,.65,1.)*3.6+edge*lit*vec3(.92,.93,1.)+fr*vec3(.35,.4,.55)*.35;' +
    'col=col/(1.+col*.45);gl_FragColor=vec4(pow(col,vec3(.95)),1.);}';
  function mount(host) {
    var cv = d.createElement('canvas'); cv.className = 'ix-gl'; host.appendChild(cv);
    var gl = cv.getContext('webgl', {antialias: true, alpha: true, premultipliedAlpha: true});
    if (!gl) { cv.remove(); return; }
    function sh(type, src) { var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return gl.getShaderParameter(s, gl.COMPILE_STATUS) ? s : null; }
    var vs = sh(gl.VERTEX_SHADER, VS), fs = sh(gl.FRAGMENT_SHADER, FS);
    if (!vs || !fs) { cv.remove(); return; }
    var pr = gl.createProgram(); gl.attachShader(pr, vs); gl.attachShader(pr, fs); gl.linkProgram(pr);
    if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) { cv.remove(); return; }
    gl.useProgram(pr);
    var g = geometry();
    function buf(data, name) { var b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
      var loc = gl.getAttribLocation(pr, name); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 3, gl.FLOAT, false, 0, 0); }
    buf(g.p, 'p'); buf(g.n, 'n'); buf(g.b, 'b'); buf(g.m, 'm');
    var U = {}; ['mvp', 'model', 'nm', 'eye', 't'].forEach(function (k) { U[k] = gl.getUniformLocation(pr, k); });
    gl.enable(gl.DEPTH_TEST); gl.clearColor(0, 0, 0, 0);
    host.classList.add('gl-on');
    var t0 = performance.now(), mx = 0, my = 0;
    function frame(now) {
      if (!cv.isConnected) { var ext = gl.getExtension('WEBGL_lose_context'); if (ext) ext.loseContext(); return; }
      w.requestAnimationFrame(frame);
      var r = cv.getBoundingClientRect();
      if (r.bottom < 0 || r.top > w.innerHeight || r.width < 2) return;              // off screen: no work
      var dpr = Math.min(w.devicePixelRatio || 1, 2), W = Math.round(r.width * dpr), H = Math.round(r.height * dpr);
      if (cv.width !== W || cv.height !== H) { cv.width = W; cv.height = H; }
      gl.viewport(0, 0, W, H); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      var t = (now - t0) / 1000, ix = d.querySelector('.ix');
      if (ix) { mx += ((parseFloat(ix.style.getPropertyValue('--px')) || 0) - mx) * .05; my += ((parseFloat(ix.style.getPropertyValue('--py')) || 0) - my) * .05; }
      var model = mul(trans(0, -.12, 0), rot(.26 + Math.sin(t * .27) * .06 + my * .12, -.5 + t * .16 + mx * .45, Math.sin(t * .19) * .05));
      var eye = [0, .15, 4.2], view = trans(-eye[0], -eye[1], -eye[2]);
      var proj = persp(.62, W / H, .1, 50), mvp = mul(proj, mul(view, model));
      var nm = new Float32Array([model[0], model[1], model[2], model[4], model[5], model[6], model[8], model[9], model[10]]);
      gl.uniformMatrix4fv(U.mvp, false, mvp); gl.uniformMatrix4fv(U.model, false, model); gl.uniformMatrix3fv(U.nm, false, nm);
      gl.uniform3fv(U.eye, eye); gl.uniform1f(U.t, t);
      gl.drawArrays(gl.TRIANGLES, 0, g.count);
    }
    w.requestAnimationFrame(frame);
  }
  every(function () {                     // the landing can appear at any rerun: give each new one its sculpture
    var hosts = d.querySelectorAll('.ix-sc:not(.gl-try)');
    for (var i = 0; i < hosts.length; i++) { hosts[i].classList.add('gl-try'); try { mount(hosts[i]); } catch (e) {} }
  }, 250);
})();
(function () {                                   // the logo opens the home page's first screen
  var w = window.parent, d = w.document;
  var VER = '__VER__', KEY = '__alturaifiLogoV';
  var OLD = w[KEY + 'Frame'];                      // the frame that started the running copy: if Streamlit has re-created it,
  if (w[KEY] === VER && OLD && OLD.isConnected) return;   // that copy's listeners died with it and this one takes over
  if (typeof w[KEY + 'Off'] === 'function') { try { w[KEY + 'Off'](); } catch (e) {} }   // an older one stops first
  w[KEY] = VER;
  w[KEY + 'Frame'] = window.frameElement;
  var offs = [];
  w[KEY + 'Off'] = function () { offs.forEach(function (f) { try { f(); } catch (e) {} }); offs = []; };
  function on(t, ev, fn, o) { t.addEventListener(ev, fn, o); offs.push(function () { t.removeEventListener(ev, fn, o); }); }
  function every(fn, ms) { var id = w.setInterval(fn, ms); offs.push(function () { w.clearInterval(id); }); }
  var LOGO = '[data-testid="stLogo"], img.stLogo, [data-testid="stLogoLink"], [data-testid="stSidebarHeader"] img, [data-testid="stHeaderLogo"]';
  on(d, 'click', function (e) {
    var t = e.target;
    if (!t || !t.closest || !t.closest(LOGO)) return;
    var b = d.querySelector('.st-key-logohome button');
    if (!b) return;
    e.preventDefault(); e.stopPropagation();
    b.click();
  }, true);
})();
(function () {                                   // the site's colours follow Streamlit's theme (⋮ → System / Light / Dark)
  var w = window.parent, d = w.document;
  var VER = '__VER__', KEY = '__alturaifiThemeV';
  var OLD = w[KEY + 'Frame'];                      // the frame that started the running copy: if Streamlit has re-created it,
  if (w[KEY] === VER && OLD && OLD.isConnected) return;   // that copy's listeners died with it and this one takes over
  if (typeof w[KEY + 'Off'] === 'function') { try { w[KEY + 'Off'](); } catch (e) {} }   // an older one stops first
  w[KEY] = VER;
  w[KEY + 'Frame'] = window.frameElement;
  var offs = [];
  w[KEY + 'Off'] = function () { offs.forEach(function (f) { try { f(); } catch (e) {} }); offs = []; };
  function every(fn, ms) { var id = w.setInterval(fn, ms); offs.push(function () { w.clearInterval(id); }); }
  // Streamlit paints the page body in the active theme's background; the server marks the theme it drew the page for.
  // When the two differ (the visitor just picked another look, or the first run could not know it yet), the hidden button
  // reruns the page once, so the server draws it again in the right look.
  var seen = '', tries = 0, last = 0;
  function check() {
    var m = (w.getComputedStyle(d.body).backgroundColor || '').match(/[\d.]+/g);
    if (!m || m.length < 3) return;
    var want = (0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]) / 255 > 0.5 ? 'light' : 'dark';
    if (want !== seen) { seen = want; tries = 0; }
    var a = d.querySelector('.css-anchor[data-th]');
    if (!a || a.getAttribute('data-th') === want || tries >= 3 || Date.now() - last < 2500) return;
    var b = d.querySelector('.st-key-lmsync button');
    if (!b) return;
    tries++; last = Date.now(); b.click();
  }
  every(check, 400); check();
})();
(function () {                                   // news pictures: a story photo that cannot load gives way to its topic photo
  var w = window.parent, d = w.document;
  var VER = '__VER__', KEY = '__alturaifiPicsV';
  var OLD = w[KEY + 'Frame'];                      // the frame that started the running copy: if Streamlit has re-created it,
  if (w[KEY] === VER && OLD && OLD.isConnected) return;   // that copy's listeners died with it and this one takes over
  if (typeof w[KEY + 'Off'] === 'function') { try { w[KEY + 'Off'](); } catch (e) {} }
  w[KEY] = VER;
  w[KEY + 'Frame'] = window.frameElement;
  var offs = [];
  w[KEY + 'Off'] = function () { offs.forEach(function (f) { try { f(); } catch (e) {} }); offs = []; };
  function swap(img) {
    var alt = img.getAttribute('data-alt');
    if (!alt) return;
    img.removeAttribute('data-alt');
    var c = img.getAttribute('data-altc');
    if (c && img.parentNode) img.parentNode.setAttribute('title', c);
    img.src = alt;
  }
  function onErr(e) { var t = e.target; if (t && t.tagName === 'IMG' && t.hasAttribute('data-alt')) swap(t); }
  d.addEventListener('error', onErr, true);
  offs.push(function () { d.removeEventListener('error', onErr, true); });
  function sweep() {                               // photos that failed before this ran
    var l = d.querySelectorAll('.nth img[data-alt]');
    for (var i = 0; i < l.length; i++) { if (l[i].complete && !l[i].naturalWidth) swap(l[i]); }
  }
  sweep();
  var id = w.setInterval(sweep, 2000);
  offs.push(function () { w.clearInterval(id); });
})();
(function () {                                   // every table: sort by any column, filter the long ones, the column under the pointer lights up
  var w = window.parent, d = w.document;
  var VER = '__VER__', KEY = '__alturaifiTablesV';
  var OLD = w[KEY + 'Frame'];                      // the frame that started the running copy: if Streamlit has re-created it,
  if (w[KEY] === VER && OLD && OLD.isConnected) return;   // that copy's listeners died with it and this one takes over
  if (typeof w[KEY + 'Off'] === 'function') { try { w[KEY + 'Off'](); } catch (e) {} }   // an older one stops first
  w[KEY] = VER;
  w[KEY + 'Frame'] = window.frameElement;
  var offs = [];
  w[KEY + 'Off'] = function () { offs.forEach(function (f) { try { f(); } catch (e) {} }); offs = []; };
  function on(t, ev, fn, o) { t.addEventListener(ev, fn, o); offs.push(function () { t.removeEventListener(ev, fn, o); }); }
  function every(fn, ms) { var id = w.setInterval(fn, ms); offs.push(function () { w.clearInterval(id); }); }
  var ROOT = '[data-testid="stMain"], [data-testid="stMainBlockContainer"], section.main';
  var MULT = {K: 1e3, M: 1e6, B: 1e9, T: 1e12};
  function ar() { var m = d.querySelector('[data-testid="stMainBlockContainer"], .block-container'); return !!m && w.getComputedStyle(m).direction === 'rtl'; }
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  function headRow(t) { return t.tHead && t.tHead.rows.length ? t.tHead.rows[t.tHead.rows.length - 1] : null; }
  // what a cell sorts by: a number when it reads as one ($1.2B, -3.4%, 2.1x, 1,250), a date, else its words; empty cells go last
  function key(cell) {
    var s = (cell ? cell.textContent : '').replace(/[\u2212\u2012\u2013]/g, '-').replace(/\s+/g, ' ').trim();
    if (!s || /^[-\u2014]+$/.test(s)) return null;
    var m = s.replace(/,/g, '').match(/^[^\d+\-.]{0,3}([+-]?)\$?(\d+(?:\.\d+)?)\s*([KMBT](?![a-z]))?/i);
    if (m) { var v = parseFloat(m[2]) * (MULT[(m[3] || '').toUpperCase()] || 1); return m[1] === '-' ? -v : v; }
    return s.toLowerCase();
  }
  function setup(t) {
    t.setAttribute('data-tx', '1');
    if (t.hasAttribute('data-nosort')) return;
    var hr = headRow(t), body = t.tBodies[0];
    if (!hr || !body || body.rows.length < 3) return;
    each(hr.cells, function (th) {
      if (!th.textContent.trim() || th.colSpan > 1) return;
      th.classList.add('tx-s'); th.tabIndex = 0; th.setAttribute('aria-sort', 'none');
      th.title = ar() ? 'رتّب حسب هذا العمود' : 'Sort by this column';
    });
    each(body.rows, function (r, i) { r.setAttribute('data-i', i); });
    if (body.rows.length >= 12) filter(t, body);
  }
  function filter(t, body) {
    var bar = d.createElement('div');
    bar.className = 'tx-tools';
    bar.innerHTML = '<label class="tx-q"><span class="ms">search</span><input type="search" autocomplete="off"></label><span class="tx-n"></span>';
    var inp = bar.querySelector('input'), n = bar.querySelector('.tx-n'), total = body.rows.length;
    inp.placeholder = ar() ? 'ابحث في الجدول…' : 'Filter the table…';
    function count(k) { n.textContent = ar() ? (k + ' من ' + total) : (k + ' of ' + total); }
    count(total);
    inp.addEventListener('input', function () {
      var q = inp.value.trim().toLowerCase(), k = 0;
      each(body.rows, function (r) { var hit = !q || r.textContent.toLowerCase().indexOf(q) >= 0; r.classList.toggle('tx-hide', !hit); if (hit) k++; });
      count(k);
    });
    var box = t.closest('.xtp');
    var at = box ? box.querySelector('.xtsc') : (t.parentElement && t.parentElement.querySelector(':scope > table') === t
             && /wrap|scroll|sc\b/.test(t.parentElement.className) ? t.parentElement : t);
    if (at && at.parentNode) at.parentNode.insertBefore(bar, at);
  }
  // first click: numbers biggest first, words A to Z; second click the other way; third click back to the original order
  function sortBy(th) {
    var t = th.closest('table'), body = t.tBodies[0], idx = th.cellIndex, hr = headRow(t);
    var st = th.getAttribute('aria-sort'), rows = Array.prototype.slice.call(body.rows);
    var fixed = rows.filter(function (r) { return r.classList.contains('ai') || r.classList.contains('tx-fix'); });
    var free = rows.filter(function (r) { return fixed.indexOf(r) < 0; });
    var items = free.map(function (r) { return {r: r, k: key(r.cells[idx]), i: +r.getAttribute('data-i')}; });
    var known = items.filter(function (o) { return o.k !== null; });
    var numeric = known.length && known.filter(function (o) { return typeof o.k === 'number'; }).length >= .7 * known.length;
    var next = st === 'descending' ? (numeric ? 'ascending' : 'none') : st === 'ascending' ? (numeric ? 'none' : 'descending')
             : (numeric ? 'descending' : 'ascending');
    each(hr.cells, function (c) { if (c.classList.contains('tx-s')) c.setAttribute('aria-sort', 'none'); });
    th.setAttribute('aria-sort', next);
    if (next === 'none') items.sort(function (a, b) { return a.i - b.i; });
    else items.sort(function (a, b) {
      var x = a.k, y = b.k, c;
      if (x === null || y === null) return x === y ? a.i - b.i : (x === null ? 1 : -1);
      if (typeof x === 'number' && typeof y === 'number') c = x - y;
      else if (typeof x === 'number') c = -1;
      else if (typeof y === 'number') c = 1;
      else c = String(x).localeCompare(String(y), undefined, {numeric: true, sensitivity: 'base'});
      return (next === 'descending' ? -c : c) || a.i - b.i;
    });
    var f = d.createDocumentFragment();
    items.forEach(function (o) { f.appendChild(o.r); });
    fixed.sort(function (a, b) { return a.getAttribute('data-i') - b.getAttribute('data-i'); }).forEach(function (r) { f.appendChild(r); });
    body.appendChild(f);
  }
  function scan() {
    var roots = d.querySelectorAll(ROOT);
    each(roots, function (root) { each(root.querySelectorAll('table:not([data-tx])'), setup); });
  }
  on(d, 'click', function (e) {
    var t = e.target;
    if (!t || !t.closest || t.closest('.gq')) return;
    var th = t.closest('th.tx-s');
    if (th) { sortBy(th); return; }
    var td = t.closest('table[data-tx] tbody td');
    if (td && !t.closest('a, button, input, label, summary')) td.parentNode.classList.toggle('tx-pin');   // a row stays lit until clicked again
  }, true);
  on(d, 'keydown', function (e) {
    var th = e.target && e.target.closest && !e.target.closest('.gq') && e.target.closest('th.tx-s');
    if (th && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); sortBy(th); }
  }, true);
  var hc = null;
  on(d, 'mouseover', function (e) {
    var td = e.target && e.target.closest && e.target.closest('table[data-tx] td');
    var th = null;
    if (td) { var hr = headRow(td.closest('table')); th = hr && hr.cells[td.cellIndex] || null; }
    if (th === hc) return;
    if (hc) hc.classList.remove('tx-hc');
    hc = th;
    if (hc) hc.classList.add('tx-hc');
  }, {passive: true});
  every(scan, 700); scan();
})();
(function () {                                   // the "?" next to every trading term: pressed, it explains the term in the page's language
  var w = window.parent, d = w.document;
  var VER = '__VER__', KEY = '__alturaifiTermsV';
  var OLD = w[KEY + 'Frame'];                      // the frame that started the running copy: if Streamlit has re-created it,
  if (w[KEY] === VER && OLD && OLD.isConnected) return;   // that copy's listeners died with it and this one takes over
  if (typeof w[KEY + 'Off'] === 'function') { try { w[KEY + 'Off'](); } catch (e) {} }   // an older one stops first
  w[KEY] = VER;
  w[KEY + 'Frame'] = window.frameElement;
  var offs = [];
  w[KEY + 'Off'] = function () { offs.forEach(function (f) { try { f(); } catch (e) {} }); offs = []; close(); };
  function on(t, ev, fn, o) { t.addEventListener(ev, fn, o); offs.push(function () { t.removeEventListener(ev, fn, o); }); }
  function every(fn, ms) { var id = w.setInterval(fn, ms); offs.push(function () { w.clearInterval(id); }); }
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  var G = __GLOSS__, T = G.t, P = [], PK = {}, QCI = null, QCS = null;
  try {
    G.p.forEach(function (x) {
      var o = {k: x[0], ci: x[1] ? new RegExp(x[1], 'iu') : null, cs: x[2] ? new RegExp(x[2], 'u') : null,
               sci: x[3] ? new RegExp(x[3], 'iu') : null, scs: x[4] ? new RegExp(x[4], 'u') : null};
      P.push(o); PK[o.k] = o;
    });
    QCI = new RegExp(G.p.map(function (x) { return x[1]; }).filter(Boolean).join('|'), 'iu');
    QCS = new RegExp(G.p.map(function (x) { return x[2]; }).filter(Boolean).join('|'), 'u');
  } catch (e) { P = null; }                         // a browser too old for these patterns: the "?" the server placed still work
  function ar() { var m = d.querySelector('[data-testid="stMainBlockContainer"], .block-container'); return !!m && w.getComputedStyle(m).direction === 'rtl'; }
  function esc(x) { return String(x).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }
  // ---- the box with the explanation, next to the "?" that was pressed
  var pop = null, anchor = null;
  function close() {
    if (pop) { pop.remove(); pop = null; }
    if (anchor) { anchor.classList.remove('on'); anchor = null; }
  }
  function place() {
    if (!pop || !anchor) return;
    if (!anchor.isConnected) { close(); return; }
    var r = anchor.getBoundingClientRect(), vw = w.innerWidth, vh = w.innerHeight, pw = pop.offsetWidth, ph = pop.offsetHeight;
    var left = Math.min(Math.max(12, r.left + r.width / 2 - pw / 2), Math.max(12, vw - pw - 12));
    var below = r.bottom + 10, top = below;
    if (below + ph > vh - 12 && r.top - ph - 10 >= 12) top = r.top - ph - 10;
    top = Math.max(12, Math.min(top, vh - ph - 12));
    pop.classList.toggle('up', top < r.top);
    pop.style.left = left + 'px'; pop.style.top = top + 'px';
    pop.style.setProperty('--ax', Math.max(18, Math.min(pw - 18, r.left + r.width / 2 - left)) + 'px');
  }
  function open(el) {
    var k = el.getAttribute('data-g'), t = T[k];
    if (!t) return;
    if (anchor === el) { close(); return; }
    close();
    var a = ar();
    var body = a ? '<div class="gqb" dir="rtl" lang="ar"><b>' + esc(t[1]) + '</b><p>' + esc(t[3]) + '</p></div>'
                 : '<div class="gqb" dir="ltr" lang="en"><b>' + esc(t[0]) + '</b><p>' + esc(t[2]) + '</p></div>';   // the page's language only
    pop = d.createElement('div');
    pop.className = 'gqpop'; pop.setAttribute('role', 'dialog'); pop.setAttribute('aria-label', a ? t[1] : t[0]); pop.dir = a ? 'rtl' : 'ltr';
    pop.innerHTML = '<button type="button" class="gqx" aria-label="' + (a ? '\u0625\u063a\u0644\u0627\u0642' : 'Close') + '">\u00d7</button>' + body;
    d.body.appendChild(pop);
    anchor = el; el.classList.add('on');
    place();
  }
  function gqAt(e) {
    var t = e.target, el = t && t.closest ? t.closest('.gq') : null;
    if (el || typeof e.clientX !== 'number' || (!e.clientX && !e.clientY)) return el;
    var stack = d.elementsFromPoint(e.clientX, e.clientY);          // a "?" under a card's invisible button
    for (var i = 0; i < stack.length && i < 10; i++) if (stack[i].classList && stack[i].classList.contains('gq')) return stack[i];
    return null;
  }
  on(d, 'click', function (e) {
    var t = e.target;
    if (pop && t && t.closest && t.closest('.gqpop')) { if (t.closest('.gqx')) close(); return; }
    var el = gqAt(e);
    if (el) { e.preventDefault(); e.stopPropagation(); open(el); return; }
    if (pop) close();
  }, true);
  on(d, 'keydown', function (e) {
    if (e.key === 'Escape' && pop) { close(); return; }
    var el = e.target && e.target.closest && e.target.closest('.gq');
    if (el && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); e.stopPropagation(); open(el); }
  }, true);
  on(w, 'scroll', function () { if (pop) place(); }, {passive: true, capture: true});
  on(w, 'resize', function () { if (pop) place(); });
  // ---- the "?" for the text Streamlit draws itself (field labels, captions, plain text): the server marks the site's own HTML
  if (!P) return;
  var BOX = '[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"]';
  // icons are words drawn by the icon font ("candlestick_chart"): a "?" inside one breaks it into letters; tab labels stay plain too
  var ICONS = '[data-testid="stIconMaterial"], [role="img"], [translate="no"]';
  var SKIP = 'button, [role="button"]:not(.gq), script, style, svg, textarea, select, option, code, pre, kbd, .gq, .ms, .material-symbols-rounded, '
           + '.st-key-topnav, .ixp, .st-key-introgo, .tape, .navbtn, .langbtn, .lopt, [class*="st-key-alturaifi_ai"], [class*="ai-"], .tx-tools, '
           + '[data-baseweb="select"], [data-baseweb="tab"], [data-baseweb="popover"], [role="listbox"], [role="option"], [data-testid="stPageLink"], '
           + '[aria-hidden="true"], [data-testid="stTooltipIcon"], .lg, .lgo, .nth, .gqpop, [data-nogq], .as, .tk, .tkc, .lnk, .co, .mchip, .mvr, .wlr, .hm, '
           + '.nogq, .tt, .mt, .meta, .kw, .kws, a.t, .ncov, .tkt, '
           + ICONS + ', [role="tab"], [data-testid="stTab"], [role="tablist"]';
  var WORD = /[A-Za-z0-9\u0621-\u064A]/, AR = /[\u0600-\u06FF]/;
  var seen = new WeakMap();
  // news headlines and summaries are everyday language ("strikes on Iran"): there only the plainly financial words count
  var NEWS = '.news, .story, .nie-card, .nb, .bstory, .sum';
  function find(x, t, strict) {
    var a = strict ? x.sci : x.ci, b = strict ? x.scs : x.cs;
    var m = a && a.exec(t), n = b && b.exec(t);
    return m && n ? (n.index < m.index ? n : m) : (m || n);
  }
  function mk(m) {
    var g = d.createElement('span');
    g.className = 'gq cl'; g.setAttribute('role', 'button'); g.tabIndex = 0; g.setAttribute('data-g', m.k); g.textContent = '?';
    var t = T[m.k] || ['', ''];
    g.setAttribute('aria-label', m.a ? '\u0645\u0627 \u0645\u0639\u0646\u0649 ' + t[1] + '\u061f' : 'What does ' + t[0] + ' mean?');
    return g;
  }
  function scanBox(box) {
    var txt = box.textContent;
    if (seen.get(box) === txt) return;
    each(box.querySelectorAll('.gq.cl'), function (g) {                 // a "?" whose term has gone (the text changed)
      var p = g.previousSibling, x = PK[g.getAttribute('data-g')];
      if (!x || !p || p.nodeType !== 3 || !find(x, p.nodeValue, !!g.closest(NEWS))) g.remove();
    });
    var have = {};
    each(box.querySelectorAll('.gq'), function (g) { have[g.getAttribute('data-g')] = 1; });
    var tw = d.createTreeWalker(box, 4, null), node, nodes = [];
    while ((node = tw.nextNode())) nodes.push(node);
    nodes.forEach(function (node) {
      var t = node.nodeValue, par = node.parentElement;
      if (!t || !par || !WORD.test(t) || !(QCI.test(t) || QCS.test(t)) || par.closest(SKIP)) return;
      var ms = [], strict = !!par.closest(NEWS);
      P.forEach(function (x, i) {
        if (have[x.k]) return;
        var m = find(x, t, strict);
        if (m) ms.push({s: m.index, e: m.index + m[0].length, k: x.k, i: i, a: AR.test(m[0])});
      });
      if (!ms.length) return;
      ms.sort(function (a, b) { return a.s - b.s || a.i - b.i; });     // first in the text; at the same place the list order decides
      var keep = [], end = -1;
      ms.forEach(function (m) { if (m.s >= end && !have[m.k]) { keep.push(m); have[m.k] = 1; end = m.e; } });
      if (par.childNodes.length === 1) {            // a text on its own (redrawn whole by Streamlit): the "?" right after the term
        for (var j = keep.length - 1; j >= 0; j--) { var rest = node.splitText(keep[j].e); par.insertBefore(mk(keep[j]), rest); }
      } else {                                      // text between other tags: the "?" after this piece of text
        var after = node.nextSibling;
        keep.forEach(function (m) { par.insertBefore(mk(m), after); });
      }
    });
    seen.set(box, box.textContent);
  }
  function scan() {
    each(d.querySelectorAll('.gq.cl'), function (g) {      // a "?" an older script put inside an icon or a tab: out, the word whole again
      var q = g.parentElement;
      if (q && q.closest(ICONS + ', [role="tab"], [data-testid="stTab"]')) { g.remove(); q.normalize(); }
    });
    each(d.querySelectorAll(BOX), function (box) {
      if (box.parentElement && box.parentElement.closest(BOX)) return;   // inside another box: scanned with it
      if (box.closest(SKIP)) return;
      try { scanBox(box); } catch (e) {}
    });
    if (pop) place();
  }
  every(scan, 800); scan();
})();
</script>""".replace("__SEL__", json.dumps(_fx)).replace("__GLOSS__", json.dumps(GL.client(), ensure_ascii=False))
FX_JS = FX_JS.replace("__VER__", hashlib.md5(FX_JS.encode()).hexdigest()[:10])   # a new script replaces the old one in open tabs


# ---------------------------------------------------------------- formatting
def fmt_price(x):
    if x is None or pd.isna(x):
        return "—"
    x = float(x)
    return f"{x:,.2f}" if abs(x) >= 1 else f"{x:.4f}"


def fmt_big(x):
    if x is None or pd.isna(x):
        return "—"
    for unit, div in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(x) >= div:
            return f"{x / div:.2f}{unit}"
    return f"{x:,.0f}"


def cls(v, invert=False):
    """'pos' / 'neg' / 'neu' for a signed value (the pastel rule)."""
    try:
        if v is None or pd.isna(v) or v == 0:
            return "neu"
    except (TypeError, ValueError):
        return "neu"
    good = v > 0
    if invert:
        good = not good
    return "pos" if good else "neg"


def txt(v, invert=False):
    """Text color class for signed values shown directly on dark surfaces."""
    c = cls(v, invert)
    return {"pos": "upt", "neg": "dnt"}.get(c, "muted")


def color_style(v):
    """Pandas Styler: light-green cell + dark-green text / light-red cell + dark-red text."""
    try:
        if v > 0:
            return LM.css(f"background-color: {POS_BG}; color: {POS_FG}; font-weight: 600")
        if v < 0:
            return LM.css(f"background-color: {NEG_BG}; color: {NEG_FG}; font-weight: 600")
    except TypeError:
        pass
    return ""


def signal_style(v, buy, sell):
    if v == buy:
        return LM.css(f"background-color: {POS_BG}; color: {POS_FG}; font-weight: 600")
    if v == sell:
        return LM.css(f"background-color: {NEG_BG}; color: {NEG_FG}; font-weight: 600")
    return ""


def esc(s):
    return html.escape(str(s))


def icon(name, color=None):
    style = f' style="color:{color}"' if color else ""
    return f'<span class="ms"{style}>{name}</span>'


def ico(name, kind="pos"):
    """Icon inside a pastel circle (readable on dark cards)."""
    bg, fg = {"pos": (POS_BG, POS_FG), "neg": (NEG_BG, NEG_FG), "acc": (ACC_BG, ACC_FG), "gold": (YEL_BG, YEL_FG),
              "neu": ("rgba(157,151,165,.2)", "#BBB5C3")}[kind]
    return f'<span class="ico" style="background:{bg};color:{fg}">{icon(name)}</span>'


# ---------------------------------------------------------------- building blocks
def page_title(ic, title, sub=""):
    return f'<div class="page-title">{icon(ic)}<h1>{esc(title)}</h1></div>' + (f'<div class="page-sub">{sub}</div>' if sub else "")


def sec(ic, text):
    return f'<div class="sec">{icon(ic)}<span>{esc(text)}</span></div>'


def stock_href(sym, lang="en"):
    return f"stock?symbol={sym}&lang={lang}"


def logo_circle(sym, uri=None, size=32):
    s = f"width:{size}px;height:{size}px;font-size:{max(9, int(size * 0.36))}px"
    if uri:
        return f'<span class="lg" style="{s}"><img src="{uri}" alt=""/></span>'
    h = int(hashlib.md5(str(sym).encode()).hexdigest()[:6], 16)
    hue = h % 360
    return (f'<span class="lg" style="{s};background:linear-gradient(135deg,hsl({hue},62%,46%),hsl({(hue + 40) % 360},62%,34%))">'
            f'{esc(str(sym).replace("^", "")[:2])}</span>')


def logo_obj(sym, size=40):
    """Company logo loaded by the browser (Parqet, then Financial Modeling Prep); the initials show when neither has it.
    <object> shows its inner content when the image fails, so there is never a broken-image icon."""
    s = str(sym).replace("^", "")
    h = int(hashlib.md5(s.encode()).hexdigest()[:6], 16) % 360
    ini = s[:3] if len(s) <= 3 else s[:2]
    fs = max(9, int(size * (0.3 if len(ini) == 3 else 0.36)))
    return (f'<span class="lgo" style="width:{size}px;height:{size}px">'
            f'<object data="https://assets.parqet.com/logos/symbol/{esc(s)}?format=png&amp;size=100" type="image/png" tabindex="-1" aria-hidden="true">'
            f'<object data="https://financialmodelingprep.com/image-stock/{esc(s)}.png" type="image/png" tabindex="-1" aria-hidden="true">'
            f'<span class="ini" style="font-size:{fs}px;background:linear-gradient(135deg,hsl({h},62%,46%),hsl({(h + 40) % 360},62%,34%))">{esc(ini)}</span>'
            f'</object></object></span>')


def _ar():
    try:
        import streamlit as st
        return st.session_state.get("lang") == "ar"
    except Exception:
        return False


def sym_label(sym, ar=None, default=None):
    """How a symbol is shown: a Saudi company by its name in the visitor's language (its code is a number), any other by its
    ticker."""
    import tasi
    s = str(sym or "")
    if not tasi.is_sa(s):
        return s
    return tasi.label(s, _ar() if ar is None else ar, default)


def name_line(sym, name=""):
    """The line under a symbol: a Saudi company's industry group (its name is already the title), else the name given."""
    import tasi
    return sym_sub(sym) if tasi.is_sa(sym) else (name or "")


def sym_sub(sym, ar=None):
    """The second line under a Saudi company's name: its industry group (in the visitor's language)."""
    import tasi
    g = tasi.industry_of(sym)
    if not g:
        return ""
    return tasi.industry_ar(g) if (_ar() if ar is None else ar) else g


def company(sym, name="", uri=None, size=32, sub=None, href=None):
    import tasi
    if tasi.is_sa(sym):                     # a Saudi company: its name, and under it its industry (never its number)
        tk = f'<div class="tk" dir="auto">{esc(sym_label(sym, default=name or None))}</div>'
        if sub is None:
            sub = sym_sub(sym)
        name = ""
    else:
        tk = f'<div class="tk"><bdi>{esc(sym)}</bdi></div>'
    sub_html = f'<div class="sub">{esc(sub if sub is not None else name)}</div>' if (sub or name) else ""
    inner = f'<div class="co">{logo_circle(sym, uri, size)}<div class="nm">{tk}{sub_html}</div></div>'
    return f'<a class="lnk" href="{href}" target="_self">{inner}</a>' if href else inner


def pill(pct, invert=False, suffix="%"):
    if pct is None or pd.isna(pct):
        return '<span class="pill neu">—</span>'
    return f'<span class="pill {cls(pct, invert)}">{pct:+.2f}{suffix}</span>'


def sparkline(values, color, w=84, h=30):
    v = np.asarray([x for x in values if pd.notna(x)], dtype=float) if values is not None else np.array([])
    if len(v) < 2:
        return ""
    lo, hi = v.min(), v.max()
    rng = hi - lo if hi > lo else 1.0
    xs = np.linspace(1, w - 1, len(v))
    ys = h - 2 - (v - lo) / rng * (h - 4)
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area = f"1,{h} " + pts + f" {w - 1},{h}"
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"><polygon fill="{color}" opacity=".14" points="{area}"/>'
            f'<polyline fill="none" stroke="{color}" stroke-width="1.8" points="{pts}"/></svg>')


def tile(name, value, chg=None, pct=None, spark=None, sub="", invert=False, head_html=None, kind=None, chg_text=None):
    """Market tile. Positive -> light-green tile + dark-green text; negative -> light-red + dark-red."""
    c = kind or cls(pct if pct is not None else chg, invert)
    color = {"pos": POS_FG, "neg": NEG_FG, "acc": ACC_FG}.get(c, MUTED)
    if chg_text is not None:
        t = chg_text
    elif pct is not None and chg is not None:
        t = f"{chg:+,.2f} ({pct:+.2f}%)"
    elif pct is not None:
        t = f"{pct:+.2f}%"
    elif chg is not None:
        t = f"{chg:+,.2f}"
    else:
        t = ""
    svg = sparkline(spark, color) if spark is not None else ""
    head = head_html or f'<div class="t-name">{esc(name)}</div>'
    k = f" {c}" if c in ("pos", "neg", "acc") else ""
    return (f'<div class="tile{k}">{head}<div class="t-row"><div><div class="t-val">{value}</div><div class="t-chg">{t}</div></div>{svg}</div>'
            + (f'<div class="t-sub">{esc(sub)}</div>' if sub else "") + "</div>")


def tiles(items):
    return '<div class="tiles">' + "".join(items) + "</div>"


def badge(text, kind="neu", ic=None):
    return f'<span class="badge b-{kind}">{icon(ic) if ic else ""}{esc(text)}</span>'


def ticker_chip(sym, pct, uri=None, href=None):
    c = cls(pct) if pct is not None and not pd.isna(pct) else "neu"
    val = pill(pct) if pct is not None and not pd.isna(pct) else ""
    lab = sym_label(sym)
    lab = lab if len(lab) <= 22 else lab[:21] + "…"
    inner = f'{logo_circle(sym, uri, 20)}<bdi>{esc(lab)}</bdi> {val}'
    if href:
        return f'<a class="tkc {c}" href="{href}" target="_self">{inner}</a>'
    return f'<span class="tkc {c}">{inner}</span>'


def kpi(ic, label, value_html, sub="", kind=None):
    k = f" {kind}" if kind in ("pos", "neg", "acc") else ""
    return (f'<div class="kpi{k}"><div class="l">{icon(ic)}{esc(label)}</div><div class="v">{value_html}</div>'
            f'<div class="s">{sub}</div></div>')


def tape(items):
    inner = "".join(f'<span class="it"><b>{esc(n)}</b>{fmt_price(p)} {pill(c)}</span>' for n, p, c in items)
    return f'<div class="tape"><div class="track">{inner}{inner}</div></div>'


def time_ago(ts, ar=False):
    if ts is None or pd.isna(ts):
        return ""
    mins = (pd.Timestamp.now(tz="UTC") - ts).total_seconds() / 60
    if ar:
        if mins < 60:
            return f"قبل {int(max(mins, 1))} دقيقة"
        if mins < 1440:
            return f"قبل {int(mins // 60)} ساعة"
        return f"قبل {int(mins // 1440)} يوم"
    if mins < 60:
        return f"{int(max(mins, 1))}m ago"
    if mins < 1440:
        return f"{int(mins // 60)}h ago"
    return f"{int(mins // 1440)}d ago"


def iq_badge(iq, ar=False):
    """Importance score box: 10 = very important (light red + dark red), 1 = not important (light green + dark green)."""
    import newsiq
    sc = int(iq["score"])
    bg, fg, bd = newsiq.colors(sc)
    en, a = newsiq.level(sc)
    why = " · ".join(f"{r[1] if ar else r[0]} {r[2]:+.1f}" for r in iq.get("reasons", []))
    tip = f"{'الأهمية' if ar else 'Importance'} {sc}/10: {a if ar else en}" + (f" · {why}" if why else "")
    return (f'<div class="iq" style="--iqb:{bg};--iqf:{fg};--iqd:{bd}" title="{esc(tip)}"><div class="n">{sc}<small>/10</small></div>'
            f'<div class="l">{esc(a if ar else en)}</div><div class="bar"><i style="width:{sc * 10}%"></i></div></div>')


def kw_chips(iq, ar=False, limit=6):
    import newsiq
    out = []
    for key, en, a in iq.get("keywords", [])[:limit]:
        k = " op" if key == "opinion" else (" ent" if key == "entity" else "")
        out.append(f'<span class="kwc{k}">{icon(newsiq.TOPIC_ICON.get(key, "label"))}{esc(a if ar else en)}</span>')
    return '<div class="kw">' + "".join(out) + "</div>" if out else ""


def iq_legend(ar=False):
    import newsiq
    cells = "".join(f'<span style="background:{newsiq.COLORS[i][0]};color:{newsiq.COLORS[i][1]}">{i}</span>' for i in range(1, 11))
    lo, hi = ("غير هام", "هام جداً") if ar else ("Not important", "Very important")
    return (f'<div class="iqleg"><span class="muted">{esc(lo)}</span><span class="sc">{cells}</span><span class="muted">{esc(hi)}</span></div>')


# topic -> (gradient, english label, arabic label) for news pictures when the story has no photo
_TG = {"macro": "linear-gradient(135deg,#1D4ED8 0%,#4F46E5 55%,#7C3AED 100%)", "world": "linear-gradient(135deg,#B45309 0%,#EA580C 55%,#DC2626 100%)",
       "company": "linear-gradient(135deg,#047857 0%,#0D9488 55%,#0891B2 100%)", "deal": "linear-gradient(135deg,#7C3AED 0%,#A21CAF 55%,#DB2777 100%)",
       "risk": "linear-gradient(135deg,#991B1B 0%,#BE123C 60%,#E11D48 100%)", "tech": "linear-gradient(135deg,#0369A1 0%,#2563EB 55%,#06B6D4 100%)",
       "crypto": "linear-gradient(135deg,#C2410C 0%,#EA580C 50%,#F59E0B 100%)", "commod": "linear-gradient(135deg,#854D0E 0%,#CA8A04 55%,#EAB308 100%)",
       "market": "linear-gradient(135deg,#1E3A8A 0%,#2563EB 50%,#0EA5E9 100%)"}
_TOPIC_GROUP = {"fed": "macro", "inflation": "macro", "jobs": "macro", "economy": "macro", "bonds": "macro", "trade": "world", "geo": "world",
                "policy": "world", "earnings": "company", "guidance": "company", "analyst": "company", "payout": "company", "mna": "deal", "ipo": "deal",
                "legal": "risk", "distress": "risk", "layoffs": "risk", "health": "tech", "ai": "tech", "product": "tech", "crypto": "crypto",
                "oil": "commod", "metals": "commod", "fx": "commod", "move": "market", "street": "market"}


def _safe_img(url):
    u = str(url or "").strip()
    if not u or not u.startswith(("http://", "https://")) or any(x in u.lower() for x in ("1x1", "pixel", "spacer", "blank.gif")):
        return ""
    return "https://" + u[7:] if u.startswith("http://") else u


def news_thumb(n, big=False):
    """Picture for a story: the outlet's photo when there is one, otherwise a topic picture (never a broken-image icon:
    if the photo cannot load, the topic picture is drawn in its place). The first affected company's logo sits in the corner."""
    import newsiq
    iq = n.get("iq") or {}
    topic = iq.get("pic") if iq.get("pic") in _TOPIC_GROUP else next((t for t in iq.get("topics", []) if t in _TOPIC_GROUP), "street")
    ic = newsiq.TOPIC_ICON.get(topic, "show_chart")
    grad = _TG[_TOPIC_GROUP.get(topic, "market")]
    lab = next(((en, ar) for key, en, ar, *_ in newsiq.TOPICS if key == topic), ("Markets", "الأسواق"))
    tick = [t for t in (n.get("tickers") or []) if t][:1]
    lg = f'<span class="nlg">{logo_obj(tick[0], 34 if big else 30)}</span>' if tick else ""
    url = _safe_img(n.get("img"))
    cls = "nth big" if big else "nth"
    try:                                             # a free photo of the story's topic (newspics): stands in when the story has none
        import newspics
        tp = newspics.topic_photo(topic, n.get("link") or n.get("title"), big)
    except Exception:
        tp = None
    if url:                                          # the story's own photo; if it cannot load, the topic photo takes its place
        alt = f' data-alt="{esc(tp["u"])}" data-altc="{esc(tp["c"])}"' if tp else ""
        return (f'<span class="{cls}" style="--g:{grad}"><img src="{esc(url)}" alt="" loading="lazy" referrerpolicy="no-referrer" '
                f'data-ic="{ic}"{alt}>{lg}</span>')
    if tp:
        return (f'<span class="{cls} tp" style="--g:{grad}" title="{esc(tp["c"])}"><img src="{esc(tp["u"])}" alt="" loading="lazy" '
                f'referrerpolicy="no-referrer" data-ic="{ic}">{lg}</span>')
    return (f'<span class="{cls} fb" style="--g:{grad}"><span class="ms">{ic}</span>'
            f'<em data-en="{esc(lab[0])}" data-ar="{esc(lab[1])}"></em>{lg}</span>')


def also_badge(also, ar=False):
    """'+3' next to the outlet: the same story was also reported by other outlets (names on hover)."""
    also = [a for a in (also or []) if a]
    if not also:
        return ""
    tip = ("نشرته أيضاً: " + "، ".join(also)) if ar else ("Also reported by: " + ", ".join(also))
    return f' <span class="also" title="{esc(tip)}">+{len(also)}</span>'


def coverage(n, ui_ar=False, titles=None):
    """The same event told by other outlets (newsbot.cluster's "more"): a drawer at the foot of the card that opens on a click.
    titles: {original title: translated title}."""
    more = [m for m in (n.get("more") or []) if m.get("title")]
    if not more:
        return ""
    tr = titles or {}
    rows = "".join(f'<li><a class="nogq" href="{esc(m.get("link") or "#")}" target="_blank" dir="auto">{esc(tr.get(m["title"]) or m["title"])}</a>'
                   f'<span>{esc(m.get("source") or "")} · {time_ago(m.get("time"), ui_ar)}</span></li>' for m in more[:8])
    k = len(more)
    lab = (f"تغطية كاملة · {k} {'خبر آخر' if k == 1 else 'أخبار أخرى'} عن نفس الحدث" if ui_ar else
           f"Full coverage · {k} more {'story' if k == 1 else 'stories'} on this")
    return (f'<details class="ncov"><summary>{icon("stacks")}<span>{esc(lab)}</span>{icon("expand_more")}</summary>'
            f'<ul>{rows}</ul></details>')


def news_card(n, title, summary, chips="", aff_label="", ar=False, tag=None, iq=None, ui_ar=None, cov_titles=None, foot=False):
    """News card. iq = newsiq.analyze(...) adds the importance box, a colored edge and keyword chips. The other outlets'
    stories of the same event open in a drawer at its foot; foot=True leaves room there for the "analyse" button."""
    import newsiq
    ui_ar = ar if ui_ar is None else ui_ar
    summary = summary or ""
    short = esc(summary[:300]) + ("…" if len(summary) > 300 else "")
    tag_html = f"{badge(tag, 'acc')} " if tag else ""
    aff = f'<div class="aff"><span class="lbl">{esc(aff_label)}</span>{chips}</div>' if chips else ""
    rtl = " rtl" if ar else ""
    head = (f'<div class="nb">{tag_html}<a class="t nogq" href="{esc(n["link"])}" target="_blank">{esc(title)}</a>'
            f'<div class="meta">{icon("schedule")} <bdi>{esc(n["source"])}</bdi>{also_badge(n.get("also"), ui_ar)} · {time_ago(n["time"], ui_ar)}</div></div>')
    pic = news_thumb(n)
    cov = coverage(n, ui_ar, cov_titles)
    ft = " hasft" if foot else ""
    if iq:
        edge = newsiq.colors(iq["score"])[2]
        return (f'<div class="news hasiq{rtl}{ft}" style="--iqd:{edge}"><div class="nwrap">{pic}<div class="nbody"><div class="nh">{head}{iq_badge(iq, ui_ar)}</div>'
                + (f'<div class="sum">{short}</div>' if short else "") + kw_chips(iq, ui_ar) + aff + "</div></div>" + cov + "</div>")
    return (f'<div class="news{rtl}{ft}"><div class="nwrap">{pic}<div class="nbody"><div class="nh">{head}</div>'
            + (f'<div class="sum">{short}</div>' if short else "") + aff + "</div></div>" + cov + "</div>")


def market_status(ar=False, market=None):
    """The market's state right now (open, pre-market, closed...) with its local time. market: us / sa (default: the market of
    the page being drawn, markets.current())."""
    import markets as MK
    state, dot, when = MK.status(market or MK.current(), ar)
    return f'<span class="status" title="{state} · {when}"><span class="dot {dot}"></span><b>{state}</b><span class="muted">· {when}</span></span>'


# ---------------------------------------------------------------- modern widgets
RATING_COLORS = ["#EF4444", "#F87171", "#64748B", "#4ADE80", "#22C55E"]


def rating_meter(score, label, title, counts=None, labels=("Strong Sell", "Sell", "Neutral", "Buy", "Strong Buy")):
    """Segmented rating bar with a pointer (score in -1..1). counts: [(text, kind), ...]."""
    pos = max(0.0, min(100.0, (score + 1) / 2 * 100))
    kind = "pos" if score > 0.1 else ("neg" if score < -0.1 else "neu")
    bg = {"pos": f"background:{POS_BG};color:{POS_FG}", "neg": f"background:{NEG_BG};color:{NEG_FG}",
          "neu": f"background:{NEU_BG};color:{NEU_FG}"}[kind]
    segs = "".join(f'<span style="background:{c}"></span>' for c in RATING_COLORS)
    cnt = "".join(f'<span class="pill {k}" style="min-width:0">{esc(t)}</span>' for t, k in (counts or []))
    return (f'<div class="rmeter"><div class="rt">{esc(title)}</div><div class="rv" style="{bg}">{esc(label)}</div>'
            f'<div class="rbar">{segs}<i style="left:calc({pos:.1f}% - 8px)"></i></div>'
            f'<div class="rlab">{"".join(f"<span>{esc(x)}</span>" for x in labels)}</div><div class="rcnt">{cnt}</div></div>')


def ladder(levels, price, now_label="Price"):
    """levels: [(name, value, 'res'|'sup'|'piv')] -> vertical price ladder with the current price highlighted."""
    rows = sorted(levels, key=lambda x: -x[1])
    out, placed = [], False
    for name, v, kind in rows:
        if not placed and v < price:
            out.append(f'<div class="lr now"><span class="ln">{esc(now_label)}</span><span class="lp">{fmt_price(price)}</span><span></span></div>')
            placed = True
        d = (v / price - 1) * 100
        out.append(f'<div class="lr {kind}"><span class="ln">{esc(name)}</span><span class="lp">{fmt_price(v)}</span>{pill(d)}</div>')
    if not placed:
        out.append(f'<div class="lr now"><span class="ln">{esc(now_label)}</span><span class="lp">{fmt_price(price)}</span><span></span></div>')
    return '<div class="ladder">' + "".join(out) + "</div>"


def ring(pct, size=150, color=ACCENT, label="", sub="", track=BORDER, stroke=14):
    r = (size - stroke) / 2
    c = 2 * np.pi * r
    off = c * (1 - max(0, min(100, pct)) / 100)
    gid = f"rg{abs(hash((pct, color, size))) % 10**6}"
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="display:block;margin:auto">'
            f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{color}"/>'
            f'<stop offset="1" stop-color="{VIOLET}"/></linearGradient></defs>'
            f'<circle cx="{size / 2}" cy="{size / 2}" r="{r}" stroke="{track}" stroke-width="{stroke}" fill="none"/>'
            f'<circle cx="{size / 2}" cy="{size / 2}" r="{r}" stroke="url(#{gid})" stroke-width="{stroke}" fill="none" stroke-linecap="round" '
            f'stroke-dasharray="{c:.1f}" stroke-dashoffset="{off:.1f}" transform="rotate(-90 {size / 2} {size / 2})"/>'
            f'<text x="50%" y="48%" text-anchor="middle" font-size="{size * 0.2:.0f}" font-weight="800" fill="#fff" font-family="{FONT}">{esc(label)}</text>'
            f'<text x="50%" y="64%" text-anchor="middle" font-size="{size * 0.085:.0f}" fill="{MUTED}" font-family="{FONT}">{esc(sub)}</text></svg>')


def pulse_gauge(pct, title, sub=""):
    """Semicircle gauge 0-100 with gradient arc and needle (market breadth)."""
    pct = max(0.0, min(100.0, pct))
    ang = np.pi * (1 - pct / 100)
    cx, cy, r = 150, 150, 110
    nx, ny = cx + (r - 20) * np.cos(ang), cy - (r - 20) * np.sin(ang)
    kind = "pos" if pct > 55 else ("neg" if pct < 45 else "neu")
    col = {"pos": POS_FG, "neg": NEG_FG, "neu": NEU_FG}[kind]
    bgc = {"pos": POS_BG, "neg": NEG_BG, "neu": NEU_BG}[kind]
    return (f'<svg viewBox="0 0 300 236" style="width:100%;max-width:340px;display:block;margin:auto">'
            '<defs><linearGradient id="pg" x1="0" x2="1"><stop offset="0" stop-color="#EF4444"/><stop offset=".5" stop-color="#F5B94A"/>'
            '<stop offset="1" stop-color="#22C55E"/></linearGradient></defs>'
            f'<path d="M40 150 A110 110 0 0 1 260 150" fill="none" stroke="{BORDER}" stroke-width="22" stroke-linecap="round"/>'
            '<path d="M40 150 A110 110 0 0 1 260 150" fill="none" stroke="url(#pg)" stroke-width="22" stroke-linecap="round" opacity=".95"/>'
            f'<line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="#fff" stroke-width="5" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="9" fill="#fff"/>'
            f'<rect x="100" y="166" width="100" height="30" rx="9" fill="{bgc}"/>'
            f'<text x="150" y="187" text-anchor="middle" font-size="18" font-weight="800" fill="{col}" font-family="{FONT}">{pct:.0f}%</text>'
            f'<text x="150" y="214" text-anchor="middle" font-size="12.5" font-weight="700" fill="#CCC7D3" font-family="{FONT}">{esc(title)}</text>'
            f'<text x="150" y="231" text-anchor="middle" font-size="11.5" fill="{MUTED}" font-family="{FONT}">{esc(sub)}</text></svg>')


def progress_bars(items):
    """items: [(label, value_text, pct 0-100, color)]"""
    return '<div class="bars">' + "".join(
        f'<div class="b"><div class="t"><span>{esc(l)}</span><span class="num">{esc(v)}</span></div>'
        f'<div class="trk"><span style="width:{max(0, min(100, p)):.1f}%;background:{c}"></span></div></div>' for l, v, p, c in items) + "</div>"


def ad_bar(adv, dec, unch=0):
    tot = max(adv + dec + unch, 1)
    return (f'<div class="adbar"><span style="width:{adv / tot * 100:.1f}%;background:{UP}"></span>'
            f'<span style="width:{unch / tot * 100:.1f}%;background:#64748B"></span>'
            f'<span style="width:{dec / tot * 100:.1f}%;background:{DOWN}"></span></div>')


def sector_card(name, etf, d1, w1, m1, spark=None, href=None):
    c = cls(d1)
    bg, fg = {"pos": (POS_BG, POS_FG), "neg": (NEG_BG, NEG_FG)}.get(c, (CARD2, TEXT))
    sp = sparkline(spark, fg, 70, 24) if spark is not None else ""
    f = lambda v: f"{v:+.1f}%" if v is not None and pd.notna(v) else "—"
    return (f'<div class="sc {c}" style="color:{fg}"><div class="h"><span>{esc(name)}</span><span style="opacity:.7">{esc(etf)}</span></div>'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-end"><div class="v">{f(d1)}</div>{sp}</div>'
            f'<div class="f"><span>1W {f(w1)}</span><span>1M {f(m1)}</span></div></div>')


# ---------------------------------------------------------------- animated skyline hero
def _windows(x0, y0, w, h, cols, rows, seed):
    rng = np.random.default_rng(seed)
    out = []
    cw, rh = w / cols, h / rows
    for r in range(rows):
        for c in range(cols):
            if rng.random() < 0.55:
                out.append(f'<rect class="win" x="{x0 + c * cw + cw * 0.28:.1f}" y="{y0 + r * rh + rh * 0.3:.1f}" width="{cw * 0.44:.1f}" '
                           f'height="{rh * 0.4:.1f}" style="animation-duration:{rng.uniform(2.5, 9):.1f}s;animation-delay:-{rng.uniform(0, 8):.1f}s"/>')
    return "".join(out)


LINE_PTS = [(0, 210), (90, 200), (160, 215), (240, 180), (320, 190), (400, 150), (470, 165), (560, 120), (640, 140),
            (720, 100), (800, 115), (880, 80), (960, 98), (1040, 60), (1120, 75), (1200, 45), (1300, 58), (1400, 30)]
LINE_PATH = "M" + " L".join(f"{x} {y}" for x, y in LINE_PTS)
HERO_CSS = f"""<style>
.hero .win {{ fill:#9DCBF7; opacity:.7; animation-name: twinkle; animation-iteration-count: infinite; animation-timing-function: ease-in-out; }}
.hero .star {{ fill:#fff; animation: twinkle 4s ease-in-out infinite; }}
@keyframes twinkle {{ 0%,100% {{ opacity:.85; }} 50% {{ opacity:.08; }} }}
.hero .mline {{ stroke-dasharray: 2600; stroke-dashoffset: 2600; animation: draw 9s ease-in-out infinite; }}
@keyframes draw {{ 0% {{ stroke-dashoffset:2600; }} 60%,100% {{ stroke-dashoffset:0; }} }}
.hero .mdot {{ offset-path: path('{LINE_PATH}'); offset-rotate: 0deg; animation: travel 9s ease-in-out infinite; }}
@keyframes travel {{ 0% {{ offset-distance:0%; }} 60%,100% {{ offset-distance:100%; }} }}
.hero .beam {{ animation: beam 7s ease-in-out infinite; transform-origin: 907px 20px; }}
@keyframes beam {{ 0%,100% {{ transform: rotate(-18deg); opacity:.16; }} 50% {{ transform: rotate(18deg); opacity:.3; }} }}
</style>"""


def _skyline():
    back, front = "#0f2247", "#070d1c"
    s = []
    rng = np.random.default_rng(7)
    for _ in range(40):
        s.append(f'<circle class="star" cx="{rng.uniform(0, 1400):.0f}" cy="{rng.uniform(5, 150):.0f}" r="{rng.uniform(0.6, 1.6):.1f}" '
                 f'style="animation-delay:-{rng.uniform(0, 4):.1f}s"/>')
    s.append('<defs><linearGradient id="ln" x1="0" x2="1"><stop offset="0" stop-color="#2DB6EB" stop-opacity="0"/>'
             '<stop offset=".35" stop-color="#3B8BEB"/><stop offset="1" stop-color="#A78BFA"/></linearGradient>'
             '<linearGradient id="bm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9DCBF7" stop-opacity=".9"/>'
             '<stop offset="1" stop-color="#9DCBF7" stop-opacity="0"/></linearGradient>'
             '<filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    s.append('<path class="beam" d="M907 20 L760 350 L1054 350 Z" fill="url(#bm)"/>')
    s.append(f'<g fill="{back}"><rect x="640" y="150" width="70" height="200"/><rect x="720" y="120" width="55" height="230"/>'
             '<rect x="1130" y="140" width="80" height="210"/><rect x="1220" y="170" width="60" height="180"/>'
             '<rect x="520" y="175" width="60" height="175"/><rect x="1300" y="130" width="70" height="220"/>'
             '<path d="M1010 350 L1010 95 Q1075 150 1080 350 Z"/><rect x="1004" y="80" width="4" height="20"/>'
             '<path d="M880 350 L880 170 L890 170 L890 120 L898 120 L898 70 L904 70 L904 20 L907 20 L910 70 L916 70 L916 120 L924 120 '
             'L924 170 L934 170 L934 350 Z"/></g>')
    s.append(f'<path class="mline" d="{LINE_PATH}" fill="none" stroke="url(#ln)" stroke-width="2.6" filter="url(#glow)"/>')
    s.append('<circle class="mdot" r="5" fill="#2DB6EB" filter="url(#glow)"/>')
    s.append(f'<g fill="{front}"><rect x="150" y="248" width="230" height="102"/><path d="M140 250 L265 205 L390 250 Z"/>'
             '<rect x="140" y="248" width="250" height="8"/><rect x="0" y="210" width="80" height="140"/><rect x="85" y="185" width="55" height="165"/>'
             '<path d="M400 350 L400 170 L412 170 L412 130 L424 130 L424 95 L432 95 L432 55 L436 55 L436 95 L444 95 L444 130 L456 130 L456 170 '
             'L468 170 L468 350 Z"/><rect x="480" y="230" width="75" height="120"/><rect x="590" y="200" width="60" height="150"/>'
             '<rect x="780" y="215" width="80" height="135"/><rect x="950" y="235" width="50" height="115"/>'
             '<rect x="1090" y="225" width="45" height="125"/><rect x="1370" y="205" width="40" height="145"/></g>')
    s.append("".join(f'<rect x="{165 + i * 28}" y="262" width="10" height="84" fill="#10234a"/>' for i in range(8)))
    s.append(_windows(0, 220, 80, 120, 4, 6, 1) + _windows(85, 195, 55, 150, 3, 7, 2) + _windows(400, 180, 68, 165, 3, 9, 3)
             + _windows(480, 240, 75, 105, 4, 5, 4) + _windows(590, 210, 60, 135, 3, 7, 5) + _windows(780, 225, 80, 120, 4, 6, 6)
             + _windows(950, 245, 50, 100, 2, 5, 8) + _windows(1090, 235, 45, 110, 2, 5, 9) + _windows(1370, 215, 40, 130, 2, 6, 10))
    return ('<svg class="city" viewBox="0 0 1400 350" preserveAspectRatio="xMidYMax slice" xmlns="http://www.w3.org/2000/svg">'
            + "".join(s) + "</svg>")


_SKYLINE = None


def hero(eyebrow, title_html, tagline, chips_html, rtl=False):
    global _SKYLINE
    if _SKYLINE is None:
        _SKYLINE = _skyline()
    wrap = ' class="rtl"' if rtl else ""
    return (f'{HERO_CSS}<div{wrap}><div class="hero">{_SKYLINE}<div class="content"><div class="eyebrow">{esc(eyebrow)}</div>'
            f'<div class="title">{title_html}</div><div class="tagline">{esc(tagline)}</div><div class="chips">{chips_html}</div></div></div></div>')




def svg_data_uri(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


# ---------------------------------------------------------------- trading-dashboard widgets
def money(v, dec=0, short=False):
    """$1,234 / -$1,234 / $1.2K (sign before the dollar). On a Saudi market page: riyals (SAR 1,234 / 1,234 ر.س)."""
    if v is None or pd.isna(v):
        return "—"
    import markets as MK
    if MK.get()["cur"] != "USD":
        return MK.money(v, dec=dec, short=short)
    sign = "-" if v < 0 else ""
    a = abs(float(v))
    if short and a >= 1000:
        for unit, div in (("M", 1e6), ("K", 1e3)):
            if a >= div:
                return f"{sign}${a / div:.1f}{unit}"
    return f"{sign}${a:,.{dec}f}"


def pbox(text, v=None, kind=None):
    """Value inside a pastel box: light green + dark green (positive) / light red + dark red (negative)."""
    k = kind or cls(v)
    return f'<span class="pbox {k}">{text}</span>'


def semi(pct, value_text=None, size=150):
    """Half-circle gauge 0-100 (green arc when >= 50, red below) with a pastel value box."""
    pct = max(0.0, min(100.0, float(pct)))
    kind = "pos" if pct >= 50 else "neg"
    col = UP if kind == "pos" else DOWN
    r, cx, cy = 52, 75, 68
    ang = np.pi * (1 - pct / 100)
    ex, ey = cx + r * np.cos(ang), cy - r * np.sin(ang)
    bg, fg = (POS_BG, POS_FG) if kind == "pos" else (NEG_BG, NEG_FG)
    txt = value_text or f"{pct:.1f}%"
    arc = (f'<path d="M{cx - r} {cy} A{r} {r} 0 0 1 {ex:.1f} {ey:.1f}" fill="none" stroke="{col}" stroke-width="12" stroke-linecap="round"/>'
           if pct > 0.5 else "")
    return (f'<svg width="{size}" height="{size * 0.62:.0f}" viewBox="0 0 150 93">'
            f'<path d="M{cx - r} {cy} A{r} {r} 0 0 1 {cx + r} {cy}" fill="none" stroke="{BORDER}" stroke-width="12" stroke-linecap="round"/>{arc}'
            f'<rect x="{cx - 36}" y="{cy - 20}" width="72" height="26" rx="8" fill="{bg}"/>'
            f'<text x="{cx}" y="{cy - 2}" text-anchor="middle" font-size="15" font-weight="800" fill="{fg}" font-family="{FONT}">{esc(txt)}</text></svg>')


def goal(pct_of_goal, left, right, met=False):
    w = max(0.0, min(100.0, pct_of_goal))
    return (f'<div class="goal{" met" if met else ""}"><div class="gt"><span>{esc(left)}</span><span>{esc(right)}</span></div>'
            f'<div class="gb"><span style="width:{w:.0f}%"></span></div></div>')


FG_ZONES = [(0, 25, "Extreme fear", "خوف شديد", "neg"), (25, 45, "Fear", "خوف", "neg"), (45, 55, "Neutral", "محايد", "neu"),
            (55, 75, "Greed", "طمع", "pos"), (75, 101, "Extreme greed", "طمع شديد", "pos")]
FG_COLORS = ["#EF4444", "#F97316", "#94A3B8", "#84CC16", "#22C55E"]


def fg_zone(v):
    for lo, hi, en, ar, kind in FG_ZONES:
        if lo <= v < hi:
            return en, ar, kind
    return FG_ZONES[-1][2:]


def fg_gauge(v, ar=False, sub=""):
    """Fear & Greed dial: five colored zones, a needle and the value in a pastel box."""
    v = max(0.0, min(100.0, float(v)))
    cx, cy, r = 160, 158, 118
    def pt(p, rr):
        a = np.pi * (1 - p / 100)
        return cx + rr * np.cos(a), cy - rr * np.sin(a)
    arcs = []
    for (lo, hi, *_), col in zip(FG_ZONES, FG_COLORS):
        x0, y0 = pt(lo + 0.9, r)
        x1, y1 = pt(min(hi, 100) - 0.9, r)
        arcs.append(f'<path d="M{x0:.1f} {y0:.1f} A{r} {r} 0 0 1 {x1:.1f} {y1:.1f}" fill="none" stroke="{col}" stroke-width="24" stroke-linecap="butt" opacity=".92"/>')
    ticks = "".join(f'<text x="{pt(t, r + 26)[0]:.1f}" y="{pt(t, r + 26)[1] + 4:.1f}" text-anchor="middle" font-size="11" fill="{MUTED}" '
                    f'font-family="{FONT}">{t}</text>' for t in (0, 25, 50, 75, 100))
    nx, ny = pt(v, r - 30)
    en, a, kind = fg_zone(v)
    bg, fg = {"pos": (POS_BG, POS_FG), "neg": (NEG_BG, NEG_FG)}.get(kind, (NEU_BG, NEU_FG))
    label = a if ar else en
    return (f'<svg viewBox="0 0 320 250" style="width:100%;max-width:380px;display:block;margin:auto">'
            f'<path d="M{cx - r} {cy} A{r} {r} 0 0 1 {cx + r} {cy}" fill="none" stroke="{BORDER}" stroke-width="30"/>{"".join(arcs)}{ticks}'
            f'<line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="#fff" stroke-width="5" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="10" fill="#fff"/><circle cx="{cx}" cy="{cy}" r="4" fill="{BG}"/>'
            f'<rect x="{cx - 62}" y="{cy + 20}" width="124" height="42" rx="12" fill="{bg}"/>'
            f'<text x="{cx}" y="{cy + 49}" text-anchor="middle" font-size="26" font-weight="800" fill="{fg}" font-family="{FONT}">{v:.0f}</text>'
            f'<text x="{cx}" y="{cy + 84}" text-anchor="middle" font-size="15" font-weight="800" fill="#fff" font-family="{FONT}">{esc(label)}</text>'
            + (f'<text x="{cx}" y="{cy + 102}" text-anchor="middle" font-size="11" fill="{MUTED}" font-family="{FONT}">{esc(sub)}</text>' if sub else "")
            + "</svg>")

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "22.4"
