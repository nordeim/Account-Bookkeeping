# Project Architecture Document: SG Bookkeeper (v5)

## 1. Introduction

### 1.1 Purpose
This document outlines the software architecture of the SG Bookkeeper application. It details the system's structure, components, their interactions, data management strategies, and the design principles guiding its development. This document is intended to provide a comprehensive understanding of the application's technical foundation for development, maintenance, and future evolution.

### 1.2 Scope
This document covers the following architectural aspects:
*   High-level system architecture and its constituent layers.
*   Detailed breakdown of components within each layer, including UI, business logic, data access, and core services.
*   Data architecture, encompassing database schema, ORM models, and data transfer objects (DTOs).
*   Key technologies and frameworks utilized.
*   Core architectural patterns and design choices.
*   Specific architectural considerations like asynchronous processing, configuration, security, and error handling.
*   An overview of the project's directory structure.

### 1.3 Intended Audience
*   **Software Developers**: To understand the system design, component responsibilities, inter-component communication, and coding conventions.
*   **Software Architects**: For architectural review, decision-making, and planning future system enhancements.
*   **Technical Leads & Project Managers**: For project oversight, understanding technical constraints, and resource allocation.
*   **QA Engineers**: To comprehend system behavior, identify test boundaries, and design effective testing strategies.

## 2. System Overview
SG Bookkeeper is a desktop accounting application tailored for Small to Medium-sized Businesses (SMBs) in Singapore. It is developed in Python, utilizing PySide6 for the graphical user interface and PostgreSQL for persistent data storage. The application aims to provide a comprehensive suite of accounting tools, including:
*   Double-entry bookkeeping core.
*   Management of Chart of Accounts, Journal Entries, Fiscal Periods.
*   Modules for Sales, Purchases, Payments, Banking (including CSV Import and Reconciliation), Customers, Vendors, and Products/Services.
*   GST F5 tax reporting and other financial statement generation.
*   User and role management with RBAC for security.
*   Dashboard for Key Performance Indicators (KPIs).
*   Comprehensive audit logging.

The system is designed to be responsive, maintainable, and robust, with a clear separation of concerns.

## 3. Architectural Goals & Principles
The architecture is designed to achieve:
*   **Modularity**: Components are organized into logical modules with well-defined responsibilities and interfaces.
*   **Maintainability**: A clear, layered architecture and consistent coding patterns facilitate easier understanding, debugging, and modification.
*   **Testability**: Separation of concerns allows for unit testing of individual components and facilitates integration testing.
*   **Responsiveness**: Asynchronous processing for backend operations ensures the UI remains fluid and does not freeze during long tasks.
*   **Data Integrity**: Robust validation at multiple levels (DTOs, business logic, database constraints) and transactional data operations.
*   **Scalability (Conceptual)**: While a desktop application, the backend structure aims to handle growing data and complexity efficiently.
*   **Extensibility**: The architecture should accommodate new features and modules with minimal disruption to existing functionality.

## 4. High-Level Architecture
SG Bookkeeper employs a multi-layered architecture, separating concerns into distinct functional areas. This promotes decoupling, testability, and maintainability.

```
+-----------------------------------------------------------------+
|                       Presentation Layer (UI)                   |
| (PySide6: MainWindow, Module Widgets, Dialogs, TableModels)   |
| Handles User Interaction, Displays Data, Qt Signals/Slots       |
| Uses Pydantic DTOs for data input/display.                      |
+-----------------------------------------------------------------+
      ^                         | (Calls Managers via `schedule_task_from_qt`)
      | (UI Events, DTOs)       | (DTOs / Result Objects via `QMetaObject.invokeMethod`)
      v                         v
+-----------------------------------------------------------------+
|                  Business Logic Layer (Managers)                |
| (ApplicationCore, *Manager classes like SalesInvoiceManager,   |
|  JournalEntryManager, BankTransactionManager, PaymentManager)   |
| Encapsulates Business Rules, Complex Workflows, Validation.     |
| Orchestrates Services. Returns `Result` objects.                |
+-----------------------------------------------------------------+
      ^                         | (Calls Service methods with ORM objects or DTOs)
      | (Service results/ORM Objects) | (Async SQLAlchemy operations within Services)
      v                         v
+-----------------------------------------------------------------+
|                       Data Access Layer (Services)              |
| (DatabaseManager, *Service classes like AccountService,        |
|  SalesInvoiceService, BankReconciliationService), SQLAlchemy Models|
| Implements Repository Pattern. Abstracts Database Interactions. |
| Manages ORM query logic.                                        |
+-----------------------------------------------------------------+
                                | (asyncpg Python DB Driver)
                                v
+-----------------------------------------------------------------+
|                          Database Layer                         |
| (PostgreSQL: Schemas [core, accounting, business, audit],      |
|  Tables, Views, Functions, Triggers, Constraints)               |
+-----------------------------------------------------------------+
```

