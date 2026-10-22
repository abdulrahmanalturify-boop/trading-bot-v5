import unittest
from unittest import mock

import numpy as np
import pandas as pd

import paperbots as P

IX = pd.bdate_range("2026-04-01", periods=120)


def frame(seed, drop=None):
    c = 100 * np.cumprod(1 + np.random.default_rng(seed).normal(0, 0.01, len(IX)))
    df = pd.DataFrame({"Open": c, "High": c * 1.01, "Low": c * 0.99, "Close": c, "Volume": 1e6}, index=IX)
    return df.drop(drop) if drop is not None else df


def day(t):
    return str(t.date())


class MissingCandleTest(unittest.TestCase):
    """A stock without a candle on a recorded session (a halt, a day missing from the feed) must not stop the replay."""

    def run_bot(self, gap, sell):
        px = {"AAA": frame(1), "BBB": frame(2, [gap])}
        with mock.patch.object(P, "_members", lambda *a, **k: ["AAA", "BBB"]):
            return self._run(px, gap, sell)

    def _run(self, px, gap, sell):
        rec = P.make_record("t", "sector", "Tech", {"SMA Crossover": {}}, 2, 10000, 0.1, 0, 0, 0, 0, day(IX[30]), ext=0)
        bot = P._norm({"id": 1, **rec})
        ev = [{"d": day(IX[100]), "a": "B", "s": "BBB", "k": "Stock", "l": "SMA Crossover", "p": 100.0, "q": 10.0}]
        if sell:
            ev.append({"d": day(gap), "a": "S", "s": "BBB", "k": "Stock", "l": "SMA Crossover", "p": 101.0, "r": "Signal"})
        fwd = {"since": day(IX[95]), "until": day(IX[-1]), "ev": ev, "sig": [], "eq": {}}
        return P.simulate(bot, px, None, record=fwd)

    def test_open_position_on_a_missing_last_candle(self):
        out = self.run_bot(IX[-1], sell=False)
        self.assertTrue(out["ok"])
        self.assertEqual(len(out["trades"]), 1)

    def test_recorded_sell_on_a_missing_candle(self):
        out = self.run_bot(IX[-5], sell=True)
        self.assertTrue(out["ok"])
        self.assertEqual(out["trades"].iloc[0]["Exit Reason"], "Signal")


if __name__ == "__main__":
    unittest.main()
