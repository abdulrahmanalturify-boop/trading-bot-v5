"""
p_xbots.py - The X Bots page: five bots that read X (Twitter) about the market and trade what they read on paper (xbots.py).

The page only shows what the bots stored on their last run (scripts/xbots_run.py, every hour of their market's day): it never
reads X itself, so opening it costs nothing.
"""
import pandas as pd
import streamlit as st

import charts
import data
import markets as MK
import theme as T
import ui
import xbots as XB
from i18n import L, is_ar

ss = st.session_state

CSS = """<style>
.xbhero { display:flex; flex-wrap:wrap; gap:10px 18px; align-items:center; justify-content:space-between; padding:14px 18px; border-radius:18px;
  background:linear-gradient(135deg, rgba(59,139,235,.14), rgba(123,69,240,.12) 60%, rgba(26,22,36,.9)); border:1px solid rgba(167,139,250,.28); }
.xbhero .st { display:flex; align-items:center; gap:10px; font-weight:700; color:#fff; }
.xbhero .st i { width:10px; height:10px; border-radius:50%; background:#F5B94A; box-shadow:0 0 0 4px rgba(245,185,74,.18); }
.xbhero .st.on i { background:#34D27A; box-shadow:0 0 0 4px rgba(52,210,122,.18); animation:xbpulse 1.8s ease-in-out infinite; }
.xbhero .st.err i { background:#F26B6B; box-shadow:0 0 0 4px rgba(242,107,107,.18); }
@keyframes xbpulse { 50% { box-shadow:0 0 0 8px rgba(52,210,122,0); } }
.xbhero .facts { display:flex; flex-wrap:wrap; gap:6px 18px; color:#B9B3C4; font-size:.84rem; }
.xbhero .facts b { color:#fff; font-variant-numeric:tabular-nums; }
.xbg { display:grid; grid-template-columns:repeat(5, minmax(0,1fr)); gap:12px; margin-top:4px; }
@media (max-width: 1250px) { .xbg { grid-template-columns:repeat(3, minmax(0,1fr)); } }
@media (max-width: 760px) { .xbg { grid-template-columns:1fr; } }
.xbc { position:relative; display:flex; flex-direction:column; gap:8px; padding:14px; border-radius:18px; overflow:hidden; min-width:0;
  background:linear-gradient(160deg, rgba(36,28,58,.95), rgba(20,16,32,.95)); border:1px solid rgba(157,151,165,.22); }
.xbc::before { content:""; position:absolute; inset:0 0 auto 0; height:3px; background:linear-gradient(90deg,#5088F2,#DF4E92); opacity:.85; }
.xbc .hd { display:flex; align-items:center; gap:10px; }
.xbc .ic { flex:none; width:38px; height:38px; border-radius:12px; display:grid; place-items:center; color:#fff;
  background:linear-gradient(140deg,#3B8BEB,#7B45F0 70%,#A855F7); box-shadow:0 10px 22px -12px rgba(123,69,240,.9); }
.xbc .ic .ms { font-size:1.3rem; }
.xbc .nm { min-width:0; } .xbc .nm b { display:block; color:#fff; font-size:.95rem; line-height:1.25; }
.xbc .nm small { color:#8F899B; font-size:.72rem; }
.xbc .beat { color:#B9B3C4; font-size:.78rem; line-height:1.5; min-height:3em; }
.xbc .row { display:flex; justify-content:space-between; align-items:center; gap:8px; font-size:.8rem; color:#B9B3C4; }
.xbc .row b { color:#fff; font-variant-numeric:tabular-nums; }
.xbc .mood { display:flex; align-items:center; gap:8px; }
.xbc .mood .bar { flex:1; height:6px; border-radius:99px; background:rgba(255,255,255,.08); position:relative; overflow:hidden; }
.xbc .mood .bar i { position:absolute; top:0; bottom:0; border-radius:99px; }
.xbc .stt { font-size:.72rem; color:#8F899B; display:flex; align-items:center; gap:6px; }
.xbc .stt i { width:7px; height:7px; border-radius:50%; background:#F5B94A; }
.xbc .stt.on i { background:#34D27A; } .xbc .stt.err i { background:#F26B6B; }
.xpost { display:flex; flex-direction:column; gap:6px; padding:12px 14px; border-radius:14px; background:rgba(255,255,255,.03);
  border:1px solid rgba(157,151,165,.16); margin-bottom:8px; }
.xpost .who { display:flex; align-items:center; gap:8px; font-size:.82rem; color:#8F899B; flex-wrap:wrap; }
.xpost .who b { color:#fff; }
.xpost .tx { color:#E7E3EB; font-size:.9rem; line-height:1.6; white-space:pre-wrap; overflow-wrap:anywhere; }
.xpost .ft { display:flex; align-items:center; gap:8px; flex-wrap:wrap; font-size:.76rem; color:#8F899B; }
.xpost .tag { padding:2px 9px; border-radius:99px; font-weight:700; font-size:.72rem; border:1px solid currentColor; }
.xpost .tag.bull { color:#4ADE80; background:rgba(74,222,128,.08); } .xpost .tag.bear { color:#F87171; background:rgba(248,113,113,.08); }
.xpost .tag.neutral { color:#C4B5FD; background:rgba(167,139,250,.08); }
.xpost a.go { margin-inline-start:auto; color:#79B8F4 !important; text-decoration:none !important; font-weight:600; }
.xrules { padding:12px 14px; border-radius:14px; border:1px dashed rgba(167,139,250,.35); background:rgba(123,69,240,.06); color:#D8D3E2;
  font-size:.86rem; line-height:1.7; }
</style>"""


