"""
scripts/site_check.py - Opens the site's pages in a headless browser, the way a visitor would, on a GitHub server (run by
.github/workflows/sitecheck.yml): the site runs locally (`streamlit run app.py`, no secrets: the trial store), a few paper bots
are added first, then every page of the list is opened in English and Arabic, in the US and the Saudi market. It saves a
screenshot of each page and a report of what went wrong (a page that raised an error, a section that couldn't load) to
OUT (default site_check/).
"""
import json
import re
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.environ.get("OUT") or os.path.join(ROOT, "site_check")
PORT = 8599
URL = f"http://localhost:{PORT}"
os.makedirs(OUT, exist_ok=True)

# (name, path, market) - each page opened fresh with ?m=<market>&lang=<lang>
PAGES = [  # 22.4: the Discover pages (trending, news, the news engine) and a story's window, the charts' new look
         ("trending", "trending", "us"), ("news", "news", "us", '[class*="st-key-nwa_"] button'),
         ("newsintel", "news-intelligence", "us", '[class*="st-key-nie_cb_"] button'),
         ("sentiment", "sentiment", "us"), ("seasonality", "seasonality", "us"), ("stock", "stock?symbol=NVDA", "us"),
         ("sa_trending", "trending", "sa"), ("sa_news", "news", "sa", '[class*="st-key-nwa_"] button')]
QUICK_PAGES = [("bots_sa", "paper-bots", "sa")]
AUTH_DEMO = False     # a quick run: made-up sign-in settings, so the top line's Sign in button can be seen
FIN_PILL = {"en": "Net margin", "ar": "صافي الهامش"}
NAV_BROWSERS = False  # the top bar's menus in WebKit and Firefox too (a quick run)


def log(*a):
    print(*a, flush=True)


def seed_bots():
    """A few Saudi bots and one US bot in the trial store (the same temp file the site reads)."""
    import paperbots as PB
    import playbooks as PBK
    import markets as MK
    if PB.backend() != "local":
        return
    rows = [PB.make_record("أرامكو المتقاطع", "company", "2222", {"SMA Crossover": {"fast": 20, "slow": 50}}, 1, 100000, 0.155, 0, 3.0, 0, 0,
                           "2025-01-05", market=MK.SA),
            PB.make_record("البنوك", "industry", "Banks", {"RSI Mean Reversion": {}, "MACD Crossover": {}}, 4, 500000, 0.155, 0, 3.0, 0, 0,
                           "2025-03-02", market=MK.SA, regime=1),
            PB.make_record("السوق كامل", "all", "all", {k: {} for k in PBK.DAILY}, 8, 1000000, 0.155, 0, 0, 0, 0, "2025-06-01",
                           {"mode": "any"}, market=MK.SA),
            PB.make_record("Apple trend", "company", "AAPL", {"SMA Crossover": {}}, 1, 100000, 0.05, 0, 3.0, 0, 0, "2025-01-06")]
    for r in rows:
        try:
            PB.create_bot(r)
        except Exception as e:
            log("seed", r["name"], e)
    log("seeded", len(PB.list_bots()), "bots")


