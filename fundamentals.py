"""
fundamentals.py - Value and financial-quality inputs from the SEC's XBRL company facts, point in time.

Every fact in a company's companyfacts file carries the date it was filed, so a value is used only from the day its report
reached the public: as_of(facts, date) never sees a number filed after `date`. GitHub Actions can reach the SEC (this
container cannot), so research/factor_test.py and the data jobs call fetch(); the site reads what they saved.

  compact(js)          -> {metric: [(start, end, filed, val), ...]}, only the tags needed here, from one companyfacts file
  known(facts, dates)  -> the same for a list of dates in one pass (the research run)
  as_of(facts, date)   -> the latest annual flows (net income, operating cash flow, gross profit) and balance-sheet values
                          (equity, assets, liabilities) and the diluted share count known on that date
  ratios(m, mcap)      -> value (earnings, book and cash-flow yields) and quality (ROE, gross profitability, leverage, accruals)
"""
import numpy as np
import pandas as pd

# metric -> the us-gaap tags that carry it, best first (companies use different ones)
FLOWS = {
    "ni": ("NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic"),
    "cfo": ("NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"),
    "gp": ("GrossProfit",),
    "rev": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet",
            "RevenueFromContractWithCustomerIncludingAssessedTax"),
    "cogs": ("CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold", "CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization"),
}
STOCKS = {
    "equity": ("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
    "assets": ("Assets",),
    "liabilities": ("Liabilities",),
    "liab_equity": ("LiabilitiesAndStockholdersEquity",),
}
SHARES = ("WeightedAverageNumberOfDilutedSharesOutstanding", "WeightedAverageNumberOfSharesOutstandingBasic")
ANNUAL = (340, 390)                                  # days a fiscal-year flow spans
STALE_FLOW, STALE_STOCK = 550, 460                  # older than this (days from the period's end): not used


def compact(js):
    """One companyfacts JSON -> {metric: sorted [(span in days or None for an instant, end, filed, val, tag rank)]}, only the
    facts needed here. Dates stay ISO strings, which compare in date order."""
    gaap = (js or {}).get("facts", {}).get("us-gaap", {})
    out = {}
    for metric, tags in {**FLOWS, **STOCKS, "shares": SHARES}.items():
        rows = []
        for rank, tag in enumerate(tags):
            units = gaap.get(tag, {}).get("units", {})
            for f in units.get("shares" if metric == "shares" else "USD", []):
                if "filed" not in f or "end" not in f or f.get("val") is None:
                    continue
                span = _days(f["start"], f["end"]) if f.get("start") else None
                rows.append((span, f["end"], f["filed"], float(f["val"]), rank))
        if rows:
            out[metric] = sorted(rows, key=lambda r: (r[1], r[2]))
    return out


def _days(a, b):
    return (pd.Timestamp(b) - pd.Timestamp(a)).days


def _known(rows, dates, kind):
    """For each date (ascending ISO strings): (value, period end) of the latest period known on it: filed on or before it,
    the latest period end, and among the facts for that end the best tag, then the latest filing (a restatement replaces
    the first number). The set of known facts only grows with the date, so the best one is a running maximum.
    kind: "annual" (a fiscal-year span), "instant" (a balance-sheet value) or "any" (a positive span of any length)."""
    rows = sorted(rows, key=lambda r: r[2])
    out, best, i = [], None, 0
    for d in dates:
        while i < len(rows) and rows[i][2] <= d:
            span, end, filed, val, rank = rows[i]
            i += 1
            if kind == "annual" and (span is None or not (ANNUAL[0] <= span <= ANNUAL[1])):
                continue
            if kind == "instant" and span is not None:
                continue
            if kind == "any" and (span is None or val <= 0):
                continue
            key = (end, -rank, filed)
            if best is None or key > best[0]:
                best = (key, val, end)
        if best is None or _days(best[2], d) > (STALE_FLOW if kind == "annual" else STALE_STOCK):
            out.append((np.nan, None))
        else:
            out.append((best[1], best[2]))
    return out


def known(facts, dates):
    """The inputs known on each date: a list of {ni, cfo, gp, equity, assets, liabilities, shares, shares_end}, NaN where
    unknown. One pass per metric, so a whole history costs little more than one date."""
    ds = sorted(str(pd.Timestamp(d).date()) for d in dates)
    cols = {k: _known(facts.get(k, []), ds, "annual") for k in FLOWS}
    cols.update({k: _known(facts.get(k, []), ds, "instant") for k in STOCKS})
    sh = _known(facts.get("shares", []), ds, "any")                  # the latest quarter's or year's diluted count
    out = []
    for i in range(len(ds)):
        m = {k: v[i][0] for k, v in cols.items()}
        if not np.isfinite(m["gp"]) and np.isfinite(m["rev"]) and np.isfinite(m["cogs"]):
            m["gp"] = m["rev"] - m["cogs"]
        if not np.isfinite(m["liabilities"]) and np.isfinite(m["liab_equity"]) and np.isfinite(m["equity"]):
            m["liabilities"] = m["liab_equity"] - m["equity"]
        m["shares"], m["shares_end"] = sh[i]
        out.append(m)
    return out


def as_of(facts, date):
    """The inputs known on one date (see known)."""
    return known(facts, [date])[0]


def _div(a, b, positive=True):
    if not (np.isfinite(a) and np.isfinite(b)) or b == 0 or (positive and b < 0):
        return np.nan
    return a / b


def ratios(m, mcap):
    """Raw value and quality ratios (higher = better for every one: leverage and accruals are negated)."""
    assets = m.get("assets", np.nan)
    return {
        "ep": _div(m.get("ni", np.nan), mcap),                   # earnings yield
        "bp": _div(m.get("equity", np.nan), mcap),               # book to price
        "cp": _div(m.get("cfo", np.nan), mcap),                  # operating cash-flow yield
        "roe": _div(m.get("ni", np.nan), m.get("equity", np.nan)),
        "gpa": _div(m.get("gp", np.nan), assets),                # gross profitability
        "lev": -_div(m.get("liabilities", np.nan), assets),      # lower leverage is better
        "acc": -_div(m.get("ni", np.nan) - m.get("cfo", np.nan), assets),   # earnings backed by cash are better
    }


VALUE = ("ep", "bp", "cp")
QUALITY = ("roe", "gpa", "lev", "acc")


def cik_map():
    import segments
    return segments.cik_map()


def fetch(cik):
    """The compact facts of one company, from the SEC (paced to its 10 requests a second)."""
    import segments
    return compact(segments._get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json", timeout=60).json())
