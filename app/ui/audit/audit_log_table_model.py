# File: app/ui/audit/audit_log_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Optional, Any
from datetime import datetime

from app.utils.pydantic_models import AuditLogEntryData

class AuditLogTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[AuditLogEntryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = [
            "ID", "Timestamp", "User", "Action", "Entity Type", 
            "Entity ID", "Entity Name", "Changes Summary", "IP Address"
        ]
        self._data: List[AuditLogEntryData] = data or []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        log_entry: AuditLogEntryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(log_entry.id)
            if col == 1: # Timestamp
                ts = log_entry.timestamp
                return ts.strftime('%d/%m/%Y %H:%M:%S') if isinstance(ts, datetime) else str(ts)
            if col == 2: return log_entry.username or "N/A"
            if col == 3: return log_entry.action
            if col == 4: return log_entry.entity_type
            if col == 5: return str(log_entry.entity_id) if log_entry.entity_id is not None else ""
            if col == 6: return log_entry.entity_name or ""
            if col == 7: return log_entry.changes_summary or ""
            if col == 8: return log_entry.ip_address or ""
            return ""

        elif role == Qt.ItemDataRole.UserRole: # Store full DTO for potential detail view
            return log_entry
        
        return None

    def get_log_entry_at_row(self, row: int) -> Optional[AuditLogEntryData]:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None

    def update_data(self, new_data: List[AuditLogEntryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()
