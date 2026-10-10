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
PAGES = [  # 22.3: the spacing, the section titles, the tabs and the charts; a story's analysis opened from the News page
         ("stock", "stock?symbol=NVDA", "us"), ("news", "news", "us", '[class*="st-key-nwa_"] button'),
         ("newsintel", "news-intelligence", "us", '[class*="st-key-nie_cb_"] button'),
         ("sentiment", "sentiment", "us"), ("seasonality", "seasonality", "us"), ("pf_dash", "portfolio", "us"),
         ("sa_stock", "stock?symbol=2222.SR", "sa"), ("sa_news", "news", "sa", '[class*="st-key-nwa_"] button')]


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


def main():
    seed_bots()
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    srv = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "true", "--server.port", str(PORT),
                            "--browser.gatherUsageStats", "false"], cwd=ROOT, env=env, stdout=open(os.path.join(OUT, "server.log"), "w"),
                           stderr=subprocess.STDOUT)
    report = {"pages": {}, "started": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())}
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
                for name, path, mk, *click in PAGES:
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
