<think>
The application continues to launch and shut down cleanly, and the `JournalEntryTableModel` has been reviewed and refined. This is excellent progress.

**Current Step: Phase 2: Integrate Journal Entry UI (Continued)**

The next file in line according to the plan and natural progression is `app/ui/accounting/journal_entry_dialog.py`.
This dialog is critical for creating new journal entries and viewing/editing existing ones.

**Plan for `app/ui/accounting/journal_entry_dialog.py` Refinements:**

1.  **Interaction with Manager**:
    *   `_load_existing_journal_entry()`: Must correctly call `self.app_core.journal_entry_manager.get_journal_entry_for_dialog(self.journal_entry_id)`. The result is an ORM object (`JournalEntry`), which then needs to be serialized to JSON for cross-thread UI update via `_populate_dialog_from_data_slot`.
    *   `_perform_save()`:
        *   If `self.journal_entry_id` exists (i.e., editing), it should call `self.app_core.journal_entry_manager.update_journal_entry(self.journal_entry_id, entry_data_dto)`.
        *   If it's a new entry, call `self.app_core.journal_entry_manager.create_journal_entry(entry_data_dto)`.
        *   Handle the `Result` object from these manager calls. On success, emit `self.journal_entry_saved.emit(saved_je.id)` and `self.accept()`. On failure, show an error message.
        *   If "Save & Post" is clicked, after a successful save, call `self.app_core.journal_entry_manager.post_journal_entry(saved_je.id, self.current_user_id)`.
2.  **Data Population and State Management**:
    *   `_populate_dialog_from_data_slot()`: Must correctly parse the JSON (serialized ORM data) and populate all header fields and line items in the `QTableWidget`.
    *   **Read-only/View Mode**: If `self.view_only_mode` is true, or if the loaded `entry_data.get("is_posted")` is true, all input fields, add/remove line buttons, and save buttons must be disabled. The window title should reflect "View Journal Entry".
3.  **ComboBoxes for Lines (Account, Tax Code)**:
    *   `_load_initial_combo_data()`: Asynchronously fetch active accounts from `ChartOfAccountsManager.get_accounts_for_selection()` and tax codes from `TaxCodeService.get_all()`.
    *   `_populate_combos_for_row()`: When adding a new line or populating from existing data, correctly fill these comboboxes and set their current index based on the `line_data` (if provided). It should handle cases where a loaded line has an account/tax code that might now be inactive (e.g., display "ID: X (Inactive)" or similar).
4.  **Line Item Logic**:
    *   `_add_new_line()`: Ensure it correctly creates `QComboBox` for Account and Tax Code, and `QDoubleSpinBox` for Debit/Credit amounts. Connect their `valueChanged` or `currentIndexChanged` signals to `_recalculate_tax_for_line` and `_calculate_totals`.
    *   `_recalculate_tax_for_line()`:
        *   Get the base amount (debit or credit).
        *   Get the selected tax code from the `QComboBox` (`currentData()` should give the tax code string).
        *   Fetch the `TaxCode` object from `self._tax_codes_cache` or call the `TaxCalculator` service if the logic is complex. For now, simple percentage is fine.
        *   Update the read-only "Tax Amt" cell.
        *   Trigger `_calculate_totals()`.
    *   `_calculate_totals()`: Accurately sum debits and credits from all lines and update the total labels and balance status display (OK/Out of Balance).
5.  **Data Collection (`_collect_data`)**:
    *   Robustly gather all data from header and line item widgets.
    *   Correctly use `QComboBox.currentData()` to get IDs/codes.
    *   Convert amounts to `Decimal`.
    *   Perform client-side validation (e.g., at least one line, account selected if amounts > 0, balanced entry check before DTO creation).
    *   Construct and return a `JournalEntryData` DTO.
6.  **Error Handling**: Display informative `QMessageBox` for validation errors or failures from manager calls.
7.  **Signal Emission**: Emit `self.journal_entry_saved.emit(saved_je_id)` on successful save/post.

The existing structure for `JournalEntryDialog` (as of file set 2) is a very good base. The main work is to ensure the interactions with the manager are precise, data flow is correct, and all states (new, edit, view, posted) are handled gracefully.
I will pay close attention to the `_perform_save` logic and the line item handling during updates.
The `CurrencyDelegate` is a nice touch for formatting, but `QDoubleSpinBox` itself with `setGroupSeparatorShown(True)` can also display commas. If `CurrencyDelegate` is used, ensure it's correctly applied. For simplicity and fewer custom classes, relying on `QDoubleSpinBox` features is often easier. I'll assume the `QDoubleSpinBox` is directly set as cell widgets for now.
The previous implementation correctly connected `valueChanged` for spinboxes to trigger total calculation. `currentIndexChanged` for tax code combo should trigger tax recalculation.
</think>

The application is stable, which is excellent. We're now ready to refine the UI components for Journal Entry management, ensuring they connect seamlessly with the backend.

The `app/ui/accounting/journal_entry_table_model.py` has been reviewed and updated. The next crucial file is `app/ui/accounting/journal_entry_dialog.py`. This dialog is central to creating, viewing, and editing journal entries.

**Goal for `app/ui/accounting/journal_entry_dialog.py`:**
Ensure it robustly handles data loading for existing entries, populates UI elements correctly (especially comboboxes in table lines), collects data into DTOs, interacts with `JournalEntryManager` for save/post operations, and manages UI state (e.g., read-only for posted/view-only entries).

---
**2. Update `app/ui/accounting/journal_entry_dialog.py`**

