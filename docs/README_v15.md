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

The application features a double-entry accounting core, GST management, interactive financial reporting, modules for essential business operations (Customer, Vendor, Product/Service Management, Sales & Purchase Invoicing, Payments), Bank Account management with transaction entry, **CSV bank statement import**, a **full Bank Reconciliation module**, and comprehensive User/Role/Permission administration including Audit Logs. Its goal is to provide an intuitive, powerful, and compliant solution that empowers business owners and accountants.

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
-   **Journal Entry System** (Implemented - UI for General Journal with Journal Type filter; transaction-specific JEs generated on posting of source documents; JEs also auto-created from Bank Reconciliation for statement-only items. Posting a JE affecting a bank-linked GL account now auto-creates a system `BankTransaction`.)
-   **Multi-Currency Support** (Foundational - Models, CurrencyManager exist. UI integration in transactions uses it.)
-   **Fiscal Year and Period Management** (Implemented - UI in Settings for FY creation and period auto-generation.)
-   **Budgeting and Variance Analysis** (Foundational - Models exist. UI/Logic planned.)

### Singapore Tax Compliance
-   **GST Tracking and Calculation** (Backend Implemented)
-   **GST F5 Return Data Preparation & Finalization** (Implemented - Backend for data prep & finalization with JE settlement. UI in Reports tab. Enhanced Excel export with transaction details per box.)
-   **Income Tax Estimation Aids** (Planned)
-   **Withholding Tax Management** (Foundational)

### Business Operations
-   **Customer Management** (Implemented)
-   **Vendor Management** (Implemented)
-   **Product and Service Management** (Implemented)
-   **Sales Invoicing and Accounts Receivable** (Implemented - Full lifecycle including WAC inventory JE)
-   **Purchase Invoicing and Accounts Payable** (Implemented - Full lifecycle including WAC inventory JE)
-   **Payment Processing and Allocation** (Implemented - UI for Customer Receipts & Vendor Payments, allocation, JE posting.)
-   **Inventory Control (Weighted Average Cost)** (Implemented)

### Banking
-   **Bank Account Management** (Implemented - Full CRUD and listing UI, linkage to GL.)
-   **Manual Bank Transaction Entry** (Implemented - UI for manual entry, listed per account.)
-   **CSV Bank Statement Import** (Implemented - UI dialog (`CSVImportConfigDialog`) for configuring and importing transactions.)
-   **Bank Reconciliation Module** (Implemented - UI (`BankReconciliationWidget`) for matching statement items with system transactions, identifying discrepancies, creating adjustment JEs, and saving reconciliation state. Database tables and logic support this.)

### Reporting & Analytics
-   **Standard Financial Statements**: Balance Sheet, Profit & Loss, Trial Balance, General Ledger (Implemented - UI in Reports tab, PDF/Excel export, enhanced GL with dimension filtering.)
-   **Dashboard KPIs** (Implemented - Displays YTD Revenue, Expenses, Net Profit; Current Cash, AR, AP balances in base currency.)
-   **Cash Flow Statement** (Planned)
-   **GST Reports** (Implemented - See GST F5 above.)
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

## Installation
*(This section remains largely the same as the previous version, as no new core dependencies or fundamental setup steps were introduced by the bank reconciliation feature itself. The key is ensuring the database schema matches v1.0.4 or later.)*

### Prerequisites
-   Python 3.9 or higher
-   PostgreSQL Server 14 or higher
-   Poetry
-   Git

### Developer Installation Steps
1.  **Clone Repository**
2.  **Install Dependencies**: `poetry install`
3.  **Prepare PostgreSQL User and Database** (e.g., `sgbookkeeper_user`, database `sg_bookkeeper`)
4.  **Configure `config.ini`**: In user's config directory (e.g., `~/.config/SGBookkeeper/config.ini`), set database credentials.
5.  **Initialize Database**:
    ```bash
    poetry run sg_bookkeeper_db_init --user YOUR_POSTGRES_ADMIN_USER --password YOUR_POSTGRES_ADMIN_PASSWORD --dbname sg_bookkeeper --drop-existing
    ```
    *(The `initial_data.sql` script now includes grants for `sgbookkeeper_user`)*
