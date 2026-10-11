"""
scripts/build_sharia.py - Builds sharia_lists.json: the Saudi market's Sharia lists, read on a GitHub server (run weekly by
.github/workflows/sharia.yml; this site's own server can't reach the sources). For every Saudi company:

  - Al Rajhi Capital's Sharia board and Albilad Capital's Sharia board: is the company on the board's list of permitted
    shares (each list's date). Read from Argaam's page that puts the boards' lists side by side (the main market and Nomu).
  - the Almaqased Center's yearly study (Dr. Mohammed bin Saud Al-Osaimi): the company's class - pure, mixed, not compliant,
    not compliant by its activity, or the public sector (Aramco) - and the purification amount per share in riyals for a year,
    from the study's PDF. The study leaves out the commercial banks and the insurers (their own Sharia boards study them).

The sources are kept as they came in research/sharia_raw/, so a change in their layout can be seen and the reader fixed.
`python scripts/build_sharia.py --offline` rebuilds the file from those copies without fetching.
"""
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "research", "sharia_raw")
OUT = os.path.join(ROOT, "sharia_lists.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Accept-Language": "ar,en;q=0.8"}

ARGAAM = "https://www.argaam.com"
MARKETS = {3: "main", 14: "nomu"}                               # Argaam's market ids: the main market (TASI) and Nomu
SIDE = "/ar/company/shariahcompanies/1/3/{m}"                   # the side-by-side table of one market
BOARDS = {"rajhi": 1, "osaimi": 2, "bilad": 6}                  # Argaam's ids of the boards (columns 1, 2, 3 of the table)
BOARD_COL = {"rajhi": 0, "osaimi": 1, "bilad": 2}
INST = "/ar/company/shariahcompaniesbyinstitution/{i}?marketid={m}"
PAGE = ARGAAM + "/ar/company/shariahcompanies/3/14/3"           # the page a visitor opens (named as the source)

# the Almaqased study: the newest PDF first (a new year's study is added at the top when it is published)
STUDY = [{"url": "https://almaqased.net/wp-content/uploads/2025/08/تقرير-عام-2024-المقاصد.pdf",
          "mirror": "https://argaamplus.s3.amazonaws.com/20dcbdb7-9c01-4763-a876-1904c998590f.pdf",
          "year": 2024, "published": "2025-08-15", "file": "almaqased_2024.pdf"}]
CLASSES = ("pure", "mixed", "not", "activity", "public")


# ---------------------------------------------------------------- fetching
def get(url, binary=False):
    import requests
    for i in range(3):
        try:
            r = requests.get(url, headers=UA, timeout=60)
            print(url, r.status_code, len(r.content))
            if r.status_code == 200:
                return r.content if binary else r.text
        except Exception as e:
            print(url, "failed", e)
        time.sleep(3 * (i + 1))
    return None


def fetch():
    os.makedirs(RAW, exist_ok=True)
    for m in MARKETS:
        html = get(ARGAAM + SIDE.format(m=m))
        if html:
            with open(os.path.join(RAW, f"argaam_side_{m}.html"), "w", encoding="utf-8") as f:
                f.write(html)
        for b, i in BOARDS.items():
            html = get(ARGAAM + INST.format(i=i, m=m))
            if html:
                with open(os.path.join(RAW, f"argaam_inst_{i}_{m}.html"), "w", encoding="utf-8") as f:
                    f.write(html)
    for s in STUDY[:1]:
        path = os.path.join(RAW, s["file"])
        if os.path.exists(path):
            continue
        for url in (s["url"], s.get("mirror")):
            pdf = get(url, binary=True) if url else None
            if pdf and pdf[:4] == b"%PDF":
                with open(path, "wb") as f:
                    f.write(pdf)
                break


