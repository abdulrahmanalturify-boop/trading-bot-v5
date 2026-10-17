"""Opportunity Hunter 3.0 (hunter3.py): no look-ahead, the v1 score replicated, the portfolio's limits, the model's export.

Run: PYTHONPATH=. python -m unittest tests.test_hunter3 -v
"""
import unittest
import warnings

import numpy as np
import pandas as pd

import hunter as H
import hunter3 as H3

warnings.filterwarnings("ignore")


def sample(n=1400, seed=1, gain=.0003, vol=.014, start="2020-01-02"):
    rng = np.random.default_rng(seed)
    ret = np.clip(gain + vol * rng.normal(size=n), -.15, .15)
    c = 80 * np.exp(np.cumsum(ret))
    o = c * (1 + .003 * rng.normal(size=n))
    idx = pd.bdate_range(start, periods=n)
    return pd.DataFrame({"Open": o, "High": np.maximum(o, c) * (1 + .008 * rng.random(n)), "Low": np.minimum(o, c) * (1 - .008 * rng.random(n)),
                         "Close": c, "Volume": 2e6 * (1 + .4 * rng.random(n))}, index=idx)


class Hunter3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bench = sample(seed=99, gain=.0003, vol=.01)
        cls.prices = {f"S{i:02}": sample(seed=i, gain=.0002 + i * .00001, vol=.012 + .0003 * i) for i in range(70)}
        cls.sectors = {s: ("Technology" if i % 3 else "Utilities") for i, s in enumerate(cls.prices)}
        cls.panel = H3.Panel(cls.prices, cls.bench, sectors=cls.sectors)
        cls.state = cls.panel.market_state()
        cls.scores, cls.groups = cls.panel.scores(("v1", "quant", "adaptive"), state=cls.state)

    def test_features_never_look_ahead(self):
        d, b = self.prices["S03"], self.bench
        full = H3.stock_features(H3.clean(d), H3.clean(b, None, 200))
        cut = d.index[-90]
        part = H3.stock_features(H3.clean(d, cut), H3.clean(b, cut, 200))
        cols = [c for c in full.columns if c != "fwd_excess"]
        pd.testing.assert_frame_equal(full.loc[:cut, cols], part[cols], check_exact=False, rtol=1e-9)
        self.assertTrue(full["fwd_excess"].iloc[-H3.HORIZON:].isna().all())

    def test_setups_never_look_ahead_and_match_the_hunter(self):
        d, b = self.prices["S05"], self.bench
        full = H3.setup_panel(H3.clean(d), H3.clean(b, None, 200))
        cut = d.index[-60]
        part = H3.setup_panel(H3.clean(d, cut), H3.clean(b, cut, 200))
        a, p = full.loc[:cut], part
        self.assertEqual(a["key"].astype(str).tolist(), p["key"].astype(str).tolist())
        np.testing.assert_allclose(a["stop"].to_numpy(float), p["stop"].to_numpy(float), equal_nan=True)
        # the last session agrees with hunter.analyze's choice on every stock
        for sym, df in list(self.prices.items())[:25]:
            r = H.analyze(df, b)
            last = self.panel.setups[sym].iloc[-1]
            if r["best"] is None:
                self.assertFalse(isinstance(last["key"], str), sym)
            else:
                self.assertEqual(last["key"], r["best"]["key"], sym)
                self.assertEqual(last["status"], r["best"]["status"], sym)
                self.assertAlmostEqual(float(last["stop"]), float(r["best"]["stop"]), places=6)
                self.assertAlmostEqual(float(last["target"]), float(r["best"]["target"]), places=6)

    def test_v1_score_replicates_hunter_hunt(self):
        res, _ = H.hunt(self.prices, self.bench, sectors=self.sectors)
        panel = self.scores["v1"].iloc[-1]
        both = pd.DataFrame({"hunt": res.set_index("Symbol")["Score"], "panel": panel}).dropna()
        self.assertGreaterEqual(len(both), 60)
        self.assertLess((both["hunt"] - both["panel"]).abs().max(), 0.2)      # hunt() rounds to one decimal

    def test_scores_are_ranks_between_0_and_100_and_gate_on_a_long_setup(self):
        side = self.panel.col("side", "setups")
        for m, frame in self.scores.items():
            v = frame.to_numpy(float)
            self.assertTrue(np.nanmin(v) >= 0 and np.nanmax(v) <= 100, m)
            no_long = ~(side >= 0) if m == "v1" else ~(side > 0)      # the old Hunter lets a watch-state setup through
            self.assertTrue((frame.where(no_long).fillna(0) <= 49).all().all(), m)

    def test_market_state(self):
        st = self.state
        self.assertTrue(st["regime"].isin(H3.REGIMES).all())
        self.assertTrue(st["breadth50"].dropna().between(0, 100).all())
        self.assertTrue(st["vol_pct"].dropna().between(0, 100).all())

    def test_portfolio_limits(self):
        res, state, groups, panel = H3.scan(self.prices, self.bench, sectors=self.sectors)
        cands = res.rename(columns={"score_adaptive": "Score"})
        cands = cands[cands["Side"] > 0].head(30)
        pos, summ = H3.build_portfolio(cands, panel, capital=100_000, risk_pct=1.0, max_pos=6, sector_cap=2, regime="bull")
        self.assertLessEqual(len(pos), 6)
        self.assertTrue((pos.groupby("Sector").size() <= 2).all())
        self.assertLessEqual(pos["Notional"].sum(), 100_000 + 1e-6)
        self.assertTrue((pos["Risk %"] <= 1.0 + 1e-9).all())
        self.assertTrue((pos["Weight %"] <= 20 + 1e-9).all())
        bear, s2 = H3.build_portfolio(cands, panel, capital=100_000, max_pos=6, regime="bear")
        self.assertLessEqual(s2["invested_pct"], H3.EXPOSURE["bear"] * 100 + 1e-6)
        braked, s3 = H3.build_portfolio(cands, panel, capital=100_000, max_pos=6, regime="bull", drawdown=-12)
        self.assertTrue(s3["drawdown_brake"])
        self.assertLessEqual(s3["invested_pct"], 50 + 1e-6)
        # a stock correlated with one already chosen is skipped
        twin = {**self.prices, "TWIN": self.prices[cands["Symbol"].iloc[0]] * 1.01}
        res2, _, _, panel2 = H3.scan(twin, self.bench, sectors={**self.sectors, "TWIN": "Healthcare"})
        c2 = res2.rename(columns={"score_adaptive": "Score"})
        c2 = c2[c2["Side"] > 0]
        if "TWIN" in set(c2["Symbol"]) and cands["Symbol"].iloc[0] in set(c2["Symbol"]):
            pos2, s4 = H3.build_portfolio(c2, panel2, capital=100_000, max_pos=8, sector_cap=8, regime="bull")
            self.assertFalse({"TWIN", cands["Symbol"].iloc[0]} <= set(pos2["Symbol"]))

    def test_explain_and_why(self):
        res, state, groups, panel = H3.scan(self.prices, self.bench, sectors=self.sectors)
        row = res.iloc[0]
        ex = panel.explain(row["Symbol"], "adaptive", None, groups, None, state)
        self.assertEqual({e["group"] for e in ex}, set(H3.GROUPS))
        w = sum(e["weight"] for e in ex)
        self.assertAlmostEqual(w, 1.0, places=3)
        case = H3.why(row, panel, "adaptive", groups, state, ar=True)
        self.assertTrue(case["invalidation"] and case["uncertain"])

    def test_model_export_matches_sklearn(self):
        try:
            from sklearn.ensemble import HistGradientBoostingClassifier
        except Exception:
            self.skipTest("scikit-learn not installed")
        rng = np.random.default_rng(0)
        X = rng.normal(size=(3000, 6))
        X[rng.random(X.shape) < 0.05] = np.nan
        y = (np.nan_to_num(X[:, 0]) + 0.5 * np.nan_to_num(X[:, 1]) + rng.normal(size=3000) * 0.5 > 0).astype(int)
        clf = HistGradientBoostingClassifier(max_iter=40, max_depth=3, random_state=0).fit(X, y)
        m = H3.export_hgb(clf, [f"f{i}" for i in range(6)])
        import json, tempfile, os
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(m, f)
        loaded = H3.load_model(f.name)
        os.unlink(f.name)
        raw = H3.predict_raw(loaded, X[:500])
        np.testing.assert_allclose(1 / (1 + np.exp(-raw)), clf.predict_proba(X[:500])[:, 1], atol=1e-6)

    def test_weights_fallback(self):
        w = H3.load_weights("/nonexistent/hunter3_weights.json")
        self.assertEqual(set(w), set(H3.REGIMES))
        self.assertAlmostEqual(sum(w["bull"].values()), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
