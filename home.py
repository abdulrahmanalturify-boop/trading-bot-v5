"""
home.py - The opening of the home page: the logo in a night sky and three glass cards
(Paper Bots · Opportunity Hunter · Markets & Research) that open their pages.
"""
import streamlit as st

import ui
from i18n import L, is_ar

BUILD = "9.3"

_LINE = "rgba(130,150,255,"
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
.cztop .czghost {{ position:absolute; left:0; right:0; top:8px; font-size:clamp(70px,13.5vw,210px); font-weight:800; letter-spacing:-.04em;
  line-height:1; color:transparent; -webkit-text-stroke:1px {_LINE}.12); pointer-events:none; direction:ltr; user-select:none; }}
.cztop .czlogo {{ position:relative; display:flex; justify-content:center; align-items:center; gap:clamp(12px,1.6vw,24px); direction:ltr;
  margin-top:clamp(18px,3.4vw,58px); }}
.cztop .czlogo svg {{ width:clamp(50px,5.6vw,84px); height:auto; filter:drop-shadow(0 0 26px rgba(91,108,255,.75)); }}
.cztop .czword {{ display:flex; align-items:flex-start; gap:clamp(8px,1vw,16px); font-size:clamp(42px,5.6vw,84px); font-weight:700;
  letter-spacing:-.035em; line-height:1; color:#fff; }}
.cztop .czpro {{ font-size:.36em; font-weight:800; letter-spacing:.14em; margin-top:.2em;
  background:linear-gradient(90deg,#5B8CFF,#A78BFA 55%,#22D3EE); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.cztop .cztag {{ position:relative; margin-top:18px; font-size:.8rem; font-weight:600; letter-spacing:.26em; text-transform:uppercase; color:#93A3DA; }}
.cztop.ar .cztag {{ letter-spacing:0; font-size:.95rem; }}
.cztop .czchips {{ position:relative; display:flex; justify-content:center; gap:10px; flex-wrap:wrap; margin-top:18px; direction:ltr; }}
.cztop .czchips .chip {{ display:inline-flex; align-items:center; gap:7px; background:rgba(12,18,48,.72); border:1px solid {_LINE}.22);
  backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px); border-radius:999px; padding:6px 8px 6px 13px; font-size:.8rem; color:#C9D2F2;
  font-variant-numeric:tabular-nums; }}
.cztop .czchips .chip b {{ color:#fff; font-weight:700; letter-spacing:.04em; }}
.cztop .czchips .chip .pill {{ min-width:0; padding:2px 8px; font-size:.74rem; border-radius:999px; }}
.cztop .czarc {{ position:absolute; left:30%; width:40%; bottom:-118px; height:130px; pointer-events:none; }}

/* the glass cards */
[class*="st-key-czcard_"] {{ position:relative; }}
[class*="st-key-czcard_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-czcard_"] [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}
[class*="st-key-czcard_"] [class*="st-key-czgo_"] {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; width:auto !important; }}
[class*="st-key-czcard_"] [class*="st-key-czgo_"] .stButton, [class*="st-key-czcard_"] [class*="st-key-czgo_"] button
  {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}
.czframe {{ padding:7px; border-radius:26px; border:1px solid {_LINE}.24); background:rgba(8,12,34,.55);
  transition:transform .25s ease, box-shadow .25s ease, border-color .25s ease; }}
[class*="st-key-czcard_"]:hover .czframe {{ transform:translateY(-6px); border-color:{_LINE}.45); box-shadow:0 30px 80px -30px rgba(79,107,255,.6); }}
.czcard {{ box-sizing:border-box; min-height:590px; border-radius:20px; border:1px solid {_LINE}.18);
  background:linear-gradient(180deg,#0B1234 0%,#070B22 55%,#050818 100%); box-shadow:inset 0 1px 0 rgba(255,255,255,.06);
  padding:16px 20px 20px; display:flex; flex-direction:column; gap:10px; }}
.czcard svg.czill {{ display:block; width:100%; max-width:392px; height:auto; margin:0 auto; }}
.czcard .czt {{ margin:2px 0 10px; text-align:center; font-size:1.9rem; font-weight:500; letter-spacing:-.01em; line-height:1.14; color:#fff; }}
.czcard .czem {{ font-family:'Instrument Serif',Georgia,serif; font-style:italic; font-weight:400; font-size:1.2em; letter-spacing:0; }}
.czcard.ar .czt {{ font-weight:600; letter-spacing:0; line-height:1.4; }}
.czcard.ar .czem {{ font-family:'Readex Pro',sans-serif; font-style:normal; font-weight:600; font-size:1em;
  background:linear-gradient(90deg,#8FB0FF,#B9A6FF 60%,#67E8F9); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.czcard .czp {{ padding:14px 18px; border-radius:12px; border:1px solid {_LINE}.24);
  background:linear-gradient(90deg,rgba(40,60,170,.18),rgba(96,74,230,.32)); text-align:center; font-size:.9rem; line-height:1.6; color:#BCC6EA;
  transition:border-color .2s ease, background .2s ease; }}
[class*="st-key-czcard_"]:hover .czp {{ border-color:{_LINE}.4); }}
.czcard .czgo {{ margin-top:auto; padding-top:8px; display:flex; justify-content:center; align-items:center; gap:6px; font-size:.84rem; font-weight:700;
  color:#9CB4FF; letter-spacing:.02em; }}
.czcard .czgo .ms {{ transition:transform .2s ease; }}
[class*="st-key-czcard_"]:hover .czgo {{ color:#fff; }}
[class*="st-key-czcard_"]:hover .czgo .ms {{ transform:translateX(4px); }}
.czcard.ar .czgo .ms {{ transform:scaleX(-1); }}
[class*="st-key-czcard_"]:hover .czcard.ar .czgo .ms {{ transform:scaleX(-1) translateX(4px); }}
@media (min-width: 900px) {{ .st-key-czcard_hunt {{ margin-top:110px; }} }}
@media (max-width: 899.98px) {{
  .st-key-czhero::before, .cztop .czarc {{ display:none; }}
  .czcard {{ min-height:0; }}
}}
@media (max-width: 640px) {{
  .cztop {{ padding:34px 0 22px; }}
  .cztop .cztag {{ font-size:.66rem; letter-spacing:.16em; line-height:1.7; }}
  .cztop.ar .cztag {{ font-size:.85rem; letter-spacing:0; }}
  .cztop .czchips {{ flex-wrap:nowrap; justify-content:flex-start; overflow-x:auto; scrollbar-width:none; padding:2px 2px 4px;
    -webkit-mask-image:linear-gradient(90deg,#000 88%,transparent); mask-image:linear-gradient(90deg,#000 88%,transparent); }}
  .cztop .czchips::-webkit-scrollbar {{ display:none; }}
  .cztop .czchips .chip {{ flex:none; font-size:.74rem; padding:5px 7px 5px 11px; }}
  .czcard .czt {{ font-size:1.65rem; }}
}}
@media (prefers-reduced-motion: reduce) {{ .cztop .czglint {{ animation:none; }} }}
</style>
"""

_MARK = ('<svg viewBox="0 0 64 64" aria-hidden="true"><defs><linearGradient id="czMarkBg" x1="0" y1="0" x2="1" y2="1">'
         '<stop offset="0" stop-color="#3D7BFF"/><stop offset="1" stop-color="#8B5CF6"/></linearGradient></defs>'
         '<rect x="0" y="0" width="64" height="64" rx="16" fill="url(#czMarkBg)"/>'
         '<path d="M17 48 L29.5 15.5 Q32 11 34.5 15.5 L47 48" fill="none" stroke="#fff" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/>'
         '<path d="M22 37 L30 31 L35 34 L48 24" fill="none" stroke="#22D3EE" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
         '<path d="M43 23.2 L48.6 23.6 L48.2 29.2" fill="none" stroke="#22D3EE" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>')

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
    return f'<svg class="czill" viewBox="0 0 392 250" aria-hidden="true">{body}</svg>'


_W = 'fill="#FFFFFF"'
_CIRCUIT = 'fill="none" stroke="#DDE3FF" stroke-opacity=".8" stroke-width="1.4"'

ILL_BOTS = _svg(
    _grid("czb")
    + '<defs><linearGradient id="czbFill" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#B9A6FF"/><stop offset="1" stop-color="#5B6CFF"/></linearGradient></defs>'
    '<circle cx="196" cy="124" r="112" fill="url(#czbGlow)"/>'
    '<circle cx="196" cy="124" r="62" fill="none" stroke="#A9B8FF" stroke-opacity=".5" stroke-width="1.2"/>'
    '<circle cx="196" cy="124" r="46" fill="#18206A" fill-opacity=".45" stroke="#A9B8FF" stroke-opacity=".22"/>'
    '<path d="M196 84 V97" stroke="#D6DCFF" stroke-width="2" stroke-linecap="round"/><circle cx="196" cy="81" r="4" fill="#22D3EE"/>'
    '<rect x="164" y="97" width="64" height="52" rx="15" fill="url(#czbFill)"/>'
    '<rect x="164" y="97" width="64" height="52" rx="15" fill="none" stroke="#FFFFFF" stroke-opacity=".55"/>'
    '<rect x="173" y="109" width="46" height="26" rx="11" fill="#0A0F2E" fill-opacity=".8"/>'
    '<circle cx="186" cy="122" r="4.5" fill="#22D3EE"/><circle cx="206" cy="122" r="4.5" fill="#22D3EE"/>'
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
    '<path d="M196 112 L260 112 A64 21 0 0 0 228 93.8 Z" fill="#22D3EE" fill-opacity=".5"/>'
    '<ellipse cx="196" cy="112" rx="40" ry="13" fill="none" stroke="#FFFFFF" stroke-opacity=".6"/>'
    '<ellipse cx="196" cy="112" rx="17" ry="5.5" fill="none" stroke="#FFFFFF" stroke-opacity=".75"/>'
    '<circle cx="222" cy="103" r="10" fill="none" stroke="#22D3EE" stroke-opacity=".6"/><circle cx="222" cy="103" r="4" fill="#22D3EE"/>'
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
    '<path d="M130 150 L178 124 L214 132 L270 78" fill="none" stroke="#22D3EE" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity=".9"/>'
    '<circle cx="270" cy="78" r="3.6" fill="#22D3EE"/>'
    f'<path d="M300 214 H352 V168" {_CIRCUIT}/><circle cx="352" cy="168" r="2.6" {_W}/>')


def cards():
    """(key, page to open, illustration, title, emphasised word, two lines break, two short texts) in the current language."""
    return [
        ("bots", "paper", ILL_BOTS, L("Paper", "البوتات"), L("Bots", "الافتراضية"), False,
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
    return (f'<div class="cztop{" ar" if ar else ""}"><div class="czline"></div>{_GLINT}<div class="czghost" aria-hidden="true">ALTURAIFI</div>'
            f'<div class="czlogo">{_MARK}<div class="czword"><span>Alturaifi</span><span class="czpro">PRO</span></div></div>'
            f'<div class="cztag">{tag}</div>{chips}{_ARC}</div>')


def card_html(ill, t1, t2, two_lines, p1, p2):
    ar = is_ar()
    brk = "<br>" if two_lines and not ar else " "        # Arabic titles are short enough for one line
    go = L("Open", "افتح")
    return (f'<div class="czframe"><div class="czcard{" ar" if ar else ""}">{ill}'
            f'<div class="czt">{t1}{brk}<span class="czem">{t2}</span></div>'
            f'<div class="czp">{p1}</div><div class="czp">{p2}</div>'
            f'<div class="czgo">{go} <span class="ms">arrow_forward</span></div></div></div>')


def hero(chips_html=""):
    """The home page's opening. Each card is one big button that opens its page."""
    with st.container(key="czhero"):
        ui.html(CSS + top_html(chips_html))
        cols = st.columns(3, gap="large")
        for col, (k, page, ill, t1, t2, two, p1, p2) in zip(cols, cards()):
            with col:
                with st.container(key=f"czcard_{k}"):
                    ui.html(card_html(ill, t1, t2, two, p1, p2))
                    label = f'{t1.replace("&amp;", "&")} {t2}'
                    if st.button(label, key=f"czgo_{k}", width="stretch"):
                        ui.goto(page)
