"""
smartbots.py - The five ready smart bots (brain.py on top of the bot engine): their settings, and their test on real prices
(smart_results.json, written by research/smart.py in GitHub Actions). The Paper Bots page offers them in "Ready bots"; a bot
starts only when someone adds it.

Every bot trades all companies (the S&P 500 + the site's largest companies) with shares, has every strategy of the site at
hand and runs the five parts of brain.py: the market regime (which sizes the trades), the score out of 100, the risk sizing
and the self-check; its strategies are open (every one may trade in every market but a panic), and for each trade it takes
the one whose signals did best lately. The five differ by what their score values in a stock, and how long they hold.
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

# what every bot allows itself: every strategy in every market (open: no family is set aside, no style is preferred; the bot
# takes, for each trade, the strategy whose signals did best lately), a sideways market at 90% of the size and a bear one at
# half, nothing new in a panic, no forced selling; 2% risk a trade, up to 4 trades a sector, trades half size from 15% under
# the peak and a 15-session break at 30%
OPEN = ["trend", "breakout", "momentum", "reversion"]
LOOSE = {"min_score": 45, "choose": "edge", "prefer": [], "bonus": 0,
         "allow": {"bull": OPEN, "neutral": OPEN, "bear": OPEN, "stress": []},
         "size": {"bull": 1.0, "neutral": 0.9, "bear": 0.5, "stress": 0.0},
         "exposure": {"bull": 1.0, "neutral": 0.9, "bear": 0.5, "stress": 0.0},
         "exit": [], "risk": 2.0, "size_floor": 0.9, "atr": 3.0, "sector_cap": 4, "be_r": 0, "trail_atr": 0, "time_bars": 0,
         "dd_half": 15, "dd_stop": 30, "pause": 15, "streak": 10, "cool": 2, "day_loss": 5, "decay": 1,
         "stress_vol": 40, "stress_x": 2.5}

BOTS = {
    "adaptive": {
        "name": ("Adaptive All-Weather", "المتكيّف مع السوق"),
        "idea": ("Any strategy, whichever has worked best lately; it weighs the six parts of a trade's score evenly and trades "
                 "smaller in a sideways or a bear market.",
                 "أي استراتيجية، اللي كانت الأنجح مؤخراً؛ ويوزن أجزاء التقييم الستة بالتوازن، ويتداول بحجم أصغر في السوق العرضي "
                 "والهابط."),
        "max_pos": 10,
        "brain": dict(LOOSE),
    },
    "trend": {
        "name": ("Trend Rider", "راكب الاتجاه"),
        "idea": ("Any strategy, whichever fits the trade; among the stocks that signal it buys those with the strongest "
                 "trends first, and lets a winner run until its strategy says sell.",
                 "أي استراتيجية تناسب الصفقة؛ ومن الأسهم اللي تعطي إشارة يشتري أول اللي اتجاهها أقوى، ويخلّي الصفقة الرابحة تمشي "
                 "لين تقول استراتيجيتها بيع."),
        "max_pos": 10,
        "brain": {**LOOSE, "weights": {"trend": 30, "mom": 20, "vol": 10, "volat": 10, "struct": 15, "rr": 15}},
    },
    "breakout": {
        "name": ("Breakout Hunter", "صياد الاختراقات"),
        "idea": ("Any strategy, whichever fits the trade; it buys first the stocks near their highs on heavy volume, and drops "
                 "a trade that goes nowhere in 20 sessions.",
                 "أي استراتيجية تناسب الصفقة؛ ويشتري أول الأسهم القريبة من قممها بحجم تداول عالي، ويطلع من الصفقة اللي ما تتحرك "
                 "خلال 20 جلسة."),
        "max_pos": 10,
        "brain": {**LOOSE, "atr": 2.5, "time_bars": 20, "time_r": 0.5,
                  "weights": {"trend": 15, "mom": 15, "vol": 25, "volat": 10, "struct": 20, "rr": 15}},
    },
    "momentum": {
        "name": ("Momentum Leaders", "قادة الزخم"),
        "idea": ("Any strategy, whichever fits the trade; among the stocks that signal it buys the market's strongest first, "
                 "ranked by momentum.",
                 "أي استراتيجية تناسب الصفقة؛ ومن الأسهم اللي تعطي إشارة يشتري أول أقوى أسهم السوق، مرتبة حسب الزخم."),
        "max_pos": 10,
        "brain": {**LOOSE, "weights": {"trend": 20, "mom": 35, "vol": 10, "volat": 10, "struct": 15, "rr": 10}},
    },
    "pullback": {
        "name": ("Pullback Buyer", "صياد التصحيحات"),
        "idea": ("Any strategy, whichever fits the trade; it buys first the stocks in an uptrend with the most room to their "
                 "recent high, and never holds a trade more than 10 sessions unless it's working.",
                 "أي استراتيجية تناسب الصفقة؛ ويشتري أول الأسهم اللي اتجاهها صاعد وعندها أكبر مجال لين قمتها القريبة، وما يمسك "
                 "الصفقة أكثر من 10 جلسات إلا إذا كانت ماشية."),
        "max_pos": 12,
        "brain": {**LOOSE, "atr": 2.5, "time_bars": 10, "time_r": 0.0,
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
BUILD = "13.9"
