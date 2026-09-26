import math
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
import academy
from academy_extra import EXTRA_COURSES
from academy_visuals import MARK, WORDMARK, cover
from academy_labs import compound_path, real_return, portfolio, expectancy, perpetuity

class AcademyTests(unittest.TestCase):
    def test_additions_and_complete_bilingual_schema(self):
        self.assertEqual(Counter(c['level'][0] for c in EXTRA_COURSES),{'Beginner':7,'Essential':3,'Advanced':2})
        self.assertEqual(len({c['id'] for c in academy.COURSES}),len(academy.COURSES))
        for c in EXTRA_COURSES:
            self.assertEqual(len(c['sections']),3)
            self.assertEqual(len(c['quiz']),3)
            self.assertTrue(all(len(x)==7 and all(x[:6]) for x in c['sections']))
            for q in c['quiz']:
                self.assertTrue(0<=q[3]<len(q[2]))
                self.assertTrue(all(len(o)==2 and all(o) for o in q[2]))
    def test_art_is_valid_xml(self):
        for svg in [MARK,WORDMARK]+[cover(c['art'],c['id']) for c in academy.COURSES]: ET.fromstring(svg)
    def test_compounding_timing_and_zero_rate(self):
        result=compound_path(1000,100,0,1).iloc[-1]
        self.assertEqual(result.Balance,2200)
        self.assertEqual(result.Contributions,2200)
        self.assertAlmostEqual(compound_path(1000,0,10,2).iloc[-1].Balance,1210)
        self.assertLess(compound_path(1000,0,-10,1).iloc[-1].Balance,1000)
    def test_financial_formulas(self):
        self.assertAlmostEqual(real_return(8,3),4.854368932)
        self.assertAlmostEqual(portfolio(.5,8,8,20,20,0)[1],math.sqrt(200))
        self.assertAlmostEqual(portfolio(.5,8,8,20,20,-1)[1],0)
        self.assertEqual(expectancy(.4,300,100,10),50)
        self.assertAlmostEqual(perpetuity(100,10,3),1428.57142857)
        self.assertIsNone(perpetuity(100,3,3))
        self.assertIsNone(perpetuity(100,2,3))

if __name__=='__main__': unittest.main()
