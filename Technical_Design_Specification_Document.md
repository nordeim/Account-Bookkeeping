# Technical Design Specification Document: SG Bookkeeper (v11)

**Version:** 11.0
**Date:** 2025-05-30 <!-- Or current date -->

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version 11, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project. This version details the implementation of **Draft Purchase Invoice Management (Backend Logic and UI Dialog)** and **Enhanced PDF/Excel Export Formatting for Balance Sheet & Profit/Loss Reports**. These build upon previously documented features like full Sales Invoicing, User/Role Management, Customer/Vendor/Product Management, GST F5 workflow, and Financial Reporting UI options.

### 1.2 Scope
This TDS covers:
-   System Architecture, Asynchronous Processing.
-   Database Schema (`scripts/schema.sql`).
-   Key UI Implementation Patterns.
-   Core Business Logic: Including Sales and Purchase Invoice (Draft) management.
-   Data Models (SQLAlchemy ORM) and DTOs (Pydantic).
-   Security Implementation (User/Role/Permission management).
-   Reporting Engine enhancements for PDF/Excel.
-   Deployment and Initialization.
-   Current Implementation Status.

### 1.3 Intended Audience
(Remains the same)
-   Software Developers, QA Engineers, System Administrators, Technical Project Managers.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application (Python, PySide6, PostgreSQL) for Singaporean SMBs. It offers double-entry accounting, GST management, interactive financial reporting (with enhanced BS/P&L exports and UI options), modules for business operations (Customer, Vendor, Product, Sales Invoicing, Purchase Invoice draft management), and comprehensive User/Role/Permission administration. The main list view and posting for Purchase Invoices are planned next.

## 2. System Architecture