# ---------------------------------------------------------------- Argaam
def _soup(name):
    from bs4 import BeautifulSoup
    path = os.path.join(RAW, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return BeautifulSoup(f.read(), "lxml")


def side_tables():
    """{code: {"market", "name", "rajhi", "osaimi", "bilad"}} and {board: list date} from the side-by-side tables."""
    rows, dates = {}, {}
    for m, mk in MARKETS.items():
        s = _soup(f"argaam_side_{m}.html")
        t = s.find("table", class_="ShariahCompanies") if s else None
        if t is None:
            print("no side table for market", m)
            continue
        trs = t.find_all("tr")
        head = [c.get_text(" ", strip=True) for c in trs[0].find_all(["th", "td"])]
        for b, col in BOARD_COL.items():
            d = re.search(r"(\d{4}-\d{2}-\d{2})", head[2 + col]) if len(head) > 2 + col else None
            if d:
                dates[b] = max(dates.get(b, ""), d.group(1))
        sector = None
        for tr in trs[1:]:
            tds = tr.find_all("td")
            if len(tds) == 1:
                sector = tds[0].get_text(strip=True)
                continue
            v = [c.get_text(strip=True) for c in tds]
            if len(v) < 5 or not re.fullmatch(r"\d{4}", v[0]):
                continue
            rows[v[0]] = {"market": mk, "name": v[1], "sector": sector,
                          **{b: v[2 + col] == "✔" for b, col in BOARD_COL.items()}}
    return rows, dates


def osaimi_argaam():
    """{code: purification} of the companies on Al-Osaimi's list as Argaam shows it (its pure companies) and the list's date."""
    out, date = {}, ""
    for m in MARKETS:
        s = _soup(f"argaam_inst_{BOARDS['osaimi']}_{m}.html")
        t = s.find("table", class_="ShariahInstitutions") if s else None
        if t is None:
            continue
        d = re.search(r'var LastUpdated = "(\d{4}-\d{2}-\d{2})', str(s))
        if d:
            date = max(date, d.group(1))
        for tr in t.find_all("tr")[1:]:
            v = [c.get_text(" ", strip=True) for c in tr.find_all("td")]
            if len(v) >= 4 and re.fullmatch(r"\d{4}", v[0]):
                try:
                    out[v[0]] = float(v[2])
                except ValueError:
                    out[v[0]] = None
    return out, date


# ---------------------------------------------------------------- the Almaqased study (PDF)
def _pdf_lines(path):
    txt = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, check=True).stdout.decode("utf-8", "replace")
    txt = unicodedata.normalize("NFKC", txt)                     # the PDF's Arabic presentation forms -> plain letters
    txt = re.sub(r"[‪-‮‎‏]", "", txt)
    return txt.split("\n")


def _cls(text):
    if "مختلطة" in text:
        return "mixed"
    if "متوافقة" in text:                                        # "غير متوافقة" (the PDF loses some letters: "غ� متوافقة")
        return "activity" if re.search(r"ال.?.شاط", text) else "not"
    if re.search(r"نق.ة", text):
        return "pure"
    if "فقرة" in text or "المنهج" in text:                       # Aramco: "see the methodology, paragraph 17"
        return "public"
    return None


_AMT = re.compile(r"^\s*(\d+\.\d+)(?=\s|$)")
_NUM = re.compile(r"(?<![\d.])(\d{1,4})(?![\d.])")


def _codes(ln):
    return [n for n in _NUM.findall(ln) if len(n) == 4 and n not in ("2024", "2025", "2026")] if not ("مكتب المقاصد" in ln) else []


def study_rows(path):
    """{code: {"cls", "purify", "n"}} from the study's table. A row is the purification amount, the class, the name, the code,
    the sector and the row's number on one line; a long name or sector wraps it: the amount (with the class) can sit on the
    line above the code or the line under it, and the row's number or the class on a line under it."""
    lines = [ln for ln in _pdf_lines(path) if ln.strip()]
    kind = []
    for ln in lines:
        if _codes(ln) and re.search(r"\s\d{1,3}\s*$", ln) or _codes(ln) and _AMT.match(ln):
            kind.append("row")
        elif _AMT.match(ln) and not _codes(ln):
            kind.append("amt")
        else:
            kind.append("txt")
    rows = {i: {"code": _codes(lines[i])[0], "amt": None, "text": [lines[i]]} for i, k in enumerate(kind) if k == "row"}
    for i, r in rows.items():
        m = _AMT.match(lines[i])
        if m:
            r["amt"] = float(m.group(1))
    for i, k in enumerate(kind):
        if k != "amt":
            continue
        a = float(_AMT.match(lines[i]).group(1))
        nxt, prv = i + 1, i - 1
        if nxt in rows and rows[nxt]["amt"] is None:          # the amount (and the class) above its code
            rows[nxt]["amt"] = a
            rows[nxt]["text"].insert(0, lines[i])
        elif prv in rows and rows[prv]["amt"] is None:        # the amount under its code
            rows[prv]["amt"] = a
            rows[prv]["text"].append(lines[i])
    out = {}
    for i, r in rows.items():
        sers = [int(n) for n in _NUM.findall(lines[i]) if len(n) <= 3]
        j = i + 1
        while j < len(lines) and j <= i + 2 and kind[j] == "txt" and "مكتب المقاصد" not in lines[j]:
            r["text"].append(lines[j])                           # a wrapped sector, the row's number, the class of a long row
            if not sers:
                sers = [int(n) for n in _NUM.findall(lines[j]) if len(n) <= 3]
            j += 1
        if r["amt"] is None or not sers:
            continue
        out[r["code"]] = {"purify": r["amt"], "cls": _cls(" ".join(r["text"])), "n": sers[-1]}
    # a class the text lost follows from the table's order: the pure companies first, then the mixed, then the rest
    by_n = sorted(out.items(), key=lambda kv: kv[1]["n"])
    last = None
    for code, r in by_n:
        if r["cls"] is None:
            r["cls"] = last if last in ("pure", "mixed", "not", "activity") else "pure"
        last = r["cls"] if r["cls"] != "public" else "pure"
    return out


