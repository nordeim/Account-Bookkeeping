<think>
The application is launching and shutting down cleanly! This is excellent and means that creating `ProductTableModel`, `ProductDialog`, and updating `app/ui/products/__init__.py` were successful and didn't cause any startup issues. The backend for Product/Service Management is already integrated into `ApplicationCore`.

**Current Step: Enhancement Execution Plan: Basic Product/Service Management Module - Phase B (Frontend UI)**

We have completed for Product/Service UI:
*   B1. Create `ProductTableModel` (Done).
*   B2. Create `ProductDialog` (Done).

The plan for Product/Service UI was:
*   B3. Enhance `ProductsWidget` (from stub to functional). (Next)

So, the immediate next step is **B3: Enhance `ProductsWidget`**. This widget will use `ProductTableModel` to display a list of products/services and `ProductDialog` to add/edit them. It will also include actions like "Toggle Active Status", mirroring the functionality of `CustomersWidget` and `VendorsWidget`.

A `ProductsWidget` stub might not exist yet in `app/ui/products/products_widget.py` according to `project_file_structure.txt`. I'll need to create it. Also, `MainWindow` needs to be updated to include a tab for it, and `app/ui/main_window.py` will need to import it. `app/ui/products/__init__.py` will need to export it.

**Plan for this Turn: Implement `ProductsWidget` and Integrate into `MainWindow` (Phase B3)**

**Objective:** Create a functional `ProductsWidget` for listing, adding, editing, and managing the active status of products/services, and integrate this widget into the main application window.

**Detailed Plan & Checklist:**

**1. Create `app/ui/products/products_widget.py` (New File)**
   *   **Goal:** The main UI for product/service management.
   *   **File to Create:** `app/ui/products/products_widget.py`
   *   **Checklist & Tasks:**
        *   [ ] Define `ProductsWidget(QWidget)`.
        *   [ ] `__init__`: Store `app_core`, init `icon_path_prefix`, call `_init_ui`, schedule `_load_products`.
        *   [ ] `_init_ui()`:
            *   `QVBoxLayout`, `QToolBar`, filter/search UI (`QLineEdit` for search, `QComboBox` for Product Type filter, `QCheckBox` for "Show Inactive").
            *   `QTableView` (`self.products_table`), instantiate `self.table_model = ProductTableModel()`.
            *   Set model, configure table (column hiding/resizing, sorting).
            *   Connect signals.
        *   [ ] `_create_toolbar()`: Actions "Add", "Edit", "Toggle Active", "Refresh".
        *   [ ] `_update_action_states()`: Enable/disable actions based on selection.
        *   [ ] `_load_products()`: Get filters, call `app_core.product_manager.get_products_for_listing()`, update model via `_update_table_model_slot`.
        *   [ ] `_update_table_model_slot(json_data_str)`: Parse JSON to `List[ProductSummaryData]`, update model.
        *   [ ] Action Handlers: `_on_add_product`, `_on_edit_product`, `_on_toggle_active_status`, `_on_refresh_products`, `_on_view_product_double_click`. These will launch `ProductDialog` or call `ProductManager` methods.
        *   [ ] Helper `_get_selected_product_id()`.

**2. Update `app/ui/products/__init__.py`**
   *   **Goal:** Export the new `ProductsWidget`.
   *   **File to Update:** `app/ui/products/__init__.py`
   *   **Checklist & Tasks:**
        *   [ ] Add `from .products_widget import ProductsWidget`.
        *   [ ] Add `ProductsWidget` to `__all__`.

**3. Update `app/ui/main_window.py`**
   *   **Goal:** Add a "Products" tab to the main application window using `ProductsWidget`.
   *   **File to Update:** `app/ui/main_window.py`
   *   **Checklist & Tasks:**
        *   [ ] Import `from app.ui.products.products_widget import ProductsWidget`.
        *   [ ] In `_add_module_tabs()`, instantiate `self.products_widget = ProductsWidget(self.app_core)`.
        *   [ ] Add the tab: `self.tab_widget.addTab(self.products_widget, QIcon(self.icon_path_prefix + "product.svg"), "Products & Services")`. (Requires a `product.svg` icon).

**4. Create `resources/icons/product.svg` (New Icon File)**
    *   **Goal**: Provide an icon for the "Products & Services" tab.
    *   **File to Create**: `resources/icons/product.svg`
    *   **Checklist & Tasks**:
        *   [ ] Design or find a simple SVG icon representing products/services (e.g., a box, a gear, a tag).

