"""
Builds infos.json: Yahoo Finance's summary of every company in the site's lists (market cap, ratios, margins, growth, balance
sheet, analysts' targets, the description), read from GitHub's servers. The site uses it when Yahoo does not answer its own
server (data.info); price-based figures are moved to the day's price there. Run on weekdays by .github/workflows/infos.yml.
"""
import json
import os
import sys
import time
from datetime import date, datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FILE = os.path.join(ROOT, "infos.json")
DROP = {"executiveTeam", "corporateActions", "messageBoardId", "uuid", "gmtOffSetMilliseconds", "maxAge", "priceHint", "tradeable",
        "cryptoTradeable", "triggerable", "customPriceAlertConfidence", "esgPopulated", "hasPrePostMarketData", "sourceInterval",
        "exchangeDataDelayedBy", "quoteSourceName", "marketState", "language", "region", "typeDisp", "irWebsite", "fax", "phone",
        "address1", "address2", "zip", "compensationAsOfEpochDate", "governanceEpochDate", "nameChangeDate", "firstTradeDateMilliseconds"}


def symbols():
    import universe as U
    from sp500 import SP500
    import taxonomy as X
    out = list(U.US_UNIVERSE) + list(SP500) + list(X.EXTRA)
    return [s for s in dict.fromkeys(out) if s and "^" not in s and "=" not in s and not s.endswith("-USD")]


def slim(info):
    """The summary without Yahoo's bookkeeping: numbers, short texts, the description and the first six officers."""
    out = {}
    for k, v in info.items():
        if k in DROP or v is None:
            continue
        if k == "companyOfficers":
            out[k] = [{x: o.get(x) for x in ("name", "title", "age") if o.get(x) is not None} for o in (v or [])[:6]]
        elif k == "longBusinessSummary" or isinstance(v, bool) or isinstance(v, (int, float)):
            out[k] = v
        elif isinstance(v, str) and len(v) <= 200:
            out[k] = v
    out["_asof"] = date.today().isoformat()
    return out


def main():
    import yfinance as yf
    try:
        with open(FILE, encoding="utf-8") as f:
            prev = json.load(f).get("items", {})
    except (OSError, ValueError):
        prev = {}
    syms = symbols()
    print(f"yfinance {yf.__version__} · {len(syms)} symbols, {len(prev)} already saved")
    items, stats, t0 = dict(prev), {"ok": 0, "kept": 0}, time.time()
    for i, s in enumerate(syms, 1):
        for attempt in range(3):
            try:
                info = yf.Ticker(s).info or {}
                if len(info) < 10:
                    raise ValueError(f"only {len(info)} fields")
                items[s] = slim(info)
                stats["ok"] += 1
                break
            except Exception as e:                  # a refusal or a hiccup: wait and try again, else keep the last copy
                if attempt == 2:
                    stats["kept"] += 1
                    print(f"  {s}: {type(e).__name__}: {str(e)[:120]}")
                else:
                    time.sleep(4 * (attempt + 1))
        time.sleep(0.2)
        if i % 50 == 0 or i == len(syms):
            with open(FILE, "w", encoding="utf-8") as f:
                json.dump({"built": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "items": items}, f, ensure_ascii=False,
                          separators=(",", ":"), sort_keys=True)
            print(f"{i}/{len(syms)} · {time.time() - t0:.0f}s · {stats}")
    for s in ("META", "NKE", "AAPL", "TSM"):
        r = items.get(s) or {}
        print(f"{s}: {len(r)} fields · price {r.get('currentPrice')} · cap {r.get('marketCap')} · PE {r.get('trailingPE')} · "
              f"margin {r.get('profitMargins')} · {r.get('_asof')}")
    print("file size", os.path.getsize(FILE) // 1024, "KB")


if __name__ == "__main__":
    main()
