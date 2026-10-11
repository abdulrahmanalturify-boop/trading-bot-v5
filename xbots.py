"""
xbots.py - Ten bots that read X (Twitter) about the market and trade what they read, on paper: five for the US market and five
for the Saudi market.

Each bot has a beat on X: the market's mood, the companies suddenly talked about, the analysts' calls, the breaking-news
accounts, and (US) the crowd's fear about the mega-caps / (Saudi) the talk about oil. Every hour of its market's day (scripts/xbots_run.py, run by GitHub Actions, so it
works while nobody has the site open) a bot reads the newest posts of its beat and turns them into a reading:

- each post: the companies it is about, its tone (bullish / bearish, from the news engine's words plus the words people use
  on X: "calls", "long", "breakout", "دخول", "تصريف"...) and its reach (the author's followers, the likes and reposts);
- the beat: its mood hour by hour (-100 bearish .. +100 bullish, every post weighted by its reach), and the companies it talks
  about most, how fast that grows (the last 6 hours against the 3-day pace) and in what tone.

Its rules then trade a paper account at the latest price while its market is open: long only, no leverage, a 0.1% fee each
way, a stop, a target and a time limit on every position. The reading decides, the price confirms.

X charges for every post read, so the bots share a daily ceiling (X_DAILY_READS, 800 by default) and each reads only what is
new since its last read. Nothing is invented: without the X key (X_BEARER_TOKEN in GitHub's Actions secrets) the bots wait,
and the page says so.

Everything a bot knows (its posts of the last 3 days, its hourly mood, its account) is one row of the paper_bots table
(strategy "__portfolio__:xbot:<id>", left out of the paper bots' list like the portfolios), or a temporary file without Supabase.
"""
import hashlib
import json
import math
import os
import re
import tempfile
import threading
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import markets as MK

API = "https://api.x.com/2/tweets/search/recent"
DAILY_READS = 800                 # posts read a day by the ten bots together (X_DAILY_READS overrides it)
PER_RUN = 20                      # posts read by one bot in one run at most (X returns 10 to 100)
KEEP_HOURS = 72                   # posts kept for the reading
START_CASH = 100_000.0
FEE = 0.001                       # 0.1% of the value, each way
KEY = "__portfolio__:xbot:"       # the row of a bot (paper_bots.strategy): left out of the bots' list like the portfolios
META = "__portfolio__:xbots"      # the shared row: posts read today
LOG = "__portfolio__:xbotlog:"    # the bot's log (its own row, read only for the bot shown): its hourly mood and its daily signals
LOG_DAYS = 120                    # signals kept (days)
HOURLY_DAYS = 45                  # hourly mood lines kept (days)
MIN_OBS = 20                      # readings with a known next day before a bot is judged
COST = 0.005                      # what X charges for one post read, in dollars

