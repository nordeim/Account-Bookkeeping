Of course. I have performed a deep analysis of the updated files and the existing codebase to understand the new features and architectural refinements. The key enhancements include a significantly more advanced and interactive dashboard with graphical charts and new financial ratios, a more user-friendly bank reconciliation process with visual matching aids, and more robust CSV import error reporting.

Based on this comprehensive review, here are the complete, updated replacement files for the `README.md` and the `Technical_Design_Specification_Document.md`.

---

### File 1 of 2: `README.md`

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
```

---
### File 2 of 2: `Technical_Design_Specification_Document.md`

```markdown
# Technical Design Specification Document: SG Bookkeeper (v17)

**Version:** 17.0
**Date:** 2025-06-10

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version **17.0**, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities up to schema version **1.0.6**.

This version specifically details significant enhancements to the application, building upon the previously established multi-company architecture:
*   **Enhanced Bank Reconciliation Module**: The UI/UX for bank reconciliation has been overhauled with real-time feedback and visual aids, including color-coded grouping of matched transactions and live calculation of selection totals.
*   **Graphical Dashboard KPIs**: The dashboard has been transformed from a static text display into a dynamic and interactive view featuring graphical bar charts for AR/AP Aging summaries and the inclusion of advanced financial ratios (Quick Ratio, Debt-to-Equity). Users can now analyze KPIs for any chosen date.
*   **Robust CSV Import Error Reporting**: The CSV import process now provides detailed, row-by-row error feedback in a dedicated dialog, greatly improving the user's ability to diagnose and fix import issues.
*   **New Financial Reports**: An "Income Tax Computation" report has been added to the reporting suite.

### 1.2 Scope
This TDS covers the following aspects of the SG Bookkeeper application:
-   **System Architecture**: The multi-company model, UI, business logic, data access layers, and asynchronous processing.
-   **Database Schema**: Details and organization as defined in `scripts/schema.sql` (v1.0.6), which includes the new `CorpTaxRate_Default` configuration.
-   **Key UI Implementation Patterns**: `PySide6` interactions, particularly the use of `QtCharts` for the dashboard, visual state management in the bank reconciliation UI, and the new error reporting dialogs.
-   **Core Business Logic**: Component structures and interactions for the enhanced `DashboardManager`, `BankTransactionManager` (for CSV import), and `FinancialStatementGenerator` (for tax computation).
-   **Data Models & DTOs**: Updates to Pydantic models like `DashboardKPIData` and the new `CSVImportErrorData`.

### 1.3 Intended Audience
-   Software Developers: For implementation, feature development, and understanding system design.
-   QA Engineers: For comprehending system behavior, designing effective test cases, and validation.
-   System Administrators: For deployment strategies, database setup, and maintenance.
-   Technical Project Managers: For project oversight, planning, and resource allocation.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application engineered with Python, utilizing PySide6 for its GUI and PostgreSQL for robust data storage. Its architecture now supports a **multi-company environment**, where each company's data is securely isolated in its own dedicated PostgreSQL database. The application provides a user-friendly interface to create new company databases and switch between them seamlessly.

Its core functionality includes a full double-entry bookkeeping system, Singapore-specific GST management, interactive financial reporting, and modules for managing Customers, Vendors, Products, Sales/Purchase Invoices, and Payments. The advanced Bank Reconciliation module features CSV import with robust error handling, persistent draft states, and visual aids for complex transaction matching. An interactive dashboard provides at-a-glance KPIs, including graphical aging summaries and key financial ratios, calculated for any user-selected date. The system is built with data integrity, security, and auditability as top priorities.

### 1.5 Current Implementation Status
As of version 17.0 (reflecting schema v1.0.6):
*   **Multi-Company Architecture**: Fully functional, allowing creation and switching between company databases.
*   **Bank Reconciliation Module (Enhanced)**:
    *   **Visual Grouping**: Provisionally matched items are now visually grouped using background colors based on their matching timestamp, making it easy to see which items were matched together.
    *   **Real-time Balancing Feedback**: The UI now displays the running totals of selected statement and system items, with color-coding to instantly show if the selection is balanced.
    *   Draft persistence, un-matching, and finalization workflows are stable.
*   **Dashboard KPIs (Enhanced)**:
    *   **Graphical Charts**: AR and AP Aging summaries are now displayed as `QBarChart`s for better visualization.
    *   **New Ratios**: Quick Ratio and Debt-to-Equity Ratio are now calculated and displayed.
    *   **"As of Date" Selector**: All KPIs can be recalculated for a user-selected historical date.
