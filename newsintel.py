"""
newsintel.py - The News Intelligence Engine: every headline of the news bot read from several angles, then set against the
price. Three levels:
  1. News Scanner  - the news bot (newsbot.py: ~35 feeds, duplicates merged, companies detected) + the importance score of
                     newsiq.py.
  2. News Analyst  - what kind of event it is, its sentiment (bullish / bearish / neutral), how material it is, its impact
                     0-100, its time horizon, the companies hit directly and indirectly, the sectors, the confidence, whether
                     it is new and whether the stock moved before it.
  3. Setup engine  - the news set against momentum, volume, trend and the market regime: a score out of 100 with its parts,
                     and a trading scenario with its levels. Transparent rules decide; a language model (when the site has an
                     AI key) only explains a story, it never trades.
Everything here is rules and numbers (no paid service); the page is p_newsintel.py.
"""
import re

import numpy as np
import pandas as pd

import newsiq
import universe as U

try:
    import sp500 as SP
    _SP = SP.SP500
except Exception:                       # pragma: no cover
    SP, _SP = None, {}

# ---------------------------------------------------------------- 1) what kind of event
# key, english, arabic, icon, time horizon, pattern (the first that matches the headline wins; then the summary)
EVENTS = [
    ("distress", "Bankruptcy risk", "خطر إفلاس", "warning", "long",
     r"\b(bankrupt\w*|chapter 11|defaults? on|defaulted|insolven\w*|going concern|delist\w*)\b"),
    ("mna", "Merger & Acquisition (M&A)", "استحواذ واندماج", "handshake", "long",
     r"\b(mergers?|acquisitions?|acquires?|acquired|buyout|takeover|deal to buy|agrees? to (?:buy|acquire)|to acquire|bid for|spin-?offs?|"
     r"merge with|combine with)\b"),
    ("earnings", "Earnings", "نتائج الأرباح", "request_quote", "days",
     r"\b(earnings|quarterly (?:results|profit|revenue|loss)|q[1-4] (?:results|profit|revenue|earnings|sales)|eps\b|(?:beats?|tops?|miss(?:es)?) "
     r"(?:estimates|expectations|forecasts)|reports? (?:a )?(?:quarterly )?(?:profit|loss|revenue)|deliveries)\b"),
    ("guidance", "Guidance", "التوقعات المستقبلية", "insights", "weeks",
     r"\b(guidance|outlook|forecasts?|raises? (?:its )?(?:full-year|annual|sales|revenue|profit)|cuts? (?:its )?(?:full-year|annual|forecast|outlook)|"
     r"warns? (?:on|of) (?:sales|profit|revenue))\b"),
    ("regulation", "Regulation", "تنظيم وقيود", "gavel", "weeks",
     r"\b(regulat\w*|export (?:controls?|curbs|restrictions?)|restrictions?|bans?|banned|antitrust|ftc|doj|sec (?:charges|probe|investigation)|"
     r"probe|investigation|fda (?:approv\w*|reject\w*|clear\w*)|approv(?:al|es|ed) by|cleared by|fined|penalty|sanctions?)\b"),
    ("lawsuit", "Lawsuit", "قضية قانونية", "balance", "long",
     r"\b(lawsuits?|sued|sues|class action|verdict|jury|court (?:rules|ruling)|settle(?:s|d|ment)|litigation)\b"),
    ("management", "Management change", "تغيير في الإدارة", "badge", "weeks",
     r"\b(ceo|cfo|coo|chief executive|chief financial|chairman|steps? down|resigns?|resignation|appoints?|appointed|names? new|"
     r"successor|to retire|ousted|board shake-?up)\b"),
    ("contract", "Contract win", "فوز بعقد", "contract", "days",
     r"\b(contracts?|wins? (?:a |an )?(?:deal|order|bid)|awarded|partnership|partners with|teams up|supply (?:deal|agreement)|order from|"
     r"deal with|agreement with|selected by)\b"),
    ("analyst", "Analyst rating", "تصنيف المحللين", "thumbs_up_down", "intraday",
     r"\b(upgrades?|upgraded|downgrades?|downgraded|price targets?|initiates? coverage|overweight|underweight|outperform|underperform|"
     r"buy rating|sell rating|neutral rating)\b"),
    ("offering", "Share offering", "طرح أسهم جديدة", "call_split", "days",
     r"\b((?:stock|share|equity) (?:offering|sale)|secondary offering|private placement|convertible (?:notes|bonds)|raises \$[\d.]+ ?(?:m|b|million|billion))\b"),
    ("payout", "Dividend or buyback", "توزيعات أو إعادة شراء", "payments", "weeks",
     r"\b(buybacks?|share repurchases?|repurchase program|(?:raises|hikes|boosts|increases|cuts|suspends) (?:its )?(?:quarterly )?dividend|"
     r"special dividend|dividend (?:hike|increase|cut))\b"),
    ("restructuring", "Layoffs & restructuring", "تسريح وإعادة هيكلة", "person_remove", "weeks",
     r"\b(layoffs?|lays? off|job cuts|cuts? [\d,]+ jobs|restructuring|plant closures?|closing (?:plants|stores))\b"),
    ("product", "Product launch", "إطلاق منتج", "new_releases", "weeks",
     r"\b(launch(?:es|ed)?|unveils?|unveiled|introduces?|rolls? out|debuts?|new (?:chip|model|product|device|service|ai model)|recalls?|recalled)\b"),
    ("macro", "Macro news", "أخبار الاقتصاد الكلي", "public", "days",
     r"\b(fed|federal reserve|fomc|powell|rate cuts?|rate hikes?|interest rates?|inflation|cpi|pce|payrolls|jobs report|nonfarm|unemployment|"
     r"jobless claims|gdp|recession|treasury yields?|bond yields?|10-year|tariffs?|trade war|opec\+?|oil prices?|crude|dollar|retail sales|"
     r"consumer (?:confidence|sentiment|prices)|ism|pmi|housing starts|central bank|ecb|boj)\b"),
]
_EV = [(k, en, ar, ic, hz, re.compile(p, re.I)) for k, en, ar, ic, hz, p in EVENTS]
EVENT = {k: (en, ar, ic, hz) for k, en, ar, ic, hz, _ in _EV}
EVENT["other"] = ("Company news", "خبر شركة", "article", "days")
EVENT["market"] = ("Market news", "خبر السوق", "show_chart", "days")
HORIZON = {"intraday": ("Intraday", "خلال اليوم"), "days": ("Days", "أيام"), "weeks": ("Weeks", "أسابيع"), "long": ("Long-Term", "طويل المدى")}
# how much an event of this kind usually matters for the stock (materiality, before the story itself)
EVENT_WEIGHT = {"distress": 3.0, "mna": 2.6, "earnings": 2.4, "guidance": 2.2, "regulation": 1.8, "lawsuit": 1.2, "management": 1.2,
                "contract": 1.2, "analyst": 0.8, "offering": 1.4, "payout": 1.0, "restructuring": 1.0, "product": 0.9, "macro": 1.6,
                "other": 0.3, "market": 0.6}


