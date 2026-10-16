"""
p_academy.py - Academy (interactive 3-minute courses with quizzes, learning dashboard) · Glossary
Clicking anywhere on a course card opens it (invisible button over the card, no page reload, progress is kept).
"""
import math
import json
import base64
import zlib
import academy_micro as AM
import academy_learning as LE
import pandas as pd
import academy_visuals as AV
import academy_labs as AL
import streamlit as st

import academy as A
import charts
import data
import ta
import theme as T
import ui
from i18n import L, is_ar

ss = st.session_state
LEVELS = {"all": ("All", "الكل"), "Beginner": ("Beginner", "مبتدئ"), "Essential": ("Essential", "أساسي"),
          "Intermediate": ("Intermediate", "متوسط"), "Advanced": ("Advanced", "متقدم")}
LEVEL_KIND = {"Beginner": "beg", "Essential": "ess", "Intermediate": "int", "Advanced": "adv"}
LEVEL_COLOR = {"Beginner": "#22C55E", "Essential": "#EAB308", "Intermediate": "#F97316", "Advanced": "#EF4444"}


def _course(cid):
    return next((c for c in A.COURSES if c["id"] == cid), None)


def _learning():
    if "ac_learning" not in ss:
        ss["ac_learning"] = LE.clean({}, A.COURSES)
    return ss["ac_learning"]


def _learning_stats():
    return LE.stats(_learning(), A.COURSES, ss.get("completed", set()),
                    {c["id"]: int(ss.get(f"step_{c['id']}", 0) or 0) for c in A.COURSES})


# ---------------------------------------------------------------- progress kept in the browser
# The progress (courses completed, the step reached in the others) is kept in this browser like the portfolio code: a compact
# text with stable course IDs. Legacy index codes are migrated using a frozen old catalog.
def _progress_code():
    """Versioned ID-based storage is unaffected by sorting or future additions."""
    courses = {c["id"]: c for c in A.COURSES}
    done = sorted(set(ss.get("completed", set())) & courses.keys())
    steps = {cid: min(max(int(ss.get(f"step_{cid}", 0) or 0), 0), len(c["sections"]))
             for cid, c in courses.items() if ss.get(f"step_{cid}", 0) and cid not in done}
    payload = json.dumps({"done": done, "steps": steps, "learning": LE.clean(_learning(), A.COURSES)}, separators=(",", ":")).encode()
    return "v3_" + base64.urlsafe_b64encode(zlib.compress(payload)).decode().rstrip("=")


def _progress_load(code):
    courses = {c["id"]: c for c in A.COURSES}
    done, steps = [], {}
    if str(code or "").startswith(("v2_", "v3_")):
        try:
            raw = code[3:]
            decoded = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
            if code.startswith("v3_"):
                decoded = zlib.decompressobj().decompress(decoded, 65537)
                if len(decoded) > 65536:
                    return
            payload = json.loads(decoded)
            if not isinstance(payload, dict):
                return
            done = payload.get("done", [])
            steps = payload.get("steps", {})
            if not isinstance(done, list) or not isinstance(steps, dict):
                return
            ss["ac_learning"] = LE.clean(payload.get("learning"), A.COURSES)
            ss["ac_week_goal"] = ss["ac_learning"]["goal"]
        except (ValueError, TypeError, zlib.error):
            return
    else:
        # Freeze the old index mapping: never interpret old codes against the new catalog.
        for part in str(code or "").split("_"):
            try:
                if part.endswith("d"):
                    i = int(part[:-1])
                    if 0 <= i < len(AM.LEGACY_IDS):
                        done.append(AM.LEGACY_IDS[i])
                elif "x" in part:
                    i, step = map(int, part.split("x", 1))
                    if 0 <= i < len(AM.LEGACY_IDS):
                        steps[AM.LEGACY_IDS[i]] = step
            except ValueError:
                continue
    ss.setdefault("completed", set()).update(cid for cid in done if isinstance(cid, str) and cid in courses)
    for cid, step in steps.items():
        if cid not in courses or type(step) is not int:
            continue
        key = f"step_{cid}"
        ss[key] = min(len(courses[cid]["sections"]), max(int(ss.get(key, 0) or 0), step, 0))


def _progress_sync():
    """Once per visit the browser's copy is merged in; afterwards every change is written back to it."""
    try:
        import p_portfolio as PP
        if not ss.get("_ac_loaded"):
            got = PP.browser()
            if got is None:                          # the browser hasn't answered yet: next run
                return
            _progress_load(got.get("tura_ac"))
            ss["_ac_loaded"] = True
            ss["_ac_kept"] = got.get("tura_ac")
        code = _progress_code()
        if code != ss.get("_ac_kept"):
            PP.keep({"tura_ac": code})
            ss["_ac_kept"] = code
    except Exception:
        pass


def _status(cid):
    if cid in ss.get("completed", set()):
        return "done"
    return "prog" if ss.get(f"step_{cid}", 0) > 0 or any(x.startswith(cid + ":") for x in _learning()["lessons"]) else "new"


def _card_html(c):
    lvl = c["level"]
    st_ = _status(c["id"])
    n = len(c["sections"]) + 1
    step = n if st_ == "done" else ss.get(f"step_{c['id']}", 0)
    status = {"done": T.badge(L("Completed", "مكتمل"), "up", "check_circle"),
              "prog": T.badge(L("In progress", "قيد التعلم"), "gold", "timelapse"),
              "new": T.badge(L("Start", "ابدأ"), "neu", "play_circle")}[st_]
    mins = T.badge(L(str(c["mins"]) + " min", str(c["mins"]) + " دقائق"), "neu", "schedule")
    if c.get("new"):
        status += T.badge(L("New", "جديد"), "vio", "auto_awesome")
    color = LEVEL_COLOR.get(lvl[0], T.ACCENT)
    return (f'<div class="course" style="--lv:{color}"><div class="art">{A.course_art(c["art"], c["id"])}'
            f'<div class="play">{T.icon("play_arrow")}</div></div><div class="body"><div class="ttl">{T.esc(L(*c["title"]))}</div>'
            f'<div class="tag">{T.esc(L(*c["tagline"]))}</div><div class="meta">{T.badge(L(*lvl), LEVEL_KIND.get(lvl[0], "neu"), "signal_cellular_alt")}'
            f'{mins}{status}</div><div class="prog"><span style="width:{step / n * 100:.0f}%"></span></div></div></div>')


def _open_course(cid):
    LE.visit(_learning(), cid)
    ss["course"] = cid
    st.query_params["course"] = cid
    if cid not in ss.get("ac_active_path", []):
        ss.pop("ac_active_path", None)


def _start_path(ids, cid):
    ss["ac_active_path"] = list(ids)
    _open_course(cid)


