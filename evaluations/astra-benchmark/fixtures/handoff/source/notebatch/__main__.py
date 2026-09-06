"""Command-line export of a note batch."""
import argparse
from pathlib import Path
from . import read_entries, render_json


def main():
    parser = argparse.ArgumentParser(description='Export a note batch')
    parser.add_argument('input', help='JSON file containing an array of notes')
    args = parser.parse_args()
    print(render_json(read_entries(Path(args.input).read_text())), end='')


if __name__ == '__main__':
    main()