# ---------------------------------------------------------------- the bots: five for the US market, five for the Saudi market
# rules: entry (what has to be true to buy), size (share of the account per position), slots (positions at most), stop / target
# (% from the entry), days (calendar days a position may stay). color: the bot's own hue on the page (the chart palette).
BOTS = [
    # ---- US
    {"id": "pulse", "market": MK.US, "icon": "monitor_heart", "color": "#5088F2",
     "name": ("Market Pulse", "نبض السوق"),
     "beat": ("The mood of X about the US market: the indices, Wall Street, the Fed and the economy.",
              "مزاج X عن السوق الأمريكي: المؤشرات ووول ستريت والفيدرالي والاقتصاد."),
     "query": '($SPY OR $QQQ OR $SPX OR "stock market" OR "Wall Street" OR "S&P 500" OR Nasdaq OR "the Fed") lang:en -is:retweet -is:reply',
     "style": "pulse", "trade": ["SPY"], "ref": "SPY", "size": 0.95, "slots": 1, "stop": 0.0, "target": 0.0, "days": 0,
     "rules": ("Holds SPY (the S&P 500) while the mood of the last 6 hours is bullish (+12 or more) and not falling against the 6 hours "
               "before; goes back to cash when the mood turns bearish (-12 or less).",
               "يمسك SPY (مؤشر S&P 500) طالما مزاج آخر 6 ساعات صاعد (+12 أو أكثر) وما نزل عن الست ساعات اللي قبلها، ويرجع كاش لما "
               "يصير المزاج هابط (-12 أو أقل).")},
    {"id": "trend", "market": MK.US, "icon": "local_fire_department", "color": "#DF4E92",
     "name": ("Trending Stocks", "الأسهم الرائجة"),
     "beat": ("The stocks X suddenly talks about: the most-followed tickers, and how fast their mentions grow.",
              "الأسهم اللي فجأة صار عنها كلام في X: أشهر الرموز، وكم تزيد الإشارات لها."),
     "query": None, "style": "trend", "size": 0.22, "slots": 4, "stop": 8.0, "target": 15.0, "days": 7,
     "rules": ("Buys a stock talked about at least twice its usual pace (the last 6 hours against the 3-day average) in a bullish "
               "tone, with at least 4 posts in a day, that is not down more than 3% today; up to 4 stocks. Sells on a bearish turn, a "
               "stop at -8%, a target at +15% or after 7 days.",
               "يشتري السهم اللي صار الكلام عنه ضعف معدله أو أكثر (آخر 6 ساعات مقابل معدل 3 أيام) بنبرة صاعدة، وعنه 4 تغريدات على "
               "الأقل باليوم، وما نزل أكثر من 3% اليوم؛ لين 4 أسهم. يبيع إذا انقلبت النبرة لهابطة، أو عند وقف -8%، أو هدف +15%، أو بعد 7 أيام.")},
    {"id": "pros", "market": MK.US, "icon": "school", "color": "#BE8700",
     "name": ("Market Pros", "حسابات المحللين"),
     "beat": ("Well-known strategists and market accounts: what they say about stocks and the market.",
              "استراتيجيون وحسابات سوق معروفة: وش يقولون عن الأسهم والسوق."),
     "query": ("(from:LizAnnSonders OR from:charliebilello OR from:KobeissiLetter OR from:unusual_whales OR from:Barchart OR "
               "from:biancoresearch OR from:NickTimiraos OR from:elerianm OR from:MarketWatch) -is:retweet"),
     "style": "calls", "size": 0.18, "slots": 5, "stop": 8.0, "target": 15.0, "days": 10,
     "rules": ("Buys a stock one of these accounts writes about in a clearly bullish tone (0.3 or more); sells when one of them turns "
               "bearish on it, at a stop of -8%, a target of +15% or after 10 days; up to 5 stocks.",
               "يشتري السهم اللي يكتب عنه أحد هالحسابات بنبرة صاعدة واضحة (0.3 أو أكثر)، ويبيع إذا قلب واحد منهم هابط عليه، أو عند وقف "
               "-8%، أو هدف +15%، أو بعد 10 أيام؛ لين 5 أسهم.")},
    {"id": "flash", "market": MK.US, "icon": "bolt", "color": "#00A99C",
     "name": ("Breaking on X", "العاجل في X"),
     "beat": ("The fastest breaking-news accounts: earnings, deals, guidance, ratings and rulings about companies.",
              "أسرع حسابات الأخبار العاجلة: أرباح وصفقات وتوقعات وتصنيفات وقرارات عن الشركات."),
     "query": ("(from:DeItaone OR from:FirstSquawk OR from:LiveSquawk OR from:CNBCnow OR from:WSJmarkets OR from:business OR "
               "from:ReutersBiz OR from:Benzinga OR from:financialjuice) -is:retweet"),
     "style": "flash", "size": 0.15, "slots": 5, "stop": 5.0, "target": 8.0, "days": 2,
     "rules": ("Buys a company right after clearly good news about it (earnings beat, deal, raised guidance, upgrade, approval: tone "
               "0.35 or more) if its price agrees today; a short trade: stop -5%, target +8%, out after 2 days; up to 5 stocks.",
               "يشتري الشركة بعد خبر زين واضح عنها (أرباح أعلى من المتوقع، صفقة، رفع توقعات، ترقية، موافقة: نبرة 0.35 أو أكثر) إذا سعرها "
               "اليوم يوافق؛ صفقة قصيرة: وقف -5%، هدف +8%، يطلع بعد يومين؛ لين 5 أسهم.")},
    {"id": "contra", "market": MK.US, "icon": "swap_vert", "color": "#9260DA",
     "name": ("Against the Crowd", "ضد التيار"),
     "beat": ("The ten largest US companies: buys the one the crowd is loudly bearish on, and waits for the fear to pass.",
              "أكبر عشر شركات أمريكية: يشتري اللي الناس متشائمين فيها بصوت عالي، وينتظر الخوف يروح."),
     "query": "($AAPL OR $MSFT OR $NVDA OR $AMZN OR $GOOGL OR $META OR $TSLA OR $AVGO OR $NFLX OR $AMD) lang:en -is:retweet -is:reply",
     "style": "contra", "size": 0.2, "slots": 4, "stop": 7.0, "target": 10.0, "days": 10,
     "rules": ("Buys a mega-cap written about in at least 6 posts in a day in a clearly bearish tone (-0.25 or less) that is not down "
               "more than 6% today (fear, not a collapse); sells when the tone recovers (+0.15), at a stop of -7%, a target of +10% or "
               "after 10 days; up to 4 stocks.",
               "يشتري الشركة العملاقة اللي عنها 6 تغريدات على الأقل باليوم بنبرة هابطة واضحة (-0.25 أو أقل) وما نزلت أكثر من 6% اليوم "
               "(خوف مو انهيار)، ويبيع لما تتحسن النبرة (+0.15)، أو عند وقف -7%، أو هدف +10%، أو بعد 10 أيام؛ لين 4 أسهم.")},
    # ---- Saudi
    {"id": "tasi", "market": MK.SA, "icon": "monitor_heart", "color": "#5088F2",
     "name": ("TASI Pulse", "نبض تاسي"),
     "beat": ("The mood of Arabic X about TASI and the Saudi market as a whole.",
              "مزاج X العربي عن تاسي والسوق السعودي ككل."),
     "query": '(تاسي OR #تاسي OR #السوق_السعودي OR "سوق الأسهم السعودية" OR "المؤشر العام" OR "سوق الأسهم") lang:ar -is:retweet -is:reply',
     "style": "pulse", "trade": ["2222.SR", "1120.SR", "1180.SR"], "ref": "^TASI.SR", "size": 0.31, "slots": 3, "stop": 0.0, "target": 0.0, "days": 0,
     "rules": ("Holds the market's three heaviest companies (Aramco, Al Rajhi, SNB) in equal parts while the mood of the last 6 hours "
               "is bullish (+12 or more) and not falling against the 6 hours before; goes back to cash when the mood turns bearish (-12 or less).",
               "يمسك أثقل ثلاث شركات في المؤشر (أرامكو، الراجحي، الأهلي) بالتساوي طالما مزاج آخر 6 ساعات صاعد (+12 أو أكثر) وما نزل عن "
               "الست ساعات اللي قبلها، ويرجع كاش لما يصير المزاج هابط (-12 أو أقل).")},
    {"id": "sa_trend", "market": MK.SA, "icon": "local_fire_department", "color": "#DF4E92",
     "name": ("Talk of TASI", "حديث تاسي"),
     "beat": ("The Saudi companies X talks about most, in what tone, and the ones suddenly on everyone's lips.",
              "الشركات السعودية اللي يتكلم عنها X أكثر، وبأي نبرة، واللي فجأة صارت على كل لسان."),
     "query": ("(أرامكو OR الراجحي OR سابك OR معادن OR الأهلي OR الإنماء OR \"اس تي سي\" OR أكوا OR \"سليمان الحبيب\" OR المراعي OR جرير OR "
               "كيان OR ينساب OR الاتصالات OR الكهرباء OR البلاد OR الرياض) lang:ar -is:retweet"),
     "style": "saudi", "size": 0.22, "slots": 4, "stop": 8.0, "target": 15.0, "days": 10,
     "rules": ("Buys a Saudi company talked about in at least 3 posts in a day in a bullish tone (0.2 or more) that is not down more "
               "than 3% today; sells on a bearish turn, a stop of -8%, a target of +15% or after 10 days; up to 4 companies.",
               "يشتري الشركة السعودية اللي عنها 3 تغريدات على الأقل باليوم بنبرة صاعدة (0.2 أو أكثر) وما نزلت أكثر من 3% اليوم، ويبيع "
               "إذا انقلبت النبرة لهابطة، أو عند وقف -8%، أو هدف +15%، أو بعد 10 أيام؛ لين 4 شركات.")},
    {"id": "sa_pros", "market": MK.SA, "icon": "school", "color": "#BE8700",
     "name": ("Chart Talk", "التحليل الفني"),
     "beat": ("The technical crowd of Saudi X: posts with supports, resistances, targets and calls on TASI companies.",
              "أهل التحليل الفني في X السعودي: تغريدات الدعوم والمقاومات والأهداف والتوصيات على شركات تاسي."),
     "query": ('(#تاسي OR #السوق_السعودي OR تاسي) (توصية OR "تحليل فني" OR دعم OR مقاومة OR اختراق OR هدف OR "وقف خسارة" OR نموذج) '
               "lang:ar -is:retweet -is:reply"),
     "style": "calls", "size": 0.18, "slots": 5, "stop": 8.0, "target": 15.0, "days": 10,
     "rules": ("Buys a company a technical post is clearly bullish on (0.3 or more); sells when a post turns bearish on it, at a stop of "
               "-8%, a target of +15% or after 10 days; up to 5 companies.",
               "يشتري الشركة اللي تغريدة فنية متفائلة فيها بوضوح (0.3 أو أكثر)، ويبيع إذا جت تغريدة هابطة عليها، أو عند وقف -8%، أو هدف "
               "+15%، أو بعد 10 أيام؛ لين 5 شركات.")},
    {"id": "sa_flash", "market": MK.SA, "icon": "bolt", "color": "#00A99C",
     "name": ("Tadawul Wire", "عاجل تداول"),
     "beat": ("The Saudi market's news accounts: announcements, results, dividends, contracts and deals of listed companies.",
              "حسابات أخبار السوق السعودي: إعلانات ونتائج وتوزيعات وعقود وصفقات الشركات المدرجة."),
     "query": ("(from:Argaam OR from:SaudiExchange OR from:aleqt OR from:MaaalNews OR from:Mubasher OR from:CNBCArabia OR "
               "from:AsharqBusiness) -is:retweet"),
     "style": "flash", "size": 0.15, "slots": 5, "stop": 5.0, "target": 8.0, "days": 2,
     "rules": ("Buys a company right after clearly good news about it (results above expectations, a contract, a dividend, an upgrade: "
               "tone 0.35 or more) if its price agrees today; a short trade: stop -5%, target +8%, out after 2 days; up to 5 companies.",
               "يشتري الشركة بعد خبر زين واضح عنها (نتائج أعلى من المتوقع، عقد، توزيعات، ترقية: نبرة 0.35 أو أكثر) إذا سعرها اليوم "
               "يوافق؛ صفقة قصيرة: وقف -5%، هدف +8%، يطلع بعد يومين؛ لين 5 شركات.")},
    {"id": "oil", "market": MK.SA, "icon": "oil_barrel", "color": "#9260DA",
     "name": ("Oil Watch", "راصد النفط"),
     "beat": ("What X says about oil, Brent and OPEC+, in Arabic and English: the market's biggest outside force.",
              "وش يقول X عن النفط وبرنت وأوبك+ بالعربي والإنجليزي: أكبر مؤثر خارجي على السوق."),
     "query": '(النفط OR برنت OR أوبك OR "أسعار النفط" OR "oil prices" OR Brent OR OPEC OR "crude oil") -is:retweet -is:reply',
     "style": "pulse", "trade": ["2222.SR", "2010.SR", "2350.SR"], "ref": "2222.SR", "size": 0.31, "slots": 3, "stop": 0.0, "target": 0.0, "days": 0,
     "rules": ("Holds Aramco, SABIC and Saudi Kayan in equal parts while the mood about oil over the last 6 hours is bullish (+12 or "
               "more) and not falling; goes back to cash when it turns bearish (-12 or less).",
               "يمسك أرامكو وسابك وكيان بالتساوي طالما مزاج آخر 6 ساعات عن النفط صاعد (+12 أو أكثر) وما نزل، ويرجع كاش لما يصير هابط "
               "(-12 أو أقل).")},
]
BY_ID = {b["id"]: b for b in BOTS}


