# File: app/ui/reports/trial_balance_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal

class TrialBalanceTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["Account Code", "Account Name", "Debit", "Credit"]
        self._debit_accounts: List[Dict[str, Any]] = []
        self._credit_accounts: List[Dict[str, Any]] = []
        self._totals: Dict[str, Decimal] = {"debits": Decimal(0), "credits": Decimal(0)}
        self._is_balanced: bool = False
        if data:
            self.update_data(data)

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): return 0
        return len(self._debit_accounts) + len(self._credit_accounts) + 1 

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def _format_decimal_for_display(self, value: Optional[Decimal]) -> str:
        if value is None or value == Decimal(0): return ""
        return f"{value:,.2f}"

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid(): return None
        
        row, col = index.row(), index.column()
        num_debit_accounts = len(self._debit_accounts)
        num_credit_accounts = len(self._credit_accounts)

        if row == num_debit_accounts + num_credit_accounts: # Totals Row
            if role == Qt.ItemDataRole.DisplayRole:
                if col == 1: return "TOTALS"
                if col == 2: return f"{self._totals['debits']:,.2f}"
                if col == 3: return f"{self._totals['credits']:,.2f}"
                return ""
            elif role == Qt.ItemDataRole.FontRole:
                from PySide6.QtGui import QFont
                font = QFont(); font.setBold(True); return font
            elif role == Qt.ItemDataRole.TextAlignmentRole and col in [2,3]:
                 return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return None

        if row < num_debit_accounts: # Debit Accounts
            account = self._debit_accounts[row]
            if role == Qt.ItemDataRole.DisplayRole:
                if col == 0: return account.get("code", "")
                if col == 1: return account.get("name", "")
                if col == 2: return self._format_decimal_for_display(account.get("balance"))
                if col == 3: return ""
            elif role == Qt.ItemDataRole.TextAlignmentRole and col == 2:
                 return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return None
        
        credit_row_index = row - num_debit_accounts # Credit Accounts
        if credit_row_index < num_credit_accounts:
            account = self._credit_accounts[credit_row_index]
            if role == Qt.ItemDataRole.DisplayRole:
                if col == 0: return account.get("code", "")
                if col == 1: return account.get("name", "")
                if col == 2: return ""
                if col == 3: return self._format_decimal_for_display(account.get("balance"))
            elif role == Qt.ItemDataRole.TextAlignmentRole and col == 3:
                 return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return None
            
        return None

    def update_data(self, report_data: Dict[str, Any]):
        self.beginResetModel()
        self._debit_accounts = report_data.get('debit_accounts', [])
        self._credit_accounts = report_data.get('credit_accounts', [])
        self._totals["debits"] = report_data.get('total_debits', Decimal(0))
        self._totals["credits"] = report_data.get('total_credits', Decimal(0))
        self._is_balanced = report_data.get('is_balanced', False)
        self.endResetModel()

    def get_balance_status(self) -> str:
        return "Balanced" if self._is_balanced else f"Out of Balance by: {abs(self._totals['debits'] - self._totals['credits']):,.2f}"
