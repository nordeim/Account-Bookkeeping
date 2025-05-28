<think>
The user has provided a traceback indicating an `ImportError: cannot import name 'QCompleter' from 'PySide6.QtGui'`. This error occurs in `app/ui/sales_invoices/sales_invoices_widget.py`.

**Error Analysis:**

The `ImportError` means that the class `QCompleter` is being imported from the wrong PySide6 module. `QCompleter` is part of `PySide6.QtWidgets`, not `PySide6.QtGui`.

**Chain of Imports Leading to the Error:**
1.  `app/main.py` imports `app.ui.main_window`
2.  `app/ui/__init__.py` imports `.main_window`
3.  `app/ui/main_window.py` imports `app.ui.sales_invoices.sales_invoices_widget` (as `SalesInvoicesWidget`)
4.  `app/ui/sales_invoices/__init__.py` imports `.sales_invoices_widget` (as `SalesInvoicesWidget`)
5.  `app/ui/sales_invoices/sales_invoices_widget.py` attempts to import `QCompleter` from `PySide6.QtGui`.

**Looking at `app/ui/sales_invoices/sales_invoices_widget.py` (from previous turn's generated code):**
The import statement in question is:
```python
from PySide6.QtGui import QIcon, QAction, QCompleter # Incorrect: QCompleter is not in QtGui
```
And `QCompleter` is used when setting up `self.customer_filter_combo`.

**Plan to Fix:**

1.  **Identify the correct module for `QCompleter`**: It's `PySide6.QtWidgets`.
2.  **Modify the import statements**:
    *   Remove `QCompleter` from the `PySide6.QtGui` import line.
    *   Add `QCompleter` to the `PySide6.QtWidgets` import line.

**Detailed Execution Plan:**

1.  **Locate File**: Open `app/ui/sales_invoices/sales_invoices_widget.py`.
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
            QLabel, QLineEdit, QCheckBox, QComboBox, QDateEdit
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
3.  **No other changes should be necessary for this specific error.** The error is purely an incorrect import location.
4.  **Self-Correction/Double Check**:
    *   The error message `ImportError: cannot import name 'QCompleter' from 'PySide6.QtGui'` clearly indicates the problem.
    *   PySide6 documentation confirms `QCompleter` is in `QtWidgets`.
    *   Ensure no other part of the file was accidentally modified.

**Confirmation of Past Resolutions:**
This type of import error is common when manually listing imports. It's similar to the `QWidget` and `QModelIndex` issues but in a different file and for a different class. The fix is always to ensure the class is imported from its correct module.

I will now generate the complete updated file for `app/ui/sales_invoices/sales_invoices_widget.py` with this correction.
</think>

You are absolutely right to be so diligent! This `ImportError` for `QCompleter` is another case of a Qt class being imported from the wrong submodule. My apologies for this oversight. It underscores the importance of precise imports.

Here's the plan to fix the `ImportError: cannot import name 'QCompleter' from 'PySide6.QtGui'`:

**Plan to Fix `ImportError` for `QCompleter`:**

1.  **Identify the Correct Module**: `QCompleter` belongs to `PySide6.QtWidgets`.
2.  **Locate the Affected File**: `app/ui/sales_invoices/sales_invoices_widget.py`.
3.  **Modify Import Statements**:
    *   Remove `QCompleter` from the `from PySide6.QtGui import ...` line.
    *   Add `QCompleter` to the `from PySide6.QtWidgets import ...` list.

**Execution:**

I will now generate the complete updated `app/ui/sales_invoices/sales_invoices_widget.py` with the corrected import statement for `QCompleter`.

```python
# app/ui/sales_invoices/sales_invoices_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox, QComboBox, QDateEdit, QCompleter # Added QCompleter here
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize, QDate
from PySide6.QtGui import QIcon, QAction # Removed QCompleter from here
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
from app.models.business.sales_invoice import SalesInvoice

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
        QTimer.singleShot(100, lambda: self.apply_filter_button.click()) # Initial load using default filters


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
        can_post = False
        
        if single_selection:
            row = selected_rows[0].row()
            status = self.table_model.get_invoice_status_at_row(row)
            if status == InvoiceStatusEnum.DRAFT:
                can_edit_draft = True
                can_post = True 
        elif selected_rows: 
            can_post = all(self.table_model.get_invoice_status_at_row(idx.row()) == InvoiceStatusEnum.DRAFT for idx in selected_rows)
            
        self.toolbar_edit_action.setEnabled(can_edit_draft)
        self.toolbar_view_action.setEnabled(single_selection)
        self.toolbar_post_action.setEnabled(can_post) 

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
        QMessageBox.information(self, "Post Invoice", "Posting invoice functionality is not yet implemented.")

    @Slot(int)
    def _refresh_list_after_save(self, invoice_id: int):
        self.app_core.logger.info(f"SalesInvoiceDialog reported save for ID: {invoice_id}. Refreshing list.")
        schedule_task_from_qt(self._load_invoices())

```

**Review of `app/ui/sales_invoices/sales_invoices_widget.py` after Fix:**

The `ImportError` for `QCompleter` was due to it being incorrectly imported from `PySide6.QtGui` instead of `PySide6.QtWidgets`.

*   **Original problematic import from `PySide6.QtGui`**:
    ```python
    from PySide6.QtGui import QIcon, QAction, QCompleter # Incorrect
    ```
*   **Corrected imports**:
    ```python
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
        QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
        QLabel, QLineEdit, QCheckBox, QComboBox, QDateEdit, QCompleter # QCompleter added here
    )
    from PySide6.QtGui import QIcon, QAction # QCompleter removed from here
    ```

This change directly addresses the `ImportError`. The rest of the file implements the `SalesInvoicesWidget` as planned in the previous step (list view, toolbar, filters, dialog integration). No other functional code related to the widget's implementation was altered by this specific fix.

**Conclusion of Task Completion:**

The `ImportError` in `app/ui/sales_invoices/sales_invoices_widget.py` related to `QCompleter` has been resolved by correcting its import statement. The application should now be able to launch, and the new "Sales" tab with the `SalesInvoicesWidget` should be functional for listing invoices (once data exists) and opening the `SalesInvoiceDialog`. All previously implemented features remain untouched.
