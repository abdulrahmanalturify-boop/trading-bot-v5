"""Point-in-time tests for fundamentals.py on a made-up companyfacts file (no network).

Run: python -m unittest discover -s tests -p 'test_fundamentals.py' -v
"""
import unittest

import numpy as np

import fundamentals as F


def fact(val, end, filed, start=None, form="10-K"):
    f = {"val": val, "end": end, "filed": filed, "form": form}
    if start:
        f["start"] = start
    return f


JS = {"facts": {"us-gaap": {
    "NetIncomeLoss": {"units": {"USD": [
        fact(100, "2020-12-31", "2021-02-20", "2020-01-01"),
        fact(30, "2021-03-31", "2021-05-01", "2021-01-01", "10-Q"),          # a quarter: never an annual flow
        fact(120, "2021-12-31", "2022-02-18", "2021-01-01"),
        fact(110, "2021-12-31", "2023-02-17", "2021-01-01"),                 # restated a year later
    ]}},
    "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": [fact(150, "2021-12-31", "2022-02-18", "2021-01-01")]}},
    "Revenues": {"units": {"USD": [fact(1000, "2021-12-31", "2022-02-18", "2021-01-01")]}},
    "CostOfRevenue": {"units": {"USD": [fact(600, "2021-12-31", "2022-02-18", "2021-01-01")]}},
    "StockholdersEquity": {"units": {"USD": [fact(500, "2021-12-31", "2022-02-18"), fact(520, "2022-03-31", "2022-04-29", form="10-Q")]}},
    "Assets": {"units": {"USD": [fact(2000, "2021-12-31", "2022-02-18")]}},
    "LiabilitiesAndStockholdersEquity": {"units": {"USD": [fact(2000, "2021-12-31", "2022-02-18")]}},
    "WeightedAverageNumberOfDilutedSharesOutstanding": {"units": {"shares": [
        fact(50, "2021-12-31", "2022-02-18", "2021-01-01"), fact(48, "2022-03-31", "2022-04-29", "2022-01-01", "10-Q")]}},
}}}


class PointInTime(unittest.TestCase):
    def setUp(self):
        self.f = F.compact(JS)

    def test_nothing_before_it_was_filed(self):
        m = F.as_of(self.f, "2022-02-17")                # a day before the 2021 report
        self.assertEqual(m["ni"], 100)
        self.assertTrue(np.isnan(m["equity"]))

    def test_the_report_counts_from_its_filing_day(self):
        m = F.as_of(self.f, "2022-02-18")
        self.assertEqual(m["ni"], 120)
        self.assertEqual(m["gp"], 400)                   # revenue less cost of revenue
        self.assertEqual(m["liabilities"], 1500)         # total less equity
        self.assertEqual(m["shares"], 50)

    def test_later_quarter_and_restatement(self):
        self.assertEqual(F.as_of(self.f, "2022-05-02")["equity"], 520)
        self.assertEqual(F.as_of(self.f, "2022-05-02")["shares"], 48)
        self.assertEqual(F.as_of(self.f, "2023-02-17")["ni"], 110)

    def test_stale_values_drop(self):
        self.assertTrue(np.isnan(F.as_of(self.f, "2024-06-01")["ni"]))

    def test_ratios_point_the_same_way(self):
        r = F.ratios(F.as_of(self.f, "2022-02-18"), 2400.0)
        self.assertAlmostEqual(r["ep"], 120 / 2400)
        self.assertAlmostEqual(r["roe"], 120 / 500)
        self.assertAlmostEqual(r["lev"], -0.75)
        self.assertAlmostEqual(r["acc"], (150 - 120) / 2000)
        self.assertTrue(np.isnan(F.ratios({"ni": 5, "equity": -10}, 100)["roe"]))   # negative equity: no ROE


if __name__ == "__main__":
    unittest.main()
