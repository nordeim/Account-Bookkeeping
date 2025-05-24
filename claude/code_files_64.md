<think>
The application continues to launch and shut down cleanly. We have successfully defined `app/ui/accounting/fiscal_year_dialog.py` and updated `app/utils/pydantic_models.py` and `app/accounting/fiscal_period_manager.py`. The `SettingsWidget` has been enhanced to include a fiscal year management section.

The `JournalEntryDialog` was also just created in the previous step.

**Current Step: Phase 2.1 - UI for Journal Entries (Continued)**

The next logical piece from the plan is to create:
1.  **`app/ui/accounting/journal_entries_widget.py` (New File)**: This widget will display a list of journal entries and provide actions like "New", "Edit Draft", "Post".
2.  **`app/ui/accounting/journal_entry_table_model.py` (New File)**: A custom `QAbstractTableModel` for the `QTableView` in `JournalEntriesWidget`.
3.  **Update `app/ui/accounting/accounting_widget.py`**: To add a tab for the new `JournalEntriesWidget`.

**Plan for `app/ui/accounting/journal_entry_table_model.py`:**
*   Subclass `QAbstractTableModel`.
*   Store `List[JournalEntryData]` or `List[Dict[str, Any]]` (summary data for JE list).
*   Implement `rowCount`, `columnCount`, `data`, `headerData`.
*   Method to update data and refresh the view (`update_data(new_data)`).

**Plan for `app/ui/accounting/journal_entries_widget.py`:**
*   **UI Elements:**
    *   `QTableView` (`self.entries_table`) using `JournalEntryTableModel`.
    *   Toolbar with `QAction`s or `QPushButton`s:
        *   "New Journal Entry"
        *   "Edit Selected Draft" (enabled if a draft is selected)
        *   "View Selected Entry" (enabled if an entry is selected)
        *   "Post Selected Draft(s)" (enabled if draft(s) selected)
        *   "Reverse Posted Entry" (enabled if a posted entry is selected)
        *   "Refresh List"
    *   Filter controls (optional for first pass, but good to plan): `QDateEdit` for start/end date, `QComboBox` for status (Draft, Posted, All).
*   **Logic:**
    *   `__init__`: Setup UI, create model, connect signals. Call `_load_entries()` via `QTimer`.
    *   `_load_entries()` (async):
        *   Fetch summary data for journal entries from `app_core.journal_entry_manager.get_journal_entries_summary(filters)`. (This manager method needs to be defined).
        *   Serialize data to JSON.
        *   Use `QMetaObject.invokeMethod` to call a slot (`_update_table_model_slot`) to update the table model.
    *   `_update_table_model_slot(json_data_str)`: Deserialize and update the table model.
    *   Slot for "New Journal Entry":
        *   Create and `exec_()` `JournalEntryDialog`.
        *   If accepted (JE saved), call `_load_entries()` to refresh.
    *   Slot for "Edit Selected Draft":
        *   Get selected entry ID from table.
        *   If it's a draft, launch `JournalEntryDialog` with the `journal_entry_id`.
        *   If accepted, refresh list.
    *   Slot for "View Selected Entry":
        *   Launch `JournalEntryDialog` in a read-only mode.
    *   Slot for "Post Selected Draft(s)":
        *   Get selected draft entry ID(s).
        *   For each, schedule `app_core.journal_entry_manager.post_journal_entry()`.
        *   Refresh list. Display aggregated success/failure.
    *   Slot for "Reverse Posted Entry": (More complex, might defer parts for MVP)
        *   Get selected posted entry ID.
        *   Launch a confirmation dialog, possibly `JournalEntryDialog` pre-filled for reversal.
        *   Schedule `app_core.journal_entry_manager.reverse_journal_entry()`.
        *   Refresh list.

I'll start with `journal_entry_table_model.py` and then `journal_entries_widget.py`. The backend manager methods will be stubbed or defined as needed when the UI interactions are implemented.
</think>

This is great! The application is stable, and the foundational fiscal year management UI is taking shape. Now, we'll build the crucial **Journal Entry** interface.

This involves:
1.  Creating a custom table model for displaying journal entries: `app/ui/accounting/journal_entry_table_model.py`.
2.  Creating the main widget to list and manage journal entries: `app/ui/accounting/journal_entries_widget.py`.
3.  Integrating this new widget into the "Accounting" tab of `app/ui/accounting/accounting_widget.py`.
4.  Ensuring the previously created `app/ui/accounting/journal_entry_dialog.py` is correctly launched from the new widget.

---
**1. Create `app/ui/accounting/journal_entry_table_model.py` (New File)**

This model will handle the data for the `QTableView` in `JournalEntriesWidget`. For the list view, we typically only need summary data for each journal entry.

```python
# File: app/ui/accounting/journal_entry_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date

class JournalEntryTableModel(QAbstractTableModel):
    def __init__(self, data: List[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["Entry No", "Date", "Description", "Type", "Total Amount", "Status"]
        self._data: List[Dict[str, Any]] = data or []

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        row_data = self._data[index.row()]
        column_name = self._headers[index.column()].lower().replace(" ", "_") # e.g. "Entry No" -> "entry_no"

        if role == Qt.ItemDataRole.DisplayRole:
            value = row_data.get(column_name)
            if column_name == "date" and isinstance(value, str): # Assuming date comes as ISO string from JSON
                try:
                    dt_value = date.fromisoformat(value)
                    return dt_value.strftime('%d/%m/%Y')
                except ValueError:
                    return value # Return original string if parsing fails
            elif column_name == "total_amount" and value is not None:
                try:
                    return f"{Decimal(str(value)):,.2f}"
                except InvalidOperation:
                    return str(value)
            return str(value) if value is not None else ""
        
        if role == Qt.ItemDataRole.UserRole: # To store the ID
            return row_data.get("id")
            
        return None

    def get_journal_entry_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            return self._data[row].get("id")
        return None
        
    def get_journal_entry_status_at_row(self, row: int) -> Optional[str]:
        if 0 <= row < len(self._data):
            return self._data[row].get("status")
        return None

    def update_data(self, new_data: List[Dict[str, Any]]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()
```

**Validation of `app/ui/accounting/journal_entry_table_model.py`:**
*   Subclasses `QAbstractTableModel`.
*   Stores data as `List[Dict[str, Any]]` (summary for each JE).
*   Implements `rowCount`, `columnCount`, `data`, `headerData`.
*   `data()` method handles basic formatting for date and amount.
*   `UserRole` is used to store the `id` of the journal entry for easy retrieval.
*   `update_data()` allows refreshing the model.

---
**2. Create `app/ui/accounting/journal_entries_widget.py` (New File)**

This widget will contain the table view and action buttons.

