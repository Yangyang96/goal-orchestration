import unittest
from store import connect, import_events, list_events

class StoreTests(unittest.TestCase):
    def test_fresh_database(self):
        db = connect(':memory:')
        self.addCleanup(db.close)
        self.assertEqual(import_events(db, [{'id': 'a', 'payload': 'value'}]), 1)
        self.assertEqual(list_events(db), [('a', 'value', 'legacy')])

if __name__ == '__main__':
    unittest.main()
