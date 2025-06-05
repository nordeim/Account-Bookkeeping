<think>
The user is pleased with the progress and wants me to continue creating the remaining unit tests for services and managers as per my earlier comprehensive plan. The previous response successfully provided tests for `PaymentService`, `BankAccountService`, `BankTransactionService`, `InventoryMovementService`, `JournalService`, `TaxCodeService`, and `GSTReturnService`.

Let's review the list of components that still need tests, based on my analysis in `response_56` and the provided file sets:

**Services (from `app/services/`):**
*   `Core Services`: `SequenceService`, `ConfigurationService`, `CompanySettingsService` (tests for these were provided by the user in `project_codebase_tests_files.md`. I should review them and generate enhanced/consistent versions if my style or coverage requirements differ significantly).
*   `Accounting Services`: `AccountTypeService`, `CurrencyService`, `ExchangeRateService`, `FiscalYearService`, `DimensionService` (tests for these were also provided by the user).
*   **`AuditService` (`app/services/audit_services.py`)**: This is a key one I haven't explicitly written tests for yet. It has complex logic for formatting change summaries and pagination.

**Managers & Utilities (from `app/tax/`, `app/reporting/`, and potentially others):**
*   `TaxCalculator` (`app/tax/tax_calculator.py`) (test already provided by user).
*   **`GSTManager` (`app/tax/gst_manager.py`)**: Complex logic, many dependencies. High priority.
*   `IncomeTaxManager` (`app.tax/income_tax_manager.py`) (largely a stub, but test for initialization).
*   `WithholdingTaxManager` (`app.tax/withholding_tax_manager.py`) (largely a stub, test for initialization).
*   **`FinancialStatementGenerator` (`app/reporting/financial_statement_generator.py`)**: Very complex logic, many dependencies. High priority.
*   Other managers from `app/accounting` and `app/business_logic` were fixed for circular imports but don't have dedicated tests from me yet (e.g., `ChartOfAccountsManager`, `CustomerManager`, `SalesInvoiceManager`, etc.). The user's original request was to expand unit test coverage to "all remaining services... and all managers."

**Focus for This Iteration:**
Given the critical nature and complexity, I will focus on:
1.  **`AuditLogService`**: Testing its pagination and summary formatting logic.
2.  **`GSTManager`**: This is a complex manager with significant business logic.
3.  **`FinancialStatementGenerator`**: Also very complex and critical.

Testing managers like `GSTManager` and `FinancialStatementGenerator` will require extensive mocking of their dependent services.

**Detailed Execution Plan & Checklist for This Iteration:**

**Phase 1: Unit Tests for `AuditLogService`**
1.  **Create `tests/unit/services/test_audit_log_service.py`**:
    *   Setup common fixtures (`mock_session`, `mock_db_manager`, `mock_app_core`).
    *   Fixture for `AuditLogService` instance.
    *   Fixtures for sample `AuditLog` and `DataChangeHistory` ORM objects, and `User` ORM for joins.
    *   Checklist for methods:
        *   `test_get_audit_logs_paginated_no_filters()`: Verify DTO conversion, basic pagination (count, data). Test `_format_changes_summary` implicitly or with specific test cases.
        *   `test_get_audit_logs_paginated_with_all_filters()`: Test user, action, entity type, entity ID, date range.
        *   `test_get_audit_logs_paginated_edge_cases()`: Empty results, page beyond total.
        *   `test_format_changes_summary_created()`: Test with sample 'Created' JSONB.
        *   `test_format_changes_summary_deleted()`: Test with sample 'Deleted' JSONB.
        *   `test_format_changes_summary_modified_few_changes()`: Test with a few field changes.
        *   `test_format_changes_summary_modified_many_changes()`: Test truncation logic (...and X other fields).
        *   `test_format_changes_summary_modified_only_timestamps()`: Test "Minor updates" message.
        *   `test_format_changes_summary_no_changes_or_none()`: Test with empty or None JSONB.
        *   `test_get_data_change_history_paginated_no_filters()`.
        *   `test_get_data_change_history_paginated_with_all_filters()`: Test table name, record ID, user, date range.
        *   `test_get_data_change_history_paginated_edge_cases()`.
        *   Test the IRepository stubs (e.g., assert `NotImplementedError` for `add`, `update`, `delete`).