def classify(title, summary=""):
    """The kind of event (key); the headline decides first, then the summary."""
    for text in (title or "", (summary or "")[:500]):
        for k, en, ar, ic, hz, pat in _EV:
            if pat.search(text):
                return k
    return "other"


# ---------------------------------------------------------------- 2) sentiment
POS = [r"beats?", r"tops?", r"surg\w+", r"soar\w*", r"jump\w*", r"ris(?:e|es|ing)", r"rall(?:y|ies|ied)", r"record(?: high)?", r"gains?",
       r"rais(?:e|es|ed) (?:its )?(?:guidance|forecast|outlook|dividend)", r"upgrad\w+", r"approv\w+", r"clear(?:s|ed) by", r"wins?", r"awarded",
       r"expand\w*", r"strong(?:er)?", r"better-than-expected", r"above (?:estimates|expectations)", r"boost\w*", r"buybacks?", r"repurchase",
       r"partnership", r"breakthrough", r"profit(?:able)?", r"growth", r"rebound\w*", r"bullish", r"outperform\w*", r"overweight", r"higher",
       r"accelerat\w+", r"exceed\w*", r"optimis\w+", r"deal to buy", r"premium", r"recovers?", r"upbeat", r"robust", r"cuts? rates", r"rate cuts?",
       r"cool(?:s|ed|ing)", r"eases?", r"easing", r"lifts?", r"climbs?"]
NEG = [r"miss(?:es|ed)?", r"fall(?:s|ing)?", r"fell", r"plung\w+", r"drops?", r"dropped", r"slump\w*", r"sinks?", r"sank", r"tumbl\w+",
       r"(?:cuts?|lowers?|slashes) (?:its )?(?:guidance|forecast|outlook|dividend)", r"downgrad\w+", r"lawsuits?", r"sued", r"probe",
       r"investigation", r"recalls?", r"restrictions?", r"curbs?", r"bans?", r"banned", r"delays?", r"delayed", r"layoffs?", r"weak(?:er|ness)?",
       r"worse-than-expected", r"below (?:estimates|expectations)", r"loss(?:es)?", r"declin\w+", r"warns?", r"warning", r"bankrupt\w*",
       r"defaults?", r"fined", r"penalt\w+", r"halt\w*", r"bearish", r"concerns?", r"slow(?:s|ed|down|ing)", r"shortfall", r"resigns?",
       r"steps? down", r"dilut\w+", r"offering", r"underperform\w*", r"underweight", r"lower", r"fears?", r"crash\w*", r"sell-?off", r"tariffs?",
       r"sanctions?", r"hotter", r"accelerat\w+ inflation", r"rate hikes?", r"hikes? rates", r"short sellers?", r"fraud", r"slides?", r"slid",
       r"cuts? (?:[\d,]+ )?jobs", r"disappoint\w*", r"downbeat", r"plummet\w*"]
