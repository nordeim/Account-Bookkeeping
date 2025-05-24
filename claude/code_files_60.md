<think>
The application is launching and shutting down cleanly! This is excellent. We've successfully implemented:
-   Robust `FiscalYearService` (in `app/services/accounting_services.py`).
-   Robust `FiscalPeriodManager` (in `app/accounting/fiscal_period_manager.py`).
-   The `FiscalYearDialog` (`app/ui/accounting/fiscal_year_dialog.py`).
-   The `FiscalYearCreateData` and related DTOs in `app/utils/pydantic_models.py`.
-   Significant enhancements to `app/ui/settings/settings_widget.py` to include a Fiscal Year management section, which loads and displays fiscal years, and uses the `FiscalYearDialog` to add new ones.

All these components are now in place and the application runs without startup errors.

**Current Status of "Step 1: Enhance Company Settings & Fiscal Year Setup":**

*   **Company Settings UI (`SettingsWidget`)**:
    *   Most fields from `core.company_settings` are now represented in the UI.
    *   Loading and saving of these settings (via `CompanySettingData` DTO and `CompanySettingsService`) is implemented.
*   **Fiscal Year Management UI (`SettingsWidget` + `FiscalYearDialog`)**:
    *   Ability to view a list of existing fiscal years in `SettingsWidget`.
    *   "Add New Fiscal Year..." button launches `FiscalYearDialog`.
    *   `FiscalYearDialog` allows input of year name, start/end dates, and auto-generation preference for periods.
    *   The dialog passes `FiscalYearCreateData` to `FiscalPeriodManager.create_fiscal_year_and_periods`.
    *   `FiscalPeriodManager` creates the `FiscalYear` and generates `FiscalPeriod` records atomically.
    *   The list of fiscal years in `SettingsWidget` refreshes after successful creation.

**What's next according to the plan (focusing on MVP for trial)?**

The immediate next big piece is **Step 2: Core Journal Entry Functionality**. This is the absolute heart of any bookkeeping application.

**Step 2 Detailed Plan (Recap & Refinement):**

1.  **`app/ui/accounting/journal_entry_dialog.py` (New File - High Priority):**
    *   **Goal**: Allow users to create and edit (draft) General Journal Entries.
    *   **UI Elements**:
        *   Header: `QDateEdit` (Entry Date), `QComboBox` (Journal Type - initially just "General Journal"), `QLineEdit` (Description), `QLineEdit` (Reference).
        *   Lines: `QTableWidget` for `JournalEntryLineData`. Columns:
            *   `Account`: Searchable `QComboBox` or a button to launch an account selection dialog. Needs to display account code and name. Stores account ID.
            *   `Description`: `QLineEdit` (or delegate).
            *   `Debit`: `QLineEdit` (formatted for currency, validates as Decimal).
            *   `Credit`: `QLineEdit` (formatted for currency, validates as Decimal).
            *   (MVP Optional, but good for Singapore): `Tax Code`: `QComboBox` (populated from `accounting.tax_codes`).
            *   (MVP Optional): `Tax Amount`: `QLineEdit` (read-only, auto-calculated if Tax Code selected).
            *   (MVP Optional): `Dimensions`: `QComboBox` for Dimension 1 & 2.
        *   Buttons to "Add Line", "Remove Line".
        *   Display running totals for Debits and Credits below the lines table, and an indicator if it's balanced.
        *   Main Actions: "Save Draft" `QPushButton`, "Save & Post" `QPushButton`, "Cancel" `QPushButton`.
    *   **Logic**:
        *   Populate Account, Tax Code, Dimension ComboBoxes by fetching data via `ApplicationCore`.
        *   Client-side validation (e.g., date in open period, debit/credit exclusivity per line).
        *   On "Save Draft" or "Save & Post":
            *   Collect all data into `JournalEntryData` DTO.
            *   Pydantic validation will catch balanced entry issues if defined in DTO.
            *   Call `app_core.journal_entry_manager.create_journal_entry(dto)`.
            *   If "Save & Post", then call `app_core.journal_entry_manager.post_journal_entry(created_entry.id, user_id)`.
            *   Handle `Result` objects and display messages.

