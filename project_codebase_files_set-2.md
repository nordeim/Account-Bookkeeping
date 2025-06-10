# app/ui/banking/reconciliation_history_table_model.py
```py
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

# app/ui/banking/banking_widget.py
```py
# File: app/ui/banking/banking_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSplitter
from PySide6.QtCore import Qt # Added Qt for orientation
from app.core.application_core import ApplicationCore
from app.ui.banking.bank_accounts_widget import BankAccountsWidget 
from app.ui.banking.bank_transactions_widget import BankTransactionsWidget # New Import

class BankingWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5,5,5,5) # Add some margins back for overall widget

        self.splitter = QSplitter(Qt.Orientation.Horizontal) # Use Horizontal splitter

        self.bank_accounts_widget = BankAccountsWidget(self.app_core, self)
        self.bank_transactions_widget = BankTransactionsWidget(self.app_core, self)

        self.splitter.addWidget(self.bank_accounts_widget)
        self.splitter.addWidget(self.bank_transactions_widget)
        
        # Set initial sizes for the splitter panes (e.g., 1/3 for accounts, 2/3 for transactions)
        # These are just suggestions, can be adjusted by user.
        initial_accounts_width = self.width() // 3 if self.width() > 0 else 300
        self.splitter.setSizes([initial_accounts_width, self.width() - initial_accounts_width if self.width() > 0 else 600])
        
        self.main_layout.addWidget(self.splitter)
        
        # Connect signals for master-detail view
        self.bank_accounts_widget.bank_account_selected.connect(
            self.bank_transactions_widget.set_current_bank_account
        )
        self.bank_accounts_widget.selection_cleared.connect(
            lambda: self.bank_transactions_widget.set_current_bank_account(None, "N/A (No bank account selected)")
        )
        
        self.setLayout(self.main_layout)

```

# app/ui/banking/bank_transaction_table_model.py
```py
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

```

# app/ui/banking/bank_account_dialog.py
```py
# File: app/ui/banking/bank_account_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QCheckBox, QDateEdit, QComboBox, QSpinBox, QTextEdit, 
    QDoubleSpinBox # For opening_balance
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Union

import json
from decimal import Decimal, InvalidOperation

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import BankAccountCreateData, BankAccountUpdateData
from app.models.business.bank_account import BankAccount
from app.models.accounting.account import Account # For Account DTO/ORM
from app.models.accounting.currency import Currency # For Currency DTO/ORM
from app.utils.result import Result
from app.utils.json_helpers import json_converter, json_date_hook

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class BankAccountDialog(QDialog):
    bank_account_saved = Signal(int) # Emits bank_account ID

    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 bank_account_id: Optional[int] = None, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self.bank_account_id = bank_account_id
        self.loaded_bank_account_orm: Optional[BankAccount] = None # Store loaded ORM

        self._currencies_cache: List[Dict[str, Any]] = [] # Store as dicts for combo
        self._gl_accounts_cache: List[Dict[str, Any]] = [] # Store as dicts for combo
        
        self.setWindowTitle("Edit Bank Account" if self.bank_account_id else "Add New Bank Account")
        self.setMinimumWidth(550)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_combo_data()))
        if self.bank_account_id:
            QTimer.singleShot(100, lambda: schedule_task_from_qt(self._load_existing_bank_account_details()))
        else: # New account
             self._on_opening_balance_changed(self.opening_balance_edit.value()) # Initial state for OB date

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.account_name_edit = QLineEdit(); form_layout.addRow("Account Name*:", self.account_name_edit)
        self.bank_name_edit = QLineEdit(); form_layout.addRow("Bank Name*:", self.bank_name_edit)
        self.account_number_edit = QLineEdit(); form_layout.addRow("Account Number*:", self.account_number_edit)
        self.bank_branch_edit = QLineEdit(); form_layout.addRow("Bank Branch:", self.bank_branch_edit)
        self.bank_swift_code_edit = QLineEdit(); form_layout.addRow("SWIFT Code:", self.bank_swift_code_edit)
        
        self.currency_combo = QComboBox(); self.currency_combo.setMinimumWidth(150)
        form_layout.addRow("Currency*:", self.currency_combo)
        
        self.gl_account_combo = QComboBox(); self.gl_account_combo.setMinimumWidth(250)
        form_layout.addRow("GL Link (Asset Account)*:", self.gl_account_combo)

        self.opening_balance_edit = QDoubleSpinBox()
        self.opening_balance_edit.setDecimals(2); self.opening_balance_edit.setRange(-999999999.99, 999999999.99)
        self.opening_balance_edit.setGroupSeparatorShown(True); self.opening_balance_edit.setValue(0.00)
        form_layout.addRow("Opening Balance:", self.opening_balance_edit)

        self.opening_balance_date_edit = QDateEdit(QDate.currentDate())
        self.opening_balance_date_edit.setCalendarPopup(True); self.opening_balance_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.opening_balance_date_edit.setEnabled(False) # Enabled if OB is non-zero
        form_layout.addRow("OB Date:", self.opening_balance_date_edit)
        
        self.description_edit = QTextEdit(); self.description_edit.setFixedHeight(60)
        form_layout.addRow("Description:", self.description_edit)

        self.is_active_check = QCheckBox("Is Active"); self.is_active_check.setChecked(True)
        form_layout.addRow(self.is_active_check)
        
        main_layout.addLayout(form_layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_save_bank_account)
        self.button_box.rejected.connect(self.reject)
        self.opening_balance_edit.valueChanged.connect(self._on_opening_balance_changed)

    @Slot(float)
    def _on_opening_balance_changed(self, value: float):
        self.opening_balance_date_edit.setEnabled(abs(value) > 0.005) # Enable if non-zero

    async def _load_combo_data(self):
        try:
            if self.app_core.currency_manager:
                active_currencies = await self.app_core.currency_manager.get_all_active_currencies()
                self._currencies_cache = [{"code": c.code, "name": c.name} for c in active_currencies]
            
            if self.app_core.chart_of_accounts_manager:
                # Fetch active Asset accounts flagged as bank accounts
                asset_accounts = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(
                    account_type="Asset", active_only=True
                )
                # Further filter for those that are `is_bank_account=True`
                self._gl_accounts_cache = [
                    {"id": acc.id, "code": acc.code, "name": acc.name} 
                    for acc in asset_accounts if acc.is_bank_account
                ]
            
            currencies_json = json.dumps(self._currencies_cache, default=json_converter)
            gl_accounts_json = json.dumps(self._gl_accounts_cache, default=json_converter)

            QMetaObject.invokeMethod(self, "_populate_combos_slot", Qt.ConnectionType.QueuedConnection, 
                                     Q_ARG(str, currencies_json), Q_ARG(str, gl_accounts_json))
        except Exception as e:
            self.app_core.logger.error(f"Error loading combo data for BankAccountDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load data for dropdowns: {str(e)}")

    @Slot(str, str)
    def _populate_combos_slot(self, currencies_json: str, gl_accounts_json: str):
        try:
            currencies_data = json.loads(currencies_json, object_hook=json_date_hook)
            gl_accounts_data = json.loads(gl_accounts_json, object_hook=json_date_hook)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Error parsing combo JSON data for BankAccountDialog: {e}")
            QMessageBox.warning(self, "Data Error", "Error parsing dropdown data."); return

        self.currency_combo.clear()
        for curr in currencies_data: self.currency_combo.addItem(f"{curr['code']} - {curr['name']}", curr['code'])
        if self.currency_combo.count() > 0: self.currency_combo.setCurrentIndex(0) # Default to first

        self.gl_account_combo.clear()
        self.gl_account_combo.addItem("-- Select GL Account --", 0) # Represents None
        for acc in gl_accounts_data: self.gl_account_combo.addItem(f"{acc['code']} - {acc['name']}", acc['id'])
        
        # If editing and ORM data is already loaded, apply it to combos
        if self.loaded_bank_account_orm:
            self._populate_fields_from_orm_after_combos(self.loaded_bank_account_orm)

    async def _load_existing_bank_account_details(self):
        if not self.bank_account_id or not self.app_core.bank_account_manager: return
        
        self.loaded_bank_account_orm = await self.app_core.bank_account_manager.get_bank_account_for_dialog(self.bank_account_id)
        if self.loaded_bank_account_orm:
            # Serialize data for thread-safe UI update
            account_dict = {col.name: getattr(self.loaded_bank_account_orm, col.name) 
                            for col in BankAccount.__table__.columns 
                            if hasattr(self.loaded_bank_account_orm, col.name)}
            account_json_str = json.dumps(account_dict, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_fields_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, account_json_str))
        else:
            QMessageBox.warning(self, "Load Error", f"Bank Account ID {self.bank_account_id} not found.")
            self.reject()

    @Slot(str)
    def _populate_fields_slot(self, account_json_str: str):
        try:
            data = json.loads(account_json_str, object_hook=json_date_hook)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse bank account data for editing."); return
        self._populate_fields_from_dict(data)

    def _populate_fields_from_dict(self, data: Dict[str, Any]):
        self.account_name_edit.setText(data.get("account_name", ""))
        self.account_number_edit.setText(data.get("account_number", ""))
        self.bank_name_edit.setText(data.get("bank_name", ""))
        self.bank_branch_edit.setText(data.get("bank_branch", "") or "")
        self.bank_swift_code_edit.setText(data.get("bank_swift_code", "") or "")
        
        ob_val = data.get("opening_balance")
        self.opening_balance_edit.setValue(float(Decimal(str(ob_val))) if ob_val is not None else 0.0)
        ob_date_val = data.get("opening_balance_date")
        self.opening_balance_date_edit.setDate(QDate(ob_date_val) if ob_date_val else QDate.currentDate())
        self._on_opening_balance_changed(self.opening_balance_edit.value()) # Update date edit enabled state

        self.description_edit.setText(data.get("description", "") or "")
        self.is_active_check.setChecked(data.get("is_active", True))

        # Set comboboxes - ensure they are populated first
        currency_idx = self.currency_combo.findData(data.get("currency_code", "SGD"))
        if currency_idx != -1: self.currency_combo.setCurrentIndex(currency_idx)
        
        gl_acc_id = data.get("gl_account_id")
        gl_acc_idx = self.gl_account_combo.findData(gl_acc_id if gl_acc_id is not None else 0)
        if gl_acc_idx != -1: self.gl_account_combo.setCurrentIndex(gl_acc_idx)

    def _populate_fields_from_orm_after_combos(self, ba_orm: BankAccount): # Called after combos are loaded
        currency_idx = self.currency_combo.findData(ba_orm.currency_code)
        if currency_idx != -1: self.currency_combo.setCurrentIndex(currency_idx)
        else: self.app_core.logger.warning(f"Loaded bank account currency '{ba_orm.currency_code}' not found in combo.")

        gl_acc_idx = self.gl_account_combo.findData(ba_orm.gl_account_id or 0)
        if gl_acc_idx != -1: self.gl_account_combo.setCurrentIndex(gl_acc_idx)
        elif ba_orm.gl_account_id:
             self.app_core.logger.warning(f"Loaded bank account GL ID '{ba_orm.gl_account_id}' not found in combo.")


    @Slot()
    def on_save_bank_account(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "No user logged in."); return

        gl_account_id_data = self.gl_account_combo.currentData()
        if not gl_account_id_data or gl_account_id_data == 0:
            QMessageBox.warning(self, "Validation Error", "GL Link Account is required.")
            return
        
        ob_val = Decimal(str(self.opening_balance_edit.value()))
        ob_date_val = self.opening_balance_date_edit.date().toPython() if self.opening_balance_date_edit.isEnabled() else None
        
        common_data_dict = {
            "account_name": self.account_name_edit.text().strip(),
            "account_number": self.account_number_edit.text().strip(),
            "bank_name": self.bank_name_edit.text().strip(),
            "bank_branch": self.bank_branch_edit.text().strip() or None,
            "bank_swift_code": self.bank_swift_code_edit.text().strip() or None,
            "currency_code": self.currency_combo.currentData() or "SGD",
            "opening_balance": ob_val,
            "opening_balance_date": ob_date_val,
            "gl_account_id": int(gl_account_id_data),
            "is_active": self.is_active_check.isChecked(),
            "description": self.description_edit.toPlainText().strip() or None,
            "user_id": self.current_user_id
        }

        try:
            if self.bank_account_id:
                dto = BankAccountUpdateData(id=self.bank_account_id, **common_data_dict) # type: ignore
            else:
                dto = BankAccountCreateData(**common_data_dict) # type: ignore
        except ValueError as pydantic_error:
             QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}")
             return

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button: ok_button.setEnabled(False)
        
        schedule_task_from_qt(self._perform_save(dto)).add_done_callback(
            lambda _: ok_button.setEnabled(True) if ok_button and self.isVisible() else None
        )

    async def _perform_save(self, dto: Union[BankAccountCreateData, BankAccountUpdateData]):
        if not self.app_core.bank_account_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Bank Account Manager not available."))
            return

        result: Result[BankAccount]
        is_update = isinstance(dto, BankAccountUpdateData)
        action_verb_past = "updated" if is_update else "created"

        if is_update:
            result = await self.app_core.bank_account_manager.update_bank_account(dto.id, dto)
        else:
            result = await self.app_core.bank_account_manager.create_bank_account(dto)

        if result.is_success and result.value:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), 
                Q_ARG(str, f"Bank Account '{result.value.account_name}' {action_verb_past} successfully (ID: {result.value.id})."))
            self.bank_account_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), 
                Q_ARG(str, f"Failed to save bank account:\n{', '.join(result.errors)}"))

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

# app/ui/banking/bank_accounts_widget.py
```py
# app/ui/banking/bank_accounts_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox, QComboBox, QGroupBox # Added QGroupBox
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize, QDate, Signal
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.banking.bank_account_table_model import BankAccountTableModel
from app.ui.banking.bank_account_dialog import BankAccountDialog
from app.utils.pydantic_models import BankAccountSummaryData
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.bank_account import BankAccount 

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class BankAccountsWidget(QWidget):
    bank_account_selected = Signal(int, str) # Emit bank_account_id and name
    selection_cleared = Signal() # Emit when no valid selection

    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass
        
        self._init_ui()
        QTimer.singleShot(0, lambda: self.toolbar_refresh_action.trigger())

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)
        self.main_layout.setContentsMargins(0,0,0,0) 

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        self._create_filter_area()
        self.main_layout.addWidget(self.filter_group) 

        self.bank_accounts_table = QTableView()
        self.bank_accounts_table.setAlternatingRowColors(True)
        self.bank_accounts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.bank_accounts_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) 
        self.bank_accounts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.bank_accounts_table.horizontalHeader().setStretchLastSection(False)
        self.bank_accounts_table.doubleClicked.connect(self._on_edit_bank_account_double_click) 
        self.bank_accounts_table.setSortingEnabled(True)

        self.table_model = BankAccountTableModel()
        self.bank_accounts_table.setModel(self.table_model)
        
        header = self.bank_accounts_table.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        if "ID" in self.table_model._headers:
            id_col_idx = self.table_model._headers.index("ID")
            self.bank_accounts_table.setColumnHidden(id_col_idx, True)
        
        if "Account Name" in self.table_model._headers:
            name_col_idx = self.table_model._headers.index("Account Name")
            visible_name_idx = name_col_idx
            if "ID" in self.table_model._headers and self.table_model._headers.index("ID") < name_col_idx and self.bank_accounts_table.isColumnHidden(self.table_model._headers.index("ID")):
                visible_name_idx -=1
            if not self.bank_accounts_table.isColumnHidden(name_col_idx):
                 header.setSectionResizeMode(visible_name_idx, QHeaderView.ResizeMode.Stretch)
        elif self.table_model.columnCount() > 1: 
            header.setSectionResizeMode(0 if self.bank_accounts_table.isColumnHidden(0) else 1, QHeaderView.ResizeMode.Stretch)

        self.main_layout.addWidget(self.bank_accounts_table)
        self.setLayout(self.main_layout)

        if self.bank_accounts_table.selectionModel():
            self.bank_accounts_table.selectionModel().selectionChanged.connect(self._on_selection_changed) 
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Bank Accounts Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add Bank Account", self)
        self.toolbar_add_action.triggered.connect(self._on_add_bank_account)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Bank Account", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_bank_account)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_toggle_active_action = QAction(QIcon(self.icon_path_prefix + "deactivate.svg"), "Toggle Active", self)
        self.toolbar_toggle_active_action.triggered.connect(self._on_toggle_active_status)
        self.toolbar.addAction(self.toolbar_toggle_active_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_bank_accounts()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    def _create_filter_area(self):
        self.filter_group = QGroupBox("Filter Bank Accounts") 
        filter_layout = QHBoxLayout(self.filter_group) 

        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem("All", None)
        self.status_filter_combo.addItem("Active", True)
        self.status_filter_combo.addItem("Inactive", False)
        self.status_filter_combo.currentIndexChanged.connect(self.toolbar_refresh_action.trigger)
        filter_layout.addWidget(self.status_filter_combo)
        filter_layout.addStretch()

    @Slot()
    def _on_selection_changed(self):
        self._update_action_states()
        selected_rows = self.bank_accounts_table.selectionModel().selectedRows()
        if len(selected_rows) == 1:
            row = selected_rows[0].row()
            ba_id = self.table_model.get_bank_account_id_at_row(row)
            
            name_item_index = self.table_model.index(row, self.table_model._headers.index("Account Name"))
            ba_name = self.table_model.data(name_item_index, Qt.ItemDataRole.DisplayRole)
            if ba_id is not None and ba_name is not None:
                self.bank_account_selected.emit(ba_id, str(ba_name))
            else:
                self.selection_cleared.emit()
        else:
            self.selection_cleared.emit()

    @Slot()
    def _update_action_states(self):
        selected_rows = self.bank_accounts_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        self.toolbar_edit_action.setEnabled(single_selection)
        self.toolbar_toggle_active_action.setEnabled(single_selection)

    async def _load_bank_accounts(self):
        if not self.app_core.bank_account_manager:
            self.app_core.logger.error("BankAccountManager not available.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Bank Account Manager not available."))
            return
        try:
            active_filter_data = self.status_filter_combo.currentData()
            
            result: Result[List[BankAccountSummaryData]] = await self.app_core.bank_account_manager.get_bank_accounts_for_listing(
                active_only=active_filter_data if isinstance(active_filter_data, bool) else None, 
                page=1, page_size=-1 
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                json_data = json.dumps([dto.model_dump() for dto in data_for_table], default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Failed to load bank accounts: {', '.join(result.errors)}"))
        except Exception as e:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            summaries = [BankAccountSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(summaries)
            
            if self.bank_accounts_table.selectionModel().hasSelection():
                self._on_selection_changed() 
            else:
                self.selection_cleared.emit()

        except Exception as e: 
            QMessageBox.critical(self, "Data Error", f"Failed to parse/validate bank account data: {e}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_bank_account(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = BankAccountDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.bank_account_saved.connect(lambda _id: schedule_task_from_qt(self._load_bank_accounts()))
        dialog.exec()

    def _get_selected_bank_account_id(self) -> Optional[int]:
        selected_rows = self.bank_accounts_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1: return None
        return self.table_model.get_bank_account_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_bank_account(self):
        bank_account_id = self._get_selected_bank_account_id()
        if bank_account_id is None: QMessageBox.information(self, "Selection", "Please select a bank account."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = BankAccountDialog(self.app_core, self.app_core.current_user.id, bank_account_id=bank_account_id, parent=self)
        dialog.bank_account_saved.connect(lambda _id: schedule_task_from_qt(self._load_bank_accounts()))
        dialog.exec()
        
    @Slot(QModelIndex)
    def _on_edit_bank_account_double_click(self, index: QModelIndex): 
        if not index.isValid(): return
        bank_account_id = self.table_model.get_bank_account_id_at_row(index.row())
        if bank_account_id is None: return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = BankAccountDialog(self.app_core, self.app_core.current_user.id, bank_account_id=bank_account_id, parent=self)
        dialog.bank_account_saved.connect(lambda _id: schedule_task_from_qt(self._load_bank_accounts()))
        dialog.exec()

    @Slot()
    def _on_toggle_active_status(self):
        bank_account_id = self._get_selected_bank_account_id()
        if bank_account_id is None: QMessageBox.information(self, "Selection", "Please select a bank account."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
            
        is_currently_active = self.table_model.get_bank_account_status_at_row(self.bank_accounts_table.currentIndex().row())
        action_verb = "deactivate" if is_currently_active else "activate"
        reply = QMessageBox.question(self, f"Confirm {action_verb.capitalize()}",
                                     f"Are you sure you want to {action_verb} this bank account?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return

        future = schedule_task_from_qt(
            self.app_core.bank_account_manager.toggle_bank_account_active_status(bank_account_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_toggle_active_result)
        else: self._handle_toggle_active_result(None)

    def _handle_toggle_active_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule status toggle."); return
        try:
            result: Result[BankAccount] = future.result()
            if result.is_success:
                QMessageBox.information(self, "Success", f"Bank account status changed successfully.")
                schedule_task_from_qt(self._load_bank_accounts()) 
            else:
                QMessageBox.warning(self, "Error", f"Failed to toggle status:\n{', '.join(result.errors)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")


```

