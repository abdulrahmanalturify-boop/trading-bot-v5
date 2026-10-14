"""
newsai.py - The news bot's reader: a language model reads every new headline in its context, the way an analyst would.

The rules in newsiq read words; this reads meaning. For each headline it answers, for the market the bot reads for (the Saudi
market or the US market):
- rel   how much the story has to do with that market: 3 its companies, its index or its economy; 2 something that moves it (oil,
        OPEC, the Fed and the dollar, the region's security when it touches the economy); 1 a loose link; 0 nothing (politics or
        statements with no economic effect, sport, society). The bots leave out 0 and 1.
- imp   how much it matters to an investor today, 1 to 10 (a statement, a condemnation, an opinion column stays low);
- topics the real subjects, read in context: "moral bankruptcy" is not a bankruptcy, a "price war" is not a war;
- kind  news (something happened), statement, opinion, analysis, promo;
- tone  for the market or the companies named, -2 to +2;
- thread a short label of the underlying event, the same for every story about it, so the site can link them;
- why   one short line on why it matters (or not), in Arabic and in English.

It runs inside each news bot, in the background, about 20 headlines per request, newest first; each headline is read once (the
answers are kept in memory and in a file, so a restart or a new version does not read them again). It needs OPENAI_API_KEY in the
Secrets (the same key as the site's AI assistant); without it the bots keep the rules alone. Secrets that tune it:
NEWS_AI = "off" stops it; NEWS_AI_MODEL (default gpt-5-mini); NEWS_AI_DAILY = requests a day for both bots together (default 200).
"""
import json
import os
import re
import sys
import threading
import time

import requests

API_URL = "https://api.openai.com/v1/responses"
BATCH = 20
DEFAULT_MODEL = "gpt-5-mini"
FALLBACK_MODELS = ("gpt-5-mini", "gpt-4.1-mini")
DAILY = 200
KEEP_DAYS = 5
PAUSE = 600                       # seconds to wait after a refusal or an error before asking again
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache", "newsai.json")
TOPICS = ["fed", "inflation", "jobs", "economy", "bonds", "trade", "geo", "policy", "earnings", "guidance", "mna", "ipo", "legal",
          "health", "distress", "layoffs", "product", "payout", "analyst", "ai", "crypto", "oil", "metals", "fx", "move", "street"]
KINDS = ["news", "statement", "opinion", "analysis", "promo", "other"]

# one state per server process, kept across module reloads (a new version of the site re-imports this file)
_S = sys.__dict__.setdefault("_tura_newsai", {"lock": threading.RLock(), "cache": {}, "loaded": False, "day": "", "used": 0,
                                              "model": None, "pause": 0.0, "err": "", "ok_at": None, "asked": 0, "dirty": 0,
                                              "threads": {"sa": [], "us": []}})

SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["items"],
    "properties": {"items": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["i", "rel", "imp", "topics", "kind", "tone", "thread", "why_ar", "why_en"],
        "properties": {
            "i": {"type": "integer"},
            "rel": {"type": "integer", "enum": [0, 1, 2, 3]},
            "imp": {"type": "integer", "enum": list(range(1, 11))},
            "topics": {"type": "array", "items": {"type": "string", "enum": TOPICS}},
            "kind": {"type": "string", "enum": KINDS},
            "tone": {"type": "integer", "enum": [-2, -1, 0, 1, 2]},
            "thread": {"type": "string"},
            "why_ar": {"type": "string"},
            "why_en": {"type": "string"}}}}}}

_MARKET = {
    "sa": ("a research site for the Saudi stock market (Tadawul, the TASI index). Its readers invest in Saudi listed companies.",
           "3 = about a Saudi listed company, TASI or the Saudi market, its regulators (CMA, Tadawul, SAMA), Saudi economic data or "
           "Saudi government economic decisions; 2 = something that moves Saudi stocks: oil prices, OPEC+, the Fed and US rates (the "
           "riyal is pegged to the dollar), the Gulf economy, global markets, the region's security when it touches oil, trade or "
           "the economy; 1 = a loose link (world news with a remote effect); 0 = nothing to do with markets or the economy: politics, "
           "diplomacy, statements, condemnations, visits and protocol, religion, society, sport, weather, crime, entertainment."),
    "us": ("a research site for the US stock market (NYSE, Nasdaq, the S&P 500). Its readers invest in US listed companies.",
           "3 = about a US listed company, the US market, the Fed, US economic data or US economic policy; 2 = something that moves "
           "US stocks: oil, China, Europe and Japan's central banks, trade and tariffs, geopolitics with a market effect, global "
           "markets; 1 = a loose link; 0 = nothing to do with markets or the economy: politics with no economic angle, sport, "
           "society, celebrity, lifestyle, personal-finance tips."),
}


