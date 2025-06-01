# File: app/ui/payments/payment_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from datetime import date as python_date

from app.utils.pydantic_models import PaymentSummaryData
from app.common.enums import PaymentTypeEnum, PaymentMethodEnum, PaymentEntityTypeEnum, PaymentStatusEnum

class PaymentTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[PaymentSummaryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = [
            "ID", "Payment No", "Date", "Type", "Method", 
            "Entity Type", "Entity Name", "Amount", "Currency", "Status"
        ]
        self._data: List[PaymentSummaryData] = data or []

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
        if value is None: 
            return "0.00"
        try:
            return f"{Decimal(str(value)):,.2f}"
        except (InvalidOperation, TypeError):
            return str(value) 

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        payment_summary: PaymentSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(payment_summary.id)
            if col == 1: return payment_summary.payment_no
            if col == 2: # Date
                pay_date = payment_summary.payment_date
                return pay_date.strftime('%d/%m/%Y') if isinstance(pay_date, python_date) else str(pay_date)
            if col == 3: # Type
                return payment_summary.payment_type.value if isinstance(payment_summary.payment_type, PaymentTypeEnum) else str(payment_summary.payment_type)
            if col == 4: # Method
                 return payment_summary.payment_method.value if isinstance(payment_summary.payment_method, PaymentMethodEnum) else str(payment_summary.payment_method)
            if col == 5: # Entity Type
                 return payment_summary.entity_type.value if isinstance(payment_summary.entity_type, PaymentEntityTypeEnum) else str(payment_summary.entity_type)
            if col == 6: return payment_summary.entity_name
            if col == 7: return self._format_decimal_for_table(payment_summary.amount)
            if col == 8: return payment_summary.currency_code
            if col == 9: # Status
                return payment_summary.status.value if isinstance(payment_summary.status, PaymentStatusEnum) else str(payment_summary.status)
            return ""

        elif role == Qt.ItemDataRole.UserRole: 
            if col == 0: 
                return payment_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] == "Amount":
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if self._headers[col] in ["Date", "Status", "Type", "Method"]:
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_payment_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            # Fallback if UserRole is not used for ID or is somehow None
            return self._data[row].id 
        return None
        
    def get_payment_status_at_row(self, row: int) -> Optional[PaymentStatusEnum]:
        if 0 <= row < len(self._data):
            status_val = self._data[row].status
            return status_val if isinstance(status_val, PaymentStatusEnum) else None
        return None

    def update_data(self, new_data: List[PaymentSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()