*   **CSV Import (Enhanced)**:
    *   The `BankTransactionManager` now captures detailed, row-level parsing and validation errors.
    *   A new `CSVImportErrorsDialog` is displayed after an import with errors, showing each failed row and the specific reason for failure in a clear table format.
*   **Reporting (Enhanced)**:
    *   A new "Income Tax Computation" report is available, providing a preliminary calculation based on P&L and configurable adjustments.
*   **Database**: Schema is at v1.0.6, which includes a new default corporate tax rate in the `core.configuration` table.

## 2. System Architecture

### 2.1 High-Level Architecture
The application maintains its robust layered architecture, now operating within a context defined by the currently selected company database. The core logic remains abstracted from the specific database it is connected to.

```mermaid
graph TD
    subgraph User Interaction
        A[UI Layer (app/ui)]
        I[Company Dialogs (app/ui/company)]
    end

    subgraph Business & Core Logic
        B[Logic Layer (Managers in app/business_logic, etc.)]
        F[Application Core (app/core/application_core)]
        J[Company Manager (app/core/company_manager)]
    end

    subgraph Data & Persistence
        C[Service Layer / DAL (app/services)]
        D[Database Manager (app/core/database_manager)]
        K[Company Registry (companies.json)]
        E[PostgreSQL Databases (One per Company)]
    end

    A -->|User Actions| B;
    I -->|User Actions| F;
    F -->|Restart App| A;
    F -->|Creates DB via| D;
    B -->|Uses Services| C;
    C -->|Uses Sessions from| D;
    D <--> E;
    F -->|Uses| J;
    J <--> K;
```

### 2.2 Component Architecture (Updates for New Features)
The recent enhancements build upon the existing component structure, primarily by adding new UI elements and expanding the logic within existing Managers and DTOs.

#### 2.2.1 Services (Data Access Layer - `app/services/`)
*   **`BankTransactionService` (`business_services.py`)**: The `get_all_for_bank_account` method now returns the `updated_at` timestamp in its DTO, which is crucial for the visual grouping feature in the bank reconciliation UI.
*   **`BankReconciliationService` (`business_services.py`)**: `get_transactions_for_reconciliation` now sorts the results by `updated_at` to facilitate grouping of items matched at the same time.

#### 2.2.2 Managers (Business Logic Layer)
*   **`DashboardManager` (`app/reporting/dashboard_manager.py`)**:
    *   `get_dashboard_kpis()` method is now parameterized with an `as_of_date`.
    *   It now calculates Total Inventory, Total Liabilities, and Total Equity to support new ratio calculations.
    *   It computes the Quick Ratio `((Current Assets - Inventory) / Current Liabilities)` and Debt-to-Equity Ratio `(Total Liabilities / Total Equity)`.
    *   These new values are populated into the expanded `DashboardKPIData` DTO.
*   **`BankTransactionManager` (`app/business_logic/bank_transaction_manager.py`)**:
    *   The `import_bank_statement_csv` method has been significantly refactored. It now captures specific error messages for each failed row and returns them in a `detailed_errors` list within the `Result` object. This provides rich data for the new error reporting UI.
*   **`FinancialStatementGenerator` (`app/reporting/financial_statement_generator.py`)**:
    *   A new public method, `generate_income_tax_computation`, has been added. It orchestrates calls to generate a P&L, then fetches accounts with specific tax treatments (e.g., "Non-Deductible") to calculate the chargeable income and estimated tax. It uses a new `CorpTaxRate_Default` value from `ConfigurationService`.

#### 2.2.3 User Interface (Presentation Layer - `app/ui/`)
*   **`DashboardWidget` (`app/ui/dashboard/dashboard_widget.py`)**:
    *   Now uses the `QtCharts` module.
    *   The static `QFormLayout` for aging summaries has been replaced with two `QChartView` widgets (`ar_aging_chart_view`, `ap_aging_chart_view`).
    *   A new private method, `_update_aging_chart`, takes a `QChartView` and KPI data to dynamically build and render a `QBarSeries` chart.
    *   Adds `QLabel`s for the new Quick Ratio and Debt-to-Equity Ratio KPIs.
    *   An "As of Date" `QDateEdit` control allows the user to select a date and trigger a full refresh of all KPIs for that specific date.
*   **`BankReconciliationWidget` (`app/ui/banking/bank_reconciliation_widget.py`)**:
    *   Introduces `_current_stmt_selection_total` and `_current_sys_selection_total` to track the sum of selected items in real-time.
    *   A new `_update_selection_totals` slot is connected to the `item_check_state_changed` signal of the unreconciled table models. It updates dedicated `QLabel`s and color-codes them green if the debit/credit totals of the selected items match.
    *   The `_update_draft_matched_tables_slot` now calls a helper, `_get_group_colors`, which uses transaction `updated_at` timestamps to assign background colors to rows, visually grouping items that were matched together in the same operation.
    *   The `ReconciliationTableModel` is updated to handle the `Qt.ItemDataRole.BackgroundRole` to display these colors.
