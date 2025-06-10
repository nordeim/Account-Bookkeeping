# pyproject.toml
```toml
# pyproject.toml
[tool.poetry]
name = "sg-bookkeeper"
version = "1.0.0"
description = "Singapore small business bookkeeping application"
authors = ["Your Name <your.email@example.com>"]
license = "MIT"
readme = "README.md"
homepage = "https://github.com/yourusername/sg_bookkeeper"
repository = "https://github.com/yourusername/sg_bookkeeper"
keywords = ["accounting", "bookkeeping", "singapore", "gst", "tax"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Financial and Insurance Industry",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12", 
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Topic :: Office/Business :: Financial :: Accounting",
]
packages = [{include = "app", from = "."}]

[tool.poetry.dependencies]
python = ">=3.9,<3.13" 
PySide6 = "^6.9.0"   # The QtCharts module from this package is used for the dashboard
SQLAlchemy = {extras = ["asyncio"], version = ">=2.0.0"}
asyncpg = ">=0.25.0"
alembic = ">=1.7.5"
pydantic = {version = "^2.0", extras = ["email"]}
reportlab = ">=3.6.6"
openpyxl = ">=3.0.9"
python-dateutil = ">=2.8.2"
bcrypt = ">=3.2.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
pytest-cov = "^4.0"
flake8 = "^6.0"
black = "^24.0" 
mypy = "^1.0" 
pre-commit = "^3.0"
pytest-qt = "^4.0"
pytest-asyncio = "^0.21.0" 

[tool.poetry.scripts]
sg_bookkeeper = "app.main:main"
sg_bookkeeper_db_init = "scripts.db_init:main"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311', 'py312']

[tool.pytest.ini_options]
python_files = "test_*.py tests.py" 
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"


```

# app/ui/banking/__init__.py
```py
# File: app/ui/banking/__init__.py
from .banking_widget import BankingWidget
from .bank_account_table_model import BankAccountTableModel 
from .bank_account_dialog import BankAccountDialog 
from .bank_accounts_widget import BankAccountsWidget 
from .bank_transaction_table_model import BankTransactionTableModel
from .bank_transaction_dialog import BankTransactionDialog
from .bank_transactions_widget import BankTransactionsWidget
from .csv_import_config_dialog import CSVImportConfigDialog
from .bank_reconciliation_widget import BankReconciliationWidget
from .reconciliation_table_model import ReconciliationTableModel
from .reconciliation_history_table_model import ReconciliationHistoryTableModel
from .csv_import_errors_dialog import CSVImportErrorsDialog # New Import
from .csv_import_errors_table_model import CSVImportErrorsTableModel # New Import

__all__ = [
    "BankingWidget",
    "BankAccountTableModel", 
    "BankAccountDialog", 
    "BankAccountsWidget", 
    "BankTransactionTableModel",
    "BankTransactionDialog",
    "BankTransactionsWidget",
    "CSVImportConfigDialog",
    "BankReconciliationWidget",
    "ReconciliationTableModel",
    "ReconciliationHistoryTableModel",
    "CSVImportErrorsDialog", # New Export
    "CSVImportErrorsTableModel", # New Export
]

```

# app/ui/banking/csv_import_errors_dialog.py
```py
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

```

# app/ui/banking/csv_import_errors_table_model.py
```py
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

```

# app/ui/banking/reconciliation_table_model.py
```py
# File: app/ui/banking/reconciliation_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QColor # New import for background role
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, InvalidOperation
from datetime import date as python_date

from app.utils.pydantic_models import BankTransactionSummaryData

class ReconciliationTableModel(QAbstractTableModel):
    item_check_state_changed = Signal(int, Qt.CheckState) # row, check_state

    def __init__(self, data: Optional[List[BankTransactionSummaryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["Select", "Txn Date", "Description", "Reference", "Amount"]
        self._table_data: List[Tuple[BankTransactionSummaryData, Qt.CheckState]] = []
        self._row_colors: Dict[int, QColor] = {}
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
        
        elif role == Qt.ItemDataRole.BackgroundRole: # New handler for background color
            return self._row_colors.get(row)

        elif role == Qt.ItemDataRole.UserRole:
            return transaction_summary

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] == "Amount":
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if self._headers[col] in ["Txn Date", "Select"]:
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
        if index.column() == 0:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def get_item_data_at_row(self, row: int) -> Optional[BankTransactionSummaryData]:
        if 0 <= row < len(self._table_data):
            return self._table_data[row][0]
        return None
        
    def get_row_check_state(self, row: int) -> Optional[Qt.CheckState]:
        if 0 <= row < len(self._table_data):
            return self._table_data[row][1]
        return None

    def get_checked_item_data(self) -> List[BankTransactionSummaryData]:
        return [dto for dto, state in self._table_data if state == Qt.CheckState.Checked]

    def update_data(self, new_data: List[BankTransactionSummaryData], row_colors: Optional[Dict[int, QColor]] = None):
        self.beginResetModel()
        self._table_data = [(dto, Qt.CheckState.Unchecked) for dto in new_data]
        self._row_colors = row_colors if row_colors is not None else {}
        self.endResetModel()
        
    def uncheck_all(self):
        self.beginResetModel()
        self._table_data = [(dto, Qt.CheckState.Unchecked) for dto, _ in self._table_data]
        self.endResetModel()

    def uncheck_items_by_id(self, ids_to_uncheck: List[int]):
        changed_indexes: List[QModelIndex] = []
        for row, (dto, check_state) in enumerate(self._table_data):
            if dto.id in ids_to_uncheck and check_state == Qt.CheckState.Checked:
                self._table_data[row] = (dto, Qt.CheckState.Unchecked)
                changed_indexes.append(self.index(row, 0))

        if changed_indexes:
            for idx in changed_indexes:
                self.dataChanged.emit(idx, idx, [Qt.ItemDataRole.CheckStateRole])
            if changed_indexes:
                 self.item_check_state_changed.emit(changed_indexes[0].row(), Qt.CheckState.Unchecked)

```

# app/ui/banking/bank_reconciliation_widget.py
```py
# File: app/ui/banking/bank_reconciliation_widget.py
import json
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Tuple, cast
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, QTableView, QPushButton,
    QToolBar, QHeaderView, QAbstractItemView, QMessageBox, QLabel,
    QDateEdit, QComboBox, QDoubleSpinBox, QSplitter, QGroupBox, QCheckBox,
    QScrollArea, QFrame, QFormLayout
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QDate, QSize, Signal
from PySide6.QtGui import QIcon, QFont, QColor

from datetime import date as python_date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.banking.reconciliation_table_model import ReconciliationTableModel 
from app.ui.banking.reconciliation_history_table_model import ReconciliationHistoryTableModel
from app.ui.banking.bank_transaction_table_model import BankTransactionTableModel
from app.ui.accounting.journal_entry_dialog import JournalEntryDialog
from app.utils.pydantic_models import (
    BankAccountSummaryData, BankTransactionSummaryData, 
    JournalEntryData, JournalEntryLineData, BankReconciliationSummaryData, BankReconciliationCreateData
)
from app.common.enums import BankTransactionTypeEnum
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.bank_reconciliation import BankReconciliation # For type hint

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice


class BankReconciliationWidget(QWidget):
    reconciliation_saved = Signal(int) # Emits BankReconciliation.id

    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._bank_accounts_cache: List[BankAccountSummaryData] = []
        self._current_bank_account_id: Optional[int] = None
        self._current_bank_account_gl_id: Optional[int] = None
        self._current_bank_account_currency: str = "SGD"
        
        self._all_loaded_statement_lines: List[BankTransactionSummaryData] = [] # Unreconciled statement lines
        self._all_loaded_system_transactions: List[BankTransactionSummaryData] = [] # Unreconciled system transactions

        self._current_draft_statement_lines: List[BankTransactionSummaryData] = [] # Provisionally matched statement lines
        self._current_draft_system_transactions: List[BankTransactionSummaryData] = [] # Provisionally matched system lines

        self._statement_ending_balance = Decimal(0)
        self._book_balance_gl = Decimal(0) 
        self._interest_earned_on_statement_not_in_book = Decimal(0)
        self._bank_charges_on_statement_not_in_book = Decimal(0)
        self._outstanding_system_deposits = Decimal(0) 
        self._outstanding_system_withdrawals = Decimal(0) 
        self._difference = Decimal(0)

        self._current_stmt_selection_total = Decimal(0) # For tracking selection totals
        self._current_sys_selection_total = Decimal(0)  # For tracking selection totals

        self._current_draft_reconciliation_id: Optional[int] = None 
        self._current_history_page = 1
        self._total_history_records = 0
        self._history_page_size = 10 

        self.icon_path_prefix = "resources/icons/"
        try: import app.resources_rc; self.icon_path_prefix = ":/icons/"
        except ImportError: pass
        
        self._group_colors = [QColor("#EAF3F9"), QColor("#F9F9EA"), QColor("#F9EAEA")]

        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_bank_accounts_for_combo()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self); self.main_layout.setContentsMargins(5,5,5,5)
        
        header_controls_group = QGroupBox("Reconciliation Setup"); header_layout = QGridLayout(header_controls_group)
        header_layout.addWidget(QLabel("Bank Account*:"), 0, 0); self.bank_account_combo = QComboBox(); self.bank_account_combo.setMinimumWidth(250); header_layout.addWidget(self.bank_account_combo, 0, 1)
        header_layout.addWidget(QLabel("Statement End Date*:"), 0, 2); self.statement_date_edit = QDateEdit(QDate.currentDate()); self.statement_date_edit.setCalendarPopup(True); self.statement_date_edit.setDisplayFormat("dd/MM/yyyy"); header_layout.addWidget(self.statement_date_edit, 0, 3)
        header_layout.addWidget(QLabel("Statement End Balance*:"), 1, 0); self.statement_balance_spin = QDoubleSpinBox(); self.statement_balance_spin.setDecimals(2); self.statement_balance_spin.setRange(-999999999.99, 999999999.99); self.statement_balance_spin.setGroupSeparatorShown(True); header_layout.addWidget(self.statement_balance_spin, 1, 1)
        self.load_transactions_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Load / Refresh Transactions"); header_layout.addWidget(self.load_transactions_button, 1, 3)
        header_layout.setColumnStretch(2,1); self.main_layout.addWidget(header_controls_group)

        self.overall_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_layout.addWidget(self.overall_splitter, 1)

        current_recon_work_area_widget = QWidget()
        current_recon_work_area_layout = QVBoxLayout(current_recon_work_area_widget)
        current_recon_work_area_layout.setContentsMargins(0,0,0,0)

        summary_group = QGroupBox("Reconciliation Summary"); summary_layout = QFormLayout(summary_group); summary_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.book_balance_gl_label = QLabel("0.00"); summary_layout.addRow("Book Balance (per GL):", self.book_balance_gl_label)
        self.adj_interest_earned_label = QLabel("0.00"); summary_layout.addRow("Add: Interest / Credits (on Stmt, not Book):", self.adj_interest_earned_label)
        self.adj_bank_charges_label = QLabel("0.00"); summary_layout.addRow("Less: Bank Charges / Debits (on Stmt, not Book):", self.adj_bank_charges_label)
        self.adjusted_book_balance_label = QLabel("0.00"); self.adjusted_book_balance_label.setFont(QFont(self.font().family(), -1, QFont.Weight.Bold)); summary_layout.addRow("Adjusted Book Balance:", self.adjusted_book_balance_label)
        summary_layout.addRow(QLabel("---")); self.statement_ending_balance_label = QLabel("0.00"); summary_layout.addRow("Statement Ending Balance:", self.statement_ending_balance_label)
        self.adj_deposits_in_transit_label = QLabel("0.00"); summary_layout.addRow("Add: Deposits in Transit (in Book, not Stmt):", self.adj_deposits_in_transit_label)
        self.adj_outstanding_checks_label = QLabel("0.00"); summary_layout.addRow("Less: Outstanding Withdrawals (in Book, not Stmt):", self.adj_outstanding_checks_label)
        self.adjusted_bank_balance_label = QLabel("0.00"); self.adjusted_bank_balance_label.setFont(QFont(self.font().family(), -1, QFont.Weight.Bold)); summary_layout.addRow("Adjusted Bank Balance:", self.adjusted_bank_balance_label)
        summary_layout.addRow(QLabel("---")); self.difference_label = QLabel("0.00"); font_diff = self.difference_label.font(); font_diff.setBold(True); font_diff.setPointSize(font_diff.pointSize()+1); self.difference_label.setFont(font_diff)
        summary_layout.addRow("Difference:", self.difference_label); current_recon_work_area_layout.addWidget(summary_group)

        self.current_recon_tables_splitter = QSplitter(Qt.Orientation.Vertical)
        current_recon_work_area_layout.addWidget(self.current_recon_tables_splitter, 1)

        unreconciled_area_widget = QWidget(); unreconciled_layout = QVBoxLayout(unreconciled_area_widget); unreconciled_layout.setContentsMargins(0,0,0,0)
        self.tables_splitter = QSplitter(Qt.Orientation.Horizontal)
        statement_items_group = QGroupBox("Bank Statement Items (Unreconciled)"); statement_layout = QVBoxLayout(statement_items_group)
        self.statement_lines_table = QTableView(); self.statement_lines_model = ReconciliationTableModel()
        self._configure_recon_table(self.statement_lines_table, self.statement_lines_model, is_statement_table=True)
        statement_layout.addWidget(self.statement_lines_table); self.tables_splitter.addWidget(statement_items_group)
        system_txns_group = QGroupBox("System Bank Transactions (Unreconciled)"); system_layout = QVBoxLayout(system_txns_group)
        self.system_txns_table = QTableView(); self.system_txns_model = ReconciliationTableModel()
        self._configure_recon_table(self.system_txns_table, self.system_txns_model, is_statement_table=False)
        system_layout.addWidget(self.system_txns_table); self.tables_splitter.addWidget(system_txns_group)
        self.tables_splitter.setSizes([self.width() // 2, self.width() // 2])
        unreconciled_layout.addWidget(self.tables_splitter, 1)
        
        selection_totals_layout = QHBoxLayout(); selection_totals_layout.setContentsMargins(5,5,5,5)
        self.statement_selection_total_label = QLabel("Statement Selected: 0.00"); self.system_selection_total_label = QLabel("System Selected: 0.00")
        selection_font = self.statement_selection_total_label.font(); selection_font.setBold(True); self.statement_selection_total_label.setFont(selection_font); self.system_selection_total_label.setFont(selection_font)
        selection_totals_layout.addWidget(QLabel("<b>Selection Totals:</b>")); selection_totals_layout.addStretch(); selection_totals_layout.addWidget(self.statement_selection_total_label); selection_totals_layout.addWidget(QLabel(" | ")); selection_totals_layout.addWidget(self.system_selection_total_label); selection_totals_layout.addStretch()
        unreconciled_layout.addLayout(selection_totals_layout)
        
        self.current_recon_tables_splitter.addWidget(unreconciled_area_widget)
        
        draft_matched_area_widget = QWidget(); draft_matched_layout = QVBoxLayout(draft_matched_area_widget); draft_matched_layout.setContentsMargins(0,5,0,0)
        self.tables_splitter_draft_matched = QSplitter(Qt.Orientation.Horizontal)
        draft_stmt_items_group = QGroupBox("Provisionally Matched Statement Items (This Session)"); draft_stmt_layout = QVBoxLayout(draft_stmt_items_group)
        self.draft_matched_statement_table = QTableView(); self.draft_matched_statement_model = ReconciliationTableModel()
        self._configure_recon_table(self.draft_matched_statement_table, self.draft_matched_statement_model, is_statement_table=True)
        draft_stmt_layout.addWidget(self.draft_matched_statement_table); self.tables_splitter_draft_matched.addWidget(draft_stmt_items_group)
        draft_sys_txns_group = QGroupBox("Provisionally Matched System Transactions (This Session)"); draft_sys_layout = QVBoxLayout(draft_sys_txns_group)
        self.draft_matched_system_table = QTableView(); self.draft_matched_system_model = ReconciliationTableModel()
        self._configure_recon_table(self.draft_matched_system_table, self.draft_matched_system_model, is_statement_table=False)
        draft_sys_layout.addWidget(self.draft_matched_system_table); self.tables_splitter_draft_matched.addWidget(draft_sys_txns_group)
        self.tables_splitter_draft_matched.setSizes([self.width() // 2, self.width() // 2])
        draft_matched_layout.addWidget(self.tables_splitter_draft_matched, 1)
        self.current_recon_tables_splitter.addWidget(draft_matched_area_widget)
        self.current_recon_tables_splitter.setSizes([int(self.height() * 0.7), int(self.height() * 0.3)])

        action_layout = QHBoxLayout()
        self.match_selected_button = QPushButton(QIcon(self.icon_path_prefix + "post.svg"), "Match Selected"); self.match_selected_button.setEnabled(False)
        self.unmatch_button = QPushButton(QIcon(self.icon_path_prefix + "reverse.svg"), "Unmatch Selected"); self.unmatch_button.setEnabled(False)
        self.create_je_button = QPushButton(QIcon(self.icon_path_prefix + "add.svg"), "Add Journal Entry"); self.create_je_button.setEnabled(False) 
        self.save_reconciliation_button = QPushButton(QIcon(self.icon_path_prefix + "backup.svg"), "Save Final Reconciliation"); self.save_reconciliation_button.setEnabled(False); self.save_reconciliation_button.setObjectName("SaveReconButton")
        action_layout.addStretch(); action_layout.addWidget(self.match_selected_button); action_layout.addWidget(self.unmatch_button); action_layout.addWidget(self.create_je_button); action_layout.addStretch(); action_layout.addWidget(self.save_reconciliation_button)
        current_recon_work_area_layout.addLayout(action_layout)
        self.overall_splitter.addWidget(current_recon_work_area_widget)

        history_outer_group = QGroupBox("Reconciliation History"); history_outer_layout = QVBoxLayout(history_outer_group)
        self.history_table = QTableView(); self.history_table_model = ReconciliationHistoryTableModel()
        self.history_table.setModel(self.history_table_model)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.horizontalHeader().setStretchLastSection(False); self.history_table.setSortingEnabled(True)
        if "ID" in self.history_table_model._headers: self.history_table.setColumnHidden(self.history_table_model._headers.index("ID"), True)
        for i in range(self.history_table_model.columnCount()): 
            if not self.history_table.isColumnHidden(i): self.history_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        if "Statement Date" in self.history_table_model._headers and not self.history_table.isColumnHidden(self.history_table_model._headers.index("Statement Date")): self.history_table.horizontalHeader().setSectionResizeMode(self.history_table_model._headers.index("Statement Date"), QHeaderView.ResizeMode.Stretch)
        history_outer_layout.addWidget(self.history_table)
        history_pagination_layout = QHBoxLayout()
        self.prev_history_button = QPushButton("<< Previous Page"); self.prev_history_button.setEnabled(False)
        self.history_page_info_label = QLabel("Page 1 of 1 (0 Records)")
        self.next_history_button = QPushButton("Next Page >>"); self.next_history_button.setEnabled(False)
        history_pagination_layout.addStretch(); history_pagination_layout.addWidget(self.prev_history_button); history_pagination_layout.addWidget(self.history_page_info_label); history_pagination_layout.addWidget(self.next_history_button); history_pagination_layout.addStretch()
        history_outer_layout.addLayout(history_pagination_layout)
        self.history_details_group = QGroupBox("Details of Selected Historical Reconciliation"); history_details_layout = QVBoxLayout(self.history_details_group)
        history_details_splitter = QSplitter(Qt.Orientation.Horizontal)
        hist_stmt_group = QGroupBox("Statement Items Cleared"); hist_stmt_layout = QVBoxLayout(hist_stmt_group)
        self.history_statement_txns_table = QTableView(); self.history_statement_txns_model = BankTransactionTableModel()
        self._configure_readonly_detail_table(self.history_statement_txns_table, self.history_statement_txns_model)
        hist_stmt_layout.addWidget(self.history_statement_txns_table); history_details_splitter.addWidget(hist_stmt_group)
        hist_sys_group = QGroupBox("System Transactions Cleared"); hist_sys_layout = QVBoxLayout(hist_sys_group)
        self.history_system_txns_table = QTableView(); self.history_system_txns_model = BankTransactionTableModel()
        self._configure_readonly_detail_table(self.history_system_txns_table, self.history_system_txns_model)
        hist_sys_layout.addWidget(self.history_system_txns_table); history_details_splitter.addWidget(hist_sys_group)
        history_details_layout.addWidget(history_details_splitter); history_outer_layout.addWidget(self.history_details_group)
        self.history_details_group.setVisible(False)
        self.overall_splitter.addWidget(history_outer_group)
        self.overall_splitter.setSizes([int(self.height() * 0.65), int(self.height() * 0.35)])
        
        self.setLayout(self.main_layout)
        self._connect_signals()

    def _configure_readonly_detail_table(self, table_view: QTableView, table_model: BankTransactionTableModel):
        table_view.setModel(table_model); table_view.setAlternatingRowColors(True)
        table_view.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_view.horizontalHeader().setStretchLastSection(False); table_view.setSortingEnabled(True)
        if "ID" in table_model._headers: table_view.setColumnHidden(table_model._headers.index("ID"), True)
        if "Reconciled" in table_model._headers: table_view.setColumnHidden(table_model._headers.index("Reconciled"), True)
        for i in range(table_model.columnCount()):
             if not table_view.isColumnHidden(i) : table_view.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        desc_col_idx = table_model._headers.index("Description")
        if "Description" in table_model._headers and not table_view.isColumnHidden(desc_col_idx):
            table_view.horizontalHeader().setSectionResizeMode(desc_col_idx, QHeaderView.ResizeMode.Stretch)

    def _configure_recon_table(self, table_view: QTableView, table_model: ReconciliationTableModel, is_statement_table: bool):
        table_view.setModel(table_model); table_view.setAlternatingRowColors(True)
        table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) 
        table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_view.horizontalHeader().setStretchLastSection(False); table_view.setSortingEnabled(True)
        header = table_view.horizontalHeader(); visible_columns = ["Select", "Txn Date", "Description", "Amount"]
        if not is_statement_table: visible_columns.append("Reference")
        for i in range(table_model.columnCount()):
            header_text = table_model.headerData(i, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            if header_text not in visible_columns : table_view.setColumnHidden(i, True)
            else: header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        desc_col_idx = table_model._headers.index("Description")
        if not table_view.isColumnHidden(desc_col_idx): header.setSectionResizeMode(desc_col_idx, QHeaderView.ResizeMode.Stretch)
        select_col_idx = table_model._headers.index("Select")
        if not table_view.isColumnHidden(select_col_idx): table_view.setColumnWidth(select_col_idx, 50)

    def _connect_signals(self):
        self.bank_account_combo.currentIndexChanged.connect(self._on_bank_account_changed)
        self.statement_balance_spin.valueChanged.connect(self._on_statement_balance_changed)
        self.load_transactions_button.clicked.connect(self._on_load_transactions_clicked)
        
        self.statement_lines_model.item_check_state_changed.connect(self._update_selection_totals)
        self.system_txns_model.item_check_state_changed.connect(self._update_selection_totals)
        
        self.draft_matched_statement_model.item_check_state_changed.connect(self._update_unmatch_button_state)
        self.draft_matched_system_model.item_check_state_changed.connect(self._update_unmatch_button_state)

        self.match_selected_button.clicked.connect(self._on_match_selected_clicked)
        self.unmatch_button.clicked.connect(self._on_unmatch_selected_clicked)
        self.create_je_button.clicked.connect(self._on_create_je_for_statement_item_clicked)
        self.save_reconciliation_button.clicked.connect(self._on_save_reconciliation_clicked)
        
        self.history_table.selectionModel().currentRowChanged.connect(self._on_history_selection_changed)
        self.prev_history_button.clicked.connect(lambda: self._load_reconciliation_history(self._current_history_page - 1))
        self.next_history_button.clicked.connect(lambda: self._load_reconciliation_history(self._current_history_page + 1))

    async def _load_bank_accounts_for_combo(self):
        if not self.app_core.bank_account_manager: return
        try:
            result = await self.app_core.bank_account_manager.get_bank_accounts_for_listing(active_only=True, page_size=-1)
            if result.is_success and result.value:
                self._bank_accounts_cache = result.value
                items_json = json.dumps([ba.model_dump(mode='json') for ba in result.value], default=json_converter)
                QMetaObject.invokeMethod(self, "_populate_bank_accounts_combo_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, items_json))
        except Exception as e: self.app_core.logger.error(f"Error loading bank accounts for reconciliation: {e}", exc_info=True)

    @Slot(str)
    def _populate_bank_accounts_combo_slot(self, items_json: str):
        self.bank_account_combo.clear(); self.bank_account_combo.addItem("-- Select Bank Account --", 0)
        try:
            items = json.loads(items_json, object_hook=json_date_hook)
            self._bank_accounts_cache = [BankAccountSummaryData.model_validate(item) for item in items]
            for ba in self._bank_accounts_cache: self.bank_account_combo.addItem(f"{ba.account_name} ({ba.bank_name} - {ba.currency_code})", ba.id)
        except json.JSONDecodeError as e: self.app_core.logger.error(f"Error parsing bank accounts JSON for combo: {e}")

    @Slot(int)
    def _on_bank_account_changed(self, index: int):
        new_bank_account_id = self.bank_account_combo.itemData(index)
        self._current_bank_account_id = int(new_bank_account_id) if new_bank_account_id and int(new_bank_account_id) != 0 else None
        self._current_bank_account_gl_id = None; self._current_bank_account_currency = "SGD" 
        self._current_draft_reconciliation_id = None 

        if self._current_bank_account_id:
            selected_ba_dto = next((ba for ba in self._bank_accounts_cache if ba.id == self._current_bank_account_id), None)
            if selected_ba_dto:
                self._current_bank_account_currency = selected_ba_dto.currency_code
                self.statement_balance_spin.setSuffix(f" {selected_ba_dto.currency_code}")
        
        self.statement_lines_model.update_data([]); self.system_txns_model.update_data([])
        self.draft_matched_statement_model.update_data([]); self.draft_matched_system_model.update_data([])
        self._reset_summary_figures(); self._calculate_and_display_balances() 
        self._update_selection_totals()
        self._load_reconciliation_history(1) 
        self.history_details_group.setVisible(False)
        self._history_statement_txns_model.update_data([])
        self._history_system_txns_model.update_data([])

    @Slot(float)
    def _on_statement_balance_changed(self, value: float):
        self._statement_ending_balance = Decimal(str(value)); self._calculate_and_display_balances()

    @Slot()
    def _on_load_transactions_clicked(self):
        if not self._current_bank_account_id: QMessageBox.warning(self, "Selection Required", "Please select a bank account."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "No user logged in."); return

        statement_date = self.statement_date_edit.date().toPython()
        self._statement_ending_balance = Decimal(str(self.statement_balance_spin.value()))
        self.load_transactions_button.setEnabled(False); self.load_transactions_button.setText("Loading...")
        
        schedule_task_from_qt(
            self._fetch_and_populate_transactions(
                self._current_bank_account_id, 
                statement_date,
                self._statement_ending_balance, 
                self.app_core.current_user.id
            )
        )
        self._load_reconciliation_history(1) 

    async def _fetch_and_populate_transactions(self, bank_account_id: int, statement_date: python_date, statement_ending_balance: Decimal, user_id: int):
        self.load_transactions_button.setEnabled(True); self.load_transactions_button.setText("Load / Refresh Transactions")
        self.match_selected_button.setEnabled(False); self._update_unmatch_button_state()
        if not all([self.app_core.bank_reconciliation_service, self.app_core.bank_transaction_manager, self.app_core.account_service, self.app_core.journal_service, self.app_core.bank_account_service]):
            self.app_core.logger.error("One or more required services are not available for reconciliation."); return
        try:
            async with self.app_core.db_manager.session() as session: 
                draft_recon_orm = await self.app_core.bank_reconciliation_service.get_or_create_draft_reconciliation(bank_account_id, statement_date, statement_ending_balance, user_id, session)
                if not draft_recon_orm or not draft_recon_orm.id:
                    QMessageBox.critical(self, "Error", "Could not get or create a draft reconciliation record."); return
                self._current_draft_reconciliation_id = draft_recon_orm.id
                QMetaObject.invokeMethod(self.statement_balance_spin, "setValue", Qt.ConnectionType.QueuedConnection, Q_ARG(float, float(draft_recon_orm.statement_ending_balance)))
                selected_bank_account_orm = await self.app_core.bank_account_service.get_by_id(bank_account_id)
                if not selected_bank_account_orm or not selected_bank_account_orm.gl_account_id:
                    QMessageBox.critical(self, "Error", "Selected bank account or its GL link is invalid."); return
                self._current_bank_account_gl_id = selected_bank_account_orm.gl_account_id; self._current_bank_account_currency = selected_bank_account_orm.currency_code
                self._book_balance_gl = await self.app_core.journal_service.get_account_balance(selected_bank_account_orm.gl_account_id, statement_date)
                unreconciled_result = await self.app_core.bank_transaction_manager.get_unreconciled_transactions_for_matching(bank_account_id, statement_date)
                if unreconciled_result.is_success and unreconciled_result.value:
                    self._all_loaded_statement_lines, self._all_loaded_system_transactions = unreconciled_result.value
                    stmt_lines_json = json.dumps([s.model_dump(mode='json') for s in self._all_loaded_statement_lines], default=json_converter)
                    sys_txns_json = json.dumps([s.model_dump(mode='json') for s in self._all_loaded_system_transactions], default=json_converter)
                    QMetaObject.invokeMethod(self, "_update_transaction_tables_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, stmt_lines_json), Q_ARG(str, sys_txns_json))
                else:
                    QMessageBox.warning(self, "Load Error", f"Failed to load unreconciled transactions: {', '.join(unreconciled_result.errors if unreconciled_result.errors else ['Unknown error'])}"); self.statement_lines_model.update_data([]); self.system_txns_model.update_data([])
                draft_stmt_items, draft_sys_items = await self.app_core.bank_reconciliation_service.get_transactions_for_reconciliation(self._current_draft_reconciliation_id)
                draft_stmt_json = json.dumps([s.model_dump(mode='json') for s in draft_stmt_items], default=json_converter); draft_sys_json = json.dumps([s.model_dump(mode='json') for s in draft_sys_items], default=json_converter)
                QMetaObject.invokeMethod(self, "_update_draft_matched_tables_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, draft_stmt_json), Q_ARG(str, draft_sys_json))
            self._reset_summary_figures(); self._calculate_and_display_balances(); self._update_selection_totals()
        except Exception as e:
            self.app_core.logger.error(f"Error during _fetch_and_populate_transactions: {e}", exc_info=True); QMessageBox.critical(self, "Error", f"An unexpected error occurred while loading reconciliation data: {e}")
            self._current_draft_reconciliation_id = None; self._update_match_button_state(); self._update_unmatch_button_state()

    @Slot(str)
    def _update_draft_matched_tables_slot(self, draft_stmt_json: str, draft_sys_json: str):
        try:
            draft_stmt_list_dict = json.loads(draft_stmt_json, object_hook=json_date_hook); self._current_draft_statement_lines = [BankTransactionSummaryData.model_validate(d) for d in draft_stmt_list_dict]
            
            stmt_row_colors = self._get_group_colors(self._current_draft_statement_lines)
            self.draft_matched_statement_model.update_data(self._current_draft_statement_lines, stmt_row_colors)
            
            draft_sys_list_dict = json.loads(draft_sys_json, object_hook=json_date_hook); self._current_draft_system_transactions = [BankTransactionSummaryData.model_validate(d) for d in draft_sys_list_dict]
            
            sys_row_colors = self._get_group_colors(self._current_draft_system_transactions)
            self.draft_matched_system_model.update_data(self._current_draft_system_transactions, sys_row_colors)
        except Exception as e: QMessageBox.critical(self, "Data Error", f"Failed to parse provisionally matched transaction data: {str(e)}")

    def _get_group_colors(self, transactions: List[BankTransactionSummaryData]) -> Dict[int, QColor]:
        """Analyzes sorted transactions and returns a dictionary mapping row index to group color."""
        row_colors: Dict[int, QColor] = {}
        if not transactions:
            return row_colors
            
        last_timestamp: Optional[datetime] = None
        color_index = 0
        time_delta_threshold = timedelta(seconds=2)

        # The transactions list is already sorted by updated_at desc from the service
        for row, txn in enumerate(transactions):
            if last_timestamp is None or (last_timestamp - txn.updated_at) > time_delta_threshold:
                color_index += 1 # New group detected
            
            row_colors[row] = self._group_colors[color_index % len(self._group_colors)]
            last_timestamp = txn.updated_at
            
        return row_colors

    @Slot(str, str)
    def _update_transaction_tables_slot(self, stmt_lines_json: str, sys_txns_json: str):
        try:
            stmt_list_dict = json.loads(stmt_lines_json, object_hook=json_date_hook); self._all_loaded_statement_lines = [BankTransactionSummaryData.model_validate(d) for d in stmt_list_dict]; self.statement_lines_model.update_data(self._all_loaded_statement_lines)
            sys_list_dict = json.loads(sys_txns_json, object_hook=json_date_hook); self._all_loaded_system_transactions = [BankTransactionSummaryData.model_validate(d) for d in sys_list_dict]; self.system_txns_model.update_data(self._all_loaded_system_transactions)
        except Exception as e: QMessageBox.critical(self, "Data Error", f"Failed to parse transaction data: {str(e)}")

    @Slot()
    def _update_selection_totals(self):
        stmt_items = self.statement_lines_model.get_checked_item_data(); self._current_stmt_selection_total = sum(item.amount for item in stmt_items)
        sys_items = self.system_txns_model.get_checked_item_data(); self._current_sys_selection_total = sum(item.amount for item in sys_items)
        self.statement_selection_total_label.setText(f"Statement Selected: {self._format_decimal(self._current_stmt_selection_total)}")
        self.system_selection_total_label.setText(f"System Selected: {self._format_decimal(self._current_sys_selection_total)}")
        is_match = abs(self._current_stmt_selection_total - self._current_sys_selection_total) < Decimal("0.01")
        color = "green" if is_match and (self._current_stmt_selection_total != 0 or self._current_sys_selection_total != 0) else "red"
        style = f"font-weight: bold; color: {color};"
        if not stmt_items and not sys_items: style = "font-weight: bold;" # Default color if nothing selected
        self.statement_selection_total_label.setStyleSheet(style); self.system_selection_total_label.setStyleSheet(style)
        self._update_match_button_state(); self._calculate_and_display_balances()

    def _reset_summary_figures(self):
        self._interest_earned_on_statement_not_in_book = Decimal(0); self._bank_charges_on_statement_not_in_book = Decimal(0)
        self._outstanding_system_deposits = Decimal(0); self._outstanding_system_withdrawals = Decimal(0)

    def _calculate_and_display_balances(self):
        self._reset_summary_figures() 
        for i in range(self.statement_lines_model.rowCount()):
            if self.statement_lines_model.get_row_check_state(i) == Qt.CheckState.Unchecked:
                item_dto = self.statement_lines_model.get_item_data_at_row(i)
                if item_dto:
                    if item_dto.amount > 0: self._interest_earned_on_statement_not_in_book += item_dto.amount
                    else: self._bank_charges_on_statement_not_in_book += abs(item_dto.amount)
        for i in range(self.system_txns_model.rowCount()):
            if self.system_txns_model.get_row_check_state(i) == Qt.CheckState.Unchecked:
                item_dto = self.system_txns_model.get_item_data_at_row(i)
                if item_dto:
                    if item_dto.amount > 0: self._outstanding_system_deposits += item_dto.amount
                    else: self._outstanding_system_withdrawals += abs(item_dto.amount)
        self.book_balance_gl_label.setText(f"{self._book_balance_gl:,.2f}"); 
        self.adj_interest_earned_label.setText(f"{self._interest_earned_on_statement_not_in_book:,.2f}"); 
        self.adj_bank_charges_label.setText(f"{self._bank_charges_on_statement_not_in_book:,.2f}")
        reconciled_book_balance = self._book_balance_gl + self._interest_earned_on_statement_not_in_book - self._bank_charges_on_statement_not_in_book
        self.adjusted_book_balance_label.setText(f"{reconciled_book_balance:,.2f}")
        self.statement_ending_balance_label.setText(f"{self._statement_ending_balance:,.2f}"); 
        self.adj_deposits_in_transit_label.setText(f"{self._outstanding_system_deposits:,.2f}"); 
        self.adj_outstanding_checks_label.setText(f"{self._outstanding_system_withdrawals:,.2f}")
        reconciled_bank_balance = self._statement_ending_balance + self._outstanding_system_deposits - self._outstanding_system_withdrawals
        self.adjusted_bank_balance_label.setText(f"{reconciled_bank_balance:,.2f}")
        self._difference = reconciled_bank_balance - reconciled_book_balance
        self.difference_label.setText(f"{self._difference:,.2f}")
        if abs(self._difference) < Decimal("0.01"): 
            self.difference_label.setStyleSheet("font-weight: bold; color: green;"); self.save_reconciliation_button.setEnabled(self._current_draft_reconciliation_id is not None)
        else: 
            self.difference_label.setStyleSheet("font-weight: bold; color: red;"); self.save_reconciliation_button.setEnabled(False)
        self.create_je_button.setEnabled(self._interest_earned_on_statement_not_in_book > 0 or self._bank_charges_on_statement_not_in_book > 0 or len(self.statement_lines_model.get_checked_item_data()) > 0)

    def _update_match_button_state(self):
        stmt_checked_count = len(self.statement_lines_model.get_checked_item_data())
        sys_checked_count = len(self.system_txns_model.get_checked_item_data())
        totals_match = abs(self._current_stmt_selection_total - self._current_sys_selection_total) < Decimal("0.01")
        self.match_selected_button.setEnabled(stmt_checked_count > 0 and sys_checked_count > 0 and totals_match and self._current_draft_reconciliation_id is not None)
        self.create_je_button.setEnabled(stmt_checked_count > 0 or self._interest_earned_on_statement_not_in_book > 0 or self._bank_charges_on_statement_not_in_book > 0)

    def _update_unmatch_button_state(self):
        draft_stmt_checked_count = len(self.draft_matched_statement_model.get_checked_item_data())
        draft_sys_checked_count = len(self.draft_matched_system_model.get_checked_item_data())
        self.unmatch_button.setEnabled(self._current_draft_reconciliation_id is not None and (draft_stmt_checked_count > 0 or draft_sys_checked_count > 0))

    @Slot()
    def _on_match_selected_clicked(self):
        if not self._current_draft_reconciliation_id: QMessageBox.warning(self, "Error", "No active reconciliation draft. Please load transactions first."); return
        selected_statement_items = self.statement_lines_model.get_checked_item_data()
        selected_system_items = self.system_txns_model.get_checked_item_data()
        if not selected_statement_items or not selected_system_items: QMessageBox.information(self, "Selection Needed", "Please select items from both tables to match."); return
        
        if abs(self._current_stmt_selection_total - self._current_sys_selection_total) > Decimal("0.01"): 
            QMessageBox.warning(self, "Match Error", f"Selected statement items total ({self._current_stmt_selection_total:,.2f}) and selected system items total ({self._current_sys_selection_total:,.2f}) do not match. Please ensure selections are balanced.")
            return
        
        all_selected_ids = [item.id for item in selected_statement_items] + [item.id for item in selected_system_items]
        self.match_selected_button.setEnabled(False); schedule_task_from_qt(self._perform_provisional_match(all_selected_ids))

    async def _perform_provisional_match(self, transaction_ids: List[int]):
        if self._current_draft_reconciliation_id is None: return 
        if not self.app_core.current_user: return
        try:
            success = await self.app_core.bank_reconciliation_service.mark_transactions_as_provisionally_reconciled(self._current_draft_reconciliation_id, transaction_ids, self.statement_date_edit.date().toPython(), self.app_core.current_user.id)
            if success: QMessageBox.information(self, "Items Matched", f"{len(transaction_ids)} items marked as provisionally reconciled for this session."); self._on_load_transactions_clicked() 
            else: QMessageBox.warning(self, "Match Error", "Failed to mark items as reconciled in the database.")
        except Exception as e: self.app_core.logger.error(f"Error during provisional match: {e}", exc_info=True); QMessageBox.critical(self, "Error", f"An unexpected error occurred while matching: {e}")
        finally: self._update_match_button_state()

    @Slot()
    def _on_unmatch_selected_clicked(self):
        if self._current_draft_reconciliation_id is None: QMessageBox.information(self, "Info", "No active draft reconciliation to unmatch from."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "No user logged in."); return
        selected_draft_stmt_items = self.draft_matched_statement_model.get_checked_item_data(); selected_draft_sys_items = self.draft_matched_system_model.get_checked_item_data()
        all_ids_to_unmatch = [item.id for item in selected_draft_stmt_items] + [item.id for item in selected_draft_sys_items]
        if not all_ids_to_unmatch: QMessageBox.information(self, "Selection Needed", "Please select items from the 'Provisionally Matched' tables to unmatch."); return
        self.unmatch_button.setEnabled(False); schedule_task_from_qt(self._perform_unmatch(all_ids_to_unmatch))

    async def _perform_unmatch(self, transaction_ids: List[int]):
        if not self.app_core.current_user: return
        try:
            success = await self.app_core.bank_reconciliation_service.unreconcile_transactions(transaction_ids, self.app_core.current_user.id)
            if success: QMessageBox.information(self, "Items Unmatched", f"{len(transaction_ids)} items have been unmarked and returned to the unreconciled lists."); self._on_load_transactions_clicked()
            else: QMessageBox.warning(self, "Unmatch Error", "Failed to unmatch items in the database.")
        except Exception as e: self.app_core.logger.error(f"Error during unmatch operation: {e}", exc_info=True); QMessageBox.critical(self, "Error", f"An unexpected error occurred while unmatching: {e}")
        finally: self._update_unmatch_button_state(); self._update_match_button_state()

    @Slot()
    def _on_create_je_for_statement_item_clicked(self):
        selected_statement_rows = [r for r in range(self.statement_lines_model.rowCount()) if self.statement_lines_model.get_row_check_state(r) == Qt.CheckState.Checked]
        if not selected_statement_rows: QMessageBox.information(self, "Selection Needed", "Please select a bank statement item to create a Journal Entry for."); return
        if len(selected_statement_rows) > 1: QMessageBox.information(self, "Selection Limit", "Please select only one statement item at a time to create a Journal Entry."); return
        selected_row = selected_statement_rows[0]; statement_item_dto = self.statement_lines_model.get_item_data_at_row(selected_row)
        if not statement_item_dto: return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        if self._current_bank_account_gl_id is None: QMessageBox.warning(self, "Error", "Current bank account GL link not found."); return
        bank_gl_account_id = self._current_bank_account_gl_id; statement_amount = statement_item_dto.amount
        bank_line: JournalEntryLineData
        if statement_amount > 0: bank_line = JournalEntryLineData(account_id=bank_gl_account_id, debit_amount=statement_amount, credit_amount=Decimal(0))
        else: bank_line = JournalEntryLineData(account_id=bank_gl_account_id, debit_amount=Decimal(0), credit_amount=abs(statement_amount))
        bank_line.description = f"Bank Rec: {statement_item_dto.description[:100]}"; bank_line.currency_code = self._current_bank_account_currency; bank_line.exchange_rate = Decimal(1)
        prefill_je_data = JournalEntryData(journal_type="General", entry_date=statement_item_dto.transaction_date, description=f"Entry for statement item: {statement_item_dto.description[:150]}", reference=statement_item_dto.reference, user_id=self.current_user_id, lines=[bank_line] )
        dialog = JournalEntryDialog(self.app_core, self.current_user_id, prefill_data_dict=prefill_je_data.model_dump(mode='json'), parent=self)
        dialog.journal_entry_saved.connect(lambda je_id: self._handle_je_created_for_statement_item(je_id, statement_item_dto.id))
        dialog.exec()

    @Slot(int, int)
    def _handle_je_created_for_statement_item(self, saved_je_id: int, original_statement_txn_id: int):
        self.app_core.logger.info(f"Journal Entry ID {saved_je_id} created for statement item ID {original_statement_txn_id}. Refreshing transactions..."); self._on_load_transactions_clicked() 

    @Slot()
    def _on_save_reconciliation_clicked(self):
        if self._current_draft_reconciliation_id is None: QMessageBox.warning(self, "Error", "No active reconciliation draft. Please load transactions first."); return
        if abs(self._difference) >= Decimal("0.01"): QMessageBox.warning(self, "Cannot Save", "Reconciliation is not balanced."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        self.save_reconciliation_button.setEnabled(False); self.save_reconciliation_button.setText("Saving..."); schedule_task_from_qt(self._perform_finalize_reconciliation())

    async def _perform_finalize_reconciliation(self):
        if not self.app_core.bank_reconciliation_service or self._current_draft_reconciliation_id is None:
            QMessageBox.critical(self, "Error", "Reconciliation Service or Draft ID not set."); self.save_reconciliation_button.setEnabled(abs(self._difference) < Decimal("0.01")); self.save_reconciliation_button.setText("Save Final Reconciliation"); return
        statement_end_bal_dec = Decimal(str(self.statement_balance_spin.value())); final_reconciled_book_balance_dec = self._book_balance_gl + self._interest_earned_on_statement_not_in_book - self._bank_charges_on_statement_not_in_book
        try:
            async with self.app_core.db_manager.session() as session: 
                result = await self.app_core.bank_reconciliation_service.finalize_reconciliation(self._current_draft_reconciliation_id, statement_end_bal_dec, final_reconciled_book_balance_dec, self._difference, self.app_core.current_user.id, session=session)
            if result.is_success and result.value:
                QMessageBox.information(self, "Success", f"Bank reconciliation finalized and saved successfully (ID: {result.value.id})."); self.reconciliation_saved.emit(result.value.id); self._current_draft_reconciliation_id = None; self._on_load_transactions_clicked(); self._load_reconciliation_history(1) 
            else: QMessageBox.warning(self, "Save Error", f"Failed to finalize reconciliation: {', '.join(result.errors if result.errors else ['Unknown error'])}")
        except Exception as e: self.app_core.logger.error(f"Error performing finalize reconciliation: {e}", exc_info=True); QMessageBox.warning(self, "Save Error", f"Failed to finalize reconciliation: {str(e)}")
        finally: self.save_reconciliation_button.setEnabled(abs(self._difference) < Decimal("0.01") and self._current_draft_reconciliation_id is not None); self.save_reconciliation_button.setText("Save Final Reconciliation")

    def _load_reconciliation_history(self, page_number: int):
        if not self._current_bank_account_id: self.history_table_model.update_data([]); self._update_history_pagination_controls(0, 0); return
        self._current_history_page = page_number; self.prev_history_button.setEnabled(False); self.next_history_button.setEnabled(False); schedule_task_from_qt(self._fetch_reconciliation_history())

    async def _fetch_reconciliation_history(self):
        if not self.app_core.bank_reconciliation_service or self._current_bank_account_id is None: self._update_history_pagination_controls(0,0); return
        history_data, total_records = await self.app_core.bank_reconciliation_service.get_reconciliations_for_account(self._current_bank_account_id, page=self._current_history_page, page_size=self._history_page_size)
        self._total_history_records = total_records; history_json = json.dumps([h.model_dump(mode='json') for h in history_data], default=json_converter)
        QMetaObject.invokeMethod(self, "_update_history_table_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, history_json))

    @Slot(str)
    def _update_history_table_slot(self, history_json_str: str):
        current_item_count = 0
        try:
            history_list_dict = json.loads(history_json_str, object_hook=json_date_hook)
            history_summaries = [BankReconciliationSummaryData.model_validate(d) for d in history_list_dict]; self.history_table_model.update_data(history_summaries); current_item_count = len(history_summaries)
        except Exception as e: QMessageBox.critical(self, "Error", f"Failed to display reconciliation history: {e}")
        self.history_details_group.setVisible(False); self._update_history_pagination_controls(current_item_count, self._total_history_records)

    def _update_history_pagination_controls(self, current_page_count: int, total_records: int):
        total_pages = (total_records + self._history_page_size - 1) // self._history_page_size;
        if total_pages == 0: total_pages = 1
        self.history_page_info_label.setText(f"Page {self._current_history_page} of {total_pages} ({total_records} Records)")
        self.prev_history_button.setEnabled(self._current_history_page > 1); self.next_history_button.setEnabled(self._current_history_page < total_pages)

    @Slot(QModelIndex, QModelIndex)
    def _on_history_selection_changed(self, current: QModelIndex, previous: QModelIndex):
        if not current.isValid(): self.history_details_group.setVisible(False); return
        selected_row = current.row(); reconciliation_id = self.history_table_model.get_reconciliation_id_at_row(selected_row)
        if reconciliation_id is not None: self.history_details_group.setTitle(f"Details for Reconciliation ID: {reconciliation_id}"); schedule_task_from_qt(self._load_historical_reconciliation_details(reconciliation_id))
        else: self.history_details_group.setVisible(False); self._history_statement_txns_model.update_data([]); self._history_system_txns_model.update_data([])

    async def _load_historical_reconciliation_details(self, reconciliation_id: int):
        if not self.app_core.bank_reconciliation_service: return
        statement_txns, system_txns = await self.app_core.bank_reconciliation_service.get_transactions_for_reconciliation(reconciliation_id)
        stmt_json = json.dumps([s.model_dump(mode='json') for s in statement_txns], default=json_converter); sys_json = json.dumps([s.model_dump(mode='json') for s in system_txns], default=json_converter)
        QMetaObject.invokeMethod(self, "_update_history_detail_tables_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, stmt_json), Q_ARG(str, sys_json))

    @Slot(str, str)
    def _update_history_detail_tables_slot(self, stmt_txns_json: str, sys_txns_json: str):
        try:
            stmt_list = json.loads(stmt_txns_json, object_hook=json_date_hook); stmt_dtos = [BankTransactionSummaryData.model_validate(d) for d in stmt_list]; self._history_statement_txns_model.update_data(stmt_dtos)
            sys_list = json.loads(sys_txns_json, object_hook=json_date_hook); sys_dtos = [BankTransactionSummaryData.model_validate(d) for d in sys_list]; self._history_system_txns_model.update_data(sys_dtos)
            self.history_details_group.setVisible(True)
        except Exception as e: QMessageBox.critical(self, "Error", f"Failed to display historical reconciliation details: {e}"); self.history_details_group.setVisible(False)

    def _format_decimal(self, value: Optional[Decimal], show_blank_for_zero: bool = False) -> str:
        if value is None: return "" if show_blank_for_zero else "0.00"
        try:
            d_val = Decimal(str(value))
            if show_blank_for_zero and d_val.is_zero(): return ""
            return f"{d_val:,.2f}"
        except (InvalidOperation, TypeError): return "Error"

```

