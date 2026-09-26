"""
p_paper.py - Paper Bots: up to 5 bots that trade with virtual money on real prices, forward from the day they start.
Each bot trades one company, a sector, an industry or all companies, with one or more Strategy Lab strategies.
Leaderboard · comparison chart · details of one bot (orders, equity, trading dashboard, charts, trades) · manage (add / delete).
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import autotrader
import charts
import data
import engine
import mcal
import paperbots as PB
import ta
import tdash
import theme as T
import ui
from i18n import L, sector_name
from sp500 import gics_name

ss = st.session_state
KIND_LABEL = {"company": ("One company", "شركة"), "sector": ("A sector", "قطاع"), "industry": ("An industry", "صناعة"),
              "all": ("All companies", "كل الشركات")}
KIND_ICON = {"company": "domain", "sector": "category", "industry": "factory", "all": "public"}
OVERLAYS = {"SMA Crossover": ["SMA 20", "SMA 50"], "Golden Cross (50/200)": ["SMA 50", "SMA 200"],
            "EMA Crossover": ["EMA 9", "EMA 21"], "Bollinger Breakout": ["Bollinger Bands"]}
PANELS = {"RSI Mean Reversion": ["RSI"], "MACD Crossover": ["MACD"], "OBV Trend (Volume)": ["OBV"], "MFI Money Flow (Volume)": ["MFI"]}
# buttons inside a container whose key starts with "pbred" get red text and a red outline (Delete, No)
RED_CSS = (f'<style>[class*="st-key-pbred"] button {{ border-color: {T.DOWN}88 !important; }}'
           f'[class*="st-key-pbred"] button p, [class*="st-key-pbred"] button span {{ color: {T.DOWN} !important; }}'
           f'[class*="st-key-pbred"] button:hover {{ border-color: {T.DOWN} !important; background: {T.DOWN}1A !important; }}</style>')
DEFAULTS = {"pb_name": "", "pb_capital": 100000, "pb_kind": "company", "pb_symbol": "AAPL", "pb_sector": "Technology",
            "pb_ind_sector": "Technology", "pb_industry": "Semiconductors", "pb_maxpos": 5, "pb_strats": ["SMA Crossover"],
            "pb_fee": 0.05, "pb_stop": 2.0, "pb_atr": 0.0, "pb_tp": 0.0, "pb_trail": 0.0}


def strat_name(k):
    return L(k, engine.STRATEGY_AR.get(k, k))


def strat_short(k):
    return strat_name(k).split(" (")[0]


def universe_label(bot, count=None):
    k, v = bot["kind"], bot["value"]
    if k == "company":
        return v
    if k == "sector":
        txt = L("Sector · ", "قطاع · ") + sector_name(v)
    elif k == "industry":
        txt = L("Industry · ", "صناعة · ") + gics_name(v)
    else:
        txt = L("All companies", "كل الشركات")
    if count:
        txt += L(f" ({count} stocks)", f" ({count} سهم)")
    return txt


def strategies_label(names, short=False):
    n = len(names)
    if n == len(engine.STRATEGIES):
        return L(f"All {n} strategies", f"كل الاستراتيجيات ({n})")
    if short and n > 2:
        return L(f"{n} strategies", f"{n} استراتيجيات")
    return " + ".join(strat_short(s) for s in names) or "—"


def _params_txt(name, params):
    spec = engine.STRATEGIES.get(name, (None, []))[1]
    labels = {k: L(lab, engine.PARAM_AR.get(lab, lab)) for k, lab, *_ in spec}
    return " · ".join(f"{labels.get(k, k)} {v:g}" for k, v in params.items())


def _risk_txt(bot):
    out = []
    for k, en, ar_, suf in (("stop_pct", "Stop", "وقف", "%"), ("atr_mult", "ATR stop ×", "وقف ATR ×", ""),
                            ("tp_pct", "Target", "هدف", "%"), ("trail_pct", "Trailing", "متحرك", "%")):
        if bot[k]:
            out.append(f"{L(en, ar_)} {bot[k]:g}{suf}")
    return " · ".join(out) or L("No stop", "بدون وقف")


def _session_live():
    """True while the US market is open (the latest daily candle is still moving)."""
    now = datetime.now(ZoneInfo("America/New_York"))
    kind, _ = mcal.day_status(now.date())
    close = 780 if kind == "early" else 960
    return now.weekday() < 5 and kind != "closed" and 570 <= now.hour * 60 + now.minute < close


# =====================================================================
# storage messages
# =====================================================================
def setup_steps():
    steps = L(
        "<b>1.</b> Create a free account at <b>supabase.com</b> and press <b>New project</b> (any name and password, the closest region).<br>"
        "<b>2.</b> In the project open <b>SQL Editor</b>, paste the code below and press <b>Run</b>. It creates the table for the bots.<br>"
        "<b>3.</b> Open <b>Project Settings</b> and copy the <b>Project ID</b> (the URL is https://PROJECT-ID.supabase.co), then open "
        "<b>API Keys</b> and copy the <b>secret</b> key (it starts with <code>sb_secret_</code>). Never use it in a public place; "
        "it only goes into Streamlit Secrets.<br>"
        "<b>4.</b> In Streamlit open your app's <b>Settings → Secrets</b> and add the three lines below under your FRED key, then press <b>Save</b>.",
        "<b>1.</b> سجّل حساب مجاني في <b>supabase.com</b> واضغط <b>New project</b> (أي اسم وكلمة مرور، واختر أقرب منطقة).<br>"
        "<b>2.</b> داخل المشروع افتح <b>SQL Editor</b>، والصق الكود اللي تحت واضغط <b>Run</b>. هذا ينشئ جدول البوتات.<br>"
        "<b>3.</b> افتح <b>Project Settings</b> وانسخ <b>Project ID</b> (الرابط يصير https://المعرّف.supabase.co)، ثم افتح <b>API Keys</b> "
        "وانسخ المفتاح <b>secret</b> (يبدأ بـ <code>sb_secret_</code>). لا تحطه في أي مكان عام، مكانه الوحيد Secrets في Streamlit.<br>"
        "<b>4.</b> في Streamlit افتح <b>Settings ← Secrets</b> للموقع، وأضف الأسطر الثلاثة اللي تحت تحت مفتاح FRED، ثم اضغط <b>Save</b>.")
    ui.html(f'<div style="line-height:2">{steps}</div>')
    st.code(PB.SETUP_SQL, language="sql")
    st.code('SUPABASE_URL = "https://xxxx.supabase.co"\nSUPABASE_KEY = "sb_secret_..."\nBOTS_PASSWORD = "' +
            L("choose-a-password", "اختر-كلمة-مرور") + '"', language="toml")


def storage_notice(err):
    if err is not None:
        msg = {"no_table": L("Supabase is connected, but the bots table is missing. Open SQL Editor in Supabase, run this code, then refresh.",
                             "Supabase متصل، لكن جدول البوتات غير موجود. افتح SQL Editor في Supabase وشغّل هذا الكود، ثم حدّث الصفحة."),
               "auth": L("Supabase refused the key. In Secrets, SUPABASE_KEY must be the secret key (Supabase → Settings → API Keys → secret).",
                         "Supabase رفض المفتاح. لازم يكون SUPABASE_KEY في Secrets هو المفتاح السري (Supabase ← Settings ← API Keys ← secret)."),
               "network": L("Couldn't reach Supabase right now. Check SUPABASE_URL in Secrets, or try again in a minute.",
                            "تعذر الاتصال بـ Supabase حالياً. تأكد من SUPABASE_URL في Secrets، أو حاول بعد دقيقة.")}.get(
            err.kind, L("Supabase returned an error.", "Supabase رجّع خطأ."))
        st.error(msg, icon=":material/database:")
        if err.kind == "no_table":
            st.code(PB.SETUP_SQL, language="sql")
        with st.expander(L("Technical details", "تفاصيل فنية")):
            st.code(err.detail[:600] or err.kind)
    elif PB.backend() == "local":
        st.warning(L("Trial mode: bots are kept in temporary storage and are lost when the site restarts. Connect Supabase (free) to keep them for good.",
                     "وضع التجربة: البوتات محفوظة مؤقتاً وتنحذف إذا أعاد الموقع التشغيل. اربط Supabase (مجاني) عشان تنحفظ بشكل دائم."),
                   icon=":material/info:")
        with st.expander(L("How to connect Supabase (5 minutes)", "طريقة ربط Supabase (5 دقائق)"), icon=":material/database:"):
            setup_steps()


# =====================================================================
# leaderboard + comparison
# =====================================================================
def status_badge(sim):
    if not sim["ok"]:
        return T.badge(L("Unavailable", "غير متاح"), "neu", "error")
    if sim["waiting"]:
        return T.badge(L("Starts next session", "يبدأ الجلسة القادمة"), "neu", "schedule")
    nb, ns = len(sim["next_buys"]), len(sim["next_sells"])
    if sim["bot"]["kind"] == "company":
        if nb:
            return T.badge(L("Buys at next open", "يشتري عند الافتتاح القادم"), "gold", "bolt")
        if ns:
            return T.badge(L("Sells at next open", "يبيع عند الافتتاح القادم"), "gold", "bolt")
    elif nb + ns == 1:
        return T.badge(L("1 order at next open", "أمر عند الافتتاح القادم"), "gold", "bolt")
    elif nb + ns:
        return T.badge(L(f"{nb + ns} orders at next open", f"{nb + ns} أوامر عند الافتتاح القادم"), "gold", "bolt")
    n = sim["n_open"]
    if n == 1:
        return T.badge(L("In a trade", "في صفقة"), "acc", "trending_up")
    if n > 1:
        return T.badge(L(f"{n} open trades", f"{n} صفقات مفتوحة"), "acc", "trending_up")
    return T.badge(L("Waiting for a signal", "ينتظر إشارة"), "neu", "hourglass_empty")


def head_html(b, logo=None):
    if b["kind"] == "company":
        return T.company(b["value"], "", logo, 32, sub=b["name"], href=ui.href(b["value"]))
    return (f'<div class="co">{T.ico(KIND_ICON[b["kind"]], "acc")}<div class="nm"><div class="tk">{T.esc(b["name"])}</div>'
            f'<div class="sub">{T.esc(universe_label(b))}</div></div></div>')


def bot_card(rank, sim, logo):
    b = sim["bot"]
    head = (f'<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">{head_html(b, logo)}'
            f'<span class="muted" style="font-weight:800">#{rank}</span></div>')
    badges = (f'<div style="margin-top:8px">{T.badge(strategies_label(list(b["strategies"]), short=True), "vio", "smart_toy")}'
              f'{status_badge(sim)}</div>')
    if sim["ok"] and not sim["waiting"]:
        ret, m = sim["ret"], sim["metrics"]
        spark = T.sparkline(sim["equity"].tail(120).values, T.UP if ret >= 0 else T.DOWN, 90, 32)
        spx = "" if sim["bench_ret"] is None else f'<div class="muted" style="font-size:.72rem;margin-top:4px;direction:ltr">S&amp;P 500 {sim["bench_ret"]:+.2f}%</div>'
        trades = L(f'{m["Trades"]} trades', f'{m["Trades"]} صفقة') + (f' · {L("win", "نجاح")} {m["Win Rate %"]:.0f}%' if m["Trades"] else "")
        watch = "" if b["kind"] == "company" else " · " + L(f'{sim["n_symbols"]} stocks', f'{sim["n_symbols"]} سهم')
        body = (f'<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:8px;margin-top:12px">'
                f'<div><div class="muted" style="font-size:.72rem">{L("Balance", "الرصيد")}</div>'
                f'<div style="font-weight:800;font-size:1.1rem;direction:ltr">{T.money(sim["final"])}</div></div>{spark}'
                f'<div style="text-align:end">{T.pbox(f"{ret:+.2f}%", ret)}{spx}</div></div>'
                f'<div class="muted" style="font-size:.74rem;margin-top:10px">{trades}{watch} · {L("since", "منذ")} {b["start_date"]}</div>')
    elif sim["ok"]:
        body = (f'<div class="muted" style="margin-top:12px;font-size:.8rem">{L("Starts with the first US session from", "يبدأ مع أول جلسة أمريكية من")} '
                f'{b["start_date"]} · {T.money(b["capital"])}</div>')
    else:
        why = L("No price data right now.", "لا توجد بيانات أسعار حالياً.") if sim["why"] == "data" else L("Strategy not found.", "الاستراتيجية غير موجودة.")
        body = f'<div class="muted" style="margin-top:12px;font-size:.8rem">{why}</div>'
    return f'<div class="card" style="margin:0;height:100%">{head}{badges}{body}</div>'


def ranked(sims):
    return sorted(sims, key=lambda s: (not (s["ok"] and not s["waiting"]), -(s.get("ret") or 0.0) if s["ok"] else 0.0))


def leaderboard(sims):
    ui.sec("leaderboard", "Leaderboard", "ترتيب البوتات")
    lg = data.logos([s["bot"]["value"] for s in sims if s["bot"]["kind"] == "company"])
    cards = "".join(bot_card(i, s, lg.get(s["bot"]["value"])) for i, s in enumerate(ranked(sims), 1))
    ui.html(f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;margin-bottom:16px">{cards}</div>')


def compare_chart(sims, spy):
    series, seen = {}, set()
    for s in sims:
        if s["ok"] and not s["waiting"] and len(s["equity"]) >= 2:
            name = s["bot"]["name"]
            if name in seen:
                name = f'{name} (#{s["bot"]["id"]})'
            seen.add(name)
            series[name] = (s["equity"] / s["bot"]["capital"] - 1) * 100
    if not series:
        return
    ui.sec("stacked_line_chart", "Return since start", "العائد منذ البداية")
    first = min(v.index[0] for v in series.values())
    spx_name = "S&P 500 (SPY)"
    if spy is not None and not spy.empty:
        sp = spy["Close"][spy.index >= first]
        if len(sp) >= 2:
            series[spx_name] = (sp / sp.iloc[0] - 1) * 100
    fig = charts.lines(series, None, suffix="%", height=380, dec=2)
    fig.update_traces(selector=dict(name=spx_name), line=dict(dash="dot", color=T.MUTED, width=1.6))
    ui.chart(fig, key="pb_cmp")
    st.caption(L("Each bot is measured from its own start date; the S&P 500 line starts with the oldest bot.",
                 "كل بوت يُقاس من تاريخ بدايته؛ وخط إس آند بي 500 يبدأ مع أقدم بوت."))


# =====================================================================
# one bot in detail
# =====================================================================
def details(sims):
    ui.sec("query_stats", "Bot details", "تفاصيل البوت")
    by_id = {s["bot"]["id"]: s for s in sims}
    ids = [s["bot"]["id"] for s in ranked(sims)]
    ui.valid("pb_sel", ids)
    sel = st.segmented_control(L("Bot", "البوت"), ids, default=ids[0], key="pb_sel", label_visibility="collapsed",
                               format_func=lambda i: f'{by_id[i]["bot"]["name"]}') or ids[0]
    sim = by_id[sel]
    b = sim["bot"]
    names = list(b["strategies"])
    group = b["kind"] != "company"
    uni = universe_label(b, sim.get("n_symbols") if sim["ok"] else None)
    badges = T.badge(uni, "gold", KIND_ICON[b["kind"]]) + T.badge(strategies_label(names), "vio", "smart_toy")
    if group:
        badges += T.badge(L(f"Up to {b['max_pos']} trades at once", f"حتى {b['max_pos']} صفقات في نفس الوقت"), "neu", "stacks")
    badges += (T.badge(_risk_txt(b), "neu", "shield") + T.badge(L("Start ", "البداية ") + b["start_date"], "neu", "event")
               + T.badge(L("Capital ", "رأس المال ") + T.money(b["capital"]), "neu", "account_balance_wallet")
               + T.badge(L("Fee {:g}% / side", "العمولة {:g}% لكل جهة").format(b["fee"]), "neu", "receipt"))
    ui.html(f'<div class="card">{badges}</div>')
    with st.expander(L("Strategy settings", "إعدادات الاستراتيجيات"), icon=":material/tune:"):
        rows = "".join(f'<div style="margin:4px 0">{T.badge(strat_name(n), "vio", "smart_toy")} '
                       f'<span class="muted">{T.esc(_params_txt(n, p))}</span></div>' for n, p in b["strategies"].items())
        ui.html(rows or "—")
        if len(names) > 1:
            st.caption(L("Any of these strategies can open a trade. A trade closes on the exit signal of the strategy that opened it, "
                         "or by the stop loss, take profit or trailing stop.",
                         "أي استراتيجية منها تقدر تفتح صفقة، والصفقة تتقفل بإشارة الخروج من نفس الاستراتيجية اللي فتحتها، "
                         "أو بوقف الخسارة أو جني الأرباح أو الوقف المتحرك."))

    if not sim["ok"]:
        if sim["why"] == "strategy":
            st.warning(L("This bot's strategy or group no longer exists on the site. Delete it and add a new one.",
                         "استراتيجية هذا البوت أو مجموعته لم تعد موجودة في الموقع. احذفه وأضف بوت جديد."), icon=":material/error:")
        else:
            st.warning(L(f"No price data for {uni} right now. Check the symbol, or try again in a minute.",
                         f"لا توجد بيانات أسعار لـ {uni} حالياً. تأكد من الرمز، أو حاول بعد دقيقة."), icon=":material/error:")
        return
    if sim["waiting"]:
        st.info(L(f"The bot starts with the first US session on or after {b['start_date']}. After that session closes it checks its "
                  "strategies, and any order is filled at the next open.",
                  f"البوت يبدأ مع أول جلسة أمريكية من تاريخ {b['start_date']}. بعد إغلاق الجلسة يفحص الاستراتيجيات، وأي أمر يتنفذ عند الافتتاح التالي."),
                icon=":material/schedule:")
        return

    m, tr, cap = sim["metrics"], sim["trades"], b["capital"]
    last = pd.Timestamp(sim["last_date"])
    op = tr[tr["Exit Reason"] == "Open"]
    if not group:
        if len(op):
            o = op.iloc[0]
            st.success(L(f"In a trade since {pd.Timestamp(o['Entry Date']):%b %d, %Y} at ${o['Entry']:,.2f} · open P&L {o['P&L %']:+.2f}%",
                         f"في صفقة شراء منذ {pd.Timestamp(o['Entry Date']):%Y-%m-%d} بسعر ${o['Entry']:,.2f} · الربح الحالي {o['P&L %']:+.2f}%"),
                       icon=":material/trending_up:")
        else:
            st.info(L("Out of the market, waiting for a buy signal.", "خارج السوق، ينتظر إشارة شراء."), icon=":material/pause_circle:")
    elif len(op):
        st.success(L(f"{len(op)} open trades: ", f"{len(op)} صفقات مفتوحة: ") + ", ".join(op["Symbol"]), icon=":material/trending_up:")
    else:
        st.info(L("No open trades, waiting for signals.", "لا توجد صفقات مفتوحة، ينتظر إشارات."), icon=":material/pause_circle:")
    if sim["next_buys"] or sim["next_sells"]:
        parts = []
        if sim["next_buys"]:
            parts.append(L("buy ", "شراء ") + ", ".join(f"{s} ({strat_short(k)})" for s, k in sim["next_buys"]))
        if sim["next_sells"]:
            parts.append(L("sell ", "بيع ") + ", ".join(f"{s} ({strat_short(k)})" for s, k in sim["next_sells"]))
        note = L(" The latest candle is still moving, so these signals are confirmed at today's close.",
                 " الشمعة الأخيرة لسا تتحرك، فالإشارات تتأكد عند إغلاق اليوم.") if _session_live() and last.date() == PB.today_ny() else ""
        st.warning(L(f"Orders for the next open (signals of {last:%Y-%m-%d}): ", f"أوامر الافتتاح القادم (إشارات {last:%Y-%m-%d}): ")
                   + " · ".join(parts) + "." + note, icon=":material/bolt:")

    closed = tr[tr["Exit Reason"] != "Open"]
    wins = int((closed["P&L $"] > 0).sum())
    bh_label = L("Buy & hold ", "شراء واحتفاظ ") if not group else L("Group bought equally ", "المجموعة بالتساوي ")
    kp = [("account_balance_wallet", L("Balance", "الرصيد"), T.money(sim["final"]), L("start ", "البداية ") + T.money(cap), T.cls(sim["ret"])),
          ("trending_up", L("Return", "العائد"), f"{sim['ret']:+.2f}%", bh_label + f"{sim['group_ret']:+.2f}%", T.cls(sim["ret"])),
          ("show_chart", L("vs S&P 500", "مقابل إس آند بي"),
           "—" if sim["bench_ret"] is None else f"{sim['ret'] - sim['bench_ret']:+.2f}%",
           "" if sim["bench_ret"] is None else f"S&P {sim['bench_ret']:+.2f}%",
           None if sim["bench_ret"] is None else T.cls(sim["ret"] - sim["bench_ret"])),
          ("south_east", L("Max drawdown", "أقصى تراجع"), f"{m['Max Drawdown %']:.2f}%", "", "neg" if m["Max Drawdown %"] < -0.05 else None),
          ("target", L("Win rate", "نسبة النجاح"), f"{m['Win Rate %']:.0f}%" if len(closed) else "—",
           L(f"{wins} of {len(closed)} closed trades", f"{wins} من {len(closed)} صفقة مغلقة"),
           ("pos" if m["Win Rate %"] >= 50 else "neg") if len(closed) else None),
          ("calendar_month", L("Running", "مدة التشغيل"), L(f"{sim['sessions']} sessions", f"{sim['sessions']} جلسة"),
           L("since ", "منذ ") + b["start_date"], None)]
    for col, (ic, lab, val, sub, kind) in zip(st.columns(6), kp):
        col.markdown(T.kpi(ic, lab, val, sub, kind), unsafe_allow_html=True)

    bench = sim["bench"] if sim["bench"] is not None else sim["group"]
    bench_name = "S&P 500 (SPY)" if sim["bench"] is not None else L("Buy & Hold", "شراء واحتفاظ")
    ui.chart(charts.equity_chart(sim["equity"], bench, (L("Bot", "البوت"), bench_name, L("Drawdown %", "التراجع %"))), key=f"pb_eq_{b['id']}")

    jr = PB.journal(sim)
    j_closed, j_open = jr[jr["Exit Reason"] != "Open"], jr[jr["Exit Reason"] == "Open"]
    s = autotrader.stats({"trades": j_closed, "open": j_open, "equity": sim["equity"], "bench": bench, "positions": sim["npos"],
                          "capital": cap})
    tdash.render(j_closed, j_open, s, cap, key=f"pb_td_{b['id']}")

    if len(closed) and (group or len(names) > 1):
        ui.sec("pie_chart", "What worked", "ماذا نجح")
        c1, c2 = st.columns(2)
        if len(names) > 1:
            g = closed.groupby("Strategy")["P&L $"].sum().sort_values()
            ui.chart(charts.hbar([strat_short(k) for k in g.index], [float(v) for v in g.values], L("P&L by strategy ($)", "الربح حسب الاستراتيجية ($)"),
                                 max(260, 34 * len(g) + 80), suffix=""), key=f"pb_bys_{b['id']}", container=c1)
        if group:
            g = closed.groupby("Symbol")["P&L $"].sum()
            g = pd.concat([g.nlargest(6), g.nsmallest(6)]).groupby(level=0).first().sort_values()
            ui.chart(charts.hbar(list(g.index), [float(v) for v in g.values], L("P&L by stock, best and worst ($)", "الربح حسب السهم، الأفضل والأسوأ ($)"),
                                 max(260, 30 * len(g) + 80), suffix=""), key=f"pb_bysym_{b['id']}", container=c2 if len(names) > 1 else c1)

    # price chart with the bot's trades on one stock (from a little before the start)
    ui.sec("candlestick_chart", "Trades on the chart", "الصفقات على الشارت")
    if group:
        traded = list(dict.fromkeys(tr.sort_values("Entry Date", ascending=False)["Symbol"]))
        if not traded:
            st.caption(L("No trades yet. The chart appears after the first trade.", "لا توجد صفقات بعد. الشارت يظهر بعد أول صفقة."))
            full = None
        else:
            ui.valid(f"pb_chart_{b['id']}", traded)
            sym = st.selectbox(L("Stock", "السهم"), traded, key=f"pb_chart_{b['id']}")
            full = data.history(sym, PB.period_for(b["start_date"]))
    else:
        sym, full = b["value"], sim.get("frame")
    if full is not None and not full.empty:
        full = ta.add_all(full)
        start_i = int(full.index.searchsorted(pd.Timestamp(sim["equity"].index[0])))
        view = full.iloc[max(0, start_i - 30):]
        one = names[0] if len(names) == 1 else None
        fig = charts.price_chart(view, "Candles" if len(view) <= 800 else "Line", OVERLAYS.get(one, []), PANELS.get(one, []),
                                 False, trades=tr[tr["Symbol"] == sym])
        try:
            fig.add_vline(x=pd.Timestamp(sim["equity"].index[0]).strftime("%Y-%m-%d"), line=dict(color=T.GOLD, width=1.2, dash="dot"))
        except Exception:
            pass
        ui.chart(fig, key=f"pb_px_{b['id']}")

    ui.sec("table_rows", "All trades", "كل الصفقات")
    if tr.empty:
        st.info(L("No trades yet. The bot trades only when a strategy gives a signal.",
                  "لا توجد صفقات بعد. البوت يتداول فقط لما تعطي استراتيجية إشارة."))
        return
    show = tr.copy()
    show.insert(0, "#", range(1, len(show) + 1))
    show["Strategy"] = show["Strategy"].map(strat_short)
    show["Entry Date"] = pd.to_datetime(show["Entry Date"]).dt.date
    show["Exit Date"] = pd.to_datetime(show["Exit Date"]).dt.date
    show["Exit Reason"] = show["Exit Reason"].map(lambda x: L(x, engine.EXIT_REASON_AR.get(x, x)))
    N = {"Symbol": L("Symbol", "الرمز"), "Strategy": L("Strategy", "الاستراتيجية"), "Entry Date": L("Entry date", "تاريخ الدخول"),
         "Entry": L("Entry", "سعر الدخول"), "Exit Date": L("Exit date", "تاريخ الخروج"), "Exit": L("Exit / now", "سعر الخروج / الحالي"),
         "Shares": L("Shares", "الأسهم"), "P&L $": L("P&L $", "الربح $"), "P&L %": L("P&L %", "الربح %"), "Bars": L("Days", "الأيام"),
         "Exit Reason": L("Exit reason", "سبب الخروج")}
    show = show.rename(columns=N)
    st.dataframe(show.iloc[::-1].style.map(T.color_style, subset=[N["P&L %"], N["P&L $"]]).format(
        {N["Entry"]: "{:,.2f}", N["Exit"]: "{:,.2f}", N["Shares"]: "{:,.2f}", N["P&L $"]: "{:+,.2f}", N["P&L %"]: "{:+.2f}%"}),
        hide_index=True, height=min(420, 38 + 35 * len(show)))
    st.download_button(L("Export CSV", "تصدير CSV"), show.to_csv(index=False).encode("utf-8-sig"), f"paper_bot_{b['id']}.csv",
                       "text/csv", icon=":material/download:", key=f"pb_csv_{b['id']}")


# =====================================================================
# manage: unlock · add · delete
# =====================================================================
def _unlock():
    if ss.get("pb_admin"):                 # typing Enter and pressing the button both call this
        return
    if PB.check_password(ss.get("pb_pw")):
        ss.pb_admin = True
        ss.pb_pw = ""
    else:
        ss.pb_bad_pw = True


def can_edit():
    mode = PB.admin_mode()
    if mode == "open" or (mode == "password" and ss.get("pb_admin")):
        return True
    if mode == "locked":
        st.info(L("To add or delete bots, add BOTS_PASSWORD to your Streamlit Secrets (Settings → Secrets). Visitors can only watch the bots.",
                  "لإضافة أو حذف البوتات، أضف BOTS_PASSWORD في Secrets حق Streamlit (Settings ← Secrets). الزوار يقدرون يشاهدون البوتات فقط."),
                icon=":material/lock:")
        st.code('BOTS_PASSWORD = "' + L("choose-a-password", "اختر-كلمة-مرور") + '"', language="toml")
        return False
    st.caption(L("Visitors can watch the bots. Enter your password to add or delete bots.",
                 "الزوار يقدرون يشاهدون البوتات. اكتب كلمة المرور لإضافة أو حذف البوتات."))
    a, b = st.columns([3, 1], vertical_alignment="bottom")
    a.text_input(L("Password", "كلمة المرور"), type="password", key="pb_pw", on_change=_unlock)
    b.button(L("Unlock", "دخول"), icon=":material/lock_open:", on_click=_unlock, width="stretch", key="pb_unlock")
    if ss.pop("pb_bad_pw", False):
        st.error(L("Wrong password.", "كلمة المرور غير صحيحة."))
    return False


def _pkey(name, k):
    return f"pb_p|{name}|{k}"


def _init_form():
    for k, v in DEFAULTS.items():
        if k not in ss:
            ss[k] = list(v) if isinstance(v, list) else v
    if ss.pop("pb_reset_name", False):
        ss["pb_name"] = ""
    if ss.get("pb_kind") not in PB.KINDS:          # clicking the selected option again clears it
        ss["pb_kind"] = "company"
    if not isinstance(ss.get("pb_strats"), list):
        ss["pb_strats"] = []
    today = PB.today_ny()
    if "pb_start" not in ss or ss["pb_start"] > today or ss["pb_start"] < today - timedelta(days=5 * 365):
        ss["pb_start"] = today


def _all_strats():
    ss["pb_strats"] = list(engine.STRATEGIES)


def _default_name(kind, value, strats):
    n = len(strats)
    how = strat_short(strats[0]) if n == 1 else (L("all strategies", "كل الاستراتيجيات") if n == len(engine.STRATEGIES)
                                                  else L(f"{n} strategies", f"{n} استراتيجيات"))
    what = {"company": value, "sector": sector_name(value), "industry": gics_name(value), "all": L("All companies", "كل الشركات")}[kind]
    return f"{what} · {how}"[:40]


def add_form(bots):
    ui.sec("add_circle", "Add a bot", "أضف بوت")
    if len(bots) >= PB.MAX_BOTS:
        st.info(L(f"You have {PB.MAX_BOTS} bots, the maximum. Delete one to add another.",
                  f"عندك {PB.MAX_BOTS} بوتات، وهذا الحد الأعلى. احذف واحد عشان تضيف غيره."), icon=":material/block:")
        return
    _init_form()
    with st.container(border=True):
        a, c = st.columns([2, 1])
        a.text_input(L("Bot name (optional)", "اسم البوت (اختياري)"), key="pb_name", max_chars=40,
                     placeholder=L("e.g. Tech momentum", "مثال: بوت التقنية"))
        c.number_input(L("Virtual capital ($)", "رأس المال الوهمي ($)"), 100, 100_000_000, step=1000, key="pb_capital")

        # 1) what it trades
        ui.valid("pb_kind", PB.KINDS)
        kind = st.segmented_control(L("What does the bot trade?", "وش يتداول البوت؟"), list(PB.KINDS), key="pb_kind",
                                    format_func=lambda k: L(*KIND_LABEL[k])) or "company"
        sectors = PB.sector_members()
        if kind == "company":
            st.text_input(L("Symbol", "الرمز"), key="pb_symbol", max_chars=15,
                          help=L("Any Yahoo Finance symbol: AAPL, SPY, BTC-USD, 2222.SR…", "أي رمز من ياهو فاينانس: AAPL، SPY، BTC-USD، 2222.SR…"))
            count = 1
        elif kind == "sector":
            ui.valid("pb_sector", sectors)
            sec = st.selectbox(L("Sector", "القطاع"), list(sectors), key="pb_sector",
                               format_func=lambda s: f"{sector_name(s)} · {len(sectors[s])} " + L("stocks", "سهم"))
            count = len(sectors.get(sec, []))
        elif kind == "industry":
            x, y = st.columns(2)
            ui.valid("pb_ind_sector", sectors)
            isec = x.selectbox(L("Sector", "القطاع"), list(sectors), key="pb_ind_sector", format_func=sector_name)
            inds = PB.industry_members(isec)
            ui.valid("pb_industry", inds)
            ind = y.selectbox(L("Industry", "الصناعة"), list(inds), key="pb_industry",
                              format_func=lambda i: f"{gics_name(i)} · {len(inds[i])} " + L("stocks", "سهم"))
            count = len(inds.get(ind, []))
        else:
            count = len(PB.all_members())
            st.caption(L(f"{count} US companies: the S&P 500 plus the site's largest names. The first load takes longer (up to a minute) "
                         "because the history of every stock is downloaded.",
                         f"{count} شركة أمريكية: إس آند بي 500 وأكبر الشركات في الموقع. أول تحميل ياخذ وقت أطول (لين دقيقة) "
                         "لأنه يحمّل تاريخ كل الأسهم."))
        if kind != "company":
            m1, m2 = st.columns([1, 2], vertical_alignment="bottom")
            maxpos = m1.number_input(L("Max open trades", "أقصى عدد صفقات مفتوحة"), 1, PB.MAX_POS_LIMIT, step=1, key="pb_maxpos")
            m2.caption(L(f"Each trade gets an equal share (1/{maxpos} of the balance). After every close the bot checks all {count} stocks; "
                         "when more stocks signal than free slots, it buys the strongest of the last 3 months first.",
                         f"كل صفقة تاخذ حصة متساوية (1/{maxpos} من الرصيد). بعد كل إغلاق يفحص البوت كل الـ {count} سهم، "
                         "وإذا أعطت أسهم إشارات أكثر من الأماكن الفاضية، يشتري الأقوى أداءً آخر 3 أشهر أولاً."))

        # 2) how it trades
        names = list(engine.STRATEGIES)
        ui.valid_multi("pb_strats", names)
        strats = st.pills(L("Strategies: one, several or all", "الاستراتيجيات: وحدة أو أكثر أو الكل"), names, selection_mode="multi",
                          key="pb_strats", format_func=strat_name) or []
        st.button(L("Select all strategies", "اختر كل الاستراتيجيات"), icon=":material/done_all:", on_click=_all_strats, key="pb_allstrats")
        strats = [s for s in names if s in strats]
        if len(strats) > 1:
            st.caption(L("Any selected strategy can open a trade; the trade closes on the exit signal of the strategy that opened it, "
                         "or by the stop loss, take profit or trailing stop.",
                         "أي استراتيجية مختارة تقدر تفتح صفقة، والصفقة تتقفل بإشارة الخروج من نفس الاستراتيجية اللي فتحتها، "
                         "أو بوقف الخسارة أو جني الأرباح أو الوقف المتحرك."))
        params = {}
        with st.expander(L("Strategy settings (optional, defaults are the Strategy Lab's)", "إعدادات الاستراتيجيات (اختياري، الافتراضي نفس المختبر)"),
                         icon=":material/tune:"):
            if not strats:
                st.caption(L("Pick a strategy first.", "اختر استراتيجية أولاً."))
            for s in strats:
                spec = engine.STRATEGIES[s][1]
                st.markdown(f"**{strat_name(s)}**")
                cols = st.columns(len(spec))
                params[s] = {}
                for col, (k, label, lo, hi, dflt, step) in zip(cols, spec):
                    key = _pkey(s, k)
                    isf = isinstance(step, float)
                    if key not in ss:
                        ss[key] = float(dflt) if isf else int(dflt)
                    lab = L(label, engine.PARAM_AR.get(label, label))
                    if isf:
                        params[s][k] = col.number_input(lab, float(lo), float(hi), step=float(step), key=key)
                    else:
                        params[s][k] = col.number_input(lab, int(lo), int(hi), step=int(step), key=key)

        # 3) risk, fees and start
        r = st.columns(5)
        off = L("0 = off", "0 = إيقاف")
        r[0].number_input(L("Fee % / side", "العمولة %"), 0.0, 1.0, step=0.01, key="pb_fee")
        r[1].number_input(L("Stop loss %", "وقف الخسارة %"), 0.0, 50.0, step=0.5, help=off, key="pb_stop")
        r[2].number_input(L("ATR stop ×", "وقف ATR ×"), 0.0, 10.0, step=0.5, help=off, key="pb_atr")
        r[3].number_input(L("Take profit %", "جني الأرباح %"), 0.0, 500.0, step=1.0, help=off, key="pb_tp")
        r[4].number_input(L("Trailing stop %", "الوقف المتحرك %"), 0.0, 50.0, step=0.5, help=off, key="pb_trail")
        today = PB.today_ny()
        d1, d2 = st.columns([1, 2], vertical_alignment="bottom")
        start = d1.date_input(L("Start date", "تاريخ البداية"), min_value=today - timedelta(days=5 * 365), max_value=today, key="pb_start")
        d2.caption(L("Today = the bot trades live from now on. An earlier date replays the past first, like the Strategy Lab, then carries on live.",
                     "اليوم = البوت يتداول مباشرة من الحين وللأمام. التاريخ الأقدم يعيد تشغيل الفترة الماضية أولاً مثل مختبر الاستراتيجيات، ثم يكمل مباشرة."))

        if st.button(L("Start the bot", "شغّل البوت"), type="primary", icon=":material/play_arrow:", key="pb_create"):
            if not strats:
                st.error(L("Pick at least one strategy.", "اختر استراتيجية وحدة على الأقل."))
                return
            for s in strats:
                p = params.get(s, {})
                if "fast" in p and "slow" in p and p["fast"] >= p["slow"]:
                    st.error(L(f"{strat_name(s)}: the fast period must be smaller than the slow period.",
                               f"{strat_name(s)}: الفترة السريعة لازم تكون أصغر من البطيئة."))
                    return
            value = {"company": str(ss.get("pb_symbol") or "").strip().upper(), "sector": ss.get("pb_sector"),
                     "industry": ss.get("pb_industry"), "all": "all"}[kind]
            if not value:
                st.error(L("Type a symbol.", "اكتب رمز السهم."))
                return
            if kind == "company":
                with st.spinner(L(f"Checking {value}...", f"جاري التحقق من {value}...")):
                    df = data.history(value, "2y")
                if df.empty or len(df) < 60:
                    st.error(L(f"No price data for {value}. Check the symbol (for example AAPL, BTC-USD, 2222.SR).",
                               f"لا توجد بيانات للرمز {value}. تأكد من الرمز (مثلاً AAPL أو BTC-USD أو 2222.SR)."))
                    return
            name = str(ss.get("pb_name") or "").strip() or _default_name(kind, value, strats)
            rec = PB.make_record(name, kind, value, params, ss.get("pb_maxpos", 5), ss["pb_capital"], ss["pb_fee"], ss["pb_stop"], ss["pb_atr"],
                                 ss["pb_tp"], ss["pb_trail"], pd.Timestamp(start).strftime("%Y-%m-%d"))
            try:
                PB.create_bot(rec)
            except PB.StoreError as e:
                if e.kind == "full":
                    st.error(L(f"You already have {PB.MAX_BOTS} bots.", f"عندك {PB.MAX_BOTS} بوتات بالفعل."))
                else:
                    storage_notice(e)
                return
            ss["pb_reset_name"] = True
            st.toast(L(f"Bot started: {name}", f"تم تشغيل البوت: {name}"), icon=":material/rocket_launch:")
            st.rerun()


def _ask_delete(bot_id):
    ss["pb_confirm"] = bot_id


def _cancel_delete():
    ss.pop("pb_confirm", None)


def delete_list(bots):
    if not bots:
        return
    ui.sec("delete", "Delete a bot", "حذف بوت")
    for b in bots:
        with st.container(border=True):
            a, c = st.columns([4, 1], vertical_alignment="center")
            a.markdown(f'<b>{T.esc(b["name"])}</b> <span class="muted">· {T.esc(universe_label(b))} · '
                       f'{T.esc(strategies_label(list(b["strategies"]), short=True))} · {L("since", "منذ")} {T.esc(b["start_date"])}</span>',
                       unsafe_allow_html=True)
            with c.container(key=f"pbred_del_{b['id']}"):
                st.button(L("Delete", "حذف"), icon=":material/delete:", key=f"pb_del_{b['id']}", on_click=_ask_delete, args=(b["id"],),
                          width="stretch")
            if ss.get("pb_confirm") != b["id"]:
                continue
            st.markdown(L(f"Delete **{b['name']}** and its whole record? This can't be undone.",
                          f"حذف **{b['name']}** وكل سجله؟ ما تقدر ترجعه بعدين."))
            y, n, _ = st.columns([1, 1, 3])
            with n.container(key=f"pbred_no_{b['id']}"):
                st.button(L("No", "لا"), icon=":material/close:", key=f"pb_no_{b['id']}", on_click=_cancel_delete, width="stretch")
            if y.button(L("Yes, delete", "نعم، احذف"), type="primary", key=f"pb_yes_{b['id']}", icon=":material/delete_forever:",
                        width="stretch"):
                try:
                    PB.delete_bot(b["id"])
                except PB.StoreError as e:
                    storage_notice(e)
                    return
                ss.pop("pb_confirm", None)
                st.toast(L("Bot deleted.", "تم حذف البوت."), icon=":material/delete:")
                st.rerun()


def manage(bots, err):
    with st.expander(L(f"Manage bots ({len(bots)} of {PB.MAX_BOTS})", f"إدارة البوتات ({len(bots)} من {PB.MAX_BOTS})"),
                     icon=":material/settings:", expanded=not bots):
        if err is not None:
            st.caption(L("Fix the storage message above first.", "صلّح رسالة التخزين اللي فوق أولاً."))
            return
        if not can_edit():
            return
        add_form(bots)
        delete_list(bots)
        if PB.admin_mode() == "password":
            if st.button(L("Lock", "قفل"), icon=":material/lock:", key="pb_lock"):
                ss.pb_admin = False
                st.rerun()


# =====================================================================
# page
# =====================================================================
def page_paper_bots():
    ui.header("robot_2", "Paper Bots", "البوتات الافتراضية",
              f"Up to {PB.MAX_BOTS} bots trade with virtual money on real prices, forward from the day they start. Each one trades a company, "
              "a sector, an industry or all companies, with one or more Strategy Lab strategies: signal on the daily close, order at the next open.",
              f"حتى {PB.MAX_BOTS} بوتات تتداول بأموال وهمية على أسعار حقيقية، من يوم تشغيلها وللأمام. كل بوت يتداول شركة أو قطاع أو صناعة أو كل الشركات، "
              "باستراتيجية وحدة أو أكثر من مختبر الاستراتيجيات: الإشارة على الإغلاق اليومي، والتنفيذ عند افتتاح اليوم التالي.")
    ui.html(RED_CSS)
    try:
        bots, err = PB.list_bots(), None
    except PB.StoreError as e:
        bots, err = [], e
    storage_notice(err)

    if bots:
        big = any(b["kind"] != "company" for b in bots)
        with st.spinner(L("Updating the bots with the latest prices" + (" (groups of stocks can take up to a minute)..." if big else "..."),
                          "جاري تحديث البوتات بآخر الأسعار" + (" (مجموعات الأسهم قد تاخذ لين دقيقة)..." if big else "..."))):
            sims, spy = PB.run_all(bots)
        ui.safe(leaderboard, sims)
        ui.safe(compare_chart, sims, spy)
        ui.safe(details, sims)
    elif err is None:
        msg = L("No bots yet. Open <b>Manage bots</b> below, choose what the bot trades (a company, a sector, an industry or all companies) "
                "and its strategies, then press <b>Start the bot</b>. From then on it checks its strategies after every US close and trades "
                "with virtual money at the next open.",
                "ما فيه بوتات للحين. افتح <b>إدارة البوتات</b> تحت، واختر وش يتداول البوت (شركة أو قطاع أو صناعة أو كل الشركات) "
                "واستراتيجياته، واضغط <b>شغّل البوت</b>. بعدها يفحص استراتيجياته بعد كل إغلاق للسوق الأمريكي، ويتداول بأموال وهمية عند الافتتاح التالي.")
        ui.html(f'<div class="card" style="line-height:1.9">{T.ico("smart_toy", "acc")} {msg}</div>')

    manage(bots, err)
    st.caption(L("Virtual trading on real daily prices (dividend-adjusted, may be delayed). Results are recalculated from each bot's start date "
                 "whenever the page opens. No real money and no broker are involved. Past results do not guarantee future returns.",
                 "تداول وهمي على أسعار يومية حقيقية (معدّلة بالتوزيعات وقد تكون متأخرة). النتائج تُحسب من جديد من تاريخ بداية كل بوت كل ما تفتح الصفحة. "
                 "لا توجد أموال حقيقية ولا وسيط. النتائج السابقة لا تضمن المستقبل."))
    ui.foot()

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.2"
