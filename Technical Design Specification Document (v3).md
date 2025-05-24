# Technical Design Specification Document: SG Bookkeeper (Updated)

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document provides comprehensive implementation details for the SG Bookkeeper application, a Singapore-compliant small business bookkeeping software. It reflects the current design, incorporating solutions and refinements developed through the initial implementation and debugging phases. It serves as a guide for ongoing development, testing, and maintenance.

### 1.2 Scope
This TDS covers:
- System architecture, including UI, business logic, data access, and asynchronous processing.
- Database schema as defined in `scripts/schema.sql`, including tables, views, functions, and triggers.
- Key UI implementation patterns, focusing on `PySide6` and `asyncio` integration.
- Core business logic component structure and interactions.
- Data models (SQLAlchemy ORM).
- Security considerations.
- Deployment and initialization procedures.

### 1.3 Intended Audience
- Software Developers: For implementation and feature development.
- QA Engineers: For understanding system behavior and designing tests.
- System Administrators: For deployment and database setup.
- Technical Project Managers: For project oversight and planning.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application built with Python, PySide6, and PostgreSQL. It provides robust double-entry bookkeeping, Singapore-specific tax management (GST, income tax estimation), financial reporting, and modules for business operations like customer/vendor management, invoicing, and banking. The application emphasizes data integrity, user-friendliness for small business owners, and compliance with local accounting standards. Its core data structures are defined in `scripts/schema.sql` and initial data in `scripts/initial_data.sql`.

## 2. System Architecture

### 2.1 High-Level Architecture
The application maintains a layered architecture:

```
+---------------------------------------------------+
|                  Presentation Layer                |
|  (PySide6 UI Widgets, Dialogs, Main Window)       |
+---------------------------------------------------+
                         |  (Qt Signals/Slots, schedule_task_from_qt)
                         v
+---------------------------------------------------+
|                  Business Logic Layer              |
|   (ApplicationCore, Managers, Services - Async)    |
+---------------------------------------------------+
                         |  (SQLAlchemy ORM, asyncpg)
                         v
+---------------------------------------------------+
|                  Data Access Layer                 |
|      (DatabaseManager, SQLAlchemy Models)          |
+---------------------------------------------------+
                         |
                         v
+---------------------------------------------------+
|                  Database                          |
|                (PostgreSQL)                        |
+---------------------------------------------------+
```
- **Presentation Layer**: Handles user interaction, built with PySide6.
- **Business Logic Layer**: Contains core application logic, service coordination, and managers for different modules. Most operations here are asynchronous.
- **Data Access Layer**: Manages database interactions using SQLAlchemy's asynchronous features with `asyncpg`.
- **Database**: PostgreSQL stores all application data.

### 2.2 Component Architecture

#### 2.2.1 Core Components (`app/core/`)
- **`Application (app/main.py)`**: Subclass of `QApplication`. Manages the Qt event loop, global asyncio event loop (in a separate thread), splash screen, and initial application setup.
- **`ApplicationCore`**: Central orchestrator. Initializes and provides access to all services and managers. Handles application startup and shutdown sequences.
- **`ConfigManager`**: Manages application settings from `config.ini` stored in a platform-specific user configuration directory.
- **`DatabaseManager`**: Handles PostgreSQL database connections (via SQLAlchemy async engine and `asyncpg` pool) and session management.
- **`SecurityManager`**: Manages user authentication (password hashing/verification with `bcrypt`), authorization (permission checks based on roles), and tracks the current user.
- **`ModuleManager`**: (Currently conceptual) Intended for dynamic loading/management of larger application modules.

#### 2.2.2 Asynchronous Task Management (`app/main.py`)
- A dedicated Python `threading.Thread` (`_ASYNC_LOOP_THREAD`) runs a persistent `asyncio` event loop (`_ASYNC_LOOP`).
- `schedule_task_from_qt(coroutine)`: Utility function to safely schedule coroutines from the main Qt GUI thread onto the dedicated asyncio loop thread using `asyncio.run_coroutine_threadsafe`.
- UI components (e.g., widgets loading data via `QTimer`) use `schedule_task_from_qt` to initiate asynchronous operations.
- UI updates from asyncio tasks are marshaled back to the Qt main thread using `QMetaObject.invokeMethod` with `Qt.ConnectionType.QueuedConnection`, typically passing data as JSON strings or other QVariant-compatible types.