2.  **`app/ui/accounting/journal_entries_widget.py` (New File - High Priority):**
    *   **Goal**: Display a list of journal entries and allow basic actions.
    *   **UI Elements**:
        *   `QTableView` to display journal entries. Columns: "Entry No", "Date", "Description", "Type", "Total Amount", "Status (Draft/Posted)".
        *   Model: Custom `QAbstractTableModel` for journal entries.
        *   Toolbar/Buttons: "New Journal Entry" (launches `JournalEntryDialog`), "Edit Draft Entry" (launches `JournalEntryDialog` with data), "View Entry" (read-only view, maybe in dialog), "Post Selected Draft(s)", "Reverse Posted Entry".
        *   Filters: `QDateEdit` for date range, `QComboBox` for status.
    *   **Logic**:
        *   Async loading of journal entries via `schedule_task_from_qt` calling manager methods.
        *   Refresh list after actions.

3.  **Backend Enhancements (`app/accounting/journal_entry_manager.py`, `app/services/journal_service.py`):**
    *   `JournalEntryManager.create_journal_entry`: Ensure it robustly handles the `JournalEntryData` DTO, creates `JournalEntry` and `JournalEntryLine` ORM objects, and saves them via `JournalService`. Properly set `created_by_user_id`, `updated_by_user_id`.
    *   `JournalEntryManager.post_journal_entry`: Ensure it checks if the entry is already posted and if the fiscal period is open.
    *   `JournalService`:
        *   Implement `get_all_with_filters(start_date, end_date, status)` for the list view.
        *   Ensure `save` correctly handles new and existing entries with lines.

4.  **`app/ui/accounting/accounting_widget.py` Modification:**
    *   Add a new tab for the `JournalEntriesWidget`.

This is a substantial piece of work. I will start by defining the `JournalEntryDialog` UI and its basic structure. Then the `JournalEntriesWidget`, followed by connecting them to the enhanced manager and service layers.
</think>

It's truly gratifying to see the application launching successfully and shutting down cleanly! This stable foundation is exactly what we need to build upon.

The next logical step, as per our plan, is to implement the **Core Journal Entry Functionality (Step 2)**. This is the heart of any bookkeeping system.

**Phase 1.2: Implementing Core Journal Entry Functionality**

This phase will involve:
1.  **Creating `app/ui/accounting/journal_entry_dialog.py`**: This dialog will be used for both creating new journal entries and editing existing draft entries.
2.  **Creating `app/ui/accounting/journal_entries_widget.py`**: This widget will display a list of journal entries and provide actions like "New", "Edit", "Post".
3.  **Enhancing `app/accounting/journal_entry_manager.py`**: To handle the business logic for creating, validating, posting, and retrieving journal entries.
4.  **Ensuring `app/services/journal_service.py`** has all necessary data access methods.
5.  **Updating `app/ui/accounting/accounting_widget.py`** to include a tab for the new `JournalEntriesWidget`.

Let's start by creating the `app/ui/accounting/journal_entry_dialog.py`. This is a complex UI component, so I'll focus on its structure and key elements.

---
**1. Create `app/ui/accounting/journal_entry_dialog.py` (New File)**

This dialog will allow users to input all details for a journal entry.

