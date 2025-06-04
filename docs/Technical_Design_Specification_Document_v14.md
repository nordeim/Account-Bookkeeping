# Technical Design Specification Document: SG Bookkeeper (final draft - to update with missing details from earlier versions)

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version 13.0, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities up to schema version 1.0.4. This version specifically details the implementation of:
*   **Bank Reconciliation Module**: Comprehensive UI and backend logic for reconciling bank statements with system bank transactions, including matching, creating adjustment journal entries, and saving reconciliation status.
*   **CSV Bank Statement Import**: Functionality to import bank transactions from CSV files with configurable column mapping.
*   **Automated Bank Transaction Creation from Journal Entries**: Posting a journal entry that affects a bank-linked GL account now automatically generates a corresponding system bank transaction.
*   **Dashboard KPIs (Initial Implementation)**: Display of key financial indicators like YTD P&L figures, cash balance, and AR/AP totals.
*   **Database Enhancements**: Introduction of the `business.bank_reconciliations` table, new fields in `bank_accounts` and `bank_transactions`, and a database trigger for automatic bank balance updates.
These build upon previously documented features like Payments, Audit Log UI, enhanced GST Reporting, Sales/Purchase Invoicing, and core accounting/admin functionalities.

### 1.2 Scope
This TDS covers:
-   System Architecture.
-   Database Schema (reflecting v1.0.4 changes).
-   Key UI Implementation Patterns for new banking and dashboard features.
-   Core Business Logic for bank reconciliation, CSV import, and KPI generation.
-   Data Models (SQLAlchemy ORM) and Data Transfer Objects (Pydantic DTOs).
-   Security Implementation.
-   Deployment and Initialization procedures.
-   Current Implementation Status.

### 1.3 Intended Audience
-   Software Developers, QA Engineers, System Administrators, Technical Project Managers.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application (Python, PySide6, PostgreSQL) for SMB accounting in Singapore. Key features include double-entry bookkeeping, GST management, financial reporting, CRM/SRM, full invoicing lifecycle, payment processing, bank account management with **CSV import and a full bank reconciliation module**, **dashboard KPIs**, and comprehensive system administration.

### 1.5 Current Implementation Status
As of version 13.0 (schema v1.0.4):
*   All features from TDS v12.0.
*   **New/Enhanced Banking & Dashboard Features**:
    *   **Bank Reconciliation**: Full UI and backend logic.
    *   **CSV Bank Statement Import**: UI and backend logic.
    *   **Automatic Bank Transactions from JEs**: Implemented in `JournalEntryManager`.
    *   **Dashboard KPIs**: Initial implementation displaying core YTD P&L, Cash, AR/AP figures.
*   **Database**: Schema v1.0.4 implemented with `bank_reconciliations` table, new bank-related columns, and balance update trigger. `initial_data.sql` updated with new permissions and config keys.
*   **Audit Log Service**: Minor improvements to change summary formatting and query logic.

## 2. System Architecture
*(The high-level architecture and diagram from TDS v12.0 remain valid. New components are integrated within existing layers.)*

### 2.1 High-Level Architecture
(Diagram from TDS v12.0 is still representative)

### 2.2 Component Architecture (Updates)

#### 2.2.1 Core Components (`app/core/`)
*   **`ApplicationCore` (`app/core/application_core.py`)**:
    *   Now initializes and provides `BankReconciliationService` and `DashboardManager`.
    *   `JournalEntryManager` instantiation corrected (no longer takes `SequenceGenerator`).
    *   Corrected `CurrencyRepoService` injection for `CustomerManager` and `VendorManager`.

#### 2.2.4 Managers (Business Logic Layer)
*   **`app/accounting/JournalEntryManager`**:
    *   `create_journal_entry`: Uses DB function for `entry_no`.
    *   `post_journal_entry`: Now auto-creates `BankTransaction` records if a JE line affects a bank-linked GL account.
*   **`app/business_logic/BankTransactionManager`**:
    *   New `import_bank_statement_csv` method for CSV import.
    *   New `get_unreconciled_transactions_for_matching` method for bank reconciliation UI.
*   **`app/reporting/DashboardManager` (New)**:
    *   Located in `app/reporting/dashboard_manager.py`.
    *   `get_dashboard_kpis()`: Fetches data from various services (`FinancialStatementGenerator`, `BankAccountService`, `CustomerService`, `VendorService`, `FiscalYearService`, `CompanySettingsService`) to compute and return KPIs in a `DashboardKPIData` DTO. Handles determination of current fiscal year and base currency.

