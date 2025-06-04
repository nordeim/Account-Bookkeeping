Okay, I have thoroughly reviewed the three provided "recent_code_change_response" files (first, second, third).

*   **`recent_code_change_response-first.md`**: This details my thought process and implementation for **Phase 1: Backend for Reconciliation History Viewing**. It involved:
    *   Adding `BankReconciliationSummaryData` DTO.
    *   Updating `IBankReconciliationRepository` interface.
    *   Implementing `get_reconciliations_for_account` (with 'Finalized' filter) and `get_transactions_for_reconciliation` in `BankReconciliationService`.
    The validation section at the end confirmed these changes were correctly implemented.

*   **`recent_code_change_response-second.md`**: This details my thought process and the presentation of the **Phase 2: UI Enhancements for Reconciliation History** which was the full `BankReconciliationWidget` code.
    *   It confirms that the `BankReconciliationWidget` (largely from response_48) was already well-structured to consume the history viewing services.
    *   The validation section at the end confirmed the UI wiring for history display was complete and correct based on the provided file (`app/ui/banking/bank_reconciliation_widget.py` from response_48 being the complete one).

*   **`recent_code_change_response-third.md`**: This details my thought process and implementation for **Phase 1 (Backend) of Persisting "Matched" State within a Reconciliation Session (Draft Reconciliations)**. This involved:
    *   Updating `IBankReconciliationRepository` with `get_or_create_draft_reconciliation`, `mark_transactions_as_provisionally_reconciled`, `finalize_reconciliation`, and `unreconcile_transactions`.
    *   Implementing these methods in `BankReconciliationService`.
    *   The validation at the end confirmed these service-level changes were correct.

**Current State after reviewing these responses:**

1.  The backend service layer (`BankReconciliationService`) is now equipped to:
    *   Create or retrieve "Draft" `BankReconciliation` records.
    *   Mark transactions as provisionally reconciled against a draft reconciliation.
    *   Finalize a draft reconciliation (changing its status to "Finalized" and updating bank account last reconciled details).
    *   Fetch finalized reconciliation history.
    *   Fetch transactions associated with a specific (historical) reconciliation.
2.  The `BankReconciliationWidget` has the UI elements for history viewing and the logic to populate them.
3.  The crucial **missing piece** is the UI logic in `BankReconciliationWidget` to utilize the new service methods for managing *draft reconciliations* and *persisting provisional matches*.