```python
# app/ui/accounting/journal_entry_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit, QComboBox,
    QPushButton, QDialogButtonBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QDoubleSpinBox, QApplication, QStyledItemDelegate,
    QAbstractSpinBox # For QDoubleSpinBox.NoButtons
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon, QKeySequence, QColor, QPalette
from typing import Optional, List, Dict, Any, TYPE_CHECKING, cast
from decimal import Decimal, InvalidOperation
import asyncio
import json
from datetime import date as python_date

from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData
from app.models.accounting.account import Account
from app.models.accounting.tax_code import TaxCode
# from app.models.accounting.currency import Currency # Not directly used in this version for line combos
from app.models.accounting.journal_entry import JournalEntry 
from app.common.enums import JournalTypeEnum 
from app.main import schedule_task_from_qt
from app.utils.json_helpers import json_converter, json_date_hook 
from app.utils.result import Result # For type hinting manager results

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore


class JournalEntryDialog(QDialog):
    journal_entry_saved = Signal(int) # Emits the ID of the saved/updated JE

    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 journal_entry_id: Optional[int] = None, 
                 view_only: bool = False, 
                 parent: Optional[QWidget] = None): # Added QWidget type hint
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self.journal_entry_id = journal_entry_id
        self.view_only_mode = view_only 
        self.loaded_journal_entry_orm: Optional[JournalEntry] = None # Store loaded ORM for reference
        self.existing_journal_entry_data_dict: Optional[Dict[str, Any]] = None # Store raw loaded data for combo repopulation

        self._accounts_cache: List[Account] = []
        self._tax_codes_cache: List[TaxCode] = []
        
        self.setWindowTitle(self._get_window_title())
        self.setMinimumSize(900, 700) # Slightly wider for better table layout
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_initial_combo_data()))
        if self.journal_entry_id:
            QTimer.singleShot(50, lambda: schedule_task_from_qt(self._load_existing_journal_entry()))
        elif not self.view_only_mode: # Only add initial lines for new, editable entries
            self._add_new_line() 
            self._add_new_line() 

    def _get_window_title(self) -> str:
        if self.view_only_mode: return "View Journal Entry"
        if self.journal_entry_id: return "Edit Journal Entry"
        return "New Journal Entry"

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        header_form = QFormLayout()
        header_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.entry_date_edit = QDateEdit(QDate.currentDate())
        self.entry_date_edit.setCalendarPopup(True)
        self.entry_date_edit.setDisplayFormat("dd/MM/yyyy")
        header_form.addRow("Entry Date*:", self.entry_date_edit)

        self.journal_type_combo = QComboBox()
        for jt_enum_member in JournalTypeEnum: self.journal_type_combo.addItem(jt_enum_member.value, jt_enum_member.value)
        self.journal_type_combo.setCurrentText(JournalTypeEnum.GENERAL.value)
        header_form.addRow("Journal Type:", self.journal_type_combo)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Overall description for the journal entry")
        header_form.addRow("Description:", self.description_edit)

        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("e.g., Invoice #, Check #, Source Document ID")
        header_form.addRow("Reference:", self.reference_edit)
        
        main_layout.addLayout(header_form)

        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(7) 
        self.lines_table.setHorizontalHeaderLabels([
            "Account*", "Description", "Debit*", "Credit*", 
            "Tax Code", "Tax Amt", "" 
        ])
        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) 
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed) 
        self.lines_table.setColumnWidth(2, 130); self.lines_table.setColumnWidth(3, 130) # Debit/Credit
        self.lines_table.setColumnWidth(4, 160); self.lines_table.setColumnWidth(5, 110) # Tax Code/Amt
        self.lines_table.setColumnWidth(6, 30) 
        self.lines_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        main_layout.addWidget(self.lines_table)

        lines_button_layout = QHBoxLayout()
        icon_path_prefix = "resources/icons/" 
        try: import app.resources_rc; icon_path_prefix = ":/icons/" # type: ignore
        except ImportError: pass
        
        self.add_line_button = QPushButton(QIcon(icon_path_prefix + "add.svg"), "Add Line")
        self.remove_line_button = QPushButton(QIcon(icon_path_prefix + "remove.svg"), "Remove Selected Line")
        lines_button_layout.addWidget(self.add_line_button)
        lines_button_layout.addWidget(self.remove_line_button)
        lines_button_layout.addStretch()
        main_layout.addLayout(lines_button_layout)

        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        self.debits_label = QLabel("Debits: 0.00")
        self.credits_label = QLabel("Credits: 0.00")
        self.balance_label = QLabel("Balance: OK")
        self.balance_label.setStyleSheet("font-weight: bold;")
        totals_layout.addWidget(self.debits_label); totals_layout.addWidget(QLabel("  |  "));
        totals_layout.addWidget(self.credits_label); totals_layout.addWidget(QLabel("  |  "));
        totals_layout.addWidget(self.balance_label)
        main_layout.addLayout(totals_layout)

        self.button_box = QDialogButtonBox()
        self.save_draft_button = self.button_box.addButton("Save Draft", QDialogButtonBox.ButtonRole.ActionRole)
        self.save_post_button = self.button_box.addButton("Save & Post", QDialogButtonBox.ButtonRole.ActionRole)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Close if self.view_only_mode else QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def _connect_signals(self):
        self.add_line_button.clicked.connect(self._add_new_line)
        self.remove_line_button.clicked.connect(self._remove_selected_line)
        self.save_draft_button.clicked.connect(self.on_save_draft)
        self.save_post_button.clicked.connect(self.on_save_and_post)
        if self.view_only_mode:
            self.button_box.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.reject) # type: ignore
        else:
            self.button_box.rejected.connect(self.reject)

    async def _load_initial_combo_data(self):
        try:
            if self.app_core.chart_of_accounts_manager:
                 self._accounts_cache = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(active_only=True)
            if self.app_core.tax_code_service:
                 self._tax_codes_cache = await self.app_core.tax_code_service.get_all() # Assuming get_all fetches active ones or is filtered later
            
            # If dialog is already populated (e.g. from _load_existing_journal_entry),
            # ensure combos in existing rows are updated/re-populated.
            QMetaObject.invokeMethod(self, "_update_combos_in_all_lines_slot", Qt.ConnectionType.QueuedConnection)

        except Exception as e:
            self.app_core.logger.error(f"Error loading initial combo data for JE Dialog: {e}", exc_info=True) # type: ignore
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Data Load Error"), Q_ARG(str, f"Could not load all data for dropdowns: {e}"))

    @Slot()
    def _update_combos_in_all_lines_slot(self):
        for r in range(self.lines_table.rowCount()):
            line_data_to_use = None
            if self.existing_journal_entry_data_dict and r < len(self.existing_journal_entry_data_dict.get("lines",[])):
                line_data_to_use = self.existing_journal_entry_data_dict["lines"][r]
            self._populate_combos_for_row(r, line_data_to_use)


    async def _load_existing_journal_entry(self):
        if not self.journal_entry_id or not self.app_core.journal_entry_manager: return
        
        self.loaded_journal_entry_orm = await self.app_core.journal_entry_manager.get_journal_entry_for_dialog(self.journal_entry_id)
        if self.loaded_journal_entry_orm:
            json_data_str = self._serialize_je_for_ui(self.loaded_journal_entry_orm)
            QMetaObject.invokeMethod(self, "_populate_dialog_from_data_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, json_data_str))
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, f"Journal Entry ID {self.journal_entry_id} not found."))
            self.reject()


    def _serialize_je_for_ui(self, je: JournalEntry) -> str: # Converts ORM to JSON string
        data = {
            "entry_date": je.entry_date, "journal_type": je.journal_type,
            "description": je.description, "reference": je.reference,
            "is_posted": je.is_posted, "source_type": je.source_type, "source_id": je.source_id,
            "lines": [
                { "account_id": line.account_id, "description": line.description,
                  "debit_amount": line.debit_amount, "credit_amount": line.credit_amount,
                  "currency_code": line.currency_code, "exchange_rate": line.exchange_rate,
                  "tax_code": line.tax_code, "tax_amount": line.tax_amount,
                  "dimension1_id": line.dimension1_id, "dimension2_id": line.dimension2_id,
                } for line in je.lines ]}
        return json.dumps(data, default=json_converter)

    @Slot(str)
    def _populate_dialog_from_data_slot(self, json_data_str: str): # Parses JSON and populates UI
        try:
            data = json.loads(json_data_str, object_hook=json_date_hook)
            self.existing_journal_entry_data_dict = data # Store for combo repopulation
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse existing journal entry data."); return

        if data.get("entry_date"): self.entry_date_edit.setDate(QDate(data["entry_date"])) # QDate handles python_date
        type_idx = self.journal_type_combo.findText(data.get("journal_type", JournalTypeEnum.GENERAL.value))
        if type_idx != -1: self.journal_type_combo.setCurrentIndex(type_idx)
        self.description_edit.setText(data.get("description", ""))
        self.reference_edit.setText(data.get("reference", ""))

        self.lines_table.setRowCount(0) 
        for line_data_dict in data.get("lines", []): self._add_new_line(line_data_dict)
        if not data.get("lines") and not self.view_only_mode: self._add_new_line(); self._add_new_line()
        self._calculate_totals()

        # is_posted might be False if we are editing a draft, but self.view_only_mode can be True
        is_read_only = self.view_only_mode or data.get("is_posted", False)
        if is_read_only:
            self.save_draft_button.setVisible(False) # Hide instead of disable for cleaner look
            self.save_post_button.setVisible(False)
            self.lines_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            for i in range(header_form.rowCount()): # Make header form fields read-only
                widget = header_form.itemAt(i, QFormLayout.FieldRole).widget()
                if isinstance(widget, (QLineEdit, QDateEdit)): widget.setReadOnly(True)
                elif isinstance(widget, QComboBox): widget.setEnabled(False)
            self.add_line_button.setEnabled(False); self.remove_line_button.setEnabled(False)
            for r in range(self.lines_table.rowCount()): # Make line delete buttons invisible
                del_btn_widget = self.lines_table.cellWidget(r, 6)
                if del_btn_widget : del_btn_widget.setVisible(False)


    def _populate_combos_for_row(self, row: int, line_data_for_this_row: Optional[Dict[str, Any]] = None):
        acc_combo = cast(QComboBox, self.lines_table.cellWidget(row, 0))
        if not acc_combo: acc_combo = QComboBox(); self.lines_table.setCellWidget(row, 0, acc_combo)
        acc_combo.clear()
        acc_combo.setEditable(True); acc_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        # acc_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains) # Requires QCompleter setup
        # acc_combo.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

        current_acc_id = line_data_for_this_row.get("account_id") if line_data_for_this_row else None
        selected_acc_idx = -1
        for i, acc_orm in enumerate(self._accounts_cache):
            acc_combo.addItem(f"{acc_orm.code} - {acc_orm.name}", acc_orm.id)
            if acc_orm.id == current_acc_id: selected_acc_idx = i
        
        if selected_acc_idx != -1: acc_combo.setCurrentIndex(selected_acc_idx)
        elif current_acc_id and self.loaded_journal_entry_orm: # Account from data not in active cache (e.g. inactive, or data is old)
            # Try to find it in the originally loaded ORM lines for display
            orig_line_orm = next((l for l in self.loaded_journal_entry_orm.lines if l.account_id == current_acc_id), None)
            if orig_line_orm and orig_line_orm.account:
                acc_combo.addItem(f"{orig_line_orm.account.code} - {orig_line_orm.account.name} (Inactive?)", current_acc_id)
                acc_combo.setCurrentIndex(acc_combo.count() -1)
            else: # Fallback if still not found
                acc_combo.addItem(f"ID: {current_acc_id} (Unknown/Not Found)", current_acc_id)
                acc_combo.setCurrentIndex(acc_combo.count() -1)

        tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, 4))
        if not tax_combo: tax_combo = QComboBox(); self.lines_table.setCellWidget(row, 4, tax_combo)
        tax_combo.clear()
        tax_combo.addItem("None", "") # Use empty string for "None" data for Pydantic Optional[str]
        current_tax_code_str = line_data_for_this_row.get("tax_code") if line_data_for_this_row else None
        selected_tax_idx = 0 # Default to "None"
        for i, tc_orm in enumerate(self._tax_codes_cache):
            tax_combo.addItem(f"{tc_orm.code} ({tc_orm.rate}%)", tc_orm.code)
            if tc_orm.code == current_tax_code_str: selected_tax_idx = i + 1
        
        tax_combo.setCurrentIndex(selected_tax_idx)
        # No need for unknown/inactive handling for tax codes as "None" is a valid option.


    def _add_new_line(self, line_data: Optional[Dict[str, Any]] = None):
        row_position = self.lines_table.rowCount()
        self.lines_table.insertRow(row_position)

        acc_combo = QComboBox(); self.lines_table.setCellWidget(row_position, 0, acc_combo)
        
        desc_item = QTableWidgetItem(line_data.get("description", "") if line_data else "")
        self.lines_table.setItem(row_position, 1, desc_item)

        debit_spin = QDoubleSpinBox(); debit_spin.setRange(0, 999999999999.99); debit_spin.setDecimals(2); debit_spin.setGroupSeparatorShown(True); debit_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        credit_spin = QDoubleSpinBox(); credit_spin.setRange(0, 999999999999.99); credit_spin.setDecimals(2); credit_spin.setGroupSeparatorShown(True); credit_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        if line_data:
            debit_spin.setValue(float(Decimal(str(line_data.get("debit_amount", "0")))))
            credit_spin.setValue(float(Decimal(str(line_data.get("credit_amount", "0")))))
        self.lines_table.setCellWidget(row_position, 2, debit_spin)
        self.lines_table.setCellWidget(row_position, 3, credit_spin)
        
        # Connect signals *after* setting initial values if line_data exists to avoid premature triggers
        debit_spin.valueChanged.connect(lambda val, r=row_position, cs=credit_spin: cs.setValue(0) if val > 0.001 else None)
        credit_spin.valueChanged.connect(lambda val, r=row_position, ds=debit_spin: ds.setValue(0) if val > 0.001 else None)
        debit_spin.valueChanged.connect(self._calculate_totals_and_tax_for_row_slot(row_position))
        credit_spin.valueChanged.connect(self._calculate_totals_and_tax_for_row_slot(row_position))

        tax_combo = QComboBox(); self.lines_table.setCellWidget(row_position, 4, tax_combo)
        tax_combo.currentIndexChanged.connect(self._calculate_totals_and_tax_for_row_slot(row_position))

        initial_tax_amt_str = "0.00"
        if line_data and line_data.get("tax_amount") is not None:
            initial_tax_amt_str = str(Decimal(str(line_data.get("tax_amount"))).quantize(Decimal("0.01")))
        tax_amt_item = QTableWidgetItem(initial_tax_amt_str)
        tax_amt_item.setFlags(tax_amt_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        tax_amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lines_table.setItem(row_position, 5, tax_amt_item)
        
        icon_path_prefix = "resources/icons/" 
        try: import app.resources_rc; icon_path_prefix = ":/icons/" # type: ignore
        except ImportError: pass
        del_button = QPushButton(QIcon(icon_path_prefix + "remove.svg"))
        del_button.setToolTip("Remove this line"); del_button.setFixedSize(24,24)
        del_button.clicked.connect(lambda _, r=row_position: self._remove_specific_line(r))
        self.lines_table.setCellWidget(row_position, 6, del_button)

        self._populate_combos_for_row(row_position, line_data) # Populate combos using cache
        self._recalculate_tax_for_line(row_position) # Initial tax calc for the new line
        self._calculate_totals() # Update overall totals

    def _calculate_totals_and_tax_for_row_slot(self, row: int):
        return lambda: self._chain_recalculate_tax_and_totals(row)

    def _chain_recalculate_tax_and_totals(self, row: int):
        self._recalculate_tax_for_line(row)
        # _calculate_totals() is called within _recalculate_tax_for_line()

    def _remove_selected_line(self):
        current_row = self.lines_table.currentRow()
        if current_row >= 0: self._remove_specific_line(current_row)

    def _remove_specific_line(self, row_to_remove: int):
        if self.view_only_mode or (self.loaded_journal_entry_orm and self.loaded_journal_entry_orm.is_posted): return
        if self.lines_table.rowCount() > 0 : # Allow removing to zero lines, validation is on save
            self.lines_table.removeRow(row_to_remove)
            self._calculate_totals()
        # else: QMessageBox.information(self, "Action Denied", "No lines to remove.")


    @Slot() 
    def _calculate_totals_from_signal(self): # Connected to amount spinboxes
        self._calculate_totals()

    def _calculate_totals(self):
        total_debits = Decimal(0)
        total_credits = Decimal(0)
        for row in range(self.lines_table.rowCount()):
            debit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 2))
            credit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 3))
            if debit_spin: total_debits += Decimal(str(debit_spin.value()))
            if credit_spin: total_credits += Decimal(str(credit_spin.value()))
        
        self.debits_label.setText(f"Debits: {total_debits:,.2f}")
        self.credits_label.setText(f"Credits: {total_credits:,.2f}")

        if abs(total_debits - total_credits) < Decimal("0.005"): 
            self.balance_label.setText("Balance: OK")
            self.balance_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            diff = total_debits - total_credits
            self.balance_label.setText(f"Balance: {diff:,.2f}")
            self.balance_label.setStyleSheet("font-weight: bold; color: red;")


    def _recalculate_tax_for_line(self, row: int):
        try:
            debit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 2))
            credit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 3))
            tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, 4))
            tax_amt_item = self.lines_table.item(row, 5)

            if not all([debit_spin, credit_spin, tax_combo]): return 
            if not tax_amt_item: 
                tax_amt_item = QTableWidgetItem("0.00")
                tax_amt_item.setFlags(tax_amt_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                tax_amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.lines_table.setItem(row, 5, tax_amt_item)

            base_amount = Decimal(str(debit_spin.value())) if debit_spin.value() > 0 else Decimal(str(credit_spin.value()))
            tax_code_str = tax_combo.currentData() # This should be the tax code string (e.g., "SR")
            
            calculated_tax = Decimal(0)
            if tax_code_str and base_amount != Decimal(0):
                tc_obj = next((tc for tc in self._tax_codes_cache if tc.code == tax_code_str), None)
                if tc_obj and tc_obj.tax_type == "GST" and tc_obj.rate is not None:
                    tax_rate = tc_obj.rate / Decimal(100)
                    calculated_tax = (base_amount * tax_rate).quantize(Decimal("0.01"))
            
            tax_amt_item.setText(f"{calculated_tax:,.2f}")
        except Exception as e:
            self.app_core.logger.error(f"Error recalculating tax for row {row}: {e}", exc_info=True) # type: ignore
            if tax_amt_item: tax_amt_item.setText("Error")
        finally:
            self._calculate_totals() # Always update totals after tax recalc attempt


    def _collect_data(self) -> Optional[JournalEntryData]:
        lines_data: List[JournalEntryLineData] = []
        total_debits = Decimal(0)
        total_credits = Decimal(0)

        for row in range(self.lines_table.rowCount()):
            try:
                acc_combo = cast(QComboBox, self.lines_table.cellWidget(row, 0))
                desc_item_widget = self.lines_table.item(row, 1)
                debit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 2))
                credit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 3))
                tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, 4))
                tax_amt_item_widget = self.lines_table.item(row, 5)

                account_id = acc_combo.currentData() if acc_combo else None
                line_debit = Decimal(str(debit_spin.value())) if debit_spin else Decimal(0)
                line_credit = Decimal(str(credit_spin.value())) if credit_spin else Decimal(0)

                if account_id is None and (line_debit != Decimal(0) or line_credit != Decimal(0)):
                    QMessageBox.warning(self, "Validation Error", f"Account not selected for line {row + 1} which has amounts.")
                    return None
                if account_id is None: continue # Skip empty lines without account

                line_dto = JournalEntryLineData(
                    account_id=int(account_id),
                    description=desc_item_widget.text() if desc_item_widget else "",
                    debit_amount=line_debit,
                    credit_amount=line_credit,
                    tax_code=tax_combo.currentData() if tax_combo and tax_combo.currentData() else None, 
                    tax_amount=Decimal(tax_amt_item_widget.text().replace(',', '')) if tax_amt_item_widget and tax_amt_item_widget.text() else Decimal(0),
                    currency_code="SGD", # Default, make dynamic if multi-currency line items
                    exchange_rate=Decimal(1), # Default
                    dimension1_id=None, dimension2_id=None # Placeholder
                )
                lines_data.append(line_dto)
                total_debits += line_debit
                total_credits += line_credit
            except Exception as e:
                QMessageBox.warning(self, "Input Error", f"Error processing line {row + 1}: {e}")
                return None
        
        if not lines_data:
             QMessageBox.warning(self, "Input Error", "Journal entry must have at least one valid line.")
             return None
        
        if abs(total_debits - total_credits) > Decimal("0.01"): # Stricter check
            QMessageBox.warning(self, "Balance Error", f"Journal entry is not balanced. Debits: {total_debits:,.2f}, Credits: {total_credits:,.2f}.")
            return None

        try:
            source_type = self.loaded_journal_entry_orm.source_type if self.loaded_journal_entry_orm else None
            source_id = self.loaded_journal_entry_orm.source_id if self.loaded_journal_entry_orm else None
            if self.existing_journal_entry_data_dict: # Prefer DTO if available (e.g. if ORM wasn't loaded due to error but dict was)
                source_type = self.existing_journal_entry_data_dict.get("source_type", source_type)
                source_id = self.existing_journal_entry_data_dict.get("source_id", source_id)


            entry_data = JournalEntryData(
                journal_type=self.journal_type_combo.currentText(),
                entry_date=self.entry_date_edit.date().toPython(),
                description=self.description_edit.text().strip() or None,
                reference=self.reference_edit.text().strip() or None,
                user_id=self.current_user_id,
                lines=lines_data,
                source_type=source_type,
                source_id=source_id
            )
            return entry_data
        except ValueError as e: 
            QMessageBox.warning(self, "Validation Error", str(e))
            return None

    @Slot()
    def on_save_draft(self):
        if self.view_only_mode or (self.loaded_journal_entry_orm and self.loaded_journal_entry_orm.is_posted):
            QMessageBox.information(self, "Info", "Cannot save. Entry is posted or in view-only mode.")
            return
            
        entry_data = self._collect_data()
        if entry_data:
            schedule_task_from_qt(self._perform_save(entry_data, post_after_save=False))

    @Slot()
    def on_save_and_post(self):
        if self.view_only_mode or (self.loaded_journal_entry_orm and self.loaded_journal_entry_orm.is_posted):
            QMessageBox.information(self, "Info", "Cannot save and post. Entry is already posted or in view-only mode.")
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

        result: Result[JournalEntry]
        if self.journal_entry_id and self.loaded_journal_entry_orm: # Check if we are editing
            result = await manager.update_journal_entry(self.journal_entry_id, entry_data)
        else: 
            result = await manager.create_journal_entry(entry_data)

        if result.is_success:
            saved_je = result.value
            assert saved_je is not None
            if post_after_save:
                post_result = await manager.post_journal_entry(saved_je.id, self.current_user_id)
                if post_result.is_success:
                    QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                        Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, "Journal entry saved and posted successfully."))
                    self.journal_entry_saved.emit(saved_je.id)
                    QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
                else:
                    error_msg = f"Journal entry saved as draft (ID: {saved_je.id}), but failed to post:\n{', '.join(post_result.errors)}"
                    QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                        Q_ARG(QWidget, self), Q_ARG(str, "Posting Error"), Q_ARG(str, error_msg))
                    self.journal_entry_saved.emit(saved_je.id) # Still emit saved signal for draft
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, "Journal entry saved as draft successfully."))
                self.journal_entry_saved.emit(saved_je.id)
                QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), Q_ARG(str, f"Failed to save journal entry:\n{', '.join(result.errors)}"))

    def open(self) -> int: 
        if not self.journal_entry_id and not self.view_only_mode : # Reset for new entry only
            self.entry_date_edit.setDate(QDate.currentDate())
            self.journal_type_combo.setCurrentText(JournalTypeEnum.GENERAL.value)
            self.description_edit.clear()
            self.reference_edit.clear()
            self.lines_table.setRowCount(0)
            self._add_new_line()
            self._add_new_line()
            self._calculate_totals()
            self.save_draft_button.setVisible(True); self.save_draft_button.setEnabled(True)
            self.save_post_button.setVisible(True); self.save_post_button.setEnabled(True)
            self.save_post_button.setText("Save & Post")
            self.lines_table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
            for i in range(self.layout().itemAt(0).layout().rowCount()): # Re-enable header form fields
                widget = self.layout().itemAt(0).layout().itemAt(i, QFormLayout.FieldRole).widget()
                if isinstance(widget, (QLineEdit, QDateEdit)): widget.setReadOnly(False)
                elif isinstance(widget, QComboBox): widget.setEnabled(True)
            self.add_line_button.setEnabled(True); self.remove_line_button.setEnabled(True)

        return super().open()
```

