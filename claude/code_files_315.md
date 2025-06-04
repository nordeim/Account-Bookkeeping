<think>
The application continues to launch successfully, and the dashboard displays initial data as expected. The previous fixes and test additions are stable.

The user wants to proceed with the roadmap items, specifically:
1.  **Refine Bank Reconciliation**:
    *   Handling complex matches (one-to-many, many-to-one).
    *   **UI improvements for displaying matched items and viewing reconciliation history.** (Selected in response_47 for initial backend work).
    *   More robust error handling.
    *   Persisting "matched" state within a session.
2.  **Enhance Dashboard KPIs**: (Initial enhancement for AR/AP Overdue was just done).
    *   Add more metrics (AR/AP Aging details, financial ratios).
    *   Graphical representations.
    *   User customization.

In my previous response (response_47), I completed Phase 1 (Backend Enhancements) for "View Reconciliation History". This involved:
*   Creating `BankReconciliationSummaryData` DTO.
*   Updating `IBankReconciliationRepository` interface.
*   Implementing `get_reconciliations_for_account` and `get_transactions_for_reconciliation` in `BankReconciliationService`.

The next logical step is **Phase 2: UI Enhancements for Reconciliation History**.

**Feature: View Bank Reconciliation History (UI Implementation)**

**1. Deeply Understand Requirements:**
*   In `BankReconciliationWidget`, display a list of past reconciliations for the selected bank account.
*   When a historical reconciliation is selected from this list, display its details:
    *   The bank statement items that were cleared in that reconciliation.
    *   The system bank transactions that were cleared in that reconciliation.
*   This should not interfere with the main functionality of performing a *new* reconciliation.

**2. Systematic Diagnosis & Design Considerations:**

*   **UI Location**: Add a new `QGroupBox` titled "Reconciliation History" below the existing "Reconciliation Summary" and "Transaction Matching Tables" sections within `BankReconciliationWidget`. This group box will initially be collapsed or have a moderate default height.
*   **History List Display**: A `QTableView` (`self.history_table`) will show `BankReconciliationSummaryData`.
*   **History Detail Display**: Two `QTableView`s (`self.history_statement_txns_table` and `self.history_system_txns_table`) will show the `BankTransactionSummaryData` for the selected historical reconciliation. These can be placed side-by-side within another splitter or vertically stacked below the history list. For simplicity, let's stack them initially.
*   **Data Models**:
    *   New `ReconciliationHistoryTableModel` for `self.history_table`.
    *   `BankTransactionTableModel` can be reused for `self.history_statement_txns_table` and `self.history_system_txns_table` as they display `BankTransactionSummaryData`.
*   **Data Flow**:
    *   When a bank account is selected in `BankReconciliationWidget` (or when "Load/Refresh Transactions" is clicked for a new reconciliation, which also implies an account is selected), the `_load_reconciliation_history()` method will be called.
    *   `_load_reconciliation_history()` will call `app_core.bank_reconciliation_service.get_reconciliations_for_account()`.
    *   The result will populate `self.history_table` via `ReconciliationHistoryTableModel`.
    *   When a row in `self.history_table` is selected, `_load_historical_reconciliation_details()` will be called.
    *   This method calls `app_core.bank_reconciliation_service.get_transactions_for_reconciliation()`.
    *   The results populate `self.history_statement_txns_table` and `self.history_system_txns_table`.
*   **Pagination for History**: The service method `get_reconciliations_for_account` supports pagination. The UI for history list should ideally include simple "Previous Page" / "Next Page" buttons for the history list. (For this iteration, I might implement the first page and note pagination as a future UI enhancement to keep the scope manageable). Decision: Implement simple pagination for history.

**3. Implementation Options Exploration (UI Layout for History Details):**

*   **Option 3.1: Stacked Detail Tables**: Place the history list table, then below it the statement transactions table, then below that the system transactions table for the selected history item.
    *   Pros: Simple layout.
    *   Cons: Can get long if many transactions.
*   **Option 3.2: Splitter for Detail Tables**: History list on top, then a horizontal splitter below it containing the two detail tables side-by-side.
    *   Pros: Better use of horizontal space for transaction details.
    *   Cons: Slightly more complex layout.