def course_cards(courses, prefix="crs", per_row=3):
    """Clickable cards: the whole card is a button (no reload, progress kept)."""
    for i in range(0, len(courses), per_row):
        cols = st.columns(per_row)
        for col, c in zip(cols, courses[i:i + per_row]):
            with col:
                with st.container(key=f"{prefix}_{c['id']}"):
                    ui.html(_card_html(c))
                    st.button(L(*c["title"]), key=f"{prefix}b_{c['id']}", on_click=_open_course, args=(c["id"],), width="stretch")


# ---------------------------------------------------------------- interactive blocks
def interactive(key):
    if key in AM.LABS:
        AM.render(key)
        return
    if key in AL.LABS:
        AL.render(key)
        return
    if key == "candle_anatomy":
        ui.html('<div class="card" style="text-align:center">' + A.CANDLE_ANATOMY.format(
            high=L("High", "الأعلى"), low=L("Low", "الأدنى"), open=L("Open", "الافتتاح"), close=L("Close", "الإغلاق"),
            body=L("Body", "الجسم"), wick=L("Wick", "الذيل")) + "</div>")
        return
    if key in ("live_spy", "sr_live", "ma_live", "rsi_live"):
        sym = st.selectbox(L("Try it on a live chart", "جرّبها على رسم مباشر"), ["SPY", "QQQ", "AAPL", "NVDA", "MSFT", "TSLA"], key=f"ia_{key}")
        df = data.history(sym, "2y")
        if df.empty:
            st.caption(L("Live data unavailable right now.", "البيانات المباشرة غير متاحة حالياً."))
            return
        d = ta.add_all(df)
        cfg = {"live_spy": (d.tail(126), [], []), "sr_live": (d.tail(252), ["Support / Resistance"], []),
               "ma_live": (d, ["SMA 50", "SMA 200"], []), "rsi_live": (d.tail(180), ["SMA 20"], ["RSI", "MACD"])}[key]
        ui.chart(charts.price_chart(cfg[0], "Candles", cfg[1], cfg[2], False, height=460 + 120 * len(cfg[2])), key=f"iac_{key}")
        return
    if key == "position_calc":
        c = st.columns(4)
        acct = c[0].number_input(L("Account ($)", "المحفظة ($)"), 100, 10_000_000, 10000, step=500, key="pc_a")
        risk = c[1].number_input(L("Risk %", "المخاطرة %"), 0.1, 10.0, 1.0, step=0.1, key="pc_r")
        entry = c[2].number_input(L("Entry $", "الدخول $"), 0.5, 100000.0, 50.0, step=0.5, key="pc_e")
        stop = c[3].number_input(L("Stop $", "الوقف $"), 0.1, 100000.0, 48.0, step=0.5, key="pc_s")
        if stop >= entry:
            st.warning(L("Stop must be below entry for a long trade.", "الوقف لازم يكون تحت سعر الدخول في صفقة الشراء."))
            return
        rps = entry - stop
        shares = int(acct * risk / 100 / rps)
        m = st.columns(4)
        m[0].metric(L("Shares to buy", "عدد الأسهم"), f"{shares:,}")
        m[1].metric(L("Position value", "قيمة الصفقة"), f"${shares * entry:,.0f}")
        m[2].metric(L("Max loss", "أقصى خسارة"), f"${shares * rps:,.0f}")
        m[3].metric(L("Target at 2R", "الهدف عند 2R"), f"${entry + 2 * rps:,.2f}")
        return
    if key == "pe_calc":
        c = st.columns(3)
        price = c[0].number_input(L("Share price $", "سعر السهم $"), 1.0, 100000.0, 150.0, step=1.0, key="pe_p")
        eps = c[1].number_input(L("EPS (annual) $", "ربحية السهم السنوية $"), 0.01, 10000.0, 6.0, step=0.1, key="pe_e")
        growth = c[2].number_input(L("Expected growth %", "النمو المتوقع %"), 0.1, 200.0, 15.0, step=1.0, key="pe_g")
        pe = price / eps
        m = st.columns(3)
        m[0].metric("P/E", f"{pe:.1f}")
        m[1].metric("PEG", f"{pe / growth:.2f}")
        m[2].metric(L("Earnings yield", "عائد الأرباح"), f"{eps / price * 100:.2f}%")
        verdict = (L("Looks reasonable relative to growth.", "يبدو معقولاً مقارنة بالنمو.") if pe / growth < 1.5
                   else L("Priced for high expectations.", "مسعّر على توقعات مرتفعة."))
        st.info(verdict, icon=":material/lightbulb:")
        return
    if key == "payoff":
        c = st.columns(4)
        kind = c[0].segmented_control(L("Type", "النوع"), ["call", "put"], default="call", key="po_k",
                                      format_func=lambda k: "Call" if k == "call" else "Put") or "call"
        strike = c[1].slider(L("Strike $", "سعر التنفيذ $"), 50, 150, 100, key="po_s")
        prem = c[2].slider(L("Premium $", "البريميوم $"), 0.5, 15.0, 3.0, step=0.5, key="po_p")
        now = c[3].slider(L("Stock now $", "سعر السهم الآن $"), 50, 150, 100, key="po_n")
        be = strike + prem if kind == "call" else strike - prem
        ui.chart(charts.payoff(kind, float(strike), float(prem), float(now), L("Profit / loss at expiration (1 contract)", "الربح والخسارة عند الانتهاء (عقد واحد)"),
                               (L("Stock price at expiration", "سعر السهم عند الانتهاء"), L("Profit / loss ($)", "الربح / الخسارة ($)"))), key="po_chart")
        m = st.columns(3)
        m[0].metric(L("Cost (max loss)", "التكلفة (أقصى خسارة)"), f"${prem * 100:,.0f}")
        m[1].metric(L("Breakeven", "نقطة التعادل"), f"${be:,.2f}")
        m[2].metric(L("Max profit", "أقصى ربح"), L("Unlimited", "غير محدود") if kind == "call" else f"${(strike - prem) * 100:,.0f}")
        return
    if key == "macro_table":
        rows = [(("CPI inflation above expected", "التضخم أعلى من المتوقع"), ("Yields up, stocks down (growth hit most)", "العوائد ترتفع والأسهم تنخفض (أسهم النمو الأكثر تضرراً)")),
                (("Jobs much stronger than expected", "وظائف أقوى بكثير من المتوقع"), ("Mixed: strong economy, but fewer rate cuts", "مختلط: اقتصاد قوي لكن خفض فائدة أقل")),
                (("Unemployment jumps", "قفزة في البطالة"), ("Recession fears, defensives outperform", "مخاوف ركود وتفوق القطاعات الدفاعية")),
                (("Fed cuts rates", "الفيدرالي يخفض الفائدة"), ("Usually positive for stocks, weaker dollar", "إيجابي عادة للأسهم وضعف الدولار")),
                (("GDP beats", "الناتج المحلي أفضل من المتوقع"), ("Cyclicals and small caps benefit", "استفادة القطاعات الدورية والشركات الصغيرة"))]
        df = pd.DataFrame([{L("Data surprise", "المفاجأة"): L(*a), L("Typical reaction", "رد الفعل المعتاد"): L(*b)} for a, b in rows])
        ui.table(df, wrap=set(df.columns))
        return


# ---------------------------------------------------------------- course view
def _course_view(c):
    cid = c["id"]
    LE.visit(_learning(), cid)
    n = len(c["sections"])
    step = min(max(int(ss.setdefault(f"step_{cid}", 0)), 0), n)
    ss[f"step_{cid}"] = step
    if st.button(L("All courses", "كل الدورات"), icon=":material/arrow_back:"):
        ss.pop("course", None)
        st.query_params.pop("course", None)
        st.rerun()
    lvl = c["level"]
    mins = T.badge(L(str(c["mins"]) + " min", str(c["mins"]) + " دقائق"), "neu", "schedule")
    lessons = T.badge(L(f"{n} lessons + quiz", f"{n} دروس + اختبار"), "acc", "menu_book")
    artwork = A.course_art(c["art"], cid + "h").replace('<svg ', '<svg preserveAspectRatio="xMidYMid slice" ', 1)
    ui.html(f'<section class="ac-course-banner"><div class="ac-course-background" aria-hidden="true">{artwork}</div>'
            f'<div class="ac-course-copy"><h1>{T.esc(L(*c["title"]))}</h1><p>{T.esc(L(*c["tagline"]))}</p>'
            f'<div class="ac-course-meta">{T.badge(L(*lvl), LEVEL_KIND.get(lvl[0], "neu"), "signal_cellular_alt")}{mins}{lessons}</div></div></section>')
    with st.expander(L("Lesson map & study notes", "خريطة الدروس وملخص المراجعة")):
        for i, section in enumerate(c["sections"]):
            reached = f"{cid}:{i}" in _learning()["lessons"] or cid in ss.get("completed", set())
            st.button(f"{'✓' if reached else f'{i+1:02d}'} · {L(section[0], section[1])}", key=f"lesson_jump_{cid}_{i}",
                      on_click=_jump_lesson, args=(cid, i), width="stretch")
        _download_notes(c, "lesson")
    _course_videos(c)
    ui.html('<div class="steps">' + "".join(f'<span class="{"on" if i <= step else ""}"></span>' for i in range(n + 1)) + "</div>")
    rtl = " rtl" if is_ar() else ""
    if step < n:
        h_en, h_ar, b_en, b_ar, t_en, t_ar, viz = c["sections"][step]
        with st.container(key="academy_lesson_panel"):
            ui.html(f'<div class="lesson{rtl}"><div class="muted" style="font-size:.8rem">{L(f"Lesson {step + 1} of {n}", f"الدرس {step + 1} من {n}")}</div>'
                    f'<h3>{T.esc(L(h_en, h_ar))}</h3><p>{T.esc(L(b_en, b_ar))}</p>'
                    f'<div class="take">{T.icon("lightbulb", T.CYAN)} <b>{L("Key takeaway", "الخلاصة")}:</b> {T.esc(L(t_en, t_ar))}</div></div>')
            if viz:
                ui.sec("touch_app", "Interactive", "تفاعلي")
                interactive(viz)
            if step < len(c["quiz"]):
                _checkpoint(c, step)
            with st.container(key="academy_lesson_navigation"):
                a, _, b = st.columns([1, 2, 1])
                if step > 0 and a.button(L("Back", "السابق"), icon=":material/chevron_left:", width="stretch"):
                    ss[f"step_{cid}"] = step - 1
                    st.rerun()
                if b.button(L("Next", "التالي") if step < n - 1 else L("Take the quiz", "ابدأ الاختبار"), icon=":material/chevron_right:",
                            type="primary", width="stretch"):
                    LE.lesson(_learning(), cid, step)
                    ss[f"step_{cid}"] = step + 1
                    st.rerun()
        return
    # ---- quiz
    st.caption(L("Pass with at least 80%. You can review and try again.", "الاجتياز من 80%. تقدر تراجع وتحاول مرة ثانية."))
    ui.sec("quiz", "Quick quiz", "اختبار سريع")
    answers = []
    for i, (q_en, q_ar, opts, ans, _, _) in enumerate(c["quiz"]):
        answers.append(st.radio(f"{i + 1}. {L(q_en, q_ar)}", list(range(len(opts))), index=None, key=f"q_{cid}_{i}",
                                format_func=lambda k, o=[L(*option) for option in opts]: o[k]))
    a, b = st.columns([1, 1])
    if a.button(L("Back to lessons", "رجوع للدروس"), icon=":material/chevron_left:", width="stretch"):
        ss[f"step_{cid}"] = n - 1
        st.rerun()
    if b.button(L("Check answers", "تحقق من الإجابات"), type="primary", icon=":material/fact_check:", width="stretch"):
        if any(answer is None for answer in answers):
            st.warning(L("Answer every question before checking.", "جاوب على كل الأسئلة قبل التحقق."))
        else:
            ss[f"checked_{cid}"] = list(answers)
            _learning()["quizzes"][cid] = {"score": sum(got == q[3] for got, q in zip(answers, c["quiz"])), "total": len(c["quiz"])}
    if ss.get(f"checked_{cid}") == answers:
        score = 0
        for i, ((q_en, q_ar, opts, ans, w_en, w_ar), got) in enumerate(zip(c["quiz"], answers)):
            ok = got == ans
            score += ok
            ui.html(f'<div class="check{rtl}">{T.ico("check", "pos") if ok else T.ico("close", "neg")}<div><b>{i + 1}. {T.esc(L(*opts[ans]))}</b> '
                    f'<span class="muted">· {T.esc(L(w_en, w_ar))}</span></div></div>')
        total = len(c["quiz"])
        if score >= math.ceil(total * 0.8):
            ss.setdefault("completed", set()).add(cid)
            st.success(L(f"Great job: {score}/{total}. Course completed!", f"أحسنت: {score}/{total}. أكملت الدورة!"), icon=":material/workspace_premium:")
        else:
            st.warning(L(f"{score}/{total}. Review the lessons and try again.", f"{score}/{total}. راجع الدروس وحاول مرة أخرى."), icon=":material/replay:")
        sequence = ss.get("ac_active_path") or [x["id"] for x in A.COURSES]
        if cid not in sequence:
            sequence = [x["id"] for x in A.COURSES]
        idx = sequence.index(cid)
        if idx + 1 < len(sequence):
            nxt = _course(sequence[idx + 1])
            ui.html(f'<div style="margin:12px 0 6px">{L("Next course", "الدورة التالية")}:</div>')
            course_cards([nxt], "nxt", 3)


