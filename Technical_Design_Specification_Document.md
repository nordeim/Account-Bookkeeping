# Technical Design Specification Document: SG Bookkeeper (v5)

**Version:** 5.0
**Date:** 2025-05-27 

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version 5, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities observed in the existing codebase, including basic Customer Relationship Management (CRM) features, GST F5 return finalization workflow, and an interactive UI for standard financial reporting. This document serves as a comprehensive guide for ongoing development, feature enhancement, testing, and maintenance, ensuring clarity and consistency across the development team.

### 1.2 Scope
This TDS covers the following aspects of the SG Bookkeeper application:
-   **System Architecture**: Detailed breakdown of the UI, business logic, data access layers, and the crucial asynchronous processing architecture for Qt/asyncio integration.
-   **Database Schema**: Alignment with the comprehensive schema defined in `scripts/schema.sql`.
-   **Key UI Implementation Patterns**: Focus on `PySide6` UI components, particularly how they interact with asynchronous backend operations, exemplified by core accounting widgets, GST reporting, financial statement generation, and customer management.
-   **Core Business Logic**: Structure and interactions of key business logic components (Managers and Services), including those for customer management.
-   **Data Models**: SQLAlchemy ORM models as defined in `app/models/`.
-   **Data Transfer Objects (DTOs)**: Pydantic models in `app/utils/pydantic_models.py` used for data validation and transfer, including new DTOs for Customer data.
-   **Security Implementation**: Details on user authentication, authorization (RBAC), and audit mechanisms.
-   **Deployment and Initialization**: Procedures for setting up the application environment, database, and initial data.
-   **Current Implementation Status**: Highlighting implemented features and noting areas for future development.

### 1.3 Intended Audience
-   Software Developers: For understanding the existing codebase, implementing new features, and maintaining architectural consistency.
-   QA Engineers: For guiding test plan creation by understanding system behavior and data flows.
-   System Administrators: For deployment, database setup, and understanding system dependencies.
-   Technical Project Managers: For project oversight, planning future sprints, and understanding technical complexities.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application engineered with Python, utilizing PySide6 for its graphical user interface and PostgreSQL for robust, relational data storage. It is tailored to provide comprehensive accounting solutions for small to medium-sized businesses in Singapore. Key functionalities include a full double-entry bookkeeping system, Singapore-specific GST management (including data preparation and finalization workflow), interactive financial reporting (Balance Sheet, P&L, Trial Balance with view and export), and foundational modules for business operations such as basic Customer Management (view, add, edit, toggle active status). The application prioritizes data integrity, compliance with Singaporean accounting standards (SFRS) and tax regulations, and aims for a user-friendly experience. The foundational data structures are meticulously defined in `scripts/schema.sql`, with initial seeding data provided by `scripts/initial_data.sql`.

## 2. System Architecture

### 2.1 High-Level Architecture
(Diagram remains the same as TDS v4)
```
+---------------------------------------------------+
|                  Presentation Layer                |
|  (PySide6: MainWindow, Module Widgets, Dialogs)   |
+---------------------------------------------------+
      ^                    | (Qt Signals/Slots for UI update,
      |                    |  schedule_task_from_qt for async calls)
(User Interaction)         v
+---------------------------------------------------+
|                  Business Logic Layer              |
|  (ApplicationCore, Managers, Services - Async)    |
+---------------------------------------------------+
                         |  (SQLAlchemy ORM via asyncpg)
                         v
+---------------------------------------------------+
|                  Data Access Layer                 |
|      (DatabaseManager, SQLAlchemy Models)          |
+---------------------------------------------------+
                         |
                         v
+---------------------------------------------------+
|                  Database                          |
|      (PostgreSQL: Schemas, Tables, Views,          |
|       Functions, Triggers)                         |
+---------------------------------------------------+
```

### 2.2 Component Architecture

