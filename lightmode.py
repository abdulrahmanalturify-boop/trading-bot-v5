"""
lightmode.py - the site's light look, made from its dark design.

Streamlit's own ⋮ menu offers System / Light / Dark once config.toml defines a [theme.light] and a [theme.dark]; Streamlit
then colours its own widgets. Everything the site draws itself (the styles in theme.py and the pages, the HTML cards, the
inline SVG and the Plotly charts) is written for the dark look, so in light mode every colour in it is turned into its light
counterpart on the way out, by what the colour does:

- surfaces (background): the night becomes a pale lavender page, cards and panels become white, the dark tinted boxes
  (dark green / dark red / dark blue ...) become their pale tints; accent colours and see-through tints stay as they are;
- text (color): white and light grey become a deep violet-black ink, bright accent text (bright green, bright red, lavender
  ...) becomes its deep shade, so it reads on white; text that was already dark (on a pale chip) stays;
- lines (border, outline): dark hairlines become light grey lines, white see-through hairlines become dark see-through ones;
- shadows: soft and lighter; drawings (SVG fill / stroke, chart lines): greys mirrored, bright accents deepened.

The landing (the intro with the crystal) keeps its night in both looks. The choice reaches the server through
st.context.theme; the page script reruns the page when the page was drawn for the other look (theme.FX_JS).
"""
import colorsys
import re
import sys
from functools import lru_cache

import streamlit as st

KEY = "_lm"                    # session flag: this run draws the light look
THEME_KEY = "_lm_theme"        # the theme Streamlit reported for this run ("light" / "dark")
VIOLET_H = 262 / 360           # the site's violet: the ink and the page keep a hint of it

_HEX = r"(?<![&\w#])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})(?![\w-])"
_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)%?"
_RGB = rf"\brgba?\(\s*{_NUM}\s*(?:,\s*|\s+){_NUM}\s*(?:,\s*|\s+){_NUM}\s*(?:(?:,|/)\s*{_NUM}\s*)?\)"
COLOR = re.compile(f"{_HEX}|{_RGB}")


# ---------------------------------------------------------------- the switch
def theme_type():
    """'light' / 'dark' as Streamlit reports the visitor's active theme (None when unknown)."""
    try:
        t = st.context.theme.type
    except Exception:
        return None
    return t if t in ("light", "dark") else None


def on():
    """True while this run draws the light look."""
    try:
        return bool(st.session_state.get(KEY))
    except Exception:
        return False


def start(landing=False):
    """Called once at the top of every run: follow the visitor's theme (the landing always keeps its night)."""
    t = theme_type() or "dark"
    st.session_state[THEME_KEY] = t
    st.session_state[KEY] = (t == "light") and not landing
    return st.session_state[KEY]


# ---------------------------------------------------------------- one colour
def _parse(tok):
    """'#abc' / '#aabbcc' / '#aabbccdd' / 'rgb(...)' / 'rgba(...)' -> (r, g, b, a) in 0..1, or None."""
    t = tok.strip()
    try:
        if t[0] == "#":
            h = t[1:]
            if len(h) in (3, 4):
                h = "".join(c * 2 for c in h)
            r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
            a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
            return r, g, b, a
        parts = re.findall(_NUM, t[t.index("(") + 1:])
        vals = []
        for i, p in enumerate(parts[:4]):
            if p.endswith("%"):
                vals.append(float(p[:-1]) / 100)
            else:
                vals.append(float(p) / (255 if i < 3 else 1))
        r, g, b = (min(1.0, max(0.0, v)) for v in vals[:3])
        a = min(1.0, max(0.0, vals[3])) if len(vals) > 3 else 1.0
        return r, g, b, a
    except (ValueError, IndexError):
        return None