def news_lab():
    """A real sample for tuning the news bot (news_us.json, news_sa.json: every headline of one round with its companies,
    keywords and score) and a contact sheet of every topic's photos (pics_*.jpg), so a wrong picture is seen at once."""
    import newsbot as NB
    import newsiq
    for name, bot in (("us", NB.NewsBot()), ("sa", NB.NewsBot(NB.SA_FEEDS, finder=NB.sa_tickers_in))):
        try:
            bot.collect(force=True)
            rows = []
            for n in bot.items(96):
                iq = newsiq.analyze(n)
                rows.append({"title": n["title"], "source": n["source"], "also": n.get("also"), "time": str(n["time"]),
                             "summary": (n.get("summary") or "")[:300], "tickers": n.get("tickers"), "cat": n.get("cat"),
                             "img": bool(n.get("img")), "score": iq["score"], "topics": iq["topics"], "pic": iq.get("pic"),
                             "kw": [k[1] for k in iq["keywords"]]})
            with open(os.path.join(OUT, f"news_{name}.json"), "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=0)
            log("news", name, len(rows))
        except Exception as e:
            log("news lab", name, e)
    try:
        import io
        import requests
        import newspics as NP
        from PIL import Image, ImageDraw
        NP.fill(budget=260)
        topics = list(NP.TOPIC_Q)
        W, H, PER = 240, 150, 8
        for part in range(0, len(topics), 5):
            group = topics[part:part + 5]
            sheet = Image.new("RGB", (W * PER, (H + 34) * len(group)), (14, 12, 22))
            dr = ImageDraw.Draw(sheet)
            for r, t in enumerate(group):
                pics = (NP._POOLS.get(t) or {}).get("pics") or []
                dr.text((6, r * (H + 34) + 2), f"{t} ({len(pics)})", fill=(255, 220, 120))
                for c, pic in enumerate(pics[:PER]):
                    try:
                        im = Image.open(io.BytesIO(requests.get(pic["u"], headers=NP.UA_WIKI, timeout=15).content)).convert("RGB")
                        im.thumbnail((W - 6, H - 6))
                        sheet.paste(im, (c * W + 3, r * (H + 34) + 16))
                    except Exception:
                        pass
                    dr.text((c * W + 3, r * (H + 34) + H + 16), str(pic.get("f") or "")[:38], fill=(200, 200, 210))
            sheet.save(os.path.join(OUT, f"pics_{part // 5}.jpg"), quality=78)
        with open(os.path.join(OUT, "pics.json"), "w", encoding="utf-8") as f:
            json.dump({t: [p.get("f") for p in (NP._POOLS.get(t) or {}).get("pics") or []] for t in topics}, f, ensure_ascii=False, indent=1)
    except Exception as e:
        log("pics lab", e)


def seed_xbots():
    """Sample posts for the X bots page's photos (clearly sample accounts; the site check has no X key): each bot reads them through
    its own engine, at the real latest prices, so the page shows a full reading, positions and trades."""
    import random
    import pandas as pd
    import markets as MK
    import xbots as XB
    rnd = random.Random(7)
    now = pd.Timestamp.now(tz="UTC").floor("min")
    texts = {
        "pulse": ["S&P 500 pushing to a new record high, breadth improving, bullish into the close 📈", "Stock market rally broadening, small caps joining 🚀",
                  "Wall Street nervous ahead of CPI, sellers in control, bearish tone", "Nasdaq rebounds strongly after the dip, buyers back"],
        "trend": ["$NVDA breaking out again, loading up calls 🚀", "$PLTR ripping to all-time highs, bullish", "$TSLA breakdown below support, bearish 📉",
                  "$NVDA demand is insane, strong beat incoming", "$AMD accumulating here, undervalued"],
        "pros": ["Earnings growth for $MSFT remains strong, upgrade to outperform", "$AAPL services margin record high, bullish setup",
                 "Breadth is weak, $SPY may struggle near term"],
        "flash": ["*NVIDIA BEATS ESTIMATES, RAISES GUIDANCE $NVDA", "*MICROSOFT WINS $10B CLOUD CONTRACT $MSFT", "*BOEING CUTS OUTLOOK $BA"],
        "contra": ["$TSLA is a bubble, dump it before it crashes 📉", "$META overvalued, selling everything, bearish", "$TSLA demand collapsing, short it",
                   "$NVDA still the best, bullish 🚀"],
        "tasi": ["تاسي يرتفع بدعم من البنوك، السوق إيجابي وصاعد 📈", "السوق السعودي يواصل الصعود، سيولة قوية ودخول", "تاسي يتراجع مع ضغط بيع على البتروكيماويات، سلبي",
                 "المؤشر العام يخترق المقاومة، فرصة شراء"],
        "sa_trend": ["أرامكو اختراق قوي مع ارتفاع أسعار النفط، فرصة دخول", "الراجحي يواصل الصعود بعد أرباح قوية، إيجابي", "سابك تراجع وكسر الدعم، سلبي",
                     "معادن قمة جديدة مع صعود الذهب، قوي"],
        "sa_pros": ["#تاسي الراجحي توصية شراء، الدعم 95 والهدف 105، اختراق", "#السوق_السعودي سابك كسر الدعم، وقف خسارة وخروج",
                    "#تاسي أرامكو نموذج صاعد، هدف 27، دخول"],
        "sa_flash": ["أرامكو تعلن ارتفاع أرباحها الفصلية 20% وتوزيعات نقدية", "الراجحي يوقع عقد تمويل بقيمة 5 مليارات ريال", "سابك تخفض توقعاتها للعام"],
        "oil": ["النفط يرتفع 3% بعد قرار أوبك+ خفض الإنتاج، برنت فوق 80 دولار، صاعد 📈", "Brent jumps as OPEC+ extends cuts, bullish for oil prices 🚀",
                "أسعار النفط تتراجع مع مخاوف الطلب، سلبي"],
    }
    users = [{"id": "u1", "username": "sample_trader", "name": "Sample Trader", "verified": False, "public_metrics": {"followers_count": 12000}},
             {"id": "u2", "username": "sample_analyst", "name": "Sample Analyst", "verified": True, "public_metrics": {"followers_count": 250000}}]

    class R:
        def __init__(self, js):
            self.js, self.status_code, self.text = js, 200, ""

        def json(self):
            return self.js
    meta = {}
    for bot in XB.BOTS:
        feed, i = [], 0
        for h in range(46, -1, -2):
            for _ in range(rnd.randint(1, 3) if h > 6 else rnd.randint(3, 5)):
                i += 1
                feed.append({"id": str(10_000_000 + i), "text": rnd.choice(texts[bot["id"]]),
                             "created_at": (now - pd.Timedelta(hours=h, minutes=rnd.randint(0, 50))).isoformat().replace("+00:00", "Z"),
                             "author_id": rnd.choice(["u1", "u2"]), "public_metrics": {"like_count": rnd.randint(5, 900), "retweet_count": rnd.randint(0, 200),
                                                                                    "reply_count": rnd.randint(0, 40), "quote_count": 0}})
        feed.sort(key=lambda p: -int(p["id"]))

        def get(url, params=None, headers=None, timeout=None, feed=feed):
            return R({"data": feed[:60], "includes": {"users": users}, "meta": {"newest_id": feed[0]["id"]}})
        try:
            XB.PER_RUN = 60
            state = XB.run(bot, "SAMPLE", meta, now=now, get=get, force=True)
            # a sample curve of the past four weeks, so the photos show the account charts (the real curve starts on the first run)
            eq, curve = XB.START_CASH, []
            for d in pd.bdate_range(end=now.tz_convert(None).normalize(), periods=22):
                eq *= 1 + rnd.gauss(0.0006, 0.007)
                curve.append({"d": d.date().isoformat(), "eq": round(eq, 2)})
            curve[-1]["eq"] = state["ledger"]["curve"][-1]["eq"] if state["ledger"]["curve"] else curve[-1]["eq"]
            state["ledger"]["curve"] = curve
            if state["ledger"]["trades"]:
                state["ledger"]["since"] = curve[0]["d"]
            # a sample log of the past six weeks (the evaluation's photos): each bot's readings and the next day's moves, with a
            # different link between the two per bot so every verdict shows; and a few closed sample trades for the metrics
            lean = {"pulse": 0.9, "trend": -0.12, "pros": 0.7, "flash": 1.0, "contra": -0.8, "tasi": 0.1, "sa_trend": 0.8, "sa_pros": -0.7,
                    "sa_flash": 0.9, "oil": 0.6}[bot["id"]]
            syms = ["NVDA", "AMD", "PLTR", "TSLA", "MSFT"] if bot["market"] == "us" else ["2222.SR", "1120.SR", "2010.SR", "1211.SR", "7010.SR"]
            if bot["style"] == "pulse":
                syms = [bot["ref"]]
            jl = state.get("_log") or XB.new_log(now)
            days_ = pd.bdate_range(end=now.tz_convert(None).normalize() - pd.Timedelta(days=1), periods=30 if bot["id"] != "oil" else 9)
            for d in days_:
                for sym in syms[: (1 if bot["style"] == "pulse" else 3)]:
                    tone_ = max(-1.0, min(1.0, rnd.gauss(0.05, 0.45)))
                    move = lean * tone_ * 2.2 + rnd.gauss(0, 1.1)
                    jl["sig"].append({"d": d.date().isoformat(), "t": d.isoformat() + "Z", "sym": sym, "s": round(tone_, 3), "n": rnd.randint(2, 9),
                                       "px": 100.0, "r1": round(move, 3), "r3": round(move * 1.4 + rnd.gauss(0, 1.5), 3)})
            jl["since"] = days_[0].isoformat() + "Z"
            state["_log"] = jl
            state["score"] = XB.scorecard(bot, jl["sig"])
            state["log_meta"] = {"since": jl["since"] + "", "hours": len(jl["hourly"]), "days": len({x["d"] for x in jl["sig"]}),
                                 "signals": len(jl["sig"]), "known": sum(1 for x in jl["sig"] if x.get("r1") is not None)}
            b0 = 100.0
            for c in state["ledger"]["curve"]:
                b0 *= 1 + rnd.gauss(0.0004, 0.008)
                c["b"] = round(b0, 3)
            for k in range(rnd.randint(3, 7)):
                pnl = round(rnd.gauss(1.0, 5.0), 2)
                t_ = now - pd.Timedelta(days=rnd.randint(2, 25))
                state["ledger"]["trades"].insert(0, {"t": t_.isoformat(), "sym": syms[k % len(syms)], "side": "sell", "qty": 10, "px": 100.0,
                                                     "why": "target" if pnl > 0 else "stop", "pnl": pnl,
                                                     "held_from": (t_ - pd.Timedelta(days=rnd.randint(1, 6))).isoformat()})
            state["perf"] = XB.perf(state["ledger"], state.get("reads"))
            XB.save_state(bot, state)
            log("xbots seed", bot["id"], len(state["posts"]), list(state["ledger"]["pos"]))
        except Exception as e:
            log("xbots seed", bot["id"], e)
    XB.save(XB.META, meta)


def chart_lab(b, report):
    """Every kind of chart drawn from made-up data with the site's last touch (charts.polish), on one page photographed
    (charts.jpg): the new look is seen without opening every page, and a chart that fails is named in the report."""
    import numpy as np
    import pandas as pd
    import charts as C
    rng = np.random.default_rng(7)
    idx = pd.bdate_range("2024-01-02", periods=420)
    walk = lambda s0, v: pd.Series(s0 * np.exp(np.cumsum(rng.normal(0.0004, v, len(idx)))), index=idx)
    a, bb, c = walk(100, 0.012), walk(100, 0.016), walk(100, 0.009)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    fg = pd.Series(np.clip(50 + np.cumsum(rng.normal(0, 4, len(idx))), 3, 97), index=idx)
    tries = [
        ("line", lambda: C.line(a, "Price")),
        ("area", lambda: C.area(a * 10, "Portfolio value")),
        ("norm_lines", lambda: C.norm_lines({"NVDA": a, "AMD": bb, "INTC": c}, "Growth of 100")),
        ("equity_chart", lambda: C.equity_chart(a * 1000, bb * 1000)),
        ("compare_bars", lambda: C.compare_bars(["2021", "2022", "2023", "2024", "2025"],
                                                {"Revenue": list(rng.uniform(40e9, 90e9, 5)), "Net income": list(rng.uniform(5e9, 30e9, 5))},
                                                "Revenue vs net income")),
        ("pct_bars", lambda: C.pct_bars(months, list(rng.normal(1, 4, 12)), "Monthly returns")),
        ("hbar", lambda: C.hbar(["Tech", "Health", "Energy", "Banks", "Retail"], list(rng.normal(0, 2, 5)), "Sectors today")),
        ("cash_trend", lambda: C.cash_trend(["2021", "2022", "2023", "2024", "2025"], list(rng.uniform(20e9, 40e9, 5)),
                                            list(-rng.uniform(5e9, 12e9, 5)), list(rng.uniform(10e9, 30e9, 5)), list(rng.uniform(15, 35, 5)))),
        ("season_bars", lambda: C.season_bars(months, list(rng.normal(0.8, 1.5, 12)), list(rng.uniform(35, 80, 12)), cur=9, title="Seasonality")),
        ("fg_history", lambda: C.fg_history(fg, "Fear & Greed", spx=a * 50)),
        ("lines", lambda: C.lines({"10Y": pd.Series(rng.normal(4.2, 0.1, 60).cumsum() / 15 + 3.8, index=idx[:60]),
                                    "2Y": pd.Series(rng.normal(4.0, 0.1, 60).cumsum() / 15 + 3.6, index=idx[:60])}, "Yields")),
        ("metric_bars", lambda: C.metric_bars(["2021", "2022", "2023", "2024", "2025"], list(rng.uniform(1e9, 9e9, 5)), "Free cash flow")),
        ("share_donut", lambda: C.share_donut(["AAPL", "MSFT", "NVDA", "Cash"], [30, 25, 35, 10], "Portfolio")),
        ("histogram", lambda: C.histogram(list(rng.normal(0, 2, 400)), "Today's moves")),
    ]
    parts, errs = [], {}
    for name, make in tries:
        try:
            fig = C.polish(make())
            parts.append(f'<div class="box"><div class="nm">{name}</div>'
                         + fig.to_html(full_html=False, include_plotlyjs=not parts, config={"displayModeBar": False}) + "</div>")
        except Exception as e:
            errs[name] = f"{type(e).__name__}: {e}"[:300]
    page = ('<html><head><meta charset="utf-8"><style>body{background:#0E0918;margin:0;padding:24px;font-family:sans-serif}'
            '.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.box{background:#1A1624;border-radius:18px;'
            'box-shadow:inset 0 0 0 1px #2C2738;overflow:hidden}.nm{color:#8F899B;font-size:12px;padding:8px 14px 0}</style></head>'
            '<body><div class="grid">' + "".join(parts) + "</div></body></html>")
    with open(os.path.join(OUT, "charts.html"), "w", encoding="utf-8") as f:
        f.write(page)
    report["charts"] = {"drawn": len(parts), "errors": errs}
    try:
        pg = b.new_page(viewport={"width": 1500, "height": 1000})
        pg.goto("file://" + os.path.join(OUT, "charts.html"))
        time.sleep(4)
        pg.screenshot(path=os.path.join(OUT, "charts.jpg"), type="jpeg", quality=80, full_page=True)
        pg.close()
    except Exception as e:
        report["charts"]["shot"] = str(e)[:300]
    log("charts", json.dumps(report["charts"])[:600])


def nav_probe(pg, tag, report):
    """Hovers every menu of the top bar and records what the browser shows: the element on top of the button, the menu's
    opacity and visibility, the "menu closed" flag; a photo of the bar with the first menu open (nav_<tag>.jpg)."""
    out = []
    try:
        n = pg.locator('[class*="st-key-navsec_"] .navbtn').count()
        for i in range(n):
            btn = pg.locator(f'.st-key-navsec_{i} .navbtn').first
            btn.hover(timeout=8000)
            time.sleep(0.6)
            info = pg.evaluate("""(i) => {
                const b = document.querySelector('.st-key-navsec_' + i + ' .navbtn'), dd = document.querySelector('.st-key-navdd_' + i);
                const r = b.getBoundingClientRect(), top = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
                const cs = dd ? getComputedStyle(dd) : null, rr = dd ? dd.getBoundingClientRect() : null;
                return {btn: b.innerText.trim(), onTop: top ? (top.className || top.tagName).toString().slice(0, 80) : null,
                        btnIsTop: !!(top && b.contains(top)), opacity: cs && cs.opacity, visibility: cs && cs.visibility,
                        menuBox: rr && [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)],
                        closedFlag: document.documentElement.hasAttribute('data-menu-closed'),
                        hovered: !!document.querySelector('.st-key-navsec_' + i + ':hover')};
            }""", i)
            out.append(info)
            if i == 0:
                vw = pg.viewport_size or {"width": 1440}
                pg.screenshot(path=os.path.join(OUT, f"nav_{tag}.jpg"), type="jpeg", quality=80, clip={"x": 0, "y": 0, "width": vw["width"], "height": 560})
        pg.mouse.move(700, 700)
    except Exception as e:
        out.append({"error": str(e)[:300]})
    report.setdefault("nav", {})[tag] = out
    log("nav", tag, json.dumps(out)[:900])


def settle(pg, limit=150):
    """Wait until the page has finished running (no 'Running...' status, no spinner) for 3 seconds in a row."""
    t0, calm = time.time(), 0
    while time.time() - t0 < limit:
        busy = pg.evaluate("""() => !!(document.querySelector('[data-testid="stStatusWidget"]') ||
                                        document.querySelector('[data-testid="stSpinner"]') ||
                                        !document.querySelector('[data-testid="stAppViewContainer"]'))""")
        calm = 0 if busy else calm + 1
        if calm >= 3:
            return time.time() - t0
        time.sleep(1)
    return None


def problems(pg):
    return pg.evaluate("""() => {
        const out = [];
        document.querySelectorAll('[data-testid="stException"]').forEach(e => out.push('EXCEPTION: ' + e.innerText.slice(0, 1500)));
        document.querySelectorAll('[data-testid="stAlert"]').forEach(e => {
            const t = e.innerText;
            if (/couldn't load|تعذر تحميل|Traceback|Error/.test(t)) out.push('ALERT: ' + t.slice(0, 600));
        });
        return out; }""")


def shoot(pg, name):
    h = pg.evaluate("() => { const m = document.querySelector('[data-testid=\"stMainBlockContainer\"]'); return m ? m.scrollHeight + 160 : 900; }")
    pg.set_viewport_size({"width": 1440, "height": min(max(int(h), 900), 8000)})
    time.sleep(1.5)
    pg.screenshot(path=os.path.join(OUT, f"{name}.jpg"), type="jpeg", quality=72, full_page=True)


QUICK = False         # a quick run: the top bar's menus and two pages, no news/photo/chart labs


XB_SEED = ""            # the X bots' photos: "sample" (clearly-marked sample posts) · "resting" (the key in, before the market's day) · "" (no key)


def seed_resting():
    """The state right after the X key is added, before the market's first hour: every bot ran once and rests."""
    import pandas as pd
    import xbots as XB
    meta = {}
    for bot in XB.BOTS:
        st_ = XB.run(bot, "KEY", meta, now=pd.Timestamp("2026-10-11 03:00", tz="UTC"), get=lambda *a, **k: None, quotes_fn=lambda syms: {})
        XB.save_state(bot, st_)
    XB.save(XB.META, meta)


SHARIA = False        # a quick run: the Sharia section of a few companies (the Company tab), Arabic and English, desktop and phone
SHARIA_SYMS = ["2222.SR", "2010.SR", "AAPL"]


def sharia_check(b, report):
    """The stock page's Company tab, cut to its Sharia section (from its title to its last note)."""
    js_box = """() => { const h = [...document.querySelectorAll('.sec')].find(e => e.textContent.includes('mosque'));
        if (!h) return null; const notes = [...document.querySelectorAll('.shnote, .shres, .shpur')];
        const end = notes.length ? notes[notes.length - 1] : h; const a = h.getBoundingClientRect(), z = end.getBoundingClientRect();
        return {y: a.top - 12, h: z.bottom - a.top + 40}; }"""
    for lang in ("ar", "en"):
        for kind in ("desk", "phone", "light"):
            if kind != "desk" and lang == "en":
                continue
            vp = {"width": 390, "height": 844} if kind == "phone" else {"width": 1440, "height": 900}
            ctx = b.new_context(viewport=vp, locale="ar-SA" if lang == "ar" else "en-US", color_scheme="light" if kind == "light" else "dark",
                                is_mobile=kind == "phone", has_touch=kind == "phone")
            pg = ctx.new_page()
            for sym in SHARIA_SYMS if kind == "desk" else SHARIA_SYMS[:2]:
                name = f"sh_{lang}_{kind}_{sym.replace('.SR', '')}"
                try:
                    mk = "sa" if sym.endswith(".SR") else "us"
                    pg.goto(f"{URL}/stock?symbol={sym}&m={mk}&lang={lang}", wait_until="domcontentloaded", timeout=90000)
                    settle(pg, 180)
                    pg.locator('[data-testid="stTabs"] [role="tab"]').nth(1).click(timeout=20000)
                    time.sleep(2)
                    settle(pg, 150)
                    time.sleep(3)
                    box = pg.evaluate(js_box)
                    if box:                  # the page as tall as its content (the content scrolls inside Streamlit's own box)
                        h = pg.evaluate("() => { const m = document.querySelector('[data-testid=\"stMainBlockContainer\"]'); "
                                        "return m ? m.scrollHeight + 160 : 900; }")
                        vh = min(max(int(h), vp["height"]), 12000)
                        pg.set_viewport_size({"width": vp["width"], "height": vh})
                        time.sleep(2)
                        box = pg.evaluate(js_box) or box
                        y = max(0, min(box["y"], vh - 200))
                        pg.screenshot(path=os.path.join(OUT, f"{name}.jpg"), type="jpeg", quality=80,
                                      clip={"x": 0, "y": y, "width": vp["width"], "height": max(200, min(box["h"], vh - y))})
                        pg.set_viewport_size(vp)
                    else:
                        shoot(pg, name)
                    report["pages"][name] = {"problems": problems(pg), "found": bool(box)}
                except Exception as e:
                    report["pages"][name] = {"error": str(e)[:400]}
            ctx.close()


TOUR = False          # the whole site in Arabic: every page, US and (where it has one) Saudi, on a desktop and on a phone
TOUR_PAGES = [("overview", 1), ("futures", 0), ("options", 0), ("economy", 0), ("trending", 1), ("news", 1), ("news-intelligence", 1),
              ("stock?symbol=NVDA", 0), ("stock?symbol=2222.SR", 2), ("screener", 1), ("brief", 1), ("articles", 1), ("sentiment", 1),
              ("seasonality", 1), ("earnings-calendar", 1), ("earnings-results", 1), ("economic-calendar", 1), ("market-holidays", 1),
              ("dividend-calendar", 1), ("stock-splits", 1), ("ipo-calendar", 0), ("academy", 1), ("glossary", 1), ("portfolio", 1),
              ("portfolio-trade", 1), ("portfolio-analytics", 1), ("portfolio-history", 1), ("robo-advisor", 1), ("paper-bots", 1),
              ("scanner", 1), ("x-bots", 1)]


TOUR_PHONE = False    # the tour on a phone only: three screens of every page, a check of what overflows or is too small to read
#                     or tap, and desktop photos of a few pages (to compare: the phone's fixes must not move the desktop)
DESK_CHECK = [("overview", "sa"), ("news", "sa"), ("stock?symbol=2222.SR", "sa"), ("paper-bots", "sa"), ("scanner", "sa"), ("x-bots", "sa"),
              ("portfolio", "sa"), ("trending", "us")]
MAIN_H = """() => { const m = document.querySelector('[data-testid="stMainBlockContainer"]'); return m ? m.scrollHeight + 160 : 900; }"""
PHONE_AUDIT = """() => {
  const W = window.innerWidth, out = {wide: [], small_text: 0, small_tap: [], fixed: []};
  const seen = new Set();
  document.querySelectorAll('body *').forEach(e => {
    const r = e.getBoundingClientRect();
    if (!r.width || !r.height) return;
    const cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity === 0) return;
    let p = e.parentElement, clipped = false;
    while (p && p !== document.body) { const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll' || o === 'hidden') { clipped = true; break; } p = p.parentElement; }
    if (!clipped && (r.right > W + 2 || r.left < -2) && r.width < 3000) {
      const k = (e.className && e.className.baseVal === undefined ? String(e.className) : e.tagName).slice(0, 60);
      if (!seen.has(k)) { seen.add(k); out.wide.push([k, Math.round(r.left), Math.round(r.right)]); }
    }
    if (e.childNodes.length && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 1) && parseFloat(cs.fontSize) < 11) out.small_text++;
    if ((e.tagName === 'BUTTON' || e.tagName === 'A' || e.getAttribute('role') === 'button') && r.height < 30 && r.width > 0) {
      const t = (e.innerText || e.getAttribute('aria-label') || '').trim().slice(0, 30);
      if (out.small_tap.length < 12) out.small_tap.push([t, Math.round(r.width), Math.round(r.height)]);
    }
    if ((cs.position === 'fixed' || cs.position === 'sticky') && r.height > 40 && out.fixed.length < 8) out.fixed.push([String(e.className).slice(0, 50), Math.round(r.top), Math.round(r.height)]);
  });
  out.wide = out.wide.slice(0, 15);
  return out; }"""


PHONE_QUICK = []
#              a short phone tour while the phone's look is being worked on ([] = every page); with it, how the top bar is built,
#              the AI button's insides, and photos of the bar at work (scrolled down, back up, a menu opened, the menus slid)
DOM_OUTLINE = """(sel) => { const root = document.querySelector(sel); if (!root) return null;
  const walk = (e, dep) => { const cs = getComputedStyle(e), r = e.getBoundingClientRect();
    const me = [e.tagName.toLowerCase(), e.getAttribute('data-testid') || '', String(e.className && e.className.baseVal === undefined ? e.className : '').split(' ').filter(c => !c.startsWith('st-emotion') && !/^e[a-z0-9]{5,}$/.test(c)).join('.'),
      cs.position, cs.overflowX, Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height), (e.children.length ? '' : (e.textContent || '').trim().slice(0, 20))];
    return dep > 0 && e.children.length ? [me, [...e.children].slice(0, 12).map(c => walk(c, dep - 1))] : [me]; };
  return walk(root, 7); }"""


def phone_bar(pp, report):
    """The top bar on a phone at work, and how it and the AI button are built."""
    out = {}
    for sel in ('[data-testid="stLayoutWrapper"]:has(> .st-key-topnav)', '.st-key-alturaifi_ai_fab'):
        try:
            out[sel] = pp.evaluate(DOM_OUTLINE, sel)
        except Exception as e:
            out[sel] = str(e)[:200]
    try:
        out["scroller"] = pp.evaluate("""() => [...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 50 &&
            /auto|scroll/.test(getComputedStyle(e).overflowY)).map(e => (e.getAttribute('data-testid') || e.tagName) + ':' + e.scrollHeight).slice(0, 5)""")
        out["html_class"] = pp.evaluate("() => document.documentElement.className")
        go = """(dy) => { const m = document.querySelector('[data-testid="stMain"]') || document.querySelector('section.stMain'); if (m) m.scrollBy(0, dy); window.scrollBy(0, dy); }"""
        for i, dy in enumerate((260, 260, 260)):
            pp.evaluate(go, dy)
            time.sleep(0.25)
        time.sleep(0.8)
        out["after_down"] = pp.evaluate("() => document.documentElement.className")
        pp.screenshot(path=os.path.join(OUT, "bar_1_down.jpg"), type="jpeg", quality=62)
        pp.evaluate(go, -60)
        time.sleep(0.25)
        pp.evaluate(go, -60)
        time.sleep(0.8)
        out["after_up"] = pp.evaluate("() => document.documentElement.className")
        pp.screenshot(path=os.path.join(OUT, "bar_2_up.jpg"), type="jpeg", quality=62)
        pp.evaluate(go, -5000)
        time.sleep(0.8)
        nb = pp.locator('.st-key-navsec_3 .navbtn').first
        nb.tap(timeout=5000)
        time.sleep(0.8)
        pp.screenshot(path=os.path.join(OUT, "bar_3_menu.jpg"), type="jpeg", quality=62)
        pp.locator('.langbtn').first.tap(timeout=5000)
        time.sleep(0.8)
        pp.screenshot(path=os.path.join(OUT, "bar_4_lang.jpg"), type="jpeg", quality=62)
    except Exception as e:
        out["error"] = str(e)[:300]
    report["phone_bar"] = out
    log("phone bar", json.dumps(out, ensure_ascii=False)[:3000])


def tour_phone(b, report):
    """Every page in Arabic on a phone (390 x 844): its first three screens, and what is wider than the screen, too small to
    read (under 11 px) or too small to tap (under 30 px); then a few pages on a desktop screen, for comparison."""
    report["tour"] = {}
    phone = b.new_context(viewport={"width": 390, "height": 844}, locale="ar-SA", color_scheme="dark", is_mobile=True, has_touch=True,
                          device_scale_factor=2)
    pp = phone.new_page()
    pp.goto(f"{URL}/?lang=ar", wait_until="domcontentloaded", timeout=90000)
    settle(pp, 180)
    for path, sa in (PHONE_QUICK or TOUR_PAGES):
        for mk in (("us",) if sa == 0 else ("sa",) if sa == 2 else ("us", "sa")):
            name = re.sub(r"[^a-z0-9]+", "_", f"{path}_{mk}").strip("_")
            sep = "&" if "?" in path else "?"
            row = {}
            try:
                if PHONE_QUICK and path == "news":
                    pp.set_viewport_size({"width": 390, "height": 844})
                    pp.goto(f"{URL}/{path}{sep}m={mk}&lang=ar", wait_until="domcontentloaded", timeout=90000)
                    settle(pp, 150)
                    time.sleep(1.5)
                    phone_bar(pp, report)
                pp.set_viewport_size({"width": 390, "height": 844})
                pp.goto(f"{URL}/{'' if path == 'overview' else path}{sep}m={mk}&lang=ar", wait_until="domcontentloaded", timeout=90000)
                row["s"] = settle(pp, 150)
                row["audit"] = pp.evaluate(PHONE_AUDIT)
                row["problems"] = problems(pp)
                if PHONE_QUICK:                   # how the page's first switch row is built (segmented controls on phones)
                    row["seg"] = pp.evaluate(DOM_OUTLINE, '[data-testid="stButtonGroup"]')
                    row["tabs"] = pp.evaluate(DOM_OUTLINE, '[data-testid="stTabs"] [role="tablist"]')
                pp.screenshot(path=os.path.join(OUT, f"q_{name}.jpg"), type="jpeg", quality=62)       # the first screen, as a phone shows it
                h = pp.evaluate(MAIN_H)
                row["height"] = int(h)
                pp.set_viewport_size({"width": 390, "height": min(max(int(h), 844), 3 * 844)})
                time.sleep(1.2)
                pp.screenshot(path=os.path.join(OUT, f"p_{name}.jpg"), type="jpeg", quality=62)
            except Exception as e:
                row["error"] = str(e)[:300]
            report["tour"][name] = row
            log("phone", name, json.dumps(row, ensure_ascii=False)[:400])
    phone.close()
    desk = b.new_context(viewport={"width": 1440, "height": 900}, locale="ar-SA", color_scheme="dark")
    pd_ = desk.new_page()
    for path, mk in DESK_CHECK:
        name = re.sub(r"[^a-z0-9]+", "_", f"{path}_{mk}").strip("_")
        sep = "&" if "?" in path else "?"
        try:
            pd_.set_viewport_size({"width": 1440, "height": 900})
            pd_.goto(f"{URL}/{'' if path == 'overview' else path}{sep}m={mk}&lang=ar", wait_until="domcontentloaded", timeout=90000)
            settle(pd_, 150)
            time.sleep(1.5)
            h = int(pd_.evaluate(MAIN_H))
            report["tour"]["desk_" + name] = {"height": h}
            if path == "news":                    # the top bar's every box on a computer (1440 and a laptop's 1100): to compare
                for vw in (1440, 1100, 800):
                    pd_.set_viewport_size({"width": vw, "height": 900})
                    time.sleep(1.2)
                    report["desk_bar_%d" % vw] = pd_.evaluate(DOM_OUTLINE, '[data-testid="stLayoutWrapper"]:has(> .st-key-topnav)')
                    report["desk_fab_%d" % vw] = pd_.evaluate(DOM_OUTLINE, '.st-key-alturaifi_ai_fab')
            pd_.set_viewport_size({"width": 1440, "height": min(max(h, 900), 2700)})
            time.sleep(1.2)
            pd_.screenshot(path=os.path.join(OUT, f"d_{name}.jpg"), type="jpeg", quality=60)
        except Exception as e:
            report["tour"]["desk_" + name] = {"error": str(e)[:300]}
    desk.close()


def tour(b, report):
    """Every page in Arabic: (US, and Saudi where the page has a Saudi version; 2 = Saudi only) a full-page photo on a 1440 px
    screen and the first screen on a phone (390 x 844), with the seconds each took to finish and any error on it."""
    report["tour"] = {}
    desk = b.new_context(viewport={"width": 1440, "height": 900}, locale="ar-SA", color_scheme="dark")
    phone = b.new_context(viewport={"width": 390, "height": 844}, locale="ar-SA", color_scheme="dark", is_mobile=True, has_touch=True,
                          device_scale_factor=2)
    pd_, pp = desk.new_page(), phone.new_page()
    t0 = time.time()
    pd_.goto(f"{URL}/?lang=ar", wait_until="domcontentloaded", timeout=90000)
    report["tour"]["cold_start"] = {"seconds": settle(pd_, 180), "wall": time.time() - t0}
    for path, sa in TOUR_PAGES:
        for mk in (("us",) if sa == 0 else ("sa",) if sa == 2 else ("us", "sa")):
            name = re.sub(r"[^a-z0-9]+", "_", f"{path}_{mk}").strip("_")
            sep = "&" if "?" in path else "?"
            url = f"{URL}/{path}{sep}m={mk}&lang=ar"
            row = {}
            try:
                pd_.set_viewport_size({"width": 1440, "height": 900})
                t1 = time.time()
                pd_.goto(url, wait_until="domcontentloaded", timeout=90000)
                row["desk_s"] = settle(pd_, 150)
                row["desk_wall"] = round(time.time() - t1, 1)
                row["problems"] = problems(pd_)
                h = pd_.evaluate("() => { const m = document.querySelector('[data-testid=\"stMainBlockContainer\"]'); return m ? m.scrollHeight + 160 : 900; }")
                row["height"] = int(h)
                pd_.set_viewport_size({"width": 1440, "height": min(max(int(h), 900), 7000)})
                time.sleep(1.2)
                pd_.screenshot(path=os.path.join(OUT, f"t_{name}.jpg"), type="jpeg", quality=55, full_page=True)
            except Exception as e:
                row["desk_error"] = str(e)[:300]
            try:
                t1 = time.time()
                pp.goto(url, wait_until="domcontentloaded", timeout=90000)
                row["phone_s"] = settle(pp, 150)
                row["phone_overflow"] = pp.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
                pp.screenshot(path=os.path.join(OUT, f"m_{name}.jpg"), type="jpeg", quality=60)
            except Exception as e:
                row["phone_error"] = str(e)[:300]
            report["tour"][name] = row
            log("tour", name, json.dumps(row, ensure_ascii=False)[:300])
    desk.close()
    phone.close()


LIVE = False          # look at the live site from GitHub's server (what a visitor sees there right now), nothing else
LIVE_URL = "https://abdulrahman.streamlit.app"
LIVE_PATH = "stock?symbol=2222.SR&m=sa&lang=ar"   # a page of the live site to look at ("": the home page, on a phone and a computer)


def live_probe():
    """The live site on a phone and on a computer: photos after 15, 45, 90 and 150 seconds, the text every frame shows (the app,
    or Streamlit Cloud's own notice: waking up, updating, an error) and the browser's errors."""
    from playwright.sync_api import sync_playwright
    report = {"live": {}, "started": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for kind, args in ((("phone", dict(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2)),
                            ("desk", dict(viewport={"width": 1440, "height": 900}))) if not LIVE_PATH else
                           (("desk", dict(viewport={"width": 1440, "height": 900})),)):
            ctx = b.new_context(locale="ar-SA", color_scheme="dark", **args)
            pg = ctx.new_page()
            errs = []
            pg.on("console", lambda m, errs=errs: errs.append(m.text[:240]) if m.type == "error" else None)
            pg.on("pageerror", lambda e, errs=errs: errs.append("pageerror: " + str(e)[:240]))
            row, t0 = {}, time.time()
            try:
                pg.goto(LIVE_URL + "/" + (LIVE_PATH or "?lang=ar"), wait_until="domcontentloaded", timeout=120000)
                row["goto_s"] = round(time.time() - t0, 1)
            except Exception as e:
                row["goto_error"] = str(e)[:300]
            for at in ((60, 330, 420) if LIVE_PATH else (15, 45, 90, 150)):
                time.sleep(max(0.0, at - (time.time() - t0)))
                if LIVE_PATH and at == 330:             # the page drawn again: what the bot has read since the first visit
                    try:
                        pg.goto(LIVE_URL + "/" + LIVE_PATH, wait_until="domcontentloaded", timeout=120000)
                        time.sleep(40)
                    except Exception as e:
                        row["reload_error"] = str(e)[:200]
                frames = []
                for fr in pg.frames:
                    try:
                        frames.append([fr.url[:90], fr.evaluate("() => ({text: (document.body ? document.body.innerText : '').slice(0, 500), "
                                                                "aibar: [...document.querySelectorAll('.aibar')].map(e => e.innerText).join(' | '), "
                                                                "pulse: (document.querySelector('.pulse') || {}).innerText || '', "
                                                                "whys: [...document.querySelectorAll('.nwhy')].slice(0, 12).map(e => e.innerText.slice(0, 140)), "
                                                                "chips: [...document.querySelectorAll('.news .kw')].slice(0, 12).map(e => e.innerText.replace(/\\s+/g, ' ').slice(0, 80)), "
                                                                "scores: [...document.querySelectorAll('.news .iq .n')].slice(0, 25).map(e => e.innerText), "
                                                                "rels: [...document.querySelectorAll('.nrel summary')].slice(0, 8).map(e => e.innerText), "
                                                                "why: document.querySelectorAll('.nwhy').length, rel: document.querySelectorAll('.nrel').length, "
                                                                "cards: [...document.querySelectorAll('.news .nb a.t')].slice(0, 25).map(a => a.innerText.slice(0, 90)), "
                                                                "bar: !!document.querySelector('.st-key-topnav'), "
                                                                "running: !!document.querySelector('[data-testid=\"stStatusWidget\"]'), "
                                                                "ver: (document.querySelector('.css-anchor') ? 'app' : '')})")])
                    except Exception as e:
                        frames.append([fr.url[:90], "ERR " + str(e)[:120]])
                row[f"t{at}"] = {"url": pg.url[:120], "frames": frames}
                if at == 60 and LIVE_PATH:              # which version is running: the ⋮ menu's About
                    for fr in pg.frames:
                        try:
                            if fr.locator('[data-testid="stMainMenu"]').count():
                                fr.locator('[data-testid="stMainMenu"]').first.click(timeout=8000)
                                time.sleep(1)
                                fr.get_by_text("About").first.click(timeout=8000)
                                time.sleep(1.5)
                                row["version"] = fr.evaluate("() => (document.querySelector('[role=\"dialog\"]') || {}).innerText || ''")[:200]
                                fr.keyboard.press("Escape") if hasattr(fr, "keyboard") else pg.keyboard.press("Escape")
                                break
                        except Exception as e:
                            row["version_error"] = str(e)[:200]
                if LIVE_PATH and at == 420:             # a card with the bot's reading, scrolled into view
                    for fr in pg.frames:
                        try:
                            if fr.locator('.nwhy').count():
                                fr.locator('.nwhy').first.scroll_into_view_if_needed(timeout=8000)
                                fr.evaluate("() => { const m = document.querySelector('[data-testid=\"stMain\"]'); if (m) m.scrollBy(0, -180); }")
                                time.sleep(1.5)
                                pg.screenshot(path=os.path.join(OUT, f"live_{kind}_why.jpg"), type="jpeg", quality=70)
                                break
                        except Exception as e:
                            row["why_error"] = str(e)[:200]
                try:
                    pg.screenshot(path=os.path.join(OUT, f"live_{kind}_{at}.jpg"), type="jpeg", quality=60)
                except Exception as e:
                    row[f"shot{at}"] = str(e)[:200]
                log("live", kind, at, json.dumps(row[f"t{at}"], ensure_ascii=False)[:1500])
            row["errors"] = errs[:25]
            report["live"][kind] = row
            ctx.close()
        b.close()
    json.dump(report, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0


MENU_CHECK = False    # the top menus: hovered and clicked on a computer, tapped on a phone, in Chrome's engine and in Safari's (WebKit)
MENU_VIS = """(sel) => { const dd = document.querySelector(sel); if (!dd) return null; const cs = getComputedStyle(dd), r = dd.getBoundingClientRect();
  const sec = dd.parentElement && dd.parentElement.closest('[class*="st-key-navsec_"], .st-key-langsec, .st-key-acctsec');
  return {shown: cs.visibility === 'visible' && +cs.opacity > .5, op: cs.opacity, vis: cs.visibility, x: Math.round(r.left), y: Math.round(r.top),
          w: Math.round(r.width), h: Math.round(r.height), open: !!(sec && sec.classList.contains('open')),
          hoverNone: matchMedia('(hover: none)').matches, js: document.documentElement.classList.contains('ix-js')}; }"""


PORTAL_VIS = """() => { const p = document.querySelector('.navportal'); if (!p) return {shown: false, none: true};
  const r = p.getBoundingClientRect(), cs = getComputedStyle(p), top = document.elementFromPoint(r.left + r.width / 2, r.top + Math.min(40, r.height / 2));
  return {shown: cs.visibility === 'visible' && +cs.opacity > .5 && r.height > 20, topmost: !!(top && p.contains(top)), x: Math.round(r.left),
          y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height), text: p.innerText.replace(/\s+/g, ' ').slice(0, 70),
          real: (() => { const d = document.querySelector('.st-key-topnav [class*="st-key-navdd_"]'); return d ? getComputedStyle(d).display : null; })()}; }"""


BOX_DUMP = """(sel) => { const root = document.querySelector(sel); if (!root) return null;
  const walk = (e, dep) => { const cs = getComputedStyle(e), r = e.getBoundingClientRect();
    const me = [e.tagName.toLowerCase(), e.getAttribute('data-testid') || '', String(e.className || '').split(' ').filter(c => c && !c.startsWith('st-emotion') && !/^e[a-z0-9]{5,}$/.test(c)).join('.'),
      cs.display, 'y' + Math.round(r.top), 'h' + Math.round(r.height), 'w' + Math.round(r.width), 'm:' + cs.margin, 'p:' + cs.padding, 'gap:' + cs.gap,
      (e.children.length ? '' : (e.textContent || '').trim().slice(0, 24))];
    return dep > 0 && e.children.length ? [me, [...e.children].slice(0, 10).map(c => walk(c, dep - 1))] : [me]; };
  return walk(root, 9); }"""


def menu_check(p, report):
    out = {}
    for eng in ("chromium", "webkit"):
        try:
            b = getattr(p, eng).launch()
        except Exception as e:
            out[eng] = {"error": str(e)[:200]}
            continue
        res = {}
        try:
            ctx = b.new_context(viewport={"width": 1440, "height": 900}, locale="ar-SA", color_scheme="dark")
            pg = ctx.new_page()
            pg.goto(f"{URL}/news?m=sa&lang=ar", wait_until="domcontentloaded", timeout=90000)
            settle(pg, 150)
            time.sleep(2)
            btn = pg.locator('.st-key-navsec_1 .navbtn').first
            btn.hover()
            time.sleep(0.7)
            res["desk_hover"] = pg.evaluate(MENU_VIS, '.st-key-navdd_1')
            res["desk_dom"] = pg.evaluate(BOX_DUMP, '.st-key-navdd_1')
            pg.screenshot(path=os.path.join(OUT, f"menu_{eng}_desk_hover.jpg"), type="jpeg", quality=60)
            btn.click()
            time.sleep(0.7)
            res["desk_click"] = pg.evaluate(MENU_VIS, '.st-key-navdd_1')
            pg.mouse.move(700, 700)
            time.sleep(0.7)
            res["desk_away"] = pg.evaluate(MENU_VIS, '.st-key-navdd_1')
            ctx.close()
        except Exception as e:
            res["desk_error"] = str(e)[:300]
        try:
            args = dict(viewport={"width": 390, "height": 844}, has_touch=True, device_scale_factor=2)
            if eng == "chromium":
                args["is_mobile"] = True
            else:
                args["user_agent"] = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
                                      "Version/18.0 Mobile/15E148 Safari/604.1")
                args["is_mobile"] = True
            ctx = b.new_context(locale="ar-SA", color_scheme="dark", **args)
            pg = ctx.new_page()
            pg.goto(f"{URL}/news?m=sa&lang=ar", wait_until="domcontentloaded", timeout=90000)
            settle(pg, 150)
            time.sleep(2)
            # first as it was before the taps were handled (the page script's flag off: focus and hover decide)
            pg.evaluate("() => document.documentElement.classList.remove('ix-js')")
            pg.locator('.st-key-navsec_1 .navbtn').first.tap()
            time.sleep(0.8)
            res["old_phone_tap"] = pg.evaluate(MENU_VIS, '.st-key-navdd_1')
            pg.screenshot(path=os.path.join(OUT, f"menu_{eng}_old_tap.jpg"), type="jpeg", quality=60)
            pg.touchscreen.tap(195, 700)
            time.sleep(0.6)
            pg.evaluate("() => { document.documentElement.classList.add('ix-js'); document.querySelectorAll('.open').forEach(e => e.classList.remove('open')); }")
            pg.locator('.st-key-navsec_1 .navbtn').first.tap()
            time.sleep(0.8)
            res["phone_tap"] = pg.evaluate(PORTAL_VIS)
            res["portal_dom"] = pg.evaluate(BOX_DUMP, '.navportal')
            pg.screenshot(path=os.path.join(OUT, f"menu_{eng}_phone_tap.jpg"), type="jpeg", quality=60)
            pg.locator('.st-key-navsec_2 .navbtn').first.tap()
            time.sleep(0.8)
            res["phone_other"] = [pg.evaluate(PORTAL_VIS), pg.evaluate("() => document.querySelectorAll('.navportal').length")]
            pg.locator('.st-key-navsec_2 .navbtn').first.tap()
            time.sleep(0.8)
            res["phone_again"] = pg.evaluate(PORTAL_VIS)
            pg.locator('.st-key-navsec_1 .navbtn').first.tap()
            time.sleep(0.6)
            pg.touchscreen.tap(195, 640)
            time.sleep(0.8)
            res["phone_away"] = pg.evaluate(PORTAL_VIS)
            card = "() => { const r = document.querySelector('.st-key-topnav').getBoundingClientRect(); return [Math.round(r.left), Math.round(r.bottom), Math.round(r.right)]; }"
            # the strip slid to its far end, then its last menu tapped
            pg.evaluate("() => { const s = document.querySelector('.st-key-navleft'); s.scrollLeft = -9999; s.scrollLeft = 9999 * (getComputedStyle(s).direction === 'rtl' ? -1 : 1); }")
            time.sleep(0.6)
            pg.locator('.st-key-navsec_7 .navbtn').first.tap()
            time.sleep(0.8)
            res["strip_end_tap"] = [pg.evaluate(PORTAL_VIS), pg.evaluate(card)]
            pg.screenshot(path=os.path.join(OUT, f"menu_{eng}_phone_end.jpg"), type="jpeg", quality=60)
            pg.touchscreen.tap(195, 760)
            time.sleep(0.6)
            # the page read down (the card frozen at the top), then a menu tapped
            pg.evaluate("() => { const m = document.querySelector('[data-testid=\"stMain\"]'); if (m) m.scrollBy(0, 900); window.scrollBy(0, 900); }")
            time.sleep(1)
            pg.locator('.st-key-navsec_0 .navbtn').first.tap()
            time.sleep(0.8)
            res["scrolled_tap"] = [pg.evaluate(PORTAL_VIS), pg.evaluate(card)]
            pg.screenshot(path=os.path.join(OUT, f"menu_{eng}_phone_scrolled.jpg"), type="jpeg", quality=60)
            pg.touchscreen.tap(195, 780)
            time.sleep(0.6)
            pg.evaluate("() => { const m = document.querySelector('[data-testid=\"stMain\"]'); if (m) m.scrollTo(0, 0); window.scrollTo(0, 0); }")
            time.sleep(0.8)
            pg.locator('.langbtn').first.tap()
            time.sleep(0.8)
            res["phone_lang"] = pg.evaluate(PORTAL_VIS)
            pg.screenshot(path=os.path.join(OUT, f"menu_{eng}_phone_lang.jpg"), type="jpeg", quality=60)
            try:
                pg.locator('.navportal [class*="st-key-langopt_en"] button').first.tap(timeout=5000)
                time.sleep(3)
                settle(pg, 60)
                res["lang_switch"] = pg.evaluate("() => (document.querySelector('.navbtn span:not(.ms)') || {}).innerText || ''")
                pg.locator('.langbtn').first.tap()
                time.sleep(0.8)
                pg.locator('.navportal [class*="st-key-langopt_ar"] button').first.tap(timeout=5000)
                time.sleep(3)
                settle(pg, 60)
                res["lang_back"] = pg.evaluate("() => (document.querySelector('.navbtn span:not(.ms)') || {}).innerText || ''")
            except Exception as e:
                res["lang_error"] = str(e)[:200]
            pg.touchscreen.tap(195, 700)
            time.sleep(0.6)
            pg.locator('.st-key-navsec_3 .navbtn').first.tap()
            time.sleep(0.8)
            pg.screenshot(path=os.path.join(OUT, f"menu_{eng}_phone_cal.jpg"), type="jpeg", quality=60)
            pg.locator('.navportal [data-testid="stPageLink"] a').nth(1).tap()
            time.sleep(3)
            settle(pg, 90)
            time.sleep(2)
            res["phone_after_link"] = {"url": pg.url[-40:], "dd": pg.evaluate(PORTAL_VIS),
                                       "h1": pg.evaluate("() => (document.querySelector('h1') || {}).innerText || ''")[:60]}
            pg.screenshot(path=os.path.join(OUT, f"menu_{eng}_phone_after.jpg"), type="jpeg", quality=60)
            pg.goto(f"{URL}/?lang=ar&m=sa", wait_until="domcontentloaded", timeout=90000)
            settle(pg, 120)
            time.sleep(2)
            pg.screenshot(path=os.path.join(OUT, f"menu_{eng}_phone_landing.jpg"), type="jpeg", quality=60)
            ctx.close()
        except Exception as e:
            res["phone_error"] = str(e)[:300]
        try:
            ctx = b.new_context(locale="ar-SA", color_scheme="light", viewport={"width": 390, "height": 844}, has_touch=True,
                                is_mobile=True, device_scale_factor=2)
            pg = ctx.new_page()
            pg.goto(f"{URL}/stock?symbol=AAPL&m=us&lang=ar", wait_until="domcontentloaded", timeout=90000)
            settle(pg, 150)
            time.sleep(3)
            pg.locator('.st-key-navsec_1 .navbtn').first.tap()
            time.sleep(0.8)
            pg.screenshot(path=os.path.join(OUT, f"menu_{eng}_light_tap.jpg"), type="jpeg", quality=70)
            pg.locator('.st-key-navsec_1 .navbtn').first.tap()
            time.sleep(0.5)
            pg.locator('.st-key-navsec_3 .navbtn').first.tap()
            time.sleep(0.8)
            pg.screenshot(path=os.path.join(OUT, f"menu_{eng}_light_cal.jpg"), type="jpeg", quality=70)
            res["light_dom"] = pg.evaluate(BOX_DUMP, '.navportal')
            ctx.close()
        except Exception as e:
            res["light_error"] = str(e)[:300]
        b.close()
        out[eng] = res
        log("menus", eng, json.dumps(res, ensure_ascii=False)[:2500])
    report["menus"] = out


BOXV2 = False         # a quick run: the new box signature (html.boxv2, added here only) and the AI button, before and after
BOX_PAGES = [("", "sa"), ("stock?symbol=2222.SR", "sa"), ("paper-bots", "sa"), ("news", "sa")]
BOX_PICK = """(skip) => { const S = '.kpi, .mcard, .card, .tile, .stat, .news, .story, .pbph, .lc, .tdc, .fgc, .czn, .shc, [data-testid="stMetric"]';
  const vh = innerHeight; const all = [...document.querySelectorAll(S)].filter(e => { const r = e.getBoundingClientRect();
    return r.width > 140 && r.height > 50 && r.top > 90 && r.bottom < vh - 20; });
  const e = all[skip] || all[0]; if (!e) return null; const r = e.getBoundingClientRect();
  return {x: r.left, y: r.top, w: r.width, h: r.height, cls: e.className.toString().slice(0, 60), n: all.length}; }"""
FAB_INFO = """() => { const f = document.querySelector('.st-key-alturaifi_ai_fab'), b = f && f.querySelector('[data-testid="stPopoverButton"]');
  const sb = document.querySelector('[data-testid="stSidebar"]'); const R = e => { if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; };
  return {fab: R(b), sidebar: R(sb), sb_open: sb && sb.getAttribute('aria-expanded'),
          sbw: getComputedStyle(document.documentElement).getPropertyValue('--sbw'), html: document.documentElement.className}; }"""


def box_check(b, report):
    out = {}
    def scroll_cards(pg):
        pg.evaluate("""() => { const e = document.querySelector('.kpi, .mcard, .card, .tile, .pbph, .news, .story, [data-testid="stMetric"]');
            if (e) { e.scrollIntoView({block: 'start'}); const m = document.querySelector('[data-testid="stMain"]'); if (m) m.scrollBy(0, -130); window.scrollBy(0, -130); } }""")
        time.sleep(1)
    def hover_shot(pg, name, skip=0):
        c = pg.evaluate(BOX_PICK, skip)
        if not c:
            return None
        pg.mouse.move(c["x"] + c["w"] * .3, c["y"] + c["h"] * .35)
        time.sleep(0.25)
        pg.mouse.move(c["x"] + c["w"] * .32, c["y"] + c["h"] * .4)
        time.sleep(0.9)
        vw = pg.viewport_size["width"]
        pad = 40
        x0, y0 = max(0, c["x"] - pad), max(0, c["y"] - pad)
        pg.screenshot(path=os.path.join(OUT, f"{name}.jpg"), type="jpeg", quality=82,
                      clip={"x": x0, "y": y0, "width": min(vw - x0, c["w"] + 2 * pad), "height": c["h"] + 2 * pad})
        return c
    for look in ("dark", "light"):
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, locale="ar-SA", color_scheme=look)
        pg = ctx.new_page()
        for path, mkt in (BOX_PAGES if look == "dark" else BOX_PAGES[:2]):
            tag = f"{look}_{path.split('?')[0] or 'overview'}"
            res = {}
            try:
                sep = "&" if "?" in path else "?"
                pg.goto(f"{URL}/{path}{sep}m={mkt}&lang=ar", wait_until="domcontentloaded", timeout=90000)
                settle(pg, 150)
                time.sleep(2.5)
                if pg.evaluate("() => !!document.querySelector('[class*=\"st-key-introgo_sa\"] button')"):   # the landing: the market picked
                    pg.evaluate("() => document.querySelector('[class*=\"st-key-introgo_sa\"] button').click()")
                    time.sleep(2)
                    settle(pg, 150)
                    time.sleep(2)
                scroll_cards(pg)
                pg.mouse.move(5, 895)
                pg.evaluate("() => document.documentElement.classList.remove('boxv2')")
                time.sleep(0.5)
                pg.screenshot(path=os.path.join(OUT, f"box_{tag}_before.jpg"), type="jpeg", quality=72)
                pg.evaluate("() => document.documentElement.classList.add('boxv2')")
                time.sleep(0.6)
                pg.screenshot(path=os.path.join(OUT, f"box_{tag}_after.jpg"), type="jpeg", quality=72)
                res["card"] = hover_shot(pg, f"box_{tag}_hover")
                res["card2"] = hover_shot(pg, f"box_{tag}_hover2", 2)
                res["problems"] = problems(pg)
                if path.startswith("stock"):
                    pg.mouse.move(700, 500)
                    time.sleep(0.5)
                    res["fab"] = pg.evaluate(FAB_INFO)
                    h = pg.viewport_size["height"]
                    pg.screenshot(path=os.path.join(OUT, f"fab_{look}_rest.jpg"), type="jpeg", quality=85,
                                  clip={"x": 0, "y": h - 200, "width": 620, "height": 200})
                    fb = pg.locator('.st-key-alturaifi_ai_fab [data-testid="stPopoverButton"]').first
                    res["fab_hit"] = pg.evaluate("""() => { const b = document.querySelector('.st-key-alturaifi_ai_fab [data-testid="stPopoverButton"]');
                        const r = b.getBoundingClientRect(), e = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                        return e ? (b.contains(e) ? 'button' : (e.tagName + '.' + e.className.toString().slice(0, 80))) : null; }""")
                    fr = res["fab"]["fab"]
                    pg.mouse.move(fr[0] + fr[2] / 2, fr[1] + fr[3] / 2)
                    time.sleep(1.2)
                    res["fab_hover"] = pg.evaluate(FAB_INFO)
                    pg.screenshot(path=os.path.join(OUT, f"fab_{look}_hover.jpg"), type="jpeg", quality=85,
                                  clip={"x": 0, "y": h - 200, "width": 620, "height": 200})
                    fb.click(timeout=8000, force=True)
                    time.sleep(2)
                    pg.mouse.move(1300, 300)
                    time.sleep(0.6)
                    pg.screenshot(path=os.path.join(OUT, f"fab_{look}_open.jpg"), type="jpeg", quality=78)
                    pg.keyboard.press("Escape")
                    time.sleep(0.6)
            except Exception as e:
                res["error"] = str(e)[:300]
            out[tag] = res
            log("box", tag, json.dumps(res, ensure_ascii=False)[:600])
        ctx.close()
    # a phone: the edge and sheen at rest, then a tap lighting a box; the AI button
    ctx = b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, device_scale_factor=2,
                        locale="ar-SA", color_scheme="dark")
    pg = ctx.new_page()
    for path, mkt in (BOX_PAGES[1], BOX_PAGES[3], BOX_PAGES[2]):
        tag = f"phone_{path.split('?')[0]}"
        res = {}
        try:
            pg.goto(f"{URL}/{path}{'&' if '?' in path else '?'}m={mkt}&lang=ar", wait_until="domcontentloaded", timeout=90000)
            settle(pg, 150)
            time.sleep(2.5)
            scroll_cards(pg)
            pg.evaluate("() => document.documentElement.classList.remove('boxv2')")
            time.sleep(0.4)
            pg.screenshot(path=os.path.join(OUT, f"box_{tag}_before.jpg"), type="jpeg", quality=70)
            pg.evaluate("() => document.documentElement.classList.add('boxv2')")
            time.sleep(0.6)
            pg.screenshot(path=os.path.join(OUT, f"box_{tag}_after.jpg"), type="jpeg", quality=70)
            c = pg.evaluate(BOX_PICK, 1)
            res["card"] = c
            if c:
                pg.evaluate("""([x, y]) => { const ev = (t, o) => document.elementFromPoint(x, y).dispatchEvent(new PointerEvent(t, Object.assign({bubbles: true,
                    clientX: x, clientY: y, pointerType: 'touch'}, o || {}))); ev('pointerdown'); ev('pointerup');
                    document.elementFromPoint(x, y).dispatchEvent(new MouseEvent('click', {bubbles: true, clientX: x, clientY: y})); }""",
                            [c["x"] + c["w"] * .5, c["y"] + c["h"] * .5])
                time.sleep(0.35)
                res["lit"] = pg.evaluate("() => (document.querySelector('.fx-on') || {className: ''}).className.toString().slice(0, 60)")
                pg.screenshot(path=os.path.join(OUT, f"box_{tag}_tap.jpg"), type="jpeg", quality=70)
            res["fab"] = pg.evaluate(FAB_INFO)
            res["problems"] = problems(pg)
        except Exception as e:
            res["error"] = str(e)[:300]
        out[tag] = res
        log("box", tag, json.dumps(res, ensure_ascii=False)[:600])
    try:
        pg.locator('.st-key-alturaifi_ai_fab [data-testid="stPopoverButton"]').first.tap()
        time.sleep(2)
        pg.screenshot(path=os.path.join(OUT, "fab_phone_open.jpg"), type="jpeg", quality=72)
    except Exception as e:
        out["phone_fab_error"] = str(e)[:300]
    ctx.close()
    report["box"] = out


