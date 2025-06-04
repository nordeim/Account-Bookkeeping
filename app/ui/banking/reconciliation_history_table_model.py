# File: app/ui/banking/reconciliation_history_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Optional, Any
from datetime import datetime
from decimal import Decimal

from app.utils.pydantic_models import BankReconciliationSummaryData

class ReconciliationHistoryTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[BankReconciliationSummaryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = [
            "ID", "Statement Date", "Statement Balance", 
            "Difference", "Reconciled On", "Reconciled By"
        ]
        self._data: List[BankReconciliationSummaryData] = data or []

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

    def _format_decimal_for_display(self, value: Optional[Decimal]) -> str:
        if value is None:
            return "0.00"
        return f"{value:,.2f}"

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        recon_summary: BankReconciliationSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(recon_summary.id)
            if col == 1: # Statement Date
                stmt_date = recon_summary.statement_date
                return stmt_date.strftime('%d/%m/%Y') if isinstance(stmt_date, datetime.date) else str(stmt_date)
            if col == 2: # Statement Balance
                return self._format_decimal_for_display(recon_summary.statement_ending_balance)
            if col == 3: # Difference
                return self._format_decimal_for_display(recon_summary.reconciled_difference)
            if col == 4: # Reconciled On
                recon_date = recon_summary.reconciliation_date
                return recon_date.strftime('%d/%m/%Y %H:%M:%S') if isinstance(recon_date, datetime) else str(recon_date)
            if col == 5: # Reconciled By
                return recon_summary.created_by_username or "N/A"
            return ""

        elif role == Qt.ItemDataRole.UserRole: # Store ID for quick retrieval
            if col == 0: 
                return recon_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] in ["Statement Balance", "Difference"]:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        
        return None

    def get_reconciliation_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            return self._data[row].id 
        return None

    def update_data(self, new_data: List[BankReconciliationSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()
