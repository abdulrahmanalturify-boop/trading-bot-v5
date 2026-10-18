"""
p_hunter_v3.py - Hunter V3 · Alpha Lab (menu: الصياد V3), laid out like the Opportunity Hunter (p_scanner.py).

The engine (hunter_v3.py) is untouched: this page only draws its results in the hunter's look.
Top to bottom:
  * a hero in the site's colours: the radar with the best-ranked stocks as blips, the totals as chips,
  * the hunt bar: the universe, the paper capital and the risk settings, the Run button,
  * the market's mood (the same tiles as the hunter) and the model's state (validation, samples, IC, exposure cap),
  * filters (setups with their counts, rank at least, no risk flags, with a forecast only, new today only),
  * the best-ranked opportunities as cards (click one to open it), then the opened one: chart with entry / stop / target,
    why it ranked what it ranked, the setup's plan and its line in the paper allocation,
  * the hypothetical allocation, every result in one table, the opportunity map and the sectors,
  * the methodology and its limits.
"""
import numpy as np
import pandas as pd
import streamlit as st

import charts
import data
import hunter as H
import hunter_v3 as V3
import p_scanner as S
import paperbots as PB
import theme as T
import ui
import universe as U
from i18n import L, is_ar, sector_name
from sp500 import SP500

ss = st.session_state
_A, _V, _C, _G, _D, _U, _MU = T.ACCENT, T.VIOLET, T.CYAN, T.GOLD, T.DOWN, T.UP, "#9D97A5"
DEFAULT = (
    "AAPL", "MSFT", "NVDA", "AMD", "GOOGL", "META", "DIS",
    "JPM", "BAC", "WFC", "XOM", "CVX", "SLB", "UNH", "JNJ", "MRK",
    "AMZN", "HD", "MCD", "NKE", "WMT", "PG", "KO", "CAT", "DE",
    "UPS", "NEE", "DUK", "SO",
)
UNIS = {"core": ("Core 29", "الأساسية (29 سهم)"), "large": ("Largest 100", "أكبر 100 شركة"),
        "sp500": ("S&P 500 (all, slower)", "إس آند بي 500 (كامل، أبطأ)"), "custom": ("My symbols", "رموزي")}
PROFILES = {"risk_controlled": ("Risk-controlled", "مضبوط المخاطر"), "return_seeking": ("Return-seeking · higher risk", "استهداف عائد أعلى · مخاطرة أكبر")}
RISK_FLAG = {"stale_data": ("history", "Stale data", "بيانات قديمة"), "extreme_volatility": ("bolt", "Extreme volatility", "تذبذب شديد"),
             "illiquid": ("water_drop", "Illiquid", "سيولة ضعيفة"), "earnings": ("event", "Earnings soon", "أرباح قريبة"),
             "extended": ("height", "Stretched", "ممتد"), "thin": ("water_drop", "Thin trading", "سيولة ضعيفة")}
N_CARDS = 8
# The S&P 500 holds 503 shares (some companies list two classes), so the cap sits above it.
MAX_SCAN = 600

CSS = f"""<style>
.hnreg.v3 {{ grid-template-columns:repeat(4,1fr); }}
@media (max-width: 1000px) {{ .hnreg.v3 {{ grid-template-columns:1fr 1fr; }} }}
.hnreg .tl.pass {{ border-color:{_U}66; background:linear-gradient(135deg,rgba(34,197,94,.14),{T.CARD}); }}
.hnreg .tl.fall {{ border-color:{_G}66; background:linear-gradient(135deg,rgba(245,185,74,.13),{T.CARD}); }}
.hnc .ft .c.al {{ color:#E8FFF0; background:rgba(34,197,94,.14); border-color:transparent; }}
.hnc .ft .c.al.dn {{ color:#FFE4E6; background:rgba(239,68,68,.14); }}
.hnparts .r.al .bar i {{ background:linear-gradient(90deg,{_C},{_U}); }}
.hnparts .r.q .bar i {{ background:linear-gradient(90deg,{_V},{_C}); }}
.v3alloc {{ display:flex; flex-direction:column; gap:6px; margin-top:10px; }}
.v3alloc .check {{ display:flex; gap:9px; align-items:center; font-size:.84rem; color:#DDD9E2; padding:6px 0; border-bottom:1px solid rgba(157,151,165,.12); }}
.v3alloc .check b {{ color:#fff; direction:ltr; unicode-bidi:isolate; }}
.v3alloc .check:last-child {{ border-bottom:0; }}
</style>"""


# ---------------------------------------------------------------- what to scan
def _symbols(choice, custom):
    if choice == "core":
        return DEFAULT
    if choice == "large":
        return tuple(dict.fromkeys(list(U.STOCKS)[:100]))
    if choice == "sp500":
        return tuple(SP500)
    out = [s.strip().upper() for s in str(custom or "").replace(";", ",").split(",")]
    return tuple(dict.fromkeys(x for x in out if x and len(x) < 12))


@st.cache_data(ttl=900, show_spinner=False, max_entries=6)
def _research(symbols):
    # All inputs on last completed daily bars, not real-time prices.
    prices = PB.load_prices(list(symbols), "3y")
    bench = data.history("SPY", "3y")
    sectors = {s: U.sector_of(s) for s in symbols}
    frame, fit, overview = V3.scan(prices, bench, sectors=sectors)
    vix = data.history("^VIX", "6mo")
    reg = H.regime(frame, bench, vix) if len(frame) else {}
    reg["mood"] = overview.get("mood", reg.get("mood", "mixed"))
    return frame, fit, overview, prices, reg


