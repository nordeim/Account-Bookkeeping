# Project Architecture Document: SG Bookkeeper (v4)

## 1. Introduction

### 1.1 Purpose
This document provides a comprehensive overview of the SG Bookkeeper application's architecture. It details the system's design, components, their interactions, data flow, and key architectural patterns employed. The goal is to serve as a guide for developers, architects, and technical stakeholders for understanding, maintaining, and evolving the application.

### 1.2 Scope
This document covers:
*   High-level system architecture and its layers.
*   Detailed component architecture, including core components, data models (ORM), data access layer (services), business logic layer (managers), and presentation layer (UI).
*   Data architecture, including database schema organization and data transfer objects (DTOs).
*   Key technologies, frameworks, and design patterns used.
*   Specialized architectural aspects such as asynchronous processing, configuration management, security, and resource handling.
*   The overall project structure.

### 1.3 Intended Audience
*   **Software Developers**: For understanding system design, component responsibilities, and development guidelines.
*   **Software Architects**: For reviewing and evolving the architecture.
*   **QA Engineers**: For understanding system behavior and designing effective test strategies.
*   **Technical Project Managers**: For project oversight and technical decision-making.

## 2. System Overview
SG Bookkeeper is a cross-platform desktop application designed to provide comprehensive accounting solutions for Small to Medium-sized Businesses (SMBs), particularly those operating in Singapore. It is built using Python, with PySide6 for the Graphical User Interface (GUI) and PostgreSQL as the backend database.

Key functionalities include:
*   Full double-entry bookkeeping.
*   Chart of Accounts management.
*   General Journal entries and postings.
*   Sales and Purchase invoicing lifecycles.
*   Customer and Vendor relationship management (CRM/SRM).
*   Product and Service management, including basic inventory tracking.
*   Bank account management, manual transaction entry, CSV bank statement import, and a comprehensive bank reconciliation module.
*   Payment processing (customer receipts, vendor payments) with invoice allocation.
*   Singapore-specific GST F5 tax return preparation and detailed reporting.
*   Financial reporting (Balance Sheet, Profit & Loss, Trial Balance, General Ledger).
*   A dashboard for Key Performance Indicators (KPIs).
*   System administration features: User and Role management with Role-Based Access Control (RBAC), system configuration, and audit logging.

The application emphasizes data integrity, compliance with local accounting standards, user-friendliness, and robust auditability. It employs an asynchronous processing model to ensure UI responsiveness.

## 3. Architectural Goals & Principles
The architecture of SG Bookkeeper is guided by the following goals and principles:
*   **Maintainability**: Clear separation of concerns and modular design to simplify understanding, debugging, and updates.
*   **Scalability**: Ability to handle increasing data volumes and feature complexity. While a desktop app, the backend logic should be robust.
*   **Responsiveness**: Asynchronous operations for long-running tasks to keep the UI fluid and responsive.
*   **Data Integrity**: Ensuring accuracy and consistency of financial data through database constraints, DTO validations, and business rule enforcement.
*   **Testability**: Designing components in a way that facilitates unit and integration testing.
*   **Modularity**: Organizing the application into distinct modules (e.g., accounting, business, banking, UI) that can be developed and maintained somewhat independently.
*   **Reusability**: Creating shared components and services where appropriate.

## 4. High-Level Architecture

The application follows a layered architecture to promote separation of concerns and maintainability.

