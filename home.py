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

BUILD = "12.5"

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
    titles = [n["title"] for n in top]
    if ar:
        try:
            tr = data.translate(titles)
            if tr and tr != titles:
                titles = tr
        except Exception:
            pass
    return [{"title": t, "link": n.get("link", ""), "source": n.get("source", ""), "time": n.get("time"), "img": n.get("img"),
             "tickers": list(n.get("tickers") or []), "iq": n["iq"]} for n, t in zip(top, titles)]


def top_news():
    try:
        return _top_news(is_ar())
    except Exception:
        return []


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
# THE LANDING: an interactive first screen before the home page (after Origin Financial's "nocturnal gallery"):
# a dawn sky over a skyline of candles, the brand's rising line drawn across it, stars, slow auroras, a spotlight and
# parallax that follow the pointer, a light serif headline, a line that types what the site can do, and "Get started"
# at the bottom in the middle. The main top bar stays, see-through while the landing shows. Shown once per visit.
# =====================================================================
import html as _html
import json as _json
import random as _random


def _stars(n=110, seed=11):
    r = _random.Random(seed)
    out = []
    for i in range(n):
        x, y, s = r.uniform(0, 1600), r.uniform(0, 620), r.choice((0.6, 0.8, 1.0, 1.0, 1.3, 1.7))
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{s}" class="tw{i % 4}" style="animation-delay:{r.uniform(0, 5):.2f}s"/>')
    return ('<svg class="ix-stars" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
            f'<g fill="#fff">{"".join(out)}</g></svg>')


def _horizon(seed=5):
    """The skyline: candles standing on the horizon, darker in front, with the brand's rising line drawn over them."""
    r = _random.Random(seed)

    def row(n, base, amp, w, fill, op):
        x, lvl, bars = 0.0, 0.0, []
        step = 1600 / n
        for i in range(n):
            lvl = max(-1.0, min(1.0, lvl + r.uniform(-.35, .38)))
            h = amp * (0.55 + 0.45 * lvl) + r.uniform(0, amp * .35) + 18
            wick = h + r.uniform(8, 26)
            cx = x + step / 2
            bars.append(f'<rect x="{cx - w / 2:.1f}" y="{base - h:.1f}" width="{w:.1f}" height="{h + 400:.1f}" rx="1.5"/>'
                        f'<rect x="{cx - .8:.1f}" y="{base - wick:.1f}" width="1.6" height="{wick - h + 2:.1f}"/>')
            x += step
        return f'<g fill="{fill}" opacity="{op}">{"".join(bars)}</g>'

    back = row(70, 815, 70, 10, "#2A2466", .5)
    mid = row(52, 845, 55, 14, "#17123A", .85)
    front = row(38, 880, 42, 20, "#0B0818", 1)
    pts = [(0, 792), (140, 786), (260, 795), (380, 760), (520, 770), (640, 730), (760, 742), (880, 690), (1000, 702), (1120, 640),
           (1240, 655), (1360, 590), (1480, 575), (1600, 520)]
    path = "M" + " L".join(f"{x} {y}" for x, y in pts)
    return ('<svg class="ix-horizon" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMax slice" aria-hidden="true">'
            '<defs><linearGradient id="ixLine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#847DFF" stop-opacity="0"/>'
            '<stop offset=".25" stop-color="#847DFF"/><stop offset=".7" stop-color="#4AA2E2"/><stop offset="1" stop-color="#2DB6EB"/></linearGradient>'
            '<filter id="ixGlow" x="-10%" y="-50%" width="120%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>'
            '<linearGradient id="ixFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0B0818" stop-opacity="0"/>'
            '<stop offset="1" stop-color="#0B0818"/></linearGradient></defs>'
            f'<g class="ix-l3">{back}</g><g class="ix-l2">{mid}</g>'
            f'<g class="ix-line"><path d="{path}" fill="none" stroke="url(#ixLine)" stroke-width="10" filter="url(#ixGlow)" opacity=".55"/>'
            f'<path class="ix-draw" d="{path}" fill="none" stroke="url(#ixLine)" stroke-width="2.6" stroke-linecap="round"/>'
            f'<circle class="ix-dot" r="5" fill="#fff" style="offset-path:path(\'{path}\')"/></g>'
            f'<g class="ix-l1">{front}</g><rect x="0" y="820" width="1600" height="80" fill="url(#ixFade)"/></svg>')


