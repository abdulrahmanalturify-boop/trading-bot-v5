"""
p_watchlist.py - The Watchlist page (its own menu in the top bar): the visitor's list, large, with each company's price, the day's
change and a month's line, and under it ideas to follow - companies of the emerging sectors (neocloud, photonics, quantum,
nuclear power for AI, space, robotics, the AI build-out), a few in each, with one line on why each matters and a button that
adds it to the list. The list itself is the sidebar's (the same session keys: watchlist / watchlist_sa).
"""
import re

import streamlit as st

import data
import markets as MK
import tasi
import theme as T
import ui
import universe as U
from i18n import L, is_ar

ss = st.session_state

CSS = """<style>
.wlp-row{display:grid;grid-template-columns:34px minmax(0,1fr) 92px 96px 84px;gap:12px;align-items:center;padding:24px 14px 6px;border-radius:14px;
  background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08)}
.wlp-row .nm{min-width:0}.wlp-row .nm b{display:block;color:#fff;font-size:.95rem;line-height:1.25;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.wlp-row .nm span{display:block;color:#9D97A5;font-size:.72rem;line-height:1.25;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.wlp-row .px{font-size:1rem;font-weight:800;color:#fff;direction:ltr;text-align:end}
.wlp-row .sp{display:grid;place-items:center}.wlp-row .sp svg{max-width:100%;height:auto}
.wlp-row .pc{display:flex;justify-content:flex-end;min-width:0}.wlp-row .pc .pill{white-space:nowrap}
/* a row with its two small round buttons inside its top corners: open on the right, drop on the left */
div[class*="st-key-wlp_r_"]{position:relative;gap:0!important}
div[class*="st-key-wlp_o_"],div[class*="st-key-wlp_d_"]{position:absolute!important;top:3px;width:auto!important;z-index:3}
div[class*="st-key-wlp_o_"]{right:6px}div[class*="st-key-wlp_d_"]{left:6px}
div[class*="st-key-wlp_o_"] button,div[class*="st-key-wlp_d_"] button{width:20px!important;height:20px!important;min-height:20px!important;padding:0!important;
  border-radius:50%!important;display:grid!important;place-items:center!important;gap:0!important}
div[class*="st-key-wlp_o_"] button [data-testid="stMarkdownContainer"],div[class*="st-key-wlp_d_"] button [data-testid="stMarkdownContainer"]{display:none!important}
div[class*="st-key-wlp_o_"] button span,div[class*="st-key-wlp_d_"] button span{font-size:13px!important;margin:0!important}
div[class*="st-key-wlp_d_"] button:hover{border-color:#F43F5E!important;color:#F43F5E!important}
@media (max-width:640px){
  .wlp-row{grid-template-columns:30px minmax(0,1fr) auto 60px auto;gap:8px;padding:24px 10px 6px}
  .wlp-row .nm span{display:none}
  .wlp-row .px{font-size:.92rem}
  .wlp-row .pc .pill{font-size:.72rem;padding:2px 6px}
}
/* the ideas */
.wlp-grp{display:flex;align-items:center;gap:10px;margin:18px 0 10px}
.wlp-grp .ic{width:36px;height:36px;border-radius:11px;display:grid;place-items:center;background:linear-gradient(135deg,var(--g1),var(--g2));box-shadow:0 8px 18px -10px var(--g1)}
.wlp-grp .ic .ms{font-size:20px;color:#fff}
.wlp-grp b{font-size:1.05rem;color:#fff}.wlp-grp span{display:block;color:#9D97A5;font-size:.78rem}
.wlp-card{position:relative;height:100%;box-sizing:border-box;padding:12px 12px 10px;border-radius:16px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
  border-top:2px solid var(--g1);transition:transform .2s,border-color .2s}
.wlp-card:hover{transform:translateY(-2px);border-color:var(--g1)}
.wlp-card .hd{display:flex;align-items:center;gap:9px}
.wlp-card .hd .nm{min-width:0;flex:1}.wlp-card .hd b{display:block;color:#fff;font-size:.95rem}.wlp-card .hd span{display:block;color:#9D97A5;font-size:.72rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.wlp-card .q{display:flex;align-items:baseline;gap:8px;margin:8px 0 6px}.wlp-card .q b{font-size:1.05rem;color:#fff;direction:ltr}
.wlp-card p{margin:0;font-size:.78rem;line-height:1.5;color:#B9B3C4;min-height:6em}
div[class*="st-key-wlp_c_"] [data-testid="stButton"] button{min-height:34px!important;border-radius:999px!important;font-size:.8rem!important}
.wlp-note{font-size:.78rem;color:#9D97A5;margin:6px 0 2px}
</style>"""