### 2.1 High-Level Architecture
(Diagram remains the same: Presentation -> Business Logic -> Data Access -> Database)
```
+---------------------------------------------------+
|                  Presentation Layer                |
|  (PySide6: MainWindow, Module Widgets, Dialogs)   |
+---------------------------------------------------+
      ^                    | (Qt Signals/Slots, schedule_task_from_qt)
      |                    v
(User Interaction)         
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
(Descriptions remain largely the same. `ApplicationCore` instantiates and provides access to `PurchaseInvoiceService` and `PurchaseInvoiceManager`.)

#### 2.2.2 Asynchronous Task Management (`app/main.py`)
(Description remains the same.)

#### 2.2.3 Services (`app/services/`)
-   **Business Services (`app/services/business_services.py`)**:
    -   `PurchaseInvoiceService`: Fully implemented for CRUD on draft `PurchaseInvoice` entities, including summary fetching.

#### 2.2.4 Managers (Business Logic) (`app/accounting/`, `app/tax/`, `app/business_logic/`)
-   **Reporting Managers (`app/reporting/`)**:
    -   `ReportEngine` (`app/reporting/report_engine.py`) **(Enhanced)**:
        -   Dispatcher `export_report` routes to specific methods for BS/P&L.
        -   New methods `_export_balance_sheet_to_pdf`, `_export_profit_loss_to_pdf`, `_export_balance_sheet_to_excel`, `_export_profit_loss_to_excel` provide improved formatting, headers, footers (PDF), sectioning, and number styling.
        -   Original generic export methods retained for other reports (TB, GL).
-   **Business Logic Managers (`app/business_logic/`)**:
    -   `PurchaseInvoiceManager` (`app/business_logic/purchase_invoice_manager.py`) **(Enhanced)**:
        -   Methods `create_draft_purchase_invoice` and `update_draft_purchase_invoice` are now fully implemented, including validation via `_validate_and_prepare_pi_data` (vendor checks, product checks, duplicate vendor invoice no. check, line calculations, total calculations).
        -   `get_invoice_for_dialog` and `get_invoices_for_listing` are functional.
        -   `post_purchase_invoice` remains a stub.

#### 2.2.5 User Interface (`app/ui/`)
-   **`MainWindow` (`app/ui/main_window.py`) (Enhanced)**: Now includes a "Purchases" tab hosting `PurchaseInvoicesWidget`.
-   **Module Widgets**:
    -   `ReportsWidget` (`app/ui/reports/reports_widget.py`) **(Enhanced)**:
        -   Financial Statements tab now includes `QCheckBox`es for "Include Zero-Balance Accounts" (BS only) and "Include Comparative Period" (BS & P&L).
        -   Dynamically shows/hides relevant `QDateEdit` controls for comparative period selection based on report type and checkbox state.
        -   Passes these new options to `FinancialStatementGenerator`.
    -   **`PurchaseInvoicesWidget` (New - `app/ui/purchase_invoices/purchase_invoices_widget.py`)**:
        -   Provides a `QTableView` (using `PurchaseInvoiceTableModel`) to list purchase invoices.
        -   Includes a toolbar with "New P.Invoice", "Edit Draft", "View P.Invoice", and "Refresh" actions. "Post" action is present but disabled.
        -   Filter area: `QComboBox` for Vendor (with completer, populates asynchronously), `QComboBox` for Status, `QDateEdit` for date range, Apply/Clear buttons.
        -   Interacts with `PurchaseInvoiceManager` and `PurchaseInvoiceDialog`.
-   **Detail Widgets & Dialogs**:
    -   **`PurchaseInvoiceTableModel` (New - `app/ui/purchase_invoices/purchase_invoice_table_model.py`)**: `QAbstractTableModel` for `PurchaseInvoiceSummaryData`.
    -   **`PurchaseInvoiceDialog` (Enhanced - `app/ui/purchase_invoices/purchase_invoice_dialog.py`)**:
        *   Fully functional for creating and editing **draft** purchase invoices (similar to `SalesInvoiceDialog`).
        *   Includes dynamic calculations for line items and invoice totals.
        *   Asynchronously loads Vendors, Products, Currencies, Tax Codes for comboboxes.
        *   Interacts with `PurchaseInvoiceManager` for saving drafts. "Save & Approve" button is disabled.

### 2.3 Technology Stack & 2.4 Design Patterns
(Remain consistent with TDS v10 / previous state.)

## 3. Data Architecture

### 3.1 Database Schema Overview, 3.2 SQLAlchemy ORM Models, 3.4 Data Access Layer Interfaces
(Remain consistent. `IPurchaseInvoiceRepository` is now fully utilized by `PurchaseInvoiceService`.)

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
(DTOs for `PurchaseInvoice` Management: `PurchaseInvoiceLineBaseData`, `PurchaseInvoiceBaseData`, `PurchaseInvoiceCreateData`, `PurchaseInvoiceUpdateData`, `PurchaseInvoiceData`, `PurchaseInvoiceSummaryData` are now fully defined and used.)

## 4. Module and Component Specifications

### 4.1 - 4.3 Core Accounting, Tax, Non-Financial Reporting Modules
(No major changes from TDS v10 for these sections themselves.)

### 4.4 Business Operations Modules

#### 4.4.1 - 4.4.3 Customer, Vendor, Product/Service Management Modules
(As detailed in TDS v10.)

#### 4.4.4 Sales Invoicing Module
(As detailed in TDS v10 - fully functional for draft CRUD and posting.)

#### 4.4.5 Purchase Invoicing Module (Draft Management Implemented, List UI Added)
This module now supports full CRUD operations for draft purchase invoices and lists them.
-   **Service (`app/services/business_services.py -> PurchaseInvoiceService`)**: Fully implemented as per TDS v10.
-   **Manager (`app/business_logic/purchase_invoice_manager.py -> PurchaseInvoiceManager`)**:
    -   Draft management methods (`create_draft_purchase_invoice`, `update_draft_purchase_invoice`) are fully implemented with validation and calculation logic.
    -   Listing and detail-fetching methods (`get_invoices_for_listing`, `get_invoice_for_dialog`) are functional.
    -   Posting logic (`post_purchase_invoice`) remains a stub.
-   **UI (`app/ui/purchase_invoices/`)**:
    -   `PurchaseInvoiceDialog`: Functionally complete for creating/editing draft purchase invoices, including all calculations and interactions with the manager for saving.
    -   `PurchaseInvoicesWidget`: Provides a list view of purchase invoices with filtering. Allows adding new, editing drafts, and viewing all purchase invoices via the `PurchaseInvoiceDialog`.

### 4.5 System Administration Modules (User, Role & Permission Management)
(As detailed in TDS v9 - UI and backend fully functional.)

## 5. User Interface Implementation (`app/ui/`)

### 5.1 - 5.6 (Excluding Purchases) Existing UI Modules
(Functionality as detailed in TDS v10, including enhanced `ReportsWidget` options.)

### 5.7 Purchase Invoicing UI (`app/ui/purchase_invoices/`) (New/Enhanced Section)
-   **`PurchaseInvoicesWidget` (`app/ui/purchase_invoices/purchase_invoices_widget.py`)**:
    -   The main UI for managing purchase invoices, accessed via a "Purchases" tab in `MainWindow`.
    -   **Layout**: Toolbar, filter area, `QTableView`.
    -   **Toolbar**: "New P.Invoice", "Edit Draft", "View P.Invoice", "Refresh". "Post" is stubbed/disabled.
    -   **Filter Area**: Vendor (`QComboBox` with completer), Status (`QComboBox`), Date Range (`QDateEdit`s), Apply/Clear buttons.
    -   **Table View**: Uses `PurchaseInvoiceTableModel` to display `PurchaseInvoiceSummaryData`. Supports sorting. Double-click opens for viewing (or editing if draft).
    -   **Data Flow**: Asynchronously loads vendors for filter, loads invoices via `PurchaseInvoiceManager` based on filters, updates table model.
    -   **Actions**: Launch `PurchaseInvoiceDialog` for New/Edit/View. `invoice_saved` signal from dialog triggers list refresh.
-   **`PurchaseInvoiceTableModel` (`app/ui/purchase_invoices/purchase_invoice_table_model.py`)**:
    -   `QAbstractTableModel` subclass for `PurchaseInvoiceSummaryData`. Columns: Our Ref No., Vendor Inv No., Date, Vendor, Total, Status.
-   **`PurchaseInvoiceDialog`**: (As detailed in TDS v10 - fully functional for draft CRUD).

## 6. Security Considerations
(No changes from TDS v10.)

## 7. Database Access Implementation (`app/services/`)
(No changes from TDS v10; `PurchaseInvoiceService` is fully implemented for draft data access.)

## 8. Deployment and Installation
(No changes from TDS v10.)

## 9. Conclusion
This TDS (v11) documents a SG Bookkeeper application with significantly enhanced Purchase Invoicing capabilities (full draft management UI and backend) and more refined reporting features (new BS/P&L export formats, more UI options for BS/P&L). The application provides a solid foundation for key accounting, business operations management, and system administration. The next major steps will likely focus on completing the Purchase Invoicing module (posting logic), further enhancing reporting, or beginning other transactional modules like Payments or Banking.