*   **`CSVImportConfigDialog` (`app/ui/banking/csv_import_config_dialog.py`)**:
    *   The `_handle_import_result_slot` is updated to check the `Result` object for a `detailed_errors` list. If errors are present, it now instantiates and opens the new `CSVImportErrorsDialog`, passing the error data to it.
*   **`CSVImportErrorsDialog` (`app/ui/banking/csv_import_errors_dialog.py`) - NEW**:
    *   A new modal dialog designed to show CSV import failures in a clear, tabular format.
    *   Uses a `QTableView` with the new `CSVImportErrorsTableModel` to display the row number, the specific error message, and the original, unprocessed data from that row of the CSV file.
*   **`ReportsWidget` (`app/ui/reports/reports_widget.py`)**:
    *   The report type combo box now includes "Income Tax Computation".
    *   The UI logic in `_on_fs_report_type_changed` is updated to show/hide the correct date/parameter controls for the new report type (e.g., a "Fiscal Year" selector).
    *   `_display_financial_report` now handles the new report title and calls `_populate_tax_computation_model` to render the data in a `QTreeView`.

### 2.3 Technology Stack
-   **Programming Language**: Python 3.9+ (up to 3.12)
-   **UI Framework**: PySide6 6.9.0+ (including `QtCharts`)
-   **Database**: PostgreSQL 14+
-   **ORM**: SQLAlchemy 2.0+ (Asynchronous ORM with `asyncpg`)
-   **Async DB Driver**: `asyncpg`
-   **Data Validation (DTOs)**: Pydantic V2
-   **Password Hashing**: `bcrypt`
-   **Reporting Libraries**: `reportlab` (PDF), `openpyxl` (Excel)
-   **Dependency Management**: Poetry

## 3. Data Architecture
The data architecture consists of a central company registry and individual, isolated company databases.

### 3.1. Company Registry
*   **File:** `companies.json`
*   **Location:** The application's user configuration directory (e.g., `~/.config/SGBookkeeper/`).
*   **Structure:** A JSON array of objects, where each object contains a `display_name` for the UI and a `database_name` for the connection.

### 3.2. Company Database Schema
*   Each company database is at version **1.0.6**.
*   The only change from v1.0.5 is the addition of a new default key in `core.configuration`: `('CorpTaxRate_Default', '17.00', 'Default Corporate Tax Rate (%)', 1)`. This supports the new Income Tax Computation report.
*   No table structures were altered in this version.

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
*   **`DashboardKPIData`**: Extended to include new fields:
    *   `total_inventory: Decimal`
    *   `total_liabilities: Decimal`
    *   `total_equity: Decimal`
    *   `quick_ratio: Optional[Decimal]`
    *   `debt_to_equity_ratio: Optional[Decimal]`
*   **`BankTransactionSummaryData`**: Now includes `updated_at: datetime` to support visual grouping of matched transactions in the reconciliation UI.
*   **`CSVImportErrorData`**: A new DTO to structure row-level error information from CSV imports for display in the new error dialog. It contains `row_number`, `row_data` (as a list of strings), and `error_message`.

## 4. Detailed Module Specifications (New & Enhanced)

### 4.1. Dashboard Module (`app/reporting/dashboard_manager.py`, `app/ui/dashboard/`)
-   **Purpose**: Provide a quick, visual overview of key financial metrics as of a user-specified date.
-   **Manager (`DashboardManager`)**:
    *   The `get_dashboard_kpis` method is now the central aggregator for all dashboard data. It accepts an `as_of_date` parameter.
    *   It calculates financial ratios by first fetching all active asset, liability, and equity accounts, then summing their balances as of the `as_of_date` to get the required totals (Total Current Assets, Total Current Liabilities, Total Inventory, Total Liabilities, Total Equity).
-   **UI (`DashboardWidget`)**:
    *   Uses `QChartView` from `PySide6.QtCharts` to display AR and AP aging data.
    *   The `_update_aging_chart` method dynamically creates a `QBarSeries` with a `QBarSet`, populates it with the aging bucket data from the `DashboardKPIData` DTO, and attaches it to the chart view. It also configures the X (category) and Y (value) axes.