**Validation for `app/ui/accounting/journal_entry_dialog.py`:**
*   **Constructor**: Added `view_only` parameter. `loaded_journal_entry_orm` to store the ORM object after loading, and `existing_journal_entry_data_dict` to store the JSON-parsed dictionary for easier re-population of combos if caches are updated.
*   **`_get_window_title()`**: Sets title based on mode.
*   **`_init_ui()`**: Minor UI adjustments (button icons, table column widths). Changed "Cancel" button to "Close" if `view_only`.
*   **`_load_initial_combo_data()`**: Now calls `_update_combos_in_all_lines_slot()` to ensure any pre-existing lines (from `_load_existing_journal_entry`) also get their combos populated/re-populated if cache data arrives after lines are initially added.
*   **`_load_existing_journal_entry()`**: Fetches ORM object via `manager.get_journal_entry_for_dialog()`, serializes it, and passes JSON to `_populate_dialog_from_data_slot()`.
*   **`_serialize_je_for_ui()`**: Converts ORM to dict then JSON string using `json_converter`.
*   **`_populate_dialog_from_data_slot()`**:
    *   Parses JSON using `json_date_hook`.
    *   Stores parsed dict in `self.existing_journal_entry_data_dict`.
    *   Handles read-only state for `view_only_mode` or if `is_posted` is true. Makes form fields read-only/disabled and hides save buttons. Also makes line delete buttons invisible.
