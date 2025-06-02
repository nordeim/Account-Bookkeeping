# File: app/ui/banking/reconciliation_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, InvalidOperation
from datetime import date as python_date

from app.utils.pydantic_models import BankTransactionSummaryData

class ReconciliationTableModel(QAbstractTableModel):
    item_check_state_changed = Signal(int, Qt.CheckState) # row, check_state

    def __init__(self, data: Optional[List[BankTransactionSummaryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["Select", "Txn Date", "Description", "Reference", "Amount"]
        # Store data as a list of tuples: (original_dto, current_check_state)
        self._table_data: List[Tuple[BankTransactionSummaryData, Qt.CheckState]] = []
        if data:
            self.update_data(data)

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._table_data)

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

        if not (0 <= row < len(self._table_data)):
            return None
            
        transaction_summary, check_state = self._table_data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return "" # Checkbox column, no display text
            if col == 1: # Txn Date
                txn_date = transaction_summary.transaction_date
                return txn_date.strftime('%d/%m/%Y') if isinstance(txn_date, python_date) else str(txn_date)
            if col == 2: return transaction_summary.description
            if col == 3: return transaction_summary.reference or ""
            if col == 4: return self._format_decimal_for_table(transaction_summary.amount)
            return ""
        
        elif role == Qt.ItemDataRole.CheckStateRole:
            if col == 0: # "Select" column
                return check_state
        
        elif role == Qt.ItemDataRole.UserRole: # Store original DTO if needed for full data access
            return transaction_summary

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] == "Amount":
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if self._headers[col] in ["Txn Date", "Select"]: # Also center checkbox
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid():
            return False

        row = index.row()
        col = index.column()

        if role == Qt.ItemDataRole.CheckStateRole and col == 0:
            if 0 <= row < len(self._table_data):
                current_dto, _ = self._table_data[row]
                new_check_state = Qt.CheckState(value)
                self._table_data[row] = (current_dto, new_check_state)
                self.dataChanged.emit(index, index, [role])
                self.item_check_state_changed.emit(row, new_check_state)
                return True
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        
        flags = super().flags(index)
        if index.column() == 0: # "Select" column
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        # Make other columns non-editable by default for this model if needed
        # else:
        #    flags &= ~Qt.ItemFlag.ItemIsEditable
        return flags

    def get_item_data_at_row(self, row: int) -> Optional[BankTransactionSummaryData]:
        if 0 <= row < len(self._table_data):
            return self._table_data[row][0] # Return the DTO
        return None
        
    def get_row_check_state(self, row: int) -> Optional[Qt.CheckState]:
        if 0 <= row < len(self._table_data):
            return self._table_data[row][1] # Return the check state
        return None

    def get_checked_item_data(self) -> List[BankTransactionSummaryData]:
        return [dto for dto, state in self._table_data if state == Qt.CheckState.Checked]

    def update_data(self, new_data: List[BankTransactionSummaryData]):
        self.beginResetModel()
        self._table_data = [(dto, Qt.CheckState.Unchecked) for dto in new_data]
        self.endResetModel()
        
    def uncheck_all(self):
        self.beginResetModel() # More efficient to reset model if many rows change
        self._table_data = [(dto, Qt.CheckState.Unchecked) for dto, _ in self._table_data]
        self.endResetModel()

    def uncheck_items_by_id(self, ids_to_uncheck: List[int]):
        changed_indexes: List[QModelIndex] = []
        for row, (dto, check_state) in enumerate(self._table_data):
            if dto.id in ids_to_uncheck and check_state == Qt.CheckState.Checked:
                self._table_data[row] = (dto, Qt.CheckState.Unchecked)
                changed_indexes.append(self.index(row, 0)) # Emit for checkbox column

        if changed_indexes:
            # Emit dataChanged for each affected row's checkbox column
            # More targeted than beginResetModel/endResetModel if only a few change
            for idx in changed_indexes:
                self.dataChanged.emit(idx, idx, [Qt.ItemDataRole.CheckStateRole])
            # Trigger recalculation by emitting a signal that the widget can connect to
            # For simplicity, assume external recalculation after this.
            # Example: self.item_check_state_changed.emit(changed_indexes[0].row(), Qt.CheckState.Unchecked)
            # if you want to signal that *some* check state changed. This would require the slot
            # to re-evaluate all.
            if changed_indexes: # Signal one representative change
                 self.item_check_state_changed.emit(changed_indexes[0].row(), Qt.CheckState.Unchecked)
