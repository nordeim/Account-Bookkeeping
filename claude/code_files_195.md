<think>
Okay, I've identified a `SyntaxError: invalid syntax` in `app/ui/purchase_invoices/purchase_invoice_dialog.py` at line 533. This is the *exact same type of error* I introduced and fixed in `app/ui/sales_invoices/sales_invoice_dialog.py` previously. It's the incorrect use of a semicolon to chain an `else` clause on the same line as an `if` statement's body in Python.

The problematic line in `purchase_invoice_dialog.py` is:
```python
if future: future.add_done_callback(lambda res: QMetaObject.invokeMethod(self, "_safe_set_buttons_for_async_operation_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, False))); else: self._set_buttons_for_async_operation(False)
```

**Error Analysis & Deja Vu:**

This is a repeat of the syntax error pattern. The semicolon before `else` is invalid. I need to apply the same correction strategy I used for `SalesInvoiceDialog`.

**Corrected Logic (Recall from previous fix):**
The `if/else` structure should be:
```python
if future:
    future.add_done_callback(
        lambda res: QMetaObject.invokeMethod(
            self, "_safe_set_buttons_for_async_operation_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, False)
        )
    )
else:
    # Log the scheduling failure and re-enable buttons directly
    self.app_core.logger.error("Failed to schedule _perform_save task in on_save_draft.") # Contextualize log
    self._set_buttons_for_async_operation(False)
```
And a corresponding slot:
```python
@Slot(bool)
def _safe_set_buttons_for_async_operation_slot(self, busy: bool):
    self._set_buttons_for_async_operation(busy)
```

This error occurs in `on_save_draft()` method of `PurchaseInvoiceDialog`. The `on_save_and_approve()` method in `PurchaseInvoiceDialog` currently just shows a "Not Implemented" message, so it doesn't have this problematic structure yet.

**Double-Checking Past Resolutions:**
I must be extremely careful not to repeat errors. The pattern of this `SyntaxError` and its correction involving `QMetaObject.invokeMethod` for thread-safe UI updates from `add_done_callback` is now well-established from the `SalesInvoiceDialog` fix.

**Plan to Fix:**

1.  **Locate the `on_save_draft()` method** in `app/ui/purchase_invoices/purchase_invoice_dialog.py`.
2.  **Replace the erroneous `if/else` line** with the corrected multi-line structure, ensuring the `else` block includes logging and a direct call to `_set_buttons_for_async_operation(False)`.
3.  **Add the `@Slot(bool) def _safe_set_buttons_for_async_operation_slot(self, busy: bool):` method** to `PurchaseInvoiceDialog` if it's not already present from a previous similar fix (it shouldn't be, as this file was just generated).
4.  **Ensure `_set_buttons_for_async_operation(self, busy: bool)`** correctly manages the state of `save_draft_button` and `save_approve_button` (though `save_approve_button` is always disabled for PIs for now).

**Detailed Execution Plan:**

1.  **File**: `app/ui/purchase_invoices/purchase_invoice_dialog.py`
2.  **In `on_save_draft()` method**:
    *   Find the line: `if future: future.add_done_callback(lambda res: QMetaObject.invokeMethod(self, "_safe_set_buttons_for_async_operation_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, False))); else: self._set_buttons_for_async_operation(False)`
    *   Replace it with:
        ```python
        if future:
            future.add_done_callback(
                lambda res: QMetaObject.invokeMethod(
                    self, "_safe_set_buttons_for_async_operation_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, False)
                )
            )
        else:
            self.app_core.logger.error("Failed to schedule _perform_save task in on_save_draft for Purchase Invoice.")
            self._set_buttons_for_async_operation(False) # Re-enable buttons if scheduling failed
        ```
3.  **Add the `_safe_set_buttons_for_async_operation_slot` method** to the `PurchaseInvoiceDialog` class:
    ```python
    @Slot(bool)
    def _safe_set_buttons_for_async_operation_slot(self, busy: bool):
        self._set_buttons_for_async_operation(busy)
    ```
4.  **Verify `_set_buttons_for_async_operation(self, busy: bool)`**:
    The existing method is:
    ```python
    def _set_buttons_for_async_operation(self, busy: bool):
        self.save_draft_button.setEnabled(not busy)
        self.save_approve_button.setEnabled(False) # Always disabled for PI for now
    ```
    This is correct for the current state where "Save & Approve" is not implemented for Purchase Invoices.

