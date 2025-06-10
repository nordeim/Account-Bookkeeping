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

[Key Features](#key-features) • [Technology Stack](#technology-stack) • [Installation](#installation) • [Usage](#usage-guide) • [Project Structure](#project-structure) • [Testing](#testing) • [Roadmap](#roadmap) • [License](#license)

</div>

## Overview

SG Bookkeeper is a comprehensive, cross-platform desktop application designed to meet the accounting and bookkeeping needs of small to medium-sized businesses (SMBs) in Singapore. Built with Python and leveraging the power of PySide6 for a modern user interface and PostgreSQL for robust data management, it offers professional-grade financial tools tailored to Singapore's regulatory environment.

The application features a full multi-company architecture, a double-entry accounting core, GST management (including 9% rate calculations), interactive financial reporting, and modules for essential business operations (Customers, Vendors, Products/Services, Sales & Purchase Invoicing, Payments). A key highlight is the advanced Bank Reconciliation module, which supports CSV imports with detailed error reporting, persistent draft reconciliations, and visual aids for complex transaction matching. Its interactive dashboard provides at-a-glance KPIs, including graphical aging summaries and key financial ratios, calculated for any user-selected date. The system is built for data integrity and auditability, featuring comprehensive user and role management with detailed audit logs.

### Why SG Bookkeeper?

-   **Multi-Company Support**: Manage multiple distinct businesses from a single installation, with each company's data securely isolated in its own database.
-   **Singapore-Centric**: Designed with Singapore Financial Reporting Standards (SFRS), GST regulations (including the 9% rate), and IRAS compliance considerations at its core.
-   **Professional Grade**: Implements a full double-entry system, detailed audit trails (via database triggers and viewable UI), and robust data validation using Pydantic DTOs.
-   **User-Friendly Interface**: Aims for an intuitive experience for users who may not be accounting experts, while providing depth for professionals. Features include an interactive dashboard, visual reconciliation aids, and detailed error reporting.
-   **Open Source & Local First**: Transparent development. Your financial data stays on your local machine or private server, ensuring privacy and control. No subscription fees.
-   **Modern & Performant**: Utilizes asynchronous operations for a responsive UI and efficient database interactions, with a dedicated asyncio event loop.

## Key Features

*(Status: **Implemented**, **Foundational** (DB/Models ready but UI/Logic is a stub), **Planned**)*

### Core Accounting & System
-   **Multi-Company Management**: Create new company databases and switch between them. (**Implemented**)
-   **Comprehensive Double-Entry Bookkeeping**: The core of the application. (**Implemented**)
-   **Customizable Hierarchical Chart of Accounts**: Full CRUD UI for managing accounts. (**Implemented**)
-   **General Ledger**: Detailed transaction history with dimension filtering and export options. (**Implemented**)
-   **Journal Entry System**: UI for manual JEs (CRUD, post, reverse) and auto-generation from source documents. (**Implemented**)
-   **Multi-Currency Support**: Foundational models exist; transaction forms support multiple currencies. (**Foundational**)
-   **Fiscal Year and Period Management**: UI for creating fiscal years and auto-generating periods. (**Implemented**)

### Singapore Tax Compliance
-   **GST Tracking and Calculation**: Based on configurable tax codes. (**Implemented**)
-   **GST F5 Return Data Preparation**: UI to prepare, save drafts, and finalize GST F5 returns with settlement JEs. Includes detailed Excel export. (**Implemented**)
-   **Income Tax Computation Report**: Generates a preliminary tax computation based on P&L and non-deductible/non-taxable accounts. (**Implemented**)
-   **Withholding Tax Management**: DB models and manager stubs exist. (**Foundational**)

### Business Operations
-   **Customer, Vendor, Product/Service Management**: Full CRUD and list views with filtering. (**Implemented**)
-   **Sales & Purchase Invoicing**: Full lifecycle from draft to posting, with inventory and financial JEs created automatically. (**Implemented**)
-   **Payment Processing**: Record customer receipts and vendor payments with allocation to multiple invoices. (**Implemented**)
-   **Inventory Control (Weighted Average Cost)**: `InventoryMovement` records created on posting documents. (**Implemented**)

### Banking
-   **Bank Account Management**: Full CRUD and listing UI, with linkage to a GL account. (**Implemented**)
-   **Bank Transaction Management**: Manual entry and CSV bank statement import with robust, row-level error reporting dialog. (**Implemented**)
-   **Bank Reconciliation Module**:
    -   Persistent draft reconciliations. (**Implemented**)
    -   Interactive real-time feedback for matching transactions. (**Implemented**)
    -   Visual grouping of provisionally matched items. (**Implemented**)
    -   "Unmatch" functionality for provisionally matched items. (**Implemented**)
    -   Creation of adjustment JEs directly from the reconciliation screen. (**Implemented**)
    -   Finalization of balanced reconciliations and viewing of history. (**Implemented**)
    -   Automatic creation of system `BankTransaction` records from relevant Journal Entries. (**Implemented**)

### Reporting & Analytics
-   **Standard Financial Statements**: Balance Sheet, P&L, Trial Balance, and General Ledger. All viewable and exportable to PDF/Excel. (**Implemented**)
-   **Dashboard with KPIs**:
    -   KPIs calculated as of a user-selectable date. (**Implemented**)
    *   Key metrics: YTD P&L, Cash Balance, AR/AP totals. (**Implemented**)
    *   Financial Ratios: Current Ratio, Quick Ratio, Debt-to-Equity Ratio. (**Implemented**)
    *   Graphical AR & AP Aging summary bar charts. (**Implemented**)
-   **Cash Flow Statement** (Planned)
-   **GST Reports** (Implemented - See GST F5.)
-   **Customizable Reporting Engine** (Foundational)

### System & Security
-   **User Authentication & RBAC**: Full UI for managing users, roles, and permissions. (**Implemented**)
-   **Comprehensive Audit Trails**: Database triggers log all data changes. UI in Settings tab provides a paginated and filterable view of both high-level actions and detailed field-level changes. (**Implemented**)

## Technology Stack
-   **Programming Language**: Python 3.9+ (up to 3.12)
-   **UI Framework**: PySide6 6.9.0+ (including `QtCharts` for visualizations)
-   **Database**: PostgreSQL 14+
-   **ORM**: SQLAlchemy 2.0+ (Asynchronous ORM)
-   **Async DB Driver**: `asyncpg`
-   **Data Validation (DTOs)**: Pydantic V2
-   **Password Hashing**: `bcrypt`
-   **Reporting Libraries**: `reportlab` (PDF), `openpyxl` (Excel)
-   **Dependency Management**: Poetry
-   **Date/Time Utilities**: `python-dateutil`
-   **Testing**: Pytest, pytest-asyncio, pytest-cov, unittest.mock

## Installation

This guide is for developers setting up the application from source.

### Prerequisites
-   Python 3.9 or higher
-   PostgreSQL Server 14 or higher (with admin/superuser access for initial setup)
-   Poetry (Python packaging and dependency management tool)
-   Git

### Developer Installation Steps
1.  **Clone Repository**: `git clone https://github.com/yourusername/sg_bookkeeper.git && cd sg_bookkeeper`
2.  **Install Dependencies**: `poetry install --with dev`
3.  **Configure `config.ini`**:
    *   The application looks for `config.ini` in a platform-specific user config directory:
        *   Linux: `~/.config/SGBookkeeper/config.ini`
        *   macOS: `~/Library/Application Support/SGBookkeeper/config.ini`
        *   Windows: `%APPDATA%\SGBookkeeper\config.ini`
    *   Create the `SGBookkeeper` directory if it doesn't exist.
    *   Create `config.ini` in that directory. Start with the following content, **providing your PostgreSQL superuser credentials** (like `postgres`) for the initial setup. This is needed for creating new company databases.
        ```ini
        [Database]
        username = YOUR_POSTGRES_ADMIN_USER
        password = YOUR_POSTGRES_ADMIN_PASSWORD
        host = localhost
        port = 5432
        database = sg_bookkeeper_default
        echo_sql = False
        pool_min_size = 2
        pool_max_size = 10
        pool_recycle_seconds = 3600

        [Application]
        theme = light
        language = en
        last_opened_company_id = 
        ```
4.  **Run the Application**:
    ```bash
    poetry run sg_bookkeeper
    ```
5.  **Create Your First Company**:
    *   On first run, the application may connect to a default database (e.g., `postgres`) but most features will be inert.
    *   Go to **File > New Company...**
    *   In the dialog, provide a user-friendly **Company Name** (e.g., "My Test Bakery") and a unique **Database Name** (e.g., `sgb_test_bakery`). The database name must be valid for PostgreSQL (lowercase, no spaces).
    *   Click "OK". The application will use the admin credentials from `config.ini` to create the new database, set up the entire schema, and populate it with initial data.
    *   You will be prompted to open the new company, which requires an application restart. Click "Yes".
    *   The application will restart and automatically connect to your new company database. The `config.ini` file will be updated to point to this new database for future launches.
    *   The default login is `admin` / `password`. You will be prompted to change this password on first login.

## Usage Guide
-   **Switching Companies**: Go to **File > Open Company...** to launch the `Company Manager` dialog. You can select a different company to open (which will restart the app) or create another new company.
-   **Dashboard Tab**: View key financial indicators. Use the "As Of Date" selector and "Refresh KPIs" button to analyze your financial position on any given day.
-   **Banking Tab**: Manage bank accounts and transactions. The "Bank Reconciliation" sub-tab is the primary tool for reconciling your accounts.
-   **Other Modules**: Explore the tabs for `Accounting`, `Sales`, `Purchases`, `Payments`, `Customers`, `Vendors`, and `Products` to manage all aspects of your business operations.
-   **Settings Tab**: Configure company details, manage fiscal years, users, roles, and view detailed audit logs.
-   **Reports Tab**: Generate GST F5 Returns, standard financial statements (BS, P&L, TB, GL), and an Income Tax Computation report. All reports are exportable to PDF/Excel.

## Project Structure
The project uses a layered architecture, with the source code organized as follows:
-   `app/`: Main application package.
    -   `core/`: Central components like `ApplicationCore`, `DatabaseManager`, `SecurityManager`, and the new `CompanyManager`.
    -   `models/`: SQLAlchemy ORM classes, mirroring the DB schema.
    -   `services/`: The Data Access Layer, implementing the Repository pattern.
    -   `business_logic/`, `accounting/`, `tax/`, `reporting/`: The Business Logic Layer, containing "Manager" classes that orchestrate workflows.
    -   `ui/`: All PySide6 GUI components, organized by feature module.
-   `scripts/`: Database setup scripts (`schema.sql`, `initial_data.sql`, `db_init.py`).
-   `tests/`: All automated tests.

## Testing
Automated tests using Pytest ensure code quality. A comprehensive suite of unit tests covers services, managers, and utilities.
-   **Run all tests**: `poetry run pytest`
-   **Generate a coverage report**: `poetry run pytest --cov=app` (requires `pytest-cov` plugin)

## Contributing
Contributions are welcome. Please fork the repository, create a feature branch, make your changes, add tests, and submit a pull request. Adherence to the existing architecture and coding standards is required.

## Roadmap

### Current Focus / Next Steps
-   **Automated Testing (CRITICAL)**:
    *   Expand unit test coverage to achieve higher percentages for all managers and remaining service methods.
    *   Begin setup and implementation of integration tests for core workflows (e.g., invoice posting and payment allocation cycle, full bank reconciliation save-and-finalize cycle).
-   **Bank Reconciliation Enhancements**:
    *   Implement logic for handling more complex matches (e.g., one-to-many with different amounts but a shared reference, requiring a write-off JE).
    *   UI improvements for visually linking matched items within the "Provisionally Matched" tables.
-   **Dashboard Enhancements**:
    *   Allow user customization of the dashboard layout or choice of KPIs to display.
    *   Implement period-over-period comparisons (e.g., This Month vs. Last Month).

### Long-term
-   Advanced reporting and analytics (e.g., customizable report builder, trend analysis).
-   Inventory Control enhancements (e.g., stocktakes, multiple locations, FIFO/LIFO costing methods).
-   Cloud synchronization options (optional data backup/sync to a user-provided cloud storage).
-   Enhanced Tax Compliance features (e.g., preparation of IRAS Audit File (IAF)).
-   Full UI test suite using a suitable framework (e.g., `pytest-qt`).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