# ---------------------------------------------------------------- the ideas: emerging sectors, a few companies each
# (key, icon, two colours, name, what the sector is, [(symbol, name, why)])
IDEAS = [
    ("neocloud", "cloud", ("#2DB6EB", "#1D4ED8"), ("Neocloud", "النيو كلاود"),
     ("The new AI clouds: companies that rent out GPU computing to the AI builders, growing faster than the big clouds.",
      "سحابات الذكاء الاصطناعي الجديدة: شركات تؤجّر حوسبة الـ GPU لبناة الذكاء الاصطناعي، وتنمو أسرع من السحابات الكبرى."),
     [("CRWV", "CoreWeave", ("The biggest pure AI cloud: GPU capacity leased to OpenAI, Microsoft and the labs.",
                             "أكبر سحابة ذكاء اصطناعي خالصة: سعة GPU مؤجّرة لـ OpenAI ومايكروسوفت والمختبرات.")),
      ("NBIS", "Nebius Group", ("An AI cloud built from the ground up in Europe and the US, with Nvidia's newest chips.",
                                "سحابة ذكاء اصطناعي بُنيت من الصفر في أوروبا وأمريكا بأحدث رقائق إنفيديا.")),
      ("IREN", "IREN", ("From bitcoin mining to AI cloud: cheap renewable power turned into GPU capacity.",
                        "من تعدين البيتكوين إلى سحابة الذكاء الاصطناعي: طاقة متجددة رخيصة تتحول لسعة GPU.")),
      ("APLD", "Applied Digital", ("Builds the data centres the AI clouds lease for years ahead.",
                                   "تبني مراكز البيانات التي تستأجرها سحابات الذكاء الاصطناعي لسنوات قادمة.")),
      ("WULF", "TeraWulf", ("Power-rich sites turned into AI hosting, with long leases signed.",
                            "مواقع غنية بالطاقة تتحول لاستضافة الذكاء الاصطناعي بعقود طويلة."))]),
    ("photonics", "flare", ("#F5B94A", "#F97316"), ("Photonics", "الفوتونيات"),
     ("Light instead of electricity: the lasers, optical parts and switches that move data between AI chips and data centres.",
      "الضوء بدل الكهرباء: الليزر والقطع البصرية والمحوّلات التي تنقل البيانات بين رقائق الذكاء الاصطناعي ومراكز البيانات."),
     [("LITE", "Lumentum", ("Lasers and optical modules at the heart of the AI data centre's network.",
                            "ليزر ووحدات بصرية في قلب شبكة مركز بيانات الذكاء الاصطناعي.")),
      ("COHR", "Coherent", ("Transceivers and lasers for 800G and 1.6T links, plus silicon photonics.",
                            "مرسلات مستقبلات وليزر لوصلات 800G و1.6T، وفوتونيات السيليكون.")),
      ("CIEN", "Ciena", ("Optical networking between data centres: the long-haul of the AI traffic.",
                         "الشبكات البصرية بين مراكز البيانات: المسافات الطويلة لحركة الذكاء الاصطناعي.")),
      ("FN", "Fabrinet", ("Makes the optical modules for the biggest names, including Nvidia's.",
                          "تصنّع الوحدات البصرية لأكبر الأسماء، ومنها إنفيديا.")),
      ("AAOI", "Applied Optoelectronics", ("A smaller optical-transceiver maker riding the hyperscalers' orders.",
                                           "صانع مرسلات بصرية أصغر يركب موجة طلبات عمالقة السحابة."))]),
    ("quantum", "blur_on", ("#7B45F0", "#A78BFA"), ("Quantum computing", "الحوسبة الكمية"),
     ("Computers built on qubits: early, volatile and years from profit, but the field the big labs and governments are racing in.",
      "حواسيب مبنية على الكيوبت: مبكرة ومتقلبة وبعيدة عن الربح بسنوات، لكنها الميدان الذي تتسابق فيه المختبرات الكبرى والحكومات."),
     [("IONQ", "IonQ", ("Trapped-ion quantum computers sold through the big clouds; the sector's largest name.",
                        "حواسيب كمية بالأيونات المحبوسة تُباع عبر السحابات الكبرى؛ أكبر اسم في القطاع.")),
      ("RGTI", "Rigetti Computing", ("Superconducting qubits and its own chip fab.",
                                     "كيوبتات فائقة التوصيل ومصنع رقائق خاص بها.")),
      ("QBTS", "D-Wave Quantum", ("Annealing machines already used for optimisation problems.",
                                  "آلات تلدين كمي تُستخدم فعلاً في مسائل التحسين.")),
      ("QUBT", "Quantum Computing Inc.", ("Photonic quantum chips: small, speculative, very volatile.",
                                          "رقائق كمية ضوئية: صغيرة ومضاربية وشديدة التقلب.")),
      ("ARQQ", "Arqit Quantum", ("Quantum-safe encryption for the day quantum computers break today's.",
                                 "تشفير آمن كمياً لليوم الذي تكسر فيه الحواسيب الكمية تشفير اليوم."))]),
    ("nuclear", "bolt", ("#22C55E", "#0E7490"), ("Nuclear power for AI", "الطاقة النووية للذكاء الاصطناعي"),
     ("Data centres need power around the clock: small modular reactors, uranium and the utilities signing nuclear deals with the clouds.",
      "مراكز البيانات تحتاج طاقة على مدار الساعة: مفاعلات صغيرة ويورانيوم ومرافق توقّع صفقات نووية مع السحابات."),
     [("OKLO", "Oklo", ("Small reactors backed by Sam Altman, with data-centre customers lined up.",
                        "مفاعلات صغيرة بدعم سام ألتمان، مع عملاء من مراكز البيانات.")),
      ("SMR", "NuScale Power", ("The first small modular reactor design approved in the US.",
                                "أول تصميم مفاعل صغير معتمد في أمريكا.")),
      ("NNE", "Nano Nuclear Energy", ("Micro-reactors for remote sites: early and speculative.",
                                      "مفاعلات مصغّرة للمواقع النائية: مبكرة ومضاربية.")),
      ("LEU", "Centrus Energy", ("The only US-owned enricher of the fuel the new reactors need.",
                                 "المخصّب الأمريكي الوحيد للوقود الذي تحتاجه المفاعلات الجديدة.")),
      ("CCJ", "Cameco", ("The West's biggest uranium miner and a stake in Westinghouse.",
                         "أكبر منجم يورانيوم في الغرب وحصة في ويستنغهاوس."))]),
    ("space", "rocket_launch", ("#38BDF8", "#6366F1"), ("Space", "الفضاء"),
     ("Launch, satellites and the phone-to-space networks: an industry that became investable in the last few years.",
      "الإطلاق والأقمار الصناعية وشبكات الهاتف من الفضاء: صناعة صارت قابلة للاستثمار في السنوات الأخيرة."),
     [("RKLB", "Rocket Lab", ("The second most-launched rocket company after SpaceX, building a bigger one.",
                              "ثاني أكثر شركة صواريخ إطلاقاً بعد SpaceX، وتبني صاروخاً أكبر.")),
      ("ASTS", "AST SpaceMobile", ("Satellites that connect ordinary phones directly, with AT&T and Verizon.",
                                   "أقمار تربط الهواتف العادية مباشرة، مع AT&T وVerizon.")),
      ("LUNR", "Intuitive Machines", ("Landed on the Moon for NASA; lunar services contracts.",
                                      "هبطت على القمر لصالح ناسا؛ عقود خدمات قمرية.")),
      ("PL", "Planet Labs", ("Images the whole Earth daily; governments are its growing customers.",
                             "تصوّر الأرض كلها يومياً؛ الحكومات عملاؤها المتزايدون.")),
      ("RDW", "Redwire", ("Parts and structures for satellites and stations.",
                          "قطع وهياكل للأقمار والمحطات الفضائية."))]),
    ("robotics", "precision_manufacturing", ("#EC4899", "#BE185D"), ("Robotics & drones", "الروبوتات والطائرات المسيّرة"),
     ("Machines that act in the real world: warehouse robots, delivery robots, defence drones and the testers behind the chips.",
      "آلات تعمل في العالم الحقيقي: روبوتات المستودعات والتوصيل، والمسيّرات الدفاعية، وأجهزة اختبار الرقائق."),
     [("SERV", "Serve Robotics", ("Sidewalk delivery robots for Uber Eats, scaling to thousands.",
                                  "روبوتات توصيل على الأرصفة لـ Uber Eats، تتوسع للآلاف.")),
      ("SYM", "Symbotic", ("Warehouse automation for Walmart and the big retailers.",
                           "أتمتة المستودعات لوولمارت وكبار التجزئة.")),
      ("KTOS", "Kratos Defense", ("Drones and hypersonic test vehicles for the Pentagon.",
                                  "مسيّرات ومركبات اختبار فرط صوتية للبنتاغون.")),
      ("AVAV", "AeroVironment", ("Small military drones and loitering munitions.",
                                 "مسيّرات عسكرية صغيرة وذخائر جوّالة.")),
      ("TER", "Teradyne", ("Chip testers plus the Universal Robots arms.",
                           "أجهزة اختبار الرقائق وأذرع Universal Robots."))]),
    ("aiinfra", "memory", ("#3B8BEB", "#7B45F0"), ("The AI build-out", "بناء الذكاء الاصطناعي"),
     ("The picks and shovels behind the AI data centre: cooling, networking, the links between chips and the servers themselves.",
      "المعاول والمجارف خلف مركز بيانات الذكاء الاصطناعي: التبريد والشبكات والوصلات بين الرقائق والخوادم نفسها."),
     [("VRT", "Vertiv", ("Cooling and power for the AI racks: every data centre needs it.",
                         "التبريد والطاقة لرفوف الذكاء الاصطناعي: كل مركز بيانات يحتاجه.")),
      ("ANET", "Arista Networks", ("The switches the hyperscalers wire their AI clusters with.",
                                   "المحوّلات التي يربط بها عمالقة السحابة عناقيد الذكاء الاصطناعي.")),
      ("CRDO", "Credo Technology", ("Cables and chips that link AI servers at high speed.",
                                    "كابلات ورقائق تربط خوادم الذكاء الاصطناعي بسرعة عالية.")),
      ("ALAB", "Astera Labs", ("Connectivity chips inside the AI server.",
                               "رقائق الربط داخل خادم الذكاء الاصطناعي.")),
      ("CLS", "Celestica", ("Builds the AI servers and switches for the clouds.",
                            "تصنّع خوادم ومحوّلات الذكاء الاصطناعي للسحابات."))]),
]
IDEA_SYMS = [s for *_, rows in IDEAS for s, _, _ in rows]


