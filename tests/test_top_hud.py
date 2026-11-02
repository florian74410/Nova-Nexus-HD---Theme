import unittest
from App.top_hud import clamp, strut
class TopHUDTests(unittest.TestCase):
    def test_range(self):
        self.assertEqual(clamp(55),50)
        self.assertEqual(clamp(1),20)
        self.assertEqual(clamp(21,True),20)
        self.assertEqual(clamp(0,True),10)
    def test_strut(self):
        self.assertEqual(strut(1920,30),[0,0,30,0,0,0,0,0,0,1919,0,0])