def dashboard():
    """Learning dashboard: overall ring, progress per level (level colors), completed vs in progress, continue card."""
    done = set(ss.get("completed", set())) & {c["id"] for c in A.COURSES}
    prog = [c for c in A.COURSES if _status(c["id"]) == "prog"]
    total = len(A.COURSES)
    pct = len(done) / total * 100 if total else 0
    order = ["Beginner", "Essential", "Intermediate", "Advanced"]
    by = {lv: [c for c in A.COURSES if c["level"][0] == lv] for lv in order}
    lv_names = {c["level"][0]: c["level"] for c in A.COURSES}
    c1, c2, c3 = st.columns([0.95, 1.1, 1.35])
    with c1:
        ui.html(f'<div class="dcard"><div class="dt">{L("Your progress", "تقدمك")}</div>'
                f'{T.ring(pct, 160, T.ACCENT, f"{pct:.0f}%", L(f"{len(done)} of {total} courses", f"{len(done)} من {total} دورات"))}'
                f'<div style="display:flex;justify-content:center;gap:6px;margin-top:10px;flex-wrap:wrap">'
                f'{T.badge(L(f"{len(done)} completed", f"{len(done)} مكتملة"), "up", "check_circle")}'
                f'{T.badge(L(f"{len(prog)} in progress", f"{len(prog)} قيد التعلم"), "gold", "timelapse")}</div></div>')
    with c2:
        rows = []
        for lv in order:
            cs = by[lv]
            if not cs:
                continue
            d_ = sum(1 for c in cs if c["id"] in done)
            p_ = sum(1 for c in cs if _status(c["id"]) == "prog")
            color = LEVEL_COLOR[lv]
            w1, w2 = d_ / len(cs) * 100, p_ / len(cs) * 100
            rows.append(f'<div class="lvl"><div class="t"><span>{T.badge(L(*lv_names[lv]), LEVEL_KIND[lv], "signal_cellular_alt")}</span>'
                        f'<span class="num">{d_}/{len(cs)}</span></div><div class="trk" style="display:flex">'
                        f'<span style="width:{w1:.0f}%;background:{color}"></span><span style="width:{w2:.0f}%;background:{color};opacity:.4"></span></div></div>')
        ui.html(f'<div class="dcard"><div class="dt">{L("Levels", "المستويات")}</div>{"".join(rows)}'
                f'<div class="muted" style="font-size:.72rem;margin-top:8px">{L("Solid = completed · light = in progress", "اللون الكامل = مكتمل · الفاتح = قيد التعلم")}</div></div>')
    with c3:
        lv_list = [lv for lv in order if by[lv]]
        ui.chart(charts.level_progress([L(*lv_names[lv]) for lv in lv_list],
                                       [sum(1 for c in by[lv] if c["id"] in done) for lv in lv_list],
                                       [sum(1 for c in by[lv] if _status(c["id"]) == "prog") for lv in lv_list],
                                       [len(by[lv]) for lv in lv_list], [LEVEL_COLOR[lv] for lv in lv_list],
                                       L("Completed vs in progress", "المكتملة مقابل قيد التعلم"),
                                       (L("Completed", "مكتملة"), L("In progress", "قيد التعلم"), L("Not started", "لم تبدأ"))), key="ac_levels")
    nxt = prog[0] if prog else next((c for c in A.COURSES if c["id"] not in done), None)
    if nxt:
        a, b = st.columns([3, 1], vertical_alignment="center")
        a.markdown(f'<div class="card" style="margin:0;display:flex;gap:12px;align-items:center">{T.ico("play_arrow", "acc")}'
                   f'<div><div class="muted" style="font-size:.75rem">{L("Continue learning", "تابع التعلم") if prog else L("Start here", "ابدأ من هنا")}</div>'
                   f'<b>{T.esc(L(*nxt["title"]))}</b></div></div>', unsafe_allow_html=True)
        b.button(L("Open course", "افتح الدورة"), icon=":material/play_circle:", type="primary", key="ac_cont", on_click=_open_course,
                 args=(nxt["id"],), width="stretch")


def _jump_lesson(cid, step):
    LE.visit(_learning(), cid)
    ss[f"step_{cid}"] = step


def _checkpoint(c, step):
    question = c["quiz"][step]
    q_en, q_ar, opts, correct, why_en, why_ar = question
    with st.container(border=True):
        st.markdown("#### " + L("Try before you continue", "جرّب قبل تكمل"))
        got = st.radio(L(q_en, q_ar), list(range(len(opts))), index=None,
                       format_func=lambda i, labels=[L(*o) for o in opts]: labels[i], key=f"checkpoint_{c['id']}_{step}")
        if got is not None:
            if got == correct:
                st.success(L("Correct. ", "صحيح. ") + L(why_en, why_ar))
            else:
                st.warning(L("Try again. ", "جرّب مرة ثانية. ") + L(why_en, why_ar))


def _study_notes(c):
    lang = 1 if is_ar() else 0
    lines = ["# " + c["title"][lang], c["tagline"][lang], ""]
    for section in c["sections"]:
        lines.extend(["## " + section[lang], section[2+lang], "", section[4+lang], ""])
    lines.extend(["## " + L("Check your understanding", "راجع فهمك")])
    for q in c["quiz"]:
        lines.extend([q[lang], L("Answer: ", "الإجابة: ") + q[2][q[3]][lang], q[4+lang], ""])
    lines.append(L("Educational examples, not investment recommendations.", "أمثلة تعليمية وليست توصيات استثمارية."))
    return "\n".join(lines)


def _download_notes(c, namespace):
    st.download_button(L("Download study notes", "حمّل ملخص المراجعة"), _study_notes(c),
                       file_name=f"tura-{c['id']}-{'ar' if is_ar() else 'en'}.md",
                       mime="text/markdown", key=f"notes_{namespace}_{c['id']}")


def _academy_hero():
    beginner_count = sum(c["level"][0] == "Beginner" for c in A.COURSES)
    direction = "rtl" if is_ar() else "ltr"
    ui.html(f'<section class="ac-campus" dir="{direction}"><div class="ac-brand-lockup" dir="ltr">'
            f'{T.brand(None, "acb", pro=None, color="#F2F5FF", label="TURA")}<span>ACADEMY</span></div>'
            f'<div class="ac-campus-content"><div><div class="ac-kicker">{L("BUILD KNOWLEDGE. ONE IDEA AT A TIME.", "معرفة تبنيها، فكرة وراء فكرة.")}</div>'
            f'<h1>{L("Invest in your understanding.", "استثمر في فهمك.")}</h1>'
            f'<p>{L("Short lessons. Clear examples. Practice that makes it click.", "دروس قصيرة، أمثلة واضحة، وتجارب تخلي الفكرة تثبت.")}</p>'
            f'<div class="ac-meta"><span>{len(A.COURSES)} {L("courses", "دورة")}</span><span>{beginner_count} {L("for beginners", "للمبتدئين")}</span>'
            f'<span>{L("Learn · Practise · Check", "افهم · جرّب · اختبر")}</span></div></div>'
            f'<div class="ac-campus-art" aria-hidden="true">{AV.MARK}<span>01 / 02 / 03</span></div></div></section>')