def bots_of(market):
    return [b for b in BOTS if b["market"] == market]


# the tickers the trending bot follows (X's search takes 512 characters: the most-followed names)
TREND_TAGS = ["NVDA", "TSLA", "AAPL", "AMD", "PLTR", "MSFT", "META", "AMZN", "GOOGL", "SMCI", "MSTR", "COIN", "AVGO", "NFLX", "SOFI",
              "HOOD", "MU", "INTC", "ARM", "RIVN", "LCID", "NIO", "BA", "DIS", "UBER", "SNOW", "CRWD", "SHOP", "RDDT", "IONQ",
              "RKLB", "ASTS", "OKLO", "SOUN", "TSM", "ORCL", "CRM", "PYPL", "GME", "AMC"]


def _trend_query():
    q, tags = "", []
    for t in TREND_TAGS:
        nxt = "(" + " OR ".join(["$" + x for x in tags + [t]]) + ") lang:en -is:retweet -is:reply"
        if len(nxt) > 500:
            break
        tags.append(t)
        q = nxt
    return q


BY_ID["trend"]["query"] = _trend_query()
BENCH = {MK.US: "SPY", MK.SA: "^TASI.SR"}
KEY_EVENTS = {"earnings", "mna", "guidance", "analyst", "regulation", "contract", "product", "payout", "management"}

# ---------------------------------------------------------------- how people write on X (on top of the news engine's words)
POS_X = [r"bullish", r"\blong\b", r"\bcalls\b", r"breakout", r"breaking out", r"all[- ]time high", r"\bATH\b", r"moon\w*", r"rip(?:ping|s)?\b",
         r"squeeze", r"undervalued", r"accumulat\w+", r"loading up", r"\bbuy(?:ing)?\b", r"higher highs", r"🚀", r"📈", r"🟢", r"🔥",
         r"صاعد", r"إيجابي", r"ايجابي", r"اختراق", r"ارتداد", r"تجميع", r"دخول", r"فرصة", r"قمة جديدة", r"أعلى مستوى", r"شراء", r"قوي"]
NEG_X = [r"bearish", r"\bshort(?:ing)?\b", r"\bputs\b", r"dump\w*", r"crash\w*", r"overvalued", r"bubble", r"breakdown", r"\bsell(?:ing)?\b",
         r"rug ?pull", r"bag ?holder\w*", r"lower lows", r"📉", r"🔴", r"🩸",
         r"هابط", r"سلبي", r"تصريف", r"كسر", r"انهيار", r"نزول", r"بيع", r"ضعيف", r"خروج", r"أدنى مستوى"]
_POS_X = re.compile("|".join(POS_X), re.I)
_NEG_X = re.compile("|".join(NEG_X), re.I)
_URL = re.compile(r"https?://\S+")
_CASH = re.compile(r"\$([A-Z]{1,5})\b")


# ---------------------------------------------------------------- settings
def _secret(name):
    v = os.environ.get(name, "").strip()
    if v:
        return v
    try:
        import streamlit as st
        v = st.secrets.get(name)
        return str(v).strip() if v else ""
    except Exception:
        return ""


def daily_reads():
    try:
        return max(50, int(float(_secret("X_DAILY_READS") or DAILY_READS)))
    except ValueError:
        return DAILY_READS


