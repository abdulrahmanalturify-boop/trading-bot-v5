"""
p_calendar.py - Calendar section: earnings week (Earnings-Hub style), earnings results, economic calendar,
market holidays, dividends, stock splits and IPOs.
"""
from datetime import timedelta

import numpy as np
import pandas as pd
import streamlit as st

import caldata as C
import data
import mcal
import theme as T
import ui
from i18n import L, is_ar

ss = st.session_state

DOW = [("MON", "الاثنين"), ("TUE", "الثلاثاء"), ("WED", "الأربعاء"), ("THU", "الخميس"), ("FRI", "الجمعة"), ("SAT", "السبت"), ("SUN", "الأحد")]
MON = [("Jan", "يناير"), ("Feb", "فبراير"), ("Mar", "مارس"), ("Apr", "أبريل"), ("May", "مايو"), ("Jun", "يونيو"), ("Jul", "يوليو"),
       ("Aug", "أغسطس"), ("Sep", "سبتمبر"), ("Oct", "أكتوبر"), ("Nov", "نوفمبر"), ("Dec", "ديسمبر")]
WHEN = {"bmo": ("wb_sunny", "Before Open", "قبل الافتتاح"), "amc": ("dark_mode", "After Close", "بعد الإغلاق"),
        "dmh": ("schedule", "During market", "أثناء التداول"), "tns": ("help", "Time not confirmed", "الوقت غير مؤكد")}
CAPS = [0, 300_000_000, 2_000_000_000, 10_000_000_000, 50_000_000_000]


# ---------------------------------------------------------------- small helpers
def dow(d, short=True):
    en, ar = DOW[d.weekday()]
    return ar if is_ar() else (en if short else en.title())


def dshort(d):
    """'Tue, Sep 29' / 'الثلاثاء 29 سبتمبر'"""
    en, ar = MON[d.month - 1]
    return f"{DOW[d.weekday()][1]} {d.day} {ar}" if is_ar() else f"{DOW[d.weekday()][0].title()}, {en} {d.day}"


def dlong(d):
    en, ar = MON[d.month - 1]
    return f"{d.day} {ar} {d.year}" if is_ar() else f"{en} {d.day}, {d.year}"


def week_label(mon):
    fri = mon + timedelta(days=4)
    (e1, a1), (e2, a2) = MON[mon.month - 1], MON[fri.month - 1]
    if is_ar():
        return f"{mon.day} {a1} – {fri.day} {a2} {fri.year}"
    return f"{e1} {mon.day} – {e2 + ' ' if fri.month != mon.month else ''}{fri.day}, {fri.year}"


def usd(x):
    """$3.6T · $210B · $4.25B · $65.0M"""
    if x is None or pd.isna(x):
        return "—"
    a, sign = abs(float(x)), "-" if x < 0 else ""
    for unit, div in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if a >= div:
            v = a / div
            return f"{sign}${v:.2f}{unit}" if v < 10 else f"{sign}${v:.1f}{unit}" if v < 100 else f"{sign}${v:.0f}{unit}"
    return f"{sign}${a:,.0f}"


def cap_label(v):
    if not v:
        return L("All companies", "كل الشركات")
    return {300_000_000: "$300M+", 2_000_000_000: "$2B+", 10_000_000_000: "$10B+", 50_000_000_000: "$50B+"}.get(v, usd(v) + "+")


def num(v, dec=2):
    if v is None or pd.isna(v):
        return "—"
    return f"{v:,.{dec}f}"


def spct(v, dec=1):
    if v is None or pd.isna(v):
        return "—"
    return f"{v:+.{dec}f}%"


def _shift(key, n):
    ss[key] = ss.get(key, 0) + n


def _reset(key):
    ss[key] = 0


def week_nav(key, max_back=8, max_fwd=8):
    """‹ previous · this week · next › - returns the Monday of the chosen week."""
    base = C.week_of(mcal.today_et())
    off = max(-max_back, min(max_fwd, int(ss.get(key, 0))))
    ss[key] = off
    prev_i, next_i = (":material/chevron_right:", ":material/chevron_left:") if is_ar() else (":material/chevron_left:", ":material/chevron_right:")
    c1, c2, c3, c4 = st.columns([1, 1.15, 1, 4.2], vertical_alignment="center")
    c1.button(L("Previous", "السابق"), icon=prev_i, key=f"{key}_p", on_click=_shift, args=(key, -1), width="stretch", disabled=off <= -max_back)
    c2.button(L("This week", "هذا الأسبوع"), icon=":material/today:", key=f"{key}_t", on_click=_reset, args=(key,), width="stretch",
              type="primary" if off == 0 else "secondary")
    c3.button(L("Next", "التالي"), icon=next_i, key=f"{key}_n", on_click=_shift, args=(key, 1), width="stretch", disabled=off >= max_fwd)
    mon = base + timedelta(weeks=off)
    tag = (L("This week", "هذا الأسبوع") if off == 0 else L("Next week", "الأسبوع القادم") if off == 1 else
           L("Last week", "الأسبوع الماضي") if off == -1 else "")
    c4.markdown(f'<div class="wklbl">{T.icon("date_range")}<b>{week_label(mon)}</b>' + (f'<span class="tag">{tag}</span>' if tag else "")
                + "</div>", unsafe_allow_html=True)
    return mon


def holiday_note(d):
    kind, key = mcal.day_status(d)
    if kind in ("closed", "early"):
        en, ar = mcal.NAMES[key]
        txt = L(f"Market closed · {en}", f"السوق مغلق · {ar}") if kind == "closed" else L(f"Closes 1:00 pm · {en}", f"إغلاق مبكر 1:00 م · {ar}")
        return f'<div class="hnote {kind}">{T.icon("beach_access" if kind == "closed" else "schedule")}{T.esc(txt)}</div>'
    return ""


def empty_box(ic, en, ar):
    ui.html(f'<div class="calempty">{T.icon(ic)}<div>{T.esc(L(en, ar))}</div></div>')


def kpis(items):
    cols = st.columns(len(items))
    for c, (ic, lab, val, sub, kind) in zip(cols, items):
        c.markdown(T.kpi(ic, lab, val, sub, kind), unsafe_allow_html=True)


