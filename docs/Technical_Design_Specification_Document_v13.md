# Technical Design Specification Document: SG Bookkeeper (update)

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version 13.0, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities up to schema version 1.0.4. This version specifically details the implementation of:
*   **Bank Reconciliation Module**: Comprehensive UI and backend logic for reconciling bank statements with system bank transactions, including matching, creating adjustment journal entries, and saving reconciliation status.
*   **CSV Bank Statement Import**: Functionality to import bank transactions from CSV files with configurable column mapping.
*   **Automated Bank Transaction Creation from Journal Entries**: Posting a journal entry that affects a bank-linked GL account now automatically generates a corresponding system bank transaction.
*   **Database Enhancements**: Introduction of the `business.bank_reconciliations` table, new fields in `bank_accounts` and `bank_transactions`, and a database trigger for automatic bank balance updates.
These build upon previously documented features like Payments, Audit Log UI, enhanced GST Reporting, Sales/Purchase Invoicing, and core accounting/admin functionalities.

### 1.2 Scope
This TDS covers:
-   System Architecture: UI, business logic, data access layers, asynchronous processing.
-   Database Schema: Details as per `scripts/schema.sql` (reflecting v1.0.4 changes), including new tables, columns, and triggers for bank reconciliation.
-   Key UI Implementation Patterns for new banking features.
-   Core Business Logic for bank reconciliation and CSV import.
-   Data Models (SQLAlchemy ORM) and Data Transfer Objects (Pydantic DTOs) related to new features.
-   Security Implementation (no major changes in this version, but context remains).
-   Deployment and Initialization procedures (updated `initial_data.sql` with new permissions/configs).
-   Current Implementation Status up to this version.

### 1.3 Intended Audience
-   Software Developers
-   QA Engineers
-   System Administrators
-   Technical Project Managers

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application (Python, PySide6, PostgreSQL) for SMB accounting in Singapore. Key features include double-entry bookkeeping, GST management (with detailed F5 export), financial reporting, CRM/SRM (Customers, Vendors, Products), full invoicing lifecycle, payment processing with allocation, bank account management, manual bank transaction entry, **CSV bank statement import, a full bank reconciliation module**, and comprehensive system administration (Users, Roles, Permissions, Audit Logs). The application emphasizes data integrity, local compliance, user-friendliness, and robust auditability.

### 1.5 Current Implementation Status
As of version 13.0 (reflecting schema v1.0.4):
*   All features listed in TDS v12.0 are considered implemented.
*   **New/Enhanced Banking Features**:
    *   **Bank Reconciliation**: Full UI (`BankReconciliationWidget`) and backend logic (`BankReconciliationService`, updates to `BankTransactionManager`) for comparing bank statement items with system transactions, matching items, calculating discrepancies, facilitating adjustment JEs, and saving the reconciliation state.
    *   **CSV Bank Statement Import**: UI (`CSVImportConfigDialog`) and backend (`BankTransactionManager.import_bank_statement_csv`) for importing transactions from CSV files.
    *   **Automatic Bank Transactions from JEs**: `JournalEntryManager.post_journal_entry` now creates `BankTransaction` records when a JE impacts a bank-linked GL account.
*   **Database**: Schema updated with `bank_reconciliations` table, new fields in `bank_accounts` and `bank_transactions`, and a trigger for `bank_accounts.current_balance` updates. `initial_data.sql` includes new banking permissions and config keys.
*   **Audit Log Service**: Minor improvements to change summary formatting and query logic.

## 2. System Architecture 
*(The high-level architecture and diagram from TDS v12.0 remain largely unchanged and accurate for v13.0. The new features are integrated within the existing layers.)*

### 2.1 High-Level Architecture
(Diagram from TDS v12.0 is still representative)

### 2.2 Component Architecture (Updates for Bank Reconciliation)

#### 2.2.1 Core Components (`app/core/`)
*   **`ApplicationCore` (`app/core/application_core.py`)**:
    *   Now initializes and provides access to `BankReconciliationService`.
    *   `JournalEntryManager` instantiation no longer passes `SequenceGenerator`.
    *   Ensures consistent `CurrencyRepoService` injection for managers needing currency data.

#### 2.2.4 Managers (Business Logic Layer - `app/accounting/`, `app/business_logic/`)
*   **`app/accounting/JournalEntryManager`**:
    *   The `post_journal_entry` method now includes logic to check if any line in the journal entry affects a GL account flagged as `is_bank_account` and linked to a `business.bank_accounts` record. If so, it automatically creates a corresponding `BankTransaction` record in the `business.bank_transactions` table, ensuring system-generated bank movements are captured.