# ---------------------------------------------------------------- reading X
class XError(Exception):
    """kind: auth (the key is wrong) · rate (too many requests) · credits (the X account has no credit left) · network · other"""

    def __init__(self, kind, detail=""):
        super().__init__(f"{kind}: {detail}")
        self.kind, self.detail = kind, str(detail)[:300]


def fetch(query, token, since_id=None, n=PER_RUN, get=None):
    """The newest posts of a search (newest first) and their authors: (posts, users by id, newest id). get: requests.get (tests)."""
    import requests
    get = get or requests.get
    params = {"query": query, "max_results": str(max(10, min(100, int(n)))),
              "tweet.fields": "created_at,public_metrics,lang,author_id", "expansions": "author_id",
              "user.fields": "username,name,verified,public_metrics"}
    if since_id:
        params["since_id"] = str(since_id)
    try:
        r = get(API, params=params, headers={"Authorization": f"Bearer {token}"}, timeout=20)
    except Exception as e:                                   # noqa: BLE001 - any network failure
        raise XError("network", e) from e
    if r.status_code in (401, 403):
        raise XError("auth", r.text[:200])
    if r.status_code == 429:
        raise XError("rate", r.text[:200])
    if r.status_code == 402:
        raise XError("credits", r.text[:200])
    if r.status_code >= 400:
        raise XError("other", f"HTTP {r.status_code}: {r.text[:200]}")
    js = r.json() or {}
    users = {u.get("id"): u for u in (js.get("includes") or {}).get("users") or []}
    return js.get("data") or [], users, (js.get("meta") or {}).get("newest_id")


# ---------------------------------------------------------------- one post
_KNOWN = {}


def known_us():
    """The US tickers a cashtag may name (so "$100" or "$CEO" is no company)."""
    if not _KNOWN:
        import universe as U
        s = set(U.STOCKS) | {"SPY", "QQQ", "IWM", "DIA", "TLT", "GLD", "SLV", "USO", "SMH", "ARKK", "XLF", "XLE", "XLK"}
        try:
            from sp500 import SP500
            s |= set(SP500)
        except Exception:
            pass
        try:
            import data
            s |= {k for k in data._info_file() if not str(k).endswith(".SR")}
        except Exception:
            pass
        s |= set(TREND_TAGS)
        _KNOWN["us"] = s
    return _KNOWN["us"]


def tone(text, sa=False):
    """(-1..1, 'bull' | 'bear' | 'neutral', kind of event): the news engine's reading of the words, plus the words of X."""
    import newsintel as NI
    ev = NI.classify(text)
    s, _lab, _w = NI.sentiment(text, "", ev, sa=sa)
    p, n = len(_POS_X.findall(text)), len(_NEG_X.findall(text))
    s = float(np.clip(s + 0.22 * (p - n), -1, 1))
    return s, ("bull" if s >= 0.15 else "bear" if s <= -0.15 else "neutral"), ev


def companies(text, market):
    if market == MK.SA:
        import tasi
        return tasi.tickers_in(text)[:4]
    import universe as U
    known = known_us()
    out = [m.group(1) for m in _CASH.finditer(text or "") if m.group(1) in known]
    out += [t for t in U.detect_tickers(text) if t not in out]
    return list(dict.fromkeys(out))[:4]


def read_post(p, users, market):
    """A post as the bots keep it: who, when, what (400 characters), its companies, tone, kind of event and weight (reach)."""
    u = users.get(p.get("author_id")) or {}
    um = u.get("public_metrics") or {}
    pm = p.get("public_metrics") or {}
    text = _URL.sub("", str(p.get("text") or "")).strip()
    s, lab, ev = tone(text, market == MK.SA)
    fol = int(um.get("followers_count") or 0)
    eng = int(pm.get("like_count") or 0) + 2 * int(pm.get("retweet_count") or 0) + int(pm.get("reply_count") or 0) + int(pm.get("quote_count") or 0)
    w = 1.0 + math.log10(1 + fol) / 2 + math.log10(1 + eng) / 2 + (0.5 if u.get("verified") else 0.0)
    return {"id": str(p.get("id")), "t": str(p.get("created_at") or ""), "user": u.get("username") or "", "name": u.get("name") or "",
            "followers": fol, "likes": int(pm.get("like_count") or 0), "reposts": int(pm.get("retweet_count") or 0),
            "text": text[:400], "tickers": companies(text, market), "s": round(s, 3), "lab": lab, "event": ev, "w": round(w, 3)}


# ---------------------------------------------------------------- the reading of a beat
def _ts(x):
    try:
        t = pd.Timestamp(x)
        if pd.isna(t):                                  # None / "" -> NaT: no time
            return None
        return t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
    except (ValueError, TypeError):
        return None


def _mood(rows):
    w = sum(r["w"] for r in rows)
    return 100.0 * sum(r["w"] * r["s"] for r in rows) / w if w else None


def reading(posts, now=None):
    """The beat right now: mood of the last 6 and 24 hours and of the 6 hours before, its hours (oldest first), the companies
    talked about (mentions in 24 h, growth: the last 6 hours against the 3-day pace, tone) and the strongest posts."""
    now = now or pd.Timestamp.now(tz="UTC")
    rows = [dict(p, _t=_ts(p.get("t"))) for p in posts]
    rows = [r for r in rows if r["_t"] is not None and (now - r["_t"]).total_seconds() <= KEEP_HOURS * 3600]

    def last(h0, h1):
        return [r for r in rows if h0 * 3600 <= (now - r["_t"]).total_seconds() < h1 * 3600]
    r6, r24, rprev = last(0, 6), last(0, 24), last(6, 12)
    hours = []
    for k in range(47, -1, -1):
        h = last(k, k + 1)
        hours.append({"t": (now - pd.Timedelta(hours=k)).floor("h").isoformat(), "mood": _mood(h), "n": len(h)})
    tick = {}
    for r in rows:
        age = (now - r["_t"]).total_seconds() / 3600
        for t in r.get("tickers") or []:
            d = tick.setdefault(t, {"sym": t, "n24": 0, "n6": 0, "n72": 0, "ws": 0.0, "w": 0.0, "users": set()})
            d["n72"] += 1
            if age < 24:
                d["n24"] += 1
                d["ws"] += r["w"] * r["s"]
                d["w"] += r["w"]
                d["users"].add(r.get("user"))
            if age < 6:
                d["n6"] += 1
    span = max(6.0, min(KEEP_HOURS, (now - min((r["_t"] for r in rows), default=now)).total_seconds() / 3600))
    talked = []
    for d in tick.values():
        pace = d["n72"] / span * 6                             # posts per 6 hours over the whole window
        talked.append({"sym": d["sym"], "n24": d["n24"], "n6": d["n6"], "spike": round(d["n6"] / pace, 2) if pace else 0.0,
                       "s": round(d["ws"] / d["w"], 3) if d["w"] else 0.0, "authors": len(d["users"] - {""})})
    talked.sort(key=lambda d: (-d["n24"], -d["spike"]))
    top, seen = [], set()
    for r in sorted(r24, key=lambda r: -(r["w"] * (0.5 + abs(r["s"])))):    # the same words posted again (copies, bots) show once
        k = re.sub(r"https?://\S+|[^\w$]+", " ", (r.get("text") or "").lower()).strip()
        if k in seen:
            continue
        seen.add(k)
        top.append(r)
        if len(top) == 12:
            break
    return {"mood6": _mood(r6), "mood24": _mood(r24), "prev6": _mood(rprev), "n6": len(r6), "n24": len(r24), "hours": hours,
            "talked": talked[:25], "top": [{k: v for k, v in r.items() if k != "_t"} for r in top]}


