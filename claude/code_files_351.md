<think>
The application is launching, and the enhanced dashboard UI (Phase 4) is complete. The user now wants to proceed with **"Automated Testing for Dashboard KPI Logic"**.

This is a critical step to ensure the correctness of the newly added KPI calculations and data aggregation.

**1. Deeply Understand Requirements for Testing:**
We need to write unit tests for the following components and their specific methods involved in generating dashboard KPIs:

*   **`DashboardManager` (`app/reporting/dashboard_manager.py`)**:
    *   `get_dashboard_kpis()`: This is the main orchestrator. Tests should verify it calls dependent services correctly, aggregates their results, calculates the Current Ratio, and populates `DashboardKPIData` DTO accurately.
    *   `_get_total_cash_balance()`: Test its logic for summing bank account balances and potentially cash-on-hand GL.
*   **`CustomerService` (`app/services/business_services.py`)**:
    *   `get_ar_aging_summary()`: Test the aging bucket logic with various invoice scenarios (not overdue, overdue in different buckets, fully paid, partially paid).
*   **`VendorService` (`app/services/business_services.py`)**:
    *   `get_ap_aging_summary()`: Similar tests as for AR aging.
*   **`AccountService` (`app/services/account_service.py`)**:
    *   `get_total_balance_by_account_category_and_type_pattern()`: Test its ability to correctly filter accounts by category and sub_type pattern, and sum their balances.

**2. Systematic Diagnosis & Design Considerations for Tests:**

*   **Test Structure**: Unit tests should be placed in the `tests/unit/` directory, mirroring the application structure.
    *   `tests/unit/reporting/test_dashboard_manager.py`
    *   `tests/unit/services/test_customer_service_dashboard.py` (or add to existing `test_customer_service.py` if one exists)
    *   `tests/unit/services/test_vendor_service_dashboard.py` (or add to existing `test_vendor_service.py`)
    *   `tests/unit/services/test_account_service_dashboard.py` (or add to existing `test_account_service.py`)
*   **Mocking**:
    *   All external dependencies for the unit under test must be mocked. This includes other services, `ApplicationCore`, `DatabaseManager`, and ORM model instances returned by mocked service calls.
    *   `unittest.mock.AsyncMock` will be used for async methods and services.
    *   `unittest.mock.MagicMock` for synchronous components or attributes.
*   **Fixtures (`pytest`)**: Use pytest fixtures to set up mock objects and test data.
*   **Test Data**: Prepare diverse test data (e.g., mock ORM objects for `SalesInvoice`, `PurchaseInvoice`, `Account`, `BankAccount`) to cover various scenarios:
    *   No data / empty results.
    *   Data falling into different aging buckets.
    *   Current liabilities being zero for Current Ratio calculation.
    *   Accounts with different types/subtypes for asset/liability summation.
*   **Assertions**: Assert expected values in the returned DTOs or dictionaries. For Decimals, ensure proper comparison.
*   **Asynchronous Tests**: All test functions interacting with `async` code must be `async def` and marked with `@pytest.mark.asyncio`.

**3. Implementation Options Exploration:**

*   **Testing `DashboardManager.get_dashboard_kpis()`**:
    *   This method is an orchestrator. The main goal is to test that it calls its dependent services with correct parameters and correctly assembles the `DashboardKPIData` from their mocked return values.
    *   Mock `app_core.financial_statement_generator.generate_profit_loss`, `_get_total_cash_balance` (can test this separately or mock its result here), `customer_service.get_ar_aging_summary`, `vendor_service.get_ap_aging_summary`, `account_service.get_all_active`, `journal_service.get_account_balance`.
*   **Testing Aging Logic (`CustomerService`/`VendorService`)**:
    *   Mock the service's `db_manager.session()` to control the data returned by `session.execute(select(SalesInvoice/PurchaseInvoice)...)`.
    *   Provide a list of mock `SalesInvoice` / `PurchaseInvoice` objects with varying `due_date`, `total_amount`, `amount_paid` to test bucket allocation.
