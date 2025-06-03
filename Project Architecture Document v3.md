# SG Bookkeeper - Project Architecture Document (v3)

## 1. Introduction

This document outlines the software architecture of the SG Bookkeeper application, reflecting its state after the integration of bank reconciliation features, CSV bank statement import, and related enhancements up to schema version 1.0.4. SG Bookkeeper is a desktop application designed for comprehensive bookkeeping and accounting, tailored for small to medium-sized businesses, with a focus on Singaporean business requirements.

The purpose of this document is to provide an updated, clear understanding of the project's structure, components, their interactions, and overall design principles.

## 2. Project Goals

Based on the codebase, the primary goals of the SG Bookkeeper project are:

*   **Comprehensive Accounting**: Provide robust double-entry bookkeeping, including Chart of Accounts, Journal Entries, Fiscal Period control, and multi-currency support.
*   **Business Operations Management**: Manage Customers, Vendors, Products/Services, Sales/Purchase Invoices, Payments, and Inventory.
*   **Banking & Reconciliation**: Offer features for managing bank accounts, bank transactions, **importing bank statements via CSV**, and performing **bank reconciliations**.
*   **Tax Compliance**: Facilitate GST calculations, F5 return preparation, and potentially income tax and withholding tax.
*   **Financial Reporting**: Generate essential financial statements (Balance Sheet, P&L, Trial Balance, General Ledger) and tax reports.
*   **User-Friendly Interface**: Provide an intuitive desktop GUI.
*   **Data Integrity and Auditability**: Ensure data accuracy with robust audit trails for changes and system actions.
*   **Security**: Manage user access via roles and permissions.
*   **Configuration**: Allow application and company-specific settings.

## 3. Core Technologies

The project leverages:

*   **Python**: >=3.9, <3.13
*   **PySide6 (Qt for Python)**: GUI framework.
*   **SQLAlchemy (asyncio)**: ORM.
*   **asyncpg**: Asynchronous PostgreSQL driver.
*   **PostgreSQL**: Relational database.
*   **Pydantic**: Data validation and DTOs.
*   **asyncio**: Asynchronous operations.
*   **ReportLab**: PDF generation.
*   **Openpyxl**: Excel generation.
*   **python-dateutil**: Advanced date/time utilities.
*   **bcrypt**: Password hashing.
*   **Alembic**: (Implied) Database migrations.
*   **Poetry**: Dependency management.

## 4. Architectural Overview

SG Bookkeeper maintains a multi-layered, modular architecture:

1.  **Presentation Layer (UI)**: `app/ui/` (PySide6 components).
2.  **Application Core Layer**: `app/core/` (Orchestration, central services).
3.  **Business Logic Layer (Managers)**: `app/business_logic/`, `app/accounting/`, `app/tax/`, `app/reporting/` (High-level operations).
4.  **Service Layer (Repositories)**: `app/services/` (Data access abstraction).
5.  **Data Model Layer (ORM)**: `app/models/` (SQLAlchemy models).
6.  **Database Layer**: PostgreSQL (Schema in `scripts/schema.sql`).
7.  **Utility Layer**: `app/utils/`, `app/common/` (Helpers, DTOs, Enums).

### Architecture Diagram (Remains valid at a high level)

```mermaid
graph TD
    A[User Interface (PySide6 - app/ui)] --> B{Application Core (app/core/application_core.py)};
    B --> C[Business Logic Managers (app/business_logic, app/accounting, app/tax, app/reporting)];
    C --> D[Service Layer / Repositories (app/services)];
    D --> E[Data Models (SQLAlchemy ORM - app/models)];
    E --> F[Database (PostgreSQL)];

    B --> G[Security Manager (app/core)];
    B --> H[Config Manager (app/core)];
    B --> I[Database Manager (app/core)];
    I --> F;

    C -- Uses --> J[Utilities (app/utils, app/common)];
    D -- Uses --> J;
    A -- Uses --> J;
    
    subgraph "Presentation Layer"
        A
    end
    
    subgraph "Core & Logic Layer"
        B
        C
        G
        H
        I
    end
    
    subgraph "Data Access Layer"
        D
        E
    end
    
    subgraph "Persistence Layer"
        F
    end
    
    subgraph "Shared Utilities"
        J
    end
```

