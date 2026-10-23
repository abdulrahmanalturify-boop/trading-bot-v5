"""Kuhailan's spending ceilings: the site-wide day / month / dollar limits and the per-visitor limits stop a question before
it reaches OpenAI, and the counts survive a restart (they are kept in a file)."""
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ai_assistant as A


class LimitsTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.file = mock.patch.object(A, "USAGE_FILE", os.path.join(self.dir, "u.json")); self.file.start()
        self.env = {}
        self.sec = mock.patch.object(A, "secret", lambda n, d="": self.env.get(n, d)); self.sec.start()
        A._U.update({"loaded": True, "day": None, "n": 0, "month": None, "mn": 0, "tin": 0, "tout": 0, "usd": 0.0, "who": {},
                     "quota": None})

    def tearDown(self):
        self.file.stop(); self.sec.stop()

    def test_daily_site_limit(self):
        self.env["AI_DAILY_LIMIT"] = "3"
        self.assertEqual([A._take(f"v{i}") for i in range(4)], [None, None, None, "day"])

    def test_monthly_limit(self):
        self.env["AI_MONTHLY_LIMIT"] = "2"
        self.assertEqual([A._take(f"v{i}") for i in range(3)], [None, None, "month"])

    def test_visitor_hour_and_day(self):
        self.env.update({"AI_VISITOR_HOURLY_LIMIT": "2", "AI_VISITOR_DAILY_LIMIT": "3"})
        t = 1_000_000.0
        self.assertIsNone(A._take("a", t)); self.assertIsNone(A._take("a", t + 1))
        self.assertEqual(A._take("a", t + 2), "visitor_hour")
        self.assertIsNone(A._take("b", t + 2))                 # another visitor is not held back
        self.assertIsNone(A._take("a", t + 3700))              # an hour later
        self.assertEqual(A._take("a", t + 7400), "visitor_day")

    def test_budget_from_tokens(self):
        self.env.update({"AI_MONTHLY_BUDGET_USD": "0.01", "AI_PRICE_IN_PER_M": "1", "AI_PRICE_OUT_PER_M": "10"})
        self.assertIsNone(A._take("a"))
        A._spent({"usage": {"input_tokens": 1000, "output_tokens": 900}})   # 0.001 + 0.009 = 0.01 dollars
        self.assertAlmostEqual(A._U["usd"], 0.01)
        self.assertEqual(A._take("b"), "budget")

    def test_switch_off(self):
        self.env["AI_ASSISTANT"] = "off"
        self.assertEqual(A._take("a"), "off")
        self.assertEqual(A._U["n"], 0)

    def test_counts_survive_restart(self):
        A._take("a"); A._take("b")
        A._U.update({"loaded": False, "n": 0, "mn": 0})
        A._load_usage()
        self.assertEqual((A._U["n"], A._U["mn"]), (2, 2))

    def test_arabic_messages(self):
        for k in A._LIMIT_MSG:
            ar = A.limit_message(k, "ar")
            self.assertFalse(any("a" <= c.lower() <= "z" for c in ar), ar)


if __name__ == "__main__":
    unittest.main()
