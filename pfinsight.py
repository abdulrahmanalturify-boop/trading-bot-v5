"""
pfinsight.py - The paper portfolio's coach: a health score (five factors, each with its reason) and the next steps that would
raise it, the achievements a trader unlocks, and the day-by-day profit and loss for the P&L calendar.

Pure functions on what portfolio.py already computes (rebuild / account / stats), so they're quick and easy to test.
Every text comes in English and Arabic: (en, ar) pairs the page picks from.
"""
import math

import numpy as np
import pandas as pd

GRADES = [(90, "A+", ("Excellent", "ممتازة")), (80, "A", ("Very strong", "قوية جداً")), (70, "B", ("Good", "جيدة")),
          (55, "C", ("Fair", "مقبولة")), (40, "D", ("Needs work", "تحتاج شغل")), (0, "E", ("At risk", "في خطر"))]


def _interp(x, xs, ys):
    return float(np.interp(x, xs, ys))


def _clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(x)))


def grade(score):
    for lo, g, name in GRADES:
        if score >= lo:
            return g, name
    return GRADES[-1][1], GRADES[-1][2]


def protected(orders, sym, qty):
    """True when a stop or trailing stop is working on the closing side of this position."""
    side = "sell" if qty > 0 else "cover"
    return any(o.get("sym") == sym and o.get("status") == "open" and o.get("side") == side and o.get("type") in ("stop", "trail")
               for o in orders)


def _syms(names):
    names = list(names)
    return ", ".join(names[:3]) + (" …" if len(names) > 3 else "")


def _syms_ar(names):
    names = list(names)
    return " و".join(names[:3]) + (" …" if len(names) > 3 else "")