def _dashboard_metrics(info):
    cards = [
        ("school", L("Courses completed", "دورات أكملتها"), str(len(info["done"])), L(f"of {len(A.COURSES)} courses", f"من {len(A.COURSES)} دورة"), "#8caaff"),
        ("menu_book", L("Lessons covered", "دروس تعلّمتها"), str(info["lessons"]), L(f"of {info['total_lessons']} lessons", f"من {info['total_lessons']} درس"), "#78d8d4"),
        ("fact_check", L("Quiz accuracy", "دقّة إجاباتك"), "—" if info["accuracy"] is None else str(info["accuracy"])+"%",
         L("Take your first quiz", "ابدأ أول اختبار") if info["accuracy"] is None else L(f"Latest result in {info['quiz_count']} quizzes", f"آخر نتيجة في {info['quiz_count']} اختبارات"), "#ba9af4"),
        ("local_fire_department", L("Learning streak", "أيامك المتواصلة"), str(info["streak"]), L("Days with a lesson or challenge", "أيام فيها درس أو تحدّي"), "#f2bd7a")]
    ui.html('<div class="ac-metrics">' + "".join(
        f'<div class="ac-metric" style="--ac-tone:{color}"><div class="ac-metric-top">{T.icon(icon)}<span>{label}</span></div>'
        f'<strong>{value}</strong><small>{hint}</small></div>' for icon, label, value, hint, color in cards) + '</div>')


def _daily_challenge():
    chosen = LE.daily_question(A.COURSES)
    if not chosen:
        return
    c, _, q = chosen
    day = LE.today().isoformat()
    with st.container(key="academy_daily", border=True):
        ui.html(f'<div class="ac-section-head"><div><div class="ac-kicker">{L("A MINUTE TO THINK", "دقيقة تختبر فيها فهمك")}</div>'
                f'<h3>{L("Your daily challenge", "تحدّيك اليومي")}</h3></div>{T.icon("bolt", "#f2bd7a")}</div>')
        solved = _learning()["activity"].get(day, {}).get("challenge", False)
        got = st.radio(L(q[0], q[1]), list(range(len(q[2]))), index=None,
                       format_func=lambda i, labels=[L(*o) for o in q[2]]: labels[i], key="ac_daily_"+day)
        if got is not None:
            if got == q[3]:
                LE.challenge(_learning())
                if not solved:
                    st.rerun()
                st.success(L("Correct! ", "صحيح! ") + L(q[4], q[5]))
            else:
                st.info(L("Try again. ", "جرّب مرة ثانية. ") + L(q[4], q[5]))
        elif solved:
            st.caption(L("You have already completed today's challenge.", "أكملت تحدّي اليوم. تقدر تراجعه مرة ثانية."))
        st.button(L("Explore this concept", "افهم الفكرة أكثر"), key="ac_daily_course", on_click=_open_course, args=(c["id"],))


def _week_goal():
    meta = _learning()
    info = _learning_stats()
    with st.container(key="academy_week", border=True):
        ui.html(f'<div class="ac-section-head"><h3>{L("Your weekly rhythm", "وتيرة تعلّمك")}</h3>{T.icon("calendar_month", "#ba9af4")}</div>')
        selected = st.segmented_control(L("Lessons per week", "دروس بالأسبوع"), [3, 5, 10],
                    default=meta["goal"], key="ac_week_goal", format_func=lambda n: L(f"{n} lessons", f"{n} دروس"))
        if selected:
            meta["goal"] = selected
        goal = meta["goal"]
        ui.html(f'<div class="ac-goal-value"><strong>{info["weekly"]}</strong><span>/ {goal} {L("lessons this week", "دروس هالأسبوع")}</span></div>')
        st.progress(min(info["weekly"] / goal, 1.0))
        if info["weekly"] >= goal:
            st.caption(L("Weekly goal reached. Keep going at your own pace.", "وصلت هدفك الأسبوعي. كمّل على راحتك."))
        else:
            st.caption(L(f"{goal-info['weekly']} more lessons to reach your goal.", f"باقي {goal-info['weekly']} دروس وتوصل لهدفك."))
        names = [("Mon", "اثنين"),("Tue", "ثلاثاء"),("Wed", "أربعاء"),("Thu", "خميس"),("Fri", "جمعة"),("Sat", "سبت"),("Sun", "أحد")]
        bars = []
        maximum = max([len(row["lessons"]) for row in info["activity"]] + [3])
        for row in info["activity"]:
            count = len(row["lessons"])
            label = L(*names[row["day"].weekday()])
            hint = f'{row["day"].isoformat()} · {count} ' + L("lessons", "دروس") + (" · "+L("challenge completed", "تحدّي مكتمل") if row["challenge"] else "")
            bars.append(f'<div class="ac-day" title="{T.esc(hint)}"><small>{count}</small><div class="ac-day-track"><span style="height:{max(4, count / maximum * 100):.0f}%" class="{"active" if count else ""}"></span></div>'
                        f'<span>{label}</span><i class="{"solved" if row["challenge"] else ""}" aria-label="{T.esc(hint)}"></i></div>')
        ui.html(f'<div class="ac-activity-label">{L("LAST 7 DAYS · LESSONS", "آخر ٧ أيام · الدروس")}</div><div class="ac-activity">{"".join(bars)}</div>')
        st.caption(L("New lessons count once. The dot marks a daily challenge. Week starts Monday.", "كل درس جديد ينحسب مرة. النقطة تعني تحدّي مكتمل. الأسبوع يبدأ الاثنين."))


