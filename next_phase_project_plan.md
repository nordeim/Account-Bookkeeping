Thank you for the kind words! It's been a rewarding process to get the application to this stage. I'm ready to help you think through the next steps to build out the core functionalities for a successful trial.

Given that the UI shell is launching and the database backend is solid, we need to prioritize implementing the features that provide the most immediate value for a bookkeeping application trial, especially for Singaporean small businesses.

**Core Functionalities for a Minimum Viable Product (MVP) Trial:**

1.  **Company Setup & Basic Configuration:**
    *   Ability to input/edit essential company details (already partially in `SettingsWidget`).
    *   Set up Fiscal Years and Accounting Periods.

2.  **Chart of Accounts (CoA) Management:**
    *   Full CRUD (Create, Read, Update, Deactivate/Activate) for accounts. (The UI for listing and dialog for add/edit is started).
    *   Support for hierarchical accounts.
    *   Pre-defined CoA templates relevant to Singapore (e.g., for sole proprietorship, Pte Ltd).

3.  **Journal Entry Management:**
    *   Manual General Journal Entry creation with debits/credits.
    *   Validation for balanced entries.
    *   Posting mechanism for journal entries.
    *   Viewing journal entries (Journal Browser/Ledger).

4.  **Basic Sales & Purchases (Simplified):**
    *   **Sales:** Create a simple sales entry (perhaps directly as a sales journal, or a very simplified invoice that generates a JE) to record revenue and GST.
    *   **Purchases/Expenses:** Create a simple expense/purchase entry (again, perhaps a direct journal or simplified bill) to record expenses and claimable GST.
    *   This avoids full-blown invoicing/billing systems for the MVP trial but captures the essential financial impact.

5.  **GST Tracking & Basic Reporting:**
    *   Automatic calculation of GST on relevant sales/purchase entries based on tax codes.
    *   A simple report showing Output GST and Input GST collected/paid for a period (precursor to GST F5).

6.  **Essential Financial Reports:**
    *   Trial Balance.
    *   Profit & Loss Statement (Income Statement).
    *   Balance Sheet.

7.  **User Management (Basic):**
    *   The `admin` user exists. For a trial, this might be sufficient, or a way to add one or two more users with predefined roles.

**Deep Dive and Implementation Strategy - Prioritized Areas:**

Let's break down how we can approach these, focusing on creating/completing the necessary backend (managers, services) and frontend (widgets, dialogs) files.

---

**I. Chart of Accounts (CoA) - Enhancements**

*   **Backend (`app/accounting/chart_of_accounts_manager.py`, `app/services/account_service.py`):**
    *   **Current State:** CRUD seems mostly there. Deactivation logic needs balance checks. `get_account_tree` is present.
    *   **To Do/Verify:**
        *   Ensure `deactivate_account` in the manager thoroughly checks for zero balance (including opening balance and all posted transactions) before allowing deactivation. This requires `JournalService.get_account_balance`.
        *   Consider a method to prevent deletion/deactivation of control accounts linked from other modules (e.g., default AR/AP, bank GL accounts) if they are in use or have balances.
        *   Ability to import CoA from a CSV template (this is a "nice to have" for trial, but very useful).
            *   New method in `ChartOfAccountsManager`: `import_coa_from_csv(file_path: str, user_id: int) -> Result`.
            *   This would parse the CSV, create `AccountCreateData` DTOs, and call `create_account` for each.

*   **Frontend (`app/ui/accounting/chart_of_accounts_widget.py`, `app/ui/accounting/account_dialog.py`):**
    *   **Current State:** Listing tree view exists. Add/Edit dialog `AccountDialog` is mostly functional for basic fields.
    *   **To Do/Verify:**
        *   **`AccountDialog`:** Ensure all relevant fields from `AccountCreateData` / `AccountUpdateData` (and thus `core.accounts` table) are present and editable (e.g., `sub_type`, `tax_treatment`, `gst_applicable`, `report_group`, `is_control_account`, `is_bank_account`, `opening_balance`, `opening_balance_date`). The `opening_balance_date` should only be enabled if `opening_balance` is non-zero.
        *   **Parent Account Selection:** The `parent_id_spin` in `AccountDialog` is not user-friendly. Replace with a `QComboBox` populated with existing accounts (perhaps filtered by type to prevent illogical parenting), or a small tree view selector. For MVP, allowing manual ID input (with validation that parent exists) might be a temporary shortcut.
        *   **Error Display:** Ensure validation errors from the manager are clearly displayed in the dialog.
        *   **CoA Widget Toolbar:** Add "Import CoA" action if implementing CSV import.

