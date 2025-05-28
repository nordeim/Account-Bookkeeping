<think>
The application continues to launch and shut down successfully, indicating that the extensive changes to `SalesInvoiceDialog` (Part 1 and Part 2) were integrated without breaking the core application lifecycle.

**Current Project Status Recap:**

*   **Backend for Sales Invoice Management (Drafts)**: Complete.
*   **Frontend UI for Sales Invoicing (`SalesInvoiceDialog`)**:
    *   Data Loading & Basic Line Management: Complete (Part 1).
    *   Calculation Logic & Saving Drafts: Complete (Part 2).
*   All previously implemented features remain stable.

**Next Step Identification (from Roadmap):**

The roadmap items for "Current Focus / Short-term" were:
1.  **Sales Invoicing**: Complete UI for listing, viewing, and managing Sales Invoices. Implement posting logic (JE creation).
2.  **Refine Reporting**: Enhance on-screen display and export options for financial reports.
3.  **User and Role Management UI**: Add UI in Settings for managing users, roles, and permissions.

We have made significant progress on item 1 by implementing the `SalesInvoiceDialog` for creating/editing drafts. The next logical step within this item is to create the main **`SalesInvoicesWidget`** for listing, viewing, and managing these invoices. The "posting logic" part of this item is a larger backend task that should follow after the list view and basic management UI is in place.

So, the plan for this turn is:
**Implement `SalesInvoicesWidget` for listing sales invoices and integrating `SalesInvoiceDialog`.**

**Objective:**
Create a new widget `app/ui/sales_invoices/sales_invoices_widget.py` that:
*   Displays a list of sales invoices using `SalesInvoiceTableModel`.
*   Provides a toolbar with actions for "New Invoice", "Edit Draft Invoice", "View Invoice".
*   Includes basic filtering capabilities (e.g., by customer, status, date range).
*   Launches `SalesInvoiceDialog` for creating new invoices or editing/viewing existing ones.
*   Refreshes its list when an invoice is saved via the dialog.

**Detailed Plan & Checklist:**

1.  **Create `app/ui/sales_invoices/sales_invoices_widget.py`**:
    *   [ ] Define `SalesInvoicesWidget(QWidget)`.
    *   [ ] `__init__`: Initialize `app_core`, UI elements.
    *   [ ] `_init_ui()`:
        *   Set up main layout (e.g., `QVBoxLayout`).
        *   Call `_create_toolbar()`.
        *   Call `_create_filter_area()`.
        *   Create `QTableView` (`self.invoices_table`).
        *   Instantiate `SalesInvoiceTableModel` (`self.table_model`) and set it to the table.
        *   Configure table properties (selection behavior, alternating row colors, header modes, hide ID column, stretch "Customer" column).
        *   Connect `self.invoices_table.doubleClicked` to an "edit/view" slot.
        *   Connect `self.invoices_table.selectionModel().selectionChanged` to `_update_action_states`.
    *   [ ] `_create_toolbar()`:
        *   Add actions: "New Invoice", "Edit Draft", "View Invoice", "Refresh List".
        *   Connect actions to respective slots.
    *   [ ] `_create_filter_area()`:
        *   Add `QComboBox` for Customer (populate async).
        *   Add `QComboBox` for Status (Draft, Approved, Paid, etc., from `InvoiceStatusEnum`).
        *   Add `QDateEdit` for Start Date and End Date.
        *   Add "Apply Filter" and "Clear Filter" buttons.
    *   [ ] Implement `_load_customers_for_filter_combo()` async method and corresponding `_populate_customers_filter_slot`.
    *   [ ] Implement `_load_invoices()` async method:
        *   Get filter values from UI controls.
        *   Call `self.app_core.sales_invoice_manager.get_invoices_for_listing()` with filter parameters.
        *   Serialize `List[SalesInvoiceSummaryData]` to JSON.
        *   Call `_update_table_model_slot(json_data)` via `QMetaObject`.
    *   [ ] Implement `_update_table_model_slot(json_data_str)`:
        *   Parse JSON to `List[SalesInvoiceSummaryData]`.
        *   Call `self.table_model.update_data()`.
        *   Call `_update_action_states()`.
    *   [ ] Implement action slots:
        *   `_on_new_invoice()`: Launch `SalesInvoiceDialog` (modal). Connect `invoice_saved` signal to `_refresh_list_after_save`.
        *   `_on_edit_draft_invoice()`: Get selected invoice ID. If status is "Draft", launch `SalesInvoiceDialog` in edit mode. Connect `invoice_saved`.
        *   `_on_view_invoice()`: Get selected invoice ID. Launch `SalesInvoiceDialog` in `view_only=True` mode.
        *   `_refresh_list_after_save(invoice_id: int)`: Calls `_load_invoices`.
    *   [ ] Implement `_update_action_states()`: Enable/disable toolbar actions based on selection and invoice status.
    *   [ ] Initial data load: Call `_load_customers_for_filter_combo` and then `_load_invoices` (or trigger via "Apply Filter" button click).

