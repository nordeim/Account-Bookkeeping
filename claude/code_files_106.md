<think>
The application continues its streak of successful launches and clean shutdowns! This confirms that the creation of `VendorTableModel` and `VendorDialog` (Phase B1 and B2 for Vendor UI) did not introduce any startup errors. The backend for Vendor management is also complete and integrated.

**Current Step: Enhancement Execution Plan: Basic Vendor Management Module - Phase B (Frontend UI)**

We have completed for Vendor Management UI:
*   B1. Create `VendorTableModel` (Done).
*   B2. Create `VendorDialog` (Done).

The plan for Vendor Management UI was:
*   B3. Enhance `VendorsWidget` (from stub to functional). (Next)

So, the immediate next step is **B3: Enhance `VendorsWidget`**. This widget will use the `VendorTableModel` to display a list of vendors and the `VendorDialog` to add/edit them. It will also include actions like "Toggle Active Status", mirroring the functionality of `CustomersWidget`.

**Plan for B3: Enhance `VendorsWidget`**
   *   **Goal:** Transform the stub `VendorsWidget` into a functional UI for listing, adding, editing, and managing the active status of vendors.
   *   **File to Update:** `app/ui/vendors/vendors_widget.py`
   *   **Checklist & Tasks:**
        *   [ ] **Import necessary classes**: `VendorTableModel`, `VendorDialog`, `VendorSummaryData`, `Vendor` (for type hints), `Q*` widgets, slots, signals, etc.
        *   [ ] **`__init__`**:
            *   Store `app_core`.
            *   Initialize `icon_path_prefix`.
            *   Call `_init_ui()`.
            *   Schedule initial `_load_vendors()` using `QTimer.singleShot`.
        *   [ ] **`_init_ui()`**:
            *   Create main `QVBoxLayout`.
            *   Call `_create_toolbar()`.
            *   Add filter/search UI (similar to `CustomersWidget`: `QLineEdit` for search, `QCheckBox` for "Show Inactive").
            *   Create `QTableView` (`self.vendors_table`).
            *   Instantiate `self.table_model = VendorTableModel()`.
            *   Set model to table: `self.vendors_table.setModel(self.table_model)`.
            *   Configure table view properties (selection, column hiding for "ID", column resizing, sorting).
            *   Connect `selectionChanged` signal to `_update_action_states`.
            *   Connect `doubleClicked` signal to an edit/view slot.
        *   [ ] **`_create_toolbar()`**:
            *   Create `QToolBar` with actions: "Add Vendor", "Edit Vendor", "Toggle Active", "Refresh List", using appropriate icons.
            *   Connect action `triggered` signals to their respective handler slots.
        *   [ ] **`_update_action_states()` Slot**:
            *   Enable/disable toolbar actions ("Edit", "Toggle Active") based on table selection.
        *   [ ] **`_load_vendors()` Async Method**:
            *   Get filter parameters (search term, active status).
            *   Call `self.app_core.vendor_manager.get_vendors_for_listing(filters)`.
            *   Handle `Result` and pass `List[VendorSummaryData]` (as JSON) to `_update_table_model_slot`.
        *   [ ] **`_update_table_model_slot(json_data_str: str)` Slot**:
            *   Parse JSON to `List[VendorSummaryData]`.
            *   Call `self.table_model.update_data()`.
            *   Call `_update_action_states()`.
        *   [ ] **Action Handler Slots**:
            *   `_on_add_vendor()`: Launch `VendorDialog` (no `vendor_id`). Connect `vendor_saved` signal to refresh.
            *   `_on_edit_vendor()`: Get selected ID, launch `VendorDialog` with `vendor_id`. Connect `vendor_saved`.
            *   `_on_toggle_active_status()`: Get ID, confirm, call `vendor_manager.toggle_vendor_active_status()`, handle result, refresh.
            *   `_on_refresh_vendors()` (connected to toolbar refresh and filter triggers): Call `_load_vendors`.
            *   `_on_view_vendor_double_click(index: QModelIndex)`: Get ID, launch `VendorDialog` (for MVP, can open in edit mode).
        *   [ ] **Helper `_get_selected_vendor_id()`**: To get ID from selected table row.

This structure is a direct parallel to `CustomersWidget`.
</think>

This is excellent! The consistent stability of the application after each backend phase for both Customer and Vendor modules is very encouraging.

We are now ready to complete **Phase B: Frontend UI for Vendor Management** by tackling **Step B3: Enhance `VendorsWidget`**. This will transform the current stub into a fully functional UI for managing vendors, mirroring the capabilities of the `CustomersWidget`.

