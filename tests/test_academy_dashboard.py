"""Verify real learner activity, resume state and compatibility with saved progress."""
import base64
from datetime import date, timedelta
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import academy as A
import academy_learning as LE
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).with_name("academy_preview_app.py"))


class LearnerActivity(unittest.TestCase):
    def test_real_activity_no_double_count_and_week_boundary(self):
        now = date(2026, 10, 14)
        meta = LE.clean({}, A.COURSES, now)
        LE.lesson(meta, "basics", 0, now - timedelta(days=2))
        LE.lesson(meta, "basics", 0, now)
        LE.lesson(meta, "basics", 1, now - timedelta(days=1))
        LE.challenge(meta, now)
        LE.lesson(meta, "price_value", 0, now - timedelta(days=3))
        stats = LE.stats(meta, A.COURSES, {"total_return"}, {}, now)
        self.assertEqual(stats["weekly"], 2)
        self.assertEqual(stats["streak"], 4)
        self.assertEqual(stats["lessons"], 6)
        self.assertIsNone(stats["accuracy"])
        self.assertEqual(len(stats["activity"]), 7)
        self.assertEqual(meta["last"], "price_value")

    def test_invalid_data_and_latest_quiz_results(self):
        now = date(2026, 10, 14)
        meta = LE.clean({"last": "missing", "goal": True, "lessons": [{}, "basics:999", "basics:0"],
            "activity": {"not-a-date": {}, "2099-01-01": {}, "2026-10-13": {"lessons": ["basics:0", "basics:0"]}},
            "quizzes": {"basics": {"score": 2}, "price_value": {"score": 999}, "total_return": {"score": True}}}, A.COURSES, now)
        self.assertEqual(meta["goal"], 5)
        self.assertIsNone(meta["last"])
        self.assertEqual(meta["lessons"], ["basics:0"])
        self.assertEqual(list(meta["activity"]), ["2026-10-13"])
        self.assertEqual(list(meta["quizzes"]), ["basics"])
        meta["quizzes"]["basics"] = {"score": 3, "total": 3}
        self.assertEqual(LE.stats(meta, A.COURSES, set(), {}, now)["accuracy"], 100)
        self.assertEqual(LE.stats(meta, A.COURSES, set(), {}, now)["streak"], 1)

    def test_compressed_round_trip_and_legacy_activity_not_fabricated(self):
        import p_academy as P
        import p_portfolio as PP
        state = {}
        with patch.object(P, "ss", state):
            payload = {"done": ["basics"], "steps": {"total_return": 2}}
            legacy = "v2_" + base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
            P._progress_load(legacy)
            self.assertEqual(P._learning_stats()["weekly"], 0)
            self.assertEqual(P._learning_stats()["lessons"], len(next(c for c in A.COURSES if c["id"] == "basics")["sections"]) + 2)
            meta = P._learning()
            meta["goal"] = 10
            meta["last"] = "price_value"
            meta["lessons"] = [f"{c['id']}:{i}" for c in A.COURSES for i in range(len(c["sections"]))]
            for i in range(91):
                LE.challenge(meta, LE.today() - timedelta(days=i))
            meta["quizzes"] = {c["id"]: {"score": len(c["quiz"]), "total": len(c["quiz"])} for c in A.COURSES}
            encoded = P._progress_code()
            self.assertTrue(PP._STORE_VAL.fullmatch(encoded), len(encoded))
            state.clear()
            P._progress_load(encoded)
            self.assertEqual(P._learning()["goal"], 10)
            self.assertEqual(P._learning()["last"], "price_value")
            self.assertEqual(state["completed"], {"basics"})
            self.assertEqual(P._learning_stats()["accuracy"], 100)
            for bad in ["v3_bad", "v3_" + base64.urlsafe_b64encode(b"plain-json").decode()]:
                P._progress_load(bad)


class DashboardFlow(unittest.TestCase):
    def ok(self, at):
        self.assertFalse(at.exception, [e.message for e in at.exception])

    def test_dashboard_goal_daily_challenge_and_resume_bilingual(self):
        at = AppTest.from_file(APP, default_timeout=40).run()
        self.ok(at)
        self.assertEqual(at.tabs[0].label, "Dashboard")
        at.button_group(key="ac_week_goal").set_value(10).run()
        self.ok(at)
        self.assertEqual(at.session_state["ac_learning"]["goal"], 10)
        _, _, question = LE.daily_question(A.COURSES)
        daily = "ac_daily_"+LE.today().isoformat()
        at.radio(key=daily).set_value(question[3]).run()
        self.ok(at)
        self.assertTrue(at.session_state["ac_learning"]["activity"][LE.today().isoformat()]["challenge"])
        at.text_input(key="ac_search").set_value(next(c for c in A.COURSES if c["id"] == "total_return")["title"][0]).run()
        at.button(key="crsb_total_return").click().run()
        self.ok(at)
        next(b for b in at.button if b.label == "Next").click().run()
        self.assertIn("total_return:0", at.session_state["ac_learning"]["lessons"])
        next(b for b in at.button if b.label == "All courses").click().run()
        at.button(key="ac_beginner_start").click().run()
        self.ok(at)
        self.assertEqual(at.session_state["course"], "total_return")
        self.assertEqual(at.session_state["step_total_return"], 1)
        next(b for b in at.button if b.label == "All courses").click().run()
        at.selectbox(key="lang").set_value("ar").run()
        self.ok(at)
        self.assertEqual(at.tabs[0].label, "لوحة التعلّم")
        at.text_input(key="ac_search").set_value("").run()
        at.selectbox(key="ac_sort").set_value("short").run()
        self.ok(at)
        self.assertEqual(at.selectbox(key="ac_page").value, 1)
        expected = [c["id"] for c in sorted(A.COURSES, key=lambda c: (c["mins"], A.LEVEL_ORDER.index(c["level"][0])))[:9]]
        self.assertEqual([b.key.removeprefix("crsb_") for b in at.button if b.key and b.key.startswith("crsb_")], expected)
        at.button(key="ac_beginner_start").click().run()
        self.ok(at)
        next(b for b in at.button if b.label == "التالي").click().run()
        self.ok(at)
        self.assertIn("total_return:1", at.session_state["ac_learning"]["lessons"])


if __name__ == "__main__":
    unittest.main()
