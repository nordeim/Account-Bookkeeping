# Project Architecture Document: SG Bookkeeper (v6)

## 1. Introduction

### 1.1 Purpose
This document provides a comprehensive overview of the SG Bookkeeper application's architecture. It details the system's design, components, their interactions, data flow, and key architectural patterns employed. The goal is to serve as a guide for developers, architects, and technical stakeholders for understanding, maintaining, and evolving the application. This version reflects the codebase state including the enhanced Bank Reconciliation module (with draft persistence and history) and expanded Dashboard KPIs.

### 1.2 Scope
This document covers the following architectural aspects:
*   High-level system architecture and its layers.
*   Detailed component architecture, including core components, data models (ORM), data access layer (services), business logic layer (managers), and presentation layer (UI).
*   Data architecture, including database schema organization (up to v1.0.5) and data transfer objects (DTOs).
*   Key technologies, frameworks, and design patterns used.
*   Specialized architectural aspects such as asynchronous processing, configuration management, security, and error handling, including refinements for circular dependency resolution.
*   An overview of the project's directory structure.

### 1.3 Intended Audience
*   **Software Developers**: For understanding system design, component responsibilities, and inter-component communication.
*   **Software Architects**: For reviewing and evolving the architecture.
*   **QA Engineers**: For understanding system behavior and designing effective test strategies.
*   **Technical Project Managers**: For project oversight and technical decision-making.

## 2. System Overview
SG Bookkeeper is a cross-platform desktop application designed to provide comprehensive accounting solutions for Small to Medium-sized Businesses (SMBs), particularly those operating in Singapore. It is built using Python, with PySide6 for the Graphical User Interface (GUI) and PostgreSQL as the backend database.

Key functionalities include:
*   Full double-entry bookkeeping.
*   Chart of Accounts management.
*   General Journal entries and postings.
*   Sales and Purchase invoicing lifecycles.
*   Customer and Vendor relationship management (CRM/SRM).
*   Product and Service management, including basic inventory tracking (Weighted Average Cost).
*   Bank Account management: manual transaction entry, CSV bank statement import, and a comprehensive Bank Reconciliation module (supporting draft reconciliations, provisional matching, unmatching, finalization, and history viewing).
*   Payment processing (customer receipts, vendor payments) with invoice allocation.
*   Singapore-specific GST F5 tax return preparation (9% rate) and detailed reporting.
*   Financial reporting (Balance Sheet, Profit & Loss, Trial Balance, General Ledger).
*   A Dashboard displaying Key Performance Indicators (KPIs) including YTD P&L figures, cash balance, AR/AP totals & overdue amounts, AR/AP aging summaries, and Current Ratio.
*   System administration: User and Role management with Role-Based Access Control (RBAC), system configuration, and audit logging with UI viewers.

The application emphasizes data integrity, compliance with local accounting standards, user-friendliness, and robust auditability. It employs an asynchronous processing model to ensure UI responsiveness and has undergone refactoring to resolve circular import dependencies.

## 3. Architectural Goals & Principles
The architecture of SG Bookkeeper is guided by the following goals and principles:
*   **Maintainability**: Clear separation of concerns and modular design to simplify understanding, debugging, and updates.
*   **Scalability**: Ability to handle increasing data volumes and feature complexity.
*   **Responsiveness**: Asynchronous operations for long-running tasks to keep the UI fluid.
*   **Data Integrity**: Ensuring accuracy and consistency of financial data through database constraints, DTO validations, and business rule enforcement.
*   **Testability**: Designing components in a way that facilitates unit and integration testing.
*   **Modularity**: Organizing the application into distinct modules.
*   **Robustness**: Systematic error handling and clear feedback to the user.

## 4. High-Level Architecture
The application follows a layered architecture:

