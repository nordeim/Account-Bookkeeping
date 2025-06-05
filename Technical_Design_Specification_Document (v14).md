# Technical Design Specification Document: SG Bookkeeper (v14)

**Version:** 14.0
**Date:** 2025-06-04

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version 14.0, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities up to schema version 1.0.4. This version specifically details the implementation of:
*   **Bank Reconciliation Module**: Comprehensive UI and backend logic for reconciling bank statements with system bank transactions, including matching, creating adjustment journal entries, and saving reconciliation status.
*   **CSV Bank Statement Import**: Functionality to import bank transactions from CSV files with configurable column mapping.
*   **Automated Bank Transaction Creation from Journal Entries**: Posting a journal entry that affects a bank-linked GL account now automatically generates a corresponding system bank transaction.
*   **Dashboard KPIs (Initial Implementation)**: Display of key financial indicators like YTD P&L figures, cash balance, and AR/AP totals.
*   **Database Enhancements**: Introduction of the `business.bank_reconciliations` table, new fields in `bank_accounts` and `bank_transactions`, and a database trigger for automatic bank balance updates.
These build upon previously documented features like Full Payments Module (Phase 1), Audit Log UI, enhanced GST F5 Reporting, full Sales/Purchase Invoicing, User/Role Management, Customer/Vendor/Product Management, and core Financial Reporting. This document serves as a comprehensive guide for ongoing development, feature enhancement, testing, and maintenance.

### 1.2 Scope
This TDS covers the following aspects of the SG Bookkeeper application:
-   System Architecture: UI, business logic, data access layers, and asynchronous processing.
-   Database Schema: Details and organization as defined in `scripts/schema.sql` (reflecting v1.0.4 changes), including new tables, columns, and triggers for bank reconciliation.
-   Key UI Implementation Patterns: `PySide6` interactions with the asynchronous backend, DTO usage, including new banking and dashboard features.
-   Core Business Logic: Component structures and interactions for implemented modules, including bank reconciliation, CSV import, and KPI generation.
-   Data Models (SQLAlchemy ORM) and Data Transfer Objects (Pydantic DTOs), including those related to new features.
-   Security Implementation: Authentication, Role-Based Access Control (RBAC), and audit mechanisms including UI.
-   Deployment and Initialization procedures, including updated `initial_data.sql` with new permissions/configs.
-   Current Implementation Status: Highlighting the features implemented up to this version.

### 1.3 Intended Audience
-   Software Developers: For implementation, feature development, and understanding system design.
-   QA Engineers: For comprehending system behavior, designing effective test cases, and validation.
-   System Administrators: For deployment strategies, database setup, and maintenance.
-   Technical Project Managers: For project oversight, planning, and resource allocation.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application engineered with Python, utilizing PySide6 for its graphical user interface and PostgreSQL for robust data storage. It is designed to provide comprehensive accounting solutions for Singaporean Small to Medium-sized Businesses (SMBs). Key features include a full double-entry bookkeeping system, Singapore-specific GST management (including F5 return preparation with detailed export), interactive financial reporting, modules for managing essential business operations (Customers, Vendors, Products/Services, full Sales & Purchase Invoicing lifecycle, Payments with allocations, Bank Account management with manual transaction entry, **CSV bank statement import, and a full bank reconciliation module**), **an initial dashboard displaying key performance indicators (KPIs)**, and comprehensive system administration for Users, Roles, Permissions, and Audit Log viewing. The application emphasizes data integrity, compliance with local accounting standards, user-friendliness, and robust auditability. Core data structures are defined in `scripts/schema.sql`, and initial seeding is performed by `scripts/initial_data.sql`.

### 1.5 Current Implementation Status
As of version 13.0 (reflecting schema v1.0.4), the following key features are implemented:
*   **Core Accounting**: Chart of Accounts (CRUD UI), General Journal (CRUD UI, Posting, Reversal, Journal Type filter), Fiscal Year/Period Management (UI in Settings).
*   **Tax Management**: GST F5 Return data preparation and finalization (UI and backend logic), enhanced Excel export with transaction breakdown, `TaxCalculator` for line item tax.
*   **Business Operations**:
    *   Customer Management: Full CRUD and listing UI.
    *   Vendor Management: Full CRUD and listing UI.
    *   Product/Service Management: Full CRUD and listing UI for Inventory, Non-Inventory, and Service types.
    *   Sales Invoicing: Full lifecycle - Draft CRUD, List View, Posting with financial JE & inventory JE (WAC) creation, "Save & Approve" in dialog, advanced product search.
    *   Purchase Invoicing: Full lifecycle - Draft CRUD, List View, Posting with financial JE & inventory JE (WAC) creation, Dialog with advanced product search.
    *   Payments: Full UI for Customer Receipts and Vendor Payments via `PaymentDialog` including invoice allocation. `PaymentsWidget` for listing and filtering. Backend `PaymentManager` handles creation, validation, JE posting, and invoice updates.
*   **Banking (Original Features from v12.0)**:
    *   Bank Account Management: Full CRUD UI (`BankAccountsWidget`, `BankAccountDialog`) and backend (`BankAccountManager`, `BankAccountService`).
    *   Basic Bank Transaction Entry: UI (`BankTransactionDialog` launched from `BankTransactionsWidget`) and backend (`BankTransactionManager`, `BankTransactionService`) for manual entry of deposits, withdrawals, fees, etc. `BankingWidget` provides a master-detail view.
*   **Reporting (Original Features from v12.0)**:
    *   Balance Sheet & Profit/Loss: On-screen tree view, enhanced PDF/Excel export (custom formatting, headers, footers), UI options for comparative periods and zero-balance accounts.
    *   Trial Balance & General Ledger: On-screen table view, enhanced PDF/Excel export. GL reports support filtering by up to two dimensions.