```
+-----------------------------------------------------------------+
|                       Presentation Layer (UI)                   |
| (PySide6: MainWindow, Module Widgets, Dialogs, TableModels)   |
| Handles User Interaction, Displays Data, Qt Signals/Slots       |
+-----------------------------------------------------------------+
      ^                         | (schedule_task_from_qt for async calls)
      | (UI Events, Pydantic DTOs) | (Results/Updates via QMetaObject.invokeMethod)
      v                         v
+-----------------------------------------------------------------+
|                  Business Logic Layer (Managers)                |
| (ApplicationCore, *Manager classes e.g., SalesInvoiceManager,  |
|  PaymentManager, JournalEntryManager, BankTransactionManager)   |
| Encapsulates Business Rules, Validation, Orchestrates Services  |
+-----------------------------------------------------------------+
      ^                         | (Service Calls, SQLAlchemy ORM Objects/DTOs)
      | (Service Results as Result objects) | (SQLAlchemy Async Operations)
      v                         v
+-----------------------------------------------------------------+
|                       Data Access Layer (Services)              |
| (DatabaseManager, *Service classes e.g., AccountService,       |
|  SalesInvoiceService, BankAccountService), SQLAlchemy ORM Models|
| Abstracts Database Interactions, Repository Pattern, Unit of Work|
+-----------------------------------------------------------------+
                                | (asyncpg DB Driver)
                                v
+-----------------------------------------------------------------+
|                          Database Layer                         |
| (PostgreSQL: Schemas [core, accounting, business, audit],      |
|  Tables, Views, Functions, Triggers)                            |
+-----------------------------------------------------------------+
```

### 4.1 Layers Description

*   **Presentation Layer (UI)**:
    *   Implemented using PySide6 (Qt for Python).
    *   Responsible for rendering the user interface and capturing user input.
    *   Consists of the `MainWindow`, various module-specific widgets (e.g., `SalesInvoicesWidget`, `BankingWidget`), dialogs for data entry/editing (e.g., `SalesInvoiceDialog`), and custom table models (`QAbstractTableModel` subclasses).
    *   Communicates with the Business Logic Layer by sending DTOs and invoking manager methods (often asynchronously).
    *   Updates are received from the backend and applied using Qt's signal/slot mechanism or `QMetaObject.invokeMethod`.

*   **Business Logic Layer (Managers)**:
    *   Contains the core business rules, complex workflows, and validation logic.
    *   Orchestrates operations involving multiple services or data entities.
    *   Managers (e.g., `SalesInvoiceManager`, `JournalEntryManager`, `PaymentManager`, `BankTransactionManager`) are the primary components in this layer.
    *   `ApplicationCore` acts as a central service locator and coordinator for managers.
    *   Receives data (often as DTOs) from the UI layer and returns `Result` objects indicating success/failure and payload/errors.

*   **Data Access Layer (Services & ORM)**:
    *   Abstracts database interactions.
    *   Services (e.g., `AccountService`, `SalesInvoiceService`, `BankReconciliationService`) implement the Repository pattern, providing a clean API for data persistence and retrieval.
    *   Uses SQLAlchemy's asynchronous ORM for object-relational mapping. ORM models (`app/models/`) define the Python representation of database tables and their relationships.
    *   The `DatabaseManager` handles database connection pooling and session management.

*   **Database Layer**:
    *   PostgreSQL is used as the relational database management system.
    *   The schema is organized into logical groups: `core` (system-wide entities), `accounting` (financial data), `business` (operational data), and `audit` (logging).
    *   Defined in `scripts/schema.sql`, it includes tables, views, functions, and triggers to enforce data integrity and automate certain processes (e.g., audit logging, bank balance updates).

## 5. Detailed Component Architecture

### 5.1 Core Components (`app/core/`)

*   **`ApplicationCore` (`application_core.py`)**:
    *   The central singleton orchestrator for the backend.
    *   Initializes and provides access to all services and managers.
    *   Manages application startup (e.g., database initialization) and shutdown.
    *   Acts as a service locator/dependency injector for other backend components.
    *   Holds a reference to the global logger.

*   **`DatabaseManager` (`database_manager.py`)**:
    *   Manages asynchronous PostgreSQL database connections using SQLAlchemy's async engine and an `asyncpg` connection pool.
    *   Provides an `asynccontextmanager` for database sessions (`session()`), ensuring proper transaction handling (commit/rollback) and setting the `app.current_user_id` session variable for audit triggers.
    *   Also provides a raw `asyncpg` connection context manager (`connection()`) for direct DB operations if needed.

*   **`ConfigManager` (`config_manager.py`)**:
    *   Loads and manages application settings from `config.ini` located in a platform-specific user configuration directory (e.g., `~/.config/SGBookkeeper/` on Linux).
    *   Provides typed access to configuration values (e.g., database connection parameters, application theme).

