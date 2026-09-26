"""
newsbot.py - The news bot.

Every 3 minutes, in the background, it reads ~35 news feeds (Reuters, Bloomberg, WSJ, FT, CNBC, MarketWatch, AP,
Benzinga, Yahoo Finance, Nasdaq, Investing.com, Seeking Alpha, Fox Business, Business Insider, TheStreet, Fortune,
The New York Times, the Fed, the SEC, BLS, PR Newswire, GlobeNewswire, CoinDesk, Cointelegraph), keeps 4 days of
headlines in memory, merges the same story told by several outlets (the story remembers every outlet that carried it)
and finds the companies each story is about.

One bot is shared by every visitor (Streamlit cache_resource), so news pages open instantly and the list keeps growing
between visits. A feed that fails (blocked, down, slow) is skipped and retried on the next round; the News page shows
the status of every source.
"""
import html as _html
import re
import threading
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import pandas as pd
import requests
import streamlit as st

import universe as U

INTERVAL = 180            # seconds between two collection rounds
KEEP_HOURS = 96           # how long a headline stays in memory
MAX_ITEMS = 3000
TIMEOUT = 9               # per feed (seconds)
ROUND_BUDGET = 25         # a round never waits longer than this for slow feeds

BROWSER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
           "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5",
           "Accept-Language": "en-US,en;q=0.9", "Cache-Control": "no-cache"}
# government sites ask automated readers to say who they are
OFFICIAL = {**BROWSER, "User-Agent": "A.Alturaifi Pro news reader/1.0 (market headlines for a personal research site)"}


def gnews(q):
    """Google News search feed (the publisher of each item is read from its <source> tag)."""
    return f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=en-US&gl=US&ceid=US:en"