*   **System Administration (Original Features from v12.0)**:
    *   Full User and Role Management UI in Settings.
    *   Backend `SecurityManager` supports these operations.
    *   Audit Log UI: Integrated into Settings, providing views for Action Log and Data Change History with filtering capabilities. Backend `AuditLogService` supports data retrieval. Minor improvements to change summary formatting and query logic have been made.
*   **New/Enhanced Banking & Dashboard Features (v14.0)**:
    *   **Bank Reconciliation**: Full UI (`BankReconciliationWidget`) and backend logic (`BankReconciliationService`, updates to `BankTransactionManager`) for comparing bank statement items with system transactions, matching items, calculating discrepancies, facilitating adjustment JEs, and saving the reconciliation state.
    *   **CSV Bank Statement Import**: UI (`CSVImportConfigDialog`) and backend (`BankTransactionManager.import_bank_statement_csv`) for importing transactions from CSV files.
    *   **Automatic Bank Transactions from JEs**: `JournalEntryManager.post_journal_entry` now creates `BankTransaction` records when a JE impacts a bank-linked GL account.
    *   **Dashboard KPIs**: Initial implementation in `DashboardWidget` displaying core YTD P&L, Cash, AR/AP figures fetched via `DashboardManager`.
*   **Database**: Schema updated to v1.0.4 with `business.bank_reconciliations` table, new fields in `bank_accounts` and `bank_transactions` (e.g., `last_reconciled_balance`, `reconciled_bank_reconciliation_id`, `is_from_statement`, `raw_statement_data`), and a trigger for `bank_accounts.current_balance` updates. `initial_data.sql` includes new banking permissions and config keys. `db_init.py` script for setup.
*   **Architecture**: Layered architecture with asynchronous processing for UI responsiveness.

## 2. System Architecture

### 2.1 High-Level Architecture

The application follows a layered architecture to promote separation of concerns and maintainability:

```
+-----------------------------------------------------------------+
|                       Presentation Layer                        |
| (PySide6: MainWindow, Module Widgets, Dialogs, TableModels)   |
| Handles User Interaction, Displays Data, Qt Signals/Slots       |
+-----------------------------------------------------------------+
      ^                         | (schedule_task_from_qt for async calls)
      | (UI Events, Data DTOs)  | (Results/Updates via QMetaObject.invokeMethod)
      v                         v
+-----------------------------------------------------------------+
|                     Business Logic Layer                        |
| (ApplicationCore, Managers [e.g., SalesInvoiceManager,         |
|  BankTransactionManager, PaymentManager, DashboardManager, etc.])|
| Encapsulates Business Rules, Validation, Orchestrates Services  |
+-----------------------------------------------------------------+
      ^                         | (Service Calls, ORM Objects/DTOs)
      | (Service Results)       | (SQLAlchemy Async Operations)
      v                         v
+-----------------------------------------------------------------+
|                       Data Access Layer                         |
| (DatabaseManager, Services [e.g., SalesInvoiceService,         |
|  PaymentService, BankReconciliationService, AuditLogService], SQLAlchemy Models)|
| Abstracts Database Interactions, Repository Pattern             |
+-----------------------------------------------------------------+
                                | (Asyncpg DB Driver)
                                v
+-----------------------------------------------------------------+
|                          Database Layer                         |
| (PostgreSQL: Schemas [core, accounting, business, audit],      |
|  Tables, Views, Functions, Triggers defined in schema.sql)      |
+-----------------------------------------------------------------+
```

### 2.2 Component Architecture

#### 2.2.1 Core Components (`app/core/`)
-   **`Application` (`app/main.py`)**: Subclass of `QApplication`. Manages the Qt event loop and bridges to a dedicated `asyncio` event loop running in a separate thread for background tasks. Handles splash screen and initial application setup.
-   **`ApplicationCore` (`app/core/application_core.py`)**:
    -   The central orchestrator. Initializes and provides access to all services and managers (e.g., `SecurityManager`, `SalesInvoiceManager`, `PurchaseInvoiceManager`, `PaymentManager`, `BankAccountManager`, `BankTransactionManager`, `JournalEntryManager`). Manages application startup and shutdown routines.
    -   Now initializes and provides access to `PaymentService`, `BankAccountService`, `BankTransactionService`, `AuditLogService`, `BankReconciliationService`, and `DashboardManager`.
    -   `JournalEntryManager` instantiation corrected (no longer takes `SequenceGenerator`).
    -   Corrected `CurrencyRepoService` injection for `CustomerManager` and `VendorManager`.
-   **`ConfigManager` (`app/core/config_manager.py`)**: Loads and manages application settings from `config.ini` located in a platform-specific user configuration directory.
-   **`DatabaseManager` (`app/core/database_manager.py`)**: Manages asynchronous PostgreSQL database connections using SQLAlchemy's async engine and an `asyncpg` connection pool. Handles session creation and management, including setting the `app.current_user_id` session variable for database audit triggers.
-   **`SecurityManager` (`app/core/security_manager.py`)**:
    -   Handles user authentication (password hashing with `bcrypt` and verification).
    -   Manages authorization through a Role-Based Access Control (RBAC) system, checking permissions (`has_permission()`).
    -   Provides backend logic for User, Role, and Permission CRUD operations, directly interacting with ORM models.
    -   Tracks the `current_user` for the application session.
-   **`ModuleManager` (`app/core/module_manager.py`)**: A conceptual component for potential future dynamic loading of large application modules. Currently, modules are statically imported.

#### 2.2.2 Asynchronous Task Management (`app/main.py`)
-   A dedicated Python `threading.Thread` (`_ASYNC_LOOP_THREAD`) runs a persistent `asyncio` event loop (`_ASYNC_LOOP`).
-   The `schedule_task_from_qt(coroutine)` utility function safely schedules coroutines (typically manager or service methods initiated by UI actions) from the main Qt GUI thread onto the dedicated asyncio loop thread using `asyncio.run_coroutine_threadsafe`.
-   UI updates resulting from these asynchronous operations are marshaled back to the Qt main thread using `QMetaObject.invokeMethod` with `Qt.ConnectionType.QueuedConnection`. Data is often serialized (e.g., to JSON) for thread-safe transfer.

