"""
markets.py - The two markets the site covers: the US market (NYSE / Nasdaq) and the Saudi market (Tadawul).

A visitor picks one (on the landing, or with the switch in the top bar); app.py keeps the choice in the session (and the
browser) and says which market the page being drawn shows: current(). Pages that have a Saudi version follow the choice; the
others still show the US market (app.py puts a note on them), so current() is "us" there.

Code that runs outside a page (a background replay, a scheduled job) never reads the session: it gets the market from what
it works on (a bot's 'market', a symbol's suffix) and passes it on.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

import mcal
import mcal_sa

US, SA = "us", "sa"
CODES = (US, SA)

SPEC = {
    US: {"code": US, "flag": "us", "name": ("US market", "السوق الأمريكي"), "short": ("US", "الأمريكي"),
         "venue": ("NYSE · Nasdaq", "نيويورك · ناسداك"), "tz": "America/New_York", "tz_label": ("ET", "نيويورك"),
         "cur": "USD", "index": "^GSPC", "index_name": ("S&P 500", "إس آند بي 500"), "bench": "SPY",
         "bench_name": ("S&P 500 (SPY)", "إس آند بي 500 (SPY)"), "open": 570, "close": 960, "cal": mcal,
         "options": True, "ext_hours": True, "short_sell": True, "max_leverage": 2.0},
    SA: {"code": SA, "flag": "sa", "name": ("Saudi market", "السوق السعودي"), "short": ("Saudi", "السعودي"),
         "venue": ("Tadawul", "تداول"), "tz": "Asia/Riyadh", "tz_label": ("Riyadh", "الرياض"),
         # Yahoo keeps no history for the TASI index (only its live quote): the benchmark's history is the iShares MSCI Saudi
         # Arabia ETF (KSA), the Saudi market in one fund (priced in dollars; the riyal is pegged, so its moves are the market's)
         "cur": "SAR", "index": "^TASI.SR", "index_name": ("TASI", "تاسي"), "bench": "KSA",
         "bench_name": ("Saudi market (MSCI Saudi Arabia, KSA)", "السوق السعودي (MSCI السعودية، KSA)"), "open": mcal_sa.OPEN, "close": mcal_sa.CLOSE, "cal": mcal_sa,
         "options": False, "ext_hours": False, "short_sell": False, "max_leverage": 1.0},
}

# pages with a Saudi version (app.py's page keys); the rest show the US market for now
SA_PAGES = {"overview", "news", "stock", "screener", "scanner", "paper", "pf_dash", "pf_trade", "pf_analytics", "pf_history",
            "academy", "glossary",
            # 22.1: the Discover, Insight and Calendar pages and the Robo Advisor (its own Saudi account)
            "trending", "newsintel", "brief", "articles", "sentiment", "seasonality", "earnings", "results", "econcal", "holidays",
            "dividends", "splits", "pf_robo",
            # 22.5: the X bots (one of them reads the Saudi market)
            "xbots"}
# no Saudi counterpart: not in the Saudi menus (futures and options don't trade on Tadawul's main market, the economy page is the
# Fed's data, and Yahoo's IPO calendar has no Saudi listings)
US_ONLY = {"futures", "options", "economy", "ipos"}


def _ss():
    try:
        import streamlit as st
        return st.session_state
    except Exception:
        return {}


def choice():
    """The market the visitor picked (us / sa), or None before they picked one."""
    try:
        v = _ss().get("market")
    except Exception:
        return None
    return v if v in CODES else None


def current():
    """The market the page being drawn shows: the visitor's choice on a page that has a Saudi version, else US. Outside a page
    (no session) always US."""
    try:
        v = _ss().get("mkt_page")
    except Exception:
        return US
    return v if v in CODES else US


def pick(code):
    """The visitor picks a market (the landing, the switch in the top line): the session turns to it, the browser keeps it
    (app.py writes it on the next run), and the stock page opens a company of that market."""
    ss = _ss()
    if code not in CODES:
        return
    old = ss.get("market") or US
    if old != code:
        ss[f"symbol_{old}"] = ss.get("symbol")
    ss["market"] = code
    ss["_mk_keep"] = code
    ss["intro_done"] = True
    if of_symbol(ss.get("symbol")) != code:
        ss["symbol"] = ss.get(f"symbol_{code}") or ("2222.SR" if code == SA else "AAPL")


def get(code=None):
    return SPEC.get(code or current(), SPEC[US])


def is_sa(code=None):
    return (code or current()) == SA


def norm(code):
    return code if code in CODES else US


def of_symbol(sym):
    """The market a Yahoo symbol trades on: '.SR' (and the TASI index) is Saudi, the rest US."""
    s = str(sym or "").upper()
    return SA if s.endswith(".SR") or s in ("^TASI", "^TASI.SR") else US


def cal(code=None):
    return get(code)["cal"]


def tz(code=None):
    return ZoneInfo(get(code)["tz"])


def now(code=None):
    """Local time of the market, without a time zone."""
    return datetime.now(tz(code)).replace(tzinfo=None)


def today(code=None):
    return now(code).date()


def name(code=None, ar=False):
    return get(code)["name"][1 if ar else 0]


def money(v, code=None, dec=0, short=False, ar=None):
    """A sum of money in the market's currency: $1,234 / SAR 1,234 (Arabic: 1,234 ر.س); short: $1.2K."""
    import pandas as pd
    if v is None or pd.isna(v):
        return "—"
    if ar is None:
        try:
            ar = _ss().get("lang") == "ar"
        except Exception:
            ar = False
    sign = "-" if v < 0 else ""
    a = abs(float(v))
    num = f"{a:,.{dec}f}"
    if short and a >= 1000:
        for unit, div in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
            if a >= div:
                num = f"{a / div:.1f}{unit}"
                break
    if get(code)["cur"] == "SAR":
        return f"{sign}{num} ر.س" if ar else f"{sign}SAR {num}"
    return f"{sign}${num}"


