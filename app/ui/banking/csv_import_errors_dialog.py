# File: app/ui/banking/csv_import_errors_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDialogButtonBox,
    QTableView, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from typing import Optional, List, TYPE_CHECKING

from app.ui.banking.csv_import_errors_table_model import CSVImportErrorsTableModel
from app.utils.pydantic_models import CSVImportErrorData

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class CSVImportErrorsDialog(QDialog):
    def __init__(self, errors: List[CSVImportErrorData], parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.setWindowTitle("CSV Import Errors")
        self.setMinimumSize(800, 400)
        self.setModal(True)

        self._init_ui(errors)

    def _init_ui(self, errors: List[CSVImportErrorData]):
        main_layout = QVBoxLayout(self)

        info_label = QLabel(
            "The CSV import completed, but some rows could not be processed.\n"
            "Please review the errors below, correct them in your source file, and try importing again."
        )
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        self.errors_table = QTableView()
        self.errors_table.setAlternatingRowColors(True)
        self.errors_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.errors_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.errors_table.setSortingEnabled(True)

        self.table_model = CSVImportErrorsTableModel(data=errors)
        self.errors_table.setModel(self.table_model)

        header = self.errors_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Row #
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Error Message
        for i in range(2, self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            self.errors_table.setColumnWidth(i, 120)

        main_layout.addWidget(self.errors_table)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)