*   **`SecurityManager` (`security_manager.py`)**:
    *   Handles user authentication (password hashing with `bcrypt` and verification).
    *   Manages authorization through a Role-Based Access Control (RBAC) system, checking permissions (`has_permission()`).
    *   Provides backend logic for User, Role, and Permission CRUD operations, interacting directly with ORM models.
    *   Tracks the `current_user` (an ORM `User` object) for the application session.

*   **Asynchronous Task Management (in `app/main.py`)**:
    *   A dedicated Python `threading.Thread` (`_ASYNC_LOOP_THREAD`) runs a persistent `asyncio` event loop (`_ASYNC_LOOP`). This loop is separate from the Qt GUI event loop.
    *   The `schedule_task_from_qt(coroutine)` utility function safely schedules coroutines (typically manager or service methods initiated by UI actions) from the main Qt GUI thread onto the dedicated asyncio loop thread using `asyncio.run_coroutine_threadsafe`.
    *   UI updates resulting from these asynchronous operations are marshaled back to the Qt main thread using `QMetaObject.invokeMethod` with `Qt.ConnectionType.QueuedConnection`, often with data serialized to JSON for thread safety.

### 5.2 Data Models (`app/models/`)
The `app/models/` directory contains SQLAlchemy ORM models that map to database tables.

*   **Base Classes (`base.py`)**:
    *   `Base`: The declarative base for all ORM models.
    *   `TimestampMixin`: Provides `created_at` and `updated_at` columns with automatic timestamp management.
    *   `UserAuditMixin`: Provides `created_by` (mapped to `created_by_user_id`) and `updated_by` (mapped to `updated_by_user_id`) columns, linking to `core.users.id`.

*   **Organization**: Models are organized into subdirectories mirroring the database schema structure:
    *   `app/models/core/`: For `User`, `Role`, `Permission`, `CompanySetting`, `Configuration`, `Sequence`.
    *   `app/models/accounting/`: For `Account`, `AccountType`, `JournalEntry`, `FiscalYear`, `TaxCode`, `GSTReturn`, etc.
    *   `app/models/business/`: For `Customer`, `Vendor`, `Product`, `SalesInvoice`, `PurchaseInvoice`, `BankAccount`, `BankTransaction`, `Payment`, `BankReconciliation`.
    *   `app/models/audit/`: For `AuditLog`, `DataChangeHistory`.

*   **Features**:
    *   Uses SQLAlchemy 2.0 mapped column style (`Mapped`, `mapped_column`) with Python type hints.
    *   Defines relationships between models (e.g., one-to-many, many-to-many) using `relationship()` with `back_populates`.
    *   Includes `CheckConstraint` where appropriate, mirroring database constraints.
    *   Junction tables for many-to-many relationships (e.g., `user_roles_table`, `role_permissions_table`) are defined explicitly as `Table` objects within the relevant model file (e.g., `app/models/core/user.py`).

*   **`app/models/__init__.py`**: Exports all ORM models, providing a single point of import for services and managers.

### 5.3 Data Access Layer (`app/services/`)
This layer abstracts database interactions and implements the Repository pattern.

*   **Interfaces (`app/services/__init__.py`)**: Defines a generic `IRepository[T, ID]` and specific interfaces for key entities (e.g., `IAccountRepository`, `ISalesInvoiceRepository`, `IBankReconciliationRepository`). These interfaces define the contract for data operations.
*   **Service Implementations (e.g., `account_service.py`, `journal_service.py`, `business_services.py`)**:
    *   Classes that implement the defined repository interfaces.
    *   Encapsulate SQLAlchemy query logic (both simple CRUD and complex queries).
    *   Use the `DatabaseManager` to obtain `AsyncSession` instances for database operations.
    *   Typically return ORM objects or lists of ORM objects. Some methods, especially those for UI listings, may return lists of DTOs or dictionaries for efficiency.
    *   Service methods are generally designed to be used within a single unit of work (database transaction) managed by the calling Manager.

### 5.4 Business Logic Layer (Managers)
Located in `app/accounting/`, `app/business_logic/`, `app/tax/`, `app/reporting/`. Managers are responsible for:

*   Encapsulating complex business workflows and rules.
*   Validating input data (often received as DTOs) before performing operations.
*   Coordinating operations between multiple services.
*   Preparing data for presentation or transforming UI input for persistence.
*   Creating and posting journal entries related to business operations (e.g., `SalesInvoiceManager` uses `JournalEntryManager`).
*   Handling application-specific logic, e.g., `GSTManager` preparing F5 return data, `BankTransactionManager` importing CSV statements.
*   Returning `Result` objects to the UI layer or other callers to indicate success/failure and carry data or error messages.

Key examples include:
*   `ChartOfAccountsManager`, `JournalEntryManager`, `FiscalPeriodManager`
*   `CustomerManager`, `VendorManager`, `ProductManager`
*   `SalesInvoiceManager`, `PurchaseInvoiceManager`, `PaymentManager`
*   `BankAccountManager`, `BankTransactionManager`, `BankReconciliationService` (often used by a manager, or its logic could be part of `BankTransactionManager` or a new `BankReconciliationManager`)
*   `GSTManager`, `TaxCalculator`
*   `FinancialStatementGenerator`, `ReportEngine`, `DashboardManager`

### 5.5 Presentation Layer (`app/ui/`)
The UI is built with PySide6.

*   **`MainWindow` (`main_window.py`)**: The main application shell, hosting a `QTabWidget` for different modules. Manages menus, toolbars, and the status bar.
*   **Module Widgets (e.g., `CustomersWidget`, `SalesInvoicesWidget`, `BankingWidget`, `BankReconciliationWidget`, `SettingsWidget`)**: Each major functional area is represented by a primary widget within a tab. These typically contain:
    *   Toolbars for common actions (add, edit, delete, refresh).
    *   Filter/search areas.
    *   Data display areas, often `QTableView` or `QTreeView`.
*   **Dialogs (e.g., `CustomerDialog`, `SalesInvoiceDialog`, `JournalEntryDialog`, `PaymentDialog`)**: Used for creating new records or editing existing ones. They feature forms for data input and validation.
*   **Table Models (e.g., `CustomerTableModel`, `SalesInvoiceTableModel`, `ReconciliationTableModel`)**: Custom subclasses of `QAbstractTableModel` provide data to `QTableView` instances, allowing for flexible data display, formatting, and handling of user interactions like sorting.
*   **Interaction with Backend**:
    *   UI actions trigger methods in Manager classes. These calls are typically scheduled asynchronously via `schedule_task_from_qt(coroutine)`.
    *   Results or data updates from asynchronous tasks are passed back to the UI thread using `QMetaObject.invokeMethod` with a slot method in the UI component, or via signals.
    *   Data is often exchanged using Pydantic DTOs for validation and clear contracts.
*   **Resource Usage**: Icons (`.svg`) and images are managed through Qt's resource system (`resources.qrc` compiled to `resources_rc.py`) or direct file paths as a fallback.

### 5.6 Utilities (`app/utils/`)

*   **`pydantic_models.py`**:
    *   Defines Pydantic DTOs for most entities. Common patterns include `BaseData`, `CreateData` (often inheriting `UserAuditData`), `UpdateData`, `Data` (full representation), and `SummaryData` (for list views).
    *   DTOs enforce data validation (types, constraints, custom validators) at the boundary between UI and Business Logic Layer.
*   **`json_helpers.py`**: Provides `json_converter` for serializing `Decimal`, `date`, `datetime` objects to JSON, and `json_date_hook` for deserializing them. Essential for inter-thread communication of complex data.
*   **`result.py`**: Defines the `Result` class, a standardized way for manager and service methods to return success/failure status along with a value or error messages.
*   **`sequence_generator.py`**: `SequenceGenerator` class for generating formatted document numbers (e.g., invoice numbers, journal entry numbers). It primarily uses a PostgreSQL function (`core.get_next_sequence_value`) for robust, concurrent sequence generation, with a Python-based fallback.
*   **Other Helpers**: `formatting.py` (currency, date), `converters.py` (e.g., `to_decimal`), `validation.py` (e.g., `is_valid_uen`).

### 5.7 Common (`app/common/`)

