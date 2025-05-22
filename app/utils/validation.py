# File: app/utils/validation.py
# (Stub content as previously generated)
def is_valid_uen(uen: str) -> bool:
    # Placeholder for Singapore UEN validation logic
    # Refer to ACRA guidelines for actual validation rules
    if not uen: return True # Optional field based on some model definitions
    # Basic length check example, not real validation
    return len(uen) >= 9 and len(uen) <= 10 
