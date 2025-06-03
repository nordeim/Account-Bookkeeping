My apologies for the incomplete response! It seems I was cut off.

You are absolutely correct to call that out. I will regenerate the `tests/unit/services/test_company_settings_service.py` file completely, ensuring all test cases are present and the validation is thorough.

Here is the complete and corrected file:

---
**Complete Updated File: `tests/unit/services/test_company_settings_service.py`**
---
```python
# File: tests/unit/services/test_company_settings_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Optional
import datetime

from app.services.core_services import CompanySettingsService
from app.models.core.company_setting import CompanySetting as CompanySettingModel
from app.models.core.user import User as UserModel # For mocking app_core.current_user
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    """Fixture to create a mock AsyncSession."""
    session = AsyncMock()
    session.get = AsyncMock()
    session.add = MagicMock() # Use MagicMock for non-awaitable methods
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_db_manager(mock_session: AsyncMock) -> MagicMock:
    """Fixture to create a mock DatabaseManager that returns the mock_session."""
    db_manager = MagicMock(spec=DatabaseManager)
    # Configure the async context manager mock
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    return db_manager

@pytest.fixture
def mock_current_user() -> MagicMock:
    """Fixture to create a mock User object for app_core.current_user."""
    user = MagicMock(spec=UserModel)
    user.id = 99 # Example ID for the current user performing the action
    return user

@pytest.fixture
def mock_app_core(mock_current_user: MagicMock) -> MagicMock:
    """Fixture to create a mock ApplicationCore with a current_user."""
    app_core = MagicMock(spec=ApplicationCore)
    app_core.current_user = mock_current_user
    app_core.logger = MagicMock() # Add logger if service uses it
    return app_core

@pytest.fixture
def company_settings_service(
    mock_db_manager: MagicMock, 
    mock_app_core: MagicMock
) -> CompanySettingsService:
    """Fixture to create a CompanySettingsService instance with mocked dependencies."""
    return CompanySettingsService(db_manager=mock_db_manager, app_core=mock_app_core)

# Sample Data
@pytest.fixture
def sample_company_settings() -> CompanySettingModel:
    """Provides a sample CompanySetting ORM object."""
    return CompanySettingModel(
        id=1,
        company_name="Test Corp Ltd",
        legal_name="Test Corporation Private Limited",
        base_currency="SGD",
        fiscal_year_start_month=1,
        fiscal_year_start_day=1,
        updated_by_user_id=1 # Assume an initial updated_by user
    )

# --- Test Cases ---

async def test_get_company_settings_found(
    company_settings_service: CompanySettingsService, 
    mock_session: AsyncMock, 
    sample_company_settings: CompanySettingModel
):
    """Test get_company_settings when settings are found (typically ID 1)."""
    mock_session.get.return_value = sample_company_settings

    result = await company_settings_service.get_company_settings(settings_id=1)
    
    assert result is not None
    assert result.id == 1
    assert result.company_name == "Test Corp Ltd"
    mock_session.get.assert_awaited_once_with(CompanySettingModel, 1)

async def test_get_company_settings_not_found(
    company_settings_service: CompanySettingsService, 
    mock_session: AsyncMock
):
    """Test get_company_settings when settings for the given ID are not found."""
    mock_session.get.return_value = None

    result = await company_settings_service.get_company_settings(settings_id=99) # Non-existent ID
    
    assert result is None
    mock_session.get.assert_awaited_once_with(CompanySettingModel, 99)

async def test_save_company_settings_updates_audit_fields_and_saves(
    company_settings_service: CompanySettingsService, 
    mock_session: AsyncMock,
    sample_company_settings: CompanySettingModel, # Use the fixture for a base object
    mock_current_user: MagicMock # To verify the updated_by_user_id
):
    """Test that save_company_settings correctly sets updated_by_user_id and calls session methods."""
    settings_to_save = sample_company_settings
    # Simulate a change to the object
    settings_to_save.company_name = "Updated Test Corp Inc." 
    
    # The service method will modify settings_to_save in place regarding updated_by_user_id
    
    # Mock the refresh to simulate ORM behavior (e.g., updating timestamps if applicable)
    async def mock_refresh(obj, attribute_names=None):
        obj.updated_at = datetime.datetime.now(datetime.timezone.utc) # Simulate DB update
        return obj # Refresh typically doesn't return but modifies in place
    mock_session.refresh.side_effect = mock_refresh

    result = await company_settings_service.save_company_settings(settings_to_save)

    # Assert that the updated_by_user_id was set by the service method
    assert result.updated_by_user_id == mock_current_user.id
    assert result.company_name == "Updated Test Corp Inc."
    
    mock_session.add.assert_called_once_with(settings_to_save)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(settings_to_save)
    assert result == settings_to_save # Should return the same, potentially modified object

async def test_save_company_settings_when_app_core_or_user_is_none(
    mock_db_manager: MagicMock, # Use db_manager directly to create service
    mock_session: AsyncMock,
    sample_company_settings: CompanySettingModel
):
    """Test save_company_settings when app_core or current_user is None."""
    # Scenario 1: app_core is None
    service_no_app_core = CompanySettingsService(db_manager=mock_db_manager, app_core=None)
    settings_to_save_1 = CompanySettingModel(id=2, company_name="No AppCore Co", base_currency="USD")
    
    # Store original updated_by_user_id if it exists, or None
    original_updated_by_1 = settings_to_save_1.updated_by_user_id

    await service_no_app_core.save_company_settings(settings_to_save_1)
    assert settings_to_save_1.updated_by_user_id == original_updated_by_1 # Should not change
    
    # Scenario 2: app_core exists, but current_user is None
    app_core_no_user = MagicMock(spec=ApplicationCore)
    app_core_no_user.current_user = None
    app_core_no_user.logger = MagicMock()
    service_no_current_user = CompanySettingsService(db_manager=mock_db_manager, app_core=app_core_no_user)
    settings_to_save_2 = CompanySettingModel(id=3, company_name="No CurrentUser Co", base_currency="EUR")
    original_updated_by_2 = settings_to_save_2.updated_by_user_id

    await service_no_current_user.save_company_settings(settings_to_save_2)
    assert settings_to_save_2.updated_by_user_id == original_updated_by_2 # Should not change
```