def _instructions(market):
    who, rel = _MARKET.get(market, _MARKET["us"])
    return (
        f"You read news headlines for {who}\n"
        "For every numbered headline (outlet, title, sometimes the opening of the story) answer in the JSON format, one entry per "
        "headline with its number i. Read each one as an analyst would, in context - never by single words:\n"
        f"- rel: how related it is to this market. {rel}\n"
        "- imp: how much it matters to an investor in this market today, 1-10. 9-10: a market-moving event (a rate decision, an "
        "OPEC+ decision, a big earnings surprise of a major company, a war escalation that hits oil). 6-8: clear news about a company "
        "or the economy. 3-5: routine company notices, small companies, analysis. 1-2: statements, condemnations, opinion columns, "
        "promotions and anything with rel 0.\n"
        "- topics: up to 3 from the list, only the real subject. A figure of speech is not an event: 'إفلاس أخلاقي' or 'morally "
        "bankrupt' (moral bankruptcy) is not distress; 'حرب أسعار' (a price war) is not geo; 'زلزال في السوق' is not a disaster. "
        "distress = a company or a country actually failing to pay, insolvent or delisted. Use [] when none fits.\n"
        "- kind: news (something happened), statement (an official statement, a condemnation, a speech), opinion (a column or a "
        "comment), analysis (market or stock analysis, forecasts), promo (an advert, a sponsored or listing page), other.\n"
        "- tone: for this market or the companies named: -2 very negative, -1 negative, 0 neutral or unclear, 1 positive, 2 very positive.\n"
        "- thread: a short English label of the underlying event or theme, lowercase words joined by hyphens, 2-6 words (e.g. "
        "'aramco-q3-results', 'opec-plus-output-cut', 'fed-rate-decision', 'houthi-attacks-on-saudi-airports'). Stories about the same "
        "event get exactly the same label; reuse a label from the list of recent labels when it is the same event.\n"
        "- why_ar: at most 12 words in Arabic: why it matters for this market, or why it does not.\n"
        "- why_en: the same in English, at most 12 words.\n"
        "Be strict: when in doubt between two values of rel or imp, take the lower one.")


def _secret(name, default=""):
    try:
        import streamlit as st
        v = st.secrets.get(name, "")
        if v:
            return str(v)
    except Exception:
        pass
    return str(os.getenv(name, default) or default)


def _key():
    k = _secret("OPENAI_API_KEY")
    if not k:
        try:
            import streamlit as st
            k = str((st.secrets.get("openai", {}) or {}).get("api_key", "") or "")
        except Exception:
            k = ""
    return k


def enabled():
    return bool(_key()) and _secret("NEWS_AI", "on").strip().lower() not in ("off", "0", "false", "no")


def _cap():
    try:
        return max(0, int(_secret("NEWS_AI_DAILY", str(DAILY))))
    except ValueError:
        return DAILY


def _models():
    first = _secret("NEWS_AI_MODEL", "") or _S.get("model") or DEFAULT_MODEL
    own = _secret("OPENAI_MODEL", "")
    return list(dict.fromkeys([m for m in (first, *FALLBACK_MODELS, own) if m]))


# ---------------------------------------------------------------- the answers kept
def _load():
    if _S["loaded"]:
        return
    _S["loaded"] = True
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        cut = time.time() - KEEP_DAYS * 86400
        _S["cache"].update({k: v for k, v in (data.get("cache") or {}).items() if v.get("at", 0) >= cut})
        for m, th in (data.get("threads") or {}).items():
            _S["threads"][m] = list(th)[-60:]
    except Exception:
        pass


def _save():
    try:
        cut = time.time() - KEEP_DAYS * 86400
        with _S["lock"]:
            for k in [k for k, v in _S["cache"].items() if v.get("at", 0) < cut]:
                _S["cache"].pop(k, None)
            data = {"cache": dict(_S["cache"]), "threads": {m: list(v) for m, v in _S["threads"].items()}}
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        tmp = CACHE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, CACHE_FILE)
    except Exception:
        pass


