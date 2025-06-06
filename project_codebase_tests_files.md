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

# tests/unit/tax/test_gst_manager.py
```py
# File: tests/unit/tax/test_gst_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date

from app.tax.gst_manager import GSTManager
from app.services.tax_service import TaxCodeService, GSTReturnService
from app.services.journal_service import JournalService
from app.services.core_services import CompanySettingsService, SequenceService 
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.accounting.journal_entry_manager import JournalEntryManager
from app.core.application_core import ApplicationCore 
from app.models.core.company_setting import CompanySetting as CompanySettingModel
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine
from app.models.accounting.account import Account as AccountModel
from app.models.accounting.tax_code import TaxCode as TaxCodeModel
from app.models.accounting.gst_return import GSTReturn as GSTReturnModel
from app.utils.pydantic_models import GSTReturnData, JournalEntryData, GSTTransactionLineDetail
from app.utils.result import Result
from app.common.enums import GSTReturnStatusEnum
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_tax_code_service() -> AsyncMock: return AsyncMock(spec=TaxCodeService)
@pytest.fixture
def mock_journal_service() -> AsyncMock: return AsyncMock(spec=JournalService)
@pytest.fixture
def mock_company_settings_service() -> AsyncMock: return AsyncMock(spec=CompanySettingsService)
@pytest.fixture
def mock_gst_return_service() -> AsyncMock: return AsyncMock(spec=GSTReturnService)
@pytest.fixture
def mock_account_service() -> AsyncMock: return AsyncMock(spec=AccountService)
@pytest.fixture
def mock_fiscal_period_service() -> AsyncMock: return AsyncMock(spec=FiscalPeriodService)
@pytest.fixture
def mock_sequence_generator() -> AsyncMock: return AsyncMock() 
@pytest.fixture
def mock_journal_entry_manager() -> AsyncMock: return AsyncMock(spec=JournalEntryManager)

@pytest.fixture
def mock_app_core(
    mock_journal_entry_manager: AsyncMock, 
    mock_configuration_service: AsyncMock 
) -> MagicMock:
    app_core = MagicMock(spec=ApplicationCore)
    app_core.logger = MagicMock(spec=logging.Logger)
    app_core.journal_entry_manager = mock_journal_entry_manager
    app_core.configuration_service = mock_configuration_service 
    return app_core

@pytest.fixture 
def mock_configuration_service() -> AsyncMock: return AsyncMock(spec=ConfigurationService)

@pytest.fixture
def gst_manager(
    mock_tax_code_service: AsyncMock, mock_journal_service: AsyncMock, 
    mock_company_settings_service: AsyncMock, mock_gst_return_service: AsyncMock,
    mock_account_service: AsyncMock, mock_fiscal_period_service: AsyncMock,
    mock_sequence_generator: AsyncMock, mock_app_core: MagicMock
) -> GSTManager:
    return GSTManager(
        tax_code_service=mock_tax_code_service, journal_service=mock_journal_service,
        company_settings_service=mock_company_settings_service, gst_return_service=mock_gst_return_service,
        account_service=mock_account_service, fiscal_period_service=mock_fiscal_period_service,
        sequence_generator=mock_sequence_generator, app_core=mock_app_core
    )

@pytest.fixture
def sample_company_settings() -> CompanySettingModel:
    return CompanySettingModel(id=1, company_name="Test Biz", gst_registration_no="M12345678Z", base_currency="SGD", updated_by_user_id=1)

@pytest.fixture
def sample_sr_tax_code() -> TaxCodeModel:
    return TaxCodeModel(id=1, code="SR", tax_type="GST", rate=Decimal("9.00"), affects_account_id=101)

@pytest.fixture
def sample_tx_tax_code() -> TaxCodeModel:
    return TaxCodeModel(id=2, code="TX", tax_type="GST", rate=Decimal("9.00"), affects_account_id=102)

@pytest.fixture
def sample_revenue_account() -> AccountModel:
    return AccountModel(id=201, code="4000", name="Sales", account_type="Revenue", created_by_user_id=1,updated_by_user_id=1)

@pytest.fixture
def sample_expense_account() -> AccountModel:
    return AccountModel(id=202, code="5000", name="Purchases", account_type="Expense", created_by_user_id=1,updated_by_user_id=1)

@pytest.fixture
def sample_posted_je_sales(sample_revenue_account: AccountModel, sample_sr_tax_code: TaxCodeModel) -> JournalEntry:
    je = JournalEntry(id=10, entry_no="JE-S001", entry_date=date(2023,1,15), is_posted=True, created_by_user_id=1,updated_by_user_id=1, description="Sales Inv #1")
    je.lines = [
        JournalEntryLine(account_id=999, account=AccountModel(id=999,code="AR",name="AR",account_type="Asset",created_by_user_id=1,updated_by_user_id=1), debit_amount=Decimal("109.00")),
        JournalEntryLine(account_id=sample_revenue_account.id, account=sample_revenue_account, credit_amount=Decimal("100.00"), tax_code="SR", tax_code_obj=sample_sr_tax_code, tax_amount=Decimal("9.00"), description="Sale of goods")
    ]
    return je

@pytest.fixture
def sample_posted_je_purchase(sample_expense_account: AccountModel, sample_tx_tax_code: TaxCodeModel) -> JournalEntry:
    je = JournalEntry(id=11, entry_no="JE-P001", entry_date=date(2023,1,20), is_posted=True, created_by_user_id=1,updated_by_user_id=1, description="Purchase Inv #P1")
    je.lines = [
        JournalEntryLine(account_id=sample_expense_account.id, account=sample_expense_account, debit_amount=Decimal("50.00"), tax_code="TX", tax_code_obj=sample_tx_tax_code, tax_amount=Decimal("4.50"), description="Purchase of materials"),
        JournalEntryLine(account_id=888, account=AccountModel(id=888,code="AP",name="AP",account_type="Liability",created_by_user_id=1,updated_by_user_id=1), credit_amount=Decimal("54.50"))
    ]
    return je

@pytest.fixture
def sample_gst_return_draft_orm() -> GSTReturnModel:
    return GSTReturnModel(
        id=1, return_period="Q1/2023", start_date=date(2023,1,1), end_date=date(2023,3,31),
        filing_due_date=date(2023,4,30), status=GSTReturnStatusEnum.DRAFT.value,
        output_tax=Decimal("1000.00"), input_tax=Decimal("300.00"), tax_payable=Decimal("700.00"),
        created_by_user_id=1, updated_by_user_id=1
    )


# --- Test Cases ---
async def test_prepare_gst_return_data_no_company_settings(gst_manager: GSTManager, mock_company_settings_service: AsyncMock):
    mock_company_settings_service.get_company_settings.return_value = None
    result = await gst_manager.prepare_gst_return_data(date(2023,1,1), date(2023,3,31), 1)
    assert not result.is_success
    assert "Company settings not found" in result.errors[0]

async def test_prepare_gst_return_data_no_transactions(gst_manager: GSTManager, mock_company_settings_service: AsyncMock, mock_journal_service: AsyncMock, sample_company_settings: CompanySettingModel):
    mock_company_settings_service.get_company_settings.return_value = sample_company_settings
    mock_journal_service.get_posted_entries_by_date_range.return_value = []
    
    result = await gst_manager.prepare_gst_return_data(date(2023,1,1), date(2023,3,31), 1)
    
    assert result.is_success
    data = result.value
    assert data is not None
    assert data.standard_rated_supplies == Decimal(0)
    assert data.output_tax == Decimal(0)
    assert data.tax_payable == Decimal(0)
    assert not data.detailed_breakdown["box1_standard_rated_supplies"] # Empty list

async def test_prepare_gst_return_data_with_sales_and_purchases(
    gst_manager: GSTManager, mock_company_settings_service: AsyncMock, mock_journal_service: AsyncMock,
    sample_company_settings: CompanySettingModel, sample_posted_je_sales: JournalEntry, sample_posted_je_purchase: JournalEntry
):
    mock_company_settings_service.get_company_settings.return_value = sample_company_settings
    mock_journal_service.get_posted_entries_by_date_range.return_value = [sample_posted_je_sales, sample_posted_je_purchase]
    
    result = await gst_manager.prepare_gst_return_data(date(2023,1,1), date(2023,3,31), 1)
    
    assert result.is_success
    data = result.value
    assert data is not None
    assert data.standard_rated_supplies == Decimal("100.00") 
    assert data.output_tax == Decimal("9.00")
    assert data.taxable_purchases == Decimal("50.00") 
    assert data.input_tax == Decimal("4.50")
    assert data.tax_payable == Decimal("4.50") 
    assert len(data.detailed_breakdown["box1_standard_rated_supplies"]) == 1
    assert data.detailed_breakdown["box1_standard_rated_supplies"][0].net_amount == Decimal("100.00")
    assert len(data.detailed_breakdown["box6_output_tax_details"]) == 1
    assert len(data.detailed_breakdown["box5_taxable_purchases"]) == 1
    assert data.detailed_breakdown["box5_taxable_purchases"][0].net_amount == Decimal("50.00")
    assert len(data.detailed_breakdown["box7_input_tax_details"]) == 1

async def test_save_gst_return_new(gst_manager: GSTManager, mock_gst_return_service: AsyncMock):
    gst_data_dto = GSTReturnData(
        return_period="Q1/2024", start_date=date(2024,1,1), end_date=date(2024,3,31),
        standard_rated_supplies=Decimal(1000), output_tax=Decimal(90), user_id=1
    )
    mock_gst_return_service.get_by_id.return_value = None 
    
    async def mock_save(return_orm: GSTReturnModel):
        return_orm.id = 10; return return_orm
    mock_gst_return_service.save_gst_return.side_effect = mock_save
    
    result = await gst_manager.save_gst_return(gst_data_dto)
    
    assert result.is_success; assert result.value is not None; assert result.value.id == 10

async def test_finalize_gst_return_success_with_je(
    gst_manager: GSTManager, mock_gst_return_service: AsyncMock, mock_journal_entry_manager: AsyncMock,
    mock_account_service: AsyncMock, mock_configuration_service: AsyncMock, sample_gst_return_draft_orm: GSTReturnModel
):
    sample_gst_return_draft_orm.status = GSTReturnStatusEnum.DRAFT.value
    sample_gst_return_draft_orm.tax_payable = Decimal("700.00")
    mock_gst_return_service.get_by_id.return_value = sample_gst_return_draft_orm
    
    mock_configuration_service.get_config_value.side_effect = lambda key, default: {"SysAcc_DefaultGSTOutput": "SYS-GST-OUT", "SysAcc_DefaultGSTInput": "SYS-GST-IN", "SysAcc_GSTControl": "SYS-GST-CTRL"}.get(key, default)
    mock_account_service.get_by_code.side_effect = lambda code: MagicMock(spec=AccountModel, id=hash(code), code=code, is_active=True)

    mock_created_je = MagicMock(spec=JournalEntry, id=55)
    mock_journal_entry_manager.create_journal_entry.return_value = Result.success(mock_created_je)
    mock_journal_entry_manager.post_journal_entry.return_value = Result.success(mock_created_je)
    mock_gst_return_service.save_gst_return.side_effect = lambda orm_obj: orm_obj

    result = await gst_manager.finalize_gst_return(1, "REF123", date(2023,4,10), 1)

    assert result.is_success
    finalized_return = result.value
    assert finalized_return is not None
    assert finalized_return.status == GSTReturnStatusEnum.SUBMITTED.value
    assert finalized_return.journal_entry_id == 55

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
from decimal import Decimal # Not directly used for SequenceGenerator, but often in related tests
import logging # Added import for logging.Logger

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
    service.save_sequence = AsyncMock(return_value=None) 
    return service

@pytest.fixture
def mock_db_manager() -> AsyncMock:
    """Fixture to create a mock DatabaseManager."""
    db_manager = AsyncMock(spec=DatabaseManager)
    db_manager.execute_scalar = AsyncMock()
    db_manager.logger = AsyncMock(spec=logging.Logger) # logging.Logger can now be resolved
    db_manager.logger.warning = MagicMock()
    db_manager.logger.error = MagicMock()
    db_manager.logger.info = MagicMock()
    return db_manager

@pytest.fixture
def mock_app_core(mock_db_manager: AsyncMock, mock_sequence_service: AsyncMock) -> MagicMock:
    """Fixture to create a mock ApplicationCore providing mocked db_manager and sequence_service."""
    app_core = MagicMock(spec=ApplicationCore)
    app_core.db_manager = mock_db_manager
    app_core.sequence_service = mock_sequence_service
    app_core.logger = MagicMock(spec=logging.Logger) 
    return app_core

@pytest.fixture
def sequence_generator(mock_sequence_service: AsyncMock, mock_app_core: MagicMock) -> SequenceGenerator:
    """Fixture to create a SequenceGenerator instance."""
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
    mock_app_core.db_manager.execute_scalar.return_value = None 

    mock_sequence_orm = SequenceModel(
        id=1, sequence_name=sequence_name, prefix="PO", next_value=10, 
        increment_by=1, min_value=1, max_value=9999, cycle=False,
        format_template="{PREFIX}-{VALUE:04d}"
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj 

    result = await sequence_generator.next_sequence(sequence_name)

    assert result == "PO-0010"
    mock_app_core.db_manager.execute_scalar.assert_awaited_once()
    mock_sequence_service.get_sequence_by_name.assert_awaited_once_with(sequence_name)
    mock_sequence_service.save_sequence.assert_awaited_once()
    assert mock_sequence_orm.next_value == 11

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
    mock_app_core: MagicMock, 
    mock_sequence_service: AsyncMock
):
    """Test Python fallback creates a new sequence if not found in DB."""
    sequence_name = "NEW_SEQ"
    mock_app_core.db_manager.execute_scalar.return_value = None 
    mock_sequence_service.get_sequence_by_name.return_value = None 

    saved_sequence_holder = {}
    async def capture_save(seq_obj):
        saved_sequence_holder['seq'] = seq_obj
        return seq_obj
    mock_sequence_service.save_sequence.side_effect = capture_save
    
    result = await sequence_generator.next_sequence(sequence_name)

    assert result == "NEW-000001" 
    mock_sequence_service.get_sequence_by_name.assert_awaited_once_with(sequence_name)
    assert mock_sequence_service.save_sequence.await_count == 2
    
    created_seq = saved_sequence_holder['seq']
    assert created_seq.sequence_name == sequence_name
    assert created_seq.prefix == "NEW"
    assert created_seq.next_value == 2
    assert created_seq.format_template == "{PREFIX}-{VALUE:06d}"

async def test_next_sequence_python_fallback_prefix_override(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock,
    mock_sequence_service: AsyncMock
):
    """Test Python fallback with prefix_override."""
    sequence_name = "ITEM_CODE"
    mock_app_core.db_manager.execute_scalar.side_effect = AssertionError("DB function should not be called with prefix_override")

    mock_sequence_orm = SequenceModel(
        id=3, sequence_name=sequence_name, prefix="ITM", next_value=5, 
        increment_by=1, format_template="{PREFIX}-{VALUE:03d}"
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj
    
    result = await sequence_generator.next_sequence(sequence_name, prefix_override="OVERRIDE")

    assert result == "OVERRIDE-005"
    mock_app_core.db_manager.execute_scalar.assert_not_awaited() 
    mock_sequence_service.get_sequence_by_name.assert_awaited_once_with(sequence_name)
    assert mock_sequence_orm.next_value == 6

async def test_next_sequence_python_fallback_cycle(
    sequence_generator: SequenceGenerator,
    mock_app_core: MagicMock,
    mock_sequence_service: AsyncMock
):
    """Test Python fallback sequence cycling."""
    sequence_name = "CYCLE_SEQ"
    mock_app_core.db_manager.execute_scalar.return_value = None 

    mock_sequence_orm = SequenceModel(
        id=4, sequence_name=sequence_name, prefix="CY", next_value=3, 
        increment_by=1, min_value=1, max_value=3, cycle=True,
        format_template="{PREFIX}{VALUE}"
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj

    result1 = await sequence_generator.next_sequence(sequence_name) 
    assert result1 == "CY3"
    assert mock_sequence_orm.next_value == 1 

    result2 = await sequence_generator.next_sequence(sequence_name) 
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
        increment_by=1, min_value=1, max_value=3, cycle=False, 
        format_template="{PREFIX}{VALUE}"
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj

    result = await sequence_generator.next_sequence(sequence_name) 
    assert result == "MX3"
    assert mock_sequence_orm.next_value == 4 

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
        increment_by=1, format_template="{PREFIX}{VALUE:06}"
    )
    mock_sequence_service.get_sequence_by_name.return_value = mock_sequence_orm
    mock_sequence_service.save_sequence.side_effect = lambda seq_obj: seq_obj

    result = await sequence_generator.next_sequence(sequence_name)
    assert result == "ZF000007"

```

