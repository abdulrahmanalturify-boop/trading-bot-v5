"""
mascot.py - Kuhailan (كحيلان), the site's robot: the face of the AI assistant and of everything to do with bots.

A small white robot with a dark visor and two glowing cyan eyes, an antenna with a light on top, round ears and a chest light,
floating a little (CSS). Drawn once here as SVG and used everywhere: the AI button at the foot of the page and the chat
window's head (ai_assistant), the home page's AI and bot cards (p_overview, promo), and the bot pages' heads (p_paper,
p_scanner, p_xbots). svg() gives the picture inline; data_uri() gives it as a CSS background image; CSS floats it.
The picture is the same in the dark and the light look (data-lm="keep").
"""
from urllib.parse import quote

BUILD = "23.4.39"

NAME = ("Kuhailan", "كحيلان")
ASK = ("Ask Kuhailan", "اسأل كحيلان")

_N = 0


def svg(size=64, cls="khl", uid=None, glow=True):
    """The robot as inline SVG, `size` px wide (its height follows); `uid` keeps the gradient ids apart when several are on
    one page (one is made up when none is given)."""
    global _N
    if uid is None:
        _N += 1
        uid = f"k{_N}"
    g = f"url(#{uid}g)"
    aura = (f'<ellipse cx="60" cy="112" rx="26" ry="5" fill="rgba(46,110,255,.22)"/>' if glow else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="{cls}" viewBox="0 0 120 120" width="{size}" height="{size}" aria-hidden="true" role="img">'
            f'<defs><linearGradient id="{uid}g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#D9E1F4"/></linearGradient>'
            f'<linearGradient id="{uid}v" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1B2A5C"/><stop offset="1" stop-color="#0B1230"/></linearGradient>'
            f'<radialGradient id="{uid}e" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#E9FFFF"/><stop offset=".45" stop-color="#5EF0FF"/><stop offset="1" stop-color="#1FB6E6"/></radialGradient>'
            f'<radialGradient id="{uid}h" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#5EF0FF" stop-opacity=".85"/><stop offset="1" stop-color="#5EF0FF" stop-opacity="0"/></radialGradient></defs>'
            f'{aura}'
            # antenna
            f'<path d="M60 26 V14" stroke="#B8C4E0" stroke-width="3.2" stroke-linecap="round"/>'
            f'<circle class="khl-tip" cx="60" cy="11" r="5.2" fill="url(#{uid}e)"/><circle cx="60" cy="11" r="9" fill="url(#{uid}h)"/>'
            # ears
            f'<rect x="12" y="44" width="11" height="22" rx="5.5" fill="#3B82F6"/><rect x="97" y="44" width="11" height="22" rx="5.5" fill="#3B82F6"/>'
            # head
            f'<rect x="20" y="24" width="80" height="60" rx="24" fill="{g}"/>'
            f'<rect x="28" y="33" width="64" height="40" rx="18" fill="url(#{uid}v)"/>'
            f'<path d="M34 40 Q60 30 86 40" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="3" stroke-linecap="round"/>'
            # eyes
            f'<ellipse class="khl-eye" cx="46" cy="53" rx="7.5" ry="8.5" fill="url(#{uid}e)"/><ellipse class="khl-eye" cx="74" cy="53" rx="7.5" ry="8.5" fill="url(#{uid}e)"/>'
            f'<circle cx="46" cy="53" r="13" fill="url(#{uid}h)"/><circle cx="74" cy="53" r="13" fill="url(#{uid}h)"/>'
            f'<path d="M52 66 Q60 70 68 66" fill="none" stroke="#5EF0FF" stroke-width="2.2" stroke-linecap="round" opacity=".8"/>'
            # neck + body
            f'<rect x="50" y="83" width="20" height="8" fill="#B8C4E0"/>'
            f'<rect x="36" y="88" width="48" height="26" rx="13" fill="{g}"/>'
            f'<circle cx="60" cy="101" r="5" fill="url(#{uid}e)"/><circle cx="60" cy="101" r="9" fill="url(#{uid}h)"/>'
            # arms
            f'<rect class="khl-arm" x="24" y="92" width="11" height="18" rx="5.5" fill="#E6ECF8"/><rect x="85" y="92" width="11" height="18" rx="5.5" fill="#E6ECF8"/>'
            f'</svg>')


def data_uri(size=120, glow=False):
    """The robot as a CSS url(): one picture, no ids to clash."""
    return "url(\"data:image/svg+xml," + quote(svg(size, "k", uid="kd", glow=glow), safe="") + "\")"


CSS = """
<style data-lm="keep">
@keyframes khlfloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}
@keyframes khlblink{0%,92%,100%{transform:scaleY(1)}96%{transform:scaleY(.1)}}
@keyframes khltip{0%,100%{opacity:1}50%{opacity:.45}}
svg.khl{display:block;overflow:visible;animation:khlfloat 3.4s ease-in-out infinite}
svg.khl .khl-eye{transform-box:fill-box;transform-origin:center;animation:khlblink 5.5s ease-in-out infinite}
svg.khl .khl-tip{animation:khltip 1.6s ease-in-out infinite}
@media(prefers-reduced-motion:reduce){svg.khl,svg.khl .khl-eye,svg.khl .khl-tip{animation:none!important}}
</style>"""