def _fmt(r, g, b, a, like):
    R, G, B = (int(round(min(1.0, max(0.0, v)) * 255)) for v in (r, g, b))
    if a >= 0.999 and like.startswith("#"):
        return f"#{R:02X}{G:02X}{B:02X}"
    if a >= 0.999 and like.lower().startswith("rgb("):
        return f"rgb({R},{G},{B})"
    return f"rgba({R},{G},{B},{round(a, 3):g})"


def _hls(h, l, s):
    return colorsys.hls_to_rgb(h, min(1.0, max(0.0, l)), min(1.0, max(0.0, s)))


def _ink(l, h=VIOLET_H, s=.30):
    """The dark ink of the light look: violet-black, l from about .1 (body text) to .45 (quiet text)."""
    return _hls(h, l, s)


@lru_cache(maxsize=8192)
def color(tok, role="ink"):
    """The light-look counterpart of one colour, by its role: 'bg', 'text', 'border', 'shadow' or 'ink'."""
    c = _parse(tok)
    if c is None:
        return tok
    r, g, b, a = c
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    chroma = max(r, g, b) - min(r, g, b)
    grey = chroma < .12
    if role == "bg":
        if l < .30:
            if chroma >= .09:                                    # dark tinted box -> its pale tint
                r, g, b = _hls(h, .94, min(1.0, s * 1.35 + .12))
            else:                                                # the night -> pale lavender page; cards and panels -> white
                r, g, b = _hls(h, min(1.0, max(.94, .952 + (l - .055))), min(s, .5))
        elif not grey:
            if a >= .9:
                return tok                                       # accents and pastels: as they are
            a *= .65                                             # see-through accent tints: a little lighter on white
        elif a < .9:                                             # white see-through layer -> dark see-through layer
            r, g, b = _ink(.06 + (1 - l) * .9)
        elif l > .85:
            return tok                                           # white boxes (company logos sit on them) stay white
        else:
            r, g, b = _hls(h, 1 - l, min(s, .3))
    elif role == "text":
        if grey:
            if l <= .5:
                return tok                                       # already dark: it sits on a pale chip
            r, g, b = _ink(.10 + (1 - l) * .62, h if s > .05 else VIOLET_H, min(max(s, .18), .3))
        elif l <= .30:
            return tok
        else:                                                    # accent text -> its deep shade, so it reads on white
            r, g, b = _hls(h, min(l, .20 + (1 - l) * .30), s * .9)
    elif role == "border":
        if grey:
            if l < .5:
                r, g, b = _hls(h, .80 + l * .35, min(s, .3))
            else:
                r, g, b = _ink(.10 + (1 - l) * .6)
        elif l < .35:
            r, g, b = _hls(h, .78 - l * .2, s)
        elif l > .6:
            r, g, b = _hls(h, .24 + (1 - l) * .40, s)
        else:
            return tok
    elif role == "shadow":
        if grey and l < .3:
            a *= .45
        elif grey:
            r, g, b = _ink(.12)
            a *= .8
        else:
            a *= .7
    else:                                                        # 'ink': SVG fills and strokes, chart lines, anything else
        if grey:
            if l < .5:
                r, g, b = _hls(h, .80 + l * .35, min(s, .3))
            else:
                r, g, b = _ink(.10 + (1 - l) * .62)
        elif l > .5:                                             # pale accent drawing -> the same colour, vivid and deeper
            r, g, b = _hls(h, .40 + (1 - l) * .2, s * .85)
        else:
            return tok
    return _fmt(r, g, b, a, tok)


# ---------------------------------------------------------------- colours in CSS, HTML and SVG
_TEXT_PROPS = {"color", "-webkit-text-fill-color", "caret-color", "text-decoration-color", "text-emphasis-color", "accent-color",
               "-webkit-text-stroke-color", "-webkit-text-stroke"}
_INK_ATTRS = {"fill", "stroke", "stop-color", "flood-color", "lighting-color"}
_KEEP_PROPS = {"mask", "mask-image", "-webkit-mask", "-webkit-mask-image"}