*   **`enums.py`**: Centralizes all application-specific enumerations (e.g., `ProductTypeEnum`, `InvoiceStatusEnum`, `PaymentTypeEnum`, `JournalTypeEnum`). This promotes consistency and type safety.

## 6. Data Architecture

### 6.1 Database System
*   **PostgreSQL (version 14+)**: Chosen for its robustness, ACID compliance, and advanced features like JSONB support and powerful procedural language (PL/pgSQL) for triggers and functions.

### 6.2 Schema Organization
The database is logically divided into four schemas, defined in `scripts/schema.sql`:
*   **`core`**: System-level entities like users, roles, permissions, company settings, application configuration, and document sequences.
*   **`accounting`**: Core financial data including chart of accounts, account types, fiscal periods/years, journal entries, currencies, exchange rates, tax codes, GST returns, and budgets.
*   **`business`**: Operational data related to customers, vendors, products/services, sales and purchase invoices, inventory movements, bank accounts, bank transactions, payments, and bank reconciliations (e.g., `business.bank_reconciliations` table).
*   **`audit`**: Tables for tracking application activity (`audit_log`) and detailed data changes (`data_change_history`).

### 6.3 Key Tables and Relationships
(A full ERD is beyond this scope, but key relationships are defined in the ORM models.)
*   `core.users` is central for ownership and audit trails (`created_by`, `updated_by` fields in many tables).
*   `accounting.accounts` forms the Chart of Accounts, linked to `accounting.journal_entry_lines`.
*   `business.sales_invoices` and `business.purchase_invoices` link to customers/vendors, products (via lines), and generate `accounting.journal_entries`.
*   `business.payments` link to customers/vendors, bank accounts, and invoices (via `business.payment_allocations`), also generating `accounting.journal_entries`.
*   `business.bank_accounts` link to `accounting.accounts` (GL link) and have `business.bank_transactions`.
*   `business.bank_reconciliations` (new) links to `business.bank_accounts` and clears `business.bank_transactions`.

### 6.4 ORM
*   **SQLAlchemy (version 2.0+)**: Used for object-relational mapping, leveraging its asynchronous features (`asyncio` extension) with the `asyncpg` driver.
*   ORM models in `app/models/` provide a Pythonic interface to database tables.

### 6.5 Data Integrity Mechanisms
*   **Primary and Foreign Keys**: Enforce relational integrity.
*   **`CHECK` Constraints**: Validate data at the database level (e.g., enum-like values, date ranges).
*   **`UNIQUE` Constraints**: Ensure uniqueness for codes, names, etc.
*   **`NOT NULL` Constraints**: Mandate required fields.
*   **Database Triggers**:
    *   Audit triggers (`audit.log_data_change_trigger_func`) automatically populate `audit.audit_log` and `audit.data_change_history` tables upon DML operations on audited tables.
    *   Timestamp triggers (`core.update_timestamp_trigger_func`) manage `updated_at` fields.
    *   Bank balance trigger (`business.update_bank_account_balance_trigger_func`) automatically updates `business.bank_accounts.current_balance` based on changes in `business.bank_transactions`.
*   **Pydantic DTO Validation**: Ensures data conforms to expected types and constraints before processing by the business logic layer.

## 7. Key Technologies & Frameworks
*   **Python**: >=3.9, <3.13
*   **UI Framework**: PySide6 (Qt 6.9.0+)
*   **Database**: PostgreSQL 14+
*   **ORM**: SQLAlchemy 2.0+ (asyncio)
*   **Async DB Driver**: `asyncpg`
*   **Data Validation (DTOs)**: Pydantic V2 (with `email-validator`)
*   **Password Hashing**: `bcrypt`
*   **Reporting Libraries**: `reportlab` (PDF), `openpyxl` (Excel)
*   **Dependency Management**: Poetry
*   **Date/Time Utilities**: `python-dateutil`
*   **Asynchronous Programming**: `asyncio`, `threading` (for dedicated asyncio loop)