# tests/unit/services/test_payment_service.py
```py
# File: tests/unit/services/test_payment_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime

from app.services.business_services import PaymentService
from app.models.business.payment import Payment, PaymentAllocation
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.bank_account import BankAccount
from app.models.accounting.currency import Currency
from app.models.accounting.journal_entry import JournalEntry
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import PaymentSummaryData
from app.common.enums import PaymentTypeEnum, PaymentMethodEnum, PaymentEntityTypeEnum, PaymentStatusEnum, InvoiceStatusEnum
import logging

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
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
    app_core.logger = MagicMock(spec=logging.Logger)
    return app_core

@pytest.fixture
def payment_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> PaymentService:
    return PaymentService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_customer_orm() -> Customer:
    return Customer(id=1, name="Test Customer Inc.", customer_code="CUST001", created_by_user_id=1,updated_by_user_id=1)

@pytest.fixture
def sample_vendor_orm() -> Vendor:
    return Vendor(id=2, name="Test Vendor Ltd.", vendor_code="VEND001", created_by_user_id=1,updated_by_user_id=1)

@pytest.fixture
def sample_payment_orm(sample_customer_orm: Customer) -> Payment:
    return Payment(
        id=1, payment_no="PAY001", 
        payment_type=PaymentTypeEnum.CUSTOMER_PAYMENT.value,
        payment_method=PaymentMethodEnum.BANK_TRANSFER.value,
        payment_date=date(2023, 5, 15),
        entity_type=PaymentEntityTypeEnum.CUSTOMER.value,
        entity_id=sample_customer_orm.id,
        amount=Decimal("100.00"), currency_code="SGD",
        status=PaymentStatusEnum.DRAFT.value,
        created_by_user_id=1, updated_by_user_id=1,
        allocations=[] # Assuming no allocations by default for simplicity in some tests
    )

# --- Test Cases ---

async def test_get_payment_by_id_found(payment_service: PaymentService, mock_session: AsyncMock, sample_payment_orm: Payment):
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_payment_orm
    result = await payment_service.get_by_id(1)
    assert result == sample_payment_orm
    assert result is not None # For mypy
    assert result.payment_no == "PAY001"
    mock_session.execute.assert_awaited_once()

async def test_get_payment_by_id_not_found(payment_service: PaymentService, mock_session: AsyncMock):
    mock_session.execute.return_value.scalars.return_value.first.return_value = None
    result = await payment_service.get_by_id(99)
    assert result is None

async def test_get_all_payments(payment_service: PaymentService, mock_session: AsyncMock, sample_payment_orm: Payment):
    mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_payment_orm]
    result = await payment_service.get_all()
    assert len(result) == 1
    assert result[0].payment_no == "PAY001"

async def test_get_by_payment_no_found(payment_service: PaymentService, mock_session: AsyncMock, sample_payment_orm: Payment):
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_payment_orm
    result = await payment_service.get_by_payment_no("PAY001")
    assert result is not None
    assert result.id == 1

async def test_get_all_summary_no_filters(payment_service: PaymentService, mock_session: AsyncMock, sample_payment_orm: Payment):
    mock_row_mapping = MagicMock()
    mock_row_mapping._asdict.return_value = {
        "id": sample_payment_orm.id, "payment_no": sample_payment_orm.payment_no,
        "payment_date": sample_payment_orm.payment_date, "payment_type": sample_payment_orm.payment_type,
        "payment_method": sample_payment_orm.payment_method, "entity_type": sample_payment_orm.entity_type,
        "entity_id": sample_payment_orm.entity_id, "amount": sample_payment_orm.amount,
        "currency_code": sample_payment_orm.currency_code, "status": sample_payment_orm.status,
        "entity_name": "Test Customer Inc." # This would be result of subquery in real scenario
    }
    mock_session.execute.return_value.mappings.return_value.all.return_value = [mock_row_mapping]
    
    summaries = await payment_service.get_all_summary()
    assert len(summaries) == 1
    assert isinstance(summaries[0], PaymentSummaryData)
    assert summaries[0].payment_no == "PAY001"
    assert summaries[0].entity_name == "Test Customer Inc."

async def test_save_new_payment(payment_service: PaymentService, mock_session: AsyncMock, sample_customer_orm: Customer):
    new_payment = Payment(
        payment_type=PaymentTypeEnum.CUSTOMER_PAYMENT.value,
        payment_method=PaymentMethodEnum.CASH.value,
        payment_date=date(2023, 6, 1),
        entity_type=PaymentEntityTypeEnum.CUSTOMER.value,
        entity_id=sample_customer_orm.id,
        amount=Decimal("50.00"), currency_code="SGD",
        status=PaymentStatusEnum.DRAFT.value,
        created_by_user_id=1, updated_by_user_id=1
    )
    # Simulate ORM refresh after save
    async def mock_refresh(obj, attribute_names=None):
        obj.id = 2 # Simulate ID generation
        obj.payment_no = "PAY002" # Simulate sequence/logic setting this
        if attribute_names and 'allocations' in attribute_names:
            obj.allocations = [] # Simulate allocations list refresh
    mock_session.refresh.side_effect = mock_refresh

    result = await payment_service.save(new_payment)
    
    mock_session.add.assert_called_once_with(new_payment)
    mock_session.flush.assert_awaited_once()
    # Refresh is called twice if allocations is not None
    mock_session.refresh.assert_any_call(new_payment)
    if hasattr(new_payment, 'allocations') and new_payment.allocations is not None :
        mock_session.refresh.assert_any_call(new_payment, attribute_names=['allocations'])
    
    assert result.id == 2
    assert result.payment_no == "PAY002"

async def test_save_updated_payment(payment_service: PaymentService, mock_session: AsyncMock, sample_payment_orm: Payment):
    sample_payment_orm.reference = "Updated Ref"
    
    result = await payment_service.save(sample_payment_orm)
    
    mock_session.add.assert_called_once_with(sample_payment_orm)
    assert result.reference == "Updated Ref"

async def test_delete_draft_payment_success(payment_service: PaymentService, mock_session: AsyncMock, sample_payment_orm: Payment):
    sample_payment_orm.status = PaymentStatusEnum.DRAFT.value # Ensure it's draft
    mock_session.get.return_value = sample_payment_orm
    
    deleted = await payment_service.delete(1)
    assert deleted is True
    mock_session.get.assert_awaited_once_with(Payment, 1)
    mock_session.delete.assert_awaited_once_with(sample_payment_orm)

async def test_delete_non_draft_payment_fails(payment_service: PaymentService, mock_session: AsyncMock, sample_payment_orm: Payment):
    sample_payment_orm.status = PaymentStatusEnum.APPROVED.value # Not draft
    mock_session.get.return_value = sample_payment_orm
    
    deleted = await payment_service.delete(1)
    assert deleted is False
    mock_session.get.assert_awaited_once_with(Payment, 1)
    mock_session.delete.assert_not_called()
    # Check logger warning if app_core.logger was properly injected and used in service
    payment_service.logger.warning.assert_called_once()


async def test_delete_payment_not_found(payment_service: PaymentService, mock_session: AsyncMock):
    mock_session.get.return_value = None
    deleted = await payment_service.delete(99)
    assert deleted is False

```

# tests/unit/services/test_sales_invoice_service.py
```py
# File: tests/unit/services/test_sales_invoice_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime

from app.services.business_services import SalesInvoiceService
from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.business.customer import Customer
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import SalesInvoiceSummaryData
from app.common.enums import InvoiceStatusEnum
import logging # For logger spec

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
    app_core.logger = MagicMock(spec=logging.Logger)
    return app_core

@pytest.fixture
def sales_invoice_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> SalesInvoiceService:
    return SalesInvoiceService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_customer_orm() -> Customer:
    return Customer(id=1, customer_code="CUS001", name="Test Customer", created_by_user_id=1, updated_by_user_id=1)

@pytest.fixture
def sample_sales_invoice_orm(sample_customer_orm: Customer) -> SalesInvoice:
    return SalesInvoice(
        id=1, invoice_no="INV001", customer_id=sample_customer_orm.id, customer=sample_customer_orm,
        invoice_date=date(2023, 1, 15), due_date=date(2023, 2, 15),
        currency_code="SGD", total_amount=Decimal("109.00"), amount_paid=Decimal("0.00"),
        status=InvoiceStatusEnum.DRAFT.value, created_by_user_id=1, updated_by_user_id=1,
        lines=[
            SalesInvoiceLine(id=1, invoice_id=1, description="Item A", quantity=Decimal(1), unit_price=Decimal(100), line_total=Decimal(109), tax_amount=Decimal(9))
        ]
    )

# --- Test Cases ---

async def test_get_by_id_found(sales_invoice_service: SalesInvoiceService, mock_session: AsyncMock, sample_sales_invoice_orm: SalesInvoice):
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_sales_invoice_orm
    result = await sales_invoice_service.get_by_id(1)
    assert result == sample_sales_invoice_orm
    mock_session.execute.assert_awaited_once()

async def test_get_by_id_not_found(sales_invoice_service: SalesInvoiceService, mock_session: AsyncMock):
    mock_session.execute.return_value.scalars.return_value.first.return_value = None
    result = await sales_invoice_service.get_by_id(99)
    assert result is None

async def test_get_all_summary(sales_invoice_service: SalesInvoiceService, mock_session: AsyncMock, sample_sales_invoice_orm: SalesInvoice):
    mock_row = MagicMock()
    mock_row._asdict.return_value = { # Simulate RowMapping._asdict()
        "id": sample_sales_invoice_orm.id,
        "invoice_no": sample_sales_invoice_orm.invoice_no,
        "invoice_date": sample_sales_invoice_orm.invoice_date,
        "due_date": sample_sales_invoice_orm.due_date,
        "customer_name": sample_sales_invoice_orm.customer.name,
        "total_amount": sample_sales_invoice_orm.total_amount,
        "amount_paid": sample_sales_invoice_orm.amount_paid,
        "status": sample_sales_invoice_orm.status,
        "currency_code": sample_sales_invoice_orm.currency_code,
    }
    mock_session.execute.return_value.mappings.return_value.all.return_value = [mock_row]
    
    result_dtos = await sales_invoice_service.get_all_summary()
    assert len(result_dtos) == 1
    assert isinstance(result_dtos[0], SalesInvoiceSummaryData)
    assert result_dtos[0].invoice_no == "INV001"

async def test_save_new_invoice(sales_invoice_service: SalesInvoiceService, mock_session: AsyncMock, sample_customer_orm: Customer):
    new_invoice = SalesInvoice(
        customer_id=sample_customer_orm.id, invoice_date=date(2023, 3, 1), due_date=date(2023, 3, 31),
        currency_code="SGD", total_amount=Decimal("200.00"), status=InvoiceStatusEnum.DRAFT.value,
        created_by_user_id=1, updated_by_user_id=1
    )
    # Simulate what refresh would do after save
    async def mock_refresh(obj, attribute_names=None):
        obj.id = 10 # Simulate ID generated by DB
        obj.invoice_no = "INV002" # Simulate sequence generation
        obj.created_at = datetime.now()
        obj.updated_at = datetime.now()
        if attribute_names and 'lines' in attribute_names and not hasattr(obj, 'lines_loaded_flag'): # Mock simple line loading
             obj.lines = [SalesInvoiceLine(id=1, description="Test", quantity=1, unit_price=100, line_total=100)]
             obj.lines_loaded_flag = True
    mock_session.refresh.side_effect = mock_refresh

    result = await sales_invoice_service.save(new_invoice)
    
    mock_session.add.assert_called_once_with(new_invoice)
    mock_session.flush.assert_awaited_once()
    # Refresh will be called twice if lines are present and invoice.id is set
    assert mock_session.refresh.await_count >= 1 
    assert result.id == 10
    assert result.invoice_no == "INV002"

async def test_get_outstanding_invoices_for_customer(
    sales_invoice_service: SalesInvoiceService, mock_session: AsyncMock, sample_sales_invoice_orm: SalesInvoice
):
    # Make sample invoice outstanding
    sample_sales_invoice_orm.status = InvoiceStatusEnum.APPROVED.value
    sample_sales_invoice_orm.amount_paid = Decimal("50.00")
    sample_sales_invoice_orm.total_amount = Decimal("109.00")
    sample_sales_invoice_orm.invoice_date = date(2023, 1, 1)
    sample_sales_invoice_orm.due_date = date(2023, 1, 31)


    mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_sales_invoice_orm]
    
    as_of = date(2023, 2, 1) # Invoice is overdue
    results = await sales_invoice_service.get_outstanding_invoices_for_customer(customer_id=1, as_of_date=as_of)

    assert len(results) == 1
    assert results[0].id == sample_sales_invoice_orm.id
    mock_session.execute.assert_awaited_once()
    # Can add more assertions on the query conditions if needed

```