def _academy_home():
    info = _learning_stats()
    ui.html(f'<div class="ac-section-head ac-dash-heading"><div><h2>{L("Your learning dashboard", "لوحة تعلّمك")}</h2>'
            f'<p>{L("A clear next step, and a little progress every day.", "خطوتك الجاية واضحة، وتقدّمك قدّامك كل يوم.")}</p></div>'
            f'<span class="ac-date" dir="ltr">{LE.today().strftime("%d / %m / %Y")}</span></div>')
    _dashboard_metrics(info)
    last = _course(_learning().get("last"))
    active = last if last and _status(last["id"]) != "done" else next((c for c in A.COURSES if _status(c["id"]) == "prog"), None)
    nxt = active or next((c for c in A.COURSES if _status(c["id"]) != "done"), None)
    left, right = st.columns([1.65, 1], gap="large")
    with left:
        with st.container(key="academy_resume", border=True):
            if nxt:
                cid = nxt["id"]
                step = min(int(ss.get(f"step_{cid}", 0) or 0), len(nxt["sections"]))
                reading_badge = T.badge(L(str(nxt["mins"])+" min reading", str(nxt["mins"])+" دقائق قراءة"), "neu", "schedule")
                ui.html(f'<div class="ac-resume-art">{A.course_art(nxt["art"], cid+"resume")}<span class="ac-resume-label">'
                        f'{T.icon("play_circle")} {L("PICK UP WHERE YOU LEFT OFF" if active else "YOUR FIRST STEP", "كمّل من مكانك" if active else "خطوتك الأولى")}</span></div>'
                        f'<div class="ac-resume-copy"><h3>{T.esc(L(*nxt["title"]))}</h3><p>{T.esc(L(*nxt["tagline"]))}</p>'
                        f'<div class="ac-resume-meta">{T.badge(L(*nxt["level"]), LEVEL_KIND[nxt["level"][0]], "school")}'
                        f'{reading_badge}</div></div>')
                lesson_label = L("Ready for the quiz", "جاهز للاختبار") if step == len(nxt["sections"]) else L(nxt["sections"][step][0], nxt["sections"][step][1])
                st.caption(L("Next: ", "التالي: ") + lesson_label)
                st.progress(step / (len(nxt["sections"]) + 1), text=L(f"{step}/{len(nxt['sections'])} lessons · quiz follows", f"{step}/{len(nxt['sections'])} دروس · بعدها الاختبار"))
                st.button(L("Continue learning" if active else "Start your first lesson", "كمّل التعلّم" if active else "ابدأ أول درس"), type="primary",
                          icon=":material/play_arrow:", key="ac_beginner_start", on_click=_open_course, args=(cid,), width="stretch")
            else:
                st.success(L("You completed every course! Keep your knowledge fresh with a daily challenge.", "أكملت كل الدورات! ثبّت معرفتك بالتحدّي اليومي."))
        _daily_challenge()
    with right:
        _week_goal()
        with st.container(key="academy_milestones", border=True):
            ui.html(f'<div class="ac-section-head"><h3>{L("Small wins, real progress", "إنجازاتك خطوة بخطوة")}</h3>{T.icon("workspace_premium", "#f2bd7a")}</div>')
            achievements = [
                (info["lessons"] >= 1, "menu_book", L("First idea learned", "تعلّمت أول فكرة"), L("Complete one lesson", "أكمل درس واحد")),
                (len(info["done"]) >= 1, "school", L("First course completed", "أكملت أول دورة"), L("Pass a course quiz", "اجتز اختبار دورة")),
                (info["streak"] >= 3, "local_fire_department", L("Three days in a row", "ثلاثة أيام متواصلة"), L("A lesson or challenge each day", "درس أو تحدّي كل يوم")),
                (len(info["done"]) >= 5, "workspace_premium", L("Five courses completed", "أكملت خمس دورات"), L("Build a solid foundation", "ابنِ أساس قوي"))]
            ui.html('<div class="ac-wins">' + "".join(f'<div class="ac-win {"earned" if earned else ""}">{T.icon(icon)}<div><b>{title}</b><small>{hint}</small></div>'
                    f'{T.icon("check_circle" if earned else "radio_button_unchecked")}</div>' for earned, icon, title, hint in achievements) + '</div>')
    ui.html(f'<div class="ac-section-head"><div><div class="ac-kicker">{L("LEARN WITH A DIRECTION", "تعلّم باتجاه واضح")}</div><h2>{L("Choose your learning path", "اختر مسار تعلّمك")}</h2></div></div>')
    tracks = [
        ("01", L("Understand the market", "افهم السوق"), L("Ownership, price and company value", "الملكية والسعر وقيمة الشركة"), ["basics", "price_value", "marketcap_split"]),
        ("02", L("Know your numbers", "اعرف أرقامك"), L("Returns, fees and recovering from losses", "العوائد والرسوم وتعويض الخسائر"), ["total_return", "fees_drag", "loss_recovery"]),
        ("03", L("Make informed decisions", "قرارات بفهم"), L("Execution, evidence and warning signs", "التنفيذ والدليل وعلامات التحذير"), ["spread_basics", "limit_practice", "scam_signals"])]
    for col, (num, title, desc, ids) in zip(st.columns(3), tracks):
        with col, st.container(key="academy_track_"+num, border=True):
            ui.html(f'<div class="ac-track-number">{num}<span>{L("STARTER PATH", "مسار البداية")}</span>{T.icon({"01":"candlestick_chart","02":"calculate","03":"verified"}[num])}</div>'
                    f'<h3 class="ac-track-title">{title}</h3><p class="ac-track-desc">{desc}</p>')
            completed = sum(_status(cid) == "done" for cid in ids)
            st.progress(completed / len(ids), text=L(f"{completed}/{len(ids)} complete · {sum(_course(cid)['mins'] for cid in ids)} min reading", f"{completed}/{len(ids)} مكتمل · {sum(_course(cid)['mins'] for cid in ids)} دقيقة قراءة"))
            target = next((cid for cid in ids if _status(cid) != "done"), ids[0])
            st.button(L("Review path" if completed == len(ids) else "Start / continue", "راجع المسار" if completed == len(ids) else "ابدأ أو أكمل"), key="ac_track_"+num,
                      on_click=_start_path, args=(ids, target), width="stretch")
    ui.html(f'<div class="ac-section-head"><div><div class="ac-kicker">{L("SHORT, PRACTICAL, WORTH YOUR TIME", "قصيرة، عملية، وعلى راحتك")}</div>'
            f'<h2>{L("Your next discoveries", "أفكار تستكشفها بعدها")}</h2></div></div>')
    recommended = [c for c in A.COURSES if c.get("micro") and _status(c["id"]) != "done" and (not nxt or c["id"] != nxt["id"])]
    recommended += [c for c in A.COURSES if c not in recommended and c.get("micro")]
    course_cards(recommended[:3], prefix="crs_featured")
    with st.expander(L("Plan a complete learning path", "رتّب مسارك التعليمي الكامل")):
        _learning_path()
    st.caption(L("Progress, goals and activity are kept in this browser on this device. Activity starts when you complete new lessons or a daily challenge.",
                 "تقدّمك وأهدافك ونشاطك محفوظة بهالمتصفح على هالجهاز. النشاط يبدأ من الدروس الجديدة اللي تكملها أو التحدّي اليومي."))