# ---------------------------------------------------------------- the paper account
def new_ledger(market):
    return {"market": market, "start": START_CASH, "cash": START_CASH, "pos": {}, "trades": [], "curve": [], "since": None}


def equity(ledger, prices):
    return ledger["cash"] + sum(p["qty"] * (prices.get(s) or p["px"]) for s, p in ledger["pos"].items())


def _buy(ledger, sym, px, value, why, now):
    qty = math.floor(value / (px * (1 + FEE)))
    if qty < 1 or px <= 0:
        return None
    cost = qty * px * (1 + FEE)
    if cost > ledger["cash"] + 1e-6:
        return None
    ledger["cash"] -= cost
    ledger["pos"][sym] = {"qty": qty, "px": round(px, 4), "t": now.isoformat(), "why": why, "peak": round(px, 4)}
    tr = {"t": now.isoformat(), "sym": sym, "side": "buy", "qty": qty, "px": round(px, 4), "why": why}
    ledger["trades"].append(tr)
    return tr


def _sell(ledger, sym, px, why, now):
    p = ledger["pos"].pop(sym, None)
    if not p or px <= 0:
        return None
    ledger["cash"] += p["qty"] * px * (1 - FEE)
    pnl = (px * (1 - FEE)) / (p["px"] * (1 + FEE)) - 1
    tr = {"t": now.isoformat(), "sym": sym, "side": "sell", "qty": p["qty"], "px": round(px, 4), "why": why, "pnl": round(pnl * 100, 2),
          "held_from": p["t"]}
    ledger["trades"].append(tr)
    return tr


WHY = {"stop": ("Stop", "وقف الخسارة"), "target": ("Target reached", "الهدف تحقق"), "time": ("Time limit", "انتهت المدة"),
       "bear": ("The tone turned bearish", "النبرة انقلبت هابطة"), "mood_up": ("The mood is bullish", "المزاج صاعد"),
       "mood_down": ("The mood turned bearish", "المزاج انقلب هابط"), "spike": ("Talked about far more than usual, bullish", "كلام أكثر بكثير من المعتاد وبنبرة صاعدة"),
       "pro": ("A market pro is bullish on it", "محلل معروف متفائل فيه"), "news": ("Good breaking news", "خبر عاجل إيجابي"),
       "sa": ("Bullish talk about it on X", "كلام إيجابي عنه في X"),
       "contra": ("The crowd is loudly bearish on it: buying the fear", "الناس متشائمين فيه بصوت عالي: شراء الخوف"),
       "calm": ("The tone recovered", "النبرة تحسنت")}


def decide(bot, read, posts, ledger, quotes, now=None):
    """The trades of this run (the market is open): exits first (stop, target, time, a bearish turn), then entries by the bot's
    rules. quotes: {symbol: (price, % change today)} for the symbols held and the candidates. Returns the trades made."""
    now = now or pd.Timestamp.now(tz="UTC")
    style, made = bot["style"], []
    px = {s: q[0] for s, q in quotes.items() if q and q[0]}
    chg = {s: q[1] for s, q in quotes.items() if q}
    tone_of = {d["sym"]: d for d in read.get("talked") or []}
    # exits
    for sym, p in list(ledger["pos"].items()):
        price = px.get(sym)
        if not price:
            continue
        p["peak"] = max(p.get("peak") or p["px"], price)
        r = (price / p["px"] - 1) * 100
        age = (now - _ts(p["t"])).total_seconds() / 86400 if _ts(p["t"]) is not None else 0
        why = None
        if style == "pulse":
            if read.get("mood6") is not None and read["mood6"] <= -12:
                why = "mood_down"
        else:
            if bot["stop"] and r <= -bot["stop"]:
                why = "stop"
            elif bot["target"] and r >= bot["target"]:
                why = "target"
            elif bot["days"] and age >= bot["days"]:
                why = "time"
            elif style == "calls" and any(sym in (x.get("tickers") or []) and x["s"] <= -0.3 and (_ts(x.get("t")) or now) > _ts(p["t"])
                                          for x in posts[:80]):
                why = "bear"
            elif style in ("trend", "saudi") and sym in tone_of and tone_of[sym]["n24"] >= 2 and tone_of[sym]["s"] <= -0.1:
                why = "bear"
            elif style == "contra" and sym in tone_of and tone_of[sym]["n24"] >= 2 and tone_of[sym]["s"] >= 0.15:
                why = "calm"
        if why:
            t = _sell(ledger, sym, price, why, now)
            if t:
                made.append(t)
    # entries
    eq = equity(ledger, px)
    free = bot["slots"] - len(ledger["pos"])
    if free <= 0:
        return made
    cands = []
    if style == "pulse":
        m6, prev = read.get("mood6"), read.get("prev6")
        if m6 is not None and m6 >= 12 and read.get("n6", 0) >= 8 and (prev is None or m6 >= prev - 5):
            cands = [(s, "mood_up", m6) for s in bot["trade"]]
    elif style == "contra":
        for d in read.get("talked") or []:
            if d["n24"] >= 6 and d["s"] <= -0.25 and (chg.get(d["sym"]) is None or chg[d["sym"]] > -6):
                cands.append((d["sym"], "contra", -d["s"] * d["n24"]))
    elif style in ("trend", "saudi"):
        for d in read.get("talked") or []:
            need_n = 4 if style == "trend" else 3
            need_s = 0.15 if style == "trend" else 0.2
            spike_ok = d["spike"] >= 2.0 if style == "trend" else True
            if d["n24"] >= need_n and d["s"] >= need_s and spike_ok and (chg.get(d["sym"]) is None or chg[d["sym"]] > -3):
                cands.append((d["sym"], "spike" if style == "trend" else "sa", d["s"] * (1 + d["spike"])))
    elif style == "calls":
        seen = set()
        for x in sorted(posts, key=lambda x: x.get("t") or "", reverse=True):
            ts = _ts(x.get("t"))
            if ts is None or (now - ts).total_seconds() > 24 * 3600:
                continue
            for sym in x.get("tickers") or []:
                if sym not in seen and x["s"] >= 0.3 and (chg.get(sym) is None or chg[sym] > -3):
                    seen.add(sym)
                    cands.append((sym, "pro", x["s"] * x["w"]))
    elif style == "flash":
        seen = set()
        for x in sorted(posts, key=lambda x: x.get("t") or "", reverse=True):
            ts = _ts(x.get("t"))
            if ts is None or (now - ts).total_seconds() > 6 * 3600:
                continue
            if x.get("event") in KEY_EVENTS and x["s"] >= 0.35:
                for sym in (x.get("tickers") or [])[:1]:
                    if sym not in seen and chg.get(sym) is not None and chg[sym] > 0:
                        seen.add(sym)
                        cands.append((sym, "news", x["s"]))
    cands.sort(key=lambda c: -c[2])
    for sym, why, _score in cands:
        if free <= 0:
            break
        if sym in ledger["pos"] or not px.get(sym):
            continue
        if any(t["sym"] == sym and t["side"] == "sell" and (now - _ts(t["t"])).total_seconds() < 86400 for t in ledger["trades"][-20:]):
            continue                                   # sold within the day: not bought straight back
        t = _buy(ledger, sym, px[sym], eq * bot["size"], why, now)
        if t:
            made.append(t)
            free -= 1
    return made