#### 2.2.1 Core Components (`app/core/`)
(Descriptions remain largely the same as TDS v4)
-   **`Application` (`app/main.py`)**
-   **`ApplicationCore` (`app/core/application_core.py`)**: Now also instantiates and provides access to `CustomerService` and `CustomerManager`.
-   **`ConfigManager` (`app/core/config_manager.py`)**
-   **`DatabaseManager` (`app/core/database_manager.py`)**: Updated to correctly set (or not set) `app.current_user_id` PostgreSQL session variable to support audit triggers, using `app_core.current_user`.
-   **`SecurityManager` (`app/core/security_manager.py`)**
-   **`ModuleManager` (`app/core/module_manager.py`)**

#### 2.2.2 Asynchronous Task Management (`app/main.py`)
(Description remains the same as TDS v4)

#### 2.2.3 Services (`app/services/`)
Services implement repository patterns for data access.
-   **Accounting & Core Services** (as listed in TDS v4, e.g., `AccountService`, `JournalService`, `FiscalPeriodService`, `FiscalYearService`, `SequenceService`, etc.)
-   **Tax Services** (as listed in TDS v4, e.g., `TaxCodeService`, `GSTReturnService`)
-   **Business Services (`app/services/business_services.py`)**:
    -   **`CustomerService` (New)**: Implements `ICustomerRepository`. Responsible for basic CRUD operations, fetching customer summaries (with filtering and pagination), and specific lookups (e.g., by customer code) for `Customer` entities.

#### 2.2.4 Managers (Business Logic) (`app/accounting/`, `app/tax/`, `app/business_logic/`)
Managers encapsulate more complex business logic and orchestrate service calls.
-   **Accounting Managers** (as listed in TDS v4, e.g., `ChartOfAccountsManager`, `JournalEntryManager`, `FiscalPeriodManager`, `CurrencyManager`)
-   **Tax Managers**:
    -   `GSTManager` (`app/tax/gst_manager.py`): Enhanced. `prepare_gst_return_data` now performs actual data aggregation from journal entries. `finalize_gst_return` logic is in place for updating status and triggering settlement JE.
    -   `TaxCalculator`, `IncomeTaxManager` (stub), `WithholdingTaxManager` (stub) (as in TDS v4).
-   **Reporting Managers**:
    -   `FinancialStatementGenerator` (`app/reporting/financial_statement_generator.py`): Output is now consumed by `ReportsWidget` for on-screen display.
    -   `ReportEngine` (`app/reporting/report_engine.py`): Export functions are now triggered from `ReportsWidget`.
-   **Business Logic Managers (`app/business_logic/`)**:
    -   **`CustomerManager` (New - `app/business_logic/customer_manager.py`)**: Orchestrates customer lifecycle operations. Handles validation (e.g., customer code uniqueness, valid foreign keys for AR account and currency), maps DTOs to ORM models, interacts with `CustomerService` for persistence, and manages customer active status.

#### 2.2.5 User Interface (`app/ui/`)
-   **`MainWindow` (`app/ui/main_window.py`)**
-   **Module Widgets**:
    -   `AccountingWidget` (`app/ui/accounting/`): Contains functional `ChartOfAccountsWidget` and `JournalEntriesWidget`.
    -   `SettingsWidget` (`app/ui/settings/`): Functional for Company Settings and Fiscal Year management.
    -   **`CustomersWidget` (Enhanced - `app/ui/customers/customers_widget.py`)**: No longer a stub. Now provides a `QTableView` (using `CustomerTableModel`) to list customers, a toolbar with "Add", "Edit", "Toggle Active", "Refresh" actions, and basic search/filter controls. Interacts with `CustomerManager` and `CustomerDialog`.
    -   **`ReportsWidget` (Enhanced - `app/ui/reports/reports_widget.py`)**:
        *   Now uses a `QTabWidget` to separate "GST F5 Preparation" and "Financial Statements".
        *   **GST F5 Tab**: Includes UI to select period, prepare data (calling `GSTManager`), display results, save draft `GSTReturn`, and **finalize** the draft (prompting for submission details and calling `GSTManager`).
        *   **Financial Statements Tab**: Allows selection of report type (BS, P&L, TB), date parameters. Generates and displays the report in a `QTextEdit` (as HTML). Provides "Export to PDF" and "Export to Excel" buttons, which use `QFileDialog` and call `ReportEngine`.
    -   `DashboardWidget`, `VendorsWidget`, `BankingWidget` (Remain stubs).