# tests/unit/services/test_journal_service.py
```py
# File: tests/unit/services/test_journal_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date, datetime

from app.services.journal_service import JournalService
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine
from app.models.accounting.account import Account
from app.models.accounting.recurring_pattern import RecurringPattern
from app.models.accounting.fiscal_period import FiscalPeriod
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore # For mocking app_core
import logging

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
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
    app_core.logger = MagicMock(spec=logging.Logger)
    # Mock other services if JournalService directly calls them via app_core
    # For now, assuming direct dependencies are passed or not used in tested methods
    return app_core

@pytest.fixture
def journal_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> JournalService:
    return JournalService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_account_orm() -> Account:
    return Account(id=101, code="1110", name="Bank", account_type="Asset", sub_type="Cash", is_active=True, created_by_user_id=1,updated_by_user_id=1)

@pytest.fixture
def sample_journal_entry_orm(sample_account_orm: Account) -> JournalEntry:
    je = JournalEntry(
        id=1, entry_no="JE001", journal_type="General", entry_date=date(2023,1,10),
        fiscal_period_id=1, description="Test JE", is_posted=False,
        created_by_user_id=1, updated_by_user_id=1
    )
    je.lines = [
        JournalEntryLine(id=1, journal_entry_id=1, line_number=1, account_id=sample_account_orm.id, debit_amount=Decimal("100.00"), credit_amount=Decimal("0.00"), account=sample_account_orm),
        JournalEntryLine(id=2, journal_entry_id=1, line_number=2, account_id=201, credit_amount=Decimal("100.00"), debit_amount=Decimal("0.00")) # Assume account 201 exists
    ]
    return je

@pytest.fixture
def sample_recurring_pattern_orm(sample_journal_entry_orm: JournalEntry) -> RecurringPattern:
    return RecurringPattern(
        id=1, name="Monthly Rent", template_entry_id=sample_journal_entry_orm.id,
        frequency="Monthly", interval_value=1, start_date=date(2023,1,1),
        next_generation_date=date(2023,2,1), is_active=True,
        created_by_user_id=1, updated_by_user_id=1,
        template_journal_entry=sample_journal_entry_orm # Link template JE
    )

# --- Test Cases ---

async def test_get_je_by_id_found(journal_service: JournalService, mock_session: AsyncMock, sample_journal_entry_orm: JournalEntry):
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_journal_entry_orm
    result = await journal_service.get_by_id(1)
    assert result == sample_journal_entry_orm
    assert result.entry_no == "JE001"

async def test_get_all_summary_no_filters(journal_service: JournalService, mock_session: AsyncMock, sample_journal_entry_orm: JournalEntry):
    mock_row_mapping = MagicMock()
    mock_row_mapping._asdict.return_value = { # Simulate RowMapping._asdict() if needed, or direct dict
        "id": sample_journal_entry_orm.id, "entry_no": sample_journal_entry_orm.entry_no,
        "entry_date": sample_journal_entry_orm.entry_date, "description": sample_journal_entry_orm.description,
        "journal_type": sample_journal_entry_orm.journal_type, "is_posted": sample_journal_entry_orm.is_posted,
        "total_debits": Decimal("100.00")
    }
    mock_session.execute.return_value.mappings.return_value.all.return_value = [mock_row_mapping]

    summaries = await journal_service.get_all_summary()
    assert len(summaries) == 1
    assert summaries[0]["entry_no"] == "JE001"
    assert summaries[0]["status"] == "Draft"

async def test_save_new_journal_entry(journal_service: JournalService, mock_session: AsyncMock, sample_account_orm: Account):
    new_je = JournalEntry(
        journal_type="General", entry_date=date(2023,2,5), fiscal_period_id=2,
        description="New test JE", created_by_user_id=1, updated_by_user_id=1
    )
    new_je.lines = [
        JournalEntryLine(account_id=sample_account_orm.id, debit_amount=Decimal("50.00"))
    ]
    async def mock_refresh(obj, attribute_names=None):
        obj.id = 2
        obj.entry_no = "JE002" # Simulate sequence
        if attribute_names and 'lines' in attribute_names:
            for line in obj.lines: line.id = line.id or (len(obj.lines) + 100) # Simulate line ID
    mock_session.refresh.side_effect = mock_refresh
    
    result = await journal_service.save(new_je)
    mock_session.add.assert_called_once_with(new_je)
    assert result.id == 2
    assert result.entry_no == "JE002"

async def test_delete_draft_je(journal_service: JournalService, mock_session: AsyncMock, sample_journal_entry_orm: JournalEntry):
    sample_journal_entry_orm.is_posted = False # Ensure draft
    mock_session.get.return_value = sample_journal_entry_orm
    
    deleted = await journal_service.delete(1)
    assert deleted is True
    mock_session.delete.assert_awaited_once_with(sample_journal_entry_orm)

async def test_delete_posted_je_fails(journal_service: JournalService, mock_session: AsyncMock, mock_app_core: MagicMock, sample_journal_entry_orm: JournalEntry):
    sample_journal_entry_orm.is_posted = True # Posted
    mock_session.get.return_value = sample_journal_entry_orm
    
    deleted = await journal_service.delete(1)
    assert deleted is False
    mock_session.delete.assert_not_called()
    mock_app_core.logger.warning.assert_called_once()

async def test_get_account_balance(journal_service: JournalService, mock_session: AsyncMock, sample_account_orm: Account):
    sample_account_orm.opening_balance = Decimal("100.00")
    sample_account_orm.opening_balance_date = date(2023,1,1)
    mock_session.execute.return_value.first.return_value = (sample_account_orm.opening_balance, sample_account_orm.opening_balance_date) # For the account fetch
    
    # For the JE activity sum
    mock_je_sum_result = AsyncMock()
    mock_je_sum_result.scalar_one_or_none.return_value = Decimal("50.00") # Net debit activity
    mock_session.execute.side_effect = [mock_session.execute.return_value, mock_je_sum_result] # First for account, second for sum

    balance = await journal_service.get_account_balance(sample_account_orm.id, date(2023,1,31))
    assert balance == Decimal("150.00") # 100 OB + 50 Activity

async def test_get_recurring_patterns_due(journal_service: JournalService, mock_session: AsyncMock, sample_recurring_pattern_orm: RecurringPattern):
    mock_session.execute.return_value.scalars.return_value.unique.return_value.all.return_value = [sample_recurring_pattern_orm]
    
    patterns = await journal_service.get_recurring_patterns_due(date(2023,2,1))
    assert len(patterns) == 1
    assert patterns[0].name == "Monthly Rent"

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

# tests/unit/services/test_tax_code_service.py
```py
# File: tests/unit/services/test_tax_code_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from decimal import Decimal
import datetime

from app.services.tax_service import TaxCodeService
from app.models.accounting.tax_code import TaxCode as TaxCodeModel
from app.models.core.user import User as UserModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock(); session.get = AsyncMock(); session.execute = AsyncMock()
    session.add = MagicMock(); session.delete = MagicMock(); session.flush = AsyncMock()
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
    user = MagicMock(spec=UserModel); user.id = 1; return user

@pytest.fixture
def mock_app_core(mock_user: MagicMock) -> MagicMock:
    app_core = MagicMock(spec=ApplicationCore); app_core.logger = MagicMock(spec=logging.Logger)
    app_core.current_user = mock_user # For audit fields in save
    return app_core

@pytest.fixture
def tax_code_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> TaxCodeService:
    return TaxCodeService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_tax_code_sr() -> TaxCodeModel:
    return TaxCodeModel(id=1, code="SR", description="Standard Rate", tax_type="GST", rate=Decimal("9.00"), is_active=True, created_by_user_id=1, updated_by_user_id=1)

@pytest.fixture
def sample_tax_code_zr_inactive() -> TaxCodeModel:
    return TaxCodeModel(id=2, code="ZR", description="Zero Rate", tax_type="GST", rate=Decimal("0.00"), is_active=False, created_by_user_id=1, updated_by_user_id=1)

async def test_get_tax_code_by_id_found(tax_code_service: TaxCodeService, mock_session: AsyncMock, sample_tax_code_sr: TaxCodeModel):
    mock_session.get.return_value = sample_tax_code_sr
    result = await tax_code_service.get_by_id(1)
    assert result == sample_tax_code_sr

async def test_get_tax_code_by_code_active_found(tax_code_service: TaxCodeService, mock_session: AsyncMock, sample_tax_code_sr: TaxCodeModel):
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_tax_code_sr
    result = await tax_code_service.get_tax_code("SR")
    assert result == sample_tax_code_sr

async def test_get_tax_code_by_code_inactive_returns_none(tax_code_service: TaxCodeService, mock_session: AsyncMock, sample_tax_code_zr_inactive: TaxCodeModel):
    # get_tax_code filters for is_active=True
    mock_session.execute.return_value.scalars.return_value.first.return_value = None 
    result = await tax_code_service.get_tax_code("ZR") # Even if ZR exists but is inactive
    assert result is None

async def test_get_all_active_tax_codes(tax_code_service: TaxCodeService, mock_session: AsyncMock, sample_tax_code_sr: TaxCodeModel):
    mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_tax_code_sr]
    results = await tax_code_service.get_all() # get_all in service implies active_only
    assert len(results) == 1
    assert results[0].code == "SR"

async def test_save_new_tax_code(tax_code_service: TaxCodeService, mock_session: AsyncMock, mock_user: MagicMock):
    new_tc = TaxCodeModel(code="EX", description="Exempt", tax_type="GST", rate=Decimal("0.00"))
    # Audit fields (created_by_user_id, updated_by_user_id) are set by service.save()

    async def mock_refresh(obj, attr=None): obj.id=3 # Simulate DB generated ID
    mock_session.refresh.side_effect = mock_refresh
    
    result = await tax_code_service.save(new_tc)
    assert result.id == 3
    assert result.created_by_user_id == mock_user.id
    assert result.updated_by_user_id == mock_user.id
    mock_session.add.assert_called_once_with(new_tc)

async def test_delete_tax_code_deactivates(tax_code_service: TaxCodeService, mock_session: AsyncMock, sample_tax_code_sr: TaxCodeModel):
    sample_tax_code_sr.is_active = True
    mock_session.get.return_value = sample_tax_code_sr
    tax_code_service.save = AsyncMock(return_value=sample_tax_code_sr) # Mock save as it's called by delete

    deleted_flag = await tax_code_service.delete(1)
    assert deleted_flag is True
    assert sample_tax_code_sr.is_active is False
    tax_code_service.save.assert_awaited_once_with(sample_tax_code_sr)

```

# tests/unit/services/test_purchase_invoice_service.py
```py
# File: tests/unit/services/test_purchase_invoice_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime

from app.services.business_services import PurchaseInvoiceService
from app.models.business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine
from app.models.business.vendor import Vendor
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import PurchaseInvoiceSummaryData
from app.common.enums import InvoiceStatusEnum
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock() # For delete test
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
    app_core.logger = MagicMock(spec=logging.Logger)
    return app_core

@pytest.fixture
def purchase_invoice_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> PurchaseInvoiceService:
    return PurchaseInvoiceService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_vendor_orm() -> Vendor:
    return Vendor(id=1, vendor_code="VEN001", name="Test Vendor", created_by_user_id=1, updated_by_user_id=1)

@pytest.fixture
def sample_purchase_invoice_orm(sample_vendor_orm: Vendor) -> PurchaseInvoice:
    return PurchaseInvoice(
        id=1, invoice_no="PI001", vendor_id=sample_vendor_orm.id, vendor=sample_vendor_orm,
        vendor_invoice_no="VINV001", invoice_date=date(2023, 1, 10), due_date=date(2023, 2, 10),
        currency_code="SGD", total_amount=Decimal("55.00"), amount_paid=Decimal("0.00"),
        status=InvoiceStatusEnum.DRAFT.value, created_by_user_id=1, updated_by_user_id=1,
        lines=[
            PurchaseInvoiceLine(id=1, invoice_id=1, description="Material X", quantity=Decimal(5), unit_price=Decimal(10), line_total=Decimal(55), tax_amount=Decimal(5))
        ]
    )

# --- Test Cases ---
async def test_get_pi_by_id_found(purchase_invoice_service: PurchaseInvoiceService, mock_session: AsyncMock, sample_purchase_invoice_orm: PurchaseInvoice):
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_purchase_invoice_orm
    result = await purchase_invoice_service.get_by_id(1)
    assert result == sample_purchase_invoice_orm
    mock_session.execute.assert_awaited_once()

async def test_get_all_pi_summary(purchase_invoice_service: PurchaseInvoiceService, mock_session: AsyncMock, sample_purchase_invoice_orm: PurchaseInvoice):
    mock_row = MagicMock()
    mock_row._asdict.return_value = {
        "id": sample_purchase_invoice_orm.id,
        "invoice_no": sample_purchase_invoice_orm.invoice_no,
        "vendor_invoice_no": sample_purchase_invoice_orm.vendor_invoice_no,
        "invoice_date": sample_purchase_invoice_orm.invoice_date,
        "vendor_name": sample_purchase_invoice_orm.vendor.name,
        "total_amount": sample_purchase_invoice_orm.total_amount,
        "status": sample_purchase_invoice_orm.status,
        "currency_code": sample_purchase_invoice_orm.currency_code,
    }
    mock_session.execute.return_value.mappings.return_value.all.return_value = [mock_row]
    
    result_dtos = await purchase_invoice_service.get_all_summary()
    assert len(result_dtos) == 1
    assert isinstance(result_dtos[0], PurchaseInvoiceSummaryData)
    assert result_dtos[0].invoice_no == "PI001"

async def test_save_new_pi(purchase_invoice_service: PurchaseInvoiceService, mock_session: AsyncMock, sample_vendor_orm: Vendor):
    new_pi = PurchaseInvoice(
        vendor_id=sample_vendor_orm.id, vendor_invoice_no="VINV002", invoice_date=date(2023, 4, 1), 
        due_date=date(2023, 4, 30), currency_code="SGD", total_amount=Decimal("300.00"), 
        status=InvoiceStatusEnum.DRAFT.value, created_by_user_id=1, updated_by_user_id=1
    )
    async def mock_refresh(obj, attribute_names=None):
        obj.id = 20 # Simulate ID
        obj.invoice_no = "PI002" # Simulate internal ref no
    mock_session.refresh.side_effect = mock_refresh

    result = await purchase_invoice_service.save(new_pi)
    mock_session.add.assert_called_once_with(new_pi)
    assert result.id == 20
    assert result.invoice_no == "PI002"

async def test_delete_draft_pi_success(purchase_invoice_service: PurchaseInvoiceService, mock_session: AsyncMock, sample_purchase_invoice_orm: PurchaseInvoice):
    sample_purchase_invoice_orm.status = InvoiceStatusEnum.DRAFT.value # Ensure it's draft
    mock_session.get.return_value = sample_purchase_invoice_orm
    
    result = await purchase_invoice_service.delete(1)
    assert result is True
    mock_session.get.assert_awaited_once_with(PurchaseInvoice, 1)
    mock_session.delete.assert_awaited_once_with(sample_purchase_invoice_orm)

async def test_delete_non_draft_pi_fails(purchase_invoice_service: PurchaseInvoiceService, mock_session: AsyncMock, sample_purchase_invoice_orm: PurchaseInvoice):
    sample_purchase_invoice_orm.status = InvoiceStatusEnum.APPROVED.value # Not draft
    mock_session.get.return_value = sample_purchase_invoice_orm
    
    with pytest.raises(ValueError) as excinfo:
        await purchase_invoice_service.delete(1)
    assert "Only Draft invoices can be deleted" in str(excinfo.value)
    mock_session.delete.assert_not_called()

async def test_get_outstanding_invoices_for_vendor(
    purchase_invoice_service: PurchaseInvoiceService, mock_session: AsyncMock, sample_purchase_invoice_orm: PurchaseInvoice
):
    sample_purchase_invoice_orm.status = InvoiceStatusEnum.APPROVED.value
    sample_purchase_invoice_orm.amount_paid = Decimal("20.00")
    sample_purchase_invoice_orm.total_amount = Decimal("55.00")
    sample_purchase_invoice_orm.invoice_date = date(2023, 1, 1)
    
    mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_purchase_invoice_orm]
    
    as_of = date(2023, 2, 1)
    results = await purchase_invoice_service.get_outstanding_invoices_for_vendor(vendor_id=1, as_of_date=as_of)

    assert len(results) == 1
    assert results[0].id == sample_purchase_invoice_orm.id

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

# tests/unit/services/test_vendor_service_dashboard_ext.py
```py
# File: tests/unit/services/test_vendor_service_dashboard_ext.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List
from decimal import Decimal
from datetime import date, timedelta

from app.services.business_services import VendorService
from app.models.business.purchase_invoice import PurchaseInvoice
from app.common.enums import InvoiceStatusEnum
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock()
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
    app_core.logger = MagicMock(spec=logging.Logger)
    return app_core

@pytest.fixture
def vendor_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> VendorService:
    return VendorService(db_manager=mock_db_manager, app_core=mock_app_core)

def create_mock_purchase_invoice(id: int, due_date: date, total_amount: Decimal, amount_paid: Decimal, status: InvoiceStatusEnum) -> MagicMock:
    inv = MagicMock(spec=PurchaseInvoice)
    inv.id = id
    inv.due_date = due_date
    inv.total_amount = total_amount
    inv.amount_paid = amount_paid
    inv.status = status.value
    inv.invoice_date = due_date - timedelta(days=30)
    return inv

async def test_get_ap_aging_summary_no_invoices(vendor_service: VendorService, mock_session: AsyncMock):
    mock_session.execute.return_value.scalars.return_value.all.return_value = []
    today = date(2023, 10, 15)
    summary = await vendor_service.get_ap_aging_summary(as_of_date=today)
    expected = {"Current": Decimal(0), "1-30 Days": Decimal(0), "31-60 Days": Decimal(0), "61-90 Days": Decimal(0), "91+ Days": Decimal(0)}
    assert summary == expected

async def test_get_ap_aging_summary_various_scenarios(vendor_service: VendorService, mock_session: AsyncMock):
    today = date(2023, 10, 15)
    mock_invoices = [
        create_mock_purchase_invoice(1, today, Decimal("1000"), Decimal("0"), InvoiceStatusEnum.APPROVED),
        create_mock_purchase_invoice(2, today - timedelta(days=15), Decimal("500"), Decimal("100"), InvoiceStatusEnum.PARTIALLY_PAID), # 400 in 1-30
        create_mock_purchase_invoice(3, today - timedelta(days=45), Decimal("750"), Decimal("0"), InvoiceStatusEnum.OVERDUE), # 750 in 31-60
        create_mock_purchase_invoice(4, today - timedelta(days=75), Decimal("200"), Decimal("0"), InvoiceStatusEnum.OVERDUE), # 200 in 61-90
        create_mock_purchase_invoice(5, today - timedelta(days=100), Decimal("300"), Decimal("0"), InvoiceStatusEnum.OVERDUE),# 300 in 91+
        create_mock_purchase_invoice(6, today + timedelta(days=5), Decimal("600"), Decimal("0"), InvoiceStatusEnum.APPROVED), # 600 in Current
    ]
    mock_session.execute.return_value.scalars.return_value.all.return_value = mock_invoices
    
    summary = await vendor_service.get_ap_aging_summary(as_of_date=today)
    
    assert summary["Current"] == Decimal("1600.00") # 1000 + 600
    assert summary["1-30 Days"] == Decimal("400.00")
    assert summary["31-60 Days"] == Decimal("750.00")
    assert summary["61-90 Days"] == Decimal("200.00")
    assert summary["91+ Days"] == Decimal("300.00")

```

