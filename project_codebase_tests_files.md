# tests/integration/__init__.py
```py

```

# tests/integration/test_example_integration.py
```py

```

# tests/__init__.py
```py

```

# tests/ui/__init__.py
```py

```

# tests/ui/test_example_ui.py
```py

```

# tests/conftest.py
```py
# File: tests/conftest.py
# This file can be used for project-wide pytest fixtures.
# For now, it can remain empty or have basic configurations if needed later.

import pytest

# Example of a fixture if needed later:
# @pytest.fixture(scope="session")
# def db_url():
#     return "postgresql+asyncpg://testuser:testpass@localhost/test_db"

```

# tests/unit/__init__.py
```py
# File: tests/unit/__init__.py
# This file makes 'unit' a Python package.

```

# tests/unit/tax/test_tax_calculator.py
```py
# File: tests/unit/tax/test_tax_calculator.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from app.tax.tax_calculator import TaxCalculator
from app.services.tax_service import TaxCodeService # Interface for mocking
from app.models.accounting.tax_code import TaxCode as TaxCodeModel # ORM Model for mock return
from app.utils.pydantic_models import TaxCalculationResultData

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_tax_code_service() -> AsyncMock:
    """Fixture to create a mock TaxCodeService."""
    service = AsyncMock(spec=TaxCodeService)
    return service

@pytest.fixture
def tax_calculator(mock_tax_code_service: AsyncMock) -> TaxCalculator:
    """Fixture to create a TaxCalculator instance with a mocked service."""
    return TaxCalculator(tax_code_service=mock_tax_code_service)

async def test_calculate_line_tax_no_tax_code(tax_calculator: TaxCalculator):
    """Test tax calculation when no tax code is provided."""
    amount = Decimal("100.00")
    result = await tax_calculator.calculate_line_tax(amount, None, "SalesInvoiceLine")
    
    assert result.tax_amount == Decimal("0.00")
    assert result.taxable_amount == amount
    assert result.tax_account_id is None

async def test_calculate_line_tax_zero_amount(tax_calculator: TaxCalculator, mock_tax_code_service: AsyncMock):
    """Test tax calculation when the input amount is zero."""
    tax_code_str = "SR"
    # Mock get_tax_code even for zero amount, as it might still be called
    mock_tax_code_service.get_tax_code.return_value = TaxCodeModel(
        id=1, code="SR", description="Standard Rate", tax_type="GST", rate=Decimal("9.00"), affects_account_id=101
    )
    result = await tax_calculator.calculate_line_tax(Decimal("0.00"), tax_code_str, "SalesInvoiceLine")
    
    assert result.tax_amount == Decimal("0.00")
    assert result.taxable_amount == Decimal("0.00")
    # tax_account_id might be populated if tax_code_info is fetched, even for 0 tax.
    # The current TaxCalculator logic returns tax_code_info.affects_account_id if tax_code_info is found.
    assert result.tax_account_id == 101 

async def test_calculate_line_tax_gst_standard_rate(tax_calculator: TaxCalculator, mock_tax_code_service: AsyncMock):
    """Test GST calculation with a standard rate."""
    amount = Decimal("100.00")
    tax_code_str = "SR"
    mock_tax_code_info = TaxCodeModel(
        id=1, code="SR", description="Standard Rate", tax_type="GST", rate=Decimal("9.00"), affects_account_id=101
    )
    mock_tax_code_service.get_tax_code.return_value = mock_tax_code_info
    
    result = await tax_calculator.calculate_line_tax(amount, tax_code_str, "SalesInvoiceLine")
    
    assert result.tax_amount == Decimal("9.00") # 100.00 * 9%
    assert result.taxable_amount == amount
    assert result.tax_account_id == 101
    mock_tax_code_service.get_tax_code.assert_called_once_with(tax_code_str)

async def test_calculate_line_tax_gst_zero_rate(tax_calculator: TaxCalculator, mock_tax_code_service: AsyncMock):
    """Test GST calculation with a zero rate."""
    amount = Decimal("200.00")
    tax_code_str = "ZR"
    mock_tax_code_info = TaxCodeModel(
        id=2, code="ZR", description="Zero Rate", tax_type="GST", rate=Decimal("0.00"), affects_account_id=102
    )
    mock_tax_code_service.get_tax_code.return_value = mock_tax_code_info
    
    result = await tax_calculator.calculate_line_tax(amount, tax_code_str, "SalesInvoiceLine")
    
    assert result.tax_amount == Decimal("0.00")
    assert result.taxable_amount == amount
    assert result.tax_account_id == 102

async def test_calculate_line_tax_non_gst_type(tax_calculator: TaxCalculator, mock_tax_code_service: AsyncMock):
    """Test tax calculation when tax code is not GST (should be handled by different logic or result in zero GST)."""
    amount = Decimal("100.00")
    tax_code_str = "WHT15"
    mock_tax_code_info = TaxCodeModel(
        id=3, code="WHT15", description="Withholding Tax 15%", tax_type="Withholding Tax", rate=Decimal("15.00"), affects_account_id=103
    )
    mock_tax_code_service.get_tax_code.return_value = mock_tax_code_info
    
    # Assuming calculate_line_tax focuses on GST if called by sales/purchase context, 
    # or routes to _calculate_withholding_tax.
    # The current implementation of calculate_line_tax explicitly calls _calculate_gst or _calculate_withholding_tax.
    # Let's test the WHT path specifically for a purchase-like transaction type.
    result_wht = await tax_calculator.calculate_line_tax(amount, tax_code_str, "Purchase Payment")

    assert result_wht.tax_amount == Decimal("15.00") # 100.00 * 15%
    assert result_wht.taxable_amount == amount
    assert result_wht.tax_account_id == 103

    # Test that it returns zero GST for a Sales transaction type with a WHT code
    result_sales_with_wht_code = await tax_calculator.calculate_line_tax(amount, tax_code_str, "SalesInvoiceLine")
    assert result_sales_with_wht_code.tax_amount == Decimal("0.00") # WHT not applicable directly on sales invoice line via this mechanism
    assert result_sales_with_wht_code.taxable_amount == amount
    assert result_sales_with_wht_code.tax_account_id == 103 # affects_account_id is still returned

async def test_calculate_line_tax_unknown_tax_code(tax_calculator: TaxCalculator, mock_tax_code_service: AsyncMock):
    """Test tax calculation when the tax code is not found."""
    amount = Decimal("100.00")
    tax_code_str = "UNKNOWN"
    mock_tax_code_service.get_tax_code.return_value = None # Simulate tax code not found
    
    result = await tax_calculator.calculate_line_tax(amount, tax_code_str, "SalesInvoiceLine")
    
    assert result.tax_amount == Decimal("0.00")
    assert result.taxable_amount == amount
    assert result.tax_account_id is None

async def test_calculate_line_tax_rounding(tax_calculator: TaxCalculator, mock_tax_code_service: AsyncMock):
    """Test rounding of tax amounts."""
    amount = Decimal("99.99")
    tax_code_str = "SR"
    mock_tax_code_info = TaxCodeModel(
        id=1, code="SR", description="Standard Rate", tax_type="GST", rate=Decimal("9.00"), affects_account_id=101
    )
    mock_tax_code_service.get_tax_code.return_value = mock_tax_code_info
    
    result = await tax_calculator.calculate_line_tax(amount, tax_code_str, "SalesInvoiceLine")
    
    # 99.99 * 0.09 = 8.9991, should round to 9.00
    assert result.tax_amount == Decimal("9.00")
    assert result.taxable_amount == amount
    assert result.tax_account_id == 101

# Example for testing calculate_transaction_taxes (more complex setup)
@pytest.fixture
def sample_transaction_data_gst() -> MagicMock:
    # Using MagicMock for transaction_data because TransactionTaxData is a Pydantic model
    # and we are focusing on the TaxCalculator's interaction with it.
    # Alternatively, create actual TransactionTaxData instances.
    mock_data = MagicMock()
    mock_data.transaction_type = "SalesInvoice"
    mock_data.lines = [
        MagicMock(amount=Decimal("100.00"), tax_code="SR", account_id=1, index=0),
        MagicMock(amount=Decimal("50.00"), tax_code="ZR", account_id=2, index=1),
        MagicMock(amount=Decimal("25.00"), tax_code=None, account_id=3, index=2),
    ]
    return mock_data

async def test_calculate_transaction_taxes_gst(tax_calculator: TaxCalculator, mock_tax_code_service: AsyncMock, sample_transaction_data_gst: MagicMock):
    """Test calculation for a whole transaction with multiple lines."""
    
    # Setup mock return values for get_tax_code for each tax code used
    def get_tax_code_side_effect(code_str):
        if code_str == "SR":
            return TaxCodeModel(id=1, code="SR", description="Std", tax_type="GST", rate=Decimal("9.00"), affects_account_id=201)
        elif code_str == "ZR":
            return TaxCodeModel(id=2, code="ZR", description="Zero", tax_type="GST", rate=Decimal("0.00"), affects_account_id=202)
        return None
    mock_tax_code_service.get_tax_code.side_effect = get_tax_code_side_effect

    results = await tax_calculator.calculate_transaction_taxes(sample_transaction_data_gst)
    
    assert len(results) == 3
    
    # Line 0: SR
    assert results[0]['line_index'] == 0
    assert results[0]['tax_amount'] == Decimal("9.00") # 100 * 9%
    assert results[0]['taxable_amount'] == Decimal("100.00")
    assert results[0]['tax_account_id'] == 201
    
    # Line 1: ZR
    assert results[1]['line_index'] == 1
    assert results[1]['tax_amount'] == Decimal("0.00")
    assert results[1]['taxable_amount'] == Decimal("50.00")
    assert results[1]['tax_account_id'] == 202
    
    # Line 2: No tax code
    assert results[2]['line_index'] == 2
    assert results[2]['tax_amount'] == Decimal("0.00")
    assert results[2]['taxable_amount'] == Decimal("25.00")
    assert results[2]['tax_account_id'] is None

```

