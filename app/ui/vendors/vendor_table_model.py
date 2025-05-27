# File: app/ui/vendors/vendor_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional

from app.utils.pydantic_models import VendorSummaryData # Using the DTO for type safety

class VendorTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[VendorSummaryData]] = None, parent=None):
        super().__init__(parent)
        # Headers should match fields in VendorSummaryData + any derived display fields
        self._headers = ["ID", "Code", "Name", "Email", "Phone", "Active"]
        self._data: List[VendorSummaryData] = data or []

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
            
        vendor_summary: VendorSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(vendor_summary.id)
            if col == 1: return vendor_summary.vendor_code
            if col == 2: return vendor_summary.name
            if col == 3: return str(vendor_summary.email) if vendor_summary.email else ""
            if col == 4: return vendor_summary.phone if vendor_summary.phone else ""
            if col == 5: return "Yes" if vendor_summary.is_active else "No"
            
            header_key = self._headers[col].lower().replace(' ', '_')
            return str(getattr(vendor_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole:
            if col == 0: 
                return vendor_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 5: # Active status
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_vendor_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            return self._data[row].id 
        return None
        
    def get_vendor_status_at_row(self, row: int) -> Optional[bool]:
        if 0 <= row < len(self._data):
            return self._data[row].is_active
        return None

    def update_data(self, new_data: List[VendorSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()