*   **`_populate_combos_for_row()`**: Refined to handle inactive/unknown accounts by checking `self.loaded_journal_entry_orm` if an account ID from loaded data isn't in the active cache. Tax code combo correctly uses empty string as data for "None".
*   **`_add_new_line()`**:
    *   `QDoubleSpinBox` has `setGroupSeparatorShown(True)` and `NoButtons`.
    *   Connects `valueChanged` of amount spinboxes and `currentIndexChanged` of tax combobox to a new slot `_calculate_totals_and_tax_for_row_slot` which then calls `_chain_recalculate_tax_and_totals`. This ensures tax is recalculated for the current line *before* overall totals are updated.
*   **`_remove_specific_line()`**: Prevents removal if in view-only/posted mode. Allows removing down to zero lines (validation for min lines is on save).
*   **`_recalculate_tax_for_line()`**: Added `try-except-finally` to ensure `_calculate_totals()` is always called.
*   **`_collect_data()`**:
    *   More robust fetching of values from cell widgets.
    *   Includes a stricter balance check (`abs(total_debits - total_credits) > Decimal("0.01")`).
    *   Correctly gets `source_type` and `source_id` from `loaded_journal_entry_orm` or `existing_journal_entry_data_dict` if editing.
*   **`_perform_save()`**:
    *   Correctly calls `manager.update_journal_entry(self.journal_entry_id, ...)` if `self.journal_entry_id` and `self.loaded_journal_entry_orm` exist.
    *   Emits `self.journal_entry_saved.emit(saved_je.id)` on successful save (draft or posted).
