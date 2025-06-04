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

The application features a double-entry accounting core, GST management, interactive financial reporting, modules for essential business operations (Customer, Vendor, Product/Service Management, Sales & Purchase Invoicing, Payments), Bank Account management with transaction entry, CSV bank statement import, a full Bank Reconciliation module, Dashboard KPIs, and comprehensive User/Role/Permission administration including Audit Logs. Its goal is to provide an intuitive, powerful, and compliant solution that empowers business owners and accountants.

### Why SG Bookkeeper?

-   **Singapore-Centric**: Designed with Singapore Financial Reporting Standards (SFRS), GST regulations (including the 9% rate), and IRAS compliance considerations at its core.
-   **Professional Grade**: Implements a full double-entry system, detailed audit trails (via database triggers and viewable UI), and robust data validation using Pydantic DTOs.
-   **User-Friendly Interface**: Aims for an intuitive experience for users who may not be accounting experts, while providing depth for professionals.
-   **Open Source & Local First**: Transparent development. Your financial data stays on your local machine or private server, ensuring privacy and control. No subscription fees.
-   **Modern & Performant**: Utilizes asynchronous operations for a responsive UI and efficient database interactions.

## Key Features

*(Status: Implemented, UI Implemented, Backend Implemented, Foundational, Planned)*

### Core Accounting
-   **Comprehensive Double-Entry Bookkeeping** (Implemented)
-   **Customizable Hierarchical Chart of Accounts** (Implemented - UI for CRUD)
-   **General Ledger with detailed transaction history** (Implemented - Report generation, on-screen view, export, with dimension filtering options)
-   **Journal Entry System** (Implemented - UI for General Journal; JEs auto-created from source documents and Bank Reconciliation; posting auto-creates BankTransaction if applicable)
-   **Multi-Currency Support** (Foundational)
-   **Fiscal Year and Period Management** (Implemented - UI in Settings)
-   **Budgeting and Variance Analysis** (Foundational)

### Singapore Tax Compliance
-   **GST Tracking and Calculation** (Backend Implemented)
-   **GST F5 Return Data Preparation & Finalization** (Implemented - UI in Reports tab; detailed Excel export)
-   **Income Tax Estimation Aids** (Planned)
-   **Withholding Tax Management** (Foundational)

### Business Operations
-   **Customer Management** (Implemented)
-   **Vendor Management** (Implemented)
-   **Product and Service Management** (Implemented)
-   **Sales Invoicing and Accounts Receivable** (Implemented - Full lifecycle including WAC inventory JE)
-   **Purchase Invoicing and Accounts Payable** (Implemented - Full lifecycle including WAC inventory JE)
-   **Payment Processing and Allocation** (Implemented - UI, allocation, JE posting.)
-   **Inventory Control (Weighted Average Cost)** (Implemented)

### Banking
-   **Bank Account Management** (Implemented - Full CRUD UI, linkage to GL.)
-   **Manual Bank Transaction Entry** (Implemented)
-   **CSV Bank Statement Import** (Implemented - UI dialog for configuration and import.)
-   **Bank Reconciliation Module** (Implemented - UI for matching, adjustment JE creation, saving reconciliation.)

### Reporting & Analytics
-   **Standard Financial Statements**: Balance Sheet, P&L, Trial Balance, General Ledger (Implemented - UI, PDF/Excel export, GL dimension filtering.)
-   **Dashboard KPIs** (Implemented - Initial set: YTD P&L, Cash, AR/AP, Overdue AR/AP.)
-   **Cash Flow Statement** (Planned)
-   **GST Reports** (Implemented - See GST F5.)
-   **Customizable Reporting Engine** (Foundational)

### System & Security
-   **User Authentication & RBAC** (Implemented - UI for Users, Roles, Permissions.)
-   **Comprehensive Audit Trails** (Implemented - DB triggers, UI for viewing logs in Settings.)
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
-   **Testing**: Pytest, pytest-asyncio, pytest-cov, unittest.mock

## Installation
*(This section remains largely the same as response_43, ensure database schema v1.0.4 or later from `scripts/schema.sql` is used during initialization.)*

### Prerequisites
-   Python 3.9 or higher
-   PostgreSQL Server 14 or higher
-   Poetry
-   Git