# ================================================================ 1) EARNINGS WEEK (Earnings Hub style)
def etile(r):
    res = ""
    if pd.notna(r.EPS) and pd.notna(r.Surprise):
        res = f'<i class="rs {"b" if r.Surprise >= 0 else "m"}"></i>'
    tip = f"{r.Company} ({r.Symbol})"
    if pd.notna(r.Cap):
        tip += f" · {L('Market cap', 'القيمة السوقية')} {usd(r.Cap)}"
    if pd.notna(r.Est):   # EPS Est
        tip += f" · {L('EPS estimate', 'تقدير الربحية')} {r.Est:.2f}"
    if pd.notna(r.EPS):
        tip += f" · {L('Reported', 'المُعلن')} {r.EPS:.2f} ({spct(r.Surprise)})"
    return (f'<a class="et" href="{ui.href(r.Symbol)}" target="_self" title="{T.esc(tip)}">{T.logo_obj(r.Symbol, 40)}'
            f'<span class="tk">{T.esc(r.Symbol)}</span>{res}</a>')


def hub_grid(df, ipo, mon, lim=12):
    today = mcal.today_et()
    cols = []
    for i in range(5):
        d = mon + timedelta(days=i)
        day = df[df["Date"] == d] if not df.empty else df
        cls = " today" if d == today else (" past" if d < today else "")
        head = (f'<div class="hd"><span class="dw">{dow(d)}</span><span class="dn">{d.day}</span>'
                f'<span class="mo">{L(MON[d.month - 1][0], MON[d.month - 1][1])}</span>'
                + (f'<span class="now">{L("Today", "اليوم")}</span>' if d == today else "")
                + f'<span class="cnt">{len(day)}</span></div>')
        body = holiday_note(d)
        for when, sel in (("bmo", ["bmo"]), ("amc", ["amc"]), ("tns", ["dmh", "tns"])):
            g = day[day["When"].isin(sel)] if not day.empty else day
            if g.empty:
                continue
            ic, en, ar = WHEN[when]
            rows = list(g.itertuples())
            tiles = "".join(etile(r) for r in rows[:lim])
            more = ""
            if len(rows) > lim:
                more = (f'<details><summary>+{len(rows) - lim} {L("more", "أخرى")}</summary><div class="tl">'
                        + "".join(etile(r) for r in rows[lim:lim + 60]) + "</div></details>")
            body += (f'<div class="grp {when}"><div class="gh">{T.icon(ic)}<span>{L(en, ar)}</span><b>{len(rows)}</b></div>'
                     f'<div class="tl">{tiles}</div>{more}</div>')
        if ipo is not None and not ipo.empty:
            g = ipo[ipo["Date"] == d]
            if not g.empty:
                items = "".join(
                    f'<div class="ipr" title="{T.esc(r.Company)}">{T.icon("flag")}<b>{T.esc(r.Symbol)}</b><span>{T.esc(str(r.Company)[:22])}</span>'
                    f'<em>{_ipo_price(r)}</em></div>' for r in g.itertuples())
                body += f'<div class="grp ipo"><div class="gh">{T.icon("rocket_launch")}<span>{L("IPOs", "اكتتابات")}</span><b>{len(g)}</b></div>{items}</div>'
        if not body:
            body = f'<div class="none">{L("No reports", "لا توجد إعلانات")}</div>'
        cols.append(f'<div class="day{cls}">{head}{body}</div>')
    return f'<div class="ehub">{"".join(cols)}</div>'


def _ipo_price(r):
    if pd.notna(r.Price):
        return f"${r.Price:,.2f}"
    if pd.notna(r.Low) and pd.notna(r.High):
        return f"${r.Low:,.0f}–{r.High:,.0f}"
    return ""


def day_table(day):
    rows = []
    for r in day.itertuples():
        ic, en, ar = WHEN[r.When]
        sur = ""
        if pd.notna(r.Surprise):
            sur = f'<span class="pill {"pos" if r.Surprise >= 0 else "neg"}">{spct(r.Surprise)}</span>'
        rows.append(f'<div class="erow"><a class="lnk" href="{ui.href(r.Symbol)}" target="_self">{T.logo_obj(r.Symbol, 34)}'
                    f'<span class="nm"><b>{T.esc(r.Symbol)}</b><small>{T.esc(r.Company)}</small></span></a>'
                    f'<span class="when {r.When}">{T.icon(ic)}{L(en, ar)}</span>'
                    f'<span class="q">{T.esc(r.Quarter) if isinstance(r.Quarter, str) else "—"}</span>'
                    f'<span class="v">{num(r.Est)}</span><span class="v">{num(r.EPS)}</span><span class="v">{sur or "—"}</span>'
                    f'<span class="v cap">{usd(r.Cap) if pd.notna(r.Cap) else "—"}</span></div>')
    head = (f'<div class="erow eh"><span>{L("Company", "الشركة")}</span><span>{L("Time", "التوقيت")}</span><span>{L("Quarter", "الربع")}</span>'
            f'<span class="v">{L("EPS est.", "الربحية المتوقعة")}</span><span class="v">{L("EPS", "الربحية")}</span>'
            f'<span class="v">{L("Surprise", "المفاجأة")}</span><span class="v cap">{L("Market cap", "القيمة السوقية")}</span></div>')
    return f'<div class="etab">{head}{"".join(rows)}</div>'


