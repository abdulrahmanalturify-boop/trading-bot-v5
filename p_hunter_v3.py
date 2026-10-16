"""TURA Hunter V3 Alpha Lab. Completely separate from Opportunity Hunter V1."""
import numpy as np
import pandas as pd
import streamlit as st

import data
import hunter_v3 as V3
import paperbots as PB
import universe as U
from i18n import L
from sp500 import SP500

BUILD = "v3-alpha-ui-20261016"
DEFAULT = (
    "AAPL", "MSFT", "NVDA", "AMD", "GOOGL", "META", "DIS",
    "JPM", "BAC", "WFC", "XOM", "CVX", "SLB", "UNH", "JNJ", "MRK",
    "AMZN", "HD", "MCD", "NKE", "WMT", "PG", "KO", "CAT", "DE",
    "UPS", "NEE", "DUK", "SO",
)
CSS = """
<style>
.v3-hero{background:linear-gradient(110deg,rgba(171,157,227,.13),rgba(124,203,222,.08));
 border:1px solid rgba(174,166,207,.25);border-radius:20px;padding:26px;margin-bottom:16px}
.v3-eyebrow{font-weight:700;letter-spacing:.15em;color:#a59bdc;font-size:.7rem}
.v3-head{font-size:clamp(1.7rem,4vw,2.55rem);font-weight:700;letter-spacing:-.04em;margin:.4rem 0}
.v3-desc{opacity:.72;max-width:740px;line-height:1.7}
</style>
"""


def _symbols(choice, custom):
    if choice == "Core 29":
        return DEFAULT
    if choice == "Large 100":
        return tuple(dict.fromkeys(list(U.STOCKS)[:100]))
    if choice == "S&P 500":
        return tuple(SP500)
    out = [s.strip().upper() for s in custom.replace(";", ",").split(",")]
    return tuple(dict.fromkeys(x for x in out if x and len(x) < 12))


@st.cache_data(ttl=900, show_spinner=False, max_entries=6)
def _research(symbols):
    # All inputs on last completed daily bars, not real-time prices.
    prices = PB.load_prices(list(symbols), "3y")
    bench = data.history("SPY", "3y")
    sectors = {s: U.sector_of(s) for s in symbols}
    frame, fit, overview = V3.scan(prices, bench, sectors=sectors)
    return frame, fit, overview, prices


