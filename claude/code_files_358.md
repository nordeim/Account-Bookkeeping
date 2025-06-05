<think>
The user wants me to continue generating the unit tests for the remaining services and managers as per the original comprehensive plan to ensure robustness after fixing circular imports and adding dashboard KPIs.

In the previous step, I provided tests for:
*   `PaymentService`
*   `BankAccountService`
*   `BankTransactionService`
*   `InventoryMovementService`

The remaining services and managers that need unit tests from the list in my earlier thought process (response_56), and that had corresponding code files provided by the user, are:

**Services (from `app/services/`):**
*   `Core Services`: `SequenceService`, `ConfigurationService`, `CompanySettingsService` (tests for these were provided in `project_codebase_tests_files.md`, but I should generate new ones or enhance them if needed to match my current style and ensure full coverage based on their current implementation).
*   `Accounting Services`: `AccountTypeService`, `CurrencyService`, `ExchangeRateService`, `FiscalYearService`, `DimensionService` (tests for these were also in `project_codebase_tests_files.md`).
*   `Tax Services`: `TaxCodeService`, `GSTReturnService`.
*   `Audit Service`: `AuditLogService`.

**Managers & Utilities (from `app/tax/`, `app/reporting/`):**
*   `TaxCalculator` (`app/tax/tax_calculator.py`) (test already provided in `project_codebase_tests_files.md`)
*   `GSTManager` (`app/tax/gst_manager.py`)
*   `IncomeTaxManager` (`app.tax/income_tax_manager.py`) (largely a stub)
*   `WithholdingTaxManager` (`app.tax/withholding_tax_manager.py`) (largely a stub)
*   `FinancialStatementGenerator` (`app/reporting/financial_statement_generator.py`)

**Focus for this Iteration:**
Given the breadth, I should prioritize services that have more complex logic or are critical and haven't been covered by the user-provided tests in `project_codebase_tests_files.md`, or if the provided tests are insufficient.

Let's look at the user-provided tests from `project_codebase_tests_files.md` again:
*   `test_tax_calculator.py`: Looks good.
*   `test_pydantic_models_journal_entry.py`: DTO tests.
*   `test_sequence_generator.py`: Utility test.
*   `test_currency_service.py`: Covers `CurrencyService`.
*   `test_company_settings_service.py`: Covers `CompanySettingsService`.
*   `test_exchange_rate_service.py`: Covers `ExchangeRateService`.
*   `test_fiscal_period_service.py`: Covers `FiscalPeriodService`.
*   `test_configuration_service.py`: Covers `ConfigurationService`.
*   `test_account_type_service.py`: Covers `AccountTypeService`.
*   `test_dimension_service.py`: Covers `DimensionService`.
*   `test_bank_reconciliation_service.py`: Covers `BankReconciliationService`.
*   `test_sequence_service.py`: Covers `SequenceService`.
*   `test_fiscal_year_service.py`: Covers `FiscalYearService`.

**Services from `project_codebase_files_set-4.md` that still need tests written by me (or enhanced):**
*   `JournalService` (`app/services/journal_service.py`) - This is critical.
*   `TaxCodeService` (`app/services/tax_service.py`)
*   `GSTReturnService` (`app/services/tax_service.py`)
*   `AuditLogService` (`app/services/audit_services.py`) - This has complex logic for formatting and pagination.

**Managers/Utilities that need tests:**
*   `GSTManager` (`app/tax/gst_manager.py`) - Complex logic.
*   `FinancialStatementGenerator` (`app/reporting/financial_statement_generator.py`) - Very complex logic.
*   Stub managers like `IncomeTaxManager`, `WithholdingTaxManager` might only need very basic tests confirming their stub nature or initialization if they don't have real logic yet.

**Plan for this Response:**
I will focus on providing unit tests for the following critical services, as they form the backbone of many operations:
1.  **`JournalService`**
2.  **`TaxCodeService`**
3.  **`GSTReturnService`**

Testing `FinancialStatementGenerator` and `GSTManager` will be substantial efforts for a subsequent step due to their complexity and many dependencies. `AuditLogService` is also a good candidate for later.

**Detailed Execution Plan & Checklist for This Iteration:**

