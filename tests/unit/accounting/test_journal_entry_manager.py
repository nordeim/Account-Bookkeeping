# File: tests/unit/accounting/test_journal_entry_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from datetime import date

from app.accounting.journal_entry_manager import JournalEntryManager
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData
from app.utils.result import Result
from app.models.accounting.journal_entry import JournalEntry
from app.models.accounting.fiscal_period import FiscalPeriod
from app.models.accounting.account import Account
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_journal_service() -> AsyncMock: return AsyncMock(spec=JournalService)

@pytest.fixture
def mock_account_service() -> AsyncMock: return AsyncMock(spec=AccountService)

@pytest.fixture
def mock_fiscal_period_service() -> AsyncMock: return AsyncMock(spec=FiscalPeriodService)

@pytest.fixture
def mock_app_core() -> MagicMock:
    app_core = MagicMock(spec=ApplicationCore)
    app_core.logger = MagicMock(spec=logging.Logger)
    app_core.db_manager = MagicMock()
    app_core.db_manager.execute_scalar = AsyncMock()
    return app_core

@pytest.fixture
def journal_entry_manager(
    mock_journal_service: AsyncMock,
    mock_account_service: AsyncMock,
    mock_fiscal_period_service: AsyncMock,
    mock_app_core: MagicMock
) -> JournalEntryManager:
    return JournalEntryManager(
        journal_service=mock_journal_service,
        account_service=mock_account_service,
        fiscal_period_service=mock_fiscal_period_service,
        app_core=mock_app_core
    )

@pytest.fixture
def valid_je_create_dto() -> JournalEntryData:
    return JournalEntryData(
        journal_type="General",
        entry_date=date(2023, 1, 20),
        description="Test Entry",
        user_id=1,
        lines=[
            JournalEntryLineData(account_id=101, debit_amount=Decimal("150.00")),
            JournalEntryLineData(account_id=201, credit_amount=Decimal("150.00")),
        ]
    )

@pytest.fixture
def sample_posted_je() -> JournalEntry:
    je = JournalEntry(
        id=5, entry_no="JE-POSTED-01", entry_date=date(2023,1,10), is_posted=True, created_by_user_id=1, updated_by_user_id=1, fiscal_period_id=1
    )
    je.lines = [
        JournalEntryLine(id=10, account_id=101, debit_amount=Decimal(100)),
        JournalEntryLine(id=11, account_id=201, credit_amount=Decimal(100))
    ]
    return je

# --- Test Cases ---

async def test_create_journal_entry_success(
    journal_entry_manager: JournalEntryManager,
    mock_fiscal_period_service: AsyncMock,
    mock_account_service: AsyncMock,
    mock_app_core: MagicMock,
    valid_je_create_dto: JournalEntryData
):
    # Setup mocks for validation pass
    mock_fiscal_period_service.get_by_date.return_value = FiscalPeriod(id=1, name="Jan 2023", start_date=date(2023,1,1), end_date=date(2023,1,31), period_type="Month", status="Open", period_number=1, created_by_user_id=1, updated_by_user_id=1)
    mock_account_service.get_by_id.side_effect = lambda id: Account(id=id, is_active=True, code=str(id), name=f"Acc {id}", account_type="Asset", created_by_user_id=1, updated_by_user_id=1)
    mock_app_core.db_manager.execute_scalar.return_value = "JE00001"
    
    # Mock the final save call
    async def mock_save(je_orm):
        je_orm.id = 1 # Simulate DB assigning an ID
        return je_orm
    # The manager doesn't call service.save, it works with the session directly
    # So we need to mock the session on the db_manager used inside create_journal_entry
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    journal_entry_manager.app_core.db_manager.session.return_value.__aenter__.return_value = mock_session

    result = await journal_entry_manager.create_journal_entry(valid_je_create_dto)

    assert result.is_success
    assert result.value is not None
    assert result.value.entry_no == "JE00001"
    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited_once()

async def test_create_journal_entry_no_open_period(journal_entry_manager: JournalEntryManager, mock_fiscal_period_service: AsyncMock, valid_je_create_dto: JournalEntryData):
    mock_fiscal_period_service.get_by_date.return_value = None
    mock_session = AsyncMock()
    journal_entry_manager.app_core.db_manager.session.return_value.__aenter__.return_value = mock_session

    result = await journal_entry_manager.create_journal_entry(valid_je_create_dto)

    assert not result.is_success
    assert "No open fiscal period" in result.errors[0]

async def test_post_journal_entry_success(journal_entry_manager: JournalEntryManager, mock_session: AsyncMock, sample_posted_je: JournalEntry):
    sample_posted_je.is_posted = False # Start as draft for the test
    mock_session.get.side_effect = [
        sample_posted_je, # First get for the JE itself
        FiscalPeriod(id=1, status="Open") # Second get for the fiscal period
    ]

    result = await journal_entry_manager.post_journal_entry(5, user_id=1, session=mock_session)
    
    assert result.is_success
    assert result.value.is_posted is True
    assert result.value.updated_by_user_id == 1
    mock_session.add.assert_called_once_with(sample_posted_je)
    
async def test_reverse_journal_entry_success(journal_entry_manager: JournalEntryManager, mock_session: AsyncMock, sample_posted_je: JournalEntry):
    # Setup
    mock_session.get.return_value = sample_posted_je
    mock_fiscal_period_service = journal_entry_manager.fiscal_period_service
    mock_fiscal_period_service.get_by_date.return_value = FiscalPeriod(id=2, status="Open") # Mock for reversal date's period
    journal_entry_manager.app_core.db_manager.execute_scalar.return_value = "JE-REV-01" # Mock sequence for reversal JE

    # Mock the create_journal_entry call within the reversal method
    reversal_je_mock = MagicMock(spec=JournalEntry, id=6)
    journal_entry_manager.create_journal_entry = AsyncMock(return_value=Result.success(reversal_je_mock))

    reversal_date = date(2023, 2, 1)
    reversal_desc = "Reversal"
    user_id = 2

    # Execute
    result = await journal_entry_manager.reverse_journal_entry(sample_posted_je.id, reversal_date, reversal_desc, user_id)
    
    # Assert
    assert result.is_success
    assert result.value == reversal_je_mock
    # Check that original entry was modified
    assert sample_posted_je.is_reversed is True
    assert sample_posted_je.reversing_entry_id == 6
    assert sample_posted_je.updated_by_user_id == 2
    # Check that the create call was correct
    create_call_args = journal_entry_manager.create_journal_entry.call_args.args[0]
    assert isinstance(create_call_args, JournalEntryData)
    assert create_call_args.lines[0].credit_amount == sample_posted_je.lines[0].debit_amount
    assert create_call_args.lines[1].debit_amount == sample_posted_je.lines[1].credit_amount
