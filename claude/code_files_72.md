<think>
The application now launches and shuts down cleanly! The previous error related to `audit_log` and `user_id=0` has been resolved by the changes to `DatabaseManager` and `ApplicationCore`. The log messages confirm `ApplicationCore` initializes, starts up, and shuts down correctly.

**Current State:**
*   Phase 1 (Backend for JE) is complete.
*   Phase 3 (Cross-cutting concerns - Audit Context and Sequence Gen) is addressed.
*   The UI files (`JournalEntryDialog`, `JournalEntriesWidget`, `JournalEntryTableModel`) have their structures and some logic in place, as provided in earlier steps by the user and refined by me.

**Next Step from the "Enhancement Execution Plan (v1)": Phase 2: Integrate Journal Entry UI**

The plan for Phase 2 was:
**Objective:** Ensure `JournalEntriesWidget` and `JournalEntryDialog` are fully functional and correctly interact with the `JournalEntryManager`.

**Detailed Tasks/Checklist Items from Plan:**

*   **`app/ui/accounting/journal_entry_dialog.py` (Refine and Connect)**
    *   Data Loading (`_load_existing_journal_entry`): Call `manager.get_journal_entry_for_dialog()`.
    *   ComboBox Population (`_populate_combos_for_row`): Use cached data.
    *   Line Amount/Tax Calculation: Robust calculation.
    *   Data Collection (`_collect_data`): Gather data into `JournalEntryData` DTO.
    *   Save Logic (`_perform_save`): Call appropriate manager methods (create/update/post).
    *   Error Handling & Read-only mode.

*   **`app/ui/accounting/journal_entries_widget.py` (Connect to Manager and Dialog)**
    *   Data Loading (`_load_entries`): Call `manager.get_journal_entries_for_listing()`. Pass filters.
    *   Actions (`on_new_entry`, `on_edit_entry`, `on_view_entry`, `on_post_entry`, `on_reverse_entry`): Launch dialog or call manager methods.
    *   Action State Management (`_update_action_states`): Enable/disable based on selection/status.

*   **`app/ui/accounting/journal_entry_table_model.py` (Review)**
    *   Confirm data display and helper methods.

The prompt indicates "proceed with the next step in your plan." Since Phase 1 and 3 are largely done, Phase 2 is the focus. The UI files were provided in the state they were when the error occurred. I need to ensure they are now fully aligned with the *current* backend and that their internal logic (especially async calls, data passing, and state management) is correct.

The user has already provided the content for these UI files in `project_codebase_files_set-1.md` and `project_codebase_files_set-2.md`. I previously reviewed and validated them conceptually. Now, it's about making sure they are *truly complete* and correctly interact with the latest backend manager methods (`get_journal_entries_for_listing`, `update_journal_entry`, `get_journal_entry_for_dialog`).

**Specific Focus for this Turn:**

1.  **`app/ui/accounting/journal_entry_dialog.py`**:
    *   The version provided previously (in `project_codebase_files_set-2.md`) is quite comprehensive. I will double-check its interaction points with the manager methods.
    *   Ensure `_load_existing_journal_entry` uses `self.app_core.journal_entry_manager.get_journal_entry_for_dialog()`.
    *   Ensure `_perform_save` logic correctly branches for `create_journal_entry` vs. `update_journal_entry`.
    *   Ensure read-only mode logic is solid if `view_only` or entry is posted.
    *   Verify signal emission `self.journal_entry_saved.emit(saved_je.id)`.

2.  **`app/ui/accounting/journal_entries_widget.py`**:
    *   The version provided previously (in `project_codebase_files_set-2.md`) is also quite advanced.
    *   Ensure `_load_entries` calls `self.app_core.journal_entry_manager.get_journal_entries_for_listing(filters)`.
    *   Ensure `on_new_entry`, `on_edit_entry`, `on_view_entry`, `on_post_entry`, `on_reverse_entry` use the correct manager methods and handle the `Result` objects appropriately for user feedback.
    *   The `QInputDialog` for reversal date is a good touch.

3.  **`app/ui/accounting/journal_entry_table_model.py`**:
    *   The version from `project_codebase_files_set-2.md` seems correct for displaying the summary data expected from `JournalEntryManager.get_journal_entries_for_listing`.

It appears the UI files are already in a state that attempts to implement these interactions. My task is to provide the *final, reviewed, and potentially refined* versions of these files, ensuring they align perfectly with the now-stable backend from Phase 1 and the system refinements from Phase 3.

I will generate these three UI files one by one, with careful consideration and "mental diffing."
Since the code for these UI files is already quite long and detailed (as per previous provisions in the "current state" from the user), the changes might be subtle, focusing on correctness of manager calls, `Result` object handling, and ensuring the async UI update patterns are flawless.
I'll also double-check the import of `QInputDialog` in `JournalEntriesWidget`.