def page_earnings_hub():
    ui.header("event_upcoming", "Earnings Calendar", "مواعيد إعلانات الأرباح",
              "Which companies report this week, and when: before the market opens or after it closes. Click a logo to open the company.",
              "الشركات التي تعلن نتائجها هذا الأسبوع وموعد كل إعلان: قبل افتتاح السوق أو بعد إغلاقه. اضغط على الشعار لفتح صفحة الشركة.")
    mon = week_nav("eh_wk")
    f1, f2, f3 = st.columns([1.25, 1.4, 2.2], vertical_alignment="bottom")
    ui.valid("eh_cap", CAPS)
    cap = f1.selectbox(L("Company size", "حجم الشركة"), CAPS, index=2, key="eh_cap", format_func=cap_label)
    q = f2.text_input(L("Find a company", "ابحث عن شركة"), key="eh_q", placeholder=L("e.g. NKE", "مثال: NKE")).strip().upper()
    with st.spinner(L("Loading this week's earnings calendar...", "جاري تحميل مواعيد الأرباح لهذا الأسبوع...")):
        df = C.earnings(mon, mon + timedelta(days=4), cap)
        ipo = ui.safe(C.ipos, mon, mon + timedelta(days=4))
    if df.empty and (ipo is None or ipo.empty):
        empty_box("event_busy", "No earnings dates found for this week (or the calendar is not reachable right now). Try another week or a smaller company size.",
                  "لا توجد مواعيد أرباح لهذا الأسبوع (أو التقويم غير متاح الآن). جرّب أسبوعاً آخر أو حجم شركات أصغر.")
        ui.foot()
        return
    if q:
        hit = df[df["Symbol"].str.contains(q, regex=False, na=False) | df["Company"].fillna("").astype(str).str.upper().str.contains(q, regex=False)]
        if hit.empty:
            st.info(L(f"“{q}” does not report this week.", f"«{q}» لا تعلن نتائجها هذا الأسبوع."), icon=":material/search_off:")
        else:
            ui.html('<div class="ehit">' + "".join(
                f'<a class="lnk chip" href="{ui.href(r.Symbol)}" target="_self">{T.logo_obj(r.Symbol, 26)}<b>{T.esc(r.Symbol)}</b>'
                f'<span>{dshort(r.Date)} · {L(*WHEN[r.When][1:])}</span></a>' for r in hit.head(8).itertuples()) + "</div>")
    rep = df[df["EPS"].notna()]
    beat = int((rep["Surprise"] > 0).sum()) if not rep.empty else 0
    big = df.head(3)["Symbol"].tolist()
    kpis([("event_available", L("Reports this week", "إعلانات هذا الأسبوع"), f"{len(df)}", cap_label(cap), None),
          ("star", L("Biggest names", "أكبر الشركات"), " · ".join(big) or "—", L("by market value", "حسب القيمة السوقية"), "acc"),
          ("fact_check", L("Already reported", "أعلنت نتائجها"), f"{len(rep)}",
           (L(f"{beat} beat estimates", f"{beat} تجاوزت التوقعات") if len(rep) else L("results appear here as they come", "تظهر النتائج هنا فور صدورها")),
           "pos" if len(rep) and beat >= len(rep) / 2 else None),
          ("rocket_launch", L("IPOs this week", "اكتتابات هذا الأسبوع"), f"{0 if ipo is None else len(ipo)}",
           L("new companies listing", "شركات جديدة تُدرج"), None)])
    ui.html(hub_grid(df, ipo, mon))
    ui.html(f'<div class="elegend"><span>{T.icon("wb_sunny")}{L("Before Open: results before 9:30 am ET", "قبل الافتتاح: النتائج قبل 9:30 صباحاً بتوقيت نيويورك")}</span>'
            f'<span>{T.icon("dark_mode")}{L("After Close: results after 4:00 pm ET", "بعد الإغلاق: النتائج بعد 4:00 مساءً بتوقيت نيويورك")}</span>'
            f'<span><i class="rs b"></i>{L("beat", "تجاوزت التوقعات")}</span><span><i class="rs m"></i>{L("missed", "أقل من التوقعات")}</span></div>')

    ui.sec("view_list", "Day details", "تفاصيل اليوم")
    days = [mon + timedelta(days=i) for i in range(5)]
    today = mcal.today_et()
    default = today if today in days else days[0]
    ui.valid("eh_day", days)
    pick = st.segmented_control(L("Day", "اليوم"), days, default=default, key="eh_day", format_func=lambda d: f"{dshort(d)} · {int((df['Date'] == d).sum())}")
    pick = pick or default
    day = df[df["Date"] == pick]
    if day.empty:
        empty_box("event_busy", "No reports on this day.", "لا توجد إعلانات في هذا اليوم.")
    else:
        order = {"bmo": 0, "dmh": 1, "amc": 2, "tns": 3}
        day = day.assign(_o=day["When"].map(order)).sort_values(["_o", "Cap"], ascending=[True, False]).drop(columns="_o")
        ui.html(day_table(day.head(80)))
        if len(day) > 80:
            st.caption(L(f"Showing the 80 largest of {len(day)} companies.", f"نعرض أكبر 80 شركة من {len(day)}."))
    st.caption(L("Source: Yahoo Finance earnings calendar. Dates can change; companies confirm them a few weeks before.",
                 "المصدر: تقويم أرباح ياهو فاينانس. قد تتغير المواعيد، والشركات تؤكدها قبل الإعلان بأسابيع."))
    ui.foot()


# ================================================================ 2) EARNINGS RESULTS (cards)
def _money(v):
    return usd(v)


def result_card(r, px, rev, react):
    sur = r.Surprise
    kind = "neu" if pd.isna(sur) or abs(sur) < 0.5 else ("beat" if sur > 0 else "miss")
    ic, en, ar = WHEN[r.When]
    q = r.Quarter if isinstance(r.Quarter, str) and r.Quarter else ""
    title = f"{r.Symbol} {q} {L('Earnings', 'نتائج')}".replace("  ", " ")
    p, chg = px.get(r.Symbol, (None, None))
    price = (f'<div class="p">{T.fmt_price(p)}</div>{T.pill(chg)}' if p is not None else "")
    rx = react.get(r.Symbol)
    rx_html = (f'<div class="rx">{L("Reaction", "ردة الفعل")} <span class="{"pos" if rx >= 0 else "neg"}">{rx:+.1f}%</span></div>'
               if rx is not None else "")
    rv = rev.get(r.Symbol) or {}
    r_act, r_est, r_ya = rv.get("rev"), rv.get("est"), rv.get("rev_ya")
    r_sur = (r_act / r_est - 1) * 100 if r_act and r_est else None
    yoy = (r_act / r_ya - 1) * 100 if r_act and r_ya else None
    rev_third = (f'<td class="{"pos" if r_sur >= 0 else "neg"}">{spct(r_sur)}</td>' if r_sur is not None else
                 f'<td class="{"pos" if (yoy or 0) >= 0 else "neg"}">{spct(yoy)} <small>{L("YoY", "سنوي")}</small></td>' if yoy is not None else "<td>—</td>")
    eps_cls = "" if pd.isna(sur) else ("pos" if sur >= 0 else "neg")
    verdict = {"beat": ("verified", "Beat estimates", "تجاوزت التوقعات"), "miss": ("error", "Missed estimates", "أقل من التوقعات"),
               "neu": ("drag_handle", "In line with estimates", "مطابقة للتوقعات")}[kind]
    if pd.isna(r.EPS):
        verdict = ("hourglass_top", "Waiting for results", "بانتظار النتائج")
    return (f'<div class="ecard {kind}"><div class="top"><a class="lnk" href="{ui.href(r.Symbol)}" target="_self">{T.logo_obj(r.Symbol, 44)}</a>'
            f'<div class="t"><div class="nm">{T.esc(title)}</div><div class="co">{T.esc(r.Company)}</div>'
            f'<div class="d">{T.icon(ic)}{dshort(r.Date)} · {L(en, ar)}</div></div><div class="px">{price}{rx_html}</div></div>'
            f'<table class="res"><tr><th></th><th>{L("Estimate", "المتوقع")}</th><th>{L("Actual", "الفعلي")}</th><th>{L("Surprise", "المفاجأة")}</th></tr>'
            f'<tr><td class="k">EPS</td><td>{num(r.Est)}</td><td class="a">{num(r.EPS)}</td><td class="{eps_cls}">{spct(sur)}</td></tr>'
            f'<tr><td class="k">{L("Revenue", "الإيرادات")}</td><td>{_money(r_est)}</td><td class="a">{_money(r_act)}</td>{rev_third}</tr></table>'
            f'<div class="vd">{T.icon(verdict[0])}{L(verdict[1], verdict[2])}</div></div>')


