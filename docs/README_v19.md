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

The application features a double-entry accounting core, GST management (including 9% rate calculations), interactive financial reporting, modules for essential business operations (Customer, Vendor, Product/Service Management, Sales & Purchase Invoicing, Payments), Bank Account management with transaction entry, CSV bank statement import, a full Bank Reconciliation module (including draft persistence, provisional matching/unmatching, and history viewing), an enhanced Dashboard with Key Performance Indicators (KPIs like AR/AP Aging and Current Ratio), and comprehensive User/Role/Permission administration including Audit Logs. Its goal is to provide an intuitive, powerful, and compliant solution that empowers business owners and accountants.

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
-   **Journal Entry System** (Implemented - UI for General Journal with Journal Type filter; transaction-specific JEs auto-generated on posting of source documents and from Bank Reconciliation; posting a JE affecting a bank-linked GL account now auto-creates a system `BankTransaction`.)
-   **Multi-Currency Support** (Foundational - Models, CurrencyManager exist. UI integration in transactions uses it.)
-   **Fiscal Year and Period Management** (Implemented - UI in Settings for FY creation and period auto-generation.)
-   **Budgeting and Variance Analysis** (Foundational - Models exist. UI/Logic planned.)

### Singapore Tax Compliance
-   **GST Tracking and Calculation** (Backend Implemented - `TaxCode` setup, `TaxCalculator` for line items.)
-   **GST F5 Return Data Preparation & Finalization** (Implemented - Backend for data prep & finalization with JE settlement. UI in Reports tab. Enhanced Excel export with transaction details per box.)
-   **Income Tax Estimation Aids** (Planned - Stubs exist.)
-   **Withholding Tax Management** (Foundational - Stubs exist.)

### Business Operations
-   **Customer Management** (Implemented - Full CRUD and listing UI.)
-   **Vendor Management** (Implemented - Full CRUD and listing UI.)
-   **Product and Service Management** (Implemented - Full CRUD and listing UI for Inventory, Non-Inventory, Service types.)
-   **Sales Invoicing and Accounts Receivable** (Implemented - Full lifecycle: Draft CRUD, List View, Posting with financial JE & inventory (WAC) JE creation, "Save & Approve" in dialog, advanced product search.)
-   **Purchase Invoicing and Accounts Payable** (Implemented - Full lifecycle: Draft CRUD, List View, Posting with financial JE & inventory (WAC based on purchase cost) JE creation, Dialog with advanced product search.)
-   **Payment Processing and Allocation** (Implemented - UI for Customer Receipts & Vendor Payments, allocation to invoices, JE posting. List view with filters.)
-   **Inventory Control (Weighted Average Cost)** (Implemented - `InventoryMovement` records created on posting Sales/Purchase invoices for 'Inventory' type products; COGS JEs for sales.)

### Banking
-   **Bank Account Management** (Implemented - Full CRUD and listing UI, linkage to GL.)
-   **Manual Bank Transaction Entry** (Implemented - UI for manual entry, listed per account.)
-   **CSV Bank Statement Import** (Implemented - UI dialog (`CSVImportConfigDialog`) for configuring column mappings and importing transactions.)
-   **Bank Reconciliation Module** (Implemented - Comprehensive UI (`BankReconciliationWidget`) for:
    *   Loading/refreshing unreconciled statement items and system transactions.
    *   Persistent provisional matching of items to a "Draft" reconciliation.
    *   Unmatching provisionally matched items within the current draft session.
    *   Creating adjustment Journal Entries for statement-only items (e.g., bank charges, interest).
    *   Finalizing and saving the reconciliation (status changes to "Finalized").
    *   Viewing paginated history of finalized reconciliations and their cleared transaction details.
    *   Automatic creation of system `BankTransaction` records from relevant Journal Entries.
)

### Reporting & Analytics
-   **Standard Financial Statements**: Balance Sheet, P&L, Trial Balance, General Ledger (Implemented - UI in Reports tab, PDF/Excel export, enhanced GL with dimension filtering.)
-   **Dashboard KPIs** (Implemented - Displays YTD Revenue, Expenses, Net Profit; Current Cash Balance, Total Outstanding AR/AP, Total Overdue AR/AP, AR/AP Aging Summaries (Current, 1-30, 31-60, 61-90, 91+ days), and Current Ratio.)
-   **Cash Flow Statement** (Planned)
-   **GST Reports** (Implemented - See GST F5.)
-   **Customizable Reporting Engine** (Foundational)

### System & Security
-   **User Authentication & RBAC** (Implemented - UI for Users, Roles, Permissions.)
-   **Comprehensive Audit Trails** (Implemented - DB triggers, UI for viewing Action Log and Data Change History in Settings.)
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

This guide is for developers setting up the application from source.

