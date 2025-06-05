<think>
The user wants me to update the main `README.md` file.
My sources are:
1.  `README.md` (the latest version, provided in the previous turn, which I will call `README_latest.md`)
2.  `README (previous).md` (an older version, provided in the current turn, which I will call `README_previous.md`)
3.  `Technical_Design_Specification_Document.md` (the TDS I just updated)
4.  `Project Architecture Document.md` (PAD v5)
5.  `diff_output_schema.sql.md` (schema diffs)
6.  The two screenshots (Dashboard and Bank Reconciliation UI).

The goal is to create a *complete* updated replacement file for `README.md`. This means:
*   It should be self-contained.
*   Remove repeating details (if any, especially if an older version had less accurate info).
*   Add missing details from other documents to make the README comprehensive and current.
*   The README should reflect the latest state of the project (schema v1.0.5, features like enhanced bank rec and dashboard).

**Strategy:**

I will use `README_latest.md` (from the previous turn, which already reflects schema v1.0.5 and enhanced features) as the primary base because it's the most current version. I will then compare it against `README_previous.md` and other documents to see if any valuable information was lost or can be enhanced. The TDS and PAD v5 will be good sources for ensuring technical accuracy and feature completeness in the README.

**Key Sections to Review and Potentially Update in the README:**

1.  **Overview**: Ensure it accurately describes the application, highlighting the latest major features (enhanced bank rec with drafts/provisional matching/unmatching, enhanced dashboard KPIs). Compare with TDS Section 1.4 and PAD v5 Section 2.
2.  **Why SG Bookkeeper?**: Check if the points are still relevant and if any new strengths can be added based on recent developments.
3.  **Key Features**: This is a critical section.
    *   For each feature, especially Banking and Reporting & Analytics (Dashboard KPIs), ensure the description is up-to-date with the latest capabilities (drafts, provisional matching, unmatching, AR/AP aging, current ratio).
    *   Compare this list with TDS Section 1.5 (Current Implementation Status) and Section 4 (Module Specs), and PAD v5's feature list.
    *   Ensure the status (Implemented, Planned, etc.) is accurate. `README_latest.md` seems quite good here already.
4.  **Technology Stack**: Verify against TDS Section 2.3 and PAD v5 Section 7. `README_latest.md` has a comprehensive list.
5.  **Installation**:
    *   Compare with TDS Section 8 and PAD v5 Section 12.
    *   Ensure the steps for `config.ini` path are correct and consistent (PAD v5 has `%APPDATA%` for Windows, `README_latest.md` has `%APPDATA%` which is good).
    *   Verify the `sg_bookkeeper_db_init` command and its reference to schema v1.0.5.
    *   Ensure `poetry install --with dev` is mentioned if dev dependencies are needed for running tests (which are mentioned later).
6.  **Usage Guide**:
    *   This section should clearly explain how to use the new features, especially the refined Bank Reconciliation workflow (drafts, provisional matching, unmatching) and view the new Dashboard KPIs.
    *   Compare with TDS Section 4.7 (Banking Module overview), TDS Section 9.2 (Bank Rec Data Flow), and the UI screenshots.
    *   The `README_latest.md` has an updated usage guide. I need to verify its comprehensiveness.
7.  **Project Structure**:
    *   Compare with TDS Section 1.5 (mention of circular import fixes might be relevant if it changed structure significantly, but unlikely for README) and PAD v5 Section 15 (Project Structure Overview).
    *   Ensure the directory structure for `tests/` accurately reflects the unit test organization, including the new `reporting` and service test subdirectories mentioned in `README_latest.md`.
8.  **Database Schema**:
    *   Mention schema version 1.0.5.
    *   Briefly highlight key recent additions like `business.bank_reconciliations.status` and related fields, and the bank balance update trigger. This is well-covered in `README_latest.md`.
9.  **Testing**:
    *   List the types of tests (Unit tests).
    *   Mention key areas covered by unit tests, especially new ones for `DashboardManager`, `BankReconciliationService`, and related service methods for AR/AP aging.
    *   The `README_latest.md` lists these test files. I'll ensure this is accurate and complete.
    *   Include commands for running tests and generating coverage.
