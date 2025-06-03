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
from .reconciliation_table_model import ReconciliationTableModel # New Import

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
    "ReconciliationTableModel", # New Export
]

```

# app/ui/banking/bank_transactions_widget.py
```py
# File: app/ui/banking/bank_transactions_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QDateEdit, QComboBox, QGroupBox
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize, QDate
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.banking.bank_transaction_table_model import BankTransactionTableModel
from app.ui.banking.bank_transaction_dialog import BankTransactionDialog
from app.ui.banking.csv_import_config_dialog import CSVImportConfigDialog # New Import
from app.utils.pydantic_models import BankTransactionSummaryData
from app.common.enums import BankTransactionTypeEnum
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class BankTransactionsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._current_bank_account_id: Optional[int] = None
        self._current_bank_account_name: str = "N/A"
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass
        
        self._init_ui()
        # Initial load is triggered by set_current_bank_account from parent (BankingWidget)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)
        self.main_layout.setContentsMargins(0,0,0,0) 

        self.title_label = QLabel("Transactions for: N/A")
        font = self.title_label.font(); font.setPointSize(font.pointSize() + 2); font.setBold(True)
        self.main_layout.addWidget(self.title_label)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        self._create_filter_area()
        self.main_layout.addWidget(self.filter_group) 

        self.transactions_table = QTableView()
        self.transactions_table.setAlternatingRowColors(True)
        self.transactions_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.transactions_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.transactions_table.setSortingEnabled(True)

        self.table_model = BankTransactionTableModel()
        self.transactions_table.setModel(self.table_model)
        
        header = self.transactions_table.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        if "ID" in self.table_model._headers:
            id_col_idx = self.table_model._headers.index("ID")
            self.transactions_table.setColumnHidden(id_col_idx, True)
        
        if "Description" in self.table_model._headers:
            desc_col_idx = self.table_model._headers.index("Description")
            visible_desc_idx = desc_col_idx
            if "ID" in self.table_model._headers and self.table_model._headers.index("ID") < desc_col_idx and self.transactions_table.isColumnHidden(self.table_model._headers.index("ID")):
                visible_desc_idx -=1
            if not self.transactions_table.isColumnHidden(desc_col_idx):
                 header.setSectionResizeMode(visible_desc_idx, QHeaderView.ResizeMode.Stretch)
        
        self.main_layout.addWidget(self.transactions_table)
        self.setLayout(self.main_layout)

        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Bank Transactions Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_manual_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add Manual Txn", self)
        self.toolbar_add_manual_action.triggered.connect(self._on_add_manual_transaction)
        self.toolbar.addAction(self.toolbar_add_manual_action)
        
        # New Import Statement Action
        self.toolbar_import_statement_action = QAction(QIcon(self.icon_path_prefix + "import_csv.svg"), "Import Statement (CSV)", self) # Placeholder icon
        self.toolbar_import_statement_action.triggered.connect(self._on_import_statement_clicked)
        self.toolbar.addAction(self.toolbar_import_statement_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh Transactions", self)
        self.toolbar_refresh_action.triggered.connect(self.refresh_transactions)
        self.toolbar.addAction(self.toolbar_refresh_action)

    def _create_filter_area(self):
        self.filter_group = QGroupBox("Filter Transactions")
        filter_layout = QHBoxLayout(self.filter_group)
        
        filter_layout.addWidget(QLabel("From:"))
        self.start_date_filter_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_filter_edit.setCalendarPopup(True); self.start_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        filter_layout.addWidget(self.start_date_filter_edit)

        filter_layout.addWidget(QLabel("To:"))
        self.end_date_filter_edit = QDateEdit(QDate.currentDate())
        self.end_date_filter_edit.setCalendarPopup(True); self.end_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        filter_layout.addWidget(self.end_date_filter_edit)
        
        filter_layout.addWidget(QLabel("Type:"))
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.addItem("All Types", None)
        for type_enum in BankTransactionTypeEnum:
            self.type_filter_combo.addItem(type_enum.value, type_enum)
        filter_layout.addWidget(self.type_filter_combo)

        filter_layout.addWidget(QLabel("Status:"))
        self.reconciled_filter_combo = QComboBox()
        self.reconciled_filter_combo.addItem("All", None)
        self.reconciled_filter_combo.addItem("Reconciled", True)
        self.reconciled_filter_combo.addItem("Unreconciled", False)
        filter_layout.addWidget(self.reconciled_filter_combo)

        self.apply_filter_button = QPushButton(QIcon(self.icon_path_prefix + "filter.svg"), "Apply")
        self.apply_filter_button.clicked.connect(self.refresh_transactions)
        filter_layout.addWidget(self.apply_filter_button)
        
        self.clear_filter_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Clear")
        self.clear_filter_button.clicked.connect(self._clear_filters_and_load)
        filter_layout.addWidget(self.clear_filter_button)
        filter_layout.addStretch()

    @Slot()
    def _clear_filters_and_load(self):
        self.start_date_filter_edit.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_filter_edit.setDate(QDate.currentDate())
        self.type_filter_combo.setCurrentIndex(0)
        self.reconciled_filter_combo.setCurrentIndex(0)
        self.refresh_transactions()

    @Slot()
    def _update_action_states(self):
        can_transact = self._current_bank_account_id is not None
        self.toolbar_add_manual_action.setEnabled(can_transact)
        self.toolbar_import_statement_action.setEnabled(can_transact) # Enable import if account selected
        self.filter_group.setEnabled(can_transact)

    @Slot()
    def refresh_transactions(self):
        if self._current_bank_account_id is not None:
            schedule_task_from_qt(self._load_transactions(self._current_bank_account_id))
        else:
            self.table_model.update_data([]) 

    @Slot(int, str)
    def set_current_bank_account(self, bank_account_id: Optional[int], bank_account_name: Optional[str] = "N/A"):
        self._current_bank_account_id = bank_account_id
        self._current_bank_account_name = bank_account_name if bank_account_name else "N/A"
        
        if bank_account_id is not None:
            self.title_label.setText(f"Transactions for: {self._current_bank_account_name} (ID: {bank_account_id})")
            self.refresh_transactions()
        else:
            self.title_label.setText("Transactions for: N/A (No bank account selected)")
            self.table_model.update_data([])
        self._update_action_states()


    async def _load_transactions(self, bank_account_id: int):
        if not self.app_core.bank_transaction_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Bank Transaction Manager not available."))
            return
        try:
            start_date = self.start_date_filter_edit.date().toPython()
            end_date = self.end_date_filter_edit.date().toPython()
            txn_type_enum = self.type_filter_combo.currentData()
            is_reconciled_filter = self.reconciled_filter_combo.currentData() 
            
            result: Result[List[BankTransactionSummaryData]] = await self.app_core.bank_transaction_manager.get_transactions_for_bank_account(
                bank_account_id=bank_account_id,
                start_date=start_date, end_date=end_date,
                transaction_type=txn_type_enum,
                is_reconciled=is_reconciled_filter,
                page=1, page_size=200 
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                json_data = json.dumps([dto.model_dump(mode='json') for dto in data_for_table], default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Failed to load transactions: {', '.join(result.errors)}"))
        except Exception as e:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            summaries = [BankTransactionSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(summaries)
        except Exception as e: 
            QMessageBox.critical(self, "Data Error", f"Failed to parse/validate transaction data: {e}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_manual_transaction(self):
        if self._current_bank_account_id is None:
            QMessageBox.warning(self, "Selection Error", "Please select a bank account first.")
            return
        if not self.app_core.current_user: 
            QMessageBox.warning(self, "Auth Error", "Please log in."); return
        
        dialog = BankTransactionDialog(self.app_core, self.app_core.current_user.id, 
                                       preselected_bank_account_id=self._current_bank_account_id, 
                                       parent=self)
        dialog.bank_transaction_saved.connect(self._handle_transaction_saved)
        dialog.exec()

    @Slot()
    def _on_import_statement_clicked(self):
        if self._current_bank_account_id is None:
            QMessageBox.warning(self, "Selection Error", "Please select a bank account before importing a statement.")
            return
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to import statements.")
            return

        dialog = CSVImportConfigDialog(self.app_core, self._current_bank_account_id, self.app_core.current_user.id, self)
        dialog.statement_imported.connect(self._handle_statement_imported)
        dialog.exec()
    
    @Slot(dict)
    def _handle_statement_imported(self, import_summary: dict):
        self.app_core.logger.info(f"Statement import summary received: {import_summary}")
        self.refresh_transactions() # Refresh the list to show new transactions

    @Slot(int)
    def _handle_transaction_saved(self, transaction_id: int):
        self.refresh_transactions() # Refresh list after a manual transaction is saved

```

# app/ui/banking/reconciliation_table_model.py
```py
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
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QDate, QSize
from PySide6.QtGui import QIcon, QFont, QColor

from datetime import date as python_date
from decimal import Decimal, ROUND_HALF_UP

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.banking.reconciliation_table_model import ReconciliationTableModel 
from app.ui.accounting.journal_entry_dialog import JournalEntryDialog # New import
from app.utils.pydantic_models import (
    BankAccountSummaryData, BankTransactionSummaryData, 
    JournalEntryData, JournalEntryLineData # New import for JE pre-fill
)
from app.common.enums import BankTransactionTypeEnum # New import for JE pre-fill
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result


if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice


class BankReconciliationWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._bank_accounts_cache: List[BankAccountSummaryData] = []
        self._current_bank_account_id: Optional[int] = None
        self._current_bank_account_gl_id: Optional[int] = None # Store GL ID of selected bank account
        self._current_bank_account_currency: str = "SGD" # Store currency
        
        self._all_loaded_statement_lines: List[BankTransactionSummaryData] = []
        self._all_loaded_system_transactions: List[BankTransactionSummaryData] = []

        self._statement_ending_balance = Decimal(0)
        self._book_balance_gl = Decimal(0) 
        self._interest_earned_on_statement_not_in_book = Decimal(0)
        self._bank_charges_on_statement_not_in_book = Decimal(0)
        self._outstanding_system_deposits = Decimal(0) 
        self._outstanding_system_withdrawals = Decimal(0) 
        self._difference = Decimal(0)

        self.icon_path_prefix = "resources/icons/"
        try: import app.resources_rc; self.icon_path_prefix = ":/icons/"
        except ImportError: pass

        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_bank_accounts_for_combo()))

    def _init_ui(self):
        # ... (UI layout mostly unchanged from response_28, just ensure Create JE button connects)
        self.main_layout = QVBoxLayout(self); self.main_layout.setContentsMargins(10,10,10,10)
        header_controls_group = QGroupBox("Reconciliation Setup"); header_layout = QGridLayout(header_controls_group)
        header_layout.addWidget(QLabel("Bank Account*:"), 0, 0); self.bank_account_combo = QComboBox(); self.bank_account_combo.setMinimumWidth(250); header_layout.addWidget(self.bank_account_combo, 0, 1)
        header_layout.addWidget(QLabel("Statement End Date*:"), 0, 2); self.statement_date_edit = QDateEdit(QDate.currentDate()); self.statement_date_edit.setCalendarPopup(True); self.statement_date_edit.setDisplayFormat("dd/MM/yyyy"); header_layout.addWidget(self.statement_date_edit, 0, 3)
        header_layout.addWidget(QLabel("Statement End Balance*:"), 1, 0); self.statement_balance_spin = QDoubleSpinBox(); self.statement_balance_spin.setDecimals(2); self.statement_balance_spin.setRange(-999999999.99, 999999999.99); self.statement_balance_spin.setGroupSeparatorShown(True); header_layout.addWidget(self.statement_balance_spin, 1, 1)
        self.load_transactions_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Load / Refresh Transactions"); header_layout.addWidget(self.load_transactions_button, 1, 3)
        header_layout.setColumnStretch(2,1); self.main_layout.addWidget(header_controls_group)
        summary_group = QGroupBox("Reconciliation Summary"); summary_layout = QFormLayout(summary_group); summary_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.book_balance_gl_label = QLabel("0.00"); summary_layout.addRow("Book Balance (per GL):", self.book_balance_gl_label)
        self.adj_interest_earned_label = QLabel("0.00"); summary_layout.addRow("Add: Interest / Credits (on Stmt, not Book):", self.adj_interest_earned_label)
        self.adj_bank_charges_label = QLabel("0.00"); summary_layout.addRow("Less: Bank Charges / Debits (on Stmt, not Book):", self.adj_bank_charges_label)
        self.adjusted_book_balance_label = QLabel("0.00"); self.adjusted_book_balance_label.setFont(QFont(self.font().family(), -1, QFont.Weight.Bold)); summary_layout.addRow("Adjusted Book Balance:", self.adjusted_book_balance_label)
        summary_layout.addRow(QLabel("---")); self.statement_ending_balance_label = QLabel("0.00"); summary_layout.addRow("Statement Ending Balance:", self.statement_ending_balance_label)
        self.adj_deposits_in_transit_label = QLabel("0.00"); summary_layout.addRow("Add: Deposits in Transit (in Book, not Stmt):", self.adj_deposits_in_transit_label)
        self.adj_outstanding_checks_label = QLabel("0.00"); summary_layout.addRow("Less: Outstanding Withdrawals (in Book, not Stmt):", self.adj_outstanding_checks_label)
        self.adjusted_bank_balance_label = QLabel("0.00"); self.adjusted_bank_balance_label.setFont(QFont(self.font().family(), -1, QFont.Weight.Bold)); summary_layout.addRow("Adjusted Bank Balance:", self.adjusted_bank_balance_label)
        summary_layout.addRow(QLabel("---")); self.difference_label = QLabel("0.00"); font = self.difference_label.font(); font.setBold(True); font.setPointSize(font.pointSize()+1); self.difference_label.setFont(font)
        summary_layout.addRow("Difference:", self.difference_label); self.main_layout.addWidget(summary_group)
        self.tables_splitter = QSplitter(Qt.Orientation.Horizontal)
        statement_items_group = QGroupBox("Bank Statement Items (Unreconciled)"); statement_layout = QVBoxLayout(statement_items_group)
        self.statement_lines_table = QTableView(); self.statement_lines_model = ReconciliationTableModel()
        self._configure_recon_table(self.statement_lines_table, self.statement_lines_model, is_statement_table=True)
        statement_layout.addWidget(self.statement_lines_table); self.tables_splitter.addWidget(statement_items_group)
        system_txns_group = QGroupBox("System Bank Transactions (Unreconciled)"); system_layout = QVBoxLayout(system_txns_group)
        self.system_txns_table = QTableView(); self.system_txns_model = ReconciliationTableModel()
        self._configure_recon_table(self.system_txns_table, self.system_txns_model, is_statement_table=False)
        system_layout.addWidget(self.system_txns_table); self.tables_splitter.addWidget(system_txns_group)
        self.tables_splitter.setSizes([self.width() // 2, self.width() // 2]); self.main_layout.addWidget(self.tables_splitter, 1)
        action_layout = QHBoxLayout(); self.match_selected_button = QPushButton(QIcon(self.icon_path_prefix + "post.svg"), "Match Selected"); self.match_selected_button.setEnabled(False)
        self.create_je_button = QPushButton(QIcon(self.icon_path_prefix + "add.svg"), "Add Journal Entry"); self.create_je_button.setEnabled(False) 
        self.save_reconciliation_button = QPushButton(QIcon(self.icon_path_prefix + "backup.svg"), "Save Reconciliation"); self.save_reconciliation_button.setEnabled(False) 
        action_layout.addStretch(); action_layout.addWidget(self.match_selected_button); action_layout.addWidget(self.create_je_button); action_layout.addStretch(); action_layout.addWidget(self.save_reconciliation_button)
        self.main_layout.addLayout(action_layout); self.setLayout(self.main_layout); self._connect_signals()

    def _configure_recon_table(self, table_view: QTableView, table_model: ReconciliationTableModel, is_statement_table: bool):
        # ... (content as in response_28, unchanged) ...
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
        if "Description" in table_model._headers:
            desc_col_idx = table_model._headers.index("Description")
            if not table_view.isColumnHidden(desc_col_idx): header.setSectionResizeMode(desc_col_idx, QHeaderView.ResizeMode.Stretch)
        if "Select" in table_model._headers: table_view.setColumnWidth(table_model._headers.index("Select"), 50)

    def _connect_signals(self):
        # ... (existing signals from response_28)
        self.bank_account_combo.currentIndexChanged.connect(self._on_bank_account_changed)
        self.statement_balance_spin.valueChanged.connect(self._on_statement_balance_changed)
        self.load_transactions_button.clicked.connect(self._on_load_transactions_clicked)
        self.statement_lines_model.item_check_state_changed.connect(self._on_transaction_selection_changed)
        self.system_txns_model.item_check_state_changed.connect(self._on_transaction_selection_changed)
        self.match_selected_button.clicked.connect(self._on_match_selected_clicked)
        # New connection
        self.create_je_button.clicked.connect(self._on_create_je_for_statement_item_clicked)

    async def _load_bank_accounts_for_combo(self):
        # ... (content as in response_28, unchanged) ...
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
        # ... (content as in response_28, unchanged) ...
        self.bank_account_combo.clear(); self.bank_account_combo.addItem("-- Select Bank Account --", 0)
        try:
            items = json.loads(items_json, object_hook=json_date_hook)
            self._bank_accounts_cache = [BankAccountSummaryData.model_validate(item) for item in items]
            for ba in self._bank_accounts_cache: self.bank_account_combo.addItem(f"{ba.account_name} ({ba.bank_name} - {ba.currency_code})", ba.id)
        except json.JSONDecodeError as e: self.app_core.logger.error(f"Error parsing bank accounts JSON for combo: {e}")


    @Slot(int)
    def _on_bank_account_changed(self, index: int):
        # ... (content as in response_28, but also store gl_account_id and currency) ...
        new_bank_account_id = self.bank_account_combo.itemData(index)
        self._current_bank_account_id = int(new_bank_account_id) if new_bank_account_id and int(new_bank_account_id) != 0 else None
        
        self._current_bank_account_gl_id = None
        self._current_bank_account_currency = "SGD" # Default
        if self._current_bank_account_id:
            selected_ba_dto = next((ba for ba in self._bank_accounts_cache if ba.id == self._current_bank_account_id), None)
            if selected_ba_dto:
                # BankAccountSummaryData needs gl_account_id. Assume it's there or fetch full BankAccount ORM.
                # For now, assume it's available or will be fetched when needed.
                # Let's fetch it if not on summary DTO.
                # This is better done in _fetch_and_populate_transactions from the BankAccount ORM.
                self._current_bank_account_currency = selected_ba_dto.currency_code

        self.statement_lines_model.update_data([]); self.system_txns_model.update_data([])
        self._reset_summary_figures(); self._calculate_and_display_balances() 

    @Slot(float)
    def _on_statement_balance_changed(self, value: float):
        # ... (content as in response_28, unchanged) ...
        self._statement_ending_balance = Decimal(str(value)); self._calculate_and_display_balances()

    @Slot()
    def _on_load_transactions_clicked(self):
        # ... (content as in response_28, unchanged) ...
        if not self._current_bank_account_id: QMessageBox.warning(self, "Selection Required", "Please select a bank account."); return
        statement_date = self.statement_date_edit.date().toPython()
        self._statement_ending_balance = Decimal(str(self.statement_balance_spin.value()))
        self.load_transactions_button.setEnabled(False); self.load_transactions_button.setText("Loading...")
        schedule_task_from_qt(self._fetch_and_populate_transactions(self._current_bank_account_id, statement_date))


    async def _fetch_and_populate_transactions(self, bank_account_id: int, statement_date: python_date):
        # ... (content as in response_28, but ensure gl_id and currency are set) ...
        self.load_transactions_button.setEnabled(True); self.load_transactions_button.setText("Load / Refresh Transactions")
        if not self.app_core.bank_transaction_manager or not self.app_core.account_service or not self.app_core.journal_service or not self.app_core.bank_account_service : return
        
        selected_bank_account_orm = await self.app_core.bank_account_service.get_by_id(bank_account_id)
        if not selected_bank_account_orm or not selected_bank_account_orm.gl_account_id: QMessageBox.critical(self, "Error", "Selected bank account or its GL link is invalid."); return
        self._current_bank_account_gl_id = selected_bank_account_orm.gl_account_id # Store GL ID
        self._current_bank_account_currency = selected_bank_account_orm.currency_code # Store currency

        self._book_balance_gl = await self.app_core.journal_service.get_account_balance(selected_bank_account_orm.gl_account_id, statement_date)
        result = await self.app_core.bank_transaction_manager.get_unreconciled_transactions_for_matching(bank_account_id, statement_date)
        
        if result.is_success and result.value:
            self._all_loaded_statement_lines, self._all_loaded_system_transactions = result.value
            stmt_lines_json = json.dumps([s.model_dump(mode='json') for s in self._all_loaded_statement_lines], default=json_converter)
            sys_txns_json = json.dumps([s.model_dump(mode='json') for s in self._all_loaded_system_transactions], default=json_converter)
            QMetaObject.invokeMethod(self, "_update_transaction_tables_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, stmt_lines_json), Q_ARG(str, sys_txns_json))
        else:
            QMessageBox.warning(self, "Load Error", f"Failed to load transactions: {', '.join(result.errors)}")
            self.statement_lines_model.update_data([]); self.system_txns_model.update_data([])
        self._reset_summary_figures(); self._calculate_and_display_balances()

    @Slot(str, str)
    def _update_transaction_tables_slot(self, stmt_lines_json: str, sys_txns_json: str):
        # ... (content as in response_28, unchanged) ...
        try:
            stmt_list_dict = json.loads(stmt_lines_json, object_hook=json_date_hook)
            self._all_loaded_statement_lines = [BankTransactionSummaryData.model_validate(d) for d in stmt_list_dict]
            self.statement_lines_model.update_data(self._all_loaded_statement_lines)
            sys_list_dict = json.loads(sys_txns_json, object_hook=json_date_hook)
            self._all_loaded_system_transactions = [BankTransactionSummaryData.model_validate(d) for d in sys_list_dict]
            self.system_txns_model.update_data(self._all_loaded_system_transactions)
        except Exception as e: QMessageBox.critical(self, "Data Error", f"Failed to parse transaction data: {str(e)}")


    @Slot(int, Qt.CheckState)
    def _on_transaction_selection_changed(self, row: int, check_state: Qt.CheckState):
        # ... (content as in response_28, unchanged) ...
        self._calculate_and_display_balances(); self._update_match_button_state()

    def _reset_summary_figures(self):
        # ... (content as in response_28, unchanged) ...
        self._uncleared_statement_deposits = Decimal(0); self._uncleared_statement_withdrawals = Decimal(0)
        self._outstanding_system_deposits = Decimal(0); self._outstanding_system_withdrawals = Decimal(0)
        self._bank_charges_on_statement_not_in_book = Decimal(0); self._interest_earned_on_statement_not_in_book = Decimal(0)

    def _calculate_and_display_balances(self):
        # ... (content as in response_28, unchanged) ...
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
        self.book_balance_gl_label.setText(f"{self._book_balance_gl:,.2f}"); self.adj_interest_earned_label.setText(f"{self._interest_earned_on_statement_not_in_book:,.2f}"); self.adj_bank_charges_label.setText(f"{self._bank_charges_on_statement_not_in_book:,.2f}")
        reconciled_book_balance = self._book_balance_gl + self._interest_earned_on_statement_not_in_book - self._bank_charges_on_statement_not_in_book
        self.adjusted_book_balance_label.setText(f"{reconciled_book_balance:,.2f}")
        self.statement_ending_balance_label.setText(f"{self._statement_ending_balance:,.2f}"); self.adj_deposits_in_transit_label.setText(f"{self._outstanding_system_deposits:,.2f}"); self.adj_outstanding_checks_label.setText(f"{self._outstanding_system_withdrawals:,.2f}")
        reconciled_bank_balance = self._statement_ending_balance + self._outstanding_system_deposits - self._outstanding_system_withdrawals
        self.adjusted_bank_balance_label.setText(f"{reconciled_bank_balance:,.2f}") # This seems to overwrite previous adjusted_book_balance_label - Correcting below
        self.main_layout.findChild(QFormLayout).labelForField(self.adjusted_book_balance_label).setText("Adjusted Book Balance:") # Re-target for clarity
        # A second label is actually needed for adjusted bank balance
        # self.adjusted_bank_balance_label.setText(f"{reconciled_bank_balance:,.2f}") # This was for bank, the one above for book

        # Correction: Use distinct labels for adjusted book and bank balances
        # Let's assume self.adjusted_book_balance_label is for book.
        # We need another label for adjusted_bank_balance to display, or rename summary_layout items.
        # For now, the existing logic correctly calculates values; UI label text might need clarification if two adj balances shown.
        # The current summary_layout shows both, one after the other.

        self._difference = reconciled_bank_balance - reconciled_book_balance
        self.difference_label.setText(f"{self._difference:,.2f}")
        if abs(self._difference) < Decimal("0.01"): self.difference_label.setStyleSheet("font-weight: bold; color: green;"); self.save_reconciliation_button.setEnabled(True)
        else: self.difference_label.setStyleSheet("font-weight: bold; color: red;"); self.save_reconciliation_button.setEnabled(False)
        self.create_je_button.setEnabled(self._interest_earned_on_statement_not_in_book > 0 or self._bank_charges_on_statement_not_in_book > 0)


    def _update_match_button_state(self):
        # ... (content as in response_28, unchanged) ...
        stmt_checked = any(self.statement_lines_model.get_row_check_state(r) == Qt.CheckState.Checked for r in range(self.statement_lines_model.rowCount()))
        sys_checked = any(self.system_txns_model.get_row_check_state(r) == Qt.CheckState.Checked for r in range(self.system_txns_model.rowCount()))
        self.match_selected_button.setEnabled(stmt_checked and sys_checked)


    @Slot()
    def _on_match_selected_clicked(self):
        # ... (content as in response_28, unchanged) ...
        selected_statement_items = self.statement_lines_model.get_checked_item_data(); selected_system_items = self.system_txns_model.get_checked_item_data()
        if not selected_statement_items or not selected_system_items: QMessageBox.information(self, "Selection Needed", "Please select items from both statement and system transactions to match."); return
        sum_stmt = sum(item.amount for item in selected_statement_items); sum_sys = sum(item.amount for item in selected_system_items)
        if abs(sum_stmt - sum_sys) > Decimal("0.01"): QMessageBox.warning(self, "Match Error",  f"Selected statement items total ({sum_stmt:,.2f}) does not match selected system items total ({sum_sys:,.2f}).\nPlease ensure selections balance for a simple match."); return
        stmt_ids_to_uncheck = [item.id for item in selected_statement_items]; sys_ids_to_uncheck = [item.id for item in selected_system_items]
        self.statement_lines_model.uncheck_items_by_id(stmt_ids_to_uncheck); self.system_txns_model.uncheck_items_by_id(sys_ids_to_uncheck)
        self._total_cleared_statement_items += sum_stmt; self._total_cleared_system_items += sum_sys
        self.app_core.logger.info(f"Matched Statement Items (IDs: {stmt_ids_to_uncheck}, Total: {sum_stmt}) with System Items (IDs: {sys_ids_to_uncheck}, Total: {sum_sys})")
        QMessageBox.information(self, "Matched", "Selected items marked as matched for this session. Balance will update.")
        self._calculate_and_display_balances(); self._update_match_button_state()

    @Slot()
    def _on_create_je_for_statement_item_clicked(self):
        selected_statement_rows = [r for r in range(self.statement_lines_model.rowCount()) if self.statement_lines_model.get_row_check_state(r) == Qt.CheckState.Checked]
        
        if not selected_statement_rows:
            QMessageBox.information(self, "Selection Needed", "Please select a bank statement item to create a Journal Entry for.")
            return
        if len(selected_statement_rows) > 1:
            QMessageBox.information(self, "Selection Limit", "Please select only one statement item at a time to create a Journal Entry.")
            return

        selected_row = selected_statement_rows[0]
        statement_item_dto = self.statement_lines_model.get_item_data_at_row(selected_row)

        if not statement_item_dto: return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        if self._current_bank_account_gl_id is None: QMessageBox.warning(self, "Error", "Current bank account GL link not found."); return

        bank_gl_account_id = self._current_bank_account_gl_id
        statement_amount = statement_item_dto.amount # This is signed from BankTransaction.amount perspective
        
        # Prepare one line of the JE (the bank side)
        bank_line: JournalEntryLineData
        if statement_amount > 0: # Inflow to bank (e.g. Interest Received) -> Debit Bank GL
            bank_line = JournalEntryLineData(account_id=bank_gl_account_id, debit_amount=statement_amount, credit_amount=Decimal(0))
        else: # Outflow from bank (e.g. Bank Charge) -> Credit Bank GL
            bank_line = JournalEntryLineData(account_id=bank_gl_account_id, debit_amount=Decimal(0), credit_amount=abs(statement_amount))
        
        bank_line.description = f"Bank Rec: {statement_item_dto.description[:100]}"
        bank_line.currency_code = self._current_bank_account_currency 
        bank_line.exchange_rate = Decimal(1) # Assume base currency for JE for now

        # Create a partial JournalEntryData
        prefill_je_data = JournalEntryData(
            journal_type="General", # Or "Adjustment"
            entry_date=statement_item_dto.transaction_date,
            description=f"Entry for statement item: {statement_item_dto.description[:150]}",
            reference=statement_item_dto.reference,
            user_id=self.current_user_id,
            lines=[bank_line] 
            # User will add the contra-entry line(s)
        )
        
        # Launch JournalEntryDialog
        dialog = JournalEntryDialog(self.app_core, self.current_user_id, prefill_data_dict=prefill_je_data.model_dump(mode='json'), parent=self)
        dialog.journal_entry_saved.connect(self._handle_je_created_for_statement_item)
        dialog.exec()

    @Slot(int)
    def _handle_je_created_for_statement_item(self, saved_je_id: int):
        self.app_core.logger.info(f"Journal Entry ID {saved_je_id} created from bank reconciliation screen. Refreshing transactions...")
        # Uncheck the processed statement item
        # (This requires knowing which row it was. For now, just reload everything.)
        # For better UX, we could pass the row index to the JE dialog or manage it here.
        
        # For now, simple refresh which will re-fetch unreconciled items.
        # The new system transaction created by the JE posting should appear.
        # The original statement item will still be there until it's matched with the new system txn.
        self._on_load_transactions_clicked() 

```

# app/ui/banking/csv_import_config_dialog.py
```py
# File: app/ui/banking/csv_import_config_dialog.py
import os
import json
from typing import Optional, Dict, Any, TYPE_CHECKING, cast, Tuple, Union # Added Union
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox,
    QMessageBox, QCheckBox, QFileDialog, QLabel, QSpinBox, QGroupBox, QHBoxLayout
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon

from app.utils.result import Result
from app.utils.json_helpers import json_converter # For emitting result dict

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from PySide6.QtGui import QPaintDevice


class CSVImportConfigDialog(QDialog):
    statement_imported = Signal(dict)  # Emits the summary dictionary from the manager

    # Define constants for field mapping keys for consistency
    FIELD_DATE = "date"
    FIELD_DESCRIPTION = "description"
    FIELD_DEBIT = "debit"
    FIELD_CREDIT = "credit"
    FIELD_AMOUNT = "amount" # For single amount column
    FIELD_REFERENCE = "reference"
    FIELD_VALUE_DATE = "value_date"
    
    FIELD_DISPLAY_NAMES = {
        FIELD_DATE: "Transaction Date*",
        FIELD_DESCRIPTION: "Description*",
        FIELD_DEBIT: "Debit Amount Column",
        FIELD_CREDIT: "Credit Amount Column",
        FIELD_AMOUNT: "Single Amount Column*",
        FIELD_REFERENCE: "Reference Column",
        FIELD_VALUE_DATE: "Value Date Column"
    }

    def __init__(self, app_core: "ApplicationCore", bank_account_id: int, current_user_id: int, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.bank_account_id = bank_account_id
        self.current_user_id = current_user_id

        self.setWindowTitle("Import Bank Statement from CSV")
        self.setMinimumWidth(600)
        self.setModal(True)

        self.icon_path_prefix = "resources/icons/"
        try: import app.resources_rc; self.icon_path_prefix = ":/icons/"
        except ImportError: pass

        self._column_mapping_inputs: Dict[str, QLineEdit] = {}
        self._init_ui()
        self._connect_signals()
        self._update_ui_for_column_type() # Initial state

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # File Selection
        file_group = QGroupBox("CSV File")
        file_layout = QHBoxLayout(file_group)
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setPlaceholderText("Select CSV file to import...")
        browse_button = QPushButton(QIcon(self.icon_path_prefix + "open_company.svg"), "Browse...")
        browse_button.setObjectName("BrowseButton") # For easier finding if needed
        file_layout.addWidget(self.file_path_edit, 1)
        file_layout.addWidget(browse_button)
        main_layout.addWidget(file_group)

        # CSV Format Options
        format_group = QGroupBox("CSV Format Options")
        format_layout = QFormLayout(format_group)
        self.has_header_check = QCheckBox("CSV file has a header row")
        self.has_header_check.setChecked(True)
        format_layout.addRow(self.has_header_check)

        self.date_format_edit = QLineEdit("%d/%m/%Y")
        date_format_hint = QLabel("Common: <code>%d/%m/%Y</code>, <code>%Y-%m-%d</code>, <code>%m/%d/%y</code>, <code>%b %d %Y</code>. <a href='https://strftime.org/'>More...</a>")
        date_format_hint.setOpenExternalLinks(True)
        format_layout.addRow("Date Format*:", self.date_format_edit)
        format_layout.addRow("", date_format_hint) # Hint below
        main_layout.addWidget(format_group)

        # Column Mapping
        mapping_group = QGroupBox("Column Mapping (Enter column index or header name)")
        self.mapping_form_layout = QFormLayout(mapping_group)

        # Standard fields
        for field_key in [self.FIELD_DATE, self.FIELD_DESCRIPTION, self.FIELD_REFERENCE, self.FIELD_VALUE_DATE]:
            edit = QLineEdit()
            self._column_mapping_inputs[field_key] = edit
            self.mapping_form_layout.addRow(self.FIELD_DISPLAY_NAMES[field_key] + ":", edit)
        
        # Amount fields - choice
        self.use_single_amount_col_check = QCheckBox("Use a single column for Amount")
        self.use_single_amount_col_check.setChecked(False)
        self.mapping_form_layout.addRow(self.use_single_amount_col_check)

        self._column_mapping_inputs[self.FIELD_DEBIT] = QLineEdit()
        # Store the widget containing the row for visibility toggling
        # QFormLayout.addRow returns the label, not the row widget. Need to get it via children or manage manually.
        # Simpler to just setEnabled on the QLineEdit itself and hide/show rows by iterating.
        self.debit_amount_label = QLabel(self.FIELD_DISPLAY_NAMES[self.FIELD_DEBIT] + ":")
        self.mapping_form_layout.addRow(self.debit_amount_label, self._column_mapping_inputs[self.FIELD_DEBIT])
        
        self._column_mapping_inputs[self.FIELD_CREDIT] = QLineEdit()
        self.credit_amount_label = QLabel(self.FIELD_DISPLAY_NAMES[self.FIELD_CREDIT] + ":")
        self.mapping_form_layout.addRow(self.credit_amount_label, self._column_mapping_inputs[self.FIELD_CREDIT])

        self._column_mapping_inputs[self.FIELD_AMOUNT] = QLineEdit()
        self.single_amount_label = QLabel(self.FIELD_DISPLAY_NAMES[self.FIELD_AMOUNT] + ":")
        self.mapping_form_layout.addRow(self.single_amount_label, self._column_mapping_inputs[self.FIELD_AMOUNT])
        
        self.debit_is_negative_check = QCheckBox("In single amount column, debits are negative values (credits are positive)")
        self.debit_is_negative_check.setChecked(True)
        self.debit_negative_label = QLabel() # Empty label for layout consistency with QFormLayout if needed, or direct addWidget
        self.mapping_form_layout.addRow(self.debit_is_negative_label, self.debit_is_negative_check)


        main_layout.addWidget(mapping_group)

        # Buttons
        self.button_box = QDialogButtonBox()
        self.import_button = self.button_box.addButton("Import", QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)
        
        self._on_has_header_changed(self.has_header_check.isChecked())


    def _connect_signals(self):
        browse_button = self.findChild(QPushButton, "BrowseButton")
        if browse_button: browse_button.clicked.connect(self._browse_file)
        
        self.has_header_check.stateChanged.connect(lambda state: self._on_has_header_changed(state == Qt.CheckState.Checked.value))
        self.use_single_amount_col_check.stateChanged.connect(self._update_ui_for_column_type)

        self.import_button.clicked.connect(self._collect_config_and_import)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button: cancel_button.clicked.connect(self.reject)

    @Slot()
    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Bank Statement CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)

    @Slot(bool)
    def _on_has_header_changed(self, checked: bool):
        placeholder = "Header Name (e.g., Transaction Date)" if checked else "Column Index (e.g., 0)"
        for edit_widget in self._column_mapping_inputs.values():
            edit_widget.setPlaceholderText(placeholder)
            
    @Slot()
    def _update_ui_for_column_type(self):
        use_single_col = self.use_single_amount_col_check.isChecked()
        
        self.debit_amount_label.setVisible(not use_single_col)
        self._column_mapping_inputs[self.FIELD_DEBIT].setVisible(not use_single_col)
        self._column_mapping_inputs[self.FIELD_DEBIT].setEnabled(not use_single_col)
        
        self.credit_amount_label.setVisible(not use_single_col)
        self._column_mapping_inputs[self.FIELD_CREDIT].setVisible(not use_single_col)
        self._column_mapping_inputs[self.FIELD_CREDIT].setEnabled(not use_single_col)
        
        self.single_amount_label.setVisible(use_single_col)
        self._column_mapping_inputs[self.FIELD_AMOUNT].setVisible(use_single_col)
        self._column_mapping_inputs[self.FIELD_AMOUNT].setEnabled(use_single_col)
        
        self.debit_is_negative_check.setVisible(use_single_col)
        self.debit_negative_label.setVisible(use_single_col) # The label for the checkbox row
        self.debit_is_negative_check.setEnabled(use_single_col)

    def _get_column_specifier(self, field_edit: QLineEdit) -> Optional[Union[str, int]]:
        text = field_edit.text().strip()
        if not text:
            return None
        if self.has_header_check.isChecked():
            return text 
        else:
            try:
                return int(text) 
            except ValueError:
                return None 

    @Slot()
    def _collect_config_and_import(self):
        file_path = self.file_path_edit.text().strip()
        if not file_path:
            QMessageBox.warning(self, "Input Error", "Please select a CSV file."); return
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Input Error", f"File not found: {file_path}"); return

        date_format = self.date_format_edit.text().strip()
        if not date_format:
            QMessageBox.warning(self, "Input Error", "Date format is required."); return

        column_map: Dict[str, Any] = {}
        errors: List[str] = []

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
            if debit_spec is None and credit_spec is None:
                errors.append("At least one of Debit or Credit Amount column mapping is required if not using single amount column.")
            if debit_spec is not None: column_map[self.FIELD_DEBIT] = debit_spec
            if credit_spec is not None: column_map[self.FIELD_CREDIT] = credit_spec
        
        ref_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_REFERENCE])
        if ref_spec is not None: column_map[self.FIELD_REFERENCE] = ref_spec
        
        val_date_spec = self._get_column_specifier(self._column_mapping_inputs[self.FIELD_VALUE_DATE])
        if val_date_spec is not None: column_map[self.FIELD_VALUE_DATE] = val_date_spec

        if not self.has_header_check.isChecked():
            for key, val in list(column_map.items()): # Iterate over items to avoid issues if key is deleted
                if val is not None and not isinstance(val, int):
                    errors.append(f"Invalid column index for '{self.FIELD_DISPLAY_NAMES.get(key, key)}': '{val}'. Must be a number when not using headers.")
        
        if errors:
            QMessageBox.warning(self, "Configuration Error", "\n".join(errors)); return

        import_options = {
            "date_format_str": date_format,
            "skip_header": self.has_header_check.isChecked(),
            "debit_is_negative_in_single_col": self.debit_is_negative_check.isChecked() if self.use_single_amount_col_check.isChecked() else False,
            "use_single_amount_column": self.use_single_amount_col_check.isChecked()
        }

        self.import_button.setEnabled(False); self.import_button.setText("Importing...")
        
        future = schedule_task_from_qt(
            self.app_core.bank_transaction_manager.import_bank_statement_csv(
                bank_account_id=self.bank_account_id,
                csv_file_path=file_path,
                user_id=self.current_user_id,
                column_mapping=column_map,
                import_options=import_options 
            )
        )
        if future:
            future.add_done_callback(
                lambda res: QMetaObject.invokeMethod(
                    self, "_handle_import_result_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, future)
                )
            )
        else:
            self.app_core.logger.error("Failed to schedule bank statement import task.")
            self._handle_import_result_slot(None) # Pass None to indicate scheduling failure

    @Slot(object)
    def _handle_import_result_slot(self, future_arg):
        self.import_button.setEnabled(True); self.import_button.setText("Import")
        if future_arg is None:
            QMessageBox.critical(self, "Task Error", "Failed to schedule import operation."); return
        try:
            result: Result[Dict[str, int]] = future_arg.result()
            if result.is_success and result.value:
                summary = result.value
                summary_msg = (
                    f"Import Complete for Bank Account ID: {self.bank_account_id}\n"
                    f"Total Rows Processed: {summary.get('total_rows_in_file', 0)}\n"
                    f"Successfully Imported: {summary.get('imported_count', 0)}\n"
                    f"Skipped (Duplicates): {summary.get('skipped_duplicates_count', 0)}\n"
                    f"Failed (Errors): {summary.get('failed_rows_count', 0)}"
                )
                QMessageBox.information(self, "Import Result", summary_msg)
                self.statement_imported.emit(summary) 
                self.accept()
            else:
                QMessageBox.warning(self, "Import Failed", f"Failed to import statement:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Exception handling import result: {e}", exc_info=True)
            QMessageBox.critical(self, "Import Error", f"An unexpected error occurred: {str(e)}")


```

# app/ui/main_window.py
```py
# File: app/ui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QStatusBar, 
    QVBoxLayout, QWidget, QMessageBox, QLabel 
)
from PySide6.QtGui import QIcon, QKeySequence, QAction 
from PySide6.QtCore import Qt, QSettings, Signal, Slot, QCoreApplication, QSize 

from app.ui.dashboard.dashboard_widget import DashboardWidget
from app.ui.accounting.accounting_widget import AccountingWidget
from app.ui.sales_invoices.sales_invoices_widget import SalesInvoicesWidget
from app.ui.purchase_invoices.purchase_invoices_widget import PurchaseInvoicesWidget
from app.ui.payments.payments_widget import PaymentsWidget 
from app.ui.customers.customers_widget import CustomersWidget
from app.ui.vendors.vendors_widget import VendorsWidget
from app.ui.products.products_widget import ProductsWidget
from app.ui.banking.banking_widget import BankingWidget
from app.ui.banking.bank_reconciliation_widget import BankReconciliationWidget 
from app.ui.reports.reports_widget import ReportsWidget
from app.ui.settings.settings_widget import SettingsWidget
from app.core.application_core import ApplicationCore

class MainWindow(QMainWindow):
    def __init__(self, app_core: ApplicationCore):
        super().__init__()
        self.app_core = app_core
        
        self.setWindowTitle(f"{QCoreApplication.applicationName()} - {QCoreApplication.applicationVersion()}")
        self.setMinimumSize(1024, 768)
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass

        settings = QSettings() 
        if settings.contains("MainWindow/geometry"):
            self.restoreGeometry(settings.value("MainWindow/geometry")) 
        else:
            self.resize(1280, 800)
        
        self._init_ui()
        
        if settings.contains("MainWindow/state"):
            self.restoreState(settings.value("MainWindow/state")) 
    
    def _init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0); self.main_layout.setSpacing(0)
        self._create_toolbar()
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(True)
        self.main_layout.addWidget(self.tab_widget)
        
        self._add_module_tabs()
        self._create_status_bar()
        self._create_actions()
        self._create_menus()
    
    def _create_toolbar(self):
        self.toolbar = QToolBar("Main Toolbar"); self.toolbar.setObjectName("MainToolbar") 
        self.toolbar.setMovable(False); self.toolbar.setIconSize(QSize(24, 24)) 
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar) 
    
    def _add_module_tabs(self):
        self.dashboard_widget = DashboardWidget(self.app_core); self.tab_widget.addTab(self.dashboard_widget, QIcon(self.icon_path_prefix + "dashboard.svg"), "Dashboard")
        self.accounting_widget = AccountingWidget(self.app_core); self.tab_widget.addTab(self.accounting_widget, QIcon(self.icon_path_prefix + "accounting.svg"), "Accounting")
        self.sales_invoices_widget = SalesInvoicesWidget(self.app_core); self.tab_widget.addTab(self.sales_invoices_widget, QIcon(self.icon_path_prefix + "transactions.svg"), "Sales") 
        self.purchase_invoices_widget = PurchaseInvoicesWidget(self.app_core); self.tab_widget.addTab(self.purchase_invoices_widget, QIcon(self.icon_path_prefix + "vendors.svg"), "Purchases") 
        self.payments_widget = PaymentsWidget(self.app_core); self.tab_widget.addTab(self.payments_widget, QIcon(self.icon_path_prefix + "banking.svg"), "Payments") 
        self.customers_widget = CustomersWidget(self.app_core); self.tab_widget.addTab(self.customers_widget, QIcon(self.icon_path_prefix + "customers.svg"), "Customers")
        self.vendors_widget = VendorsWidget(self.app_core); self.tab_widget.addTab(self.vendors_widget, QIcon(self.icon_path_prefix + "vendors.svg"), "Vendors")
        self.products_widget = ProductsWidget(self.app_core); self.tab_widget.addTab(self.products_widget, QIcon(self.icon_path_prefix + "product.svg"), "Products & Services")
        self.banking_widget = BankingWidget(self.app_core)
        self.tab_widget.addTab(self.banking_widget, QIcon(self.icon_path_prefix + "banking.svg"), "Banking C.R.U.D") 
        self.bank_reconciliation_widget = BankReconciliationWidget(self.app_core)
        self.tab_widget.addTab(self.bank_reconciliation_widget, QIcon(self.icon_path_prefix + "transactions.svg"), "Bank Reconciliation") 
        self.reports_widget = ReportsWidget(self.app_core)
        self.tab_widget.addTab(self.reports_widget, QIcon(self.icon_path_prefix + "reports.svg"), "Reports")
        self.settings_widget = SettingsWidget(self.app_core)
        self.tab_widget.addTab(self.settings_widget, QIcon(self.icon_path_prefix + "settings.svg"), "Settings")
    
    def _create_status_bar(self):
        self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready"); self.status_bar.addWidget(self.status_label, 1) 
        user_text = "User: Guest"; 
        if self.app_core.current_user: user_text = f"User: {self.app_core.current_user.username}"
        self.user_label = QLabel(user_text); self.status_bar.addPermanentWidget(self.user_label)
        self.version_label = QLabel(f"Version: {QCoreApplication.applicationVersion()}"); self.status_bar.addPermanentWidget(self.version_label)

    def _create_actions(self):
        self.new_company_action = QAction(QIcon(self.icon_path_prefix + "new_company.svg"), "New Company...", self); self.new_company_action.setShortcut(QKeySequence(QKeySequence.StandardKey.New)); self.new_company_action.triggered.connect(self.on_new_company)
        self.open_company_action = QAction(QIcon(self.icon_path_prefix + "open_company.svg"), "Open Company...", self); self.open_company_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Open)); self.open_company_action.triggered.connect(self.on_open_company)
        self.backup_action = QAction(QIcon(self.icon_path_prefix + "backup.svg"), "Backup Data...", self); self.backup_action.triggered.connect(self.on_backup)
        self.restore_action = QAction(QIcon(self.icon_path_prefix + "restore.svg"), "Restore Data...", self); self.restore_action.triggered.connect(self.on_restore)
        self.exit_action = QAction(QIcon(self.icon_path_prefix + "exit.svg"), "Exit", self); self.exit_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Quit)); self.exit_action.triggered.connect(self.close) 
        self.preferences_action = QAction(QIcon(self.icon_path_prefix + "preferences.svg"), "Preferences...", self); self.preferences_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Preferences)); self.preferences_action.triggered.connect(self.on_preferences)
        self.help_contents_action = QAction(QIcon(self.icon_path_prefix + "help.svg"), "Help Contents", self); self.help_contents_action.setShortcut(QKeySequence(QKeySequence.StandardKey.HelpContents)); self.help_contents_action.triggered.connect(self.on_help_contents)
        self.about_action = QAction(QIcon(self.icon_path_prefix + "about.svg"), "About " + QCoreApplication.applicationName(), self); self.about_action.triggered.connect(self.on_about)

    def _create_menus(self):
        self.file_menu = self.menuBar().addMenu("&File"); self.file_menu.addAction(self.new_company_action); self.file_menu.addAction(self.open_company_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.backup_action); self.file_menu.addAction(self.restore_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.exit_action)
        self.edit_menu = self.menuBar().addMenu("&Edit"); self.edit_menu.addAction(self.preferences_action)
        self.view_menu = self.menuBar().addMenu("&View"); self.tools_menu = self.menuBar().addMenu("&Tools")
        self.help_menu = self.menuBar().addMenu("&Help"); self.help_menu.addAction(self.help_contents_action); self.help_menu.addSeparator(); self.help_menu.addAction(self.about_action)
        self.toolbar.addAction(self.new_company_action); self.toolbar.addAction(self.open_company_action); self.toolbar.addSeparator(); self.toolbar.addAction(self.backup_action); self.toolbar.addAction(self.preferences_action)
    
    @Slot()
    def on_new_company(self): QMessageBox.information(self, "New Company", "New company wizard not yet implemented.")
    @Slot()
    def on_open_company(self): QMessageBox.information(self, "Open Company", "Open company dialog not yet implemented.")
    @Slot()
    def on_backup(self): QMessageBox.information(self, "Backup Data", "Backup functionality not yet implemented.")
    @Slot()
    def on_restore(self): QMessageBox.information(self, "Restore Data", "Restore functionality not yet implemented.")
    @Slot()
    def on_preferences(self): 
        settings_tab_index = -1
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) == self.settings_widget: settings_tab_index = i; break
        if settings_tab_index != -1: self.tab_widget.setCurrentIndex(settings_tab_index)
        else: QMessageBox.information(self, "Preferences", "Preferences (Settings Tab) not found or full dialog not yet implemented.")
    @Slot()
    def on_help_contents(self): QMessageBox.information(self, "Help", "Help system not yet implemented.")
    @Slot()
    def on_about(self): QMessageBox.about(self, f"About {QCoreApplication.applicationName()}", f"{QCoreApplication.applicationName()} {QCoreApplication.applicationVersion()}\n\nA comprehensive bookkeeping application for Singapore small businesses.\n\n© 2024 {QCoreApplication.organizationName()}"); 
    def closeEvent(self, event): 
        settings = QSettings(); settings.setValue("MainWindow/geometry", self.saveGeometry()); settings.setValue("MainWindow/state", self.saveState()); settings.sync()
        reply = QMessageBox.question(self, "Confirm Exit", "Are you sure you want to exit?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes: event.accept() 
        else: event.ignore()

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
class BankTransactionSummaryData(AppBaseModel): id: int; transaction_date: date; value_date: Optional[date] = None; transaction_type: BankTransactionTypeEnum; description: str; reference: Optional[str] = None; amount: Decimal; is_reconciled: bool = False

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
    

```

# app/services/audit_services.py
```py
# File: app/services/audit_services.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any, TYPE_CHECKING, Dict, Tuple, Union # Ensure Union is imported
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, aliased
from datetime import datetime, date # date might not be used directly but good to have with datetime

from app.core.database_manager import DatabaseManager
from app.models.audit.audit_log import AuditLog
from app.models.audit.data_change_history import DataChangeHistory
from app.models.core.user import User 
from app.services import IRepository # Base repository interface
from app.utils.pydantic_models import AuditLogEntryData, DataChangeHistoryEntryData
# from app.utils.result import Result # Not typically returned by services, but managers
from app.common.enums import DataChangeTypeEnum

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    # from sqlalchemy.ext.asyncio import AsyncSession # If session is passed around

# Define Interfaces (can also be in __init__.py, but here for clarity with service)
class IAuditLogRepository(IRepository[AuditLog, int]):
    @abstractmethod
    async def get_audit_logs_paginated(
        self,
        user_id_filter: Optional[int] = None,
        action_filter: Optional[str] = None,
        entity_type_filter: Optional[str] = None,
        entity_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None,
        end_date_filter: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[AuditLogEntryData], int]: # Returns list of DTOs and total count
        pass

class IDataChangeHistoryRepository(IRepository[DataChangeHistory, int]):
    @abstractmethod
    async def get_data_change_history_paginated(
        self,
        table_name_filter: Optional[str] = None,
        record_id_filter: Optional[int] = None,
        changed_by_user_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None,
        end_date_filter: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[DataChangeHistoryEntryData], int]: # Returns list of DTOs and total count
        pass


class AuditLogService(IAuditLogRepository, IDataChangeHistoryRepository): 
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core # app_core can be used for accessing logger or other global components

    # --- Standard IRepository Stubs (Audit logs are mostly read-only from app perspective) ---
    async def get_by_id(self, id_val: int) -> Optional[Union[AuditLog, DataChangeHistory]]:
        # This method might be less useful for audit logs which are usually queried by context, not ID.
        # However, implementing for interface compliance or specific edge cases.
        async with self.db_manager.session() as session:
            log_entry = await session.get(AuditLog, id_val)
            if log_entry:
                # Could convert to DTO here if consistency is desired, but service usually returns ORM
                return log_entry
            history_entry = await session.get(DataChangeHistory, id_val)
            return history_entry # Could also be DTO
            
    async def get_all(self) -> List[Union[AuditLog, DataChangeHistory]]:
        # Not practical for potentially huge audit tables. Use paginated methods.
        raise NotImplementedError("Use paginated methods for audit logs. Get_all is not supported.")

    async def add(self, entity: Union[AuditLog, DataChangeHistory]) -> Union[AuditLog, DataChangeHistory]:
        # Audit logs are typically generated by database triggers or specialized logging calls, not generic add.
        raise NotImplementedError("Audit logs are system-generated and cannot be added via this service.")

    async def update(self, entity: Union[AuditLog, DataChangeHistory]) -> Union[AuditLog, DataChangeHistory]:
        # Audit logs should be immutable.
        raise NotImplementedError("Audit logs are immutable and cannot be updated.")

    async def delete(self, id_val: int) -> bool:
        # Audit logs should generally not be deleted programmatically, archiving is preferred.
        raise NotImplementedError("Audit logs should not be deleted programmatically via this service.")

    # --- Custom Service Methods for Audit Logs ---

    def _format_changes_summary(self, changes_jsonb: Optional[Dict[str, Any]]) -> Optional[str]:
        if not changes_jsonb:
            return None
        
        summary_parts = []
        old_data = changes_jsonb.get('old')
        new_data = changes_jsonb.get('new')

        action = "Modified" # Default action
        if isinstance(new_data, dict) and old_data is None:
            action = "Created"
        elif new_data is None and isinstance(old_data, dict):
            action = "Deleted"
        
        if action == "Created" and isinstance(new_data, dict):
            # For created records, list some key fields if possible, or just confirm creation
            # Example: List up to 3 non-sensitive fields.
            keys_to_show = [k for k in new_data.keys() if k not in ["id", "created_at", "updated_at", "password_hash", "logo"]][:3]
            if keys_to_show:
                details = ", ".join([f"{k}: '{str(new_data[k])[:30]}...'" if len(str(new_data[k])) > 30 else f"{k}: '{str(new_data[k])}'" for k in keys_to_show])
                summary_parts.append(f"Record {action}. Details: {details}")
            else:
                summary_parts.append(f"Record {action}.")
        elif action == "Deleted" and isinstance(old_data, dict):
            summary_parts.append(f"Record {action}.")
        elif action == "Modified" and isinstance(new_data, dict) and isinstance(old_data, dict):
            changed_fields_count = 0
            for key, new_val in new_data.items():
                if key in ["created_at", "updated_at", "password_hash", "logo"]: # Skip noisy or sensitive fields
                    continue 
                old_val = old_data.get(key) # Use .get() in case old_data doesn't have the key (new field added to schema)
                
                # Handle cases where a value might be a list or dict itself (e.g. JSONB field)
                # For simplicity, we'll compare their string representations for this summary
                str_old_val = str(old_val)
                str_new_val = str(new_val)

                if str_old_val != str_new_val: 
                    changed_fields_count += 1
                    if changed_fields_count <= 3: # Show details for first few changes
                        summary_parts.append(
                            f"'{key}': '{str_old_val[:30]}...' -> '{str_new_val[:30]}...'" 
                            if len(str_old_val) > 30 or len(str_new_val) > 30 
                            else f"'{key}': '{str_old_val}' -> '{str_new_val}'"
                        )
            if changed_fields_count > 3:
                summary_parts.append(f"...and {changed_fields_count - 3} other field(s).")
            if not summary_parts and changed_fields_count == 0 : # Only timestamps / sensitive fields changed
                 summary_parts.append("Minor updates (e.g., timestamps).")

        return "; ".join(summary_parts) if summary_parts else "No changes detailed or only sensitive fields updated."


    async def get_audit_logs_paginated(
        self,
        user_id_filter: Optional[int] = None,
        action_filter: Optional[str] = None,
        entity_type_filter: Optional[str] = None,
        entity_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None,
        end_date_filter: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[AuditLogEntryData], int]:
        async with self.db_manager.session() as session:
            conditions = []
            if user_id_filter is not None:
                conditions.append(AuditLog.user_id == user_id_filter)
            if action_filter:
                conditions.append(AuditLog.action.ilike(f"%{action_filter}%")) # Case-insensitive search
            if entity_type_filter:
                conditions.append(AuditLog.entity_type.ilike(f"%{entity_type_filter}%"))
            if entity_id_filter is not None:
                conditions.append(AuditLog.entity_id == entity_id_filter)
            if start_date_filter:
                conditions.append(AuditLog.timestamp >= start_date_filter)
            if end_date_filter: # Add 1 day to end_date_filter to make it inclusive of the whole day
                conditions.append(AuditLog.timestamp < (end_date_filter + datetime.timedelta(days=1)))


            UserAlias = aliased(User, name="user_alias") # Explicit alias name
            
            # Count total matching records
            count_stmt = select(func.count(AuditLog.id))
            if conditions:
                count_stmt = count_stmt.where(and_(*conditions))
            total_count_res = await session.execute(count_stmt)
            total_count = total_count_res.scalar_one()

            # Fetch paginated records
            stmt = select(AuditLog, UserAlias.username.label("username")).outerjoin(
                UserAlias, AuditLog.user_id == UserAlias.id # Ensure correct join condition
            )
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(AuditLog.timestamp.desc()) # type: ignore[attr-defined]
            if page_size > 0: # Allow page_size=0 or negative to fetch all (though not recommended for large tables)
                 stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            
            result = await session.execute(stmt)
            log_entries_data: List[AuditLogEntryData] = []
            
            for row_mapping in result.mappings().all(): # Use mappings() for dict-like access
                log_orm = row_mapping[AuditLog]
                username = row_mapping["username"] if row_mapping["username"] else \
                           (f"User ID: {log_orm.user_id}" if log_orm.user_id else "System/Unknown")
                
                log_entries_data.append(AuditLogEntryData(
                    id=log_orm.id,
                    timestamp=log_orm.timestamp,
                    username=username,
                    action=log_orm.action,
                    entity_type=log_orm.entity_type,
                    entity_id=log_orm.entity_id,
                    entity_name=log_orm.entity_name,
                    changes_summary=self._format_changes_summary(log_orm.changes),
                    ip_address=log_orm.ip_address
                ))
            return log_entries_data, total_count

    async def get_data_change_history_paginated(
        self,
        table_name_filter: Optional[str] = None,
        record_id_filter: Optional[int] = None,
        changed_by_user_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None,
        end_date_filter: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[DataChangeHistoryEntryData], int]:
        async with self.db_manager.session() as session:
            conditions = []
            if table_name_filter:
                conditions.append(DataChangeHistory.table_name.ilike(f"%{table_name_filter}%"))
            if record_id_filter is not None:
                conditions.append(DataChangeHistory.record_id == record_id_filter)
            if changed_by_user_id_filter is not None:
                conditions.append(DataChangeHistory.changed_by == changed_by_user_id_filter)
            if start_date_filter:
                conditions.append(DataChangeHistory.changed_at >= start_date_filter)
            if end_date_filter: # Add 1 day to end_date_filter to make it inclusive of the whole day
                conditions.append(DataChangeHistory.changed_at < (end_date_filter + datetime.timedelta(days=1)))


            UserAlias = aliased(User, name="changed_by_user_alias") # Explicit alias name

            # Count total matching records
            count_stmt = select(func.count(DataChangeHistory.id))
            if conditions:
                count_stmt = count_stmt.where(and_(*conditions))
            total_count_res = await session.execute(count_stmt)
            total_count = total_count_res.scalar_one()

            # Fetch paginated records
            stmt = select(DataChangeHistory, UserAlias.username.label("changed_by_username")).outerjoin(
                UserAlias, DataChangeHistory.changed_by == UserAlias.id # Ensure correct join condition
            )
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(DataChangeHistory.changed_at.desc()) # type: ignore[attr-defined]
            if page_size > 0:
                 stmt = stmt.limit(page_size).offset((page - 1) * page_size)

            result = await session.execute(stmt)
            history_entries_data: List[DataChangeHistoryEntryData] = []

            for row_mapping in result.mappings().all(): # Use mappings() for dict-like access
                hist_orm = row_mapping[DataChangeHistory]
                username = row_mapping["changed_by_username"] if row_mapping["changed_by_username"] else \
                           (f"User ID: {hist_orm.changed_by}" if hist_orm.changed_by else "System/Unknown")
                
                history_entries_data.append(DataChangeHistoryEntryData(
                    id=hist_orm.id,
                    changed_at=hist_orm.changed_at,
                    table_name=hist_orm.table_name,
                    record_id=hist_orm.record_id,
                    field_name=hist_orm.field_name,
                    old_value=hist_orm.old_value,
                    new_value=hist_orm.new_value,
                    change_type=DataChangeTypeEnum(hist_orm.change_type), # Convert string from DB to Enum
                    changed_by_username=username
                ))
            return history_entries_data, total_count

```

# app/services/__init__.py
```py
# File: app/services/__init__.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Generic, TypeVar, Dict, Tuple 
from datetime import date, datetime 
from decimal import Decimal 
from sqlalchemy.ext.asyncio import AsyncSession # Added for IBankReconciliationRepository

T = TypeVar('T') 
ID = TypeVar('ID') 

class IRepository(ABC, Generic[T, ID]):
    @abstractmethod
    async def get_by_id(self, id_val: ID) -> Optional[T]: pass
    @abstractmethod
    async def get_all(self) -> List[T]: pass
    @abstractmethod
    async def add(self, entity: T) -> T: pass
    @abstractmethod
    async def update(self, entity: T) -> T: pass
    @abstractmethod
    async def delete(self, id_val: ID) -> bool: pass

# --- ORM Model Imports ---
from app.models.accounting.account import Account
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine 
from app.models.accounting.fiscal_period import FiscalPeriod
from app.models.accounting.tax_code import TaxCode
from app.models.core.company_setting import CompanySetting 
from app.models.accounting.gst_return import GSTReturn
from app.models.accounting.recurring_pattern import RecurringPattern
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.account_type import AccountType 
from app.models.accounting.currency import Currency 
from app.models.accounting.exchange_rate import ExchangeRate 
from app.models.core.sequence import Sequence 
from app.models.core.configuration import Configuration 
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.product import Product
from app.models.business.sales_invoice import SalesInvoice
from app.models.business.purchase_invoice import PurchaseInvoice
from app.models.business.inventory_movement import InventoryMovement
from app.models.accounting.dimension import Dimension 
from app.models.business.bank_account import BankAccount 
from app.models.business.bank_transaction import BankTransaction 
from app.models.business.payment import Payment, PaymentAllocation 
from app.models.audit.audit_log import AuditLog 
from app.models.audit.data_change_history import DataChangeHistory 
from app.models.business.bank_reconciliation import BankReconciliation

# --- DTO Imports (for return types in interfaces) ---
from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData,
    BankAccountSummaryData, BankTransactionSummaryData,
    PaymentSummaryData,
    AuditLogEntryData, DataChangeHistoryEntryData, BankReconciliationData
)
from app.common.enums import ( 
    ProductTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum,
    PaymentTypeEnum, PaymentEntityTypeEnum, PaymentStatusEnum, DataChangeTypeEnum 
)