---

**II. Journal Entry Management - Core Implementation**

This is critical. Users need to be able to make manual journal entries.

*   **Backend (`app/accounting/journal_entry_manager.py`, `app/services/journal_service.py`):**
    *   **Current State:** `create_journal_entry`, `post_journal_entry`, `reverse_journal_entry` stubs/implementations exist. `RecurringPattern` logic is also there.
    *   **To Do/Verify:**
        *   **Validation in `create_journal_entry`**:
            *   Ensure `JournalEntryData` Pydantic model correctly validates balanced entries.
            *   Manager should verify that `account_id` in lines exist and are active.
            *   Verify `currency_code`, `tax_code`, `dimension_id`s exist if provided.
        *   **Posting Logic (`post_journal_entry`)**: Ensure it robustly sets `is_posted = True` and updates audit fields.
        *   **Impact of Posting**: Consider how posting affects other parts (e.g., account balances should only reflect posted entries). Views like `account_balances` already filter by `is_posted = TRUE`.
        *   **Sequence Generation**: The `SequenceGenerator` currently simulates DB sequence for `journal_entry`. The DB function `core.get_next_sequence_value('journal_entry')` is more robust. Consider if `JournalEntryManager` should call this DB function directly via `db_manager.execute_scalar` or if the Python `SequenceGenerator` is sufficient for the trial. For simplicity and robustness, direct DB function call is often better for critical sequences.
            *   If using DB func: `entry_no_str = await self.db_manager.execute_scalar("SELECT core.get_next_sequence_value('journal_entry')")` (inject `db_manager` or access via `app_core`).

*   **Frontend (`app/ui/accounting/journal_entries_widget.py` - New File, `app/ui/accounting/journal_entry_dialog.py` - New File):**
    *   **`JournalEntriesWidget(QWidget)`**:
        *   This will be a new tab under "Accounting".
        *   **Display**: A `QTableView` or `QTreeView` to list existing journal entries (entry no, date, description, total debit/credit, status: Draft/Posted).
        *   **Actions**: Buttons/Toolbar for "New Journal Entry", "Edit Draft", "View/Print", "Post Entry", "Reverse Entry".
        *   **Filtering**: By date range, status.
        *   **Data Loading**: Async loading of journal entries using `schedule_task_from_qt` and `QMetaObject.invokeMethod` for UI updates.
    *   **`JournalEntryDialog(QDialog)`**:
        *   **Header Fields**: Entry Date (`QDateEdit`), Journal Type (`QComboBox` from `JournalTypeEnum`), Description (`QLineEdit`), Reference (`QLineEdit`).
        *   **Lines Table**: A `QTableWidget` or a custom model/view for `JournalEntryLineData`.
            *   Columns: Line #, Account (ComboBox populated from CoA, searchable), Description, Debit, Credit, Currency, Ex.Rate, Tax Code (ComboBox), Tax Amt, Dimensions (ComboBoxes).
            *   Dynamic rows: Add/Remove Line buttons.
            *   Automatic calculation of Tax Amount based on Tax Code and Debit/Credit.
            *   Display running totals for Debits and Credits to show if balanced.
        *   **Save/Post Actions**: "Save Draft", "Save and Post".
        *   **Validation**: Client-side basic validation (e.g., date, required fields) and display server-side validation errors from `JournalEntryManager`.

---

**III. Simplified Sales & Purchases (via General Journal)**

For an MVP trial, instead of full Sales/Purchase Invoice modules, we can guide users to record these using specific General Journal entries.

*   **Documentation/Guidance**: Provide examples of how to record:
    *   **Simple Cash Sale**: Debit Cash/Bank, Credit Sales Revenue, Credit GST Output Tax.
    *   **Simple Credit Sale**: Debit Accounts Receivable, Credit Sales Revenue, Credit GST Output Tax.
    *   **Simple Cash Purchase/Expense**: Debit Expense/Asset, Debit GST Input Tax, Credit Cash/Bank.
    *   **Simple Credit Purchase/Expense**: Debit Expense/Asset, Debit GST Input Tax, Credit Accounts Payable.
*   **Enhance `JournalEntryDialog` (Potentially):**
    *   Could add "presets" or templates for common entries like "Sales" or "Expense" that pre-fill some accounts or descriptions, making it easier than a blank GJ form. This is optional for MVP.

---