def mark(ledger, prices, now=None, bench=None):
    """Today's point of the account's curve (one per day, the latest value of the day) with the market's benchmark (bench: its
    price now, SPY / TASI) so the account can be set against its market."""
    now = now or pd.Timestamp.now(tz="UTC")
    d = now.tz_convert(MK.tz(ledger.get("market"))).date().isoformat()
    eq = round(equity(ledger, prices), 2)
    if ledger["curve"] and ledger["curve"][-1]["d"] == d:
        ledger["curve"][-1]["eq"] = eq
    else:
        ledger["curve"].append({"d": d, "eq": eq})
    if bench:
        ledger["curve"][-1]["b"] = round(float(bench), 4)
    ledger["curve"] = ledger["curve"][-400:]
    return eq


def stats(ledger, prices=None):
    """Return since the start, the closed trades (count, wins, average), the value now."""
    eq = equity(ledger, prices or {})
    closed = [t for t in ledger["trades"] if t["side"] == "sell" and t.get("pnl") is not None]
    wins = [t for t in closed if t["pnl"] > 0]
    return {"equity": eq, "ret": (eq / ledger["start"] - 1) * 100, "closed": len(closed), "wins": len(wins),
            "win_rate": len(wins) / len(closed) * 100 if closed else None,
            "avg": float(np.mean([t["pnl"] for t in closed])) if closed else None, "open": len(ledger["pos"])}


# ---------------------------------------------------------------- the log: does the mood come before the price?
# Every run adds a line to the bot's hourly log (its mood, posts and the price of what it is judged against). While its market is
# open it also keeps, for every trading day, its last reading of each company it talks about (for a market-mood bot: of the
# market) and the price at that moment; once the next sessions have closed, the log fills in where the price went (the next
# day's close, three days later). Those pairs say whether the bot's reading came before the price: a "truthful" bot's bullish
# readings are followed by rises and its bearish ones by falls more often than not; a "noise" bot's are not; a "reversed" bot's
# go the other way.
def new_log(now=None):
    return {"since": (now or pd.Timestamp.now(tz="UTC")).isoformat(), "hourly": [], "sig": []}


def log_reading(log, bot, read, px, now, live):
    """Adds this run to the log. px: {symbol: price now} (the companies talked about and the bot's reference); live: its market
    is open (a signal is kept only with a price that trades)."""
    ref = bot.get("ref")
    log["hourly"].append({"t": now.floor("min").isoformat(), "m": None if read.get("mood6") is None else round(read["mood6"], 1),
                          "n": int(read.get("n6") or 0), "px": px.get(ref) if ref else None})
    cut = (now - pd.Timedelta(days=HOURLY_DAYS)).isoformat()
    log["hourly"] = [h for h in log["hourly"] if h["t"] >= cut][-2000:]
    if not live:
        return
    d = now.tz_convert(MK.tz(bot["market"])).date().isoformat()
    obs = []
    if bot["style"] == "pulse":
        if read.get("mood24") is not None and px.get(ref):
            obs.append((ref, read["mood24"] / 100, int(read.get("n24") or 0), px[ref]))
    else:
        for t in (read.get("talked") or [])[:10]:
            if t["n24"] >= 2 and px.get(t["sym"]):
                obs.append((t["sym"], t["s"], t["n24"], px[t["sym"]]))
    keep = {(x["d"], x["sym"]): x for x in log["sig"]}
    for sym, s_, n_, p_ in obs:                          # the day's last reading of each (a later run of the day replaces it)
        keep[(d, sym)] = {"d": d, "t": now.floor("min").isoformat(), "sym": sym, "s": round(float(s_), 3), "n": int(n_),
                          "px": round(float(p_), 4), "r1": None, "r3": None}
    cutd = (now - pd.Timedelta(days=LOG_DAYS)).date().isoformat()
    log["sig"] = sorted((x for x in keep.values() if x["d"] >= cutd), key=lambda x: (x["d"], x["sym"]))


def fill_moves(log, market, now, closes_fn=None):
    """Fills in the next day's and the third day's move of every signal whose sessions have closed: from the daily closes, or
    (an index Yahoo keeps no history for, TASI) from the log's own later readings of it."""
    today = now.tz_convert(MK.tz(market)).date().isoformat()
    todo = [x for x in log["sig"] if x["d"] < today and (x.get("r1") is None or x.get("r3") is None)]
    if not todo:
        return
    syms = sorted({x["sym"] for x in todo})
    try:
        closes = (closes_fn or _closes)(syms)
    except Exception:
        closes = {}
    by_sym = {}
    for x in log["sig"]:
        by_sym.setdefault(x["sym"], []).append(x)
    for x in todo:
        c = closes.get(x["sym"])
        later = []
        if c is not None and len(c):
            later = [float(v) for k, v in c.items() if k.date().isoformat() > x["d"] and k.date().isoformat() < today and pd.notna(v)]
        if not later:                                   # no history (TASI): the log's own last readings of the next days
            later = [y["px"] for y in by_sym.get(x["sym"], []) if x["d"] < y["d"] < today]
        if x.get("r1") is None and len(later) >= 1:
            x["r1"] = round((later[0] / x["px"] - 1) * 100, 3)
        if x.get("r3") is None and len(later) >= 3:
            x["r3"] = round((later[2] / x["px"] - 1) * 100, 3)


