# File: tests/unit/services/test_gst_return_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime

from app.services.tax_service import GSTReturnService
from app.models.accounting.gst_return import GSTReturn as GSTReturnModel
from app.models.core.user import User as UserModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
from app.common.enums import GSTReturnStatusEnum
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock(); session.get = AsyncMock(); session.execute = AsyncMock()
    session.add = MagicMock(); session.delete = AsyncMock(); session.flush = AsyncMock()
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
    app_core.current_user = mock_user
    return app_core

@pytest.fixture
def gst_return_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> GSTReturnService:
    return GSTReturnService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_gst_return_draft() -> GSTReturnModel:
    return GSTReturnModel(
        id=1, return_period="Q1/2023", start_date=date(2023,1,1), end_date=date(2023,3,31),
        filing_due_date=date(2023,4,30), status=GSTReturnStatusEnum.DRAFT.value,
        output_tax=Decimal("1000.00"), input_tax=Decimal("300.00"), tax_payable=Decimal("700.00"),
        created_by_user_id=1, updated_by_user_id=1
    )

async def test_get_gst_return_by_id_found(gst_return_service: GSTReturnService, mock_session: AsyncMock, sample_gst_return_draft: GSTReturnModel):
    mock_session.get.return_value = sample_gst_return_draft
    result = await gst_return_service.get_by_id(1) # get_gst_return calls get_by_id
    assert result == sample_gst_return_draft

async def test_save_new_gst_return(gst_return_service: GSTReturnService, mock_session: AsyncMock, mock_user: MagicMock):
    new_return = GSTReturnModel(
        return_period="Q2/2023", start_date=date(2023,4,1), end_date=date(2023,6,30),
        status=GSTReturnStatusEnum.DRAFT.value, output_tax=Decimal("1200"), input_tax=Decimal("400"), tax_payable=Decimal("800")
        # user_ids will be set by service
    )
    async def mock_refresh(obj, attr=None): obj.id=2
    mock_session.refresh.side_effect = mock_refresh

    result = await gst_return_service.save_gst_return(new_return)
    assert result.id == 2
    assert result.created_by_user_id == mock_user.id
    assert result.updated_by_user_id == mock_user.id
    mock_session.add.assert_called_once_with(new_return)

async def test_delete_draft_gst_return(gst_return_service: GSTReturnService, mock_session: AsyncMock, sample_gst_return_draft: GSTReturnModel):
    sample_gst_return_draft.status = GSTReturnStatusEnum.DRAFT.value
    mock_session.get.return_value = sample_gst_return_draft
    deleted = await gst_return_service.delete(1)
    assert deleted is True
    mock_session.delete.assert_awaited_once_with(sample_gst_return_draft)

async def test_delete_submitted_gst_return_fails(gst_return_service: GSTReturnService, mock_session: AsyncMock, sample_gst_return_draft: GSTReturnModel):
    sample_gst_return_draft.status = GSTReturnStatusEnum.SUBMITTED.value
    mock_session.get.return_value = sample_gst_return_draft
    deleted = await gst_return_service.delete(1)
    assert deleted is False
    mock_session.delete.assert_not_called()