2.  **Update `app/ui/main_window.py`**:
    *   [ ] Import `SalesInvoicesWidget`.
    *   [ ] Instantiate `SalesInvoicesWidget`.
    *   [ ] Add a new tab "Sales Invoices" (or similar) to `self.tab_widget` for this new widget.
    *   [ ] Add a corresponding icon (e.g., `transactions.svg` or create a new `invoice.svg`).

3.  **Update `app/resources/resources.qrc` (if a new icon is used)**:
    *   [ ] Add an entry for the new sales invoice icon if one is created. If reusing `transactions.svg`, no change needed here other than ensuring it's already listed. For now, let's assume we can reuse `transactions.svg` or a generic document icon initially.

4.  **Update `app/ui/sales_invoices/__init__.py`**:
    *   [ ] Add `SalesInvoicesWidget` to `__all__`.

This plan focuses on the UI for listing and managing invoices. The "posting logic" part of the roadmap item is a significant backend change (JE creation, inventory updates, etc.) and will be tackled after this UI is functional.
</think>

Okay, I will proceed with implementing the `SalesInvoicesWidget` and integrating it into the application. This aligns with the "Current Focus / Short-term" roadmap item of completing the UI for listing, viewing, and managing Sales Invoices.

Here's the execution plan:

**Execution Plan for Sales Invoicing UI (List View):**

1.  **Create `app/ui/sales_invoices/sales_invoices_widget.py`**:
    *   Define the `SalesInvoicesWidget` class inheriting from `QWidget`.
    *   Implement `__init__` to store `app_core` and call `_init_ui`.
    *   Implement `_init_ui` to set up the main layout, toolbar, filter area, and `QTableView`.
        *   Instantiate `SalesInvoiceTableModel` and assign it to the table.
        *   Configure table properties (selection, sorting, column visibility/sizing).
        *   Connect table signals (`doubleClicked`, `selectionChanged`).
    *   Implement `_create_toolbar` with actions for "New", "Edit Draft", "View", "Refresh".
    *   Implement `_create_filter_area` with `QComboBox` for Customer (initially empty or with a placeholder), `QComboBox` for Status, `QDateEdit` for Start/End Dates, and "Apply"/"Clear" filter buttons.
    *   Implement `_load_customers_for_filter_combo` (async) to fetch active customers and `_populate_customers_filter_slot` to update the customer filter `QComboBox`.
    *   Implement `_load_invoices` (async) to get filter criteria and call `app_core.sales_invoice_manager.get_invoices_for_listing`. Serialize results to JSON for the UI update slot.
    *   Implement `_update_table_model_slot` to parse JSON and update `self.table_model`.
    *   Implement slots for toolbar actions (`_on_new_invoice`, `_on_edit_draft_invoice`, `_on_view_invoice`). These will launch `SalesInvoiceDialog`.
        *   Connect the `invoice_saved` signal from `SalesInvoiceDialog` to a slot (`_refresh_list_after_save`) in `SalesInvoicesWidget` to reload the list.
    *   Implement `_update_action_states` to enable/disable toolbar buttons based on table selection and invoice status.
    *   Trigger initial data load (`_load_customers_for_filter_combo` then `_load_invoices`).
    *   **Checklist**: [ ] Widget defined. [ ] Toolbar created. [ ] Filter area created. [ ] TableView setup. [ ] Model assigned. [ ] Signals connected. [ ] Customer combo populates. [ ] Invoice list loads and updates. [ ] Action slots launch dialog. [ ] Dialog save refreshes list. [ ] Action states update.

