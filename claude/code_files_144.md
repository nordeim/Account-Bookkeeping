Okay, I will generate the complete, updated replacement files for `README.md` and `Technical_Design_Specification_Document.md`. These will consolidate information from the previous versions you provided and reflect the current state of the codebase as per my review of `project_codebase_files_set-1.md` through `project_codebase_files_set-5.md`.

## Updated `README.md`

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

SG Bookkeeper is a comprehensive, cross-platform desktop application designed to meet the accounting and bookkeeping needs of small to medium-sized businesses in Singapore. Built with Python and leveraging the power of PySide6 for a modern user interface and PostgreSQL for robust data management, it offers professional-grade financial tools tailored to Singapore's regulatory environment.

The application features a double-entry accounting core, GST management, financial reporting, and modules for essential business operations including customer, vendor, and product/service management. Its goal is to provide an intuitive, powerful, and compliant solution that empowers business owners and accountants.

### Why SG Bookkeeper?

-   **Singapore-Centric**: Designed with Singapore Financial Reporting Standards (SFRS), GST regulations (including 9% rate), and IRAS compliance considerations at its core.
-   **Professional Grade**: Implements a full double-entry system, detailed audit trails (via database triggers), and robust data validation using Pydantic DTOs.
-   **User-Friendly Interface**: Aims for an intuitive experience for users who may not be accounting experts, while providing depth for professionals. Core accounting, customer/vendor/product management, reporting UI, and initial Sales Invoicing dialog are functional.
-   **Open Source & Local First**: Transparent development. Your financial data stays on your local machine or private server, ensuring privacy and control. No subscription fees.
-   **Modern & Performant**: Utilizes asynchronous operations for a responsive UI and efficient database interactions, with a dedicated asyncio event loop.

## Key Features

*(Status: Implemented, Backend Implemented, UI Dialog Implemented, Foundational (DB/Models ready), Planned)*

### Core Accounting
-   **Comprehensive Double-Entry Bookkeeping** (Implemented)
-   **Customizable Hierarchical Chart of Accounts** (Implemented - UI for CRUD)
-   **General Ledger with detailed transaction history** (Implemented - Report generation, on-screen view, export)
-   **Journal Entry System** (Implemented - UI for General Journal; transaction-specific JEs via respective modules are planned for posting stage)
-   **Multi-Currency Support** (Foundational - Models, CurrencyManager exist. UI integration in transactions pending.)
-   **Fiscal Year and Period Management** (Implemented - UI in Settings for FY creation and period auto-generation; period closing/reopening logic in manager.)
-   **Budgeting and Variance Analysis** (Foundational - Models exist. UI/Logic planned.)

### Singapore Tax Compliance
-   **GST Tracking and Calculation** (Backend Implemented - `TaxCode` setup, `TaxCalculator` for line items. Full JE line item tax application in Sales Invoicing Dialog in progress.)
-   **GST F5 Return Data Preparation & Finalization** (Implemented - Backend for data prep & finalization with JE settlement. UI in Reports tab for prep, view, draft save, and finalize.)
-   **Income Tax Estimation Aids** (Planned - `IncomeTaxManager` stub exists.)
-   **Withholding Tax Management** (Foundational - Models and `WithholdingTaxManager` stub exist.)

### Business Operations
-   **Customer Management** (Implemented - List, Add, Edit, Toggle Active status, with search/filter.)
-   **Vendor Management** (Implemented - List, Add, Edit, Toggle Active status, with search/filter.)
-   **Product and Service Management** (Implemented - List, Add, Edit, Toggle Active status for Products & Services, with search/filter by type.)
-   **Sales Invoicing and Accounts Receivable** (Backend Implemented for draft management, UI Dialog Implemented - CRUD for draft invoices, line item calculations, tax. Posting and full AR cycle Planned.)
-   **Purchase Invoicing and Accounts Payable** (Foundational - Models exist. UI/Logic planned.)
-   **Payment Processing and Allocation** (Foundational - Models exist. UI/Logic planned.)
-   **Bank Account Management and Reconciliation Tools** (Foundational - Models exist. UI is a stub.)
-   **Basic Inventory Control** (Foundational - Models exist; `Product` model includes inventory-specific fields. Logic planned.)