# tests/unit/services/__init__.py
```py
# File: tests/unit/services/__init__.py
# This file makes 'services' (under 'unit') a Python package.

```

# tests/unit/services/test_audit_log_service.py
```py
# File: tests/unit/services/test_audit_log_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal 

from app.services.audit_services import AuditLogService
from app.models.audit.audit_log import AuditLog as AuditLogModel
from app.models.audit.data_change_history import DataChangeHistory as DataChangeHistoryModel
from app.models.core.user import User as UserModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore 
from app.utils.pydantic_models import AuditLogEntryData, DataChangeHistoryEntryData
from app.common.enums import DataChangeTypeEnum
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock()
    session.get = AsyncMock() 
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
    app_core.logger = MagicMock(spec=logging.Logger)
    return app_core

@pytest.fixture
def audit_log_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> AuditLogService:
    return AuditLogService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_user_orm() -> UserModel:
    return UserModel(id=1, username="test_user", full_name="Test User FullName", password_hash="hashed", is_active=True)

@pytest.fixture
def sample_audit_log_orm_create(sample_user_orm: UserModel) -> AuditLogModel:
    return AuditLogModel(
        id=1, user_id=sample_user_orm.id, action="Insert", entity_type="core.customer",
        entity_id=101, entity_name="Customer Alpha", 
        changes={"new": {"name": "Customer Alpha", "credit_limit": "1000.00", "is_active": True}},
        ip_address="127.0.0.1", timestamp=datetime(2023, 1, 1, 10, 0, 0)
    )

@pytest.fixture
def sample_audit_log_orm_update(sample_user_orm: UserModel) -> AuditLogModel:
    return AuditLogModel(
        id=2, user_id=sample_user_orm.id, action="Update", entity_type="core.customer",
        entity_id=101, entity_name="Customer Alpha V2", 
        changes={"old": {"name": "Customer Alpha", "credit_limit": "1000.00"}, "new": {"name": "Customer Alpha V2", "credit_limit": "1500.00"}},
        ip_address="127.0.0.1", timestamp=datetime(2023, 1, 1, 10, 5, 0)
    )

@pytest.fixture
def sample_audit_log_orm_delete(sample_user_orm: UserModel) -> AuditLogModel:
    return AuditLogModel(
        id=3, user_id=sample_user_orm.id, action="Delete", entity_type="core.customer",
        entity_id=102, entity_name="Customer Beta", 
        changes={"old": {"name": "Customer Beta"}},
        ip_address="127.0.0.1", timestamp=datetime(2023, 1, 1, 10, 10, 0)
    )
    
@pytest.fixture
def sample_data_change_history_orm(sample_user_orm: UserModel) -> DataChangeHistoryModel:
    return DataChangeHistoryModel(
        id=1, table_name="core.customer", record_id=101, field_name="credit_limit",
        old_value="500.00", new_value="1000.00", change_type=DataChangeTypeEnum.UPDATE.value,
        changed_by=sample_user_orm.id, changed_at=datetime(2023,1,1,10,0,0)
    )

# --- Tests for AuditLogService ---

async def test_get_audit_logs_paginated_no_filters(
    audit_log_service: AuditLogService, 
    mock_session: AsyncMock, 
    sample_audit_log_orm_create: AuditLogModel, 
    sample_user_orm: UserModel
):
    mock_count_execute = AsyncMock(); mock_count_execute.scalar_one.return_value = 1
    mock_data_execute = AsyncMock()
    mock_data_execute.mappings.return_value.all.return_value = [
        {AuditLogModel: sample_audit_log_orm_create, "username": sample_user_orm.username}
    ]
    mock_session.execute.side_effect = [mock_count_execute, mock_data_execute]

    logs, total_records = await audit_log_service.get_audit_logs_paginated(page=1, page_size=10)

    assert total_records == 1
    assert len(logs) == 1
    assert isinstance(logs[0], AuditLogEntryData)
    assert logs[0].id == sample_audit_log_orm_create.id
    assert logs[0].username == sample_user_orm.username
    assert "Record Created." in (logs[0].changes_summary or "")
    assert "name: 'Customer Alpha'" in (logs[0].changes_summary or "")
    assert "credit_limit: '1000.00'" in (logs[0].changes_summary or "")
    assert mock_session.execute.await_count == 2

async def test_get_audit_logs_paginated_with_user_filter(
    audit_log_service: AuditLogService, mock_session: AsyncMock
):
    await audit_log_service.get_audit_logs_paginated(user_id_filter=1)
    assert mock_session.execute.await_count == 2 

def test_format_changes_summary_created(audit_log_service: AuditLogService):
    changes = {"new": {"name": "Item X", "code": "X001", "price": "10.99"}}
    summary = audit_log_service._format_changes_summary(changes)
    assert summary == "Record Created. Details: name: 'Item X', code: 'X001', price: '10.99'"

def test_format_changes_summary_deleted(audit_log_service: AuditLogService):
    changes = {"old": {"name": "Item Y", "code": "Y001"}}
    summary = audit_log_service._format_changes_summary(changes)
    assert summary == "Record Deleted."

def test_format_changes_summary_modified_few(audit_log_service: AuditLogService):
    changes = {"old": {"status": "Active", "notes": "Old note"}, "new": {"status": "Inactive", "notes": "Old note"}}
    summary = audit_log_service._format_changes_summary(changes)
    assert summary == "'status': 'Active' -> 'Inactive'"

def test_format_changes_summary_modified_many(audit_log_service: AuditLogService):
    changes = {
        "old": {"f1": "a", "f2": "b", "f3": "c", "f4": "d", "f5": "e"},
        "new": {"f1": "A", "f2": "B", "f3": "C", "f4": "D", "f5": "E"}
    }
    summary = audit_log_service._format_changes_summary(changes)
    assert "'f1': 'a' -> 'A'; 'f2': 'b' -> 'B'; 'f3': 'c' -> 'C'; ...and 2 other field(s)." == summary

def test_format_changes_summary_no_meaningful_change(audit_log_service: AuditLogService):
    changes = {"old": {"updated_at": "ts1"}, "new": {"updated_at": "ts2"}} 
    summary = audit_log_service._format_changes_summary(changes)
    assert "updated_at" in summary # Current impl shows this

def test_format_changes_summary_no_diff_fields(audit_log_service: AuditLogService):
    changes = {"old": {"field": "value"}, "new": {"field": "value"}}
    summary = audit_log_service._format_changes_summary(changes)
    assert summary == "No changes detailed or only sensitive fields updated."


def test_format_changes_summary_none(audit_log_service: AuditLogService):
    summary = audit_log_service._format_changes_summary(None)
    assert summary is None

async def test_get_data_change_history_paginated(
    audit_log_service: AuditLogService, mock_session: AsyncMock, 
    sample_data_change_history_orm: DataChangeHistoryModel, sample_user_orm: UserModel
):
    mock_count_execute = AsyncMock(); mock_count_execute.scalar_one.return_value = 1
    mock_data_execute = AsyncMock()
    mock_data_execute.mappings.return_value.all.return_value = [
        {DataChangeHistoryModel: sample_data_change_history_orm, "changed_by_username": sample_user_orm.username}
    ]
    mock_session.execute.side_effect = [mock_count_execute, mock_data_execute]

    history, total_records = await audit_log_service.get_data_change_history_paginated()
    assert total_records == 1
    assert len(history) == 1
    assert history[0].field_name == "credit_limit"
    assert history[0].change_type == DataChangeTypeEnum.UPDATE
    assert history[0].changed_by_username == sample_user_orm.username

async def test_audit_log_service_unsupported_methods(audit_log_service: AuditLogService):
    """Test that add, update, delete methods for AuditLog/DataChangeHistory raise NotImplementedError."""
    with pytest.raises(NotImplementedError):
        await audit_log_service.add(MagicMock(spec=AuditLogModel))
    with pytest.raises(NotImplementedError):
        await audit_log_service.update(MagicMock(spec=AuditLogModel))
    with pytest.raises(NotImplementedError):
        await audit_log_service.delete(1) # Argument is id_val: int
    with pytest.raises(NotImplementedError):
        await audit_log_service.get_all()
    
    # Check get_by_id - it has a minimal implementation for completeness
    mock_session = audit_log_service.db_manager.session.return_value.__aenter__.return_value
    mock_session.get.side_effect = [None, None] # Return None for both AuditLog and DataChangeHistory get
    result = await audit_log_service.get_by_id(123)
    assert result is None
    assert mock_session.get.await_count == 2
    mock_session.get.assert_any_await(AuditLogModel, 123)
    mock_session.get.assert_any_await(DataChangeHistoryModel, 123)

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

# tests/unit/services/test_bank_transaction_service.py
```py
# File: tests/unit/services/test_bank_transaction_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime
import logging

from app.services.business_services import BankTransactionService
from app.models.business.bank_transaction import BankTransaction as BankTransactionModel
from app.models.business.bank_account import BankAccount as BankAccountModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import BankTransactionSummaryData
from app.common.enums import BankTransactionTypeEnum

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
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
    app_core.logger = MagicMock(spec=logging.Logger)
    return app_core

@pytest.fixture
def bank_transaction_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> BankTransactionService:
    return BankTransactionService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_bank_transaction_orm() -> BankTransactionModel:
    return BankTransactionModel(
        id=1, bank_account_id=1, transaction_date=date(2023,1,5),
        transaction_type=BankTransactionTypeEnum.DEPOSIT.value,
        description="Cash Deposit", amount=Decimal("500.00"),
        is_reconciled=False, created_by_user_id=1, updated_by_user_id=1
    )

async def test_get_bank_transaction_by_id_found(bank_transaction_service: BankTransactionService, mock_session: AsyncMock, sample_bank_transaction_orm: BankTransactionModel):
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_bank_transaction_orm
    result = await bank_transaction_service.get_by_id(1)
    assert result == sample_bank_transaction_orm

async def test_get_all_for_bank_account(bank_transaction_service: BankTransactionService, mock_session: AsyncMock, sample_bank_transaction_orm: BankTransactionModel):
    mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_bank_transaction_orm]
    
    summaries = await bank_transaction_service.get_all_for_bank_account(bank_account_id=1)
    assert len(summaries) == 1
    assert isinstance(summaries[0], BankTransactionSummaryData)
    assert summaries[0].description == "Cash Deposit"

async def test_save_new_bank_transaction(bank_transaction_service: BankTransactionService, mock_session: AsyncMock):
    new_txn = BankTransactionModel(
        bank_account_id=1, transaction_date=date(2023,2,1), 
        transaction_type=BankTransactionTypeEnum.WITHDRAWAL.value,
        description="ATM Withdrawal", amount=Decimal("-100.00"),
        created_by_user_id=1, updated_by_user_id=1
    )
    async def mock_refresh(obj, attr=None): obj.id = 2
    mock_session.refresh.side_effect = mock_refresh
    
    result = await bank_transaction_service.save(new_txn)
    mock_session.add.assert_called_once_with(new_txn)
    assert result.id == 2

async def test_delete_unreconciled_transaction(bank_transaction_service: BankTransactionService, mock_session: AsyncMock, sample_bank_transaction_orm: BankTransactionModel):
    sample_bank_transaction_orm.is_reconciled = False
    mock_session.get.return_value = sample_bank_transaction_orm
    
    deleted = await bank_transaction_service.delete(1)
    assert deleted is True
    mock_session.delete.assert_awaited_once_with(sample_bank_transaction_orm)

async def test_delete_reconciled_transaction_fails(bank_transaction_service: BankTransactionService, mock_session: AsyncMock, sample_bank_transaction_orm: BankTransactionModel):
    sample_bank_transaction_orm.is_reconciled = True
    mock_session.get.return_value = sample_bank_transaction_orm
    
    deleted = await bank_transaction_service.delete(1)
    assert deleted is False
    mock_session.delete.assert_not_called()
    bank_transaction_service.logger.warning.assert_called_once()

```

# tests/unit/services/test_customer_service_dashboard_ext.py
```py
# File: tests/unit/services/test_customer_service_dashboard_ext.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List
from decimal import Decimal
from datetime import date, timedelta

from app.services.business_services import CustomerService
from app.models.business.sales_invoice import SalesInvoice
from app.common.enums import InvoiceStatusEnum
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock()
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
    app_core.logger = MagicMock(spec=logging.Logger)
    return app_core
    
@pytest.fixture
def customer_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> CustomerService:
    return CustomerService(db_manager=mock_db_manager, app_core=mock_app_core)

def create_mock_sales_invoice(id: int, due_date: date, total_amount: Decimal, amount_paid: Decimal, status: InvoiceStatusEnum) -> MagicMock:
    inv = MagicMock(spec=SalesInvoice)
    inv.id = id
    inv.due_date = due_date
    inv.total_amount = total_amount
    inv.amount_paid = amount_paid
    inv.status = status.value
    inv.invoice_date = due_date - timedelta(days=30) # Assume invoice date is 30 days before due date
    return inv

async def test_get_ar_aging_summary_no_invoices(customer_service: CustomerService, mock_session: AsyncMock):
    mock_session.execute.return_value.scalars.return_value.all.return_value = []
    today = date(2023, 10, 15)
    summary = await customer_service.get_ar_aging_summary(as_of_date=today)
    expected = {"Current": Decimal(0), "1-30 Days": Decimal(0), "31-60 Days": Decimal(0), "61-90 Days": Decimal(0), "91+ Days": Decimal(0)}
    assert summary == expected

async def test_get_ar_aging_summary_various_scenarios(customer_service: CustomerService, mock_session: AsyncMock):
    today = date(2023, 10, 15)
    mock_invoices = [
        # Current (due today or future)
        create_mock_sales_invoice(1, today, Decimal("100"), Decimal("0"), InvoiceStatusEnum.APPROVED),
        create_mock_sales_invoice(2, today + timedelta(days=10), Decimal("50"), Decimal("0"), InvoiceStatusEnum.APPROVED),
        # 1-30 Days Overdue
        create_mock_sales_invoice(3, today - timedelta(days=1), Decimal("200"), Decimal("0"), InvoiceStatusEnum.OVERDUE),
        create_mock_sales_invoice(4, today - timedelta(days=30), Decimal("150"), Decimal("50"), InvoiceStatusEnum.PARTIALLY_PAID), # Outstanding 100
        # 31-60 Days Overdue
        create_mock_sales_invoice(5, today - timedelta(days=31), Decimal("300"), Decimal("0"), InvoiceStatusEnum.OVERDUE),
        create_mock_sales_invoice(6, today - timedelta(days=60), Decimal("250"), Decimal("0"), InvoiceStatusEnum.OVERDUE),
        # 61-90 Days Overdue
        create_mock_sales_invoice(7, today - timedelta(days=61), Decimal("400"), Decimal("100"), InvoiceStatusEnum.PARTIALLY_PAID), # Outstanding 300
        create_mock_sales_invoice(8, today - timedelta(days=90), Decimal("350"), Decimal("0"), InvoiceStatusEnum.OVERDUE),
        # 91+ Days Overdue
        create_mock_sales_invoice(9, today - timedelta(days=91), Decimal("500"), Decimal("0"), InvoiceStatusEnum.OVERDUE),
        create_mock_sales_invoice(10, today - timedelta(days=120), Decimal("450"), Decimal("0"), InvoiceStatusEnum.OVERDUE),
        # Paid / Voided (should be ignored)
        create_mock_sales_invoice(11, today - timedelta(days=5), Decimal("50"), Decimal("50"), InvoiceStatusEnum.PAID),
        create_mock_sales_invoice(12, today - timedelta(days=5), Decimal("60"), Decimal("0"), InvoiceStatusEnum.VOIDED),
    ]
    mock_session.execute.return_value.scalars.return_value.all.return_value = mock_invoices
    
    summary = await customer_service.get_ar_aging_summary(as_of_date=today)
    
    assert summary["Current"] == Decimal("150.00") # 100 + 50
    assert summary["1-30 Days"] == Decimal("300.00") # 200 + 100
    assert summary["31-60 Days"] == Decimal("550.00") # 300 + 250
    assert summary["61-90 Days"] == Decimal("650.00") # 300 + 350
    assert summary["91+ Days"] == Decimal("950.00") # 500 + 450

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

