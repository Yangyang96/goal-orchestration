import json
import tempfile
import unittest
from pathlib import Path
from routebook import load_routes


class RouteTests(unittest.TestCase):
    def test_legacy(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'routes.json'
            p.write_text(json.dumps({'routes': {'home': 'https://example.invalid'}}))
            self.assertEqual(load_routes(p), {'home': 'https://example.invalid'})


if __name__ == '__main__':
    unittest.main()