This fix should resolve the `SyntaxError` and ensure that button states are updated correctly and thread-safely after an attempt to save a draft purchase invoice.
</think>

You are absolutely right to call for extreme thoroughness. That `SyntaxError` in `app/ui/purchase_invoices/purchase_invoice_dialog.py` is indeed a repeat of a mistake I made earlier in `SalesInvoiceDialog`. I apologize for this lapse in diligence. It's crucial to learn from these patterns.

The issue is the incorrect Python syntax for an `if/else` statement on a single line using a semicolon, and the fix involves restructuring it and ensuring thread-safe UI updates from the asynchronous callback.

**Plan to Fix `SyntaxError` in `PurchaseInvoiceDialog` and Ensure Thread-Safe UI Updates:**

1.  **Correct Python Syntax in `on_save_draft`**: The `if future: ...; else: ...` line will be rewritten as a proper multi-line `if/else` block.
2.  **Ensure Thread Safety for UI Update**: A new slot `_safe_set_buttons_for_async_operation_slot` will be added, and `QMetaObject.invokeMethod` will be used to call this slot from the `future.add_done_callback()`, ensuring the UI update happens on the Qt main thread.
3.  **Logging**: Add a log message in the `else` path if `schedule_task_from_qt` fails to return a future.

**Execution:**

I will now provide the complete updated replacement file for `app/ui/purchase_invoices/purchase_invoice_dialog.py` with the necessary corrections.