@st.cache_data(ttl=120, show_spinner=False)
def _load():
    return XB.load_all()


def _when(iso):
    t = pd.Timestamp(iso) if iso else None
    if t is None or pd.isna(t):
        return "—"
    t = t.tz_localize("UTC") if t.tzinfo is None else t
    return T.time_ago(t, is_ar())


def _mood_word(m):
    if m is None:
        return L("No posts yet", "ما فيه تغريدات للحين"), "#8F899B"
    if m >= 25:
        return L("Bullish", "صاعد"), "#4ADE80"
    if m >= 8:
        return L("Leaning bullish", "يميل للصعود"), "#86EFAC"
    if m <= -25:
        return L("Bearish", "هابط"), "#F87171"
    if m <= -8:
        return L("Leaning bearish", "يميل للهبوط"), "#FCA5A5"
    return L("Mixed", "متوازن"), "#C4B5FD"


def _status(state):
    """(css class, words) of a bot's state."""
    s = (state or {}).get("status")
    if s == "ok":
        return "on", L(f"Read X {_when(state.get('read_at'))}", f"قرأ X {_when(state.get('read_at'))}")
    if s == "resting":
        return "on", L("Resting until its market's next day", "يرتاح لين يوم السوق الجاي")
    if s == "cap":
        return "", L("Today's reading ceiling reached", "وصل سقف القراءة لليوم")
    if s == "error":
        return "err", L("X did not answer on the last try", "X ما رد في آخر محاولة")
    return "", L("Waiting for the X connection", "ينتظر ربط X")


def _card(bot, state):
    read = (state or {}).get("read") or {}
    led = (state or {}).get("ledger") or XB.new_ledger(bot["market"])
    m = read.get("mood6") if read.get("mood6") is not None else read.get("mood24")
    word, col = _mood_word(m)
    st_ = XB.stats(led, {s: p["px"] for s, p in led["pos"].items()})
    ret = st_["ret"]
    pos = max(-100.0, min(100.0, m or 0.0))
    bar = (f'<i style="left:50%;width:{pos / 2:.1f}%;background:{col}"></i>' if pos >= 0 else
           f'<i style="left:{50 + pos / 2:.1f}%;width:{-pos / 2:.1f}%;background:{col}"></i>')
    cls, words = _status(state)
    flag = "🇸🇦" if bot["market"] == MK.SA else "🇺🇸"
    return (f'<div class="xbc"><div class="hd"><span class="ic">{T.icon(bot["icon"])}</span><span class="nm"><b>{T.esc(L(*bot["name"]))}</b>'
            f'<small>{flag} {T.esc(L("US market", "السوق الأمريكي") if bot["market"] == MK.US else L("Saudi market", "السوق السعودي"))}</small></span></div>'
            f'<div class="beat">{T.esc(L(*bot["beat"]))}</div>'
            f'<div class="row"><span>{T.esc(L("Mood (6 h)", "المزاج (6 ساعات)"))}</span><b style="color:{col}">'
            f'{"—" if m is None else f"{m:+.0f}"} · {T.esc(word)}</b></div>'
            f'<div class="mood"><span class="bar">{bar}</span></div>'
            f'<div class="row"><span>{T.esc(L("Paper account", "الحساب الوهمي"))}</span>{T.pill(ret)}</div>'
            f'<div class="row"><span>{T.esc(L("Open positions", "مراكز مفتوحة"))}</span><b>{st_["open"]} / {bot["slots"]}</b></div>'
            f'<div class="stt {cls}"><i></i>{T.esc(words)}</div></div>')