**5. Update `resources/resources.qrc`**
    *   **Goal**: Add the new `product.svg` icon to the Qt Resource system.
    *   **File to Update**: `resources/resources.qrc`
    *   **Checklist & Tasks**:
        *   [ ] Add `<file alias="icons/product.svg">icons/product.svg</file>`.
        *   [ ] Remind user to recompile QRC: `poetry run pyside6-rcc resources/resources.qrc -o app/resources_rc.py`.

This plan covers creating the UI for Products/Services and integrating it. I'll start with the `product.svg` icon, then `products_widget.py`, then update the `__init__` files and `MainWindow`.
</think>

This is excellent! The application's continued stability confirms that the backend for Vendor Management, including its integration into `ApplicationCore`, is solid.

We are now ready to proceed with **Phase B: Frontend UI for Vendor Management**, specifically **Step B3: Enhance `VendorsWidget`**. This will transform the stub into a functional UI for listing, adding, editing, and managing vendors.

Following that, as per your general request to "close any gap in the core feature set of the application as noted in your Roadmap suggestion," we can then move to **Product/Service Management**, starting with its backend.

However, let's complete the Vendor UI first to maintain module coherence.

**Enhancement Execution Plan: Basic Vendor Management Module - Phase B (Frontend UI continued)**

**Overall Objective (Phase B for Vendors):** Create a functional user interface for managing vendors, including list display, filtering, and CRUD operations via a dialog.

---
**B3. Update `app/ui/vendors/vendors_widget.py` (Enhance from Stub to Functional)**

**Goal:** Create a functional UI for managing vendors, including a table view for listing, filter/search capabilities, and actions for adding, editing, and toggling the active status of vendors, all interacting with `VendorManager` via `VendorDialog`.

