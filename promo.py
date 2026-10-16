"""
promo.py - The home page's cards for the Trading Bot menu's three pages: the Paper Bots, the Opportunity Hunter and the X Bots.
Each one is an advert in the style of the home page's tool cards (p_overview.CSS, class "ovad") with a small interactive piece
at the top: the Paper Bots card redraws its balance curve for the strategy chosen, the Hunter's radar opens the pick whose blip
is pressed, the X Bots card turns its mood dial to the bot chosen. The pieces are HTML and CSS alone (hidden radio buttons the
styles react to): no script, so they work inside st.markdown and keep working when the page is redrawn.

The whole card still opens its page: p_overview lays a hidden button over every card, so the card lets clicks through to it
(pointer-events) and only the controls catch them. The day's own numbers go in where they exist (today's picks, the site's bots'
balance, the X bots' moods and posts); the rest is drawn and marked as an example.
"""
import markets as MK
import theme as T
import mascot
from i18n import L, is_ar

CSS = """<style data-lm="keep">
.ovad.pz{position:relative;z-index:4;pointer-events:none}
.ovad.pz>input{position:absolute;opacity:0;width:0;height:0;pointer-events:none}
.ovad.pz .pzc{pointer-events:auto;cursor:pointer}
.ovad.pz .pzs{position:relative;margin:14px 0 14px;padding:12px;border-radius:16px;background:rgba(5,8,25,.3);border:1px solid rgba(255,255,255,.12);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.08);min-width:0}
.ovad.pz .pzo{display:none}
.ovad.pz:not(:has(>input:checked)) .pzo[data-o="0"],.ovad.pz>input:nth-of-type(1):checked~.bd .pzo[data-o="0"],.ovad.pz>input:nth-of-type(2):checked~.bd .pzo[data-o="1"],
.ovad.pz>input:nth-of-type(3):checked~.bd .pzo[data-o="2"],.ovad.pz>input:nth-of-type(4):checked~.bd .pzo[data-o="3"],
.ovad.pz>input:nth-of-type(5):checked~.bd .pzo[data-o="4"]{display:block}
.ovad.pz .pzh .pzos{display:contents}
.ovad.pz:not(:has(>input:checked)) .pzh .pzo[data-o="0"],.ovad.pz>input:nth-of-type(1):checked~.bd .pzh .pzo[data-o="0"],
.ovad.pz>input:nth-of-type(2):checked~.bd .pzh .pzo[data-o="1"],.ovad.pz>input:nth-of-type(3):checked~.bd .pzh .pzo[data-o="2"],
.ovad.pz>input:nth-of-type(4):checked~.bd .pzh .pzo[data-o="3"]{display:contents}
.ovad.pz .pzl{display:inline-flex;align-items:center;gap:5px;border:1px solid rgba(255,255,255,.28);background:rgba(255,255,255,.08);color:#fff;border-radius:999px;
  padding:4px 10px;font-size:11.5px;font-weight:700;line-height:1.3;white-space:nowrap;transition:background .2s,color .2s}
.ovad.pz .pzl .ms{font-size:14px}
.ovad.pz:not(:has(>input:checked)) .pzl[data-o="0"],.ovad.pz>input:nth-of-type(1):checked~.bd .pzl[data-o="0"],.ovad.pz>input:nth-of-type(2):checked~.bd .pzl[data-o="1"],
.ovad.pz>input:nth-of-type(3):checked~.bd .pzl[data-o="2"],.ovad.pz>input:nth-of-type(4):checked~.bd .pzl[data-o="3"],
.ovad.pz>input:nth-of-type(5):checked~.bd .pzl[data-o="4"]{background:#fff;color:var(--a2);border-color:#fff}
.ovad.pz>input:focus-visible~.bd .pzl{outline:2px solid #fff;outline-offset:2px}
.ovad.pz .pzk{font-size:10.5px;color:rgba(255,255,255,.7)}
.ovad.pz .pzrow{display:flex;align-items:center;justify-content:space-between;gap:8px;min-width:0}
.ovad.pz .pzlive{display:inline-flex;align-items:center;gap:6px;padding:3px 9px;border-radius:999px;background:rgba(255,255,255,.95);color:var(--a2);font-size:10px;font-weight:800;letter-spacing:.08em}
.ovad.pz .pzlive i{width:6px;height:6px;border-radius:50%;background:#22C55E;animation:ovlive 1.8s infinite}
.ovad.pz .pzchips{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.ovad.pz .pzn{direction:ltr;unicode-bidi:isolate;font-variant-numeric:tabular-nums}
/* the Paper Bots: the balance and its curve */
.ovad.pz .pzbal{display:flex;align-items:flex-end;justify-content:space-between;gap:8px;margin-top:6px}
.ovad.pz .pzbal .v{font-size:22px;font-weight:800;line-height:1.1}
.ovad.pz .pzbal .p{font-size:12px;font-weight:800;color:#4ADE80;background:rgba(74,222,128,.16);border-radius:8px;padding:3px 8px}
.ovad.pz .pzbal .p.neg{color:#FCA5A5;background:rgba(248,113,113,.18)}
.ovad.pz svg.pzeq{display:block;width:100%;height:84px;margin-top:4px}
.ovad.pz svg.pzeq .ln{fill:none;stroke:#fff;stroke-width:2.4;stroke-linejoin:round;stroke-linecap:round;stroke-dasharray:520;animation:ovdraw 1.6s ease-out both}
.ovad.pz .pzslots{display:flex;gap:5px;margin-top:10px}
.ovad.pz .pzslots span{flex:1;height:5px;border-radius:3px;background:rgba(255,255,255,.2)}
.ovad.pz .pzslots span.on{background:#fff}
.ovad.pz .pzsite{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:8px;padding-top:8px;border-top:1px solid rgba(255,255,255,.14);font-size:11.5px}
.ovad.pz .pzsite b{font-size:13px}
/* the Hunter: the radar and the pick */
.ovad.pz .pzh{display:grid;grid-template-columns:118px minmax(0,1fr);gap:10px 12px;align-items:center}
.ovad.pz .pzpick{min-width:0}
.ovad.pz .pzradar{position:relative;width:118px;height:118px;border-radius:50%;overflow:hidden;background:
  radial-gradient(circle,rgba(255,255,255,.05) 0 30%,transparent 31%),repeating-radial-gradient(circle,transparent 0 18px,rgba(255,255,255,.16) 19px 20px),rgba(4,20,52,.45)}
.ovad.pz .pzradar::before,.ovad.pz .pzradar::after{content:"";position:absolute;background:rgba(255,255,255,.14)}
.ovad.pz .pzradar::before{left:50%;top:0;bottom:0;width:1px}.ovad.pz .pzradar::after{top:50%;left:0;right:0;height:1px}
.ovad.pz .pzsweep{position:absolute;inset:0;border-radius:50%;background:conic-gradient(from 0deg,rgba(120,230,255,.55),rgba(120,230,255,0) 70deg);animation:pzspin 4s linear infinite}
@keyframes pzspin{to{transform:rotate(360deg)}}
.ovad.pz .pzblip{position:absolute;width:12px;height:12px;margin:-6px;border-radius:50%;z-index:2;background:#fff;box-shadow:0 0 0 4px rgba(255,255,255,.22);transition:transform .2s,background .2s}
.ovad.pz:not(:has(>input:checked)) .pzblip[data-o="0"],.ovad.pz>input:nth-of-type(1):checked~.bd .pzblip[data-o="0"],.ovad.pz>input:nth-of-type(2):checked~.bd .pzblip[data-o="1"],
.ovad.pz>input:nth-of-type(3):checked~.bd .pzblip[data-o="2"],.ovad.pz>input:nth-of-type(4):checked~.bd .pzblip[data-o="3"]
  {background:#F5B94A;box-shadow:0 0 0 5px rgba(245,185,74,.35);transform:scale(1.25)}
.ovad.pz .pzpick .sy{display:flex;align-items:center;gap:8px;margin-top:4px;min-width:0}
.ovad.pz .pzpick .sy b{font-size:15px}
.ovad.pz .pzpick .nm{font-size:10.5px;line-height:1.35;color:rgba(255,255,255,.78);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.ovad.pz .pzring{width:44px;height:44px;flex:none}
.ovad.pz .pzring circle{fill:none;stroke-width:4}
.ovad.pz .pzring text{fill:#fff;font-size:13px;font-weight:800;text-anchor:middle;font-family:inherit}
.ovad.pz .pzsetup{margin-top:6px;font-size:11px;font-weight:700;display:inline-flex;gap:5px;align-items:center;background:rgba(255,255,255,.14);border-radius:8px;padding:3px 8px;max-width:100%}
.ovad.pz .pzsetup .ms{font-size:14px}
.ovad.pz .pzplan{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;grid-column:1/-1}
.ovad.pz .pzplan .pzk{white-space:nowrap}
.ovad.pz .pzplan>div{background:rgba(4,20,52,.4);border-radius:10px;padding:6px 8px;text-align:center;min-width:0}
.ovad.pz .pzplan .v{font-size:12.5px;font-weight:800;white-space:nowrap}
.ovad.pz .pzplan .t{color:#7CF3C2}.ovad.pz .pzplan .s{color:#FFB4B4}
/* the X bots: the dial and the posts */
.ovad.pz .pzg{display:flex;align-items:center;gap:12px}
.ovad.pz .pzmood{min-width:0}
.ovad.pz.wide .pzs{margin:12px 0 0}
.ovad.pz .pzg svg{flex:none}
.ovad.pz .pzmood .v{font-size:21px;font-weight:800;line-height:1.1}
.ovad.pz .pzmood .w{font-size:11.5px;font-weight:700}
.ovad.pz .pzbeat{margin-top:6px;font-size:11px;line-height:1.5;color:rgba(255,255,255,.82);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.ovad.pz .pzfeed{margin-top:10px;height:86px;overflow:hidden;-webkit-mask-image:linear-gradient(transparent,#000 18%,#000 82%,transparent);mask-image:linear-gradient(transparent,#000 18%,#000 82%,transparent)}
.ovad.pz .pzfeed ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:minmax(0,1fr);gap:6px;animation:pzroll 16s linear infinite}
@keyframes pzroll{to{transform:translateY(-50%)}}
.ovad.pz .pzfeed li{display:flex;gap:8px;align-items:center;background:rgba(255,255,255,.07);border-radius:10px;padding:6px 8px;font-size:11px;min-width:0}
.ovad.pz .pzfeed .av{width:22px;height:22px;border-radius:50%;flex:none;display:grid;place-items:center;font-size:10px;font-weight:800;background:rgba(255,255,255,.14)}
.ovad.pz .pzfeed .tx{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ovad.pz .pzfeed .tn{flex:none;font-size:9.5px;font-weight:800;border-radius:6px;padding:1px 6px}
.ovad.pz .pzfeed .tn.bull{background:rgba(74,222,128,.18);color:#86EFAC}.ovad.pz .pzfeed .tn.bear{background:rgba(248,113,113,.18);color:#FCA5A5}
.ovad.pz .pzfeed .tn.neutral{background:rgba(255,255,255,.14);color:#E7E3EB}
.ovad.pz .pzfeed .ln{flex:1;display:flex;flex-direction:column;gap:4px}.ovad.pz .pzfeed .ln i{display:block;height:5px;border-radius:9px;background:rgba(255,255,255,.22)}
.ovad.pz .pzbots{display:flex;gap:6px;overflow-x:auto;padding-bottom:2px;margin-top:10px;scrollbar-width:none}
.ovad.pz .pzbots::-webkit-scrollbar{display:none}
.ovad.pz .pzbots .pzl{flex:none}
@media (max-width:420px){.ovad.pz .pzh{grid-template-columns:100px minmax(0,1fr)}.ovad.pz .pzradar{width:100px;height:100px}}
@media (prefers-reduced-motion:reduce){.ovad.pz .pzsweep,.ovad.pz .pzfeed ul,.ovad.pz svg.pzeq .ln{animation:none!important}}
</style>"""