*   **`app/business_logic/BankTransactionManager`**:
    *   **`import_bank_statement_csv`**: New method that takes a CSV file path, column mapping configuration, and import options. It reads the CSV, parses rows according to the mapping, transforms data into `BankTransactionCreateData` DTOs (marking them as `is_from_statement=True`), performs basic duplicate detection against existing statement transactions, and saves valid new transactions using `BankTransactionService`. It returns a summary of the import results.
    *   **`get_unreconciled_transactions_for_matching`**: New method that fetches two lists of `BankTransactionSummaryData`: (1) unreconciled transactions originating from imported statements (`is_from_statement=True`) and (2) unreconciled system-generated bank transactions (`is_from_statement=False`), both up to a specified statement end date. This data is used to populate the bank reconciliation UI.

#### 2.2.5 User Interface (Presentation Layer - `app/ui/banking/`)
*   **`BankReconciliationWidget` (`app/ui/banking/bank_reconciliation_widget.py`)**: A new, central UI component for the bank reconciliation process. It features:
    *   Controls to select a bank account, input the statement end date, and statement ending balance.
    *   A "Load / Refresh Transactions" button to fetch data via `BankTransactionManager`.
    *   A "Reconciliation Summary" group box displaying calculated figures: book balance (from GL), adjustments for unmatched statement items (interest, charges), adjusted book balance, statement ending balance, adjustments for outstanding system items (deposits in transit, outstanding withdrawals), adjusted bank balance, and the final difference.
    *   A `QSplitter` dividing the main area into two tables:
        *   "Bank Statement Items (Unreconciled)": Displays transactions loaded from imported statements (`is_from_statement=True`) using `ReconciliationTableModel`.
        *   "System Bank Transactions (Unreconciled)": Displays system-generated transactions (`is_from_statement=False`) using another `ReconciliationTableModel`.
    *   Both tables allow users to select/check items for matching.
    *   Action buttons:
        *   "Match Selected": (Currently for UI-side calculation/clearing) Allows users to mark selected items from both tables as "matched" for the current reconciliation session if their amounts net to zero.
        *   "Add Journal Entry": For selected unmatched statement items, it pre-fills and opens the `JournalEntryDialog` to allow the user to create the corresponding system entry (e.g., for bank charges or interest earned).
        *   "Save Reconciliation": Enabled when the difference is zero. Persists the reconciliation by creating a `BankReconciliation` record and updating the `is_reconciled` status of matched `BankTransaction` records via `BankReconciliationService`.
*   **`ReconciliationTableModel` (`app/ui/banking/reconciliation_table_model.py`)**: A specialized `QAbstractTableModel` for the two tables in the reconciliation widget. It supports displaying `BankTransactionSummaryData` and includes a checkable column for users to select items. Emits a signal when an item's check state changes to trigger summary recalculations.
*   **`CSVImportConfigDialog` (`app/ui/banking/csv_import_config_dialog.py`)**: A new dialog that allows users to:
    *   Select a CSV file using `QFileDialog`.
    *   Configure CSV format options (has header, date format string).
    *   Map CSV columns (either by header name if present, or by 0-based index) to standard bank transaction fields: Date, Description, Debit Amount, Credit Amount, Single Amount (if applicable), Reference, Value Date.
    *   Specify if debits are negative in a single amount column.
    *   Initiates the import process by calling `BankTransactionManager.import_bank_statement_csv`.
*   **`BankTransactionsWidget` (`app/ui/banking/bank_transactions_widget.py`)**:
    *   Added a new toolbar action "Import Statement (CSV)" which opens the `CSVImportConfigDialog` for the currently selected bank account.
*   **`MainWindow` (`app/ui/main_window.py`)**:
    *   A new top-level tab "Bank Reconciliation" is added, hosting the `BankReconciliationWidget`. The "Banking C.R.U.D" tab name is indicative of its focus on basic bank account and transaction management.

## 3. Data Architecture (Updates)

