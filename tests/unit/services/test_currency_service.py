# File: tests/unit/services/test_currency_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
import datetime

from app.services.accounting_services import CurrencyService
from app.models.accounting.currency import Currency as CurrencyModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore # For mocking app_core
from app.models.core.user import User as UserModel # For mocking current_user

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    """Fixture to create a mock AsyncSession."""
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
    """Fixture to create a mock DatabaseManager that returns the mock_session."""
    db_manager = MagicMock(spec=DatabaseManager)
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def mock_user() -> MagicMock:
    user = MagicMock(spec=UserModel)
    user.id = 123 # Example user ID
    return user

@pytest.fixture
def mock_app_core(mock_user: MagicMock) -> MagicMock:
    """Fixture to create a mock ApplicationCore with a current_user."""
    app_core = MagicMock(spec=ApplicationCore)
    app_core.current_user = mock_user
    return app_core

@pytest.fixture
def currency_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> CurrencyService:
    """Fixture to create a CurrencyService instance with mocked dependencies."""
    return CurrencyService(db_manager=mock_db_manager, app_core=mock_app_core)

# --- Test Cases ---

async def test_get_currency_by_id_found(currency_service: CurrencyService, mock_session: AsyncMock):
    """Test get_by_id when Currency is found."""
    expected_currency = CurrencyModel(code="SGD", name="Singapore Dollar", symbol="$")
    mock_session.get.return_value = expected_currency

    result = await currency_service.get_by_id("SGD")
    
    assert result == expected_currency
    mock_session.get.assert_awaited_once_with(CurrencyModel, "SGD")

async def test_get_currency_by_id_not_found(currency_service: CurrencyService, mock_session: AsyncMock):
    """Test get_by_id when Currency is not found."""
    mock_session.get.return_value = None

    result = await currency_service.get_by_id("XXX")
    
    assert result is None
    mock_session.get.assert_awaited_once_with(CurrencyModel, "XXX")

async def test_get_all_currencies(currency_service: CurrencyService, mock_session: AsyncMock):
    """Test get_all returns a list of Currencies ordered by name."""
    curr1 = CurrencyModel(code="AUD", name="Australian Dollar", symbol="$")
    curr2 = CurrencyModel(code="SGD", name="Singapore Dollar", symbol="$")
    mock_execute_result = AsyncMock()
    # Service orders by name, so mock should reflect that for this test's assertion simplicity
    mock_execute_result.scalars.return_value.all.return_value = [curr1, curr2] 
    mock_session.execute.return_value = mock_execute_result

    result = await currency_service.get_all()

    assert len(result) == 2
    assert result[0].code == "AUD"
    assert result[1].code == "SGD"
    mock_session.execute.assert_awaited_once()
    # Could assert statement for order_by(Currency.name)

async def test_get_all_active_currencies(currency_service: CurrencyService, mock_session: AsyncMock):
    """Test get_all_active returns only active currencies."""
    curr1_active = CurrencyModel(code="SGD", name="Singapore Dollar", symbol="$", is_active=True)
    curr2_inactive = CurrencyModel(code="OLD", name="Old Currency", symbol="O", is_active=False) # Not expected
    curr3_active = CurrencyModel(code="USD", name="US Dollar", symbol="$", is_active=True)
    
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.all.return_value = [curr1_active, curr3_active]
    mock_session.execute.return_value = mock_execute_result

    result = await currency_service.get_all_active()

    assert len(result) == 2
    assert all(c.is_active for c in result)
    assert result[0].code == "SGD" # Assuming mock returns them ordered by name already
    assert result[1].code == "USD"
    mock_session.execute.assert_awaited_once()
    # Assert that the query contained "is_active == True"

async def test_add_currency(currency_service: CurrencyService, mock_session: AsyncMock, mock_user: MagicMock):
    """Test adding a new Currency, checking audit user IDs."""
    new_currency_data = CurrencyModel(code="XYZ", name="New Currency", symbol="X")
    
    async def mock_refresh(obj, attribute_names=None):
        obj.id = "XYZ" # Simulate ID being set (though for Currency, code is ID)
        obj.created_at = datetime.datetime.now()
        obj.updated_at = datetime.datetime.now()
        # The service itself sets user_ids before add, so check them on new_currency_data
    mock_session.refresh.side_effect = mock_refresh

    result = await currency_service.add(new_currency_data)

    assert new_currency_data.created_by_user_id == mock_user.id
    assert new_currency_data.updated_by_user_id == mock_user.id
    mock_session.add.assert_called_once_with(new_currency_data)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(new_currency_data)
    assert result == new_currency_data

async def test_update_currency(currency_service: CurrencyService, mock_session: AsyncMock, mock_user: MagicMock):
    """Test updating an existing Currency, checking updated_by_user_id."""
    existing_currency = CurrencyModel(id="SGD", code="SGD", name="Singapore Dollar", symbol="$", created_by_user_id=99)
    existing_currency.name = "Singapore Dollar (Updated)" # Simulate change
    
    async def mock_refresh(obj, attribute_names=None):
        obj.updated_at = datetime.datetime.now()
    mock_session.refresh.side_effect = mock_refresh

    result = await currency_service.update(existing_currency)

    assert result.updated_by_user_id == mock_user.id
    assert result.name == "Singapore Dollar (Updated)"
    mock_session.add.assert_called_once_with(existing_currency)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(existing_currency)

async def test_delete_currency_found(currency_service: CurrencyService, mock_session: AsyncMock):
    """Test deleting an existing Currency."""
    currency_to_delete = CurrencyModel(code="DEL", name="Delete Me", symbol="D")
    mock_session.get.return_value = currency_to_delete

    result = await currency_service.delete("DEL")

    assert result is True
    mock_session.get.assert_awaited_once_with(CurrencyModel, "DEL")
    mock_session.delete.assert_awaited_once_with(currency_to_delete)

async def test_delete_currency_not_found(currency_service: CurrencyService, mock_session: AsyncMock):
    """Test deleting a non-existent Currency."""
    mock_session.get.return_value = None

    result = await currency_service.delete("NON")

    assert result is False
    mock_session.get.assert_awaited_once_with(CurrencyModel, "NON")
    mock_session.delete.assert_not_called()
