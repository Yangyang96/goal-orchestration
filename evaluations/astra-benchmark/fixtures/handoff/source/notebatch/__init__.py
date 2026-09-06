"""Utilities for preparing a batch of notes for export."""
import json


def normalize_entries(entries):
    """Return normalized entries without modifying the caller's input."""
    return list(entries)


def read_entries(text):
    return normalize_entries(json.loads(text))


def render_json(entries):
    """Legacy output is a JSON array with one final newline."""
    return json.dumps(entries, ensure_ascii=False, indent=2) + '\n'
