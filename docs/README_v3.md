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

SG Bookkeeper is a comprehensive, cross-platform desktop application designed to meet the accounting and bookkeeping needs of small to medium-sized businesses in Singapore. Built with Python and leveraging the power of PySide6 for a modern user interface and PostgreSQL for robust data management, it offers professional-grade financial tools tailored to Singapore's regulatory environment.

The application features a double-entry accounting core, GST management, financial reporting, and modules for essential business operations. Its goal is to provide an intuitive, powerful, and compliant solution that empowers business owners and accountants.

### Why SG Bookkeeper?

-   **Singapore-Centric**: Designed with Singapore Financial Reporting Standards (SFRS), GST regulations (including 9% rate), and IRAS compliance considerations at its core.
-   **Professional Grade**: Implements a full double-entry system, detailed audit trails (via database triggers), and robust data validation using Pydantic DTOs.
-   **User-Friendly Interface**: Aims for an intuitive experience for users who may not be accounting experts, while providing depth for professionals. Core accounting UI is functional.
-   **Open Source & Local First**: Transparent development. Your financial data stays on your local machine or private server, ensuring privacy and control. No subscription fees.
-   **Modern & Performant**: Utilizes asynchronous operations for a responsive UI and efficient database interactions, with a dedicated asyncio event loop.

## Key Features

*(Status: Implemented, Partially Implemented, Foundational (DB/Models ready), Planned)*

### Core Accounting
-   **Comprehensive Double-Entry Bookkeeping** (Implemented)
-   **Customizable Hierarchical Chart of Accounts** (Implemented - UI for CRUD, Singapore-specific templates in `data/`)
-   **General Ledger with detailed transaction history** (Foundational - JEs can be viewed, full GL report planned)
-   **Journal Entry System** (Implemented - UI for General Journal, Sales/Purchases JEs via respective modules are planned)
-   **Multi-Currency Support** (Foundational - `accounting.currencies` & `exchange_rates` tables and models exist, `CurrencyManager` for backend logic. UI integration in transactions pending.)
-   **Fiscal Year and Period Management** (Implemented - UI in Settings for FY creation and period auto-generation; period closing/reopening logic in manager.)
-   **Budgeting and Variance Analysis** (Foundational - `accounting.budgets` & `budget_details` tables and models exist. UI/Logic planned.)

### Singapore Tax Compliance
-   **GST Tracking and Calculation** (Partially Implemented - `TaxCode` setup for SR, ZR, ES, TX at 9%; `TaxCalculator` exists. `GSTManager` can create `GSTReturn` records. Full JE line item tax application in all transaction UIs is ongoing.)
-   **GST F5 Return Data Preparation** (Partially Implemented - `GSTManager` structure exists. Aggregation logic from JEs is a placeholder. Settlement JE creation is implemented.)
-   **Income Tax Estimation Aids** (Planned - `IncomeTaxManager` stub exists.)
-   **Withholding Tax Management** (Foundational - `accounting.withholding_tax_certificates` table/model and `WithholdingTaxManager` stub exist.)

### Business Operations
-   **Customer and Vendor Relationship Management (CRM)** (Foundational - `business.customers` & `business.vendors` tables/models exist. UI is a stub.)
-   **Sales Invoicing and Accounts Receivable** (Foundational - `business.sales_invoices` tables/models exist. UI/Logic planned.)
-   **Purchase Invoicing and Accounts Payable** (Foundational - `business.purchase_invoices` tables/models exist. UI/Logic planned.)
-   **Payment Processing and Allocation** (Foundational - `business.payments` tables/models exist. UI/Logic planned.)
-   **Bank Account Management and Reconciliation Tools** (Foundational - `business.bank_accounts` & `bank_transactions` tables/models exist. UI is a stub.)
-   **Product and Service Management** (Foundational - `business.products` table/model exists. UI/Logic planned.)
-   **Basic Inventory Control** (Foundational - `business.inventory_movements` table/model exists. Logic planned.)

### Reporting & Analytics
-   **Standard Financial Statements**: Balance Sheet, Profit & Loss, Trial Balance (Implemented - `FinancialStatementGenerator` produces data; `ReportEngine` exports basic PDF/Excel.)
-   **Cash Flow Statement** (Planned)
-   **GST Reports** (Partially Implemented - `FinancialStatementGenerator` can produce data for GST F5. Formatted report planned.)
-   **Customizable Reporting Engine** (Planned - Current `ReportEngine` is basic.)
-   **Dashboard with Key Performance Indicators (KPIs)** (Planned - UI is a stub.)