def _init():
    for k, v in {"v3_uni": "core", "v3_custom": "AAPL, MSFT, NVDA, AMZN", "v3_cap": 100_000.0, "v3_risk": .5, "v3_maxpos": 5,
                 "v3_seclim": 2, "v3_profile": "risk_controlled", "v3_grade": "all", "v3_clean": False, "v3_alpha": False,
                 "v3_fresh": False}.items():
        ss.setdefault(k, v)


def _go():
    ss["v3_run"] = _symbols(ss.get("v3_uni"), ss.get("v3_custom"))
    ss["v3_sel"] = None


def _as_v1(frame):
    """The V3 frame with its rank in the hunter's Score / Grade columns, for the hunter's drawings (radar, map, sectors)."""
    f = frame.copy()
    f["Score"] = f["Rank"].astype(float)
    f["Grade"] = f["Score"].map(H.grade)
    return f


# ---------------------------------------------------------------- hero
def hero_html(frame, fit, market, label):
    chips = []
    if frame is not None and len(frame):
        active = fit.get("status") == "active"
        chips.append(f'<span class="chip">{T.icon("radar")}{L("Scanned", "تم فحص")} <b>{market.get("universe", 0):,}</b> · {T.esc(label)}</span>')
        chips.append(f'<span class="chip">{T.icon("target")}{L("Eligible opportunities", "الفرص المؤهلة")} <b>{market.get("eligible_longs", 0)}</b></span>')
        chips.append(f'<span class="chip">{T.icon("psychology")}{L("Model", "النموذج")} <b>{L("validated", "مُعتمد") if active else L("fallback", "بديل")}</b></span>')
        chips.append(f'<span class="chip">{T.icon("bolt")}{L("New today", "جديدة اليوم")} <b>{int((frame["Status"] == "fresh").sum())}</b></span>')
        chips.append(f'<span class="chip">{T.icon("schedule")}{L("Last data", "آخر بيانات")} <b>{T.esc(str(market.get("date", "—")))}</b></span>')
    tag = L("The hunter's exact setups with a second scoring layer: a ridge model, validated on a purged chronological holdout, forecasts "
            "each stock's 20-session return over SPY; the rank blends the V1 score, technical quality and that forecast. "
            "Research and paper trading only.",
            "نفس فرص الصياد بشروطها الدقيقة مع طبقة ترتيب ثانية: نموذج إحصائي، مُختبر على فترة تاريخية مستقلة، يتوقع عائد كل سهم "
            "الزائد على المؤشر خلال 20 جلسة، والترتيب يجمع تقييم الصياد والجودة الفنية والتوقع. أبحاث وتداول افتراضي فقط.")
    res = _as_v1(frame) if frame is not None and len(frame) else None
    return (f'<div class="hnhero{" rtl" if is_ar() else ""}"><div class="grid"></div><div class="art">{S._radar(res, is_ar())}</div>'
            f'<div class="txt"><div class="eb">{T.icon("query_stats")}{L("Alpha Lab · quant research", "مختبر ألفا · بحث كمي")}</div>'
            f'<div class="t">{L("Hunter <b>V3</b>", "الصياد <b>V3</b>")}</div><div class="tg">{T.esc(tag)}</div>'
            f'<div class="chips">{"".join(chips)}</div><div class="st">{T.market_status(is_ar(), "us")}</div></div></div>')


# ---------------------------------------------------------------- the hunt bar
def hunt_bar():
    with st.container(key="hnbar_v3"):
        c = st.columns([1.9, 2.6, 1.1], vertical_alignment="bottom")
        c[0].selectbox(L("What to scan", "وش أفحص"), list(UNIS), key="v3_uni", format_func=lambda k: L(*UNIS[k]))
        if ss.get("v3_uni") == "custom":
            c[1].text_input(L("Symbols (comma separated)", "الرموز (مفصولة بفاصلة)"), key="v3_custom", placeholder="AAPL, MSFT, NVDA")
        else:
            n = len(_symbols(ss.get("v3_uni"), ""))
            note = L(f"{n:,} US stocks · daily bars · 3 years of history.", f"{n:,} سهم أمريكي · شموع يومية · 3 سنوات تاريخ.")
            if ss.get("v3_uni") == "sp500":
                note += L(" The whole S&P 500 takes a minute or two the first time, then it is kept for 15 minutes.",
                          " إس آند بي 500 كامل ياخذ دقيقة أو دقيقتين أول مرة، وبعدها ينحفظ 15 دقيقة.")
            c[1].caption(note)
        c[2].button(L("Run V3", "شغّل V3"), icon=":material/radar:", key="hn_go_v3", on_click=_go, width="stretch")
        d = st.columns([1.3, 1.2, 1, 1, 1.9], vertical_alignment="bottom")
        d[0].number_input(L("Paper capital ($)", "رأس مال افتراضي ($)"), min_value=1_000., max_value=10_000_000., step=10_000., key="v3_cap")
        d[1].slider(L("Risk budget / trade", "مخاطرة الصفقة"), min_value=.1, max_value=2.0, step=.1, format="%.1f%%", key="v3_risk")
        d[2].slider(L("Max holdings", "الحد الأقصى للمراكز"), 1, 15, key="v3_maxpos")
        d[3].slider(L("Max names / sector", "الحد الأقصى لكل قطاع"), 1, 6, key="v3_seclim")
        d[4].segmented_control(L("Paper allocation profile", "نوع المحفظة الافتراضية"), list(PROFILES), key="v3_profile",
                               format_func=lambda k: L(*PROFILES[k]))
        if not ss.get("v3_profile"):
            ss["v3_profile"] = "risk_controlled"


