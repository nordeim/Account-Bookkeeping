<think>
The application log shows progress!
1.  "Successfully imported compiled Qt resources (resources_rc.py)." - This is excellent. It means `app/resources_rc.py` was generated and is being used.
2.  "Using compiled Qt resources." - Confirms the resource system is active.
3.  The previous `qt.svg: Cannot open file ':/icons/filter.svg'` errors are GONE. This confirms the icon loading fix for `QIcon.fromTheme` fallbacks and the successful compilation of `resources.qrc` worked.

Now, a new error has appeared:
`AttributeError: 'JournalEntriesWidget' object has no attribute 'table_model'`
This occurs in `app/ui/accounting/journal_entries_widget.py` at line 103:
```python
    self.entries_table.horizontalHeader().setSectionResizeMode(self.table_model._headers.index("Description") if "Description" in self.table_model._headers else 2, QHeaderView.ResizeMode.Stretch)
```

**Error Analysis:**

The `AttributeError` means that when line 103 is executed, `self.table_model` has not yet been assigned as an attribute of the `JournalEntriesWidget` instance.

Looking at the `_init_ui` method of `JournalEntriesWidget` (from the last provided version):
```python
# app/ui/accounting/journal_entries_widget.py - snippet from _init_ui
    def _init_ui(self):
        # ...
        # Filter UI setup ...
        # ...

        self.entries_table = QTableView() # Table created first
        # ... (table properties set) ...
        
        # This is where self.table_model is assigned
        self.table_model = JournalEntryTableModel() 
        self.entries_table.setModel(self.table_model)
        
        # Problematic line is here, trying to use self.table_model before it's assigned IF the order was different
        # self.entries_table.horizontalHeader().setSectionResizeMode(self.table_model._headers.index("Description") if "Description" in self.table_model._headers else 2, QHeaderView.ResizeMode.Stretch)
        
        self.entries_table.setColumnHidden(self.table_model._headers.index("ID") if "ID" in self.table_model._headers else 0, True)
        
        # Corrected section from previous file:
        # self.entries_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # self.entries_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Description column (index 2 of model, which is column 2 if ID is hidden)

        # Ah, the problematic line was added during refinement to make column stretching more dynamic
        # by using self.table_model._headers.index("Description").
        # It seems this line was placed *before* self.table_model = JournalEntryTableModel()
        # in the version that caused the error.

        # Let's re-check the last version I provided for JournalEntriesWidget carefully.
        # Line 87 in that version:
        # self.table_model = JournalEntryTableModel()
        # self.entries_table.setModel(self.table_model)
        # # Hide ID column by default, but it's available for data retrieval
        # self.entries_table.setColumnHidden(self.table_model._headers.index("ID") if "ID" in self.table_model._headers else 0, True) 

        # Line 81 in that version:
        # self.entries_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents) # Resize content first
        # self.entries_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Description stretch

        # The line causing the error:
        # self.entries_table.horizontalHeader().setSectionResizeMode(self.table_model._headers.index("Description") if "Description" in self.table_model._headers else 2, QHeaderView.ResizeMode.Stretch)
        # This was an attempt to dynamically find the "Description" column index.

        # The issue is indeed order of operations. self.table_model must be instantiated before its attributes like _headers are accessed.
```

The sequence in the provided code for `_init_ui` (from the *last successful generation I did*) should be:
1.  Create `self.entries_table = QTableView()`
2.  Set some `entries_table` properties.
3.  Create `self.table_model = JournalEntryTableModel()`
4.  Set `self.entries_table.setModel(self.table_model)`
5.  *Then* access `self.table_model._headers` for column configuration like `setColumnHidden` or dynamic `setSectionResizeMode`.