-   **Detail Widgets & Dialogs**:
    -   `AccountDialog`, `JournalEntryDialog`, `FiscalYearDialog` (as in TDS v4).
    -   **`CustomerTableModel` (New - `app/ui/customers/customer_table_model.py`)**: `QAbstractTableModel` subclass for displaying `CustomerSummaryData` in `CustomersWidget`.
    -   **`CustomerDialog` (New - `app/ui/customers/customer_dialog.py`)**: `QDialog` for adding and editing customer details. Includes fields for all customer attributes, asynchronously populates `QComboBox`es for currency and A/R accounts, validates input, and interacts with `CustomerManager` for saving.

### 2.3 Technology Stack
(Largely same as TDS v4, added `email-validator`)
-   **Programming Language**: Python 3.9+ (up to 3.12)
-   **UI Framework**: PySide6 6.9.0+
-   **Database**: PostgreSQL 14+
-   **Asynchronous DB Driver**: `asyncpg` >= 0.25.0
-   **ORM**: SQLAlchemy >= 2.0.0 (async features)
-   **Database Initialization/Schema**: `scripts/schema.sql`, `scripts/initial_data.sql`.
-   **Password Hashing**: `bcrypt`
-   **Date/Time Utilities**: `python-dateutil`
-   **Reporting Libraries**: `reportlab` (PDF), `openpyxl` (Excel).
-   **Data Validation (DTOs)**: Pydantic V2 (including `EmailStr` which requires `email-validator`).
-   **Dependency Management**: Poetry.
-   **Email Validation Library**: `email-validator` (installed via `pydantic[email]` extra).

### 2.4 Design Patterns
(Largely same as TDS v4. The new Customer module follows these established patterns.)
-   Layered Architecture, MVC/MVP, Repository (Services), Dependency Injection, Observer (Qt Signals/Slots), Result Object, DTOs, Threaded Asynchronous Execution.

## 3. Data Architecture

### 3.1 Database Schema Overview
(Remains consistent with `scripts/schema.sql` as described in TDS v4. The `business.customers` table is now actively used.)

### 3.2 SQLAlchemy ORM Models (`app/models/`)
(Structure remains. `app/models/business/customer.py` is now actively used by the new Customer module.)

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
The following DTOs have been added to support Customer Management:
-   **`CustomerBaseData`**: Common fields for customer creation and updates. Includes Pydantic validation (e.g., `EmailStr`, field lengths).
-   **`CustomerCreateData(CustomerBaseData, UserAuditData)`**: For creating new customers.
-   **`CustomerUpdateData(CustomerBaseData, UserAuditData)`**: Includes `id: int` for identifying the customer to update.
-   **`CustomerData(CustomerBaseData)`**: Represents a full customer record, including audit fields, typically for detailed views or when returning a full ORM object mapped to a DTO.
-   **`CustomerSummaryData(AppBaseModel)`**: A slim DTO (`id`, `customer_code`, `name`, `email`, `phone`, `is_active`) for populating list views efficiently.

### 3.4 Data Access Layer Interfaces (`app/services/__init__.py`)
The following interface has been added:
-   **`ICustomerRepository(IRepository[Customer, int])`**:
    ```python
    from app.models.business.customer import Customer
    from app.utils.pydantic_models import CustomerSummaryData

    class ICustomerRepository(IRepository[Customer, int]):
        @abstractmethod
        async def get_by_code(self, code: str) -> Optional[Customer]: pass
        
        @abstractmethod
        async def get_all_summary(self, active_only: bool = True,
                                  search_term: Optional[str] = None,
                                  page: int = 1, page_size: int = 50
                                 ) -> List[CustomerSummaryData]: pass
    ```

## 4. Module and Component Specifications

### 4.1 Core Accounting Module
(Existing specifications for CoA, JE, Fiscal Periods remain largely as per TDS v4, with backend methods now fully implemented and connected to UI.)

