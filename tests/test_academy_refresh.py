"""Regression checks for the short-course catalog, persistence, and learner actions."""
from pathlib import Path
import json
import base64
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
import academy as A
import academy_micro as M

APP = str(Path(__file__).with_name('academy_preview_app.py'))

class MicroContent(unittest.TestCase):
    def test_catalog_and_financial_examples(self):
        self.assertEqual(len(A.COURSES),37)
        self.assertEqual(sum(c['level'][0]=='Beginner' for c in A.COURSES),26)
        self.assertEqual(len(set(c['id'] for c in A.COURSES)),37)
        for c in M.MICRO_COURSES:
            self.assertEqual(len(c['sections']),3)
            self.assertEqual(len(c['quiz']),3)
            self.assertLessEqual(c['mins'],4)
            for s in c['sections']:
                self.assertEqual(len(s),7)
                self.assertTrue(all(s[:6]))
            for q in c['quiz']:
                self.assertTrue(0 <= q[3] < len(q[2]))
        gain,ret=M.net_return(100,110,2,1,1,1)
        self.assertEqual(gain,10)
        self.assertAlmostEqual(ret,10/101*100)
        self.assertEqual(M.recovery(20),25)
        self.assertEqual(M.recovery(50),100)
        self.assertEqual(M.recovery(0),0)

    def test_progress_migration_and_invalid_input(self):
        import p_academy as P
        state={}
        with patch.object(P,'ss',state):
            P._progress_load('12d_14x2_24d_-1d_999d')
            self.assertEqual(state['completed'],{'candles','robustness'})
            self.assertEqual(state['step_risk'],2)
            encoded=P._progress_code()
            import p_portfolio as PP
            self.assertTrue(PP._STORE_VAL.fullmatch(encoded))
            state.clear()
            P._progress_load(encoded)
            self.assertEqual(state['completed'],{'candles','robustness'})
            self.assertEqual(state['step_risk'],2)
            P._progress_load('v2_'+base64.urlsafe_b64encode(json.dumps({'done':['missing',{}], 'steps':{'risk':999,'basics':-1}}).encode()).decode().rstrip('='))
            self.assertEqual(state['step_risk'],len(next(c for c in A.COURSES if c['id']=='risk')['sections']))
            self.assertEqual(state['step_basics'],0)
            for bad in ['v2_bad','v2_W10','v2_eyJkb25lIjpudWxsLCJzdGVwcyI6W119']:
                P._progress_load(bad)

class LearnerFlow(unittest.TestCase):
    def ok(self,at):
        self.assertFalse(at.exception,[e.message for e in at.exception])

    def test_catalog_materials_and_all_labs_bilingual(self):
        at=AppTest.from_file(APP,default_timeout=40).run();self.ok(at)
        self.assertEqual(len([b for b in at.button if b.key and b.key.startswith('crsb_')]),9)
        at.selectbox(key='ac_page').set_value(5).run();self.ok(at)
        at.text_input(key='ac_search').set_value('nonsense-no-match').run();self.ok(at)
        self.assertTrue(any('No matching' in x.value for x in at.info))
        at.text_input(key='ac_search').set_value('loss').run();self.ok(at)
        self.assertEqual(at.selectbox(key='ac_page').value,1)
        at.text_input(key='ac_search').set_value('').run()
        at.select_slider(key='ac_duration').set_value(4).run();self.ok(at)
        for lang in ['en','ar']:
            at.selectbox(key='lang').set_value(lang).run();self.ok(at)
            for key in list(M.LABS)+['compound','inflation','allocation','expectancy','duration','valuation','journal']:
                at.selectbox(key='ac_lab').set_value(key).run();self.ok(at)
            at.selectbox(key='ac_material_course').set_value('total_return').run();self.ok(at)
            # AppTest exposes segmented controls as button_group.
            at.button_group(key='ac_material_type').set_value('cards').run();self.ok(at)
            at.checkbox(key='reveal_total_return_0').check().run();self.ok(at)
            self.assertTrue(at.success)
            at.button_group(key='ac_material_type').set_value('notes').run();self.ok(at)

    def test_new_lessons_quiz_and_completion(self):
        at=AppTest.from_file(APP,default_timeout=40).run()
        for lang in ['en','ar']:
            at.selectbox(key='lang').set_value(lang).run()
            for course in M.MICRO_COURSES:
                cid=course['id']
                at.session_state['course']=cid
                for step in [0,1,2]:
                    at.session_state[f'step_{cid}']=step
                    at.run();self.ok(at)
                    at.radio(key=f'checkpoint_{cid}_{step}').set_value(course['quiz'][step][3]).run();self.ok(at)
                    self.assertTrue(at.success)
                # Real navigation from last lesson to quiz.
                next(b for b in at.button if b.label in ['Take the quiz','ابدأ الاختبار']).click().run();self.ok(at)
                submit=next(b for b in at.button if b.label in ['Check answers','تحقق من الإجابات'])
                if lang=='en':
                    submit.click().run()
                    self.assertTrue(at.warning)
                for i,q in enumerate(course['quiz']):
                    at.radio(key=f'q_{cid}_{i}').set_value(q[3])
                next(b for b in at.button if b.label in ['Check answers','تحقق من الإجابات']).click().run();self.ok(at)
                self.assertIn(cid,at.session_state['completed'])
            next(b for b in at.button if b.label in ['All courses','كل الدورات']).click().run();self.ok(at)
        self.assertEqual(len(at.session_state['completed']),12)

if __name__=='__main__':
    unittest.main()