def _materials():
    st.subheader(L("Your study desk", "مكتبك الدراسي"))
    st.caption(L("Review a concept, practise with flashcards, or download a course summary.", "راجع فكرة، تمرّن ببطاقات المراجعة، أو حمّل ملخص الدورة."))
    ui.html('<div class="ac-resource-strip">'+"".join(
        f'<div>{T.icon(icon)}<span><b>{title}</b><small>{desc}</small></span></div>' for icon, title, desc in [
        ("description",L("Course summaries","ملخصات الدورات"),L("Read & download","راجع وحمّل")),
        ("style",L("Active recall","بطاقات المراجعة"),L("Think, then reveal","فكّر، بعدها اكشف الحل")),
        ("play_circle",L("Video library","مكتبة الفيديو"),L("Watch, then practise","شاهد، بعدها طبّق"))])+'</div>')
    kind = st.segmented_control(L("Material type", "نوع المادة"), ["notes", "cards", "video"], default="notes", key="ac_material_type",
                                format_func=lambda v, labels={"notes":L("Study notes", "ملخصات"),"cards":L("Flashcards", "بطاقات مراجعة"),"video":L("Videos", "فيديوهات")}:labels[v]) or "notes"
    if kind == "video":
        _video_library()
        return
    selected = st.selectbox(L("Course", "الدورة"), [c["id"] for c in A.COURSES], format_func=lambda cid, labels={c["id"]:L(*c["title"]) for c in A.COURSES}:labels[cid], key="ac_material_course")
    c = _course(selected)
    if kind == "notes":
        for i, section in enumerate(c["sections"], 1):
            with st.expander(f"{i:02d} · {L(section[0],section[1])}", expanded=i==1):
                st.write(L(section[2],section[3]))
                st.info(L(section[4],section[5]))
        _download_notes(c, "materials")
        st.button(L("Practise in this course", "طبّق داخل الدورة"), key="material_open", on_click=_open_course, args=(selected,))
    else:
        index = st.selectbox(L("Review card", "بطاقة المراجعة"), list(range(len(c["quiz"]))), format_func=lambda i: str(i+1), key="ac_flash_"+selected)
        question = c["quiz"][index]
        with st.container(border=True):
            st.markdown("### " + L(question[0],question[1]))
            st.caption(L("Think of your answer before revealing it.", "فكّر بإجابتك قبل تكشف الحل."))
            if st.checkbox(L("Reveal answer", "اكشف الإجابة"), key=f"reveal_{selected}_{index}"):
                st.success(L(*question[2][question[3]]))
                st.write(L(question[4],question[5]))


def _learning_path():
    paths = {
        "start": (L("Start investing", "أبدأ الاستثمار"), ["money_foundations", "goals", "basics", "broker_safety", "diversification_basics", "funds", "compounding", "returns_costs", "inflation", "allocation"]),
        "research": (L("Analyse companies", "أحلل الشركات"), ["statements", "value", "quality", "valuation_scenarios"]),
        "trade": (L("Build a trading process", "أبني منهج تداول"), ["execution", "candles", "risk", "behaviour", "robustness"]),
    }
    goal = st.selectbox(L("My learning goal", "هدفي من التعلم"), list(paths), format_func=lambda x:paths[x][0], key="ac_goal")
    minutes=st.slider(L("Study minutes per week", "دقائق الدراسة بالأسبوع"),10,120,30,step=10,key="ac_minutes")
    courses=[_course(cid) for cid in paths[goal][1] if _course(cid)]
    remaining=[c for c in courses if _status(c["id"])!="done"]
    total_minutes=sum(c["mins"] for c in remaining)
    st.info(L(f"{len(remaining)} courses remaining · about {total_minutes} reading minutes · {math.ceil(total_minutes/minutes)} study weeks. Allow extra time for practice.",
              f"باقي {len(remaining)} دورات · تقريبًا {total_minutes} دقيقة قراءة · {math.ceil(total_minutes/minutes)} أسابيع دراسة. خصص وقت إضافي للتطبيق."))
    if remaining:
        st.button(L("Start / continue this path", "ابدأ أو أكمل المسار"),type="primary",key="ac_path_start",on_click=_start_path,args=([c["id"] for c in courses],remaining[0]["id"]))
    for i,c in enumerate(courses,1):
        st.write(f"{i:02d} · {L(*c['title'])} " + ("✓" if _status(c['id'])=="done" else ""))


def _video_player(v):
    st.markdown("#### " + L(*v["title"]))
    st.caption(v["creator"] + " · " + ("العربية" if v["language"] == "ar" else "English"))
    st.write(L(*v["note"]))
    st.video(v["url"])
    st.link_button(L("Open on YouTube", "افتح في يوتيوب"), v["url"])
    if v["language"] == "en":
        st.caption(L("English audio. Subtitle availability depends on the publisher.",
                     "الصوت إنجليزي. توفر الترجمة يعتمد على ناشر الفيديو."))


def _course_videos(c):
    related = [v for v in A.VIDEOS if c["id"] in v["courses"]]
    if not related:
        return
    related.sort(key=lambda v: v["language"] != ("ar" if is_ar() else "en"))
    with st.expander(L("Watch an explanation", "شاهد شرح بالفيديو"), icon=":material/play_circle:"):
        chosen = st.selectbox(L("Choose a video", "اختر الفيديو"), range(len(related)),
                             format_func=lambda i, labels=[L(*v["title"]) for v in related]: labels[i],
                             key="ac_course_video_" + c["id"])
        _video_player(related[chosen])


def _video_library():
    st.subheader(L("Learn by watching", "تعلّم بالمشاهدة"))
    st.caption(L("Selected explanations from Thameen and Khan Academy. Start with a topic, then practise in its course.",
                 "شروحات مختارة من ثمين وKhan Academy. اختر الموضوع، وبعد المشاهدة طبّق بدورته."))
    language = st.radio(L("Video language", "لغة الفيديو"), ["all", "ar", "en"], horizontal=True,
                        format_func=lambda x, labels={"all": L("All", "الكل"), "ar": "العربية", "en": "English"}: labels[x],
                        key="ac_video_language")
    items = [v for v in A.VIDEOS if language == "all" or v["language"] == language]
    selected = st.selectbox(L("Choose a video", "اختر الفيديو"), [v["id"] for v in items],
                           format_func=lambda x, labels={v["id"]: L(*v["title"]) for v in items}: labels[x],
                           key="ac_video_pick_" + language)
    v = next(v for v in items if v["id"] == selected)
    _video_player(v)
    st.caption(L("Continue with the related courses", "كمّل مع الدورات المرتبطة"))
    course_cards([_course(cid) for cid in v["courses"] if _course(cid)], prefix="crs_video")


def page_academy():
    st.logo(AV.academy_wordmark(T.brand(None, "acsidebar", pro=None)), icon_image=AV.MARK, size="large")
    ui.html(AV.CSS)
    _progress_sync()                                 # the progress this browser keeps
    try:
        _page_academy()
    finally:
        _progress_sync()                             # and what changed on this run, written back