### Reporting & Analytics
-   **Standard Financial Statements**: Balance Sheet, Profit & Loss, Trial Balance, General Ledger (Implemented - UI in Reports tab for selection, on-screen view via native Qt views, and PDF/Excel export.)
-   **Cash Flow Statement** (Planned)
-   **GST Reports** (Implemented - See GST F5 above. Formatted GST reports planned.)
-   **Customizable Reporting Engine** (Planned - Current `ReportEngine` is basic.)
-   **Dashboard with Key Performance Indicators (KPIs)** (Planned - UI is a stub.)

### System & Security
-   **User Authentication with Role-Based Access Control (RBAC)** (Implemented)
-   **Granular Permissions System** (Foundational)
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

The application provides a range of functional modules accessible via tabs:

-   **Accounting Tab**:
    -   **Chart of Accounts**: View, add, edit, and (de)activate accounts.
    -   **Journal Entries**: List, filter, create, edit drafts, view, post, and reverse general journal entries.
-   **Customers Tab**:
    -   View, search, filter, add, edit, and toggle active status for customers.
-   **Vendors Tab**:
    -   View, search, filter, add, edit, and toggle active status for vendors.
-   **Products & Services Tab**:
    -   View a list of products and services.
    -   Filter by product type (Inventory, Service, Non-Inventory), active status, or search term.
    -   Add new items and edit existing ones using a comprehensive dialog that adapts to product type.
    -   Toggle the active/inactive status of products/services.
-   **Reports Tab**:
    -   **GST F5 Preparation**: Prepare, view, save draft, and finalize GST F5 returns.
    *   **Financial Statements**: Generate Balance Sheet, P&L, Trial Balance, or General Ledger. View in structured tables/trees and export to PDF/Excel.
-   **Settings Tab**:
    -   Configure Company Information and manage Fiscal Years.

Other modules (Sales Invoicing List View, Dashboard, Banking) are currently placeholders or under active development.
The default `admin` user (password: `password` - change on first login) has full access.

## Project Structure

```
sg_bookkeeper/
├── app/                    # Application source code
│   ├── __init__.py
│   ├── main.py             # Main application entry point (QApplication, asyncio bridge)
│   ├── core/               # Core components (ApplicationCore, DBManager, Config, Security)
│   ├── common/             # Common utilities, enums
│   ├── models/             # SQLAlchemy ORM models (organized by schema)
│   ├── services/           # Data access services (repositories)
│   ├── accounting/         # Business logic managers for accounting module
│   ├── tax/                # Business logic managers for tax module
│   ├── business_logic/     # Managers for Customers, Vendors, Products, SalesInvoices
│   ├── reporting/          # Logic managers for generating reports
│   ├── ui/                 # PySide6 UI components (organized by module)
│   │   ├── customers/
│   │   ├── vendors/
│   │   ├── products/
│   │   ├── sales_invoices/ # Contains SalesInvoiceDialog, SalesInvoiceTableModel
│   │   └── ... (other ui modules)
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
-   **Sales Invoicing**: Complete UI for listing, viewing, and managing Sales Invoices. Implement posting logic (JE creation).
-   **User and Role Management UI**: Add UI in Settings for managing users, roles, and permissions.
-   **Refine Reporting**: Enhance on-screen display and export options for financial reports.

### Medium-term
-   Basic Purchase Invoicing workflows (similar to Sales Invoicing).
-   Bank Account management and basic transaction entry UI in Banking module.
-   Enhance GST F5 report export options (e.g., consider IAF format).

### Long-term
-   Bank Reconciliation features.
-   Advanced reporting and analytics, dashboard KPIs.
-   Inventory Control enhancements (e.g., stock movements, valuation).
-   Multi-company support.
-   Cloud synchronization options (optional).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

## Updated `Technical_Design_Specification_Document.md` (as v8.0)

```markdown
# Technical Design Specification Document: SG Bookkeeper (v8)

