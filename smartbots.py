"""
smartbots.py - The five ready smart bots (brain.py on top of the bot engine): their settings, and their test on real prices
(smart_results.json, written by research/smart.py in GitHub Actions). The Paper Bots page offers them in "Ready bots"; a bot
starts only when someone adds it.

Every bot trades all companies (the S&P 500 + the site's largest companies) with shares, has every strategy of the site at
hand and runs the five parts of brain.py: the market regime, the strategy families allowed in each regime, the score out of
100, the risk sizing and the self-check. For each trade it takes the strategy that suits the market and whose signals did
best lately (its own style first); the five differ by that style, their score weights and how long they hold.
The risk rules are the lighter ones asked for (LOOSE); the test shows each bot period by period, 2008 to now.
"""
import json
import os

import brain as BR
import engine

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "smart_results.json")
FEE = 0.10          # % per side: the broker fee and the slippage of a real fill together (conservative for large companies)

ALL = {name: {} for name in engine.STRATEGIES}     # every bot has every strategy at hand, each at its own default settings

# what every bot allows itself (lighter risk rules): all strategy families in a bull or a sideways market (a sideways one
# at 90%), dip-buying and momentum at half size in a bear market, nothing new in a panic, no forced selling; 2% risk a
# trade, up to 4 trades a sector, trades half size from 15% under the peak and a 15-session break at 30%
LOOSE = {"min_score": 45, "choose": "edge", "bonus": 10,
         "allow": {"bull": ["trend", "breakout", "momentum", "reversion"], "neutral": ["trend", "breakout", "momentum", "reversion"],
                   "bear": ["momentum", "reversion"], "stress": []},
         "size": {"bull": 1.0, "neutral": 0.9, "bear": 0.5, "stress": 0.0},
         "exposure": {"bull": 1.0, "neutral": 0.9, "bear": 0.5, "stress": 0.0},
         "exit": [], "risk": 2.0, "size_floor": 0.9, "atr": 3.0, "sector_cap": 4, "be_r": 0, "trail_atr": 0, "time_bars": 0,
         "dd_half": 15, "dd_stop": 30, "pause": 15, "streak": 10, "cool": 2, "day_loss": 5, "decay": 1,
         "stress_vol": 40, "stress_x": 2.5}

BOTS = {
    "adaptive": {
        "name": ("Adaptive All-Weather", "المتكيّف مع السوق"),
        "idea": ("No style of its own: it reads the market, and for each trade takes whichever of its strategies suits the "
                 "market and has worked best lately.",
                 "ما عنده أسلوب ثابت: يقرأ السوق، ولكل صفقة ياخذ أي استراتيجية تناسب السوق وكانت الأنجح مؤخراً."),
        "max_pos": 10,
        "brain": {**LOOSE, "prefer": [], "bonus": 0},
    },
    "trend": {
        "name": ("Trend Rider", "راكب الاتجاه"),
        "idea": ("Prefers riding trends, lets a winner run until its strategy says sell, and uses any other strategy when a "
                 "trend isn't there.",
                 "يفضّل ركوب الاتجاهات، ويخلّي الصفقة الرابحة تمشي لين تقول استراتيجيتها بيع، ويستخدم أي استراتيجية ثانية "
                 "إذا ما فيه اتجاه."),
        "max_pos": 10,
        "brain": {**LOOSE, "prefer": ["trend"], "weights": {"trend": 30, "mom": 20, "vol": 10, "volat": 10, "struct": 15, "rr": 15}},
    },
    "breakout": {
        "name": ("Breakout Hunter", "صياد الاختراقات"),
        "idea": ("Prefers breakouts to new highs on heavy volume, drops a trade that goes nowhere in 20 sessions, and uses any "
                 "other strategy when the market offers no breakouts.",
                 "يفضّل الاختراقات لقمم جديدة بحجم تداول عالي، ويطلع من الصفقة اللي ما تتحرك خلال 20 جلسة، ويستخدم أي "
                 "استراتيجية ثانية إذا السوق ما فيه اختراقات."),
        "max_pos": 10,
        "brain": {**LOOSE, "prefer": ["breakout"], "atr": 2.5, "time_bars": 20, "time_r": 0.5,
                  "weights": {"trend": 15, "mom": 15, "vol": 25, "volat": 10, "struct": 20, "rr": 15}},
    },
    "momentum": {
        "name": ("Momentum Leaders", "قادة الزخم"),
        "idea": ("Prefers the market's strongest stocks against the S&P 500, ranked by momentum, and uses any other strategy "
                 "when leadership is unclear.",
                 "يفضّل أقوى الأسهم مقارنة بالسوق، مرتبة حسب الزخم، ويستخدم أي استراتيجية ثانية إذا ما كان فيه قادة واضحين."),
        "max_pos": 10,
        "brain": {**LOOSE, "prefer": ["momentum"], "weights": {"trend": 20, "mom": 35, "vol": 10, "volat": 10, "struct": 15, "rr": 10}},
    },
    "pullback": {
        "name": ("Pullback Buyer", "صياد التصحيحات"),
        "idea": ("Prefers buying short dips in stocks that are in an uptrend and never waits more than 10 sessions for the "
                 "bounce; uses any other strategy when there are no good dips.",
                 "يفضّل شراء الهبوط القصير في الأسهم اللي اتجاهها صاعد، وما ينتظر الارتداد أكثر من 10 جلسات؛ ويستخدم أي "
                 "استراتيجية ثانية إذا ما فيه تصحيحات زينة."),
        "max_pos": 12,
        "brain": {**LOOSE, "prefer": ["reversion"], "atr": 2.5, "time_bars": 10, "time_r": 0.0,
                  "weights": {"trend": 30, "mom": 20, "vol": 5, "volat": 15, "struct": 10, "rr": 20}},
    },
}
for _b in BOTS.values():
    _b["strategies"] = ALL
ORDER = list(BOTS)


def brain_of(key):
    return BR.clean(BOTS[key]["brain"])


def record_args(key):
    """What paperbots.make_record needs for this bot (besides the name, the capital and the start date)."""
    b = BOTS[key]
    br = brain_of(key)
    return {"strategies": {s: dict(p) for s, p in b["strategies"].items()}, "max_pos": b["max_pos"], "fee": FEE,
            "atr_mult": br["atr"], "brain": br}


def same_bot(bot, key):
    """Is this saved bot the ready bot `key` (the same strategies, open trades and brain)?"""
    b = BOTS[key]
    return (bot.get("kind") == "all" and set(bot.get("strategies") or {}) == set(b["strategies"])
            and int(bot.get("max_pos") or 0) == b["max_pos"] and bot.get("brain") == brain_of(key))


_CACHE = {}


def results():
    """smart_results.json (None until the test has run), re-read when the file changes."""
    try:
        m = os.path.getmtime(RESULTS)
    except OSError:
        return None
    if _CACHE.get("m") != m:
        try:
            _CACHE.update(m=m, r=json.load(open(RESULTS, encoding="utf-8")))
        except Exception:
            _CACHE.update(m=m, r=None)
    return _CACHE.get("r")

# version stamp: app.py reloads any module still in memory from an older version of the site
BUILD = "13.8"
