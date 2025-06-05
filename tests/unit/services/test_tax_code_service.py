# File: tests/unit/services/test_tax_code_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from decimal import Decimal
import datetime

from app.services.tax_service import TaxCodeService
from app.models.accounting.tax_code import TaxCode as TaxCodeModel
from app.models.core.user import User as UserModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock(); session.get = AsyncMock(); session.execute = AsyncMock()
    session.add = MagicMock(); session.delete = MagicMock(); session.flush = AsyncMock()
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
    user = MagicMock(spec=UserModel); user.id = 1; return user

@pytest.fixture
def mock_app_core(mock_user: MagicMock) -> MagicMock:
    app_core = MagicMock(spec=ApplicationCore); app_core.logger = MagicMock(spec=logging.Logger)
    app_core.current_user = mock_user # For audit fields in save
    return app_core

@pytest.fixture
def tax_code_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> TaxCodeService:
    return TaxCodeService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_tax_code_sr() -> TaxCodeModel:
    return TaxCodeModel(id=1, code="SR", description="Standard Rate", tax_type="GST", rate=Decimal("9.00"), is_active=True, created_by_user_id=1, updated_by_user_id=1)

@pytest.fixture
def sample_tax_code_zr_inactive() -> TaxCodeModel:
    return TaxCodeModel(id=2, code="ZR", description="Zero Rate", tax_type="GST", rate=Decimal("0.00"), is_active=False, created_by_user_id=1, updated_by_user_id=1)

async def test_get_tax_code_by_id_found(tax_code_service: TaxCodeService, mock_session: AsyncMock, sample_tax_code_sr: TaxCodeModel):
    mock_session.get.return_value = sample_tax_code_sr
    result = await tax_code_service.get_by_id(1)
    assert result == sample_tax_code_sr

async def test_get_tax_code_by_code_active_found(tax_code_service: TaxCodeService, mock_session: AsyncMock, sample_tax_code_sr: TaxCodeModel):
    mock_session.execute.return_value.scalars.return_value.first.return_value = sample_tax_code_sr
    result = await tax_code_service.get_tax_code("SR")
    assert result == sample_tax_code_sr

async def test_get_tax_code_by_code_inactive_returns_none(tax_code_service: TaxCodeService, mock_session: AsyncMock, sample_tax_code_zr_inactive: TaxCodeModel):
    # get_tax_code filters for is_active=True
    mock_session.execute.return_value.scalars.return_value.first.return_value = None 
    result = await tax_code_service.get_tax_code("ZR") # Even if ZR exists but is inactive
    assert result is None

async def test_get_all_active_tax_codes(tax_code_service: TaxCodeService, mock_session: AsyncMock, sample_tax_code_sr: TaxCodeModel):
    mock_session.execute.return_value.scalars.return_value.all.return_value = [sample_tax_code_sr]
    results = await tax_code_service.get_all() # get_all in service implies active_only
    assert len(results) == 1
    assert results[0].code == "SR"

async def test_save_new_tax_code(tax_code_service: TaxCodeService, mock_session: AsyncMock, mock_user: MagicMock):
    new_tc = TaxCodeModel(code="EX", description="Exempt", tax_type="GST", rate=Decimal("0.00"))
    # Audit fields (created_by_user_id, updated_by_user_id) are set by service.save()

    async def mock_refresh(obj, attr=None): obj.id=3 # Simulate DB generated ID
    mock_session.refresh.side_effect = mock_refresh
    
    result = await tax_code_service.save(new_tc)
    assert result.id == 3
    assert result.created_by_user_id == mock_user.id
    assert result.updated_by_user_id == mock_user.id
    mock_session.add.assert_called_once_with(new_tc)

async def test_delete_tax_code_deactivates(tax_code_service: TaxCodeService, mock_session: AsyncMock, sample_tax_code_sr: TaxCodeModel):
    sample_tax_code_sr.is_active = True
    mock_session.get.return_value = sample_tax_code_sr
    tax_code_service.save = AsyncMock(return_value=sample_tax_code_sr) # Mock save as it's called by delete

    deleted_flag = await tax_code_service.delete(1)
    assert deleted_flag is True
    assert sample_tax_code_sr.is_active is False
    tax_code_service.save.assert_awaited_once_with(sample_tax_code_sr)
