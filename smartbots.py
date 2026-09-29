"""
smartbots.py - The five ready smart bots (brain.py on top of the bot engine): their settings, and their test on real prices
(smart_results.json, written by research/smart.py in GitHub Actions). The Paper Bots page offers them in "Ready bots"; a bot
starts only when someone adds it.

Every bot trades all companies (the S&P 500 + the site's largest companies) with shares, and
trades six COMBINED STRATEGIES (a combination buys a stock when enough of its strategies are in their buy state at once,
and sells when they no longer are): the 30 best combinations of research/combos.py, dealt in turn. It runs the parts of
brain.py on top: the market regime (which sizes the trades), the score out of 100, the risk sizing and the self-check, and
for each trade it takes the combination whose signals did best lately.
The risk rules are the lighter ones asked for (LOOSE); the test shows each bot period by period, 2008 to now.
"""
import json
import os

import brain as BR

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "smart_results.json")
FEE = 0.10          # % per side: the broker fee and the slippage of a real fill together (conservative for large companies)

# the 30 best combined strategies of research/combos.py (every pair, triple and group of four, ranked on 2010-2019 only), dealt
# to the five bots in turn: each bot has six, one of each group of five (1-5, 6-10 ... 26-30), and picks per trade the one
# whose signals did best lately
LOOSE = {"min_score": 45, "choose": "edge", "prefer": [], "bonus": 0, "multi": [], "sector_rank": 0,
         "allow": {"bull": ["trend", "breakout", "momentum", "reversion"], "neutral": ["trend", "breakout", "momentum", "reversion"],
                   "bear": ["trend", "breakout", "momentum", "reversion"], "stress": []},
         "size": {"bull": 1.0, "neutral": 0.9, "bear": 0.5, "stress": 0.0},
         "exposure": {"bull": 1.0, "neutral": 0.9, "bear": 0.5, "stress": 0.0},
         "exit": [], "risk": 2.0, "size_floor": 0.9, "atr": 3.0, "sector_cap": 4, "be_r": 0, "trail_atr": 0, "time_bars": 0,
         "dd_half": 15, "dd_stop": 30, "pause": 15, "streak": 10, "cool": 2, "day_loss": 5, "decay": 1,
         "stress_vol": 40, "stress_x": 2.5}