#### 2.2.3 Services (`app/services/`)
Services implement repository patterns for data access, providing an abstraction layer over direct ORM queries.
- **`AccountService`**: Manages CRUD for `Account` entities, tree generation.
- **`JournalService`**: Manages CRUD for `JournalEntry`, `JournalEntryLine`, `RecurringPattern`. Calculates account balances.
- **`FiscalPeriodService`**: Manages `FiscalPeriod` entities.
- **`FiscalYearService` (in `accounting_services.py`)**: Manages `FiscalYear` entities.
- **`Core Services` (`core_services.py`)**:
    - `SequenceService`: Manages `Sequence` entities for document numbering.
    - `ConfigurationService`: Manages `Configuration` key-value store.
    - `CompanySettingsService`: Manages the single `CompanySetting` record.
- **`Tax Services` (`tax_service.py`)**:
    - `TaxCodeService`: Manages `TaxCode` entities.
    - `GSTReturnService`: Manages `GSTReturn` entities.
- **`Accounting Services` (`accounting_services.py`)**:
    - `AccountTypeService`: Manages `AccountType` entities.
    - `CurrencyService`: Manages `Currency` entities.
    - `ExchangeRateService`: Manages `ExchangeRate` entities.

#### 2.2.4 Managers (Business Logic) (`app/accounting/`, `app/tax/`, etc.)
Managers encapsulate more complex business logic, orchestrating calls to multiple services.
- **`ChartOfAccountsManager`**: Handles account creation, updates, deactivation, validation.
- **`JournalEntryManager`**: Manages journal creation, posting, reversal, recurring entry generation.
- **`FiscalPeriodManager`**: Manages fiscal year/period creation, closing, reopening.
- **`CurrencyManager`**: Handles currency and exchange rate information access.
- **`GSTManager`**: Prepares GST return data, finalizes returns, creates settlement journal entries.
- **`IncomeTaxManager`**, **`WithholdingTaxManager`**: (Currently stubs) Intended for specific tax logic.
- **`TaxCalculator`**: Provides generic tax calculation logic based on tax codes.
- **`FinancialStatementGenerator`**: Generates Balance Sheet, P&L, Trial Balance.
- **`ReportEngine`**: Exports reports to PDF/Excel.

#### 2.2.5 User Interface (`app/ui/`)
- **`MainWindow`**: Main application frame, holds menus, toolbars, status bar, and tabbed interface for modules.
- **Module Widgets** (e.g., `DashboardWidget`, `AccountingWidget`, `SettingsWidget`): Each occupies a tab in `MainWindow` and serves as the entry point for a functional area.
- **Detail Widgets** (e.g., `ChartOfAccountsWidget`): Provides specific views and interactions within a module.
- **Dialogs** (e.g., `AccountDialog`): For data entry and modification.

### 2.3 Technology Stack
- **Python**: 3.9+
- **UI Framework**: PySide6 6.9.0
- **Database**: PostgreSQL 14+
- **Database Connector (Async)**: `asyncpg` >= 0.25.0
- **ORM**: SQLAlchemy >= 2.0.0 (using async features)
- **Database Initialization/Schema**: `scripts/schema.sql`, `scripts/initial_data.sql`
- **Password Hashing**: `bcrypt`
- **Date/Time Utilities**: `python-dateutil`
- **Reporting**: `reportlab` (PDF), `openpyxl` (Excel)
- **Data Validation (DTOs)**: `Pydantic` V2
- **Dependency Management**: Poetry

### 2.4 Design Patterns
- **Layered Architecture**: Presentation, Business Logic, Data Access.
- **Model-View-Controller (MVC) / Model-View-Presenter (MVP)**: Guiding UI structure.
- **Repository Pattern**: Implemented by Service classes for data access.
- **Dependency Injection**: `ApplicationCore` instantiates and injects dependencies into managers/services.
- **Observer Pattern**: Qt Signals/Slots for UI and inter-component communication.
- **Result Object Pattern (`app.utils.Result`)**: For returning success/failure and error messages from service/manager methods.
- **Data Transfer Objects (DTOs - `app.utils.pydantic_models`)**: Pydantic models for structured data transfer between layers, especially UI to managers.
- **Threaded Asynchronous Execution**: For keeping UI responsive during I/O-bound operations.

## 3. Data Architecture

### 3.1 Database Schema Overview
The PostgreSQL database is organized into four schemas: `core`, `accounting`, `business`, and `audit`. The complete DDL is in `scripts/schema.sql`. Key features:
- Comprehensive table structures for all accounting and business entities.
- Extensive use of foreign keys for referential integrity.
- `CHECK` constraints for data validation at the database level.
- Indexes for performance on common query patterns.
- User audit trails (`created_by`, `updated_by`, `created_at`, `updated_at` columns) on most tables.
- Dedicated audit tables (`audit.audit_log`, `audit.data_change_history`) populated by database triggers.
- Views for aggregated data (e.g., `accounting.trial_balance`, `business.customer_balances`).
- Stored functions for specific database operations (e.g., `core.get_next_sequence_value`).

**Order of DDL Execution in `schema.sql`:**
1.  Extensions and Schemas creation.
2.  All `CREATE TABLE` statements.
3.  All `CREATE INDEX` statements (non-PK/non-UK).
4.  All `ALTER TABLE ... ADD CONSTRAINT FOREIGN KEY` statements (grouped at the end to handle dependencies).
5.  All `CREATE OR REPLACE VIEW` statements.
6.  All `CREATE OR REPLACE FUNCTION` statements.
7.  Trigger creation `DO $$...$$` blocks.

### 3.2 SQLAlchemy ORM Models (`app/models/`)
- Models are organized into subdirectories mirroring database schemas (e.g., `app/models/core/`, `app/models/accounting/`).
- All models inherit from a common `Base` (from `sqlalchemy.ext.declarative.declarative_base()`).
- `TimestampMixin` provides `created_at` and `updated_at` columns with automatic timestamping.
- `UserAuditMixin` (used selectively or fields added directly) provides `created_by` and `updated_by` foreign keys to `core.users`.
- Relationships (`relationship`) are defined with `back_populates` for bidirectional access.
- Mapped dataclasses (`Mapped`, `mapped_column`) from SQLAlchemy 2.0 style are used.

**Example: `core.users.User` Model Snippet**
```python
# app/models/core/user.py
from sqlalchemy import Table, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import Base, TimestampMixin 

user_roles_table = Table(
    'user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('core.users.id', ondelete="CASCADE"), primary_key=True),
    # ...
    schema='core'
)

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    # ... other fields ...
    roles: Mapped[List["Role"]] = relationship(secondary=user_roles_table, back_populates="users")
```

## 4. Module and Component Specifications (Selected Examples)

### 4.1 Application Startup (`app/main.py`)
- Initializes `QApplication`.
- Starts a dedicated asyncio event loop in a background thread (`start_asyncio_event_loop_thread`).
- Uses `schedule_task_from_qt` to run `Application.initialize_app()` on this loop.
- `initialize_app()`:
    - Initializes `ConfigManager`, `DatabaseManager`, `ApplicationCore`.
    - Calls `ApplicationCore.startup()` (async).
    - Attempts a default user authentication.
    - Emits `initialization_done_signal` to the main Qt thread.
- `_on_initialization_done()` (slot in Qt thread):
    - Creates and shows `MainWindow`.
    - Finishes splash screen.
- `actual_shutdown_sequence()` (connected to `aboutToQuit`):
    - Schedules `ApplicationCore.shutdown()` on the asyncio loop.
    - Stops and joins the asyncio loop thread.

