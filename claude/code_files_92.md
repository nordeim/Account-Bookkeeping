<think>
The application is still launching and shutting down cleanly! This is excellent. It confirms that the creation of `CustomerTableModel` and `CustomerDialog`, along with the backend updates for `CustomerManager` and `CustomerService`, and their integration into `ApplicationCore`, did not introduce any startup/shutdown issues.

**Current Project Status Recap:**

*   **Backend for Customer Management (Phase A)**: Complete.
*   **Frontend UI Foundation for Customer Management (Phase B - partially done)**:
    *   B1. `CustomerTableModel` (Created).
    *   B2. `CustomerDialog` (Created).
*   All previously implemented features remain stable.

**Next Step Identification:**

The user asks to "proceed with the next step in your plan."
The overall plan for Customer Management was:
*   **Phase A: Backend for Customer Management (Completed)**
*   **Phase B: Frontend UI for Customer Management (Current Focus)**
    *   B1. Create `CustomerTableModel` (Done).
    *   B2. Create `CustomerDialog` (Done).
    *   **B3. Enhance `CustomersWidget` (from stub to functional) (Next logical step)**.

So, the immediate next step is **B3: Enhance `CustomersWidget`**. This widget will use the `CustomerTableModel` to display a list of customers and the `CustomerDialog` to add/edit them. It will also include actions like "Toggle Active Status".

**Plan for this Turn: Implement `CustomersWidget` (Phase B3)**

**Objective:** Transform the stub `CustomersWidget` into a functional UI for listing, adding, editing, and managing the active status of customers.

**Detailed Plan & Checklist:**

**B3. Enhance `app/ui/customers/customers_widget.py`**
   *   **Goal:** A functional widget for customer management, integrating `CustomerTableModel` and `CustomerDialog`.
   *   **File to Update:** `app/ui/customers/customers_widget.py`
   *   **Checklist & Tasks:**
        *   [ ] **UI Layout**:
            *   Replace the placeholder `QLabel` with a `QVBoxLayout`.
            *   Add a `QToolBar` for actions ("Add", "Edit", "Toggle Active", "Refresh").
            *   Add a `QTableView` (`self.customers_table`).
            *   (Optional) Add filter/search input fields (`QLineEdit` for search term, `QCheckBox` for "Show Inactive").
        *   [ ] **Model Setup**:
            *   Instantiate `self.table_model = CustomerTableModel()`.
            *   Set `self.customers_table.setModel(self.table_model)`.
            *   Configure table view properties (selection behavior, column hiding for "ID", column resizing, sorting enabled).
        *   [ ] **Asynchronous Data Loading (`_load_customers`)**:
            *   Slot/method to fetch customer data.
            *   Collect filter parameters (search term, active status).
            *   Call `self.app_core.customer_manager.get_customers_for_listing(filters)` asynchronously.
            *   Use `future.add_done_callback` or `QMetaObject.invokeMethod` to pass the `List[CustomerSummaryData]` (as JSON) to `_update_table_model_slot`.
        *   [ ] **UI Update Slot (`_update_table_model_slot`)**:
            *   Receives customer summary data (JSON string).
            *   Parses JSON to `List[CustomerSummaryData]`.
            *   Calls `self.table_model.update_data()`.
            *   Calls `_update_action_states()` for toolbar buttons.
        *   [ ] **Action Handling Slots**:
            *   `_on_add_customer()`:
                *   Check for `current_user`.
                *   Launch `CustomerDialog` (with `customer_id=None`).
                *   Connect `dialog.customer_saved` signal to `self._load_customers` to refresh table.
            *   `_on_edit_customer()`:
                *   Get selected customer ID from table model.
                *   Launch `CustomerDialog` with the `customer_id`.
                *   Connect `dialog.customer_saved` signal to `self._load_customers`.
            *   `_on_toggle_active_status()`:
                *   Get selected customer ID.
                *   Confirm action with `QMessageBox`.
                *   Call `self.app_core.customer_manager.toggle_customer_active_status(customer_id, user_id)` asynchronously.
                *   Handle result (show message, refresh list).
            *   `_on_refresh_customers()`: Call `_load_customers`.
            *   `_on_view_customer_double_click(index: QModelIndex)`: Get customer ID, launch `CustomerDialog` in view-only/edit mode based on permissions or just edit. (For MVP, edit is fine).
        *   [ ] **Action State Management (`_update_action_states`)**:
            *   Enable/disable "Edit", "Toggle Active" based on whether a customer is selected in the table.
        *   [ ] **Initial Load**: Call `_load_customers` on widget initialization (e.g., using `QTimer.singleShot`).

This will complete the basic UI for the Customer module.
</think>

Excellent! The application remains stable, and the backend components for Customer Management are now integrated into `ApplicationCore`. This means Phase A of the Customer Management module implementation is complete.

We will now proceed with **Phase B: Frontend UI for Customer Management**, focusing on **Step B3: Enhance `CustomersWidget`**. This involves transforming the existing stub file into a functional widget that can list customers, and allows users to add, edit, and manage their active status using the `CustomerTableModel` and `CustomerDialog` we created previously.

