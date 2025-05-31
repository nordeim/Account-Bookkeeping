# Technical Design Specification Document: SG Bookkeeper (v11.0)

**Version:** 11.0
**Date:** 2025-05-30

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version 11.0, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities. This version details the implementation of **Draft Purchase Invoice Management (Backend Logic and UI - List View & Dialog)** and **Enhanced PDF/Excel Export Formatting for Balance Sheet & Profit/Loss Reports**. These build upon previously documented features like full Sales Invoicing, User/Role Management, Customer/Vendor/Product Management, GST F5 workflow, and Financial Reporting UI options. This document serves as a comprehensive guide for ongoing development, feature enhancement, testing, and maintenance.

### 1.2 Scope
This TDS covers the following aspects of the SG Bookkeeper application:
-   System Architecture: UI, business logic, data access layers, and asynchronous processing.
-   Database Schema: Details and organization as defined in `scripts/schema.sql`.
-   Key UI Implementation Patterns: `PySide6` interactions with the asynchronous backend, DTO usage.
-   Core Business Logic: Component structures and interactions for implemented modules.
-   Data Models (SQLAlchemy ORM) and Data Transfer Objects (Pydantic DTOs).
-   Security Implementation: Authentication, Role-Based Access Control (RBAC), and audit mechanisms.
-   Deployment and Initialization procedures.
-   Current Implementation Status: Highlighting the features implemented up to this version.

### 1.3 Intended Audience
-   Software Developers: For implementation, feature development, and understanding system design.
-   QA Engineers: For comprehending system behavior, designing effective test cases, and validation.
-   System Administrators: For deployment strategies, database setup, and maintenance.
-   Technical Project Managers: For project oversight, planning, and resource allocation.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application engineered with Python, utilizing PySide6 for its graphical user interface and PostgreSQL for robust data storage. It is designed to provide comprehensive accounting solutions for Singaporean Small to Medium-sized Businesses (SMBs). Key features include a full double-entry bookkeeping system, Singapore-specific GST management (including F5 return preparation), interactive financial reporting with enhanced export options, modules for managing essential business operations (Customers, Vendors, Products/Services, full Sales Invoicing lifecycle, and Purchase Invoice draft management with list views and dialogs), and comprehensive system administration for Users, Roles, and Permissions. The application emphasizes data integrity, compliance with local accounting standards, and user-friendliness for business owners and accounting professionals. Core data structures are defined in `scripts/schema.sql`, and initial seeding is performed by `scripts/initial_data.sql`.

### 1.5 Current Implementation Status
As of version 11.0, the following key features are implemented:
*   **Core Accounting**: Chart of Accounts (CRUD UI), General Journal (CRUD UI, Posting, Reversal), Fiscal Year/Period Management (UI in Settings).
*   **Tax Management**: GST F5 Return data preparation and finalization (UI and backend logic), `TaxCalculator` for line item tax.
*   **Business Operations**:
    *   Customer Management: Full CRUD and listing UI.
    *   Vendor Management: Full CRUD and listing UI.
    *   Product/Service Management: Full CRUD and listing UI for Inventory, Non-Inventory, and Service types.
    *   Sales Invoicing: Full lifecycle - Draft CRUD, List View, Posting with Journal Entry creation, "Save & Approve" in dialog.
    *   Purchase Invoicing: Full Draft Management - Backend logic for creating/updating drafts, UI Dialog (`PurchaseInvoiceDialog`) for draft CRUD with calculations, and UI List View (`PurchaseInvoicesWidget`) with filtering. Posting logic is a stub.
*   **Reporting**:
    *   Balance Sheet & Profit/Loss: On-screen tree view, enhanced PDF/Excel export (custom formatting, headers, footers), UI options for comparative periods and zero-balance accounts.
    *   Trial Balance & General Ledger: On-screen table view, basic PDF/Excel export.
*   **System Administration**:
    *   Full User and Role Management UI in Settings: User CRUD, password management, role assignment. Role CRUD, permission assignment to roles.
    *   Backend `SecurityManager` supports these operations.
