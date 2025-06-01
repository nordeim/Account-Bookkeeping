# app/services/audit_services.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any, TYPE_CHECKING, Dict, Tuple, Union # Added Union
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, aliased
from datetime import datetime, date

from app.core.database_manager import DatabaseManager
from app.models.audit.audit_log import AuditLog
from app.models.audit.data_change_history import DataChangeHistory
from app.models.core.user import User 
from app.services import IRepository 
from app.utils.pydantic_models import AuditLogEntryData, DataChangeHistoryEntryData
from app.utils.result import Result
from app.common.enums import DataChangeTypeEnum

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class IAuditLogRepository(IRepository[AuditLog, int]): 
    @abstractmethod
    async def get_audit_logs_paginated(
        self,
        user_id_filter: Optional[int] = None,
        action_filter: Optional[str] = None,
        entity_type_filter: Optional[str] = None,
        entity_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None,
        end_date_filter: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[AuditLogEntryData], int]: pass

class IDataChangeHistoryRepository(IRepository[DataChangeHistory, int]): 
    @abstractmethod
    async def get_data_change_history_paginated(
        self,
        table_name_filter: Optional[str] = None,
        record_id_filter: Optional[int] = None,
        changed_by_user_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None,
        end_date_filter: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[DataChangeHistoryEntryData], int]: pass


