# app/ui/customers/customer_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional

from app.utils.pydantic_models import CustomerSummaryData # Using the DTO for type safety

class CustomerTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[CustomerSummaryData]] = None, parent=None):
        super().__init__(parent)
        # Headers should match fields in CustomerSummaryData + any derived display fields
        self._headers = ["ID", "Code", "Name", "Email", "Phone", "Active"]
        self._data: List[CustomerSummaryData] = data or []

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
            
        customer_summary: CustomerSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(customer_summary.id)
            if col == 1: return customer_summary.customer_code
            if col == 2: return customer_summary.name
            if col == 3: return str(customer_summary.email) if customer_summary.email else ""
            if col == 4: return customer_summary.phone if customer_summary.phone else ""
            if col == 5: return "Yes" if customer_summary.is_active else "No"
            
            # Fallback for safety, though all defined headers should be covered
            header_key = self._headers[col].lower().replace(' ', '_')
            return str(getattr(customer_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole:
            # Store the full DTO or just the ID in UserRole for easy retrieval
            # Storing ID in the first column's UserRole is common.
            if col == 0: 
                return customer_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 5: # Active status
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_customer_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) # Assuming ID is in/associated with the first column (model index 0)
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            # Fallback if UserRole is not used for ID or is somehow None
            return self._data[row].id 
        return None
        
    def get_customer_status_at_row(self, row: int) -> Optional[bool]:
        if 0 <= row < len(self._data):
            return self._data[row].is_active
        return None

    def update_data(self, new_data: List[CustomerSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()