# app/ui/banking/csv_import_config_dialog.py
```py
# File: app/ui/banking/csv_import_config_dialog.py
import os
import json
from typing import Optional, Dict, Any, TYPE_CHECKING, cast, Tuple, Union, List # Added List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox,
    QMessageBox, QCheckBox, QFileDialog, QLabel, QSpinBox, QGroupBox, QHBoxLayout
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon

from app.utils.result import Result
from app.utils.json_helpers import json_converter
from app.utils.pydantic_models import CSVImportErrorData
from app.ui.banking.csv_import_errors_dialog import CSVImportErrorsDialog

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from PySide6.QtGui import QPaintDevice


class CSVImportConfigDialog(QDialog):
    statement_imported = Signal(dict)

    FIELD_DATE = "date"; FIELD_DESCRIPTION = "description"; FIELD_DEBIT = "debit"; FIELD_CREDIT = "credit"; FIELD_AMOUNT = "amount"; FIELD_REFERENCE = "reference"; FIELD_VALUE_DATE = "value_date"
    
    FIELD_DISPLAY_NAMES = {
        FIELD_DATE: "Transaction Date*", FIELD_DESCRIPTION: "Description*", FIELD_DEBIT: "Debit Amount Column", FIELD_CREDIT: "Credit Amount Column",
        FIELD_AMOUNT: "Single Amount Column*", FIELD_REFERENCE: "Reference Column", FIELD_VALUE_DATE: "Value Date Column"
    }

    def __init__(self, app_core: "ApplicationCore", bank_account_id: int, current_user_id: int, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core; self.bank_account_id = bank_account_id; self.current_user_id = current_user_id
        self.setWindowTitle("Import Bank Statement from CSV"); self.setMinimumWidth(600); self.setModal(True)
        self.icon_path_prefix = "resources/icons/";
        try: import app.resources_rc; self.icon_path_prefix = ":/icons/"
        except ImportError: pass
        self._column_mapping_inputs: Dict[str, QLineEdit] = {}; self._init_ui(); self._connect_signals(); self._update_ui_for_column_type()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        file_group = QGroupBox("CSV File"); file_layout = QHBoxLayout(file_group)
        self.file_path_edit = QLineEdit(); self.file_path_edit.setReadOnly(True); self.file_path_edit.setPlaceholderText("Select CSV file to import...")
        browse_button = QPushButton(QIcon(self.icon_path_prefix + "open_company.svg"), "Browse..."); browse_button.setObjectName("BrowseButton")
        file_layout.addWidget(self.file_path_edit, 1); file_layout.addWidget(browse_button); main_layout.addWidget(file_group)
        format_group = QGroupBox("CSV Format Options"); format_layout = QFormLayout(format_group)
        self.has_header_check = QCheckBox("CSV file has a header row"); self.has_header_check.setChecked(True); format_layout.addRow(self.has_header_check)
        self.date_format_edit = QLineEdit("%d/%m/%Y"); date_format_hint = QLabel("Common: <code>%d/%m/%Y</code>, <code>%Y-%m-%d</code>, <code>%m/%d/%y</code>, <code>%b %d %Y</code>. <a href='https://strftime.org/'>More...</a>"); date_format_hint.setOpenExternalLinks(True); format_layout.addRow("Date Format*:", self.date_format_edit); format_layout.addRow("", date_format_hint); main_layout.addWidget(format_group)
        mapping_group = QGroupBox("Column Mapping (Enter column index or header name)"); self.mapping_form_layout = QFormLayout(mapping_group)
        for field_key in [self.FIELD_DATE, self.FIELD_DESCRIPTION, self.FIELD_REFERENCE, self.FIELD_VALUE_DATE]: edit = QLineEdit(); self._column_mapping_inputs[field_key] = edit; self.mapping_form_layout.addRow(self.FIELD_DISPLAY_NAMES[field_key] + ":", edit)
        self.use_single_amount_col_check = QCheckBox("Use a single column for Amount"); self.use_single_amount_col_check.setChecked(False); self.mapping_form_layout.addRow(self.use_single_amount_col_check)
        self._column_mapping_inputs[self.FIELD_DEBIT] = QLineEdit(); self.debit_amount_label = QLabel(self.FIELD_DISPLAY_NAMES[self.FIELD_DEBIT] + ":"); self.mapping_form_layout.addRow(self.debit_amount_label, self._column_mapping_inputs[self.FIELD_DEBIT])
        self._column_mapping_inputs[self.FIELD_CREDIT] = QLineEdit(); self.credit_amount_label = QLabel(self.FIELD_DISPLAY_NAMES[self.FIELD_CREDIT] + ":"); self.mapping_form_layout.addRow(self.credit_amount_label, self._column_mapping_inputs[self.FIELD_CREDIT])
        self._column_mapping_inputs[self.FIELD_AMOUNT] = QLineEdit(); self.single_amount_label = QLabel(self.FIELD_DISPLAY_NAMES[self.FIELD_AMOUNT] + ":"); self.mapping_form_layout.addRow(self.single_amount_label, self._column_mapping_inputs[self.FIELD_AMOUNT])
        self.debit_is_negative_check = QCheckBox("In single amount column, debits are negative values (credits are positive)"); self.debit_is_negative_check.setChecked(True); self.debit_negative_label = QLabel(); self.mapping_form_layout.addRow(self.debit_negative_label, self.debit_is_negative_check)
        main_layout.addWidget(mapping_group)
        self.button_box = QDialogButtonBox(); self.import_button = self.button_box.addButton("Import", QDialogButtonBox.ButtonRole.AcceptRole); self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel); main_layout.addWidget(self.button_box)
        self.setLayout(main_layout); self._on_has_header_changed(self.has_header_check.isChecked())

    def _connect_signals(self):
        browse_button = self.findChild(QPushButton, "BrowseButton");
        if browse_button: browse_button.clicked.connect(self._browse_file)
        self.has_header_check.stateChanged.connect(lambda state: self._on_has_header_changed(state == Qt.CheckState.Checked.value))
        self.use_single_amount_col_check.stateChanged.connect(self._update_ui_for_column_type)
        self.import_button.clicked.connect(self._collect_config_and_import)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button: cancel_button.clicked.connect(self.reject)

    @Slot()
    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Bank Statement CSV", "", "CSV Files (*.csv);;All Files (*)");
        if file_path: self.file_path_edit.setText(file_path)

    @Slot(bool)
    def _on_has_header_changed(self, checked: bool):
        placeholder = "Header Name (e.g., Transaction Date)" if checked else "Column Index (e.g., 0)"
        for edit_widget in self._column_mapping_inputs.values(): edit_widget.setPlaceholderText(placeholder)
            
    @Slot()
    def _update_ui_for_column_type(self):
        use_single_col = self.use_single_amount_col_check.isChecked()
        self.debit_amount_label.setVisible(not use_single_col); self._column_mapping_inputs[self.FIELD_DEBIT].setVisible(not use_single_col); self._column_mapping_inputs[self.FIELD_DEBIT].setEnabled(not use_single_col)
        self.credit_amount_label.setVisible(not use_single_col); self._column_mapping_inputs[self.FIELD_CREDIT].setVisible(not use_single_col); self._column_mapping_inputs[self.FIELD_CREDIT].setEnabled(not use_single_col)
        self.single_amount_label.setVisible(use_single_col); self._column_mapping_inputs[self.FIELD_AMOUNT].setVisible(use_single_col); self._column_mapping_inputs[self.FIELD_AMOUNT].setEnabled(use_single_col)
        self.debit_is_negative_check.setVisible(use_single_col); self.debit_negative_label.setVisible(use_single_col); self.debit_is_negative_check.setEnabled(use_single_col)

    def _get_column_specifier(self, field_edit: QLineEdit) -> Optional[Union[str, int]]:
        text = field_edit.text().strip()
        if not text: return None
        if self.has_header_check.isChecked(): return text 
        else:
            try: return int(text) 
            except ValueError: return None 

    @Slot()
    def _collect_config_and_import(self):
        file_path = self.file_path_edit.text().strip()
        if not file_path: QMessageBox.warning(self, "Input Error", "Please select a CSV file."); return
        if not os.path.exists(file_path): QMessageBox.warning(self, "Input Error", f"File not found: {file_path}"); return
        date_format = self.date_format_edit.text().strip()
        if not date_format: QMessageBox.warning(self, "Input Error", "Date format is required."); return
        column_map: Dict[str, Any] = {}; errors: List[str] = []
        date_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_DATE])
        if date_spec is None: errors.append("Date column mapping is required.")
        else: column_map[self.FIELD_DATE] = date_spec
        desc_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_DESCRIPTION])
        if desc_spec is None: errors.append("Description column mapping is required.")
        else: column_map[self.FIELD_DESCRIPTION] = desc_spec
        if self.use_single_amount_col_check.isChecked():
            amount_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_AMOUNT])
            if amount_spec is None: errors.append("Single Amount column mapping is required when selected.")
            else: column_map[self.FIELD_AMOUNT] = amount_spec
        else:
            debit_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_DEBIT])
            credit_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_CREDIT])
            if debit_spec is None and credit_spec is None: errors.append("At least one of Debit or Credit Amount column mapping is required if not using single amount column.")
            if debit_spec is not None: column_map[self.FIELD_DEBIT] = debit_spec
            if credit_spec is not None: column_map[self.FIELD_CREDIT] = credit_spec
        ref_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_REFERENCE]);
        if ref_spec is not None: column_map[self.FIELD_REFERENCE] = ref_spec
        val_date_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_VALUE_DATE]);
        if val_date_spec is not None: column_map[self.FIELD_VALUE_DATE] = val_date_spec
        if not self.has_header_check.isChecked():
            for key, val in list(column_map.items()):
                if val is not None and not isinstance(val, int): errors.append(f"Invalid column index for '{self.FIELD_DISPLAY_NAMES.get(key, key)}': '{val}'. Must be a number when not using headers.")
        if errors: QMessageBox.warning(self, "Configuration Error", "\n".join(errors)); return
        import_options = {"date_format_str": date_format, "skip_header": self.has_header_check.isChecked(), "debit_is_negative_in_single_col": self.debit_is_negative_check.isChecked() if self.use_single_amount_col_check.isChecked() else False, "use_single_amount_column": self.use_single_amount_col_check.isChecked()}
        self.import_button.setEnabled(False); self.import_button.setText("Importing...")
        future = schedule_task_from_qt(self.app_core.bank_transaction_manager.import_bank_statement_csv(self.bank_account_id, file_path, self.current_user_id, column_map, import_options))
        if future: future.add_done_callback(lambda res: QMetaObject.invokeMethod(self, "_handle_import_result_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, future)))
        else: self.app_core.logger.error("Failed to schedule bank statement import task."); self._handle_import_result_slot(None)

    @Slot(object)
    def _handle_import_result_slot(self, future_arg):
        self.import_button.setEnabled(True); self.import_button.setText("Import")
        if future_arg is None: QMessageBox.critical(self, "Task Error", "Failed to schedule import operation."); return
        try:
            result: Result[Dict[str, Any]] = future_arg.result()
            if result.is_success and result.value:
                summary = result.value
                detailed_errors = summary.get("detailed_errors", [])
                
                summary_msg_parts = [
                    f"Import Process Complete for Bank Account ID: {self.bank_account_id}",
                    f"Total Rows Processed: {summary.get('total_rows_in_file', 0)}",
                    f"Successfully Imported: {summary.get('imported_count', 0)}",
                    f"Skipped (Duplicates): {summary.get('skipped_duplicates_count', 0)}",
                    f"Skipped (Zero Amount): {summary.get('zero_amount_skipped_count', 0)}",
                    f"Failed (Errors): {len(detailed_errors)}"
                ]
                
                if detailed_errors:
                    error_dialog = CSVImportErrorsDialog(detailed_errors, self)
                    error_dialog.exec()
                    # After reviewing errors, show the summary message box
                    QMessageBox.warning(self, "Import Complete with Errors", "\n".join(summary_msg_parts))
                else:
                    QMessageBox.information(self, "Import Successful", "\n".join(summary_msg_parts))
                
                self.statement_imported.emit(summary) 
                self.accept()
            else:
                QMessageBox.warning(self, "Import Failed", f"Failed to import statement:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Exception handling import result: {e}", exc_info=True)
            QMessageBox.critical(self, "Import Error", f"An unexpected error occurred: {str(e)}")

```

# app/ui/dashboard/dashboard_widget.py
```py
# app/ui/dashboard/dashboard_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QGroupBox, QPushButton, QMessageBox,
    QScrollArea, QFrame, QFormLayout, QDateEdit
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QMargins, QDate
from PySide6.QtGui import QFont, QIcon, QPainter, QColor
from PySide6.QtCharts import QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis, QValueAxis

from typing import Optional, TYPE_CHECKING, List, Dict 
from decimal import Decimal, InvalidOperation 
import json 
from datetime import date as python_date, datetime, timedelta

from app.utils.pydantic_models import DashboardKPIData
from app.main import schedule_task_from_qt

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class DashboardWidget(QWidget):
    def __init__(self, app_core: "ApplicationCore", parent: Optional[QWidget] = None): 
        super().__init__(parent)
        self.app_core = app_core
        self._load_request_count = 0 
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass
            
        self._group_colors = [QColor("#4F81BD"), QColor("#C0504D"), QColor("#9BBB59")]

        self._init_ui()
        self.app_core.logger.info("DashboardWidget: Scheduling initial KPI load.")
        QTimer.singleShot(0, self._request_kpi_load)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        top_controls_layout = QHBoxLayout()
        top_controls_layout.addWidget(QLabel("<b>Dashboard As Of Date:</b>"))
        self.as_of_date_edit = QDateEdit(QDate.currentDate())
        self.as_of_date_edit.setCalendarPopup(True)
        self.as_of_date_edit.setDisplayFormat("dd/MM/yyyy")
        top_controls_layout.addWidget(self.as_of_date_edit)
        top_controls_layout.addStretch()
        self.refresh_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh KPIs")
        self.refresh_button.clicked.connect(self._request_kpi_load)
        top_controls_layout.addWidget(self.refresh_button)
        self.main_layout.addLayout(top_controls_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.main_layout.addWidget(scroll_area)

        container_widget = QWidget()
        scroll_area.setWidget(container_widget)
        
        container_layout = QVBoxLayout(container_widget)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        kpi_group = QGroupBox("Key Performance Indicators")
        container_layout.addWidget(kpi_group)
        
        self.kpi_layout = QGridLayout(kpi_group) 
        self.kpi_layout.setSpacing(10)
        self.kpi_layout.setColumnStretch(1, 1) 
        self.kpi_layout.setColumnStretch(3, 1) 
        self.kpi_layout.setColumnMinimumWidth(0, 220) 
        self.kpi_layout.setColumnMinimumWidth(2, 220) 

        def add_kpi_row(layout: QGridLayout, row: int, col_offset: int, title: str) -> QLabel:
            title_label = QLabel(title)
            title_label.setFont(QFont(self.font().family(), -1, QFont.Weight.Bold))
            value_label = QLabel("Loading...")
            value_label.setFont(QFont(self.font().family(), 11)) 
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(title_label, row, col_offset)
            layout.addWidget(value_label, row, col_offset + 1)
            return value_label

        current_row = 0
        self.period_label = QLabel("Period: Loading...")
        self.period_label.setStyleSheet("font-style: italic; color: grey;")
        self.kpi_layout.addWidget(self.period_label, current_row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter) 

        self.base_currency_label = QLabel("Currency: Loading...")
        self.base_currency_label.setStyleSheet("font-style: italic; color: grey;")
        self.kpi_layout.addWidget(self.base_currency_label, current_row, 2, 1, 2, Qt.AlignmentFlag.AlignCenter) 
        current_row += 1
        
        self.revenue_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Revenue (YTD):")
        self.cash_balance_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Current Cash Balance:")
        current_row += 1
        self.expenses_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Expenses (YTD):")
        self.current_ratio_label = add_kpi_row(self.kpi_layout, current_row, 2, "Current Ratio:") 
        current_row += 1
        self.net_profit_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Net Profit / (Loss) (YTD):")
        self.quick_ratio_label = add_kpi_row(self.kpi_layout, current_row, 2, "Quick Ratio (Acid Test):")
        current_row += 1
        
        self.debt_to_equity_label = add_kpi_row(self.kpi_layout, current_row, 2, "Debt-to-Equity Ratio:")
        current_row += 1

        self.kpi_layout.addWidget(QLabel("---"), current_row, 0, 1, 4) 
        current_row += 1
        self.ar_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Outstanding AR:")
        self.ap_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Total Outstanding AP:")
        current_row += 1
        self.ar_overdue_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total AR Overdue:")
        self.ap_overdue_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Total AP Overdue:")
        current_row += 1
        
        self.ar_aging_chart_view = self._create_aging_chart_view("AR Aging Summary")
        self.kpi_layout.addWidget(self.ar_aging_chart_view, current_row, 0, 1, 2) 

        self.ap_aging_chart_view = self._create_aging_chart_view("AP Aging Summary")
        self.kpi_layout.addWidget(self.ap_aging_chart_view, current_row, 2, 1, 2) 
        
        container_layout.addStretch() 

    def _create_aging_chart_view(self, title: str) -> QChartView:
        chart = QChart()
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.legend().setVisible(False)
        chart.setMargins(QMargins(0,0,0,0))
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumHeight(250)
        return chart_view

    def _format_decimal_for_display(self, value: Optional[Decimal], currency_symbol: str = "") -> str:
        if value is None: return "N/A"
        prefix = f"{currency_symbol} " if currency_symbol else ""
        try:
            if not isinstance(value, Decimal) : value = Decimal(str(value))
            if not value.is_finite(): return "N/A (Infinite)" 
            return f"{prefix}{value:,.2f}"
        except (TypeError, InvalidOperation): return f"{prefix}Error"

    def _format_ratio_for_display(self, value: Optional[Decimal]) -> str:
        if value is None: return "N/A"
        try:
            if not isinstance(value, Decimal) : value = Decimal(str(value))
            if not value.is_finite(): return "N/A (Infinite)" 
            return f"{value:.2f} : 1"
        except (TypeError, InvalidOperation): return "Error"

    @Slot()
    def _request_kpi_load(self):
        self._load_request_count += 1
        self.app_core.logger.info(f"DashboardWidget: _request_kpi_load called (Count: {self._load_request_count}). Setting labels to 'Loading...'.")
        
        self.refresh_button.setEnabled(False)
        labels_to_reset = [
            self.revenue_value_label, self.expenses_value_label, self.net_profit_value_label,
            self.cash_balance_value_label, self.ar_value_label, self.ap_value_label,
            self.ar_overdue_value_label, self.ap_overdue_value_label,
            self.current_ratio_label, self.quick_ratio_label, self.debt_to_equity_label
        ]
        for label in labels_to_reset:
            if hasattr(self, 'app_core') and self.app_core and hasattr(self.app_core, 'logger'): 
                 self.app_core.logger.debug(f"DashboardWidget: Resetting label to 'Loading...'")
            label.setText("Loading...")
        
        self.ar_aging_chart_view.chart().removeAllSeries()
        self.ap_aging_chart_view.chart().removeAllSeries()

        self.period_label.setText("Period: Loading...")
        self.base_currency_label.setText("Currency: Loading...")

        as_of_date = self.as_of_date_edit.date().toPython()
        future = schedule_task_from_qt(self._fetch_kpis_data(as_of_date))
        if future:
            future.add_done_callback(
                lambda res: QMetaObject.invokeMethod(self.refresh_button, "setEnabled", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, True))
            )
        else:
            self.app_core.logger.error("DashboardWidget: Failed to schedule _fetch_kpis_data task.")
            self.refresh_button.setEnabled(True) 

    async def _fetch_kpis_data(self, as_of_date: python_date):
        self.app_core.logger.info("DashboardWidget: _fetch_kpis_data started.")
        kpi_data_result: Optional[DashboardKPIData] = None
        json_payload: Optional[str] = None
        try:
            if not self.app_core.dashboard_manager:
                self.app_core.logger.error("DashboardWidget: Dashboard Manager not available in _fetch_kpis_data.")
            else:
                kpi_data_result = await self.app_core.dashboard_manager.get_dashboard_kpis(as_of_date=as_of_date)
                if kpi_data_result:
                    self.app_core.logger.info(f"DashboardWidget: Fetched KPI data: Period='{kpi_data_result.kpi_period_description}', Revenue='{kpi_data_result.total_revenue_ytd}'")
                    json_payload = kpi_data_result.model_dump_json()
                else:
                    self.app_core.logger.warning("DashboardWidget: DashboardManager.get_dashboard_kpis returned None.")
        except Exception as e:
            self.app_core.logger.error(f"DashboardWidget: Exception in _fetch_kpis_data during manager call: {e}", exc_info=True)
        
        self.app_core.logger.info(f"DashboardWidget: Queuing _update_kpi_display_slot with payload: {'JSON string' if json_payload else 'None'}")
        QMetaObject.invokeMethod(self, "_update_kpi_display_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_payload if json_payload is not None else ""))

    @Slot(str)
    def _update_kpi_display_slot(self, kpi_data_json_str: str):
        self.app_core.logger.info(f"DashboardWidget: _update_kpi_display_slot called. Received JSON string length: {len(kpi_data_json_str)}")
        self.refresh_button.setEnabled(True)
        
        kpi_data_dto: Optional[DashboardKPIData] = None
        if kpi_data_json_str:
            try:
                kpi_data_dto = DashboardKPIData.model_validate_json(kpi_data_json_str)
                self.app_core.logger.info(f"DashboardWidget: Successfully deserialized KPI JSON to DTO.")
            except Exception as e:
                self.app_core.logger.error(f"DashboardWidget: Error deserializing/validating KPI JSON: '{kpi_data_json_str[:100]}...' - Error: {e}", exc_info=True)
        
        if kpi_data_dto:
            self.app_core.logger.info(f"DashboardWidget: Updating UI with KPI Data: Period='{kpi_data_dto.kpi_period_description}'")
            self.period_label.setText(f"Period: {kpi_data_dto.kpi_period_description}")
            self.base_currency_label.setText(f"Currency: {kpi_data_dto.base_currency}")
            bc_symbol = kpi_data_dto.base_currency 
            
            self.revenue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_revenue_ytd, bc_symbol))
            self.expenses_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_expenses_ytd, bc_symbol))
            self.net_profit_value_label.setText(self._format_decimal_for_display(kpi_data_dto.net_profit_ytd, bc_symbol))
            self.cash_balance_value_label.setText(self._format_decimal_for_display(kpi_data_dto.current_cash_balance, bc_symbol))
            self.ar_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_outstanding_ar, bc_symbol))
            self.ap_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_outstanding_ap, bc_symbol))
            self.ar_overdue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_ar_overdue, bc_symbol)) 
            self.ap_overdue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_ap_overdue, bc_symbol)) 

            self._update_aging_chart(self.ar_aging_chart_view, kpi_data_dto, "ar")
            self.ap_aging_chart_view.chart().setTitleFont(QFont(self.font().family(), -1, QFont.Weight.Bold))
            self._update_aging_chart(self.ap_aging_chart_view, kpi_data_dto, "ap")
            
            self.current_ratio_label.setText(self._format_ratio_for_display(kpi_data_dto.current_ratio))
            self.quick_ratio_label.setText(self._format_ratio_for_display(kpi_data_dto.quick_ratio))
            self.debt_to_equity_label.setText(self._format_ratio_for_display(kpi_data_dto.debt_to_equity_ratio))

            self.app_core.logger.info("DashboardWidget: UI labels and charts updated with KPI data.")
        else:
            self.app_core.logger.warning("DashboardWidget: _update_kpi_display_slot called with no valid DTO. Setting error text.")
            error_text = "N/A - Data unavailable"
            for label in [self.revenue_value_label, self.expenses_value_label, self.net_profit_value_label,
                          self.cash_balance_value_label, self.ar_value_label, self.ap_value_label,
                          self.ar_overdue_value_label, self.ap_overdue_value_label,
                          self.current_ratio_label, self.quick_ratio_label, self.debt_to_equity_label]:
                label.setText(error_text)
            self.ar_aging_chart_view.chart().removeAllSeries()
            self.ap_aging_chart_view.chart().removeAllSeries()
            self.period_label.setText("Period: N/A")
            self.base_currency_label.setText("Currency: N/A")
            if kpi_data_json_str: 
                 QMessageBox.warning(self, "Dashboard Data Error", "Could not process Key Performance Indicators data.")

    def _update_aging_chart(self, chart_view: QChartView, kpi_data: DashboardKPIData, data_prefix: str):
        chart = chart_view.chart()
        chart.removeAllSeries()
        for axis in chart.axes(): chart.removeAxis(axis)

        bar_set = QBarSet("Amount")
        bar_set.setColor(QColor("#4F81BD"))
        
        aging_data = [
            kpi_data.ar_aging_current if data_prefix == "ar" else kpi_data.ap_aging_current,
            kpi_data.ar_aging_1_30 if data_prefix == "ar" else kpi_data.ap_aging_1_30,
            kpi_data.ar_aging_31_60 if data_prefix == "ar" else kpi_data.ap_aging_31_60,
            kpi_data.ar_aging_61_90 if data_prefix == "ar" else kpi_data.ap_aging_61_90,
            kpi_data.ar_aging_91_plus if data_prefix == "ar" else kpi_data.ap_aging_91_plus
        ]
        
        max_val = 0
        for val in aging_data:
            float_val = float(val)
            bar_set.append(float_val)
            if float_val > max_val: max_val = float_val

        series = QBarSeries()
        series.append(bar_set)
        series.setLabelsVisible(True)
        series.setLabelsFormat("@value")
        chart.addSeries(series)

        categories = ["Current", "1-30", "31-60", "61-90", "91+"]
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%'i")
        axis_y.setRange(0, max_val * 1.15 if max_val > 0 else 100)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

```