# tests/unit/tax/__init__.py
```py
# File: tests/unit/tax/__init__.py
# This file makes 'tax' (under 'unit') a Python package.

```

# tests/unit/utils/__init__.py
```py
# File: tests/unit/utils/__init__.py
# This file makes 'utils' (under 'unit') a Python package.

```

# tests/unit/utils/test_pydantic_models_journal_entry.py
```py
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

```

# tests/unit/utils/test_sequence_generator.py
```py
# File: tests/unit/utils/test_sequence_generator.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal # Not directly used, but good to have context from other tests

from app.utils.sequence_generator import SequenceGenerator
from app.services.core_services import SequenceService # For mocking interface
from app.models.core.sequence import Sequence as SequenceModel # ORM Model
from app.core.database_manager import DatabaseManager # For mocking db_manager
from app.core.application_core import ApplicationCore # For mocking app_core

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_sequence_service() -> AsyncMock:
    """Fixture to create a mock SequenceService."""
    service = AsyncMock(spec=SequenceService)
    service.get_sequence_by_name = AsyncMock()
    service.save_sequence = AsyncMock(return_value=None) # save_sequence returns the saved object, but mock can be simpler
    return service

@pytest.fixture
def mock_db_manager() -> AsyncMock:
    """Fixture to create a mock DatabaseManager."""
    db_manager = AsyncMock(spec=DatabaseManager)
    db_manager.execute_scalar = AsyncMock()
    # Mock logger on db_manager if SequenceGenerator tries to use it
    db_manager.logger = AsyncMock(spec=logging.Logger)
    db_manager.logger.warning = MagicMock()
    db_manager.logger.error = MagicMock()
    db_manager.logger.info = MagicMock()
    return db_manager

@pytest.fixture
def mock_app_core(mock_db_manager: AsyncMock, mock_sequence_service: AsyncMock) -> MagicMock:
    """Fixture to create a mock ApplicationCore providing mocked db_manager and sequence_service."""
    app_core = MagicMock(spec=ApplicationCore)
    app_core.db_manager = mock_db_manager
    app_core.sequence_service = mock_sequence_service # Though SequenceGenerator takes service directly
    app_core.logger = MagicMock(spec=logging.Logger) # Mock logger on app_core too
    return app_core

@pytest.fixture
def sequence_generator(mock_sequence_service: AsyncMock, mock_app_core: MagicMock) -> SequenceGenerator:
    """Fixture to create a SequenceGenerator instance."""
    # SequenceGenerator constructor: sequence_service, app_core_ref
    return SequenceGenerator(sequence_service=mock_sequence_service, app_core_ref=mock_app_core)

# --- Test Cases ---

async def test_next_sequence_db_function_success(
    sequence_generator: SequenceGenerator, 
    mock_app_core: MagicMock
):
    """Test successful sequence generation using the database function."""
    sequence_name = "SALES_INVOICE"
    expected_formatted_value = "INV-000123"
    mock_app_core.db_manager.execute_scalar.return_value = expected_formatted_value

    result = await sequence_generator.next_sequence(sequence_name)
    
    assert result == expected_formatted_value
    mock_app_core.db_manager.execute_scalar.assert_awaited_once_with(
        f"SELECT core.get_next_sequence_value('{sequence_name}');"
    )

async def test_next_sequence_db_function_returns_none_fallback(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock,
    mock_sequence_service: AsyncMock
):
    """Test Python fallback when DB function returns None."""
    sequence_name = "PURCHASE_ORDER"
    mock_app_core.db_manager.execute_scalar.return_value = None # Simulate DB function failure

    # Setup for Python fallback
    mock_sequence_orm = SequenceModel(
        id=1, sequence_name=sequence_name, prefix="PO", next_value=10, 
        increment_by=1, min_value=1, max_value=9999, cycle=False,
        format_template="{PREFIX}-{VALUE:04d}" # Ensure 'd' for integer formatting
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj # Return the object passed to it

    result = await sequence_generator.next_sequence(sequence_name)

    assert result == "PO-0010"
    mock_app_core.db_manager.execute_scalar.assert_awaited_once()
    mock_sequence_service.get_sequence_by_name.assert_awaited_once_with(sequence_name)
    mock_sequence_service.save_sequence.assert_awaited_once()
    assert mock_sequence_orm.next_value == 11 # Check increment

async def test_next_sequence_db_function_exception_fallback(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock,
    mock_sequence_service: AsyncMock
):
    """Test Python fallback when DB function raises an exception."""
    sequence_name = "JOURNAL_ENTRY"
    mock_app_core.db_manager.execute_scalar.side_effect = Exception("DB connection error")

    mock_sequence_orm = SequenceModel(
        id=2, sequence_name=sequence_name, prefix="JE", next_value=1, 
        increment_by=1, format_template="{PREFIX}{VALUE:06d}"
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj

    result = await sequence_generator.next_sequence(sequence_name)

    assert result == "JE000001"
    mock_app_core.db_manager.execute_scalar.assert_awaited_once()
    mock_sequence_service.get_sequence_by_name.assert_awaited_once_with(sequence_name)

async def test_next_sequence_python_fallback_new_sequence(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock, # For db_manager to be present on app_core
    mock_sequence_service: AsyncMock
):
    """Test Python fallback creates a new sequence if not found in DB."""
    sequence_name = "NEW_SEQ"
    # Simulate DB function failure (e.g., returns None or raises error, leading to fallback)
    mock_app_core.db_manager.execute_scalar.return_value = None 
    mock_sequence_service.get_sequence_by_name.return_value = None # Sequence not found

    # The save_sequence mock should capture the argument passed to it
    # so we can assert its properties.
    saved_sequence_holder = {}
    async def capture_save(seq_obj):
        saved_sequence_holder['seq'] = seq_obj
        return seq_obj
    mock_sequence_service.save_sequence.side_effect = capture_save
    
    result = await sequence_generator.next_sequence(sequence_name)

    assert result == "NEW-000001" # Based on default prefix logic and format_template
    
    # Check that get_sequence_by_name was called
    mock_sequence_service.get_sequence_by_name.assert_awaited_once_with(sequence_name)
    
    # Check that save_sequence was called (once for creation, once for update)
    assert mock_sequence_service.save_sequence.await_count == 2
    
    # Check the details of the created sequence object
    created_seq = saved_sequence_holder['seq']
    assert created_seq.sequence_name == sequence_name
    assert created_seq.prefix == "NEW" # Default prefix logic: sequence_name.upper()[:3]
    assert created_seq.next_value == 2 # Initial value was 1, used, then incremented
    assert created_seq.format_template == "{PREFIX}-{VALUE:06d}"


async def test_next_sequence_python_fallback_prefix_override(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock,
    mock_sequence_service: AsyncMock
):
    """Test Python fallback with prefix_override."""
    sequence_name = "ITEM_CODE"
    # DB function is skipped when prefix_override is used, so mock it to ensure it's not called.
    mock_app_core.db_manager.execute_scalar.side_effect = AssertionError("DB function should not be called with prefix_override")

    mock_sequence_orm = SequenceModel(
        id=3, sequence_name=sequence_name, prefix="ITM", next_value=5, 
        increment_by=1, format_template="{PREFIX}-{VALUE:03d}"
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj
    
    result = await sequence_generator.next_sequence(sequence_name, prefix_override="OVERRIDE")

    assert result == "OVERRIDE-005"
    mock_app_core.db_manager.execute_scalar.assert_not_awaited() # Verify DB func not called
    mock_sequence_service.get_sequence_by_name.assert_awaited_once_with(sequence_name)
    assert mock_sequence_orm.next_value == 6

async def test_next_sequence_python_fallback_cycle(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock,
    mock_sequence_service: AsyncMock
):
    """Test Python fallback sequence cycling."""
    sequence_name = "CYCLE_SEQ"
    mock_app_core.db_manager.execute_scalar.return_value = None # Force Python fallback

    mock_sequence_orm = SequenceModel(
        id=4, sequence_name=sequence_name, prefix="CY", next_value=3, 
        increment_by=1, min_value=1, max_value=3, cycle=True,
        format_template="{PREFIX}{VALUE}"
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj

    result1 = await sequence_generator.next_sequence(sequence_name) # Uses 3, next_value becomes 1 (cycles)
    assert result1 == "CY3"
    assert mock_sequence_orm.next_value == 1 # Cycled

    result2 = await sequence_generator.next_sequence(sequence_name) # Uses 1, next_value becomes 2
    assert result2 == "CY1"
    assert mock_sequence_orm.next_value == 2

async def test_next_sequence_python_fallback_max_value_no_cycle(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock,
    mock_sequence_service: AsyncMock
):
    """Test Python fallback hitting max value without cycling."""
    sequence_name = "MAX_SEQ"
    mock_app_core.db_manager.execute_scalar.return_value = None

    mock_sequence_orm = SequenceModel(
        id=5, sequence_name=sequence_name, prefix="MX", next_value=3, 
        increment_by=1, min_value=1, max_value=3, cycle=False, # cycle=False
        format_template="{PREFIX}{VALUE}"
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj

    result = await sequence_generator.next_sequence(sequence_name) # Uses 3, next_value becomes 4
    assert result == "MX3"
    assert mock_sequence_orm.next_value == 4 

    # Next call should raise ValueError
    with pytest.raises(ValueError) as excinfo:
        await sequence_generator.next_sequence(sequence_name)
    assert f"Sequence '{sequence_name}' has reached its maximum value (3) and cannot cycle." in str(excinfo.value)

async def test_next_sequence_format_template_zfill_variant(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock,
    mock_sequence_service: AsyncMock
):
    """Test a format_template with {VALUE:06} (no 'd')."""
    sequence_name = "ZFILL_TEST"
    mock_app_core.db_manager.execute_scalar.return_value = None

    mock_sequence_orm = SequenceModel(
        id=6, sequence_name=sequence_name, prefix="ZF", next_value=7,
        increment_by=1, format_template="{PREFIX}{VALUE:06}" # Note: no 'd'
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj

    result = await sequence_generator.next_sequence(sequence_name)
    assert result == "ZF000007"

```