```python
# app/ui/vendors/vendors_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox # Added for filtering/search
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.vendors.vendor_table_model import VendorTableModel 
from app.ui.vendors.vendor_dialog import VendorDialog 
from app.utils.pydantic_models import VendorSummaryData 
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.vendor import Vendor # For Result type hint from manager

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class VendorsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for VendorsWidget.")
        except ImportError:
            self.app_core.logger.info("VendorsWidget: Compiled Qt resources not found. Using direct file paths.")
            # self.icon_path_prefix remains "resources/icons/"

        self._init_ui()
        # Initial load triggered by filter button click to respect default filter settings
        QTimer.singleShot(0, lambda: self.toolbar_refresh_action.trigger() if hasattr(self, 'toolbar_refresh_action') else schedule_task_from_qt(self._load_vendors()))


    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        # --- Toolbar ---
        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        # --- Filter/Search Area ---
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Enter code, name, or email...")
        self.search_edit.returnPressed.connect(self.toolbar_refresh_action.trigger) 
        filter_layout.addWidget(self.search_edit)

        self.show_inactive_check = QCheckBox("Show Inactive")
        self.show_inactive_check.stateChanged.connect(self.toolbar_refresh_action.trigger) 
        filter_layout.addWidget(self.show_inactive_check)
        
        self.clear_filters_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"),"Clear Filters")
        self.clear_filters_button.clicked.connect(self._clear_filters_and_load)
        filter_layout.addWidget(self.clear_filters_button)
        filter_layout.addStretch()
        self.main_layout.addLayout(filter_layout)

        # --- Table View ---
        self.vendors_table = QTableView()
        self.vendors_table.setAlternatingRowColors(True)
        self.vendors_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.vendors_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.vendors_table.horizontalHeader().setStretchLastSection(False) # Changed for better control
        self.vendors_table.doubleClicked.connect(self._on_edit_vendor) # Or view_vendor
        self.vendors_table.setSortingEnabled(True)

        self.table_model = VendorTableModel()
        self.vendors_table.setModel(self.table_model)
        
        # Configure columns after model is set
        header = self.vendors_table.horizontalHeader()
        for i in range(self.table_model.columnCount()): # Default to ResizeToContents
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        if "ID" in self.table_model._headers:
            id_col_idx = self.table_model._headers.index("ID")
            self.vendors_table.setColumnHidden(id_col_idx, True)
        
        if "Name" in self.table_model._headers:
            name_col_model_idx = self.table_model._headers.index("Name")
            # Calculate visible index for "Name" if "ID" is hidden before it
            visible_name_idx = name_col_model_idx
            if "ID" in self.table_model._headers and self.table_model._headers.index("ID") < name_col_model_idx and self.vendors_table.isColumnHidden(self.table_model._headers.index("ID")):
                visible_name_idx -=1
            
            if not self.vendors_table.isColumnHidden(name_col_model_idx):
                 header.setSectionResizeMode(visible_name_idx, QHeaderView.ResizeMode.Stretch)
        else: 
             # Fallback: if ID is hidden (col 0), then Code (model col 1 -> vis col 0), Name (model col 2 -> vis col 1)
             # Stretch the second visible column which is typically Name.
             if self.table_model.columnCount() > 2 and self.vendors_table.isColumnHidden(0):
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 
             elif self.table_model.columnCount() > 1: # If ID is not hidden or not present
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)


        self.main_layout.addWidget(self.vendors_table)
        self.setLayout(self.main_layout)

        if self.vendors_table.selectionModel():
            self.vendors_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Vendor Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add Vendor", self)
        self.toolbar_add_action.triggered.connect(self._on_add_vendor)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Vendor", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_vendor)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_toggle_active_action = QAction(QIcon(self.icon_path_prefix + "deactivate.svg"), "Toggle Active", self) # Icon might need specific "activate" variant too
        self.toolbar_toggle_active_action.triggered.connect(self._on_toggle_active_status)
        self.toolbar.addAction(self.toolbar_toggle_active_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_vendors()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    @Slot()
    def _clear_filters_and_load(self):
        self.search_edit.clear()
        self.show_inactive_check.setChecked(False)
        schedule_task_from_qt(self._load_vendors()) # Trigger load with cleared filters

    @Slot()
    def _update_action_states(self):
        selected_rows = self.vendors_table.selectionModel().selectedRows()
        has_selection = bool(selected_rows)
        single_selection = len(selected_rows) == 1
        
        self.toolbar_edit_action.setEnabled(single_selection)
        self.toolbar_toggle_active_action.setEnabled(single_selection)

    async def _load_vendors(self):
        if not self.app_core.vendor_manager:
            self.app_core.logger.error("VendorManager not available in VendorsWidget.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Vendor Manager component not available."))
            return
        try:
            search_term = self.search_edit.text().strip() or None
            active_only = not self.show_inactive_check.isChecked()
            
            result: Result[List[VendorSummaryData]] = await self.app_core.vendor_manager.get_vendors_for_listing(
                active_only=active_only, 
                search_term=search_term,
                page=1, 
                page_size=200 # Load a reasonable number for MVP table, pagination UI later
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                list_of_dicts = [dto.model_dump() for dto in data_for_table]
                json_data = json.dumps(list_of_dicts, default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                error_msg = f"Failed to load vendors: {', '.join(result.errors)}"
                self.app_core.logger.error(error_msg)
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))
        except Exception as e:
            error_msg = f"Unexpected error loading vendors: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            vendor_summaries: List[VendorSummaryData] = [VendorSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(vendor_summaries)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse vendor data: {e}")
        except Exception as p_error: 
            QMessageBox.critical(self, "Data Error", f"Invalid vendor data format: {p_error}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_vendor(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to add a vendor.")
            return
        
        dialog = VendorDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.vendor_saved.connect(lambda _id: schedule_task_from_qt(self._load_vendors()))
        dialog.exec()

    def _get_selected_vendor_id(self) -> Optional[int]:
        selected_rows = self.vendors_table.selectionModel().selectedRows()
        if not selected_rows: # No message if simply no selection for state update
            return None
        if len(selected_rows) > 1:
            QMessageBox.information(self, "Selection", "Please select only a single vendor for this action.")
            return None
        return self.table_model.get_vendor_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_vendor(self):
        vendor_id = self._get_selected_vendor_id()
        if vendor_id is None: 
            # Message only if action was explicitly triggered and no single item was selected
            if self.sender() == self.toolbar_edit_action : # type: ignore
                 QMessageBox.information(self, "Selection", "Please select a single vendor to edit.")
            return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit a vendor.")
            return
            
        dialog = VendorDialog(self.app_core, self.app_core.current_user.id, vendor_id=vendor_id, parent=self)
        dialog.vendor_saved.connect(lambda _id: schedule_task_from_qt(self._load_vendors()))
        dialog.exec()
        
    @Slot(QModelIndex)
    def _on_view_vendor_double_click(self, index: QModelIndex): # Renamed for clarity
        if not index.isValid(): return
        vendor_id = self.table_model.get_vendor_id_at_row(index.row())
        if vendor_id is None: return
        
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to view/edit vendor.")
            return
        # For MVP, double-click opens for edit. Can be changed to view-only later.
        dialog = VendorDialog(self.app_core, self.app_core.current_user.id, vendor_id=vendor_id, parent=self)
        dialog.vendor_saved.connect(lambda _id: schedule_task_from_qt(self._load_vendors()))
        dialog.exec()

    @Slot()
    def _on_toggle_active_status(self):
        vendor_id = self._get_selected_vendor_id()
        if vendor_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single vendor to toggle status.")
            return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to change vendor status.")
            return
            
        vendor_status_active = self.table_model.get_vendor_status_at_row(self.vendors_table.currentIndex().row())
        action_verb = "deactivate" if vendor_status_active else "activate"
        reply = QMessageBox.question(self, f"Confirm {action_verb.capitalize()}",
                                     f"Are you sure you want to {action_verb} this vendor?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        future = schedule_task_from_qt(
            self.app_core.vendor_manager.toggle_vendor_active_status(vendor_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_toggle_active_result)
        else: self._handle_toggle_active_result(None) # Handle scheduling failure

    def _handle_toggle_active_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule vendor status toggle."); return
        try:
            result: Result[Vendor] = future.result()
            if result.is_success:
                action_verb_past = "activated" if result.value and result.value.is_active else "deactivated"
                QMessageBox.information(self, "Success", f"Vendor {action_verb_past} successfully.")
                schedule_task_from_qt(self._load_vendors()) 
            else:
                QMessageBox.warning(self, "Error", f"Failed to toggle vendor status:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Error handling toggle active status result for vendor: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

```
**Validation for `app/ui/vendors/vendors_widget.py`:**
*   **Class Name & Imports**: Correctly named `VendorsWidget`. Imports `VendorTableModel`, `VendorDialog`, `VendorSummaryData`, `Vendor`.
*   **`__init__`**: Initializes `icon_path_prefix` with logging. Calls `_init_ui`. Schedules initial `_load_vendors` via refresh action trigger for consistency with filter logic.
*   **`_init_ui`**:
    *   Toolbar created.
    *   Filter UI for search and "Show Inactive" checkbox added. `returnPressed` on search and `stateChanged` on checkbox now trigger `toolbar_refresh_action` (which calls `_load_vendors`). Added "Clear Filters" button.
    *   `QTableView` (`self.vendors_table`) and `VendorTableModel` are set up.
    *   Column configuration: Hides "ID". Sets default `ResizeToContents` for all, then tries to make "Name" column stretch (with more robust index calculation if "ID" is hidden).
