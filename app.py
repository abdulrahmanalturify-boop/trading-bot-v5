"""
app.py - TURA Pro · US and Saudi markets platform (entry point).
Run locally:  streamlit run app.py
"""
import importlib
import sys

import streamlit as st

# ---------------------------------------------------------------- always run the newest code
# Streamlit Cloud re-reads app.py after every GitHub upload but can keep the other modules (theme, data, ...) from the
# previous version in memory. Every module carries BUILD; if one in memory is older, all of them are reloaded in order.
BUILD = "21.9"
_ORDER = ["terms", "lightmode", "i18n", "ai_assistant", "flags", "mcal", "mcal_sa", "markets", "tasi", "universe", "sp500", "taxonomy", "ta", "academy_visuals", "academy", "insight", "heatmap", "newsiq", "newspics", "theme", "data",
          "caldata", "newsbot", "newsintel", "charts", "engine", "playbooks", "autotrader", "ui", "fairvalue", "segments", "holders", "sharia", "lab", "tdash", "mlbots", "brain", "paperbots", "smartbots", "portfolio", "robobot", "robo", "pfinsight", "p_markets", "p_newsintel", "p_research", "p_insight",
          "p_academy", "p_paper", "p_portfolio", "p_robo", "p_calendar", "hunter", "p_scanner", "home"]
if any(m in sys.modules and getattr(sys.modules[m], "BUILD", None) != BUILD for m in _ORDER):
    for _m in _ORDER:
        if _m in sys.modules:
            try:
                importlib.reload(sys.modules[_m])
            except Exception:
                sys.modules.pop(_m, None)       # imported fresh below

import lightmode as LM

LM.install()                           # the light look: the site's own colours follow Streamlit's theme (⋮ → System / Light / Dark)

import ai_assistant
import data
import newsbot
# Reload the academy revision once for already-running sessions.
if "academy" in sys.modules and getattr(sys.modules["academy"], "ACADEMY_REVISION", None) != "2026-09-27.6":
    for _ac in ("academy_extra", "academy_visuals", "academy_labs", "academy", "p_academy"):
        if _ac in sys.modules:
            importlib.reload(sys.modules[_ac])

import p_academy
import p_calendar
import p_insight
import p_markets
import p_newsintel
import p_paper
import p_portfolio
import p_robo
import p_research
import p_scanner
import markets as MK
import tasi
import theme as T
import ui
import universe as U
from i18n import L

SITE_NAME = "TURA Pro"
st.set_page_config(page_title=f"{SITE_NAME} · Markets", page_icon=":material/candlestick_chart:", layout="wide",
                   menu_items={"About": f"**{SITE_NAME}** · version {BUILD}"})      # the ⋮ menu → About: which version is running

ss = st.session_state
# language: remembered in the session, starts from ?lang= (kept by links and by the address bar) or English
if ss.get("lang") not in ("en", "ar"):
    ss.lang = "ar" if st.query_params.get("lang") == "ar" else "en"
try:
    if ss.lang == "ar" and st.query_params.get("lang") != "ar":
        st.query_params["lang"] = "ar"
    elif ss.lang == "en" and "lang" in st.query_params:
        del st.query_params["lang"]
except Exception:
    pass
