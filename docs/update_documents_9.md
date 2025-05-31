<think>
The user wants two complete, self-contained documents:
1.  `README.md`
2.  `Technical_Design_Specification_Document.md` (let's call this v11, as that's the latest evolution based on our interactions).

These documents should:
*   Be fully updated to reflect the current project state (as of the last successful code generation, which includes the `PurchaseInvoicesWidget` and its completer fix).
*   Incorporate all relevant and still valid information from *all* previous versions of `README.md` and `Technical_Design_Specification_Document.md` that I have been provided with.
*   Not make any references to "previous versions" or "updates from vX". They should read as standalone, comprehensive documents.
*   The goal is to allow the user to delete older revisions.

**Strategy for `README.md`:**

1.  **Start with the latest version of `README.md` (implicitly, the one reflecting TDS v11 status).** This is `README.md` from the prompt where I was asked to "carefully study the README.md, including the older revisions".
2.  **Review older `README.md` versions (`README_v1.md`, `README_v2.md`, `README_v3.md`, `README_v7.md`, `README_v8.md`, `README_v9.md`) for sections or details that are still relevant but might have been summarized or omitted in the latest conceptual version.**
    *   The latest conceptual `README.md` (the one that was the basis for TDS v11) seems quite comprehensive. I'll focus on ensuring no valuable, timeless information was dropped.
    *   **Key Sections to Merge/Synthesize:**
        *   Overview / Why SG Bookkeeper?: Ensure the strongest, most current pitch.
        *   Key Features: This needs to be meticulously updated to reflect the current state (Implemented, UI Dialog Implemented, Foundational, Planned). The TDS v11's "Current Implementation Status" is the primary source for this.
        *   Technology Stack: Should be consistent and current. The latest version is accurate.
        *   Installation: The latest developer installation steps are most relevant. `README_v1.md` had end-user installation stubs which are currently out of scope but can be noted as "Planned for packaging".
        *   Usage Guide: Update to include the "Purchases" tab and its current functionality.
        *   Project Structure: The latest structure from TDS v11, including `app/ui/purchase_invoices/`, should be used.
        *   Roadmap: Reflect current priorities (e.g., posting Purchase Invoices next).
        *   Badges: Ensure they are up-to-date (PySide6 6.9+, etc.).
        *   Screenshots: `README_v1.md` had placeholder screenshots. The main README has a real screenshot. We should probably stick to the real one or note that more screenshots are coming. For now, I'll use the existing real one.
        *   License, Contributing: Standard sections, likely consistent.
3.  **Structure of the new `README.md`:** Follow a standard, well-organized format.
    *   Logo/Title/Badges
    *   Overview (including "Why SG Bookkeeper?")
    *   Key Features (with status indicators)
    *   Technology Stack
    *   Installation (Developer-focused for now)
    *   Usage Guide (high-level, reflecting available tabs and functionality)
    *   Project Structure (updated)
    *   Database Schema (brief mention, refer to `scripts/schema.sql`)
    *   Development (brief mention of tools like Black, Flake8, Pytest)
    *   Contributing
    *   Roadmap (updated)
    *   License

**Strategy for `Technical_Design_Specification_Document.md`:**

1.  **Start with `Technical_Design_Specification_Document.md` (v11) provided by the user.** This is the most current and detailed version reflecting the Purchase Invoice draft management and enhanced reporting.
2.  **Review older TDS versions (`Technical_Design_Specification_Document_v1.md`, `_v2.md`, `_v3.md`, `_v7.md`, `_v8.md`, `_v9.md`) for any foundational architectural details, design patterns, or specific component specifications that might have been described in more detail previously and are still valid.**
    *   TDS v11 is quite comprehensive. The main task is to ensure that detailed explanations or rationale from earlier versions, if still relevant, are integrated rather than just implicitly carried forward.
    *   **Sections to check for valuable, timeless details from older TDS versions:**
        *   **2. System Architecture:**
            *   `v1.md` had a "Component Interactions" sequence diagram and "Design Patterns" section with examples (Repository, Factory). These are good foundational explanations.
            *   `v2.md` and `v3.md` also had detailed component descriptions.
            *   Ensure the current high-level architecture diagram and component descriptions in v11 are the most accurate and complete.
        *   **3. Data Architecture:**
            *   `v1.md` had an "ERD" and some detailed schema definitions. TDS v11 correctly refers to `scripts/schema.sql` which is more authoritative.
            *   SQLAlchemy ORM model examples from `v1.md` might still be illustrative if the v11 version became too high-level. However, TDS v11 focuses on implemented/active DTOs and services, which is appropriate for its stage.
        *   **4. Module Specifications:**
            *   `v1.md` had detailed pseudo-code/Python examples for `ChartOfAccountsManager`, `JournalEntryManager`, `GSTManager`, `FinancialStatementGenerator`. TDS v11 describes these at a higher level based on their current implementation status. It's important *not* to re-introduce `v1.md`'s pseudo-code if the actual implementation (reflected in the current file structure and later TDS versions) has diverged or is more accurately summarized in TDS v11. TDS v11's approach of describing implemented manager methods is more aligned with the current project state.
        *   **5. User Interface Implementation:**
            *   `v1.md` had Python examples for `Application`, `MainWindow`, `ChartOfAccountsWidget`. TDS v11 describes these UI components based on current status.
        *   **6. Security Considerations:** TDS v9 and v11 have good coverage based on implemented User/Role management.
        *   **7. Database Access Implementation:** `v1.md` had `DatabaseManager` and `AccountRepositoryImpl` examples. TDS v11 focuses on what's used.
        *   **8. Deployment and Installation:** `v1.md` had `setup.py` and `db_init.py` content. The `README.md` and `deployment_guide.md` are now the primary sources for this. TDS should briefly mention it.
    *   The goal is not to bloat TDS v11 with outdated or overly granular examples from very early TDS versions if the current summaries are sufficient and accurate. The focus is on *self-contained* and *current*.