**Diagram Description:** The fundamental layered structure remains. New features like bank reconciliation are implemented within these existing layers (e.g., new UI widgets in `app/ui/banking`, new service logic in `app/services/business_services.py`, new models in `app/models/business/`).

## 5. Directory Structure and Key Module Updates

*   **`app/ui/banking/`**:
    *   **New**: `bank_reconciliation_widget.py`, `reconciliation_table_model.py`, `csv_import_config_dialog.py`.
    *   Updated: `__init__.py` (exports new components), `bank_transactions_widget.py` (adds CSV import action).
*   **`app/ui/main_window.py`**: Added "Bank Reconciliation" tab.
*   **`app/models/business/`**:
    *   **New**: `bank_reconciliation.py` (defines `BankReconciliation` ORM model).
    *   Updated: `bank_account.py` (adds `last_reconciled_balance`, `reconciliations` relationship), `bank_transaction.py` (adds `reconciled_bank_reconciliation_id`, `reconciliation_instance` relationship, and confirms `is_from_statement`, `raw_statement_data`). `__init__.py` exports `BankReconciliation`.
*   **`app/models/__init__.py`**: Exports `BankReconciliation`.
*   **`app/services/`**:
    *   `__init__.py`: Defines `IBankReconciliationRepository` interface; imports and exports `BankReconciliationService`, `BankReconciliation` model, `BankReconciliationData` DTO. Corrected `AsyncSession` type hints.
    *   `business_services.py`: Implements `BankReconciliationService` and updates `BankTransactionService` (for `is_from_statement_filter` and sorting).
    *   `audit_services.py`: Refinements to change summary formatting and pagination queries.
*   **`app/business_logic/bank_transaction_manager.py`**:
    *   Added `import_bank_statement_csv` method.
    *   Added `get_unreconciled_transactions_for_matching` method.
*   **`app/accounting/journal_entry_manager.py`**:
    *   Constructor updated (removes `SequenceGenerator`).
    *   `create_journal_entry` uses DB function for sequence number.
    *   `post_journal_entry` now auto-creates `BankTransaction` records for relevant JE lines.
*   **`app/core/application_core.py`**:
    *   Instantiates and provides `BankReconciliationService`.
    *   Corrected `JournalEntryManager` instantiation.
    *   Updated `CurrencyService` to `CurrencyRepoService` in `CustomerManager` and `VendorManager` initializations.
*   **`app/utils/pydantic_models.py`**: Added `BankReconciliationBaseData`, `BankReconciliationCreateData`, `BankReconciliationData`.
*   **`resources/`**: Added `import_csv.svg` and updated `resources.qrc`.
*   **`scripts/`**:
    *   `schema.sql`: Reflects schema v1.0.4 changes (new `bank_reconciliations` table, modifications to `bank_accounts` and `bank_transactions`, new trigger `update_bank_account_balance_trigger_func`, audit triggers on banking tables).
    *   `initial_data.sql`: Updated with new permissions (e.g., `VIEW_AUDIT_LOG`, granular banking perms), new default configuration keys, additional system accounts, and updated privilege grants.

## 6. Detailed Component Breakdown (Updates)

### 6.1. `app/core/application_core.py` (Updates)
*   Now initializes and provides `BankReconciliationService`.
*   `JournalEntryManager` instantiation no longer requires `SequenceGenerator` as sequence numbers are primarily fetched via a database function call (`core.get_next_sequence_value`) managed by `DatabaseManager`.
*   Ensures consistent use of `CurrencyRepoService` for currency-related dependencies in managers.

### 6.2. `app/models/` (Updates)
*   **`business.bank_reconciliation.BankReconciliation`**: New ORM model representing a completed bank reconciliation event. Stores statement details, calculated balances, and links to reconciled transactions.
*   **`business.bank_account.BankAccount`**:
    *   Added `last_reconciled_balance: Optional[Decimal]`.
    *   Added `reconciliations: Mapped[List["BankReconciliation"]]` relationship.
*   **`business.bank_transaction.BankTransaction`**:
    *   Added `is_from_statement: Mapped[bool]` (indicates if transaction originated from a CSV import).
    *   Added `raw_statement_data: Mapped[Optional[Dict[str, Any]]]` (stores original CSV row data for imported transactions).
    *   Added `reconciled_bank_reconciliation_id: Mapped[Optional[int]]` (FK to `bank_reconciliations.id`).
    *   Added `reconciliation_instance: Mapped[Optional["BankReconciliation"]]` relationship.