**Next Step: Enhance `BankReconciliationWidget` to support Draft Reconciliations and Persistent Provisional Matching (UI Layer Changes for response-third's backend work).**

This directly addresses the roadmap item: **"Refine Bank Reconciliation"** -> sub-item **(d) Persisting "matched" state within a reconciliation session before final save.**

**1. Deeply Understand Requirements:**
*   When a bank account and statement date are selected and "Load / Refresh Transactions" is clicked:
    *   The widget must call `BankReconciliationService.get_or_create_draft_reconciliation`.
    *   The ID of this draft reconciliation (`self._current_draft_reconciliation_id`) must be stored.
    *   The statement ending balance from the UI should be used when creating/retrieving the draft.
*   When the user clicks "Match Selected" in `BankReconciliationWidget`:
    *   The current matching logic (sum of statement items vs. sum of system items) needs to be re-verified. Based on previous analysis, it should check if `abs(sum_stmt_items_amounts - sum_sys_items_amounts) < tolerance`.
    *   If a valid match is found, the widget must call `BankReconciliationService.mark_transactions_as_provisionally_reconciled` with `self._current_draft_reconciliation_id` and the IDs of the selected transactions.
    *   After a successful provisional match, the unreconciled transaction lists in the UI should be reloaded (they will naturally exclude the now-reconciled items).
*   When the user clicks "Save Reconciliation":
    *   The widget must call `BankReconciliationService.finalize_reconciliation` with `self._current_draft_reconciliation_id` and the final reconciliation figures.
*   The "Add Journal Entry" flow for unmatched statement items remains largely the same, but after the JE and its corresponding system `BankTransaction` are created, that new system `BankTransaction` should then be immediately available for provisional matching against the original statement item within the current draft session.

**2. Systematic Diagnosis & Design Considerations for `BankReconciliationWidget`:**

*   **State Management**:
    *   `self._current_draft_reconciliation_id: Optional[int]` needs to be consistently managed.
*   **Loading Transactions (`_fetch_and_populate_transactions`)**:
    *   This method will now first call `get_or_create_draft_reconciliation`.
    *   The logic for fetching *unreconciled* transactions (`BankTransactionManager.get_unreconciled_transactions_for_matching`) should remain focused on fetching `is_reconciled = False` items. Items provisionally matched to the *current draft* will have `is_reconciled = True` and `reconciled_bank_reconciliation_id = self._current_draft_reconciliation_id`, so they will correctly not appear in the "unreconciled" lists.
*   **Matching Logic (`_on_match_selected_clicked`)**:
    *   **Crucial Correction**: The current logic `abs(sum_stmt + sum_sys) < Decimal("0.01")` is likely incorrect for matching a statement deposit to a system deposit (or withdrawal to withdrawal). It implies one is positive and one is negative. For like-for-like matching (e.g., a $100 deposit on statement matches a $100 deposit in system), the check should be `abs(sum_stmt_amounts - sum_sys_amounts) < Decimal("0.01")`. I will proceed with this corrected logic.
    *   After local validation, this method will call a new async method `_perform_provisional_match`.
*   **Saving Logic (`_perform_save_reconciliation`)**:
    *   This method already exists. It will now take `self._current_draft_reconciliation_id` and call `finalize_reconciliation` instead of building a new ORM object from scratch and calling the old `save_reconciliation_details`.

**3. Detailed Execution Plan:**

1.  **Modify `BankReconciliationWidget` (`app/ui/banking/bank_reconciliation_widget.py`)**:
    *   **`_on_load_transactions_clicked()` / `_fetch_and_populate_transactions()`**:
        *   Before fetching unreconciled transactions, call `self.app_core.bank_reconciliation_service.get_or_create_draft_reconciliation(...)`.
            *   Pass `bank_account_id`, `statement_date`, `statement_ending_balance` (from UI), and `user_id`.
            *   Store the returned `reconciliation.id` in `self._current_draft_reconciliation_id`.
            *   Handle potential errors from this service call.
        *   The subsequent call to `self.app_core.bank_transaction_manager.get_unreconciled_transactions_for_matching()` remains to fetch items where `is_reconciled = False`.
    *   **`_on_match_selected_clicked()`**:
        *   **Correct the sum comparison**: Change `if abs(sum_stmt + sum_sys) < Decimal("0.01"):` to `if abs(sum_stmt_amounts - sum_sys_amounts) < Decimal("0.01"):`.
        *   If amounts match, instead of just `uncheck_items_by_id`, collect the IDs of all selected statement items and system items.
        *   Call `schedule_task_from_qt(self._perform_provisional_match(all_selected_ids))`.
    *   **New async method `_perform_provisional_match(self, transaction_ids: List[int])`**:
        *   Check if `self._current_draft_reconciliation_id` is set. If not, show error.
        *   Call `self.app_core.bank_reconciliation_service.mark_transactions_as_provisionally_reconciled(draft_reconciliation_id=self._current_draft_reconciliation_id, transaction_ids=transaction_ids, statement_date=self.statement_date_edit.date().toPython(), user_id=self.app_core.current_user.id)`.
        *   On success: Log, optionally show a transient message, and trigger `self._on_load_transactions_clicked()` to refresh the unreconciled lists.
        *   On failure: Show error message.
    *   **Modify `_on_save_reconciliation_clicked()` / `_perform_save_reconciliation()`**:
        *   Instead of creating a new `BankReconciliation` ORM object, this method will now use `self._current_draft_reconciliation_id`.
        *   It will call `self.app_core.bank_reconciliation_service.finalize_reconciliation()` passing the `draft_reconciliation_id`, and the final calculated figures (`statement_ending_balance`, `calculated_book_balance`, `reconciled_difference`), and `user_id`.
        *   The service method will handle updating the draft reconciliation's status to "Finalized" and updating the bank account.
        *   Remove the manual creation of `new_reconciliation_orm` and the call to the old `save_reconciliation_details`.
    *   **Initialization**: `self._current_draft_reconciliation_id` should be initialized to `None`.
    *   **`_on_bank_account_changed()`**: When the bank account or statement date changes significantly, any existing `_current_draft_reconciliation_id` should probably be cleared, forcing a new `get_or_create_draft_reconciliation` call when "Load Transactions" is next clicked.
    *   **Ensure error handling** for all new service calls.
    *   **Disable "Match Selected" button** if `_current_draft_reconciliation_id` is not set (i.e., initial load failed).

This set of changes will make the matching process persistent within a draft session.

I will now generate the updated `app/ui/banking/bank_reconciliation_widget.py` file incorporating these changes. All other files from the previous responses remain valid for this step.

```python
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
        
        self._all_loaded_statement_lines: List[BankTransactionSummaryData] = []
        self._all_loaded_system_transactions: List[BankTransactionSummaryData] = []

        self._statement_ending_balance = Decimal(0)
        self._book_balance_gl = Decimal(0) 
        self._interest_earned_on_statement_not_in_book = Decimal(0)
        self._bank_charges_on_statement_not_in_book = Decimal(0)
        self._outstanding_system_deposits = Decimal(0) 
        self._outstanding_system_withdrawals = Decimal(0) 
        self._difference = Decimal(0)

        self._current_draft_reconciliation_id: Optional[int] = None 
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
        if "ID" in self.history_table_model._headers:
            id_col_idx_hist = self.history_table_model._headers.index("ID")
            self.history_table.setColumnHidden(id_col_idx_hist, True)
        for i in range(self.history_table_model.columnCount()): 
            if not self.history_table.isColumnHidden(i):
                self.history_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        if "Statement Date" in self.history_table_model._headers and not self.history_table.isColumnHidden(self.history_table_model._headers.index("Statement Date")):
            self.history_table.horizontalHeader().setSectionResizeMode(self.history_table_model._headers.index("Statement Date"), QHeaderView.ResizeMode.Stretch)
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
        self.overall_splitter.setSizes([self.height() * 3 // 5, self.height() * 2 // 5]) 
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
        self._current_draft_reconciliation_id = None # Clear draft ID when account changes

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
        self.match_selected_button.setEnabled(False) # Disable until draft is loaded


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
                self._statement_ending_balance, # Pass current statement balance to get_or_create_draft
                self.app_core.current_user.id
            )
        )
        self._load_reconciliation_history(1) # Refresh history when current items are (re)loaded

    async def _fetch_and_populate_transactions(self, bank_account_id: int, statement_date: python_date,
                                               statement_ending_balance: Decimal, user_id: int):
        self.load_transactions_button.setEnabled(True); self.load_transactions_button.setText("Load / Refresh Transactions")
        self.match_selected_button.setEnabled(False) # Disable until draft is loaded
        if not self.app_core.bank_reconciliation_service or \
           not self.app_core.bank_transaction_manager or \
           not self.app_core.account_service or \
           not self.app_core.journal_service or \
           not self.app_core.bank_account_service:
            self.app_core.logger.error("One or more required services are not available for reconciliation.")
            return

        try:
            # Get or create draft reconciliation
            async with self.app_core.db_manager.session() as session: # Use a session for combined ops
                draft_recon_orm = await self.app_core.bank_reconciliation_service.get_or_create_draft_reconciliation(
                    bank_account_id=bank_account_id,
                    statement_date=statement_date,
                    statement_ending_balance=statement_ending_balance,
                    user_id=user_id,
                    session=session # Pass the session
                )
                if not draft_recon_orm or not draft_recon_orm.id:
                    QMessageBox.critical(self, "Error", "Could not get or create a draft reconciliation record.")
                    return
                self._current_draft_reconciliation_id = draft_recon_orm.id
                # Update UI with potentially new/updated statement balance from draft
                QMetaObject.invokeMethod(self.statement_balance_spin, "setValue", Qt.ConnectionType.QueuedConnection, Q_ARG(float, float(draft_recon_orm.statement_ending_balance)))
                
                # Fetch GL account details
                selected_bank_account_orm = await self.app_core.bank_account_service.get_by_id(bank_account_id) # No session needed if service manages its own
                if not selected_bank_account_orm or not selected_bank_account_orm.gl_account_id:
                    QMessageBox.critical(self, "Error", "Selected bank account or its GL link is invalid."); return
                self._current_bank_account_gl_id = selected_bank_account_orm.gl_account_id
                self._current_bank_account_currency = selected_bank_account_orm.currency_code
                
                # Fetch Book Balance
                self._book_balance_gl = await self.app_core.journal_service.get_account_balance(selected_bank_account_orm.gl_account_id, statement_date)
                
                # Fetch Unreconciled Transactions (those not reconciled AT ALL)
                result = await self.app_core.bank_transaction_manager.get_unreconciled_transactions_for_matching(bank_account_id, statement_date)
                if result.is_success and result.value:
                    self._all_loaded_statement_lines, self._all_loaded_system_transactions = result.value
                    stmt_lines_json = json.dumps([s.model_dump(mode='json') for s in self._all_loaded_statement_lines], default=json_converter)
                    sys_txns_json = json.dumps([s.model_dump(mode='json') for s in self._all_loaded_system_transactions], default=json_converter)
                    QMetaObject.invokeMethod(self, "_update_transaction_tables_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, stmt_lines_json), Q_ARG(str, sys_txns_json))
                else:
                    QMessageBox.warning(self, "Load Error", f"Failed to load unreconciled transactions: {', '.join(result.errors if result.errors else ['Unknown error'])}")
                    self.statement_lines_model.update_data([]); self.system_txns_model.update_data([])
                
            self._reset_summary_figures(); self._calculate_and_display_balances()
            if self._current_draft_reconciliation_id: self.match_selected_button.setEnabled(True)

        except Exception as e:
            self.app_core.logger.error(f"Error during _fetch_and_populate_transactions: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred while loading reconciliation data: {e}")
            self._current_draft_reconciliation_id = None # Clear draft ID on error
            self.match_selected_button.setEnabled(False)


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
            self.save_reconciliation_button.setEnabled(self._current_draft_reconciliation_id is not None) # Enable save only if draft exists
        else: 
            self.difference_label.setStyleSheet("font-weight: bold; color: red;"); 
            self.save_reconciliation_button.setEnabled(False)
        self.create_je_button.setEnabled(self._interest_earned_on_statement_not_in_book > 0 or self._bank_charges_on_statement_not_in_book > 0 or len(self.statement_lines_model.get_checked_item_data()) > 0)

    def _update_match_button_state(self):
        stmt_checked_count = len(self.statement_lines_model.get_checked_item_data())
        sys_checked_count = len(self.system_txns_model.get_checked_item_data())
        self.match_selected_button.setEnabled(stmt_checked_count > 0 and sys_checked_count > 0 and self._current_draft_reconciliation_id is not None)
        self.create_je_button.setEnabled(stmt_checked_count > 0 or self._interest_earned_on_statement_not_in_book > 0 or self._bank_charges_on_statement_not_in_book > 0)

    @Slot()
    def _on_match_selected_clicked(self):
        if not self._current_draft_reconciliation_id:
            QMessageBox.warning(self, "Error", "No active reconciliation draft. Please load transactions first.")
            return

        selected_statement_items = self.statement_lines_model.get_checked_item_data()
        selected_system_items = self.system_txns_model.get_checked_item_data()
        if not selected_statement_items or not selected_system_items:
            QMessageBox.information(self, "Selection Needed", "Please select items from both tables to match."); return
        
        sum_stmt_amounts = sum(item.amount for item in selected_statement_items)
        sum_sys_amounts = sum(item.amount for item in selected_system_items)

        if abs(sum_stmt_amounts - sum_sys_amounts) > Decimal("0.01"): # Corrected logic
            QMessageBox.warning(self, "Match Error",  
                                f"Selected statement items total ({sum_stmt_amounts:,.2f}) and selected system items total ({sum_sys_amounts:,.2f}) do not match. "
                                "Please ensure selections represent the same net financial event.")
            return
        
        all_selected_ids = [item.id for item in selected_statement_items] + [item.id for item in selected_system_items]
        
        self.match_selected_button.setEnabled(False) # Disable while processing
        schedule_task_from_qt(self._perform_provisional_match(all_selected_ids))

    async def _perform_provisional_match(self, transaction_ids: List[int]):
        if self._current_draft_reconciliation_id is None: return # Should not happen if button was enabled
        if not self.app_core.current_user: return

        try:
            success = await self.app_core.bank_reconciliation_service.mark_transactions_as_provisionally_reconciled(
                draft_reconciliation_id=self._current_draft_reconciliation_id,
                transaction_ids=transaction_ids,
                statement_date=self.statement_date_edit.date().toPython(),
                user_id=self.app_core.current_user.id
            )
            if success:
                QMessageBox.information(self, "Items Matched", f"{len(transaction_ids)} items marked as provisionally reconciled for this session.")
                # Trigger reload of unreconciled items
                self._on_load_transactions_clicked() 
            else:
                QMessageBox.warning(self, "Match Error", "Failed to mark items as reconciled in the database.")
        except Exception as e:
            self.app_core.logger.error(f"Error during provisional match: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred while matching: {e}")
        finally:
            self._update_match_button_state() # Re-evaluate button state


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
        self._on_load_transactions_clicked() # This will refresh both statement and system transactions

    @Slot()
    def _on_save_reconciliation_clicked(self):
        if self._current_draft_reconciliation_id is None:
            QMessageBox.warning(self, "Error", "No active reconciliation draft. Please load transactions first.")
            return
        if abs(self._difference) >= Decimal("0.01"):
            QMessageBox.warning(self, "Cannot Save", "Reconciliation is not balanced.")
            return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        
        self.save_reconciliation_button.setEnabled(False); self.save_reconciliation_button.setText("Saving...")
        schedule_task_from_qt(self._perform_finalize_reconciliation())

    async def _perform_finalize_reconciliation(self):
        if not self.app_core.bank_reconciliation_service or self._current_draft_reconciliation_id is None:
            QMessageBox.critical(self, "Error", "Reconciliation Service or Draft ID not set.")
            self.save_reconciliation_button.setEnabled(abs(self._difference) < Decimal("0.01")); self.save_reconciliation_button.setText("Save Reconciliation"); return

        statement_end_bal_dec = Decimal(str(self.statement_balance_spin.value()))
        final_reconciled_book_balance_dec = self._book_balance_gl + self._interest_earned_on_statement_not_in_book - self._bank_charges_on_statement_not_in_book
        
        try:
            async with self.app_core.db_manager.session() as session: # Manage session here for finalize
                result = await self.app_core.bank_reconciliation_service.finalize_reconciliation(
                    draft_reconciliation_id=self._current_draft_reconciliation_id,
                    statement_ending_balance=statement_end_bal_dec,
                    calculated_book_balance=final_reconciled_book_balance_dec,
                    reconciled_difference=self._difference,
                    user_id=self.app_core.current_user.id,
                    session=session # Pass the session
                )
            
            if result.is_success and result.value:
                QMessageBox.information(self, "Success", f"Bank reconciliation finalized and saved successfully (ID: {result.value.id}).")
                self.reconciliation_saved.emit(result.value.id)
                self._current_draft_reconciliation_id = None # Clear draft ID
                self._on_load_transactions_clicked() # Refresh current view (will show empty)
                self._load_reconciliation_history(1) # Refresh history
            else:
                QMessageBox.warning(self, "Save Error", f"Failed to finalize reconciliation: {', '.join(result.errors if result.errors else ['Unknown error'])}")
        except Exception as e:
            self.app_core.logger.error(f"Error performing finalize reconciliation: {e}", exc_info=True)
            QMessageBox.warning(self, "Save Error", f"Failed to finalize reconciliation: {str(e)}")
        finally:
            self.save_reconciliation_button.setEnabled(abs(self._difference) < Decimal("0.01") and self._current_draft_reconciliation_id is not None); 
            self.save_reconciliation_button.setText("Save Reconciliation")


    def _load_reconciliation_history(self, page_number: int):
        if not self._current_bank_account_id:
            self.history_table_model.update_data([])
            self._update_history_pagination_controls(0, 0)
            return
        self._current_history_page = page_number
        self.prev_history_button.setEnabled(False); self.next_history_button.setEnabled(False)
        schedule_task_from_qt(self._fetch_reconciliation_history())

    async def _fetch_reconciliation_history(self):
        if not self.app_core.bank_reconciliation_service or self._current_bank_account_id is None: 
            self._update_history_pagination_controls(0,0); return

        history_data, total_records = await self.app_core.bank_reconciliation_service.get_reconciliations_for_account(
            bank_account_id=self._current_bank_account_id,
            page=self._current_history_page,
            page_size=self._history_page_size
        )
        self._total_history_records = total_records
        
        history_json = json.dumps([h.model_dump(mode='json') for h in history_data], default=json_converter)
        QMetaObject.invokeMethod(self, "_update_history_table_slot", Qt.ConnectionType.QueuedConnection,
                                 Q_ARG(str, history_json))

    @Slot(str)
    def _update_history_table_slot(self, history_json_str: str):
        current_item_count = 0
        try:
            history_list_dict = json.loads(history_json_str, object_hook=json_date_hook)
            history_summaries = [BankReconciliationSummaryData.model_validate(d) for d in history_list_dict]
            self.history_table_model.update_data(history_summaries)
            current_item_count = len(history_summaries)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to display reconciliation history: {e}")
        self.history_details_group.setVisible(False)
        self._update_history_pagination_controls(current_item_count, self._total_history_records)


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
            self.history_details_group.setTitle(f"Details for Reconciliation ID: {reconciliation_id}")
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

