"""
p_paper.py - Paper Bots: up to 5 bots that trade with virtual money on real prices, forward from the day they start.
Each bot trades one company, a sector, an industry or all companies, with one or more Strategy Lab strategies, buying stocks
or options.
Top: one card per bot (hover = zoom + a pencil to edit on the right + a red trash on the left; click = select, blue top line)
and an "+ Add Bot" card. Only the selected bots' details are shown below (Select all selects every bot).
Adding, editing and deleting open in dialogs; a password unlocks them when BOTS_PASSWORD is set.
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
from i18n import L, is_ar, sector_name
from sp500 import gics_name

ss = st.session_state
KIND_LABEL = {"company": ("One company", "شركة"), "sector": ("A sector", "قطاع"), "industry": ("An industry", "صناعة"),
              "all": ("All companies", "كل الشركات")}
KIND_ICON = {"company": "domain", "sector": "category", "industry": "factory", "all": "public"}
OVERLAYS = {"SMA Crossover": ["SMA 20", "SMA 50"], "Golden Cross (50/200)": ["SMA 50", "SMA 200"],
            "EMA Crossover": ["EMA 9", "EMA 21"], "Bollinger Breakout": ["Bollinger Bands"]}
PANELS = {"RSI Mean Reversion": ["RSI"], "MACD Crossover": ["MACD"], "OBV Trend (Volume)": ["OBV"], "MFI Money Flow (Volume)": ["MFI"]}
CATS = {"trend": ("Trend", "اتجاه", ["SMA Crossover", "EMA Crossover", "Golden Cross (50/200)", "MACD Crossover"]),
        "breakout": ("Breakout", "اختراق", ["Bollinger Breakout", "Donchian Breakout (Turtle)", "Volume Breakout"]),
        "reversion": ("Mean reversion", "ارتداد", ["RSI Mean Reversion", "MFI Money Flow (Volume)"]),
        "volume": ("Volume", "فوليوم", ["OBV Trend (Volume)", "Volume Breakout", "VWMA Crossover (Volume)", "MFI Money Flow (Volume)"])}
OTYPE_LABEL = {"call": ("Calls (buy signals)", "Call (إشارات الشراء)"), "put": ("Puts (sell signals)", "Put (إشارات البيع)"),
               "both": ("Calls + Puts", "Call + Put")}
STRIKE_LABEL = {-10: ("10% in the money", "داخل السعر 10%"), -5: ("5% in the money", "داخل السعر 5%"), 0: ("At the money", "عند السعر"),
                5: ("5% out of the money", "خارج السعر 5%"), 10: ("10% out of the money", "خارج السعر 10%")}
DEFAULTS = {"pb_name": "", "pb_capital": 100000, "pb_kind": "company", "pb_symbol": "AAPL", "pb_sector": "Technology",
            "pb_ind_sector": "Technology", "pb_industry": "Semiconductors", "pb_maxpos": 5, "pb_store": ["SMA Crossover"],
            "pb_fee": 0.05, "pb_stop": 2.0, "pb_atr": 0.0, "pb_tp": 0.0, "pb_trail": 0.0, "pb_combine": "any", "pb_instr": "stock",
            "pb_otype": "call", "pb_dte": 30, "pb_strike": 0, "pb_oalloc": 5.0, "pb_otp": 100.0, "pb_osl": 50.0}
_A, _D, _BG = T.ACCENT, T.DOWN, T.CARD2
PAGE_CSS = f"""<style>
[class*="st-key-pbred"] button {{ border-color:{_D}88 !important; }}
[class*="st-key-pbred"] button p, [class*="st-key-pbred"] button span {{ color:{_D} !important; }}
[class*="st-key-pbred"] button:hover {{ border-color:{_D} !important; background:{_D}1A !important; }}
.pbc {{ margin:0 !important; min-height:248px; height:100%; transition: box-shadow .18s ease, border-color .18s ease; }}
.pbc .top {{ display:flex; justify-content:flex-end; height:22px; margin:-4px 0 4px; }}
.pbc .rk {{ font-weight:800; color:{T.MUTED}; transition:opacity .15s; }}
.pbc.sel {{ border-top:3px solid {_A}; box-shadow:0 0 0 1px {_A}55, 0 12px 30px {_A}26; }}
.pbadd {{ display:flex; flex-direction:column; align-items:center; justify-content:center; gap:10px; border:1.5px dashed {_A}88 !important;
         color:{_A}; text-align:center; }}
.pbadd .plus {{ width:54px; height:54px; border-radius:50%; background:{_A}22; display:flex; align-items:center; justify-content:center;
               font-size:34px; font-weight:300; line-height:1; }}
.pbadd b {{ font-size:1.02rem; }} .pbadd span.sub {{ color:{T.MUTED}; font-size:.78rem; }}
[class*="st-key-pbcard_"] {{ position:relative; transition:transform .18s ease; }}
[class*="st-key-pbcard_"]:hover {{ transform:translateY(-4px) scale(1.02); z-index:3; }}
[class*="st-key-pbcard_"]:hover .pbc {{ box-shadow:0 14px 34px rgba(61,123,255,.20); }}
[class*="st-key-pbcard_"]:hover .pbc .rk {{ opacity:0; }}
[class*="st-key-pbcard_"] [data-testid="stElementContainer"] {{ position:static !important; }}
[class*="st-key-pbcard_"] [class*="st-key-pb_pick_"] {{ position:absolute !important; inset:0; z-index:4; margin:0 !important; width:auto !important; }}
[class*="st-key-pbcard_"] [class*="st-key-pb_pick_"] .stButton, [class*="st-key-pbcard_"] [class*="st-key-pb_pick_"] button
  {{ width:100% !important; height:100% !important; opacity:0; cursor:pointer; }}