### 4.2 Tax Management Module (`app/tax/`)
-   **`GSTManager` (`app/tax/gst_manager.py`)**:
    -   `prepare_gst_return_data()`: Now implements actual data aggregation by querying posted `JournalEntryLine` records. It categorizes amounts based on `Account.account_type` and `TaxCode.code` to populate the fields of `GSTReturnData` (Standard-Rated Supplies, Taxable Purchases, Output/Input Tax, etc.).
    -   `finalize_gst_return()`: This method (previously defined) is now callable from the UI. It updates the `GSTReturn` status to "Submitted", records submission details, and orchestrates the creation of a settlement Journal Entry via `JournalEntryManager`.

### 4.3 Financial Reporting Module (`app/reporting/`)
-   **`FinancialStatementGenerator`**: Its methods (`generate_balance_sheet`, `generate_profit_loss`, `generate_trial_balance`) now provide data directly to the `ReportsWidget` for on-screen display.
-   **`ReportEngine`**: Its `export_report` method is now triggered from the `ReportsWidget` UI, allowing users to export the currently generated financial statement to PDF or Excel.

### 4.4 Business Operations Modules

#### 4.4.1 Customer Management Module
This module provides basic CRUD operations for customer entities.
-   **Service (`app/services/business_services.py`)**:
    -   **`CustomerService`**: Implements `ICustomerRepository`.
        -   `get_by_id()`: Fetches a `Customer` ORM object, eager-loading `currency` and `receivables_account`.
        -   `get_all_summary()`: Fetches a paginated and filterable list of `CustomerSummaryData` DTOs by selecting specific columns for efficiency. Supports filtering by `active_only` status and a `search_term` (on code, name, email).
        -   `save()`: Persists `Customer` ORM objects (for create/update).
-   **Manager (`app/business_logic/customer_manager.py`)**:
    -   **`CustomerManager`**:
        -   Dependencies: `CustomerService`, `AccountService` (for AR account validation), `CurrencyService` (for currency validation), `ApplicationCore`.
        -   `get_customer_for_dialog()`: Retrieves a full `Customer` ORM for dialog population.
        -   `get_customers_for_listing()`: Retrieves `List[CustomerSummaryData]` for table display, applying filters.
        -   `create_customer(dto: CustomerCreateData)`: Validates DTO (Pydantic) and business rules (e.g., code uniqueness via `CustomerService.get_by_code()`, existence and validity of `receivables_account_id` and `currency_code` via respective services). Maps DTO to `Customer` ORM, sets audit user IDs, and saves.
        -   `update_customer(customer_id: int, dto: CustomerUpdateData)`: Fetches existing customer, validates changes (especially code uniqueness), updates ORM fields from DTO, sets audit user ID, and saves.
        -   `toggle_customer_active_status(customer_id: int, user_id: int)`: Fetches customer, flips `is_active` status, sets audit user ID, and saves.

## 5. User Interface Implementation (`app/ui/`)

### 5.1 Core UI Components (MainWindow, Accounting, Settings)
(Remain largely as described in TDS v4, with their respective functionalities now more complete and tested.)

### 5.2 Reports Widget (`app/ui/reports/reports_widget.py`)
The `ReportsWidget` has been significantly enhanced and now uses a `QTabWidget`:
-   **GST F5 Preparation Tab**:
    -   Allows selection of period start/end dates.
    -   "Prepare GST F5 Data" button triggers `GSTManager.prepare_gst_return_data()` asynchronously.
    -   Results (Standard-Rated Supplies, Output Tax, etc.) are displayed in read-only `QLineEdit`s.
    -   "Save Draft GST Return" button calls `GSTManager.save_gst_return()`.
    -   **New**: "Finalize GST Return" button:
        -   Enabled only after a draft is successfully saved (and `_saved_draft_gst_return_orm.id` is available).
        -   Prompts user for "Submission Reference No." and "Submission Date" using `QInputDialog`.
        -   Calls `GSTManager.finalize_gst_return()` asynchronously.
        -   Updates UI based on success/failure (e.g., disables buttons, shows confirmation).