EXAMPLE = ("Example", "مثال")


def _radios(name, n):
    # none is checked in the HTML: a checked attribute makes React (which draws the markdown) hold the radio in that state and undo
    # the visitor's choice; the styles show the first option while nothing is chosen (:has)
    return "".join(f'<input type="radio" name="{name}" id="{name}_{i}">' for i in range(n))


def _label(name, i, text, icon=None, extra=""):
    ic = T.icon(icon) if icon else ""
    return f'<label class="pzl pzc" for="{name}_{i}" data-o="{i}"{extra}>{ic}{T.esc(text)}</label>'


def _curve(ys, w=264, h=84):
    """One balance curve over the card's width: the line, the area under it and the start line, with the buys and sells."""
    step = w / (len(ys) - 1)
    pts = [(i * step, y) for i, y in enumerate(ys)]
    line = "M" + " L".join(f"{x:.1f} {y}" for x, y in pts)
    marks = ""
    for k in (3, 7, 11):
        x, y = pts[k]
        up = ys[k + 1] < y
        marks += (f'<path d="M{x - 5:.1f} {y + (12 if up else -12)} l5 {-7 if up else 7} l5 {7 if up else -7}z" fill="{"#4ADE80" if up else "#FCA5A5"}"/>')
    return (f'<svg class="pzeq" viewBox="0 0 {w} {h}" preserveAspectRatio="none" aria-hidden="true">'
            f'<line x1="0" y1="{ys[0]}" x2="{w}" y2="{ys[0]}" stroke="rgba(255,255,255,.35)" stroke-dasharray="3 4"/>'
            f'<path d="{line} L{w} {h} L0 {h} Z" fill="rgba(255,255,255,.14)"/><path class="ln" d="{line}"/>{marks}</svg>')