_POS = re.compile(r"\b(" + "|".join(POS) + r")\b", re.I)
_NEG = re.compile(r"\b(" + "|".join(NEG) + r")\b", re.I)
_NOT = re.compile(r"\b(not|no|without|fails? to|unlikely to)\b", re.I)
# the usual sign of an event before its words are read (a downgrade is bearish, a buyback bullish, ...)
EVENT_PRIOR = {"distress": -0.6, "lawsuit": -0.35, "offering": -0.35, "restructuring": -0.1, "payout": 0.3, "contract": 0.3,
               "regulation": -0.25}
SENT = {"bull": ("Bullish", "صاعد", "#4ADE80"), "bear": ("Bearish", "هابط", "#F87171"), "neutral": ("Neutral", "محايد", "#C4B5FD")}


def sentiment(title, summary="", event="other"):
    """(-1..1 score, 'bull' | 'bear' | 'neutral', words found). The headline counts twice as much as the summary."""
    t, s = title or "", (summary or "")[:500]
    pos_w = [m.group(0) for m in _POS.finditer(t)]
    neg_w = [m.group(0) for m in _NEG.finditer(t)]
    p = len(pos_w) * 2.0 + len(_POS.findall(s)) * 0.7
    n = len(neg_w) * 2.0 + len(_NEG.findall(s)) * 0.7
    if _NOT.search(t) and p > n:               # "fails to beat", "no approval" turns a positive headline
        p, n = n, p
    score = (p - n) / (p + n + 2.0) + EVENT_PRIOR.get(event, 0.0)
    if event == "analyst":
        if re.search(r"upgrad\w+|outperform|overweight|buy rating|raises? price target", t, re.I):
            score += 0.35
        if re.search(r"downgrad\w+|underperform|underweight|sell rating|cuts? price target|lowers? price target", t, re.I):
            score -= 0.35
    if event == "regulation" and re.search(r"approv\w+|clear(?:s|ed)|wins? approval", t, re.I):
        score += 0.45
    if event == "macro":                        # the market's usual reading of the macro news (a hot inflation print is bad news)
        mk = macro_kind(t, s)
        if mk:
            score += MACRO_SIGN.get(mk[0], 0.0)
    score = float(np.clip(score, -1, 1))
    lab = "bull" if score > 0.15 else "bear" if score < -0.15 else "neutral"
    return score, lab, pos_w + neg_w


# ---------------------------------------------------------------- 3) companies: direct and indirect
# known links beyond the same industry: suppliers, customers, the closest rivals (a short, hand-kept list for the biggest names)
LINKS = {
    "NVDA": ["TSM", "AMD", "AVGO", "MU", "ASML", "SMCI"], "AMD": ["NVDA", "INTC", "TSM", "AVGO"], "INTC": ["AMD", "NVDA", "TSM", "QCOM"],
    "TSM": ["NVDA", "AAPL", "AMD", "AVGO", "ASML"], "AVGO": ["NVDA", "AAPL", "MRVL", "QCOM"], "MU": ["NVDA", "WDC", "STX", "AMAT"],
    "AAPL": ["TSM", "AVGO", "QCOM", "SWKS", "GOOGL"], "MSFT": ["NVDA", "GOOGL", "AMZN", "ORCL", "CRM"], "GOOGL": ["META", "MSFT", "AMZN", "NVDA"],
    "AMZN": ["WMT", "MSFT", "GOOGL", "SHOP", "UPS"], "META": ["GOOGL", "SNAP", "PINS", "NVDA"], "TSLA": ["RIVN", "GM", "F", "ALB", "LCID"],
    "NFLX": ["DIS", "WBD", "ROKU", "SPOT"], "ORCL": ["MSFT", "AMZN", "CRM", "NVDA"], "CRM": ["MSFT", "ORCL", "NOW", "ADBE"],
    "JPM": ["BAC", "WFC", "C", "GS", "MS"], "XOM": ["CVX", "COP", "OXY", "SLB"], "LLY": ["NVO", "MRK", "PFE", "ABBV"],
    "UNH": ["CVS", "CI", "ELV", "HUM"], "BA": ["LMT", "RTX", "GE", "SPR"], "WMT": ["COST", "TGT", "AMZN", "KR"],
    "PLTR": ["SNOW", "MSFT", "CRM", "NOW"], "SMCI": ["NVDA", "DELL", "HPE", "AMD"], "COIN": ["HOOD", "MSTR", "SQ"],
}


def company(sym):
    """(name, sector, industry) for a symbol the site knows."""
    if sym in _SP:
        n, sec, sub = _SP[sym]
        return n, sec, sub
    if U.known(sym):
        return U.name_of(sym), U.sector_of(sym), U.industry_of(sym)
    return sym, "", ""


def _mcap(sym):
    rec = U.STOCKS.get(sym)
    return rec[3] if rec and len(rec) > 3 else 0