# tests/unit/services/test_account_service_dashboard_ext.py
```py
# File: tests/unit/services/test_account_service_dashboard_ext.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List
from decimal import Decimal
from datetime import date

from app.services.account_service import AccountService
from app.models.accounting.account import Account as AccountModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.services.journal_service import JournalService # For mocking
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock()
    return session

@pytest.fixture
def mock_db_manager(mock_session: AsyncMock) -> MagicMock:
    db_manager = MagicMock(spec=DatabaseManager)
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def mock_journal_service() -> AsyncMock:
    return AsyncMock(spec=JournalService)

@pytest.fixture
def mock_app_core(mock_journal_service: AsyncMock) -> MagicMock:
    app_core = MagicMock(spec=ApplicationCore)
    app_core.logger = MagicMock(spec=logging.Logger)
    app_core.journal_service = mock_journal_service # Inject mock journal_service
    return app_core

@pytest.fixture
def account_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> AccountService:
    return AccountService(db_manager=mock_db_manager, app_core=mock_app_core)

# Sample Accounts
@pytest.fixture
def current_asset_accounts() -> List[AccountModel]:
    return [
        AccountModel(id=1, code="1010", name="Cash", account_type="Asset", sub_type="Cash and Cash Equivalents", is_active=True, created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=2, code="1020", name="AR", account_type="Asset", sub_type="Accounts Receivable", is_active=True, created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=3, code="1030", name="Inventory", account_type="Asset", sub_type="Inventory", is_active=True, created_by_user_id=1,updated_by_user_id=1),
    ]

@pytest.fixture
def current_liability_accounts() -> List[AccountModel]:
    return [
        AccountModel(id=4, code="2010", name="AP", account_type="Liability", sub_type="Accounts Payable", is_active=True, created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=5, code="2020", name="GST Payable", account_type="Liability", sub_type="GST Payable", is_active=True, created_by_user_id=1,updated_by_user_id=1),
    ]

@pytest.fixture
def non_current_asset_account() -> AccountModel:
     return AccountModel(id=6, code="1500", name="Equipment", account_type="Asset", sub_type="Fixed Asset", is_active=True, created_by_user_id=1,updated_by_user_id=1)


async def test_get_total_balance_current_assets(
    account_service: AccountService, 
    mock_session: AsyncMock, 
    mock_journal_service: AsyncMock,
    current_asset_accounts: List[AccountModel]
):
    mock_session.execute.return_value.scalars.return_value.all.return_value = current_asset_accounts
    
    # Mock balances for these accounts
    def get_balance_side_effect(acc_id, as_of_date):
        if acc_id == 1: return Decimal("1000.00")
        if acc_id == 2: return Decimal("5000.00")
        if acc_id == 3: return Decimal("12000.00")
        return Decimal("0.00")
    mock_journal_service.get_account_balance.side_effect = get_balance_side_effect

    # Test for a specific subtype that matches one of the accounts
    total = await account_service.get_total_balance_by_account_category_and_type_pattern(
        account_category="Asset", 
        account_type_name_like="Cash and Cash Equivalents", # Exact match for first account's sub_type
        as_of_date=date.today()
    )
    assert total == Decimal("1000.00")

    # Test with a pattern matching multiple accounts
    # Reset side effect for a new call scenario
    mock_journal_service.get_account_balance.side_effect = get_balance_side_effect
    total_current = await account_service.get_total_balance_by_account_category_and_type_pattern(
        account_category="Asset",
        # Using a pattern that should ideally match multiple current asset subtypes based on your DashboardManager's lists
        # For this test, we assume these sub_types are fetched if they match "Current Asset%"
        # A more precise test might involve mocking specific `sub_type` names from `CURRENT_ASSET_SUBTYPES`
        account_type_name_like="Current Asset%", # Example, this might need adjustment based on actual CoA data
        as_of_date=date.today()
    )
    # This test depends on how broadly "Current Asset%" matches the sub_types in current_asset_accounts
    # If only AccountModel(sub_type="Current Asset") existed, the result would be based on that.
    # Given the current sample data, "Current Asset%" likely won't match any sub_type.
    # This test highlights the dependency on the `account_type_name_like` parameter and the data.
    # To make it robust, let's assume we are looking for "Cash and Cash Equivalents" and "Accounts Receivable"
    # This requires a more flexible `get_total_balance_by_sub_types` or multiple calls.
    
    # Let's test with actual subtypes from DashboardManager's CURRENT_ASSET_SUBTYPES logic
    # This test simulates how DashboardManager would sum up.
    
    # Mock setup for this specific scenario:
    # Accounts that match CURRENT_ASSET_SUBTYPES
    matching_accounts = [
        AccountModel(id=1, sub_type="Cash and Cash Equivalents", account_type="Asset", is_active=True, code="CASH", name="Cash", created_by_user_id=1, updated_by_user_id=1),
        AccountModel(id=2, sub_type="Accounts Receivable", account_type="Asset", is_active=True, code="AR", name="AR", created_by_user_id=1, updated_by_user_id=1),
        AccountModel(id=7, sub_type="Fixed Asset", account_type="Asset", is_active=True, code="FA", name="FA", created_by_user_id=1, updated_by_user_id=1) # Non-current
    ]
    mock_session.execute.return_value.scalars.return_value.all.return_value = matching_accounts
    
    def get_balance_for_current_asset_test(acc_id, as_of_date):
        if acc_id == 1: return Decimal("200") # Cash
        if acc_id == 2: return Decimal("300") # AR
        if acc_id == 7: return Decimal("1000") # FA
        return Decimal(0)
    mock_journal_service.get_account_balance.side_effect = get_balance_for_current_asset_test
    
    # Simulate DashboardManager's iteration and summation
    from app.reporting.dashboard_manager import CURRENT_ASSET_SUBTYPES # Import the list
    
    calculated_current_assets = Decimal(0)
    for acc_subtype in CURRENT_ASSET_SUBTYPES:
        # This relies on the `account_type_name_like` to be an exact match here
        # The actual AccountService method takes one pattern. 
        # To test the sum for dashboard, we need to call it for each subtype or adapt it.
        # Let's adapt the test to reflect how AccountService.get_total_balance_by_account_category_and_type_pattern
        # would be called for a single subtype from the list.
        
        # Test for one specific subtype from the list
        mock_session.execute.return_value.scalars.return_value.all.return_value = [matching_accounts[0]] # Only cash account
        mock_journal_service.get_account_balance.side_effect = lambda acc_id, dt: Decimal("200") if acc_id == 1 else Decimal(0)
        sum_for_cash_subtype = await account_service.get_total_balance_by_account_category_and_type_pattern(
            account_category="Asset",
            account_type_name_like="Cash and Cash Equivalents", # Exact subtype
            as_of_date=date.today()
        )
        assert sum_for_cash_subtype == Decimal("200.00")

        mock_session.execute.return_value.scalars.return_value.all.return_value = [matching_accounts[1]] # Only AR account
        mock_journal_service.get_account_balance.side_effect = lambda acc_id, dt: Decimal("300") if acc_id == 2 else Decimal(0)
        sum_for_ar_subtype = await account_service.get_total_balance_by_account_category_and_type_pattern(
            account_category="Asset",
            account_type_name_like="Accounts Receivable", # Exact subtype
            as_of_date=date.today()
        )
        assert sum_for_ar_subtype == Decimal("300.00")


async def test_get_total_balance_no_matching_accounts(
    account_service: AccountService, mock_session: AsyncMock, mock_journal_service: AsyncMock
):
    mock_session.execute.return_value.scalars.return_value.all.return_value = [] # No accounts match criteria
    
    total = await account_service.get_total_balance_by_account_category_and_type_pattern(
        account_category="Asset", 
        account_type_name_like="NonExistentSubType%", 
        as_of_date=date.today()
    )
    assert total == Decimal("0.00")
    mock_journal_service.get_account_balance.assert_not_called() # Should not be called if no accounts found

```

# tests/unit/services/test_bank_account_service.py
```py
# File: tests/unit/services/test_bank_account_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime
import logging

from app.services.business_services import BankAccountService
from app.models.business.bank_account import BankAccount as BankAccountModel
from app.models.accounting.account import Account as AccountModel
from app.models.accounting.currency import Currency as CurrencyModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import BankAccountSummaryData

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock() # For BankAccount, delete means deactivate
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
    app_core.logger = MagicMock(spec=logging.Logger)
    return app_core

@pytest.fixture
def bank_account_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> BankAccountService:
    return BankAccountService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_gl_account_orm() -> AccountModel:
    return AccountModel(id=101, code="1110", name="Bank GL", account_type="Asset", sub_type="Cash and Cash Equivalents", is_active=True, created_by_user_id=1, updated_by_user_id=1)

@pytest.fixture
def sample_currency_orm() -> CurrencyModel:
    return CurrencyModel(code="SGD", name="Singapore Dollar", symbol="$", is_active=True)

@pytest.fixture
def sample_bank_account_orm(sample_gl_account_orm: AccountModel, sample_currency_orm: CurrencyModel) -> BankAccountModel:
    return BankAccountModel(
        id=1, account_name="DBS Current", account_number="123-456-789", bank_name="DBS Bank",
        currency_code=sample_currency_orm.code, currency=sample_currency_orm,
        gl_account_id=sample_gl_account_orm.id, gl_account=sample_gl_account_orm,
        current_balance=Decimal("10000.00"), is_active=True,
        created_by_user_id=1, updated_by_user_id=1
    )

# --- Test Cases ---
async def test_get_bank_account_by_id_found(bank_account_service: BankAccountService, mock_session: AsyncMock, sample_bank_account_orm: BankAccountModel):
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_bank_account_orm
    result = await bank_account_service.get_by_id(1)
    assert result == sample_bank_account_orm
    assert result.account_name == "DBS Current"

async def test_get_all_bank_accounts(bank_account_service: BankAccountService, mock_session: AsyncMock, sample_bank_account_orm: BankAccountModel):
    mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_bank_account_orm]
    result = await bank_account_service.get_all()
    assert len(result) == 1
    assert result[0] == sample_bank_account_orm

async def test_get_all_summary_filters(bank_account_service: BankAccountService, mock_session: AsyncMock, sample_bank_account_orm: BankAccountModel):
    mock_row = MagicMock()
    mock_row._asdict.return_value = {
        "id": sample_bank_account_orm.id, "account_name": sample_bank_account_orm.account_name,
        "bank_name": sample_bank_account_orm.bank_name, "account_number": sample_bank_account_orm.account_number,
        "currency_code": sample_bank_account_orm.currency_code, "current_balance": sample_bank_account_orm.current_balance,
        "is_active": sample_bank_account_orm.is_active, 
        "gl_account_code": sample_bank_account_orm.gl_account.code, 
        "gl_account_name": sample_bank_account_orm.gl_account.name
    }
    mock_session.execute.return_value.mappings.return_value.all.return_value = [mock_row]
    
    summaries = await bank_account_service.get_all_summary(active_only=True, currency_code="SGD")
    assert len(summaries) == 1
    assert isinstance(summaries[0], BankAccountSummaryData)
    assert summaries[0].currency_code == "SGD"
    # Further assertions could check the SQL query string for filter application if mock_session.execute was more detailed

async def test_save_new_bank_account(bank_account_service: BankAccountService, mock_session: AsyncMock, sample_gl_account_orm: AccountModel):
    new_ba = BankAccountModel(
        account_name="OCBC Savings", account_number="987-654-321", bank_name="OCBC Bank",
        currency_code="SGD", gl_account_id=sample_gl_account_orm.id, current_balance=Decimal("500.00"),
        created_by_user_id=1, updated_by_user_id=1
    )
    async def mock_refresh(obj, attribute_names=None): obj.id = 2
    mock_session.refresh.side_effect = mock_refresh

    result = await bank_account_service.save(new_ba)
    mock_session.add.assert_called_once_with(new_ba)
    assert result.id == 2

async def test_delete_active_bank_account_deactivates(bank_account_service: BankAccountService, mock_session: AsyncMock, sample_bank_account_orm: BankAccountModel):
    sample_bank_account_orm.is_active = True
    mock_session.get.return_value = sample_bank_account_orm
    
    # Mock the save call within delete
    bank_account_service.save = AsyncMock(return_value=sample_bank_account_orm)

    deleted = await bank_account_service.delete(1)
    assert deleted is True
    assert sample_bank_account_orm.is_active is False
    bank_account_service.save.assert_awaited_once_with(sample_bank_account_orm)

async def test_get_by_gl_account_id_found(bank_account_service: BankAccountService, mock_session: AsyncMock, sample_bank_account_orm: BankAccountModel):
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_bank_account_orm
    result = await bank_account_service.get_by_gl_account_id(101) # sample_gl_account_orm.id
    assert result == sample_bank_account_orm
    mock_session.execute.assert_awaited_once()

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

# tests/unit/services/test_bank_reconciliation_service.py
```py
# File: tests/unit/services/test_bank_reconciliation_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, call # Import call for checking multiple calls
from typing import List, Optional, Tuple
from datetime import date, datetime
from decimal import Decimal
import logging # For logger spec

from sqlalchemy import select, update as sqlalchemy_update # For constructing expected statements

from app.services.business_services import BankReconciliationService
from app.models.business.bank_reconciliation import BankReconciliation as BankReconciliationModel
from app.models.business.bank_transaction import BankTransaction as BankTransactionModel
from app.models.business.bank_account import BankAccount as BankAccountModel
from app.models.core.user import User as UserModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import BankReconciliationSummaryData, BankTransactionSummaryData
from app.common.enums import BankTransactionTypeEnum


# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock() # Changed to AsyncMock for await session.delete(entity)
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
    app_core.logger = MagicMock(spec=logging.Logger)
    return app_core

@pytest.fixture
def reconciliation_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> BankReconciliationService:
    return BankReconciliationService(db_manager=mock_db_manager, app_core=mock_app_core)

# Sample Data
@pytest.fixture
def sample_bank_account() -> BankAccountModel:
    return BankAccountModel(id=1, account_name="Test Bank Account", gl_account_id=101, currency_code="SGD", created_by_user_id=1, updated_by_user_id=1)

@pytest.fixture
def sample_user() -> UserModel:
    return UserModel(id=1, username="testuser")

@pytest.fixture
def sample_reconciliation(sample_bank_account: BankAccountModel, sample_user: UserModel) -> BankReconciliationModel:
    return BankReconciliationModel(
        id=1,
        bank_account_id=sample_bank_account.id,
        statement_date=date(2023, 1, 31),
        statement_ending_balance=Decimal("1000.00"),
        calculated_book_balance=Decimal("1000.00"),
        reconciled_difference=Decimal("0.00"),
        reconciliation_date=datetime(2023, 2, 1, 10, 0, 0),
        created_by_user_id=sample_user.id
    )