---
**1. Update `app/ui/customers/customers_widget.py`**

**Goal:** Create a functional UI for managing customers, including a table view, action buttons, and interaction with `CustomerManager` via `CustomerDialog`.

```python
# app/ui/customers/customers_widget.py
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
from app.ui.customers.customer_table_model import CustomerTableModel # New import
from app.ui.customers.customer_dialog import CustomerDialog # New import
from app.utils.pydantic_models import CustomerSummaryData # For type hinting
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.customer import Customer # For Result type hint from manager

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class CustomersWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for CustomersWidget.")
        except ImportError:
            self.app_core.logger.info("CustomersWidget: Compiled Qt resources not found. Using direct file paths.")
            pass
        
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_customers()))

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
        self.search_edit.returnPressed.connect(self.toolbar_refresh_action.trigger) # Trigger refresh on Enter
        filter_layout.addWidget(self.search_edit)

        self.show_inactive_check = QCheckBox("Show Inactive")
        self.show_inactive_check.stateChanged.connect(self.toolbar_refresh_action.trigger) # Trigger refresh on change
        filter_layout.addWidget(self.show_inactive_check)
        filter_layout.addStretch()
        self.main_layout.addLayout(filter_layout)

        # --- Table View ---
        self.customers_table = QTableView()
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.customers_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.customers_table.horizontalHeader().setStretchLastSection(True)
        self.customers_table.doubleClicked.connect(self._on_edit_customer) # Or view
        self.customers_table.setSortingEnabled(True)

        self.table_model = CustomerTableModel()
        self.customers_table.setModel(self.table_model)
        
        # Configure columns after model is set
        if "ID" in self.table_model._headers:
            self.customers_table.setColumnHidden(self.table_model._headers.index("ID"), True)
        if "Name" in self.table_model._headers:
            name_col_idx = self.table_model._headers.index("Name")
            self.customers_table.horizontalHeader().setSectionResizeMode(name_col_idx, QHeaderView.ResizeMode.Stretch)
        else: # Fallback if "Name" header changes
             self.customers_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)


        self.main_layout.addWidget(self.customers_table)
        self.setLayout(self.main_layout)

        if self.customers_table.selectionModel():
            self.customers_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()


    def _create_toolbar(self):
        self.toolbar = QToolBar("Customer Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add Customer", self)
        self.toolbar_add_action.triggered.connect(self._on_add_customer)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Customer", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_customer)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_toggle_active_action = QAction(QIcon(self.icon_path_prefix + "deactivate.svg"), "Toggle Active", self)
        self.toolbar_toggle_active_action.triggered.connect(self._on_toggle_active_status)
        self.toolbar.addAction(self.toolbar_toggle_active_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_customers()))
        self.toolbar.addAction(self.toolbar_refresh_action)


    @Slot()
    def _update_action_states(self):
        selected_rows = self.customers_table.selectionModel().selectedRows()
        has_selection = bool(selected_rows)
        single_selection = len(selected_rows) == 1
        
        self.toolbar_edit_action.setEnabled(single_selection)
        self.toolbar_toggle_active_action.setEnabled(single_selection)

    async def _load_customers(self):
        if not self.app_core.customer_manager:
            self.app_core.logger.error("CustomerManager not available in CustomersWidget.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Customer Manager component not available."))
            return
        try:
            search_term = self.search_edit.text().strip() or None
            active_only = not self.show_inactive_check.isChecked()
            
            # For MVP, pagination is handled by service if params are passed. UI doesn't have page controls yet.
            result: Result[List[CustomerSummaryData]] = await self.app_core.customer_manager.get_customers_for_listing(
                active_only=active_only, 
                search_term=search_term,
                page=1, # Default to first page
                page_size=200 # Load a reasonable number for MVP table
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                json_data = json.dumps([dto.model_dump() for dto in data_for_table], default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                error_msg = f"Failed to load customers: {', '.join(result.errors)}"
                self.app_core.logger.error(error_msg)
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))
        except Exception as e:
            error_msg = f"Unexpected error loading customers: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            # Convert list of dicts to list of CustomerSummaryData DTOs
            customer_summaries: List[CustomerSummaryData] = [CustomerSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(customer_summaries)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse customer data: {e}")
        except Exception as p_error: # Catch Pydantic validation errors too
            QMessageBox.critical(self, "Data Error", f"Invalid customer data format: {p_error}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_customer(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to add a customer.")
            return
        
        dialog = CustomerDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.customer_saved.connect(lambda _id: schedule_task_from_qt(self._load_customers()))
        dialog.exec()

    def _get_selected_customer_id(self) -> Optional[int]:
        selected_rows = self.customers_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1:
            QMessageBox.information(self, "Selection", "Please select a single customer.")
            return None
        return self.table_model.get_customer_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_customer(self):
        customer_id = self._get_selected_customer_id()
        if customer_id is None: return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit a customer.")
            return
            
        dialog = CustomerDialog(self.app_core, self.app_core.current_user.id, customer_id=customer_id, parent=self)
        dialog.customer_saved.connect(lambda _id: schedule_task_from_qt(self._load_customers()))
        dialog.exec()
        
    @Slot(QModelIndex)
    def _on_view_customer_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        customer_id = self.table_model.get_customer_id_at_row(index.row())
        if customer_id is None: return
        # For MVP, double-click also opens for edit. Can be changed to view-only later.
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to view/edit customer.")
            return
        dialog = CustomerDialog(self.app_core, self.app_core.current_user.id, customer_id=customer_id, parent=self)
        dialog.customer_saved.connect(lambda _id: schedule_task_from_qt(self._load_customers()))
        dialog.exec()


    @Slot()
    def _on_toggle_active_status(self):
        customer_id = self._get_selected_customer_id()
        if customer_id is None: return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to change customer status.")
            return
            
        # Confirm action
        customer_status_active = self.table_model.get_customer_status_at_row(self.customers_table.currentIndex().row())
        action_verb = "deactivate" if customer_status_active else "activate"
        reply = QMessageBox.question(self, f"Confirm {action_verb.capitalize()}",
                                     f"Are you sure you want to {action_verb} this customer?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        future = schedule_task_from_qt(
            self.app_core.customer_manager.toggle_customer_active_status(customer_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_toggle_active_result)
        else: self._handle_toggle_active_result(None)

    def _handle_toggle_active_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule customer status toggle."); return
        try:
            result: Result[Customer] = future.result()
            if result.is_success:
                action_verb_past = "activated" if result.value and result.value.is_active else "deactivated"
                QMessageBox.information(self, "Success", f"Customer {action_verb_past} successfully.")
                schedule_task_from_qt(self._load_customers()) # Refresh list
            else:
                QMessageBox.warning(self, "Error", f"Failed to toggle customer status:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Error handling toggle active status result: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

```
**Validation for `app/ui/customers/customers_widget.py`:**
*   **Imports**: Added `CustomerTableModel`, `CustomerDialog`, `CustomerSummaryData`, `Customer` (for type hint).
*   **`__init__`**: Initializes `icon_path_prefix` and calls `_init_ui`. Schedules initial `_load_customers`.
*   **`_init_ui`**:
    *   Sets up a `QVBoxLayout`.
    *   Calls `_create_toolbar()`.
    *   Adds filter UI: `QLineEdit` for search, `QCheckBox` for "Show Inactive". Search `returnPressed` and checkbox `stateChanged` trigger a refresh.
    *   Creates `QTableView` (`self.customers_table`) and `CustomerTableModel` (`self.table_model`).
    *   Sets model to table, configures table properties (selection, sorting, hides "ID" column, sets "Name" column to stretch).
    *   Connects `selectionChanged` to `_update_action_states`.