**IV. GST Tracking & Basic Reporting**

*   **Backend:**
    *   **`TaxCodeService`**: Ensure it can fetch tax codes and their rates.
    *   **`JournalEntryLine` model**: Already has `tax_code` and `tax_amount`.
    *   **`GSTManager.prepare_gst_return_data`**: The stub needs to be replaced with actual logic to sum up `tax_amount` and base amounts from `JournalEntryLine` records based on `tax_code` (SR, ZR, ES, TX, etc.) and account types (Revenue, Expense/Asset). This method should query posted `JournalEntryLine`s.
        *   This method is already designed to produce a `GSTReturnData` DTO, which is good.

*   **Frontend (`app/ui/reports/gst_report_widget.py` - New File, or integrated into `ReportsWidget`):**
    *   **GST Report Widget**:
        *   Allow user to select a period (e.g., a quarter from `FiscalPeriod`s).
        *   Button "Prepare GST Data".
        *   Calls `app_core.gst_manager.prepare_gst_return_data()`.
        *   Displays the fields of the returned `GSTReturnData` DTO in a read-only form (Boxes 1-9 of GST F5).
        *   (Future) Button to "Save Draft GST Return" which would call `gst_manager.save_gst_return()`.

---

**V. Essential Financial Reports**

*   **Backend (`app/reporting/financial_statement_generator.py`):**
    *   **Current State**: Methods like `generate_balance_sheet`, `generate_profit_loss`, `generate_trial_balance` exist.
    *   **To Do/Verify:**
        *   **Trial Balance**: Ensure it correctly sums debits and credits from `account_balances` view (which uses `journal_service.get_account_balance`).
        *   **Profit & Loss**: Ensure it correctly sums Revenue and Expense account activities for the period using `journal_service.get_account_balance_for_period`.
        *   **Balance Sheet**: Ensure it uses `journal_service.get_account_balance` as of a specific date for Asset, Liability, Equity accounts. The "Retained Earnings" for the current period is implicitly part of the P&L calculation and should flow into Equity on the Balance Sheet. This often requires careful calculation of prior year retained earnings + current year net profit.
            *   A common approach for BS Equity: Share Capital + Retained Earnings (Opening) + Net Profit for Current Period - Dividends.
            *   For simplicity in MVP, `total_equity` might just be sum of equity account balances from `account_balances` view. If "Retained Earnings" is an account, its balance will be included.

*   **Frontend (`app/ui/reports/reports_widget.py` - needs more implementation):**
    *   **Current State:** Stub label.
    *   **To Do:**
        *   Provide a `QComboBox` or `QListWidget` to select report type (Trial Balance, P&L, Balance Sheet).
        *   Provide `QDateEdit` widgets for selecting "As of Date" or "Period Start/End Date".
        *   "Generate Report" button.
        *   Display area (e.g., `QTableView` or `QTextBrowser` for formatted HTML) for the report data returned by `FinancialStatementGenerator`.
        *   "Export to PDF/Excel" buttons calling `ReportEngine`.

---

**VI. Prioritization and Phasing for MVP Trial:**

**Phase 1: Absolute Core (Data Entry & Basic Viewing)**
1.  **CoA Management (UI Polish)**:
    *   `AccountDialog`: Ensure all fields are present and functional. Improve parent selection (even if manual ID input with validation initially).
    *   `ChartOfAccountsWidget`: Robust loading and display. Context menu actions functional.