# tests/unit/services/test_currency_service.py
```py
# File: tests/unit/services/test_currency_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
import datetime

from app.services.accounting_services import CurrencyService
from app.models.accounting.currency import Currency as CurrencyModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore # For mocking app_core
from app.models.core.user import User as UserModel # For mocking current_user

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    """Fixture to create a mock AsyncSession."""
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_db_manager(mock_session: AsyncMock) -> MagicMock:
    """Fixture to create a mock DatabaseManager that returns the mock_session."""
    db_manager = MagicMock(spec=DatabaseManager)
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def mock_user() -> MagicMock:
    user = MagicMock(spec=UserModel)
    user.id = 123 # Example user ID
    return user

@pytest.fixture
def mock_app_core(mock_user: MagicMock) -> MagicMock:
    """Fixture to create a mock ApplicationCore with a current_user."""
    app_core = MagicMock(spec=ApplicationCore)
    app_core.current_user = mock_user
    return app_core

@pytest.fixture
def currency_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> CurrencyService:
    """Fixture to create a CurrencyService instance with mocked dependencies."""
    return CurrencyService(db_manager=mock_db_manager, app_core=mock_app_core)

# --- Test Cases ---

async def test_get_currency_by_id_found(currency_service: CurrencyService, mock_session: AsyncMock):
    """Test get_by_id when Currency is found."""
    expected_currency = CurrencyModel(code="SGD", name="Singapore Dollar", symbol="$")
    mock_session.get.return_value = expected_currency

    result = await currency_service.get_by_id("SGD")
    
    assert result == expected_currency
    mock_session.get.assert_awaited_once_with(CurrencyModel, "SGD")

async def test_get_currency_by_id_not_found(currency_service: CurrencyService, mock_session: AsyncMock):
    """Test get_by_id when Currency is not found."""
    mock_session.get.return_value = None

    result = await currency_service.get_by_id("XXX")
    
    assert result is None
    mock_session.get.assert_awaited_once_with(CurrencyModel, "XXX")

async def test_get_all_currencies(currency_service: CurrencyService, mock_session: AsyncMock):
    """Test get_all returns a list of Currencies ordered by name."""
    curr1 = CurrencyModel(code="AUD", name="Australian Dollar", symbol="$")
    curr2 = CurrencyModel(code="SGD", name="Singapore Dollar", symbol="$")
    mock_execute_result = AsyncMock()
    # Service orders by name, so mock should reflect that for this test's assertion simplicity
    mock_execute_result.scalars.return_value.all.return_value = [curr1, curr2] 
    mock_session.execute.return_value = mock_execute_result

    result = await currency_service.get_all()

    assert len(result) == 2
    assert result[0].code == "AUD"
    assert result[1].code == "SGD"
    mock_session.execute.assert_awaited_once()
    # Could assert statement for order_by(Currency.name)

async def test_get_all_active_currencies(currency_service: CurrencyService, mock_session: AsyncMock):
    """Test get_all_active returns only active currencies."""
    curr1_active = CurrencyModel(code="SGD", name="Singapore Dollar", symbol="$", is_active=True)
    curr2_inactive = CurrencyModel(code="OLD", name="Old Currency", symbol="O", is_active=False) # Not expected
    curr3_active = CurrencyModel(code="USD", name="US Dollar", symbol="$", is_active=True)
    
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.all.return_value = [curr1_active, curr3_active]
    mock_session.execute.return_value = mock_execute_result

    result = await currency_service.get_all_active()

    assert len(result) == 2
    assert all(c.is_active for c in result)
    assert result[0].code == "SGD" # Assuming mock returns them ordered by name already
    assert result[1].code == "USD"
    mock_session.execute.assert_awaited_once()
    # Assert that the query contained "is_active == True"

async def test_add_currency(currency_service: CurrencyService, mock_session: AsyncMock, mock_user: MagicMock):
    """Test adding a new Currency, checking audit user IDs."""
    new_currency_data = CurrencyModel(code="XYZ", name="New Currency", symbol="X")
    
    async def mock_refresh(obj, attribute_names=None):
        obj.id = "XYZ" # Simulate ID being set (though for Currency, code is ID)
        obj.created_at = datetime.datetime.now()
        obj.updated_at = datetime.datetime.now()
        # The service itself sets user_ids before add, so check them on new_currency_data
    mock_session.refresh.side_effect = mock_refresh

    result = await currency_service.add(new_currency_data)

    assert new_currency_data.created_by_user_id == mock_user.id
    assert new_currency_data.updated_by_user_id == mock_user.id
    mock_session.add.assert_called_once_with(new_currency_data)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(new_currency_data)
    assert result == new_currency_data

async def test_update_currency(currency_service: CurrencyService, mock_session: AsyncMock, mock_user: MagicMock):
    """Test updating an existing Currency, checking updated_by_user_id."""
    existing_currency = CurrencyModel(id="SGD", code="SGD", name="Singapore Dollar", symbol="$", created_by_user_id=99)
    existing_currency.name = "Singapore Dollar (Updated)" # Simulate change
    
    async def mock_refresh(obj, attribute_names=None):
        obj.updated_at = datetime.datetime.now()
    mock_session.refresh.side_effect = mock_refresh

    result = await currency_service.update(existing_currency)

    assert result.updated_by_user_id == mock_user.id
    assert result.name == "Singapore Dollar (Updated)"
    mock_session.add.assert_called_once_with(existing_currency)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(existing_currency)

async def test_delete_currency_found(currency_service: CurrencyService, mock_session: AsyncMock):
    """Test deleting an existing Currency."""
    currency_to_delete = CurrencyModel(code="DEL", name="Delete Me", symbol="D")
    mock_session.get.return_value = currency_to_delete

    result = await currency_service.delete("DEL")

    assert result is True
    mock_session.get.assert_awaited_once_with(CurrencyModel, "DEL")
    mock_session.delete.assert_awaited_once_with(currency_to_delete)

async def test_delete_currency_not_found(currency_service: CurrencyService, mock_session: AsyncMock):
    """Test deleting a non-existent Currency."""
    mock_session.get.return_value = None

    result = await currency_service.delete("NON")

    assert result is False
    mock_session.get.assert_awaited_once_with(CurrencyModel, "NON")
    mock_session.delete.assert_not_called()

```

