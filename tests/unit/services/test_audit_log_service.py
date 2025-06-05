# File: tests/unit/services/test_audit_log_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal 

from app.services.audit_services import AuditLogService
from app.models.audit.audit_log import AuditLog as AuditLogModel
from app.models.audit.data_change_history import DataChangeHistory as DataChangeHistoryModel
from app.models.core.user import User as UserModel
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore 
from app.utils.pydantic_models import AuditLogEntryData, DataChangeHistoryEntryData
from app.common.enums import DataChangeTypeEnum
import logging

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock()
    session.get = AsyncMock() 
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
def audit_log_service(mock_db_manager: MagicMock, mock_app_core: MagicMock) -> AuditLogService:
    return AuditLogService(db_manager=mock_db_manager, app_core=mock_app_core)

@pytest.fixture
def sample_user_orm() -> UserModel:
    return UserModel(id=1, username="test_user", full_name="Test User FullName", password_hash="hashed", is_active=True)

@pytest.fixture
def sample_audit_log_orm_create(sample_user_orm: UserModel) -> AuditLogModel:
    return AuditLogModel(
        id=1, user_id=sample_user_orm.id, action="Insert", entity_type="core.customer",
        entity_id=101, entity_name="Customer Alpha", 
        changes={"new": {"name": "Customer Alpha", "credit_limit": "1000.00", "is_active": True}},
        ip_address="127.0.0.1", timestamp=datetime(2023, 1, 1, 10, 0, 0)
    )

@pytest.fixture
def sample_audit_log_orm_update(sample_user_orm: UserModel) -> AuditLogModel:
    return AuditLogModel(
        id=2, user_id=sample_user_orm.id, action="Update", entity_type="core.customer",
        entity_id=101, entity_name="Customer Alpha V2", 
        changes={"old": {"name": "Customer Alpha", "credit_limit": "1000.00"}, "new": {"name": "Customer Alpha V2", "credit_limit": "1500.00"}},
        ip_address="127.0.0.1", timestamp=datetime(2023, 1, 1, 10, 5, 0)
    )

@pytest.fixture
def sample_audit_log_orm_delete(sample_user_orm: UserModel) -> AuditLogModel:
    return AuditLogModel(
        id=3, user_id=sample_user_orm.id, action="Delete", entity_type="core.customer",
        entity_id=102, entity_name="Customer Beta", 
        changes={"old": {"name": "Customer Beta"}},
        ip_address="127.0.0.1", timestamp=datetime(2023, 1, 1, 10, 10, 0)
    )
    
@pytest.fixture
def sample_data_change_history_orm(sample_user_orm: UserModel) -> DataChangeHistoryModel:
    return DataChangeHistoryModel(
        id=1, table_name="core.customer", record_id=101, field_name="credit_limit",
        old_value="500.00", new_value="1000.00", change_type=DataChangeTypeEnum.UPDATE.value,
        changed_by=sample_user_orm.id, changed_at=datetime(2023,1,1,10,0,0)
    )

# --- Tests for AuditLogService ---

async def test_get_audit_logs_paginated_no_filters(
    audit_log_service: AuditLogService, 
    mock_session: AsyncMock, 
    sample_audit_log_orm_create: AuditLogModel, 
    sample_user_orm: UserModel
):
    mock_count_execute = AsyncMock(); mock_count_execute.scalar_one.return_value = 1
    mock_data_execute = AsyncMock()
    mock_data_execute.mappings.return_value.all.return_value = [
        {AuditLogModel: sample_audit_log_orm_create, "username": sample_user_orm.username}
    ]
    mock_session.execute.side_effect = [mock_count_execute, mock_data_execute]

    logs, total_records = await audit_log_service.get_audit_logs_paginated(page=1, page_size=10)

    assert total_records == 1
    assert len(logs) == 1
    assert isinstance(logs[0], AuditLogEntryData)
    assert logs[0].id == sample_audit_log_orm_create.id
    assert logs[0].username == sample_user_orm.username
    assert "Record Created." in (logs[0].changes_summary or "")
    assert "name: 'Customer Alpha'" in (logs[0].changes_summary or "")
    assert "credit_limit: '1000.00'" in (logs[0].changes_summary or "")
    assert mock_session.execute.await_count == 2