*   **Testing Account Summation (`AccountService`)**:
    *   Mock `db_manager.session()` to return a list of mock `Account` objects with different `account_type` and `sub_type`.
    *   Mock `app_core.journal_service.get_account_balance` to return predefined balances for these accounts.
    *   Verify the sum.

**Chosen Implementation Strategy:**
Follow the standard unit testing approach using `pytest` and `unittest.mock`. Create separate test files for each service/manager method being tested.

**Detailed Execution Plan & Checklist:**

**Phase 1: Setup Test Files and Common Fixtures**

1.  **Create Test Files (if they don't exist or need organizing for dashboard tests)**:
    *   Checklist:
        *   [ ] `tests/unit/reporting/test_dashboard_manager.py`
        *   [ ] `tests/unit/services/test_customer_service_dashboard.py` (or integrate into `test_customer_service.py`)
        *   [ ] `tests/unit/services/test_vendor_service_dashboard.py` (or integrate)
        *   [ ] `tests/unit/services/test_account_service_dashboard.py` (or integrate)
    *   *Decision*: For clarity, I will create new files suffixed with `_dashboard` for these tests for now. If they grow, they can be merged.

2.  **Common Pytest Fixtures (in `tests/conftest.py` or at the top of test files)**:
    *   Checklist:
        *   [ ] `mock_session`: Reusable `AsyncMock` for `AsyncSession`.
        *   [ ] `mock_db_manager`: Reusable `MagicMock` for `DatabaseManager`.
        *   [ ] `mock_app_core`: Reusable `MagicMock` for `ApplicationCore`, allowing specific services to be attached as mocks.
        *   [ ] Mock ORM object fixtures (e.g., `sample_sales_invoice`, `sample_account`) as needed.

**Phase 2: Unit Tests for Service Methods**

1.  **Test `CustomerService.get_ar_aging_summary`** (`tests/unit/services/test_customer_service_dashboard.py`):
    *   Checklist:
        *   [ ] Test case: No outstanding invoices. Expected: All aging buckets are zero.
        *   [ ] Test case: Invoices only in "Current" bucket.
        *   [ ] Test case: Invoices spread across all buckets (1-30, 31-60, 61-90, 91+).
        *   [ ] Test case: Invoices exactly on bucket boundaries (e.g., 0 days overdue, 30 days overdue, 31 days overdue).
        *   [ ] Test case: Partially paid invoices correctly contribute their outstanding balance.
        *   [ ] Mock `session.execute()` to return a list of `SalesInvoice` mocks.

2.  **Test `VendorService.get_ap_aging_summary`** (`tests/unit/services/test_vendor_service_dashboard.py`):
    *   Checklist:
        *   [ ] Similar test cases as for AR aging, using `PurchaseInvoice` mocks.

3.  **Test `AccountService.get_total_balance_by_account_category_and_type_pattern`** (`tests/unit/services/test_account_service_dashboard.py`):
    *   Checklist:
        *   [ ] Test case: No matching accounts. Expected: `Decimal(0)`.
        *   [ ] Test case: Matching "Asset" accounts with "Current Asset" sub_type. Mock `journal_service.get_account_balance` for these.
        *   [ ] Test case: Matching "Liability" accounts with "Current Liability" sub_type.
        *   [ ] Test case: Accounts that match category but not sub_type pattern are excluded.
        *   [ ] Test case: Inactive accounts are excluded.
        *   [ ] Mock `session.execute()` for fetching accounts and `app_core.journal_service.get_account_balance`.

**Phase 3: Unit Tests for `DashboardManager` Methods**

1.  **Test `DashboardManager._get_total_cash_balance`** (`tests/unit/reporting/test_dashboard_manager.py`):
    *   Checklist:
        *   [ ] Mock `app_core.bank_account_service.get_all_summary` to return list of `BankAccountSummaryData`.
        *   [ ] Mock `app_core.configuration_service.get_config_value` for "SysAcc_DefaultCash".
        *   [ ] Mock `app_core.account_service.get_by_code` for cash on hand GL.
        *   [ ] Mock `app_core.bank_account_service.get_by_gl_account_id` to simulate cash GL linked/not linked to a bank account.
        *   [ ] Mock `app_core.journal_service.get_account_balance` for cash on hand GL.
        *   [ ] Test case: No bank accounts, no cash GL. Expected: `Decimal(0)`.
        *   [ ] Test case: Only bank accounts in base currency.
        *   [ ] Test case: Bank accounts in mixed currencies (only base currency should be summed).
        *   [ ] Test case: Only cash on hand GL (not linked to a bank account).
        *   [ ] Test case: Cash on hand GL *is* linked to a bank account (should not be double-counted).
        *   [ ] Test case: Both bank accounts and unlinked cash on hand GL.

2.  **Test `DashboardManager.get_dashboard_kpis`** (`tests/unit/reporting/test_dashboard_manager.py`):
    *   Checklist:
        *   [ ] Mock all dependent services on `app_core` accessed by `get_dashboard_kpis`:
            *   `company_settings_service.get_company_settings`
            *   `fiscal_year_service.get_all`
            *   `financial_statement_generator.generate_profit_loss`
            *   `_get_total_cash_balance` (can mock this method of `DashboardManager` itself using `patch.object` or use its actual logic if already tested). Let's mock it to isolate `get_dashboard_kpis` logic.
            *   `customer_service.get_total_outstanding_balance`, `customer_service.get_total_overdue_balance`, `customer_service.get_ar_aging_summary`
            *   `vendor_service.get_total_outstanding_balance`, `vendor_service.get_total_overdue_balance`, `vendor_service.get_ap_aging_summary`
            *   `account_service.get_all_active`
            *   `journal_service.get_account_balance` (for current assets/liabilities loop)
        *   [ ] Test case: No active fiscal year. Verify YTD figures are zero, `kpi_period_description` is correct. Other figures should still calculate.
        *   [ ] Test case: Active fiscal year, data present for all KPIs. Verify all fields in `DashboardKPIData` are populated correctly.
        *   [ ] Test case: Current Ratio - current liabilities are zero. Expected: `current_ratio = None` (or handle Infinity if service returns that).
        *   [ ] Test case: Current Ratio - current assets are zero. Expected: `current_ratio = Decimal(0)`.
        *   [ ] Test case: Current Ratio - valid calculation.

I will create new test files for these units. For services, I'll create new files like `test_customer_service_dashboard_ext.py` to keep dashboard-specific tests separate from any existing service tests, or append to existing ones if they are small.

Let's start by creating `tests/unit/reporting/test_dashboard_manager.py`.
Then, for services: `tests/unit/services/test_customer_service_dashboard_ext.py`, `tests/unit/services/test_vendor_service_dashboard_ext.py`, `tests/unit/services/test_account_service_dashboard_ext.py`.

The `CURRENT_ASSET_SUBTYPES` and `CURRENT_LIABILITY_SUBTYPES` lists in `DashboardManager` need to be comprehensive based on the `general_template.csv` or typical CoA structure.
From `general_template.csv`:
Current Asset SubTypes: "Current Asset", "Cash and Cash Equivalents", "Accounts Receivable", "Inventory" (and potentially "GST Receivable" if that's how "SYS-GST-INPUT" is classified).
Current Liability SubTypes: "Current Liability", "Accounts Payable", "GST Payable" (and potentially "SYS-GST-CONTROL").

The existing `CURRENT_ASSET_SUBTYPES` in `DashboardManager` in `response_53` are:
`"Cash and Cash Equivalents", "Accounts Receivable", "Inventory", "Prepaid Expenses", "Other Current Assets", "Current Asset"`
The existing `CURRENT_LIABILITY_SUBTYPES` are:
`"Accounts Payable", "Accrued Liabilities", "Short-Term Loans", "Current Portion of Long-Term Debt", "GST Payable", "Other Current Liabilities", "Current Liability"`
These lists seem reasonable as a starting point. Test cases in `AccountService` tests should use these to verify the summation.

Let's proceed with generating the test files. I will provide them one by one, starting with `test_dashboard_manager.py`.
</think>

Excellent! The application is stable, and the Dashboard is correctly displaying its initial set of KPIs, including the new AR/AP Aging and Current Ratio figures based on the logic implemented in `DashboardManager`.

Now, as per your direction, we will proceed with the crucial step of **"Automated Testing for Dashboard KPI Logic"**. This will ensure the correctness and reliability of the data aggregation and calculations performed by `DashboardManager` and its underlying services.

**Overall Test Plan:**
We will create unit tests for the key methods involved in fetching and processing data for the dashboard KPIs. This includes:
1.  Testing the aging logic in `CustomerService` and `VendorService`.
2.  Testing the account balance summation logic for current assets/liabilities in `AccountService`.
3.  Testing the cash balance calculation and the main KPI aggregation in `DashboardManager`.

We'll use `pytest` and `unittest.mock.AsyncMock` for asynchronous code.

I will provide the test files one by one, starting with the tests for `DashboardManager`.

---
**1. New File: `tests/unit/reporting/test_dashboard_manager.py`**
---
```python
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

**Note on `_get_total_cash_balance` test setup:**
The `_get_total_cash_balance` method in `DashboardManager` uses `self.app_core.bank_account_service.get_by_gl_account_id`. My previous fix added this method to `BankAccountService`. The unit test for `_get_total_cash_balance` will need to correctly mock this call on the mocked `bank_account_service`.

For the test `test_get_dashboard_kpis_full_data`, I explicitly patched `dashboard_manager._get_total_cash_balance` to focus on the aggregation logic of `get_dashboard_kpis` itself. The individual logic of `_get_total_cash_balance` is tested separately. This is a common and good unit testing practice.

I will create the test files for the services next. Starting with `CustomerService` aging.
</think>

Excellent! The application is running without import errors, and the Dashboard UI is ready to display the new KPIs. We've successfully completed:
*   Phase 1: DTO Update (`DashboardKPIData`)
*   Phase 2: Service Layer Enhancements (`CustomerService`, `VendorService`, `AccountService`)
*   Phase 3: Manager Layer Update (`DashboardManager`)
*   Phase 4: UI Layer Update (Initial `DashboardWidget` UI elements for new KPIs) - *Correction: My previous step completed Phase 3 (Manager). This current prompt is addressing the UI Layer (Phase 4) by fixing the `NameError`.*

The current `NameError` for `QFormLayout` in `DashboardWidget` is a straightforward import issue. After fixing this, the Dashboard should display the new KPIs correctly.

Once this UI fix is validated, the next logical step from your request is to proceed with **"Automated Testing for Dashboard KPI Logic"**.

**Plan for Current Step (Fix `NameError`):**

1.  **Modify `app/ui/dashboard/dashboard_widget.py`**:
    *   Add `QFormLayout` to the import statement from `PySide6.QtWidgets`.

I will provide the corrected `dashboard_widget.py` file.

---
**Complete Updated File: `app/ui/dashboard/dashboard_widget.py`**
---
```python
# File: app/ui/dashboard/dashboard_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QGroupBox, QPushButton, QMessageBox,
    QScrollArea, QFrame, QFormLayout # Added QFormLayout
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QFont, QIcon
from typing import Optional, TYPE_CHECKING, List, Dict # Added List, Dict
from decimal import Decimal, InvalidOperation # Added InvalidOperation

import json 

from app.utils.pydantic_models import DashboardKPIData
from app.main import schedule_task_from_qt

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    # from PySide6.QtGui import QPaintDevice # QPaintDevice not directly used, can be removed

class DashboardWidget(QWidget):
    def __init__(self, app_core: "ApplicationCore", parent: Optional[QWidget] = None): 
        super().__init__(parent)
        self.app_core = app_core
        self._load_request_count = 0 
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass

        self._init_ui()
        self.app_core.logger.info("DashboardWidget: Scheduling initial KPI load.")
        QTimer.singleShot(0, self._request_kpi_load)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        refresh_button_layout = QHBoxLayout()
        self.refresh_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh KPIs")
        self.refresh_button.clicked.connect(self._request_kpi_load)
        refresh_button_layout.addStretch()
        refresh_button_layout.addWidget(self.refresh_button)
        self.main_layout.addLayout(refresh_button_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.main_layout.addWidget(scroll_area)

        container_widget = QWidget()
        scroll_area.setWidget(container_widget)
        
        container_layout = QVBoxLayout(container_widget)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        kpi_group = QGroupBox("Key Performance Indicators")
        container_layout.addWidget(kpi_group)
        
        self.kpi_layout = QGridLayout(kpi_group) 
        self.kpi_layout.setSpacing(10)
        self.kpi_layout.setColumnStretch(1, 1) 
        self.kpi_layout.setColumnStretch(3, 1) 
        self.kpi_layout.setColumnMinimumWidth(0, 200) 
        self.kpi_layout.setColumnMinimumWidth(2, 200) 


        def add_kpi_row(layout: QGridLayout, row: int, col_offset: int, title: str) -> QLabel:
            title_label = QLabel(title)
            title_label.setFont(QFont(self.font().family(), -1, QFont.Weight.Bold))
            value_label = QLabel("Loading...")
            value_label.setFont(QFont(self.font().family(), 11)) # Increased font size for values
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(title_label, row, col_offset)
            layout.addWidget(value_label, row, col_offset + 1)
            return value_label

        current_row = 0
        self.period_label = QLabel("Period: Loading...")
        self.period_label.setStyleSheet("font-style: italic; color: grey;")
        self.kpi_layout.addWidget(self.period_label, current_row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter) 

        self.base_currency_label = QLabel("Currency: Loading...")
        self.base_currency_label.setStyleSheet("font-style: italic; color: grey;")
        self.kpi_layout.addWidget(self.base_currency_label, current_row, 2, 1, 2, Qt.AlignmentFlag.AlignCenter) 
        current_row += 1
        
        # YTD P&L and Cash
        self.revenue_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Revenue (YTD):")
        self.cash_balance_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Current Cash Balance:")
        current_row += 1
        self.expenses_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Expenses (YTD):")
        self.current_ratio_label = add_kpi_row(self.kpi_layout, current_row, 2, "Current Ratio:") 
        current_row += 1
        self.net_profit_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Net Profit / (Loss) (YTD):")
        current_row += 1 # Spacer row before next set of KPIs

        # AR/AP Totals
        self.kpi_layout.addWidget(QLabel("---"), current_row, 0, 1, 4) # Visual separator
        current_row += 1
        self.ar_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Outstanding AR:")
        self.ap_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Total Outstanding AP:")
        current_row += 1
        self.ar_overdue_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total AR Overdue:")
        self.ap_overdue_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Total AP Overdue:")
        current_row += 1
        
        # AR Aging Group Box
        ar_aging_group = QGroupBox("AR Aging Summary")
        ar_aging_layout = QFormLayout(ar_aging_group) 
        ar_aging_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.ar_aging_current_label = QLabel("Loading..."); ar_aging_layout.addRow("Current (Not Overdue):", self.ar_aging_current_label)
        self.ar_aging_1_30_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (1-30 days):", self.ar_aging_1_30_label)
        self.ar_aging_31_60_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (31-60 days):", self.ar_aging_31_60_label)
        self.ar_aging_61_90_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (61-90 days):", self.ar_aging_61_90_label)
        self.ar_aging_91_plus_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (91+ days):", self.ar_aging_91_plus_label)
        self.kpi_layout.addWidget(ar_aging_group, current_row, 0, 1, 2) 

        # AP Aging Group Box
        ap_aging_group = QGroupBox("AP Aging Summary")
        ap_aging_layout = QFormLayout(ap_aging_group) 
        ap_aging_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.ap_aging_current_label = QLabel("Loading..."); ap_aging_layout.addRow("Current (Not Overdue):", self.ap_aging_current_label)
        self.ap_aging_1_30_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (1-30 days):", self.ap_aging_1_30_label)
        self.ap_aging_31_60_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (31-60 days):", self.ap_aging_31_60_label)
        self.ap_aging_61_90_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (61-90 days):", self.ap_aging_61_90_label)
        self.ap_aging_91_plus_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (91+ days):", self.ap_aging_91_plus_label)
        self.kpi_layout.addWidget(ap_aging_group, current_row, 2, 1, 2) 
        
        container_layout.addStretch() 


    def _format_decimal_for_display(self, value: Optional[Decimal], currency_symbol: str = "") -> str:
        if value is None:
            return "N/A"
        prefix = f"{currency_symbol} " if currency_symbol else ""
        try:
            if not isinstance(value, Decimal) : value = Decimal(str(value))
            if not value.is_finite(): return "N/A (Infinite)" # Handle Decimal('Infinity')
            return f"{prefix}{value:,.2f}"
        except (TypeError, InvalidOperation): # Catch potential errors during conversion
            return f"{prefix}Error"


    @Slot()
    def _request_kpi_load(self):
        self._load_request_count += 1
        self.app_core.logger.info(f"DashboardWidget: _request_kpi_load called (Count: {self._load_request_count}). Setting labels to 'Loading...'.")
        
        self.refresh_button.setEnabled(False)
        labels_to_reset = [
            self.revenue_value_label, self.expenses_value_label, self.net_profit_value_label,
            self.cash_balance_value_label, self.ar_value_label, self.ap_value_label,
            self.ar_overdue_value_label, self.ap_overdue_value_label,
            self.ar_aging_current_label, self.ar_aging_1_30_label, self.ar_aging_31_60_label, 
            self.ar_aging_61_90_label, self.ar_aging_91_plus_label,
            self.ap_aging_current_label, self.ap_aging_1_30_label, self.ap_aging_31_60_label, 
            self.ap_aging_61_90_label, self.ap_aging_91_plus_label,
            self.current_ratio_label
        ]
        for label in labels_to_reset:
            if hasattr(self, 'app_core') and self.app_core and hasattr(self.app_core, 'logger'): # Defensive check
                 self.app_core.logger.debug(f"DashboardWidget: Resetting label to 'Loading...'")
            label.setText("Loading...")
        self.period_label.setText("Period: Loading...")
        self.base_currency_label.setText("Currency: Loading...")

        future = schedule_task_from_qt(self._fetch_kpis_data())
        if future:
            future.add_done_callback(
                lambda res: QMetaObject.invokeMethod(self.refresh_button, "setEnabled", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, True))
            )
        else:
            self.app_core.logger.error("DashboardWidget: Failed to schedule _fetch_kpis_data task.")
            self.refresh_button.setEnabled(True) 

    async def _fetch_kpis_data(self):
        self.app_core.logger.info("DashboardWidget: _fetch_kpis_data started.")
        kpi_data_result: Optional[DashboardKPIData] = None
        json_payload: Optional[str] = None
        try:
            if not self.app_core.dashboard_manager:
                self.app_core.logger.error("DashboardWidget: Dashboard Manager not available in _fetch_kpis_data.")
            else:
                kpi_data_result = await self.app_core.dashboard_manager.get_dashboard_kpis()
                if kpi_data_result:
                    self.app_core.logger.info(f"DashboardWidget: Fetched KPI data: Period='{kpi_data_result.kpi_period_description}', Revenue='{kpi_data_result.total_revenue_ytd}'")
                    json_payload = kpi_data_dto.model_dump_json()
                else:
                    self.app_core.logger.warning("DashboardWidget: DashboardManager.get_dashboard_kpis returned None.")
        except Exception as e:
            self.app_core.logger.error(f"DashboardWidget: Exception in _fetch_kpis_data during manager call: {e}", exc_info=True)
        
        self.app_core.logger.info(f"DashboardWidget: Queuing _update_kpi_display_slot with payload: {'JSON string' if json_payload else 'None'}")
        QMetaObject.invokeMethod(self, "_update_kpi_display_slot", 
                                 Qt.ConnectionType.QueuedConnection, 
                                 Q_ARG(str, json_payload if json_payload is not None else ""))

    @Slot(str)
    def _update_kpi_display_slot(self, kpi_data_json_str: str):
        self.app_core.logger.info(f"DashboardWidget: _update_kpi_display_slot called. Received JSON string length: {len(kpi_data_json_str)}")
        self.refresh_button.setEnabled(True)
        
        kpi_data_dto: Optional[DashboardKPIData] = None
        if kpi_data_json_str:
            try:
                kpi_data_dto = DashboardKPIData.model_validate_json(kpi_data_json_str)
                self.app_core.logger.info(f"DashboardWidget: Successfully deserialized KPI JSON to DTO.")
            except Exception as e:
                self.app_core.logger.error(f"DashboardWidget: Error deserializing/validating KPI JSON: '{kpi_data_json_str[:100]}...' - Error: {e}", exc_info=True)
        
        if kpi_data_dto:
            self.app_core.logger.info(f"DashboardWidget: Updating UI with KPI Data: Period='{kpi_data_dto.kpi_period_description}'")
            self.period_label.setText(f"Period: {kpi_data_dto.kpi_period_description}")
            self.base_currency_label.setText(f"Currency: {kpi_data_dto.base_currency}")
            bc_symbol = kpi_data_dto.base_currency 
            
            self.revenue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_revenue_ytd, bc_symbol))
            self.expenses_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_expenses_ytd, bc_symbol))
            self.net_profit_value_label.setText(self._format_decimal_for_display(kpi_data_dto.net_profit_ytd, bc_symbol))
            self.cash_balance_value_label.setText(self._format_decimal_for_display(kpi_data_dto.current_cash_balance, bc_symbol))
            self.ar_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_outstanding_ar, bc_symbol))
            self.ap_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_outstanding_ap, bc_symbol))
            self.ar_overdue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_ar_overdue, bc_symbol)) 
            self.ap_overdue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_ap_overdue, bc_symbol)) 

            # AR Aging
            self.ar_aging_current_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_current, bc_symbol))
            self.ar_aging_1_30_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_1_30, bc_symbol)) 
            self.ar_aging_31_60_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_31_60, bc_symbol))
            self.ar_aging_61_90_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_61_90, bc_symbol))
            self.ar_aging_91_plus_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_91_plus, bc_symbol))

            # AP Aging
            self.ap_aging_current_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_current, bc_symbol))
            self.ap_aging_1_30_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_1_30, bc_symbol)) 
            self.ap_aging_31_60_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_31_60, bc_symbol))
            self.ap_aging_61_90_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_61_90, bc_symbol))
            self.ap_aging_91_plus_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_91_plus, bc_symbol))
            
            # Current Ratio
            if kpi_data_dto.current_ratio is None:
                self.current_ratio_label.setText("N/A")
            elif not kpi_data_dto.current_ratio.is_finite(): 
                self.current_ratio_label.setText("N/A (Infinite)")
            else:
                self.current_ratio_label.setText(f"{kpi_data_dto.current_ratio:.2f} : 1")

            self.app_core.logger.info("DashboardWidget: UI labels updated with KPI data.")
        else:
            self.app_core.logger.warning("DashboardWidget: _update_kpi_display_slot called with no valid DTO. Setting error text.")
            error_text = "N/A - Data unavailable"
            self.period_label.setText("Period: N/A")
            self.base_currency_label.setText("Currency: N/A")
            for label in [self.revenue_value_label, self.expenses_value_label, self.net_profit_value_label,
                          self.cash_balance_value_label, self.ar_value_label, self.ap_value_label,
                          self.ar_overdue_value_label, self.ap_overdue_value_label,
                          self.ar_aging_current_label, self.ar_aging_1_30_label, self.ar_aging_31_60_label, 
                          self.ar_aging_61_90_label, self.ar_aging_91_plus_label,
                          self.ap_aging_current_label, self.ap_aging_1_30_label, self.ap_aging_31_60_label,
                          self.ap_aging_61_90_label, self.ap_aging_91_plus_label,
                          self.current_ratio_label]:
                label.setText(error_text)
            if kpi_data_json_str: 
                 QMessageBox.warning(self, "Dashboard Data Error", "Could not process Key Performance Indicators data.")