#### 2.2.5 User Interface (Presentation Layer - `app/ui/`)
*   **`app/ui/dashboard/DashboardWidget`**: Updated from placeholder to display KPIs (revenue, expenses, net profit, cash, AR/AP) fetched via `DashboardManager`. Includes a refresh mechanism.
*   **`app/ui/banking/BankReconciliationWidget` (New)**: Main UI for bank reconciliation, featuring setup controls, a summary section, and two tables for matching statement items against system transactions. Includes actions for matching, creating adjustment JEs, and saving the reconciliation.
*   **`app/ui/banking/ReconciliationTableModel` (New)**: Table model for the reconciliation tables, supporting checkable items.
*   **`app/ui/banking/CSVImportConfigDialog` (New)**: Dialog for configuring CSV bank statement imports.
*   **`app/ui/banking/BankTransactionsWidget`**: Added "Import Statement (CSV)" action.
*   **`app/ui/main_window.py`**: "Bank Reconciliation" tab added.

## 3. Data Architecture (Updates based on Schema v1.0.4)

### 3.1 Database Schema Overview
Key updates for v1.0.4 (reflected in `scripts/schema.sql`):
-   **New Table: `business.bank_reconciliations`**: Stores completed reconciliation summaries.
    *   Columns: `id`, `bank_account_id` (FK), `statement_date`, `statement_ending_balance`, `calculated_book_balance`, `reconciled_difference`, `reconciliation_date`, `notes`, `created_by_user_id` (FK), audit timestamps.
    *   Unique constraint: `(bank_account_id, statement_date)`.
-   **Table `business.bank_accounts`**:
    *   Added `last_reconciled_balance NUMERIC(15,2) NULL`.
-   **Table `business.bank_transactions`**:
    *   Added `reconciled_bank_reconciliation_id INT NULL` (FK to `bank_reconciliations.id`).
    *   Existing fields `is_from_statement BOOLEAN` and `raw_statement_data JSONB` are utilized by CSV import.
-   **New Trigger: `business.update_bank_account_balance_trigger_func()`**: Updates `bank_accounts.current_balance` automatically when `bank_transactions` are changed.
-   **Audit Triggers**: Extended to `bank_accounts` and `bank_transactions`.

### 3.2 SQLAlchemy ORM Models (`app/models/`)
*   **`app/models/business/bank_reconciliation.py`**: New `BankReconciliation` ORM model.
*   **`app/models/business/bank_account.py`**: Updated `BankAccount` model.
*   **`app/models/business/bank_transaction.py`**: Updated `BankTransaction` model.

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
*   **New DTOs**:
    *   `BankReconciliationBaseData`, `BankReconciliationCreateData`, `BankReconciliationData`.
    *   `DashboardKPIData`: For structuring KPI values.
*   `GSTTransactionLineDetail` was confirmed as added in previous reviews.
*   `SalesInvoiceSummaryData` and `PurchaseInvoiceSummaryData` confirmed to include `currency_code`.

## 4. Module and Component Specifications (Updates)

### 4.6 Banking Module (Significant Enhancements)
-   **Bank Reconciliation Workflow**:
    1.  User selects bank account, statement date, and end balance in `BankReconciliationWidget`.
    2.  `BankTransactionManager.get_unreconciled_transactions_for_matching` fetches unreconciled statement items (CSV imports) and system transactions.
    3.  UI displays items; user checks items to match. Summary auto-updates.
    4.  For unmatched statement items (e.g., bank charges), user can click "Add Journal Entry". `JournalEntryDialog` opens, pre-filled. Posting this JE auto-creates a system `BankTransaction`.
    5.  When "Difference" is zero, user clicks "Save Reconciliation".
    6.  `BankReconciliationService.save_reconciliation_details` saves the `BankReconciliation` record, updates reconciled `BankTransaction` records, and updates `BankAccount.last_reconciled_date/balance`.
-   **CSV Bank Statement Import**:
    1.  User clicks "Import Statement (CSV)" in `BankTransactionsWidget`.
    2.  `CSVImportConfigDialog` opens for file selection and column mapping.
    3.  `BankTransactionManager.import_bank_statement_csv` processes the file, creates `BankTransaction` records (marked `is_from_statement=True`, `raw_statement_data` populated).

### 4.X Dashboard Module (New Minimal Implementation)
-   **Purpose**: Provide a quick overview of key financial metrics.
-   **Manager (`DashboardManager`)**:
    *   `get_dashboard_kpis()`: Retrieves data for:
        *   YTD Revenue, Expenses, Net Profit (via `FinancialStatementGenerator`).
        *   Current Cash Balance (sum of base currency active bank accounts via `BankAccountService`).
        *   Total Outstanding AR/AP (via `CustomerService`/`VendorService` querying respective balance views).
    *   Returns data in `DashboardKPIData` DTO.
-   **UI (`DashboardWidget`)**:
    *   Displays KPIs fetched from `DashboardManager`.
    *   Includes a refresh button.

