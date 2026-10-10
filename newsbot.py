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
OFFICIAL = {**BROWSER, "User-Agent": "TURA Pro news reader/1.0 (market headlines for a personal research site)"}


def gnews(q):
    """Google News search feed (the publisher of each item is read from its <source> tag)."""
    return f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=en-US&gl=US&ceid=US:en"


def gnews_ar(q):
    """Google News search feed in Arabic, Saudi edition."""
    return f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=ar&gl=SA&ceid=SA:ar"


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

# the Saudi market's feeds (Arabic and English), read by a bot of their own (sa_bot)
SA_FEEDS = [
    ("sa_market", "Saudi market", "markets", gnews_ar("(السوق السعودية OR الأسهم السعودية OR تاسي) when:2d")),
    ("sa_tadawul", "Saudi market", "markets", gnews_ar("(تداول السعودية OR مؤشر السوق الرئيسية) when:2d")),
    ("sa_argaam", "أرقام", "markets", gnews_ar("site:argaam.com when:2d")),
    ("sa_aleqt", "الاقتصادية", "markets", gnews_ar("site:aleqt.com (أسهم OR السوق OR أرباح OR شركة) when:2d")),
    ("sa_maaal", "مال", "markets", gnews_ar("site:maaal.com when:2d")),
    ("sa_asharq", "الشرق بلومبرغ", "markets", gnews_ar("site:asharqbusiness.com السعودية when:2d")),
    ("sa_cnbcar", "CNBC عربية", "markets", gnews_ar("site:cnbcarabia.com السعودية when:2d")),
    ("sa_alarabiya", "العربية Business", "markets", gnews_ar("site:alarabiya.net (أسهم OR السوق السعودية OR أرامكو) when:2d")),
    ("sa_results", "Saudi market", "earnings", gnews_ar("(نتائج OR أرباح OR توزيعات) (شركة OR بنك) السعودية when:3d")),
    ("sa_economy", "Saudi market", "economy", gnews_ar("(الاقتصاد السعودي OR البنك المركزي السعودي OR التضخم في السعودية) when:3d")),
    ("sa_oil", "Saudi market", "economy", gnews_ar("(أسعار النفط OR أوبك) when:2d")),
    ("sa_en_market", "Saudi market", "markets", gnews("(Saudi stocks OR Tadawul OR TASI OR \"Saudi Exchange\") when:3d")),
    ("sa_en_argaam", "Argaam", "markets", gnews("site:argaam.com when:3d")),
    ("sa_en_arabnews", "Arab News", "markets", gnews("site:arabnews.com (business OR economy) Saudi when:3d")),
    ("sa_en_reuters", "Reuters", "markets", gnews("site:reuters.com Saudi (stocks OR economy OR Aramco OR banks) when:3d")),
    ("sa_en_bloomberg", "Bloomberg", "markets", gnews("site:bloomberg.com Saudi when:3d")),
    ("sa_en_aramco", "Saudi market", "companies", gnews("(Aramco OR SABIC OR \"Al Rajhi\" OR Maaden OR ACWA) when:3d")),
]
SA_OUTLETS = list(dict.fromkeys(f[1] for f in SA_FEEDS))
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
# pages that are not news (a quote page "NFLX مقابل USD", a company's page "BAAN 3 | 1820 | TADAWUL | TASI", "TAQA - Disclosures"),
# sport (a golf tournament named after Aramco) and outlets that cover another market
JUNK = re.compile(r"(مقابل USD\s*$|\|\s*TADAWUL\s*\|\s*TASI|TADAWUL:\d{4}\s*$|%[0-9A-F]{2}%[0-9A-F]{2}|^\s*[\w&.\- ]{2,30} - (?:Disclosures|Latest News|"
                  r"Announcements|Financials?|Profile|Overview)\s*$|^\s*(?:Calendar|Home|Markets?)\s*$|\b(?:golf|lpga|pga tour|ladies european tour|"
                  r"championship|tournament|grand prix|world cup|premier league|(?:day \w+|round \d|match|game|race) highlights)\b|"
                  r"[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]|مقابل الجنيه|السوق المصري|البنوك المصرية|السوق السوداء|"
                  # shopping deals, profile pages, law-firm adverts, call transcripts and automatic "stocks moving" lists
                  r"\bis selling an? .{3,80} for (?:only |just )?\$[\d,.]+|: profile and biography\b|\binvestor counsel\b|\bclass action lawsuit\b|"
                  r"\b(?:final )?deadline(?: alert)?:|\bshareholder alert\b|\bearnings call(?::)? (?:complete )?transcript\b|^full transcript:|"
                  r"\b\d+ [\w ]{0,40}stocks (?:moving|with whale alerts)\b|"
                  # a data feed's test rows, company pages and forum threads, daily gold-and-riyal price posts, Bengali video titles
                  r"^test data\b|معلومات وتحديثات|مناقشات السوق|عيار 2[14]|سعر الريال السعودي اليوم|سعر الذهب في السعودية|[\u0980-\u09ff]|"
                  r"^\W*\w+\W+\w+\W*$|^middle east economy$)", re.I)
