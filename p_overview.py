"""
p_overview.py - The home page (Overview), the site's first screen since 23.4: the logo and the main prices, then what is
moving the market today, starting with what's trending (the breaking stories, the top three stories, the companies in the
news, the market summary and the movers), the market's mood (fear and greed, the news mood), the heat map and the markets.
The site's tools run down the side like adverts (on a tablet or a phone they slide across above the page).
Replaces the landing ("Beyond investment") and the old overview.
"""
import streamlit as st

import data
import home
import markets as MK
import p_calendar as PC
import p_insight as PI
import p_markets as PM
import p_newsintel as PNI
import theme as T
import ui
import universe as U
from i18n import L, is_ar

ss = st.session_state

# the tools down the side: (key, page, icon, tone, title, pitch, call to action). "ai" opens the chat window instead of a page.
TOOLS = [
    ("ai", None, "auto_awesome", "ai", ("TURA AI", "TURA AI"),
     ("Ask about any number, chart or term on the page and get it explained in plain words.",
      "اسأل عن أي رقم أو رسم أو مصطلح بالصفحة، ويشرح لك بكلام بسيط."), ("Start a chat", "ابدأ محادثة")),
    ("hunt", "scanner", "radar", "hunt", ("Opportunity Hunter", "صائد الفرص"),
     ("Today's setups scored out of 100, each with its entry, stop and target.",
      "فرص اليوم بدرجة من 100، ولكل فرصة دخول ووقف وهدف."), ("See today's picks", "شوف فرص اليوم")),
    ("bots", "paper", "smart_toy", "bots", ("Paper Bots", "البوتات الافتراضية"),
     ("Build a trading bot in a minute and let it trade virtual money for you.",
      "ابنِ بوت تداول بدقيقة وخله يتداول عنك بفلوس افتراضية."), ("Build a bot", "ابنِ بوتك")),
    ("pf", "pf_dash", "account_balance_wallet", "pf", ("Paper trading", "التداول الافتراضي"),
     ("Buy and sell at real prices with virtual money, and get a health score for your portfolio.",
      "اشترِ وبع بأسعار حقيقية وفلوس افتراضية، وخذ تقييم لصحة محفظتك من 100."), ("Open my portfolio", "افتح محفظتي")),
    ("robo", "pf_robo", "psychology", "robo", ("Robo Advisor", "المستشار الآلي"),
     ("Answer a few questions and get a portfolio built for your goal and your risk.",
      "جاوب على كم سؤال وخذ محفظة مبنية على هدفك ومخاطرتك."), ("Get my plan", "خذ خطتي")),
    ("academy", "academy", "school", "academy", ("Academy", "الأكاديمية"),
     ("Courses from the basics to options, with labs on real charts.",
      "دورات من الأساسيات إلى الخيارات، مع تطبيقات على رسوم حقيقية."), ("Start learning", "ابدأ التعلّم")),
    ("xbots", "xbots", "alternate_email", "x", ("X Bots", "بوتات X"),
     ("Bots that read X every hour and trade on the market's mood. Who reads it right?",
      "بوتات تقرأ X كل ساعة وتتداول على مزاج السوق. مين يقراه صح؟"), ("Meet the bots", "تعرّف عليها")),
    ("screener", "screener", "filter_alt", "scr", ("Screener", "فلتر الأسهم"),
     ("Filter stocks by value, growth, dividends and technical signals.",
      "فلتر الأسهم حسب القيمة والنمو والتوزيعات والإشارات الفنية."), ("Open the screener", "افتح الفلتر")),
]

