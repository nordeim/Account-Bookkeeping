# File: app/ui/audit/data_change_history_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Optional, Any
from datetime import datetime

from app.utils.pydantic_models import DataChangeHistoryEntryData
from app.common.enums import DataChangeTypeEnum

class DataChangeHistoryTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[DataChangeHistoryEntryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = [
            "ID", "Changed At", "Table", "Record ID", "Field", 
            "Old Value", "New Value", "Change Type", "Changed By"
        ]
        self._data: List[DataChangeHistoryEntryData] = data or []

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
            
        history_entry: DataChangeHistoryEntryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(history_entry.id)
            if col == 1: # Changed At
                ts = history_entry.changed_at
                return ts.strftime('%d/%m/%Y %H:%M:%S') if isinstance(ts, datetime) else str(ts)
            if col == 2: return history_entry.table_name
            if col == 3: return str(history_entry.record_id)
            if col == 4: return history_entry.field_name
            if col == 5: return str(history_entry.old_value)[:200] if history_entry.old_value is not None else "" # Truncate long values
            if col == 6: return str(history_entry.new_value)[:200] if history_entry.new_value is not None else "" # Truncate long values
            if col == 7: # Change Type
                return history_entry.change_type.value if isinstance(history_entry.change_type, DataChangeTypeEnum) else str(history_entry.change_type)
            if col == 8: return history_entry.changed_by_username or "N/A"
            return ""
            
        elif role == Qt.ItemDataRole.UserRole: # Store full DTO
            return history_entry
            
        return None

    def get_history_entry_at_row(self, row: int) -> Optional[DataChangeHistoryEntryData]:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None

    def update_data(self, new_data: List[DataChangeHistoryEntryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()
