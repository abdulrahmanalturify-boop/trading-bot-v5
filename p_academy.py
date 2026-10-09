"""
p_academy.py - Academy (interactive 3-minute courses with quizzes, learning dashboard) · Glossary
Clicking anywhere on a course card opens it (invisible button over the card, no page reload, progress is kept).
"""
import math
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


def _status(cid):
    if cid in ss.get("completed", set()):
        return "done"
    return "prog" if ss.get(f"step_{cid}", 0) > 0 else "new"


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
    ss["course"] = cid
    st.query_params["course"] = cid


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
    n = len(c["sections"])
    step = ss.setdefault(f"step_{cid}", 0)
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
            with st.container(key="academy_lesson_navigation"):
                a, _, b = st.columns([1, 2, 1])
                if step > 0 and a.button(L("Back", "السابق"), icon=":material/chevron_left:", width="stretch"):
                    ss[f"step_{cid}"] = step - 1
                    st.rerun()
                if b.button(L("Next", "التالي") if step < n - 1 else L("Take the quiz", "ابدأ الاختبار"), icon=":material/chevron_right:",
                            type="primary", width="stretch"):
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
            ss[f"checked_{cid}"] = True
    if ss.get(f"checked_{cid}"):
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
        idx = [x["id"] for x in A.COURSES].index(cid)
        if idx + 1 < len(A.COURSES):
            nxt = A.COURSES[idx + 1]
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


def _academy_hero():
    count = len(A.COURSES)
    ui.html(f'<section class="ac-hero"><div class="ac-brand-lockup" dir="ltr">{T.brand(None, "acb", pro=None, color="#F2F5FF", label="TURA")}<span>ACADEMY</span></div><div dir="auto">'
            f'<h1>{L("Build knowledge.<br>Invest with understanding.", "ابنِ معرفتك.<br>واستثمر بفهم.")}</h1>'
            f'<p>{L("Your learning space for markets, investing and trading. Follow a path, explore a lesson and test the idea yourself.", "مساحتك لتعلّم الأسواق والاستثمار والتداول. اختر مسارك، افهم الفكرة، وجرّبها بنفسك.")}</p>'
            f'<div class="ac-meta"><span>{count} {L("courses", "دورة")}</span>'
            f'<span>{len(AL.LABS)} {L("interactive labs", "مختبرات تفاعلية")}</span>'
            f'<span>{L("Arabic + English", "عربي + إنجليزي")}</span></div></div>'
            f'<div class="ac-emblem">{AV.MARK}</div></section>')


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
        st.button(L("Start / continue this path", "ابدأ أو أكمل المسار"),type="primary",key="ac_path_start",on_click=_open_course,args=(remaining[0]["id"],))
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
        catalog, videos, path, labs, progress = st.tabs([L("Course library", "مكتبة الكورسات"), L("Video explanations", "شروحات الفيديو"), L("My learning path", "مساري التعليمي"),
                                              L("Interactive labs", "المختبرات التفاعلية"), L("My progress", "تقدمي")])
        with catalog:
            with st.container(key="academy_start_here"):
                st.markdown("### " + L("New to investing? Start here.", "جديد على الاستثمار؟ ابدأ هنا."))
                st.caption(L("Build your foundation first, then move through each level at your own pace.",
                             "ابدأ بالأساسيات، وبعدها تقدّم بالمستويات على راحتك."))
                st.button(L("Start the beginner journey", "ابدأ رحلة المبتدئ"), type="primary",
                          key="ac_beginner_start", on_click=_open_course, args=("money_foundations",))
            a,b=st.columns([3,1])
            query=a.text_input(L("Search courses", "ابحث عن دورة"),placeholder=L("e.g. bonds, cash flow, risk", "مثل: السندات، النقد، المخاطرة"),key="ac_search").strip().casefold()
            state=b.selectbox(L("Show", "اعرض"),["all","new","progress","done"],key="ac_status",format_func=lambda x, labels={"all":L("All courses","كل الدورات"),"new":L("New additions","المضافة حديثًا"),"progress":L("In progress","قيد التعلم"),"done":L("Completed","المكتملة")}:labels[x])
            lvl=st.radio(L("Level", "المستوى"),list(LEVELS),index=0,horizontal=True,key="ac_lvl",format_func=lambda k, labels={key:L(*val) for key,val in LEVELS.items()}:labels[k]) or "all"
            courses=[c for c in A.COURSES if (lvl=="all" or c["level"][0]==lvl)
                     and (not query or query in " ".join(c["title"]+c["tagline"]).casefold())
                     and (state=="all" or state=="new" and c.get("new") or state=="progress" and _status(c["id"])=="prog" or state=="done" and _status(c["id"])=="done")]
            st.caption(L(f"{len(courses)} courses · choose a card to begin",f"{len(courses)} دورة · اختر بطاقة للبدء"))
            if courses:
                descriptions = {
                    "Beginner": ("Start from zero: money, markets and your first portfolio.", "من الصفر: فلوسك، السوق، وأول محفظة لك."),
                    "Essential": ("Build the skills every investor needs.", "مهارات أساسية يحتاجها كل مستثمر."),
                    "Intermediate": ("Go deeper into analysis and market behaviour.", "تعمّق بالتحليل وفهم حركة الأسواق."),
                    "Advanced": ("Explore derivatives, valuation scenarios and strategy testing.", "المشتقات وسيناريوهات التقييم واختبار الاستراتيجيات.")}
                for index, level in enumerate(A.LEVEL_ORDER, 1):
                    group = [c for c in courses if c["level"][0] == level]
                    if group:
                        st.subheader(f"{index:02d} · {L(*LEVELS[level])} · {len(group)}")
                        st.caption(L(*descriptions[level]))
                        course_cards(group)
            else: st.info(L("No matching courses. Try another search or level.","ما فيه دورات تطابق الاختيار. غيّر البحث أو المستوى."))
        with videos:
            _video_library()
        with catalog:
            with st.expander(L("Photo credits", "مصادر الصور")):
                for photo in AV.PHOTOS.values():
                    st.markdown(f'[{photo["credit"]} · Unsplash]({photo["page"]})')
        with path:
            _learning_path()
        with labs:
            ui.html('<div class="ac-note">'+L("Change the assumptions and see the result. These labs use hypothetical data and work without live market feeds.","غيّر الافتراضات وشوف النتيجة. المختبرات تستخدم بيانات افتراضية وتعمل بدون أسعار سوق مباشرة.")+'</div>')
            selected=st.selectbox(L("Choose a lab", "اختر المختبر"),list(AL.LABS),format_func=lambda x, labels={key:L(*val) for key,val in AL.LABS.items()}:labels[x],key="ac_lab")
            AL.render(selected,namespace="hub")
        with progress:
            ui.safe(dashboard)
            st.caption(L("Progress is stored for this session, not in a permanent learner account.","التقدم محفوظ للجلسة الحالية، مو بحساب متعلم دائم."))
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
BUILD = "21.4"


