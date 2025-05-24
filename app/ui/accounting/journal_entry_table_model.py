# File: app/ui/accounting/journal_entry_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date

class JournalEntryTableModel(QAbstractTableModel):
    def __init__(self, data: List[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["Entry No", "Date", "Description", "Type", "Total Amount", "Status"]
        self._data: List[Dict[str, Any]] = data or []

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        row_data = self._data[index.row()]
        column_name = self._headers[index.column()].lower().replace(" ", "_") # e.g. "Entry No" -> "entry_no"

        if role == Qt.ItemDataRole.DisplayRole:
            value = row_data.get(column_name)
            if column_name == "date" and isinstance(value, str): # Assuming date comes as ISO string from JSON
                try:
                    dt_value = date.fromisoformat(value)
                    return dt_value.strftime('%d/%m/%Y')
                except ValueError:
                    return value # Return original string if parsing fails
            elif column_name == "total_amount" and value is not None:
                try:
                    return f"{Decimal(str(value)):,.2f}"
                except InvalidOperation:
                    return str(value)
            return str(value) if value is not None else ""
        
        if role == Qt.ItemDataRole.UserRole: # To store the ID
            return row_data.get("id")
            
        return None

    def get_journal_entry_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            return self._data[row].get("id")
        return None
        
    def get_journal_entry_status_at_row(self, row: int) -> Optional[str]:
        if 0 <= row < len(self._data):
            return self._data[row].get("status")
        return None

    def update_data(self, new_data: List[Dict[str, Any]]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()