# ---------------------------------------------------------------- the model's state
def model_html(fit, market):
    active = fit.get("status") == "active"
    ic = fit.get("holdout_ic")
    ic_s = f"{float(ic):+.3f}" if ic is not None and np.isfinite(float(ic)) else "—"
    mood = market.get("mood", "mixed")
    expo = {"on": 100, "mixed": 65, "off": 25}.get(mood, 65)
    if ss.get("v3_profile") == "return_seeking":
        expo = 100 if mood in ("on", "mixed") else 70
    tiles = [
        f'<div class="tl {"pass" if active else "fall"}"><div class="l">{T.icon("verified" if active else "warning")}{L("Model validation", "حالة النموذج")}</div>'
        f'<div class="v">{L("Validated", "مُعتمد") if active else L("Fallback", "ترتيب بديل")}</div>'
        f'<div class="s">{L("the forecast is on: it beat its baseline on the holdout", "التوقع شغّال: تفوق على مرجعه في فترة التحقق") if active else L("the forecast is off: a transparent rank without predictions", "التوقع متوقف: ترتيب شفاف بدون توقعات")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("dataset")}{L("Training samples", "عينات التدريب")}</div><div class="v">{int(fit.get("n", 0) or 0):,}</div>'
        f'<div class="s">{L("labeled outcomes, 20 sessions ahead", "نتائج معلومة، 20 جلسة للأمام")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("insights")}{L("Validation IC", "ارتباط التحقق")}</div><div class="v">{ic_s}</div>'
        f'<div class="s">{L("forecast vs realized, out of sample · benchmark SPY", "التوقع مقابل الفعلي خارج العينة · المؤشر SPY")}</div></div>',
        f'<div class="tl"><div class="l">{T.icon("shield")}{L("Exposure cap", "حد الانكشاف")}</div><div class="v">{expo}%</div>'
        f'<div class="s">{L("of the paper capital, from the market mood and the profile", "من رأس المال الافتراضي، حسب مزاج السوق ونوع المحفظة")}</div></div>']
    return '<div class="hnreg v3">' + "".join(tiles) + "</div>"


# ---------------------------------------------------------------- filters
def filters(frame, fit):
    counts = frame["Setups"].str.split(",").explode().value_counts()
    keys = [k for k in H.ORDER if counts.get(k, 0)]
    if "v3_setups" in ss:
        ss["v3_setups"] = [k for k in ss["v3_setups"] if k in keys]
    with st.container(key="hnfilt_v3"):
        ui.html(f'<div class="hnfh">{T.icon("filter_alt")}<b>{L("Filters", "التصفية")}</b>'
                f'<span>{L("Pick setups to see only them; with none picked, every eligible long shows.", "اختر فرص عشان تشوفها بس؛ وبدون اختيار تظهر كل الفرص المؤهلة.")}</span></div>')
        st.pills(L("Setups", "الفرص"), keys, selection_mode="multi", key="v3_setups", label_visibility="collapsed",
                 format_func=lambda k: f"{S.short_name(k)} · {int(counts.get(k, 0))}")
        c = st.columns([1.55, 1, 1.15, 1], vertical_alignment="bottom")
        c[0].segmented_control(L("Rank at least", "الترتيب على الأقل"), list(S.MIN_GRADE), key="v3_grade",
                               format_func=lambda g: L("All", "الكل") if g == "all" else f"{g} · {S.MIN_GRADE[g]}")
        c[1].toggle(L("New today", "الجديدة اليوم"), key="v3_fresh")
        c[2].toggle(L("No risk flags", "بدون تحذيرات"), key="v3_clean")
        c[3].toggle(L("With a forecast", "مع توقع"), key="v3_alpha", disabled=fit.get("status") != "active")


def apply(frame):
    v = frame[(frame["Side"] > 0) & (frame["Rank"] >= 50)].copy()
    picks = ss.get("v3_setups") or []
    if picks:
        v = v[v["Setups"].apply(lambda s: any(k in str(s).split(",") for k in picks))]
    v = v[v["Rank"] >= S.MIN_GRADE.get(ss.get("v3_grade") or "all", 0)]
    if ss.get("v3_fresh"):
        v = v[v["Status"] == "fresh"]
    if ss.get("v3_clean"):
        v = v[~v["Risk Flag"].astype(str).str.contains("illiquid|stale_data|extreme_volatility", na=False)]
    if ss.get("v3_alpha"):
        v = v[v["Alpha %"].notna()]
    return v.sort_values(["Rank", "V1 Score"], ascending=False)


