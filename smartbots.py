"""
smartbots.py - The five ready smart bots (brain.py on top of the bot engine): their settings, and their test on real prices
(smart_results.json, written by research/smart.py in GitHub Actions). The Paper Bots page offers them in "Ready bots"; a bot
starts only when someone adds it.

Every bot trades all companies (the S&P 500 + the site's largest companies) with shares and runs the parts of brain.py:
the market regime, the score out of 100, the risk sizing and the self-check, and for each trade it takes the strategy (or
combination) whose signals did best lately.
- Strong Stocks on Sale trades five COMBINED STRATEGIES (a combination buys a stock when enough of its strategies are in
  their buy state at once, and sells when they no longer are), picked from the best of research/combos.py, plus Donchian
  Breakout on its own signals (in place of its weakest combination on 2010-2019).
- The other four have every strategy of the site at hand, open (every one may trade in every market); they differ by what
  their score values in a stock, and how long they hold.
All five take HIGH risk (asked for): full size in every market, trades even in a panic (at half size), 3% risk a trade, and
only a deep drawdown slows them down. The test shows each bot period by period, 2008 to now.
"""
import json
import os

import brain as BR
import engine

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "smart_results.json")
FEE = 0.10          # % per side: the broker fee and the slippage of a real fill together (conservative for large companies)

ALL = {name: {} for name in engine.STRATEGIES}     # every strategy of the site at hand, each at its own default settings

# HIGH risk (asked for): every strategy family in every market, a panic included; full size in a sideways and a bear market
# and half size in a panic (nothing is sold because of the market); 3% risk a trade at the 3-ATR stop and every signal that
# passes the score at full size; up to 5 trades a sector; trades half size only from 25% under the peak and a 10-session
# break at 40%; no break after losing streaks or a bad day. The self-check (a strategy that lost its edge is muted) stays.
OPEN = ["trend", "breakout", "momentum", "reversion"]
HIGH = {"min_score": 45, "choose": "edge", "prefer": [], "bonus": 0, "multi": [], "sector_rank": 0,
        "allow": {"bull": OPEN, "neutral": OPEN, "bear": OPEN, "stress": OPEN},
        "size": {"bull": 1.0, "neutral": 1.0, "bear": 1.0, "stress": 0.5},
        "exposure": {"bull": 1.0, "neutral": 1.0, "bear": 1.0, "stress": 0.5},
        "exit": [], "risk": 3.0, "size_floor": 1.0, "atr": 3.0, "sector_cap": 5, "be_r": 0, "trail_atr": 0, "time_bars": 0,
        "dd_half": 25, "dd_stop": 40, "pause": 10, "streak": 0, "cool": 0, "day_loss": 0, "decay": 1,
        "stress_vol": 40, "stress_x": 2.5}
# the lighter risk the bots had before (14.0 to 14.4)
LOOSE = {**HIGH, "allow": {"bull": OPEN, "neutral": OPEN, "bear": OPEN, "stress": []},
         "size": {"bull": 1.0, "neutral": 0.9, "bear": 0.5, "stress": 0.0},
         "exposure": {"bull": 1.0, "neutral": 0.9, "bear": 0.5, "stress": 0.0},
         "risk": 2.0, "size_floor": 0.9, "sector_cap": 4, "dd_half": 15, "dd_stop": 30, "pause": 15, "streak": 10, "cool": 2,
         "day_loss": 5}
# careful: smaller in a sideways (60%) and a bear (30%) market, everything sold in a panic; 1% risk a trade and a weak signal
# at half size; up to 3 trades a sector; half size from 10% under the peak and a 20-session break at 20%; a 5-session break
# after 5 losing trades in a row, and no buys after a session that lost 3%
CAREFUL = {**HIGH, "allow": {"bull": OPEN, "neutral": OPEN, "bear": OPEN, "stress": []},
           "size": {"bull": 1.0, "neutral": 0.6, "bear": 0.3, "stress": 0.0},
           "exposure": {"bull": 1.0, "neutral": 0.6, "bear": 0.3, "stress": 0.0}, "exit": ["stress"],
           "risk": 1.0, "size_floor": 0.5, "sector_cap": 3, "dd_half": 10, "dd_stop": 20, "pause": 20, "streak": 5, "cool": 5,
           "day_loss": 3}
RISK_KEYS = ("allow", "size", "exposure", "exit", "risk", "size_floor", "sector_cap", "dd_half", "dd_stop", "pause", "streak",
             "cool", "day_loss")
# the risk tolerance picked when a ready bot is added (the bots below are set, and shown, at "aggressive")
RISK = {"conservative": {k: CAREFUL[k] for k in RISK_KEYS}, "moderate": {k: LOOSE[k] for k in RISK_KEYS},
        "aggressive": {k: HIGH[k] for k in RISK_KEYS}}
RISK_LABEL = {"conservative": ("Conservative", "محافظ"), "moderate": ("Moderate", "معتدل"), "aggressive": ("Aggressive", "جريء")}
RISK_DEFAULT = "aggressive"
RISK_VARIANT = {"conservative": "risk_conservative", "moderate": "risk_moderate", "aggressive": "smart"}   # in smart_results

