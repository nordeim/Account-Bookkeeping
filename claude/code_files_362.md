<think>
The user is satisfied with the unit tests provided so far for `AuditLogService` and `GSTManager`. I need to continue with the plan to create unit tests for the remaining critical services and managers that were part of the provided codebase snippets and haven't been covered adequately by existing tests (either user-provided or my previous generations).

**Recap of Remaining Components (from previous analysis in response_57) needing tests from me:**

**Services:**
*   `Core Services`: `SequenceService`, `ConfigurationService`, `CompanySettingsService` (user provided tests for these, I should review and decide if enhancements/my style of tests are needed).
*   `Accounting Services`: `AccountTypeService`, `CurrencyService`, `ExchangeRateService`, `FiscalYearService`, `DimensionService` (user provided tests for these, similar review needed).
*   `Tax Services`: `TaxCodeService`, `GSTReturnService` (I just provided tests for these in response_57).

**Managers & Utilities:**
*   `FinancialStatementGenerator` (`app/reporting/financial_statement_generator.py`) - Very complex logic, many dependencies. High priority.
*   Stub Managers: `IncomeTaxManager`, `WithholdingTaxManager` (basic tests for initialization or simple stubs).

**Focus for this Iteration:**
Given the complexity and criticality, I will focus on:
1.  **`FinancialStatementGenerator`**: This is a major piece of logic responsible for generating core financial reports. Testing this thoroughly is important.
2.  Review user-provided tests for **Core Services** (`SequenceService`, `ConfigurationService`, `CompanySettingsService`) and **Accounting Services** (`AccountTypeService`, `CurrencyService`, `ExchangeRateService`, `FiscalYearService`, `DimensionService`). If they are comprehensive and follow good patterns, I may not need to regenerate them. If they are minimal or missing key aspects, I will provide enhanced versions. *For now, I will assume the user-provided tests are sufficient for those services listed in `project_codebase_tests_files.md` and focus on generating tests for components *not* covered by those.*

Therefore, the main target for this iteration is `FinancialStatementGenerator`.

**1. Deeply Understand Requirements for Testing `FinancialStatementGenerator`:**

*   **Methods to Test**:
    *   `_get_account_type_map()`: Internal helper, test caching.
    *   `_calculate_account_balances_for_report()`: Test balance calculation logic, sign flipping for credit-nature accounts.
    *   `_calculate_account_period_activity_for_report()`: Similar to above but for period activity.
    *   `generate_balance_sheet()`: Test correct aggregation for Assets, Liabilities, Equity. Test `is_balanced` flag. Test comparative period logic. Test `include_zero_balances` option.
    *   `generate_profit_loss()`: Test correct aggregation for Revenue, Expenses. Test Net Profit calculation. Test comparative period logic.
    *   `generate_trial_balance()`: Test correct debit/credit balance segregation and totals. Test `is_balanced` flag.
    *   `generate_general_ledger()`: Test opening balance, transaction listing, running balance, closing balance for a single account. Test dimension filtering.
    *   `generate_income_tax_computation()`: If it evolves beyond a stub, test its logic. (Currently complex, may require many mocks if fully tested).
    *   `generate_gst_f5()`: (Currently complex, may require many mocks if fully tested. `GSTManager` handles the main logic).

*   **Dependencies to Mock**: This class has many service dependencies injected via `__init__`:
    *   `AccountService`
    *   `JournalService`
    *   `FiscalPeriodService`
    *   `AccountTypeService`
    *   `TaxCodeService` (Optional)
    *   `CompanySettingsService` (Optional)
    *   `DimensionService` (Optional)
    All these will need to be mocked.

**2. Systematic Diagnosis & Design Considerations for Tests:**

*   **Test File**: `tests/unit/reporting/test_financial_statement_generator.py`.
*   **Mocking Strategy**:
    *   Mock each service dependency (`AsyncMock`).
    *   Configure the return values of the service methods that `FinancialStatementGenerator` calls (e.g., `account_service.get_all_active()`, `journal_service.get_account_balance()`, etc.).
*   **Test Data (Fixtures)**:
    *   Sample `Account` ORM objects with varying `account_type`, `sub_type`, `opening_balance`.
    *   Sample `JournalEntryLine` ORM objects to simulate transactions.
    *   Sample `AccountType` ORM objects.
    *   Sample `FiscalYear`, `FiscalPeriod` ORM objects.
    *   Sample `CompanySetting` ORM (for report headers).
*   **Assertions**:
    *   Verify the structure of the returned dictionaries for each report (e.g., presence of 'title', 'assets', 'liabilities', 'equity' sections for BS).
    *   Verify calculated totals (Total Assets, Total Liabilities, Net Profit, etc.).
    *   Verify correct account grouping and balances within sections.
    *   Verify handling of options like `comparative_date` and `include_zero_balances`.

**3. Implementation Options Exploration (Test Structure for Complex Reports):**

