<think>
The application is stable, and the documentation (`README.md` and `TDS v6.md`) has been updated to reflect the completion of basic Vendor Management. This is a solid state.

The user wants to proceed with the "next step" based on the "Current Focus / Short-term" roadmap I previously suggested in the README. The items were:
1.  **Product/Service Management UI**: Implement basic UI (List, Add, Edit, Toggle Active) for products and services, using the established backend.
2.  **Refine Reporting**: Improve on-screen display of financial reports (e.g., explore `QTableView`).
3.  **User and Role Management UI**: Add UI in Settings for managing users, roles, and permissions.

**Choosing the Next Feature from the Short-Term Roadmap:**

*   **Product/Service Management UI**: The backend for this (DTOs, Service, Manager) is already complete. Implementing the UI (TableModel, Dialog, Widget) would follow the now well-established pattern from Customer and Vendor modules. This is a natural continuation and completes another core data entity management feature, which is essential for future invoicing.
*   **Refine Reporting**: While important for UX, it's an enhancement of existing functionality rather than adding a new core capability.
*   **User and Role Management UI**: This is important for administration and security. The backend models (`User`, `Role`, `Permission`) and `SecurityManager` are in place. This UI would likely reside in the `SettingsWidget`.

**Decision for this Turn:**
Implementing the **Product/Service Management UI** is the most logical next step. It completes the "Products & Services" module (at least for basic CRUD), builds upon the just-completed backend for it, and leverages the UI patterns already used for Customers and Vendors.

**Plan for this Turn: Implement Product/Service Management UI (Phase B)**

This will complete the "Basic Product/Service Management Module" by adding its frontend components.
*   **Phase A: Backend for Product/Service Management (Completed)**
*   **Phase B: Frontend UI for Product/Service Management (Current Focus)**
    *   B1. `ProductTableModel` (Already created in a previous step).
    *   B2. `ProductDialog` (Already created in a previous step).
    *   B3. Enhance `ProductsWidget` (from stub to functional) and integrate into `MainWindow`. (This is the primary task for this turn).

**Detailed Plan & Checklist (Phase B - Product/Service UI):**