# (id, outlet, category, url)
FEEDS = [
    ("reuters", "Reuters", "markets", gnews("site:reuters.com (stocks OR markets OR economy OR earnings OR Fed) when:2d")),
    ("reuters_biz", "Reuters", "companies", gnews("site:reuters.com business when:1d")),
    ("bloomberg", "Bloomberg", "markets", "https://feeds.bloomberg.com/markets/news.rss"),
    ("bloomberg_eco", "Bloomberg", "economy", "https://feeds.bloomberg.com/economics/news.rss"),
    ("bloomberg_gn", "Bloomberg", "markets", gnews("site:bloomberg.com (stocks OR markets OR economy) when:1d")),
    ("wsj", "WSJ", "markets", "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"),
    ("wsj_biz", "WSJ", "companies", "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml"),
    ("wsj_gn", "WSJ", "markets", gnews("site:wsj.com (stocks OR markets OR economy OR earnings) when:2d")),
    ("ft", "Financial Times", "markets", "https://www.ft.com/markets?format=rss"),
    ("ft_us", "Financial Times", "economy", "https://www.ft.com/rss/home/us"),
    ("ft_gn", "Financial Times", "markets", gnews("site:ft.com (markets OR stocks OR economy OR companies) when:2d")),
    ("cnbc", "CNBC", "markets", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("cnbc_inv", "CNBC", "markets", "https://www.cnbc.com/id/15839069/device/rss/rss.html"),
    ("cnbc_eco", "CNBC", "economy", "https://www.cnbc.com/id/20910258/device/rss/rss.html"),
    ("cnbc_earn", "CNBC", "earnings", "https://www.cnbc.com/id/15839135/device/rss/rss.html"),
    ("marketwatch", "MarketWatch", "markets", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("ap", "AP", "economy", gnews("site:apnews.com (business OR economy OR stocks OR inflation) when:2d")),
    ("benzinga", "Benzinga", "markets", "https://www.benzinga.com/feed"),
    ("benzinga_gn", "Benzinga", "markets", gnews("site:benzinga.com when:1d")),
    ("yahoo", "Yahoo Finance", "markets", "https://finance.yahoo.com/news/rssindex"),
    ("nasdaq", "Nasdaq", "markets", "https://www.nasdaq.com/feed/rssoutbound?category=Markets"),
    ("nasdaq_st", "Nasdaq", "companies", "https://www.nasdaq.com/feed/rssoutbound?category=Stocks"),
    ("investing", "Investing.com", "markets", "https://www.investing.com/rss/news_25.rss"),
    ("investing_eco", "Investing.com", "economy", "https://www.investing.com/rss/news_14.rss"),
    ("seekingalpha", "Seeking Alpha", "markets", "https://seekingalpha.com/market_currents.xml"),
    ("foxbiz", "Fox Business", "markets", "https://moxie.foxbusiness.com/google-publisher/markets.xml"),
    ("foxbiz_eco", "Fox Business", "economy", "https://moxie.foxbusiness.com/google-publisher/economy.xml"),
    ("bi", "Business Insider", "markets", "https://markets.businessinsider.com/rss/news"),
    ("thestreet", "TheStreet", "markets", "https://www.thestreet.com/.rss/full/"),
    ("fortune", "Fortune", "companies", "https://fortune.com/feed/"),
    ("nyt", "New York Times", "economy", "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml"),
    ("fed", "Federal Reserve", "official", "https://www.federalreserve.gov/feeds/press_all.xml"),
    ("sec", "SEC", "official", "https://www.sec.gov/news/pressreleases.rss"),
    ("bls", "BLS", "official", "https://www.bls.gov/feed/news_release.rss"),
    ("prn", "PR Newswire", "press", "https://www.prnewswire.com/rss/financial-services-latest-news/earnings-list.rss"),
    ("gnw", "GlobeNewswire", "press", "https://www.globenewswire.com/RssFeed/subjectcode/13-Earnings%20Releases%20And%20Operating%20Results/"
                                      "feedTitle/GlobeNewswire%20-%20Earnings%20Releases%20And%20Operating%20Results"),
    ("coindesk", "CoinDesk", "crypto", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("cointelegraph", "Cointelegraph", "crypto", "https://cointelegraph.com/rss"),
]
FEED = {f[0]: f for f in FEEDS}
OUTLETS = list(dict.fromkeys(f[1] for f in FEEDS))
CATS = {"markets": ("Markets", "الأسواق", "show_chart"), "economy": ("Economy", "الاقتصاد", "public"),
        "companies": ("Companies", "الشركات", "domain"), "earnings": ("Earnings", "الأرباح", "request_quote"),
        "official": ("Official", "جهات رسمية", "account_balance"), "press": ("Press releases", "بيانات الشركات", "campaign"),
        "crypto": ("Crypto", "العملات الرقمية", "currency_bitcoin")}
# outlet rank when the same story comes from several places (the best outlet becomes the main link)
RANK = {o: i for i, o in enumerate(["Reuters", "Bloomberg", "WSJ", "Financial Times", "AP", "CNBC", "MarketWatch", "Federal Reserve", "BLS", "SEC",
                                    "New York Times", "Barron's", "Benzinga", "Yahoo Finance", "Nasdaq", "Investing.com", "Fox Business",
                                    "Business Insider", "Fortune", "TheStreet", "Seeking Alpha", "CoinDesk", "Cointelegraph", "PR Newswire",
                                    "GlobeNewswire"])}
# Google News publisher names -> our outlet names
ALIAS = {"the wall street journal": "WSJ", "wsj": "WSJ", "financial times": "Financial Times", "ft.com": "Financial Times", "reuters": "Reuters",
         "bloomberg": "Bloomberg", "bloomberg.com": "Bloomberg", "associated press": "AP", "ap news": "AP", "the associated press": "AP",
         "benzinga": "Benzinga", "cnbc": "CNBC", "marketwatch": "MarketWatch", "barron's": "Barron's", "barrons": "Barron's",
         "yahoo finance": "Yahoo Finance", "the new york times": "New York Times", "nasdaq": "Nasdaq"}

# not market news: personal-finance rate tables, price-prediction spam, sports and celebrity items
NOISE = re.compile(r"\b(cd rates?|savings (?:account )?rates?|mortgage (?:and refinance )?rates? today|best (?:high-yield )?savings|credit cards? (?:of|for)|"
                   r"horoscope|price prediction|sweepstakes|promo code|coupon|grand prix|nfl|nba|mlb|nhl|wwe|aew|super bowl|recipe)\b", re.I)
_TAG = re.compile(r"<[^>]+>")
_IMG = re.compile(r"""<img[^>]+?src=["']([^"']+)["']""", re.I)
_WS = re.compile(r"\s+")
_EXCH = re.compile(r"\((?:NYSE(?:\s*American)?|NASDAQ|Nasdaq|NasdaqGS|NasdaqGM|NasdaqCM|AMEX|NYSEAMERICAN|NYSE MKT|CBOE|OTCQX|OTCQB|OTC)\s*:\s*([A-Z]{1,5}(?:\.[A-Z])?)\)")
_BAD_XML = re.compile(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_ENT_FIX = re.compile(rb"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)")
STOP = set("a an the and or of to in on for with at by from as is are be was were has have had after before over under into amid says said "
           "will would its it this that new more than up down us its their his her they you your why how what who when report reports".split())


# ---------------------------------------------------------------- parsing (RSS 2.0, RSS 1.0 / RDF, Atom)
def clean(s):
    return _WS.sub(" ", _html.unescape(_TAG.sub(" ", s or ""))).strip()


def parse_time(s):
    s = (s or "").strip()
    if not s:
        return None
    ts = None
    try:
        ts = pd.Timestamp(parsedate_to_datetime(s))
    except Exception:
        try:
            ts = pd.to_datetime(s, utc=True)
        except Exception:
            return None
    if ts is None or pd.isna(ts):
        return None
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def _local(tag):
    return tag.rsplit("}", 1)[-1].lower() if isinstance(tag, str) else ""


def _root(content):
    if isinstance(content, str):
        content = content.encode("utf-8", "ignore")
    try:
        return ET.fromstring(content)
    except ET.ParseError:
        pass
    try:                                           # stray control characters or HTML entities (&nbsp;) inside the XML
        return ET.fromstring(_ENT_FIX.sub(b"&amp;", _BAD_XML.sub(b"", content)))
    except ET.ParseError:
        return None


def parse_feed(content):
    """-> [{"title", "link", "time", "summary", "source", "img", "tickers"}]"""
    root = _root(content)
    if root is None:
        return []
    out = []
    for el in root.iter():
        if _local(el.tag) not in ("item", "entry"):
            continue
        d = {"title": "", "link": "", "time": None, "summary": "", "source": "", "img": "", "tickers": []}
        for ch in el:
            n = _local(ch.tag)
            txt = (ch.text or "").strip()
            if n == "title":
                d["title"] = clean("".join(ch.itertext()) or txt)
            elif n == "link":
                href = ch.get("href")
                if href:
                    if ch.get("rel") in (None, "alternate") and not d["link"]:
                        d["link"] = href
                elif txt and not d["link"]:
                    d["link"] = txt
            elif n in ("pubdate", "published", "updated", "date", "issued", "modified"):
                d["time"] = d["time"] or parse_time(txt)
            elif n in ("content", "thumbnail") and ch.get("url"):
                if (ch.get("medium") or "image") == "image" and not str(ch.get("type") or "image").startswith(("video", "audio")):
                    d["img"] = d["img"] or ch.get("url")
            elif n in ("description", "summary", "content", "encoded"):
                raw_html = "".join(ch.itertext()) or txt
                if not d["img"]:
                    m = _IMG.search(raw_html)
                    if m:
                        d["img"] = _html.unescape(m.group(1))
                if not d["summary"]:
                    d["summary"] = clean(raw_html)
            elif n == "group":                                  # <media:group><media:content url=...>
                for g in ch:
                    if _local(g.tag) in ("content", "thumbnail") and g.get("url") and not d["img"]:
                        if (g.get("medium") or "image") == "image" and not str(g.get("type") or "image").startswith("video"):
                            d["img"] = g.get("url")
            elif n == "enclosure" and (ch.get("type") or "").startswith("image"):
                d["img"] = d["img"] or ch.get("url") or ""
            elif n == "source":
                d["source"] = clean(txt)
            elif n in ("tickers", "ticker", "symbols", "stock"):
                d["tickers"] += [t.strip().upper() for t in re.split(r"[,\s;]+", txt) if re.fullmatch(r"[A-Za-z]{1,5}(?:\.[A-Za-z])?", t.strip())]
            elif n == "category" and re.search(r"symbol|ticker|stock", " ".join(str(v) for v in ch.attrib.values()), re.I):
                if re.fullmatch(r"[A-Z]{1,5}(?:\.[A-Z])?", txt):
                    d["tickers"].append(txt)
            elif n == "guid" and not d["link"] and txt.startswith("http"):
                d["link"] = txt
        if d["title"] and d["link"].startswith("http"):
            out.append(d)
    return out


# ---------------------------------------------------------------- one headline
def _outlet(raw_source, feed_outlet):
    s = (raw_source or "").strip()
    return ALIAS.get(s.lower(), s) if s else feed_outlet


def tickers_in(text, extra=()):
    found = [t for t in extra if t]
    found += [m.group(1).replace(".", "-") for m in _EXCH.finditer(text or "")]
    found += U.detect_tickers(text or "")
    return [s for s in dict.fromkeys(found) if s and "^" not in s and "=" not in s][:6]


def build(raw, feed, now=None):
    fid, outlet, cat, url = feed
    gn = "news.google.com" in url
    src = _outlet(raw.get("source"), outlet) if gn else outlet
    title = raw["title"]
    for suffix in {raw.get("source") or "", src}:           # Google News titles end with " - Publisher"
        if suffix and title.endswith(f" - {suffix}"):
            title = title[: -len(suffix) - 3].rstrip()
    summary = "" if gn else raw.get("summary") or ""
    if summary[:60].lower() == title[:60].lower():
        summary = ""
    ts = raw.get("time")
    now = now or pd.Timestamp.now(tz="UTC")
    if ts is None or pd.isna(ts):
        ts = now
    elif ts > now + pd.Timedelta(minutes=30):                    # a feed with a wrong clock
        ts = now
    # companies are looked up later, only for headlines that turn out to be new (saves work on every round)
    return {"title": title, "link": raw["link"], "source": src, "time": ts, "summary": summary[:700],
            "tickers": list(raw.get("tickers") or []), "_text": title + " · " + summary[:400], "cat": cat, "feed": fid,
            "img": raw.get("img") or "", "also": []}


def key_of(title):
    return " ".join(re.findall(r"[a-z0-9]+", (title or "").lower()))[:180]


def tokens(title):
    return frozenset(w for w in re.findall(r"[a-z0-9$%]+", (title or "").lower()) if len(w) > 2 and w not in STOP)


# ---------------------------------------------------------------- the bot
class NewsBot:
    def __init__(self, feeds=FEEDS):
        self.feeds = list(feeds)
        self.lock = threading.RLock()
        self.running = threading.Lock()
        self.first = threading.Event()
        self.store = {}           # key -> item
        self.index = {}           # token -> set(keys)   (finds the same story told with other words)
        self.status = {}          # feed id -> {"ok", "n", "new", "ms", "err", "at"}
        self.updated = None       # time of the last finished round
        self.rounds = 0
        self.thread = None
        self.build = BUILD
        self.stopped = False

    # ---- one feed
    def fetch(self, feed):
        fid, outlet, cat, url = feed
        t0 = time.time()
        try:
            hdr = OFFICIAL if cat == "official" else BROWSER
            r = requests.get(url, headers=hdr, timeout=TIMEOUT)
            ms = int((time.time() - t0) * 1000)
            code = getattr(r, "status_code", 0)
            if code != 200:
                return fid, [], {"ok": False, "err": f"HTTP {code}", "ms": ms}
            raw = parse_feed(r.content)
            if not raw:
                return fid, [], {"ok": False, "err": "no headlines (not a feed)", "ms": ms}
            now = pd.Timestamp.now(tz="UTC")
            items = [build(x, feed, now) for x in raw]
            return fid, items, {"ok": True, "n": len(items), "ms": ms}
        except requests.exceptions.Timeout:
            return fid, [], {"ok": False, "err": "timeout", "ms": int((time.time() - t0) * 1000)}
        except Exception as e:
            return fid, [], {"ok": False, "err": type(e).__name__, "ms": int((time.time() - t0) * 1000)}

    # ---- merging
    def _similar(self, it):
        tk = tokens(it["title"])
        if len(tk) < 4:
            return None
        cnt = {}
        for t in tk:
            for k in self.index.get(t, ()):
                cnt[k] = cnt.get(k, 0) + 1
        best, best_j = None, 0.0
        for k, c in cnt.items():
            if c < 3:
                continue
            other = self.store.get(k)
            if other is None:
                continue
            j = c / len(tk | other["_tk"])
            if j > best_j and abs((other["time"] - it["time"]).total_seconds()) < 36 * 3600:
                best, best_j = k, j
        return best if best_j >= 0.6 else None

    def _add(self, it):
        """True when the headline is new (not the same story as one already stored)."""
        if NOISE.search(it["title"]):
            return False
        k = key_of(it["title"])
        if not k:
            return False
        hit = k if k in self.store else self._similar(it)
        text = it.pop("_text", it["title"])
        if hit is None:
            it["tickers"] = tickers_in(text, it["tickers"])
            it["_tk"] = tokens(it["title"])
            it["_key"] = k
            self.store[k] = it
            for t in it["_tk"]:
                self.index.setdefault(t, set()).add(k)
            return True
        cur = self.store[hit]
        if it["source"] == cur["source"] or it["source"] in cur["also"]:
            return False
        if RANK.get(it["source"], 99) < RANK.get(cur["source"], 99):        # a better outlet becomes the main link
            cur["also"] = [cur["source"]] + [s for s in cur["also"] if s != it["source"]]
            for f in ("title", "link", "source", "summary", "feed"):
                cur[f] = it[f] or cur[f]
        else:
            cur["also"].append(it["source"])
        cur["time"] = min(cur["time"], it["time"])
        cur["tickers"] = list(dict.fromkeys(cur["tickers"] + it["tickers"]))[:6]
        if not cur.get("img") and it.get("img"):
            cur["img"] = it["img"]
        return False

    def _prune(self):
        cut = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=KEEP_HOURS)
        drop = [k for k, v in self.store.items() if v["time"] < cut]
        if len(self.store) - len(drop) > MAX_ITEMS:
            keep = sorted((v["time"], k) for k, v in self.store.items() if v["time"] >= cut)
            drop += [k for _, k in keep[: len(keep) - MAX_ITEMS]]
        for k in drop:
            it = self.store.pop(k, None)
            for t in (it or {}).get("_tk", ()):
                s = self.index.get(t)
                if s:
                    s.discard(k)
                    if not s:
                        self.index.pop(t, None)

    # ---- one round over the feeds that are due
    def _due(self, feed, now):
        """Google News and official sites are read every 10 minutes, the rest every round; a failing feed waits longer each time."""
        st_ = self.status.get(feed[0])
        if not st_:
            return True
        base = 600 if ("news.google.com" in feed[3] or feed[2] == "official") else INTERVAL
        wait = base * min(5, 1 + st_.get("fails", 0)) if not st_.get("ok") else base
        return now - st_.get("at", 0) >= wait - 5

    def collect(self, force=False):
        if not self.running.acquire(blocking=False):      # a round is already running
            return
        try:
            results = []
            t_now = time.time()
            todo = [f for f in self.feeds if force or self._due(f, t_now)]
            ex = ThreadPoolExecutor(max_workers=16)
            futs = [ex.submit(self.fetch, f) for f in todo]
            try:
                for fu in as_completed(futs, timeout=ROUND_BUDGET):
                    results.append(fu.result())
            except Exception:                              # the slowest feeds are dropped from this round
                pass
            ex.shutdown(wait=False)
            done = {r[0] for r in results}
            now = time.time()
            with self.lock:
                for fid, items, st_ in results:
                    items.sort(key=lambda x: x["time"])
                    st_["new"] = sum(1 for it in items if self._add(it))
                    st_["at"] = now
                    st_["fails"] = 0 if st_["ok"] else self.status.get(fid, {}).get("fails", 0) + 1
                    self.status[fid] = st_
                for f in todo:
                    if f[0] not in done:
                        self.status[f[0]] = {"ok": False, "err": "timeout", "ms": ROUND_BUDGET * 1000, "at": now, "new": 0,
                                             "fails": self.status.get(f[0], {}).get("fails", 0) + 1}
                self._prune()
                self.updated = now
                self.rounds += 1
        finally:
            self.running.release()
            self.first.set()

    def _loop(self):
        while not self.stopped:
            try:
                self.collect()
            except Exception:
                self.first.set()
            time.sleep(INTERVAL)

    def start(self):
        if self.stopped:
            return
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._loop, name="news-bot", daemon=True)
            self.thread.start()

    # ---- reading
    def items(self, hours=None):
        """Copies of the stored headlines, newest first."""
        with self.lock:
            vals = list(self.store.values())
        if hours:
            cut = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=hours)
            vals = [v for v in vals if v["time"] >= cut]
        out = [{k: (list(v) if isinstance(v, list) else v) for k, v in it.items() if not k.startswith("_")} for it in vals]
        out.sort(key=lambda n: n["time"], reverse=True)
        return out

    def health(self):
        """One row per outlet: working feeds, headlines now in memory, speed, last error."""
        with self.lock:
            st_ = dict(self.status)
            in_mem = {}
            for v in self.store.values():
                for s in [v["source"]] + v["also"]:
                    in_mem[s] = in_mem.get(s, 0) + 1
        rows = {}
        for fid, outlet, cat, url in self.feeds:
            s = st_.get(fid)
            r = rows.setdefault(outlet, {"outlet": outlet, "feeds": 0, "ok": 0, "ms": [], "err": "", "items": in_mem.get(outlet, 0)})
            r["feeds"] += 1
            if s:
                if s.get("ok"):
                    r["ok"] += 1
                    r["ms"].append(s.get("ms", 0))
                elif not r["err"]:
                    r["err"] = s.get("err", "")
        out = []
        for r in rows.values():
            r["ms"] = int(sum(r["ms"]) / len(r["ms"])) if r["ms"] else None
            out.append(r)
        out.sort(key=lambda r: (-(r["ok"] > 0), -r["items"], r["outlet"]))
        return out


@st.cache_resource(show_spinner=False)
def _shared_bot():
    b = NewsBot()
    b.start()                  # first round starts at once, in the background
    return b


def bot(wait=True, timeout=14):
    """The shared bot. wait=True: the very first time, wait (a few seconds) for its first round."""
    b = _shared_bot()
    if getattr(b, "build", None) != BUILD:        # a bot from an older version of the site: retire it, start the new one
        try:
            b.stopped = True
            _shared_bot.clear()
        except Exception:
            pass
        b = _shared_bot()
    b.start()                  # restarts the loop if it ever stopped
    if b.updated and time.time() - b.updated > 3 * INTERVAL:
        threading.Thread(target=b.collect, daemon=True).start()   # the loop looks stuck: refresh now, in the background
    if wait and not b.first.is_set():
        b.first.wait(timeout)
    return b


def headlines(hours=48):
    try:
        return bot().items(hours)
    except Exception:
        return []

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.5"