[class*="st-key-pbcard_"] [class*="st-key-pb_edit_"], [class*="st-key-pbcard_"] [class*="st-key-pb_trash_"]
  {{ position:absolute !important; top:9px; z-index:6; width:auto !important; margin:0 !important; opacity:0; transition:opacity .15s ease; }}
[class*="st-key-pbcard_"] [class*="st-key-pb_edit_"] {{ right:9px; left:auto; }}
[class*="st-key-pbcard_"] [class*="st-key-pb_trash_"] {{ left:9px; right:auto; }}
[class*="st-key-pbcard_"]:hover [class*="st-key-pb_edit_"], [class*="st-key-pbcard_"]:hover [class*="st-key-pb_trash_"] {{ opacity:1; }}
[class*="st-key-pb_edit_"] button, [class*="st-key-pb_trash_"] button {{ min-height:0 !important; padding:3px 8px !important; border-radius:10px !important;
  background:{_BG} !important; }}
[class*="st-key-pb_edit_"] button {{ border:1.5px solid {_A} !important; }}
[class*="st-key-pb_edit_"] button span {{ color:{_A} !important; }}
[class*="st-key-pb_trash_"] button {{ border:1.5px solid {_D} !important; }}
[class*="st-key-pb_trash_"] button span {{ color:{_D} !important; }}
[class*="st-key-pb_edit_"] button p, [class*="st-key-pb_trash_"] button p {{ display:none !important; }}
@media (hover: none) {{ [class*="st-key-pbcard_"] [class*="st-key-pb_edit_"], [class*="st-key-pbcard_"] [class*="st-key-pb_trash_"] {{ opacity:1; }} }}
</style>"""


def strat_name(k):
    if k == PB.COMBO:
        return L("Combined rule", "القاعدة المركبة")
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


def combo_rule(bot):
    """'Combined: all 3 agree' / 'Combined: 2 of 3', or None when each strategy trades on its own."""
    c, n = bot.get("combine") or {}, len(bot["strategies"])
    if c.get("mode") != "combo":
        return None
    if c["min"] >= n:
        return L(f"Combined: all {n} agree", f"مركبة: لازم تتفق الـ {n} كلها")
    return L(f"Combined: {c['min']} of {n} agree", f"مركبة: تتفق {c['min']} من {n}")


def how_label(bot, short=False):
    rule = combo_rule(bot)
    names = list(bot["strategies"])
    if rule and short:
        return rule
    if rule:
        return rule + " · " + " + ".join(strat_short(x) for x in names)
    return strategies_label(names, short)


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
    if bot.get("instrument") == "options":
        o = bot["options"]
        return " · ".join([L(*OTYPE_LABEL[o["type"]]), L(f"{o['dte']} days", f"{o['dte']} يوم"), L(*STRIKE_LABEL[o["strike"]]),
                           L(f"{o['alloc']:g}% per trade", f"{o['alloc']:g}% لكل صفقة"), L(f"target +{o['tp']:g}%", f"هدف +{o['tp']:g}%"),
                           L(f"stop -{o['sl']:g}%", f"وقف -{o['sl']:g}%")])
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
# cards: leaderboard with hover actions, selection and "+ Add Bot"
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
        return T.company(b["value"], "", logo, 32, sub=b["name"])
    return (f'<div class="co">{T.ico(KIND_ICON[b["kind"]], "acc")}<div class="nm"><div class="tk">{T.esc(b["name"])}</div>'
            f'<div class="sub">{T.esc(universe_label(b))}</div></div></div>')


def bot_card(rank, sim, logo, selected=False):
    b = sim["bot"]
    top = f'<div class="top"><span class="rk">#{rank}</span></div>'
    badges = f'<div style="margin-top:8px">{T.badge(how_label(b, short=True), "vio", "smart_toy")}'
    if b.get("instrument") == "options":
        badges += T.badge(L("Options", "أوبشن"), "gold", "receipt_long")
    badges += f'{status_badge(sim)}</div>'
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
    return f'<div class="card pbc{" sel" if selected else ""}">{top}{head_html(b, logo)}{badges}{body}</div>'


def add_card(n_bots):
    left = PB.MAX_BOTS - n_bots
    return (f'<div class="card pbc pbadd"><div class="plus">+</div><b>{L("Add Bot", "أضف بوت")}</b>'
            f'<span class="sub">{L(f"{left} of {PB.MAX_BOTS} left", f"باقي {left} من {PB.MAX_BOTS}")}</span></div>')


def ranked(sims):
    return sorted(sims, key=lambda s: (not (s["ok"] and not s["waiting"]), -(s.get("ret") or 0.0) if s["ok"] else 0.0))


def _selected(ids):
    sel = [i for i in ss.get("pb_selected", []) if i in ids]
    ss["pb_selected"] = sel
    return sel


def _toggle(bot_id):
    sel = list(ss.get("pb_selected", []))
    ss["pb_selected"] = [i for i in sel if i != bot_id] if bot_id in sel else sel + [bot_id]


def _select_all(ids):
    ss["pb_selected"] = list(ids)


def _select_none():
    ss["pb_selected"] = []


def _open(mode, bot=None):
    """Card buttons: remember which dialog to open on this run (add / edit / delete) and fill the form."""
    if mode == "add":
        _reset_form()
    elif mode == "edit":
        _load_form(bot)
    ss["pb_open"] = (mode, bot["id"] if bot else None)


def leaderboard(sims, n_bots, can_add):
    ui.sec("leaderboard", "Leaderboard", "ترتيب البوتات")
    ids = [s["bot"]["id"] for s in sims]
    sel = _selected(ids)
    if sims:
        a, b, c, _ = st.columns([1.25, 1.25, 1, 4], vertical_alignment="center")
        a.button(L("Select all", "تحديد الكل"), icon=":material/done_all:", key="pb_selall", on_click=_select_all, args=(ids,),
                 type="primary" if len(sel) < len(ids) else "secondary", width="stretch")
        b.button(L("Clear selection", "إلغاء التحديد"), icon=":material/deselect:", key="pb_selnone", on_click=_select_none,
                 disabled=not sel, width="stretch")
        if PB.admin_mode() == "password" and ss.get("pb_admin"):
            if c.button(L("Lock", "قفل"), icon=":material/lock:", key="pb_lock", width="stretch"):
                ss.pb_admin = False
                st.rerun()
    lg = data.logos([s["bot"]["value"] for s in sims if s["bot"]["kind"] == "company"])
    items = [(i, s) for i, s in enumerate(ranked(sims), 1)] + ([("add", None)] if can_add else [])
    per_row = 5
    for r in range(0, len(items), per_row):
        cols = st.columns(per_row)
        for col, (rank, sim) in zip(cols, items[r:r + per_row]):
            with col:
                if rank == "add":
                    with st.container(key="pbcard_add"):
                        ui.html(add_card(n_bots))
                        st.button(L("Add Bot", "أضف بوت"), key="pb_pick_add", on_click=_open, args=("add",), width="stretch")
                    continue
                b = sim["bot"]
                with st.container(key=f"pbcard_{b['id']}"):
                    ui.html(bot_card(rank, sim, lg.get(b["value"]), b["id"] in sel))
                    st.button(b["name"], key=f"pb_pick_{b['id']}", on_click=_toggle, args=(b["id"],), width="stretch")
                    st.button(L("Edit", "تعديل"), icon=":material/edit:", key=f"pb_edit_{b['id']}", on_click=_open, args=("edit", b),
                              help=L("Edit this bot", "تعديل البوت"))
                    st.button(L("Delete", "حذف"), icon=":material/delete:", key=f"pb_trash_{b['id']}", on_click=_open, args=("delete", b),
                              help=L("Delete this bot", "حذف البوت"))
    return sel


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
def _order_txt(item):
    sym, label, kind = item
    extra = "" if kind == "Stock" else f" {kind.upper()}"
    return f"{sym} ({strat_short(label)}{extra})"


def details(sim):
    b = sim["bot"]
    names = list(b["strategies"])
    group = b["kind"] != "company"
    opts = b.get("instrument") == "options"
    uni = universe_label(b, sim.get("n_symbols") if sim["ok"] else None)
    ui.html(f'<div style="font-weight:800;font-size:1.15rem;margin:6px 0 8px">{head_html(b)}</div>')
    badges = T.badge(uni, "gold", KIND_ICON[b["kind"]]) + T.badge(how_label(b), "vio", "smart_toy")
    if opts:
        badges += T.badge(L("Buys options", "يشتري أوبشن"), "gold", "receipt_long")
    if group:
        badges += T.badge(L(f"Up to {b['max_pos']} trades at once", f"حتى {b['max_pos']} صفقات في نفس الوقت"), "neu", "stacks")
    badges += (T.badge(_risk_txt(b), "neu", "shield") + T.badge(L("Start ", "البداية ") + b["start_date"], "neu", "event")
               + T.badge(L("Capital ", "رأس المال ") + T.money(b["capital"]), "neu", "account_balance_wallet"))
    if not opts:
        badges += T.badge(L("Fee {:g}% / side", "العمولة {:g}% لكل جهة").format(b["fee"]), "neu", "receipt")
    ui.html(f'<div class="card">{badges}</div>')
    with st.expander(L("How this bot trades", "طريقة تداول البوت"), icon=":material/tune:"):
        rows = "".join(f'<div style="margin:4px 0">{T.badge(strat_name(n), "vio", "smart_toy")} '
                       f'<span class="muted">{T.esc(_params_txt(n, p))}</span></div>' for n, p in b["strategies"].items())
        ui.html(rows or "—")
        if combo_rule(b):
            st.caption(combo_caption(b["combine"]["min"], len(names)))
        elif len(names) > 1:
            st.caption(L("Any of these strategies can open a trade. A trade closes on the exit signal of the strategy that opened it, "
                         "or by the stop loss, take profit or trailing stop.",
                         "أي استراتيجية منها تقدر تفتح صفقة، والصفقة تتقفل بإشارة الخروج من نفس الاستراتيجية اللي فتحتها، "
                         "أو بوقف الخسارة أو جني الأرباح أو الوقف المتحرك."))
        if opts:
            st.caption(options_caption())

    if not sim["ok"]:
        if sim["why"] == "strategy":
            st.warning(L("This bot's strategy or group no longer exists on the site. Edit it or delete it.",
                         "استراتيجية هذا البوت أو مجموعته لم تعد موجودة في الموقع. عدّله أو احذفه."), icon=":material/error:")
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
            what = f"{o['Contract']} · " if opts else ""
            st.success(what + L(f"In a trade since {pd.Timestamp(o['Entry Date']):%b %d, %Y} at ${o['Entry']:,.2f} · open P&L {o['P&L %']:+.2f}%",
                                f"في صفقة منذ {pd.Timestamp(o['Entry Date']):%Y-%m-%d} بسعر ${o['Entry']:,.2f} · الربح الحالي {o['P&L %']:+.2f}%"),
                       icon=":material/trending_up:")
        else:
            st.info(L("Out of the market, waiting for a buy signal.", "خارج السوق، ينتظر إشارة شراء."), icon=":material/pause_circle:")
    elif len(op):
        st.success(L(f"{len(op)} open trades: ", f"{len(op)} صفقات مفتوحة: ") + ", ".join(op["Contract"] if opts else op["Symbol"]),
                   icon=":material/trending_up:")
    else:
        st.info(L("No open trades, waiting for signals.", "لا توجد صفقات مفتوحة، ينتظر إشارات."), icon=":material/pause_circle:")
    if sim["next_buys"] or sim["next_sells"]:
        parts = []
        if sim["next_buys"]:
            parts.append(L("buy ", "شراء ") + ", ".join(_order_txt(x) for x in sim["next_buys"]))
        if sim["next_sells"]:
            parts.append(L("sell ", "بيع ") + ", ".join(_order_txt(x) for x in sim["next_sells"]))
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
        overlays = list(dict.fromkeys(o for n in names for o in OVERLAYS.get(n, [])))
        panels = list(dict.fromkeys(p for n in names for p in PANELS.get(n, [])))[:2]
        marks = tr[tr["Symbol"] == sym].copy()
        if opts:                                     # options: mark the stock price, not the option premium
            marks["Entry"], marks["Exit"] = marks["Stock Entry"], marks["Stock Exit"]
        fig = charts.price_chart(view, "Candles" if len(view) <= 800 else "Line", overlays, panels, False, trades=marks)
        try:
            fig.add_vline(x=pd.Timestamp(sim["equity"].index[0]).strftime("%Y-%m-%d"), line=dict(color=T.GOLD, width=1.2, dash="dot"))
        except Exception:
            pass
        ui.chart(fig, key=f"pb_px_{b['id']}")

    ui.sec("show_chart", "Balance vs the market", "الرصيد مقابل السوق")
    bench = sim["bench"] if sim["bench"] is not None else sim["group"]
    bench_name = "S&P 500 (SPY)" if sim["bench"] is not None else L("Buy & Hold", "شراء واحتفاظ")
    ui.chart(charts.equity_chart(sim["equity"], bench, (L("Bot", "البوت"), bench_name, L("Drawdown %", "التراجع %"))), key=f"pb_eq_{b['id']}")
    ui.chart(charts.monthly_heatmap(engine.monthly_returns(sim["equity"]), L("Monthly returns", "العوائد الشهرية"),
                                    tdash.MONTHS_AR if is_ar() else None), key=f"pb_month_{b['id']}")

    jr = PB.journal(sim)
    j_closed, j_open = jr[jr["Exit Reason"] != "Open"], jr[jr["Exit Reason"] == "Open"]
    s = autotrader.stats({"trades": j_closed, "open": j_open, "equity": sim["equity"], "bench": bench, "positions": sim["npos"],
                          "capital": cap})
    tdash.render(j_closed, j_open, s, cap, key=f"pb_td_{b['id']}")

    by_strat = len(names) > 1 and not combo_rule(b)
    if len(closed) and (group or by_strat):
        ui.sec("pie_chart", "What worked", "ماذا نجح")
        c1, c2 = st.columns(2)
        if by_strat:
            g = closed.groupby("Strategy")["P&L $"].sum().sort_values()
            ui.chart(charts.hbar([strat_short(k) for k in g.index], [float(v) for v in g.values], L("P&L by strategy ($)", "الربح حسب الاستراتيجية ($)"),
                                 max(260, 34 * len(g) + 80), suffix=""), key=f"pb_bys_{b['id']}", container=c1)
        if group:
            g = closed.groupby("Symbol")["P&L $"].sum()
            g = pd.concat([g.nlargest(6), g.nsmallest(6)]).groupby(level=0).first().sort_values()
            ui.chart(charts.hbar(list(g.index), [float(v) for v in g.values], L("P&L by stock, best and worst ($)", "الربح حسب السهم، الأفضل والأسوأ ($)"),
                                 max(260, 30 * len(g) + 80), suffix=""), key=f"pb_bysym_{b['id']}", container=c2 if by_strat else c1)

    ui.sec("table_rows", "All trades", "كل الصفقات")
    if tr.empty:
        st.info(L("No trades yet. The bot trades only when a strategy gives a signal.",
                  "لا توجد صفقات بعد. البوت يتداول فقط لما تعطي استراتيجية إشارة."))
        return
    show = tr.copy() if opts else tr.drop(columns=["Type", "Contract", "Stock Entry", "Stock Exit", "Fees"])
    if opts:
        show = show.drop(columns=["Fees"])
    show.insert(0, "#", range(1, len(show) + 1))
    show["Strategy"] = show["Strategy"].map(strat_short)
    show["Entry Date"] = pd.to_datetime(show["Entry Date"]).dt.date
    show["Exit Date"] = pd.to_datetime(show["Exit Date"]).dt.date
    show["Exit Reason"] = show["Exit Reason"].map(lambda x: L(x, engine.EXIT_REASON_AR.get(x, x)))
    N = {"Symbol": L("Symbol", "الرمز"), "Strategy": L("Strategy", "الاستراتيجية"), "Entry Date": L("Entry date", "تاريخ الدخول"),
         "Entry": L("Entry", "سعر الدخول"), "Exit Date": L("Exit date", "تاريخ الخروج"), "Exit": L("Exit / now", "سعر الخروج / الحالي"),
         "Shares": L("Shares", "الأسهم"), "P&L $": L("P&L $", "الربح $"), "P&L %": L("P&L %", "الربح %"), "Bars": L("Days", "الأيام"),
         "Exit Reason": L("Exit reason", "سبب الخروج"), "Type": L("Type", "النوع"), "Contract": L("Contract", "العقد"),
         "Stock Entry": L("Stock at entry", "السهم عند الدخول"), "Stock Exit": L("Stock at exit / now", "السهم عند الخروج / الحالي")}
    if opts:
        N.update({"Entry": L("Premium in", "سعر العقد دخول"), "Exit": L("Premium out / now", "سعر العقد خروج / الحالي"),
                  "Shares": L("Contracts", "العقود")})
    show = show.rename(columns=N)
    st.dataframe(show.iloc[::-1].style.map(T.color_style, subset=[N["P&L %"], N["P&L $"]]).format(
        {N["Entry"]: "{:,.2f}", N["Exit"]: "{:,.2f}", N["Shares"]: "{:,.0f}" if opts else "{:,.2f}", N["P&L $"]: "{:+,.2f}",
         N["P&L %"]: "{:+.2f}%", **({N["Stock Entry"]: "{:,.2f}", N["Stock Exit"]: "{:,.2f}"} if opts else {})}),
        hide_index=True, height=min(420, 38 + 35 * len(show)))
    st.download_button(L("Export CSV", "تصدير CSV"), show.to_csv(index=False).encode("utf-8-sig"), f"paper_bot_{b['id']}.csv",
                       "text/csv", icon=":material/download:", key=f"pb_csv_{b['id']}")




# =====================================================================
# dialogs: unlock · add / edit · delete
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
        st.info(L("To add, edit or delete bots, add BOTS_PASSWORD to your Streamlit Secrets (Settings → Secrets). Visitors can only watch the bots.",
                  "لإضافة البوتات أو تعديلها أو حذفها، أضف BOTS_PASSWORD في Secrets حق Streamlit (Settings ← Secrets). الزوار يقدرون يشاهدون البوتات فقط."),
                icon=":material/lock:")
        st.code('BOTS_PASSWORD = "' + L("choose-a-password", "اختر-كلمة-مرور") + '"', language="toml")
        return False
    st.caption(L("Visitors can watch the bots. Enter your password to add, edit or delete bots.",
                 "الزوار يقدرون يشاهدون البوتات. اكتب كلمة المرور لإضافة البوتات أو تعديلها أو حذفها."))
    a, b = st.columns([3, 1], vertical_alignment="bottom")
    a.text_input(L("Password", "كلمة المرور"), type="password", key="pb_pw", on_change=_unlock)
    b.button(L("Unlock", "دخول"), icon=":material/lock_open:", on_click=_unlock, width="stretch", key="pb_unlock")
    if ss.pop("pb_bad_pw", False):
        st.error(L("Wrong password.", "كلمة المرور غير صحيحة."))
    return False


FORM_KEYS = list(DEFAULTS) + ["pb_min", "pb_start", "pb_cat", "pb_edit_id"]


def _reset_form():
    for k in [k for k in list(ss.keys()) if k in FORM_KEYS or str(k).startswith("pb_strats_")]:
        del ss[k]


def _init_form():
    for k, v in DEFAULTS.items():
        if k not in ss:
            ss[k] = list(v) if isinstance(v, list) else v
    if ss.get("pb_kind") not in PB.KINDS:          # clicking the selected option again clears it
        ss["pb_kind"] = "company"
    if not isinstance(ss.get("pb_store"), list):
        ss["pb_store"] = []
    today = PB.today_ny()
    if "pb_start" not in ss or ss["pb_start"] > today:
        ss["pb_start"] = today


def _clip(v, lo, hi, cast=float):
    return cast(min(max(cast(v), lo), hi))


def _load_form(bot):
    """Fill the form with a bot's settings (pencil on its card)."""
    _reset_form()
    k, v = bot["kind"], bot["value"]
    ss.update({"pb_edit_id": bot["id"], "pb_name": bot["name"], "pb_capital": _clip(round(bot["capital"]), 100, 100_000_000, int),
               "pb_kind": k, "pb_store": [s for s in engine.STRATEGIES if s in bot["strategies"]], "pb_combine": bot["combine"]["mode"],
               "pb_maxpos": _clip(bot["max_pos"] if k != "company" else 5, 1, PB.MAX_POS_LIMIT, int),
               "pb_instr": bot.get("instrument", "stock"), "pb_fee": _clip(bot["fee"], 0.0, 1.0), "pb_stop": _clip(bot["stop_pct"], 0.0, 50.0),
               "pb_atr": _clip(bot["atr_mult"], 0.0, 10.0), "pb_tp": _clip(bot["tp_pct"], 0.0, 500.0),
               "pb_trail": _clip(bot["trail_pct"], 0.0, 50.0), "pb_start": pd.Timestamp(bot["start_date"]).date()})
    if bot["combine"]["mode"] == "combo":
        ss["pb_min"] = int(bot["combine"]["min"])
    o = bot.get("options") or PB.OPTION_DEFAULTS
    ss.update({"pb_otype": o["type"], "pb_dte": int(o["dte"]), "pb_strike": int(o["strike"]), "pb_oalloc": float(o["alloc"]),
               "pb_otp": float(o["tp"]), "pb_osl": float(o["sl"])})
    if k == "company":
        ss["pb_symbol"] = v
    elif k == "sector":
        ss["pb_sector"] = v
    elif k == "industry":
        ss["pb_industry"], ss["pb_ind_sector"] = v, PB.industry_sector(v) or "Technology"


