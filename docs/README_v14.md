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
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

[Key Features](#key-features) • [Technology Stack](#technology-stack) • [Installation](#installation) • [Usage](#usage-guide) • [Project Structure](#project-structure) • [Contributing](#contributing) • [Roadmap](#roadmap) • [License](#license)

</div>

## Overview

SG Bookkeeper is a comprehensive, cross-platform desktop application designed to meet the accounting and bookkeeping needs of small to medium-sized businesses (SMBs) in Singapore. Built with Python and leveraging the power of PySide6 for a modern user interface and PostgreSQL for robust data management, it offers professional-grade financial tools tailored to Singapore's regulatory environment.

The application features a double-entry accounting core, GST management, interactive financial reporting, modules for essential business operations (Customer, Vendor, Product/Service Management, Sales & Purchase Invoicing, Payments), Bank Account management with transaction entry and **CSV statement import**, a **full Bank Reconciliation module**, and comprehensive User/Role/Permission administration including Audit Logs. Its goal is to provide an intuitive, powerful, and compliant solution that empowers business owners and accountants.

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
-   **General Ledger with detailed transaction history** (Implemented - Report generation, on-screen view, export, with dimension filtering options)
-   **Journal Entry System** (Implemented - UI for General Journal with Journal Type filter; transaction-specific JEs generated on posting of source documents; JEs also auto-created from Bank Reconciliation for statement-only items)
-   **Multi-Currency Support** (Foundational - Models, CurrencyManager exist. UI integration in transactions uses it, e.g., payments, invoices.)
-   **Fiscal Year and Period Management** (Implemented - UI in Settings for FY creation and period auto-generation.)
-   **Budgeting and Variance Analysis** (Foundational - Models exist. UI/Logic planned.)

### Singapore Tax Compliance
-   **GST Tracking and Calculation** (Backend Implemented - `TaxCode` setup, `TaxCalculator` for line items. Sales/Purchase Invoice Dialogs use it.)
-   **GST F5 Return Data Preparation & Finalization** (Implemented - Backend for data prep & finalization with JE settlement. UI in Reports tab. Enhanced Excel export with transaction details per box.)
-   **Income Tax Estimation Aids** (Planned)
-   **Withholding Tax Management** (Foundational)

### Business Operations
-   **Customer Management** (Implemented - Full CRUD and listing UI.)
-   **Vendor Management** (Implemented - Full CRUD and listing UI.)
-   **Product and Service Management** (Implemented - Full CRUD and listing UI.)
-   **Sales Invoicing and Accounts Receivable** (Implemented - Draft CRUD, Posting with financial JE & inventory (WAC) JE creation, List View UI, Dialog with "Save & Approve" and advanced product search.)
-   **Purchase Invoicing and Accounts Payable** (Implemented - Draft CRUD, Posting with financial JE & inventory (WAC based on purchase cost) JE creation, List View UI, Dialog with advanced product search.)
-   **Payment Processing and Allocation** (Implemented - UI for recording Customer Receipts & Vendor Payments, allocation to invoices, JE posting. List view with filters.)
-   **Inventory Control (Weighted Average Cost)** (Implemented - `InventoryMovement` records created on posting Sales/Purchase invoices for 'Inventory' type products; COGS JEs for sales.)

### Banking
-   **Bank Account Management** (Implemented - Full CRUD and listing UI for bank accounts, linkage to GL.)
-   **Manual Bank Transaction Entry** (Implemented - UI for manual entry of deposits, withdrawals, fees, interest directly against bank accounts. Transactions are listed per account.)
-   **CSV Bank Statement Import** (Implemented - UI dialog for configuring and importing bank transactions from CSV files.)
-   **Bank Reconciliation Tools** (Implemented - UI for matching bank statement items with system transactions, identifying discrepancies, creating adjustment JEs, and saving reconciliation state.)

### Reporting & Analytics
-   **Standard Financial Statements**: Balance Sheet, Profit & Loss, Trial Balance, General Ledger (Implemented - UI in Reports tab with options for comparative/zero-balance, on-screen view, PDF/Excel export with enhanced formatting for all four statements. GL includes dimension filtering options.)
-   **Cash Flow Statement** (Planned)
-   **GST Reports** (Implemented - See GST F5 above, including detailed Excel export.)
-   **Customizable Reporting Engine** (Foundational - `ReportEngine` has enhanced exports; further customization planned)
-   **Dashboard with Key Performance Indicators (KPIs)** (Planned - UI is a stub.)

### System & Security
-   **User Authentication** (Implemented - Login, password hashing)
-   **Role-Based Access Control (RBAC)** (Implemented - UI for managing Users, Roles, and assigning Permissions to Roles.)
-   **Granular Permissions System** (Implemented - Backend checks via `SecurityManager.has_permission()`, permissions seeded.)
-   **Comprehensive Audit Trails** (Implemented - Via DB triggers and `app.current_user_id`. UI for viewing Action Log and Data Change History now available in Settings.)
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
    This command creates a virtual environment (typically `.venv` in the project root if one doesn't exist) and installs all dependencies specified in `pyproject.toml`.

3.  **Prepare PostgreSQL Database User and Database:**
    *   Connect to your PostgreSQL instance as a superuser (e.g., `postgres`):
        ```bash
        psql -U postgres
        ```
    *   Create a dedicated database user for the application (replace `YourSecurePassword123!` securely):
        ```sql
        CREATE USER sgbookkeeper_user WITH PASSWORD 'YourSecurePassword123!';
        -- The database itself (sg_bookkeeper) will be created by the db_init.py script if it doesn't exist,
        -- provided the connecting user (e.g., postgres) has CREATEDB rights.
        -- Alternatively, create it manually:
        -- CREATE DATABASE sg_bookkeeper OWNER sgbookkeeper_user;
        \q
        ```

4.  **Configure Database Connection (`config.ini`):**
    *   The application expects `config.ini` in a platform-specific user configuration directory.
        *   Linux: `~/.config/SGBookkeeper/config.ini`
        *   macOS: `~/Library/Application Support/SGBookkeeper/config.ini`
        *   Windows: `C:\Users\<YourUser>\AppData\Roaming\SGBookkeeper\config.ini`
    *   Create this directory if it doesn't exist.
    *   Copy the following example content into `config.ini` in that location, adjusting values as necessary:
        ```ini
        [Database]
        username = sgbookkeeper_user ; User for application runtime
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
        last_opened_company_id = 1 ; Default company settings ID from initial_data.sql
        ```
    *   Ensure `username`, `password`, `host`, `port`, and `database` match your PostgreSQL setup.

5.  **Initialize the Database Schema and Seed Initial Data:**
    *   This step requires PostgreSQL administrative privileges (e.g., user `postgres`) to create the database (if not existing) and extensions.
    *   Run the database initialization script using Poetry. Replace `YOUR_POSTGRES_ADMIN_PASSWORD` with the password for your PostgreSQL admin user.
    ```bash
    poetry run sg_bookkeeper_db_init --user postgres --password YOUR_POSTGRES_ADMIN_PASSWORD --dbname sg_bookkeeper --drop-existing
    ```
    *   **`--drop-existing`**: Use this flag with caution. It will delete and recreate the `sg_bookkeeper` database, ensuring a clean setup. Omit it if you want to preserve an existing database (the script might then fail if tables conflict).
    *   This script executes `scripts/schema.sql` (DDL) and `scripts/initial_data.sql` (DML for seeding).

6.  **Grant Privileges to Application User (if `sgbookkeeper_user` didn't create the DB):**
    *   The `scripts/initial_data.sql` file now includes `GRANT` statements that should be executed by the superuser after the schema is created by `db_init.py`. If `db_init.py` is run by `postgres`, these grants should apply correctly to `sgbookkeeper_user`. If you encounter permission issues, manually run the `GRANT` statements found at the end of `scripts/initial_data.sql` while connected as a superuser to the `sg_bookkeeper` database.

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

## Usage Guide

The application provides a range of functional modules accessible via tabs in the main window:

-   **Dashboard Tab**: (Placeholder) Intended for an overview of financial health.
-   **Accounting Tab**:
    -   **Chart of Accounts**: View, add, edit, and (de)activate accounts.
    -   **Journal Entries**: List, filter (including by Journal Type), create, edit drafts, view, post, and reverse general journal entries.
-   **Sales Tab**: Create, view, filter, edit draft, post Sales Invoices (with financial and inventory JEs), and use advanced product search.
-   **Purchases Tab**: Create, view, filter, edit draft, and post Purchase Invoices (with financial and inventory JEs), and use advanced product search.
-   **Payments Tab**: Record Customer Receipts and Vendor Payments, allocate them to invoices. List and filter payments.
-   **Customers Tab**: View, search, filter, add, edit, and toggle active status for customers.
-   **Vendors Tab**: View, search, filter, add, edit, and toggle active status for vendors.
-   **Products & Services Tab**: Manage products and services (Inventory, Non-Inventory, Service types) with list view, filters, add/edit dialog.
-   **Banking C.R.U.D Tab**:
    -   **Bank Accounts**: Manage bank accounts (add, edit, toggle active), view list of accounts.
    -   **Transactions**: For a selected bank account, view its transactions and add manual entries (deposits, withdrawals, fees, etc.). Import bank statements via CSV.
-   **Bank Reconciliation Tab**: Perform bank reconciliations by selecting an account, statement date, and ending balance. Load unreconciled statement items (from CSV imports) and system transactions. Match items, create adjustment JEs for unmatched statement items (like bank charges or interest), and save the reconciliation once the difference is zero.
-   **Reports Tab**:
    -   **GST F5 Preparation**: Prepare, view, save draft, and finalize GST F5 returns. Export detailed breakdown to Excel.
    *   **Financial Statements**: Generate Balance Sheet, Profit & Loss, Trial Balance, or General Ledger. View in structured tables/trees. Export to PDF/Excel with enhanced formatting. GL reports support filtering by up to two dimensions. BS/P&L reports support comparative periods and zero-balance account options.
-   **Settings Tab**:
    -   **Company**: Configure company-wide information.
    -   **Fiscal Years**: Manage Fiscal Years and their periods.
    -   **Users**: Manage user accounts (add, edit, toggle active, change password, assign roles).
    *   **Roles & Permissions**: Manage roles (add, edit, delete) and assign system permissions to roles.
    *   **Audit Logs**: View Action Log (system-wide actions) and Data Change History (field-level modifications) with filtering capabilities.

Upon first run (after DB initialization), an `admin` user is created with the password `password`. You will be prompted to change this password on first login.

## Project Structure

```
sg_bookkeeper/
├── app/
│   ├── __init__.py
│   ├── main.py                     # Main application entry point
│   ├── core/                       # Core components (ApplicationCore, DBManager, Config, Security)
│   ├── common/                     # Common utilities, enums
│   ├── models/                     # SQLAlchemy ORM models (organized by schema)
│   │   ├── accounting/
│   │   ├── audit/
│   │   ├── business/
│   │   └── core/
│   ├── services/                   # Data access services (repositories)
│   ├── accounting/                 # Business logic managers for accounting module
│   ├── tax/                        # Business logic managers for tax module
│   ├── business_logic/             # Managers for Customers, Vendors, Products, Invoices, Payments, Banking
│   ├── reporting/                  # Logic managers for generating reports
│   ├── ui/                         # PySide6 UI components (organized by module)
│   │   ├── accounting/
│   │   ├── audit/
│   │   ├── banking/                # UI for Banking (Accounts, Transactions, Reconciliation, CSV Import)
│   │   ├── customers/
│   │   ├── payments/
│   │   ├── products/
│   │   ├── purchase_invoices/
│   │   ├── reports/
│   │   ├── sales_invoices/
│   │   ├── settings/               
│   │   ├── shared/                 # Shared UI components
│   │   └── ... (other ui modules)
│   ├── utils/                      # General utility functions, Pydantic DTOs, helpers
│   └── resources_rc.py             # Compiled Qt resources
├── data/                           # Default data templates
├── docs/                           # Project documentation
├── resources/                      # UI assets (icons, images, .qrc file)
├── scripts/                        # Database initialization and utility scripts
├── tests/                          # Automated tests (planned)
├── .gitignore
├── pyproject.toml                  # Poetry configuration
├── poetry.lock
├── README.md                       # This file
└── LICENSE
```

## Database Schema
The application uses a PostgreSQL database with a schema organized into four main parts: `core`, `accounting`, `business`, and `audit`. This schema is designed to be comprehensive, supporting a wide range of accounting and business functionalities, including the new `bank_reconciliations` table and related fields for bank transaction management. For the complete schema details, including table structures, views, functions, and triggers, please refer to `scripts/schema.sql`.

## Development
-   **Formatting**: Code is formatted using Black. Run `poetry run black .`
-   **Linting**: Flake8 is used for linting. Run `poetry run flake8 .`
-   **Type Checking**: MyPy can be used. Run `poetry run mypy app scripts`
-   **Testing**: Pytest is set up. Run tests with `poetry run pytest`. (Test coverage needs significant improvement).

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

### Recently Completed (v1.0.4 Features)
-   **Banking Module (Phase 1.5)**:
    *   **Bank Reconciliation UI & Core Logic**: Interface for selecting account, statement date/balance. Loading unreconciled statement items and system transactions. UI calculations for reconciliation summary. Ability to "Match Selected" items (for UI calculation). "Save Reconciliation" functionality to persist reconciled state and update related records.
    *   **CSV Bank Statement Import**: UI dialog (`CSVImportConfigDialog`) for configuring column mappings and importing transactions from CSV files into `bank_transactions` table, flagged as `is_from_statement=True`.
    *   **Journal Entry for Statement Items**: UI button in reconciliation screen to pre-fill `JournalEntryDialog` for unmatched statement items (e.g., bank charges, interest). Posting these JEs now auto-creates corresponding system `BankTransaction` records.
-   Database schema updates for bank reconciliation (`bank_reconciliations` table, new columns in `bank_accounts`, `bank_transactions`).
-   Automatic `bank_accounts.current_balance` updates via database trigger on `bank_transactions` changes.
-   `JournalEntryManager` now auto-creates `BankTransaction` records when a JE line affects a bank-linked GL account.

### Current Focus / Next Steps
-   **Dashboard KPIs**:
    *   Implement `DashboardWidget` to display key financial indicators (e.g., Revenue vs. Expense, Profit Trends, Cash Flow Summary, AR/AP Aging).
-   **Automated Testing (Phase 1 - CRITICAL)**:
    *   Establish a comprehensive test suite: unit tests for services/managers, integration tests for core workflows, and basic UI tests for critical paths.
-   **Refine Bank Reconciliation**:
    *   Handling of complex matches (e.g., one-to-many, many-to-one).
    *   UI improvements for displaying matched items and reconciliation history.
    *   More robust error handling and user feedback during import and reconciliation.

### Long-term
-   Advanced reporting and analytics (customizable reports, more visual dashboards).
-   Inventory Control enhancements (e.g., stocktakes, stock movements beyond invoicing, potentially alternative valuation methods).
-   Multi-company support (major architectural consideration).
-   Cloud synchronization options (optional, for future exploration).
-   Enhanced Tax Compliance features (e.g., more detailed Income Tax aids, potential for IAF generation).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