### 4.1 Layers Description

*   **Presentation Layer (UI)**:
    *   Built with PySide6, responsible for all user interaction and data display.
    *   Key components include `MainWindow`, various module-specific `QWidget` subclasses (e.g., `SalesInvoicesWidget`, `BankingWidget`, `DashboardWidget`), data entry dialogs (`QDialog` subclasses like `SalesInvoiceDialog`, `PaymentDialog`), and custom table models (`QAbstractTableModel` subclasses).
    *   Communicates with the Business Logic Layer primarily by invoking methods on Manager classes. User input is often packaged into Pydantic DTOs before being sent to managers.
    *   Handles asynchronous calls to the backend via `schedule_task_from_qt` and receives results/updates via `QMetaObject.invokeMethod` to update UI elements safely from the Qt main thread.

*   **Business Logic Layer (Managers)**:
    *   This layer contains the application's core business rules, validation logic, and orchestrates complex operations.
    *   Managers (e.g., `SalesInvoiceManager`, `JournalEntryManager`, `PaymentManager`, `BankTransactionManager`, `DashboardManager`) are the primary components. They coordinate actions between multiple services, enforce business rules, and prepare data for the UI or for persistence.
    *   `ApplicationCore` acts as a central access point and initializer for these managers and their service dependencies.
    *   Managers typically operate on DTOs received from the UI and interact with services using ORM objects or DTOs.
    *   They return `Result` objects (from `app/utils/result.py`) to indicate the outcome of operations.

*   **Data Access Layer (Services & ORM)**:
    *   Provides an abstraction over direct database interactions.
    *   **Services** (e.g., `AccountService`, `SalesInvoiceService`, `BankReconciliationService` located in `app/services/`) implement the Repository pattern. They encapsulate the logic for querying and persisting data for specific ORM models or groups of related models.
    *   **SQLAlchemy ORM Models** (in `app/models/`) define the object-oriented mapping to database tables. They include relationships, data types, and sometimes model-level validation or behavior.
    *   The `DatabaseManager` (from `app/core/`) provides asynchronous database sessions used by the services.

*   **Database Layer**:
    *   **PostgreSQL** is the RDBMS.
    *   The database schema (defined in `scripts/schema.sql`) is organized into four main schemas: `core`, `accounting`, `business`, and `audit`.
    *   It includes tables, views, functions (e.g., `core.get_next_sequence_value`), and triggers (e.g., for audit logging and automatic bank balance updates).
    *   Data integrity is enforced through primary keys, foreign keys, `CHECK` constraints, `UNIQUE` constraints, and `NOT NULL` constraints.

## 5. Detailed Component Architecture

### 5.1 Core Components (`app/core/`)

*   **`ApplicationCore` (`application_core.py`)**:
    *   The central hub of the application's backend.
    *   Instantiated once by `app.main.Application`.
    *   Initializes and provides access to all Manager and Service instances, effectively acting as a service locator and facilitating dependency injection.
    *   Holds a reference to the global `ConfigManager` and `DatabaseManager`.
    *   Manages critical application lifecycle events like startup (initializing DB connections, loading services/managers) and shutdown.
    *   Provides properties (e.g., `app_core.customer_manager`, `app_core.journal_service`) for easy access to shared components.

*   **`ConfigManager` (`config_manager.py`)**:
    *   Responsible for loading and providing access to application settings stored in `config.ini`.
    *   Handles platform-specific configuration directory paths.
    *   Creates a default `config.ini` if one doesn't exist.