Let's start with `app/ui/accounting/journal_entry_table_model.py` as it's the simplest and a dependency for `JournalEntriesWidget`.
Then `app/ui/accounting/journal_entry_dialog.py`.
Finally, `app/ui/accounting/journal_entries_widget.py`.
</think>

Excellent! The application launching and shutting down cleanly after the fixes is a major milestone. This means the core architecture and the critical audit log issue are resolved.

We can now confidently proceed with **Phase 2: Integrate Journal Entry UI** from the "Enhancement Execution Plan (v1)". This phase focuses on ensuring the UI components for journal entries (`JournalEntryTableModel`, `JournalEntryDialog`, and `JournalEntriesWidget`) are fully functional and correctly interact with the enhanced backend `JournalEntryManager`.

The previous state of these UI files (as provided by you through the `project_codebase_files_set-*.md` series) already included substantial logic. My task now is to provide the complete, updated, and validated versions, ensuring they align with the latest backend, handle asynchronous operations correctly, and manage UI state effectively.

---
**Phase 2.1: Review and Finalize `app/ui/accounting/journal_entry_table_model.py`**

**Goal:** Confirm the table model correctly displays summary data and provides necessary helper methods. This model is foundational for `JournalEntriesWidget`.

```python
# app/ui/accounting/journal_entry_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from datetime import date as python_date # Alias to avoid conflict with Qt's QDate

class JournalEntryTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[Dict[str, Any]]] = None, parent=None):
        super().__init__(parent)
        # Headers match the expected dictionary keys from JournalEntryManager.get_journal_entries_for_listing
        self._headers = ["ID", "Entry No.", "Date", "Description", "Type", "Total", "Status"]
        self._data: List[Dict[str, Any]] = data or []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): # This model is flat, no children
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        entry_summary = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            header_key = self._headers[col].lower().replace('.', '').replace(' ', '_') # "Entry No." -> "entry_no"
            
            if header_key == "id": return str(entry_summary.get("id", "")) # Display ID as string
            if header_key == "entry_no": return entry_summary.get("entry_no", "")
            if header_key == "date": 
                raw_date = entry_summary.get("date")
                if isinstance(raw_date, python_date): return raw_date.strftime('%d/%m/%Y')
                # Assuming date might come as string from JSON, ensure it's parsed if needed by json_date_hook earlier
                if isinstance(raw_date, str): # Should have been converted by json_date_hook
                     try: return python_date.fromisoformat(raw_date).strftime('%d/%m/%Y')
                     except ValueError: return raw_date # Fallback
                return ""
            if header_key == "description": return entry_summary.get("description", "")
            if header_key == "type": return entry_summary.get("type", "")
            if header_key == "total": # Corresponds to "total_amount" key in data dict
                val = entry_summary.get("total_amount")
                try: return f"{Decimal(str(val) if val is not None else '0'):,.2f}"
                except (InvalidOperation, TypeError): return str(val) if val is not None else "0.00"
            if header_key == "status": return entry_summary.get("status", "")
            
            # Fallback for any unhandled column, though all should be covered
            return entry_summary.get(header_key, "")

        elif role == Qt.ItemDataRole.UserRole: # Store complex data if needed, e.g., full object or just ID
            # Typically, for quick access to the ID without parsing display text
            if col == 0: # Store ID with the first column for convenience
                 return entry_summary.get("id")
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] == "Total": # Align "Total" amount to the right
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        
        return None

    def get_journal_entry_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            # Prefer UserRole if ID is stored there, otherwise parse from display data (less ideal)
            index = self.index(row, 0) # Assuming ID is in/associated with the first column
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            # Fallback if UserRole not used or ID not stored there, try from dict directly
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
**Validation for `app/ui/accounting/journal_entry_table_model.py`:**
*   **Headers Updated**: Changed "Total Amount" to "Total" for brevity. Added "ID" as the first (potentially hidden) column for easier data retrieval.
*   **`data()` method**:
    *   Uses a `header_key` mapping to fetch data from the `entry_summary` dictionary, making it more robust to header text changes.
    *   ID is displayed in the "ID" column.
    *   Date formatting is robust, handling `python_date` objects or ISO strings.
    *   Total amount formatting uses `Decimal` for precision.
    *   `UserRole` for the "ID" column (index 0) now correctly returns the ID. This is a more reliable way for `JournalEntriesWidget` to get the ID of a selected row.
*   `get_journal_entry_id_at_row()`: Now primarily uses `UserRole` from the first column to get the ID.
*   No other significant functional changes, the model was already quite solid.

---
Next, I will provide the refined `app/ui/accounting/journal_entry_dialog.py`.