class AuditLogService(IAuditLogRepository, IDataChangeHistoryRepository): 
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[Union[AuditLog, DataChangeHistory]]:
        async with self.db_manager.session() as session:
            # Attempt to get AuditLog first, then DataChangeHistory if context isn't clear
            # This method is less ideal for a service implementing multiple specific repositories
            log_entry = await session.get(AuditLog, id_val)
            if log_entry:
                return log_entry
            history_entry = await session.get(DataChangeHistory, id_val)
            return history_entry # Will be None if not found in DataChangeHistory either

    async def get_all(self) -> List[Union[AuditLog, DataChangeHistory]]: raise NotImplementedError("Use paginated methods for audit logs.")
    async def add(self, entity: Union[AuditLog, DataChangeHistory]) -> Union[AuditLog, DataChangeHistory]: raise NotImplementedError("Audit logs are system-generated.")
    async def update(self, entity: Union[AuditLog, DataChangeHistory]) -> Union[AuditLog, DataChangeHistory]: raise NotImplementedError("Audit logs are immutable.")
    async def delete(self, id_val: int) -> bool: raise NotImplementedError("Audit logs should generally not be deleted programmatically.")

    def _format_changes_summary(self, changes_jsonb: Optional[Dict[str, Any]]) -> Optional[str]:
        if not changes_jsonb:
            return None
        
        summary_parts = []
        old_data = changes_jsonb.get('old')
        new_data = changes_jsonb.get('new')

        if isinstance(new_data, dict) and isinstance(old_data, dict): 
            for key, new_val in new_data.items():
                if key in ["created_at", "updated_at", "password_hash"]: continue 
                old_val = old_data.get(key)
                if old_val != new_val: 
                    summary_parts.append(f"'{key}': '{str(old_val)[:50]}' -> '{str(new_val)[:50]}'")
        elif isinstance(new_data, dict): 
            summary_parts.append("New record created.")
        elif isinstance(old_data, dict): 
            summary_parts.append("Record deleted.")

        return "; ".join(summary_parts) if summary_parts else "No changes detailed or only timestamp/sensitive fields changed."


    async def get_audit_logs_paginated(
        self,
        user_id_filter: Optional[int] = None,
        action_filter: Optional[str] = None,
        entity_type_filter: Optional[str] = None,
        entity_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None,
        end_date_filter: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[AuditLogEntryData], int]:
        async with self.db_manager.session() as session:
            conditions = []
            if user_id_filter is not None:
                conditions.append(AuditLog.user_id == user_id_filter)
            if action_filter:
                conditions.append(AuditLog.action.ilike(f"%{action_filter}%"))
            if entity_type_filter:
                conditions.append(AuditLog.entity_type.ilike(f"%{entity_type_filter}%"))
            if entity_id_filter is not None:
                conditions.append(AuditLog.entity_id == entity_id_filter)
            if start_date_filter:
                conditions.append(AuditLog.timestamp >= start_date_filter)
            if end_date_filter:
                conditions.append(AuditLog.timestamp <= end_date_filter)

            UserAlias = aliased(User)
            
            count_stmt = select(func.count(AuditLog.id))
            if conditions:
                count_stmt = count_stmt.where(and_(*conditions))
            total_count_res = await session.execute(count_stmt)
            total_count = total_count_res.scalar_one()

            stmt = select(AuditLog, UserAlias.username.label("username")).outerjoin(
                UserAlias, AuditLog.user_id == UserAlias.id
            )
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(AuditLog.timestamp.desc()) # type: ignore
            if page_size > 0:
                 stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            
            result = await session.execute(stmt)
            log_entries: List[AuditLogEntryData] = []
            for row in result.mappings().all(): 
                log_orm = row[AuditLog]
                username = row.username if row.username else (f"User ID: {log_orm.user_id}" if log_orm.user_id else "System/Unknown")
                
                log_entries.append(AuditLogEntryData(
                    id=log_orm.id,
                    timestamp=log_orm.timestamp,
                    username=username,
                    action=log_orm.action,
                    entity_type=log_orm.entity_type,
                    entity_id=log_orm.entity_id,
                    entity_name=log_orm.entity_name,
                    changes_summary=self._format_changes_summary(log_orm.changes),
                    ip_address=log_orm.ip_address
                ))
            return log_entries, total_count

    async def get_data_change_history_paginated(
        self,
        table_name_filter: Optional[str] = None,
        record_id_filter: Optional[int] = None,
        changed_by_user_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None,
        end_date_filter: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[DataChangeHistoryEntryData], int]:
        async with self.db_manager.session() as session:
            conditions = []
            if table_name_filter:
                conditions.append(DataChangeHistory.table_name.ilike(f"%{table_name_filter}%"))
            if record_id_filter is not None:
                conditions.append(DataChangeHistory.record_id == record_id_filter)
            if changed_by_user_id_filter is not None:
                conditions.append(DataChangeHistory.changed_by == changed_by_user_id_filter)
            if start_date_filter:
                conditions.append(DataChangeHistory.changed_at >= start_date_filter)
            if end_date_filter:
                conditions.append(DataChangeHistory.changed_at <= end_date_filter)

            UserAlias = aliased(User)

            count_stmt = select(func.count(DataChangeHistory.id))
            if conditions:
                count_stmt = count_stmt.where(and_(*conditions))
            total_count_res = await session.execute(count_stmt)
            total_count = total_count_res.scalar_one()


            stmt = select(DataChangeHistory, UserAlias.username.label("changed_by_username")).outerjoin(
                UserAlias, DataChangeHistory.changed_by == UserAlias.id
            )
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(DataChangeHistory.changed_at.desc()) # type: ignore
            if page_size > 0:
                 stmt = stmt.limit(page_size).offset((page - 1) * page_size)

            result = await session.execute(stmt)
            history_entries: List[DataChangeHistoryEntryData] = []
            for row in result.mappings().all():
                hist_orm = row[DataChangeHistory]
                username = row.changed_by_username if row.changed_by_username else (f"User ID: {hist_orm.changed_by}" if hist_orm.changed_by else "System/Unknown")
                
                history_entries.append(DataChangeHistoryEntryData(
                    id=hist_orm.id,
                    changed_at=hist_orm.changed_at,
                    table_name=hist_orm.table_name,
                    record_id=hist_orm.record_id,
                    field_name=hist_orm.field_name,
                    old_value=hist_orm.old_value,
                    new_value=hist_orm.new_value,
                    change_type=DataChangeTypeEnum(hist_orm.change_type), 
                    changed_by_username=username
                ))
            return history_entries, total_count