# the three example strategies of the Paper Bots card (the names are the Strategy Lab's; the curves are drawn)
STRATS = [(("Momentum Rider", "راكب الزخم"), ("Momentum", "الزخم"), 12.48, [60, 56, 58, 48, 51, 42, 37, 40, 30, 26, 28, 18, 14, 10]),
          (("Breakout Hunter", "صيّاد الاختراق"), ("Breakout", "الاختراق"), 8.95, [60, 62, 55, 57, 50, 53, 45, 47, 40, 42, 34, 36, 30, 28]),
          (("Mean Reversion", "ارتداد المتوسط"), ("Reversion", "الارتداد"), -3.16, [60, 54, 58, 52, 60, 64, 59, 67, 62, 70, 66, 72, 69, 67])]


def bots_html(f, live, mk, wide=False):
    """The Paper Bots card: an example bot's curve for the strategy chosen, the site's bots' balance when they have one, the
    visitor's free slots, and what the page gives."""
    name = f"pzb_{mk}"
    start = 100000.0
    opts, chips = "", ""
    for i, (nm, chip, ret, ys) in enumerate(STRATS):
        bal = start * (1 + ret / 100)
        opts += (f'<div class="pzo" data-o="{i}"><div class="pzrow"><span class="pzk">{T.esc(L(*EXAMPLE))} · {T.esc(L(*nm))}</span>'
                 f'<span class="pzlive"><i></i>LIVE</span></div>'
                 f'<div class="pzbal"><div><div class="pzk">{T.esc(L("Virtual balance", "الرصيد الافتراضي"))}</div><div class="v pzn">{T.esc(MK.money(bal))}</div></div>'
                 f'<span class="p pzn{" neg" if ret < 0 else ""}">{ret:+.2f}%</span></div>{_curve(ys)}</div>')
        chips += _label(name, i, L(*chip))
    site = ""
    if live and "bal" in live:
        site = (f'<div class="pzsite"><span>{T.icon("smart_toy")} {T.esc(L("The site's bots now", "بوتات الموقع الحين"))}</span>'
                f'<span><b class="pzn">{T.esc(MK.money(live["bal"]))}</b> {T.pill(live["ret"])}</span></div>')
    mine = int(f.get("mine") or 3)
    slots = '<div class="pzslots" aria-hidden="true"><span class="on"></span>' + "<span></span>" * (mine - 1) + "</div>"
    room = L(f"One bot of {mine}: room for {mine - 1} more, free", f"بوت واحد من {mine}: عندك مكان لـ {mine - 1} بعد، مجاناً")
    stage = f'<div class="pzs">{opts}<div class="pzchips">{chips}</div>{site}{slots}<div class="pzk" style="margin-top:6px">{T.esc(room)}</div></div>'
    pts = [L(f"{f['single']} strategies and {f['combined']} ready combinations, alone or together", f"{f['single']} استراتيجية و{f['combined']} تركيبات جاهزة، لحالها أو مع بعض"),
           L("Stocks or options, on one company, a sector or the whole market", "أسهم أو خيارات، على شركة أو قطاع أو السوق كله") if mk == MK.US else
           L("On one company, a sector or the whole Saudi market, in riyals", "على شركة أو قطاع أو السوق السعودي كله، بالريال"),
           L("An honest forward test, kept apart from the historical simulation", "اختبار أمامي صادق، منفصل عن المحاكاة التاريخية"),
           L(f"Up to {mine} bots of your own in each market, free", f"لين {mine} بوتات خاصة فيك في كل سوق، مجاناً")]
    return _radios(name, len(STRATS)), stage, pts