#### 2.2.3 Services (Data Access Layer - `app/services/`)
Services implement the repository pattern, abstracting direct ORM query logic for data persistence and retrieval. Key services include:
-   **Core Services (`core_services.py`)**: `SequenceService`, `CompanySettingsService`, `ConfigurationService`.
-   **Accounting Services (`accounting_services.py`, `account_service.py`, etc.)**: `AccountService`, `JournalService`, `FiscalPeriodService`, `FiscalYearService`, `AccountTypeService`, `CurrencyService`, `ExchangeRateService`.
-   **Tax Services (`tax_service.py`)**: `TaxCodeService`, `GSTReturnService`.
-   **Business Services (`business_services.py`)**:
    *   `CustomerService`, `VendorService`, `ProductService`, `SalesInvoiceService`, `PurchaseInvoiceService`.
    *   `BankAccountService`: Handles CRUD and querying for `BankAccount` entities.
    *   `BankTransactionService`: Handles CRUD and querying for `BankTransaction` entities, especially for listing within a bank account and supporting reconciliation.
    *   `PaymentService`: Handles CRUD for `Payment` and `PaymentAllocation` entities, ensuring transactional integrity for a payment and its allocations.
    *   `BankReconciliationService` (New): Handles persistence for `BankReconciliation` records and updates related `BankTransaction` and `BankAccount` statuses.
-   **Audit Services (`audit_services.py`)**:
    *   `AuditLogService`: Fetches data from `audit.audit_log` and `audit.data_change_history` with filtering and pagination for UI display.

#### 2.2.4 Managers (Business Logic Layer - `app/accounting/`, `app/tax/`, `app/business_logic/`, `app/reporting/`)
Managers encapsulate complex business workflows, validation logic, and coordinate operations between multiple services and DTOs.
-   **Accounting Managers**: `ChartOfAccountsManager`, `FiscalPeriodManager`, `CurrencyManager`.
    *   `JournalEntryManager`: Handles creation, validation, posting, reversal. `create_journal_entry` uses DB function for `entry_no`. `post_journal_entry` now auto-creates `BankTransaction` records if a JE line affects a bank-linked GL account.
-   **Tax Managers**: `GSTManager`, `TaxCalculator`. (`IncomeTaxManager`, `WithholdingTaxManager` are stubs).
    *   `GSTManager`: `prepare_gst_return_data` method collects detailed transaction breakdowns for each relevant GST F5 box.
-   **Business Logic Managers**: `CustomerManager`, `VendorManager`, `ProductManager`, `SalesInvoiceManager`, `PurchaseInvoiceManager`.
    *   `SalesInvoiceManager`: Handles full lifecycle for sales invoices including draft CRUD and posting with financial JE & inventory JE creation.
    *   `PurchaseInvoiceManager`: Handles full lifecycle for purchase invoices, including validation, calculations, and posting logic.
    *   `BankAccountManager`: Manages CRUD operations for bank accounts, including validation.
    *   `BankTransactionManager`:
        *   Manages creation of manual bank transactions and listing transactions.
        *   New `import_bank_statement_csv` method for CSV import.
        *   New `get_unreconciled_transactions_for_matching` method for bank reconciliation UI.
    *   `PaymentManager`: Orchestrates the creation of payments/receipts. Validates payment data and allocations, generates payment numbers, creates `Payment` and `PaymentAllocation` records, coordinates `JournalEntryManager` for posting financial JEs, and updates invoice balances.
-   **Reporting Managers**: `FinancialStatementGenerator`, `ReportEngine`.
    *   `DashboardManager` (New, `app/reporting/dashboard_manager.py`):
        *   `get_dashboard_kpis()`: Fetches data from various services (`FinancialStatementGenerator`, `BankAccountService`, `CustomerService`, `VendorService`, `FiscalYearService`, `CompanySettingsService`) to compute and return KPIs in a `DashboardKPIData` DTO. Handles determination of current fiscal year and base currency.

#### 2.2.5 User Interface (Presentation Layer - `app/ui/`)
-   **`MainWindow` (`app/ui/main_window.py`)**: The main application window, using a `QTabWidget` to host different functional modules. It includes menus, a toolbar, and a status bar.
    *   Includes a "Payments" tab.
    *   A new top-level tab "Bank Reconciliation" is added, hosting the `BankReconciliationWidget`. The "Banking" tab name (hosting `BankingWidget`) may be referred to as "Banking C.R.U.D" or similar to differentiate its focus on basic management.
-   **Module Widgets**: Each tab in `MainWindow` hosts a primary widget for a module:
    *   `DashboardWidget` (`app/ui/dashboard/DashboardWidget`): Updated from placeholder to display KPIs (revenue, expenses, net profit, cash, AR/AP) fetched via `DashboardManager`. Includes a refresh mechanism.
    *   `AccountingWidget` (hosts `ChartOfAccountsWidget`, `JournalEntriesWidget`)
    *   `SalesInvoicesWidget`, `PurchaseInvoicesWidget` (list views)
    *   `CustomersWidget`, `VendorsWidget`, `ProductsWidget` (list views)
    *   `ReportsWidget` (UI for GST F5 and Financial Statements)
    *   `BankingWidget`: Re-architected in v12.0 to use `QSplitter` for master-detail: `BankAccountsWidget` (master) and `BankTransactionsWidget` (detail).
    *   `BankAccountsWidget`: For listing bank accounts with CRUD actions.
    *   `BankTransactionsWidget`: Displays transactions for a selected bank account. Allows adding manual transactions. Includes filtering. Added "Import Statement (CSV)" action which opens `CSVImportConfigDialog`.
    *   `BankReconciliationWidget` (New, `app/ui/banking/bank_reconciliation_widget.py`): Main UI for bank reconciliation, featuring setup controls, a summary section, and two tables for matching statement items against system transactions. Includes actions for matching, creating adjustment JEs, and saving the reconciliation.
    *   `PaymentsWidget`: For listing customer/vendor payments, with filtering and creation action.
    *   `SettingsWidget`: Hosts sub-tabs for Company Info, Fiscal Years, User Management, Role Management, and an "Audit Logs" sub-tab hosting `AuditLogWidget`.
    *   `AuditLogWidget`: With two sub-tabs ("Action Log", "Data Change History") for viewing and filtering audit records.