## 8. Design Patterns Used
*   **Layered Architecture**
*   **Model-View-Controller (MVC) / Model-View-Presenter (MVP)** (variant)
*   **Repository Pattern** (Services in DAL)
*   **Data Transfer Object (DTO)** (Pydantic models)
*   **Result Object Pattern** (`app/utils/result.py`)
*   **Observer Pattern** (Qt Signals/Slots)
*   **Dependency Injection** (Conceptual, via `ApplicationCore`)
*   **Singleton** (Conceptual, for `ApplicationCore`)
*   **Mixins** (`TimestampMixin`, `UserAuditMixin` for ORM models)

## 9. Asynchronous Processing Model
To maintain UI responsiveness, long-running backend operations (database queries, complex calculations) are executed asynchronously.
1.  A dedicated Python thread (`_ASYNC_LOOP_THREAD`) is created at application startup, which runs its own `asyncio` event loop (`_ASYNC_LOOP`).
2.  UI event handlers (e.g., button clicks) that need to perform backend work schedule an awaitable coroutine (typically a manager method) onto this dedicated asyncio loop using `schedule_task_from_qt(coroutine)`. This function uses `asyncio.run_coroutine_threadsafe`.
3.  The manager method, running in the asyncio thread, performs its operations (e.g., calling services, which in turn make async database calls).
4.  Once the asynchronous task completes, if the UI needs to be updated, the result is marshaled back to the Qt main GUI thread using `QMetaObject.invokeMethod(target_widget, "slot_name", Qt.ConnectionType.QueuedConnection, Q_ARG(type, data))`. Data passed between threads is often serialized (e.g., to JSON using `json_helpers.py`) to ensure thread safety.
5.  The slot method in the UI widget then updates the UI components with the received data.

This model prevents the GUI from freezing during potentially lengthy backend operations.

## 10. Configuration Management
*   Application configuration is managed by `ConfigManager` (`app/core/config_manager.py`).
*   Settings are stored in `config.ini`, located in a platform-specific user configuration directory (e.g., `~/.config/SGBookkeeper/config.ini` on Linux, `%APPDATA%\SGBookkeeper\config.ini` on Windows).
*   The `config.ini` typically includes sections for `[Database]` (connection parameters, pool settings) and `[Application]` (theme, language, last opened company).
*   A default `config.ini` is created if one doesn't exist.

## 11. Security Architecture
*   **Authentication**:
    *   Managed by `SecurityManager`.
    *   Usernames and hashed passwords (using `bcrypt`) are stored in `core.users`.
    *   Login attempts are tracked, and accounts can be locked after multiple failed attempts.
*   **Authorization (RBAC)**:
    *   A granular Role-Based Access Control system is implemented.
    *   `core.permissions` defines available permissions (e.g., `USER_MANAGE`, `INVOICE_CREATE`).
    *   `core.roles` defines roles (e.g., `Administrator`, `Accountant`).
    *   `core.role_permissions` links permissions to roles.
    *   `core.user_roles` links users to roles.
    *   `SecurityManager.has_permission(required_permission_code)` checks if the `current_user` is authorized for an action based on their assigned roles and permissions. The "Administrator" role typically has all permissions.
*   **Audit Logging**:
    *   Comprehensive audit trails are maintained.
    *   The `DatabaseManager` sets a session variable `app.current_user_id` upon session creation if a user is logged in.
    *   Database triggers (e.g., `audit.log_data_change_trigger_func`) on key tables capture DML operations (INSERT, UPDATE, DELETE) and record them in:
        *   `audit.audit_log`: Stores action summaries (who, what, when, which entity).
        *   `audit.data_change_history`: Stores field-level changes (table, record ID, field, old value, new value).
    *   An `AuditLogService` and `AuditLogWidget` provide UI for viewing and filtering these logs.

## 12. Deployment & Initialization
*   **Prerequisites**: Python (>=3.9), PostgreSQL (14+), Poetry (for dependency management).
*   **Setup**:
    1.  Clone repository.
    2.  Install dependencies: `poetry install`.
    3.  Configure database connection details in `config.ini`.
    4.  Initialize the database: `poetry run sg_bookkeeper_db_init --user <pg_admin_user> ...`. This script (`scripts/db_init.py`):
        *   Creates the database if it doesn't exist (optionally dropping an existing one).
        *   Executes `scripts/schema.sql` to define tables, views, functions, and triggers.
        *   Executes `scripts/initial_data.sql` to seed default data (roles, permissions, system users, currencies, initial company settings, sequences, system GL accounts, tax codes).
        *   Sets default privileges for the application user (`sgbookkeeper_user`).
