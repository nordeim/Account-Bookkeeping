# File: app/ui/banking/csv_import_errors_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional

from app.utils.pydantic_models import CSVImportErrorData

class CSVImportErrorsTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[CSVImportErrorData]] = None, parent=None):
        super().__init__(parent)
        self._data: List[CSVImportErrorData] = data or []
        
        self._headers = ["Row #", "Error Message"]
        if self._data and self._data[0].row_data:
            # Dynamically create headers for the original data columns
            num_data_cols = len(self._data[0].row_data)
            self._headers.extend([f"Original Col {i+1}" for i in range(num_data_cols)])

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        error_entry: CSVImportErrorData = self._data[row]

        if col == 0:
            return str(error_entry.row_number)
        elif col == 1:
            return error_entry.error_message
        else:
            # Display original row data
            data_col_index = col - 2
            if 0 <= data_col_index < len(error_entry.row_data):
                return error_entry.row_data[data_col_index]
            return ""
        
        return None

    def update_data(self, new_data: List[CSVImportErrorData]):
        self.beginResetModel()
        self._data = new_data or []
        self._headers = ["Row #", "Error Message"]
        if self._data and self._data[0].row_data:
            num_data_cols = len(self._data[0].row_data)
            self._headers.extend([f"Original Col {i+1}" for i in range(num_data_cols)])
        self.endResetModel()