10. **Contributing**: Standard section, likely no changes needed unless project policies have updated.
11. **Roadmap**:
    *   **Recently Completed**: Ensure this aligns perfectly with the latest implemented features (enhanced Bank Rec, enhanced Dashboard KPIs, circular import fixes, schema v1.0.5, progress in unit tests for new logic).
    *   **Current Focus / Next Steps**: Should reflect immediate priorities.
    *   **Long-term**: General future goals.
    *   Compare with TDS Section 10 (Conclusion) for themes.
12. **License**: Standard.

**Comparing `README_latest.md` with `README_previous.md`:**

`README_previous.md` is the one attached in *this* user prompt. `README_latest.md` is the one provided in the *previous* user prompt (the one I was told to update).

*   `README_previous.md`'s "Key Features" for Banking:
    > **Bank Reconciliation Module** (Implemented - UI (`BankReconciliationWidget`) for matching statement items with system transactions, identifying discrepancies, creating adjustment JEs, and saving reconciliation state (`Draft` and `Finalized` statuses). Includes Reconciliation History view.)
*   `README_latest.md`'s "Key Features" for Banking:
    > **Bank Reconciliation Module** (Implemented - Comprehensive UI (`BankReconciliationWidget`) for:
    >     *   Loading/refreshing unreconciled statement items and system transactions.
    >     *   Persistent provisional matching of items to a "Draft" reconciliation.
    >     *   Unmatching provisionally matched items within the current draft session.
    >     *   Creating adjustment Journal Entries for statement-only items (e.g., bank charges, interest).
    >     *   Finalizing and saving the reconciliation (status changes to "Finalized").
    >     *   Viewing paginated history of finalized reconciliations and their cleared transaction details.
    >     *   Automatic creation of system `BankTransaction` records from relevant Journal Entries.
    This is much more detailed and accurate in `README_latest.md`.

*   `README_previous.md`'s "Key Features" for Dashboard KPIs:
    > **Dashboard KPIs** (Implemented - Initial set: YTD Revenue, Expenses, Net Profit; Current Cash Balance, Total Outstanding AR/AP, and Total Overdue AR/AP. Fetched via `DashboardManager`.)
*   `README_latest.md`'s "Key Features" for Dashboard KPIs:
    > **Dashboard KPIs** (Implemented - Displays YTD Revenue, Expenses, Net Profit; Current Cash Balance, Total Outstanding AR/AP, Total Overdue AR/AP, AR/AP Aging Summaries (Current, 1-30, 31-60, 61-90, 91+ days), and Current Ratio.)
    This is also more detailed and accurate in `README_latest.md`.

*   `README_previous.md`'s "Usage Guide" for Bank Reconciliation:
    > ...Once the "Difference" in the reconciliation summary is zero, click "Save Reconciliation" to finalize the reconciliation (status becomes `Finalized`) and mark transactions as reconciled. View reconciliation history...
*   `README_latest.md`'s "Usage Guide" for Bank Reconciliation:
    > ...A "Draft" reconciliation is created/loaded. Load unreconciled statement items and system transactions. "Match Selected" items to provisionally reconcile them against the current draft (these are persisted). "Unmatch Selected" to revert provisional matches. Create adjustment JEs for statement-only items. When balanced, "Save Final Reconciliation" to finalize. View history of finalized reconciliations and their details.
    `README_latest.md` is clearly superior here.

*   `README_previous.md`'s "Database Schema" mentions v1.0.5 but doesn't detail `bank_reconciliations.status`.
*   `README_latest.md`'s "Database Schema" correctly details it:
    > The PostgreSQL database schema is at version **1.0.5**. It includes tables for core system functions, detailed accounting, business operations, and comprehensive audit trails. Key recent additions include the `business.bank_reconciliations` table with a `status` column ('Draft', 'Finalized') and related fields in `bank_accounts` and `bank_transactions` to support the full bank reconciliation workflow, including draft persistence. A trigger `update_bank_account_balance_trigger_func` ensures `bank_accounts.current_balance` is automatically updated. See `scripts/schema.sql` for full details.

*   `README_previous.md`'s "Testing" section is less detailed about specific new tests.
*   `README_latest.md`'s "Testing" section lists more specific tests including:
    > Reporting Logic: `DashboardManager` including `_get_total_cash_balance` and `get_dashboard_kpis` (in `tests/unit/reporting/test_dashboard_manager.py`).
    > Service methods used by Dashboard: AR/AP Aging in `CustomerService`/`VendorService`, and `AccountService.get_total_balance_by_account_category_and_type_pattern`.

*   `README_previous.md`'s "Roadmap" (Recently Completed):
    > **Banking Module Enhancements**: Full Bank Reconciliation UI & Core Logic (including `Draft` and `Finalized` status for reconciliations). CSV Bank Statement Import functionality. Automatic `BankTransaction` creation from JEs affecting bank GLs. Database schema updates for reconciliation (v1.0.5) and automatic bank balance updates.
    > **Dashboard KPIs (Initial)**: Display of YTD P&L, Cash, AR/AP, and Overdue AR/AP balances.
*   `README_latest.md`'s "Roadmap" (Recently Completed):
    > **Bank Reconciliation Enhancements (Schema v1.0.5)**: Full workflow including Draft persistence for reconciliations. Persistent Provisional Matching... "Unmatch" functionality... Finalization... UI for viewing paginated history... CSV Bank Statement Import and automatic `BankTransaction` creation from relevant JEs.
    > **Dashboard KPI Enhancements**: Added AR/AP Aging Summaries... Added Current Ratio calculation... Backend services and manager logic...
    > **Circular Import Resolution**: Systematically fixed import cycles...
    > **Automated Testing (Phase 1 - Dashboard Logic)**: Unit tests for `DashboardManager` methods and dependent service logic for new KPIs.
    `README_latest.md` is much more accurate and detailed in the roadmap.

**Conclusion of Comparison**: `README_latest.md` (from the previous turn) is significantly more up-to-date and detailed than `README_previous.md` (from the current turn). So, my primary task will be to ensure `README_latest.md` is indeed complete and self-contained, and if there are any *other* details from TDS or PAD v5 that could further enhance it without making it overly technical for a README.

**Final Review of `README_latest.md` against TDS and PAD v5:**

*   **Key Features - Banking**: The list in `README_latest.md` is excellent. It covers all key aspects: loading, draft persistence, provisional matching, unmatching, JEs, finalization, history, auto-creation of `BankTransaction`. This aligns well with TDS 4.7 (refined) and 9.2.
*   **Key Features - Dashboard KPIs**: `README_latest.md` lists the new KPIs (AR/AP Aging, Current Ratio). This aligns with TDS 4.6.
*   **Installation**: The `config.ini` path section:
    `README_latest.md`:
    > Linux: `~/.config/SGBookkeeper/config.ini`
    > macOS: `~/Library/Application Support/SGBookkeeper/config.ini`
    > Windows: `%APPDATA%\SGBookkeeper\config.ini`
    TDS Section 8 uses `C:\Users\<YourUser>\AppData\Roaming\SGBookkeeper\config.ini` for Windows. `%APPDATA%` typically expands to this, so it's consistent.
    The `poetry run sg_bookkeeper_db_init` command correctly refers to schema v1.0.5 (implicitly, by saying "ensure it's v1.0.5").
*   **Usage Guide**:
    *   Dashboard: "View key financial indicators including YTD Revenue... AR & AP Aging summaries... Current Ratio." - Good.
    *   Bank Rec: "A 'Draft' reconciliation is created/loaded... 'Match Selected' items to provisionally reconcile them against the current draft (these are persisted). 'Unmatch Selected' to revert provisional matches... 'Save Final Reconciliation' to finalize." - This concisely captures the new workflow. It's excellent for a README.
*   **Project Structure**: The `tests/unit/reporting/` subdirectory is included in `README_latest.md`'s structure, which is good as it's mentioned in the Testing section.
*   **Database Schema**: The description in `README_latest.md` is good, mentioning schema v1.0.5, `bank_reconciliations.status`, related fields, and the trigger.
*   **Testing**: `README_latest.md` includes more detailed list of unit tests, including `DashboardManager` tests and tests for AR/AP aging service methods. This is current.
*   **Roadmap**: `README_latest.md`'s "Recently Completed" section is very accurate, covering bank rec enhancements, dashboard KPI enhancements, circular import resolution, and dashboard logic testing.

It seems `README_latest.md` is already very well updated and self-contained. The main task is to present this as the final output. I will make sure that no instructions like "make sure it's v1.0.5" are present, but rather state it *is* v1.0.5.
The user asked me to create a *complete updated replacement file*. So I will provide the full content of this improved `README.md`.

I will do one final pass to ensure clarity, self-containment, and remove any meta-commentary. The links at the end of `README_previous.md` (Google Drive links etc.) are not part of the README content itself, so they will be omitted from the actual `README.md` file content. The image link for the logo is a raw GitHub link, which is standard.
The instruction "Make sure your updated documents are self-contained with no reference to the prior versions. I should not need to refer to the earlier versions to fill in the gap in your updated documents" is key. The version of README I'm about to produce should stand alone.
The README from the previous turn (which I'm calling `README_latest.md` in my thoughts) looks to be a very strong candidate already. I will use its structure and content as the primary source, ensuring it's polished.
I have a clear understanding. The `README.md` provided in the previous turn seems to be the target standard. I will ensure the generated output is precisely that, after confirming it meets all criteria.
The previous README was generated as a result of request: `please update README.md document to reflect the latest developments, features, and information from the previous documents and responses. Make sure all sections are updated to be current and accurate, particularly Key Features, Usage Guide, Installation (esp. database initialization schema version), Database Schema section, Testing section, and Roadmap (Recently Completed and Next Steps).`
This means it should already incorporate information from other documents available at that time. My current task is to ensure *this specific version* being outputted is the correct, final one.

The user provided "README (previous).md" in *this* prompt, which I've established is older than the one from the *previous* prompt. I should base my output on the more current one and ensure it is complete.

Looks like I'm ready.

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
1.  **Clone Repository**: `git clone https://github.com/yourusername/sg_bookkeeper.git && cd sg_bookkeeper` (Replace `yourusername` with the actual path if forked).
2.  **Install Dependencies**: `poetry install --with dev` (The `--with dev` flag includes development dependencies like `pytest`).
3.  **Prepare PostgreSQL**:
    *   Ensure your PostgreSQL server is running.
    *   Create a dedicated database user (e.g., `sgbookkeeper_user`) and a database (e.g., `sg_bookkeeper`).
    *   Example (using `psql` as a PostgreSQL superuser like `postgres`):
        ```sql
        CREATE USER sgbookkeeper_user WITH PASSWORD 'YourSecurePassword123!';
        CREATE DATABASE sg_bookkeeper OWNER sgbookkeeper_user;
        ```
    *   The user specified in `config.ini` will need appropriate permissions on this database.
4.  **Configure `config.ini`**:
    *   The application expects `config.ini` in a platform-specific user configuration directory:
        *   Linux: `~/.config/SGBookkeeper/config.ini`
        *   macOS: `~/Library/Application Support/SGBookkeeper/config.ini`
        *   Windows: `%APPDATA%\SGBookkeeper\config.ini` (e.g., `C:\Users\<YourUser>\AppData\Roaming\SGBookkeeper\config.ini`)
    *   Create the `SGBookkeeper` directory if it doesn't exist.
    *   Copy `config.example.ini` (if provided in the repository) to this location as `config.ini`, or create `config.ini` with the following structure, adjusting values as necessary:
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
        last_opened_company_id = 1
        ```
    *   Ensure `username`, `password`, `host`, `port`, and `database` match your PostgreSQL setup.
5.  **Initialize Database**:
    *   This step typically requires PostgreSQL administrative privileges for the user running the script (e.g., `postgres`) to create extensions or if the database itself needs to be created by the script.
    *   Run the database initialization script using Poetry. This script uses `scripts/schema.sql` (which defines schema version 1.0.5) and `scripts/initial_data.sql`.
    ```bash
    poetry run sg_bookkeeper_db_init --user YOUR_POSTGRES_ADMIN_USER --password YOUR_POSTGRES_ADMIN_PASSWORD --dbname sg_bookkeeper --dbhost localhost --dbport 5432
    ```
    *   Replace placeholders like `YOUR_POSTGRES_ADMIN_USER` and `YOUR_POSTGRES_ADMIN_PASSWORD` with your PostgreSQL admin credentials.
    *   Add the `--drop-existing` flag *with caution* if you want to delete and recreate the `sg_bookkeeper` database for a clean setup.
6.  **Compile Qt Resources** (Recommended for consistent icon loading):
    ```bash
    poetry run pyside6-rcc resources/resources.qrc -o app/resources_rc.py
    ```
7.  **Run Application**:
    Ensure your `config.ini` points to the application database user (e.g., `sgbookkeeper_user`).
    ```bash
    poetry run sg_bookkeeper
    ```
    Default admin login: `admin`/`password`. You should be prompted to change this password on first login.

## Usage Guide
*(Updated to reflect Bank Reconciliation draft persistence, provisional matching/unmatching, and new Dashboard KPIs)*

-   **Dashboard Tab**: View key financial indicators including YTD Revenue, Expenses, Net Profit; Current Cash Balance; Total Outstanding & Overdue AR/AP; AR & AP Aging summaries (Current, 1-30, 31-60, 61-90, 91+ days); and Current Ratio. Use the "Refresh KPIs" button to update the displayed data.
-   **Banking C.R.U.D Tab**: Manage Bank Accounts (add, edit, toggle active status). View transaction lists for selected accounts. Manually add bank transactions (deposits, withdrawals, fees). Import bank statements using the "Import Statement (CSV)" action, which opens a dialog to configure column mappings specific to your CSV file format.
-   **Bank Reconciliation Tab**: Perform bank reconciliations.
    1.  Select a Bank Account.
    2.  Enter the Statement End Date and Statement Ending Balance from your bank statement.
    3.  Click "Load / Refresh Transactions". A "Draft" reconciliation is automatically created or loaded if one exists for the selected account and date.
    4.  The UI will display unreconciled statement items (from imports/manual entry) and unreconciled system-generated bank transactions in separate tables. Transactions already provisionally matched to the current draft will appear in "Provisionally Matched (This Session)" tables.
    5.  Select items from the "Unreconciled" tables and click "Match Selected". If amounts match, these items are provisionally reconciled against the current draft and moved to the "Provisionally Matched" tables (this is persisted in the database).
    6.  To undo a provisional match, select items from the "Provisionally Matched" tables and click "Unmatch Selected Items".
    7.  For statement items not yet in your books (e.g., bank charges, interest), use the "Add Journal Entry" button. This opens a pre-filled `JournalEntryDialog`. Posting this JE will also auto-create a corresponding system `BankTransaction`, which will then appear in the unreconciled list for matching.
    8.  The "Reconciliation Summary" section dynamically updates to show the difference.
    9.  Once the "Difference" is zero (or within an acceptable tolerance), click "Save Final Reconciliation". This changes the draft's status to "Finalized", updates the bank account's last reconciled date/balance, and permanently marks the reconciled transactions.
    10. View a paginated history of finalized reconciliations and their cleared transaction details in the "Reconciliation History" section.
-   **Accounting Tab**: Manage Chart of Accounts (CRUD) and Journal Entries (CRUD, post, reverse, filter by type).
-   **Sales/Purchases Tabs**: Full lifecycle management for Sales and Purchase Invoices, including draft creation, editing, posting (which generates financial and inventory JEs), list views with filtering, and dialogs with advanced product search.
-   **Payments Tab**: Record Customer Receipts and Vendor Payments, allocate them to specific invoices. List and filter payments.
-   **Customers/Vendors/Products & Services Tabs**: Full CRUD and list views with filtering for master data.
-   **Reports Tab**: Generate GST F5 Returns (with detailed Excel export) and standard Financial Statements (Balance Sheet, P&L, Trial Balance, General Ledger) with PDF/Excel export options. GL reports support filtering by up to two dimensions.
-   **Settings Tab**: Configure Company Information, manage Fiscal Years/Periods, Users (CRUD, password changes, role assignment), Roles & Permissions (CRUD, assign permissions to roles), and view Audit Logs (Action Log, Data Change History with filtering).

## Project Structure
```
sg_bookkeeper/
├── app/                          # Main application source code
│   ├── __init__.py
│   ├── main.py                     # Main application entry point
│   ├── core/                       # Core components (ApplicationCore, DBManager, Config, Security)
│   ├── common/                     # Common enums, constants, etc.
│   ├── models/                     # SQLAlchemy ORM models (organized by schema: core, accounting, business, audit)
│   ├── services/                   # Data access layer services (repositories)
│   ├── accounting/                 # Business logic managers for accounting module
│   ├── business_logic/             # Managers for Customers, Vendors, Products, Invoices, Payments, Banking
│   ├── reporting/                  # Logic managers for generating reports & dashboard data
│   ├── tax/                        # Business logic managers for tax module
│   ├── ui/                         # PySide6 UI components (organized by module)
│   │   ├── shared/                 # Shared UI components (e.g., ProductSearchDialog)
│   │   └── ... (other ui modules: accounting, audit, banking, customers, dashboard, etc.)
│   ├── utils/                      # General utility functions, Pydantic DTOs, helpers
│   └── resources_rc.py             # Compiled Qt resources (generated if pyside6-rcc is run)
├── data/                         # Default data templates (CoA, report templates, tax codes)
├── docs/                         # Project documentation (like this README, TDS, Architecture)
├── resources/                    # UI assets (icons, images, .qrc file)
├── scripts/                      # Database initialization scripts (db_init.py, schema.sql, initial_data.sql)
├── tests/                        # Automated tests
│   ├── conftest.py
│   ├── __init__.py
│   ├── unit/                     # Unit tests (organized by module)
│   │   ├── __init__.py
│   │   ├── accounting/           # Unit tests for accounting logic
│   │   ├── business_logic/       # Unit tests for business operations logic
│   │   ├── core/                 # Unit tests for core components
│   │   ├── reporting/            # Tests for reporting logic (e.g., DashboardManager)
│   │   ├── services/             # Tests for service layer components
│   │   ├── tax/                  # Tests for tax logic
│   │   └── utils/                # Tests for utilities
│   ├── integration/              # Integration tests (planned)
│   │   └── __init__.py
│   └── ui/                       # UI tests (planned)
│       └── __init__.py
├── .gitignore
├── pyproject.toml                # Poetry configuration
├── poetry.lock
├── README.md                     # This file
└── LICENSE
```

## Database Schema
The PostgreSQL database schema is at version **1.0.5**. It includes tables for core system functions, detailed accounting, business operations, and comprehensive audit trails. Key recent additions include the `business.bank_reconciliations` table with a `status` column ('Draft', 'Finalized') and related fields in `bank_accounts` and `bank_transactions` to support the full bank reconciliation workflow, including draft persistence. A trigger `update_bank_account_balance_trigger_func` ensures `bank_accounts.current_balance` is automatically updated based on its transactions. Refer to `scripts/schema.sql` for full details.

## Testing
Automated tests are implemented using Pytest to ensure code quality and prevent regressions.
-   **Unit Tests**: Located in `tests/unit/`, these verify individual components by mocking dependencies. Current unit tests cover:
    *   `TaxCalculator` (`tests/unit/tax/test_tax_calculator.py`)
    *   Pydantic DTO validators for `JournalEntryData` and `JournalEntryLineData` (`tests/unit/utils/test_pydantic_models_journal_entry.py`)
    *   `SequenceGenerator` (`tests/unit/utils/test_sequence_generator.py`)
    *   Core Services: `AccountTypeService`, `CompanySettingsService`, `ConfigurationService`, `CurrencyService`, `DimensionService`, `ExchangeRateService`, `FiscalPeriodService`, `FiscalYearService`, `SequenceService` (various files in `tests/unit/services/`).
    *   Business Service: `BankReconciliationService` (`tests/unit/services/test_bank_reconciliation_service.py`).
    *   Reporting Logic: `DashboardManager` including methods like `_get_total_cash_balance` and `get_dashboard_kpis` (in `tests/unit/reporting/test_dashboard_manager.py`).
    *   Service methods supporting Dashboard KPIs: AR/AP Aging summary methods in `CustomerService`/`VendorService`, and `AccountService.get_total_balance_by_account_category_and_type_pattern`.
-   **Running Tests**:
    *   To run all tests: `poetry run pytest`
    *   To generate a coverage report: `poetry run pytest --cov=app` (requires `pytest-cov` plugin)

## Contributing
Contributions are welcome! Please follow standard open-source contribution practices:
1.  Fork the repository.
2.  Create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name`).
3.  Make your changes, ensuring to add relevant tests where applicable.
4.  Run linters (e.g., `flake8`), formatters (e.g., `black`), and type checkers (e.g., `mypy`), and ensure all tests pass.
5.  Commit your changes with descriptive messages (Conventional Commits style preferred if possible).
6.  Push to your branch (`git push origin feature/your-feature-name`).
7.  Submit a Pull Request against the `main` (or `develop`) branch of the original repository.

Please adhere to coding standards and ensure your contributions align with the project's goals and architectural patterns.

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
-   **Automated Testing (Phase 1 - Dashboard Logic & Core Bank Rec)**: Unit tests for `DashboardManager` methods, dependent service logic for new KPIs, and key `BankReconciliationService` methods.

### Current Focus / Next Steps
-   **Automated Testing (Continued - CRITICAL)**:
    *   Expand unit test coverage to all remaining services (especially business services like `SalesInvoiceService`, `PaymentService`, remaining `BankAccountService`/`BankTransactionService` methods) and all managers.
    *   Begin setup and implementation of integration tests for core workflows (e.g., invoice posting, payment allocation, full bank reconciliation cycle).
-   **Refine Bank Reconciliation**:
    *   Implement UI and logic for handling complex matches (e.g., one-to-many, many-to-one statement lines to system transactions).
    *   UI improvements for visually linking matched items within the "Provisionally Matched" tables or a dedicated view.
    *   More robust error handling and user feedback during CSV import (e.g., detailed row-level error reporting for parsing issues).
-   **Enhance Dashboard KPIs (Phase 2)**:
    *   Add more financial ratios (e.g., Quick Ratio, Debt-to-Equity).
    *   Investigate and implement simple graphical representations for key KPIs (e.g., bar charts for aging summaries).
    *   Allow user customization or period selection for dashboard information.

### Long-term
-   Advanced reporting and analytics (e.g., customizable report builder).
-   Inventory Control enhancements (e.g., stocktakes, multiple locations, FIFO/LIFO costing methods).
-   Multi-company support within a single installation.
-   Cloud synchronization options (optional data backup/sync to a user-provided cloud storage).
-   Enhanced Tax Compliance features (e.g., more detailed Income Tax aids, preparation of IRAS Audit File (IAF)).
-   Full UI test suite using a suitable framework.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```

---
https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221C3YLnRKPRGzPZnYLR1QTk7UWEwAsh3Nz%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1Ca9966PXKMDnjAxCsyT8OmVM2CPRlb-7/view?usp=sharing, https://drive.google.com/file/d/1Uej9gO7t12EkmldGnw5jk_V_fDjhTJMw/view?usp=sharing, https://drive.google.com/file/d/1ZsmOW6huYvGv9eyPviU1VZzh2YZqtxgW/view?usp=sharing, https://drive.google.com/file/d/1azUf7bWoZO_Niu3T7P81Vg8osVNEAvdG/view?usp=sharing, https://drive.google.com/file/d/1bI33CCtQPwhzoEUl854m3V002dxflsWg/view?usp=sharing, https://drive.google.com/file/d/1eFLuD4rI0YIctcHcXtE_aGXdEI19KS7A/view?usp=sharing, https://drive.google.com/file/d/1i0d3rPoQdMDESiN3d1xl0HwlhxsW8IKA/view?usp=sharing, https://drive.google.com/file/d/1peEbFNwTqJse_rI4-Cr6AHJC5VkdMEyJ/view?usp=sharing, https://drive.google.com/file/d/1wiAxnIzKK89xeuNXnUIwze7jX3IRpmh0/view?usp=sharing