def _closes(syms):
    """{symbol: daily closes (Series)} of the last three months."""
    import data
    hist = data.history_many(tuple(syms), period="3mo")
    out = {}
    for s_, df in (hist or {}).items():
        if df is not None and len(df) and "Close" in df:
            c = df["Close"].dropna()
            c.index = pd.to_datetime(c.index)
            out[s_] = c.tz_localize(None) if c.index.tz is not None else c
    return out


def scorecard(bot, sig):
    """Does the bot's reading come before the price? From its signals with a known next day: hit (% of bullish readings followed
    by a rise and bearish ones by a fall; for the contrarian bot the other way round), edge (the next day's average move after
    its bullish readings minus after its bearish ones, in %), ic (rank correlation between the tone and the next day's move),
    the average move after bearish / neutral / bullish readings, and the verdict."""
    sign = -1.0 if bot["style"] == "contra" else 1.0
    obs = [x for x in sig if x.get("r1") is not None]
    bull = [x for x in obs if x["s"] >= 0.12]
    bear = [x for x in obs if x["s"] <= -0.12]
    neut = [x for x in obs if -0.12 < x["s"] < 0.12]
    n = len(bull) + len(bear)

    def avg(rows, k="r1"):
        v = [x[k] for x in rows if x.get(k) is not None]
        return round(float(np.mean(v)), 3) if v else None
    hits = sum(1 for x in bull if x["r1"] * sign > 0) + sum(1 for x in bear if x["r1"] * sign < 0)
    hit = round(hits / n * 100, 1) if n else None
    edge = round(((avg(bull) or 0.0) - (avg(bear) or 0.0)) * sign, 3) if bull and bear else (
        round((avg(bull) or 0.0) * sign, 3) if bull else round(-(avg(bear) or 0.0) * sign, 3) if bear else None)
    ic = None
    if len(obs) >= 5:
        a = pd.Series([x["s"] for x in obs]).rank()
        b = pd.Series([x["r1"] for x in obs]).rank()
        if a.std() > 0 and b.std() > 0:
            ic = round(float(np.corrcoef(a, b)[0, 1]) * sign, 3)
    if n < MIN_OBS:
        verdict = "collecting"
    elif hit >= 55 and (edge or 0) > 0 and (ic is None or ic > 0.05):
        verdict = "truthful"
    elif hit <= 45 and (edge or 0) < 0:
        verdict = "reversed"
    else:
        verdict = "noise"
    return {"n": n, "obs": len(obs), "hit": hit, "edge": edge, "ic": ic, "verdict": verdict,
            "buckets": {"bear": [avg(bear), len(bear)], "neutral": [avg(neut), len(neut)], "bull": [avg(bull), len(bull)]},
            "r3": {"bear": avg(bear, "r3"), "bull": avg(bull, "r3")}}


def perf(ledger, reads=0):
    """The account's metrics: return, the market's return over the same days, the difference, the deepest fall from a high,
    closed trades, wins, average win and loss, profit factor (gains / losses), average days held, and the cost of its reading."""
    curve = ledger.get("curve") or []
    eqs = [c["eq"] for c in curve if c.get("eq") is not None]
    ret = (eqs[-1] / ledger["start"] - 1) * 100 if eqs else 0.0
    bs = [c["b"] for c in curve if c.get("b")]
    bench = (bs[-1] / bs[0] - 1) * 100 if len(bs) >= 2 else None
    mdd = 0.0
    if eqs:
        e = pd.Series([ledger["start"]] + eqs)
        mdd = float((e / e.cummax() - 1).min() * 100)
    closed = [t for t in ledger["trades"] if t["side"] == "sell" and t.get("pnl") is not None]
    wins = [t["pnl"] for t in closed if t["pnl"] > 0]
    losses = [t["pnl"] for t in closed if t["pnl"] <= 0]
    holds = []
    for t in closed:
        a, b = _ts(t.get("held_from")), _ts(t.get("t"))
        if a is not None and b is not None:
            holds.append((b - a).total_seconds() / 86400)
    return {"ret": round(ret, 3), "bench": None if bench is None else round(bench, 3), "vs": None if bench is None else round(ret - bench, 3),
            "mdd": round(mdd, 3), "closed": len(closed), "wins": len(wins),
            "win_rate": round(len(wins) / len(closed) * 100, 1) if closed else None,
            "avg_win": round(float(np.mean(wins)), 3) if wins else None, "avg_loss": round(float(np.mean(losses)), 3) if losses else None,
            "pf": round(sum(wins) / -sum(losses), 2) if losses and sum(losses) < 0 else None,      # None: no losing trade yet
            "hold": round(float(np.mean(holds)), 2) if holds else None, "cost": round(int(reads or 0) * COST, 2)}


# ---------------------------------------------------------------- the store (one row per bot, and one shared row)
_LOCK = threading.Lock()


def _local(key):
    return os.path.join(tempfile.gettempdir(), f"alturaifi_xbot_{hashlib.sha256(key.encode()).hexdigest()[:16]}.json")


def load(key):
    """(the stored object or None, row id)."""
    import paperbots as PB
    if PB.backend() == "supabase":
        url, h = PB._sb()
        r = PB._request("GET", url, headers=h, params={"select": "id,params", "strategy": f"eq.{key}", "order": "id.asc", "limit": "1"})
        PB._check(r)
        rows = r.json()
        if rows:
            p = rows[0].get("params") or {}
            if isinstance(p, str):
                p = json.loads(p)
            return p.get("x"), rows[0]["id"]
        return None, None
    with _LOCK:
        try:
            with open(_local(key), encoding="utf-8") as f:
                return json.load(f), 0
        except (OSError, ValueError):
            return None, None


def save(key, obj, row_id=None):
    import paperbots as PB
    body = json.loads(json.dumps(obj, default=str))
    if PB.backend() == "supabase":
        url, h = PB._sb()
        rec = {"name": f"X bot {key.rsplit(':', 1)[-1]}", "symbol": "XBOT", "strategy": key, "params": {"x": body},
               "capital": START_CASH, "start_date": datetime.now(timezone.utc).date().isoformat()}
        if row_id:
            r = PB._request("PATCH", url, headers={**h, "Prefer": "return=minimal"}, params={"id": f"eq.{int(row_id)}"}, data=json.dumps(rec))
        else:
            r = PB._request("POST", url, headers={**h, "Prefer": "return=minimal"}, data=json.dumps(rec))
        PB._check(r)
        return
    with _LOCK:
        tmp = _local(key) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(body, f, ensure_ascii=False)
        os.replace(tmp, _local(key))


