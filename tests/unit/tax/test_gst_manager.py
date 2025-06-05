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