def health(view, acct, stats, orders, sector_of, sec_name=None):
    """{'score', 'grade', 'name': (en, ar), 'factors': [...], 'tips': [...]}; score None before the first trade.
    factors: {'key', 'icon', 'name': (en, ar), 'score' (0-100 or None), 'detail': (en, ar)}
    tips: {'icon', 'kind' ('warn' / 'info' / 'good'), 'text': (en, ar)}, the most useful first (at most four)."""
    pos = view.get("positions") or []
    eq = max(float(acct.get("equity") or 0), 1e-9)
    n = len(pos)
    secs = {}
    for p in pos:
        secs.setdefault(sector_of(p["sym"]) or "Other", []).append(p["sym"])
    factors, tips = [], []

    # 1 diversification: how many positions, in how many sectors
    if n:
        div = _clamp(_interp(n, [1, 2, 3, 4, 5, 8], [25, 45, 60, 72, 85, 100]) + 5 * min(len(secs) - 1, 3))
        d = (f"{n} position{'s' if n != 1 else ''} · {len(secs)} sector{'s' if len(secs) != 1 else ''}",
             f"{n} {'مركز' if n == 1 or n > 10 else 'مراكز'} · {len(secs)} {'قطاع' if len(secs) == 1 or len(secs) > 10 else 'قطاعات'}")
    else:
        div, d = None, ("No positions", "ما فيه مراكز")
    factors.append({"key": "div", "icon": "hub", "name": ("Diversification", "التنويع"), "score": div, "detail": d})

    # 2 concentration: the biggest single bet
    if n:
        big = max(pos, key=lambda p: p["weight"])
        conc = _clamp(_interp(big["weight"], [10, 20, 30, 45, 60, 80], [100, 90, 72, 50, 30, 10]))
        d = (f"Largest: {big['sym']} {big['weight']:.1f}%", f"الأكبر: {big['sym']} {big['weight']:.1f}%")
    else:
        big, conc, d = None, None, ("No positions", "ما فيه مراكز")
    factors.append({"key": "conc", "icon": "pie_chart", "name": ("Concentration", "التركيز"), "score": conc, "detail": d})

    # 3 protection: share of the money with a stop working on it
    bare = [p for p in pos if not protected(orders, p["sym"], p["qty"])]
    if n:
        tot = sum(abs(p["mv"]) for p in pos) or 1e-9
        prot = _clamp((1 - sum(abs(p["mv"]) for p in bare) / tot) * 100)
        d = (f"{n - len(bare)} of {n} with a stop", f"{n - len(bare)} من {n} عليها وقف")
    else:
        prot, d = None, ("No positions", "ما فيه مراكز")
    factors.append({"key": "prot", "icon": "shield", "name": ("Protection", "الحماية"), "score": prot, "detail": d})

    # 4 risk: leverage, margin, how much it swings, how much is short
    lev, used = float(acct.get("leverage") or 0), float(acct.get("used") or 0)
    vol = stats.get("vol")
    short_pct = float(acct.get("smv") or 0) / eq * 100
    risk = 100.0
    risk -= max(lev - 1, 0) * 40
    risk -= max(used - 50, 0) * 1.2
    risk -= max((vol or 0) - 25, 0) * 2
    risk -= max(short_pct - 50, 0) * 0.5
    if acct.get("margin_call"):
        risk = min(risk, 10)
    risk = _clamp(risk)
    d = (f"Leverage {lev:.2f}× · margin used {used:.0f}%" + (f" · swings {vol:.0f}%/yr" if vol is not None else ""),
         f"الرافعة {lev:.2f}× · الهامش المستخدم {used:.0f}%" + (f" · التذبذب {vol:.0f}% سنوياً" if vol is not None else ""))
    factors.append({"key": "risk", "icon": "speed", "name": ("Risk", "المخاطرة"), "score": risk if (n or view.get("trades")) else None, "detail": d})

    # 5 performance against the market (needs a week of sessions)
    twr, bret, days = stats.get("twr"), stats.get("bench_ret"), int(stats.get("days") or 0)
    if twr is not None and days >= 5:
        ex = twr - (bret if bret is not None else 0.0)
        perf = _clamp(50 + ex * 4)
        d = ((f"{twr:+.1f}% vs S&P 500 {bret:+.1f}%" if bret is not None else f"{twr:+.1f}% so far"),
             (f"{twr:+.1f}% مقابل S&P 500 {bret:+.1f}%" if bret is not None else f"{twr:+.1f}% للحين"))
    else:
        perf, d = None, ("After a week of sessions", "بعد أسبوع من الجلسات")
    factors.append({"key": "perf", "icon": "trending_up", "name": ("Against the market", "مقابل السوق"), "score": perf, "detail": d})

    have = [f["score"] for f in factors if f["score"] is not None]
    if not n and not view.get("trades"):
        return {"score": None, "grade": None, "name": None, "factors": factors,
                "tips": [{"icon": "rocket_launch", "kind": "info",
                          "text": ("Start with a few stocks you know, each with a stop loss: your score appears with your first position.",
                                   "ابدأ بكم سهم تعرفها، وكل واحد عليه وقف خسارة: تقييمك يطلع مع أول مركز.")}]}
    score = round(sum(have) / len(have)) if have else 50

    # ---- next steps, the most useful first
    if acct.get("margin_call"):
        tips.append({"icon": "warning", "kind": "warn", "text": (
            "Margin call: close or cover part of a position to bring the account back above the maintenance line.",
            "نداء هامش: سكّر أو غطِّ جزء من مركز عشان يرجع الحساب فوق الحد الأدنى.")})
    if bare:
        names = [p["sym"] for p in sorted(bare, key=lambda p: -abs(p["mv"]))]
        tips.append({"icon": "shield", "kind": "warn", "text": (
            f"Add a stop to {_syms(names)}: a stop caps the loss if the price turns against you.",
            f"حط وقف خسارة على {_syms_ar(names)}: الوقف يحدد خسارتك إذا انعكس السعر ضدك.")})
    if big is not None and big["weight"] > 30:
        tips.append({"icon": "pie_chart", "kind": "warn", "text": (
            f"{big['sym']} is {big['weight']:.0f}% of the account. Many traders keep one stock under 20–25%.",
            f"{big['sym']} يمثل {big['weight']:.0f}% من الحساب. كثير من المتداولين يخلون السهم الواحد تحت 20–25%.")})
    losers = [p for p in pos if p["upnl_pct"] <= -15]
    if losers:
        w = min(losers, key=lambda p: p["upnl_pct"])
        tips.append({"icon": "trending_down", "kind": "warn", "text": (
            f"{w['sym']} is {w['upnl_pct']:.0f}% since you opened it: decide on purpose — cut it, or set a stop where you'd admit you were wrong.",
            f"{w['sym']} نازل {abs(w['upnl_pct']):.0f}% من فتحته: قرّر بوعي — سكّره، أو حط وقف عند النقطة اللي تعترف فيها إنك غلطت.")})
    if 0 < n < 4:
        tips.append({"icon": "hub", "kind": "info", "text": (
            f"Only {n} position{'s' if n != 1 else ''}: spreading over 5+ stocks from different sectors softens one bad surprise.",
            f"عندك {n} {'مركز' if n == 1 else 'مراكز'} بس: التوزيع على 5 أسهم أو أكثر من قطاعات مختلفة يخفف أثر أي مفاجأة سيئة.")})
    elif n >= 2 and len(secs) == 1:
        s = (sec_name or str)(next(iter(secs)))
        tips.append({"icon": "category", "kind": "info", "text": (
            f"Every position is in {s}: one bad day for the sector hits all of them.",
            f"كل مراكزك في قطاع واحد ({s}): يوم سيء للقطاع يضربها كلها.")})
    if n and float(acct.get("smv") or 0) == 0 and float(acct.get("lmv") or 0) / eq < 0.3:
        idle = 100 - float(acct.get("lmv") or 0) / eq * 100
        tips.append({"icon": "savings", "kind": "info", "text": (
            f"{idle:.0f}% of the account is idle cash: fine while you wait for a setup, just a choice to make on purpose.",
            f"{idle:.0f}% من الحساب كاش واقف: عادي وأنت تنتظر فرصة، بس خلّه قرار مقصود.")})
    if lev > 1.5:
        tips.append({"icon": "speed", "kind": "warn", "text": (
            f"Leverage {lev:.1f}×: gains and losses both come bigger than the market's moves.",
            f"الرافعة {lev:.1f}×: الأرباح والخسائر كلها أكبر من حركة السوق.")})
    if not tips:
        tips.append({"icon": "verified", "kind": "good", "text": (
            "Well balanced: nothing urgent to fix. Keep the stops moving up as winners grow.",
            "محفظة متوازنة وما فيها شي مستعجل. ارفع الوقف مع الأسهم الرابحة.")})
    g, name = grade(score)
    return {"score": score, "grade": g, "name": name, "factors": factors, "tips": tips[:4]}