STYLE_PICK = False    # a quick run: every box style and AI button on trial, filmed frame by frame on the overview (and still on the news)
BX = ["bx-a", "bx-b", "bx-c", "bx-d", "bx-e"]
FABS = ["", "fab2", "fab3", "fab4"]
SET_CLS = """([pre, v]) => { const h = document.documentElement; [...h.classList].filter(c => c.startsWith(pre)).forEach(c => h.classList.remove(c));
  if (v) h.classList.add(v); }"""
ROW = """() => { const t = [...document.querySelectorAll('.tile')].map(e => e.getBoundingClientRect()).filter(r => r.top > 80 && r.bottom < innerHeight - 40);
  const rows = {}; t.forEach(r => { const k = Math.round(r.top / 8); (rows[k] = rows[k] || []).push(r); });
  const best = Object.values(rows).filter(r => r.length >= 3).sort((a, b) => a[0].top - b[0].top)[0] || null;
  return best ? best.map(r => ({x: r.left, y: r.top, w: r.width, h: r.height})).sort((a, b) => b.x - a.x) : null; }"""


def film(pg, folder, clip, pts):
    os.makedirs(os.path.join(OUT, folder), exist_ok=True)
    t0, times = time.time(), []
    for i, pt in enumerate(pts):
        if pt:
            pg.mouse.move(pt[0], pt[1])
        pg.screenshot(path=os.path.join(OUT, folder, f"{i:03d}.jpg"), type="jpeg", quality=78, clip=clip)
        times.append(round(time.time() - t0, 3))
    return times


