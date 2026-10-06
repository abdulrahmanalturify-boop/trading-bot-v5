"""
segments.py - Where a company's revenue comes from (by product line, by business segment, or by region), read from its latest
annual report filed with the SEC (10-K, or 20-F / 40-F for companies abroad), the XBRL data that comes with every filing.

  - The breakdown is the one the company reports itself: the revenue facts tagged with one member of the product / segment /
    geography axis, for the latest fiscal year. Nested lines (iPhone, Mac ... and "Products" over them) are untangled by
    keeping the finest set of lines that adds up to the total revenue.
  - Lines carry the company's own labels (from the filing's label file).
  - scripts/build_segments.py fills segments.json for the site's ~550 companies once a month (GitHub Actions can reach the SEC);
    the page reads that file, and fetches a company that isn't in it live (kept 7 days).
"""
import io
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import date
from itertools import combinations

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(HERE, "segments.json")
UA = os.environ.get("SEC_USER_AGENT") or "A.Alturaifi Pro research research@abdulrahman.streamlit.app"
VERSION = 2                                         # a change in how a filing is read: every company is read again
FORMS = ("10-K", "20-F", "40-F")

REVENUE = ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "RevenueFromContractWithCustomerIncludingAssessedTax",
           "SalesRevenueNet", "Revenue", "RevenueFromContractsWithCustomers", "RevenuesNetOfInterestExpense")
# axis local name -> (kind, priority): a product split says most about the business, then segments, then regions
AXES = {"ProductOrServiceAxis": ("product", 3), "ProductsAndServicesAxis": ("product", 3),
        "StatementBusinessSegmentsAxis": ("segment", 2), "SegmentsAxis": ("segment", 2),
        "StatementGeographicalAxis": ("region", 1), "GeographicalAreasAxis": ("region", 1)}
SKIP = re.compile(r"Elimination|Intersegment|IntersegmentElimination|Corporate|Reconcil|Consolidat|Adjust|Hedg|Unallocated|"
                  r"OperatingSegmentsMember$|SegmentsMember$|^Segments?$", re.I)
COUNTRY = {"US": "United States", "CN": "China", "TW": "Taiwan", "JP": "Japan", "GB": "United Kingdom", "DE": "Germany",
           "FR": "France", "CA": "Canada", "IN": "India", "KR": "South Korea", "NL": "Netherlands", "IE": "Ireland", "CH": "Switzerland",
           "MX": "Mexico", "BR": "Brazil", "SG": "Singapore", "HK": "Hong Kong", "AU": "Australia", "IL": "Israel"}


class Missing(Exception):
    pass


# ---------------------------------------------------------------- the SEC
_S = requests.Session()
_LAST = [0.0]


def _get(url, timeout=40):
    wait = 0.12 - (time.time() - _LAST[0])           # the SEC asks for at most 10 requests a second
    if wait > 0:
        time.sleep(wait)
    _LAST[0] = time.time()
    r = _S.get(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"}, timeout=timeout)
    if r.status_code != 200:
        raise Missing(f"HTTP {r.status_code} {url}")
    return r


def cik_map():
    """ticker -> CIK, for every company that files with the SEC."""
    js = _get("https://www.sec.gov/files/company_tickers.json").json()
    return {str(v["ticker"]).upper().replace(".", "-"): int(v["cik_str"]) for v in js.values()}


def latest_annual(cik):
    """(form, accession, report date, filing date) of the latest annual report, or None."""
    js = _get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json").json()
    pages = [js.get("filings", {}).get("recent", {})]
    for f in (js.get("filings", {}).get("files") or [])[:1]:   # a busy filer: its annual report may sit on the next page
        try:
            pages.append(_get(f"https://data.sec.gov/submissions/{f['name']}").json())
        except Exception:
            pass
    for rec in pages:
        for form, acc, rep, fil in zip(rec.get("form", []), rec.get("accessionNumber", []), rec.get("reportDate", []), rec.get("filingDate", [])):
            if form in FORMS:
                return form, acc, rep, fil
    return None


def filing_files(cik, acc):
    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}"
    items = _get(base + "/index.json").json().get("directory", {}).get("item", [])
    names = [i.get("name", "") for i in items]
    inst = [n for n in names if n.endswith("_htm.xml")]
    if not inst:
        inst = [n for n in names if n.endswith(".xml") and not re.search(r"_(cal|def|lab|pre)\.xml$|FilingSummary|MetaLinks", n, re.I)]
    lab = [n for n in names if re.search(r"[_-]lab\.xml$", n, re.I)]
    return base, (inst[0] if inst else None), (lab[0] if lab else None)