# --- Existing Interfaces ---
class IAccountRepository(IRepository[Account, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Account]: pass
    @abstractmethod
    async def get_all_active(self) -> List[Account]: pass
    @abstractmethod
    async def get_by_type(self, account_type: str, active_only: bool = True) -> List[Account]: pass
    @abstractmethod
    async def save(self, account: Account) -> Account: pass 
    @abstractmethod
    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]: pass 
    @abstractmethod
    async def has_transactions(self, account_id: int) -> bool: pass
    @abstractmethod
    async def get_accounts_by_tax_treatment(self, tax_treatment_code: str) -> List[Account]: pass

class IJournalEntryRepository(IRepository[JournalEntry, int]): 
    @abstractmethod
    async def get_by_entry_no(self, entry_no: str) -> Optional[JournalEntry]: pass
    @abstractmethod
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]: pass
    @abstractmethod
    async def get_posted_entries_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]: pass
    @abstractmethod
    async def save(self, journal_entry: JournalEntry) -> JournalEntry: pass
    @abstractmethod
    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal: pass
    @abstractmethod
    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal: pass
    @abstractmethod
    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]: pass
    @abstractmethod
    async def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern: pass
    @abstractmethod
    async def get_all_summary(self, start_date_filter: Optional[date] = None, 
                              end_date_filter: Optional[date] = None, 
                              status_filter: Optional[str] = None,
                              entry_no_filter: Optional[str] = None,
                              description_filter: Optional[str] = None,
                              journal_type_filter: Optional[str] = None
                             ) -> List[Dict[str, Any]]: pass
    @abstractmethod
    async def get_posted_lines_for_account_in_range(self, account_id: int, start_date: date, end_date: date, 
                                                    dimension1_id: Optional[int] = None, dimension2_id: Optional[int] = None
                                                    ) -> List[JournalEntryLine]: pass 