*   **`DatabaseManager` (`database_manager.py`)**:
    *   Manages the asynchronous database engine (SQLAlchemy `create_async_engine`) and connection pool (using `asyncpg`).
    *   Provides an `asynccontextmanager` (`session()`) for obtaining `AsyncSession` instances, which ensures proper transaction management (commit/rollback).
    *   Critically, within the `session()` context, it sets a session-local variable `app.current_user_id` in the database, which is used by database triggers for auditing purposes.
    *   Can also provide raw `asyncpg` connections if needed.

*   **`SecurityManager` (`security_manager.py`)**:
    *   Handles user authentication using `bcrypt` for password hashing and verification. Includes logic for tracking failed login attempts and account locking.
    *   Implements Role-Based Access Control (RBAC) for authorization. The `has_permission(required_permission_code)` method checks if the `current_user` has the necessary rights.
    *   Provides backend methods for managing `User`, `Role`, and `Permission` entities.
    *   Stores the currently authenticated `User` ORM object in its `current_user` attribute.

*   **`ModuleManager` (`module_manager.py`)**:
    *   A conceptual component intended for potential future dynamic loading of larger application modules. Currently, modules are statically imported and initialized via `ApplicationCore`.

*   **Asynchronous Task Management (Implemented in `app/main.py`)**:
    *   A dedicated Python `threading.Thread` (`_ASYNC_LOOP_THREAD`) hosts a persistent `asyncio` event loop (`_ASYNC_LOOP`), kept separate from the Qt GUI thread.
    *   `schedule_task_from_qt(coroutine)`: A utility function that safely submits coroutines (typically manager methods) from the Qt thread to the asyncio loop thread using `asyncio.run_coroutine_threadsafe`.
    *   `QMetaObject.invokeMethod(target, slot_name, Qt.ConnectionType.QueuedConnection, Q_ARG(type, data))`: Used to marshal results or UI update requests from the asyncio thread back to slots in Qt widgets on the main GUI thread.

### 5.2 Data Models (`app/models/`)
SQLAlchemy ORM models define the application's data structures and their mapping to database tables.

*   **Base (`base.py`)**:
    *   `Base = declarative_base()`: The foundation for all ORM models.
    *   `TimestampMixin`: Adds `created_at` and `updated_at` (with `server_default=func.now()` and `onupdate=func.now()`).
    *   `UserAuditMixin`: Adds `created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'))` and `updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'))`.

*   **Organization**: Models are structured in subdirectories (`core`, `accounting`, `business`, `audit`) mirroring the database schemas. `app/models/__init__.py` aggregates all model imports.

*   **Key Models Examples**:
    *   `core.User`, `core.Role`, `core.Permission`: Define the RBAC structure. Junction tables (`user_roles_table`, `role_permissions_table`) are defined in `user.py`.
    *   `core.CompanySetting`, `core.Configuration`, `core.Sequence`: System-level settings.
    *   `accounting.Account`, `accounting.JournalEntry`, `accounting.JournalEntryLine`, `accounting.FiscalYear`, `accounting.FiscalPeriod`, `accounting.TaxCode`, `accounting.GSTReturn`: Core accounting entities.
    *   `business.Customer`, `business.Vendor`, `business.Product`: Master data for business operations.
    *   `business.SalesInvoice`, `business.PurchaseInvoice`, `business.Payment`: Transactional documents.
    *   `business.BankAccount`, `business.BankTransaction`, `business.BankReconciliation`: Banking module entities.
    *   `audit.AuditLog`, `audit.DataChangeHistory`: For logging.

*   **Style**: Uses SQLAlchemy 2.0 `Mapped` and `mapped_column` syntax with type annotations. Relationships are defined with `relationship()` and `back_populates`.

### 5.3 Data Access Layer (Services - `app/services/`)
Services abstract database interactions, implementing the Repository pattern.

*   **Interfaces (`app/services/__init__.py`)**: Defines generic `IRepository[T, ID]` and specific interfaces (e.g., `IAccountRepository`, `ISalesInvoiceRepository`, `IBankReconciliationRepository`, `IAuditLogRepository`).
*   **Implementations (e.g., `core_services.py`, `account_service.py`, `journal_service.py`, `business_services.py`, `tax_service.py`, `audit_services.py`)**:
    *   Provide concrete implementations for these interfaces.
    *   Encapsulate SQLAlchemy `select`, `insert`, `update`, `delete` logic.
    *   Utilize `DatabaseManager.session()` to perform operations within a transactional context.
    *   Methods often include `get_by_id`, `get_all`, `save` (for add/update), `delete`, and more specific query methods (e.g., `get_all_summary`, `get_by_code`).
    *   `AuditLogService` includes logic to format change summaries for display.