*   **`_create_toolbar`**: Actions "Add Vendor", "Edit Vendor", "Toggle Active", "Refresh List" created.
*   **`_update_action_states`**: Enables/disables "Edit", "Toggle Active" based on single selection.
*   **`_load_vendors`**: Collects filter params, calls `vendor_manager.get_vendors_for_listing()`, uses `dto.model_dump()` before JSON serialization.
*   **`_update_table_model_slot`**: Parses JSON to `List[VendorSummaryData]` DTOs, updates model. Catches Pydantic validation errors during `model_validate`.
*   **Action Slots**: `_on_add_vendor`, `_on_edit_vendor`, `_on_toggle_active_status`, `_on_view_vendor_double_click` are implemented, launching `VendorDialog` or calling `VendorManager` methods. `_get_selected_vendor_id` refined.
*   This widget closely mirrors `CustomersWidget` in structure and functionality, adapted for Vendors.

---
**Next, update `app/ui/vendors/__init__.py` to export `VendorsWidget`.**

```python
# app/ui/vendors/__init__.py
from .vendors_widget import VendorsWidget # Was previously just a stub, now functional
from .vendor_dialog import VendorDialog
from .vendor_table_model import VendorTableModel

__all__ = [
    "VendorsWidget",
    "VendorDialog",
    "VendorTableModel",
]
```
**Validation for `app/ui/vendors/__init__.py`:**
*   Ensures `VendorsWidget` (the main widget for the tab) is exported.

---
**Finally, review `app/ui/main_window.py` to ensure `VendorsWidget` is correctly instantiated and added as a tab.**
This part should already be correct from when `VendorsWidget` was initially added as a stub.

Relevant part in `_add_module_tabs` of `MainWindow`:
```python
        # ... other tabs ...
        self.vendors_widget = VendorsWidget(self.app_core)
        self.tab_widget.addTab(self.vendors_widget, QIcon(self.icon_path_prefix + "vendors.svg"), "Vendors")
        # ... other tabs ...
```
This looks correct.

---

This completes **Phase B (Frontend UI)** for the basic Vendor Management module. The application should now have a functional "Vendors" tab allowing users to list, search, filter, add, edit, and toggle the active status of vendors.

The next logical step is thorough testing of this new Vendor module, followed by updating the project documentation (`README.md`, TDS) to reflect its completion.
