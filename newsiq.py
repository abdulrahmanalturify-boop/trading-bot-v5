"""
newsiq.py - News intelligence: keywords + an importance score from 1 to 10 for every headline.
10 = very important (red), 1 = not important (green). Transparent rules, no paid AI service:
topic weight + market-moving events + source quality + how much the affected stocks moved + mega-caps + freshness
- clickbait / opinion pieces.
"""
import re
from collections import Counter

import pandas as pd

# (key, english, arabic, weight, pattern)
TOPICS = [
    ("fed", "Fed & rates", "الفيدرالي والفائدة", 3.0,
     r"\b(fed|federal reserve|fomc|powell|rate cuts?|rate hikes?|rate decision|interest rates?|monetary policy|dot plot|central bank)\b"),
    ("inflation", "Inflation", "التضخم", 3.0,
     r"\b(inflation|cpi|pce|consumer prices?|producer prices?|ppi|price index|disinflation)\b"),
    ("jobs", "Jobs", "الوظائف", 2.6, r"\b(jobs? (?:report|data|numbers)|payrolls?|nonfarm|unemployment|jobless claims?|labor market|hiring)\b"),
    ("economy", "Economy", "الاقتصاد", 2.4,
     r"\b(gdp|recession|economic growth|economy|slowdown|stagflation|soft landing|consumer spending|retail sales|consumer confidence)\b"),
    ("bonds", "Bonds & yields", "السندات والعوائد", 2.0, r"\b(treasur(?:y|ies)|bond yields?|yields?|10-year|2-year|bond market)\b"),
    ("trade", "Tariffs & trade", "الرسوم والتجارة", 2.6,
     r"\b(tariffs?|trade war|trade deal|trade talks|export controls?|sanctions?|import duties)\b"),
    ("geo", "Geopolitics", "الجيوسياسة", 2.4,
     r"\b(war|missiles?|invasion|military|conflict|ceasefire|geopolitic\w*|israel|iran|ukraine|russia|taiwan|middle east|red sea)\b"),
    ("policy", "Policy & politics", "السياسة والحكومة", 1.8,
     r"\b(white house|congress|senate|election|shutdown|debt ceiling|stimulus|budget|tax bill|tax cuts?|executive order|trump|administration)\b"),
    ("earnings", "Earnings", "الأرباح", 2.4,
     r"\b(earnings|quarterly results|results|q[1-4]|eps|revenue|profits?|deliveries|beats? estimates|miss(?:es|ed)? estimates|tops? estimates)\b"),
    ("guidance", "Guidance", "التوقعات المستقبلية", 2.0,
     r"\b(guidance|outlook|forecasts?|raises? (?:its )?(?:full-year|annual)|cuts? (?:its )?(?:forecast|outlook))\b"),
    ("mna", "M&A", "استحواذ واندماج", 2.6,
     r"\b(mergers?|acquisitions?|acquires?|acquired|buyout|takeover|deal to buy|agrees? to buy|bid for|spin-?off)\b"),
    ("ipo", "IPO", "طرح عام أولي", 1.6, r"\b(ipo|initial public offering|goes public|direct listing|market debut)\b"),
    ("legal", "Legal & regulatory", "قضايا وتنظيم", 2.0,
     r"\b(sec|lawsuit|sued|sues|probe|investigation|antitrust|doj|ftc|faa|fined|settlement|charged|fraud|regulators?|recalls?|recalled)\b"),
    ("health", "FDA & health", "الدواء والصحة", 2.0, r"\b(fda|clinical trial|phase [123]|drug approval|approves|vaccine)\b"),
    ("distress", "Bankruptcy risk", "خطر الإفلاس", 3.0,
     r"\b(bankrupt\w*|chapter 11|defaults?|defaulted|insolven\w*|delist\w*|going concern)\b"),
    ("layoffs", "Layoffs", "تسريح موظفين", 1.6, r"\b(layoffs?|job cuts|cuts? [\d,]+ jobs|restructuring)\b"),
    ("product", "Products & launches", "منتجات وإطلاقات", 1.2,
     r"\b(unveils?|unveiled|launch(?:es|ed)?|rolls? out|new models?|iphone|product event)\b"),
    ("payout", "Dividends & buybacks", "التوزيعات وإعادة الشراء", 1.2, r"\b(dividends?|buybacks?|share repurchases?|stock split)\b"),
    ("analyst", "Analyst ratings", "تصنيفات المحللين", 1.2,
     r"\b(upgrades?|downgrades?|upgraded|downgraded|price target|initiates? coverage|overweight|underweight|outperform)\b"),
    ("ai", "AI & chips", "الذكاء الاصطناعي والرقائق", 1.4,
     r"\b(ai|artificial intelligence|chips?|chipmakers?|semiconductors?|gpus?|data cent(?:er|re)s?|openai)\b"),
    ("crypto", "Crypto", "العملات الرقمية", 1.2, r"\b(bitcoin|crypto\w*|ether(?:eum)?|stablecoins?|btc|blockchain)\b"),
    ("oil", "Oil & energy", "النفط والطاقة", 1.8, r"\b(oil|crude|opec\+?|brent|wti|natural gas|gasoline)\b"),
    ("metals", "Gold & commodities", "الذهب والسلع", 1.2, r"\b(gold|silver|copper|commodit\w*)\b"),
    ("fx", "Dollar & FX", "الدولار والعملات", 1.2, r"\b(dollar|currenc\w*|yen|euro|yuan|forex)\b"),
    ("move", "Big move", "حركة قوية", 1.4,
     r"\b(record highs?|all-time highs?|plunges?|plunged|soars?|soared|surges?|surged|tumbles?|tumbled|crash(?:es|ed)?|sell-?off|"
     r"slumps?|slumped|skyrockets?|sinks?|sank|jumps?|jumped|rall(?:y|ies|ied)|rebounds?|rebounded|slides?|slid)\b"),
    ("street", "Wall Street", "وول ستريت", 0.8, r"(\bs&p 500\b|\bnasdaq\b|\bdow jones\b|\bwall street\b|\bstock market\b|\bstocks\b|\bequities\b)"),
]
_TOPICS = [(k, en, ar, w, re.compile(p, re.I)) for k, en, ar, w, p in TOPICS]
TOPIC_ICON = {"fed": "account_balance", "inflation": "trending_up", "jobs": "work", "economy": "public", "bonds": "percent",
              "trade": "local_shipping", "geo": "travel_explore", "policy": "gavel", "earnings": "request_quote", "guidance": "insights",
              "mna": "handshake", "ipo": "rocket_launch", "legal": "balance", "health": "medication", "distress": "warning",
              "layoffs": "person_remove", "payout": "payments", "analyst": "thumbs_up_down", "ai": "memory", "crypto": "currency_bitcoin",
              "oil": "oil_barrel", "product": "new_releases", "metals": "diamond", "fx": "currency_exchange", "move": "bolt", "street": "show_chart", "opinion": "chat"}

