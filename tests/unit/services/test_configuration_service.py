# File: tests/unit/services/test_configuration_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Optional

from app.services.core_services import ConfigurationService
from app.models.core.configuration import Configuration as ConfigurationModel
from app.core.database_manager import DatabaseManager

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    """Fixture to create a mock AsyncSession."""
    session = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
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
def config_service(mock_db_manager: MagicMock) -> ConfigurationService:
    """Fixture to create a ConfigurationService instance with a mocked db_manager."""
    return ConfigurationService(db_manager=mock_db_manager)

# Sample data
@pytest.fixture
def sample_config_entry_1() -> ConfigurationModel:
    return ConfigurationModel(
        id=1, config_key="TestKey1", config_value="TestValue1", description="Desc1"
    )

@pytest.fixture
def sample_config_entry_none_value() -> ConfigurationModel:
    return ConfigurationModel(
        id=2, config_key="TestKeyNone", config_value=None, description="DescNone"
    )

# --- Test Cases ---

async def test_get_config_by_key_found(
    config_service: ConfigurationService, 
    mock_session: AsyncMock, 
    sample_config_entry_1: ConfigurationModel
):
    """Test get_config_by_key when the configuration entry is found."""
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = sample_config_entry_1
    mock_session.execute.return_value = mock_execute_result

    result = await config_service.get_config_by_key("TestKey1")
    
    assert result == sample_config_entry_1
    mock_session.execute.assert_awaited_once() # Could add statement assertion if complex

async def test_get_config_by_key_not_found(config_service: ConfigurationService, mock_session: AsyncMock):
    """Test get_config_by_key when the configuration entry is not found."""
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_execute_result

    result = await config_service.get_config_by_key("NonExistentKey")
    
    assert result is None

async def test_get_config_value_found_with_value(
    config_service: ConfigurationService, 
    mock_session: AsyncMock, 
    sample_config_entry_1: ConfigurationModel
):
    """Test get_config_value when key is found and has a value."""
    mock_execute_result = AsyncMock() # Re-mock for this specific call path if get_config_by_key is called internally
    mock_execute_result.scalars.return_value.first.return_value = sample_config_entry_1
    mock_session.execute.return_value = mock_execute_result
    
    # Patch get_config_by_key if it's called internally by get_config_value
    with patch.object(config_service, 'get_config_by_key', AsyncMock(return_value=sample_config_entry_1)) as mock_get_by_key:
        result = await config_service.get_config_value("TestKey1", "Default")
        assert result == "TestValue1"
        mock_get_by_key.assert_awaited_once_with("TestKey1")


async def test_get_config_value_found_with_none_value(
    config_service: ConfigurationService, 
    mock_session: AsyncMock, 
    sample_config_entry_none_value: ConfigurationModel
):
    """Test get_config_value when key is found but its value is None."""
    with patch.object(config_service, 'get_config_by_key', AsyncMock(return_value=sample_config_entry_none_value)) as mock_get_by_key:
        result = await config_service.get_config_value("TestKeyNone", "DefaultValue")
        assert result == "DefaultValue" # Should return default
        mock_get_by_key.assert_awaited_once_with("TestKeyNone")

async def test_get_config_value_not_found(config_service: ConfigurationService, mock_session: AsyncMock):
    """Test get_config_value when key is not found."""
    with patch.object(config_service, 'get_config_by_key', AsyncMock(return_value=None)) as mock_get_by_key:
        result = await config_service.get_config_value("NonExistentKey", "DefaultValue")
        assert result == "DefaultValue"
        mock_get_by_key.assert_awaited_once_with("NonExistentKey")

async def test_get_config_value_not_found_no_default(config_service: ConfigurationService, mock_session: AsyncMock):
    """Test get_config_value when key is not found and no default is provided."""
    with patch.object(config_service, 'get_config_by_key', AsyncMock(return_value=None)) as mock_get_by_key:
        result = await config_service.get_config_value("NonExistentKey") # Default is None
        assert result is None
        mock_get_by_key.assert_awaited_once_with("NonExistentKey")

async def test_save_config(config_service: ConfigurationService, mock_session: AsyncMock):
    """Test saving a Configuration entry."""
    config_to_save = ConfigurationModel(config_key="NewKey", config_value="NewValue")
    
    async def mock_refresh(obj, attribute_names=None):
        obj.id = 10 # Simulate ID generation if it's an autoincrement PK
        obj.created_at = datetime.now()
        obj.updated_at = datetime.now()
        # Configuration model has updated_by, but service doesn't set it from app_core.
        # For this unit test, we assume it's either set on the object before calling save,
        # or handled by DB triggers/defaults if applicable.
    mock_session.refresh.side_effect = mock_refresh

    result = await config_service.save_config(config_to_save)

    mock_session.add.assert_called_once_with(config_to_save)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(config_to_save)
    assert result == config_to_save
    assert result.id == 10 # Check if refresh side_effect worked