def _wl_key():
    return "watchlist_sa" if MK.choice() == MK.SA else "watchlist"


def _toggle(sym, key):
    wl = ss.setdefault(key, [])
    if sym in wl:
        wl.remove(sym)
    else:
        wl.append(sym)


def _add_all(syms, key):
    wl = ss.setdefault(key, [])
    for s_ in syms:
        if s_ not in wl:
            wl.append(s_)


def _name(sym, q=None):
    if tasi.known(sym):
        return tasi.name_of(sym, is_ar())
    if U.known(sym):
        return U.name_of(sym)
    try:
        from sp500 import SP500
        if sym in SP500:
            return SP500[sym][0]
    except Exception:
        pass
    return str(q.get("Name", "")) if q is not None and q.get("Name") else ""


def _list(wl, key):
    """The visitor's list: a slim row per company with the price, the day's change and a month's line, and two small round
    buttons on its top corners: open it (right), drop it (left)."""
    ui.sec("star", "My watchlist", "قائمة متابعتي")
    if not wl:
        st.caption(L("Your list is empty: add a symbol below, or pick ideas from the sectors under it.",
                     "قائمتك فاضية: أضف رمزاً تحت، أو اختر أفكاراً من القطاعات اللي بعده."))
        return
    px = data.history_many(tuple(wl), "1mo")
    if MK.choice() == MK.SA:
        px = data.with_quotes(px, [s_ for s_ in wl if s_.startswith("^")])
    lg = data.logos(wl)
    for s_ in wl:
        df = px.get(s_)
        p = pct = sp = None
        if df is not None and len(df) >= 2:
            c = df["Close"].dropna()
            if len(c) >= 2:
                p, pct, sp = float(c.iloc[-1]), float((c.iloc[-1] / c.iloc[-2] - 1) * 100), c.tail(22).values
        top_, sub_ = (T.sym_label(s_), T.sym_sub(s_)) if tasi.is_sa(s_) else (s_, _name(s_))
        spark = T.sparkline(sp, T.UP if (pct or 0) >= 0 else T.DOWN, 84, 26) if sp is not None else "<span></span>"
        with st.container(key=f"wlp_r_{s_}"):
            ui.html(f'<div class="wlp-row">{T.logo_circle(s_, lg.get(s_), 30)}<div class="nm"><b dir="auto">{T.esc(top_)}</b><span>{T.esc(sub_)}</span></div>'
                    f'<div class="px">{T.fmt_price(p) if p is not None else "—"}</div><div class="sp">{spark}</div>'
                    f'<div class="pc">{T.pill(pct) if pct is not None else ""}</div></div>')
            st.button(L("Open", "افتح"), key=f"wlp_o_{s_}", icon=":material/open_in_new:", help=L("Open", "افتح"),
                      on_click=ui.open_stock, args=(s_,))
            st.button(L("Drop", "احذف"), key=f"wlp_d_{s_}", icon=":material/close:", help=L("Drop", "احذف"),
                      on_click=_toggle, args=(s_, key))