```
+-----------------------------------------------------------------+
|                       Presentation Layer (UI)                   |
| (PySide6: MainWindow, Module Widgets, Dialogs, TableModels)   |
| Handles User Interaction, Displays Data, Qt Signals/Slots       |
| Uses Pydantic DTOs for data input/display.                      |
+-----------------------------------------------------------------+
      ^                         | (Calls Managers via `schedule_task_from_qt`)
      | (UI Events, DTOs)       | (DTOs / Result Objects via `QMetaObject.invokeMethod`)
      v                         v
+-----------------------------------------------------------------+
|                  Business Logic Layer (Managers)                |
| (ApplicationCore, *Manager classes e.g., SalesInvoiceManager,  |
|  JournalEntryManager, BankTransactionManager, PaymentManager,   |
|  DashboardManager, BankReconciliationService acting as manager)|
| Encapsulates Business Rules, Complex Workflows, Validation.     |
| Orchestrates Services. Returns `Result` objects.                |
+-----------------------------------------------------------------+
      ^                         | (Calls Service methods with ORM objects or DTOs)
      | (Service results/ORM Objects) | (Async SQLAlchemy operations within Services)
      v                         v
+-----------------------------------------------------------------+
|                       Data Access Layer (Services)              |
| (DatabaseManager, *Service classes e.g., AccountService,        |
|  SalesInvoiceService, BankReconciliationService), SQLAlchemy Models|
| Implements Repository Pattern. Abstracts Database Interactions. |
| Manages ORM query logic.                                        |
+-----------------------------------------------------------------+
                                | (asyncpg Python DB Driver)
                                v
+-----------------------------------------------------------------+
|                          Database Layer                         |
| (PostgreSQL: Schemas [core, accounting, business, audit],      |
|  Tables, Views, Functions, Triggers, Constraints - v1.0.5)      |
+-----------------------------------------------------------------+
```

### 4.1 Layers Description
*   **Presentation Layer (UI)**: Built with PySide6. Responsible for user interaction, data rendering. Components include `MainWindow`, module-specific widgets (e.g., `BankReconciliationWidget`), dialogs, and custom table models. Communicates asynchronously with the Business Logic Layer using DTOs and `Result` objects.
*   **Business Logic Layer (Managers)**: Contains business rules, workflows, and validation. Managers (e.g., `SalesInvoiceManager`, `DashboardManager`) orchestrate operations. `ApplicationCore` serves as a central access point. For Bank Reconciliation, `BankReconciliationWidget` currently holds some manager-like orchestration logic calling `BankReconciliationService` directly.
*   **Data Access Layer (Services & ORM)**: Abstracts database interactions. Services (e.g., `AccountService`, `BankReconciliationService`) implement the Repository pattern using SQLAlchemy's asynchronous ORM. `DatabaseManager` handles connections and sessions.
*   **Database Layer**: PostgreSQL (schema v1.0.5). Organized into `core`, `accounting`, `business`, and `audit` schemas. Includes tables, views, functions, and triggers for data integrity and automation.

## 5. Detailed Component Architecture

### 5.1 Core Components (`app/core/`)
*   **`ApplicationCore` (`application_core.py`)**:
    *   Central orchestrator, initializes and provides access to managers and services.
    *   **Refactor Note**: Service classes are now imported locally within the `startup()` method (and type-hinted using `TYPE_CHECKING`) to prevent circular import dependencies. Manager classes are still imported at the module level but have been refactored to use conditional imports for their service dependencies.
*   **`DatabaseManager` (`database_manager.py`)**: Manages async PostgreSQL connections (SQLAlchemy, `asyncpg`), provides sessions, and sets `app.current_user_id` for audit triggers.
*   **`ConfigManager` (`config_manager.py`)**: Manages `config.ini`.
*   **`SecurityManager` (`security_manager.py`)**: Handles authentication (`bcrypt`), RBAC, and User/Role/Permission CRUD backend.
*   **Asynchronous Task Management (`app/main.py`)**: Dedicated `asyncio` event loop in a separate thread, with `schedule_task_from_qt` and `QMetaObject.invokeMethod` for UI-backend communication.

### 5.2 Data Models (`app/models/`)
SQLAlchemy ORM models.
*   **Base Classes (`base.py`)**: `Base`, `TimestampMixin`, `UserAuditMixin`.
*   **Organization**: Subdirectories (`core`, `accounting`, `business`, `audit`) mirror DB schemas. `app/models/__init__.py` aggregates all models.
*   **Key New/Updated Models**:
    *   `business.BankReconciliation`: Includes `id`, `bank_account_id`, `statement_date`, `statement_ending_balance`, `calculated_book_balance`, `reconciled_difference`, `reconciliation_date`, `notes`, `status` ('Draft', 'Finalized'), and audit user/timestamps.
    *   `business.BankAccount`: Added `last_reconciled_balance` and `reconciliations` relationship.
    *   `business.BankTransaction`: Added `reconciled_bank_reconciliation_id` and `reconciliation_instance` relationship.