# app/ui/reports/reports_widget.py
```py
# File: app/ui/reports/reports_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDateEdit, QPushButton, QFormLayout, 
    QLineEdit, QGroupBox, QHBoxLayout, QMessageBox, QSpacerItem, QSizePolicy,
    QTabWidget, QTextEdit, QComboBox, QFileDialog, QInputDialog, QCompleter,
    QStackedWidget, QTreeView, QTableView, 
    QAbstractItemView, QCheckBox 
)
from PySide6.QtCore import Qt, Slot, QDate, QTimer, QMetaObject, Q_ARG, QStandardPaths
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem, QFont, QColor
from typing import Optional, Dict, Any, TYPE_CHECKING, List 

import json
from decimal import Decimal, InvalidOperation
import os 
from datetime import date as python_date, timedelta 

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.pydantic_models import GSTReturnData, GSTTransactionLineDetail, FiscalYearData 
from app.utils.result import Result 
from app.models.accounting.gst_return import GSTReturn 
from app.models.accounting.account import Account 
from app.models.accounting.dimension import Dimension 
from app.models.accounting.fiscal_year import FiscalYear

from .trial_balance_table_model import TrialBalanceTableModel
from .general_ledger_table_model import GeneralLedgerTableModel

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice 

class ReportsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._prepared_gst_data: Optional[GSTReturnData] = None 
        self._saved_draft_gst_return_orm: Optional[GSTReturn] = None 
        self._current_financial_report_data: Optional[Dict[str, Any]] = None
        self._gl_accounts_cache: List[Dict[str, Any]] = [] 
        self._dimension_types_cache: List[str] = []
        self._dimension_codes_cache: Dict[str, List[Dict[str, Any]]] = {} 
        self._fiscal_years_cache: List[FiscalYearData] = []

        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass

        self.main_layout = QVBoxLayout(self)
        
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self._create_gst_f5_tab()
        self._create_financial_statements_tab()
        
        self.setLayout(self.main_layout)
        # Load data required for filter combos
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_fs_combo_data()))

    def _format_decimal_for_display(self, value: Optional[Decimal], default_str: str = "0.00", show_blank_for_zero: bool = False) -> str:
        if value is None: return default_str if not show_blank_for_zero else ""
        try:
            d_value = Decimal(str(value)); 
            if show_blank_for_zero and d_value.is_zero(): return ""
            return f"{d_value:,.2f}"
        except (InvalidOperation, TypeError): return "Error" 

    def _create_gst_f5_tab(self):
        gst_f5_widget = QWidget(); gst_f5_main_layout = QVBoxLayout(gst_f5_widget); gst_f5_group = QGroupBox("GST F5 Return Data Preparation"); gst_f5_group_layout = QVBoxLayout(gst_f5_group) 
        date_selection_layout = QHBoxLayout(); date_form = QFormLayout()
        self.gst_start_date_edit = QDateEdit(QDate.currentDate().addMonths(-3).addDays(-QDate.currentDate().day()+1)); self.gst_start_date_edit.setCalendarPopup(True); self.gst_start_date_edit.setDisplayFormat("dd/MM/yyyy"); date_form.addRow("Period Start Date:", self.gst_start_date_edit)
        self.gst_end_date_edit = QDateEdit(QDate.currentDate().addDays(-QDate.currentDate().day())); 
        if self.gst_end_date_edit.date() < self.gst_start_date_edit.date(): self.gst_end_date_edit.setDate(self.gst_start_date_edit.date().addMonths(1).addDays(-1))
        self.gst_end_date_edit.setCalendarPopup(True); self.gst_end_date_edit.setDisplayFormat("dd/MM/yyyy"); date_form.addRow("Period End Date:", self.gst_end_date_edit)
        date_selection_layout.addLayout(date_form); prepare_button_layout = QVBoxLayout()
        self.prepare_gst_button = QPushButton(QIcon(self.icon_path_prefix + "reports.svg"), "Prepare GST F5 Data"); self.prepare_gst_button.clicked.connect(self._on_prepare_gst_f5_clicked)
        prepare_button_layout.addWidget(self.prepare_gst_button); prepare_button_layout.addStretch(); date_selection_layout.addLayout(prepare_button_layout); date_selection_layout.addStretch(1); gst_f5_group_layout.addLayout(date_selection_layout)
        self.gst_display_form = QFormLayout(); self.gst_std_rated_supplies_display = QLineEdit(); self.gst_std_rated_supplies_display.setReadOnly(True); self.gst_zero_rated_supplies_display = QLineEdit(); self.gst_zero_rated_supplies_display.setReadOnly(True); self.gst_exempt_supplies_display = QLineEdit(); self.gst_exempt_supplies_display.setReadOnly(True); self.gst_total_supplies_display = QLineEdit(); self.gst_total_supplies_display.setReadOnly(True); self.gst_total_supplies_display.setStyleSheet("font-weight: bold;"); self.gst_taxable_purchases_display = QLineEdit(); self.gst_taxable_purchases_display.setReadOnly(True); self.gst_output_tax_display = QLineEdit(); self.gst_output_tax_display.setReadOnly(True); self.gst_input_tax_display = QLineEdit(); self.gst_input_tax_display.setReadOnly(True); self.gst_adjustments_display = QLineEdit("0.00"); self.gst_adjustments_display.setReadOnly(True); self.gst_net_payable_display = QLineEdit(); self.gst_net_payable_display.setReadOnly(True); self.gst_net_payable_display.setStyleSheet("font-weight: bold;"); self.gst_filing_due_date_display = QLineEdit(); self.gst_filing_due_date_display.setReadOnly(True)
        self.gst_display_form.addRow("1. Standard-Rated Supplies:", self.gst_std_rated_supplies_display); self.gst_display_form.addRow("2. Zero-Rated Supplies:", self.gst_zero_rated_supplies_display); self.gst_display_form.addRow("3. Exempt Supplies:", self.gst_exempt_supplies_display); self.gst_display_form.addRow("4. Total Supplies (1+2+3):", self.gst_total_supplies_display); self.gst_display_form.addRow("5. Taxable Purchases:", self.gst_taxable_purchases_display); self.gst_display_form.addRow("6. Output Tax Due:", self.gst_output_tax_display); self.gst_display_form.addRow("7. Input Tax and Refunds Claimed:", self.gst_input_tax_display); self.gst_display_form.addRow("8. GST Adjustments:", self.gst_adjustments_display); self.gst_display_form.addRow("9. Net GST Payable / (Claimable):", self.gst_net_payable_display); self.gst_display_form.addRow("Filing Due Date:", self.gst_filing_due_date_display)
        gst_f5_group_layout.addLayout(self.gst_display_form)
        
        gst_action_button_layout = QHBoxLayout()
        self.save_draft_gst_button = QPushButton("Save Draft GST Return"); self.save_draft_gst_button.setEnabled(False); self.save_draft_gst_button.clicked.connect(self._on_save_draft_gst_return_clicked)
        self.finalize_gst_button = QPushButton("Finalize GST Return"); self.finalize_gst_button.setEnabled(False); self.finalize_gst_button.clicked.connect(self._on_finalize_gst_return_clicked)
        
        self.export_gst_detail_excel_button = QPushButton("Export Details (Excel)"); self.export_gst_detail_excel_button.setEnabled(False)
        self.export_gst_detail_excel_button.clicked.connect(self._on_export_gst_f5_details_excel_clicked)

        gst_action_button_layout.addStretch()
        gst_action_button_layout.addWidget(self.export_gst_detail_excel_button); gst_action_button_layout.addWidget(self.save_draft_gst_button); gst_action_button_layout.addWidget(self.finalize_gst_button)
        gst_f5_group_layout.addLayout(gst_action_button_layout)

        gst_f5_main_layout.addWidget(gst_f5_group); gst_f5_main_layout.addStretch(); self.tab_widget.addTab(gst_f5_widget, "GST F5 Preparation")

    @Slot()
    def _on_prepare_gst_f5_clicked(self):
        start_date = self.gst_start_date_edit.date().toPython(); end_date = self.gst_end_date_edit.date().toPython()
        if start_date > end_date: QMessageBox.warning(self, "Date Error", "Start date cannot be after end date."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        if not self.app_core.gst_manager: QMessageBox.critical(self, "Error", "GST Manager not available."); return
        self.prepare_gst_button.setEnabled(False); self.prepare_gst_button.setText("Preparing...")
        self._saved_draft_gst_return_orm = None; self.finalize_gst_button.setEnabled(False); self.export_gst_detail_excel_button.setEnabled(False) 
        future = schedule_task_from_qt(self.app_core.gst_manager.prepare_gst_return_data(start_date, end_date, self.app_core.current_user.id))
        if future: future.add_done_callback(lambda res: QMetaObject.invokeMethod(self, "_safe_handle_prepare_gst_f5_result_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, future)))
        else: self.app_core.logger.error("Failed to schedule GST data preparation task."); self._handle_prepare_gst_f5_result(None) 

    @Slot(object)
    def _safe_handle_prepare_gst_f5_result_slot(self, future_arg):
        self._handle_prepare_gst_f5_result(future_arg)

    def _handle_prepare_gst_f5_result(self, future):
        self.prepare_gst_button.setEnabled(True); self.prepare_gst_button.setText("Prepare GST F5 Data"); self.export_gst_detail_excel_button.setEnabled(False) 
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule GST data preparation."); self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False); return
        try:
            result: Result[GSTReturnData] = future.result()
            if result.is_success and result.value: 
                self._prepared_gst_data = result.value; self._update_gst_f5_display(self._prepared_gst_data)
                self.save_draft_gst_button.setEnabled(True); self.finalize_gst_button.setEnabled(False) 
                if self._prepared_gst_data and self._prepared_gst_data.detailed_breakdown: self.export_gst_detail_excel_button.setEnabled(True)
            else: self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False); QMessageBox.warning(self, "GST Data Error", f"Failed to prepare GST data:\n{', '.join(result.errors)}")
        except Exception as e: self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False); self.app_core.logger.error(f"Exception handling GST F5 preparation result: {e}", exc_info=True); QMessageBox.critical(self, "GST Data Error", f"An unexpected error occurred: {str(e)}")

    def _update_gst_f5_display(self, gst_data: GSTReturnData):
        self.gst_std_rated_supplies_display.setText(self._format_decimal_for_display(gst_data.standard_rated_supplies)); self.gst_zero_rated_supplies_display.setText(self._format_decimal_for_display(gst_data.zero_rated_supplies)); self.gst_exempt_supplies_display.setText(self._format_decimal_for_display(gst_data.exempt_supplies)); self.gst_total_supplies_display.setText(self._format_decimal_for_display(gst_data.total_supplies)); self.gst_taxable_purchases_display.setText(self._format_decimal_for_display(gst_data.taxable_purchases)); self.gst_output_tax_display.setText(self._format_decimal_for_display(gst_data.output_tax)); self.gst_input_tax_display.setText(self._format_decimal_for_display(gst_data.input_tax)); self.gst_adjustments_display.setText(self._format_decimal_for_display(gst_data.tax_adjustments)); self.gst_net_payable_display.setText(self._format_decimal_for_display(gst_data.tax_payable)); self.gst_filing_due_date_display.setText(gst_data.filing_due_date.strftime('%d/%m/%Y') if gst_data.filing_due_date else "")
    
    def _clear_gst_display_fields(self):
        for w in [self.gst_std_rated_supplies_display, self.gst_zero_rated_supplies_display, self.gst_exempt_supplies_display, self.gst_total_supplies_display, self.gst_taxable_purchases_display, self.gst_output_tax_display, self.gst_input_tax_display, self.gst_net_payable_display, self.gst_filing_due_date_display]: w.clear()
        self.gst_adjustments_display.setText("0.00"); self._prepared_gst_data = None; self._saved_draft_gst_return_orm = None; self.export_gst_detail_excel_button.setEnabled(False) 
    
    @Slot()
    def _on_save_draft_gst_return_clicked(self):
        if not self._prepared_gst_data: QMessageBox.warning(self, "No Data", "Please prepare GST data first."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        self._prepared_gst_data.user_id = self.app_core.current_user.id
        if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.id: self._prepared_gst_data.id = self._saved_draft_gst_return_orm.id
        self.save_draft_gst_button.setEnabled(False); self.save_draft_gst_button.setText("Saving Draft..."); self.finalize_gst_button.setEnabled(False)
        future = schedule_task_from_qt(self.app_core.gst_manager.save_gst_return(self._prepared_gst_data))
        if future: future.add_done_callback(lambda res: QMetaObject.invokeMethod(self, "_safe_handle_save_draft_gst_result_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, future)))
        else: self.app_core.logger.error("Failed to schedule GST draft save task."); self._handle_save_draft_gst_result(None)

    @Slot(object)
    def _safe_handle_save_draft_gst_result_slot(self, future_arg):
        self._handle_save_draft_gst_result(future_arg)

    def _handle_save_draft_gst_result(self, future):
        self.save_draft_gst_button.setEnabled(True); self.save_draft_gst_button.setText("Save Draft GST Return")
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule GST draft save."); return
        try:
            result: Result[GSTReturn] = future.result()
            if result.is_success and result.value: 
                self._saved_draft_gst_return_orm = result.value
                if self._prepared_gst_data: self._prepared_gst_data.id = result.value.id 
                QMessageBox.information(self, "Success", f"GST Return draft saved successfully (ID: {result.value.id})."); self.finalize_gst_button.setEnabled(True); self.export_gst_detail_excel_button.setEnabled(bool(self._prepared_gst_data and self._prepared_gst_data.detailed_breakdown))
            else: QMessageBox.warning(self, "Save Error", f"Failed to save GST Return draft:\n{', '.join(result.errors)}"); self.finalize_gst_button.setEnabled(False)
        except Exception as e: self.app_core.logger.error(f"Exception handling save draft GST result: {e}", exc_info=True); QMessageBox.critical(self, "Save Error", f"An unexpected error occurred: {str(e)}"); self.finalize_gst_button.setEnabled(False)

    @Slot()
    def _on_finalize_gst_return_clicked(self):
        if not self._saved_draft_gst_return_orm or not self._saved_draft_gst_return_orm.id: QMessageBox.warning(self, "No Draft", "Please prepare and save a draft GST return first."); return
        if self._saved_draft_gst_return_orm.status != "Draft": QMessageBox.information(self, "Already Processed", f"This GST Return (ID: {self._saved_draft_gst_return_orm.id}) is already '{self._saved_draft_gst_return_orm.status}'."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        submission_ref, ok_ref = QInputDialog.getText(self, "Finalize GST Return", "Enter Submission Reference No.:")
        if not ok_ref or not submission_ref.strip(): QMessageBox.information(self, "Cancelled", "Submission reference not provided. Finalization cancelled."); return
        submission_date_str, ok_date = QInputDialog.getText(self, "Finalize GST Return", "Enter Submission Date (YYYY-MM-DD):", text=python_date.today().isoformat())
        if not ok_date or not submission_date_str.strip(): QMessageBox.information(self, "Cancelled", "Submission date not provided. Finalization cancelled."); return
        try: parsed_submission_date = python_date.fromisoformat(submission_date_str)
        except ValueError: QMessageBox.warning(self, "Invalid Date", "Submission date format is invalid. Please use YYYY-MM-DD."); return
        self.finalize_gst_button.setEnabled(False); self.finalize_gst_button.setText("Finalizing..."); self.save_draft_gst_button.setEnabled(False); self.export_gst_detail_excel_button.setEnabled(False)
        future = schedule_task_from_qt(self.app_core.gst_manager.finalize_gst_return(return_id=self._saved_draft_gst_return_orm.id, submission_reference=submission_ref.strip(), submission_date=parsed_submission_date, user_id=self.app_core.current_user.id))
        if future: future.add_done_callback(lambda res: QMetaObject.invokeMethod(self, "_safe_handle_finalize_gst_result_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, future)))
        else: self.app_core.logger.error("Failed to schedule GST finalization task."); self._handle_finalize_gst_result(None)

    @Slot(object)
    def _safe_handle_finalize_gst_result_slot(self, future_arg):
        self._handle_finalize_gst_result(future_arg)

    def _handle_finalize_gst_result(self, future): 
        self.finalize_gst_button.setText("Finalize GST Return"); can_finalize_default = self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.status == "Draft"; can_save_draft_default = self._prepared_gst_data is not None and (not self._saved_draft_gst_return_orm or self._saved_draft_gst_return_orm.status == "Draft"); can_export_detail_default = bool(self._prepared_gst_data and self._prepared_gst_data.detailed_breakdown)
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule GST finalization."); self.finalize_gst_button.setEnabled(can_finalize_default); self.save_draft_gst_button.setEnabled(can_save_draft_default); self.export_gst_detail_excel_button.setEnabled(can_export_detail_default); return
        try:
            result: Result[GSTReturn] = future.result()
            if result.is_success and result.value: 
                QMessageBox.information(self, "Success", f"GST Return (ID: {result.value.id}) finalized successfully.\nStatus: {result.value.status}.\nSettlement JE ID: {result.value.journal_entry_id or 'N/A'}"); self._saved_draft_gst_return_orm = result.value; self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False); self.export_gst_detail_excel_button.setEnabled(can_export_detail_default) 
                if self._prepared_gst_data: self._prepared_gst_data.status = result.value.status
            else: QMessageBox.warning(self, "Finalization Error", f"Failed to finalize GST Return:\n{', '.join(result.errors)}"); self.finalize_gst_button.setEnabled(can_finalize_default); self.save_draft_gst_button.setEnabled(can_save_draft_default); self.export_gst_detail_excel_button.setEnabled(can_export_detail_default)
        except Exception as e: self.app_core.logger.error(f"Exception handling finalize GST result: {e}", exc_info=True); QMessageBox.critical(self, "Finalization Error", f"An unexpected error occurred: {str(e)}"); self.finalize_gst_button.setEnabled(can_finalize_default); self.save_draft_gst_button.setEnabled(can_save_draft_default); self.export_gst_detail_excel_button.setEnabled(can_export_detail_default)

    @Slot()
    def _on_export_gst_f5_details_excel_clicked(self):
        if not self._prepared_gst_data or not self._prepared_gst_data.detailed_breakdown: QMessageBox.warning(self, "No Data", "Please prepare GST data with details first."); return
        default_filename = f"GST_F5_Details_{self._prepared_gst_data.start_date.strftime('%Y%m%d')}_{self._prepared_gst_data.end_date.strftime('%Y%m%d')}.xlsx"; documents_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        file_path, _ = QFileDialog.getSaveFileName(self, "Save GST F5 Detail Report (Excel)", os.path.join(documents_path, default_filename), "Excel Files (*.xlsx);;All Files (*)")
        if file_path: 
            self.export_gst_detail_excel_button.setEnabled(False)
            future = schedule_task_from_qt(self.app_core.report_engine.export_report(self._prepared_gst_data, "gst_excel_detail"))
            if future: future.add_done_callback(lambda res, fp=file_path: QMetaObject.invokeMethod(self, "_safe_handle_gst_detail_export_result_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, future), Q_ARG(str, fp)))
            else: self.app_core.logger.error("Failed to schedule GST detail export task."); self.export_gst_detail_excel_button.setEnabled(True) 

    @Slot(object, str)
    def _safe_handle_gst_detail_export_result_slot(self, future_arg, file_path_arg: str):
        self._handle_gst_detail_export_result(future_arg, file_path_arg)

    def _handle_gst_detail_export_result(self, future, file_path: str):
        self.export_gst_detail_excel_button.setEnabled(True) 
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule GST detail export."); return
        try:
            report_bytes: Optional[bytes] = future.result()
            if report_bytes:
                with open(file_path, "wb") as f: f.write(report_bytes)
                QMessageBox.information(self, "Export Successful", f"GST F5 Detail Report exported to:\n{file_path}")
            else: QMessageBox.warning(self, "Export Failed", "Failed to generate GST F5 Detail report bytes.")
        except Exception as e: self.app_core.logger.error(f"Exception handling GST detail export result: {e}", exc_info=True); QMessageBox.critical(self, "Export Error", f"An error occurred during GST detail export: {str(e)}")
    
    def _create_financial_statements_tab(self):
        fs_widget = QWidget(); fs_main_layout = QVBoxLayout(fs_widget); fs_group = QGroupBox("Financial Statements"); fs_group_layout = QVBoxLayout(fs_group) 
        controls_layout = QHBoxLayout(); self.fs_params_form = QFormLayout() 
        self.fs_report_type_combo = QComboBox(); self.fs_report_type_combo.addItems(["Balance Sheet", "Profit & Loss Statement", "Trial Balance", "General Ledger", "Income Tax Computation"]); self.fs_params_form.addRow("Report Type:", self.fs_report_type_combo)
        self.fs_fiscal_year_label = QLabel("Fiscal Year:"); self.fs_fiscal_year_combo = QComboBox(); self.fs_fiscal_year_combo.setMinimumWidth(200); self.fs_params_form.addRow(self.fs_fiscal_year_label, self.fs_fiscal_year_combo)
        self.fs_gl_account_label = QLabel("Account for GL:"); self.fs_gl_account_combo = QComboBox(); self.fs_gl_account_combo.setMinimumWidth(250); self.fs_gl_account_combo.setEditable(True)
        completer = QCompleter([f"{item.get('code')} - {item.get('name')}" for item in self._gl_accounts_cache]); completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion); completer.setFilterMode(Qt.MatchFlag.MatchContains); self.fs_gl_account_combo.setCompleter(completer); self.fs_params_form.addRow(self.fs_gl_account_label, self.fs_gl_account_combo)
        self.fs_as_of_date_edit = QDateEdit(QDate.currentDate()); self.fs_as_of_date_edit.setCalendarPopup(True); self.fs_as_of_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow("As of Date:", self.fs_as_of_date_edit)
        self.fs_start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1).addDays(-QDate.currentDate().day()+1)); self.fs_start_date_edit.setCalendarPopup(True); self.fs_start_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow("Period Start Date:", self.fs_start_date_edit)
        self.fs_end_date_edit = QDateEdit(QDate.currentDate().addDays(-QDate.currentDate().day())); self.fs_end_date_edit.setCalendarPopup(True); self.fs_end_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow("Period End Date:", self.fs_end_date_edit)
        self.fs_include_zero_balance_check = QCheckBox("Include Zero-Balance Accounts"); self.fs_params_form.addRow(self.fs_include_zero_balance_check) 
        self.fs_include_comparative_check = QCheckBox("Include Comparative Period"); self.fs_params_form.addRow(self.fs_include_comparative_check)
        self.fs_comparative_as_of_date_label = QLabel("Comparative As of Date:"); self.fs_comparative_as_of_date_edit = QDateEdit(QDate.currentDate().addYears(-1)); self.fs_comparative_as_of_date_edit.setCalendarPopup(True); self.fs_comparative_as_of_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow(self.fs_comparative_as_of_date_label, self.fs_comparative_as_of_date_edit)
        self.fs_comparative_start_date_label = QLabel("Comparative Start Date:"); self.fs_comparative_start_date_edit = QDateEdit(QDate.currentDate().addYears(-1).addMonths(-1).addDays(-QDate.currentDate().day()+1)); self.fs_comparative_start_date_edit.setCalendarPopup(True); self.fs_comparative_start_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow(self.fs_comparative_start_date_label, self.fs_comparative_start_date_edit)
        self.fs_comparative_end_date_label = QLabel("Comparative End Date:"); self.fs_comparative_end_date_edit = QDateEdit(QDate.currentDate().addYears(-1).addDays(-QDate.currentDate().day())); self.fs_comparative_end_date_edit.setCalendarPopup(True); self.fs_comparative_end_date_edit.setDisplayFormat("dd/MM/yyyy"); self.fs_params_form.addRow(self.fs_comparative_end_date_label, self.fs_comparative_end_date_edit)
        self.fs_dim1_type_label = QLabel("Dimension 1 Type:"); self.fs_dim1_type_combo = QComboBox(); self.fs_dim1_type_combo.addItem("All Types", None); self.fs_dim1_type_combo.setObjectName("fs_dim1_type_combo"); self.fs_params_form.addRow(self.fs_dim1_type_label, self.fs_dim1_type_combo)
        self.fs_dim1_code_label = QLabel("Dimension 1 Code:"); self.fs_dim1_code_combo = QComboBox(); self.fs_dim1_code_combo.addItem("All Codes", None); self.fs_dim1_code_combo.setObjectName("fs_dim1_code_combo"); self.fs_params_form.addRow(self.fs_dim1_code_label, self.fs_dim1_code_combo)
        self.fs_dim2_type_label = QLabel("Dimension 2 Type:"); self.fs_dim2_type_combo = QComboBox(); self.fs_dim2_type_combo.addItem("All Types", None); self.fs_dim2_type_combo.setObjectName("fs_dim2_type_combo"); self.fs_params_form.addRow(self.fs_dim2_type_label, self.fs_dim2_type_combo)
        self.fs_dim2_code_label = QLabel("Dimension 2 Code:"); self.fs_dim2_code_combo = QComboBox(); self.fs_dim2_code_combo.addItem("All Codes", None); self.fs_dim2_code_combo.setObjectName("fs_dim2_code_combo"); self.fs_params_form.addRow(self.fs_dim2_code_label, self.fs_dim2_code_combo)
        controls_layout.addLayout(self.fs_params_form)
        generate_fs_button_layout = QVBoxLayout(); self.generate_fs_button = QPushButton(QIcon(self.icon_path_prefix + "reports.svg"), "Generate Report"); self.generate_fs_button.clicked.connect(self._on_generate_financial_report_clicked)
        generate_fs_button_layout.addWidget(self.generate_fs_button); generate_fs_button_layout.addStretch(); controls_layout.addLayout(generate_fs_button_layout); controls_layout.addStretch(1); fs_group_layout.addLayout(controls_layout)
        self.fs_display_stack = QStackedWidget(); fs_group_layout.addWidget(self.fs_display_stack, 1)
        self.bs_tree_view = QTreeView(); self.bs_tree_view.setAlternatingRowColors(True); self.bs_tree_view.setHeaderHidden(False); self.bs_tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.bs_model = QStandardItemModel(); self.bs_tree_view.setModel(self.bs_model); self.fs_display_stack.addWidget(self.bs_tree_view)
        self.pl_tree_view = QTreeView(); self.pl_tree_view.setAlternatingRowColors(True); self.pl_tree_view.setHeaderHidden(False); self.pl_tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.pl_model = QStandardItemModel(); self.pl_tree_view.setModel(self.pl_model); self.fs_display_stack.addWidget(self.pl_tree_view)
        self.tb_table_view = QTableView(); self.tb_table_view.setAlternatingRowColors(True); self.tb_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.tb_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection); self.tb_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.tb_table_view.setSortingEnabled(True); self.tb_model = TrialBalanceTableModel(); self.tb_table_view.setModel(self.tb_model); self.fs_display_stack.addWidget(self.tb_table_view)
        gl_widget_container = QWidget(); gl_layout = QVBoxLayout(gl_widget_container); gl_layout.setContentsMargins(0,0,0,0)
        self.gl_summary_label_account = QLabel("Account: N/A"); self.gl_summary_label_account.setStyleSheet("font-weight: bold;"); self.gl_summary_label_period = QLabel("Period: N/A"); self.gl_summary_label_ob = QLabel("Opening Balance: 0.00"); gl_summary_header_layout = QHBoxLayout(); gl_summary_header_layout.addWidget(self.gl_summary_label_account); gl_summary_header_layout.addStretch(); gl_summary_header_layout.addWidget(self.gl_summary_label_period); gl_layout.addLayout(gl_summary_header_layout); gl_layout.addWidget(self.gl_summary_label_ob)
        self.gl_table_view = QTableView(); self.gl_table_view.setAlternatingRowColors(True); self.gl_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.gl_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection); self.gl_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.gl_table_view.setSortingEnabled(True); self.gl_model = GeneralLedgerTableModel(); self.gl_table_view.setModel(self.gl_model); gl_layout.addWidget(self.gl_table_view)
        self.gl_summary_label_cb = QLabel("Closing Balance: 0.00"); self.gl_summary_label_cb.setAlignment(Qt.AlignmentFlag.AlignRight); gl_layout.addWidget(self.gl_summary_label_cb)
        self.fs_display_stack.addWidget(gl_widget_container); self.gl_widget_container = gl_widget_container 
        
        self.tax_comp_tree_view = QTreeView(); self.tax_comp_tree_view.setAlternatingRowColors(True); self.tax_comp_tree_view.setHeaderHidden(False); self.tax_comp_tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.tax_comp_model = QStandardItemModel(); self.tax_comp_tree_view.setModel(self.tax_comp_model); self.fs_display_stack.addWidget(self.tax_comp_tree_view)

        export_button_layout = QHBoxLayout(); self.export_pdf_button = QPushButton("Export to PDF"); self.export_pdf_button.setEnabled(False); self.export_pdf_button.clicked.connect(lambda: self._on_export_report_clicked("pdf")); self.export_excel_button = QPushButton("Export to Excel"); self.export_excel_button.setEnabled(False); self.export_excel_button.clicked.connect(lambda: self._on_export_report_clicked("excel")); export_button_layout.addStretch(); export_button_layout.addWidget(self.export_pdf_button); export_button_layout.addWidget(self.export_excel_button); fs_group_layout.addLayout(export_button_layout)
        fs_main_layout.addWidget(fs_group); self.tab_widget.addTab(fs_widget, "Financial Statements")
        self.fs_report_type_combo.currentTextChanged.connect(self._on_fs_report_type_changed)
        self.fs_include_comparative_check.stateChanged.connect(self._on_comparative_check_changed)
        self.fs_dim1_type_combo.currentIndexChanged.connect(lambda index, tc=self.fs_dim1_type_combo, cc=self.fs_dim1_code_combo: self._on_dimension_type_selected(tc, cc))
        self.fs_dim2_type_combo.currentIndexChanged.connect(lambda index, tc=self.fs_dim2_type_combo, cc=self.fs_dim2_code_combo: self._on_dimension_type_selected(tc, cc))
        self._on_fs_report_type_changed(self.fs_report_type_combo.currentText()) 

    async def _load_fs_combo_data(self):
        await self._load_gl_accounts_for_combo()
        await self._load_fiscal_years_for_combo()

    @Slot(str)
    def _on_fs_report_type_changed(self, report_type: str):
        is_bs = (report_type == "Balance Sheet"); is_pl = (report_type == "Profit & Loss Statement"); is_gl = (report_type == "General Ledger"); is_tb = (report_type == "Trial Balance"); is_tax = (report_type == "Income Tax Computation")
        self.fs_as_of_date_edit.setVisible(is_bs or is_tb); self.fs_start_date_edit.setVisible(is_pl or is_gl); self.fs_end_date_edit.setVisible(is_pl or is_gl)
        self.fs_fiscal_year_combo.setVisible(is_tax); self.fs_fiscal_year_label.setVisible(is_tax)
        self.fs_gl_account_combo.setVisible(is_gl); self.fs_gl_account_label.setVisible(is_gl); self.fs_include_zero_balance_check.setVisible(is_bs); self.fs_include_comparative_check.setVisible(is_bs or is_pl)
        for w in [self.fs_dim1_type_label, self.fs_dim1_type_combo, self.fs_dim1_code_label, self.fs_dim1_code_combo, self.fs_dim2_type_label, self.fs_dim2_type_combo, self.fs_dim2_code_label, self.fs_dim2_code_combo]: w.setVisible(is_gl)
        if is_gl and self.fs_dim1_type_combo.count() <= 1 : schedule_task_from_qt(self._load_dimension_types())
        self._on_comparative_check_changed(self.fs_include_comparative_check.checkState().value) 
        if is_gl: self.fs_display_stack.setCurrentWidget(self.gl_widget_container)
        elif is_bs: self.fs_display_stack.setCurrentWidget(self.bs_tree_view)
        elif is_pl: self.fs_display_stack.setCurrentWidget(self.pl_tree_view)
        elif is_tb: self.fs_display_stack.setCurrentWidget(self.tb_table_view)
        elif is_tax: self.fs_display_stack.setCurrentWidget(self.tax_comp_tree_view)
        self._clear_current_financial_report_display(); self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False)
    async def _load_dimension_types(self):
        if not self.app_core.dimension_service: self.app_core.logger.error("DimensionService not available."); return
        try:
            dim_types = await self.app_core.dimension_service.get_distinct_dimension_types(); json_data = json.dumps(dim_types)
            QMetaObject.invokeMethod(self, "_populate_dimension_types_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
        except Exception as e: self.app_core.logger.error(f"Error loading dimension types: {e}", exc_info=True)
    @Slot(str)
    def _populate_dimension_types_slot(self, dim_types_json_str: str):
        try: dim_types = json.loads(dim_types_json_str)
        except json.JSONDecodeError: self.app_core.logger.error("Failed to parse dimension types JSON."); return
        self._dimension_types_cache = ["All Types"] + dim_types 
        for combo in [self.fs_dim1_type_combo, self.fs_dim2_type_combo]:
            current_data = combo.currentData(); combo.clear(); combo.addItem("All Types", None)
            for dt in dim_types: combo.addItem(dt, dt)
            idx = combo.findData(current_data); 
            if idx != -1: combo.setCurrentIndex(idx)
            else: combo.setCurrentIndex(0) 
        self._on_dimension_type_selected(self.fs_dim1_type_combo, self.fs_dim1_code_combo); self._on_dimension_type_selected(self.fs_dim2_type_combo, self.fs_dim2_code_combo)
    @Slot(QComboBox, QComboBox) 
    def _on_dimension_type_selected(self, type_combo: QComboBox, code_combo: QComboBox):
        selected_type_str = type_combo.currentData() 
        if selected_type_str: schedule_task_from_qt(self._load_dimension_codes_for_type(selected_type_str, code_combo.objectName() or ""))
        else: code_combo.clear(); code_combo.addItem("All Codes", None)
    async def _load_dimension_codes_for_type(self, dim_type_str: str, target_code_combo_name: str):
        if not self.app_core.dimension_service: self.app_core.logger.error("DimensionService not available."); return
        try:
            dimensions: List[Dimension] = await self.app_core.dimension_service.get_dimensions_by_type(dim_type_str)
            dim_codes_data = [{"id": d.id, "code": d.code, "name": d.name} for d in dimensions]; self._dimension_codes_cache[dim_type_str] = dim_codes_data
            json_data = json.dumps(dim_codes_data, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_dimension_codes_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data), Q_ARG(str, target_code_combo_name))
        except Exception as e: self.app_core.logger.error(f"Error loading dimension codes for type '{dim_type_str}': {e}", exc_info=True)
    @Slot(str, str)
    def _populate_dimension_codes_slot(self, dim_codes_json_str: str, target_code_combo_name: str):
        target_combo: Optional[QComboBox] = self.findChild(QComboBox, target_code_combo_name)
        if not target_combo: self.app_core.logger.error(f"Target code combo '{target_code_combo_name}' not found."); return
        current_data = target_combo.currentData(); target_combo.clear(); target_combo.addItem("All Codes", None) 
        try:
            dim_codes = json.loads(dim_codes_json_str, object_hook=json_date_hook)
            for dc in dim_codes: target_combo.addItem(f"{dc['code']} - {dc['name']}", dc['id'])
            idx = target_combo.findData(current_data)
            if idx != -1: target_combo.setCurrentIndex(idx)
            else: target_combo.setCurrentIndex(0) 
        except json.JSONDecodeError: self.app_core.logger.error(f"Failed to parse dim codes JSON for {target_code_combo_name}")
    @Slot(int)
    def _on_comparative_check_changed(self, state: int):
        is_checked = (state == Qt.CheckState.Checked.value); report_type = self.fs_report_type_combo.currentText(); is_bs = (report_type == "Balance Sheet"); is_pl = (report_type == "Profit & Loss Statement")
        self.fs_comparative_as_of_date_label.setVisible(is_bs and is_checked); self.fs_comparative_as_of_date_edit.setVisible(is_bs and is_checked)
        self.fs_comparative_start_date_label.setVisible(is_pl and is_checked); self.fs_comparative_start_date_edit.setVisible(is_pl and is_checked)
        self.fs_comparative_end_date_label.setVisible(is_pl and is_checked); self.fs_comparative_end_date_edit.setVisible(is_pl and is_checked)
    async def _load_gl_accounts_for_combo(self):
        if not self.app_core.chart_of_accounts_manager: self.app_core.logger.error("ChartOfAccountsManager not available for GL account combo."); return
        try:
            accounts_orm: List[Account] = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(active_only=True)
            self._gl_accounts_cache = [{"id": acc.id, "code": acc.code, "name": acc.name} for acc in accounts_orm]
            accounts_json = json.dumps(self._gl_accounts_cache, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_gl_account_combo_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, accounts_json))
        except Exception as e: self.app_core.logger.error(f"Error loading accounts for GL combo: {e}", exc_info=True); QMessageBox.warning(self, "Account Load Error", "Could not load accounts for General Ledger selection.")
    @Slot(str)
    def _populate_gl_account_combo_slot(self, accounts_json_str: str):
        self.fs_gl_account_combo.clear()
        try:
            accounts_data = json.loads(accounts_json_str); self._gl_accounts_cache = accounts_data if accounts_data else []
            self.fs_gl_account_combo.addItem("-- Select Account --", 0) 
            for acc_data in self._gl_accounts_cache: self.fs_gl_account_combo.addItem(f"{acc_data['code']} - {acc_data['name']}", acc_data['id'])
            if isinstance(self.fs_gl_account_combo.completer(), QCompleter): self.fs_gl_account_combo.completer().setModel(self.fs_gl_account_combo.model())
        except json.JSONDecodeError: self.app_core.logger.error("Failed to parse accounts JSON for GL combo."); self.fs_gl_account_combo.addItem("Error loading accounts", 0)

    async def _load_fiscal_years_for_combo(self):
        if not self.app_core.fiscal_period_manager: self.app_core.logger.error("FiscalPeriodManager not available."); return
        try:
            fy_orms = await self.app_core.fiscal_period_manager.get_all_fiscal_years()
            self._fiscal_years_cache = [FiscalYearData.model_validate(fy) for fy in fy_orms]
            fy_json = json.dumps([fy.model_dump(mode='json') for fy in self._fiscal_years_cache])
            QMetaObject.invokeMethod(self, "_populate_fiscal_years_combo_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, fy_json))
        except Exception as e: self.app_core.logger.error(f"Error loading fiscal years for combo: {e}", exc_info=True)

    @Slot(str)
    def _populate_fiscal_years_combo_slot(self, fy_json_str: str):
        self.fs_fiscal_year_combo.clear()
        try:
            fy_dicts = json.loads(fy_json_str, object_hook=json_date_hook)
            self._fiscal_years_cache = [FiscalYearData.model_validate(fy) for fy in fy_dicts]
            if not self._fiscal_years_cache: self.fs_fiscal_year_combo.addItem("No fiscal years found", 0); return
            for fy_data in sorted(self._fiscal_years_cache, key=lambda fy: fy.start_date, reverse=True):
                self.fs_fiscal_year_combo.addItem(f"{fy_data.year_name} ({fy_data.start_date.strftime('%d/%m/%Y')} - {fy_data.end_date.strftime('%d/%m/%Y')})", fy_data.id)
        except Exception as e: self.app_core.logger.error(f"Error parsing fiscal years for combo: {e}"); self.fs_fiscal_year_combo.addItem("Error loading", 0)

    def _clear_current_financial_report_display(self):
        self._current_financial_report_data = None; current_view = self.fs_display_stack.currentWidget()
        if isinstance(current_view, QTreeView): model = current_view.model(); 
        if isinstance(model, QStandardItemModel): model.clear() 
        elif isinstance(current_view, QTableView): model = current_view.model(); 
        if hasattr(model, 'update_data'): model.update_data([]) 
        elif current_view == self.gl_widget_container : self.gl_model.update_data({}); self.gl_summary_label_account.setText("Account: N/A"); self.gl_summary_label_period.setText("Period: N/A"); self.gl_summary_label_ob.setText("Opening Balance: 0.00"); self.gl_summary_label_cb.setText("Closing Balance: 0.00")
    
    @Slot()
    def _on_generate_financial_report_clicked(self):
        report_type = self.fs_report_type_combo.currentText()
        if not self.app_core.financial_statement_generator: QMessageBox.critical(self, "Error", "Financial Statement Generator not available."); return
        self._clear_current_financial_report_display(); self.generate_fs_button.setEnabled(False); self.generate_fs_button.setText("Generating..."); self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False)
        coro: Optional[Any] = None; comparative_date_bs: Optional[python_date] = None; comparative_start_pl: Optional[python_date] = None; comparative_end_pl: Optional[python_date] = None; include_zero_bal_bs: bool = False
        dim1_id_val = self.fs_dim1_code_combo.currentData() if self.fs_dim1_type_label.isVisible() else None ; dim2_id_val = self.fs_dim2_code_combo.currentData() if self.fs_dim2_type_label.isVisible() else None
        dimension1_id = int(dim1_id_val) if dim1_id_val and dim1_id_val !=0 else None; dimension2_id = int(dim2_id_val) if dim2_id_val and dim2_id_val !=0 else None
        if self.fs_include_comparative_check.isVisible() and self.fs_include_comparative_check.isChecked():
            if report_type == "Balance Sheet": comparative_date_bs = self.fs_comparative_as_of_date_edit.date().toPython()
            elif report_type == "Profit & Loss Statement":
                comparative_start_pl = self.fs_comparative_start_date_edit.date().toPython(); comparative_end_pl = self.fs_comparative_end_date_edit.date().toPython()
                if comparative_start_pl and comparative_end_pl and comparative_start_pl > comparative_end_pl: QMessageBox.warning(self, "Date Error", "Comparative start date cannot be after comparative end date for P&L."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
        if report_type == "Balance Sheet": as_of_date_val = self.fs_as_of_date_edit.date().toPython(); include_zero_bal_bs = self.fs_include_zero_balance_check.isChecked() if self.fs_include_zero_balance_check.isVisible() else False; coro = self.app_core.financial_statement_generator.generate_balance_sheet(as_of_date_val, comparative_date=comparative_date_bs, include_zero_balances=include_zero_bal_bs)
        elif report_type == "Profit & Loss Statement": 
            start_date_val = self.fs_start_date_edit.date().toPython(); end_date_val = self.fs_end_date_edit.date().toPython()
            if start_date_val > end_date_val: QMessageBox.warning(self, "Date Error", "Start date cannot be after end date for P&L."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            coro = self.app_core.financial_statement_generator.generate_profit_loss(start_date_val, end_date_val, comparative_start=comparative_start_pl, comparative_end=comparative_end_pl)
        elif report_type == "Trial Balance": as_of_date_val = self.fs_as_of_date_edit.date().toPython(); coro = self.app_core.financial_statement_generator.generate_trial_balance(as_of_date_val)
        elif report_type == "General Ledger":
            account_id = self.fs_gl_account_combo.currentData(); 
            if not isinstance(account_id, int) or account_id == 0: QMessageBox.warning(self, "Selection Error", "Please select a valid account for the General Ledger report."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            start_date_val = self.fs_start_date_edit.date().toPython(); end_date_val = self.fs_end_date_edit.date().toPython() 
            if start_date_val > end_date_val: QMessageBox.warning(self, "Date Error", "Start date cannot be after end date for General Ledger."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            coro = self.app_core.financial_statement_generator.generate_general_ledger(account_id, start_date_val, end_date_val, dimension1_id, dimension2_id)
        elif report_type == "Income Tax Computation":
            fy_id = self.fs_fiscal_year_combo.currentData()
            if not isinstance(fy_id, int) or fy_id == 0: QMessageBox.warning(self, "Selection Error", "Please select a Fiscal Year for the Tax Computation report."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            fy_data_obj = next((fy for fy in self._fiscal_years_cache if fy.id == fy_id), None)
            if not fy_data_obj: QMessageBox.warning(self, "Data Error", f"Could not find data for selected fiscal year ID {fy_id}."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            coro = self.app_core.financial_statement_generator.generate_income_tax_computation(fy_data_obj) # Pass DTO

        future_obj: Optional[Any] = None ; 
        if coro: future_obj = schedule_task_from_qt(coro)
        if future_obj: future_obj.add_done_callback( lambda res: QMetaObject.invokeMethod( self, "_safe_handle_financial_report_result_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, future_obj)))
        else: self.app_core.logger.error(f"Failed to schedule report generation for {report_type}."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); self._handle_financial_report_result(None) 
    
    @Slot(object)
    def _safe_handle_financial_report_result_slot(self, future_arg): self._handle_financial_report_result(future_arg)
    
    def _handle_financial_report_result(self, future):
        self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); self.export_pdf_button.setEnabled(False) ; self.export_excel_button.setEnabled(False); self._current_financial_report_data = None
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule report generation."); return
        try:
            report_data: Optional[Dict[str, Any]] = future.result()
            if report_data: self._current_financial_report_data = report_data; self._display_financial_report(report_data); self.export_pdf_button.setEnabled(True); self.export_excel_button.setEnabled(True)
            else: QMessageBox.warning(self, "Report Error", "Failed to generate report data or report data is empty.")
        except Exception as e: self.app_core.logger.error(f"Exception handling financial report result: {e}", exc_info=True); QMessageBox.critical(self, "Report Generation Error", f"An unexpected error occurred: {str(e)}")

    def _populate_balance_sheet_model(self, model: QStandardItemModel, report_data: Dict[str, Any]):
        model.clear(); has_comparative = bool(report_data.get('comparative_date')); headers = ["Description", "Amount"]; 
        if has_comparative: headers.append(f"Comparative ({report_data.get('comparative_date','Prev').strftime('%d/%m/%Y') if isinstance(report_data.get('comparative_date'), python_date) else 'Prev'})")
        model.setHorizontalHeaderLabels(headers); root_node = model.invisibleRootItem(); bold_font = QFont(); bold_font.setBold(True)
        def add_account_rows(parent_item: QStandardItem, accounts: List[Dict[str,Any]], comparative_accounts: Optional[List[Dict[str,Any]]]):
            for acc_dict in accounts:
                desc_item = QStandardItem(f"  {acc_dict.get('code','')} - {acc_dict.get('name','')}"); amount_item = QStandardItem(self._format_decimal_for_display(acc_dict.get('balance'))); amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); row_items = [desc_item, amount_item]
                if has_comparative:
                    comp_val_str = ""; 
                    if comparative_accounts: comp_acc = next((ca for ca in comparative_accounts if ca['id'] == acc_dict['id']), None); comp_val_str = self._format_decimal_for_display(comp_acc['balance']) if comp_acc and comp_acc['balance'] is not None else ""
                    comp_amount_item = QStandardItem(comp_val_str); comp_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); row_items.append(comp_amount_item)
                parent_item.appendRow(row_items)
        for section_key, section_title_display in [('assets', "Assets"), ('liabilities', "Liabilities"), ('equity', "Equity")]:
            section_data = report_data.get(section_key); 
            if not section_data or not isinstance(section_data, dict): continue
            section_header_item = QStandardItem(section_title_display); section_header_item.setFont(bold_font); empty_amount_item = QStandardItem(""); empty_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); header_row = [section_header_item, empty_amount_item]; 
            if has_comparative: header_row.append(QStandardItem("")); root_node.appendRow(header_row)
            add_account_rows(section_header_item, section_data.get("accounts", []), section_data.get("comparative_accounts"))
            total_desc_item = QStandardItem(f"Total {section_title_display}"); total_desc_item.setFont(bold_font); total_amount_item = QStandardItem(self._format_decimal_for_display(section_data.get("total"))); total_amount_item.setFont(bold_font); total_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); total_row_items = [total_desc_item, total_amount_item]; 
            if has_comparative: comp_total_item = QStandardItem(self._format_decimal_for_display(section_data.get("comparative_total"))); comp_total_item.setFont(bold_font); comp_total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); total_row_items.append(comp_total_item)
            root_node.appendRow(total_row_items); 
            if section_key != 'equity': root_node.appendRow([QStandardItem(""), QStandardItem("")] + ([QStandardItem("")] if has_comparative else []))
        if 'total_liabilities_equity' in report_data:
            root_node.appendRow([QStandardItem(""), QStandardItem("")] + ([QStandardItem("")] if has_comparative else [])); tle_desc = QStandardItem("Total Liabilities & Equity"); tle_desc.setFont(bold_font); tle_amount = QStandardItem(self._format_decimal_for_display(report_data.get('total_liabilities_equity'))); tle_amount.setFont(bold_font); tle_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); tle_row = [tle_desc, tle_amount]; 
            if has_comparative: comp_tle_amount = QStandardItem(self._format_decimal_for_display(report_data.get('comparative_total_liabilities_equity'))); comp_tle_amount.setFont(bold_font); comp_tle_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); tle_row.append(comp_tle_amount)
            root_node.appendRow(tle_row)
        if report_data.get('is_balanced') is False: warning_item = QStandardItem("Warning: Balance Sheet is out of balance!"); warning_item.setForeground(QColor("red")); warning_item.setFont(bold_font); warning_row = [warning_item, QStandardItem("")]; 
        if has_comparative: warning_row.append(QStandardItem("")); root_node.appendRow(warning_row)
    
    def _populate_profit_loss_model(self, model: QStandardItemModel, report_data: Dict[str, Any]):
        model.clear(); has_comparative = bool(report_data.get('comparative_start')); comp_header_text = "Comparative"; 
        if has_comparative and report_data.get('comparative_start') and report_data.get('comparative_end'): comp_start_str = report_data['comparative_start'].strftime('%d/%m/%y'); comp_end_str = report_data['comparative_end'].strftime('%d/%m/%y'); comp_header_text = f"Comp. ({comp_start_str}-{comp_end_str})"
        headers = ["Description", "Amount"]; 
        if has_comparative: headers.append(comp_header_text); 
        model.setHorizontalHeaderLabels(headers); root_node = model.invisibleRootItem(); bold_font = QFont(); bold_font.setBold(True)
        def add_pl_account_rows(parent_item: QStandardItem, accounts: List[Dict[str,Any]], comparative_accounts: Optional[List[Dict[str,Any]]]):
            for acc_dict in accounts:
                desc_item = QStandardItem(f"  {acc_dict.get('code','')} - {acc_dict.get('name','')}"); amount_item = QStandardItem(self._format_decimal_for_display(acc_dict.get('balance'))); amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); row_items = [desc_item, amount_item]
                if has_comparative:
                    comp_val_str = ""; 
                    if comparative_accounts: comp_acc = next((ca for ca in comparative_accounts if ca['id'] == acc_dict['id']), None); comp_val_str = self._format_decimal_for_display(comp_acc['balance']) if comp_acc and comp_acc['balance'] is not None else ""
                    comp_amount_item = QStandardItem(comp_val_str); comp_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); row_items.append(comp_amount_item)
                parent_item.appendRow(row_items)
        for section_key, section_title_display in [('revenue', "Revenue"), ('expenses', "Operating Expenses")]: 
            section_data = report_data.get(section_key); 
            if not section_data or not isinstance(section_data, dict): continue
            section_header_item = QStandardItem(section_title_display); section_header_item.setFont(bold_font); empty_amount_item = QStandardItem(""); empty_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); header_row = [section_header_item, empty_amount_item]; 
            if has_comparative: header_row.append(QStandardItem("")); root_node.appendRow(header_row)
            add_pl_account_rows(section_header_item, section_data.get("accounts", []), section_data.get("comparative_accounts"))
            total_desc_item = QStandardItem(f"Total {section_title_display}"); total_desc_item.setFont(bold_font); total_amount_item = QStandardItem(self._format_decimal_for_display(section_data.get("total"))); total_amount_item.setFont(bold_font); total_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); total_row_items = [total_desc_item, total_amount_item]; 
            if has_comparative: comp_total_item = QStandardItem(self._format_decimal_for_display(section_data.get("comparative_total"))); comp_total_item.setFont(bold_font); comp_total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); total_row_items.append(comp_total_item)
            root_node.appendRow(total_row_items); root_node.appendRow([QStandardItem(""), QStandardItem("")] + ([QStandardItem("")] if has_comparative else [])) 
        if 'net_profit' in report_data:
            np_desc = QStandardItem("Net Profit / (Loss)"); np_desc.setFont(bold_font); np_amount = QStandardItem(self._format_decimal_for_display(report_data.get('net_profit'))); np_amount.setFont(bold_font); np_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); np_row = [np_desc, np_amount]; 
            if has_comparative: comp_np_amount = QStandardItem(self._format_decimal_for_display(report_data.get('comparative_net_profit'))); comp_np_amount.setFont(bold_font); comp_np_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); np_row.append(comp_np_amount)
            root_node.appendRow(np_row)

    def _populate_tax_computation_model(self, model: QStandardItemModel, report_data: Dict[str, Any]):
        model.clear(); headers = ["Description", "Amount"]; model.setHorizontalHeaderLabels(headers); root_node = model.invisibleRootItem(); bold_font = QFont(); bold_font.setBold(True)
        def add_row(parent: QStandardItem, desc: str, amt: Optional[Decimal] = None, is_bold: bool = False, is_underline: bool = False):
            desc_item = QStandardItem(desc); amt_item = QStandardItem(self._format_decimal_for_display(amt) if amt is not None else ""); amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if is_bold: desc_item.setFont(bold_font); amt_item.setFont(bold_font)
            if is_underline: desc_item.setData(QColor('black'), Qt.ItemDataRole.ForegroundRole); amt_item.setData(QColor('black'), Qt.ItemDataRole.ForegroundRole) # This doesn't create underline, just for concept
            parent.appendRow([desc_item, amt_item])
        
        add_row(root_node, "Net Profit Before Tax", report_data.get('net_profit_before_tax'), is_bold=True)
        add_row(root_node, "") # Spacer
        
        add_row(root_node, "Add: Non-Deductible Expenses", is_bold=True)
        for adj in report_data.get('add_back_adjustments', []): add_row(root_node, f"  {adj['name']}", adj['amount'])
        add_row(root_node, "Total Additions", report_data.get('total_add_back'), is_underline=True)
        add_row(root_node, "") # Spacer
        
        add_row(root_node, "Less: Non-Taxable Income", is_bold=True)
        for adj in report_data.get('less_adjustments', []): add_row(root_node, f"  {adj['name']}", adj['amount'])
        add_row(root_node, "Total Subtractions", report_data.get('total_less'), is_underline=True)
        add_row(root_node, "") # Spacer

        add_row(root_node, "Chargeable Income", report_data.get('chargeable_income'), is_bold=True)
        add_row(root_node, f"Tax at {report_data.get('tax_rate', 0):.2f}%", is_bold=False) # Description only
        add_row(root_node, "Estimated Tax Payable", report_data.get('estimated_tax'), is_bold=True)


    def _display_financial_report(self, report_data: Dict[str, Any]):
        report_title = report_data.get('title', '')
        if report_title == "Balance Sheet":
            self.fs_display_stack.setCurrentWidget(self.bs_tree_view); self._populate_balance_sheet_model(self.bs_model, report_data)
            self.bs_tree_view.expandAll(); [self.bs_tree_view.resizeColumnToContents(i) for i in range(self.bs_model.columnCount())]
        elif report_title == "Profit & Loss Statement":
            self.fs_display_stack.setCurrentWidget(self.pl_tree_view); self._populate_profit_loss_model(self.pl_model, report_data)
            self.pl_tree_view.expandAll(); [self.pl_tree_view.resizeColumnToContents(i) for i in range(self.pl_model.columnCount())]
        elif report_title == "Trial Balance":
            self.fs_display_stack.setCurrentWidget(self.tb_table_view); self.tb_model.update_data(report_data)
            [self.tb_table_view.resizeColumnToContents(i) for i in range(self.tb_model.columnCount())]
        elif report_title == "General Ledger": 
            self.fs_display_stack.setCurrentWidget(self.gl_widget_container); self.gl_model.update_data(report_data)
            gl_summary_data = self.gl_model.get_report_summary(); self.gl_summary_label_account.setText(f"Account: {gl_summary_data['account_name']}"); self.gl_summary_label_period.setText(gl_summary_data['period_description'])
            self.gl_summary_label_ob.setText(f"Opening Balance: {self._format_decimal_for_display(gl_summary_data['opening_balance'], show_blank_for_zero=False)}"); self.gl_summary_label_cb.setText(f"Closing Balance: {self._format_decimal_for_display(gl_summary_data['closing_balance'], show_blank_for_zero=False)}")
            [self.gl_table_view.resizeColumnToContents(i) for i in range(self.gl_model.columnCount())]
        elif report_title == "Income Tax Computation":
            self.fs_display_stack.setCurrentWidget(self.tax_comp_tree_view); self._populate_tax_computation_model(self.tax_comp_model, report_data)
            self.tax_comp_tree_view.expandAll(); [self.tax_comp_tree_view.resizeColumnToContents(i) for i in range(self.tax_comp_model.columnCount())]
        else: self._clear_current_financial_report_display(); self.app_core.logger.warning(f"Unhandled report title '{report_title}' for specific display."); QMessageBox.warning(self, "Display Error", f"Display format for '{report_title}' is not fully implemented in this view.")

    @Slot(str)
    def _on_export_report_clicked(self, format_type: str):
        if not self._current_financial_report_data: QMessageBox.warning(self, "No Report", "Please generate a report first before exporting."); return
        report_title_str = self._current_financial_report_data.get('title', 'FinancialReport')
        if not isinstance(report_title_str, str): report_title_str = "FinancialReport"
        default_filename = f"{report_title_str.replace(' ', '_').replace('&', 'And').replace('/', '-').replace(':', '')}_{python_date.today().strftime('%Y%m%d')}.{format_type}"
        documents_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation); 
        if not documents_path: documents_path = os.path.expanduser("~") 
        file_path, _ = QFileDialog.getSaveFileName(self, f"Save {format_type.upper()} Report", os.path.join(documents_path, default_filename), f"{format_type.upper()} Files (*.{format_type});;All Files (*)")
        if file_path: 
            self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False)
            future = schedule_task_from_qt(self.app_core.report_engine.export_report(self._current_financial_report_data, format_type)); 
            if future: future.add_done_callback( lambda res, fp=file_path, ft=format_type: QMetaObject.invokeMethod( self, "_safe_handle_export_result_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, future), Q_ARG(str, fp), Q_ARG(str, ft)))
            else: self.app_core.logger.error("Failed to schedule report export task."); self._handle_export_result(None, file_path, format_type) 
    @Slot(object, str, str)
    def _safe_handle_export_result_slot(self, future_arg, file_path_arg: str, format_type_arg: str): self._handle_export_result(future_arg, file_path_arg, format_type_arg)
    def _handle_export_result(self, future, file_path: str, format_type: str):
        self.export_pdf_button.setEnabled(True); self.export_excel_button.setEnabled(True)
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule report export."); return
        try:
            report_bytes: Optional[bytes] = future.result()
            if report_bytes:
                with open(file_path, "wb") as f: f.write(report_bytes)
                QMessageBox.information(self, "Export Successful", f"Report exported to:\n{file_path}")
            else: QMessageBox.warning(self, "Export Failed", f"Failed to generate report bytes for {format_type.upper()}.")
        except Exception as e: self.app_core.logger.error(f"Exception handling report export result: {e}", exc_info=True); QMessageBox.critical(self, "Export Error", f"An error occurred during export: {str(e)}")

```