@pytest.fixture
def sample_statement_txn(sample_bank_account: BankAccountModel, sample_user: UserModel) -> BankTransactionModel:
    return BankTransactionModel(
        id=10, bank_account_id=sample_bank_account.id, transaction_date=date(2023,1,15),
        amount=Decimal("100.00"), description="Statement Inflow", transaction_type=BankTransactionTypeEnum.DEPOSIT.value,
        is_from_statement=True, created_by_user_id=sample_user.id, updated_by_user_id=sample_user.id
    )

@pytest.fixture
def sample_system_txn(sample_bank_account: BankAccountModel, sample_user: UserModel) -> BankTransactionModel:
    return BankTransactionModel(
        id=20, bank_account_id=sample_bank_account.id, transaction_date=date(2023,1,16),
        amount=Decimal("-50.00"), description="System Outflow", transaction_type=BankTransactionTypeEnum.WITHDRAWAL.value,
        is_from_statement=False, created_by_user_id=sample_user.id, updated_by_user_id=sample_user.id
    )
    
# --- Test Cases ---

async def test_get_reconciliation_by_id_found(
    reconciliation_service: BankReconciliationService, 
    mock_session: AsyncMock, 
    sample_reconciliation: BankReconciliationModel
):
    mock_session.get.return_value = sample_reconciliation
    result = await reconciliation_service.get_by_id(1)
    assert result == sample_reconciliation
    mock_session.get.assert_awaited_once_with(BankReconciliationModel, 1)

async def test_get_reconciliations_for_account(
    reconciliation_service: BankReconciliationService, 
    mock_session: AsyncMock,
    sample_reconciliation: BankReconciliationModel,
    sample_user: UserModel
):
    # Mock for the count query
    mock_count_execute_result = AsyncMock()
    mock_count_execute_result.scalar_one_or_none.return_value = 1
    
    # Mock for the data query
    mock_data_execute_result = AsyncMock()
    # Simulate result from join: (BankReconciliation_instance, username_str)
    mock_data_execute_result.mappings.return_value.all.return_value = [
        {BankReconciliationModel: sample_reconciliation, "created_by_username": sample_user.username}
    ]
    mock_session.execute.side_effect = [mock_count_execute_result, mock_data_execute_result]

    summaries, total_records = await reconciliation_service.get_reconciliations_for_account(bank_account_id=1)
    
    assert total_records == 1
    assert len(summaries) == 1
    assert summaries[0].id == sample_reconciliation.id
    assert summaries[0].created_by_username == sample_user.username
    assert mock_session.execute.await_count == 2

async def test_get_transactions_for_reconciliation(
    reconciliation_service: BankReconciliationService, 
    mock_session: AsyncMock,
    sample_statement_txn: BankTransactionModel,
    sample_system_txn: BankTransactionModel
):
    mock_execute_result = AsyncMock()
    # Ensure the mocked transactions have reconciled_bank_reconciliation_id set as if they belong to a reconciliation
    sample_statement_txn.reconciled_bank_reconciliation_id = 1
    sample_system_txn.reconciled_bank_reconciliation_id = 1
    
    mock_execute_result.scalars.return_value.all.return_value = [sample_statement_txn, sample_system_txn]
    mock_session.execute.return_value = mock_execute_result

    stmt_txns, sys_txns = await reconciliation_service.get_transactions_for_reconciliation(reconciliation_id=1)
    
    assert len(stmt_txns) == 1
    assert stmt_txns[0].id == sample_statement_txn.id
    assert len(sys_txns) == 1
    assert sys_txns[0].id == sample_system_txn.id
    mock_session.execute.assert_awaited_once()

async def test_save_reconciliation_details(
    reconciliation_service: BankReconciliationService, 
    mock_session: AsyncMock,
    sample_reconciliation: BankReconciliationModel, # This will be the ORM object to save
    sample_bank_account: BankAccountModel
):
    statement_date = sample_reconciliation.statement_date
    bank_account_id = sample_reconciliation.bank_account_id
    statement_ending_balance = sample_reconciliation.statement_ending_balance
    
    cleared_stmt_ids = [10, 11]
    cleared_sys_ids = [20, 21]
    all_cleared_ids = [10, 11, 20, 21]

    mock_session.get.return_value = sample_bank_account # For fetching BankAccount to update

    saved_recon = await reconciliation_service.save_reconciliation_details(
        reconciliation_orm=sample_reconciliation,
        cleared_statement_txn_ids=cleared_stmt_ids,
        cleared_system_txn_ids=cleared_sys_ids,
        statement_end_date=statement_date,
        bank_account_id=bank_account_id,
        statement_ending_balance=statement_ending_balance,
        session=mock_session # Pass the mock session
    )

    mock_session.add.assert_any_call(sample_reconciliation) # Called to save/update reconciliation
    mock_session.add.assert_any_call(sample_bank_account)  # Called to save/update bank account
    
    # Check if BankTransaction update was executed
    assert mock_session.execute.await_count == 1 
    # A more robust check would inspect the actual update statement
    # For example, by checking call_args on mock_session.execute

    await mock_session.flush.call_count == 2 # Once after adding reconciliation, once after all updates
    
    assert sample_bank_account.last_reconciled_date == statement_date
    assert sample_bank_account.last_reconciled_balance == statement_ending_balance
    assert saved_recon == sample_reconciliation

async def test_delete_reconciliation(
    reconciliation_service: BankReconciliationService, 
    mock_session: AsyncMock, 
    sample_reconciliation: BankReconciliationModel
):
    mock_session.get.return_value = sample_reconciliation # Simulate reconciliation exists

    deleted = await reconciliation_service.delete(sample_reconciliation.id)

    assert deleted is True
    # Verify that transactions were updated to be unreconciled
    mock_session.execute.assert_awaited_once() # For the update statement
    # Verify that the reconciliation record was deleted
    mock_session.delete.assert_awaited_once_with(sample_reconciliation)
    mock_session.flush.assert_awaited_once()

```

# tests/unit/services/test_inventory_movement_service.py
```py
# File: tests/unit/services/test_inventory_movement_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime
import logging

from app.services.business_services import InventoryMovementService
from app.models.business.inventory_movement import InventoryMovement as InventoryMovementModel
from app.models.business.product import Product as ProductModel # For context
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.common.enums import InventoryMovementTypeEnum

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
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
    app_core.logger = MagicMock(spec=logging.Logger)
    return app_core

@pytest.fixture
def inventory_movement_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> InventoryMovementService:
    return InventoryMovementService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_product_orm() -> ProductModel:
    return ProductModel(id=1, product_code="ITEM001", name="Test Item", product_type="Inventory", created_by_user_id=1, updated_by_user_id=1)

@pytest.fixture
def sample_inventory_movement_orm(sample_product_orm: ProductModel) -> InventoryMovementModel:
    return InventoryMovementModel(
        id=1, product_id=sample_product_orm.id, 
        movement_date=date(2023, 1, 10),
        movement_type=InventoryMovementTypeEnum.PURCHASE.value,
        quantity=Decimal("10.00"), unit_cost=Decimal("5.00"), total_cost=Decimal("50.00"),
        created_by_user_id=1
    )

# --- Test Cases ---
async def test_get_movement_by_id_found(inventory_movement_service: InventoryMovementService, mock_session: AsyncMock, sample_inventory_movement_orm: InventoryMovementModel):
    mock_session.get.return_value = sample_inventory_movement_orm
    result = await inventory_movement_service.get_by_id(1)
    assert result == sample_inventory_movement_orm

async def test_get_all_movements(inventory_movement_service: InventoryMovementService, mock_session: AsyncMock, sample_inventory_movement_orm: InventoryMovementModel):
    mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_inventory_movement_orm]
    result = await inventory_movement_service.get_all()
    assert len(result) == 1
    assert result[0] == sample_inventory_movement_orm

async def test_save_new_movement(inventory_movement_service: InventoryMovementService, mock_session: AsyncMock, sample_product_orm: ProductModel):
    new_movement = InventoryMovementModel(
        product_id=sample_product_orm.id, movement_date=date(2023, 2, 2),
        movement_type=InventoryMovementTypeEnum.SALE.value, quantity=Decimal("-2.00"),
        unit_cost=Decimal("5.00"), total_cost=Decimal("10.00"),
        created_by_user_id=1
    )
    async def mock_refresh(obj, attr=None): obj.id = 2
    mock_session.refresh.side_effect = mock_refresh
    
    result = await inventory_movement_service.save(new_movement)
    mock_session.add.assert_called_once_with(new_movement)
    assert result.id == 2

async def test_save_movement_with_explicit_session(inventory_movement_service: InventoryMovementService, mock_session: AsyncMock, sample_inventory_movement_orm: InventoryMovementModel):
    # Pass the session explicitly
    result = await inventory_movement_service.save(sample_inventory_movement_orm, session=mock_session)
    mock_session.add.assert_called_once_with(sample_inventory_movement_orm)
    assert result == sample_inventory_movement_orm

async def test_delete_movement(inventory_movement_service: InventoryMovementService, mock_session: AsyncMock, sample_inventory_movement_orm: InventoryMovementModel):
    mock_session.get.return_value = sample_inventory_movement_orm
    deleted = await inventory_movement_service.delete(1)
    assert deleted is True
    mock_session.delete.assert_awaited_once_with(sample_inventory_movement_orm)
    inventory_movement_service.logger.warning.assert_called_once() # Check for warning log

```

# tests/unit/services/test_gst_return_service.py
```py
# File: tests/unit/services/test_gst_return_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime

from app.services.tax_service import GSTReturnService
from app.models.accounting.gst_return import GSTReturn as GSTReturnModel
from app.models.core.user import User as UserModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.common.enums import GSTReturnStatusEnum
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock(); session.get = AsyncMock(); session.execute = AsyncMock()
    session.add = MagicMock(); session.delete = AsyncMock(); session.flush = AsyncMock()
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
    user = MagicMock(spec=UserModel); user.id = 1; return user

@pytest.fixture
def mock_app_core(mock_user: MagicMock) -> MagicMock:
    app_core = MagicMock(spec=ApplicationCore); app_core.logger = MagicMock(spec=logging.Logger)
    app_core.current_user = mock_user
    return app_core

@pytest.fixture
def gst_return_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> GSTReturnService:
    return GSTReturnService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_gst_return_draft() -> GSTReturnModel:
    return GSTReturnModel(
        id=1, return_period="Q1/2023", start_date=date(2023,1,1), end_date=date(2023,3,31),
        filing_due_date=date(2023,4,30), status=GSTReturnStatusEnum.DRAFT.value,
        output_tax=Decimal("1000.00"), input_tax=Decimal("300.00"), tax_payable=Decimal("700.00"),
        created_by_user_id=1, updated_by_user_id=1
    )

async def test_get_gst_return_by_id_found(gst_return_service: GSTReturnService, mock_session: AsyncMock, sample_gst_return_draft: GSTReturnModel):
    mock_session.get.return_value = sample_gst_return_draft
    result = await gst_return_service.get_by_id(1) # get_gst_return calls get_by_id
    assert result == sample_gst_return_draft

async def test_save_new_gst_return(gst_return_service: GSTReturnService, mock_session: AsyncMock, mock_user: MagicMock):
    new_return = GSTReturnModel(
        return_period="Q2/2023", start_date=date(2023,4,1), end_date=date(2023,6,30),
        status=GSTReturnStatusEnum.DRAFT.value, output_tax=Decimal("1200"), input_tax=Decimal("400"), tax_payable=Decimal("800")
        # user_ids will be set by service
    )
    async def mock_refresh(obj, attr=None): obj.id=2
    mock_session.refresh.side_effect = mock_refresh

    result = await gst_return_service.save_gst_return(new_return)
    assert result.id == 2
    assert result.created_by_user_id == mock_user.id
    assert result.updated_by_user_id == mock_user.id
    mock_session.add.assert_called_once_with(new_return)

async def test_delete_draft_gst_return(gst_return_service: GSTReturnService, mock_session: AsyncMock, sample_gst_return_draft: GSTReturnModel):
    sample_gst_return_draft.status = GSTReturnStatusEnum.DRAFT.value
    mock_session.get.return_value = sample_gst_return_draft
    deleted = await gst_return_service.delete(1)
    assert deleted is True
    mock_session.delete.assert_awaited_once_with(sample_gst_return_draft)

async def test_delete_submitted_gst_return_fails(gst_return_service: GSTReturnService, mock_session: AsyncMock, sample_gst_return_draft: GSTReturnModel):
    sample_gst_return_draft.status = GSTReturnStatusEnum.SUBMITTED.value
    mock_session.get.return_value = sample_gst_return_draft
    deleted = await gst_return_service.delete(1)
    assert deleted is False
    mock_session.delete.assert_not_called()

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