# app/ui/banking/bank_transaction_dialog.py
```py
# File: app/ui/banking/bank_transaction_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QDateEdit, QComboBox, QTextEdit, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Union

import json
from decimal import Decimal, InvalidOperation

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import BankTransactionCreateData, BankAccountSummaryData
from app.models.business.bank_transaction import BankTransaction
from app.common.enums import BankTransactionTypeEnum
from app.utils.result import Result
from app.utils.json_helpers import json_converter, json_date_hook

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class BankTransactionDialog(QDialog):
    bank_transaction_saved = Signal(int) # Emits bank_transaction ID

    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 preselected_bank_account_id: Optional[int] = None,
                 parent: Optional["QWidget"] = None): # transaction_id for editing later
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self.preselected_bank_account_id = preselected_bank_account_id
        # self.transaction_id = transaction_id # For future edit mode
        
        self._bank_accounts_cache: List[Dict[str, Any]] = []

        self.setWindowTitle("New Manual Bank Transaction") # For now, only new
        self.setMinimumWidth(500)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_combo_data()))
        # If self.transaction_id, load existing transaction data

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.bank_account_combo = QComboBox()
        self.bank_account_combo.setMinimumWidth(250)
        form_layout.addRow("Bank Account*:", self.bank_account_combo)

        self.transaction_date_edit = QDateEdit(QDate.currentDate())
        self.transaction_date_edit.setCalendarPopup(True); self.transaction_date_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Transaction Date*:", self.transaction_date_edit)
        
        self.value_date_edit = QDateEdit(QDate.currentDate())
        self.value_date_edit.setCalendarPopup(True); self.value_date_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Value Date:", self.value_date_edit)

        self.transaction_type_combo = QComboBox()
        for type_enum in BankTransactionTypeEnum:
            self.transaction_type_combo.addItem(type_enum.value, type_enum)
        form_layout.addRow("Transaction Type*:", self.transaction_type_combo)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Description of the transaction")
        form_layout.addRow("Description*:", self.description_edit)

        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("e.g., Check no., transfer ID")
        form_layout.addRow("Reference:", self.reference_edit)

        self.amount_edit = QDoubleSpinBox()
        self.amount_edit.setDecimals(2); self.amount_edit.setRange(0.01, 999999999.99) # Magnitude only
        self.amount_edit.setGroupSeparatorShown(True); self.amount_edit.setPrefix("$ ") # Placeholder, update with currency
        form_layout.addRow("Amount (Magnitude)*:", self.amount_edit)
        
        # Note: GL Contra Account selection could be added here for immediate JE posting.
        # For basic entry, this is deferred.

        main_layout.addLayout(form_layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_save_transaction)
        self.button_box.rejected.connect(self.reject)
        self.bank_account_combo.currentIndexChanged.connect(self._update_amount_prefix)
        self.transaction_type_combo.currentDataChanged.connect(self._on_transaction_type_changed)


    @Slot()
    def _update_amount_prefix(self):
        bank_account_id = self.bank_account_combo.currentData()
        if bank_account_id and bank_account_id != 0:
            selected_ba = next((ba for ba in self._bank_accounts_cache if ba.get("id") == bank_account_id), None)
            if selected_ba and selected_ba.get("currency_code"):
                self.amount_edit.setPrefix(f"{selected_ba.get('currency_code')} ")
                return
        self.amount_edit.setPrefix("$ ") # Default/fallback

    @Slot(BankTransactionTypeEnum)
    def _on_transaction_type_changed(self, txn_type: Optional[BankTransactionTypeEnum]):
        # Could provide hints or change UI based on type, e.g., suggest positive/negative
        # For now, mainly for internal logic when saving.
        pass

    async def _load_combo_data(self):
        try:
            if self.app_core.bank_account_manager:
                result = await self.app_core.bank_account_manager.get_bank_accounts_for_listing(active_only=True, page_size=-1) # Get all active
                if result.is_success and result.value:
                    self._bank_accounts_cache = [ba.model_dump() for ba in result.value]
            
            bank_accounts_json = json.dumps(self._bank_accounts_cache, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_combos_slot", Qt.ConnectionType.QueuedConnection, 
                                     Q_ARG(str, bank_accounts_json))
        except Exception as e:
            self.app_core.logger.error(f"Error loading combo data for BankTransactionDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load bank accounts: {str(e)}")

    @Slot(str)
    def _populate_combos_slot(self, bank_accounts_json: str):
        try:
            bank_accounts_data = json.loads(bank_accounts_json, object_hook=json_date_hook)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Error parsing bank accounts JSON for BankTransactionDialog: {e}")
            QMessageBox.warning(self, "Data Error", "Error parsing bank account data."); return

        self.bank_account_combo.clear()
        self.bank_account_combo.addItem("-- Select Bank Account --", 0)
        for ba in bank_accounts_data:
            self.bank_account_combo.addItem(f"{ba['account_name']} ({ba['bank_name']} - {ba['account_number'][-4:] if ba['account_number'] else 'N/A'})", ba['id'])
        
        if self.preselected_bank_account_id:
            idx = self.bank_account_combo.findData(self.preselected_bank_account_id)
            if idx != -1:
                self.bank_account_combo.setCurrentIndex(idx)
        elif self.bank_account_combo.count() > 1: # More than just "-- Select..."
             self.bank_account_combo.setCurrentIndex(1) # Default to first actual account
        
        self._update_amount_prefix()


    @Slot()
    def on_save_transaction(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "No user logged in."); return

        bank_account_id_data = self.bank_account_combo.currentData()
        if not bank_account_id_data or bank_account_id_data == 0:
            QMessageBox.warning(self, "Validation Error", "Bank Account must be selected.")
            return
        
        bank_account_id = int(bank_account_id_data)
        transaction_date_py = self.transaction_date_edit.date().toPython()
        value_date_py = self.value_date_edit.date().toPython()
        
        selected_type_enum = self.transaction_type_combo.currentData()
        if not isinstance(selected_type_enum, BankTransactionTypeEnum):
            QMessageBox.warning(self, "Validation Error", "Invalid transaction type selected.")
            return

        description_str = self.description_edit.text().strip()
        if not description_str:
            QMessageBox.warning(self, "Validation Error", "Description is required.")
            return
        
        reference_str = self.reference_edit.text().strip() or None
        amount_magnitude = Decimal(str(self.amount_edit.value()))

        # Determine signed amount based on transaction type
        signed_amount: Decimal
        if selected_type_enum in [BankTransactionTypeEnum.DEPOSIT, BankTransactionTypeEnum.INTEREST]:
            signed_amount = amount_magnitude # Positive
        elif selected_type_enum in [BankTransactionTypeEnum.WITHDRAWAL, BankTransactionTypeEnum.FEE]:
            signed_amount = -amount_magnitude # Negative
        elif selected_type_enum == BankTransactionTypeEnum.TRANSFER:
            # For transfers, amount could be positive or negative depending on direction.
            # This basic dialog might need a "Transfer In/Out" distinction or more UI.
            # For now, assume positive for "Transfer In" and user adjusts if it's "Transfer Out".
            # Better: a separate "Transfer" dialog or more type options.
            # For "Basic Entry", let's assume transfers handled by specific UIs later or this is generic.
            # For now, let user decide sign by making a choice.
            # A simple approach for this dialog: make Transfers require user to specify sign
            # implicitly by selecting "Deposit" or "Withdrawal" type for the transfer leg.
            # Or prompt user:
            reply = QMessageBox.question(self, "Transfer Direction", 
                                         "Is this transfer an INFLOW (money in) or OUTFLOW (money out) for this bank account?",
                                         "Inflow", "Outflow")
            if reply == 0: # Inflow
                signed_amount = amount_magnitude
            else: # Outflow
                signed_amount = -amount_magnitude
        else: # Adjustment
            signed_amount = amount_magnitude # Allow positive or negative based on user's intent for adjustment

        try:
            dto = BankTransactionCreateData(
                bank_account_id=bank_account_id,
                transaction_date=transaction_date_py,
                value_date=value_date_py,
                transaction_type=selected_type_enum,
                description=description_str,
                reference=reference_str,
                amount=signed_amount,
                user_id=self.current_user_id
            )
        except ValueError as pydantic_error: # Catches Pydantic DTO validation errors
             QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}")
             return

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button: ok_button.setEnabled(False)
        
        schedule_task_from_qt(self._perform_save(dto)).add_done_callback(
            lambda _: ok_button.setEnabled(True) if ok_button and self.isVisible() else None
        )

    async def _perform_save(self, dto: BankTransactionCreateData):
        if not self.app_core.bank_transaction_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Bank Transaction Manager not available."))
            return

        result: Result[BankTransaction]
        result = await self.app_core.bank_transaction_manager.create_manual_bank_transaction(dto)

        if result.is_success and result.value:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), 
                Q_ARG(str, f"Bank Transaction created successfully (ID: {result.value.id})."))
            self.bank_transaction_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), 
                Q_ARG(str, f"Failed to save bank transaction:\n{', '.join(result.errors)}"))

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

# app/ui/banking/bank_reconciliation_widget.py-previous
```py-previous
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