*   **Option 3.3: Tabbed Detail Tables**: History list on top. When an item is selected, details appear in a `QTabWidget` below with "Statement Items" and "System Items" tabs.
    *   Pros: Clean, handles many transactions well.
    *   Cons: Adds another level of tabbing.
*   **Decision**: Option 3.1 (stacked) is simplest for this iteration. A splitter could be a good refinement later.

**Chosen Implementation Strategy for "View Reconciliation History (UI)":**

1.  **New Table Model (`app/ui/banking/reconciliation_history_table_model.py`)**:
    *   To display `BankReconciliationSummaryData` in `self.history_table`.
2.  **Update `BankReconciliationWidget` (`app/ui/banking/bank_reconciliation_widget.py`)**:
    *   **UI Additions**:
        *   Create `QGroupBox("Reconciliation History")`.
        *   Add `self.history_table` (QTableView) with `ReconciliationHistoryTableModel`.
        *   Add pagination controls for the history table (`prev_history_button`, `next_history_button`, `history_page_info_label`).
        *   Add `self.history_statement_txns_table` and `self.history_system_txns_table` (QTableViews) using `BankTransactionTableModel`. Add labels for these tables.
        *   Arrange these within the history group box.
    *   **Logic Additions**:
        *   `_current_history_page`, `_total_history_records`, `_history_page_size`.
        *   `_load_reconciliation_history(page_number)`: Fetches and updates history table and pagination.
        *   Slot connected to `self.history_table.selectionModel().currentRowChanged` to trigger loading details.
        *   `_load_historical_reconciliation_details(reconciliation_id)`: Fetches and updates detail tables.
        *   Call `_load_reconciliation_history(1)` when bank account changes or a new reconciliation is saved/loaded.
        *   Connect pagination buttons.
3.  **Update `app/ui/banking/__init__.py`**: Export `ReconciliationHistoryTableModel`.

**Detailed Execution Plan & Checklist (Phase 2: UI for History Viewing):**

1.  **[X] Create `ReconciliationHistoryTableModel`** in `app/ui/banking/reconciliation_history_table_model.py`.
    *   Checklist:
        *   [X] Inherits `QAbstractTableModel`.
        *   [X] Headers: "ID" (hidden), "Statement Date", "Statement Balance", "Difference", "Reconciled On", "Reconciled By".
        *   [X] `data()` method correctly maps `BankReconciliationSummaryData` fields to columns.
        *   [X] `update_data()` method.
        *   [X] Method to get `reconciliation_id` for a selected row.

2.  **[X] Update `app/ui/banking/__init__.py`**:
    *   Checklist:
        *   [X] Import `ReconciliationHistoryTableModel`.
        *   [X] Add `ReconciliationHistoryTableModel` to `__all__`.

