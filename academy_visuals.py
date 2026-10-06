"""Local vector artwork and scoped academy styling; no remote image dependency."""
from html import escape
import hashlib
ACADEMY_REVISION = "2026-09-27.6"
MARK = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" role="img" aria-label="Academy university emblem"><defs><linearGradient id="acmark" x2="1" y2="1"><stop stop-color="#3B8BEB"/><stop offset="1" stop-color="#7B45F0"/></linearGradient></defs><rect x="2" y="2" width="92" height="92" rx="25" fill="url(#acmark)"/><path d="M20 36 48 20 76 36M24 40H72M29 43V63M42 43V59M54 43V59M67 43V63M20 73H76" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><path d="M25 63Q37 58 48 65Q59 58 71 63V78Q59 73 48 80Q37 73 25 78ZM48 65V80" fill="#1F1839" stroke="#79E6F3" stroke-width="2.5" stroke-linejoin="round"/></svg>'''
WORDMARK = MARK.replace('viewBox="0 0 96 96"','viewBox="0 0 420 96"').replace('</svg>','<text x="114" y="43" fill="#EDF2FF" font-family="Arial,sans-serif" font-size="25" font-weight="700">TURA</text><text x="114" y="72" fill="#A9BFFF" font-family="Arial,sans-serif" font-size="20" letter-spacing="5">ACADEMY</text></svg>')


def vector_cover(kind, uid="course"):
    """Topic-specific, original SVG covers in a unified blue/violet palette."""
    token=hashlib.sha1(uid.encode()).hexdigest()[:10]
    shapes={
      "plan": '<rect x="140" y="34" width="120" height="118" rx="14"/><path d="M164 64h68M164 85h44M164 106h56M164 127h35"/>',
      "growth": '<path d="M80 138H320M90 130Q180 125 220 88T312 36"/><path d="m289 39 25-4-1 26"/>',
      "fund": '<rect x="110" y="50" width="72" height="80" rx="12"/><rect x="197" y="29" width="72" height="80" rx="12"/><rect x="225" y="78" width="72" height="80" rx="12"/>',
      "orders": '<path d="M83 60h208l-19-18M291 60l-19 18M317 125H109l19-18M109 125l19 18"/><circle cx="122" cy="60" r="12"/><circle cx="274" cy="125" r="12"/>',
      "statements": '<rect x="87" y="55" width="85" height="103" rx="9"/><rect x="164" y="30" width="85" height="128" rx="9"/><rect x="241" y="68" width="72" height="90" rx="9"/><path d="M183 57h46M183 77h33M183 97h46M183 117h25"/>',
      "inflation": '<circle cx="160" cy="94" r="53"/><path d="M160 61v66M177 70h-24a14 14 0 0 0 0 28h14a14 14 0 0 1 0 28h-25M235 129V57m-16 19 16-19 16 19M270 145V91"/>',
      "mind": '<path d="M153 143v-23c-35-22-28-77 13-88 51-15 88 29 70 67l20 20h-24v24h-26v18M164 70l17 17 29-32"/>',
      "allocation": '<circle cx="200" cy="95" r="60"/><path d="M200 35v60h60M200 95l-44 41"/><circle cx="200" cy="95" r="22"/>',
      "quality": '<path d="M90 80h64v62H90ZM173 57h64v85h-64ZM256 31h64v111h-64Z"/><path d="m117 57 16 10 22-24M261 158h60"/>',
      "bonds": '<rect x="103" y="40" width="194" height="106" rx="12"/><path d="M125 65h109M125 84h80M125 119h70"/><circle cx="258" cy="108" r="22"/><path d="m246 128-4 29 16-10 16 10-4-29"/>',
      "valuation": '<path d="M77 141h244M99 126 153 91 208 108 292 41M99 126 153 114 208 93 292 83M99 126 153 139 208 130 292 139"/><circle cx="292" cy="41" r="6"/>',
      "research": '<rect x="84" y="44" width="180" height="102" rx="12"/><path d="m107 118 27-25 29 13 25-39 38 13"/><circle cx="270" cy="118" r="34"/><path d="m294 143 27 25"/>',
    }
    aliases={"market":"growth","candles":"quality","levels":"orders","ma":"valuation","osc":"research","risk":"mind","value":"statements","options":"valuation","macro":"bonds"}
    art=shapes.get(kind,shapes.get(aliases.get(kind),shapes["plan"]))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 190" role="img" aria-label="{escape(kind)} course illustration"><defs><linearGradient id="bg{token}" x2="1" y2="1"><stop stop-color="#231B38"/><stop offset="1" stop-color="#201A41"/></linearGradient><linearGradient id="ink{token}" x2="1" y2="1"><stop stop-color="#6ECDF5"/><stop offset="1" stop-color="#AC94FF"/></linearGradient></defs><rect width="400" height="190" fill="url(#bg{token})"/><circle cx="349" cy="26" r="97" fill="#8362EF" opacity=".09"/><circle cx="54" cy="191" r="113" fill="#3B8BEB" opacity=".09"/><g stroke="#A4B7E5" opacity=".06">{''.join(f'<path d="M{x} 0v190"/>' for x in range(0,401,25))}{''.join(f'<path d="M0 {y}h400"/>' for y in range(0,191,25))}</g><g fill="#1A1528" fill-opacity=".8" stroke="url(#ink{token})" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">{art}</g><circle cx="34" cy="28" r="4" fill="#6ECDF5"/><path d="M46 28h38" stroke="#8096BB" stroke-width="2"/></svg>'''