### Prerequisites
-   Python 3.9 or higher
-   PostgreSQL Server 14 or higher
-   Poetry (Python packaging and dependency management tool)
-   Git

### Developer Installation Steps
1.  **Clone Repository**: `git clone https://github.com/yourusername/sg_bookkeeper.git && cd sg_bookkeeper` (Replace `yourusername` with the actual path if forked).
2.  **Install Dependencies**: `poetry install --with dev` (The `--with dev` flag includes development dependencies like `pytest`).
3.  **Prepare PostgreSQL**:
    *   Ensure your PostgreSQL server is running.
    *   Create a dedicated database user (e.g., `sgbookkeeper_user`) and a database (e.g., `sg_bookkeeper`).
    *   Example (using `psql` as a PostgreSQL superuser like `postgres`):
        ```sql
        CREATE USER sgbookkeeper_user WITH PASSWORD 'YourSecurePassword123!';
        CREATE DATABASE sg_bookkeeper OWNER sgbookkeeper_user;
        ```
    *   The user specified in `config.ini` will need appropriate permissions on this database (grants are included in `scripts/initial_data.sql`).
4.  **Configure `config.ini`**:
    *   The application expects `config.ini` in a platform-specific user configuration directory:
        *   Linux: `~/.config/SGBookkeeper/config.ini`
        *   macOS: `~/Library/Application Support/SGBookkeeper/config.ini`
        *   Windows: `%APPDATA%\SGBookkeeper\config.ini` (e.g., `C:\Users\<YourUser>\AppData\Roaming\SGBookkeeper\config.ini`)
    *   Create the `SGBookkeeper` directory if it doesn't exist.
    *   Copy `config.example.ini` (if provided in the repository) to this location as `config.ini`, or create `config.ini` with the following structure, adjusting values as necessary:
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
5.  **Initialize Database**:
    *   This step requires PostgreSQL administrative privileges for the user running the script (e.g., `postgres`) to create extensions or if the database itself needs to be created by the script.
    *   Run the database initialization script using Poetry. This script uses `scripts/schema.sql` (which defines schema version 1.0.5) and `scripts/initial_data.sql`.
    ```bash
    poetry run sg_bookkeeper_db_init --user YOUR_POSTGRES_ADMIN_USER --password YOUR_POSTGRES_ADMIN_PASSWORD --dbname sg_bookkeeper --dbhost localhost --dbport 5432
    ```
    *   Replace placeholders like `YOUR_POSTGRES_ADMIN_USER` and `YOUR_POSTGRES_ADMIN_PASSWORD` with your PostgreSQL admin credentials. The `--dbhost` and `--dbport` arguments can be omitted if PostgreSQL is running on `localhost:5432`.
    *   Add the `--drop-existing` flag *with caution* if you want to delete and recreate the `sg_bookkeeper` database for a clean setup.
6.  **Compile Qt Resources** (Recommended for consistent icon loading):
    ```bash
    poetry run pyside6-rcc resources/resources.qrc -o app/resources_rc.py
    ```
7.  **Run Application**:
    Ensure your `config.ini` points to the application database user (e.g., `sgbookkeeper_user`).
    ```bash
    poetry run sg_bookkeeper
    ```
    Default admin login: `admin`/`password`. You should be prompted to change this password on first login.

## Usage Guide
*(Updated to reflect Bank Reconciliation draft persistence, provisional matching/unmatching, and new Dashboard KPIs)*

-   **Dashboard Tab**: View key financial indicators including YTD Revenue, Expenses, Net Profit; Current Cash Balance; Total Outstanding & Overdue AR/AP; AR & AP Aging summaries (Current, 1-30, 31-60, 61-90, 91+ days); and Current Ratio. Use the "Refresh KPIs" button to update the displayed data.
-   **Banking C.R.U.D Tab**: Manage Bank Accounts (add, edit, toggle active status). View transaction lists for selected accounts. Manually add bank transactions (deposits, withdrawals, fees). Import bank statements using the "Import Statement (CSV)" action, which opens a dialog to configure column mappings specific to your CSV file format.
-   **Bank Reconciliation Tab**: Perform bank reconciliations.
    1.  Select a Bank Account.
    2.  Enter the Statement End Date and Statement Ending Balance from your bank statement.
    3.  Click "Load / Refresh Transactions". A "Draft" reconciliation is automatically created or loaded if one exists for the selected account and date.
    4.  The UI will display unreconciled statement items (from imports/manual entry) and unreconciled system-generated bank transactions in separate tables. Transactions already provisionally matched to the current draft will appear in "Provisionally Matched (This Session)" tables.
    5.  Select items from the "Unreconciled" tables and click "Match Selected". If amounts match, these items are provisionally reconciled against the current draft and moved to the "Provisionally Matched" tables (this is persisted in the database).
    6.  To undo a provisional match, select items from the "Provisionally Matched" tables and click "Unmatch Selected Items".
    7.  For statement items not yet in your books (e.g., bank charges, interest), use the "Add Journal Entry" button. This opens a pre-filled `JournalEntryDialog`. Posting this JE will also auto-create a corresponding system `BankTransaction`, which will then appear in the unreconciled list for matching.
    8.  The "Reconciliation Summary" section dynamically updates to show the difference.
    9.  Once the "Difference" is zero (or within an acceptable tolerance), click "Save Final Reconciliation". This changes the draft's status to "Finalized", updates the bank account's last reconciled date/balance, and permanently marks the reconciled transactions.
    10. View a paginated history of finalized reconciliations and their cleared transaction details in the "Reconciliation History" section.