def cached(key):
    """The reading kept for a headline (its newsbot key), or None."""
    _load()
    return _S["cache"].get(key)


def _fingerprint():
    """The key (only a hash of it) and the site's version: a new key or a new version tries again at once after a refusal."""
    import hashlib
    return hashlib.sha256((_key() + "|" + str(globals().get("BUILD", ""))).encode()).hexdigest()[:16]


def can_ask():
    """A request may go out now (switched on, under the day's ceiling, not resting after an error)."""
    if not enabled():
        return False
    if _S["pause"] and _S.get("pause_for") != _fingerprint():
        _S["pause"], _S["err"] = 0.0, ""
    if time.time() < _S["pause"]:
        return False
    day = time.strftime("%Y-%m-%d", time.gmtime())
    with _S["lock"]:
        if _S["day"] != day:
            _S["day"], _S["used"] = day, 0
        return _S["used"] < _cap()


def problem(ar=False):
    """The last refusal in plain words for the News page (no part of the key), or ''."""
    e = str(_S.get("err") or "")
    if not e:
        return ""
    for k, en, a in (("missing_scope", "OpenAI refuses the key: it is restricted - create one with the permission All",
                      "OpenAI رفض المفتاح: صلاحياته محدودة - سوّ مفتاح جديد بصلاحية All"),
                     ("invalid_api_key", "OpenAI refuses the key: it is not a valid key - copy it again, whole",
                      "OpenAI رفض المفتاح: المفتاح غير صحيح - انسخه مرة ثانية كامل"),
                     ("insufficient_quota", "no credit left in the OpenAI account - add credit under Billing",
                      "ما فيه رصيد في حساب OpenAI - اشحن من صفحة Billing"),
                     ("org_not_verified", "OpenAI asks to verify the organization for this model",
                      "OpenAI يطلب توثيق الحساب لهذا النموذج"),
                     ("HTTP 401", "OpenAI refuses the key (401) - check it is copied whole, or create a new one",
                      "OpenAI رفض المفتاح (401) - تأكد إنه منسوخ كامل أو سوّ مفتاح جديد"),
                     ("HTTP 429", "OpenAI is busy or the account's limit is reached - tried again in 10 minutes",
                      "OpenAI مشغول أو وصل حد الحساب - يعيد المحاولة بعد 10 دقائق"),
                     ("no model", "no model available to this key", "ما فيه نموذج متاح لهالمفتاح")):
        if k in e:
            return (a if ar else en) + f" ({e})"
    return e


def status():
    """For the News page: on/off, the model, requests today and the ceiling, headlines read, the last problem."""
    _load()
    return {"on": enabled(), "model": _S.get("model") or (_models()[0] if enabled() else ""), "used": _S["used"], "cap": _cap(),
            "read": len(_S["cache"]), "err": _S["err"], "ok_at": _S["ok_at"], "paused": time.time() < _S["pause"]}


# ---------------------------------------------------------------- one request
def _text_of(js):
    out = []
    for item in js.get("output") or []:
        if isinstance(item, dict) and item.get("type") == "message":
            for c in item.get("content") or []:
                if isinstance(c, dict) and c.get("type") == "output_text" and c.get("text"):
                    out.append(str(c["text"]))
    return "".join(out).strip() or str(js.get("output_text") or "")


def _reason(r):
    """A short, key-free reason for a refusal: the error's code from OpenAI's answer (never its message, which can show part of
    the key), or what the message says when there is no code (a key without the permission for this API)."""
    try:
        e = (r.json() or {}).get("error") or {}
    except Exception:
        e = {}
    msg = str(e.get("message") or "").lower()
    if "missing scopes" in msg or "insufficient permissions" in msg:
        return "missing_scope"
    if "verify" in msg and "organization" in msg:
        return "org_not_verified"
    code = str(e.get("code") or e.get("type") or "").strip()
    return re.sub(r"[^a-z0-9_]", "", code.lower())[:40]


def _post(key, body):
    return requests.post(API_URL, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=body, timeout=75)


