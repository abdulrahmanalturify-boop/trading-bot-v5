"""
newspics.py - A photo for every headline.

1) The story's own photo: the picture its article page shows when the link is shared (og:image / twitter:image). The news bot
   looks it up in the background for every story whose feed sent no picture (Google News links are first turned into the
   publisher's own link), so the pages never wait for it.
2) When the article has none (or the outlet blocks readers): a free photo of the story's topic from Wikimedia Commons
   (public domain or Creative Commons; the photographer and the licence show on hover). The photos of each topic are
   looked up once a week, kept on disk, and the same story always gets the same photo.
3) If a photo cannot load in the browser, the next one takes its place (theme.FX_JS), and last the topic's coloured card.
"""
import hashlib
import html as _html
import json
import os
import re
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait
from urllib.parse import quote, urljoin, urlparse

import requests

# commons asks every tool to say who it is
UA_WIKI = {"User-Agent": "AAlturaifiPro/1.0 (https://abdulrahman.streamlit.app; market-news pictures)"}
BROWSER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"}

# the searches behind each topic's photos (newsiq topic keys; "street" is the general market picture)
TOPIC_Q = {
    "fed": ["Eccles Building Federal Reserve", "Federal Reserve Bank building"],
    "inflation": ["supermarket aisle", "grocery store shelves"],
    "jobs": ["construction workers building site", "factory assembly line"],
    "economy": ["Manhattan financial district skyline", "shopping street crowd"],
    "bonds": ["Treasury Building Washington", "United States Department of the Treasury building"],
    "trade": ["container ship port", "container terminal cranes"],
    "geo": ["United Nations headquarters flags", "oil tanker at sea"],
    "policy": ["United States Capitol", "White House Washington"],
    "earnings": ["stock market quotes screen", "corporate headquarters skyscraper"],
    "guidance": ["stock chart computer screen", "business meeting presentation"],
    "analyst": ["stock market display board", "trading screens"],
    "payout": ["stack of coins", "United States dollar banknotes"],
    "mna": ["office towers skyscrapers", "conference room table"],
    "ipo": ["New York Stock Exchange facade", "Nasdaq MarketSite Times Square"],
    "legal": ["Supreme Court of the United States building", "courthouse columns"],
    "health": ["pills tablets medicine", "laboratory pipette"],
    "distress": ["store closing sign", "abandoned shopping mall"],
    "layoffs": ["empty office", "office cubicles"],
    "product": ["smartphones", "consumer electronics store"],
    "ai": ["semiconductor wafer", "data center servers", "integrated circuit chip"],
    "crypto": ["bitcoin coins", "cryptocurrency coins"],
    "oil": ["pumpjack oil field", "oil refinery"],
    "metals": ["gold bars", "gold bullion"],
    "fx": ["banknotes currencies", "currency exchange rates board"],
    "move": ["New York Stock Exchange trading floor", "stock ticker board"],
    "street": ["Wall Street New York", "New York Stock Exchange"],
}
GENERAL = "street"
WEEK = 7 * 86400
_DISK = os.path.join(tempfile.gettempdir(), "alturaifi_newspics_v1.json")
_POOLS = {}                 # topic -> {"at": time, "pics": [{"u": 500px url, "b": 960px url, "c": credit}]}
_LOCK = threading.Lock()
_FILLING = threading.Lock()
_STATE = {"tried": 0.0, "loaded": False, "rest": 0.0}

# never shown, whatever the search brings back
_BAD_WORDS = re.compile(r"\b(nude|naked|nsfw|sex\w*|erotic|porn\w*|lingerie|bikini|corpse|dead|death|blood\w*|gore|injur\w*|war|weapons?|guns?|"
                        r"rifles?|soldiers?|army|military|protest\w*|riot\w*|fire|burn\w*|accident|crash\w*|child\w*|kids?|bab(?:y|ies)|"
                        r"portrait|selfie|logo|diagram|chart|graph|map|svg|icon|flag of)\b", re.I)
_TAGS = re.compile(r"<[^>]+>")
_PX = re.compile(r"/(\d+)px-")             # the width in a thumbnail link


# ---------------------------------------------------------------- topic photos (Wikimedia Commons)
def _credit(meta):
    def v(k):
        return _html.unescape(_TAGS.sub("", str((meta.get(k) or {}).get("value") or ""))).strip()
    who = re.sub(r"\s+", " ", v("Artist"))[:70]
    lic = v("LicenseShortName")
    return " · ".join(x for x in (f"Photo: {who}" if who else "Photo", lic, "Wikimedia Commons") if x)


def _free(meta):
    lic = str((meta.get("LicenseShortName") or {}).get("value") or "").lower()
    return lic.startswith(("public domain", "pd", "cc0", "cc by", "cc-by"))