### 3.1 Database Schema Overview
The database schema (as per `scripts/schema.sql` v1.0.4) now includes specific structures to support bank reconciliation:
-   **New Table: `business.bank_reconciliations`**:
    *   `id` (PK, SERIAL)
    *   `bank_account_id` (FK to `business.bank_accounts.id`, NOT NULL)
    *   `statement_date` (DATE, NOT NULL): The end date of the bank statement being reconciled.
    *   `statement_ending_balance` (NUMERIC(15,2), NOT NULL)
    *   `calculated_book_balance` (NUMERIC(15,2), NOT NULL): The general ledger's bank account balance that, after considering reconciling items, matches the statement.
    *   `reconciled_difference` (NUMERIC(15,2), NOT NULL): Should be zero or very close to zero for a successful reconciliation.
    *   `reconciliation_date` (TIMESTAMP WITH TIME ZONE, DEFAULT CURRENT_TIMESTAMP): When this reconciliation record was created.
    *   `notes` (TEXT, NULL)
    *   `created_at`, `updated_at` (TIMESTAMPTZ)
    *   `created_by_user_id` (FK to `core.users.id`, NOT NULL)
    *   Unique constraint on `(bank_account_id, statement_date)`.
-   **Table `business.bank_accounts`**:
    *   New column: `last_reconciled_balance NUMERIC(15,2) NULL` - Stores the statement ending balance of the last successful reconciliation for this account.
-   **Table `business.bank_transactions`**:
    *   New column: `reconciled_bank_reconciliation_id INT NULL` - Foreign key referencing `business.bank_reconciliations.id`. This links a bank transaction to the specific reconciliation instance where it was cleared.
    *   Existing (from v1.0.3) relevant columns:
        *   `is_from_statement BOOLEAN NOT NULL DEFAULT FALSE`: True if the transaction was imported from a bank statement CSV.
        *   `raw_statement_data JSONB NULL`: Stores the original row data from the imported CSV for statement transactions.
        *   `is_reconciled BOOLEAN DEFAULT FALSE NOT NULL`: Standard flag indicating if a transaction has been reconciled.
        *   `reconciled_date DATE NULL`: The date (typically statement_date) it was reconciled.
-   **Triggers**:
    *   The new trigger `trg_update_bank_balance` on `business.bank_transactions` now calls `business.update_bank_account_balance_trigger_func()` AFTER INSERT, UPDATE, or DELETE. This function adjusts the `current_balance` in the corresponding `business.bank_accounts` record based on the transaction's amount, ensuring the bank account's running balance is automatically maintained by the database.
    *   The audit trigger `audit.log_data_change_trigger_func()` has been extended to cover `business.bank_accounts` and `business.bank_transactions`.

### 3.2 SQLAlchemy ORM Models (`app/models/`)
-   **`app/models/business/bank_reconciliation.py`**: New `BankReconciliation` ORM class mapping to the `business.bank_reconciliations` table, including relationships.
-   **`app/models/business/bank_account.py`**: `BankAccount` model updated to include the `last_reconciled_balance` attribute and a `reconciliations` relationship (one-to-many, to `BankReconciliation`).
-   **`app/models/business/bank_transaction.py`**: `BankTransaction` model updated to include `reconciled_bank_reconciliation_id` attribute and a `reconciliation_instance` relationship (many-to-one, to `BankReconciliation`). Also includes existing `is_from_statement` and `raw_statement_data` attributes.

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
-   New DTOs for bank reconciliation:
    *   **`BankReconciliationBaseData`**: Fields like `bank_account_id`, `statement_date`, `statement_ending_balance`, `calculated_book_balance`, `reconciled_difference`, `notes`.
    *   **`BankReconciliationCreateData`**: Extends `BankReconciliationBaseData` and includes `UserAuditData`.
    *   **`BankReconciliationData`**: Full representation including `id`, audit timestamps, typically for retrieval.

## 4. Module and Component Specifications (Updates)

### 4.7 Banking (`app/business_logic/bank_transaction_manager.py`, `app/services/business_services.py`, `app/ui/banking/`)
-   **Bank Reconciliation Process**:
    -   **UI**: `BankReconciliationWidget` allows users to select a bank account, input statement details, and load unreconciled transactions. It displays statement items and system transactions in separate tables. Users can select items for matching. The UI dynamically calculates and shows a reconciliation summary (book balance vs. statement balance, considering outstanding items). Buttons are provided to "Match Selected", "Add Journal Entry" (for statement-only items like bank charges/interest, which pre-fills `JournalEntryDialog`), and "Save Reconciliation".
    -   **Manager (`BankTransactionManager`)**:
        *   `get_unreconciled_transactions_for_matching()`: Fetches unreconciled statement transactions and system transactions up to the statement date to populate the UI.
    -   **Service (`BankReconciliationService`)**:
        *   `save_reconciliation_details()`: This is the core persistence method. It receives a `BankReconciliation` ORM object and lists of cleared transaction IDs (both from statement and system). Within a single database transaction, it:
            1.  Saves the `BankReconciliation` record.
            2.  Updates all provided `BankTransaction` IDs: sets `is_reconciled=True`, `reconciled_date` (to statement end date), and `reconciled_bank_reconciliation_id` to link them to the saved reconciliation record.
            3.  Updates the `BankAccount` record by setting `last_reconciled_date` and `last_reconciled_balance`.