BLOCKED = {"vietnam.vn", "sky sports", "yahoo sports", "ladies european tour", "www.golfpost.com", "golfpost", "스타뉴스", "espn",
           "golf channel", "golf digest"}
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
# outlet names as Google News sends them -> the short name readers know
_OUTLET_RX = [(re.compile(p, re.I), name) for p, name in (
    (r"^(?:ارقام|أرقام)\b", "أرقام"), (r"^argaam", "Argaam"), (r"^(?:https?://)?(?:www\.)?marketscreener", "MarketScreener"),
    (r"^(?:https?://)?(?:www\.)?alsaudi\.news", "السعودي نيوز"), (r"^(?:https?://)?(?:www\.)?([\w-]+)\.(?:com|net|org|news|sa)/?$", None))]


def _outlet(raw_source, feed_outlet):
    s = (raw_source or "").strip()
    if not s:
        return feed_outlet
    for rx, name in _OUTLET_RX:
        m = rx.search(s)
        if m:
            s = name or m.group(1).replace("-", " ").title()
            break
    return ALIAS.get(s.lower(), s)


def subject_tickers(detect, text, lead=180, most=2):
    """The companies a story is about, not the ones it mentions in passing: the companies named in the headline; when the
    headline names none, the ones named at the start of the summary - and only when they are one or two (a summary listing
    Amazon, Google and Broadcom as examples is background, not the subject)."""
    title, _, summ = str(text or "").partition(" · ")
    t_ = detect(title)
    if t_:
        return t_
    s_ = detect(summ[:lead]) if summ else []
    return s_ if len(s_) <= most else []


def tickers_in(text, extra=()):
    title = str(text or "").partition(" · ")[0]
    found = [t for t in extra if t]
    if len(found) > 2 and not U.detect_tickers(title) and not _EXCH.search(title):
        found = []        # a market round-up ("Stocks settle higher on earnings optimism"): the feed lists the day's movers, the
                          # story is about the market, not about Apple or Verizon
    found += [m.group(1).replace(".", "-") for m in _EXCH.finditer(text or "")]      # "(NASDAQ: QNCX)": the company itself
    found += subject_tickers(U.detect_tickers, text)
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
    return " ".join(re.findall(r"[^\W_]+", (title or "").lower()))[:180]      # letters and digits of any script (Arabic too)


def tokens(title):
    return frozenset(w for w in re.findall(r"(?:[^\W_]|[$%])+", (title or "").lower()) if len(w) > 2 and w not in STOP)


# ---------------------------------------------------------------- one story told by several outlets ("full coverage")
# the bot itself merges a headline repeated almost word for word; the pages also group the same event told in different words
# ("White House forms committee to probe Fed's Cook", "Can Trump fire Fed governor Lisa Cook?") into one card with its coverage
_SERIES = re.compile(r"^(?:(?:stock market today,?\s*\w{3,9}\.?\s*\d{1,2}\s*[:\-]|world economy latest:|morning bid:|closing bell:|exclusive[:\-|]|"
                     r"breaking:|update \d+[:\-]|analysis[:\-]|factbox[:\-]|explainer[:\-]|wall st\.? week ahead[:\-]?|instant view:|live:|"
                     r"commentary:|opinion:|firstft:)\s*)+", re.I)
