# Technical Design Specification Document: SG Bookkeeper (v4)

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version 4, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities observed in the existing codebase. This document serves as a comprehensive guide for ongoing development, feature enhancement, testing, and maintenance, ensuring clarity and consistency across the development team.

### 1.2 Scope
This TDS covers the following aspects of the SG Bookkeeper application:
-   **System Architecture**: Detailed breakdown of the UI, business logic, data access layers, and the crucial asynchronous processing architecture for Qt/asyncio integration.
-   **Database Schema**: Alignment with the comprehensive schema defined in `scripts/schema.sql`, including tables, views, functions, and triggers across `core`, `accounting`, `business`, and `audit` schemas.
-   **Key UI Implementation Patterns**: Focus on `PySide6` UI components, particularly how they interact with asynchronous backend operations, exemplified by core accounting widgets.
-   **Core Business Logic**: Structure and interactions of key business logic components (Managers and Services).
-   **Data Models**: SQLAlchemy ORM models as defined in `app/models/`, reflecting the database structure.
-   **Security Implementation**: Details on user authentication, authorization (RBAC), and audit mechanisms.
-   **Deployment and Initialization**: Procedures for setting up the application environment, database, and initial data.
-   **Current Implementation Status**: Highlighting implemented features and noting areas for future development.

### 1.3 Intended Audience
-   **Software Developers**: For understanding the existing codebase, implementing new features, and maintaining architectural consistency.
-   **QA Engineers**: For guiding test plan creation by understanding system behavior and data flows.
-   **System Administrators**: For deployment, database setup, and understanding system dependencies.
-   **Technical Project Managers**: For project oversight, planning future sprints, and understanding technical complexities.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application engineered with Python, utilizing PySide6 for its graphical user interface and PostgreSQL for robust, relational data storage. It is tailored to provide comprehensive accounting solutions for small to medium-sized businesses in Singapore. Key functionalities include a full double-entry bookkeeping system, Singapore-specific GST management, financial reporting capabilities, and modules for core business operations such as customer/vendor management (planned), invoicing (planned), and banking (planned). The application prioritizes data integrity, compliance with Singaporean accounting standards (SFRS) and tax regulations, and aims for a user-friendly experience. The foundational data structures are meticulously defined in `scripts/schema.sql`, with initial seeding data provided by `scripts/initial_data.sql`.

## 2. System Architecture

### 2.1 High-Level Architecture
The application employs a layered architecture to ensure separation of concerns and maintainability:

```
+---------------------------------------------------+
|                  Presentation Layer                |
|  (PySide6: MainWindow, Module Widgets, Dialogs)   |
+---------------------------------------------------+
      ^                    | (Qt Signals/Slots for UI update,
      |                    |  schedule_task_from_qt for async calls)
(User Interaction)         v
+---------------------------------------------------+
|                  Business Logic Layer              |
|  (ApplicationCore, Managers, Services - Async)    |
+---------------------------------------------------+
                         |  (SQLAlchemy ORM via asyncpg)
                         v
+---------------------------------------------------+
|                  Data Access Layer                 |
|      (DatabaseManager, SQLAlchemy Models)          |
+---------------------------------------------------+
                         |
                         v
+---------------------------------------------------+
|                  Database                          |
|      (PostgreSQL: Schemas, Tables, Views,          |
|       Functions, Triggers)                         |
+---------------------------------------------------+
```
-   **Presentation Layer**: Built with `PySide6`, responsible for all user interactions, rendering views, and capturing user input. It communicates with the Business Logic Layer, typically initiating asynchronous operations.
-   **Business Logic Layer**: Houses the core application logic, orchestrates workflows, and enforces business rules. It's composed of `ApplicationCore`, various `Managers` for different functional modules, and `Services` that abstract data access. Operations in this layer are predominantly asynchronous.
-   **Data Access Layer**: Manages all interactions with the PostgreSQL database. It utilizes `SQLAlchemy`'s asynchronous ORM capabilities, powered by the `asyncpg` driver, and is centered around the `DatabaseManager` and ORM models.
-   **Database Layer**: PostgreSQL serves as the persistent data store, featuring a structured schema with tables, views, stored functions, and triggers to ensure data integrity and support complex queries.

### 2.2 Component Architecture

