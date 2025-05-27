# app/ui/products/product_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation

from app.utils.pydantic_models import ProductSummaryData # Using the DTO for type safety
from app.common.enums import ProductTypeEnum # For displaying enum value

class ProductTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[ProductSummaryData]] = None, parent=None):
        super().__init__(parent)
        # Headers match fields in ProductSummaryData + any derived display fields
        self._headers = ["ID", "Code", "Name", "Type", "Sales Price", "Purchase Price", "Active"]
        self._data: List[ProductSummaryData] = data or []

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
    
    def _format_decimal_for_table(self, value: Optional[Decimal]) -> str:
        if value is None: return ""
        try:
            return f"{Decimal(str(value)):,.2f}"
        except (InvalidOperation, TypeError):
            return str(value) # Fallback

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        product_summary: ProductSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            header_key = self._headers[col].lower().replace(' ', '_') # e.g. "Sales Price" -> "sales_price"
            
            if col == 0: return str(product_summary.id)
            if col == 1: return product_summary.product_code
            if col == 2: return product_summary.name
            if col == 3: return product_summary.product_type.value if isinstance(product_summary.product_type, ProductTypeEnum) else str(product_summary.product_type)
            if col == 4: return self._format_decimal_for_table(product_summary.sales_price)
            if col == 5: return self._format_decimal_for_table(product_summary.purchase_price)
            if col == 6: return "Yes" if product_summary.is_active else "No"
            
            # Fallback for safety (should be covered by above)
            return str(getattr(product_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole:
            if col == 0: 
                return product_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] in ["Sales Price", "Purchase Price"]:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if self._headers[col] == "Active":
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_product_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            return self._data[row].id 
        return None
        
    def get_product_status_at_row(self, row: int) -> Optional[bool]:
        if 0 <= row < len(self._data):
            return self._data[row].is_active
        return None

    def update_data(self, new_data: List[ProductSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()