### Developer Installation Steps
1.  **Clone Repository**
2.  **Install Dependencies**: `poetry install` (or `poetry install --with dev` to include dev dependencies explicitly)
3.  **Prepare PostgreSQL User and Database**
4.  **Configure `config.ini`**
5.  **Initialize Database**: Use `poetry run sg_bookkeeper_db_init ...` with `scripts/schema.sql` (v1.0.4+) and `scripts/initial_data.sql`.
6.  **Grant Privileges** (if needed, see `scripts/initial_data.sql` for grants).
7.  **Compile Qt Resources**: `poetry run pyside6-rcc resources/resources.qrc -o app/resources_rc.py`
8.  **Run Application**: `poetry run sg_bookkeeper` (Default: `admin`/`password`)

## Usage Guide
*(Updated to reflect Bank Reconciliation and Dashboard functionalities more clearly.)*
-   **Dashboard Tab**: View key financial indicators like YTD Revenue, Expenses, Net Profit, Current Cash Balance, Total Outstanding AR/AP, and Total Overdue AR/AP. Use the "Refresh KPIs" button to update.
-   **Banking C.R.U.D Tab**: Manage Bank Accounts and their individual transactions. Import bank statements via CSV.
-   **Bank Reconciliation Tab**: Perform bank reconciliations. Select an account, set statement details, load unreconciled items, match transactions, create adjustment JEs for bank charges/interest, and save the reconciliation when balanced.
-   Other modules (Accounting, Sales, Purchases, Payments, Customers, Vendors, Products, Reports, Settings) function as previously described, with ongoing enhancements.

## Project Structure
*(Minor update to reflect testing structure)*
```
sg_bookkeeper/
├── app/                          # Main application source code
├── data/                         # Default data templates
├── docs/                         # Project documentation
├── resources/                    # UI assets (icons, images)
├── scripts/                      # Database initialization scripts
├── tests/                        # Automated tests
│   ├── conftest.py
│   ├── unit/                     # Unit tests (for tax, utils, services, etc.)
│   ├── integration/              # Integration tests (planned)
│   └── ui_tests/                 # UI tests (planned)
├── .gitignore
├── pyproject.toml                # Poetry configuration
├── poetry.lock
├── README.md                     # This file
└── LICENSE
```

## Database Schema
The PostgreSQL database (schema v1.0.4+) includes tables for core system functions, detailed accounting, business operations, and comprehensive audit trails. Key recent additions include the `business.bank_reconciliations` table and related fields in `bank_accounts` and `bank_transactions` to support the bank reconciliation feature. A trigger `update_bank_account_balance_trigger_func` ensures `bank_accounts.current_balance` is automatically updated. See `scripts/schema.sql` for full details.

## Testing
Automated tests are being progressively implemented using the Pytest framework.
-   **Unit Tests**: Located in `tests/unit/`, these tests verify individual components in isolation by mocking dependencies. Current unit tests cover:
    *   `TaxCalculator` (`app/tax/tax_calculator.py`)
    *   Pydantic DTO validators (e.g., `JournalEntryData`, `JournalEntryLineData` in `app/utils/pydantic_models.py`)
    *   `SequenceGenerator` (`app/utils/sequence_generator.py`)
    *   Several service classes (e.g., `AccountTypeService`, `CurrencyService`, `ExchangeRateService`, `FiscalPeriodService`, `ConfigurationService`, `CompanySettingsService`, `SequenceService`, `DimensionService` from `app/services/`).
-   **Running Tests**: Refer to `project_test_guide.md` for detailed instructions on running tests and generating coverage reports.

## Contributing
*(No changes to contribution guidelines from previous version)*

## Roadmap

### Recently Completed
-   **Banking Module Enhancements (Schema v1.0.4)**:
    *   Full Bank Reconciliation UI & Core Logic.
    *   CSV Bank Statement Import functionality.
    *   Automatic `BankTransaction` creation from JEs affecting bank GLs.
    *   Database schema updates for reconciliation and automatic bank balance updates.