*   **Database**: Schema defined in `scripts/schema.sql` including audit triggers, views, and functions. `db_init.py` script for setup.
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
|  PurchaseInvoiceManager, SecurityManager, GSTManager, etc.])   |
| Encapsulates Business Rules, Validation, Orchestrates Services  |
+-----------------------------------------------------------------+
      ^                         | (Service Calls, ORM Objects/DTOs)
      | (Service Results)       | (SQLAlchemy Async Operations)
      v                         v
+-----------------------------------------------------------------+
|                       Data Access Layer                         |
| (DatabaseManager, Services [e.g., SalesInvoiceService,         |
|  PurchaseInvoiceService, AccountService], SQLAlchemy Models)   |
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
-   **Presentation Layer**: Manages all user interactions and data display, built with PySide6.
-   **Business Logic Layer**: Contains the application's core rules, validation, and workflow orchestration through managers and `ApplicationCore`.
-   **Data Access Layer**: Abstracts database operations using services (implementing repository pattern) and SQLAlchemy ORM.
-   **Database Layer**: PostgreSQL database storing all application data as per the defined schema.

### 2.2 Component Architecture

#### 2.2.1 Core Components (`app/core/`)
-   **`Application` (`app/main.py`)**: Subclass of `QApplication`. Manages the Qt event loop and bridges to a dedicated `asyncio` event loop running in a separate thread for background tasks. Handles splash screen and initial application setup.
-   **`ApplicationCore` (`app/core/application_core.py`)**: The central orchestrator. Initializes and provides access to all services and managers (e.g., `SecurityManager`, `SalesInvoiceManager`, `PurchaseInvoiceManager`). Manages application startup and shutdown routines.
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
-   **Business Services (`business_services.py`)**: `CustomerService`, `VendorService`, `ProductService`, `SalesInvoiceService`, `PurchaseInvoiceService`.

#### 2.2.4 Managers (Business Logic Layer - `app/accounting/`, `app/tax/`, `app/business_logic/`, `app/reporting/`)
Managers encapsulate complex business workflows, validation logic, and coordinate operations between multiple services and DTOs.
-   **Accounting Managers**: `ChartOfAccountsManager`, `JournalEntryManager`, `FiscalPeriodManager`, `CurrencyManager`.
-   **Tax Managers**: `GSTManager`, `TaxCalculator`. (`IncomeTaxManager`, `WithholdingTaxManager` are stubs).
-   **Reporting Managers**: `FinancialStatementGenerator`, `ReportEngine`.
-   **Business Logic Managers**: `CustomerManager`, `VendorManager`, `ProductManager`, `SalesInvoiceManager`, `PurchaseInvoiceManager`.
    -   `SalesInvoiceManager`: Handles full lifecycle for sales invoices including draft CRUD and posting with JE creation.
    -   `PurchaseInvoiceManager`: Handles draft CRUD for purchase invoices, including validation and calculations. Posting logic is a stub.

#### 2.2.5 User Interface (Presentation Layer - `app/ui/`)
-   **`MainWindow` (`app/ui/main_window.py`)**: The main application window, using a `QTabWidget` to host different functional modules. It includes menus, a toolbar, and a status bar.
-   **Module Widgets**: Each tab in `MainWindow` hosts a primary widget for a module:
    *   `DashboardWidget` (stub)
    *   `AccountingWidget` (hosts `ChartOfAccountsWidget`, `JournalEntriesWidget`)
    *   `SalesInvoicesWidget` (list view for sales invoices)
    *   `PurchaseInvoicesWidget` (list view for purchase invoices)
    *   `CustomersWidget`, `VendorsWidget`, `ProductsWidget` (list views for respective entities)
    *   `BankingWidget` (stub)
    *   `ReportsWidget` (UI for GST F5 and Financial Statements)
    *   `SettingsWidget` (hosts sub-tabs for Company Info, Fiscal Years, User Management, Role Management)
-   **Detail Widgets & Dialogs**: Specific screens for data entry, editing, or viewing details (e.g., `AccountDialog`, `SalesInvoiceDialog`, `PurchaseInvoiceDialog`, `UserDialog`, `RoleDialog`). These dialogs typically interact with their respective managers for data operations.
-   **Table Models**: Subclasses of `QAbstractTableModel` (e.g., `SalesInvoiceTableModel`, `PurchaseInvoiceTableModel`) are used to provide data to `QTableView` instances in list views.

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