```

---
https://drive.google.com/file/d/1-vPle_bsfW5q1aXJ4JI9VB5cOYY3f7oU/view?usp=sharing, https://drive.google.com/file/d/13M2zztt62TD_vYJ_XLKtW4t2E53jIHl4/view?usp=sharing, https://drive.google.com/file/d/14hkYD6mD9rl8PpF-MsJD9nZAy-1sAr0T/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%2216tABsm1Plf_0fhtruoJyyxobBli3e8-7%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/18WGWMhYAOK7uwQ6JIahz-5MoVuK4BmWe/view?usp=sharing, https://drive.google.com/file/d/19ERvDxLdRedhVXYp9Gh0Xsg6tMIucGWO/view?usp=sharing, https://drive.google.com/file/d/19T9JbSrHCuXhHpzFMUh4Ti_0sDPDycSW/view?usp=sharing, https://drive.google.com/file/d/1D7GYodcMgZv3ROPPRJTYX0g9Rrsq8wJD/view?usp=sharing, https://drive.google.com/file/d/1EGOoM0TGqPgNBJzwxKdVO2u331Myhd4b/view?usp=sharing, https://drive.google.com/file/d/1Ivh39pjoqQ9z4_oj7w7hWc0zOje2-Xjb/view?usp=sharing, https://drive.google.com/file/d/1JsX5NYICgfKkbhMVeQ7ZONrbNZFb0ms3/view?usp=sharing, https://drive.google.com/file/d/1LzMu08SqY6E5ZuvISa4BsEHxatVPE9g_/view?usp=sharing, https://drive.google.com/file/d/1QyS0xlh6owfMif6KMlyXmE2Zx2hmcdza/view?usp=sharing, https://drive.google.com/file/d/1XeBi9hSp0z0vgqVVSFxhKP_ZwSv_s5B-/view?usp=sharing, https://drive.google.com/file/d/1Y9orpJ67I0XwezEBeUhyJs03DdjkAMhH/view?usp=sharing, https://drive.google.com/file/d/1YG0Vqa2pI5htxdsACYigsS2TMjDHxTcl/view?usp=sharing, https://drive.google.com/file/d/1YT2dDZirM9wxwWzYP0p9SDXSYOcG0Js4/view?usp=sharing, https://drive.google.com/file/d/1ZZODHjv2AX2Pn1cRh_0CJDTSzXRGjAt_/view?usp=sharing, https://drive.google.com/file/d/1_c8t-qcWtcVdVUEUkDQ760cjc0vL2Y9Z/view?usp=sharing, https://drive.google.com/file/d/1_qYJXTG-2GtEtmjV0Js5Hn_m_8ts9X0d/view?usp=sharing, https://drive.google.com/file/d/1bSRRtsWeJI9djXTDZTZTjZxnsWS3cvsV/view?usp=sharing, https://drive.google.com/file/d/1cp5LuyXlsbaa_wFSiIMxRlBFSro8qhXq/view?usp=sharing, https://drive.google.com/file/d/1ghGjh0MtEZSDVftjVx583ocaaCDK2j9X/view?usp=sharing, https://drive.google.com/file/d/1mbj5C_Pqa-lbGFf4obvSnpdGm-ALui7y/view?usp=sharing, https://drive.google.com/file/d/1pLih0cWs3ZiqnDKd9f2GEaR1GXCmD8KA/view?usp=sharing, https://drive.google.com/file/d/1sYr8SFT1d9ZMDHLfxOS6VjtwJ3920sFT/view?usp=sharing, https://drive.google.com/file/d/1uKfTNXg8Oaes7aGaoaPB6klSZzywizh9/view?usp=sharing, https://drive.google.com/file/d/1vTPAoLcEetjBj17-5nTa_Z6RS7ND5Wmz/view?usp=sharing, https://drive.google.com/file/d/1xbA8X7irZHUayYcfOWWfi4oWm18hFDo2/view?usp=sharing