def _pick_changed(key, opts):
    """Strategy pills of one filter changed: keep the picks from the other filters."""
    picked = set(ss.get(key) or [])
    keep = [s for s in ss.get("pb_store", []) if s not in opts]
    ss["pb_store"] = [s for s in engine.STRATEGIES if s in picked or s in keep]


def _all_strats():
    ss["pb_store"] = list(engine.STRATEGIES)


def _no_strats():
    ss["pb_store"] = []


def combo_caption(need, n):
    return L(f"A strategy agrees while it is in its buy state: from its own buy signal until its own sell signal. The bot buys on the day "
             f"at least {need} of the {n} agree, and sells when fewer than {need} agree, or by the stop loss, take profit or trailing stop.",
             f"الاستراتيجية تعتبر موافقة ما دامها في وضع شراء: من إشارة الشراء حقها لين إشارة البيع حقها. البوت يشتري في اليوم اللي توافق فيه "
             f"{need} على الأقل من الـ {n}، ويبيع إذا صار الموافق أقل من {need}، أو بوقف الخسارة أو جني الأرباح أو الوقف المتحرك.")


def options_caption():
    return L("Calls are bought on buy signals and puts on sell signals; each position is closed on the opposite signal of the same rule, at "
             "the option's take profit or stop loss (checked at the close), or 5 days before expiry. Option prices are estimated with the "
             "Black-Scholes model from each stock's own volatility, plus $0.65 per contract, so real prices will differ.",
             "عقود Call تنشرى مع إشارات الشراء، وعقود Put مع إشارات البيع. كل عقد يتقفل بالإشارة المعاكسة من نفس القاعدة، أو عند هدف الربح أو "
             "وقف الخسارة للعقد (يُفحص عند الإغلاق)، أو قبل الانتهاء بـ 5 أيام. أسعار العقود تقديرية بنموذج بلاك-شولز من تذبذب السهم نفسه، "
             "مع 0.65$ لكل عقد، فالأسعار الحقيقية تختلف.")