#### 2.2.1 Core Components (`app/core/`)
-   **`Application` (`app/main.py`)**: A subclass of `PySide6.QtWidgets.QApplication`. It manages the main Qt event loop, initializes and manages a dedicated background thread for the `asyncio` event loop, displays a splash screen during startup, and orchestrates the initial application setup sequence.
-   **`ApplicationCore` (`app/core/application_core.py`)**: The central orchestrator of the application. It's responsible for initializing all services, managers, and core components. It provides a unified access point to these components for other parts of the application and manages global startup and shutdown procedures.
-   **`ConfigManager` (`app/core/config_manager.py`)**: Handles loading and saving application settings from a `config.ini` file located in a platform-specific user configuration directory (e.g., `~/.config/SGBookkeeper/` on Linux).
-   **`DatabaseManager` (`app/core/database_manager.py`)**: Manages asynchronous connections to the PostgreSQL database. It initializes the `SQLAlchemy` async engine and an `asyncpg` connection pool, providing session management for database transactions.
-   **`SecurityManager` (`app/core/security_manager.py`)**: Responsible for user authentication (using `bcrypt` for password hashing and verification), authorization (checking permissions based on user roles), and maintaining the state of the `current_user`.
-   **`ModuleManager` (`app/core/module_manager.py`)**: Currently a conceptual component intended for dynamic loading and management of larger, distinct application modules or plugins. Its full implementation is part of future scope.

#### 2.2.2 Asynchronous Task Management (`app/main.py`)
To maintain a responsive user interface while performing potentially long-running I/O-bound operations (like database queries or complex calculations), the application employs a dedicated thread for its `asyncio` event loop:
-   A Python `threading.Thread` named `_ASYNC_LOOP_THREAD` is started at application launch.
-   This thread runs a persistent `asyncio` event loop (`_ASYNC_LOOP`).
-   **`schedule_task_from_qt(coroutine)`**: A utility function in `app/main.py` allows scheduling `asyncio` coroutines from the main Qt (GUI) thread onto the dedicated `_ASYNC_LOOP` thread. This is achieved using `asyncio.run_coroutine_threadsafe`.
-   UI components (e.g., widgets loading data in their initialization or upon user action) use `schedule_task_from_qt` to initiate asynchronous backend operations.
-   **UI Updates from Async Tasks**: When an asynchronous task completes and needs to update the UI, results are marshaled back to the Qt main thread safely using `PySide6.QtCore.QMetaObject.invokeMethod` with `Qt.ConnectionType.QueuedConnection`. Data is often passed as JSON strings (using helpers in `app/utils/json_helpers.py`) or other `QVariant`-compatible types to ensure thread safety.

```python
# Snippet from app/main.py illustrating async task scheduling
# (Conceptual, actual usage is within widget methods)
# async def some_async_operation():
#     # ... perform database calls or heavy computation ...
#     result = await ...
#     return result
#
# # From a Qt widget method (GUI thread):
# future = schedule_task_from_qt(some_async_operation())
# # Optionally, connect to future.add_done_callback() for simple cases,
# # or have the coroutine itself schedule a UI update slot.
```

#### 2.2.3 Services (`app/services/`)
Services implement the Repository pattern, providing a clean abstraction layer for data access operations. They encapsulate `SQLAlchemy` ORM queries and are typically injected into Managers.
-   **`AccountService`**: CRUD operations for `Account` entities, generation of hierarchical account tree data.
-   **`JournalService`**: CRUD for `JournalEntry`, `JournalEntryLine`, `RecurringPattern`. Calculates account balances.
-   **`FiscalPeriodService`**: Manages `FiscalPeriod` entities (fetching, status updates).
-   **`FiscalYearService`** (in `app/services/accounting_services.py`): Manages `FiscalYear` entities.
-   **Core Services (`app/services/core_services.py`)**:
    -   `SequenceService`: Manages `Sequence` entities for document numbering (though a DB function `core.get_next_sequence_value` also exists).
    -   `ConfigurationService`: Manages `Configuration` key-value store from the database.
    -   `CompanySettingsService`: Manages the single `CompanySetting` record.
-   **Tax Services (`app/services/tax_service.py`)**:
    -   `TaxCodeService`: Manages `TaxCode` entities.
    -   `GSTReturnService`: Manages `GSTReturn` entities.
-   **Accounting Services (`app/services/accounting_services.py`)**:
    -   `AccountTypeService`: Manages `AccountType` entities.
    -   `CurrencyService`: Manages `Currency` entities.
    -   `ExchangeRateService`: Manages `ExchangeRate` entities.