-   **Financial Statements Tab**:
    -   `QComboBox` to select Report Type ("Balance Sheet", "Profit & Loss Statement", "Trial Balance").
    -   Relevant `QDateEdit` fields for date parameters (dynamically shown/hidden based on report type).
    -   "Generate Report" button triggers the appropriate method on `FinancialStatementGenerator` asynchronously.
    -   Generated report data is displayed in a read-only `QTextEdit` using simple HTML formatting for structure.
    -   "Export to PDF" and "Export to Excel" buttons:
        -   Enabled after a report is generated.
        -   Use `QFileDialog.getSaveFileName()` to get the save path.
        -   Call `ReportEngine.export_report()` asynchronously to get report bytes, then write to file.

### 5.3 Customers Module UI (`app/ui/customers/`)
-   **`CustomersWidget` (`app/ui/customers/customers_widget.py`)**:
    -   Main layout with a toolbar, filter area, and a `QTableView`.
    -   **Toolbar**: Actions for "Add Customer", "Edit Customer", "Toggle Active Status", "Refresh List".
    *   **Filter Area**: `QLineEdit` for text-based search (code, name, email) and a `QCheckBox` for "Show Inactive" customers. Filters trigger `_load_customers`.
    -   **Table View**: Uses `CustomerTableModel` to display customer summaries. Supports sorting. Double-click on a row opens the customer for editing (or viewing, similar effect for MVP).
    -   `_load_customers()`: Asynchronously calls `CustomerManager.get_customers_for_listing()` with filter parameters. Updates `CustomerTableModel` via `_update_table_model_slot` (JSON serialization for thread safety).
    -   Action slots (`_on_add_customer`, `_on_edit_customer`, `_on_toggle_active_status`) interact with `CustomerDialog` and `CustomerManager`.
-   **`CustomerTableModel` (`app/ui/customers/customer_table_model.py`)**:
    -   Subclass of `QAbstractTableModel`.
    -   Displays `CustomerSummaryData` (ID (hidden), Code, Name, Email, Phone, Active status).
    -   Provides `get_customer_id_at_row()` for easy ID retrieval.
-   **`CustomerDialog` (`app/ui/customers/customer_dialog.py`)**:
    *   `QDialog` for adding or editing a customer.
    *   Contains input fields for all `Customer` attributes (code, name, contact details, address, financial terms, currency, A/R account, etc.).
    *   `QComboBox`es for "Default Currency" and "A/R Account" are populated asynchronously by fetching data from `CurrencyService` and `AccountService`.
    *   In edit mode, loads existing customer data by calling `CustomerManager.get_customer_for_dialog()`.
    *   On save, collects data into `CustomerCreateData` or `CustomerUpdateData` DTOs. Pydantic validation is implicitly triggered.
    *   Calls `CustomerManager.create_customer()` or `CustomerManager.update_customer()` asynchronously.
    *   Handles `Result` object from manager, displays success/error messages. Emits `customer_saved(customer_id)` signal.

## 6. Security Considerations
(Largely same as TDS v4. Audit trigger context setting in `DatabaseManager` is now confirmed and working.)
-   Passwords hashed (`bcrypt`). RBAC via `core.roles`/`permissions`.
-   Audit trails via DB triggers, using `app.current_user_id` set by `DatabaseManager`.

## 7. Database Access Implementation (`app/services/`)
-   **`CustomerService` (`app/services/business_services.py`)**:
    -   Implements `ICustomerRepository`.
    -   `get_all_summary()` method efficiently fetches specific columns for listing, supports filtering by active status and a search term (on code, name, email), and includes basic pagination. It maps results to `CustomerSummaryData` DTOs.
    -   Other methods (`get_by_id`, `get_by_code`, `save`) provide standard repository functionality.

## 8. Deployment and Installation
(No changes from TDS v4, but the `pydantic[email]` dependency implies `email-validator` is now installed via Poetry.)

## 9. Conclusion
This TDS (v5) reflects significant progress, particularly with the full lifecycle implementation for Journal Entries, GST F5 data preparation and finalization workflow UI, an interactive UI for generating and exporting standard financial reports, and the foundational backend and UI for basic Customer Management. The application is increasingly feature-rich and stable. Future work will focus on completing other business modules (Vendors, Products, Invoicing, Banking), enhancing reporting, and adding more advanced features.