_SERIES_END = re.compile(r"\s*(?:\|\s*closing bell|-\s*live updates?|\|\s*live)\s*$", re.I)
_SAME = [(re.compile(p, re.I), r) for p, r in ((r"federal reserve", "fed"), (r"\bu\.s\.", "us"), (r"\bwall st\b", "wall street"),
                                             (r"\bs&p 500\b", "spx"), (r"\bnasdaq composite\b", "nasdaq"))]
CL_STOP = STOP | set("stock stocks share shares market markets investors traders could may might just now still says say week weeks "
                     "today day days year years month amid ahead latest big after first next last time about against while back "
                     "higher lower rise rises rose fall falls fell gains gain loses lose slips slip jumps jump surges surge "
                     "wall street monday tuesday wednesday thursday friday saturday sunday january february march april june july "
                     "august september october november december transcript complete full call session intraday premarket pre-market "
                     "after-hours moving falling rising trading futures settle modestly steady steadie price prices q1 q2 q3 q4 "
                     "here what's whats know best right buy sell can hit hits top worth invested much funding round valuation "
                     "billion million trillion percent record low high near report reuters bloomberg benzinga exclusive commentary "
                     "update analysis backed seek seeks one two three four five six seven eight nine ten company companies firm "
                     "group shares fiscal financial result results quarter half announces announce earning earnings revenue revenues "
                     "profit reveal reveals filing filings plan plans".split()) | set(
    # the Arabic headlines' everyday words (a profit story about Extra is not a profit story about Samsung)
    "في من إلى الى على عن مع عند بعد قبل خلال حتى منذ بين نحو أن إن كان كانت التي الذي هذا هذه ذلك تلك ما لا لم لن قد كما أو ثم "
    "بسبب وسط رغم اليوم أمس السبت الأحد الإثنين الاثنين الثلاثاء الأربعاء الخميس الجمعة يناير فبراير مارس أبريل مايو يونيو يوليو "
    "أغسطس سبتمبر أكتوبر نوفمبر ديسمبر الربع الأول الثاني الثالث الرابع النصف العام السنة أرباح الأرباح ارتفاع تراجع انخفاض يرتفع "
    "ترتفع يتراجع تتراجع ينخفض تنخفض تقفز يقفز صعود هبوط مليون مليار ريال ريالا ريالات دولار دولارا السعودية السعودي سعر أسعار سوق "
    "السوق الأسهم أسهم شركة الشركة خبر أخبار عاجل مستوى أعلى أدنى نسبة بنسبة تسجل يسجل تحقق يحقق مؤشر المؤشر يغلق تغلق إغلاق "
    "منخفضا منخفضًا مرتفعا مرتفعًا مكاسب خسائر أسبوعية أسبوعي الأسبوع للأسبوع التوالي middle east".split())


_CL_STOP = set()                 # CL_STOP and its stems (filled below, once _stem exists)
# words that tell the same thing
_SYN = {w: k for k, ws in {"probe": "investigate investigation inquiry probing", "acquire": "acquisition takeover buyout",
                           "tariff": "duty duties levy levies", "layoff": "job-cuts", "plunge": "tumble sink sank slump crash",
                           "soar": "surge jump skyrocket", "approve": "approval approved clear clears", "ceo": "chief-executive",
                           "lawsuit": "sue sued suing"}.items() for w in ws.split()}


def _stem(w):
    """A light stem: probes -> probe, launches -> launch, companies -> company, futures -> future."""
    w = w[:-2] if w.endswith("'s") else w
    if len(w) > 4:
        if w.endswith("ies"):
            return w[:-3] + "y"
        if w.endswith(("ches", "shes", "sses", "xes", "zes")):
            return w[:-2]
        if w.endswith("s") and not w.endswith(("ss", "us", "is")):
            return w[:-1]
    return w