-   **Detail Widgets & Dialogs**: For data entry/editing (e.g., `AccountDialog`, `SalesInvoiceDialog`, `UserDialog`).
    *   `BankAccountDialog`: For creating/editing bank accounts.
    *   `BankTransactionDialog`: For manual entry of bank transactions.
    *   `PaymentDialog`: For recording payments/receipts, with invoice allocation table.
    *   `CSVImportConfigDialog` (New, `app/ui/banking/csv_import_config_dialog.py`): Dialog for configuring CSV bank statement imports, allowing file selection and column mapping.
-   **Table Models**: Subclasses of `QAbstractTableModel` provide data to `QTableView`s.
    *   `SalesInvoiceTableModel`, `PurchaseInvoiceTableModel`, `BankAccountTableModel`, `BankTransactionTableModel`, `PaymentTableModel`, `AuditLogTableModel`, `DataChangeHistoryTableModel`.
    *   `ReconciliationTableModel` (New, `app/ui/banking/reconciliation_table_model.py`): Table model for the reconciliation tables in `BankReconciliationWidget`, supporting checkable items.

### 2.3 Technology Stack
-   **Programming Language**: Python 3.9+ (actively tested up to 3.12).
-   **UI Framework**: PySide6 6.9.0+.
-   **Database**: PostgreSQL 14+.
-   **ORM**: SQLAlchemy 2.0+ (utilizing asynchronous ORM features).
-   **Asynchronous DB Driver**: `asyncpg` for PostgreSQL.
-   **Data Validation (DTOs)**: Pydantic V2 (with `email-validator` for email string validation).
-   **Password Hashing**: `bcrypt`.
-   **Reporting Libraries**: `reportlab` for PDF generation, `openpyxl` for Excel generation.
-   **Dependency Management**: Poetry.
-   **Date/Time Utilities**: `python-dateutil`.

### 2.4 Design Patterns
The application incorporates several design patterns to enhance structure, maintainability, and scalability:
-   **Layered Architecture**: As described in Section 2.1.
-   **Model-View-Controller (MVC) / Model-View-Presenter (MVP)**: Broadly guides the separation of UI (View), data (Model - SQLAlchemy ORM, Pydantic DTOs), and application logic (Controller/Presenter - Managers, UI widget event handlers).
-   **Repository Pattern**: Implemented by Service classes in the Data Access Layer. They provide an abstraction for data access operations, decoupling business logic from direct ORM/database query details.
-   **Data Transfer Object (DTO)**: Pydantic models (`app/utils/pydantic_models.py`) are used for structured data exchange between the UI layer and the Business Logic Layer, providing validation and clear data contracts.
-   **Result Object Pattern**: A custom `Result` class (`app/utils/result.py`) is used by manager and service methods to return operation outcomes, clearly indicating success or failure and providing error messages or a value.
-   **Observer Pattern**: Qt's Signals and Slots mechanism is extensively used for communication between UI components and for handling UI updates in response to asynchronous operations.
-   **Dependency Injection (Conceptual)**: `ApplicationCore` acts as a central point for instantiating and providing services and managers, effectively injecting dependencies into components that require them.
-   **Singleton (Conceptual for `ApplicationCore`)**: `ApplicationCore` is instantiated once and accessed globally within the application context, typical for managing core services.

## 3. Data Architecture (Updates based on Schema v1.0.4)

### 3.1 Database Schema Overview
The PostgreSQL database schema is foundational and defined in `scripts/schema.sql` (v1.0.4). It is organized into four distinct schemas: `core`, `accounting`, `business`, and `audit`.
-   **`core`**: System-level tables (`users`, `roles`, `permissions`, `company_settings`, `sequences`, etc.).
-   **`accounting`**: Core accounting tables (`accounts`, `journal_entries`, `fiscal_years`, `tax_codes`, etc.).
-   **`business`**: Operational data tables (`customers`, `vendors`, `products`, `sales_invoices`, `purchase_invoices`, `payments`, etc.). Key updates for v1.0.4:
    *   **New Table: `business.bank_reconciliations`**: Stores completed reconciliation summaries.
        *   Columns: `id` (PK), `bank_account_id` (FK to `bank_accounts.id`), `statement_date` (NOT NULL), `statement_ending_balance` (NOT NULL), `calculated_book_balance` (NOT NULL), `reconciled_difference` (NOT NULL), `reconciliation_date` (DEFAULT CURRENT_TIMESTAMP), `notes`, `created_by_user_id` (FK), audit timestamps.
        *   Unique constraint: `(bank_account_id, statement_date)`.
    *   **Table `business.bank_accounts`**:
        *   Added `current_balance NUMERIC(15,2) DEFAULT 0.00` (managed by trigger).
        *   Added `last_reconciled_date DATE NULL`.
        *   Added `last_reconciled_balance NUMERIC(15,2) NULL`.
    *   **Table `business.bank_transactions`**:
        *   Added `is_from_statement BOOLEAN NOT NULL DEFAULT FALSE` (for CSV imports).
        *   Added `raw_statement_data JSONB NULL` (stores original CSV row data).
        *   Added `reconciled_bank_reconciliation_id INT NULL` (FK to `bank_reconciliations.id`).
        *   Existing fields `is_reconciled BOOLEAN DEFAULT FALSE NOT NULL` and `reconciled_date DATE NULL` are used by the reconciliation process.