# app/utils/__init__.py
```py
# File: app/utils/__init__.py
from .converters import to_decimal
from .formatting import format_currency, format_date, format_datetime
from .json_helpers import json_converter, json_date_hook
from .pydantic_models import (
    AppBaseModel, UserAuditData, 
    AccountBaseData, AccountCreateData, AccountUpdateData,
    JournalEntryLineData, JournalEntryData,
    GSTReturnData, TaxCalculationResultData, GSTTransactionLineDetail,
    TransactionLineTaxData, TransactionTaxData,
    AccountValidationResult, AccountValidator, CompanySettingData,
    FiscalYearCreateData, FiscalYearData, FiscalPeriodData,
    CustomerBaseData, CustomerCreateData, CustomerUpdateData, CustomerSummaryData, CustomerData,
    VendorBaseData, VendorCreateData, VendorUpdateData, VendorSummaryData, VendorData,
    ProductBaseData, ProductCreateData, ProductUpdateData, ProductSummaryData, ProductData,
    SalesInvoiceLineBaseData, SalesInvoiceBaseData, SalesInvoiceCreateData, SalesInvoiceUpdateData, SalesInvoiceData, SalesInvoiceSummaryData,
    RoleData, UserSummaryData, UserRoleAssignmentData, UserBaseData, UserCreateInternalData, UserCreateData, UserUpdateData, UserPasswordChangeData,
    RoleCreateData, RoleUpdateData, PermissionData,
    PurchaseInvoiceLineBaseData, PurchaseInvoiceBaseData, PurchaseInvoiceCreateData, PurchaseInvoiceUpdateData, PurchaseInvoiceData, PurchaseInvoiceSummaryData,
    BankAccountBaseData, BankAccountCreateData, BankAccountUpdateData, BankAccountSummaryData,
    BankTransactionBaseData, BankTransactionCreateData, BankTransactionSummaryData,
    PaymentAllocationBaseData, PaymentBaseData, PaymentCreateData, PaymentSummaryData,
    AuditLogEntryData, DataChangeHistoryEntryData,
    BankReconciliationBaseData, BankReconciliationCreateData, BankReconciliationData,
    BankReconciliationSummaryData,
    DashboardKPIData,
    CSVImportErrorData
)
from .result import Result
from .sequence_generator import SequenceGenerator
from .validation import is_valid_uen

__all__ = [
    "to_decimal", "format_currency", "format_date", "format_datetime",
    "json_converter", "json_date_hook",
    "AppBaseModel", "UserAuditData", 
    "AccountBaseData", "AccountCreateData", "AccountUpdateData",
    "JournalEntryLineData", "JournalEntryData",
    "GSTReturnData", "TaxCalculationResultData", "GSTTransactionLineDetail",
    "TransactionLineTaxData", "TransactionTaxData",
    "AccountValidationResult", "AccountValidator", "CompanySettingData",
    "FiscalYearCreateData", "FiscalYearData", "FiscalPeriodData",
    "CustomerBaseData", "CustomerCreateData", "CustomerUpdateData", "CustomerSummaryData", "CustomerData",
    "VendorBaseData", "VendorCreateData", "VendorUpdateData", "VendorSummaryData", "VendorData",
    "ProductBaseData", "ProductCreateData", "ProductUpdateData", "ProductSummaryData", "ProductData",
    "SalesInvoiceLineBaseData", "SalesInvoiceBaseData", "SalesInvoiceCreateData", "SalesInvoiceUpdateData", "SalesInvoiceData", "SalesInvoiceSummaryData",
    "RoleData", "UserSummaryData", "UserRoleAssignmentData", "UserBaseData", "UserCreateInternalData", "UserCreateData", "UserUpdateData", "UserPasswordChangeData",
    "RoleCreateData", "RoleUpdateData", "PermissionData",
    "PurchaseInvoiceLineBaseData", "PurchaseInvoiceBaseData", "PurchaseInvoiceCreateData", "PurchaseInvoiceUpdateData", "PurchaseInvoiceData", "PurchaseInvoiceSummaryData",
    "BankAccountBaseData", "BankAccountCreateData", "BankAccountUpdateData", "BankAccountSummaryData",
    "BankTransactionBaseData", "BankTransactionCreateData", "BankTransactionSummaryData",
    "PaymentAllocationBaseData", "PaymentBaseData", "PaymentCreateData", "PaymentSummaryData",
    "AuditLogEntryData", "DataChangeHistoryEntryData",
    "BankReconciliationBaseData", "BankReconciliationCreateData", "BankReconciliationData",
    "BankReconciliationSummaryData",
    "DashboardKPIData",
    "CSVImportErrorData",
    "Result", "SequenceGenerator", "is_valid_uen"
]

```

