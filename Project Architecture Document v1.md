## SG Bookkeeper: Architectural Understanding (Based on Current Codebase Review - TDS v11 alignment)

**Version:** 2.0 (Internal CodeNavigator Version)
**Date:** 2025-05-30

### 1. Introduction

This document provides a comprehensive architectural overview of the SG Bookkeeper application, reflecting its current state as determined by a detailed review of the provided codebase. SG Bookkeeper is a cross-platform desktop application developed with Python, PySide6, and PostgreSQL, aimed at providing Singaporean Small to Medium-sized Businesses (SMBs) with a robust, compliant, and user-friendly accounting solution. Key functionalities include double-entry bookkeeping, GST management, business operations modules (Customers, Vendors, Products, Sales & Purchase Invoicing), detailed financial reporting with enhanced export capabilities, and comprehensive system administration for users and roles.

### 2. System Architecture

#### 2.1 High-Level Architectural Diagram

The application employs a layered architecture designed for modularity, maintainability, and separation of concerns.

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

#### 2.2 Layer Descriptions

*   **Presentation Layer (UI - `app/ui/`)**:
    *   Built entirely with **PySide6 (v6.9.0+)**.
    *   `MainWindow` (`app/ui/main_window.py`) serves as the main application shell, hosting a `QTabWidget` for different functional modules.
    *   **Module Widgets** (e.g., `SalesInvoicesWidget`, `PurchaseInvoicesWidget`, `ReportsWidget`, `SettingsWidget`) represent top-level UI for each module tab.
    *   **Detail Widgets & Dialogs** (e.g., `SalesInvoiceDialog`, `PurchaseInvoiceDialog`, `AccountDialog`, `UserDialog`, `RoleDialog`) are used for data entry, editing, and viewing specific records.
    *   **Table Models** (`QAbstractTableModel` subclasses like `SalesInvoiceTableModel`, `PurchaseInvoiceTableModel`) provide data to `QTableView`s for list displays.
    *   User interactions trigger actions that often involve asynchronous calls to the Business Logic Layer. UI updates resulting from these backend operations are marshaled back to the Qt main thread.

*   **Business Logic Layer (Managers - `app/core/`, `app/accounting/`, `app/business_logic/`, `app/tax/`, `app/reporting/`)**:
    *   `ApplicationCore` (`app/core/application_core.py`): Central orchestrator, initializes and provides access to all managers and services.
    *   **Managers** (e.g., `SalesInvoiceManager`, `PurchaseInvoiceManager`, `SecurityManager`, `JournalEntryManager`, `GSTManager`, `FinancialStatementGenerator`, `ReportEngine`) encapsulate the primary business rules, validation logic, and workflow orchestration for their respective domains.
    *   Managers use **Pydantic DTOs** (`app/utils/pydantic_models.py`) for receiving data from the UI and returning structured results.
    *   They interact with one or more **Services** from the Data Access Layer to perform data persistence and retrieval.
    *   Complex calculations (e.g., invoice totals, tax computations via `TaxCalculator`) are handled here.
    *   Most manager methods involving I/O are `async`.