# ---------------------------------------------------------------- cards
def _flags(r):
    out = []
    for f in [x for x in str(r.get("Risk Flag") or "").split(",") if x]:
        ic, en, ar_ = RISK_FLAG.get(f, ("flag", f, f))
        out.append((ic, L(en, ar_)))
    return out


def _spark(prices, sym):
    d = prices.get(sym)
    return d["Close"].tail(63).tolist() if d is not None and "Close" in d else []


def card(r, prices, selected):
    sym, k = r["Symbol"], r["Setup"]
    ic = H.SETUPS[k][2] if k in H.SETUPS else "radar"
    entry, stop, tgt = r["Entry"], r["Stop"], r["Target"]
    rank = float(r["Rank"])
    top = (f'<div class="top"><span class="su">{T.icon(ic)}<span class="tx">{T.esc(S.short_name(k))}</span></span>'
           f'{S.status_tag(r["Status"], r["Age"])}</div>')
    go_ = L(f"Open the {T.sym_label(sym)} page", f"افتح صفحة {T.sym_label(sym)}")
    chg = r.get("Chg %")
    px = ""
    if np.isfinite(r["Price"]):
        pill = f'<i class="{"up" if chg >= 0 else "dn"}">{chg:+.2f}%</i>' if chg is not None and np.isfinite(chg) else ""
        px = f'<div class="px"><b>{S._money_px(r["Price"])}</b>{pill}</div>'
    hd = (f'<div class="hd"><a class="co" href="{T.esc(ui.href(sym))}" target="_self" title="{T.esc(go_)}">{T.logo_obj(sym, 36)}'
          f'<div class="nm"><b>{T.esc(T.sym_label(sym))}</b><span>{T.esc(T.name_line(sym, str(r["Name"])))}</span>{px}</div></a>'
          f'{S.ring(rank, H.grade(rank))}</div>')
    sp = f'<div class="spk">{S.spark(_spark(prices, sym), entry, stop, tgt, S._key(sym))}</div>'
    watch = r["Status"] == "watch"
    lv = (f'<div class="lv"><div><span>{L("Buy above", "شراء فوق") if watch else L("Entry", "الدخول")}</span><b>{S._money_px(entry)}</b></div>'
          f'<div><span>{L("Stop", "الوقف")}</span><b>{S._money_px(stop)}</b><i class="dn">{S._pct(entry, stop):+.1f}%</i></div>'
          f'<div><span>{L("Target", "الهدف")}</span><b>{S._money_px(tgt)}</b><i class="up">{S._pct(entry, tgt):+.1f}%</i></div></div>') if np.isfinite(entry) else ""
    alpha = r["Alpha %"]
    v1 = float(r["V1 Score"])
    mt = (f'<div class="mt"><div><span>{L("V1 score", "تقييم الصياد")}</span><b style="color:{S.GRADE_COLOR.get(H.grade(v1), _C)}">{v1:.0f}</b></div>'
          f'<div><span>{L("Forecast 20d", "توقع 20 جلسة")}</span><b style="color:{"#4ADE80" if pd.notna(alpha) and alpha >= 0 else "#F87171" if pd.notna(alpha) else _MU}">'
          f'{f"{alpha:+.1f}%" if pd.notna(alpha) else "—"}</b></div>'
          f'<div><span>{L("Volatility", "التذبذب")}</span><b>{r["ATR %"]:.1f}%</b></div></div>')
    chips = [f'<span class="c">RS <b>{int(r["RS"])}</b></span>']
    if np.isfinite(r["R:R"]):
        chips.append(f'<span class="c">R:R <b>{r["R:R"]:.1f}</b></span>')
    for ic_, txt in _flags(r):
        chips.insert(0, f'<span class="c w">{T.icon(ic_)}{T.esc(txt)}</span>')
    return f'<div class="card hnc{" sel" if selected else ""}">{top}{hd}{sp}{mt}{lv}<div class="ft">{"".join(chips)}</div></div>'


def _pick(sym):
    ss["v3_sel"] = sym


def cards(view, prices):
    top = view.head(N_CARDS)
    sel = ss.get("v3_sel")
    rows = list(top.iterrows())
    for i in range(0, len(rows), 4):
        cols = st.columns(4)
        for col, (_, r) in zip(cols, rows[i:i + 4]):
            with col:
                with st.container(key=f"hncard_v3_{S._key(r['Symbol'])}"):
                    ui.html(card(r, prices, r["Symbol"] == sel))
                    st.button(r["Symbol"], key=f"hn_pick_v3_{S._key(r['Symbol'])}", on_click=_pick, args=(r["Symbol"],), width="stretch")


