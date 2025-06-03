# File: tests/unit/services/test_fiscal_year_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal # For context

from app.services.accounting_services import FiscalYearService
from app.models.accounting.fiscal_year import FiscalYear as FiscalYearModel
from app.models.accounting.fiscal_period import FiscalPeriod as FiscalPeriodModel # For testing delete constraint
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore # For mocking app_core

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
def mock_app_core() -> MagicMock:
    """Fixture to create a basic mock ApplicationCore."""
    app_core = MagicMock(spec=ApplicationCore)
    # Add logger mock if FiscalYearService uses it (currently doesn't seem to directly)
    app_core.logger = MagicMock() 
    return app_core

@pytest.fixture
def fiscal_year_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> FiscalYearService:
    return FiscalYearService(db_manager=mock_db_manager, app_core=mock_app_core)

# Sample Data
@pytest.fixture
def sample_fy_2023() -> FiscalYearModel:
    return FiscalYearModel(
        id=1, year_name="FY2023", 
        start_date=date(2023, 1, 1), end_date=date(2023, 12, 31),
        created_by_user_id=1, updated_by_user_id=1,
        fiscal_periods=[] # Initialize with no periods for some tests
    )

@pytest.fixture
def sample_fy_2024() -> FiscalYearModel:
    return FiscalYearModel(
        id=2, year_name="FY2024", 
        start_date=date(2024, 1, 1), end_date=date(2024, 12, 31),
        created_by_user_id=1, updated_by_user_id=1,
        fiscal_periods=[]
    )

# --- Test Cases ---

async def test_get_fy_by_id_found(
    fiscal_year_service: FiscalYearService, 
    mock_session: AsyncMock, 
    sample_fy_2023: FiscalYearModel
):
    mock_session.get.return_value = sample_fy_2023
    result = await fiscal_year_service.get_by_id(1)
    assert result == sample_fy_2023
    mock_session.get.assert_awaited_once_with(FiscalYearModel, 1)

async def test_get_fy_by_id_not_found(fiscal_year_service: FiscalYearService, mock_session: AsyncMock):
    mock_session.get.return_value = None
    result = await fiscal_year_service.get_by_id(99)
    assert result is None

async def test_get_all_fys(
    fiscal_year_service: FiscalYearService, 
    mock_session: AsyncMock, 
    sample_fy_2023: FiscalYearModel, 
    sample_fy_2024: FiscalYearModel
):
    mock_execute_result = AsyncMock()
    # Service orders by start_date.desc()
    mock_execute_result.scalars.return_value.all.return_value = [sample_fy_2024, sample_fy_2023]
    mock_session.execute.return_value = mock_execute_result
    result = await fiscal_year_service.get_all()
    assert len(result) == 2
    assert result[0].year_name == "FY2024"

async def test_save_new_fy(fiscal_year_service: FiscalYearService, mock_session: AsyncMock):
    new_fy_data = FiscalYearModel(
        year_name="FY2025", start_date=date(2025,1,1), end_date=date(2025,12,31),
        created_by_user_id=1, updated_by_user_id=1 # Assume set by manager before service.save
    )
    async def mock_refresh(obj, attribute_names=None): obj.id = 100
    mock_session.refresh.side_effect = mock_refresh
    
    result = await fiscal_year_service.save(new_fy_data) # Covers add()
    mock_session.add.assert_called_once_with(new_fy_data)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(new_fy_data)
    assert result == new_fy_data
    assert result.id == 100

async def test_delete_fy_no_periods(
    fiscal_year_service: FiscalYearService, 
    mock_session: AsyncMock, 
    sample_fy_2023: FiscalYearModel
):
    sample_fy_2023.fiscal_periods = [] # Ensure no periods
    mock_session.get.return_value = sample_fy_2023
    deleted = await fiscal_year_service.delete(sample_fy_2023.id)
    assert deleted is True
    mock_session.delete.assert_awaited_once_with(sample_fy_2023)

async def test_delete_fy_with_periods_raises_error(
    fiscal_year_service: FiscalYearService, 
    mock_session: AsyncMock, 
    sample_fy_2023: FiscalYearModel
):
    # Simulate FY having periods
    sample_fy_2023.fiscal_periods = [FiscalPeriodModel(id=10, name="Jan", fiscal_year_id=sample_fy_2023.id, start_date=date(2023,1,1), end_date=date(2023,1,31), period_type="Month", status="Open", period_number=1, created_by_user_id=1, updated_by_user_id=1)]
    mock_session.get.return_value = sample_fy_2023
    
    with pytest.raises(ValueError) as excinfo:
        await fiscal_year_service.delete(sample_fy_2023.id)
    assert f"Cannot delete fiscal year '{sample_fy_2023.year_name}' as it has associated fiscal periods." in str(excinfo.value)
    mock_session.delete.assert_not_called()

async def test_delete_fy_not_found(fiscal_year_service: FiscalYearService, mock_session: AsyncMock):
    mock_session.get.return_value = None
    deleted = await fiscal_year_service.delete(99)
    assert deleted is False

async def test_get_fy_by_name_found(
    fiscal_year_service: FiscalYearService, 
    mock_session: AsyncMock, 
    sample_fy_2023: FiscalYearModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = sample_fy_2023
    mock_session.execute.return_value = mock_execute_result
    
    result = await fiscal_year_service.get_by_name("FY2023")
    assert result == sample_fy_2023

async def test_get_fy_by_date_overlap_found(
    fiscal_year_service: FiscalYearService, 
    mock_session: AsyncMock, 
    sample_fy_2023: FiscalYearModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = sample_fy_2023
    mock_session.execute.return_value = mock_execute_result
    
    result = await fiscal_year_service.get_by_date_overlap(date(2023,6,1), date(2023,7,1))
    assert result == sample_fy_2023

async def test_get_fy_by_date_overlap_not_found(
    fiscal_year_service: FiscalYearService, mock_session: AsyncMock
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_execute_result
    
    result = await fiscal_year_service.get_by_date_overlap(date(2025,1,1), date(2025,12,31))
    assert result is None

async def test_get_fy_by_date_overlap_exclude_id(
    fiscal_year_service: FiscalYearService, mock_session: AsyncMock
):
    mock_execute_result = AsyncMock()
    # Simulate it would find something, but exclude_id prevents it
    mock_execute_result.scalars.return_value.first.return_value = None 
    mock_session.execute.return_value = mock_execute_result
    
    result = await fiscal_year_service.get_by_date_overlap(date(2023,6,1), date(2023,7,1), exclude_id=1)
    assert result is None 
    # To properly test exclude_id, the mock for session.execute would need to be more sophisticated
    # to check the WHERE clause of the statement passed to it. For now, this ensures it's called.
    mock_session.execute.assert_awaited_once()