-   **CSV Bank Statement Import**:
    -   **UI**: `CSVImportConfigDialog` allows users to select a CSV file and configure mappings for columns (Date, Description, Amount/Debit/Credit, Reference, Value Date) and format options (header, date format).
    -   **Manager (`BankTransactionManager`)**:
        *   `import_bank_statement_csv()`: Parses the CSV according to the configuration. For each valid row, it creates a `BankTransaction` record with `is_from_statement=True` and stores the original CSV row in `raw_statement_data`. Performs basic duplicate checks against existing statement transactions. Returns an import summary (total, imported, skipped, failed).
-   **Automatic Bank Transactions from Journal Entries**:
    -   **Manager (`JournalEntryManager`)**: The `post_journal_entry()` method, when posting a JE, now iterates through its lines. If a line affects a GL account that is configured as `is_bank_account=True` and has a corresponding `business.bank_accounts` record, a new system-generated `BankTransaction` (with `is_from_statement=False`) is automatically created. The `BankTransaction.amount` is signed based on whether the JE line was a debit (inflow) or credit (outflow) to the bank GL account.

## 5. User Interface Implementation (`app/ui/`) (Updates)
*   **`BankReconciliationWidget`**: Added to the "Bank Reconciliation" tab in `MainWindow`. Provides the main interface for the reconciliation workflow.
*   **`ReconciliationTableModel`**: Supports the checkable tables in `BankReconciliationWidget`.
*   **`CSVImportConfigDialog`**: Modal dialog launched from `BankTransactionsWidget` for CSV import setup.
*   **`BankTransactionsWidget`**: Toolbar now includes an "Import Statement (CSV)" action.

## 7. Database Access Implementation (Updates)
*   `BankReconciliationService` uses `DatabaseManager` to ensure that saving reconciliation details (the `BankReconciliation` record, updates to `BankTransaction` records, and update to the `BankAccount` record) occurs within a single atomic database transaction.

## 10. Data Flow (New Example: Bank Reconciliation Process)

1.  **Setup (UI: `BankReconciliationWidget`)**:
    *   User selects a Bank Account from a combo box.
    *   User enters the Statement Date and Statement Ending Balance from their bank statement.
    *   User clicks "Load / Refresh Transactions".
2.  **Fetch Data (Manager: `BankTransactionManager`, Service: `BankTransactionService`, `JournalService`, `AccountService`)**:
    *   `_fetch_and_populate_transactions` in the widget calls `BankTransactionManager.get_unreconciled_transactions_for_matching()`.
    *   This manager method, via `BankTransactionService`, fetches:
        *   Unreconciled statement items (`is_from_statement=True`) up to `statement_date`.
        *   Unreconciled system bank transactions (`is_from_statement=False`) up to `statement_date`.
    *   The widget also fetches the current GL balance for the bank account's linked GL account as of `statement_date` via `JournalService.get_account_balance()`. This becomes the starting "Book Balance (per GL)".
3.  **Display & Initial Calculation (UI)**:
    *   The two lists of transactions are displayed in separate tables using `ReconciliationTableModel`.
    *   The "Reconciliation Summary" section is populated. Initially:
        *   "Add: Interest / Credits (on Stmt, not Book)" and "Less: Bank Charges / Debits (on Stmt, not Book)" are sums of *all currently unchecked* statement items (positive for credits, negative for debits on statement that affect amount).
        *   "Add: Deposits in Transit (in Book, not Stmt)" and "Less: Outstanding Withdrawals (in Book, not Stmt)" are sums of *all currently unchecked* system transactions.
        *   Adjusted Book Balance and Adjusted Bank Balance are calculated, and the Difference is shown.
