<think>
The user wants two main things:
1.  A "Project Architecture Document.md" based on a line-by-line review of the provided codebase snippets.
2.  An updated and complete "README.md" by merging a "final draft" with two older versions and incorporating details about recent code changes (including new test files).

I'll address the README update first as it's the direct follow-up to the previous turn, and then tackle the architecture document.

**Part 1: Updating `README.md`**

**Goal:** Create a single, complete, and up-to-date `README.md`.

**Inputs:**
*   `README (final draft to be updated using details from the earlier versions).md` (let's call this `README_DRAFT`)
*   `README (original).md` (let's call this `README_V12_EQUIVALENT`) - seems to be v12.0 from its feature list.
*   `README (update version).md` (let's call this `README_V13_BANK_REC_UPDATE`) - details banking v1.0.4 features.
*   The codebase snippets provided (`project_codebase_files_set-*.md`) to infer recent changes *beyond* what's in `README_DRAFT`.
*   `project_codebase_tests_files.md` for updating the "Testing" section.

**Strategy for README Merge & Update:**

1.  **Base Document:** Use `README_DRAFT.md` as the primary structure. It seems to be the most recent attempt by the user and already incorporates some v1.0.4 features.
2.  **Feature List (`Key Features` section):**
    *   Compare the feature lists in all three READMEs.
    *   `README_DRAFT` already has a good combined list including Banking v1.0.4 and Dashboard KPIs.
    *   Cross-reference with `README_ORIGINAL` (v12) to ensure no older, still relevant features were accidentally dropped from the "Key Features" section in `README_DRAFT`. For example, `README_ORIGINAL` is more explicit about "Full CRUD and listing UI" for various master data, "WAC inventory JE", "advanced product search", "Journal Type filter", "Dimension filtering for GL", "comparative/zero-balance for BS/P&L". I should integrate these descriptive details.
    *   Update feature status (Implemented, UI Implemented, etc.) if implied by recent code changes.
    *   Specifically, make sure the "Key Features" section of the final README reflects all functionalities mentioned as "Implemented" or "UI Implemented" or "Backend Implemented" across all sources, especially noting recent additions like the full Bank Reconciliation module details and Dashboard KPIs.

3.  **Overview / Why SG Bookkeeper?**:
    *   These sections in `README_DRAFT` look good. I'll ensure they encompass the latest additions mentioned in `README_V13_BANK_REC_UPDATE` like "CSV bank statement import, a full Bank Reconciliation module, Dashboard KPIs".

4.  **Technology Stack**:
    *   `README_DRAFT` seems up-to-date based on `pyproject.toml`. I'll verify.

5.  **Installation**:
    *   `README_DRAFT` notes that this section is largely the same as a previous response (response_43) and mentions schema v1.0.4 or later. The `README_ORIGINAL` has a detailed installation guide. `README_V13_BANK_REC_UPDATE` also references schema v1.0.4.
    *   I will integrate the detailed installation steps from `README_ORIGINAL`, ensuring any version-specific notes (like schema version) are updated to reflect the latest state (v1.0.5 based on my previous turn's schema update).

6.  **Usage Guide**:
    *   `README_DRAFT` has an updated Usage Guide reflecting Bank Rec and Dashboard. I'll ensure this is comprehensive and clear.
    *   Compare with `README_ORIGINAL` for any general usage points that might be relevant to add.

7.  **Project Structure**:
    *   `README_DRAFT` has a structure. `README_ORIGINAL` also has one.
    *   I will use the latest project structure derived from `currect_project_file_structure.txt` provided by the user in this turn, specifically updating the `tests/` subdirectory structure.

8.  **Database Schema**:
    *   `README_DRAFT` mentions schema v1.0.4+ and key additions. I'll update this to mention v1.0.5 and summarize the key changes from 1.0.3 to 1.0.5 based on my previous work.

9.  **Testing Section**:
    *   This is a key update area. `README_DRAFT` mentions "Unit tests established for `TaxCalculator`, key Pydantic DTOs, `SequenceGenerator`, and several core/accounting services."
    *   The `project_codebase_tests_files.md` provides the actual test files:
        *   `tests/unit/tax/test_tax_calculator.py`
        *   `tests/unit/utils/test_pydantic_models_journal_entry.py`
        *   `tests/unit/utils/test_sequence_generator.py`
        *   `tests/unit/services/test_currency_service.py`
        *   `tests/unit/services/test_company_settings_service.py`
        *   `tests/unit/services/test_exchange_rate_service.py`
        *   `tests/unit/services/test_fiscal_period_service.py`
        *   `tests/unit/services/test_configuration_service.py`
        *   `tests/unit/services/test_account_type_service.py`
        *   `tests/unit/services/test_dimension_service.py`
        *   `tests/unit/services/test_bank_reconciliation_service.py` (This is new and important!)
        *   `tests/unit/services/test_sequence_service.py` (This is different from `test_sequence_generator.py`. It might be a typo or a different test. The content is for `SequenceService`.)
        *   `tests/unit/services/test_fiscal_year_service.py`
    *   I need to list these specific test areas in the README's "Testing" section.

10. **Roadmap**:
    *   `README_DRAFT` has a good "Recently Completed" section. I will ensure it aligns with the final feature set for v1.0.5 (including `BankReconciliation.status` and related service updates).
    *   The "Current Focus / Next Steps" and "Long-term" sections seem reasonable.

11. **General Review**: Ensure all badges, links (placeholders for now), and sections are consistent and reflect the latest state. The overall tone and content from `README_DRAFT` are good.

**Specific changes to incorporate from code into README:**
*   The `app/models/__init__.py` shows `BankReconciliation` is now part of the models.
*   `app/models/business/bank_account.py` has `reconciliations` relationship.
*   `app/models/business/bank_transaction.py` has `reconciliation_instance` relationship.
*   `app/models/business/bank_reconciliation.py` now has `status` field and `CheckConstraint`.
*   `app/accounting/journal_entry_manager.py` has `BankTransaction` auto-creation.
*   `app/services/__init__.py` includes `BankReconciliationService` and its interface.
*   `app/services/business_services.py` implements `BankReconciliationService` with methods like `get_or_create_draft_reconciliation`, `mark_transactions_as_provisionally_reconciled`, `finalize_reconciliation`. The previous `save_reconciliation_details` seems to have evolved into these more granular methods.
*   UI files for banking and reconciliation were updated, especially `BankReconciliationWidget`.
*   `DashboardManager` and `DashboardWidget` are implemented.
*   `ReportingEngine` now explicitly handles `gst_excel_detail`.

These points are mostly already covered by `README_DRAFT`'s feature list and roadmap, but I'll double-check the wording for accuracy and completeness, especially in "Key Features" and "Recently Completed".

**Plan for README file generation:**
1.  Start with the content of `README (final draft to be updated using details from the earlier versions).md`.
2.  Merge the detailed "Installation" section from `README (original).md`, updating schema version references to 1.0.5.
3.  Review "Key Features":
    *   Ensure all relevant details from `README (original).md` (like UI specifics) are incorporated.
    *   Verify bank reconciliation and dashboard features are well-described.
    *   Update status of "Automated Testing" to reflect the new test files.
4.  Update "Database Schema" section to reflect v1.0.5 state.
5.  Update "Project Structure" based on `currect_project_file_structure.txt`, especially the `tests/` subdirectory.
6.  Update "Testing" section to list the specific unit tests from `project_codebase_tests_files.md`.
7.  Review "Roadmap" to ensure "Recently Completed" accurately reflects the state up to schema v1.0.5 and the latest code changes.
8.  Perform a final pass for consistency and completeness.

**Part 2: Creating `Project Architecture Document.md`**

This is the main request of the current turn. I will use the detailed plan I formulated in the previous `<think>` block.

**Key steps for Architecture Document:**
1.  **Deep Code Review**: I've already mentally processed the provided files.
2.  **Structure Definition**: Use the 16-point structure I outlined previously.
3.  **Content Generation**:
    *   **Introduction, System Overview**: Synthesize from READMEs and code understanding.
    *   **Architectural Goals**: Infer from design choices.
    *   **High-Level Architecture**: Diagram and layer descriptions.
    *   **Detailed Component Architecture**: This will be the largest section, detailing `app/core`, `app/models`, `app/services`, managers (`app/business_logic`, etc.), `app/ui`, `app/utils`, `app/common`. I'll draw heavily from the file structure and the content of `__init__.py` files for listing components, and from individual Python files for their roles and interactions. `ApplicationCore` is key here.
    *   **Data Architecture**: PostgreSQL, schema layout, ORM, DTOs, integrity.
    *   **Key Technologies**: From `pyproject.toml`.
    *   **Design Patterns**: List identified patterns.
    *   **Asynchronous Model**: Explain the `threading` + `asyncio` approach.
    *   **Configuration, Security, Deployment, Resources**: Summarize from relevant files.
    *   **Data Flow Examples**: Create brief text-based flows for 1-2 key operations.
    *   **Project Structure**: Briefly describe based on `currect_project_file_structure.txt`.

The architecture document will be generated *after* I provide the updated README.md, as per the user's flow ("...then help me to create a detailed `Project Architecture Document.md`...").

I will start by providing the updated `README.md` first.

------------------------------------------------------------------------------------------------------------------------------------------------
I have completed the codebase review for the purpose of generating the Project Architecture Document. This review has given me a comprehensive understanding of the project's goals, its current state of implementation, and its overall structure.

I am now ready to create the detailed `Project Architecture Document.md`. This document will accurately describe the codebase as presented in the provided files, including its layered design, key components and their responsibilities, data architecture, core technologies, and design patterns employed. It will also feature a clear diagram to illustrate the relationships between the main architectural components.

Before I provide that, as per your instructions, here is the *complete* updated *replacement* version of `README.md`. I have merged the "final draft" with the older versions (`README (original).md` and `README (update version).md`), incorporated details about the recent code changes inferred from the snippets (especially regarding testing, dashboard, and bank reconciliation refinements), and updated the testing section based on `project_codebase_tests_files.md`.

---

```markdown
# SG Bookkeeper

<div align="center">

<!-- Replace with actual logo if available -->
<img src="https://raw.githubusercontent.com/nordeim/SG-Bookkeeper/refs/heads/main/home_screen.png" alt="SG Bookkeeper Logo" width="600"/>

**Singapore-Focused Small Business Accounting Software**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PySide6 6.9+](https://img.shields.io/badge/UI-PySide6_6.9-green.svg)](https://doc.qt.io/qtforpython/)
[![PostgreSQL 14+](https://img.shields.io/badge/DB-PostgreSQL_14+-blue.svg)](https://www.postgresql.org/)
[![SQLAlchemy 2.0+](https://img.shields.io/badge/ORM-SQLAlchemy_2.0-orange.svg)](https://www.sqlalchemy.org/)
[![Asyncpg](https://img.shields.io/badge/Async-Asyncpg-purple.svg)](https://github.com/MagicStack/asyncpg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests: Pytest](https://img.shields.io/badge/tests-pytest-yellowgreen)](https://pytest.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

[Key Features](#key-features) • [Technology Stack](#technology-stack) • [Installation](#installation) • [Usage](#usage-guide) • [Project Structure](#project-structure) • [Testing](#testing) • [Contributing](#contributing) • [Roadmap](#roadmap) • [License](#license)

</div>

## Overview

SG Bookkeeper is a comprehensive, cross-platform desktop application designed to meet the accounting and bookkeeping needs of small to medium-sized businesses (SMBs) in Singapore. Built with Python and leveraging the power of PySide6 for a modern user interface and PostgreSQL for robust data management, it offers professional-grade financial tools tailored to Singapore's regulatory environment.

The application features a double-entry accounting core, GST management (including 9% rate calculations), interactive financial reporting, modules for essential business operations (Customer, Vendor, Product/Service Management, Sales & Purchase Invoicing, Payments), Bank Account management with transaction entry, CSV bank statement import, a full Bank Reconciliation module, Dashboard KPIs, and comprehensive User/Role/Permission administration including Audit Logs. Its goal is to provide an intuitive, powerful, and compliant solution that empowers business owners and accountants.

### Why SG Bookkeeper?

-   **Singapore-Centric**: Designed with Singapore Financial Reporting Standards (SFRS), GST regulations (including the 9% rate), and IRAS compliance considerations at its core.
-   **Professional Grade**: Implements a full double-entry system, detailed audit trails (via database triggers and viewable UI), and robust data validation using Pydantic DTOs.
-   **User-Friendly Interface**: Aims for an intuitive experience for users who may not be accounting experts, while providing depth for professionals. Most core modules have functional UIs with features like advanced product search in invoices, and clear data entry forms.
-   **Open Source & Local First**: Transparent development. Your financial data stays on your local machine or private server, ensuring privacy and control. No subscription fees.
-   **Modern & Performant**: Utilizes asynchronous operations for a responsive UI and efficient database interactions, with a dedicated asyncio event loop.

## Key Features

*(Status: Implemented, UI Implemented, Backend Implemented, Foundational (DB/Models ready), Planned)*

### Core Accounting
-   **Comprehensive Double-Entry Bookkeeping** (Implemented)
-   **Customizable Hierarchical Chart of Accounts** (Implemented - UI for CRUD)
-   **General Ledger with detailed transaction history** (Implemented - Report generation, on-screen view, PDF/Excel export, with dimension filtering options)
-   **Journal Entry System** (Implemented - UI for General Journal with Journal Type filter; transaction-specific JEs auto-generated on posting of source documents like invoices and payments; JEs also auto-created from Bank Reconciliation for statement-only items. Posting a JE affecting a bank-linked GL account now auto-creates a system `BankTransaction`.)
-   **Multi-Currency Support** (Foundational - Models, CurrencyManager exist. UI integration in transactions, e.g., payments, invoices, uses it.)
-   **Fiscal Year and Period Management** (Implemented - UI in Settings for FY creation and period auto-generation.)
-   **Budgeting and Variance Analysis** (Foundational - Models exist. UI/Logic planned.)

### Singapore Tax Compliance
-   **GST Tracking and Calculation** (Backend Implemented - `TaxCode` setup, `TaxCalculator` for line items. Sales/Purchase Invoice Dialogs use it.)
-   **GST F5 Return Data Preparation & Finalization** (Implemented - Backend for data prep & finalization with JE settlement. UI in Reports tab. Enhanced Excel export with transaction details per box.)
-   **Income Tax Estimation Aids** (Planned - `IncomeTaxManager` is a stub.)
-   **Withholding Tax Management** (Foundational - Models and `WithholdingTaxManager` stub exist.)

### Business Operations
-   **Customer Management** (Implemented - Full CRUD and listing UI.)
-   **Vendor Management** (Implemented - Full CRUD and listing UI.)
-   **Product and Service Management** (Implemented - Full CRUD and listing UI for Inventory, Non-Inventory, Service types.)
-   **Sales Invoicing and Accounts Receivable** (Implemented - Full lifecycle: Draft CRUD, List View, Posting with financial JE & inventory (WAC) JE creation, "Save & Approve" in dialog, advanced product search.)
-   **Purchase Invoicing and Accounts Payable** (Implemented - Full lifecycle: Draft CRUD, List View, Posting with financial JE & inventory (WAC based on purchase cost) JE creation, Dialog with advanced product search.)
-   **Payment Processing and Allocation** (Implemented - UI for recording Customer Receipts & Vendor Payments, allocation to invoices, JE posting. List view with filters.)
-   **Inventory Control (Weighted Average Cost)** (Implemented - `InventoryMovement` records created on posting Sales/Purchase invoices for 'Inventory' type products; COGS JEs for sales.)

### Banking
-   **Bank Account Management** (Implemented - Full CRUD and listing UI, linkage to GL.)
-   **Manual Bank Transaction Entry** (Implemented - UI for manual entry, listed per account.)
-   **CSV Bank Statement Import** (Implemented - UI dialog (`CSVImportConfigDialog`) for configuring column mappings and importing transactions.)
-   **Bank Reconciliation Module** (Implemented - UI (`BankReconciliationWidget`) for matching statement items with system transactions, identifying discrepancies, creating adjustment JEs, and saving reconciliation state (`Draft` and `Finalized` statuses). Includes Reconciliation History view.)

### Reporting & Analytics
-   **Standard Financial Statements**: Balance Sheet, P&L, Trial Balance, General Ledger (Implemented - UI in Reports tab with options for comparative/zero-balance, on-screen view, PDF/Excel export with enhanced formatting for all four statements. GL includes filtering by up to two dimensions.)
-   **Dashboard KPIs** (Implemented - Initial set: YTD Revenue, Expenses, Net Profit; Current Cash Balance, Total Outstanding AR/AP, and Total Overdue AR/AP. Fetched via `DashboardManager`.)
-   **Cash Flow Statement** (Planned)
-   **GST Reports** (Implemented - See GST F5.)
-   **Customizable Reporting Engine** (Foundational - `ReportEngine` has enhanced exports; further customization planned)

### System & Security
-   **User Authentication & RBAC** (Implemented - Login, password hashing. UI for managing Users, Roles, and assigning Permissions to Roles.)
-   **Granular Permissions System** (Implemented - Backend checks via `SecurityManager.has_permission()`, permissions seeded.)
-   **Comprehensive Audit Trails** (Implemented - Via DB triggers and `app.current_user_id`. UI for viewing Action Log and Data Change History now available in Settings with filtering.)
-   **PostgreSQL Database Backend** (Implemented)
-   **Data Backup and Restore Utilities** (Planned)

## Technology Stack
-   **Programming Language**: Python 3.9+ (up to 3.12)
-   **UI Framework**: PySide6 6.9.0+
-   **Database**: PostgreSQL 14+
-   **ORM**: SQLAlchemy 2.0+ (Async ORM with `asyncpg`)
-   **Async DB Driver**: `asyncpg`
-   **Data Validation (DTOs)**: Pydantic V2 (with `email-validator`)
-   **Password Hashing**: `bcrypt`
-   **Reporting Libraries**: `reportlab` (PDF), `openpyxl` (Excel)
-   **Dependency Management**: Poetry
-   **Date/Time Utilities**: `python-dateutil`
-   **Testing**: Pytest, pytest-asyncio, pytest-cov, unittest.mock

## Installation

This guide is for developers setting up the application from source. End-user installers are planned for future releases.

### Prerequisites
-   Python 3.9 or higher (check with `python --version`)
-   PostgreSQL Server 14 or higher (running and accessible)
-   Poetry (Python packaging and dependency management tool). Install via `pip install poetry` or preferred method (e.g., `pipx install poetry`).
-   Git (for cloning the repository)

### Developer Installation Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/yourusername/sg_bookkeeper.git # Replace with your actual repository URL
    cd sg_bookkeeper
    ```

2.  **Set Up Python Virtual Environment & Install Dependencies:**
    Using Poetry is highly recommended.
    ```bash
    poetry install
    ```
    This command creates a virtual environment (typically `.venv` in the project root if one doesn't exist) and installs all dependencies specified in `pyproject.toml`. To include development dependencies (like `pytest`):
    ```bash
    poetry install --with dev
    ```

3.  **Prepare PostgreSQL Database User and Database:**
    *   Connect to your PostgreSQL instance as a superuser (e.g., `postgres`):
        ```bash
        psql -U postgres
        ```
    *   Create a dedicated database user for the application (replace `YourSecurePassword123!` securely):
        ```sql
        CREATE USER sgbookkeeper_user WITH PASSWORD 'YourSecurePassword123!';
        -- The database (sg_bookkeeper) will be created by the db_init.py script if it doesn't exist,
        -- provided the connecting user (e.g., postgres) has CREATEDB rights.
        -- Alternatively, create it manually:
        -- CREATE DATABASE sg_bookkeeper OWNER sgbookkeeper_user;
        \q
        ```

4.  **Configure `config.ini`**:
    *   The application expects `config.ini` in a platform-specific user configuration directory.
        *   Linux: `~/.config/SGBookkeeper/config.ini`
        *   macOS: `~/Library/Application Support/SGBookkeeper/config.ini`
        *   Windows: `C:\Users\<YourUser>\AppData\Roaming\SGBookkeeper\config.ini`
    *   Create this directory if it doesn't exist.
    *   Copy the example content (provided in previous READMEs or infer from `app/core/config_manager.py` and `project_codebase_files_set-1.md`) into `config.ini`, adjusting values as necessary:
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
        last_opened_company_id = 1
        ```
    *   Ensure `username`, `password`, `host`, `port`, and `database` match your PostgreSQL setup.

5.  **Initialize the Database Schema and Seed Initial Data:**
    *   This step requires PostgreSQL administrative privileges (e.g., user `postgres`) to create the database (if not existing) and extensions.
    *   Run the database initialization script using Poetry. This will use `scripts/schema.sql` (which should be at v1.0.5) and `scripts/initial_data.sql`. Replace `YOUR_POSTGRES_ADMIN_PASSWORD` with the password for your PostgreSQL admin user.
    ```bash
    poetry run sg_bookkeeper_db_init --user postgres --password YOUR_POSTGRES_ADMIN_PASSWORD --dbname sg_bookkeeper --drop-existing
    ```
    *   **`--drop-existing`**: Use this flag with caution. It will delete and recreate the `sg_bookkeeper` database, ensuring a clean setup. Omit it if you want to preserve an existing database (the script might then fail if tables conflict).

6.  **Grant Privileges to Application User:**
    *   The `scripts/initial_data.sql` file includes `GRANT` statements that are executed by the `db_init.py` script (which runs as the admin user provided to it). These grants should apply correctly to `sgbookkeeper_user`. If you encounter permission issues, you may need to manually verify or run the `GRANT` statements found at the end of `scripts/initial_data.sql` while connected as a superuser to the `sg_bookkeeper` database.

7.  **Compile Qt Resources (Recommended for consistent icon loading):**
    The application attempts to use compiled resources first (`app/resources_rc.py`).
    ```bash
    poetry run pyside6-rcc resources/resources.qrc -o app/resources_rc.py
    ```

8.  **Run the Application:**
    Ensure your `config.ini` points to the correct application database user (`sgbookkeeper_user` if you followed the example).
    ```bash
    poetry run sg_bookkeeper
    ```
    Default admin login: `admin`/`password` (change on first login).

## Usage Guide
*(Updated to reflect current features)*
-   **Dashboard Tab**: View key financial indicators like YTD Revenue, Expenses, Net Profit, Current Cash Balance, Total Outstanding AR/AP, and Total Overdue AR/AP. Use the "Refresh KPIs" button to update.
-   **Banking C.R.U.D Tab**: Manage Bank Accounts (add, edit, toggle active status) and their individual transactions. View transaction lists for selected accounts. Manually add bank transactions (deposits, withdrawals, fees, etc.). Import bank statements using the "Import Statement (CSV)" action, which opens a dialog to configure column mappings.
-   **Bank Reconciliation Tab**: Perform bank reconciliations. Select an account, set the statement end date and ending balance. Load unreconciled statement items (from imports) and system-generated bank transactions into separate tables. Select items from both tables to match them (if amounts net to zero, they are cleared for the session). For statement items not in your books (e.g., bank charges, interest), use the "Add Journal Entry" button to open a pre-filled `JournalEntryDialog`; posting this JE will also auto-create a system `BankTransaction` which can then be matched. Once the "Difference" in the reconciliation summary is zero, click "Save Reconciliation" to finalize the reconciliation (status becomes `Finalized`) and mark transactions as reconciled. View reconciliation history for the selected bank account.
-   **Accounting Tab**: Manage Chart of Accounts (CRUD) and Journal Entries (CRUD, post, reverse, filter by type).
-   **Sales/Purchases Tabs**: Full lifecycle management for Sales and Purchase Invoices, including draft creation, editing, posting (which generates financial and inventory JEs), list views with filtering, and dialogs with advanced product search.
-   **Payments Tab**: Record Customer Receipts and Vendor Payments, allocate them to specific invoices. List and filter payments.
-   **Customers/Vendors/Products & Services Tabs**: Full CRUD and list views with filtering for master data.
-   **Reports Tab**: Generate GST F5 Returns (with detailed Excel export) and standard Financial Statements (Balance Sheet, P&L, Trial Balance, General Ledger) with PDF/Excel export options. GL reports support filtering by up to two dimensions.
-   **Settings Tab**: Configure Company Information, manage Fiscal Years/Periods, Users (CRUD, password changes, role assignment), Roles & Permissions (CRUD, assign permissions to roles), and view Audit Logs (Action Log, Data Change History with filtering).

Upon first run (after DB initialization), an `admin` user is created with the password `password`. You will be prompted to change this password on first login.

## Project Structure
```
sg_bookkeeper/
├── app/                          # Main application source code
│   ├── __init__.py
│   ├── main.py                     # Main application entry point (QApplication, asyncio bridge)
│   ├── core/                       # Core components (ApplicationCore, DBManager, Config, Security)
│   ├── common/                     # Common utilities, enums
│   ├── models/                     # SQLAlchemy ORM models (organized by schema)
│   ├── services/                   # Data access services (repositories)
│   ├── accounting/                 # Business logic managers for accounting module
│   ├── tax/                        # Business logic managers for tax module
│   ├── business_logic/             # Managers for Customers, Vendors, Products, Invoices, Payments, Banking
│   ├── reporting/                  # Logic managers for generating reports & dashboard data
│   ├── ui/                         # PySide6 UI components (organized by module)
│   │   ├── shared/                 # Shared UI components like ProductSearchDialog
│   │   └── ... (other ui modules: accounting, audit, banking, customers, dashboard, etc.)
│   ├── utils/                      # General utility functions, Pydantic DTOs, helpers
│   └── resources_rc.py             # Compiled Qt resources (if generated)
├── data/                         # Default data templates (CoA, report templates, tax codes)
├── docs/                         # Project documentation (like this README, TDS)
├── resources/                    # UI assets (icons, images, .qrc file)
├── scripts/                      # Database initialization scripts (db_init.py, schema.sql, initial_data.sql)
├── tests/                        # Automated tests
│   ├── conftest.py
│   ├── __init__.py
│   ├── unit/                     # Unit tests (organized by module: tax, utils, services)
│   │   ├── __init__.py
│   │   ├── tax/
│   │   ├── services/
│   │   └── utils/
│   ├── integration/              # Integration tests (planned)
│   │   └── __init__.py
│   └── ui/                       # UI tests (planned)
│       └── __init__.py
├── .gitignore
├── pyproject.toml                # Poetry configuration
├── poetry.lock
├── README.md                     # This file
└── LICENSE
```

## Database Schema
The PostgreSQL database (schema version **1.0.5**) includes tables for core system functions, detailed accounting, business operations, and comprehensive audit trails. Key recent additions and updates include:
-   `business.bank_reconciliations` table with a `status` column (`Draft`, `Finalized`).
-   Related fields `last_reconciled_balance` in `business.bank_accounts` and `reconciled_bank_reconciliation_id` in `business.bank_transactions`.
-   A trigger `update_bank_account_balance_trigger_func` automatically maintains `bank_accounts.current_balance`.
Refer to `scripts/schema.sql` for full details.

## Testing
Automated tests are being progressively implemented using the Pytest framework.
-   **Unit Tests**: Located in `tests/unit/`, these tests verify individual components in isolation, typically by mocking dependencies. Current unit tests cover:
    *   **Tax Logic**: `TaxCalculator` (`tests/unit/tax/test_tax_calculator.py`).
    *   **Utilities**: Pydantic DTO validators for `JournalEntryData` and `JournalEntryLineData` (`tests/unit/utils/test_pydantic_models_journal_entry.py`), `SequenceGenerator` (`tests/unit/utils/test_sequence_generator.py`).
    *   **Services**:
        *   `AccountTypeService`, `CurrencyService`, `ExchangeRateService`, `FiscalPeriodService`, `FiscalYearService`, `DimensionService` (in `tests/unit/services/`).
        *   `ConfigurationService`, `CompanySettingsService`, `SequenceService` (in `tests/unit/services/`).
        *   `BankReconciliationService` (`tests/unit/services/test_bank_reconciliation_service.py`).
-   **Running Tests**: Refer to `project_test_guide.md` (if available) or standard Pytest execution (`poetry run pytest`). Code coverage reports can be generated using `pytest-cov`.

## Contributing
Contributions are welcome! Please follow standard open-source contribution practices:
1.  Fork the repository.
2.  Create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name`).
3.  Make your changes, ensuring to add relevant tests where applicable.
4.  Run linters, formatters, and tests to ensure code quality.
5.  Commit your changes with descriptive messages following conventional commit guidelines if possible.
6.  Push to your branch (`git push origin feature/your-feature-name`).
7.  Submit a Pull Request against the `main` (or `develop`) branch of the original repository.

Please adhere to standard coding practices and ensure your contributions align with the project's goals and architectural patterns.

## Roadmap

### Recently Completed (Reflecting Schema v1.0.5 and Codebase)
-   **Banking Module Enhancements**:
    *   Full Bank Reconciliation UI & Core Logic (including `Draft` and `Finalized` status for reconciliations).
    *   CSV Bank Statement Import functionality.
    *   Automatic `BankTransaction` creation from JEs affecting bank GLs.
    *   Database schema updates for reconciliation (v1.0.5) and automatic bank balance updates.
-   **Dashboard KPIs (Initial)**: Display of YTD P&L, Cash, AR/AP, and Overdue AR/AP balances.
-   **Automated Testing (Phase 1 Progress)**: Unit tests established for `TaxCalculator`, key Pydantic DTOs, `SequenceGenerator`, and a growing number of core/accounting/business services including `BankReconciliationService`.

### Current Focus / Next Steps
-   **Automated Testing (Phase 1 Continued - CRITICAL)**:
    *   Expand unit test coverage to more services (especially remaining business services like `SalesInvoiceService`, `PaymentService`) and all managers.
    *   Begin setup for integration tests with a dedicated test database, focusing on core workflows (e.g., invoice posting, payment allocation, bank reconciliation save).
-   **Refine Bank Reconciliation**:
    *   Implement logic and UI for handling complex matches (one-to-many, many-to-one).
    *   Improve UI for displaying already matched items and viewing details of historical reconciliations (currently shows list, detail tables for transactions).
    *   Persist partially matched/selected state within a reconciliation session before final save.
-   **Enhance Dashboard KPIs**:
    *   Add more metrics (e.g., AR/AP Aging details, financial ratios).
    *   Investigate options for simple graphical representations.
    *   Allow user customization or period selection for dashboard KPIs.
-   **Complete Purchase Invoice Posting Logic**: While draft management is implemented, ensure posting logic (Financial JE, Inventory JE) is fully robust and mirrors Sales Invoice capabilities. *(Note: The codebase suggests full PI lifecycle is implemented; this point might be outdated or refer to further refinements.)*

### Long-term
-   Advanced reporting and analytics (customizable reports, more visual dashboards).
-   Inventory Control enhancements (e.g., stocktakes, multiple locations, FIFO/LIFO).
-   Multi-company support.
-   Cloud synchronization options.
-   Enhanced Tax Compliance features (e.g., more detailed Income Tax aids, IAF generation).
-   Full UI test suite.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

---

Now, I will proceed to create the `Project Architecture Document.md`. This will be a detailed document based on my review of the provided codebase.

```markdown
# Project Architecture Document: SG Bookkeeper

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
```

---
https://drive.google.com/file/d/1-vPle_bsfW5q1aXJ4JI9VB5cOYY3f7oU/view?usp=sharing, https://drive.google.com/file/d/14hkYD6mD9rl8PpF-MsJD9nZAy-1sAr0T/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%2216tABsm1Plf_0fhtruoJyyxobBli3e8-7%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/19T9JbSrHCuXhHpzFMUh4Ti_0sDPDycSW/view?usp=sharing, https://drive.google.com/file/d/1D7GYodcMgZv3ROPPRJTYX0g9Rrsq8wJD/view?usp=sharing, https://drive.google.com/file/d/1EGOoM0TGqPgNBJzwxKdVO2u331Myhd4b/view?usp=sharing, https://drive.google.com/file/d/1Ivh39pjoqQ9z4_oj7w7hWc0zOje2-Xjb/view?usp=sharing, https://drive.google.com/file/d/1LzMu08SqY6E5ZuvISa4BsEHxatVPE9g_/view?usp=sharing, https://drive.google.com/file/d/1QyS0xlh6owfMif6KMlyXmE2Zx2hmcdza/view?usp=sharing, https://drive.google.com/file/d/1Y9orpJ67I0XwezEBeUhyJs03DdjkAMhH/view?usp=sharing, https://drive.google.com/file/d/1ZZODHjv2AX2Pn1cRh_0CJDTSzXRGjAt_/view?usp=sharing, https://drive.google.com/file/d/1bSRRtsWeJI9djXTDZTZTjZxnsWS3cvsV/view?usp=sharing, https://drive.google.com/file/d/1cp5LuyXlsbaa_wFSiIMxRlBFSro8qhXq/view?usp=sharing, https://drive.google.com/file/d/1ghGjh0MtEZSDVftjVx583ocaaCDK2j9X/view?usp=sharing, https://drive.google.com/file/d/1mbj5C_Pqa-lbGFf4obvSnpdGm-ALui7y/view?usp=sharing, https://drive.google.com/file/d/1uKfTNXg8Oaes7aGaoaPB6klSZzywizh9/view?usp=sharing, https://drive.google.com/file/d/1vTPAoLcEetjBj17-5nTa_Z6RS7ND5Wmz/view?usp=sharing, https://drive.google.com/file/d/1xbA8X7irZHUayYcfOWWfi4oWm18hFDo2/view?usp=sharing
