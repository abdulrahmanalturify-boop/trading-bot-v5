"""
smartbots.py - The five ready smart bots (brain.py on top of the bot engine): their settings, and their test on real prices
(smart_results.json, written by research/smart.py in GitHub Actions). The Paper Bots page offers them in "Ready bots"; a bot
starts only when someone adds it.

Every bot trades all companies (the S&P 500 + the site's largest companies) with shares, and runs the five parts of brain.py:
the market regime, the strategy families allowed in each regime, the score out of 100, the risk sizing and the self-check.
The settings were chosen on 2010-2019 only (research/results/smart_rounds.md: four rounds, one rule fixed before looking);
2020-now, which played no part in the choice, shows how they hold up on years they never saw.
"""
import json
import os

import brain as BR

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "smart_results.json")
FEE = 0.10          # % per side: the broker fee and the slippage of a real fill together (conservative for large companies)

BOTS = {
    "adaptive": {
        "name": ("Adaptive All-Weather", "المتكيّف مع السوق"),
        "idea": ("Reads the market first, then picks the strategy that suits it: trends and breakouts in a bull market, strong "
                 "stocks and dips in a sideways one, small dip-buys in a bear market, and nothing new in a panic.",
                 "يقرأ السوق أول، وبعدين يختار الاستراتيجية اللي تناسبه: الاتجاه والاختراقات في السوق الصاعد، والأسهم القوية "
                 "والتصحيحات في العرضي، وشراء تصحيحات صغير في الهابط، وما يشتري شي جديد وقت الذعر."),
        "strategies": {"Trend Following": {}, "Breakout Strategy": {}, "Relative Strength Strategy": {}, "Mean Reversion": {},
                       "VWAP Reclaim / Pullback": {}},
        "max_pos": 10,
        "brain": {"min_score": 60,
                  "allow": {"bull": ["trend", "breakout", "momentum", "reversion"], "neutral": ["momentum", "reversion"],
                            "bear": ["reversion"], "stress": []},
                  "size": {"bull": 1.0, "neutral": 0.6, "bear": 0.3, "stress": 0.0},
                  "exposure": {"bull": 1.0, "neutral": 0.6, "bear": 0.3, "stress": 0.0},
                  "exit": [], "risk": 1.0, "atr": 3.0, "sector_cap": 3, "be_r": 1.5, "trail_atr": 3.5, "time_bars": 0,
                  "dd_half": 10, "dd_stop": 20, "pause": 20, "streak": 5, "cool": 5, "day_loss": 3, "decay": 1},
    },
    "trend": {
        "name": ("Trend Rider", "راكب الاتجاه"),
        "idea": ("Rides uptrends in bull and sideways markets (smaller in sideways ones), lets a winner run until its strategy "
                 "says sell, and buys nothing new in a bear market or a panic.",
                 "يركب الاتجاهات الصاعدة في السوق الصاعد والعرضي (بحجم أصغر في العرضي)، ويخلّي الصفقة الرابحة تمشي لين تقول "
                 "استراتيجيتها بيع، وما يشتري شي جديد في السوق الهابط أو وقت الذعر."),
        "strategies": {"Trend Following": {}, "Moving Average Crossover": {}, "Golden Cross (50/200)": {}, "EMA Crossover": {}},
        "max_pos": 10,
        "brain": {"min_score": 50, "allow": {"bull": ["trend"], "neutral": ["trend"], "bear": [], "stress": []},
                  "size": {"bull": 1.0, "neutral": 0.8, "bear": 0.0, "stress": 0.0},
                  "exposure": {"bull": 1.0, "neutral": 0.8, "bear": 0.0, "stress": 0.0},
                  "exit": [], "risk": 1.5, "size_floor": 0.8, "atr": 3.0, "sector_cap": 3, "be_r": 0, "trail_atr": 0, "time_bars": 0,
                  "dd_half": 15, "dd_stop": 25, "pause": 20, "streak": 8, "cool": 3, "day_loss": 3, "decay": 1,
                  "stress_vol": 40, "stress_x": 2.5},
    },
    "breakout": {
        "name": ("Breakout Hunter", "صياد الاختراقات"),
        "idea": ("Buys stocks breaking out to new highs on heavy volume, with a close stop, drops a breakout that goes nowhere "
                 "in 20 sessions, and sells everything when the market turns bear.",
                 "يشتري الأسهم اللي تخترق لقمم جديدة بحجم تداول عالي، بوقف قريب، ويطلع من الاختراق اللي ما يتحرك خلال 20 جلسة، "
                 "ويبيع كل شي إذا صار السوق هابط."),
        "strategies": {"Breakout Strategy": {}, "Donchian Breakout (Turtle)": {}, "Volume Breakout": {}, "Volatility Breakout": {}},
        "max_pos": 8,
        "brain": {"min_score": 65, "weights": {"trend": 15, "mom": 15, "vol": 25, "volat": 10, "struct": 20, "rr": 15},
                  "allow": {"bull": ["breakout"], "neutral": ["breakout"], "bear": [], "stress": []},
                  "size": {"bull": 1.0, "neutral": 1.0, "bear": 0.0, "stress": 0.0},
                  "exposure": {"bull": 1.0, "neutral": 1.0, "bear": 0.0, "stress": 0.0},
                  "exit": ["bear"], "risk": 0.75, "size_floor": 1.0, "atr": 2.5, "sector_cap": 2, "be_r": 0, "trail_atr": 0,
                  "time_bars": 20, "time_r": 0.5, "dd_half": 10, "dd_stop": 20, "pause": 20, "streak": 6, "cool": 5,
                  "day_loss": 3, "decay": 1, "stress_vol": 40, "stress_x": 2.5},
    },
    "momentum": {
        "name": ("Momentum Leaders", "قادة الزخم"),
        "idea": ("Holds the market's strongest stocks against the S&P 500, ranked by momentum; fewer in a sideways market, "
                 "nothing new in a bear market or a panic.",
                 "يمسك أقوى الأسهم مقارنة بالسوق، مرتبة حسب الزخم؛ وعدد أقل في السوق العرضي، ولا شي جديد في السوق الهابط أو وقت الذعر."),
        "strategies": {"Relative Strength Strategy": {}, "Momentum Strategy": {}, "Portfolio-Level Strategy": {}},
        "max_pos": 10,
        "brain": {"min_score": 60, "weights": {"trend": 20, "mom": 35, "vol": 10, "volat": 10, "struct": 15, "rr": 10},
                  "allow": {"bull": ["momentum"], "neutral": ["momentum"], "bear": [], "stress": []},
                  "size": {"bull": 1.0, "neutral": 0.8, "bear": 0.0, "stress": 0.0},
                  "exposure": {"bull": 1.0, "neutral": 0.8, "bear": 0.0, "stress": 0.0},
                  "exit": [], "risk": 1.5, "size_floor": 0.8, "atr": 3.0, "sector_cap": 3, "be_r": 0, "trail_atr": 0,
                  "time_bars": 0, "dd_half": 15, "dd_stop": 25, "pause": 20, "streak": 8, "cool": 3, "day_loss": 3, "decay": 1,
                  "stress_vol": 40, "stress_x": 2.5},
    },
    "pullback": {
        "name": ("Pullback Buyer", "صياد التصحيحات"),
        "idea": ("Buys short dips in stocks that are in an uptrend, sells on the bounce, and never waits more than 10 "
                 "sessions for it; stays out of bear markets and sells everything in a panic.",
                 "يشتري الهبوط القصير في الأسهم اللي اتجاهها صاعد، ويبيع مع الارتداد، وما ينتظره أكثر من 10 جلسات؛ "
                 "ويبتعد عن السوق الهابط ويبيع كل شي وقت الذعر."),
        "strategies": {"Mean Reversion": {}, "RSI Mean Reversion": {"period": 2, "buy_below": 10, "sell_above": 60},
                       "VWAP Mean Reversion": {}, "VWAP Reclaim / Pullback": {}},
        "max_pos": 12,
        "brain": {"min_score": 55, "weights": {"trend": 30, "mom": 20, "vol": 5, "volat": 15, "struct": 10, "rr": 20},
                  "allow": {"bull": ["reversion"], "neutral": ["reversion"], "bear": [], "stress": []},
                  "size": {"bull": 1.0, "neutral": 1.0, "bear": 0.0, "stress": 0.0},
                  "exposure": {"bull": 1.0, "neutral": 1.0, "bear": 0.0, "stress": 0.0},
                  "exit": ["stress"], "risk": 0.75, "atr": 2.5, "sector_cap": 3, "be_r": 0, "trail_atr": 0, "time_bars": 10,
                  "time_r": 0.0, "dd_half": 10, "dd_stop": 20, "pause": 20, "streak": 6, "cool": 5, "day_loss": 3, "decay": 1},
    },
}
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