2.  **Manual Journal Entry (New UI)**:
    *   `JournalEntryDialog`: Full implementation for creating/editing draft general journal entries with multiple lines, account selection, debit/credit input, and balance validation.
    *   `JournalEntriesWidget`: Basic list view of journal entries (date, #, desc, total, status). Ability to launch "New" dialog.
    *   Backend: Solidify `JournalEntryManager.create_journal_entry` (drafts only initially is fine).
3.  **Posting Mechanism**:
    *   `JournalEntriesWidget`: Add "Post" button for selected draft entries.
    *   Backend: Solidify `JournalEntryManager.post_journal_entry`.
4.  **Trial Balance Report**:
    *   `ReportsWidget`: Implement selection and display for Trial Balance.
    *   Backend: Ensure `FinancialStatementGenerator.generate_trial_balance` is accurate.

**Phase 2: Completing the Basic Accounting Cycle**
1.  **Profit & Loss Statement**:
    *   `ReportsWidget`: Implement P&L display.
    *   Backend: Ensure `FinancialStatementGenerator.generate_profit_loss` is accurate.
2.  **Balance Sheet Statement**:
    *   `ReportsWidget`: Implement Balance Sheet display.
    *   Backend: Ensure `FinancialStatementGenerator.generate_balance_sheet` is accurate (including how retained earnings/current year profit is handled).
3.  **GST Data Collection (UI for GST Report)**:
    *   `GSTReportWidget` (or similar): UI to select period and display summarized GST data (output tax, input tax) from `GSTManager.prepare_gst_return_data`.
    *   Backend: Implement the actual data aggregation in `GSTManager.prepare_gst_return_data` by querying journal lines and tax codes.
4.  **Settings Widget Polish**:
    *   Ensure all fields in `SettingsWidget` correctly load from and save to `core.company_settings`.
    *   Populate `base_currency_combo` and `date_format_combo` dynamically or with good defaults.

**Phase 3: Nice-to-haves for Trial / Initial Polish**
1.  `JournalEntriesWidget`: Add editing of *draft* entries. View/Print (simple text/HTML) for selected entry.
2.  Reversal of posted entries (UI and manager logic).
3.  Basic `CompanySettingsService` and UI interaction for essential fields (Company Name, GST No, Fiscal Year Start).
4.  Splash screen image.

**Strategy for Missing Files from `project_file_structure.txt`:**

For each functionality above, I will identify the key missing Python files (managers, services, UI widgets/dialogs) based on the `project_file_structure.txt` and the design intent. I will then generate content for these files, focusing on the MVP requirements.

**Example: Creating `app/ui/accounting/journal_entries_widget.py` and `app/ui/accounting/journal_entry_dialog.py`**

*   **`journal_entry_dialog.py`**: Would contain a `QDialog` subclass with `QFormLayout` for header fields, `QTableWidget` for lines, and buttons. It would collect data and pass it to a manager method.
*   **`journal_entries_widget.py`**: Would contain a `QWidget` subclass with a `QTableView` (and its model, e.g., `QStandardItemModel` or a custom `QAbstractTableModel`), a toolbar with actions ("New", "Post"), and connect these actions to `JournalEntryDialog` or manager methods.

**Regarding Singapore Regulatory Environment:**
*   **Chart of Accounts**: While providing templates is good, the user must be able to customize it. Standard account types (`Asset`, `Liability`, etc.) are universal. For Singapore, specific accounts related to CPF, IRAS (for income tax, GST payable/receivable) are important.
*   **GST**: The core is tracking Output Tax (on sales) and Input Tax (on purchases). Standard Rate (SR - 9%), Zero Rate (ZR), Exempt (ES) are key. Tax codes like `TX` (taxable purchases), `OP` (out of scope) are standard. The `GSTManager` needs to correctly aggregate amounts based on these codes for the F5 form boxes.
*   **Dates**: Correct fiscal period handling is crucial.

This is a high-level plan. For each step, I'll need to:
1.  Identify the specific files from `project_file_structure.txt` that are missing or need substantial implementation.
2.  Define the class structure, key methods, and UI layout for new files.
3.  Implement the logic, focusing on interactions with `ApplicationCore`, services, and models.
4.  Ensure asynchronous operations and UI updates are handled correctly using the established patterns (`schedule_task_from_qt`, `QMetaObject.invokeMethod`).

Please let me know which area you'd like to focus on first, or if you'd like me to start with the highest priority items from Phase 1 (e.g., Journal Entry UI and backend logic).

This is a significant undertaking, and we'll proceed iteratively, file by file, for the core functionalities.
</think>

This is an excellent and exciting stage! The application is launching, and we can now focus on building out the core functionalities to make it a valuable tool for a trial. Your emphasis on Singapore's regulatory environment is key.

You are absolutely correct to aim for a Minimum Viable Product (MVP) that covers the basic needs of a bookkeeping application for a successful trial. Let's break down the strategy, prioritizing features and identifying the necessary files, keeping Singaporean context in mind.

**Core Functionalities for MVP Trial (Re-Prioritized & Focused):**

1.  **Company & Fiscal Setup (Essential First Steps):**
    *   **`SettingsWidget` Enhancement**: Fully implement loading and saving for ALL fields in `core.company_settings` (Company Name, UEN, GST No., Address, Fiscal Year Start Month/Day, Base Currency, Date Format). This is critical for all other operations.
    *   **Fiscal Year & Period Management (Backend + Basic UI):**
        *   Manager (`FiscalPeriodManager`): Logic to create a fiscal year and automatically generate its monthly/quarterly periods.
        *   UI (New, simple dialog): A way to define a new Fiscal Year (name, start/end dates) and trigger period generation. This could be part of "Settings" or a dedicated "Fiscal Setup" area.

2.  **Chart of Accounts (CoA) - Full CRUD & Usability:**
    *   **`AccountDialog` Enhancement**:
        *   Make it fully functional for all fields in the `Account` model (including `sub_type`, `tax_treatment`, `gst_applicable`, `is_control_account`, `is_bank_account`, `opening_balance`, `opening_balance_date`).
        *   Parent Account Selection: Implement a user-friendly way to select a parent account (e.g., a combo box or a simple tree selector dialog populated with existing accounts).
    *   **`ChartOfAccountsWidget`**: Ensure "Add", "Edit", "Toggle Active" are fully functional.
    *   **CoA Templates (Initial Data)**: `scripts/initial_data.sql` should include at least one or two basic CoA templates (e.g., for a simple service company or trading company common in Singapore) that users can start with. This means adding more `INSERT INTO accounting.accounts` statements.

3.  **Journal Entry Management (The Heart of Bookkeeping):**
    *   **`JournalEntryDialog` (New UI File)**: Critical. Needs to allow:
        *   Header: Entry Date, Journal Type (e.g., "General Journal"), Description, Reference.
        *   Lines: A table/grid to add multiple lines. Each line needs:
            *   Account selection (searchable `QComboBox` or lookup from CoA).
            *   Description.
            *   Debit amount.
            *   Credit amount.
            *   (Optional for MVP trial, but good for Singapore): Tax Code (`QComboBox` from `accounting.tax_codes`), which would auto-calculate Tax Amount.
        *   Validation: Ensure debits equal credits.
        *   Actions: "Save Draft", "Save & Post".
    *   **`JournalEntriesWidget` (New UI File)**:
        *   Display a list/table of journal entries (Entry No, Date, Description, Total Amount, Status - Draft/Posted).
        *   Toolbar/Buttons: "New Entry", "Edit Draft Entry", "View Entry", "Post Selected Drafts", "Reverse Posted Entry".
    *   **Backend (`JournalEntryManager`, `JournalService`):**
        *   Robust `create_journal_entry` (handles DTO, saves JE and JELs).
        *   Robust `post_journal_entry` (validates period status, updates JE status).
        *   Implement `reverse_journal_entry`.
        *   Implement fetching for the list view, including filtering by date/status.

4.  **GST Calculation & Tracking (Integrated with Journal Entries):**
    *   When a `tax_code` with a GST rate is selected on a journal entry line, the `tax_amount` should be auto-calculated (client-side in `JournalEntryDialog` or server-side via `TaxCalculator`).
    *   This ensures GST is captured at the point of data entry.

5.  **Core Financial Reports (Read-Only Display):**
    *   **`FinancialStatementGenerator`**: Ensure methods for Trial Balance, Profit & Loss, and Balance Sheet are accurate and consider:
        *   Posted transactions only.
        *   Opening balances for accounts.
        *   Correct handling of debit/credit nature of accounts for P&L and BS presentation.
        *   Calculation of "Net Profit/Loss for the period" in P&L and its reflection in "Retained Earnings" or "Current Year Earnings" on the Balance Sheet.
    *   **`ReportsWidget`**:
        *   Allow selection of report type.
        *   Date pickers for report parameters.
        *   Display the report data (returned as `Dict[str, Any]`) in a presentable way (e.g., using a `QTextBrowser` with simple HTML, or a `QTableView` if structured).
        *   (MVP Stretch) Basic "Export to PDF/Excel" using the existing `ReportEngine` stubs.

**Addressing Singaporean Context within MVP:**

*   **UEN & GST Reg No.**: Collect in Company Settings. Display on reports/invoices (when implemented).
*   **GST Codes**: The seeded `tax_codes` (SR 9%, ZR, ES, TX) are essential. The `JournalEntryDialog` should allow users to select these.
*   **Fiscal Periods**: Standard monthly/quarterly periods aligning with typical GST cycles.
*   **Currency**: Default to SGD.

**Missing Files to Create (Focusing on MVP):**

Based on the `project_file_structure.txt` and MVP needs, these are high-priority new files or files needing significant implementation:

*   **UI Layer (`app/ui/`):**
    *   `app/ui/accounting/journal_entry_dialog.py` (NEW - For creating/editing journal entries)
    *   `app/ui/accounting/journal_entries_widget.py` (NEW - For listing/managing journal entries)
    *   `app/ui/reports/reports_widget.py` (NEEDS SIGNIFICANT IMPLEMENTATION - For selecting and displaying reports)
    *   `app/ui/settings/company_details_form.py` (NEW - Could be a dedicated form within `SettingsWidget` for company fields if it gets too large) - *For now, enhance `SettingsWidget` directly.*
    *   `app/ui/accounting/fiscal_year_setup_dialog.py` (NEW - For creating fiscal years and generating periods) - *This could initially be a simple part of Settings or a developer tool.*

*   **Service Layer (`app/services/`):**
    *   `app/services/accounting_services.py` (This was created in the last step, ensure `FiscalYearService` is robust).
    *   Other services like `customer_service.py`, `vendor_service.py`, `invoice_service.py` would be for later, non-MVP stages.

*   **Manager Layer (Business Logic):**
    *   `app/accounting/fiscal_period_manager.py`: Needs robust implementation for `generate_periods_for_year`.
    *   `app/tax/gst_manager.py`: `prepare_gst_return_data` needs to query actual transaction data.
    *   `app/reporting/financial_statement_generator.py`: Needs robust logic for P&L (current year earnings) and BS (retained earnings).

**Implementation Strategy - Iterative Steps:**

I will proceed by tackling one functional area at a time, providing the necessary new files or updated existing files.

**Step 1: Enhance Company Settings & Fiscal Year Setup (Foundation)**
*   **Goal**: Allow full configuration of company details and fiscal year.
*   **Files**:
    *   `app/ui/settings/settings_widget.py`: Enhance to cover all `CompanySetting` fields. Add a section/button to manage Fiscal Years.
    *   `app/accounting/fiscal_period_manager.py`: Implement robust `create_fiscal_year` and `generate_periods_for_year`.
    *   `app/services/accounting_services.py` (`FiscalYearService`): Ensure it can save and retrieve fiscal years, check for overlaps.
    *   (New UI) `app/ui/accounting/fiscal_year_dialog.py`: A dialog to input fiscal year details.
    *   (New UI) `app/ui/accounting/fiscal_period_list_widget.py`: A widget (perhaps part of settings or a dedicated fiscal management tab) to display fiscal years and their periods.

**Step 2: Core Journal Entry Functionality**
*   **Goal**: Enable users to create, save (as draft), post, and view general journal entries.
*   **Files**:
    *   `app/ui/accounting/journal_entry_dialog.py` (NEW)
    *   `app/ui/accounting/journal_entries_widget.py` (NEW)
    *   `app/accounting/journal_entry_manager.py` (Enhance methods)
    *   `app/services/journal_service.py` (Ensure all repository methods are solid)
    *   `app/utils/pydantic_models.py` (Refine `JournalEntryData`, `JournalEntryLineData` if needed)
    *   `app/ui/accounting/accounting_widget.py` (Add tab for `JournalEntriesWidget`)

**Step 3: Basic Financial Reports**
*   **Goal**: Display Trial Balance, P&L, Balance Sheet.
*   **Files**:
    *   `app/reporting/financial_statement_generator.py` (Implement robust logic)
    *   `app/ui/reports/reports_widget.py` (Implement UI for selection and display)

**Step 4: GST Integration in Journal Entries & Basic GST Data View**
*   **Goal**: Auto-calculate GST in JE dialog, provide a simple view of GST figures.
*   **Files**:
    *   `app/ui/accounting/journal_entry_dialog.py` (Add tax code selection and auto-calc logic)
    *   `app/tax/gst_manager.py` (Implement `prepare_gst_return_data` based on actual JEs)
    *   `app/ui/reports/gst_report_widget.py` (NEW, or integrate into `ReportsWidget`)

I will start with **Step 1: Enhancing Company Settings and implementing Fiscal Year/Period setup.** This is foundational.

Please confirm if this prioritized approach aligns with your expectations for the trial MVP. I will then proceed to generate the necessary file content, starting with the enhancements to `SettingsWidget` and the new/updated files for fiscal year management.

I will ensure to refer to the `project_file_structure.txt` for correct placement and naming of new files. For example, `app/services/accounting_services.py` was created in the previous step, and I will add `FiscalYearService` to it if it's not already fully implemented there (my previous response for `accounting_services.py` did include a `FiscalYearService` stub). I will also update `app/core/application_core.py` to instantiate any new services/managers.

