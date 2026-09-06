"""Load a route table from a JSON file."""
import json
from pathlib import Path


def load_routes(path):
    """Legacy API: return {route_name: destination} from a JSON file."""
    data = json.loads(Path(path).read_text())
    routes = data['routes']
    if not isinstance(routes, dict):
        raise ValueError('routes must be an object')
    return dict(routes)