-   **`audit`**: Tables for tracking changes (`audit_log`, `data_change_history`), populated by database triggers.
-   **Triggers**:
    *   New trigger `trg_update_bank_balance` on `business.bank_transactions` (AFTER INSERT, UPDATE, DELETE) calls `business.update_bank_account_balance_trigger_func()` to automatically update `business.bank_accounts.current_balance`.
    *   Audit triggers (`audit.log_data_change_trigger_func`) extended to `business.bank_accounts` and `business.bank_transactions`.
-   The schema enforces data integrity through keys, constraints, and indexes.

### 3.2 SQLAlchemy ORM Models (`app/models/`)
SQLAlchemy ORM models interface with database tables.
-   Organized into subdirectories mirroring schema structure.
-   Inherit from `Base` and may use `TimestampMixin`. Include `created_by_user_id`, `updated_by_user_id`.
-   Relationships use `relationship()` with `back_populates`. Mapped ORM style with type hints.
-   **`app/models/business/bank_reconciliation.py`**: New `BankReconciliation` ORM model.
-   **`app/models/business/bank_account.py`**: `BankAccount` model updated with `last_reconciled_balance`, `last_reconciled_date`, `current_balance`, and `reconciliations` relationship.
-   **`app/models/business/bank_transaction.py`**: `BankTransaction` model updated with `reconciled_bank_reconciliation_id`, `is_from_statement`, `raw_statement_data`, and `reconciliation_instance` relationship.
-   `app/models/business/payment.py`: `Payment` and `PaymentAllocation` models are utilized.
-   `app/models/audit/audit_log.py`, `app/models/audit/data_change_history.py`: Map to audit tables.

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
Pydantic models for data validation and transfer between layers.
-   Standard DTOs sets: `BaseData`, `CreateData`, `UpdateData`, `Data`, `SummaryData`.
-   Include validations, constraints, custom validators. Enums from `app/common/enums.py`.
-   **New/Updated DTOs for v14.0**:
    *   `BankReconciliationBaseData`, `BankReconciliationCreateData`, `BankReconciliationData`.
    *   `DashboardKPIData`: For structuring KPI values (e.g., `ytd_revenue`, `total_cash_balance`, `total_accounts_receivable`, `total_accounts_payable`, `net_profit_loss`).
-   **Existing DTOs (relevant examples from v12.0, confirmed updates where noted)**:
    *   Bank Account DTOs: `BankAccountBaseData`, `BankAccountCreateData`, etc.
    *   Bank Transaction DTOs: `BankTransactionBaseData`, `BankTransactionCreateData`, etc.
    *   Payment DTOs: `PaymentAllocationBaseData`, `PaymentBaseData`, `PaymentCreateData`, etc.
    *   Audit Log DTOs: `AuditLogEntryData`, `DataChangeHistoryEntryData`.
    *   GST DTOs: `GSTTransactionLineDetail` (added for detailed F5 export), `GSTReturnData` (updated with `detailed_breakdown`).
    *   `SalesInvoiceSummaryData` and `PurchaseInvoiceSummaryData` (updated to include `currency_code`).

### 3.4 Data Access Layer Interfaces (Services - `app/services/__init__.py`)
While a generic `IRepository` interface is defined, individual service classes often directly implement required data access methods for their ORM model(s).
-   Examples: `IAccountRepository`, `ISalesInvoiceRepository`, `IPurchaseInvoiceRepository`, `IBankAccountRepository`, `IBankTransactionRepository`, `IPaymentRepository`, `IAuditLogRepository`, `IDataChangeHistoryRepository`.
-   New services like `BankReconciliationService` follow this pattern, providing specific methods like `save_reconciliation_details`.

## 4. Module and Component Specifications

### 4.1 Core Accounting Module (`app/accounting/`, `app/ui/accounting/`)
-   **Chart of Accounts**: Hierarchical account management.
    -   Manager: `ChartOfAccountsManager`. Service: `AccountService`. UI: `ChartOfAccountsWidget`, `AccountDialog`.
-   **Journal Entries**: Manual journal entry creation and management.
    -   Manager: `JournalEntryManager`. Service: `JournalService`. UI: `JournalEntriesWidget`, `JournalEntryDialog`.
    *   `JournalEntryManager.post_journal_entry` now auto-creates `BankTransaction` if a bank-linked GL account is affected.
-   **Fiscal Period Management**: Setup and control of fiscal years/periods.
    -   Manager: `FiscalPeriodManager`. Services: `FiscalYearService`, `FiscalPeriodService`. UI: In `SettingsWidget`, `FiscalYearDialog`.

### 4.2 Tax Management Module (`app/tax/`, `app/ui/reports/`)
-   **GST Management**:
    *   Manager: `GSTManager` (prepares `GSTReturnData` DTO including `detailed_breakdown` of `GSTTransactionLineDetail` objects for F5 boxes, saves draft, finalizes with settlement JE).
    *   Service: `TaxCodeService`, `GSTReturnService`.
    *   UI: `ReportsWidget` (GST F5 tab) includes "Export Details (Excel)" for detailed breakdown.
-   **Tax Calculation**: `TaxCalculator` service (`calculate_line_tax`) used by invoice managers.

### 4.3 Business Operations Modules (`app/business_logic/`, `app/ui/.../`)
-   **Customer, Vendor, Product/Service Management**: Full CRUD and list views.
    -   Managers: `CustomerManager`, `VendorManager`, `ProductManager`. Services: `CustomerService`, `VendorService`, `ProductService`. UI: `CustomersWidget`, `VendorsWidget`, `ProductsWidget`, respective dialogs.
-   **Sales Invoicing Module**: Full lifecycle.
    -   Manager: `SalesInvoiceManager` (validation, calculations, draft CRUD, posting with financial & inventory JEs). Service: `SalesInvoiceService`. UI: `SalesInvoicesWidget`, `SalesInvoiceDialog`.
