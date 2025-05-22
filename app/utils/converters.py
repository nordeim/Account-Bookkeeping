# File: app/utils/converters.py
# (Stub content as previously generated)
from decimal import Decimal, InvalidOperation

def to_decimal(value: any, default: Decimal = Decimal(0)) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError): # Catch more conversion errors
        return default