def page_hunter_v3():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="v3-hero"><div class="v3-eyebrow">TURA · QUANT RESEARCH</div>'
                '<div class="v3-head">Hunter V3 · Alpha Lab</div>'
                '<div class="v3-desc">An independent experimental signal-ranking engine with '
                'chronologically validated forecasts, risk regime filters and a capped paper allocation plan.'
                '</div></div>', unsafe_allow_html=True)
    st.caption(L("US equities · daily bars · educational/paper research only · no brokerage execution.",
                 "أسهم أمريكية · شموع يومية · أبحاث وتداول افتراضي فقط · بدون تنفيذ حقيقي."))

    a, b, c = st.columns([1.2, 1.0, 2.0])
    choice = a.selectbox(L("Stock universe", "نطاق الأسهم"), ["Core 29", "Large 100", "S&P 500", "Custom"])
    cap = b.number_input(L("Paper capital ($)", "رأس مال افتراضي ($)"),
                         min_value=1_000., max_value=10_000_000., value=100_000., step=10_000.)
    custom = c.text_input(L("Custom symbols", "رموز مخصصة"), value="AAPL, MSFT, NVDA, AMZN",
                          disabled=choice != "Custom")
    d, e, f = st.columns(3)
    risk = d.slider(L("Risk budget / trade", "مخاطرة الصفقة"), min_value=.1, max_value=2.0,
                    value=.5, step=.1, format="%.1f%%")
    maxpos = e.slider(L("Max holdings", "الحد الأقصى للمراكز"), 1, 15, 5)
    sectorlim = f.slider(L("Max names / sector", "الحد الأقصى لكل قطاع"), 1, 6, 2)

    symbols = _symbols(choice, custom)
    if not symbols:
        st.info(L("Enter at least one US stock symbol.", "أدخل رمز سهم أمريكي واحد على الأقل."))
        return
    if len(symbols) > 500:
        st.error(L("Limit scans to 500 symbols.", "الحد الأقصى للفحص 500 سهم."))
        return
    if st.button(L(f"Run separate V3 scan ({len(symbols)} stocks)", f"تشغيل الصياد V3 بشكل مستقل ({len(symbols)} سهم)"),
                 icon=":material/radar:", type="primary", use_container_width=True):
        with st.spinner(L("Loading historical prices and validating the alpha model...",
                          "جاري قراءة الأسعار التاريخية وتدريب النموذج والتحقق منه...")):
            try:
                frame, fit, overview, prices = _research(symbols)
                st.session_state["tura_v3_scan"] = (frame, fit, overview, prices)
                st.session_state["tura_v3_symbols"] = symbols
            except Exception as exc:
                st.error(L(f"Scan failed: {type(exc).__name__}: {exc}",
                           f"تعذّر الفحص: {type(exc).__name__}: {exc}"))
                return

    result = st.session_state.get("tura_v3_scan")
    if result is None or st.session_state.get("tura_v3_symbols") != symbols:
        st.info(L("Choose your universe, then run the V3 scan. V1 remains untouched.",
                  "اختر الأسهم ثم شغّل الصياد V3. الصياد القديم ما يتغير."))
        return
    frame, fit, market, prices = result
    if frame.empty:
        st.warning(L("No valid completed-bar setups for this universe.", "ما فيه فرص مكتملة مؤهلة بهذه القائمة."))
        return

    model_active = fit.get("status") == "active"
    if not model_active:
        st.warning(L("The forecasting model did not beat its historical validation baseline (or data were insufficient). "
                     "V3 uses a transparent, non-predictive ranking fallback and leaves Alpha blank.",
                     "النموذج التنبؤي ما تفوق على مرجعه في التحقق التاريخي (أو البيانات ناقصة). "
                     "V3 يستخدم ترتيبًا بديلًا بدون توقعات، ويترك خانة Alpha فارغة."))
    k = st.columns(4)
    k[0].metric(L("Scanned", "الأسهم المفحوصة"), market.get("universe", 0))
    k[1].metric(L("Eligible opportunities", "الفرص المؤهلة"), market.get("eligible_longs", 0))
    k[2].metric(L("Market regime", "حالة السوق"), market.get("mood", "unknown").upper())
    k[3].metric(L("Model validation", "حالة النموذج"), "PASS" if model_active else "FALLBACK")
    st.caption(L(f"Last market data: {market.get('date', '—')} | training samples: {fit.get('n', 0)} | "
                 f"validation IC: {fit.get('holdout_ic', '—')} | benchmark: SPY",
                 f"آخر بيانات: {market.get('date', '—')} | عينات التدريب: {fit.get('n', 0)} | "
                 f"ارتباط التحقق: {fit.get('holdout_ic', '—')} | المؤشر: SPY"))

    st.subheader(L("Highest-ranked research opportunities", "أعلى فرص البحث الكمي"))
    good = frame[(frame["Side"] > 0) & (frame["Rank"] >= 50) &
                 ~frame["Risk Flag"].str.contains("illiquid|stale_data|extreme_volatility", na=False)].copy()
    showcols = ["Symbol", "Name", "Sector", "Rank", "V1 Score", "Alpha %", "Setup",
                "Status", "Entry", "Stop", "Target", "R:R", "ATR %", "$Vol", "Risk Flag"]
    st.dataframe(good[showcols] if len(good) else frame[showcols].head(30),
                 hide_index=True, use_container_width=True, height=460)
    st.download_button(L("Export V3 research CSV", "تصدير نتائج V3"),
                       data=frame.to_csv(index=False).encode("utf-8-sig"),
                       file_name="tura-hunter-v3-research.csv", mime="text/csv")

    st.subheader(L("Hypothetical allocation · no live orders", "محفظة افتراضية · بدون أوامر حقيقية"))
    selected, allocations = V3.allocate(frame, capital=cap, risk_per_trade_pct=risk,
                                         max_positions=maxpos, sector_limit=sectorlim,
                                         mode=market.get("mood", "off"))
    p1, p2, p3 = st.columns(3)
    p1.metric(L("Invested", "نسبة الاستثمار"), f"{allocations['invested_pct']:.1f}%")
    p2.metric(L("Cash", "النقد"), f"\${allocations['remaining_cash']:,.0f}")
    p3.metric(L("Exposure limit", "حد الانكشاف"), f"{allocations['market_exposure_cap_pct']:.0f}%")
    if len(selected):
        st.dataframe(selected, hide_index=True, use_container_width=True)
    else:
        st.info(L("No positions meet sizing and risk constraints today.",
                  "ما فيه مراكز تستوفي شروط الحجم والمخاطرة اليوم."))
    st.caption(L("Stop prices may gap through; modeled risk budgets cannot cap realized losses. "
                 "Prices may be delayed. No auto orders, derivatives or leverage.",
                 "قد ينفذ وقف الخسارة بسعر أسوأ عند وجود فجوة. تحديد المخاطرة لا يضمن سقفًا للخسارة. "
                 "الأسعار قد تتأخر، ولا يوجد تداول فعلي أو مشتقات أو رافعة."))

    st.subheader(L("Inspect one opportunity", "افحص فرصة بالتفصيل"))
    symbol = st.selectbox(L("Symbol", "السهم"), frame["Symbol"].tolist(), key="hunter_v3_symbol")
    r = frame.set_index("Symbol").loc[symbol]
    d = prices.get(symbol)
    if d is not None and len(d) > 20:
        st.line_chart(d[["Close"]].tail(160), height=265)
        q = st.columns(4)
        q[0].metric(L("V3 Rank", "ترتيب V3"), f"{r['Rank']:.1f}/100")
        q[1].metric(L("Old V1", "القديم V1"), f"{r['V1 Score']:.1f}/100")
        q[2].metric(L("Forecast 20d excess", "العائد الزائد المتوقع 20 جلسة"),
                    f"{r['Alpha %']:+.2f}%" if pd.notna(r["Alpha %"]) else "—")
        q[3].metric(L("Reward / Risk", "العائد / المخاطرة"),
                    f"{r['R:R']:.2f}" if pd.notna(r["R:R"]) else "—")
    with st.expander(L("Research methodology and limitations", "منهجية البحث والقيود")):
        st.write(L(
            "V3 scans the same deterministic long setups as V1, with a different scoring layer. "
            "The pooled ridge model predicts stock return less SPY return over the next 20 sessions, "
            "using only past-labeled outcomes, a purged chronological holdout, and a validation gate. "
            "If validation fails the predictor is deactivated. The allocation is long-only, cash-based, "
            "and scaled down in adverse regimes. No future return or win probability is guaranteed. "
            "This is NOT a verified profitable strategy and must be evaluated with a point-in-time universe "
            "and realistic walk-forward backtests before relying on it.",
            "V3 يستخدم نفس شروط فرص الشراء القديمة مع طبقة ترتيب جديدة. نموذج Ridge يتوقع عائد السهم "
            "الزائد على SPY خلال 20 جلسة. يتدرب على نتائج معلومة تاريخيًا فقط مع فصل زمني واختبار تحقق "
            "مستقل، ويُعطّل إذا ما اجتاز الاختبار. المحفظة افتراضية وبدون اقتراض، وتقلل الانكشاف إذا "
            "ساءت حالة السوق. ما فيه ضمان للعائد أو دقة التنبؤ، ولازم اختبارات تاريخية أقوى قبل الاعتماد."))