def glide(a, b, n):
    return [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(1, n + 1)]


def style_pick(b, report):
    out = {"films": {}}
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, locale="ar-SA", color_scheme="dark")
    pg = ctx.new_page()
    try:
        pg.goto(f"{URL}/?m=sa&lang=ar", wait_until="domcontentloaded", timeout=90000)
        settle(pg, 150)
        time.sleep(2)
        if pg.evaluate("() => !!document.querySelector('[class*=\"st-key-introgo_sa\"] button')"):
            pg.evaluate("() => document.querySelector('[class*=\"st-key-introgo_sa\"] button').click()")
            time.sleep(2)
            settle(pg, 150)
            time.sleep(2)
        pg.evaluate("""() => { const t = [...document.querySelectorAll('.tile')][2]; if (t) { t.scrollIntoView({block: 'center'});
            const m = document.querySelector('[data-testid="stMain"]'); if (m) m.scrollBy(0, -60); window.scrollBy(0, -60); } }""")
        time.sleep(1.5)
        row = pg.evaluate(ROW)
        out["row"] = row
        if row:
            x0 = max(0, min(r["x"] for r in row) - 28); x1 = min(1440, max(r["x"] + r["w"] for r in row) + 28)
            y0 = max(0, row[0]["y"] - 34); y1 = min(900, row[0]["y"] + row[0]["h"] + 120)
            clip = {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}
            out["clip"] = clip
            away = (x1 + 6 if x1 < 1430 else 1435, y0 - 30)
            for v in BX:
                pg.evaluate(SET_CLS, ["bx-", v])
                pg.mouse.move(*away)
                time.sleep(0.6)
                pts = [None] * 3
                cur = away
                for r in row[:3]:
                    a = (r["x"] + r["w"] * .78, r["y"] + r["h"] * .3)
                    pts += glide(cur, a, 4)
                    pts += glide(a, (r["x"] + r["w"] * .3, r["y"] + r["h"] * .62), 7)
                    cur = pts[-1]
                pts += glide(cur, (cur[0], y0 - 30), 3) + [None] * 3
                out["films"][v] = film(pg, f"film_{v}", clip, pts)
                log("film", v, len(pts))
        pg.evaluate(SET_CLS, ["bx-", "bx-a"])
        f = pg.evaluate(FAB_INFO)["fab"]
        out["fab_rect"] = f
        clip = {"x": max(0, f[0] - 26), "y": f[1] - 44, "width": 300, "height": min(900 - (f[1] - 44), f[3] + 66)}
        out["fab_clip"] = clip
        c = (f[0] + f[2] / 2, f[1] + f[3] / 2)
        for v in FABS:
            pg.evaluate(SET_CLS, ["fab", v])
            pg.mouse.move(c[0] + 420, c[1] - 260)
            time.sleep(0.8)
            pts = [None] * 8 + glide((c[0] + 140, c[1] - 90), c, 3) + [(c[0] + (k % 3) - 1, c[1]) for k in range(16)] + \
                glide(c, (c[0] + 200, c[1] - 160), 3) + [None] * 6
            out["films"][v or "fab1"] = film(pg, f"film_{v or 'fab1'}", clip, pts)
            log("film", v or "fab1", len(pts))
        pg.evaluate(SET_CLS, ["fab", ""])
        # the news page: a news card and a number box, resting and under the pointer, in each style
        pg.goto(f"{URL}/news?m=sa&lang=ar", wait_until="domcontentloaded", timeout=90000)
        settle(pg, 150)
        time.sleep(2.5)
        pg.evaluate("""() => { const e = document.querySelector('.news'); if (e) { e.scrollIntoView({block: 'center'}); } }""")
        time.sleep(1.2)
        r = pg.evaluate("() => { const e = document.querySelector('.news'); if (!e) return null; const r = e.getBoundingClientRect(); return {x: r.left, y: r.top, w: r.width, h: r.height}; }")
        out["news_card"] = r
        if r:
            clip = {"x": max(0, r["x"] - 30), "y": max(0, r["y"] - 30), "width": min(1440 - max(0, r["x"] - 30), r["w"] + 60), "height": min(900, r["h"] + 60)}
            for v in BX:
                pg.evaluate(SET_CLS, ["bx-", v])
                pg.mouse.move(5, 5)
                time.sleep(0.6)
                pg.screenshot(path=os.path.join(OUT, f"news_{v}_rest.jpg"), type="jpeg", quality=80, clip=clip)
                pg.mouse.move(r["x"] + r["w"] * .62, r["y"] + r["h"] * .3)
                time.sleep(0.25)
                pg.mouse.move(r["x"] + r["w"] * .6, r["y"] + r["h"] * .35)
                time.sleep(0.45)
                pg.screenshot(path=os.path.join(OUT, f"news_{v}_hover.jpg"), type="jpeg", quality=80, clip=clip)
        out["problems"] = problems(pg)
    except Exception as e:
        out["error"] = str(e)[:600]
    ctx.close()
    report["style_pick"] = out


