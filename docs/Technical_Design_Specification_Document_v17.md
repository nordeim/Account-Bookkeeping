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

---
https://drive.google.com/file/d/13a54HCe719DE9LvoTL2G3fufXVAZ68s9/view?usp=sharing, https://drive.google.com/file/d/16sEyvS8ZfOJFIHl3N-L34xQnhEo5XPcI/view?usp=sharing, https://drive.google.com/file/d/17Lx6TxeEQJauqxEwWQIjL_Vounz-OOuU/view?usp=sharing, https://drive.google.com/file/d/17M3-d4q02eUhkRMgogRQMxwSbiDkCJow/view?usp=sharing, https://drive.google.com/file/d/1MxP_SNNW86u44e2wupzz6i2gb0ibGeUE/view?usp=sharing, https://drive.google.com/file/d/1QsDwk2m_1Nh4JHOshQw4zjEI3x1mgGkM/view?usp=sharing, https://drive.google.com/file/d/1RkrdC_e7A_-nbzKVAiL_fX48uib6mu1T/view?usp=sharing, https://drive.google.com/file/d/1Wvi2CiVPY0EL2kErW2muu_LbMy4J_sRF/view?usp=sharing, https://drive.google.com/file/d/1XPEV3rOOikcWVvhB7GwX0raI__osRg-Z/view?usp=sharing, https://drive.google.com/file/d/1Z0gGlgu698IMIFg56GxD60l4xKNg1fIt/view?usp=sharing, https://drive.google.com/file/d/1cJjbc9s6IGkKHeAhk-dh7ey9i7ArJMJe/view?usp=sharing, https://drive.google.com/file/d/1jNlP9TOSJtMzQMeLH1RoqmU2Hx7iwQkJ/view?usp=sharing, https://drive.google.com/file/d/1q3W6Cs4WVx7dLwL1XGN9aQ6bb-hyHmWS/view?usp=sharing, https://drive.google.com/file/d/1qYszGazA6Zm1-3YGdaKdDlPEr3HipU5k/view?usp=sharing, https://drive.google.com/file/d/1uYEc0AZDEBE2A4qrR5O1OFcFVHJsCtds/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221v7mZ4CEkZueuPt-aoH1XmYRmOooNELC3%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing

