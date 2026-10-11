"""
scripts/build_sharia.py - The Saudi market's Sharia lists, read on a GitHub server (run by .github/workflows/sharia.yml).

Step one: the sources are fetched (on a GitHub server; this one has no way to reach them) and kept as they are in research/sharia_raw/ (the pages and the PDF), so the reader that
turns them into sharia_lists.json can be written against the real files:
  - Argaam's page that puts the Sharia boards' lists side by side (Al Rajhi Capital, Dr. Mohammed Al-Osaimi, Albilad Capital),
    in Arabic and in English;
  - the Almaqased Center's yearly study of the Saudi companies (Dr. Mohammed Al-Osaimi): every company's class (pure, mixed,
    not compliant) and the purification amount per share.
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "research", "sharia_raw")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Accept-Language": "ar,en;q=0.8"}

PAGES = {
    "argaam_ar": "https://www.argaam.com/ar/company/shariahcompanies/3/14/3",
    "argaam_en": "https://www.argaam.com/en/company/shariahcompanies/3/14/3",
    "argaam_article": "https://www.argaam.com/ar/article/articledetail/id/1836781",
    "almaqased_home": "https://almaqased.net/",
    "almaqased_lists": "https://almaqased.net/cleansing-calculator/",
    # the side-by-side table of each market (3 TASI, 14 Nomu) and each board's own list with its purification amounts
    # (1 Al Rajhi Capital, 2 Dr. Mohammed Al-Osaimi, 6 Albilad Capital)
    "argaam_side_3": "https://www.argaam.com/ar/company/shariahcompanies/1/3/3",
    "argaam_side_14": "https://www.argaam.com/ar/company/shariahcompanies/1/3/14",
    **{f"argaam_inst_{i}_{m}": f"https://www.argaam.com/ar/company/shariahcompaniesbyinstitution/{i}?marketid={m}"
       for i in (1, 2, 6) for m in (3, 14)},
}
PDFS = {
    "almaqased_2024_argaam": "https://argaamplus.s3.amazonaws.com/20dcbdb7-9c01-4763-a876-1904c998590f.pdf",
    "almaqased_2024": "https://almaqased.net/wp-content/uploads/2025/08/تقرير-عام-2024-المقاصد.pdf",
}


def get(url, binary=False):
    for i in range(3):
        try:
            r = requests.get(url, headers=UA, timeout=60)
            print(url, r.status_code, len(r.content), r.headers.get("content-type"))
            if r.status_code == 200:
                return r.content if binary else r.text
        except Exception as e:
            print(url, "failed", e)
        time.sleep(3 * (i + 1))
    return None


def main():
    os.makedirs(RAW, exist_ok=True)
    found = {}
    for name, url in PAGES.items():
        html = get(url)
        if html is None:
            continue
        with open(os.path.join(RAW, f"{name}.html"), "w", encoding="utf-8") as f:
            f.write(html)
        # every link to another Sharia list page or a PDF, so the next step knows what exists
        links = sorted({urljoin(url, h) for h in re.findall(r'href="([^"]+)"', html)
                        if "shariah" in h.lower() or h.lower().endswith(".pdf") or "uploads" in h.lower()})
        found[name] = links
    for name, url in PDFS.items():
        pdf = get(url, binary=True)
        if pdf and pdf[:4] == b"%PDF":
            with open(os.path.join(RAW, f"{name}.pdf"), "wb") as f:
                f.write(pdf)
    with open(os.path.join(RAW, "links.json"), "w", encoding="utf-8") as f:
        json.dump({"fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "links": found}, f, ensure_ascii=False, indent=1)
    print("saved", sorted(os.listdir(RAW)))


if __name__ == "__main__":
    sys.exit(main())
