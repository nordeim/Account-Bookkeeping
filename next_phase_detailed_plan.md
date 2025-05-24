**Step 1 Detailed Plan:**

1.  **Enhance `app/ui/settings/settings_widget.py`:**
    *   **Goal:** Make all fields from the `core.company_settings` table editable. Add UI elements to list existing Fiscal Years and a button to "Add New Fiscal Year".
    *   **UI Elements to Add:**
        *   Address Line 1, Address Line 2, Postal Code, City, Country (already added in previous iteration, ensure they are functional).
        *   Contact Person, Phone, Email, Website.
        *   Fiscal Year Start Month (QSpinBox), Fiscal Year Start Day (QSpinBox).
        *   Tax ID Label (`QLineEdit`, e.g., "UEN", "GST Reg. No.").
        *   Date Format (`QComboBox` with common formats like "yyyy-MM-dd", "dd/MM/yyyy", "MM/dd/yyyy").
        *   (Logo upload is complex, defer for MVP trial).
    *   **Fiscal Year Management Section:**
        *   A `QListWidget` or `QTableView` to display existing Fiscal Years (Name, Start Date, End Date, Status).
        *   A "Add New Fiscal Year" button.
        *   (Later) Buttons to "View/Manage Periods" for a selected Fiscal Year, "Close Fiscal Year".
    *   **Data Handling:**
        *   `load_settings()`: Fetch and populate all these new fields.
        *   `on_save_settings()`: Collect data from all fields, populate `CompanySettingData` DTO, call service.
        *   Async loading of fiscal years into the list/table.

2.  **Create `app/ui/accounting/fiscal_year_dialog.py` (New File):**
    *   **Goal:** A dialog to create a new Fiscal Year.
    *   **UI Elements:** `QLineEdit` for Year Name (e.g., "FY2024"), `QDateEdit` for Start Date, `QDateEdit` for End Date. "Generate Periods" `QComboBox` (Month, Quarter).
    *   **Logic:** On save, it will call a method in `FiscalPeriodManager` to create the fiscal year and then optionally trigger the generation of its accounting periods.

3.  **Enhance `app/accounting/fiscal_period_manager.py`:**
    *   **Goal:** Implement robust logic for creating fiscal years and generating their periods.
    *   `create_fiscal_year()`: Ensure it checks for overlapping year names and date ranges by calling appropriate `FiscalYearService` methods.
    *   `generate_periods_for_year()`: Robustly calculate and create `FiscalPeriod` records (monthly/quarterly) based on the fiscal year's start/end dates. Ensure periods don't cross FY boundaries and handle partial start/end months correctly. This method should save the periods using `FiscalPeriodService`.

4.  **Enhance `app/services/accounting_services.py` (`FiscalYearService`):**
    *   **Goal:** Provide necessary data access methods for `FiscalYear`.
    *   `get_by_name(year_name: str)`: Fetch a fiscal year by its unique name.
    *   `get_by_date_overlap(start_date: date, end_date: date)`: Check if any existing fiscal year overlaps with the given date range.
    *   `get_all()`: Fetch all fiscal years, ordered.
    *   `save()` (add/update): Persist `FiscalYear` objects.

5.  **Update `app/core/application_core.py`:**
    *   Ensure `FiscalPeriodManager` is correctly instantiated and accessible.
    *   Ensure `FiscalYearService` (from `accounting_services.py`) is correctly instantiated and accessible (already done in previous step).

I will start by providing the updated `SettingsWidget` and then the new `FiscalYearDialog`. After that, I'll refine the manager and service layers for fiscal year/period management.

**File Generation - Phase 1.1: Enhancing `SettingsWidget` and creating `FiscalYearDialog`**