def _ideas(wl, key):
    ui.sec("auto_awesome", "Ideas to follow: the emerging sectors", "أفكار للمتابعة: القطاعات الناشئة")
    st.caption(L("A few companies in each of the sectors the market is only starting to price: new, fast-moving and risky. Ideas to "
                 "research, not advice to buy.",
                 "كم شركة في كل قطاع من القطاعات اللي السوق بدأ يسعّرها للتو: جديدة وسريعة الحركة وعالية المخاطر. أفكار للبحث، مو نصيحة شراء."))
    q = {}
    try:
        qd = data.quotes_df(IDEA_SYMS)
        if not qd.empty:
            q = {r["Symbol"]: r for _, r in qd.iterrows()}
    except Exception:
        q = {}
    lg = data.logos(IDEA_SYMS)
    for gkey, icon, (g1, g2), name, about, rows in IDEAS:
        ui.html(f'<div class="wlp-grp" style="--g1:{g1};--g2:{g2}"><span class="ic">{T.icon(icon)}</span><div><b>{T.esc(L(*name))}</b>'
                f'<span>{T.esc(L(*about))}</span></div></div>')
        cols = st.columns(len(rows))
        for col, (sym, nm, why) in zip(cols, rows):
            qq = q.get(sym)
            p = qq.get("Price") if qq is not None else None
            chg = qq.get("Chg %") if qq is not None else None
            price = f'<div class="q"><b>{T.fmt_price(p)}</b>{T.pill(chg) if chg is not None and chg == chg else ""}</div>' if p is not None and p == p else '<div class="q"><b>—</b></div>'
            inwl = sym in wl
            with col:
                with st.container(key=f"wlp_c_{sym}"):
                    ui.html(f'<div class="wlp-card" style="--g1:{g1};--g2:{g2}"><div class="hd">{T.logo_circle(sym, lg.get(sym), 34)}'
                            f'<div class="nm"><b>{T.esc(sym)}</b><span>{T.esc(nm)}</span></div></div>{price}<p>{T.esc(L(*why))}</p></div>')
                    st.button(L("In my list", "في قائمتي") if inwl else L("Follow", "تابع"), key=f"wlp_f_{sym}", width="stretch",
                              icon=":material/check:" if inwl else ":material/add:", type="primary" if inwl else "secondary",
                              on_click=_toggle, args=(sym, key))
        st.button(L(f"Follow all {len(rows)}", f"تابع الـ {len(rows)} كلها"), key=f"wlp_all_{gkey}", icon=":material/playlist_add:",
                  on_click=_add_all, args=([s for s, _, _ in rows], key))