def page_earnings_results():
    ui.header("request_quote", "Earnings Results", "نتائج الأرباح",
              "Latest quarterly results: earnings per share and revenue against analysts' estimates, and how the stock reacted.",
              "أحدث النتائج الفصلية: ربحية السهم والإيرادات مقارنة بتوقعات المحللين، وكيف تفاعل السهم.")
    today = mcal.today_et()
    c1, c2, c3, c4 = st.columns([1.9, 1.2, 1.35, 0.9], vertical_alignment="bottom")
    per = c1.segmented_control(L("Reported", "تاريخ الإعلان"), ["today", "yday", "week", "last"], default="week", key="er_per",
                               format_func=lambda k: {"today": L("Today", "اليوم"), "yday": L("Previous day", "اليوم السابق"),
                                                      "week": L("This week", "هذا الأسبوع"), "last": L("Last week", "الأسبوع الماضي")}[k]) or "week"
    ui.valid("er_cap", CAPS)
    cap = c2.selectbox(L("Company size", "حجم الشركة"), CAPS, index=3, key="er_cap", format_func=cap_label)
    res = c3.segmented_control(L("Result", "النتيجة"), ["all", "beat", "miss"], default="all", key="er_res",
                               format_func=lambda k: {"all": L("All", "الكل"), "beat": L("Beats", "تجاوزت"), "miss": L("Misses", "أقل")}[k]) or "all"
    n = c4.selectbox(L("Show", "العدد"), [12, 24, 48], index=1, key="er_n")
    mon = C.week_of(today) if today.weekday() < 5 else C.week_of(today) - timedelta(days=7)
    start, end = {"today": (today, today), "yday": (mcal.prev_trading_day(today),) * 2, "week": (mon, min(today, mon + timedelta(days=4))),
                  "last": (mon - timedelta(days=7), mon - timedelta(days=3))}[per]
    with st.spinner(L("Loading results...", "جاري تحميل النتائج...")):
        df = C.earnings(start, end, cap)
    rep = df[df["EPS"].notna()].copy() if not df.empty else df
    if rep.empty:
        waiting = df[df["EPS"].isna()] if not df.empty else df
        empty_box("hourglass_top", "No results reported yet for this period. Pick another period, or check the Earnings Calendar for upcoming dates.",
                  "لا توجد نتائج معلنة بعد لهذه الفترة. اختر فترة أخرى أو راجع مواعيد إعلانات الأرباح القادمة.")
        if not waiting.empty:
            ui.sec("hourglass_top", "Reporting soon", "تعلن قريباً")
            ui.html(day_table(waiting.head(20)))
        ui.foot()
        return
    beats, misses = int((rep["Surprise"] > 0).sum()), int((rep["Surprise"] < 0).sum())
    rate = beats / len(rep) * 100
    best = rep.loc[rep["Surprise"].idxmax()] if rep["Surprise"].notna().any() else None
    worst = rep.loc[rep["Surprise"].idxmin()] if rep["Surprise"].notna().any() else None
    kpis([("fact_check", L("Companies reported", "شركات أعلنت"), f"{len(rep)}", f"{T.esc(dshort(start))} → {T.esc(dshort(end))}", None),
          ("verified", L("Beat rate", "نسبة التفوق"), f"{rate:.0f}%", L(f"{beats} beat · {misses} missed", f"{beats} تفوقت · {misses} أقل"),
           "pos" if rate >= 60 else ("neg" if rate < 45 else None)),
          ("trending_up", L("Biggest beat", "أكبر مفاجأة إيجابية"), (f"{best['Symbol']} {spct(best['Surprise'])}" if best is not None else "—"),
           T.esc(str(best["Company"])[:26]) if best is not None else "", "pos"),
          ("trending_down", L("Biggest miss", "أكبر مفاجأة سلبية"), (f"{worst['Symbol']} {spct(worst['Surprise'])}" if worst is not None else "—"),
           T.esc(str(worst["Company"])[:26]) if worst is not None else "", "neg")])
    if res == "beat":
        rep = rep[rep["Surprise"] > 0]
    elif res == "miss":
        rep = rep[rep["Surprise"] < 0]
    rep = rep.sort_values(["Date", "Cap"], ascending=[False, False]).head(n)
    if rep.empty:
        empty_box("filter_alt_off", "No companies match this filter.", "لا توجد شركات تطابق هذا الفلتر.")
        ui.foot()
        return
    syms = rep["Symbol"].tolist()
    with st.spinner(L("Adding revenue and price reaction...", "جاري إضافة الإيرادات وردة فعل السعر...")):
        px = data.changes(tuple(syms)) or {}
        rev = C.revenue_many(syms, dict(zip(rep["Symbol"], rep["Date"])))
        react = C.reactions(rep[["Symbol", "Date", "When"]])
    cards = [result_card(r, px, rev, react) for r in rep.itertuples()]
    ui.html('<div class="egrid">' + "".join(cards) + "</div>")
    st.caption(L("EPS = earnings per share. Surprise = how far the result was from the analysts' average estimate. Reaction = the stock's move on the "
                 "first trading day after the report. Revenue estimates exist only before a report, so after it the card shows growth versus the same "
                 "quarter last year (YoY). Sources: Yahoo Finance.",
                 "ربحية السهم = صافي الربح لكل سهم. المفاجأة = الفرق بين النتيجة ومتوسط توقعات المحللين. ردة الفعل = حركة السهم في أول يوم تداول بعد "
                 "الإعلان. تقديرات الإيرادات متاحة قبل الإعلان فقط، لذلك تعرض البطاقة بعده النمو مقارنة بنفس الربع من العام الماضي. المصدر: ياهو فاينانس."))
    ui.foot()


# ================================================================ 3) ECONOMIC CALENDAR
def _stars(n):
    return f'<span class="stars s{n}">' + "".join(f'<i class="{"on" if i < n else ""}"></i>' for i in range(3)) + "</span>"


def _fmt_val(v):
    if v is None or pd.isna(v):
        return "—"
    a = abs(v)
    return f"{v:,.0f}" if a >= 1000 else f"{v:,.2f}".rstrip("0").rstrip(".") if a < 100 else f"{v:,.1f}"