```python
# File: app/ui/accounting/journal_entry_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit, QComboBox,
    QPushButton, QDialogButtonBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QDoubleSpinBox, QApplication
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer
from PySide6.QtGui import QIcon, QKeySequence
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from decimal import Decimal, InvalidOperation
import asyncio
from datetime import date as python_date

from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData
from app.models.accounting.account import Account
from app.models.accounting.tax_code import TaxCode
from app.models.accounting.currency import Currency
from app.models.accounting.dimension import Dimension
from app.models.accounting.journal_entry import JournalEntry # For loading existing
from app.common.enums import JournalTypeEnum # Assuming you have this
from app.main import schedule_task_from_qt

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class JournalEntryDialog(QDialog):
    # Signal to indicate a JE was saved, potentially with its ID
    journal_entry_saved = Signal(int) 

    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 journal_entry_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self.journal_entry_id = journal_entry_id
        self.existing_journal_entry: Optional[JournalEntry] = None

        self.setWindowTitle("Edit Journal Entry" if journal_entry_id else "New Journal Entry")
        self.setMinimumSize(800, 600)
        self.setModal(True)

        self._accounts_cache: List[Account] = []
        self._tax_codes_cache: List[TaxCode] = []
        self._currencies_cache: List[Currency] = []
        self._dimensions1_cache: List[Dimension] = [] # Assuming dimension type 1
        self._dimensions2_cache: List[Dimension] = [] # Assuming dimension type 2

        self._init_ui()
        self._connect_signals()

        # Load data asynchronously
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_initial_combo_data()))
        if self.journal_entry_id:
            QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_existing_journal_entry()))


    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Header Section ---
        header_form = QFormLayout()
        self.entry_date_edit = QDateEdit(QDate.currentDate())
        self.entry_date_edit.setCalendarPopup(True)
        self.entry_date_edit.setDisplayFormat("dd/MM/yyyy")
        header_form.addRow("Entry Date*:", self.entry_date_edit)

        self.journal_type_combo = QComboBox()
        # Populate with JournalTypeEnum values or common types
        self.journal_type_combo.addItems([jt.value for jt in JournalTypeEnum] if hasattr(JournalTypeEnum, '__members__') else ["General Journal"]) # Fallback
        header_form.addRow("Journal Type:", self.journal_type_combo)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Overall description for the journal entry")
        header_form.addRow("Description:", self.description_edit)

        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("e.g., Invoice #, Check #, Source Document ID")
        header_form.addRow("Reference:", self.reference_edit)
        
        main_layout.addLayout(header_form)

        # --- Lines Table Section ---
        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(8) # Account, Desc, Debit, Credit, Tax Code, Tax Amt, Dim1, Dim2
        self.lines_table.setHorizontalHeaderLabels([
            "Account", "Description", "Debit", "Credit", 
            "Tax Code", "Tax Amt", "Dept/Dim1", "Project/Dim2"
        ])
        self.lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.lines_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Account
        self.lines_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive) # Debit
        self.lines_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive) # Credit
        self.lines_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        # self.lines_table.setItemDelegateForColumn(2, CurrencyDelegate(self)) # Custom delegate for currency input
        # self.lines_table.setItemDelegateForColumn(3, CurrencyDelegate(self))
        main_layout.addWidget(self.lines_table)

        lines_button_layout = QHBoxLayout()
        self.add_line_button = QPushButton(QIcon.fromTheme("list-add"), "Add Line")
        self.remove_line_button = QPushButton(QIcon.fromTheme("list-remove"), "Remove Line")
        lines_button_layout.addWidget(self.add_line_button)
        lines_button_layout.addWidget(self.remove_line_button)
        lines_button_layout.addStretch()
        main_layout.addLayout(lines_button_layout)

        # --- Totals Section ---
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        self.debits_label = QLabel("Debits: 0.00")
        self.credits_label = QLabel("Credits: 0.00")
        self.balance_label = QLabel("Balance: OK") # Or "Out of Balance: X.XX"
        self.balance_label.setStyleSheet("font-weight: bold;")
        totals_layout.addWidget(self.debits_label)
        totals_layout.addWidget(QLabel(" | "))
        totals_layout.addWidget(self.credits_label)
        totals_layout.addWidget(QLabel(" | "))
        totals_layout.addWidget(self.balance_label)
        main_layout.addLayout(totals_layout)

        # --- Dialog Buttons ---
        self.button_box = QDialogButtonBox()
        self.save_draft_button = self.button_box.addButton("Save Draft", QDialogButtonBox.ButtonRole.ActionRole)
        self.save_post_button = self.button_box.addButton("Save & Post", QDialogButtonBox.ButtonRole.ActionRole)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)
        self._add_new_line() # Start with one empty line

    def _connect_signals(self):
        self.add_line_button.clicked.connect(self._add_new_line)
        self.remove_line_button.clicked.connect(self._remove_selected_line)
        self.lines_table.itemChanged.connect(self._calculate_totals) # For direct edits
        # More robust: connect to delegate's commitData or editor's editingFinished signals
        
        self.save_draft_button.clicked.connect(self.on_save_draft)
        self.save_post_button.clicked.connect(self.on_save_and_post)
        self.button_box.rejected.connect(self.reject)

    async def _load_initial_combo_data(self):
        # Load accounts, tax codes, currencies, dimensions for combo boxes in table cells
        # This runs in the asyncio thread.
        # For simplicity, we'll store them and assume QComboBox/QTableWidgetItem can be populated
        # directly. For very large lists, consider more optimized models or background population.
        try:
            if self.app_core.chart_of_accounts_manager:
                 self._accounts_cache = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(active_only=True)
            if self.app_core.tax_code_service:
                 self._tax_codes_cache = await self.app_core.tax_code_service.get_all() # Assuming get_all gets active ones
            if self.app_core.currency_manager:
                 self._currencies_cache = await self.app_core.currency_manager.get_active_currencies()
            # TODO: Load Dimensions (e.g., self.app_core.dimension_service.get_by_type('Department'))
            print(f"Loaded {len(self._accounts_cache)} accounts, {len(self._tax_codes_cache)} tax codes for JE Dialog.")
        except Exception as e:
            print(f"Error loading initial combo data for JE Dialog: {e}")
            # Show error via QMetaObject if critical, or let user proceed with potentially empty combos
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Data Load Error"), Q_ARG(str, f"Could not load all data for dropdowns: {e}"))


    async def _load_existing_journal_entry(self):
        if not self.journal_entry_id or not self.app_core.journal_entry_manager:
            return
        result = await self.app_core.journal_entry_manager.journal_service.get_by_id(self.journal_entry_id) # type: ignore
        if result:
            self.existing_journal_entry = result
            # Marshal UI update to main thread
            json_data = self._serialize_je_for_ui(self.existing_journal_entry)
            QMetaObject.invokeMethod(self, "_populate_dialog_from_data_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, json_data))
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, f"Journal Entry ID {self.journal_entry_id} not found."))


    def _serialize_je_for_ui(self, je: JournalEntry) -> str:
        data = {
            "entry_date": je.entry_date.isoformat(),
            "journal_type": je.journal_type,
            "description": je.description,
            "reference": je.reference,
            "lines": [
                {
                    "account_id": line.account_id,
                    "description": line.description,
                    "debit_amount": str(line.debit_amount),
                    "credit_amount": str(line.credit_amount),
                    "currency_code": line.currency_code,
                    "exchange_rate": str(line.exchange_rate),
                    "tax_code": line.tax_code,
                    "tax_amount": str(line.tax_amount),
                    "dimension1_id": line.dimension1_id,
                    "dimension2_id": line.dimension2_id,
                } for line in je.lines
            ]
        }
        return json.dumps(data)

    @Slot(str)
    def _populate_dialog_from_data_slot(self, json_data: str):
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse existing journal entry data.")
            return

        self.entry_date_edit.setDate(QDate.fromString(data["entry_date"], Qt.DateFormat.ISODate))
        
        type_idx = self.journal_type_combo.findText(data["journal_type"])
        if type_idx != -1: self.journal_type_combo.setCurrentIndex(type_idx)
        
        self.description_edit.setText(data.get("description", ""))
        self.reference_edit.setText(data.get("reference", ""))

        self.lines_table.setRowCount(0) # Clear existing lines
        for line_data in data.get("lines", []):
            self._add_new_line(line_data)
        self._calculate_totals()

        if self.existing_journal_entry and self.existing_journal_entry.is_posted:
            self.save_draft_button.setEnabled(False)
            self.save_post_button.setText("Already Posted")
            self.save_post_button.setEnabled(False)
            self.lines_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Read-only

    def _add_new_line(self, line_data: Optional[Dict[str, Any]] = None):
        row_position = self.lines_table.rowCount()
        self.lines_table.insertRow(row_position)

        # Account ComboBox
        acc_combo = QComboBox()
        acc_combo.setEditable(True) # Allow searching
        acc_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        # acc_combo.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion) # Requires QCompleter
        for acc in self._accounts_cache:
            acc_combo.addItem(f"{acc.code} - {acc.name}", acc.id)
        self.lines_table.setCellWidget(row_position, 0, acc_combo)

        # Description
        desc_item = QTableWidgetItem(line_data.get("description", "") if line_data else "")
        self.lines_table.setItem(row_position, 1, desc_item)

        # Debit / Credit (using QDoubleSpinBox for better input)
        debit_spin = QDoubleSpinBox(); debit_spin.setRange(0, 999999999.99); debit_spin.setDecimals(2)
        credit_spin = QDoubleSpinBox(); credit_spin.setRange(0, 999999999.99); credit_spin.setDecimals(2)
        if line_data:
            debit_spin.setValue(float(Decimal(line_data.get("debit_amount", "0"))))
            credit_spin.setValue(float(Decimal(line_data.get("credit_amount", "0"))))
        self.lines_table.setCellWidget(row_position, 2, debit_spin)
        self.lines_table.setCellWidget(row_position, 3, credit_spin)
        
        # Connect debit/credit spinbox valueChanged to ensure only one is non-zero
        debit_spin.valueChanged.connect(lambda val, r=row_position, cs=credit_spin: cs.setValue(0) if val > 0 else None)
        credit_spin.valueChanged.connect(lambda val, r=row_position, ds=debit_spin: ds.setValue(0) if val > 0 else None)
        debit_spin.valueChanged.connect(self._calculate_totals_from_signal) # Connect to recalculate totals
        credit_spin.valueChanged.connect(self._calculate_totals_from_signal)

        # Tax Code ComboBox
        tax_combo = QComboBox()
        tax_combo.addItem("None", None) # User data is None
        for tc in self._tax_codes_cache:
            tax_combo.addItem(f"{tc.code} ({tc.rate}%)", tc.code)
        if line_data and line_data.get("tax_code"):
            idx = tax_combo.findData(line_data["tax_code"])
            if idx != -1: tax_combo.setCurrentIndex(idx)
        self.lines_table.setCellWidget(row_position, 4, tax_combo)
        tax_combo.currentIndexChanged.connect(lambda index, r=row_position: self._recalculate_tax_for_line(r))


        # Tax Amount (read-only for now, or auto-calculated)
        tax_amt_item = QTableWidgetItem(line_data.get("tax_amount", "0.00") if line_data else "0.00")
        tax_amt_item.setFlags(tax_amt_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        tax_amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lines_table.setItem(row_position, 5, tax_amt_item)
        
        # Dimensions (Placeholders for now)
        dim1_combo = QComboBox(); dim1_combo.addItem("Default Dept", 0) # Example
        dim2_combo = QComboBox(); dim2_combo.addItem("Default Proj", 0) # Example
        self.lines_table.setCellWidget(row_position, 6, dim1_combo)
        self.lines_table.setCellWidget(row_position, 7, dim2_combo)


    def _remove_selected_line(self):
        current_row = self.lines_table.currentRow()
        if current_row >= 0 and self.lines_table.rowCount() > 1: # Keep at least one line
            self.lines_table.removeRow(current_row)
            self._calculate_totals()
        elif self.lines_table.rowCount() == 1:
            QMessageBox.warning(self, "Action Denied", "Cannot remove the last line. Add a new line first or clear fields.")

    @Slot() # To be connected if direct cell editing is enabled and totals need update
    def _calculate_totals_from_signal(self):
        self._calculate_totals()

    def _calculate_totals(self):
        total_debits = Decimal(0)
        total_credits = Decimal(0)
        for row in range(self.lines_table.rowCount()):
            debit_spin = self.lines_table.cellWidget(row, 2)
            credit_spin = self.lines_table.cellWidget(row, 3)
            if isinstance(debit_spin, QDoubleSpinBox):
                total_debits += Decimal(str(debit_spin.value()))
            if isinstance(credit_spin, QDoubleSpinBox):
                total_credits += Decimal(str(credit_spin.value()))
        
        self.debits_label.setText(f"Debits: {total_debits:,.2f}")
        self.credits_label.setText(f"Credits: {total_credits:,.2f}")

        if abs(total_debits - total_credits) < Decimal("0.005"): # Tolerance for float
            self.balance_label.setText("Balance: OK")
            self.balance_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            diff = total_debits - total_credits
            self.balance_label.setText(f"Out of Balance: {diff:,.2f}")
            self.balance_label.setStyleSheet("font-weight: bold; color: red;")

    def _recalculate_tax_for_line(self, row: int):
        # This function would be called when a tax code or amount changes in a line
        # For MVP, this might be manual or a simplified auto-calc.
        # Get amount (debit or credit), get tax code, fetch rate, calculate tax_amount
        # Update the tax_amount cell. Then call _calculate_totals()
        try:
            debit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 2))
            credit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 3))
            tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, 4))
            tax_amt_item = self.lines_table.item(row, 5)
            if not tax_amt_item: # Create if not exists
                tax_amt_item = QTableWidgetItem("0.00")
                tax_amt_item.setFlags(tax_amt_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                tax_amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.lines_table.setItem(row, 5, tax_amt_item)


            base_amount = Decimal(str(debit_spin.value())) if debit_spin.value() > 0 else Decimal(str(credit_spin.value()))
            tax_code_str = tax_combo.currentData() # Get the tax code (e.g., 'SR')

            if tax_code_str and base_amount != Decimal(0):
                # Find the tax code object from cache
                tc_obj = next((tc for tc in self._tax_codes_cache if tc.code == tax_code_str), None)
                if tc_obj and tc_obj.tax_type == "GST": # Only for GST for now
                    tax_rate = tc_obj.rate / Decimal(100)
                    calculated_tax = (base_amount * tax_rate).quantize(Decimal("0.01"))
                    tax_amt_item.setText(f"{calculated_tax:,.2f}")
                else:
                    tax_amt_item.setText("0.00")
            else:
                tax_amt_item.setText("0.00")
        except Exception as e:
            print(f"Error recalculating tax for row {row}: {e}")
            if tax_amt_item: tax_amt_item.setText("Error")
        
        self._calculate_totals()


    def _collect_data(self) -> Optional[JournalEntryData]:
        lines_data: List[JournalEntryLineData] = []
        for row in range(self.lines_table.rowCount()):
            try:
                acc_combo = cast(QComboBox, self.lines_table.cellWidget(row, 0))
                desc_item = self.lines_table.item(row, 1)
                debit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 2))
                credit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 3))
                tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, 4))
                tax_amt_item = self.lines_table.item(row, 5)
                dim1_combo = cast(QComboBox, self.lines_table.cellWidget(row, 6)) # Placeholder
                dim2_combo = cast(QComboBox, self.lines_table.cellWidget(row, 7)) # Placeholder

                account_id = acc_combo.currentData()
                if account_id is None: # Skip line if no account selected
                    # Or raise validation error if all lines must have accounts
                    if debit_spin.value() != 0 or credit_spin.value() != 0: # Only error if there are amounts
                        QMessageBox.warning(self, "Validation Error", f"Account not selected for line {row+1} with amounts.")
                        return None
                    continue 

                line_dto = JournalEntryLineData(
                    account_id=int(account_id),
                    description=desc_item.text() if desc_item else "",
                    debit_amount=Decimal(str(debit_spin.value())),
                    credit_amount=Decimal(str(credit_spin.value())),
                    tax_code=tax_combo.currentData(), # Store the code ('SR')
                    tax_amount=Decimal(tax_amt_item.text().replace(',','')) if tax_amt_item else Decimal(0),
                    dimension1_id=dim1_combo.currentData() if dim1_combo.currentData() != 0 else None, # Assuming 0 for None
                    dimension2_id=dim2_combo.currentData() if dim2_combo.currentData() != 0 else None
                )
                lines_data.append(line_dto)
            except Exception as e:
                QMessageBox.warning(self, "Input Error", f"Error processing line {row + 1}: {e}")
                return None
        
        if not lines_data:
            QMessageBox.warning(self, "Input Error", "Journal entry must have at least one line.")
            return None

        try:
            entry_data = JournalEntryData(
                journal_type=self.journal_type_combo.currentText(),
                entry_date=self.entry_date_edit.date().toPython(),
                description=self.description_edit.text().strip() or None,
                reference=self.reference_edit.text().strip() or None,
                user_id=self.current_user_id,
                lines=lines_data,
                source_type=self.existing_journal_entry.source_type if self.existing_journal_entry else None,
                source_id=self.existing_journal_entry.source_id if self.existing_journal_entry else None,
                # is_recurring and recurring_pattern_id are not set in this basic dialog
            )
            return entry_data
        except ValueError as e: # Pydantic validation error
            QMessageBox.warning(self, "Validation Error", str(e))
            return None

    @Slot()
    def on_save_draft(self):
        if self.existing_journal_entry and self.existing_journal_entry.is_posted:
            QMessageBox.information(self, "Info", "Cannot save a posted journal entry as draft.")
            return
            
        entry_data = self._collect_data()
        if entry_data:
            schedule_task_from_qt(self._perform_save(entry_data, post_after_save=False))

    @Slot()
    def on_save_and_post(self):
        if self.existing_journal_entry and self.existing_journal_entry.is_posted:
            QMessageBox.information(self, "Info", "Journal entry is already posted.")
            return

        entry_data = self._collect_data()
        if entry_data:
            schedule_task_from_qt(self._perform_save(entry_data, post_after_save=True))

    async def _perform_save(self, entry_data: JournalEntryData, post_after_save: bool):
        manager = self.app_core.journal_entry_manager
        if not manager:
             QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Journal Entry Manager not available."))
             return

        if self.existing_journal_entry and self.existing_journal_entry.id: # Update existing draft
            result = await manager.update_journal_entry(self.existing_journal_entry.id, entry_data) # Needs update_journal_entry method
        else: # Create new
            result = await manager.create_journal_entry(entry_data)

        if result.is_success:
            saved_je = result.value
            assert saved_je is not None
            if post_after_save:
                post_result = await manager.post_journal_entry(saved_je.id, self.current_user_id)
                if post_result.is_success:
                    QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                        Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, "Journal entry saved and posted successfully."))
                    QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
                    self.journal_entry_saved.emit(saved_je.id)
                else:
                    error_msg = f"Journal entry saved as draft (ID: {saved_je.id}), but failed to post:\n{', '.join(post_result.errors)}"
                    QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                        Q_ARG(QWidget, self), Q_ARG(str, "Posting Error"), Q_ARG(str, error_msg))
                    # Dialog remains open for user to decide next step
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, "Journal entry saved as draft successfully."))
                QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
                self.journal_entry_saved.emit(saved_je.id)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), Q_ARG(str, f"Failed to save journal entry:\n{', '.join(result.errors)}"))
```

**Validation of `app/ui/accounting/fiscal_year_dialog.py`:**
*   Correctly uses `QDateEdit` for dates, `QComboBox` for period generation type.
*   `_update_default_end_date` slot provides a helpful default for the end date.
*   `accept_data` performs client-side validation and creates the `FiscalYearCreateData` DTO.
*   `get_fiscal_year_data` provides access to the DTO.
*   `open()` method correctly resets the dialog for new entries.
*   Imported `python_date` alias to avoid conflicts with `QDate`.

---
Next, I will update `app/ui/settings/settings_widget.py` to integrate this dialog.