# names worth showing as keywords (people, countries, institutions)
ENTITIES = [("Powell", "باول", r"\bpowell\b"), ("Trump", "ترامب", r"\btrump\b"), ("China", "الصين", r"\b(china|chinese|beijing)\b"),
            ("Europe", "أوروبا", r"\b(europe|european|eu|ecb)\b"), ("Japan", "اليابان", r"\b(japan|japanese|boj)\b"),
            ("OPEC", "أوبك", r"\bopec\+?\b"), ("Musk", "ماسك", r"\bmusk\b"), ("Buffett", "بافيت", r"\b(buffett|berkshire)\b"),
            ("Nvidia", "إنفيديا", r"\bnvidia\b"), ("Apple", "أبل", r"\bapple\b"), ("Microsoft", "مايكروسوفت", r"\bmicrosoft\b"),
            ("Tesla", "تسلا", r"\btesla\b"), ("Amazon", "أمازون", r"\bamazon\b"), ("Alphabet", "ألفابت", r"\b(alphabet|google)\b"),
            ("Meta", "ميتا", r"\bmeta\b"), ("OpenAI", "أوبن إيه آي", r"\bopenai\b"), ("Treasury", "وزارة الخزانة", r"\btreasury secretary\b")]
_ENT = [(en, ar, re.compile(p, re.I)) for en, ar, p in ENTITIES]