# ---------------------------------------------------------------- the opened opportunity
def detail(r, prices, market, fit, selected, alloc):
    sym, k = r["Symbol"], r["Setup"]
    rank, v1, alpha = float(r["Rank"]), float(r["V1 Score"]), r["Alpha %"]
    with st.container(key=f"hnsec_v3_head_{S._key(sym)}"):
        badges = T.badge(sector_name(r["Sector"]) if r["Sector"] else "—", "gold", "category")
        badges += T.badge(f'{L("V1", "الصياد")} {H.grade(v1)} · {v1:.0f}', "acc", "radar")
        if k in H.SETUPS and r["Status"] in H.STATUS:
            badges += T.badge(S.setup_name(k) + " · " + L(*H.STATUS[r["Status"]][:2]), H.STATUS[r["Status"]][2], H.SETUPS[k][2])
        for ic_, txt in _flags(r):
            badges += T.badge(txt, "gold", ic_)
        nm_ = T.sym_label(sym)
        ui.html(f'<div class="card hndh"><a class="co" href="{T.esc(ui.href(sym))}" target="_self" title="{T.esc(L(f"Open the {nm_} page", f"افتح صفحة {nm_}"))}">'
                f'{T.logo_obj(sym, 48)}<div class="nm"><b>{T.esc(nm_)}</b><span>{T.esc(T.name_line(sym, str(r["Name"])))}</span></div></a>'
                f'{S.ring(rank, H.grade(rank), 62)}<div class="bd">{badges}</div>'
                f'<div class="px"><b>{S._money_px(r["Price"])}</b>{T.pill(r["Chg %"])}</div></div>')
        if k in H.SETUPS:
            ui.html(f'<div class="hnnote" style="margin-top:10px">{T.icon(H.SETUPS[k][2], _C)} <b>{T.esc(S.setup_name(k))}:</b> '
                    f'{T.esc(L(H.SETUPS[k][6], H.SETUPS[k][7]))}</div>')

    d = prices.get(sym)
    with st.container(key=f"hnsec_v3_body_{S._key(sym)}"):
        left, right = st.columns([1.7, 1], gap="medium")
        with left:
            if d is not None and len(d) > 20:
                levels = ([(L("Entry", "دخول"), r["Entry"], _A, "solid"), (L("Stop", "وقف"), r["Stop"], _D, "dash"),
                           (L("Target", "هدف"), r["Target"], _U, "dash")] if np.isfinite(r["Entry"]) else None)
                dd = d.dropna(subset=["Close"]).tail(190)
                ui.chart(charts.price_chart(dd, "Candles", [], [], False, levels=levels, height=430), key=f"hn_chart_v3_{S._key(sym)}")
            k4 = st.columns(4)
            k4[0].metric(L("V3 rank", "ترتيب V3"), f"{rank:.1f}/100")
            k4[1].metric(L("Hunter V1 score", "تقييم الصياد V1"), f"{v1:.1f}/100")
            k4[2].metric(L("Forecast 20d excess", "العائد الزائد المتوقع 20 جلسة"), f"{alpha:+.2f}%" if pd.notna(alpha) else "—")
            k4[3].metric(L("Reward / Risk", "العائد / المخاطرة"), f"{r['R:R']:.2f}" if pd.notna(r["R:R"]) else "—")
        with right:
            ui.sec("donut_large", "Why this rank", "ليش هالترتيب")
            q = V3._technical_quality(r, market.get("mood", "mixed"))
            if pd.notna(alpha):
                parts = [("", L("Hunter V1 score", "تقييم الصياد V1"), 55, v1), ("q", L("Technical quality", "الجودة الفنية"), 20, q),
                         ("al", L("Forecast", "التوقع"), 25, float(np.clip(50 + 3 * alpha, 0, 100)))]
            else:
                parts = [("", L("Hunter V1 score", "تقييم الصياد V1"), 75, v1), ("q", L("Technical quality", "الجودة الفنية"), 25, q)]
            ui.html('<div class="hnparts">' + "".join(
                f'<div class="r {c_}"><span>{T.esc(l_)} <span class="w">· {w}%</span></span>'
                f'<div class="bar"><i style="width:{float(v):.0f}%"></i></div><b>{float(v):.0f}</b></div>' for c_, l_, w, v in parts) + "</div>")
            capped = str(r["Risk Flag"] or "") or (r["Side"] <= 0)
            if capped:
                st.caption(L("A risk flag (or no buying setup) caps the rank at 49.", "تحذير المخاطر (أو غياب فرصة شراء) يحدّ الترتيب عند 49."))
            line = selected[selected["Symbol"] == sym] if len(selected) else pd.DataFrame()
            if len(line):
                a = line.iloc[0]
                items = [("inventory_2", f'{L("Shares", "الأسهم")}: <b>{int(a["Shares"]):,}</b>'),
                         ("payments", f'{L("Notional", "القيمة")}: <b>{T.money(a["Notional"])}</b> · {a["Weight %"]:.1f}% {L("of the capital", "من رأس المال")}'),
                         ("shield", f'{L("Risk at the stop", "الخسارة عند الوقف")}: <b>{T.money(a["Stop Risk $"])}</b>')]
                chip = S.score_chip(L("in the plan", "ضمن الخطة"), True)
            else:
                items = [("do_not_disturb_on", L("Not in the paper allocation: the rank, a risk flag, the sector limit, the position cap or the cash left it out.",
                                                 "خارج المحفظة الافتراضية: الترتيب أو تحذير المخاطر أو حد القطاع أو حد المراكز أو النقد المتبقي استبعدوه."))]
                chip = S.score_chip(L("not in the plan", "خارج الخطة"), False)
            ui.html(f'<div class="hnbox" style="margin-top:12px"><div class="hnbt">{T.icon("account_balance_wallet")}<span>{L("Paper allocation", "المحفظة الافتراضية")}</span>{chip}</div>'
                    f'<div class="v3alloc">' + "".join(f'<div class="check">{T.ico(ic, "acc")}<div>{t}</div></div>' for ic, t in items) + "</div></div>")
    if np.isfinite(r["Entry"]) and int(r["Side"] or 0) > 0:
        with st.container(key=f"hnsec_v3_plan_{S._key(sym)}"):
            ui.sec("flag", "Setup levels", "مستويات الفرصة")
            entry, stop, tgt = float(r["Entry"]), float(r["Stop"]), float(r["Target"])
            watch = r["Status"] == "watch"
            tiles = [("en", L("Buy above", "شراء فوق") if watch else L("Entry", "الدخول"), S._money_px(entry),
                      L("on a close above it", "بإغلاق فوقه") if watch else L("next open, near this price", "الافتتاح القادم، قرب هذا السعر")),
                     ("sl", L("Stop loss", "وقف الخسارة"), S._money_px(stop), f"{S._pct(entry, stop):+.1f}%"),
                     ("tp", L("Target", "الهدف"), S._money_px(tgt), f"{S._pct(entry, tgt):+.1f}%"),
                     ("", "R:R", f"{r['R:R']:.1f} : 1" if np.isfinite(r["R:R"]) else "—", L("reward for each 1 of risk", "العائد لكل 1 مخاطرة")),
                     ("", "ATR (14)", f"{r['ATR %']:.1f}%", L("a day", "يومياً")),
                     ("", L("Traded a day", "التداول اليومي"), T.money(r["$Vol"], short=True), L("dollar volume", "قيمة التداول"))]
            ui.html('<div class="hnplan">' + "".join(f'<div class="p {c_}"><div class="l">{T.esc(l_)}</div><div class="v">{v_}</div>'
                                                     f'<div class="s">{T.esc(s_)}</div></div>' for c_, l_, v_, s_ in tiles) + "</div>")