# ---------------------------------------------------------------- achievements
def _month_best(curve):
    if curve is None or len(curve) < 2:
        return None
    e = curve["equity"]
    r = ((e - curve["flow"]) / e.shift(1) - 1).iloc[1:].replace([np.inf, -np.inf], np.nan).dropna()
    if not len(r):
        return None
    m = (1 + r).groupby([r.index.year, r.index.month]).prod() - 1
    return float(m.max()) * 100 if len(m) else None


def _drawdown_last(curve, n):
    """The deepest drop from a high (in %) over the last n sessions, None before two sessions."""
    if curve is None or len(curve) < 2:
        return None
    e = curve["equity"]
    r = ((e - curve["flow"]) / e.shift(1) - 1).iloc[1:].replace([np.inf, -np.inf], np.nan).dropna().tail(n)
    if not len(r):
        return None
    idx = (1 + r).cumprod()
    return float(min((idx / idx.cummax() - 1).min(), 0.0)) * 100


def badges(view, stats, state, sector_of):
    """The achievements: [{'key', 'icon', 'name': (en, ar), 'desc': (en, ar), 'earned', 'prog' (0-1), 'txt': (en, ar)}]."""
    fills = state.get("fills") or []
    orders = state.get("orders") or []
    pos = view.get("positions") or []
    trades = view.get("trades") or []
    n_f = len(fills)
    days = int(stats.get("days") or 0)
    ret = stats.get("twr", view.get("ret") or 0.0) or 0.0
    out = []

    def add(key, icon, name, desc, have, need, txt=None):
        prog = 1.0 if need <= 0 else max(0.0, min(1.0, have / need))
        out.append({"key": key, "icon": icon, "name": name, "desc": desc, "earned": prog >= 1.0, "prog": prog,
                    "txt": txt or (f"{min(have, need):g} / {need:g}", f"{min(have, need):g} / {need:g}")})

    add("first", "rocket_launch", ("First trade", "أول صفقة"), ("Your first order filled.", "تنفذ أول أمر لك."), n_f, 1)
    add("short", "trending_down", ("Short seller", "بائع على المكشوف"), ("Sold a stock short.", "بعت سهم على المكشوف."),
        sum(1 for f in fills if f.get("side") == "short"), 1)
    add("win", "emoji_events", ("First win", "أول ربح"), ("Closed a trade with a profit.", "سكّرت صفقة رابحة."),
        sum(1 for t in trades if t.get("pnl", 0) > 0), 1)
    covered = sum(1 for p in pos if protected(orders, p["sym"], p["qty"]))
    add("guard", "shield", ("Fully protected", "محمي بالكامل"), ("Every open position has a stop working.", "كل مراكزك المفتوحة عليها وقف."),
        covered if pos else 0, max(len(pos), 1), (f"{covered} / {len(pos)}", f"{covered} / {len(pos)}") if pos else ("—", "—"))
    nsec = len({sector_of(p["sym"]) or "Other" for p in pos})
    add("diverse", "hub", ("Diversified", "منوّع"), ("5 or more positions in 3 or more sectors.", "5 مراكز أو أكثر في 3 قطاعات أو أكثر."),
        min(len(pos) / 5, nsec / 3), 1, (f"{len(pos)} / 5 · {nsec} / 3", f"{len(pos)} / 5 · {nsec} / 3"))
    add("ten", "bolt", ("Active trader", "متداول نشط"), ("10 orders filled.", "10 أوامر منفذة."), n_f, 10)
    add("fifty", "local_fire_department", ("Market regular", "من أهل السوق"), ("50 orders filled.", "50 أمر منفذ."), n_f, 50)
    bret = stats.get("bench_ret")
    beat = days >= 20 and bret is not None and ret > bret
    if days < 20 or bret is None:
        have, txt = min(days, 19) / 20 * 0.9, (f"{min(days, 20)} / 20 sessions", f"{min(days, 20)} / 20 جلسة")
    elif beat:
        have, txt = 1, (f"ahead by {ret - bret:.1f}%", f"متقدم {ret - bret:.1f}%")
    else:
        have, txt = 0.9, (f"behind by {bret - ret:.1f}%", f"متأخر {bret - ret:.1f}%")
    add("beat", "military_tech", ("Beat the market", "تفوقت على السوق"),
        ("Ahead of the S&P 500 after 20 sessions or more.", "متقدم على S&P 500 بعد 20 جلسة أو أكثر."), have, 1, txt)
    mb = _month_best(view.get("curve"))
    add("green", "calendar_month", ("Green month", "شهر أخضر"), ("A calendar month up 3% or more.", "شهر كامل صاعد 3% أو أكثر."),
        max(mb or 0, 0), 3, (f"{max(mb or 0, 0):.1f}% / 3%", f"{max(mb or 0, 0):.1f}% / 3%"))
    add("up10", "rocket", ("Up 10%", "صاعد 10%"), ("The account is up 10% or more.", "الحساب صاعد 10% أو أكثر."),
        max(ret, 0), 10, (f"{max(ret, 0):.1f}% / 10%", f"{max(ret, 0):.1f}% / 10%"))
    nt = len(trades)
    wr = stats.get("win_rate") or 0
    sharp = nt >= 10 and wr >= 60
    add("sharp", "target", ("Sharpshooter", "قنّاص"), ("Win rate 60% or more over 10+ closed trades.", "نسبة فوز 60% أو أكثر على 10 صفقات مغلقة أو أكثر."),
        1 if sharp else (0.9 if nt >= 10 else min(nt, 9) / 10 * 0.9), 1, (f"{min(nt, 10)} / 10 · {wr:.0f}%", f"{min(nt, 10)} / 10 · {wr:.0f}%"))
    # the last 60 sessions without a 10% drop from their high (a bad stretch long ago doesn't lock it for good)
    dd60 = _drawdown_last(view.get("curve"), 60)
    calm = days >= 60 and dd60 is not None and dd60 > -10
    if calm:
        have = 1
    elif dd60 is not None and dd60 <= -10:
        have = 0.0
    else:
        have = min(days, 59) / 60 * 0.9
    dtxt = f" · {dd60:.1f}%" if dd60 is not None else ""
    add("calm", "self_improvement", ("Steady hands", "أعصاب ثابتة"), ("60 sessions in a row without a drop of 10% from the high.",
                                                                       "60 جلسة متتالية بدون هبوط 10% من القمة."),
        have, 1, (f"{min(days, 60)} / 60{dtxt}", f"{min(days, 60)} / 60{dtxt}"))
    divs = float((view.get("totals") or {}).get("divs") or 0)
    add("divs", "payments", ("Dividend collector", "جامع التوزيعات"), ("Received a dividend.", "استلمت توزيعات أرباح."),
        1 if divs > 0 else 0, 1, (f"${divs:,.2f}", f"{divs:,.2f}$"))
    return out


# ---------------------------------------------------------------- the P&L calendar
def pnl_days(curve, start_cash):
    """Profit and loss of each session in dollars (deposits and withdrawals are not gains)."""
    if curve is None or not len(curve):
        return pd.Series(dtype=float)
    e, f = curve["equity"].astype(float), curve["flow"].astype(float)
    prev = e.shift(1)
    prev.iloc[0] = float(start_cash)
    out = (e - f - prev).replace([np.inf, -np.inf], np.nan).dropna()
    out.index = pd.to_datetime(out.index)
    return out


def short_money(v):
    """+$798 · -$1.2k · +$12k · +$1.3M (for small calendar cells)."""
    if v is None or not math.isfinite(v):
        return "—"
    s = "+" if v > 0 else "-" if v < 0 else ""
    a = abs(v)
    if a >= 1e6:
        t = f"{a / 1e6:.1f}M"
    elif a >= 1e4:
        t = f"{a / 1e3:.0f}k"
    elif a >= 1e3:
        t = f"{a / 1e3:.1f}k"
    else:
        t = f"{a:.0f}"
    return f"{s}${t}"


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "19.9"