# tests/unit/services/test_company_settings_service.py
```py
# File: tests/unit/services/test_company_settings_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Optional
import datetime

from app.services.core_services import CompanySettingsService
from app.models.core.company_setting import CompanySetting as CompanySettingModel
from app.models.core.user import User as UserModel # For mocking app_core.current_user
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    """Fixture to create a mock AsyncSession."""
    session = AsyncMock()
    session.get = AsyncMock()
    session.add = MagicMock() # Use MagicMock for non-awaitable methods
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_db_manager(mock_session: AsyncMock) -> MagicMock:
    """Fixture to create a mock DatabaseManager that returns the mock_session."""
    db_manager = MagicMock(spec=DatabaseManager)
    # Configure the async context manager mock
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def mock_current_user() -> MagicMock:
    """Fixture to create a mock User object for app_core.current_user."""
    user = MagicMock(spec=UserModel)
    user.id = 99 # Example ID for the current user performing the action
    return user

@pytest.fixture
def mock_app_core(mock_current_user: MagicMock) -> MagicMock:
    """Fixture to create a mock ApplicationCore with a current_user."""
    app_core = MagicMock(spec=ApplicationCore)
    app_core.current_user = mock_current_user
    app_core.logger = MagicMock() # Add logger if service uses it
    return app_core

@pytest.fixture
def company_settings_service(
    mock_db_manager: MagicMock, 
    mock_app_core: MagicMock
) -> CompanySettingsService:
    """Fixture to create a CompanySettingsService instance with mocked dependencies."""
    return CompanySettingsService(db_manager=mock_db_manager, app_core=mock_app_core)

# Sample Data
@pytest.fixture
def sample_company_settings() -> CompanySettingModel:
    """Provides a sample CompanySetting ORM object."""
    return CompanySettingModel(
        id=1,
        company_name="Test Corp Ltd",
        legal_name="Test Corporation Private Limited",
        base_currency="SGD",
        fiscal_year_start_month=1,
        fiscal_year_start_day=1,
        updated_by_user_id=1 # Assume an initial updated_by user
    )

# --- Test Cases ---

async def test_get_company_settings_found(
    company_settings_service: CompanySettingsService, 
    mock_session: AsyncMock, 
    sample_company_settings: CompanySettingModel
):
    """Test get_company_settings when settings are found (typically ID 1)."""
    mock_session.get.return_value = sample_company_settings

    result = await company_settings_service.get_company_settings(settings_id=1)
    
    assert result is not None
    assert result.id == 1
    assert result.company_name == "Test Corp Ltd"
    mock_session.get.assert_awaited_once_with(CompanySettingModel, 1)

async def test_get_company_settings_not_found(
    company_settings_service: CompanySettingsService, 
    mock_session: AsyncMock
):
    """Test get_company_settings when settings for the given ID are not found."""
    mock_session.get.return_value = None

    result = await company_settings_service.get_company_settings(settings_id=99) # Non-existent ID
    
    assert result is None
    mock_session.get.assert_awaited_once_with(CompanySettingModel, 99)

async def test_save_company_settings_updates_audit_fields_and_saves(
    company_settings_service: CompanySettingsService, 
    mock_session: AsyncMock,
    sample_company_settings: CompanySettingModel, # Use the fixture for a base object
    mock_current_user: MagicMock # To verify the updated_by_user_id
):
    """Test that save_company_settings correctly sets updated_by_user_id and calls session methods."""
    settings_to_save = sample_company_settings
    # Simulate a change to the object
    settings_to_save.company_name = "Updated Test Corp Inc." 
    
    # The service method will modify settings_to_save in place regarding updated_by_user_id
    
    # Mock the refresh to simulate ORM behavior (e.g., updating timestamps if applicable)
    async def mock_refresh(obj, attribute_names=None):
        obj.updated_at = datetime.datetime.now(datetime.timezone.utc) # Simulate DB update
        return obj # Refresh typically doesn't return but modifies in place
    mock_session.refresh.side_effect = mock_refresh

    result = await company_settings_service.save_company_settings(settings_to_save)

    # Assert that the updated_by_user_id was set by the service method
    assert result.updated_by_user_id == mock_current_user.id
    assert result.company_name == "Updated Test Corp Inc."
    
    mock_session.add.assert_called_once_with(settings_to_save)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(settings_to_save)
    assert result == settings_to_save # Should return the same, potentially modified object

async def test_save_company_settings_when_app_core_or_user_is_none(
    mock_db_manager: MagicMock, # Use db_manager directly to create service
    mock_session: AsyncMock,
    sample_company_settings: CompanySettingModel
):
    """Test save_company_settings when app_core or current_user is None."""
    # Scenario 1: app_core is None
    service_no_app_core = CompanySettingsService(db_manager=mock_db_manager, app_core=None)
    settings_to_save_1 = CompanySettingModel(id=2, company_name="No AppCore Co", base_currency="USD")
    
    # Store original updated_by_user_id if it exists, or None
    original_updated_by_1 = settings_to_save_1.updated_by_user_id

    await service_no_app_core.save_company_settings(settings_to_save_1)
    assert settings_to_save_1.updated_by_user_id == original_updated_by_1 # Should not change
    
    # Scenario 2: app_core exists, but current_user is None
    app_core_no_user = MagicMock(spec=ApplicationCore)
    app_core_no_user.current_user = None
    app_core_no_user.logger = MagicMock()
    service_no_current_user = CompanySettingsService(db_manager=mock_db_manager, app_core=app_core_no_user)
    settings_to_save_2 = CompanySettingModel(id=3, company_name="No CurrentUser Co", base_currency="EUR")
    original_updated_by_2 = settings_to_save_2.updated_by_user_id

    await service_no_current_user.save_company_settings(settings_to_save_2)
    assert settings_to_save_2.updated_by_user_id == original_updated_by_2 # Should not change

```

# tests/unit/services/__init__.py
```py
# File: tests/unit/services/__init__.py
# This file makes 'services' (under 'unit') a Python package.

```

# tests/unit/services/test_exchange_rate_service.py
```py
# File: tests/unit/services/test_exchange_rate_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime

from app.services.accounting_services import ExchangeRateService
from app.models.accounting.exchange_rate import ExchangeRate as ExchangeRateModel
from app.models.accounting.currency import Currency as CurrencyModel # For creating related objects if needed
from app.models.core.user import User as UserModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_db_manager(mock_session: AsyncMock) -> MagicMock:
    db_manager = MagicMock(spec=DatabaseManager)
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def mock_user() -> MagicMock:
    user = MagicMock(spec=UserModel)
    user.id = 789 # Example admin/system user ID for auditing
    return user

@pytest.fixture
def mock_app_core(mock_user: MagicMock) -> MagicMock:
    app_core = MagicMock(spec=ApplicationCore)
    app_core.current_user = mock_user
    return app_core

@pytest.fixture
def exchange_rate_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> ExchangeRateService:
    return ExchangeRateService(db_manager=mock_db_manager, app_core=mock_app_core)

# Sample data
@pytest.fixture
def sample_exchange_rate_1() -> ExchangeRateModel:
    return ExchangeRateModel(
        id=1, from_currency_code="USD", to_currency_code="SGD", 
        rate_date=date(2023, 1, 1), exchange_rate_value=Decimal("1.350000")
    )

@pytest.fixture
def sample_exchange_rate_2() -> ExchangeRateModel:
    return ExchangeRateModel(
        id=2, from_currency_code="EUR", to_currency_code="SGD", 
        rate_date=date(2023, 1, 1), exchange_rate_value=Decimal("1.480000")
    )

# --- Test Cases ---

async def test_get_exchange_rate_by_id_found(
    exchange_rate_service: ExchangeRateService, 
    mock_session: AsyncMock, 
    sample_exchange_rate_1: ExchangeRateModel
):
    mock_session.get.return_value = sample_exchange_rate_1
    result = await exchange_rate_service.get_by_id(1)
    assert result == sample_exchange_rate_1
    mock_session.get.assert_awaited_once_with(ExchangeRateModel, 1)

async def test_get_exchange_rate_by_id_not_found(exchange_rate_service: ExchangeRateService, mock_session: AsyncMock):
    mock_session.get.return_value = None
    result = await exchange_rate_service.get_by_id(99)
    assert result is None

async def test_get_all_exchange_rates(
    exchange_rate_service: ExchangeRateService, 
    mock_session: AsyncMock, 
    sample_exchange_rate_1: ExchangeRateModel, 
    sample_exchange_rate_2: ExchangeRateModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.all.return_value = [sample_exchange_rate_1, sample_exchange_rate_2]
    mock_session.execute.return_value = mock_execute_result

    result = await exchange_rate_service.get_all()
    assert len(result) == 2
    assert result[0] == sample_exchange_rate_1

async def test_save_new_exchange_rate(
    exchange_rate_service: ExchangeRateService, 
    mock_session: AsyncMock, 
    mock_user: MagicMock
):
    new_rate_data = ExchangeRateModel(
        from_currency_code="JPY", to_currency_code="SGD", 
        rate_date=date(2023, 1, 2), exchange_rate_value=Decimal("0.010000")
        # ID will be None initially
    )
    # Simulate id and audit fields being set after add/flush/refresh
    async def mock_refresh(obj, attribute_names=None):
        obj.id = 3 # Simulate ID generation
        obj.created_at = datetime.now()
        obj.updated_at = datetime.now()
        # Service sets created_by and updated_by before calling session.add
    mock_session.refresh.side_effect = mock_refresh
    
    result = await exchange_rate_service.save(new_rate_data)

    assert result.id == 3
    assert result.created_by_user_id == mock_user.id
    assert result.updated_by_user_id == mock_user.id
    mock_session.add.assert_called_once_with(new_rate_data)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(new_rate_data)

async def test_save_update_exchange_rate(
    exchange_rate_service: ExchangeRateService, 
    mock_session: AsyncMock, 
    sample_exchange_rate_1: ExchangeRateModel, 
    mock_user: MagicMock
):
    sample_exchange_rate_1.exchange_rate_value = Decimal("1.360000") # Modify
    original_created_by = sample_exchange_rate_1.created_by_user_id # Should remain unchanged

    async def mock_refresh(obj, attribute_names=None):
        obj.updated_at = datetime.now()
    mock_session.refresh.side_effect = mock_refresh

    result = await exchange_rate_service.save(sample_exchange_rate_1)
    
    assert result.exchange_rate_value == Decimal("1.360000")
    assert result.updated_by_user_id == mock_user.id
    if original_created_by: # If it was set
        assert result.created_by_user_id == original_created_by
    
    mock_session.add.assert_called_once_with(sample_exchange_rate_1)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(sample_exchange_rate_1)

async def test_delete_exchange_rate_found(
    exchange_rate_service: ExchangeRateService, 
    mock_session: AsyncMock, 
    sample_exchange_rate_1: ExchangeRateModel
):
    mock_session.get.return_value = sample_exchange_rate_1
    deleted = await exchange_rate_service.delete(1)
    assert deleted is True
    mock_session.get.assert_awaited_once_with(ExchangeRateModel, 1)
    mock_session.delete.assert_awaited_once_with(sample_exchange_rate_1)

async def test_delete_exchange_rate_not_found(exchange_rate_service: ExchangeRateService, mock_session: AsyncMock):
    mock_session.get.return_value = None
    deleted = await exchange_rate_service.delete(99)
    assert deleted is False
    mock_session.get.assert_awaited_once_with(ExchangeRateModel, 99)
    mock_session.delete.assert_not_called()

async def test_get_rate_for_date_found(
    exchange_rate_service: ExchangeRateService, 
    mock_session: AsyncMock, 
    sample_exchange_rate_1: ExchangeRateModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = sample_exchange_rate_1
    mock_session.execute.return_value = mock_execute_result
    
    result = await exchange_rate_service.get_rate_for_date("USD", "SGD", date(2023, 1, 1))
    
    assert result == sample_exchange_rate_1
    mock_session.execute.assert_awaited_once()
    # More detailed assertion could check the statement construction if needed

async def test_get_rate_for_date_not_found(exchange_rate_service: ExchangeRateService, mock_session: AsyncMock):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_execute_result
    
    result = await exchange_rate_service.get_rate_for_date("USD", "EUR", date(2023, 1, 1))
    
    assert result is None

```