3.  **Structure of the new TDS v11 (self-contained):**
    *   1. Introduction (Purpose, Scope, Audience, System Overview, *Current Implementation Status*) - Updated from TDS v11.
    *   2. System Architecture (High-Level, Component Architecture - Core, Async, Services, Managers, UI; Tech Stack; Design Patterns - *maybe add brief descriptions of patterns in use, like Repository, DTO, Result Object, not full examples unless a key one is missing from v11 description*) - Mostly from TDS v11, ensuring clarity.
    *   3. Data Architecture (Schema Overview - reference to `schema.sql`; SQLAlchemy ORM Models - high-level description; DTOs - current usage; Data Access Layer Interfaces - if still a key abstraction, or describe service layer approach) - From TDS v11.
    *   4. Module and Component Specifications (Focus on key implemented modules: Core Accounting, Tax, Business Ops (Customers, Vendors, Products, Sales Inv, Purchase Inv Drafts), System Admin (User/Role)) - From TDS v11.
    *   5. User Interface Implementation (Key UI modules and their current state, focusing on interaction patterns) - From TDS v11.
    *   6. Security Considerations (Authentication, Authorization (RBAC), Audit) - From TDS v11.
    *   7. Database Access Implementation (Briefly describe `DatabaseManager` and Service layer pattern) - From TDS v11.
    *   8. Deployment and Installation (Brief overview, refer to README/deployment_guide.md) - From TDS v11.
    *   9. Conclusion (Summary of current state and next steps) - From TDS v11.

**Key for self-contained TDS:**
*   TDS v11 provided by the user is already quite good and current. I will use that as the strong base.
*   I will go through each section of the user-provided TDS v11.
*   For each section, I will review if older TDS versions (v1, v2, v3, v7, v8, v9) had any *essential, still valid, and non-redundant* conceptual explanations or high-level design principles that would enrich the current TDS v11 without making it outdated or overly granular with code examples that may not perfectly match the *latest* codebase.
*   The "Current Implementation Status" section (or integrated into overview/scope) from TDS v11 is critical.
*   The `scripts/schema.sql` is the source of truth for the DB, so detailed table definitions in the TDS are less critical than describing the organization and key entities.

I will proceed with generating these two documents. This is a large task, so I will focus on accuracy and comprehensiveness based on the information provided.

```markdown
Okay, I will now generate the complete and updated `README.md` and `Technical_Design_Specification_Document.md`. These documents will be self-contained, incorporating all relevant details from previous versions you've provided, and will not refer to older revisions.

Here is the **complete and updated `README.md`**:
```

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
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