def peers(sym, k=5, exclude=()):
    """Companies a story about sym can hit indirectly: its known links first, then the largest of its own GICS sub-industry."""
    out = [s for s in LINKS.get(sym, []) if s != sym and s not in exclude]
    sub = _SP.get(sym, (None, None, None))[2]
    if sub:
        same = [s for s, v in _SP.items() if v[2] == sub and s != sym and s not in exclude and s not in out]
        same.sort(key=lambda s: -_mcap(s))
        out += same
    return list(dict.fromkeys(out))[:k]


# ---------------------------------------------------------------- 4) macro news: how each sector usually takes it
# a rule of thumb of how a sector tends to react (+2 helped a lot .. -2 hurt a lot); the page shows next to it how each sector
# ETF actually moved today, so the rule is checked against the market
MACRO = [
    ("cut", "Rate cut / dovish Fed", "خفض الفائدة / فيدرالي متساهل",
     r"\b(cuts? (?:interest )?rates?|rate cuts?|lowers? rates|dovish|eas(?:es|ing) (?:policy|rates))\b",
     {"Real Estate": 2, "Utilities": 2, "Technology": 2, "Consumer Cyclical": 1, "Communication Services": 1, "Basic Materials": 1,
      "Industrials": 1, "Healthcare": 0, "Consumer Defensive": 0, "Energy": 0, "Financial Services": -1}),
    ("hike", "Rate hike / hawkish Fed", "رفع الفائدة / فيدرالي متشدد",
     r"\b(hikes? (?:interest )?rates?|rate hikes?|raises? rates|hawkish|higher for longer|tighten\w*)\b",
     {"Real Estate": -2, "Utilities": -2, "Technology": -2, "Consumer Cyclical": -1, "Communication Services": -1, "Basic Materials": -1,
      "Industrials": -1, "Healthcare": 0, "Consumer Defensive": 0, "Energy": 0, "Financial Services": 1}),
    ("infl_hot", "Hot inflation", "تضخم مرتفع",
     r"\b(?:inflation|cpi|pce|consumer prices|producer prices)\b.{0,60}\b(hotter|rises?|rose|jumps?|jumped|accelerat\w+|higher than|above|surges?|heats)\b",
     {"Technology": -2, "Real Estate": -2, "Utilities": -1, "Consumer Cyclical": -1, "Communication Services": -1, "Consumer Defensive": 0,
      "Healthcare": 0, "Industrials": 0, "Financial Services": 1, "Energy": 2, "Basic Materials": 1}),
    ("infl_cool", "Cooling inflation", "تضخم يهدأ",
     r"\b(?:inflation|cpi|pce|consumer prices|producer prices)\b.{0,60}\b(cool\w*|eases?|eased|slows?|slowed|falls?|fell|lower than|below|softer)\b",
     {"Technology": 2, "Real Estate": 2, "Utilities": 1, "Consumer Cyclical": 1, "Communication Services": 1, "Consumer Defensive": 0,
      "Healthcare": 0, "Industrials": 1, "Financial Services": 0, "Energy": -1, "Basic Materials": 0}),
    ("jobs_weak", "Weak jobs data", "بيانات وظائف ضعيفة",
     r"\b(?:payrolls|jobs report|jobless claims|unemployment|hiring|labor market)\b.{0,60}\b(weak\w*|miss\w*|falls?|fell|slows?|slowed|rises?|jumps?|cool\w*)\b",
     {"Consumer Defensive": 1, "Utilities": 1, "Healthcare": 1, "Real Estate": 1, "Technology": 0, "Financial Services": -1,
      "Consumer Cyclical": -1, "Industrials": -1, "Energy": -1, "Basic Materials": -1, "Communication Services": 0}),
    ("oil_up", "Oil prices up", "ارتفاع أسعار النفط",
     r"\b(oil|crude|brent|wti)\b.{0,50}\b(surges?|jumps?|rises?|rallies|climbs?|soars?|spikes?)\b|\bopec\+? (?:cuts?|agrees? to cut)\b",
     {"Energy": 2, "Basic Materials": 1, "Industrials": -1, "Consumer Cyclical": -1, "Consumer Defensive": -1, "Utilities": 0,
      "Technology": 0, "Healthcare": 0, "Financial Services": 0, "Real Estate": 0, "Communication Services": 0}),
    ("oil_down", "Oil prices down", "هبوط أسعار النفط",
     r"\b(oil|crude|brent|wti)\b.{0,50}\b(falls?|fell|drops?|slumps?|tumbles?|plunges?|slides?)\b|\bopec\+? (?:raises|boosts|increases) output\b",
     {"Energy": -2, "Basic Materials": -1, "Industrials": 1, "Consumer Cyclical": 1, "Consumer Defensive": 1, "Utilities": 0,
      "Technology": 0, "Healthcare": 0, "Financial Services": 0, "Real Estate": 0, "Communication Services": 0}),
    ("tariffs", "Tariffs & trade war", "رسوم جمركية وحرب تجارية",
     r"\b(tariffs?|trade war|import duties|export controls?)\b",
     {"Consumer Cyclical": -2, "Technology": -1, "Industrials": -1, "Basic Materials": -1, "Communication Services": 0,
      "Consumer Defensive": -1, "Energy": 0, "Healthcare": 0, "Utilities": 1, "Real Estate": 0, "Financial Services": 0}),
    ("yields_up", "Bond yields up", "ارتفاع عوائد السندات",
     r"\b(treasury|bond)? ?yields?\b.{0,40}\b(rise|rises|rose|jump\w*|climb\w*|surge\w*|spike\w*|hit \d+-(?:week|month|year) high)\b",
     {"Real Estate": -2, "Utilities": -2, "Technology": -1, "Consumer Cyclical": -1, "Financial Services": 1, "Energy": 0,
      "Basic Materials": 0, "Industrials": 0, "Healthcare": 0, "Consumer Defensive": -1, "Communication Services": -1}),
]
_MACRO = [(k, en, ar, re.compile(p, re.I), eff) for k, en, ar, p, eff in MACRO]
# how the stock market as a whole usually reads each kind (added to the words' sentiment)
MACRO_SIGN = {"cut": 0.45, "hike": -0.45, "infl_hot": -0.5, "infl_cool": 0.45, "jobs_weak": -0.1, "oil_up": -0.2, "oil_down": 0.15,
              "tariffs": -0.4, "yields_up": -0.35}