### 5.3 Data Access Layer (Services - `app/services/`)
*   **Interfaces (`app/services/__init__.py`)**: Defines `IRepository` and specific service interfaces.
    *   `IBankAccountRepository`: Added `get_by_gl_account_id`.
    *   `IBankReconciliationRepository`: Updated with methods for draft management (`get_or_create_draft_reconciliation`), provisional matching (`mark_transactions_as_provisionally_reconciled`), finalization (`finalize_reconciliation`), unmatching (`unreconcile_transactions`), and history/detail fetching.
    *   `ICustomerRepository` & `IVendorRepository`: Added methods for AR/AP aging summaries.
    *   `IAccountRepository`: Added `get_total_balance_by_account_category_and_type_pattern`.
*   **Implementations**:
    *   `BankReconciliationService`: Implements new methods for draft lifecycle, transaction linking, and finalization.
    *   `CustomerService` & `VendorService`: Implement aging summary logic.
    *   `AccountService`: Implements new balance aggregation logic.
    *   `BankAccountService`: Implements `get_by_gl_account_id`.

### 5.4 Business Logic Layer (Managers)
*   **Refactor Note**: All manager classes that are initialized by `ApplicationCore` and receive service instances in their constructors have been modified to import these services conditionally (using `if TYPE_CHECKING:`) and use string literals for type hints in their `__init__` signatures to resolve circular import issues.
*   **Key Managers & Updates**:
    *   `BankTransactionManager`: Handles manual transaction entry, CSV import, and fetching unreconciled transactions for reconciliation display.
    *   `DashboardManager`: Orchestrates fetching data for all KPIs, including new AR/AP aging and Current Ratio. Uses various services (`CustomerService`, `VendorService`, `AccountService`, `JournalService`, `FinancialStatementGenerator`, etc.).
    *   Other managers (`SalesInvoiceManager`, `JournalEntryManager`, etc.) function as previously, but with refined import patterns.

### 5.5 Presentation Layer (UI - `app/ui/`)
*   **`BankReconciliationWidget`**:
    *   Manages the full reconciliation workflow:
        *   Gets or creates a "Draft" `BankReconciliation` session.
        *   Loads unreconciled statement and system transactions.
        *   Displays provisionally matched transactions for the current draft session in new tables.
        *   Handles "Match Selected" by calling services to link transactions to the draft and mark them provisionally reconciled. Logic for amount comparison corrected to `abs(sum_stmt_amounts - sum_sys_amounts)`.
        *   Handles "Unmatch Selected Items" by calling services to unlink transactions from the draft.
        *   Handles "Save Final Reconciliation" by calling services to update the draft to "Finalized".
    *   Displays paginated history of "Finalized" reconciliations and details of selected historical reconciliations.
*   **`DashboardWidget`**:
    *   UI updated with new `QGroupBox` sections for AR/AP Aging Summaries and a field for Current Ratio.
    *   Uses `QFormLayout` for better alignment within aging summary groups.
    *   Populates these new fields from the extended `DashboardKPIData` DTO.
    *   Layout improved with `QScrollArea` and two-column KPI display.

### 5.6 Utilities (`app/utils/`)
*   **`pydantic_models.py`**:
    *   `DashboardKPIData`: Extended with fields for AR/AP aging buckets (`ar_aging_current`, `ar_aging_1_30`, etc.), `total_current_assets`, `total_current_liabilities`, `current_ratio`.
    *   `BankReconciliationSummaryData`: Added for displaying history.
*   Other utilities (`json_helpers.py`, `result.py`, etc.) remain crucial.

## 6. Data Architecture (Schema v1.0.5)
*   **Database**: PostgreSQL.
*   **Schemas**: `core`, `accounting`, `business`, `audit`.
*   **Key Table Changes for v1.0.5**:
    *   `business.bank_reconciliations`: Now includes a `status` column ('Draft', 'Finalized') and related check constraint.
    *   Other tables (`bank_accounts`, `bank_transactions`) have fields linking to reconciliations.