*   **`open()`**: Refined reset logic for new entries, ensuring all relevant UI elements are re-enabled/reset.

This dialog is now much more robust and should interact correctly with the backend manager.

---
Next, `app/ui/accounting/journal_entries_widget.py`.

```python
# app/ui/accounting/journal_entries_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QDateEdit, QComboBox, QInputDialog, QLineEdit # Added QLineEdit for filter
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QDate
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING
import json
from datetime import date as python_date 
from decimal import Decimal

from app.ui.accounting.journal_entry_dialog import JournalEntryDialog
from app.ui.accounting.journal_entry_table_model import JournalEntryTableModel
from app.common.enums import JournalTypeEnum 
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import JournalEntryData 
from app.models.accounting.journal_entry import JournalEntry 
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result # For type hinting

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class JournalEntriesWidget(QWidget):
    def __init__(self, app_core: "ApplicationCore", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._init_ui()
        # Initial load is triggered after UI setup and Apply Filter button connection
        QTimer.singleShot(0, lambda: self.apply_filter_button.click())


    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        # Filter Layout
        filter_group_layout = QHBoxLayout()
        
        filter_layout_form = QFormLayout()
        filter_layout_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.start_date_filter_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_filter_edit.setCalendarPopup(True)
        self.start_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        
        self.end_date_filter_edit = QDateEdit(QDate.currentDate())
        self.end_date_filter_edit.setCalendarPopup(True)
        self.end_date_filter_edit.setDisplayFormat("dd/MM/yyyy")

        self.entry_no_filter_edit = QLineEdit()
        self.entry_no_filter_edit.setPlaceholderText("Filter by Entry No.")
        
        self.description_filter_edit = QLineEdit()
        self.description_filter_edit.setPlaceholderText("Filter by Description")

        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["All", "Draft", "Posted"])
        
        filter_layout_form.addRow("From Date:", self.start_date_filter_edit)
        filter_layout_form.addRow("To Date:", self.end_date_filter_edit)
        filter_layout_form.addRow("Entry No.:", self.entry_no_filter_edit)
        filter_layout_form.addRow("Description:", self.description_filter_edit)
        filter_layout_form.addRow("Status:", self.status_filter_combo)

        filter_group_layout.addLayout(filter_layout_form)

        filter_button_layout = QVBoxLayout()
        self.apply_filter_button = QPushButton(QIcon.fromTheme("edit-find"), "Apply Filter")
        self.apply_filter_button.clicked.connect(lambda: schedule_task_from_qt(self._load_entries()))
        self.clear_filter_button = QPushButton(QIcon.fromTheme("edit-clear"), "Clear Filters")
        self.clear_filter_button.clicked.connect(self._clear_filters_and_load)
        filter_button_layout.addWidget(self.apply_filter_button)
        filter_button_layout.addWidget(self.clear_filter_button)
        filter_button_layout.addStretch()
        filter_group_layout.addLayout(filter_button_layout)
        filter_group_layout.addStretch(1)


        self.main_layout.addLayout(filter_group_layout)

        self.entries_table = QTableView()
        self.entries_table.setAlternatingRowColors(True)
        self.entries_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.entries_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.entries_table.horizontalHeader().setStretchLastSection(True)
        self.entries_table.doubleClicked.connect(self.on_view_entry_double_click) 
        self.entries_table.setSortingEnabled(True) # Enable column sorting

        self.table_model = JournalEntryTableModel()
        self.entries_table.setModel(self.table_model)
        # Hide ID column by default, but it's available for data retrieval
        self.entries_table.setColumnHidden(0, True) 
        
        self._create_toolbar() 
        self.main_layout.addWidget(self.toolbar) 
        self.main_layout.addWidget(self.entries_table) 
        self.setLayout(self.main_layout)

    def _clear_filters_and_load(self):
        self.start_date_filter_edit.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_filter_edit.setDate(QDate.currentDate())
        self.entry_no_filter_edit.clear()
        self.description_filter_edit.clear()
        self.status_filter_combo.setCurrentText("All")
        schedule_task_from_qt(self._load_entries())

    def _create_toolbar(self):
        # ... (toolbar creation logic from previous step, remains largely the same)
        from PySide6.QtCore import QSize
        self.toolbar = QToolBar("Journal Entries Toolbar")
        self.toolbar.setObjectName("JournalEntriesToolbar")
        self.toolbar.setIconSize(QSize(16, 16)) 

        icon_path_prefix = "resources/icons/" 
        try: import app.resources_rc; icon_path_prefix = ":/icons/" # type: ignore
        except ImportError: pass 

        self.new_entry_action = QAction(QIcon(icon_path_prefix + "add.svg"), "New Entry", self) 
        self.new_entry_action.triggered.connect(self.on_new_entry)
        self.toolbar.addAction(self.new_entry_action)

        self.edit_entry_action = QAction(QIcon(icon_path_prefix + "edit.svg"), "Edit Draft", self)
        self.edit_entry_action.triggered.connect(self.on_edit_entry)
        self.toolbar.addAction(self.edit_entry_action)
        
        self.view_entry_action = QAction(QIcon(icon_path_prefix + "view.svg"), "View Entry", self) 
        self.view_entry_action.triggered.connect(self.on_view_entry_toolbar) # Distinct slot for toolbar action
        self.toolbar.addAction(self.view_entry_action)

        self.toolbar.addSeparator()

        self.post_entry_action = QAction(QIcon(icon_path_prefix + "post.svg"), "Post Selected", self) 
        self.post_entry_action.triggered.connect(self.on_post_entry)
        self.toolbar.addAction(self.post_entry_action)
        
        self.reverse_entry_action = QAction(QIcon(icon_path_prefix + "reverse.svg"), "Reverse Selected", self) 
        self.reverse_entry_action.triggered.connect(self.on_reverse_entry)
        self.toolbar.addAction(self.reverse_entry_action)

        self.toolbar.addSeparator()
        # Refresh action now calls _load_entries directly, which uses current filter values
        self.refresh_action = QAction(QIcon(icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_entries()))
        self.toolbar.addAction(self.refresh_action)

        if self.entries_table.selectionModel():
            self.entries_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states() 

    @Slot()
    def _update_action_states(self):
        # ... (Logic from previous step is fine)
        selected_indexes = self.entries_table.selectionModel().selectedRows()
        has_selection = bool(selected_indexes)
        is_draft = False
        is_posted = False
        single_selection = len(selected_indexes) == 1

        if single_selection: # Actions requiring single selection
            first_selected_row = selected_indexes[0].row()
            status = self.table_model.get_journal_entry_status_at_row(first_selected_row)
            is_draft = status == "Draft" 
            is_posted = status == "Posted"
        
        can_post_any_draft = False
        if has_selection: # Post can apply to multiple drafts
            for index in selected_indexes:
                if self.table_model.get_journal_entry_status_at_row(index.row()) == "Draft":
                    can_post_any_draft = True
                    break
        
        self.edit_entry_action.setEnabled(single_selection and is_draft)
        self.view_entry_action.setEnabled(single_selection)
        self.post_entry_action.setEnabled(can_post_any_draft) 
        self.reverse_entry_action.setEnabled(single_selection and is_posted)


    async def _load_entries(self):
        if not self.app_core.journal_entry_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Journal Entry Manager not available."))
            return
        try:
            start_date = self.start_date_filter_edit.date().toPython()
            end_date = self.end_date_filter_edit.date().toPython()
            status_text = self.status_filter_combo.currentText()
            status_filter = status_text if status_text != "All" else None
            entry_no_filter_text = self.entry_no_filter_edit.text().strip()
            description_filter_text = self.description_filter_edit.text().strip()


            filters = {
                "start_date": start_date, "end_date": end_date, 
                "status": status_filter,
                "entry_no": entry_no_filter_text if entry_no_filter_text else None,
                "description": description_filter_text if description_filter_text else None
            }
            
            result: Result[List[Dict[str, Any]]] = await self.app_core.journal_entry_manager.get_journal_entries_for_listing(filters=filters)
            
            if result.is_success:
                entries_data_for_table = result.value if result.value is not None else []
                json_data = json.dumps(entries_data_for_table, default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection,
                                         Q_ARG(str, json_data))
            else:
                error_msg = f"Failed to load journal entries: {', '.join(result.errors)}"
                self.app_core.logger.error(error_msg) # type: ignore
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))
                
        except Exception as e:
            error_msg = f"Unexpected error loading journal entries: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True) # type: ignore
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            entries_data: List[Dict[str, Any]] = json.loads(json_data_str, object_hook=json_date_hook)
            self.table_model.update_data(entries_data)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse journal entry data: {e}")
        self._update_action_states() # Update actions after data changes


    @Slot()
    def on_new_entry(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to create a journal entry.")
            return
        # Pass self.app_core.current_user.id
        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.journal_entry_saved.connect(lambda _id: schedule_task_from_qt(self._load_entries()))
        dialog.exec() 

    def _get_selected_entry_id_and_status(self, require_single_selection: bool = True) -> tuple[Optional[int], Optional[str]]:
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows:
            if require_single_selection: QMessageBox.information(self, "Selection", "Please select a journal entry.")
            return None, None
        if require_single_selection and len(selected_rows) > 1:
            QMessageBox.information(self, "Selection", "Please select only a single journal entry for this action.")
            return None, None
        
        row = selected_rows[0].row() 
        # Use model's helper to get ID from UserRole, which is more reliable
        entry_id = self.table_model.get_journal_entry_id_at_row(row)
        entry_status = self.table_model.get_journal_entry_status_at_row(row)
        return entry_id, entry_status

    @Slot()
    def on_edit_entry(self):
        entry_id, entry_status = self._get_selected_entry_id_and_status()
        if entry_id is None: return

        if entry_status != "Draft":
            QMessageBox.warning(self, "Edit Error", "Only draft entries can be edited.")
            return
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit.")
            return

        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, journal_entry_id=entry_id, parent=self)
        dialog.journal_entry_saved.connect(lambda _id: schedule_task_from_qt(self._load_entries()))
        dialog.exec()

    @Slot(QModelIndex) 
    def on_view_entry_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        entry_id = self.table_model.get_journal_entry_id_at_row(index.row())
        if entry_id is None: return
        self._show_view_entry_dialog(entry_id)

    @Slot()
    def on_view_entry_toolbar(self): 
        entry_id, _ = self._get_selected_entry_id_and_status()
        if entry_id is None: return
        self._show_view_entry_dialog(entry_id)

    def _show_view_entry_dialog(self, entry_id: int):
        if not self.app_core.current_user: 
             QMessageBox.warning(self, "Auth Error", "Please log in.")
             return
        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, journal_entry_id=entry_id, view_only=True, parent=self)
        dialog.exec()


    @Slot()
    def on_post_entry(self):
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Selection", "Please select one or more draft journal entries to post.")
            return
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to post entries.")
            return

        entries_to_post_ids = []
        for index in selected_rows:
            entry_id = self.table_model.get_journal_entry_id_at_row(index.row())
            entry_status = self.table_model.get_journal_entry_status_at_row(index.row())
            if entry_id and entry_status == "Draft":
                entries_to_post_ids.append(entry_id)
        
        if not entries_to_post_ids:
            QMessageBox.information(self, "Selection", "No draft entries selected for posting.")
            return

        schedule_task_from_qt(self._perform_post_entries(entries_to_post_ids, self.app_core.current_user.id))

    async def _perform_post_entries(self, entry_ids: List[int], user_id: int):
        # ... (Logic from previous step is fine, ensure manager is checked)
        if not self.app_core.journal_entry_manager: 
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Journal Entry Manager not available."))
            return

        success_count = 0; errors = []
        for entry_id_to_post in entry_ids:
            result: Result[JournalEntry] = await self.app_core.journal_entry_manager.post_journal_entry(entry_id_to_post, user_id)
            if result.is_success: success_count += 1
            else:
                je_no_str = f"ID {entry_id_to_post}" 
                # Try to get entry_no for better error message
                try:
                    temp_je = await self.app_core.journal_entry_manager.get_journal_entry_for_dialog(entry_id_to_post)
                    if temp_je: je_no_str = temp_je.entry_no
                except Exception: pass
                errors.append(f"Entry {je_no_str}: {', '.join(result.errors)}")
        
        message = f"{success_count} of {len(entry_ids)} entries posted."
        if errors: message += "\n\nErrors:\n" + "\n".join(errors)
        
        msg_box_method = QMessageBox.information if not errors and success_count > 0 else QMessageBox.warning
        title = "Posting Complete" if not errors and success_count > 0 else ("Posting Failed" if success_count == 0 else "Posting Partially Failed")
        
        QMetaObject.invokeMethod(msg_box_method, "", Qt.ConnectionType.QueuedConnection,
            Q_ARG(QWidget, self), Q_ARG(str, title), Q_ARG(str, message))
        
        if success_count > 0: schedule_task_from_qt(self._load_entries())


    @Slot()
    def on_reverse_entry(self):
        entry_id, entry_status = self._get_selected_entry_id_and_status()
        if entry_id is None or entry_status != "Posted":
            QMessageBox.warning(self, "Reverse Error", "Only single, posted entries can be reversed.")
            return
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to reverse entries.")
            return
        
        reply = QMessageBox.question(self, "Confirm Reversal", 
                                     f"Are you sure you want to reverse journal entry ID {entry_id}?\nA new counter-entry will be created as a DRAFT.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return

        reversal_date_str, ok = QInputDialog.getText(self, "Reversal Date", 
                                                     "Enter reversal date (YYYY-MM-DD):", 
                                                     QLineEdit.EchoMode.Normal, python_date.today().isoformat())
        if ok and reversal_date_str:
            try:
                parsed_reversal_date = python_date.fromisoformat(reversal_date_str)
                reversal_desc_str, ok_desc = QInputDialog.getText(self, "Reversal Description", 
                                                     "Enter description for reversal entry:", 
                                                     QLineEdit.EchoMode.Normal, f"Reversal of JE ID {entry_id}")
                if ok_desc:
                    schedule_task_from_qt(self._perform_reverse_entry(entry_id, parsed_reversal_date, reversal_desc_str, self.app_core.current_user.id))
                else:
                    QMessageBox.information(self, "Cancelled", "Reversal description input cancelled.")
            except ValueError:
                QMessageBox.warning(self, "Invalid Date", "Reversal date format is invalid. Please use YYYY-MM-DD.")
        else:
            QMessageBox.information(self, "Cancelled", "Reversal date input cancelled.")


    async def _perform_reverse_entry(self, entry_id: int, reversal_date: python_date, description: str, user_id: int):
        # ... (Logic from previous step, ensure manager is checked)
        if not self.app_core.journal_entry_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Journal Entry Manager not available."))
            return

        result: Result[JournalEntry] = await self.app_core.journal_entry_manager.reverse_journal_entry(entry_id, reversal_date, description, user_id)

        if result.is_success and result.value:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, f"Journal entry ID {entry_id} reversed. New reversal entry: {result.value.entry_no} (Draft)."))
            schedule_task_from_qt(self._load_entries())
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Reversal Error"), Q_ARG(str, f"Failed to reverse journal entry:\n{', '.join(result.errors)}"))
```