### 4.2 Chart of Accounts UI (`app/ui/accounting/chart_of_accounts_widget.py`)
- Uses a `QTreeView` with `QStandardItemModel` (and `QSortFilterProxyModel`).
- **Asynchronous Data Loading**:
    - `_load_accounts()` is an `async` method.
    - It's called from `_init_ui` via `QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_accounts()))`.
    - Fetches data using `self.app_core.accounting_service.get_account_tree()`.
    - Data (list of dicts) is serialized to JSON.
    - `QMetaObject.invokeMethod` calls `_update_account_model_slot` on the main thread, passing the JSON string.
- **Thread-Safe UI Update**:
    - `_update_account_model_slot(self, json_str: str)`: Deserializes JSON, clears and populates the `QStandardItemModel`.
- **Dialog Interaction**: `AccountDialog` for add/edit, also uses async manager methods scheduled via `schedule_task_from_qt` if saving directly from dialog, or dialog returns data and widget schedules save.

### 4.3 Audit Triggers (`scripts/schema.sql`)
- `audit.log_data_change_trigger_func()` is attached to key tables.
- **User ID Retrieval**:
    1.  Tries `current_setting('app.current_user_id', TRUE)::INTEGER`.
    2.  If NULL, falls back to `NEW.created_by` (for INSERT) or `NEW.updated_by` (for UPDATE).
    3.  Special handling for `core.users` table: if `created_by`/`updated_by` don't exist on `NEW` (which they don't for `core.users` itself), it uses `NEW.id`.
    4.  Uses `BEGIN...EXCEPTION WHEN undefined_column...END` for robustness when accessing `NEW.created_by` etc.
- **Change Tracking**:
    - Inserts a summary into `audit.audit_log` with old/new JSONB data.
    - For `UPDATE`s, iterates through `jsonb_object_keys(v_old_data)` and inserts detailed field changes into `audit.data_change_history`. The loop is `FOR current_field_name_from_json IN SELECT key_alias FROM jsonb_object_keys(v_old_data) AS t(key_alias) LOOP`.

## 5. Deployment and Installation
Refer to `README.md` and `deployment_guide.md` for detailed steps. Key aspects:
- Python 3.9+, PostgreSQL 14+, Poetry.
- Database initialization via `poetry run sg_bookkeeper_db_init --user <admin_user> --password <pass> --dbname <dbname> [--drop-existing]`.
    - This script executes `scripts/schema.sql` then `scripts/initial_data.sql`.
    - An optional `ALTER DATABASE ... SET search_path` command is now included in `db_init.py` to set the default search path for new connections to the application database.
- Application execution: `poetry run sg_bookkeeper`.
- Configuration is managed via `config.ini` in a platform-specific user config directory (e.g., `~/.config/SGBookkeeper/` on Linux).
- Dedicated database user (e.g., `sgbookkeeper_user`) should be created and granted appropriate privileges (see `README.md` or `deployment_guide.md`).

## 6. Security Considerations
- Passwords hashed using `bcrypt`.
- Role-based access control (RBAC) via `core.roles` and `core.permissions`.
- Comprehensive audit trails via `audit_log` and `data_change_history` tables, populated by database triggers.
- Sensitive configuration values can be marked for encryption in `core.configuration` (encryption mechanism TBD).

## 7. Future Considerations / Missing Pieces
- Full implementation of all UI widgets and business logic for all modules (Customers, Vendors, Invoicing, Banking, full Reporting features, etc.).
- Robust error handling and user feedback throughout the UI.
- Data validation beyond Pydantic DTOs, potentially at service/manager layers.
- Internationalization (i18n) support.
- Comprehensive unit and integration tests for services, managers, and UI components.
- Packaging for distribution (e.g., using PyInstaller).
- A more sophisticated asyncio/Qt bridge (e.g., `quamash`, `asyncqt`) if `schedule_task_from_qt` with `QMetaObject.invokeMethod` becomes a bottleneck or too complex for some use cases.

*(This TDS will continue to evolve as development progresses.)*
