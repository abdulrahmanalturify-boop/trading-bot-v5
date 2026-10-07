"""
Builds infos.json: Yahoo Finance's summary of every company in the site's lists (market cap, ratios, margins, growth, balance
sheet, analysts' targets, the description), read from GitHub's servers. The site uses it when Yahoo does not answer its own
server (data.info); price-based figures are moved to the day's price there. Run twice a week by .github/workflows/infos.yml.
"""
import json
import os
import sys
import time
from datetime import date, datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FILE = os.path.join(ROOT, "infos.json")               # the figures (rewritten twice a week)
TEXT_FILE = os.path.join(ROOT, "profiles.json")       # the texts: the same bytes when nothing changed, so git keeps no new copy
INS_FILE = os.path.join(ROOT, "insiders.json")        # insider transactions of the last 6 months (at most 40 per company)
INS_COLS = ("Start Date", "Insider", "Position", "Transaction", "Text", "Shares", "Value", "Ownership")
TEXT = ("longBusinessSummary", "companyOfficers", "website", "city", "state", "country", "longName", "shortName", "displayName",
        "industry", "sector", "industryDisp", "sectorDisp", "industryKey", "sectorKey")
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


def insider_rows(df):
    """[[date, insider, position, transaction, text, shares, value, ownership]] of the last 6 months, newest first, at most 40."""
    import pandas as pd
    if not isinstance(df, pd.DataFrame) or df.empty or "Start Date" not in df:
        return []
    d = df.copy()
    d["Start Date"] = pd.to_datetime(d["Start Date"], errors="coerce")
    d = d[d["Start Date"] >= pd.Timestamp.now() - pd.Timedelta(days=186)].sort_values("Start Date", ascending=False).head(40)
    out = []
    for _, r in d.iterrows():
        row = []
        for c in INS_COLS:
            v = r.get(c)
            if c == "Start Date":
                v = v.strftime("%Y-%m-%d") if not pd.isna(v) else None
            elif c in ("Shares", "Value"):
                v = None if v is None or pd.isna(v) else float(v)
            else:
                v = None if v is None or (not isinstance(v, str) and pd.isna(v)) else str(v)[:120]
            row.append(v)
        out.append(row)
    return out


def save(items, ins=None):
    nums = {s: {k: v for k, v in d.items() if k not in TEXT} for s, d in items.items()}
    text = {s: {k: v for k, v in d.items() if k in TEXT} for s, d in items.items()}
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump({"built": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "items": nums}, f, ensure_ascii=False,
                  separators=(",", ":"), sort_keys=True)
    with open(TEXT_FILE, "w", encoding="utf-8") as f:
        json.dump({"items": text}, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    if ins is not None:
        with open(INS_FILE, "w", encoding="utf-8") as f:
            json.dump({"asof": date.today().isoformat(), "cols": INS_COLS, "items": ins}, f, ensure_ascii=False, separators=(",", ":"),
                      sort_keys=True)


def main():
    import yfinance as yf
    prev = {}
    for path in (FILE, TEXT_FILE):
        try:
            with open(path, encoding="utf-8") as f:
                for k, v in json.load(f).get("items", {}).items():
                    prev.setdefault(k, {}).update(v)
        except (OSError, ValueError):
            pass
    syms = symbols()
    print(f"yfinance {yf.__version__} · {len(syms)} symbols, {len(prev)} already saved")
    items, stats, t0 = dict(prev), {"ok": 0, "kept": 0}, time.time()
    try:
        with open(INS_FILE, encoding="utf-8") as f:
            ins = json.load(f).get("items", {})
    except (OSError, ValueError):
        ins = {}
    for i, s in enumerate(syms, 1):
        for attempt in range(3):
            try:
                t = yf.Ticker(s)
                info = t.info or {}
                if len(info) < 10:
                    raise ValueError(f"only {len(info)} fields")
                row = slim(info)
                try:                                # the analysts per rating, as Yahoo names its columns (data._webull_scale reads it)
                    rec = t.recommendations_summary
                    r0 = rec[rec["period"].astype(str) == "0m"].iloc[0] if "period" in rec else rec.iloc[0]
                    row["_rec"] = {k: int(r0.get(k) or 0) for k in ("strongBuy", "buy", "hold", "sell", "strongSell")}
                except Exception:
                    pass
                try:
                    ins[s] = insider_rows(t.insider_transactions)
                except Exception:
                    pass
                items[s] = row
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
            save(items, ins)
            print(f"{i}/{len(syms)} · {time.time() - t0:.0f}s · {stats}")
    for s in ("META", "NKE", "AAPL", "TSM"):
        r = items.get(s) or {}
        print(f"{s}: {len(r)} fields · price {r.get('currentPrice')} · cap {r.get('marketCap')} · PE {r.get('trailingPE')} · "
              f"margin {r.get('profitMargins')} · rec {r.get('_rec')} · {r.get('_asof')}")
    print("sizes", os.path.getsize(FILE) // 1024, "KB figures,", os.path.getsize(TEXT_FILE) // 1024, "KB texts,",
          os.path.getsize(INS_FILE) // 1024, "KB insiders")
    print("insiders:", {k: len(ins.get(k) or []) for k in ("META", "NKE", "AAPL", "TSLA", "CRWV")})


if __name__ == "__main__":
    main()