```python
# File: app/ui/accounting/journal_entries_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING
import json
from datetime import date

from app.ui.accounting.journal_entry_dialog import JournalEntryDialog
from app.ui.accounting.journal_entry_table_model import JournalEntryTableModel
from app.common.enums import JournalTypeEnum # For status or type filtering
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import JournalEntryData # For type hint

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class JournalEntriesWidget(QWidget):
    def __init__(self, app_core: "ApplicationCore", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_entries()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        self.entries_table = QTableView()
        self.entries_table.setAlternatingRowColors(True)
        self.entries_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.entries_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.entries_table.horizontalHeader().setStretchLastSection(True)
        self.entries_table.doubleClicked.connect(self.on_view_entry) # Or edit on double click for drafts

        self.table_model = JournalEntryTableModel()
        self.entries_table.setModel(self.table_model)
        self.main_layout.addWidget(self.entries_table)

        self.setLayout(self.main_layout)

    def _create_toolbar(self):
        from PySide6.QtCore import QSize
        self.toolbar = QToolBar("Journal Entries Toolbar")
        self.toolbar.setObjectName("JournalEntriesToolbar")
        self.toolbar.setIconSize(QSize(20, 20)) # Slightly smaller icons for more compact toolbar

        icon_path_prefix = "resources/icons/" # Fallback, QRC preferred
        try:
            import app.resources_rc 
            icon_path_prefix = ":/icons/"
        except ImportError:
            pass 

        self.new_entry_action = QAction(QIcon(icon_path_prefix + "add.svg"), "New Entry", self) # Assuming add.svg exists
        self.new_entry_action.triggered.connect(self.on_new_entry)
        self.toolbar.addAction(self.new_entry_action)

        self.edit_entry_action = QAction(QIcon(icon_path_prefix + "edit.svg"), "Edit Draft", self)
        self.edit_entry_action.triggered.connect(self.on_edit_entry)
        self.toolbar.addAction(self.edit_entry_action)
        
        self.view_entry_action = QAction(QIcon(icon_path_prefix + "view.svg"), "View Entry", self) # Assuming view.svg
        self.view_entry_action.triggered.connect(self.on_view_entry)
        self.toolbar.addAction(self.view_entry_action)

        self.toolbar.addSeparator()

        self.post_entry_action = QAction(QIcon(icon_path_prefix + "post.svg"), "Post Selected", self) # Assuming post.svg
        self.post_entry_action.triggered.connect(self.on_post_entry)
        self.toolbar.addAction(self.post_entry_action)
        
        self.reverse_entry_action = QAction(QIcon(icon_path_prefix + "reverse.svg"), "Reverse Selected", self) # Assuming reverse.svg
        self.reverse_entry_action.triggered.connect(self.on_reverse_entry)
        self.toolbar.addAction(self.reverse_entry_action)

        self.toolbar.addSeparator()
        self.refresh_action = QAction(QIcon(icon_path_prefix + "refresh.svg"), "Refresh", self)
        self.refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_entries()))
        self.toolbar.addAction(self.refresh_action)

        # Enable/disable actions based on selection
        self.entries_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states() # Initial state


    @Slot()
    def _update_action_states(self):
        selected_indexes = self.entries_table.selectionModel().selectedRows()
        has_selection = bool(selected_indexes)
        is_draft = False
        is_posted = False

        if has_selection:
            # For simplicity, consider the first selected item for status-dependent actions
            first_selected_row = selected_indexes[0].row()
            status = self.table_model.get_journal_entry_status_at_row(first_selected_row)
            is_draft = status == "Draft" # Assuming status string from your data
            is_posted = status == "Posted"

        self.edit_entry_action.setEnabled(has_selection and is_draft)
        self.view_entry_action.setEnabled(has_selection)
        self.post_entry_action.setEnabled(has_selection and is_draft) # Can be enhanced for multi-select
        self.reverse_entry_action.setEnabled(has_selection and is_posted)


    async def _load_entries(self):
        # This method runs in the asyncio thread
        if not self.app_core.journal_entry_manager:
            # Error handling for missing manager
            return
        try:
            # TODO: Implement get_journal_entries_summary in JournalEntryManager
            # It should return List[Dict[str, Any]] with keys matching table_model headers
            # For now, let's assume it returns a list of ORM objects and we serialize them
            entries_orm: List[JournalEntry] = await self.app_core.journal_entry_manager.journal_service.get_all() # Placeholder
            
            entries_data_for_table: List[Dict[str, Any]] = []
            for je in entries_orm:
                total_debit = sum(line.debit_amount for line in je.lines)
                entries_data_for_table.append({
                    "id": je.id,
                    "entry_no": je.entry_no,
                    "date": je.entry_date, # Will be serialized by json_converter
                    "description": je.description,
                    "type": je.journal_type,
                    "total_amount": total_debit, # Or sum of debits/credits
                    "status": "Posted" if je.is_posted else "Draft"
                })
            
            json_data = json.dumps(entries_data_for_table, default=json_converter)
            QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, json_data))
        except Exception as e:
            error_msg = f"Failed to load journal entries: {str(e)}"
            print(error_msg)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            entries_data: List[Dict[str, Any]] = json.loads(json_data_str)
            # Convert date strings back to date objects if necessary for model or sorting
            for entry in entries_data:
                if 'date' in entry and isinstance(entry['date'], str):
                    try: entry['date'] = python_date.fromisoformat(entry['date'])
                    except ValueError: pass # Keep as string if not ISO
            self.table_model.update_data(entries_data)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse journal entry data: {e}")
        self._update_action_states()


    @Slot()
    def on_new_entry(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to create a journal entry.")
            return
        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.journal_entry_saved.connect(lambda _id: schedule_task_from_qt(self._load_entries()))
        dialog.exec() # For modal dialog

    @Slot()
    def on_edit_entry(self):
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Selection", "Please select a draft journal entry to edit.")
            return
        
        row = selected_rows[0].row() # Assuming single selection for now
        entry_id = self.table_model.get_journal_entry_id_at_row(row)
        entry_status = self.table_model.get_journal_entry_status_at_row(row)

        if entry_id is None or entry_status != "Draft":
            QMessageBox.warning(self, "Edit Error", "Only draft entries can be edited. This entry is not a draft or ID is missing.")
            return
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit.")
            return

        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, journal_entry_id=entry_id, parent=self)
        dialog.journal_entry_saved.connect(lambda _id: schedule_task_from_qt(self._load_entries()))
        dialog.exec()

    @Slot()
    def on_view_entry(self):
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Selection", "Please select a journal entry to view.")
            return
        
        row = selected_rows[0].row()
        entry_id = self.table_model.get_journal_entry_id_at_row(row)
        if entry_id is None: return

        if not self.app_core.current_user: # Though view might not need user strictly
             QMessageBox.warning(self, "Auth Error", "Please log in.")
             return

        # Launch dialog in a read-only mode (dialog needs to support this)
        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, journal_entry_id=entry_id, parent=self)
        # TODO: Add a method to JournalEntryDialog to set read-only state based on existing_journal_entry.is_posted
        dialog.exec()


    @Slot()
    def on_post_entry(self):
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Selection", "Please select one or more draft journal entries to post.")
            return
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to post entries.")
            return

        entries_to_post = []
        for index in selected_rows:
            row = index.row()
            entry_id = self.table_model.get_journal_entry_id_at_row(row)
            entry_status = self.table_model.get_journal_entry_status_at_row(row)
            if entry_id and entry_status == "Draft":
                entries_to_post.append(entry_id)
        
        if not entries_to_post:
            QMessageBox.information(self, "Selection", "No draft entries selected for posting.")
            return

        schedule_task_from_qt(self._perform_post_entries(entries_to_post, self.app_core.current_user.id))

    async def _perform_post_entries(self, entry_ids: List[int], user_id: int):
        if not self.app_core.journal_entry_manager: return

        success_count = 0
        errors = []
        for entry_id in entry_ids:
            result = await self.app_core.journal_entry_manager.post_journal_entry(entry_id, user_id)
            if result.is_success:
                success_count += 1
            else:
                errors.append(f"ID {entry_id}: {', '.join(result.errors)}")
        
        message = f"{success_count} of {len(entry_ids)} entries posted."
        if errors:
            message += "\nErrors:\n" + "\n".join(errors)
        
        QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information" if not errors else "warning", Qt.ConnectionType.QueuedConnection,
            Q_ARG(QWidget, self), Q_ARG(str, "Posting Complete" if not errors else "Posting Partially Failed"), 
            Q_ARG(str, message))
        
        schedule_task_from_qt(self._load_entries()) # Refresh list

    @Slot()
    def on_reverse_entry(self):
        # Implementation for reversing an entry
        QMessageBox.information(self, "Reverse Entry", "Reverse entry functionality to be implemented.")

```