*   **Execution**: `poetry run sg_bookkeeper` (invokes `app.main:main`).

## 13. Resource Management
*   UI resources like icons and images are stored in the `resources/` directory.
*   Icons are primarily SVGs.
*   A Qt Resource Collection file (`resources/resources.qrc`) is used to compile these resources into a Python module (`app/resources_rc.py`).
*   The application attempts to load resources using `:/icons/` paths (from compiled resources). If `resources_rc.py` is not found (e.g., during development without prior compilation), it falls back to direct file system paths relative to `resources/`.

## 14. Data Flow Examples

### 14.1 Sales Invoice Posting (Simplified)
1.  **UI (`SalesInvoiceDialog`)**: User fills invoice details and clicks "Save & Approve".
2.  **DTO Creation**: UI data is packaged into `SalesInvoiceCreateData` DTO.
3.  **Manager (`SalesInvoiceManager.create_and_post_invoice`)**:
    *   Validates DTO and business rules (e.g., customer active, fiscal period open).
    *   Calculates line totals, tax (using `TaxCalculator`), and grand total.
    *   Generates invoice number (via `SequenceService` through `ApplicationCore` or `SequenceGenerator` using DB function).
    *   Calls `SalesInvoiceService` to save the draft invoice and lines.
    *   If successful, prepares data for Journal Entries.
4.  **Journal Entry Creation (`JournalEntryManager`)**:
    *   `SalesInvoiceManager` calls `JournalEntryManager.create_journal_entry` for financial JE (AR, Sales, GST).
    *   `JournalEntryManager` validates, creates, and saves JE.
    *   `SalesInvoiceManager` calls `JournalEntryManager.post_journal_entry` to post the financial JE.
5.  **Inventory & COGS (if applicable)**:
    *   `SalesInvoiceManager` calculates COGS (e.g., using WAC from `ProductService` or `inventory_summary` view).
    *   Calls `InventoryMovementService` to record inventory outflow.
    *   Calls `JournalEntryManager` to create and post COGS JE (COGS, Inventory).
6.  **Status Update**: `SalesInvoiceManager` updates invoice status to "Approved" (or "Posted") via `SalesInvoiceService` and links the main JE ID.
7.  **UI Feedback**: Success message; invoice list refreshes.

### 14.2 Bank Reconciliation (Simplified)
1.  **UI (`BankReconciliationWidget`)**: User selects bank account, statement date, enters statement end balance, clicks "Load Transactions".
2.  **Manager (`BankTransactionManager.get_unreconciled_transactions_for_matching`)**:
    *   Fetches unreconciled statement items (via `BankTransactionService`, `is_from_statement=True`).
    *   Fetches unreconciled system bank transactions (via `BankTransactionService`, `is_from_statement=False`).
    *   Fetches current GL balance for the bank (via `JournalService.get_account_balance`).
3.  **UI**: Displays items in tables. Calculates initial summary (Book Balance, Statement Balance, Difference).
4.  **User Interaction**:
    *   User checks items to match. UI updates summary. (UI-side "clearing").
    *   For statement-only items (e.g., bank charges), user clicks "Add Journal Entry". `JournalEntryDialog` opens, pre-filled. Posting this JE (via `JournalEntryManager`) also auto-creates a system `BankTransaction`. UI reloads.
5.  **Saving Reconciliation (`BankReconciliationService.save_reconciliation_details`)**:
    *   When difference is zero, user clicks "Save Reconciliation".
    *   UI passes `BankReconciliationCreateData` and IDs of cleared `BankTransaction` records.
    *   `BankReconciliationService` (likely via a manager method):
        1.  Creates/saves a `business.bank_reconciliations` record.
        2.  Updates matched `BankTransaction` records (sets `is_reconciled=True`, `reconciled_date`, `reconciled_bank_reconciliation_id`).
        3.  Updates `BankAccount` (`last_reconciled_date`, `last_reconciled_balance`).
        4.  All within a single database transaction.