async def test_get_audit_logs_paginated_with_user_filter(
    audit_log_service: AuditLogService, mock_session: AsyncMock
):
    await audit_log_service.get_audit_logs_paginated(user_id_filter=1)
    assert mock_session.execute.await_count == 2 

def test_format_changes_summary_created(audit_log_service: AuditLogService):
    changes = {"new": {"name": "Item X", "code": "X001", "price": "10.99"}}
    summary = audit_log_service._format_changes_summary(changes)
    assert summary == "Record Created. Details: name: 'Item X', code: 'X001', price: '10.99'"

def test_format_changes_summary_deleted(audit_log_service: AuditLogService):
    changes = {"old": {"name": "Item Y", "code": "Y001"}}
    summary = audit_log_service._format_changes_summary(changes)
    assert summary == "Record Deleted."

def test_format_changes_summary_modified_few(audit_log_service: AuditLogService):
    changes = {"old": {"status": "Active", "notes": "Old note"}, "new": {"status": "Inactive", "notes": "Old note"}}
    summary = audit_log_service._format_changes_summary(changes)
    assert summary == "'status': 'Active' -> 'Inactive'"

def test_format_changes_summary_modified_many(audit_log_service: AuditLogService):
    changes = {
        "old": {"f1": "a", "f2": "b", "f3": "c", "f4": "d", "f5": "e"},
        "new": {"f1": "A", "f2": "B", "f3": "C", "f4": "D", "f5": "E"}
    }
    summary = audit_log_service._format_changes_summary(changes)
    assert "'f1': 'a' -> 'A'; 'f2': 'b' -> 'B'; 'f3': 'c' -> 'C'; ...and 2 other field(s)." == summary

def test_format_changes_summary_no_meaningful_change(audit_log_service: AuditLogService):
    changes = {"old": {"updated_at": "ts1"}, "new": {"updated_at": "ts2"}} 
    summary = audit_log_service._format_changes_summary(changes)
    assert "updated_at" in summary # Current impl shows this

def test_format_changes_summary_no_diff_fields(audit_log_service: AuditLogService):
    changes = {"old": {"field": "value"}, "new": {"field": "value"}}
    summary = audit_log_service._format_changes_summary(changes)
    assert summary == "No changes detailed or only sensitive fields updated."


def test_format_changes_summary_none(audit_log_service: AuditLogService):
    summary = audit_log_service._format_changes_summary(None)
    assert summary is None

async def test_get_data_change_history_paginated(
    audit_log_service: AuditLogService, mock_session: AsyncMock, 
    sample_data_change_history_orm: DataChangeHistoryModel, sample_user_orm: UserModel
):
    mock_count_execute = AsyncMock(); mock_count_execute.scalar_one.return_value = 1
    mock_data_execute = AsyncMock()
    mock_data_execute.mappings.return_value.all.return_value = [
        {DataChangeHistoryModel: sample_data_change_history_orm, "changed_by_username": sample_user_orm.username}
    ]
    mock_session.execute.side_effect = [mock_count_execute, mock_data_execute]

    history, total_records = await audit_log_service.get_data_change_history_paginated()
    assert total_records == 1
    assert len(history) == 1
    assert history[0].field_name == "credit_limit"
    assert history[0].change_type == DataChangeTypeEnum.UPDATE
    assert history[0].changed_by_username == sample_user_orm.username

async def test_audit_log_service_unsupported_methods(audit_log_service: AuditLogService):
    """Test that add, update, delete methods for AuditLog/DataChangeHistory raise NotImplementedError."""
    with pytest.raises(NotImplementedError):
        await audit_log_service.add(MagicMock(spec=AuditLogModel))
    with pytest.raises(NotImplementedError):
        await audit_log_service.update(MagicMock(spec=AuditLogModel))
    with pytest.raises(NotImplementedError):
        await audit_log_service.delete(1) # Argument is id_val: int
    with pytest.raises(NotImplementedError):
        await audit_log_service.get_all()
    
    # Check get_by_id - it has a minimal implementation for completeness
    mock_session = audit_log_service.db_manager.session.return_value.__aenter__.return_value
    mock_session.get.side_effect = [None, None] # Return None for both AuditLog and DataChangeHistory get
    result = await audit_log_service.get_by_id(123)
    assert result is None
    assert mock_session.get.await_count == 2
    mock_session.get.assert_any_await(AuditLogModel, 123)
    mock_session.get.assert_any_await(DataChangeHistoryModel, 123)
