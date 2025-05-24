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