def _role(prop, block):
    p = prop.lower()
    if p in _KEEP_PROPS:
        return None
    if p in _TEXT_PROPS:
        return "text"
    if p.startswith("background"):
        return "text" if ("clip:text" in block or "clip: text" in block) else "bg"
    if p.startswith(("border", "outline", "column-rule", "scrollbar")):
        return "border"
    if p in ("box-shadow", "text-shadow", "filter", "-webkit-filter"):
        return "shadow"
    if p.startswith("--"):                                    # custom properties: by their name
        if any(k in p for k in ("bg", "back", "surface", "card", "panel", "fill-bg")):
            return "bg"
        if any(k in p for k in ("bd", "border", "line", "edge", "ring")):
            return "border"
        if any(k in p for k in ("fg", "text", "ink", "color", "c-")):
            return "text"
        return "ink"
    return "ink"


_BLOCK_CH = re.compile(r"[;{}<>]")


def _block(s, i):
    """The CSS rule (or style attribute) around position i, for the clip:text and coloured-button checks."""
    a = max(0, i - 1500)
    lo = max(s.rfind("{", a, i), s.rfind('style="', a, i), s.rfind("style='", a, i), s.rfind("}", a, i))
    q = '"' if s.rfind('style="', a, i) >= s.rfind("style='", a, i) else "'"
    hi_brace, hi_quote = s.find("}", i, i + 1500), s.find(q, i, i + 1500)
    his = [x for x in (hi_brace, hi_quote) if x >= 0]
    return s[max(0, lo):(min(his) if his else min(len(s), i + 400))]


def _on_colour(block):
    """True when the rule also paints a strong colour behind its text (a blue button, a coloured avatar): white text stays."""
    for m in re.finditer(r"background(?:-color|-image)?\s*:([^;}]*)", block):
        for t in COLOR.findall(m.group(1)):
            c = _parse(t)
            if not c:
                continue
            r, g, b, a = c
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            if max(r, g, b) - min(r, g, b) >= .25 and .22 < l < .75 and a >= .6:
                return True
    return False


def _context(s, i):
    """(kind, name) of the colour at s[i]: ('css', property) or ('attr', attribute) or (None, None)."""
    lo = max(0, i - 600)
    w = s[lo:i]
    cut = -1
    for m in _BLOCK_CH.finditer(w):
        cut = m.start()
    k = max(w.rfind('style="'), w.rfind("style='"))
    if k >= 0 and k + 6 > cut:
        cut = k + 6
    seg = w[cut + 1:]
    m = re.match(r"\s*(--[\w-]+|-?[a-zA-Z][\w-]*)\s*:", seg)
    if m and "=" not in seg[:m.end()]:
        return "css", m.group(1)
    m = re.search(r"([a-zA-Z][\w-]*)\s*=\s*[\"']?\s*$", seg)
    if m:
        return "attr", m.group(1)
    return None, None


def _in_style(s, i):
    """True inside a <style> element (a colour there with no property around it is still a colour)."""
    return s.rfind("<style", 0, i) > s.rfind("</style", 0, i)


@lru_cache(maxsize=96)
def _convert_cached(s):
    return _convert(s)


def convert(s):
    """Every colour in a piece of CSS / HTML / SVG, turned into its light-look counterpart by what it does.
    Style sheets (the same text every run) are remembered; page HTML (new numbers every run) is converted as it comes."""
    if not s or ("#" not in s and "rgb" not in s):
        return s
    return _convert_cached(s) if "<style" in s else _convert(s)


_KEEP = re.compile(r'<style data-lm="keep">.*?</style>', re.S)