-   **Purchase Invoicing Module**: Full lifecycle.
    -   Manager: `PurchaseInvoiceManager` (validation, calculations, draft CRUD, posting with financial & inventory JEs). Service: `PurchaseInvoiceService`. UI: `PurchaseInvoicesWidget`, `PurchaseInvoiceDialog`.

### 4.4 System Administration Modules (`app/core/security_manager.py`, `app/ui/settings/`, `app/ui/audit/`)
-   **User Management**:
    -   Manager: `SecurityManager`. UI: `UserManagementWidget`, `UserDialog`, `UserPasswordDialog`.
-   **Role & Permission Management**:
    -   Manager: `SecurityManager`. UI: `RoleManagementWidget`, `RoleDialog`.
-   **Audit Log Viewing**:
    -   Service: `AuditLogService` (fetches `AuditLog`, `DataChangeHistory` with pagination/filtering). UI: `AuditLogWidget` in `SettingsWidget` with "Action Log" and "Data Change History" tabs. Minor improvements to change summary formatting.

### 4.5 Reporting Module (`app/reporting/`, `app/ui/reports/`)
-   **Financial Statements**: Generation and export (BS, P&L, TB, GL).
    -   Manager: `FinancialStatementGenerator`, `ReportEngine` (PDF/Excel export with enhanced formatting). UI: Financial Statements tab in `ReportsWidget`.

### 4.6 Dashboard Module (New Minimal Implementation - `app/reporting/dashboard_manager.py`, `app/ui/dashboard/`)
-   **Purpose**: Provide a quick overview of key financial metrics.
-   **Manager (`DashboardManager`)**:
    *   `get_dashboard_kpis()`: Retrieves data for YTD Revenue, Expenses, Net Profit (via `FinancialStatementGenerator`); Current Cash Balance (sum of base currency active bank accounts via `BankAccountService`); Total Outstanding AR/AP (via `CustomerService`/`VendorService` querying respective balance views, or from GL account balances). Returns data in `DashboardKPIData` DTO.
-   **UI (`DashboardWidget`)**:
    *   Displays KPIs fetched from `DashboardManager`.
    *   Includes a refresh button.

### 4.7 Banking Module (Significant Enhancements - `app/business_logic/`, `app/services/business_services.py`, `app/ui/banking/`)
-   **Purpose**: Manage bank accounts, transactions, CSV import, and reconciliation.
-   **Bank Account Management (Existing)**: CRUD via `BankAccountManager`, `BankAccountService`, `BankAccountsWidget`, `BankAccountDialog`.
-   **Bank Transaction Entry (Manual - Existing)**: Via `BankTransactionManager`, `BankTransactionService`, `BankTransactionsWidget`, `BankTransactionDialog`.
-   **Bank Reconciliation Workflow (New)**:
    1.  User selects bank account, statement date, and end balance in `BankReconciliationWidget`.
    2.  `BankTransactionManager.get_unreconciled_transactions_for_matching` fetches unreconciled statement items (from CSV imports, `is_from_statement=True`) and system transactions (`is_from_statement=False`). GL balance for the bank account is also fetched.
    3.  UI displays items in two tables (`ReconciliationTableModel`); user checks items to match. Reconciliation summary (Book Balance, Statement Balance, Adjustments, Difference) auto-updates.
    4.  For unmatched statement items (e.g., bank charges, interest), user can click "Add Journal Entry". `JournalEntryDialog` opens, pre-filled. Posting this JE via `JournalEntryManager` auto-creates a corresponding system `BankTransaction` (`is_from_statement=False`).
    5.  When "Difference" in summary is zero (or within tolerance), user clicks "Save Reconciliation".
    6.  `BankReconciliationService.save_reconciliation_details` is called. It saves the `BankReconciliation` record, updates reconciled `BankTransaction` records (sets `is_reconciled=True`, `reconciled_date`, `reconciled_bank_reconciliation_id`), and updates `BankAccount.last_reconciled_date` and `BankAccount.last_reconciled_balance`. All these DB operations are in a single transaction.
-   **CSV Bank Statement Import (New)**:
    1.  User clicks "Import Statement (CSV)" in `BankTransactionsWidget` (toolbar for the selected bank account).
    2.  `CSVImportConfigDialog` opens for file selection, CSV format options (header, date format), and column mapping (Date, Description, Debit/Credit/Single Amount, Reference, Value Date).
    3.  `BankTransactionManager.import_bank_statement_csv` processes the file according to configuration, creates `BankTransaction` records (marked `is_from_statement=True`, `raw_statement_data` populated with original CSV row). Performs basic duplicate checks. Returns import summary.
-   **Automatic Bank Transactions from Journal Entries (New)**:
    -   `JournalEntryManager.post_journal_entry()`: If a JE line debits/credits a GL account linked to a bank account, a `BankTransaction` record is automatically created.

### 4.8 Payments Module (`app/business_logic/payment_manager.py`, `app/ui/payments/`)
-   **Purpose**: Record customer receipts and vendor payments, allocate them to invoices, and generate corresponding financial postings.
-   **Payment Processing**:
    -   Manager: `PaymentManager` (validates data, generates payment numbers, creates `Payment` & `PaymentAllocation` records, orchestrates JE creation via `JournalEntryManager`, updates invoice balances).
    -   Service: `PaymentService` (DB operations for `Payment`, `PaymentAllocation`).
    -   UI: `PaymentsWidget` (list view with filters), `PaymentDialog` (add payment/receipt, with detailed invoice allocation table).