# ---------------------------------------------------------------- reading the XBRL
def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _qlocal(q):
    return str(q).split(":", 1)[-1]


def parse_instance(xml_bytes):
    """(contexts, units, facts): contexts id -> (start, end, {axis: member}); facts [(concept local name, ctx, unit, value)]."""
    ctx, units, facts = {}, {}, []
    for _, el in ET.iterparse(io.BytesIO(xml_bytes), events=("end",)):
        t = _local(el.tag)
        if t == "context":
            start = end = None
            dims = {}
            for sub in el.iter():
                lt = _local(sub.tag)
                if lt == "startDate":
                    start = (sub.text or "").strip()
                elif lt == "endDate":
                    end = (sub.text or "").strip()
                elif lt == "instant":
                    start = end = (sub.text or "").strip()
                elif lt == "explicitMember":
                    dims[_qlocal(sub.get("dimension"))] = (sub.text or "").strip()
                elif lt == "typedMember":
                    dims[_qlocal(sub.get("dimension"))] = "typed"
            ctx[el.get("id")] = (start, end, dims)
            el.clear()
        elif t == "unit":
            m = [(s.text or "").strip() for s in el.iter() if _local(s.tag) == "measure"]
            units[el.get("id")] = m[0].split(":")[-1] if len(m) == 1 else "/".join(m)
            el.clear()
        elif t in REVENUE and el.get("contextRef"):
            try:
                v = float((el.text or "").strip())
            except ValueError:
                continue
            facts.append((t, el.get("contextRef"), el.get("unitRef"), v))
    return ctx, units, facts


def parse_labels(xml_bytes):
    """'prefix_LocalName' -> its label (the terse one when there is one)."""
    loc, lab, arcs = {}, {}, []
    for _, el in ET.iterparse(io.BytesIO(xml_bytes), events=("end",)):
        t = _local(el.tag)
        attrs = {_local(k): v for k, v in el.attrib.items()}
        if t == "loc":
            loc[attrs.get("label")] = attrs.get("href", "").split("#")[-1]
        elif t == "label":
            role = attrs.get("role", "")
            lab.setdefault(attrs.get("label"), []).append((role, (el.text or "").strip()))
        elif t == "labelArc":
            arcs.append((attrs.get("from"), attrs.get("to")))
    out = {}
    for f, to in arcs:
        el_id = loc.get(f)
        if not el_id:
            continue
        best = None
        for role, text in lab.get(to, []):
            if not text:
                continue
            if role.endswith("terseLabel"):
                best = text
                break
            if role.endswith("/label") and best is None:
                best = text
        if best:
            out[el_id] = re.sub(r"\s*\[(Member|Domain)\]\s*$", "", best).strip()
    return out


def humanize(member):
    loc = _qlocal(member)
    if member.startswith("country:"):
        return COUNTRY.get(loc, loc)
    loc = re.sub(r"(Segment)?Member$", "", loc)
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", loc).strip() or member


def _days(a, b):
    try:
        return (date.fromisoformat(b) - date.fromisoformat(a)).days
    except (TypeError, ValueError):
        return 0


def breakdown(ctx, units, facts):
    """The best revenue breakdown in an annual report: {'end', 'start', 'cur', 'total', 'axis', 'kind', 'rows': [(member, value)]} or None."""
    annual = [(c, ctx[c]) for _, c, _, _ in facts if c in ctx and 340 <= _days(ctx[c][0], ctx[c][1]) <= 380]
    if not annual:
        return None
    end = max(v[1] for _, v in annual)
    start = max(v[0] for _, v in annual if v[1] == end)
    period = lambda c: c in ctx and ctx[c][1] == end and ctx[c][0] == start
    totals = {}
    for con, c, u, v in facts:
        if period(c) and not ctx[c][2] and v > 0:
            totals.setdefault(con, (v, units.get(u, "USD")))
    if not totals:
        return None
    groups = {}
    for con, c, u, v in facts:
        if not period(c) or len(ctx[c][2]) != 1:
            continue
        (axis, member), = ctx[c][2].items()
        if axis not in AXES or member == "typed" or v <= 0 or SKIP.search(_qlocal(member)):
            continue
        groups.setdefault((con, axis), {})[member] = v
    best = None
    for (con, axis), mem in groups.items():
        total, cur = totals.get(con) or next(iter(totals.values()))
        items = sorted(mem.items(), key=lambda kv: -kv[1])[:14]
        pick, cov, exact = _fit(items, total)
        if not pick:
            continue
        kind, pri = AXES[axis]
        # three lines or more say more than two broad ones; then products over segments over regions; then an exact fit
        score = (len(pick) >= 3, pri, exact, -abs(cov - 1), len(pick))
        if best is None or score > best[0]:
            best = (score, {"end": end, "start": start, "cur": cur, "total": total, "axis": axis, "kind": kind,
                            "rows": [(m, v) for m, v in pick], "coverage": cov})
    return best[1] if best else None