# app/utils/pydantic_models.py
```py
# File: app/utils/pydantic_models.py
from pydantic import BaseModel, Field, validator, root_validator, EmailStr # type: ignore
from typing import List, Optional, Union, Any, Dict 
from datetime import date, datetime
from decimal import Decimal

from app.common.enums import ( 
    ProductTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum,
    PaymentTypeEnum, PaymentMethodEnum, PaymentEntityTypeEnum, PaymentStatusEnum, 
    PaymentAllocationDocTypeEnum, DataChangeTypeEnum
)

class AppBaseModel(BaseModel):
    class Config:
        from_attributes = True 
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None and v.is_finite() else None, 
            EmailStr: lambda v: str(v) if v is not None else None,
        }
        validate_assignment = True 

class UserAuditData(BaseModel):
    user_id: int

# --- Account Related DTOs ---
class AccountBaseData(AppBaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    account_type: str 
    sub_type: Optional[str] = Field(None, max_length=30)
    tax_treatment: Optional[str] = Field(None, max_length=20)
    gst_applicable: bool = False
    description: Optional[str] = None
    parent_id: Optional[int] = None
    report_group: Optional[str] = Field(None, max_length=50)
    is_control_account: bool = False
    is_bank_account: bool = False
    opening_balance: Decimal = Field(Decimal(0))
    opening_balance_date: Optional[date] = None
    is_active: bool = True
    @validator('opening_balance', pre=True, always=True)
    def opening_balance_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)

class AccountCreateData(AccountBaseData, UserAuditData): pass
class AccountUpdateData(AccountBaseData, UserAuditData): id: int

# --- Journal Entry Related DTOs ---
class JournalEntryLineData(AppBaseModel):
    account_id: int
    description: Optional[str] = Field(None, max_length=200)
    debit_amount: Decimal = Field(Decimal(0))
    credit_amount: Decimal = Field(Decimal(0))
    currency_code: str = Field("SGD", max_length=3) 
    exchange_rate: Decimal = Field(Decimal(1))
    tax_code: Optional[str] = Field(None, max_length=20) 
    tax_amount: Decimal = Field(Decimal(0))
    dimension1_id: Optional[int] = None
    dimension2_id: Optional[int] = None 
    @validator('debit_amount', 'credit_amount', 'exchange_rate', 'tax_amount', pre=True, always=True)
    def je_line_amounts_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0) 
    @root_validator(skip_on_failure=True)
    def check_je_line_debit_credit_exclusive(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        debit = values.get('debit_amount', Decimal(0)); credit = values.get('credit_amount', Decimal(0))
        if debit > Decimal(0) and credit > Decimal(0): raise ValueError("Debit and Credit amounts cannot both be positive for a single line.")
        return values

class JournalEntryData(AppBaseModel, UserAuditData):
    journal_type: str
    entry_date: date
    description: Optional[str] = Field(None, max_length=500)
    reference: Optional[str] = Field(None, max_length=100)
    is_recurring: bool = False 
    recurring_pattern_id: Optional[int] = None
    source_type: Optional[str] = Field(None, max_length=50)
    source_id: Optional[int] = None
    lines: List[JournalEntryLineData]
    @validator('lines')
    def check_je_lines_not_empty(cls, v: List[JournalEntryLineData]) -> List[JournalEntryLineData]: 
        if not v: raise ValueError("Journal entry must have at least one line.")
        return v
    @root_validator(skip_on_failure=True)
    def check_je_balanced_entry(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        lines = values.get('lines', []); total_debits = sum(l.debit_amount for l in lines); total_credits = sum(l.credit_amount for l in lines)
        if abs(total_debits - total_credits) > Decimal("0.01"): raise ValueError(f"Journal entry must be balanced (Debits: {total_debits}, Credits: {total_credits}).")
        return values

# --- GST Related DTOs ---
class GSTTransactionLineDetail(AppBaseModel):
    transaction_date: date
    document_no: str 
    entity_name: Optional[str] = None 
    description: str
    account_code: str
    account_name: str
    net_amount: Decimal
    gst_amount: Decimal
    tax_code_applied: Optional[str] = None

class GSTReturnData(AppBaseModel, UserAuditData):
    id: Optional[int] = None
    return_period: str = Field(..., max_length=20)
    start_date: date; end_date: date
    filing_due_date: Optional[date] = None 
    standard_rated_supplies: Decimal = Field(Decimal(0))         
    zero_rated_supplies: Decimal = Field(Decimal(0))             
    exempt_supplies: Decimal = Field(Decimal(0))                 
    total_supplies: Decimal = Field(Decimal(0))                  
    taxable_purchases: Decimal = Field(Decimal(0))               
    output_tax: Decimal = Field(Decimal(0))                      
    input_tax: Decimal = Field(Decimal(0))                       
    tax_adjustments: Decimal = Field(Decimal(0))                 
    tax_payable: Decimal = Field(Decimal(0))                     
    status: str = Field("Draft", max_length=20)
    submission_date: Optional[date] = None
    submission_reference: Optional[str] = Field(None, max_length=50)
    journal_entry_id: Optional[int] = None
    notes: Optional[str] = None
    detailed_breakdown: Optional[Dict[str, List[GSTTransactionLineDetail]]] = Field(None, exclude=True) 

    @validator('standard_rated_supplies', 'zero_rated_supplies', 'exempt_supplies', 
               'total_supplies', 'taxable_purchases', 'output_tax', 'input_tax', 
               'tax_adjustments', 'tax_payable', pre=True, always=True)
    def gst_amounts_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)

# --- Tax Calculation DTOs ---
class TaxCalculationResultData(AppBaseModel): tax_amount: Decimal; tax_account_id: Optional[int] = None; taxable_amount: Decimal
class TransactionLineTaxData(AppBaseModel): amount: Decimal; tax_code: Optional[str] = None; account_id: Optional[int] = None; index: int 
class TransactionTaxData(AppBaseModel): transaction_type: str; lines: List[TransactionLineTaxData]

# --- Validation Result DTO ---
class AccountValidationResult(AppBaseModel): is_valid: bool; errors: List[str] = Field(default_factory=list)
class AccountValidator: 
    def validate_common(self, account_data: AccountBaseData) -> List[str]:
        errors = []; 
        if not account_data.code: errors.append("Account code is required.")
        if not account_data.name: errors.append("Account name is required.")
        if not account_data.account_type: errors.append("Account type is required.")
        if account_data.is_bank_account and account_data.account_type != 'Asset': errors.append("Bank accounts must be of type 'Asset'.")
        if account_data.opening_balance_date and account_data.opening_balance == Decimal(0): errors.append("Opening balance date provided but opening balance is zero.")
        if account_data.opening_balance != Decimal(0) and not account_data.opening_balance_date: errors.append("Opening balance provided but opening balance date is missing.")
        return errors
    def validate_create(self, account_data: AccountCreateData) -> AccountValidationResult:
        errors = self.validate_common(account_data); return AccountValidationResult(is_valid=not errors, errors=errors)
    def validate_update(self, account_data: AccountUpdateData) -> AccountValidationResult:
        errors = self.validate_common(account_data)
        if not account_data.id: errors.append("Account ID is required for updates.")
        return AccountValidationResult(is_valid=not errors, errors=errors)

# --- Company Setting DTO ---
class CompanySettingData(AppBaseModel, UserAuditData): 
    id: Optional[int] = None; company_name: str = Field(..., max_length=100); legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20); gst_registration_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False; address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100); postal_code: Optional[str] = Field(None, max_length=20); city: str = Field("Singapore", max_length=50); country: str = Field("Singapore", max_length=50); contact_person: Optional[str] = Field(None, max_length=100); phone: Optional[str] = Field(None, max_length=20); email: Optional[EmailStr] = None; website: Optional[str] = Field(None, max_length=100); logo: Optional[bytes] = None; fiscal_year_start_month: int = Field(1, ge=1, le=12); fiscal_year_start_day: int = Field(1, ge=1, le=31); base_currency: str = Field("SGD", max_length=3); tax_id_label: str = Field("UEN", max_length=50); date_format: str = Field("dd/MM/yyyy", max_length=20)

# --- Fiscal Year Related DTOs ---
class FiscalYearCreateData(AppBaseModel, UserAuditData): 
    year_name: str = Field(..., max_length=20); start_date: date; end_date: date; auto_generate_periods: Optional[str] = None
    @root_validator(skip_on_failure=True)
    def check_fy_dates(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        start, end = values.get('start_date'), values.get('end_date');
        if start and end and start >= end: raise ValueError("End date must be after start date.")
        return values
class FiscalPeriodData(AppBaseModel): id: int; name: str; start_date: date; end_date: date; period_type: str; status: str; period_number: int; is_adjustment: bool
class FiscalYearData(AppBaseModel): id: int; year_name: str; start_date: date; end_date: date; is_closed: bool; closed_date: Optional[datetime] = None; periods: List[FiscalPeriodData] = Field(default_factory=list)

# --- Customer Related DTOs ---
class CustomerBaseData(AppBaseModel): 
    customer_code: str = Field(..., min_length=1, max_length=20); name: str = Field(..., min_length=1, max_length=100); legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False; gst_no: Optional[str] = Field(None, max_length=20); contact_person: Optional[str] = Field(None, max_length=100); email: Optional[EmailStr] = None; phone: Optional[str] = Field(None, max_length=20); address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100); postal_code: Optional[str] = Field(None, max_length=20); city: Optional[str] = Field(None, max_length=50); country: str = Field("Singapore", max_length=50); credit_terms: int = Field(30, ge=0); credit_limit: Optional[Decimal] = Field(None, ge=Decimal(0)); currency_code: str = Field("SGD", min_length=3, max_length=3); is_active: bool = True; customer_since: Optional[date] = None; notes: Optional[str] = None; receivables_account_id: Optional[int] = None
    @validator('credit_limit', pre=True, always=True)
    def customer_credit_limit_to_decimal(cls, v): return Decimal(str(v)) if v is not None else None 
    @root_validator(skip_on_failure=True)
    def check_gst_no_if_registered_customer(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('gst_registered') and not values.get('gst_no'): raise ValueError("GST No. is required if customer is GST registered.")
        return values
class CustomerCreateData(CustomerBaseData, UserAuditData): pass
class CustomerUpdateData(CustomerBaseData, UserAuditData): id: int
class CustomerData(CustomerBaseData): id: int; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class CustomerSummaryData(AppBaseModel): id: int; customer_code: str; name: str; email: Optional[EmailStr] = None; phone: Optional[str] = None; is_active: bool

# --- Vendor Related DTOs ---
class VendorBaseData(AppBaseModel): 
    vendor_code: str = Field(..., min_length=1, max_length=20); name: str = Field(..., min_length=1, max_length=100); legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False; gst_no: Optional[str] = Field(None, max_length=20); withholding_tax_applicable: bool = False; withholding_tax_rate: Optional[Decimal] = Field(None, ge=Decimal(0), le=Decimal(100)); contact_person: Optional[str] = Field(None, max_length=100); email: Optional[EmailStr] = None; phone: Optional[str] = Field(None, max_length=20); address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100); postal_code: Optional[str] = Field(None, max_length=20); city: Optional[str] = Field(None, max_length=50); country: str = Field("Singapore", max_length=50); payment_terms: int = Field(30, ge=0); currency_code: str = Field("SGD", min_length=3, max_length=3); is_active: bool = True; vendor_since: Optional[date] = None; notes: Optional[str] = None; bank_account_name: Optional[str] = Field(None, max_length=100); bank_account_number: Optional[str] = Field(None, max_length=50); bank_name: Optional[str] = Field(None, max_length=100); bank_branch: Optional[str] = Field(None, max_length=100); bank_swift_code: Optional[str] = Field(None, max_length=20); payables_account_id: Optional[int] = None
    @validator('withholding_tax_rate', pre=True, always=True)
    def vendor_wht_rate_to_decimal(cls, v): return Decimal(str(v)) if v is not None else None 
    @root_validator(skip_on_failure=True)
    def check_gst_no_if_registered_vendor(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('gst_registered') and not values.get('gst_no'): raise ValueError("GST No. is required if vendor is GST registered.")
        return values
    @root_validator(skip_on_failure=True)
    def check_wht_rate_if_applicable_vendor(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        if values.get('withholding_tax_applicable') and values.get('withholding_tax_rate') is None: raise ValueError("Withholding Tax Rate is required if Withholding Tax is applicable.")
        return values
class VendorCreateData(VendorBaseData, UserAuditData): pass
class VendorUpdateData(VendorBaseData, UserAuditData): id: int
class VendorData(VendorBaseData): id: int; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class VendorSummaryData(AppBaseModel): id: int; vendor_code: str; name: str; email: Optional[EmailStr] = None; phone: Optional[str] = None; is_active: bool

# --- Product/Service Related DTOs ---
class ProductBaseData(AppBaseModel): 
    product_code: str = Field(..., min_length=1, max_length=20); name: str = Field(..., min_length=1, max_length=100); description: Optional[str] = None; product_type: ProductTypeEnum; category: Optional[str] = Field(None, max_length=50); unit_of_measure: Optional[str] = Field(None, max_length=20); barcode: Optional[str] = Field(None, max_length=50); sales_price: Optional[Decimal] = Field(None, ge=Decimal(0)); purchase_price: Optional[Decimal] = Field(None, ge=Decimal(0)); sales_account_id: Optional[int] = None; purchase_account_id: Optional[int] = None; inventory_account_id: Optional[int] = None; tax_code: Optional[str] = Field(None, max_length=20); is_active: bool = True; min_stock_level: Optional[Decimal] = Field(None, ge=Decimal(0)); reorder_point: Optional[Decimal] = Field(None, ge=Decimal(0))     
    @validator('sales_price', 'purchase_price', 'min_stock_level', 'reorder_point', pre=True, always=True)
    def product_decimal_fields(cls, v): return Decimal(str(v)) if v is not None else None
    @root_validator(skip_on_failure=True)
    def check_inventory_fields_product(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        product_type = values.get('product_type')
        if product_type == ProductTypeEnum.INVENTORY:
            if values.get('inventory_account_id') is None: raise ValueError("Inventory Account ID is required for 'Inventory' type products.")
        else: 
            if values.get('inventory_account_id') is not None: raise ValueError("Inventory Account ID should only be set for 'Inventory' type products.")
            if values.get('min_stock_level') is not None or values.get('reorder_point') is not None: raise ValueError("Stock levels are only applicable for 'Inventory' type products.")
        return values
class ProductCreateData(ProductBaseData, UserAuditData): pass
class ProductUpdateData(ProductBaseData, UserAuditData): id: int
class ProductData(ProductBaseData): id: int; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class ProductSummaryData(AppBaseModel): id: int; product_code: str; name: str; product_type: ProductTypeEnum; sales_price: Optional[Decimal] = None; purchase_price: Optional[Decimal] = None; is_active: bool

# --- Sales Invoice Related DTOs ---
class SalesInvoiceLineBaseData(AppBaseModel):
    product_id: Optional[int] = None; description: str = Field(..., min_length=1, max_length=200); quantity: Decimal = Field(..., gt=Decimal(0)); unit_price: Decimal = Field(..., ge=Decimal(0)); discount_percent: Decimal = Field(Decimal(0), ge=Decimal(0), le=Decimal(100)); tax_code: Optional[str] = Field(None, max_length=20); dimension1_id: Optional[int] = None; dimension2_id: Optional[int] = None 
    @validator('quantity', 'unit_price', 'discount_percent', pre=True, always=True)
    def sales_inv_line_decimals(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)
class SalesInvoiceBaseData(AppBaseModel):
    customer_id: int; invoice_date: date; due_date: date; currency_code: str = Field("SGD", min_length=3, max_length=3); exchange_rate: Decimal = Field(Decimal(1), ge=Decimal(0)); notes: Optional[str] = None; terms_and_conditions: Optional[str] = None
    @validator('exchange_rate', pre=True, always=True)
    def sales_inv_hdr_decimals(cls, v): return Decimal(str(v)) if v is not None else Decimal(1)
    @root_validator(skip_on_failure=True)
    def check_due_date(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        invoice_date, due_date = values.get('invoice_date'), values.get('due_date')
        if invoice_date and due_date and due_date < invoice_date: raise ValueError("Due date cannot be before invoice date.")
        return values
class SalesInvoiceCreateData(SalesInvoiceBaseData, UserAuditData): lines: List[SalesInvoiceLineBaseData] = Field(..., min_length=1)
class SalesInvoiceUpdateData(SalesInvoiceBaseData, UserAuditData): id: int; lines: List[SalesInvoiceLineBaseData] = Field(..., min_length=1)
class SalesInvoiceData(SalesInvoiceBaseData): id: int; invoice_no: str; subtotal: Decimal; tax_amount: Decimal; total_amount: Decimal; amount_paid: Decimal; status: InvoiceStatusEnum; journal_entry_id: Optional[int] = None; lines: List[SalesInvoiceLineBaseData]; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class SalesInvoiceSummaryData(AppBaseModel): id: int; invoice_no: str; invoice_date: date; due_date: date; customer_name: str; total_amount: Decimal; amount_paid: Decimal; status: InvoiceStatusEnum; currency_code: str

# --- User & Role Management DTOs ---
class RoleData(AppBaseModel): id: int; name: str; description: Optional[str] = None; permission_ids: List[int] = Field(default_factory=list) 
class UserSummaryData(AppBaseModel): id: int; username: str; full_name: Optional[str] = None; email: Optional[EmailStr] = None; is_active: bool; last_login: Optional[datetime] = None; roles: List[str] = Field(default_factory=list) 
class UserRoleAssignmentData(AppBaseModel): role_id: int
class UserBaseData(AppBaseModel): username: str = Field(..., min_length=3, max_length=50); full_name: Optional[str] = Field(None, max_length=100); email: Optional[EmailStr] = None; is_active: bool = True
class UserCreateInternalData(UserBaseData): password_hash: str; assigned_roles: List[UserRoleAssignmentData] = Field(default_factory=list)
class UserCreateData(UserBaseData, UserAuditData): 
    password: str = Field(..., min_length=8); confirm_password: str; assigned_role_ids: List[int] = Field(default_factory=list)
    @root_validator(skip_on_failure=True)
    def passwords_match(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        pw1, pw2 = values.get('password'), values.get('confirm_password')
        if pw1 is not None and pw2 is not None and pw1 != pw2: raise ValueError('Passwords do not match')
        return values
class UserUpdateData(UserBaseData, UserAuditData): id: int; assigned_role_ids: List[int] = Field(default_factory=list)
class UserPasswordChangeData(AppBaseModel, UserAuditData): 
    user_id_to_change: int; new_password: str = Field(..., min_length=8); confirm_new_password: str
    @root_validator(skip_on_failure=True)
    def new_passwords_match(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        pw1, pw2 = values.get('new_password'), values.get('confirm_new_password')
        if pw1 is not None and pw2 is not None and pw1 != pw2: raise ValueError('New passwords do not match')
        return values
class RoleCreateData(AppBaseModel): name: str = Field(..., min_length=3, max_length=50); description: Optional[str] = Field(None, max_length=200); permission_ids: List[int] = Field(default_factory=list)
class RoleUpdateData(RoleCreateData): id: int
class PermissionData(AppBaseModel): id: int; code: str; description: Optional[str] = None; module: str

# --- Purchase Invoice Related DTOs ---
class PurchaseInvoiceLineBaseData(AppBaseModel):
    product_id: Optional[int] = None; description: str = Field(..., min_length=1, max_length=200); quantity: Decimal = Field(..., gt=Decimal(0)); unit_price: Decimal = Field(..., ge=Decimal(0)); discount_percent: Decimal = Field(Decimal(0), ge=Decimal(0), le=Decimal(100)); tax_code: Optional[str] = Field(None, max_length=20); dimension1_id: Optional[int] = None; dimension2_id: Optional[int] = None
    @validator('quantity', 'unit_price', 'discount_percent', pre=True, always=True)
    def purch_inv_line_decimals(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)
class PurchaseInvoiceBaseData(AppBaseModel):
    vendor_id: int; vendor_invoice_no: Optional[str] = Field(None, max_length=50); invoice_date: date; due_date: date; currency_code: str = Field("SGD", min_length=3, max_length=3); exchange_rate: Decimal = Field(Decimal(1), ge=Decimal(0)); notes: Optional[str] = None
    @validator('exchange_rate', pre=True, always=True)
    def purch_inv_hdr_decimals(cls, v): return Decimal(str(v)) if v is not None else Decimal(1)
    @root_validator(skip_on_failure=True)
    def check_pi_due_date(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        invoice_date, due_date = values.get('invoice_date'), values.get('due_date')
        if invoice_date and due_date and due_date < invoice_date: raise ValueError("Due date cannot be before invoice date.")
        return values
class PurchaseInvoiceCreateData(PurchaseInvoiceBaseData, UserAuditData): lines: List[PurchaseInvoiceLineBaseData] = Field(..., min_length=1)
class PurchaseInvoiceUpdateData(PurchaseInvoiceBaseData, UserAuditData): id: int; lines: List[PurchaseInvoiceLineBaseData] = Field(..., min_length=1)
class PurchaseInvoiceData(PurchaseInvoiceBaseData): id: int; invoice_no: str; subtotal: Decimal; tax_amount: Decimal; total_amount: Decimal; amount_paid: Decimal; status: InvoiceStatusEnum; journal_entry_id: Optional[int] = None; lines: List[PurchaseInvoiceLineBaseData]; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class PurchaseInvoiceSummaryData(AppBaseModel): id: int; invoice_no: str; vendor_invoice_no: Optional[str] = None; invoice_date: date; vendor_name: str; total_amount: Decimal; status: InvoiceStatusEnum; currency_code: str 

# --- Bank Account DTOs ---
class BankAccountBaseData(AppBaseModel):
    account_name: str = Field(..., min_length=1, max_length=100); account_number: str = Field(..., min_length=1, max_length=50); bank_name: str = Field(..., min_length=1, max_length=100); bank_branch: Optional[str] = Field(None, max_length=100); bank_swift_code: Optional[str] = Field(None, max_length=20); currency_code: str = Field("SGD", min_length=3, max_length=3); opening_balance: Decimal = Field(Decimal(0)); opening_balance_date: Optional[date] = None; gl_account_id: int; is_active: bool = True; description: Optional[str] = None
    @validator('opening_balance', pre=True, always=True)
    def bank_opening_balance_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)
    @root_validator(skip_on_failure=True)
    def check_ob_date_if_ob_exists_bank(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        ob = values.get('opening_balance'); ob_date = values.get('opening_balance_date')
        if ob is not None and ob != Decimal(0) and ob_date is None: raise ValueError("Opening Balance Date is required if Opening Balance is not zero.")
        if ob_date is not None and (ob is None or ob == Decimal(0)): values['opening_balance_date'] = None 
        return values
class BankAccountCreateData(BankAccountBaseData, UserAuditData): pass
class BankAccountUpdateData(BankAccountBaseData, UserAuditData): id: int
class BankAccountSummaryData(AppBaseModel): id: int; account_name: str; bank_name: str; account_number: str; currency_code: str; current_balance: Decimal; gl_account_code: Optional[str] = None; gl_account_name: Optional[str] = None; is_active: bool

# --- Bank Transaction DTOs ---
class BankTransactionBaseData(AppBaseModel):
    bank_account_id: int; transaction_date: date; value_date: Optional[date] = None; transaction_type: BankTransactionTypeEnum; description: str = Field(..., min_length=1, max_length=200); reference: Optional[str] = Field(None, max_length=100); amount: Decimal 
    @validator('amount', pre=True, always=True)
    def bank_txn_amount_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)
    @root_validator(skip_on_failure=True)
    def check_amount_sign_vs_type_bank_txn(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        amount = values.get('amount'); txn_type = values.get('transaction_type')
        if amount is None or txn_type is None: return values 
        if txn_type in [BankTransactionTypeEnum.DEPOSIT, BankTransactionTypeEnum.INTEREST]:
            if amount < Decimal(0): raise ValueError(f"{txn_type.value} amount must be positive or zero.")
        elif txn_type in [BankTransactionTypeEnum.WITHDRAWAL, BankTransactionTypeEnum.FEE]:
            if amount > Decimal(0): raise ValueError(f"{txn_type.value} amount must be negative or zero.")
        return values
class BankTransactionCreateData(BankTransactionBaseData, UserAuditData): pass
class BankTransactionSummaryData(AppBaseModel): 
    id: int
    transaction_date: date
    value_date: Optional[date] = None
    transaction_type: BankTransactionTypeEnum
    description: str
    reference: Optional[str] = None
    amount: Decimal
    is_reconciled: bool = False
    updated_at: datetime

# --- Payment DTOs ---
class PaymentAllocationBaseData(AppBaseModel):
    document_id: int; document_type: PaymentAllocationDocTypeEnum; amount_allocated: Decimal = Field(..., gt=Decimal(0))
    @validator('amount_allocated', pre=True, always=True)
    def payment_alloc_amount_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)
class PaymentBaseData(AppBaseModel):
    payment_type: PaymentTypeEnum; payment_method: PaymentMethodEnum; payment_date: date; entity_type: PaymentEntityTypeEnum; entity_id: int; bank_account_id: Optional[int] = None; currency_code: str = Field(..., min_length=3, max_length=3); exchange_rate: Decimal = Field(Decimal(1), ge=Decimal(0)); amount: Decimal = Field(..., gt=Decimal(0)); reference: Optional[str] = Field(None, max_length=100); description: Optional[str] = None; cheque_no: Optional[str] = Field(None, max_length=50)
    @validator('exchange_rate', 'amount', pre=True, always=True)
    def payment_base_decimals(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)
    @root_validator(skip_on_failure=True)
    def check_bank_account_for_non_cash(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        payment_method = values.get('payment_method'); bank_account_id = values.get('bank_account_id')
        if payment_method != PaymentMethodEnum.CASH and bank_account_id is None: raise ValueError("Bank Account is required for non-cash payment methods.")
        if payment_method == PaymentMethodEnum.CASH and bank_account_id is not None: raise ValueError("Bank Account should not be specified for Cash payment method.")
        return values
class PaymentCreateData(PaymentBaseData, UserAuditData):
    allocations: List[PaymentAllocationBaseData] = Field(default_factory=list)
    @root_validator(skip_on_failure=True)
    def check_total_allocation_vs_payment_amount(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        payment_amount = values.get('amount', Decimal(0)); allocations = values.get('allocations', []); total_allocated = sum(alloc.amount_allocated for alloc in allocations)
        if total_allocated > payment_amount: raise ValueError(f"Total allocated amount ({total_allocated}) cannot exceed payment amount ({payment_amount}).")
        return values
class PaymentSummaryData(AppBaseModel): id: int; payment_no: str; payment_date: date; payment_type: PaymentTypeEnum; payment_method: PaymentMethodEnum; entity_type: PaymentEntityTypeEnum; entity_name: str; amount: Decimal; currency_code: str; status: PaymentStatusEnum

# --- Audit Log DTOs ---
class AuditLogEntryData(AppBaseModel): id: int; timestamp: datetime; username: Optional[str] = "System"; action: str; entity_type: str; entity_id: Optional[int] = None; entity_name: Optional[str] = None; changes_summary: Optional[str] = None; ip_address: Optional[str] = None
class DataChangeHistoryEntryData(AppBaseModel): id: int; changed_at: datetime; table_name: str; record_id: int; field_name: str; old_value: Optional[str] = None; new_value: Optional[str] = None; change_type: DataChangeTypeEnum; changed_by_username: Optional[str] = "System"

# --- Bank Reconciliation DTOs ---
class BankReconciliationBaseData(AppBaseModel):
    bank_account_id: int
    statement_date: date
    statement_ending_balance: Decimal
    calculated_book_balance: Decimal
    reconciled_difference: Decimal
    notes: Optional[str] = None

class BankReconciliationCreateData(BankReconciliationBaseData, UserAuditData):
    pass 

class BankReconciliationData(BankReconciliationBaseData): 
    id: int
    reconciliation_date: datetime 
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int
    
class BankReconciliationSummaryData(AppBaseModel): 
    id: int
    statement_date: date
    statement_ending_balance: Decimal
    reconciled_difference: Decimal
    reconciliation_date: datetime
    created_by_username: Optional[str] = None

# --- CSV Import DTOs ---
class CSVImportErrorData(AppBaseModel):
    row_number: int
    row_data: List[str]
    error_message: str

# --- Dashboard DTOs ---
class DashboardKPIData(AppBaseModel):
    kpi_period_description: str
    base_currency: str
    total_revenue_ytd: Decimal = Field(Decimal(0))
    total_expenses_ytd: Decimal = Field(Decimal(0))
    net_profit_ytd: Decimal = Field(Decimal(0))
    current_cash_balance: Decimal = Field(Decimal(0))
    total_outstanding_ar: Decimal = Field(Decimal(0))
    total_outstanding_ap: Decimal = Field(Decimal(0))
    total_ar_overdue: Decimal = Field(Decimal(0)) 
    total_ap_overdue: Decimal = Field(Decimal(0))
    ar_aging_current: Decimal = Field(Decimal(0)) 
    ar_aging_1_30: Decimal = Field(Decimal(0))
    ar_aging_31_60: Decimal = Field(Decimal(0))
    ar_aging_61_90: Decimal = Field(Decimal(0))
    ar_aging_91_plus: Decimal = Field(Decimal(0))
    ap_aging_current: Decimal = Field(Decimal(0)) 
    ap_aging_1_30: Decimal = Field(Decimal(0))
    ap_aging_31_60: Decimal = Field(Decimal(0))
    ap_aging_61_90: Decimal = Field(Decimal(0))
    ap_aging_91_plus: Decimal = Field(Decimal(0))
    total_current_assets: Decimal = Field(Decimal(0))
    total_current_liabilities: Decimal = Field(Decimal(0))
    total_inventory: Decimal = Field(Decimal(0))
    total_liabilities: Decimal = Field(Decimal(0))
    total_equity: Decimal = Field(Decimal(0))
    current_ratio: Optional[Decimal] = None
    quick_ratio: Optional[Decimal] = None
    debt_to_equity_ratio: Optional[Decimal] = None

```