## 3. Data Architecture

### 3.1 Database Schema Overview
The PostgreSQL database schema is foundational to the application and is meticulously defined in `scripts/schema.sql`. It is organized into four distinct schemas:
-   **`core`**: Contains system-level tables such as `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `company_settings`, `configuration` (for key-value app settings), and `sequences` (for document numbering).
-   **`accounting`**: Houses all core accounting tables, including `accounts`, `account_types`, `fiscal_years`, `fiscal_periods`, `journal_entries`, `journal_entry_lines`, `currencies`, `exchange_rates`, `tax_codes`, `gst_returns`, `budgets`, `budget_details`, `recurring_patterns`, `dimensions`, and `withholding_tax_certificates`.
-   **`business`**: Includes tables for business operational data: `customers`, `vendors`, `products`, `sales_invoices`, `sales_invoice_lines`, `purchase_invoices`, `purchase_invoice_lines`, `inventory_movements`, `bank_accounts`, `bank_transactions`, `payments`, and `payment_allocations`.
-   **`audit`**: Comprises tables for tracking changes: `audit_log` (for action summaries) and `data_change_history` (for field-level changes). These are primarily populated by database triggers defined in `schema.sql`.

The schema enforces data integrity through primary keys, foreign keys, `CHECK` constraints, `UNIQUE` constraints, and `NOT NULL` constraints. Indexes are strategically placed for query performance.

### 3.2 SQLAlchemy ORM Models (`app/models/`)
SQLAlchemy ORM models provide the Python object-oriented interface to the database tables.
-   Models are organized into subdirectories under `app/models/` that mirror the database schema structure (e.g., `app/models/core/user.py`, `app/models/accounting/account.py`).
-   All models inherit from a common `Base` (from `sqlalchemy.orm.declarative_base()`).
-   A `TimestampMixin` provides `created_at` and `updated_at` columns with automatic timestamp management.
-   Most transactional tables include `created_by_user_id` and `updated_by_user_id` fields, linking to `core.users.id`, to support auditability.
-   Relationships between models (e.g., one-to-many, many-to-many) are defined using SQLAlchemy's `relationship()` construct, typically with `back_populates` for bidirectional navigation.
-   The Mapped ORM style (SQLAlchemy 2.0+) with type hints (`Mapped`, `mapped_column`) is used for clearer model definitions.

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
Pydantic models serve as DTOs for validating and structuring data passed between application layers, especially from the UI to managers.
-   Each major entity typically has a set of DTOs:
    *   `BaseData`: Common fields.
    *   `CreateData`: Fields required for creating a new entity, often including `user_id` from a `UserAuditData` mixin.
    *   `UpdateData`: Fields allowed for updating an existing entity, usually including `id` and `user_id`.
    *   `Data` (or entity name): Full representation of an entity, often used for returning detailed data.
    *   `SummaryData`: A slimmed-down version for list views.
-   DTOs include field type validations, constraints (e.g., `min_length`, `max_length`, `ge`, `le`), and custom validators (`@validator`, `@root_validator`) for more complex business rule checks (e.g., password confirmation, conditional field requirements).
-   Enums from `app/common/enums.py` are used for fields with predefined choices (e.g., `ProductTypeEnum`, `InvoiceStatusEnum`).

### 3.4 Data Access Layer Interfaces (Services - `app/services/__init__.py`)
While a generic `IRepository` interface is defined, individual service classes often directly implement the required data access methods for their specific ORM model(s) without strictly adhering to all methods of a generic interface. They provide a clear contract for data operations. Examples:
-   `IAccountRepository`: Defines methods like `get_by_code`, `get_account_tree`.
-   `ISalesInvoiceRepository`: Defines methods like `get_by_invoice_no`, `get_all_summary`.
-   `IPurchaseInvoiceRepository`: Defines methods like `get_by_internal_ref_no`, `get_all_summary`.

## 4. Module and Component Specifications

This section details the specifications for key implemented modules.

### 4.1 Core Accounting Module (`app/accounting/`, `app/ui/accounting/`)
-   **Chart of Accounts**: Allows users to define and manage a hierarchical chart of accounts.
    -   Manager: `ChartOfAccountsManager` (validation, CRUD orchestration).
    -   Service: `AccountService` (DB operations for `Account` model).
    -   UI: `ChartOfAccountsWidget` (tree view), `AccountDialog` (add/edit).
-   **Journal Entries**: Facilitates manual journal entry creation and management.
    -   Manager: `JournalEntryManager` (creation, validation, posting, reversal, recurring entry generation).
    -   Service: `JournalService` (DB operations for `JournalEntry`, `JournalEntryLine`).
    -   UI: `JournalEntriesWidget` (list view), `JournalEntryDialog` (add/edit/view).
-   **Fiscal Period Management**: Allows setup and control of fiscal years and periods.
    -   Manager: `FiscalPeriodManager` (creation of years and auto-generation of monthly/quarterly periods, closing/reopening).
    -   Services: `FiscalYearService`, `FiscalPeriodService`.
    -   UI: Integrated into `SettingsWidget`. `FiscalYearDialog` for adding new fiscal years.

### 4.2 Tax Management Module (`app/tax/`, `app/ui/reports/`)
-   **GST Management**:
    *   Manager: `GSTManager` (prepares `GSTReturnData` DTO from posted JEs, saves draft `GSTReturn` ORM, finalizes return with settlement JE creation via `JournalEntryManager`).
    *   Service: `TaxCodeService`, `GSTReturnService`.
    *   UI: GST F5 preparation section in `ReportsWidget`.
-   **Tax Calculation**:
    *   `TaxCalculator` service: Provides methods (`calculate_line_tax`) to compute tax amounts based on net amount and tax code. Used by invoice managers.

### 4.3 Business Operations Modules (`app/business_logic/`, `app/ui/.../`)
-   **Customer, Vendor, Product/Service Management**: Full CRUD capabilities and list views with filtering.
    -   Managers: `CustomerManager`, `VendorManager`, `ProductManager`.
    -   Services: `CustomerService`, `VendorService`, `ProductService`.
    -   UI: `CustomersWidget`, `VendorsWidget`, `ProductsWidget`, and respective dialogs.
-   **Sales Invoicing Module**: Supports the full sales invoice lifecycle.
    -   Manager: `SalesInvoiceManager` (validates data, calculates totals using `TaxCalculator`, creates/updates drafts via `SalesInvoiceService`, posts invoices including JE creation via `JournalEntryManager`).
    -   Service: `SalesInvoiceService`.
    -   UI: `SalesInvoicesWidget` (list view), `SalesInvoiceDialog` (add/edit draft, save & approve for posting).
-   **Purchase Invoicing Module**: Supports draft management for purchase invoices.
    -   Manager: `PurchaseInvoiceManager` (validates data including duplicate vendor invoice number check, calculates totals using `TaxCalculator`, creates/updates drafts via `PurchaseInvoiceService`. Posting is a stub).
    -   Service: `PurchaseInvoiceService`.
    -   UI: `PurchaseInvoicesWidget` (list view), `PurchaseInvoiceDialog` (add/edit draft).

### 4.4 System Administration Modules (`app/core/security_manager.py`, `app/ui/settings/`)
-   **User Management**: Allows administrators to manage user accounts.
    -   Manager: `SecurityManager` handles backend logic.
    -   UI: `UserManagementWidget` and `UserDialog` (for details & role assignment), `UserPasswordDialog`.
-   **Role & Permission Management**: Enables administrators to define roles and assign permissions.
    -   Manager: `SecurityManager` handles backend logic.
    -   UI: `RoleManagementWidget` and `RoleDialog` (for role details & permission assignment via a multi-select list).

### 4.5 Reporting Module (`app/reporting/`, `app/ui/reports/`)
-   **Financial Statements**: Generation and export of key financial reports.
    -   Manager: `FinancialStatementGenerator` (prepares data for BS, P&L, TB, GL). `ReportEngine` (handles PDF/Excel export with enhanced formatting for BS/P&L).
    -   UI: Financial Statements tab in `ReportsWidget` with various options and display views.

## 5. User Interface Implementation (`app/ui/`)

-   **Main Window (`MainWindow`)**: Serves as the primary application container with a tabbed interface for accessing different modules.
-   **Module Widgets**: Each major functional area (e.g., Sales, Purchases, Reports, Settings) has a dedicated widget hosted in a tab. These widgets typically contain toolbars, filter areas, and data display areas (often `QTableView` or `QTreeView`).
-   **Dialogs**: Used for creating new records or editing existing ones (e.g., `SalesInvoiceDialog`, `AccountDialog`). They feature forms for data input and interact with managers for data persistence.
-   **Table Models**: Custom `QAbstractTableModel` subclasses are used to feed data into `QTableView`s, providing flexibility in data display and formatting.
-   **Asynchronous Interaction**: UI elements initiate backend operations (manager calls) via `schedule_task_from_qt`. Callbacks or `QMetaObject.invokeMethod` are used to update the UI with results from these async tasks, ensuring the UI remains responsive.
-   **Data Validation**: Input validation is primarily handled by Pydantic DTOs (on data collection from UI) and then by manager classes before database operations. UI provides immediate feedback for some simple validation errors.
-   **Resource Management**: Icons and images are loaded from `resources/` directory, preferentially using a compiled Qt resource file (`app/resources_rc.py`) if available.

## 6. Security Considerations
-   **Authentication**: User login is handled by `SecurityManager` using `bcrypt` for password hashing. Failed login attempts are tracked, and accounts can be locked.
-   **Authorization (RBAC)**: A granular permission system is in place. Permissions are defined and can be assigned to roles. Users are assigned roles. `SecurityManager.has_permission()` is used to check if the current user is authorized to perform an action. The "Administrator" role has all permissions by default and is protected.
-   **Audit Trails**: Comprehensive audit logging is implemented at the database level using triggers. The `DatabaseManager` sets a session variable `app.current_user_id` which is captured by these triggers to record who made the changes. Audit data is stored in `audit.audit_log` and `audit.data_change_history`.
-   **Data Integrity**: Enforced through database constraints, DTO validation, and business logic validation in managers.

## 7. Database Access Implementation
-   **`DatabaseManager`**: Manages the SQLAlchemy async engine and `asyncpg` connection pool. It is responsible for providing database sessions.
-   **Services (Repository Pattern)**: Service classes (e.g., `AccountService`, `SalesInvoiceService`) encapsulate data access logic for specific ORM models. They use SQLAlchemy's async session to perform CRUD operations and execute queries. Common methods include `get_by_id`, `get_all_summary`, `save`.
-   **ORM Models (`app/models/`)**: SQLAlchemy model classes define the mapping between Python objects and database tables. Relationships, constraints, and mixins (`TimestampMixin`) are defined here.
-   **Transactions**: Database operations that involve multiple steps (e.g., saving an invoice and its lines, posting an invoice and creating a JE) are typically handled within a single database session managed by `async with db_manager.session():`, ensuring atomicity. Manager methods often orchestrate these transactional units.

## 8. Deployment and Installation
-   **Prerequisites**: Python 3.9+, PostgreSQL 14+, Poetry.
-   **Setup**:
    1.  Clone repository.
    2.  Install dependencies using `poetry install`.
    3.  Configure database connection in `config.ini` (located in a platform-specific user config directory).
    4.  Initialize the database using `poetry run sg_bookkeeper_db_init --user <pg_admin_user> ...`. This script executes `scripts/schema.sql` (DDL) and `scripts/initial_data.sql` (seeding).
-   **Execution**: Run `poetry run sg_bookkeeper`.
-   Refer to `README.md` and `deployment_guide.md` for more detailed installation and setup instructions.

## 9. Conclusion
SG Bookkeeper version 11.0 represents a significant step towards a feature-complete accounting application for Singaporean SMBs. The implementation of draft Purchase Invoice management (including a list view UI and a fully functional dialog for CRUD operations) and enhanced financial report exports (Balance Sheet, Profit & Loss) are key advancements. These build upon a solid foundation of core accounting, comprehensive business entity management, full sales invoicing capabilities, and robust user/role administration. The architecture remains scalable and maintainable, leveraging asynchronous operations for a responsive user experience. The next major steps will likely focus on completing the Purchase Invoicing module by implementing posting logic, further enhancing reporting capabilities for other statement types, and potentially beginning work on other transactional modules like Payments or Banking.

---
https://drive.google.com/file/d/10NQZe3AATtiodERb3NEjPFqGN_RwqV8V/view?usp=sharing, https://drive.google.com/file/d/13I6IC_fPXgIu51NJdpl4hSud70xeNksT/view?usp=sharing, https://drive.google.com/file/d/13UTU4WGBLEji-2V1_c1Vm0CU5yjAAtEl/view?usp=sharing, https://drive.google.com/file/d/16h5hgHm8_8eJHIcv3IlqY9EOwelrur25/view?usp=sharing, https://drive.google.com/file/d/1AM4pzDhd3lo5VY3qsEm6fVsw_Z7iw0ht/view?usp=sharing, https://drive.google.com/file/d/1H7adg-9W50pczl6941vi2oe2OioCl75v/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221Jek1dhLzt3_VmBaCpltwEgVXlLziuPfh%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1MAxpqINIn0DhFCe2Q5izaLTiYqPsdVkc/view?usp=sharing, https://drive.google.com/file/d/1Nm5wabOgWCtVKR7AfHNxS-qTAjaJpaWV/view?usp=sharing, https://drive.google.com/file/d/1O4_3WqbLhXuJwUMBWWglGwoPWRVBCXD9/view?usp=sharing, https://drive.google.com/file/d/1QdQyCh2708zFoDCCGTqMerLXPRKwMd_y/view?usp=sharing, https://drive.google.com/file/d/1QiCI5C2uzVrIJ4TLqOt8jmnG8xYOLk3L/view?usp=sharing, https://drive.google.com/file/d/1R2DblOk4TOXxLfbaMnxryzHEC_xGqf5I/view?usp=sharing, https://drive.google.com/file/d/1U_8wYmPi1gYywlN5EUMsnOFY6miX5NzI/view?usp=sharing, https://drive.google.com/file/d/1VTDvkd0euAJxI03-B_wqlaJWL0gjb1Qo/view?usp=sharing, https://drive.google.com/file/d/1VqKCTYOGp4kvWbPdDMkXxXfLcaOto2e9/view?usp=sharing, https://drive.google.com/file/d/1_IJiDhrxb8h4ZoDHPRHN4TTHHNmoWC8c/view?usp=sharing, https://drive.google.com/file/d/1a3ku0WZ4NS1nuZ_2RXgBLNpE0Hp77Qaa/view?usp=sharing, https://drive.google.com/file/d/1cFh9KYlyBfh_asfkvW2TskFgf1cMbBVb/view?usp=sharing, https://drive.google.com/file/d/1dbPxe6ZDKaJZZ3fRNENg1IkP_tsm3HMI/view?usp=sharing, https://drive.google.com/file/d/1hC-uzD9MLhtizqXPKAwOVfeEBYLOE8mG/view?usp=sharing, https://drive.google.com/file/d/1hoITa2HMGuSqh12ftIsU0EGlrGgiDivM/view?usp=sharing, https://drive.google.com/file/d/1ltHzvIRZN0ai7DwQkOaWDuGgUuB2jtXo/view?usp=sharing, https://drive.google.com/file/d/1qgUPpEvs8vFi7n4Z1ynb1k-mLcHbGdTC/view?usp=sharing, https://drive.google.com/file/d/1rghvbIqkwirHLtF1Vq9aeuyVWzDzcpEM/view?usp=sharing, https://drive.google.com/file/d/1sCd6qSpbRL2lkze0Tswv7cuygQVyVTtn/view?usp=sharing, https://drive.google.com/file/d/1tWGlfoC-ALwANG5z-52tK0VsUJpLpSTa/view?usp=sharing, https://drive.google.com/file/d/1tsYe-fhVo00JwkBq5C3rT-D0Ixh1P_J1/view?usp=sharing, https://drive.google.com/file/d/1uwTPQsCijSJXdFTNzFnP3ggajVllZFQi/view?usp=sharing