# ---------------------------------------------------------------- allocation and the table
def allocation(selected, allocations, profile):
    ui.sec("account_balance_wallet", "Hypothetical allocation · no live orders", "محفظة افتراضية · بدون أوامر حقيقية")
    tiles = [("en", L("Invested", "نسبة الاستثمار"), f"{allocations['invested_pct']:.1f}%", L("of the paper capital", "من رأس المال الافتراضي")),
             ("", L("Cash", "النقد"), T.money(allocations["remaining_cash"]), L("left after sizing", "المتبقي بعد التوزيع")),
             ("", L("Exposure limit", "حد الانكشاف"), f"{allocations['market_exposure_cap_pct']:.0f}%", L("from the mood and the profile", "حسب مزاج السوق ونوع المحفظة")),
             ("tp", L("Positions", "المراكز"), f"{allocations['positions']}", L(*PROFILES[profile]))]
    ui.html('<div class="hnplan">' + "".join(f'<div class="p {c_}"><div class="l">{T.esc(l_)}</div><div class="v">{v_}</div>'
                                             f'<div class="s">{T.esc(s_)}</div></div>' for c_, l_, v_, s_ in tiles) + "</div>")
    if len(selected):
        show = selected.copy()
        show["Sector"] = show["Sector"].map(lambda s: sector_name(s) if s else "—")
        N = {"Symbol": L("Symbol", "الرمز"), "Sector": L("Sector", "القطاع"), "Shares": L("Shares", "الأسهم"), "Entry": L("Entry", "الدخول"),
             "Stop": L("Stop", "الوقف"), "Notional": L("Notional ($)", "القيمة ($)"), "Weight %": L("Weight %", "الوزن %"),
             "Stop Risk $": L("Risk at stop ($)", "الخسارة عند الوقف ($)"), "Alpha %": L("Forecast %", "التوقع %"), "Rank": L("Rank", "الترتيب")}
        show = show.rename(columns=N)
        ui.table(show, sym=N["Symbol"], cell={N["Rank"]: lambda v, r: ui.score_bar(v)}, signed={N["Alpha %"]},
                 fmt={N["Shares"]: "{:,.0f}", N["Entry"]: "{:,.2f}", N["Stop"]: "{:,.2f}", N["Notional"]: "{:,.0f}", N["Weight %"]: "{:.1f}%",
                      N["Stop Risk $"]: "{:,.0f}", N["Alpha %"]: "{:+.2f}%"})
    else:
        st.info(L("No positions meet sizing and risk constraints today.", "ما فيه مراكز تستوفي شروط الحجم والمخاطرة اليوم."), icon=":material/info:")
    if profile == "return_seeking":
        st.warning(L("Return-seeking mode can stay substantially exposed in bear markets. Higher exposure can amplify losses; it is not a higher-return guarantee.",
                     "وضع استهداف العائد قد يحتفظ بانكشاف كبير حتى بالسوق الهابط، وقد يضاعف الخسائر ولا يضمن عائدًا أعلى."), icon=":material/warning:")
    st.caption(L("Stop prices may gap through; modeled risk budgets cannot cap realized losses. Prices may be delayed. No auto orders, derivatives or leverage.",
                 "قد ينفذ وقف الخسارة بسعر أسوأ عند وجود فجوة. تحديد المخاطرة لا يضمن سقفًا للخسارة. الأسعار قد تتأخر، ولا يوجد تداول فعلي أو مشتقات أو رافعة."))