BOTS = {
    "strong": {
        "name": ("Strong Stocks on Sale", "الأسهم القوية بسعر مخفّض"),
        "idea": ("Buys a short dip in stocks that its momentum and factor strategies call strong, only when all or most strategies of one of its six combinations agree.",
                 "يشتري الهبوط القصير في الأسهم اللي تقول عنها استراتيجيات الزخم والعوامل إنها قوية، وبس لما تتفق كل أو أغلب استراتيجيات وحدة من تركيباته الست."),
        "max_pos": 10,
        "brain": {**LOOSE, "combos": [{"of": ["VWAP Mean Reversion", "Multi-Factor Strategy", "Momentum Strategy", "Portfolio-Level Strategy"], "min": 4},
                                       {"of": ["Momentum Strategy", "VWAP Mean Reversion", "Multi-Factor Strategy"], "min": 3},
                                       {"of": ["VWAP Mean Reversion", "Statistical Arbitrage", "Multi-Factor Strategy", "Relative Strength Strategy"], "min": 3},
                                       {"of": ["Mean Reversion", "Multi-Factor Strategy", "Regime-Based Strategy", "Portfolio-Level Strategy"], "min": 4},
                                       {"of": ["Mean Reversion", "Multi-Factor Strategy", "Regime-Based Strategy"], "min": 3},
                                       {"of": ["VWAP Mean Reversion", "RSI Mean Reversion", "Relative Strength Strategy", "Portfolio-Level Strategy"], "min": 3}]},
    },
    "factor": {
        "name": ("Factor Dips", "تصحيحات العوامل"),
        "idea": ("Buys dips that its factor, momentum, statistical and pairs strategies agree on: six combinations of three or four strategies.",
                 "يشتري التصحيحات اللي تتفق عليها استراتيجيات العوامل والزخم والإحصاء والأزواج: ست تركيبات من ثلاث أو أربع استراتيجيات."),
        "max_pos": 10,
        "brain": {**LOOSE, "combos": [{"of": ["VWAP Mean Reversion", "Mean Reversion", "Multi-Factor Strategy", "Momentum Strategy"], "min": 4},
                                       {"of": ["SMA Crossover", "VWAP Mean Reversion", "Multi-Factor Strategy"], "min": 3},
                                       {"of": ["VWAP Mean Reversion", "RSI Mean Reversion", "Statistical Arbitrage", "Momentum Strategy"], "min": 3},
                                       {"of": ["VWAP Mean Reversion", "Statistical Arbitrage", "Multi-Factor Strategy", "Regime-Based Strategy"], "min": 3},
                                       {"of": ["Pairs Trading", "Regime-Based Strategy", "Portfolio-Level Strategy"], "min": 3},
                                       {"of": ["Pairs Trading", "VWAP Mean Reversion", "MFI Money Flow (Volume)", "Statistical Arbitrage"], "min": 3}]},
    },
    "deep": {
        "name": ("Deep Pullbacks", "التصحيحات العميقة"),
        "idea": ("Waits until its mean-reversion strategies and the market's own trend, rotation and momentum strategies agree on a stock, then buys the pullback: six combinations.",
                 "ينتظر لين تتفق استراتيجيات الارتداد للمتوسط مع استراتيجيات الاتجاه والتدوير والزخم على سهم، وبعدين يشتري التصحيح: ست تركيبات."),
        "max_pos": 10,
        "brain": {**LOOSE, "combos": [{"of": ["VWAP Mean Reversion", "Mean Reversion", "Regime-Based Strategy", "Portfolio-Level Strategy"], "min": 4},
                                       {"of": ["VWAP Mean Reversion", "Mean Reversion", "Multi-Factor Strategy", "Portfolio-Level Strategy"], "min": 4},
                                       {"of": ["VWAP Reclaim / Pullback", "Pairs Trading", "Statistical Arbitrage"], "min": 2},
                                       {"of": ["VWAP Mean Reversion", "RSI Mean Reversion", "Momentum Strategy", "Relative Strength Strategy"], "min": 3},
                                       {"of": ["VWAP Mean Reversion", "Multi-Factor Strategy", "Portfolio-Level Strategy"], "min": 3},
                                       {"of": ["Momentum Strategy", "Mean Reversion", "Statistical Arbitrage"], "min": 3}]},
    },
    "trendpb": {
        "name": ("Trend Pullbacks", "تصحيحات الاتجاه"),
        "idea": ("Buys a pullback to the average price in stocks whose regime, rotation and trend strategies say the trend is up: six combinations.",
                 "يشتري نزول السعر لمتوسطه في الأسهم اللي تقول استراتيجيات الحالة والتدوير والاتجاه إن اتجاهها صاعد: ست تركيبات."),
        "max_pos": 10,
        "brain": {**LOOSE, "combos": [{"of": ["VWAP Mean Reversion", "Regime-Based Strategy", "Portfolio-Level Strategy"], "min": 3},
                                       {"of": ["VWAP Mean Reversion", "RSI Mean Reversion", "Statistical Arbitrage", "Regime-Based Strategy"], "min": 3},
                                       {"of": ["VWAP Mean Reversion", "MFI Money Flow (Volume)", "Multi-Factor Strategy", "Moving Average Crossover"], "min": 3},
                                       {"of": ["SMA Crossover", "Bollinger Breakout", "Pairs Trading"], "min": 3},
                                       {"of": ["Trend Following", "Mean Reversion", "Portfolio-Level Strategy"], "min": 3},
                                       {"of": ["SMA Crossover", "Momentum Strategy", "VWAP Mean Reversion"], "min": 3}]},
    },
    "golden": {
        "name": ("Golden Cross Pullbacks", "تصحيحات التقاطع الذهبي"),
        "idea": ("Buys a dip in stocks above their golden cross (50-day over 200-day average) when the regime strategy agrees, or when several reversion, relative-strength and money-flow strategies do: six combinations.",
                 "يشتري الهبوط في الأسهم اللي فوق تقاطعها الذهبي (متوسط 50 فوق 200) لما توافق استراتيجية الحالة، أو لما تتفق عدة استراتيجيات للارتداد والقوة النسبية وتدفق السيولة: ست تركيبات."),
        "max_pos": 10,
        "brain": {**LOOSE, "combos": [{"of": ["Golden Cross (50/200)", "VWAP Mean Reversion", "Regime-Based Strategy"], "min": 3},
                                       {"of": ["Mean Reversion", "Statistical Arbitrage", "Regime-Based Strategy", "Relative Strength Strategy"], "min": 3},
                                       {"of": ["VWAP Mean Reversion", "Pairs Trading", "Multi-Factor Strategy"], "min": 2},
                                       {"of": ["Golden Cross (50/200)", "Pairs Trading", "Regime-Based Strategy"], "min": 3},
                                       {"of": ["Mean Reversion", "Statistical Arbitrage", "Momentum Strategy", "Portfolio-Level Strategy"], "min": 4},
                                       {"of": ["MACD Crossover", "MFI Money Flow (Volume)", "VWAP Reclaim / Pullback"], "min": 3}]},
    },
}
for _b in BOTS.values():                          # each bot has the strategies of its combinations, at their defaults
    _b["strategies"] = {x: {} for c in _b["brain"]["combos"] for x in c["of"]}

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
BUILD = "14.4"