6.  **Compile Qt Resources**: `poetry run pyside6-rcc resources/resources.qrc -o app/resources_rc.py`
7.  **Run Application**: `poetry run sg_bookkeeper` (Default admin: `admin`/`password` - change on first login)

## Usage Guide
*(Updated to include new Banking features)*
-   **Banking C.R.U.D Tab**:
    *   Manage Bank Accounts (add, edit, toggle active).
    *   View transactions for a selected account.
    *   Manually add bank transactions.
    *   **Import Bank Statements**: Use the "Import Statement (CSV)" action to import transactions from a CSV file, configuring column mappings as needed.
-   **Bank Reconciliation Tab**:
    *   Select a bank account, enter the statement end date and ending balance.
    *   Load unreconciled statement items (from imports) and system-generated bank transactions.
    *   Match items between the two lists. The reconciliation summary will update dynamically.
    *   For statement items not in your books (e.g., bank charges, interest), use the "Add Journal Entry" button to create the necessary system entries. These will then appear in the system transactions list for matching.
    *   Once the "Difference" in the summary is zero, click "Save Reconciliation" to finalize and mark transactions as reconciled.
-   Other modules (Dashboard, Accounting, Sales, Purchases, Payments, Customers, Vendors, Products, Reports, Settings) function as previously described, with enhancements like Journal Type filter for JEs and Dimension filtering for GL reports.

## Project Structure
*(Key additions for Banking/Reconciliation)*
```
sg_bookkeeper/
├── app/
│   ├── ui/
│   │   ├── banking/
│   │   │   ├── bank_reconciliation_widget.py   # New UI for reconciliation
│   │   │   ├── reconciliation_table_model.py # New Table Model
│   │   │   ├── csv_import_config_dialog.py   # New Dialog for CSV import
│   │   │   └── ... (other banking UI files)
│   ├── models/
│   │   ├── business/
│   │   │   └── bank_reconciliation.py        # New ORM Model
│   ├── services/
│   │   └── business_services.py          # Includes BankReconciliationService
│   ├── business_logic/
│   │   └── bank_transaction_manager.py   # Updated with import/matching logic
│   └── ... (other directories as before)
├── resources/
│   ├── icons/
│   │   └── import_csv.svg                # New icon
└── ... (other files and directories as before)
```

## Database Schema
The PostgreSQL database schema now includes `business.bank_reconciliations` table, and `business.bank_accounts` and `business.bank_transactions` have been updated with new fields and foreign keys to support the bank reconciliation process. A new trigger (`update_bank_account_balance_trigger_func`) automatically maintains `bank_accounts.current_balance`. Refer to `scripts/schema.sql` (reflecting v1.0.4) for full details.

## Development
*(No changes to development workflow)*

## Contributing
*(No changes to contribution guidelines)*

## Roadmap

### Recently Completed (v1.0.4 Features - Current State)
-   **Banking Module Enhancements**:
    *   **Bank Reconciliation UI & Core Logic**: Interface for selecting account, statement date/balance. Loading unreconciled statement items and system transactions. UI calculations for reconciliation summary. Ability to "Match Selected" items. "Save Reconciliation" functionality.
    *   **CSV Bank Statement Import**: UI dialog (`CSVImportConfigDialog`) for configuring column mappings and importing transactions.
    *   **Journal Entry for Statement Items**: UI button in reconciliation screen to pre-fill `JournalEntryDialog` for unmatched statement items. Posting these JEs now auto-creates corresponding system `BankTransaction` records.
-   Database schema updates for bank reconciliation.
-   Automatic `bank_accounts.current_balance` updates via database trigger.
-   `JournalEntryManager` auto-creates `BankTransaction` records.
-   **Dashboard KPIs**: Basic display of YTD P&L figures, Cash, AR, AP.