def big(v, code=None, ar=None):
    """A big sum in the market's currency: $1.20B / SAR 1.20B (Arabic: 1.20B ر.س)."""
    import pandas as pd
    if v is None or pd.isna(v):
        return "—"
    import theme as T
    sign = "-" if v < 0 else ""
    if get(code)["cur"] == "SAR":
        if ar is None:
            try:
                ar = _ss().get("lang") == "ar"
            except Exception:
                ar = False
        return f"{sign}{T.fmt_big(abs(v))} ر.س" if ar else f"{sign}SAR {T.fmt_big(abs(v))}"
    return f"{sign}${T.fmt_big(abs(v))}"


def cur_sign(code=None, ar=None):
    """The currency's sign for labels: $ / SAR (Arabic: ر.س)."""
    if get(code)["cur"] != "SAR":
        return "$"
    if ar is None:
        try:
            ar = _ss().get("lang") == "ar"
        except Exception:
            ar = False
    return "ر.س" if ar else "SAR"


def status(code=None, ar=False):
    """(state text, dot class, local time text) of the market right now."""
    sp = get(code)
    t_ = now(sp["code"])
    m = t_.hour * 60 + t_.minute
    kind, _ = sp["cal"].day_status(t_.date())
    tl = sp["tz_label"][1 if ar else 0]
    if sp["code"] == SA:
        if kind == "weekend":
            st_ = ("السوق مغلق (عطلة)" if ar else "Closed · Weekend"), "closed"
        elif kind == "closed":
            st_ = ("السوق مغلق (إجازة رسمية)" if ar else "Closed · Holiday"), "closed"
        elif mcal_sa.PRE_OPEN <= m < mcal_sa.OPEN:
            st_ = ("مزاد الافتتاح" if ar else "Opening auction"), "pre"
        elif mcal_sa.OPEN <= m < mcal_sa.CLOSE:
            st_ = ("السوق مفتوح" if ar else "Market Open"), "live"
        elif mcal_sa.CLOSE <= m < mcal_sa.LAST_END:
            st_ = ("مزاد الإغلاق" if ar else "Closing auction"), "pre"
        else:
            st_ = ("السوق مغلق" if ar else "Market Closed"), "closed"
        return st_[0], st_[1], f"{t_:%H:%M} {tl}"
    close = 780 if kind == "early" else 960
    if kind == "weekend":
        st_ = ("السوق مغلق (عطلة)" if ar else "Closed · Weekend"), "closed"
    elif kind == "closed":
        st_ = ("السوق مغلق (إجازة رسمية)" if ar else "Closed · Holiday"), "closed"
    elif 570 <= m < close:
        st_ = ("السوق مفتوح" if ar else "Market Open"), "live"
    elif 240 <= m < 570:
        st_ = ("ما قبل الافتتاح" if ar else "Pre-Market"), "pre"
    elif close <= m < 1200:
        st_ = ("ما بعد الإغلاق" if ar else "After-Hours"), "pre"
    else:
        st_ = ("السوق مغلق" if ar else "Market Closed"), "closed"
    return st_[0], st_[1], f"{t_:%H:%M} {tl}"


def session_live(code=None):
    """True while the market's regular session runs (its latest daily candle still moves)."""
    sp = get(code)
    t_ = now(sp["code"])
    kind, _ = sp["cal"].day_status(t_.date())
    if kind in ("weekend", "closed"):
        return False
    m = t_.hour * 60 + t_.minute
    close = 780 if kind == "early" else sp["close"]
    return sp["open"] <= m < close


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "22.5.1"