*   **Data Access Layer (Services - `app/services/`)**:
    *   `DatabaseManager` (`app/core/database_manager.py`): Manages asynchronous database connections (using SQLAlchemy's async engine and `asyncpg` pool) and session lifecycles. It also sets `app.current_user_id` as a PostgreSQL session variable for audit triggers.
    *   **Services** (e.g., `SalesInvoiceService`, `PurchaseInvoiceService`, `AccountService`, `ProductService`, `CoreServices`) implement repository patterns. They provide an abstraction layer over direct SQLAlchemy ORM queries, handling CRUD operations and complex data fetching for specific ORM models.
    *   **SQLAlchemy ORM Models** (`app/models/`): Define the Python object mapping to database tables. Organized into subdirectories (`core`, `accounting`, `business`, `audit`) mirroring the database schemas.

*   **Database Layer (PostgreSQL - `scripts/`)**:
    *   **PostgreSQL (v14+)** is the chosen relational database.
    *   The entire database schema is defined in `scripts/schema.sql`, which includes:
        *   Four main schemas: `core`, `accounting`, `business`, `audit`.
        *   Tables for all application entities with appropriate constraints and indexes.
        *   Views for aggregated data (e.g., `accounting.trial_balance`, `business.customer_balances`).
        *   Stored functions (e.g., `core.get_next_sequence_value` for document numbering).
        *   Triggers (e.g., `audit.log_data_change_trigger_func`) for populating `audit.audit_log` and `audit.data_change_history`.
    *   `scripts/initial_data.sql` seeds the database with essential default data (roles, permissions, system users, currencies, tax codes, sequences, default configurations).
    *   `scripts/db_init.py` is used to initialize the database by executing `schema.sql` and then `initial_data.sql`.

#### 2.3 Core Components (`app/core/`)

*   **`ApplicationCore` (`app/core/application_core.py`)**:
    *   Instantiated by `app.main.Application`.
    *   Initializes all service and manager instances during its `startup()` method, injecting necessary dependencies (like `DatabaseManager` or other services into managers).
    *   Provides access to these services and managers via properties (e.g., `app_core.sales_invoice_manager`).
    *   Manages global application state like `current_user` (via `SecurityManager`).
    *   Handles application shutdown sequence by calling `db_manager.close_connections()`.

*   **`DatabaseManager` (`app/core/database_manager.py`)**:
    *   Configured via `ConfigManager`.
    *   Initializes and manages the SQLAlchemy async engine (`create_async_engine`) and `asyncpg` connection pool.
    *   Provides an `asynccontextmanager` for database sessions (`session()`) ensuring commits or rollbacks.
    *   Crucially, within the `session()` context manager, it attempts to set the `app.current_user_id` PostgreSQL session variable using `SET LOCAL app.current_user_id = ...;`. This is vital for the audit triggers in `schema.sql` to correctly attribute data changes to the logged-in user.
    *   Provides methods for raw SQL execution if needed (`execute_query`, `execute_scalar`, `execute_transaction`).

*   **`ConfigManager` (`app/core/config_manager.py`)**:
    *   Reads and writes application configuration from/to `config.ini` located in a platform-specific user configuration directory (e.g., `~/.config/SGBookkeeper/` on Linux).
    *   Provides typed access to database settings and application settings (theme, language, etc.).

*   **`SecurityManager` (`app/core/security_manager.py`)**:
    *   Handles user authentication:
        *   `hash_password()`: Uses `bcrypt` to hash passwords.
        *   `verify_password()`: Verifies plain text password against a stored hash.
        *   `authenticate_user()`: Authenticates a user, updates `last_login`, resets `failed_login_attempts`, and sets `self.current_user`. Handles login attempt tracking and account locking.
    *   Manages the `current_user` (instance of `User` ORM model) for the application session.
    *   Provides authorization checks: `has_permission(required_permission_code: str)` checks if the `current_user` has the specified permission through their assigned roles.
    *   Handles full CRUD operations for Users, Roles, and Permission assignments to roles, interacting directly with the ORM models and the database session provided by `DatabaseManager`. This includes complex logic like preventing deactivation of the last admin or deletion of the "Administrator" role.

#### 2.4 Asynchronous Task Management (`app/main.py`)

*   A dedicated Python `threading.Thread` (`_ASYNC_LOOP_THREAD`) hosts a persistent `asyncio` event loop (`_ASYNC_LOOP`). This loop is started when the application launches.
*   **`schedule_task_from_qt(coroutine)`**: This utility function is called from the Qt main thread (UI thread) to safely schedule an `async` coroutine (typically a manager or service method) to run on the dedicated `_ASYNC_LOOP`. It uses `asyncio.run_coroutine_threadsafe`.
*   **UI Updates from Async Tasks**: When an `async` task completes and needs to update the UI:
    *   It prepares the data (often serializing complex objects to JSON using `app.utils.json_helpers.json_converter`).
    *   It uses `QMetaObject.invokeMethod(target_qt_object, "slot_name", Qt.ConnectionType.QueuedConnection, Q_ARG(type, data))` to call a Qt slot on the main GUI thread, passing the prepared data. This ensures thread-safe UI updates.
    *   The receiving slot (e.g., `_update_table_model_slot`) then deserializes the data (e.g., using `json.loads` with `app.utils.json_helpers.json_date_hook`) and updates the UI elements (like table models).

### 3. Module & Component Specifications (Key Modules as Implemented)

#### 3.1 Accounting Module (`app/accounting/` & `app/ui/accounting/`)

*   **Chart of Accounts (CoA)**:
    *   **UI**: `ChartOfAccountsWidget` uses a `QTreeView` to display hierarchical accounts. `AccountDialog` for CRUD.
    *   **Manager**: `ChartOfAccountsManager` handles validation, CRUD logic, and tree structure retrieval via `AccountService.get_account_tree`.
    *   **Service**: `AccountService` provides ORM operations for `Account` model.
    *   **DTOs**: `AccountCreateData`, `AccountUpdateData`.
*   **Journal Entries (JE)**:
    *   **UI**: `JournalEntriesWidget` lists JEs in a `QTableView` (via `JournalEntryTableModel`). `JournalEntryDialog` for creating/editing (drafts)/viewing JEs. Actions for posting and reversing.
    *   **Manager**: `JournalEntryManager` handles creation, validation (balanced entries), posting (sets `is_posted=True`), reversal (creates counter-entry), and generation of recurring entries. Uses `SequenceService` (via DB function in `SequenceGenerator`) for `entry_no`.
    *   **Service**: `JournalService` for `JournalEntry`, `JournalEntryLine`, `RecurringPattern` ORM operations.
    *   **DTOs**: `JournalEntryData`, `JournalEntryLineData`.
*   **Fiscal Year & Periods**:
    *   **UI**: Managed within `SettingsWidget`. `FiscalYearDialog` for creating new fiscal years and auto-generating periods. `FiscalYearTableModel` lists fiscal years.
    *   **Manager**: `FiscalPeriodManager` handles creation of `FiscalYear` and associated `FiscalPeriod` records, closing/reopening periods/years.
    *   **Services**: `FiscalYearService`, `FiscalPeriodService`.
    *   **DTOs**: `FiscalYearCreateData`, `FiscalYearData`, `FiscalPeriodData`.

#### 3.2 Business Operations Module (`app/business_logic/` & `app/ui/.../`)

*   **Customers, Vendors, Products & Services**:
    *   **UI**: Dedicated widgets (`CustomersWidget`, `VendorsWidget`, `ProductsWidget`) with table views (`CustomerTableModel`, etc.) and dialogs (`CustomerDialog`, etc.) for full CRUD operations, filtering, and search. `ProductDialog` dynamically adapts UI based on `ProductTypeEnum`.
    *   **Managers**: `CustomerManager`, `VendorManager`, `ProductManager` handle validation (e.g., code uniqueness, valid GL accounts, tax codes) and orchestrate service calls.
    *   **Services**: `CustomerService`, `VendorService`, `ProductService`.
    *   **DTOs**: Respective `CreateData`, `UpdateData`, `SummaryData` DTOs (e.g., `ProductCreateData`).
*   **Sales Invoicing**:
    *   **UI**: `SalesInvoicesWidget` lists sales invoices (using `SalesInvoiceTableModel`). `SalesInvoiceDialog` for creating/editing drafts and posting. Features dynamic line item and total calculations. Combo boxes are populated asynchronously.
    *   **Manager**: `SalesInvoiceManager`:
        *   Validates invoice data (customer, products, tax codes).
        *   Uses `TaxCalculator` for line item tax and calculates overall totals.
        *   Handles `SalesInvoiceCreateData`, `SalesInvoiceUpdateData`.
        *   `create_draft_invoice`, `update_draft_invoice`: Manages draft persistence via `SalesInvoiceService`.
        *   `post_invoice`: Changes status to `Approved`, orchestrates JE creation via `JournalEntryManager`, links JE to invoice.
    *   **Service**: `SalesInvoiceService` for `SalesInvoice` and `SalesInvoiceLine` ORM operations.
    *   **DTOs**: `SalesInvoiceCreateData`, `SalesInvoiceUpdateData`, `SalesInvoiceSummaryData`, `SalesInvoiceLineBaseData`.
*   **Purchase Invoicing**:
    *   **UI**: `PurchaseInvoicesWidget` lists purchase invoices (using `PurchaseInvoiceTableModel`). `PurchaseInvoiceDialog` for creating/editing draft purchase invoices. Similar dynamic calculation features as `SalesInvoiceDialog`.
    *   **Manager**: `PurchaseInvoiceManager`:
        *   Validates invoice data (vendor, products, tax codes, duplicate vendor invoice no.).
        *   Uses `TaxCalculator` for line item tax and calculates overall totals.
        *   Handles `PurchaseInvoiceCreateData`, `PurchaseInvoiceUpdateData`.
        *   `create_draft_purchase_invoice`, `update_draft_purchase_invoice`: Manages draft persistence via `PurchaseInvoiceService`.
        *   `post_purchase_invoice`: Currently a stub, planned for JE creation.
    *   **Service**: `PurchaseInvoiceService` for `PurchaseInvoice` and `PurchaseInvoiceLine` ORM operations.
    *   **DTOs**: `PurchaseInvoiceCreateData`, `PurchaseInvoiceUpdateData`, `PurchaseInvoiceSummaryData`, `PurchaseInvoiceLineBaseData`.

#### 3.3 System Administration Module (`app/core/security_manager.py` & `app/ui/settings/`)

*   **UI**: `SettingsWidget` hosts `UserManagementWidget` and `RoleManagementWidget`.
    *   `UserManagementWidget`: Lists users (`UserTableModel`), allows Add/Edit (`UserDialog`), Toggle Active, Change Password (`UserPasswordDialog`).
    *   `RoleManagementWidget`: Lists roles (`RoleTableModel`), allows Add/Edit/Delete (`RoleDialog`). `RoleDialog` includes a `QListWidget` for assigning permissions to roles.
*   **Manager**: `SecurityManager` (as described in Core Components) handles all backend logic.
*   **DTOs**: `UserCreateData`, `UserUpdateData`, `UserSummaryData`, `RoleCreateData`, `RoleUpdateData`, `PermissionData`.

#### 3.4 Reporting Module (`app/reporting/`, `app/tax/gst_manager.py` & `app/ui/reports/`)

*   **UI**: `ReportsWidget`:
    *   **GST F5 Tab**: Date selection, "Prepare" button. Displays F5 data in read-only fields. "Save Draft" and "Finalize" buttons.
    *   **Financial Statements Tab**: `QComboBox` for report type (BS, P&L, TB, GL). Date pickers for period/as-of date. `QCheckBox`es for "Include Zero-Balance Accounts" (BS) and "Include Comparative Period" (BS & P&L), dynamically showing/hiding relevant comparative date editors. `QStackedWidget` displays reports: `QTreeView` for BS & P&L (with custom population logic for hierarchy and formatting), `QTableView` for TB (via `TrialBalanceTableModel`) and GL (via `GeneralLedgerTableModel` within a custom GL container widget). Export to PDF/Excel buttons.
*   **Managers**:
    *   `GSTManager`: `prepare_gst_return_data` (calculates F5 figures from JEs), `save_gst_return` (saves `GSTReturn` ORM), `finalize_gst_return` (updates status, creates settlement JE via `JournalEntryManager`).
    *   `FinancialStatementGenerator`: Methods to generate data for BS, P&L, TB, GL.
    *   `ReportEngine`:
        *   Dispatcher `export_report` routes to specific methods.
        *   `_export_balance_sheet_to_pdf`, `_export_profit_loss_to_pdf`, `_export_balance_sheet_to_excel`, `_export_profit_loss_to_excel`: Implement enhanced formatting (headers, footers, styling).
        *   Generic PDF/Excel methods retained for TB, GL.
*   **Services**: Underlying services (`JournalService`, `AccountService`, `TaxCodeService`, `CompanySettingsService`) are used by managers.
*   **DTOs**: `GSTReturnData`. Report data is typically passed as `Dict[str, Any]`.

### 4. Data Architecture

*   **Database Schema**: Defined in `scripts/schema.sql`. It's comprehensive, normalized, and uses PostgreSQL-specific features like `EXCLUDE USING gist` for overlapping date ranges and functions for sequences. Audit tables (`audit.audit_log`, `audit.data_change_history`) are populated by DB triggers.
*   **SQLAlchemy ORM Models (`app/models/`)**: Python classes mapped to database tables, organized by schema. They include relationships (`relationship`) with `back_populates` and necessary mixins (`TimestampMixin`).
*   **Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)**: Pydantic models ensure type safety and validation for data passed between UI and business logic layers. Custom validators and root validators are used for complex checks (e.g., password confirmation, conditional field requirements).