# example picks when no hunt was made yet today (marked as examples; the real picks take their place)
EX_US = [("MRNA", "Moderna", 93, "A+", "retest", 34.20, 32.10, 38.40), ("ABBV", "AbbVie", 90, "A", "leader", 182.60, 175.90, 196.00),
         ("MPC", "Marathon Petroleum", 84, "A", "pullback", 158.30, 151.70, 171.50), ("NVDA", "NVIDIA", 78, "B", "squeeze", 131.40, 125.20, 143.80)]
EX_SA = [("2222.SR", "Saudi Aramco", 91, "A+", "pullback", 27.40, 26.30, 29.60), ("1120.SR", "Al Rajhi Bank", 88, "A", "leader", 96.80, 92.90, 104.50),
         ("2010.SR", "SABIC", 83, "A", "retest", 68.20, 65.40, 73.80), ("7010.SR", "stc", 77, "B", "squeeze", 42.10, 40.30, 45.70)]
BLIPS = [(30, 64), (62, 30), (72, 70), (24, 28)]           # top %, left % of each blip on the radar


def _ring(score, grade):
    from p_scanner import GRADE_COLOR, _C
    col = GRADE_COLOR.get(grade, _C)
    circ = 2 * 3.14159 * 18
    return (f'<svg class="pzring" viewBox="0 0 44 44" aria-hidden="true"><circle cx="22" cy="22" r="18" stroke="rgba(255,255,255,.18)"/>'
            f'<circle cx="22" cy="22" r="18" stroke="{col}" stroke-linecap="round" stroke-dasharray="{circ * min(100, max(0, score)) / 100:.1f} {circ:.1f}" transform="rotate(-90 22 22)"/>'
            f'<text x="22" y="26.5">{score:.0f}</text></svg>')