# market-moving events in the headline itself (decisions, data releases, deals)
EVENTS = re.compile(
    r"(\b(?:cuts?|hikes?|raises?|holds?|keeps?|leaves?|lowers?) (?:interest )?rates?\b|\brates? (?:unchanged|steady|decision)\b|"
    r"\b(?:cpi|inflation|pce|payrolls|jobs report|gdp|unemployment|jobless claims)\b.{0,50}\b(?:rose|rises|fell|falls|jumped|jumps|cooled|cools|"
    r"heated|hotter|cooler|beat|beats|missed|misses|came in|accelerat\w*|slow\w*|surged|slid|unexpectedly)\b|"
    r"\bopec\+? (?:agrees?|cuts?|raises?|decides?|boosts?)\b|\b(?:files?|filed) for (?:bankruptcy|chapter 11)\b|"
    r"\b(?:agrees? to (?:buy|acquire)|to acquire|in talks to (?:buy|acquire))\b|\bguidance (?:cut|raise)\b|\b(?:raises|cuts|lowers) (?:its )?(?:guidance|outlook|forecast)\b)",
    re.I)
OPINION = re.compile(
    r"(\bshould you buy\b|\bis it time to buy\b|\bbetter buy\b|\bcould make you\b|\bmillionaire\b|\bstocks? to buy\b|\bbuy and hold\b|"
    r"\bno-brainer\b|\bbuy now\b|\bstock a buy\b|\bprediction\b|\bhere's why\b|\bwhat to know\b|\bi'd buy\b|\bi would buy\b|\btop \d+\b|\b\d+ (?:top |best |great )?"
    r"(?:stocks?|dividend stocks?|etfs?|reasons)\b|\bforever\b|\bretire\w*\b|\bpassive income\b|\bmotley\b|\bshould you\b|\bgrowth stocks? to\b)",
    re.I)

SOURCES = [(1.0, ("reuters", "bloomberg", "wall street journal", "wsj", "associated press", "financial times", "cnbc", "barron",
                  "marketwatch", "new york times", "dow jones", "the economist", "axios", "ap news")),
           (0.4, ("yahoo finance", "investopedia", "business insider", "fortune", "forbes", "investor's business daily", "thestreet",
                  "the information", "techcrunch", "politico")),
           (-1.0, ("motley fool", "investorplace", "insider monkey")),
           (-0.8, ("zacks", "simply wall", "gurufocus", "24/7 wall", "benzinga insights", "stocktwits", "kiplinger")),
           (1.0, ("federal reserve", "bls", "sec")),
           (0.3, ("benzinga", "nasdaq", "investing.com", "fox business", "seeking alpha", "coindesk", "pr newswire", "globenewswire",
                  "cointelegraph"))]
MEGA = {"AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "AVGO", "TSLA", "BRK-B", "JPM", "LLY", "V", "MA", "UNH", "XOM", "WMT",
        "ORCL", "NFLX", "COST", "JNJ", "PG", "HD", "BAC", "ABBV", "KO", "PLTR", "AMD", "CRM", "TSM", "SPY", "QQQ"}

LEVELS = [(9, "Very important", "هام جداً"), (7, "Important", "هام"), (5, "Medium", "متوسط الأهمية"), (3, "Low", "منخفض الأهمية"),
          (1, "Not important", "غير هام")]
# score -> (light box, dark text, border): 1 green ... 5 yellow ... 10 red (the pastel rule)
COLORS = {1: ("#D1E7DD", "#0F5132", "#A3CFBB"), 2: ("#DCEEDA", "#1C5A2B", "#B3D8AE"), 3: ("#E6F2D3", "#355E12", "#C4DF9E"),
          4: ("#F0F3CE", "#545A0F", "#DBE29A"), 5: ("#FEF3C7", "#854D0E", "#F4DB8B"), 6: ("#FEE8C3", "#8A4A0B", "#F5CD8A"),
          7: ("#FFE2CB", "#9A3412", "#F6C09A"), 8: ("#FCD8CE", "#9A2B1B", "#F1AF9C"), 9: ("#F9D1D4", "#8C1D27", "#EDA3AB"),
          10: ("#F5C0C6", "#6B111A", "#E1858F")}


def level(score):
    for lo, en, ar in LEVELS:
        if score >= lo:
            return en, ar
    return LEVELS[-1][1:]


def colors(score):
    return COLORS[max(1, min(10, int(score)))]


def _source_weight(src):
    s = (src or "").lower()
    for w, names in SOURCES:
        if any(n in s for n in names):
            return w
    return 0.0