def econ_rows(day):
    out = []
    for r in day.itertuples():
        a_cls = ""
        if pd.notna(r.Actual) and pd.notna(r.Expected) and r.Actual != r.Expected:
            better = (r.Actual > r.Expected) != bool(C.LOWER_IS_BETTER.search(r.Event))
            a_cls = "pos" if better else "neg"
        t = r.Time.strftime("%H:%M") if pd.notna(r.Time) and (r.Time.hour or r.Time.minute) else L("All day", "طوال اليوم")
        per = f"<small>{T.esc(r.Period)}</small>" if isinstance(r.Period, str) and r.Period not in ("", "nan", "None") else ""
        reg = f'<span class="rg">{T.esc(r.Region)}</span>' if r.Region not in ("US", "USA") else ""
        act = f'<span class="pill {a_cls}">{_fmt_val(r.Actual)}</span>' if a_cls else _fmt_val(r.Actual)
        out.append(f'<div class="evr s{r.Stars}"><span class="tm">{t}</span>{_stars(r.Stars)}<span class="nm">{reg}{T.esc(r.Event)} {per}</span>'
                   f'<span class="v a">{act}</span><span class="v">{_fmt_val(r.Expected)}</span><span class="v">{_fmt_val(r.Last)}</span></div>')
    return "".join(out)


def page_econ_calendar():
    ui.header("event_note", "Economic Calendar", "التقويم الاقتصادي",
              "Data releases and central-bank events that move markets: time (New York), importance, actual vs. forecast vs. previous.",
              "البيانات الاقتصادية وأحداث البنوك المركزية التي تحرك الأسواق: الوقت (نيويورك) والأهمية والفعلي مقابل المتوقع والسابق.")
    mon = week_nav("ec_wk", 6, 6)
    c1, c2, c3 = st.columns([1.5, 1.2, 2.2], vertical_alignment="bottom")
    imp = c1.segmented_control(L("Importance", "الأهمية"), [1, 2, 3], default=1, key="ec_imp",
                               format_func=lambda v: {1: L("All", "الكل"), 2: "★★+", 3: "★★★"}[v]) or 1
    reg = c2.segmented_control(L("Region", "المنطقة"), ["US", "ALL"], default="US", key="ec_reg",
                               format_func=lambda v: L("United States", "أمريكا") if v == "US" else L("World", "العالم")) or "US"
    q = c3.text_input(L("Search an event", "ابحث عن حدث"), key="ec_q", placeholder=L("e.g. CPI, payrolls, Fed", "مثال: CPI، الوظائف، الفيدرالي")).strip()
    with st.spinner(L("Loading the economic calendar...", "جاري تحميل التقويم الاقتصادي...")):
        df = C.econ(mon, mon + timedelta(days=6), reg)
    if df.empty:
        empty_box("event_busy", "The economic calendar is not reachable right now. Please try again in a few minutes.",
                  "التقويم الاقتصادي غير متاح حالياً. حاول مرة أخرى بعد دقائق.")
        ui.foot()
        return
    now = pd.Timestamp.now(tz=mcal.ET)
    nxt = df[(df["Time"] >= now) & (df["Stars"] >= 3)].head(1)
    released = df[df["Actual"].notna()]
    k = [("event", L("Events this week", "أحداث هذا الأسبوع"), f"{len(df)}", L(f"{int((df['Stars'] >= 3).sum())} high importance",
                                                                            f"{int((df['Stars'] >= 3).sum())} عالية الأهمية"), None),
         ("done_all", L("Released", "صدرت"), f"{len(released)}", L("with actual numbers", "بأرقام فعلية"), None)]
    if not nxt.empty:
        r = nxt.iloc[0]
        mins = (r["Time"] - now).total_seconds() / 60
        left = (f"{int(mins // 1440)}{L('d', 'ي')} {int(mins % 1440 // 60)}{L('h', 'س')}" if mins >= 1440 else
                f"{int(mins // 60)}{L('h', 'س')} {int(mins % 60)}{L('m', 'د')}")
        k.append(("alarm", L("Next key event", "الحدث المهم القادم"), T.esc(str(r["Event"])[:28]), f"{dshort(r['Date'])} {r['Time']:%H:%M} ET · {left}", "acc"))
    kpis(k)
    if imp > 1:
        df = df[df["Stars"] >= imp]
    if q:
        df = df[df["Event"].str.contains(q, case=False, regex=False, na=False)]
    if df.empty:
        empty_box("filter_alt_off", "No events match these filters.", "لا توجد أحداث تطابق هذه الفلاتر.")
        ui.foot()
        return
    head = (f'<div class="evr eh"><span class="tm">{L("Time ET", "الوقت")}</span><span>{L("Impact", "الأهمية")}</span><span class="nm">{L("Event", "الحدث")}</span>'
            f'<span class="v">{L("Actual", "الفعلي")}</span><span class="v">{L("Forecast", "المتوقع")}</span><span class="v">{L("Previous", "السابق")}</span></div>')
    today = mcal.today_et()
    blocks = []
    for d, day in df.groupby("Date", sort=True):
        blocks.append(f'<div class="evday{" today" if d == today else ""}"><div class="dh">{T.icon("calendar_today")}{dshort(d)}'
                      + (f'<span class="now">{L("Today", "اليوم")}</span>' if d == today else "") + holiday_note(d)
                      + f'<span class="c">{len(day)}</span></div>{head}{econ_rows(day)}</div>')
    ui.html('<div class="evcal">' + "".join(blocks) + "</div>")
    st.caption(L("★★★ = market-moving (inflation, jobs, the Fed, GDP, retail sales, ISM). Green actual = better than forecast for the economy, "
                 "red = worse (for unemployment and jobless claims, lower is better). Source: Yahoo Finance economic calendar.",
                 "★★★ = يحرك السوق (التضخم والوظائف والفيدرالي والناتج المحلي ومبيعات التجزئة وISM). الفعلي الأخضر = أفضل من المتوقع للاقتصاد، "
                 "والأحمر = أسوأ (في البطالة وطلبات إعانة البطالة الأقل أفضل). المصدر: التقويم الاقتصادي في ياهو فاينانس."))
    ui.foot()