CSS = """<style data-lm="keep">
/* the page and its side: the tools stay in view while the page is read (they scroll on their own when taller than the
   screen); on a tablet or a phone they slide across above the page */
[data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] div.st-key-ovrail){align-items:flex-start!important}
[data-testid="stColumn"]:has(div.st-key-ovrail){position:sticky;top:76px;align-self:flex-start}
div.st-key-ovrail{max-height:calc(100vh - 176px);overflow-y:auto;overflow-x:hidden;scrollbar-width:none;padding:2px 2px 10px;gap:12px!important}
div.st-key-ovrail::-webkit-scrollbar{display:none}
.ovrh{display:flex;align-items:center;gap:8px;margin:2px 2px 0;font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#8E97AD}
.ovrh i{flex:1;height:1px;background:linear-gradient(90deg,rgba(142,151,173,.35),transparent)}
/* an advert: a coloured card with its tool's icon, name, one line and a call to action; the whole card opens the tool */
div[class*="st-key-ovad_"]{position:relative}
div[class*="st-key-ovad_"] [data-testid="stElementContainer"]:has([data-testid="stButton"]){position:absolute!important;inset:0;z-index:3;margin:0!important}
div[class*="st-key-ovad_"] [data-testid="stButton"],div[class*="st-key-ovad_"] [data-testid="stButton"] button{width:100%!important;height:100%!important;min-height:100%!important}
div[class*="st-key-ovad_"] [data-testid="stButton"] button{opacity:0!important;cursor:pointer}
.ovad{position:relative;overflow:hidden;isolation:isolate;border-radius:18px;padding:15px 16px 14px;color:#fff;background:linear-gradient(150deg,var(--a1),var(--a2));
  border:1px solid rgba(255,255,255,.1);box-shadow:0 16px 34px -22px var(--sh);transition:transform .28s cubic-bezier(.2,.8,.2,1),box-shadow .28s ease;cursor:pointer}
.ovad .big{position:absolute;inset-inline-end:-12px;bottom:-22px;z-index:-1;font-family:"Material Symbols Rounded";font-size:104px;line-height:1;color:#fff;opacity:.13;transform:rotate(-12deg);transition:transform .5s cubic-bezier(.2,.8,.2,1)}
.ovad .k{display:flex;align-items:center;justify-content:space-between;font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:rgba(255,255,255,.72)}
.ovad .k em{font-style:normal;letter-spacing:.06em;padding:2px 8px;border-radius:999px;background:rgba(255,255,255,.16);color:#fff}
.ovad .ic{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;margin:12px 0 10px;background:rgba(255,255,255,.16);box-shadow:inset 0 1px 0 rgba(255,255,255,.18)}
.ovad .ic .ms{font-size:21px;color:#fff}
.ovad b{display:block;font-size:16px;font-weight:700;line-height:1.3;color:#fff}
.ovad p{margin:5px 0 12px;font-size:12.5px;line-height:1.55;color:rgba(255,255,255,.84)}
.ovad .go{display:inline-flex;align-items:center;gap:6px;padding:7px 12px;border-radius:999px;font-size:12.5px;font-weight:700;color:#fff;background:rgba(255,255,255,.17);transition:background .2s ease}
.ovad .go .ms{font-size:16px;transition:transform .25s cubic-bezier(.2,.8,.2,1)}
.ovad.rtl .go .ms{transform:scaleX(-1)}
div[class*="st-key-ovad_"]:hover .ovad,.ovad.solo:hover{transform:translateY(-3px);box-shadow:0 22px 40px -22px var(--sh)}
div[class*="st-key-ovad_"]:hover .ovad .go,.ovad.solo:hover .go{background:rgba(255,255,255,.26)}
div[class*="st-key-ovad_"]:hover .ovad .go .ms,.ovad.solo:hover .go .ms{transform:translateX(3px)}
div[class*="st-key-ovad_"]:hover .ovad.rtl .go .ms,.ovad.solo.rtl:hover .go .ms{transform:scaleX(-1) translateX(3px)}
div[class*="st-key-ovad_"]:hover .ovad .big,.ovad.solo:hover .big{transform:rotate(-4deg) scale(1.06)}
.ovad.ai{--a1:#1E3A8A;--a2:#6D28D9;--sh:rgba(79,70,229,.75)}
.ovad.hunt{--a1:#0E7490;--a2:#1D4ED8;--sh:rgba(14,116,144,.7)}
.ovad.bots{--a1:#6D28D9;--a2:#BE185D;--sh:rgba(147,51,234,.7)}
.ovad.pf{--a1:#047857;--a2:#0E7490;--sh:rgba(4,120,87,.7)}
.ovad.robo{--a1:#0F766E;--a2:#4338CA;--sh:rgba(15,118,110,.7)}
.ovad.academy{--a1:#B45309;--a2:#C2410C;--sh:rgba(194,65,12,.65)}
.ovad.x{--a1:#111827;--a2:#334155;--sh:rgba(15,23,42,.75)}
.ovad.scr{--a1:#1E40AF;--a2:#0284C7;--sh:rgba(30,64,175,.7)}
/* the market summary in the narrower main column: its tiles two by two */
div.st-key-ovmain .msg{grid-template-columns:repeat(2,minmax(0,1fr))!important}
@media (max-width:640px){div.st-key-ovmain .msg{grid-template-columns:minmax(0,1fr)!important}}
/* the earnings card in the side: one day of the earnings calendar */
.ehub.one{grid-template-columns:1fr!important;margin:0!important}
.ehub.one .day{border-radius:18px}
div.st-key-ovearn [data-testid="stButton"] button{min-height:34px!important;border-radius:999px!important;font-size:12.5px!important}
/* the mood row: the two dials side by side, the same height */
div.st-key-ovmood [data-testid="stHorizontalBlock"]{align-items:stretch!important}
div.st-key-ovmood [data-testid="stColumn"]>div{height:100%}
.ovcard{height:100%;box-sizing:border-box;padding:14px 14px 10px;border-radius:18px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08)}
.ovcard .h{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#C9C4D3;margin-bottom:6px}
.ovcard .h .ms{font-size:18px}
div.st-key-ovmood .nie-hc{height:100%;box-sizing:border-box}
div.st-key-ovmore [data-testid="stButton"] button,div.st-key-ovmore2 [data-testid="stButton"] button{border-radius:999px!important}
/* a tablet or a phone: the tools slide across above the page, one card after another */
@media (max-width:1199px){
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] div.st-key-ovrail){flex-direction:column!important;flex-wrap:nowrap!important;gap:14px!important}
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] div.st-key-ovrail)>[data-testid="stColumn"]{width:100%!important;flex:1 1 auto!important;min-width:0!important;max-width:100%!important}
  [data-testid="stColumn"]:has(div.st-key-ovrail){position:static;order:-1}
  div.st-key-ovrail{flex-direction:row!important;max-height:none;overflow-x:auto;overflow-y:hidden;scroll-snap-type:x mandatory;padding:2px 2px 12px;gap:12px!important}
  div.st-key-ovrail>*{flex:0 0 264px!important;width:264px!important;scroll-snap-align:start}
  div.st-key-ovrail>*:has(.ovrh){display:none!important}
}
@media (max-width:640px){div.st-key-ovrail>*{flex-basis:240px!important;width:240px!important}}
@media (prefers-reduced-motion:reduce){.ovad,.ovad *{transition:none!important}}
</style>"""


