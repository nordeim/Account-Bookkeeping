# app/ui/sales_invoices/sales_invoice_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from datetime import date as python_date

from app.utils.pydantic_models import SalesInvoiceSummaryData
from app.common.enums import InvoiceStatusEnum

class SalesInvoiceTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[SalesInvoiceSummaryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = [
            "ID", "Inv No.", "Inv Date", "Due Date", 
            "Customer", "Total", "Paid", "Balance", "Status"
        ]
        self._data: List[SalesInvoiceSummaryData] = data or []

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

    def _format_decimal_for_table(self, value: Optional[Decimal], show_zero_as_blank: bool = False) -> str:
        if value is None: 
            return "0.00" if not show_zero_as_blank else ""
        try:
            d_value = Decimal(str(value))
            if show_zero_as_blank and d_value == Decimal(0):
                return ""
            return f"{d_value:,.2f}"
        except (InvalidOperation, TypeError):
            return str(value) # Fallback

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        invoice_summary: SalesInvoiceSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            header_key = self._headers[col].lower().replace('.', '').replace(' ', '_')
            
            if col == 0: return str(invoice_summary.id)
            if col == 1: return invoice_summary.invoice_no
            if col == 2: # Inv Date
                inv_date = invoice_summary.invoice_date
                return inv_date.strftime('%d/%m/%Y') if isinstance(inv_date, python_date) else str(inv_date)
            if col == 3: # Due Date
                due_date = invoice_summary.due_date
                return due_date.strftime('%d/%m/%Y') if isinstance(due_date, python_date) else str(due_date)
            if col == 4: return invoice_summary.customer_name
            if col == 5: return self._format_decimal_for_table(invoice_summary.total_amount, False) # Total
            if col == 6: return self._format_decimal_for_table(invoice_summary.amount_paid, True)  # Paid
            if col == 7: # Balance
                balance = invoice_summary.total_amount - invoice_summary.amount_paid
                return self._format_decimal_for_table(balance, False)
            if col == 8: # Status
                status_val = invoice_summary.status
                return status_val.value if isinstance(status_val, InvoiceStatusEnum) else str(status_val)
            
            return str(getattr(invoice_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole: # Store ID for quick retrieval
            if col == 0: 
                return invoice_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] in ["Total", "Paid", "Balance"]:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if self._headers[col] == "Status":
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_invoice_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            return self._data[row].id 
        return None
        
    def get_invoice_status_at_row(self, row: int) -> Optional[InvoiceStatusEnum]:
        if 0 <= row < len(self._data):
            status_val = self._data[row].status
            return status_val if isinstance(status_val, InvoiceStatusEnum) else None
        return None

    def update_data(self, new_data: List[SalesInvoiceSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