### 5.4 Business Logic Layer (Managers)
Located across `app/accounting/`, `app/business_logic/`, `app/tax/`, `app/reporting/`.

*   **Responsibilities**:
    *   Enforce business rules and validation logic beyond simple DTO constraints.
    *   Orchestrate calls to multiple services to fulfill a use case.
    *   Manage units of work/transactions when multiple database operations are involved (though the session context from `DatabaseManager` often handles the transaction boundary).
    *   Transform data between DTOs (from UI) and ORM objects (for services).
    *   Handle complex calculations (e.g., `TaxCalculator`, invoice totals).
*   **Key Managers**:
    *   `ApplicationCore` initializes instances of these managers and makes them available.
    *   **Accounting**: `ChartOfAccountsManager`, `JournalEntryManager` (handles JE creation, posting, reversal, auto-creation of `BankTransaction` from JEs), `FiscalPeriodManager`, `CurrencyManager`.
    *   **Business Logic**: `CustomerManager`, `VendorManager`, `ProductManager`, `SalesInvoiceManager` (full lifecycle, JE creation, inventory updates), `PurchaseInvoiceManager` (similar to sales), `BankAccountManager`, `BankTransactionManager` (manual entry, CSV import, fetching data for reconciliation), `PaymentManager` (payment recording, allocation, JE posting).
    *   **Tax**: `GSTManager` (F5 preparation, finalization, settlement JE), `TaxCalculator` (line item tax computation).
    *   **Reporting**: `FinancialStatementGenerator`, `ReportEngine` (PDF/Excel generation), `DashboardManager` (aggregates data for KPIs).

### 5.5 Presentation Layer (UI - `app/ui/`)
Built with PySide6 (Qt).

*   **`MainWindow` (`main_window.py`)**: Main application window (`QMainWindow`) using `QTabWidget` for modules. Initializes menus, toolbar, status bar.
*   **Module Widgets (e.g., `DashboardWidget`, `AccountingWidget`, `SalesInvoicesWidget`, `BankingWidget`, `BankReconciliationWidget`, `SettingsWidget`)**: Each primary tab hosts a dedicated widget for a major functional area.
*   **Detail Dialogs (e.g., `AccountDialog`, `SalesInvoiceDialog`, `PaymentDialog`, `CSVImportConfigDialog`)**: `QDialog` subclasses for creating/editing records.
*   **Table Models (e.g., `CustomerTableModel`, `SalesInvoiceTableModel`, `ReconciliationTableModel`, `AuditLogTableModel`)**: Subclasses of `QAbstractTableModel` that interface between backend data (usually lists of DTOs or dictionaries) and `QTableView`s.
*   **Asynchronous Interaction**: UI actions trigger manager methods via `schedule_task_from_qt`. Callbacks (often slots connected via `QMetaObject.invokeMethod`) update the UI upon completion of async tasks.
*   **Shared UI Components (`app/ui/shared/`)**: E.g., `ProductSearchDialog`.
*   **Resources**: Icons and images are loaded from `resources/` either directly or via compiled Qt resources (`resources_rc.py`). `resources.qrc` defines these resources.

### 5.6 Utilities (`app/utils/`)

*   **`pydantic_models.py`**: Defines a comprehensive set of Pydantic DTOs for:
    *   Data validation at API boundaries (UI to Manager).
    *   Clear data contracts between layers.
    *   Common patterns: `BaseData`, `CreateData`, `UpdateData`, `Data` (full representation), `SummaryData`.
    *   Includes `UserAuditData` mixin for DTOs requiring `user_id`.
*   **`json_helpers.py`**: `json_converter` (for `Decimal`, `date`, `datetime` serialization) and `json_date_hook` (for deserialization).
*   **`result.py`**: `Result` class for standardized success/failure reporting from managers/services.
*   **`sequence_generator.py`**: `SequenceGenerator` for creating formatted, sequential document numbers.
*   **`formatting.py`, `converters.py`, `validation.py`**: General-purpose utility functions.

### 5.7 Common (`app/common/`)