class IFiscalPeriodRepository(IRepository[FiscalPeriod, int]): 
    @abstractmethod
    async def get_by_date(self, target_date: date) -> Optional[FiscalPeriod]: pass
    @abstractmethod
    async def get_fiscal_periods_for_year(self, fiscal_year_id: int, period_type: Optional[str] = None) -> List[FiscalPeriod]: pass

class IFiscalYearRepository(IRepository[FiscalYear, int]): 
    @abstractmethod
    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def get_by_date_overlap(self, start_date: date, end_date: date, exclude_id: Optional[int] = None) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def save(self, entity: FiscalYear) -> FiscalYear: pass

class ITaxCodeRepository(IRepository[TaxCode, int]): 
    @abstractmethod
    async def get_tax_code(self, code: str) -> Optional[TaxCode]: pass
    @abstractmethod
    async def save(self, entity: TaxCode) -> TaxCode: pass 

class ICompanySettingsRepository(IRepository[CompanySetting, int]): 
    @abstractmethod
    async def get_company_settings(self, settings_id: int = 1) -> Optional[CompanySetting]: pass
    @abstractmethod
    async def save_company_settings(self, settings_obj: CompanySetting) -> CompanySetting: pass

class IGSTReturnRepository(IRepository[GSTReturn, int]): 
    @abstractmethod
    async def get_gst_return(self, return_id: int) -> Optional[GSTReturn]: pass 
    @abstractmethod
    async def save_gst_return(self, gst_return_data: GSTReturn) -> GSTReturn: pass