### 5. Security Considerations

*   **Authentication**: Managed by `SecurityManager` using `bcrypt` for password hashing. Includes failed login attempt tracking and account locking.
*   **Authorization (RBAC)**: `SecurityManager.has_permission()` checks if the current user has a specific permission code. Permissions are assigned to Roles, and Roles are assigned to Users. This is fully manageable via the UI in the Settings module. The "Administrator" role is protected.
*   **Audit Trails**: Database triggers on key tables automatically log changes to `audit.audit_log` (summary) and `audit.data_change_history` (field-level changes). The application sets the `app.current_user_id` session variable via `DatabaseManager` for these triggers.

### 6. Deployment and Initialization

*   **Dependencies**: Managed by `pyproject.toml` via Poetry.
*   **Database Setup**:
    *   `scripts/db_init.py`: Orchestrates database creation and initialization.
    *   `scripts/schema.sql`: Creates all schemas, tables, views, functions, triggers.
    *   `scripts/initial_data.sql`: Seeds essential data (roles, permissions, default user 'admin'/'password', system accounts for GST, currencies, sequences, default company settings, etc.). The 'system_init_user' (ID 1) is created for system-generated records and is typically inactive.
*   **Configuration**: `config.ini` in a user-specific directory, managed by `ConfigManager`.
*   **Execution**: `poetry run sg_bookkeeper` starts the application via `app/main.py`.