**Validation of `app/ui/accounting/journal_entry_table_model.py` and `journal_entries_widget.py`:**
*   **`JournalEntryTableModel`**:
    *   Basic structure for `rowCount`, `columnCount`, `data`, `headerData`.
    *   `data()` method handles display formatting for date and amount. Stores JE `id` in `UserRole`.
*   **`JournalEntriesWidget`**:
    *   Sets up a `QTableView` with `JournalEntryTableModel`.
    *   Creates a toolbar with actions: "New", "Edit Draft", "View", "Post", "Reverse", "Refresh".
    *   `_load_entries()` (async) fetches JE summary data (currently placeholder using `get_all`, needs specific summary method in service), serializes to JSON, and updates model via `QMetaObject`.
    *   `_update_table_model_slot()` deserializes and updates the table model.
    *   `on_new_entry()` creates and shows `JournalEntryDialog`. Connects `journal_entry_saved` signal to refresh.
    *   `on_edit_entry()` and `on_view_entry()` get selected JE ID and launch `JournalEntryDialog` (view mode needs to be handled by dialog).
    *   `on_post_entry()` gets selected draft JEs and schedules `_perform_post_entries`.
    *   `_perform_post_entries()` (async) calls manager to post, aggregates results, shows message.
    *   `_update_action_states()` slot to enable/disable toolbar actions based on selection and entry status.