CSS = '''<style>
.st-key-academy_root .ac-hero {position:relative;overflow:hidden;border:1px solid #2C2738;border-radius:26px;padding:38px;background:linear-gradient(90deg,#3B8BEB,#7B45F0,#2DB6EB) top / 100% 3px no-repeat,radial-gradient(ellipse at 88% 10%,#7553c83d,transparent 55%),linear-gradient(115deg,#221D2F,#1A1624 65%);margin-bottom:20px;display:grid;grid-template-columns:minmax(0,1fr) 210px;gap:32px;align-items:center;}
.ac-hero h1 {font-size:clamp(30px,3vw,46px);line-height:1.2;letter-spacing:-1px;color:#F2F5FF;margin:12px 0!important;}
.ac-hero p {color:#B1BED5;max-width:680px;font-size:15px;line-height:1.9;margin:10px 0;}
.st-key-academy_root .ac-eyebrow {
  display:inline-block;max-width:100%;font-size:clamp(15px,1.5vw,20px);
  font-weight:600;letter-spacing:1.8px;line-height:1.5;color:#A8BDFF;
}
@supports ((background-clip:text) or (-webkit-background-clip:text)) {
  .st-key-academy_root .ac-eyebrow {
    background:linear-gradient(100deg,#73A6FF 0%,#A88BFA 55%,#67DDF0 100%);
    -webkit-background-clip:text;background-clip:text;color:transparent;
    -webkit-text-fill-color:transparent;
  }
}
.ac-emblem {max-width:180px;margin:auto;filter:drop-shadow(0 22px 40px #050a17aa);transform:rotate(-5deg);}
.ac-emblem svg {width:100%;height:auto;}
.ac-meta {display:flex;flex-wrap:wrap;gap:10px;margin-top:22px;}
.ac-meta span {font-size:12px;color:#CBD7EF;padding:7px 12px;border:1px solid #2C2738;border-radius:8px;background:rgba(26,22,36,.6);}
.st-key-academy_root .course {border-radius:18px;border:1px solid #2C2738;background:linear-gradient(90deg,#3B8BEB,#7B45F0,#2DB6EB) top / 100% 3px no-repeat, linear-gradient(180deg,#221D2F,#1A1624);height:100%;}
.st-key-academy_root .course .art::after {content:"";position:absolute;left:0;right:0;top:0;height:3px;background:linear-gradient(90deg,#3B8BEB,#7B45F0,#2DB6EB);z-index:2;}
.st-key-academy_root .course .art {height:170px;}
.st-key-academy_root .course .body {padding:20px;}
.st-key-academy_root .course .ttl {font-size:1.02rem;min-height:48px;}
.st-key-academy_root .course .tag {font-size:.8rem;min-height:50px;color:#A1B0C9;}
.st-key-academy_root .course .play {background:#18243de8;border:1px solid #6b7eac;color:#BDD4FF;width:32px;height:32px;}
.st-key-academy_root .course .prog {height:3px;background:#2F2A3C;margin-top:18px;}
.st-key-academy_root .course .prog span {background:linear-gradient(90deg,#4F8AFF,#A78BFA);}
.st-key-academy_root .dcard {background:linear-gradient(90deg,#3B8BEB,#7B45F0,#2DB6EB) top / 100% 3px no-repeat, linear-gradient(180deg,#221D2F,#1A1624);border-color:#2C2738;border-radius:18px;}
.st-key-academy_root .lesson {background:linear-gradient(90deg,#3B8BEB,#7B45F0,#2DB6EB) top / 100% 3px no-repeat, linear-gradient(180deg,#221D2F,#1A1624);border:1px solid #2C2738;border-radius:20px;}
.st-key-academy_root .lesson p {font-size:1.02rem;line-height:2;}
.st-key-academy_root [class*="st-key-crs_"]:focus-within .course {outline:2px solid #8CAFFF;outline-offset:3px;}
.st-key-academy_root [data-testid="stTabs"] button {font-weight:600;}
.ac-note {padding:16px 20px;border-inline-start:3px solid #7B45F0;border-radius:8px;background:linear-gradient(90deg,#3B8BEB,#7B45F0,#2DB6EB) top / 100% 3px no-repeat,#221D2F;color:#B7C7E4;font-size:13px;line-height:1.8;}
@media(max-width:650px){.st-key-academy_root .ac-hero {grid-template-columns:1fr;padding:24px;gap:12px;}.ac-emblem {max-width:80px;position:absolute;inset-inline-end:20px;top:20px;opacity:.3;}.ac-hero h1{max-width:90%;}.st-key-academy_root .course .ttl,.st-key-academy_root .course .tag{min-height:0;}}
@media(prefers-reduced-motion:reduce){.st-key-academy_root *{transition:none!important;animation:none!important;}}
.st-key-academy_root .ac-course-banner {position:relative;isolation:isolate;overflow:hidden;min-height:330px;display:flex;align-items:flex-end;border:1px solid #2C2738;border-radius:22px;margin-bottom:18px;background:#231B38;}
.st-key-academy_root .ac-course-banner::before {content:"";position:absolute;left:0;right:0;top:0;height:3px;background:linear-gradient(90deg,#3B8BEB,#7B45F0,#2DB6EB);z-index:2;}
.st-key-academy_root .ac-course-background {position:absolute;inset:0;z-index:-2;}
.st-key-academy_root .ac-course-background svg {display:block;width:100%;height:100%;max-width:none;}
.st-key-academy_root .ac-course-banner::after {content:"";position:absolute;inset:0;z-index:-1;background:linear-gradient(0deg,rgba(18,13,30,.97),rgba(18,13,30,.55) 55%,rgba(18,13,30,.08));}
.st-key-academy_root .ac-course-copy {padding:32px;width:100%;position:relative;}
.st-key-academy_root .ac-course-copy h1 {font-size:clamp(25px,2.5vw,36px);line-height:1.25;color:#f1f5ff;margin:0 0 12px;}
.st-key-academy_root .ac-course-copy p {color:#c2cfe7;font-size:16px;margin:0 0 24px;max-width:760px;}
.st-key-academy_root .ac-course-meta {display:flex;flex-wrap:wrap;gap:10px;}
.st-key-academy_root .st-key-academy_lesson_panel {padding:24px;border:1px solid #2C2738;border-radius:20px;background:linear-gradient(90deg,#3B8BEB,#7B45F0,#2DB6EB) top / 100% 3px no-repeat, linear-gradient(180deg,#221D2F,#1A1624);}
.st-key-academy_root .st-key-academy_lesson_panel .lesson {padding:0;margin:0;border:0;border-radius:0;background:none;}
.st-key-academy_root .st-key-academy_lesson_panel [data-testid="stHorizontalBlock"] {row-gap:12px;}
@media(max-width:650px){.st-key-academy_root .ac-course-banner{min-height:300px;}.st-key-academy_root .ac-course-copy{padding:22px;}.st-key-academy_root .st-key-academy_lesson_panel{padding:18px;}}
.st-key-academy_root .st-key-academy_lesson_navigation {padding-top:24px!important;}
.st-key-academy_root .st-key-academy_start_here {padding:22px;border:1px solid #405381;border-radius:18px;background:linear-gradient(115deg,#28203F,#262040);margin-bottom:20px;}
.st-key-academy_root .ac-brand-lockup {grid-column:1/-1;direction:ltr!important;text-align:left!important;justify-self:start;display:flex;flex-direction:column;align-items:flex-start;gap:14px;width:100%;margin-bottom:8px;}
.st-key-academy_root .ac-brand-lockup .brand {height:clamp(30px,4.4vw,64px);width:auto;max-width:100%;filter:drop-shadow(0 0 16px rgba(91,140,255,.35));}
.st-key-academy_root .ac-brand-lockup span {font-family:Arial,sans-serif;font-size:14px;letter-spacing:6px;font-weight:600;color:#91BCFF;}
.st-key-academy_root .ac-hero {direction:ltr!important;}

.st-key-academy_root .ac-photo-cover {position:relative;width:100%;height:100%;overflow:hidden;background:#211A36;}
.st-key-academy_root .ac-photo-cover img {position:absolute;inset:0;display:block;width:100%!important;height:100%!important;max-width:none;object-fit:cover;}
.st-key-academy_root .ac-photo-fallback {position:absolute;inset:0;}
.st-key-academy_root .ac-photo-fallback svg {width:100%;height:100%;}
.st-key-academy_root .course .art {overflow:hidden;}
@media(max-width:650px){.st-key-academy_root .ac-brand-lockup{padding-right:50px;}.st-key-academy_root .ac-brand-lockup span{font-size:11px;letter-spacing:4px;}}
</style>'''