**Version:** 8.0
**Date:** 2025-05-28 <!-- Or current date -->

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version 8, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities. This version specifically details the backend logic and initial UI dialog for **Sales Invoicing (Draft Management)**, alongside previously documented features like Customer, Vendor, Product/Service Management, GST F5 workflow, and Financial Reporting. This document serves as a comprehensive guide for ongoing development, feature enhancement, testing, and maintenance.

### 1.2 Scope
This TDS covers the following aspects of the SG Bookkeeper application:
-   System Architecture: UI, business logic, data access layers, and asynchronous processing.
-   Database Schema: Alignment with `scripts/schema.sql`.
-   Key UI Implementation Patterns: `PySide6` interactions with the asynchronous backend.
-   Core Business Logic: Component structures, including those for Customer, Vendor, Product/Service, and Sales Invoice management.
-   Data Models (SQLAlchemy ORM) and Data Transfer Objects (Pydantic DTOs).
-   Security Implementation: Authentication, authorization, and audit mechanisms.
-   Deployment and Initialization procedures.
-   Current Implementation Status: Highlighting implemented features such as Settings, CoA, Journal Entries, GST workflow, Financial Reports, Customer/Vendor/Product Management, and Sales Invoicing (backend logic and initial dialog).

### 1.3 Intended Audience
(Remains the same as TDS v7)
-   Software Developers, QA Engineers, System Administrators, Technical Project Managers.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application engineered with Python, utilizing PySide6 for its graphical user interface and PostgreSQL for robust data storage. It provides comprehensive accounting for Singaporean SMBs, including double-entry bookkeeping, GST management, interactive financial reporting, and foundational modules for business operations such as Customer, Vendor, Product/Service management, and initial Sales Invoicing capabilities (allowing creation and update of draft invoices). The application emphasizes data integrity, compliance, and user-friendliness. Data structures are defined in `scripts/schema.sql` and seeded by `scripts/initial_data.sql`.

## 2. System Architecture

### 2.1 High-Level Architecture
(Diagram and core description remain the same as TDS v7)

### 2.2 Component Architecture

#### 2.2.1 Core Components (`app/core/`)
(Descriptions remain largely the same as TDS v7. `ApplicationCore` now also instantiates and provides access to `SalesInvoiceService` and `SalesInvoiceManager`.)

#### 2.2.2 Asynchronous Task Management (`app/main.py`)
(Description remains the same as TDS v7)

#### 2.2.3 Services (`app/services/`)
-   **Accounting & Core Services** (as listed in TDS v7).
-   **Tax Services** (as listed in TDS v7).
-   **Business Services (`app/services/business_services.py`)**:
    -   `CustomerService`: Manages `Customer` entity data access.
    -   `VendorService`: Manages `Vendor` entity data access.
    -   `ProductService`: Manages `Product` entity data access.
    -   **`SalesInvoiceService` (New)**: Implements `ISalesInvoiceRepository`. Responsible for CRUD operations on `SalesInvoice` and `SalesInvoiceLine` entities, fetching invoice summaries (with filtering and pagination), and specific lookups (e.g., by invoice number).

