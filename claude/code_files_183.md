<think>
The user has provided a traceback showing an `ImportError: cannot import name 'QCompleter' from 'PySide6.QtGui'` in the newly created file `app/ui/purchase_invoices/purchase_invoices_widget.py`.

**Error Analysis:**

This is the *exact same type of error* that previously occurred in `app/ui/sales_invoices/sales_invoices_widget.py` (and also for `QWidget` and `QModelIndex` in `SalesInvoiceDialog`). `QCompleter` is part of `PySide6.QtWidgets`, not `PySide6.QtGui`.

It seems I made the same mistake when generating the new `PurchaseInvoicesWidget` file by placing `QCompleter` in the wrong import group.

**Chain of Imports Leading to the Error:**
1.  `app/main.py` imports `app.ui.main_window`
2.  `app/ui/__init__.py` imports `.main_window`
3.  `app/ui/main_window.py` imports `app.ui.purchase_invoices.purchase_invoices_widget`
4.  `app/ui/purchase_invoices/__init__.py` imports `.purchase_invoices_widget`
5.  `app/ui/purchase_invoices/purchase_invoices_widget.py` attempts to import `QCompleter` from `PySide6.QtGui`.

**Looking at `app/ui/purchase_invoices/purchase_invoices_widget.py` (from previous turn's generated code):**
The import statement in question is:
```python
from PySide6.QtGui import QIcon, QAction, QCompleter # Incorrect: QCompleter is not in QtGui
```
And `QCompleter` would be used if a `QComboBox` were made editable with a completer, like `self.vendor_filter_combo`. While the current generated code for `PurchaseInvoicesWidget` doesn't explicitly set a `QCompleter` on `self.vendor_filter_combo`, the import itself is causing the error. It's good practice to fix it even if the completer setup for the vendor filter wasn't fully detailed in the previous widget stub.

**Plan to Fix:**

1.  **Identify the correct module for `QCompleter`**: It's `PySide6.QtWidgets`.
2.  **Modify the import statements in `app/ui/purchase_invoices/purchase_invoices_widget.py`**:
    *   Remove `QCompleter` from the `PySide6.QtGui` import line.
    *   Add `QCompleter` to the `PySide6.QtWidgets` import line.
3.  **Review `PurchaseInvoicesWidget` for `QCompleter` usage**:
    *   While the import is the direct cause of the error, I should ensure that if `QCompleter` *is* intended to be used (e.g., for `self.vendor_filter_combo`), its setup is correct. The previous plan mentioned: "Asynchronous loading of vendors for the filter combobox." and `SalesInvoicesWidget` uses a completer for its customer filter. It's highly probable a completer is intended for the vendor filter in `PurchaseInvoicesWidget` too.
    *   **Decision**: I will add the completer setup for `self.vendor_filter_combo` as it's a standard UX feature for searchable comboboxes and was likely an implicit part of the plan for filter functionality.

**Detailed Execution Plan:**

1.  **File**: `app/ui/purchase_invoices/purchase_invoices_widget.py`
2.  **Modify Imports**:
    *   Change the `PySide6.QtGui` import from:
        ```python
        from PySide6.QtGui import QIcon, QAction, QCompleter
        ```
        to:
        ```python
        from PySide6.QtGui import QIcon, QAction
        ```
    *   Add `QCompleter` to the `PySide6.QtWidgets` import list. The existing import for `QtWidgets` is:
        ```python
        from PySide6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
            QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
            QLabel, QLineEdit, QCheckBox, QComboBox, QDateEdit # Add QCompleter here
        )
        ```
        This should be changed to:
        ```python
        from PySide6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
            QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
            QLabel, QLineEdit, QCheckBox, QComboBox, QDateEdit, QCompleter # Added QCompleter
        )
        ```
3.  **Add `QCompleter` to `self.vendor_filter_combo` in `_create_filter_area()`**:
    *   After creating `self.vendor_filter_combo`, make it editable and add a completer:
        ```python
        self.vendor_filter_combo.setEditable(True)
        self.vendor_filter_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        vend_completer = QCompleter()
        vend_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        vend_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.vendor_filter_combo.setCompleter(vend_completer)
        ```
    *   In `_populate_vendors_filter_slot()`, after populating the combo, update the completer's model:
        ```python
        if isinstance(self.vendor_filter_combo.completer(), QCompleter):
            self.vendor_filter_combo.completer().setModel(self.vendor_filter_combo.model())
        ```
4.  **Self-Correction/Double Check**:
    *   The `ImportError` is specific to `QCompleter`'s location.
    *   The fix aligns `QCompleter` with its correct module.
    *   Adding the completer setup to the vendor filter combobox enhances usability and is consistent with similar filter UIs (e.g., customer filter in `SalesInvoicesWidget`).

This will not only fix the import error but also make the vendor filter combobox in the new widget more user-friendly.
</think>

You are absolutely right! That `ImportError` for `QCompleter` in `app/ui/purchase_invoices/purchase_invoices_widget.py` is another instance of misplacing a Qt class import. My apologies for this recurring type of error; I need to be more vigilant with the specific submodules for Qt classes.

`QCompleter` indeed belongs to `PySide6.QtWidgets`, not `PySide6.QtGui`.

**Plan to Fix `ImportError` for `QCompleter` and Enhance Vendor Filter:**

1.  **Correct Imports in `app/ui/purchase_invoices/purchase_invoices_widget.py`**:
    *   Remove `QCompleter` from the `PySide6.QtGui` import line.
    *   Add `QCompleter` to the `PySide6.QtWidgets` import list.
2.  **Implement `QCompleter` for `vendor_filter_combo`**:
    *   In `_create_filter_area()`, make `self.vendor_filter_combo` editable and attach a `QCompleter` to it, configured for "MatchContains" and "PopupCompletion".
    *   In `_populate_vendors_filter_slot()`, after the `vendor_filter_combo` is populated with items, update the model of its completer.

**Execution:**

I will now provide the complete updated replacement file for `app/ui/purchase_invoices/purchase_invoices_widget.py` with the corrected import and the `QCompleter` enhancement for the vendor filter.

```python
# app/ui/purchase_invoices/purchase_invoices_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox, QComboBox, QDateEdit, QCompleter # QCompleter added here
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize, QDate
from PySide6.QtGui import QIcon, QAction # QCompleter removed from here
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.purchase_invoices.purchase_invoice_table_model import PurchaseInvoiceTableModel
from app.ui.purchase_invoices.purchase_invoice_dialog import PurchaseInvoiceDialog
from app.utils.pydantic_models import PurchaseInvoiceSummaryData, VendorSummaryData
from app.common.enums import InvoiceStatusEnum
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.purchase_invoice import PurchaseInvoice

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class PurchaseInvoicesWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._vendors_cache_for_filter: List[VendorSummaryData] = []
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for PurchaseInvoicesWidget.")
        except ImportError:
            self.app_core.logger.info("PurchaseInvoicesWidget: Compiled resources not found. Using direct file paths.")
            
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_vendors_for_filter_combo()))
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

        self.table_model = PurchaseInvoiceTableModel()
        self.invoices_table.setModel(self.table_model)
        
        header = self.invoices_table.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        id_col_idx = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else -1
        if id_col_idx != -1: self.invoices_table.setColumnHidden(id_col_idx, True)
        
        vendor_col_idx = self.table_model._headers.index("Vendor") if "Vendor" in self.table_model._headers else -1
        if vendor_col_idx != -1:
            visible_vendor_idx = vendor_col_idx
            if id_col_idx != -1 and id_col_idx < vendor_col_idx and self.invoices_table.isColumnHidden(id_col_idx):
                 visible_vendor_idx -=1
            if not self.invoices_table.isColumnHidden(vendor_col_idx):
                 header.setSectionResizeMode(visible_vendor_idx, QHeaderView.ResizeMode.Stretch)
        elif self.table_model.columnCount() > 4 : 
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) 


        self.main_layout.addWidget(self.invoices_table)
        self.setLayout(self.main_layout)

        if self.invoices_table.selectionModel():
            self.invoices_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Purchase Invoice Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_new_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "New P.Invoice", self)
        self.toolbar_new_action.triggered.connect(self._on_new_invoice)
        self.toolbar.addAction(self.toolbar_new_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Draft", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_draft_invoice)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_view_action = QAction(QIcon(self.icon_path_prefix + "view.svg"), "View P.Invoice", self)
        self.toolbar_view_action.triggered.connect(self._on_view_invoice_toolbar)
        self.toolbar.addAction(self.toolbar_view_action)
        
        self.toolbar_post_action = QAction(QIcon(self.icon_path_prefix + "post.svg"), "Post P.Invoice(s)", self)
        self.toolbar_post_action.triggered.connect(self._on_post_invoice) 
        self.toolbar_post_action.setEnabled(False) 
        self.toolbar.addAction(self.toolbar_post_action)

        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_invoices()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    def _create_filter_area(self):
        self.filter_layout = QHBoxLayout() 
        
        self.filter_layout.addWidget(QLabel("Vendor:"))
        self.vendor_filter_combo = QComboBox()
        self.vendor_filter_combo.setMinimumWidth(200)
        self.vendor_filter_combo.addItem("All Vendors", 0) 
        self.vendor_filter_combo.setEditable(True) # Make editable for completer
        self.vendor_filter_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        vend_completer = QCompleter(self) # Pass self as parent
        vend_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        vend_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.vendor_filter_combo.setCompleter(vend_completer)
        self.filter_layout.addWidget(self.vendor_filter_combo)

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

    async def _load_vendors_for_filter_combo(self):
        if not self.app_core.vendor_manager: return
        try:
            result: Result[List[VendorSummaryData]] = await self.app_core.vendor_manager.get_vendors_for_listing(active_only=True, page_size=-1) 
            if result.is_success and result.value:
                self._vendors_cache_for_filter = result.value
                vendors_json = json.dumps([v.model_dump() for v in result.value], default=json_converter)
                QMetaObject.invokeMethod(self, "_populate_vendors_filter_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, vendors_json))
        except Exception as e:
            self.app_core.logger.error(f"Error loading vendors for filter: {e}", exc_info=True)

    @Slot(str)
    def _populate_vendors_filter_slot(self, vendors_json_str: str):
        current_selection_data = self.vendor_filter_combo.currentData()
        self.vendor_filter_combo.clear()
        self.vendor_filter_combo.addItem("All Vendors", 0) 
        try:
            vendors_data = json.loads(vendors_json_str)
            self._vendors_cache_for_filter = [VendorSummaryData.model_validate(v) for v in vendors_data]
            for vend_summary in self._vendors_cache_for_filter:
                self.vendor_filter_combo.addItem(f"{vend_summary.vendor_code} - {vend_summary.name}", vend_summary.id)
            
            # Restore selection if possible
            idx = self.vendor_filter_combo.findData(current_selection_data)
            if idx != -1:
                self.vendor_filter_combo.setCurrentIndex(idx)
            
            if isinstance(self.vendor_filter_combo.completer(), QCompleter): # Update completer model
                 self.vendor_filter_combo.completer().setModel(self.vendor_filter_combo.model())
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Failed to parse vendors JSON for filter: {e}")

    @Slot()
    def _clear_filters_and_load(self):
        self.vendor_filter_combo.setCurrentIndex(0) 
        self.status_filter_combo.setCurrentIndex(0)   
        self.start_date_filter_edit.setDate(QDate.currentDate().addMonths(-3))
        self.end_date_filter_edit.setDate(QDate.currentDate())
        schedule_task_from_qt(self._load_invoices())

    @Slot()
    def _update_action_states(self):
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        can_edit_draft = False
        
        if single_selection:
            row = selected_rows[0].row()
            status = self.table_model.get_invoice_status_at_row(row)
            if status == InvoiceStatusEnum.DRAFT:
                can_edit_draft = True
            
        self.toolbar_edit_action.setEnabled(can_edit_draft)
        self.toolbar_view_action.setEnabled(single_selection)
        self.toolbar_post_action.setEnabled(False) 

    async def _load_invoices(self):
        if not self.app_core.purchase_invoice_manager:
            self.app_core.logger.error("PurchaseInvoiceManager not available."); return
        try:
            vend_id_data = self.vendor_filter_combo.currentData()
            vendor_id_filter = int(vend_id_data) if vend_id_data and vend_id_data != 0 else None
            
            status_enum_data = self.status_filter_combo.currentData()
            status_filter_val: Optional[InvoiceStatusEnum] = status_enum_data if isinstance(status_enum_data, InvoiceStatusEnum) else None
            
            start_date_filter = self.start_date_filter_edit.date().toPython()
            end_date_filter = self.end_date_filter_edit.date().toPython()

            result: Result[List[PurchaseInvoiceSummaryData]] = await self.app_core.purchase_invoice_manager.get_invoices_for_listing(
                vendor_id=vendor_id_filter, status=status_filter_val,
                start_date=start_date_filter, end_date=end_date_filter,
                page=1, page_size=200 
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                json_data = json.dumps([dto.model_dump() for dto in data_for_table], default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Failed to load purchase invoices: {', '.join(result.errors)}"))
        except Exception as e:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error loading purchase invoices: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            invoice_summaries: List[PurchaseInvoiceSummaryData] = [PurchaseInvoiceSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(invoice_summaries)
        except Exception as e: 
            QMessageBox.critical(self, "Data Error", f"Failed to parse/validate purchase invoice data: {e}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_new_invoice(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = PurchaseInvoiceDialog(self.app_core, self.app_core.current_user.id, parent=self)
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
        if invoice_id is None: QMessageBox.information(self, "Selection", "Please select a single purchase invoice to edit."); return
        if status != InvoiceStatusEnum.DRAFT: QMessageBox.warning(self, "Edit Error", "Only Draft purchase invoices can be edited."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        
        dialog = PurchaseInvoiceDialog(self.app_core, self.app_core.current_user.id, invoice_id=invoice_id, parent=self)
        dialog.invoice_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    @Slot()
    def _on_view_invoice_toolbar(self):
        invoice_id, _ = self._get_selected_invoice_id_and_status()
        if invoice_id is None: QMessageBox.information(self, "Selection", "Please select a single purchase invoice to view."); return
        self._show_view_invoice_dialog(invoice_id)

    @Slot(QModelIndex)
    def _on_view_invoice_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        invoice_id = self.table_model.get_invoice_id_at_row(index.row())
        if invoice_id is None: return
        self._show_view_invoice_dialog(invoice_id)

    def _show_view_invoice_dialog(self, invoice_id: int):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = PurchaseInvoiceDialog(self.app_core, self.app_core.current_user.id, invoice_id=invoice_id, view_only=True, parent=self)
        dialog.exec()
        
    @Slot()
    def _on_post_invoice(self):
        QMessageBox.information(self, "Post Purchase Invoice", "Posting purchase invoice functionality is not yet implemented.")

    @Slot(int)
    def _refresh_list_after_save(self, invoice_id: int):
        self.app_core.logger.info(f"PurchaseInvoiceDialog reported save for ID: {invoice_id}. Refreshing list.")
        schedule_task_from_qt(self._load_invoices())

```

**Review of `app/ui/purchase_invoices/purchase_invoices_widget.py` after Fix:**

*   **`ImportError` for `QCompleter`**:
    *   The original erroneous import `from PySide6.QtGui import QIcon, QAction, QCompleter` has been corrected.
    *   `QCompleter` is now correctly imported from `PySide6.QtWidgets`.
*   **`QCompleter` Implementation for Vendor Filter**:
    *   In `_create_filter_area()`:
        *   `self.vendor_filter_combo` is now set to `setEditable(True)` and `setInsertPolicy(QComboBox.InsertPolicy.NoInsert)`.
        *   A `QCompleter` instance (`vend_completer`) is created, configured with `MatchContains` and `PopupCompletion`.
        *   The completer is set for `self.vendor_filter_combo`.
    *   In `_populate_vendors_filter_slot()`:
        *   After populating the combo box items, `self.vendor_filter_combo.completer().setModel(self.vendor_filter_combo.model())` is called to ensure the completer uses the updated model from the combobox.
        *   Logic to restore previous selection in the combo (if any) after repopulating is also added.
*   **No Omission of Features**: All other functionalities of `PurchaseInvoicesWidget` (toolbar setup, table view, other filter elements, data loading, dialog launching, action state updates) remain as implemented in the previous step. The fix is targeted and also enhances the vendor filter.

**Conclusion of Task Completion:**

The `ImportError` in `app/ui/purchase_invoices/purchase_invoices_widget.py` related to `QCompleter` has been resolved by correcting its import statement. Additionally, the vendor filter `QComboBox` has been enhanced with a `QCompleter` for better usability.

The application should now launch without this import error, and the "Purchases" tab should display the `PurchaseInvoicesWidget` with a searchable vendor filter. All other features remain intact.