def _fol(n):
    """A follower count the way X shows it: 950, 12K, 250K, 1.2M."""
    n = int(n or 0)
    for d, u in ((1e6, "M"), (1e3, "K")):
        if n >= d:
            v = n / d
            return f"{v:.1f}".rstrip("0").rstrip(".") + u if v < 10 else f"{v:,.0f}{u}"
    return f"{n:,}"


def _post(p, ar):
    lab = p.get("lab") or "neutral"
    words = {"bull": L("Bullish", "صاعد"), "bear": L("Bearish", "هابط"), "neutral": L("Neutral", "محايد")}[lab]
    tick = "".join(f'<span class="mchip">{T.esc(T.sym_label(t))}</span>' for t in (p.get("tickers") or []))
    link = f"https://x.com/{p.get('user') or 'i'}/status/{p.get('id')}"
    return (f'<div class="xpost"><div class="who"><b dir="auto">{T.esc(p.get("name") or p.get("user") or "")}</b>'
            f'<span dir="ltr">@{T.esc(p.get("user") or "")}</span><span>· {T.esc(_when(p.get("t")))}</span>'
            f'<span>· {_fol(p.get("followers"))} {T.esc(L("followers", "متابع"))}</span></div>'
            f'<div class="tx" dir="auto">{T.esc(p.get("text") or "")}</div>'
            f'<div class="ft"><span class="tag {lab}">{T.esc(words)} {p.get("s", 0):+.2f}</span>{tick}'
            f'<span>♥ {int(p.get("likes") or 0):,} · ↻ {int(p.get("reposts") or 0):,}</span>'
            f'<a class="go" href="{T.esc(link)}" target="_blank" rel="noopener">{T.esc(L("Open on X", "افتح في X"))} ↗</a></div></div>')