[Key Features](#key-features) • [Technology Stack](#technology-stack) • [Installation](#installation) • [Usage](#usage-guide) • [Project Structure](#project-structure) • [Contributing](#contributing) • [Roadmap](#roadmap) • [License](#license)

</div>

## Overview

SG Bookkeeper is a comprehensive, cross-platform desktop application designed to meet the accounting and bookkeeping needs of small to medium-sized businesses (SMBs) in Singapore. Built with Python and leveraging the power of PySide6 for a modern user interface and PostgreSQL for robust data management, it offers professional-grade financial tools tailored to Singapore's regulatory environment.

The application features a double-entry accounting core, GST management, interactive financial reporting, modules for essential business operations (Customer, Vendor, Product/Service Management, Sales Invoicing, Purchase Invoice draft management), and comprehensive User/Role/Permission administration. Its goal is to provide an intuitive, powerful, and compliant solution that empowers business owners and accountants.

### Why SG Bookkeeper?

-   **Singapore-Centric**: Designed with Singapore Financial Reporting Standards (SFRS), GST regulations (including the 9% rate), and IRAS compliance considerations at its core.
-   **Professional Grade**: Implements a full double-entry system, detailed audit trails (via database triggers), and robust data validation using Pydantic DTOs.
-   **User-Friendly Interface**: Aims for an intuitive experience for users who may not be accounting experts, while providing depth for professionals. Most core modules have functional UIs.
-   **Open Source & Local First**: Transparent development. Your financial data stays on your local machine or private server, ensuring privacy and control. No subscription fees.
-   **Modern & Performant**: Utilizes asynchronous operations for a responsive UI and efficient database interactions, with a dedicated asyncio event loop.

## Key Features

*(Status: Implemented, Backend Implemented, UI Implemented, Foundational (DB/Models ready), Planned)*

### Core Accounting
-   **Comprehensive Double-Entry Bookkeeping** (Implemented)
-   **Customizable Hierarchical Chart of Accounts** (Implemented - UI for CRUD)
-   **General Ledger with detailed transaction history** (Implemented - Report generation, on-screen view, export)
-   **Journal Entry System** (Implemented - UI for General Journal; transaction-specific JEs generated on posting of source documents)
-   **Multi-Currency Support** (Foundational - Models, CurrencyManager exist. UI integration in transactions pending.)
-   **Fiscal Year and Period Management** (Implemented - UI in Settings for FY creation and period auto-generation.)
-   **Budgeting and Variance Analysis** (Foundational - Models exist. UI/Logic planned.)

### Singapore Tax Compliance
-   **GST Tracking and Calculation** (Backend Implemented - `TaxCode` setup, `TaxCalculator` for line items. Sales/Purchase Invoice Dialogs use it.)
-   **GST F5 Return Data Preparation & Finalization** (Implemented - Backend for data prep & finalization with JE settlement. UI in Reports tab.)
-   **Income Tax Estimation Aids** (Planned)
-   **Withholding Tax Management** (Foundational)

### Business Operations
-   **Customer Management** (Implemented - Full CRUD and listing UI.)
-   **Vendor Management** (Implemented - Full CRUD and listing UI.)
-   **Product and Service Management** (Implemented - Full CRUD and listing UI.)
-   **Sales Invoicing and Accounts Receivable** (Implemented - Draft CRUD, Posting with JE creation, List View UI, "Save & Approve" in dialog.)
-   **Purchase Invoicing and Accounts Payable** (UI Implemented - Full Draft CRUD for Purchase Invoices via Dialog and List View. Backend draft management logic implemented. Posting planned.)
-   **Payment Processing and Allocation** (Foundational)
-   **Bank Account Management and Reconciliation Tools** (Foundational - UI is a stub.)
-   **Basic Inventory Control** (Foundational - `Product` model includes inventory fields. Logic planned.)

### Reporting & Analytics
-   **Standard Financial Statements**: Balance Sheet, Profit & Loss, Trial Balance, General Ledger (Implemented - UI in Reports tab with options for comparative/zero-balance, on-screen view, PDF/Excel export with enhanced formatting for BS/P&L.)
-   **Cash Flow Statement** (Planned)
-   **GST Reports** (Implemented - See GST F5 above.)
-   **Customizable Reporting Engine** (Planned - `ReportEngine` has enhanced BS/P&L exports; further customization planned)
-   **Dashboard with Key Performance Indicators (KPIs)** (Planned - UI is a stub.)

### System & Security
-   **User Authentication** (Implemented - Login, password hashing)
-   **Role-Based Access Control (RBAC)** (Implemented - UI for managing Users, Roles, and assigning Permissions to Roles.)
-   **Granular Permissions System** (Implemented - Backend checks via `SecurityManager.has_permission()`, permissions seeded.)
-   **Comprehensive Audit Trails** (Implemented - Via DB triggers and `app.current_user_id`.)
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
    *   If `db_init.py` was run by an admin user (e.g., `postgres`) and created the database, connect as that admin user to `sg_bookkeeper` database:
        ```bash
        psql -U postgres -d sg_bookkeeper
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
    -   **Journal Entries**: List, filter, create, edit drafts, view, post, and reverse general journal entries.
-   **Sales Tab**: Create, view, filter, edit draft, and post Sales Invoices.
-   **Purchases Tab**: Create, view, filter, and edit draft Purchase Invoices. (Posting is planned).
-   **Customers Tab**: View, search, filter, add, edit, and toggle active status for customers.
-   **Vendors Tab**: View, search, filter, add, edit, and toggle active status for vendors.
-   **Products & Services Tab**: Manage products and services (Inventory, Non-Inventory, Service types) with list view, filters, add/edit dialog.
-   **Banking Tab**: (Placeholder) For bank account management and reconciliation.
-   **Reports Tab**:
    -   **GST F5 Preparation**: Prepare, view, save draft, and finalize GST F5 returns.
    *   **Financial Statements**: Generate Balance Sheet, Profit & Loss, Trial Balance, or General Ledger. View in structured tables/trees. Export to PDF/Excel with enhanced formatting for BS/P&L and new UI options (comparative periods, zero-balance accounts).
-   **Settings Tab**:
    -   **Company**: Configure company-wide information.
    -   **Fiscal Years**: Manage Fiscal Years and their periods.
    -   **Users**: Manage user accounts (add, edit, toggle active, change password, assign roles).
    *   **Roles & Permissions**: Manage roles (add, edit, delete) and assign system permissions to roles.

Upon first run (after DB initialization), an `admin` user is created with the password `password`. You will be prompted to change this password on first login.

## Project Structure

```
sg_bookkeeper/
├── app/
│   ├── __init__.py
│   ├── main.py                     # Main application entry point (QApplication, asyncio bridge)
│   ├── core/                       # Core components (ApplicationCore, DBManager, Config, Security)
│   ├── common/                     # Common utilities, enums
│   ├── models/                     # SQLAlchemy ORM models (organized by schema: core, accounting, etc.)
│   ├── services/                   # Data access services (repositories)
│   ├── accounting/                 # Business logic managers for accounting module
│   ├── tax/                        # Business logic managers for tax module
│   ├── business_logic/             # Managers for Customers, Vendors, Products, Invoices
│   ├── reporting/                  # Logic managers for generating reports
│   ├── ui/                         # PySide6 UI components (organized by module)
│   │   ├── accounting/
│   │   ├── customers/
│   │   ├── vendors/
│   │   ├── products/
│   │   ├── sales_invoices/
│   │   ├── purchase_invoices/      # UI for Purchase Invoices (widget, dialog, table model)
│   │   ├── reports/
│   │   ├── settings/               # Includes User/Role management UI
│   │   └── ... (other ui modules)
│   ├── utils/                      # General utility functions, Pydantic DTOs, helpers
│   └── resources_rc.py             # Compiled Qt resources (if generated)
├── data/                           # Default data templates (CoA, report templates, tax codes)
├── docs/                           # Project documentation (like this README, TDS)
├── resources/                      # UI assets (icons, images, .qrc file)
├── scripts/                        # Database initialization and utility scripts (db_init.py, schema.sql, initial_data.sql)
├── tests/                          # Automated tests (planned)
├── .gitignore
├── pyproject.toml                  # Poetry configuration for dependencies and project metadata
├── poetry.lock
├── README.md                       # This file
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

### Current Focus / Short-term
-   **Purchase Invoicing**:
    *   Implement posting logic (JE creation) for Purchase Invoices.
-   **Sales Invoicing & Purchase Invoicing**:
    *   Enhance line item entry (e.g., more advanced product search/selection in dialogs).
    *   Handle inventory updates upon posting (for 'Inventory' type products).
-   **Refine Reporting**:
    *   Improve PDF/Excel export formatting for Trial Balance and General Ledger.
    *   Add more filtering options to existing reports (e.g., dimensions, transaction status).

### Medium-term
-   Bank Account management and basic transaction entry UI in Banking module.
-   Payment recording and allocation to Sales and Purchase invoices.
-   Enhance GST F5 report export options (e.g., consider IAF format for IRAS).
-   Implement full audit log viewing capabilities in the UI.

### Long-term
-   Bank Reconciliation features.
-   Advanced reporting and analytics, dashboard KPIs.
-   Inventory Control enhancements (e.g., stock movements, valuation methods like FIFO/Weighted Avg).
-   Multi-company support (major architectural consideration).
-   Cloud synchronization options (optional).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

Here is the **complete and updated `Technical_Design_Specification_Document.md` (as v11.0)**:

```markdown
# Technical Design Specification Document: SG Bookkeeper (v11.0)

**Version:** 11.0
**Date:** 2025-05-30

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version 11.0, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities. This version details the implementation of **Draft Purchase Invoice Management (Backend Logic and UI - List View & Dialog)** and **Enhanced PDF/Excel Export Formatting for Balance Sheet & Profit/Loss Reports**. These build upon previously documented features like full Sales Invoicing, User/Role Management, Customer/Vendor/Product Management, GST F5 workflow, and Financial Reporting UI options. This document serves as a comprehensive guide for ongoing development, feature enhancement, testing, and maintenance.

### 1.2 Scope
This TDS covers the following aspects of the SG Bookkeeper application:
-   System Architecture: UI, business logic, data access layers, and asynchronous processing.
-   Database Schema: Details and organization as defined in `scripts/schema.sql`.
-   Key UI Implementation Patterns: `PySide6` interactions with the asynchronous backend, DTO usage.
-   Core Business Logic: Component structures and interactions for implemented modules.
-   Data Models (SQLAlchemy ORM) and Data Transfer Objects (Pydantic DTOs).
-   Security Implementation: Authentication, Role-Based Access Control (RBAC), and audit mechanisms.
-   Deployment and Initialization procedures.
-   Current Implementation Status: Highlighting the features implemented up to this version.

### 1.3 Intended Audience
-   Software Developers: For implementation, feature development, and understanding system design.
-   QA Engineers: For comprehending system behavior, designing effective test cases, and validation.
-   System Administrators: For deployment strategies, database setup, and maintenance.
-   Technical Project Managers: For project oversight, planning, and resource allocation.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application engineered with Python, utilizing PySide6 for its graphical user interface and PostgreSQL for robust data storage. It is designed to provide comprehensive accounting solutions for Singaporean Small to Medium-sized Businesses (SMBs). Key features include a full double-entry bookkeeping system, Singapore-specific GST management (including F5 return preparation), interactive financial reporting with enhanced export options, modules for managing essential business operations (Customers, Vendors, Products/Services, full Sales Invoicing lifecycle, and Purchase Invoice draft management with list views and dialogs), and comprehensive system administration for Users, Roles, and Permissions. The application emphasizes data integrity, compliance with local accounting standards, and user-friendliness for business owners and accounting professionals. Core data structures are defined in `scripts/schema.sql`, and initial seeding is performed by `scripts/initial_data.sql`.

### 1.5 Current Implementation Status
As of version 11.0, the following key features are implemented:
*   **Core Accounting**: Chart of Accounts (CRUD UI), General Journal (CRUD UI, Posting, Reversal), Fiscal Year/Period Management (UI in Settings).
*   **Tax Management**: GST F5 Return data preparation and finalization (UI and backend logic), `TaxCalculator` for line item tax.
*   **Business Operations**:
    *   Customer Management: Full CRUD and listing UI.
    *   Vendor Management: Full CRUD and listing UI.
    *   Product/Service Management: Full CRUD and listing UI for Inventory, Non-Inventory, and Service types.
    *   Sales Invoicing: Full lifecycle - Draft CRUD, List View, Posting with Journal Entry creation, "Save & Approve" in dialog.
    *   Purchase Invoicing: Full Draft Management - Backend logic for creating/updating drafts, UI Dialog (`PurchaseInvoiceDialog`) for draft CRUD with calculations, and UI List View (`PurchaseInvoicesWidget`) with filtering. Posting logic is a stub.
*   **Reporting**:
    *   Balance Sheet & Profit/Loss: On-screen tree view, enhanced PDF/Excel export (custom formatting, headers, footers), UI options for comparative periods and zero-balance accounts.
    *   Trial Balance & General Ledger: On-screen table view, basic PDF/Excel export.
*   **System Administration**:
    *   Full User and Role Management UI in Settings: User CRUD, password management, role assignment. Role CRUD, permission assignment to roles.
    *   Backend `SecurityManager` supports these operations.
*   **Database**: Schema defined in `scripts/schema.sql` including audit triggers, views, and functions. `db_init.py` script for setup.
*   **Architecture**: Layered architecture with asynchronous processing for UI responsiveness.

## 2. System Architecture

### 2.1 High-Level Architecture
The application follows a layered architecture to promote separation of concerns and maintainability:
```
+-----------------------------------------------------------------+
|                       Presentation Layer                        |
| (PySide6: MainWindow, Module Widgets, Dialogs, TableModels)   |
| Handles User Interaction, Displays Data, Qt Signals/Slots       |
+-----------------------------------------------------------------+
      ^                         | (schedule_task_from_qt for async calls)
      | (UI Events, Data DTOs)  | (Results/Updates via QMetaObject.invokeMethod)
      v                         v
+-----------------------------------------------------------------+
|                     Business Logic Layer                        |
| (ApplicationCore, Managers [e.g., SalesInvoiceManager,         |
|  PurchaseInvoiceManager, SecurityManager, GSTManager, etc.])   |
| Encapsulates Business Rules, Validation, Orchestrates Services  |
+-----------------------------------------------------------------+
      ^                         | (Service Calls, ORM Objects/DTOs)
      | (Service Results)       | (SQLAlchemy Async Operations)
      v                         v
+-----------------------------------------------------------------+
|                       Data Access Layer                         |
| (DatabaseManager, Services [e.g., SalesInvoiceService,         |
|  PurchaseInvoiceService, AccountService], SQLAlchemy Models)   |
| Abstracts Database Interactions, Repository Pattern             |
+-----------------------------------------------------------------+
                                | (Asyncpg DB Driver)
                                v
+-----------------------------------------------------------------+
|                          Database Layer                         |
| (PostgreSQL: Schemas [core, accounting, business, audit],      |
|  Tables, Views, Functions, Triggers defined in schema.sql)      |
+-----------------------------------------------------------------+
```
-   **Presentation Layer**: Manages all user interactions and data display, built with PySide6.
-   **Business Logic Layer**: Contains the application's core rules, validation, and workflow orchestration through managers and `ApplicationCore`.
-   **Data Access Layer**: Abstracts database operations using services (implementing repository pattern) and SQLAlchemy ORM.
-   **Database Layer**: PostgreSQL database storing all application data as per the defined schema.

### 2.2 Component Architecture

#### 2.2.1 Core Components (`app/core/`)
-   **`Application` (`app/main.py`)**: Subclass of `QApplication`. Manages the Qt event loop and bridges to a dedicated `asyncio` event loop running in a separate thread for background tasks. Handles splash screen and initial application setup.
-   **`ApplicationCore` (`app/core/application_core.py`)**: The central orchestrator. Initializes and provides access to all services and managers (e.g., `SecurityManager`, `SalesInvoiceManager`, `PurchaseInvoiceManager`). Manages application startup and shutdown routines.
-   **`ConfigManager` (`app/core/config_manager.py`)**: Loads and manages application settings from `config.ini` located in a platform-specific user configuration directory.
-   **`DatabaseManager` (`app/core/database_manager.py`)**: Manages asynchronous PostgreSQL database connections using SQLAlchemy's async engine and an `asyncpg` connection pool. Handles session creation and management, including setting the `app.current_user_id` session variable for database audit triggers.
-   **`SecurityManager` (`app/core/security_manager.py`)**:
    -   Handles user authentication (password hashing with `bcrypt` and verification).
    -   Manages authorization through a Role-Based Access Control (RBAC) system, checking permissions (`has_permission()`).
    -   Provides backend logic for User, Role, and Permission CRUD operations, directly interacting with ORM models.
    -   Tracks the `current_user` for the application session.
-   **`ModuleManager` (`app/core/module_manager.py`)**: A conceptual component for potential future dynamic loading of large application modules. Currently, modules are statically imported.

#### 2.2.2 Asynchronous Task Management (`app/main.py`)
-   A dedicated Python `threading.Thread` (`_ASYNC_LOOP_THREAD`) runs a persistent `asyncio` event loop (`_ASYNC_LOOP`).
-   The `schedule_task_from_qt(coroutine)` utility function safely schedules coroutines (typically manager or service methods initiated by UI actions) from the main Qt GUI thread onto the dedicated asyncio loop thread using `asyncio.run_coroutine_threadsafe`.
-   UI updates resulting from these asynchronous operations are marshaled back to the Qt main thread using `QMetaObject.invokeMethod` with `Qt.ConnectionType.QueuedConnection`. Data is often serialized (e.g., to JSON) for thread-safe transfer.

#### 2.2.3 Services (Data Access Layer - `app/services/`)
Services implement the repository pattern, abstracting direct ORM query logic for data persistence and retrieval. Key services include:
-   **Core Services (`core_services.py`)**: `SequenceService`, `CompanySettingsService`, `ConfigurationService`.
-   **Accounting Services (`accounting_services.py`, `account_service.py`, etc.)**: `AccountService`, `JournalService`, `FiscalPeriodService`, `FiscalYearService`, `AccountTypeService`, `CurrencyService`, `ExchangeRateService`.
-   **Tax Services (`tax_service.py`)**: `TaxCodeService`, `GSTReturnService`.
-   **Business Services (`business_services.py`)**: `CustomerService`, `VendorService`, `ProductService`, `SalesInvoiceService`, `PurchaseInvoiceService`.

#### 2.2.4 Managers (Business Logic Layer - `app/accounting/`, `app/tax/`, `app/business_logic/`, `app/reporting/`)
Managers encapsulate complex business workflows, validation logic, and coordinate operations between multiple services and DTOs.
-   **Accounting Managers**: `ChartOfAccountsManager`, `JournalEntryManager`, `FiscalPeriodManager`, `CurrencyManager`.
-   **Tax Managers**: `GSTManager`, `TaxCalculator`. (`IncomeTaxManager`, `WithholdingTaxManager` are stubs).
-   **Reporting Managers**: `FinancialStatementGenerator`, `ReportEngine`.
-   **Business Logic Managers**: `CustomerManager`, `VendorManager`, `ProductManager`, `SalesInvoiceManager`, `PurchaseInvoiceManager`.
    -   `SalesInvoiceManager`: Handles full lifecycle for sales invoices including draft CRUD and posting with JE creation.
    -   `PurchaseInvoiceManager`: Handles draft CRUD for purchase invoices, including validation and calculations. Posting logic is a stub.

#### 2.2.5 User Interface (Presentation Layer - `app/ui/`)
-   **`MainWindow` (`app/ui/main_window.py`)**: The main application window, using a `QTabWidget` to host different functional modules. It includes menus, a toolbar, and a status bar.
-   **Module Widgets**: Each tab in `MainWindow` hosts a primary widget for a module:
    *   `DashboardWidget` (stub)
    *   `AccountingWidget` (hosts `ChartOfAccountsWidget`, `JournalEntriesWidget`)
    *   `SalesInvoicesWidget` (list view for sales invoices)
    *   `PurchaseInvoicesWidget` (list view for purchase invoices)
    *   `CustomersWidget`, `VendorsWidget`, `ProductsWidget` (list views for respective entities)
    *   `BankingWidget` (stub)
    *   `ReportsWidget` (UI for GST F5 and Financial Statements)
    *   `SettingsWidget` (hosts sub-tabs for Company Info, Fiscal Years, User Management, Role Management)
-   **Detail Widgets & Dialogs**: Specific screens for data entry, editing, or viewing details (e.g., `AccountDialog`, `SalesInvoiceDialog`, `PurchaseInvoiceDialog`, `UserDialog`, `RoleDialog`). These dialogs typically interact with their respective managers for data operations.
-   **Table Models**: Subclasses of `QAbstractTableModel` (e.g., `SalesInvoiceTableModel`, `PurchaseInvoiceTableModel`) are used to provide data to `QTableView` instances in list views.

### 2.3 Technology Stack
-   **Programming Language**: Python 3.9+ (actively tested up to 3.12).
-   **UI Framework**: PySide6 6.9.0+.
-   **Database**: PostgreSQL 14+.
-   **ORM**: SQLAlchemy 2.0+ (utilizing asynchronous ORM features).
-   **Asynchronous DB Driver**: `asyncpg` for PostgreSQL.
-   **Data Validation (DTOs)**: Pydantic V2 (with `email-validator` for email string validation).
-   **Password Hashing**: `bcrypt`.
-   **Reporting Libraries**: `reportlab` for PDF generation, `openpyxl` for Excel generation.
-   **Dependency Management**: Poetry.
-   **Date/Time Utilities**: `python-dateutil`.

### 2.4 Design Patterns
The application incorporates several design patterns to enhance structure, maintainability, and scalability:
-   **Layered Architecture**: As described in Section 2.1.
-   **Model-View-Controller (MVC) / Model-View-Presenter (MVP)**: Broadly guides the separation of UI (View), data (Model - SQLAlchemy ORM, Pydantic DTOs), and application logic (Controller/Presenter - Managers, UI widget event handlers).
-   **Repository Pattern**: Implemented by Service classes in the Data Access Layer. They provide an abstraction for data access operations, decoupling business logic from direct ORM/database query details.
-   **Data Transfer Object (DTO)**: Pydantic models (`app/utils/pydantic_models.py`) are used for structured data exchange between the UI layer and the Business Logic Layer, providing validation and clear data contracts.
-   **Result Object Pattern**: A custom `Result` class (`app/utils/result.py`) is used by manager and service methods to return operation outcomes, clearly indicating success or failure and providing error messages or a value.
-   **Observer Pattern**: Qt's Signals and Slots mechanism is extensively used for communication between UI components and for handling UI updates in response to asynchronous operations.
-   **Dependency Injection (Conceptual)**: `ApplicationCore` acts as a central point for instantiating and providing services and managers, effectively injecting dependencies into components that require them.
-   **Singleton (Conceptual for `ApplicationCore`)**: `ApplicationCore` is instantiated once and accessed globally within the application context, typical for managing core services.

## 3. Data Architecture

### 3.1 Database Schema Overview
The PostgreSQL database schema is foundational to the application and is meticulously defined in `scripts/schema.sql`. It is organized into four distinct schemas:
-   **`core`**: Contains system-level tables such as `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `company_settings`, `configuration` (for key-value app settings), and `sequences` (for document numbering).
-   **`accounting`**: Houses all core accounting tables, including `accounts`, `account_types`, `fiscal_years`, `fiscal_periods`, `journal_entries`, `journal_entry_lines`, `currencies`, `exchange_rates`, `tax_codes`, `gst_returns`, `budgets`, `budget_details`, `recurring_patterns`, `dimensions`, and `withholding_tax_certificates`.
-   **`business`**: Includes tables for business operational data: `customers`, `vendors`, `products`, `sales_invoices`, `sales_invoice_lines`, `purchase_invoices`, `purchase_invoice_lines`, `inventory_movements`, `bank_accounts`, `bank_transactions`, `payments`, and `payment_allocations`.
-   **`audit`**: Comprises tables for tracking changes: `audit_log` (for action summaries) and `data_change_history` (for field-level changes). These are primarily populated by database triggers defined in `schema.sql`.

The schema enforces data integrity through primary keys, foreign keys, `CHECK` constraints, `UNIQUE` constraints, and `NOT NULL` constraints. Indexes are strategically placed for query performance.

### 3.2 SQLAlchemy ORM Models (`app/models/`)
SQLAlchemy ORM models provide the Python object-oriented interface to the database tables.
-   Models are organized into subdirectories under `app/models/` that mirror the database schema structure (e.g., `app/models/core/user.py`, `app/models/accounting/account.py`).
-   All models inherit from a common `Base` (from `sqlalchemy.orm.declarative_base()`).
-   A `TimestampMixin` provides `created_at` and `updated_at` columns with automatic timestamp management.
-   Most transactional tables include `created_by_user_id` and `updated_by_user_id` fields, linking to `core.users.id`, to support auditability.
-   Relationships between models (e.g., one-to-many, many-to-many) are defined using SQLAlchemy's `relationship()` construct, typically with `back_populates` for bidirectional navigation.
-   The Mapped ORM style (SQLAlchemy 2.0+) with type hints (`Mapped`, `mapped_column`) is used for clearer model definitions.

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
Pydantic models serve as DTOs for validating and structuring data passed between application layers, especially from the UI to managers.
-   Each major entity typically has a set of DTOs:
    *   `BaseData`: Common fields.
    *   `CreateData`: Fields required for creating a new entity, often including `user_id` from a `UserAuditData` mixin.
    *   `UpdateData`: Fields allowed for updating an existing entity, usually including `id` and `user_id`.
    *   `Data` (or entity name): Full representation of an entity, often used for returning detailed data.
    *   `SummaryData`: A slimmed-down version for list views.
-   DTOs include field type validations, constraints (e.g., `min_length`, `max_length`, `ge`, `le`), and custom validators (`@validator`, `@root_validator`) for more complex business rule checks (e.g., password confirmation, conditional field requirements).
-   Enums from `app/common/enums.py` are used for fields with predefined choices (e.g., `ProductTypeEnum`, `InvoiceStatusEnum`).

### 3.4 Data Access Layer Interfaces (Services - `app/services/__init__.py`)
While a generic `IRepository` interface is defined, individual service classes often directly implement the required data access methods for their specific ORM model(s) without strictly adhering to all methods of a generic interface. They provide a clear contract for data operations. Examples:
-   `IAccountRepository`: Defines methods like `get_by_code`, `get_account_tree`.
-   `ISalesInvoiceRepository`: Defines methods like `get_by_invoice_no`, `get_all_summary`.
-   `IPurchaseInvoiceRepository`: Defines methods like `get_by_internal_ref_no`, `get_all_summary`.

## 4. Module and Component Specifications

This section details the specifications for key implemented modules.

### 4.1 Core Accounting Module (`app/accounting/`, `app/ui/accounting/`)
-   **Chart of Accounts**: Allows users to define and manage a hierarchical chart of accounts.
    -   Manager: `ChartOfAccountsManager` (validation, CRUD orchestration).
    -   Service: `AccountService` (DB operations for `Account` model).
    -   UI: `ChartOfAccountsWidget` (tree view), `AccountDialog` (add/edit).
-   **Journal Entries**: Facilitates manual journal entry creation and management.
    -   Manager: `JournalEntryManager` (creation, validation, posting, reversal, recurring entry generation).
    -   Service: `JournalService` (DB operations for `JournalEntry`, `JournalEntryLine`).
    -   UI: `JournalEntriesWidget` (list view), `JournalEntryDialog` (add/edit/view).
-   **Fiscal Period Management**: Allows setup and control of fiscal years and periods.
    -   Manager: `FiscalPeriodManager` (creation of years and auto-generation of monthly/quarterly periods, closing/reopening).
    -   Services: `FiscalYearService`, `FiscalPeriodService`.
    -   UI: Integrated into `SettingsWidget`. `FiscalYearDialog` for adding new fiscal years.

### 4.2 Tax Management Module (`app/tax/`, `app/ui/reports/`)
-   **GST Management**:
    *   Manager: `GSTManager` (prepares `GSTReturnData` DTO from posted JEs, saves draft `GSTReturn` ORM, finalizes return with settlement JE creation via `JournalEntryManager`).
    *   Service: `TaxCodeService`, `GSTReturnService`.
    *   UI: GST F5 preparation section in `ReportsWidget`.
-   **Tax Calculation**:
    *   `TaxCalculator` service: Provides methods (`calculate_line_tax`) to compute tax amounts based on net amount and tax code. Used by invoice managers.

### 4.3 Business Operations Modules (`app/business_logic/`, `app/ui/.../`)
-   **Customer, Vendor, Product/Service Management**: Full CRUD capabilities and list views with filtering.
    -   Managers: `CustomerManager`, `VendorManager`, `ProductManager`.
    -   Services: `CustomerService`, `VendorService`, `ProductService`.
    -   UI: `CustomersWidget`, `VendorsWidget`, `ProductsWidget`, and respective dialogs.
-   **Sales Invoicing Module**: Supports the full sales invoice lifecycle.
    -   Manager: `SalesInvoiceManager` (validates data, calculates totals using `TaxCalculator`, creates/updates drafts via `SalesInvoiceService`, posts invoices including JE creation via `JournalEntryManager`).
    -   Service: `SalesInvoiceService`.
    -   UI: `SalesInvoicesWidget` (list view), `SalesInvoiceDialog` (add/edit draft, save & approve for posting).
-   **Purchase Invoicing Module**: Supports draft management for purchase invoices.
    -   Manager: `PurchaseInvoiceManager` (validates data including duplicate vendor invoice number check, calculates totals using `TaxCalculator`, creates/updates drafts via `PurchaseInvoiceService`. Posting is a stub).
    -   Service: `PurchaseInvoiceService`.
    -   UI: `PurchaseInvoicesWidget` (list view), `PurchaseInvoiceDialog` (add/edit draft).

### 4.4 System Administration Modules (`app/core/security_manager.py`, `app/ui/settings/`)
-   **User Management**: Allows administrators to manage user accounts.
    -   Manager: `SecurityManager` handles backend logic.
    -   UI: `UserManagementWidget` and `UserDialog` (for details & role assignment), `UserPasswordDialog`.
-   **Role & Permission Management**: Enables administrators to define roles and assign permissions.
    -   Manager: `SecurityManager` handles backend logic.
    -   UI: `RoleManagementWidget` and `RoleDialog` (for role details & permission assignment via a multi-select list).

### 4.5 Reporting Module (`app/reporting/`, `app/ui/reports/`)
-   **Financial Statements**: Generation and export of key financial reports.
    -   Manager: `FinancialStatementGenerator` (prepares data for BS, P&L, TB, GL). `ReportEngine` (handles PDF/Excel export with enhanced formatting for BS/P&L).
    -   UI: Financial Statements tab in `ReportsWidget` with various options and display views.

## 5. User Interface Implementation (`app/ui/`)

-   **Main Window (`MainWindow`)**: Serves as the primary application container with a tabbed interface for accessing different modules.
-   **Module Widgets**: Each major functional area (e.g., Sales, Purchases, Reports, Settings) has a dedicated widget hosted in a tab. These widgets typically contain toolbars, filter areas, and data display areas (often `QTableView` or `QTreeView`).
-   **Dialogs**: Used for creating new records or editing existing ones (e.g., `SalesInvoiceDialog`, `AccountDialog`). They feature forms for data input and interact with managers for data persistence.
-   **Table Models**: Custom `QAbstractTableModel` subclasses are used to feed data into `QTableView`s, providing flexibility in data display and formatting.
-   **Asynchronous Interaction**: UI elements initiate backend operations (manager calls) via `schedule_task_from_qt`. Callbacks or `QMetaObject.invokeMethod` are used to update the UI with results from these async tasks, ensuring the UI remains responsive.
-   **Data Validation**: Input validation is primarily handled by Pydantic DTOs (on data collection from UI) and then by manager classes before database operations. UI provides immediate feedback for some simple validation errors.
-   **Resource Management**: Icons and images are loaded from `resources/` directory, preferentially using a compiled Qt resource file (`app/resources_rc.py`) if available.

## 6. Security Considerations
-   **Authentication**: User login is handled by `SecurityManager` using `bcrypt` for password hashing. Failed login attempts are tracked, and accounts can be locked.
-   **Authorization (RBAC)**: A granular permission system is in place. Permissions are defined and can be assigned to roles. Users are assigned roles. `SecurityManager.has_permission()` is used to check if the current user is authorized to perform an action. The "Administrator" role has all permissions by default and is protected.
-   **Audit Trails**: Comprehensive audit logging is implemented at the database level using triggers. The `DatabaseManager` sets a session variable `app.current_user_id` which is captured by these triggers to record who made the changes. Audit data is stored in `audit.audit_log` and `audit.data_change_history`.
-   **Data Integrity**: Enforced through database constraints, DTO validation, and business logic validation in managers.

## 7. Database Access Implementation
-   **`DatabaseManager`**: Manages the SQLAlchemy async engine and `asyncpg` connection pool. It is responsible for providing database sessions.
-   **Services (Repository Pattern)**: Service classes (e.g., `AccountService`, `SalesInvoiceService`) encapsulate data access logic for specific ORM models. They use SQLAlchemy's async session to perform CRUD operations and execute queries. Common methods include `get_by_id`, `get_all_summary`, `save`.
-   **ORM Models (`app/models/`)**: SQLAlchemy model classes define the mapping between Python objects and database tables. Relationships, constraints, and mixins (`TimestampMixin`) are defined here.
-   **Transactions**: Database operations that involve multiple steps (e.g., saving an invoice and its lines, posting an invoice and creating a JE) are typically handled within a single database session managed by `async with db_manager.session():`, ensuring atomicity. Manager methods often orchestrate these transactional units.

## 8. Deployment and Installation
-   **Prerequisites**: Python 3.9+, PostgreSQL 14+, Poetry.
-   **Setup**:
    1.  Clone repository.
    2.  Install dependencies using `poetry install`.
    3.  Configure database connection in `config.ini` (located in a platform-specific user config directory).
    4.  Initialize the database using `poetry run sg_bookkeeper_db_init --user <pg_admin_user> ...`. This script executes `scripts/schema.sql` (DDL) and `scripts/initial_data.sql` (seeding).
-   **Execution**: Run `poetry run sg_bookkeeper`.
-   Refer to `README.md` and `deployment_guide.md` for more detailed installation and setup instructions.

## 9. Conclusion
SG Bookkeeper version 11.0 represents a significant step towards a feature-complete accounting application for Singaporean SMBs. The implementation of draft Purchase Invoice management (including a list view UI and a fully functional dialog for CRUD operations) and enhanced financial report exports (Balance Sheet, Profit & Loss) are key advancements. These build upon a solid foundation of core accounting, comprehensive business entity management, full sales invoicing capabilities, and robust user/role administration. The architecture remains scalable and maintainable, leveraging asynchronous operations for a responsive user experience. The next major steps will likely focus on completing the Purchase Invoicing module by implementing posting logic, further enhancing reporting capabilities for other statement types, and potentially beginning work on other transactional modules like Payments or Banking.
```

**Summary of Document Generation:**

*   **`README.md`**:
    *   I've synthesized the strongest parts from the various README versions to create a comprehensive overview.
    *   The "Key Features" section is updated to reflect the status of each module as per TDS v11 (e.g., Purchase Invoicing is now "UI Implemented" for drafts).
    *   The "Usage Guide" now mentions the "Purchases" tab.
    *   The "Project Structure" includes `app/ui/purchase_invoices/`.
    *   The "Roadmap" reflects that Purchase Invoice draft UI is done and posting is next.
    *   Installation and Tech Stack sections are based on the latest, most accurate information.

*   **`Technical_Design_Specification_Document.md` (v11.0)**:
    *   This document is primarily based on the user-provided TDS v11 structure, which was already quite current.
    *   I've ensured all section introductions (Purpose, Scope, Overview, Current Implementation Status) clearly reflect the state after the implementation of Purchase Invoice Drafts and Enhanced Reporting Exports.
    *   Component descriptions for `PurchaseInvoiceManager`, `PurchaseInvoiceService`, `PurchaseInvoicesWidget`, `PurchaseInvoiceDialog`, and `ReportEngine` have been updated/confirmed to match their current capabilities as per TDS v11.
    *   References to older versions have been removed.
    *   The document aims to be a complete, standalone reference for the current project architecture and design.
    *   I've incorporated general architectural principles (like the layered diagram, asynchronous processing model, DTO usage, Result pattern) that were well-established in earlier TDS versions and remain fundamental, ensuring they are clearly presented in this consolidated version.

Both documents are now self-contained and should provide a complete and accurate picture of the SG Bookkeeper project at its current stage.
