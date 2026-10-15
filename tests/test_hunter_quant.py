"""Focused regression checks for TURA Opportunity Hunter quantitative overlay.

Run: python -m unittest discover -s tests -p 'test_hunter_quant.py' -v
"""
import unittest

import numpy as np
import pandas as pd

import hunter as H
import hunter_quant as Q


def prices(n=280, drift=.0010, scale=1.0):
    x = np.arange(n, dtype=float)
    # Deterministic, mildly noisy trend; enough history for 200-day screens.
    close = 100 * np.exp(drift * x + .015 * np.sin(x / 9) * scale)
    return pd.DataFrame({
        "Open": close * .999,
        "High": close * 1.02,
        "Low": close * .98,
        "Close": close,
        "Volume": np.full(n, 2_000_000.0),
    }, index=pd.bdate_range("2025-01-01", periods=n))


class QuantFactors(unittest.TestCase):
    def test_scores_are_finite_and_bounded(self):
        p = prices()
        b = prices(drift=.0003)
        out = Q.assess(p, b)
        self.assertEqual(out["quality"], "ok")
        self.assertGreaterEqual(out["score"], 0)
        self.assertLessEqual(out["score"], 100)
        self.assertTrue(np.isfinite(out["beta"]))
        self.assertTrue(np.isfinite(out["excess_return_pct"]))
        self.assertAlmostEqual(sum(Q.FACTOR_WEIGHTS.values()), 1.0)

    def test_no_benchmark_future_leakage(self):
        p, b = prices(), prices(drift=.0004)
        target = Q.assess(p.iloc[:190], b.iloc[:190])
        future = Q.assess(p.iloc[:190], b)
        self.assertEqual(target, future)

    def test_neutral_when_insufficient(self):
        self.assertEqual(Q.assess(prices(40))["score"], 50.0)
        self.assertEqual(Q.assess(prices(40))["quality"], "insufficient")

    def test_solid_vs_choppy_quality_diagnostics(self):
        smooth = prices(drift=.002, scale=.2)
        choppy = prices(drift=.002, scale=12)
        a, b = Q.assess(smooth), Q.assess(choppy)
        self.assertGreater(a["efficiency_pct"], b["efficiency_pct"])
        self.assertGreater(a["score"], b["score"])

    def test_narrow_sector_scan_is_neutral(self):
        only = [(f"S{i}", "Technology", float(i), True) for i in range(20)]
        res = Q.sector_scores(only)
        self.assertEqual(set(res.values()), {50.0})

    def test_sectors_rank_only_with_broad_sample(self):
        entries = []
        for sector, x in (("Strong", 20), ("Medium", 5), ("Weak", -10)):
            entries.extend((f"{sector}{i}", sector, x, x > 0) for i in range(4))
        r = Q.sector_scores(entries)
        self.assertGreater(r["Strong0"], r["Medium0"])
        self.assertGreater(r["Medium0"], r["Weak0"])


class HunterIntegration(unittest.TestCase):
    def test_seven_factor_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(H.WEIGHTS.values()), 1.0)
        self.assertEqual(set(H.PARTS), set(H.WEIGHTS))

    def test_scan_has_quant_columns_without_fabricated_probabilities(self):
        a = prices(drift=.001)
        b = prices(drift=-.001)
        market = prices(drift=.0003)
        result, detail = H.hunt({"AAA": a, "BBB": b}, market)
        self.assertEqual(len(result), 2)
        for k in ("Quant", "SectorPts", "Vol63 %", "MaxDD63 %", "IR63",
                  "Efficiency %", "PositiveWeeks %", "Flags"):
            self.assertIn(k, result.columns)
        self.assertTrue(result["Score"].between(0, 100).all())
        self.assertTrue(result["Quant"].between(0, 100).all())
        self.assertTrue(result.loc[result["Side"] <= 0, "Score"].le(49).all())

    def test_historical_edge_costs_and_small_sample_warning(self):
        rows = pd.DataFrame({
            "R": [1.0, -1.0, 1.5, -.5],
            "Entry": [100.0] * 4, "Stop": [95.0] * 4,
            "Ret %": [5.0, -5.0, 7.5, -2.5],
        })
        gross = H.edge(rows, round_trip_bps=0)
        net = H.edge(rows, round_trip_bps=30)
        self.assertLess(net["net_avg_r"], gross["avg_r"])
        self.assertEqual(net["n"], 4)
        self.assertFalse(net["sample_adequate"])
        self.assertLessEqual(net["net_win_lower95"], net["net_win_shrunk"])

    def test_missing_data_does_not_raise(self):
        p = prices()
        p.loc[p.index[-1], "Close"] = np.nan
        self.assertEqual(Q.assess(p)["quality"], "insufficient")


if __name__ == "__main__":
    unittest.main()
