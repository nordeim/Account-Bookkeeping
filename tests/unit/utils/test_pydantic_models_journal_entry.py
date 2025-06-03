# File: tests/unit/utils/test_pydantic_models_journal_entry.py
import pytest
from decimal import Decimal
from datetime import date

from pydantic import ValidationError

from app.utils.pydantic_models import JournalEntryLineData, JournalEntryData
from app.common.enums import JournalTypeEnum

# --- Tests for JournalEntryLineData ---

def test_jel_valid_debit_only():
    """Test JournalEntryLineData with valid debit amount and zero credit."""
    data = {
        "account_id": 1, "description": "Test debit", 
        "debit_amount": Decimal("100.00"), "credit_amount": Decimal("0.00")
    }
    try:
        line = JournalEntryLineData(**data)
        assert line.debit_amount == Decimal("100.00")
        assert line.credit_amount == Decimal("0.00")
    except ValidationError as e:
        pytest.fail(f"Validation failed for valid debit-only line: {e}")

def test_jel_valid_credit_only():
    """Test JournalEntryLineData with valid credit amount and zero debit."""
    data = {
        "account_id": 1, "description": "Test credit", 
        "debit_amount": Decimal("0.00"), "credit_amount": Decimal("100.00")
    }
    try:
        line = JournalEntryLineData(**data)
        assert line.debit_amount == Decimal("0.00")
        assert line.credit_amount == Decimal("100.00")
    except ValidationError as e:
        pytest.fail(f"Validation failed for valid credit-only line: {e}")

def test_jel_valid_zero_amounts():
    """Test JournalEntryLineData with zero debit and credit amounts (might be valid for placeholder lines)."""
    data = {
        "account_id": 1, "description": "Test zero amounts", 
        "debit_amount": Decimal("0.00"), "credit_amount": Decimal("0.00")
    }
    try:
        line = JournalEntryLineData(**data)
        assert line.debit_amount == Decimal("0.00")
        assert line.credit_amount == Decimal("0.00")
    except ValidationError as e:
        pytest.fail(f"Validation failed for zero amount line: {e}")

def test_jel_invalid_both_debit_and_credit_positive():
    """Test JournalEntryLineData fails if both debit and credit are positive."""
    data = {
        "account_id": 1, "description": "Invalid both positive", 
        "debit_amount": Decimal("100.00"), "credit_amount": Decimal("50.00")
    }
    with pytest.raises(ValidationError) as excinfo:
        JournalEntryLineData(**data)
    assert "Debit and Credit amounts cannot both be positive for a single line." in str(excinfo.value)

# --- Tests for JournalEntryData ---

@pytest.fixture
def sample_valid_lines() -> list[dict]:
    return [
        {"account_id": 101, "debit_amount": Decimal("100.00"), "credit_amount": Decimal("0.00")},
        {"account_id": 201, "debit_amount": Decimal("0.00"), "credit_amount": Decimal("100.00")},
    ]

@pytest.fixture
def sample_unbalanced_lines() -> list[dict]:
    return [
        {"account_id": 101, "debit_amount": Decimal("100.00"), "credit_amount": Decimal("0.00")},
        {"account_id": 201, "debit_amount": Decimal("0.00"), "credit_amount": Decimal("50.00")}, # Unbalanced
    ]

def test_je_valid_data(sample_valid_lines: list[dict]):
    """Test JournalEntryData with valid, balanced lines."""
    data = {
        "journal_type": JournalTypeEnum.GENERAL.value,
        "entry_date": date(2023, 1, 15),
        "user_id": 1,
        "lines": sample_valid_lines
    }
    try:
        entry = JournalEntryData(**data)
        assert len(entry.lines) == 2
        assert entry.lines[0].debit_amount == Decimal("100.00")
    except ValidationError as e:
        pytest.fail(f"Validation failed for valid journal entry: {e}")

def test_je_invalid_empty_lines():
    """Test JournalEntryData fails if lines list is empty."""
    data = {
        "journal_type": JournalTypeEnum.GENERAL.value,
        "entry_date": date(2023, 1, 15),
        "user_id": 1,
        "lines": [] # Empty lines
    }
    with pytest.raises(ValidationError) as excinfo:
        JournalEntryData(**data)
    assert "Journal entry must have at least one line." in str(excinfo.value)

def test_je_invalid_unbalanced_lines(sample_unbalanced_lines: list[dict]):
    """Test JournalEntryData fails if lines are not balanced."""
    data = {
        "journal_type": JournalTypeEnum.GENERAL.value,
        "entry_date": date(2023, 1, 15),
        "user_id": 1,
        "lines": sample_unbalanced_lines
    }
    with pytest.raises(ValidationError) as excinfo:
        JournalEntryData(**data)
    assert "Journal entry must be balanced" in str(excinfo.value)

def test_je_valid_lines_with_optional_fields(sample_valid_lines: list[dict]):
    """Test JournalEntryData with optional fields present."""
    lines_with_optionals = [
        {**sample_valid_lines[0], "description": "Line 1 desc", "currency_code": "USD", "exchange_rate": Decimal("1.35"), "tax_code": "SR", "tax_amount": Decimal("9.00")},
        {**sample_valid_lines[1], "description": "Line 2 desc"}
    ]
    data = {
        "journal_type": JournalTypeEnum.GENERAL.value,
        "entry_date": date(2023, 1, 15),
        "description": "JE Description",
        "reference": "JE Ref123",
        "user_id": 1,
        "lines": lines_with_optionals
    }
    try:
        entry = JournalEntryData(**data)
        assert entry.lines[0].description == "Line 1 desc"
        assert entry.lines[0].tax_code == "SR"
    except ValidationError as e:
        pytest.fail(f"Validation failed for JE with optional fields: {e}")
