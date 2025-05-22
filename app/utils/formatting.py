# File: app/utils/formatting.py
# (Content as previously generated, verified)
from decimal import Decimal
from datetime import date, datetime

def format_currency(amount: Decimal, currency_code: str = "SGD") -> str:
    return f"{currency_code} {amount:,.2f}"

def format_date(d: date, fmt_str: str = "%d %b %Y") -> str: 
    return d.strftime(fmt_str) 

def format_datetime(dt: datetime, fmt_str: str = "%d %b %Y %H:%M:%S") -> str: 
    return dt.strftime(fmt_str)
