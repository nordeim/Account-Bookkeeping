# File: app/utils/formatting.py
# (Stub content as previously generated)
from decimal import Decimal
from datetime import date, datetime

def format_currency(amount: Decimal, currency_code: str = "SGD") -> str:
    # This is a placeholder. Use a library like Babel for proper locale-aware formatting.
    return f"{currency_code} {amount:,.2f}"

def format_date(d: date, fmt_str: str = "%d %b %Y") -> str: # Added fmt_str
    return d.strftime(fmt_str) 

def format_datetime(dt: datetime, fmt_str: str = "%d %b %Y %H:%M:%S") -> str: # Added fmt_str
    return dt.strftime(fmt_str)