#### 2.2.4 Managers (Business Logic) (`app/accounting/`, `app/tax/`, etc.)
Managers encapsulate more complex business logic, orchestrate calls to multiple services, and enforce business rules. They are the primary interface for UI components to interact with the backend logic.
-   **`ChartOfAccountsManager` (`app/accounting/chart_of_accounts_manager.py`)**: Handles business logic for account creation (including validation using Pydantic DTOs), updates, deactivation (with balance checks), and fetching the account tree.
-   **`JournalEntryManager` (`app/accounting/journal_entry_manager.py`)**: Manages the lifecycle of journal entries: creation from `JournalEntryData` DTO, posting, reversal (creating counter-entries), and generation of recurring entries based on `RecurringPattern`. Uses `SequenceGenerator` for `entry_no`.
-   **`FiscalPeriodManager` (`app/accounting/fiscal_period_manager.py`)**: Handles business logic for fiscal year and period management, including creating new fiscal years and automatically generating their constituent periods (e.g., monthly, quarterly) within a single transaction.
-   **`CurrencyManager` (`app/accounting/currency_manager.py`)**: Provides an interface for accessing currency and exchange rate information, coordinating `CurrencyService` and `ExchangeRateService`.
-   **`GSTManager` (`app/tax/gst_manager.py`)**: Responsible for preparing `GSTReturnData` for GST F5 forms (data aggregation logic from JEs is currently a placeholder), saving draft `GSTReturn` entities, and finalizing them (which includes generating a settlement journal entry).
-   **`TaxCalculator` (`app/tax/tax_calculator.py`)**: Provides generic tax calculation logic based on `TaxCode` details (rate, type).
-   **`IncomeTaxManager`**, **`WithholdingTaxManager`** (`app/tax/`): Currently stubs, intended for future implementation of specific income tax and withholding tax logic.
-   **`FinancialStatementGenerator` (`app/reporting/financial_statement_generator.py`)**: Generates the data structures for standard financial reports like Balance Sheet, Profit & Loss, and Trial Balance, utilizing various services to fetch and aggregate data.
-   **`ReportEngine` (`app/reporting/report_engine.py`)**: Responsible for exporting generated report data into different formats, currently supporting PDF (via `reportlab`) and Excel (via `openpyxl`).

#### 2.2.5 User Interface Components (`app/ui/`)
-   **`MainWindow` (`app/ui/main_window.py`)**: The main application window. It contains the primary menu bar, toolbar, status bar, and a `QTabWidget` to host different module widgets.
-   **Module Widgets**: Each primary functional area of the application is encapsulated in a module widget, displayed as a tab in the `MainWindow`. Examples:
    -   `DashboardWidget` (`app/ui/dashboard/`) (Currently a stub)
    -   `AccountingWidget` (`app/ui/accounting/`): Hosts sub-tabs for Chart of Accounts, Journal Entries, etc.
    -   `SettingsWidget` (`app/ui/settings/`): Allows configuration of company settings and fiscal year management.
    -   `CustomersWidget`, `VendorsWidget`, `BankingWidget`, `ReportsWidget` (Currently stubs for planned features).
-   **Detail Widgets**: Provide specific views and interactions within a module.
    -   `ChartOfAccountsWidget` (`app/ui/accounting/chart_of_accounts_widget.py`): Displays the CoA in a `QTreeView`, supports add/edit/deactivate actions, and uses the async loading pattern.
    -   `JournalEntriesWidget` (`app/ui/accounting/journal_entries_widget.py`): Displays a list of journal entries in a `QTableView` using `JournalEntryTableModel`, with actions for new, edit, view, post.
-   **Dialogs**: Used for data entry, modification, and specific interactions.
    -   `AccountDialog` (`app/ui/accounting/account_dialog.py`): For creating and editing accounts.
    -   `JournalEntryDialog` (`app/ui/accounting/journal_entry_dialog.py`): A complex dialog for detailed creation and editing of journal entries, including line items.
    -   `FiscalYearDialog` (`app/ui/accounting/fiscal_year_dialog.py`): Used within `SettingsWidget` for creating new fiscal years.

### 2.3 Technology Stack
The application is built using the following technologies:
-   **Programming Language**: Python 3.9+ (explicitly tested up to 3.12 as per `pyproject.toml`)
-   **UI Framework**: PySide6 6.9.0+
-   **Database**: PostgreSQL 14+
-   **Asynchronous DB Driver**: `asyncpg` >= 0.25.0
-   **ORM**: SQLAlchemy >= 2.0.0 (utilizing asynchronous features with `asyncpg`)
-   **Database Initialization/Schema**: Defined in `scripts/schema.sql` (DDL) and `scripts/initial_data.sql` (seed data).
-   **Password Hashing**: `bcrypt`
-   **Date/Time Utilities**: `python-dateutil`
-   **Reporting Libraries**: `reportlab` (for PDF generation), `openpyxl` (for Excel generation).
-   **Data Validation (DTOs)**: Pydantic V2 (`app/utils/pydantic_models.py`).
-   **Dependency Management & Packaging**: Poetry.

### 2.4 Design Patterns
The application incorporates several design patterns to promote maintainability, scalability, and separation of concerns:
-   **Layered Architecture**: As described in Section 2.1.
-   **Model-View-Controller (MVC) / Model-View-Presenter (MVP)**: Variations guide the structure of UI components, separating data (Models), presentation (Views - Qt Widgets), and control/presentation logic (Controller/Presenter - often part of the widget class or dedicated helper classes).
-   **Repository Pattern**: Implemented by Service classes (e.g., `AccountService`, `JournalService`) in `app/services/`, providing an abstraction layer for data access operations and decoupling business logic from direct ORM/database specifics.
-   **Dependency Injection**: `ApplicationCore` instantiates and provides (injects) dependencies (services, managers, config) to components that require them, promoting loose coupling.
-   **Observer Pattern**: Qt's Signals and Slots mechanism is extensively used for communication between UI components, and between UI and backend logic (via `QMetaObject.invokeMethod` for thread-safe updates).
-   **Result Object Pattern (`app/utils/Result`)**: Service and Manager methods typically return a `Result` object, encapsulating success/failure status, the operation's value (if successful), or a list of error messages (if failed).
-   **Data Transfer Objects (DTOs)**: Pydantic models defined in `app/utils/pydantic_models.py` are used for structured data transfer between layers, particularly from the UI to Managers for create/update operations, ensuring data validation at the boundary.
-   **Threaded Asynchronous Execution**: A dedicated thread runs the `asyncio` event loop, allowing the Qt GUI to remain responsive while backend operations (database I/O, etc.) are performed asynchronously. `schedule_task_from_qt` and `QMetaObject.invokeMethod` bridge the two event loops.