### 7. Data & Resource Files

*   **Report Templates (`data/report_templates/`)**: JSON files (e.g., `balance_sheet_default.json`) define the structure/grouping for financial statements, although the current rendering logic in `FinancialStatementGenerator` and `ReportEngine` seems more hardcoded for BS/P&L sectioning rather than fully driven by these JSON templates. The JSON template files might be for future more dynamic reporting or as a reference.
*   **Tax Codes (`data/tax_codes/sg_gst_codes_2023.csv`)**: This CSV is *not* directly used by the application at runtime. The tax codes are inserted into the `accounting.tax_codes` table by `scripts/initial_data.sql`. The CSV serves as a source or reference for the initial SQL data.
*   **Chart of Accounts Templates (`data/chart_of_accounts/`)**: CSV files like `general_template.csv` can be imported by the user via a UI feature (if implemented, not explicitly detailed as fully functional yet but foundational for CoA setup).
*   **Icons (`resources/icons/`)**: SVG icons used throughout the UI.
*   **Images (`resources/images/`)**: Splash screen image.
*   **Qt Resources (`resources/resources.qrc`, `app/resources_rc.py`)**: The `resources.qrc` file lists all resource files. It's compiled into `app/resources_rc.py` (e.g., using `pyside6-rcc`). The application attempts to import `app.resources_rc` and uses `:/icons/` paths if successful, otherwise falls back to direct file paths like `resources/icons/`. The provided logs confirm `resources_rc.py` is being successfully imported and used.

