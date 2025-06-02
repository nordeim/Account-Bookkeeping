<think>
The user has encountered another `NameError`, this time `NameError: name 'QFormLayout' is not defined` in `app/ui/banking/bank_reconciliation_widget.py`.

**1. Deeply Understand Requirements:**
The goal is to fix this `NameError`. It means `QFormLayout` was used without being imported from `PySide6.QtWidgets`. I need to provide a complete, corrected version of `bank_reconciliation_widget.py`.

**2. Systematic Diagnosis:**

*   **Error Message**: `NameError: name 'QFormLayout' is not defined. Did you mean: 'QVBoxLayout'?`
*   **File**: `app/ui/banking/bank_reconciliation_widget.py`
*   **Line**: The error occurs at line 78 in the `_init_ui` method, where `QFormLayout` is instantiated: `summary_layout = QFormLayout(summary_group)`.
*   **Root Cause**: The class `QFormLayout` is used, but it has not been imported from `PySide6.QtWidgets`.
*   **Hypothesis**: Adding `QFormLayout` to the list of imports from `PySide6.QtWidgets` will resolve the issue.

**3. Thorough Analysis of Potential Solutions:**

*   **Option 1: Add `QFormLayout` to `PySide6.QtWidgets` imports**:
    *   This is the direct and correct fix.
    *   The existing import line for `PySide6.QtWidgets` in `bank_reconciliation_widget.py` (from response_27) is:
        ```python
        from PySide6.QtWidgets import (
            QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, QTableView, QPushButton,
            QToolBar, QHeaderView, QAbstractItemView, QMessageBox, QLabel,
            QDateEdit, QComboBox, QDoubleSpinBox, QSplitter, QGroupBox, QCheckBox,
            QScrollArea, QFrame # QFormLayout is missing
        )
        ```
    *   I need to add `QFormLayout` to this list.

*   **Option 2: Replace `QFormLayout` with another layout manager**:
    *   The error message suggests `QVBoxLayout`. While possible, `QFormLayout` is specifically designed for label-field pairs and is appropriate for the "Reconciliation Summary" section where labels like "Book Balance (GL):" are paired with display `QLabel`s. Changing to `QVBoxLayout` would require manual pairing of labels and fields using nested `QHBoxLayout`s, which is more verbose and less idiomatic for this purpose.
    *   **Decision**: Sticking with `QFormLayout` and fixing the import is the better approach.

**4. Precise Implementation - Plan for `app/ui/banking/bank_reconciliation_widget.py`:**

*   **Execution Plan**:
    1.  **[ ] Locate the `PySide6.QtWidgets` import statement** at the top of `app/ui/banking/bank_reconciliation_widget.py`.
    2.  **[ ] Add `QFormLayout`** to the list of imported classes from `PySide6.QtWidgets`.
    3.  **[ ] Validate the rest of the file**: Ensure no other code is accidentally modified.
    4.  **[ ] Generate the complete updated file**.

**5. Rigorous Validation:**

*   **Line-by-line diff (conceptual)**: Compare the newly generated file with the version from response_27. The only change should be the addition of `QFormLayout` to the `PySide6.QtWidgets` import.
*   **Syntax check (mental)**: Confirm the import statement is correct.
*   **Logic check (mental)**: Confirm the change only affects imports and doesn't alter program logic.
*   **Contextual Check**: This is another missed import. My process for generating new UI files needs to be more diligent in scanning for all Qt classes used and ensuring they are imported.

**Pre-computation/Pre-analysis (Self-Correction/Double Checking):**
*   The traceback clearly points to `QFormLayout` being undefined.
*   My generated code for `bank_reconciliation_widget.py` in response_27 does indeed use `QFormLayout` here:
    ```python
    summary_group = QGroupBox("Reconciliation Summary")
    summary_layout = QFormLayout(summary_group) # This is the line
    summary_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
    
    self.book_balance_gl_label = QLabel("0.00"); summary_layout.addRow("Book Balance (GL):", self.book_balance_gl_label)
    ```
*   The import list for `PySide6.QtWidgets` in that file did not include `QFormLayout`. This was my oversight.

The fix is straightforward: add `QFormLayout` to the import.
</think>

You are absolutely right to point out this error. My apologies again for the oversight. This `NameError` for `QFormLayout` is another instance where a necessary import was missed during the generation of the new `BankReconciliationWidget`. I am committed to improving my process to catch these more consistently.

