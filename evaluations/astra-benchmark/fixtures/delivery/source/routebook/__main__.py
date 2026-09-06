import argparse
import json
from .core import load_routes


def main():
    parser = argparse.ArgumentParser(description='Read route destinations')
    parser.add_argument('config')
    args = parser.parse_args()
    print(json.dumps(load_routes(args.config), sort_keys=True))


if __name__ == '__main__':
    main()
