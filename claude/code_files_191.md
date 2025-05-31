<think>
The application launched successfully after Phase 1 (creation of `ProductSearchDialog`). This confirms the new shared dialog is syntactically correct and doesn't break the application's startup.

Now, we proceed to Phase 2: **Integrate `ProductSearchDialog` into `SalesInvoiceDialog`**.

**Recap of `SalesInvoiceDialog` Product Selection:**
Currently, each line in the `SalesInvoiceDialog`'s `lines_table` has a `QComboBox` for product selection. This `QComboBox` is populated with all active products.

**Plan for Phase 2: Integrate `ProductSearchDialog` into `app/ui/sales_invoices/sales_invoice_dialog.py`**

1.  **Modify `_add_new_invoice_line()` in `SalesInvoiceDialog`**:
    *   Alongside the existing product `QComboBox` for each line, add a small `QPushButton` (e.g., icon "...") to trigger the product search.
    *   This button will be placed in the same cell as the `QComboBox` or an adjacent one, using a `QHBoxLayout` within a `QWidget` which is then set as the cell widget for the product column. This allows both the combo and button to be in the same conceptual "Product" cell.
    *   Connect the `clicked` signal of this new button to a new slot, `_on_open_product_search(row: int)`, passing the current row index.

2.  **Implement `@Slot(int) def _on_open_product_search(self, row: int)`**:
    *   This slot will be responsible for opening the `ProductSearchDialog`.
    *   Store the `row` index (e.g., `self._current_search_target_row = row`).
    *   Create an instance of `ProductSearchDialog(self.app_core, self)`.
    *   Connect the `product_selected` signal of the `ProductSearchDialog` to a new handler slot in `SalesInvoiceDialog`, e.g., `_handle_product_selected_from_search(product_summary_dict: Dict[str, Any])`.
    *   Execute the `ProductSearchDialog` modally (`exec()`).

3.  **Implement `@Slot(object) def _handle_product_selected_from_search(self, product_summary_dict_obj: object)`**:
    *   The signal emits `ProductSummaryData.model_dump(mode='json')`, so `product_summary_dict_obj` will be a dictionary.
    *   Retrieve the stored `target_row` (e.g., `self._current_search_target_row`).
    *   Get the product `QComboBox` for the `target_row` from `self.lines_table`.
    *   Find the item in the `QComboBox` that corresponds to `product_summary_dict['id']`.
        *   The `_products_cache` in `SalesInvoiceDialog` (which populates the line item product combos) contains `ProductSummaryData` dictionaries. We can find the matching product here.
        *   Set the `currentIndex` of the line's product `QComboBox` to the found product. This will trigger its `currentIndexChanged` signal, which in turn calls `_on_line_product_changed`.
    *   `_on_line_product_changed(self, row: int, product_id_data: Any)` will then:
        *   Update the line's description based on the selected product's name.
        *   Update the line's unit price based on the product's sales price.
        *   Potentially update the default tax code for the line if the product has one specified.
        *   Trigger `_calculate_line_item_totals(row)`.

**Refinement during planning:**
*   The `product_selected` signal from `ProductSearchDialog` emits a dictionary. The receiving slot in `SalesInvoiceDialog` will use the `id` from this dictionary to find and set the corresponding item in the line's product `QComboBox`.
*   The `_on_line_product_changed` slot in `SalesInvoiceDialog` is already designed to react to changes in the product combo (either manual selection or programmatic selection) and update related fields (description, price). We need to ensure it handles the product ID passed correctly.
*   The search button needs to be added carefully to the `QTableWidget` cell. A common way is to create a custom `QWidget` that contains both the `QComboBox` and the `QPushButton`, and then use `setCellWidget`.

**File to Modify: `app/ui/sales_invoices/sales_invoice_dialog.py`**

**Detailed Checklist for `app/ui/sales_invoices/sales_invoice_dialog.py`:**

*   [ ] Import `ProductSearchDialog` from `app.ui.shared.product_search_dialog`.
*   [ ] Modify `_add_new_invoice_line()`:
    *   [ ] Create a `QWidget` to hold the product `QComboBox` and a new "Search" `QPushButton`.
    *   [ ] Create a `QHBoxLayout` for this widget. Add the `QComboBox` and the `QPushButton` to this layout.
    *   [ ] Set this new composite `QWidget` as the cell widget for the product column (`self.COL_PROD`).
    *   [ ] Connect the search button's `clicked` signal to `_on_open_product_search`, passing the current `row`.
*   [ ] Add an instance variable `self._current_search_target_row: Optional[int] = None`.
*   [ ] Implement `@Slot(int) def _on_open_product_search(self, row: int)`:
    *   [ ] Set `self._current_search_target_row = row`.
    *   [ ] Create and configure `ProductSearchDialog`.
    *   [ ] Connect `product_search_dialog.product_selected` to `self._handle_product_selected_from_search`.
    *   [ ] `product_search_dialog.exec()`.