def _ad_html(key, icon, tone, title, pitch, cta, solo=False):
    ar = is_ar()
    kick = L("Tool", "أداة") if key != "ai" else L("Assistant", "مساعد")
    free = L("Free", "مجاني")
    attrs = ' data-open-ai="1" role="button" tabindex="0"' if solo else ""
    return (f'<div class="ovad {tone}{" rtl" if ar else ""}{" solo" if solo else ""}" data-nogq{attrs}><span class="big" aria-hidden="true">{icon}</span>'
            f'<div class="k"><span>{T.esc(kick)}</span><em>{T.esc(free)}</em></div><div class="ic">{T.icon(icon)}</div>'
            f'<b>{T.esc(L(*title))}</b><p>{T.esc(L(*pitch))}</p><span class="go">{T.esc(L(*cta))}{T.icon("arrow_forward")}</span></div>')


def _open_tool(key, page):
    if key == "bots":                               # the visitor's own bots, the new bot's form open (p_paper)
        ss["pb_view"] = "mine"
        ss["pb_build"] = True
    ss["goto"] = page


def _rail(sa):
    ui.html(f'<div class="ovrh">{T.esc(L("Tools", "الأدوات"))}<i></i></div>')
    for i, (key, page, icon, tone, title, pitch, cta) in enumerate(TOOLS):
        if sa and page and page not in MK.SA_PAGES:
            continue
        if key == "ai":                             # the chat window opens on the page (theme.FX_JS presses the AI button)
            ui.html(_ad_html(key, icon, tone, title, pitch, cta, solo=True))
            continue
        with st.container(key=f"ovad_{key}"):
            ui.html(_ad_html(key, icon, tone, title, pitch, cta))
            st.button(L(*title), key=f"ovgo_{key}", on_click=_open_tool, args=(key, page), width="stretch")
        if key == "hunt" and not sa:                # the next session's earnings, between the adverts
            with st.container(key="ovearn"):
                got = ui.safe(PC.next_session_html, 8)
                if got:
                    ui.html(got)
                    st.button(L("Earnings calendar", "مواعيد الأرباح"), key="ovgo_earn", icon=":material/event_upcoming:", width="stretch",
                              on_click=_open_tool, args=("earn", "earnings"))