**Phase 2: Unit Tests for `GSTManager` (High-Level - will be complex)**
1.  **Create `tests/unit/tax/test_gst_manager.py`**:
    *   Setup common fixtures.
    *   Extensive mocking for `TaxCodeService`, `JournalService`, `CompanySettingsService`, `GSTReturnService`, `AccountService`, `FiscalPeriodService`, `SequenceGenerator` (or its DB function via `db_manager`), `ApplicationCore` (and its `journal_entry_manager`).
    *   Sample ORM objects for `Account`, `TaxCode`, `JournalEntry`, `JournalEntryLine`, `CompanySetting`, `GSTReturn`.
    *   Checklist for methods:
        *   **`prepare_gst_return_data()`**: This is the core.
            *   Test with no transactions.
            *   Test with transactions affecting standard-rated supplies (SR) and output tax.
            *   Test with transactions affecting zero-rated supplies (ZR).
            *   Test with transactions affecting exempt supplies (ES).
            *   Test with transactions affecting taxable purchases (TX) and input tax.
            *   Test with transactions affecting blocked input tax (BL).
            *   Test with mixed transaction types.
            *   Verify correct calculation of all GST F5 box values in the returned `GSTReturnData` DTO.
            *   Verify `detailed_breakdown` structure and content for each relevant box.
            *   Verify correct calculation of `filing_due_date`.
        *   **`save_gst_return()`**:
            *   Test creating a new draft return.
            *   Test updating an existing draft return.
            *   Mock `gst_return_service.save_gst_return()` and verify it's called with correctly transformed ORM object.
        *   **`finalize_gst_return()`**:
            *   Test successful finalization: status change, submission details set, settlement JE created and posted. Mock `journal_entry_manager.create_journal_entry` and `post_journal_entry`.
            *   Test finalization when GST payable is zero (no JE created).
            *   Test failure if return not found or not in Draft status.
            *   Test failure if essential GL accounts for settlement JE are missing (verify error message).
            *   Test failure if JE creation or posting fails.

**Phase 3: Unit Tests for `FinancialStatementGenerator` (High-Level - also complex)**
1.  **Create `tests/unit/reporting/test_financial_statement_generator.py`**:
    *   Setup common fixtures.
    *   Extensive mocking for `AccountService`, `JournalService`, `FiscalPeriodService`, `AccountTypeService`, `TaxCodeService`, `CompanySettingsService`, `DimensionService`.
    *   Sample ORM objects (`Account`, `JournalEntryLine`, `FiscalYear`, `FiscalPeriod`, `AccountType`).
    *   Checklist for methods:
        *   **`_get_account_type_map()`**: Verify cache works.
        *   **`_calculate_account_balances_for_report()`**: Test correct balance calculation and sign flipping based on account nature.
        *   **`_calculate_account_period_activity_for_report()`**: Similar to above but for period activity.
        *   **`generate_balance_sheet()`**:
            *   Test with simple CoA and transactions. Verify asset, liability, equity totals and individual account balances.
            *   Test `is_balanced` condition.
            *   Test with `comparative_date`.
            *   Test with `include_zero_balances`.
        *   **`generate_profit_loss()`**:
            *   Test with revenue and expense transactions. Verify totals and net profit.
            *   Test with `comparative_start`/`end`.
        *   **`generate_trial_balance()`**:
            *   Test correct segregation of debit/credit balances.
            *   Verify totals and `is_balanced`.
        *   **`generate_general_ledger()`**:
            *   Test for a single account with opening balance and several transactions.
            *   Verify running balance calculation.
            *   Test with dimension filters.
        *   **`generate_income_tax_computation()`** (if logic becomes more complex than stub).
        *   **`generate_gst_f5()`** (if logic becomes more complex than stub).