## 3. Data Architecture

### 3.1 Database Schema Overview
The PostgreSQL database schema is central to the application's design and is meticulously defined in `scripts/schema.sql`. It is organized into four logical schemas:
1.  **`core`**: Contains tables essential for application operation and administration, including `users`, `roles`, `permissions`, `company_settings`, `configuration` (for general app settings), and `sequences` (for document numbering).
2.  **`accounting`**: Houses all tables related to core accounting functions, such as `accounts` (Chart of Accounts), `fiscal_years`, `fiscal_periods`, `journal_entries`, `journal_entry_lines`, `currencies`, `exchange_rates`, `budgets`, `tax_codes`, `gst_returns`, `dimensions`, and `recurring_patterns`.
3.  **`business`**: Designed to support business operations beyond pure accounting. Includes tables like `customers`, `vendors`, `products`, `inventory_movements`, `sales_invoices`, `purchase_invoices`, `bank_accounts`, `bank_transactions`, and `payments`. Many of these are foundational for planned features.
4.  **`audit`**: Provides a comprehensive audit trail. Includes `audit_log` (for high-level action logging) and `data_change_history` (for detailed field-level change tracking), primarily populated by database triggers.

Key characteristics of the schema include:
-   Extensive use of foreign keys to maintain referential integrity.
-   `CHECK` constraints for data validation at the database level.
-   Appropriate indexing for common query patterns to ensure performance.
-   Standardized audit columns (`created_at`, `updated_at`, `created_by`, `updated_by`) on most tables.
-   Database views (e.g., `accounting.trial_balance`, `business.customer_balances`) for simplified querying of aggregated data.
-   Stored functions (e.g., `core.get_next_sequence_value()`, `accounting.calculate_account_balance()`) to encapsulate specific database operations, some of which can be called from the application or used within other database objects.

The DDL execution order in `schema.sql` is structured to handle dependencies: Extensions & Schemas -> Tables -> Indexes -> Foreign Keys -> Views -> Functions -> Triggers.

### 3.2 SQLAlchemy ORM Models (`app/models/`)
The ORM layer, using SQLAlchemy, maps Python classes to database tables, facilitating object-oriented interaction with the data.
-   Models are organized into subdirectories mirroring the database schemas (e.g., `app/models/core/`, `app/models/accounting/`).
-   All models inherit from a common `Base` (from `sqlalchemy.orm.declarative_base()`).
-   `TimestampMixin` (`app/models/base.py`) provides `created_at` and `updated_at` columns with automatic server-side timestamping.
-   User audit fields (`created_by_user_id`, `updated_by_user_id`) are directly included in models and linked to `core.users.id` via `ForeignKey`.
-   Relationships between models (e.g., one-to-many, many-to-many) are defined using `sqlalchemy.orm.relationship`, typically with `back_populates` for bidirectional access.
-   The modern SQLAlchemy 2.0 style with `Mapped` and `mapped_column` is used for type-annotated model definitions.

**Example: `Account` Model Snippet (`app/models/accounting/account.py`)**
```python
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, CheckConstraint, Date, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import List, Optional
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin
from app.models.core.user import User # For FK type hints

class Account(Base, TimestampMixin):
    __tablename__ = 'accounts'
    __table_args__ = (
         CheckConstraint("account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')", name='ck_accounts_account_type_category'),
        {'schema': 'accounting'}
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # ... other fields like sub_type, description, parent_id, opening_balance ...
    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)
        
    parent: Mapped[Optional["Account"]] = relationship("Account", remote_side=[id], back_populates="children", foreign_keys=[parent_id])
    children: Mapped[List["Account"]] = relationship("Account", back_populates="parent")
    
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

    # Example of a back-populated relationship
    journal_lines: Mapped[List["JournalEntryLine"]] = relationship(back_populates="account") # type: ignore
    # ... other relationships ...
```

## 4. Module and Component Specifications

This section details the implementation of key modules and components, reflecting their current state in the codebase.