# ================================================================ 4) MARKET HOLIDAYS
def page_holidays():
    ui.header("beach_access", "Market Holidays", "عطلات السوق",
              "When the US stock market is closed or closes early (NYSE and Nasdaq), and the days only the bond market closes.",
              "الأيام التي يُغلق فيها سوق الأسهم الأمريكي أو يُغلق مبكراً (بورصة نيويورك وناسداك)، والأيام التي يُغلق فيها سوق السندات فقط.")
    today = mcal.today_et()
    years = [today.year, today.year + 1]
    evs = [(d, k, kind) for y in years for d, k, kind in mcal.year_events(y)]
    up = [e for e in evs if e[0] >= today]
    nxt_closed = next((e for e in up if e[2] == "closed"), None)
    nxt_early = next((e for e in up if e[2] == "early"), None)
    status, key = mcal.day_status(today)
    now = pd.Timestamp.now(tz=mcal.ET)
    mins = now.hour * 60 + now.minute
    close = 780 if status == "early" else 960
    if status in ("open", "early") and mins < 570:
        st_txt = (L("Opens at 9:30 am ET", "يفتح 9:30 ص بتوقيت نيويورك"), "acc", "schedule")
    elif status in ("open", "early") and mins < close:
        st_txt = (L("Open now", "مفتوح الآن"), "pos", "storefront") if status == "open" else (L("Open · closes 1:00 pm", "مفتوح · يُغلق 1:00 م"), "acc", "schedule")
    elif status in ("open", "early"):
        nd = mcal.next_trading_day(today)
        st_txt = (L(f"Closed · opens {dshort(nd)}", f"مغلق · يفتح {dshort(nd)}"), "neg", "bedtime")
    else:
        nd = mcal.next_trading_day(today)
        st_txt = ((L("Closed · weekend", "مغلق · عطلة نهاية الأسبوع") if status == "weekend" else L("Closed today", "مغلق اليوم")) + f" · {L('opens', 'يفتح')} {dshort(nd)}",
                  "neg", "weekend" if status == "weekend" else "block")
    left = mcal.trading_days(today + timedelta(days=1), today.replace(month=12, day=31))
    items = [(st_txt[2], L("Stock market", "سوق الأسهم"), st_txt[0], L(*mcal.NAMES[key]) if key else L("regular hours 9:30 am – 4:00 pm ET",
                                                                                                        "الساعات المعتادة 9:30 ص – 4:00 م بتوقيت نيويورك"), st_txt[1])]
    if nxt_closed:
        d, k, _ = nxt_closed
        items.append(("event_busy", L("Next market holiday", "العطلة القادمة"), T.esc(L(*mcal.NAMES[k])),
                      f"{dshort(d)} · {L(f'in {(d - today).days} days', f'بعد {(d - today).days} يوم')}", "acc"))
    if nxt_early:
        d, k, _ = nxt_early
        items.append(("schedule", L("Next early close", "الإغلاق المبكر القادم"), dshort(d), L("stocks close at 1:00 pm ET", "الأسهم تُغلق 1:00 م بتوقيت نيويورك"), None))
    items.append(("date_range", L("Trading days left this year", "أيام التداول المتبقية هذا العام"), f"{left}", str(today.year), None))
    kpis(items)
    tabs = st.tabs([str(y) for y in years])
    kind_txt = {"closed": ("block", L("Closed", "مغلق")), "early": ("schedule", L("Early close 1:00 pm", "إغلاق مبكر 1:00 م")),
                "bonds": ("account_balance", L("Bond market closed · stocks open", "سوق السندات مغلق · الأسهم مفتوحة"))}
    for tab, y in zip(tabs, years):
        rows = []
        for d, k, kind in mcal.year_events(y):
            en, ar = mcal.NAMES[k]
            cls = " past" if d < today else (" next" if nxt_closed and d == nxt_closed[0] or nxt_early and d == nxt_early[0] else "")
            when = (L(f"in {(d - today).days} days", f"بعد {(d - today).days} يوم") if d > today else L("Today", "اليوم") if d == today else L("Passed", "مضى"))
            ic, txt = kind_txt[kind]
            rows.append(f'<div class="hrow {kind}{cls}"><div class="dt"><b>{d.day}</b><span>{L(MON[d.month - 1][0], MON[d.month - 1][1])}</span></div>'
                        f'<div class="nm"><b>{T.esc(L(en, ar))}</b><small>{dow(d, False)} · {dlong(d)}</small></div>'
                        f'<span class="st">{T.icon(ic)}{txt}</span><span class="wh">{when}</span></div>')
        with tab:
            ui.html('<div class="hlist">' + "".join(rows) + "</div>")
    ui.html(f'<div class="card calnote">{T.icon("info")}<div>{L("Regular hours: 9:30 am – 4:00 pm New York time (4:30 pm – 11:00 pm Saudi time; one hour earlier from November to early March). On early-close days stocks stop at 1:00 pm and most stock options at 1:15 pm. The bond market follows SIFMA: it also closes on Columbus Day and Veterans Day and closes early at 2:00 pm before some holidays.", "الساعات المعتادة: 9:30 صباحاً – 4:00 مساءً بتوقيت نيويورك (4:30 مساءً – 11:00 مساءً بتوقيت السعودية، وأبكر بساعة من نوفمبر إلى أوائل مارس). في أيام الإغلاق المبكر تتوقف الأسهم 1:00 ظهراً ومعظم عقود الخيارات 1:15. سوق السندات يتبع جمعية SIFMA: يُغلق أيضاً في يوم كولومبوس ويوم المحاربين القدامى ويُغلق مبكراً 2:00 ظهراً قبل بعض العطلات.")}</div></div>')
    ui.foot()