This is a very ambitious set for one go. I will start with `AuditLogService` as it's a bit more self-contained than the large managers. Then I will proceed to `GSTManager`. `FinancialStatementGenerator` is likely too large to include with these two fully.

**Decision for this iteration:**
1.  Unit tests for `AuditLogService`.
2.  Unit tests for `GSTManager`.

If these are completed successfully and within reasonable output limits, I will then assess if `FinancialStatementGenerator` tests can be added or if they should be deferred.
</think>

Excellent, the application is robust and the Dashboard KPIs are functioning as intended! We will now proceed with the critical task of expanding automated test coverage, as outlined in the "Current Focus / Next Steps" of your `README.md`.

As per my detailed plan, I will focus on creating unit tests for key services and managers. For this iteration, I will provide tests for:

1.  **`AuditLogService`**: This service has important logic for pagination and formatting change summaries, which needs to be verified.
2.  **`GSTManager`**: This manager contains complex business logic for preparing and finalizing GST returns, making it a high-priority candidate for testing.

Due to the potential size and complexity of full test suites for all remaining components, I will generate these two test files first. Tests for `FinancialStatementGenerator` and other managers/services will follow in subsequent steps.

---
**1. New File: `tests/unit/services/test_audit_log_service.py`**
---
```python
# File: tests/unit/services/test_audit_log_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal # For completeness, though not directly used by AuditLog models

from app.services.audit_services import AuditLogService
from app.models.audit.audit_log import AuditLog as AuditLogModel
from app.models.audit.data_change_history import DataChangeHistory as DataChangeHistoryModel
from app.models.core.user import User as UserModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore # For app_core mock
from app.utils.pydantic_models import AuditLogEntryData, DataChangeHistoryEntryData
from app.common.enums import DataChangeTypeEnum
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock()
    # get, add, delete, etc. are not primary actions for AuditLogService from app perspective
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
def sample_audit_log_orm(sample_user_orm: UserModel) -> AuditLogModel:
    return AuditLogModel(
        id=1, user_id=sample_user_orm.id, action="Create", entity_type="core.customer",
        entity_id=101, entity_name="Customer Alpha", 
        changes={"new": {"name": "Customer Alpha", "credit_limit": 1000}},
        ip_address="127.0.0.1", timestamp=datetime(2023, 1, 1, 10, 0, 0)
    )

@pytest.fixture
def sample_data_change_history_orm(sample_user_orm: UserModel) -> DataChangeHistoryModel:
    return DataChangeHistoryModel(
        id=1, table_name="core.customer", record_id=101, field_name="credit_limit",
        old_value="500", new_value="1000", change_type=DataChangeTypeEnum.UPDATE.value,
        changed_by=sample_user_orm.id, changed_at=datetime(2023,1,1,10,0,0)
    )

# --- Tests for AuditLogService ---

async def test_get_audit_logs_paginated_no_filters(audit_log_service: AuditLogService, mock_session: AsyncMock, sample_audit_log_orm: AuditLogModel, sample_user_orm: UserModel):
    # Mock for count query
    mock_count_execute = AsyncMock()
    mock_count_execute.scalar_one.return_value = 1
    
    # Mock for data query
    mock_data_execute = AsyncMock()
    # Simulate result from join: (AuditLog_instance, username_str)
    mock_data_execute.mappings.return_value.all.return_value = [
        {AuditLogModel: sample_audit_log_orm, "username": sample_user_orm.username}
    ]
    mock_session.execute.side_effect = [mock_count_execute, mock_data_execute]

    logs, total_records = await audit_log_service.get_audit_logs_paginated(page=1, page_size=10)

    assert total_records == 1
    assert len(logs) == 1
    assert isinstance(logs[0], AuditLogEntryData)
    assert logs[0].id == sample_audit_log_orm.id
    assert logs[0].username == sample_user_orm.username
    assert "Record Created. Details: name: 'Customer Alpha', credit_limit: '1000'" in logs[0].changes_summary if logs[0].changes_summary else False
    assert mock_session.execute.await_count == 2

async def test_format_changes_summary(audit_log_service: AuditLogService):
    # Created
    changes_create = {"new": {"name": "New Item", "value": 100, "sensitive": "secret"}}
    summary_create = audit_log_service._format_changes_summary(changes_create)
    assert "Record Created." in summary_create
    assert "name: 'New Item'" in summary_create
    assert "value: '100'" in summary_create
    assert "sensitive" not in summary_create # Assuming sensitive fields might be filtered by key name

    # Deleted
    changes_delete = {"old": {"name": "Old Item"}}
    summary_delete = audit_log_service._format_changes_summary(changes_delete)
    assert "Record Deleted." in summary_delete

    # Modified - few changes
    changes_modify_few = {"old": {"status": "Draft"}, "new": {"status": "Approved"}}
    summary_modify_few = audit_log_service._format_changes_summary(changes_modify_few)
    assert "'status': 'Draft' -> 'Approved'" in summary_modify_few

    # Modified - many changes (more than 3 shown by default)
    changes_modify_many = {
        "old": {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        "new": {"a": 10, "b": 20, "c": 30, "d": 40, "e": 50}
    }
    summary_modify_many = audit_log_service._format_changes_summary(changes_modify_many)
    assert "'a': '1' -> '10'" in summary_modify_many
    assert "'b': '2' -> '20'" in summary_modify_many
    assert "'c': '3' -> '30'" in summary_modify_many
    assert "...and 2 other field(s)." in summary_modify_many # d, e are other 2

    # Modified - only timestamps (should be considered minor)
    now = datetime.now()
    changes_timestamps = {"old": {"updated_at": (now - timedelta(hours=1)).isoformat()}, 
                          "new": {"updated_at": now.isoformat()}}
    summary_timestamps = audit_log_service._format_changes_summary(changes_timestamps)
    # The current _format_changes_summary does not specifically filter 'updated_at'
    # so it would show: "'updated_at': '... -> ...'".
    # If filtering is added for "updated_at", then it should be "Minor updates".
    # For now, based on provided code, it will show the change.
    # This test points out a potential refinement for _format_changes_summary.
    # Based on current code it will show the timestamp change.
    assert "updated_at" in summary_timestamps 
    
    # No changes detailed
    changes_no_diff = {"old": {"field": "value"}, "new": {"field": "value"}}
    summary_no_diff = audit_log_service._format_changes_summary(changes_no_diff)
    assert summary_no_diff == "No changes detailed or only sensitive fields updated."


async def test_get_data_change_history_paginated(audit_log_service: AuditLogService, mock_session: AsyncMock, sample_data_change_history_orm: DataChangeHistoryModel, sample_user_orm: UserModel):
    mock_count_execute = AsyncMock(); mock_count_execute.scalar_one.return_value = 1
    mock_data_execute = AsyncMock()
    mock_data_execute.mappings.return_value.all.return_value = [
        {DataChangeHistoryModel: sample_data_change_history_orm, "changed_by_username": sample_user_orm.username}
    ]
    mock_session.execute.side_effect = [mock_count_execute, mock_data_execute]

    history, total_records = await audit_log_service.get_data_change_history_paginated()

    assert total_records == 1
    assert len(history) == 1
    assert isinstance(history[0], DataChangeHistoryEntryData)
    assert history[0].table_name == "core.customer"
    assert history[0].field_name == "credit_limit"
    assert history[0].changed_by_username == sample_user_orm.username

# Test IRepository stubs
async def test_audit_log_service_unsupported_methods(audit_log_service: AuditLogService):
    with pytest.raises(NotImplementedError):
        await audit_log_service.add(MagicMock())
    with pytest.raises(NotImplementedError):
        await audit_log_service.update(MagicMock())
    with pytest.raises(NotImplementedError):
        await audit_log_service.delete(1)
    # get_by_id and get_all are also not fully practical but might have stubs.
    # The service implementation for get_by_id has some logic.
    # get_all raises NotImplementedError.
    with pytest.raises(NotImplementedError):
        await audit_log_service.get_all()
```