ORB_CHECK = False     # a quick run: the AI button's sphere filmed resting and hovered (dark and light), its chat window, and on a phone


Z_INFO = """() => { const zi = e => { for (; e && e !== document.body; e = e.parentElement) { const z = getComputedStyle(e).zIndex;
    if (z !== 'auto') return z; } return 'auto'; };
  const q = s => document.querySelector(s); const pb = q('[data-testid="stPopoverBody"]');
  const all = [...document.querySelectorAll('.st-key-alturaifi_ai_fab *')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 70 || r.height > 70; })
    .map(e => (e.getAttribute('data-testid') || e.tagName) + ':' + Math.round(e.getBoundingClientRect().width) + 'x' + Math.round(e.getBoundingClientRect().height));
  return {sidebar: zi(q('[data-testid="stSidebar"]')), fab: zi(q('.st-key-alturaifi_ai_fab')), canvas: (q('canvas.ai-neural') || {style: {}}).style.zIndex,
          popover: pb ? zi(pb) : null, wide_inside_fab: all.slice(0, 8)}; }"""


FAB_STYLE = """() => { const f = document.querySelector('.st-key-alturaifi_ai_fab'), b = f && f.querySelector('[data-testid="stPopoverButton"]');
  if (!f || !b) return 'none'; const r = b.getBoundingClientRect();
  return getComputedStyle(f).position + ' ' + Math.round(r.width) + 'x' + Math.round(r.height); }"""


