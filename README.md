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

---
https://drive.google.com/file/d/1-vPle_bsfW5q1aXJ4JI9VB5cOYY3f7oU/view?usp=sharing, https://drive.google.com/file/d/14hkYD6mD9rl8PpF-MsJD9nZAy-1sAr0T/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%2216tABsm1Plf_0fhtruoJyyxobBli3e8-7%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/19T9JbSrHCuXhHpzFMUh4Ti_0sDPDycSW/view?usp=sharing, https://drive.google.com/file/d/1D7GYodcMgZv3ROPPRJTYX0g9Rrsq8wJD/view?usp=sharing, https://drive.google.com/file/d/1EGOoM0TGqPgNBJzwxKdVO2u331Myhd4b/view?usp=sharing, https://drive.google.com/file/d/1Ivh39pjoqQ9z4_oj7w7hWc0zOje2-Xjb/view?usp=sharing, https://drive.google.com/file/d/1LzMu08SqY6E5ZuvISa4BsEHxatVPE9g_/view?usp=sharing, https://drive.google.com/file/d/1QyS0xlh6owfMif6KMlyXmE2Zx2hmcdza/view?usp=sharing, https://drive.google.com/file/d/1Y9orpJ67I0XwezEBeUhyJs03DdjkAMhH/view?usp=sharing, https://drive.google.com/file/d/1ZZODHjv2AX2Pn1cRh_0CJDTSzXRGjAt_/view?usp=sharing, https://drive.google.com/file/d/1bSRRtsWeJI9djXTDZTZTjZxnsWS3cvsV/view?usp=sharing, https://drive.google.com/file/d/1cp5LuyXlsbaa_wFSiIMxRlBFSro8qhXq/view?usp=sharing, https://drive.google.com/file/d/1ghGjh0MtEZSDVftjVx583ocaaCDK2j9X/view?usp=sharing, https://drive.google.com/file/d/1mbj5C_Pqa-lbGFf4obvSnpdGm-ALui7y/view?usp=sharing, https://drive.google.com/file/d/1uKfTNXg8Oaes7aGaoaPB6klSZzywizh9/view?usp=sharing, https://drive.google.com/file/d/1vTPAoLcEetjBj17-5nTa_Z6RS7ND5Wmz/view?usp=sharing, https://drive.google.com/file/d/1xbA8X7irZHUayYcfOWWfi4oWm18hFDo2/view?usp=sharing

