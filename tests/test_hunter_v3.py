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
        self.assertIn(report["status"], ("active", "weak", "rejected"))
        self.assertGreater(report["fit_n"], 100)
        self.assertGreater(report["validation_n"], 40)
        self.assertGreaterEqual(report["validation_days"], 12)
        self.assertEqual(len(model["coef"]), len(V3.MODEL_FEATURES))
        self.assertEqual(report["forecast_weight"], V3.forecast_weight(report["status"]))

    def test_a_planted_signal_is_found_and_weighted(self):
        # 30 stocks whose drift persists for months: past excess return predicts the next 20 sessions, so the
        # cross-sectional model must measure a clearly positive IC walking forward and be validated.
        rng = np.random.default_rng(7)
        n, idx = 700, pd.bdate_range("2022-06-01", periods=700)
        prices = {}
        for i in range(30):
            drift = np.zeros(n)
            for t in range(1, n):
                drift[t] = .985 * drift[t - 1] + .0006 * rng.normal()
            ret = np.clip(drift + .006 * rng.normal(size=n), -.15, .15)
            close = 50 * np.exp(np.cumsum(ret))
            prices[f"P{i:02}"] = pd.DataFrame({"Open": close * .999, "High": close * 1.01, "Low": close * .99, "Close": close,
                                               "Volume": 2_000_000 * (1 + .2 * rng.random(n))}, index=idx)
        market = sample(n=n, seed=99, gain=.0002)
        market.index = idx
        model, report = V3.train(prices, market)
        self.assertEqual(report["status"], "active", report)
        self.assertGreater(report["holdout_ic"], .05)
        self.assertEqual(report["forecast_weight"], V3.FORECAST_WEIGHT)
        feats = pd.DataFrame({s_: V3.features_for(prices[s_], market)[0].iloc[-1] for s_ in prices}).T
        fc = V3.forecast(model, feats)
        self.assertTrue(fc.notna().all())
        # the forecast agrees with the planted drift: the stocks with the best 3-month excess return rank highest
        self.assertGreater(np.corrcoef(fc.rank(), feats["excess_63"].rank())[0, 1], .5)

    def test_tiny_universe_predictor_fails_closed(self):
        model, report = V3.train({"A": sample(280)}, self.market)
        self.assertIsNone(model)
        self.assertIn("insufficient", report["status"])

    def test_ranking_shows_the_forecast_and_weights_it_by_status(self):
        cut = self.market.index[-1]
        res, report, mode = V3.scan(self.prices, self.market, cutoff=cut)
        self.assertEqual(len(res), 10)
        self.assertEqual(report["horizon_sessions"], 20)
        self.assertTrue(res["Rank"].between(0, 100).all())
        self.assertTrue((res["V1 Score"] == res["Score"]).all())
        self.assertTrue(res["Quant Score"].between(0, 100).all())
        capped = res["Risk Flag"].str.contains("stale_data|extreme_volatility|illiquid", na=False)
        self.assertTrue(res.loc[capped, "Rank"].le(49).all())
        self.assertTrue(res["Alpha %"].notna().all())                 # the forecast shows whatever the model measured
        w = report["forecast_weight"]
        free = res[~capped]
        np.testing.assert_allclose(free["Rank"], w * free["Forecast Pctl"] + (1 - w) * free["Quant Score"])
        if report["status"] == "rejected":
            np.testing.assert_allclose(free["Rank"], free["Quant Score"])

    def test_rank_is_quantitative_not_the_hunter_score(self):
        cut = self.market.index[-1]
        res, _, _ = V3.scan(self.prices, self.market, cutoff=cut)
        for name, *_ in V3.FACTORS:
            self.assertTrue(res[name].between(0, 100).all())
        # The quant factors are cross-sectional percentiles: their mean across the stocks sits at 50.
        self.assertAlmostEqual(float(res["Q Momentum"].mean()), 50.0, places=6)

    def test_percentile_of_one_stock_is_neutral(self):
        self.assertEqual(float(V3._pctl([3.0]).iloc[0]), 50.0)
        self.assertEqual(V3._pctl([1.0, 2.0], -1).tolist(), [75.0, 25.0])

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

    def test_return_seeking_increases_exposure_without_leverage(self):
        data = pd.DataFrame({
            "Symbol": [f"S{i}" for i in range(5)],
            "Sector": [f"T{i}" for i in range(5)],
            "Side": [1]*5, "Rank": [95, 93, 91, 89, 87],
            "Entry": [100.]*5, "Stop": [90.]*5,
            "ATR %": [2.]*5, "Alpha %": [2.]*5, "Risk Flag": [""]*5,
        })
        _, safe = V3.allocate(data, capital=10_000, mode="off",
                              profile="risk_controlled", risk_per_trade_pct=1)
        _, seek = V3.allocate(data, capital=10_000, mode="off",
                              profile="return_seeking", risk_per_trade_pct=1)
        self.assertEqual(safe["market_exposure_cap_pct"], 25)
        self.assertEqual(seek["market_exposure_cap_pct"], 70)
        self.assertGreater(seek["invested_pct"], safe["invested_pct"])
        self.assertLessEqual(seek["invested_pct"], 70)

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
