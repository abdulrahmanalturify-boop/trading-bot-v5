"""
research/compact.py - Turns the lab reports (research/results/*.json) into the small file the site reads: lab_results.json
at the top of the repository. Run it after research/run.py.

rows[strategy][view][variant] = [sharpe, cagr, maxdd] for 2012-2019, then the same for 2020-now; the "company" view adds
[median sharpe, share of companies where the bot beat holding the stock] for each period.
Views: company (the 100 company bots as one basket), sector (5 trades), all10 and all20 (the all-companies bot).
"""
import json
import math
import os
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
DEST = os.path.join(os.path.dirname(HERE), "lab_results.json")


def _r(x, n=3):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) or math.isinf(x) else round(x, n)


def _trio(d):
    return [_r(d.get("sharpe")), _r(d.get("cagr")), _r(d.get("maxdd"))] if d else None


def main():
    runs = {}
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".json") and f != "summary.json":
            j = json.load(open(os.path.join(OUT, f)))
            runs[j["variant"]] = j
    if "baseline" not in runs:
        raise SystemExit("no baseline report yet")
    periods = list(runs["baseline"]["periods"])
    rows, bh = {}, {}
    for v, j in runs.items():
        for pi, per in enumerate(periods):
            p = j["periods"].get(per) or {}
            if v == "baseline":
                b = p.get("buy_hold") or {}
                any_all = next((s.get("all_bot", {}).get("20") for s in p.get("strategies", {}).values() if s.get("all_bot")), None) or {}
                bh.setdefault("company", []).extend(_trio(b) or [None] * 3)
                bh.setdefault("all", []).extend([_r(any_all.get("bh_sharpe")), _r(any_all.get("bh_cagr")), _r(any_all.get("bh_maxdd"))])
            for s, d in (p.get("strategies") or {}).items():
                views = {"company": _trio(d.get("all")), "sector": _trio(d.get("sector")),
                         "all10": _trio((d.get("all_bot") or {}).get("10")), "all20": _trio((d.get("all_bot") or {}).get("20"))}
                for view, t in views.items():
                    if not t:
                        continue
                    cell = rows.setdefault(s, {}).setdefault(view, {}).setdefault(v, [None] * (10 if view == "company" else 6))
                    cell[pi * 3:pi * 3 + 3] = t
                    if view == "company":
                        cell[6 + pi * 2:8 + pi * 2] = [_r(d.get("median_sharpe")), _r(d.get("beat_bh"))]
    out = {"updated": f"{date.today():%Y-%m-%d}", "periods": ["2012-2019", "2020-now"],
           "variants": {v: j.get("settings") or {} for v, j in runs.items()}, "buy_hold": bh, "rows": rows}
    json.dump(out, open(DEST, "w"), separators=(",", ":"))
    print(f"{DEST}: {len(rows)} strategies, {len(runs)} variants, {os.path.getsize(DEST) // 1024} KB")


if __name__ == "__main__":
    main()
