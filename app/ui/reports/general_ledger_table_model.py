# app/ui/reports/general_ledger_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date as python_date

class GeneralLedgerTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["Date", "Entry No.", "Description", "Debit", "Credit", "Balance"]
        self._transactions: List[Dict[str, Any]] = []
        self._opening_balance = Decimal(0)
        self._closing_balance = Decimal(0)
        self._account_name = ""
        self._period_description = ""

        if data:
            self.update_data(data)

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): return 0
        # +2 for opening and closing balance rows if we display them in table
        # For now, let's assume they are displayed outside the table by the widget
        return len(self._transactions)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def _format_decimal_for_display(self, value: Optional[Decimal], show_zero_as_blank: bool = True) -> str:
        if value is None: return ""
        if show_zero_as_blank and value == Decimal(0): return ""
        return f"{value:,.2f}"

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid(): return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._transactions)): return None
            
        txn = self._transactions[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: # Date
                raw_date = txn.get("date")
                return raw_date.strftime('%d/%m/%Y') if isinstance(raw_date, python_date) else str(raw_date)
            if col == 1: return txn.get("entry_no", "") # Entry No.
            if col == 2: # Description
                desc = txn.get("je_description", "")
                line_desc = txn.get("line_description", "")
                return f"{desc} // {line_desc}" if desc and line_desc else (desc or line_desc)
            if col == 3: return self._format_decimal_for_display(txn.get("debit"), True)  # Debit
            if col == 4: return self._format_decimal_for_display(txn.get("credit"), True) # Credit
            if col == 5: return self._format_decimal_for_display(txn.get("balance"), False) # Balance (show zero)
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in [3, 4, 5]: # Debit, Credit, Balance
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        
        return None

    def update_data(self, report_data: Dict[str, Any]):
        self.beginResetModel()
        self._transactions = report_data.get('transactions', [])
        self._opening_balance = report_data.get('opening_balance', Decimal(0))
        self._closing_balance = report_data.get('closing_balance', Decimal(0))
        self._account_name = f"{report_data.get('account_code','')} - {report_data.get('account_name','')}"
        start = report_data.get('start_date')
        end = report_data.get('end_date')
        self._period_description = f"For {start.strftime('%d/%m/%Y') if start else ''} to {end.strftime('%d/%m/%Y') if end else ''}"
        self.endResetModel()

    def get_report_summary(self) -> Dict[str, Any]:
        return {
            "account_name": self._account_name,
            "period_description": self._period_description,
            "opening_balance": self._opening_balance,
            "closing_balance": self._closing_balance
        }