### 4.1 Application Startup and Core Initialization (`app/main.py`, `app/core/application_core.py`)
The application startup sequence is critical for establishing the asynchronous environment and initializing core components:
1.  **`main()` function (`app/main.py`)**:
    *   Starts the dedicated `asyncio` event loop thread (`_ASYNC_LOOP_THREAD`).
    *   Waits for the `_ASYNC_LOOP_STARTED` event, ensuring the loop is running.
    *   Instantiates `Application(QApplication)`.
    *   Connects `Application.aboutToQuit` signal to `Application.actual_shutdown_sequence`.
    *   Calls `app.exec()` to start the Qt event loop.
2.  **`Application.__init__()`**:
    *   Sets application metadata (name, version).
    *   Displays the splash screen.
    *   Uses `schedule_task_from_qt` to run `Application.initialize_app()` on the `_ASYNC_LOOP`.
3.  **`Application.initialize_app()` (async coroutine)**:
    *   Runs in the `_ASYNC_LOOP` thread.
    *   Initializes `ConfigManager`, then `DatabaseManager`.
    *   Initializes `ApplicationCore`.
    *   Calls `ApplicationCore.startup()` (which is also async).
    *   Attempts a default user authentication (e.g., "admin"/"password").
    *   Emits `initialization_done_signal` with the `ApplicationCore` instance (on success) or an exception (on failure) back to the Qt main thread.
    *   Splash screen messages are updated using `QMetaObject.invokeMethod`.
4.  **`Application._on_initialization_done()` (Qt slot)**:
    *   Receives the signal from `initialize_app()`.
    *   If successful, creates and shows `MainWindow`, passing the `ApplicationCore` instance. Finishes the splash screen.
    *   If failed, displays an error message and quits the application.
5.  **`ApplicationCore.startup()` (async method)**:
    *   Calls `self.db_manager.initialize()` to set up the database engine and connection pool.
    *   Instantiates all service and manager classes, injecting dependencies (like `db_manager` or `self` (ApplicationCore) for inter-manager/service communication).
6.  **`Application.actual_shutdown_sequence()`**:
    *   Called when the application is about to quit.
    *   Schedules `ApplicationCore.shutdown()` (async) on the `_ASYNC_LOOP`.
    *   Stops the `_ASYNC_LOOP` and joins its thread to ensure graceful cleanup.

### 4.2 Core Accounting Module

#### 4.2.1 Chart of Accounts (`app/accounting/chart_of_accounts_manager.py`, `app/ui/accounting/chart_of_accounts_widget.py`, `app/ui/accounting/account_dialog.py`)
-   **Manager (`ChartOfAccountsManager`)**:
    -   Uses `AccountService` for database operations.
    -   Employs `AccountValidator` (from Pydantic DTOs) for validating `AccountCreateData` and `AccountUpdateData`.
    -   `create_account`, `update_account`: Map DTOs to `Account` ORM model, set user audit fields, and save. Handles code uniqueness checks.
    -   `deactivate_account`: Checks if the account is already inactive and if it has a non-zero balance (using `JournalService.get_account_balance`) before proceeding.
    -   `get_account_tree`: Delegates to `AccountService.get_account_tree`, which uses a recursive SQL CTE for efficient hierarchical data retrieval.
-   **UI Widget (`ChartOfAccountsWidget`)**:
    -   Displays accounts in a `QTreeView` using `QStandardItemModel` and `QSortFilterProxyModel`.
    -   **Asynchronous Data Loading**: `_load_accounts()` is an `async` method called via `schedule_task_from_qt`. It fetches the account tree, serializes it to JSON (using `json_helpers.json_converter`), and passes the JSON string to `_update_account_model_slot` via `QMetaObject.invokeMethod`.
    -   `_update_account_model_slot()`: Runs in the Qt main thread, deserializes JSON, clears the existing model, and populates it with `QStandardItem`s, reflecting the account hierarchy. Displays Code, Name, Type, Opening Balance, and Is Active status.
    -   Actions (Add, Edit, Toggle Active) launch `AccountDialog` or trigger manager methods asynchronously.
-   **Dialog (`AccountDialog`)**:
    -   Provides fields for all `Account` attributes defined in `scripts/schema.sql` and the `Account` model, including `opening_balance`, `opening_balance_date`, `report_group`, `is_control_account`, etc.
    -   `opening_balance_date_edit` is enabled only if `opening_balance` is non-zero.
    -   On save, collects data, creates `AccountCreateData` or `AccountUpdateData` DTOs.
    -   Calls the respective `ChartOfAccountsManager` methods (`_perform_create` or `_perform_update`) asynchronously via `asyncio.ensure_future` (or could use `schedule_task_from_qt`).

