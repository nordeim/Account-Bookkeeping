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