def page_watchlist():
    ui.html(CSS)
    ui.header("star", "Watchlist", "قائمة المتابعة",
              "The companies you follow, at a glance, and ideas from the sectors that are only starting: neocloud, photonics, quantum and more.",
              "الشركات اللي تتابعها بنظرة وحدة، وأفكار من القطاعات اللي للتو بادية: النيو كلاود والفوتونيات والحوسبة الكمية وغيرها.")
    key = _wl_key()
    wl = ss.setdefault(key, [])
    _list(wl, key)
    st.text_input(L("Add a symbol", "أضف رمزاً"), key="wlp_add", placeholder=L("e.g. PLTR, or 2222 for Aramco", "مثال: PLTR، أو 2222 لأرامكو"),
                  on_change=_add_typed, args=(key,))
    if MK.choice() == MK.SA:
        st.caption(L("The ideas below are US companies: they go into your US list.", "الأفكار اللي تحت شركات أمريكية: تنضاف لقائمتك الأمريكية."))
    _ideas(ss.setdefault("watchlist", []), "watchlist")
    ui.foot()


_WL_SYM = re.compile(r"^[A-Z0-9^][A-Z0-9.\-=^]{0,14}$")


def _wl_sym(x):
    """A typed entry as a symbol (2222 -> 2222.SR, a Saudi company's name -> its code), None when it can't be one (the sidebar's rule)."""
    v = str(x or "").strip()
    if not v:
        return None
    if v.isdigit() and len(v) == 4:
        return v + ".SR"
    if MK.choice() == MK.SA or not v.isascii():
        r = ui.resolve_sym(v, True)
        if r.endswith(".SR"):
            return r
        if not v.isascii():
            return None
    v = v.upper()
    return v if _WL_SYM.match(v) else None


def _add_typed(key):
    v = _wl_sym(ss.get("wlp_add"))
    wl = ss.setdefault(key, [])
    if v and v not in wl:
        wl.append(v)
    ss.wlp_add = ""


BUILD = "23.4.60"
