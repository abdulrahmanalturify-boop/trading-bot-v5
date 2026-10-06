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
import threading
import time
import xml.etree.ElementTree as ET
from datetime import date
from itertools import combinations

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(HERE, "segments.json")
# the SEC asks automated tools to say who they are; the earlier agent stays as a second try (it is known to be accepted)
AGENTS = [a for a in (os.environ.get("SEC_USER_AGENT"), "TURA Pro research research@abdulrahman.streamlit.app",
                      "A.Alturaifi Pro research research@abdulrahman.streamlit.app") if a]
UA = AGENTS[0]
VERSION = 6                                         # a change in how a filing is read: every company is read again
FORMS = ("10-K", "20-F", "40-F")

REVENUE = ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "RevenueFromContractWithCustomerIncludingAssessedTax",
           "SalesRevenueNet", "Revenue", "RevenueFromContractsWithCustomers", "RevenuesNetOfInterestExpense",
           "RegulatedAndUnregulatedOperatingRevenue", "ElectricUtilityRevenue", "RealEstateRevenueNet", "HealthCareOrganizationRevenue",
           "PremiumsEarnedNet", "OperatingLeaseLeaseIncome", "InterestAndDividendIncomeOperating")
# a part of the revenue (an insurer's premiums, a landlord's rents): its lines are measured against the whole, the rest is "Other"
PARTIAL = {"PremiumsEarnedNet", "OperatingLeaseLeaseIncome", "InterestAndDividendIncomeOperating"}
# axis local name -> (kind, priority): a product split says most about the business, then segments, then regions
AXES = {"ProductOrServiceAxis": ("product", 3), "ProductsAndServicesAxis": ("product", 3),
        "StatementBusinessSegmentsAxis": ("segment", 2), "SegmentsAxis": ("segment", 2),
        "StatementGeographicalAxis": ("region", 1), "GeographicalAreasAxis": ("region", 1)}
SKIP = re.compile(r"Elimination|Intersegment|IntersegmentElimination|Corporate|Reconcil|Consolidat|Adjust|Hedg|Unallocated|"
                  r"OperatingSegmentsMember$|SegmentsMember$|^Segments?$", re.I)
BEFORE = {"XOM": 34088}                           # ticker -> the CIK that filed its annual reports before a reorganization
COUNTRY = {"US": "United States", "CN": "China", "TW": "Taiwan", "JP": "Japan", "GB": "United Kingdom", "DE": "Germany",
           "FR": "France", "CA": "Canada", "IN": "India", "KR": "South Korea", "NL": "Netherlands", "IE": "Ireland", "CH": "Switzerland",
           "MX": "Mexico", "BR": "Brazil", "SG": "Singapore", "HK": "Hong Kong", "AU": "Australia", "IL": "Israel"}


class Missing(Exception):
    pass


# ---------------------------------------------------------------- the SEC
_S = requests.Session()
_LAST = [0.0]


_PACE = threading.Lock()