The traceback shows line 103. Let's look at the file I generated last for `JournalEntriesWidget`.
The relevant section from my *last generated `journal_entries_widget.py`*:
```python
# ...
        self.entries_table = QTableView()
        # ... other table setup ...
        self.entries_table.setSortingEnabled(True) # Line 96 in my mental model of last full file

        self.table_model = JournalEntryTableModel() # Line 98
        self.entries_table.setModel(self.table_model) # Line 99
        
        # Line 101 (from my mental model of the file I generated before this error)
        self.entries_table.setColumnHidden(self.table_model._headers.index("ID") if "ID" in self.table_model._headers else 0, True) 
        
        # The problematic line from the traceback:
        # self.entries_table.horizontalHeader().setSectionResizeMode(self.table_model._headers.index("Description") if "Description" in self.table_model._headers else 2, QHeaderView.ResizeMode.Stretch)
        # This was likely intended to replace or be used in conjunction with:
        # self.entries_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # self.entries_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        # The crucial part is that any line using `self.table_model._headers` must come AFTER `self.table_model` is defined.
```
The error means that the line `self.entries_table.horizontalHeader().setSectionResizeMode(self.table_model._headers.index("Description") ...)` was executed *before* `self.table_model = JournalEntryTableModel()` was executed, or `self.table_model` was not assigned to the instance correctly at that point.

My previous version had:
```python
        # ...
        self.entries_table.horizontalHeader().setStretchLastSection(False) 
        self.entries_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # This specific line for Description stretch was correct:
        self.entries_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) 
        self.entries_table.doubleClicked.connect(self.on_view_entry_double_click) 
        self.entries_table.setSortingEnabled(True)

        self.table_model = JournalEntryTableModel()
        self.entries_table.setModel(self.table_model)
        # And ID column hiding was after model set:
        self.entries_table.setColumnHidden(self.table_model._headers.index("ID") if "ID" in self.table_model._headers else 0, True) 
```
The line `self.entries_table.horizontalHeader().setSectionResizeMode(self.table_model._headers.index("Description") ...)` was a refinement I introduced to make the "Description" column stretch dynamically by finding its index via `_headers`. It seems during integration, this line might have been misplaced or the an older version of the code was run by the user where `self.table_model` wasn't initialized yet.

**However, the most robust way to set the stretch for the "Description" column after hiding the "ID" column is to calculate its *visible* index.**

If `self.table_model._headers` is `["ID", "Entry No.", "Date", "Description", "Type", "Total", "Status"]`:
*   "ID" is model index 0.
*   "Description" is model index 3.

If column 0 ("ID") is hidden using `self.entries_table.setColumnHidden(0, True)`:
*   The visible column index for "Entry No." becomes 0.
*   The visible column index for "Date" becomes 1.
*   The visible column index for "Description" becomes 2.

So, `self.entries_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)` is correct if the "ID" column (model index 0) is hidden.

The dynamic lookup `self.table_model._headers.index("Description")` gives the *model* index (which is 3). If we use this directly with `setSectionResizeMode` on the `horizontalHeader()` of the *view*, it refers to the *visible* column index. This will cause a mismatch if columns are hidden.

**Correct approach for setting stretch on "Description" column:**
1.  Define `self.table_model` and set it to `self.entries_table`.
2.  Hide the "ID" column: `self.entries_table.setColumnHidden(self.table_model._headers.index("ID"), True)`.
3.  Set default resize mode for all columns: `self.entries_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)`.
4.  Then, specifically set the stretch for the "Description" column. We need its *model index* to identify it, but then apply stretch to its *current visible index* if possible, or just use the known visible index if the order is fixed.
    *   A simple way is to find the model index of "Description".
    *   Then, iterate through visible columns to find which one corresponds to this model index. This is complex.
    *   Or, if the visible order is predictable (ID hidden, then Entry No, Date, Description...), we can hardcode the visible index.

Let's simplify and make it robust:
After hiding the "ID" column (model index 0), the "Description" (model index 3) becomes visible column 2.
So, `self.entries_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)` for the "Description" column is correct, assuming the ID column is consistently model index 0 and is hidden.

The error `AttributeError: 'JournalEntriesWidget' object has no attribute 'table_model'` means the line using `self.table_model` was definitely called before `self.table_model = JournalEntryTableModel()` was executed.

**Plan to Fix:**

