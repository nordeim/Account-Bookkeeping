# File: tests/unit/services/test_journal_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date, datetime

from app.services.journal_service import JournalService
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine
from app.models.accounting.account import Account
from app.models.accounting.recurring_pattern import RecurringPattern
from app.models.accounting.fiscal_period import FiscalPeriod
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore # For mocking app_core
import logging

# Mark all tests in this module as asyncio
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
    # Mock other services if JournalService directly calls them via app_core
    # For now, assuming direct dependencies are passed or not used in tested methods
    return app_core

@pytest.fixture
def journal_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> JournalService:
    return JournalService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_account_orm() -> Account:
    return Account(id=101, code="1110", name="Bank", account_type="Asset", sub_type="Cash", is_active=True, created_by_user_id=1,updated_by_user_id=1)

@pytest.fixture
def sample_journal_entry_orm(sample_account_orm: Account) -> JournalEntry:
    je = JournalEntry(
        id=1, entry_no="JE001", journal_type="General", entry_date=date(2023,1,10),
        fiscal_period_id=1, description="Test JE", is_posted=False,
        created_by_user_id=1, updated_by_user_id=1
    )
    je.lines = [
        JournalEntryLine(id=1, journal_entry_id=1, line_number=1, account_id=sample_account_orm.id, debit_amount=Decimal("100.00"), credit_amount=Decimal("0.00"), account=sample_account_orm),
        JournalEntryLine(id=2, journal_entry_id=1, line_number=2, account_id=201, credit_amount=Decimal("100.00"), debit_amount=Decimal("0.00")) # Assume account 201 exists
    ]
    return je

@pytest.fixture
def sample_recurring_pattern_orm(sample_journal_entry_orm: JournalEntry) -> RecurringPattern:
    return RecurringPattern(
        id=1, name="Monthly Rent", template_entry_id=sample_journal_entry_orm.id,
        frequency="Monthly", interval_value=1, start_date=date(2023,1,1),
        next_generation_date=date(2023,2,1), is_active=True,
        created_by_user_id=1, updated_by_user_id=1,
        template_journal_entry=sample_journal_entry_orm # Link template JE
    )

# --- Test Cases ---

async def test_get_je_by_id_found(journal_service: JournalService, mock_session: AsyncMock, sample_journal_entry_orm: JournalEntry):
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_journal_entry_orm
    result = await journal_service.get_by_id(1)
    assert result == sample_journal_entry_orm
    assert result.entry_no == "JE001"

async def test_get_all_summary_no_filters(journal_service: JournalService, mock_session: AsyncMock, sample_journal_entry_orm: JournalEntry):
    mock_row_mapping = MagicMock()
    mock_row_mapping._asdict.return_value = { # Simulate RowMapping._asdict() if needed, or direct dict
        "id": sample_journal_entry_orm.id, "entry_no": sample_journal_entry_orm.entry_no,
        "entry_date": sample_journal_entry_orm.entry_date, "description": sample_journal_entry_orm.description,
        "journal_type": sample_journal_entry_orm.journal_type, "is_posted": sample_journal_entry_orm.is_posted,
        "total_debits": Decimal("100.00")
    }
    mock_session.execute.return_value.mappings.return_value.all.return_value = [mock_row_mapping]

    summaries = await journal_service.get_all_summary()
    assert len(summaries) == 1
    assert summaries[0]["entry_no"] == "JE001"
    assert summaries[0]["status"] == "Draft"

async def test_save_new_journal_entry(journal_service: JournalService, mock_session: AsyncMock, sample_account_orm: Account):
    new_je = JournalEntry(
        journal_type="General", entry_date=date(2023,2,5), fiscal_period_id=2,
        description="New test JE", created_by_user_id=1, updated_by_user_id=1
    )
    new_je.lines = [
        JournalEntryLine(account_id=sample_account_orm.id, debit_amount=Decimal("50.00"))
    ]
    async def mock_refresh(obj, attribute_names=None):
        obj.id = 2
        obj.entry_no = "JE002" # Simulate sequence
        if attribute_names and 'lines' in attribute_names:
            for line in obj.lines: line.id = line.id or (len(obj.lines) + 100) # Simulate line ID
    mock_session.refresh.side_effect = mock_refresh
    
    result = await journal_service.save(new_je)
    mock_session.add.assert_called_once_with(new_je)
    assert result.id == 2
    assert result.entry_no == "JE002"

async def test_delete_draft_je(journal_service: JournalService, mock_session: AsyncMock, sample_journal_entry_orm: JournalEntry):
    sample_journal_entry_orm.is_posted = False # Ensure draft
    mock_session.get.return_value = sample_journal_entry_orm
    
    deleted = await journal_service.delete(1)
    assert deleted is True
    mock_session.delete.assert_awaited_once_with(sample_journal_entry_orm)

async def test_delete_posted_je_fails(journal_service: JournalService, mock_session: AsyncMock, mock_app_core: MagicMock, sample_journal_entry_orm: JournalEntry):
    sample_journal_entry_orm.is_posted = True # Posted
    mock_session.get.return_value = sample_journal_entry_orm
    
    deleted = await journal_service.delete(1)
    assert deleted is False
    mock_session.delete.assert_not_called()
    mock_app_core.logger.warning.assert_called_once()

async def test_get_account_balance(journal_service: JournalService, mock_session: AsyncMock, sample_account_orm: Account):
    sample_account_orm.opening_balance = Decimal("100.00")
    sample_account_orm.opening_balance_date = date(2023,1,1)
    mock_session.execute.return_value.first.return_value = (sample_account_orm.opening_balance, sample_account_orm.opening_balance_date) # For the account fetch
    
    # For the JE activity sum
    mock_je_sum_result = AsyncMock()
    mock_je_sum_result.scalar_one_or_none.return_value = Decimal("50.00") # Net debit activity
    mock_session.execute.side_effect = [mock_session.execute.return_value, mock_je_sum_result] # First for account, second for sum

    balance = await journal_service.get_account_balance(sample_account_orm.id, date(2023,1,31))
    assert balance == Decimal("150.00") # 100 OB + 50 Activity

async def test_get_recurring_patterns_due(journal_service: JournalService, mock_session: AsyncMock, sample_recurring_pattern_orm: RecurringPattern):
    mock_session.execute.return_value.scalars.return_value.unique.return_value.all.return_value = [sample_recurring_pattern_orm]
    
    patterns = await journal_service.get_recurring_patterns_due(date(2023,2,1))
    assert len(patterns) == 1
    assert patterns[0].name == "Monthly Rent"