def _convert(s):
    out, last = [], 0
    keep = [(k.start(), k.end()) for k in _KEEP.finditer(s)] if 'data-lm="keep"' in s else []
    for m in COLOR.finditer(s):
        i = m.start()
        if keep and any(a <= i < b for a, b in keep):
            continue                                         # written for the light look already
        kind, name = _context(s, i)
        tok = m.group(0)
        if kind == "css":
            blk = _block(s, i)
            role = _role(name, blk)
            if role is None:
                continue
            if role == "text" and name.lower() == "color" and _on_colour(blk):
                continue                                     # white text on a coloured button keeps its white
        elif kind == "attr":
            n = name.lower()
            if n in _INK_ATTRS:
                role = "ink"
            elif n in ("color", "bgcolor"):
                role = "text" if n == "color" else "bg"
            elif n == "style":
                role = "ink"
            else:
                continue                                     # href="#abc", id="..." and the like
        elif _in_style(s, i):
            role = "ink"
        else:
            continue                                         # "#123" in a sentence is not a colour
        out.append(s[last:i])
        out.append(color(tok, role))
        last = m.end()
    if not out:
        return s
    out.append(s[last:])
    return "".join(out)


def css(decl):
    """A short style string (a pandas Styler cell, an inline style) in the current look."""
    return convert(decl) if on() and isinstance(decl, str) else decl


def html(s):
    return convert(s) if on() and isinstance(s, str) else s


# ---------------------------------------------------------------- Plotly charts
_PLOTLY_BG = ("bgcolor", "paper_bgcolor", "plot_bgcolor", "fillcolor")
_PLOTLY_LINE = ("gridcolor", "linecolor", "zerolinecolor", "bordercolor", "tickcolor", "spikecolor", "outlinecolor")


def _plotly_walk(o, key="", parent=""):
    if isinstance(o, dict):
        return {k: _plotly_walk(v, k, key) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_plotly_walk(v, key, parent) for v in o]
    if isinstance(o, str) and ("#" in o or "rgb" in o) and COLOR.fullmatch(o.strip() or "x"):
        k = key.lower()
        if k in _PLOTLY_BG:
            return color(o.strip(), "bg")
        if k in _PLOTLY_LINE:
            return color(o.strip(), "border")
        if k == "color" and parent.lower() in ("font", "tickfont", "title", "titlefont", "textfont", "insidetextfont", "outsidetextfont", "hoverlabel"):
            return color(o.strip(), "text")
        return color(o.strip(), "ink")
    if isinstance(o, str) and "<" in o and ("#" in o or "rgb" in o):   # rich text (annotations): <span style="color:...">
        return convert(o)
    return o


def figure(fig):
    """A Plotly figure in the current look (a copy; the dark figure itself is untouched)."""
    if not on() or fig is None:
        return fig
    try:
        import plotly.graph_objects as go
        d = _plotly_walk(fig.to_plotly_json())
        out = go.Figure(d, skip_invalid=True)
        return out
    except Exception:
        return fig


# ---------------------------------------------------------------- hooks: every st.markdown / st.html on the way out
_STYLE_BLOCK = re.compile(r"<style[^>]*>.*?</style>", re.S | re.I)
_STYLE_START = re.compile(r"(?<=[^\n])(<style\b)", re.I)
_BLANK = re.compile(r"\n[ \t]*(?:\n[ \t]*)+")


def tidy_styles(body):
    """Markdown reads a <style> as styles only when it starts a line and runs without a blank line: otherwise the rest of it
    shows on the page as text (it happened after "</style><style>" and a blank line in the Arabic styles of Paper Bots)."""
    if "<style" not in body:
        return body
    body = _STYLE_START.sub(r"\n\1", body)
    return _STYLE_BLOCK.sub(lambda m: _BLANK.sub("\n", m.group(0)), body)


def _body(name, body, a, k):
    """The body to send (HTML and styles only; plain Markdown text is left alone): styles kept whole, a "?" after every trading
    term (terms.py), and the colours converted while the light look is on."""
    if isinstance(body, str) and (name == "html" or k.get("unsafe_allow_html") or (a and a[0] is True)):
        try:
            body = tidy_styles(body)
        except Exception:
            pass
        try:
            import terms
            body = terms.annotate(body)
        except Exception:
            pass
        if on():
            return convert(body)
    return body