def macro_kind(title, summary=""):
    """(key, english, arabic, {sector: -2..2}) of a macro story, else None."""
    for text in (title or "", (summary or "")[:400]):
        for k, en, ar, pat, eff in _MACRO:
            if pat.search(text):
                return k, en, ar, eff
    return None


# ---------------------------------------------------------------- 5) the price around the story
def _ny_date(ts):
    try:
        t = pd.Timestamp(ts)
        t = t.tz_localize("UTC") if t.tzinfo is None else t
        return t.tz_convert("America/New_York").tz_localize(None).normalize()
    except Exception:
        return None


def price_facts(df, when=None):
    """Numbers of one stock from its daily prices: the last close, today's change, relative volume, ATR %, the averages,
    1-month and 5-day returns, today's range, and the move in the 3 sessions before the story's day. None when too short."""
    if df is None or len(df) < 30:
        return None
    df = df.dropna(subset=["Close"])
    c, h, l_, v = (df[k].astype(float) for k in ("Close", "High", "Low", "Volume"))
    prev = c.shift(1)
    tr = pd.concat([h - l_, (h - prev).abs(), (l_ - prev).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1])
    last = float(c.iloc[-1])
    vol20 = float(v.iloc[-21:-1].mean()) if len(v) > 21 else float(v.mean())
    sma = lambda n: float(c.rolling(n).mean().iloc[-1]) if len(c) >= n else None
    f = {"close": last, "chg": float(c.iloc[-1] / c.iloc[-2] - 1) * 100 if len(c) > 1 else 0.0,
         "rvol": float(v.iloc[-1] / vol20) if vol20 > 0 else None, "atr_pct": atr / last * 100 if last else None,
         "sma20": sma(20), "sma50": sma(50), "sma200": sma(200),
         "ret21": float(c.iloc[-1] / c.iloc[-22] - 1) * 100 if len(c) > 22 else None,
         "ret5": float(c.iloc[-1] / c.iloc[-6] - 1) * 100 if len(c) > 6 else None,
         "hi": float(h.iloc[-1]), "lo": float(l_.iloc[-1]), "pre": None}
    d = _ny_date(when) if when is not None else None
    if d is not None:
        idx = pd.DatetimeIndex(df.index)
        idx = idx.tz_convert("America/New_York").tz_localize(None) if idx.tz is not None else idx
        before = np.flatnonzero(idx.normalize() < d)
        if len(before) >= 4:
            i = before[-1]
            f["pre"] = float(c.iloc[i] / c.iloc[i - 3] - 1) * 100            # the 3 sessions before the story's day
    return f


def regime(spy):
    """'bull' | 'bear' | 'mixed' from the S&P 500 (SPY): above / below its 200-day average, and the 50-day against the 200-day."""
    f = price_facts(spy)
    if not f or not f["sma200"] or not f["sma50"]:
        return "mixed"
    up = f["close"] > f["sma200"]
    trend = f["sma50"] > f["sma200"]
    return "bull" if up and trend else "bear" if not up and not trend else "mixed"


REGIME = {"bull": ("Bull market", "سوق صاعد"), "bear": ("Bear market", "سوق هابط"), "mixed": ("Mixed market", "سوق متذبذب")}