# ================================================================ 5) DIVIDENDS
def page_dividends():
    ui.header("payments", "Dividend Calendar", "تقويم التوزيعات",
              "Upcoming ex-dividend dates. To receive a dividend you must own the stock before its ex-dividend date.",
              "مواعيد استحقاق التوزيعات القادمة. لتحصل على التوزيع يجب أن تملك السهم قبل تاريخ الاستحقاق.")
    mon = week_nav("dv_wk", 4, 4)
    c1, c2 = st.columns([2, 1.2], vertical_alignment="bottom")
    q = c1.text_input(L("Find a company", "ابحث عن شركة"), key="dv_q", placeholder=L("e.g. KO", "مثال: KO")).strip().upper()
    big_only = c2.toggle(L("Large companies only", "الشركات الكبيرة فقط"), value=True, key="dv_big")
    with st.spinner(L("Loading ex-dividend dates...", "جاري تحميل مواعيد التوزيعات...")):
        df, src = C.dividends(mon, mon + timedelta(days=4))
    if df.empty:
        empty_box("event_busy", "No ex-dividend dates found for this week (or the calendar is not reachable right now). Try another week.",
                  "لا توجد مواعيد توزيعات لهذا الأسبوع (أو التقويم غير متاح الآن). جرّب أسبوعاً آخر.")
        ui.foot()
        return
    qd = data.quotes_df(df["Symbol"].tolist()[:450])
    if not qd.empty:
        df = df.merge(qd[["Symbol", "Price", "Mkt Cap"]].rename(columns={"Price": "Px", "Mkt Cap": "MktCap"}), on="Symbol", how="left")
    else:
        df["Px"], df["MktCap"] = np.nan, np.nan
    df["Px"] = pd.to_numeric(df["Px"], errors="coerce").fillna(pd.to_numeric(df["Price"], errors="coerce"))
    ann = pd.to_numeric(df["Annual"], errors="coerce")
    df["Yield"] = np.where((df["Px"] > 0) & (ann > 0), ann / df["Px"] * 100, np.nan)
    if big_only and df["MktCap"].notna().sum() >= 5:
        df = df[df["MktCap"] >= 2e9]
    if q:
        df = df[df["Symbol"].str.contains(q, regex=False, na=False) | df["Company"].fillna("").astype(str).str.upper().str.contains(q, regex=False)]
    if df.empty:
        empty_box("filter_alt_off", "No companies match these filters.", "لا توجد شركات تطابق هذه الفلاتر.")
        ui.foot()
        return
    top = df.sort_values("Yield", ascending=False).iloc[0] if df["Yield"].notna().any() else None
    kpis([("payments", L("Ex-dividend this week", "توزيعات هذا الأسبوع"), f"{len(df)}", L("companies", "شركة"), None),
          ("percent", L("Highest yield", "أعلى عائد"), (f"{top['Symbol']} {top['Yield']:.1f}%" if top is not None else "—"),
           T.esc(str(top["Company"])[:28]) if top is not None else "", "pos"),
          ("info", L("Rule", "القاعدة"), L("Buy before ex-date", "اشترِ قبل تاريخ الاستحقاق"), L("the day before at the latest", "في اليوم السابق كحد أقصى"), "acc")])
    today = mcal.today_et()
    head = (f'<div class="drow th"><span>{L("Company", "الشركة")}</span><span class="v">{L("Dividend", "التوزيع")}</span>'
            f'<span class="v">{L("Yearly", "سنوياً")}</span><span class="v">{L("Yield", "العائد")}</span><span class="v">{L("Pay date", "تاريخ الدفع")}</span></div>')
    blocks = []
    for d, day in df.groupby("ExDate", sort=True):
        day = day.sort_values(["MktCap", "Yield"], ascending=False, na_position="last")
        rows = "".join(
            f'<div class="drow"><a class="lnk" href="{ui.href(r.Symbol)}" target="_self">{T.logo_obj(r.Symbol, 32)}<span class="nm"><b>{T.esc(r.Symbol)}</b>'
            f'<small>{T.esc(str(r.Company)[:40])}</small></span></a><span class="v">{"$" + format(r.Amount, ",.4g") if pd.notna(r.Amount) else "—"}</span>'
            f'<span class="v">{"$" + format(r.Annual, ",.3g") if pd.notna(r.Annual) else "—"}</span>'
            f'<span class="v y">{f"{r.Yield:.2f}%" if pd.notna(r.Yield) else "—"}</span>'
            f'<span class="v">{dshort(r.PayDate) if isinstance(r.PayDate, type(today)) else "—"}</span></div>' for r in day.head(60).itertuples())
        blocks.append(f'<div class="evday{" today" if d == today else ""}"><div class="dh">{T.icon("event")}{L("Ex-dividend", "الاستحقاق")} · {dshort(d)}'
                      + (f'<span class="now">{L("Today", "اليوم")}</span>' if d == today else "") + f'<span class="c">{len(day)}</span></div>{head}{rows}</div>')
    ui.html('<div class="evcal">' + "".join(blocks) + "</div>")
    st.caption(L(f"Yield = yearly dividend ÷ price. Source: {src}.", f"العائد = التوزيع السنوي ÷ السعر. المصدر: {src}."))
    ui.foot()


# ================================================================ 6) STOCK SPLITS
def page_splits():
    ui.header("call_split", "Stock Splits", "تقسيم الأسهم",
              "Upcoming and recent stock splits. A 10-for-1 split turns every share into 10 cheaper shares; a reverse split merges shares.",
              "عمليات تقسيم الأسهم القادمة والأخيرة. التقسيم 10 مقابل 1 يحوّل كل سهم إلى 10 أسهم بسعر أقل، والتقسيم العكسي يدمج الأسهم.")
    today = mcal.today_et()
    view = st.segmented_control(L("Show", "عرض"), ["up", "recent"], default="up", key="sp_view",
                                format_func=lambda k: L("Upcoming", "القادمة") if k == "up" else L("Last 60 days", "آخر 60 يوماً")) or "up"
    with st.spinner(L("Loading stock splits...", "جاري تحميل عمليات التقسيم...")):
        df = C.splits(today - timedelta(days=60), today + timedelta(days=120))
    if df.empty:
        empty_box("event_busy", "No stock splits found (or the calendar is not reachable right now).", "لا توجد عمليات تقسيم (أو التقويم غير متاح الآن).")
        ui.foot()
        return
    up, rec = df[df["Date"] >= today], df[df["Date"] < today].sort_values("Date", ascending=False)
    kpis([("event_upcoming", L("Upcoming splits", "تقسيمات قادمة"), f"{len(up)}", L("next 120 days", "خلال 120 يوماً"), None),
          ("call_split", L("Forward splits", "تقسيم عادي"), f"{int((df['Kind'] == 'forward').sum())}", L("more, cheaper shares", "أسهم أكثر بسعر أقل"), "pos"),
          ("merge", L("Reverse splits", "تقسيم عكسي"), f"{int((df['Kind'] == 'reverse').sum())}", L("often a sign of a weak stock", "غالباً علامة ضعف"), "neg")])
    rows = up if view == "up" else rec
    if rows.empty:
        empty_box("event_busy", "Nothing to show here right now.", "لا يوجد ما يُعرض هنا حالياً.")
        ui.foot()
        return
    out = []
    for r in rows.head(120).itertuples():
        each = (L(f"each share becomes {r.New / r.Old:g}", f"كل سهم يصبح {r.New / r.Old:g}") if r.Kind == "forward"
                else L(f"every {r.Old / r.New:g} shares become 1", f"كل {r.Old / r.New:g} أسهم تصبح سهماً واحداً"))
        out.append(f'<div class="sprow {r.Kind}"><a class="lnk" href="{ui.href(r.Symbol)}" target="_self">{T.logo_obj(r.Symbol, 36)}'
                   f'<span class="nm"><b>{T.esc(r.Symbol)}</b><small>{T.esc(str(r.Company)[:44])}</small></span></a>'
                   f'<span class="ratio">{T.esc(r.Ratio)}</span><span class="k">{T.icon("call_split" if r.Kind == "forward" else "merge")}'
                   f'{L("Forward", "عادي") if r.Kind == "forward" else L("Reverse", "عكسي")}</span><span class="ex">{T.esc(each)}</span>'
                   f'<span class="dt">{dshort(r.Date)}</span></div>')
    ui.html('<div class="splist">' + "".join(out) + "</div>")
    st.caption(L("A split does not change what your investment is worth: you own more (or fewer) shares at a proportionally lower (or higher) price. "
                 "Source: Yahoo Finance splits calendar.",
                 "التقسيم لا يغيّر قيمة استثمارك: تملك أسهماً أكثر (أو أقل) بسعر أقل (أو أعلى) بنفس النسبة. المصدر: تقويم التقسيمات في ياهو فاينانس."))
    ui.foot()