### 8. Conclusion

The SG Bookkeeper application, as reflected in the current codebase, has a well-defined n-tier architecture with clear separation of concerns. The asynchronous processing model is consistently applied to keep the UI responsive. The database schema is comprehensive and supports a wide range of accounting and business functions. Key modules, including core accounting, customer/vendor/product management, full sales invoicing, draft purchase invoicing (with list view), and user/role administration, are substantially implemented. Financial reporting has been enhanced with better export formatting and more UI options for key statements. The project is in a mature state, with a solid foundation for completing the Purchase Invoicing lifecycle and further expanding other modules.

---
https://drive.google.com/file/d/10NQZe3AATtiodERb3NEjPFqGN_RwqV8V/view?usp=sharing, https://drive.google.com/file/d/13I6IC_fPXgIu51NJdpl4hSud70xeNksT/view?usp=sharing, https://drive.google.com/file/d/13UTU4WGBLEji-2V1_c1Vm0CU5yjAAtEl/view?usp=sharing, https://drive.google.com/file/d/16h5hgHm8_8eJHIcv3IlqY9EOwelrur25/view?usp=sharing, https://drive.google.com/file/d/1AM4pzDhd3lo5VY3qsEm6fVsw_Z7iw0ht/view?usp=sharing, https://drive.google.com/file/d/1H7adg-9W50pczl6941vi2oe2OioCl75v/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221Jek1dhLzt3_VmBaCpltwEgVXlLziuPfh%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1Nm5wabOgWCtVKR7AfHNxS-qTAjaJpaWV/view?usp=sharing, https://drive.google.com/file/d/1O4_3WqbLhXuJwUMBWWglGwoPWRVBCXD9/view?usp=sharing, https://drive.google.com/file/d/1QdQyCh2708zFoDCCGTqMerLXPRKwMd_y/view?usp=sharing, https://drive.google.com/file/d/1QiCI5C2uzVrIJ4TLqOt8jmnG8xYOLk3L/view?usp=sharing, https://drive.google.com/file/d/1R2DblOk4TOXxLfbaMnxryzHEC_xGqf5I/view?usp=sharing, https://drive.google.com/file/d/1U_8wYmPi1gYywlN5EUMsnOFY6miX5NzI/view?usp=sharing, https://drive.google.com/file/d/1VTDvkd0euAJxI03-B_wqlaJWL0gjb1Qo/view?usp=sharing, https://drive.google.com/file/d/1VqKCTYOGp4kvWbPdDMkXxXfLcaOto2e9/view?usp=sharing, https://drive.google.com/file/d/1_IJiDhrxb8h4ZoDHPRHN4TTHHNmoWC8c/view?usp=sharing, https://drive.google.com/file/d/1a3ku0WZ4NS1nuZ_2RXgBLNpE0Hp77Qaa/view?usp=sharing, https://drive.google.com/file/d/1cFh9KYlyBfh_asfkvW2TskFgf1cMbBVb/view?usp=sharing, https://drive.google.com/file/d/1hC-uzD9MLhtizqXPKAwOVfeEBYLOE8mG/view?usp=sharing, https://drive.google.com/file/d/1hoITa2HMGuSqh12ftIsU0EGlrGgiDivM/view?usp=sharing, https://drive.google.com/file/d/1ltHzvIRZN0ai7DwQkOaWDuGgUuB2jtXo/view?usp=sharing, https://drive.google.com/file/d/1qgUPpEvs8vFi7n4Z1ynb1k-mLcHbGdTC/view?usp=sharing, https://drive.google.com/file/d/1rghvbIqkwirHLtF1Vq9aeuyVWzDzcpEM/view?usp=sharing, https://drive.google.com/file/d/1tWGlfoC-ALwANG5z-52tK0VsUJpLpSTa/view?usp=sharing, https://drive.google.com/file/d/1tsYe-fhVo00JwkBq5C3rT-D0Ixh1P_J1/view?usp=sharing, https://drive.google.com/file/d/1uwTPQsCijSJXdFTNzFnP3ggajVllZFQi/view?usp=sharing