*   **`_create_toolbar`**: Adds actions "Add Customer", "Edit Customer", "Toggle Active", "Refresh List", with icons and connects them to slots.
*   **`_update_action_states`**: Enables/disables toolbar buttons based on table selection.
*   **`_load_customers`**:
    *   Collects filter parameters (search term from `search_edit`, active status from `show_inactive_check`).
    *   Calls `self.app_core.customer_manager.get_customers_for_listing()` with filters.
    *   Handles `Result` and passes `List[CustomerSummaryData]` (as JSON string) to `_update_table_model_slot`.
*   **`_update_table_model_slot`**:
    *   Parses JSON, validates DTOs, and updates `self.table_model`.
    *   Calls `_update_action_states()`.
*   **Action Slots (`_on_add_customer`, `_on_edit_customer`, `_on_toggle_active_status`)**:
    *   Check for `current_user`.
    *   `_on_add_customer`: Launches `CustomerDialog` with no `customer_id`. Connects `customer_saved` signal to refresh.
    *   `_on_edit_customer`: Gets selected customer ID, launches `CustomerDialog` with ID. Connects `customer_saved`.
    *   `_on_view_customer_double_click`: Similar to edit for MVP.
    *   `_on_toggle_active_status`: Gets ID, confirms, calls manager method, handles result, refreshes.
*   **Helper `_get_selected_customer_id()`**: For retrieving ID from selected row.

This `CustomersWidget` now provides a functional UI for basic customer management.

---
**Next Steps:**

1.  **Review `app/ui/customers/__init__.py`**: Ensure it exports `CustomersWidget`, `CustomerDialog`, and `CustomerTableModel`.
2.  **Review `app/ui/main_window.py`**: Ensure `CustomersWidget` is correctly instantiated and added as a tab.
3.  **Thorough Testing (Phase B - UI Testing & Phase 4 from overall plan)**: Manually test the entire Customer Management workflow:
    *   Listing customers (initially empty).
    *   Adding new customers (with validation).
    *   Viewing the list update.
    *   Editing existing customers.
    *   Toggling active status.
    *   Searching/filtering.
    *   Checking data persistence in the database (`business.customers` table).
    *   Checking audit logs for customer creation/updates.

After these files are updated in your project, the basic Customer Management module should be functional and testable.
