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
