"""
Builds segments.json: where each company's revenue comes from (product lines, business segments or regions), read from its
latest annual report at the SEC (segments.py does the reading). Run monthly by .github/workflows/segments.yml; a company whose
latest annual report is the one already read is not downloaded again.
"""
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import segments as SG  # noqa: E402


def symbols():
    import universe as U
    from sp500 import SP500
    import taxonomy as X
    out = list(U.US_UNIVERSE) + list(SP500) + list(X.EXTRA)
    return [s for s in dict.fromkeys(out) if s and "^" not in s and "=" not in s and not s.endswith("-USD")]


def main():
    try:
        with open(SG.FILE, encoding="utf-8") as f:
            prev = json.load(f).get("items", {})
    except (OSError, ValueError):
        prev = {}
    # the SEC asks automated tools to say who they are; try the declared agents in turn (SEC_USER_AGENT first, when set)
    agents = list(SG.AGENTS) + ["Mozilla/5.0 (compatible; TURAPro/1.0; +https://abdulrahman.streamlit.app)"]
    ciks = None
    for a in agents:
        SG.UA = a
        try:
            ciks = SG.cik_map()
            print("SEC answered with the agent:", a)
            break
        except Exception as e:
            print("SEC refused the agent:", a, "-", e)
    if ciks is None:
        raise SystemExit("the SEC refused every agent")
    syms = symbols()
    print(f"{len(syms)} symbols, {len(ciks)} SEC filers known, {len(prev)} already read")
    items = dict(prev)
    stats = {"ok": 0, "same": 0, "none": 0, "error": 0}
    t0 = time.time()
    for i, s in enumerate(syms, 1):
        old = prev.get(s)
        try:
            r = SG.fetch(s, ciks, old)
            if old is not None and r is old:
                stats["same"] += 1
            elif r.get("rows"):
                stats["ok"] += 1
            else:
                stats["none"] += 1
            items[s] = r
        except Exception as e:                      # a network hiccup: keep what was there
            stats["error"] += 1
            print(f"  {s}: {type(e).__name__}: {str(e)[:160]}")
            if os.environ.get("SEG_DEBUG"):
                traceback.print_exc()
        if i % 25 == 0 or i == len(syms):
            with open(SG.FILE, "w", encoding="utf-8") as f:
                json.dump({"built": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "items": items}, f, ensure_ascii=False,
                          separators=(",", ":"))
            print(f"{i}/{len(syms)} · {time.time() - t0:.0f}s · {stats}")
    for s in ("AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "JPM", "TSM", "XOM", "LLY", "KO", "IONQ", "AVGO", "V", "COST", "NFLX", "PLTR"):
        r = items.get(s) or {}
        if r.get("rows"):
            tot = r["total"]
            parts = ", ".join(f"{n} {v / tot * 100:.1f}%" for n, v in r["rows"])
            print(f"{s}: {r['form']} {r['end']} {r['kind']} {r['cur']} {tot / 1e9:.1f}B -> {parts}")
            if r.get("alt"):
                a = r["alt"]
                print(f"    and {a['kind']}: " + ", ".join(f"{n} {v / a['total'] * 100:.1f}%" for n, v in a["rows"]))
        else:
            print(f"{s}: none ({r.get('why')})")
    whys = {}
    for r in items.values():
        if not r.get("rows"):
            whys[r.get("why")] = whys.get(r.get("why"), 0) + 1
    print("without a breakdown:", whys)
    for why in whys:
        print(f"  {why}: {' '.join(sorted(k for k, r in items.items() if not r.get('rows') and r.get('why') == why))}")


if __name__ == "__main__":
    main()