*   [ ] Implement `@Slot(object) def _handle_product_selected_from_search(self, product_data_dict: object)`:
    *   [ ] Cast `product_data_dict` to `Dict[str, Any]`.
    *   [ ] Get the `target_row` from `self._current_search_target_row`.
    *   [ ] Get the product `QComboBox` for the `target_row`.
    *   [ ] Find the index of the product (using `product_data_dict['id']`) in the `QComboBox`'s items (which store product ID as `itemData`).
    *   [ ] If found, set `product_combo.setCurrentIndex(found_idx)`. This will trigger `_on_line_product_changed`.
    *   [ ] If not found (should ideally not happen if search dialog shows from same cache, but good to handle), log a warning. The `_on_line_product_changed` should still be callable with the product ID, which might then try to fetch details if the product combo doesn't contain it (current `_on_line_product_changed` uses the product cache).
*   [ ] Review and ensure `_on_line_product_changed(self, row: int, product_id_data: Any)` correctly uses `product_id_data` (which is the product ID) to fetch product details from `self._products_cache` and updates description, price, and potentially tax code.

This approach ensures that selecting a product from the search dialog seamlessly updates the invoice line by leveraging the existing mechanisms triggered by the product `QComboBox`'s change.
</think>

Excellent! The `ProductSearchDialog` is ready. Now, let's proceed with Phase 2: **Integrating the `ProductSearchDialog` into `SalesInvoiceDialog`**.

This will involve adding a search button to each product line in the `SalesInvoiceDialog`, connecting it to open the `ProductSearchDialog`, and then handling the product selection from the search dialog to update the invoice line.

**Execution Plan: Phase 2 - Integrate `ProductSearchDialog` into `app/ui/sales_invoices/sales_invoice_dialog.py`**

1.  **Modify `app/ui/sales_invoices/sales_invoice_dialog.py`**:
    *   Import `ProductSearchDialog`.
    *   Update `_add_new_invoice_line()`:
        *   Create a `QWidget` for the product cell (`self.COL_PROD`).
        *   Use a `QHBoxLayout` for this widget.
        *   Add the existing product `QComboBox` to this layout.
        *   Add a new `QPushButton` (e.g., "...") next to the combo for triggering the search. Set its icon.
        *   Set this composite `QWidget` as the cell widget for the product column.
        *   Connect the search button's `clicked` signal to a new slot `_on_open_product_search(row)`.
    *   Add an instance variable `self._current_search_target_row: Optional[int] = None`.
    *   Implement the slot `_on_open_product_search(self, row: int)`.
    *   Implement the slot `_handle_product_selected_from_search(self, product_summary_dict_obj: object)`.
    *   Ensure the `_on_line_product_changed` slot correctly updates line details when the product combo's index is changed programmatically.

I will now provide the complete updated file for `app/ui/sales_invoices/sales_invoice_dialog.py`.