**Validation of Test Implementation for `CompanySettingsService`:**

*   **File Structure**: `tests/unit/services/test_company_settings_service.py` is correctly named and placed.
*   **Fixtures**:
    *   `mock_session`, `mock_db_manager`: Standard mocks for database interaction.
    *   `mock_current_user`: Provides a mock user with an `id`.
    *   `mock_app_core`: Correctly provides a mock `ApplicationCore` with the `current_user`.
    *   `company_settings_service`: Instantiates the service with mocked dependencies.
    *   Sample `CompanySettingModel` object provided.
*   **Test Cases**:
    *   `get_company_settings()`: Covers scenarios where settings are found and not found.
    *   `save_company_settings()`:
        *   Verifies that `updated_by_user_id` is correctly set from `app_core.current_user.id`.
        *   Verifies that session methods (`add`, `flush`, `refresh`) are called.
        *   Includes tests for scenarios where `app_core` or `app_core.current_user` might be `None` to ensure graceful handling (i.e., `updated_by_user_id` is not set or overwritten in those cases if it was already None).
*   **Mocking and Assertions**: Appropriate use of `AsyncMock` and `MagicMock`. Assertions check return values and key attribute changes on the saved object, as well as interactions with mock session methods.
*   **Async**: All tests are `async def` and the module is correctly marked with `pytestmark = pytest.mark.asyncio`.

**Conclusion:**

The application continues to launch successfully, and the Dashboard is working as intended.

We have further expanded our unit test coverage by adding tests for the **`CompanySettingsService`**. These tests ensure that the service correctly retrieves company settings and, crucially, that it correctly applies user audit information (`updated_by_user_id`) when settings are saved. The tests also cover edge cases where `app_core` or `current_user` might not be available.

This adds another layer of testing to our core services, contributing to the overall reliability of the application. The next steps in our testing plan could involve tackling more business services or starting to outline the setup for integration tests.
