"""
scripts/site_check.py - Opens the site's pages in a headless browser, the way a visitor would, on a GitHub server (run by
.github/workflows/sitecheck.yml): the site runs locally (`streamlit run app.py`, no secrets: the trial store), a few paper bots
are added first, then every page of the list is opened in English and Arabic, in the US and the Saudi market. It saves a
screenshot of each page and a report of what went wrong (a page that raised an error, a section that couldn't load) to
OUT (default site_check/).
"""
import json
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
QUICK_PAGES = [("xbots", "x-bots", "us"), ("xbots_sa", "x-bots", "sa")]
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
        "saudi": ["أرامكو اختراق قوي مع ارتفاع أسعار النفط، فرصة دخول", "الراجحي يواصل الصعود بعد أرباح قوية، إيجابي", "سابك تراجع وكسر الدعم، سلبي",
                  "تاسي يرتفع بدعم من البنوك، السوق إيجابي"],
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
            for _ in range(rnd.randint(1, 3)):
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


QUICK = False          # a quick run: the top bar's menus and two pages, no news/photo/chart labs


def main():
    if QUICK:
        seed_xbots()
    if not QUICK:
        news_lab()
    seed_bots()
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