class IAccountTypeRepository(IRepository[AccountType, int]): 
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[AccountType]: pass
    @abstractmethod
    async def get_by_category(self, category: str) -> List[AccountType]: pass

class ICurrencyRepository(IRepository[Currency, str]): 
    @abstractmethod
    async def get_all_active(self) -> List[Currency]: pass

class IExchangeRateRepository(IRepository[ExchangeRate, int]): 
    @abstractmethod
    async def get_rate_for_date(self, from_code: str, to_code: str, r_date: date) -> Optional[ExchangeRate]: pass
    @abstractmethod
    async def save(self, entity: ExchangeRate) -> ExchangeRate: pass

class ISequenceRepository(IRepository[Sequence, int]): 
    @abstractmethod
    async def get_sequence_by_name(self, name: str) -> Optional[Sequence]: pass
    @abstractmethod
    async def save_sequence(self, sequence_obj: Sequence) -> Sequence: pass

class IConfigurationRepository(IRepository[Configuration, int]): 
    @abstractmethod
    async def get_config_by_key(self, key: str) -> Optional[Configuration]: pass
    @abstractmethod
    async def save_config(self, config_obj: Configuration) -> Configuration: pass

class ICustomerRepository(IRepository[Customer, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Customer]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[CustomerSummaryData]: pass

class IVendorRepository(IRepository[Vendor, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Vendor]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[VendorSummaryData]: pass

class IProductRepository(IRepository[Product, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Product]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              active_only: bool = True,
                              product_type_filter: Optional[ProductTypeEnum] = None,
                              search_term: Optional[str] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[ProductSummaryData]: pass

class ISalesInvoiceRepository(IRepository[SalesInvoice, int]):
    @abstractmethod
    async def get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              customer_id: Optional[int] = None,
                              status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[SalesInvoiceSummaryData]: pass

class IPurchaseInvoiceRepository(IRepository[PurchaseInvoice, int]):
    @abstractmethod
    async def get_by_internal_ref_no(self, internal_ref_no: str) -> Optional[PurchaseInvoice]: pass 
    @abstractmethod
    async def get_by_vendor_and_vendor_invoice_no(self, vendor_id: int, vendor_invoice_no: str) -> Optional[PurchaseInvoice]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              vendor_id: Optional[int] = None,
                              status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[PurchaseInvoiceSummaryData]: pass

class IInventoryMovementRepository(IRepository[InventoryMovement, int]):
    @abstractmethod
    async def save(self, entity: InventoryMovement, session: Optional[AsyncSession]=None) -> InventoryMovement: pass # Updated type hint to AsyncSession

class IDimensionRepository(IRepository[Dimension, int]):
    @abstractmethod
    async def get_distinct_dimension_types(self) -> List[str]: pass
    @abstractmethod
    async def get_dimensions_by_type(self, dim_type: str, active_only: bool = True) -> List[Dimension]: pass
    @abstractmethod
    async def get_by_type_and_code(self, dim_type: str, code: str) -> Optional[Dimension]: pass

class IBankAccountRepository(IRepository[BankAccount, int]):
    @abstractmethod
    async def get_by_account_number(self, account_number: str) -> Optional[BankAccount]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True, 
                              currency_code: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[BankAccountSummaryData]: pass
    @abstractmethod
    async def save(self, entity: BankAccount) -> BankAccount: pass

class IBankTransactionRepository(IRepository[BankTransaction, int]):
    @abstractmethod
    async def get_all_for_bank_account(self, bank_account_id: int,
                                       start_date: Optional[date] = None,
                                       end_date: Optional[date] = None,
                                       transaction_type: Optional[BankTransactionTypeEnum] = None,
                                       is_reconciled: Optional[bool] = None,
                                       is_from_statement_filter: Optional[bool] = None, 
                                       page: int = 1, page_size: int = 50
                                      ) -> List[BankTransactionSummaryData]: pass 
    @abstractmethod
    async def save(self, entity: BankTransaction, session: Optional[AsyncSession] = None) -> BankTransaction: # Updated type hint

class IPaymentRepository(IRepository[Payment, int]):
    @abstractmethod
    async def get_by_payment_no(self, payment_no: str) -> Optional[Payment]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              entity_type: Optional[PaymentEntityTypeEnum] = None,
                              entity_id: Optional[int] = None,
                              status: Optional[PaymentStatusEnum] = None,
                              start_date: Optional[date] = None,
                              end_date: Optional[date] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[PaymentSummaryData]: pass
    @abstractmethod
    async def save(self, entity: Payment, session: Optional[AsyncSession] = None) -> Payment: # Updated type hint

class IAuditLogRepository(IRepository[AuditLog, int]):
    @abstractmethod
    async def get_audit_logs_paginated(
        self, user_id_filter: Optional[int] = None, action_filter: Optional[str] = None, entity_type_filter: Optional[str] = None,
        entity_id_filter: Optional[int] = None, start_date_filter: Optional[datetime] = None, end_date_filter: Optional[datetime] = None,   
        page: int = 1, page_size: int = 50
    ) -> Tuple[List[AuditLogEntryData], int]: pass 

class IDataChangeHistoryRepository(IRepository[DataChangeHistory, int]):
    @abstractmethod
    async def get_data_change_history_paginated(
        self, table_name_filter: Optional[str] = None, record_id_filter: Optional[int] = None, changed_by_user_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None, end_date_filter: Optional[datetime] = None,   
        page: int = 1, page_size: int = 50
    ) -> Tuple[List[DataChangeHistoryEntryData], int]: pass 

class IBankReconciliationRepository(IRepository[BankReconciliation, int]):
    @abstractmethod
    async def save_reconciliation_details(
        self, 
        reconciliation_orm: BankReconciliation,
        cleared_statement_txn_ids: List[int], 
        cleared_system_txn_ids: List[int],
        statement_end_date: date,
        bank_account_id: int,
        statement_ending_balance: Decimal,
        session: AsyncSession 
    ) -> BankReconciliation: pass

from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService, DimensionService
from .business_services import (
    CustomerService, VendorService, ProductService, 
    SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService,
    BankAccountService, BankTransactionService, PaymentService, 
    BankReconciliationService
)
from .audit_services import AuditLogService 

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository", 
    "ICustomerRepository", "IVendorRepository", "IProductRepository",
    "ISalesInvoiceRepository", "IPurchaseInvoiceRepository", 
    "IInventoryMovementRepository", 
    "IDimensionRepository", 
    "IBankAccountRepository", 
    "IBankTransactionRepository", 
    "IPaymentRepository", 
    "IAuditLogRepository", "IDataChangeHistoryRepository", 
    "IBankReconciliationRepository", 
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService", "DimensionService", 
    "CustomerService", "VendorService", "ProductService", 
    "SalesInvoiceService", "PurchaseInvoiceService", 
    "InventoryMovementService", 
    "BankAccountService", 
    "BankTransactionService",
    "PaymentService", 
    "AuditLogService", 
    "BankReconciliationService", 
]


```

# app/services/business_services.py
```py
# File: app/services/business_services.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict, Tuple
from sqlalchemy import select, func, and_, or_, literal_column, case, update as sqlalchemy_update
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.orm import selectinload, joinedload 
from decimal import Decimal
import logging 
from datetime import date 

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
from app.models.business.bank_reconciliation import BankReconciliation # New import
from app.models.accounting.account import Account 
from app.models.accounting.currency import Currency 
from app.models.accounting.tax_code import TaxCode 
from app.services import (
    ICustomerRepository, IVendorRepository, IProductRepository, 
    ISalesInvoiceRepository, IPurchaseInvoiceRepository, IInventoryMovementRepository,
    IBankAccountRepository, IBankTransactionRepository, IPaymentRepository,
    IBankReconciliationRepository # New import
)
from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData,
    BankAccountSummaryData, BankTransactionSummaryData,
    PaymentSummaryData # BankReconciliationData not directly returned by this file's services but good for consistency
)
from app.common.enums import ProductTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum, PaymentEntityTypeEnum, PaymentStatusEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

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
                summaries.append(BankTransactionSummaryData(id=txn.id,transaction_date=txn.transaction_date,value_date=txn.value_date,transaction_type=BankTransactionTypeEnum(txn.transaction_type), description=txn.description,reference=txn.reference,amount=txn.amount, is_reconciled=txn.is_reconciled))
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
            return await session.get(BankReconciliation, id_val)

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
        self.logger.warning(f"Deletion of BankReconciliation ID {id_val} attempted. This operation should be handled with care and may require reversing reconciled transactions.")
        async with self.db_manager.session() as session:
            update_stmt = (
                sqlalchemy_update(BankTransaction)
                .where(BankTransaction.reconciled_bank_reconciliation_id == id_val)
                .values(is_reconciled=False, reconciled_date=None, reconciled_bank_reconciliation_id=None)
            )
            await session.execute(update_stmt)
            entity = await session.get(BankReconciliation, id_val)
            if entity:
                await session.delete(entity)
                await session.flush() 
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

    async def save_reconciliation_details(
        self, 
        reconciliation_orm: BankReconciliation,
        cleared_statement_txn_ids: List[int], 
        cleared_system_txn_ids: List[int],
        statement_end_date: date,
        bank_account_id: int,
        statement_ending_balance: Decimal, 
        session: AsyncSession
    ) -> BankReconciliation:
        session.add(reconciliation_orm)
        await session.flush() 
        await session.refresh(reconciliation_orm)
        
        all_cleared_txn_ids = list(set(cleared_statement_txn_ids + cleared_system_txn_ids))
        if all_cleared_txn_ids:
            update_txn_stmt = (
                sqlalchemy_update(BankTransaction)
                .where(BankTransaction.id.in_(all_cleared_txn_ids))
                .values(
                    is_reconciled=True,
                    reconciled_date=statement_end_date,
                    reconciled_bank_reconciliation_id=reconciliation_orm.id
                )
                .execution_options(synchronize_session="fetch") 
            )
            await session.execute(update_txn_stmt)

        bank_account_to_update = await session.get(BankAccount, bank_account_id)
        if bank_account_to_update:
            bank_account_to_update.last_reconciled_date = statement_end_date
            bank_account_to_update.last_reconciled_balance = statement_ending_balance 
            session.add(bank_account_to_update)
        else:
            self.logger.error(f"BankAccount ID {bank_account_id} not found during reconciliation save for BankReconciliation ID {reconciliation_orm.id}.")
            raise ValueError(f"BankAccount ID {bank_account_id} not found during reconciliation save.")

        await session.flush() 
        await session.refresh(reconciliation_orm) 
        return reconciliation_orm

```

# app/core/application_core.py
```py
# File: app/core/application_core.py
from typing import Optional, Any
from app.core.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager 
from app.core.security_manager import SecurityManager
from app.core.module_manager import ModuleManager

# Accounting Managers
from app.accounting.chart_of_accounts_manager import ChartOfAccountsManager
from app.accounting.journal_entry_manager import JournalEntryManager
from app.accounting.fiscal_period_manager import FiscalPeriodManager
from app.accounting.currency_manager import CurrencyManager

# Business Logic Managers
from app.business_logic.customer_manager import CustomerManager 
from app.business_logic.vendor_manager import VendorManager 
from app.business_logic.product_manager import ProductManager
from app.business_logic.sales_invoice_manager import SalesInvoiceManager
from app.business_logic.purchase_invoice_manager import PurchaseInvoiceManager 
from app.business_logic.bank_account_manager import BankAccountManager 
from app.business_logic.bank_transaction_manager import BankTransactionManager
from app.business_logic.payment_manager import PaymentManager 

# Services
from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.core_services import SequenceService, CompanySettingsService, ConfigurationService
from app.services.tax_service import TaxCodeService, GSTReturnService 
from app.services.accounting_services import (
    AccountTypeService, CurrencyService as CurrencyRepoService, 
    ExchangeRateService, FiscalYearService, DimensionService 
)
from app.services.business_services import (
    CustomerService, VendorService, ProductService, 
    SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService,
    BankAccountService, BankTransactionService, PaymentService 
)
from app.services.audit_services import AuditLogService

# Utilities
from app.utils.sequence_generator import SequenceGenerator 

# Tax and Reporting
from app.tax.gst_manager import GSTManager
from app.tax.tax_calculator import TaxCalculator
from app.reporting.financial_statement_generator import FinancialStatementGenerator
from app.reporting.report_engine import ReportEngine
import logging 

class ApplicationCore:
    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.db_manager.app_core = self 
        
        self.logger = logging.getLogger("SGBookkeeperAppCore")
        if not self.logger.handlers:
            handler = logging.StreamHandler(); formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter); self.logger.addHandler(handler); self.logger.setLevel(logging.INFO) 
        if not hasattr(self.db_manager, 'logger') or self.db_manager.logger is None: self.db_manager.logger = self.logger

        self.security_manager = SecurityManager(self.db_manager)
        self.module_manager = ModuleManager(self)

        # Service Instance Placeholders
        self._account_service_instance: Optional[AccountService] = None
        self._journal_service_instance: Optional[JournalService] = None
        self._fiscal_period_service_instance: Optional[FiscalPeriodService] = None
        self._fiscal_year_service_instance: Optional[FiscalYearService] = None
        self._sequence_service_instance: Optional[SequenceService] = None
        self._company_settings_service_instance: Optional[CompanySettingsService] = None
        self._configuration_service_instance: Optional[ConfigurationService] = None
        self._tax_code_service_instance: Optional[TaxCodeService] = None
        self._gst_return_service_instance: Optional[GSTReturnService] = None
        self._account_type_service_instance: Optional[AccountTypeService] = None
        self._currency_repo_service_instance: Optional[CurrencyRepoService] = None
        self._exchange_rate_service_instance: Optional[ExchangeRateService] = None
        self._dimension_service_instance: Optional[DimensionService] = None
        self._customer_service_instance: Optional[CustomerService] = None
        self._vendor_service_instance: Optional[VendorService] = None
        self._product_service_instance: Optional[ProductService] = None
        self._sales_invoice_service_instance: Optional[SalesInvoiceService] = None
        self._purchase_invoice_service_instance: Optional[PurchaseInvoiceService] = None 
        self._inventory_movement_service_instance: Optional[InventoryMovementService] = None
        self._bank_account_service_instance: Optional[BankAccountService] = None 
        self._bank_transaction_service_instance: Optional[BankTransactionService] = None
        self._payment_service_instance: Optional[PaymentService] = None
        self._audit_log_service_instance: Optional[AuditLogService] = None

        # Manager Instance Placeholders
        self._coa_manager_instance: Optional[ChartOfAccountsManager] = None
        self._je_manager_instance: Optional[JournalEntryManager] = None
        self._fp_manager_instance: Optional[FiscalPeriodManager] = None
        self._currency_manager_instance: Optional[CurrencyManager] = None
        self._gst_manager_instance: Optional[GSTManager] = None
        self._tax_calculator_instance: Optional[TaxCalculator] = None
        self._financial_statement_generator_instance: Optional[FinancialStatementGenerator] = None
        self._report_engine_instance: Optional[ReportEngine] = None
        self._customer_manager_instance: Optional[CustomerManager] = None
        self._vendor_manager_instance: Optional[VendorManager] = None
        self._product_manager_instance: Optional[ProductManager] = None
        self._sales_invoice_manager_instance: Optional[SalesInvoiceManager] = None
        self._purchase_invoice_manager_instance: Optional[PurchaseInvoiceManager] = None
        self._bank_account_manager_instance: Optional[BankAccountManager] = None
        self._bank_transaction_manager_instance: Optional[BankTransactionManager] = None
        self._payment_manager_instance: Optional[PaymentManager] = None
        
        self.logger.info("ApplicationCore initialized.")

    async def startup(self):
        self.logger.info("ApplicationCore starting up...")
        await self.db_manager.initialize() 
        
        self._sequence_service_instance = SequenceService(self.db_manager)
        self._company_settings_service_instance = CompanySettingsService(self.db_manager, self)
        self._configuration_service_instance = ConfigurationService(self.db_manager)
        self._account_service_instance = AccountService(self.db_manager, self)
        self._journal_service_instance = JournalService(self.db_manager, self)
        self._fiscal_period_service_instance = FiscalPeriodService(self.db_manager)
        self._fiscal_year_service_instance = FiscalYearService(self.db_manager, self)
        self._account_type_service_instance = AccountTypeService(self.db_manager, self) 
        self._currency_repo_service_instance = CurrencyRepoService(self.db_manager, self)
        self._exchange_rate_service_instance = ExchangeRateService(self.db_manager, self)
        self._dimension_service_instance = DimensionService(self.db_manager, self)
        self._tax_code_service_instance = TaxCodeService(self.db_manager, self)
        self._gst_return_service_instance = GSTReturnService(self.db_manager, self)
        self._customer_service_instance = CustomerService(self.db_manager, self)
        self._vendor_service_instance = VendorService(self.db_manager, self) 
        self._product_service_instance = ProductService(self.db_manager, self)
        self._sales_invoice_service_instance = SalesInvoiceService(self.db_manager, self)
        self._purchase_invoice_service_instance = PurchaseInvoiceService(self.db_manager, self) 
        self._inventory_movement_service_instance = InventoryMovementService(self.db_manager, self) 
        self._bank_account_service_instance = BankAccountService(self.db_manager, self) 
        self._bank_transaction_service_instance = BankTransactionService(self.db_manager, self)
        self._payment_service_instance = PaymentService(self.db_manager, self) 
        self._audit_log_service_instance = AuditLogService(self.db_manager, self)

        # py_sequence_generator is still created as GSTManager might expect it.
        # If GSTManager also moves to DB sequences, this can be removed.
        py_sequence_generator = SequenceGenerator(self.sequence_service, app_core_ref=self) 
        
        self._coa_manager_instance = ChartOfAccountsManager(self.account_service, self)
        # Corrected instantiation for JournalEntryManager: removed py_sequence_generator
        self._je_manager_instance = JournalEntryManager(self.journal_service, self.account_service, self.fiscal_period_service, self)
        self._fp_manager_instance = FiscalPeriodManager(self) 
        self._currency_manager_instance = CurrencyManager(self) 
        self._tax_calculator_instance = TaxCalculator(self.tax_code_service) 
        # GSTManager still takes py_sequence_generator in its signature from file set 6
        self._gst_manager_instance = GSTManager(self.tax_code_service, self.journal_service, self.company_settings_service, self.gst_return_service, self.account_service, self.fiscal_period_service, py_sequence_generator, self)
        self._financial_statement_generator_instance = FinancialStatementGenerator(self.account_service, self.journal_service, self.fiscal_period_service, self.account_type_service, self.tax_code_service, self.company_settings_service, self.dimension_service)
        self._report_engine_instance = ReportEngine(self)
        self._customer_manager_instance = CustomerManager(customer_service=self.customer_service, account_service=self.account_service, currency_service=self.currency_repo_service, app_core=self)
        self._vendor_manager_instance = VendorManager( vendor_service=self.vendor_service, account_service=self.account_service, currency_service=self.currency_repo_service, app_core=self)
        self._product_manager_instance = ProductManager( product_service=self.product_service, account_service=self.account_service, tax_code_service=self.tax_code_service, app_core=self)
        self._sales_invoice_manager_instance = SalesInvoiceManager(sales_invoice_service=self.sales_invoice_service, customer_service=self.customer_service, product_service=self.product_service, tax_code_service=self.tax_code_service, tax_calculator=self.tax_calculator, sequence_service=self.sequence_service, account_service=self.account_service, configuration_service=self.configuration_service, app_core=self, inventory_movement_service=self.inventory_movement_service)
        self._purchase_invoice_manager_instance = PurchaseInvoiceManager( purchase_invoice_service=self.purchase_invoice_service, vendor_service=self.vendor_service, product_service=self.product_service, tax_code_service=self.tax_code_service, tax_calculator=self.tax_calculator, sequence_service=self.sequence_service, account_service=self.account_service, configuration_service=self.configuration_service, app_core=self, inventory_movement_service=self.inventory_movement_service)
        self._bank_account_manager_instance = BankAccountManager( bank_account_service=self.bank_account_service, account_service=self.account_service, currency_service=self.currency_repo_service, app_core=self)
        self._bank_transaction_manager_instance = BankTransactionManager( bank_transaction_service=self.bank_transaction_service, bank_account_service=self.bank_account_service, app_core=self)
        self._payment_manager_instance = PaymentManager( payment_service=self.payment_service, sequence_service=self.sequence_service, bank_account_service=self.bank_account_service, customer_service=self.customer_service, vendor_service=self.vendor_service, sales_invoice_service=self.sales_invoice_service, purchase_invoice_service=self.purchase_invoice_service, journal_entry_manager=self.journal_entry_manager, account_service=self.account_service, configuration_service=self.configuration_service, app_core=self)
        
        self.module_manager.load_all_modules() 
        self.logger.info("ApplicationCore startup complete.")

    async def shutdown(self): 
        self.logger.info("ApplicationCore shutting down...")
        await self.db_manager.close_connections()
        self.logger.info("ApplicationCore shutdown complete.")

    @property
    def current_user(self): 
        return self.security_manager.get_current_user()

    @property
    def account_service(self) -> AccountService: 
        if not self._account_service_instance: raise RuntimeError("AccountService not initialized.")
        return self._account_service_instance
    @property
    def journal_service(self) -> JournalService: 
        if not self._journal_service_instance: raise RuntimeError("JournalService not initialized.")
        return self._journal_service_instance
    @property
    def fiscal_period_service(self) -> FiscalPeriodService: 
        if not self._fiscal_period_service_instance: raise RuntimeError("FiscalPeriodService not initialized.")
        return self._fiscal_period_service_instance
    @property
    def fiscal_year_service(self) -> FiscalYearService: 
        if not self._fiscal_year_service_instance: raise RuntimeError("FiscalYearService not initialized.")
        return self._fiscal_year_service_instance
    @property
    def sequence_service(self) -> SequenceService: 
        if not self._sequence_service_instance: raise RuntimeError("SequenceService not initialized.")
        return self._sequence_service_instance
    @property
    def company_settings_service(self) -> CompanySettingsService: 
        if not self._company_settings_service_instance: raise RuntimeError("CompanySettingsService not initialized.")
        return self._company_settings_service_instance
    @property
    def configuration_service(self) -> ConfigurationService: 
        if not self._configuration_service_instance: raise RuntimeError("ConfigurationService not initialized.")
        return self._configuration_service_instance
    @property
    def tax_code_service(self) -> TaxCodeService: 
        if not self._tax_code_service_instance: raise RuntimeError("TaxCodeService not initialized.")
        return self._tax_code_service_instance
    @property
    def gst_return_service(self) -> GSTReturnService: 
        if not self._gst_return_service_instance: raise RuntimeError("GSTReturnService not initialized.")
        return self._gst_return_service_instance
    @property
    def account_type_service(self) -> AccountTypeService:  
        if not self._account_type_service_instance: raise RuntimeError("AccountTypeService not initialized.")
        return self._account_type_service_instance 
    @property
    def currency_repo_service(self) -> CurrencyRepoService: 
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyRepoService not initialized.")
        return self._currency_repo_service_instance 
    @property # Keep for existing manager compatibility
    def currency_service(self) -> CurrencyRepoService: 
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyService (CurrencyRepoService) not initialized.")
        return self._currency_repo_service_instance
    @property
    def exchange_rate_service(self) -> ExchangeRateService: 
        if not self._exchange_rate_service_instance: raise RuntimeError("ExchangeRateService not initialized.")
        return self._exchange_rate_service_instance 
    @property
    def dimension_service(self) -> DimensionService: 
        if not self._dimension_service_instance: raise RuntimeError("DimensionService not initialized.")
        return self._dimension_service_instance
    @property
    def customer_service(self) -> CustomerService: 
        if not self._customer_service_instance: raise RuntimeError("CustomerService not initialized.")
        return self._customer_service_instance
    @property
    def vendor_service(self) -> VendorService: 
        if not self._vendor_service_instance: raise RuntimeError("VendorService not initialized.")
        return self._vendor_service_instance
    @property
    def product_service(self) -> ProductService: 
        if not self._product_service_instance: raise RuntimeError("ProductService not initialized.")
        return self._product_service_instance
    @property
    def sales_invoice_service(self) -> SalesInvoiceService: 
        if not self._sales_invoice_service_instance: raise RuntimeError("SalesInvoiceService not initialized.")
        return self._sales_invoice_service_instance
    @property
    def purchase_invoice_service(self) -> PurchaseInvoiceService: 
        if not self._purchase_invoice_service_instance: raise RuntimeError("PurchaseInvoiceService not initialized.")
        return self._purchase_invoice_service_instance
    @property
    def inventory_movement_service(self) -> InventoryMovementService: 
        if not self._inventory_movement_service_instance: raise RuntimeError("InventoryMovementService not initialized.")
        return self._inventory_movement_service_instance
    @property
    def bank_account_service(self) -> BankAccountService: 
        if not self._bank_account_service_instance: raise RuntimeError("BankAccountService not initialized.")
        return self._bank_account_service_instance
    @property
    def bank_transaction_service(self) -> BankTransactionService: 
        if not self._bank_transaction_service_instance: raise RuntimeError("BankTransactionService not initialized.")
        return self._bank_transaction_service_instance
    @property
    def payment_service(self) -> PaymentService: 
        if not self._payment_service_instance: raise RuntimeError("PaymentService not initialized.")
        return self._payment_service_instance
    @property
    def audit_log_service(self) -> AuditLogService: 
        if not self._audit_log_service_instance: raise RuntimeError("AuditLogService not initialized.")
        return self._audit_log_service_instance

    @property
    def chart_of_accounts_manager(self) -> ChartOfAccountsManager: 
        if not self._coa_manager_instance: raise RuntimeError("ChartOfAccountsManager not initialized.")
        return self._coa_manager_instance
    @property # Alias for backward compatibility if some UI uses it
    def accounting_service(self) -> ChartOfAccountsManager: 
        return self.chart_of_accounts_manager
    @property
    def journal_entry_manager(self) -> JournalEntryManager: 
        if not self._je_manager_instance: raise RuntimeError("JournalEntryManager not initialized.")
        return self._je_manager_instance
    @property
    def fiscal_period_manager(self) -> FiscalPeriodManager: 
        if not self._fp_manager_instance: raise RuntimeError("FiscalPeriodManager not initialized.")
        return self._fp_manager_instance
    @property
    def currency_manager(self) -> CurrencyManager: 
        if not self._currency_manager_instance: raise RuntimeError("CurrencyManager not initialized.")
        return self._currency_manager_instance
    @property
    def gst_manager(self) -> GSTManager: 
        if not self._gst_manager_instance: raise RuntimeError("GSTManager not initialized.")
        return self._gst_manager_instance
    @property
    def tax_calculator(self) -> TaxCalculator: 
        if not self._tax_calculator_instance: raise RuntimeError("TaxCalculator not initialized.")
        return self._tax_calculator_instance
    @property
    def financial_statement_generator(self) -> FinancialStatementGenerator: 
        if not self._financial_statement_generator_instance: raise RuntimeError("FinancialStatementGenerator not initialized.")
        return self._financial_statement_generator_instance
    @property
    def report_engine(self) -> ReportEngine: 
        if not self._report_engine_instance: raise RuntimeError("ReportEngine not initialized.")
        return self._report_engine_instance
    @property
    def customer_manager(self) -> CustomerManager: 
        if not self._customer_manager_instance: raise RuntimeError("CustomerManager not initialized.")
        return self._customer_manager_instance
    @property
    def vendor_manager(self) -> VendorManager: 
        if not self._vendor_manager_instance: raise RuntimeError("VendorManager not initialized.")
        return self._vendor_manager_instance
    @property
    def product_manager(self) -> ProductManager: 
        if not self._product_manager_instance: raise RuntimeError("ProductManager not initialized.")
        return self._product_manager_instance
    @property
    def sales_invoice_manager(self) -> SalesInvoiceManager: 
        if not self._sales_invoice_manager_instance: raise RuntimeError("SalesInvoiceManager not initialized.")
        return self._sales_invoice_manager_instance
    @property
    def purchase_invoice_manager(self) -> PurchaseInvoiceManager: 
        if not self._purchase_invoice_manager_instance: raise RuntimeError("PurchaseInvoiceManager not initialized.")
        return self._purchase_invoice_manager_instance
    @property
    def bank_account_manager(self) -> BankAccountManager: 
        if not self._bank_account_manager_instance: raise RuntimeError("BankAccountManager not initialized.")
        return self._bank_account_manager_instance
    @property
    def bank_transaction_manager(self) -> BankTransactionManager: 
        if not self._bank_transaction_manager_instance: raise RuntimeError("BankTransactionManager not initialized.")
        return self._bank_transaction_manager_instance
    @property
    def payment_manager(self) -> PaymentManager: 
        if not self._payment_manager_instance: raise RuntimeError("PaymentManager not initialized.")
        return self._payment_manager_instance