ss.setdefault("symbol", "AAPL")
ss.setdefault("watchlist", ["SPY", "QQQ", "AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "META", "GOOGL", "AMD"])
ss.setdefault("watchlist_sa", ["2222.SR", "1120.SR", "1180.SR", "2010.SR", "7010.SR", "1211.SR", "2082.SR", "4013.SR"])
ss.setdefault("acct", {"size": 10000, "risk": 1.0})
ss["_run_n"] = ss.get("_run_n", 0) + 1         # this run (the browser-storage frame is drawn once per run)

# market: the US market or the Saudi market (Tadawul). Remembered in the session; a new visit starts from ?m= (kept in the address
# bar like ?lang=), else from what this browser keeps (the visitor's last choice), else the landing asks.
if ss.get("market") not in MK.CODES:
    _qm = st.query_params.get("m")
    if _qm in MK.CODES:
        ss.market = _qm
    else:
        try:
            _got = p_portfolio.browser()             # None until the browser answers (the first moment of a visit)
        except Exception:
            _got = {}
        if _got is not None and _got.get("tura_mk") in MK.CODES:
            ss.market = _got["tura_mk"]
try:
    if ss.get("market") in MK.CODES and st.query_params.get("m") != ss.market:
        st.query_params["m"] = ss.market
except Exception:
    pass
if ss.get("_mk_keep") in MK.CODES:               # a choice made on the last run: kept in the browser for the next visit
    p_portfolio.keep({"tura_mk": ss.pop("_mk_keep")})

# links like  stock?symbol=NVDA  (heatmap tiles, company chips, tables) open that company
_qs = st.query_params.get("symbol")
if _qs:
    ss.symbol = str(_qs).strip().upper()[:15] or ss.symbol
    del st.query_params["symbol"]
    if MK.of_symbol(ss.symbol) == MK.SA and ss.get("market") != MK.SA:
        ss.market = MK.SA

try:
    newsbot.bot(wait=False)          # the news bot starts collecting in the background
except Exception:
    pass


ETF_NAMES = {"SPY": "SPDR S&P 500 ETF", "QQQ": "Invesco QQQ · Nasdaq 100", "IWM": "iShares Russell 2000", "DIA": "SPDR Dow Jones",
             "VOO": "Vanguard S&P 500", "VTI": "Vanguard Total Market", "GLD": "SPDR Gold", "TLT": "20+ Year Treasury", "ARKK": "ARK Innovation",
             "SMH": "VanEck Semiconductor", "XLK": "Technology Select Sector", "XLF": "Financial Select Sector", "XLE": "Energy Select Sector",
             "SCHD": "Schwab US Dividend Equity", "VYM": "Vanguard High Dividend", "HYG": "iShares High Yield Bond", "IBIT": "iShares Bitcoin Trust"}
EXTRA_SEARCH = {"^GSPC": "S&P 500 Index", "^IXIC": "Nasdaq Composite", "^DJI": "Dow Jones Industrial Average", "^RUT": "Russell 2000 Index",
                "^VIX": "CBOE Volatility Index (VIX)", "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana",
                "GC=F": "Gold futures", "CL=F": "WTI crude oil futures", "ES=F": "S&P 500 futures", "NQ=F": "Nasdaq 100 futures"}


# well-known US-listed names outside the S&P 500 and the site's lists, so typing them shows a suggestion
POPULAR_SEARCH = {
    "TTD": "The Trade Desk", "SE": "Sea Limited", "MELI": "MercadoLibre", "CPNG": "Coupang", "GRAB": "Grab Holdings", "JD": "JD.com",
    "BIDU": "Baidu", "TOST": "Toast", "DKNG": "DraftKings", "CAVA": "CAVA Group", "DUOL": "Duolingo", "ONON": "On Holding",
    "CELH": "Celsius Holdings", "ELF": "e.l.f. Beauty", "CROX": "Crocs", "CHWY": "Chewy", "W": "Wayfair", "SN": "SharkNinja",
    "GME": "GameStop", "AMC": "AMC Entertainment", "ZM": "Zoom Communications", "DOCU": "DocuSign", "TWLO": "Twilio",
    "ESTC": "Elastic", "GTLB": "GitLab", "IOT": "Samsara", "BILL": "BILL Holdings", "ALAB": "Astera Labs",
    "CRDO": "Credo Technology", "NVTS": "Navitas Semiconductor", "TEM": "Tempus AI", "BBAI": "BigBear.ai",
    "QUBT": "Quantum Computing Inc.", "SERV": "Serve Robotics", "RXRX": "Recursion Pharmaceuticals", "HIMS": "Hims & Hers Health",
    "OSCR": "Oscar Health", "PLUG": "Plug Power", "TLN": "Talen Energy", "NNE": "NANO Nuclear Energy", "ACHR": "Archer Aviation",
    "JOBY": "Joby Aviation", "LUNR": "Intuitive Machines", "APLD": "Applied Digital", "CORZ": "Core Scientific", "CIFR": "Cipher Mining",
    "WULF": "TeraWulf", "HUT": "Hut 8", "GLXY": "Galaxy Digital", "CRCL": "Circle Internet Group", "CHYM": "Chime Financial",
    "ETOR": "eToro Group", "BLSH": "Bullish", "FIG": "Figma", "KLAR": "Klarna Group", "OPEN": "Opendoor Technologies",
}


@st.cache_data(ttl=86400, show_spinner=False)
def _search_options_sa(ar):
    """'2222.SR · أرامكو السعودية · Saudi Aramco' for every Saudi company, the biggest first."""
    out = [f"{s} · {tasi.name_of(s, True)} · {tasi.name_of(s)}" if ar else f"{s} · {tasi.name_of(s)} · {tasi.name_of(s, True)}"
           for s in sorted(tasi.SYMBOLS, key=lambda x: (-tasi.cap_b(x), x))]
    return ["^TASI.SR · " + ("مؤشر السوق الرئيسية تاسي" if ar else "TASI · Tadawul All Share Index")] + out


@st.cache_data(ttl=86400, show_spinner=False)
def _search_options():
    """'SYMBOL · Company' for the S&P 500, the site's universe and themes, well-known names outside them, popular ETFs, indices
    and crypto (type-ahead list). Any other symbol can still be typed in full and confirmed."""
    from sp500 import SP500
    from taxonomy import EXTRA
    names = {s: r[0] for s, r in SP500.items()}
    for s in U.STOCKS:
        names.setdefault(s, U.name_of(s))
    for s, r in EXTRA.items():                      # the theme lists' companies (CoreWeave, Nebius, IonQ, Rocket Lab...)
        names.setdefault(s, r[0])
    for s, n in list(POPULAR_SEARCH.items()) + list(ETF_NAMES.items()) + list(EXTRA_SEARCH.items()):
        names.setdefault(s, n)
    big = {s: i for i, s in enumerate(sorted(U.STOCKS, key=lambda x: -U.STOCKS[x][3]))}
    order = sorted(names, key=lambda s: (s not in big, big.get(s, 0), s))
    return [f"{s} · {names[s]}" for s in order]


def _resolve(q):
    q = (q or "").strip()
    if not q:
        return None
    if " · " in q:
        return q.split(" · ", 1)[0].strip().upper()
    if q.isdigit() and len(q) == 4:                 # a Tadawul code: 2222 -> 2222.SR
        return f"{q}.SR"
    hit = tasi.search(q)
    if hit and (MK.choice() == MK.SA or not q.isascii()):
        return hit[0]
    res = data.search(q)
    if res:
        return res[0]["symbol"].upper()
    return q.upper() if len(q) <= 8 and " " not in q else None


def _open_search(value):
    sym = _resolve(value)
    if sym:
        ss.symbol = sym
        ss.goto = "stock"
    else:
        ss.search_miss = value


def _pick_search():
    v = ss.get("gq_sel")
    ss["gq_sel"] = None
    if v:
        _open_search(str(v))


def _global_search():
    q = (ss.get("gq") or "").strip()
    ss.gq = ""
    if q:
        _open_search(q)


def search_box():
    """Wide type-ahead search: suggestions while typing, any symbol or company name accepted."""
    sa = MK.choice() == MK.SA
    ph = (L("Search a company or code…  e.g. 2222, Aramco, Al Rajhi", "ابحث عن شركة أو رمز…  مثال: 2222، أرامكو، الراجحي") if sa else
          L("Search a symbol or company…  e.g. NVDA, Apple, Bitcoin", "ابحث عن سهم أو شركة…  مثال: NVDA، أبل، بيتكوين"))
    opts = (_search_options_sa(ss.lang == "ar") + _search_options()) if sa else (_search_options() + _search_options_sa(ss.lang == "ar"))
    try:
        st.selectbox("search", opts, index=None, key="gq_sel", on_change=_pick_search, placeholder=ph,
                     accept_new_options=True, label_visibility="collapsed")
    except TypeError:   # older Streamlit without accept_new_options
        st.text_input("search", key="gq", on_change=_global_search, label_visibility="collapsed", placeholder=ph)


# ---------------------------------------------------------------- pages · hover menus (Yahoo / TradingView style)
P = ui.PAGES
P.update({
    "overview": st.Page(p_markets.page_overview, title=L("Overview", "نظرة عامة"), icon=":material/monitoring:", url_path="overview", default=True),
    "futures": st.Page(p_markets.page_futures, title=L("Futures", "العقود الآجلة"), icon=":material/update:", url_path="futures"),
    "options": st.Page(p_markets.page_options, title=L("Options", "الخيارات"), icon=":material/tune:", url_path="options"),
    "economy": st.Page(p_markets.page_economy, title=L("Economy", "الاقتصاد"), icon=":material/account_balance:", url_path="economy"),
    "trending": st.Page(p_markets.page_trending, title=L("What's Trending", "الأكثر رواجاً"), icon=":material/local_fire_department:", url_path="trending"),
    "news": st.Page(p_markets.page_news, title=L("News", "الأخبار"), icon=":material/newspaper:", url_path="news"),
    "newsintel": st.Page(p_newsintel.page_news_intel, title=L("News Intelligence Engine", "محرك ذكاء الأخبار"), icon=":material/neurology:",
                         url_path="news-intelligence"),
    "stock": st.Page(p_research.page_stock, title=L("Stock", "السهم"), icon=":material/candlestick_chart:", url_path="stock"),
    "screener": st.Page(p_research.page_screener, title=L("Screener", "فلتر الأسهم"), icon=":material/filter_alt:", url_path="screener"),
    "brief": st.Page(p_insight.page_brief, title=L("Daily Brief", "الموجز اليومي"), icon=":material/summarize:", url_path="brief"),
    "articles": st.Page(p_insight.page_articles, title=L("Articles", "المقالات"), icon=":material/article:", url_path="articles"),
    "sentiment": st.Page(p_insight.page_sentiment, title=L("Fear & Greed", "مؤشر الخوف والطمع"), icon=":material/speed:", url_path="sentiment"),
    "seasonality": st.Page(p_insight.page_seasonality, title=L("Seasonality", "الموسمية"), icon=":material/event_repeat:", url_path="seasonality"),
    "earnings": st.Page(p_calendar.page_earnings_hub, title=L("Earnings Calendar", "مواعيد إعلانات الأرباح"), icon=":material/event_upcoming:",
                        url_path="earnings-calendar"),
    "results": st.Page(p_calendar.page_earnings_results, title=L("Earnings", "نتائج الأرباح"), icon=":material/request_quote:",
                       url_path="earnings-results"),
    "econcal": st.Page(p_calendar.page_econ_calendar, title=L("Economic Calendar", "التقويم الاقتصادي"), icon=":material/event_note:",
                       url_path="economic-calendar"),
    "holidays": st.Page(p_calendar.page_holidays, title=L("Holiday Calendar", "عطلات السوق"), icon=":material/beach_access:", url_path="market-holidays"),
    "dividends": st.Page(p_calendar.page_dividends, title=L("Dividend Calendar", "تقويم التوزيعات"), icon=":material/payments:", url_path="dividend-calendar"),
    "splits": st.Page(p_calendar.page_splits, title=L("Splits Calendar", "تقسيم الأسهم"), icon=":material/call_split:", url_path="stock-splits"),
    "ipos": st.Page(p_calendar.page_ipos, title=L("IPO Calendar", "الاكتتابات العامة"), icon=":material/rocket_launch:", url_path="ipo-calendar"),
    "academy": st.Page(p_academy.page_academy, title=L("Courses", "الدورات"), icon=":material/school:", url_path="academy"),
    "glossary": st.Page(p_academy.page_glossary, title=L("Glossary", "قاموس المصطلحات"), icon=":material/menu_book:", url_path="glossary"),
    "pf_dash": st.Page(p_portfolio.page_dashboard, title=L("Dashboard", "لوحة المحفظة"), icon=":material/space_dashboard:", url_path="portfolio"),
    "pf_trade": st.Page(p_portfolio.page_trade, title=L("Trade", "تداول"), icon=":material/swap_horiz:", url_path="portfolio-trade"),
    "pf_analytics": st.Page(p_portfolio.page_analytics, title=L("Analytics", "التحليلات"), icon=":material/query_stats:", url_path="portfolio-analytics"),
    "pf_history": st.Page(p_portfolio.page_history, title=L("Orders & History", "الأوامر والسجل"), icon=":material/receipt_long:",
                          url_path="portfolio-history"),
    "pf_robo": st.Page(p_robo.page_robo, title=L("Robo Advisor", "المستشار الآلي"), icon=":material/smart_toy:", url_path="robo-advisor"),
    "paper": st.Page(p_paper.page_paper_bots, title=L("Paper Bots", "البوتات الافتراضية"), icon=":material/robot_2:", url_path="paper-bots"),
    "scanner": st.Page(p_scanner.page_scanner, title=L("Scanner", "صائد الفرص"), icon=":material/radar:", url_path="scanner"),
})
SECTIONS = [
    (L("Markets", "الأسواق"), "monitoring", ["overview", "futures", "options", "economy"]),
    (L("Discover", "اكتشف"), "explore", ["trending", "news", "newsintel"]),
    (L("Research", "الأبحاث"), "query_stats", ["stock", "screener"]),
    (L("Calendar", "التقويم"), "calendar_month", ["earnings", "results", "econcal", "holidays", "dividends", "splits", "ipos"]),
    (L("Insight", "رؤى"), "lightbulb", ["brief", "articles", "sentiment", "seasonality"]),
    (L("Academy", "الأكاديمية"), "school", ["academy", "glossary"]),
    (L("Portfolio", "المحفظة"), "account_balance_wallet", ["pf_dash", "pf_trade", "pf_analytics", "pf_history", "pf_robo"]),
    (L("Trading Bot", "بوت التداول"), "smart_toy", ["paper", "scanner"]),
]
# the built-in menu is hidden; the bar below opens its menus on hover and navigates without reloading the site
pg = st.navigation({label: [P[k] for k in keys] for label, _, keys in SECTIONS}, position="hidden")


def menu_sections():
    """The bar's menus: the Saudi market leaves out the pages that only exist for the US market (futures, options, the economy)."""
    if MK.choice() != MK.SA:
        return SECTIONS
    return [(lab, ic, [k for k in keys if k not in MK.US_ONLY]) for lab, ic, keys in SECTIONS if any(k not in MK.US_ONLY for k in keys)]


# the market this page shows: the visitor's choice on a page that has a Saudi version, else the US market (see markets.py)
_KEY_OF = {getattr(pg_, "url_path", None): k for k, pg_ in P.items()}
_PAGE_KEY = _KEY_OF.get(getattr(pg, "url_path", ""), "overview" if getattr(pg, "url_path", "") == "" else None)
ss["mkt_page"] = MK.SA if MK.choice() == MK.SA and _PAGE_KEY in MK.SA_PAGES else MK.US
p_portfolio.PF.use(ss["mkt_page"])     # the paper portfolio's session hours and calendar on this run (the Robo Advisor: US)

try:                                   # the saved paper bots are replayed in the background, so the Paper Bots page opens at once
    p_paper.PB.warm()
except Exception:
    pass

if ss.get("goto"):
    ui.goto(ss.pop("goto"))
if ss.get("search_miss"):
    st.toast(L(f"No match for “{ss.search_miss}”. Try a ticker such as NVDA.", f"لا توجد نتيجة لـ «{ss.search_miss}». جرّب رمزاً مثل NVDA."),
             icon=":material/search_off:")
    ss.pop("search_miss")

# arriving at the Academy from another page shows the course catalog (unless a course link was opened)
_cur = getattr(pg, "url_path", "")
# Overview opened from another page (the top bar, a link): straight to the home page with the market overview under it.
# The landing stays the site's first screen (a visit that starts at the address) and what the logo brings back.
if _cur in ("", "overview"):
    if not ss.pop("_to_landing", False) and ss.get("_page") not in (None, "", "overview"):
        ss["intro_done"] = True
if ss.get("_page") != _cur:
    if _cur == "academy" and ss.get("_page") is not None and not st.query_params.get("course"):
        ss.pop("course", None)
    if _cur == "articles" and ss.get("_page") is not None and not st.query_params.get("a"):
        ss.pop("article", None)
    ss["_page"] = _cur

# ---------------------------------------------------------------- the site's styles, in the visitor's look
# Light or dark follows the theme picked in Streamlit's ⋮ menu (System / Light / Dark); the landing keeps its night in both.
_light = LM.start(landing=_cur in ("", "overview") and not ss.get("intro_done"))
try:
    _static = bool(st.get_option("server.enableStaticServing"))
except Exception:
    _static = False
_bg = LM.background_css(f"app/static/{LM.BG_FILE}" if _static else LM.BG_CDN) if _light else T.background_css(_static)
st.markdown(f'<span class="css-anchor" data-th="{ss.get(LM.THEME_KEY, "dark")}"></span>' + T.CSS + _bg + (T.RTL_CSS if ss.lang == "ar" else "")
            + LM.landing_css() + T.logo_glow_css(_light), unsafe_allow_html=True)
st.logo(T.logo_wordmark(_light), icon_image=T.LOGO_ICON_LIGHT if _light else T.LOGO_ICON, size="large")
try:                                   # interactive cards: the light follows the pointer (a script run once per browser tab)
    import streamlit.components.v1 as _components
    st.markdown('<span class="css-anchor"></span>\n' + T.FX_CSS, unsafe_allow_html=True)   # the style on its own line (else Markdown eats it)
    _components.html(T.FX_JS, height=0)
except Exception:
    pass
with st.container(key="lmsync"):          # hidden; theme.FX_JS presses it when the page was drawn for the other look
    st.button("theme", key="lm_sync_btn")


# ---------------------------------------------------------------- top bar (in the site's top line): menus · search · market status · language
LANGS = [("en", "us", "English", "الإنجليزية"), ("ar", "sa", "العربية", "Arabic")]


def _set_lang(code):
    ss.lang = code


def _set_market(code):
    """The market switch: the site turns to that market (kept in this browser for the next visit)."""
    if code not in MK.CODES or code == ss.get("market"):
        return
    MK.pick(code)
    if code == MK.SA and _PAGE_KEY in MK.US_ONLY:       # a page the Saudi market doesn't have: its overview
        ss["goto"] = "overview"


def market_switch():
    """Two flags in the top line: the US market / the Saudi market (Tadawul)."""
    cur = MK.choice() or MK.US
    with st.container(key="mktsw", horizontal=True, vertical_alignment="center", gap="small", width="content"):
        for code in MK.CODES:
            sp = MK.SPEC[code]
            on = code == cur
            with st.container(key=f"mkt_{code}{'_on' if on else ''}", width="content"):
                st.button(L("US", "أمريكي") if code == MK.US else L("Saudi", "سعودي"), key=f"mktb_{code}",
                          on_click=_set_market, args=(code,), help=L(*sp["name"]) + " · " + L(*sp["venue"]))


def lang_menu():
    cur = ss.lang
    with st.container(key="langsec", width="content"):
        st.markdown(f'<div class="langbtn" tabindex="0" title="Language · اللغة"><span class="ms lic">translate</span><b class="lcode">{"ع" if cur == "ar" else "EN"}</b>'
                    f'<span class="ms chev">expand_more</span></div>', unsafe_allow_html=True)
        with st.container(key="langdd"):
            st.markdown(f'<div class="navhd">{L("Language", "اللغة")} · {L("اللغة", "Language")}</div>', unsafe_allow_html=True)
            for code, fl, native, other in LANGS:
                on = code == cur
                sub = f"<small>{other}</small>" if code != cur else ""        # the name in the other language, e.g. العربية · Arabic
                with st.container(key=f"langopt_{code}"):
                    st.markdown(f'<div class="lopt{" on" if on else ""}"><span class="lcode">{"ع" if code == "ar" else "EN"}</span><span class="nm"><b>{native}</b>{sub}</span>'
                                + ('<span class="ms ck">check_circle</span>' if on else "") + "</div>", unsafe_allow_html=True)
                    st.button(native, key=f"langb_{code}", on_click=_set_lang, args=(code,), width="stretch")


def nav_bar():
    cur = getattr(pg, "url_path", "")
    with st.container(key="topnav", horizontal=True, vertical_alignment="center", gap="small"):
        with st.container(key="navleft", horizontal=True, vertical_alignment="center", gap="small", width="content"):
            for i, (label, ic, keys) in enumerate(menu_sections()):
                active = any(getattr(P[k], "url_path", None) == cur for k in keys)
                with st.container(key=f"navsec_{i}", width="content"):
                    st.markdown(f'<div class="navbtn{" on" if active else ""}" tabindex="0" title="{T.esc(label)}">{T.icon(ic)}'
                                f'<span>{T.esc(label)}</span><span class="ms chev">expand_more</span></div>', unsafe_allow_html=True)
                    with st.container(key=f"navdd_{i}"):
                        st.markdown(f'<div class="navhd">{T.esc(label)}</div>', unsafe_allow_html=True)
                        for k in keys:
                            page = P[k]
                            if getattr(page, "url_path", None) == cur:
                                with st.container(key=f"navon_{k}"):
                                    st.page_link(page, label=page.title, icon=page.icon, width="stretch")
                            else:
                                st.page_link(page, label=page.title, icon=page.icon, width="stretch")
        with st.container(key="navsearch"):
            search_box()
        with st.container(key="navright", horizontal=True, vertical_alignment="center", gap="small", width="content"):
            st.markdown(T.market_status(ss.lang == "ar", MK.choice() or MK.US), unsafe_allow_html=True)
            market_switch()
            lang_menu()


def nav_fallback():
    """Plain menu if this Streamlit version lacks the layout features used above."""
    for label, _, keys in menu_sections():
        cols = st.columns(len(keys) + 1)
        cols[0].markdown(f"**{label}**")
        for col, k in zip(cols[1:], keys):
            with col:
                st.page_link(P[k], label=P[k].title, icon=P[k].icon)
    a, b, c = st.columns([4, 1, 1])
    a.text_input("search", key="gq", on_change=_global_search, label_visibility="collapsed",
                 placeholder=L("Search a symbol or company…", "ابحث عن سهم أو شركة…"))
    b.button("English", key="fb_en", on_click=_set_lang, args=("en",), width="stretch")
    c.button("العربية", key="fb_ar", on_click=_set_lang, args=("ar",), width="stretch")
    d, e = st.columns(2)
    d.button(L("US market", "السوق الأمريكي"), key="fb_us", on_click=_set_market, args=(MK.US,), width="stretch")
    e.button(L("Saudi market", "السوق السعودي"), key="fb_sa", on_click=_set_market, args=(MK.SA,), width="stretch")


try:
    nav_bar()
except Exception:
    nav_fallback()


def _logo_home():
    """The logo was clicked: back to the landing (the home page's first screen)."""
    ss["intro_done"] = False
    ss["_to_landing"] = True
    ss["goto"] = "overview"


with st.container(key="logohome"):          # hidden; theme.FX_JS presses it when the logo is clicked
    st.button("home", key="logo_home_btn", on_click=_logo_home)

# ---------------------------------------------------------------- sidebar: market pulse + watchlist
PULSE = {"^GSPC": "S&P 500", "^IXIC": "Nasdaq", "^DJI": "Dow Jones", "^VIX": "VIX"}
PULSE_SA = {"^TASI.SR": ("TASI", "تاسي"), "2222.SR": ("Saudi Aramco", "أرامكو"), "1120.SR": ("Al Rajhi", "الراجحي"), "BZ=F": ("Brent crude", "خام برنت")}


def _name(sym):
    from sp500 import SP500
    if tasi.known(sym):
        return tasi.name_of(sym, ss.lang == "ar")
    if sym in ETF_NAMES:
        return ETF_NAMES[sym]
    if U.known(sym):
        return U.name_of(sym)
    return SP500[sym][0] if sym in SP500 else ""


def _wl_key():
    """The session key of the chosen market's watchlist."""
    return "watchlist_sa" if MK.choice() == MK.SA else "watchlist"


def _wl_add():
    v = (ss.get("wl_add") or "").strip().upper()
    if v.isdigit() and len(v) == 4:
        v += ".SR"
    wl = ss[_wl_key()]
    if v and v not in wl:
        wl.append(v)
    ss.wl_add = ""


def sidebar():
    sa = MK.choice() == MK.SA
    pulse = {k: v[1 if ss.lang == "ar" else 0] for k, v in PULSE_SA.items()} if sa else PULSE
    wl = ss[_wl_key()]
    px = data.history_many(tuple(list(pulse) + list(wl)), "1mo")
    if sa:
        px = data.with_quotes(px, ["^TASI.SR"])

    def last(sym):
        df = px.get(sym)
        if df is None or len(df) < 2:
            return None, None, None
        c = df["Close"].dropna()
        return float(c.iloc[-1]), float((c.iloc[-1] / c.iloc[-2] - 1) * 100), c.tail(22).values
    rows = []
    for sym, name in pulse.items():
        p, pct, sp = last(sym)
        if p is None:
            continue
        col = T.NEG_FG if (pct < 0) != (sym == "^VIX") else T.POS_FG
        rows.append(f'<div class="pr"><div><div class="n">{name}</div><div class="v">{T.fmt_price(p)}</div></div>'
                    f'{T.sparkline(sp, T.UP if col == T.POS_FG else T.DOWN, 58, 22)}{T.pill(pct, invert=sym == "^VIX")}</div>')
    if rows:
        status = T.market_status(ss.lang == "ar", MK.choice() or MK.US).replace('class="status"', 'class="status mini"')
        st.markdown(f'<div class="pulse"><div class="ph">{T.icon("monitor_heart")}<span>{L("Market pulse", "نبض السوق")}</span>'
                    f'{status}</div>{"".join(rows)}</div>', unsafe_allow_html=True)
    moves = [last(s_)[1] for s_ in wl]
    up = sum(1 for m in moves if m is not None and m > 0)
    dn = sum(1 for m in moves if m is not None and m < 0)
    st.markdown(f'<div class="wlh"><span class="t">{T.icon("star")}{L("Watchlist", "قائمة المتابعة")} · {len(wl)}</span>'
                f'<span><span class="pill pos" style="min-width:0;padding:1px 7px">▲ {up}</span> '
                f'<span class="pill neg" style="min-width:0;padding:1px 7px">▼ {dn}</span></span></div>'
                + (T.ad_bar(up, dn, max(0, len(wl) - up - dn)) if wl else ""), unsafe_allow_html=True)
    lg = data.logos(wl)
    for s_ in wl:
        p, pct, sp = last(s_)
        with st.container(key=f"wlr_{s_}"):
            right = (f'<div class="r"><div class="p">{T.fmt_price(p)}</div>{T.pill(pct)}</div>' if p is not None
                     else '<div class="r"><div class="p muted">—</div></div>')
            spark = T.sparkline(sp, T.UP if (pct or 0) >= 0 else T.DOWN, 56, 22) if sp is not None else "<span></span>"
            st.markdown(f'<div class="wlr"><div class="l">{T.logo_circle(s_, lg.get(s_), 30)}<div class="nm"><b>{T.esc(s_)}</b>'
                        f'<span>{T.esc(_name(s_))}</span></div></div>{spark}{right}</div>', unsafe_allow_html=True)
            if st.button(s_, key=f"wl_{s_}", width="stretch"):
                ui.open_stock(s_)
    st.text_input("add", key="wl_add", on_change=_wl_add, label_visibility="collapsed",
                  placeholder=L("+ Add a code (e.g. 2222)", "+ أضف رمزاً (مثال: 2222)") if sa else L("+ Add a symbol (e.g. PLTR)", "+ أضف رمزاً (مثال: PLTR)"))
    with st.expander(L("Edit watchlist", "تعديل القائمة"), icon=":material/edit:"):
        txt = st.text_area(L("Symbols (comma separated)", "الرموز (مفصولة بفاصلة)"), ", ".join(wl))
        if st.button(L("Save", "حفظ")):
            ss[_wl_key()] = [(x.strip().upper() + (".SR" if x.strip().isdigit() and len(x.strip()) == 4 else "")) for x in txt.split(",") if x.strip()]
            st.rerun()


with st.sidebar:
    ui.safe(sidebar)

# ---------------------------------------------------------------- page (one error never takes the whole site down)
if MK.choice() == MK.SA and _PAGE_KEY in MK.US_ONLY:
    st.info(L("This page is for the US market only: the Saudi market has nothing like it, so it isn't in the Saudi menus.",
              "هالصفحة للسوق الأمريكي فقط: ما لها مقابل في السوق السعودي، عشان كذا ما تطلع في قوائم السوق السعودي."), icon=":material/flag:")
elif MK.choice() == MK.SA and _PAGE_KEY not in MK.SA_PAGES and not (_PAGE_KEY == "overview"):
    st.info(L("This page shows the US market for now; its Saudi version is on the way. The Saudi market's pages: Overview, News, "
              "Stock, Screener, Scanner, Paper Bots and Portfolio.",
              "هالصفحة تعرض السوق الأمريكي حالياً، ونسختها السعودية جاية. صفحات السوق السعودي: النظرة العامة، والأخبار، والسهم، "
              "والفلتر، وصائد الفرص، والبوتات الافتراضية، والمحفظة."), icon=":material/flag:")
try:
    pg.run()
except Exception as e:  # Streamlit's own rerun / page-switch signals are not Exceptions, so they pass through
    st.error(L("Something went wrong on this page. Please refresh, or try again in a minute.",
               "حدث خطأ في هذه الصفحة. حدّث الصفحة أو حاول بعد دقيقة."), icon=":material/error:")
    with st.expander(L("Technical details", "تفاصيل فنية")):
        st.exception(e)

# Persistent visitor assistant: page-aware, bilingual, and fixed over every page.
try:
    ai_assistant.render(
        page_path=getattr(pg, "url_path", "") or "",
        page_title=getattr(pg, "title", "") or "",
        symbol=ss.get("symbol", "") or "",
        lang=ss.get("lang", "en"),
    )
except Exception:
    pass
