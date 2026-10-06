"""
Builds holders.json: who owns each company in the site's lists (institutions, insiders, everyone else, the largest holders)
from Yahoo Finance, with a weekly snapshot kept for about a year so the page can show the change over a month (holders.py).
Run weekly by .github/workflows/holders.yml.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import holders as HD  # noqa: E402


def symbols():
    import universe as U
    from sp500 import SP500
    import taxonomy as X
    out = list(U.US_UNIVERSE) + list(SP500) + list(X.EXTRA)
    return [s for s in dict.fromkeys(out) if s and "^" not in s and "=" not in s and not s.endswith("-USD")]


def save(items):
    with open(HD.FILE, "w", encoding="utf-8") as f:
        json.dump({"built": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "items": items}, f, ensure_ascii=False,
                  separators=(",", ":"))


def main():
    import yfinance as yf
    try:
        with open(HD.FILE, encoding="utf-8") as f:
            prev = json.load(f).get("items", {})
    except (OSError, ValueError):
        prev = {}
    syms = symbols()
    print(f"{len(syms)} symbols, {len(prev)} already known")
    items = dict(prev)
    stats = {"ok": 0, "none": 0, "error": 0}
    t0 = time.time()
    for i, s in enumerate(syms, 1):
        for attempt in range(3):
            try:
                cur = HD.snapshot(yf.Ticker(s))
                cur["hist"] = HD.add_history(prev.get(s), cur)
                items[s] = cur
                stats["ok"] += 1
                break
            except HD.Missing:
                stats["none"] += 1
                break
            except Exception as e:                  # rate limit or a network hiccup: wait and try again, else keep what was there
                if attempt == 2:
                    stats["error"] += 1
                    print(f"  {s}: {type(e).__name__}: {str(e)[:140]}")
                else:
                    time.sleep(4 * (attempt + 1))
        time.sleep(0.25)
        if i % 50 == 0 or i == len(syms):
            save(items)
            print(f"{i}/{len(syms)} · {time.time() - t0:.0f}s · {stats}")
    for s in ("AAPL", "MSFT", "NVDA", "AMZN", "TSLA", "META", "CRWV", "PLTR", "JPM", "KO"):
        r = items.get(s) or {}
        top = ", ".join(f"{h[0]} {h[1]:.2f}%" for h in (r.get("top") or [])[:3] if h[1] is not None)
        print(f"{s}: inst {r.get('inst')} ins {r.get('ins')} instf {r.get('instf')} n {r.get('n')} rep {r.get('rep')} "
              f"6m {r.get('ins6m')} hist {len(r.get('hist') or [])} · 1M inst {HD.change(r, 'inst')} · top: {top}")


if __name__ == "__main__":
    main()