def _bot_view(bot, state):
    ar = is_ar()
    state = state or XB.new_bot_state(bot)
    read = state.get("read") or XB.reading([])
    led = state["ledger"]
    held = list(led["pos"])
    talked = read.get("talked") or []
    syms = list(dict.fromkeys(held + [d["sym"] for d in talked[:15]]))
    chg = data.quick_changes(syms) if syms else {}
    now_px = {s: (chg.get(s) or (None, None))[0] or led["pos"].get(s, {}).get("px") for s in syms}
    stt = XB.stats(led, {s: v for s, v in now_px.items() if v})
    cur = "SAR " if bot["market"] == MK.SA else "$"
    k = st.columns(4)
    k[0].markdown(T.kpi("account_balance_wallet", L("Account value", "قيمة الحساب"), f"{cur}{stt['equity']:,.0f}",
                        L(f"started with {cur}{led['start']:,.0f}", f"بدأ بـ {cur}{led['start']:,.0f}")), unsafe_allow_html=True)
    k[1].markdown(T.kpi("trending_up", L("Return", "العائد"), T.pill(stt["ret"]),
                        L(f"since {_when(led.get('since'))}" if led.get("since") else "no trade yet", f"من {_when(led.get('since'))}" if led.get("since") else "ما تداول للحين"),
                        "pos" if stt["ret"] > 0 else "neg" if stt["ret"] < 0 else None), unsafe_allow_html=True)
    wr = "—" if stt["win_rate"] is None else f"{stt['win_rate']:.0f}%"
    k[2].markdown(T.kpi("rule", L("Closed trades", "صفقات مقفلة"), f"{stt['closed']}", L(f"won {wr}", f"الرابحة {wr}")), unsafe_allow_html=True)
    k[3].markdown(T.kpi("forum", L("Posts read (24 h)", "تغريدات مقروءة (24 ساعة)"), f"{read.get('n24', 0):,}",
                        T.esc(_mood_word(read.get('mood24'))[0])), unsafe_allow_html=True)
    a, b = st.columns(2)
    hours = read.get("hours") or []
    with a:
        if any(h.get("n") for h in hours):
            ui.chart(charts.mood_bars([h["t"] for h in hours], [h["mood"] for h in hours],
                                      L("Mood hour by hour (last 48 h)", "المزاج ساعة بساعة (آخر 48 ساعة)"), 300,
                                      (L("Mood", "المزاج"), L("Posts", "تغريدات"))), key=f"xb_mood_{bot['id']}")
        else:
            st.caption(L("The mood chart appears after the first reads.", "رسم المزاج يطلع بعد أول قراءة."))
    with b:
        curve = led.get("curve") or []
        if len(curve) >= 2:
            s_ = pd.Series([c["eq"] for c in curve], index=pd.to_datetime([c["d"] for c in curve]))
            ui.chart(charts.line(s_, L("Paper account", "الحساب الوهمي"), height=300), key=f"xb_eq_{bot['id']}")
        else:
            st.caption(L("The account's curve starts with its first trading day.", "منحنى الحساب يبدأ من أول يوم تداول."))
    ui.sec("forum", "What X talks about", "وش يتكلم عنه X")
    if talked:
        rows = [{"Symbol": d["sym"], L("Posts (24 h)", "تغريدات (24 ساعة)"): d["n24"], L("Growth", "النمو"): d["spike"],
                 L("Tone", "النبرة"): d["s"], L("Today %", "اليوم %"): (chg.get(d["sym"]) or (None, None))[1]} for d in talked[:12]]
        df = pd.DataFrame(rows)
        ui.table(df, sym="Symbol", pills={L("Today %", "اليوم %")}, signed={L("Tone", "النبرة")},
                 fmt={L("Growth", "النمو"): "{:.1f}×", L("Tone", "النبرة"): "{:+.2f}", L("Today %", "اليوم %"): "{:+.2f}%"})
    else:
        st.caption(L("No company in its posts yet.", "ما فيه شركات في تغريداته للحين."))
    ui.sec("work", "Open positions", "المراكز المفتوحة")
    if led["pos"]:
        rows = []
        for s, p in led["pos"].items():
            px = now_px.get(s) or p["px"]
            rows.append({"Symbol": s, L("Shares", "الأسهم"): p["qty"], L("Entry", "الدخول"): p["px"], L("Now", "الآن"): px,
                         L("Return %", "العائد %"): (px / p["px"] - 1) * 100, L("Why", "السبب"): L(*XB.WHY.get(p.get("why"), ("", "")))})
        ui.table(pd.DataFrame(rows), sym="Symbol", pills={L("Return %", "العائد %")}, wrap={L("Why", "السبب")},
                 fmt={L("Entry", "الدخول"): "{:,.2f}", L("Now", "الآن"): "{:,.2f}", L("Return %", "العائد %"): "{:+.2f}%"})
    else:
        st.caption(L("No open position: the bot waits for its signal.", "ما فيه مراكز: البوت ينتظر إشارته."))
    ui.sec("receipt_long", "Latest trades", "آخر الصفقات")
    if led["trades"]:
        rows = []
        for t in reversed(led["trades"][-15:]):
            rows.append({L("When", "متى"): _when(t["t"]), "Symbol": t["sym"],
                         L("Side", "الجهة"): L("Buy", "شراء") if t["side"] == "buy" else L("Sell", "بيع"),
                         L("Price", "السعر"): t["px"], L("Result %", "النتيجة %"): t.get("pnl"),
                         L("Why", "السبب"): L(*XB.WHY.get(t.get("why"), ("", "")))})
        ui.table(pd.DataFrame(rows), sym="Symbol", pills={L("Result %", "النتيجة %")}, wrap={L("Why", "السبب")},
                 words={L("Side", "الجهة"): (L("Buy", "شراء"), L("Sell", "بيع"))},
                 fmt={L("Price", "السعر"): "{:,.2f}", L("Result %", "النتيجة %"): lambda v: "—" if v is None or pd.isna(v) else f"{v:+.2f}%"})
    else:
        st.caption(L("No trade yet.", "ما فيه صفقات للحين."))
    ui.sec("chat", "Its strongest posts (24 h)", "أقوى تغريداته (24 ساعة)")
    top = read.get("top") or []
    if top:
        ui.html("".join(_post(p, ar) for p in top[:8]))
    else:
        st.caption(L("No posts read yet.", "ما قرأ تغريدات للحين."))
    ui.html(f'<div class="xrules"><b>{T.esc(L("Its rules", "قواعده"))}:</b> {T.esc(L(*bot["rules"]))}</div>')
    with st.expander(L("What it searches on X", "وش يبحث عنه في X"), icon=":material/search:"):
        st.code(bot["query"], language=None)