def table(frame):
    cols = ["Symbol", "Name", "Sector", "Rank", "V1 Score", "Alpha %", "Setup", "Status", "Price", "Chg %", "Entry", "Stop", "Target", "R:R", "ATR %", "$Vol", "Risk Flag"]
    show = frame[cols].copy()
    show["Sector"] = show["Sector"].map(lambda s: sector_name(s) if s else "—")
    show["Setup"] = show["Setup"].map(S.setup_name)
    show["Status"] = show["Status"].map(lambda s: L(*H.STATUS[s][:2]) if s in H.STATUS else "—")
    show["Risk Flag"] = show["Risk Flag"].map(lambda s: " · ".join(L(*RISK_FLAG[f][1:]) if f in RISK_FLAG else f for f in str(s or "").split(",") if f) or "—")
    N = {"Symbol": L("Symbol", "الرمز"), "Name": L("Company", "الشركة"), "Sector": L("Sector", "القطاع"), "Rank": L("V3 rank", "ترتيب V3"),
         "V1 Score": L("V1 score", "تقييم الصياد"), "Alpha %": L("Forecast %", "التوقع %"), "Setup": L("Setup", "الفرصة"), "Status": L("Status", "الحالة"),
         "Price": L("Price", "السعر"), "Chg %": L("Chg %", "التغير %"), "Entry": L("Entry", "الدخول"), "Stop": L("Stop", "الوقف"), "Target": L("Target", "الهدف"),
         "R:R": "R:R", "ATR %": L("ATR %", "التذبذب %"), "$Vol": L("Traded/day ($)", "التداول اليومي ($)"), "Risk Flag": L("Risk flags", "تحذيرات")}
    show = show.rename(columns=N)
    ui.table(show, sym=N["Symbol"], height=600, pills={N["Chg %"]}, signed={N["Alpha %"]}, wrap={N["Risk Flag"]},
             cell={N["Rank"]: lambda v, r: ui.score_bar(v), N["V1 Score"]: lambda v, r: ui.score_bar(v)},
             fmt={N["Alpha %"]: "{:+.2f}%", N["Price"]: "{:,.2f}", N["Chg %"]: "{:+.2f}%", N["Entry"]: "{:,.2f}", N["Stop"]: "{:,.2f}",
                  N["Target"]: "{:,.2f}", "R:R": "{:.1f}", N["ATR %"]: "{:.1f}%", N["$Vol"]: lambda v: T.money(v, short=True)})
    st.download_button(L("Export V3 research CSV", "تصدير نتائج V3"), data=frame.to_csv(index=False).encode("utf-8-sig"),
                       file_name="tura-hunter-v3-research.csv", mime="text/csv", icon=":material/download:", key="v3_csv")