def hunt_html(f, live, mk, sa, wide=False):
    """The Opportunity Hunter card: the radar's blips are today's best picks (the examples until a hunt was made); the one pressed
    shows its score, its setup and its plan."""
    from p_scanner import short_name
    from hunter import SETUPS
    name = f"pzh_{mk}"
    real = bool(live and live.get("picks"))
    picks = live["picks"][:4] if real else [{"sym": s, "name": n, "score": sc, "grade": g, "setup": st_, "entry": e, "stop": x, "target": t}
                                              for s, n, sc, g, st_, e, x, t in (EX_SA if sa else EX_US)]
    icons = {k: v[2] for k, v in SETUPS.items()}
    blips, opts = "", ""

    def px(v):
        return "—" if v is None or v != v else T.esc(MK.money(v, dec=2))
    for i, pk in enumerate(picks):
        top, left = BLIPS[i]
        sym = T.esc(T.sym_label(pk["sym"]))
        blips += f'<label class="pzblip pzc" for="{name}_{i}" data-o="{i}" style="top:{top}%;left:{left}%" title="{sym}"></label>'
        head = L("Today's pick", "فرصة اليوم") if real else L(*EXAMPLE)
        opts += (f'<div class="pzo" data-o="{i}"><div class="pzpick"><div class="pzk">{T.esc(head)} · {T.esc(L("press a blip", "اضغط نقطة في الرادار"))}</div>'
                 f'<div class="sy">{_ring(float(pk["score"]), str(pk["grade"]))}<div style="min-width:0"><b class="pzn">{sym}</b>'
                 f'<div class="nm">{T.esc(T.name_line(pk["sym"], pk["name"]))} · {T.esc(L("Grade", "الدرجة"))} {T.esc(pk["grade"])}</div></div></div>'
                 f'<span class="pzsetup">{T.icon(icons.get(pk["setup"], "radar"))}{T.esc(short_name(pk["setup"]) if pk["setup"] else L("Setup", "نمط الدخول"))}</span></div>'
                 f'<div class="pzplan"><div><div class="pzk">{T.esc(L("Entry", "الدخول"))}</div><div class="v pzn">{px(pk.get("entry"))}</div></div>'
                 f'<div><div class="pzk">{T.esc(L("Stop", "الوقف"))}</div><div class="v pzn s">{px(pk.get("stop"))}</div></div>'
                 f'<div><div class="pzk">{T.esc(L("Target", "الهدف"))}</div><div class="v pzn t">{px(pk.get("target"))}</div></div></div></div>')
    stage = f'<div class="pzs pzh"><div class="pzradar"><div class="pzsweep"></div>{blips}</div><div class="pzos">{opts}</div></div>'
    n = f"{f['sa_stocks']}" if sa else f"{f['top']}"
    pts = [L(f"Scans the S&P 500, the {n} largest or your own list", f"يفحص S&P 500 أو أكبر {n} شركة أو قائمتك") if not sa else
           L(f"Scans all {n} Saudi companies, a sector or your own list", f"يفحص كل الشركات السعودية ({n}) أو قطاع أو قائمتك"),
           L(f"{len(SETUPS)} setups: breakout, pullback, squeeze, accumulation day…", f"{len(SETUPS)} نمط دخول: اختراق، ارتداد، انضغاط، يوم تجميع…"),
           L("How the same setup did on the same stock over the last 5 years", "كيف كان نفس النمط على نفس السهم في آخر 5 سنوات"),
           L("Analyst ratings, insider trades and news in one view", "تقييمات المحللين وصفقات المطّلعين والأخبار في مكان واحد")]
    return _radios(name, len(picks)), stage, pts