BOTS = {
    "strong": {
        "name": ("Strong Stocks on Sale", "الأسهم القوية بسعر مخفّض"),
        "idea": ("Buys a short dip in stocks that its momentum and factor strategies call strong, when all or most strategies of one of its five combinations agree, and also buys Donchian breakouts to a new 20-day high.",
                 "يشتري الهبوط القصير في الأسهم اللي تقول عنها استراتيجيات الزخم والعوامل إنها قوية، لما تتفق كل أو أغلب استراتيجيات وحدة من تركيباته الخمس، ويشتري بعد اختراقات دونشيان لقمة 20 يوم جديدة."),
        "max_pos": 10,
        # five of the 30 best combinations of research/combos.py (ranked on 2010-2019) and Donchian Breakout on its own, in
        # place of "Mean Reversion & Multi-Factor & Regime-Based (3/3)", the one that earned least in this bot on 2010-2019
        "brain": {**HIGH, "combos": [{"of": ["VWAP Mean Reversion", "Multi-Factor Strategy", "Momentum Strategy", "Portfolio-Level Strategy"], "min": 4},
                                      {"of": ["Momentum Strategy", "VWAP Mean Reversion", "Multi-Factor Strategy"], "min": 3},
                                      {"of": ["VWAP Mean Reversion", "Statistical Arbitrage", "Multi-Factor Strategy", "Relative Strength Strategy"], "min": 3},
                                      {"of": ["Mean Reversion", "Multi-Factor Strategy", "Regime-Based Strategy", "Portfolio-Level Strategy"], "min": 4},
                                      {"of": ["VWAP Mean Reversion", "RSI Mean Reversion", "Relative Strength Strategy", "Portfolio-Level Strategy"], "min": 3},
                                      {"of": ["Donchian Breakout (Turtle)"], "min": 1}]},
    },
    "adaptive": {
        "name": ("Adaptive All-Weather", "المتكيّف مع السوق"),
        "idea": ("Any strategy, whichever has worked best lately; it weighs the six parts of a trade's score evenly.",
                 "أي استراتيجية، اللي كانت الأنجح مؤخراً؛ ويوزن أجزاء التقييم الستة بالتوازن."),
        "max_pos": 10,
        "brain": dict(HIGH),
    },
    "trend": {
        "name": ("Trend Rider", "راكب الاتجاه"),
        "idea": ("Any strategy, whichever fits the trade; among the stocks that signal it buys those with the strongest "
                 "trends first, and lets a winner run until its strategy says sell.",
                 "أي استراتيجية تناسب الصفقة؛ ومن الأسهم اللي تعطي إشارة يشتري أول اللي اتجاهها أقوى، ويخلّي الصفقة الرابحة تمشي "
                 "لين تقول استراتيجيتها بيع."),
        "max_pos": 10,
        "brain": {**HIGH, "weights": {"trend": 30, "mom": 20, "vol": 10, "volat": 10, "struct": 15, "rr": 15}},
    },
    "momentum": {
        "name": ("Momentum Leaders", "قادة الزخم"),
        "idea": ("Any strategy, whichever fits the trade; among the stocks that signal it buys the market's strongest first, "
                 "ranked by momentum.",
                 "أي استراتيجية تناسب الصفقة؛ ومن الأسهم اللي تعطي إشارة يشتري أول أقوى أسهم السوق، مرتبة حسب الزخم."),
        "max_pos": 10,
        "brain": {**HIGH, "weights": {"trend": 20, "mom": 35, "vol": 10, "volat": 10, "struct": 15, "rr": 10}},
    },
    "pullback": {
        "name": ("Pullback Buyer", "صياد التصحيحات"),
        "idea": ("Any strategy, whichever fits the trade; it buys first the stocks in an uptrend with the most room to their "
                 "recent high, and never holds a trade more than 10 sessions unless it's working.",
                 "أي استراتيجية تناسب الصفقة؛ ويشتري أول الأسهم اللي اتجاهها صاعد وعندها أكبر مجال لين قمتها القريبة، وما يمسك "
                 "الصفقة أكثر من 10 جلسات إلا إذا كانت ماشية."),
        "max_pos": 12,
        "brain": {**HIGH, "atr": 2.5, "time_bars": 10, "time_r": 0.0,
                  "weights": {"trend": 30, "mom": 20, "vol": 5, "volat": 15, "struct": 10, "rr": 20}},
    },
}
# the combination a single strategy replaced (the test also runs the bot with it back)
SWAPPED = {"strong": {"of": ["Mean Reversion", "Multi-Factor Strategy", "Regime-Based Strategy"], "min": 3}}
for _b in BOTS.values():            # a bot with combinations has their strategies; the others have every strategy
    _b["strategies"] = ({x: {} for c in _b["brain"]["combos"] for x in c["of"]} if _b["brain"].get("combos") else ALL)

ORDER = list(BOTS)


def brain_of(key, risk=None):
    """The bot's brain; with a risk tolerance ("conservative", "moderate", "aggressive"), at that level."""
    b = BOTS[key]["brain"]
    return BR.clean({**b, **RISK[risk]} if risk in RISK else b)


def record_args(key, risk=None):
    """What paperbots.make_record needs for this bot (besides the name, the capital and the start date)."""
    b = BOTS[key]
    br = brain_of(key, risk)
    return {"strategies": {s: dict(p) for s, p in b["strategies"].items()}, "max_pos": b["max_pos"], "fee": FEE,
            "atr_mult": br["atr"], "brain": br}


def risk_of(bot, key):
    """The risk tolerance a saved copy of the ready bot `key` runs at (None when it isn't one)."""
    b = BOTS[key]
    if not (bot.get("kind") == "all" and set(bot.get("strategies") or {}) == set(b["strategies"])
            and int(bot.get("max_pos") or 0) == b["max_pos"]):
        return None
    return next((r for r in RISK if bot.get("brain") == brain_of(key, r)), None)


def same_bot(bot, key):
    """Is this saved bot the ready bot `key` (the same strategies, open trades and brain, at any risk tolerance)?"""
    return risk_of(bot, key) is not None


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
BUILD = "15.4"