# tests/unit/services/test_fiscal_period_service.py
```py
# File: tests/unit/services/test_fiscal_period_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal # For context with other financial models

from app.services.fiscal_period_service import FiscalPeriodService
from app.models.accounting.fiscal_period import FiscalPeriod as FiscalPeriodModel
from app.models.accounting.fiscal_year import FiscalYear as FiscalYearModel
from app.core.database_manager import DatabaseManager

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_db_manager(mock_session: AsyncMock) -> MagicMock:
    db_manager = MagicMock(spec=DatabaseManager)
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def fiscal_period_service(mock_db_manager: MagicMock) -> FiscalPeriodService:
    # FiscalPeriodService only takes db_manager
    return FiscalPeriodService(db_manager=mock_db_manager)

# Sample Data
@pytest.fixture
def sample_fy_2023() -> FiscalYearModel:
    return FiscalYearModel(id=1, year_name="FY2023", start_date=date(2023,1,1), end_date=date(2023,12,31), created_by_user_id=1, updated_by_user_id=1)

@pytest.fixture
def sample_period_jan_2023(sample_fy_2023: FiscalYearModel) -> FiscalPeriodModel:
    return FiscalPeriodModel(id=1, fiscal_year_id=sample_fy_2023.id, name="Jan 2023", 
                             start_date=date(2023,1,1), end_date=date(2023,1,31),
                             period_type="Month", status="Open", period_number=1,
                             created_by_user_id=1, updated_by_user_id=1)

@pytest.fixture
def sample_period_q1_2023(sample_fy_2023: FiscalYearModel) -> FiscalPeriodModel:
    return FiscalPeriodModel(id=2, fiscal_year_id=sample_fy_2023.id, name="Q1 2023",
                             start_date=date(2023,1,1), end_date=date(2023,3,31),
                             period_type="Quarter", status="Closed", period_number=1,
                             created_by_user_id=1, updated_by_user_id=1)

# --- Test Cases ---

async def test_get_fiscal_period_by_id_found(
    fiscal_period_service: FiscalPeriodService, 
    mock_session: AsyncMock, 
    sample_period_jan_2023: FiscalPeriodModel
):
    mock_session.get.return_value = sample_period_jan_2023
    result = await fiscal_period_service.get_by_id(1)
    assert result == sample_period_jan_2023
    mock_session.get.assert_awaited_once_with(FiscalPeriodModel, 1)

async def test_get_fiscal_period_by_id_not_found(fiscal_period_service: FiscalPeriodService, mock_session: AsyncMock):
    mock_session.get.return_value = None
    result = await fiscal_period_service.get_by_id(99)
    assert result is None

async def test_get_all_fiscal_periods(
    fiscal_period_service: FiscalPeriodService, 
    mock_session: AsyncMock, 
    sample_period_jan_2023: FiscalPeriodModel, 
    sample_period_q1_2023: FiscalPeriodModel
):
    mock_execute_result = AsyncMock()
    # Service orders by start_date
    mock_execute_result.scalars.return_value.all.return_value = [sample_period_jan_2023, sample_period_q1_2023]
    mock_session.execute.return_value = mock_execute_result
    result = await fiscal_period_service.get_all()
    assert len(result) == 2
    assert result[0] == sample_period_jan_2023

async def test_add_fiscal_period(fiscal_period_service: FiscalPeriodService, mock_session: AsyncMock):
    new_period_data = FiscalPeriodModel(
        fiscal_year_id=1, name="Feb 2023", start_date=date(2023,2,1), end_date=date(2023,2,28),
        period_type="Month", status="Open", period_number=2,
        created_by_user_id=1, updated_by_user_id=1 # Assume these are set by manager
    )
    async def mock_refresh(obj, attribute_names=None): obj.id = 100 # Simulate ID generation
    mock_session.refresh.side_effect = mock_refresh
    
    result = await fiscal_period_service.add(new_period_data)
    mock_session.add.assert_called_once_with(new_period_data)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(new_period_data)
    assert result == new_period_data
    assert result.id == 100

async def test_delete_fiscal_period_open(
    fiscal_period_service: FiscalPeriodService, 
    mock_session: AsyncMock, 
    sample_period_jan_2023: FiscalPeriodModel
):
    sample_period_jan_2023.status = "Open" # Ensure it's open
    mock_session.get.return_value = sample_period_jan_2023
    deleted = await fiscal_period_service.delete(1)
    assert deleted is True
    mock_session.delete.assert_awaited_once_with(sample_period_jan_2023)

async def test_delete_fiscal_period_archived_fails(
    fiscal_period_service: FiscalPeriodService, 
    mock_session: AsyncMock, 
    sample_period_jan_2023: FiscalPeriodModel
):
    sample_period_jan_2023.status = "Archived"
    mock_session.get.return_value = sample_period_jan_2023
    deleted = await fiscal_period_service.delete(1)
    assert deleted is False # Cannot delete archived period
    mock_session.delete.assert_not_called()

async def test_get_fiscal_period_by_date_found(
    fiscal_period_service: FiscalPeriodService, 
    mock_session: AsyncMock, 
    sample_period_jan_2023: FiscalPeriodModel
):
    sample_period_jan_2023.status = "Open"
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = sample_period_jan_2023
    mock_session.execute.return_value = mock_execute_result
    
    result = await fiscal_period_service.get_by_date(date(2023, 1, 15))
    assert result == sample_period_jan_2023

async def test_get_fiscal_period_by_date_not_found_or_not_open(
    fiscal_period_service: FiscalPeriodService, mock_session: AsyncMock
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_execute_result
    
    result = await fiscal_period_service.get_by_date(date(2024, 1, 15))
    assert result is None

async def test_get_fiscal_year_by_year_value(
    fiscal_period_service: FiscalPeriodService, # Testing method within FiscalPeriodService
    mock_session: AsyncMock, 
    sample_fy_2023: FiscalYearModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = sample_fy_2023
    mock_session.execute.return_value = mock_execute_result
    
    result = await fiscal_period_service.get_fiscal_year(2023)
    assert result == sample_fy_2023
    # Could assert that the SQL query used 'LIKE %2023%'

async def test_get_fiscal_periods_for_year(
    fiscal_period_service: FiscalPeriodService, 
    mock_session: AsyncMock,
    sample_period_jan_2023: FiscalPeriodModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.all.return_value = [sample_period_jan_2023]
    mock_session.execute.return_value = mock_execute_result

    result = await fiscal_period_service.get_fiscal_periods_for_year(1, period_type="Month")
    assert len(result) == 1
    assert result[0] == sample_period_jan_2023

```

