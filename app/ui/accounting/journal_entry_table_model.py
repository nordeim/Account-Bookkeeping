# app/ui/accounting/journal_entry_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from datetime import date as python_date # Alias to avoid conflict with Qt's QDate

class JournalEntryTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[Dict[str, Any]]] = None, parent=None):
        super().__init__(parent)
        # Headers match the expected dictionary keys from JournalEntryManager.get_journal_entries_for_listing
        self._headers = ["ID", "Entry No.", "Date", "Description", "Type", "Total", "Status"]
        self._data: List[Dict[str, Any]] = data or []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): # This model is flat, no children
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
            
        entry_summary = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            header_key = self._headers[col].lower().replace('.', '').replace(' ', '_') # "Entry No." -> "entry_no"
            
            if header_key == "id": return str(entry_summary.get("id", "")) # Display ID as string
            if header_key == "entry_no": return entry_summary.get("entry_no", "")
            if header_key == "date": 
                raw_date = entry_summary.get("date")
                if isinstance(raw_date, python_date): return raw_date.strftime('%d/%m/%Y')
                # Assuming date might come as string from JSON, ensure it's parsed if needed by json_date_hook earlier
                if isinstance(raw_date, str): # Should have been converted by json_date_hook
                     try: return python_date.fromisoformat(raw_date).strftime('%d/%m/%Y')
                     except ValueError: return raw_date # Fallback
                return ""
            if header_key == "description": return entry_summary.get("description", "")
            if header_key == "type": return entry_summary.get("type", "")
            if header_key == "total": # Corresponds to "total_amount" key in data dict
                val = entry_summary.get("total_amount")
                try: return f"{Decimal(str(val) if val is not None else '0'):,.2f}"
                except (InvalidOperation, TypeError): return str(val) if val is not None else "0.00"
            if header_key == "status": return entry_summary.get("status", "")
            
            # Fallback for any unhandled column, though all should be covered
            return entry_summary.get(header_key, "")

        elif role == Qt.ItemDataRole.UserRole: # Store complex data if needed, e.g., full object or just ID
            # Typically, for quick access to the ID without parsing display text
            if col == 0: # Store ID with the first column for convenience
                 return entry_summary.get("id")
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] == "Total": # Align "Total" amount to the right
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        
        return None

    def get_journal_entry_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            # Prefer UserRole if ID is stored there, otherwise parse from display data (less ideal)
            index = self.index(row, 0) # Assuming ID is in/associated with the first column
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            # Fallback if UserRole not used or ID not stored there, try from dict directly
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