def sample_fab(pg, press, secs=8.0):
    """While the page is drawn again (after press()), how the AI button looks every 120 ms: fixed and round, or not."""
    seen = {}
    try:
        press()
    except Exception as e:
        return {"press_error": str(e)[:200]}
    t0 = time.time()
    while time.time() - t0 < secs:
        try:
            v = pg.evaluate(FAB_STYLE)
        except Exception:
            v = "eval-error"
        seen[v] = seen.get(v, 0) + 1
        time.sleep(0.12)
    return seen


def orb_check(b, report):
    out = {}
    for look in ("dark", "light"):
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, locale="ar-SA", color_scheme=look, device_scale_factor=2)
        pg = ctx.new_page()
        try:
            pg.goto(f"{URL}/stock?symbol=2222.SR&m=sa&lang=ar", wait_until="domcontentloaded", timeout=90000)
            settle(pg, 150)
            time.sleep(3)
            f = pg.evaluate(FAB_INFO)["fab"]
            out[f"{look}_fab"] = f
            out[f"{look}_z"] = pg.evaluate(Z_INFO)
            pg.screenshot(path=os.path.join(OUT, f"orb_{look}_rest.jpg"), type="jpeg", quality=82)
            pg.screenshot(path=os.path.join(OUT, f"orb_{look}_corner.png"), clip={"x": 0, "y": 900 - 240, "width": 420, "height": 240})
            out[f"{look}_canvas"] = pg.evaluate("""() => { const c = document.querySelector('canvas.ai-neural'); if (!c) return null; const r = c.getBoundingClientRect();
                return {r: [Math.round(r.left), Math.round(r.top), Math.round(r.width)], op: c.style.opacity, w: c.width}; }""")
            clip = {"x": max(0, f[0] - 30), "y": f[1] - 40, "width": 300, "height": min(900 - (f[1] - 40), f[3] + 70)}
            c = (f[0] + f[2] / 2, f[1] + f[3] / 2)
            pg.mouse.move(c[0] + 500, c[1] - 300)
            time.sleep(0.5)
            pts = [None] * 16 + [c] * 26 + [(c[0] + 500, c[1] - 300)] + [None] * 8
            out["films"] = out.get("films", {})
            out["films"][f"orb_{look}"] = film(pg, f"film_orb_{look}", clip, pts)
            pg.mouse.move(c[0] + 500, c[1] - 300)
            if look == "dark":                    # the label beside the button opens the chat too
                pg.mouse.click(f[0] + f[2] + 70, c[1])
                time.sleep(1.5)
                out["label_opens"] = pg.evaluate("() => document.querySelector('.st-key-alturaifi_ai_fab [data-testid=\"stPopoverButton\"]').getAttribute('aria-expanded')")
            else:
                pg.locator('.st-key-alturaifi_ai_fab [data-testid="stPopoverButton"]').first.click(timeout=8000, force=True)
            time.sleep(2.5)
            pg.mouse.move(1300, 300)
            time.sleep(0.5)
            pg.screenshot(path=os.path.join(OUT, f"orb_{look}_open.jpg"), type="jpeg", quality=80)
            out[f"{look}_z_open"] = pg.evaluate(Z_INFO)
            pb = pg.evaluate("() => { const e = document.querySelector('[data-testid=\"stPopoverBody\"]'); if (!e) return null; const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }")
            out[f"{look}_panel"] = pb
            if pb:
                win = {"x": max(0, pb[0] - 12), "y": max(0, pb[1] - 12), "width": min(1440 - max(0, pb[0] - 12), pb[2] + 24), "height": min(900 - max(0, pb[1] - 12), pb[3] + 24)}
                pg.screenshot(path=os.path.join(OUT, f"win_{look}_empty.png"), clip=win)
                pg.mouse.move(pb[0] + 60, pb[1] + pb[3] * .55)        # a suggested question hovered
                time.sleep(.6)
                pg.screenshot(path=os.path.join(OUT, f"win_{look}_hover.png"), clip=win)
                if look == "dark":
                    out["fab_html"] = pg.evaluate("() => { const b = document.querySelector('.st-key-alturaifi_ai_fab [data-testid=\"stPopoverButton\"]'); return b ? b.outerHTML.replace(/\\s+/g, ' ').slice(0, 2500) : null; }")
                    inp = pg.locator('div.st-key-alturaifi_ai_prompt input').first
                    inp.click(timeout=8000)
                    inp.fill("ما هو مؤشر القوة النسبية؟")
                    pg.screenshot(path=os.path.join(OUT, "win_dark_typing.png"), clip=win)
                    inp.press("Enter")
                    time.sleep(.35)
                    pg.screenshot(path=os.path.join(OUT, "win_dark_sending.png"), type="jpeg", quality=82)
                    out["typing_shown"] = pg.evaluate("() => !!document.querySelector('.ai-typing')")
                    time.sleep(4)
                    pb2 = pg.evaluate("() => { const e = document.querySelector('[data-testid=\"stPopoverBody\"]'); if (!e) return null; const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }")
                    out["dark_panel_chat"] = pb2
                    out["typing_after"] = pg.evaluate("() => !!document.querySelector('.ai-typing')")
                    if pb2:
                        pg.screenshot(path=os.path.join(OUT, "win_dark_chat.png"), clip={"x": max(0, pb2[0] - 12), "y": max(0, pb2[1] - 12),
                                      "width": min(1440 - max(0, pb2[0] - 12), pb2[2] + 24), "height": min(900 - max(0, pb2[1] - 12), pb2[3] + 24)})
            out[f"{look}_head"] = pg.evaluate("() => !!document.querySelector('.ai-orb canvas.ai-neural')")
            out[f"{look}_problems"] = problems(pg)
            if look == "dark":
                pg.keyboard.press("Escape")
                time.sleep(1)
                out["desk_page_switch"] = sample_fab(pg, lambda: pg.evaluate(
                    "() => { const a = [...document.querySelectorAll('a[href]')].find(x => /\\/news|\\/overview|\\/brief/.test(x.getAttribute('href') || '')); if (a) a.click(); return !!a; }"))
        except Exception as e:
            out[f"{look}_error"] = str(e)[:400]
        ctx.close()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, device_scale_factor=3, locale="ar-SA", color_scheme="dark")
    pg = ctx.new_page()
    try:
        pg.goto(f"{URL}/news?m=sa&lang=ar", wait_until="domcontentloaded", timeout=90000)
        settle(pg, 150)
        time.sleep(3)
        f = pg.evaluate(FAB_INFO)["fab"]
        out["phone_fab"] = f
        pg.screenshot(path=os.path.join(OUT, "orb_phone.jpg"), type="jpeg", quality=78)
        out["films"]["orb_phone"] = film(pg, "film_orb_phone", {"x": 0, "y": f[1] - 30, "width": 200, "height": 844 - (f[1] - 30)}, [None] * 18)
        pg.locator('.st-key-alturaifi_ai_fab [data-testid="stPopoverButton"]').first.tap()
        time.sleep(2.5)
        pg.screenshot(path=os.path.join(OUT, "orb_phone_open.jpg"), type="jpeg", quality=78)
        pg.goto(f"{URL}/news?m=sa&lang=ar", wait_until="domcontentloaded", timeout=90000)
        settle(pg, 150)
        time.sleep(2)
        import re as _re
        out["phone_rerun"] = sample_fab(pg, lambda: pg.get_by_role("button", name=_re.compile("تحديث")).first.tap(timeout=8000))
        out["phone_page_switch"] = sample_fab(pg, lambda: pg.evaluate(
            "() => { const a = [...document.querySelectorAll('a[href]')].find(x => /\\/stock|\\/overview|\\/brief/.test(x.getAttribute('href') || '')); if (a) a.click(); return !!a; }"))
    except Exception as e:
        out["phone_error"] = str(e)[:400]
    ctx.close()
    report["orb"] = out


LOOK_LANG = False     # a quick run: a first visit opens in the light look and in the phone's language; a language picked is kept


def _follow_look():
    """Every test browser follows its own colour scheme (as the site did before the light look became the default), unless asked."""
    try:
        from playwright.sync_api import Browser
    except Exception:
        return
    if getattr(Browser, "_tura_follow", False):
        return
    orig = Browser.new_context

    def new_context(self, *a, follow_look=True, **k):
        c = orig(self, *a, **k)
        if follow_look:
            c.add_init_script("try{if(!localStorage.getItem('tura_look'))localStorage.setItem('tura_look','System')}catch(e){}")
        return c
    Browser.new_context = new_context
    Browser._tura_follow = True