## 5. User Interface Implementation (`app/ui/`)
-   **Main Window (`MainWindow`)**: Primary application container with a tabbed interface.
-   **Module Widgets**: Dedicated widgets for major functional areas (Sales, Purchases, Reports, Settings, Banking, Bank Reconciliation, Payments, Dashboard) hosted in tabs. Typically include toolbars, filter areas, and data displays (`QTableView`, `QTreeView`).
-   **Dialogs**: For creating/editing records (e.g., `SalesInvoiceDialog`, `AccountDialog`, `BankAccountDialog`, `BankTransactionDialog`, `PaymentDialog`, `CSVImportConfigDialog`, `JournalEntryDialog`). Feature forms for input and interact with managers.
-   **Table Models**: Custom `QAbstractTableModel` subclasses (e.g., `SalesInvoiceTableModel`, `BankAccountTableModel`, `ReconciliationTableModel`) feed data to `QTableView`s.
-   **Asynchronous Interaction**: UI elements initiate backend operations via `schedule_task_from_qt`. Callbacks or `QMetaObject.invokeMethod` update UI with results from async tasks, ensuring responsiveness.
-   **Data Validation**: Primarily by Pydantic DTOs (on UI data collection) and manager classes. UI provides immediate feedback for some simple validation.
-   **Resource Management**: Icons/images from `resources/`, using compiled Qt resource file (`app/resources_rc.py`).
-   **Specific UI Components for v14.0**:
    *   `DashboardWidget`: Displays KPIs.
    *   `BankReconciliationWidget`: Central UI for bank reconciliation.
    *   `ReconciliationTableModel`: For tables in `BankReconciliationWidget`.
    *   `CSVImportConfigDialog`: For CSV import configuration.
    *   `BankTransactionsWidget`: Toolbar updated with "Import Statement (CSV)" action.
    *   `MainWindow`: "Bank Reconciliation" tab added.
-   **Overall Structure (from v12.0, still relevant)**:
    *   `BankingWidget`: Master-detail for bank accounts and their transactions.
    *   `PaymentsWidget`: List view and entry point for `PaymentDialog`.
    *   `SettingsWidget`: Includes "Audit Logs" tab with `AuditLogWidget`.

## 6. Security Considerations
-   **Authentication**: User login handled by `SecurityManager` using `bcrypt` for password hashing. Failed attempts tracked; accounts can be locked.
-   **Authorization (RBAC)**: Granular permission system. Permissions assigned to roles; users assigned roles. `SecurityManager.has_permission()` checks authorization. "Administrator" role has all permissions, protected.
-   **Audit Trails**: Comprehensive database-level audit logging via triggers. `DatabaseManager` sets `app.current_user_id` session variable captured by triggers. Data in `audit.audit_log` (action summaries) and `audit.data_change_history` (field-level changes).
-   **Data Integrity**: Enforced by database constraints, DTO validation, and business logic validation in managers.

## 7. Database Access Implementation
-   **`DatabaseManager`**: Manages SQLAlchemy async engine and `asyncpg` connection pool. Provides database sessions.
-   **Services (Repository Pattern)**: Service classes (e.g., `AccountService`, `SalesInvoiceService`, `BankReconciliationService`) encapsulate data access logic for ORM models using SQLAlchemy's async session. Common methods: `get_by_id`, `get_all_summary`, `save`.
-   **ORM Models (`app/models/`)**: Define mapping between Python objects and database tables, including relationships, constraints, mixins.
-   **Transactions**: Multi-step database operations (e.g., invoice posting, payment recording, bank reconciliation saving) are handled within a single database session (`async with db_manager.session():`) managed by manager methods to ensure atomicity.
    *   `BankReconciliationService.save_reconciliation_details` ensures that saving the `BankReconciliation` record, updating multiple `BankTransaction` records, and updating the `BankAccount` record occurs within a single atomic database transaction.

## 8. Deployment and Installation
-   **Prerequisites**: Python 3.9+, PostgreSQL 14+, Poetry.
-   **Setup**:
    1.  Clone repository.
    2.  Install dependencies: `poetry install`.
    3.  Configure database connection in `config.ini` (platform-specific user config directory). Create `config.ini` from `config.example.ini` if it doesn't exist.
    4.  Initialize database: `poetry run sg_bookkeeper_db_init --user <pg_admin_user> ...`. This executes `scripts/schema.sql` (DDL, v1.0.4) and `scripts/initial_data.sql` (seeding, updated for new permissions/configs).
-   **Execution**: `poetry run sg_bookkeeper`.
-   Refer to `README.md` and `deployment_guide.md` for detailed instructions.

## 9. Data Flow Examples

### 9.1 Data Flow Example: Sales Invoice Posting
1.  **UI (`SalesInvoiceDialog`)**: User completes invoice details (customer, items, quantities, dates), clicks "Save & Approve".
2.  **Data Collection & DTO (UI/Manager)**: UI data (header, lines) gathered into `SalesInvoiceCreateData` DTO.
3.  **Manager (`SalesInvoiceManager.create_and_post_invoice`)**:
    *   Receives DTO. Performs validations (fiscal period open, customer valid, product valid, quantities available for inventory items).
    *   Calculates line totals, subtotals, tax amounts (using `TaxCalculator`), and grand total.
    *   Generates unique invoice number (via `SequenceService` obtained from `ApplicationCore`).
    *   Calls `SalesInvoiceService.create_invoice_from_dto()` to save `SalesInvoice` and `SalesInvoiceLine` ORM objects to database.
4.  **Financial Journal Entry (Manager: `JournalEntryManager`)**:
    *   If invoice saved successfully, `SalesInvoiceManager` prepares data for financial JE (Debit Accounts Receivable, Credit Sales Revenue, Credit GST Payable).
    *   Calls `JournalEntryManager.create_and_post_journal_entry()` with JE data. This validates, creates, and posts the JE, updating account balances.
5.  **Inventory Journal Entry (Manager: `JournalEntryManager`, Service: `ProductService`)**:
    *   If invoice includes inventory items, `SalesInvoiceManager` calculates Cost of Goods Sold (COGS) using Weighted Average Cost (WAC) from `ProductService`.
    *   Prepares data for COGS JE (Debit COGS, Credit Inventory).
    *   Calls `JournalEntryManager.create_and_post_journal_entry()` for COGS JE.
    *   (Conceptually, `InventoryMovement` records are also created.)
6.  **Invoice Status Update (Service: `SalesInvoiceService`)**:
    *   `SalesInvoiceManager` calls `SalesInvoiceService` to update the invoice's status to "Posted" and links the main financial JE ID.