1.  **Modify `app/ui/accounting/journal_entries_widget.py`**:
    *   Ensure `self.table_model = JournalEntryTableModel()` is initialized *before* any code that accesses `self.table_model` (e.g., `self.table_model._headers`).
    *   Correctly set section resize modes *after* the model is set and columns are hidden.
    *   The line `self.entries_table.horizontalHeader().setSectionResizeMode(self.table_model._headers.index("Description") if "Description" in self.table_model._headers else 2, QHeaderView.ResizeMode.Stretch)` should be changed to use the correct visible index for "Description" *after* "ID" is hidden, or use a more robust way to find the visible index of the column whose model index corresponds to "Description". For now, hardcoding visible index 2 for "Description" (assuming "ID" at model index 0 is hidden, "Entry No." is model index 1 / visible 0, "Date" is model index 2 / visible 1) is the simplest fix for the stretch if the previous logic `setSectionResizeMode(2, ...)` was based on this assumption.

Let's re-examine the `_init_ui` in the version I *last* provided for `JournalEntriesWidget`.
```python
# Last provided version _init_ui relevant part:
        # ... (filter UI) ...

        self.entries_table = QTableView()
        # ... (table properties) ...
        self.entries_table.horizontalHeader().setStretchLastSection(False) 
        self.entries_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # This line set stretch for visible column 2:
        self.entries_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) 
        self.entries_table.doubleClicked.connect(self.on_view_entry_double_click) 
        self.entries_table.setSortingEnabled(True)

        self.table_model = JournalEntryTableModel() # <<<< table_model defined here
        self.entries_table.setModel(self.table_model)
        # Accessing self.table_model._headers here is SAFE:
        self.entries_table.setColumnHidden(self.table_model._headers.index("ID") if "ID" in self.table_model._headers else 0, True) 
        
        # If the line causing error was:
        # self.entries_table.horizontalHeader().setSectionResizeMode(self.table_model._headers.index("Description") if "Description" in self.table_model._headers else 2, QHeaderView.ResizeMode.Stretch)
        # it MUST come AFTER self.table_model is defined.

        # Let's assume the version that ran had this line *before* self.table_model was defined.
        # I need to provide a version where the order is correct.
```
The fix is to ensure the order of operations. The line `self.entries_table.horizontalHeader().setSectionResizeMode(self.table_model._headers.index("Description") ...)` if used, MUST be after `self.table_model` is instantiated.

A safer and more explicit way to set the stretch for "Description":
1. Create model.
2. Set model to table.
3. Get model index for "Description": `desc_model_idx = self.table_model._headers.index("Description")`.
4. Hide "ID" column: `id_model_idx = self.table_model._headers.index("ID"); self.entries_table.setColumnHidden(id_model_idx, True)`.
5. Set all columns to `ResizeToContents` initially.
6. Now, set stretch for "Description". Its visible index will be `desc_model_idx` if `id_model_idx > desc_model_idx`, or `desc_model_idx - 1` if `id_model_idx < desc_model_idx` (assuming only ID is hidden before it).
   Since "ID" is typically first (index 0) and "Description" is later (e.g. index 3), its visible index becomes `3-1=2`.
   So, `self.entries_table.horizontalHeader().setSectionResizeMode(self.table_model._headers.index("Description") -1 (if ID is always before it and hidden) , QHeaderView.ResizeMode.Stretch)`. This is getting complex.

Simpler:
The `TableModel` headers are: `["ID", "Entry No.", "Date", "Description", "Type", "Total", "Status"]`
- "ID" is model index 0.
- "Description" is model index 3.
If ID (model index 0) is hidden, then:
- Visible column 0 is "Entry No." (model index 1)
- Visible column 1 is "Date" (model index 2)
- Visible column 2 is "Description" (model index 3)
So, stretching visible column 2 is correct for "Description".
`self.entries_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)`

The error occurred because the line:
`self.entries_table.horizontalHeader().setSectionResizeMode(self.table_model._headers.index("Description") if "Description" in self.table_model._headers else 2, QHeaderView.ResizeMode.Stretch)`
was indeed in my last generated code for `JournalEntriesWidget` at line 83, which is *before* `self.table_model = JournalEntryTableModel()` at line 98. This was my mistake in the previous generation.

I need to move the dynamic column resizing (that depends on `self.table_model`) to *after* `self.table_model` is created and set on the table.