#### 2.2.4 Managers (Business Logic) (`app/accounting/`, `app/tax/`, `app/business_logic/`)
-   **Accounting, Tax, Reporting Managers** (as listed in TDS v7).
-   **Business Logic Managers (`app/business_logic/`)**:
    -   `CustomerManager`: Orchestrates customer lifecycle operations.
    -   `VendorManager`: Orchestrates vendor lifecycle operations.
    -   `ProductManager`: Orchestrates product/service lifecycle operations.
    -   **`SalesInvoiceManager` (New details - `app/business_logic/sales_invoice_manager.py`)**: Orchestrates sales invoice lifecycle operations, particularly for draft invoices. Handles validation of invoice data (customer, products, tax codes), calculation of line item totals and tax (using `TaxCalculator`), overall invoice totals (subtotal, tax, grand total), mapping DTOs to ORM models, interaction with `SalesInvoiceService` for persistence, and generation of invoice numbers using `SequenceService` (via DB function). Posting logic (JE creation) is a placeholder.

#### 2.2.5 User Interface (`app/ui/`)
-   **`MainWindow` (`app/ui/main_window.py`)**: Includes "Products & Services" tab. A "Sales" or "Invoicing" tab is conceptually planned but the main list widget might be a stub.
-   **Module Widgets**:
    -   `AccountingWidget`, `SettingsWidget`, `ReportsWidget`, `CustomersWidget`, `VendorsWidget`, `ProductsWidget` (Functional as per TDS v7).
    -   `DashboardWidget`, `BankingWidget` (Remain stubs).
    -   **`SalesInvoicesWidget` (Planned/Stub - `app/ui/sales_invoices/sales_invoices_widget.py`)**: Intended to provide a list view for sales invoices. Currently, a dialog for creating/editing is the primary UI.
-   **Detail Widgets & Dialogs**:
    -   `AccountDialog`, `JournalEntryDialog`, `FiscalYearDialog`, `CustomerDialog`, `VendorDialog`, `ProductDialog` (as in TDS v7).
    -   **`SalesInvoiceTableModel` (New - `app/ui/sales_invoices/sales_invoice_table_model.py`)**: `QAbstractTableModel` subclass for displaying `SalesInvoiceSummaryData`.
    -   **`SalesInvoiceDialog` (New details - `app/ui/sales_invoices/sales_invoice_dialog.py`)**: `QDialog` for creating and editing draft sales invoice details. Includes fields for header information (customer, dates, currency) and a `QTableWidget` for line items (product, description, quantity, price, discount, tax code). Dynamically calculates line totals and invoice totals. Interacts with `SalesInvoiceManager` for saving drafts. Asynchronously populates `QComboBox`es for customers, products, currencies, and tax codes.

### 2.3 Technology Stack
(Same as TDS v7)

### 2.4 Design Patterns
(Same as TDS v7. New Sales Invoice module follows established patterns.)

## 3. Data Architecture

### 3.1 Database Schema Overview
(Remains consistent. `business.sales_invoices` and `business.sales_invoice_lines` tables are now actively used.)

### 3.2 SQLAlchemy ORM Models (`app/models/`)
(`app/models/business/sales_invoice.py` is now actively used.)

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
DTOs for `SalesInvoice` Management have been added and are actively used:
-   `SalesInvoiceLineBaseData`: Common fields for invoice lines.
-   `SalesInvoiceBaseData`: Common fields for invoice header.
-   `SalesInvoiceCreateData(SalesInvoiceBaseData, UserAuditData)`: For creating new invoices.
-   `SalesInvoiceUpdateData(SalesInvoiceBaseData, UserAuditData)`: For updating existing invoices.
-   `SalesInvoiceData`: Full representation of an invoice, including calculated totals and status.
-   `SalesInvoiceSummaryData`: Slim DTO for list views.
-   `TaxCalculationResultData` is used by `SalesInvoiceManager` via `TaxCalculator`.