### 6.3. `app/services/` (Updates)
*   **`business_services.BankTransactionService`**:
    *   `get_all_for_bank_account` method enhanced with an `is_from_statement_filter` parameter and refined sorting including `value_date`.
*   **`business_services.BankReconciliationService` (New)**:
    *   Implements `IBankReconciliationRepository`.
    *   **`save_reconciliation_details`**: Key method that transactionally:
        1.  Saves the `BankReconciliation` ORM object.
        2.  Updates all associated `BankTransaction` records (both from statement and system) by setting `is_reconciled=True`, `reconciled_date`, and `reconciled_bank_reconciliation_id`.
        3.  Updates the parent `BankAccount` record with the `last_reconciled_date` and `last_reconciled_balance`.
*   **`audit_services.AuditLogService`**:
    *   Improved `_format_changes_summary` to better represent created/deleted records and handle sensitive/noisy fields more gracefully.
    *   Refined date filtering in pagination queries to be inclusive of the end date.
*   **`__init__.py`**: Added `IBankReconciliationRepository` and registered `BankReconciliationService`. Corrected `AsyncSession` type hints for `save` methods in several repository interfaces (e.g., `IInventoryMovementRepository`, `IBankTransactionRepository`, `IPaymentRepository`).

### 6.4. `app/business_logic/` & `app/accounting/` (Manager Updates)
*   **`accounting.JournalEntryManager`**:
    *   `create_journal_entry`: Now relies on `app_core.db_manager.execute_scalar` calling `core.get_next_sequence_value` for generating `entry_no`.
    *   `post_journal_entry`: When posting a JE, if any line debits/credits a GL account that is flagged as `is_bank_account` and linked to a `business.bank_accounts` record, this method will now automatically create a corresponding `BankTransaction` record. This ensures that system-side bank movements are captured.
*   **`business_logic.BankTransactionManager`**:
    *   **`import_bank_statement_csv`**: New method to handle CSV file uploads. It parses the CSV based on user-provided column mapping and date format, transforms rows into `BankTransaction` objects (marked as `is_from_statement=True` and storing `raw_statement_data`), performs basic duplicate checks against existing statement transactions, and saves valid new transactions. Returns a summary of the import (total, imported, skipped, failed).
    *   **`get_unreconciled_transactions_for_matching`**: New method to fetch two lists of `BankTransactionSummaryData`:
        1.  Unreconciled transactions originating from imported statements (`is_from_statement=True`).
        2.  Unreconciled transactions originating from system actions (e.g., JEs, payments) (`is_from_statement=False`).
        Both lists are filtered up to a given statement end date. This data feeds the bank reconciliation UI.

### 6.5. `app/ui/` (Updates)
*   **`banking.BankReconciliationWidget` (New)**: A major new UI component providing the interface for:
    *   Selecting a bank account and entering statement details (end date, ending balance).
    *   Loading unreconciled statement transactions and system-generated bank transactions.
    *   Displaying these transactions in two separate tables (`ReconciliationTableModel`).
    *   Allowing users to select items from both tables for matching.
    *   Calculating and displaying a reconciliation summary: book balance, adjustments (e.g., interest, charges based on unmatched statement items), outstanding deposits/withdrawals (based on unmatched system items), and the final difference.
    *   Providing an action to "Match Selected" items (which currently just updates the UI calculation; persistence is via "Save Reconciliation").
    *   Providing an action to "Create Journal Entry" for unmatched statement items (pre-fills `JournalEntryDialog`).
    *   Providing an action to "Save Reconciliation" which will persist the reconciliation state.
*   **`banking.ReconciliationTableModel` (New)**: A `QAbstractTableModel` specifically for the bank reconciliation screen, supporting checkable items for selecting transactions to match or process.
*   **`banking.CSVImportConfigDialog` (New)**: A dialog allowing users to:
    *   Select a CSV file.
    *   Specify CSV format options (header row, date format).
    *   Map CSV columns (by name or index) to required transaction fields (date, description, debit/credit/amount, reference, value date).
    *   Specify handling for single vs. dual amount columns.
