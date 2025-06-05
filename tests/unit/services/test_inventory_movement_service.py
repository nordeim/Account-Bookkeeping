# File: tests/unit/services/test_inventory_movement_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime
import logging

from app.services.business_services import InventoryMovementService
from app.models.business.inventory_movement import InventoryMovement as InventoryMovementModel
from app.models.business.product import Product as ProductModel # For context
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.common.enums import InventoryMovementTypeEnum

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
    return app_core

@pytest.fixture
def inventory_movement_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> InventoryMovementService:
    return InventoryMovementService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_product_orm() -> ProductModel:
    return ProductModel(id=1, product_code="ITEM001", name="Test Item", product_type="Inventory", created_by_user_id=1, updated_by_user_id=1)

@pytest.fixture
def sample_inventory_movement_orm(sample_product_orm: ProductModel) -> InventoryMovementModel:
    return InventoryMovementModel(
        id=1, product_id=sample_product_orm.id, 
        movement_date=date(2023, 1, 10),
        movement_type=InventoryMovementTypeEnum.PURCHASE.value,
        quantity=Decimal("10.00"), unit_cost=Decimal("5.00"), total_cost=Decimal("50.00"),
        created_by_user_id=1
    )

# --- Test Cases ---
async def test_get_movement_by_id_found(inventory_movement_service: InventoryMovementService, mock_session: AsyncMock, sample_inventory_movement_orm: InventoryMovementModel):
    mock_session.get.return_value = sample_inventory_movement_orm
    result = await inventory_movement_service.get_by_id(1)
    assert result == sample_inventory_movement_orm

async def test_get_all_movements(inventory_movement_service: InventoryMovementService, mock_session: AsyncMock, sample_inventory_movement_orm: InventoryMovementModel):
    mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_inventory_movement_orm]
    result = await inventory_movement_service.get_all()
    assert len(result) == 1
    assert result[0] == sample_inventory_movement_orm

async def test_save_new_movement(inventory_movement_service: InventoryMovementService, mock_session: AsyncMock, sample_product_orm: ProductModel):
    new_movement = InventoryMovementModel(
        product_id=sample_product_orm.id, movement_date=date(2023, 2, 2),
        movement_type=InventoryMovementTypeEnum.SALE.value, quantity=Decimal("-2.00"),
        unit_cost=Decimal("5.00"), total_cost=Decimal("10.00"),
        created_by_user_id=1
    )
    async def mock_refresh(obj, attr=None): obj.id = 2
    mock_session.refresh.side_effect = mock_refresh
    
    result = await inventory_movement_service.save(new_movement)
    mock_session.add.assert_called_once_with(new_movement)
    assert result.id == 2

async def test_save_movement_with_explicit_session(inventory_movement_service: InventoryMovementService, mock_session: AsyncMock, sample_inventory_movement_orm: InventoryMovementModel):
    # Pass the session explicitly
    result = await inventory_movement_service.save(sample_inventory_movement_orm, session=mock_session)
    mock_session.add.assert_called_once_with(sample_inventory_movement_orm)
    assert result == sample_inventory_movement_orm

async def test_delete_movement(inventory_movement_service: InventoryMovementService, mock_session: AsyncMock, sample_inventory_movement_orm: InventoryMovementModel):
    mock_session.get.return_value = sample_inventory_movement_orm
    deleted = await inventory_movement_service.delete(1)
    assert deleted is True
    mock_session.delete.assert_awaited_once_with(sample_inventory_movement_orm)
    inventory_movement_service.logger.warning.assert_called_once() # Check for warning log