7.  **UI Feedback**: Success message. Sales invoice list view updates.

### 9.2 Data Flow Example: Bank Reconciliation Process
1.  **Setup (UI: `BankReconciliationWidget`)**:
    *   User selects a Bank Account.
    *   User enters Statement Date and Statement Ending Balance from their bank statement.
    *   User clicks "Load / Refresh Transactions".
2.  **Fetch Data (Manager: `BankTransactionManager`, Services: `BankTransactionService`, `JournalService`, `AccountService`)**:
    *   Widget calls `BankTransactionManager.get_unreconciled_transactions_for_matching()`.
    *   Manager fetches via `BankTransactionService`:
        *   Unreconciled statement items (`is_from_statement=True`) up to `statement_date`.
        *   Unreconciled system bank transactions (`is_from_statement=False`) up to `statement_date`.
    *   Widget fetches current GL balance for the bank account's linked GL account via `JournalService.get_account_balance()`. This is the initial "Book Balance (per GL)".
3.  **Display & Initial Calculation (UI)**:
    *   Transactions populate two tables (`ReconciliationTableModel`).
    *   "Reconciliation Summary" section calculates: Book Balance, adjustments for *unchecked* statement items (interest, charges), adjustments for *unchecked* system items (deposits in transit, outstanding withdrawals), Adjusted Book Balance, Adjusted Bank Balance, and Difference.
4.  **User Interaction (UI)**:
    *   **Matching**: User selects/checks items from statement table and system table. "Match Selected" button (if implemented for session-level clearing) would visually pair them if sums match, and they'd be excluded from summary recalculation. UI summary updates dynamically as items are checked/unchecked.
    *   **Creating JEs for Statement Items**: User selects an unmatched statement item (e.g., bank charge).
        *   Clicks "Add Journal Entry".
        *   `JournalEntryDialog` opens, pre-filled (e.g., debit Bank Charge Expense, credit Bank GL Account).
        *   User completes and posts JE. `JournalEntryManager.post_journal_entry()` creates JE and auto-creates a new system `BankTransaction`.
        *   `BankReconciliationWidget` reloads transactions. The new system transaction appears for matching.
5.  **Saving Reconciliation (UI -> Manager (conceptual) -> Service: `BankReconciliationService`)**:
    *   When "Difference" is zero, "Save Reconciliation" button enabled. User clicks it.
    *   UI collects data for `BankReconciliationCreateData` DTO (bank_account_id, statement_date, statement_ending_balance, final calculated_book_balance, notes) and IDs of all `BankTransaction` records "cleared" (checked) in the session.
    *   `BankReconciliationService.save_reconciliation_details()` is called. This service method:
        1.  Creates and saves a new `business.bank_reconciliations` record.
        2.  Updates all "cleared" `business.bank_transactions`: sets `is_reconciled=True`, `reconciled_date` (to statement_date), `reconciled_bank_reconciliation_id`.
        3.  Updates `business.bank_accounts`: sets `last_reconciled_date`, `last_reconciled_balance`.
        4.  All DB operations performed in a single transaction.
6.  **UI Feedback**: Success/error message. UI might clear or reload.

## 10. Conclusion
Version 13.0 of SG Bookkeeper introduces significant advancements in its banking module, primarily through the implementation of CSV bank statement import and a comprehensive bank reconciliation feature. The automated creation of bank transactions from relevant journal entries further enhances data integrity. Additionally, an initial dashboard providing key performance indicators offers users valuable financial insights at a glance. These additions, built upon the established layered architecture and robust database schema (v1.0.4), substantially increase the application's practical utility for managing bank activities and ensuring financial accuracy, moving it closer to a feature-complete accounting solution for SMBs. The focus on meticulous implementation ensures a solid foundation for future development, which will critically include the establishment of a comprehensive automated testing suite and continued refinement of existing modules.

---
https://drive.google.com/file/d/11Cv4mFJ5z4I3inVCg8nkncVsAQtuIWrl/view?usp=sharing, https://drive.google.com/file/d/13aFutu059EFwgvQM4JE5LrYT13_62ztj/view?usp=sharing, https://drive.google.com/file/d/150VU2J4NfkYirCIGqQxC5VL9a_s7jyV0/view?usp=sharing, https://drive.google.com/file/d/1Fcdn0EWCauERrISMKReM_r0_nVIQvPiH/view?usp=sharing, https://drive.google.com/file/d/1GWOGYCBqwiPra5MdbwwhwXrV2V-gc4iw/view?usp=sharing, https://drive.google.com/file/d/1IRffneWyqY8ILVvfOu3apYxB15SnhMYD/view?usp=sharing, https://drive.google.com/file/d/1QYQSJ32tb7UYfuT-VHC2vgYYS3Cw_9dz/view?usp=sharing, https://drive.google.com/file/d/1S4zRP59L2Jxru__jXeoTL2TGZ4JN_GOT/view?usp=sharing, https://drive.google.com/file/d/1X5XkobtrDHItY5dTnWRYajA9LTVvZTGy/view?usp=sharing, https://drive.google.com/file/d/1bsb7xdrTRvfFSLOJVv_YBVncejRYeX-p/view?usp=sharing, https://drive.google.com/file/d/1eU9E4v6uT69z91uEABi8xf4-L1_PUKaI/view?usp=sharing, https://drive.google.com/file/d/1fcRRxU4xYdqMgGp58OyuFDOqIcGeOIW_/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221gVm5GnROGWVVYBXkgumxd5puGZ6g5Qs3%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1hF6djKphaR51gqDKE6GLgeBnlWXdKcWU/view?usp=sharing, https://drive.google.com/file/d/1ndjSoP14ry1oCHgOguxNgNWxyP4c18ww/view?usp=sharing, https://drive.google.com/file/d/1zWrsOeANNSTZ51c666H-DxQapeSjXnZY/view?usp=sharing