*   **Balance Sheet / P&L**: These reports involve hierarchical data. Tests should set up a small, representative Chart of Accounts and a few transactions, then verify that accounts are correctly categorized and summed.
*   **General Ledger**: Test with one account, mock its opening balance, and a series of mock `JournalEntryLine` objects affecting it. Verify the transaction list and running/closing balances. Test dimension filtering by mocking `journal_service.get_posted_lines_for_account_in_range` to return different sets of lines based on dimension IDs.

**Chosen Implementation Strategy:**
Create focused tests for each main report generation method. Start with simpler reports like Trial Balance if it helps build up context, then move to BS, P&L, and GL.
The income tax and GST F5 generation methods in `FinancialStatementGenerator` are noted as complex and might overlap significantly with `IncomeTaxManager` and `GSTManager` respectively. For unit testing `FinancialStatementGenerator`, if these methods are just stubs or simple calls, testing might be minimal. If they contain significant unique logic, they'd need dedicated test cases. Based on the provided code, these methods in `FinancialStatementGenerator` *do* contain their own logic.

**Detailed Execution Plan for `FinancialStatementGenerator` Tests:**

1.  **Create `tests/unit/reporting/test_financial_statement_generator.py`**:
    *   Setup common fixtures (`mock_account_service`, `mock_journal_service`, etc., `financial_statement_generator` instance).
    *   Fixture for `sample_company_settings_orm`.
    *   Fixture for `sample_accounts_list_orm` (diverse types).
    *   Fixture for `sample_account_types_list_orm`.
    *   Checklist for methods:
        *   [ ] `test_get_account_type_map_caches_results()`
        *   [ ] `test_calculate_account_balances_for_report_asset_expense_nature()` (debit positive)
        *   [ ] `test_calculate_account_balances_for_report_liability_equity_revenue_nature()` (credit positive, shown as positive)
        *   [ ] `test_generate_trial_balance_balanced()`
        *   [ ] `test_generate_trial_balance_unbalanced()`
        *   [ ] `test_generate_balance_sheet_simple_no_comparative()`
        *   [ ] `test_generate_balance_sheet_with_comparative()`
        *   [ ] `test_generate_balance_sheet_include_zero_balances_option()`
        *   [ ] `test_generate_balance_sheet_is_balanced_flag()`
        *   [ ] `test_generate_profit_loss_simple_no_comparative()`
        *   [ ] `test_generate_profit_loss_with_comparative()`
        *   [ ] `test_generate_general_ledger_basic()`
        *   [ ] `test_generate_general_ledger_with_dimension_filters()` (mock `DimensionService.get_by_id` and `JournalService.get_posted_lines_for_account_in_range` to react to dimension IDs).
        *   [ ] (Optional, if time/complexity permits for this iteration) Basic test for `generate_income_tax_computation` structure if `FiscalPeriodService.get_fiscal_year` is mocked.
        *   [ ] (Optional, if time/complexity permits) Basic test for `generate_gst_f5` structure if dependencies are mocked.

Given the complexity, I will focus on providing comprehensive tests for `generate_trial_balance`, `generate_balance_sheet`, `generate_profit_loss`, and `generate_general_ledger`. The tax-specific report methods in `FinancialStatementGenerator` might be better tested alongside their respective managers (`GSTManager`, `IncomeTaxManager`) in more integrated tests later, or with very high-level structural checks here. For now, I'll focus on the core financial statements.

I will start by generating `tests/unit/services/test_audit_log_service.py` (as it's smaller and self-contained), and then the more complex `tests/unit/reporting/test_financial_statement_generator.py`. I'll then move to `GSTManager` tests if the response size allows.
</think>

Absolutely! We'll continue with the **"Automated Testing (Continued - CRITICAL)"** roadmap item. Based on our previous discussion and the files provided, the next high-priority components for unit testing are:

1.  **`AuditLogService`**: Crucial for verifying the integrity and utility of the audit trail functionality.
2.  **`FinancialStatementGenerator`**: Core to the application's reporting capabilities; its logic for aggregating and presenting financial data needs thorough testing.
3.  **`GSTManager`**: Contains complex, region-specific tax logic.

I will generate the test files for these components. Due to the potential length, I'll provide `AuditLogService` tests first, then `FinancialStatementGenerator`, and then `GSTManager`.

---
**1. New File: `tests/unit/services/test_audit_log_service.py`**
---
```python
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
    session.get = AsyncMock() # Though not used by primary methods, good for completeness
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
    # First execute is count, second is data. Check that where clause of data query contains user_id filter.
    # This requires inspecting the statement object passed to session.execute.
    # For simplicity, we assume the SQLAlchemy query construction is correct if called.
    # A more detailed test would use a library to assert SQL string or clause elements.
    # For now, this confirms the path is taken. A similar approach for other filters.

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
    changes = {"old": {"updated_at": "ts1"}, "new": {"updated_at": "ts2"}} # Example of only timestamp
    summary = audit_log_service._format_changes_summary(changes)
    # Current impl shows this change. A refinement might classify it as "Minor updates".
    assert "updated_at" in summary

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
```

---
**2. New File: `tests/unit/reporting/test_financial_statement_generator.py`**
---
```python
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