_follow_look()

LOOK_INFO = """() => { const m = (getComputedStyle(document.body).backgroundColor || '').match(/[\\d.]+/g) || [0, 0, 0];
  const keys = Object.keys(localStorage).filter(k => k.startsWith('stActiveTheme') || k.startsWith('tura_'));
  return {look: (0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]) / 255 > .5 ? 'light' : 'dark', url: location.href.slice(-60),
          rtl: !!document.querySelector('.block-container[dir], [data-testid="stMainBlockContainer"]') && getComputedStyle(document.querySelector('[data-testid="stMainBlockContainer"]') || document.body).direction,
          h1: ((document.querySelector('h1') || {}).innerText || '').slice(0, 40), store: Object.fromEntries(keys.map(k => [k.slice(0, 40), localStorage.getItem(k)]))}; }"""


def look_lang(b, report):
    out = {}
    phone = dict(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, device_scale_factor=2)
    # 1) a first visit from an Arabic phone in dark mode, straight to a page: light and Arabic
    for tag, loc, scheme, path in (("ar_dark_news", "ar-SA", "dark", "news?m=sa"), ("en_dark_news", "en-US", "dark", "news?m=us"),
                                   ("ar_light_home", "ar-SA", "light", "")):
        res = {}
        try:
            ctx = b.new_context(locale=loc, color_scheme=scheme, follow_look=False, **phone)
            pg = ctx.new_page()
            pg.goto(f"{URL}/{path}", wait_until="domcontentloaded", timeout=90000)
            settle(pg, 150)
            time.sleep(3)
            res["first"] = pg.evaluate(LOOK_INFO)
            pg.screenshot(path=os.path.join(OUT, f"ll_{tag}_1.jpg"), type="jpeg", quality=70)
            if not path:                             # the landing: a market picked, then the page after it
                pg.evaluate("() => { const b = document.querySelector('[class*=\"st-key-introgo_sa\"] button'); if (b) b.click(); }")
                time.sleep(3)
                settle(pg, 150)
            time.sleep(4)
            settle(pg, 120)
            time.sleep(2)
            res["after"] = pg.evaluate(LOOK_INFO)
            pg.screenshot(path=os.path.join(OUT, f"ll_{tag}_2.jpg"), type="jpeg", quality=70)
            if tag == "ar_dark_news":
                # the visitor picks English; a new visit without ?lang= opens in English
                pg.locator('.langbtn').first.tap()
                time.sleep(0.8)
                pg.locator('.navportal [class*="st-key-langopt_en"] button').first.tap(timeout=5000)
                time.sleep(3)
                settle(pg, 60)
                time.sleep(2)
                res["picked_en"] = pg.evaluate(LOOK_INFO)
                pg.goto(f"{URL}/stock?m=sa", wait_until="domcontentloaded", timeout=90000)
                settle(pg, 150)
                time.sleep(4)
                settle(pg, 60)
                res["revisit"] = pg.evaluate(LOOK_INFO)
                pg.screenshot(path=os.path.join(OUT, f"ll_{tag}_3.jpg"), type="jpeg", quality=70)
            ctx.close()
        except Exception as e:
            res["error"] = str(e)[:400]
        out[tag] = res
        log("looklang", tag, json.dumps(res, ensure_ascii=False)[:900])
    report["look_lang"] = out


LIVE_LOOK = False     # the live site, as a first-time visitor on an Arabic and on an English phone in dark mode sees it


def live_look():
    from playwright.sync_api import sync_playwright
    report = {"live_look": {}}
    phone = dict(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, device_scale_factor=2)
    with sync_playwright() as p:
        b = p.chromium.launch()
        for loc, tag in (("ar-SA", "ar"), ("en-US", "en")):
            res = {}
            try:
                ctx = b.new_context(locale=loc, color_scheme="dark", follow_look=False, **phone)
                pg = ctx.new_page()
                pg.goto(f"{LIVE_URL}/news?m=sa", wait_until="domcontentloaded", timeout=120000)
                for k in range(24):                  # the app inside Streamlit Cloud's page: until it has drawn its title
                    time.sleep(5)
                    fr = [f for f in pg.frames if "/~/+/" in f.url] or [pg.main_frame]
                    try:
                        info = fr[0].evaluate(LOOK_INFO)
                    except Exception:
                        continue
                    if info.get("h1"):
                        break
                time.sleep(10)
                fr = [f for f in pg.frames if "/~/+/" in f.url] or [pg.main_frame]
                res = fr[0].evaluate(LOOK_INFO)
                res["store"] = {k: v for k, v in res.get("store", {}).items() if k.startswith("tura")}
                pg.screenshot(path=os.path.join(OUT, f"live_look_{tag}.jpg"), type="jpeg", quality=72)
                ctx.close()
            except Exception as e:
                res["error"] = str(e)[:300]
            report["live_look"][tag] = res
            log("live_look", tag, json.dumps(res, ensure_ascii=False)[:600])
        b.close()
    json.dump(report, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0


NEWS_FILTER = False   # a quick run: the News page with its closed Filter panel, opened, and its Category list (categories and keywords)


def news_filter(b, report):
    out = {}
    for tag, lang, vp in (("en_desk", "en", {"width": 1440, "height": 900}), ("ar_desk", "ar", {"width": 1440, "height": 900}),
                          ("ar_phone", "ar", {"width": 390, "height": 844})):
        res = {}
        kw = dict(viewport=vp, locale="ar-SA" if lang == "ar" else "en-US", color_scheme="light")
        if vp["width"] < 500:
            kw.update(has_touch=True, is_mobile=True, device_scale_factor=2)
        try:
            ctx = b.new_context(**kw)
            pg = ctx.new_page()
            pg.goto(f"{URL}/news?m=sa&lang={lang}", wait_until="domcontentloaded", timeout=90000)
            settle(pg, 150)
            time.sleep(3)
            res["problems"] = problems(pg)
            res["expanders"] = pg.evaluate("() => [...document.querySelectorAll('[data-testid=\"stExpander\"] summary')].map(s => s.innerText.trim().slice(0, 40))")
            pg.screenshot(path=os.path.join(OUT, f"nf_{tag}_1_closed.jpg"), type="jpeg", quality=72)
            fl = pg.locator('[data-testid="stExpander"] summary', has_text="فلتر" if lang == "ar" else "Filter").first
            fl.click()
            time.sleep(1.5)
            pg.screenshot(path=os.path.join(OUT, f"nf_{tag}_2_open.jpg"), type="jpeg", quality=72)
            ms = pg.locator('[data-testid="stMultiSelect"]', has_text="التصنيف" if lang == "ar" else "Category").first
            ms.locator('input').first.click()
            time.sleep(1.2)
            res["options"] = pg.evaluate("() => [...document.querySelectorAll('[role=\"option\"]')].map(o => o.innerText.trim()).slice(0, 30)")
            pg.screenshot(path=os.path.join(OUT, f"nf_{tag}_3_list.jpg"), type="jpeg", quality=72)
            opt = pg.locator('[role="option"]', has_text="·").first
            res["picked"] = opt.inner_text().strip()
            opt.click()
            time.sleep(2)
            settle(pg, 90)
            pg.keyboard.press("Escape")
            time.sleep(1)
            res["after_pick"] = {"problems": problems(pg), "open": pg.evaluate("() => [...document.querySelectorAll('[data-testid=\"stExpander\"] details')].map(d => d.open)"),
                                 "cards": pg.evaluate("() => document.querySelectorAll('.news').length")}
            pg.screenshot(path=os.path.join(OUT, f"nf_{tag}_4_picked.jpg"), type="jpeg", quality=72)
            ctx.close()
        except Exception as e:
            res["error"] = str(e)[:400]
        out[tag] = res
        log("newsfilter", tag, json.dumps(res, ensure_ascii=False)[:900])
    report["news_filter"] = out


FONT_PICK = False     # a quick run: the Arabic pages in each Arabic typeface on trial (the font swapped on the test page only)
FONTS = [("readex", "Readex Pro", ""),
         ("plex", "IBM Plex Sans Arabic", "IBM+Plex+Sans+Arabic:wght@300;400;500;600;700"),
         ("almarai", "Almarai", "Almarai:wght@300;400;700;800"),
         ("tajawal", "Tajawal", "Tajawal:wght@300;400;500;700;800")]
SET_FONT = """([fam, q]) => new Promise(res => {
  let st = document.getElementById('fontpick'); if (!st) { st = document.createElement('style'); st.id = 'fontpick'; document.head.appendChild(st); }
  if (q && !document.getElementById('fl_' + q.slice(0, 8))) { const l = document.createElement('link'); l.id = 'fl_' + q.slice(0, 8); l.rel = 'stylesheet';
    l.href = 'https://fonts.googleapis.com/css2?family=' + q + '&display=swap'; document.head.appendChild(l); }
  st.textContent = fam === 'Readex Pro' ? '' : `body *:not(.ms):not(.material-symbols-rounded):not([data-testid="stIconMaterial"]):not([class*="material-symbols"]):not(.lic):not(.chev) {
    font-family: '${fam}', 'DM Sans', system-ui, sans-serif !important; }`;
  const t0 = Date.now();
  const wait = () => { document.fonts.load(`500 16px "${fam}"`, 'عربي').then(() => document.fonts.ready).then(() => {
    if (document.fonts.check(`16px "${fam}"`, 'عربي') || Date.now() - t0 > 8000) setTimeout(() => res(document.fonts.check(`16px "${fam}"`, 'عربي')), 600);
    else setTimeout(wait, 300); }).catch(() => setTimeout(wait, 300)); };
  wait(); })"""


def font_pick(b, report):
    out = {}
    pages = [("overview", "?m=sa&lang=ar", (300, 60, 1440, 620)), ("news", "news?m=sa&lang=ar", (300, 360, 1440, 900)),
             ("stock", "stock?symbol=2222.SR&m=sa&lang=ar", (300, 60, 1440, 620))]
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, locale="ar-SA", color_scheme="light", device_scale_factor=1.5)
    pg = ctx.new_page()
    for name, path, box in pages:
        res = {}
        try:
            pg.goto(f"{URL}/{path}", wait_until="domcontentloaded", timeout=90000)
            settle(pg, 150)
            time.sleep(3)
            if name == "news":
                pg.evaluate("() => { const e = document.querySelector('.news'); if (e) { e.scrollIntoView({block: 'start'}); const m = document.querySelector('[data-testid=\"stMain\"]'); if (m) m.scrollBy(0, -260); window.scrollBy(0, -260); } }")
                time.sleep(1)
            for key, fam, q in FONTS:
                res[key] = pg.evaluate(SET_FONT, [fam, q])
                pg.mouse.move(5, 895)
                time.sleep(0.8)
                pg.screenshot(path=os.path.join(OUT, f"font_{name}_{key}.jpg"), type="jpeg", quality=86,
                              clip={"x": box[0], "y": box[1], "width": box[2] - box[0], "height": box[3] - box[1]})
            pg.evaluate(SET_FONT, ["Readex Pro", ""])
        except Exception as e:
            res["error"] = str(e)[:300]
        out[name] = res
        log("font", name, json.dumps(res))
    ctx.close()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, device_scale_factor=2, locale="ar-SA", color_scheme="light")
    pg = ctx.new_page()
    try:
        pg.goto(f"{URL}/news?m=sa&lang=ar", wait_until="domcontentloaded", timeout=90000)
        settle(pg, 150)
        time.sleep(3)
        pg.evaluate("() => { const e = document.querySelector('.news'); if (e) { e.scrollIntoView({block: 'start'}); const m = document.querySelector('[data-testid=\"stMain\"]'); if (m) m.scrollBy(0, -120); window.scrollBy(0, -120); } }")
        time.sleep(1)
        for key, fam, q in FONTS:
            pg.evaluate(SET_FONT, [fam, q])
            time.sleep(0.8)
            pg.screenshot(path=os.path.join(OUT, f"font_phone_{key}.jpg"), type="jpeg", quality=80)
    except Exception as e:
        out["phone_error"] = str(e)[:300]
    ctx.close()
    report["font_pick"] = out


LIVE_AI = False      # a quick run: the AI chat window on the live sites (Streamlit Cloud and the Oracle server), as a visitor opens it