def _chips(px, sa):
    chips = ""
    if sa:
        for s_ in ("^TASI.SR", "2222.SR", "1120.SR", "BZ=F", "GC=F", "DX-Y.NYB"):
            p, _, c = PM._last(px, s_)
            if p is not None:
                chips += f'<span class="chip"><b>{T.esc(PM._sa_name(s_))}</b>{T.fmt_price(p)} {T.pill(c)}</span>'
        return chips
    for s_, name in (("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ"), ("^DJI", "DOW"), ("^TNX", "US10Y"), ("GC=F", "GOLD"), ("BTC-USD", "BTC")):
        p, _, c = PM._last(px, s_)
        if p is not None:
            chips += f'<span class="chip"><b>{name}</b>{f"{p:.2f}%" if s_ == "^TNX" else T.fmt_price(p)} {T.pill(c)}</span>'
            ui.ai_note(name, f"{p:,.2f} ({c:+.2f}% today)" if c is not None else f"{p:,.2f}")
    return chips


def _pick_news(sym):
    ss["nie_tkf"] = sym
    ss["nie_n"] = 12
    ss["goto"] = "newsintel"


def _trending(px, sa):
    ui.header("local_fire_department", "What's trending", "الأكثر رواجاً",
              "The stories moving the market right now, the companies everyone is talking about, and today's biggest moves.",
              "الأخبار اللي تحرّك السوق الحين، والشركات اللي الكل يتكلم عنها، وأكبر تحركات اليوم.")
    snap = ui.safe(PNI.snapshot)
    if snap and snap["res"]:
        ui.html(PNI.breaking_html(snap))
    if sa:
        mv = data.sa_moves()
        lists = PM.sa_lists(mv)
        all_syms = [s_ for df in lists.values() if not df.empty for s_ in df["Symbol"].head(12)]
    else:
        mv = PM._universe_moves()
        lists = {k: PM._list(k, mv) for k in PM.LISTS}
        all_syms = [s_ for df, _ in lists.values() if not df.empty for s_ in df["Symbol"].head(12)]
    ui.sec("newspaper", "Top 3 trending stories", "أهم 3 أخبار رائجة")
    stories = ui.safe(PM.top_stories, 3) or []
    tick = sorted({s_ for n in stories for s_ in n["tickers"]})
    lg = data.logos(list(dict.fromkeys(all_syms + tick)))
    if stories:
        ui.html(PM.stories_html(stories, lg, sa=sa))
    else:
        st.caption(L("No trending stories right now.", "لا توجد أخبار رائجة حالياً."))
    tks = PNI.in_the_news(snap) if snap and snap["res"] else []
    if tks:
        ui.sec("trending_up", "In the news now", "في الأخبار الحين")
        with st.container(key="nie_tks"):
            cols = st.columns(len(tks))
            for col, (sym, n, net, c) in zip(cols, tks):
                with col:
                    with st.container(key="nie_tk_" + sym):
                        ui.html(PNI.tk_card(sym, n, net, c))
                        st.button(sym, key="nie_tb_" + sym, on_click=_pick_news, args=(sym,), width="stretch")
    ui.sec("summarize", "Market summary", "ملخص السوق")
    if sa:
        ui.html(PM.summary_html_sa(px, mv, lists, lg))
    else:
        ui.html(PM.summary_html(PM.summary_data(px, mv, lists), lg))
    if sa and mv.empty:
        st.info(L("Saudi quotes are unavailable right now. Try again in a minute.", "أسعار السوق السعودي غير متاحة حالياً. حاول بعد دقيقة."))
        return snap
    ui.sec("leaderboard", "Movers at a glance", "الأسهم الأكثر حركة")
    PM.movers_grid(lists, lg, sa=sa, per_row=2)
    with st.container(key="ovmore", horizontal=True, gap="small"):
        st.button(L("Everything trending today", "كل اللي رائج اليوم"), key="ovgo_trend", icon=":material/local_fire_department:",
                  on_click=_open_tool, args=("trend", "trending"))
        st.button(L("All the news", "كل الأخبار"), key="ovgo_news", icon=":material/newspaper:", on_click=_open_tool, args=("news", "news"))
    return snap