---
**2. New File: `tests/unit/tax/test_gst_manager.py`**
---
```python
# File: tests/unit/tax/test_gst_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date

from app.tax.gst_manager import GSTManager
from app.services.tax_service import TaxCodeService, GSTReturnService
from app.services.journal_service import JournalService
from app.services.core_services import CompanySettingsService, SequenceService # SequenceService not directly used by GSTManager methods shown
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.accounting.journal_entry_manager import JournalEntryManager
from app.core.application_core import ApplicationCore # For mocking app_core
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
def mock_sequence_generator() -> AsyncMock: return AsyncMock() # spec=SequenceGenerator if defined
@pytest.fixture
def mock_journal_entry_manager() -> AsyncMock: return AsyncMock(spec=JournalEntryManager)

@pytest.fixture
def mock_app_core(
    mock_journal_entry_manager: AsyncMock, 
    mock_configuration_service: AsyncMock # Add other services AppCore provides if GSTManager uses them
) -> MagicMock:
    app_core = MagicMock(spec=ApplicationCore)
    app_core.logger = MagicMock(spec=logging.Logger)
    app_core.journal_entry_manager = mock_journal_entry_manager
    app_core.configuration_service = mock_configuration_service # For default GL accounts
    return app_core

@pytest.fixture # For configuration_service mock in app_core
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

# Sample Data
@pytest.fixture
def sample_company_settings() -> CompanySettingModel:
    return CompanySettingModel(id=1, company_name="Test Biz", gst_registration_no="M12345678Z", base_currency="SGD", updated_by_user_id=1)

@pytest.fixture
def sample_sr_tax_code() -> TaxCodeModel:
    return TaxCodeModel(id=1, code="SR", tax_type="GST", rate=Decimal("9.00"), affects_account_id=101) # Assume affects_account_id

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
    je = JournalEntry(id=10, entry_no="JE-S001", entry_date=date(2023,1,15), is_posted=True, created_by_user_id=1,updated_by_user_id=1)
    je.lines = [
        JournalEntryLine(account_id=999, account=AccountModel(id=999,code="AR",name="AR",account_type="Asset",created_by_user_id=1,updated_by_user_id=1), debit_amount=Decimal("109.00")),
        JournalEntryLine(account_id=sample_revenue_account.id, account=sample_revenue_account, credit_amount=Decimal("100.00"), tax_code="SR", tax_code_obj=sample_sr_tax_code, tax_amount=Decimal("9.00"))
    ]
    return je

@pytest.fixture
def sample_posted_je_purchase(sample_expense_account: AccountModel, sample_tx_tax_code: TaxCodeModel) -> JournalEntry:
    je = JournalEntry(id=11, entry_no="JE-P001", entry_date=date(2023,1,20), is_posted=True, created_by_user_id=1,updated_by_user_id=1)
    je.lines = [
        JournalEntryLine(account_id=sample_expense_account.id, account=sample_expense_account, debit_amount=Decimal("50.00"), tax_code="TX", tax_code_obj=sample_tx_tax_code, tax_amount=Decimal("4.50")),
        JournalEntryLine(account_id=888, account=AccountModel(id=888,code="AP",name="AP",account_type="Liability",created_by_user_id=1,updated_by_user_id=1), credit_amount=Decimal("54.50"))
    ]
    return je

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
    assert data.taxable_purchases == Decimal(0)
    assert data.output_tax == Decimal(0)
    assert data.input_tax == Decimal(0)
    assert data.tax_payable == Decimal(0)
    assert len(data.detailed_breakdown["box1_standard_rated_supplies"]) == 0

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
    assert data.standard_rated_supplies == Decimal("100.00") # From sales line's credit
    assert data.output_tax == Decimal("9.00")
    assert data.taxable_purchases == Decimal("50.00") # From purchase line's debit
    assert data.input_tax == Decimal("4.50")
    assert data.tax_payable == Decimal("4.50") # 9.00 - 4.50
    assert len(data.detailed_breakdown["box1_standard_rated_supplies"]) == 1
    assert data.detailed_breakdown["box1_standard_rated_supplies"][0].net_amount == Decimal("100.00")
    assert len(data.detailed_breakdown["box5_taxable_purchases"]) == 1
    assert data.detailed_breakdown["box5_taxable_purchases"][0].net_amount == Decimal("50.00")

async def test_save_gst_return_new(gst_manager: GSTManager, mock_gst_return_service: AsyncMock, sample_company_settings: CompanySettingModel):
    gst_data_dto = GSTReturnData(
        return_period="Q1/2024", start_date=date(2024,1,1), end_date=date(2024,3,31),
        standard_rated_supplies=Decimal(1000), output_tax=Decimal(90), user_id=1
    )
    mock_gst_return_service.get_by_id.return_value = None # Simulate not found for new save
    
    # Simulate the service.save_gst_return correctly populating the ORM and returning it
    async def mock_save(return_orm: GSTReturnModel):
        return_orm.id = 10 # Simulate DB generated ID
        return_orm.created_by_user_id = gst_data_dto.user_id
        return_orm.updated_by_user_id = gst_data_dto.user_id
        return return_orm
    mock_gst_return_service.save_gst_return.side_effect = mock_save
    
    result = await gst_manager.save_gst_return(gst_data_dto)
    
    assert result.is_success
    assert result.value is not None
    assert result.value.id == 10
    assert result.value.return_period == "Q1/2024"
    mock_gst_return_service.save_gst_return.assert_awaited_once()
    # Check that the ORM passed to save_gst_return has correct fields set from DTO

async def test_finalize_gst_return_success_with_je(
    gst_manager: GSTManager, 
    mock_gst_return_service: AsyncMock, 
    mock_journal_entry_manager: AsyncMock,
    mock_account_service: AsyncMock,
    mock_configuration_service: AsyncMock,
    sample_gst_return_draft: GSTReturnModel
):
    sample_gst_return_draft.status = GSTReturnStatusEnum.DRAFT.value # Ensure it's draft
    sample_gst_return_draft.tax_payable = Decimal("700.00") # Needs settlement
    mock_gst_return_service.get_by_id.return_value = sample_gst_return_draft
    
    # Mock config values for GL accounts
    mock_configuration_service.get_config_value.side_effect = {
        "SysAcc_DefaultGSTOutput": "SYS-GST-OUT", "SysAcc_DefaultGSTInput": "SYS-GST-IN", "SysAcc_GSTControl": "SYS-GST-CTRL"
    }.get
    
    # Mock account lookups
    mock_account_service.get_by_code.side_effect = lambda code: MagicMock(spec=AccountModel, id=hash(code), code=code, is_active=True)

    # Mock JE creation and posting
    mock_created_je = MagicMock(spec=JournalEntry, id=55)
    mock_journal_entry_manager.create_journal_entry.return_value = Result.success(mock_created_je)
    mock_journal_entry_manager.post_journal_entry.return_value = Result.success(mock_created_je) # Assume posting also returns JE

    mock_gst_return_service.save_gst_return.side_effect = lambda orm_obj: orm_obj # Just return back for simplicity

    result = await gst_manager.finalize_gst_return(1, "REF123", date(2023,4,10), 1)

    assert result.is_success
    finalized_return = result.value
    assert finalized_return is not None
    assert finalized_return.status == GSTReturnStatusEnum.SUBMITTED.value
    assert finalized_return.submission_reference == "REF123"
    assert finalized_return.journal_entry_id == 55
    mock_journal_entry_manager.create_journal_entry.assert_awaited_once()
    mock_journal_entry_manager.post_journal_entry.assert_awaited_once_with(55, 1)
    assert mock_gst_return_service.save_gst_return.await_count == 1 # Should be called once to save final state
```