# tests/unit/reporting/test_dashboard_manager.py
```py
# File: tests/unit/reporting/test_dashboard_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import date

from app.reporting.dashboard_manager import DashboardManager, CURRENT_ASSET_SUBTYPES, CURRENT_LIABILITY_SUBTYPES
from app.utils.pydantic_models import DashboardKPIData
from app.models.core.company_setting import CompanySetting as CompanySettingModel
from app.models.accounting.fiscal_year import FiscalYear as FiscalYearModel
from app.models.business.bank_account import BankAccount as BankAccountModel # For BankAccountSummaryData mock
from app.utils.pydantic_models import BankAccountSummaryData # For _get_total_cash_balance mock
from app.models.accounting.account import Account as AccountModel


# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_app_core() -> MagicMock:
    """Fixture to create a mock ApplicationCore with mocked services."""
    app_core = MagicMock(spec_set=["company_settings_service", "fiscal_year_service", 
                                   "financial_statement_generator", "bank_account_service", 
                                   "customer_service", "vendor_service", 
                                   "account_service", "journal_service", "logger",
                                   "configuration_service"]) # Added configuration_service
    
    app_core.company_settings_service = AsyncMock()
    app_core.fiscal_year_service = AsyncMock()
    app_core.financial_statement_generator = AsyncMock()
    app_core.bank_account_service = AsyncMock()
    app_core.customer_service = AsyncMock()
    app_core.vendor_service = AsyncMock()
    app_core.account_service = AsyncMock()
    app_core.journal_service = AsyncMock()
    app_core.configuration_service = AsyncMock() # Mock for configuration service
    app_core.logger = MagicMock()
    return app_core

@pytest.fixture
def dashboard_manager(mock_app_core: MagicMock) -> DashboardManager:
    """Fixture to create a DashboardManager instance."""
    return DashboardManager(app_core=mock_app_core)

# --- Tests for _get_total_cash_balance ---
async def test_get_total_cash_balance_no_accounts(dashboard_manager: DashboardManager, mock_app_core: MagicMock):
    mock_app_core.bank_account_service.get_all_summary.return_value = []
    mock_app_core.configuration_service.get_config_value.return_value = "1110" # Example cash GL
    mock_app_core.account_service.get_by_code.return_value = None # No cash GL account

    balance = await dashboard_manager._get_total_cash_balance("SGD")
    assert balance == Decimal("0")

async def test_get_total_cash_balance_with_bank_accounts(dashboard_manager: DashboardManager, mock_app_core: MagicMock):
    mock_bank_accounts = [
        BankAccountSummaryData(id=1, account_name="B1", bank_name="BankA", account_number="111", currency_code="SGD", current_balance=Decimal("1000.50"), gl_account_code="1010", is_active=True),
        BankAccountSummaryData(id=2, account_name="B2", bank_name="BankB", account_number="222", currency_code="SGD", current_balance=Decimal("500.25"), gl_account_code="1011", is_active=True),
        BankAccountSummaryData(id=3, account_name="B3", bank_name="BankC", account_number="333", currency_code="USD", current_balance=Decimal("200.00"), gl_account_code="1012", is_active=True), # Different currency
    ]
    mock_app_core.bank_account_service.get_all_summary.return_value = mock_bank_accounts
    mock_app_core.configuration_service.get_config_value.return_value = None # No separate cash GL

    balance = await dashboard_manager._get_total_cash_balance("SGD")
    assert balance == Decimal("1500.75")

async def test_get_total_cash_balance_with_cash_gl(dashboard_manager: DashboardManager, mock_app_core: MagicMock):
    mock_app_core.bank_account_service.get_all_summary.return_value = [] # No bank accounts
    
    mock_cash_gl = AccountModel(id=5, code="1110", name="Cash On Hand", account_type="Asset", sub_type="Cash and Cash Equivalents", is_active=True, created_by_user_id=1, updated_by_user_id=1)
    mock_app_core.configuration_service.get_config_value.return_value = "1110"
    mock_app_core.account_service.get_by_code.return_value = mock_cash_gl
    mock_app_core.bank_account_service.get_by_gl_account_id.return_value = None # Cash GL not linked to a bank account
    mock_app_core.journal_service.get_account_balance.return_value = Decimal("50.00")

    balance = await dashboard_manager._get_total_cash_balance("SGD")
    assert balance == Decimal("50.00")

async def test_get_total_cash_balance_cash_gl_linked_to_bank(dashboard_manager: DashboardManager, mock_app_core: MagicMock):
    mock_bank_account_linked_to_cash_gl = BankAccountSummaryData(id=1, account_name="Main SGD", bank_name="DBS", account_number="123", currency_code="SGD", current_balance=Decimal("100.00"), gl_account_code="1110", gl_account_name="Cash On Hand", is_active=True)
    mock_app_core.bank_account_service.get_all_summary.return_value = [mock_bank_account_linked_to_cash_gl]
    
    mock_cash_gl = AccountModel(id=5, code="1110", name="Cash On Hand", account_type="Asset", sub_type="Cash and Cash Equivalents", is_active=True, created_by_user_id=1, updated_by_user_id=1)
    mock_app_core.configuration_service.get_config_value.return_value = "1110"
    mock_app_core.account_service.get_by_code.return_value = mock_cash_gl
    # Simulate that this GL account IS linked to a bank account (the one we already summed)
    mock_app_core.bank_account_service.get_by_gl_account_id.return_value = BankAccountModel(id=1, gl_account_id=5, account_name="Main SGD", account_number="123", bank_name="DBS", currency_code="SGD", created_by_user_id=1,updated_by_user_id=1)

    balance = await dashboard_manager._get_total_cash_balance("SGD")
    assert balance == Decimal("100.00") # Should not double count

# --- Tests for get_dashboard_kpis ---
@pytest.fixture
def mock_kpi_dependencies(mock_app_core: MagicMock):
    mock_app_core.company_settings_service.get_company_settings.return_value = CompanySettingModel(id=1, company_name="Test Co", base_currency="SGD", fiscal_year_start_month=1, fiscal_year_start_day=1, updated_by_user_id=1)
    mock_app_core.fiscal_year_service.get_all.return_value = [
        FiscalYearModel(id=1, year_name="FY2023", start_date=date(2023,1,1), end_date=date(2023,12,31), is_closed=False, created_by_user_id=1, updated_by_user_id=1)
    ]
    mock_app_core.financial_statement_generator.generate_profit_loss.return_value = {
        "revenue": {"total": Decimal("120000")},
        "expenses": {"total": Decimal("80000")},
        "net_profit": Decimal("40000")
    }
    # Mock _get_total_cash_balance directly for this test's focus
    # Patching an async method of an instance requires careful setup if not mocking the instance itself
    # For simplicity, let's assume _get_total_cash_balance is called and returns a value
    
    mock_app_core.customer_service.get_total_outstanding_balance.return_value = Decimal("15000")
    mock_app_core.customer_service.get_total_overdue_balance.return_value = Decimal("5000")
    mock_app_core.customer_service.get_ar_aging_summary.return_value = {
        "Current": Decimal("10000"), "1-30 Days": Decimal("3000"), 
        "31-60 Days": Decimal("1500"), "61-90 Days": Decimal("500"), "91+ Days": Decimal(0)
    }
    mock_app_core.vendor_service.get_total_outstanding_balance.return_value = Decimal("8000")
    mock_app_core.vendor_service.get_total_overdue_balance.return_value = Decimal("2000")
    mock_app_core.vendor_service.get_ap_aging_summary.return_value = {
        "Current": Decimal("6000"), "1-30 Days": Decimal("1000"), 
        "31-60 Days": Decimal("700"), "61-90 Days": Decimal("300"), "91+ Days": Decimal(0)
    }
    # Mock account fetching for Current Ratio
    mock_app_core.account_service.get_all_active.return_value = [
        AccountModel(id=10, code="CA1", name="Current Asset 1", account_type="Asset", sub_type="Current Asset", is_active=True, created_by_user_id=1, updated_by_user_id=1),
        AccountModel(id=11, code="CA2", name="Bank", account_type="Asset", sub_type="Cash and Cash Equivalents", is_active=True, created_by_user_id=1, updated_by_user_id=1),
        AccountModel(id=20, code="CL1", name="Current Liability 1", account_type="Liability", sub_type="Current Liability", is_active=True, created_by_user_id=1, updated_by_user_id=1),
        AccountModel(id=21, code="CL2", name="AP Control", account_type="Liability", sub_type="Accounts Payable", is_active=True, created_by_user_id=1, updated_by_user_id=1),
        AccountModel(id=30, code="NCA1", name="Fixed Asset", account_type="Asset", sub_type="Fixed Asset", is_active=True, created_by_user_id=1, updated_by_user_id=1),
    ]
    # Mock journal_service.get_account_balance calls
    def mock_get_balance(acc_id, as_of_date):
        if acc_id == 10: return Decimal("50000") # CA1
        if acc_id == 11: return Decimal("30000") # CA2 (Bank)
        if acc_id == 20: return Decimal("20000") # CL1
        if acc_id == 21: return Decimal("10000") # CL2 (AP)
        if acc_id == 30: return Decimal("100000") # NCA1
        return Decimal(0)
    mock_app_core.journal_service.get_account_balance.side_effect = mock_get_balance
    
    # Mock for cash balance method if not testing it directly here
    # This needs to be an async mock if _get_total_cash_balance is async
    # For simplicity, we mock the result it contributes to.
    # Or, we can make _get_total_cash_balance a synchronous helper if it only orchestrates async calls.
    # Let's assume it's async for now and patch it.
    
async def test_get_dashboard_kpis_full_data(dashboard_manager: DashboardManager, mock_app_core: MagicMock, mock_kpi_dependencies):
    # Patch the _get_total_cash_balance method for this specific test
    with patch.object(dashboard_manager, '_get_total_cash_balance', AsyncMock(return_value=Decimal("30000"))) as mock_cash_balance_method:
        kpis = await dashboard_manager.get_dashboard_kpis()

    assert kpis is not None
    assert kpis.kpi_period_description.startswith("YTD as of")
    assert kpis.base_currency == "SGD"
    assert kpis.total_revenue_ytd == Decimal("120000")
    assert kpis.total_expenses_ytd == Decimal("80000")
    assert kpis.net_profit_ytd == Decimal("40000")
    
    mock_cash_balance_method.assert_awaited_once_with("SGD")
    assert kpis.current_cash_balance == Decimal("30000") # From patched method

    assert kpis.total_outstanding_ar == Decimal("15000")
    assert kpis.total_ar_overdue == Decimal("5000")
    assert kpis.ar_aging_current == Decimal("10000")
    assert kpis.ar_aging_1_30 == Decimal("3000")
    
    assert kpis.total_outstanding_ap == Decimal("8000")
    assert kpis.total_ap_overdue == Decimal("2000")
    assert kpis.ap_aging_current == Decimal("6000")
    assert kpis.ap_aging_1_30 == Decimal("1000")

    # Current Assets = CA1 (50000) + CA2 (30000) = 80000
    # Current Liabilities = CL1 (20000) + CL2 (10000) = 30000
    # Current Ratio = 80000 / 30000 = 2.666... -> 2.67
    assert kpis.total_current_assets == Decimal("80000.00")
    assert kpis.total_current_liabilities == Decimal("30000.00")
    assert kpis.current_ratio == Decimal("2.67") # 80000 / 30000

async def test_get_dashboard_kpis_no_fiscal_year(dashboard_manager: DashboardManager, mock_app_core: MagicMock, mock_kpi_dependencies):
    mock_app_core.fiscal_year_service.get_all.return_value = [] # No fiscal years
    
    with patch.object(dashboard_manager, '_get_total_cash_balance', AsyncMock(return_value=Decimal("100"))):
        kpis = await dashboard_manager.get_dashboard_kpis()

    assert kpis is not None
    assert kpis.kpi_period_description.endswith("(No active FY)")
    assert kpis.total_revenue_ytd == Decimal("0") # Default if no FY
    assert kpis.net_profit_ytd == Decimal("0")

async def test_get_dashboard_kpis_current_ratio_zero_liabilities(dashboard_manager: DashboardManager, mock_app_core: MagicMock, mock_kpi_dependencies):
    # Override AccountService.get_all_active and JournalService.get_account_balance for this case
    mock_app_core.account_service.get_all_active.return_value = [
        AccountModel(id=10, code="CA1", name="Current Asset 1", account_type="Asset", sub_type="Current Asset", is_active=True, created_by_user_id=1, updated_by_user_id=1)
    ]
    mock_app_core.journal_service.get_account_balance.side_effect = lambda acc_id, as_of_date: Decimal("50000") if acc_id == 10 else Decimal(0)

    with patch.object(dashboard_manager, '_get_total_cash_balance', AsyncMock(return_value=Decimal("0"))):
        kpis = await dashboard_manager.get_dashboard_kpis()
    
    assert kpis is not None
    assert kpis.total_current_assets == Decimal("50000.00")
    assert kpis.total_current_liabilities == Decimal("0.00")
    assert kpis.current_ratio == Decimal('Infinity') # Or None if we prefer to represent it that way in DTO
    # My DTO stores current_ratio: Optional[Decimal], manager sets it to Decimal('Infinity') then DTO field is Optional.
    # Pydantic might convert Decimal('Infinity') to float('inf'). The DashboardWidget then handles display.
    # This needs to be consistent. Let's say manager sets `current_ratio = None` if liabilities are zero.
    # I updated DashboardManager to set current_ratio to Decimal('Infinity') if L=0 and A>0.
    # The DTO DashboardKPIData current_ratio field is Optional[Decimal].
    # The _format_decimal_for_display handles is_finite(), so this should become "N/A (Infinite)"

```

# tests/unit/reporting/test_financial_statement_generator.py.bak
```bak
# File: tests/unit/reporting/test_financial_statement_generator.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date

from app.reporting.financial_statement_generator import FinancialStatementGenerator
from app.models.accounting.account import Account as AccountModel
from app.models.accounting.account_type import AccountType as AccountTypeModel
from app.models.accounting.fiscal_year import FiscalYear as FiscalYearModel
from app.models.core.company_setting import CompanySetting as CompanySettingModel
# Services to mock
from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.accounting_services import AccountTypeService, DimensionService
from app.services.tax_service import TaxCodeService
from app.services.core_services import CompanySettingsService

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_account_service() -> AsyncMock: return AsyncMock(spec=AccountService)
@pytest.fixture
def mock_journal_service() -> AsyncMock: return AsyncMock(spec=JournalService)
@pytest.fixture
def mock_fiscal_period_service() -> AsyncMock: return AsyncMock(spec=FiscalPeriodService)
@pytest.fixture
def mock_account_type_service() -> AsyncMock: return AsyncMock(spec=AccountTypeService)
@pytest.fixture
def mock_tax_code_service() -> AsyncMock: return AsyncMock(spec=TaxCodeService)
@pytest.fixture
def mock_company_settings_service() -> AsyncMock: return AsyncMock(spec=CompanySettingsService)
@pytest.fixture
def mock_dimension_service() -> AsyncMock: return AsyncMock(spec=DimensionService)


@pytest.fixture
def fs_generator(
    mock_account_service: AsyncMock, mock_journal_service: AsyncMock,
    mock_fiscal_period_service: AsyncMock, mock_account_type_service: AsyncMock,
    mock_tax_code_service: AsyncMock, mock_company_settings_service: AsyncMock,
    mock_dimension_service: AsyncMock
) -> FinancialStatementGenerator:
    return FinancialStatementGenerator(
        account_service=mock_account_service, journal_service=mock_journal_service,
        fiscal_period_service=mock_fiscal_period_service, account_type_service=mock_account_type_service,
        tax_code_service=mock_tax_code_service, company_settings_service=mock_company_settings_service,
        dimension_service=mock_dimension_service
    )

# Sample ORM objects
@pytest.fixture
def asset_account_type() -> AccountTypeModel:
    return AccountTypeModel(id=1, name="Current Asset", category="Asset", is_debit_balance=True, report_type="BS", display_order=1)
@pytest.fixture
def liability_account_type() -> AccountTypeModel:
    return AccountTypeModel(id=2, name="Current Liability", category="Liability", is_debit_balance=False, report_type="BS", display_order=2)
@pytest.fixture
def equity_account_type() -> AccountTypeModel:
    return AccountTypeModel(id=3, name="Share Capital", category="Equity", is_debit_balance=False, report_type="BS", display_order=3)
@pytest.fixture
def revenue_account_type() -> AccountTypeModel:
    return AccountTypeModel(id=4, name="Sales Revenue", category="Revenue", is_debit_balance=False, report_type="PL", display_order=4)
@pytest.fixture
def expense_account_type() -> AccountTypeModel:
    return AccountTypeModel(id=5, name="Rent Expense", category="Expense", is_debit_balance=True, report_type="PL", display_order=5)

@pytest.fixture
def sample_accounts(asset_account_type, liability_account_type, equity_account_type, revenue_account_type, expense_account_type) -> List[AccountModel]:
    # Account.account_type stores the category, Account.sub_type stores the AccountType.name
    return [
        AccountModel(id=1, code="1010", name="Cash", account_type="Asset", sub_type="Current Asset", is_active=True, created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=2, code="2010", name="AP", account_type="Liability", sub_type="Current Liability", is_active=True, created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=3, code="3010", name="Capital", account_type="Equity", sub_type="Share Capital", is_active=True, created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=4, code="4010", name="Sales", account_type="Revenue", sub_type="Sales Revenue", is_active=True, created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=5, code="5010", name="Rent", account_type="Expense", sub_type="Rent Expense", is_active=True, created_by_user_id=1,updated_by_user_id=1),
    ]

async def test_generate_trial_balance(fs_generator: FinancialStatementGenerator, mock_account_service: AsyncMock, mock_journal_service: AsyncMock, sample_accounts: List[AccountModel]):
    as_of = date(2023,12,31)
    mock_account_service.get_all_active.return_value = sample_accounts
    
    def get_balance_side_effect(acc_id, dt):
        if acc_id == 1: return Decimal("1000") # Cash - Debit
        if acc_id == 2: return Decimal("-1500") # AP - Credit (JournalService returns signed, FSG flips for display)
        if acc_id == 3: return Decimal("-500")  # Capital - Credit
        if acc_id == 4: return Decimal("-2000") # Sales - Credit
        if acc_id == 5: return Decimal("1000")  # Rent - Debit
        return Decimal(0)
    mock_journal_service.get_account_balance.side_effect = get_balance_side_effect
    
    # Mock AccountTypeService for _get_account_type_map
    mock_account_type_service = fs_generator.account_type_service
    mock_account_type_service.get_all.return_value = [ # type: ignore
        AccountTypeModel(category="Asset", is_debit_balance=True, name="N/A", id=0, display_order=0, report_type="N/A"), 
        AccountTypeModel(category="Liability", is_debit_balance=False, name="N/A", id=0, display_order=0, report_type="N/A"),
        AccountTypeModel(category="Equity", is_debit_balance=False, name="N/A", id=0, display_order=0, report_type="N/A"),
        AccountTypeModel(category="Revenue", is_debit_balance=False, name="N/A", id=0, display_order=0, report_type="N/A"),
        AccountTypeModel(category="Expense", is_debit_balance=True, name="N/A", id=0, display_order=0, report_type="N/A")
    ]


    tb_data = await fs_generator.generate_trial_balance(as_of)

    assert tb_data['title'] == "Trial Balance"
    assert tb_data['total_debits'] == Decimal("2000.00") # 1000 Cash + 1000 Rent
    assert tb_data['total_credits'] == Decimal("4000.00") # 1500 AP + 500 Capital + 2000 Sales
    assert tb_data['is_balanced'] is False # Based on these numbers

    # Check if accounts are in correct columns
    debit_codes = [acc['code'] for acc in tb_data['debit_accounts']]
    credit_codes = [acc['code'] for acc in tb_data['credit_accounts']]
    assert "1010" in debit_codes
    assert "5010" in debit_codes
    assert "2010" in credit_codes
    assert "3010" in credit_codes
    assert "4010" in credit_codes


async def test_generate_balance_sheet(fs_generator: FinancialStatementGenerator, mock_account_service: AsyncMock, mock_journal_service: AsyncMock, sample_accounts: List[AccountModel]):
    as_of = date(2023,12,31)
    mock_account_service.get_all_active.return_value = sample_accounts
    
    def get_balance_side_effect(acc_id, dt): # Balances for BS
        if acc_id == 1: return Decimal("1000") # Cash
        if acc_id == 2: return Decimal("-1500")# AP
        if acc_id == 3: return Decimal("-500") # Capital
        return Decimal(0) # Revenue/Expense not on BS directly
    mock_journal_service.get_account_balance.side_effect = get_balance_side_effect
    mock_account_type_service = fs_generator.account_type_service
    mock_account_type_service.get_all.return_value = [ # type: ignore
        AccountTypeModel(category="Asset", is_debit_balance=True, name="N/A", id=0, display_order=0, report_type="N/A"), 
        AccountTypeModel(category="Liability", is_debit_balance=False, name="N/A", id=0, display_order=0, report_type="N/A"),
        AccountTypeModel(category="Equity", is_debit_balance=False, name="N/A", id=0, display_order=0, report_type="N/A")
    ]

    bs_data = await fs_generator.generate_balance_sheet(as_of)

    assert bs_data['assets']['total'] == Decimal("1000.00")
    assert bs_data['liabilities']['total'] == Decimal("1500.00") # Note: -1500 becomes 1500 due to !is_debit_nature
    assert bs_data['equity']['total'] == Decimal("500.00")
    assert bs_data['total_liabilities_equity'] == Decimal("2000.00")
    assert bs_data['is_balanced'] is False # 1000 != 2000

async def test_generate_profit_loss(fs_generator: FinancialStatementGenerator, mock_account_service: AsyncMock, mock_journal_service: AsyncMock, sample_accounts: List[AccountModel]):
    start_date, end_date = date(2023,1,1), date(2023,12,31)
    mock_account_service.get_all_active.return_value = sample_accounts

    def get_period_activity_side_effect(acc_id, sd, ed): # Balances for P&L (period activity)
        if acc_id == 4: return Decimal("-2000") # Sales (credit balance shown as positive revenue)
        if acc_id == 5: return Decimal("1000")  # Rent (debit balance shown as positive expense)
        return Decimal(0) # Assets/Liab/Equity not on P&L directly
    mock_journal_service.get_account_balance_for_period.side_effect = get_period_activity_side_effect
    mock_account_type_service = fs_generator.account_type_service
    mock_account_type_service.get_all.return_value = [ # type: ignore
        AccountTypeModel(category="Revenue", is_debit_balance=False, name="N/A", id=0, display_order=0, report_type="N/A"),
        AccountTypeModel(category="Expense", is_debit_balance=True, name="N/A", id=0, display_order=0, report_type="N/A")
    ]

    pl_data = await fs_generator.generate_profit_loss(start_date, end_date)
    
    assert pl_data['revenue']['total'] == Decimal("2000.00") # Note: -2000 becomes 2000
    assert pl_data['expenses']['total'] == Decimal("1000.00")
    assert pl_data['net_profit'] == Decimal("1000.00") # 2000 - 1000

```

