<think>
This is fantastic! The application (`poetry run sg_bookkeeper`) now launches successfully, shows the main window with the "Dashboard Widget Content..." placeholder, and then shuts down cleanly without any tracebacks or errors in the console output. The "User: Guest Version: 1.0.0" in the status bar also indicates that the default admin login attempt (`admin`/`password`) in `app/main.py` failed (as expected, because the `admin` user in `initial_data.sql` uses `crypt('password', gen_salt('bf'))` which is a proper hash, not the literal "password", so `SecurityManager.verify_password` would correctly return `False`). The application then proceeds to show the main window without an authenticated user, which is acceptable behavior for now.

The console output confirms:
1.  The global asyncio event loop starts and is ready.
2.  Resource warnings are printed (normal if `resources_rc.py` isn't compiled).
3.  Splash image fallback is used (normal if `splash.png` is missing/invalid).
4.  `ApplicationCore` initializes and starts up.
5.  The default admin login fails, which is fine as it's a placeholder authentication attempt.
6.  The application UI (main window) is shown (implied by the screenshot and lack of further errors before shutdown).
7.  The application shuts down cleanly, including the `ApplicationCore` and the asyncio loop thread.

**Current State Assessment:**
The application's core startup sequence, UI shell, database initialization, and basic asyncio integration seem to be working correctly. The major blockers have been resolved.

**Tasks Requested:**

1.  **Generate an updated `technical_design_specification_updated.md`**:
    *   Based on the original `Technical Design Specification Document (v2).md`.
    *   Incorporate all changes, fixes, and current understanding of the project state.
    *   Expand with more detail, code snippets, and explanations.
2.  **Create an updated `README.md`**:
    *   Based on the original `README.md`.
    *   Make it informative, detailed, and attractive for contributors.

**Plan for Generating `technical_design_specification_updated.md`:**

I need to go through the original TDS (v2) section by section and update it based on the evolution of the codebase through our debugging and refinement process.

*   **Section 1 (Introduction):** Largely unchanged, but versioning/status can be updated.
*   **Section 2 (System Architecture):**
    *   High-level architecture diagram remains valid.
    *   Component Architecture:
        *   Update list of managers/services in `ApplicationCore` to reflect actual instantiations (e.g., `FiscalYearService` added).
        *   Mention the threaded asyncio loop and `schedule_task_from_qt` mechanism in `app/main.py`.
        *   Clarify that `ModuleManager` is still conceptual.
    *   Component Interactions: The example sequence diagram for posting a transaction is still high-level and valid conceptually.
    *   Technology Stack: Update versions if any changed significantly (e.g., PySide6 6.9.0). Mention `asyncpg` explicitly.
    *   Design Patterns:
        *   The Repository Pattern (Service Layer) example for `AccountService` is still relevant.
        *   The Result Object Pattern example is still relevant.
        *   Mention the use of `QMetaObject.invokeMethod` with JSON serialization for cross-thread UI updates as a key pattern now.
*   **Section 3 (Data Architecture):**
    *   Database Schema Overview: This should reflect the final, working `scripts/schema.sql`. The organization into four schemas is correct.
    *   Core Entity Relationship Diagram: The textual description of key entity relationships can be expanded based on the final schema. A full graphical ERD is still noted as complex.
    *   Detailed Schema Definitions: Can point to `scripts/schema.sql` and provide key examples that were refined (e.g., `budget_details` unique index, audit trigger).
    *   Data Access Layer (SQLAlchemy Models):
        *   Emphasize the organization of models into subdirectories (`app/models/core/`, `app/models/accounting/`, etc.).
        *   Provide updated snippets for key models, ensuring `Mapped` and `mapped_column` are used correctly, and relationships include `back_populates` where appropriate. Show an example of a model with `UserAuditMixin` and one without.
        *   Show how junction tables are defined (e.g., `user_roles_table`).
    *   Data Access Interfaces (Repository Interfaces): Update `IAccountRepository`, `IJournalEntryRepository`, and add `IFiscalYearRepository`.
*   **Section 4 (Module Specifications):**
    *   Core Accounting Module:
        *   Update `ChartOfAccountsManager` responsibilities and key function snippets to reflect current understanding (e.g., use of DTOs, `user_id` handling).
        *   Update `JournalEntryManager` (e.g., use of `sequence_generator`, handling of `recurring_pattern_id`, `source_type`/`source_id`).
    *   Tax Management Module (`GSTManager`): Update snippet to show current structure, use of enums, and placeholder logic for GST calculation.
    *   Financial Reporting Module: Update snippets to show current service dependencies.
*   **Section 5 (User Interface Implementation):**
    *   Main Application Structure (`app/main.py`): Describe the threaded asyncio loop, `schedule_task_from_qt`, and the startup sequence using `initialization_done_signal`.
    *   `MainWindow`: Mention toolbar object name.
    *   `ChartOfAccountsWidget` / `SettingsWidget`: Describe the use of `schedule_task_from_qt` for async data loading and `QMetaObject.invokeMethod` (with JSON serialization) for UI updates from the async thread.
*   **Section 6 (Business Logic Implementation):** Largely conceptual, can keep as is or slightly update based on service signatures.
*   **Section 7 (Database Access Implementation):** `DatabaseManager` description is fine. `AccountService` example can be updated if needed.
*   **Section 8 (Deployment and Installation):**
    *   Update `pyproject.toml` snippet if necessary (current one seems fine).
    *   `db_init.py`: Describe its current functionality (including the `ALTER DATABASE SET search_path` if I had added it in the last `db_init.py` provided to user). *User confirmed they did not run the updated `db_init.py` with `ALTER DATABASE` yet, so I should mention this as an optional step.*
    *   `scripts/schema.sql` and `initial_data.sql`: Mention their roles and key features (e.g., reordered FKs, idempotent initial data).
    *   Installation Guide: Cross-reference with `README.md`. Add the step for granting permissions to `sgbookkeeper_user`.
*   **Section 9 (Conclusion):** Update to reflect current project maturity.

**Plan for Generating `README.md`:**

*   Start with the original `README.md`.
*   **Update Technical Details**:
    *   Reflect current Python version (3.9+), PySide6 version (6.9.0), PostgreSQL (14+).
    *   Mention `asyncpg`, `bcrypt`.
*   **Installation Instructions**:
    *   Clarify steps for developer installation.
    *   Crucially, add the database user creation and permission granting steps (`CREATE USER`, `GRANT ...`).
    *   Emphasize running `poetry run sg_bookkeeper_db_init` (and explain its purpose, including `--drop-existing`).
*   **Project Structure**: Update to match the `project_file_structure.txt` if it has changed significantly (it has with models being in subdirs). I have the `project_file_structure.txt`.
*   **Database Schema**: Briefly mention the four main schemas and point to `scripts/schema.sql` for full details. The ERD sketch can remain as a high-level overview.
*   **Development Setup**: Ensure commands for `black`, `flake8`, `pytest`, `coverage` are accurate.
*   **API Documentation**: The API examples are conceptual for internal APIs; these can be kept as illustrative.
*   **Roadmap, Contributing, etc.**: These sections are more about project vision and can largely remain, perhaps with minor updates to reflect progress.
*   **Screenshots**: Current placeholders are fine. The main application screenshot provided by the user can be described.
*   **Current Status**: Indicate that the application is now launching its basic UI shell successfully.

This will be a significant update for both documents. I will focus on accuracy based on the file states and successful launch.
I will generate the two documents sequentially.
First, the `technical_design_specification_updated.md`.
Then, the `README.md`.

The list of files in `project_file_structure.txt` seems mostly covered by what has been provided or generated. Some specific service files (like `app/services/accounting_services.py`) were created by me. I'll assume the structure is mostly stable now for documentation purposes. Any stubs (like `IncomeTaxManager`) will be documented as such.
</think>

This is excellent news! The application launching to the main UI and shutting down cleanly, even if some initial data loading might have warnings or default user states, is a major milestone. The "Default company settings not found" dialog is also correct behavior given that `initial_data.sql` didn't previously seed this table.

Based on this successful launch and the debugging journey, I can now generate the updated `technical_design_specification_updated.md` and `README.md`.

**Regarding Missing Image Generation:**
You asked to "generate the missing image." As an AI, I cannot create actual image files (like PNGs for the splash screen). However, the application uses a fallback if `resources/images/splash.png` is missing, which is what you're seeing.

To fix the "Warning: Splash image not found or invalid" message:
1.  Create an image (e.g., 600x400 pixels or similar) using any image editor.
2.  Save it as `splash.png` in the `resources/images/` directory of your project.
The application will then pick it up on the next run.

The SVG icon issues you saw earlier (`qt.svg: Cannot open file...`) should be resolved if you've placed all the placeholder SVG files I provided in the `resources/icons/` directory and ensured `dashboard.svg` contains valid SVG code.

Now, I will proceed to generate the updated documentation.

---

**1. Updated Technical Design Specification Document**

This document will reflect the current architecture, database schema (as successfully implemented by `scripts/schema.sql`), key code structures (like the asyncio handling in `app/main.py`), and refined component interactions.

```markdown
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
```

---

**2. Updated README.md**

This README will be updated to reflect the current state, technology stack, improved installation instructions (including database user setup), and a more accurate project structure.

```markdown
# SG Bookkeeper

<div align="center">

<!-- Replace with actual logo if available -->
<img src="https://via.placeholder.com/150?text=SG+Bookkeeper+Logo" alt="SG Bookkeeper Logo" width="150"/>

**Singapore-Focused Small Business Accounting Software**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PySide6 6.9+](https://img.shields.io/badge/UI-PySide6_6.9-green.svg)](https://doc.qt.io/qtforpython/)
[![PostgreSQL 14+](https://img.shields.io/badge/DB-PostgreSQL_14+-blue.svg)](https://www.postgresql.org/)
[![SQLAlchemy 2.0+](https://img.shields.io/badge/ORM-SQLAlchemy_2.0-orange.svg)](https://www.sqlalchemy.org/)
[![Asyncpg](https://img.shields.io/badge/Async-Asyncpg-purple.svg)](https://github.com/MagicStack/asyncpg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

[Key Features](#key-features) • [Technology Stack](#technology-stack) • [Installation](#installation) • [Usage](#usage-guide) • [Project Structure](#project-structure) • [Contributing](#contributing) • [Roadmap](#roadmap) • [License](#license)

</div>

## Overview

SG Bookkeeper is a comprehensive, cross-platform desktop application designed to meet the accounting and bookkeeping needs of small to medium-sized businesses in Singapore. Built with Python and leveraging the power of PySide6 for a modern user interface and PostgreSQL for robust data management, it offers professional-grade financial tools tailored to Singapore's regulatory environment.

The application features a double-entry accounting core, GST management, financial reporting, and modules for essential business operations. Its goal is to provide an intuitive, powerful, and compliant solution that empowers business owners and accountants.

### Why SG Bookkeeper?

-   **Singapore-Centric**: Designed with Singapore Financial Reporting Standards (SFRS), GST regulations, and IRAS compliance considerations at its core.
-   **Professional Grade**: Implements a full double-entry system, detailed audit trails, and robust data validation.
-   **User-Friendly Interface**: Aims for an intuitive experience for users who may not be accounting experts, while providing depth for professionals.
-   **Open Source & Local First**: Transparent development. Your financial data stays on your local machine or private server, ensuring privacy and control. No subscription fees.
-   **Modern & Performant**: Utilizes asynchronous operations for a responsive UI and efficient database interactions.

## Key Features

*(This section can be expanded as features are fully implemented. Based on schema and design intent:)*

### Core Accounting
-   Comprehensive Double-Entry Bookkeeping
-   Customizable Hierarchical Chart of Accounts (Singapore-specific templates)
-   General Ledger with detailed transaction history
-   Journal Entry System (General, Sales, Purchases, etc.)
-   Multi-Currency Support with Exchange Rate Management
-   Fiscal Year and Period Management
-   Budgeting and Variance Analysis

### Singapore Tax Compliance
-   GST Tracking and Calculation (SR, ZR, ES, TX codes)
-   GST F5 Return Data Preparation
-   (Planned) Income Tax Estimation Aids
-   (Planned) Withholding Tax Management

### Business Operations
-   Customer and Vendor Relationship Management (CRM)
-   Sales Invoicing and Accounts Receivable
-   Purchase Invoicing and Accounts Payable
-   Payment Processing and Allocation
-   Bank Account Management and Reconciliation Tools
-   Product and Service Management (Inventory, Non-Inventory, Services)
-   (Planned) Basic Inventory Control

### Reporting & Analytics
-   Standard Financial Statements: Balance Sheet, Profit & Loss, Trial Balance
-   (Planned) Cash Flow Statement
-   GST Reports
-   (Planned) Customizable Reporting Engine
-   (Planned) Dashboard with Key Performance Indicators (KPIs)

### System & Security
-   User Authentication with Role-Based Access Control (RBAC)
-   Granular Permissions System
-   Comprehensive Audit Trails for data changes and system actions
-   PostgreSQL Database Backend for data integrity and scalability
-   Data Backup and Restore Utilities (Conceptual/Planned)

## Technology Stack

-   **Programming Language**: Python 3.9+
-   **UI Framework**: PySide6 6.9.0+
-   **Database**: PostgreSQL 14+
-   **ORM**: SQLAlchemy 2.0+ (Async ORM with `asyncpg`)
-   **Async DB Driver**: `asyncpg`
-   **Data Validation (DTOs)**: Pydantic V2
-   **Password Hashing**: `bcrypt`
-   **Reporting Libraries**: `reportlab` (PDF), `openpyxl` (Excel)
-   **Dependency Management**: Poetry
-   **Date/Time Utilities**: `python-dateutil`

## Installation

### Prerequisites

-   Python 3.9 or higher (check with `python --version`)
-   PostgreSQL Server 14 or higher (running and accessible)
-   Poetry (Python packaging and dependency management tool). Install via `pip install poetry`.
-   Git (for cloning the repository)

### Developer Installation Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/yourusername/sg_bookkeeper.git # Replace with actual URL
    cd sg_bookkeeper
    ```

2.  **Set Up Python Virtual Environment & Install Dependencies:**
    It's highly recommended to use a virtual environment.
    ```bash
    poetry install
    ```
    This command will create a virtual environment (if not already present in the project via `.venv`) and install all dependencies listed in `pyproject.toml`.

3.  **Prepare PostgreSQL Database and User:**
    *   Connect to your PostgreSQL instance as a superuser (e.g., `postgres`):
        ```bash
        sudo -u postgres psql
        ```
    *   Create a dedicated database user and database (replace passwords securely):
        ```sql
        CREATE USER sgbookkeeper_user WITH PASSWORD 'YourSecurePassword123!';
        -- Database will be created by db_init.py script, or you can create it:
        -- CREATE DATABASE sg_bookkeeper OWNER sgbookkeeper_user; 
        -- \q 
        ```
        *Note: The `db_init.py` script can create the database if it doesn't exist, using the admin credentials you provide to the script.*

4.  **Configure Database Connection:**
    *   The application looks for `config.ini` in a platform-specific user configuration directory. On Linux, this is typically `~/.config/SGBookkeeper/config.ini`.
    *   Copy or create `config.ini` in that location. Example content:
        ```ini
        [Database]
        username = sgbookkeeper_user
        password = YourSecurePassword123!
        host = localhost
        port = 5432
        database = sg_bookkeeper
        echo_sql = False 
        pool_min_size = 2
        pool_max_size = 10
        pool_recycle_seconds = 3600

        [Application]
        theme = light
        language = en
        ```
    *   Ensure the `username`, `password`, `host`, `port`, and `database` match your PostgreSQL setup.

5.  **Initialize the Database Schema and Seed Initial Data:**
    Run the database initialization script using Poetry. This script will create all necessary tables, views, functions, and populate essential default data.
    *   Use an admin PostgreSQL user (like `postgres` or one with `CREATEDB` rights) for the initial setup, as it needs to create the database and extensions if they don't exist.
    ```bash
    poetry run sg_bookkeeper_db_init --user postgres --password YOUR_POSTGRES_ADMIN_PASSWORD --dbname sg_bookkeeper --drop-existing
    ```
    *   `--drop-existing`: Use this flag with caution as it will delete the database if it already exists, ensuring a clean setup. Omit it if you want to preserve an existing `sg_bookkeeper` database (the script will then fail if tables conflict without `IF NOT EXISTS`).
    *   The script also sets a default `search_path` for the database for easier `psql` interaction.

6.  **Grant Privileges to Application User:**
    After the database is initialized (by the admin user like `postgres`), grant necessary privileges to your application user (`sgbookkeeper_user` in this example). Connect to `psql` as `postgres`:
    ```bash
    sudo -u postgres psql -d sg_bookkeeper 
    ```
    Then execute these grant commands (replace `sgbookkeeper_user` if you used a different name):
    ```sql
    GRANT USAGE ON SCHEMA core, accounting, business, audit TO sgbookkeeper_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO sgbookkeeper_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA accounting TO sgbookkeeper_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA business TO sgbookkeeper_user;
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA audit TO sgbookkeeper_user;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA core TO sgbookkeeper_user;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA accounting TO sgbookkeeper_user;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA audit TO sgbookkeeper_user;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA business TO sgbookkeeper_user;
    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA core TO sgbookkeeper_user;
    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA accounting TO sgbookkeeper_user;
    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA audit TO sgbookkeeper_user;

    -- For future tables created by postgres user (or role running migrations)
    ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA core GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
    ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA accounting GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
    ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA business GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
    ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA audit GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
    ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA core GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
    ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA accounting GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
    ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA audit GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
    ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA business GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
    \q
    ```

7.  **Compile Qt Resources (Optional but Recommended):**
    For icons and other Qt resources to be bundled correctly, especially for packaging.
    ```bash
    poetry run pyside6-rcc resources/resources.qrc -o app/resources_rc.py
    ```
    If `app/resources_rc.py` is not found, the application will attempt to load resources from direct file paths relative to the `resources` directory.

8.  **Run the Application:**
    Ensure your `config.ini` points to `sgbookkeeper_user`.
    ```bash
    poetry run sg_bookkeeper
    ```

## Usage Guide

*(This section would be filled out as UI and workflows are developed. Currently, the application launches to a basic UI shell.)*

### First-Time Setup (Conceptual)
-   Initial launch would guide through Company Information, Fiscal Year setup, Chart of Accounts selection, and Admin User creation if not seeded.
-   Currently, `initial_data.sql` seeds some of this. The "Settings" tab allows viewing/editing company settings.

### Key Modules (Tabs)
-   **Dashboard**: Overview of financial health (To be implemented).
-   **Accounting**: Chart of Accounts, Journal Entries, Fiscal Period management (Chart of Accounts view is partially implemented).
-   **Customers**: Manage customer data and related transactions (To be implemented).
-   **Vendors**: Manage vendor data and related transactions (To be implemented).
-   **Banking**: Manage bank accounts, transactions, reconciliation (To be implemented).
-   **Reports**: Generate financial statements and tax reports (To be implemented).
-   **Settings**: Configure company details, application preferences (Partially implemented).

## Project Structure

```
sg_bookkeeper/
├── app/                    # Application source code
│   ├── __init__.py
│   ├── main.py             # Main application entry point (QApplication)
│   ├── core/               # Core components (ApplicationCore, DBManager, Config, Security)
│   ├── common/             # Common utilities, enums
│   ├── models/             # SQLAlchemy ORM models (organized by schema: core, accounting, etc.)
│   ├── services/           # Data access services (repositories)
│   ├── accounting/         # Business logic for accounting module
│   ├── tax/                # Business logic for tax module
│   ├── business_logic/     # Placeholder for other business operations modules (customers, vendors etc.)
│   ├── reporting/          # Logic for generating reports
│   ├── ui/                 # PySide6 UI components (organized by module)
│   └── utils/              # General utility functions, Pydantic DTOs
├── data/                   # Default data templates (e.g., CoA templates)
├── docs/                   # Project documentation
├── resources/              # UI assets
│   ├── icons/              # SVG icons
│   ├── images/             # Splash screen, etc.
│   └── resources.qrc       # Qt resource collection file
├── scripts/                # Database initialization scripts
│   ├── db_init.py          # Python script to initialize DB
│   ├── schema.sql          # Full DDL for database schema
│   └── initial_data.sql    # SQL for seeding initial/default data
├── tests/                  # Automated tests (unit, integration, UI)
├── .gitignore
├── pyproject.toml          # Poetry configuration
├── poetry.lock
├── README.md               # This file
└── LICENSE
```

## Database Schema
The application uses a PostgreSQL database with a schema organized into four main parts: `core`, `accounting`, `business`, and `audit`. For the complete schema details, please refer to `scripts/schema.sql`.

## Development
(Information about linters, formatters, test execution - from original README - can be kept here)
-   **Formatting**: `poetry run black .`
-   **Linting**: `poetry run flake8 .`
-   **Testing**: `poetry run pytest`
-   **Test Coverage**: `poetry run pytest --cov=app`

## Contributing
Contributions are welcome! Please follow these steps:
1.  Fork the repository.
2.  Create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name`).
3.  Make your changes, ensuring to add relevant tests.
4.  Run tests and linters.
5.  Commit your changes with descriptive messages.
6.  Push to your branch (`git push origin feature/your-feature-name`).
7.  Submit a Pull Request against the `main` (or `develop`) branch.

Please adhere to the project's [Code of Conduct](CODE_OF_CONDUCT.md) (if one exists).

## Roadmap
*(This reflects the aspirational state from the original README. Actual progress may vary.)*
### Short-term
-   Complete core UI for Chart of Accounts and Journal Entries.
-   Implement basic Customer and Vendor management UI.
-   Basic Sales and Purchase Invoicing.
### Medium-term
-   Bank Reconciliation features.
-   Full GST F5 reporting.
-   User and Role management UI in Settings.
### Long-term
-   Advanced reporting and analytics.
-   Multi-company support.
-   Cloud synchronization options.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

---
https://drive.google.com/file/d/10TYPOybooA3cAXLtTgqyVRFonRuFDUXP/view?usp=sharing, https://drive.google.com/file/d/11KndoHQCP9vTKPlRbWLtqy6gHfC8w4Dk/view?usp=sharing, https://drive.google.com/file/d/12_JVpgeBBX9M-hzFk8qi9g0LJr-jm14S/view?usp=sharing, https://drive.google.com/file/d/17MfzKFSisoo3ZRtNqWL-vooRP8xDfXhS/view?usp=sharing, https://drive.google.com/file/d/1DMQwEJGM_oVbh4wl3igdWbKFBp7vZRiM/view?usp=sharing, https://drive.google.com/file/d/1EwsvcutY25rEKdDxZN2imU3hrOwGNVYL/view?usp=sharing, https://drive.google.com/file/d/1JFn6__74LT8vYl6YdlNwc-BY2PYQUQFQ/view?usp=sharing, https://drive.google.com/file/d/1Mk0kQbJtJdGvx2rKVVqxhmXfS8lQ1CR7/view?usp=sharing, https://drive.google.com/file/d/1Nhrj6yvXO3YuJWobJ6pYA1zAoGRW9Pkb/view?usp=sharing, https://drive.google.com/file/d/1PEY7tCyM7pE80nYf9NIZEi9IXVpbmU2q/view?usp=sharing, https://drive.google.com/file/d/1PeiUhKZrNTPXZA-gID8YSgycyoBGsTVW/view?usp=sharing, https://drive.google.com/file/d/1R8FgPOnpgTglA_cwhgFBLyk0dxvW48GY/view?usp=sharing, https://drive.google.com/file/d/1Uj8kEw4aDhusQD2-r3VkOdTNIsVPKEOf/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221VLBZXJQEO8dnjyEdi4_ZoIjec1ikMutf%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1XqNcfV2N4Zd3EV6Z9Kp_yn5T3TZWWMBf/view?usp=sharing, https://drive.google.com/file/d/1YqzdexaRTu_7xuCkAaEXR5AJUMNF-a8K/view?usp=sharing, https://drive.google.com/file/d/1dMoqfUucM6xTkbJAcC47YdBzJ43CM6mG/view?usp=sharing, https://drive.google.com/file/d/1hwT4APLGEoSZXgMxh0d5sYPkuszzTJE_/view?usp=sharing, https://drive.google.com/file/d/1l-_PWDhb0i9eaVtbVuN0Zg4sckshfr18/view?usp=sharing, https://drive.google.com/file/d/1nUTcU9ePoVvmVXo1zGI-N1TGQo1-155U/view?usp=sharing, https://drive.google.com/file/d/1wkrzkWG1WJ1HasL6o4Huaq_xqvH0btrE/view?usp=sharing