def xbots_html(f, states, mk, wide=False):
    """The X Bots card: the market's five bots as chips; the one chosen turns the dial to its mood of the last 6 hours and shows
    its beat, with its strongest posts rolling under it (drawn lines until the first read)."""
    import xbots as XB
    from p_xbots import _gauge, _mood_word
    name = f"pzx_{mk}"
    bots = XB.bots_of(mk)
    states = states or {}
    chips, opts = "", ""
    for i, b in enumerate(bots):
        st_ = states.get(b["id"]) or {}
        read = st_.get("read") or {}
        m = read.get("mood6") if read.get("mood6") is not None else read.get("mood24")
        word, col = _mood_word(m)
        posts = [p for p in (read.get("top") or []) if p.get("text")][:4]
        if posts:
            li = "".join(f'<li><span class="av">@</span><span class="tx" dir="auto">{T.esc(p["text"][:90])}</span>'
                         f'<span class="tn {p.get("lab") or "neutral"}">{T.esc({"bull": L("Bullish", "صاعد"), "bear": L("Bearish", "هابط")}.get(p.get("lab"), L("Neutral", "محايد")))}</span></li>'
                         for p in posts)
            feed = f'<div class="pzfeed"><ul>{li}{li}</ul></div>'
        else:
            feed = ('<div class="pzfeed" style="height:auto;mask-image:none;-webkit-mask-image:none"><ul style="animation:none">'
                    + "".join(f'<li><span class="av">@</span><span class="ln"><i style="width:{w}%"></i><i style="width:{w2}%"></i></span></li>' for w, w2 in ((82, 56), (70, 44)))
                    + f'</ul><div class="pzk" style="margin-top:6px">{T.esc(L("The first read comes in the first hour of the market day", "أول قراءة في أول ساعة من يوم السوق"))}</div></div>')
        opts += (f'<div class="pzo" data-o="{i}"><div class="pzg">{_gauge(m, col, 104)}<div class="pzmood"><div class="pzk">{T.esc(L("Mood · 6 h", "المزاج · 6 ساعات"))}</div>'
                 f'<div class="v pzn" style="color:{col}">{"—" if m is None else f"{m:+.0f}"}</div><div class="w" style="color:{col}">{T.esc(word)}</div></div></div>'
                 f'<div class="pzbeat">{T.esc(L(*b["beat"]))}</div>{feed}</div>')
        chips += _label(name, i, L(*b["name"]), b["icon"])
    stage = f'<div class="pzs">{opts}<div class="pzbots">{chips}</div></div>'
    pts = [L(f"{len(bots)} bots, each with its own beat on X", f"{len(bots)} بوتات، كل واحد له تخصص على X"),
           L("A mood from -100 to +100, every post weighted by its reach", "مزاج من -100 لين +100، كل منشور بوزن انتشاره"),
           L("Catches the stock everyone suddenly talks about", "يلقط السهم اللي فجأة صار حديث الناس"),
           L("Long only, with a stop, a target and a time limit on every trade", "شراء فقط، بوقف وهدف ومدة لكل صفقة")]
    return _radios(name, len(bots)), stage, pts