# tests/unit/services/test_configuration_service.py
```py
# File: tests/unit/services/test_configuration_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Optional

from app.services.core_services import ConfigurationService
from app.models.core.configuration import Configuration as ConfigurationModel
from app.core.database_manager import DatabaseManager

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    """Fixture to create a mock AsyncSession."""
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_db_manager(mock_session: AsyncMock) -> MagicMock:
    """Fixture to create a mock DatabaseManager that returns the mock_session."""
    db_manager = MagicMock(spec=DatabaseManager)
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def config_service(mock_db_manager: MagicMock) -> ConfigurationService:
    """Fixture to create a ConfigurationService instance with a mocked db_manager."""
    return ConfigurationService(db_manager=mock_db_manager)

# Sample data
@pytest.fixture
def sample_config_entry_1() -> ConfigurationModel:
    return ConfigurationModel(
        id=1, config_key="TestKey1", config_value="TestValue1", description="Desc1"
    )

@pytest.fixture
def sample_config_entry_none_value() -> ConfigurationModel:
    return ConfigurationModel(
        id=2, config_key="TestKeyNone", config_value=None, description="DescNone"
    )

# --- Test Cases ---

async def test_get_config_by_key_found(
    config_service: ConfigurationService, 
    mock_session: AsyncMock, 
    sample_config_entry_1: ConfigurationModel
):
    """Test get_config_by_key when the configuration entry is found."""
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = sample_config_entry_1
    mock_session.execute.return_value = mock_execute_result

    result = await config_service.get_config_by_key("TestKey1")
    
    assert result == sample_config_entry_1
    mock_session.execute.assert_awaited_once() # Could add statement assertion if complex

async def test_get_config_by_key_not_found(config_service: ConfigurationService, mock_session: AsyncMock):
    """Test get_config_by_key when the configuration entry is not found."""
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_execute_result

    result = await config_service.get_config_by_key("NonExistentKey")
    
    assert result is None

async def test_get_config_value_found_with_value(
    config_service: ConfigurationService, 
    mock_session: AsyncMock, 
    sample_config_entry_1: ConfigurationModel
):
    """Test get_config_value when key is found and has a value."""
    mock_execute_result = AsyncMock() # Re-mock for this specific call path if get_config_by_key is called internally
    mock_execute_result.scalars.return_value.first.return_value = sample_config_entry_1
    mock_session.execute.return_value = mock_execute_result
    
    # Patch get_config_by_key if it's called internally by get_config_value
    with patch.object(config_service, 'get_config_by_key', AsyncMock(return_value=sample_config_entry_1)) as mock_get_by_key:
        result = await config_service.get_config_value("TestKey1", "Default")
        assert result == "TestValue1"
        mock_get_by_key.assert_awaited_once_with("TestKey1")


async def test_get_config_value_found_with_none_value(
    config_service: ConfigurationService, 
    mock_session: AsyncMock, 
    sample_config_entry_none_value: ConfigurationModel
):
    """Test get_config_value when key is found but its value is None."""
    with patch.object(config_service, 'get_config_by_key', AsyncMock(return_value=sample_config_entry_none_value)) as mock_get_by_key:
        result = await config_service.get_config_value("TestKeyNone", "DefaultValue")
        assert result == "DefaultValue" # Should return default
        mock_get_by_key.assert_awaited_once_with("TestKeyNone")

async def test_get_config_value_not_found(config_service: ConfigurationService, mock_session: AsyncMock):
    """Test get_config_value when key is not found."""
    with patch.object(config_service, 'get_config_by_key', AsyncMock(return_value=None)) as mock_get_by_key:
        result = await config_service.get_config_value("NonExistentKey", "DefaultValue")
        assert result == "DefaultValue"
        mock_get_by_key.assert_awaited_once_with("NonExistentKey")

async def test_get_config_value_not_found_no_default(config_service: ConfigurationService, mock_session: AsyncMock):
    """Test get_config_value when key is not found and no default is provided."""
    with patch.object(config_service, 'get_config_by_key', AsyncMock(return_value=None)) as mock_get_by_key:
        result = await config_service.get_config_value("NonExistentKey") # Default is None
        assert result is None
        mock_get_by_key.assert_awaited_once_with("NonExistentKey")

async def test_save_config(config_service: ConfigurationService, mock_session: AsyncMock):
    """Test saving a Configuration entry."""
    config_to_save = ConfigurationModel(config_key="NewKey", config_value="NewValue")
    
    async def mock_refresh(obj, attribute_names=None):
        obj.id = 10 # Simulate ID generation if it's an autoincrement PK
        obj.created_at = datetime.now()
        obj.updated_at = datetime.now()
        # Configuration model has updated_by, but service doesn't set it from app_core.
        # For this unit test, we assume it's either set on the object before calling save,
        # or handled by DB triggers/defaults if applicable.
    mock_session.refresh.side_effect = mock_refresh

    result = await config_service.save_config(config_to_save)

    mock_session.add.assert_called_once_with(config_to_save)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(config_to_save)
    assert result == config_to_save
    assert result.id == 10 # Check if refresh side_effect worked

```

# tests/unit/services/test_account_type_service.py
```py
# File: tests/unit/services/test_account_type_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from decimal import Decimal # Though not directly used by AccountType, good for context

from app.services.accounting_services import AccountTypeService
from app.models.accounting.account_type import AccountType as AccountTypeModel
from app.core.database_manager import DatabaseManager

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    """Fixture to create a mock AsyncSession."""
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_db_manager(mock_session: AsyncMock) -> MagicMock:
    """Fixture to create a mock DatabaseManager that returns the mock_session."""
    db_manager = MagicMock(spec=DatabaseManager)
    # Make the async context manager work
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def account_type_service(mock_db_manager: MagicMock) -> AccountTypeService:
    """Fixture to create an AccountTypeService instance with a mocked db_manager."""
    # AccountTypeService constructor takes db_manager and optional app_core
    # For unit tests, we typically don't need a full app_core if service only uses db_manager
    return AccountTypeService(db_manager=mock_db_manager, app_core=None)

# --- Test Cases ---

async def test_get_account_type_by_id_found(account_type_service: AccountTypeService, mock_session: AsyncMock):
    """Test get_by_id when AccountType is found."""
    expected_at = AccountTypeModel(id=1, name="Current Asset", category="Asset", is_debit_balance=True, report_type="BS", display_order=10)
    mock_session.get.return_value = expected_at

    result = await account_type_service.get_by_id(1)
    
    assert result == expected_at
    mock_session.get.assert_awaited_once_with(AccountTypeModel, 1)

async def test_get_account_type_by_id_not_found(account_type_service: AccountTypeService, mock_session: AsyncMock):
    """Test get_by_id when AccountType is not found."""
    mock_session.get.return_value = None

    result = await account_type_service.get_by_id(99)
    
    assert result is None
    mock_session.get.assert_awaited_once_with(AccountTypeModel, 99)

async def test_get_all_account_types(account_type_service: AccountTypeService, mock_session: AsyncMock):
    """Test get_all returns a list of AccountTypes."""
    at1 = AccountTypeModel(id=1, name="CA", category="Asset", is_debit_balance=True, report_type="BS", display_order=10)
    at2 = AccountTypeModel(id=2, name="CL", category="Liability", is_debit_balance=False, report_type="BS", display_order=20)
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.all.return_value = [at1, at2]
    mock_session.execute.return_value = mock_execute_result

    result = await account_type_service.get_all()

    assert len(result) == 2
    assert result[0].name == "CA"
    assert result[1].name == "CL"
    mock_session.execute.assert_awaited_once()
    # We can also assert the statement passed to execute if needed, but it's more complex

async def test_add_account_type(account_type_service: AccountTypeService, mock_session: AsyncMock):
    """Test adding a new AccountType."""
    new_at_data = AccountTypeModel(name="New Type", category="Equity", is_debit_balance=False, report_type="BS", display_order=30)
    
    # Configure refresh to work on the passed object
    async def mock_refresh(obj, attribute_names=None):
        pass # In a real scenario, this might populate obj.id if it's autogenerated
    mock_session.refresh.side_effect = mock_refresh

    result = await account_type_service.add(new_at_data)

    mock_session.add.assert_called_once_with(new_at_data)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(new_at_data)
    assert result == new_at_data

async def test_update_account_type(account_type_service: AccountTypeService, mock_session: AsyncMock):
    """Test updating an existing AccountType."""
    existing_at = AccountTypeModel(id=1, name="Old Name", category="Asset", is_debit_balance=True, report_type="BS", display_order=5)
    existing_at.name = "Updated Name" # Simulate a change
    
    async def mock_refresh_update(obj, attribute_names=None):
        obj.updated_at = MagicMock() # Simulate timestamp update
    mock_session.refresh.side_effect = mock_refresh_update

    result = await account_type_service.update(existing_at)

    mock_session.add.assert_called_once_with(existing_at) # SQLAlchemy uses add for updates too if object is managed
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(existing_at)
    assert result.name == "Updated Name"

async def test_delete_account_type_found(account_type_service: AccountTypeService, mock_session: AsyncMock):
    """Test deleting an existing AccountType."""
    at_to_delete = AccountTypeModel(id=1, name="To Delete", category="Expense", is_debit_balance=True, report_type="PL", display_order=100)
    mock_session.get.return_value = at_to_delete

    result = await account_type_service.delete(1)

    assert result is True
    mock_session.get.assert_awaited_once_with(AccountTypeModel, 1)
    mock_session.delete.assert_awaited_once_with(at_to_delete)

async def test_delete_account_type_not_found(account_type_service: AccountTypeService, mock_session: AsyncMock):
    """Test deleting a non-existent AccountType."""
    mock_session.get.return_value = None

    result = await account_type_service.delete(99)

    assert result is False
    mock_session.get.assert_awaited_once_with(AccountTypeModel, 99)
    mock_session.delete.assert_not_called()

async def test_get_account_type_by_name_found(account_type_service: AccountTypeService, mock_session: AsyncMock):
    """Test get_by_name when AccountType is found."""
    expected_at = AccountTypeModel(id=1, name="Specific Asset", category="Asset", is_debit_balance=True, report_type="BS", display_order=10)
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = expected_at
    mock_session.execute.return_value = mock_execute_result
    
    result = await account_type_service.get_by_name("Specific Asset")
    
    assert result == expected_at
    mock_session.execute.assert_awaited_once() # Could add statement assertion

async def test_get_account_types_by_category(account_type_service: AccountTypeService, mock_session: AsyncMock):
    """Test get_by_category returns a list of matching AccountTypes."""
    at1 = AccountTypeModel(id=1, name="Cash", category="Asset", is_debit_balance=True, report_type="BS", display_order=10)
    at2 = AccountTypeModel(id=2, name="Bank", category="Asset", is_debit_balance=True, report_type="BS", display_order=11)
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.all.return_value = [at1, at2]
    mock_session.execute.return_value = mock_execute_result

    result = await account_type_service.get_by_category("Asset")

    assert len(result) == 2
    assert result[0].name == "Cash"
    assert result[1].category == "Asset"
    mock_session.execute.assert_awaited_once()

```