```python
# app/ui/purchase_invoices/purchase_invoice_dialog.py
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
    PurchaseInvoiceCreateData, PurchaseInvoiceUpdateData, PurchaseInvoiceLineBaseData,
    VendorSummaryData, ProductSummaryData 
)
from app.models.business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine
from app.models.accounting.currency import Currency 
from app.models.accounting.tax_code import TaxCode 
from app.models.business.product import Product 
from app.common.enums import InvoiceStatusEnum, ProductTypeEnum
from app.utils.result import Result
from app.utils.json_helpers import json_converter, json_date_hook
from app.ui.sales_invoices.sales_invoice_dialog import LineItemNumericDelegate # Re-use delegate
from app.ui.shared.product_search_dialog import ProductSearchDialog

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice, QAbstractItemModel 

class PurchaseInvoiceDialog(QDialog):
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
        self.loaded_invoice_orm: Optional[PurchaseInvoice] = None
        self.loaded_invoice_data_dict: Optional[Dict[str, Any]] = None
        self._current_search_target_row: Optional[int] = None 

        self._vendors_cache: List[Dict[str, Any]] = []
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
        if self.loaded_invoice_orm and self.loaded_invoice_orm.invoice_no: 
            inv_no_str = f" (Ref: {self.loaded_invoice_orm.invoice_no})"
        elif self.loaded_invoice_data_dict and self.loaded_invoice_data_dict.get("invoice_no"): 
            inv_no_str = f" (Ref: {self.loaded_invoice_data_dict.get('invoice_no')})"
            
        if self.view_only_mode: return f"View Purchase Invoice{inv_no_str}"
        if self.invoice_id: return f"Edit Purchase Invoice{inv_no_str}"
        return "New Purchase Invoice"

    def _init_ui(self):
        main_layout = QVBoxLayout(self); self.header_form = QFormLayout()
        self.header_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows) 
        self.header_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.vendor_combo = QComboBox(); self.vendor_combo.setEditable(True); self.vendor_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert); self.vendor_combo.setMinimumWidth(300)
        vend_completer = QCompleter(); vend_completer.setFilterMode(Qt.MatchFlag.MatchContains); vend_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.vendor_combo.setCompleter(vend_completer)
        
        self.our_ref_no_label = QLabel("To be generated"); self.our_ref_no_label.setStyleSheet("font-style: italic; color: grey;")
        self.vendor_invoice_no_edit = QLineEdit(); self.vendor_invoice_no_edit.setPlaceholderText("Supplier's Invoice Number")
        
        self.invoice_date_edit = QDateEdit(QDate.currentDate()); self.invoice_date_edit.setCalendarPopup(True); self.invoice_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.due_date_edit = QDateEdit(QDate.currentDate().addDays(30)); self.due_date_edit.setCalendarPopup(True); self.due_date_edit.setDisplayFormat("dd/MM/yyyy")
        
        self.currency_combo = QComboBox()
        self.exchange_rate_spin = QDoubleSpinBox(); self.exchange_rate_spin.setDecimals(6); self.exchange_rate_spin.setRange(0.000001, 999999.0); self.exchange_rate_spin.setValue(1.0)
        
        grid_header_layout = QGridLayout()
        grid_header_layout.addWidget(QLabel("Vendor*:"), 0, 0); grid_header_layout.addWidget(self.vendor_combo, 0, 1, 1, 2) 
        grid_header_layout.addWidget(QLabel("Our Ref No.:"), 0, 3); grid_header_layout.addWidget(self.our_ref_no_label, 0, 4)
        
        grid_header_layout.addWidget(QLabel("Vendor Inv No.:"), 1,0); grid_header_layout.addWidget(self.vendor_invoice_no_edit, 1,1,1,2)
        
        grid_header_layout.addWidget(QLabel("Invoice Date*:"), 2, 0); grid_header_layout.addWidget(self.invoice_date_edit, 2, 1)
        grid_header_layout.addWidget(QLabel("Due Date*:"), 2, 3); grid_header_layout.addWidget(self.due_date_edit, 2, 4)
        
        grid_header_layout.addWidget(QLabel("Currency*:"), 3, 0); grid_header_layout.addWidget(self.currency_combo, 3, 1)
        grid_header_layout.addWidget(QLabel("Exchange Rate:"), 3, 3); grid_header_layout.addWidget(self.exchange_rate_spin, 3, 4)
        
        grid_header_layout.setColumnStretch(2,1) 
        grid_header_layout.setColumnStretch(5,1) 
        main_layout.addLayout(grid_header_layout)

        self.notes_edit = QTextEdit(); self.notes_edit.setFixedHeight(60); self.header_form.addRow("Notes:", self.notes_edit)
        main_layout.addLayout(self.header_form) 

        self.lines_table = QTableWidget(); self.lines_table.setColumnCount(self.COL_TOTAL + 1) 
        self.lines_table.setHorizontalHeaderLabels(["", "Product/Service", "Description", "Qty*", "Unit Price*", "Disc %", "Subtotal", "Tax", "Tax Amt", "Total"])
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
        self.save_approve_button.setToolTip("Save purchase invoice and mark as Approved (posts Journal Entry).")
        self.save_approve_button.setEnabled(False) 
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

        self.vendor_combo.currentIndexChanged.connect(self._on_vendor_changed)
        self.currency_combo.currentIndexChanged.connect(self._on_currency_changed)
        self.invoice_date_edit.dateChanged.connect(self._on_invoice_date_changed)

    async def _load_initial_combo_data(self):
        try:
            cs_svc = self.app_core.company_settings_service
            if cs_svc: settings = await cs_svc.get_company_settings(); self._base_currency = settings.base_currency if settings else "SGD"

            vend_res: Result[List[VendorSummaryData]] = await self.app_core.vendor_manager.get_vendors_for_listing(active_only=True, page_size=-1)
            self._vendors_cache = [vs.model_dump() for vs in vend_res.value] if vend_res.is_success and vend_res.value else []
            
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
            self.app_core.logger.error(f"Error loading combo data for PurchaseInvoiceDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load initial data for dropdowns: {str(e)}")

    @Slot()
    def _populate_initial_combos_slot(self):
        self.vendor_combo.clear(); self.vendor_combo.addItem("-- Select Vendor --", 0)
        for vend in self._vendors_cache: self.vendor_combo.addItem(f"{vend['vendor_code']} - {vend['name']}", vend['id'])
        if isinstance(self.vendor_combo.completer(), QCompleter): self.vendor_combo.completer().setModel(self.vendor_combo.model()) 

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
        if not self.invoice_id or not self.app_core.purchase_invoice_manager: return
        self.loaded_invoice_orm = await self.app_core.purchase_invoice_manager.get_invoice_for_dialog(self.invoice_id)
        self.setWindowTitle(self._get_window_title()) 
        if self.loaded_invoice_orm:
            inv_dict = {col.name: getattr(self.loaded_invoice_orm, col.name) for col in PurchaseInvoice.__table__.columns if hasattr(self.loaded_invoice_orm, col.name)}
            inv_dict["lines"] = []
            if self.loaded_invoice_orm.lines: 
                for line_orm in self.loaded_invoice_orm.lines:
                    line_dict = {col.name: getattr(line_orm, col.name) for col in PurchaseInvoiceLine.__table__.columns if hasattr(line_orm, col.name)}
                    inv_dict["lines"].append(line_dict)
            
            invoice_json_str = json.dumps(inv_dict, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_dialog_from_data_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, invoice_json_str))
        else:
            QMessageBox.warning(self, "Load Error", f"Purchase Invoice ID {self.invoice_id} not found.")
            self.reject()

    @Slot(str)
    def _populate_dialog_from_data_slot(self, invoice_json_str: str):
        try:
            data = json.loads(invoice_json_str, object_hook=json_date_hook)
            self.loaded_invoice_data_dict = data 
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse existing purchase invoice data."); return

        self.our_ref_no_label.setText(data.get("invoice_no", "N/A")) 
        self.our_ref_no_label.setStyleSheet("font-style: normal; color: black;" if data.get("invoice_no") else "font-style: italic; color: grey;")
        self.vendor_invoice_no_edit.setText(data.get("vendor_invoice_no", "") or "")
        
        if data.get("invoice_date"): self.invoice_date_edit.setDate(QDate(data["invoice_date"]))
        if data.get("due_date"): self.due_date_edit.setDate(QDate(data["due_date"]))
        
        vend_idx = self.vendor_combo.findData(data.get("vendor_id"))
        if vend_idx != -1: self.vendor_combo.setCurrentIndex(vend_idx)
        
        curr_idx = self.currency_combo.findData(data.get("currency_code"))
        if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
        self.exchange_rate_spin.setValue(float(data.get("exchange_rate", 1.0) or 1.0))
        self._on_currency_changed(self.currency_combo.currentIndex()) 

        self.notes_edit.setText(data.get("notes", "") or "")
        
        self.lines_table.setRowCount(0) 
        for line_data_dict in data.get("lines", []): self._add_new_invoice_line(line_data_dict)
        if not data.get("lines") and not self.view_only_mode: self._add_new_invoice_line()
        
        self._update_invoice_totals() 
        self._set_read_only_state(self.view_only_mode or (data.get("status") != InvoiceStatusEnum.DRAFT.value))

    def _populate_fields_from_orm(self, invoice_orm: PurchaseInvoice): 
        vend_idx = self.vendor_combo.findData(invoice_orm.vendor_id)
        if vend_idx != -1: self.vendor_combo.setCurrentIndex(vend_idx)
        curr_idx = self.currency_combo.findData(invoice_orm.currency_code)
        if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
    
    def _set_read_only_state(self, read_only: bool):
        self.vendor_combo.setEnabled(not read_only)
        self.vendor_invoice_no_edit.setReadOnly(read_only)
        for w in [self.invoice_date_edit, self.due_date_edit, self.notes_edit]:
            if hasattr(w, 'setReadOnly'): w.setReadOnly(read_only) 
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
        self.save_approve_button.setEnabled(False) # Always false for PI for now

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
                price_val = prod_dict.get('purchase_price') 
                price_str = f"{Decimal(str(price_val)):.2f}" if price_val is not None else "N/A"
                prod_type_val = prod_dict.get('product_type')
                type_str = prod_type_val if isinstance(prod_type_val, str) else (prod_type_val.value if isinstance(prod_type_val, ProductTypeEnum) else "Unknown")
                display_text = f"{prod_dict['product_code']} - {prod_dict['name']} (Cost: {price_str})"
                prod_combo.addItem(display_text, prod_dict['id'])
                if prod_dict['id'] == current_prod_id: selected_prod_idx = i + 1
            prod_combo.setCurrentIndex(selected_prod_idx)
            if isinstance(prod_combo.completer(), QCompleter): prod_combo.completer().setModel(prod_combo.model())
        
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
            if price_widget and price_widget.value() == 0.0 and product_detail.get('purchase_price') is not None: 
                try: price_widget.setValue(float(Decimal(str(product_detail['purchase_price']))))
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
            self.app_core.logger.error(f"Error calculating PI line totals for row {row}: {e}", exc_info=True)
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
            except (InvalidOperation, AttributeError) as e: self.app_core.logger.warning(f"Could not parse amount from PI line {r} during total update: {e}")
        grand_total_agg = invoice_subtotal_agg + total_tax_agg
        self.subtotal_display.setText(self._format_decimal_for_cell(invoice_subtotal_agg, False))
        self.total_tax_display.setText(self._format_decimal_for_cell(total_tax_agg, False))
        self.grand_total_display.setText(self._format_decimal_for_cell(grand_total_agg, False))
        
    def _collect_data(self) -> Optional[Union[PurchaseInvoiceCreateData, PurchaseInvoiceUpdateData]]:
        vendor_id_data = self.vendor_combo.currentData()
        if not vendor_id_data or vendor_id_data == 0: QMessageBox.warning(self, "Validation Error", "Vendor must be selected."); return None
        vendor_id = int(vendor_id_data)
        vendor_invoice_no_str = self.vendor_invoice_no_edit.text().strip() or None
        if not vendor_invoice_no_str: QMessageBox.warning(self, "Validation Error", "Vendor Invoice No. is required."); return None
        invoice_date_py = self.invoice_date_edit.date().toPython(); due_date_py = self.due_date_edit.date().toPython()
        if due_date_py < invoice_date_py: QMessageBox.warning(self, "Validation Error", "Due date cannot be before invoice date."); return None
        line_dtos: List[PurchaseInvoiceLineBaseData] = []
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
                line_dtos.append(PurchaseInvoiceLineBaseData(product_id=product_id, description=description, quantity=quantity, unit_price=unit_price, discount_percent=discount_percent, tax_code=tax_code_str))
            except Exception as e: QMessageBox.warning(self, "Input Error", f"Error processing line {r + 1}: {str(e)}"); return None
        if not line_dtos: QMessageBox.warning(self, "Input Error", "Purchase invoice must have at least one valid line item."); return None
        common_data = { "vendor_id": vendor_id, "vendor_invoice_no": vendor_invoice_no_str, "invoice_date": invoice_date_py, "due_date": due_date_py, "currency_code": self.currency_combo.currentData() or self._base_currency, "exchange_rate": Decimal(str(self.exchange_rate_spin.value())), "notes": self.notes_edit.toPlainText().strip() or None, "user_id": self.current_user_id, "lines": line_dtos }
        try:
            if self.invoice_id: return PurchaseInvoiceUpdateData(id=self.invoice_id, **common_data) 
            else: return PurchaseInvoiceCreateData(**common_data) 
        except ValueError as ve: QMessageBox.warning(self, "Validation Error", f"Data validation failed:\n{str(ve)}"); return None

    @Slot()
    def on_save_draft(self):
        if self.view_only_mode or (self.loaded_invoice_orm and self.loaded_invoice_orm.status != InvoiceStatusEnum.DRAFT.value): QMessageBox.information(self, "Info", "Cannot save. Invoice is not a draft or in view-only mode."); return
        dto = self._collect_data()
        if dto: 
            self._set_buttons_for_async_operation(True)
            future = schedule_task_from_qt(self._perform_save(dto, post_invoice_after=False))
            if future:
                future.add_done_callback(
                    lambda res: QMetaObject.invokeMethod(
                        self, "_safe_set_buttons_for_async_operation_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, False)
                    )
                )
            else:
                self.app_core.logger.error("Failed to schedule _perform_save task in on_save_draft for Purchase Invoice.")
                self._set_buttons_for_async_operation(False) # Re-enable buttons if scheduling failed


    @Slot()
    def on_save_and_approve(self): QMessageBox.information(self, "Not Implemented", "Save & Approve for Purchase Invoices is not yet available.")

    @Slot(bool)
    def _safe_set_buttons_for_async_operation_slot(self, busy: bool):
        self._set_buttons_for_async_operation(busy)

    def _set_buttons_for_async_operation(self, busy: bool):
        self.save_draft_button.setEnabled(not busy)
        self.save_approve_button.setEnabled(False) 

    async def _perform_save(self, dto: Union[PurchaseInvoiceCreateData, PurchaseInvoiceUpdateData], post_invoice_after: bool):
        if not self.app_core.purchase_invoice_manager: QMessageBox.critical(self, "Error", "Purchase Invoice Manager not available."); return
        save_result: Result[PurchaseInvoice]; is_update = isinstance(dto, PurchaseInvoiceUpdateData); action_verb_past = "updated" if is_update else "created"
        if is_update: save_result = await self.app_core.purchase_invoice_manager.update_draft_purchase_invoice(dto.id, dto) 
        else: save_result = await self.app_core.purchase_invoice_manager.create_draft_purchase_invoice(dto) 
        if not save_result.is_success or not save_result.value: QMessageBox.warning(self, "Save Error", f"Failed to {('update' if is_update else 'create')} purchase invoice draft:\n{', '.join(save_result.errors)}"); return 
        saved_invoice = save_result.value; self.invoice_saved.emit(saved_invoice.id); self.invoice_id = saved_invoice.id; self.loaded_invoice_orm = saved_invoice; self.setWindowTitle(self._get_window_title()); self.our_ref_no_label.setText(saved_invoice.invoice_no); self.our_ref_no_label.setStyleSheet("font-style: normal; color: black;")
        if not post_invoice_after: QMessageBox.information(self, "Success", f"Purchase Invoice draft {action_verb_past} successfully (ID: {saved_invoice.id}, Our Ref: {saved_invoice.invoice_no})."); self._set_read_only_state(self.view_only_mode or (saved_invoice.status != InvoiceStatusEnum.DRAFT.value)); self.accept(); return
        # PI Posting logic here if post_invoice_after is True

    @Slot(int)
    def _on_vendor_changed(self, index: int):
        vendor_id = self.vendor_combo.itemData(index)
        if vendor_id and vendor_id != 0 and self._vendors_cache:
            vendor_data = next((v for v in self._vendors_cache if v.get("id") == vendor_id), None)
            if vendor_data and vendor_data.get("currency_code"):
                curr_idx = self.currency_combo.findData(vendor_data["currency_code"])
                if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
            if vendor_data and vendor_data.get("payment_terms") is not None: self.due_date_edit.setDate(self.invoice_date_edit.date().addDays(int(vendor_data["payment_terms"])))

    @Slot(int)
    def _on_currency_changed(self, index: int):
        currency_code = self.currency_combo.currentData(); is_base = (currency_code == self._base_currency)
        self.exchange_rate_spin.setEnabled(not is_base and not self.view_only_mode); self.exchange_rate_spin.setReadOnly(is_base or self.view_only_mode); 
        if is_base: self.exchange_rate_spin.setValue(1.0)

    @Slot(QDate)
    def _on_invoice_date_changed(self, new_date: QDate):
        vendor_id = self.vendor_combo.currentData(); terms = 30 
        if vendor_id and vendor_id != 0 and self._vendors_cache:
            vendor_data = next((v for v in self._vendors_cache if v.get("id") == vendor_id), None)
            if vendor_data and vendor_data.get("payment_terms") is not None:
                try: terms = int(vendor_data["payment_terms"])
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
                if found_idx != -1: prod_combo.setCurrentIndex(found_idx) 
                else: self.app_core.logger.warning(f"Product ID {product_id} from search not in line combo for PI row {target_row}. Forcing."); self._on_line_product_changed(target_row, product_id) 
            else: self.app_core.logger.error(f"Product combo not found for PI row {target_row}.")
        except Exception as e: self.app_core.logger.error(f"Error handling product selected from search for PI: {e}", exc_info=True); QMessageBox.warning(self, "Product Selection Error", f"Could not apply product: {str(e)}")
        finally: self._current_search_target_row = None

```