6.  **UI Feedback**: Success/error; UI refreshes.

## 15. Project Structure Overview
The project follows a standard Python application structure:
*   **`app/`**: Main application source code.
    *   **`core/`**: Core application components (`ApplicationCore`, `DatabaseManager`, etc.).
    *   **`models/`**: SQLAlchemy ORM models, organized by schema.
    *   **`services/`**: Data Access Layer services.
    *   **`accounting/`, `business_logic/`, `tax/`, `reporting/`**: Business Logic Layer managers.
    *   **`ui/`**: PySide6 UI components, organized by module.
        *   **`shared/`**: Reusable UI components.
    *   **`utils/`**: Utility classes and functions (DTOs, helpers).
    *   **`common/`**: Common elements like Enums.
    *   **`main.py`**: Main application entry point.
*   **`scripts/`**: Database initialization scripts (`schema.sql`, `initial_data.sql`, `db_init.py`).
*   **`data/`**: CSV templates, report templates.
*   **`resources/`**: Icons, images, and Qt resource files.
*   **`tests/`**: Unit and integration tests (structure implies future use).
*   **Root**: `pyproject.toml`, `README.md`, etc.

## 16. Future Considerations / Areas for Improvement (Conceptual)
*   **Comprehensive Automated Testing**: Implement unit, integration, and UI tests for better reliability.
*   **Enhanced Reporting**: More flexible and customizable reporting options.
*   **Background Task Management**: For very long-running tasks or scheduled jobs (e.g., nightly batch processing, email notifications), a more robust background task queue (like Celery) might be considered if the application evolves beyond a simple desktop scope.
*   **API Layer (Optional)**: If web access or integration with other systems becomes a requirement, an API layer (e.g., FastAPI) could be introduced.
*   **Plugin Architecture**: Using `ModuleManager` more formally to allow for dynamic loading of optional features or third-party extensions.
*   **Internationalization (i18n) / Localization (l10n)**: While "language" is in `config.ini`, a full i18n system (e.g., Qt Linguist) would be needed for multi-language support.
*   **ORM Optimization**: For performance-critical queries, review and optimize SQLAlchemy usage, potentially using more core SQL expressions where beneficial.
*   **Enhanced Security**: Further security hardening (e.g., rate limiting, more detailed permission checks, two-factor authentication if user base grows).

This document provides a snapshot of the SG Bookkeeper application's architecture based on the provided codebase. It should be updated as the project evolves.

---
https://drive.google.com/file/d/1-vPle_bsfW5q1aXJ4JI9VB5cOYY3f7oU/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%2216tABsm1Plf_0fhtruoJyyxobBli3e8-7%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/19T9JbSrHCuXhHpzFMUh4Ti_0sDPDycSW/view?usp=sharing, https://drive.google.com/file/d/1D7GYodcMgZv3ROPPRJTYX0g9Rrsq8wJD/view?usp=sharing, https://drive.google.com/file/d/1EGOoM0TGqPgNBJzwxKdVO2u331Myhd4b/view?usp=sharing, https://drive.google.com/file/d/1Ivh39pjoqQ9z4_oj7w7hWc0zOje2-Xjb/view?usp=sharing, https://drive.google.com/file/d/1LzMu08SqY6E5ZuvISa4BsEHxatVPE9g_/view?usp=sharing, https://drive.google.com/file/d/1QyS0xlh6owfMif6KMlyXmE2Zx2hmcdza/view?usp=sharing, https://drive.google.com/file/d/1ZZODHjv2AX2Pn1cRh_0CJDTSzXRGjAt_/view?usp=sharing, https://drive.google.com/file/d/1bSRRtsWeJI9djXTDZTZTjZxnsWS3cvsV/view?usp=sharing, https://drive.google.com/file/d/1uKfTNXg8Oaes7aGaoaPB6klSZzywizh9/view?usp=sharing, https://drive.google.com/file/d/1vTPAoLcEetjBj17-5nTa_Z6RS7ND5Wmz/view?usp=sharing, https://drive.google.com/file/d/1xbA8X7irZHUayYcfOWWfi4oWm18hFDo2/view?usp=sharing