def card_html(key, tool, f, live, mk, sa, wide=False):
    """One card: the hidden radios, the kicker row, the stage and the text, inside the home page's "ovad" frame."""
    page, icon, tone, kick, title, pitch, cta = tool
    ar = is_ar()
    if key == "bots":
        radios, stage, pts = bots_html(f, live, mk, wide)
    elif key == "hunt":
        radios, stage, pts = hunt_html(f, live, mk, sa, wide)
    else:
        radios, stage, pts = xbots_html(f, live, mk, wide)
    xs = T.xify if key == "xbots" else T.esc          # the X bots' card: the letter X drawn as X's logo
    li = "".join(f'<li>{T.icon("check_circle")}<span>{xs(x)}</span></li>' for x in pts)
    text = (f'<div class="tx"><b class="tt">{xs(L(*title))}</b><p>{xs(L(*pitch))}</p><ul>{li}</ul>'
            f'<span class="go">{T.esc(L(*cta))}{T.icon("arrow_forward")}</span></div>')
    from p_overview import _kick_pill
    return (f'<div class="ovad pz {tone}{" rtl" if ar else ""}{" wide" if wide else ""}" data-nogq>{radios}'
            f'<div class="k"><span><span class="ic">{mascot.svg(26, uid="kp" + key)}</span>{xs(L(*kick))}</span>{_kick_pill(key, live)}</div>'
            f'<div class="bd">{stage}{text}</div></div>')
