"""
app.py - A.Alturaifi Pro · US Markets platform (entry point).
Run locally:  streamlit run app.py
"""
import streamlit as st

import data
import p_academy
import p_bot
import p_markets
import p_research
import theme as T
import ui
import universe as U
from i18n import L

SITE_NAME = "A.Alturaifi Pro"
st.set_page_config(page_title=f"{SITE_NAME} · US Markets", page_icon=":material/candlestick_chart:", layout="wide")

ss = st.session_state
# language: widget state > ?lang= query param (kept by every link on the site) > English
if "lang_ctl" not in ss:
    ss["lang_ctl"] = "عربي" if st.query_params.get("lang") == "ar" else "EN"
ss.lang = "ar" if ss.get("lang_ctl") == "عربي" else ("en" if ss.get("lang_ctl") == "EN" else ss.get("lang", "en"))
ss.setdefault("symbol", "AAPL")
ss.setdefault("watchlist", ["SPY", "QQQ", "AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "META", "GOOGL", "AMD"])
ss.setdefault("lab_cfg", {"symbol": "AAPL", "period": "2y", "strategy": "SMA Crossover", "params": {},
                          "capital": 10000, "fee": 0.05, "stop": 7.0, "atr": 0.0, "tp": 0.0, "trail": 0.0})
ss.setdefault("acct", {"size": 10000, "risk": 1.0})

# links like  stock?symbol=NVDA  (heatmap tiles, company chips, tables) open that company
_qs = st.query_params.get("symbol")
if _qs:
    ss.symbol = str(_qs).strip().upper()[:15] or ss.symbol
    del st.query_params["symbol"]

st.markdown(T.CSS + (T.RTL_CSS if ss.lang == "ar" else ""), unsafe_allow_html=True)
st.logo(T.LOGO_WORDMARK, icon_image=T.LOGO_ICON, size="large")


def _global_search():
    q = (ss.get("gq") or "").strip()
    if not q:
        return
    res = data.search(q)
    sym = res[0]["symbol"] if res else (q.upper() if len(q) <= 6 else None)
    if sym:
        ss.symbol = sym.upper()
        ss.goto = "stock"
    ss.gq = ""


# ---------------------------------------------------------------- pages · dropdown menus (Yahoo / TradingView style)
P = ui.PAGES
P.update({
    "overview": st.Page(p_markets.page_overview, title=L("Overview", "نظرة عامة"), icon=":material/monitoring:", url_path="overview", default=True),
    "futures": st.Page(p_markets.page_futures, title=L("Futures", "العقود الآجلة"), icon=":material/update:", url_path="futures"),
    "options": st.Page(p_markets.page_options, title=L("Options", "الخيارات"), icon=":material/tune:", url_path="options"),
    "economy": st.Page(p_markets.page_economy, title=L("Economy", "الاقتصاد"), icon=":material/account_balance:", url_path="economy"),
    "trending": st.Page(p_markets.page_trending, title=L("What's Trending", "الأكثر رواجاً"), icon=":material/local_fire_department:", url_path="trending"),
    "news": st.Page(p_markets.page_news, title=L("News", "الأخبار"), icon=":material/newspaper:", url_path="news"),
    "stock": st.Page(p_research.page_stock, title=L("Stock", "السهم"), icon=":material/candlestick_chart:", url_path="stock"),
    "screener": st.Page(p_research.page_screener, title=L("Screener", "فلتر الأسهم"), icon=":material/filter_alt:", url_path="screener"),
    "academy": st.Page(p_academy.page_academy, title=L("Courses", "الدورات"), icon=":material/school:", url_path="academy"),
    "glossary": st.Page(p_academy.page_glossary, title=L("Glossary", "قاموس المصطلحات"), icon=":material/menu_book:", url_path="glossary"),
    "auto": st.Page(p_bot.page_autotrader, title=L("Auto Trader", "التداول الآلي"), icon=":material/rocket_launch:", url_path="auto-trader"),
    "scanner": st.Page(p_research.page_scanner, title=L("Scanner", "صائد الفرص"), icon=":material/radar:", url_path="scanner"),
    "catalyst": st.Page(p_research.page_catalyst, title="Catalyst Pro", icon=":material/bolt:", url_path="catalyst"),
    "lab": st.Page(p_bot.page_lab, title=L("Strategy Lab", "مختبر الاستراتيجيات"), icon=":material/smart_toy:", url_path="strategy-lab"),
    "trades": st.Page(p_bot.page_trades, title=L("Trade Journal", "سجل الصفقات"), icon=":material/receipt_long:", url_path="trades"),
})
SECTIONS = [
    (L("Markets", "الأسواق"), "monitoring", ["overview", "futures", "options", "economy"]),
    (L("Discover", "اكتشف"), "explore", ["trending", "news"]),
    (L("Research", "الأبحاث"), "query_stats", ["stock", "screener"]),
    (L("Academy", "الأكاديمية"), "school", ["academy", "glossary"]),
    (L("Trading Bot", "بوت التداول"), "smart_toy", ["auto", "scanner", "catalyst", "lab", "trades"]),
]
# the built-in menu is hidden; the bar below opens its menus on hover and navigates without reloading the site
pg = st.navigation({label: [P[k] for k in keys] for label, _, keys in SECTIONS}, position="hidden")

if ss.get("goto"):
    ui.goto(ss.pop("goto"))

# arriving at the Academy from another page shows the course catalog (unless a course link was opened)
_cur = getattr(pg, "url_path", "")
if ss.get("_page") != _cur:
    if _cur == "academy" and ss.get("_page") is not None and not st.query_params.get("course"):
        ss.pop("course", None)
    ss["_page"] = _cur

# ---------------------------------------------------------------- top bar: hover menus · market status · search · language
def nav_bar():
    cur = getattr(pg, "url_path", "")
    with st.container(key="topnav", horizontal=True, vertical_alignment="center", gap="small"):
        with st.container(key="navleft", horizontal=True, vertical_alignment="center", gap="small"):
            for i, (label, ic, keys) in enumerate(SECTIONS):
                active = any(getattr(P[k], "url_path", None) == cur for k in keys)
                with st.container(key=f"navsec_{i}", width="content"):
                    st.markdown(f'<div class="navbtn{" on" if active else ""}" tabindex="0">{T.icon(ic)}<span>{T.esc(label)}</span>'
                                f'<span class="ms chev">expand_more</span></div>', unsafe_allow_html=True)
                    with st.container(key=f"navdd_{i}"):
                        st.markdown(f'<div class="navhd">{T.esc(label)}</div>', unsafe_allow_html=True)
                        for k in keys:
                            page = P[k]
                            if getattr(page, "url_path", None) == cur:
                                with st.container(key=f"navon_{k}"):
                                    st.page_link(page, label=page.title, icon=page.icon, width="stretch")
                            else:
                                st.page_link(page, label=page.title, icon=page.icon, width="stretch")
        with st.container(key="navright", horizontal=True, vertical_alignment="center", gap="small", width="content"):
            st.markdown(T.market_status(ss.lang == "ar"), unsafe_allow_html=True)
            st.text_input("search", key="gq", on_change=_global_search, label_visibility="collapsed", width=260,
                          placeholder=L("Search symbol or company…", "ابحث عن سهم أو شركة…"))
            st.segmented_control("Language", ["EN", "عربي"], key="lang_ctl", label_visibility="collapsed")


def nav_fallback():
    """Plain menu if this Streamlit version lacks the layout features used above."""
    for label, _, keys in SECTIONS:
        cols = st.columns(len(keys) + 1)
        cols[0].markdown(f"**{label}**")
        for col, k in zip(cols[1:], keys):
            with col:
                st.page_link(P[k], label=P[k].title, icon=P[k].icon)
    a, b = st.columns([3, 1])
    a.text_input("search", key="gq", on_change=_global_search, label_visibility="collapsed",
                 placeholder=L("Search symbol or company…", "ابحث عن سهم أو شركة…"))
    b.segmented_control("Language", ["EN", "عربي"], key="lang_ctl", label_visibility="collapsed")


try:
    nav_bar()
except Exception:
    nav_fallback()

# ---------------------------------------------------------------- sidebar: market pulse + watchlist
ETF_NAMES = {"SPY": "SPDR S&P 500 ETF", "QQQ": "Invesco QQQ · Nasdaq 100", "IWM": "iShares Russell 2000", "DIA": "SPDR Dow Jones",
             "VOO": "Vanguard S&P 500", "VTI": "Vanguard Total Market", "GLD": "SPDR Gold", "TLT": "20+ Year Treasury", "ARKK": "ARK Innovation"}
PULSE = {"^GSPC": "S&P 500", "^IXIC": "Nasdaq", "^DJI": "Dow Jones", "^VIX": "VIX"}


def _name(sym):
    from sp500 import SP500
    if sym in ETF_NAMES:
        return ETF_NAMES[sym]
    if U.known(sym):
        return U.name_of(sym)
    return SP500[sym][0] if sym in SP500 else ""


def _wl_add():
    v = (ss.get("wl_add") or "").strip().upper()
    if v and v not in ss.watchlist:
        ss.watchlist.append(v)
    ss.wl_add = ""


def sidebar():
    px = data.history_many(tuple(list(PULSE) + list(ss.watchlist)), "1mo")

    def last(sym):
        df = px.get(sym)
        if df is None or len(df) < 2:
            return None, None, None
        c = df["Close"].dropna()
        return float(c.iloc[-1]), float((c.iloc[-1] / c.iloc[-2] - 1) * 100), c.tail(22).values
    rows = []
    for sym, name in PULSE.items():
        p, pct, sp = last(sym)
        if p is None:
            continue
        col = T.NEG_FG if (pct < 0) != (sym == "^VIX") else T.POS_FG
        rows.append(f'<div class="pr"><div><div class="n">{name}</div><div class="v">{T.fmt_price(p)}</div></div>'
                    f'{T.sparkline(sp, T.UP if col == T.POS_FG else T.DOWN, 58, 22)}{T.pill(pct, invert=sym == "^VIX")}</div>')
    if rows:
        status = T.market_status(ss.lang == "ar").replace('class="status"', 'class="status mini"')
        st.markdown(f'<div class="pulse"><div class="ph">{T.icon("monitor_heart")}<span>{L("Market pulse", "نبض السوق")}</span>'
                    f'{status}</div>{"".join(rows)}</div>', unsafe_allow_html=True)
    moves = [last(s_)[1] for s_ in ss.watchlist]
    up = sum(1 for m in moves if m is not None and m > 0)
    dn = sum(1 for m in moves if m is not None and m < 0)
    st.markdown(f'<div class="wlh"><span class="t">{T.icon("star")}{L("Watchlist", "قائمة المتابعة")} · {len(ss.watchlist)}</span>'
                f'<span><span class="pill pos" style="min-width:0;padding:1px 7px">▲ {up}</span> '
                f'<span class="pill neg" style="min-width:0;padding:1px 7px">▼ {dn}</span></span></div>'
                + (T.ad_bar(up, dn, max(0, len(ss.watchlist) - up - dn)) if ss.watchlist else ""), unsafe_allow_html=True)
    lg = data.logos(ss.watchlist)
    for s_ in ss.watchlist:
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
                  placeholder=L("+ Add a symbol (e.g. PLTR)", "+ أضف رمزاً (مثال: PLTR)"))
    with st.expander(L("Edit watchlist", "تعديل القائمة"), icon=":material/edit:"):
        txt = st.text_area(L("Symbols (comma separated)", "الرموز (مفصولة بفاصلة)"), ", ".join(ss.watchlist))
        if st.button(L("Save", "حفظ")):
            ss.watchlist = [x.strip().upper() for x in txt.split(",") if x.strip()]
            st.rerun()


with st.sidebar:
    ui.safe(sidebar)

# ---------------------------------------------------------------- page (one error never takes the whole site down)
try:
    pg.run()
except Exception as e:  # Streamlit's own rerun / page-switch signals are not Exceptions, so they pass through
    st.error(L("Something went wrong on this page. Please refresh, or try again in a minute.",
               "حدث خطأ في هذه الصفحة. حدّث الصفحة أو حاول بعد دقيقة."), icon=":material/error:")
    with st.expander(L("Technical details", "تفاصيل فنية")):
        st.exception(e)