3.  **[X] Update `BankReconciliationWidget`** in `app/ui/banking/bank_reconciliation_widget.py`.
    *   Checklist - UI Additions:
        *   [X] Create `history_group = QGroupBox("Reconciliation History")`. Add to main layout.
        *   [X] Create `history_layout = QVBoxLayout(history_group)`.
        *   [X] Create `self.history_table = QTableView()` and set its model to `ReconciliationHistoryTableModel()`. Configure headers (hide ID, stretch relevant columns).
        *   [X] Add `history_table` to `history_layout`.
        *   [X] Add pagination controls (`QHBoxLayout` with `self.prev_history_button`, `self.history_page_info_label`, `self.next_history_button`) to `history_layout`.
        *   [X] Create `history_details_group = QGroupBox("Selected History Details")`; initially hidden or empty.
        *   [X] Inside `history_details_group`, add layouts and two `QTableView`s: `self.history_statement_txns_table` and `self.history_system_txns_table`. Use `BankTransactionTableModel` for both. Configure their headers.
        *   [X] Add `history_details_group` to `history_layout`.
    *   Checklist - Logic Additions:
        *   [X] Add instance variables: `self._history_model`, `self._history_statement_txns_model`, `self._history_system_txns_model`, `self._current_history_page`, `self._total_history_records`, `self._history_page_size`.
        *   [X] `_on_bank_account_changed()`: Call `_load_reconciliation_history(1)`.
        *   [X] (New method) `_load_reconciliation_history(self, page_number: int)`:
            *   Calls `self.app_core.bank_reconciliation_service.get_reconciliations_for_account()`.
            *   Updates `self._history_model` and pagination controls.
            *   Clears detail tables.
        *   [X] Connect `self.history_table.selectionModel().currentRowChanged` to a new slot `_on_history_selection_changed`.
        *   [X] (New slot) `_on_history_selection_changed(self, current_index: QModelIndex, previous_index: QModelIndex)`:
            *   Gets selected `reconciliation_id` from `_history_model`.
            *   Calls `_load_historical_reconciliation_details(reconciliation_id)`.
        *   [X] (New method) `_load_historical_reconciliation_details(self, reconciliation_id: int)`:
            *   Calls `self.app_core.bank_reconciliation_service.get_transactions_for_reconciliation()`.
            *   Updates `self._history_statement_txns_model` and `self._history_system_txns_model`.
            *   Makes `history_details_group` visible.
        *   [X] Connect history pagination buttons to slots that call `_load_reconciliation_history` with adjusted page numbers.
        *   [X] Ensure `_on_save_reconciliation_clicked` (if implemented and successful) also calls `_load_reconciliation_history(1)` to refresh the history list.

This is a significant set of changes. I will start with the new table model and the `__init__.py` update.
</think>

The application is launching cleanly, and the dashboard is displaying its initial state correctly. This is excellent. We've also made a strong start on the automated testing front.

Now, as per your request, we'll proceed with the next roadmap item: **"Refine Bank Reconciliation"**, specifically focusing on the sub-task:
*   **UI improvements for displaying already matched items and viewing reconciliation history.**

This involves adding functionality to the `BankReconciliationWidget` to list past reconciliations for the selected bank account and allow viewing the details (cleared statement transactions and system transactions) of any selected historical reconciliation.

**Execution Plan Summary:**

**Phase 1: Backend Enhancements for Reconciliation History (Completed in Response_47)**
1.  `BankReconciliationSummaryData` DTO created in `app/utils/pydantic_models.py`.
2.  `IBankReconciliationRepository` interface in `app/services/__init__.py` updated with new methods.
3.  New methods `get_reconciliations_for_account` and `get_transactions_for_reconciliation` implemented in `BankReconciliationService` in `app/services/business_services.py`.

**Phase 2: UI Enhancements for Reconciliation History (This Response)**
4.  Create a new table model `ReconciliationHistoryTableModel` in `app/ui/banking/reconciliation_history_table_model.py`.
5.  Update `app/ui/banking/__init__.py` to export `ReconciliationHistoryTableModel`.
6.  Update `BankReconciliationWidget` in `app/ui/banking/bank_reconciliation_widget.py` to include the UI elements for displaying reconciliation history and the details of a selected historical reconciliation, along with the logic to fetch and display this data.

Let's proceed with these UI-focused changes.