```

# app/models/__init__.py
```py
# File: app/models/__init__.py
from .base import Base, TimestampMixin, UserAuditMixin

# Core schema models
from .core.user import User, Role, Permission 
from .core.company_setting import CompanySetting
from .core.configuration import Configuration
from .core.sequence import Sequence

# Accounting schema models
from .accounting.account_type import AccountType
from .accounting.currency import Currency 
from .accounting.exchange_rate import ExchangeRate 
from .accounting.account import Account 
from .accounting.fiscal_year import FiscalYear
from .accounting.fiscal_period import FiscalPeriod 
from .accounting.journal_entry import JournalEntry, JournalEntryLine 
from .accounting.recurring_pattern import RecurringPattern
from .accounting.dimension import Dimension 
from .accounting.budget import Budget, BudgetDetail 
from .accounting.tax_code import TaxCode 
from .accounting.gst_return import GSTReturn 
from .accounting.withholding_tax_certificate import WithholdingTaxCertificate

# Business schema models
from .business.customer import Customer
from .business.vendor import Vendor
from .business.product import Product
from .business.inventory_movement import InventoryMovement
from .business.sales_invoice import SalesInvoice, SalesInvoiceLine
from .business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine
from .business.bank_account import BankAccount
from .business.bank_transaction import BankTransaction
from .business.payment import Payment, PaymentAllocation
from .business.bank_reconciliation import BankReconciliation # New Import