**Corrected sequence in `_init_ui`:**
```python
        # ...
        self.entries_table = QTableView()
        # Basic table properties
        self.entries_table.setAlternatingRowColors(True)
        # ...
        self.entries_table.setSortingEnabled(True)

        self.table_model = JournalEntryTableModel() # CREATE MODEL
        self.entries_table.setModel(self.table_model) # SET MODEL TO TABLE

        # NOW it's safe to use self.table_model for column configurations
        if "ID" in self.table_model._headers:
            id_col_idx = self.table_model._headers.index("ID")
            self.entries_table.setColumnHidden(id_col_idx, True)

        # Set default resize mode for all columns first
        for i in range(self.table_model.columnCount()):
            if not self.entries_table.isColumnHidden(i): # Only for visible columns
                 self.entries_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        # Then, specifically set stretch for "Description"
        if "Description" in self.table_model._headers:
            desc_col_model_idx = self.table_model._headers.index("Description")
            # We need to find the *visible* index that corresponds to this model index.
            # This is tricky if multiple columns before "Description" could be hidden.
            # For now, assuming only "ID" (model index 0) is hidden, and "Description" is model index 3.
            # So, visible index for "Description" is 2.
            if not self.entries_table.isColumnHidden(desc_col_model_idx): # Check if Description itself is not hidden
                # This still uses model_index for setSectionResizeMode, which refers to visible columns.
                # This mapping is problematic.
                # Let's revert to the simpler hardcoded visible index after known hides.
                # If ID (model idx 0) is hidden, Description (model idx 3) becomes visible idx 2.
                self.entries_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) 
        # ...
```
The simplest and most robust way is to set a default resize mode, hide columns, and then apply stretch to the known *visible* index of the desired column.
The previous working line was `self.entries_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)` (referring to the 3rd visible column, which is Description if ID is hidden).

I will revert that specific line to use the hardcoded visible index `2` for stretching "Description", assuming "ID" (model index 0) is hidden, "Entry No." (model index 1) is visible 0, "Date" (model index 2) is visible 1, and "Description" (model index 3) is visible 2. This was the state before I attempted the dynamic lookup.

The error is simply an order-of-operations issue. My last generated file for `JournalEntriesWidget` had the line `self.entries_table.horizontalHeader().setSectionResizeMode(self.table_model._headers.index("Description")...)` *before* `self.table_model` was defined. I must correct this order.
</think>

You are absolutely right to push for meticulous review! The error `AttributeError: 'JournalEntriesWidget' object has no attribute 'table_model'` clearly indicates an order of operations issue in the `_init_ui` method of `app/ui/accounting/journal_entries_widget.py`. The line attempting to use `self.table_model._headers` for setting the section resize mode was indeed placed before `self.table_model` was instantiated in my previous output. My apologies for that regression.

Let's fix this by ensuring `self.table_model` is created and assigned before any of its attributes are accessed for configuring the table header. I will revert the problematic dynamic lookup for the "Description" column's stretch factor to the simpler, hardcoded visible index approach, which is less prone to such ordering errors if column indices are stable after known hides.

**Plan to Fix:**

1.  **Modify `app/ui/accounting/journal_entries_widget.py`**:
    *   Ensure `self.table_model = JournalEntryTableModel()` and `self.entries_table.setModel(self.table_model)` are called *before* any lines that access `self.table_model` (like `setColumnHidden` or `setSectionResizeMode` that might use model properties).
    *   Revert the `setSectionResizeMode` for the "Description" column to use its known visible index after the "ID" column is hidden.

Here is the corrected and complete file:

---
**1. Update `app/ui/accounting/journal_entries_widget.py`**