_IX_WORDS = {
    "en": ["Which stocks are breaking out today?", "Build a bot that buys momentum leaders", "Test a strategy on ten years of prices",
           "Is this company Sharia compliant?", "What moved the S&P 500 this morning?"],
    "ar": ["وش الأسهم اللي تخترق اليوم؟", "ابنِ بوت يشتري أقوى أسهم الزخم", "جرّب استراتيجية على أسعار عشر سنين",
           "هل الشركة متوافقة مع الشريعة؟", "وش اللي حرّك إس آند بي 500 اليوم؟"],
}
_IX_CHIPS = [("robot_2", "Paper bots", "بوتات افتراضية", "c1"), ("radar", "Opportunity radar", "رادار الفرص", "c2"),
             ("summarize", "Daily brief", "الموجز اليومي", "c3"), ("verified", "Sharia check", "فحص الشريعة", "c4"),
             ("school", "Academy", "الأكاديمية", "c5")]

INTRO_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Roboto+Mono:wght@400;500&display=swap');
/* the landing covers the page; the top bar stays over it, see-through */
header[data-testid="stHeader"] { background: transparent !important; backdrop-filter: none !important; -webkit-backdrop-filter: none !important;
  border-bottom-color: transparent !important; box-shadow: none !important; }
header[data-testid="stHeader"]::after { opacity: 0; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
.ix { position: fixed; inset: 0; z-index: 90; overflow: hidden; color: #F5F5F7; font-family: 'DM Sans', 'Readex Pro', system-ui, sans-serif;
  background: linear-gradient(180deg, #0B0818 0%, #110C24 18%, #1B1850 38%, #2B3A96 60%, #3F74C8 80%, #6AAFE6 100%); }
.ix > * { position: absolute; }
.ix-stars { inset: 0; width: 100%; height: 100%; opacity: .9; transform: translate3d(calc(var(--px,0) * -6px), calc(var(--py,0) * -4px), 0); }
.ix-stars .tw0 { animation: ixtw 3.2s ease-in-out infinite; } .ix-stars .tw1 { animation: ixtw 4.6s ease-in-out infinite; }
.ix-stars .tw2 { animation: ixtw 5.8s ease-in-out infinite; } .ix-stars .tw3 { opacity: .45; }
@keyframes ixtw { 0%,100% { opacity: .9; } 50% { opacity: .15; } }
.ix-aurora { inset: -20%; pointer-events: none; transform: translate3d(calc(var(--px,0) * -22px), calc(var(--py,0) * -14px), 0); }
.ix-aurora i { position: absolute; border-radius: 50%; filter: blur(70px); opacity: .55; mix-blend-mode: screen; }
.ix-aurora i:nth-child(1) { width: 46vw; height: 30vw; left: 12%; top: 22%; background: #6B21EF; animation: ixdrift1 18s ease-in-out infinite alternate; }
.ix-aurora i:nth-child(2) { width: 40vw; height: 26vw; right: 8%; top: 30%; background: #077AC7; animation: ixdrift2 22s ease-in-out infinite alternate; }
.ix-aurora i:nth-child(3) { width: 30vw; height: 18vw; left: 40%; top: 48%; background: #847DFF; opacity: .35; animation: ixdrift1 26s ease-in-out infinite alternate-reverse; }
@keyframes ixdrift1 { 0% { transform: translate(0,0) scale(1); } 100% { transform: translate(6vw,-3vw) scale(1.15); } }
@keyframes ixdrift2 { 0% { transform: translate(0,0) scale(1.1); } 100% { transform: translate(-7vw,2vw) scale(.95); } }
.ix-spot { inset: 0; pointer-events: none; background: radial-gradient(520px circle at var(--cx,50%) var(--cy,40%), rgba(209,201,255,.16), transparent 62%); }
.ix-horizon { left: 0; right: 0; bottom: 0; width: 100%; height: 100%; transform: translate3d(calc(var(--px,0) * -10px), 0, 0); }
.ix-horizon .ix-l3 { transform: translate3d(calc(var(--px,0) * 6px), 0, 0); }
.ix-horizon .ix-l2 { transform: translate3d(calc(var(--px,0) * 12px), 0, 0); }
.ix-horizon .ix-l1 { transform: translate3d(calc(var(--px,0) * 20px), 0, 0); }
.ix-draw { stroke-dasharray: 2400; stroke-dashoffset: 2400; animation: ixdraw 2.5s cubic-bezier(.455,.03,.515,.955) .4s forwards; }
@keyframes ixdraw { to { stroke-dashoffset: 0; } }
.ix-dot { offset-distance: 0%; animation: ixrun 7s cubic-bezier(.455,.03,.515,.955) 2.9s infinite; filter: drop-shadow(0 0 8px #fff); opacity: 0; }
@keyframes ixrun { 0% { offset-distance: 0%; opacity: 0; } 8% { opacity: 1; } 90% { opacity: 1; } 100% { offset-distance: 100%; opacity: 0; } }
/* the words in the middle */
.ix-center { left: 50%; top: 44%; width: min(980px, 92vw); transform: translate(-50%, -50%); text-align: center; z-index: 3; }
.ix-eyebrow { display: inline-flex; align-items: center; gap: 12px; font-family: 'Roboto Mono', monospace; font-size: 12px; letter-spacing: .18em;
  text-transform: uppercase; color: rgba(245,245,247,.72); }
.ix-pill { padding: 5px 12px; border-radius: 9999px; background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.55); color: #fff;
  font-size: 11px; letter-spacing: .16em; display: inline-flex; align-items: center; gap: 7px; }
.ix-pill i { width: 7px; height: 7px; border-radius: 50%; background: #4ADE80; box-shadow: 0 0 0 0 rgba(74,222,128,.6); animation: ixpulse 1.8s infinite; }
@keyframes ixpulse { 0% { box-shadow: 0 0 0 0 rgba(74,222,128,.55); } 70% { box-shadow: 0 0 0 9px rgba(74,222,128,0); } 100% { box-shadow: 0 0 0 0 rgba(74,222,128,0); } }
.ix-h { margin: 22px 0 18px !important; padding: 0 !important; font-family: 'Instrument Serif', 'DM Serif Display', Georgia, serif !important;
  font-weight: 400 !important; font-size: clamp(46px, 7.2vw, 104px) !important; line-height: .95 !important; letter-spacing: -.02em !important;
  color: #F5F5F7 !important; text-shadow: 0 10px 40px rgba(11,8,24,.45); }
.ix-h em { font-style: italic; background: linear-gradient(90deg, #D1C9FF, #9DCBF7 55%, #FFFFFF); -webkit-background-clip: text; background-clip: text;
  color: transparent; padding-inline-end: .06em; }
.ix.ar .ix-h { font-family: 'Readex Pro', sans-serif !important; font-weight: 300 !important; font-size: clamp(38px, 5.6vw, 84px) !important;
  line-height: 1.25 !important; letter-spacing: 0 !important; }
.ix.ar .ix-h em { font-style: normal; font-weight: 400; }
.ix-sub { margin: 0 auto; max-width: 620px; font-size: 17px; line-height: 1.6; font-weight: 300; color: rgba(245,245,247,.72); }
.ix.ar .ix-sub { font-size: 18px; line-height: 1.9; }
.ix-ask { margin: 30px auto 0; width: min(560px, 100%); box-sizing: border-box; display: flex; align-items: center; gap: 12px; padding: 14px 18px; border-radius: 14px;
  background: rgba(11,8,24,.42); border: 1px solid rgba(255,255,255,.22); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.12), 0 20px 50px -20px rgba(11,8,24,.8); text-align: start; cursor: default; }
.ix-ask .ms { color: #D1C9FF; font-size: 1.25rem; }
.ix-ask .ix-type { font-size: 16px; color: #F5F5F7; white-space: nowrap; overflow: hidden; }
.ix-ask .ix-caret { width: 2px; height: 20px; background: #D1C9FF; animation: ixcaret 1s steps(1) infinite; margin-inline-start: -8px; }
@keyframes ixcaret { 50% { opacity: 0; } }
/* the features floating around the words, each on its own depth */
.ix-chips { inset: 0; pointer-events: none; z-index: 2; }
.ix-chip { position: absolute; pointer-events: auto; display: inline-flex; align-items: center; gap: 9px; padding: 10px 15px 10px 11px; border-radius: 9999px;
  background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.28); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  font-family: 'Roboto Mono', monospace; font-size: 12px; letter-spacing: .1em; text-transform: uppercase; color: #F5F5F7;
  transition: background .2s ease, border-color .2s ease, box-shadow .2s ease; animation: ixfloat 7s ease-in-out infinite; }
.ix.ar .ix-chip { font-family: 'Readex Pro', sans-serif; font-size: 13.5px; letter-spacing: 0; text-transform: none; padding: 9px 11px 9px 15px; }
.ix-chip .ms { width: 28px; height: 28px; border-radius: 50%; display: inline-grid; place-items: center; font-size: 1.05rem; color: #0B0818; }
.ix-chip:hover { background: rgba(255,255,255,.18); border-color: #fff; box-shadow: 0 0 30px rgba(209,201,255,.35); }
.ix-chip.c1 { left: 9%; top: 23%; --d: 1.6; } .ix-chip.c1 .ms { background: #847DFF; }
.ix-chip.c2 { right: 10%; top: 20%; --d: 2.2; animation-delay: -2s; } .ix-chip.c2 .ms { background: #00B3DD; }
.ix-chip.c3 { left: 6%; top: 58%; --d: 1.1; animation-delay: -4s; } .ix-chip.c3 .ms { background: #90B8F0; }
.ix-chip.c4 { right: 7%; top: 56%; --d: 1.4; animation-delay: -1s; } .ix-chip.c4 .ms { background: #DD90D8; }
.ix-chip.c5 { left: 50%; top: 13%; --d: .8; animation-delay: -3s; margin-left: -70px; } .ix-chip.c5 .ms { background: #D1C9FF; }
.ix-chip { translate: calc(var(--px,0) * var(--d,1) * -26px) calc(var(--py,0) * var(--d,1) * -18px); }
@keyframes ixfloat { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
/* the note at the bottom, under the button */
.ix-foot { left: 50%; bottom: clamp(12px, 3vh, 26px); translate: -50% 0; z-index: 3; font-family: 'Roboto Mono', monospace; font-size: 11px;
  letter-spacing: .18em; text-transform: uppercase; color: rgba(245,245,247,.62); white-space: nowrap; }
.ix.ar .ix-foot { font-family: 'Readex Pro', sans-serif; letter-spacing: 0; font-size: 12.5px; }
.ix-eyebrow { flex-wrap: wrap; justify-content: center; row-gap: 8px; }
.ix-pill { white-space: nowrap; }
.ix.ar .ix-eyebrow, .ix.ar .ix-pill { font-family: 'Readex Pro', sans-serif; letter-spacing: 0; text-transform: none; font-size: 13px; }
.ix.ar .ix-eyebrow bdi { font-family: 'Roboto Mono', monospace; letter-spacing: .14em; font-size: 12px; }
/* the reveal: slow, confident */
.ix-center > *, .ix-chip, .ix-foot { opacity: 0; animation-name: ixin; animation-duration: 1.6s; animation-timing-function: cubic-bezier(.455,.03,.515,.955);
  animation-fill-mode: forwards; }
.ix-chip { animation: ixin 1.6s cubic-bezier(.455,.03,.515,.955) forwards, ixfloat 7s ease-in-out 1.6s infinite; }
.ix-center > :nth-child(1) { animation-delay: .1s; } .ix-center > :nth-child(2) { animation-delay: .3s; }
.ix-center > :nth-child(3) { animation-delay: .6s; } .ix-center > :nth-child(4) { animation-delay: .9s; }
.ix-chip.c1 { animation-delay: 1.1s, 2.7s; } .ix-chip.c2 { animation-delay: 1.25s, 2.85s; } .ix-chip.c3 { animation-delay: 1.4s, 3s; }
.ix-chip.c4 { animation-delay: 1.55s, 3.15s; } .ix-chip.c5 { animation-delay: 1.7s, 3.3s; } .ix-foot { animation-delay: 1.4s; }
@keyframes ixin { from { opacity: 0; transform: translateY(14px); filter: blur(6px); } to { opacity: 1; transform: none; filter: none; } }
/* "Get started": white on black, the only action, at the bottom in the middle */
.st-key-introgo { position: fixed !important; left: 50%; bottom: clamp(48px, 9vh, 92px); translate: -50% 0; z-index: 95; width: auto !important;
  animation: ixin 1.6s cubic-bezier(.455,.03,.515,.955) 1.2s both; }
.st-key-introgo .stElementContainer, .st-key-introgo [data-testid="stElementContainer"] { width: auto !important; }
.st-key-introgo button { min-height: 52px !important; padding: 0 30px !important; border-radius: 8px !important; background: #FFFFFF !important;
  border: 1px solid #FFFFFF !important; box-shadow: 0 18px 50px -12px rgba(11,8,24,.75), 0 0 0 6px rgba(255,255,255,.08) !important;
  transition: transform .2s ease, box-shadow .2s ease, background .2s ease !important; }
.st-key-introgo button p { color: #000 !important; font-size: 16px !important; font-weight: 500 !important; letter-spacing: .01em; }
.st-key-introgo button p::after { content: "  \\2192"; display: inline-block; margin-inline-start: 8px; transition: transform .2s ease; }
.st-key-introgo button:hover { transform: translateY(-2px); background: #EDEBFF !important; box-shadow: 0 22px 60px -12px rgba(132,125,255,.7), 0 0 0 8px rgba(255,255,255,.1) !important; }
.st-key-introgo button:hover p::after { transform: translateX(4px); }
.st-key-introgo button:active { transform: translateY(0) scale(.98); }
@media (max-width: 900px) { .ix-chip { display: none; } .ix-center { top: 42%; } .ix-sub { font-size: 15px; }
  .ix-foot { white-space: normal; width: 90vw; text-align: center; line-height: 1.7; } .ix-ask { padding: 12px 14px; } }
@media (prefers-reduced-motion: reduce) { .ix *, .st-key-introgo { animation: none !important; opacity: 1 !important; transform: none; }
  .ix-draw { stroke-dashoffset: 0; } .ix-center { transform: translate(-50%, -50%) !important; } }
</style>"""


def _start():
    st.session_state["intro_done"] = True


def intro_html():
    ar = is_ar()
    lang = "ar" if ar else "en"
    words = _IX_WORDS[lang]
    chips = "".join(f'<span class="ix-chip {c}"><span class="ms">{ic}</span>{L(en, a)}</span>' for ic, en, a, c in _IX_CHIPS)
    head = L("Trade the market<br><em>before you risk a dollar.</em>", "تداول السوق<br><em>قبل ما تخاطر بدولار.</em>")
    sub = L("Paper-trading bots, a daily opportunity hunter and market research, in one place, in English and Arabic.",
            "بوتات تداول افتراضية، وصياد فرص يومي، وأبحاث السوق، في مكان واحد، بالعربي والإنجليزي.")
    eyebrow = L("A.Alturaifi Pro · US markets", "<bdi>A.ALTURAIFI PRO</bdi> · الأسواق الأمريكية")
    pill = L("Paper trading", "تداول افتراضي")
    foot = L("Virtual money only · real prices · no real funds at risk", "فلوس افتراضية فقط · أسعار حقيقية · بدون أي مخاطرة بأموال حقيقية")
    return (f'<div class="ix{" ar" if ar else ""}" dir="{"rtl" if ar else "ltr"}">'
            '<div class="ix-aurora"><i></i><i></i><i></i></div>' + _stars() + '<div class="ix-spot"></div>' + _horizon()
            + f'<div class="ix-chips">{chips}</div>'
            f'<div class="ix-center"><div class="ix-eyebrow"><span class="ix-pill"><i></i>{pill}</span><span>{eyebrow}</span></div>'
            f'<div class="ix-h" role="heading" aria-level="1">{head}</div><p class="ix-sub">{sub}</p>'
            f'<div class="ix-ask"><span class="ms">auto_awesome</span>'
            f'<span class="ix-type" data-words="{_html.escape(_json.dumps(words, ensure_ascii=False))}">{words[0]}</span>'
            '<span class="ix-caret"></span></div></div>'
            f'<div class="ix-foot">{foot}</div></div>')


def intro():
    """The landing. Returns True while it shows (the caller then draws nothing else)."""
    if st.session_state.get("intro_done"):
        return False
    ui.html('<span class="css-anchor"></span>' + INTRO_CSS
            + ('<style>.st-key-introgo button p::after { content: "  \\2190" !important; }'
               '.st-key-introgo button:hover p::after { transform: translateX(-4px) !important; }</style>' if is_ar() else ""))
    ui.html(intro_html())
    with st.container(key="introgo"):
        st.button(L("Get started", "ابدأ الآن"), key="intro_go", on_click=_start)
    return True