from datetime import date as python_date, datetime
from decimal import Decimal, ROUND_HALF_UP

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.banking.reconciliation_table_model import ReconciliationTableModel 
from app.ui.banking.reconciliation_history_table_model import ReconciliationHistoryTableModel
from app.ui.banking.bank_transaction_table_model import BankTransactionTableModel
from app.ui.accounting.journal_entry_dialog import JournalEntryDialog
from app.utils.pydantic_models import (
    BankAccountSummaryData, BankTransactionSummaryData, 
    JournalEntryData, JournalEntryLineData, BankReconciliationSummaryData
)
from app.common.enums import BankTransactionTypeEnum
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.bank_reconciliation import BankReconciliation # For ORM instantiation

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
        
        self._all_loaded_statement_lines: List[BankTransactionSummaryData] = []
        self._all_loaded_system_transactions: List[BankTransactionSummaryData] = []

        self._statement_ending_balance = Decimal(0)
        self._book_balance_gl = Decimal(0) 
        self._interest_earned_on_statement_not_in_book = Decimal(0)
        self._bank_charges_on_statement_not_in_book = Decimal(0)
        self._outstanding_system_deposits = Decimal(0) 
        self._outstanding_system_withdrawals = Decimal(0) 
        self._difference = Decimal(0)

        self._current_history_page = 1
        self._total_history_records = 0
        self._history_page_size = 10 

        self.icon_path_prefix = "resources/icons/"
        try: import app.resources_rc; self.icon_path_prefix = ":/icons/"
        except ImportError: pass

        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_bank_accounts_for_combo()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self); self.main_layout.setContentsMargins(10,10,10,10)
        
        header_controls_group = QGroupBox("Reconciliation Setup"); header_layout = QGridLayout(header_controls_group)
        header_layout.addWidget(QLabel("Bank Account*:"), 0, 0); self.bank_account_combo = QComboBox(); self.bank_account_combo.setMinimumWidth(250); header_layout.addWidget(self.bank_account_combo, 0, 1)
        header_layout.addWidget(QLabel("Statement End Date*:"), 0, 2); self.statement_date_edit = QDateEdit(QDate.currentDate()); self.statement_date_edit.setCalendarPopup(True); self.statement_date_edit.setDisplayFormat("dd/MM/yyyy"); header_layout.addWidget(self.statement_date_edit, 0, 3)
        header_layout.addWidget(QLabel("Statement End Balance*:"), 1, 0); self.statement_balance_spin = QDoubleSpinBox(); self.statement_balance_spin.setDecimals(2); self.statement_balance_spin.setRange(-999999999.99, 999999999.99); self.statement_balance_spin.setGroupSeparatorShown(True); header_layout.addWidget(self.statement_balance_spin, 1, 1)
        self.load_transactions_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Load / Refresh Transactions"); header_layout.addWidget(self.load_transactions_button, 1, 3)
        header_layout.setColumnStretch(2,1); self.main_layout.addWidget(header_controls_group)

        self.overall_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_layout.addWidget(self.overall_splitter, 1)

        current_recon_widget = QWidget()
        current_recon_layout = QVBoxLayout(current_recon_widget)
        current_recon_layout.setContentsMargins(0,0,0,0)

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
        summary_layout.addRow("Difference:", self.difference_label); current_recon_layout.addWidget(summary_group)
        
        self.tables_splitter = QSplitter(Qt.Orientation.Horizontal)
        statement_items_group = QGroupBox("Bank Statement Items (Unreconciled)"); statement_layout = QVBoxLayout(statement_items_group)
        self.statement_lines_table = QTableView(); self.statement_lines_model = ReconciliationTableModel()
        self._configure_recon_table(self.statement_lines_table, self.statement_lines_model, is_statement_table=True)
        statement_layout.addWidget(self.statement_lines_table); self.tables_splitter.addWidget(statement_items_group)
        
        system_txns_group = QGroupBox("System Bank Transactions (Unreconciled)"); system_layout = QVBoxLayout(system_txns_group)
        self.system_txns_table = QTableView(); self.system_txns_model = ReconciliationTableModel()
        self._configure_recon_table(self.system_txns_table, self.system_txns_model, is_statement_table=False)
        system_layout.addWidget(self.system_txns_table); self.tables_splitter.addWidget(system_txns_group)
        self.tables_splitter.setSizes([self.width() // 2, self.width() // 2]); current_recon_layout.addWidget(self.tables_splitter, 1)
        
        action_layout = QHBoxLayout(); self.match_selected_button = QPushButton(QIcon(self.icon_path_prefix + "post.svg"), "Match Selected"); self.match_selected_button.setEnabled(False)
        self.create_je_button = QPushButton(QIcon(self.icon_path_prefix + "add.svg"), "Add Journal Entry"); self.create_je_button.setEnabled(False) 
        self.save_reconciliation_button = QPushButton(QIcon(self.icon_path_prefix + "backup.svg"), "Save Reconciliation"); self.save_reconciliation_button.setEnabled(False) 
        action_layout.addStretch(); action_layout.addWidget(self.match_selected_button); action_layout.addWidget(self.create_je_button); action_layout.addStretch(); action_layout.addWidget(self.save_reconciliation_button)
        current_recon_layout.addLayout(action_layout)
        self.overall_splitter.addWidget(current_recon_widget)

        history_outer_group = QGroupBox("Reconciliation History")
        history_outer_layout = QVBoxLayout(history_outer_group)
        self.history_table = QTableView(); self.history_table_model = ReconciliationHistoryTableModel()
        self.history_table.setModel(self.history_table_model)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.horizontalHeader().setStretchLastSection(False); self.history_table.setSortingEnabled(True)
        self.history_table.setColumnHidden(self.history_table_model._headers.index("ID"), True)
        for i in range(1, self.history_table_model.columnCount()): self.history_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        if "Statement Date" in self.history_table_model._headers : self.history_table.horizontalHeader().setSectionResizeMode(self.history_table_model._headers.index("Statement Date"), QHeaderView.ResizeMode.Stretch)
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
        self.overall_splitter.setSizes([self.height() * 2 // 3, self.height() // 3])
        self.setLayout(self.main_layout)
        self._connect_signals()

    def _configure_readonly_detail_table(self, table_view: QTableView, table_model: BankTransactionTableModel):
        table_view.setModel(table_model)
        table_view.setAlternatingRowColors(True)
        table_view.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_view.horizontalHeader().setStretchLastSection(False)
        table_view.setSortingEnabled(True)
        if "ID" in table_model._headers: table_view.setColumnHidden(table_model._headers.index("ID"), True)
        if "Reconciled" in table_model._headers: table_view.setColumnHidden(table_model._headers.index("Reconciled"), True)
        for i in range(table_model.columnCount()):
             if not table_view.isColumnHidden(i) : table_view.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        desc_col_idx = table_model._headers.index("Description")
        if not table_view.isColumnHidden(desc_col_idx):
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
        self.statement_lines_model.item_check_state_changed.connect(self._on_transaction_selection_changed)
        self.system_txns_model.item_check_state_changed.connect(self._on_transaction_selection_changed)
        self.match_selected_button.clicked.connect(self._on_match_selected_clicked)
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
        self._current_bank_account_gl_id = None
        self._current_bank_account_currency = "SGD" 
        if self._current_bank_account_id:
            selected_ba_dto = next((ba for ba in self._bank_accounts_cache if ba.id == self._current_bank_account_id), None)
            if selected_ba_dto:
                self._current_bank_account_currency = selected_ba_dto.currency_code
                self.statement_balance_spin.setSuffix(f" {selected_ba_dto.currency_code}")
        self.statement_lines_model.update_data([]); self.system_txns_model.update_data([])
        self._reset_summary_figures(); self._calculate_and_display_balances() 
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
        statement_date = self.statement_date_edit.date().toPython()
        self._statement_ending_balance = Decimal(str(self.statement_balance_spin.value()))
        self.load_transactions_button.setEnabled(False); self.load_transactions_button.setText("Loading...")
        schedule_task_from_qt(self._fetch_and_populate_transactions(self._current_bank_account_id, statement_date))
        self._load_reconciliation_history(1)

    async def _fetch_and_populate_transactions(self, bank_account_id: int, statement_date: python_date):
        self.load_transactions_button.setEnabled(True); self.load_transactions_button.setText("Load / Refresh Transactions")
        if not self.app_core.bank_transaction_manager or not self.app_core.account_service or not self.app_core.journal_service or not self.app_core.bank_account_service : return
        selected_bank_account_orm = await self.app_core.bank_account_service.get_by_id(bank_account_id)
        if not selected_bank_account_orm or not selected_bank_account_orm.gl_account_id: QMessageBox.critical(self, "Error", "Selected bank account or its GL link is invalid."); return
        self._current_bank_account_gl_id = selected_bank_account_orm.gl_account_id
        self._current_bank_account_currency = selected_bank_account_orm.currency_code
        self._book_balance_gl = await self.app_core.journal_service.get_account_balance(selected_bank_account_orm.gl_account_id, statement_date)
        result = await self.app_core.bank_transaction_manager.get_unreconciled_transactions_for_matching(bank_account_id, statement_date)
        if result.is_success and result.value:
            self._all_loaded_statement_lines, self._all_loaded_system_transactions = result.value
            stmt_lines_json = json.dumps([s.model_dump(mode='json') for s in self._all_loaded_statement_lines], default=json_converter)
            sys_txns_json = json.dumps([s.model_dump(mode='json') for s in self._all_loaded_system_transactions], default=json_converter)
            QMetaObject.invokeMethod(self, "_update_transaction_tables_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, stmt_lines_json), Q_ARG(str, sys_txns_json))
        else:
            QMessageBox.warning(self, "Load Error", f"Failed to load transactions: {', '.join(result.errors if result.errors else ['Unknown error'])}")
            self.statement_lines_model.update_data([]); self.system_txns_model.update_data([])
        self._reset_summary_figures(); self._calculate_and_display_balances()

    @Slot(str, str)
    def _update_transaction_tables_slot(self, stmt_lines_json: str, sys_txns_json: str):
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
        self._calculate_and_display_balances(); self._update_match_button_state()

    def _reset_summary_figures(self):
        self._interest_earned_on_statement_not_in_book = Decimal(0)
        self._bank_charges_on_statement_not_in_book = Decimal(0)
        self._outstanding_system_deposits = Decimal(0) 
        self._outstanding_system_withdrawals = Decimal(0) 

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
            self.difference_label.setStyleSheet("font-weight: bold; color: green;"); 
            self.save_reconciliation_button.setEnabled(True)
        else: 
            self.difference_label.setStyleSheet("font-weight: bold; color: red;"); 
            self.save_reconciliation_button.setEnabled(False)
        self.create_je_button.setEnabled(self._interest_earned_on_statement_not_in_book > 0 or self._bank_charges_on_statement_not_in_book > 0 or len(self.statement_lines_model.get_checked_item_data()) > 0)

    def _update_match_button_state(self):
        stmt_checked_count = len(self.statement_lines_model.get_checked_item_data())
        sys_checked_count = len(self.system_txns_model.get_checked_item_data())
        self.match_selected_button.setEnabled(stmt_checked_count > 0 and sys_checked_count > 0)
        self.create_je_button.setEnabled(stmt_checked_count > 0 or self._interest_earned_on_statement_not_in_book > 0 or self._bank_charges_on_statement_not_in_book > 0)

    @Slot()
    def _on_match_selected_clicked(self):
        selected_statement_items = self.statement_lines_model.get_checked_item_data(); 
        selected_system_items = self.system_txns_model.get_checked_item_data()
        if not selected_statement_items or not selected_system_items: QMessageBox.information(self, "Selection Needed", "Please select items from both tables to match."); return
        sum_stmt = sum(item.amount for item in selected_statement_items); sum_sys = sum(item.amount for item in selected_system_items)
        if abs(sum_stmt + sum_sys) > Decimal("0.01"): 
            QMessageBox.warning(self, "Match Error",  f"Selected statement items total ({sum_stmt:,.2f}) and selected system items total ({sum_sys:,.2f}) do not net to zero. Please ensure selections form a balanced match (e.g. a deposit and a withdrawal of same absolute amount)."); return
        stmt_ids_to_clear = [item.id for item in selected_statement_items]; 
        sys_ids_to_clear = [item.id for item in selected_system_items]
        self.statement_lines_model.uncheck_items_by_id(stmt_ids_to_clear)
        self.system_txns_model.uncheck_items_by_id(sys_ids_to_clear)
        self.app_core.logger.info(f"UI Matched Statement Items (IDs: {stmt_ids_to_clear}) with System Items (IDs: {sys_ids_to_clear})")
        QMessageBox.information(self, "Items Selected for Matching", "Selected items are marked for matching. Finalize with 'Save Reconciliation'.")
        self._calculate_and_display_balances(); self._update_match_button_state()

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
        self.app_core.logger.info(f"Journal Entry ID {saved_je_id} created for statement item ID {original_statement_txn_id}. Refreshing transactions...")
        for r in range(self.statement_lines_model.rowCount()):
            dto = self.statement_lines_model.get_item_data_at_row(r)
            if dto and dto.id == original_statement_txn_id:
                self.statement_lines_model.uncheck_items_by_id([original_statement_txn_id])
                break
        self._on_load_transactions_clicked()

    @Slot()
    def _on_save_reconciliation_clicked(self):
        if not self._current_bank_account_id or abs(self._difference) >= Decimal("0.01"):
            QMessageBox.warning(self, "Cannot Save", "Reconciliation is not balanced or no bank account selected.")
            return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        all_statement_ids = {txn.id for txn in self._all_loaded_statement_lines}
        all_system_ids = {txn.id for txn in self._all_loaded_system_transactions}
        current_unreconciled_statement_ids = {self.statement_lines_model.get_item_data_at_row(r).id for r in range(self.statement_lines_model.rowCount()) if self.statement_lines_model.get_item_data_at_row(r)}
        current_unreconciled_system_ids = {self.system_txns_model.get_item_data_at_row(r).id for r in range(self.system_txns_model.rowCount()) if self.system_txns_model.get_item_data_at_row(r)}
        cleared_statement_item_ids = list(all_statement_ids - current_unreconciled_statement_ids)
        cleared_system_item_ids = list(all_system_ids - current_unreconciled_system_ids)
        self.app_core.logger.info(f"Saving reconciliation. Cleared Stmt IDs: {cleared_statement_item_ids}, Cleared Sys IDs: {cleared_system_item_ids}")
        self.save_reconciliation_button.setEnabled(False); self.save_reconciliation_button.setText("Saving...")
        schedule_task_from_qt(self._perform_save_reconciliation(cleared_statement_item_ids, cleared_system_item_ids))

    async def _perform_save_reconciliation(self, cleared_statement_ids: List[int], cleared_system_ids: List[int]):
        if not self.app_core.bank_reconciliation_service or not self._current_bank_account_id:
            QMessageBox.critical(self, "Error", "Reconciliation Service or Bank Account not set.")
            self.save_reconciliation_button.setEnabled(abs(self._difference) < Decimal("0.01")); self.save_reconciliation_button.setText("Save Reconciliation"); return

        statement_date_py = self.statement_date_edit.date().toPython()
        statement_end_bal_dec = Decimal(str(self.statement_balance_spin.value()))
        final_reconciled_book_balance_dec = self._book_balance_gl + self._interest_earned_on_statement_not_in_book - self._bank_charges_on_statement_not_in_book
        
        new_reconciliation_orm = BankReconciliation(
            bank_account_id=self._current_bank_account_id,
            statement_date=statement_date_py,
            statement_ending_balance=statement_end_bal_dec,
            calculated_book_balance=final_reconciled_book_balance_dec,
            reconciled_difference=self._difference,
            created_by_user_id=self.app_core.current_user.id,
            notes=None 
        )
        try:
            async with self.app_core.db_manager.session() as session:
                saved_recon_orm = await self.app_core.bank_reconciliation_service.save_reconciliation_details(
                    reconciliation_orm=new_reconciliation_orm,
                    cleared_statement_txn_ids=cleared_statement_ids,
                    cleared_system_txn_ids=cleared_system_ids,
                    statement_end_date=statement_date_py,
                    bank_account_id=self._current_bank_account_id,
                    statement_ending_balance=statement_end_bal_dec,
                    session=session
                )
            QMessageBox.information(self, "Success", f"Bank reconciliation saved successfully (ID: {saved_recon_orm.id}).")
            self.reconciliation_saved.emit(saved_recon_orm.id)
            self._on_load_transactions_clicked() 
            self._load_reconciliation_history(1)
        except Exception as e:
            self.app_core.logger.error(f"Error performing save reconciliation: {e}", exc_info=True)
            QMessageBox.warning(self, "Save Error", f"Failed to save reconciliation: {str(e)}")
        finally:
            self.save_reconciliation_button.setEnabled(abs(self._difference) < Decimal("0.01")); 
            self.save_reconciliation_button.setText("Save Reconciliation")

    def _load_reconciliation_history(self, page_number: int):
        if not self._current_bank_account_id:
            self.history_table_model.update_data([])
            self._update_history_pagination_controls(0, 0)
            return
        self._current_history_page = page_number
        schedule_task_from_qt(self._fetch_reconciliation_history())

    async def _fetch_reconciliation_history(self):
        if not self.app_core.bank_reconciliation_service or self._current_bank_account_id is None: return
        history_data, total_records = await self.app_core.bank_reconciliation_service.get_reconciliations_for_account(
            bank_account_id=self._current_bank_account_id,
            page=self._current_history_page,
            page_size=self._history_page_size
        )
        self._total_history_records = total_records
        history_json = json.dumps([h.model_dump(mode='json') for h in history_data], default=json_converter)
        QMetaObject.invokeMethod(self, "_update_history_table_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, history_json))
        self._update_history_pagination_controls(len(history_data), total_records)

    @Slot(str)
    def _update_history_table_slot(self, history_json_str: str):
        try:
            history_list_dict = json.loads(history_json_str, object_hook=json_date_hook)
            history_summaries = [BankReconciliationSummaryData.model_validate(d) for d in history_list_dict]
            self.history_table_model.update_data(history_summaries)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to display reconciliation history: {e}")
        self.history_details_group.setVisible(False)

    def _update_history_pagination_controls(self, current_page_count: int, total_records: int):
        total_pages = (total_records + self._history_page_size - 1) // self._history_page_size
        if total_pages == 0: total_pages = 1
        self.history_page_info_label.setText(f"Page {self._current_history_page} of {total_pages} ({total_records} Records)")
        self.prev_history_button.setEnabled(self._current_history_page > 1)
        self.next_history_button.setEnabled(self._current_history_page < total_pages)

    @Slot(QModelIndex, QModelIndex)
    def _on_history_selection_changed(self, current: QModelIndex, previous: QModelIndex):
        if not current.isValid(): self.history_details_group.setVisible(False); return
        selected_row = current.row()
        reconciliation_id = self.history_table_model.get_reconciliation_id_at_row(selected_row)
        if reconciliation_id is not None:
            schedule_task_from_qt(self._load_historical_reconciliation_details(reconciliation_id))
        else:
            self.history_details_group.setVisible(False)
            self._history_statement_txns_model.update_data([])
            self._history_system_txns_model.update_data([])

    async def _load_historical_reconciliation_details(self, reconciliation_id: int):
        if not self.app_core.bank_reconciliation_service: return
        statement_txns, system_txns = await self.app_core.bank_reconciliation_service.get_transactions_for_reconciliation(reconciliation_id)
        stmt_json = json.dumps([s.model_dump(mode='json') for s in statement_txns], default=json_converter)
        sys_json = json.dumps([s.model_dump(mode='json') for s in system_txns], default=json_converter)
        QMetaObject.invokeMethod(self, "_update_history_detail_tables_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, stmt_json), Q_ARG(str, sys_json))

    @Slot(str, str)
    def _update_history_detail_tables_slot(self, stmt_txns_json: str, sys_txns_json: str):
        try:
            stmt_list = json.loads(stmt_txns_json, object_hook=json_date_hook)
            stmt_dtos = [BankTransactionSummaryData.model_validate(d) for d in stmt_list]
            self._history_statement_txns_model.update_data(stmt_dtos)
            sys_list = json.loads(sys_txns_json, object_hook=json_date_hook)
            sys_dtos = [BankTransactionSummaryData.model_validate(d) for d in sys_list]
            self._history_system_txns_model.update_data(sys_dtos)
            self.history_details_group.setVisible(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to display historical reconciliation details: {e}")
            self.history_details_group.setVisible(False)

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

# app/ui/banking/bank_account_table_model.py
```py
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

```

# app/ui/products/__init__.py
```py
# app/ui/products/__init__.py
from .product_table_model import ProductTableModel
from .product_dialog import ProductDialog
from .products_widget import ProductsWidget # New export

__all__ = [
    "ProductTableModel",
    "ProductDialog",
    "ProductsWidget", # Added to __all__
]


```

# app/ui/products/product_table_model.py
```py
# app/ui/products/product_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation

from app.utils.pydantic_models import ProductSummaryData # Using the DTO for type safety
from app.common.enums import ProductTypeEnum # For displaying enum value

class ProductTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[ProductSummaryData]] = None, parent=None):
        super().__init__(parent)
        # Headers match fields in ProductSummaryData + any derived display fields
        self._headers = ["ID", "Code", "Name", "Type", "Sales Price", "Purchase Price", "Active"]
        self._data: List[ProductSummaryData] = data or []

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
        if value is None: return ""
        try:
            return f"{Decimal(str(value)):,.2f}"
        except (InvalidOperation, TypeError):
            return str(value) # Fallback

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        product_summary: ProductSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            header_key = self._headers[col].lower().replace(' ', '_') # e.g. "Sales Price" -> "sales_price"
            
            if col == 0: return str(product_summary.id)
            if col == 1: return product_summary.product_code
            if col == 2: return product_summary.name
            if col == 3: return product_summary.product_type.value if isinstance(product_summary.product_type, ProductTypeEnum) else str(product_summary.product_type)
            if col == 4: return self._format_decimal_for_table(product_summary.sales_price)
            if col == 5: return self._format_decimal_for_table(product_summary.purchase_price)
            if col == 6: return "Yes" if product_summary.is_active else "No"
            
            # Fallback for safety (should be covered by above)
            return str(getattr(product_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole:
            if col == 0: 
                return product_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] in ["Sales Price", "Purchase Price"]:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if self._headers[col] == "Active":
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_product_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            return self._data[row].id 
        return None
        
    def get_product_status_at_row(self, row: int) -> Optional[bool]:
        if 0 <= row < len(self._data):
            return self._data[row].is_active
        return None

    def update_data(self, new_data: List[ProductSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

```

# app/ui/products/products_widget.py
```py
# app/ui/products/products_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox, QComboBox 
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.products.product_table_model import ProductTableModel 
from app.ui.products.product_dialog import ProductDialog 
from app.utils.pydantic_models import ProductSummaryData 
from app.common.enums import ProductTypeEnum 
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.product import Product 

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class ProductsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for ProductsWidget.")
        except ImportError:
            self.app_core.logger.info("ProductsWidget: Compiled Qt resources not found. Using direct file paths.")
            pass
        
        self._init_ui()
        QTimer.singleShot(0, lambda: self.toolbar_refresh_action.trigger() if hasattr(self, 'toolbar_refresh_action') else schedule_task_from_qt(self._load_products()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Code, Name, Description...")
        self.search_edit.returnPressed.connect(self.toolbar_refresh_action.trigger)
        filter_layout.addWidget(self.search_edit)

        filter_layout.addWidget(QLabel("Type:"))
        self.product_type_filter_combo = QComboBox()
        self.product_type_filter_combo.addItem("All Types", None) 
        for pt_enum in ProductTypeEnum:
            self.product_type_filter_combo.addItem(pt_enum.value, pt_enum) 
        self.product_type_filter_combo.currentIndexChanged.connect(self.toolbar_refresh_action.trigger)
        filter_layout.addWidget(self.product_type_filter_combo)

        self.show_inactive_check = QCheckBox("Show Inactive")
        self.show_inactive_check.stateChanged.connect(self.toolbar_refresh_action.trigger)
        filter_layout.addWidget(self.show_inactive_check)
        
        self.clear_filters_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"),"Clear Filters")
        self.clear_filters_button.clicked.connect(self._clear_filters_and_load)
        filter_layout.addWidget(self.clear_filters_button)
        filter_layout.addStretch()
        self.main_layout.addLayout(filter_layout)

        self.products_table = QTableView()
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.products_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.products_table.horizontalHeader().setStretchLastSection(False)
        self.products_table.doubleClicked.connect(self._on_edit_product_double_click) 
        self.products_table.setSortingEnabled(True)

        self.table_model = ProductTableModel()
        self.products_table.setModel(self.table_model)
        
        header = self.products_table.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        id_col_idx = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else -1
        if id_col_idx != -1: self.products_table.setColumnHidden(id_col_idx, True)
        
        name_col_idx = self.table_model._headers.index("Name") if "Name" in self.table_model._headers else -1
        if name_col_idx != -1:
            visible_name_idx = name_col_idx
            if id_col_idx != -1 and id_col_idx < name_col_idx and self.products_table.isColumnHidden(id_col_idx): # Check if ID column is actually hidden
                visible_name_idx -=1
            
            # Check if the model column corresponding to name_col_idx is not hidden before stretching
            if not self.products_table.isColumnHidden(name_col_idx): # Use model index for isColumnHidden
                 header.setSectionResizeMode(visible_name_idx, QHeaderView.ResizeMode.Stretch)
        elif self.table_model.columnCount() > 2 : 
            # Fallback: if ID (model index 0) is hidden, stretch second visible column (model index 2 -> visible 1)
            # This assumes "Code" is model index 1 (visible 0) and "Name" is model index 2 (visible 1)
            # If headers are ["ID", "Code", "Name", ...], and ID is hidden, visible Name is index 1.
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 


        self.main_layout.addWidget(self.products_table)
        self.setLayout(self.main_layout)

        if self.products_table.selectionModel():
            self.products_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Product/Service Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add Product/Service", self)
        self.toolbar_add_action.triggered.connect(self._on_add_product)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Product/Service", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_product)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_toggle_active_action = QAction(QIcon(self.icon_path_prefix + "deactivate.svg"), "Toggle Active", self)
        self.toolbar_toggle_active_action.triggered.connect(self._on_toggle_active_status)
        self.toolbar.addAction(self.toolbar_toggle_active_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_products()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    @Slot()
    def _clear_filters_and_load(self):
        self.search_edit.clear()
        self.product_type_filter_combo.setCurrentIndex(0) 
        self.show_inactive_check.setChecked(False)
        schedule_task_from_qt(self._load_products())

    @Slot()
    def _update_action_states(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        
        self.toolbar_edit_action.setEnabled(single_selection)
        self.toolbar_toggle_active_action.setEnabled(single_selection)

    async def _load_products(self):
        if not self.app_core.product_manager:
            self.app_core.logger.error("ProductManager not available in ProductsWidget.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Product Manager component not available."))
            return
        try:
            search_term = self.search_edit.text().strip() or None
            active_only = not self.show_inactive_check.isChecked()
            product_type_enum_filter: Optional[ProductTypeEnum] = self.product_type_filter_combo.currentData()
            
            result: Result[List[ProductSummaryData]] = await self.app_core.product_manager.get_products_for_listing(
                active_only=active_only, 
                product_type_filter=product_type_enum_filter,
                search_term=search_term,
                page=1, 
                page_size=200 
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                list_of_dicts = [dto.model_dump() for dto in data_for_table]
                json_data = json.dumps(list_of_dicts, default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                error_msg = f"Failed to load products/services: {', '.join(result.errors)}"
                self.app_core.logger.error(error_msg)
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))
        except Exception as e:
            error_msg = f"Unexpected error loading products/services: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            product_summaries: List[ProductSummaryData] = [ProductSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(product_summaries)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse product/service data: {e}")
        except Exception as p_error: 
            QMessageBox.critical(self, "Data Error", f"Invalid product/service data format: {p_error}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_product(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to add a product/service.")
            return
        
        dialog = ProductDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.product_saved.connect(lambda _id: schedule_task_from_qt(self._load_products()))
        dialog.exec()

    def _get_selected_product_id(self) -> Optional[int]:
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1:
            return None
        return self.table_model.get_product_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_product(self):
        product_id = self._get_selected_product_id()
        if product_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single product/service to edit.")
            return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit a product/service.")
            return
            
        dialog = ProductDialog(self.app_core, self.app_core.current_user.id, product_id=product_id, parent=self)
        dialog.product_saved.connect(lambda _id: schedule_task_from_qt(self._load_products()))
        dialog.exec()
        
    @Slot(QModelIndex)
    def _on_edit_product_double_click(self, index: QModelIndex): 
        if not index.isValid(): return
        product_id = self.table_model.get_product_id_at_row(index.row())
        if product_id is None: return
        
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit product/service.")
            return
        dialog = ProductDialog(self.app_core, self.app_core.current_user.id, product_id=product_id, parent=self)
        dialog.product_saved.connect(lambda _id: schedule_task_from_qt(self._load_products()))
        dialog.exec()

    @Slot()
    def _on_toggle_active_status(self):
        product_id = self._get_selected_product_id()
        if product_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single product/service to toggle status.")
            return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to change product/service status.")
            return
            
        current_row = self.products_table.currentIndex().row()
        if current_row < 0: # Should not happen if product_id is not None
            return

        product_status_active = self.table_model.get_product_status_at_row(current_row)
        action_verb = "deactivate" if product_status_active else "activate"
        reply = QMessageBox.question(self, f"Confirm {action_verb.capitalize()}",
                                     f"Are you sure you want to {action_verb} this product/service?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        future = schedule_task_from_qt(
            self.app_core.product_manager.toggle_product_active_status(product_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_toggle_active_result)
        else: self._handle_toggle_active_result(None)

    def _handle_toggle_active_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule product/service status toggle."); return
        try:
            result: Result[Product] = future.result()
            if result.is_success:
                action_verb_past = "activated" if result.value and result.value.is_active else "deactivated"
                QMessageBox.information(self, "Success", f"Product/Service {action_verb_past} successfully.")
                schedule_task_from_qt(self._load_products()) 
            else:
                QMessageBox.warning(self, "Error", f"Failed to toggle product/service status:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Error handling toggle active status result for product/service: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")


```

# app/ui/products/product_dialog.py
```py
# app/ui/products/product_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QCheckBox, QDateEdit, QComboBox, QSpinBox, QTextEdit, QDoubleSpinBox,
    QCompleter
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon
from typing import Optional, List, Dict, Any, TYPE_CHECKING, cast
from decimal import Decimal, InvalidOperation

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import ProductCreateData, ProductUpdateData
from app.models.business.product import Product
from app.models.accounting.account import Account
from app.models.accounting.tax_code import TaxCode
from app.common.enums import ProductTypeEnum # Enum for product type
from app.utils.result import Result
from app.utils.json_helpers import json_converter, json_date_hook


if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class ProductDialog(QDialog):
    product_saved = Signal(int) # Emits product ID on successful save

    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 product_id: Optional[int] = None, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self.product_id = product_id
        self.loaded_product_data: Optional[Product] = None 

        self._sales_accounts_cache: List[Account] = []
        self._purchase_accounts_cache: List[Account] = []
        self._inventory_accounts_cache: List[Account] = []
        self._tax_codes_cache: List[TaxCode] = []
        
        self.setWindowTitle("Edit Product/Service" if self.product_id else "Add New Product/Service")
        self.setMinimumWidth(600)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_combo_data()))
        if self.product_id:
            QTimer.singleShot(50, lambda: schedule_task_from_qt(self._load_existing_product_details()))
        else: # For new product, trigger initial UI state based on default product type
            self._on_product_type_changed(self.product_type_combo.currentData().value if self.product_type_combo.currentData() else ProductTypeEnum.SERVICE.value)


    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.product_code_edit = QLineEdit(); form_layout.addRow("Code*:", self.product_code_edit)
        self.name_edit = QLineEdit(); form_layout.addRow("Name*:", self.name_edit)
        self.description_edit = QTextEdit(); self.description_edit.setFixedHeight(60); form_layout.addRow("Description:", self.description_edit)

        self.product_type_combo = QComboBox()
        for pt_enum in ProductTypeEnum: self.product_type_combo.addItem(pt_enum.value, pt_enum) # Store Enum member as data
        form_layout.addRow("Product Type*:", self.product_type_combo)

        self.category_edit = QLineEdit(); form_layout.addRow("Category:", self.category_edit)
        self.unit_of_measure_edit = QLineEdit(); form_layout.addRow("Unit of Measure:", self.unit_of_measure_edit)
        self.barcode_edit = QLineEdit(); form_layout.addRow("Barcode:", self.barcode_edit)
        
        self.sales_price_spin = QDoubleSpinBox(); self.sales_price_spin.setDecimals(2); self.sales_price_spin.setRange(0, 99999999.99); self.sales_price_spin.setGroupSeparatorShown(True); form_layout.addRow("Sales Price:", self.sales_price_spin)
        self.purchase_price_spin = QDoubleSpinBox(); self.purchase_price_spin.setDecimals(2); self.purchase_price_spin.setRange(0, 99999999.99); self.purchase_price_spin.setGroupSeparatorShown(True); form_layout.addRow("Purchase Price:", self.purchase_price_spin)
        
        self.sales_account_combo = QComboBox(); self.sales_account_combo.setMinimumWidth(200); form_layout.addRow("Sales Account:", self.sales_account_combo)
        self.purchase_account_combo = QComboBox(); self.purchase_account_combo.setMinimumWidth(200); form_layout.addRow("Purchase Account:", self.purchase_account_combo)
        
        self.inventory_account_label = QLabel("Inventory Account*:") # For toggling visibility
        self.inventory_account_combo = QComboBox(); self.inventory_account_combo.setMinimumWidth(200)
        form_layout.addRow(self.inventory_account_label, self.inventory_account_combo)
        
        self.tax_code_combo = QComboBox(); self.tax_code_combo.setMinimumWidth(150); form_layout.addRow("Default Tax Code:", self.tax_code_combo)
        
        stock_group = QGroupBox("Inventory Details (for 'Inventory' type products)")
        stock_layout = QFormLayout(stock_group)
        self.min_stock_level_spin = QDoubleSpinBox(); self.min_stock_level_spin.setDecimals(2); self.min_stock_level_spin.setRange(0, 999999.99); stock_layout.addRow("Min. Stock Level:", self.min_stock_level_spin)
        self.reorder_point_spin = QDoubleSpinBox(); self.reorder_point_spin.setDecimals(2); self.reorder_point_spin.setRange(0, 999999.99); stock_layout.addRow("Reorder Point:", self.reorder_point_spin)
        form_layout.addRow(stock_group)
        self.stock_details_group_box = stock_group # Store reference to toggle visibility

        self.is_active_check = QCheckBox("Is Active"); self.is_active_check.setChecked(True); form_layout.addRow(self.is_active_check)
        
        main_layout.addLayout(form_layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_save_product)
        self.button_box.rejected.connect(self.reject)
        self.product_type_combo.currentDataChanged.connect(self._on_product_type_changed_enum) # Use currentDataChanged for Enums

    @Slot(ProductTypeEnum) # Slot to receive the Enum member directly
    def _on_product_type_changed_enum(self, product_type_enum: Optional[ProductTypeEnum]):
        if product_type_enum:
            self._on_product_type_changed(product_type_enum.value)

    def _on_product_type_changed(self, product_type_value: str):
        is_inventory_type = (product_type_value == ProductTypeEnum.INVENTORY.value)
        self.inventory_account_label.setVisible(is_inventory_type)
        self.inventory_account_combo.setVisible(is_inventory_type)
        self.stock_details_group_box.setVisible(is_inventory_type)
        if not is_inventory_type: # Clear inventory specific fields if not applicable
            self.inventory_account_combo.setCurrentIndex(-1) # Or find "None" if added
            self.min_stock_level_spin.setValue(0)
            self.reorder_point_spin.setValue(0)


    async def _load_combo_data(self):
        try:
            coa_manager = self.app_core.chart_of_accounts_manager
            if coa_manager:
                self._sales_accounts_cache = await coa_manager.get_accounts_for_selection(account_type="Revenue", active_only=True)
                self._purchase_accounts_cache = await coa_manager.get_accounts_for_selection(account_type="Expense", active_only=True) # Could also be Asset
                self._inventory_accounts_cache = await coa_manager.get_accounts_for_selection(account_type="Asset", active_only=True)
            if self.app_core.tax_code_service:
                self._tax_codes_cache = await self.app_core.tax_code_service.get_all() # Assumes active

            # Serialize for thread-safe UI update
            def acc_to_dict(acc: Account): return {"id": acc.id, "code": acc.code, "name": acc.name}
            sales_acc_json = json.dumps(list(map(acc_to_dict, self._sales_accounts_cache)))
            purch_acc_json = json.dumps(list(map(acc_to_dict, self._purchase_accounts_cache)))
            inv_acc_json = json.dumps(list(map(acc_to_dict, self._inventory_accounts_cache)))
            tax_codes_json = json.dumps([{"code": tc.code, "description": f"{tc.code} ({tc.rate}%)"} for tc in self._tax_codes_cache])

            QMetaObject.invokeMethod(self, "_populate_combos_slot", Qt.ConnectionType.QueuedConnection, 
                                     Q_ARG(str, sales_acc_json), Q_ARG(str, purch_acc_json),
                                     Q_ARG(str, inv_acc_json), Q_ARG(str, tax_codes_json))
        except Exception as e:
            self.app_core.logger.error(f"Error loading combo data for ProductDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load data for dropdowns: {str(e)}")

    @Slot(str, str, str, str)
    def _populate_combos_slot(self, sales_acc_json: str, purch_acc_json: str, inv_acc_json: str, tax_codes_json: str):
        def populate_combo(combo: QComboBox, json_str: str, data_key: str = "id", name_format="{code} - {name}", add_none=True):
            combo.clear()
            if add_none: combo.addItem("None", 0) # Using 0 as data for "None"
            try:
                items = json.loads(json_str)
                for item in items: combo.addItem(name_format.format(**item), item[data_key])
            except json.JSONDecodeError: self.app_core.logger.error(f"Error parsing JSON for {combo.objectName()}")

        populate_combo(self.sales_account_combo, sales_acc_json, add_none=True)
        populate_combo(self.purchase_account_combo, purch_acc_json, add_none=True)
        populate_combo(self.inventory_account_combo, inv_acc_json, add_none=True)
        populate_combo(self.tax_code_combo, tax_codes_json, data_key="code", name_format="{description}", add_none=True) # tax_code stores code string
        
        if self.loaded_product_data: # If editing, set current values after combos are populated
            self._populate_fields_from_orm(self.loaded_product_data)


    async def _load_existing_product_details(self):
        if not self.product_id or not self.app_core.product_manager: return
        self.loaded_product_data = await self.app_core.product_manager.get_product_for_dialog(self.product_id)
        if self.loaded_product_data:
            product_dict = {col.name: getattr(self.loaded_product_data, col.name) for col in Product.__table__.columns}
            product_json_str = json.dumps(product_dict, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_fields_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, product_json_str))
        else:
            QMessageBox.warning(self, "Load Error", f"Product/Service ID {self.product_id} not found.")
            self.reject()

    @Slot(str)
    def _populate_fields_slot(self, product_json_str: str):
        try:
            data = json.loads(product_json_str, object_hook=json_date_hook)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse product data for editing."); return
        self._populate_fields_from_dict(data)

    def _populate_fields_from_orm(self, product_orm: Product): # Called after combos populated, if editing
        def set_combo_by_data(combo: QComboBox, data_value: Any):
            if data_value is None and combo.itemData(0) == 0 : combo.setCurrentIndex(0); return # Select "None"
            idx = combo.findData(data_value)
            if idx != -1: combo.setCurrentIndex(idx)
            else: self.app_core.logger.warning(f"Value '{data_value}' for combo '{combo.objectName()}' not found.")
        
        set_combo_by_data(self.sales_account_combo, product_orm.sales_account_id)
        set_combo_by_data(self.purchase_account_combo, product_orm.purchase_account_id)
        set_combo_by_data(self.inventory_account_combo, product_orm.inventory_account_id)
        set_combo_by_data(self.tax_code_combo, product_orm.tax_code) # tax_code is string

    def _populate_fields_from_dict(self, data: Dict[str, Any]):
        self.product_code_edit.setText(data.get("product_code", ""))
        self.name_edit.setText(data.get("name", ""))
        self.description_edit.setText(data.get("description", "") or "")
        
        pt_enum_val = data.get("product_type") # This will be string value from DB
        pt_idx = self.product_type_combo.findData(ProductTypeEnum(pt_enum_val) if pt_enum_val else ProductTypeEnum.SERVICE, Qt.ItemDataRole.UserRole) # Find by Enum member
        if pt_idx != -1: self.product_type_combo.setCurrentIndex(pt_idx)
        self._on_product_type_changed(pt_enum_val if pt_enum_val else ProductTypeEnum.SERVICE.value) # Trigger UI update based on type

        self.category_edit.setText(data.get("category", "") or "")
        self.unit_of_measure_edit.setText(data.get("unit_of_measure", "") or "")
        self.barcode_edit.setText(data.get("barcode", "") or "")
        self.sales_price_spin.setValue(float(data.get("sales_price", 0.0) or 0.0))
        self.purchase_price_spin.setValue(float(data.get("purchase_price", 0.0) or 0.0))
        self.min_stock_level_spin.setValue(float(data.get("min_stock_level", 0.0) or 0.0))
        self.reorder_point_spin.setValue(float(data.get("reorder_point", 0.0) or 0.0))
        
        self.is_active_check.setChecked(data.get("is_active", True))
        
        # Combos are set by _populate_fields_from_orm if data was from ORM,
        # or if self.loaded_product_data is None (new entry), they will be default.
        # This call might be redundant if _populate_combos_slot already called _populate_fields_from_orm.
        if self.loaded_product_data: self._populate_fields_from_orm(self.loaded_product_data)


    @Slot()
    def on_save_product(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "No user logged in."); return

        sales_acc_id = self.sales_account_combo.currentData()
        purch_acc_id = self.purchase_account_combo.currentData()
        inv_acc_id = self.inventory_account_combo.currentData()
        tax_code_val = self.tax_code_combo.currentData()

        selected_product_type_enum = self.product_type_combo.currentData()
        if not isinstance(selected_product_type_enum, ProductTypeEnum):
            QMessageBox.warning(self, "Input Error", "Invalid product type selected."); return


        data_dict = {
            "product_code": self.product_code_edit.text().strip(), "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip() or None,
            "product_type": selected_product_type_enum, # Pass the enum member
            "category": self.category_edit.text().strip() or None,
            "unit_of_measure": self.unit_of_measure_edit.text().strip() or None,
            "barcode": self.barcode_edit.text().strip() or None,
            "sales_price": Decimal(str(self.sales_price_spin.value())),
            "purchase_price": Decimal(str(self.purchase_price_spin.value())),
            "sales_account_id": int(sales_acc_id) if sales_acc_id and sales_acc_id !=0 else None,
            "purchase_account_id": int(purch_acc_id) if purch_acc_id and purch_acc_id !=0 else None,
            "inventory_account_id": int(inv_acc_id) if inv_acc_id and inv_acc_id !=0 and selected_product_type_enum == ProductTypeEnum.INVENTORY else None,
            "tax_code": str(tax_code_val) if tax_code_val else None,
            "is_active": self.is_active_check.isChecked(),
            "min_stock_level": Decimal(str(self.min_stock_level_spin.value())) if selected_product_type_enum == ProductTypeEnum.INVENTORY else None,
            "reorder_point": Decimal(str(self.reorder_point_spin.value())) if selected_product_type_enum == ProductTypeEnum.INVENTORY else None,
            "user_id": self.current_user_id
        }

        try:
            if self.product_id: dto = ProductUpdateData(id=self.product_id, **data_dict) # type: ignore
            else: dto = ProductCreateData(**data_dict) # type: ignore
        except ValueError as pydantic_error: 
             QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}"); return

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button: ok_button.setEnabled(False)
        schedule_task_from_qt(self._perform_save(dto)).add_done_callback(
            lambda _: ok_button.setEnabled(True) if ok_button else None)

    async def _perform_save(self, dto: ProductCreateData | ProductUpdateData):
        if not self.app_core.product_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Product Manager not available."))
            return

        result: Result[Product]
        if isinstance(dto, ProductUpdateData): result = await self.app_core.product_manager.update_product(dto.id, dto)
        else: result = await self.app_core.product_manager.create_product(dto)

        if result.is_success and result.value:
            action = "updated" if isinstance(dto, ProductUpdateData) else "created"
            QMessageBox.information(self, "Success", f"Product/Service {action} successfully (ID: {result.value.id}).")
            self.product_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), Q_ARG(str, f"Failed to save product/service:\n{', '.join(result.errors)}"))


```

# app/ui/sales_invoices/__init__.py
```py
# app/ui/sales_invoices/__init__.py
from .sales_invoice_table_model import SalesInvoiceTableModel
from .sales_invoice_dialog import SalesInvoiceDialog
from .sales_invoices_widget import SalesInvoicesWidget # New import

__all__ = [
    "SalesInvoiceTableModel",
    "SalesInvoiceDialog",
    "SalesInvoicesWidget", # Added to __all__
]


```

# app/ui/sales_invoices/sales_invoices_widget.py
```py
# app/ui/sales_invoices/sales_invoices_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox, QComboBox, QDateEdit, QCompleter
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize, QDate
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.sales_invoices.sales_invoice_table_model import SalesInvoiceTableModel
from app.ui.sales_invoices.sales_invoice_dialog import SalesInvoiceDialog
from app.utils.pydantic_models import SalesInvoiceSummaryData, CustomerSummaryData
from app.common.enums import InvoiceStatusEnum
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.sales_invoice import SalesInvoice # For Result type hint

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class SalesInvoicesWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._customers_cache_for_filter: List[CustomerSummaryData] = []
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for SalesInvoicesWidget.")
        except ImportError:
            self.app_core.logger.info("SalesInvoicesWidget: Compiled resources not found. Using direct file paths.")
            
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_customers_for_filter_combo()))
        QTimer.singleShot(100, lambda: self.apply_filter_button.click())


    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        self._create_filter_area()
        self.main_layout.addLayout(self.filter_layout) 

        self.invoices_table = QTableView()
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.invoices_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.invoices_table.horizontalHeader().setStretchLastSection(False)
        self.invoices_table.doubleClicked.connect(self._on_view_invoice_double_click) 
        self.invoices_table.setSortingEnabled(True)

        self.table_model = SalesInvoiceTableModel()
        self.invoices_table.setModel(self.table_model)
        
        header = self.invoices_table.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        id_col_idx = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else -1
        if id_col_idx != -1: self.invoices_table.setColumnHidden(id_col_idx, True)
        
        customer_col_idx = self.table_model._headers.index("Customer") if "Customer" in self.table_model._headers else -1
        if customer_col_idx != -1:
            visible_customer_idx = customer_col_idx
            if id_col_idx != -1 and id_col_idx < customer_col_idx and self.invoices_table.isColumnHidden(id_col_idx):
                 visible_customer_idx -=1
            if not self.invoices_table.isColumnHidden(customer_col_idx):
                 header.setSectionResizeMode(visible_customer_idx, QHeaderView.ResizeMode.Stretch)
        elif self.table_model.columnCount() > 4 : 
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) 


        self.main_layout.addWidget(self.invoices_table)
        self.setLayout(self.main_layout)

        if self.invoices_table.selectionModel():
            self.invoices_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Sales Invoice Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_new_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "New Invoice", self)
        self.toolbar_new_action.triggered.connect(self._on_new_invoice)
        self.toolbar.addAction(self.toolbar_new_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Draft", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_draft_invoice)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_view_action = QAction(QIcon(self.icon_path_prefix + "view.svg"), "View Invoice", self)
        self.toolbar_view_action.triggered.connect(self._on_view_invoice_toolbar)
        self.toolbar.addAction(self.toolbar_view_action)
        
        self.toolbar_post_action = QAction(QIcon(self.icon_path_prefix + "post.svg"), "Post Invoice(s)", self)
        self.toolbar_post_action.triggered.connect(self._on_post_invoice) 
        self.toolbar_post_action.setEnabled(False) 
        self.toolbar.addAction(self.toolbar_post_action)

        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_invoices()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    def _create_filter_area(self):
        self.filter_layout = QHBoxLayout() 
        
        self.filter_layout.addWidget(QLabel("Customer:"))
        self.customer_filter_combo = QComboBox()
        self.customer_filter_combo.setMinimumWidth(200)
        self.customer_filter_combo.addItem("All Customers", 0) 
        self.filter_layout.addWidget(self.customer_filter_combo)

        self.filter_layout.addWidget(QLabel("Status:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem("All Statuses", None) 
        for status_enum in InvoiceStatusEnum:
            self.status_filter_combo.addItem(status_enum.value, status_enum)
        self.filter_layout.addWidget(self.status_filter_combo)

        self.filter_layout.addWidget(QLabel("From:"))
        self.start_date_filter_edit = QDateEdit(QDate.currentDate().addMonths(-3))
        self.start_date_filter_edit.setCalendarPopup(True); self.start_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        self.filter_layout.addWidget(self.start_date_filter_edit)

        self.filter_layout.addWidget(QLabel("To:"))
        self.end_date_filter_edit = QDateEdit(QDate.currentDate())
        self.end_date_filter_edit.setCalendarPopup(True); self.end_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        self.filter_layout.addWidget(self.end_date_filter_edit)

        self.apply_filter_button = QPushButton(QIcon(self.icon_path_prefix + "filter.svg"), "Apply")
        self.apply_filter_button.clicked.connect(lambda: schedule_task_from_qt(self._load_invoices()))
        self.filter_layout.addWidget(self.apply_filter_button)
        
        self.clear_filter_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Clear")
        self.clear_filter_button.clicked.connect(self._clear_filters_and_load)
        self.filter_layout.addWidget(self.clear_filter_button)
        self.filter_layout.addStretch()

    async def _load_customers_for_filter_combo(self):
        if not self.app_core.customer_manager: return
        try:
            result: Result[List[CustomerSummaryData]] = await self.app_core.customer_manager.get_customers_for_listing(active_only=True, page_size=-1) 
            if result.is_success and result.value:
                self._customers_cache_for_filter = result.value
                customers_json = json.dumps([c.model_dump() for c in result.value], default=json_converter)
                QMetaObject.invokeMethod(self, "_populate_customers_filter_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, customers_json))
        except Exception as e:
            self.app_core.logger.error(f"Error loading customers for filter: {e}", exc_info=True)

    @Slot(str)
    def _populate_customers_filter_slot(self, customers_json_str: str):
        self.customer_filter_combo.clear()
        self.customer_filter_combo.addItem("All Customers", 0) 
        try:
            customers_data = json.loads(customers_json_str)
            self._customers_cache_for_filter = [CustomerSummaryData.model_validate(c) for c in customers_data]
            for cust_summary in self._customers_cache_for_filter:
                self.customer_filter_combo.addItem(f"{cust_summary.customer_code} - {cust_summary.name}", cust_summary.id)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Failed to parse customers JSON for filter: {e}")

    @Slot()
    def _clear_filters_and_load(self):
        self.customer_filter_combo.setCurrentIndex(0) 
        self.status_filter_combo.setCurrentIndex(0)   
        self.start_date_filter_edit.setDate(QDate.currentDate().addMonths(-3))
        self.end_date_filter_edit.setDate(QDate.currentDate())
        schedule_task_from_qt(self._load_invoices())

    @Slot()
    def _update_action_states(self):
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        can_edit_draft = False
        can_post_any_selected = False # Changed logic to allow posting multiple drafts
        
        if single_selection:
            row = selected_rows[0].row()
            status = self.table_model.get_invoice_status_at_row(row)
            if status == InvoiceStatusEnum.DRAFT:
                can_edit_draft = True
        
        if selected_rows: # Check if any selected are drafts for posting
            can_post_any_selected = any(
                self.table_model.get_invoice_status_at_row(idx.row()) == InvoiceStatusEnum.DRAFT
                for idx in selected_rows
            )
            
        self.toolbar_edit_action.setEnabled(can_edit_draft) # Edit only single draft
        self.toolbar_view_action.setEnabled(single_selection)
        self.toolbar_post_action.setEnabled(can_post_any_selected) 

    async def _load_invoices(self):
        if not self.app_core.sales_invoice_manager:
            self.app_core.logger.error("SalesInvoiceManager not available."); return
        try:
            cust_id_data = self.customer_filter_combo.currentData()
            customer_id_filter = int(cust_id_data) if cust_id_data and cust_id_data != 0 else None
            
            status_enum_data = self.status_filter_combo.currentData()
            status_filter_val: Optional[InvoiceStatusEnum] = status_enum_data if isinstance(status_enum_data, InvoiceStatusEnum) else None
            
            start_date_filter = self.start_date_filter_edit.date().toPython()
            end_date_filter = self.end_date_filter_edit.date().toPython()

            result: Result[List[SalesInvoiceSummaryData]] = await self.app_core.sales_invoice_manager.get_invoices_for_listing(
                customer_id=customer_id_filter, status=status_filter_val,
                start_date=start_date_filter, end_date=end_date_filter,
                page=1, page_size=200 
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                json_data = json.dumps([dto.model_dump() for dto in data_for_table], default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Failed to load invoices: {', '.join(result.errors)}"))
        except Exception as e:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error loading invoices: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            invoice_summaries: List[SalesInvoiceSummaryData] = [SalesInvoiceSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(invoice_summaries)
        except Exception as e: 
            QMessageBox.critical(self, "Data Error", f"Failed to parse/validate invoice data: {e}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_new_invoice(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = SalesInvoiceDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.invoice_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    def _get_selected_invoice_id_and_status(self) -> tuple[Optional[int], Optional[InvoiceStatusEnum]]:
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1:
            return None, None
        row = selected_rows[0].row()
        inv_id = self.table_model.get_invoice_id_at_row(row)
        inv_status = self.table_model.get_invoice_status_at_row(row)
        return inv_id, inv_status

    @Slot()
    def _on_edit_draft_invoice(self):
        invoice_id, status = self._get_selected_invoice_id_and_status()
        if invoice_id is None: QMessageBox.information(self, "Selection", "Please select a single invoice to edit."); return
        if status != InvoiceStatusEnum.DRAFT: QMessageBox.warning(self, "Edit Error", "Only Draft invoices can be edited."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        
        dialog = SalesInvoiceDialog(self.app_core, self.app_core.current_user.id, invoice_id=invoice_id, parent=self)
        dialog.invoice_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    @Slot()
    def _on_view_invoice_toolbar(self):
        invoice_id, _ = self._get_selected_invoice_id_and_status()
        if invoice_id is None: QMessageBox.information(self, "Selection", "Please select a single invoice to view."); return
        self._show_view_invoice_dialog(invoice_id)

    @Slot(QModelIndex)
    def _on_view_invoice_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        invoice_id = self.table_model.get_invoice_id_at_row(index.row())
        if invoice_id is None: return
        self._show_view_invoice_dialog(invoice_id)

    def _show_view_invoice_dialog(self, invoice_id: int):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = SalesInvoiceDialog(self.app_core, self.app_core.current_user.id, invoice_id=invoice_id, view_only=True, parent=self)
        dialog.exec()
        
    @Slot()
    def _on_post_invoice(self):
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        if not selected_rows: 
            QMessageBox.information(self, "Selection", "Please select one or more Draft invoices to post.")
            return
        
        if not self.app_core.current_user: 
            QMessageBox.warning(self, "Auth Error", "Please log in to post invoices.")
            return

        draft_invoice_ids_to_post: List[int] = []
        non_draft_selected_count = 0
        for index in selected_rows:
            inv_id = self.table_model.get_invoice_id_at_row(index.row())
            status = self.table_model.get_invoice_status_at_row(index.row())
            if inv_id and status == InvoiceStatusEnum.DRAFT:
                draft_invoice_ids_to_post.append(inv_id)
            elif inv_id: # It's a selected non-draft invoice
                non_draft_selected_count += 1
        
        if not draft_invoice_ids_to_post:
            QMessageBox.information(self, "Selection", "No Draft invoices selected for posting.")
            return
        
        warning_message = ""
        if non_draft_selected_count > 0:
            warning_message = f"\n\nNote: {non_draft_selected_count} selected invoice(s) are not in 'Draft' status and will be ignored."

        reply = QMessageBox.question(self, "Confirm Posting", 
                                     f"Are you sure you want to post {len(draft_invoice_ids_to_post)} selected draft invoice(s)?\nThis will create journal entries and change their status to 'Approved'.{warning_message}",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
            
        self.toolbar_post_action.setEnabled(False) # Disable while processing
        schedule_task_from_qt(self._perform_post_invoices(draft_invoice_ids_to_post, self.app_core.current_user.id))


    async def _perform_post_invoices(self, invoice_ids: List[int], user_id: int):
        if not self.app_core.sales_invoice_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Sales Invoice Manager not available."))
            self._update_action_states() # Re-enable button based on current state
            return

        success_count = 0
        failed_posts: List[str] = [] # Store "InvoiceNo: Error"

        for inv_id_to_post in invoice_ids:
            # Fetch invoice number for logging/messaging before attempting to post
            # This is a read, so should be relatively safe outside the main post transaction
            invoice_orm_for_no = await self.app_core.sales_invoice_manager.get_invoice_for_dialog(inv_id_to_post)
            inv_no_str = invoice_orm_for_no.invoice_no if invoice_orm_for_no else f"ID {inv_id_to_post}"

            result: Result[SalesInvoice] = await self.app_core.sales_invoice_manager.post_invoice(inv_id_to_post, user_id)
            if result.is_success:
                success_count += 1
            else:
                failed_posts.append(f"Invoice {inv_no_str}: {', '.join(result.errors)}")
        
        summary_message_parts = []
        if success_count > 0:
            summary_message_parts.append(f"{success_count} invoice(s) posted successfully.")
        if failed_posts:
            summary_message_parts.append(f"{len(failed_posts)} invoice(s) failed to post:")
            summary_message_parts.extend([f"  - {err}" for err in failed_posts])
        
        final_message = "\n".join(summary_message_parts)
        if not final_message: final_message = "No invoices were processed."

        msg_box_method = QMessageBox.information
        title = "Posting Complete"
        if failed_posts and success_count == 0:
            msg_box_method = QMessageBox.critical
            title = "Posting Failed"
        elif failed_posts:
            msg_box_method = QMessageBox.warning
            title = "Posting Partially Successful"
        
        QMetaObject.invokeMethod(msg_box_method, "", Qt.ConnectionType.QueuedConnection, 
            Q_ARG(QWidget, self), Q_ARG(str, title), Q_ARG(str, final_message))
        
        # Refresh list and update button states
        schedule_task_from_qt(self._load_invoices())


    @Slot(int)
    def _refresh_list_after_save(self, invoice_id: int):
        self.app_core.logger.info(f"SalesInvoiceDialog reported save for ID: {invoice_id}. Refreshing list.")
        schedule_task_from_qt(self._load_invoices())


```

# app/ui/sales_invoices/sales_invoice_dialog.py
```py
# app/ui/sales_invoices/sales_invoice_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QCheckBox, QDateEdit, QComboBox, QSpinBox, QTextEdit, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QCompleter,
    QSizePolicy, QApplication, QStyledItemDelegate, QAbstractSpinBox, QLabel, QFrame,
    QGridLayout, QWidget 
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG, QModelIndex 
from PySide6.QtGui import QIcon, QFont, QPalette, QColor
from typing import Optional, List, Dict, Any, TYPE_CHECKING, cast, Union
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import json
from datetime import date as python_date

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import (
    SalesInvoiceCreateData, SalesInvoiceUpdateData, SalesInvoiceLineBaseData,
    CustomerSummaryData, ProductSummaryData 
)
from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.accounting.currency import Currency 
from app.models.accounting.tax_code import TaxCode 
from app.models.business.product import Product 
from app.common.enums import InvoiceStatusEnum, ProductTypeEnum
from app.utils.result import Result
from app.utils.json_helpers import json_converter, json_date_hook
from app.ui.shared.product_search_dialog import ProductSearchDialog

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice, QAbstractItemModel 

class LineItemNumericDelegate(QStyledItemDelegate):
    def __init__(self, decimals=2, allow_negative=False, max_val=999999999.9999, parent=None):
        super().__init__(parent)
        self.decimals = decimals
        self.allow_negative = allow_negative
        self.max_val = max_val

    def createEditor(self, parent: QWidget, option, index: QModelIndex) -> QWidget: # type: ignore
        editor = QDoubleSpinBox(parent)
        editor.setDecimals(self.decimals)
        editor.setMinimum(-self.max_val if self.allow_negative else 0.0)
        editor.setMaximum(self.max_val) 
        editor.setGroupSeparatorShown(True)
        editor.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        return editor

    def setEditorData(self, editor: QDoubleSpinBox, index: QModelIndex):
        value_str = index.model().data(index, Qt.ItemDataRole.EditRole) 
        try:
            val = Decimal(str(value_str if value_str and str(value_str).strip() else '0'))
            editor.setValue(float(val))
        except (TypeError, ValueError, InvalidOperation):
            editor.setValue(0.0)

    def setModelData(self, editor: QDoubleSpinBox, model: "QAbstractItemModel", index: QModelIndex): # type: ignore
        precision_str = '0.01' if self.decimals == 2 else ('0.0001' if self.decimals == 4 else '0.000001')
        
        table_widget_item = None
        if isinstance(self.parent(), QTableWidget) and isinstance(model, QTableWidget): # More robust check
             table_widget_item = self.parent().item(index.row(), index.column())

        if table_widget_item:
            table_widget_item.setText(str(Decimal(str(editor.value())).quantize(Decimal(precision_str), ROUND_HALF_UP)))
        else: 
             model.setData(index, str(Decimal(str(editor.value())).quantize(Decimal(precision_str), ROUND_HALF_UP)), Qt.ItemDataRole.EditRole)


class SalesInvoiceDialog(QDialog):
    invoice_saved = Signal(int) 

    COL_DEL = 0; COL_PROD = 1; COL_DESC = 2; COL_QTY = 3; COL_PRICE = 4
    COL_DISC_PCT = 5; COL_SUBTOTAL = 6; COL_TAX_CODE = 7; COL_TAX_AMT = 8; COL_TOTAL = 9
    
    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 invoice_id: Optional[int] = None, 
                 view_only: bool = False, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core; self.current_user_id = current_user_id
        self.invoice_id = invoice_id; self.view_only_mode = view_only
        self.loaded_invoice_orm: Optional[SalesInvoice] = None
        self.loaded_invoice_data_dict: Optional[Dict[str, Any]] = None
        self._current_search_target_row: Optional[int] = None 

        self._customers_cache: List[Dict[str, Any]] = []
        self._products_cache: List[Dict[str, Any]] = [] 
        self._currencies_cache: List[Dict[str, Any]] = []
        self._tax_codes_cache: List[Dict[str, Any]] = []
        self._base_currency: str = "SGD" 

        self.icon_path_prefix = "resources/icons/"
        try: import app.resources_rc; self.icon_path_prefix = ":/icons/"
        except ImportError: pass
        
        self.setWindowTitle(self._get_window_title())
        self.setMinimumSize(1000, 750); self.setModal(True)
        self._init_ui(); self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_initial_combo_data()))
        if self.invoice_id:
            QTimer.singleShot(100, lambda: schedule_task_from_qt(self._load_existing_invoice_data()))
        elif not self.view_only_mode: self._add_new_invoice_line() 

    def _get_window_title(self) -> str:
        inv_no_str = ""
        if self.loaded_invoice_orm and self.loaded_invoice_orm.invoice_no: inv_no_str = f" ({self.loaded_invoice_orm.invoice_no})"
        elif self.loaded_invoice_data_dict and self.loaded_invoice_data_dict.get("invoice_no"): inv_no_str = f" ({self.loaded_invoice_data_dict.get('invoice_no')})"
        if self.view_only_mode: return f"View Sales Invoice{inv_no_str}"
        if self.invoice_id: return f"Edit Sales Invoice{inv_no_str}"
        return "New Sales Invoice"

    def _init_ui(self):
        main_layout = QVBoxLayout(self); self.header_form = QFormLayout()
        self.header_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows) 
        self.header_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.customer_combo = QComboBox(); self.customer_combo.setEditable(True); self.customer_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert); self.customer_combo.setMinimumWidth(300)
        cust_completer = QCompleter(); cust_completer.setFilterMode(Qt.MatchFlag.MatchContains); cust_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.customer_combo.setCompleter(cust_completer)
        
        self.invoice_no_label = QLabel("To be generated"); self.invoice_no_label.setStyleSheet("font-style: italic; color: grey;")
        
        self.invoice_date_edit = QDateEdit(QDate.currentDate()); self.invoice_date_edit.setCalendarPopup(True); self.invoice_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.due_date_edit = QDateEdit(QDate.currentDate().addDays(30)); self.due_date_edit.setCalendarPopup(True); self.due_date_edit.setDisplayFormat("dd/MM/yyyy")
        
        self.currency_combo = QComboBox()
        self.exchange_rate_spin = QDoubleSpinBox(); self.exchange_rate_spin.setDecimals(6); self.exchange_rate_spin.setRange(0.000001, 999999.0); self.exchange_rate_spin.setValue(1.0)
        
        grid_header_layout = QGridLayout()
        grid_header_layout.addWidget(QLabel("Customer*:"), 0, 0); grid_header_layout.addWidget(self.customer_combo, 0, 1, 1, 2) 
        grid_header_layout.addWidget(QLabel("Invoice Date*:"), 1, 0); grid_header_layout.addWidget(self.invoice_date_edit, 1, 1)
        grid_header_layout.addWidget(QLabel("Invoice No.:"), 0, 3); grid_header_layout.addWidget(self.invoice_no_label, 0, 4)
        grid_header_layout.addWidget(QLabel("Due Date*:"), 1, 3); grid_header_layout.addWidget(self.due_date_edit, 1, 4)
        grid_header_layout.addWidget(QLabel("Currency*:"), 2, 0); grid_header_layout.addWidget(self.currency_combo, 2, 1)
        grid_header_layout.addWidget(QLabel("Exchange Rate:"), 2, 3); grid_header_layout.addWidget(self.exchange_rate_spin, 2, 4)
        grid_header_layout.setColumnStretch(2,1) 
        grid_header_layout.setColumnStretch(5,1) 
        main_layout.addLayout(grid_header_layout)

        self.notes_edit = QTextEdit(); self.notes_edit.setFixedHeight(40); self.header_form.addRow("Notes:", self.notes_edit)
        self.terms_edit = QTextEdit(); self.terms_edit.setFixedHeight(40); self.header_form.addRow("Terms & Conditions:", self.terms_edit)
        main_layout.addLayout(self.header_form) 

        self.lines_table = QTableWidget(); self.lines_table.setColumnCount(self.COL_TOTAL + 1) 
        self.lines_table.setHorizontalHeaderLabels(["", "Product/Service", "Description", "Qty*", "Price*", "Disc %", "Subtotal", "Tax", "Tax Amt", "Total"])
        self._configure_lines_table_columns(); main_layout.addWidget(self.lines_table)
        lines_button_layout = QHBoxLayout()
        self.add_line_button = QPushButton(QIcon(self.icon_path_prefix + "add.svg"), "Add Line")
        self.remove_line_button = QPushButton(QIcon(self.icon_path_prefix + "remove.svg"), "Remove Line")
        lines_button_layout.addWidget(self.add_line_button); lines_button_layout.addWidget(self.remove_line_button); lines_button_layout.addStretch()
        main_layout.addLayout(lines_button_layout)

        totals_form = QFormLayout(); totals_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows); totals_form.setStyleSheet("QLabel { font-weight: bold; } QLineEdit { font-weight: bold; }")
        self.subtotal_display = QLineEdit("0.00"); self.subtotal_display.setReadOnly(True); self.subtotal_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_tax_display = QLineEdit("0.00"); self.total_tax_display.setReadOnly(True); self.total_tax_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.grand_total_display = QLineEdit("0.00"); self.grand_total_display.setReadOnly(True); self.grand_total_display.setAlignment(Qt.AlignmentFlag.AlignRight); self.grand_total_display.setStyleSheet("font-weight: bold; font-size: 14pt;")
        totals_form.addRow("Subtotal:", self.subtotal_display); totals_form.addRow("Total Tax:", self.total_tax_display); totals_form.addRow("Grand Total:", self.grand_total_display)
        align_totals_layout = QHBoxLayout(); align_totals_layout.addStretch(); align_totals_layout.addLayout(totals_form)
        main_layout.addLayout(align_totals_layout)
        
        self.button_box = QDialogButtonBox()
        self.save_draft_button = self.button_box.addButton("Save Draft", QDialogButtonBox.ButtonRole.ActionRole)
        self.save_approve_button = self.button_box.addButton("Save & Approve", QDialogButtonBox.ButtonRole.ActionRole) 
        self.save_approve_button.setToolTip("Save invoice and mark as Approved (posts Journal Entry).")
        self.button_box.addButton(QDialogButtonBox.StandardButton.Close if self.view_only_mode else QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box); self.setLayout(main_layout)

    def _configure_lines_table_columns(self):
        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(self.COL_DEL, QHeaderView.ResizeMode.Fixed); self.lines_table.setColumnWidth(self.COL_DEL, 30)
        header.setSectionResizeMode(self.COL_PROD, QHeaderView.ResizeMode.Interactive); self.lines_table.setColumnWidth(self.COL_PROD, 250) 
        header.setSectionResizeMode(self.COL_DESC, QHeaderView.ResizeMode.Stretch) 
        for col in [self.COL_QTY, self.COL_PRICE, self.COL_DISC_PCT]: 
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive); self.lines_table.setColumnWidth(col,100)
        for col in [self.COL_SUBTOTAL, self.COL_TAX_AMT, self.COL_TOTAL]: 
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive); self.lines_table.setColumnWidth(col,120)
        header.setSectionResizeMode(self.COL_TAX_CODE, QHeaderView.ResizeMode.Interactive); self.lines_table.setColumnWidth(self.COL_TAX_CODE, 150)
        
        self.lines_table.setItemDelegateForColumn(self.COL_QTY, LineItemNumericDelegate(2, self))
        self.lines_table.setItemDelegateForColumn(self.COL_PRICE, LineItemNumericDelegate(4, self)) 
        self.lines_table.setItemDelegateForColumn(self.COL_DISC_PCT, LineItemNumericDelegate(2, False, 100.00, self))

    def _connect_signals(self):
        self.add_line_button.clicked.connect(self._add_new_invoice_line)
        self.remove_line_button.clicked.connect(self._remove_selected_invoice_line)
        self.lines_table.itemChanged.connect(self._on_line_item_changed_desc_only) 
        
        self.save_draft_button.clicked.connect(self.on_save_draft)
        self.save_approve_button.clicked.connect(self.on_save_and_approve) 
        
        close_button = self.button_box.button(QDialogButtonBox.StandardButton.Close)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if close_button: close_button.clicked.connect(self.reject)
        if cancel_button: cancel_button.clicked.connect(self.reject)

        self.customer_combo.currentIndexChanged.connect(self._on_customer_changed)
        self.currency_combo.currentIndexChanged.connect(self._on_currency_changed)
        self.invoice_date_edit.dateChanged.connect(self._on_invoice_date_changed)

    async def _load_initial_combo_data(self):
        try:
            cs_svc = self.app_core.company_settings_service
            if cs_svc: settings = await cs_svc.get_company_settings(); self._base_currency = settings.base_currency if settings else "SGD"

            cust_res: Result[List[CustomerSummaryData]] = await self.app_core.customer_manager.get_customers_for_listing(active_only=True, page_size=-1)
            self._customers_cache = [cs.model_dump() for cs in cust_res.value] if cust_res.is_success and cust_res.value else []
            
            prod_res: Result[List[ProductSummaryData]] = await self.app_core.product_manager.get_products_for_listing(active_only=True, page_size=-1)
            self._products_cache = [ps.model_dump() for ps in prod_res.value] if prod_res.is_success and prod_res.value else []

            if self.app_core.currency_manager:
                curr_orms = await self.app_core.currency_manager.get_all_currencies()
                self._currencies_cache = [{"code":c.code, "name":c.name} for c in curr_orms if c.is_active]
            
            if self.app_core.tax_code_service:
                tc_orms = await self.app_core.tax_code_service.get_all()
                self._tax_codes_cache = [{"code":tc.code, "rate":tc.rate, "description":f"{tc.code} ({tc.rate:.0f}%)"} for tc in tc_orms if tc.is_active] 

            QMetaObject.invokeMethod(self, "_populate_initial_combos_slot", Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            self.app_core.logger.error(f"Error loading combo data for SalesInvoiceDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load initial data for dropdowns: {str(e)}")

    @Slot()
    def _populate_initial_combos_slot(self):
        self.customer_combo.clear(); self.customer_combo.addItem("-- Select Customer --", 0)
        for cust in self._customers_cache: self.customer_combo.addItem(f"{cust['customer_code']} - {cust['name']}", cust['id'])
        if isinstance(self.customer_combo.completer(), QCompleter): self.customer_combo.completer().setModel(self.customer_combo.model()) 

        self.currency_combo.clear()
        for curr in self._currencies_cache: self.currency_combo.addItem(f"{curr['code']} - {curr['name']}", curr['code'])
        base_curr_idx = self.currency_combo.findData(self._base_currency)
        if base_curr_idx != -1: self.currency_combo.setCurrentIndex(base_curr_idx)
        elif self._currencies_cache : self.currency_combo.setCurrentIndex(0) 
        self._on_currency_changed(self.currency_combo.currentIndex())

        if self.loaded_invoice_orm: self._populate_fields_from_orm(self.loaded_invoice_orm)
        elif self.loaded_invoice_data_dict: self._populate_fields_from_dict(self.loaded_invoice_data_dict)
        
        for r in range(self.lines_table.rowCount()): self._populate_line_combos(r)

    async def _load_existing_invoice_data(self):
        if not self.invoice_id or not self.app_core.sales_invoice_manager: return
        self.loaded_invoice_orm = await self.app_core.sales_invoice_manager.get_invoice_for_dialog(self.invoice_id)
        self.setWindowTitle(self._get_window_title()) 
        if self.loaded_invoice_orm:
            inv_dict = {col.name: getattr(self.loaded_invoice_orm, col.name) for col in SalesInvoice.__table__.columns if hasattr(self.loaded_invoice_orm, col.name)}
            inv_dict["lines"] = []
            if self.loaded_invoice_orm.lines: 
                for line_orm in self.loaded_invoice_orm.lines:
                    line_dict = {col.name: getattr(line_orm, col.name) for col in SalesInvoiceLine.__table__.columns if hasattr(line_orm, col.name)}
                    inv_dict["lines"].append(line_dict)
            
            invoice_json_str = json.dumps(inv_dict, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_dialog_from_data_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, invoice_json_str))
        else:
            QMessageBox.warning(self, "Load Error", f"Sales Invoice ID {self.invoice_id} not found.")
            self.reject()

    @Slot(str)
    def _populate_dialog_from_data_slot(self, invoice_json_str: str):
        try:
            data = json.loads(invoice_json_str, object_hook=json_date_hook)
            self.loaded_invoice_data_dict = data 
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse existing invoice data."); return

        self.invoice_no_label.setText(data.get("invoice_no", "N/A"))
        self.invoice_no_label.setStyleSheet("font-style: normal; color: black;" if data.get("invoice_no") else "font-style: italic; color: grey;")
        
        if data.get("invoice_date"): self.invoice_date_edit.setDate(QDate(data["invoice_date"]))
        if data.get("due_date"): self.due_date_edit.setDate(QDate(data["due_date"]))
        
        cust_idx = self.customer_combo.findData(data.get("customer_id"))
        if cust_idx != -1: self.customer_combo.setCurrentIndex(cust_idx)
        else: self.app_core.logger.warning(f"Loaded invoice customer ID '{data.get('customer_id')}' not found in combo.")

        curr_idx = self.currency_combo.findData(data.get("currency_code"))
        if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
        else: self.app_core.logger.warning(f"Loaded invoice currency '{data.get('currency_code')}' not found in combo.")
        self.exchange_rate_spin.setValue(float(data.get("exchange_rate", 1.0) or 1.0))
        self._on_currency_changed(self.currency_combo.currentIndex()) 

        self.notes_edit.setText(data.get("notes", "") or "")
        self.terms_edit.setText(data.get("terms_and_conditions", "") or "")

        self.lines_table.setRowCount(0) 
        for line_data_dict in data.get("lines", []): self._add_new_invoice_line(line_data_dict)
        if not data.get("lines") and not self.view_only_mode: self._add_new_invoice_line()
        
        self._update_invoice_totals() 
        self._set_read_only_state(self.view_only_mode or (data.get("status") != InvoiceStatusEnum.DRAFT.value))

    def _populate_fields_from_orm(self, invoice_orm: SalesInvoice): 
        cust_idx = self.customer_combo.findData(invoice_orm.customer_id)
        if cust_idx != -1: self.customer_combo.setCurrentIndex(cust_idx)
        curr_idx = self.currency_combo.findData(invoice_orm.currency_code)
        if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
    
    def _set_read_only_state(self, read_only: bool):
        self.customer_combo.setEnabled(not read_only)
        for w in [self.invoice_date_edit, self.due_date_edit, self.notes_edit, self.terms_edit]:
            if hasattr(w, 'setReadOnly'): w.setReadOnly(read_only) # type: ignore
        self.currency_combo.setEnabled(not read_only)
        self._on_currency_changed(self.currency_combo.currentIndex()) 
        if read_only: self.exchange_rate_spin.setReadOnly(True)

        self.add_line_button.setEnabled(not read_only)
        self.remove_line_button.setEnabled(not read_only)
        
        is_draft = True 
        if self.loaded_invoice_data_dict:
            is_draft = (self.loaded_invoice_data_dict.get("status") == InvoiceStatusEnum.DRAFT.value)
        elif self.loaded_invoice_orm:
            is_draft = (self.loaded_invoice_orm.status == InvoiceStatusEnum.DRAFT.value)

        can_edit_or_create = not self.view_only_mode and (self.invoice_id is None or is_draft)

        self.save_draft_button.setVisible(can_edit_or_create)
        self.save_approve_button.setVisible(can_edit_or_create)
        self.save_approve_button.setEnabled(can_edit_or_create) 

        edit_trigger = QAbstractItemView.EditTrigger.NoEditTriggers if read_only else QAbstractItemView.EditTrigger.AllInputs
        self.lines_table.setEditTriggers(edit_trigger)
        for r in range(self.lines_table.rowCount()):
            del_btn_widget = self.lines_table.cellWidget(r, self.COL_DEL)
            if del_btn_widget: del_btn_widget.setEnabled(not read_only)
            
            prod_cell_widget = self.lines_table.cellWidget(r, self.COL_PROD)
            if isinstance(prod_cell_widget, QWidget): 
                search_button = prod_cell_widget.findChild(QPushButton)
                if search_button: search_button.setEnabled(not read_only)
                combo = prod_cell_widget.findChild(QComboBox)
                if combo: combo.setEnabled(not read_only)


    def _add_new_invoice_line(self, line_data: Optional[Dict[str, Any]] = None):
        row = self.lines_table.rowCount()
        self.lines_table.insertRow(row)

        del_btn = QPushButton(QIcon(self.icon_path_prefix + "remove.svg")); del_btn.setFixedSize(24,24); del_btn.setToolTip("Remove this line")
        del_btn.clicked.connect(lambda _, r=row: self._remove_specific_invoice_line(r))
        self.lines_table.setCellWidget(row, self.COL_DEL, del_btn)

        prod_cell_widget = QWidget()
        prod_cell_layout = QHBoxLayout(prod_cell_widget)
        prod_cell_layout.setContentsMargins(0,0,0,0); prod_cell_layout.setSpacing(2)
        prod_combo = QComboBox(); prod_combo.setEditable(True); prod_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        prod_completer = QCompleter(); prod_completer.setFilterMode(Qt.MatchFlag.MatchContains); prod_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        prod_combo.setCompleter(prod_completer)
        prod_combo.setMaxVisibleItems(15)
        prod_search_btn = QPushButton("..."); prod_search_btn.setFixedSize(24,24); prod_search_btn.setToolTip("Search Product/Service")
        prod_search_btn.clicked.connect(lambda _, r=row: self._on_open_product_search(r))
        prod_cell_layout.addWidget(prod_combo, 1); prod_cell_layout.addWidget(prod_search_btn)
        self.lines_table.setCellWidget(row, self.COL_PROD, prod_cell_widget)
        
        desc_item = QTableWidgetItem(line_data.get("description", "") if line_data else "")
        self.lines_table.setItem(row, self.COL_DESC, desc_item) 

        qty_spin = QDoubleSpinBox(); qty_spin.setDecimals(2); qty_spin.setRange(0.01, 999999.99); qty_spin.setValue(float(line_data.get("quantity", 1.0) or 1.0) if line_data else 1.0)
        self.lines_table.setCellWidget(row, self.COL_QTY, qty_spin)
        price_spin = QDoubleSpinBox(); price_spin.setDecimals(4); price_spin.setRange(0, 999999.9999); price_spin.setValue(float(line_data.get("unit_price", 0.0) or 0.0) if line_data else 0.0)
        self.lines_table.setCellWidget(row, self.COL_PRICE, price_spin)
        disc_spin = QDoubleSpinBox(); disc_spin.setDecimals(2); disc_spin.setRange(0, 100.00); disc_spin.setValue(float(line_data.get("discount_percent", 0.0) or 0.0) if line_data else 0.0)
        self.lines_table.setCellWidget(row, self.COL_DISC_PCT, disc_spin)

        tax_combo = QComboBox(); self.lines_table.setCellWidget(row, self.COL_TAX_CODE, tax_combo)

        for col_idx in [self.COL_SUBTOTAL, self.COL_TAX_AMT, self.COL_TOTAL]:
            item = QTableWidgetItem("0.00"); item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable); self.lines_table.setItem(row, col_idx, item)

        self._populate_line_combos(row, line_data) 
        
        prod_combo.currentIndexChanged.connect(lambda idx, r=row, pc=prod_combo: self._on_line_product_changed(r, pc.itemData(idx)))
        qty_spin.valueChanged.connect(lambda val, r=row: self._trigger_line_recalculation_slot(r))
        price_spin.valueChanged.connect(lambda val, r=row: self._trigger_line_recalculation_slot(r))
        disc_spin.valueChanged.connect(lambda val, r=row: self._trigger_line_recalculation_slot(r))
        tax_combo.currentIndexChanged.connect(lambda idx, r=row: self._trigger_line_recalculation_slot(r))

        if line_data: self._calculate_line_item_totals(row)
        self._update_invoice_totals()

    def _populate_line_combos(self, row: int, line_data: Optional[Dict[str, Any]] = None):
        prod_cell_widget = self.lines_table.cellWidget(row, self.COL_PROD)
        prod_combo = prod_cell_widget.findChild(QComboBox) if prod_cell_widget else None
        if prod_combo:
            prod_combo.clear(); prod_combo.addItem("-- Select Product/Service --", 0)
            current_prod_id = line_data.get("product_id") if line_data else None
            selected_prod_idx = 0 
            for i, prod_dict in enumerate(self._products_cache):
                price_val = prod_dict.get('sales_price')
                price_str = f"{Decimal(str(price_val)):.2f}" if price_val is not None else "N/A"
                prod_type_val = prod_dict.get('product_type')
                type_str = prod_type_val if isinstance(prod_type_val, str) else (prod_type_val.value if isinstance(prod_type_val, ProductTypeEnum) else "Unknown")
                display_text = f"{prod_dict['product_code']} - {prod_dict['name']} (Type: {type_str}, Price: {price_str})"
                prod_combo.addItem(display_text, prod_dict['id'])
                if prod_dict['id'] == current_prod_id: selected_prod_idx = i + 1
            prod_combo.setCurrentIndex(selected_prod_idx)
            if isinstance(prod_combo.completer(), QCompleter): prod_combo.completer().setModel(prod_combo.model()) # type: ignore
        
        tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, self.COL_TAX_CODE))
        if tax_combo:
            tax_combo.clear(); tax_combo.addItem("None", "") 
            current_tax_code_str = line_data.get("tax_code") if line_data else None
            selected_tax_idx = 0 
            for i, tc_dict in enumerate(self._tax_codes_cache):
                tax_combo.addItem(tc_dict['description'], tc_dict['code']) 
                if tc_dict['code'] == current_tax_code_str: selected_tax_idx = i + 1
            tax_combo.setCurrentIndex(selected_tax_idx)

    @Slot(int)
    def _on_line_product_changed(self, row:int, product_id_data: Any): 
        if not isinstance(product_id_data, int) or product_id_data == 0: 
             self._calculate_line_item_totals(row); return

        product_id = product_id_data
        product_detail = next((p for p in self._products_cache if p['id'] == product_id), None)
        
        if product_detail:
            desc_item = self.lines_table.item(row, self.COL_DESC)
            prod_cell_widget = self.lines_table.cellWidget(row, self.COL_PROD)
            prod_combo = prod_cell_widget.findChild(QComboBox) if prod_cell_widget else None

            if desc_item and prod_combo and (not desc_item.text().strip() or "-- Select Product/Service --" in prod_combo.itemText(0)):
                desc_item.setText(product_detail.get('name', ''))
            
            price_widget = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, self.COL_PRICE))
            if price_widget and price_widget.value() == 0.0 and product_detail.get('sales_price') is not None:
                try: price_widget.setValue(float(Decimal(str(product_detail['sales_price']))))
                except: pass 
            
            tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, self.COL_TAX_CODE))
            if tax_combo and product_detail.get('tax_code'):
                tax_idx = tax_combo.findData(product_detail['tax_code'])
                if tax_idx != -1: tax_combo.setCurrentIndex(tax_idx)

        self._calculate_line_item_totals(row)

    def _remove_selected_invoice_line(self):
        if self.view_only_mode or (self.loaded_invoice_orm and self.loaded_invoice_orm.status != InvoiceStatusEnum.DRAFT.value): return
        current_row = self.lines_table.currentRow()
        if current_row >= 0: self._remove_specific_invoice_line(current_row)

    def _remove_specific_invoice_line(self, row:int):
        if self.view_only_mode or (self.loaded_invoice_orm and self.loaded_invoice_orm.status != InvoiceStatusEnum.DRAFT.value): return
        self.lines_table.removeRow(row); self._update_invoice_totals()

    @Slot(QTableWidgetItem)
    def _on_line_item_changed_desc_only(self, item: QTableWidgetItem): 
        if item.column() == self.COL_DESC: pass 

    @Slot() 
    def _trigger_line_recalculation_slot(self, row_for_recalc: Optional[int] = None):
        current_row = row_for_recalc
        if current_row is None: 
            sender_widget = self.sender()
            if sender_widget and isinstance(sender_widget, QWidget):
                for r in range(self.lines_table.rowCount()):
                    for c in [self.COL_QTY, self.COL_PRICE, self.COL_DISC_PCT, self.COL_TAX_CODE, self.COL_PROD]: 
                        cell_w = self.lines_table.cellWidget(r,c)
                        if isinstance(cell_w, QWidget) and cell_w.isAncestorOf(sender_widget): 
                            current_row = r; break
                        elif cell_w == sender_widget:
                            current_row = r; break
                    if current_row is not None: break
        if current_row is not None: self._calculate_line_item_totals(current_row)

    def _format_decimal_for_cell(self, value: Optional[Decimal], show_zero_as_blank: bool = False) -> str:
        if value is None: return "0.00" if not show_zero_as_blank else ""
        if show_zero_as_blank and value.is_zero(): return ""
        return f"{value:,.2f}"

    def _calculate_line_item_totals(self, row: int):
        try:
            qty_w = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, self.COL_QTY))
            price_w = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, self.COL_PRICE))
            disc_pct_w = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, self.COL_DISC_PCT))
            tax_combo_w = cast(QComboBox, self.lines_table.cellWidget(row, self.COL_TAX_CODE))
            qty = Decimal(str(qty_w.value())) if qty_w else Decimal(0); price = Decimal(str(price_w.value())) if price_w else Decimal(0)
            disc_pct = Decimal(str(disc_pct_w.value())) if disc_pct_w else Decimal(0)
            discount_amount = (qty * price * (disc_pct / Decimal(100))).quantize(Decimal("0.0001"), ROUND_HALF_UP)
            line_subtotal_before_tax = (qty * price) - discount_amount
            tax_code_str = tax_combo_w.currentData() if tax_combo_w and tax_combo_w.currentIndex() > 0 else None
            line_tax_amount = Decimal(0)
            if tax_code_str and line_subtotal_before_tax != Decimal(0):
                tax_code_detail = next((tc for tc in self._tax_codes_cache if tc.get("code") == tax_code_str), None)
                if tax_code_detail and tax_code_detail.get("rate") is not None:
                    rate = Decimal(str(tax_code_detail["rate"]))
                    line_tax_amount = (line_subtotal_before_tax * (rate / Decimal(100))).quantize(Decimal("0.01"), ROUND_HALF_UP)
            line_total = line_subtotal_before_tax + line_tax_amount
            subtotal_item = self.lines_table.item(row, self.COL_SUBTOTAL); tax_amt_item = self.lines_table.item(row, self.COL_TAX_AMT); total_item = self.lines_table.item(row, self.COL_TOTAL)
            if not subtotal_item: subtotal_item = QTableWidgetItem(); self.lines_table.setItem(row, self.COL_SUBTOTAL, subtotal_item)
            subtotal_item.setText(self._format_decimal_for_cell(line_subtotal_before_tax.quantize(Decimal("0.01")), False))
            if not tax_amt_item: tax_amt_item = QTableWidgetItem(); self.lines_table.setItem(row, self.COL_TAX_AMT, tax_amt_item)
            tax_amt_item.setText(self._format_decimal_for_cell(line_tax_amount, True))
            if not total_item: total_item = QTableWidgetItem(); self.lines_table.setItem(row, self.COL_TOTAL, total_item)
            total_item.setText(self._format_decimal_for_cell(line_total.quantize(Decimal("0.01")), False))
        except Exception as e:
            self.app_core.logger.error(f"Error calculating line totals for row {row}: {e}", exc_info=True)
            for col_idx in [self.COL_SUBTOTAL, self.COL_TAX_AMT, self.COL_TOTAL]:
                item = self.lines_table.item(row, col_idx); 
                if item: item.setText("Error")
        finally: self._update_invoice_totals()

    def _update_invoice_totals(self):
        invoice_subtotal_agg = Decimal(0); total_tax_agg = Decimal(0)
        for r in range(self.lines_table.rowCount()):
            try:
                sub_item = self.lines_table.item(r, self.COL_SUBTOTAL); tax_item = self.lines_table.item(r, self.COL_TAX_AMT)
                if sub_item and sub_item.text() and sub_item.text() != "Error": invoice_subtotal_agg += Decimal(sub_item.text().replace(',',''))
                if tax_item and tax_item.text() and tax_item.text() != "Error": total_tax_agg += Decimal(tax_item.text().replace(',',''))
            except (InvalidOperation, AttributeError) as e: self.app_core.logger.warning(f"Could not parse amount from line {r} during total update: {e}")
        grand_total_agg = invoice_subtotal_agg + total_tax_agg
        self.subtotal_display.setText(self._format_decimal_for_cell(invoice_subtotal_agg, False))
        self.total_tax_display.setText(self._format_decimal_for_cell(total_tax_agg, False))
        self.grand_total_display.setText(self._format_decimal_for_cell(grand_total_agg, False))
        
    def _collect_data(self) -> Optional[Union[SalesInvoiceCreateData, SalesInvoiceUpdateData]]:
        customer_id_data = self.customer_combo.currentData()
        if not customer_id_data or customer_id_data == 0: QMessageBox.warning(self, "Validation Error", "Customer must be selected."); return None
        customer_id = int(customer_id_data)
        invoice_date_py = self.invoice_date_edit.date().toPython(); due_date_py = self.due_date_edit.date().toPython()
        if due_date_py < invoice_date_py: QMessageBox.warning(self, "Validation Error", "Due date cannot be before invoice date."); return None
        line_dtos: List[SalesInvoiceLineBaseData] = []
        for r in range(self.lines_table.rowCount()):
            try:
                prod_cell_widget = self.lines_table.cellWidget(r, self.COL_PROD)
                prod_combo = prod_cell_widget.findChild(QComboBox) if prod_cell_widget else None
                desc_item = self.lines_table.item(r, self.COL_DESC); qty_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(r, self.COL_QTY))
                price_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(r, self.COL_PRICE)); disc_pct_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(r, self.COL_DISC_PCT))
                tax_combo = cast(QComboBox, self.lines_table.cellWidget(r, self.COL_TAX_CODE))
                product_id_data = prod_combo.currentData() if prod_combo else None
                product_id = int(product_id_data) if product_id_data and product_id_data != 0 else None
                description = desc_item.text().strip() if desc_item else ""; quantity = Decimal(str(qty_spin.value()))
                unit_price = Decimal(str(price_spin.value())); discount_percent = Decimal(str(disc_pct_spin.value()))
                tax_code_str = tax_combo.currentData() if tax_combo and tax_combo.currentData() else None
                if not description and not product_id: continue 
                if quantity <= 0: QMessageBox.warning(self, "Validation Error", f"Quantity must be positive on line {r+1}."); return None
                if unit_price < 0: QMessageBox.warning(self, "Validation Error", f"Unit price cannot be negative on line {r+1}."); return None
                line_dtos.append(SalesInvoiceLineBaseData(product_id=product_id, description=description, quantity=quantity, unit_price=unit_price, discount_percent=discount_percent, tax_code=tax_code_str))
            except Exception as e: QMessageBox.warning(self, "Input Error", f"Error processing line {r + 1}: {str(e)}"); return None
        if not line_dtos: QMessageBox.warning(self, "Input Error", "Sales invoice must have at least one valid line item."); return None
        common_data = { "customer_id": customer_id, "invoice_date": invoice_date_py, "due_date": due_date_py, "currency_code": self.currency_combo.currentData() or self._base_currency, "exchange_rate": Decimal(str(self.exchange_rate_spin.value())), "notes": self.notes_edit.toPlainText().strip() or None, "terms_and_conditions": self.terms_edit.toPlainText().strip() or None, "user_id": self.current_user_id, "lines": line_dtos }
        try:
            if self.invoice_id: return SalesInvoiceUpdateData(id=self.invoice_id, **common_data) # type: ignore
            else: return SalesInvoiceCreateData(**common_data) # type: ignore
        except ValueError as ve: QMessageBox.warning(self, "Validation Error", f"Data validation failed:\n{str(ve)}"); return None

    @Slot()
    def on_save_draft(self):
        if self.view_only_mode or (self.loaded_invoice_orm and self.loaded_invoice_orm.status != InvoiceStatusEnum.DRAFT.value): QMessageBox.information(self, "Info", "Cannot save. Invoice is not a draft or in view-only mode."); return
        dto = self._collect_data()
        if dto: 
            self._set_buttons_for_async_operation(True)
            future = schedule_task_from_qt(self._perform_save(dto, post_invoice_after=False))
            if future:
                future.add_done_callback(lambda res: QMetaObject.invokeMethod(self, "_safe_set_buttons_for_async_operation_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, False)))
            else:
                self.app_core.logger.error("Failed to schedule _perform_save task in on_save_draft.")
                self._set_buttons_for_async_operation(False)

    @Slot()
    def on_save_and_approve(self):
        if self.view_only_mode or (self.loaded_invoice_orm and self.loaded_invoice_orm.status != InvoiceStatusEnum.DRAFT.value): QMessageBox.information(self, "Info", "Cannot Save & Approve. Invoice is not a draft or in view-only mode."); return
        dto = self._collect_data()
        if dto: 
            self._set_buttons_for_async_operation(True)
            future = schedule_task_from_qt(self._perform_save(dto, post_invoice_after=True))
            if future:
                future.add_done_callback(lambda res: QMetaObject.invokeMethod(self, "_safe_set_buttons_for_async_operation_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, False)))
            else:
                self.app_core.logger.error("Failed to schedule _perform_save task in on_save_and_approve.")
                self._set_buttons_for_async_operation(False)

    @Slot(bool)
    def _safe_set_buttons_for_async_operation_slot(self, busy: bool):
        self._set_buttons_for_async_operation(busy)

    def _set_buttons_for_async_operation(self, busy: bool):
        self.save_draft_button.setEnabled(not busy)
        can_approve = (self.invoice_id is None or (self.loaded_invoice_orm and self.loaded_invoice_orm.status == InvoiceStatusEnum.DRAFT.value)) and not self.view_only_mode
        self.save_approve_button.setEnabled(not busy and can_approve)

    async def _perform_save(self, dto: Union[SalesInvoiceCreateData, SalesInvoiceUpdateData], post_invoice_after: bool):
        if not self.app_core.sales_invoice_manager: QMessageBox.critical(self, "Error", "Sales Invoice Manager not available."); return
        save_result: Result[SalesInvoice]; is_update = isinstance(dto, SalesInvoiceUpdateData); action_verb_past = "updated" if is_update else "created"
        if is_update: save_result = await self.app_core.sales_invoice_manager.update_draft_invoice(dto.id, dto) 
        else: save_result = await self.app_core.sales_invoice_manager.create_draft_invoice(dto) 
        if not save_result.is_success or not save_result.value: QMessageBox.warning(self, "Save Error", f"Failed to {('update' if is_update else 'create')} sales invoice draft:\n{', '.join(save_result.errors)}"); return 
        saved_invoice = save_result.value; self.invoice_saved.emit(saved_invoice.id); self.invoice_id = saved_invoice.id; self.loaded_invoice_orm = saved_invoice; self.setWindowTitle(self._get_window_title()); self.invoice_no_label.setText(saved_invoice.invoice_no); self.invoice_no_label.setStyleSheet("font-style: normal; color: black;")
        if not post_invoice_after: QMessageBox.information(self, "Success", f"Sales Invoice draft {action_verb_past} successfully (ID: {saved_invoice.id}, No: {saved_invoice.invoice_no})."); self._set_read_only_state(self.view_only_mode or (saved_invoice.status != InvoiceStatusEnum.DRAFT.value)); return
        post_result: Result[SalesInvoice] = await self.app_core.sales_invoice_manager.post_invoice(saved_invoice.id, self.current_user_id)
        if post_result.is_success: QMessageBox.information(self, "Success", f"Sales Invoice {saved_invoice.invoice_no} saved and posted successfully. JE created."); self.accept()
        else: msg = (f"Sales Invoice {saved_invoice.invoice_no} was saved as a Draft successfully, BUT FAILED to post/approve:\n{', '.join(post_result.errors)}\n\nPlease review and post manually from the invoice list."); QMessageBox.warning(self, "Posting Error After Save", msg); self._set_read_only_state(self.view_only_mode or (saved_invoice.status != InvoiceStatusEnum.DRAFT.value))

    @Slot(int)
    def _on_customer_changed(self, index: int):
        customer_id = self.customer_combo.itemData(index)
        if customer_id and customer_id != 0 and self._customers_cache:
            customer_data = next((c for c in self._customers_cache if c.get("id") == customer_id), None)
            if customer_data and customer_data.get("currency_code"):
                curr_idx = self.currency_combo.findData(customer_data["currency_code"])
                if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
            if customer_data and customer_data.get("credit_terms") is not None: self.due_date_edit.setDate(self.invoice_date_edit.date().addDays(int(customer_data["credit_terms"])))

    @Slot(int)
    def _on_currency_changed(self, index: int):
        currency_code = self.currency_combo.currentData(); is_base = (currency_code == self._base_currency)
        self.exchange_rate_spin.setEnabled(not is_base and not self.view_only_mode); self.exchange_rate_spin.setReadOnly(is_base or self.view_only_mode); 
        if is_base: self.exchange_rate_spin.setValue(1.0)

    @Slot(QDate)
    def _on_invoice_date_changed(self, new_date: QDate):
        customer_id = self.customer_combo.currentData(); terms = 30 
        if customer_id and customer_id != 0 and self._customers_cache:
            customer_data = next((c for c in self._customers_cache if c.get("id") == customer_id), None)
            if customer_data and customer_data.get("credit_terms") is not None:
                try: terms = int(customer_data["credit_terms"])
                except: pass
        self.due_date_edit.setDate(new_date.addDays(terms))

    @Slot(int)
    def _on_open_product_search(self, row: int):
        self._current_search_target_row = row
        search_dialog = ProductSearchDialog(self.app_core, self)
        search_dialog.product_selected.connect(self._handle_product_selected_from_search)
        search_dialog.exec()

    @Slot(object)
    def _handle_product_selected_from_search(self, product_summary_dict_obj: object):
        if self._current_search_target_row is None: return
        target_row = self._current_search_target_row
        
        try:
            product_data_dict = cast(Dict[str, Any], product_summary_dict_obj)
            product_id = product_data_dict.get("id")
            if product_id is None: return

            prod_cell_widget = self.lines_table.cellWidget(target_row, self.COL_PROD)
            prod_combo = prod_cell_widget.findChild(QComboBox) if prod_cell_widget else None
            
            if prod_combo:
                found_idx = prod_combo.findData(product_id)
                if found_idx != -1:
                    prod_combo.setCurrentIndex(found_idx) 
                else: 
                    self.app_core.logger.warning(f"Product ID {product_id} selected from search not found in line combo for row {target_row}. Forcing _on_line_product_changed.")
                    self._on_line_product_changed(target_row, product_id) 
            else:
                self.app_core.logger.error(f"Product combo not found for row {target_row} in SalesInvoiceDialog.")

        except Exception as e:
            self.app_core.logger.error(f"Error handling product selected from search: {e}", exc_info=True)
            QMessageBox.warning(self, "Product Selection Error", f"Could not apply selected product: {str(e)}")
        finally:
            self._current_search_target_row = None


```

# app/ui/sales_invoices/sales_invoice_table_model.py
```py
# app/ui/sales_invoices/sales_invoice_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from datetime import date as python_date

from app.utils.pydantic_models import SalesInvoiceSummaryData
from app.common.enums import InvoiceStatusEnum

class SalesInvoiceTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[SalesInvoiceSummaryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = [
            "ID", "Inv No.", "Inv Date", "Due Date", 
            "Customer", "Total", "Paid", "Balance", "Status"
        ]
        self._data: List[SalesInvoiceSummaryData] = data or []

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

    def _format_decimal_for_table(self, value: Optional[Decimal], show_zero_as_blank: bool = False) -> str:
        if value is None: 
            return "0.00" if not show_zero_as_blank else ""
        try:
            d_value = Decimal(str(value))
            if show_zero_as_blank and d_value == Decimal(0):
                return ""
            return f"{d_value:,.2f}"
        except (InvalidOperation, TypeError):
            return str(value) # Fallback

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        invoice_summary: SalesInvoiceSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            header_key = self._headers[col].lower().replace('.', '').replace(' ', '_')
            
            if col == 0: return str(invoice_summary.id)
            if col == 1: return invoice_summary.invoice_no
            if col == 2: # Inv Date
                inv_date = invoice_summary.invoice_date
                return inv_date.strftime('%d/%m/%Y') if isinstance(inv_date, python_date) else str(inv_date)
            if col == 3: # Due Date
                due_date = invoice_summary.due_date
                return due_date.strftime('%d/%m/%Y') if isinstance(due_date, python_date) else str(due_date)
            if col == 4: return invoice_summary.customer_name
            if col == 5: return self._format_decimal_for_table(invoice_summary.total_amount, False) # Total
            if col == 6: return self._format_decimal_for_table(invoice_summary.amount_paid, True)  # Paid
            if col == 7: # Balance
                balance = invoice_summary.total_amount - invoice_summary.amount_paid
                return self._format_decimal_for_table(balance, False)
            if col == 8: # Status
                status_val = invoice_summary.status
                return status_val.value if isinstance(status_val, InvoiceStatusEnum) else str(status_val)
            
            return str(getattr(invoice_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole: # Store ID for quick retrieval
            if col == 0: 
                return invoice_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] in ["Total", "Paid", "Balance"]:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if self._headers[col] == "Status":
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_invoice_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            return self._data[row].id 
        return None
        
    def get_invoice_status_at_row(self, row: int) -> Optional[InvoiceStatusEnum]:
        if 0 <= row < len(self._data):
            status_val = self._data[row].status
            return status_val if isinstance(status_val, InvoiceStatusEnum) else None
        return None

    def update_data(self, new_data: List[SalesInvoiceSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()


```

# app/ui/audit/__init__.py
```py
# File: app/ui/audit/__init__.py
from .audit_log_table_model import AuditLogTableModel
from .data_change_history_table_model import DataChangeHistoryTableModel
from .audit_log_widget import AuditLogWidget # New Import

__all__ = [
    "AuditLogTableModel",
    "DataChangeHistoryTableModel",
    "AuditLogWidget", # New Export
]

```

# app/ui/audit/audit_log_table_model.py
```py
# File: app/ui/audit/audit_log_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Optional, Any
from datetime import datetime

from app.utils.pydantic_models import AuditLogEntryData

class AuditLogTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[AuditLogEntryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = [
            "ID", "Timestamp", "User", "Action", "Entity Type", 
            "Entity ID", "Entity Name", "Changes Summary", "IP Address"
        ]
        self._data: List[AuditLogEntryData] = data or []

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

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        log_entry: AuditLogEntryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(log_entry.id)
            if col == 1: # Timestamp
                ts = log_entry.timestamp
                return ts.strftime('%d/%m/%Y %H:%M:%S') if isinstance(ts, datetime) else str(ts)
            if col == 2: return log_entry.username or "N/A"
            if col == 3: return log_entry.action
            if col == 4: return log_entry.entity_type
            if col == 5: return str(log_entry.entity_id) if log_entry.entity_id is not None else ""
            if col == 6: return log_entry.entity_name or ""
            if col == 7: return log_entry.changes_summary or ""
            if col == 8: return log_entry.ip_address or ""
            return ""

        elif role == Qt.ItemDataRole.UserRole: # Store full DTO for potential detail view
            return log_entry
        
        return None

    def get_log_entry_at_row(self, row: int) -> Optional[AuditLogEntryData]:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None

    def update_data(self, new_data: List[AuditLogEntryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

```

# app/ui/audit/data_change_history_table_model.py
```py
# File: app/ui/audit/data_change_history_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Optional, Any
from datetime import datetime

from app.utils.pydantic_models import DataChangeHistoryEntryData
from app.common.enums import DataChangeTypeEnum

class DataChangeHistoryTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[DataChangeHistoryEntryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = [
            "ID", "Changed At", "Table", "Record ID", "Field", 
            "Old Value", "New Value", "Change Type", "Changed By"
        ]
        self._data: List[DataChangeHistoryEntryData] = data or []

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

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        history_entry: DataChangeHistoryEntryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(history_entry.id)
            if col == 1: # Changed At
                ts = history_entry.changed_at
                return ts.strftime('%d/%m/%Y %H:%M:%S') if isinstance(ts, datetime) else str(ts)
            if col == 2: return history_entry.table_name
            if col == 3: return str(history_entry.record_id)
            if col == 4: return history_entry.field_name
            if col == 5: return str(history_entry.old_value)[:200] if history_entry.old_value is not None else "" # Truncate long values
            if col == 6: return str(history_entry.new_value)[:200] if history_entry.new_value is not None else "" # Truncate long values
            if col == 7: # Change Type
                return history_entry.change_type.value if isinstance(history_entry.change_type, DataChangeTypeEnum) else str(history_entry.change_type)
            if col == 8: return history_entry.changed_by_username or "N/A"
            return ""
            
        elif role == Qt.ItemDataRole.UserRole: # Store full DTO
            return history_entry
            
        return None

    def get_history_entry_at_row(self, row: int) -> Optional[DataChangeHistoryEntryData]:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None

    def update_data(self, new_data: List[DataChangeHistoryEntryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

```

# app/ui/audit/audit_log_widget.py
```py
# app/ui/audit/audit_log_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QHeaderView, QAbstractItemView, QMessageBox, QLabel, QLineEdit, 
    QComboBox, QDateEdit, QTabWidget, QTextEdit, QSplitter, QGroupBox,
    QSpinBox, QFormLayout # Added QFormLayout
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QDate
from PySide6.QtGui import QIcon
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Tuple

import json
from datetime import datetime, time

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.audit.audit_log_table_model import AuditLogTableModel
from app.ui.audit.data_change_history_table_model import DataChangeHistoryTableModel
from app.utils.pydantic_models import AuditLogEntryData, DataChangeHistoryEntryData, UserSummaryData
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class AuditLogWidget(QWidget):
    DEFAULT_PAGE_SIZE = 50

    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self._users_cache: List[UserSummaryData] = []
        
        self._action_log_current_page = 1
        self._action_log_total_records = 0
        self._action_log_page_size = self.DEFAULT_PAGE_SIZE

        self._data_change_current_page = 1
        self._data_change_total_records = 0
        self._data_change_page_size = self.DEFAULT_PAGE_SIZE
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass
        
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_initial_filter_data()))


    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()

        self._create_action_log_tab()
        self._create_data_change_history_tab()

        self.main_layout.addWidget(self.tab_widget)
        self.setLayout(self.main_layout)

    def _create_filter_group(self, title: str) -> Tuple[QGroupBox, QFormLayout]:
        group = QGroupBox(title)
        layout = QFormLayout(group)
        layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        return group, layout

    # --- Action Log Tab ---
    def _create_action_log_tab(self):
        action_log_widget = QWidget()
        layout = QVBoxLayout(action_log_widget)

        filter_group, filter_form = self._create_filter_group("Filter Action Log")
        
        self.al_user_filter_combo = QComboBox(); self.al_user_filter_combo.addItem("All Users", 0)
        filter_form.addRow("User:", self.al_user_filter_combo)

        self.al_action_filter_edit = QLineEdit(); self.al_action_filter_edit.setPlaceholderText("e.g., Insert, Update")
        filter_form.addRow("Action:", self.al_action_filter_edit)
        
        self.al_entity_type_filter_edit = QLineEdit(); self.al_entity_type_filter_edit.setPlaceholderText("e.g., core.users, business.sales_invoices")
        filter_form.addRow("Entity Type:", self.al_entity_type_filter_edit)

        self.al_entity_id_filter_spin = QSpinBox(); self.al_entity_id_filter_spin.setRange(0, 99999999); self.al_entity_id_filter_spin.setSpecialValueText("Any ID")
        filter_form.addRow("Entity ID:", self.al_entity_id_filter_spin)

        date_filter_layout = QHBoxLayout()
        self.al_start_date_filter_edit = QDateEdit(QDate.currentDate().addDays(-7)); self.al_start_date_filter_edit.setCalendarPopup(True); self.al_start_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        self.al_end_date_filter_edit = QDateEdit(QDate.currentDate()); self.al_end_date_filter_edit.setCalendarPopup(True); self.al_end_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        date_filter_layout.addWidget(QLabel("From:")); date_filter_layout.addWidget(self.al_start_date_filter_edit)
        date_filter_layout.addWidget(QLabel("To:")); date_filter_layout.addWidget(self.al_end_date_filter_edit)
        filter_form.addRow(date_filter_layout)

        al_filter_buttons_layout = QHBoxLayout()
        self.al_apply_filter_button = QPushButton(QIcon(self.icon_path_prefix + "filter.svg"), "Apply Filters")
        self.al_clear_filter_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Clear Filters")
        al_filter_buttons_layout.addStretch(); al_filter_buttons_layout.addWidget(self.al_apply_filter_button); al_filter_buttons_layout.addWidget(self.al_clear_filter_button)
        filter_form.addRow(al_filter_buttons_layout)
        layout.addWidget(filter_group)

        al_splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.action_log_table = QTableView()
        self.action_log_table.setAlternatingRowColors(True)
        self.action_log_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.action_log_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.action_log_table.horizontalHeader().setStretchLastSection(True)
        self.action_log_table_model = AuditLogTableModel()
        self.action_log_table.setModel(self.action_log_table_model)
        self.action_log_table.setColumnHidden(self.action_log_table_model._headers.index("ID"), True)
        al_splitter.addWidget(self.action_log_table)

        self.al_changes_detail_edit = QTextEdit(); self.al_changes_detail_edit.setReadOnly(True)
        self.al_changes_detail_edit.setPlaceholderText("Select a log entry to view change details...")
        al_splitter.addWidget(self.al_changes_detail_edit)
        al_splitter.setSizes([400, 200]) 
        layout.addWidget(al_splitter)

        al_pagination_layout = QHBoxLayout()
        self.al_prev_page_button = QPushButton("Previous"); self.al_prev_page_button.setEnabled(False)
        self.al_page_info_label = QLabel("Page 1 of 1 (0 records)")
        self.al_next_page_button = QPushButton("Next"); self.al_next_page_button.setEnabled(False)
        al_pagination_layout.addStretch(); al_pagination_layout.addWidget(self.al_prev_page_button); al_pagination_layout.addWidget(self.al_page_info_label); al_pagination_layout.addWidget(self.al_next_page_button); al_pagination_layout.addStretch()
        layout.addLayout(al_pagination_layout)

        self.tab_widget.addTab(action_log_widget, "Action Log")

        self.al_apply_filter_button.clicked.connect(lambda: self._load_audit_logs_page(1))
        self.al_clear_filter_button.clicked.connect(self._clear_action_log_filters)
        self.action_log_table.selectionModel().selectionChanged.connect(self._on_action_log_selection_changed)
        self.al_prev_page_button.clicked.connect(lambda: self._load_audit_logs_page(self._action_log_current_page - 1))
        self.al_next_page_button.clicked.connect(lambda: self._load_audit_logs_page(self._action_log_current_page + 1))

    def _create_data_change_history_tab(self):
        data_change_widget = QWidget()
        layout = QVBoxLayout(data_change_widget)

        filter_group, filter_form = self._create_filter_group("Filter Data Changes")

        self.dch_table_name_filter_edit = QLineEdit(); self.dch_table_name_filter_edit.setPlaceholderText("e.g., accounting.accounts")
        filter_form.addRow("Table Name:", self.dch_table_name_filter_edit)

        self.dch_record_id_filter_spin = QSpinBox(); self.dch_record_id_filter_spin.setRange(0, 99999999); self.dch_record_id_filter_spin.setSpecialValueText("Any ID")
        filter_form.addRow("Record ID:", self.dch_record_id_filter_spin)

        self.dch_user_filter_combo = QComboBox(); self.dch_user_filter_combo.addItem("All Users", 0)
        filter_form.addRow("Changed By User:", self.dch_user_filter_combo)

        dch_date_filter_layout = QHBoxLayout()
        self.dch_start_date_filter_edit = QDateEdit(QDate.currentDate().addDays(-7)); self.dch_start_date_filter_edit.setCalendarPopup(True); self.dch_start_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        self.dch_end_date_filter_edit = QDateEdit(QDate.currentDate()); self.dch_end_date_filter_edit.setCalendarPopup(True); self.dch_end_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        dch_date_filter_layout.addWidget(QLabel("From:")); dch_date_filter_layout.addWidget(self.dch_start_date_filter_edit)
        dch_date_filter_layout.addWidget(QLabel("To:")); dch_date_filter_layout.addWidget(self.dch_end_date_filter_edit)
        filter_form.addRow(dch_date_filter_layout)

        dch_filter_buttons_layout = QHBoxLayout()
        self.dch_apply_filter_button = QPushButton(QIcon(self.icon_path_prefix + "filter.svg"), "Apply Filters")
        self.dch_clear_filter_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Clear Filters")
        dch_filter_buttons_layout.addStretch(); dch_filter_buttons_layout.addWidget(self.dch_apply_filter_button); dch_filter_buttons_layout.addWidget(self.dch_clear_filter_button)
        filter_form.addRow(dch_filter_buttons_layout)
        layout.addWidget(filter_group)

        self.data_change_table = QTableView()
        self.data_change_table.setAlternatingRowColors(True)
        self.data_change_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.data_change_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.data_change_table.horizontalHeader().setStretchLastSection(False) 
        self.data_change_table_model = DataChangeHistoryTableModel()
        self.data_change_table.setModel(self.data_change_table_model)
        self.data_change_table.setColumnHidden(self.data_change_table_model._headers.index("ID"), True)
        
        for i in range(self.data_change_table_model.columnCount()):
            self.data_change_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        if "Old Value" in self.data_change_table_model._headers:
            self.data_change_table.horizontalHeader().setSectionResizeMode(self.data_change_table_model._headers.index("Old Value"), QHeaderView.ResizeMode.Stretch)
        if "New Value" in self.data_change_table_model._headers:
            self.data_change_table.horizontalHeader().setSectionResizeMode(self.data_change_table_model._headers.index("New Value"), QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.data_change_table)

        dch_pagination_layout = QHBoxLayout()
        self.dch_prev_page_button = QPushButton("Previous"); self.dch_prev_page_button.setEnabled(False)
        self.dch_page_info_label = QLabel("Page 1 of 1 (0 records)")
        self.dch_next_page_button = QPushButton("Next"); self.dch_next_page_button.setEnabled(False)
        dch_pagination_layout.addStretch(); dch_pagination_layout.addWidget(self.dch_prev_page_button); dch_pagination_layout.addWidget(self.dch_page_info_label); dch_pagination_layout.addWidget(self.dch_next_page_button); dch_pagination_layout.addStretch()
        layout.addLayout(dch_pagination_layout)

        self.tab_widget.addTab(data_change_widget, "Data Change History")
        
        self.dch_apply_filter_button.clicked.connect(lambda: self._load_data_changes_page(1))
        self.dch_clear_filter_button.clicked.connect(self._clear_data_change_filters)
        self.dch_prev_page_button.clicked.connect(lambda: self._load_data_changes_page(self._data_change_current_page - 1))
        self.dch_next_page_button.clicked.connect(lambda: self._load_data_changes_page(self._data_change_current_page + 1))

    async def _load_initial_filter_data(self):
        if self.app_core.security_manager:
            users = await self.app_core.security_manager.get_all_users_summary()
            self._users_cache = users
            user_items_json = json.dumps([u.model_dump(mode='json') for u in users])
            QMetaObject.invokeMethod(self, "_populate_user_filters_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, user_items_json))
        
        self._load_audit_logs_page(1)
        self._load_data_changes_page(1)

    @Slot(str)
    def _populate_user_filters_slot(self, users_json_str: str):
        try:
            users_data = json.loads(users_json_str)
            self._users_cache = [UserSummaryData.model_validate(u) for u in users_data]
            
            current_al_user = self.al_user_filter_combo.currentData()
            current_dch_user = self.dch_user_filter_combo.currentData()

            self.al_user_filter_combo.clear(); self.al_user_filter_combo.addItem("All Users", 0)
            self.dch_user_filter_combo.clear(); self.dch_user_filter_combo.addItem("All Users", 0)
            
            for user_summary in self._users_cache:
                display_text = f"{user_summary.username} ({user_summary.full_name or 'N/A'})"
                self.al_user_filter_combo.addItem(display_text, user_summary.id)
                self.dch_user_filter_combo.addItem(display_text, user_summary.id)
            
            if current_al_user: self.al_user_filter_combo.setCurrentIndex(self.al_user_filter_combo.findData(current_al_user))
            if current_dch_user: self.dch_user_filter_combo.setCurrentIndex(self.dch_user_filter_combo.findData(current_dch_user))

        except json.JSONDecodeError:
            self.app_core.logger.error("Failed to parse users for audit log filters.")

    @Slot()
    def _clear_action_log_filters(self):
        self.al_user_filter_combo.setCurrentIndex(0)
        self.al_action_filter_edit.clear()
        self.al_entity_type_filter_edit.clear()
        self.al_entity_id_filter_spin.setValue(0)
        self.al_start_date_filter_edit.setDate(QDate.currentDate().addDays(-7))
        self.al_end_date_filter_edit.setDate(QDate.currentDate())
        self._load_audit_logs_page(1)

    def _load_audit_logs_page(self, page_number: int):
        self._action_log_current_page = page_number
        schedule_task_from_qt(self._fetch_audit_logs())

    async def _fetch_audit_logs(self):
        if not self.app_core.audit_log_service: return
        
        user_id = self.al_user_filter_combo.currentData()
        start_dt = datetime.combine(self.al_start_date_filter_edit.date().toPython(), time.min)
        end_dt = datetime.combine(self.al_end_date_filter_edit.date().toPython(), time.max)

        logs, total_records = await self.app_core.audit_log_service.get_audit_logs_paginated(
            user_id_filter=int(user_id) if user_id and user_id != 0 else None,
            action_filter=self.al_action_filter_edit.text().strip() or None,
            entity_type_filter=self.al_entity_type_filter_edit.text().strip() or None,
            entity_id_filter=self.al_entity_id_filter_spin.value() if self.al_entity_id_filter_spin.value() != 0 else None,
            start_date_filter=start_dt,
            end_date_filter=end_dt,
            page=self._action_log_current_page,
            page_size=self._action_log_page_size
        )
        self._action_log_total_records = total_records
        
        logs_json = json.dumps([log.model_dump(mode='json') for log in logs], default=json_converter)
        QMetaObject.invokeMethod(self, "_update_action_log_table_slot", Qt.ConnectionType.QueuedConnection, 
                                 Q_ARG(str, logs_json))
        self._update_action_log_pagination_controls()

    @Slot(str)
    def _update_action_log_table_slot(self, logs_json_str: str):
        try:
            log_dicts = json.loads(logs_json_str, object_hook=json_date_hook)
            log_entries = [AuditLogEntryData.model_validate(d) for d in log_dicts]
            self.action_log_table_model.update_data(log_entries)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to display action logs: {e}")
        self.al_changes_detail_edit.clear()

    def _update_action_log_pagination_controls(self):
        total_pages = (self._action_log_total_records + self._action_log_page_size - 1) // self._action_log_page_size
        if total_pages == 0: total_pages = 1 
        self.al_page_info_label.setText(f"Page {self._action_log_current_page} of {total_pages} ({self._action_log_total_records} records)")
        self.al_prev_page_button.setEnabled(self._action_log_current_page > 1)
        self.al_next_page_button.setEnabled(self._action_log_current_page < total_pages)
        
    @Slot(QModelIndex, QModelIndex)
    def _on_action_log_selection_changed(self, selected: QModelIndex, deselected: QModelIndex):
        selected_rows = self.action_log_table.selectionModel().selectedRows()
        if selected_rows:
            log_entry = self.action_log_table_model.get_log_entry_at_row(selected_rows[0].row())
            if log_entry and log_entry.changes_summary:
                self.al_changes_detail_edit.setText(log_entry.changes_summary)
            else:
                self.al_changes_detail_edit.clear()
        else:
            self.al_changes_detail_edit.clear()

    @Slot()
    def _clear_data_change_filters(self):
        self.dch_table_name_filter_edit.clear()
        self.dch_record_id_filter_spin.setValue(0)
        self.dch_user_filter_combo.setCurrentIndex(0)
        self.dch_start_date_filter_edit.setDate(QDate.currentDate().addDays(-7))
        self.dch_end_date_filter_edit.setDate(QDate.currentDate())
        self._load_data_changes_page(1)

    def _load_data_changes_page(self, page_number: int):
        self._data_change_current_page = page_number
        schedule_task_from_qt(self._fetch_data_changes())

    async def _fetch_data_changes(self):
        if not self.app_core.audit_log_service: return

        user_id = self.dch_user_filter_combo.currentData()
        start_dt = datetime.combine(self.dch_start_date_filter_edit.date().toPython(), time.min)
        end_dt = datetime.combine(self.dch_end_date_filter_edit.date().toPython(), time.max)

        history_entries, total_records = await self.app_core.audit_log_service.get_data_change_history_paginated(
            table_name_filter=self.dch_table_name_filter_edit.text().strip() or None,
            record_id_filter=self.dch_record_id_filter_spin.value() if self.dch_record_id_filter_spin.value() != 0 else None,
            changed_by_user_id_filter=int(user_id) if user_id and user_id != 0 else None,
            start_date_filter=start_dt,
            end_date_filter=end_dt,
            page=self._data_change_current_page,
            page_size=self._data_change_page_size
        )
        self._data_change_total_records = total_records
        
        history_json = json.dumps([h.model_dump(mode='json') for h in history_entries], default=json_converter)
        QMetaObject.invokeMethod(self, "_update_data_change_table_slot", Qt.ConnectionType.QueuedConnection,
                                 Q_ARG(str, history_json))
        self._update_data_change_pagination_controls()

    @Slot(str)
    def _update_data_change_table_slot(self, history_json_str: str):
        try:
            history_dicts = json.loads(history_json_str, object_hook=json_date_hook)
            history_entries = [DataChangeHistoryEntryData.model_validate(d) for d in history_dicts]
            self.data_change_table_model.update_data(history_entries)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to display data change history: {e}")
    
    def _update_data_change_pagination_controls(self):
        total_pages = (self._data_change_total_records + self._data_change_page_size - 1) // self._data_change_page_size
        if total_pages == 0: total_pages = 1
        self.dch_page_info_label.setText(f"Page {self._data_change_current_page} of {total_pages} ({self._data_change_total_records} records)")
        self.dch_prev_page_button.setEnabled(self._data_change_current_page > 1)
        self.dch_next_page_button.setEnabled(self._data_change_current_page < total_pages)


```

