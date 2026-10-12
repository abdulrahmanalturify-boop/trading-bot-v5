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


def main():
    if QUICK and XB_SEED == "sample":
        seed_xbots()
    elif QUICK and XB_SEED == "resting":
        seed_resting()
    if not QUICK and not SHARIA:
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
                                pg.locator('[class*="st-key-fin_metric"] button').filter(has_text=FIN_PILL[lang]).first.click(timeout=15000)
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
