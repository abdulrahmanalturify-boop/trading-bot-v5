"""Deterministic tests for completely independent TURA Hunter V3.

Run: python -m unittest discover -s tests -p 'test_hunter_v3.py' -v
"""
import unittest

import numpy as np
import pandas as pd

import hunter as H
import hunter_v3 as V3


def sample(n=530, seed=1, gain=.0004):
    rng = np.random.default_rng(seed)
    ret = np.clip(gain + .008 * rng.normal(size=n), -.15, .15)
    close = 80 * np.exp(np.cumsum(ret))
    idx = pd.bdate_range("2023-01-02", periods=n)
    return pd.DataFrame({
        "Open": close * (1 - .002),
        "High": close * 1.012,
        "Low": close * .985,
        "Close": close,
        "Volume": 1_000_000 * (1 + .25 * rng.random(n)),
    }, index=idx)


class HunterV3Safety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.market = sample(seed=4, gain=.00025)
        cls.prices = {f"T{i:02}": sample(seed=10+i, gain=.0003+i*.00004) for i in range(10)}

    def test_horizon_and_features(self):
        d = self.prices["T00"]
        f, labels = V3.features_for(d, self.market)
        self.assertEqual(f.index.tolist(), d.index.tolist())
        self.assertTrue(labels.iloc[-V3.HORIZON:].isna().all())
        self.assertTrue(np.isfinite(f.iloc[-1].to_numpy(float)).all())

    def test_cutoff_never_sees_future_bars(self):
        d, b = self.prices["T01"], self.market
        cutoff = d.index[-85]
        aa = V3._clean(d, cutoff)
        bb = V3._clean(b, cutoff)
        fa, ya = V3.features_for(aa, bb)
        later = d.iloc[:len(d)-85]
        self.assertTrue(aa.index.max() <= cutoff)
        self.assertEqual(len(aa), len(d.loc[:cutoff]))
        expected_x, expected_y = V3.features_for(d.loc[:cutoff], b.loc[:cutoff])
        pd.testing.assert_frame_equal(fa, expected_x)
        pd.testing.assert_series_equal(ya, expected_y)

    def test_regression_no_lookahead_to_cutoff(self):
        cutoff = self.market.index[-70]
        orig_model, orig_stats = V3.train(
            {k: d.loc[:cutoff] for k, d in self.prices.items()},
            self.market.loc[:cutoff])
        full_model, full_stats = V3.train(self.prices, self.market, cutoff=cutoff)
        self.assertEqual(orig_stats, full_stats)
        if orig_model is not None and full_model is not None:
            np.testing.assert_array_equal(orig_model["coef"], full_model["coef"])

    def test_validation_and_sufficient_samples(self):
        model, report = V3.train(self.prices, self.market)
        self.assertIn(report["status"], ("active", "rejected_by_validation"))
        self.assertGreater(report["fit_n"], 100)
        self.assertGreater(report["validation_n"], 40)
        self.assertTrue(model is None or len(model["coef"]) == len(V3.FEATURES))

    def test_tiny_universe_predictor_fails_closed(self):
        model, report = V3.train({"A": sample(280)}, self.market)
        self.assertIsNone(model)
        self.assertIn("insufficient", report["status"])

    def test_ranking_works_when_model_rejected(self):
        cut = self.market.index[-1]
        res, report, mode = V3.scan(self.prices, self.market, cutoff=cut)
        self.assertEqual(len(res), 10)
        self.assertEqual(report["horizon_sessions"], 20)
        self.assertTrue(res["Rank"].between(0, 100).all())
        self.assertTrue((res["V1 Score"] == res["Score"]).all())
        self.assertTrue(res.loc[res["Side"] <= 0, "Rank"].le(49).all())
        if report["status"] != "active":
            self.assertTrue(res["Alpha %"].isna().all())

    def test_allocation_respects_exposure_and_cash(self):
        data = pd.DataFrame({
            "Symbol": [f"S{i}" for i in range(6)],
            "Sector": ["A", "A", "B", "C", "D", "E"],
            "Side": [1]*6,
            "Rank": [95, 90, 85, 80, 75, 70],
            "Entry": [100.]*6,
            "Stop": [95.]*6,
            "ATR %": [2.]*6,
            "Alpha %": [np.nan]*6,
            "Risk Flag": [""]*6,
        })
        result, info = V3.allocate(data, capital=10_000, risk_per_trade_pct=1,
                                   max_positions=6, sector_limit=1, mode="off")
        self.assertLessEqual(info["invested_pct"], 25.0)
        self.assertLessEqual(len(result), 5)
        self.assertLessEqual(result["Notional"].sum(), 2500 + 0.01)
        self.assertLessEqual(result["Stop Risk $"].max(), 100)
        self.assertEqual(len(set(result["Sector"])), len(result))

    def test_allocation_rejects_broken_stops(self):
        data = pd.DataFrame({
            "Symbol": ["A"], "Sector": ["T"], "Side": [1], "Rank": [95],
            "Entry": [100.], "Stop": [105.], "ATR %": [2.],
            "Alpha %": [2.], "Risk Flag": [""],
        })
        result, info = V3.allocate(data)
        self.assertEqual(len(result), 0)
        self.assertEqual(info["positions"], 0)

    def test_old_hunter_weights_stay_unchanged(self):
        self.assertEqual(H.WEIGHTS, {
            "trend": .25, "rs": .25, "volume": .15, "setup": .20, "risk": .15
        })

    def test_allocation_is_research_only(self):
        p = pd.DataFrame(columns=["Symbol", "Sector", "Side", "Rank",
                                   "Risk Flag", "Entry", "Stop", "ATR %", "Alpha %"])
        _, info = V3.allocate(p)
        self.assertFalse(info["live_orders"])


if __name__ == "__main__":
    unittest.main()
