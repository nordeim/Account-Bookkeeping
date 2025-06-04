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
