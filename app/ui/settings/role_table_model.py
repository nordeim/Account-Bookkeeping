# File: app/ui/settings/role_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Optional, Any

from app.utils.pydantic_models import RoleData # Use RoleData DTO

class RoleTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[RoleData]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["ID", "Name", "Description"]
        self._data: List[RoleData] = data or []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            # Allow UserRole for ID retrieval
            if role == Qt.ItemDataRole.UserRole and index.column() == 0 and 0 <= index.row() < len(self._data):
                return self._data[index.row()].id
            return None
        
        row = index.row(); col = index.column()
        if not (0 <= row < len(self._data)): return None
            
        role_data: RoleData = self._data[row]

        if col == 0: return str(role_data.id)
        if col == 1: return role_data.name
        if col == 2: return role_data.description or ""
            
        return None

    def get_role_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            # Try UserRole first for consistency if data() method is updated to store it
            idx = self.index(row, 0)
            role_id = self.data(idx, Qt.ItemDataRole.UserRole)
            if role_id is not None: return int(role_id)
            return self._data[row].id 
        return None
        
    def get_role_name_at_row(self, row: int) -> Optional[str]:
        if 0 <= row < len(self._data):
            return self._data[row].name
        return None

    def update_data(self, new_data: List[RoleData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()