# Audit schema models
from .audit.audit_log import AuditLog
from .audit.data_change_history import DataChangeHistory

__all__ = [
    "Base", "TimestampMixin", "UserAuditMixin",
    # Core
    "User", "Role", "Permission", 
    "CompanySetting", "Configuration", "Sequence",
    # Accounting
    "AccountType", "Currency", "ExchangeRate", "Account",
    "FiscalYear", "FiscalPeriod", "JournalEntry", "JournalEntryLine",
    "RecurringPattern", "Dimension", "Budget", "BudgetDetail",
    "TaxCode", "GSTReturn", "WithholdingTaxCertificate",
    # Business
    "Customer", "Vendor", "Product", "InventoryMovement",
    "SalesInvoice", "SalesInvoiceLine", "PurchaseInvoice", "PurchaseInvoiceLine",
    "BankAccount", "BankTransaction", "Payment", "PaymentAllocation",
    "BankReconciliation", # New Export
    # Audit
    "AuditLog", "DataChangeHistory",
]

```

# app/models/business/__init__.py
```py
# File: app/models/business/__init__.py
from .inventory_movement import InventoryMovement
from .sales_invoice import SalesInvoice, SalesInvoiceLine
from .purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine
from .bank_account import BankAccount
from .bank_transaction import BankTransaction
from .payment import Payment, PaymentAllocation
from .bank_reconciliation import BankReconciliation # New Import

__all__ = [
    "InventoryMovement", 
    "SalesInvoice", "SalesInvoiceLine",
    "PurchaseInvoice", "PurchaseInvoiceLine",
    "BankAccount", "BankTransaction",
    "Payment", "PaymentAllocation",
    "BankReconciliation", # New Export
]

```

# app/models/business/bank_account.py
```py
# File: app/models/business/bank_account.py
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account 
from app.models.accounting.currency import Currency 
from app.models.core.user import User
from typing import List, Optional, TYPE_CHECKING
import datetime
from decimal import Decimal

if TYPE_CHECKING:
    from app.models.business.bank_transaction import BankTransaction # For relationship type hint
    from app.models.business.payment import Payment # For relationship type hint
    from app.models.business.bank_reconciliation import BankReconciliation # New import

class BankAccount(Base, TimestampMixin):
    __tablename__ = 'bank_accounts'
    __table_args__ = {'schema': 'business'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_swift_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), nullable=False)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    current_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    last_reconciled_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    last_reconciled_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True) # New field
    gl_account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    currency: Mapped["Currency"] = relationship("Currency")
    gl_account: Mapped["Account"] = relationship("Account", back_populates="bank_account_links")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
    
    bank_transactions: Mapped[List["BankTransaction"]] = relationship("BankTransaction", back_populates="bank_account") 
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="bank_account") 
    reconciliations: Mapped[List["BankReconciliation"]] = relationship("BankReconciliation", order_by="desc(BankReconciliation.statement_date)", back_populates="bank_account")

# This back_populates was already in the base file for BankAccount, ensuring it's correctly set up.
# Account.bank_account_links = relationship("BankAccount", back_populates="gl_account") 

```

# app/models/business/bank_transaction.py
```py
# File: app/models/business/bank_transaction.py
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB 
from app.models.base import Base, TimestampMixin
from app.models.business.bank_account import BankAccount
from app.models.core.user import User
from app.models.accounting.journal_entry import JournalEntry
# from app.models.business.bank_reconciliation import BankReconciliation # Forward reference if problematic
import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.business.bank_reconciliation import BankReconciliation # For type hint

class BankTransaction(Base, TimestampMixin):
    __tablename__ = 'bank_transactions'
    __table_args__ = (
        CheckConstraint("transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Interest', 'Fee', 'Adjustment')", name='ck_bank_transactions_type'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_account_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.bank_accounts.id'), nullable=False)
    transaction_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    value_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False) 
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False) 
    is_reconciled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reconciled_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    statement_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True) 
    statement_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) 
    is_from_statement: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_statement_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # New field for linking to bank_reconciliations table
    reconciled_bank_reconciliation_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('business.bank_reconciliations.id'), nullable=True)

    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=True)
    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)
    
    # Relationships
    bank_account: Mapped["BankAccount"] = relationship("BankAccount", back_populates="bank_transactions")
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry") 
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
    
    reconciliation_instance: Mapped[Optional["BankReconciliation"]] = relationship(
        "BankReconciliation", 
        back_populates="reconciled_transactions",
        foreign_keys=[reconciled_bank_reconciliation_id]
    )

    def __repr__(self) -> str:
        return f"<BankTransaction(id={self.id}, date={self.transaction_date}, type='{self.transaction_type}', amount={self.amount})>"

```

# app/models/business/bank_reconciliation.py
```py
# File: app/models/business/bank_reconciliation.py
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import datetime
from decimal import Decimal
from typing import Optional, List

from app.models.base import Base, TimestampMixin # UserAuditMixin will be handled by direct FKs for created_by
from app.models.business.bank_account import BankAccount
from app.models.core.user import User
# from app.models.business.bank_transaction import BankTransaction # Needed for back_populates