*   **Triggers**: Audit triggers and `update_bank_account_balance_trigger_func` are active.

*(Sections 7-13: Key Technologies, Design Patterns, Async Processing, Configuration, Security, Deployment, Resource Management remain largely the same as detailed in the previous version of this document (from response_50), with the understanding that schema versions and specific initialization scripts have been updated.)*

## 14. Data Flow Examples

### 14.1 Bank Reconciliation (Updated Flow)
1.  **Initiate/Load (UI: `BankReconciliationWidget`)**:
    *   User selects Bank Account, Statement Date, enters Statement Ending Balance.
    *   Clicks "Load / Refresh Transactions".
2.  **Get/Create Draft (Service: `BankReconciliationService`, orchestrated by Widget)**:
    *   `_fetch_and_populate_transactions` calls `get_or_create_draft_reconciliation(bank_account_id, statement_date, statement_ending_balance, user_id)`.
    *   This returns a "Draft" `BankReconciliation` ORM object; its ID is stored as `_current_draft_reconciliation_id`. UI `statement_balance_spin` might update.
3.  **Fetch Transactions (Manager: `BankTransactionManager`, Service: `BankTransactionService`)**:
    *   `_fetch_and_populate_transactions` calls `BankTransactionManager.get_unreconciled_transactions_for_matching()` (fetches `is_reconciled=False` items).
    *   It also calls `BankReconciliationService.get_transactions_for_reconciliation(self._current_draft_reconciliation_id)` to fetch items already provisionally matched to this draft.
4.  **Display (UI)**: Unreconciled items populate their tables; provisionally matched items populate their new tables. Summary calculates.
5.  **User Interaction - Provisional Match (UI -> Service)**:
    *   User selects items in Unreconciled tables, clicks "Match Selected".
    *   Widget validates sums (`abs(sum_stmt - sum_sys) < tolerance`).
    *   Calls `BankReconciliationService.mark_transactions_as_provisionally_reconciled(draft_id, selected_txn_ids, statement_date, user_id)`.
    *   UI reloads all transaction lists (matched items move from unreconciled to provisionally matched tables).
6.  **User Interaction - Unmatch (UI -> Service)**:
    *   User selects items in Provisionally Matched tables, clicks "Unmatch Selected".
    *   Widget calls `BankReconciliationService.unreconcile_transactions(selected_txn_ids_to_unmatch, user_id)`.
    *   UI reloads all transaction lists (unmatched items move back to unreconciled tables).
7.  **User Interaction - Create JE for Statement Item (UI -> Manager -> Service)**:
    *   User selects statement item, clicks "Add JE". `JournalEntryDialog` pre-fills.
    *   Posting (via `JournalEntryManager`) auto-creates system `BankTransaction`. UI reloads.
8.  **Finalizing (UI -> Service)**:
    *   When Difference is zero, user clicks "Save Final Reconciliation".
    *   Widget calls `BankReconciliationService.finalize_reconciliation(draft_id, final_stmt_bal, final_book_bal, final_diff, user_id)`.
    *   Service updates `BankReconciliation.status` to 'Finalized', updates balances, updates `BankAccount` last reconciled info.
9.  **UI Feedback**: Success/error. History list refreshes. Current recon area clears/resets.

*(Sales Invoice Posting data flow remains similar to the previous document version.)*

## 15. Project Structure Overview
The project structure (detailed in `README.md`) organizes code into `app` (with sub-packages for `core`, `models`, `services`, `business_logic`/`accounting`/etc. for managers, `ui`, `utils`, `common`), `scripts`, `data`, `resources`, and `tests`. This promotes modularity and separation of concerns.

## 16. Future Considerations / Areas for Improvement
*   **Comprehensive Automated Testing**: Continue expanding unit and integration test coverage, especially for complex workflows like reconciliation and financial statement generation.
*   **Bank Reconciliation UI**: Enhance display of provisionally matched items (e.g., visually linking matched pairs). Implement more complex matching scenarios (one-to-many).
*   **Dashboard**: Add graphical representations and user customization for KPIs.
*   **Refactoring**: Consider introducing a dedicated `BankReconciliationManager` to encapsulate orchestration logic currently in `BankReconciliationWidget`.
*   **Error Handling**: Further standardize and improve user-facing error messages and backend logging.