4.  **User Interaction (UI)**:
    *   **Matching**: User selects one or more items from the "Statement Items" table and one or more items from the "System Transactions" table.
        *   If "Match Selected" is clicked: The UI checks if the sum of selected statement items equals the sum of selected system items. If so, these items are conceptually "cleared" for this session (e.g., their check state is toggled, and they are removed from the summary calculations). No DB changes yet.
    *   **Creating JEs for Statement Items**: User selects an unmatched statement item (e.g., a bank charge).
        *   Clicks "Add Journal Entry".
        *   `JournalEntryDialog` opens, pre-filled with one line (debiting Bank Charge Expense, crediting Bank GL Account, or vice-versa for interest).
        *   User completes and posts the JE.
        *   `JournalEntryManager.post_journal_entry()` creates the JE and also creates a new system `BankTransaction` (with `is_from_statement=False`).
        *   The `BankReconciliationWidget` reloads/refreshes its transaction lists. The new system transaction appears and can now be matched with the original statement item.
5.  **Saving Reconciliation (UI -> Manager (conceptual) -> Service: `BankReconciliationService`)**:
    *   When the "Difference" in the summary is zero (or within tolerance), the "Save Reconciliation" button is enabled.
    *   User clicks "Save Reconciliation".
    *   The UI collects data for `BankReconciliationCreateData` DTO (bank_account_id, statement_date, statement_ending_balance, final calculated_book_balance, notes).
    *   It also collects the IDs of all `BankTransaction` records that were successfully "cleared" (matched or accounted for by new JEs) during this session.
    *   `BankReconciliationService.save_reconciliation_details()` is called (likely via a manager method). This service method:
        1.  Creates and saves a new `business.bank_reconciliations` record.
        2.  Updates all the "cleared" `business.bank_transactions` records: sets `is_reconciled=True`, `reconciled_date` (to statement_date), and `reconciled_bank_reconciliation_id` (to the ID of the new reconciliation record).
        3.  Updates the `business.bank_accounts` record: sets `last_reconciled_date` (to statement_date) and `last_reconciled_balance` (to statement_ending_balance).
        4.  All these DB operations are performed in a single transaction.
6.  **UI Feedback**: Success or error message is displayed. The reconciliation UI might clear or reload to reflect the saved state.

## 11. Conclusion (Updated)
Version 13.0 of SG Bookkeeper introduces significant advancements in its banking module, primarily through the implementation of CSV bank statement import and a comprehensive bank reconciliation feature. These additions, along with the automated creation of bank transactions from relevant journal entries, greatly enhance the application's practical utility for managing bank activities and ensuring financial accuracy. The underlying architecture has proven capable of accommodating these complex features. Future efforts will continue to refine these modules, expand reporting capabilities, and prioritize the development of a robust automated testing suite.

---
https://drive.google.com/file/d/11Cv4mFJ5z4I3inVCg8nkncVsAQtuIWrl/view?usp=sharing, https://drive.google.com/file/d/13aFutu059EFwgvQM4JE5LrYT13_62ztj/view?usp=sharing, https://drive.google.com/file/d/150VU2J4NfkYirCIGqQxC5VL9a_s7jyV0/view?usp=sharing, https://drive.google.com/file/d/1Fcdn0EWCauERrISMKReM_r0_nVIQvPiH/view?usp=sharing, https://drive.google.com/file/d/1GWOGYCBqwiPra5MdbwwhwXrV2V-gc4iw/view?usp=sharing, https://drive.google.com/file/d/1IRffneWyqY8ILVvfOu3apYxB15SnhMYD/view?usp=sharing, https://drive.google.com/file/d/1QYQSJ32tb7UYfuT-VHC2vgYYS3Cw_9dz/view?usp=sharing, https://drive.google.com/file/d/1S4zRP59L2Jxru__jXeoTL2TGZ4JN_GOT/view?usp=sharing, https://drive.google.com/file/d/1X5XkobtrDHItY5dTnWRYajA9LTVvZTGy/view?usp=sharing, https://drive.google.com/file/d/1bsb7xdrTRvfFSLOJVv_YBVncejRYeX-p/view?usp=sharing, https://drive.google.com/file/d/1eU9E4v6uT69z91uEABi8xf4-L1_PUKaI/view?usp=sharing, https://drive.google.com/file/d/1fcRRxU4xYdqMgGp58OyuFDOqIcGeOIW_/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221gVm5GnROGWVVYBXkgumxd5puGZ6g5Qs3%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1hF6djKphaR51gqDKE6GLgeBnlWXdKcWU/view?usp=sharing, https://drive.google.com/file/d/1ndjSoP14ry1oCHgOguxNgNWxyP4c18ww/view?usp=sharing, https://drive.google.com/file/d/1zWrsOeANNSTZ51c666H-DxQapeSjXnZY/view?usp=sharing

