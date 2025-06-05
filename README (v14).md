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
-   Poetry
-   Git

### Developer Installation Steps
1.  **Clone Repository**: `git clone https://github.com/yourusername/sg_bookkeeper.git && cd sg_bookkeeper`
2.  **Install Dependencies**: `poetry install --with dev`
3.  **Prepare PostgreSQL**: Ensure a user (e.g., `sgbookkeeper_user`) and a database (e.g., `sg_bookkeeper`) are created. The user specified in `config.ini` needs appropriate permissions.
4.  **Configure `config.ini`**:
    *   Locate/create at:
        *   Linux: `~/.config/SGBookkeeper/config.ini`
        *   macOS: `~/Library/Application Support/SGBookkeeper/config.ini`
        *   Windows: `%APPDATA%\SGBookkeeper\config.ini`
    *   Set database credentials (username, password, host, port, database name). Example:
        ```ini
        [Database]
        username = sgbookkeeper_user
        password = YourSecurePassword123!
        host = localhost
        port = 5432
        database = sg_bookkeeper
        ; ... other DB settings ...
        [Application]
        ; ... app settings ...
        ```
5.  **Initialize Database**: Run `poetry run sg_bookkeeper_db_init --user YOUR_POSTGRES_ADMIN_USER ...`. This uses `scripts/schema.sql` (ensure it's v1.0.5) and `scripts/initial_data.sql`. Use `--drop-existing` with caution.
6.  **Compile Qt Resources**: `poetry run pyside6-rcc resources/resources.qrc -o app/resources_rc.py`
7.  **Run Application**: `poetry run sg_bookkeeper` (Default admin: `admin`/`password` - change on first login)

## Usage Guide
*(Updated to reflect Bank Reconciliation draft persistence and new Dashboard KPIs)*
-   **Dashboard Tab**: View key financial indicators including YTD Revenue, Expenses, Net Profit; Current Cash Balance; Total Outstanding & Overdue AR/AP; AR & AP Aging summaries (Current, 1-30, 31-60, 61-90, 91+ days); and Current Ratio.
-   **Banking C.R.U.D Tab**: Manage Bank Accounts. View/add manual transactions. Import bank statements via CSV.
-   **Bank Reconciliation Tab**: Perform bank reconciliations. Select an account, set statement details. A "Draft" reconciliation is created/loaded. Load unreconciled statement items and system transactions. "Match Selected" items to provisionally reconcile them against the current draft (these are persisted). "Unmatch Selected" to revert provisional matches. Create adjustment JEs for statement-only items. When balanced, "Save Final Reconciliation" to finalize. View history of finalized reconciliations and their details.
-   Other modules function as previously detailed, providing comprehensive tools for accounting, sales, purchases, payments, master data management, reporting, and system settings.

## Project Structure
```
sg_bookkeeper/
├── app/                          # Main application source code
│   ├── __init__.py
│   ├── main.py                     # Main application entry point
│   ├── core/                       # Core components
│   ├── common/                     # Common enums, etc.
│   ├── models/                     # SQLAlchemy ORM models (by schema)
│   ├── services/                   # Data access layer services
│   ├── accounting/                 # Business logic for accounting
│   ├── business_logic/             # Business logic for ops (customers, vendors, etc.)
│   ├── reporting/                  # Business logic for reports & dashboard
│   ├── tax/                        # Business logic for tax
│   ├── ui/                         # PySide6 UI components (by module)
│   └── utils/                      # Utilities (DTOs, helpers)
├── data/                         # Default data templates (CoA, report templates)
├── docs/                         # Project documentation
├── resources/                    # UI assets (icons, images, .qrc)
├── scripts/                      # Database scripts (schema, initial_data, db_init.py)
├── tests/                        # Automated tests
│   ├── conftest.py
│   ├── __init__.py
│   ├── unit/                     # Unit tests
│   │   ├── __init__.py
│   │   ├── reporting/            # Tests for reporting logic (e.g., DashboardManager)
│   │   ├── services/             # Tests for service layer components
│   │   ├── tax/                  # Tests for tax logic
│   │   └── utils/                # Tests for utilities
│   ├── integration/              # Integration tests (planned)
│   └── ui/                       # UI tests (planned)
├── .gitignore
├── pyproject.toml                # Poetry configuration
├── poetry.lock
├── README.md                     # This file
└── LICENSE
```

## Database Schema
The PostgreSQL database schema is at version **1.0.5**. It includes tables for core system functions, detailed accounting, business operations, and comprehensive audit trails. Key recent additions include the `business.bank_reconciliations` table with a `status` column ('Draft', 'Finalized') and related fields in `bank_accounts` and `bank_transactions` to support the full bank reconciliation workflow, including draft persistence. A trigger `update_bank_account_balance_trigger_func` ensures `bank_accounts.current_balance` is automatically updated. See `scripts/schema.sql` for full details.

## Testing
Automated tests are implemented using Pytest to ensure code quality and prevent regressions.
-   **Unit Tests**: Located in `tests/unit/`, these verify individual components by mocking dependencies. Current unit tests cover:
    *   `TaxCalculator` (`tests/unit/tax/test_tax_calculator.py`)
    *   Pydantic DTO validators for `JournalEntryData` and `JournalEntryLineData` (`tests/unit/utils/test_pydantic_models_journal_entry.py`)
    *   `SequenceGenerator` (`tests/unit/utils/test_sequence_generator.py`)
    *   Core Services: `AccountTypeService`, `CompanySettingsService`, `ConfigurationService`, `CurrencyService`, `DimensionService`, `ExchangeRateService`, `FiscalPeriodService`, `FiscalYearService`, `SequenceService` (various files in `tests/unit/services/`).
    *   Business Service: `BankReconciliationService` (`tests/unit/services/test_bank_reconciliation_service.py`).
    *   Reporting Logic: `DashboardManager` including `_get_total_cash_balance` and `get_dashboard_kpis` (in `tests/unit/reporting/test_dashboard_manager.py`).
    *   Service methods used by Dashboard: AR/AP Aging in `CustomerService`/`VendorService`, and `AccountService.get_total_balance_by_account_category_and_type_pattern`.
-   **Running Tests**: Use `poetry run pytest`. For coverage: `poetry run pytest --cov=app`.

## Contributing
Contributions are welcome! Please fork the repository, create a feature branch, make your changes (including tests), ensure all checks pass, and then submit a Pull Request.

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
-   **Automated Testing (Phase 1 - Dashboard Logic)**: Unit tests for `DashboardManager` methods and dependent service logic for new KPIs.

### Current Focus / Next Steps
-   **Automated Testing (Continued - CRITICAL)**:
    *   Expand unit test coverage to all remaining services (especially business services like `SalesInvoiceService`, `PaymentService`, remaining `BankAccountService`/`BankTransactionService` methods) and all managers.
    *   Begin setup and implementation of integration tests for core workflows (e.g., invoice posting, payment allocation, full bank reconciliation cycle).
-   **Refine Bank Reconciliation**:
    *   Implement UI and logic for handling complex matches (e.g., one-to-many, many-to-one statement lines to system transactions).
    *   UI improvements for visually linking matched items within the "Provisionally Matched" tables or a dedicated view.
    *   More robust error handling and user feedback during CSV import (e.g., detailed row-level error reporting).
-   **Enhance Dashboard KPIs (Phase 2)**:
    *   Add more financial ratios (e.g., Quick Ratio, Debt-to-Equity).
    *   Investigate and implement simple graphical representations for key KPIs.
    *   Allow user customization or period selection for dashboard information.

### Long-term
-   Advanced reporting and analytics.
-   Inventory Control enhancements (stocktakes, multiple locations).
-   Multi-company support.
-   Enhanced Tax Compliance features.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
