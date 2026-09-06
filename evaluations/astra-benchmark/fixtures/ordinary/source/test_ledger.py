import unittest
from ledger import summarize, render

class LedgerTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(summarize('customer,amount,status\nA,1.20,paid\nB,2,open\n'), {'A': 120})

    def test_render(self):
        self.assertEqual(render({'A': 120}), 'A\t120\n')

if __name__ == '__main__':
    unittest.main()