*   **`enums.py`**: Defines various Python `Enum` classes (e.g., `ProductTypeEnum`, `InvoiceStatusEnum`, `PaymentTypeEnum`, `JournalTypeEnum`, `BankTransactionTypeEnum`) used for predefined choices and type safety throughout the application.

## 6. Data Architecture

### 6.1 Database System
*   **PostgreSQL (version 14+)**: Provides robust transactional capabilities, data integrity features, and support for advanced SQL constructs.

### 6.2 Schema Organization
Defined in `scripts/schema.sql`. The database is structured into four main schemas:
*   **`core`**: System-wide tables (users, roles, permissions, company settings, app configuration, sequences).
*   **`accounting`**: Core accounting data (chart of accounts, fiscal periods/years, journal entries, currencies, tax codes, GST returns).
*   **`business`**: Operational data (customers, vendors, products, sales/purchase invoices, payments, bank accounts, bank transactions, bank reconciliations).
*   **`audit`**: Audit trails (`audit_log` for actions, `data_change_history` for field-level changes).

Key tables like `business.bank_reconciliations` and updated fields in `business.bank_accounts` and `business.bank_transactions` support the bank reconciliation feature.

### 6.3 Data Integrity
*   Enforced via PostgreSQL constraints (PK, FK, CHECK, UNIQUE, NOT NULL).
*   Database triggers automate audit logging and `bank_accounts.current_balance` updates.
*   Pydantic DTOs provide validation at the application layer before data reaches business logic.
*   Business logic managers perform further contextual validation.

### 6.4 ORM and DTOs
*   **SQLAlchemy 2.0+ (Async)**: Used for ORM, with models defined in `app/models/`.
*   **Pydantic DTOs (`app/utils/pydantic_models.py`)**: Used for data transfer between UI and managers, providing validation and clear data contracts.

## 7. Key Technologies & Frameworks
*   **Python**: Core programming language (version >=3.9).
*   **PySide6**: For the desktop GUI (Qt 6 bindings).
*   **PostgreSQL**: Relational database.
*   **SQLAlchemy (Async ORM)**: Database interaction.
*   **asyncpg**: Asynchronous PostgreSQL driver.
*   **Pydantic V2**: Data validation and settings management.
*   **bcrypt**: Password hashing.
*   **reportlab, openpyxl**: PDF and Excel report generation.
*   **Poetry**: Dependency management and packaging.
*   **pytest, pytest-asyncio, pytest-cov**: For testing.
*   **Black, Flake8, MyPy**: Code formatting, linting, and type checking.

## 8. Design Patterns Used
*   Layered Architecture
*   Model-View-Controller (MVC) / Model-View-Presenter (MVP) - loosely followed
*   Repository Pattern (Services)
*   Data Transfer Object (DTO)
*   Result Object (`app/utils/result.py`)
*   Observer Pattern (Qt Signals/Slots)
*   Dependency Injection (via `ApplicationCore`)
*   Singleton (conceptually for `ApplicationCore` and global managers/services accessed through it)
*   Mixin (for ORM models: `TimestampMixin`, `UserAuditMixin`)

## 9. Asynchronous Processing Model
The application uses a hybrid threading and asyncio model to keep the UI responsive:
1.  A global `asyncio` event loop runs in a dedicated background thread (`_ASYNC_LOOP_THREAD` in `app/main.py`).
2.  Qt UI events trigger actions that may involve I/O-bound or CPU-intensive backend work.
3.  These tasks are defined as `async` coroutines (usually manager methods).
4.  The UI thread calls `schedule_task_from_qt(coroutine)` to submit the coroutine to the dedicated asyncio loop.
5.  Results or UI update instructions are passed back to the Qt main thread using `QMetaObject.invokeMethod`, ensuring thread-safe UI updates.
This prevents the GUI from freezing during database operations or complex calculations.

## 10. Configuration Management
*   Application settings (database connection, UI preferences) are managed by `ConfigManager`.
*   Configuration is read from `config.ini` in a platform-specific user directory.
*   A default `config.ini` is created if one is not found.