# ---------------------------------------------------------------- 6) one story, read from every angle
def analyze(n, px=None, chg=None, spy_regime="mixed", now=None):
    """The whole reading of one headline (n: an item of the news bot with n["iq"] from newsiq). px: {symbol: daily prices}."""
    px, chg = px or {}, chg or {}
    now = now or pd.Timestamp.now(tz="UTC")
    title, summ = str(n.get("title") or ""), str(n.get("summary") or "")
    iq = n.get("iq") or newsiq.analyze(n, chg, now)
    tick = [t for t in (n.get("tickers") or []) if t and t not in ("SPY", "QQQ", "DIA", "IWM")][:4]
    ev = classify(title, summ)
    mk = macro_kind(title, summ) if (ev == "macro" or not tick) else None
    if not tick and mk:
        ev = "macro"
    elif not tick and ev == "other":
        ev = "market"
    s, lab, words = sentiment(title, summ, ev)
    main = tick[0] if tick else "SPY"                  # a story without a company is read on the whole market (the S&P 500)
    fa = price_facts(px.get(main), n.get("time"))
    if fa and main in chg and chg[main][1] is not None and pd.notna(chg[main][1]):
        fa["chg"] = float(chg[main][1])                 # today's change: the live quote (the daily bar can still be yesterday's)
    if fa is None and main and main in chg:
        fa = {"close": chg[main][0], "chg": chg[main][1], "rvol": None, "atr_pct": None, "sma20": None, "sma50": None, "sma200": None,
              "ret21": None, "ret5": None, "hi": None, "lo": None, "pre": None}
    # the price's own vote: a clear move today, measured in normal days (ATR)
    move = None
    if fa and fa.get("chg") is not None:
        a_ = fa.get("atr_pct") or 2.0
        move = fa["chg"] / max(a_, 0.3)
    if lab == "neutral" and move is not None and abs(move) >= 1.0:          # no clear words: the market's reaction says
        lab = "bull" if move > 0 else "bear"
        s = float(np.clip(0.25 * np.sign(move), -1, 1))
    d = 1 if lab == "bull" else -1 if lab == "bear" else 0
    # materiality 0-10: the importance score, the kind of event, the coverage, the volume
    mat = iq["score"] * 0.7 + EVENT_WEIGHT.get(ev, 0.5)
    if len(n.get("also") or []) >= 2:
        mat += 0.8
    if fa and fa.get("rvol") and fa["rvol"] >= 2:
        mat += 1.0
    if any(k[0] == "opinion" for k in iq.get("keywords", [])):
        mat -= 2.0
    mat = float(np.clip(mat, 0, 10))
    conf_price = 1.0
    if move is not None and d:
        conf_price = 1.2 if d * move >= 1 else 1.05 if d * move > 0.3 else 0.8 if d * move <= -0.5 else 1.0
    impact = float(np.clip(100 * (mat / 10) ** 0.85 * (0.55 + 0.45 * abs(s)) * conf_price, 0, 100))
    # confidence: the source, the coverage, the words, the price agreeing (or not)
    conf = 50 + 12 * max(0.0, newsiq._source_weight(n.get("source"))) + 6 * min(len(n.get("also") or []), 2)
    conf += 10 * min(abs(s) / 0.6, 1)
    if move is not None and d:
        conf += 14 if d * move >= 1 else 6 if d * move > 0.3 else -16 if d * move <= -0.5 else 0
    if tick and re.search(re.escape(company(main)[0].split()[0]), title, re.I):
        conf += 5
    conf = int(np.clip(conf, 20, 95))
    ts = n.get("time")
    age_h = (now - ts).total_seconds() / 3600 if ts is not None and pd.notna(ts) else None
    moved_before = None
    if fa and fa.get("pre") is not None and fa.get("atr_pct"):
        moved_before = abs(fa["pre"]) >= 1.5 * fa["atr_pct"]
    direct = tick
    indirect = peers(main, 5, exclude=direct) if tick else []
    secs = []
    for t in direct:
        _, sec, sub = company(t)
        if sec and (sec, sub) not in secs:
            secs.append((sec, sub))
    return {"n": n, "iq": iq, "event": ev, "macro": mk, "sent": s, "lab": lab, "words": words, "dir": d, "main": main, "facts": fa,
            "move": move, "materiality": mat, "impact": impact, "severity": int(round(impact / 10)), "confidence": conf,
            "horizon": EVENT[ev][3] if ev in EVENT else "days", "direct": direct, "indirect": indirect, "sectors": secs[:3],
            "age_h": age_h, "new": age_h is not None and age_h < 6, "moved_before": moved_before, "regime": spy_regime,
            "setup": setup(impact, d, fa, spy_regime)}


# ---------------------------------------------------------------- 7) the setup: the news against the price
PARTS = [("news", "News Impact", "أثر الخبر", 30), ("mom", "Momentum", "الزخم", 20), ("vol", "Volume", "حجم التداول", 20),
         ("trend", "Trend", "الاتجاه", 20), ("regime", "Market Regime", "حالة السوق", 10)]


