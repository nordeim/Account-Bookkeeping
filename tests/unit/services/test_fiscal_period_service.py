# File: tests/unit/services/test_fiscal_period_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal # For context with other financial models

from app.services.fiscal_period_service import FiscalPeriodService
from app.models.accounting.fiscal_period import FiscalPeriod as FiscalPeriodModel
from app.models.accounting.fiscal_year import FiscalYear as FiscalYearModel
from app.core.database_manager import DatabaseManager

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
def fiscal_period_service(mock_db_manager: MagicMock) -> FiscalPeriodService:
    # FiscalPeriodService only takes db_manager
    return FiscalPeriodService(db_manager=mock_db_manager)

# Sample Data
@pytest.fixture
def sample_fy_2023() -> FiscalYearModel:
    return FiscalYearModel(id=1, year_name="FY2023", start_date=date(2023,1,1), end_date=date(2023,12,31), created_by_user_id=1, updated_by_user_id=1)

@pytest.fixture
def sample_period_jan_2023(sample_fy_2023: FiscalYearModel) -> FiscalPeriodModel:
    return FiscalPeriodModel(id=1, fiscal_year_id=sample_fy_2023.id, name="Jan 2023", 
                             start_date=date(2023,1,1), end_date=date(2023,1,31),
                             period_type="Month", status="Open", period_number=1,
                             created_by_user_id=1, updated_by_user_id=1)

@pytest.fixture
def sample_period_q1_2023(sample_fy_2023: FiscalYearModel) -> FiscalPeriodModel:
    return FiscalPeriodModel(id=2, fiscal_year_id=sample_fy_2023.id, name="Q1 2023",
                             start_date=date(2023,1,1), end_date=date(2023,3,31),
                             period_type="Quarter", status="Closed", period_number=1,
                             created_by_user_id=1, updated_by_user_id=1)

# --- Test Cases ---

async def test_get_fiscal_period_by_id_found(
    fiscal_period_service: FiscalPeriodService, 
    mock_session: AsyncMock, 
    sample_period_jan_2023: FiscalPeriodModel
):
    mock_session.get.return_value = sample_period_jan_2023
    result = await fiscal_period_service.get_by_id(1)
    assert result == sample_period_jan_2023
    mock_session.get.assert_awaited_once_with(FiscalPeriodModel, 1)

async def test_get_fiscal_period_by_id_not_found(fiscal_period_service: FiscalPeriodService, mock_session: AsyncMock):
    mock_session.get.return_value = None
    result = await fiscal_period_service.get_by_id(99)
    assert result is None

async def test_get_all_fiscal_periods(
    fiscal_period_service: FiscalPeriodService, 
    mock_session: AsyncMock, 
    sample_period_jan_2023: FiscalPeriodModel, 
    sample_period_q1_2023: FiscalPeriodModel
):
    mock_execute_result = AsyncMock()
    # Service orders by start_date
    mock_execute_result.scalars.return_value.all.return_value = [sample_period_jan_2023, sample_period_q1_2023]
    mock_session.execute.return_value = mock_execute_result
    result = await fiscal_period_service.get_all()
    assert len(result) == 2
    assert result[0] == sample_period_jan_2023

async def test_add_fiscal_period(fiscal_period_service: FiscalPeriodService, mock_session: AsyncMock):
    new_period_data = FiscalPeriodModel(
        fiscal_year_id=1, name="Feb 2023", start_date=date(2023,2,1), end_date=date(2023,2,28),
        period_type="Month", status="Open", period_number=2,
        created_by_user_id=1, updated_by_user_id=1 # Assume these are set by manager
    )
    async def mock_refresh(obj, attribute_names=None): obj.id = 100 # Simulate ID generation
    mock_session.refresh.side_effect = mock_refresh
    
    result = await fiscal_period_service.add(new_period_data)
    mock_session.add.assert_called_once_with(new_period_data)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(new_period_data)
    assert result == new_period_data
    assert result.id == 100

async def test_delete_fiscal_period_open(
    fiscal_period_service: FiscalPeriodService, 
    mock_session: AsyncMock, 
    sample_period_jan_2023: FiscalPeriodModel
):
    sample_period_jan_2023.status = "Open" # Ensure it's open
    mock_session.get.return_value = sample_period_jan_2023
    deleted = await fiscal_period_service.delete(1)
    assert deleted is True
    mock_session.delete.assert_awaited_once_with(sample_period_jan_2023)

async def test_delete_fiscal_period_archived_fails(
    fiscal_period_service: FiscalPeriodService, 
    mock_session: AsyncMock, 
    sample_period_jan_2023: FiscalPeriodModel
):
    sample_period_jan_2023.status = "Archived"
    mock_session.get.return_value = sample_period_jan_2023
    deleted = await fiscal_period_service.delete(1)
    assert deleted is False # Cannot delete archived period
    mock_session.delete.assert_not_called()

async def test_get_fiscal_period_by_date_found(
    fiscal_period_service: FiscalPeriodService, 
    mock_session: AsyncMock, 
    sample_period_jan_2023: FiscalPeriodModel
):
    sample_period_jan_2023.status = "Open"
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = sample_period_jan_2023
    mock_session.execute.return_value = mock_execute_result
    
    result = await fiscal_period_service.get_by_date(date(2023, 1, 15))
    assert result == sample_period_jan_2023

async def test_get_fiscal_period_by_date_not_found_or_not_open(
    fiscal_period_service: FiscalPeriodService, mock_session: AsyncMock
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_execute_result
    
    result = await fiscal_period_service.get_by_date(date(2024, 1, 15))
    assert result is None

async def test_get_fiscal_year_by_year_value(
    fiscal_period_service: FiscalPeriodService, # Testing method within FiscalPeriodService
    mock_session: AsyncMock, 
    sample_fy_2023: FiscalYearModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = sample_fy_2023
    mock_session.execute.return_value = mock_execute_result
    
    result = await fiscal_period_service.get_fiscal_year(2023)
    assert result == sample_fy_2023
    # Could assert that the SQL query used 'LIKE %2023%'

async def test_get_fiscal_periods_for_year(
    fiscal_period_service: FiscalPeriodService, 
    mock_session: AsyncMock,
    sample_period_jan_2023: FiscalPeriodModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.all.return_value = [sample_period_jan_2023]
    mock_session.execute.return_value = mock_execute_result

    result = await fiscal_period_service.get_fiscal_periods_for_year(1, period_type="Month")
    assert len(result) == 1
    assert result[0] == sample_period_jan_2023