---
**Validation for `app/ui/accounting/journal_entries_widget.py`:**
*   **Filter UI**: Added `QLineEdit` for Entry No. and Description filters. Grouped filter controls into a `QFormLayout` within a `QHBoxLayout` for better structure. Added "Clear Filters" button.
*   **`_load_entries`**: Now passes `entry_no` and `description` filter text to `get_journal_entries_for_listing`.
*   **`_clear_filters_and_load`**: Resets filter UI elements and reloads entries.
*   **Toolbar Icons**: Smaller icon size for a more compact toolbar. Ensured fallback path for icons.
*   **`_update_action_states`**: Refined logic for enabling/disabling actions based on single vs. multiple selections and status.
*   **`on_view_entry_double_click` and `on_view_entry_toolbar`**: Consolidated view logic into `_show_view_entry_dialog`.
*   **`on_reverse_entry`**: Added `QInputDialog` for reversal description.
*   **`_perform_post_entries`**: Improved error message to include JE number if possible.
*   **Sorting**: Enabled `QTableView.setSortingEnabled(True)`. The `JournalEntryTableModel` would need to implement `sort()` if client-side sorting is desired, or sorting would be handled by the database query in `JournalService.get_all_summary`. For now, client-side sorting is not implemented in the model, so clicking headers will only sort by the display text if the underlying model supports it or if a proxy model is used.
*   **ID Column**: The "ID" column is now hidden by default in `_init_ui` (`self.entries_table.setColumnHidden(0, True)`), as it's mainly for internal use by the widget to get IDs, not for user display.