### 4.2. Banking Module (`app/business_logic/`, `app/ui/banking/`)
-   **Bank Reconciliation UX Enhancements (`BankReconciliationWidget`)**:
    *   **Selection Totals**: The `_update_selection_totals` slot is triggered whenever a checkbox in either of the unreconciled tables is toggled. It recalculates the sum of selected debit/credit amounts for each table and updates the `statement_selection_total_label` and `system_selection_total_label`. Crucially, it compares these totals and applies a green or red stylesheet to the labels to provide instant visual feedback on whether the current selection is balanced.
    *   **Visual Grouping**: The `_get_group_colors` method is called when populating the "Provisionally Matched" tables. It iterates through the transactions (which are pre-sorted by their match timestamp), detects when the time gap between consecutive transactions is significant (more than a few seconds), and assigns a new background color to the new group. This results in items matched in the same "click" having the same color.
-   **CSV Import Error Handling**:
    *   The `BankTransactionManager.import_bank_statement_csv` method now uses a `try...except` block within its main loop. Any validation error (e.g., invalid date format, invalid number) for a specific row is caught, a `CSVImportErrorData` object is created with the row number and original data, and the loop continues to the next row.
    *   The `CSVImportConfigDialog` receives the `Result` object containing both the summary counts and the list of detailed errors. If the error list is not empty, it instantiates and shows the `CSVImportErrorsDialog` before displaying the final summary message.

### 4.3. Reporting Module (`app/reporting/financial_statement_generator.py`)
-   **Income Tax Computation**:
    *   The new `generate_income_tax_computation` method in `FinancialStatementGenerator` takes a `FiscalYear` DTO as input.
    *   It begins by calling `generate_profit_loss` for the given fiscal year to get the Net Profit Before Tax.
    *   It then queries for all accounts with a `tax_treatment` of 'Non-Deductible' and 'Non-Taxable Income'.
    *   It sums the period activity for these accounts to get total add-backs and subtractions.
    *   It calculates the Chargeable Income and applies the default corporate tax rate (from `ConfigurationService`) to arrive at an estimated tax payable.
    *   The results are structured into a dictionary that the `ReportsWidget` and `ReportEngine` can use for display and export.

## 5. Conclusion
Version 17.0 of SG Bookkeeper introduces significant enhancements to user experience and functionality. The transformation of the dashboard into a dynamic, graphical, and more insightful tool provides immediate value. The refined bank reconciliation workflow, with its real-time feedback and visual aids, greatly simplifies one of the most complex bookkeeping tasks. Furthermore, the addition of robust, user-friendly error reporting for CSV imports and the new tax computation report elevates the application's professional capabilities. These updates demonstrate a commitment to creating a powerful, intuitive, and comprehensive accounting solution.
```

---
https://drive.google.com/file/d/13a54HCe719DE9LvoTL2G3fufXVAZ68s9/view?usp=sharing, https://drive.google.com/file/d/16sEyvS8ZfOJFIHl3N-L34xQnhEo5XPcI/view?usp=sharing, https://drive.google.com/file/d/17Lx6TxeEQJauqxEwWQIjL_Vounz-OOuU/view?usp=sharing, https://drive.google.com/file/d/17M3-d4q02eUhkRMgogRQMxwSbiDkCJow/view?usp=sharing, https://drive.google.com/file/d/1MxP_SNNW86u44e2wupzz6i2gb0ibGeUE/view?usp=sharing, https://drive.google.com/file/d/1QsDwk2m_1Nh4JHOshQw4zjEI3x1mgGkM/view?usp=sharing, https://drive.google.com/file/d/1RkrdC_e7A_-nbzKVAiL_fX48uib6mu1T/view?usp=sharing, https://drive.google.com/file/d/1Wvi2CiVPY0EL2kErW2muu_LbMy4J_sRF/view?usp=sharing, https://drive.google.com/file/d/1XPEV3rOOikcWVvhB7GwX0raI__osRg-Z/view?usp=sharing, https://drive.google.com/file/d/1Z0gGlgu698IMIFg56GxD60l4xKNg1fIt/view?usp=sharing, https://drive.google.com/file/d/1cJjbc9s6IGkKHeAhk-dh7ey9i7ArJMJe/view?usp=sharing, https://drive.google.com/file/d/1jNlP9TOSJtMzQMeLH1RoqmU2Hx7iwQkJ/view?usp=sharing, https://drive.google.com/file/d/1q3W6Cs4WVx7dLwL1XGN9aQ6bb-hyHmWS/view?usp=sharing, https://drive.google.com/file/d/1qYszGazA6Zm1-3YGdaKdDlPEr3HipU5k/view?usp=sharing, https://drive.google.com/file/d/1uYEc0AZDEBE2A4qrR5O1OFcFVHJsCtds/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221v7mZ4CEkZueuPt-aoH1XmYRmOooNELC3%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing

