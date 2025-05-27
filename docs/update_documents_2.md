<think>
The application is launching and shutting down cleanly! The log message "INFO - Using compiled Qt resources for CustomersWidget" is a new and positive sign, indicating that `CustomersWidget` was initialized, and its `icon_path_prefix` logic (which includes a logger call) executed correctly. This implies that the integration of the basic Customer Management module (backend and frontend UI stubs/foundations) has been successful at the startup level.

**Current Project Status Recap:**

*   **Backend for Customer Management (Phase A)**: Complete.
*   **Frontend UI Foundation for Customer Management (Phase B - partially done)**:
    *   B1. `CustomerTableModel` (Created and seems fine).
    *   B2. `CustomerDialog` (Created and seems fine).
    *   B3. `CustomersWidget` (Enhanced from stub to include table, toolbar, basic filter UI, and slots for actions. Data loading and actions are connected to the backend manager).
*   All previously implemented features remain stable.

**The user asks to "proceed with the next step in your plan for the implementation of 'the basic Customer Management module'". If this has been completed, please carefully update the README.md and TDS documents...**

Based on the plan, "Phase B: Frontend UI for Customer Management" involved:
    *   B1. Create `CustomerTableModel` (Done)
    *   B2. Create `CustomerDialog` (Done)
    *   B3. Enhance `CustomersWidget` (from stub to functional) (Done in the previous step)

This means the **initial implementation of the basic Customer Management module is complete.** The UI allows listing, adding, editing, and toggling the active status of customers.

Therefore, the "next step" as per the user's request is to:
**Update the `README.md` and `Technical Design Specification Document (v4).md` to carefully and accurately detail the current state of the project, including the newly implemented Customer Management module.**

**Plan for this Turn: Documentation Update**

**Objective:** Reflect the newly implemented basic Customer Management functionality in the project's `README.md` and `Technical Design Specification Document (v4).md`.

**Detailed Plan & Checklist:**

**1. Update `README.md`**
   *   **Goal:** Inform users and potential contributors about the new Customer Management feature.
   *   **File to Update:** `README.md`
   *   **Checklist & Tasks:**
        *   [ ] **Key Features Section**:
            *   Update the status of "Customer and Vendor Relationship Management (CRM)" or add a specific entry for "Basic Customer Management" and mark it as "Partially Implemented" or "Basic UI Implemented".
            *   Briefly describe what's available (list, add, edit, toggle active status).
        *   [ ] **Project Structure Section**:
            *   Add entries for the new files created for customer management:
                *   `app/services/business_services.py` (if not already listed generally)
                *   `app/business_logic/__init__.py`
                *   `app/business_logic/customer_manager.py`
                *   `app/ui/customers/customer_table_model.py`
                *   `app/ui/customers/customer_dialog.py`
            *   Verify `app/ui/customers/customers_widget.py` is mentioned as updated.
        *   [ ] **Usage Guide Section** (if it exists or is planned):
            *   Briefly mention that the "Customers" tab now allows basic customer management.
        *   [ ] **Roadmap Section**:
            *   Update the status or progress related to CRM/Customer Management. Indicate that basic functionality is in place and more advanced features (e.g., linking to invoices, detailed transaction history per customer) are future.