## 11. Security Architecture
*   **Authentication**: `SecurityManager` handles user login with `bcrypt` hashed passwords.
*   **Authorization (RBAC)**: `SecurityManager` uses a system of `User`, `Role`, and `Permission` ORM models to enforce access control. `has_permission()` checks are used to guard sensitive operations.
*   **Audit Logging**: Database triggers on key tables automatically log changes to `audit.audit_log` and `audit.data_change_history`. The `DatabaseManager` sets the `app.current_user_id` PostgreSQL session variable, which is captured by these triggers. A UI for viewing audit logs is provided in the Settings module.

## 12. Deployment & Initialization
*   The application is intended to be run from source using Poetry.
*   Database initialization is handled by `scripts/db_init.py`, which:
    *   Creates the database (if it doesn't exist).
    *   Applies the schema from `scripts/schema.sql` (current version: 1.0.5).
    *   Seeds initial data from `scripts/initial_data.sql` (roles, permissions, default user, system accounts, etc.).
*   The main application is launched via `poetry run sg_bookkeeper` which calls `app.main:main`.

## 13. Resource Management
*   Static assets like icons (`.svg`) and images (`.png`) are stored in the `resources/` directory.
*   A Qt resource file (`resources.qrc`) compiles these assets into `app/resources_rc.py`.
*   The application attempts to load resources from the compiled module first (e.g., `:/icons/add.svg`), falling back to direct file paths if `resources_rc.py` is not available.

## 14. Project Structure Overview
(Refer to the Project Structure section in the README.md for a visual layout)
The main directories include:
*   `app/`: Contains all application source code, further divided into:
    *   `core/`, `models/`, `services/`, `accounting/` (managers), `business_logic/` (managers), `tax/` (managers), `reporting/` (managers), `ui/` (by module), `utils/`, `common/`.
*   `scripts/`: Database setup and utility scripts.
*   `data/`: Seed data files (CSV, JSON templates).
*   `resources/`: Static assets like icons and images.
*   `tests/`: Automated tests, organized into `unit/`, `integration/`, `ui/`.

This architecture provides a solid foundation for the SG Bookkeeper application, balancing separation of concerns with the practical needs of a desktop application.

---
https://drive.google.com/file/d/1-vPle_bsfW5q1aXJ4JI9VB5cOYY3f7oU/view?usp=sharing, https://drive.google.com/file/d/14hkYD6mD9rl8PpF-MsJD9nZAy-1sAr0T/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%2216tABsm1Plf_0fhtruoJyyxobBli3e8-7%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/19T9JbSrHCuXhHpzFMUh4Ti_0sDPDycSW/view?usp=sharing, https://drive.google.com/file/d/1D7GYodcMgZv3ROPPRJTYX0g9Rrsq8wJD/view?usp=sharing, https://drive.google.com/file/d/1EGOoM0TGqPgNBJzwxKdVO2u331Myhd4b/view?usp=sharing, https://drive.google.com/file/d/1Ivh39pjoqQ9z4_oj7w7hWc0zOje2-Xjb/view?usp=sharing, https://drive.google.com/file/d/1LzMu08SqY6E5ZuvISa4BsEHxatVPE9g_/view?usp=sharing, https://drive.google.com/file/d/1QyS0xlh6owfMif6KMlyXmE2Zx2hmcdza/view?usp=sharing, https://drive.google.com/file/d/1Y9orpJ67I0XwezEBeUhyJs03DdjkAMhH/view?usp=sharing, https://drive.google.com/file/d/1ZZODHjv2AX2Pn1cRh_0CJDTSzXRGjAt_/view?usp=sharing, https://drive.google.com/file/d/1bSRRtsWeJI9djXTDZTZTjZxnsWS3cvsV/view?usp=sharing, https://drive.google.com/file/d/1cp5LuyXlsbaa_wFSiIMxRlBFSro8qhXq/view?usp=sharing, https://drive.google.com/file/d/1ghGjh0MtEZSDVftjVx583ocaaCDK2j9X/view?usp=sharing, https://drive.google.com/file/d/1mbj5C_Pqa-lbGFf4obvSnpdGm-ALui7y/view?usp=sharing, https://drive.google.com/file/d/1uKfTNXg8Oaes7aGaoaPB6klSZzywizh9/view?usp=sharing, https://drive.google.com/file/d/1vTPAoLcEetjBj17-5nTa_Z6RS7ND5Wmz/view?usp=sharing, https://drive.google.com/file/d/1xbA8X7irZHUayYcfOWWfi4oWm18hFDo2/view?usp=sharing