## 10. Data Flow (Updates)

*(The Data Flow for Sales Invoice Posting remains relevant. Add a new Data Flow for Bank Reconciliation. The previously generated one for Bank Reconciliation is accurate and reflects the changes.)*

**Data Flow Example: Bank Reconciliation Process**

1.  **Setup (UI: `BankReconciliationWidget`)**: User selects Bank Account, enters Statement Date & Ending Balance, clicks "Load Transactions".
2.  **Fetch Data (Managers/Services)**:
    *   `BankTransactionManager.get_unreconciled_transactions_for_matching()` fetches statement items (`is_from_statement=True`) and system transactions (`is_from_statement=False`) via `BankTransactionService`.
    *   `JournalService.get_account_balance()` fetches GL balance for the bank account.
3.  **Display & Calculate (UI)**: Transactions populate tables. Reconciliation summary (Book vs. Bank, Difference) is calculated based on *unchecked* items.
4.  **User Interaction (UI)**:
    *   **Matching**: User checks matching items. UI updates summary. (Internal "session" match).
    *   **New JE for Statement Item**: User selects an unmatched statement item (e.g., bank charge), clicks "Add Journal Entry". `JournalEntryDialog` is pre-filled. Posting the JE via `JournalEntryManager` also auto-creates a system `BankTransaction`. UI reloads transactions.
5.  **Saving (UI -> Manager -> Service)**: When Difference is zero, user clicks "Save Reconciliation".
    *   `BankReconciliationWidget` collects data (`BankReconciliationCreateData`, IDs of "cleared" transactions).
    *   This is passed to `BankReconciliationService.save_reconciliation_details` (likely via a new manager method in `BankTransactionManager` or a new `BankReconciliationManager` in the future).
    *   `BankReconciliationService`:
        1.  Creates/saves `BankReconciliation` record.
        2.  Updates matched `BankTransaction` records (sets `is_reconciled=True`, `reconciled_date`, `reconciled_bank_reconciliation_id`).
        3.  Updates `BankAccount` (`last_reconciled_date`, `last_reconciled_balance`).
        4.  All in one DB transaction.
6.  **UI Feedback**: Success/error message. UI may refresh.

## 11. Conclusion (Updated)
Version 13.0 significantly enhances SG Bookkeeper with the introduction of CSV bank statement import, a full bank reconciliation module, and an initial dashboard for KPIs. The automatic creation of bank transactions from journal entries further improves data consistency. These features, built upon the established layered architecture, bring the application much closer to a production-ready accounting tool for SMBs. The focus on meticulous implementation and schema integrity ensures a robust foundation for future development, which will critically include comprehensive automated testing and further refinements to existing modules.

---
https://drive.google.com/file/d/11Cv4mFJ5z4I3inVCg8nkncVsAQtuIWrl/view?usp=sharing, https://drive.google.com/file/d/13aFutu059EFwgvQM4JE5LrYT13_62ztj/view?usp=sharing, https://drive.google.com/file/d/150VU2J4NfkYirCIGqQxC5VL9a_s7jyV0/view?usp=sharing, https://drive.google.com/file/d/1Fcdn0EWCauERrISMKReM_r0_nVIQvPiH/view?usp=sharing, https://drive.google.com/file/d/1GWOGYCBqwiPra5MdbwwhwXrV2V-gc4iw/view?usp=sharing, https://drive.google.com/file/d/1IRffneWyqY8ILVvfOu3apYxB15SnhMYD/view?usp=sharing, https://drive.google.com/file/d/1QYQSJ32tb7UYfuT-VHC2vgYYS3Cw_9dz/view?usp=sharing, https://drive.google.com/file/d/1S4zRP59L2Jxru__jXeoTL2TGZ4JN_GOT/view?usp=sharing, https://drive.google.com/file/d/1X5XkobtrDHItY5dTnWRYajA9LTVvZTGy/view?usp=sharing, https://drive.google.com/file/d/1bsb7xdrTRvfFSLOJVv_YBVncejRYeX-p/view?usp=sharing, https://drive.google.com/file/d/1eU9E4v6uT69z91uEABi8xf4-L1_PUKaI/view?usp=sharing, https://drive.google.com/file/d/1fcRRxU4xYdqMgGp58OyuFDOqIcGeOIW_/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221gVm5GnROGWVVYBXkgumxd5puGZ6g5Qs3%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1hF6djKphaR51gqDKE6GLgeBnlWXdKcWU/view?usp=sharing, https://drive.google.com/file/d/1ndjSoP14ry1oCHgOguxNgNWxyP4c18ww/view?usp=sharing, https://drive.google.com/file/d/1zWrsOeANNSTZ51c666H-DxQapeSjXnZY/view?usp=sharing