# ---------------------------------------------------------------- page
def page_hunter_v3():
    ui.html(S.CSS + (S.RTL_CSS if is_ar() else "") + CSS)
    _init()
    symbols = ss.get("v3_run")
    got = None
    if symbols:
        if len(symbols) > MAX_SCAN:
            st.error(L(f"Limit scans to {MAX_SCAN} symbols.", f"الحد الأقصى للفحص {MAX_SCAN} سهم."))
        else:
            with st.spinner(L(f"Loading {len(symbols)} stocks and validating the alpha model...",
                              f"جاري قراءة أسعار {len(symbols)} سهم وتدريب النموذج والتحقق منه...")):
                try:
                    got = _research(symbols)
                except Exception as exc:
                    st.error(L(f"Scan failed: {type(exc).__name__}: {exc}", f"تعذّر الفحص: {type(exc).__name__}: {exc}"))
    frame, fit, market, prices, reg = got if got else (pd.DataFrame(), {}, {}, {}, {})
    label = L(*UNIS.get(ss.get("v3_uni"), UNIS["core"]))
    ui.html(hero_html(frame, fit, market, label))
    hunt_bar()
    if not symbols:
        st.info(L("Choose your universe, then run the V3 scan. Hunter V1 remains untouched.", "اختر الأسهم ثم شغّل الصياد V3. الصياد القديم ما يتغير."),
                icon=":material/info:")
        ui.foot()
        return
    if symbols != _symbols(ss.get("v3_uni"), ss.get("v3_custom")):
        st.caption(L("The settings changed since the last run: press Run V3 to scan the new list.",
                     "الإعدادات تغيرت بعد آخر تشغيل: اضغط «شغّل V3» عشان تفحص القائمة الجديدة."))
    if got is None:
        ui.foot()
        return
    if frame.empty:
        st.warning(L("No valid completed-bar setups for this universe.", "ما فيه فرص مكتملة مؤهلة بهذه القائمة."), icon=":material/search_off:")
        ui.foot()
        return
    if fit.get("status") != "active":
        st.warning(L("The forecasting model did not beat its historical validation baseline (or data were insufficient). "
                     "V3 uses a transparent, non-predictive ranking fallback and leaves the forecast blank.",
                     "النموذج التنبؤي ما تفوق على مرجعه في التحقق التاريخي (أو البيانات ناقصة). "
                     "V3 يستخدم ترتيبًا بديلًا بدون توقعات، ويترك خانة التوقع فارغة."), icon=":material/warning:")
    with st.container(key="hnsec_v3_mood"):
        ui.safe(lambda: ui.html(S.mood_html(reg)))
        ui.safe(lambda: ui.html(model_html(fit, market)))
        st.caption(L(f"Last market data: {market.get('date', '—')} · training samples: {fit.get('n', 0)} · validation IC: {fit.get('holdout_ic', '—')} · benchmark: SPY",
                     f"آخر بيانات: {market.get('date', '—')} · عينات التدريب: {fit.get('n', 0)} · ارتباط التحقق: {fit.get('holdout_ic', '—')} · المؤشر: SPY"))
    with st.container(key="hnsec_v3_filters"):
        ui.safe(filters, frame, fit)
    view = apply(frame)
    profile = ss.get("v3_profile") or "risk_controlled"
    selected, allocations = V3.allocate(frame, capital=float(ss["v3_cap"]), risk_per_trade_pct=float(ss["v3_risk"]),
                                         max_positions=int(ss["v3_maxpos"]), sector_limit=int(ss["v3_seclim"]),
                                         mode=market.get("mood", "off"), profile=profile)
    if not view.empty:
        if ss.get("v3_sel") not in set(view["Symbol"]):
            ss["v3_sel"] = view["Symbol"].iloc[0]
        with st.container(key="hnsec_v3_cards"):
            ui.sec("target", f"Highest-ranked opportunities ({len(view)})", f"أعلى الفرص ترتيبًا ({len(view)})")
            ui.safe(cards, view, prices)
        r = view[view["Symbol"] == ss["v3_sel"]].iloc[0]
        ui.safe(detail, r, prices, market, fit, selected, allocations)
    else:
        with st.container(key="hnsec_v3_none"):
            st.info(L("Nothing matches these filters. Lower the rank, clear the setups, or scan a bigger universe.",
                      "ما فيه شي يطابق هالتصفية. نزّل الترتيب، أو شيل الفرص المختارة، أو افحص نطاق أكبر."), icon=":material/search_off:")
    with st.container(key="hnsec_v3_alloc"):
        ui.safe(allocation, selected, allocations, profile)
    with st.container(key="hnsec_v3_table"):
        ui.sec("table_rows", "Every result", "كل النتائج")
        ui.safe(table, frame)
    with st.container(key="hnsec_v3_charts"):
        v1 = _as_v1(frame)
        c1, c2 = st.columns([1.15, 1], gap="medium")
        with c1:
            ui.safe(lambda: ui.chart(charts.hunt_map(v1, L("Opportunity map: leaders sit top right", "خريطة الفرص: القادة فوق يمين"),
                                                     (L("From 52-week high %", "البعد عن القمة السنوية %"), L("RS rating (1-99)", "تقييم RS (1-99)"),
                                                      L("V3 rank", "ترتيب V3"))), key="hn_map_v3"))
        with c2:
            ui.safe(S.sector_chart, H.sectors(v1))
    with st.expander(L("Research methodology and limitations", "منهجية البحث والقيود"), icon=":material/help:"):
        ui.html('<div class="hnnote">' + L(
            "V3 scans the same deterministic long setups as V1, with a different scoring layer. The pooled ridge model predicts stock return "
            "less SPY return over the next 20 sessions, using only past-labeled outcomes, a purged chronological holdout, and a validation gate. "
            "If validation fails the predictor is deactivated. <b>The rank</b>: 55% the V1 score, 20% technical quality (reward-to-risk, "
            "volatility, distance from the high, the market mood) and 25% the forecast; without a forecast, 75% and 25%. A risk flag (stale data, "
            "extreme volatility, illiquid) or no buying setup caps it at 49. The allocation is long-only, cash-based, and scaled down in adverse "
            "regimes. No future return or win probability is guaranteed. This is NOT a verified profitable strategy and must be evaluated with a "
            "point-in-time universe and realistic walk-forward backtests before relying on it.",
            "V3 يستخدم نفس شروط فرص الشراء القديمة مع طبقة ترتيب جديدة. النموذج الإحصائي يتوقع عائد السهم الزائد على المؤشر خلال 20 جلسة، "
            "ويتدرب على نتائج معلومة تاريخيًا فقط مع فصل زمني واختبار تحقق مستقل، ويُعطّل إذا ما اجتاز الاختبار. <b>الترتيب</b>: 55% تقييم الصياد، "
            "و20% الجودة الفنية (العائد مقابل المخاطرة، والتذبذب، والبعد عن القمة، ومزاج السوق)، و25% التوقع؛ وبدون توقع 75% و25%. تحذير المخاطر "
            "(بيانات قديمة، تذبذب شديد، سيولة ضعيفة) أو غياب فرصة شراء يحدّه عند 49. المحفظة افتراضية وبدون اقتراض، وتقلل الانكشاف إذا ساءت حالة "
            "السوق. ما فيه ضمان للعائد أو دقة التنبؤ، ولازم اختبارات تاريخية أقوى قبل الاعتماد.") + "</div>")
    st.caption(L("US equities · daily bars from Yahoo Finance (may be delayed) · educational/paper research only · no brokerage execution.",
                 "أسهم أمريكية · شموع يومية من ياهو فاينانس (قد تكون متأخرة) · أبحاث وتداول افتراضي فقط · بدون تنفيذ حقيقي."))
    ui.foot()


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "23.4.45"