def _search(q, quality=True, n=40):
    """Landscape JPEG photos with a free licence for one search (the photos rated 'quality images' first)."""
    params = {"action": "query", "format": "json", "formatversion": "2", "generator": "search", "gsrnamespace": "6",
              "gsrsearch": f"{q} filetype:bitmap" + (" incategory:Quality_images" if quality else ""), "gsrlimit": str(n),
              "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": "960",
              "iiextmetadatafilter": "LicenseShortName|Artist", "maxlag": "5"}
    r = requests.get("https://commons.wikimedia.org/w/api.php", params=params, headers=UA_WIKI, timeout=12)
    r.raise_for_status()
    pages = (r.json().get("query") or {}).get("pages") or []
    if isinstance(pages, dict):                      # the older answer shape
        pages = list(pages.values())
    out = []
    for p in sorted(pages, key=lambda p: p.get("index", 999)):
        ii = (p.get("imageinfo") or [{}])[0]
        title, meta = str(p.get("title") or ""), ii.get("extmetadata") or {}
        w, h, big = ii.get("width") or 0, ii.get("height") or 0, str(ii.get("thumburl") or "")
        px = _PX.search(big)
        if ii.get("mime") != "image/jpeg" or not big.startswith("https://") or not px:
            continue
        if w < 1200 or not (1.2 * h <= w <= 3.2 * h) or _BAD_WORDS.search(title) or not _free(meta):
            continue
        small = big[:px.start()] + "/500px-" + big[px.end():] if int(px.group(1)) > 500 else big
        out.append({"u": small, "b": big, "c": _credit(meta)})
    return out


def _load():
    if _STATE["loaded"]:
        return
    _STATE["loaded"] = True
    try:
        with open(_DISK, encoding="utf-8") as f:
            saved = json.load(f)
        with _LOCK:
            for k, v in saved.items():
                if k in TOPIC_Q and isinstance(v, dict) and v.get("pics"):
                    _POOLS.setdefault(k, v)
    except Exception:
        pass


def _save():
    try:
        with _LOCK:
            snap = dict(_POOLS)
        tmp = _DISK + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(snap, f)
        os.replace(tmp, _DISK)
    except Exception:
        pass


def fill(budget=90):
    """Looks up the photos of every topic that has none, or whose photos are a week old (the news bot calls this)."""
    _load()
    if time.time() < _STATE["rest"] or not _FILLING.acquire(blocking=False):
        return
    try:
        end = time.time() + budget
        now = time.time()
        todo = [t for t in TOPIC_Q if now - (_POOLS.get(t) or {}).get("at", 0) > WEEK or not (_POOLS.get(t) or {}).get("pics")]
        todo.sort(key=lambda t: t != GENERAL)          # the general picture first: it stands in for every other topic
        changed = False
        for t in todo:
            if time.time() > end:
                break
            pics, seen = [], set()
            for q in TOPIC_Q[t]:
                for quality in (True, False):
                    if len(pics) >= 10:
                        break
                    try:
                        found = _search(q, quality)
                    except requests.HTTPError as e:
                        if getattr(e.response, "status_code", 0) in (403, 429):
                            _STATE["rest"] = time.time() + 1800
                            return
                        found = []
                    except Exception:
                        found = []
                    for p in found:
                        if p["b"] not in seen:
                            seen.add(p["b"])
                            pics.append(p)
                    time.sleep(0.3)
            if pics:
                with _LOCK:
                    _POOLS[t] = {"at": time.time(), "pics": pics[:12]}
                changed = True
        if changed:
            _save()
    finally:
        _FILLING.release()


def _fill_soon():
    """Starts a background lookup when a page needs a topic photo that is not there yet (at most every 10 minutes)."""
    if time.time() - _STATE["tried"] < 600:
        return
    _STATE["tried"] = time.time()
    try:
        threading.Thread(target=fill, daemon=True, name="news-pics").start()
    except RuntimeError:
        pass


def topic_photo(topic, key, big=False):
    """{"u": url, "c": credit} of the topic's photo for this story (the same story always gets the same one), or None."""
    _load()
    pool = (_POOLS.get(topic) or {}).get("pics") or (_POOLS.get(GENERAL) or {}).get("pics")
    if not pool or (topic in TOPIC_Q and not (_POOLS.get(topic) or {}).get("pics")):
        _fill_soon()
    if not pool:
        return None
    i = int(hashlib.md5(str(key or "").encode("utf-8")).hexdigest()[:8], 16) % len(pool)
    p = pool[i]
    return {"u": p["b"] if big else p["u"], "c": p.get("c") or ""}


def topic_of(n, known=None):
    """The story's topic (as theme.news_thumb picks it)."""
    iq = n.get("iq") or {}
    return next((t for t in iq.get("topics", []) if t in TOPIC_Q and (known is None or t in known)), GENERAL)