-   **Dashboard KPIs (Initial)**: Display of YTD P&L, Cash, AR/AP, Overdue AR/AP.
-   **Automated Testing (Phase 1 Started)**: Unit tests established for `TaxCalculator`, key Pydantic DTOs, `SequenceGenerator`, and several core/accounting services.

### Current Focus / Next Steps
-   **Automated Testing (Phase 1 Continued - CRITICAL)**:
    *   Expand unit test coverage to more services (especially business services like `SalesInvoiceService`, `PaymentService`) and managers.
    *   Begin setup for integration tests with a dedicated test database.
-   **Refine Bank Reconciliation**:
    *   Implement logic and UI for handling complex matches (one-to-many, many-to-one).
    *   Improve UI for displaying already matched items and viewing reconciliation history.
    *   Enhance error handling and user feedback for CSV import and reconciliation.
    *   Persist partially matched/selected state within a reconciliation session before final save.
-   **Enhance Dashboard KPIs**:
    *   Add more metrics (e.g., AR/AP Aging details, financial ratios like Quick Ratio, Current Ratio).
    *   Investigate options for simple graphical representations (e.g., bar charts for P&L components).
    *   Allow user customization or period selection for dashboard KPIs.

### Long-term
-   Advanced reporting and analytics.
-   Inventory Control enhancements.
-   Multi-company support.
-   Cloud synchronization options.
-   Enhanced Tax Compliance features.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
https://drive.google.com/file/d/11Cv4mFJ5z4I3inVCg8nkncVsAQtuIWrl/view?usp=sharing, https://drive.google.com/file/d/13aFutu059EFwgvQM4JE5LrYT13_62ztj/view?usp=sharing, https://drive.google.com/file/d/150VU2J4NfkYirCIGqQxC5VL9a_s7jyV0/view?usp=sharing, https://drive.google.com/file/d/150bjU-eqzjI-Ytq5ndyS8Dqn6dc_Q-Lf/view?usp=sharing, https://drive.google.com/file/d/1Fcdn0EWCauERrISMKReM_r0_nVIQvPiH/view?usp=sharing, https://drive.google.com/file/d/1GWOGYCBqwiPra5MdbwwhwXrV2V-gc4iw/view?usp=sharing, https://drive.google.com/file/d/1IRffneWyqY8ILVvfOu3apYxB15SnhMYD/view?usp=sharing, https://drive.google.com/file/d/1Jn7YcXqS_35PuABZKuxDJRWFTN2K9HQE/view?usp=sharing, https://drive.google.com/file/d/1QYQSJ32tb7UYfuT-VHC2vgYYS3Cw_9dz/view?usp=sharing, https://drive.google.com/file/d/1S4zRP59L2Jxru__jXeoTL2TGZ4JN_GOT/view?usp=sharing, https://drive.google.com/file/d/1X5XkobtrDHItY5dTnWRYajA9LTVvZTGy/view?usp=sharing, https://drive.google.com/file/d/1aZvbOd6iuCcF5xeqlxGo_SdlzdwtWHpU/view?usp=sharing, https://drive.google.com/file/d/1bsb7xdrTRvfFSLOJVv_YBVncejRYeX-p/view?usp=sharing, https://drive.google.com/file/d/1eU9E4v6uT69z91uEABi8xf4-L1_PUKaI/view?usp=sharing, https://drive.google.com/file/d/1fcRRxU4xYdqMgGp58OyuFDOqIcGeOIW_/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221gVm5GnROGWVVYBXkgumxd5puGZ6g5Qs3%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1hF6djKphaR51gqDKE6GLgeBnlWXdKcWU/view?usp=sharing, https://drive.google.com/file/d/1jDfGr6zuWj_vuE2F6hzLB5mPpmk6O6Fb/view?usp=sharing, https://drive.google.com/file/d/1ndjSoP14ry1oCHgOguxNgNWxyP4c18ww/view?usp=sharing, https://drive.google.com/file/d/1pIaT2K8fvvCkfIp1fxQ2uSbBIMJKotCf/view?usp=sharing, https://drive.google.com/file/d/1qZ1u0nir4od0Vm_1PnX1gL57zfsGWKxP/view?usp=sharing, https://drive.google.com/file/d/1zWrsOeANNSTZ51c666H-DxQapeSjXnZY/view?usp=sharing