-   **Accounting Tab**: Manage Chart of Accounts (CRUD) and Journal Entries (CRUD, post, reverse, filter by type).
-   **Sales/Purchases Tabs**: Full lifecycle management for Sales and Purchase Invoices, including draft creation, editing, posting (which generates financial and inventory JEs), list views with filtering, and dialogs with advanced product search.
-   **Payments Tab**: Record Customer Receipts and Vendor Payments, allocate them to specific invoices. List and filter payments.
-   **Customers/Vendors/Products & Services Tabs**: Full CRUD and list views with filtering for master data.
-   **Reports Tab**: Generate GST F5 Returns (with detailed Excel export) and standard Financial Statements (Balance Sheet, P&L, Trial Balance, General Ledger) with PDF/Excel export options. GL reports support filtering by up to two dimensions.
-   **Settings Tab**: Configure Company Information, manage Fiscal Years/Periods, Users (CRUD, password changes, role assignment), Roles & Permissions (CRUD, assign permissions to roles), and view Audit Logs (Action Log, Data Change History with filtering).

## Project Structure
```
sg_bookkeeper/
├── app/                          # Main application source code
│   ├── __init__.py
│   ├── main.py                     # Main application entry point
│   ├── core/                       # Core components (ApplicationCore, DBManager, Config, Security)
│   ├── common/                     # Common enums, constants, etc.
│   ├── models/                     # SQLAlchemy ORM models (organized by schema: core, accounting, business, audit)
│   │   ├── accounting/
│   │   ├── audit/
│   │   ├── business/
│   │   └── core/
│   ├── services/                   # Data access layer services (repositories)
│   ├── accounting/                 # Business logic managers for accounting module
│   ├── business_logic/             # Managers for Customers, Vendors, Products, Invoices, Payments, Banking
│   ├── reporting/                  # Logic managers for generating reports & dashboard data
│   ├── tax/                        # Business logic managers for tax module
│   ├── ui/                         # PySide6 UI components (organized by module)
│   │   ├── shared/                 # Shared UI components (e.g., ProductSearchDialog)
│   │   └── ... (other ui modules: accounting, audit, banking, customers, dashboard, etc.)
│   ├── utils/                      # General utility functions, Pydantic DTOs, helpers
│   └── resources_rc.py             # Compiled Qt resources (generated if pyside6-rcc is run)
├── data/                         # Default data templates (CoA, report templates, tax codes)
├── docs/                         # Project documentation (like this README, TDS, Architecture)
├── resources/                    # UI assets (icons, images, .qrc file)
├── scripts/                      # Database initialization scripts (db_init.py, schema.sql, initial_data.sql)
├── tests/                        # Automated tests
│   ├── conftest.py
│   ├── __init__.py
│   ├── unit/                     # Unit tests (organized by module)
│   │   ├── __init__.py
│   │   ├── accounting/           # Unit tests for accounting logic (currently empty)
│   │   ├── business_logic/       # Unit tests for business operations logic (currently empty)
│   │   ├── core/                 # Unit tests for core components (currently empty)
│   │   ├── reporting/            # Tests for reporting logic (e.g., DashboardManager, FinancialStatementGenerator)
│   │   ├── services/             # Tests for service layer components
│   │   ├── tax/                  # Tests for tax logic (e.g., TaxCalculator, GSTManager)
│   │   └── utils/                # Tests for utilities (e.g., Pydantic models, SequenceGenerator)
│   ├── integration/              # Integration tests (planned, currently basic structure)
│   │   └── __init__.py
│   └── ui/                       # UI tests (planned, currently basic structure)
│       └── __init__.py
├── .gitignore
├── pyproject.toml                # Poetry configuration
├── poetry.lock
├── README.md                     # This file
└── LICENSE
```

## Database Schema
The PostgreSQL database schema is at version **1.0.5**. It includes tables for core system functions, detailed accounting, business operations, and comprehensive audit trails. Key recent additions include the `business.bank_reconciliations` table with a `status` column ('Draft', 'Finalized') and related fields in `bank_accounts` and `bank_transactions` to support the full bank reconciliation workflow, including draft persistence. A trigger `update_bank_account_balance_trigger_func` ensures `bank_accounts.current_balance` is automatically updated based on its transactions. Refer to `scripts/schema.sql` for full details.