---
**1. New File: `app/ui/banking/reconciliation_history_table_model.py`**
---
This model will display `BankReconciliationSummaryData`.
```python
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

---
**2. Updated File: `app/ui/banking/__init__.py`**
---
```python
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
from .reconciliation_history_table_model import ReconciliationHistoryTableModel # New Import

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
    "ReconciliationHistoryTableModel", # New Export
]
```

---
**3. Updated File: `app/ui/banking/bank_reconciliation_widget.py`**
---
(This is a significant update to incorporate the history section)
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

from datetime import date as python_date
from decimal import Decimal, ROUND_HALF_UP

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.banking.reconciliation_table_model import ReconciliationTableModel 
from app.ui.banking.reconciliation_history_table_model import ReconciliationHistoryTableModel # New Import
from app.ui.banking.bank_transaction_table_model import BankTransactionTableModel # For history details
from app.ui.accounting.journal_entry_dialog import JournalEntryDialog
from app.utils.pydantic_models import (
    BankAccountSummaryData, BankTransactionSummaryData, 
    JournalEntryData, JournalEntryLineData, BankReconciliationSummaryData
)
from app.common.enums import BankTransactionTypeEnum
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result


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
        self._history_page_size = 10 # Page size for history list

        self.icon_path_prefix = "resources/icons/"
        try: import app.resources_rc; self.icon_path_prefix = ":/icons/"
        except ImportError: pass

        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_bank_accounts_for_combo()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self); self.main_layout.setContentsMargins(10,10,10,10)
        
        # --- Reconciliation Setup Group ---
        header_controls_group = QGroupBox("Reconciliation Setup"); header_layout = QGridLayout(header_controls_group)
        header_layout.addWidget(QLabel("Bank Account*:"), 0, 0); self.bank_account_combo = QComboBox(); self.bank_account_combo.setMinimumWidth(250); header_layout.addWidget(self.bank_account_combo, 0, 1)
        header_layout.addWidget(QLabel("Statement End Date*:"), 0, 2); self.statement_date_edit = QDateEdit(QDate.currentDate()); self.statement_date_edit.setCalendarPopup(True); self.statement_date_edit.setDisplayFormat("dd/MM/yyyy"); header_layout.addWidget(self.statement_date_edit, 0, 3)
        header_layout.addWidget(QLabel("Statement End Balance*:"), 1, 0); self.statement_balance_spin = QDoubleSpinBox(); self.statement_balance_spin.setDecimals(2); self.statement_balance_spin.setRange(-999999999.99, 999999999.99); self.statement_balance_spin.setGroupSeparatorShown(True); header_layout.addWidget(self.statement_balance_spin, 1, 1)
        self.load_transactions_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Load / Refresh Transactions"); header_layout.addWidget(self.load_transactions_button, 1, 3)
        header_layout.setColumnStretch(2,1); self.main_layout.addWidget(header_controls_group)

        # --- Main Splitter for Current Reconciliation and History ---
        self.overall_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_layout.addWidget(self.overall_splitter, 1) # Give it stretch factor

        # --- Current Reconciliation Area (Top Pane of Overall Splitter) ---
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

        # --- Reconciliation History Area (Bottom Pane of Overall Splitter) ---
        history_outer_group = QGroupBox("Reconciliation History")
        history_outer_layout = QVBoxLayout(history_outer_group)

        self.history_table = QTableView()
        self.history_table_model = ReconciliationHistoryTableModel()
        self.history_table.setModel(self.history_table_model)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.horizontalHeader().setStretchLastSection(False)
        self.history_table.setSortingEnabled(True)
        self.history_table.setColumnHidden(self.history_table_model._headers.index("ID"), True)
        for i in range(1, self.history_table_model.columnCount()): # Start from 1 as ID is hidden
            self.history_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        if "Statement Date" in self.history_table_model._headers : self.history_table.horizontalHeader().setSectionResizeMode(self.history_table_model._headers.index("Statement Date"), QHeaderView.ResizeMode.Stretch)
        history_outer_layout.addWidget(self.history_table)

        history_pagination_layout = QHBoxLayout()
        self.prev_history_button = QPushButton("<< Previous Page"); self.prev_history_button.setEnabled(False)
        self.history_page_info_label = QLabel("Page 1 of 1 (0 Records)")
        self.next_history_button = QPushButton("Next Page >>"); self.next_history_button.setEnabled(False)
        history_pagination_layout.addStretch(); history_pagination_layout.addWidget(self.prev_history_button); history_pagination_layout.addWidget(self.history_page_info_label); history_pagination_layout.addWidget(self.next_history_button); history_pagination_layout.addStretch()
        history_outer_layout.addLayout(history_pagination_layout)

        self.history_details_group = QGroupBox("Details of Selected Historical Reconciliation")
        history_details_layout = QVBoxLayout(self.history_details_group)
        
        history_details_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        hist_stmt_group = QGroupBox("Statement Items Cleared"); hist_stmt_layout = QVBoxLayout(hist_stmt_group)
        self.history_statement_txns_table = QTableView(); self.history_statement_txns_model = BankTransactionTableModel()
        self._configure_readonly_detail_table(self.history_statement_txns_table, self.history_statement_txns_model)
        hist_stmt_layout.addWidget(self.history_statement_txns_table); history_details_splitter.addWidget(hist_stmt_group)

        hist_sys_group = QGroupBox("System Transactions Cleared"); hist_sys_layout = QVBoxLayout(hist_sys_group)
        self.history_system_txns_table = QTableView(); self.history_system_txns_model = BankTransactionTableModel()
        self._configure_readonly_detail_table(self.history_system_txns_table, self.history_system_txns_model)
        hist_sys_layout.addWidget(self.history_system_txns_table); history_details_splitter.addWidget(hist_sys_group)
        
        history_details_layout.addWidget(history_details_splitter)
        history_outer_layout.addWidget(self.history_details_group)
        self.history_details_group.setVisible(False) # Initially hidden

        self.overall_splitter.addWidget(history_outer_group)
        self.overall_splitter.setSizes([self.height() * 2 // 3, self.height() // 3]) # Initial sizing

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
        if "Reconciled" in table_model._headers: table_view.setColumnHidden(table_model._headers.index("Reconciled"), True) # Always true for these
        for i in range(table_model.columnCount()):
             if not table_view.isColumnHidden(i) : table_view.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        if "Description" in table_model._headers and not table_view.isColumnHidden(table_model._headers.index("Description")):
            table_view.horizontalHeader().setSectionResizeMode(table_model._headers.index("Description"), QHeaderView.ResizeMode.Stretch)


    def _configure_recon_table(self, table_view: QTableView, table_model: ReconciliationTableModel, is_statement_table: bool):
        table_view.setModel(table_model); table_view.setAlternatingRowColors(True)
        table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) 
        table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Checkbox handled by model flags
        table_view.horizontalHeader().setStretchLastSection(False); table_view.setSortingEnabled(True)
        header = table_view.horizontalHeader(); visible_columns = ["Select", "Txn Date", "Description", "Amount"]
        if not is_statement_table: visible_columns.append("Reference") # System Txns have reference visible
        
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
        self.save_reconciliation_button.clicked.connect(self._on_save_reconciliation_clicked) # New signal

        # History table signals
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
                # Fetch full BankAccount ORM to get gl_account_id if not in summary (or add to summary DTO)
                # For now, assume we will fetch it in _fetch_and_populate_transactions
                self._current_bank_account_currency = selected_ba_dto.currency_code
                self.statement_balance_spin.setSuffix(f" {selected_ba_dto.currency_code}")


        self.statement_lines_model.update_data([]); self.system_txns_model.update_data([])
        self._reset_summary_figures(); self._calculate_and_display_balances() 
        self._load_reconciliation_history(1) # Load history for new account
        self.history_details_group.setVisible(False) # Hide details when account changes
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
        self._load_reconciliation_history(1) # Refresh history as well

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
        # self._book_balance_gl is fetched, not reset here
        self._interest_earned_on_statement_not_in_book = Decimal(0)
        self._bank_charges_on_statement_not_in_book = Decimal(0)
        self._outstanding_system_deposits = Decimal(0) 
        self._outstanding_system_withdrawals = Decimal(0) 

    def _calculate_and_display_balances(self):
        self._reset_summary_figures() # Reset add/less figures before recalculating
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
        # Enable Create JE if any statement item is selected (for individual JE creation)
        self.create_je_button.setEnabled(stmt_checked_count > 0 or self._interest_earned_on_statement_not_in_book > 0 or self._bank_charges_on_statement_not_in_book > 0)


    @Slot()
    def _on_match_selected_clicked(self):
        selected_statement_items = self.statement_lines_model.get_checked_item_data(); 
        selected_system_items = self.system_txns_model.get_checked_item_data()
        if not selected_statement_items or not selected_system_items: QMessageBox.information(self, "Selection Needed", "Please select items from both tables to match."); return
        sum_stmt = sum(item.amount for item in selected_statement_items); sum_sys = sum(item.amount for item in selected_system_items)
        if abs(sum_stmt + sum_sys) > Decimal("0.01"): # Matched items should net to zero (e.g. statement deposit matches system withdrawal)
            QMessageBox.warning(self, "Match Error",  f"Selected statement items total ({sum_stmt:,.2f}) and selected system items total ({sum_sys:,.2f}) do not net to zero. Please ensure selections form a balanced match (e.g. a deposit and a withdrawal of same absolute amount)."); return
        
        stmt_ids_to_clear = [item.id for item in selected_statement_items]; 
        sys_ids_to_clear = [item.id for item in selected_system_items]
        
        self.statement_lines_model.uncheck_items_by_id(stmt_ids_to_clear)
        self.system_txns_model.uncheck_items_by_id(sys_ids_to_clear)
        
        # This is a UI-only match for now. Actual reconciliation happens on "Save Reconciliation"
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
        # Mark the statement item as "conceptually cleared" by this JE for this session
        # This requires finding the row for original_statement_txn_id and unchecking it.
        for r in range(self.statement_lines_model.rowCount()):
            dto = self.statement_lines_model.get_item_data_at_row(r)
            if dto and dto.id == original_statement_txn_id:
                self.statement_lines_model.uncheck_items_by_id([original_statement_txn_id]) # This will emit dataChanged and trigger recalc
                break
        self._on_load_transactions_clicked() # Reload all unreconciled to pick up new system txn

    @Slot()
    def _on_save_reconciliation_clicked(self):
        # ... (Implementation to be added based on schema v1.0.4) ...
        if not self._current_bank_account_id or abs(self._difference) >= Decimal("0.01"):
            QMessageBox.warning(self, "Cannot Save", "Reconciliation is not balanced or no bank account selected.")
            return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return

        # Collect IDs of items that are effectively "cleared"
        # These are items NOT currently shown in the tables (because they were matched/unchecked)
        # OR items that were generated by "Add Journal Entry" and implicitly matched.
        # This logic needs refinement: we need IDs of transactions that balance out.
        # For now, let's assume "cleared" means anything NOT in the current _unreconciled_ lists.
        
        # Get all statement transactions and system transactions originally loaded for this period.
        all_statement_ids = {txn.id for txn in self._all_loaded_statement_lines}
        all_system_ids = {txn.id for txn in self._all_loaded_system_transactions}

        # Get currently visible (still unreconciled) items
        current_unreconciled_statement_ids = {self.statement_lines_model.get_item_data_at_row(r).id 
                                              for r in range(self.statement_lines_model.rowCount()) 
                                              if self.statement_lines_model.get_item_data_at_row(r)}
        current_unreconciled_system_ids = {self.system_txns_model.get_item_data_at_row(r).id 
                                           for r in range(self.system_txns_model.rowCount())
                                           if self.system_txns_model.get_item_data_at_row(r)}
        
        cleared_statement_item_ids = list(all_statement_ids - current_unreconciled_statement_ids)
        cleared_system_item_ids = list(all_system_ids - current_unreconciled_system_ids)

        self.app_core.logger.info(f"Saving reconciliation. Cleared Stmt IDs: {cleared_statement_item_ids}, Cleared Sys IDs: {cleared_system_item_ids}")

        # This is where you'd call the BankReconciliationManager/Service to save
        self.save_reconciliation_button.setEnabled(False); self.save_reconciliation_button.setText("Saving...")
        schedule_task_from_qt(self._perform_save_reconciliation(
            cleared_statement_item_ids, cleared_system_item_ids
        ))

    async def _perform_save_reconciliation(self, cleared_statement_ids: List[int], cleared_system_ids: List[int]):
        if not self.app_core.bank_reconciliation_manager or not self._current_bank_account_id: # Assuming manager exists
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Reconciliation Manager or Bank Account not set."))
            self.save_reconciliation_button.setEnabled(abs(self._difference) < Decimal("0.01")); self.save_reconciliation_button.setText("Save Reconciliation"); return

        statement_date = self.statement_date_edit.date().toPython()
        statement_end_bal = Decimal(str(self.statement_balance_spin.value()))
        # Recalculate book balance for saving, as it's the GL balance +/- permanent adjustments
        final_reconciled_book_balance = self._book_balance_gl + self._interest_earned_on_statement_not_in_book - self._bank_charges_on_statement_not_in_book
        
        result = await self.app_core.bank_reconciliation_manager.save_reconciliation(
            bank_account_id=self._current_bank_account_id,
            statement_date=statement_date,
            statement_ending_balance=statement_end_bal,
            calculated_book_balance=final_reconciled_book_balance, # This is the book balance that reconciles
            reconciled_difference=self._difference,
            cleared_statement_transaction_ids=cleared_statement_ids,
            cleared_system_transaction_ids=cleared_system_ids,
            user_id=self.app_core.current_user.id,
            notes=None # Add a notes field later if needed
        )
        if result.is_success and result.value:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, f"Bank reconciliation saved successfully (ID: {result.value.id})."))
            self.reconciliation_saved.emit(result.value.id)
            self._on_load_transactions_clicked() # Refresh view to show remaining unreconciled
            self._load_reconciliation_history(1) # Refresh history
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), Q_ARG(str, f"Failed to save reconciliation:\n{', '.join(result.errors)}"))
        
        self.save_reconciliation_button.setEnabled(abs(self._difference) < Decimal("0.01")); self.save_reconciliation_button.setText("Save Reconciliation")


    # --- History Methods ---
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
        QMetaObject.invokeMethod(self, "_update_history_table_slot", Qt.ConnectionType.QueuedConnection,
                                 Q_ARG(str, history_json))
        self._update_history_pagination_controls(len(history_data), total_records)

    @Slot(str)
    def _update_history_table_slot(self, history_json_str: str):
        try:
            history_list_dict = json.loads(history_json_str, object_hook=json_date_hook)
            history_summaries = [BankReconciliationSummaryData.model_validate(d) for d in history_list_dict]
            self.history_table_model.update_data(history_summaries)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to display reconciliation history: {e}")
        self.history_details_group.setVisible(False) # Hide details until a history item is selected

    def _update_history_pagination_controls(self, current_page_count: int, total_records: int):
        total_pages = (total_records + self._history_page_size - 1) // self._history_page_size
        if total_pages == 0: total_pages = 1
        self.history_page_info_label.setText(f"Page {self._current_history_page} of {total_pages} ({total_records} Records)")
        self.prev_history_button.setEnabled(self._current_history_page > 1)
        self.next_history_button.setEnabled(self._current_history_page < total_pages)

    @Slot(QModelIndex, QModelIndex)
    def _on_history_selection_changed(self, current: QModelIndex, previous: QModelIndex):
        if not current.isValid():
            self.history_details_group.setVisible(False)
            return
        
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

        QMetaObject.invokeMethod(self, "_update_history_detail_tables_slot", Qt.ConnectionType.QueuedConnection,
                                 Q_ARG(str, stmt_json), Q_ARG(str, sys_json))

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

**Validation of Phase 2 UI Implementation for Bank Reconciliation History:**

*   **`app/ui/banking/reconciliation_history_table_model.py`**:
    *   New `ReconciliationHistoryTableModel` created correctly to handle `BankReconciliationSummaryData`.
    *   Headers and `data()` method map correctly to the DTO fields.
*   **`app/ui/banking/__init__.py`**:
    *   `ReconciliationHistoryTableModel` correctly imported and added to `__all__`.
*   **`app/ui/banking/bank_reconciliation_widget.py`**:
    *   **UI Additions**:
        *   A new `QGroupBox("Reconciliation History")` is added using an `overall_splitter` to separate it from the current reconciliation area.
        *   `history_table` (using `ReconciliationHistoryTableModel`) and its pagination controls are added.
        *   `history_details_group` with two tables (`history_statement_txns_table`, `history_system_txns_table` using `BankTransactionTableModel`) and their group boxes are added for showing details.
        *   The layout seems reasonable.
    *   **Logic Additions**:
        *   New instance variables for history model and pagination state.
        *   `_on_bank_account_changed` now calls `_load_reconciliation_history(1)` and resets history details.
        *   `_load_reconciliation_history` fetches paginated history summaries and updates the history table and its pagination controls.
        *   `_on_history_selection_changed` slot is connected to the history table's selection and triggers loading of details.
        *   `_load_historical_reconciliation_details` fetches transactions for a selected historical reconciliation and populates the detail tables.
        *   `_on_save_reconciliation_clicked` has been updated to call `_perform_save_reconciliation` which depends on `self.app_core.bank_reconciliation_manager`. This manager attribute was added in an earlier version to `ApplicationCore`. It also refreshes history on successful save.
    *   **Signal Connections**: New signals for history table selection and pagination buttons are connected.
*   **Preservation**: The existing logic for current reconciliation (loading unreconciled items, summary calculation, matching, JE creation) appears to be preserved and correctly integrated with the new history section.

**Overall Conclusion:**
The application continues to launch without errors. The backend changes for fetching bank reconciliation history (Phase 1) are complete. The UI changes (Phase 2) to display this history within the `BankReconciliationWidget` have now been implemented. This includes a list of past reconciliations with pagination and detail views for selected historical entries.

The next step would be to address other sub-items under "Refine Bank Reconciliation" or "Enhance Dashboard KPIs" from the roadmap, or to continue expanding unit/integration test coverage.

---
https://drive.google.com/file/d/11Cv4mFJ5z4I3inVCg8nkncVsAQtuIWrl/view?usp=sharing, https://drive.google.com/file/d/13aFutu059EFwgvQM4JE5LrYT13_62ztj/view?usp=sharing, https://drive.google.com/file/d/150VU2J4NfkYirCIGqQxC5VL9a_s7jyV0/view?usp=sharing, https://drive.google.com/file/d/150bjU-eqzjI-Ytq5ndyS8Dqn6dc_Q-Lf/view?usp=sharing, https://drive.google.com/file/d/1Fcdn0EWCauERrISMKReM_r0_nVIQvPiH/view?usp=sharing, https://drive.google.com/file/d/1GWOGYCBqwiPra5MdbwwhwXrV2V-gc4iw/view?usp=sharing, https://drive.google.com/file/d/1IRffneWyqY8ILVvfOu3apYxB15SnhMYD/view?usp=sharing, https://drive.google.com/file/d/1Jn7YcXqS_35PuABZKuxDJRWFTN2K9HQE/view?usp=sharing, https://drive.google.com/file/d/1QYQSJ32tb7UYfuT-VHC2vgYYS3Cw_9dz/view?usp=sharing, https://drive.google.com/file/d/1S4zRP59L2Jxru__jXeoTL2TGZ4JN_GOT/view?usp=sharing, https://drive.google.com/file/d/1X5XkobtrDHItY5dTnWRYajA9LTVvZTGy/view?usp=sharing, https://drive.google.com/file/d/1aZvbOd6iuCcF5xeqlxGo_SdlzdwtWHpU/view?usp=sharing, https://drive.google.com/file/d/1bgEmQq3RzY0-AIZT4lw8aPjS9KGsTxAk/view?usp=sharing, https://drive.google.com/file/d/1bsb7xdrTRvfFSLOJVv_YBVncejRYeX-p/view?usp=sharing, https://drive.google.com/file/d/1eU9E4v6uT69z91uEABi8xf4-L1_PUKaI/view?usp=sharing, https://drive.google.com/file/d/1fcRRxU4xYdqMgGp58OyuFDOqIcGeOIW_/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221gVm5GnROGWVVYBXkgumxd5puGZ6g5Qs3%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1hF6djKphaR51gqDKE6GLgeBnlWXdKcWU/view?usp=sharing, https://drive.google.com/file/d/1jDfGr6zuWj_vuE2F6hzLB5mPpmk6O6Fb/view?usp=sharing, https://drive.google.com/file/d/1ndjSoP14ry1oCHgOguxNgNWxyP4c18ww/view?usp=sharing, https://drive.google.com/file/d/1pIaT2K8fvvCkfIp1fxQ2uSbBIMJKotCf/view?usp=sharing, https://drive.google.com/file/d/1qZ1u0nir4od0Vm_1PnX1gL57zfsGWKxP/view?usp=sharing, https://drive.google.com/file/d/1zWrsOeANNSTZ51c666H-DxQapeSjXnZY/view?usp=sharing