# tests/unit/services/test_dimension_service.py
```py
# File: tests/unit/services/test_dimension_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from datetime import date, datetime # For created_at/updated_at in model

from app.services.accounting_services import DimensionService
from app.models.accounting.dimension import Dimension as DimensionModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore # For mocking app_core

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_db_manager(mock_session: AsyncMock) -> MagicMock:
    db_manager = MagicMock(spec=DatabaseManager)
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def mock_app_core() -> MagicMock:
    app_core = MagicMock(spec=ApplicationCore)
    app_core.logger = MagicMock() # If service uses logger
    return app_core

@pytest.fixture
def dimension_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> DimensionService:
    return DimensionService(db_manager=mock_db_manager, app_core=mock_app_core)

# Sample Data
@pytest.fixture
def sample_dim_dept_fin() -> DimensionModel:
    return DimensionModel(
        id=1, dimension_type="Department", code="FIN", name="Finance", 
        created_by=1, updated_by=1 # Assuming UserAuditMixin fields are set
    )

@pytest.fixture
def sample_dim_dept_hr() -> DimensionModel:
    return DimensionModel(
        id=2, dimension_type="Department", code="HR", name="Human Resources", 
        is_active=False, created_by=1, updated_by=1
    )

@pytest.fixture
def sample_dim_proj_alpha() -> DimensionModel:
    return DimensionModel(
        id=3, dimension_type="Project", code="ALPHA", name="Project Alpha", 
        created_by=1, updated_by=1
    )

# --- Test Cases ---

async def test_get_dimension_by_id_found(
    dimension_service: DimensionService, mock_session: AsyncMock, sample_dim_dept_fin: DimensionModel
):
    mock_session.get.return_value = sample_dim_dept_fin
    result = await dimension_service.get_by_id(1)
    assert result == sample_dim_dept_fin
    mock_session.get.assert_awaited_once_with(DimensionModel, 1)

async def test_get_dimension_by_id_not_found(dimension_service: DimensionService, mock_session: AsyncMock):
    mock_session.get.return_value = None
    result = await dimension_service.get_by_id(99)
    assert result is None

async def test_get_all_dimensions(
    dimension_service: DimensionService, mock_session: AsyncMock, 
    sample_dim_dept_fin: DimensionModel, sample_dim_proj_alpha: DimensionModel
):
    mock_execute_result = AsyncMock()
    # Service orders by dimension_type, then code
    mock_execute_result.scalars.return_value.all.return_value = [sample_dim_dept_fin, sample_dim_proj_alpha]
    mock_session.execute.return_value = mock_execute_result
    result = await dimension_service.get_all()
    assert len(result) == 2
    assert result[0].code == "FIN"

async def test_add_dimension(dimension_service: DimensionService, mock_session: AsyncMock):
    new_dim_data = DimensionModel(
        dimension_type="Location", code="SG", name="Singapore Office",
        created_by=1, updated_by=1 # Assume set by manager
    )
    async def mock_refresh(obj, attribute_names=None): obj.id = 101
    mock_session.refresh.side_effect = mock_refresh
    
    result = await dimension_service.add(new_dim_data)
    mock_session.add.assert_called_once_with(new_dim_data)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(new_dim_data)
    assert result == new_dim_data
    assert result.id == 101

async def test_delete_dimension_found(
    dimension_service: DimensionService, mock_session: AsyncMock, sample_dim_dept_fin: DimensionModel
):
    mock_session.get.return_value = sample_dim_dept_fin
    deleted = await dimension_service.delete(1)
    assert deleted is True
    mock_session.delete.assert_awaited_once_with(sample_dim_dept_fin)

async def test_get_distinct_dimension_types(dimension_service: DimensionService, mock_session: AsyncMock):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.all.return_value = ["Department", "Project"]
    mock_session.execute.return_value = mock_execute_result
    
    result = await dimension_service.get_distinct_dimension_types()
    assert result == ["Department", "Project"]

async def test_get_dimensions_by_type_active_only(
    dimension_service: DimensionService, mock_session: AsyncMock, sample_dim_dept_fin: DimensionModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.all.return_value = [sample_dim_dept_fin] # sample_dim_dept_hr is inactive
    mock_session.execute.return_value = mock_execute_result
    
    result = await dimension_service.get_dimensions_by_type("Department", active_only=True)
    assert len(result) == 1
    assert result[0] == sample_dim_dept_fin

async def test_get_dimensions_by_type_all(
    dimension_service: DimensionService, mock_session: AsyncMock, 
    sample_dim_dept_fin: DimensionModel, sample_dim_dept_hr: DimensionModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.all.return_value = [sample_dim_dept_fin, sample_dim_dept_hr]
    mock_session.execute.return_value = mock_execute_result
    
    result = await dimension_service.get_dimensions_by_type("Department", active_only=False)
    assert len(result) == 2

async def test_get_by_type_and_code_found(
    dimension_service: DimensionService, mock_session: AsyncMock, sample_dim_dept_fin: DimensionModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = sample_dim_dept_fin
    mock_session.execute.return_value = mock_execute_result
    
    result = await dimension_service.get_by_type_and_code("Department", "FIN")
    assert result == sample_dim_dept_fin

async def test_get_by_type_and_code_not_found(dimension_service: DimensionService, mock_session: AsyncMock):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_execute_result
    
    result = await dimension_service.get_by_type_and_code("Department", "NONEXISTENT")
    assert result is None

```