PHOTOS = {
  "savings": {
    "id": "photo-1633158829875-e5316a358c6f",
    "credit": "Towfiqu barbhuiya",
    "page": "https://unsplash.com/photos/joqWSI9u_XM",
    "alt": "Savings jar with coins and a growing plant"
  },
  "budget": {
    "id": "photo-1725258080098-727051947997",
    "credit": "Jakub Żerdzicki",
    "page": "https://unsplash.com/photos/zR7nFjjIAWE",
    "alt": "Calculator, receipts and money for financial planning"
  },
  "chart": {
    "id": "photo-1616261167032-b16d2df8333b",
    "credit": "Markus Spiske",
    "page": "https://unsplash.com/photos/jgOkEjVw-KM",
    "alt": "Stock market line chart on a screen"
  },
  "trading": {
    "id": "photo-1768055105681-7d2096c5165f",
    "credit": "Jakub Żerdzicki",
    "page": "https://unsplash.com/photos/j_hho1mE47s",
    "alt": "Investor analysing financial charts on multiple screens"
  },
  "planning": {
    "id": "photo-1740220321128-b06e20bd28a5",
    "credit": "Jakub Żerdzicki",
    "page": "https://unsplash.com/photos/Bb5Q2ImiJGM",
    "alt": "Money and calculator for financial planning"
  },
  "growth": {
    "id": "photo-1579621970563-ebec7560ff3e",
    "credit": "micheile henderson",
    "page": "https://unsplash.com/photos/lZ_4nPFKcV8",
    "alt": "Plant growing from coins"
  }
}