def live_ai():
    from playwright.sync_api import sync_playwright
    report = {"live_ai": {}, "started": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name, base in (("cloud", LIVE_URL), ("oracle", "http://84.13.143.157")):
            row = {}
            ctx = b.new_context(viewport={"width": 1440, "height": 900}, locale="en-US", color_scheme="light", device_scale_factor=2)
            pg = ctx.new_page()
            t0 = time.time()
            try:
                pg.goto(base + "/stock?symbol=AAPL&lang=en", wait_until="domcontentloaded", timeout=150000)
                pg.wait_for_selector('.st-key-alturaifi_ai_fab [data-testid="stPopoverButton"]', timeout=180000)
                row["fab_s"] = round(time.time() - t0, 1)
                time.sleep(4)
                pg.locator('.st-key-alturaifi_ai_fab [data-testid="stPopoverButton"]').first.click(timeout=10000, force=True)
                time.sleep(3)
                row["new_window"] = pg.evaluate("() => !!document.querySelector('.ai-hello, div.st-key-alturaifi_ai_composer')")
                row["old_window"] = pg.evaluate("() => !!document.querySelector('.ai-empty')")
                row["build"] = pg.evaluate("() => { const t = document.body.innerText.match(/23\\.\\d+(\\.\\d+)?/); return t ? t[0] : null; }")
                pg.screenshot(path=os.path.join(OUT, f"live_ai_{name}.jpg"), type="jpeg", quality=80)
            except Exception as e:
                row["error"] = str(e)[:300]
                try:
                    pg.screenshot(path=os.path.join(OUT, f"live_ai_{name}_error.jpg"), type="jpeg", quality=70)
                except Exception:
                    pass
            report["live_ai"][name] = row
            ctx.close()
        b.close()
    json.dump(report, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0


def main():
    if LIVE_AI:
        return live_ai()
    if LIVE_LOOK:
        return live_look()
    if LIVE:
        return live_probe()
    if QUICK and XB_SEED == "sample":
        seed_xbots()
    elif QUICK and XB_SEED == "resting":
        seed_resting()
    if not QUICK and not SHARIA and not MENU_CHECK and not BOXV2 and not STYLE_PICK and not ORB_CHECK and not LOOK_LANG and not NEWS_FILTER and not FONT_PICK:
        news_lab()
    seed_bots()
    if QUICK and AUTH_DEMO:                     # made-up sign-in settings on the test server only: the Sign in button shows
        os.makedirs(os.path.join(ROOT, ".streamlit"), exist_ok=True)
        with open(os.path.join(ROOT, ".streamlit", "secrets.toml"), "w", encoding="utf-8") as f:
            f.write('[auth]\nredirect_uri = "http://localhost:8599/oauth2callback"\ncookie_secret = "site-check-only"\n'
                    '[auth.auth0]\nclient_id = "demo"\nclient_secret = "demo"\n'
                    'server_metadata_url = "https://example.invalid/.well-known/openid-configuration"\n')
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    srv = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "true", "--server.port", str(PORT),
                            "--browser.gatherUsageStats", "false"], cwd=ROOT, env=env, stdout=open(os.path.join(OUT, "server.log"), "w"),
                           stderr=subprocess.STDOUT)
    report = {"pages": {}, "started": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())}
    try:
        import streamlit
        report["streamlit"] = streamlit.__version__
    except Exception:
        pass
    try:
        import requests
        for _ in range(60):
            try:
                if requests.get(URL + "/_stcore/health", timeout=2).ok:
                    break
            except Exception:
                pass
            time.sleep(1)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            if SHARIA:
                try:
                    sharia_check(b, report)
                finally:
                    json.dump(report, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                b.close()
                return 0
            if MENU_CHECK:
                try:
                    menu_check(p, report)
                finally:
                    json.dump(report, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                b.close()
                return 0
            if FONT_PICK:
                try:
                    font_pick(b, report)
                finally:
                    json.dump(report, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                b.close()
                return 0
            if NEWS_FILTER:
                try:
                    news_filter(b, report)
                finally:
                    json.dump(report, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                b.close()
                return 0
            if LOOK_LANG:
                try:
                    look_lang(b, report)
                finally:
                    json.dump(report, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                b.close()
                return 0
            if ORB_CHECK:
                try:
                    orb_check(b, report)
                finally:
                    json.dump(report, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                b.close()
                return 0
            if STYLE_PICK:
                try:
                    style_pick(b, report)
                finally:
                    json.dump(report, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                b.close()
                return 0
            if BOXV2:
                try:
                    box_check(b, report)
                finally:
                    json.dump(report, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                b.close()
                return 0
            if TOUR:
                try:
                    (tour_phone if TOUR_PHONE else tour)(b, report)
                finally:
                    json.dump(report, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                b.close()
                return 0
            if not QUICK:
                chart_lab(b, report)
            for lang in ("ar", "en"):
                ctx = b.new_context(viewport={"width": 1440, "height": 900}, locale="ar-SA" if lang == "ar" else "en-US", color_scheme="dark")
                pg = ctx.new_page()
                # the landing: a new visitor picks a market (the two buttons at the end of the landing)
                pg.goto(f"{URL}/?lang={lang}", wait_until="domcontentloaded")
                took = settle(pg)
                report["pages"][f"{lang}_landing"] = {"seconds": took, "problems": problems(pg)}
                try:
                    pg.evaluate("() => document.querySelector('[class*=\"st-key-introgo_sa\"]').scrollIntoView({block: 'center'})")
                    time.sleep(2.5)
                    pg.screenshot(path=os.path.join(OUT, f"{lang}_landing_pick.jpg"), type="jpeg", quality=80)
                    pg.evaluate("() => { const t = [...document.querySelectorAll('[class*=\"ixmk\"]')][0]; if (t) { t.scrollIntoView({block: 'center'}); window.scrollBy(0, -60); } }")
                    time.sleep(2.5)
                    pg.screenshot(path=os.path.join(OUT, f"{lang}_landing_two.jpg"), type="jpeg", quality=80)
                except Exception as e:
                    report.setdefault("notes", []).append(f"landing {lang}: {e}"[:300])
                try:
                    pg.evaluate("() => document.querySelector('[class*=\"st-key-introgo_sa\"] button').click()")
                    time.sleep(2)
                    took = settle(pg, 180)
                    pg.evaluate("() => window.scrollTo(0, 0)")
                    shoot(pg, f"{lang}_overview")
                    report["pages"][f"{lang}_overview"] = {"seconds": took, "problems": problems(pg), "url": pg.url}
                except Exception as e:
                    report["pages"][f"{lang}_overview"] = {"error": str(e)[:400]}
                # the switch in the top line: back to the US market
                try:
                    pg.evaluate("() => document.querySelector('.st-key-mktb_us button').click()")
                    time.sleep(2)
                    took = settle(pg, 180)
                    shoot(pg, f"{lang}_us_overview")
                    report["pages"][f"{lang}_us_overview"] = {"seconds": took, "problems": problems(pg), "url": pg.url}
                except Exception as e:
                    report["pages"][f"{lang}_us_overview"] = {"error": str(e)[:400]}
                try:                                 # the top bar's menus: on a page, then after choosing a page from a menu
                    pg.set_viewport_size({"width": 1440, "height": 900})
                    pg.goto(f"{URL}/news?m=us&lang={lang}", wait_until="domcontentloaded")
                    settle(pg)
                    nav_probe(pg, f"{lang}_first", report)
                    pg.locator('.st-key-navsec_0 .navbtn').first.hover()
                    time.sleep(0.6)
                    pg.locator('.st-key-navdd_0 [data-testid="stPageLink"] a').nth(1).click(timeout=8000)
                    time.sleep(2)
                    settle(pg)
                    nav_probe(pg, f"{lang}_after_click", report)
                    # the visitor's path: the Saudi market, Portfolio chosen from its menu, then the Insight menu hovered
                    pg.goto(f"{URL}/news?m=sa&lang={lang}", wait_until="domcontentloaded")
                    settle(pg)
                    pg.locator('.st-key-navsec_6 .navbtn').first.hover()
                    time.sleep(0.6)
                    pg.locator('.st-key-navdd_6 [data-testid="stPageLink"] a').first.click(timeout=8000)
                    time.sleep(2)
                    settle(pg)
                    nav_probe(pg, f"{lang}_sa_portfolio", report)
                    # a stopped page script (its frame re-created): the flag left behind must not keep the menus shut
                    pg.evaluate("""() => { document.documentElement.setAttribute('data-menu-closed', '1');
                        document.querySelectorAll('iframe').forEach(f => { try { if ((f.srcdoc || '').includes('__alturaifiCards')) f.remove(); } catch (e) {} }); }""")
                    time.sleep(3)
                    nav_probe(pg, f"{lang}_stopped_script", report)
                except Exception as e:
                    report.setdefault("notes", []).append(f"nav {lang}: {e}"[:300])
                for name, path, mk, *click in (QUICK_PAGES if QUICK else PAGES):
                    sep = "&" if "?" in path else "?"
                    t0 = time.time()
                    try:
                        pg.goto(f"{URL}/{path}{sep}m={mk}&lang={lang}", wait_until="domcontentloaded", timeout=60000)
                        took = settle(pg, 180)
                        if name == "pf_trade" and lang == "ar":
                            try:                     # an order from the ticket (the market may be closed: it then waits)
                                pg.locator('[class*="st-key-pf_send"] button').first.click(timeout=10000)
                                settle(pg)
                            except Exception as e:
                                report.setdefault("notes", []).append(f"{lang} send: {e}"[:300])
                        shoot(pg, f"{lang}_{name}")
                        report["pages"][f"{lang}_{name}"] = {"seconds": took, "problems": problems(pg)}
                        if path == "paper-bots":    # "Build your bot": the visitor's own list with the form open
                            try:
                                pg.set_viewport_size({"width": 1440, "height": 900})
                                pg.locator('[class*="st-key-pb_site_build"] button').first.click(timeout=15000)
                                time.sleep(2)
                                settle(pg, 120)
                                time.sleep(2)
                                pg.screenshot(path=os.path.join(OUT, f"{lang}_{name}_build.jpg"), type="jpeg", quality=80)
                                pg.keyboard.press("Escape")
                                time.sleep(1.5)
                                settle(pg, 60)
                                shoot(pg, f"{lang}_{name}_mine")
                                report["pages"][f"{lang}_{name}_build"] = {"problems": problems(pg)}
                            except Exception as e:
                                report.setdefault("notes", []).append(f"{lang} {name} build: {e}"[:300])
                        if path.startswith("stock?"):  # the stock's financials: quarterly net margin and the cash flow charts
                            try:
                                pg.locator('[data-testid="stTabs"] [role="tab"]').nth(3).click(timeout=15000)
                                time.sleep(2)
                                settle(pg, 150)
                                pg.locator('[class*="st-key-fin_freq"] button').nth(1).click(timeout=15000)
                                time.sleep(2)
                                settle(pg, 120)
                                pg.locator('[class*="st-key-fin_metric"] [data-testid="stSelectbox"]').first.click(timeout=15000)
                                time.sleep(0.8)
                                shoot(pg, f"{lang}_{name}_finpick")
                                pg.get_by_role("option", name=FIN_PILL[lang]).first.click(timeout=15000)
                                time.sleep(2)
                                settle(pg, 120)
                                time.sleep(2)
                                shoot(pg, f"{lang}_{name}_fin")
                                report["pages"][f"{lang}_{name}_fin"] = {"problems": problems(pg)}
                            except Exception as e:
                                report.setdefault("notes", []).append(f"{lang} {name} fin: {e}"[:300])
                        if path == "x-bots":         # the bot's evaluation tab ("Is it truthful?")
                            try:
                                pg.locator('[data-testid="stTabs"] [role="tab"]').nth(2).click(timeout=15000)
                                time.sleep(2)
                                settle(pg, 120)
                                time.sleep(2)
                                shoot(pg, f"{lang}_{name}_score")
                                report["pages"][f"{lang}_{name}_score"] = {"problems": problems(pg)}
                            except Exception as e:
                                report.setdefault("notes", []).append(f"{lang} {name} score: {e}"[:300])
                        if click:                    # open the first story's analysis window and photograph it
                            try:
                                pg.set_viewport_size({"width": 1440, "height": 2400})
                                pg.locator(click[0]).first.click(timeout=15000)
                                time.sleep(2)
                                settle(pg, 150)
                                time.sleep(2)
                                pg.locator('[role="dialog"]').first.screenshot(path=os.path.join(OUT, f"{lang}_{name}_open.jpg"),
                                                                             type="jpeg", quality=78)
                                report["pages"][f"{lang}_{name}_open"] = {"problems": problems(pg)}
                            except Exception as e:
                                report.setdefault("notes", []).append(f"{lang} {name} open: {e}"[:300])
                    except Exception as e:
                        report["pages"][f"{lang}_{name}"] = {"error": str(e)[:400], "seconds": time.time() - t0}
                    log(lang, name, json.dumps(report["pages"].get(f"{lang}_{name}"), ensure_ascii=False)[:300])
                # the top line close up (the market switch and the language menu)
                try:
                    pg.goto(f"{URL}/news?m=sa&lang={lang}", wait_until="domcontentloaded")
                    settle(pg)
                    pg.set_viewport_size({"width": 1440, "height": 900})
                    pg.screenshot(path=os.path.join(OUT, f"{lang}_topbar.jpg"), type="jpeg", quality=80, clip={"x": 0, "y": 0, "width": 1440, "height": 220})
                except Exception as e:
                    report.setdefault("notes", []).append(f"topbar {lang}: {e}"[:300])
                ctx.close()
            b.close()
            if QUICK and NAV_BROWSERS:                # the menus in other browsers and on narrower windows (a zoomed laptop)
                for kind, w_ in (("chromium", 1280), ("chromium", 1000), ("webkit", 1440), ("webkit", 1100), ("firefox", 1440)):
                    try:
                        bx = getattr(p, kind).launch()
                        cx = bx.new_context(viewport={"width": w_, "height": 900}, color_scheme="dark")
                        px_ = cx.new_page()
                        for path in ("news?m=us&lang=en", "?m=us&lang=en"):
                            px_.goto(f"{URL}/{path}", wait_until="domcontentloaded")
                            settle(px_, 180)
                            nav_probe(px_, f"{kind}_{w_}_{'news' if 'news' in path else 'home'}", report)
                        bx.close()
                    except Exception as e:
                        report.setdefault("notes", []).append(f"{kind} {w_}: {e}"[:300])
    finally:
        srv.terminate()
        try:
            srv.wait(10)
        except Exception:
            srv.kill()
    json.dump(report, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    bad = {k: v for k, v in report["pages"].items() if v.get("error") or v.get("problems")}
    log("pages with problems:", json.dumps(bad, ensure_ascii=False, indent=1)[:6000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