# ---------------------------------------------------------------- the file
def build():
    side, dates = side_tables()
    osa_a, osa_date = osaimi_argaam()
    study, meta = {}, None
    for s in STUDY:
        p = os.path.join(RAW, s["file"])
        if os.path.exists(p):
            study, meta = study_rows(p), s
            break
    n = len(study)
    print(f"side tables: {len(side)} companies; Al-Osaimi on Argaam: {len(osa_a)} ({osa_date}); study rows: {n}")
    if n:
        ser = sorted(r["n"] for r in study.values())
        print("study classes", {c: sum(r["cls"] == c for r in study.values()) for c in CLASSES}, "rows", ser[0], "-", ser[-1],
              "missing", sorted(set(range(1, ser[-1] + 1)) - set(ser))[:20])
        # the two copies of Al-Osaimi's list must agree: Argaam's are the study's pure companies
        diff = [c for c in osa_a if c in study and study[c]["cls"] not in ("pure", "public")]
        print("on Argaam's Al-Osaimi list but not pure in the study:", diff[:20])
    if len(side) < 200 or (meta and n < 250):
        print("too little read: the file is left as it was")
        return 1
    # a newer Al-Osaimi list on Argaam than the study read here: its pure companies (and their amounts) win, and a company the
    # study called pure that the newer list leaves out is no longer known
    newer = bool(meta and osa_date and len(osa_a) > 150 and osa_date > (meta.get("published") or "") and
                 (datetime.fromisoformat(osa_date) - datetime.fromisoformat(meta["published"])).days > 45)
    if newer:
        print(f"Argaam's Al-Osaimi list ({osa_date}) is newer than the study ({meta['published']}): add the new study's PDF to STUDY")
    items = {}
    for code in sorted(set(side) | set(study) | set(osa_a)):
        sd, sr = side.get(code), study.get(code)
        it = {}
        if sd:
            it.update(m=sd["market"], rajhi=sd["rajhi"], bilad=sd["bilad"])
        if code in osa_a and (newer or not sr):                 # on Argaam's copy of the list: pure
            it.update(osaimi="pure", purify=osa_a[code])
        elif sr and not (newer and sr["cls"] == "pure"):        # (a pure one on the newer list was taken above)
            it.update(osaimi=sr["cls"], purify=sr["purify"])
        items[f"{code}.SR"] = it
    doc = {"built": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "sources": {"rajhi": {"date": dates.get("rajhi"), "url": PAGE},
                       "bilad": {"date": dates.get("bilad"), "url": PAGE},
                       "osaimi": {"date": osa_date if newer else (meta or {}).get("published") or osa_date,
                                  "year": None if newer else (meta or {}).get("year"),
                                  "url": PAGE if newer else (meta or {}).get("url") or PAGE, "argaam_date": osa_date}},
           "items": items}
    try:
        with open(OUT, encoding="utf-8") as f:
            prev = json.load(f)
        if {k: v for k, v in prev.items() if k != "built"} == {k: v for k, v in doc.items() if k != "built"}:
            print("the lists haven't changed:", len(items), "companies")
            return 0
    except (OSError, ValueError):
        pass
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote", OUT, len(items), "companies")
    return 0


def main():
    if "--offline" not in sys.argv:
        fetch()
    return build()


if __name__ == "__main__":
    sys.exit(main())