PHOTO_TOPICS = {
    "plan":"planning", "growth":"growth", "fund":"savings", "orders":"trading",
    "statements":"budget", "inflation":"budget", "mind":"planning",
    "allocation":"savings", "quality":"budget", "bonds":"savings",
    "valuation":"chart", "research":"trading", "market":"trading",
    "candles":"trading", "levels":"chart", "ma":"chart", "osc":"chart",
    "risk":"planning", "value":"budget", "options":"trading", "macro":"budget",
}
def cover(kind, uid="course"):
    photo = PHOTOS[PHOTO_TOPICS.get(kind, "planning")]
    source = "https://images.unsplash.com/" + photo["id"] + "?auto=format&fit=crop&w=1600&q=80"
    # Local artwork stays underneath while loading or if an external host fails.
    return ('<div class="ac-photo-cover"><div class="ac-photo-fallback" aria-hidden="true">'
            + vector_cover(kind, uid) + '</div><img src="' + escape(source, quote=True)
            + '" alt="' + escape(photo["alt"], quote=True)
            + '" loading="lazy" decoding="async" referrerpolicy="no-referrer"/></div>')

def academy_wordmark(brand):
    mark = MARK.replace('<svg ', '<svg x="0" y="12" width="96" height="96" ', 1)
    try:                                            # as wide as the name needs (it is short now), never narrower than ACADEMY
        vb = brand.split('viewBox="', 1)[1].split('"', 1)[0].split()
        lw = 50 * float(vb[2]) / float(vb[3])
    except (IndexError, ValueError, ZeroDivisionError):
        lw = 470
    width = 116 + max(lw, 215) + 8
    letters = brand.replace('<svg ', f'<svg x="116" y="25" width="{lw:.0f}" height="50" preserveAspectRatio="xMinYMid meet" ', 1)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} 130">'
            + mark + letters + '<text x="116" y="108" fill="#A9BFFF" font-family="Arial,sans-serif" '
            'font-size="22" letter-spacing="7">ACADEMY</text></svg>')


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "19.5"