def _default_name(kind, value, strats, need=None, options=False):
    n = len(strats)
    how = strat_short(strats[0]) if n == 1 else (L("all strategies", "كل الاستراتيجيات") if n == len(engine.STRATEGIES)
                                                  else L(f"{n} strategies", f"{n} استراتيجيات"))
    if need:
        how = L(f"combined {need}/{n}", f"مركبة {need}/{n}")
    what = {"company": value, "sector": sector_name(value), "industry": gics_name(value), "all": L("All companies", "كل الشركات")}[kind]
    return f"{what} · {how}{' · ' + L('options', 'أوبشن') if options else ''}"[:40]


def bot_form(mode, bot=None):
    """The add / edit form (inside a dialog)."""
    _init_form()
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

    # 2) what it buys
    ui.valid("pb_instr", ["stock", "options"])
    instr = st.segmented_control(L("What does the bot buy?", "وش يشتري البوت؟"), ["stock", "options"], key="pb_instr",
                                 format_func=lambda k: {"stock": L("Stocks", "أسهم"), "options": L("Options", "أوبشن")}[k]) or "stock"
    if kind != "company":
        m1, m2 = st.columns([1, 2], vertical_alignment="bottom")
        maxpos = m1.number_input(L("Max open trades", "أقصى عدد صفقات مفتوحة"), 1, PB.MAX_POS_LIMIT, step=1, key="pb_maxpos")
        share = L("a set % of the balance (below)", "نسبة ثابتة من الرصيد (تحت)") if instr == "options" else f"1/{maxpos}"
        m2.caption(L(f"Each trade gets {share} of the balance. After every close the bot checks all {count} stocks; "
                     "when more stocks signal than free slots, it buys the strongest of the last 3 months first (puts: the weakest).",
                     f"كل صفقة تاخذ {share} من الرصيد. بعد كل إغلاق يفحص البوت كل الـ {count} سهم، "
                     "وإذا أعطت أسهم إشارات أكثر من الأماكن الفاضية، يشتري الأقوى أداءً آخر 3 أشهر أولاً (والـ Put الأضعف)."))

    # 3) strategies: filter · pills · select all
    names = list(engine.STRATEGIES)
    ui.valid("pb_cat", list(CATS))
    cat = st.segmented_control(L("Filter strategies", "فلتر الاستراتيجيات"), list(CATS), key="pb_cat",
                               format_func=lambda k: L(*CATS[k][:2]))
    opts = [s for s in names if s in CATS[cat][2]] if cat in CATS else names
    pkey = f"pb_strats_{cat or 'all'}"
    ss[pkey] = [s for s in opts if s in ss.get("pb_store", [])]
    st.pills(L("Strategies: one, several or all", "الاستراتيجيات: وحدة أو أكثر أو الكل"), opts, selection_mode="multi", key=pkey,
             format_func=strat_name, on_change=_pick_changed, args=(pkey, opts))
    strats = [s for s in names if s in ss.get("pb_store", [])]
    s1, s2, s3 = st.columns([1.2, 1, 3], vertical_alignment="center")
    s1.button(L("Select all", "تحديد الكل"), icon=":material/done_all:", on_click=_all_strats, key="pb_allstrats", width="stretch",
              type="primary" if len(strats) < len(names) else "secondary")
    s2.button(L("Clear", "مسح"), icon=":material/close:", on_click=_no_strats, key="pb_nostrats", width="stretch", disabled=not strats)
    s3.caption(L(f"{len(strats)} selected: ", f"{len(strats)} مختارة: ") + (", ".join(strat_short(s) for s in strats) or "—"))
    mode_, need = "any", None
    if len(strats) > 1:
        ui.valid("pb_combine", ["any", "combo"])
        mode_ = st.segmented_control(L("How do the strategies work together?", "كيف تشتغل الاستراتيجيات مع بعض؟"), ["any", "combo"],
                                     key="pb_combine", format_func=lambda k: {
                                         "any": L("Each on its own", "كل وحدة لحالها"),
                                         "combo": L("Combined (custom rule)", "مركبة (قاعدة مخصصة)")}[k]) or "any"
        if mode_ == "combo":
            n = len(strats)
            if not isinstance(ss.get("pb_min"), int) or not 2 <= ss["pb_min"] <= n:
                ss["pb_min"] = n
            q1, q2 = st.columns([1, 2], vertical_alignment="bottom")
            need = q1.number_input(L(f"Buy only when at least … of {n} agree", f"يشتري فقط إذا اتفقت على الأقل … من {n}"), 2, n, step=1,
                                   key="pb_min")
            q2.caption(combo_caption(need, n))
        else:
            st.caption(L("Any selected strategy can open a trade; the trade closes on the exit signal of the strategy that opened it, "
                         "or by the stop loss, take profit or trailing stop.",
                         "أي استراتيجية مختارة تقدر تفتح صفقة، والصفقة تتقفل بإشارة الخروج من نفس الاستراتيجية اللي فتحتها، "
                         "أو بوقف الخسارة أو جني الأرباح أو الوقف المتحرك."))

    # 4) exits: option filters, or the stock stops and fee
    if instr == "options":
        ui.sec("tune", "Option filters", "فلاتر الأوبشن")
        o1, o2, o3 = st.columns(3)
        ui.valid("pb_otype", list(PB.OPTION_TYPES))
        o1.selectbox(L("Option type", "نوع العقد"), list(PB.OPTION_TYPES), key="pb_otype", format_func=lambda k: L(*OTYPE_LABEL[k]))
        o2.number_input(L("Days to expiry", "أيام حتى الانتهاء"), 7, 180, step=1, key="pb_dte")
        ui.valid("pb_strike", list(PB.STRIKES))
        o3.selectbox(L("Strike", "سعر التنفيذ"), list(PB.STRIKES), key="pb_strike", format_func=lambda k: L(*STRIKE_LABEL[k]))
        o4, o5, o6 = st.columns(3)
        o4.number_input(L("Per trade (% of balance)", "لكل صفقة (% من الرصيد)"), 0.5, 50.0, step=0.5, key="pb_oalloc")
        o5.number_input(L("Take profit on the option %", "هدف ربح العقد %"), 5.0, 2000.0, step=5.0, key="pb_otp")
        o6.number_input(L("Stop loss on the option %", "وقف خسارة العقد %"), 5.0, 95.0, step=5.0, key="pb_osl")
        st.caption(options_caption())
    else:
        r = st.columns(5)
        off = L("0 = off", "0 = إيقاف")
        r[0].number_input(L("Fee % / side", "العمولة %"), 0.0, 1.0, step=0.01, key="pb_fee")
        r[1].number_input(L("Stop loss %", "وقف الخسارة %"), 0.0, 50.0, step=0.5, help=off, key="pb_stop")
        r[2].number_input(L("ATR stop ×", "وقف ATR ×"), 0.0, 10.0, step=0.5, help=off, key="pb_atr")
        r[3].number_input(L("Take profit %", "جني الأرباح %"), 0.0, 500.0, step=1.0, help=off, key="pb_tp")
        r[4].number_input(L("Trailing stop %", "الوقف المتحرك %"), 0.0, 50.0, step=0.5, help=off, key="pb_trail")

    # 5) start
    today = PB.today_ny()
    low = min(today - timedelta(days=5 * 365), ss["pb_start"])
    d1, d2 = st.columns([1, 2], vertical_alignment="bottom")
    start = d1.date_input(L("Start date", "تاريخ البداية"), min_value=low, max_value=today, key="pb_start")
    d2.caption(L("Today = the bot trades live from now on. An earlier date replays the past first, like the Strategy Lab, then carries on live.",
                 "اليوم = البوت يتداول مباشرة من الحين وللأمام. التاريخ الأقدم يعيد تشغيل الفترة الماضية أولاً مثل مختبر الاستراتيجيات، ثم يكمل مباشرة."))

    label = L("Start the bot", "شغّل البوت") if mode == "add" else L("Save changes", "حفظ التعديلات")
    if not st.button(label, type="primary", icon=":material/play_arrow:" if mode == "add" else ":material/save:", key="pb_create"):
        return
    if not strats:
        st.error(L("Pick at least one strategy.", "اختر استراتيجية وحدة على الأقل."))
        return
    keep = (bot or {}).get("strategies", {})
    params = {s: keep.get(s, {}) for s in strats}                     # an edited bot keeps its own strategy settings
    for s in strats:
        p = PB.clean_params(s, params[s])
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
    combo = mode_ == "combo" and len(strats) > 1
    is_opt = instr == "options"
    name = str(ss.get("pb_name") or "").strip() or _default_name(kind, value, strats, need if combo else None, is_opt)
    options = {"type": ss["pb_otype"], "dte": ss["pb_dte"], "strike": ss["pb_strike"], "alloc": ss["pb_oalloc"], "tp": ss["pb_otp"],
               "sl": ss["pb_osl"]} if is_opt else None
    risk = (0.0, 0.0, 0.0, 0.0) if is_opt else (ss["pb_stop"], ss["pb_atr"], ss["pb_tp"], ss["pb_trail"])
    rec = PB.make_record(name, kind, value, params, ss.get("pb_maxpos", 5), ss["pb_capital"], ss["pb_fee"], *risk,
                         pd.Timestamp(start).strftime("%Y-%m-%d"), {"mode": "combo", "min": int(need)} if combo else None,
                         instrument=instr, options=options)
    try:
        if mode == "add":
            PB.create_bot(rec)
        else:
            PB.update_bot(bot["id"], rec)
    except PB.StoreError as e:
        if e.kind == "full":
            st.error(L(f"You already have {PB.MAX_BOTS} bots.", f"عندك {PB.MAX_BOTS} بوتات بالفعل."))
        else:
            storage_notice(e)
        return
    if mode == "add":
        st.toast(L(f"Bot started: {name}", f"تم تشغيل البوت: {name}"), icon=":material/rocket_launch:")
    else:
        st.toast(L(f"Saved: {name}", f"تم الحفظ: {name}"), icon=":material/save:")
    st.rerun()


