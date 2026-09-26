"""
p_paper.py - Paper Bots: up to 5 bots that trade with virtual money on real prices, forward from the day they start.
Leaderboard · comparison chart · details of one bot (chart, equity, trading dashboard, trades) · manage (add / delete).
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
from i18n import L

ss = st.session_state
NEW_BOT = {"name": "", "symbol": "AAPL", "strategy": "SMA Crossover", "params": {}, "capital": 10000, "fee": 0.05,
           "stop": 7.0, "atr": 0.0, "tp": 0.0, "trail": 0.0}
OVERLAYS = {"SMA Crossover": ["SMA 20", "SMA 50"], "Golden Cross (50/200)": ["SMA 50", "SMA 200"],
            "EMA Crossover": ["EMA 9", "EMA 21"], "Bollinger Breakout": ["Bollinger Bands"]}
PANELS = {"RSI Mean Reversion": ["RSI"], "MACD Crossover": ["MACD"]}


def strat_name(k):
    return L(k, engine.STRATEGY_AR.get(k, k))


def _params_txt(bot):
    spec = engine.STRATEGIES.get(bot["strategy"], (None, []))[1]
    labels = {k: L(lab, engine.PARAM_AR.get(lab, lab)) for k, lab, *_ in spec}
    return " · ".join(f"{labels.get(k, k)} {v:g}" for k, v in bot["params"].items())


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
        "<b>3.</b> Open <b>Project Settings</b> and copy the <b>Project URL</b>, then open <b>API Keys</b> and copy the <b>secret</b> key "
        "(it starts with <code>sb_secret_</code>). Never use it in a public place; it only goes into Streamlit Secrets.<br>"
        "<b>4.</b> In Streamlit open your app's <b>Settings → Secrets</b> and add the three lines below under your FRED key, then press <b>Save</b>.",
        "<b>1.</b> سجّل حساب مجاني في <b>supabase.com</b> واضغط <b>New project</b> (أي اسم وكلمة مرور، واختر أقرب منطقة).<br>"
        "<b>2.</b> داخل المشروع افتح <b>SQL Editor</b>، والصق الكود اللي تحت واضغط <b>Run</b>. هذا ينشئ جدول البوتات.<br>"
        "<b>3.</b> افتح <b>Project Settings</b> وانسخ <b>Project URL</b>، ثم افتح <b>API Keys</b> وانسخ المفتاح <b>secret</b> "
        "(يبدأ بـ <code>sb_secret_</code>). لا تحطه في أي مكان عام، مكانه الوحيد Secrets في Streamlit.<br>"
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
    if sim["next"] == "buy":
        return T.badge(L("Buys at next open", "يشتري عند الافتتاح القادم"), "gold", "bolt")
    if sim["next"] == "sell":
        return T.badge(L("Sells at next open", "يبيع عند الافتتاح القادم"), "gold", "bolt")
    if sim["in_pos"]:
        return T.badge(L("In a trade", "في صفقة"), "acc", "trending_up")
    return T.badge(L("Waiting for a signal", "ينتظر إشارة"), "neu", "hourglass_empty")


def bot_card(rank, sim, logo):
    b = sim["bot"]
    head = (f'<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">'
            f'{T.company(b["symbol"], "", logo, 32, sub=b["name"], href=ui.href(b["symbol"]))}'
            f'<span class="muted" style="font-weight:800">#{rank}</span></div>')
    badges = f'<div style="margin-top:8px">{T.badge(strat_name(b["strategy"]), "vio", "smart_toy")}{status_badge(sim)}</div>'
    if sim["ok"] and not sim["waiting"]:
        ret, m = sim["ret"], sim["metrics"]
        spark = T.sparkline(sim["equity"].tail(120).values, T.UP if ret >= 0 else T.DOWN, 90, 32)
        spx = "" if sim["bench_ret"] is None else f'<div class="muted" style="font-size:.72rem;margin-top:4px;direction:ltr">S&amp;P 500 {sim["bench_ret"]:+.2f}%</div>'
        trades = L(f'{m["Trades"]} trades', f'{m["Trades"]} صفقة') + (f' · {L("win", "نجاح")} {m["Win Rate %"]:.0f}%' if m["Trades"] else "")
        body = (f'<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:8px;margin-top:12px">'
                f'<div><div class="muted" style="font-size:.72rem">{L("Balance", "الرصيد")}</div>'
                f'<div style="font-weight:800;font-size:1.1rem;direction:ltr">{T.money(sim["final"])}</div></div>{spark}'
                f'<div style="text-align:end">{T.pbox(f"{ret:+.2f}%", ret)}{spx}</div></div>'
                f'<div class="muted" style="font-size:.74rem;margin-top:10px">{trades} · {L("since", "منذ")} {b["start_date"]}</div>')
    elif sim["ok"]:
        body = (f'<div class="muted" style="margin-top:12px;font-size:.8rem">{L("Starts with the first US session from", "يبدأ مع أول جلسة أمريكية من")} '
                f'{b["start_date"]} · {T.money(b["capital"])}</div>')
    else:
        body = f'<div class="muted" style="margin-top:12px;font-size:.8rem">{L("No price data right now.", "لا توجد بيانات أسعار حالياً.") if sim["why"] == "data" else L("Strategy not found.", "الاستراتيجية غير موجودة.")}</div>'
    return f'<div class="card" style="margin:0;height:100%">{head}{badges}{body}</div>'


def ranked(sims):
    return sorted(sims, key=lambda s: (not (s["ok"] and not s["waiting"]), -(s.get("ret") or 0.0) if s["ok"] else 0.0))


def leaderboard(sims):
    ui.sec("leaderboard", "Leaderboard", "ترتيب البوتات")
    lg = data.logos([s["bot"]["symbol"] for s in sims])
    cards = "".join(bot_card(i, s, lg.get(s["bot"]["symbol"])) for i, s in enumerate(ranked(sims), 1))
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
    start_txt = L("Start ", "البداية ") + b["start_date"]
    cap_txt = L("Capital ", "رأس المال ") + T.money(b["capital"])
    fee_txt = L("Fee {:g}% / side", "العمولة {:g}% لكل جهة").format(b["fee"])
    ui.html('<div class="card">' + T.badge(b["symbol"], "gold", "sell") + T.badge(strat_name(b["strategy"]), "vio", "smart_toy")
            + T.badge(_params_txt(b) or "—", "neu", "tune") + T.badge(_risk_txt(b), "neu", "shield") + T.badge(start_txt, "neu", "event")
            + T.badge(cap_txt, "neu", "account_balance_wallet") + T.badge(fee_txt, "neu", "receipt") + "</div>")

    if not sim["ok"]:
        if sim["why"] == "strategy":
            st.warning(L("This bot uses a strategy that no longer exists on the site. Delete it and add a new one.",
                         "هذا البوت يستخدم استراتيجية لم تعد موجودة في الموقع. احذفه وأضف بوت جديد."), icon=":material/error:")
        else:
            st.warning(L(f"No price data for {b['symbol']} right now. Check the symbol, or try again in a minute.",
                         f"لا توجد بيانات أسعار للرمز {b['symbol']} حالياً. تأكد من الرمز، أو حاول بعد دقيقة."), icon=":material/error:")
        return
    if sim["waiting"]:
        st.info(L(f"The bot starts with the first US session on or after {b['start_date']}. After that session closes it checks its "
                  "strategy, and any order is filled at the next open.",
                  f"البوت يبدأ مع أول جلسة أمريكية من تاريخ {b['start_date']}. بعد إغلاق الجلسة يفحص الاستراتيجية، وأي أمر يتنفذ عند الافتتاح التالي."),
                icon=":material/schedule:")
        return

    m, tr, cap = sim["metrics"], sim["trades"], b["capital"]
    last = pd.Timestamp(sim["last_date"])
    if sim["in_pos"] and sim["open"] is not None:
        o = sim["open"]
        st.success(L(f"In a trade since {pd.Timestamp(o['Entry Date']):%b %d, %Y} at ${o['Entry']:,.2f} · open P&L {o['P&L %']:+.2f}%",
                     f"في صفقة شراء منذ {pd.Timestamp(o['Entry Date']):%Y-%m-%d} بسعر ${o['Entry']:,.2f} · الربح الحالي {o['P&L %']:+.2f}%"),
                   icon=":material/trending_up:")
    else:
        st.info(L("Out of the market, waiting for a buy signal.", "خارج السوق، ينتظر إشارة شراء."), icon=":material/pause_circle:")
    if sim["next"]:
        live = _session_live() and last.date() == PB.today_ny()
        what = L("buy", "شراء") if sim["next"] == "buy" else L("sell", "بيع")
        note = L(" The latest candle is still moving, so the signal is confirmed at today's close.",
                 " الشمعة الأخيرة لسا تتحرك، فالإشارة تتأكد عند إغلاق اليوم.") if live else ""
        st.warning(L(f"{what.capitalize()} signal on the latest session ({last:%Y-%m-%d}): the bot will {what} at the next open.{note}",
                     f"إشارة {what} في آخر جلسة ({last:%Y-%m-%d}): البوت ب{'يشتري' if sim['next'] == 'buy' else 'يبيع'} عند الافتتاح التالي.{note}"),
                   icon=":material/bolt:")

    closed = tr[tr["Exit Reason"] != "Open"]
    wins = int((closed["P&L $"] > 0).sum())
    kp = [("account_balance_wallet", L("Balance", "الرصيد"), T.money(sim["final"]), L(f"start {T.money(cap)}", f"البداية {T.money(cap)}"), T.cls(sim["ret"])),
          ("trending_up", L("Return", "العائد"), f"{sim['ret']:+.2f}%", L(f"Buy & hold {m['Buy & Hold %']:+.2f}%", f"شراء واحتفاظ {m['Buy & Hold %']:+.2f}%"), T.cls(sim["ret"])),
          ("show_chart", L("vs S&P 500", "مقابل إس آند بي"),
           "—" if sim["bench_ret"] is None else f"{sim['ret'] - sim['bench_ret']:+.2f}%",
           "" if sim["bench_ret"] is None else f"S&P {sim['bench_ret']:+.2f}%",
           None if sim["bench_ret"] is None else T.cls(sim["ret"] - sim["bench_ret"])),
          ("south_east", L("Max drawdown", "أقصى تراجع"), f"{m['Max Drawdown %']:.2f}%", "", "neg" if m["Max Drawdown %"] < -0.05 else None),
          ("target", L("Win rate", "نسبة النجاح"), f"{m['Win Rate %']:.0f}%" if len(closed) else "—",
           L(f"{wins} of {len(closed)} closed trades", f"{wins} من {len(closed)} صفقة مغلقة"),
           ("pos" if m["Win Rate %"] >= 50 else "neg") if len(closed) else None),
          ("calendar_month", L("Running", "مدة التشغيل"), L(f"{sim['sessions']} sessions", f"{sim['sessions']} جلسة"),
           L(f"since {b['start_date']}", f"منذ {b['start_date']}"), None)]
    for col, (ic, lab, val, sub, kind) in zip(st.columns(6), kp):
        col.markdown(T.kpi(ic, lab, val, sub, kind), unsafe_allow_html=True)

    # price with the bot's trades (from a little before the start)
    full = ta.add_all(sim["full"])
    i0 = max(0, int(full.index.searchsorted(sim["d"].index[0])) - 30)
    view = full.iloc[i0:]
    fig = charts.price_chart(view, "Candles" if len(view) <= 800 else "Line", OVERLAYS.get(b["strategy"], []), PANELS.get(b["strategy"], []),
                             False, trades=tr)
    try:
        fig.add_vline(x=pd.Timestamp(sim["d"].index[0]).strftime("%Y-%m-%d"), line=dict(color=T.GOLD, width=1.2, dash="dot"))
    except Exception:
        pass
    ui.chart(fig, key=f"pb_px_{b['id']}")

    bench = sim["bench"] if sim["bench"] is not None else sim["d"]["Close"] / sim["d"]["Close"].iloc[0] * cap
    bench_name = "S&P 500 (SPY)" if sim["bench"] is not None else L("Buy & Hold", "شراء واحتفاظ")
    ui.chart(charts.equity_chart(sim["equity"], bench, (L("Bot", "البوت"), bench_name, L("Drawdown %", "التراجع %"))), key=f"pb_eq_{b['id']}")

    jr = PB.journal(sim)
    j_closed, j_open = jr[jr["Exit Reason"] != "Open"], jr[jr["Exit Reason"] == "Open"]
    s = autotrader.stats({"trades": j_closed, "open": j_open, "equity": sim["equity"], "bench": bench, "positions": sim["position"],
                          "capital": cap})
    tdash.render(j_closed, j_open, s, cap, key=f"pb_td_{b['id']}")

    ui.sec("table_rows", "All trades", "كل الصفقات")
    if tr.empty:
        st.info(L("No trades yet. The bot trades only when its strategy gives a signal.",
                  "لا توجد صفقات بعد. البوت يتداول فقط لما تعطي الاستراتيجية إشارة."))
        return
    show = tr.copy()
    show.insert(0, "#", range(1, len(show) + 1))
    show["Entry Date"] = pd.to_datetime(show["Entry Date"]).dt.date
    show["Exit Date"] = pd.to_datetime(show["Exit Date"]).dt.date
    show["Exit Reason"] = show["Exit Reason"].map(lambda x: L(x, engine.EXIT_REASON_AR.get(x, x)))
    N = {"Entry Date": L("Entry date", "تاريخ الدخول"), "Entry": L("Entry", "سعر الدخول"), "Exit Date": L("Exit date", "تاريخ الخروج"),
         "Exit": L("Exit / now", "سعر الخروج / الحالي"), "Shares": L("Shares", "الأسهم"), "P&L $": L("P&L $", "الربح $"), "P&L %": L("P&L %", "الربح %"),
         "Bars": L("Days", "الأيام"), "Exit Reason": L("Exit reason", "سبب الخروج")}
    show = show.rename(columns=N)
    st.dataframe(show.iloc[::-1].style.map(T.color_style, subset=[N["P&L %"], N["P&L $"]]).format(
        {N["Entry"]: "{:,.2f}", N["Exit"]: "{:,.2f}", N["Shares"]: "{:,.2f}", N["P&L $"]: "{:+,.2f}", N["P&L %"]: "{:+.2f}%"}),
        hide_index=True, height=min(420, 38 + 35 * len(show)))
    st.download_button(L("Export CSV", "تصدير CSV"), show.to_csv(index=False).encode("utf-8-sig"), f"paper_bot_{b['symbol']}_{b['id']}.csv",
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


def _from_lab():
    lab = ss.get("lab_cfg") or {}
    new = dict(NEW_BOT)
    for k in ("symbol", "strategy", "capital", "fee", "stop", "atr", "tp", "trail"):
        if k in lab:
            new[k] = lab[k]
    new["params"] = {k: dict(v) for k, v in (lab.get("params") or {}).items()}
    ss.pb_new = new


def add_form(bots):
    ui.sec("add_circle", "Add a bot", "أضف بوت")
    if len(bots) >= PB.MAX_BOTS:
        st.info(L(f"You have {PB.MAX_BOTS} bots, the maximum. Delete one to add another.",
                  f"عندك {PB.MAX_BOTS} بوتات، وهذا الحد الأعلى. احذف واحد عشان تضيف غيره."), icon=":material/block:")
        return
    cfg = ss.setdefault("pb_new", {**NEW_BOT, "params": {}})
    if cfg.get("strategy") not in engine.STRATEGIES:
        cfg["strategy"] = NEW_BOT["strategy"]
    st.button(L("Copy my Strategy Lab settings", "انسخ إعدادات مختبر الاستراتيجيات"), icon=":material/content_copy:", on_click=_from_lab,
              key="pb_copylab")
    with st.container(border=True):
        c = st.columns([1.3, 1, 1.6, 1, 0.8])
        cfg["name"] = c[0].text_input(L("Bot name", "اسم البوت"), cfg["name"], max_chars=40, placeholder=L("e.g. Apple trend", "مثال: بوت أبل"))
        cfg["symbol"] = c[1].text_input(L("Symbol", "الرمز"), cfg["symbol"], max_chars=15,
                                        help=L("Any Yahoo Finance symbol: AAPL, SPY, BTC-USD, 2222.SR…",
                                               "أي رمز من ياهو فاينانس: AAPL، SPY، BTC-USD، 2222.SR…")).strip().upper()
        names = list(engine.STRATEGIES)
        cfg["strategy"] = c[2].selectbox(L("Strategy", "الاستراتيجية"), names, index=names.index(cfg["strategy"]), format_func=strat_name)
        cfg["capital"] = c[3].number_input(L("Virtual capital ($)", "رأس المال الوهمي ($)"), 100, 100_000_000, int(cfg["capital"]), step=1000)
        cfg["fee"] = c[4].number_input(L("Fee % / side", "العمولة %"), 0.0, 1.0, float(cfg["fee"]), step=0.01)
        spec = engine.STRATEGIES[cfg["strategy"]][1]
        params = cfg["params"].setdefault(cfg["strategy"], {k: dflt for k, _, _, _, dflt, _ in spec})
        pc = st.columns(len(spec) + 4)
        for i, (k, label, lo, hi, dflt, step) in enumerate(spec):
            lab = L(label, engine.PARAM_AR.get(label, label))
            if isinstance(step, float):
                params[k] = pc[i].number_input(lab, float(lo), float(hi), min(max(float(params.get(k, dflt)), float(lo)), float(hi)), step=float(step))
            else:
                params[k] = pc[i].number_input(lab, int(lo), int(hi), min(max(int(params.get(k, dflt)), int(lo)), int(hi)), step=int(step))
        j = len(spec)
        off = L("0 = off", "0 = إيقاف")
        cfg["stop"] = pc[j].number_input(L("Stop loss %", "وقف الخسارة %"), 0.0, 50.0, float(cfg["stop"]), step=0.5, help=off)
        cfg["atr"] = pc[j + 1].number_input(L("ATR stop ×", "وقف ATR ×"), 0.0, 10.0, float(cfg["atr"]), step=0.5, help=off)
        cfg["tp"] = pc[j + 2].number_input(L("Take profit %", "جني الأرباح %"), 0.0, 500.0, float(cfg["tp"]), step=1.0, help=off)
        cfg["trail"] = pc[j + 3].number_input(L("Trailing stop %", "الوقف المتحرك %"), 0.0, 50.0, float(cfg["trail"]), step=0.5, help=off)
        today = PB.today_ny()
        d1, d2 = st.columns([1, 2], vertical_alignment="bottom")
        start = d1.date_input(L("Start date", "تاريخ البداية"), today, min_value=today - timedelta(days=5 * 365), max_value=today, key="pb_start")
        d2.caption(L("Today = the bot trades live from now on. An earlier date replays the past first, like the Strategy Lab, then carries on live.",
                     "اليوم = البوت يتداول مباشرة من الحين وللأمام. التاريخ الأقدم يعيد تشغيل الفترة الماضية أولاً مثل مختبر الاستراتيجيات، ثم يكمل مباشرة."))

        if st.button(L("Start the bot", "شغّل البوت"), type="primary", icon=":material/play_arrow:", key="pb_create"):
            sym = cfg["symbol"]
            if "fast" in params and "slow" in params and params["fast"] >= params["slow"]:
                st.error(L("Fast period must be smaller than slow period.", "الفترة السريعة لازم تكون أصغر من البطيئة."))
                return
            if not sym:
                st.error(L("Type a symbol.", "اكتب رمز السهم."))
                return
            with st.spinner(L(f"Checking {sym}...", f"جاري التحقق من {sym}...")):
                df = data.history(sym, "2y")
            if df.empty or len(df) < 60:
                st.error(L(f"No price data for {sym}. Check the symbol (for example AAPL, BTC-USD, 2222.SR).",
                           f"لا توجد بيانات للرمز {sym}. تأكد من الرمز (مثلاً AAPL أو BTC-USD أو 2222.SR)."))
                return
            short = strat_name(cfg["strategy"]).split(" (")[0]
            rec = {"name": (cfg["name"].strip() or f"{sym} · {short}")[:40], "symbol": sym, "strategy": cfg["strategy"],
                   "params": dict(params), "capital": float(cfg["capital"]), "fee": float(cfg["fee"]), "stop_pct": float(cfg["stop"]),
                   "atr_mult": float(cfg["atr"]), "tp_pct": float(cfg["tp"]), "trail_pct": float(cfg["trail"]),
                   "start_date": pd.Timestamp(start).strftime("%Y-%m-%d")}
            try:
                PB.create_bot(rec)
            except PB.StoreError as e:
                if e.kind == "full":
                    st.error(L(f"You already have {PB.MAX_BOTS} bots.", f"عندك {PB.MAX_BOTS} بوتات بالفعل."))
                else:
                    storage_notice(e)
                return
            cfg["name"] = ""
            st.toast(L(f"Bot started: {rec['name']}", f"تم تشغيل البوت: {rec['name']}"), icon=":material/rocket_launch:")
            st.rerun()


def delete_list(bots):
    if not bots:
        return
    ui.sec("delete", "Delete a bot", "حذف بوت")
    for b in bots:
        with st.container(border=True):
            a, c = st.columns([4, 1], vertical_alignment="center")
            a.markdown(f'<b>{T.esc(b["name"])}</b> <span class="muted">· {T.esc(b["symbol"])} · {T.esc(strat_name(b["strategy"]))} · '
                       f'{L("since", "منذ")} {T.esc(b["start_date"])}</span>', unsafe_allow_html=True)
            with c.popover(L("Delete", "حذف"), icon=":material/delete:", width="stretch"):
                st.markdown(L(f"Delete **{b['name']}** and its whole record? This can't be undone.",
                              f"حذف **{b['name']}** وكل سجله؟ ما تقدر ترجعه بعدين."))
                if st.button(L("Yes, delete", "نعم، احذف"), type="primary", key=f"pb_del_{b['id']}", icon=":material/delete_forever:"):
                    try:
                        PB.delete_bot(b["id"])
                    except PB.StoreError as e:
                        storage_notice(e)
                        return
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
              f"Up to {PB.MAX_BOTS} bots trade with virtual money on real prices, forward from the day they start. "
              "Same engine as the Strategy Lab: signal on the daily close, order at the next open, stops checked during the day.",
              f"حتى {PB.MAX_BOTS} بوتات تتداول بأموال وهمية على أسعار حقيقية، من يوم تشغيلها وللأمام. "
              "نفس محرك مختبر الاستراتيجيات: الإشارة على الإغلاق اليومي، والتنفيذ عند افتتاح اليوم التالي، والوقف يُفحص خلال اليوم.")
    try:
        bots, err = PB.list_bots(), None
    except PB.StoreError as e:
        bots, err = [], e
    storage_notice(err)

    if bots:
        with st.spinner(L("Updating the bots with the latest prices...", "جاري تحديث البوتات بآخر الأسعار...")):
            sims, spy = PB.run_all(bots)
        ui.safe(leaderboard, sims)
        ui.safe(compare_chart, sims, spy)
        ui.safe(details, sims)
    elif err is None:
        msg = L("No bots yet. Open <b>Manage bots</b> below, pick a symbol and a strategy, and press <b>Start the bot</b>. "
                "From then on the bot checks its strategy after every US close and trades with virtual money at the next open.",
                "ما فيه بوتات للحين. افتح <b>إدارة البوتات</b> تحت، واختر السهم والاستراتيجية، واضغط <b>شغّل البوت</b>. "
                "بعدها البوت يفحص استراتيجيته بعد كل إغلاق للسوق الأمريكي، ويتداول بأموال وهمية عند الافتتاح التالي.")
        ui.html(f'<div class="card" style="line-height:1.9">{T.ico("smart_toy", "acc")} {msg}</div>')

    manage(bots, err)
    st.caption(L("Virtual trading on real daily prices (dividend-adjusted, may be delayed). Results are recalculated from each bot's start date "
                 "whenever the page opens. No real money and no broker are involved. Past results do not guarantee future returns.",
                 "تداول وهمي على أسعار يومية حقيقية (معدّلة بالتوزيعات وقد تكون متأخرة). النتائج تُحسب من جديد من تاريخ بداية كل بوت كل ما تفتح الصفحة. "
                 "لا توجد أموال حقيقية ولا وسيط. النتائج السابقة لا تضمن المستقبل."))
    ui.foot()

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.1"