#### 4.2.2 Journal Entries (`app/accounting/journal_entry_manager.py`, `app/ui/accounting/journal_entries_widget.py`, `app/ui/accounting/journal_entry_dialog.py`)
-   **Manager (`JournalEntryManager`)**:
    -   `create_journal_entry`: Validates fiscal period, generates `entry_no` using `SequenceGenerator` (which internally uses `SequenceService`). Maps `JournalEntryData` DTO to `JournalEntry` and `JournalEntryLine` ORM models. Sets user audit fields. Ensures lines are balanced (validation also in Pydantic DTO).
    -   `post_journal_entry`: Checks if already posted and if fiscal period is open. Sets `is_posted = True`.
    -   `reverse_journal_entry`: Validates original entry. Creates a new `JournalEntryData` with reversed debits/credits and negated tax amounts. Sets `source_type` to "JournalEntryReversal". Updates `is_reversed` and `reversing_entry_id` on the original entry.
    -   `generate_recurring_entries`: Fetches due `RecurringPattern`s. For each, fetches the `template_entry_id`, constructs new `JournalEntryData`, creates the JE, and updates the pattern's `last_generated_date` and `next_generation_date` (using `_calculate_next_generation_date`).
-   **UI Widget (`JournalEntriesWidget`)**:
    -   Displays entries in a `QTableView` using `JournalEntryTableModel`.
    -   Toolbar actions (New, Edit Draft, View, Post, Reverse) are contextually enabled/disabled based on selection and entry status.
    -   `_load_entries()` loads all JEs asynchronously, serializes key data (Entry No, Date, Desc, Type, Total Debit, Status) to JSON, and updates `JournalEntryTableModel` in the Qt thread.
-   **Dialog (`JournalEntryDialog`)**:
    -   Complex dialog for creating/editing JEs.
    -   Header fields: Entry Date, Journal Type (QComboBox from `JournalTypeEnum`), Description, Reference.
    -   `QTableWidget` for line items:
        -   Account: `QComboBox` populated asynchronously from `_accounts_cache`.
        -   Description: `QTableWidgetItem`.
        -   Debit/Credit: `QDoubleSpinBox` with mutual exclusion logic (if debit > 0, credit becomes 0, and vice-versa).
        -   Tax Code: `QComboBox` populated asynchronously from `_tax_codes_cache`.
        -   Tax Amount: `QTableWidgetItem` (read-only, calculated based on tax code and base amount).
        -   Delete button per line.
    -   Dynamically recalculates line tax amount upon tax code change (`_recalculate_tax_for_line`).
    -   Displays running totals for Debits, Credits, and Balance status (OK or Out of Balance with difference).
    -   Asynchronously loads existing JE data if `journal_entry_id` is provided. Disables editing for posted entries.
    -   `_collect_data()` gathers UI data into a `JournalEntryData` DTO.
    -   "Save Draft" and "Save & Post" actions call `_perform_save` asynchronously.
    -   Emits `journal_entry_saved` signal upon successful save.

#### 4.2.3 Fiscal Year and Period Management (`app/accounting/fiscal_period_manager.py`, `app/ui/settings/settings_widget.py`, `app/ui/accounting/fiscal_year_dialog.py`)
-   **Manager (`FiscalPeriodManager`)**:
    -   `create_fiscal_year_and_periods`: Key method.
        -   Validates against name conflicts and date overlaps using `FiscalYearService`.
        -   Creates `FiscalYear` ORM object.
        -   If `auto_generate_periods` (e.g., "Month", "Quarter") is specified in `FiscalYearCreateData` DTO, calls `_generate_periods_for_year_internal` to create `FiscalPeriod` records.
        -   **Transactional Integrity**: The creation of `FiscalYear` and its `FiscalPeriod`s is performed within a single database session/transaction by passing the `AsyncSession` from the manager to the internal generation method. This ensures atomicity.
    -   `close_period`, `reopen_period`: Update `FiscalPeriod.status`.
    -   `close_fiscal_year`: Checks if all constituent periods are closed. Sets `FiscalYear.is_closed = True`. (Year-end closing journal entry logic is conceptual).
-   **UI (`SettingsWidget` & `FiscalYearDialog`)**:
    -   `SettingsWidget`:
        -   Displays existing `FiscalYear`s in a `QTableView` using `FiscalYearTableModel`.
        -   "Add New Fiscal Year" button launches `FiscalYearDialog`.
        -   Data loading for table is asynchronous.
    -   `FiscalYearDialog`:
        -   Allows input for Year Name, Start Date, End Date.
        *   Automatically suggests a default end date (one year after start date minus one day).
        -   `QComboBox` for `auto_generate_periods` ("Monthly", "Quarterly", "None").
        -   On accept, validates data and creates `FiscalYearCreateData` DTO.
        -   Calls `FiscalPeriodManager.create_fiscal_year_and_periods` asynchronously.

### 4.3 Tax Management Module (`app/tax/`)
-   **`GSTManager`**:
    -   `prepare_gst_return_data`: Constructs a `GSTReturnData` DTO.
        -   **Current State**: The actual aggregation of transaction data (standard rated supplies, input tax, etc.) from `JournalEntryLine` records is currently a placeholder. It needs to query posted JEs, join with `Account` and `TaxCode` to categorize amounts based on account type and tax code.
        -   Calculates `filing_due_date` (typically end of month following period end).
    -   `save_gst_return`: Saves/updates a `GSTReturn` ORM object from `GSTReturnData`.
    -   `finalize_gst_return`: Sets `GSTReturn.status` to "Submitted".
        -   Crucially, it creates a settlement journal entry to clear GST Output/Input tax accounts to a GST Payable/Control account. It uses system account codes (configurable or defaults like "SYS-GST-OUTPUT", "SYS-GST-INPUT", "GST-PAYABLE") to build this JE.