```python
# app/ui/accounting/journal_entries_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QDateEdit, QComboBox, QInputDialog, QLineEdit,
    QFormLayout 
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QDate, QSize
from PySide6.QtGui import QIcon, QAction 
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json
from datetime import date as python_date 
from decimal import Decimal

from app.ui.accounting.journal_entry_dialog import JournalEntryDialog
from app.ui.accounting.journal_entry_table_model import JournalEntryTableModel
# from app.common.enums import JournalTypeEnum # Not directly used in this file's logic
from app.main import schedule_task_from_qt
# from app.utils.pydantic_models import JournalEntryData # Not directly used by widget
from app.models.accounting.journal_entry import JournalEntry 
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class JournalEntriesWidget(QWidget):
    def __init__(self, app_core: "ApplicationCore", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for JournalEntriesWidget.")
        except ImportError:
            self.app_core.logger.info("JournalEntriesWidget: Compiled Qt resources (resources_rc.py) not found. Using direct file paths.")
            pass

        self._init_ui()
        QTimer.singleShot(0, lambda: self.apply_filter_button.click())


    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        filter_group_layout = QHBoxLayout()
        filter_layout_form = QFormLayout()
        filter_layout_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.start_date_filter_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_filter_edit.setCalendarPopup(True); self.start_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        
        self.end_date_filter_edit = QDateEdit(QDate.currentDate())
        self.end_date_filter_edit.setCalendarPopup(True); self.end_date_filter_edit.setDisplayFormat("dd/MM/yyyy")

        self.entry_no_filter_edit = QLineEdit(); self.entry_no_filter_edit.setPlaceholderText("Filter by Entry No.")
        self.description_filter_edit = QLineEdit(); self.description_filter_edit.setPlaceholderText("Filter by Description")
        self.status_filter_combo = QComboBox(); self.status_filter_combo.addItems(["All", "Draft", "Posted"])
        
        filter_layout_form.addRow("From Date:", self.start_date_filter_edit)
        filter_layout_form.addRow("To Date:", self.end_date_filter_edit)
        filter_layout_form.addRow("Entry No.:", self.entry_no_filter_edit)
        filter_layout_form.addRow("Description:", self.description_filter_edit)
        filter_layout_form.addRow("Status:", self.status_filter_combo)
        filter_group_layout.addLayout(filter_layout_form)

        filter_button_layout = QVBoxLayout()
        self.apply_filter_button = QPushButton(
            QIcon.fromTheme("edit-find", QIcon(self.icon_path_prefix + "filter.svg")),
            "Apply Filter"
        )
        self.apply_filter_button.clicked.connect(lambda: schedule_task_from_qt(self._load_entries()))
        
        self.clear_filter_button = QPushButton(
            QIcon.fromTheme("edit-clear", QIcon(self.icon_path_prefix + "refresh.svg")),
            "Clear Filters"
        )
        self.clear_filter_button.clicked.connect(self._clear_filters_and_load)
        
        filter_button_layout.addWidget(self.apply_filter_button)
        filter_button_layout.addWidget(self.clear_filter_button)
        filter_button_layout.addStretch()
        filter_group_layout.addLayout(filter_button_layout)
        filter_group_layout.addStretch(1)
        self.main_layout.addLayout(filter_group_layout)

        self.entries_table = QTableView()
        self.entries_table.setAlternatingRowColors(True)
        self.entries_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.entries_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.entries_table.doubleClicked.connect(self.on_view_entry_double_click) 
        self.entries_table.setSortingEnabled(True)

        # Create and set the model FIRST
        self.table_model = JournalEntryTableModel()
        self.entries_table.setModel(self.table_model)

        # Now configure header and columns using self.table_model
        header = self.entries_table.horizontalHeader()
        header.setStretchLastSection(False) 
        
        # Set default resize mode for all columns first
        for i in range(self.table_model.columnCount()): # Use model's column count
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        # Hide ID column (model index 0, assuming headers are ["ID", "Entry No.", ...])
        id_column_model_index = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else 0
        self.entries_table.setColumnHidden(id_column_model_index, True)
        
        # Specifically set stretch for "Description" column
        # "Description" is model index 3. If "ID" (model index 0) is hidden,
        # visible indices are: Entry No (0), Date (1), Description (2), Type (3), Total (4), Status (5)
        # So, visible index for "Description" is 2.
        description_column_visible_index = 2 
        header.setSectionResizeMode(description_column_visible_index, QHeaderView.ResizeMode.Stretch)
        
        self._create_toolbar() 
        self.main_layout.addWidget(self.toolbar) 
        self.main_layout.addWidget(self.entries_table) 
        self.setLayout(self.main_layout)

    @Slot()
    def _clear_filters_and_load(self):
        self.start_date_filter_edit.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_filter_edit.setDate(QDate.currentDate())
        self.entry_no_filter_edit.clear()
        self.description_filter_edit.clear()
        self.status_filter_combo.setCurrentText("All")
        schedule_task_from_qt(self._load_entries())

    def _create_toolbar(self):
        self.toolbar = QToolBar("Journal Entries Toolbar")
        self.toolbar.setObjectName("JournalEntriesToolbar")
        self.toolbar.setIconSize(QSize(16, 16)) 

        self.new_entry_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "New Entry", self) 
        self.new_entry_action.triggered.connect(self.on_new_entry)
        self.toolbar.addAction(self.new_entry_action)

        self.edit_entry_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Draft", self)
        self.edit_entry_action.triggered.connect(self.on_edit_entry)
        self.toolbar.addAction(self.edit_entry_action)
        
        self.view_entry_action = QAction(QIcon(self.icon_path_prefix + "view.svg"), "View Entry", self) 
        self.view_entry_action.triggered.connect(self.on_view_entry_toolbar) 
        self.toolbar.addAction(self.view_entry_action)

        self.toolbar.addSeparator()

        self.post_entry_action = QAction(QIcon(self.icon_path_prefix + "post.svg"), "Post Selected", self) 
        self.post_entry_action.triggered.connect(self.on_post_entry)
        self.toolbar.addAction(self.post_entry_action)
        
        self.reverse_entry_action = QAction(QIcon(self.icon_path_prefix + "reverse.svg"), "Reverse Selected", self) 
        self.reverse_entry_action.triggered.connect(self.on_reverse_entry)
        self.toolbar.addAction(self.reverse_entry_action)

        self.toolbar.addSeparator()
        self.refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_entries()))
        self.toolbar.addAction(self.refresh_action)

        if self.entries_table.selectionModel():
            self.entries_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states() 

    @Slot()
    def _update_action_states(self):
        selected_indexes = self.entries_table.selectionModel().selectedRows()
        has_selection = bool(selected_indexes)
        is_draft = False; is_posted = False; single_selection = len(selected_indexes) == 1

        if single_selection:
            first_selected_row = selected_indexes[0].row()
            status = self.table_model.get_journal_entry_status_at_row(first_selected_row)
            if status is not None: 
                is_draft = status == "Draft" 
                is_posted = status == "Posted"
        
        can_post_any_draft = False
        if has_selection: 
            for index in selected_indexes:
                if self.table_model.get_journal_entry_status_at_row(index.row()) == "Draft":
                    can_post_any_draft = True; break
        
        self.edit_entry_action.setEnabled(single_selection and is_draft)
        self.view_entry_action.setEnabled(single_selection)
        self.post_entry_action.setEnabled(can_post_any_draft) 
        self.reverse_entry_action.setEnabled(single_selection and is_posted)

    async def _load_entries(self):
        if not self.app_core.journal_entry_manager:
            error_msg = "Journal Entry Manager not available."
            self.app_core.logger.critical(error_msg)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Critical Error"), Q_ARG(str, error_msg))
            return
        try:
            start_date = self.start_date_filter_edit.date().toPython()
            end_date = self.end_date_filter_edit.date().toPython()
            status_text = self.status_filter_combo.currentText()
            status_filter = status_text if status_text != "All" else None
            entry_no_filter_text = self.entry_no_filter_edit.text().strip()
            description_filter_text = self.description_filter_edit.text().strip()

            filters = {"start_date": start_date, "end_date": end_date, "status": status_filter,
                       "entry_no": entry_no_filter_text or None, 
                       "description": description_filter_text or None}
            
            result: Result[List[Dict[str, Any]]] = await self.app_core.journal_entry_manager.get_journal_entries_for_listing(filters=filters)
            
            if result.is_success:
                entries_data_for_table = result.value if result.value is not None else []
                json_data = json.dumps(entries_data_for_table, default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                error_msg = f"Failed to load journal entries: {', '.join(result.errors)}"
                self.app_core.logger.error(error_msg)
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))
        except Exception as e:
            error_msg = f"Unexpected error loading journal entries: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            entries_data: List[Dict[str, Any]] = json.loads(json_data_str, object_hook=json_date_hook)
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
        dialog.exec() 

    def _get_selected_entry_id_and_status(self, require_single_selection: bool = True) -> tuple[Optional[int], Optional[str]]:
        selected_indexes = self.entries_table.selectionModel().selectedRows()
        if not selected_indexes:
            if require_single_selection: QMessageBox.information(self, "Selection", "Please select a journal entry.")
            return None, None
        if require_single_selection and len(selected_indexes) > 1:
            QMessageBox.information(self, "Selection", "Please select only a single journal entry for this action.")
            return None, None
        
        row = selected_indexes[0].row() 
        entry_id = self.table_model.get_journal_entry_id_at_row(row)
        entry_status = self.table_model.get_journal_entry_status_at_row(row)
        return entry_id, entry_status

    @Slot()
    def on_edit_entry(self):
        entry_id, entry_status = self._get_selected_entry_id_and_status()
        if entry_id is None: return
        if entry_status != "Draft": QMessageBox.warning(self, "Edit Error", "Only draft entries can be edited."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in to edit."); return
        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, journal_entry_id=entry_id, parent=self)
        dialog.journal_entry_saved.connect(lambda _id: schedule_task_from_qt(self._load_entries()))
        dialog.exec()

    @Slot(QModelIndex) 
    def on_view_entry_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        entry_id = self.table_model.get_journal_entry_id_at_row(index.row())
        if entry_id is None: return
        self._show_view_entry_dialog(entry_id)

    @Slot()
    def on_view_entry_toolbar(self): 
        entry_id, _ = self._get_selected_entry_id_and_status()
        if entry_id is None: return
        self._show_view_entry_dialog(entry_id)

    def _show_view_entry_dialog(self, entry_id: int):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, journal_entry_id=entry_id, view_only=True, parent=self)
        dialog.exec()

    @Slot()
    def on_post_entry(self):
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows: QMessageBox.information(self, "Selection", "Please select draft journal entries to post."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in to post entries."); return
        entries_to_post_ids = []
        for index in selected_rows:
            entry_id = self.table_model.get_journal_entry_id_at_row(index.row())
            entry_status = self.table_model.get_journal_entry_status_at_row(index.row())
            if entry_id and entry_status == "Draft": entries_to_post_ids.append(entry_id)
        if not entries_to_post_ids: QMessageBox.information(self, "Selection", "No draft entries selected for posting."); return
        schedule_task_from_qt(self._perform_post_entries(entries_to_post_ids, self.app_core.current_user.id))

    async def _perform_post_entries(self, entry_ids: List[int], user_id: int):
        if not self.app_core.journal_entry_manager: 
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Journal Entry Manager not available."))
            return
        success_count = 0; errors = []
        for entry_id_to_post in entry_ids:
            result: Result[JournalEntry] = await self.app_core.journal_entry_manager.post_journal_entry(entry_id_to_post, user_id)
            if result.is_success: success_count += 1
            else:
                je_no_str = f"ID {entry_id_to_post}" 
                try:
                    temp_je = await self.app_core.journal_entry_manager.get_journal_entry_for_dialog(entry_id_to_post)
                    if temp_je: je_no_str = temp_je.entry_no
                except Exception: pass
                errors.append(f"Entry {je_no_str}: {', '.join(result.errors)}")
        message = f"{success_count} of {len(entry_ids)} entries posted."
        if errors: message += "\n\nErrors:\n" + "\n".join(errors)
        msg_box_method = QMessageBox.information if not errors and success_count > 0 else QMessageBox.warning
        title = "Posting Complete" if not errors and success_count > 0 else ("Posting Failed" if success_count == 0 else "Posting Partially Failed")
        QMetaObject.invokeMethod(msg_box_method, "", Qt.ConnectionType.QueuedConnection, 
            Q_ARG(QWidget, self), Q_ARG(str, title), Q_ARG(str, message))
        if success_count > 0: schedule_task_from_qt(self._load_entries())


    @Slot()
    def on_reverse_entry(self):
        entry_id, entry_status = self._get_selected_entry_id_and_status()
        if entry_id is None or entry_status != "Posted": QMessageBox.warning(self, "Reverse Error", "Only single, posted entries can be reversed."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in to reverse entries."); return
        reply = QMessageBox.question(self, "Confirm Reversal", 
                                     f"Are you sure you want to reverse journal entry ID {entry_id}?\nA new counter-entry will be created as a DRAFT.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return
        reversal_date_str, ok_date = QInputDialog.getText(self, "Reversal Date", "Enter reversal date (YYYY-MM-DD):", QLineEdit.EchoMode.Normal, python_date.today().isoformat())
        if ok_date and reversal_date_str:
            try:
                parsed_reversal_date = python_date.fromisoformat(reversal_date_str)
                reversal_desc_str, ok_desc = QInputDialog.getText(self, "Reversal Description", "Enter description for reversal entry (optional):", QLineEdit.EchoMode.Normal, f"Reversal of JE {entry_id}")
                if ok_desc: 
                    schedule_task_from_qt(self._perform_reverse_entry(entry_id, parsed_reversal_date, reversal_desc_str, self.app_core.current_user.id))
                else: QMessageBox.information(self, "Cancelled", "Reversal description input cancelled.")
            except ValueError: QMessageBox.warning(self, "Invalid Date", "Reversal date format is invalid. Please use YYYY-MM-DD.")
        else: QMessageBox.information(self, "Cancelled", "Reversal date input cancelled.")

    async def _perform_reverse_entry(self, entry_id: int, reversal_date: python_date, description: str, user_id: int):
        if not self.app_core.journal_entry_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Journal Entry Manager not available."))
            return
        result: Result[JournalEntry] = await self.app_core.journal_entry_manager.reverse_journal_entry(entry_id, reversal_date, description, user_id)
        if result.is_success and result.value:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, f"Journal entry ID {entry_id} reversed. New reversal entry: {result.value.entry_no} (Draft)."))
            schedule_task_from_qt(self._load_entries())
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Reversal Error"), Q_ARG(str, f"Failed to reverse journal entry:\n{', '.join(result.errors)}"))

```
**Validation of Changes for `app/ui/accounting/journal_entries_widget.py`:**