# ---------------------------------------------------------------- the article's own photo
_META = re.compile(r"<meta\b[^>]*>", re.I)
_ATTR = re.compile(r"""([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')""")
_LOGOISH = re.compile(r"(logo|favicon|sprite|placeholder|default[-_]?(?:image|img|og|share|social)|og[-_]default|social[-_]default|"
                      r"share[-_]default|fallback|blank\.|spacer|1x1|pixel\.)", re.I)
_PREF = ("og:image:secure_url", "og:image", "og:image:url", "twitter:image", "twitter:image:src")


def page_image(url, timeout=7, limit=400_000):
    """The photo an article page shows when it is shared (its og:image), '' when it has none or cannot be read."""
    if not url or not url.startswith("http"):
        return ""
    try:
        with requests.get(url, headers=BROWSER, timeout=timeout, stream=True, allow_redirects=True) as r:
            if r.status_code >= 400 or "html" not in r.headers.get("Content-Type", "html").lower():
                return ""
            buf, size = [], 0
            for chunk in r.iter_content(16384):
                buf.append(chunk)
                size += len(chunk)
                if size >= limit or b"</head>" in chunk.lower():
                    break
            page = b"".join(buf).decode(r.encoding or "utf-8", "ignore")
            base = r.url
    except Exception:
        return ""
    head = page.split("</head>", 1)[0] if "</head>" in page else page
    found = {}
    for tag in _META.findall(head):
        at = {k.lower(): (a or b) for k, a, b in _ATTR.findall(tag)}
        key = (at.get("property") or at.get("name") or at.get("itemprop") or "").lower()
        if key in _PREF or key == "image":
            found.setdefault(key, at.get("content") or "")
    for key in _PREF + ("image",):
        u = _html.unescape(found.get(key) or "").strip()
        if not u:
            continue
        u = "https:" + u if u.startswith("//") else urljoin(base, u)
        if u.startswith("http://"):
            u = "https://" + u[7:]
        if u.startswith("https://") and not _LOGOISH.search(urlparse(u).path):
            return u
    return ""


# ---------------------------------------------------------------- Google News links -> the publisher's link
_GN_ID = re.compile(r"/(?:rss/)?articles/([^/?#]+)")
_GN = {"rest": 0.0}


def gn_decode(link, timeout=7):
    """The publisher's own link behind a news.google.com link ('' when it cannot be found)."""
    m = _GN_ID.search(urlparse(link or "").path)
    if not m or time.time() < _GN["rest"]:
        return ""
    gid = m.group(1)
    try:
        r = requests.get(f"https://news.google.com/rss/articles/{gid}", headers=BROWSER, timeout=timeout)
        if r.status_code == 429:
            _GN["rest"] = time.time() + 900
            return ""
        sg = re.search(r'data-n-a-sg="([^"]+)"', r.text)
        ts = re.search(r'data-n-a-ts="([^"]+)"', r.text)
        if not (sg and ts):
            return ""
        req = [[["Fbv4je", '["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,'
                           f'null,0,0,null,0],"{gid}",{ts.group(1)},"{sg.group(1)}"]', None, "generic"]]]
        r = requests.post("https://news.google.com/_/DotsSplashUi/data/batchexecute", timeout=timeout,
                          headers={**BROWSER, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
                          data=f"f.req={quote(json.dumps(req))}")
        if r.status_code == 429:
            _GN["rest"] = time.time() + 900
            return ""
        r.raise_for_status()
        rows = json.loads(r.text.split("\n\n")[1])
        for row in rows:
            if isinstance(row, list) and len(row) > 2 and isinstance(row[2], str) and "garturlres" in row[2]:
                real = json.loads(row[2])[1]
                return real if isinstance(real, str) and real.startswith("http") else ""
    except Exception:
        pass
    return ""


def find_images(stories, budget=60, workers=8):
    """{link: photo url} for the stories given (dicts with "link"), each looked up on its article page; Google News links
    are turned into the publisher's link first. Never raises; stops waiting after `budget` seconds."""
    def one(link):
        url = gn_decode(link) if "news.google.com" in link else link
        return link, page_image(url) if url else ""
    links = list(dict.fromkeys(s.get("link") or "" for s in stories if s.get("link")))
    if not links:
        return {}
    ex = ThreadPoolExecutor(max_workers=workers)
    futs = [ex.submit(one, u) for u in links]
    wait(futs, timeout=budget)
    ex.shutdown(wait=False, cancel_futures=True)
    out = {}
    for f in futs:
        if f.done() and not f.cancelled() and f.exception() is None:
            link, img = f.result()
            if img:
                out[link] = img
    return out


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "19.0"