2.  **Update `app/ui/main_window.py`**:
    *   Import `SalesInvoicesWidget`.
    *   In `_add_module_tabs`, instantiate `SalesInvoicesWidget` and add it as a new tab (e.g., "Sales"). Choose an appropriate icon (e.g., `transactions.svg` or reuse `product.svg` for now if an "invoice" icon isn't available).
    *   **Checklist**: [ ] Import added. [ ] Widget instantiated. [ ] Tab added.

3.  **Update `app/resources/resources.qrc`**:
    *   If a new specific icon for "sales invoice" is created and used, add its alias here. For now, I will reuse an existing icon like `transactions.svg` or `product.svg` (if suitable, or fallback to no icon for the tab). Assuming `transactions.svg` as a placeholder.
    *   **Checklist**: [ ] (If new icon) Entry added.

4.  **Update `app/ui/sales_invoices/__init__.py`**:
    *   Add `SalesInvoicesWidget` to the `__all__` list.
    *   **Checklist**: [ ] `__all__` list updated.

I will now generate the code for these files.

---
**1. Create `app/ui/sales_invoices/sales_invoices_widget.py`**
```python
# app/ui/sales_invoices/sales_invoices_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox, QComboBox, QDateEdit
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize, QDate
from PySide6.QtGui import QIcon, QAction, QCompleter
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
        self.main_layout.addLayout(self.filter_layout) # Add filter_layout to main_layout

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
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) # Fallback: stretch 4th visible (Customer)


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
        
        # Placeholder for Post Action
        self.toolbar_post_action = QAction(QIcon(self.icon_path_prefix + "post.svg"), "Post Invoice(s)", self)
        self.toolbar_post_action.triggered.connect(self._on_post_invoice) # To be implemented
        self.toolbar_post_action.setEnabled(False) # Disabled for now
        self.toolbar.addAction(self.toolbar_post_action)

        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_invoices()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    def _create_filter_area(self):
        self.filter_layout = QHBoxLayout() # Make it an instance variable
        
        self.filter_layout.addWidget(QLabel("Customer:"))
        self.customer_filter_combo = QComboBox()
        self.customer_filter_combo.setMinimumWidth(200)
        self.customer_filter_combo.addItem("All Customers", 0) # Placeholder for "All"
        self.filter_layout.addWidget(self.customer_filter_combo)

        self.filter_layout.addWidget(QLabel("Status:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem("All Statuses", None) # Data is None for all
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
            result: Result[List[CustomerSummaryData]] = await self.app_core.customer_manager.get_customers_for_listing(active_only=True, page_size=-1) # Get all active
            if result.is_success and result.value:
                self._customers_cache_for_filter = result.value
                # Serialize for thread-safe update
                customers_json = json.dumps([c.model_dump() for c in result.value], default=json_converter)
                QMetaObject.invokeMethod(self, "_populate_customers_filter_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, customers_json))
        except Exception as e:
            self.app_core.logger.error(f"Error loading customers for filter: {e}", exc_info=True)

    @Slot(str)
    def _populate_customers_filter_slot(self, customers_json_str: str):
        self.customer_filter_combo.clear()
        self.customer_filter_combo.addItem("All Customers", 0) # UserData for 'All' is 0 or None
        try:
            customers_data = json.loads(customers_json_str)
            self._customers_cache_for_filter = [CustomerSummaryData.model_validate(c) for c in customers_data]
            for cust_summary in self._customers_cache_for_filter:
                self.customer_filter_combo.addItem(f"{cust_summary.customer_code} - {cust_summary.name}", cust_summary.id)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Failed to parse customers JSON for filter: {e}")

    @Slot()
    def _clear_filters_and_load(self):
        self.customer_filter_combo.setCurrentIndex(0) # "All Customers"
        self.status_filter_combo.setCurrentIndex(0)   # "All Statuses"
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
                can_post = True # Can post a single draft
        elif selected_rows: # Multiple selected
            can_post = all(self.table_model.get_invoice_status_at_row(idx.row()) == InvoiceStatusEnum.DRAFT for idx in selected_rows)
            
        self.toolbar_edit_action.setEnabled(can_edit_draft)
        self.toolbar_view_action.setEnabled(single_selection)
        self.toolbar_post_action.setEnabled(can_post) # Enable if any selection can be posted

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
                page=1, page_size=200 # MVP: Load up to 200, no UI pagination yet
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
        except Exception as e: # Broader catch for Pydantic errors too
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
        # This will handle posting selected draft invoices.
        # For now, a placeholder message.
        QMessageBox.information(self, "Post Invoice", "Posting invoice functionality is not yet implemented.")


    @Slot(int)
    def _refresh_list_after_save(self, invoice_id: int):
        self.app_core.logger.info(f"SalesInvoiceDialog reported save for ID: {invoice_id}. Refreshing list.")
        schedule_task_from_qt(self._load_invoices())

```

---
**2. Update `app/ui/main_window.py`**
```python
# app/ui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QStatusBar, 
    QVBoxLayout, QWidget, QMessageBox, QLabel 
)
from PySide6.QtGui import QIcon, QKeySequence, QAction 
from PySide6.QtCore import Qt, QSettings, Signal, Slot, QCoreApplication, QSize 

from app.ui.dashboard.dashboard_widget import DashboardWidget
from app.ui.accounting.accounting_widget import AccountingWidget
from app.ui.customers.customers_widget import CustomersWidget
from app.ui.vendors.vendors_widget import VendorsWidget
from app.ui.products.products_widget import ProductsWidget
from app.ui.sales_invoices.sales_invoices_widget import SalesInvoicesWidget # New Import
from app.ui.banking.banking_widget import BankingWidget
from app.ui.reports.reports_widget import ReportsWidget
from app.ui.settings.settings_widget import SettingsWidget
from app.core.application_core import ApplicationCore

class MainWindow(QMainWindow):
    def __init__(self, app_core: ApplicationCore):
        super().__init__()
        self.app_core = app_core
        
        self.setWindowTitle(f"{QCoreApplication.applicationName()} - {QCoreApplication.applicationVersion()}")
        self.setMinimumSize(1024, 768)
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass

        settings = QSettings() 
        if settings.contains("MainWindow/geometry"):
            self.restoreGeometry(settings.value("MainWindow/geometry")) 
        else:
            self.resize(1280, 800)
        
        self._init_ui()
        
        if settings.contains("MainWindow/state"):
            self.restoreState(settings.value("MainWindow/state")) 
    
    def _init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self._create_toolbar()
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(True)
        self.main_layout.addWidget(self.tab_widget)
        
        self._add_module_tabs()
        self._create_status_bar()
        self._create_actions()
        self._create_menus()
    
    def _create_toolbar(self):
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setObjectName("MainToolbar") 
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24)) 
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar) 
    
    def _add_module_tabs(self):
        self.dashboard_widget = DashboardWidget(self.app_core)
        self.tab_widget.addTab(self.dashboard_widget, QIcon(self.icon_path_prefix + "dashboard.svg"), "Dashboard")
        
        self.accounting_widget = AccountingWidget(self.app_core)
        self.tab_widget.addTab(self.accounting_widget, QIcon(self.icon_path_prefix + "accounting.svg"), "Accounting")
        
        # New Sales Invoices Tab
        self.sales_invoices_widget = SalesInvoicesWidget(self.app_core)
        self.tab_widget.addTab(self.sales_invoices_widget, QIcon(self.icon_path_prefix + "transactions.svg"), "Sales") # Using transactions.svg for now

        self.customers_widget = CustomersWidget(self.app_core)
        self.tab_widget.addTab(self.customers_widget, QIcon(self.icon_path_prefix + "customers.svg"), "Customers")
        
        self.vendors_widget = VendorsWidget(self.app_core)
        self.tab_widget.addTab(self.vendors_widget, QIcon(self.icon_path_prefix + "vendors.svg"), "Vendors")

        self.products_widget = ProductsWidget(self.app_core) 
        self.tab_widget.addTab(self.products_widget, QIcon(self.icon_path_prefix + "product.svg"), "Products & Services")
        
        self.banking_widget = BankingWidget(self.app_core)
        self.tab_widget.addTab(self.banking_widget, QIcon(self.icon_path_prefix + "banking.svg"), "Banking")
        
        self.reports_widget = ReportsWidget(self.app_core)
        self.tab_widget.addTab(self.reports_widget, QIcon(self.icon_path_prefix + "reports.svg"), "Reports")
        
        self.settings_widget = SettingsWidget(self.app_core)
        self.tab_widget.addTab(self.settings_widget, QIcon(self.icon_path_prefix + "settings.svg"), "Settings")
    
    def _create_status_bar(self):
        self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready"); self.status_bar.addWidget(self.status_label, 1) 
        user_text = "User: Guest"; 
        if self.app_core.current_user: user_text = f"User: {self.app_core.current_user.username}"
        self.user_label = QLabel(user_text); self.status_bar.addPermanentWidget(self.user_label)
        self.version_label = QLabel(f"Version: {QCoreApplication.applicationVersion()}"); self.status_bar.addPermanentWidget(self.version_label)

    
    def _create_actions(self):
        self.new_company_action = QAction(QIcon(self.icon_path_prefix + "new_company.svg"), "New Company...", self); self.new_company_action.setShortcut(QKeySequence(QKeySequence.StandardKey.New)); self.new_company_action.triggered.connect(self.on_new_company)
        self.open_company_action = QAction(QIcon(self.icon_path_prefix + "open_company.svg"), "Open Company...", self); self.open_company_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Open)); self.open_company_action.triggered.connect(self.on_open_company)
        self.backup_action = QAction(QIcon(self.icon_path_prefix + "backup.svg"), "Backup Data...", self); self.backup_action.triggered.connect(self.on_backup)
        self.restore_action = QAction(QIcon(self.icon_path_prefix + "restore.svg"), "Restore Data...", self); self.restore_action.triggered.connect(self.on_restore)
        self.exit_action = QAction(QIcon(self.icon_path_prefix + "exit.svg"), "Exit", self); self.exit_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Quit)); self.exit_action.triggered.connect(self.close) 
        self.preferences_action = QAction(QIcon(self.icon_path_prefix + "preferences.svg"), "Preferences...", self); self.preferences_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Preferences)); self.preferences_action.triggered.connect(self.on_preferences)
        self.help_contents_action = QAction(QIcon(self.icon_path_prefix + "help.svg"), "Help Contents", self); self.help_contents_action.setShortcut(QKeySequence(QKeySequence.StandardKey.HelpContents)); self.help_contents_action.triggered.connect(self.on_help_contents)
        self.about_action = QAction(QIcon(self.icon_path_prefix + "about.svg"), "About " + QCoreApplication.applicationName(), self); self.about_action.triggered.connect(self.on_about)

    def _create_menus(self):
        self.file_menu = self.menuBar().addMenu("&File"); self.file_menu.addAction(self.new_company_action); self.file_menu.addAction(self.open_company_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.backup_action); self.file_menu.addAction(self.restore_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.exit_action)
        self.edit_menu = self.menuBar().addMenu("&Edit"); self.edit_menu.addAction(self.preferences_action)
        self.view_menu = self.menuBar().addMenu("&View"); self.tools_menu = self.menuBar().addMenu("&Tools")
        self.help_menu = self.menuBar().addMenu("&Help"); self.help_menu.addAction(self.help_contents_action); self.help_menu.addSeparator(); self.help_menu.addAction(self.about_action)
        self.toolbar.addAction(self.new_company_action); self.toolbar.addAction(self.open_company_action); self.toolbar.addSeparator(); self.toolbar.addAction(self.backup_action); self.toolbar.addAction(self.preferences_action)
    
    @Slot()
    def on_new_company(self): QMessageBox.information(self, "New Company", "New company wizard not yet implemented.")
    @Slot()
    def on_open_company(self): QMessageBox.information(self, "Open Company", "Open company dialog not yet implemented.")
    @Slot()
    def on_backup(self): QMessageBox.information(self, "Backup Data", "Backup functionality not yet implemented.")
    @Slot()
    def on_restore(self): QMessageBox.information(self, "Restore Data", "Restore functionality not yet implemented.")
    @Slot()
    def on_preferences(self): 
        settings_tab_index = -1
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) == self.settings_widget:
                settings_tab_index = i
                break
        if settings_tab_index != -1:
            self.tab_widget.setCurrentIndex(settings_tab_index)
        else:
            QMessageBox.information(self, "Preferences", "Preferences (Settings Tab) not found or full dialog not yet implemented.")

    @Slot()
    def on_help_contents(self): QMessageBox.information(self, "Help", "Help system not yet implemented.")
    @Slot()
    def on_about(self): QMessageBox.about(self, f"About {QCoreApplication.applicationName()}", f"{QCoreApplication.applicationName()} {QCoreApplication.applicationVersion()}\n\nA comprehensive bookkeeping application for Singapore small businesses.\n\n© 2024 {QCoreApplication.organizationName()}"); 
    def closeEvent(self, event): 
        settings = QSettings(); settings.setValue("MainWindow/geometry", self.saveGeometry()); settings.setValue("MainWindow/state", self.saveState()); settings.sync()
        reply = QMessageBox.question(self, "Confirm Exit", "Are you sure you want to exit?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes: event.accept() 
        else: event.ignore()

```

---
**3. Update `app/resources/resources.qrc` (No changes needed if reusing an existing icon for "Sales" tab)**

The icon `transactions.svg` is already listed in `resources.qrc`. If a new, specific "invoice.svg" or "sales.svg" were created, it would need to be added here. For this step, we'll reuse `transactions.svg`.

---
**4. Update `app/ui/sales_invoices/__init__.py`**
```python
# app/ui/sales_invoices/__init__.py    
from .sales_invoice_table_model import SalesInvoiceTableModel
from .sales_invoice_dialog import SalesInvoiceDialog 
from .sales_invoices_widget import SalesInvoicesWidget # New import

__all__ = [
    "SalesInvoiceTableModel",
    "SalesInvoiceDialog", 
    "SalesInvoicesWidget", # Added to __all__
]

```

**Summary of Task Completion:**

1.  **`app/ui/sales_invoices/sales_invoices_widget.py`**: A new file has been created. It implements the list view for sales invoices, including:
    *   Toolbar for actions (New, Edit Draft, View, Post (stubbed), Refresh).
    *   Filter area (Customer, Status, Date Range).
    *   Asynchronous loading of customers for the filter combobox.
    *   Asynchronous loading of invoice summaries using `SalesInvoiceManager`.
    *   `QTableView` with `SalesInvoiceTableModel` to display the data.
    *   Integration with `SalesInvoiceDialog` for creating new invoices and editing/viewing existing ones.
    *   Dynamic enabling/disabling of actions based on selection and invoice status.

2.  **`app/ui/main_window.py`**:
    *   Imported `SalesInvoicesWidget`.
    *   Instantiated `SalesInvoicesWidget`.
    *   Added a new "Sales" tab to the main application window, using `transactions.svg` as a placeholder icon. The tab is placed after "Accounting" and before "Customers" for logical flow.

3.  **`app/resources/resources.qrc`**: No direct changes made in this step, as an existing icon (`transactions.svg`) was reused for the new "Sales" tab.

4.  **`app/ui/sales_invoices/__init__.py`**:
    *   Added `SalesInvoicesWidget` to the `__all__` list, making it available for import.

**Validation and Review:**

*   **Line-by-line comparison (mental simulation)**:
    *   `SalesInvoicesWidget`: The structure aligns with other module widgets (e.g., `CustomersWidget`). Asynchronous data loading, UI updates via slots, and dialog integration follow established patterns. Filter logic and action state updates are included.
    *   `MainWindow`: The integration of the new tab is straightforward and follows the pattern of other module tabs.
    *   `__init__.py`: Correctly updated to export the new widget.
*   **No Omission of Features**: This step adds new files and modifies existing ones to incorporate the new feature. No existing features were touched in a way that would cause omission.
*   **Regression Prevention**: The changes are modular. The new widget is self-contained. `MainWindow` changes are additive. The risk of regression in other modules is low.
*   **Adherence to Plan**: All items in the checklist for this stage have been addressed.

The application should now have a functional "Sales" tab that lists sales invoices and allows users to open the `SalesInvoiceDialog` to create new drafts or view/edit existing ones (drafts only for editing). The "Post" functionality for invoices is stubbed in the UI, as the backend logic for posting (JE creation, etc.) is planned for a subsequent step.
