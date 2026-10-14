import unittest
from analytics import parse_csv, analyze, classify

HEADER = 'tutor_id,student_id,subject,session_completed,rating,price,location\n'
class AnalyticsTests(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual([classify(d,s) for d,s in [(4,1),(3,1),(1,1),(0,1),(1,0),(0,0)]], ['High demand','Moderate demand','Balanced','Low demand','No supply','No activity'])
    def test_distinct_and_dedup(self):
        row = 'T1,S1,Math,2,4,100,Puducherry\n'
        rows = parse_csv(HEADER+row+row+'T1,S2,Math,3,5,100,Puducherry\n')
        result = analyze(rows)
        self.assertEqual(result['records'],2)
        self.assertEqual((result['subjects'][0]['demand'],result['subjects'][0]['supply']),(2,1))
        self.assertEqual(result['tutors'][0]['sessions'],3)
    def test_zero_supply(self):
        result = analyze(parse_csv(HEADER+',S1,Math,,,,Chennai\n'))
        self.assertIsNone(result['subjects'][0]['ratio'])
        self.assertEqual(result['subjects'][0]['additional_tutors'],1)
    def test_invalid_data(self):
        for value in ['nan','inf','-1','6']:
            with self.assertRaises(ValueError):
                parse_csv(HEADER+f'T1,S1,Math,2,{value},100,Chennai\n')
    def test_filter(self):
        rows = parse_csv(HEADER+'T1,S1,Math,2,4,100,A\nT2,S2,Math,2,4,100,B\n')
        self.assertEqual(analyze(rows,'A')['summary']['tutors'],1)
    def test_tutor_weighted_mean(self):
        rows = parse_csv(HEADER+'T1,S1,Math,2,5,100,A\nT1,S2,Math,2,5,100,A\nT2,,Math,2,1,200,A\n')
        self.assertEqual(analyze(rows)['subjects'][0]['rating'],3)
if __name__ == '__main__':
    unittest.main()