def new_bot_state(bot):
    return {"id": bot["id"], "market": bot["market"], "since_id": None, "posts": [], "read": None, "ledger": new_ledger(bot["market"]),
            "updated": None, "read_at": None, "status": "waiting", "error": None, "reads": 0}


def load_all():
    """{bot id: its stored state} and the shared row ({"date", "reads"}). Never raises: a bot that can't be read is left out."""
    out = {}
    for b in BOTS:
        try:
            obj, _ = load(KEY + b["id"])
        except Exception:
            obj = None
        if obj:
            out[b["id"]] = obj
    try:
        meta, _ = load(META)
    except Exception:
        meta = None
    return out, meta or {}


# ---------------------------------------------------------------- one run of one bot
def in_hours(bot, now=None):
    """The bot reads from an hour before its market opens to an hour after it closes, on its trading days."""
    code = bot["market"]
    t_ = (now or pd.Timestamp.now(tz="UTC")).tz_convert(MK.tz(code)).tz_localize(None)
    kind, _ = MK.cal(code).day_status(t_.date())
    if kind in ("weekend", "closed"):
        return False
    sp = MK.get(code)
    m = t_.hour * 60 + t_.minute
    return sp["open"] - 60 <= m <= sp["close"] + 60


def run(bot, token, meta, now=None, get=None, quotes_fn=None, force=False, closes_fn=None):
    """One run of a bot: read the new posts (within today's ceiling), update its reading, trade while its market is open, mark its
    account. meta: the shared row (posts read today), updated in place. Returns the bot's new state (saved by the caller)."""
    now = now or pd.Timestamp.now(tz="UTC")
    try:
        state, row = load(KEY + bot["id"])
    except Exception:
        state, row = None, None
    state = state or new_bot_state(bot)
    state["_row"] = row
    today = now.date().isoformat()
    if meta.get("date") != today:
        meta.update({"date": today, "reads": 0})
    cap = daily_reads()
    if not token:
        state["status"], state["error"] = "no_key", None
    elif not (force or in_hours(bot, now)):
        state["status"] = "resting"
    elif meta["reads"] >= cap:
        state["status"] = "cap"
    else:
        n = min(PER_RUN, cap - meta["reads"])
        try:
            data_, users, newest = fetch(bot["query"], token, state.get("since_id"), max(10, n), get=get)
            meta["reads"] += len(data_)
            state["reads"] = int(state.get("reads") or 0) + len(data_)
            fresh = [read_post(p, users, bot["market"]) for p in data_]
            have = {p["id"] for p in state["posts"]}
            state["posts"] = sorted([p for p in fresh if p["id"] not in have] + state["posts"], key=lambda p: p.get("t") or "", reverse=True)
            cut = (now - pd.Timedelta(hours=KEEP_HOURS)).isoformat()
            state["posts"] = [p for p in state["posts"] if (p.get("t") or "") >= cut[:19]][:400]
            if newest:
                state["since_id"] = newest
            state["status"], state["error"], state["read_at"] = "ok", None, now.isoformat()
        except XError as e:
            state["status"], state["error"] = "error", e.kind
    state["read"] = reading(state["posts"], now)
    # trade while the market is open, at the latest prices
    led = state["ledger"]
    held = list(led["pos"])
    cand = [d["sym"] for d in (state["read"].get("talked") or [])[:12]] + [s for p in state["posts"][:60] for s in (p.get("tickers") or [])]
    syms = list(dict.fromkeys(held + (bot.get("trade") or []) + cand))[:40]
    quotes = (quotes_fn or _quotes)(syms) if syms else {}
    open_ = force or MK.session_live(bot["market"])
    if open_ and state["status"] in ("ok", "cap", "resting", "error") and state["posts"]:
        if not led.get("since"):
            led["since"] = now.isoformat()
        state.setdefault("log", [])
        for t in decide(bot, state["read"], state["posts"], led, quotes, now):
            state["log"] = (state["log"] + [t])[-50:]
    bench = BENCH[bot["market"]]
    extra = [x for x in (bot.get("ref"), bench) if x]
    px_x = _index_px(extra, quotes_fn)
    px = {s: q[0] for s, q in quotes.items() if q and q[0]}
    px.update({k: v for k, v in px_x.items() if v})
    mark(led, px, now, px.get(bench))
    # the log (its own row): this run's line, the day's signals, the moves that followed; the verdict and the metrics
    if token:
        try:
            log, log_row = load(LOG + bot["id"])
        except Exception:
            log, log_row = None, None
        log = log or new_log(now)
        log_reading(log, bot, state["read"], px, now, open_ and state["status"] != "no_key")
        fill_moves(log, bot["market"], now, closes_fn)
        state["_log"], state["_log_row"] = log, log_row
        state["score"] = scorecard(bot, log["sig"])
        state["log_meta"] = {"since": log["since"], "hours": len(log["hourly"]), "days": len({x["d"] for x in log["sig"]}),
                             "signals": len(log["sig"]), "known": sum(1 for x in log["sig"] if x.get("r1") is not None)}
    state["perf"] = perf(led, state.get("reads"))
    state["updated"] = now.isoformat()
    return state


def _index_px(syms, quotes_fn=None):
    """{symbol: price now} for indices and other symbols the batch quotes leave out (TASI, SPY)."""
    if quotes_fn:
        try:
            return {s: q[0] for s, q in quotes_fn(syms).items() if q and q[0]}
        except Exception:
            return {}
    import data
    try:
        df = data.quotes_df(list(syms))
        return {r["Symbol"]: float(r["Price"]) for _, r in df.iterrows() if pd.notna(r.get("Price"))} if not df.empty else {}
    except Exception:
        return {}


def _quotes(syms):
    """{symbol: (price, % change today)} from the site's quotes."""
    import data
    try:
        return {s: (float(p), float(c)) for s, (p, c) in data.quick_changes(syms).items() if p is not None and pd.notna(p) and c is not None}
    except Exception:
        return {}


def save_state(bot, state):
    row = state.pop("_row", None)
    log, log_row = state.pop("_log", None), state.pop("_log_row", None)
    save(KEY + bot["id"], state, row)
    if log is not None:
        save(LOG + bot["id"], log, log_row)


def load_log(bot_id):
    """The bot's log (or an empty one)."""
    try:
        log, _ = load(LOG + bot_id)
    except Exception:
        log = None
    return log or {"since": None, "hourly": [], "sig": []}


# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "23.2"