# tests/unit/services/test_sequence_service.py
```py
# File: tests/unit/services/test_sequence_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Optional
import datetime

from app.services.core_services import SequenceService
from app.models.core.sequence import Sequence as SequenceModel
from app.core.database_manager import DatabaseManager

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    """Fixture to create a mock AsyncSession."""
    session = AsyncMock()
    session.get = AsyncMock() # Not directly used by SequenceService, but good for generic mock
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_db_manager(mock_session: AsyncMock) -> MagicMock:
    """Fixture to create a mock DatabaseManager that returns the mock_session."""
    db_manager = MagicMock(spec=DatabaseManager)
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def sequence_service(mock_db_manager: MagicMock) -> SequenceService:
    """Fixture to create a SequenceService instance with a mocked db_manager."""
    return SequenceService(db_manager=mock_db_manager)

# Sample Data
@pytest.fixture
def sample_sequence_orm() -> SequenceModel:
    return SequenceModel(
        id=1,
        sequence_name="SALES_INVOICE",
        prefix="INV-",
        next_value=101,
        increment_by=1,
        min_value=1,
        max_value=999999,
        cycle=False,
        format_template="{PREFIX}{VALUE:06d}" 
    )

# --- Test Cases ---

async def test_get_sequence_by_name_found(
    sequence_service: SequenceService, 
    mock_session: AsyncMock, 
    sample_sequence_orm: SequenceModel
):
    """Test get_sequence_by_name when the sequence is found."""
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = sample_sequence_orm
    mock_session.execute.return_value = mock_execute_result

    result = await sequence_service.get_sequence_by_name("SALES_INVOICE")
    
    assert result == sample_sequence_orm
    mock_session.execute.assert_awaited_once()
    # We could inspect the statement passed to execute if needed
    # e.g., call_args[0][0].compile(compile_kwargs={"literal_binds": True})

async def test_get_sequence_by_name_not_found(
    sequence_service: SequenceService, 
    mock_session: AsyncMock
):
    """Test get_sequence_by_name when the sequence is not found."""
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_execute_result

    result = await sequence_service.get_sequence_by_name("NON_EXISTENT_SEQ")
    
    assert result is None
    mock_session.execute.assert_awaited_once()

async def test_save_sequence(
    sequence_service: SequenceService, 
    mock_session: AsyncMock, 
    sample_sequence_orm: SequenceModel
):
    """Test saving a Sequence object."""
    
    # Simulate ORM behavior where refresh might update the object (e.g., timestamps)
    async def mock_refresh(obj, attribute_names=None):
        obj.updated_at = datetime.datetime.now(datetime.timezone.utc) # Simulate timestamp update
        if not obj.created_at:
            obj.created_at = datetime.datetime.now(datetime.timezone.utc)
        # If ID were autogenerated and None before save, it would be set here.
        # But for Sequence, sequence_name is unique key and ID is serial.
    mock_session.refresh.side_effect = mock_refresh

    sequence_to_save = sample_sequence_orm
    result = await sequence_service.save_sequence(sequence_to_save)

    mock_session.add.assert_called_once_with(sequence_to_save)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(sequence_to_save)
    assert result == sequence_to_save
    assert result.updated_at is not None # Check that refresh side_effect worked

async def test_save_new_sequence_object(
    sequence_service: SequenceService, 
    mock_session: AsyncMock
):
    """Test saving a brand new Sequence object instance."""
    new_sequence = SequenceModel(
        sequence_name="TEST_SEQ",
        prefix="TS-",
        next_value=1,
        increment_by=1,
        format_template="{PREFIX}{VALUE:04d}"
    )
    
    async def mock_refresh_new(obj, attribute_names=None):
        obj.id = 123 # Simulate ID generation
        obj.created_at = datetime.datetime.now(datetime.timezone.utc)
        obj.updated_at = datetime.datetime.now(datetime.timezone.utc)
    mock_session.refresh.side_effect = mock_refresh_new

    result = await sequence_service.save_sequence(new_sequence)

    mock_session.add.assert_called_once_with(new_sequence)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(new_sequence)
    assert result.id == 123
    assert result.prefix == "TS-"

```

# tests/unit/services/test_fiscal_year_service.py
```py
# File: tests/unit/services/test_fiscal_year_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal # For context

from app.services.accounting_services import FiscalYearService
from app.models.accounting.fiscal_year import FiscalYear as FiscalYearModel
from app.models.accounting.fiscal_period import FiscalPeriod as FiscalPeriodModel # For testing delete constraint
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore # For mocking app_core

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_db_manager(mock_session: AsyncMock) -> MagicMock:
    db_manager = MagicMock(spec=DatabaseManager)
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def mock_app_core() -> MagicMock:
    """Fixture to create a basic mock ApplicationCore."""
    app_core = MagicMock(spec=ApplicationCore)
    # Add logger mock if FiscalYearService uses it (currently doesn't seem to directly)
    app_core.logger = MagicMock() 
    return app_core

@pytest.fixture
def fiscal_year_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> FiscalYearService:
    return FiscalYearService(db_manager=mock_db_manager, app_core=mock_app_core)

# Sample Data
@pytest.fixture
def sample_fy_2023() -> FiscalYearModel:
    return FiscalYearModel(
        id=1, year_name="FY2023", 
        start_date=date(2023, 1, 1), end_date=date(2023, 12, 31),
        created_by_user_id=1, updated_by_user_id=1,
        fiscal_periods=[] # Initialize with no periods for some tests
    )

@pytest.fixture
def sample_fy_2024() -> FiscalYearModel:
    return FiscalYearModel(
        id=2, year_name="FY2024", 
        start_date=date(2024, 1, 1), end_date=date(2024, 12, 31),
        created_by_user_id=1, updated_by_user_id=1,
        fiscal_periods=[]
    )

# --- Test Cases ---

async def test_get_fy_by_id_found(
    fiscal_year_service: FiscalYearService, 
    mock_session: AsyncMock, 
    sample_fy_2023: FiscalYearModel
):
    mock_session.get.return_value = sample_fy_2023
    result = await fiscal_year_service.get_by_id(1)
    assert result == sample_fy_2023
    mock_session.get.assert_awaited_once_with(FiscalYearModel, 1)

async def test_get_fy_by_id_not_found(fiscal_year_service: FiscalYearService, mock_session: AsyncMock):
    mock_session.get.return_value = None
    result = await fiscal_year_service.get_by_id(99)
    assert result is None

async def test_get_all_fys(
    fiscal_year_service: FiscalYearService, 
    mock_session: AsyncMock, 
    sample_fy_2023: FiscalYearModel, 
    sample_fy_2024: FiscalYearModel
):
    mock_execute_result = AsyncMock()
    # Service orders by start_date.desc()
    mock_execute_result.scalars.return_value.all.return_value = [sample_fy_2024, sample_fy_2023]
    mock_session.execute.return_value = mock_execute_result
    result = await fiscal_year_service.get_all()
    assert len(result) == 2
    assert result[0].year_name == "FY2024"

async def test_save_new_fy(fiscal_year_service: FiscalYearService, mock_session: AsyncMock):
    new_fy_data = FiscalYearModel(
        year_name="FY2025", start_date=date(2025,1,1), end_date=date(2025,12,31),
        created_by_user_id=1, updated_by_user_id=1 # Assume set by manager before service.save
    )
    async def mock_refresh(obj, attribute_names=None): obj.id = 100
    mock_session.refresh.side_effect = mock_refresh
    
    result = await fiscal_year_service.save(new_fy_data) # Covers add()
    mock_session.add.assert_called_once_with(new_fy_data)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(new_fy_data)
    assert result == new_fy_data
    assert result.id == 100

async def test_delete_fy_no_periods(
    fiscal_year_service: FiscalYearService, 
    mock_session: AsyncMock, 
    sample_fy_2023: FiscalYearModel
):
    sample_fy_2023.fiscal_periods = [] # Ensure no periods
    mock_session.get.return_value = sample_fy_2023
    deleted = await fiscal_year_service.delete(sample_fy_2023.id)
    assert deleted is True
    mock_session.delete.assert_awaited_once_with(sample_fy_2023)

async def test_delete_fy_with_periods_raises_error(
    fiscal_year_service: FiscalYearService, 
    mock_session: AsyncMock, 
    sample_fy_2023: FiscalYearModel
):
    # Simulate FY having periods
    sample_fy_2023.fiscal_periods = [FiscalPeriodModel(id=10, name="Jan", fiscal_year_id=sample_fy_2023.id, start_date=date(2023,1,1), end_date=date(2023,1,31), period_type="Month", status="Open", period_number=1, created_by_user_id=1, updated_by_user_id=1)]
    mock_session.get.return_value = sample_fy_2023
    
    with pytest.raises(ValueError) as excinfo:
        await fiscal_year_service.delete(sample_fy_2023.id)
    assert f"Cannot delete fiscal year '{sample_fy_2023.year_name}' as it has associated fiscal periods." in str(excinfo.value)
    mock_session.delete.assert_not_called()

async def test_delete_fy_not_found(fiscal_year_service: FiscalYearService, mock_session: AsyncMock):
    mock_session.get.return_value = None
    deleted = await fiscal_year_service.delete(99)
    assert deleted is False

async def test_get_fy_by_name_found(
    fiscal_year_service: FiscalYearService, 
    mock_session: AsyncMock, 
    sample_fy_2023: FiscalYearModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = sample_fy_2023
    mock_session.execute.return_value = mock_execute_result
    
    result = await fiscal_year_service.get_by_name("FY2023")
    assert result == sample_fy_2023

async def test_get_fy_by_date_overlap_found(
    fiscal_year_service: FiscalYearService, 
    mock_session: AsyncMock, 
    sample_fy_2023: FiscalYearModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = sample_fy_2023
    mock_session.execute.return_value = mock_execute_result
    
    result = await fiscal_year_service.get_by_date_overlap(date(2023,6,1), date(2023,7,1))
    assert result == sample_fy_2023

async def test_get_fy_by_date_overlap_not_found(
    fiscal_year_service: FiscalYearService, mock_session: AsyncMock
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_execute_result
    
    result = await fiscal_year_service.get_by_date_overlap(date(2025,1,1), date(2025,12,31))
    assert result is None

async def test_get_fy_by_date_overlap_exclude_id(
    fiscal_year_service: FiscalYearService, mock_session: AsyncMock
):
    mock_execute_result = AsyncMock()
    # Simulate it would find something, but exclude_id prevents it
    mock_execute_result.scalars.return_value.first.return_value = None 
    mock_session.execute.return_value = mock_execute_result
    
    result = await fiscal_year_service.get_by_date_overlap(date(2023,6,1), date(2023,7,1), exclude_id=1)
    assert result is None 
    # To properly test exclude_id, the mock for session.execute would need to be more sophisticated
    # to check the WHERE clause of the statement passed to it. For now, this ensures it's called.
    mock_session.execute.assert_awaited_once()

```

# tests/unit/test_example_unit.py
```py

```