### System & Security
-   **User Authentication with Role-Based Access Control (RBAC)** (Implemented - `SecurityManager`, DB tables for users, roles, permissions are functional. Initial admin user seeded.)
-   **Granular Permissions System** (Foundational - DB tables exist, `SecurityManager.has_permission` implemented. Full UI integration pending.)
-   **Comprehensive Audit Trails** (Implemented - DB triggers populate `audit.audit_log` and `audit.data_change_history` for key tables. Requires `app.current_user_id` session variable to be set by application.)
-   **PostgreSQL Database Backend** (Implemented)
-   **Data Backup and Restore Utilities** (Planned)

## Technology Stack

-   **Programming Language**: Python 3.9+ (up to 3.12)
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
-   Poetry (Python packaging and dependency management tool). Install via `pip install poetry` or preferred method.
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

3.  **Prepare PostgreSQL Database User:**
    *   Connect to your PostgreSQL instance as a superuser (e.g., `postgres`):
        ```bash
        sudo -u postgres psql # Or psql -U postgres on Windows/macOS if postgres user needs password
        ```
    *   Create a dedicated database user for the application (replace `YourSecurePassword123!` securely):
        ```sql
        CREATE USER sgbookkeeper_user WITH PASSWORD 'YourSecurePassword123!';
        \q
        ```
        *Note: The database itself (`sg_bookkeeper`) will be created by the `db_init.py` script if it doesn't exist.*