# tests/unit/reporting/test_financial_statement_generator.py
```py
# File: tests/unit/reporting/test_financial_statement_generator.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date

from app.reporting.financial_statement_generator import FinancialStatementGenerator
from app.models.accounting.account import Account as AccountModel
from app.models.accounting.account_type import AccountType as AccountTypeModel
from app.models.accounting.fiscal_year import FiscalYear as FiscalYearModel
from app.models.accounting.fiscal_period import FiscalPeriod as FiscalPeriodModel
from app.models.core.company_setting import CompanySetting as CompanySettingModel
from app.models.accounting.journal_entry import JournalEntry as JournalEntryModel, JournalEntryLine as JournalEntryLineModel
from app.models.accounting.dimension import Dimension as DimensionModel

# Service Mocks
from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.accounting_services import AccountTypeService, DimensionService
from app.services.tax_service import TaxCodeService 
from app.services.core_services import CompanySettingsService 

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_account_service() -> AsyncMock: return AsyncMock(spec=AccountService)
@pytest.fixture
def mock_journal_service() -> AsyncMock: return AsyncMock(spec=JournalService)
@pytest.fixture
def mock_fiscal_period_service() -> AsyncMock: return AsyncMock(spec=FiscalPeriodService)
@pytest.fixture
def mock_account_type_service() -> AsyncMock: return AsyncMock(spec=AccountTypeService)
@pytest.fixture
def mock_tax_code_service() -> AsyncMock: return AsyncMock(spec=TaxCodeService) # Optional
@pytest.fixture
def mock_company_settings_service() -> AsyncMock: return AsyncMock(spec=CompanySettingsService) # Optional
@pytest.fixture
def mock_dimension_service() -> AsyncMock: return AsyncMock(spec=DimensionService) # Optional

@pytest.fixture
def fs_generator(
    mock_account_service: AsyncMock, mock_journal_service: AsyncMock,
    mock_fiscal_period_service: AsyncMock, mock_account_type_service: AsyncMock,
    mock_tax_code_service: AsyncMock, mock_company_settings_service: AsyncMock,
    mock_dimension_service: AsyncMock
) -> FinancialStatementGenerator:
    return FinancialStatementGenerator(
        account_service=mock_account_service, journal_service=mock_journal_service,
        fiscal_period_service=mock_fiscal_period_service, account_type_service=mock_account_type_service,
        tax_code_service=mock_tax_code_service, company_settings_service=mock_company_settings_service,
        dimension_service=mock_dimension_service
    )

# --- Sample ORM Data ---
@pytest.fixture
def sample_account_types() -> List[AccountTypeModel]:
    return [
        AccountTypeModel(id=1, name="Cash Equivalents", category="Asset", is_debit_balance=True, report_type="BS", display_order=1),
        AccountTypeModel(id=2, name="Accounts Payable", category="Liability", is_debit_balance=False, report_type="BS", display_order=2),
        AccountTypeModel(id=3, name="Retained Earnings", category="Equity", is_debit_balance=False, report_type="BS", display_order=3),
        AccountTypeModel(id=4, name="Product Sales", category="Revenue", is_debit_balance=False, report_type="PL", display_order=4),
        AccountTypeModel(id=5, name="Operating Expenses", category="Expense", is_debit_balance=True, report_type="PL", display_order=5),
        AccountTypeModel(id=6, name="Current Asset", category="Asset", is_debit_balance=True, report_type="BS", display_order=0), # Generic
        AccountTypeModel(id=7, name="Current Liability", category="Liability", is_debit_balance=False, report_type="BS", display_order=0) # Generic
    ]

@pytest.fixture
def sample_accounts_for_fs(sample_account_types: List[AccountTypeModel]) -> List[AccountModel]:
    # Account.account_type stores the category (Asset, Liability etc.)
    # Account.sub_type stores the specific AccountType.name (Cash Equivalents, Accounts Payable etc.)
    return [
        AccountModel(id=1, code="1010", name="Cash in Bank", account_type="Asset", sub_type="Cash Equivalents", is_active=True, opening_balance=Decimal(0),created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=2, code="1020", name="Accounts Receivable", account_type="Asset", sub_type="Current Asset", is_active=True, opening_balance=Decimal(0),created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=3, code="2010", name="Trade Payables", account_type="Liability", sub_type="Accounts Payable", is_active=True, opening_balance=Decimal(0),created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=4, code="3010", name="Share Capital", account_type="Equity", sub_type="Retained Earnings", is_active=True, opening_balance=Decimal(0),created_by_user_id=1,updated_by_user_id=1), # Using RE as subtype example
        AccountModel(id=5, code="4010", name="Product Revenue", account_type="Revenue", sub_type="Product Sales", is_active=True, opening_balance=Decimal(0),created_by_user_id=1,updated_by_user_id=1),
        AccountModel(id=6, code="5010", name="Rent Expense", account_type="Expense", sub_type="Operating Expenses", is_active=True, opening_balance=Decimal(0),created_by_user_id=1,updated_by_user_id=1),
    ]

# --- Test Cases ---

async def test_get_account_type_map_caching(fs_generator: FinancialStatementGenerator, mock_account_type_service: AsyncMock, sample_account_types: List[AccountTypeModel]):
    mock_account_type_service.get_all.return_value = sample_account_types
    
    # First call
    await fs_generator._get_account_type_map()
    mock_account_type_service.get_all.assert_awaited_once()
    
    # Second call should use cache
    await fs_generator._get_account_type_map()
    mock_account_type_service.get_all.assert_awaited_once() # Still called only once

async def test_calculate_balances_correct_sign(fs_generator: FinancialStatementGenerator, mock_journal_service: AsyncMock, sample_accounts_for_fs: List[AccountModel], sample_account_types: List[AccountTypeModel]):
    as_of = date(2023,12,31)
    # Mock get_all for _get_account_type_map
    fs_generator.account_type_service.get_all = AsyncMock(return_value=sample_account_types) # type: ignore

    # Mock balances: Cash (Asset, debit nature) = +100, AP (Liability, credit nature) = -50 (GL balance), Sales (Revenue, credit nature) = -200
    mock_journal_service.get_account_balance.side_effect = lambda acc_id, dt: {1: Decimal(100), 3: Decimal(-50), 5: Decimal(-200)}.get(acc_id, Decimal(0))

    accounts_to_test = [
        next(acc for acc in sample_accounts_for_fs if acc.id == 1), # Cash
        next(acc for acc in sample_accounts_for_fs if acc.id == 3), # AP
        next(acc for acc in sample_accounts_for_fs if acc.id == 5), # Sales
    ]
    results = await fs_generator._calculate_account_balances_for_report(accounts_to_test, as_of)
    
    assert next(r['balance'] for r in results if r['id'] == 1) == Decimal(100)  # Asset, debit nature, positive stays positive
    assert next(r['balance'] for r in results if r['id'] == 3) == Decimal(50)   # Liability, credit nature, GL -50 becomes +50 for report
    assert next(r['balance'] for r in results if r['id'] == 5) == Decimal(200)  # Revenue, credit nature, GL -200 becomes +200 for report


async def test_generate_trial_balance(fs_generator: FinancialStatementGenerator, mock_account_service: AsyncMock, mock_journal_service: AsyncMock, sample_accounts_for_fs, sample_account_types):
    as_of = date(2023,12,31)
    mock_account_service.get_all_active.return_value = sample_accounts_for_fs
    fs_generator.account_type_service.get_all = AsyncMock(return_value=sample_account_types) # type: ignore

    # Cash +100 (D), AR +200 (D), AP -150 (C), Capital -50 (C), Sales -300 (C), Rent +100 (D)
    # Debits: 100 + 200 + 100 = 400
    # Credits: 150 + 50 + 300 = 500 => Unbalanced
    mock_journal_service.get_account_balance.side_effect = lambda id, dt: {
        1: Decimal("100"), 2: Decimal("200"), 3: Decimal("-150"), 
        4: Decimal("-50"), 5: Decimal("-300"), 6: Decimal("100")
    }.get(id, Decimal(0))

    tb_data = await fs_generator.generate_trial_balance(as_of)
    assert tb_data['total_debits'] == Decimal("400.00")
    assert tb_data['total_credits'] == Decimal("500.00")
    assert tb_data['is_balanced'] is False

async def test_generate_balance_sheet_simple(fs_generator: FinancialStatementGenerator, mock_account_service: AsyncMock, mock_journal_service: AsyncMock, sample_accounts_for_fs, sample_account_types):
    as_of = date(2023,12,31)
    mock_account_service.get_all_active.return_value = sample_accounts_for_fs
    fs_generator.account_type_service.get_all = AsyncMock(return_value=sample_account_types) # type: ignore
    
    # Cash +1000, AR +2000 => Assets = 3000
    # AP -1500 => Liabilities = 1500
    # Capital -500 => Equity = 500
    # L+E = 2000. Assets = 3000. Unbalanced.
    mock_journal_service.get_account_balance.side_effect = lambda id, dt: {
        1: Decimal("1000"), 2: Decimal("2000"), 
        3: Decimal("-1500"), 4: Decimal("-500") 
    }.get(id, Decimal(0))

    bs_data = await fs_generator.generate_balance_sheet(as_of)
    assert bs_data['assets']['total'] == Decimal("3000.00")
    assert bs_data['liabilities']['total'] == Decimal("1500.00")
    assert bs_data['equity']['total'] == Decimal("500.00")
    assert bs_data['total_liabilities_equity'] == Decimal("2000.00")
    assert bs_data['is_balanced'] is False

async def test_generate_profit_loss_simple(fs_generator: FinancialStatementGenerator, mock_account_service: AsyncMock, mock_journal_service: AsyncMock, sample_accounts_for_fs, sample_account_types):
    start_date, end_date = date(2023,1,1), date(2023,12,31)
    mock_account_service.get_all_active.return_value = sample_accounts_for_fs
    fs_generator.account_type_service.get_all = AsyncMock(return_value=sample_account_types) # type: ignore

    # Sales (Revenue) activity -20000 (so +20000 for report)
    # Rent (Expense) activity +5000 (so +5000 for report)
    # Net Profit = 20000 - 5000 = 15000
    mock_journal_service.get_account_balance_for_period.side_effect = lambda id, sd, ed: {
        5: Decimal("-20000"), # Product Revenue (ID 5)
        6: Decimal("5000")    # Rent Expense (ID 6)
    }.get(id, Decimal(0))

    pl_data = await fs_generator.generate_profit_loss(start_date, end_date)
    assert pl_data['revenue']['total'] == Decimal("20000.00")
    assert pl_data['expenses']['total'] == Decimal("5000.00")
    assert pl_data['net_profit'] == Decimal("15000.00")

async def test_generate_general_ledger(fs_generator: FinancialStatementGenerator, mock_account_service: AsyncMock, mock_journal_service: AsyncMock, sample_accounts_for_fs):
    target_account = next(acc for acc in sample_accounts_for_fs if acc.id == 1) # Cash account
    start_date, end_date = date(2023,1,1), date(2023,1,31)
    
    mock_account_service.get_by_id.return_value = target_account
    mock_journal_service.get_account_balance.return_value = Decimal("100.00") # Opening balance as of Dec 31, 2022

    mock_lines = [
        MagicMock(spec=JournalEntryLineModel, journal_entry=MagicMock(spec=JournalEntryModel, entry_date=date(2023,1,5), entry_no="JE001", description="Cash Sale"), description="LineDesc1", debit_amount=Decimal("200"), credit_amount=Decimal(0)),
        MagicMock(spec=JournalEntryLineModel, journal_entry=MagicMock(spec=JournalEntryModel, entry_date=date(2023,1,10), entry_no="JE002", description="Paid Rent"), description="LineDesc2", debit_amount=Decimal(0), credit_amount=Decimal("50")),
    ]
    mock_journal_service.get_posted_lines_for_account_in_range.return_value = mock_lines
    
    gl_data = await fs_generator.generate_general_ledger(1, start_date, end_date)

    assert gl_data['account_code'] == "1010"
    assert gl_data['opening_balance'] == Decimal("100.00")
    assert len(gl_data['transactions']) == 2
    assert gl_data['transactions'][0]['debit'] == Decimal("200")
    assert gl_data['transactions'][0]['balance'] == Decimal("300.00") # 100 + 200
    assert gl_data['transactions'][1]['credit'] == Decimal("50")
    assert gl_data['transactions'][1]['balance'] == Decimal("250.00") # 300 - 50
    assert gl_data['closing_balance'] == Decimal("250.00")

```

# tests/unit/test_example_unit.py
```py

```