def _mood(snap):
    ui.sec("speed", "The market's mood", "مزاج السوق")
    v = PI.fg_now()
    with st.container(key="ovmood"):
        a, b = st.columns(2, gap="medium")
        with a:
            if v is not None:
                ui.ai_note("Fear & Greed", f"{v:.0f}/100")
                ui.html(f'<div class="ovcard" data-nogq><div class="h">{T.icon("speed")}{T.esc(L("Fear & Greed", "الخوف والطمع"))}</div>'
                        f'{T.fg_gauge(v, is_ar(), L("Seven market signals in one score", "سبع إشارات من السوق في درجة واحدة"))}</div>')
            else:
                st.caption(L("The Fear & Greed index is not available right now.", "مؤشر الخوف والطمع غير متاح حالياً."))
            st.button(L("What drives it", "وش يحرّكه"), key="ovgo_fg", icon=":material/speed:", width="stretch",
                      on_click=_open_tool, args=("fg", "sentiment"))
        with b:
            if snap and snap["res"]:
                ui.html(PNI.dial_html(snap["res"], snap["hrs"]))
            else:
                st.caption(L("The news mood is not available right now.", "مزاج الأخبار غير متاح حالياً."))
            st.button(L("Read the news like an analyst", "اقرأ الأخبار مثل المحلل"), key="ovgo_ni", icon=":material/neurology:", width="stretch",
                      on_click=_open_tool, args=("ni", "newsintel"))


def _markets(px, sa):
    ui.sec("monitoring", "Markets at a glance", "الأسواق بلمحة")
    groups = PM.SA_TILES if sa else U.MARKET_TILES
    tabs = st.tabs([L(gen, gar) for gen, gar in groups])
    for tab, ((gen, gar), syms) in zip(tabs, groups.items()):
        with tab:
            items = []
            for sym, names in syms.items():
                name = PM._sa_name(sym) if sa else L(*names)
                p, chg, pct = PM._last(px, sym)
                if p is None:
                    items.append(T.tile(name, "—"))
                    continue
                val = f"{p:.3f}%" if gen == "Treasury Yields" else T.fmt_price(p)
                items.append(T.tile(name, val, chg, pct, px[sym]["Close"].tail(22).values, invert=(sym == "^VIX")))
            ui.html(T.tiles(items))
    if not sa:
        ui.safe(PM.indicators_section, True)


def page_overview():
    sa = MK.is_sa()
    ui.html('<span class="css-anchor"></span>\n' + CSS + PNI.CSS + PNI.CSS2)
    ui.html('<span class="css-anchor"></span>\n' + home.CSS)
    px = PM._tile_prices()
    PM.ticker_tape(px)
    ui.html(home.top_html(_chips(px, sa)))
    main, side = st.columns([2.75, 1], gap="large")
    with side:                                      # the tools first: they show at once while the page's data comes in
        with st.container(key="ovrail"):
            _rail(sa)
    with main:
        with st.container(key="ovmain"):
            snap = ui.safe(_trending, px, sa)
            ui.safe(_mood, snap)
            ui.safe(PM.heatmap_section)
            ui.safe(_markets, px, sa)
    if sa:
        st.caption(L("Prices from Yahoo Finance (may be delayed). The Saudi market trades Sunday to Thursday, 10 am to 3 pm Riyadh time.",
                     "الأسعار من Yahoo Finance (قد تكون متأخرة). السوق السعودي يتداول من الأحد للخميس، من 10 الصبح لين 3 العصر بتوقيت الرياض."))
    ui.foot()


BUILD = "23.4.3"
