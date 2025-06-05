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
