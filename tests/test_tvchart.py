import unittest

import numpy as np
import pandas as pd

import tvchart as TV


class TvSymbolTest(unittest.TestCase):
    def test_symbols(self):
        self.assertEqual(TV.tv_symbol("2222.SR"), "TADAWUL:2222")
        self.assertEqual(TV.tv_symbol("1120"), "TADAWUL:1120")
        self.assertEqual(TV.tv_symbol("^TASI.SR"), "TADAWUL:TASI")
        self.assertEqual(TV.tv_symbol("AAPL"), "AAPL")
        self.assertEqual(TV.tv_symbol("brk-b"), "BRK.B")
        self.assertEqual(TV.tv_symbol("^GSPC"), "SP:SPX")
        self.assertEqual(TV.tv_symbol("BTC-USD"), "BITSTAMP:BTCUSD")
        self.assertEqual(TV.tv_symbol("EURUSD=X"), "FX:EURUSD")


class CandlesTest(unittest.TestCase):
    def frame(self, tz=None):
        idx = pd.date_range("2026-01-02", periods=30, freq="B", tz=tz)
        c = np.linspace(100, 130, 30)
        return pd.DataFrame({"Open": c - 1, "High": c + 2, "Low": c - 2, "Close": c, "Volume": 1e6}, index=idx)

    def test_bars_and_marks(self):
        for tz in (None, "America/New_York"):
            d = self.frame(tz)
            bars, vols = TV.candle_data(d)
            self.assertEqual(len(bars), 30)
            self.assertEqual(len(vols), 30)
            self.assertTrue(all(a["time"] < b["time"] for a, b in zip(bars, bars[1:])))
            trades = pd.DataFrame([
                {"Entry Date": "2026-01-05", "Exit Date": "2026-01-12", "Exit Reason": "Target", "P&L %": 4.2},
                {"Entry Date": "2026-01-20", "Exit Date": None, "Exit Reason": "Open", "P&L %": None},
                {"Entry Date": "2025-01-01", "Exit Date": "2025-02-01", "Exit Reason": "Stop", "P&L %": -1},  # off the chart
            ])
            marks = TV.trade_markers(d, trades, {"BUY": "شراء", "SELL": "بيع"})
            self.assertEqual([m["shape"] for m in marks], ["arrowUp", "arrowDown", "arrowUp"])
            self.assertEqual(marks[1]["text"], "بيع \u2066+4.2%\u2069")
            times = {b["time"] for b in bars}
            self.assertTrue(all(m["time"] in times for m in marks))

    def test_html(self):
        h = TV.candles_html(self.frame(), None)
        self.assertIn("LightweightCharts.createChart", h)
        self.assertNotIn("</script\n", h)
        w = TV.widget_html("2222.SR")
        self.assertIn('"symbol": "TADAWUL:2222"', w)
        self.assertIn("embed-widget-advanced-chart.js", w)


if __name__ == "__main__":
    unittest.main()