## Testing
Automated tests are implemented using Pytest to ensure code quality and prevent regressions.
-   **Unit Tests**: Located in `tests/unit/`, these verify individual components by mocking dependencies. Key areas covered include:
    *   **Reporting Logic**: `DashboardManager` (KPI calculations), `FinancialStatementGenerator`.
    *   **Service Layer**: A broad range of services including `AccountService` (esp. methods for dashboard KPIs), `AuditLogService`, `BankAccountService`, `BankReconciliationService` (drafts, matching, finalization), `CompanySettingsService`, `ConfigurationService`, `CurrencyService`, `CustomerService` (AR aging), `DimensionService`, `ExchangeRateService`, `FiscalPeriodService`, `FiscalYearService`, `GSTReturnService`, `InventoryMovementService`, `JournalService`, `PaymentService`, `PurchaseInvoiceService`, `SalesInvoiceService`, `SequenceService`, `TaxCodeService`, `VendorService` (AP aging).
    *   **Tax Logic**: `TaxCalculator`, `GSTManager`.
    *   **Utilities**: Pydantic DTO validators (e.g., for `JournalEntryData`), `SequenceGenerator`.
-   **Running Tests**:
    *   To run all tests: `poetry run pytest`
    *   To generate a coverage report: `poetry run pytest --cov=app` (requires `pytest-cov` plugin)

## Contributing
Contributions are welcome! Please follow standard open-source contribution practices:
1.  Fork the repository.
2.  Create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name`).
3.  Make your changes, ensuring to add relevant tests where applicable.
4.  Run linters (e.g., `flake8`), formatters (e.g., `black`), and type checkers (e.g., `mypy`), and ensure all tests pass.
5.  Commit your changes with descriptive messages (Conventional Commits style preferred if possible).
6.  Push to your branch (`git push origin feature/your-feature-name`).
7.  Submit a Pull Request against the `main` (or `develop`) branch of the original repository.

Please adhere to coding standards and ensure your contributions align with the project's goals and architectural patterns.

## Roadmap

### Recently Completed
-   **Bank Reconciliation Enhancements (Schema v1.0.5)**:
    *   Full workflow including Draft persistence for reconciliations.
    *   Persistent Provisional Matching of statement and system transactions to the draft.
    *   "Unmatch" functionality for provisionally matched items within a draft session.
    *   Finalization of draft reconciliations.
    *   UI for viewing paginated history of finalized reconciliations and their details.
    *   CSV Bank Statement Import and automatic `BankTransaction` creation from relevant JEs.
-   **Dashboard KPI Enhancements**:
    *   Added AR/AP Aging Summaries (Current, 1-30, 31-60, 61-90, 91+ days).
    *   Added Current Ratio calculation and display.
    *   Backend services and manager logic for these new KPIs.
-   **Circular Import Resolution**: Systematically fixed import cycles across managers, services, and `ApplicationCore`.
-   **Automated Testing (Phase 1 - Dashboard Logic & Core Bank Rec)**: Unit tests for `DashboardManager` methods, dependent service logic for new KPIs, and key `BankReconciliationService` methods. Expanded unit test coverage across many other services.

### Current Focus / Next Steps
-   **Automated Testing (Continued - CRITICAL)**:
    *   Expand unit test coverage to achieve higher percentages for all managers and remaining service methods.
    *   Begin setup and implementation of integration tests for core workflows (e.g., invoice posting and payment allocation cycle, full bank reconciliation save-and-finalize cycle).
-   **Refine Bank Reconciliation**:
    *   Implement UI and logic for handling complex matches (e.g., one-to-many, many-to-one statement lines to system transactions).
    *   UI improvements for visually linking matched items within the "Provisionally Matched" tables or a dedicated view.
    *   More robust error handling and user feedback during CSV import (e.g., detailed row-level error reporting for parsing issues, duplicate detection).
-   **Enhance Dashboard KPIs (Phase 2)**:
    *   Add more financial ratios (e.g., Quick Ratio, Debt-to-Equity).
    *   Investigate and implement simple graphical representations for key KPIs (e.g., bar charts for aging summaries).
    *   Allow user customization or period selection for dashboard information.

### Long-term
-   Advanced reporting and analytics (e.g., customizable report builder, trend analysis).
-   Inventory Control enhancements (e.g., stocktakes, multiple locations, FIFO/LIFO costing methods).
-   Multi-company support within a single installation.
-   Cloud synchronization options (optional data backup/sync to a user-provided cloud storage).
-   Enhanced Tax Compliance features (e.g., more detailed Income Tax aids, preparation of IRAS Audit File (IAF)).
-   Full UI test suite using a suitable framework (e.g., `pytest-qt`).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