def _bot_dialog_body(mode, bot, n_bots):
    if not can_edit():
        return
    if mode == "add" and n_bots >= PB.MAX_BOTS:
        st.info(L(f"You have {PB.MAX_BOTS} bots, the maximum. Delete one to add another.",
                  f"عندك {PB.MAX_BOTS} بوتات، وهذا الحد الأعلى. احذف واحد عشان تضيف غيره."), icon=":material/block:")
        return
    if mode == "edit":
        st.caption(L("Saving replays the bot from its start date with the new settings.",
                     "الحفظ يعيد حساب البوت من تاريخ بدايته بالإعدادات الجديدة."))
    bot_form(mode, bot)


def _delete_body(bot):
    if not can_edit():
        return
    st.markdown(L(f"Delete **{bot['name']}** and its whole record? This can't be undone.",
                  f"حذف **{bot['name']}** وكل سجله؟ ما تقدر ترجعه بعدين."))
    y, n = st.columns(2)
    if y.button(L("Yes, delete", "نعم، احذف"), type="primary", key=f"pb_yes_{bot['id']}", icon=":material/delete_forever:", width="stretch"):
        try:
            PB.delete_bot(bot["id"])
        except PB.StoreError as e:
            storage_notice(e)
            return
        ss["pb_selected"] = [i for i in ss.get("pb_selected", []) if i != bot["id"]]
        st.toast(L("Bot deleted.", "تم حذف البوت."), icon=":material/delete:")
        st.rerun()
    with n.container(key=f"pbred_no_{bot['id']}"):
        if st.button(L("No", "لا"), key=f"pb_no_{bot['id']}", icon=":material/close:", width="stretch"):
            st.rerun()


def open_dialog(op, bots):
    mode, bid = op
    bot = next((b for b in bots if b["id"] == bid), None)
    if mode == "delete" and bot:
        st.dialog(L("Delete bot", "حذف البوت"))(_delete_body)(bot)
    elif mode == "edit" and bot:
        st.dialog(L("Edit bot", "تعديل البوت"), width="large")(_bot_dialog_body)("edit", bot, len(bots))
    elif mode == "add":
        st.dialog(L("Add a bot", "أضف بوت"), width="large")(_bot_dialog_body)("add", None, len(bots))


# =====================================================================
# page
# =====================================================================
def page_paper_bots():
    ui.html(PAGE_CSS)
    ui.header("robot_2", "Paper Bots", "البوتات الافتراضية",
              f"Up to {PB.MAX_BOTS} bots trade with virtual money on real prices, forward from the day they start. Each one trades a company, "
              "a sector, an industry or all companies, with one or more strategies, buying stocks or options.",
              f"حتى {PB.MAX_BOTS} بوتات تتداول بأموال وهمية على أسعار حقيقية، من يوم تشغيلها وللأمام. كل بوت يتداول شركة أو قطاع أو صناعة أو كل الشركات، "
              "باستراتيجية وحدة أو أكثر، ويشتري أسهم أو أوبشن.")
    try:
        bots, err = PB.list_bots(), None
    except PB.StoreError as e:
        bots, err = [], e
    storage_notice(err)

    sims, spy = [], None
    if bots:
        big = any(b["kind"] != "company" for b in bots)
        with st.spinner(L("Updating the bots with the latest prices" + (" (groups of stocks can take up to a minute)..." if big else "..."),
                          "جاري تحديث البوتات بآخر الأسعار" + (" (مجموعات الأسهم قد تاخذ لين دقيقة)..." if big else "..."))):
            sims, spy = PB.run_all(bots)
    sel = ui.safe(leaderboard, sims, len(bots), err is None and len(bots) < PB.MAX_BOTS) or []

    op = ss.pop("pb_open", None)
    if op and err is None:
        open_dialog(op, bots)

    if not bots and err is None:
        ui.html(f'<div class="card" style="line-height:1.9;margin-top:14px">{T.ico("smart_toy", "acc")} ' + L(
            "No bots yet. Press <b>+ Add Bot</b>, choose what the bot trades (a company, a sector, an industry or all companies), what it buys "
            "(stocks or options) and its strategies. From then on it checks its strategies after every US close and trades with virtual money "
            "at the next open.",
            "ما فيه بوتات للحين. اضغط <b>+ أضف بوت</b>، واختر وش يتداول (شركة أو قطاع أو صناعة أو كل الشركات)، ووش يشتري (أسهم أو أوبشن)، "
            "واستراتيجياته. بعدها يفحص استراتيجياته بعد كل إغلاق للسوق الأمريكي، ويتداول بأموال وهمية عند الافتتاح التالي.") + "</div>")
    elif sims:
        chosen = [s for s in ranked(sims) if s["bot"]["id"] in sel]
        if not chosen:
            ui.html(f'<div class="card" style="line-height:1.9;margin-top:14px">{T.ico("ads_click", "acc")} ' + L(
                "Click a bot's card to see its details. Select one, several, or press <b>Select all</b>.",
                "اضغط على كرت البوت عشان تشوف تفاصيله. تقدر تحدد واحد أو أكثر، أو تضغط <b>تحديد الكل</b>.") + "</div>")
        elif len(chosen) == 1:
            ui.safe(details, chosen[0])
        else:
            ui.safe(compare_chart, chosen, spy)
            rank = {s["bot"]["id"]: i for i, s in enumerate(ranked(sims), 1)}
            tabs = st.tabs([f'#{rank[s["bot"]["id"]]} {s["bot"]["name"]}' for s in chosen])
            for tab, s in zip(tabs, chosen):
                with tab:
                    ui.safe(details, s)

    st.caption(L("Virtual trading on real daily prices (dividend-adjusted, may be delayed). Results are recalculated from each bot's start date "
                 "whenever the page opens. No real money and no broker are involved. Past results do not guarantee future returns.",
                 "تداول وهمي على أسعار يومية حقيقية (معدّلة بالتوزيعات وقد تكون متأخرة). النتائج تُحسب من جديد من تاريخ بداية كل بوت كل ما تفتح الصفحة. "
                 "لا توجد أموال حقيقية ولا وسيط. النتائج السابقة لا تضمن المستقبل."))
    ui.foot()

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.3"