# ================================================================ 7) IPOs
IPO_STATUS = {"expected": ("event_upcoming", "Expected", "متوقع", "acc"), "priced": ("sell", "Priced", "تم التسعير", "pos"),
              "filed": ("description", "Filed", "قُدّم الطلب", "neu"), "withdrawn": ("block", "Withdrawn", "انسحب", "neg"),
              "amended": ("edit_note", "Amended", "معدّل", "neu")}


def page_ipos():
    ui.header("rocket_launch", "IPO Calendar", "الاكتتابات العامة",
              "Companies going public: upcoming listings with their price range, and recent IPOs with their performance since the first day.",
              "الشركات التي تطرح أسهمها للاكتتاب: الطروحات القادمة ونطاق سعرها، والطروحات الأخيرة وأداؤها منذ أول يوم.")
    today = mcal.today_et()
    with st.spinner(L("Loading IPOs...", "جاري تحميل الاكتتابات...")):
        df = C.ipos(today - timedelta(days=45), today + timedelta(days=60))
    if df.empty:
        empty_box("event_busy", "No IPOs found (or the calendar is not reachable right now).", "لا توجد اكتتابات (أو التقويم غير متاح الآن).")
        ui.foot()
        return
    st_ = df["Status"].fillna("")
    up = df[(df["Date"] >= today) & ~st_.str.contains("withdraw")]
    priced = df[(df["Date"] < today) & ~st_.str.contains("withdraw")].sort_values("Date", ascending=False)
    wd = df[st_.str.contains("withdraw")]
    qd = data.quotes_df(priced["Symbol"].tolist()[:150]) if not priced.empty else pd.DataFrame()
    last = dict(zip(qd["Symbol"], qd["Price"])) if not qd.empty else {}
    raised = priced["Size"].sum(skipna=True) if not priced.empty else 0
    kpis([("event_upcoming", L("Upcoming IPOs", "اكتتابات قادمة"), f"{len(up)}", L("next 60 days", "خلال 60 يوماً"), "acc"),
          ("sell", L("Recent IPOs", "اكتتابات أخيرة"), f"{len(priced)}", L("last 45 days", "آخر 45 يوماً"), None),
          ("savings", L("Money raised", "المبالغ المجمعة"), usd(raised) if raised else "—", L("recent IPOs", "الاكتتابات الأخيرة"), None),
          ("block", L("Withdrawn", "انسحبت"), f"{len(wd)}", L("postponed or cancelled", "أُجلت أو أُلغيت"), None)])
    view = st.segmented_control(L("Show", "عرض"), ["up", "recent", "wd"], default="up", key="ipo_view",
                                format_func=lambda k: {"up": L("Upcoming", "القادمة"), "recent": L("Recent", "الأخيرة"),
                                                       "wd": L("Withdrawn", "المنسحبة")}[k]) or "up"
    rows = {"up": up, "recent": priced, "wd": wd}[view]
    if rows.empty:
        empty_box("event_busy", "Nothing to show here right now.", "لا يوجد ما يُعرض هنا حالياً.")
        ui.foot()
        return
    out = []
    for r in rows.head(120).itertuples():
        key = next((k for k in IPO_STATUS if k in str(r.Status)), None)
        ic, en, ar, kind = IPO_STATUS.get(key, ("help", str(r.Status).title() or "—", str(r.Status) or "—", "neu"))
        perf = "<span></span>"
        if view == "recent" and r.Symbol in last and pd.notna(r.Price) and r.Price:
            ch = (last[r.Symbol] / r.Price - 1) * 100
            perf = f'<span class="pill {"pos" if ch >= 0 else "neg"}" title="{L("since the IPO price", "منذ سعر الطرح")}">{ch:+.1f}%</span>'
        size = usd(r.Size) if pd.notna(r.Size) and r.Size else "—"
        shares = f"{r.Shares / 1e6:,.1f}M" if pd.notna(r.Shares) and r.Shares else "—"
        out.append(f'<div class="iprow"><div class="dt"><b>{r.Date.day}</b><span>{L(MON[r.Date.month - 1][0], MON[r.Date.month - 1][1])}</span></div>'
                   f'{T.logo_obj(r.Symbol, 36)}<span class="nm"><b>{T.esc(r.Symbol)}</b><small>{T.esc(str(r.Company)[:46])}</small></span>'
                   f'<span class="ex">{T.esc(r.Exchange or "")}</span><span class="v">{_ipo_price(r) or "—"}</span>'
                   f'<span class="v">{shares}</span><span class="v">{size}</span>{perf}'
                   f'<span class="badge b-{kind}">{T.icon(ic)}{L(en, ar)}</span></div>')
    head = (f'<div class="iprow ih"><span>{L("Date", "التاريخ")}</span><span></span><span class="nm">{L("Company", "الشركة")}</span>'
            f'<span class="ex">{L("Exchange", "السوق")}</span><span class="v">{L("Price", "السعر")}</span><span class="v">{L("Shares", "الأسهم")}</span>'
            f'<span class="v">{L("Deal size", "حجم الطرح")}</span><span></span></div>')
    ui.html('<div class="iplist">' + head + "".join(out) + "</div>")
    st.caption(L("Price = the final IPO price, or the expected range before pricing. Deal size = shares × price. Dates can move. Source: Yahoo Finance IPO calendar.",
                 "السعر = سعر الطرح النهائي، أو النطاق المتوقع قبل التسعير. حجم الطرح = عدد الأسهم × السعر. قد تتغير المواعيد. المصدر: تقويم الاكتتابات في ياهو فاينانس."))
    ui.foot()

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.7"
