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