1.  **Import `QFormLayout`**: Corrected the `NameError` by adding `QFormLayout` to imports.
2.  **Icon Path (`self.icon_path_prefix`)**: Initialized in `__init__` to correctly determine whether to use resource paths (`:/icons/`) or direct file paths (`resources/icons/`) based on the successful import of `app.resources_rc`. This prefix is then used for all `QIcon` instantiations, including those in `QIcon.fromTheme` fallbacks.
3.  **Table Column Resizing**:
    *   `self.table_model = JournalEntryTableModel()` is now created and set *before* any header configurations that might depend on it (like `setColumnHidden` or `setSectionResizeMode` if they were to use `self.table_model._headers`).
    *   The `setSectionResizeMode` for the "Description" column is now set using a hardcoded visible index `2`, which is correct given that model column "ID" (index 0) is hidden, and the visible columns are "Entry No." (vis idx 0), "Date" (vis idx 1), "Description" (vis idx 2).
    *   A loop is added to set `ResizeToContents` for all columns initially, then "Description" is set to `Stretch`.
4.  **Logging**: Added `self.app_core.logger` calls for more detailed error reporting from async methods.
5.  **Minor Refinements**:
    *   `_get_selected_entry_id_and_status` now uses `selectedRows()` for consistency.
    *   `_update_action_states` includes a `status is not None` check for robustness.
    *   Initial load triggered by `apply_filter_button.click()` to respect default filter values.
    *   Filter layout adjusted slightly for better visual grouping.

These changes should resolve the `AttributeError` and the icon loading issues. The application should now launch correctly, display icons properly (if `app.resources_rc.py` is compiled and SVG files exist, or via direct paths if SVG files exist), and the Journal Entries tab should be ready for functional testing.