**2. Update `Technical Design Specification Document (v4).md` (to become v5)**
   *   **Goal:** Detail the technical design and implementation of the Customer Management module.
   *   **File to Update:** `Technical Design Specification Document (v4).md` (will effectively become v5 after these updates)
   *   **Checklist & Tasks:**
        *   [ ] **Document Version**: Increment to v5. Update date.
        *   [ ] **Section 1.2 (Scope)**: Mention that Customer Management (basic CRUD, listing) is now covered.
        *   [ ] **Section 1.4 (System Overview)**: Briefly note the addition of basic Customer Management.
        *   [ ] **Section 2.2 (Component Architecture)**:
            *   **2.2.3 Functional Components (Managers/Services)**: Add `CustomerManager` and `CustomerService` with their responsibilities.
            *   **2.2.5 User Interface Components**: Detail `CustomersWidget`, `CustomerDialog`, and `CustomerTableModel`.
        *   [ ] **Section 2.5 (Design Patterns)**:
            *   If the Customer module implementation highlights any specific pattern usage not already covered, mention it or use it as a concrete example.
        *   [ ] **Section 3 (Data Architecture)**:
            *   **3.3 Detailed Schema Definitions**: `business.customers` table is already in `schema.sql`. No change needed here, but ensure it's referenced as being actively used.
            *   **3.4.1 SQLAlchemy ORM Model Definitions**: `app/models/business/customer.py` already exists. Briefly reference its key attributes if not already done.
            *   **3.4.2 Data Access Interface**: Update with `ICustomerRepository` details from `app/services/__init__.py`.
        *   [ ] **Section 4 (Module Specifications)**:
            *   Add a new major subsection for "Business Operations Modules" (if it doesn't exist) or directly "Customer Management Module".
            *   **4.X.1 Customer Manager (`app/business_logic/customer_manager.py`)**:
                *   Detail its responsibilities (validation, orchestration).
                *   Provide key function signatures/snippets (`create_customer`, `update_customer`, `get_customers_for_listing`, `toggle_customer_active_status`).
            *   **(Optional) Customer Service (`app/services/business_services.py`)**: Briefly describe its role as the repository for `Customer` if not covered sufficiently under Data Access Layer.
        *   [ ] **Section 5 (User Interface Implementation)**:
            *   Add a new subsection for `CustomersWidget`.
                *   Describe its layout (toolbar, filter, table).
                *   Explain its data loading (`_load_customers`) and interaction with `CustomerManager`.
                *   Mention `CustomerTableModel`.
            *   Add a new subsection for `CustomerDialog`.
                *   Describe its fields and purpose (Add/Edit).
                *   Explain how it collects data into DTOs and calls `CustomerManager`.
        *   [ ] **Section 7 (Database Access Implementation)**:
            *   **7.2 Repository Implementation**: Add an example for `CustomerService` if it highlights specific patterns or complex queries (e.g., `get_all_summary` with filtering).
        *   [ ] **Section 9 (Conclusion/Current Status)**: Update to reflect that basic Customer Management is now implemented. List it under "Key Implementation Highlights."
        *   [ ] **Update relevant DTOs section if changes were made to `pydantic_models.py`** (Customer DTOs were added, so this section in TDS needs to reflect that). This was part of step A1.
        *   **Throughout**: Ensure consistency in naming and paths.

This is a significant documentation update. I will proceed by generating the updated `README.md` first, then the updated TDS.
</think>

This is excellent progress! The application is stable, and the log confirms that the new `CustomersWidget` is being initialized and its resources are being recognized. This means the foundational backend and UI structure for Customer Management (Phase A and the initial parts of Phase B) are in place without causing immediate runtime errors at startup.

Since the core implementation steps for the **basic Customer Management module** (DTOs, Service, Manager, TableModel, Dialog, Widget integration) are complete, the next logical step, as per your request, is to **update the `README.md` and `Technical Design Specification Document`** to reflect these new capabilities and the current state of the project.

This documentation update is crucial for keeping the project well-documented for users and current/future developers.

---
**1. Update `README.md`**

**Goal:** Update the README to reflect the addition of basic Customer Management functionality and the new files/structure related to it.

```markdown
# README.md
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

The application features a double-entry accounting core, GST management, financial reporting, and modules for essential business operations including basic customer management. Its goal is to provide an intuitive, powerful, and compliant solution that empowers business owners and accountants.

### Why SG Bookkeeper?

-   **Singapore-Centric**: Designed with Singapore Financial Reporting Standards (SFRS), GST regulations (including 9% rate), and IRAS compliance considerations at its core.
-   **Professional Grade**: Implements a full double-entry system, detailed audit trails (via database triggers), and robust data validation using Pydantic DTOs.
-   **User-Friendly Interface**: Aims for an intuitive experience for users who may not be accounting experts, while providing depth for professionals. Core accounting and basic customer management UI are functional.
-   **Open Source & Local First**: Transparent development. Your financial data stays on your local machine or private server, ensuring privacy and control. No subscription fees.
-   **Modern & Performant**: Utilizes asynchronous operations for a responsive UI and efficient database interactions, with a dedicated asyncio event loop.

## Key Features

*(Status: Implemented, Partially Implemented, Basic UI Implemented, Foundational (DB/Models ready), Planned)*

### Core Accounting
-   **Comprehensive Double-Entry Bookkeeping** (Implemented)
-   **Customizable Hierarchical Chart of Accounts** (Implemented - UI for CRUD, Singapore-specific templates in `data/`)
-   **General Ledger with detailed transaction history** (Foundational - JEs can be viewed, full GL report planned)
-   **Journal Entry System** (Implemented - UI for General Journal; Sales/Purchases JEs via respective modules are planned)
-   **Multi-Currency Support** (Foundational - `accounting.currencies` & `exchange_rates` tables and models exist, `CurrencyManager` for backend logic. UI integration in transactions pending.)
-   **Fiscal Year and Period Management** (Implemented - UI in Settings for FY creation and period auto-generation; period closing/reopening logic in manager.)
-   **Budgeting and Variance Analysis** (Foundational - `accounting.budgets` & `budget_details` tables and models exist. UI/Logic planned.)

### Singapore Tax Compliance
-   **GST Tracking and Calculation** (Partially Implemented - `TaxCode` setup for SR, ZR, ES, TX at 9%; `TaxCalculator` exists. `GSTManager` can create `GSTReturn` records. Full JE line item tax application in all transaction UIs is ongoing.)
-   **GST F5 Return Data Preparation & Finalization** (Partially Implemented - `GSTManager` backend for data prep & finalization with JE settlement. Basic UI in Reports tab for prep, view, draft save, and finalize.)
-   **Income Tax Estimation Aids** (Planned - `IncomeTaxManager` stub exists.)
-   **Withholding Tax Management** (Foundational - `accounting.withholding_tax_certificates` table/model and `WithholdingTaxManager` stub exist.)

### Business Operations
-   **Customer Management** (Basic UI Implemented - List, Add, Edit, Toggle Active status for Customers.)
-   **Vendor Management** (Foundational - `business.vendors` table/model exists. UI/Logic planned.)
-   **Sales Invoicing and Accounts Receivable** (Foundational - `business.sales_invoices` tables/models exist. UI/Logic planned.)
-   **Purchase Invoicing and Accounts Payable** (Foundational - `business.purchase_invoices` tables/models exist. UI/Logic planned.)
-   **Payment Processing and Allocation** (Foundational - `business.payments` tables/models exist. UI/Logic planned.)
-   **Bank Account Management and Reconciliation Tools** (Foundational - `business.bank_accounts` & `bank_transactions` tables/models exist. UI is a stub.)
-   **Product and Service Management** (Foundational - `business.products` table/model exists. UI/Logic planned.)
-   **Basic Inventory Control** (Foundational - `business.inventory_movements` table/model exists. Logic planned.)

### Reporting & Analytics
-   **Standard Financial Statements**: Balance Sheet, Profit & Loss, Trial Balance (Implemented - `FinancialStatementGenerator` produces data; `ReportEngine` exports basic PDF/Excel. Basic UI in Reports tab for selection, on-screen view, and export.)
-   **Cash Flow Statement** (Planned)
-   **GST Reports** (Partially Implemented - See GST F5 above. Formatted GST reports planned.)
-   **Customizable Reporting Engine** (Planned - Current `ReportEngine` is basic.)
-   **Dashboard with Key Performance Indicators (KPIs)** (Planned - UI is a stub.)

### System & Security
-   **User Authentication with Role-Based Access Control (RBAC)** (Implemented - `SecurityManager`, DB tables for users, roles, permissions are functional. Initial admin user seeded.)
-   **Granular Permissions System** (Foundational - DB tables exist, `SecurityManager.has_permission` implemented. Full UI integration pending.)
-   **Comprehensive Audit Trails** (Implemented - DB triggers populate `audit.audit_log` and `audit.data_change_history` for key tables. Uses `app.current_user_id` session variable.)
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
-   **Email Validation**: `email-validator` (via `pydantic[email]`)

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
    This command creates a virtual environment (typically `.venv` in the project root if one doesn't exist) and installs all dependencies specified in `pyproject.toml`, including `email-validator` via `pydantic[email]`.

3.  **Prepare PostgreSQL Database User:** (Steps remain the same)
    *   Connect to your PostgreSQL instance as a superuser (e.g., `postgres`).
    *   Create a dedicated database user: `CREATE USER sgbookkeeper_user WITH PASSWORD 'YourSecurePassword123!';`

4.  **Configure Database Connection (`config.ini`):** (Steps remain the same)
    *   Locate/Create `config.ini` in platform-specific user config directory.
    *   Ensure connection details match your PostgreSQL setup.

5.  **Initialize the Database Schema and Seed Initial Data:** (Steps remain the same)
    ```bash
    poetry run sg_bookkeeper_db_init --user postgres --password YOUR_POSTGRES_ADMIN_PASSWORD --dbname sg_bookkeeper --drop-existing
    ```

6.  **Grant Privileges to Application User:** (Steps remain the same)
    *   Connect as PostgreSQL admin and grant necessary privileges to `sgbookkeeper_user` on all schemas and tables.

7.  **Compile Qt Resources (Recommended):**
    ```bash
    poetry run pyside6-rcc resources/resources.qrc -o app/resources_rc.py
    ```
    The application now logs whether compiled resources or direct paths are used.

8.  **Run the Application:**
    Ensure your `config.ini` points to the application user (`sgbookkeeper_user`).
    ```bash
    poetry run sg_bookkeeper
    ```

## Usage Guide

The application is under active development. Current functional areas include:

-   **Accounting Tab**:
    -   **Chart of Accounts**: View, add, edit, and (de)activate accounts.
    -   **Journal Entries**: View list of journal entries with filtering. Create new general journal entries with multiple lines, tax codes. Edit draft entries. Post entries. Reverse posted entries.
-   **Customers Tab**:
    -   View list of customers with basic search and active/inactive filter.
    -   Add new customers with detailed information.
    -   Edit existing customers.
    -   Toggle active/inactive status of customers.
-   **Reports Tab**:
    -   **GST F5 Preparation**: Select period, prepare GST F5 data based on posted transactions, view summary, save as draft, and finalize (which creates a settlement JE).
    *   **Financial Statements**: Select report type (Balance Sheet, P&L, Trial Balance), set date parameters, generate and view an on-screen summary, and export to PDF or Excel.
-   **Settings Tab**:
    -   View and edit Company Information.
    -   Manage Fiscal Years: Add new fiscal years and automatically generate their monthly or quarterly periods. View existing fiscal years.

Other modules like Vendors, full Banking, advanced Product/Inventory Management, and the Dashboard are placeholders for future development. Upon first run (after DB initialization), an `admin` user is created with the password `password`. You will be prompted to change this password for security.

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
│   │   ├── __init__.py
│   │   ├── account_service.py
│   │   ├── accounting_services.py # For AccountType, Currency, ExchangeRate, FiscalYear services
│   │   ├── business_services.py   # For CustomerService, VendorService, etc. (NEW)
│   │   ├── core_services.py
│   │   ├── fiscal_period_service.py
│   │   ├── journal_service.py
│   │   └── tax_service.py
│   ├── accounting/         # Business logic managers for accounting module
│   ├── tax/                # Business logic managers for tax module
│   ├── business_logic/     # Business logic managers for business entities (e.g., CustomerManager) (NEW)
│   │   ├── __init__.py     # (NEW)
│   │   └── customer_manager.py # (NEW)
│   ├── reporting/          # Logic managers for generating reports
│   ├── ui/                 # PySide6 UI components (organized by module)
│   │   └── customers/      # Customer specific UI
│   │       ├── __init__.py
│   │       ├── customer_dialog.py # (NEW)
│   │       ├── customer_table_model.py # (NEW)
│   │       └── customers_widget.py # (Enhanced)
│   └── utils/              # General utility functions, Pydantic DTOs
├── data/                   # Default data templates (e.g., CoA templates)
├── docs/                   # Project documentation
├── resources/              # UI assets (icons, images)
│   └── resources.qrc       # Qt resource collection file
├── scripts/                # Database initialization scripts
│   ├── db_init.py
│   ├── schema.sql
│   └── initial_data.sql
├── tests/                  # Automated tests (planned)
├── .gitignore
├── pyproject.toml          # Poetry configuration
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
-   **Testing**: Pytest is set up. Run tests with `poetry run pytest`. (Test coverage needs improvement).

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
-   **Vendor Management**: Implement basic UI (List, Add, Edit, Toggle Active) similar to Customer Management.
-   **Product/Service Management**: Implement basic UI for managing products and services.
-   **Refine Reporting**: Improve on-screen display of financial reports (e.g., using `QTableView`).
-   **User and Role Management UI**: Add UI in Settings for managing users, roles, and permissions.

### Medium-term
-   Basic Sales and Purchase Invoicing workflows.
-   Bank Account management and basic transaction entry UI in Banking module.
-   Enhance GST F5 report with full data aggregation and export options (e.g., IAF format).

### Long-term
-   Bank Reconciliation features.
-   Advanced reporting and analytics, dashboard KPIs.
-   Inventory Control enhancements.
-   Multi-company support.
-   Cloud synchronization options.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

---
**Validation for `README.md`:**
*   **Overview**: Updated to mention basic customer management.
*   **Why SG Bookkeeper**: Updated "User-Friendly Interface" to reflect customer management UI.
*   **Key Features**:
    *   Updated "Customer Management" status to "Basic UI Implemented" and briefly described its capabilities.
    *   Updated "GST F5 Return Data Preparation & Finalization" to reflect that the UI now supports these steps.
    *   Updated "Standard Financial Statements" to reflect that basic UI for selection, view, and export is implemented.
*   **Technology Stack**: Added `email-validator` via `pydantic[email]`.
*   **Installation**: Updated `poetry install` to note it includes `email-validator`.
*   **Usage Guide**: Added a section for the "Customers Tab" describing its current functionality. Updated GST and Reports tab descriptions.
*   **Project Structure**: Added new files/directories for customer management backend (`app/services/business_services.py`, `app/business_logic/*`) and frontend (`app/ui/customers/*`).
*   **Roadmap**: Updated "Current Focus / Short-term" to reflect that Customer Management basics are done and Vendor/Product are next for business modules.

The README now accurately reflects the current state, including the new Customer Management features.

---
Next, I will generate the updated **Technical Design Specification Document (v5).md**. This will be a more extensive update.

---

