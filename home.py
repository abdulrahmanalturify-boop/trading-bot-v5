"""
home.py - The opening of the home page: the logo in a night sky, three glass cards (Paper Bots · Opportunity Hunter ·
Markets & Research) and under them two wide ones (the two most important headlines · the Academy). Each card opens its page.
"""
import streamlit as st

import data
import newsiq
import theme as T
import ui
from i18n import L, is_ar

BUILD = "20.3"

_LINE = "rgba(150,140,250,"
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&display=swap');
.st-key-czhero {{ position:relative; gap:0 !important; padding-bottom:26px; }}
.st-key-czhero > * {{ position:relative; z-index:1; }}
.st-key-czhero::before {{ content:""; position:absolute; z-index:0; pointer-events:none; top:0; bottom:0; left:4%; right:4%;
  background:
    linear-gradient({_LINE}.16),{_LINE}.16)) left 0 top 0 / 1px 100% no-repeat,
    linear-gradient({_LINE}.16),{_LINE}.16)) left 72px top 0 / 1px 100% no-repeat,
    repeating-linear-gradient(135deg,{_LINE}.12) 0 1px,transparent 1px 9px) left 0 top 0 / 72px 100% no-repeat,
    linear-gradient({_LINE}.16),{_LINE}.16)) right 0 top 0 / 1px 100% no-repeat,
    linear-gradient({_LINE}.16),{_LINE}.16)) right 72px top 0 / 1px 100% no-repeat,
    repeating-linear-gradient(135deg,{_LINE}.12) 0 1px,transparent 1px 9px) right 0 top 0 / 72px 100% no-repeat,
    linear-gradient({_LINE}.2),{_LINE}.03)) left 24% top 0 / 1px 100% no-repeat,
    linear-gradient({_LINE}.2),{_LINE}.03)) left 76% top 0 / 1px 100% no-repeat;
  -webkit-mask-image: linear-gradient(180deg,#000 55%,transparent); mask-image: linear-gradient(180deg,#000 55%,transparent); }}
.st-key-czhero [data-testid="stHorizontalBlock"] {{ align-items:flex-start; }}

/* the logo in the sky */
.cztop {{ position:relative; text-align:center; padding:40px 12px 34px; }}
.cztop .czline {{ position:absolute; left:0; right:0; top:0; height:1px;
  background:linear-gradient(90deg,transparent,{_LINE}.36) 18%,{_LINE}.36) 82%,transparent); }}
.cztop .czglint {{ position:absolute; top:-30px; left:59%; width:60px; height:60px; pointer-events:none; animation:czglint 5s ease-in-out infinite; }}
@keyframes czglint {{ 0%,100% {{ opacity:.75; transform:scale(.92) rotate(0deg); }} 50% {{ opacity:1; transform:scale(1.08) rotate(12deg); }} }}
.cztop .czghost {{ position:absolute; left:0; right:0; top:10px; display:flex; justify-content:center; pointer-events:none; user-select:none; }}
.cztop .czghost .brand {{ height:clamp(58px,10.5vw,168px); width:auto; max-width:96%; }}
.cztop .czlogo {{ position:relative; display:flex; justify-content:center; align-items:center; gap:clamp(14px,1.8vw,28px); direction:ltr;
  margin-top:clamp(18px,3.4vw,58px); }}
.cztop .czlogo svg.czmark {{ flex:none; width:clamp(72px,7.6vw,122px); height:auto; filter:drop-shadow(0 0 22px rgba(45,182,235,.55)); }}
.cztop .czlogo .brand {{ height:clamp(30px,4.4vw,64px); width:auto; max-width:66vw; filter:drop-shadow(0 0 16px rgba(91,140,255,.35)); }}
.cztop .cztag {{ position:relative; margin-top:18px; font-size:.8rem; font-weight:600; letter-spacing:.26em; text-transform:uppercase; color:#A69ED0; }}
.cztop.ar .cztag {{ letter-spacing:0; font-size:.95rem; }}
.cztop .czchips {{ position:relative; display:flex; justify-content:center; gap:10px; flex-wrap:wrap; margin-top:18px; direction:ltr; }}
.cztop .czchips .chip {{ display:inline-flex; align-items:center; gap:7px; background:rgba(26,22,36,.88); border:1px solid {_LINE}.22);
  backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px); border-radius:999px; padding:6px 8px 6px 13px; font-size:.8rem; color:#D2CCEB;
  font-variant-numeric:tabular-nums; }}
.cztop .czchips .chip b {{ color:#fff; font-weight:600; letter-spacing:.04em; }}
.cztop .czchips .chip .pill {{ min-width:0; padding:2px 8px; font-size:.74rem; border-radius:999px; }}
.cztop .czarc {{ position:absolute; left:30%; width:40%; bottom:-118px; height:130px; pointer-events:none; }}

/* the calls to action under the logo: side by side in the middle */
.st-key-czcta {{ flex-direction:row !important; flex-wrap:wrap; justify-content:center; align-items:center; gap:12px !important; margin:-6px 0 34px; }}
.st-key-czcta .stElementContainer {{ width:auto !important; flex:none; }}
.st-key-czcta button {{ min-height:44px; padding:0 22px; border-radius:10px; }}
.st-key-czcta button p {{ font-size:.95rem; }}
/* the glass cards */
[class*="st-key-czcard_"] {{ position:relative; }}
[class*="st-key-czcard_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-czcard_"] [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}
[class*="st-key-czcard_"] [class*="st-key-czgo_"] {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; width:auto !important; }}
[class*="st-key-czcard_"] [class*="st-key-czgo_"] .stButton, [class*="st-key-czcard_"] [class*="st-key-czgo_"] button
  {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}
.czframe {{ padding:7px; border-radius:26px; border:1px solid {_LINE}.24); background:rgba(18,13,30,.55);
  transition:transform .25s ease, box-shadow .25s ease, border-color .25s ease; }}
[class*="st-key-czcard_"]:hover .czframe {{ transform:translateY(-6px); border-color:{_LINE}.45); box-shadow:0 30px 80px -30px rgba(79,107,255,.6); }}
.czcard {{ box-sizing:border-box; border-radius:20px; border:1px solid {_LINE}.18);
  background:{T.TOP}, linear-gradient(180deg,#16112A 0%,#120D1F 55%,#0E0918 100%); box-shadow:inset 0 1px 0 rgba(255,255,255,.06);
  padding:14px 20px 18px; display:flex; flex-direction:column; gap:9px; }}
.czcard svg.czill {{ display:block; width:100%; max-width:330px; height:auto; margin:0 auto; overflow:visible; }}
.czcard .czt {{ margin:0 0 6px; text-align:center; font-size:1.9rem; font-weight:500; letter-spacing:-.01em; line-height:1.14; color:#fff; }}
.czcard .czem {{ font-family:'Instrument Serif',Georgia,serif; font-style:italic; font-weight:400; font-size:1.2em; letter-spacing:0; }}
.czcard.ar .czt {{ font-weight:600; letter-spacing:0; line-height:1.4; }}
.czcard.ar .czem {{ font-family:'Readex Pro',sans-serif; font-style:normal; font-weight:600; font-size:1em;
  background:linear-gradient(90deg,#8FB0FF,#B9A6FF 60%,#67E8F9); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.czcard .czp {{ padding:12px 16px; border-radius:12px; border:1px solid {_LINE}.24);
  background:linear-gradient(90deg,rgba(40,60,170,.18),rgba(96,74,230,.32)); text-align:center; font-size:.88rem; line-height:1.55; color:#C6C0E4;
  transition:border-color .2s ease, background .2s ease; }}
[class*="st-key-czcard_"]:hover .czp {{ border-color:{_LINE}.4); }}
.czcard .czgo {{ margin-top:auto; padding-top:4px; display:flex; justify-content:center; align-items:center; gap:6px; font-size:.84rem; font-weight:600;
  color:#9CC4F4; letter-spacing:.02em; }}
.czcard .czgo .ms {{ transition:transform .2s ease; }}
[class*="st-key-czcard_"]:hover .czgo {{ color:#fff; }}
[class*="st-key-czcard_"]:hover .czgo .ms {{ transform:translateX(4px); }}
.czcard.ar .czgo .ms {{ transform:scaleX(-1); }}
[class*="st-key-czcard_"]:hover .czcard.ar .czgo .ms {{ transform:scaleX(-1) translateX(4px); }}
@media (min-width: 900px) {{ .st-key-czcard_hunt {{ margin-top:80px; }} }}

/* the two wide cards under them: news and the academy */
.st-key-czrow2 {{ margin-top:30px; }}
[class*="st-key-czcard_"]:hover .czframe.czwide {{ transform:none; }}
.czframe.czwide {{ container-type:inline-size; }}
.czwide .czcard {{ display:grid; grid-template-columns:minmax(200px,34%) minmax(0,1fr); gap:12px 22px; align-items:center; padding:16px 20px; }}
.czwide .czside {{ display:flex; flex-direction:column; align-items:center; gap:2px; }}
.czwide svg.czill {{ max-width:250px; }}
.czwide .czt {{ font-size:1.65rem; margin:0 0 2px; }}
.czwide .czgo {{ margin-top:2px; padding-top:0; }}
.czwide .czlist {{ display:flex; flex-direction:column; gap:10px; }}
.czn {{ position:relative; z-index:5; display:flex; gap:12px; align-items:center; padding:9px 11px; border-radius:12px; text-decoration:none !important;
  border:1px solid {_LINE}.24); background:linear-gradient(90deg,rgba(40,60,170,.18),rgba(96,74,230,.32)); transition:border-color .2s ease, background .2s ease; }}
.czn:hover {{ border-color:{_LINE}.6); background:linear-gradient(90deg,rgba(52,76,200,.26),rgba(110,84,240,.42)); }}
.czn .nth {{ width:88px; height:62px; border-radius:10px; }}
.czn .nth.fb .ms {{ font-size:30px; }} .czn .nth.fb em, .czn .nth .nlg {{ display:none; }}
.czn .nb {{ flex:1; min-width:0; display:flex; flex-direction:column; gap:3px; }}
.czn .t {{ color:#F1EEFA; font-weight:500; font-size:.9rem; line-height:1.5; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
  overflow:hidden; text-align:start; }}
.czn:hover .t {{ color:#fff; }}
.czn .meta {{ color:#9A93BE; font-size:.74rem; display:flex; align-items:center; gap:4px; }}
.czn .meta .ms {{ font-size:.9rem; }}
.czn .sc {{ flex:none; min-width:46px; text-align:center; border-radius:10px; padding:5px 6px 4px; font-weight:600; font-size:1rem; line-height:1.1;
  background:var(--iqb); color:var(--iqf); border:1px solid var(--iqd); direction:ltr; font-variant-numeric:tabular-nums; }}
.czn .sc small {{ display:block; font-size:.58rem; font-weight:600; opacity:.75; margin-top:1px; }}
/* a narrow wide card (small screens, open sidebar): picture and title on top, the two boxes under them */
@container (max-width: 640px) {{
  .czwide .czcard {{ grid-template-columns:minmax(0,1fr); }}
  .czwide svg.czill {{ max-width:230px; }}
}}
@media (max-width: 899.98px) {{
  .st-key-czhero::before, .cztop .czarc {{ display:none; }}
  .czcard {{ min-height:0; }}
  .czwide .czcard {{ grid-template-columns:minmax(0,1fr); }}
}}
@media (max-width: 640px) {{
  .cztop {{ padding:34px 0 22px; }}
  .cztop .cztag {{ font-size:.66rem; letter-spacing:.16em; line-height:1.7; }}
  .cztop.ar .cztag {{ font-size:.85rem; letter-spacing:0; }}
  .cztop .czchips {{ flex-wrap:nowrap; justify-content:flex-start; overflow-x:auto; scrollbar-width:none; padding:2px 2px 4px;
    -webkit-mask-image:linear-gradient(90deg,#000 88%,transparent); mask-image:linear-gradient(90deg,#000 88%,transparent); }}
  .cztop .czchips::-webkit-scrollbar {{ display:none; }}
  .cztop .czchips .chip {{ flex:none; font-size:.74rem; padding:5px 7px 5px 11px; }}
  .czcard .czt {{ font-size:1.6rem; }}
  .czn .nth {{ width:78px; height:58px; }}
}}
@media (prefers-reduced-motion: reduce) {{ .cztop .czglint {{ animation:none; }} }}
</style>
"""

_GLINT = ('<svg class="czglint" viewBox="0 0 64 64" aria-hidden="true"><defs><radialGradient id="czGlintHalo" cx="50%" cy="50%" r="50%">'
          '<stop offset="0" stop-color="#7EA0FF" stop-opacity=".9"/><stop offset="1" stop-color="#3D5BFF" stop-opacity="0"/></radialGradient></defs>'
          '<circle cx="32" cy="32" r="22" fill="url(#czGlintHalo)"/>'
          '<path d="M32 6 L34.2 29.8 L58 32 L34.2 34.2 L32 58 L29.8 34.2 L6 32 L29.8 29.8 Z" fill="#E8EEFF"/>'
          '<path d="M32 18 L33 31 L46 32 L33 33 L32 46 L31 33 L18 32 L31 31 Z" fill="#FFFFFF" transform="rotate(45 32 32)" opacity=".55"/></svg>')

_ARC = ('<svg class="czarc" viewBox="0 0 600 130" preserveAspectRatio="none" aria-hidden="true">'
        '<path d="M0 128 Q300 -8 600 128" fill="none" stroke="#8EA2FF" stroke-opacity=".28" stroke-width="1.2" vector-effect="non-scaling-stroke"/>'
        '<path d="M40 128 Q300 22 560 128" fill="none" stroke="#8EA2FF" stroke-opacity=".1" stroke-width="1" vector-effect="non-scaling-stroke"/></svg>')


def _grid(p):
    """The faded grid and the glow shared by the three illustrations (ids prefixed per card)."""
    return (f'<defs><radialGradient id="{p}Fade" cx="50%" cy="48%" r="58%"><stop offset="0" stop-color="#fff" stop-opacity="1"/>'
            f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
            f'<mask id="{p}Mask"><rect width="392" height="250" fill="url(#{p}Fade)"/></mask>'
            f'<radialGradient id="{p}Glow" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#4F6BFF" stop-opacity=".8"/>'
            f'<stop offset=".45" stop-color="#3D4FE0" stop-opacity=".3"/><stop offset="1" stop-color="#1B2470" stop-opacity="0"/></radialGradient></defs>'
            f'<g mask="url(#{p}Mask)"><path d="M56 0V250M112 0V250M168 0V250M224 0V250M280 0V250M336 0V250M0 40H392M0 96H392M0 152H392M0 208H392" '
            f'fill="none" stroke="#8EA2FF" stroke-opacity=".24" stroke-width="1"/></g>')


def _svg(body):
    return f'<svg class="czill" viewBox="0 40 392 188" aria-hidden="true">{body}</svg>'


_W = 'fill="#FFFFFF"'
_CIRCUIT = 'fill="none" stroke="#DDE3FF" stroke-opacity=".8" stroke-width="1.4"'

ILL_BOTS = _svg(
    _grid("czb")
    + '<defs><linearGradient id="czbFill" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#B9A6FF"/><stop offset="1" stop-color="#5B6CFF"/></linearGradient></defs>'
    '<circle cx="196" cy="124" r="112" fill="url(#czbGlow)"/>'
    '<circle cx="196" cy="124" r="62" fill="none" stroke="#A9B8FF" stroke-opacity=".5" stroke-width="1.2"/>'
    '<circle cx="196" cy="124" r="46" fill="#18206A" fill-opacity=".45" stroke="#A9B8FF" stroke-opacity=".22"/>'
    '<path d="M196 84 V97" stroke="#D6DCFF" stroke-width="2" stroke-linecap="round"/><circle cx="196" cy="81" r="4" fill="#2DB6EB"/>'
    '<rect x="164" y="97" width="64" height="52" rx="15" fill="url(#czbFill)"/>'
    '<rect x="164" y="97" width="64" height="52" rx="15" fill="none" stroke="#FFFFFF" stroke-opacity=".55"/>'
    '<rect x="173" y="109" width="46" height="26" rx="11" fill="#120C1F" fill-opacity=".8"/>'
    '<circle cx="186" cy="122" r="4.5" fill="#2DB6EB"/><circle cx="206" cy="122" r="4.5" fill="#2DB6EB"/>'
    '<rect x="157" y="114" width="7" height="18" rx="3.5" fill="#8FA0FF"/><rect x="228" y="114" width="7" height="18" rx="3.5" fill="#8FA0FF"/>'
    f'<circle cx="164" cy="97" r="3" {_W}/><circle cx="228" cy="149" r="3" {_W}/>'
    f'<path d="M34 150 H92 V116 H134" {_CIRCUIT}/><circle cx="34" cy="150" r="2.6" {_W}/>'
    f'<path d="M360 150 V196 H262" {_CIRCUIT}/><circle cx="262" cy="196" r="2.6" {_W}/>')

ILL_HUNT = _svg(
    _grid("czh")
    + '<defs><pattern id="czhStripes" width="6" height="4" patternUnits="userSpaceOnUse"><rect width="6" height="4" fill="#B9B4FF"/>'
    '<rect y="3" width="6" height="1" fill="#6E69E6"/></pattern></defs>'
    '<circle cx="196" cy="126" r="112" fill="url(#czhGlow)"/>'
    '<ellipse cx="196" cy="152" rx="64" ry="21" fill="none" stroke="#A9B8FF" stroke-opacity=".75" stroke-width="1.4"/>'
    '<ellipse cx="196" cy="133" rx="64" ry="21" fill="none" stroke="#A9B8FF" stroke-opacity=".75" stroke-width="1.4"/>'
    '<path d="M132 112 V152 M260 112 V152" stroke="#A9B8FF" stroke-opacity=".75" stroke-width="1.4"/>'
    '<ellipse cx="196" cy="112" rx="64" ry="21" fill="url(#czhStripes)" stroke="#ECE9FF" stroke-width="1.4"/>'
    '<path d="M196 112 L260 112 A64 21 0 0 0 228 93.8 Z" fill="#2DB6EB" fill-opacity=".5"/>'
    '<ellipse cx="196" cy="112" rx="40" ry="13" fill="none" stroke="#FFFFFF" stroke-opacity=".6"/>'
    '<ellipse cx="196" cy="112" rx="17" ry="5.5" fill="none" stroke="#FFFFFF" stroke-opacity=".75"/>'
    '<circle cx="222" cy="103" r="10" fill="none" stroke="#2DB6EB" stroke-opacity=".6"/><circle cx="222" cy="103" r="4" fill="#2DB6EB"/>'
    f'<circle cx="196" cy="91" r="3" {_W}/><circle cx="132" cy="133" r="3" {_W}/><circle cx="260" cy="133" r="3" {_W}/><circle cx="196" cy="173" r="3" {_W}/>'
    f'<path d="M52 64 V110 H104 V140" {_CIRCUIT}/><circle cx="52" cy="64" r="2.6" {_W}/>'
    f'<path d="M150 216 H300" {_CIRCUIT}/><circle cx="150" cy="216" r="2.6" {_W}/>')

ILL_RESEARCH = _svg(
    _grid("czr")
    + '<defs><pattern id="czrStripes" width="4" height="6" patternUnits="userSpaceOnUse"><rect width="4" height="6" fill="#B9B4FF"/>'
    '<rect x="3" width="1" height="6" fill="#7A74EC"/></pattern>'
    '<filter id="czrBlur" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="12"/></filter></defs>'
    '<circle cx="200" cy="120" r="112" fill="url(#czrGlow)"/>'
    '<rect x="180" y="92" width="44" height="86" fill="#5B6CFF" opacity=".6" filter="url(#czrBlur)"/>'
    '<rect x="142" y="130" width="32" height="38" fill="none" stroke="#E6EAFF" stroke-width="1.6"/>'
    '<rect x="186" y="100" width="32" height="68" fill="url(#czrStripes)"/>'
    '<rect x="230" y="56" width="32" height="112" fill="none" stroke="#E6EAFF" stroke-width="1.6"/>'
    f'<circle cx="230" cy="56" r="3.4" {_W}/>'
    '<path d="M130 150 L178 124 L214 132 L270 78" fill="none" stroke="#2DB6EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity=".9"/>'
    '<circle cx="270" cy="78" r="3.6" fill="#2DB6EB"/>'
    f'<path d="M300 214 H352 V168" {_CIRCUIT}/><circle cx="352" cy="168" r="2.6" {_W}/>')

ILL_NEWS = _svg(
    _grid("czw")
    + '<defs><linearGradient id="czwFill" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#B9A6FF"/><stop offset="1" stop-color="#5B6CFF"/></linearGradient></defs>'
    '<circle cx="196" cy="134" r="112" fill="url(#czwGlow)"/>'
    '<rect x="170" y="82" width="96" height="112" rx="12" fill="#18206A" fill-opacity=".35" stroke="#A9B8FF" stroke-opacity=".5" stroke-width="1.2"/>'
    '<rect x="148" y="96" width="96" height="112" rx="12" fill="url(#czwFill)"/>'
    '<rect x="148" y="96" width="96" height="112" rx="12" fill="none" stroke="#FFFFFF" stroke-opacity=".55"/>'
    '<rect x="158" y="108" width="34" height="26" rx="5" fill="#120C1F" fill-opacity=".8"/>'
    '<path d="M162 130 L171 120 L178 126 L184 118 L189 130 Z" fill="#2DB6EB" fill-opacity=".8"/>'
    '<rect x="198" y="110" width="36" height="6" rx="3" fill="#FFFFFF" fill-opacity=".92"/>'
    '<rect x="198" y="122" width="26" height="6" rx="3" fill="#FFFFFF" fill-opacity=".6"/>'
    '<rect x="158" y="146" width="76" height="5" rx="2.5" fill="#120C1F" fill-opacity=".55"/>'
    '<rect x="158" y="158" width="64" height="5" rx="2.5" fill="#120C1F" fill-opacity=".55"/>'
    '<rect x="158" y="170" width="70" height="5" rx="2.5" fill="#120C1F" fill-opacity=".55"/>'
    '<rect x="158" y="182" width="46" height="5" rx="2.5" fill="#120C1F" fill-opacity=".55"/>'
    '<circle cx="262" cy="86" r="12" fill="none" stroke="#2DB6EB" stroke-opacity=".5"/><circle cx="262" cy="86" r="5" fill="#2DB6EB"/>'
    '<path d="M280 74 A20 20 0 0 1 280 98 M288 67 A30 30 0 0 1 288 105" fill="none" stroke="#2DB6EB" stroke-opacity=".7" stroke-width="1.6" stroke-linecap="round"/>'
    f'<circle cx="148" cy="96" r="3" {_W}/><circle cx="244" cy="208" r="3" {_W}/>'
    f'<path d="M40 178 H100 V142 H148" {_CIRCUIT}/><circle cx="40" cy="178" r="2.6" {_W}/>'
    f'<path d="M352 196 V160 H300" {_CIRCUIT}/><circle cx="300" cy="160" r="2.6" {_W}/>')

ILL_ACADEMY = _svg(
    _grid("cza")
    + '<defs><pattern id="czaStripes" width="6" height="4" patternUnits="userSpaceOnUse"><rect width="6" height="4" fill="#B9B4FF"/>'
    '<rect y="3" width="6" height="1" fill="#6E69E6"/></pattern>'
    '<linearGradient id="czaFill" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9C8BFF"/><stop offset="1" stop-color="#4F5FE6"/></linearGradient></defs>'
    '<circle cx="196" cy="130" r="112" fill="url(#czaGlow)"/>'
    '<path d="M148 124 V160 Q196 188 244 160 V124 L196 146 Z" fill="url(#czaFill)"/>'
    '<path d="M148 124 V160 Q196 188 244 160 V124" fill="none" stroke="#FFFFFF" stroke-opacity=".5"/>'
    '<polygon points="196,78 278,110 196,142 114,110" fill="url(#czaStripes)" stroke="#ECE9FF" stroke-width="1.4"/>'
    '<path d="M196 110 L262 124 V166" fill="none" stroke="#2DB6EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<circle cx="262" cy="172" r="6" fill="#2DB6EB"/><circle cx="262" cy="172" r="12" fill="none" stroke="#2DB6EB" stroke-opacity=".45"/>'
    f'<circle cx="196" cy="110" r="4" {_W}/><circle cx="114" cy="110" r="3" {_W}/><circle cx="278" cy="110" r="3" {_W}/>'
    f'<path d="M44 76 V126 H102" {_CIRCUIT}/><circle cx="44" cy="76" r="2.6" {_W}/>'
    f'<path d="M296 210 H350 V166" {_CIRCUIT}/><circle cx="350" cy="166" r="2.6" {_W}/>')


def cards():
    """(key, page to open, illustration, title, emphasised word, two lines break, two short texts) in the current language."""
    return [
        ("bots", "paper", ILL_BOTS, L("Paper", "البوتات"), L("Bots", "الافتراضية"), True,
         L("Build trading bots and run them on virtual money, with no real funds at risk.",
           "ابنِ بوتات تداول وشغّلها بأموال افتراضية، بدون أي مخاطرة بأموال حقيقية."),
         L("Forward tests save every signal and trade the moment it happens, with the strategy version.",
           "الاختبار الأمامي يحفظ كل إشارة وصفقة لحظة حدوثها، مع رقم إصدار الاستراتيجية.")),
        ("hunt", "scanner", ILL_HUNT, L("Opportunity", "صائد"), L("Hunter", "الفرص"), True,
         L("Scores every stock on trend, relative strength, accumulation, setup and reward-to-risk.",
           "يقيّم كل سهم حسب الاتجاه والقوة النسبية والتجميع ونمط الدخول ونسبة العائد إلى المخاطرة."),
         L("Analyst ratings, insider transactions, events and news for every pick in one view.",
           "تقييمات المحللين وصفقات المطّلعين والأحداث والأخبار لكل فرصة في مكان واحد.")),
        ("research", "stock", ILL_RESEARCH, L("Markets &amp;", "الأسواق"), L("Research", "والأبحاث"), True,
         L("Market overview, futures, options and the economy, with stock research and screeners.",
           "نظرة على السوق والعقود الآجلة والخيارات والاقتصاد، مع أبحاث الأسهم والفلاتر."),
         L("Earnings, economic, dividend and IPO calendars, plus courses in the Academy.",
           "تقاويم الأرباح والاقتصاد والتوزيعات والاكتتابات، ودورات الأكاديمية.")),
    ]


def top_html(chips_html=""):
    ar = is_ar()
    tag = L("Paper trading · Opportunity hunting · Market research", "تداول افتراضي · صيد الفرص · أبحاث السوق")
    chips = f'<div class="czchips">{chips_html}</div>' if chips_html else ""
    return (f'<div class="cztop{" ar" if ar else ""}"><div class="czline"></div>{_GLINT}'
            f'<div class="czghost" aria-hidden="true">{T.brand(None, "czgh", pro=None, color="rgba(150,170,255,.09)", label="")}</div>'
            f'<div class="czlogo">{T.logo_mark("czlg", "czmark")}{T.brand(None, "czbr")}</div>'
            f'<div class="cztag">{tag}</div>{chips}{_ARC}</div>')


def card_html(ill, t1, t2, two_lines, p1, p2):
    ar = is_ar()
    brk = "<br>" if two_lines and not ar else " "        # Arabic titles are short enough for one line
    go = L("Open", "افتح")
    return (f'<div class="czframe"><div class="czcard{" ar" if ar else ""}">{ill}'
            f'<div class="czt">{t1}{brk}<span class="czem">{t2}</span></div>'
            f'<div class="czp">{p1}</div><div class="czp">{p2}</div>'
            f'<div class="czgo">{go} <span class="ms">arrow_forward</span></div></div></div>')


# ---------------------------------------------------------------- the two wide cards
@st.cache_data(ttl=180, show_spinner=False)
def _top_news(ar):
    """The two most important headlines of the last 24 hours (the News page's default order), titles in Arabic when asked.
    Raises while the news bot has nothing yet, so an empty answer is never kept."""
    items = []
    try:
        import newsbot
        items = newsbot.bot(wait=False).items(24)
    except Exception:
        items = []
    if len(items) < 2:
        try:
            import pandas as pd
            cut = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=24)
            items = [n for n in data.market_news(24) if pd.notna(n.get("time")) and n["time"] >= cut]
        except Exception:
            items = []
    if not items:
        raise LookupError("no headlines yet")
    tick = sorted({s for n in items[:250] for s in n.get("tickers", [])})
    try:
        chg = data.quick_changes(tick) if tick else {}
    except Exception:
        chg = {}
    newsiq.enrich(items, chg)
    top = newsiq.rank(items)[:2]
    return [{"title": n["title"], "link": n.get("link", ""), "source": n.get("source", ""), "time": n.get("time"), "img": n.get("img"),
             "tickers": list(n.get("tickers") or []), "iq": n["iq"]} for n in top]


def top_news():
    try:
        items = [dict(n) for n in _top_news(False)]
    except Exception:
        return []
    if is_ar() and items:
        for n, t in zip(items, data.translate([n["title"] for n in items], budget=8)):
            n["title"] = t
    return items


def news_pane(n):
    """One headline, as on the News page: picture, title (opens the story), outlet · time, importance score."""
    ar = is_ar()
    sc = int(n["iq"]["score"])
    bg, fg, bd = newsiq.colors(sc)
    lv = newsiq.level(sc)
    return (f'<a class="czn" href="{T.esc(n["link"])}" target="_blank" rel="noopener">{T.news_thumb(n)}'
            f'<span class="nb"><span class="t" dir="auto">{T.esc(n["title"])}</span>'
            f'<span class="meta">{T.icon("schedule")} {T.esc(n["source"])} · {T.time_ago(n["time"], ar)}</span></span>'
            f'<span class="sc" style="--iqb:{bg};--iqf:{fg};--iqd:{bd}" title="{T.esc(L(*lv))}">{sc}<small>/10</small></span></a>')


def academy_texts():
    try:
        import academy as A
        import academy_labs as AL
        n, labs, terms = len(A.COURSES), len(AL.LABS), len(A.GLOSSARY)
        return (L(f"{n} courses from beginner to advanced, in Arabic and English, each ending with a short quiz.",
                  f"{n} دورة من المبتدئ إلى المتقدم، بالعربي والإنجليزي، وكل دورة تنتهي باختبار قصير."),
                L(f"{labs} interactive labs to try the ideas yourself, plus a glossary of {terms} market terms.",
                  f"{labs} مختبرات تفاعلية لتجربة الأفكار بنفسك، وقاموس فيه {terms} مصطلحاً من مصطلحات السوق."))
    except Exception:
        return (L("Courses from beginner to advanced, in Arabic and English, each ending with a short quiz.",
                  "دورات من المبتدئ إلى المتقدم، بالعربي والإنجليزي، وكل دورة تنتهي باختبار قصير."),
                L("Interactive labs to try the ideas yourself, plus a glossary of market terms.",
                  "مختبرات تفاعلية لتجربة الأفكار بنفسك، وقاموس لمصطلحات السوق."))


def wide_html(ill, t1, t2, body):
    ar = is_ar()
    go = L("Open", "افتح")
    return (f'<div class="czframe czwide"><div class="czcard{" ar" if ar else ""}"><div class="czside">{ill}'
            f'<div class="czt">{t1} <span class="czem">{t2}</span></div><div class="czgo">{go} <span class="ms">arrow_forward</span></div></div>'
            f'<div class="czlist">{body}</div></div></div>')


def news_html(items):
    if items:
        body = "".join(news_pane(n) for n in items[:2])
    else:
        body = (f'<div class="czp">{L("The news bot is collecting the latest headlines from 35 feeds. They appear here in a moment.", "بوت الأخبار يجمع آخر العناوين من 35 مصدراً، وتظهر هنا بعد لحظات.")}</div>')
    return wide_html(ILL_NEWS, L("Market", "أخبار"), L("News", "السوق"), body)


def academy_html():
    p1, p2 = academy_texts()
    return wide_html(ILL_ACADEMY, L("Learning", "الأكاديمية"), L("Academy", "التعليمية"), f'<div class="czp">{p1}</div><div class="czp">{p2}</div>')


def _card(key, page, html, label):
    with st.container(key=f"czcard_{key}"):
        ui.html(html)
        if st.button(label, key=f"czgo_{key}", width="stretch"):
            ui.goto(page)


def hero(chips_html=""):
    """The home page's opening. Each card is one big button that opens its page (a headline opens its story)."""
    with st.container(key="czhero"):
        ui.html(CSS + top_html(chips_html))
        with st.container(key="czcta"):                  # the two calls to action under the logo, as on n8n's home page
            if st.button(L("Build a bot", "ابنِ بوتك"), type="primary", icon=":material/smart_toy:", key="czcta_bot"):
                ui.goto("paper")
            if st.button(L("Today's opportunities", "فرص اليوم"), icon=":material/radar:", key="czcta_hunt"):
                ui.goto("scanner")
        cols = st.columns(3, gap="large")
        for col, (k, page, ill, t1, t2, two, p1, p2) in zip(cols, cards()):
            with col:
                _card(k, page, card_html(ill, t1, t2, two, p1, p2), f'{t1.replace("&amp;", "&")} {t2}')
        with st.container(key="czrow2"):
            a, b = st.columns(2, gap="large")
            with a:
                _card("news", "news", news_html(top_news()), L("Market News", "أخبار السوق"))
            with b:
                _card("academy", "academy", academy_html(), L("Learning Academy", "الأكاديمية التعليمية"))


# =====================================================================
# THE LANDING: the page a visit opens on, after Origin Financial's "nocturnal gallery": a full-screen dawn sky over a
# skyline of candles, then sections about the site and its parts, scrolling like a product page. "Get started" stays
# at the bottom in the middle all the way down and opens the home page as it was. The main top bar stays over the
# landing, see-through; after "Get started" it is back to normal. Shown once per visit (the logo brings it back).
# The motion (parallax, spotlight, typing line, reveals, tilting cards) is theme.FX_JS; without it everything still shows.
# =====================================================================


def _facts():
    """The numbers on the landing, read from the site itself (never typed in by hand)."""
    f = {"stocks": 500, "single": 0, "combined": 0, "bots": 10, "courses": 0, "labs": 0, "terms": 0}
    try:
        import sp500
        f["stocks"] = len(sp500.SP500)
    except Exception:
        pass
    try:
        import engine
        import playbooks
        f["single"], f["combined"] = len(engine.STRATEGIES), len(playbooks.PLAYBOOKS)
    except Exception:
        pass
    try:
        import paperbots
        f["bots"] = paperbots.MAX_BOTS
    except Exception:
        pass
    try:
        import academy as A
        import academy_labs as AL
        import terms
        f["courses"], f["labs"], f["terms"] = len(A.COURSES), len(AL.LABS), len(terms.glossary(A.GLOSSARY))
    except Exception:
        pass
    return f


INTRO_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Instrument+Serif:ital@0;1&family=Roboto+Mono:wght@400;500&display=swap');
/* while the landing shows: the page runs edge to edge under a see-through top bar, without the sidebar */
header[data-testid="stHeader"], header.stAppHeader, .stAppHeader, [data-testid="stHeader"] > div, [data-testid="stToolbar"] {
  background: transparent !important; background-color: transparent !important; backdrop-filter: none !important; -webkit-backdrop-filter: none !important;
  border-bottom-color: transparent !important; box-shadow: none !important; transition: background .3s ease, backdrop-filter .3s ease; }
header[data-testid="stHeader"]::after, header[data-testid="stHeader"]::before { opacity: 0 !important; }
/* no dark strip on the right: the page scrolls without a visible bar while the landing shows */
[data-testid="stMain"], section.stMain, [data-testid="stAppViewContainer"], .stApp { scrollbar-width: none !important; }
[data-testid="stMain"]::-webkit-scrollbar, section.stMain::-webkit-scrollbar, [data-testid="stAppViewContainer"]::-webkit-scrollbar { width: 0 !important; height: 0 !important; }
html.ix-scrolled header[data-testid="stHeader"] { background: rgba(14,9,24,.32) !important; background-color: rgba(14,9,24,.32) !important;
  backdrop-filter: blur(14px) !important; -webkit-backdrop-filter: blur(14px) !important; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
.st-key-navsearch [role="group"], .st-key-navsearch [data-baseweb="select"] > div, .st-key-navsearch [data-baseweb="input"],
.st-key-navsearch [data-baseweb="base-input"], .st-key-navsearch input, .st-key-navright .status, .langbtn, .navbtn.on {
  background: transparent !important; background-color: transparent !important; backdrop-filter: none !important; box-shadow: none !important; }
.st-key-navsearch [role="group"], .st-key-navsearch [data-baseweb="select"] > div, .st-key-navsearch [data-baseweb="input"],
.st-key-navright .status, .langbtn, .navbtn.on { border: 1px solid rgba(255,255,255,.28) !important; }
.st-key-navsearch input::placeholder { color: rgba(255,255,255,.7) !important; }
.st-key-langsec:hover .langbtn, [class*="st-key-navsec_"]:hover .navbtn { background: rgba(255,255,255,.08) !important; }
.block-container, [data-testid="stMainBlockContainer"], [data-testid="stMainBlockContainer"]:has(.st-key-topnav) { max-width: none !important;
  padding: 0 !important; }
@media (max-width: 1023.98px) { .st-key-topnav { margin: 22px 8px 8px !important; } }   /* phones: a little under the top line (the page's script sets the exact gap) */
.ixp { margin-top: -1rem; color: #F5F5F7; font-family: 'DM Sans', 'Readex Pro', system-ui, sans-serif; overflow: hidden; isolation: isolate;
  background: linear-gradient(180deg, #14101A 0%, #14101A 12%, #150F22 22%, #160E28 36%, #130D24 52%, #170F2C 68%, #110B21 84%, #0E0918 100%); }
.ixs::before { content: ""; position: absolute; z-index: -1; pointer-events: none; top: -10%; width: 80vw; height: 120%; left: -40vw;
  background: radial-gradient(closest-side, rgba(74,20,140,.20), rgba(74,20,140,.06) 55%, transparent 80%); }
.ixs:nth-of-type(2n)::before { left: auto; right: -40vw; background: radial-gradient(closest-side, rgba(40,112,132,.14), rgba(40,112,132,.04) 55%, transparent 80%); }
.ixend::before { content: ""; position: absolute; z-index: -1; left: 50%; bottom: 0; width: 110vw; height: 90%; margin-left: -55vw; pointer-events: none;
  background: radial-gradient(closest-side, rgba(74,20,140,.35), transparent 78%); }
.ixend { position: relative; }
.ixp.ar { font-family: 'Readex Pro', 'DM Sans', sans-serif; }
/* ---------- the first screen: a violet-lit void, a slowly turning iridescent sculpture, two lines of words ---------- */
.ix { position: relative; min-height: 100vh; overflow: hidden; background: #180B2C; }
/* the first screen melts into the page under it: no hard line between the two */
.ix::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 34vh; z-index: 3; pointer-events: none;
  background: linear-gradient(180deg, rgba(20,16,26,0) 0%, rgba(20,16,26,.55) 55%, #14101A 100%); }
.ix > * { position: absolute; }
.ix-glow { inset: -6%; pointer-events: none; transform: translate3d(calc(var(--px,0) * -16px), calc(var(--py,0) * -10px), 0); }
.ix-glow i { position: absolute; inset: 0; }
/* Letter's colour field, with its red turned very dark violet: a wide wash over the upper left and the middle, a
   teal-grey haze low on the left, near-black on the right, a cold bloom where the sculpture stands */
.ix-glow .g1 { background: radial-gradient(ellipse 110% 130% at 40% 22%, #230E42 0%, #200D3C 22%, #1D0C36 42%, #1A0B30 62%, #180B2C 82%, transparent 96%);
  animation: ixbreath 11s ease-in-out infinite alternate; }
.ix-glow .g2 { background: radial-gradient(ellipse 42% 70% at -4% 82%, #23384A 0%, rgba(35,56,74,.8) 34%, rgba(35,54,72,.3) 60%, transparent 82%);
  animation: ixdrift 19s ease-in-out infinite alternate; }
.ix-glow .g3 { background: radial-gradient(ellipse 62% 95% at 104% 6%, #0C0B0F 0%, rgba(12,11,15,.92) 36%, rgba(12,11,15,.45) 62%, transparent 82%); }
.ix-glow .g4 { background: radial-gradient(ellipse 30% 26% at 50% 104%, rgba(126,129,170,.75) 0%, rgba(92,76,140,.4) 42%, transparent 76%);
  animation: ixbreath 7s ease-in-out -3s infinite alternate; }
@keyframes ixbreath { 0% { transform: scale(1) translate(0,0); opacity: .9; } 100% { transform: scale(1.06) translate(1.5%,1.5%); opacity: 1; } }
@keyframes ixdrift { 0% { transform: translate(0,0) scale(1); } 100% { transform: translate(3vw,-3vh) scale(1.08); } }
.ix-grain { inset: 0; pointer-events: none; opacity: .07; mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>"); }
.ix-sc { left: 50%; bottom: -9vh; width: min(820px, 92vw); height: 50vh; translate: -50% 0; pointer-events: none;
  transform: translate3d(calc(var(--px,0) * -14px), calc(var(--py,0) * -8px), 0);
  opacity: 0; animation: ixrise 2.4s cubic-bezier(.455,.03,.515,.955) .5s forwards; }
@keyframes ixrise { from { opacity: 0; filter: blur(14px); translate: -50% 60px; } to { opacity: 1; filter: none; translate: -50% 0; } }
.ix-sc .ix-gl { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
.ix-sc .ix-gem { position: absolute; left: 50%; bottom: 8%; width: 44%; translate: -50% 0; animation: ixturn 14s ease-in-out infinite alternate; }
.ix-sc.gl-on .ix-gem { display: none; }                                    /* the WebGL sculpture replaces the drawing */
@keyframes ixturn { 0% { transform: rotate(-4deg) scale(1); } 100% { transform: rotate(5deg) scale(1.04); } }
.ix-fl { position: absolute; z-index: 2; width: 150px; height: 150px; translate: -50% -50%; opacity: 0; mix-blend-mode: screen;
  background: radial-gradient(closest-side, #FFFFFF, rgba(255,255,255,.85) 12%, rgba(220,230,255,.35) 32%, transparent 70%);
  animation: ixflare 5.5s ease-in-out infinite; }
.ix-fl::after { content: ""; position: absolute; left: -60%; right: -60%; top: 50%; height: 2px; margin-top: -1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.75), transparent); filter: blur(.4px); }
.ix-fl.f1 { left: 29%; top: 44%; animation: ixglow 4.8s ease-in-out infinite; }
.ix-fl.f2 { left: 64%; top: 84%; width: 120px; height: 120px; animation: ixglow 5.6s ease-in-out -2s infinite; }
.ix-fl.f3 { left: 46%; top: 30%; width: 54px; height: 54px; animation-delay: 3.8s; }
.ix-fl.f3::after { display: none; }
.ix-fl.f4 { left: 37%; top: 66%; width: 70px; height: 70px; animation-delay: 1.2s; }
.ix-gl-o, .ix-gl-b { position: absolute; z-index: 2; width: 26px; height: 26px; translate: -50% -50%; border-radius: 50%; opacity: 0; mix-blend-mode: screen;
  animation: ixflare 4.6s ease-in-out infinite; }
.ix-gl-o { left: 58%; top: 70%; background: radial-gradient(closest-side, #FFB054, rgba(255,140,40,.4) 45%, transparent 75%); animation-delay: 1.6s; }
.ix-gl-b { left: 40%; top: 80%; background: radial-gradient(closest-side, #8EC5FF, rgba(80,150,255,.4) 45%, transparent 75%); animation-delay: 3.1s; }
@keyframes ixglow { 0%, 100% { opacity: .6; transform: scale(.9); } 45% { opacity: 1; transform: scale(1.08); } 70% { opacity: .75; transform: scale(.95); } }
@keyframes ixflare { 0%, 100% { opacity: 0; transform: scale(.6); } 35% { opacity: .95; transform: scale(1); } 55% { opacity: .55; transform: scale(.85); } 70% { opacity: 0; } }
.ix-center { left: 50%; top: 42%; width: min(980px, 92vw); transform: translate(-50%, -50%); text-align: center; z-index: 3;
  margin-top: var(--ixdrop, 0px); }                                  /* phones: moved under the menu card by the page's script */
.ix-h { margin: 0 0 20px; font-family: 'DM Serif Display', 'Instrument Serif', Georgia, serif; font-weight: 400; font-size: clamp(46px, 5.8vw, 86px);
  line-height: 1.08; letter-spacing: .02em; color: #FFFFFF; text-shadow: 0 12px 50px rgba(16,13,23,.55); }
.ix-h em, .ixh em { font-style: italic; background: linear-gradient(90deg, #D1C9FF, #9DCBF7 55%, #FFFFFF); -webkit-background-clip: text;
  background-clip: text; color: transparent; padding-inline-end: .06em; }
.ixp.ar .ix-h { font-family: 'Readex Pro', sans-serif; font-weight: 500; font-size: clamp(42px, 6vw, 92px); line-height: 1.25; letter-spacing: 0; }
.ixp.ar .ix-h em, .ixp.ar .ixh em { font-style: normal; font-weight: 400; }
.ix-sub { margin: 0 auto; max-width: 640px; font-size: clamp(16px, 1.35vw, 19px); line-height: 1.55; font-weight: 400; color: rgba(255,255,255,.84);
  text-shadow: 0 2px 18px rgba(20,6,40,.35); }
.ix-sub b { display: block; margin-top: 10px; font-weight: 500; color: rgba(255,255,255,.92); }
.ixp .ix-sub, .ixp .ixend .ixt { margin-left: auto !important; margin-right: auto !important; margin-bottom: 0 !important; }
.ixp .ix-center { text-align: center !important; }
.ixp.ar .ix-sub { font-size: clamp(17px, 1.4vw, 20px); line-height: 1.9; }
.ix-scroll { left: 50%; bottom: clamp(22px, 4.5vh, 44px); translate: -50% 0; z-index: 4; display: flex; flex-direction: column; align-items: center; gap: 10px;
  font-family: 'Roboto Mono', monospace; font-size: 11px; letter-spacing: .22em; text-transform: uppercase; color: rgba(245,245,247,.85);
  cursor: pointer; padding: 12px 20px 10px; border-radius: 16px; transition: color .2s ease, background .2s ease;
  background: transparent; border: 1px solid rgba(255,255,255,.28);
  opacity: 0; animation: ixin 1.6s cubic-bezier(.455,.03,.515,.955) 1.8s forwards; }
.ix-scroll:hover { color: #fff; background: rgba(255,255,255,.06); border-color: rgba(255,255,255,.55); }
.ix-scroll:hover i { border-color: #fff; }
.ixp.ar .ix-scroll { font-family: 'Readex Pro', sans-serif; letter-spacing: 0; font-size: 12px; }
.ix-scroll i { width: 24px; height: 38px; border: 1.5px solid rgba(245,245,247,.75); border-radius: 13px; position: relative; transition: border-color .2s ease; }
.ix-scroll i::after { content: ""; position: absolute; left: 50%; top: 7px; width: 3px; height: 7px; margin-left: -1.5px; border-radius: 2px; background: #fff;
  animation: ixwheel 1.8s ease-in-out infinite; }
@keyframes ixwheel { 0% { transform: translateY(0); opacity: 1; } 80% { transform: translateY(10px); opacity: 0; } 100% { opacity: 0; } }
.ix-center > * { opacity: 0; animation: ixin 1.8s cubic-bezier(.455,.03,.515,.955) forwards; }
.ix-center > :nth-child(1) { animation-delay: .15s; } .ix-center > :nth-child(2) { animation-delay: .55s; }
@keyframes ixin { from { opacity: 0; transform: translateY(14px); filter: blur(8px); } to { opacity: 1; transform: none; filter: none; } }
@keyframes ixdraw { to { stroke-dashoffset: 0; } }
@keyframes ixpulse { 0% { box-shadow: 0 0 0 0 rgba(74,222,128,.55); } 70% { box-shadow: 0 0 0 9px rgba(74,222,128,0); } 100% { box-shadow: 0 0 0 0 rgba(74,222,128,0); } }
/* ---------- the sections under it ---------- */
.ixs { position: relative; max-width: 1200px; margin: 0 auto; padding: 120px 24px 0; box-sizing: border-box; }
.ixl { font-family: 'Roboto Mono', monospace; font-size: 12px; letter-spacing: .18em; text-transform: uppercase; color: #D1C9FF;
  display: inline-flex; align-items: center; gap: 10px; }
.ixl::before { content: ""; width: 26px; height: 1px; background: currentColor; opacity: .6; }
.ixp.ar .ixl { font-family: 'Readex Pro', sans-serif; letter-spacing: 0; font-size: 13.5px; text-transform: none; }
.ixh { margin: 18px 0 16px; font-family: 'Instrument Serif', 'DM Serif Display', Georgia, serif; font-weight: 400; font-size: clamp(38px, 5vw, 72px);
  line-height: .98; letter-spacing: -.02em; color: #F5F5F7; }
.ixp.ar .ixh { font-family: 'Readex Pro', sans-serif; font-weight: 300; font-size: clamp(32px, 3.8vw, 56px); line-height: 1.3; letter-spacing: 0; }
.ixt { font-size: 17px; line-height: 1.7; font-weight: 300; color: rgba(245,245,247,.62); max-width: 560px; }
.ixp.ar .ixt { font-size: 17.5px; line-height: 1.95; }
.ix-state { text-align: center; }
.ix-state .ixh { font-size: clamp(34px, 4.4vw, 64px); max-width: 980px; margin: 22px auto 0; line-height: 1.08; }
.ix-state .ixh span { color: rgba(245,245,247,.38); }
.ixp.ar .ix-state .ixh { font-size: clamp(28px, 3.2vw, 48px); line-height: 1.5; }
/* the six parts of the site: one colour each */
.ixg { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; margin-top: 44px; perspective: 1200px; }
.ixc { position: relative; overflow: hidden; border-radius: 30px; padding: 32px; min-height: 290px; box-sizing: border-box; display: flex; flex-direction: column;
  color: #FFFFFF; transform-style: preserve-3d; transition: transform .35s cubic-bezier(.2,.8,.2,1), box-shadow .35s ease;
  transform: rotateX(calc(var(--ty,0) * -7deg)) rotateY(calc(var(--tx,0) * 9deg)); }
.ixc::after { content: ""; position: absolute; inset: 0; pointer-events: none; opacity: 0; transition: opacity .3s ease;
  background: radial-gradient(380px circle at var(--gx,50%) var(--gy,50%), rgba(255,255,255,.35), transparent 55%); mix-blend-mode: soft-light; }
.ixc.tilt { box-shadow: 0 30px 60px -20px rgba(0,0,0,.6); } .ixc.tilt::after { opacity: 1; }
.ixc .n { font-family: 'Roboto Mono', monospace; font-size: 12px; letter-spacing: .16em; text-transform: uppercase; opacity: .8; display: flex;
  justify-content: space-between; align-items: center; }
.ixc .n .ms { font-size: 1.6rem; opacity: 1; }
.ixc .h3 { margin: auto 0 10px !important; padding: 0 !important; font-family: 'Instrument Serif', 'DM Serif Display', Georgia, serif !important;
  font-weight: 400 !important; font-size: 38px !important; line-height: 1 !important; letter-spacing: -.01em !important; color: inherit !important; }
.ixp.ar .ixc .h3 { font-family: 'Readex Pro', sans-serif !important; font-weight: 400 !important; font-size: 28px !important; line-height: 1.35 !important; }
.ixp.ar .ixc .n { font-family: 'Readex Pro', sans-serif; letter-spacing: 0; text-transform: none; font-size: 13px; }
.ixc p { margin: 0; font-size: 15.5px; line-height: 1.55; opacity: .92; }
.ixc.k1 { background: #847DFF; } .ixc.k2 { background: #00B3DD; color: #04121A; } .ixc.k3 { background: #90B8F0; color: #0B1630; }
.ixc.k4 { background: #4B49AA; } .ixc.k5 { background: #DD90D8; color: #2A0B28; } .ixc.k6 { background: #D1C9FF; color: #1A1440; }
/* a feature: words on one side, an example on the other */
.ixf { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.08fr); gap: 64px; align-items: center; }
.ixf.rev > :first-child { order: 2; }
.ixf ul { list-style: none; margin: 26px 0 0; padding: 0; display: flex; flex-direction: column; gap: 14px; }
.ixf li { display: flex; gap: 12px; align-items: flex-start; font-size: 16px; line-height: 1.6; color: rgba(245,245,247,.82); }
.ixf li .ms { color: #D1C9FF; margin-top: 3px; }
.ixm { position: relative; border-radius: 16px; background: #1B1728; padding: clamp(28px, 5vw, 64px); overflow: hidden;
  border: 1px solid rgba(255,255,255,.06); transition: transform .35s cubic-bezier(.2,.8,.2,1);
  transform: perspective(1200px) rotateX(calc(var(--ty,0) * -4deg)) rotateY(calc(var(--tx,0) * 5deg)); }
.ixm::before { content: ""; position: absolute; inset: 0; background: radial-gradient(600px circle at 80% 0%, rgba(107,33,239,.28), transparent 60%),
  radial-gradient(500px circle at 0% 100%, rgba(7,122,199,.2), transparent 60%); pointer-events: none; }
.ixm .ex { position: absolute; top: 16px; inset-inline-end: 16px; font-family: 'Roboto Mono', monospace; font-size: 10px; letter-spacing: .18em;
  padding: 4px 10px; border-radius: 9999px; background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.3); color: #fff; z-index: 2; }
.ixp.ar .ixm .ex { font-family: 'Readex Pro', sans-serif; letter-spacing: 0; font-size: 11px; }
.ixm > :not(.ex) { position: relative; }
/* example: a bot card */
.mbot { border-radius: 18px; background: rgba(14,9,24,.78); border: 1px solid rgba(255,255,255,.1); padding: 20px; box-shadow: 0 30px 60px -24px rgba(0,0,0,.8); }
.mbot .top { display: flex; justify-content: space-between; align-items: center; font-family: 'Roboto Mono', monospace; font-size: 11px; letter-spacing: .12em;
  color: rgba(245,245,247,.6); text-transform: uppercase; }
.mbot .live { display: inline-flex; align-items: center; gap: 6px; color: #4ADE80; background: rgba(34,197,94,.14); padding: 3px 8px; border-radius: 6px; }
.mbot .live::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; animation: ixpulse 1.8s infinite; }
.mbot .nm { margin-top: 14px; font-size: 20px; color: #fff; }
.mbot .bd { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
.mbot .bd span { font-size: 12px; padding: 4px 10px; border-radius: 9999px; background: rgba(132,125,255,.18); color: #D1C9FF; }
.mbot svg { display: block; width: 100%; height: 120px; margin: 18px 0 10px; }
.mbot .ln { stroke-dasharray: 900; stroke-dashoffset: 900; }
.rv.in .mbot .ln { animation: ixdraw 2.2s cubic-bezier(.455,.03,.515,.955) .3s forwards; }
.mbot .row { display: flex; justify-content: space-between; align-items: flex-end; }
.mbot .row .l { font-size: 12px; color: rgba(245,245,247,.55); } .mbot .row .v { font-size: 26px; color: #fff; font-weight: 300; direction: ltr; }
.mbot .row .p { font-size: 14px; color: #4ADE80; background: rgba(34,197,94,.14); border: 1px solid rgba(74,222,128,.3); padding: 4px 10px; border-radius: 8px; direction: ltr; }
.mbot .ft { margin-top: 12px; font-size: 12px; color: rgba(245,245,247,.5); }
/* example: the radar */
.mrad { display: grid; grid-template-columns: 200px minmax(0, 1fr); gap: 22px; align-items: center; }
.mrad svg { width: 200px; height: 200px; display: block; }
.mrad .sw { transform-origin: 100px 100px; animation: ixspin 5s linear infinite; }
@keyframes ixspin { to { transform: rotate(360deg); } }
.mrad .rows { display: flex; flex-direction: column; gap: 8px; }
.mrad .r { display: grid; grid-template-columns: minmax(0,1fr) auto auto; gap: 10px; align-items: center; padding: 10px 12px; border-radius: 12px;
  background: rgba(14,9,24,.7); border: 1px solid rgba(255,255,255,.08); font-size: 14px; direction: ltr; }
.mrad .r b { color: #fff; font-weight: 500; } .mrad .r small { display: block; color: rgba(245,245,247,.5); font-size: 11.5px; }
.mrad .g { font-family: 'Roboto Mono', monospace; font-size: 12px; padding: 3px 8px; border-radius: 6px; background: rgba(34,197,94,.16); color: #86EFAC; }
.mrad .s { font-family: 'Roboto Mono', monospace; font-size: 13px; color: #fff; }
/* example: the market map */
.mheat { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); grid-auto-rows: 58px; gap: 5px; direction: ltr; }
.mheat span { border-radius: 8px; display: flex; flex-direction: column; justify-content: center; align-items: center; font-size: 12.5px; color: #fff;
  transition: transform .2s ease, filter .2s ease; }
.mheat span:hover { transform: scale(1.06); filter: brightness(1.2); z-index: 2; }
.mheat span b { font-weight: 500; } .mheat span small { font-size: 11px; opacity: .85; font-family: 'Roboto Mono', monospace; }
.mheat .w2 { grid-column: span 2; } .mheat .h2 { grid-row: span 2; }
/* example: the courses */
.mcrs { display: flex; flex-direction: column; gap: 10px; }
.mcrs .c { display: grid; grid-template-columns: 44px minmax(0,1fr) auto; gap: 14px; align-items: center; padding: 14px; border-radius: 14px;
  background: rgba(14,9,24,.72); border: 1px solid rgba(255,255,255,.08); transition: transform .2s ease, border-color .2s ease; }
.mcrs .c:hover { transform: translateX(4px); border-color: rgba(209,201,255,.4); }
.ixp.ar .mcrs .c:hover { transform: translateX(-4px); }
.mcrs .i { width: 44px; height: 44px; border-radius: 12px; display: grid; place-items: center; color: #0B0818; }
.mcrs .t { color: #fff; font-size: 15px; } .mcrs .t small { display: block; color: rgba(245,245,247,.5); font-size: 12px; margin-top: 2px; }
.mcrs .bar { height: 4px; border-radius: 3px; background: rgba(255,255,255,.1); margin-top: 8px; overflow: hidden; }
.mcrs .bar i { display: block; height: 100%; border-radius: 3px; background: linear-gradient(90deg, #847DFF, #2DB6EB); }
.mcrs .lv { font-family: 'Roboto Mono', monospace; font-size: 10.5px; letter-spacing: .12em; padding: 4px 8px; border-radius: 6px; background: rgba(255,255,255,.08); }
.ixp.ar .mcrs .lv { font-family: 'Readex Pro', sans-serif; letter-spacing: 0; font-size: 11.5px; }
/* the numbers: a light card that breaks the dark */
.ixn { border-radius: 30px; background: #CACACA; color: #000; padding: clamp(32px, 5vw, 64px); display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 24px; }
.ixn .v { font-family: 'Instrument Serif', 'DM Serif Display', Georgia, serif; font-size: clamp(56px, 7vw, 96px); line-height: .9; letter-spacing: -.03em; direction: ltr; }
.ixn .l { margin-top: 14px; font-size: 15px; line-height: 1.5; color: #1C1C1E; max-width: 220px; }
.ixn .k { font-family: 'Roboto Mono', monospace; font-size: 11px; letter-spacing: .16em; text-transform: uppercase; color: #3F4041; margin-bottom: 18px; }
.ixp.ar .ixn .k { font-family: 'Readex Pro', sans-serif; letter-spacing: 0; font-size: 12.5px; }
/* how it works */
.ixw { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; margin-top: 44px; counter-reset: st; }
.ixw .s { position: relative; border-radius: 22px; padding: 30px 28px; background: #1B1728; border: 1px solid rgba(255,255,255,.07); overflow: hidden;
  transition: transform .3s ease, border-color .3s ease; }
.ixw .s:hover { transform: translateY(-6px); border-color: rgba(209,201,255,.35); }
.ixw .s .no { font-family: 'Roboto Mono', monospace; font-size: 12px; letter-spacing: .16em; color: #D1C9FF; }
.ixw .s .h4 { margin: 40px 0 10px !important; padding: 0 !important; font-family: 'Instrument Serif', Georgia, serif !important; font-weight: 400 !important;
  font-size: 30px !important; line-height: 1.05 !important; color: #fff !important; }
.ixp.ar .ixw .s .h4 { font-family: 'Readex Pro', sans-serif !important; font-size: 22px !important; line-height: 1.4 !important; }
.ixw .s p { margin: 0; color: rgba(245,245,247,.6); font-size: 15px; line-height: 1.65; }
.ixw .s::after { content: ""; position: absolute; right: -40px; top: -40px; width: 140px; height: 140px; border-radius: 50%;
  background: radial-gradient(circle, rgba(132,125,255,.35), transparent 70%); }
.ixp.ar .ixw .s::after { right: auto; left: -40px; }
/* the last words */
.ixend { text-align: center; padding: 140px 24px 190px; }
.ixend .ixh { font-size: clamp(44px, 7vw, 110px); margin: 20px auto 18px; max-width: 1000px; }
.ixp.ar .ixend .ixh { font-size: clamp(36px, 5vw, 80px); }
.ixend .ixt { margin: 0 auto; text-align: center; }
.ixfoot { border-top: 1px solid rgba(255,255,255,.08); max-width: 1200px; margin: 0 auto; padding: 28px 24px 150px; display: flex; justify-content: space-between;
  gap: 16px; flex-wrap: wrap; font-family: 'Roboto Mono', monospace; font-size: 11px; letter-spacing: .14em; text-transform: uppercase; color: rgba(245,245,247,.45); }
.ixp.ar .ixfoot { font-family: 'Readex Pro', sans-serif; letter-spacing: 0; font-size: 12.5px; text-transform: none; }
/* reveals as the page scrolls (only when the page script runs: without it everything simply shows) */
html.ix-js .rv { opacity: 0; translate: 0 34px; transition: opacity 1.1s cubic-bezier(.455,.03,.515,.955), translate 1.1s cubic-bezier(.455,.03,.515,.955),
  transform .35s cubic-bezier(.2,.8,.2,1), box-shadow .35s ease; }
html.ix-js .rv.in { opacity: 1; translate: 0 0; }
html.ix-js .ixg .rv:nth-child(2), html.ix-js .ixw .rv:nth-child(2) { transition-delay: .12s; }
html.ix-js .ixg .rv:nth-child(3), html.ix-js .ixw .rv:nth-child(3) { transition-delay: .24s; }
html.ix-js .ixg .rv:nth-child(5) { transition-delay: .12s; } html.ix-js .ixg .rv:nth-child(6) { transition-delay: .24s; }
/* "Get started": white on black, the only action, at the bottom in the middle all the way down */
.st-key-introgo { position: fixed !important; left: 50%; bottom: clamp(26px, 5vh, 48px); translate: -50% 0; z-index: 999980; width: auto !important;
  transition: opacity .5s cubic-bezier(.455,.03,.515,.955), translate .5s cubic-bezier(.455,.03,.515,.955); }
html.ix-js .st-key-introgo { opacity: 0; translate: -50% 24px; pointer-events: none; }            /* the first screen shows "Scroll down" instead */
html.ix-js.ix-past .st-key-introgo { opacity: 1; translate: -50% 0; pointer-events: auto; }
.st-key-introgo .stElementContainer, .st-key-introgo [data-testid="stElementContainer"] { width: auto !important; }
.st-key-introgo button { min-height: 52px !important; padding: 0 30px !important; border-radius: 8px !important; background: #FFFFFF !important;
  border: 1px solid #FFFFFF !important; box-shadow: 0 18px 50px -12px rgba(11,8,24,.75), 0 0 0 6px rgba(255,255,255,.08) !important;
  transition: transform .2s ease, box-shadow .2s ease, background .2s ease !important; }
.st-key-introgo button p { color: #000 !important; font-size: 16px !important; font-weight: 500 !important; letter-spacing: .01em; }
.st-key-introgo button p::after { content: "  \\2192"; display: inline-block; margin-inline-start: 8px; transition: transform .2s ease; }
.st-key-introgo button:hover { transform: translateY(-2px); background: #EDEBFF !important; box-shadow: 0 22px 60px -12px rgba(132,125,255,.7), 0 0 0 8px rgba(255,255,255,.1) !important; }
.st-key-introgo button:hover p::after { transform: translateX(4px); }
.st-key-introgo button:active { transform: translateY(0) scale(.98); }
/* "Get started" pressed: the landing fades out at once while the main page loads (the page's script adds the class) */
html.ix-leaving .ixp, html.ix-leaving .st-key-introgo, html.ix-leaving .ix-scroll { opacity: 0 !important; pointer-events: none !important;
  transition: opacity .16s ease !important; }
@media (max-width: 1000px) { .ixg { grid-template-columns: repeat(2, minmax(0, 1fr)); } .ixf { grid-template-columns: 1fr; gap: 36px; }
  .ixf.rev > :first-child { order: 0; } .ixn { grid-template-columns: repeat(2, minmax(0, 1fr)); } .ixw { grid-template-columns: 1fr; } }
@media (max-width: 900px) { .ix-center { top: 38%; } .ix-sc { height: 44vh; bottom: -6vh; } .ixs { padding-top: 84px; } }
@media (max-width: 640px) { .ixg { grid-template-columns: 1fr; } .ixc { min-height: 220px; } .mrad { grid-template-columns: 1fr; justify-items: center; }
  .mheat { grid-template-columns: repeat(3, minmax(0, 1fr)); } .ixn { grid-template-columns: 1fr 1fr; } }
@media (prefers-reduced-motion: reduce) { .ixp *, .st-key-introgo { animation: none !important; opacity: 1 !important; }
  .mbot .ln { stroke-dashoffset: 0; } html.ix-js .rv { opacity: 1; translate: none; } .ix-sc { translate: -50% 0; filter: none; } }
</style>"""


def _start():
    st.session_state["intro_done"] = True


def _mock_bot():
    pts = [(0, 96), (40, 90), (80, 94), (120, 78), (160, 82), (200, 66), (240, 70), (280, 52), (320, 58), (360, 40), (400, 44), (440, 26), (480, 18)]
    line = "M" + " L".join(f"{x} {y}" for x, y in pts)
    area = line + " L480 120 L0 120 Z"
    return (f'<div class="mbot"><div class="top"><span>{L("All companies · 2 strategies", "كل الشركات · استراتيجيتين")}</span>'
            f'<span class="live">LIVE</span></div><div class="nm">{L("Momentum Rider", "راكب الزخم")}</div>'
            f'<div class="bd"><span>Trend Following</span><span>Breakout</span><span>{L("ATR stop ×3", "وقف ATR ×3")}</span></div>'
            '<svg viewBox="0 0 480 120" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="mbA" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#4ADE80" stop-opacity=".35"/><stop offset="1" stop-color="#4ADE80" stop-opacity="0"/></linearGradient></defs>'
            f'<path d="{area}" fill="url(#mbA)"/><path class="ln" d="{line}" fill="none" stroke="#4ADE80" stroke-width="2.4" stroke-linejoin="round"/></svg>'
            f'<div class="row"><div><div class="l">{L("Balance", "الرصيد")}</div><div class="v">$112,480</div></div><div class="p">+12.5%</div></div>'
            f'<div class="ft">{L("Forward test · recorded session by session", "اختبار أمامي · مسجّل جلسة بجلسة")}</div></div>')


def _mock_radar():
    dots = [(100, 58, "#4ADE80"), (136, 80, "#4ADE80"), (70, 122, "#86EFAC"), (128, 138, "#4ADE80"), (58, 76, "#86EFAC")]
    svg = ('<svg viewBox="0 0 200 200" aria-hidden="true"><defs><linearGradient id="mrS" x1="0" y1="0" x2="1" y2="1">'
           '<stop offset="0" stop-color="#2DB6EB" stop-opacity=".55"/><stop offset="1" stop-color="#2DB6EB" stop-opacity="0"/></linearGradient></defs>'
           + "".join(f'<circle cx="100" cy="100" r="{r}" fill="none" stroke="rgba(255,255,255,.14)"/>' for r in (30, 60, 92))
           + '<line x1="100" y1="8" x2="100" y2="192" stroke="rgba(255,255,255,.08)"/><line x1="8" y1="100" x2="192" y2="100" stroke="rgba(255,255,255,.08)"/>'
           '<path class="sw" d="M100 100 L100 8 A92 92 0 0 1 180 55 Z" fill="url(#mrS)"/>'
           + "".join(f'<circle cx="{x}" cy="{y}" r="4.5" fill="{c}"><animate attributeName="r" values="4.5;7;4.5" dur="2.4s" begin="{i * .4}s" repeatCount="indefinite"/></circle>'
                     for i, (x, y, c) in enumerate(dots)) + '<circle cx="100" cy="100" r="4" fill="#2DB6EB"/></svg>')
    rows = [("MSFT", "Microsoft", "A+", 90), ("CRWD", "CrowdStrike", "A+", 87), ("TMO", "Thermo Fisher", "A", 83)]
    return (f'<div class="mrad">{svg}<div class="rows">'
            + "".join(f'<div class="r"><div><b>{t}</b><small>{n}</small></div><span class="g">{g}</span><span class="s">{s}</span></div>' for t, n, g, s in rows)
            + "</div></div>")


def _mock_heat():
    cells = [("NVDA", 3.2, "w2 h2"), ("MSFT", 0.8, "w2"), ("AAPL", -0.6, ""), ("AMZN", 1.4, ""), ("GOOGL", 0.4, ""), ("META", -1.9, ""),
             ("AVGO", 2.1, "w2"), ("TSLA", -2.8, ""), ("JPM", 0.2, ""), ("LLY", -0.9, ""), ("XOM", 1.1, ""), ("V", 0.3, ""), ("WMT", -0.2, "")]

    def col(p):
        if p >= 2:
            return "#1F8A4E"
        if p >= 0.5:
            return "#17643A"
        if p >= 0:
            return "#1E3A2C"
        if p > -1:
            return "#4A1F29"
        return "#8C2B38"
    return ('<div class="mheat">' + "".join(f'<span class="{c}" style="background:{col(p)}"><b>{t}</b><small>{p:+.1f}%</small></span>'
                                           for t, p, c in cells) + "</div>")


def _mock_courses(f):
    items = [("#847DFF", "candlestick_chart", L("Reading candles", "قراءة الشموع"), L("Beginner · 6 lessons", "مبتدئ · 6 دروس"), 100, L("DONE", "مكتملة")),
             ("#00B3DD", "trending_up", L("Trend and momentum", "الاتجاه والزخم"), L("Essential · 5 lessons", "أساسي · 5 دروس"), 60, "60%"),
             ("#DD90D8", "shield", L("Risk and position size", "المخاطرة وحجم الصفقة"), L("Intermediate · 7 lessons", "متوسط · 7 دروس"), 0, L("NEW", "جديدة"))]
    return ('<div class="mcrs">' + "".join(
        f'<div class="c"><span class="i" style="background:{bg}"><span class="ms">{ic}</span></span><div class="t">{t}<small>{sub}</small>'
        f'<div class="bar"><i style="width:{w}%"></i></div></div><span class="lv">{lv}</span></div>' for bg, ic, t, sub, w, lv in items) + "</div>")


def intro_html():
    ar = is_ar()
    f = _facts()
    ex = L("EXAMPLE", "مثال")
    gem = ('<svg class="ix-gem" viewBox="0 0 400 260" aria-hidden="true"><defs>'
           '<linearGradient id="gmA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2A2A30"/><stop offset=".5" stop-color="#060608"/><stop offset="1" stop-color="#1A1C22"/></linearGradient>'
           '<linearGradient id="gmB" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF" stop-opacity=".9"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient></defs>'
           '<path d="M40 210 L90 90 L170 40 L260 52 L340 110 L372 206 L300 250 L110 250 Z" fill="url(#gmA)" stroke="rgba(255,255,255,.45)"/>'
           '<path d="M90 90 L170 40 L200 120 Z M170 40 L260 52 L200 120 Z M260 52 L340 110 L200 120 Z M90 90 L200 120 L110 250 L40 210 Z" fill="url(#gmB)" opacity=".18"/>'
           '<path d="M200 120 L300 250 M200 120 L372 206 M200 120 L110 250" stroke="rgba(255,255,255,.25)"/></svg>')
    hero = ('<section class="ix"><div class="ix-glow"><i class="g1"></i><i class="g2"></i><i class="g3"></i><i class="g4"></i></div>'
            '<div class="ix-grain"></div>'
            f'<div class="ix-sc">{gem}<span class="ix-fl f1"></span><span class="ix-fl f2"></span><span class="ix-fl f3"></span><span class="ix-fl f4"></span><span class="ix-gl-o"></span><span class="ix-gl-b"></span></div>'
            f'<div class="ix-center"><div class="ix-h" role="heading" aria-level="1">{L("Beyond Investing", "أبعد من الاستثمار")}</div>'
            f'<p class="ix-sub">{L("Paper-trading bots, a daily opportunity hunter and market research, in one place.", "بوتات تداول افتراضية، وصياد فرص يومي، وأبحاث السوق، في مكان واحد.")}'
            f'<b>{L("Our goal is to teach you, and to let you trade on paper first.", "هدفنا نعلّمك، ونخليك تتداول افتراضياً.")}</b></p></div>'
            f'<div class="ix-scroll" role="button" tabindex="0"><i></i>{L("Scroll down", "انزل لتحت")}</div></section>')
    state = (f'<section class="ixs ix-state rv"><span class="ixl">{L("What it is", "وش هو")}</span>'
             f'<div class="ixh">{L("One place to learn the market, test your ideas and let them trade. <span>With virtual money, on real prices.</span>", "مكان واحد تتعلّم فيه السوق، وتجرّب أفكارك، وتخليها تتداول لحالها. <span>بفلوس افتراضية، على أسعار حقيقية.</span>")}</div></section>')
    parts = [
        ("k1", "robot_2", L("Paper Bots", "البوتات الافتراضية"), L(f"Up to {f['bots']} bots trade on their own, each with a forward test recorded session by session.", f"لين {f['bots']} بوتات تتداول لحالها، ولكل واحد اختبار أمامي مسجّل جلسة بجلسة.")),
        ("k2", "radar", L("Opportunity Hunter", "صائد الفرص"), L("Every stock scored from 0 to 100 on trend, strength and setup, with a full trade plan.", "كل سهم يتقيّم من 0 لين 100 على الاتجاه والقوة ونمط الدخول، مع خطة تداول كاملة.")),
        ("k3", "query_stats", L("Markets & Research", "الأسواق والأبحاث"), L("Indices, futures, options, the economy, a screener and a page for every company.", "المؤشرات والعقود الآجلة والخيارات والاقتصاد، وفلتر للأسهم، وصفحة لكل شركة.")),
        ("k4", "lightbulb", L("Insight", "رؤى"), L("The daily brief, fear & greed, seasonality and articles that explain the moves.", "الموجز اليومي، ومؤشر الخوف والطمع، والموسمية، ومقالات تشرح الحركة.")),
        ("k5", "calendar_month", L("Calendars", "التقويم"), L("Earnings, economic events, dividends, splits, IPOs and market holidays.", "الأرباح والأحداث الاقتصادية والتوزيعات والتقسيمات والاكتتابات وعطلات السوق.")),
        ("k6", "school", L("Academy", "الأكاديمية"), L(f"{f['courses']} courses, {f['labs']} interactive labs and a glossary of {f['terms']} terms.", f"{f['courses']} دورة، و{f['labs']} مختبرات تفاعلية، وقاموس فيه {f['terms']} مصطلحاً.")),
    ]
    grid = (f'<section class="ixs"><div class="rv"><span class="ixl">{L("Inside the site", "داخل الموقع")}</span>'
            f'<div class="ixh">{L("Six parts, <em>one purpose.</em>", "ستة أقسام، <em>وهدف واحد.</em>")}</div></div><div class="ixg">'
            + "".join(f'<div class="ixc {k} rv"><div class="n"><span>0{i + 1}</span><span class="ms">{ic}</span></div><div class="h3" role="heading" aria-level="3">{t}</div><p>{d}</p></div>'
                      for i, (k, ic, t, d) in enumerate(parts)) + "</div></section>")

    def feature(label, title, text, bullets, mock, rev=False):
        li = "".join(f'<li><span class="ms">check_circle</span><span>{b}</span></li>' for b in bullets)
        return (f'<section class="ixs"><div class="ixf{" rev" if rev else ""}"><div class="rv"><span class="ixl">{label}</span>'
                f'<div class="ixh">{title}</div><p class="ixt">{text}</p><ul>{li}</ul></div>'
                f'<div class="ixm rv"><span class="ex">{ex}</span>{mock}</div></div></section>')

    bots = feature(L("Paper Bots", "البوتات الافتراضية"), L("Your strategy,<br><em>running on its own.</em>", "استراتيجيتك،<br><em>تشتغل لحالها.</em>"),
                   L("Pick what the bot trades and how it decides, then watch it buy and sell with virtual money on real prices.",
                     "اختر وش يتداول البوت وكيف يقرر، وبعدها شوفه يشتري ويبيع بفلوس افتراضية على أسعار حقيقية."),
                   [L(f"{f['single']} strategies, alone or together, plus {f['combined']} ready-made combined playbooks.", f"{f['single']} استراتيجية لحالها أو مع بعض، و{f['combined']} استراتيجيات مركّبة جاهزة."),
                    L("A lab that tested every strategy on 2012–2019 and again on 2020–now.", "مختبر جرّب كل استراتيجية على 2012–2019 ومرة ثانية على 2020 لين اليوم."),
                    L("Forward tests kept apart from the historical simulation, so the record stays honest.", "الاختبار الأمامي منفصل عن المحاكاة التاريخية، عشان يبقى السجل صادق.")],
                   _mock_bot())
    hunt = feature(L("Opportunity Hunter", "صائد الفرص"), L("Every stock,<br><em>checked every day.</em>", "كل سهم،<br><em>يتفحّص كل يوم.</em>"),
                   L("The hunter scores the market on exact setups and shows only what passes, with the entry, the stop and the target.",
                     "الصياد يقيّم السوق على أنماط دقيقة ويعرض بس اللي يجتازها، مع نقطة الدخول والوقف والهدف."),
                   [L("A grade and a score from 0 to 100 for every pick.", "درجة وتقييم من 0 لين 100 لكل فرصة."),
                    L("How the same setup did on the same stock before.", "كيف كان نفس النمط على نفس السهم قبل."),
                    L("Analyst ratings, insider trades, events and news in one view.", "تقييمات المحللين وصفقات المطّلعين والأحداث والأخبار في مكان واحد.")],
                   _mock_radar(), rev=True)
    mkts = feature(L("Markets & Research", "الأسواق والأبحاث"), L("The whole market<br><em>on one screen.</em>", "السوق كله<br><em>في شاشة وحدة.</em>"),
                   L("From the heatmap of the S&P 500 to a single company: prices, charts, financials and what moves them.",
                     "من خريطة إس آند بي 500 لين شركة وحدة: الأسعار والرسوم والقوائم المالية واللي يحرّكها."),
                   [L("Futures, options chains, rates and the economy.", "العقود الآجلة وسلاسل الخيارات والفوائد والاقتصاد."),
                    L("A screener and technical signals for every stock.", "فلتر للأسهم وإشارات فنية لكل سهم."),
                    L("A Sharia check on every company page.", "فحص شرعي في صفحة كل شركة.")],
                   _mock_heat())
    nums = [(f"{f['stocks']}", L("S&P 500", "إس آند بي 500"), L("companies covered, each with its own page", "شركة، ولكل وحدة صفحة خاصة")),
            (f"{f['single'] + f['combined']}", L("Strategies", "استراتيجيات"), L("to build your bots with, alone or combined", "تبني فيها بوتاتك، لحالها أو مركّبة")),
            (f"{f['bots']}", L("Bots", "بوتات"), L("trading at the same time, on virtual money", "تتداول في نفس الوقت، بفلوس افتراضية")),
            (f"{f['courses']}", L("Courses", "دورات"), L("from beginner to advanced, in both languages", "من المبتدئ للمتقدم، باللغتين"))]
    numbers = ('<section class="ixs"><div class="ixn rv">'
               + "".join(f'<div><div class="k">{k}</div><div class="v">{v}</div><div class="l">{t}</div></div>' for v, k, t in nums) + "</div></section>")
    steps = [(L("Choose", "اختر"), L("Pick a strategy", "اختر استراتيجية"), L("One rule set or several, on one company, a sector or the whole market.", "مجموعة قواعد وحدة أو أكثر، على شركة أو قطاع أو السوق كله.")),
             (L("Test", "جرّب"), L("See it on history", "شوفها على التاريخ"), L("The same engine runs it on years of real prices, with the lab's verdict.", "نفس المحرك يشغّلها على سنين من الأسعار الحقيقية، مع حكم المختبر.")),
             (L("Run", "شغّل"), L("Let it trade forward", "خلّها تتداول للأمام"), L("From today on, every signal and every fill is saved, session by session.", "من اليوم ورايح، كل إشارة وكل تنفيذ ينحفظ، جلسة بجلسة."))]
    how = (f'<section class="ixs"><div class="rv"><span class="ixl">{L("How it works", "كيف يشتغل")}</span>'
           f'<div class="ixh">{L("Three steps, <em>no real money.</em>", "ثلاث خطوات، <em>بدون فلوس حقيقية.</em>")}</div></div><div class="ixw">'
           + "".join(f'<div class="s rv"><div class="no">0{i + 1} · {k}</div><div class="h4" role="heading" aria-level="3">{t}</div><p>{d}</p></div>' for i, (k, t, d) in enumerate(steps)) + "</div></section>")
    learn = feature(L("Academy", "الأكاديمية"), L("Learn first,<br><em>then trade.</em>", "تعلّم أول،<br><em>وبعدين تداول.</em>"),
                    L("Short courses that end with a quiz, labs to try the ideas yourself and a glossary for every term you meet.",
                      "دورات قصيرة تنتهي باختبار، ومختبرات تجرّب فيها الأفكار بنفسك، وقاموس لكل مصطلح يمرّ عليك."),
                    [L("From reading a candle to sizing a position.", "من قراءة الشمعة لين تحديد حجم الصفقة."),
                     L("In Arabic and English, side by side.", "بالعربي والإنجليزي."),
                     L("Your progress is kept as you go.", "تقدّمك ينحفظ أول بأول.")],
                    _mock_courses(f), rev=True)
    end = (f'<section class="ixend rv"><span class="ixl">{L("Ready when you are", "جاهز متى ما كنت جاهز")}</span>'
           f'<div class="ixh">{L("Your next trade<br><em>starts on paper.</em>", "صفقتك الجاية<br><em>تبدأ افتراضية.</em>")}</div>'
           f'<p class="ixt">{L("Press Get started to open the markets, the hunter and your bots.", "اضغط ابدأ الآن عشان تفتح الأسواق والصياد وبوتاتك.")}</p></section>')
    foot = (f'<div class="ixfoot"><span>© TURA Pro</span><span>{L("Virtual money only · real prices · not investment advice", "فلوس افتراضية فقط · أسعار حقيقية · ليست نصيحة استثمارية")}</span></div>')
    return (f'<div class="ixp{" ar" if ar else ""}" dir="{"rtl" if ar else "ltr"}">' + hero + state + grid + bots + hunt + mkts + numbers + how + learn
            + end + foot + "</div>")


def intro():
    """The landing. Returns True while it shows (the caller then draws nothing else)."""
    if st.session_state.get("intro_done"):
        return False
    rtl = ('<style>.st-key-introgo button p::after { content: "  \\2190" !important; }'
           '.st-key-introgo button:hover p::after { transform: translateX(-4px) !important; }</style>') if is_ar() else ""
    ui.html('<span class="css-anchor"></span>\n' + INTRO_CSS + T.landing_bg_css() + rtl)   # the style on its own line (else Markdown eats it)
    ui.html(intro_html())
    with st.container(key="introgo"):
        st.button(L("Get started", "ابدأ الآن"), key="intro_go", on_click=_start)
    return True
