# File: tests/unit/services/test_dimension_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from datetime import date, datetime # For created_at/updated_at in model

from app.services.accounting_services import DimensionService
from app.models.accounting.dimension import Dimension as DimensionModel
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
    app_core = MagicMock(spec=ApplicationCore)
    app_core.logger = MagicMock() # If service uses logger
    return app_core

@pytest.fixture
def dimension_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> DimensionService:
    return DimensionService(db_manager=mock_db_manager, app_core=mock_app_core)

# Sample Data
@pytest.fixture
def sample_dim_dept_fin() -> DimensionModel:
    return DimensionModel(
        id=1, dimension_type="Department", code="FIN", name="Finance", 
        created_by=1, updated_by=1 # Assuming UserAuditMixin fields are set
    )

@pytest.fixture
def sample_dim_dept_hr() -> DimensionModel:
    return DimensionModel(
        id=2, dimension_type="Department", code="HR", name="Human Resources", 
        is_active=False, created_by=1, updated_by=1
    )

@pytest.fixture
def sample_dim_proj_alpha() -> DimensionModel:
    return DimensionModel(
        id=3, dimension_type="Project", code="ALPHA", name="Project Alpha", 
        created_by=1, updated_by=1
    )

# --- Test Cases ---

async def test_get_dimension_by_id_found(
    dimension_service: DimensionService, mock_session: AsyncMock, sample_dim_dept_fin: DimensionModel
):
    mock_session.get.return_value = sample_dim_dept_fin
    result = await dimension_service.get_by_id(1)
    assert result == sample_dim_dept_fin
    mock_session.get.assert_awaited_once_with(DimensionModel, 1)

async def test_get_dimension_by_id_not_found(dimension_service: DimensionService, mock_session: AsyncMock):
    mock_session.get.return_value = None
    result = await dimension_service.get_by_id(99)
    assert result is None

async def test_get_all_dimensions(
    dimension_service: DimensionService, mock_session: AsyncMock, 
    sample_dim_dept_fin: DimensionModel, sample_dim_proj_alpha: DimensionModel
):
    mock_execute_result = AsyncMock()
    # Service orders by dimension_type, then code
    mock_execute_result.scalars.return_value.all.return_value = [sample_dim_dept_fin, sample_dim_proj_alpha]
    mock_session.execute.return_value = mock_execute_result
    result = await dimension_service.get_all()
    assert len(result) == 2
    assert result[0].code == "FIN"

async def test_add_dimension(dimension_service: DimensionService, mock_session: AsyncMock):
    new_dim_data = DimensionModel(
        dimension_type="Location", code="SG", name="Singapore Office",
        created_by=1, updated_by=1 # Assume set by manager
    )
    async def mock_refresh(obj, attribute_names=None): obj.id = 101
    mock_session.refresh.side_effect = mock_refresh
    
    result = await dimension_service.add(new_dim_data)
    mock_session.add.assert_called_once_with(new_dim_data)
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(new_dim_data)
    assert result == new_dim_data
    assert result.id == 101

async def test_delete_dimension_found(
    dimension_service: DimensionService, mock_session: AsyncMock, sample_dim_dept_fin: DimensionModel
):
    mock_session.get.return_value = sample_dim_dept_fin
    deleted = await dimension_service.delete(1)
    assert deleted is True
    mock_session.delete.assert_awaited_once_with(sample_dim_dept_fin)

async def test_get_distinct_dimension_types(dimension_service: DimensionService, mock_session: AsyncMock):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.all.return_value = ["Department", "Project"]
    mock_session.execute.return_value = mock_execute_result
    
    result = await dimension_service.get_distinct_dimension_types()
    assert result == ["Department", "Project"]

async def test_get_dimensions_by_type_active_only(
    dimension_service: DimensionService, mock_session: AsyncMock, sample_dim_dept_fin: DimensionModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.all.return_value = [sample_dim_dept_fin] # sample_dim_dept_hr is inactive
    mock_session.execute.return_value = mock_execute_result
    
    result = await dimension_service.get_dimensions_by_type("Department", active_only=True)
    assert len(result) == 1
    assert result[0] == sample_dim_dept_fin

async def test_get_dimensions_by_type_all(
    dimension_service: DimensionService, mock_session: AsyncMock, 
    sample_dim_dept_fin: DimensionModel, sample_dim_dept_hr: DimensionModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.all.return_value = [sample_dim_dept_fin, sample_dim_dept_hr]
    mock_session.execute.return_value = mock_execute_result
    
    result = await dimension_service.get_dimensions_by_type("Department", active_only=False)
    assert len(result) == 2

async def test_get_by_type_and_code_found(
    dimension_service: DimensionService, mock_session: AsyncMock, sample_dim_dept_fin: DimensionModel
):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = sample_dim_dept_fin
    mock_session.execute.return_value = mock_execute_result
    
    result = await dimension_service.get_by_type_and_code("Department", "FIN")
    assert result == sample_dim_dept_fin

async def test_get_by_type_and_code_not_found(dimension_service: DimensionService, mock_session: AsyncMock):
    mock_execute_result = AsyncMock()
    mock_execute_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_execute_result
    
    result = await dimension_service.get_by_type_and_code("Department", "NONEXISTENT")
    assert result is None