-   **`TaxCalculator`**:
    -   Uses `TaxCodeService` to fetch `TaxCode` details (rate, type).
    -   `_calculate_gst`: Basic GST calculation (exclusive).
    -   `_calculate_withholding_tax`: Placeholder for WHT logic.

### 4.4 Financial Reporting Module (`app/reporting/`)
-   **`FinancialStatementGenerator`**:
    -   Relies on `AccountService` and `JournalService` (especially `get_account_balance` and `get_account_balance_for_period`).
    -   `generate_balance_sheet`, `generate_profit_loss`, `generate_trial_balance`: Fetch relevant accounts, calculate balances/activity, and structure them into dictionaries.
        -   Correctly uses `AccountType.is_debit_balance` (via `_get_account_type_map`) or account category heuristics to determine the natural balance of accounts for report presentation (e.g., revenue is credit-natured, so activity is negated for P&L).
        -   `get_account_balance` in `JournalService` correctly incorporates `Account.opening_balance`.
    -   `generate_income_tax_computation`: Fetches P&L, identifies "Tax Adjustment" accounts via `Account.tax_treatment`, and calculates taxable income.
    -   `generate_gst_f5`: Similar data aggregation logic to `GSTManager.prepare_gst_return_data` but tailored for direct reporting output.
-   **`ReportEngine`**:
    -   `export_report`: Takes a report data dictionary (from `FinancialStatementGenerator`) and format type ("pdf" or "excel").
    -   `_export_to_pdf_generic`: Uses `reportlab` to generate a basic PDF table structure for common reports (Trial Balance, P&L, Balance Sheet).
    -   `_export_to_excel_generic`: Uses `openpyxl` to generate an Excel spreadsheet with similar tabular data. Formatting is basic.