### 3.4 Data Access Layer Interfaces (`app/services/__init__.py`)
The following interface has been added:
-   **`ISalesInvoiceRepository(IRepository[SalesInvoice, int])`**:
    ```python
    from app.models.business.sales_invoice import SalesInvoice
    from app.utils.pydantic_models import SalesInvoiceSummaryData
    from app.common.enums import InvoiceStatusEnum
    from datetime import date

    class ISalesInvoiceRepository(IRepository[SalesInvoice, int]):
        @abstractmethod
        async def get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]: pass
        
        @abstractmethod
        async def get_all_summary(self, 
                                  customer_id: Optional[int] = None,
                                  status: Optional[InvoiceStatusEnum] = None, 
                                  start_date: Optional[date] = None, 
                                  end_date: Optional[date] = None,
                                  page: int = 1, 
                                  page_size: int = 50
                                 ) -> List[SalesInvoiceSummaryData]: pass
    ```

## 4. Module and Component Specifications

### 4.1 - 4.3 Core Accounting, Tax, Reporting Modules
(Functionality as detailed in TDS v7 remains current.)

### 4.4 Business Operations Modules

#### 4.4.1 Customer Management Module 
(As detailed in TDS v7)

#### 4.4.2 Vendor Management Module
(As detailed in TDS v7)

#### 4.4.3 Product/Service Management Module
(As detailed in TDS v7)

#### 4.4.4 Sales Invoicing Module (Backend and Initial Dialog Implemented)
This module provides capabilities for creating and managing draft sales invoices.
-   **Service (`app/services/business_services.py`)**:
    -   **`SalesInvoiceService`**: Implements `ISalesInvoiceRepository`.
        -   `get_by_id()`: Fetches a `SalesInvoice` ORM, eager-loading lines (with product, tax_code_obj), customer, currency, and audit users.
        -   `get_all_summary()`: Fetches `List[SalesInvoiceSummaryData]` with filtering and pagination.
        -   `save()`: Persists `SalesInvoice` ORM objects, handling cascaded line items.
-   **Manager (`app/business_logic/sales_invoice_manager.py`)**:
    -   **`SalesInvoiceManager`**:
        -   Dependencies: `SalesInvoiceService`, `CustomerService`, `ProductService`, `TaxCodeService`, `TaxCalculator`, `SequenceService`, `ApplicationCore`.
        -   `get_invoice_for_dialog()`: Retrieves full `SalesInvoice` ORM for dialogs.
        -   `get_invoices_for_listing()`: Retrieves `List[SalesInvoiceSummaryData]`.
        -   `_validate_and_prepare_invoice_data()`: Core internal method to validate DTOs, fetch related entities (customer, products, tax codes for each line), calculate line subtotals, discounts, tax per line (using `TaxCalculator`), and then aggregate for invoice header totals (subtotal, total tax, grand total).
        -   `create_draft_invoice(dto: SalesInvoiceCreateData)`: Uses `_validate_and_prepare_invoice_data`. Generates `invoice_no` via `core.get_next_sequence_value` DB function. Maps DTO and calculated data to `SalesInvoice` and `SalesInvoiceLine` ORMs. Sets status to `Draft` and audit IDs, then saves.
        -   `update_draft_invoice(invoice_id: int, dto: SalesInvoiceUpdateData)`: Fetches existing draft invoice. Uses `_validate_and_prepare_invoice_data`. Updates ORM fields, handles replacement of line items (transactionally deletes old lines and adds new ones). Sets audit ID and saves.
        -   `post_invoice(invoice_id: int, user_id: int)`: Currently a placeholder; intended to change status to `Approved`/`Sent`, generate accounting journal entries, and potentially update inventory.

## 5. User Interface Implementation (`app/ui/`)

### 5.1 - 5.4 Core UI, Accounting, Settings, Reports, Customers, Vendors, Products Modules
(Functionality as detailed in TDS v7.)

### 5.5 Sales Invoicing Module UI (`app/ui/sales_invoices/`) (New Section)
-   **`SalesInvoicesWidget` (Planned/Stub)**:
    -   The main list view for sales invoices is not yet fully implemented.