**B3. Create/Enhance `app/ui/products/products_widget.py`**
   *   **Goal:** A functional widget for product/service management, integrating `ProductTableModel` and `ProductDialog`.
   *   **File to Create/Update:** `app/ui/products/products_widget.py` (This file likely doesn't exist yet or is a minimal stub as per `project_file_structure.txt` which often lists placeholders).
   *   **Checklist & Tasks:**
        *   [ ] Define `ProductsWidget(QWidget)`.
        *   [ ] `__init__`: Store `app_core`, init `icon_path_prefix`, call `_init_ui`, schedule `_load_products`.
        *   [ ] `_init_ui()`:
            *   `QVBoxLayout`, `QToolBar`.
            *   Filter UI: `QLineEdit` for search, `QComboBox` for Product Type (populated from `ProductTypeEnum`), `QCheckBox` for "Show Inactive".
            *   `QTableView` (`self.products_table`), instantiate `self.table_model = ProductTableModel()`.
            *   Set model, configure table (column hiding for "ID", column resizing, sorting).
            *   Connect signals (`selectionChanged`, `doubleClicked`).
        *   [ ] `_create_toolbar()`: Actions "Add Product/Service", "Edit", "Toggle Active", "Refresh List".
        *   [ ] `_update_action_states()`: Enable/disable actions based on selection.
        *   [ ] `_load_products()`: Get filters (search term, product type, active status). Call `app_core.product_manager.get_products_for_listing()`. Update model via `_update_table_model_slot`.
        *   [ ] `_update_table_model_slot(json_data_str)`: Parse JSON to `List[ProductSummaryData]`, update table model.
        *   [ ] Action Handlers: `_on_add_product`, `_on_edit_product`, `_on_toggle_active_status`, `_on_refresh_products`, `_on_view_product_double_click`. These will launch `ProductDialog` or call `ProductManager` methods.
        *   [ ] Helper `_get_selected_product_id()`.

**Supporting Steps (Updates to existing files):**

1.  **Update `app/ui/products/__init__.py`**:
    *   **Goal:** Export the new `ProductsWidget`.
    *   **File to Update:** `app/ui/products/__init__.py`
    *   **Checklist & Tasks:**
        *   [ ] Add `from .products_widget import ProductsWidget`.
        *   [ ] Add `ProductsWidget` to `__all__`.

2.  **Update `app/ui/main_window.py`**:
    *   **Goal:** Add a "Products & Services" tab using the new `ProductsWidget`.
    *   **File to Update:** `app/ui/main_window.py`
    *   **Checklist & Tasks:**
        *   [ ] Import `from app.ui.products.products_widget import ProductsWidget`.
        *   [ ] In `_add_module_tabs()`, instantiate `self.products_widget = ProductsWidget(self.app_core)`.
        *   [ ] Add the tab: `self.tab_widget.addTab(self.products_widget, QIcon(self.icon_path_prefix + "product.svg"), "Products & Services")`. (The `product.svg` icon was created in a previous step).

This plan focuses on creating the main list view and integrating the previously created dialog and table model for products/services.
</think>

This is great! The application's continued stability is a strong foundation for adding new features.

As per your request and our roadmap, the next logical step is to implement the **Product/Service Management UI**. The backend for this module (DTOs, Service, Manager) is already complete and integrated into `ApplicationCore`. Phase B of this module involves creating the frontend components.

We have already created the foundational `ProductTableModel` and `ProductDialog` in previous steps. The main task now is to create/enhance `ProductsWidget` to use these components and integrate it into the `MainWindow`.

**Enhancement Execution Plan: Implement Product/Service Management UI (Phase B3)**

**Overall Objective:** Create a functional `ProductsWidget` that allows users to list, filter, add, edit, and manage the active status of products and services, and add this widget as a new tab in the main application window.

---
**1. Create/Update `app/ui/products/products_widget.py`**

**Goal:** The main UI for product/service management, providing a table view, filtering, and action buttons.

```python
# app/ui/products/products_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox, QComboBox # Added QComboBox for type filter
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.products.product_table_model import ProductTableModel 
from app.ui.products.product_dialog import ProductDialog 
from app.utils.pydantic_models import ProductSummaryData 
from app.common.enums import ProductTypeEnum # For product type filter
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.product import Product # For Result type hint from manager

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class ProductsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for ProductsWidget.")
        except ImportError:
            self.app_core.logger.info("ProductsWidget: Compiled Qt resources not found. Using direct file paths.")
            pass
        
        self._init_ui()
        # Initial load triggered by filter button/refresh action to respect default filters
        QTimer.singleShot(0, lambda: self.toolbar_refresh_action.trigger() if hasattr(self, 'toolbar_refresh_action') else schedule_task_from_qt(self._load_products()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Code, Name, Description...")
        self.search_edit.returnPressed.connect(self.toolbar_refresh_action.trigger)
        filter_layout.addWidget(self.search_edit)

        filter_layout.addWidget(QLabel("Type:"))
        self.product_type_filter_combo = QComboBox()
        self.product_type_filter_combo.addItem("All Types", None) # User data is None
        for pt_enum in ProductTypeEnum:
            self.product_type_filter_combo.addItem(pt_enum.value, pt_enum) # Store Enum member as data
        self.product_type_filter_combo.currentIndexChanged.connect(self.toolbar_refresh_action.trigger)
        filter_layout.addWidget(self.product_type_filter_combo)

        self.show_inactive_check = QCheckBox("Show Inactive")
        self.show_inactive_check.stateChanged.connect(self.toolbar_refresh_action.trigger)
        filter_layout.addWidget(self.show_inactive_check)
        
        self.clear_filters_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Clear Filters")
        self.clear_filters_button.clicked.connect(self._clear_filters_and_load)
        filter_layout.addWidget(self.clear_filters_button)
        filter_layout.addStretch()
        self.main_layout.addLayout(filter_layout)

        self.products_table = QTableView()
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.products_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.products_table.horizontalHeader().setStretchLastSection(False)
        self.products_table.doubleClicked.connect(self._on_edit_product_double_click) 
        self.products_table.setSortingEnabled(True)

        self.table_model = ProductTableModel()
        self.products_table.setModel(self.table_model)
        
        header = self.products_table.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        id_col_idx = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else -1
        if id_col_idx != -1: self.products_table.setColumnHidden(id_col_idx, True)
        
        name_col_idx = self.table_model._headers.index("Name") if "Name" in self.table_model._headers else -1
        if name_col_idx != -1:
            visible_name_idx = name_col_idx - 1 if id_col_idx != -1 and id_col_idx < name_col_idx else name_col_idx
            if not self.products_table.isColumnHidden(name_col_model_idx):
                 header.setSectionResizeMode(visible_name_idx, QHeaderView.ResizeMode.Stretch)
        elif self.table_model.columnCount() > 2 : # Fallback: stretch second visible column
            header.setSectionResizeMode(1 if id_col_idx == 0 else 2, QHeaderView.ResizeMode.Stretch)


        self.main_layout.addWidget(self.products_table)
        self.setLayout(self.main_layout)

        if self.products_table.selectionModel():
            self.products_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Product/Service Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add Product/Service", self)
        self.toolbar_add_action.triggered.connect(self._on_add_product)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Product/Service", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_product)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_toggle_active_action = QAction(QIcon(self.icon_path_prefix + "deactivate.svg"), "Toggle Active", self)
        self.toolbar_toggle_active_action.triggered.connect(self._on_toggle_active_status)
        self.toolbar.addAction(self.toolbar_toggle_active_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_products()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    @Slot()
    def _clear_filters_and_load(self):
        self.search_edit.clear()
        self.product_type_filter_combo.setCurrentIndex(0) # "All Types"
        self.show_inactive_check.setChecked(False)
        schedule_task_from_qt(self._load_products())

    @Slot()
    def _update_action_states(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        
        self.toolbar_edit_action.setEnabled(single_selection)
        self.toolbar_toggle_active_action.setEnabled(single_selection)

    async def _load_products(self):
        if not self.app_core.product_manager:
            self.app_core.logger.error("ProductManager not available in ProductsWidget.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Product Manager component not available."))
            return
        try:
            search_term = self.search_edit.text().strip() or None
            active_only = not self.show_inactive_check.isChecked()
            product_type_enum_filter: Optional[ProductTypeEnum] = self.product_type_filter_combo.currentData()
            
            result: Result[List[ProductSummaryData]] = await self.app_core.product_manager.get_products_for_listing(
                active_only=active_only, 
                product_type_filter=product_type_enum_filter,
                search_term=search_term,
                page=1, 
                page_size=200 
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                list_of_dicts = [dto.model_dump() for dto in data_for_table]
                json_data = json.dumps(list_of_dicts, default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                error_msg = f"Failed to load products/services: {', '.join(result.errors)}"
                self.app_core.logger.error(error_msg)
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))
        except Exception as e:
            error_msg = f"Unexpected error loading products/services: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            product_summaries: List[ProductSummaryData] = [ProductSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(product_summaries)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse product/service data: {e}")
        except Exception as p_error: 
            QMessageBox.critical(self, "Data Error", f"Invalid product/service data format: {p_error}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_product(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to add a product/service.")
            return
        
        dialog = ProductDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.product_saved.connect(lambda _id: schedule_task_from_qt(self._load_products()))
        dialog.exec()

    def _get_selected_product_id(self) -> Optional[int]:
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1:
            return None
        return self.table_model.get_product_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_product(self):
        product_id = self._get_selected_product_id()
        if product_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single product/service to edit.")
            return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit a product/service.")
            return
            
        dialog = ProductDialog(self.app_core, self.app_core.current_user.id, product_id=product_id, parent=self)
        dialog.product_saved.connect(lambda _id: schedule_task_from_qt(self._load_products()))
        dialog.exec()
        
    @Slot(QModelIndex)
    def _on_edit_product_double_click(self, index: QModelIndex): # Changed to edit on double click
        if not index.isValid(): return
        product_id = self.table_model.get_product_id_at_row(index.row())
        if product_id is None: return
        
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit product/service.")
            return
        dialog = ProductDialog(self.app_core, self.app_core.current_user.id, product_id=product_id, parent=self)
        dialog.product_saved.connect(lambda _id: schedule_task_from_qt(self._load_products()))
        dialog.exec()

    @Slot()
    def _on_toggle_active_status(self):
        product_id = self._get_selected_product_id()
        if product_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single product/service to toggle status.")
            return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to change product/service status.")
            return
            
        product_status_active = self.table_model.get_product_status_at_row(self.products_table.currentIndex().row())
        action_verb = "deactivate" if product_status_active else "activate"
        reply = QMessageBox.question(self, f"Confirm {action_verb.capitalize()}",
                                     f"Are you sure you want to {action_verb} this product/service?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        future = schedule_task_from_qt(
            self.app_core.product_manager.toggle_product_active_status(product_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_toggle_active_result)
        else: self._handle_toggle_active_result(None)

    def _handle_toggle_active_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule product/service status toggle."); return
        try:
            result: Result[Product] = future.result()
            if result.is_success:
                action_verb_past = "activated" if result.value and result.value.is_active else "deactivated"
                QMessageBox.information(self, "Success", f"Product/Service {action_verb_past} successfully.")
                schedule_task_from_qt(self._load_products()) 
            else:
                QMessageBox.warning(self, "Error", f"Failed to toggle product/service status:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Error handling toggle active status result for product/service: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

```
**Validation for `app/ui/products/products_widget.py`:**
*   **Imports**: All necessary modules, including `ProductTableModel`, `ProductDialog`, `ProductSummaryData`, `ProductTypeEnum`, and `Product` are imported.
*   **`__init__`**: Standard setup for `app_core`, `icon_path_prefix`, `_init_ui`, and initial data load.
*   **`_init_ui`**:
    *   Toolbar is created.
    *   Filter area includes `search_edit`, `product_type_filter_combo` (populated with `ProductTypeEnum` values), and `show_inactive_check`. A "Clear Filters" button is added.
    *   `QTableView` (`self.products_table`) is set up with `ProductTableModel`.
    *   Column hiding and resizing logic is similar to `CustomersWidget` and `VendorsWidget`, adapted for product-specific columns.
*   **`_create_toolbar`**: Actions "Add Product/Service", "Edit", "Toggle Active", "Refresh List" are created with icons.
*   **`_clear_filters_and_load`**: Resets filter UI to defaults and triggers `_load_products`.
*   **`_update_action_states`**: Enables/disables actions based on selection.
*   **`_load_products`**: Gets filter values (search, active status, product type from `product_type_filter_combo.currentData()`), calls `product_manager.get_products_for_listing()`, and updates the table model.
*   **`_update_table_model_slot`**: Parses JSON and updates `ProductTableModel`.
*   **Action Slots**: `_on_add_product`, `_on_edit_product`, `_on_toggle_active_status`, `_on_edit_product_double_click` are implemented, launching `ProductDialog` or calling `ProductManager` methods, similar to Customer/Vendor widgets.
*   This widget follows the established pattern very closely.

---
**2. Update `app/ui/products/__init__.py` to export `ProductsWidget`**

```python
# app/ui/products/__init__.py
from .product_table_model import ProductTableModel
from .product_dialog import ProductDialog
from .products_widget import ProductsWidget # New export

__all__ = [
    "ProductTableModel",
    "ProductDialog",
    "ProductsWidget", # Added to __all__
]
```
**Validation for `app/ui/products/__init__.py`:**
*   Added `from .products_widget import ProductsWidget`.
*   Added `ProductsWidget` to `__all__`.

---
**3. Update `app/ui/main_window.py` to include the "Products & Services" tab**

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
from app.ui.products.products_widget import ProductsWidget # New Import
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
        
        # Determine icon path prefix once
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            # This message is better placed in main.py or ApplicationCore for a one-time startup log
            # print("MainWindow: Compiled Qt resources (resources_rc.py) not found. Using direct file paths.")
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
        self.toolbar.setIconSize(QSize(24, 24)) # Slightly larger toolbar icons
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar) 
    
    def _add_module_tabs(self):
        # Icon path prefix is now an instance variable self.icon_path_prefix
        self.dashboard_widget = DashboardWidget(self.app_core)
        self.tab_widget.addTab(self.dashboard_widget, QIcon(self.icon_path_prefix + "dashboard.svg"), "Dashboard")
        
        self.accounting_widget = AccountingWidget(self.app_core)
        self.tab_widget.addTab(self.accounting_widget, QIcon(self.icon_path_prefix + "accounting.svg"), "Accounting")
        
        self.customers_widget = CustomersWidget(self.app_core)
        self.tab_widget.addTab(self.customers_widget, QIcon(self.icon_path_prefix + "customers.svg"), "Customers")
        
        self.vendors_widget = VendorsWidget(self.app_core)
        self.tab_widget.addTab(self.vendors_widget, QIcon(self.icon_path_prefix + "vendors.svg"), "Vendors")

        self.products_widget = ProductsWidget(self.app_core) # New Widget
        self.tab_widget.addTab(self.products_widget, QIcon(self.icon_path_prefix + "product.svg"), "Products & Services") # New Tab
        
        self.banking_widget = BankingWidget(self.app_core)
        self.tab_widget.addTab(self.banking_widget, QIcon(self.icon_path_prefix + "banking.svg"), "Banking")
        
        self.reports_widget = ReportsWidget(self.app_core)
        self.tab_widget.addTab(self.reports_widget, QIcon(self.icon_path_prefix + "reports.svg"), "Reports")
        
        self.settings_widget = SettingsWidget(self.app_core)
        self.tab_widget.addTab(self.settings_widget, QIcon(self.icon_path_prefix + "settings.svg"), "Settings")
    
    def _create_status_bar(self):
        # ... (no changes from previous version)
        self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready"); self.status_bar.addWidget(self.status_label, 1) 
        user_text = "User: Guest"; 
        if self.app_core.current_user: user_text = f"User: {self.app_core.current_user.username}"
        self.user_label = QLabel(user_text); self.status_bar.addPermanentWidget(self.user_label)
        self.version_label = QLabel(f"Version: {QCoreApplication.applicationVersion()}"); self.status_bar.addPermanentWidget(self.version_label)

    
    def _create_actions(self):
        # ... (no changes from previous version, uses self.icon_path_prefix)
        self.new_company_action = QAction(QIcon(self.icon_path_prefix + "new_company.svg"), "New Company...", self); self.new_company_action.setShortcut(QKeySequence(QKeySequence.StandardKey.New)); self.new_company_action.triggered.connect(self.on_new_company)
        self.open_company_action = QAction(QIcon(self.icon_path_prefix + "open_company.svg"), "Open Company...", self); self.open_company_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Open)); self.open_company_action.triggered.connect(self.on_open_company)
        self.backup_action = QAction(QIcon(self.icon_path_prefix + "backup.svg"), "Backup Data...", self); self.backup_action.triggered.connect(self.on_backup)
        self.restore_action = QAction(QIcon(self.icon_path_prefix + "restore.svg"), "Restore Data...", self); self.restore_action.triggered.connect(self.on_restore)
        self.exit_action = QAction(QIcon(self.icon_path_prefix + "exit.svg"), "Exit", self); self.exit_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Quit)); self.exit_action.triggered.connect(self.close) 
        self.preferences_action = QAction(QIcon(self.icon_path_prefix + "preferences.svg"), "Preferences...", self); self.preferences_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Preferences)); self.preferences_action.triggered.connect(self.on_preferences)
        self.help_contents_action = QAction(QIcon(self.icon_path_prefix + "help.svg"), "Help Contents", self); self.help_contents_action.setShortcut(QKeySequence(QKeySequence.StandardKey.HelpContents)); self.help_contents_action.triggered.connect(self.on_help_contents)
        self.about_action = QAction(QIcon(self.icon_path_prefix + "about.svg"), "About " + QCoreApplication.applicationName(), self); self.about_action.triggered.connect(self.on_about)

    def _create_menus(self):
        # ... (no changes from previous version)
        self.file_menu = self.menuBar().addMenu("&File"); self.file_menu.addAction(self.new_company_action); self.file_menu.addAction(self.open_company_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.backup_action); self.file_menu.addAction(self.restore_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.exit_action)
        self.edit_menu = self.menuBar().addMenu("&Edit"); self.edit_menu.addAction(self.preferences_action)
        self.view_menu = self.menuBar().addMenu("&View"); self.tools_menu = self.menuBar().addMenu("&Tools")
        self.help_menu = self.menuBar().addMenu("&Help"); self.help_menu.addAction(self.help_contents_action); self.help_menu.addSeparator(); self.help_menu.addAction(self.about_action)
        self.toolbar.addAction(self.new_company_action); self.toolbar.addAction(self.open_company_action); self.toolbar.addSeparator(); self.toolbar.addAction(self.backup_action); self.toolbar.addAction(self.preferences_action)
    
    @Slot()
    def on_new_company(self): QMessageBox.information(self, "New Company", "New company wizard not yet implemented.")
    @Slot()
    def on_open_company(self): QMessageBox.information(self, "Open Company", "Open company dialog not yet implemented.")
    # ... (other slots remain unchanged) ...
    @Slot()
    def on_backup(self): QMessageBox.information(self, "Backup Data", "Backup functionality not yet implemented.")
    @Slot()
    def on_restore(self): QMessageBox.information(self, "Restore Data", "Restore functionality not yet implemented.")
    @Slot()
    def on_preferences(self): 
        # Example: Navigate to Settings tab, or open a dedicated preferences dialog
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
**Validation for `app/ui/main_window.py`:**
*   Added `from app.ui.products.products_widget import ProductsWidget`.
*   In `_add_module_tabs()`:
    *   `self.products_widget = ProductsWidget(self.app_core)` is instantiated.
    *   `self.tab_widget.addTab(self.products_widget, QIcon(self.icon_path_prefix + "product.svg"), "Products & Services")` adds the new tab. (Assumes `product.svg` exists).
