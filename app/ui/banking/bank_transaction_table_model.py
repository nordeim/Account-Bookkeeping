# File: app/ui/banking/bank_transaction_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from datetime import date as python_date

from app.utils.pydantic_models import BankTransactionSummaryData
from app.common.enums import BankTransactionTypeEnum

class BankTransactionTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[BankTransactionSummaryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = [
            "ID", "Txn Date", "Value Date", "Type", "Description", 
            "Reference", "Amount", "Reconciled"
        ]
        self._data: List[BankTransactionSummaryData] = data or []

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
            return "0.00" # Show 0.00 for None, as it's an amount
        try:
            # Negative numbers should be displayed with a minus sign by default with f-string formatting
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
            
        transaction_summary: BankTransactionSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(transaction_summary.id)
            if col == 1: # Txn Date
                txn_date = transaction_summary.transaction_date
                return txn_date.strftime('%d/%m/%Y') if isinstance(txn_date, python_date) else str(txn_date)
            if col == 2: # Value Date
                val_date = transaction_summary.value_date
                return val_date.strftime('%d/%m/%Y') if isinstance(val_date, python_date) else ""
            if col == 3: # Type
                return transaction_summary.transaction_type.value if isinstance(transaction_summary.transaction_type, BankTransactionTypeEnum) else str(transaction_summary.transaction_type)
            if col == 4: return transaction_summary.description
            if col == 5: return transaction_summary.reference or ""
            if col == 6: return self._format_decimal_for_table(transaction_summary.amount) # Amount (signed)
            if col == 7: return "Yes" if transaction_summary.is_reconciled else "No"
            return ""

        elif role == Qt.ItemDataRole.UserRole: 
            if col == 0: 
                return transaction_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] == "Amount":
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if self._headers[col] in ["Txn Date", "Value Date", "Reconciled"]:
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_transaction_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            return self._data[row].id 
        return None
        
    def get_transaction_reconciled_status_at_row(self, row: int) -> Optional[bool]:
        if 0 <= row < len(self._data):
            return self._data[row].is_reconciled
        return None

    def update_data(self, new_data: List[BankTransactionSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()