def _fit(items, total):
    """The finest set of lines that adds up to the total (within 1.5%, then 3%); else all of them with an 'Other' remainder
    when they cover at least 60% without passing it. ([(member, value)], coverage, exact) or ([], 0, False)."""
    vals = [v for _, v in items]
    n = len(items)
    if n < 2:
        return [], 0.0, False
    for tol in (0.015, 0.03):
        for k in range(n, 1, -1):
            hit = None
            for idx in combinations(range(n), k):
                s = sum(vals[i] for i in idx)
                if abs(s / total - 1) <= tol and (hit is None or abs(s / total - 1) < hit[1]):
                    hit = (idx, abs(s / total - 1))
            if hit:
                return [items[i] for i in hit[0]], sum(vals[i] for i in hit[0]) / total, True
    s = sum(vals)
    if 0.6 <= s / total < 1.0:
        return items + [("Other", total - s)], s / total, False
    return [], 0.0, False


def fetch(sym, ciks=None, prev=None):
    """One company's breakdown from its latest annual report: a dict ready for segments.json (or {'acc', 'why'} when none).
    prev: what segments.json already holds for it (nothing is downloaded again when the filing is the same)."""
    ciks = ciks or cik_map()
    cik = ciks.get(sym.upper())
    if not cik:
        return {"why": "no SEC filer"}
    la = latest_annual(cik)
    if not la:
        return {"why": "no annual report", "cik": cik}
    form, acc, rep, fil = la
    if prev and prev.get("acc") == acc and prev.get("v") == VERSION:
        return prev
    base, inst, lab = filing_files(cik, acc)
    if not inst:
        return {"acc": acc, "why": "no XBRL data", "cik": cik}
    ctx, units, facts = parse_instance(_get(f"{base}/{inst}", timeout=90).content)
    b = breakdown(ctx, units, facts)
    if not b:
        return {"acc": acc, "why": "no breakdown", "cik": cik}
    labels = parse_labels(_get(f"{base}/{lab}", timeout=60).content) if lab else {}
    if os.environ.get("SEG_DEBUG") and sym.upper() in os.environ.get("SEG_DEBUG", "").split(","):
        print(f"  [{sym}] instance {inst} · labels {lab} ({len(labels)}) · rows {[m for m, _ in b['rows']]}")
        print(f"  [{sym}] label keys like: {[k for k in labels if 'Member' in k][:6]}")
    rows = [(labels.get(m.replace(":", "_")) or humanize(m) if m != "Other" else "Other", round(v, 2)) for m, v in b["rows"]
            if v / b["total"] >= 0.0005]
    return {"v": VERSION, "acc": acc, "cik": cik, "form": form, "end": b["end"], "start": b["start"], "filed": fil, "cur": b["cur"],
            "total": b["total"], "kind": b["kind"], "axis": b["axis"], "rows": rows,
            "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{acc}-index.htm"}


# ---------------------------------------------------------------- for the page
_FILE_CACHE = {"mtime": None, "data": {}}


def _file():
    try:
        m = os.path.getmtime(FILE)
    except OSError:
        return {}
    if _FILE_CACHE["mtime"] != m:
        try:
            with open(FILE, encoding="utf-8") as f:
                _FILE_CACHE["data"] = json.load(f).get("items", {})
            _FILE_CACHE["mtime"] = m
        except (OSError, ValueError):
            return {}
    return _FILE_CACHE["data"]


def get(sym):
    """The revenue breakdown of a company for the page, or None. From segments.json, else fetched live from the SEC (kept 7 days)."""
    hit = _file().get(sym.upper())
    if hit is not None:
        return hit if hit.get("rows") else None
    try:
        r = _live(sym.upper())
    except Exception:
        return None
    return r if r and r.get("rows") else None


try:
    import streamlit as st

    @st.cache_data(ttl=7 * 86400, show_spinner=False)
    def _live(sym):
        return fetch(sym, _ciks())

    @st.cache_data(ttl=86400, show_spinner=False)
    def _ciks():
        return cik_map()
except Exception:                                   # the builder script runs without Streamlit
    def _live(sym):
        return fetch(sym)

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "19.1"