This document will be updated as the SG Bookkeeper application architecture evolves.

---
https://drive.google.com/file/d/1-vPle_bsfW5q1aXJ4JI9VB5cOYY3f7oU/view?usp=sharing, https://drive.google.com/file/d/13M2zztt62TD_vYJ_XLKtW4t2E53jIHl4/view?usp=sharing, https://drive.google.com/file/d/14hkYD6mD9rl8PpF-MsJD9nZAy-1sAr0T/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%2216tABsm1Plf_0fhtruoJyyxobBli3e8-7%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/17uYGbfjBJ4WXQvK3l3utPF3ivE6qlIzZ/view?usp=sharing, https://drive.google.com/file/d/18WGWMhYAOK7uwQ6JIahz-5MoVuK4BmWe/view?usp=sharing, https://drive.google.com/file/d/19ERvDxLdRedhVXYp9Gh0Xsg6tMIucGWO/view?usp=sharing, https://drive.google.com/file/d/19T9JbSrHCuXhHpzFMUh4Ti_0sDPDycSW/view?usp=sharing, https://drive.google.com/file/d/1D7GYodcMgZv3ROPPRJTYX0g9Rrsq8wJD/view?usp=sharing, https://drive.google.com/file/d/1EGOoM0TGqPgNBJzwxKdVO2u331Myhd4b/view?usp=sharing, https://drive.google.com/file/d/1Ivh39pjoqQ9z4_oj7w7hWc0zOje2-Xjb/view?usp=sharing, https://drive.google.com/file/d/1JsX5NYICgfKkbhMVeQ7ZONrbNZFb0ms3/view?usp=sharing, https://drive.google.com/file/d/1LzMu08SqY6E5ZuvISa4BsEHxatVPE9g_/view?usp=sharing, https://drive.google.com/file/d/1QyS0xlh6owfMif6KMlyXmE2Zx2hmcdza/view?usp=sharing, https://drive.google.com/file/d/1XeBi9hSp0z0vgqVVSFxhKP_ZwSv_s5B-/view?usp=sharing, https://drive.google.com/file/d/1Y9orpJ67I0XwezEBeUhyJs03DdjkAMhH/view?usp=sharing, https://drive.google.com/file/d/1YG0Vqa2pI5htxdsACYigsS2TMjDHxTcl/view?usp=sharing, https://drive.google.com/file/d/1YT2dDZirM9wxwWzYP0p9SDXSYOcG0Js4/view?usp=sharing, https://drive.google.com/file/d/1ZZODHjv2AX2Pn1cRh_0CJDTSzXRGjAt_/view?usp=sharing, https://drive.google.com/file/d/1_c8t-qcWtcVdVUEUkDQ760cjc0vL2Y9Z/view?usp=sharing, https://drive.google.com/file/d/1_qYJXTG-2GtEtmjV0Js5Hn_m_8ts9X0d/view?usp=sharing, https://drive.google.com/file/d/1bSRRtsWeJI9djXTDZTZTjZxnsWS3cvsV/view?usp=sharing, https://drive.google.com/file/d/1co7XAzm8TWDpKWSqUCAAZmvtqroIbUdn/view?usp=sharing, https://drive.google.com/file/d/1cp5LuyXlsbaa_wFSiIMxRlBFSro8qhXq/view?usp=sharing, https://drive.google.com/file/d/1ghGjh0MtEZSDVftjVx583ocaaCDK2j9X/view?usp=sharing, https://drive.google.com/file/d/1mbj5C_Pqa-lbGFf4obvSnpdGm-ALui7y/view?usp=sharing, https://drive.google.com/file/d/1pLih0cWs3ZiqnDKd9f2GEaR1GXCmD8KA/view?usp=sharing, https://drive.google.com/file/d/1sYr8SFT1d9ZMDHLfxOS6VjtwJ3920sFT/view?usp=sharing, https://drive.google.com/file/d/1uKfTNXg8Oaes7aGaoaPB6klSZzywizh9/view?usp=sharing, https://drive.google.com/file/d/1vTPAoLcEetjBj17-5nTa_Z6RS7ND5Wmz/view?usp=sharing, https://drive.google.com/file/d/1xbA8X7irZHUayYcfOWWfi4oWm18hFDo2/view?usp=sharing