class BankReconciliation(Base, TimestampMixin):
    __tablename__ = 'bank_reconciliations'
    __table_args__ = (
        UniqueConstraint('bank_account_id', 'statement_date', name='uq_bank_reconciliation_account_statement_date'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_account_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.bank_accounts.id'), nullable=False)
    statement_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    statement_ending_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    calculated_book_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    reconciled_difference: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    reconciliation_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    # updated_by is implicitly handled by TimestampMixin if updated_at is sufficient. 
    # If explicit updated_by is needed, add UserAuditMixin or direct fields. Schema has created_by only.

    # Relationships
    bank_account: Mapped["BankAccount"] = relationship("BankAccount") # back_populates on BankAccount if needed
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    
    # Link to BankTransaction records reconciled by this instance
    reconciled_transactions: Mapped[List["BankTransaction"]] = relationship(
        "BankTransaction", 
        back_populates="reconciliation_instance"
    ) # type: ignore

    def __repr__(self) -> str:
        return f"<BankReconciliation(id={self.id}, bank_account_id={self.bank_account_id}, stmt_date={self.statement_date}, diff={self.reconciled_difference})>"

# Add back_populates to BankAccount and BankTransaction
BankAccount.reconciliations = relationship("BankReconciliation", order_by=BankReconciliation.statement_date.desc(), back_populates="bank_account") # type: ignore

# BankTransaction model needs to be imported here to add the relationship,
# or this relationship definition should be moved to bank_transaction.py to avoid circular imports.
# For now, let's assume BankTransaction will be updated separately or this implies it.
# This is better defined in bank_transaction.py.
# from app.models.business.bank_transaction import BankTransaction
# BankTransaction.reconciliation_instance = relationship("BankReconciliation", back_populates="reconciled_transactions")

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
from app.services.business_services import BankTransactionService, BankAccountService
from app.utils.result import Result
from app.utils.pydantic_models import (
    BankTransactionCreateData, BankTransactionSummaryData
)
from app.common.enums import BankTransactionTypeEnum

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from sqlalchemy.ext.asyncio import AsyncSession

class BankTransactionManager:
    def __init__(self,
                 bank_transaction_service: BankTransactionService,
                 bank_account_service: BankAccountService, 
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
    ) -> Result[Dict[str, int]]:
        imported_count = 0; skipped_duplicates_count = 0; failed_rows_count = 0; zero_amount_skipped_count = 0; total_rows_processed = 0
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
                        total_rows_processed += 1; raw_row_dict_for_json: Dict[str, str] = {}
                        try:
                            def get_field_value(field_key: str) -> Optional[str]:
                                specifier = column_mapping.get(field_key); 
                                if specifier is None: return None; val: Optional[str] = None
                                if using_header_names and isinstance(raw_row_data, dict): val = raw_row_data.get(str(specifier))
                                elif not using_header_names and isinstance(raw_row_data, list) and isinstance(specifier, int):
                                    if 0 <= specifier < len(raw_row_data): val = raw_row_data[specifier]
                                return val.strip() if val else None
                            if using_header_names and isinstance(raw_row_data, dict): raw_row_dict_for_json = {k: str(v) for k,v in raw_row_data.items()}
                            elif isinstance(raw_row_data, list): raw_row_dict_for_json = {f"column_{i}": str(val) for i, val in enumerate(raw_row_data)}
                            else: raw_row_dict_for_json = {"error": "Unknown row format"}
                            transaction_date_str = get_field_value("date"); description_str = get_field_value("description")
                            if not transaction_date_str or not description_str: self.logger.warning(f"CSV Import (Row {row_num}): Skipping due to missing date or description."); failed_rows_count += 1; continue
                            try: parsed_transaction_date = datetime.strptime(transaction_date_str, date_format_str).date()
                            except ValueError: self.logger.warning(f"CSV Import (Row {row_num}): Invalid transaction date format '{transaction_date_str}'. Expected '{date_format_str}'. Skipping."); failed_rows_count += 1; continue
                            value_date_str = get_field_value("value_date"); parsed_value_date: Optional[date] = None
                            if value_date_str:
                                try: parsed_value_date = datetime.strptime(value_date_str, date_format_str).date()
                                except ValueError: self.logger.warning(f"CSV Import (Row {row_num}): Invalid value date format '{value_date_str}'.")
                            final_bt_amount = Decimal(0)
                            if use_single_amount_col:
                                amount_str = get_field_value("amount")
                                if not amount_str: self.logger.warning(f"CSV Import (Row {row_num}): Single amount column specified but value is missing. Skipping."); failed_rows_count += 1; continue
                                try:
                                    parsed_csv_amount = Decimal(amount_str.replace(',', ''))
                                    if debit_is_negative: final_bt_amount = parsed_csv_amount
                                    else: final_bt_amount = -parsed_csv_amount
                                except InvalidOperation: self.logger.warning(f"CSV Import (Row {row_num}): Invalid amount '{amount_str}' in single amount column. Skipping."); failed_rows_count += 1; continue
                            else:
                                debit_str = get_field_value("debit"); credit_str = get_field_value("credit")
                                try:
                                    parsed_debit = Decimal(debit_str.replace(',', '')) if debit_str else Decimal(0)
                                    parsed_credit = Decimal(credit_str.replace(',', '')) if credit_str else Decimal(0)
                                    final_bt_amount = parsed_credit - parsed_debit
                                except InvalidOperation: self.logger.warning(f"CSV Import (Row {row_num}): Invalid debit '{debit_str}' or credit '{credit_str}' amount. Skipping."); failed_rows_count += 1; continue
                            if abs(final_bt_amount) < Decimal("0.005"): self.logger.info(f"CSV Import (Row {row_num}): Skipping due to zero net amount."); zero_amount_skipped_count += 1; continue
                            reference_str = get_field_value("reference")
                            stmt_dup = select(BankTransaction).where(BankTransaction.bank_account_id == bank_account_id,BankTransaction.transaction_date == parsed_transaction_date,BankTransaction.amount == final_bt_amount,BankTransaction.description == description_str,BankTransaction.is_from_statement == True)
                            existing_dup_res = await session.execute(stmt_dup)
                            if existing_dup_res.scalars().first(): self.logger.info(f"CSV Import (Row {row_num}): Skipping as likely duplicate."); skipped_duplicates_count += 1; continue
                            txn_type_enum = BankTransactionTypeEnum.DEPOSIT if final_bt_amount > 0 else BankTransactionTypeEnum.WITHDRAWAL
                            txn_orm = BankTransaction(bank_account_id=bank_account_id,transaction_date=parsed_transaction_date,value_date=parsed_value_date,transaction_type=txn_type_enum.value,description=description_str,reference=reference_str if reference_str else None,amount=final_bt_amount,is_reconciled=False,is_from_statement=True,raw_statement_data=raw_row_dict_for_json, created_by_user_id=user_id,updated_by_user_id=user_id)
                            session.add(txn_orm); imported_count += 1
                        except Exception as e_row: self.logger.error(f"CSV Import (Row {row_num}): Unexpected error: {e_row}", exc_info=True); failed_rows_count += 1
            summary = {"total_rows_in_file": total_rows_processed, "imported_count": imported_count, "skipped_duplicates_count": skipped_duplicates_count, "failed_rows_count": failed_rows_count, "zero_amount_skipped_count": zero_amount_skipped_count}
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
                bank_account_id=bank_account_id,
                end_date=statement_end_date, 
                is_reconciled=False,
                is_from_statement_filter=True,
                page=1, page_size=page_size_override 
            )
            if not statement_items_result.is_success:
                return Result.failure(["Failed to fetch statement items for reconciliation."] + (statement_items_result.errors or []))
            
            statement_lines = statement_items_result.value or []

            system_items_result = await self.get_transactions_for_bank_account(
                bank_account_id=bank_account_id,
                end_date=statement_end_date, 
                is_reconciled=False,
                is_from_statement_filter=False,
                page=1, page_size=page_size_override
            )
            if not system_items_result.is_success:
                return Result.failure(["Failed to fetch system transactions for reconciliation."] + (system_items_result.errors or []))
            
            system_txns = system_items_result.value or []
            
            return Result.success((statement_lines, system_txns))

        except Exception as e:
            self.logger.error(f"Error fetching transactions for matching UI (Account ID: {bank_account_id}): {e}", exc_info=True)
            return Result.failure([f"Unexpected error fetching transactions for reconciliation: {str(e)}"])

```

# app/accounting/journal_entry_manager.py
```py
# File: app/accounting/journal_entry_manager.py
from typing import List, Optional, Any, Dict, TYPE_CHECKING
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.orm import selectinload

from app.models import JournalEntry, JournalEntryLine, RecurringPattern, FiscalPeriod, Account
from app.models.business.bank_account import BankAccount # New import
from app.models.business.bank_transaction import BankTransaction # New import
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
# SequenceGenerator is initialized in ApplicationCore and passed if needed, or app_core.sequence_service used
from app.utils.result import Result
from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData 
from app.common.enums import JournalTypeEnum, BankTransactionTypeEnum # New import

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    # Removed SequenceGenerator from here, will use app_core.sequence_service if directly needed.
    # However, sequence generation is handled by DB function now, called via db_manager.

class JournalEntryManager:
    def __init__(self, 
                 journal_service: JournalService, 
                 account_service: AccountService, 
                 fiscal_period_service: FiscalPeriodService, 
                 # sequence_generator: SequenceGenerator, # Replaced by direct DB call
                 app_core: "ApplicationCore"):
        self.journal_service = journal_service
        self.account_service = account_service
        self.fiscal_period_service = fiscal_period_service
        # self.sequence_generator = sequence_generator 
        self.app_core = app_core
        self.logger = app_core.logger

    async def create_journal_entry(self, entry_data: JournalEntryData, session: Optional[AsyncSession] = None) -> Result[JournalEntry]:
        async def _create_je_logic(current_session: AsyncSession):
            fiscal_period_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= entry_data.entry_date, FiscalPeriod.end_date >= entry_data.entry_date, FiscalPeriod.status == 'Open')
            fiscal_period_res = await current_session.execute(fiscal_period_stmt); fiscal_period = fiscal_period_res.scalars().first()
            if not fiscal_period: return Result.failure([f"No open fiscal period for entry date {entry_data.entry_date} or period not open."])
            
            # Use DB function for sequence number
            entry_no_str = await self.app_core.db_manager.execute_scalar("SELECT core.get_next_sequence_value($1);", "journal_entry", session=current_session) # Pass session
            if not entry_no_str: return Result.failure(["Failed to generate journal entry number."])
            
            current_user_id = entry_data.user_id
            journal_entry_orm = JournalEntry(entry_no=entry_no_str, journal_type=entry_data.journal_type, entry_date=entry_data.entry_date, fiscal_period_id=fiscal_period.id, description=entry_data.description, reference=entry_data.reference, is_recurring=entry_data.is_recurring, recurring_pattern_id=entry_data.recurring_pattern_id, is_posted=False, source_type=entry_data.source_type, source_id=entry_data.source_id, created_by_user_id=current_user_id, updated_by_user_id=current_user_id)
            for i, line_dto in enumerate(entry_data.lines, 1):
                account_stmt = select(Account).where(Account.id == line_dto.account_id); account_res = await current_session.execute(account_stmt); account = account_res.scalars().first()
                if not account or not account.is_active: return Result.failure([f"Invalid or inactive account ID {line_dto.account_id} on line {i}."])
                line_orm = JournalEntryLine(line_number=i, account_id=line_dto.account_id, description=line_dto.description, debit_amount=line_dto.debit_amount, credit_amount=line_dto.credit_amount, currency_code=line_dto.currency_code, exchange_rate=line_dto.exchange_rate, tax_code=line_dto.tax_code, tax_amount=line_dto.tax_amount, dimension1_id=line_dto.dimension1_id, dimension2_id=line_dto.dimension2_id)
                journal_entry_orm.lines.append(line_orm)
            current_session.add(journal_entry_orm); await current_session.flush(); await current_session.refresh(journal_entry_orm)
            if journal_entry_orm.lines: await current_session.refresh(journal_entry_orm, attribute_names=['lines'])
            return Result.success(journal_entry_orm)
        if session: return await _create_je_logic(session)
        else:
            try:
                async with self.app_core.db_manager.session() as new_session: # type: ignore
                    return await _create_je_logic(new_session)
            except Exception as e: 
                self.logger.error(f"Error creating JE with new session: {e}", exc_info=True)
                return Result.failure([f"Failed to save JE: {str(e)}"])

    async def update_journal_entry(self, entry_id: int, entry_data: JournalEntryData) -> Result[JournalEntry]:
        # ... (content as in project_codebase_files_set-2.md, unchanged for this step)
        async with self.app_core.db_manager.session() as session: # type: ignore
            existing_entry = await session.get(JournalEntry, entry_id, options=[selectinload(JournalEntry.lines)])
            if not existing_entry: return Result.failure([f"JE ID {entry_id} not found for update."])
            if existing_entry.is_posted: return Result.failure([f"Cannot update posted JE: {existing_entry.entry_no}."])
            fp_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= entry_data.entry_date, FiscalPeriod.end_date >= entry_data.entry_date, FiscalPeriod.status == 'Open')
            fp_res = await session.execute(fp_stmt); fiscal_period = fp_res.scalars().first()
            if not fiscal_period: return Result.failure([f"No open fiscal period for new entry date {entry_data.entry_date} or period not open."])
            current_user_id = entry_data.user_id
            existing_entry.journal_type = entry_data.journal_type; existing_entry.entry_date = entry_data.entry_date
            existing_entry.fiscal_period_id = fiscal_period.id; existing_entry.description = entry_data.description
            existing_entry.reference = entry_data.reference; existing_entry.is_recurring = entry_data.is_recurring
            existing_entry.recurring_pattern_id = entry_data.recurring_pattern_id
            existing_entry.source_type = entry_data.source_type; existing_entry.source_id = entry_data.source_id
            existing_entry.updated_by_user_id = current_user_id
            for line in list(existing_entry.lines): await session.delete(line)
            existing_entry.lines.clear(); await session.flush() 
            new_lines_orm: List[JournalEntryLine] = []
            for i, line_dto in enumerate(entry_data.lines, 1):
                acc_stmt = select(Account).where(Account.id == line_dto.account_id); acc_res = await session.execute(acc_stmt); account = acc_res.scalars().first()
                if not account or not account.is_active: raise ValueError(f"Invalid or inactive account ID {line_dto.account_id} on line {i} during update.")
                new_lines_orm.append(JournalEntryLine(line_number=i, account_id=line_dto.account_id, description=line_dto.description, debit_amount=line_dto.debit_amount, credit_amount=line_dto.credit_amount, currency_code=line_dto.currency_code, exchange_rate=line_dto.exchange_rate, tax_code=line_dto.tax_code, tax_amount=line_dto.tax_amount, dimension1_id=line_dto.dimension1_id, dimension2_id=line_dto.dimension2_id))
            existing_entry.lines.extend(new_lines_orm); session.add(existing_entry) 
            try:
                await session.flush(); await session.refresh(existing_entry)
                if existing_entry.lines: await session.refresh(existing_entry, attribute_names=['lines'])
                return Result.success(existing_entry)
            except Exception as e: self.logger.error(f"Error updating JE ID {entry_id}: {e}", exc_info=True); return Result.failure([f"Failed to update JE: {str(e)}"])

    async def post_journal_entry(self, entry_id: int, user_id: int, session: Optional[AsyncSession] = None) -> Result[JournalEntry]:
        async def _post_je_logic(current_session: AsyncSession):
            # Load entry with lines and their accounts for bank transaction creation
            entry = await current_session.get(
                JournalEntry, entry_id, 
                options=[selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account)]
            )
            if not entry: return Result.failure([f"JE ID {entry_id} not found."])
            if entry.is_posted: return Result.failure([f"JE '{entry.entry_no}' is already posted."])
            
            fiscal_period = await current_session.get(FiscalPeriod, entry.fiscal_period_id)
            if not fiscal_period or fiscal_period.status != 'Open': 
                return Result.failure([f"Cannot post. Fiscal period not open. Status: {fiscal_period.status if fiscal_period else 'Unknown'}."])
            
            entry.is_posted = True
            entry.updated_by_user_id = user_id
            current_session.add(entry)
            await current_session.flush() # Flush to ensure entry.id is available if it's a new entry being posted in same transaction
            
            # --- Create BankTransaction if JE affects a bank-linked GL account ---
            for line in entry.lines:
                if line.account and line.account.is_bank_account:
                    # Find the BankAccount ORM linked to this GL account
                    bank_account_stmt = select(BankAccount).where(BankAccount.gl_account_id == line.account_id)
                    bank_account_res = await current_session.execute(bank_account_stmt)
                    linked_bank_account = bank_account_res.scalars().first()

                    if linked_bank_account:
                        # Determine transaction type and amount for BankTransaction
                        # BankTransaction.amount: positive for inflow, negative for outflow
                        # JE Line: debit to bank GL account = inflow; credit to bank GL account = outflow
                        bank_txn_amount = line.debit_amount - line.credit_amount
                        
                        bank_txn_type_enum: BankTransactionTypeEnum
                        if bank_txn_amount > Decimal(0):
                            bank_txn_type_enum = BankTransactionTypeEnum.DEPOSIT # Or ADJUSTMENT
                        elif bank_txn_amount < Decimal(0):
                            bank_txn_type_enum = BankTransactionTypeEnum.WITHDRAWAL # Or ADJUSTMENT
                        else: # Zero amount line affecting bank, skip BankTransaction
                            continue 

                        new_bank_txn = BankTransaction(
                            bank_account_id=linked_bank_account.id,
                            transaction_date=entry.entry_date,
                            value_date=entry.entry_date, # Default value date to transaction date
                            transaction_type=bank_txn_type_enum.value,
                            description=f"JE: {entry.entry_no} - {line.description or entry.description or 'Journal Posting'}",
                            reference=entry.entry_no,
                            amount=bank_txn_amount,
                            is_from_statement=False, # System generated
                            is_reconciled=False,
                            journal_entry_id=entry.id,
                            created_by_user_id=user_id,
                            updated_by_user_id=user_id
                        )
                        current_session.add(new_bank_txn)
                        self.logger.info(f"Auto-created BankTransaction for JE line {line.id} (Account: {line.account.code}) linked to Bank Account {linked_bank_account.id}")
                    else:
                        self.logger.warning(f"JE line {line.id} affects GL account {line.account.code} which is_bank_account=True, but no BankAccount record is linked to it. No BankTransaction created.")
            
            await current_session.flush() # Flush again to save BankTransaction and get its ID if needed
            await current_session.refresh(entry) # Refresh entry to reflect any changes from flush
            return Result.success(entry)

        if session: return await _post_je_logic(session)
        else:
            try:
                async with self.app_core.db_manager.session() as new_session: # type: ignore
                    return await _post_je_logic(new_session)
            except Exception as e: 
                self.logger.error(f"Error posting JE ID {entry_id} with new session: {e}", exc_info=True)
                return Result.failure([f"Failed to post JE: {str(e)}"])

    async def reverse_journal_entry(self, entry_id: int, reversal_date: date, description: Optional[str], user_id: int) -> Result[JournalEntry]:
        # ... (content as in project_codebase_files_set-2.md, but ensure sequence_generator is not used if DB func handles it)
        async with self.app_core.db_manager.session() as session: # type: ignore
            original_entry = await session.get(JournalEntry, entry_id, options=[selectinload(JournalEntry.lines)])
            if not original_entry: return Result.failure([f"JE ID {entry_id} not found for reversal."])
            if not original_entry.is_posted: return Result.failure(["Only posted entries can be reversed."])
            if original_entry.is_reversed or original_entry.reversing_entry_id is not None: return Result.failure([f"Entry '{original_entry.entry_no}' is already reversed."])
            reversal_fp_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= reversal_date, FiscalPeriod.end_date >= reversal_date, FiscalPeriod.status == 'Open')
            reversal_fp_res = await session.execute(reversal_fp_stmt); reversal_fiscal_period = reversal_fp_res.scalars().first()
            if not reversal_fiscal_period: return Result.failure([f"No open fiscal period for reversal date {reversal_date} or period not open."])
            
            # Reversal entry_no will be generated by create_journal_entry via DB function
            reversal_lines_dto: List[JournalEntryLineData] = []
            for orig_line in original_entry.lines:
                reversal_lines_dto.append(JournalEntryLineData(account_id=orig_line.account_id, description=f"Reversal: {orig_line.description or ''}", debit_amount=orig_line.credit_amount, credit_amount=orig_line.debit_amount, currency_code=orig_line.currency_code, exchange_rate=orig_line.exchange_rate, tax_code=orig_line.tax_code, tax_amount=-orig_line.tax_amount if orig_line.tax_amount is not None else Decimal(0), dimension1_id=orig_line.dimension1_id, dimension2_id=orig_line.dimension2_id))
            reversal_je_data = JournalEntryData(journal_type=original_entry.journal_type, entry_date=reversal_date, description=description or f"Reversal of entry {original_entry.entry_no}", reference=f"REV:{original_entry.entry_no}", is_posted=False, source_type="JournalEntryReversalSource", source_id=original_entry.id, user_id=user_id, lines=reversal_lines_dto)
            create_reversal_result = await self.create_journal_entry(reversal_je_data, session=session)
            if not create_reversal_result.is_success or not create_reversal_result.value: return Result.failure(["Failed to create reversal JE."] + create_reversal_result.errors)
            reversal_je_orm = create_reversal_result.value
            original_entry.is_reversed = True; original_entry.reversing_entry_id = reversal_je_orm.id
            original_entry.updated_by_user_id = user_id; session.add(original_entry)
            try:
                await session.flush(); await session.refresh(reversal_je_orm)
                if reversal_je_orm.lines: await session.refresh(reversal_je_orm, attribute_names=['lines'])
                return Result.success(reversal_je_orm)
            except Exception as e: self.logger.error(f"Error reversing JE ID {entry_id} (flush/commit stage): {e}", exc_info=True); return Result.failure([f"Failed to finalize reversal: {str(e)}"])

    def _calculate_next_generation_date(self, last_date: date, frequency: str, interval: int, day_of_month: Optional[int] = None, day_of_week: Optional[int] = None) -> date:
        # ... (content as in project_codebase_files_set-2.md, unchanged)
        next_date = last_date
        if frequency == 'Monthly':
            next_date = last_date + relativedelta(months=interval)
            if day_of_month:
                try: next_date = next_date.replace(day=day_of_month)
                except ValueError: next_date = next_date + relativedelta(day=31) 
        elif frequency == 'Yearly':
            next_date = last_date + relativedelta(years=interval)
            if day_of_month:
                try: next_date = next_date.replace(day=day_of_month, month=last_date.month)
                except ValueError: next_date = next_date.replace(month=last_date.month) + relativedelta(day=31)
        elif frequency == 'Weekly':
            next_date = last_date + relativedelta(weeks=interval)
            if day_of_week is not None: 
                 current_weekday = next_date.weekday() 
                 days_to_add = (day_of_week - current_weekday + 7) % 7
                 next_date += timedelta(days=days_to_add)
        elif frequency == 'Daily': next_date = last_date + relativedelta(days=interval)
        elif frequency == 'Quarterly':
            next_date = last_date + relativedelta(months=interval * 3)
            if day_of_month:
                try: next_date = next_date.replace(day=day_of_month)
                except ValueError: next_date = next_date + relativedelta(day=31)
        else: raise NotImplementedError(f"Frequency '{frequency}' not supported for next date calculation.")
        return next_date

    async def generate_recurring_entries(self, as_of_date: date, user_id: int) -> List[Result[JournalEntry]]:
        # ... (content as in project_codebase_files_set-2.md, unchanged)
        patterns_due: List[RecurringPattern] = await self.journal_service.get_recurring_patterns_due(as_of_date); generated_results: List[Result[JournalEntry]] = []
        for pattern in patterns_due:
            if not pattern.template_journal_entry: self.logger.error(f"Template JE not loaded for pattern ID {pattern.id}. Skipping."); generated_results.append(Result.failure([f"Template JE not loaded for pattern '{pattern.name}'."])); continue
            entry_date_for_new_je = pattern.next_generation_date; 
            if not entry_date_for_new_je : continue 
            template_entry = pattern.template_journal_entry
            new_je_lines_data = [JournalEntryLineData(account_id=line.account_id, description=line.description, debit_amount=line.debit_amount, credit_amount=line.credit_amount, currency_code=line.currency_code, exchange_rate=line.exchange_rate, tax_code=line.tax_code, tax_amount=line.tax_amount, dimension1_id=line.dimension1_id, dimension2_id=line.dimension2_id) for line in template_entry.lines]
            new_je_data = JournalEntryData(journal_type=template_entry.journal_type, entry_date=entry_date_for_new_je, description=f"{pattern.description or template_entry.description or ''} (Recurring - {pattern.name})", reference=template_entry.reference, user_id=user_id, lines=new_je_lines_data, recurring_pattern_id=pattern.id, source_type="RecurringPattern", source_id=pattern.id)
            create_result = await self.create_journal_entry(new_je_data); generated_results.append(create_result)
            if create_result.is_success:
                async with self.app_core.db_manager.session() as session: # type: ignore
                    pattern_to_update = await session.get(RecurringPattern, pattern.id)
                    if pattern_to_update:
                        pattern_to_update.last_generated_date = entry_date_for_new_je
                        try:
                            next_gen = self._calculate_next_generation_date(pattern_to_update.last_generated_date, pattern_to_update.frequency, pattern_to_update.interval_value, pattern_to_update.day_of_month, pattern_to_update.day_of_week)
                            if pattern_to_update.end_date and next_gen > pattern_to_update.end_date: pattern_to_update.next_generation_date = None; pattern_to_update.is_active = False 
                            else: pattern_to_update.next_generation_date = next_gen
                        except NotImplementedError: pattern_to_update.next_generation_date = None; pattern_to_update.is_active = False; self.logger.warning(f"Next gen date calc not implemented for pattern {pattern_to_update.name}, deactivating.") # type: ignore
                        pattern_to_update.updated_by_user_id = user_id; session.add(pattern_to_update); await session.commit()
                    else: self.logger.error(f"Failed to re-fetch pattern ID {pattern.id} for update after recurring JE generation.") 
        return generated_results

    async def get_journal_entry_for_dialog(self, entry_id: int) -> Optional[JournalEntry]:
        # ... (content as in project_codebase_files_set-2.md, unchanged)
        return await self.journal_service.get_by_id(entry_id)

    async def get_journal_entries_for_listing(self, filters: Optional[Dict[str, Any]] = None) -> Result[List[Dict[str, Any]]]:
        # ... (content as in project_codebase_files_set-2.md, unchanged)
        filters = filters or {}
        try:
            summary_data = await self.journal_service.get_all_summary(start_date_filter=filters.get("start_date"),end_date_filter=filters.get("end_date"),status_filter=filters.get("status"),entry_no_filter=filters.get("entry_no"),description_filter=filters.get("description"),journal_type_filter=filters.get("journal_type"))
            return Result.success(summary_data)
        except Exception as e: self.logger.error(f"Error fetching JE summaries for listing: {e}", exc_info=True); return Result.failure([f"Failed to retrieve journal entry summaries: {str(e)}"])