---
**B3. Update `app/ui/vendors/vendors_widget.py`**

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
from app.ui.vendors.vendor_table_model import VendorTableModel # New import
from app.ui.vendors.vendor_dialog import VendorDialog # New import
from app.utils.pydantic_models import VendorSummaryData # For type hinting
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
            pass
        
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_vendors()))

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
        filter_layout.addStretch()
        self.main_layout.addLayout(filter_layout)

        # --- Table View ---
        self.vendors_table = QTableView()
        self.vendors_table.setAlternatingRowColors(True)
        self.vendors_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.vendors_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.vendors_table.horizontalHeader().setStretchLastSection(True)
        self.vendors_table.doubleClicked.connect(self._on_edit_vendor) 
        self.vendors_table.setSortingEnabled(True)

        self.table_model = VendorTableModel()
        self.vendors_table.setModel(self.table_model)
        
        if "ID" in self.table_model._headers:
            id_col_idx = self.table_model._headers.index("ID")
            self.vendors_table.setColumnHidden(id_col_idx, True)
        
        # Set default resize mode for all columns first
        for i in range(self.table_model.columnCount()):
            self.vendors_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        if "Name" in self.table_model._headers:
            name_col_model_idx = self.table_model._headers.index("Name")
            # Adjust for hidden ID column if "Name" is not the first visible
            name_col_visible_idx = name_col_model_idx - 1 if id_col_idx < name_col_model_idx else name_col_model_idx
            if not self.vendors_table.isColumnHidden(name_col_model_idx): # Check if Name column itself is not hidden
                 self.vendors_table.horizontalHeader().setSectionResizeMode(name_col_visible_idx, QHeaderView.ResizeMode.Stretch)
        else: # Fallback if "Name" header changes or not found, stretch a common visible column
             self.vendors_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Usually second visible


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

        self.toolbar_toggle_active_action = QAction(QIcon(self.icon_path_prefix + "deactivate.svg"), "Toggle Active", self)
        self.toolbar_toggle_active_action.triggered.connect(self._on_toggle_active_status)
        self.toolbar.addAction(self.toolbar_toggle_active_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_vendors()))
        self.toolbar.addAction(self.toolbar_refresh_action)


    @Slot()
    def _update_action_states(self):
        selected_rows = self.vendors_table.selectionModel().selectedRows()
        has_selection = bool(selected_rows)
        single_selection = len(selected_rows) == 1
        
        self.toolbar_edit_action.setEnabled(single_selection)
        self.toolbar_toggle_active_action.setEnabled(single_selection) # Changed from has_selection to single_selection for consistency

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
                page_size=200 
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                # Convert DTOs to dicts for JSON serialization if model_dump is not used by json_converter
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
        if not selected_rows or len(selected_rows) > 1:
            # Only show message if it's not a general selection update
            # This method is usually called by specific actions that expect single selection
            # QMessageBox.information(self, "Selection", "Please select a single vendor.")
            return None
        return self.table_model.get_vendor_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_vendor(self):
        vendor_id = self._get_selected_vendor_id()
        if vendor_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single vendor to edit.")
            return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit a vendor.")
            return
            
        dialog = VendorDialog(self.app_core, self.app_core.current_user.id, vendor_id=vendor_id, parent=self)
        dialog.vendor_saved.connect(lambda _id: schedule_task_from_qt(self._load_vendors()))
        dialog.exec()
        
    @Slot(QModelIndex)
    def _on_view_vendor_double_click(self, index: QModelIndex): # Name changed for clarity
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
        else: self._handle_toggle_active_result(None)

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
*   **Class Name**: Changed from `CustomersWidget` to `VendorsWidget` (this was a copy-paste error in my previous thought process for `CustomersWidget` itself, which I corrected there. Ensuring it's `VendorsWidget` here).
*   **Imports**: Correctly imports `VendorTableModel`, `VendorDialog`, `VendorSummaryData`, `Vendor`.
*   **`__init__`**: Initializes `icon_path_prefix` with logging for resource status. Calls `_init_ui` and schedules initial `_load_vendors`.
*   **`_init_ui`**:
    *   Sets up layout, toolbar, filter area (`search_edit`, `show_inactive_check`), and `QTableView` (`self.vendors_table`).
    *   Instantiates `VendorTableModel` and sets it to the table.
    *   Configures table: hides "ID", makes "Name" column stretch (with robust index finding).
    *   Connects signals for selection changes and double-click.
*   **`_create_toolbar`**: Creates actions "Add Vendor", "Edit Vendor", "Toggle Active", "Refresh List" and connects them.
*   **`_update_action_states`**: Enables/disables "Edit" and "Toggle Active" based on single selection.
*   **`_load_vendors`**:
    *   Gets filter parameters.
    *   Calls `self.app_core.vendor_manager.get_vendors_for_listing()`.
    *   Uses `dto.model_dump()` before JSON serialization for `CustomerSummaryData`. For `VendorSummaryData`, it should be the same.
*   **`_update_table_model_slot`**: Parses JSON to `List[VendorSummaryData]` DTOs and updates table model. Handles Pydantic validation errors if DTO conversion fails.
*   **Action Slots**:
    *   `_on_add_vendor`: Launches `VendorDialog`.
    *   `_on_edit_vendor`: Gets ID, launches `VendorDialog`.
    *   `_on_view_vendor_double_click`: Renamed from `_on_view_customer_double_click` and logic adjusted for vendors. For MVP, it opens the edit dialog.
    *   `_on_toggle_active_status`: Gets ID, confirms, calls manager.
*   **Helper `_get_selected_vendor_id()`**: Correctly implemented.

The `VendorsWidget` now mirrors the structure and functionality of `CustomersWidget`, adapted for Vendors.

---
**Final Steps for this Turn (Conceptual):**

1.  **Update `app/ui/vendors/__init__.py`**: Ensure it exports `VendorsWidget`, `VendorDialog`, `VendorTableModel`.
2.  **Update `app/ui/main_window.py`**: Ensure `VendorsWidget` is instantiated and added as a tab, similar to `CustomersWidget`.

Since these are straightforward `__init__.py` and `MainWindow` modifications just to make the new widget visible, and `MainWindow` was already adding a `VendorsWidget` stub, I'll provide the `__init__.py` for `app/ui/vendors/` and assume `MainWindow` is correctly set up.

---
**Update `app/ui/vendors/__init__.py` (New or Update)**

```python
# app/ui/vendors/__init__.py
from .vendors_widget import VendorsWidget
from .vendor_dialog import VendorDialog
from .vendor_table_model import VendorTableModel

__all__ = [
    "VendorsWidget",
    "VendorDialog",
    "VendorTableModel",
]
```

This completes Phase B for Vendor Management. The application should now have a functional basic Vendor module. The next step would be thorough testing of this new module.