*   Made `self.icon_path_prefix` an instance variable in `__init__` so it's consistently available to `_add_module_tabs` and `_create_actions`.
*   Toolbar icon size slightly increased for better visibility: `self.toolbar.setIconSize(QSize(24, 24))`.
*   Refined `on_preferences` slot to navigate to the Settings tab if it exists.

---
**4. Create `resources/icons/product.svg` (New Icon File)**

**Goal**: Provide an icon for the "Products & Services" tab.

```svg
# resources/icons/product.svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm-1 14H5c-.55 0-1-.45-1-1V7c0-.55.45-1 1-1h14c.55 0 1 .45 1 1v10c0 .55-.45 1-1 1z"/>
  <path d="M8 10h2v2H8zm0 4h2v2H8zm4-4h2v2h-2zm0 4h2v2h-2z"/>
</svg>
```
**Validation**: This SVG provides a simple "box with items" representation suitable for products/services.

---
**5. Update `resources/resources.qrc`**

**Goal**: Add the new `product.svg` icon to the Qt Resource system.

```xml
# resources/resources.qrc
<!DOCTYPE RCC><RCC version="1.0">
<qresource prefix="/">
    <file alias="icons/dashboard.svg">icons/dashboard.svg</file>
    <file alias="icons/accounting.svg">icons/accounting.svg</file>
    <file alias="icons/customers.svg">icons/customers.svg</file>
    <file alias="icons/vendors.svg">icons/vendors.svg</file>
    <file alias="icons/product.svg">icons/product.svg</file> <!-- New Icon -->
    <file alias="icons/banking.svg">icons/banking.svg</file>
    <file alias="icons/reports.svg">icons/reports.svg</file>
    <file alias="icons/settings.svg">icons/settings.svg</file>
    <file alias="icons/new_company.svg">icons/new_company.svg</file>
    <file alias="icons/open_company.svg">icons/open_company.svg</file>
    <file alias="icons/backup.svg">icons/backup.svg</file>
    <file alias="icons/restore.svg">icons/restore.svg</file>
    <file alias="icons/exit.svg">icons/exit.svg</file>
    <file alias="icons/preferences.svg">icons/preferences.svg</file>
    <file alias="icons/help.svg">icons/help.svg</file>
    <file alias="icons/about.svg">icons/about.svg</file>
    <file alias="icons/filter.svg">icons/filter.svg</file>
    <file alias="icons/expand_all.svg">icons/expand_all.svg</file>
    <file alias="icons/collapse_all.svg">icons/collapse_all.svg</file>
    <file alias="icons/refresh.svg">icons/refresh.svg</file>
    <file alias="icons/edit.svg">icons/edit.svg</file>
    <file alias="icons/transactions.svg">icons/transactions.svg</file>
    <file alias="icons/deactivate.svg">icons/deactivate.svg</file>
    <file alias="icons/add.svg">icons/add.svg</file>
    <file alias="icons/remove.svg">icons/remove.svg</file>
    <file alias="icons/view.svg">icons/view.svg</file>
    <file alias="icons/post.svg">icons/post.svg</file>
    <file alias="icons/reverse.svg">icons/reverse.svg</file>
    <file alias="images/splash.png">images/splash.png</file>
</qresource>
</RCC>
```
**Validation for `resources/resources.qrc`:**
*   Added `<file alias="icons/product.svg">icons/product.svg</file>`.