**Phase 1: Unit Tests for `JournalService`**
1.  **Create `tests/unit/services/test_journal_service.py`**:
    *   Setup common fixtures (`mock_session`, `mock_db_manager`, `mock_app_core`).
    *   Fixture for `JournalService` instance.
    *   Fixtures for sample ORM objects (`JournalEntry`, `JournalEntryLine`, `Account`, `RecurringPattern`).
    *   Checklist for methods in `JournalService` (referencing `app/services/journal_service.py` from file set 4):
        *   [ ] `test_get_by_id_found_and_not_found()`: Check eager loading.
        *   [ ] `test_get_all_returns_list_and_empty()`: Check ordering.
        *   [ ] `test_get_all_summary_no_filters()`: Verify DTO-like structure.
        *   [ ] `test_get_all_summary_with_filters()`: Test `start_date`, `end_date`, `status`, `entry_no`, `description`, `journal_type`.
        *   [ ] `test_get_by_entry_no_found_and_not_found()`.
        *   [ ] `test_get_by_date_range()`.
        *   [ ] `test_get_posted_entries_by_date_range()`.
        *   [ ] `test_save_new_journal_entry()` (covers `add`).
        *   [ ] `test_save_updated_journal_entry()` (covers `update`).
        *   [ ] `test_delete_draft_journal_entry_success()`.
        *   [ ] `test_delete_posted_journal_entry_fails()` (check logger warning).
        *   [ ] `test_delete_journal_entry_not_found()`.
        *   [ ] `test_get_account_balance_correct_calculation()`: Test with opening balance, debits, credits, different dates.
        *   [ ] `test_get_account_balance_account_not_found()` (if service should handle this, or assume valid ID).
        *   [ ] `test_get_account_balance_for_period_correct_calculation()`.
        *   [ ] `test_get_posted_lines_for_account_in_range_no_filters()`.
        *   [ ] `test_get_posted_lines_for_account_in_range_with_dimension_filters()`.
        *   [ ] `test_get_recurring_patterns_due()`: Test with patterns due, not due, inactive, past end date.
        *   [ ] `test_save_recurring_pattern()`.

**Phase 2: Unit Tests for `TaxCodeService`**
1.  **Create `tests/unit/services/test_tax_code_service.py`**:
    *   Setup common fixtures. Fixture for `TaxCodeService`. Sample `TaxCode` ORM.
    *   Checklist for methods (referencing `app/services/tax_service.py`):
        *   [ ] `test_get_by_id_found_and_not_found()`.
        *   [ ] `test_get_tax_code_found_active()` (for `code` string).
        *   [ ] `test_get_tax_code_not_found()`.
        *   [ ] `test_get_tax_code_inactive()` (should not be returned by `get_tax_code`).
        *   [ ] `test_get_all_active_tax_codes()` (service's `get_all` filters by `is_active`).
        *   [ ] `test_save_new_tax_code()` (covers `add`). Check audit fields.
        *   [ ] `test_save_updated_tax_code()` (covers `update`). Check audit fields.
        *   [ ] `test_delete_tax_code_deactivates()`: Verify `is_active` becomes `False`.
        *   [ ] `test_delete_already_inactive_tax_code()`.

**Phase 3: Unit Tests for `GSTReturnService`**
1.  **Create `tests/unit/services/test_gst_return_service.py`**:
    *   Setup common fixtures. Fixture for `GSTReturnService`. Sample `GSTReturn` ORM.
    *   Checklist for methods (referencing `app/services/tax_service.py`):
        *   [ ] `test_get_by_id_found_and_not_found()` (covers `get_gst_return`).
        *   [ ] `test_save_gst_return_new()` (covers `add`). Check audit fields.
        *   [ ] `test_save_gst_return_update()`. Check audit fields.
        *   [ ] `test_get_all_returns_list_and_empty()`: Check ordering.
        *   [ ] `test_delete_draft_gst_return_success()`.
        *   [ ] `test_delete_non_draft_gst_return_fails()`.
        *   [ ] `test_delete_gst_return_not_found()`.

This is a good set of tests for these core services. I will generate the files.
</think>

Excellent! The application is stable, and the dashboard is displaying the new KPIs correctly. We are making solid progress.

As per your direction, we will continue with the **"Automated Testing (Continued - CRITICAL)"** roadmap item. Having tested `DashboardManager` and some of its dependent service methods, we'll now expand unit test coverage to other key services that are critical for the application's functionality.

For this iteration, I will focus on creating unit tests for:
1.  **`JournalService`**: This service is central to all accounting transactions.
2.  **`TaxCodeService`**: Essential for GST and other tax calculations.
3.  **`GSTReturnService`**: Manages the persistence of GST return data.

I will create new test files for each of these in the `tests/unit/services/` directory, following the established patterns using `pytest` and `unittest.mock.AsyncMock`.

---
**1. New File: `tests/unit/services/test_journal_service.py`**
---
```python
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

---
**2. New File: `tests/unit/services/test_tax_code_service.py`**
---
```python
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

---
**3. New File: `tests/unit/services/test_gst_return_service.py`**
---
```python
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