### Current Focus / Next Steps
-   **Automated Testing (Phase 1 - CRITICAL)**:
    *   Establish a comprehensive test suite: unit tests for services/managers, integration tests for core workflows (e.g., invoice posting, payment allocation, bank reconciliation save), and basic UI tests for critical paths.
-   **Refine Bank Reconciliation**:
    *   Handling of complex matches (e.g., one-to-many, many-to-one statement lines to system transactions).
    *   UI improvements for displaying matched items and reconciliation history.
    *   More robust error handling and user feedback during CSV import and reconciliation processes.
    *   Persisting "matched" state within a reconciliation session before final save.
-   **Enhance Dashboard KPIs**:
    *   Add more KPIs (e.g., AR/AP Aging, Quick Ratio, Current Ratio).
    *   Consider graphical representations.
    *   Allow user customization or period selection for KPIs.

### Long-term
-   Advanced reporting and analytics.
-   Inventory Control enhancements.
-   Multi-company support.
-   Cloud synchronization options.
-   Enhanced Tax Compliance features.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
https://drive.google.com/file/d/11Cv4mFJ5z4I3inVCg8nkncVsAQtuIWrl/view?usp=sharing, https://drive.google.com/file/d/13aFutu059EFwgvQM4JE5LrYT13_62ztj/view?usp=sharing, https://drive.google.com/file/d/150VU2J4NfkYirCIGqQxC5VL9a_s7jyV0/view?usp=sharing, https://drive.google.com/file/d/150bjU-eqzjI-Ytq5ndyS8Dqn6dc_Q-Lf/view?usp=sharing, https://drive.google.com/file/d/1Fcdn0EWCauERrISMKReM_r0_nVIQvPiH/view?usp=sharing, https://drive.google.com/file/d/1GWOGYCBqwiPra5MdbwwhwXrV2V-gc4iw/view?usp=sharing, https://drive.google.com/file/d/1IRffneWyqY8ILVvfOu3apYxB15SnhMYD/view?usp=sharing, https://drive.google.com/file/d/1QYQSJ32tb7UYfuT-VHC2vgYYS3Cw_9dz/view?usp=sharing, https://drive.google.com/file/d/1S4zRP59L2Jxru__jXeoTL2TGZ4JN_GOT/view?usp=sharing, https://drive.google.com/file/d/1X5XkobtrDHItY5dTnWRYajA9LTVvZTGy/view?usp=sharing, https://drive.google.com/file/d/1aZvbOd6iuCcF5xeqlxGo_SdlzdwtWHpU/view?usp=sharing, https://drive.google.com/file/d/1bsb7xdrTRvfFSLOJVv_YBVncejRYeX-p/view?usp=sharing, https://drive.google.com/file/d/1eU9E4v6uT69z91uEABi8xf4-L1_PUKaI/view?usp=sharing, https://drive.google.com/file/d/1fcRRxU4xYdqMgGp58OyuFDOqIcGeOIW_/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221gVm5GnROGWVVYBXkgumxd5puGZ6g5Qs3%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1hF6djKphaR51gqDKE6GLgeBnlWXdKcWU/view?usp=sharing, https://drive.google.com/file/d/1jDfGr6zuWj_vuE2F6hzLB5mPpmk6O6Fb/view?usp=sharing, https://drive.google.com/file/d/1ndjSoP14ry1oCHgOguxNgNWxyP4c18ww/view?usp=sharing, https://drive.google.com/file/d/1pIaT2K8fvvCkfIp1fxQ2uSbBIMJKotCf/view?usp=sharing, https://drive.google.com/file/d/1qZ1u0nir4od0Vm_1PnX1gL57zfsGWKxP/view?usp=sharing, https://drive.google.com/file/d/1zWrsOeANNSTZ51c666H-DxQapeSjXnZY/view?usp=sharing