*   **Missing SVGs**: Placeholder icons `add.svg`, `view.svg`, `post.svg`, `reverse.svg` are referenced. These will need to be created.

---
**3. Update `app/ui/accounting/accounting_widget.py`**

Add a tab for the new `JournalEntriesWidget`.

```python
# File: app/ui/accounting/accounting_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget
from app.ui.accounting.chart_of_accounts_widget import ChartOfAccountsWidget
from app.ui.accounting.journal_entries_widget import JournalEntriesWidget # Import new widget
from app.core.application_core import ApplicationCore 

class AccountingWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None): 
        super().__init__(parent)
        self.app_core = app_core
        
        self.layout = QVBoxLayout(self)
        
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        self.coa_widget = ChartOfAccountsWidget(self.app_core)
        self.tab_widget.addTab(self.coa_widget, "Chart of Accounts")
        
        self.journal_entries_widget = JournalEntriesWidget(self.app_core) # Create instance
        self.tab_widget.addTab(self.journal_entries_widget, "Journal Entries") # Add as tab
        
        other_label = QLabel("Other Accounting Features (e.g., Fiscal Periods, Budgets)")
        self.tab_widget.addTab(other_label, "More...")

        self.setLayout(self.layout)
```
**Validation:** `JournalEntriesWidget` imported and added as a tab.

---
**4. Update `app/ui/accounting/__init__.py`**

Export the new widget and model.
```python
# File: app/ui/accounting/__init__.py
from .accounting_widget import AccountingWidget
from .chart_of_accounts_widget import ChartOfAccountsWidget
from .account_dialog import AccountDialog
from .fiscal_year_dialog import FiscalYearDialog 
from .journal_entry_dialog import JournalEntryDialog # Added
from .journal_entries_widget import JournalEntriesWidget # Added
from .journal_entry_table_model import JournalEntryTableModel # Added

__all__ = [
    "AccountingWidget", 
    "ChartOfAccountsWidget", 
    "AccountDialog",
    "FiscalYearDialog", 
    "JournalEntryDialog",
    "JournalEntriesWidget",
    "JournalEntryTableModel",
]
```
**Validation:** New classes exported.

---
**Placeholder SVG Icons to Create:**
(If these are not already present from previous steps, create them in `resources/icons/`)

*   `resources/icons/add.svg` (generic plus sign)
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
    ```
*   `resources/icons/view.svg` (generic eye icon)
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
    ```
*   `resources/icons/post.svg` (generic checkmark or upload icon)
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>
    ```
*   `resources/icons/reverse.svg` (generic undo arrow)
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C20.36 11.36 16.79 8 12.5 8z"/></svg>
    ```
*   `resources/icons/remove.svg` (generic minus sign)
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19 13H5v-2h14v2z"/></svg>
    ```

**Next Steps:**

1.  **Create/Update Files:**
    *   Create `app/ui/accounting/journal_entry_table_model.py` with the content provided.
    *   Create `app/ui/accounting/journal_entries_widget.py` with the content provided.
    *   Update `app/ui/accounting/accounting_widget.py`.
    *   Update `app/ui/accounting/__init__.py`.
    *   Ensure `app/ui/accounting/journal_entry_dialog.py` (from previous step) is in place.
2.  **Add SVG Icons**: Create the new SVG files (`add.svg`, `view.svg`, `post.svg`, `reverse.svg`, `remove.svg`) in `resources/icons/`.
3.  **Backend Implementation (Following this UI setup):**
    *   Add `get_journal_entries_summary()` method to `JournalEntryManager` (and potentially `JournalService`).
    *   Implement `update_journal_entry()` in `JournalEntryManager`.
4.  **Run the application**:
    ```bash
    poetry run sg_bookkeeper
    ```

After these changes, you should see a "Journal Entries" tab under "Accounting". It will initially be empty. Clicking "New Entry" should launch the `JournalEntryDialog`. The backend manager methods for saving/posting will need to be implemented next for full functionality.