### 4.5 Database Triggers and Functions (from `scripts/schema.sql`)
-   **Audit Triggers (`audit.log_data_change_trigger_func`)**:
    -   Attached to key tables (e.g., `accounts`, `journal_entries`, `users`).
    -   Logs changes to `audit.audit_log` (summary) and `audit.data_change_history` (field-level changes for UPDATEs).
    -   **User Context**: Attempts to retrieve `current_setting('app.current_user_id', TRUE)::INTEGER`. If not set by the application, it falls back to `NEW.created_by` or `NEW.updated_by` if available on the record being modified.
        -   **Implementation Note**: The application must execute `SET app.current_user_id = %s` (where `%s` is the current user's ID) at the beginning of each database session/transaction for this mechanism to work reliably and capture the correct user performing the action. This is typically done in `DatabaseManager.session()` or a similar context.
-   **Timestamp Trigger (`core.update_timestamp_trigger_func`)**: Automatically updates `updated_at` columns.
-   **Database Functions**:
    -   `core.get_next_sequence_value(p_sequence_name VARCHAR)`: Atomically fetches and increments a named sequence from `core.sequences`, applying prefix/suffix and formatting. This is the preferred method for generating document numbers due to its concurrency safety.
    -   `accounting.calculate_account_balance(p_account_id INTEGER, p_as_of_date DATE)`: Calculates account balance considering opening balance and posted journal entries up to a date.
    -   `accounting.generate_journal_entry(...)`, `accounting.post_journal_entry(...)`: Database-level functions for creating and posting JEs.
        -   **Design Consideration**: There's an overlap between these DB functions and the Python `JournalEntryManager`. The project should clarify whether the Python manager calls these DB functions or reimplements the logic. DB functions can offer better atomicity for complex operations.

## 5. Deployment and Installation

### 5.1 Application Packaging
-   The project uses **Poetry** for dependency management and packaging, as defined in `pyproject.toml`.
-   For distribution, tools like PyInstaller or cx_Freeze would be used to create executables (this is future scope).

### 5.2 Database Initialization (`scripts/db_init.py`)
-   The `scripts/db_init.py` script is crucial for setting up the PostgreSQL database.
-   **Usage**: `poetry run sg_bookkeeper_db_init --user <pg_admin_user> --password <pg_admin_pass> --dbname <target_dbname> [--drop-existing]`
-   **Process**:
    1.  Connects to PostgreSQL as an administrative user (e.g., `postgres`).
    2.  Optionally drops the target database if `--drop-existing` is used and the database exists (after terminating connections).
    3.  Creates the target database if it doesn't exist.
    4.  Connects to the newly created/emptied target database.
    5.  Executes `scripts/schema.sql` to create all schemas, tables, views, functions, and triggers.
    6.  Executes `scripts/initial_data.sql` to populate default/seed data (roles, permissions, admin user, currencies, sequences, tax codes, etc.).
    7.  Sets the default `search_path` for the application database to `core, accounting, business, audit, public`.
-   **Important**: After `db_init.py` (run by a PostgreSQL superuser/admin), a dedicated application database user (e.g., `sgbookkeeper_user`) must be granted appropriate privileges on the schemas and tables (see README.md for example `GRANT` commands).

### 5.3 Application Configuration (`config.ini`)
-   The application reads its configuration from `config.ini`.
-   This file is located in a platform-specific user configuration directory (e.g., `~/.config/SGBookkeeper/config.ini` on Linux, handled by `ConfigManager`).
-   A default `config.ini` is created by `ConfigManager` if one doesn't exist.
-   Key sections include `[Database]` (connection parameters) and `[Application]` (theme, language).
-   The `[Database]` section in `config.ini` should use the credentials of the dedicated application user (e.g., `sgbookkeeper_user`), not the PostgreSQL admin user.

### 5.4 Running the Application
-   After installation (Poetry setup, DB initialization, configuration), the application is launched using:
    `poetry run sg_bookkeeper`

## 6. Security Considerations

-   **Authentication**:
    -   User passwords are hashed using `bcrypt` via `SecurityManager`.
    -   `SecurityManager` handles user login attempts and includes logic for account locking after multiple failed attempts.
-   **Authorization (RBAC)**:
    -   A role-based access control system is implemented using `core.users`, `core.roles`, `core.permissions`, and their respective junction tables.
    -   `SecurityManager.has_permission(permission_code)` is used to check if the `current_user` has a specific permission. UI elements and backend operations should be guarded by these checks.
    -   `initial_data.sql` seeds default roles and assigns all permissions to the 'Administrator' role.
-   **Audit Trails**:
    -   Comprehensive audit trails are implemented at the database level via triggers defined in `scripts/schema.sql`.
    -   `audit.log_data_change_trigger_func()` logs actions to `audit.audit_log` and field-level changes to `audit.data_change_history`.
    -   **User Context for Auditing**: The audit trigger function attempts to get the `user_id` from the PostgreSQL session variable `app.current_user_id`.
        -   **Requirement**: The application (likely in `DatabaseManager.session()`) **must** execute `SET LOCAL app.current_user_id = %s;` at the beginning of each transaction or session block, where `%s` is the ID of the authenticated application user. This ensures actions are correctly attributed in the audit log. If this session variable is not set, the trigger has fallbacks but they might not be as accurate.
-   **Data Encryption**:
    -   The `core.configuration` table has an `is_encrypted` flag, suggesting that sensitive configuration values stored in the database could be encrypted (encryption/decryption mechanism TBD).
-   **Input Validation**:
    -   Pydantic DTOs (`app/utils/pydantic_models.py`) provide initial input validation for data coming from the UI or other sources into the business logic layer.

## 7. Future Considerations / Missing Pieces (as of v4)

While significant progress has been made on core accounting and foundational architecture, several areas from the original project vision (as per `README.md`) require further development:
-   **Full Business Modules Implementation**:
    -   Customer Relationship Management (CRM).
    -   Vendor Management (beyond basic data).
    -   Sales Invoicing (full cycle from quote to invoice to payment).
    -   Purchase Invoicing (full cycle).
    -   Payment Processing and Allocation (detailed allocation to invoices).
    -   Banking Module (bank account management, transaction import, reconciliation).
    -   Product and Service Management (including basic inventory control based on `business.inventory_movements`).
    -   UI widgets, managers, and services for these modules are largely stubs or foundational.
-   **Advanced Reporting & Analytics**:
    -   Cash Flow Statement generation.
    -   Customizable Reporting Engine (beyond basic PDF/Excel tables).
    -   Dashboard with Key Performance Indicators (KPIs).
-   **Tax Compliance Enhancements**:
    -   Full implementation of Income Tax Estimation aids (`IncomeTaxManager`).
    -   Withholding Tax management and S45 form data generation (`WithholdingTaxManager`).
    -   Complete data aggregation for GST F5 return in `GSTManager`.
-   **System Features**:
    -   Robust Backup and Restore utilities.
    -   User and Role Management UI within the Settings module.
    -   Multi-company support (current design is single-company).
    -   Internationalization (i18n) support.
-   **Testing**:
    -   Comprehensive unit tests for services and managers.
    -   Integration tests for key workflows.
    -   UI tests using `pytest-qt`.
-   **Packaging and Distribution**: Creating standalone executables (e.g., using PyInstaller or similar tools).
-   **Error Handling & User Feedback**: More granular error handling and user-friendly feedback mechanisms throughout the UI.
-   **Documentation**: User manual, more detailed developer documentation for specific complex modules.

*(This TDS v4 reflects the current understanding of the implemented system and provides a strong foundation for addressing these future considerations.)*