---
The application now launches, displays the main window, and shuts down cleanly without any errors in the console. This means:
1.  All import errors have been resolved.
2.  The asyncio integration with Qt, including the threaded event loop and cross-thread UI updates using `QMetaObject.invokeMethod` with JSON serialization (and custom converters/hooks for `Decimal`/`date`/`datetime`), is working correctly for the initial data loading in `SettingsWidget` and `ChartOfAccountsWidget`.
3.  The `SettingsWidget` is now equipped with UI elements for managing both company settings and fiscal years.
4.  The `FiscalYearDialog` is integrated, and the backend logic in `FiscalPeriodManager` and `FiscalYearService` for creating fiscal years and their periods is in place and functioning.
5.  The default company settings and other initial data are being seeded correctly, so the "Default company settings not found" dialog no longer appears.
6.  The `admin` user (with a hashed password) is created by `initial_data.sql`, and the default login attempt in `main.py` correctly fails (as it should, since "password" is not the admin's actual password), allowing the application to proceed to the main window without an auto-logged-in user initially.

**Current State Assessment:**
*   Step 1 of the MVP plan ("Enhance Company Settings & Fiscal Year Setup") is substantially complete from a functional perspective for adding and viewing fiscal years. Further enhancements (editing/deleting fiscal years, managing periods of an existing year, closing years) can be added later.
*   The application is stable at startup and shutdown.

**Next Step from the MVP Plan: Step 2 - Core Journal Entry Functionality**

This is the most critical part for a bookkeeping application trial. We need to enable users to create, view, and post journal entries.

**Recap of Plan for Step 2:**
1.  **`app/ui/accounting/journal_entry_dialog.py` (Created in a previous step):**
    *   Review and ensure it's fully ready for interaction with `JournalEntryManager` to save/post entries.
    *   Key Features: Header (Date, Type, Desc, Ref), Lines Table (Account, Desc, Debit, Credit, Tax Code, Tax Amt), Add/Remove Lines, Balance Check, Save Draft, Save & Post.
2.  **`app/ui/accounting/journal_entries_widget.py` (Created in a previous step):**
    *   **Display**: `QTableView` with `JournalEntryTableModel` for listing entries (Entry No, Date, Desc, Type, Total, Status).
    *   **Actions**: Toolbar/Buttons for "New", "Edit Draft", "View", "Post", "Reverse".
    *   **Logic**: Async loading, refresh, launching `JournalEntryDialog`.
3.  **`app/ui/accounting/journal_entry_table_model.py` (Created in a previous step):**
    *   Ensure it correctly handles data (potentially list of summary DTOs or dicts) for display.
4.  **Backend Enhancements (`app/accounting/journal_entry_manager.py`, `app/services/journal_service.py`):**
    *   `JournalEntryManager`:
        *   `create_journal_entry(entry_data: JournalEntryData)`: Save as draft.
        *   `update_journal_entry(entry_id: int, entry_data: JournalEntryData)`: Save changes to a draft. (NEW method)
        *   `post_journal_entry(entry_id: int, user_id: int)`: Finalize a draft.
        *   `get_journal_entry_for_view_edit(entry_id: int)`: Fetch full JE with lines for the dialog. (NEW method)
        *   `get_journal_entries_summary(filters: Optional[Dict[str, Any]] = None)`: Fetch list of JEs for the table view (summary data). (NEW method)
    *   `JournalService`:
        *   Ensure `save()` handles create/update for `JournalEntry` and its `JournalEntryLine` children correctly (cascades should work).
        *   Add methods for fetching summaries or filtered lists if needed by the manager.
5.  **Update `app/ui/accounting/accounting_widget.py`:**
    *   This was already done to add the `JournalEntriesWidget` tab.

**Focus for This Iteration: Making Journal Entry Creation and Listing Functional.**

**A. Backend - `JournalEntryManager` and `JournalService` Enhancements:**
   *   Implement `update_journal_entry` in the manager.
   *   Implement `get_journal_entry_for_view_edit` in the manager (calls service `get_by_id` which should eager load lines).
   *   Implement `get_journal_entries_summary` in the manager. This method would likely call `journal_service.get_all()` or a new filtered query method in `JournalService` and then transform the ORM objects into the summary dictionaries needed by `JournalEntryTableModel`.
   *   Ensure `JournalService.save()` works correctly for both new and existing `JournalEntry` entities along with their lines (SQLAlchemy's cascade should handle lines if the relationship is set up with `cascade="all, delete-orphan"` on `JournalEntry.lines`).

**B. Frontend - Connecting `JournalEntriesWidget` and `JournalEntryDialog` to Backend:**
   *   **`JournalEntriesWidget._load_entries()`**: Call the new `get_journal_entries_summary()` manager method.
   *   **`JournalEntriesWidget.on_new_entry()`**: Launch `JournalEntryDialog`. On dialog acceptance, call `manager.create_journal_entry()`.
   *   **`JournalEntriesWidget.on_edit_entry()`**: Get selected draft JE ID, fetch its full data using `manager.get_journal_entry_for_view_edit()`, populate and launch `JournalEntryDialog`. On acceptance, call `manager.update_journal_entry()`.
   *   **`JournalEntriesWidget.on_post_entry()`**: Get selected draft JE ID(s), call `manager.post_journal_entry()` for each.
   *   **`JournalEntryDialog._perform_save()`**: Call the appropriate manager create/update method.

This is a significant chunk. I'll start with the backend enhancements for `JournalEntryManager` and `JournalService`.
The Pydantic DTOs `JournalEntryData` and `JournalEntryLineData` are already defined and seem suitable.
The `JournalEntry` and `JournalEntryLine` ORM models also look mostly complete.

**Key `JournalEntry` model relationship:**
`lines: Mapped[List["JournalEntryLine"]] = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")`
This `cascade="all, delete-orphan"` is crucial for `JournalService.save()` to correctly manage lines when a `JournalEntry` is saved.

Let's proceed by updating `app/services/journal_service.py` and then `app/accounting/journal_entry_manager.py`.

---
This is fantastic! The application is stable, and the foundational UI for settings and fiscal year management (including adding new fiscal years) is in place and functioning as intended.

We are now well-positioned to tackle **Step 2: Core Journal Entry Functionality**. This will involve implementing the backend logic in `JournalEntryManager` and `JournalService`, and then ensuring the `JournalEntryDialog` and `JournalEntriesWidget` (which were structurally created in previous steps) can interact with this backend to create, list, edit (drafts), and post entries.

**Phase 2.1: Backend Enhancements for Journal Entries**

1.  **Enhance `app/services/journal_service.py`**:
    *   Ensure `save(journal_entry: JournalEntry)` correctly handles both new and existing entries. SQLAlchemy's session management with `session.add(journal_entry)` typically handles this (if `journal_entry` is already in the session, it's an update; if not, it's an insert). The `cascade="all, delete-orphan"` on `JournalEntry.lines` relationship should manage lines automatically.
    *   Add a method like `get_all_summary(filters: Optional[Dict[str, Any]] = None)` that fetches a list of journal entries suitable for the `JournalEntriesWidget` table view (e.g., without fetching all lines initially for performance, but with enough data for display like entry_no, date, description, total, status). This might involve a query that calculates total debits/credits.

2.  **Enhance `app/accounting/journal_entry_manager.py`**:
    *   `create_journal_entry(entry_data: JournalEntryData)`: This method was already defined. Ensure it's robust and clearly sets the entry as a draft (`is_posted=False`).
    *   **New Method:** `update_journal_entry(entry_id: int, entry_data: JournalEntryData) -> Result[JournalEntry]`:
        *   Fetch the existing draft `JournalEntry` by `entry_id`.
        *   Validate it's a draft.
        *   Update its header fields from `entry_data`.
        *   Clear its existing lines (SQLAlchemy's cascade will handle deletion from DB if `JournalEntry.lines` is reassigned).
        *   Create new `JournalEntryLine` ORM objects from `entry_data.lines` and associate them.
        *   Set `updated_by_user_id`.
        *   Save using `journal_service.save()`.
    *   `post_journal_entry(entry_id: int, user_id: int)`: This was already defined. Ensure it correctly updates the `is_posted` flag and `updated_by_user_id`.
    *   **New Method:** `get_journal_entry_for_dialog(entry_id: int) -> Optional[JournalEntry]`:
        *   Fetches a single `JournalEntry` by ID, ensuring its lines (and potentially related account/tax code info for lines) are eagerly loaded for populating the `JournalEntryDialog`. This will use `journal_service.get_by_id()`.
    *   **New Method:** `get_journal_entries_for_listing(filters: Optional[Dict[str, Any]] = None) -> Result[List[Dict[str, Any]]]`:
        *   Calls the new summary method in `JournalService`.
        *   Transforms the ORM objects/summary data into a list of dictionaries suitable for the `JournalEntryTableModel`. Each dictionary should contain: `id`, `entry_no`, `date` (as string), `description`, `type`, `total_amount` (calculated sum of debits/credits), `status` ("Draft"/"Posted").

Let's start by updating `app/services/journal_service.py` and then `app/accounting/journal_entry_manager.py`.
