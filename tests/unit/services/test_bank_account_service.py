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