def setup(impact, d, fa, spy_regime):
    """The setup's score out of 100 in the direction of the story (d: +1 bullish, -1 bearish, 0 none): each part adds when it
    agrees with that direction and takes away when it disagrees. {"parts": {key: points}, "total", "dir", "label"}."""
    parts = {k: 0.0 for k, *_ in PARTS}
    if not d:
        return {"parts": parts, "total": 0, "dir": 0, "label": ("No setup — the story has no clear direction", "لا توجد فرصة — الخبر بلا اتجاه واضح")}
    parts["news"] = 30 * impact / 100
    if fa:
        c = fa.get("close")
        r21, s20, s50, s200 = fa.get("ret21"), fa.get("sma20"), fa.get("sma50"), fa.get("sma200")
        if r21 is not None and c and s20:
            parts["mom"] = 20 * (0.6 * float(np.clip(d * r21 / 8.0, -1, 1)) + 0.4 * float(np.clip(d * (c / s20 - 1) / 0.03, -1, 1)))
        rv = fa.get("rvol")
        if rv is not None:
            strength = float(np.clip((rv - 1) / 2, 0, 1))
            agree = d * (fa.get("chg") or 0) >= 0
            parts["vol"] = 20 * strength * (1 if agree else -1)
        if c and s50:
            parts["trend"] += 10 * (1 if d * (c - s50) > 0 else -1)
        if s50 and s200:
            parts["trend"] += 10 * (1 if d * (s50 - s200) > 0 else -1)
    parts["regime"] = {"bull": 10, "bear": -10, "mixed": 0}[spy_regime] * d
    total = int(round(float(np.clip(sum(parts.values()), 0, 100))))
    side = ("Bullish", "صاعدة") if d > 0 else ("Bearish", "هابطة")
    if total >= 75:
        lab = (f"Strongly {side[0]} Setup", f"فرصة {side[1]} قوية")
    elif total >= 55:
        lab = (f"Moderately {side[0]} Setup", f"فرصة {side[1]} متوسطة")
    elif total >= 40:
        lab = (f"Weak {side[0]} Setup", f"فرصة {side[1]} ضعيفة")
    else:
        lab = ("No setup — the price does not confirm the story", "لا توجد فرصة — السعر ما يؤكد الخبر")
    return {"parts": {k: round(v, 1) for k, v in parts.items()}, "total": total, "dir": d, "label": lab}


def plan(a):
    """The trading scenario's levels (education: the rules above decide it, not a recommendation), or None when there is no
    setup or no prices: {"dir", "price", "trigger", "stop", "target", "risk_pct", "reward_pct"}."""
    st_, fa = a["setup"], a["facts"]
    if not fa or not st_["dir"] or st_["total"] < 40 or not fa.get("hi") or not fa.get("atr_pct"):
        return None
    c, hi, lo, atrp = fa["close"], fa["hi"], fa["lo"], fa["atr_pct"]
    atr = c * atrp / 100
    if st_["dir"] > 0:
        stop = min(lo, c - 1.5 * atr)
        trig, tgt = hi, c + 2 * (c - stop)
    else:
        stop = max(hi, c + 1.5 * atr)
        trig, tgt = lo, c - 2 * (stop - c)
    return {"dir": st_["dir"], "price": c, "trigger": trig, "stop": stop, "target": tgt,
            "risk_pct": abs(c - stop) / c * 100, "reward_pct": abs(tgt - c) / c * 100}


def scenario(a):
    """The trading scenario in words: (english, arabic) or None."""
    p = plan(a)
    if not p:
        return None
    fmt = lambda x: f"${x:,.2f}"
    if p["dir"] > 0:
        return (f"Continuation if the price closes above today's high ({fmt(p['trigger'])}) with volume above its average. The idea is wrong "
                f"below {fmt(p['stop'])} (today's low or 1.5 ATR under the price). A first target at 2× the risk: {fmt(p['target'])}.",
                f"استمرار الصعود إذا أغلق السعر فوق أعلى سعر اليوم ({fmt(p['trigger'])}) بحجم تداول فوق متوسطه. الفكرة تسقط تحت {fmt(p['stop'])} "
                f"(أدنى سعر اليوم أو 1.5 ATR تحت السعر). أول هدف عند ضعف المخاطرة: {fmt(p['target'])}.")
    return (f"Continuation down if the price closes below today's low ({fmt(p['trigger'])}) with volume above its average. The idea is wrong "
            f"above {fmt(p['stop'])} (today's high or 1.5 ATR over the price). A first target at 2× the risk: {fmt(p['target'])}.",
            f"استمرار الهبوط إذا أغلق السعر تحت أدنى سعر اليوم ({fmt(p['trigger'])}) بحجم تداول فوق متوسطه. الفكرة تسقط فوق {fmt(p['stop'])} "
            f"(أعلى سعر اليوم أو 1.5 ATR فوق السعر). أول هدف عند ضعف المخاطرة: {fmt(p['target'])}.")


