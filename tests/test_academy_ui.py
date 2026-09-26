from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest
import academy_extra as E

class AcademyUI(unittest.TestCase):
    def test_catalog_labs_and_course_completion(self):
        app=str(Path(__file__).with_name('academy_preview_app.py'))
        at=AppTest.from_file(app,default_timeout=30).run()
        assert not at.exception,[e.message for e in at.exception]
        assert len([b for b in at.button if b.key and b.key.startswith('crsb_')])==21
        at.text_input(key='ac_search').set_value('nonsense-no-match').run()
        assert any('No matching' in x.value for x in at.info)
        at.text_input(key='ac_search').set_value('').run()
        at.selectbox(key='ac_status').set_value('new').run()
        assert len([b for b in at.button if b.key and b.key.startswith('crsb_')])==12
        for lang in ['en','ar']:
         at.selectbox(key='lang').set_value(lang).run()
         for lab in ['compound','inflation','allocation','expectancy','duration','valuation','journal']:
          at.selectbox(key='ac_lab').set_value(lab).run()
          assert not at.exception,(lang,lab,[x.message for x in at.exception])
        print('PASS catalog search, 12-new filter, 7 labs in both languages')
        for course in E.EXTRA_COURSES:
         cid=course['id']
         at.session_state['course']=cid
         at.session_state[f'step_{cid}']=2
         at.run()
         assert not at.exception,(cid,[x.message for x in at.exception])
         at.session_state[f'step_{cid}']=3
         at.run()
         assert len(at.radio)==3
         for i,q in enumerate(course['quiz']): at.radio(key=f'q_{cid}_{i}').set_value(q[3])
         next(b for b in at.button if b.label in ('Check answers','تحقق من الإجابات')).click().run()
         assert cid in at.session_state['completed'],cid
         assert not at.exception
        print('PASS 12 course final lessons, quiz submissions and completion state')