# app/services/business_services.py
```py
# File: app/services/business_services.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict, Tuple
from sqlalchemy import select, func, and_, or_, literal_column, case, update as sqlalchemy_update, table, column
from sqlalchemy.types import DECIMAL 
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.orm import selectinload, joinedload 
from decimal import Decimal
import logging 
from datetime import date, datetime, timedelta 

from app.core.database_manager import DatabaseManager
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.product import Product
from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine 
from app.models.business.inventory_movement import InventoryMovement 
from app.models.business.bank_account import BankAccount 
from app.models.business.bank_transaction import BankTransaction
from app.models.business.payment import Payment, PaymentAllocation 
from app.models.business.bank_reconciliation import BankReconciliation
from app.models.accounting.account import Account 
from app.models.accounting.currency import Currency 
from app.models.accounting.tax_code import TaxCode 
from app.models.core.user import User
from app.services import (
    ICustomerRepository, IVendorRepository, IProductRepository, 
    ISalesInvoiceRepository, IPurchaseInvoiceRepository, IInventoryMovementRepository,
    IBankAccountRepository, IBankTransactionRepository, IPaymentRepository,
    IBankReconciliationRepository
)
from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData,
    BankAccountSummaryData, BankTransactionSummaryData,
    PaymentSummaryData, BankReconciliationSummaryData
)
from app.utils.result import Result 
from app.common.enums import ProductTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum, PaymentEntityTypeEnum, PaymentStatusEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

customer_balances_view_table = table(
    "customer_balances",
    column("outstanding_balance", DECIMAL(15, 2)), 
    column("overdue_amount", DECIMAL(15, 2)),
    schema="business"
)

vendor_balances_view_table = table(
    "vendor_balances",
    column("outstanding_balance", DECIMAL(15, 2)),
    column("overdue_amount", DECIMAL(15, 2)),
    schema="business"
)

class CustomerService(ICustomerRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, customer_id: int) -> Optional[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).options(selectinload(Customer.currency),selectinload(Customer.receivables_account),selectinload(Customer.created_by_user),selectinload(Customer.updated_by_user)).where(Customer.id == customer_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).order_by(Customer.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[CustomerSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Customer.is_active == True)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Customer.customer_code.ilike(search_pattern), Customer.name.ilike(search_pattern), Customer.email.ilike(search_pattern) if Customer.email else False )) 
            stmt = select(Customer.id, Customer.customer_code, Customer.name, Customer.email, Customer.phone, Customer.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Customer.name)
            if page_size > 0 : stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [CustomerSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).where(Customer.customer_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, customer: Customer) -> Customer:
        async with self.db_manager.session() as session:
            session.add(customer); await session.flush(); await session.refresh(customer); return customer
    async def add(self, entity: Customer) -> Customer: return await self.save(entity)
    async def update(self, entity: Customer) -> Customer: return await self.save(entity)
    async def delete(self, customer_id: int) -> bool:
        raise NotImplementedError("Hard delete of customers is not supported. Use deactivation.")
    async def get_total_outstanding_balance(self) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = select(func.sum(customer_balances_view_table.c.outstanding_balance))
            result = await session.execute(stmt)
            total_outstanding = result.scalar_one_or_none()
            return total_outstanding if total_outstanding is not None else Decimal(0)
    async def get_total_overdue_balance(self) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = select(func.sum(customer_balances_view_table.c.overdue_amount))
            result = await session.execute(stmt)
            total_overdue = result.scalar_one_or_none()
            return total_overdue if total_overdue is not None else Decimal(0)
    
    async def get_ar_aging_summary(self, as_of_date: date) -> Dict[str, Decimal]:
        aging_summary = {
            "Current": Decimal(0),    
            "1-30 Days": Decimal(0),  
            "31-60 Days": Decimal(0), 
            "61-90 Days": Decimal(0), 
            "91+ Days": Decimal(0)    
        }
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).where(
                SalesInvoice.status.in_([InvoiceStatusEnum.APPROVED.value, InvoiceStatusEnum.PARTIALLY_PAID.value, InvoiceStatusEnum.OVERDUE.value]),
                SalesInvoice.total_amount > SalesInvoice.amount_paid
            )
            result = await session.execute(stmt)
            outstanding_invoices: List[SalesInvoice] = list(result.scalars().all())

            for inv in outstanding_invoices:
                outstanding_balance = inv.total_amount - inv.amount_paid
                if outstanding_balance <= Decimal("0.005"): 
                    continue
                
                days_overdue = (as_of_date - inv.due_date).days

                if days_overdue <= 0: # Not yet due or due today
                    aging_summary["Current"] += outstanding_balance
                elif 1 <= days_overdue <= 30:
                    aging_summary["1-30 Days"] += outstanding_balance
                elif 31 <= days_overdue <= 60:
                    aging_summary["31-60 Days"] += outstanding_balance
                elif 61 <= days_overdue <= 90:
                    aging_summary["61-90 Days"] += outstanding_balance
                else: # days_overdue >= 91
                    aging_summary["91+ Days"] += outstanding_balance
        
        return {k: v.quantize(Decimal("0.01")) for k, v in aging_summary.items()}


class VendorService(IVendorRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, vendor_id: int) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).options(selectinload(Vendor.currency), selectinload(Vendor.payables_account),selectinload(Vendor.created_by_user), selectinload(Vendor.updated_by_user)).where(Vendor.id == vendor_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).order_by(Vendor.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[VendorSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Vendor.is_active == True)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Vendor.vendor_code.ilike(search_pattern), Vendor.name.ilike(search_pattern), Vendor.email.ilike(search_pattern) if Vendor.email else False))
            stmt = select(Vendor.id, Vendor.vendor_code, Vendor.name, Vendor.email, Vendor.phone, Vendor.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Vendor.name)
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [VendorSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).where(Vendor.vendor_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, vendor: Vendor) -> Vendor:
        async with self.db_manager.session() as session:
            session.add(vendor); await session.flush(); await session.refresh(vendor); return vendor
    async def add(self, entity: Vendor) -> Vendor: return await self.save(entity)
    async def update(self, entity: Vendor) -> Vendor: return await self.save(entity)
    async def delete(self, vendor_id: int) -> bool:
        raise NotImplementedError("Hard delete of vendors is not supported. Use deactivation.")
    async def get_total_outstanding_balance(self) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = select(func.sum(vendor_balances_view_table.c.outstanding_balance))
            result = await session.execute(stmt)
            total_outstanding = result.scalar_one_or_none()
            return total_outstanding if total_outstanding is not None else Decimal(0)
    async def get_total_overdue_balance(self) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = select(func.sum(vendor_balances_view_table.c.overdue_amount))
            result = await session.execute(stmt)
            total_overdue = result.scalar_one_or_none()
            return total_overdue if total_overdue is not None else Decimal(0)

    async def get_ap_aging_summary(self, as_of_date: date) -> Dict[str, Decimal]:
        aging_summary = {
            "Current": Decimal(0),    
            "1-30 Days": Decimal(0),  
            "31-60 Days": Decimal(0),
            "61-90 Days": Decimal(0),
            "91+ Days": Decimal(0)
        }
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).where(
                PurchaseInvoice.status.in_([InvoiceStatusEnum.APPROVED.value, InvoiceStatusEnum.PARTIALLY_PAID.value, InvoiceStatusEnum.OVERDUE.value]),
                PurchaseInvoice.total_amount > PurchaseInvoice.amount_paid
            )
            result = await session.execute(stmt)
            outstanding_invoices: List[PurchaseInvoice] = list(result.scalars().all())

            for inv in outstanding_invoices:
                outstanding_balance = inv.total_amount - inv.amount_paid
                if outstanding_balance <= Decimal("0.005"):
                    continue
                
                days_overdue = (as_of_date - inv.due_date).days

                if days_overdue <= 0:
                    aging_summary["Current"] += outstanding_balance
                elif 1 <= days_overdue <= 30:
                    aging_summary["1-30 Days"] += outstanding_balance
                elif 31 <= days_overdue <= 60:
                    aging_summary["31-60 Days"] += outstanding_balance
                elif 61 <= days_overdue <= 90:
                    aging_summary["61-90 Days"] += outstanding_balance
                else: 
                    aging_summary["91+ Days"] += outstanding_balance
        
        return {k: v.quantize(Decimal("0.01")) for k, v in aging_summary.items()}

class ProductService(IProductRepository): 
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, product_id: int) -> Optional[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).options(selectinload(Product.sales_account),selectinload(Product.purchase_account),selectinload(Product.inventory_account),selectinload(Product.tax_code_obj),selectinload(Product.created_by_user),selectinload(Product.updated_by_user)).where(Product.id == product_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).order_by(Product.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,product_type_filter: Optional[ProductTypeEnum] = None,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[ProductSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Product.is_active == True)
            if product_type_filter: conditions.append(Product.product_type == product_type_filter.value)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Product.product_code.ilike(search_pattern), Product.name.ilike(search_pattern), Product.description.ilike(search_pattern) if Product.description else False ))
            stmt = select(Product.id, Product.product_code, Product.name, Product.product_type, Product.sales_price, Product.purchase_price, Product.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Product.product_type, Product.name)
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [ProductSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).where(Product.product_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, product: Product) -> Product:
        async with self.db_manager.session() as session:
            session.add(product); await session.flush(); await session.refresh(product); return product
    async def add(self, entity: Product) -> Product: return await self.save(entity)
    async def update(self, entity: Product) -> Product: return await self.save(entity)
    async def delete(self, product_id: int) -> bool:
        raise NotImplementedError("Hard delete of products/services is not supported. Use deactivation.")

class SalesInvoiceService(ISalesInvoiceRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, invoice_id: int) -> Optional[SalesInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).options(selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product),selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.tax_code_obj),selectinload(SalesInvoice.customer), selectinload(SalesInvoice.currency),selectinload(SalesInvoice.journal_entry), selectinload(SalesInvoice.created_by_user), selectinload(SalesInvoice.updated_by_user)).where(SalesInvoice.id == invoice_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[SalesInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.invoice_no.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, customer_id: Optional[int] = None, status: Optional[InvoiceStatusEnum] = None, start_date: Optional[date] = None, end_date: Optional[date] = None,page: int = 1, page_size: int = 50) -> List[SalesInvoiceSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if customer_id is not None: conditions.append(SalesInvoice.customer_id == customer_id)
            if status: conditions.append(SalesInvoice.status == status.value)
            if start_date: conditions.append(SalesInvoice.invoice_date >= start_date)
            if end_date: conditions.append(SalesInvoice.invoice_date <= end_date)
            stmt = select( SalesInvoice.id, SalesInvoice.invoice_no, SalesInvoice.invoice_date, SalesInvoice.due_date, Customer.name.label("customer_name"), SalesInvoice.total_amount, SalesInvoice.amount_paid, SalesInvoice.status, SalesInvoice.currency_code).join(Customer, SalesInvoice.customer_id == Customer.id) 
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.invoice_no.desc()) # type: ignore
            if page_size > 0 : stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [SalesInvoiceSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]: 
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).options(selectinload(SalesInvoice.lines)).where(SalesInvoice.invoice_no == invoice_no)
            result = await session.execute(stmt); return result.scalars().first()
    async def save(self, invoice: SalesInvoice) -> SalesInvoice:
        async with self.db_manager.session() as session:
            session.add(invoice); await session.flush(); await session.refresh(invoice)
            if invoice.id and invoice.lines: await session.refresh(invoice, attribute_names=['lines'])
            return invoice
    async def add(self, entity: SalesInvoice) -> SalesInvoice: return await self.save(entity)
    async def update(self, entity: SalesInvoice) -> SalesInvoice: return await self.save(entity)
    async def delete(self, invoice_id: int) -> bool:
        raise NotImplementedError("Hard delete of sales invoices is not supported. Use voiding/cancellation.")
    async def get_outstanding_invoices_for_customer(self, customer_id: Optional[int], as_of_date: date) -> List[SalesInvoice]: # New for aging
        async with self.db_manager.session() as session:
            conditions = [
                SalesInvoice.status.in_([
                    InvoiceStatusEnum.APPROVED.value, 
                    InvoiceStatusEnum.PARTIALLY_PAID.value, 
                    InvoiceStatusEnum.OVERDUE.value
                ]),
                SalesInvoice.total_amount > SalesInvoice.amount_paid,
                SalesInvoice.invoice_date <= as_of_date # Include invoices issued on or before as_of_date
            ]
            if customer_id is not None:
                conditions.append(SalesInvoice.customer_id == customer_id)
            
            stmt = select(SalesInvoice).where(and_(*conditions))
            result = await session.execute(stmt)
            return list(result.scalars().all())

class PurchaseInvoiceService(IPurchaseInvoiceRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, invoice_id: int) -> Optional[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(selectinload(PurchaseInvoice.lines).selectinload(PurchaseInvoiceLine.product),selectinload(PurchaseInvoice.lines).selectinload(PurchaseInvoiceLine.tax_code_obj),selectinload(PurchaseInvoice.vendor), selectinload(PurchaseInvoice.currency),selectinload(PurchaseInvoice.journal_entry),selectinload(PurchaseInvoice.created_by_user), selectinload(PurchaseInvoice.updated_by_user)).where(PurchaseInvoice.id == invoice_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).order_by(PurchaseInvoice.invoice_date.desc(), PurchaseInvoice.invoice_no.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, vendor_id: Optional[int] = None, status: Optional[InvoiceStatusEnum] = None, start_date: Optional[date] = None, end_date: Optional[date] = None,page: int = 1, page_size: int = 50) -> List[PurchaseInvoiceSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if vendor_id is not None: conditions.append(PurchaseInvoice.vendor_id == vendor_id)
            if status: conditions.append(PurchaseInvoice.status == status.value)
            if start_date: conditions.append(PurchaseInvoice.invoice_date >= start_date)
            if end_date: conditions.append(PurchaseInvoice.invoice_date <= end_date)
            stmt = select( PurchaseInvoice.id, PurchaseInvoice.invoice_no, PurchaseInvoice.vendor_invoice_no, PurchaseInvoice.invoice_date, Vendor.name.label("vendor_name"), PurchaseInvoice.total_amount, PurchaseInvoice.status, PurchaseInvoice.currency_code).join(Vendor, PurchaseInvoice.vendor_id == Vendor.id)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(PurchaseInvoice.invoice_date.desc(), PurchaseInvoice.invoice_no.desc()) # type: ignore
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [PurchaseInvoiceSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_internal_ref_no(self, internal_ref_no: str) -> Optional[PurchaseInvoice]: 
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(selectinload(PurchaseInvoice.lines)).where(PurchaseInvoice.invoice_no == internal_ref_no) 
            result = await session.execute(stmt); return result.scalars().first()
    async def get_by_vendor_and_vendor_invoice_no(self, vendor_id: int, vendor_invoice_no: str) -> Optional[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(selectinload(PurchaseInvoice.lines)).where(PurchaseInvoice.vendor_id == vendor_id, PurchaseInvoice.vendor_invoice_no == vendor_invoice_no)
            result = await session.execute(stmt); return result.scalars().first() 
    async def save(self, invoice: PurchaseInvoice) -> PurchaseInvoice:
        async with self.db_manager.session() as session:
            session.add(invoice); await session.flush(); await session.refresh(invoice)
            if invoice.id and invoice.lines: await session.refresh(invoice, attribute_names=['lines'])
            return invoice
    async def add(self, entity: PurchaseInvoice) -> PurchaseInvoice: return await self.save(entity)
    async def update(self, entity: PurchaseInvoice) -> PurchaseInvoice: return await self.save(entity)
    async def delete(self, invoice_id: int) -> bool:
        async with self.db_manager.session() as session:
            pi = await session.get(PurchaseInvoice, invoice_id)
            if pi and pi.status == InvoiceStatusEnum.DRAFT.value: await session.delete(pi); return True
            elif pi: self.logger.warning(f"Attempt to delete non-draft PI ID {invoice_id} with status {pi.status}. Denied."); raise ValueError(f"Cannot delete PI {pi.invoice_no} as its status is '{pi.status}'. Only Draft invoices can be deleted.")
        return False
    async def get_outstanding_invoices_for_vendor(self, vendor_id: Optional[int], as_of_date: date) -> List[PurchaseInvoice]: # New for aging
        async with self.db_manager.session() as session:
            conditions = [
                PurchaseInvoice.status.in_([
                    InvoiceStatusEnum.APPROVED.value, 
                    InvoiceStatusEnum.PARTIALLY_PAID.value, 
                    InvoiceStatusEnum.OVERDUE.value
                ]),
                PurchaseInvoice.total_amount > PurchaseInvoice.amount_paid,
                PurchaseInvoice.invoice_date <= as_of_date
            ]
            if vendor_id is not None:
                conditions.append(PurchaseInvoice.vendor_id == vendor_id)
            
            stmt = select(PurchaseInvoice).where(and_(*conditions))
            result = await session.execute(stmt)
            return list(result.scalars().all())

class InventoryMovementService(IInventoryMovementRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, id_val: int) -> Optional[InventoryMovement]:
        async with self.db_manager.session() as session: return await session.get(InventoryMovement, id_val)
    async def get_all(self) -> List[InventoryMovement]:
        async with self.db_manager.session() as session:
            stmt = select(InventoryMovement).order_by(InventoryMovement.movement_date.desc(), InventoryMovement.id.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def save(self, entity: InventoryMovement, session: Optional[AsyncSession] = None) -> InventoryMovement:
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity); await current_session.flush(); await current_session.refresh(entity); return entity
        if session: return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: return await _save_logic(new_session) # type: ignore
    async def add(self, entity: InventoryMovement) -> InventoryMovement: return await self.save(entity) 
    async def update(self, entity: InventoryMovement) -> InventoryMovement:
        self.logger.warning(f"Update called on InventoryMovementService for ID {entity.id}. Typically movements are immutable.")
        return await self.save(entity)
    async def delete(self, id_val: int) -> bool:
        self.logger.warning(f"Hard delete attempted for InventoryMovement ID {id_val}. This is generally not recommended.")
        async with self.db_manager.session() as session:
            entity = await session.get(InventoryMovement, id_val)
            if entity: await session.delete(entity); return True
            return False

class BankAccountService(IBankAccountRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, id_val: int) -> Optional[BankAccount]:
        async with self.db_manager.session() as session:
            stmt = select(BankAccount).options(selectinload(BankAccount.currency),selectinload(BankAccount.gl_account),selectinload(BankAccount.created_by_user),selectinload(BankAccount.updated_by_user)).where(BankAccount.id == id_val)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[BankAccount]:
        async with self.db_manager.session() as session:
            stmt = select(BankAccount).order_by(BankAccount.account_name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True, currency_code: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[BankAccountSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if active_only: conditions.append(BankAccount.is_active == True)
            if currency_code: conditions.append(BankAccount.currency_code == currency_code)
            stmt = select(BankAccount.id, BankAccount.account_name, BankAccount.bank_name,BankAccount.account_number, BankAccount.currency_code,BankAccount.current_balance, BankAccount.is_active,Account.code.label("gl_account_code"), Account.name.label("gl_account_name")).join(Account, BankAccount.gl_account_id == Account.id)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(BankAccount.account_name)
            if page_size > 0 : stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [BankAccountSummaryData.model_validate(row._asdict()) for row in result.mappings().all()]
    async def get_by_account_number(self, account_number: str) -> Optional[BankAccount]:
        async with self.db_manager.session() as session:
            stmt = select(BankAccount).where(BankAccount.account_number == account_number); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, entity: BankAccount) -> BankAccount:
        async with self.db_manager.session() as session:
            session.add(entity); await session.flush(); await session.refresh(entity); return entity
    async def add(self, entity: BankAccount) -> BankAccount: return await self.save(entity)
    async def update(self, entity: BankAccount) -> BankAccount: return await self.save(entity)
    async def delete(self, id_val: int) -> bool:
        bank_account = await self.get_by_id(id_val)
        if bank_account:
            if bank_account.is_active: bank_account.is_active = False; await self.save(bank_account); return True
            else: self.logger.info(f"BankAccount ID {id_val} is already inactive. No change made by delete."); return True 
        return False
    async def get_by_gl_account_id(self, gl_account_id: int) -> Optional[BankAccount]: # New method
        async with self.db_manager.session() as session:
            stmt = select(BankAccount).where(BankAccount.gl_account_id == gl_account_id)
            result = await session.execute(stmt)
            return result.scalars().first()

class BankTransactionService(IBankTransactionRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, id_val: int) -> Optional[BankTransaction]:
        async with self.db_manager.session() as session:
            stmt = select(BankTransaction).options(selectinload(BankTransaction.bank_account),selectinload(BankTransaction.journal_entry), selectinload(BankTransaction.created_by_user),selectinload(BankTransaction.updated_by_user)).where(BankTransaction.id == id_val)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[BankTransaction]: 
        async with self.db_manager.session() as session:
            stmt = select(BankTransaction).order_by(BankTransaction.transaction_date.desc(), BankTransaction.id.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_for_bank_account(self, bank_account_id: int,start_date: Optional[date] = None,end_date: Optional[date] = None,transaction_type: Optional[BankTransactionTypeEnum] = None,is_reconciled: Optional[bool] = None,is_from_statement_filter: Optional[bool] = None, page: int = 1, page_size: int = 50) -> List[BankTransactionSummaryData]:
        async with self.db_manager.session() as session:
            conditions = [BankTransaction.bank_account_id == bank_account_id]
            if start_date: conditions.append(BankTransaction.transaction_date >= start_date)
            if end_date: conditions.append(BankTransaction.transaction_date <= end_date)
            if transaction_type: conditions.append(BankTransaction.transaction_type == transaction_type.value)
            if is_reconciled is not None: conditions.append(BankTransaction.is_reconciled == is_reconciled)
            if is_from_statement_filter is not None: conditions.append(BankTransaction.is_from_statement == is_from_statement_filter)
            stmt = select(BankTransaction).where(and_(*conditions)).order_by(BankTransaction.transaction_date.desc(), BankTransaction.value_date.desc(), BankTransaction.id.desc()) # type: ignore
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); txns_orm = result.scalars().all()
            summaries: List[BankTransactionSummaryData] = []
            for txn in txns_orm:
                summaries.append(BankTransactionSummaryData(id=txn.id,transaction_date=txn.transaction_date,value_date=txn.value_date,transaction_type=BankTransactionTypeEnum(txn.transaction_type), description=txn.description,reference=txn.reference,amount=txn.amount, is_reconciled=txn.is_reconciled, updated_at=txn.updated_at))
            return summaries
    async def save(self, entity: BankTransaction, session: Optional[AsyncSession] = None) -> BankTransaction:
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity); await current_session.flush(); await current_session.refresh(entity); return entity
        if session: return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: return await _save_logic(new_session) # type: ignore
    async def add(self, entity: BankTransaction) -> BankTransaction: return await self.save(entity)
    async def update(self, entity: BankTransaction) -> BankTransaction: return await self.save(entity)
    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(BankTransaction, id_val)
            if entity:
                if entity.is_reconciled: self.logger.warning(f"Attempt to delete reconciled BankTransaction ID {id_val}. Denied."); return False 
                await session.delete(entity); return True
            return False

class PaymentService(IPaymentRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, id_val: int) -> Optional[Payment]:
        async with self.db_manager.session() as session:
            stmt = select(Payment).options(selectinload(Payment.allocations),selectinload(Payment.bank_account),selectinload(Payment.currency),selectinload(Payment.journal_entry),selectinload(Payment.created_by_user),selectinload(Payment.updated_by_user)).where(Payment.id == id_val)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Payment]:
        async with self.db_manager.session() as session:
            stmt = select(Payment).order_by(Payment.payment_date.desc(), Payment.payment_no.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_by_payment_no(self, payment_no: str) -> Optional[Payment]:
        async with self.db_manager.session() as session:
            stmt = select(Payment).options(selectinload(Payment.allocations)).where(Payment.payment_no == payment_no)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all_summary(self, entity_type: Optional[PaymentEntityTypeEnum] = None,entity_id: Optional[int] = None,status: Optional[PaymentStatusEnum] = None,start_date: Optional[date] = None,end_date: Optional[date] = None,page: int = 1, page_size: int = 50) -> List[PaymentSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if entity_type: conditions.append(Payment.entity_type == entity_type.value)
            if entity_id is not None: conditions.append(Payment.entity_id == entity_id)
            if status: conditions.append(Payment.status == status.value)
            if start_date: conditions.append(Payment.payment_date >= start_date)
            if end_date: conditions.append(Payment.payment_date <= end_date)
            stmt = select(Payment.id, Payment.payment_no, Payment.payment_date, Payment.payment_type,Payment.payment_method, Payment.entity_type, Payment.entity_id,Payment.amount, Payment.currency_code, Payment.status,case((Payment.entity_type == PaymentEntityTypeEnum.CUSTOMER.value, select(Customer.name).where(Customer.id == Payment.entity_id).scalar_subquery()),(Payment.entity_type == PaymentEntityTypeEnum.VENDOR.value, select(Vendor.name).where(Vendor.id == Payment.entity_id).scalar_subquery()),else_=literal_column("'Other/N/A'")).label("entity_name"))
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Payment.payment_date.desc(), Payment.payment_no.desc()) # type: ignore
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [PaymentSummaryData.model_validate(row._asdict()) for row in result.mappings().all()]
    async def save(self, entity: Payment, session: Optional[AsyncSession] = None) -> Payment:
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity); await current_session.flush(); await current_session.refresh(entity)
            if entity.id and entity.allocations: await current_session.refresh(entity, attribute_names=['allocations'])
            return entity
        if session: return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: return await _save_logic(new_session) # type: ignore
    async def add(self, entity: Payment) -> Payment: return await self.save(entity)
    async def update(self, entity: Payment) -> Payment: return await self.save(entity)
    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            payment = await session.get(Payment, id_val)
            if payment:
                if payment.status == PaymentStatusEnum.DRAFT.value: await session.delete(payment); self.logger.info(f"Draft Payment ID {id_val} deleted."); return True
                else: self.logger.warning(f"Attempt to delete non-draft Payment ID {id_val} (status: {payment.status}). Denied."); return False 
            return False

class BankReconciliationService(IBankReconciliationRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)

    async def get_by_id(self, id_val: int) -> Optional[BankReconciliation]:
        async with self.db_manager.session() as session:
            stmt = select(BankReconciliation).options(
                selectinload(BankReconciliation.created_by_user) 
            ).where(BankReconciliation.id == id_val)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[BankReconciliation]:
        async with self.db_manager.session() as session:
            stmt = select(BankReconciliation).order_by(BankReconciliation.statement_date.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: BankReconciliation, session: Optional[AsyncSession] = None) -> BankReconciliation:
        return await self.save(entity, session)

    async def update(self, entity: BankReconciliation, session: Optional[AsyncSession] = None) -> BankReconciliation:
        return await self.save(entity, session)

    async def delete(self, id_val: int) -> bool:
        self.logger.warning(f"Deletion of BankReconciliation ID {id_val} attempted. This operation un-reconciles linked transactions.")
        async with self.db_manager.session() as session: 
            async with session.begin(): 
                update_stmt = (
                    sqlalchemy_update(BankTransaction)
                    .where(BankTransaction.reconciled_bank_reconciliation_id == id_val)
                    .values(is_reconciled=False, reconciled_date=None, reconciled_bank_reconciliation_id=None)
                    .execution_options(synchronize_session=False) 
                )
                await session.execute(update_stmt)
                entity = await session.get(BankReconciliation, id_val)
                if entity:
                    await session.delete(entity)
                    return True
            return False 
            
    async def save(self, entity: BankReconciliation, session: Optional[AsyncSession] = None) -> BankReconciliation:
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity)
            await current_session.flush()
            await current_session.refresh(entity)
            return entity
        if session: return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: # type: ignore
                return await _save_logic(new_session)

    async def get_or_create_draft_reconciliation(
        self, 
        bank_account_id: int, 
        statement_date: date, 
        statement_ending_balance: Decimal, 
        user_id: int, 
        session: AsyncSession
    ) -> BankReconciliation:
        draft_stmt = select(BankReconciliation).where(
            BankReconciliation.bank_account_id == bank_account_id,
            BankReconciliation.statement_date == statement_date,
            BankReconciliation.status == "Draft"
        )
        result = await session.execute(draft_stmt)
        existing_draft = result.scalars().first()

        if existing_draft:
            self.logger.info(f"Found existing draft reconciliation ID {existing_draft.id} for account {bank_account_id} on {statement_date}.")
            if existing_draft.statement_ending_balance != statement_ending_balance:
                existing_draft.statement_ending_balance = statement_ending_balance
            return existing_draft
        else:
            self.logger.info(f"Creating new draft reconciliation for account {bank_account_id} on {statement_date}.")
            new_draft = BankReconciliation(
                bank_account_id=bank_account_id,
                statement_date=statement_date,
                statement_ending_balance=statement_ending_balance,
                calculated_book_balance=Decimal(0), 
                reconciled_difference=statement_ending_balance, 
                status="Draft",
                created_by_user_id=user_id
            )
            session.add(new_draft)
            await session.flush()
            await session.refresh(new_draft)
            return new_draft

    async def mark_transactions_as_provisionally_reconciled(
        self, 
        draft_reconciliation_id: int, 
        transaction_ids: List[int], 
        statement_date: date, 
        user_id: int, 
        session: AsyncSession
    ) -> bool:
        if not transaction_ids:
            return True 

        update_stmt = (
            sqlalchemy_update(BankTransaction)
            .where(BankTransaction.id.in_(transaction_ids))
            .values(
                is_reconciled=True,
                reconciled_date=statement_date,
                reconciled_bank_reconciliation_id=draft_reconciliation_id
            )
            .execution_options(synchronize_session=False) 
        )
        result = await session.execute(update_stmt)
        self.logger.info(f"Marked {result.rowcount} transactions as provisionally reconciled for draft recon ID {draft_reconciliation_id}.")
        return result.rowcount == len(transaction_ids)


    async def finalize_reconciliation(
        self, 
        draft_reconciliation_id: int, 
        statement_ending_balance: Decimal, 
        calculated_book_balance: Decimal, 
        reconciled_difference: Decimal,
        user_id: int,
        session: AsyncSession 
    ) -> Result[BankReconciliation]:
        recon_orm = await session.get(BankReconciliation, draft_reconciliation_id, options=[selectinload(BankReconciliation.bank_account)])
        if not recon_orm:
            return Result.failure([f"Draft Reconciliation ID {draft_reconciliation_id} not found."])
        if recon_orm.status == "Finalized":
            return Result.failure([f"Reconciliation ID {draft_reconciliation_id} is already finalized."])

        recon_orm.status = "Finalized"
        recon_orm.statement_ending_balance = statement_ending_balance
        recon_orm.calculated_book_balance = calculated_book_balance
        recon_orm.reconciled_difference = reconciled_difference
        recon_orm.reconciliation_date = datetime.now(datetime.timezone.utc) 
        
        if recon_orm.bank_account:
            recon_orm.bank_account.last_reconciled_date = recon_orm.statement_date
            recon_orm.bank_account.last_reconciled_balance = recon_orm.statement_ending_balance 
            session.add(recon_orm.bank_account)
        else:
            self.logger.error(f"BankAccount not found for Reconciliation ID {draft_reconciliation_id} during finalization.")
            return Result.failure([f"Associated BankAccount for Reconciliation ID {draft_reconciliation_id} not found."])
            
        session.add(recon_orm)
        return Result.success(recon_orm)

    async def unreconcile_transactions( 
        self, 
        transaction_ids: List[int], 
        user_id: int, 
        session: AsyncSession
    ) -> bool:
        if not transaction_ids:
            return True
        
        update_stmt = (
            sqlalchemy_update(BankTransaction)
            .where(BankTransaction.id.in_(transaction_ids))
            .values(
                is_reconciled=False,
                reconciled_date=None,
                reconciled_bank_reconciliation_id=None
            )
            .execution_options(synchronize_session=False)
        )
        result = await session.execute(update_stmt)
        self.logger.info(f"Unreconciled {result.rowcount} transactions.")
        return result.rowcount == len(transaction_ids)

    async def get_reconciliations_for_account(
        self, 
        bank_account_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> Tuple[List[BankReconciliationSummaryData], int]:
        async with self.db_manager.session() as session:
            base_conditions = [
                BankReconciliation.bank_account_id == bank_account_id,
                BankReconciliation.status == "Finalized" 
            ]
            
            count_stmt = select(func.count(BankReconciliation.id)).where(and_(*base_conditions))
            total_count_res = await session.execute(count_stmt)
            total_records = total_count_res.scalar_one_or_none() or 0

            stmt = select(BankReconciliation, User.username.label("created_by_username"))\
                .join(User, BankReconciliation.created_by_user_id == User.id)\
                .where(and_(*base_conditions))\
                .order_by(BankReconciliation.statement_date.desc(), BankReconciliation.id.desc()) 
            
            if page_size > 0:
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            
            result = await session.execute(stmt)
            summaries: List[BankReconciliationSummaryData] = []
            for row in result.mappings().all():
                recon_orm = row[BankReconciliation]
                summaries.append(BankReconciliationSummaryData(
                    id=recon_orm.id, statement_date=recon_orm.statement_date,
                    statement_ending_balance=recon_orm.statement_ending_balance,
                    reconciled_difference=recon_orm.reconciled_difference,
                    reconciliation_date=recon_orm.reconciliation_date,
                    created_by_username=row.created_by_username
                ))
            return summaries, total_records

    async def get_transactions_for_reconciliation(
        self, reconciliation_id: int
    ) -> Tuple[List[BankTransactionSummaryData], List[BankTransactionSummaryData]]:
        async with self.db_manager.session() as session:
            stmt = select(BankTransaction)\
                .where(BankTransaction.reconciled_bank_reconciliation_id == reconciliation_id)\
                .order_by(BankTransaction.updated_at.desc(), BankTransaction.id) 
            
            result = await session.execute(stmt)
            all_txns_orm = result.scalars().all()

            statement_items: List[BankTransactionSummaryData] = []
            system_items: List[BankTransactionSummaryData] = []

            for txn_orm in all_txns_orm:
                summary_dto = BankTransactionSummaryData(
                    id=txn_orm.id, transaction_date=txn_orm.transaction_date,
                    value_date=txn_orm.value_date, transaction_type=BankTransactionTypeEnum(txn_orm.transaction_type),
                    description=txn_orm.description, reference=txn_orm.reference,
                    amount=txn_orm.amount, is_reconciled=txn_orm.is_reconciled, 
                    updated_at=txn_orm.updated_at
                )
                if txn_orm.is_from_statement:
                    statement_items.append(summary_dto)
                else:
                    system_items.append(summary_dto)
            
            return statement_items, system_items

```

# app/reporting/financial_statement_generator.py
```py
# File: app/reporting/financial_statement_generator.py
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import date, timedelta 
from decimal import Decimal

from app.models.accounting.account import Account 
from app.models.accounting.fiscal_year import FiscalYear
from app.models.accounting.account_type import AccountType 
from app.models.accounting.journal_entry import JournalEntryLine 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.account_service import AccountService
    from app.services.journal_service import JournalService
    from app.services.fiscal_period_service import FiscalPeriodService
    from app.services.tax_service import TaxCodeService
    from app.services.core_services import CompanySettingsService, ConfigurationService
    from app.services.accounting_services import AccountTypeService, DimensionService


class FinancialStatementGenerator:
    def __init__(self, 
                 account_service: "AccountService", 
                 journal_service: "JournalService", 
                 fiscal_period_service: "FiscalPeriodService", 
                 account_type_service: "AccountTypeService", 
                 tax_code_service: Optional["TaxCodeService"] = None, 
                 company_settings_service: Optional["CompanySettingsService"] = None,
                 dimension_service: Optional["DimensionService"] = None,
                 configuration_service: Optional["ConfigurationService"] = None
                 ):
        self.account_service = account_service
        self.journal_service = journal_service
        self.fiscal_period_service = fiscal_period_service
        self.account_type_service = account_type_service
        self.tax_code_service = tax_code_service
        self.company_settings_service = company_settings_service
        self.dimension_service = dimension_service 
        self.configuration_service = configuration_service
        self._account_type_map_cache: Optional[Dict[str, AccountType]] = None


    async def _get_account_type_map(self) -> Dict[str, AccountType]:
        if self._account_type_map_cache is None:
             ats = await self.account_type_service.get_all()
             self._account_type_map_cache = {at.category: at for at in ats} 
        return self._account_type_map_cache

    async def _calculate_account_balances_for_report(self, accounts: List[Account], as_of_date: date) -> List[Dict[str, Any]]:
        result_list = []; acc_type_map = await self._get_account_type_map()
        for account in accounts:
            balance_value = await self.journal_service.get_account_balance(account.id, as_of_date); display_balance = balance_value 
            acc_detail = acc_type_map.get(account.account_type); is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])
            if not is_debit_nature: display_balance = -balance_value 
            result_list.append({'id': account.id, 'code': account.code, 'name': account.name, 'balance': display_balance})
        return result_list

    async def _calculate_account_period_activity_for_report(self, accounts: List[Account], start_date: date, end_date: date) -> List[Dict[str, Any]]:
        result_list = []; acc_type_map = await self._get_account_type_map()
        for account in accounts:
            activity_value = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date); display_activity = activity_value
            acc_detail = acc_type_map.get(account.account_type); is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])
            if not is_debit_nature: display_activity = -activity_value 
            result_list.append({'id': account.id, 'code': account.code, 'name': account.name, 'balance': display_activity})
        return result_list

    async def generate_balance_sheet(self, as_of_date: date, comparative_date: Optional[date] = None, include_zero_balances: bool = False) -> Dict[str, Any]:
        accounts = await self.account_service.get_all_active(); assets_orm = [a for a in accounts if a.account_type == 'Asset']; liabilities_orm = [a for a in accounts if a.account_type == 'Liability']; equity_orm = [a for a in accounts if a.account_type == 'Equity']
        asset_accounts = await self._calculate_account_balances_for_report(assets_orm, as_of_date); liability_accounts = await self._calculate_account_balances_for_report(liabilities_orm, as_of_date); equity_accounts = await self._calculate_account_balances_for_report(equity_orm, as_of_date)
        comp_asset_accs, comp_liab_accs, comp_equity_accs = None, None, None
        if comparative_date: comp_asset_accs = await self._calculate_account_balances_for_report(assets_orm, comparative_date); comp_liab_accs = await self._calculate_account_balances_for_report(liabilities_orm, comparative_date); comp_equity_accs = await self._calculate_account_balances_for_report(equity_orm, comparative_date)
        if not include_zero_balances:
            asset_accounts = [a for a in asset_accounts if a['balance'] != Decimal(0)]; liability_accounts = [a for a in liability_accounts if a['balance'] != Decimal(0)]; equity_accounts = [a for a in equity_accounts if a['balance'] != Decimal(0)]
            if comparative_date: comp_asset_accs = [a for a in comp_asset_accs if a['balance'] != Decimal(0)] if comp_asset_accs else None; comp_liab_accs = [a for a in comp_liab_accs if a['balance'] != Decimal(0)] if comp_liab_accs else None; comp_equity_accs = [a for a in comp_equity_accs if a['balance'] != Decimal(0)] if comp_equity_accs else None
        total_assets = sum(a['balance'] for a in asset_accounts); total_liabilities = sum(a['balance'] for a in liability_accounts); total_equity = sum(a['balance'] for a in equity_accounts)
        comp_total_assets = sum(a['balance'] for a in comp_asset_accs) if comp_asset_accs else None; comp_total_liabilities = sum(a['balance'] for a in comp_liab_accs) if comp_liab_accs else None; comp_total_equity = sum(a['balance'] for a in comp_equity_accs) if comp_equity_accs else None
        return {'title': 'Balance Sheet', 'report_date_description': f"As of {as_of_date.strftime('%d %b %Y')}",'as_of_date': as_of_date, 'comparative_date': comparative_date,'assets': {'accounts': asset_accounts, 'total': total_assets, 'comparative_accounts': comp_asset_accs, 'comparative_total': comp_total_assets},'liabilities': {'accounts': liability_accounts, 'total': total_liabilities, 'comparative_accounts': comp_liab_accs, 'comparative_total': comp_total_liabilities},'equity': {'accounts': equity_accounts, 'total': total_equity, 'comparative_accounts': comp_equity_accs, 'comparative_total': comp_total_equity},'total_liabilities_equity': total_liabilities + total_equity,'comparative_total_liabilities_equity': (comp_total_liabilities + comp_total_equity) if comparative_date and comp_total_liabilities is not None and comp_total_equity is not None else None,'is_balanced': abs(total_assets - (total_liabilities + total_equity)) < Decimal("0.01")}

    async def generate_profit_loss(self, start_date: date, end_date: date, comparative_start: Optional[date] = None, comparative_end: Optional[date] = None) -> Dict[str, Any]:
        accounts = await self.account_service.get_all_active(); revenues_orm = [a for a in accounts if a.account_type == 'Revenue']; expenses_orm = [a for a in accounts if a.account_type == 'Expense'] 
        revenue_accounts = await self._calculate_account_period_activity_for_report(revenues_orm, start_date, end_date); expense_accounts = await self._calculate_account_period_activity_for_report(expenses_orm, start_date, end_date)
        comp_rev_accs, comp_exp_accs = None, None
        if comparative_start and comparative_end: comp_rev_accs = await self._calculate_account_period_activity_for_report(revenues_orm, comparative_start, comparative_end); comp_exp_accs = await self._calculate_account_period_activity_for_report(expenses_orm, comparative_start, comparative_end)
        total_revenue = sum(a['balance'] for a in revenue_accounts); total_expenses = sum(a['balance'] for a in expense_accounts) 
        net_profit = total_revenue - total_expenses
        comp_total_revenue = sum(a['balance'] for a in comp_rev_accs) if comp_rev_accs else None; comp_total_expenses = sum(a['balance'] for a in comp_exp_accs) if comp_exp_accs else None
        comp_net_profit = (comp_total_revenue - comp_total_expenses) if comp_total_revenue is not None and comp_total_expenses is not None else None
        return {'title': 'Profit & Loss Statement', 'report_date_description': f"For the period {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",'start_date': start_date, 'end_date': end_date, 'comparative_start': comparative_start, 'comparative_end': comparative_end,'revenue': {'accounts': revenue_accounts, 'total': total_revenue, 'comparative_accounts': comp_rev_accs, 'comparative_total': comp_total_revenue},'expenses': {'accounts': expense_accounts, 'total': total_expenses, 'comparative_accounts': comp_exp_accs, 'comparative_total': comp_total_expenses},'net_profit': net_profit, 'comparative_net_profit': comp_net_profit}

    async def generate_trial_balance(self, as_of_date: date) -> Dict[str, Any]:
        accounts = await self.account_service.get_all_active(); debit_accounts_list, credit_accounts_list = [], []; total_debits_val, total_credits_val = Decimal(0), Decimal(0) 
        acc_type_map = await self._get_account_type_map()
        for account in accounts:
            raw_balance = await self.journal_service.get_account_balance(account.id, as_of_date)
            if abs(raw_balance) < Decimal("0.01"): continue
            account_data = {'id': account.id, 'code': account.code, 'name': account.name, 'balance': abs(raw_balance)}
            acc_detail = acc_type_map.get(account.account_type); is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])
            if is_debit_nature: 
                if raw_balance >= Decimal(0): debit_accounts_list.append(account_data); total_debits_val += raw_balance
                else: account_data['balance'] = abs(raw_balance); credit_accounts_list.append(account_data); total_credits_val += abs(raw_balance)
            else: 
                if raw_balance <= Decimal(0): credit_accounts_list.append(account_data); total_credits_val += abs(raw_balance)
                else: account_data['balance'] = raw_balance; debit_accounts_list.append(account_data); total_debits_val += raw_balance
        debit_accounts_list.sort(key=lambda a: a['code']); credit_accounts_list.sort(key=lambda a: a['code'])
        return {'title': 'Trial Balance', 'report_date_description': f"As of {as_of_date.strftime('%d %b %Y')}",'as_of_date': as_of_date,'debit_accounts': debit_accounts_list, 'credit_accounts': credit_accounts_list,'total_debits': total_debits_val, 'total_credits': total_credits_val,'is_balanced': abs(total_debits_val - total_credits_val) < Decimal("0.01")}

    async def generate_income_tax_computation(self, fiscal_year: FiscalYear) -> Dict[str, Any]:
        if not self.configuration_service:
            raise RuntimeError("ConfigurationService not available for tax computation.")
            
        start_date, end_date = fiscal_year.start_date, fiscal_year.end_date
        
        pl_data = await self.generate_profit_loss(start_date, end_date)
        net_profit_before_tax = pl_data.get('net_profit', Decimal(0))

        add_back_adjustments: List[Dict[str, Any]] = []
        less_adjustments: List[Dict[str, Any]] = []
        total_add_back = Decimal(0)
        total_less = Decimal(0)

        non_deductible_accounts = await self.account_service.get_accounts_by_tax_treatment('Non-Deductible')
        for account in non_deductible_accounts:
            activity = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date)
            if activity != Decimal(0):
                add_back_adjustments.append({'name': f"{account.code} - {account.name}", 'amount': activity})
                total_add_back += activity

        non_taxable_accounts = await self.account_service.get_accounts_by_tax_treatment('Non-Taxable Income')
        for account in non_taxable_accounts:
            activity = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date)
            if activity != Decimal(0):
                # Revenue has negative balance, so activity is negative. We subtract a negative -> add.
                # To show it as a subtraction, we use the absolute value.
                less_adjustments.append({'name': f"{account.code} - {account.name}", 'amount': abs(activity)})
                total_less += abs(activity)
        
        chargeable_income = net_profit_before_tax + total_add_back - total_less
        
        tax_rate_str = await self.configuration_service.get_config_value("CorpTaxRate_Default", "17.0")
        tax_rate = Decimal(tax_rate_str if tax_rate_str else "17.0")
        
        # Note: This is a simplified calculation. Real tax computation involves capital allowances, PTE, etc.
        estimated_tax = chargeable_income * (tax_rate / Decimal(100))
        if estimated_tax < 0:
            estimated_tax = Decimal(0)

        return {
            'title': 'Income Tax Computation',
            'report_date_description': f"For Financial Year Ended {fiscal_year.end_date.strftime('%d %b %Y')}",
            'fiscal_year_name': fiscal_year.year_name,
            'net_profit_before_tax': net_profit_before_tax,
            'add_back_adjustments': add_back_adjustments,
            'total_add_back': total_add_back,
            'less_adjustments': less_adjustments,
            'total_less': total_less,
            'chargeable_income': chargeable_income,
            'tax_rate': tax_rate,
            'estimated_tax': estimated_tax
        }

    async def generate_gst_f5(self, start_date: date, end_date: date) -> Dict[str, Any]:
        if not self.company_settings_service or not self.tax_code_service: raise RuntimeError("TaxCodeService and CompanySettingsService are required for GST F5.")
        company = await self.company_settings_service.get_company_settings();
        if not company: raise ValueError("Company settings not found.")
        report_data: Dict[str, Any] = {'title': f"GST F5 Return for period {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",'company_name': company.company_name,'gst_registration_no': company.gst_registration_no,'period_start': start_date, 'period_end': end_date,'standard_rated_supplies': Decimal(0), 'zero_rated_supplies': Decimal(0),'exempt_supplies': Decimal(0), 'total_supplies': Decimal(0),'taxable_purchases': Decimal(0), 'output_tax': Decimal(0),'input_tax': Decimal(0), 'tax_adjustments': Decimal(0), 'tax_payable': Decimal(0)}
        entries = await self.journal_service.get_posted_entries_by_date_range(start_date, end_date)
        for entry in entries:
            for line in entry.lines: 
                if not line.tax_code or not line.account: continue
                tax_code_info = await self.tax_code_service.get_tax_code(line.tax_code)
                if not tax_code_info or tax_code_info.tax_type != 'GST': continue
                line_net_amount = (line.debit_amount if line.debit_amount > Decimal(0) else line.credit_amount) 
                tax_on_line = line.tax_amount if line.tax_amount is not None else Decimal(0)
                if line.account.account_type == 'Revenue':
                    if tax_code_info.code == 'SR': report_data['standard_rated_supplies'] += line_net_amount; report_data['output_tax'] += tax_on_line
                    elif tax_code_info.code == 'ZR': report_data['zero_rated_supplies'] += line_net_amount
                    elif tax_code_info.code == 'ES': report_data['exempt_supplies'] += line_net_amount
                elif line.account.account_type in ['Expense', 'Asset']:
                    if tax_code_info.code == 'TX': report_data['taxable_purchases'] += line_net_amount; report_data['input_tax'] += tax_on_line
                    elif tax_code_info.code == 'BL': report_data['taxable_purchases'] += line_net_amount 
        report_data['total_supplies'] = (report_data['standard_rated_supplies'] + report_data['zero_rated_supplies'] + report_data['exempt_supplies'])
        report_data['tax_payable'] = report_data['output_tax'] - report_data['input_tax'] + report_data['tax_adjustments']
        return report_data

    async def generate_general_ledger(self, account_id: int, start_date: date, end_date: date,
                                      dimension1_id: Optional[int] = None, 
                                      dimension2_id: Optional[int] = None) -> Dict[str, Any]:
        account_orm = await self.account_service.get_by_id(account_id)
        if not account_orm:
            raise ValueError(f"Account with ID {account_id} not found.")

        ob_date = start_date - timedelta(days=1)
        opening_balance = await self.journal_service.get_account_balance(account_id, ob_date)

        lines: List[JournalEntryLine] = await self.journal_service.get_posted_lines_for_account_in_range(
            account_id, start_date, end_date, dimension1_id, dimension2_id 
        )

        transactions_data = []
        current_balance = opening_balance
        for line in lines:
            if not line.journal_entry: continue 
            movement = line.debit_amount - line.credit_amount
            current_balance += movement
            transactions_data.append({
                "date": line.journal_entry.entry_date, "entry_no": line.journal_entry.entry_no,
                "je_description": line.journal_entry.description or "", "line_description": line.description or "",
                "debit": line.debit_amount, "credit": line.credit_amount, "balance": current_balance,
                "dim1_id": line.dimension1_id, "dim2_id": line.dimension2_id 
            })
        closing_balance = current_balance
        
        report_desc = f"For Account: {account_orm.code} - {account_orm.name} from {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"
        if dimension1_id and self.dimension_service:
            dim1 = await self.dimension_service.get_by_id(dimension1_id)
            if dim1: report_desc += f" (Dim1: {dim1.dimension_type}-{dim1.code})"
        if dimension2_id and self.dimension_service:
            dim2 = await self.dimension_service.get_by_id(dimension2_id)
            if dim2: report_desc += f" (Dim2: {dim2.dimension_type}-{dim2.code})"

        return {
            "title": "General Ledger", "report_date_description": report_desc,
            "account_code": account_orm.code, "account_name": account_orm.name,
            "start_date": start_date, "end_date": end_date,
            "opening_balance": opening_balance, "transactions": transactions_data,
            "closing_balance": closing_balance
        }

```