def why(a):
    """Why it matters, in plain words: (english, arabic)."""
    ev, main = a["event"], a["main"]
    name = company(main)[0].rstrip(".") if main and a["direct"] else ""
    en_ev, ar_ev = EVENT.get(ev, EVENT["other"])[:2]
    sec = a["sectors"][0] if a["sectors"] else None
    peers_ = ", ".join(a["indirect"][:3])
    base = {
        "earnings": ("Earnings reset what the market expects the company to make; a surprise usually moves the price for days.",
                     "النتائج تعيد تقدير أرباح الشركة المتوقعة، والمفاجأة عادةً تحرك السعر لعدة أيام."),
        "guidance": ("Guidance changes the next quarters' numbers, so analysts rewrite their estimates and the price follows for weeks.",
                     "التوقعات تغيّر أرقام الأرباع القادمة، فيعدّل المحللون تقديراتهم ويتبعهم السعر أسابيع."),
        "mna": ("A deal changes who owns what: the target usually jumps towards the offer, the buyer can fall on the price it pays.",
                "الصفقة تغيّر الملكية: الشركة المستهدفة عادةً تقفز نحو سعر العرض، والمشترية ممكن تنزل بسبب السعر اللي بتدفعه."),
        "regulation": ("Rules and approvals decide where and what the company may sell: they can cut or open a whole market.",
                       "القوانين والموافقات تحدد وين ووش تقدر الشركة تبيع: ممكن تقفل أو تفتح سوق كامل."),
        "lawsuit": ("A lawsuit is a risk of fines or settlements; the market prices the worst case until it is clear.",
                    "القضية خطر غرامات أو تسويات، والسوق يسعّر أسوأ احتمال لين يتضح الأمر."),
        "management": ("A new leader can change the strategy; a sudden exit often worries the market more than a planned one.",
                       "القائد الجديد ممكن يغيّر الاستراتيجية، والخروج المفاجئ يقلق السوق أكثر من المخطط له."),
        "contract": ("A contract adds revenue that was not in the estimates, more so when it is large next to the company's sales.",
                     "العقد يضيف إيرادات ما كانت في التقديرات، خصوصاً لما يكون كبير مقارنة بمبيعات الشركة."),
        "analyst": ("A rating change moves the price mostly the same day, as the funds that follow that analyst react.",
                    "تغيير التصنيف يحرك السعر غالباً في نفس اليوم، لأن الصناديق اللي تتابع المحلل تتفاعل."),
        "offering": ("New shares divide the company among more owners (dilution): the price often drops to the offering price.",
                     "الأسهم الجديدة توزع الشركة على ملاك أكثر (تخفيف)، والسعر غالباً ينزل لسعر الطرح."),
        "payout": ("Buybacks and dividends return cash to shareholders and show the company's confidence in its cash flow.",
                   "إعادة الشراء والتوزيعات ترجع فلوس للمساهمين وتبين ثقة الشركة في تدفقاتها النقدية."),
        "restructuring": ("Cuts lower costs later but show that the business is under pressure now.",
                          "التقليص يخفض التكاليف لاحقاً لكنه يبين إن الشركة تحت ضغط الحين."),
        "product": ("A launch matters when it can change sales; the market judges it by the first reviews and orders.",
                    "الإطلاق يهم لما يقدر يغيّر المبيعات، والسوق يحكم عليه من أول المراجعات والطلبات."),
        "distress": ("A risk of bankruptcy threatens the shares first: they are paid last, after the lenders.",
                     "خطر الإفلاس يهدد الأسهم أول، لأن المساهمين يُدفع لهم آخر شي بعد الدائنين."),
        "macro": ("Macro news moves the whole market through rates, costs and demand; sectors take it differently (below).",
                  "أخبار الاقتصاد تحرك السوق كله عبر الفائدة والتكاليف والطلب، والقطاعات تتأثر بشكل مختلف (تحت)."),
    }.get(ev, ("The story names the company; its weight shows in the price and volume that follow.",
               "الخبر يذكر الشركة، ووزنه يبان في السعر وحجم التداول بعده."))
    en, ar = base
    if name:
        en = f"{en_ev} news on {name}. " + en
        ar = f"خبر {ar_ev} عن {name}. " + ar
    if sec and peers_:
        en += f" Companies in {sec[1] or sec[0]} such as {peers_} often move with it."
        ar += f" وشركات من نفس المجال مثل {peers_} غالباً تتحرك معه."
    return en, ar


def analyze_all(items, px=None, chg=None, spy=None, now=None):
    """Every story analysed, newest first; stories without a company that are neither macro nor market-wide are kept too."""
    now = now or pd.Timestamp.now(tz="UTC")
    rg = regime(spy) if spy is not None else "mixed"
    out = []
    for n in items:
        try:
            out.append(analyze(n, px, chg, rg, now))
        except Exception:
            continue
    return out



def word_sign(w):
    """+1 for a word that reads bullish, -1 bearish (for the chips of the words that decided the sentiment)."""
    return 1 if _POS.fullmatch(w or "") else -1

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "16.8"