*   **`banking.BankTransactionsWidget`**:
    *   Added an "Import Statement (CSV)" toolbar action that opens the `CSVImportConfigDialog`.
*   **`main_window.MainWindow`**:
    *   Added a new top-level tab "Bank Reconciliation" which hosts the `BankReconciliationWidget`.

### 6.6. `app/utils/pydantic_models.py` (Updates)
*   Added new DTOs for bank reconciliation:
    *   `BankReconciliationBaseData`: Core fields for a reconciliation.
    *   `BankReconciliationCreateData`: Includes `UserAuditData` for creating a reconciliation.
    *   `BankReconciliationData`: Represents a full reconciliation record, typically for retrieval.

## 7. Data Model and Database (Updates based on v1.0.4)

*   **New Table: `business.bank_reconciliations`**:
    *   `id`, `bank_account_id` (FK), `statement_date`, `statement_ending_balance`, `calculated_book_balance`, `reconciled_difference`, `reconciliation_date`, `notes`, `created_at`, `updated_at`, `created_by_user_id` (FK).
    *   Unique constraint on `(bank_account_id, statement_date)`.
*   **Table `business.bank_accounts` Changes**:
    *   Added `last_reconciled_balance NUMERIC(15,2) NULL`: Stores the bank statement's ending balance from the last completed reconciliation for this account.
*   **Table `business.bank_transactions` Changes**:
    *   Added `reconciled_bank_reconciliation_id INT NULL`: FK to `business.bank_reconciliations.id`, linking a transaction to the specific reconciliation event that cleared it.
    *   (Existing from v1.0.3) `is_from_statement BOOLEAN NOT NULL DEFAULT FALSE`: Flags transactions imported from CSV statements.
    *   (Existing from v1.0.3) `raw_statement_data JSONB NULL`: Stores the original imported row data for statement transactions.
*   **New Trigger: `business.update_bank_account_balance_trigger_func()`**:
    *   Attached to `business.bank_transactions` (AFTER INSERT, UPDATE, DELETE).
    *   Automatically updates `business.bank_accounts.current_balance` when bank transactions are created, modified, or deleted. This ensures the `current_balance` in `bank_accounts` is always in sync with its underlying transactions.
*   **Audit Triggers**: The `audit.log_data_change_trigger_func()` is now also applied to `business.bank_accounts` and `business.bank_transactions`.
*   **Initial Data (`scripts/initial_data.sql` updates)**:
    *   Added new permissions: `VIEW_AUDIT_LOG`, `BANK_ACCOUNT_VIEW`, `BANK_ACCOUNT_MANAGE`, `BANK_TRANSACTION_VIEW`, `BANK_TRANSACTION_MANAGE`, `BANK_RECONCILE`, `BANK_STATEMENT_IMPORT`.
    *   Added new default configuration keys for system accounts: `SysAcc_DefaultCash`, `SysAcc_DefaultInventoryAsset`, `SysAcc_DefaultCOGS`, `SysAcc_GSTControl`.
    *   Ensured system accounts like `SYS-GST-CONTROL`, `Cash on Hand`, `Inventory Asset Control` are created.
    *   Updated role privileges, including for `audit` schema sequences.

## 8. Configuration and Initialization (Updates)

*   **`scripts/initial_data.sql`**: Now includes new default configuration keys (e.g., `SysAcc_DefaultCash`, `SysAcc_GSTControl`) and permissions related to new banking features and audit logs.
*   **`app/core/application_core.py`**: Service and manager instantiations updated to reflect new dependencies and components like `BankReconciliationService` and changes to `JournalEntryManager`.

## 9. Key Architectural Patterns & Considerations (Updates)

*   **Automated Record Creation**: The system now demonstrates more instances of automated record creation based on other processes:
    *   `JournalEntryManager.post_journal_entry()` creates `BankTransaction` records.
    *   `BankTransactionManager.import_bank_statement_csv()` creates `BankTransaction` records from external data.
*   **Database Triggers for Data Integrity**: The new `update_bank_account_balance_trigger_func()` enhances data integrity by ensuring `bank_accounts.current_balance` is automatically maintained.

## 10. Data Flow (New Example: Bank Reconciliation)

1.  **UI (`BankReconciliationWidget`)**:
    *   User selects a Bank Account, enters Statement Date and Statement Ending Balance.
    *   Clicks "Load / Refresh Transactions".