4.  **Configure Database Connection (`config.ini`):**
    *   The application expects `config.ini` in a platform-specific user configuration directory.
        *   Linux: `~/.config/SGBookkeeper/config.ini`
        *   macOS: `~/Library/Application Support/SGBookkeeper/config.ini`
        *   Windows: `C:\Users\<YourUser>\AppData\Roaming\SGBookkeeper\config.ini`
    *   Create this directory if it doesn't exist.
    *   Copy the following example content into `config.ini` in that location, adjusting values as necessary:
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
        last_opened_company_id = 1 ; Default company settings ID from initial_data.sql
        ```
    *   Ensure `username`, `password`, `host`, `port`, and `database` match your PostgreSQL setup and the user created in step 3.

5.  **Initialize the Database Schema and Seed Initial Data:**
    *   This step requires PostgreSQL administrative privileges to create the database (if not existing) and extensions.
    *   Run the database initialization script using Poetry. Replace `YOUR_POSTGRES_ADMIN_PASSWORD` with the password for your PostgreSQL admin user (e.g., `postgres`).
    ```bash
    poetry run sg_bookkeeper_db_init --user postgres --password YOUR_POSTGRES_ADMIN_PASSWORD --dbname sg_bookkeeper --drop-existing
    ```
    *   **`--drop-existing`**: Use this flag with caution. It will delete and recreate the `sg_bookkeeper` database, ensuring a clean setup. Omit it if you want to preserve an existing database (the script might then fail if tables conflict).
    *   This script executes `scripts/schema.sql` and `scripts/initial_data.sql`.

6.  **Grant Privileges to Application User:**
    *   After the database is initialized by the admin user, connect to the `sg_bookkeeper` database as the PostgreSQL admin user:
        ```bash
        sudo -u postgres psql -d sg_bookkeeper # Or psql -U postgres -d sg_bookkeeper
        ```
    *   Execute the following `GRANT` commands (replace `sgbookkeeper_user` if you used a different application username):
        ```sql
        GRANT USAGE ON SCHEMA core, accounting, business, audit TO sgbookkeeper_user;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA core TO sgbookkeeper_user;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA accounting TO sgbookkeeper_user;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA business TO sgbookkeeper_user;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA audit TO sgbookkeeper_user;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA core TO sgbookkeeper_user;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA accounting TO sgbookkeeper_user;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA business TO sgbookkeeper_user;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA audit TO sgbookkeeper_user;
        GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA core TO sgbookkeeper_user;
        GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA accounting TO sgbookkeeper_user;
        GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA audit TO sgbookkeeper_user;

        -- For future tables created by the admin role (e.g., during migrations)
        ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA core GRANT ALL ON TABLES TO sgbookkeeper_user;
        ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA accounting GRANT ALL ON TABLES TO sgbookkeeper_user;
        ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA business GRANT ALL ON TABLES TO sgbookkeeper_user;
        ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA audit GRANT ALL ON TABLES TO sgbookkeeper_user;
        ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA core GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
        ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA accounting GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
        ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA business GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
        ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA audit GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
        \q
        ```

7.  **Compile Qt Resources (Recommended):**
    For icons and other Qt resources to be bundled correctly:
    ```bash
    poetry run pyside6-rcc resources/resources.qrc -o app/resources_rc.py
    ```
    The application attempts to load compiled resources first, falling back to direct file paths if `app/resources_rc.py` is not found.

8.  **Run the Application:**
    Ensure your `config.ini` points to the application user (`sgbookkeeper_user`).
    ```bash
    poetry run sg_bookkeeper
    ```

## Usage Guide

The application is under active development. Currently, the following areas have functional UI components:

-   **Accounting Tab**:
    -   **Chart of Accounts**: View, add, edit, and (de)activate accounts.
    -   **Journal Entries**: View list of journal entries. Create new general journal entries with multiple lines, tax codes. Edit draft entries. Post entries.
-   **Settings Tab**:
    -   View and edit Company Information.
    -   Manage Fiscal Years: Add new fiscal years and automatically generate their monthly or quarterly periods.

Other modules like Customers, Vendors, Banking, full Reports, and the Dashboard are placeholders for future development.
Upon first run (after DB initialization), an `admin` user is created with the password `password`. You will be prompted to change this password.

## Project Structure

```
sg_bookkeeper/
├── app/                    # Application source code
│   ├── __init__.py
│   ├── main.py             # Main application entry point (QApplication, asyncio bridge)
│   ├── core/               # Core components (ApplicationCore, DBManager, Config, Security)
│   ├── common/             # Common utilities, enums
│   ├── models/             # SQLAlchemy ORM models (organized by schema: core, accounting, etc.)
│   ├── services/           # Data access services (repositories)
│   ├── accounting/         # Business logic managers for accounting module
│   ├── tax/                # Business logic managers for tax module
│   ├── reporting/          # Logic managers for generating reports
│   ├── ui/                 # PySide6 UI components (organized by module)
│   └── utils/              # General utility functions, Pydantic DTOs, helpers
├── data/                   # Default data templates (e.g., CoA templates, sample tax codes)
├── docs/                   # Project documentation (like this README, TDS)
├── resources/              # UI assets
│   ├── icons/              # SVG icons
│   ├── images/             # Splash screen, etc.
│   └── resources.qrc       # Qt resource collection file
├── scripts/                # Database initialization and utility scripts
│   ├── db_init.py          # Python script to initialize DB
│   ├── schema.sql          # Full DDL for database schema
│   └── initial_data.sql    # SQL for seeding initial/default data
├── tests/                  # Automated tests (unit, integration, UI - planned)
├── .gitignore
├── pyproject.toml          # Poetry configuration for dependencies and project metadata
├── poetry.lock
├── README.md               # This file
└── LICENSE
```

## Database Schema
The application uses a PostgreSQL database with a schema organized into four main parts: `core`, `accounting`, `business`, and `audit`. This schema is designed to be comprehensive, supporting a wide range of accounting and business functionalities. For the complete schema details, including table structures, views, functions, and triggers, please refer to `scripts/schema.sql`.

## Development
-   **Formatting**: Code is formatted using Black. Run `poetry run black .`
-   **Linting**: Flake8 is used for linting. Run `poetry run flake8 .`
-   **Type Checking**: MyPy can be used. Run `poetry run mypy app scripts`
-   **Testing**: Pytest is set up. Run tests with `poetry run pytest`. (Test coverage is currently low).

## Contributing
Contributions are welcome! Please follow these steps:
1.  Fork the repository.
2.  Create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name`).
3.  Make your changes, ensuring to add relevant tests.
4.  Run linters, formatters, and tests.
5.  Commit your changes with descriptive messages.
6.  Push to your branch (`git push origin feature/your-feature-name`).
7.  Submit a Pull Request against the `main` (or `develop`) branch.

Please adhere to standard coding practices and ensure your contributions align with the project's goals.

## Roadmap

### Current Focus / Short-term
-   Solidify and test core accounting workflows (JE posting, reversals, CoA management).
-   Enhance `GSTManager` with actual data aggregation for F5 preparation.
-   Implement basic UI for Customer and Vendor management (CRUD operations).
-   Begin implementation of Sales Invoicing UI and backend logic.

### Medium-term
-   Implement Purchase Invoicing UI and backend logic.
-   Develop Bank Account management and basic transaction entry UI.
-   Expand Financial Reporting options (e.g., detailed GL report, Aged Receivables/Payables).
-   Implement User and Role management UI in Settings.

### Long-term
-   Bank Reconciliation features.
-   Full GST F5 report generation and IAF (Audit File) export.
-   Inventory module enhancements.
-   Dashboard with key financial KPIs.
-   Advanced reporting and analytics, possibly with custom report building.
-   Data backup and restore utilities.
-   Multi-company support (major architectural consideration).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