def _ask(text, market):
    """-> parsed JSON items, or None (the reason is kept in _S['err'])."""
    key = _key()
    for model in _models():
        body = {"model": model, "instructions": _instructions(market), "input": text, "max_output_tokens": 6000, "store": False,
                "text": {"format": {"type": "json_schema", "name": "news_reading", "strict": True, "schema": SCHEMA}}}
        if model.startswith(("gpt-5", "o3", "o4")):
            body["reasoning"] = {"effort": "minimal"}
        try:
            r = _post(key, body)
            if r.status_code == 400 and "reasoning" in body and "reason" in r.text.lower():
                body.pop("reasoning")
                r = _post(key, body)
        except Exception as e:
            _S["err"] = type(e).__name__
            return None
        if r.status_code in (400, 404) and "model" in r.text.lower():
            continue                                   # this model is not available to the key: the next one
        if r.status_code >= 400:
            why = _reason(r)
            _S["err"] = f"HTTP {r.status_code}" + (f" {why}" if why else "")
            if r.status_code in (401, 403, 429) or r.status_code >= 500:
                _S["pause"] = time.time() + (PAUSE * (6 if r.status_code in (401, 403) else 1))
                _S["pause_for"] = _fingerprint()
            return None
        try:
            items = json.loads(_text_of(r.json())).get("items")
        except Exception:
            _S["err"] = "unreadable answer"
            return None
        _S["model"], _S["err"], _S["ok_at"] = model, "", time.time()
        return items if isinstance(items, list) else None
    _S["err"] = "no model available"
    _S["pause"] = time.time() + PAUSE * 6
    _S["pause_for"] = _fingerprint()
    return None


_SLUG = re.compile(r"[^a-z0-9]+")


def _clean(v):
    try:
        rel = int(v.get("rel"))
        imp = int(v.get("imp"))
    except (TypeError, ValueError):
        return None
    if rel not in (0, 1, 2, 3) or not 1 <= imp <= 10:
        return None
    try:
        tone = max(-2, min(2, int(v.get("tone") or 0)))
    except (TypeError, ValueError):
        tone = 0
    topics = [t for t in dict.fromkeys(v.get("topics") or []) if t in TOPICS][:3]
    kind = v.get("kind") if v.get("kind") in KINDS else "news"
    thread = _SLUG.sub("-", str(v.get("thread") or "").lower()).strip("-")[:60]
    return {"rel": rel, "imp": imp, "topics": topics, "kind": kind, "tone": tone, "thread": thread,
            "why_ar": str(v.get("why_ar") or "").replace("\\", "").strip()[:160],
            "why_en": str(v.get("why_en") or "").replace("\\", "").strip()[:160]}


def judge(stories, market="us"):
    """stories: [{"key", "title", "summary", "source"}] (up to BATCH). Reads them in one request; -> {key: reading}.
    Each reading is kept, so a headline is never read twice."""
    _load()
    stories = [s for s in stories if s.get("key") and s.get("title")][:BATCH]
    if not stories or not can_ask():
        return {}
    with _S["lock"]:
        _S["used"] += 1
        _S["asked"] += 1
        recent = list(_S["threads"].get(market) or [])[-40:]
    lines = []
    for i, s in enumerate(stories, 1):
        summ = re.sub(r"\s+", " ", str(s.get("summary") or ""))[:220]
        title = re.sub(r"\s+", " ", str(s["title"])).replace("|", "/")
        lines.append(f"{i} | {str(s.get('source') or '').replace('|', '/')} | {title}" + (f" | {summ.replace('|', '/')}" if summ else ""))
    text = ("Recent event labels: " + (", ".join(recent) if recent else "(none yet)") + "\n\nHeadlines:\n" + "\n".join(lines))
    items = _ask(text, market)
    if not items:
        return {}
    out, now = {}, time.time()
    for v in items:
        if not isinstance(v, dict):
            continue
        try:
            i = int(v.get("i"))
        except (TypeError, ValueError):
            continue
        if not 1 <= i <= len(stories):
            continue
        c = _clean(v)
        if c is None:
            continue
        c["at"] = now
        out[stories[i - 1]["key"]] = c
    if out:
        with _S["lock"]:
            _S["cache"].update(out)
            th = _S["threads"].setdefault(market, [])
            for c in out.values():
                if c["thread"] and c["rel"] >= 2:
                    if c["thread"] in th:
                        th.remove(c["thread"])
                    th.append(c["thread"])
            del th[:-60]
            _S["dirty"] += 1
        _save()
    return out

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "23.4.20"