2.  **Manager (`BankTransactionManager`)**: `get_unreconciled_transactions_for_matching(bank_account_id, statement_date)` is called.
3.  **Service (`BankTransactionService`)**: Fetches two lists via `get_all_for_bank_account`:
    *   Unreconciled transactions marked `is_from_statement=True`.
    *   Unreconciled transactions marked `is_from_statement=False` (system entries).
4.  **UI**: Populates two tables with these transactions. Calculates and displays initial reconciliation summary.
5.  **User Interaction**: User selects items from both tables to match (e.g., a statement deposit against a system deposit JE).
    *   UI updates summary figures based on *unchecked* items.
    *   If user clicks "Match Selected":
        *   UI validates if selected amounts match.
        *   If matched, items are effectively "cleared" for this session (e.g., model might uncheck them, and they are excluded from summary recalculation *as if* they were reconciled).
    *   If user clicks "Create Journal Entry" for an unmatched statement item (e.g., bank charge):
        *   `JournalEntryDialog` is pre-filled with bank line details.
        *   User completes and posts the JE.
        *   `JournalEntryManager.post_journal_entry()` creates the JE and a corresponding system `BankTransaction`.
        *   List is refreshed; the new system transaction appears, and the statement item can now be matched.
6.  **Saving Reconciliation (`BankReconciliationWidget` -> `BankReconciliationManager` (conceptual, logic in service) -> `BankReconciliationService`)**:
    *   User clicks "Save Reconciliation" (enabled when difference is zero).
    *   A `BankReconciliationCreateData` DTO is assembled.
    *   `BankReconciliationService.save_reconciliation_details()` is called:
        *   Creates a new `BankReconciliation` record.
        *   Updates all `BankTransaction` records that were "cleared" (i.e., successfully matched or newly created and matched during the session) by setting `is_reconciled=True`, `reconciled_date`, and `reconciled_bank_reconciliation_id`.
        *   Updates the `BankAccount` with `last_reconciled_date` and `last_reconciled_balance`.
        *   All these operations occur within a single database transaction.
7.  **UI**: Confirms save and potentially clears reconciled items from view or reloads.

## 11. Conclusion (Updated)

The SG Bookkeeper project has evolved with significant enhancements, notably in the banking module with the introduction of CSV bank statement import and a comprehensive bank reconciliation feature. The architecture continues to support these additions effectively by leveraging its layered design. New UI components, service logic, data models, and database structures have been integrated while maintaining the core principles of modularity, asynchronous processing, and data integrity. The increased use of database triggers and automated record creation (like JEs creating Bank Transactions) further strengthens data consistency. The project remains a robust platform for small business accounting.

---
https://drive.google.com/file/d/11Cv4mFJ5z4I3inVCg8nkncVsAQtuIWrl/view?usp=sharing, https://drive.google.com/file/d/13aFutu059EFwgvQM4JE5LrYT13_62ztj/view?usp=sharing, https://drive.google.com/file/d/150VU2J4NfkYirCIGqQxC5VL9a_s7jyV0/view?usp=sharing, https://drive.google.com/file/d/1Fcdn0EWCauERrISMKReM_r0_nVIQvPiH/view?usp=sharing, https://drive.google.com/file/d/1IRffneWyqY8ILVvfOu3apYxB15SnhMYD/view?usp=sharing, https://drive.google.com/file/d/1S4zRP59L2Jxru__jXeoTL2TGZ4JN_GOT/view?usp=sharing, https://drive.google.com/file/d/1X5XkobtrDHItY5dTnWRYajA9LTVvZTGy/view?usp=sharing, https://drive.google.com/file/d/1bsb7xdrTRvfFSLOJVv_YBVncejRYeX-p/view?usp=sharing, https://drive.google.com/file/d/1eU9E4v6uT69z91uEABi8xf4-L1_PUKaI/view?usp=sharing, https://drive.google.com/file/d/1fcRRxU4xYdqMgGp58OyuFDOqIcGeOIW_/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221gVm5GnROGWVVYBXkgumxd5puGZ6g5Qs3%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1ndjSoP14ry1oCHgOguxNgNWxyP4c18ww/view?usp=sharing, https://drive.google.com/file/d/1zWrsOeANNSTZ51c666H-DxQapeSjXnZY/view?usp=sharing

