# File: app/ui/settings/user_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.utils.pydantic_models import UserSummaryData

class UserTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[UserSummaryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["ID", "Username", "Full Name", "Email", "Roles", "Active", "Last Login"]
        self._data: List[UserSummaryData] = data or []

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
            
        user_summary: UserSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            header_key = self._headers[col].lower().replace(' ', '_')
            
            if col == 0: return str(user_summary.id)
            if col == 1: return user_summary.username
            if col == 2: return user_summary.full_name or ""
            if col == 3: return str(user_summary.email) if user_summary.email else ""
            if col == 4: return ", ".join(user_summary.roles) if user_summary.roles else "N/A"
            if col == 5: return "Yes" if user_summary.is_active else "No"
            if col == 6: 
                # Ensure last_login is datetime before formatting
                last_login_val = user_summary.last_login
                if isinstance(last_login_val, str): # It might come as ISO string from JSON
                    try:
                        last_login_val = datetime.fromisoformat(last_login_val.replace('Z', '+00:00'))
                    except ValueError:
                        return "Invalid Date" # Or keep original string
                
                return last_login_val.strftime('%d/%m/%Y %H:%M') if isinstance(last_login_val, datetime) else "Never"
            
            return str(getattr(user_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole:
            if col == 0: # Store ID with the first column
                return user_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] == "Active":
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_user_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None: return int(id_val)
            return self._data[row].id 
        return None
        
    def get_user_active_status_at_row(self, row: int) -> Optional[bool]:
        if 0 <= row < len(self._data):
            return self._data[row].is_active
        return None
        
    def get_username_at_row(self, row: int) -> Optional[str]:
        if 0 <= row < len(self._data):
            return self._data[row].username
        return None

    def update_data(self, new_data: List[UserSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()