def _get(url, timeout=40):
    with _PACE:
        wait = 0.12 - (time.time() - _LAST[0])       # the SEC asks for at most 10 requests a second
        if wait > 0:
            time.sleep(wait)
        _LAST[0] = time.time()
    global UA
    r = _S.get(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"}, timeout=timeout)
    if r.status_code == 403 and UA in AGENTS and AGENTS.index(UA) + 1 < len(AGENTS):
        UA = AGENTS[AGENTS.index(UA) + 1]           # refused: the next declared agent, kept from then on
        return _get(url, timeout)
    if r.status_code != 200:
        raise Missing(f"HTTP {r.status_code} {url}")
    return r


def cik_map():
    """ticker -> CIK, for every company that files with the SEC."""
    js = _get("https://www.sec.gov/files/company_tickers.json").json()
    return {str(v["ticker"]).upper().replace(".", "-"): int(v["cik_str"]) for v in js.values()}


def latest_annual(cik, debug=False):
    """(form, accession, report date, filing date) of the latest annual report, or None."""
    js = _get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json").json()
    pages = [js.get("filings", {}).get("recent", {})]
    if debug:
        forms = {}
        for f in pages[0].get("form", []):
            forms[f] = forms.get(f, 0) + 1
        print(f"  [CIK {cik}] {js.get('name')} · {len(pages[0].get('form', []))} recent filings · "
              f"{sorted(forms.items(), key=lambda kv: -kv[1])[:12]} · more pages {[f.get('name') for f in js.get('filings', {}).get('files') or []][:3]}")
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
    xsd = [n for n in names if n.endswith(".xsd")]
    return base, (inst[0] if inst else None), (lab[0] if lab else None), (xsd[0] if xsd else None)


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


def breakdown(ctx, units, facts, debug=None):
    """The best revenue breakdowns in an annual report: {'biz': by product line or business segment, 'geo': by region}, each
    {'end', 'start', 'cur', 'total', 'axis', 'kind', 'rows': [(member, value)], 'coverage', 'exact'} or None."""
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
    whole = [t for k, t in totals.items() if k not in PARTIAL]
    if not whole:
        return None
    biggest = max(whole, key=lambda t: t[0])
    total_of = lambda con: biggest if con in PARTIAL else (totals.get(con) or biggest)
    groups, pairs = {}, {}
    for con, c, u, v in facts:
        if not period(c) or v <= 0:
            continue
        # "the operating segments together" adds nothing to a fact's meaning (the newer segment notes tag every line with it)
        dims = {a: m for a, m in ctx[c][2].items() if not (a == "ConsolidationItemsAxis" and _qlocal(m) == "OperatingSegmentsMember")}
        if not dims or any(m == "typed" or SKIP.search(_qlocal(m)) for m in dims.values()):
            continue
        if len(dims) == 1:
            (axis, member), = dims.items()
            if axis in AXES:
                groups.setdefault((con, axis), {})[member] = v
        elif len(dims) == 2:                            # e.g. each drug's sales in the US and abroad, or product lines inside segments
            for axis, member in dims.items():
                if axis in AXES:
                    oax = next(a for a in dims if a != axis)
                    pairs.setdefault((con, axis, oax), {}).setdefault(member, {})[dims[oax]] = v
    cands = [(con, axis, "", mem) for (con, axis), mem in groups.items()]
    for (con, axis, oax), mem in pairs.items():
        total = total_of(con)[0]
        sums = {m: sum(o.values()) for m, o in mem.items()}
        one = all(len(o) == 1 for o in mem.values())    # each line told once: the same as a plain split
        whole_ = abs(sum(sums.values()) / total - 1) <= 0.02
        ok = len(sums) >= 2 and (one or whole_)
        drill = _drill(mem, groups.get((con, oax), {}), AXES.get(oax, ("", 0))[0], total) \
            if AXES[axis][0] == "product" and oax in AXES and AXES[oax][0] != "product" else None
        if debug is not None:
            debug.append(f"{con} · {axis} x {oax} · {len(sums)} lines · sum {sum(sums.values()) / total:.3f} · "
                         f"{'told once' if one else 'added up'}{' -> candidate' if ok else ''}"
                         f"{' · inside each part: ' + str(len(drill)) + ' lines' if drill else ''}")
        if ok:
            cands.append((con, axis, "one" if one else "all", sums))
        if drill and len(drill) >= 2:
            cands.append((con, axis, "all", drill))
    best = {"biz": None, "geo": None}
    for con, axis, how, mem in cands:
        total, cur = total_of(con)
        items = sorted(mem.items(), key=lambda kv: -kv[1])
        if how == "all":                                # every line, added across the other split, is the whole: keep them all
            pick, cov, exact = items, sum(mem.values()) / total, True
        elif how == "one":                              # a looser fit could take a total and its own parts together
            pick, cov, exact = _fit(items[:14], total, (0.015,))
            if not exact and con not in PARTIAL:
                pick = []
        else:
            pick, cov, exact = _fit(items[:14], total)
        if debug is not None:
            debug.append(f"{con} · {axis}{' (' + how + ')' if how else ''} · {len(mem)} lines · sum {sum(mem.values()) / total:.3f} of "
                         f"{total / 1e9:.1f}B · picked {len(pick)} exact={exact} cov={cov:.3f} · {[_qlocal(m)[:28] for m, _ in items[:8]]}")
        if not pick:
            continue
        kind, pri = AXES[axis]
        side = "geo" if kind == "region" else "biz"
        # three lines or more say more than two broad ones; then the split that accounts for the whole revenue;
        # then products over segments; then the finer one
        score = (len(pick) >= 3, exact, -round(abs(cov - 1) * 200), pri, len(pick))
        if best[side] is None or score > best[side][0]:
            best[side] = (score, {"end": end, "start": start, "cur": cur, "total": total, "axis": axis, "kind": kind,
                                  "rows": [(m, v) for m, v in pick], "coverage": cov, "exact": exact})
    out = {k: v[1] for k, v in best.items() if v}
    return out or None


def _drill(mem, parts, kind, total):
    """Product lines told inside each part of another split (Alphabet's Search, YouTube... inside Google Services; each drug's
    sales in the US and abroad): {product: value} over the parts that make up the whole revenue, or None.
    mem: {product: {part: value}}; parts: {part: value} from the other split itself."""
    inside = {}
    for prod, by in mem.items():
        for part, v in by.items():
            inside.setdefault(part, {})[prod] = v
    usable = sorted(((o, v) for o, v in parts.items() if o in inside or kind == "segment"), key=lambda kv: -kv[1])[:14]
    whole, _, exact = _fit(usable, total, (0.015,))
    if not exact:
        return None
    out, opened = {}, False
    for part, val in whole:
        lines = sorted(inside.get(part, {}).items(), key=lambda kv: -kv[1])[:14]
        if len(lines) >= 2:
            sub, _, ok = _fit(lines, val, (0.015,))
        else:
            sub, ok = lines, bool(lines) and abs(lines[0][1] / val - 1) <= 0.015
        if not ok:
            if kind != "segment":                       # a region without its lines: the sum would be short
                return None
            sub = [(part, val)]                         # a segment told without lines (Google Cloud) stays one line
        else:
            opened = True
        for prod, v in sub:
            out[prod] = out.get(prod, 0.0) + v
    return out if opened else None


def _fit(items, total, tols=(0.015, 0.03)):
    """The finest set of lines that adds up to the total (within 1.5%, then 3%); else all of them with an 'Other' remainder
    when they cover at least 60% without passing it. ([(member, value)], coverage, exact) or ([], 0, False)."""
    vals = [v for _, v in items]
    n = len(items)
    if n < 2:
        return [], 0.0, False
    for tol in tols:
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
    dbg = [] if os.environ.get("SEG_DEBUG") and sym.upper() in os.environ.get("SEG_DEBUG", "").split(",") else None
    la = latest_annual(cik, dbg is not None)
    if not la and sym.upper() in BEFORE:               # a new holding company: the last annual report is under the old one
        cik = BEFORE[sym.upper()]
        la = latest_annual(cik, dbg is not None)
    if not la:
        return {"why": "no annual report", "cik": cik}
    form, acc, rep, fil = la
    if prev and prev.get("acc") == acc and prev.get("v") == VERSION:
        return prev
    base, inst, lab, xsd = filing_files(cik, acc)
    if not inst:
        return {"acc": acc, "why": "no XBRL data", "cik": cik}
    ctx, units, facts = parse_instance(_get(f"{base}/{inst}", timeout=90).content)
    bd = breakdown(ctx, units, facts, dbg)
    if dbg is not None:
        print(f"  [{sym}] instance {inst} · label file {lab} · xsd {xsd}")
        for line in dbg:
            print(f"  [{sym}]   {line}")
    if not bd:
        return {"v": VERSION, "acc": acc, "why": "no breakdown", "cik": cik}
    labels = parse_labels(_get(f"{base}/{lab}", timeout=60).content) if lab else {}
    if xsd and not any(k.endswith("Member") and not k.startswith(("us-gaap_", "srt_", "dei_", "country_")) for k in labels):
        try:                                       # newer filings keep their own labels inside the schema
            labels.update(parse_labels(_get(f"{base}/{xsd}", timeout=60).content))
        except Exception:
            pass
    if dbg is not None:
        print(f"  [{sym}] labels {len(labels)} · e.g. {[k for k in labels if 'Member' in k][:4]}")
    def name(m):
        if m == "Other":
            return "Other"
        lab_ = labels.get(m.replace(":", "_"))
        if m.startswith("country:"):                    # the SEC's country list is in capitals: "UNITED STATES"
            return COUNTRY.get(_qlocal(m)) or (lab_.title() if lab_ and lab_.isupper() else lab_) or humanize(m)
        return lab_ or humanize(m)
    pack = lambda b: [(name(m), round(v, 2)) for m, v in b["rows"] if v / b["total"] >= 0.0005]
    main, alt = bd.get("biz"), bd.get("geo")
    if not main or (alt and max(v for _, v in main["rows"]) / main["total"] >= 0.95):
        main, alt = alt or main, (main if alt else None)   # one line near 100% says little: the regions first
    out = {"v": VERSION, "acc": acc, "cik": cik, "form": form, "end": main["end"], "start": main["start"], "filed": fil, "cur": main["cur"],
           "total": main["total"], "kind": main["kind"], "axis": main["axis"], "rows": pack(main),
           "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{acc}-index.htm"}
    if alt:
        out["alt"] = {"kind": alt["kind"], "axis": alt["axis"], "total": alt["total"], "cur": alt["cur"], "rows": pack(alt)}
    return out


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


_LIVE, _LOCK, _CIKS = {}, threading.Lock(), {"t": 0.0, "map": None}


def _ciks():
    if _CIKS["map"] is None or time.time() - _CIKS["t"] > 86400:
        _CIKS["map"], _CIKS["t"] = cik_map(), time.time()
    return _CIKS["map"]


def _work(sym):
    try:
        r = fetch(sym, _ciks())
    except Exception as e:                          # the SEC busy or unreachable: try again in an hour
        r = {"why": f"error {type(e).__name__}", "retry": True}
    _LIVE[sym] = (time.time(), r)


def get(sym):
    """The revenue breakdown of a company for the page, or None. From segments.json; a company outside it is read from the SEC
    in the background (the page never waits for it) and shows on the next refresh, kept for a week."""
    sym = sym.upper()
    hit = _file().get(sym)
    if hit is not None:
        return hit if hit.get("rows") else None
    with _LOCK:
        got = _LIVE.get(sym)
        stale = got is not None and got[0] and time.time() - got[0] > (3600 if got[1].get("retry") else 7 * 86400)
        if got is None or stale:
            _LIVE[sym] = (0.0, {})                  # being read
            threading.Thread(target=_work, args=(sym,), daemon=True).start()
            return None
    r = got[1]
    return r if r.get("rows") else None


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "19.5"