# app/reporting/dashboard_manager.py
```py
# File: app/reporting/dashboard_manager.py
from typing import Optional, TYPE_CHECKING, List, Dict
from datetime import date
from decimal import Decimal

from app.utils.pydantic_models import DashboardKPIData
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.account import Account

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

CURRENT_ASSET_SUBTYPES = ["Cash and Cash Equivalents", "Accounts Receivable", "Inventory", "Prepaid Expenses", "Other Current Assets", "Current Asset"]
CURRENT_LIABILITY_SUBTYPES = ["Accounts Payable", "Accrued Liabilities", "Short-Term Loans", "Current Portion of Long-Term Debt", "GST Payable", "Other Current Liabilities", "Current Liability"]
NON_CURRENT_LIABILITY_SUBTYPES = ["Long-term Liability", "Long-Term Loans"]

class DashboardManager:
    def __init__(self, app_core: "ApplicationCore"):
        self.app_core = app_core
        self.logger = app_core.logger

    async def get_dashboard_kpis(self, as_of_date: Optional[date] = None) -> Optional[DashboardKPIData]:
        try:
            effective_date = as_of_date if as_of_date is not None else date.today()
            self.logger.info(f"Fetching dashboard KPIs as of {effective_date}...")
            
            company_settings = await self.app_core.company_settings_service.get_company_settings()
            if not company_settings: self.logger.error("Company settings not found."); return None
            base_currency = company_settings.base_currency

            all_fiscal_years_orm: List[FiscalYear] = await self.app_core.fiscal_year_service.get_all()
            current_fy: Optional[FiscalYear] = next((fy for fy in sorted(all_fiscal_years_orm, key=lambda fy: fy.start_date, reverse=True) if fy.start_date <= effective_date <= fy.end_date and not fy.is_closed), None)
            if not current_fy: current_fy = next((fy for fy in sorted(all_fiscal_years_orm, key=lambda fy: fy.start_date, reverse=True) if not fy.is_closed), None)
            if not current_fy and all_fiscal_years_orm: current_fy = max(all_fiscal_years_orm, key=lambda fy: fy.start_date)

            total_revenue_ytd, total_expenses_ytd, net_profit_ytd = Decimal(0), Decimal(0), Decimal(0)
            kpi_period_description = f"As of {effective_date.strftime('%d %b %Y')} (No active FY)"
            if current_fy and effective_date >= current_fy.start_date:
                effective_end_date_for_ytd = min(effective_date, current_fy.end_date)
                kpi_period_description = f"YTD as of {effective_end_date_for_ytd.strftime('%d %b %Y')} (FY: {current_fy.year_name})"
                pl_data = await self.app_core.financial_statement_generator.generate_profit_loss(current_fy.start_date, effective_end_date_for_ytd)
                if pl_data:
                    total_revenue_ytd, total_expenses_ytd, net_profit_ytd = pl_data.get('revenue', {}).get('total', Decimal(0)), pl_data.get('expenses', {}).get('total', Decimal(0)), pl_data.get('net_profit', Decimal(0))
            elif current_fy:
                 kpi_period_description = f"As of {effective_date.strftime('%d %b %Y')} (FY: {current_fy.year_name} not started)"

            current_cash_balance = await self._get_total_cash_balance(base_currency, effective_date)
            total_outstanding_ar = await self.app_core.customer_service.get_total_outstanding_balance(); total_outstanding_ap = await self.app_core.vendor_service.get_total_outstanding_balance()
            total_ar_overdue = await self.app_core.customer_service.get_total_overdue_balance(); total_ap_overdue = await self.app_core.vendor_service.get_total_overdue_balance() 
            ar_aging_summary = await self.app_core.customer_service.get_ar_aging_summary(effective_date); ap_aging_summary = await self.app_core.vendor_service.get_ap_aging_summary(effective_date)

            # --- Ratio Calculations ---
            total_current_assets, total_current_liabilities, total_non_current_liabilities, total_inventory, total_equity = (Decimal(0) for _ in range(5))
            all_active_accounts: List[Account] = await self.app_core.account_service.get_all_active()

            for acc in all_active_accounts:
                balance = await self.app_core.journal_service.get_account_balance(acc.id, effective_date)
                if acc.account_type == "Asset":
                    if acc.sub_type in CURRENT_ASSET_SUBTYPES: total_current_assets += balance
                    if acc.sub_type == "Inventory": total_inventory += balance
                elif acc.account_type == "Liability":
                    if acc.sub_type in CURRENT_LIABILITY_SUBTYPES: total_current_liabilities += balance
                    elif acc.sub_type in NON_CURRENT_LIABILITY_SUBTYPES: total_non_current_liabilities += balance
                elif acc.account_type == "Equity": total_equity += balance

            total_liabilities = total_current_liabilities + total_non_current_liabilities
            
            quick_ratio: Optional[Decimal] = None
            if total_current_liabilities > 0: quick_ratio = ((total_current_assets - total_inventory) / total_current_liabilities).quantize(Decimal("0.01"))
            elif (total_current_assets - total_inventory) > 0: quick_ratio = Decimal('Infinity')

            debt_to_equity_ratio: Optional[Decimal] = None
            if total_equity > 0: debt_to_equity_ratio = (total_liabilities / total_equity).quantize(Decimal("0.01"))
            elif total_liabilities > 0: debt_to_equity_ratio = Decimal('Infinity')

            current_ratio: Optional[Decimal] = None
            if total_current_liabilities > 0: current_ratio = (total_current_assets / total_current_liabilities).quantize(Decimal("0.01"))
            elif total_current_assets > 0: current_ratio = Decimal('Infinity')

            return DashboardKPIData(
                kpi_period_description=kpi_period_description, base_currency=base_currency,
                total_revenue_ytd=total_revenue_ytd, total_expenses_ytd=total_expenses_ytd, net_profit_ytd=net_profit_ytd,
                current_cash_balance=current_cash_balance, total_outstanding_ar=total_outstanding_ar, total_outstanding_ap=total_outstanding_ap,
                total_ar_overdue=total_ar_overdue, total_ap_overdue=total_ap_overdue,
                ar_aging_current=ar_aging_summary.get("Current", Decimal(0)), ar_aging_1_30=ar_aging_summary.get("1-30 Days", Decimal(0)),
                ar_aging_31_60=ar_aging_summary.get("31-60 Days", Decimal(0)), ar_aging_61_90=ar_aging_summary.get("61-90 Days", Decimal(0)),
                ar_aging_91_plus=ar_aging_summary.get("91+ Days", Decimal(0)),
                ap_aging_current=ap_aging_summary.get("Current", Decimal(0)), ap_aging_1_30=ap_aging_summary.get("1-30 Days", Decimal(0)),
                ap_aging_31_60=ap_aging_summary.get("31-60 Days", Decimal(0)), ap_aging_61_90=ap_aging_summary.get("61-90 Days", Decimal(0)),
                ap_aging_91_plus=ap_aging_summary.get("91+ Days", Decimal(0)),
                total_current_assets=total_current_assets.quantize(Decimal("0.01")), total_current_liabilities=total_current_liabilities.quantize(Decimal("0.01")),
                total_inventory=total_inventory.quantize(Decimal("0.01")), total_liabilities=total_liabilities.quantize(Decimal("0.01")), total_equity=total_equity.quantize(Decimal("0.01")),
                current_ratio=current_ratio, quick_ratio=quick_ratio, debt_to_equity_ratio=debt_to_equity_ratio
            )
        except Exception as e:
            self.logger.error(f"Error fetching dashboard KPIs: {e}", exc_info=True)
            return None

    async def _get_total_cash_balance(self, base_currency: str, as_of_date: date) -> Decimal:
        active_bank_accounts_summary = await self.app_core.bank_account_service.get_all_summary(active_only=True, currency_code=base_currency, page_size=-1)
        total_cash = sum(ba.current_balance for ba in active_bank_accounts_summary if ba.currency_code == base_currency and ba.current_balance is not None)
        cash_on_hand_code = await self.app_core.configuration_service.get_config_value("SysAcc_DefaultCash")
        if cash_on_hand_code:
            cash_on_hand_acc = await self.app_core.account_service.get_by_code(cash_on_hand_code)
            if cash_on_hand_acc and cash_on_hand_acc.is_active:
                linked_bank_acc_check = await self.app_core.bank_account_service.get_by_gl_account_id(cash_on_hand_acc.id)
                if not linked_bank_acc_check:
                    total_cash += await self.app_core.journal_service.get_account_balance(cash_on_hand_acc.id, as_of_date)
        return total_cash.quantize(Decimal("0.01"))

```

# app/reporting/report_engine.py
```py
# File: app/reporting/report_engine.py
from typing import Dict, Any, Literal, List, Optional, TYPE_CHECKING, cast 
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepInFrame
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib import colors 
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm 
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
import openpyxl 
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill 
from openpyxl.utils import get_column_letter 
from decimal import Decimal, InvalidOperation
from datetime import date

from app.utils.pydantic_models import GSTReturnData, GSTTransactionLineDetail

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class ReportEngine:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(name='ReportTitle', parent=self.styles['h1'], alignment=TA_CENTER, spaceAfter=0.2*inch))
        self.styles.add(ParagraphStyle(name='ReportSubTitle', parent=self.styles['h2'], alignment=TA_CENTER, fontSize=12, spaceAfter=0.2*inch))
        self.styles.add(ParagraphStyle(name='SectionHeader', parent=self.styles['h3'], fontSize=11, spaceBefore=0.2*inch, spaceAfter=0.1*inch, textColor=colors.HexColor("#2F5496")))
        self.styles.add(ParagraphStyle(name='AccountName', parent=self.styles['Normal'], leftIndent=0.2*inch))
        self.styles.add(ParagraphStyle(name='AccountNameBold', parent=self.styles['AccountName'], fontName='Helvetica-Bold'))
        self.styles.add(ParagraphStyle(name='Amount', parent=self.styles['Normal'], alignment=TA_RIGHT))
        self.styles.add(ParagraphStyle(name='AmountBold', parent=self.styles['Amount'], fontName='Helvetica-Bold'))
        self.styles.add(ParagraphStyle(name='TableHeader', parent=self.styles['Normal'], fontName='Helvetica-Bold', alignment=TA_CENTER, textColor=colors.whitesmoke))
        self.styles.add(ParagraphStyle(name='Footer', parent=self.styles['Normal'], alignment=TA_CENTER, fontSize=8))
        self.styles.add(ParagraphStyle(name='NormalRight', parent=self.styles['Normal'], alignment=TA_RIGHT))
        self.styles.add(ParagraphStyle(name='NormalCenter', parent=self.styles['Normal'], alignment=TA_CENTER))
        self.styles.add(ParagraphStyle(name='GLAccountHeader', parent=self.styles['h3'], fontSize=10, spaceBefore=0.1*inch, spaceAfter=0.05*inch, alignment=TA_LEFT))

    async def export_report(self, report_data: Dict[str, Any], format_type: Literal["pdf", "excel", "gst_excel_detail"]) -> Optional[bytes]:
        title = report_data.get('title', "Financial Report")
        is_gst_detail_export = isinstance(report_data, GSTReturnData) and "gst_excel_detail" in format_type

        if format_type == "pdf":
            if title == "Balance Sheet": return await self._export_balance_sheet_to_pdf(report_data)
            elif title == "Profit & Loss Statement": return await self._export_profit_loss_to_pdf(report_data)
            elif title == "Trial Balance": return await self._export_trial_balance_to_pdf(report_data)
            elif title == "General Ledger": return await self._export_general_ledger_to_pdf(report_data)
            elif title == "Income Tax Computation": return await self._export_tax_computation_to_pdf(report_data)
            else: return self._export_generic_table_to_pdf(report_data) 
        elif format_type == "excel":
            if title == "Balance Sheet": return await self._export_balance_sheet_to_excel(report_data)
            elif title == "Profit & Loss Statement": return await self._export_profit_loss_to_excel(report_data)
            elif title == "Trial Balance": return await self._export_trial_balance_to_excel(report_data)
            elif title == "General Ledger": return await self._export_general_ledger_to_excel(report_data)
            elif title == "Income Tax Computation": return await self._export_tax_computation_to_excel(report_data)
            else: return self._export_generic_table_to_excel(report_data) 
        elif is_gst_detail_export:
            return await self._export_gst_f5_details_to_excel(cast(GSTReturnData, report_data))
        else:
            self.app_core.logger.error(f"Unsupported report format or data type mismatch: {format_type}, type: {type(report_data)}")
            return None

    def _format_decimal(self, value: Optional[Decimal], places: int = 2, show_blank_for_zero: bool = False) -> str:
        if value is None: return "" if show_blank_for_zero else self._format_decimal(Decimal(0), places) 
        if not isinstance(value, Decimal): 
            try: value = Decimal(str(value))
            except InvalidOperation: return "ERR_DEC" 
        if show_blank_for_zero and value.is_zero(): return ""
        return f"{value:,.{places}f}"

    async def _get_company_name(self) -> str:
        settings = await self.app_core.company_settings_service.get_company_settings()
        return settings.company_name if settings else "Your Company"

    def _add_pdf_header_footer(self, canvas, doc, company_name: str, report_title: str, date_desc: str):
        canvas.saveState(); page_width = doc.width + doc.leftMargin + doc.rightMargin; header_y_start = doc.height + doc.topMargin - 0.5*inch
        canvas.setFont('Helvetica-Bold', 14); canvas.drawCentredString(page_width/2, header_y_start, company_name)
        canvas.setFont('Helvetica-Bold', 12); canvas.drawCentredString(page_width/2, header_y_start - 0.25*inch, report_title)
        canvas.setFont('Helvetica', 10); canvas.drawCentredString(page_width/2, header_y_start - 0.5*inch, date_desc)
        footer_y = 0.5*inch; canvas.setFont('Helvetica', 8); canvas.drawString(doc.leftMargin, footer_y, f"Generated on: {date.today().strftime('%d %b %Y')}"); canvas.drawRightString(page_width - doc.rightMargin, footer_y, f"Page {doc.page}"); canvas.restoreState()

    async def _export_balance_sheet_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO(); company_name = await self._get_company_name(); report_title = report_data.get('title', "Balance Sheet"); date_desc = report_data.get('report_date_description', "")
        doc = SimpleDocTemplate(buffer, pagesize=A4,rightMargin=0.75*inch, leftMargin=0.75*inch,topMargin=1.25*inch, bottomMargin=0.75*inch)
        story: List[Any] = []; has_comparative = bool(report_data.get('comparative_date')); col_widths = [3.5*inch, 1.5*inch]; 
        if has_comparative: col_widths.append(1.5*inch)
        header_texts = ["Description", "Current Period"]; 
        if has_comparative: header_texts.append("Comparative")
        table_header_row = [Paragraph(text, self.styles['TableHeader']) for text in header_texts]
        def build_section_data(section_key: str, title: str):
            data: List[List[Any]] = []; section = report_data.get(section_key, {})
            data.append([Paragraph(title, self.styles['SectionHeader'])] + (["", ""] if has_comparative else [""]))
            for acc in section.get('accounts', []):
                row = [Paragraph(f"{acc['code']} - {acc['name']}", self.styles['AccountName']), Paragraph(self._format_decimal(acc['balance']), self.styles['Amount'])]
                if has_comparative:
                    comp_bal_str = ""; 
                    if section.get('comparative_accounts'):
                        comp_acc_list = section['comparative_accounts']; comp_acc_match = next((ca for ca in comp_acc_list if ca['id'] == acc['id']), None)
                        if comp_acc_match and comp_acc_match.get('balance') is not None: comp_bal_str = self._format_decimal(comp_acc_match['balance'])
                    row.append(Paragraph(comp_bal_str, self.styles['Amount']))
                data.append(row)
            total_row = [Paragraph(f"Total {title}", self.styles['AccountNameBold']), Paragraph(self._format_decimal(section.get('total')), self.styles['AmountBold'])]
            if has_comparative: total_row.append(Paragraph(self._format_decimal(section.get('comparative_total')), self.styles['AmountBold']))
            data.append(total_row); data.append([Spacer(1, 0.1*inch)] * len(col_widths)); return data
        bs_data: List[List[Any]] = [table_header_row]; bs_data.extend(build_section_data('assets', 'Assets')); bs_data.extend(build_section_data('liabilities', 'Liabilities')); bs_data.extend(build_section_data('equity', 'Equity'))
        total_lia_eq_row = [Paragraph("Total Liabilities & Equity", self.styles['AccountNameBold']), Paragraph(self._format_decimal(report_data.get('total_liabilities_equity')), self.styles['AmountBold'])]
        if has_comparative: total_lia_eq_row.append(Paragraph(self._format_decimal(report_data.get('comparative_total_liabilities_equity')), self.styles['AmountBold']))
        bs_data.append(total_lia_eq_row); bs_table = Table(bs_data, colWidths=col_widths)
        style = TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LINEABOVE', (0, -1), (-1,-1), 1, colors.black), ('LINEBELOW', (1, -1), (-1, -1), 1, colors.black, None, (2,2), 0, 1), ('LINEBELOW', (1, -1), (-1, -1), 0.5, colors.black, None, (1,1), 0, 1),])
        current_row_idx = 1 
        for section_key in ['assets', 'liabilities', 'equity']:
            if section_key in report_data: style.add('SPAN', (0, current_row_idx), (len(col_widths)-1, current_row_idx)); current_row_idx += len(report_data[section_key].get('accounts', [])) + 2 
        bs_table.setStyle(style); story.append(bs_table)
        if report_data.get('is_balanced') is False: story.append(Spacer(1, 0.2*inch)); story.append(Paragraph("Warning: Balance Sheet is out of balance!", ParagraphStyle(name='Warning', parent=self.styles['Normal'], textColor=colors.red, fontName='Helvetica-Bold')))
        doc.build(story, onFirstPage=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc), onLaterPages=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc)); return buffer.getvalue()

    async def _export_profit_loss_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO(); company_name = await self._get_company_name(); report_title = report_data.get('title', "Profit & Loss Statement"); date_desc = report_data.get('report_date_description', "")
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.75*inch, leftMargin=0.75*inch,topMargin=1.25*inch, bottomMargin=0.75*inch)
        story: List[Any] = []; has_comparative = bool(report_data.get('comparative_start')); comp_header_text = "Comparative"; 
        if has_comparative and report_data.get('comparative_start') and report_data.get('comparative_end'): comp_start_str = report_data['comparative_start'].strftime('%d/%m/%y'); comp_end_str = report_data['comparative_end'].strftime('%d/%m/%y'); comp_header_text = f"Comp. ({comp_start_str}-{comp_end_str})"
        headers = ["Description", "Amount"]; 
        if has_comparative: headers.append(comp_header_text); 
        table_header_row = [Paragraph(text, self.styles['TableHeader']) for text in headers]; col_widths = [3.5*inch, 1.5*inch]; 
        if has_comparative: col_widths.append(1.5*inch)
        def build_pl_section_data(section_key: str, title: str, is_subtraction: bool = False):
            data: List[List[Any]] = []; section = report_data.get(section_key, {})
            data.append([Paragraph(title, self.styles['SectionHeader'])] + (["", ""] if has_comparative else [""]))
            for acc in section.get('accounts', []):
                balance = acc['balance']; row = [Paragraph(f"  {acc['code']} - {acc['name']}", self.styles['AccountName']), Paragraph(self._format_decimal(balance), self.styles['Amount'])]
                if has_comparative:
                    comp_bal_str = ""; 
                    if section.get('comparative_accounts'):
                        comp_acc_list = section['comparative_accounts']; comp_acc_match = next((ca for ca in comp_acc_list if ca['id'] == acc['id']), None)
                        if comp_acc_match and comp_acc_match.get('balance') is not None: comp_bal_str = self._format_decimal(comp_acc_match['balance'])
                    row.append(Paragraph(comp_bal_str, self.styles['Amount']))
                data.append(row)
            total = section.get('total'); total_row = [Paragraph(f"Total {title}", self.styles['AccountNameBold']), Paragraph(self._format_decimal(total), self.styles['AmountBold'])]
            if has_comparative: comp_total = section.get('comparative_total'); total_row.append(Paragraph(self._format_decimal(comp_total), self.styles['AmountBold']))
            data.append(total_row); data.append([Spacer(1, 0.1*inch)] * len(col_widths)); return data, total, section.get('comparative_total') if has_comparative else None
        pl_data: List[List[Any]] = [table_header_row]; rev_data, total_revenue, comp_total_revenue = build_pl_section_data('revenue', 'Revenue'); pl_data.extend(rev_data)
        exp_data, total_expenses, comp_total_expenses = build_pl_section_data('expenses', 'Operating Expenses', is_subtraction=True); pl_data.extend(exp_data)
        net_profit = report_data.get('net_profit', Decimal(0)); comp_net_profit = report_data.get('comparative_net_profit')
        net_profit_row = [Paragraph("Net Profit / (Loss)", self.styles['AccountNameBold']), Paragraph(self._format_decimal(net_profit), self.styles['AmountBold'])]
        if has_comparative: net_profit_row.append(Paragraph(self._format_decimal(comp_net_profit), self.styles['AmountBold']))
        pl_data.append(net_profit_row); pl_table = Table(pl_data, colWidths=col_widths)
        style = TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LINEABOVE', (1, -1), (-1,-1), 1, colors.black), ('LINEBELOW', (1, -1), (-1, -1), 1, colors.black, None, (2,2), 0, 1), ('LINEBELOW', (1, -1), (-1, -1), 0.5, colors.black, None, (1,1), 0, 1),])
        current_row_idx = 1
        for section_key in ['revenue', 'expenses']: 
            if section_key in report_data: style.add('SPAN', (0, current_row_idx), (len(col_widths)-1, current_row_idx)); current_row_idx += len(report_data[section_key].get('accounts', [])) + 2
        pl_table.setStyle(style); story.append(pl_table)
        doc.build(story, onFirstPage=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc), onLaterPages=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc)); return buffer.getvalue()

    async def _export_trial_balance_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO(); company_name = await self._get_company_name(); report_title = report_data.get('title', "Trial Balance"); date_desc = report_data.get('report_date_description', f"As of {date.today().strftime('%d %b %Y')}")
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.75*inch, leftMargin=0.75*inch,topMargin=1.25*inch, bottomMargin=0.75*inch)
        story: List[Any] = []; col_widths = [1.5*inch, 3*inch, 1.25*inch, 1.25*inch]; header_texts = ["Account Code", "Account Name", "Debit", "Credit"]
        table_header_row = [Paragraph(text, self.styles['TableHeader']) for text in header_texts]; tb_data: List[List[Any]] = [table_header_row]
        for acc in report_data.get('debit_accounts', []): tb_data.append([Paragraph(acc['code'], self.styles['Normal']), Paragraph(acc['name'], self.styles['Normal']), Paragraph(self._format_decimal(acc['balance']), self.styles['NormalRight']), Paragraph("", self.styles['NormalRight'])])
        for acc in report_data.get('credit_accounts', []): tb_data.append([Paragraph(acc['code'], self.styles['Normal']), Paragraph(acc['name'], self.styles['Normal']), Paragraph("", self.styles['NormalRight']), Paragraph(self._format_decimal(acc['balance']), self.styles['NormalRight'])])
        tb_data.append([Paragraph(""), Paragraph("TOTALS", self.styles['AccountNameBold']), Paragraph(self._format_decimal(report_data.get('total_debits')), self.styles['AmountBold']), Paragraph(self._format_decimal(report_data.get('total_credits')), self.styles['AmountBold'])])
        tb_table = Table(tb_data, colWidths=col_widths)
        style = TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LINEABOVE', (2, -1), (3, -1), 1, colors.black), ('LINEBELOW', (2, -1), (3, -1), 1, colors.black), ('ALIGN', (2,1), (3,-1), 'RIGHT'),])
        tb_table.setStyle(style); story.append(tb_table)
        if report_data.get('is_balanced') is False: story.append(Spacer(1,0.2*inch)); story.append(Paragraph("Warning: Trial Balance is out of balance!", ParagraphStyle(name='Warning', parent=self.styles['Normal'], textColor=colors.red, fontName='Helvetica-Bold')))
        doc.build(story, onFirstPage=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc), onLaterPages=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc)); return buffer.getvalue()

    async def _export_general_ledger_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO(); company_name = await self._get_company_name(); report_title = report_data.get('title', "General Ledger"); date_desc = report_data.get('report_date_description', "") 
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=1.25*inch, bottomMargin=0.75*inch)
        story: List[Any] = []; story.append(Paragraph(f"Account: {report_data.get('account_code')} - {report_data.get('account_name')}", self.styles['GLAccountHeader'])); story.append(Spacer(1, 0.1*inch)); story.append(Paragraph(f"Opening Balance: {self._format_decimal(report_data.get('opening_balance'))}", self.styles['AccountNameBold'])); story.append(Spacer(1, 0.2*inch))
        headers = ["Date", "Entry No.", "JE Description", "Line Description", "Debit", "Credit", "Balance"]
        table_header_row = [Paragraph(h, self.styles['TableHeader']) for h in headers]; gl_data: List[List[Any]] = [table_header_row]
        for txn in report_data.get('transactions', []): gl_data.append([Paragraph(txn['date'].strftime('%d/%m/%Y') if isinstance(txn['date'], date) else str(txn['date']), self.styles['NormalCenter']), Paragraph(txn['entry_no'], self.styles['Normal']), Paragraph(txn.get('je_description','')[:40], self.styles['Normal']), Paragraph(txn.get('line_description','')[:40], self.styles['Normal']), Paragraph(self._format_decimal(txn['debit'], show_blank_for_zero=True), self.styles['NormalRight']), Paragraph(self._format_decimal(txn['credit'], show_blank_for_zero=True), self.styles['NormalRight']), Paragraph(self._format_decimal(txn['balance']), self.styles['NormalRight'])])
        col_widths_gl = [0.9*inch, 1.0*inch, 2.8*inch, 2.8*inch, 1.0*inch, 1.0*inch, 1.19*inch]
        gl_table = Table(gl_data, colWidths=col_widths_gl); style = TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,1), (1,-1), 'CENTER'), ('ALIGN', (4,1), (6,-1), 'RIGHT'),]); gl_table.setStyle(style); story.append(gl_table); story.append(Spacer(1, 0.1*inch)); story.append(Paragraph(f"Closing Balance: {self._format_decimal(report_data.get('closing_balance'))}", self.styles['AmountBold']))
        doc.build(story, onFirstPage=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc), onLaterPages=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc)); return buffer.getvalue()

    async def _export_tax_computation_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO(); company_name = await self._get_company_name(); report_title = report_data.get('title', "Tax Computation"); date_desc = report_data.get('report_date_description', "")
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.75*inch, leftMargin=0.75*inch, topMargin=1.25*inch, bottomMargin=0.75*inch)
        story: List[Any] = []; col_widths = [5*inch, 1.5*inch]; table_header_row = [Paragraph("Description", self.styles['TableHeader']), Paragraph("Amount", self.styles['TableHeader'])]; data: List[List[Any]] = [table_header_row]
        data.append([Paragraph("Net Profit Before Tax", self.styles['AccountNameBold']), Paragraph(self._format_decimal(report_data.get('net_profit_before_tax')), self.styles['AmountBold'])])
        data.append([Paragraph("Add: Non-Deductible Expenses", self.styles['SectionHeader']), ""]); 
        for adj in report_data.get('add_back_adjustments', []): data.append([Paragraph(f"  {adj['name']}", self.styles['AccountName']), Paragraph(self._format_decimal(adj['amount']), self.styles['Amount'])])
        data.append([Paragraph("Less: Non-Taxable Income", self.styles['SectionHeader']), ""])
        for adj in report_data.get('less_adjustments', []): data.append([Paragraph(f"  {adj['name']}", self.styles['AccountName']), Paragraph(f"({self._format_decimal(adj['amount'])})", self.styles['Amount'])])
        data.append([Paragraph("Chargeable Income", self.styles['AccountNameBold']), Paragraph(self._format_decimal(report_data.get('chargeable_income')), self.styles['AmountBold'])])
        data.append([Paragraph(f"Estimated Tax @ {report_data.get('tax_rate', 0):.2f}%", self.styles['AccountNameBold']), Paragraph(self._format_decimal(report_data.get('estimated_tax')), self.styles['AmountBold'])])
        table = Table(data, colWidths=col_widths)
        style = TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LINEABOVE', (1, -1), (1,-1), 1, colors.black), ('LINEBELOW', (1, -1), (1, -1), 1, colors.black, None, (2,2), 0, 1),])
        style.add('SPAN', (0, 2), (1, 2)); style.add('SPAN', (0, len(data)-5), (1, len(data)-5)); 
        table.setStyle(style); story.append(table)
        doc.build(story, onFirstPage=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc), onLaterPages=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc)); return buffer.getvalue()

    def _export_generic_table_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        self.app_core.logger.warning(f"Using generic PDF export for report: {report_data.get('title')}")
        buffer = BytesIO(); doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story: List[Any] = [Paragraph(report_data.get('title', "Report"), self.styles['h1'])]; 
        if report_data.get('report_date_description'): story.append(Paragraph(report_data.get('report_date_description'), self.styles['h3']))
        story.append(Spacer(1, 0.2*inch)); data_to_display = report_data.get('data_rows', []); headers = report_data.get('headers', [])
        if headers and data_to_display:
            table_data: List[List[Any]] = [[Paragraph(str(h), self.styles['TableHeader']) for h in headers]]
            for row_dict in data_to_display: table_data.append([Paragraph(str(row_dict.get(h_key, '')), self.styles['Normal']) for h_key in headers]) 
            num_cols = len(headers); col_widths_generic = [doc.width/num_cols]*num_cols
            table = Table(table_data, colWidths=col_widths_generic); table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD"))])); story.append(table)
        else: story.append(Paragraph("No data or headers provided for generic export.", self.styles['Normal']))
        doc.build(story); return buffer.getvalue()

    def _apply_excel_header_style(self, cell, bold=True, size=12, alignment='center', fill_color: Optional[str]=None):
        cell.font = Font(bold=bold, size=size, color="FFFFFF" if fill_color else "000000")
        if alignment == 'center': cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        elif alignment == 'right': cell.alignment = Alignment(horizontal='right', vertical='center')
        else: cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        if fill_color: cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")

    def _apply_excel_amount_style(self, cell, bold=False, underline: Optional[str]=None):
        cell.number_format = '#,##0.00;[Red](#,##0.00);"-"' 
        cell.alignment = Alignment(horizontal='right')
        if bold: cell.font = Font(bold=True)
        if underline: cell.border = Border(bottom=Side(style=underline))
        
    async def _export_balance_sheet_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Balance Sheet"; company_name = await self._get_company_name(); has_comparative = bool(report_data.get('comparative_date')); row_num = 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=company_name), size=14); row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('title')), size=12); row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')), size=10, bold=False); row_num += 2
        headers = ["Description", "Current Period"]; 
        if has_comparative: headers.append("Comparative")
        for col, header_text in enumerate(headers, 1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), alignment='center' if col>0 else 'left', fill_color="4F81BD")
        row_num +=1
        def write_section(section_key: str, title: str):
            nonlocal row_num; section = report_data.get(section_key, {})
            ws.cell(row=row_num, column=1, value=title).font = Font(bold=True, size=11, color="2F5496"); row_num +=1
            for acc in section.get('accounts', []):
                ws.cell(row=row_num, column=1, value=f"  {acc['code']} - {acc['name']}")
                self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(acc['balance'] if acc.get('balance') is not None else 0)))
                if has_comparative:
                    comp_val = None
                    if section.get('comparative_accounts'):
                        comp_acc_match = next((ca for ca in section['comparative_accounts'] if ca['id'] == acc['id']), None)
                        if comp_acc_match and comp_acc_match.get('balance') is not None: comp_val = float(comp_acc_match['balance'])
                    self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=comp_val if comp_val is not None else "-"))
                row_num +=1
            ws.cell(row=row_num, column=1, value=f"Total {title}").font = Font(bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(section.get('total',0))), bold=True, underline="thin")
            if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(section.get('comparative_total',0))), bold=True, underline="thin")
            row_num += 2
        write_section('assets', 'Assets'); write_section('liabilities', 'Liabilities'); write_section('equity', 'Equity')
        ws.cell(row=row_num, column=1, value="Total Liabilities & Equity").font = Font(bold=True, size=11)
        self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(report_data.get('total_liabilities_equity',0))), bold=True, underline="double")
        if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(report_data.get('comparative_total_liabilities_equity',0))), bold=True, underline="double")
        row_num +=1
        if report_data.get('is_balanced') is False: ws.cell(row=row_num, column=1, value="Warning: Balance Sheet out of balance!").font = Font(color="FF0000", bold=True)
        for i, col_letter in enumerate(['A','B','C'][:len(headers)]): ws.column_dimensions[col_letter].width = 45 if i==0 else 20
        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()

    async def _export_profit_loss_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Profit and Loss"; company_name = await self._get_company_name(); has_comparative = bool(report_data.get('comparative_start')); row_num = 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=company_name), size=14); row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('title')), size=12); row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')), size=10, bold=False); row_num += 2
        headers = ["Description", "Current Period"]; 
        if has_comparative: headers.append("Comparative")
        for col, header_text in enumerate(headers, 1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), alignment='center' if col>0 else 'left', fill_color="4F81BD")
        row_num +=1
        def write_pl_section(section_key: str, title: str):
            nonlocal row_num; section = report_data.get(section_key, {})
            ws.cell(row=row_num, column=1, value=title).font = Font(bold=True, size=11, color="2F5496"); row_num +=1
            for acc in section.get('accounts', []):
                ws.cell(row=row_num, column=1, value=f"  {acc['code']} - {acc['name']}")
                self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(acc['balance'] if acc.get('balance') is not None else 0)))
                if has_comparative:
                    comp_val = None
                    if section.get('comparative_accounts'):
                        comp_acc_match = next((ca for ca in section['comparative_accounts'] if ca['id'] == acc['id']), None)
                        if comp_acc_match and comp_acc_match.get('balance') is not None: comp_val = float(comp_acc_match['balance'])
                    self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=comp_val if comp_val is not None else "-"))
                row_num +=1
            ws.cell(row=row_num, column=1, value=f"Total {title}").font = Font(bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(section.get('total',0))), bold=True, underline="thin")
            if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(section.get('comparative_total',0))), bold=True, underline="thin")
            row_num +=1; return section.get('total', Decimal(0)), section.get('comparative_total') if has_comparative else Decimal(0)
        total_revenue, comp_total_revenue = write_pl_section('revenue', 'Revenue'); row_num +=1 
        total_expenses, comp_total_expenses = write_pl_section('expenses', 'Operating Expenses'); row_num +=1 
        ws.cell(row=row_num, column=1, value="Net Profit / (Loss)").font = Font(bold=True, size=11)
        self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(report_data.get('net_profit',0))), bold=True, underline="double")
        if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(report_data.get('comparative_net_profit',0))), bold=True, underline="double")
        for i, col_letter in enumerate(['A','B','C'][:len(headers)]): ws.column_dimensions[col_letter].width = 45 if i==0 else 20
        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()
    
    async def _export_trial_balance_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Trial Balance"; company_name = await self._get_company_name(); row_num = 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=4); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=company_name), size=14, alignment='center'); row_num += 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=4); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('title')), size=12, alignment='center'); row_num += 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=4); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')), size=10, bold=False, alignment='center'); row_num += 2
        headers = ["Account Code", "Account Name", "Debit", "Credit"]
        for col, header_text in enumerate(headers, 1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), fill_color="4F81BD", alignment='center' if col > 1 else 'left')
        row_num += 1
        for acc in report_data.get('debit_accounts', []): ws.cell(row=row_num, column=1, value=acc['code']); ws.cell(row=row_num, column=2, value=acc['name']); self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(acc['balance'] if acc.get('balance') is not None else 0))); ws.cell(row=row_num, column=4, value=None); row_num += 1
        for acc in report_data.get('credit_accounts', []): ws.cell(row=row_num, column=1, value=acc['code']); ws.cell(row=row_num, column=2, value=acc['name']); ws.cell(row=row_num, column=3, value=None); self._apply_excel_amount_style(ws.cell(row=row_num, column=4, value=float(acc['balance'] if acc.get('balance') is not None else 0))); row_num += 1
        row_num +=1; ws.cell(row=row_num, column=2, value="TOTALS").font = Font(bold=True); ws.cell(row=row_num, column=2).alignment = Alignment(horizontal='right')
        self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(report_data.get('total_debits', 0))), bold=True, underline="thin"); self._apply_excel_amount_style(ws.cell(row=row_num, column=4, value=float(report_data.get('total_credits', 0))), bold=True, underline="thin")
        if report_data.get('is_balanced', True) is False: row_num +=2; ws.cell(row=row_num, column=1, value="Warning: Trial Balance is out of balance!").font = Font(color="FF0000", bold=True)
        ws.column_dimensions[get_column_letter(1)].width = 15; ws.column_dimensions[get_column_letter(2)].width = 45; ws.column_dimensions[get_column_letter(3)].width = 20; ws.column_dimensions[get_column_letter(4)].width = 20
        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()

    async def _export_general_ledger_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = f"GL-{report_data.get('account_code', 'Account')}"[:30]; company_name = await self._get_company_name(); row_num = 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=7); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=company_name), size=14, alignment='center'); row_num += 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=7); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('title')), size=12, alignment='center'); row_num += 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=7); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')), size=10, bold=False, alignment='center'); row_num += 2
        headers = ["Date", "Entry No.", "JE Description", "Line Description", "Debit", "Credit", "Balance"]
        for col, header_text in enumerate(headers, 1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), fill_color="4F81BD", alignment='center' if col > 3 else 'left')
        row_num += 1
        ws.cell(row=row_num, column=4, value="Opening Balance").font = Font(bold=True); ws.cell(row=row_num, column=4).alignment = Alignment(horizontal='right'); self._apply_excel_amount_style(ws.cell(row=row_num, column=7, value=float(report_data.get('opening_balance',0))), bold=True); row_num += 1
        for txn in report_data.get('transactions', []):
            ws.cell(row=row_num, column=1, value=txn['date'].strftime('%d/%m/%Y') if isinstance(txn['date'], date) else txn['date']); ws.cell(row=row_num, column=1).alignment = Alignment(horizontal='center')
            ws.cell(row=row_num, column=2, value=txn['entry_no']); ws.cell(row=row_num, column=3, value=txn.get('je_description','')); ws.cell(row=row_num, column=4, value=txn.get('line_description',''))
            self._apply_excel_amount_style(ws.cell(row=row_num, column=5, value=float(txn['debit'] if txn['debit'] else 0))); self._apply_excel_amount_style(ws.cell(row=row_num, column=6, value=float(txn['credit'] if txn['credit'] else 0))); self._apply_excel_amount_style(ws.cell(row=row_num, column=7, value=float(txn['balance']))); row_num += 1
        ws.cell(row=row_num, column=4, value="Closing Balance").font = Font(bold=True); ws.cell(row=row_num, column=4).alignment = Alignment(horizontal='right'); self._apply_excel_amount_style(ws.cell(row=row_num, column=7, value=float(report_data.get('closing_balance',0))), bold=True, underline="thin")
        ws.column_dimensions[get_column_letter(1)].width = 12; ws.column_dimensions[get_column_letter(2)].width = 15; ws.column_dimensions[get_column_letter(3)].width = 40; ws.column_dimensions[get_column_letter(4)].width = 40
        for i in [5,6,7]: ws.column_dimensions[get_column_letter(i)].width = 18
        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()

    async def _export_tax_computation_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Tax Computation"; company_name = await self._get_company_name(); row_num = 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=2); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=company_name), size=14, alignment='center'); row_num += 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=2); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('title')), size=12, alignment='center'); row_num += 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=2); self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')), size=10, bold=False, alignment='center'); row_num += 2
        for col, header_text in enumerate(["Description", "Amount"], 1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), fill_color="4F81BD")
        row_num +=1
        ws.cell(row=row_num, column=1, value="Net Profit Before Tax").font = Font(bold=True); self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(report_data.get('net_profit_before_tax',0))), bold=True); row_num += 2
        ws.cell(row=row_num, column=1, value="Add: Non-Deductible Expenses").font = Font(bold=True, color="2F5496"); row_num +=1
        for adj in report_data.get('add_back_adjustments', []): ws.cell(row=row_num, column=1, value=f"  {adj['name']}"); self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(adj['amount']))); row_num += 1
        ws.cell(row=row_num, column=1, value="Less: Non-Taxable Income").font = Font(bold=True, color="2F5496"); row_num +=1
        for adj in report_data.get('less_adjustments', []): ws.cell(row=row_num, column=1, value=f"  {adj['name']}"); self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(adj['amount']))); row_num += 1
        row_num += 1; ws.cell(row=row_num, column=1, value="Chargeable Income").font = Font(bold=True); self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(report_data.get('chargeable_income',0))), bold=True, underline="thin"); row_num += 2
        ws.cell(row=row_num, column=1, value=f"Estimated Tax @ {report_data.get('tax_rate', 0):.2f}%").font = Font(bold=True); self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(report_data.get('estimated_tax',0))), bold=True, underline="double");
        ws.column_dimensions[get_column_letter(1)].width = 60; ws.column_dimensions[get_column_letter(2)].width = 20
        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()
        
    async def _export_gst_f5_details_to_excel(self, report_data: GSTReturnData) -> bytes:
        wb = openpyxl.Workbook()
        ws_summary = wb.active; ws_summary.title = "GST F5 Summary"; company_name = await self._get_company_name(); row_num = 1
        ws_summary.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3); self._apply_excel_header_style(ws_summary.cell(row=row_num, column=1, value=company_name), size=14); row_num += 1
        ws_summary.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3); self._apply_excel_header_style(ws_summary.cell(row=row_num, column=1, value="GST F5 Return"), size=12); row_num += 1
        ws_summary.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3); date_desc = f"For period: {report_data.start_date.strftime('%d %b %Y')} to {report_data.end_date.strftime('%d %b %Y')}"; self._apply_excel_header_style(ws_summary.cell(row=row_num, column=1, value=date_desc), size=10, bold=False); row_num += 2
        f5_boxes = [("1. Standard-Rated Supplies", report_data.standard_rated_supplies),("2. Zero-Rated Supplies", report_data.zero_rated_supplies),("3. Exempt Supplies", report_data.exempt_supplies),("4. Total Supplies (1+2+3)", report_data.total_supplies, True),("5. Taxable Purchases", report_data.taxable_purchases),("6. Output Tax Due", report_data.output_tax),("7. Input Tax and Refunds Claimed", report_data.input_tax),("8. GST Adjustments (e.g. Bad Debt Relief)", report_data.tax_adjustments),("9. Net GST Payable / (Claimable)", report_data.tax_payable, True)]
        for desc, val, *is_bold in f5_boxes: ws_summary.cell(row=row_num, column=1, value=desc).font = Font(bold=bool(is_bold and is_bold[0])); self._apply_excel_amount_style(ws_summary.cell(row=row_num, column=2, value=float(val)), bold=bool(is_bold and is_bold[0])); row_num +=1
        ws_summary.column_dimensions['A'].width = 45; ws_summary.column_dimensions['B'].width = 20
        detail_headers = ["Date", "Doc No.", "Entity", "Description", "GL Code", "GL Name", "Net Amount", "GST Amount", "Tax Code"]
        box_map_to_detail_key = {"Box 1: Std Supplies": "box1_standard_rated_supplies","Box 2: Zero Supplies": "box2_zero_rated_supplies","Box 3: Exempt Supplies": "box3_exempt_supplies","Box 5: Taxable Purchases": "box5_taxable_purchases","Box 6: Output Tax": "box6_output_tax_details","Box 7: Input Tax": "box7_input_tax_details"}
        if report_data.detailed_breakdown:
            for sheet_title_prefix, detail_key in box_map_to_detail_key.items():
                transactions: List[GSTTransactionLineDetail] = report_data.detailed_breakdown.get(detail_key, [])
                if not transactions: continue
                ws_detail = wb.create_sheet(title=sheet_title_prefix[:30]); row_num_detail = 1
                for col, header_text in enumerate(detail_headers, 1): self._apply_excel_header_style(ws_detail.cell(row=row_num_detail, column=col, value=header_text), fill_color="4F81BD")
                row_num_detail +=1
                for txn in transactions:
                    ws_detail.cell(row=row_num_detail, column=1, value=txn.transaction_date.strftime('%d/%m/%Y') if txn.transaction_date else None); ws_detail.cell(row=row_num_detail, column=2, value=txn.document_no); ws_detail.cell(row=row_num_detail, column=3, value=txn.entity_name); ws_detail.cell(row=row_num_detail, column=4, value=txn.description); ws_detail.cell(row=row_num_detail, column=5, value=txn.account_code); ws_detail.cell(row=row_num_detail, column=6, value=txn.account_name); self._apply_excel_amount_style(ws_detail.cell(row=row_num_detail, column=7, value=float(txn.net_amount))); self._apply_excel_amount_style(ws_detail.cell(row=row_num_detail, column=8, value=float(txn.gst_amount))); ws_detail.cell(row=row_num_detail, column=9, value=txn.tax_code_applied); row_num_detail += 1
                for i, col_letter in enumerate([get_column_letter(j+1) for j in range(len(detail_headers))]):
                    if i in [0,1,8]: ws_detail.column_dimensions[col_letter].width = 15
                    elif i in [2,3,4,5]: ws_detail.column_dimensions[col_letter].width = 30
                    else: ws_detail.column_dimensions[col_letter].width = 18
        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()
        
    def _export_generic_table_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        self.app_core.logger.warning(f"Using generic Excel export for report: {report_data.get('title')}")
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = report_data.get('title', "Report")[:30] # type: ignore
        row_num = 1; ws.cell(row=row_num, column=1, value=report_data.get('title')).font = Font(bold=True, size=14); row_num += 1 # type: ignore
        if report_data.get('report_date_description'): ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')).font = Font(italic=True); row_num += 1 # type: ignore
        row_num += 1; headers = report_data.get('headers', []); data_rows = report_data.get('data_rows', []) 
        if headers:
            for col, header_text in enumerate(headers,1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), fill_color="4F81BD")
            row_num +=1
        if data_rows:
            for data_item in data_rows:
                if isinstance(data_item, dict):
                    for col, header_text in enumerate(headers, 1): ws.cell(row=row_num, column=col, value=data_item.get(header_text, data_item.get(header_text.lower().replace(' ','_'))))
                elif isinstance(data_item, list):
                     for col, cell_val in enumerate(data_item, 1): ws.cell(row=row_num, column=col, value=cell_val)
                row_num +=1
        for col_idx_generic in range(1, len(headers) + 1): ws.column_dimensions[get_column_letter(col_idx_generic)].width = 20
        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()

```