These UI files should now be well-integrated with the backend. The next steps involve thorough testing as per Phase 4 of the plan. No new files need to be created in this step. The focus was on refining the existing UI files to fully utilize the backend logic.

---
https://drive.google.com/file/d/1-lQNYxO1i_5DT1QqEfMtYybal2mzhUAc/view?usp=sharing, https://drive.google.com/file/d/16gFjJpsNDcAcE0E4TkhL40Ka12eBq0i_/view?usp=sharing, https://drive.google.com/file/d/1Io9vpSP3ST1lRbemAqr0SnAfSLSCmzqI/view?usp=sharing, https://drive.google.com/file/d/1JIsAZQEejE1qm-fGe1L-QpLfOWBWWW-9/view?usp=sharing, https://drive.google.com/file/d/1Oa85u5sAFd9OgiARagGmGnqJlSw0SV8u/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221SQTCjVSg9-JUmuGgq5bhvaOTbHhi2gWe%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1TArp9rSH4Oz6EVarWHaYNBHbdJOkuU1Z/view?usp=sharing, https://drive.google.com/file/d/1Z2KhH8Sd1yHpRUoz6TOU1jLev6icDwkd/view?usp=sharing, https://drive.google.com/file/d/1e9CQtKfd6E1LhSmXliLFwXUFxeGoR35E/view?usp=sharing, https://drive.google.com/file/d/1e9OAGmsj8Z2SAD1oNT2pAwmnm3zBnlGi/view?usp=sharing, https://drive.google.com/file/d/1km1x5NEIFLkBRhpyq7OS0PsXiMoXz1VY/view?usp=sharing, https://drive.google.com/file/d/1rnl0de93Aokl_FDNzUQTEu_C4p5LECWJ/view?usp=sharing, https://drive.google.com/file/d/1s6CXBUuwyh945SzNa2Ti4PUYJpTVTXdt/view?usp=sharing

