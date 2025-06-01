# File: app/ui/banking/bank_account_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation

from app.utils.pydantic_models import BankAccountSummaryData

class BankAccountTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[BankAccountSummaryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = [
            "ID", "Account Name", "Bank Name", "Account Number", 
            "Currency", "Current Balance", "GL Account", "Active"
        ]
        self._data: List[BankAccountSummaryData] = data or []

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
            
        bank_account_summary: BankAccountSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(bank_account_summary.id)
            if col == 1: return bank_account_summary.account_name
            if col == 2: return bank_account_summary.bank_name
            if col == 3: return bank_account_summary.account_number
            if col == 4: return bank_account_summary.currency_code
            if col == 5: return self._format_decimal_for_table(bank_account_summary.current_balance)
            if col == 6: 
                gl_code = bank_account_summary.gl_account_code
                gl_name = bank_account_summary.gl_account_name
                if gl_code and gl_name: return f"{gl_code} - {gl_name}"
                if gl_code: return gl_code
                return "N/A"
            if col == 7: return "Yes" if bank_account_summary.is_active else "No"
            return ""

        elif role == Qt.ItemDataRole.UserRole: 
            if col == 0: 
                return bank_account_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] == "Current Balance":
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if self._headers[col] == "Active":
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_bank_account_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            return self._data[row].id 
        return None
        
    def get_bank_account_status_at_row(self, row: int) -> Optional[bool]:
        if 0 <= row < len(self._data):
            return self._data[row].is_active
        return None

    def update_data(self, new_data: List[BankAccountSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()
