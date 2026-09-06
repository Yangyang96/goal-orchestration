import json
import unittest
from notebatch import normalize_entries, read_entries, render_json


class NoteBatchTests(unittest.TestCase):
    def test_existing_normalized_entry(self):
        value = [{'title': 'Inbox', 'tags': ['home']}]
        self.assertEqual(normalize_entries(value), value)

    def test_empty_batch(self):
        self.assertEqual(read_entries('[]'), [])

    def test_json_output(self):
        value = [{'title': '中文', 'tags': []}]
        rendered = render_json(value)
        self.assertEqual(json.loads(rendered), value)
        self.assertTrue(rendered.endswith('\n'))
        self.assertIn('中文', rendered)


if __name__ == '__main__':
    unittest.main()