-   **`SalesInvoiceTableModel` (`app/ui/sales_invoices/sales_invoice_table_model.py`)**:
    -   `QAbstractTableModel` subclass.
    -   Manages `List[SalesInvoiceSummaryData]`.
    -   Provides data for columns: ID (hidden), Invoice No., Invoice Date, Due Date, Customer Name, Total Amount, Amount Paid, Balance, Status.
-   **`SalesInvoiceDialog` (`app/ui/sales_invoices/sales_invoice_dialog.py`)**:
    *   `QDialog` for creating or editing (draft) sales invoice details.
    *   **Header Fields**: `QComboBox` for Customer (with completer), `QDateEdit` for Invoice Date and Due Date, `QComboBox` for Currency, `QDoubleSpinBox` for Exchange Rate, `QTextEdit` for Notes and Terms. Displays Invoice No. (generated on save).
    *   **Line Items Table (`QTableWidget`)**: Columns for Delete (button), Product/Service (`QComboBox` with completer), Description (`QLineEdit`), Quantity (`QDoubleSpinBox` via delegate), Unit Price (`QDoubleSpinBox` via delegate), Discount % (`QDoubleSpinBox` via delegate), Line Subtotal (read-only), Tax Code (`QComboBox`), Tax Amount (read-only), Line Total (read-only).
    *   **Dynamic UI & Calculations**:
        *   Line subtotals, tax amounts, and line totals are calculated dynamically as quantity, price, discount, or tax code change for a line.
        *   Invoice subtotal, total tax, and grand total are updated in read-only display fields based on line item changes.
    *   **ComboBox Population**: Asynchronously loads active customers, products (filtered for saleable types), currencies, and tax codes into respective `QComboBox`es during dialog initialization.
    *   **Data Handling**:
        -   In edit mode, loads existing draft invoice data via `SalesInvoiceManager.get_invoice_for_dialog()`.
        -   On save (draft), collects UI data into `SalesInvoiceCreateData` or `SalesInvoiceUpdateData` DTOs. Pydantic validation occurs.
        -   Calls `SalesInvoiceManager.create_draft_invoice()` or `SalesInvoiceManager.update_draft_invoice()` asynchronously.
        -   Displays success/error messages and emits `invoice_saved(invoice_id)` signal.
        -   "Save & Approve" button is present but currently disabled, indicating future functionality for posting.

## 6. Security Considerations
(Unchanged from TDS v7)

## 7. Database Access Implementation (`app/services/`)
-   **`business_services.py`**:
    -   `CustomerService`, `VendorService`, `ProductService` (As detailed in TDS v7).
    -   **`SalesInvoiceService` (New details)**: Implements `ISalesInvoiceRepository`.
        -   `get_by_id()`: Fetches `SalesInvoice` ORM, eager-loading `lines` (with their `product` and `tax_code_obj`), `customer`, `currency`, `journal_entry`, and audit users.
        -   `get_all_summary()`: Fetches `List[SalesInvoiceSummaryData]` with filtering (customer, status, dates) and pagination. Joins with `Customer` to include customer name.
        -   `save()`: Persists `SalesInvoice` ORM objects, managing related `SalesInvoiceLine` items (SQLAlchemy handles cascades based on relationship configuration). This method is designed to be called within a transaction managed by the `SalesInvoiceManager` for operations like updates that involve deleting old lines.

## 8. Deployment and Installation
(Unchanged from TDS v7)

## 9. Conclusion
This TDS (v8) documents further progress, notably the addition of backend logic for managing draft Sales Invoices, including complex calculations and data validation. A functional UI dialog for creating and editing these draft invoices has also been implemented. This complements the existing Customer, Vendor, and Product/Service management modules, laying a critical foundation for transactional accounting. Core accounting, GST workflow, and financial reporting functionalities remain robust. Future iterations will focus on completing the Sales Invoicing lifecycle (posting, payment tracking), implementing Purchase Invoicing, and further enhancing other modules.
```