def _page_academy():
    with st.container(key="academy_root"):
        cid = ss.get("course") or st.query_params.get("course")
        c = _course(cid) if cid else None
        if c:
            ss["course"] = c["id"]
            _course_view(c)
            st.caption(L("Course photography: Unsplash · illustrative images.", "صور الدورات: Unsplash · صور توضيحية."))
            with st.expander(L("Further learning", "قراءات إضافية")):
                for label, url in A.COURSE_SOURCES.get(c["id"], []):
                    st.markdown(f"[{label}]({url})")
                st.markdown("[Investor.gov — investing education](https://www.investor.gov/introduction-investing)\n\n"
                            "[Financial Industry Regulatory Authority — bonds](https://www.finra.org/investors/investing/investment-products/bonds)")
            ui.foot()
            return
        _academy_hero()
        home, catalog, materials, labs, progress = st.tabs([L("Dashboard", "لوحة التعلّم"), L("Course library", "مكتبة الكورسات"),
            L("Study materials", "مواد التعلّم"), L("Practice labs", "مختبرات التطبيق"), L("My progress", "تقدمي")])
        with home:
            _academy_home()
        with catalog:
            st.subheader(L("Find your next small step", "اختر خطوتك الجاية"))
            st.caption(L("Beginner first. Filter by level, reading time or progress.", "المبتدئ أولًا. صفِّ حسب المستوى أو وقت القراءة أو تقدمك."))
            a,b=st.columns([3,1])
            query=a.text_input(L("Search courses", "ابحث عن دورة"),placeholder=L("e.g. bonds, cash flow, risk", "مثل: السندات، النقد، المخاطرة"),key="ac_search").strip().casefold()
            state=b.selectbox(L("Show", "اعرض"),["all","new","progress","done"],key="ac_status",format_func=lambda x, labels={"all":L("All courses","كل الدورات"),"new":L("New additions","المضافة حديثًا"),"progress":L("In progress","قيد التعلم"),"done":L("Completed","المكتملة")}:labels[x])
            lvl=st.radio(L("Level", "المستوى"),list(LEVELS),index=0,horizontal=True,key="ac_lvl",format_func=lambda k, labels={key:L(*val) for key,val in LEVELS.items()}:labels[k]) or "all"
            duration=st.select_slider(L("Maximum reading time", "أقصى وقت للقراءة"),options=[4,6,8],value=8,key="ac_duration")
            sorting = st.selectbox(L("Sort courses", "ترتيب الدورات"), ["level", "short", "new"], key="ac_sort",
                                  format_func=lambda v, labels={"level":L("Beginner first", "المبتدئ أولًا"),"short":L("Shortest first", "الأقصر أولًا"),"new":L("Newest first", "الأحدث أولًا")}:labels[v])
            courses=[c for c in A.COURSES if c["mins"]<=duration and (lvl=="all" or c["level"][0]==lvl)
                     and (not query or query in " ".join(c["title"]+c["tagline"]).casefold())
                     and (state=="all" or state=="new" and c.get("new") or state=="progress" and _status(c["id"])=="prog" or state=="done" and _status(c["id"])=="done")]
            if sorting == "short":
                courses.sort(key=lambda c: (c["mins"], A.LEVEL_ORDER.index(c["level"][0])))
            elif sorting == "new":
                courses.sort(key=lambda c: (not c.get("new", False), A.LEVEL_ORDER.index(c["level"][0])))
            st.caption(L(f"{len(courses)} courses · choose a card to begin",f"{len(courses)} دورة · اختر بطاقة للبدء"))
            if courses:
                signature = (query, state, lvl, duration, sorting)
                if ss.get("ac_filter_signature") != signature:
                    ss["ac_page"] = 1
                    ss["ac_filter_signature"] = signature
                page_count = math.ceil(len(courses)/9)
                page = st.selectbox(L("Page", "الصفحة"), list(range(1, page_count+1)), key="ac_page",
                                    format_func=lambda x, labels={i:L(f"Page {i} of {page_count}",f"صفحة {i} من {page_count}") for i in range(1,page_count+1)}:labels[x])
                courses = courses[(page-1)*9:page*9]
                descriptions = {
                    "Beginner": ("Start from zero: money, markets and your first portfolio.", "من الصفر: فلوسك، السوق، وأول محفظة لك."),
                    "Essential": ("Build the skills every investor needs.", "مهارات أساسية يحتاجها كل مستثمر."),
                    "Intermediate": ("Go deeper into analysis and market behaviour.", "تعمّق بالتحليل وفهم حركة الأسواق."),
                    "Advanced": ("Explore derivatives, valuation scenarios and strategy testing.", "المشتقات وسيناريوهات التقييم واختبار الاستراتيجيات.")}
                if sorting != "level":
                    course_cards(courses)
                for index, level in enumerate(A.LEVEL_ORDER if sorting == "level" else [], 1):
                    group = [c for c in courses if c["level"][0] == level]
                    if group:
                        st.subheader(f"{index:02d} · {L(*LEVELS[level])} · {len(group)}")
                        st.caption(L(*descriptions[level]))
                        course_cards(group)
            else: st.info(L("No matching courses. Try another search or level.","ما فيه دورات تطابق الاختيار. غيّر البحث أو المستوى."))
        with materials:
            _materials()
        with catalog:
            with st.expander(L("Photo credits", "مصادر الصور")):
                for photo in AV.PHOTOS.values():
                    st.markdown(f'[{photo["credit"]} · Unsplash]({photo["page"]})')
        with labs:
            ui.html('<div class="ac-note">'+L("Change the assumptions and see the result. These labs use hypothetical data and work without live market feeds.","غيّر الافتراضات وشوف النتيجة. المختبرات تستخدم بيانات افتراضية وتعمل بدون أسعار سوق مباشرة.")+'</div>')
            all_labs = {**AM.LABS, **AL.LABS}
            selected=st.selectbox(L("Choose a lab", "اختر المختبر"),list(all_labs),format_func=lambda x, labels={key:L(*val) for key,val in all_labs.items()}:labels[x],key="ac_lab")
            (AM.render if selected in AM.LABS else AL.render)(selected,namespace="hub")
        with progress:
            ui.safe(dashboard)
            st.caption(L("Your progress is kept in this browser on this device (no account needed). Another device, or clearing the browser's "
                         "data, starts fresh.",
                         "تقدمك محفوظ في هالمتصفح على هالجهاز (بدون حساب). أي جهاز ثاني أو مسح بيانات المتصفح يبدأ من جديد."))
        ui.foot()


def page_glossary():
    ui.header("menu_book", "Glossary", "قاموس المصطلحات",
              "Key investing and trading terms explained simply.", "أهم مصطلحات الاستثمار والتداول بشرح مبسط.")
    q = st.text_input(L("Search a term", "ابحث عن مصطلح"), "", placeholder=L("e.g. RSI, spread, option", "مثال: RSI، السبريد، الخيارات")).strip().lower()
    import terms
    allg = sorted(terms.glossary(A.GLOSSARY), key=lambda g: (g[1] if is_ar() else g[0]).lower())
    items = [g for g in allg if not q or q in " ".join(g).lower()]
    rtl = " rtl" if is_ar() else ""
    st.caption(L(f"{len(allg)} terms. Anywhere on the site, press the small ? next to a term to read it there.",
                 f"{len(allg)} مصطلح. وفي أي مكان بالموقع اضغط علامة ؟ الصغيرة جنب المصطلح عشان تقرأ شرحه."))
    ui.html(f'<div class="card{rtl}" data-nogq="1">' + "".join(
        f'<div class="gl"><b>{T.esc(L(en, ar))}</b> <span class="muted">· {T.esc(ar if not is_ar() else en)}</span>'
        f'<div class="d">{T.esc(L(den, dar))}</div></div>' for en, ar, den, dar in items) + "</div>"
        if items else f'<div class="muted">{L("No matching terms.", "لا توجد مصطلحات مطابقة.")}</div>')
    ui.foot()

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "23.4.39"


