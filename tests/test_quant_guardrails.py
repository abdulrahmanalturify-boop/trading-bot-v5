"""Regression tests for opt-in strategy backtest safeguards and research splits.

Run from repository root:
    python -m unittest discover -s tests -p 'test_quant_guardrails.py' -v
"""
import unittest

import numpy as np
import pandas as pd

import engine
import quant_validation as Q


class BacktestRiskTests(unittest.TestCase):
    def setUp(self):
        ix = pd.bdate_range("2024-01-01", periods=260)
        self.df = pd.DataFrame({
            "Open": np.full(len(ix), 100.0),
            "High": np.full(len(ix), 102.0),
            "Low": np.full(len(ix), 98.0),
            "Close": np.full(len(ix), 100.0),
            "Volume": np.full(len(ix), 1_000_000.0),
        }, index=ix)
        self.entries = pd.Series(False, index=ix)
        self.exits = pd.Series(False, index=ix)
        self.entries.iloc[210] = True
        self.exits.iloc[213] = True

    def test_opt_in_risk_budget_sizes_using_stop(self):
        res = engine.backtest(self.df, self.entries, self.exits,
                              capital=10_000.0, fee=0, stop_pct=5,
                              risk_per_trade_pct=1.0)
        # 1% of $10k = $100 risk; $5/share stop distance => 20 shares.
        self.assertAlmostEqual(res["trades"].iloc[0]["Shares"], 20.0)

    def test_allocation_cap_takes_minimum_of_caps(self):
        res = engine.backtest(self.df, self.entries, self.exits,
                              capital=10_000.0, fee=0, stop_pct=5,
                              risk_per_trade_pct=1.0, max_allocation_pct=10.0)
        # $1k cap at $100/share => 10 shares.
        self.assertAlmostEqual(res["trades"].iloc[0]["Shares"], 10.0)

    def test_risk_sized_trade_requires_valid_stop(self):
        res = engine.backtest(self.df, self.entries, self.exits,
                              capital=10_000.0, fee=0, risk_per_trade_pct=1.0)
        self.assertEqual(len(res["trades"]), 0)

    def test_default_full_cash_remains_backward_compatible(self):
        res = engine.backtest(self.df, self.entries, self.exits,
                              capital=10_000.0, fee=0, stop_pct=5)
        self.assertAlmostEqual(res["trades"].iloc[0]["Shares"], 100.0)

    def test_slippage_is_adverse_on_both_sides(self):
        res = engine.backtest(self.df, self.entries, self.exits,
                              capital=10_000.0, fee=0, stop_pct=5,
                              slippage_bps=100)
        trade = res["trades"].iloc[0]
        self.assertAlmostEqual(trade["Entry"], 101.0)
        self.assertAlmostEqual(trade["Exit"], 99.0)
        self.assertLess(trade["P&L $"], 0)

    def test_circuit_breaker_blocks_new_buys_after_drawdown(self):
        # Exit the first trade after a 10% overnight gap.
        d = self.df.copy()
        d.iloc[214, d.columns.get_loc("Open")] = 90.0
        d.iloc[214, d.columns.get_loc("Close")] = 90.0
        d.iloc[214, d.columns.get_loc("High")] = 92.0
        d.iloc[214, d.columns.get_loc("Low")] = 88.0
        entries = self.entries.copy()
        entries.iloc[214] = True  # would buy next morning absent the circuit breaker
        res = engine.backtest(d, entries, self.exits,
                              capital=10_000.0, fee=0, max_drawdown_pct=5.0)
        self.assertEqual(len(res["trades"]), 1)
        self.assertTrue(bool(res["risk_halt"].iloc[214]))
        self.assertTrue(bool(res["risk_halt"].iloc[-1]))

    def test_reject_invalid_controls(self):
        with self.assertRaises(ValueError):
            engine.backtest(self.df, self.entries, self.exits, slippage_bps=10000)
        with self.assertRaises(ValueError):
            engine.backtest(self.df, self.entries, self.exits, max_drawdown_pct=0)


class ResearchValidationTests(unittest.TestCase):
    def test_walk_forward_gap_and_nonoverlapping_tests(self):
        windows = list(Q.embargoed_walk_forward(150, train_size=60,
                                                test_size=20, gap=10))
        self.assertEqual(len(windows), 4)
        for w in windows:
            self.assertGreaterEqual(w.test_start - w.train_stop, 10)
            self.assertEqual(w.train_start, 0)
        for a, b in zip(windows, windows[1:]):
            self.assertLessEqual(a.test_stop, b.test_start)

    def test_rolling_has_fixed_training_size(self):
        windows = list(Q.embargoed_walk_forward(150, train_size=60,
                                                test_size=20, gap=10, expanding=False))
        self.assertTrue(all(w.train_stop - w.train_start == 60 for w in windows))
        self.assertGreater(windows[-1].train_start, 0)

    def test_reject_overlapping_test_periods(self):
        with self.assertRaises(ValueError):
            list(Q.embargoed_walk_forward(200, train_size=60,
                                          test_size=20, gap=10, step=5))

    def test_return_statistics_and_bootstrap_are_deterministic(self):
        net = np.array([0.01, -0.02, 0.005, -0.001, 0.003])
        x = Q.return_statistics(net, np.zeros(len(net)))
        self.assertLessEqual(x["max_drawdown_pct"], 0)
        self.assertEqual(x["days"], 5)
        self.assertIn("excess_total_return_pct", x)
        a = Q.block_bootstrap_drawdown(net, block_size=2, simulations=30, seed=5)
        b = Q.block_bootstrap_drawdown(net, block_size=2, simulations=30, seed=5)
        self.assertEqual(a, b)
        self.assertLessEqual(a["p05_drawdown_pct"], a["p95_drawdown_pct"])


if __name__ == "__main__":
    unittest.main()