def _cl_tokens(title):
    t = _SERIES_END.sub("", _SERIES.sub("", str(title or "")))
    for rx, rep in _SAME:
        t = rx.sub(rep, t)
    out = set()
    for w in re.findall(r"[^\W_]+(?:'s)?", t.lower()):
        w = _SYN.get(_stem(w), _stem(w))
        if len(w) > 2 and w not in _CL_STOP and not w.isdigit():
            out.add(w)
    return out


def _cl_time(n):
    ts = n.get("time")
    return ts if ts is not None and pd.notna(ts) else None


def _cl_join(groups, items, idf, rare, hours):
    """Second pass: two groups (or a story and a group) that tell the same event in different words - the first pass compares
    one headline with another, so "Trump strikes deal with Putin to get diesel" can miss each single telling of the diesel deal
    yet share most of its rare words with all of them together - are joined."""
    from collections import Counter
    words = [set().union(*G["t"]) if G["t"] else set() for G in groups]
    ticks = [frozenset().union(*G["k"]) if G["k"] else frozenset() for G in groups]
    when = []
    for G in groups:
        ts = [_cl_time(items[i]) for i in G["m"] if _cl_time(items[i]) is not None]
        when.append((min(ts), max(ts)) if ts else None)
    rare_w = [{w for w in W if idf.get(w, 0) >= rare} for W in words]
    weight = [sum(idf.get(w, 0) for w in W) for W in words]
    inv = {}
    for g, R in enumerate(rare_w):
        for w in R:
            inv.setdefault(w, []).append(g)
    parent = list(range(len(groups)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    span = hours * 3600
    for g, R in enumerate(rare_w):
        if not R:
            continue
        for h, c in Counter(h for w in R for h in inv[w] if h > g).items():
            if c < 3 or find(g) == find(h):
                continue
            if ticks[g] and ticks[h] and not (ticks[g] & ticks[h]):
                continue
            a, b = when[g], when[h]
            if a and b and max(abs((a[0] - b[1]).total_seconds()), abs((b[0] - a[1]).total_seconds())) > span * 1.5:
                continue
            ws = sum(idf[w] for w in words[g] & words[h])
            if ws / max(min(weight[g], weight[h]), 1e-9) >= 0.5:
                parent[find(h)] = find(g)
    if all(find(g) == g for g in range(len(groups))):
        return groups
    out = {}
    for g, G in enumerate(groups):
        r = find(g)
        M = out.setdefault(r, {"m": [], "t": [], "k": [], "ts": G.get("ts")})
        M["m"] += G["m"]
        M["t"] += G["t"]
        M["k"] += G["k"]
    return [out[r] for r in sorted(out, key=lambda r: min(out[r]["m"]))]


_CL_STOP = CL_STOP | {_stem(w) for w in CL_STOP}
_CL_MEMO = {}


def cluster(items, hours=30, rank=None):
    """_cluster() remembered for the same list of stories (a page runs again on every click): fresh copies each time."""
    if rank is not None:
        return _cluster(items, hours, rank)
    key = (hours, len(items), hash(tuple((n.get("link"), n.get("title")) for n in items)))
    hit = _CL_MEMO.get(key)
    if hit is None:
        hit = _cluster(items, hours)
        if len(_CL_MEMO) > 6:
            _CL_MEMO.pop(next(iter(_CL_MEMO)))
        _CL_MEMO[key] = hit
    return [{k: v for k, v in n.items() if k != "iq"} for n in hit]


def _cluster(items, hours=30, rank=None):
    """[lead story, ...]: the same event told by several outlets grouped under its best outlet's story. The lead gets "more"
    (the other stories: title, source, link, time, newest first), its "also" lists every other outlet and its companies are
    pooled. Order: the order of each group's first story in items. rank(n) -> sort key for the lead (default: the outlet's
    rank, then the newest)."""
    import math
    items = [n for n in items if n.get("title")]
    if len(items) < 2:
        return [dict(n) for n in items]
    toks = [_cl_tokens(n["title"]) for n in items]
    tick = [frozenset(n.get("tickers") or ()) for n in items]
    df = {}
    for tk in toks:
        for w in tk:
            df[w] = df.get(w, 0) + 1
    N = len(items)
    idf = {w: math.log((N + 1) / (c + 0.5)) for w, c in df.items()}
    rare = math.log((N + 1) / (max(3.0, N * 0.02) + 0.5))      # a word found in under 2% of the headlines (or in three)
    groups, index = [], {}                                      # [{"m": member indexes, "t": their words, "ts": first time}]
    for i, n in enumerate(items):
        tk, ts = toks[i], _cl_time(n)
        cand = {g for w in tk if idf.get(w, 0) >= rare for g in index.get(w, ())}
        best, best_s = None, 0.0
        for g in cand:
            G = groups[g]
            if ts is not None and G["ts"] is not None and abs((G["ts"] - ts).total_seconds()) > hours * 3600:
                continue
            for o, ok_ in zip(G["t"], G["k"]):
                if tick[i] and ok_ and not (tick[i] & ok_):
                    continue                  # two different companies ("Why is Arm stock falling", "Why is AST stock falling")
                sh = tk & o
                if len(sh) < 2:
                    continue
                ws = sum(idf[w] for w in sh)
                wj = ws / sum(idf[w] for w in tk | o)
                ov = ws / min(sum(idf[w] for w in tk), sum(idf[w] for w in o))
                n_rare = sum(1 for w in sh if idf[w] >= rare)
                s_ = wj if (wj >= 0.30 and n_rare >= 2) else (ov * 0.7 if ov >= 0.58 and n_rare >= 2 else 0.0)
                if s_ > best_s:
                    best, best_s = g, s_
        if best is None:
            best = len(groups)
            groups.append({"m": [], "t": [], "k": [], "ts": ts})
        G = groups[best]
        G["m"].append(i)
        G["t"].append(tk)
        G["k"].append(tick[i])
        for w in tk:
            if idf.get(w, 0) >= rare:
                index.setdefault(w, set()).add(best)
    groups = _cl_join(groups, items, idf, rare, hours)
    key = rank or (lambda n: (RANK.get(n.get("source"), 99), -(_cl_time(n).value if _cl_time(n) is not None else 0)))
    zero = pd.Timestamp(0, tz="UTC")
    out = []
    for G in groups:
        mem = [items[i] for i in G["m"]]
        top = min(mem, key=key)
        lead = dict(top)
        rest = [m for m in mem if m is not top and m.get("link") != top.get("link")]
        if rest:
            outlets = [top.get("source")] + list(top.get("also") or [])
            for m in rest:
                outlets += [m.get("source")] + list(m.get("also") or [])
            lead["also"] = [o for o in dict.fromkeys(outlets) if o and o != top.get("source")]
            lead["more"] = [{"title": m["title"], "source": m.get("source"), "link": m.get("link"), "time": m.get("time")}
                            for m in sorted(rest, key=lambda m: _cl_time(m) or zero, reverse=True)]
            lead["tickers"] = list(dict.fromkeys(list(top.get("tickers") or []) + [t for m in rest for t in m.get("tickers") or []]))[:6]
            if not lead.get("img"):
                lead["img"] = next((m["img"] for m in rest if m.get("img")), "")
            lead.pop("iq", None)                  # its importance is read again with its full coverage
        out.append(lead)
    return out


# ---------------------------------------------------------------- the bot
class NewsBot:
    def __init__(self, feeds=FEEDS, finder=None):
        """finder(text, tickers) -> the companies a headline is about (default: the US market's tickers_in)."""
        self.feeds = list(feeds)
        self.finder = finder or tickers_in
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
        if NOISE.search(it["title"]) or JUNK.search(it["title"]) or str(it.get("source") or "").strip().lower() in BLOCKED:
            return False
        k = key_of(it["title"])
        if not k:
            return False
        hit = k if k in self.store else self._similar(it)
        text = it.pop("_text", it["title"])
        if hit is None:
            it["tickers"] = self.finder(text, it["tickers"])
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
            ex.shutdown(wait=False, cancel_futures=True)   # feeds not started yet are dropped, not left running
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
            self._side()
            time.sleep(INTERVAL)

    def _side(self):
        """The Arabic titles and the pictures are prepared beside the collector (one such thread at a time), so they never
        delay the next round of headlines."""
        t = getattr(self, "_side_t", None)
        if t is not None and t.is_alive():
            return
        def run():
            self._warm()
            self._pics()
        self._side_t = threading.Thread(target=run, daemon=True, name="news-side")
        self._side_t.start()

    def _pics(self, limit=80, budget=60):
        """Stories whose feed sent no picture get the photo of their own article page (newspics.find_images), newest first,
        each story tried at most twice; then the topic photos are looked up if they are missing or a week old."""
        try:
            import newspics
        except Exception:
            return
        try:
            cut = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=48)
            with self.lock:
                todo = sorted((v for v in self.store.values() if not v.get("img") and v.get("_pic", 0) < 2 and v["time"] >= cut),
                              key=lambda v: v["time"], reverse=True)[:limit]
                for v in todo:
                    v["_pic"] = v.get("_pic", 0) + 1
            found = newspics.find_images([{"link": v["link"]} for v in todo], budget=budget) if todo else {}
            if found:
                with self.lock:
                    for v in todo:
                        if not v.get("img") and found.get(v["link"]):
                            v["img"] = found[v["link"]]
        except Exception:
            pass
        try:
            newspics.fill(budget=45)
        except Exception:
            pass

    def _warm(self):
        """While visitors use the site in Arabic: the headlines of the last day are translated here, in the background, a few at a
        time, so the Arabic pages show them at once (each headline is translated once; data.translate keeps the answers)."""
        if self.feeds and self.feeds[0][0].startswith("sa_"):
            return                                     # the Saudi bot's headlines are mostly Arabic already
        try:
            import data
            if not data.arabic_in_use():
                return
            titles = [it["title"] for it in self.items(24)[:400] if it.get("title")]
            data.translate(titles, "ar", budget=45, workers=2, warm=True)
        except Exception:
            pass

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


_REFRESH = threading.Lock()   # held while a background refresh (started from a page) runs


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
    if b.updated and time.time() - b.updated > 3 * INTERVAL and not b.running.locked() and _REFRESH.acquire(blocking=False):
        # the loop looks stuck: refresh now, in the background (one such thread at a time, not one per page view)
        def _refresh():
            try:
                b.collect()
            finally:
                _REFRESH.release()
        try:
            threading.Thread(target=_refresh, daemon=True).start()
        except RuntimeError:
            _REFRESH.release()
    if wait and not b.first.is_set():
        b.first.wait(timeout)
    return b


def headlines(hours=48):
    try:
        return bot().items(hours)
    except Exception:
        return []


# ---------------------------------------------------------------- the Saudi market's news bot
def sa_tickers_in(text, extra=()):
    import tasi
    found = [t for t in extra if t and str(t).endswith(".SR")] + subject_tickers(tasi.tickers_in, text)
    return list(dict.fromkeys(found))[:6]


@st.cache_resource(show_spinner=False)
def _shared_sa_bot():
    b = NewsBot(SA_FEEDS, finder=sa_tickers_in)
    b.start()
    return b


def sa_bot(wait=True, timeout=14):
    """The Saudi market's shared bot (Arabic and English feeds on Saudi stocks), started on the first Saudi page."""
    b = _shared_sa_bot()
    if getattr(b, "build", None) != BUILD:
        try:
            b.stopped = True
            _shared_sa_bot.clear()
        except Exception:
            pass
        b = _shared_sa_bot()
    b.start()
    if wait and not b.first.is_set():
        b.first.wait(timeout)
    return b


def sa_headlines(hours=48):
    try:
        return sa_bot().items(hours)
    except Exception:
        return []

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "22.5"
