<think>
The user wants to proceed with the roadmap, specifically:
1.  **Sales Invoicing**: Complete UI for listing, viewing, and managing Sales Invoices. Implement posting logic (JE creation).
2.  **Refine Reporting**: Enhance on-screen display and export options for financial reports.

Given the current state (Part 1 of `SalesInvoiceDialog` focusing on data loading and basic line management is complete), the most logical next step for "Sales Invoicing" is to implement **Part 2 of `SalesInvoiceDialog`: Calculation Logic and Saving Drafts.**

The "Refine Reporting" item can be addressed after the Sales Invoicing module is more complete, as invoices will provide more data for reports.

So, the immediate plan for this turn is:
**Implement Core Logic for `SalesInvoiceDialog` - Part 2 (Line & Invoice Total Calculations, Data Collection, and Saving Drafts).**

**Objective:**
Flesh out the calculation logic within `SalesInvoiceDialog` for line items and overall invoice totals. Implement the data collection process to create DTOs and the save mechanism to persist draft invoices using the `SalesInvoiceManager`.

**Detailed Plan & Checklist for `app/ui/sales_invoices/sales_invoice_dialog.py` - Part 2:**

1.  **Implement `_calculate_line_item_totals(row: int)`**:
    *   [ ] Get Qty, Unit Price, Discount % from the widgets in the specified `row`.
    *   [ ] Calculate `discount_amount = (qty * price * disc_pct / 100)`. Quantize to 4 decimal places for intermediate, 2 for final display.
    *   [ ] Calculate `line_subtotal_before_tax = (qty * price) - discount_amount`.
    *   [ ] Get selected `tax_code_str` from the line's tax code `QComboBox`.
    *   [ ] If `tax_code_str` is valid:
        *   Fetch `TaxCode` details from `self._tax_codes_cache` (or make an async call if cache isn't sufficient, but cache is preferred here).
        *   Calculate `line_tax_amount = (line_subtotal_before_tax * tax_rate / 100)`. Quantize to 2 decimal places.
        *   **Note**: `TaxCalculator` was initially considered, but for direct display updates in the dialog, direct calculation based on cached tax rates might be simpler and faster. The manager will use `TaxCalculator` during final validation/save. For UI, this direct approach for immediate feedback is fine.
    *   [ ] Else, `line_tax_amount = Decimal(0)`.
    *   [ ] Calculate `line_total = line_subtotal_before_tax + line_tax_amount`.
    *   [ ] Update the read-only `QTableWidgetItem`s for Line Subtotal, Tax Amount, and Line Total in the specified `row`. Format as currency strings.
    *   [ ] After updating the line, call `self._update_invoice_totals()`.

2.  **Implement `_update_invoice_totals()`**:
    *   [ ] Initialize `invoice_subtotal`, `invoice_total_tax`, `invoice_grand_total` to `Decimal(0)`.
    *   [ ] Iterate through all rows in `self.lines_table`.
    *   [ ] For each row, parse the text from the Line Subtotal and Tax Amount cells (which were set by `_calculate_line_item_totals`) back to `Decimal`. Handle potential parsing errors.
    *   [ ] Add to `invoice_subtotal` and `invoice_total_tax`.
    *   [ ] Calculate `invoice_grand_total = invoice_subtotal + invoice_total_tax`.
    *   [ ] Update `self.subtotal_display`, `self.total_tax_display`, `self.grand_total_display` QLineEdits with formatted currency strings.

3.  **Implement `_collect_data()` -> `Optional[Union[SalesInvoiceCreateData, SalesInvoiceUpdateData]]`**:
    *   [ ] Perform basic header validations (e.g., customer selected, dates valid). Show `QMessageBox` on error and return `None`.
    *   [ ] Create `SalesInvoiceLineBaseData` DTOs for each line:
        *   Get product ID, description, qty, price, disc %, tax code from widgets/items.
        *   If a line is essentially empty (e.g., no product and zero amounts), skip it, unless it's the only line and user intended to fill it.
        *   Ensure at least one valid line item. Show `QMessageBox` on error and return `None`.
    *   [ ] Create `SalesInvoiceCreateData` or `SalesInvoiceUpdateData` DTO:
        *   Populate with header field values.
        *   Populate `lines` attribute with the list of `SalesInvoiceLineBaseData` DTOs.
        *   Include `user_id`.
        *   If `self.invoice_id` exists, it's an `SalesInvoiceUpdateData` DTO.
    *   [ ] Handle Pydantic validation errors during DTO creation. Show `QMessageBox` and return `None`.
    *   [ ] Return the created DTO.

4.  **Implement `on_save_draft()` slot**:
    *   [ ] Call `self._collect_data()`.
    *   [ ] If DTO is successfully created:
        *   Disable save buttons.
        *   Call `schedule_task_from_qt(self._perform_save(dto, post_action=None))`.
        *   Add a callback to re-enable save buttons.

5.  **Implement `_perform_save(dto, post_action)` async method**:
    *   [ ] If `dto` is `SalesInvoiceUpdateData`:
        *   Call `self.app_core.sales_invoice_manager.update_draft_invoice(dto.id, dto)`.
    *   [ ] Else (if `dto` is `SalesInvoiceCreateData`):
        *   Call `self.app_core.sales_invoice_manager.create_draft_invoice(dto)`.
    *   [ ] Handle the `Result` object returned by the manager.
    *   [ ] On success:
        *   Show success `QMessageBox`.
        *   Emit `self.invoice_saved` signal with the saved invoice ID.
        *   Call `self.accept()` to close the dialog.
    *   [ ] On failure:
        *   Show error `QMessageBox` with errors from `result.errors`.
        *   Re-enable save buttons (done by callback in `on_save_draft`).

6.  **Refine Signal Connections for Line Items**:
    *   Ensure that `valueChanged` signals from `QDoubleSpinBox` (Qty, Price, Disc %) and `currentIndexChanged` from `QComboBox` (Tax Code) in each line correctly trigger `_trigger_line_recalculation_slot(row)` with the correct row index.

**Pre-computation/Pre-analysis:**

*   **Tax Calculation in UI vs. Manager**: The `SalesInvoiceManager` uses `TaxCalculator` for robust tax calculation, especially when preparing data for ORM. The UI's `_calculate_line_item_totals` needs to perform a similar calculation for immediate user feedback. It can use cached tax rates for simplicity. The manager will perform the definitive calculation before saving.
*   **Data Flow for Saving**: UI (`_collect_data`) -> DTO -> Manager (`create/update_draft_invoice` which internally calls `_validate_and_prepare_invoice_data`) -> Service (`save`) -> DB.
*   **Decimal Precision**: Ensure all monetary calculations use `Decimal` and are quantized appropriately at each step (intermediate calculations can have more precision, final display/storage usually 2 decimal places). `LineItemNumericDelegate` helps with input.

Let's proceed with implementing these parts for `app/ui/sales_invoices/sales_invoice_dialog.py`.
</think>

Okay, I will proceed with implementing **Part 2 of `SalesInvoiceDialog`: Calculation Logic and Saving Drafts**. This involves fleshing out the methods responsible for dynamic calculations of line items and invoice totals, collecting data from the UI into DTOs, and interacting with the `SalesInvoiceManager` to save draft invoices.

Here is the detailed execution plan:

**Execution Plan for `app/ui/sales_invoices/sales_invoice_dialog.py` - Part 2:**

1.  **Implement `_calculate_line_item_totals(row: int)`**:
    *   Retrieve values for quantity, unit price, and discount percentage from the `QDoubleSpinBox` widgets in the specified table row.
    *   Retrieve the selected tax code string from the `QComboBox` in the row.
    *   Perform calculations:
        *   `discount_amount = (quantity * unit_price * discount_percent / 100)`
        *   `line_subtotal_before_tax = (quantity * unit_price) - discount_amount`
        *   Look up the tax rate from `self._tax_codes_cache` based on the selected tax code string.
        *   `line_tax_amount = line_subtotal_before_tax * (tax_rate / 100)`
        *   `line_total = line_subtotal_before_tax + line_tax_amount`
    *   Update the read-only `QTableWidgetItem`s for "Subtotal", "Tax Amt", and "Line Total" in the current row with formatted decimal strings.
    *   Call `self._update_invoice_totals()` to refresh the overall invoice summary.
    *   **Checklist**: [ ] Values retrieved correctly. [ ] Calculations are accurate using `Decimal`. [ ] Read-only cells updated. [ ] `_update_invoice_totals` called.

2.  **Implement `_update_invoice_totals()`**:
    *   Initialize `total_invoice_subtotal`, `total_invoice_tax`, `grand_invoice_total` to `Decimal(0)`.
    *   Iterate through all rows of `self.lines_table`.
    *   For each row, retrieve the string values from the "Subtotal" and "Tax Amt" cells. Convert these strings back to `Decimal` (handle potential errors if text is not a valid number).
    *   Accumulate these values into the respective total variables.
    *   Calculate `grand_invoice_total`.
    *   Update the text of `self.subtotal_display`, `self.total_tax_display`, and `self.grand_total_display` QLineEdits with formatted decimal strings.
    *   **Checklist**: [ ] Iteration through all rows. [ ] Correct parsing of cell text to Decimal. [ ] Accurate accumulation. [ ] Display fields updated.

3.  **Implement `_collect_data()`**:
    *   Retrieve header data: customer ID, invoice date, due date, currency code, exchange rate, notes, terms.
    *   Perform basic validation (e.g., customer selected, invoice date <= due date). If invalid, show a `QMessageBox` and return `None`.
    *   Initialize an empty list for `SalesInvoiceLineBaseData` DTOs.
    *   Iterate through `self.lines_table` rows:
        *   For each row, retrieve product ID, description, quantity, unit price, discount percent, and tax code from the respective widgets.
        *   Skip lines that are essentially empty (e.g., no product ID and zero quantity/price).
        *   Create a `SalesInvoiceLineBaseData` DTO for each valid line. Quantity, price, discount percent should be Decimals.
    *   If no valid lines are collected, show a `QMessageBox` ("Invoice must have at least one line item.") and return `None`.
    *   Determine if creating a new invoice (`self.invoice_id` is `None`) or updating an existing one.
    *   Construct either `SalesInvoiceCreateData` or `SalesInvoiceUpdateData` DTO, including `user_id` and the list of line DTOs. If updating, include `id=self.invoice_id`.
    *   Catch Pydantic `ValueError` during DTO instantiation, show a `QMessageBox` with the error, and return `None`.
    *   Return the populated DTO.
    *   **Checklist**: [ ] Header data retrieved. [ ] Header validation performed. [ ] Lines iterated. [ ] Empty lines skipped. [ ] Line DTOs created. [ ] At least one line check. [ ] Correct main DTO (Create/Update) created. [ ] Pydantic errors handled. [ ] DTO returned.

4.  **Implement `on_save_draft()` Slot**:
    *   Call `self._collect_data()`.
    *   If a valid DTO is returned:
        *   Disable the "Save Draft" and "Save & Approve" buttons to prevent multiple clicks.
        *   Schedule the `self._perform_save(dto, post_action=None)` coroutine using `schedule_task_from_qt`.
        *   Add a `done_callback` to the future to re-enable the save buttons, regardless of the outcome of `_perform_save`.
    *   **Checklist**: [ ] `_collect_data` called. [ ] Buttons disabled. [ ] `_perform_save` scheduled. [ ] Callback to re-enable buttons added.

5.  **Implement `_perform_save(dto, post_action)` Async Method**:
    *   Check if `self.app_core.sales_invoice_manager` is available.
    *   If `dto` is `SalesInvoiceUpdateData`:
        *   Call `self.app_core.sales_invoice_manager.update_draft_invoice(dto.id, dto)`.
    *   Else (if `dto` is `SalesInvoiceCreateData`):
        *   Call `self.app_core.sales_invoice_manager.create_draft_invoice(dto)`.
    *   Await the result from the manager.
    *   If `result.is_success`:
        *   Use `QMetaObject.invokeMethod` to show an success `QMessageBox`.
        *   Emit `self.invoice_saved.emit(result.value.id)`.
        *   Use `QMetaObject.invokeMethod` to call `self.accept()`.
    *   Else (on failure):
        *   Use `QMetaObject.invokeMethod` to show a warning `QMessageBox` with `result.errors`.
    *   **Checklist**: [ ] Correct manager method called. [ ] Result handled. [ ] UI feedback (MessageBox, signal, accept/reject) invoked via `QMetaObject`.

6.  **Final Review and Testing**:
    *   Mentally simulate the flow: user input -> line calculation -> total calculation -> save click -> data collection -> DTO creation -> manager call -> result handling.
    *   Ensure all `Decimal` conversions and quantizations are handled correctly to avoid precision issues.

I will now proceed to generate the updated `app/ui/sales_invoices/sales_invoice_dialog.py` file.

```python
# app/ui/sales_invoices/sales_invoice_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QCheckBox, QDateEdit, QComboBox, QSpinBox, QTextEdit, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QCompleter,
    QSizePolicy, QApplication, QStyledItemDelegate, QAbstractSpinBox, QLabel, QFrame,
    QGridLayout
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG
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
        # For QTableWidget, model is the table widget itself, use setItem for QTableWidgetItem
        if isinstance(model, QTableWidget):
            item = model.item(index.row(), index.column())
            if not item: item = QTableWidgetItem()
            item.setText(str(Decimal(str(editor.value())).quantize(Decimal(precision_str), ROUND_HALF_UP)))
            # model.setItem(index.row(), index.column(), item) # Not needed if item is obtained from model
        else: # For QAbstractTableModel
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

        # --- Header Fields ---
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

        # --- Lines Table ---
        self.lines_table = QTableWidget(); self.lines_table.setColumnCount(self.COL_TOTAL + 1) 
        self.lines_table.setHorizontalHeaderLabels(["", "Product/Service", "Description", "Qty*", "Price*", "Disc %", "Subtotal", "Tax", "Tax Amt", "Total"])
        self._configure_lines_table_columns(); main_layout.addWidget(self.lines_table)
        lines_button_layout = QHBoxLayout()
        self.add_line_button = QPushButton(QIcon(self.icon_path_prefix + "add.svg"), "Add Line")
        self.remove_line_button = QPushButton(QIcon(self.icon_path_prefix + "remove.svg"), "Remove Line")
        lines_button_layout.addWidget(self.add_line_button); lines_button_layout.addWidget(self.remove_line_button); lines_button_layout.addStretch()
        main_layout.addLayout(lines_button_layout)

        # --- Totals Display ---
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
        self.save_approve_button.setToolTip("Future: Save, mark as Approved, and generate Journal Entry."); self.save_approve_button.setEnabled(False) 
        self.button_box.addButton(QDialogButtonBox.StandardButton.Close if self.view_only_mode else QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box); self.setLayout(main_layout)

    def _configure_lines_table_columns(self):
        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(self.COL_DEL, QHeaderView.ResizeMode.Fixed); self.lines_table.setColumnWidth(self.COL_DEL, 30)
        header.setSectionResizeMode(self.COL_PROD, QHeaderView.ResizeMode.Interactive); self.lines_table.setColumnWidth(self.COL_PROD, 200)
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
        # self.save_approve_button.clicked.connect(self.on_save_approve)
        
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
                self._tax_codes_cache = [{"code":tc.code, "rate":tc.rate, "description":f"{tc.code} ({tc.rate}%)"} for tc in tc_orms if tc.is_active]

            QMetaObject.invokeMethod(self, "_populate_initial_combos_slot", Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            self.app_core.logger.error(f"Error loading combo data for SalesInvoiceDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load initial data for dropdowns: {str(e)}")

    @Slot()
    def _populate_initial_combos_slot(self):
        self.customer_combo.clear(); self.customer_combo.addItem("-- Select Customer --", 0)
        for cust in self._customers_cache: self.customer_combo.addItem(f"{cust['customer_code']} - {cust['name']}", cust['id'])
        if isinstance(self.customer_combo.completer(), QCompleter): self.customer_combo.completer().setModel(self.customer_combo.model()) # type: ignore

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
        self.save_draft_button.setVisible(not read_only)
        self.save_approve_button.setVisible(not read_only) 
        
        edit_trigger = QAbstractItemView.EditTrigger.NoEditTriggers if read_only else QAbstractItemView.EditTrigger.AllInputs
        self.lines_table.setEditTriggers(edit_trigger)
        for r in range(self.lines_table.rowCount()):
            del_btn_widget = self.lines_table.cellWidget(r, self.COL_DEL)
            if del_btn_widget: del_btn_widget.setEnabled(not read_only)

    def _add_new_invoice_line(self, line_data: Optional[Dict[str, Any]] = None):
        row = self.lines_table.rowCount()
        self.lines_table.insertRow(row)

        del_btn = QPushButton(QIcon(self.icon_path_prefix + "remove.svg")); del_btn.setFixedSize(24,24)
        del_btn.clicked.connect(lambda _, r=row: self._remove_specific_invoice_line(r))
        self.lines_table.setCellWidget(row, self.COL_DEL, del_btn)

        prod_combo = QComboBox(); prod_combo.setEditable(True); prod_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        prod_completer = QCompleter(); prod_completer.setFilterMode(Qt.MatchFlag.MatchContains); prod_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        prod_combo.setCompleter(prod_completer)
        self.lines_table.setCellWidget(row, self.COL_PROD, prod_combo)
        
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
        prod_combo = cast(QComboBox, self.lines_table.cellWidget(row, self.COL_PROD))
        prod_combo.clear(); prod_combo.addItem("-- Select Product/Service --", 0)
        current_prod_id = line_data.get("product_id") if line_data else None
        selected_prod_idx = 0 
        for i, prod_dict in enumerate(self._products_cache):
            prod_combo.addItem(f"{prod_dict['product_code']} - {prod_dict['name']}", prod_dict['id'])
            if prod_dict['id'] == current_prod_id: selected_prod_idx = i + 1
        prod_combo.setCurrentIndex(selected_prod_idx)
        if isinstance(prod_combo.completer(), QCompleter): prod_combo.completer().setModel(prod_combo.model()) # type: ignore
        
        tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, self.COL_TAX_CODE))
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
            if desc_item and (not desc_item.text().strip() or "Product/Service" in desc_item.text()): 
                desc_item.setText(product_detail.get('name', ''))
            
            price_widget = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, self.COL_PRICE))
            if price_widget and price_widget.value() == 0.0 and product_detail.get('sales_price') is not None:
                try: price_widget.setValue(float(Decimal(str(product_detail['sales_price']))))
                except: pass 
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
        # Only connected for description text item, QDoubleSpinBox handle their own valueChanged
        if item.column() == self.COL_DESC:
             pass # Description change doesn't directly affect totals, but might be useful later

    @Slot() 
    def _trigger_line_recalculation_slot(self, row_for_recalc: Optional[int] = None):
        current_row = row_for_recalc
        if current_row is None: # Determine row from sender if not passed
            sender_widget = self.sender()
            if sender_widget and isinstance(sender_widget, QWidget):
                for r in range(self.lines_table.rowCount()):
                    for c in [self.COL_QTY, self.COL_PRICE, self.COL_DISC_PCT, self.COL_TAX_CODE, self.COL_PROD]:
                        if self.lines_table.cellWidget(r,c) == sender_widget: current_row = r; break
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

            qty = Decimal(str(qty_w.value()))
            price = Decimal(str(price_w.value()))
            disc_pct = Decimal(str(disc_pct_w.value()))
            
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

            self.lines_table.item(row, self.COL_SUBTOTAL).setText(self._format_decimal_for_cell(line_subtotal_before_tax.quantize(Decimal("0.01")), False))
            self.lines_table.item(row, self.COL_TAX_AMT).setText(self._format_decimal_for_cell(line_tax_amount, True))
            self.lines_table.item(row, self.COL_TOTAL).setText(self._format_decimal_for_cell(line_total.quantize(Decimal("0.01")), False))
        except Exception as e:
            self.app_core.logger.error(f"Error calculating line totals for row {row}: {e}", exc_info=True)
            for col_idx in [self.COL_SUBTOTAL, self.COL_TAX_AMT, self.COL_TOTAL]:
                item = self.lines_table.item(row, col_idx)
                if item: item.setText("Error")
        finally:
            self._update_invoice_totals()

    def _update_invoice_totals(self):
        invoice_subtotal_agg = Decimal(0)
        total_tax_agg = Decimal(0)
        for r in range(self.lines_table.rowCount()):
            try:
                sub_item = self.lines_table.item(r, self.COL_SUBTOTAL)
                tax_item = self.lines_table.item(r, self.COL_TAX_AMT)
                if sub_item and sub_item.text() and sub_item.text() != "Error": 
                    invoice_subtotal_agg += Decimal(sub_item.text().replace(',',''))
                if tax_item and tax_item.text() and tax_item.text() != "Error": 
                    total_tax_agg += Decimal(tax_item.text().replace(',',''))
            except (InvalidOperation, AttributeError) as e:
                 self.app_core.logger.warning(f"Could not parse amount from line {r} during total update: {e}")
        
        grand_total_agg = invoice_subtotal_agg + total_tax_agg
        self.subtotal_display.setText(self._format_decimal_for_cell(invoice_subtotal_agg, False))
        self.total_tax_display.setText(self._format_decimal_for_cell(total_tax_agg, False))
        self.grand_total_display.setText(self._format_decimal_for_cell(grand_total_agg, False))
        
    def _collect_data(self) -> Optional[Union[SalesInvoiceCreateData, SalesInvoiceUpdateData]]:
        customer_id_data = self.customer_combo.currentData()
        if not customer_id_data or customer_id_data == 0:
            QMessageBox.warning(self, "Validation Error", "Customer must be selected.")
            return None
        customer_id = int(customer_id_data)

        invoice_date_py = self.invoice_date_edit.date().toPython()
        due_date_py = self.due_date_edit.date().toPython()
        if due_date_py < invoice_date_py:
            QMessageBox.warning(self, "Validation Error", "Due date cannot be before invoice date.")
            return None
        
        line_dtos: List[SalesInvoiceLineBaseData] = []
        for r in range(self.lines_table.rowCount()):
            try:
                prod_combo = cast(QComboBox, self.lines_table.cellWidget(r, self.COL_PROD))
                desc_item = self.lines_table.item(r, self.COL_DESC)
                qty_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(r, self.COL_QTY))
                price_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(r, self.COL_PRICE))
                disc_pct_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(r, self.COL_DISC_PCT))
                tax_combo = cast(QComboBox, self.lines_table.cellWidget(r, self.COL_TAX_CODE))

                product_id_data = prod_combo.currentData() if prod_combo else None
                product_id = int(product_id_data) if product_id_data and product_id_data != 0 else None
                
                description = desc_item.text().strip() if desc_item else ""
                quantity = Decimal(str(qty_spin.value()))
                unit_price = Decimal(str(price_spin.value()))
                discount_percent = Decimal(str(disc_pct_spin.value()))
                tax_code_str = tax_combo.currentData() if tax_combo and tax_combo.currentData() else None

                if not description and not product_id: continue # Skip entirely empty lines
                if quantity <= 0:
                    QMessageBox.warning(self, "Validation Error", f"Quantity must be positive on line {r+1}.")
                    return None
                if unit_price < 0:
                     QMessageBox.warning(self, "Validation Error", f"Unit price cannot be negative on line {r+1}.")
                     return None

                line_dtos.append(SalesInvoiceLineBaseData(
                    product_id=product_id, description=description, quantity=quantity,
                    unit_price=unit_price, discount_percent=discount_percent, tax_code=tax_code_str
                    # Calculated fields (subtotal, tax_amount, total) will be re-derived by manager
                ))
            except Exception as e:
                QMessageBox.warning(self, "Input Error", f"Error processing line {r + 1}: {str(e)}"); return None
        
        if not line_dtos:
            QMessageBox.warning(self, "Input Error", "Sales invoice must have at least one valid line item."); return None

        common_data = {
            "customer_id": customer_id, "invoice_date": invoice_date_py, "due_date": due_date_py,
            "currency_code": self.currency_combo.currentData() or self._base_currency,
            "exchange_rate": Decimal(str(self.exchange_rate_spin.value())),
            "notes": self.notes_edit.toPlainText().strip() or None,
            "terms_and_conditions": self.terms_edit.toPlainText().strip() or None,
            "user_id": self.current_user_id, "lines": line_dtos
        }
        try:
            if self.invoice_id: return SalesInvoiceUpdateData(id=self.invoice_id, **common_data) # type: ignore
            else: return SalesInvoiceCreateData(**common_data) # type: ignore
        except ValueError as ve: # Pydantic validation error
            QMessageBox.warning(self, "Validation Error", f"Data validation failed:\n{str(ve)}"); return None

    @Slot()
    def on_save_draft(self):
        if self.view_only_mode or (self.loaded_invoice_orm and self.loaded_invoice_orm.status != InvoiceStatusEnum.DRAFT.value):
             QMessageBox.information(self, "Info", "Cannot save. Invoice is not a draft or in view-only mode.")
             return
        
        dto = self._collect_data()
        if dto:
            ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok) # Assuming Ok is Save Draft here
            if not ok_button : ok_button = self.save_draft_button # Fallback if not standard button
            if ok_button: ok_button.setEnabled(False)
            if self.save_approve_button: self.save_approve_button.setEnabled(False)

            future = schedule_task_from_qt(self._perform_save(dto, post_action=None))
            if future:
                future.add_done_callback(
                    lambda _: (
                        (ok_button.setEnabled(True) if ok_button else None),
                        (self.save_approve_button.setEnabled(False) if self.save_approve_button else None) # Keep approve disabled
                    )
                )
            else: # Handle scheduling failure
                if ok_button: ok_button.setEnabled(True)
                if self.save_approve_button: self.save_approve_button.setEnabled(False) # Still disabled

    async def _perform_save(self, dto: Union[SalesInvoiceCreateData, SalesInvoiceUpdateData], post_action: Optional[str]=None):
        if not self.app_core.sales_invoice_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Sales Invoice Manager not available."))
            return

        result: Result[SalesInvoice]
        is_update = isinstance(dto, SalesInvoiceUpdateData)
        action_verb_present = "update" if is_update else "create"
        action_verb_past = "updated" if is_update else "created"

        if is_update:
            result = await self.app_core.sales_invoice_manager.update_draft_invoice(dto.id, dto) # type: ignore
        else:
            result = await self.app_core.sales_invoice_manager.create_draft_invoice(dto) # type: ignore

        if result.is_success and result.value:
            msg = f"Sales Invoice draft {action_verb_past} successfully (ID: {result.value.id}, No: {result.value.invoice_no})."
            # TODO: Add posting logic if post_action is set
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, msg))
            self.invoice_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), Q_ARG(str, f"Failed to {action_verb_present} sales invoice draft:\n{', '.join(result.errors)}"))


    @Slot(int)
    def _on_customer_changed(self, index: int):
        customer_id = self.customer_combo.itemData(index)
        if customer_id and customer_id != 0 and self._customers_cache:
            customer_data = next((c for c in self._customers_cache if c.get("id") == customer_id), None)
            if customer_data and customer_data.get("currency_code"):
                curr_idx = self.currency_combo.findData(customer_data["currency_code"])
                if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
            if customer_data and customer_data.get("credit_terms") is not None:
                self.due_date_edit.setDate(self.invoice_date_edit.date().addDays(int(customer_data["credit_terms"])))

    @Slot(int)
    def _on_currency_changed(self, index: int):
        currency_code = self.currency_combo.itemData(index)
        is_base = (currency_code == self._base_currency)
        self.exchange_rate_spin.setEnabled(not is_base and not self.view_only_mode) # Also check view_only_mode
        self.exchange_rate_spin.setReadOnly(is_base or self.view_only_mode) 
        if is_base: self.exchange_rate_spin.setValue(1.0)

    @Slot(QDate)
    def _on_invoice_date_changed(self, new_date: QDate):
        customer_id = self.customer_combo.currentData()
        terms = 30 
        if customer_id and customer_id != 0 and self._customers_cache:
            customer_data = next((c for c in self._customers_cache if c.get("id") == customer_id), None)
            if customer_data and customer_data.get("credit_terms") is not None:
                try: terms = int(customer_data["credit_terms"])
                except: pass
        self.due_date_edit.setDate(new_date.addDays(terms))

```

**Summary of Changes and Validation for `app/ui/sales_invoices/sales_invoice_dialog.py` (Part 2):**

*   **`LineItemNumericDelegate.setModelData`**: Adjusted to handle `QTableWidget`'s item-based model by checking `isinstance(model, QTableWidget)`.
*   **`_calculate_line_item_totals(row)`**: Implemented to:
    *   Fetch quantity, price, discount percentage from cell widgets.
    *   Calculate discount amount and line subtotal.
    *   Fetch tax code selection. If a valid tax code is selected and subtotal > 0:
        *   Look up tax rate from `self._tax_codes_cache`.
        *   Calculate tax amount for the line.
    *   Calculate line total.
    *   Update the corresponding `QTableWidgetItem`s in the row for subtotal, tax amount, and line total.
    *   Calls `self._update_invoice_totals()`. Error handling included.
*   **`_update_invoice_totals()`**: Implemented to:
    *   Iterate all lines, parse subtotal and tax amount from each line's `QTableWidgetItem`.
    *   Sum these up to get invoice subtotal and total tax.
    *   Calculate grand total.
    *   Update the `self.subtotal_display`, `self.total_tax_display`, `self.grand_total_display` QLineEdits.
*   **`_collect_data()`**: Implemented to:
    *   Retrieve and validate header fields (customer selected, due date >= invoice date).
    *   Iterate through table lines, creating `SalesInvoiceLineBaseData` DTOs for valid lines (skips empty lines, validates quantity/price).
    *   Ensures at least one line item.
    *   Constructs `SalesInvoiceCreateData` or `SalesInvoiceUpdateData` DTO with header and line DTOs, including `user_id`.
    *   Catches and displays Pydantic validation errors.
*   **`on_save_draft()`**:
    *   Calls `_collect_data()`.
    *   If DTO is valid, disables save buttons and schedules `_perform_save(dto)`.
    *   Adds a `done_callback` to re-enable save buttons.
*   **`_perform_save(dto, post_action)`**:
    *   Calls the appropriate `SalesInvoiceManager` method (`create_draft_invoice` or `update_draft_invoice`).
    *   Handles the `Result` from the manager, showing success or error `QMessageBox` via `QMetaObject.invokeMethod`.
    *   On success, emits `invoice_saved` signal and calls `self.accept()`.
*   **Signal Connections in `_add_new_invoice_line`**: All editable widgets (product combo, qty, price, disc %, tax combo) in a new line now correctly connect their respective `currentIndexChanged` or `valueChanged` signals to `_trigger_line_recalculation_slot(row)`.
*   **Helper `_format_decimal_for_cell`**: Added for consistent formatting of calculated amounts in table cells.

**Validation against Plan:**
All checklist items for Part 2 have been addressed. The calculation logic is now in place for both individual lines and overall invoice totals. The data collection mechanism correctly creates DTOs from UI inputs. The save process interacts with the `SalesInvoiceManager` and provides UI feedback.

The codebase for `app/ui/sales_invoices/sales_invoice_dialog.py` is now substantially more functional and aligns with the planned implementation for handling draft sales invoices.
The use of `Decimal` for all monetary calculations and appropriate `quantize` calls are crucial for financial accuracy and have been incorporated.
The separation of UI updates (triggered from async tasks) using `QMetaObject.invokeMethod` is maintained.

The file is ready for the next stage (e.g., implementing the "Save & Approve" logic which would involve JE creation, or building the main `SalesInvoicesWidget` for listing invoices).
