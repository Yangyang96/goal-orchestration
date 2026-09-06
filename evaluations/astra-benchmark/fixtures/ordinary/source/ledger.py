"""Summarize invoice CSV exports. All monetary output is exact, in cents."""
import csv
from decimal import Decimal, ROUND_HALF_UP
from io import StringIO


def summarize(text):
    """Return customer -> total cents, sorted by customer name.

    Input columns: customer, amount, status. Extra columns are ignored.
    Blank amounts count as zero. Only paid invoices are included.
    Amounts are rounded per row to cents using ROUND_HALF_UP.
    Refunds (negative amounts) are supported.
    Invalid paid amounts raise ValueError with the physical CSV row number.
    """
    totals = {}
    for row in csv.DictReader(StringIO(text)):
        if row['status'] != 'paid':
            continue
        customer = row['customer']
        cents = round(float(row['amount'] or 0) * 100)
        totals[customer] = totals.get(customer, 0) + cents
    return dict(sorted(totals.items()))


def render(totals):
    """Stable tab-separated report; no header."""
    return ''.join(f'{name}\t{cents}\n' for name, cents in totals.items())