def _live():
    """This module as it is now (after a reload the hooks installed earlier use the new code)."""
    return sys.modules.get(__name__) or sys.modules.get("lightmode")


def _wrap_dg(name):
    from streamlit.delta_generator import DeltaGenerator as DG
    orig = getattr(DG, name, None)
    if orig is None or getattr(orig, "_lm", False):
        return

    def patched(self, body, *a, **k):
        return orig(self, _live()._body(name, body, a, k), *a, **k)
    patched._lm = True
    patched.__wrapped__ = orig
    setattr(DG, name, patched)


def _wrap_module(name):
    orig = getattr(st, name, None)
    if orig is None or getattr(orig, "_lm", False):
        return

    def patched(body, *a, **k):
        return orig(_live()._body(name, body, a, k), *a, **k)
    patched._lm = True
    patched.__wrapped__ = orig
    setattr(st, name, patched)


def install():
    """Route st.markdown / st.html (and their column / container versions) through convert() while the light look is on."""
    for n in ("markdown", "html"):
        for wrap in (_wrap_dg, _wrap_module):
            try:
                wrap(n)
            except Exception:
                pass


# ---------------------------------------------------------------- the page behind everything, in the light look
BG_FILE = "bg_markets_light.jpg"     # the site's background picture in light tones (static/, made from bg_markets.jpg)
BG_CDN = f"https://cdn.jsdelivr.net/gh/abdulrahmanalturify-boop/trading-bot-v5@main/static/{BG_FILE}"


def background_css(url, calm=False):
    """The same globe picture as the dark look, in light tones (its lightness turned over, its colours kept: a pale lavender
    sky, the globe and the market numbers in dark dots), under a light veil that deepens a little towards the bottom."""
    veil = ("linear-gradient(180deg, rgba(246,244,251,.56) 0%, rgba(246,244,251,.64) 45%, rgba(246,244,251,.76) 100%)" if calm else   # a reading page
            "linear-gradient(180deg, rgba(246,244,251,.16) 0%, rgba(246,244,251,.26) 45%, rgba(246,244,251,.46) 100%)")
    keep_white = (".lg, .lgo .ini, .nth.fb .ms, .nth.fb em, .nth img::after, .sax .sx-ic, .sax .sx-ic .ms, "   # white letters on a coloured tile stay white
                  ".rbtl .ti .ms, .rbstep .n .ms, .rbo.on .ic .ms, .rbo.on .ck .ms, "
                  '[data-testid="stTabs"] [role="tab"][data-selected], [data-testid="stTabs"] [role="tab"][data-selected] [role="img"]')
    return (f'<style data-lm="keep">:root {{ color-scheme: light; }} {keep_white} {{ color: white !important; }}'
            f'.stApp::before {{ background: {veil}, url("{url}") 68% 40% / cover no-repeat, #F6F4FB !important; }}'
            f'.stApp::after {{ background: none !important; }}'
            f'@media (max-width: 768px) {{ .stApp::before {{ background-position: 0 0, 72% 30%; }} }}</style>')


def landing_css():
    """The landing keeps its night while Streamlit's own widgets are in the light theme: the few of them that sit on the
    landing's dark menus (the page links, the language buttons) get the night's light text back."""
    try:
        light_theme = st.session_state.get(THEME_KEY) == "light"
    except Exception:
        light_theme = False
    if not light_theme or on():
        return ""
    return ('<style>[class*="st-key-navdd_"] [data-testid="stPageLink"] a, [class*="st-key-navdd_"] [data-testid="stPageLink"] a *, '
            '.st-key-langdd button, .st-key-langdd button * { color: #E7E3EB !important; }</style>')


BUILD = "22.5.1"