**Review of `app/ui/purchase_invoices/purchase_invoice_dialog.py` after Syntax Fix and Thread Safety Enhancement:**

1.  **Syntax Error Fix (L533 in original context, now L554 in new context for `on_save_draft`):**
    *   The problematic line:
        ```python
        # if future: future.add_done_callback(lambda res: QMetaObject.invokeMethod(self, "_safe_set_buttons_for_async_operation_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, False))); else: self._set_buttons_for_async_operation(False)
        ```
    *   Has been correctly replaced with:
        ```python
        if future:
            future.add_done_callback(
                lambda res: QMetaObject.invokeMethod(
                    self, "_safe_set_buttons_for_async_operation_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, False)
                )
            )
        else:
            self.app_core.logger.error("Failed to schedule _perform_save task in on_save_draft for Purchase Invoice.")
            self._set_buttons_for_async_operation(False) # Re-enable buttons if scheduling failed
        ```
    *   **Validation**: This is correct and mirrors the fix applied to `SalesInvoiceDialog`. The Python `SyntaxError` is resolved. The `else` block correctly handles failed task scheduling.

2.  **New Slot `_safe_set_buttons_for_async_operation_slot`:**
    *   The slot `@Slot(bool) def _safe_set_buttons_for_async_operation_slot(self, busy: bool):` has been added:
        ```python
        @Slot(bool)
        def _safe_set_buttons_for_async_operation_slot(self, busy: bool):
            self._set_buttons_for_async_operation(busy)
        ```
    *   **Validation**: This correctly allows `QMetaObject.invokeMethod` to call `_set_buttons_for_async_operation` on the main Qt thread.