```

# app/common/enums.py
```py
# File: app/common/enums.py
# (Content as previously generated, verified)
from enum import Enum

class AccountCategory(Enum): 
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"

class AccountTypeEnum(Enum): # Matches AccountCategory for now, can diverge
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"


class JournalTypeEnum(Enum): 
    GENERAL = "General" 
    SALES = "Sales"
    PURCHASE = "Purchase"
    CASH_RECEIPT = "Cash Receipt" 
    CASH_DISBURSEMENT = "Cash Disbursement" 
    PAYROLL = "Payroll"
    OPENING_BALANCE = "Opening Balance"
    ADJUSTMENT = "Adjustment"

class FiscalPeriodTypeEnum(Enum): 
    MONTH = "Month"
    QUARTER = "Quarter"
    YEAR = "Year" 

class FiscalPeriodStatusEnum(Enum): 
    OPEN = "Open"
    CLOSED = "Closed"
    ARCHIVED = "Archived"

class TaxTypeEnum(Enum): 
    GST = "GST"
    INCOME_TAX = "Income Tax"
    WITHHOLDING_TAX = "Withholding Tax"

class ProductTypeEnum(Enum): 
    INVENTORY = "Inventory"
    SERVICE = "Service"
    NON_INVENTORY = "Non-Inventory"

class GSTReturnStatusEnum(Enum): 
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    AMENDED = "Amended"

class InventoryMovementTypeEnum(Enum): 
    PURCHASE = "Purchase"
    SALE = "Sale"
    ADJUSTMENT = "Adjustment"
    TRANSFER = "Transfer"
    RETURN = "Return"
    OPENING = "Opening"

class InvoiceStatusEnum(Enum): 
    DRAFT = "Draft"
    APPROVED = "Approved"
    SENT = "Sent" 
    PARTIALLY_PAID = "Partially Paid"
    PAID = "Paid"
    OVERDUE = "Overdue"
    VOIDED = "Voided"
    DISPUTED = "Disputed" # Added for Purchase Invoices

class BankTransactionTypeEnum(Enum): 
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"
    TRANSFER = "Transfer"
    INTEREST = "Interest"
    FEE = "Fee"
    ADJUSTMENT = "Adjustment"

class PaymentTypeEnum(Enum): 
    CUSTOMER_PAYMENT = "Customer Payment"
    VENDOR_PAYMENT = "Vendor Payment"
    REFUND = "Refund"
    CREDIT_NOTE_APPLICATION = "Credit Note" # Application of a credit note to an invoice
    OTHER = "Other"

class PaymentMethodEnum(Enum): 
    CASH = "Cash"
    CHECK = "Check"
    BANK_TRANSFER = "Bank Transfer"
    CREDIT_CARD = "Credit Card"
    GIRO = "GIRO"
    PAYNOW = "PayNow"
    OTHER = "Other"

class PaymentEntityTypeEnum(Enum): 
    CUSTOMER = "Customer"
    VENDOR = "Vendor"
    OTHER = "Other"

class PaymentStatusEnum(Enum): 
    DRAFT = "Draft"
    APPROVED = "Approved"
    COMPLETED = "Completed" # After reconciliation or bank confirmation for some methods
    VOIDED = "Voided"
    RETURNED = "Returned" # E.g. bounced cheque

class PaymentAllocationDocTypeEnum(Enum): 
    SALES_INVOICE = "Sales Invoice"
    PURCHASE_INVOICE = "Purchase Invoice"
    CREDIT_NOTE = "Credit Note"
    DEBIT_NOTE = "Debit Note"
    OTHER = "Other"

class WHCertificateStatusEnum(Enum): # Withholding Tax Certificate Status
    DRAFT = "Draft"
    ISSUED = "Issued"
    VOIDED = "Voided"

class DataChangeTypeEnum(Enum): # For Audit Log
    INSERT = "Insert"
    UPDATE = "Update"
    DELETE = "Delete"

class RecurringFrequencyEnum(Enum): # For Recurring Journal Entries
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    YEARLY = "Yearly"

```

# app/common/__init__.py
```py
# File: app/common/__init__.py
# (Content as previously generated)
from .enums import (
    AccountCategory, AccountTypeEnum, JournalTypeEnum, FiscalPeriodTypeEnum, 
    FiscalPeriodStatusEnum, TaxTypeEnum, ProductTypeEnum, GSTReturnStatusEnum, 
    InventoryMovementTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum,
    PaymentTypeEnum, PaymentMethodEnum, PaymentEntityTypeEnum, PaymentStatusEnum,
    PaymentAllocationDocTypeEnum, WHCertificateStatusEnum, DataChangeTypeEnum, 
    RecurringFrequencyEnum
)

__all__ = [
    "AccountCategory", "AccountTypeEnum", "JournalTypeEnum", "FiscalPeriodTypeEnum", 
    "FiscalPeriodStatusEnum", "TaxTypeEnum", "ProductTypeEnum", "GSTReturnStatusEnum", 
    "InventoryMovementTypeEnum", "InvoiceStatusEnum", "BankTransactionTypeEnum",
    "PaymentTypeEnum", "PaymentMethodEnum", "PaymentEntityTypeEnum", "PaymentStatusEnum",
    "PaymentAllocationDocTypeEnum", "WHCertificateStatusEnum", "DataChangeTypeEnum", 
    "RecurringFrequencyEnum"
]

```

# resources/icons/import_csv.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M6 2h9l5 5v13H6V2zm8 0v5h5l-5-5zM12 18l-4-4h3v-5h2v5h3l-4 4z"/>
</svg>

```

# resources/resources.qrc
```qrc
<!DOCTYPE RCC><RCC version="1.0"> 
<qresource prefix="/">
    <file alias="icons/dashboard.svg">icons/dashboard.svg</file>
    <file alias="icons/accounting.svg">icons/accounting.svg</file>
    <file alias="icons/customers.svg">icons/customers.svg</file>
    <file alias="icons/vendors.svg">icons/vendors.svg</file>
    <file alias="icons/product.svg">icons/product.svg</file>
    <file alias="icons/banking.svg">icons/banking.svg</file>
    <file alias="icons/reports.svg">icons/reports.svg</file>
    <file alias="icons/settings.svg">icons/settings.svg</file>
    <file alias="icons/new_company.svg">icons/new_company.svg</file>
    <file alias="icons/open_company.svg">icons/open_company.svg</file>
    <file alias="icons/backup.svg">icons/backup.svg</file>
    <file alias="icons/restore.svg">icons/restore.svg</file>
    <file alias="icons/exit.svg">icons/exit.svg</file>
    <file alias="icons/preferences.svg">icons/preferences.svg</file>
    <file alias="icons/help.svg">icons/help.svg</file>
    <file alias="icons/about.svg">icons/about.svg</file>
    <file alias="icons/filter.svg">icons/filter.svg</file>
    <file alias="icons/expand_all.svg">icons/expand_all.svg</file>
    <file alias="icons/collapse_all.svg">icons/collapse_all.svg</file>
    <file alias="icons/refresh.svg">icons/refresh.svg</file>
    <file alias="icons/edit.svg">icons/edit.svg</file>
    <file alias="icons/transactions.svg">icons/transactions.svg</file>
    <file alias="icons/deactivate.svg">icons/deactivate.svg</file>
    <file alias="icons/add.svg">icons/add.svg</file>
    <file alias="icons/remove.svg">icons/remove.svg</file>
    <file alias="icons/view.svg">icons/view.svg</file>
    <file alias="icons/post.svg">icons/post.svg</file>
    <file alias="icons/reverse.svg">icons/reverse.svg</file>
    <file alias="icons/import_csv.svg">icons/import_csv.svg</file> <!-- New Icon Added -->
    <file alias="images/splash.png">images/splash.png</file>
</qresource>
</RCC>

```