---
This completes Phase B for Product/Service Management. The application now has the backend logic and the frontend UI structure (Widget, TableModel, Dialog) for managing Products and Services. The `ProductsWidget` is integrated into the `MainWindow` as a new tab.

**Next Steps for You:**
1.  Create the new file `app/ui/products/products_widget.py` with the provided content.
2.  Update `app/ui/products/__init__.py`.
3.  Update `app/ui/main_window.py`.
4.  Create the new icon file `resources/icons/product.svg`.
5.  Update `resources/resources.qrc`.
6.  **Crucially, re-run `poetry run pyside6-rcc resources/resources.qrc -o app/resources_rc.py`** from your project root to include the new icon in the compiled resources.
7.  Run `poetry run sg_bookkeeper` to test. You should see the new "Products & Services" tab.

After confirming the application launches and the new tab is present, the next phase would be thorough testing of the Product/Service module UI and backend interactions.

---
https://drive.google.com/file/d/1-lQNYxO1i_5DT1QqEfMtYybal2mzhUAc/view?usp=sharing, https://drive.google.com/file/d/16gFjJpsNDcAcE0E4TkhL40Ka12eBq0i_/view?usp=sharing, https://drive.google.com/file/d/1Io9vpSP3ST1lRbemAqr0SnAfSLSCmzqI/view?usp=sharing, https://drive.google.com/file/d/1JIsAZQEejE1qm-fGe1L-QpLfOWBWWW-9/view?usp=sharing, https://drive.google.com/file/d/1NGBX2Et-BABCUeL5QJkhX44BBI0MrYA3/view?usp=sharing, https://drive.google.com/file/d/1Oa85u5sAFd9OgiARagGmGnqJlSw0SV8u/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221SQTCjVSg9-JUmuGgq5bhvaOTbHhi2gWe%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1TArp9rSH4Oz6EVarWHaYNBHbdJOkuU1Z/view?usp=sharing, https://drive.google.com/file/d/1Z2KhH8Sd1yHpRUoz6TOU1jLev6icDwkd/view?usp=sharing, https://drive.google.com/file/d/1e9CQtKfd6E1LhSmXliLFwXUFxeGoR35E/view?usp=sharing, https://drive.google.com/file/d/1e9OAGmsj8Z2SAD1oNT2pAwmnm3zBnlGi/view?usp=sharing, https://drive.google.com/file/d/1km1x5NEIFLkBRhpyq7OS0PsXiMoXz1VY/view?usp=sharing, https://drive.google.com/file/d/1rnl0de93Aokl_FDNzUQTEu_C4p5LECWJ/view?usp=sharing, https://drive.google.com/file/d/1s6CXBUuwyh945SzNa2Ti4PUYJpTVTXdt/view?usp=sharing

