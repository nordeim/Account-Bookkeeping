# File: tests/unit/services/test_exchange_rate_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime

from app.services.accounting_services import ExchangeRateService
from app.models.accounting.exchange_rate import ExchangeRate as ExchangeRateModel
from app.models.accounting.currency import Currency as CurrencyModel # For creating related objects if needed
from app.models.core.user import User as UserModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
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
def mock_user() -> MagicMock:
    user = MagicMock(spec=UserModel)
    user.id = 789 # Example admin/system user ID for auditing
    return user

@pytest.fixture
def mock_app_core(mock_user: MagicMock) -> MagicMock:
    app_core = MagicMock(spec=ApplicationCore)
    app_core.current_user = mock_user
    return app_core

@pytest.fixture
def exchange_rate_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> ExchangeRateService:
    return ExchangeRateService(db_manager=mock_db_manager, app_core=mock_app_core)

# Sample data
@pytest.fixture
def sample_exchange_rate_1() -> ExchangeRateModel:
    return ExchangeRateModel(
        id=1, from_currency_code="USD", to_currency_code="SGD", 
        rate_date=date(2023, 1, 1), exchange_rate_value=Decimal("1.350000")
    )

@pytest.fixture
def sample_exchange_rate_2() -> ExchangeRateModel:
    return ExchangeRateModel(
        id=2, from_currency_code="EUR", to_currency_code="SGD", 
        rate_date=date(2023, 1, 1), exchange_rate_value=Decimal("1.480000")
    )

# --- Test Cases ---

async def test_get_exchange_rate_by_id_found(
    exchange_rate_service: ExchangeRateService, 
    mock_session: AsyncMock, 
    sample_exchange_rate_1: ExchangeRateModel
):
    mock_session.get.return_value = sample_exchange_rate_1
    result = await exchange_rate_service.get_by_id(1)
    assert result == sample_exchange_rate_1
    mock_session.get.assert_awaited_once_with(ExchangeRateModel, 1)

async def test_get_exchange_rate_by_id_not_found(exchange_rate_service: ExchangeRateService, mock_session: AsyncMock):
    mock_session.get.return_value = None
    result = await exchange_rate_service.get_by_id(99)
    assert result is None

async def test_get_all_exchange_rates(
    exchange_rate_service: ExchangeRateService, 
    mock_session: AsyncMock, 
    sample_exchange_rate_1: ExchangeRateModel, 
    sample_exchange_rate_2: ExchangeRateModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.all.return_value = [sample_exchange_rate_1, sample_exchange_rate_2]
    mock_session.execute.return_value = mock_execute_result

    result = await exchange_rate_service.get_all()
    assert len(result) == 2
    assert result[0] == sample_exchange_rate_1

async def test_save_new_exchange_rate(
    exchange_rate_service: ExchangeRateService, 
    mock_session: AsyncMock, 
    mock_user: MagicMock
):
    new_rate_data = ExchangeRateModel(
        from_currency_code="JPY", to_currency_code="SGD", 
        rate_date=date(2023, 1, 2), exchange_rate_value=Decimal("0.010000")
        # ID will be None initially
    )
    # Simulate id and audit fields being set after add/flush/refresh
    async def mock_refresh(obj, attribute_names=None):
        obj.id = 3 # Simulate ID generation
        obj.created_at = datetime.now()
        obj.updated_at = datetime.now()
        # Service sets created_by and updated_by before calling session.add
    mock_session.refresh.side_effect = mock_refresh
    
    result = await exchange_rate_service.save(new_rate_data)

    assert result.id == 3
    assert result.created_by_user_id == mock_user.id
    assert result.updated_by_user_id == mock_user.id
    mock_session.add.assert_called_once_with(new_rate_data)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(new_rate_data)

async def test_save_update_exchange_rate(
    exchange_rate_service: ExchangeRateService, 
    mock_session: AsyncMock, 
    sample_exchange_rate_1: ExchangeRateModel, 
    mock_user: MagicMock
):
    sample_exchange_rate_1.exchange_rate_value = Decimal("1.360000") # Modify
    original_created_by = sample_exchange_rate_1.created_by_user_id # Should remain unchanged

    async def mock_refresh(obj, attribute_names=None):
        obj.updated_at = datetime.now()
    mock_session.refresh.side_effect = mock_refresh

    result = await exchange_rate_service.save(sample_exchange_rate_1)
    
    assert result.exchange_rate_value == Decimal("1.360000")
    assert result.updated_by_user_id == mock_user.id
    if original_created_by: # If it was set
        assert result.created_by_user_id == original_created_by
    
    mock_session.add.assert_called_once_with(sample_exchange_rate_1)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(sample_exchange_rate_1)

async def test_delete_exchange_rate_found(
    exchange_rate_service: ExchangeRateService, 
    mock_session: AsyncMock, 
    sample_exchange_rate_1: ExchangeRateModel
):
    mock_session.get.return_value = sample_exchange_rate_1
    deleted = await exchange_rate_service.delete(1)
    assert deleted is True
    mock_session.get.assert_awaited_once_with(ExchangeRateModel, 1)
    mock_session.delete.assert_awaited_once_with(sample_exchange_rate_1)

async def test_delete_exchange_rate_not_found(exchange_rate_service: ExchangeRateService, mock_session: AsyncMock):
    mock_session.get.return_value = None
    deleted = await exchange_rate_service.delete(99)
    assert deleted is False
    mock_session.get.assert_awaited_once_with(ExchangeRateModel, 99)
    mock_session.delete.assert_not_called()

async def test_get_rate_for_date_found(
    exchange_rate_service: ExchangeRateService, 
    mock_session: AsyncMock, 
    sample_exchange_rate_1: ExchangeRateModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = sample_exchange_rate_1
    mock_session.execute.return_value = mock_execute_result
    
    result = await exchange_rate_service.get_rate_for_date("USD", "SGD", date(2023, 1, 1))
    
    assert result == sample_exchange_rate_1
    mock_session.execute.assert_awaited_once()
    # More detailed assertion could check the statement construction if needed

async def test_get_rate_for_date_not_found(exchange_rate_service: ExchangeRateService, mock_session: AsyncMock):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_execute_result
    
    result = await exchange_rate_service.get_rate_for_date("USD", "EUR", date(2023, 1, 1))
    
    assert result is None