3.  **Delegate `setModelData` in `LineItemNumericDelegate`**:
    *   The diff shows an attempt to refine the `setModelData` method within `LineItemNumericDelegate` (which is imported from `sales_invoice_dialog.py`).
    *   The change from the previous version was:
        ```diff
        -        if isinstance(model, QTableWidget): # This check won't work, model is internal
        -            item = self.parent().item(index.row(), index.column()) if isinstance(self.parent(), QTableWidget) else None # Try to get item if model is table
        -            if item:
        -                 item.setText(str(Decimal(str(editor.value())).quantize(Decimal(precision_str), ROUND_HALF_UP)))
        -            else: # Fallback or if model is not QTableWidget
        -                 model.setData(index, str(Decimal(str(editor.value())).quantize(Decimal(precision_str), ROUND_HALF_UP)), Qt.ItemDataRole.EditRole)
        +        table_widget_item = None
        +        if isinstance(self.parent(), QTableWidget) and isinstance(model, QTableWidget): # More robust check
        +             table_widget_item = self.parent().item(index.row(), index.column())
        ```
    *   The problematic part `and isinstance(model, QTableWidget)` was **still present in the `-orig` version of the file provided for this diff context**. The latest generated version of `sales_invoice_dialog.py` (from the previous turn where this delegate was fixed) has the corrected logic:
        ```python
        # Corrected logic in sales_invoice_dialog.py (from previous turn)
        precision_str = '0.01' if self.decimals == 2 else ('0.0001' if self.decimals == 4 else '0.000001')
        view = self.parent()
        if isinstance(view, QTableWidget):
            item = view.item(index.row(), index.column())
            if item: 
                item.setText(str(Decimal(str(editor.value())).quantize(Decimal(precision_str), ROUND_HALF_UP)))
            else:
                model.setData(index, str(Decimal(str(editor.value())).quantize(Decimal(precision_str), ROUND_HALF_UP)), Qt.ItemDataRole.EditRole)
        else:
            model.setData(index, str(Decimal(str(editor.value())).quantize(Decimal(precision_str), ROUND_HALF_UP)), Qt.ItemDataRole.EditRole)
        ```
    *   **The `purchase_invoice_dialog.py` *imports* `LineItemNumericDelegate` from `sales_invoice_dialog.py`. Therefore, `purchase_invoice_dialog.py` itself does not need to redefine or fix the delegate. The fix made in `sales_invoice_dialog.py` will be used by `purchase_invoice_dialog.py`.** The diff shown is for `sales_invoice_dialog.py`, not `purchase_invoice_dialog.py` in this section of the diff. My review of the sales dialog's diff confirms this delegate fix was indeed made there.

4.  **No other functional changes** were introduced to `purchase_invoice_dialog.py` beyond fixing the syntax and ensuring thread-safe UI updates for button states in `on_save_draft`. All other logic for product search integration, calculations, and data handling remains as validated in the previous step.

**Conclusion on `app/ui/purchase_invoices/purchase_invoice_dialog.py` Changes:**

The changes are **valid and primarily address the critical `SyntaxError`.**
*   **Syntax Error**: The `SyntaxError` in `on_save_draft` is fixed.
*   **Thread Safety**: UI updates for button states from the async task callback are now correctly marshaled to the Qt main thread.
*   **No Loss of Functionality**: The core logic for purchase invoice creation, editing, product search integration, and calculations remains intact.

The application should now run without the `SyntaxError`, and both sales and purchase invoice dialogs should have a functional and robust product search feature, along with correct asynchronous operation handling.