**Error Analysis:**

*   **Error Type**: `NameError`
*   **Message**: `name 'QFormLayout' is not defined. Did you mean: 'QVBoxLayout'?`
*   **File**: `app/ui/banking/bank_reconciliation_widget.py`
*   **Line**: 78 (in the provided traceback, actual line number in the file might vary but the context is the instantiation of `QFormLayout`).
    ```python
    summary_layout = QFormLayout(summary_group)
    ```
*   **Root Cause**: The class `QFormLayout` from `PySide6.QtWidgets` was used without being imported.

**Plan to Fix:**

1.  **Identify the `PySide6.QtWidgets` import statement** in `app/ui/banking/bank_reconciliation_widget.py`.
2.  **Add `QFormLayout`** to the list of classes imported from `PySide6.QtWidgets`.
3.  No other changes to the file's logic are required for this specific fix.
4.  Generate the complete, corrected file and perform a conceptual line-by-line diff against the version from response_27 to ensure only the import was modified as intended.

I will now provide the complete updated file for `app/ui/banking/bank_reconciliation_widget.py`.

---
**Complete Updated File: `app/ui/banking/bank_reconciliation_widget.py`**
---

```python
# File: app/ui/banking/bank_reconciliation_widget.py
import json
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Tuple, cast
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, QTableView, QPushButton,
    QToolBar, QHeaderView, QAbstractItemView, QMessageBox, QLabel,
    QDateEdit, QComboBox, QDoubleSpinBox, QSplitter, QGroupBox, QCheckBox,
    QScrollArea, QFrame, QFormLayout # Added QFormLayout
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QDate, QSize
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem, QFont, QColor

from datetime import date as python_date 
from decimal import Decimal, ROUND_HALF_UP

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.banking.bank_transaction_table_model import BankTransactionTableModel 
from app.utils.pydantic_models import BankAccountSummaryData, BankTransactionSummaryData
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
        self._statement_lines: List[BankTransactionSummaryData] = []
        self._system_transactions: List[BankTransactionSummaryData] = []

        self._statement_ending_balance = Decimal(0)
        self._book_balance_gl = Decimal(0) 
        self._total_cleared_statement_items = Decimal(0)
        self._total_cleared_system_items = Decimal(0)   
        self._deposits_in_transit_total = Decimal(0) 
        self._outstanding_checks_total = Decimal(0)  
        self._bank_charges_on_statement_not_in_book = Decimal(0)
        self._interest_earned_on_statement_not_in_book = Decimal(0)
        self._difference = Decimal(0)

        self.icon_path_prefix = "resources/icons/"
        try: import app.resources_rc; self.icon_path_prefix = ":/icons/"
        except ImportError: pass

        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_bank_accounts_for_combo()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10,10,10,10)

        header_controls_group = QGroupBox("Reconciliation Setup")
        header_layout = QGridLayout(header_controls_group)
        header_layout.addWidget(QLabel("Bank Account*:"), 0, 0)
        self.bank_account_combo = QComboBox(); self.bank_account_combo.setMinimumWidth(250)
        header_layout.addWidget(self.bank_account_combo, 0, 1)
        header_layout.addWidget(QLabel("Statement End Date*:"), 0, 2)
        self.statement_date_edit = QDateEdit(QDate.currentDate())
        self.statement_date_edit.setCalendarPopup(True); self.statement_date_edit.setDisplayFormat("dd/MM/yyyy")
        header_layout.addWidget(self.statement_date_edit, 0, 3)
        header_layout.addWidget(QLabel("Statement End Balance*:"), 1, 0)
        self.statement_balance_spin = QDoubleSpinBox()
        self.statement_balance_spin.setDecimals(2); self.statement_balance_spin.setRange(-999999999.99, 999999999.99)
        self.statement_balance_spin.setGroupSeparatorShown(True)
        header_layout.addWidget(self.statement_balance_spin, 1, 1)
        self.load_transactions_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Load / Refresh Transactions")
        header_layout.addWidget(self.load_transactions_button, 1, 3)
        header_layout.setColumnStretch(2,1) 
        self.main_layout.addWidget(header_controls_group)

        summary_group = QGroupBox("Reconciliation Summary")
        summary_layout = QFormLayout(summary_group)
        summary_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.book_balance_gl_label = QLabel("0.00"); summary_layout.addRow("Book Balance (GL):", self.book_balance_gl_label)
        self.statement_ending_balance_label = QLabel("0.00"); summary_layout.addRow("Statement Ending Balance:", self.statement_ending_balance_label)
        self.adjusted_book_balance_label = QLabel("0.00"); summary_layout.addRow("Adjusted Book Balance (Calculated):", self.adjusted_book_balance_label)
        self.difference_label = QLabel("0.00"); font = self.difference_label.font(); font.setBold(True); self.difference_label.setFont(font)
        summary_layout.addRow("Difference:", self.difference_label)
        self.main_layout.addWidget(summary_group)

        self.tables_splitter = QSplitter(Qt.Orientation.Horizontal)
        statement_items_group = QGroupBox("Bank Statement Items (Unreconciled)")
        statement_layout = QVBoxLayout(statement_items_group)
        self.statement_lines_table = QTableView()
        self.statement_lines_model = BankTransactionTableModel() 
        self._configure_recon_table(self.statement_lines_table, self.statement_lines_model)
        statement_layout.addWidget(self.statement_lines_table)
        self.tables_splitter.addWidget(statement_items_group)
        system_txns_group = QGroupBox("System Bank Transactions (Unreconciled)")
        system_layout = QVBoxLayout(system_txns_group)
        self.system_txns_table = QTableView()
        self.system_txns_model = BankTransactionTableModel() 
        self._configure_recon_table(self.system_txns_table, self.system_txns_model)
        system_layout.addWidget(self.system_txns_table)
        self.tables_splitter.addWidget(system_txns_group)
        self.tables_splitter.setSizes([self.width() // 2, self.width() // 2]) 
        self.main_layout.addWidget(self.tables_splitter, 1)

        action_layout = QHBoxLayout()
        self.match_selected_button = QPushButton("Match Selected"); self.match_selected_button.setEnabled(False) 
        self.create_je_button = QPushButton("Create Journal Entry"); self.create_je_button.setEnabled(False) 
        self.save_reconciliation_button = QPushButton("Save Reconciliation"); self.save_reconciliation_button.setEnabled(False) 
        action_layout.addStretch(); action_layout.addWidget(self.match_selected_button); action_layout.addWidget(self.create_je_button); action_layout.addStretch(); action_layout.addWidget(self.save_reconciliation_button)
        self.main_layout.addLayout(action_layout)
        
        self.setLayout(self.main_layout)
        self._connect_signals()

    def _configure_recon_table(self, table_view: QTableView, table_model: BankTransactionTableModel):
        table_view.setModel(table_model); table_view.setAlternatingRowColors(True)
        table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) 
        table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_view.horizontalHeader().setStretchLastSection(False); table_view.setSortingEnabled(True)
        header = table_view.horizontalHeader(); visible_columns = ["Txn Date", "Description", "Amount"]
        for i in range(table_model.columnCount()):
            header_text = table_model.headerData(i, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            if header_text not in visible_columns and header_text != "ID": table_view.setColumnHidden(i, True)
            else: header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        if "Description" in table_model._headers:
            desc_col_idx = table_model._headers.index("Description")
            if not table_view.isColumnHidden(desc_col_idx): header.setSectionResizeMode(desc_col_idx, QHeaderView.ResizeMode.Stretch)

    def _connect_signals(self):
        self.bank_account_combo.currentIndexChanged.connect(self._on_bank_account_changed)
        self.statement_balance_spin.valueChanged.connect(self._on_statement_balance_changed)
        self.load_transactions_button.clicked.connect(self._on_load_transactions_clicked)

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
        self._current_bank_account_id = self.bank_account_combo.currentData()
        if not self._current_bank_account_id or self._current_bank_account_id == 0: self._current_bank_account_id = None
        self.statement_lines_model.update_data([]); self.system_txns_model.update_data([])
        self._calculate_and_display_balances()

    @Slot(float)
    def _on_statement_balance_changed(self, value: float):
        self._statement_ending_balance = Decimal(str(value))
        self._calculate_and_display_balances()

    @Slot()
    def _on_load_transactions_clicked(self):
        if not self._current_bank_account_id: QMessageBox.warning(self, "Selection Required", "Please select a bank account."); return
        statement_date = self.statement_date_edit.date().toPython()
        self._statement_ending_balance = Decimal(str(self.statement_balance_spin.value()))
        schedule_task_from_qt(self._fetch_and_populate_transactions(self._current_bank_account_id, statement_date))

    async def _fetch_and_populate_transactions(self, bank_account_id: int, statement_date: python_date):
        if not self.app_core.bank_transaction_manager or not self.app_core.account_service or not self.app_core.journal_service or not self.app_core.bank_account_service : return
        selected_bank_account_orm = await self.app_core.bank_account_service.get_by_id(bank_account_id)
        if not selected_bank_account_orm or not selected_bank_account_orm.gl_account_id: QMessageBox.critical(self, "Error", "Selected bank account or its GL link is invalid."); return
        self._book_balance_gl = await self.app_core.journal_service.get_account_balance(selected_bank_account_orm.gl_account_id, statement_date)
        result = await self.app_core.bank_transaction_manager.get_unreconciled_transactions_for_matching(bank_account_id, statement_date)
        if result.is_success and result.value:
            statement_lines_dto, system_txns_dto = result.value
            self._statement_lines = statement_lines_dto; self._system_transactions = system_txns_dto
            stmt_lines_json = json.dumps([s.model_dump(mode='json') for s in self._statement_lines], default=json_converter)
            sys_txns_json = json.dumps([s.model_dump(mode='json') for s in self._system_transactions], default=json_converter)
            QMetaObject.invokeMethod(self, "_update_transaction_tables_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, stmt_lines_json), Q_ARG(str, sys_txns_json))
        else:
            QMessageBox.warning(self, "Load Error", f"Failed to load transactions: {', '.join(result.errors)}")
            self.statement_lines_model.update_data([]); self.system_txns_model.update_data([])
        self._calculate_and_display_balances()

    @Slot(str, str)
    def _update_transaction_tables_slot(self, stmt_lines_json: str, sys_txns_json: str):
        try:
            stmt_list_dict = json.loads(stmt_lines_json, object_hook=json_date_hook)
            self._statement_lines = [BankTransactionSummaryData.model_validate(d) for d in stmt_list_dict]
            self.statement_lines_model.update_data(self._statement_lines)
            sys_list_dict = json.loads(sys_txns_json, object_hook=json_date_hook)
            self._system_transactions = [BankTransactionSummaryData.model_validate(d) for d in sys_list_dict]
            self.system_txns_model.update_data(self._system_transactions)
        except Exception as e: QMessageBox.critical(self, "Data Error", f"Failed to parse transaction data: {str(e)}")

    def _calculate_and_display_balances(self):
        self.book_balance_gl_label.setText(f"{self._book_balance_gl:,.2f}")
        self.statement_ending_balance_label.setText(f"{self._statement_ending_balance:,.2f}")
        adjusted_book_balance = self._book_balance_gl 
        self._difference = self._statement_ending_balance - adjusted_book_balance 
        self.adjusted_book_balance_label.setText(f"{adjusted_book_balance:,.2f}")
        self.difference_label.setText(f"{self._difference:,.2f}")
        if abs(self._difference) < Decimal("0.01"): self.difference_label.setStyleSheet("font-weight: bold; color: green;")
        else: self.difference_label.setStyleSheet("font-weight: bold; color: red;")
        self.save_reconciliation_button.setEnabled(abs(self._difference) < Decimal("0.01"))

```

**Validation of `app/ui/banking/bank_reconciliation_widget.py`:**

*   **Line-by-Line Diff (Conceptual) vs. response_27 Version**:
    *   The import `from datetime import date as python_date` has been correctly added.
    *   The import from `PySide6.QtWidgets` has been updated to include `QFormLayout`:
        ```python
        from PySide6.QtWidgets import (
            # ... existing imports ...
            QScrollArea, QFrame, QFormLayout # Added QFormLayout
        )
        ```
*   **Correctness**:
    *   The `NameError: name 'python_date' is not defined` is resolved by the `datetime` import.
    *   The `NameError: name 'QFormLayout' is not defined` is resolved by adding it to the `PySide6.QtWidgets` import.
*   **Preservation**: All other functionalities of the `BankReconciliationWidget` (UI layout, other signal/slot connections, existing methods) as generated in response_27 are preserved.
*   **Conclusion**: The file is now correctly updated with the necessary imports and should resolve both `NameError` exceptions.

The application should now launch successfully, and the basic structure of the Bank Reconciliation tab will be visible.