def page_xbots():
    ui.html(CSS)
    ui.header("alternate_email", "X Bots", "بوتات X",
              "Five bots that read X (Twitter) about the market every hour of its day: the mood, the stocks suddenly talked about, the "
              "market pros, breaking news and the Saudi market. Each turns what it reads into signals and trades them on paper.",
              "خمس بوتات تقرأ X (تويتر) عن السوق كل ساعة من يومه: المزاج، والأسهم اللي فجأة صار عنها كلام، والمحللين، والعاجل، والسوق "
              "السعودي. كل بوت يحوّل اللي يقرأه لإشارات ويتداولها وهمياً.")
    try:
        states, meta = _load()
    except Exception:
        states, meta = {}, {}
    order = sorted(XB.BOTS, key=lambda b: b["market"] != MK.current())        # the page's market first
    read_at = max((s.get("read_at") or "" for s in states.values()), default="")
    errs = [s for s in states.values() if s.get("status") == "error"]
    if read_at:
        cls, head = ("err", L("X did not answer on the last try", "X ما رد في آخر محاولة")) if errs and len(errs) == len(states) else \
                    ("on", L("Reading X every hour of the market's day", "تقرأ X كل ساعة من يوم السوق"))
        facts = (f'<span>{T.esc(L("Last read", "آخر قراءة"))} <b>{T.esc(_when(read_at))}</b></span>'
                 f'<span>{T.esc(L("Posts read today", "تغريدات مقروءة اليوم"))} <b>{int(meta.get("reads") or 0):,}</b> / {XB.daily_reads():,}</span>'
                 f'<span>{T.esc(L("Trades on paper: no real money", "التداول وهمي: بدون فلوس حقيقية"))}</span>')
    else:
        cls, head = "", L("Ready: waiting for the X connection", "جاهزة: تنتظر ربط X")
        facts = (f'<span>{T.esc(L("The bots start reading X as soon as the site is connected to it; until then nothing is read or traded.", "البوتات تبدأ تقرأ X أول ما يتربط الموقع فيه، وقبلها ما تقرأ ولا تتداول شي."))}</span>')
    ui.html(f'<div class="xbhero"><div class="st {cls}"><i></i>{T.esc(head)}</div><div class="facts">{facts}</div></div>')
    ui.html('<div class="xbg">' + "".join(_card(b, states.get(b["id"])) for b in order) + "</div>")
    tabs = st.tabs([f":material/{b['icon']}: {L(*b['name'])}" for b in order])
    for tab, b in zip(tabs, order):
        with tab:
            ui.safe(_bot_view, b, states.get(b["id"]))
    st.caption(L("The posts are shown as written on X, with a link to each. The bots' trades are on paper at the latest prices (long only, "
                 "a 0.1% fee each way): an experiment in reading the crowd, not advice.",
                 "التغريدات معروضة مثل ما انكتبت في X مع رابط كل وحدة. صفقات البوتات وهمية بآخر الأسعار (شراء فقط، رسوم 0.1% كل اتجاه): "
                 "تجربة لقراءة كلام الناس، مو توصية."))
    ui.foot()


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "22.5.1"