# app/business_logic/bank_transaction_manager.py
```py
# File: app/business_logic/bank_transaction_manager.py
import csv 
from datetime import date, datetime 
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast, Tuple 

from sqlalchemy import select 

from app.models.business.bank_transaction import BankTransaction
from app.utils.result import Result
from app.utils.pydantic_models import (
    BankTransactionCreateData, BankTransactionSummaryData, CSVImportErrorData
)
from app.common.enums import BankTransactionTypeEnum

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.services.business_services import BankTransactionService, BankAccountService

class BankTransactionManager:
    def __init__(self,
                 bank_transaction_service: "BankTransactionService",
                 bank_account_service: "BankAccountService", 
                 app_core: "ApplicationCore"):
        self.bank_transaction_service = bank_transaction_service
        self.bank_account_service = bank_account_service
        self.app_core = app_core
        self.logger = app_core.logger

    async def _validate_transaction_data(
        self,
        dto: BankTransactionCreateData,
        existing_transaction_id: Optional[int] = None 
    ) -> List[str]:
        errors: List[str] = []
        bank_account = await self.bank_account_service.get_by_id(dto.bank_account_id)
        if not bank_account:
            errors.append(f"Bank Account with ID {dto.bank_account_id} not found.")
        elif not bank_account.is_active:
            errors.append(f"Bank Account '{bank_account.account_name}' is not active.")
        if dto.value_date and dto.value_date < dto.transaction_date:
            errors.append("Value date cannot be before transaction date.")
        return errors

    async def create_manual_bank_transaction(self, dto: BankTransactionCreateData) -> Result[BankTransaction]:
        validation_errors = await self._validate_transaction_data(dto)
        if validation_errors:
            return Result.failure(validation_errors)
        try:
            bank_transaction_orm = BankTransaction(
                bank_account_id=dto.bank_account_id,
                transaction_date=dto.transaction_date,
                value_date=dto.value_date,
                transaction_type=dto.transaction_type.value, 
                description=dto.description,
                reference=dto.reference,
                amount=dto.amount, 
                is_reconciled=False, 
                is_from_statement=False, 
                raw_statement_data=None,
                created_by_user_id=dto.user_id,
                updated_by_user_id=dto.user_id
            )
            saved_transaction = await self.bank_transaction_service.save(bank_transaction_orm)
            self.logger.info(f"Manual bank transaction ID {saved_transaction.id} created for bank account ID {dto.bank_account_id}.")
            return Result.success(saved_transaction)
        except Exception as e:
            self.logger.error(f"Error creating manual bank transaction: {e}", exc_info=True)
            return Result.failure([f"An unexpected error occurred: {str(e)}"])


    async def get_transactions_for_bank_account(
        self,
        bank_account_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transaction_type: Optional[BankTransactionTypeEnum] = None,
        is_reconciled: Optional[bool] = None,
        is_from_statement_filter: Optional[bool] = None, 
        page: int = 1,
        page_size: int = 50
    ) -> Result[List[BankTransactionSummaryData]]:
        try:
            summaries = await self.bank_transaction_service.get_all_for_bank_account(
                bank_account_id=bank_account_id,
                start_date=start_date,
                end_date=end_date,
                transaction_type=transaction_type,
                is_reconciled=is_reconciled,
                is_from_statement_filter=is_from_statement_filter, 
                page=page,
                page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching bank transactions for account ID {bank_account_id}: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve bank transaction list: {str(e)}"])

    async def get_bank_transaction_for_dialog(self, transaction_id: int) -> Optional[BankTransaction]:
        try:
            return await self.bank_transaction_service.get_by_id(transaction_id)
        except Exception as e:
            self.logger.error(f"Error fetching BankTransaction ID {transaction_id} for dialog: {e}", exc_info=True)
            return None
            
    async def import_bank_statement_csv(
        self, 
        bank_account_id: int, 
        csv_file_path: str, 
        user_id: int,
        column_mapping: Dict[str, Any], 
        import_options: Dict[str, Any]
    ) -> Result[Dict[str, Any]]:
        imported_count = 0; skipped_duplicates_count = 0; zero_amount_skipped_count = 0; total_rows_processed = 0
        detailed_errors: List[CSVImportErrorData] = []
        date_format_str = import_options.get("date_format_str", "%d/%m/%Y"); skip_header = import_options.get("skip_header", True)
        use_single_amount_col = import_options.get("use_single_amount_column", False); debit_is_negative = import_options.get("debit_is_negative_in_single_col", False)
        bank_account = await self.bank_account_service.get_by_id(bank_account_id)
        if not bank_account or not bank_account.is_active: return Result.failure([f"Bank Account ID {bank_account_id} not found or is inactive."])
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8-sig') as csvfile:
                using_header_names = any(isinstance(v, str) for v in column_mapping.values()); reader: Any
                if using_header_names: reader = csv.DictReader(csvfile)
                else: reader = csv.reader(csvfile); 
                if skip_header and not using_header_names: 
                    try: next(reader) 
                    except StopIteration: return Result.failure(["CSV file is empty or only contains a header."])
                
                async with self.app_core.db_manager.session() as session:
                    start_row_num = 2 if skip_header else 1
                    for row_num, raw_row_data in enumerate(reader, start=start_row_num):
                        total_rows_processed += 1
                        original_row_list = list(raw_row_data.values()) if isinstance(raw_row_data, dict) else raw_row_data
                        
                        def add_error(msg: str):
                            nonlocal detailed_errors
                            detailed_errors.append(CSVImportErrorData(row_number=row_num, row_data=original_row_list, error_message=msg))

                        try:
                            def get_field_value(field_key: str) -> Optional[str]:
                                specifier = column_mapping.get(field_key); 
                                if specifier is None: return None; val: Optional[str] = None
                                if using_header_names and isinstance(raw_row_data, dict): val = raw_row_data.get(str(specifier))
                                elif not using_header_names and isinstance(raw_row_data, list) and isinstance(specifier, int):
                                    if 0 <= specifier < len(raw_row_data): val = raw_row_data[specifier]
                                return val.strip() if val else None
                            
                            raw_row_dict_for_json: Dict[str, str] = {k: str(v) for k,v in raw_row_data.items()} if isinstance(raw_row_data, dict) else {f"column_{i}": str(val) for i, val in enumerate(raw_row_data)}
                            
                            transaction_date_str = get_field_value("date"); description_str = get_field_value("description")
                            if not transaction_date_str or not description_str: add_error("Skipping: Missing required Date or Description field."); continue
                            try: parsed_transaction_date = datetime.strptime(transaction_date_str, date_format_str).date()
                            except ValueError: add_error(f"Invalid transaction date format '{transaction_date_str}'. Expected '{date_format_str}'."); continue
                            
                            value_date_str = get_field_value("value_date"); parsed_value_date: Optional[date] = None
                            if value_date_str:
                                try: parsed_value_date = datetime.strptime(value_date_str, date_format_str).date()
                                except ValueError: add_error(f"Invalid value date format '{value_date_str}'. Ignored.")
                            
                            final_bt_amount = Decimal(0)
                            if use_single_amount_col:
                                amount_str = get_field_value("amount")
                                if not amount_str: add_error("Single amount column specified but value is missing."); continue
                                try: parsed_csv_amount = Decimal(amount_str.replace(',', '')); final_bt_amount = -parsed_csv_amount if debit_is_negative else parsed_csv_amount
                                except InvalidOperation: add_error(f"Invalid amount '{amount_str}' in single amount column."); continue
                            else:
                                debit_str = get_field_value("debit"); credit_str = get_field_value("credit")
                                try:
                                    parsed_debit = Decimal(debit_str.replace(',', '')) if debit_str else Decimal(0)
                                    parsed_credit = Decimal(credit_str.replace(',', '')) if credit_str else Decimal(0)
                                    final_bt_amount = parsed_credit - parsed_debit
                                except InvalidOperation: add_error(f"Invalid debit '{debit_str}' or credit '{credit_str}' amount."); continue
                            
                            if abs(final_bt_amount) < Decimal("0.005"): zero_amount_skipped_count += 1; continue
                            
                            reference_str = get_field_value("reference")
                            stmt_dup = select(BankTransaction).where(BankTransaction.bank_account_id == bank_account_id,BankTransaction.transaction_date == parsed_transaction_date,BankTransaction.amount == final_bt_amount,BankTransaction.description == description_str,BankTransaction.is_from_statement == True)
                            if (await session.execute(stmt_dup)).scalars().first(): skipped_duplicates_count += 1; continue
                            
                            txn_type_enum = BankTransactionTypeEnum.DEPOSIT if final_bt_amount > 0 else BankTransactionTypeEnum.WITHDRAWAL
                            txn_orm = BankTransaction(bank_account_id=bank_account_id,transaction_date=parsed_transaction_date,value_date=parsed_value_date,transaction_type=txn_type_enum.value,description=description_str,reference=reference_str if reference_str else None,amount=final_bt_amount,is_reconciled=False,is_from_statement=True,raw_statement_data=raw_row_dict_for_json, created_by_user_id=user_id,updated_by_user_id=user_id)
                            session.add(txn_orm); imported_count += 1
                        except Exception as e_row: add_error(f"Unexpected error: {str(e_row)}")

            summary = {"total_rows_processed": total_rows_processed, "imported_count": imported_count, "skipped_duplicates_count": skipped_duplicates_count, "failed_rows_count": len(detailed_errors), "zero_amount_skipped_count": zero_amount_skipped_count, "detailed_errors": detailed_errors}
            self.logger.info(f"Bank statement import complete for account ID {bank_account_id}: {summary}")
            return Result.success(summary)

        except FileNotFoundError: self.logger.error(f"CSV Import: File not found at path: {csv_file_path}"); return Result.failure([f"CSV file not found: {csv_file_path}"])
        except Exception as e: self.logger.error(f"CSV Import: General error for account ID {bank_account_id}: {e}", exc_info=True); return Result.failure([f"General error during CSV import: {str(e)}"])

    async def get_unreconciled_transactions_for_matching(
        self, 
        bank_account_id: int, 
        statement_end_date: date,
        page_size_override: int = -1 
    ) -> Result[Tuple[List[BankTransactionSummaryData], List[BankTransactionSummaryData]]]:
        try:
            statement_items_result = await self.get_transactions_for_bank_account(
                bank_account_id=bank_account_id, end_date=statement_end_date, 
                is_reconciled=False, is_from_statement_filter=True, page=1, page_size=page_size_override 
            )
            if not statement_items_result.is_success:
                return Result.failure(["Failed to fetch statement items for reconciliation."] + (statement_items_result.errors or []))
            
            system_items_result = await self.get_transactions_for_bank_account(
                bank_account_id=bank_account_id, end_date=statement_end_date, 
                is_reconciled=False, is_from_statement_filter=False, page=1, page_size=page_size_override
            )
            if not system_items_result.is_success:
                return Result.failure(["Failed to fetch system transactions for reconciliation."] + (system_items_result.errors or []))
            
            return Result.success((statement_items_result.value or [], system_items_result.value or []))

        except Exception as e:
            self.logger.error(f"Error fetching transactions for matching UI (Account ID: {bank_account_id}): {e}", exc_info=True)
            return Result.failure([f"Unexpected error fetching transactions for reconciliation: {str(e)}"])

```

# scripts/initial_data.sql
```sql
-- File: scripts/initial_data.sql
-- ============================================================================
-- INITIAL DATA (Version 1.0.6)
-- ============================================================================
-- Changes from 1.0.5:
-- - Added 'CorpTaxRate_Default' to core.configuration for use in tax computation reports.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- Insert default roles
-- ----------------------------------------------------------------------------
INSERT INTO core.roles (name, description) VALUES
('Administrator', 'Full system access'),
('Accountant', 'Access to accounting functions'),
('Bookkeeper', 'Basic transaction entry and reporting'),
('Manager', 'Access to reports and dashboards'),
('Viewer', 'Read-only access to data')
ON CONFLICT (name) DO UPDATE SET 
    description = EXCLUDED.description, 
    updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert default permissions
-- ----------------------------------------------------------------------------
INSERT INTO core.permissions (code, description, module) VALUES
('SYSTEM_SETTINGS', 'Manage system settings', 'System'), ('USER_MANAGE', 'Manage users', 'System'),
('ROLE_MANAGE', 'Manage roles and permissions', 'System'), ('DATA_BACKUP', 'Backup and restore data', 'System'),
('DATA_IMPORT', 'Import data', 'System'), ('DATA_EXPORT', 'Export data', 'System'),
('VIEW_AUDIT_LOG', 'View audit logs', 'System'), ('ACCOUNT_VIEW', 'View chart of accounts', 'Accounting'),
('ACCOUNT_CREATE', 'Create accounts', 'Accounting'), ('ACCOUNT_EDIT', 'Edit accounts', 'Accounting'),
('ACCOUNT_DELETE', 'Delete/deactivate accounts', 'Accounting'), ('JOURNAL_VIEW', 'View journal entries', 'Accounting'),
('JOURNAL_CREATE', 'Create journal entries', 'Accounting'), ('JOURNAL_EDIT', 'Edit draft journal entries', 'Accounting'),
('JOURNAL_POST', 'Post journal entries', 'Accounting'), ('JOURNAL_REVERSE', 'Reverse posted journal entries', 'Accounting'),
('PERIOD_MANAGE', 'Manage fiscal periods', 'Accounting'), ('YEAR_CLOSE', 'Close fiscal years', 'Accounting'),
('CUSTOMER_VIEW', 'View customers', 'Business'), ('CUSTOMER_CREATE', 'Create customers', 'Business'),
('CUSTOMER_EDIT', 'Edit customers', 'Business'), ('CUSTOMER_DELETE', 'Delete customers', 'Business'),
('VENDOR_VIEW', 'View vendors', 'Business'), ('VENDOR_CREATE', 'Create vendors', 'Business'),
('VENDOR_EDIT', 'Edit vendors', 'Business'), ('VENDOR_DELETE', 'Delete vendors', 'Business'),
('PRODUCT_VIEW', 'View products', 'Business'), ('PRODUCT_CREATE', 'Create products', 'Business'),
('PRODUCT_EDIT', 'Edit products', 'Business'), ('PRODUCT_DELETE', 'Delete products', 'Business'),
('INVOICE_VIEW', 'View invoices', 'Transactions'), ('INVOICE_CREATE', 'Create invoices', 'Transactions'),
('INVOICE_EDIT', 'Edit invoices', 'Transactions'), ('INVOICE_DELETE', 'Delete invoices', 'Transactions'),
('INVOICE_APPROVE', 'Approve invoices', 'Transactions'), ('PAYMENT_VIEW', 'View payments', 'Transactions'),
('PAYMENT_CREATE', 'Create payments', 'Transactions'), ('PAYMENT_EDIT', 'Edit payments', 'Transactions'),
('PAYMENT_DELETE', 'Delete payments', 'Transactions'), ('PAYMENT_APPROVE', 'Approve payments', 'Transactions'),
('BANK_ACCOUNT_VIEW', 'View bank accounts', 'Banking'), ('BANK_ACCOUNT_MANAGE', 'Manage bank accounts (CRUD)', 'Banking'),
('BANK_TRANSACTION_VIEW', 'View bank transactions', 'Banking'), ('BANK_TRANSACTION_MANAGE', 'Manage bank transactions (manual entry)', 'Banking'),
('BANK_RECONCILE', 'Reconcile bank accounts', 'Banking'), ('BANK_STATEMENT_IMPORT', 'Import bank statements', 'Banking'),
('TAX_VIEW', 'View tax settings', 'Tax'), ('TAX_EDIT', 'Edit tax settings', 'Tax'),
('GST_PREPARE', 'Prepare GST returns', 'Tax'), ('GST_SUBMIT', 'Mark GST returns as submitted', 'Tax'),
('TAX_REPORT', 'Generate tax reports', 'Tax'), ('REPORT_FINANCIAL', 'Access financial reports', 'Reporting'),
('REPORT_TAX', 'Access tax reports', 'Reporting'), ('REPORT_MANAGEMENT', 'Access management reports', 'Reporting'),
('REPORT_CUSTOM', 'Create custom reports', 'Reporting'), ('REPORT_EXPORT', 'Export reports', 'Reporting')
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, module = EXCLUDED.module;

-- ----------------------------------------------------------------------------
-- Insert System Init User (ID 1)
-- ----------------------------------------------------------------------------
INSERT INTO core.users (id, username, password_hash, email, full_name, is_active, require_password_change)
VALUES (1, 'system_init_user', crypt('system_init_secure_password_!PLACEHOLDER!', gen_salt('bf')), 'system_init@sgbookkeeper.com', 'System Initializer', FALSE, FALSE) 
ON CONFLICT (id) DO UPDATE SET 
    username = EXCLUDED.username, password_hash = EXCLUDED.password_hash, email = EXCLUDED.email, 
    full_name = EXCLUDED.full_name, is_active = EXCLUDED.is_active, require_password_change = EXCLUDED.require_password_change,
    updated_at = CURRENT_TIMESTAMP;

SELECT setval(pg_get_serial_sequence('core.users', 'id'), COALESCE((SELECT MAX(id) FROM core.users), 1), true);

-- ----------------------------------------------------------------------------
-- Insert default currencies
-- ----------------------------------------------------------------------------
INSERT INTO accounting.currencies (code, name, symbol, is_active, decimal_places, created_by, updated_by) VALUES
('SGD', 'Singapore Dollar', '$', TRUE, 2, 1, 1) ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, symbol = EXCLUDED.symbol, is_active = EXCLUDED.is_active, decimal_places = EXCLUDED.decimal_places, created_by = COALESCE(accounting.currencies.created_by, EXCLUDED.created_by), updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;
INSERT INTO accounting.currencies (code, name, symbol, is_active, decimal_places, created_by, updated_by) VALUES
('USD', 'US Dollar', '$', TRUE, 2, 1, 1), ('EUR', 'Euro', '€', TRUE, 2, 1, 1),
('GBP', 'British Pound', '£', TRUE, 2, 1, 1), ('AUD', 'Australian Dollar', '$', TRUE, 2, 1, 1),
('JPY', 'Japanese Yen', '¥', TRUE, 0, 1, 1), ('CNY', 'Chinese Yuan', '¥', TRUE, 2, 1, 1),
('MYR', 'Malaysian Ringgit', 'RM', TRUE, 2, 1, 1), ('IDR', 'Indonesian Rupiah', 'Rp', TRUE, 0, 1, 1)
ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, symbol = EXCLUDED.symbol, is_active = EXCLUDED.is_active, decimal_places = EXCLUDED.decimal_places, created_by = COALESCE(accounting.currencies.created_by, EXCLUDED.created_by), updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert Default Company Settings (ID = 1)
-- ----------------------------------------------------------------------------
INSERT INTO core.company_settings (id, company_name, legal_name, uen_no, gst_registration_no, gst_registered, address_line1, postal_code, city, country, fiscal_year_start_month, fiscal_year_start_day, base_currency, tax_id_label, date_format, updated_by) 
VALUES (1, 'My Demo Company Pte. Ltd.', 'My Demo Company Private Limited', '202400001Z', 'M90000001Z', TRUE, '1 Marina Boulevard', '018989', 'Singapore', 'Singapore', 1, 1, 'SGD', 'UEN', 'dd/MM/yyyy', 1)
ON CONFLICT (id) DO UPDATE SET
    company_name = EXCLUDED.company_name, legal_name = EXCLUDED.legal_name, uen_no = EXCLUDED.uen_no,
    gst_registration_no = EXCLUDED.gst_registration_no, gst_registered = EXCLUDED.gst_registered,
    address_line1 = EXCLUDED.address_line1, postal_code = EXCLUDED.postal_code, city = EXCLUDED.city, country = EXCLUDED.country,
    fiscal_year_start_month = EXCLUDED.fiscal_year_start_month, fiscal_year_start_day = EXCLUDED.fiscal_year_start_day,
    base_currency = EXCLUDED.base_currency, tax_id_label = EXCLUDED.tax_id_label, date_format = EXCLUDED.date_format,
    updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert default document sequences
-- ----------------------------------------------------------------------------
INSERT INTO core.sequences (sequence_name, prefix, next_value, format_template) VALUES
('journal_entry', 'JE', 1, '{PREFIX}{VALUE:06}'), ('sales_invoice', 'INV', 1, '{PREFIX}{VALUE:06}'),
('purchase_invoice', 'PUR', 1, '{PREFIX}{VALUE:06}'), ('payment', 'PAY', 1, '{PREFIX}{VALUE:06}'),
('receipt', 'REC', 1, '{PREFIX}{VALUE:06}'), ('customer', 'CUS', 1, '{PREFIX}{VALUE:04}'),
('vendor', 'VEN', 1, '{PREFIX}{VALUE:04}'), ('product', 'PRD', 1, '{PREFIX}{VALUE:04}'),
('wht_certificate', 'WHT', 1, '{PREFIX}{VALUE:06}')
ON CONFLICT (sequence_name) DO UPDATE SET prefix = EXCLUDED.prefix, next_value = GREATEST(core.sequences.next_value, EXCLUDED.next_value), format_template = EXCLUDED.format_template, updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert default configuration values
-- ----------------------------------------------------------------------------
INSERT INTO core.configuration (config_key, config_value, description, updated_by) VALUES
('SysAcc_DefaultAR', '1120', 'Default Accounts Receivable account code', 1),
('SysAcc_DefaultSalesRevenue', '4100', 'Default Sales Revenue account code', 1),
('SysAcc_DefaultGSTOutput', 'SYS-GST-OUTPUT', 'Default GST Output Tax account code', 1),
('SysAcc_DefaultAP', '2110', 'Default Accounts Payable account code', 1),
('SysAcc_DefaultPurchaseExpense', '5100', 'Default Purchase/COGS account code', 1),
('SysAcc_DefaultGSTInput', 'SYS-GST-INPUT', 'Default GST Input Tax account code', 1),
('SysAcc_DefaultCash', '1112', 'Default Cash on Hand account code', 1), 
('SysAcc_DefaultInventoryAsset', '1130', 'Default Inventory Asset account code', 1),
('SysAcc_DefaultCOGS', '5100', 'Default Cost of Goods Sold account code', 1),
('SysAcc_GSTControl', 'SYS-GST-CONTROL', 'GST Control/Clearing Account', 1),
('CorpTaxRate_Default', '17.00', 'Default Corporate Tax Rate (%)', 1) -- NEW
ON CONFLICT (config_key) DO UPDATE SET
    config_value = EXCLUDED.config_value, description = EXCLUDED.description,
    updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert account types
-- ----------------------------------------------------------------------------
INSERT INTO accounting.account_types (name, category, is_debit_balance, report_type, display_order, description) VALUES
('Current Asset', 'Asset', TRUE, 'Balance Sheet', 10, 'Assets expected to be converted to cash within one year'),
('Fixed Asset', 'Asset', TRUE, 'Balance Sheet', 20, 'Long-term tangible assets'),
('Other Asset', 'Asset', TRUE, 'Balance Sheet', 30, 'Assets that don''t fit in other categories'),
('Current Liability', 'Liability', FALSE, 'Balance Sheet', 40, 'Obligations due within one year'),
('Long-term Liability', 'Liability', FALSE, 'Balance Sheet', 50, 'Obligations due beyond one year'),
('Equity', 'Equity', FALSE, 'Balance Sheet', 60, 'Owner''s equity and retained earnings'),
('Revenue', 'Revenue', FALSE, 'Income Statement', 70, 'Income from business operations'),
('Cost of Sales', 'Expense', TRUE, 'Income Statement', 80, 'Direct costs of goods sold'),
('Expense', 'Expense', TRUE, 'Income Statement', 90, 'General business expenses'),
('Other Income', 'Revenue', FALSE, 'Income Statement', 100, 'Income from non-core activities'),
('Other Expense', 'Expense', TRUE, 'Income Statement', 110, 'Expenses from non-core activities')
ON CONFLICT (name) DO UPDATE SET
    category = EXCLUDED.category, is_debit_balance = EXCLUDED.is_debit_balance, report_type = EXCLUDED.report_type,
    display_order = EXCLUDED.display_order, description = EXCLUDED.description, updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Ensure key GL accounts for system configuration exist
-- ----------------------------------------------------------------------------
INSERT INTO accounting.accounts (code, name, account_type, sub_type, created_by, updated_by, is_active, is_control_account, is_bank_account) VALUES
('1120', 'Accounts Receivable Control', 'Asset', 'Accounts Receivable', 1, 1, TRUE, TRUE, FALSE),
('2110', 'Accounts Payable Control', 'Liability', 'Accounts Payable', 1, 1, TRUE, TRUE, FALSE),
('4100', 'General Sales Revenue', 'Revenue', 'Sales', 1, 1, TRUE, FALSE, FALSE),
('5100', 'General Cost of Goods Sold', 'Expense', 'Cost of Sales', 1, 1, TRUE, FALSE, FALSE),
('SYS-GST-OUTPUT', 'System GST Output Tax', 'Liability', 'GST Payable', 1, 1, TRUE, FALSE, FALSE),
('SYS-GST-INPUT', 'System GST Input Tax', 'Asset', 'GST Receivable', 1, 1, TRUE, FALSE, FALSE),
('SYS-GST-CONTROL', 'System GST Control', 'Liability', 'GST Payable', 1, 1, TRUE, TRUE, FALSE),
('1112', 'Cash on Hand', 'Asset', 'Cash and Cash Equivalents', 1,1, TRUE, FALSE, FALSE),
('1130', 'Inventory Asset Control', 'Asset', 'Inventory', 1,1,TRUE, TRUE, FALSE)
ON CONFLICT (code) DO NOTHING;

-- ----------------------------------------------------------------------------
-- Insert default tax codes (GST updated to 9%)
-- ----------------------------------------------------------------------------
INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id)
SELECT 'SR', 'Standard Rate (9%)', 'GST', 9.00, TRUE, TRUE, 1, 1, acc.id FROM accounting.accounts acc WHERE acc.code = 'SYS-GST-OUTPUT'
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, tax_type = EXCLUDED.tax_type, rate = EXCLUDED.rate, is_default = EXCLUDED.is_default, is_active = EXCLUDED.is_active, updated_by = EXCLUDED.updated_by, affects_account_id = EXCLUDED.affects_account_id, updated_at = CURRENT_TIMESTAMP;
INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('ZR', 'Zero Rate', 'GST', 0.00, FALSE, TRUE, 1, 1, NULL) ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;
INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('ES', 'Exempt Supply', 'GST', 0.00, FALSE, TRUE, 1, 1, NULL) ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;
INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('OP', 'Out of Scope', 'GST', 0.00, FALSE, TRUE, 1, 1, NULL) ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;
INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id)
SELECT 'TX', 'Taxable Purchase (9%)', 'GST', 9.00, FALSE, TRUE, 1, 1, acc.id FROM accounting.accounts acc WHERE acc.code = 'SYS-GST-INPUT'
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, tax_type = EXCLUDED.tax_type, rate = EXCLUDED.rate, is_default = EXCLUDED.is_default, is_active = EXCLUDED.is_active, updated_by = EXCLUDED.updated_by, affects_account_id = EXCLUDED.affects_account_id, updated_at = CURRENT_TIMESTAMP;
INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('BL', 'Blocked Input Tax (9%)', 'GST', 9.00, FALSE, TRUE, 1, 1, NULL) ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, rate = EXCLUDED.rate, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;
INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('NR', 'Non-Resident Services', 'Withholding Tax', 15.00, FALSE, TRUE, 1, 1, NULL) ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;
INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('ND', 'Non-Deductible', 'Income Tax', 0.00, FALSE, TRUE, 1, 1, NULL) ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;
INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('CA', 'Capital Allowance', 'Income Tax', 0.00, FALSE, TRUE, 1, 1, NULL) ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Create an active 'admin' user for application login
-- ----------------------------------------------------------------------------
INSERT INTO core.users (username, password_hash, email, full_name, is_active, require_password_change)
VALUES ('admin', crypt('password', gen_salt('bf')), 'admin@sgbookkeeper.com', 'Administrator', TRUE, TRUE)
ON CONFLICT (username) DO UPDATE SET
    password_hash = EXCLUDED.password_hash, email = EXCLUDED.email, full_name = EXCLUDED.full_name,
    is_active = EXCLUDED.is_active, require_password_change = EXCLUDED.require_password_change,
    updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Assign 'Administrator' role to 'admin' user
-- ----------------------------------------------------------------------------
WITH admin_user_id_cte AS (SELECT id FROM core.users WHERE username = 'admin'),
     admin_role_id_cte AS (SELECT id FROM core.roles WHERE name = 'Administrator')
INSERT INTO core.user_roles (user_id, role_id, created_at)
SELECT admin_user_id_cte.id, admin_role_id_cte.id, CURRENT_TIMESTAMP FROM admin_user_id_cte, admin_role_id_cte
WHERE admin_user_id_cte.id IS NOT NULL AND admin_role_id_cte.id IS NOT NULL
ON CONFLICT (user_id, role_id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- For all permissions, grant them to the 'Administrator' role
-- ----------------------------------------------------------------------------
INSERT INTO core.role_permissions (role_id, permission_id, created_at)
SELECT r.id, p.id, CURRENT_TIMESTAMP
FROM core.roles r, core.permissions p
WHERE r.name = 'Administrator'
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- Grant Privileges to Application User (sgbookkeeper_user)
-- ----------------------------------------------------------------------------
GRANT USAGE ON SCHEMA core, accounting, business, audit TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA accounting TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA business TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA audit TO sgbookkeeper_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA core TO sgbookkeeper_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA accounting TO sgbookkeeper_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA business TO sgbookkeeper_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA audit TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA core TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA accounting TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA business TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA audit TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA core GRANT ALL ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA accounting GRANT ALL ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA business GRANT ALL ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA audit GRANT ALL ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA core GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA accounting GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA business GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA audit GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;

COMMIT; 

```