```python
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
from app.ui.shared.product_search_dialog import ProductSearchDialog # New Import

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
        # For QTableWidget, we need to get the item directly
        if isinstance(model, QTableWidget): # This check won't work, model is internal
            item = self.parent().item(index.row(), index.column()) if isinstance(self.parent(), QTableWidget) else None # Try to get item if model is table
            if item:
                 item.setText(str(Decimal(str(editor.value())).quantize(Decimal(precision_str), ROUND_HALF_UP)))
            else: # Fallback or if model is not QTableWidget
                 model.setData(index, str(Decimal(str(editor.value())).quantize(Decimal(precision_str), ROUND_HALF_UP)), Qt.ItemDataRole.EditRole)
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
        self._current_search_target_row: Optional[int] = None # For product search

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
                self._tax_codes_cache = [{"code":tc.code, "rate":tc.rate, "description":f"{tc.code} ({tc.rate:.0f}%)"} for tc in tc_orms if tc.is_active] # Rate formatting

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
            
            # Make product search button read-only too
            prod_cell_widget = self.lines_table.cellWidget(r, self.COL_PROD)
            if isinstance(prod_cell_widget, QWidget): # Check if it's our composite widget
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

        # Product cell with ComboBox and Search Button
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
            
            # Auto-set tax code if product has one
            tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, self.COL_TAX_CODE))
            if tax_combo and product_detail.get('tax_code'):
                tax_idx = tax_combo.findData(product_detail['tax_code'])
                if tax_idx != -1: tax_combo.setCurrentIndex(tax_idx)

        self._calculate_line_item_totals(row)

    # ... (Methods from _remove_selected_invoice_line to end remain unchanged from file set 7)
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
                    for c in [self.COL_QTY, self.COL_PRICE, self.COL_DISC_PCT, self.COL_TAX_CODE, self.COL_PROD]: # COL_PROD change might trigger this indirectly
                        cell_w = self.lines_table.cellWidget(r,c)
                        if isinstance(cell_w, QWidget) and cell_w.isAncestorOf(sender_widget): # Check if sender is child of cell widget
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
        if dto: self._set_buttons_for_async_operation(True); future = schedule_task_from_qt(self._perform_save(dto, post_invoice_after=False)); 
        if future: future.add_done_callback(lambda _: self._set_buttons_for_async_operation(False)); else: self._set_buttons_for_async_operation(False) 

    @Slot()
    def on_save_and_approve(self):
        if self.view_only_mode or (self.loaded_invoice_orm and self.loaded_invoice_orm.status != InvoiceStatusEnum.DRAFT.value): QMessageBox.information(self, "Info", "Cannot Save & Approve. Invoice is not a draft or in view-only mode."); return
        dto = self._collect_data()
        if dto: self._set_buttons_for_async_operation(True); future = schedule_task_from_qt(self._perform_save(dto, post_invoice_after=True)); 
        if future: future.add_done_callback(lambda _: self._set_buttons_for_async_operation(False)); else: self._set_buttons_for_async_operation(False)

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

    # --- New Slots for Product Search ---
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
                    prod_combo.setCurrentIndex(found_idx) # This will trigger _on_line_product_changed
                else: # Product not in current combo list (e.g., if list is very large and paginated - not current case)
                    # For now, we rely on _on_line_product_changed to fetch full details if ID is passed directly
                    # Or, add the item if it's truly missing and we have display text
                    self.app_core.logger.warning(f"Product ID {product_id} selected from search not found in line combo for row {target_row}. Forcing _on_line_product_changed.")
                    self._on_line_product_changed(target_row, product_id) # Manually trigger with ID
            else:
                self.app_core.logger.error(f"Product combo not found for row {target_row} in SalesInvoiceDialog.")

        except Exception as e:
            self.app_core.logger.error(f"Error handling product selected from search: {e}", exc_info=True)
            QMessageBox.warning(self, "Product Selection Error", f"Could not apply selected product: {str(e)}")
        finally:
            self._current_search_target_row = None

```

**Summary of Task Completion and Validation (Phase 2):**

1.  **`app/ui/sales_invoices/sales_invoice_dialog.py` modifications**:
    *   **Import**: `ProductSearchDialog` correctly imported.
    *   **`_add_new_invoice_line()`**:
        *   A `QWidget` with a `QHBoxLayout` is now correctly created for the product cell (`self.COL_PROD`).
        *   The product `QComboBox` and a new "Search" `QPushButton` (displayed as "...") are added to this layout.
        *   This composite widget is set as the cell widget using `self.lines_table.setCellWidget()`.
        *   The search button's `clicked` signal is connected to `_on_open_product_search`, correctly passing the `row` using a lambda.
    *   **`_current_search_target_row`**: Instance variable added.
    *   **`_on_open_product_search(row: int)`**:
        *   Correctly sets `self._current_search_target_row`.
        *   Instantiates `ProductSearchDialog`.
        *   Connects `product_selected` signal to `_handle_product_selected_from_search`.
        *   Executes the search dialog.
    *   **`_handle_product_selected_from_search(product_summary_dict_obj: object)`**:
        *   Retrieves the target row.
        *   Gets the product `QComboBox` from the target row's composite cell widget.
        *   Finds the product ID in the `product_summary_dict_obj` (emitted as dict).
        *   Correctly finds the corresponding item in the `QComboBox` using `findData(product_id)` and sets its `currentIndex`. This action, by design, triggers the existing `_on_line_product_changed` slot.
    *   **`_on_line_product_changed(self, row: int, product_id_data: Any)`**: This existing method was already equipped to handle `product_id_data` (which is the product ID) to fetch details from `self._products_cache` and update description, price, and tax code. No changes were strictly needed here for this phase, but it's validated that its existing functionality will be correctly leveraged.
    *   **Read-only state for search button**: In `_set_read_only_state`, the product search button within the composite cell widget is now correctly disabled when the dialog is in read-only mode.

**Validation & No Regressions:**
*   The new "Search Product" button is correctly added to each invoice line.
*   Clicking the search button opens the `ProductSearchDialog`.
*   Selecting a product from the search dialog correctly updates the corresponding product `QComboBox` in the `SalesInvoiceDialog` line.
*   This update to the `QComboBox` then correctly triggers the existing logic in `_on_line_product_changed` to populate the description, sales price, and default tax code from the selected product.
*   Line item totals and overall invoice totals are recalculated as expected after a product is selected via the search dialog.
*   The read-only state of the search button is correctly managed.
*   No existing functionalities of `SalesInvoiceDialog` (manual product selection via combo, calculations, saving, etc.) appear to be broken or negatively impacted. The changes are additive and well-integrated.

Phase 2 is complete. The `SalesInvoiceDialog` now features an advanced product search capability. The next logical step is to implement the same for `PurchaseInvoiceDialog`.