def analyze(n, chg=None, now=None):
    """-> {"score": 1..10, "raw": float, "keywords": [(key, en, ar)], "reasons": [(en, ar, +w)], "topics": [key]}"""
    title = str(n.get("title") or "")
    summ = str(n.get("summary") or "")[:500]
    tickers = [t for t in (n.get("tickers") or []) if t]
    hits = []
    for key, en, ar, w, pat in _TOPICS:
        if pat.search(title):
            hits.append((w, key, en, ar))
        elif summ and pat.search(summ):
            hits.append((w * 0.6, key, en, ar))
    hits.sort(key=lambda h: -h[0])
    reasons = []
    topic = 0.0
    for i, (w, key, en, ar) in enumerate(hits[:3]):
        part = w * (1.0, 0.5, 0.25)[i]
        topic += part
    topic = min(topic, 4.6)
    if hits:
        reasons.append((hits[0][2], hits[0][3], round(topic, 1)))
    event = 2.0 if EVENTS.search(title) else 0.0
    if event:
        reasons.append(("Market-moving event", "حدث مؤثر في السوق", event))
    opinion = -2.2 if OPINION.search(title) else 0.0
    if opinion:
        reasons.append(("Opinion / list article", "مقال رأي أو قائمة", opinion))
    src = _source_weight(n.get("source"))
    if src:
        reasons.append((str(n.get("source") or ""), str(n.get("source") or ""), src))
    impact, mx = 0.0, 0.0
    if chg and tickers:
        moves = [abs(chg[s][1]) for s in tickers if s in chg and chg[s][1] is not None and pd.notna(chg[s][1])]
        mx = max(moves) if moves else 0.0
        impact = 2.2 if mx >= 8 else 1.8 if mx >= 5 else 1.2 if mx >= 3 else 0.6 if mx >= 1.5 else 0.0
        if impact:
            reasons.append((f"Stock moved {mx:.1f}% today", f"السهم تحرك {mx:.1f}% اليوم", impact))
    mega = 0.8 if any(s in MEGA for s in tickers) else 0.0
    if mega:
        reasons.append(("Mega-cap company", "شركة عملاقة", mega))
    breadth = 0.4 if len(tickers) >= 3 else 0.0
    if breadth:
        reasons.append(("Several companies affected", "عدة شركات متأثرة", breadth))
    k = len(n.get("also") or [])                  # the news bot found the same story at other outlets
    wide = min(1.5, 0.5 * k)
    if wide:
        reasons.append((f"Covered by {k + 1} outlets", f"نشرته {k + 1} مصادر إخبارية", wide))
    rec = 0.0
    ts = n.get("time")
    if ts is not None and pd.notna(ts):
        now = now or pd.Timestamp.now(tz="UTC")
        try:
            age = (now - ts).total_seconds() / 3600
        except (TypeError, ValueError):
            age = None
        if age is not None:
            rec = 0.6 if age < 2 else 0.3 if age < 6 else 0.0 if age < 24 else -0.6 if age < 72 else -1.5
            if rec > 0:
                reasons.append(("Fresh news", "خبر حديث", rec))
            elif rec < 0:
                reasons.append(("Older story", "خبر قديم", rec))
    raw = 2.0 + topic + event + opinion + src + impact + mega + breadth + wide + rec
    score = int(max(1, min(10, round(raw))))
    kws = [(key, en, ar) for _, key, en, ar in hits[:4] if key != "street" or len(hits) == 1]
    for en, ar, pat in _ENT:
        if len(kws) >= 6:
            break
        if pat.search(title) and not any(en == k[1] for k in kws):
            kws.append(("entity", en, ar))
    if opinion:
        kws.append(("opinion", "Opinion", "رأي"))
    return {"score": score, "raw": raw, "keywords": kws, "reasons": reasons, "topics": [h[1] for h in hits], "move": mx}


def enrich(items, chg=None):
    """Adds n["iq"] to every item (once)."""
    now = pd.Timestamp.now(tz="UTC")
    for n in items:
        if "iq" not in n:
            n["iq"] = analyze(n, chg, now)
    return items


def top_keywords(items, k=12):
    """Most frequent keywords across headlines: [((key, en, ar), count)]"""
    c = Counter()
    for n in items:
        for kw in (n.get("iq") or {}).get("keywords", []):
            if kw[0] != "opinion":
                c[kw] += 1
    return c.most_common(k)


def rank(items):
    """Most important first, newest first among equal scores."""
    zero = pd.Timestamp("1970-01-01", tz="UTC")
    return sorted(items, key=lambda n: ((n.get("iq") or {}).get("raw", 0), n["time"] if pd.notna(n.get("time")) else zero), reverse=True)

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "7.4"
