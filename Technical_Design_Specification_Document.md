# Technical Design Specification Document: SG Bookkeeper (v10)

**Version:** 10.0
**Date:** 2025-05-30 <!-- Or current date -->

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version 10, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project. This version specifically details the implementation of **Draft Purchase Invoice Management (Backend Logic and UI Dialog)**, building upon previously documented features such as full Sales Invoicing, User/Role Management, Customer/Vendor/Product Management, GST F5 workflow, and Financial Reporting.

### 1.2 Scope
This TDS covers:
-   System Architecture, Asynchronous Processing.
-   Database Schema (`scripts/schema.sql`).
-   Key UI Implementation Patterns.
-   Core Business Logic: Including Sales and Purchase Invoice (Draft) management.
-   Data Models (SQLAlchemy ORM) and DTOs (Pydantic).
-   Security Implementation (User/Role/Permission management).
-   Deployment and Initialization.
-   Current Implementation Status: Highlighting the newly functional Purchase Invoice Dialog for draft management.

### 1.3 Intended Audience
(Remains the same as TDS v9)
-   Software Developers, QA Engineers, System Administrators, Technical Project Managers.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application (Python, PySide6, PostgreSQL) for Singaporean SMBs. It offers double-entry accounting, GST management, financial reporting, business operations modules (Customer, Vendor, Product, Sales Invoicing), User/Role/Permission administration, and now, capabilities for creating and managing **Draft Purchase Invoices**. The main list view and posting for Purchase Invoices are planned next.

## 2. System Architecture

### 2.1 High-Level Architecture
(Diagram and core description remain the same as TDS v9)

### 2.2 Component Architecture

#### 2.2.1 Core Components (`app/core/`)
(Descriptions remain largely the same. `ApplicationCore` now also instantiates and provides access to `PurchaseInvoiceService` and `PurchaseInvoiceManager`.)

#### 2.2.2 Asynchronous Task Management (`app/main.py`)
(Description remains the same.)

#### 2.2.3 Services (`app/services/`)
-   **Accounting, Core, Tax Services** (as listed in TDS v9).
-   **Business Services (`app/services/business_services.py`)**:
    -   `CustomerService`, `VendorService`, `ProductService`, `SalesInvoiceService`.
    -   **`PurchaseInvoiceService` (Enhanced)**: Implements `IPurchaseInvoiceRepository`. Provides full CRUD for `PurchaseInvoice` and `PurchaseInvoiceLine` entities, including summary fetching with filters and specific lookups. Delete operation is restricted to draft invoices.

#### 2.2.4 Managers (Business Logic) (`app/accounting/`, `app/tax/`, `app/business_logic/`)
-   **Accounting, Tax, Reporting Managers** (as listed in TDS v9).
-   **Business Logic Managers (`app/business_logic/`)**:
    -   `CustomerManager`, `VendorManager`, `ProductManager`, `SalesInvoiceManager`.
    -   **`PurchaseInvoiceManager` (Enhanced - `app/business_logic/purchase_invoice_manager.py`)**:
        -   Orchestrates purchase invoice draft lifecycle.
        -   `_validate_and_prepare_pi_data()`: Validates DTOs, fetches related entities (Vendor, Products, Tax Codes), calculates line item totals (subtotal, discount, tax using `TaxCalculator`), and aggregates invoice totals. Includes checks for duplicate vendor invoice numbers.
        -   `create_draft_purchase_invoice()`: Uses prepared data, generates an internal reference number (`invoice_no`) via sequence, maps to ORM, and saves.
        -   `update_draft_purchase_invoice()`: Fetches existing draft, uses prepared data to update, handles line item replacement transactionally.
        -   `get_invoice_for_dialog()` and `get_invoices_for_listing()` are functional.
        -   `post_purchase_invoice()`: Remains a stub for future implementation (JE creation, status update, inventory).

#### 2.2.5 User Interface (`app/ui/`)
-   **`MainWindow` (`app/ui/main_window.py`)**: No new top-level tabs for Purchase Invoices yet.
-   **Module Widgets**:
    -   Existing widgets (`AccountingWidget`, `SalesInvoicesWidget`, etc.) functional as per TDS v9.
    -   **`PurchaseInvoicesWidget` (Planned/Stub)**: The main list view for purchase invoices is not yet implemented.
-   **Detail Widgets & Dialogs**:
    -   Existing dialogs (`SalesInvoiceDialog`, `UserDialog`, etc.) functional as per TDS v9.
    -   **`PurchaseInvoiceDialog` (Enhanced - `app/ui/purchase_invoices/purchase_invoice_dialog.py`)**:
        *   Fully functional for creating and editing **draft** purchase invoices.
        *   Header Fields: Vendor (`QComboBox` with completer), Vendor Invoice No. (`QLineEdit`), Our Internal Ref No. (`QLabel`, auto-generated on save), Invoice Date, Due Date, Currency, Exchange Rate, Notes.
        *   Line Items Table (`QTableWidget`): Dynamically adds/removes lines. Columns for Product/Service (`QComboBox` with completer, auto-fills purchase price), Description, Quantity, Unit Price, Discount %, Tax Code (`QComboBox`), and read-only calculated Subtotal, Tax Amount, Line Total.
        *   Dynamic Calculations: Line totals and overall invoice totals (Subtotal, Total Tax, Grand Total) update automatically as line data changes.
        *   ComboBox Population: Asynchronously loads Vendors, Products, Currencies, Tax Codes.
        *   Data Handling: On "Save Draft", collects UI data into `PurchaseInvoiceCreateData` or `PurchaseInvoiceUpdateData` DTOs, calls `PurchaseInvoiceManager` methods. Displays success/error messages. Dialog closes on successful draft save.
        *   "Save & Approve" button is present but disabled, as posting logic for PIs is not yet implemented.

### 2.3 Technology Stack
(Same as TDS v9)

### 2.4 Design Patterns
(Same as TDS v9. Purchase Invoice draft management follows established patterns.)

## 3. Data Architecture

### 3.1 Database Schema Overview
(Remains consistent. `business.purchase_invoices` and `business.purchase_invoice_lines` tables are actively used by new components.)

### 3.2 SQLAlchemy ORM Models (`app/models/`)
(`app/models/business/purchase_invoice.py` is actively used and its definition is confirmed suitable.)

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
DTOs for `PurchaseInvoice` Management are now fully defined and actively used:
-   `PurchaseInvoiceLineBaseData`, `PurchaseInvoiceBaseData`, `PurchaseInvoiceCreateData`, `PurchaseInvoiceUpdateData`, `PurchaseInvoiceData`, `PurchaseInvoiceSummaryData`.

### 3.4 Data Access Layer Interfaces (`app/services/__init__.py`)
The `IPurchaseInvoiceRepository` interface is defined with methods for specific lookups and summary fetching.

## 4. Module and Component Specifications

### 4.1 - 4.4 Core Accounting, Tax, Reporting, Other Business Operations Modules
(Functionality as detailed in TDS v9 remains current for Sales Invoicing, Customer, Vendor, Product Management etc.)

### 4.5 Purchase Invoicing Module (Draft Management Implemented)
This module provides capabilities for creating and managing draft purchase invoices.
-   **Service (`app/services/business_services.py`)**:
    -   **`PurchaseInvoiceService`**: Implements `IPurchaseInvoiceRepository`. Full CRUD for `PurchaseInvoice` (drafts), including eager loading for `get_by_id` and comprehensive summary fetching with filtering for `get_all_summary`.
-   **Manager (`app/business_logic/purchase_invoice_manager.py`)**:
    -   **`PurchaseInvoiceManager`**:
        -   `_validate_and_prepare_pi_data()`: Validates DTOs, related entities (Vendor, Products, Tax Codes), calculates line item and invoice totals, checks for duplicate vendor invoice numbers.
        -   `create_draft_purchase_invoice()`: Orchestrates validation, internal reference number generation, ORM object creation, and saving of new draft purchase invoices.
        -   `update_draft_purchase_invoice()`: Orchestrates validation and updating of existing draft purchase invoices, including transactional replacement of line items.
        -   `get_invoice_for_dialog()`, `get_invoices_for_listing()`: Functional.
        -   `post_purchase_invoice()`: Remains a stub for future implementation.
-   **UI Dialog (`app/ui/purchase_invoices/purchase_invoice_dialog.py`)**:
    -   **`PurchaseInvoiceDialog`**: Provides the UI for creating new draft purchase invoices and editing existing ones. Includes dynamic calculations for line items and invoice totals, asynchronous loading of selection data (vendors, products, etc.), and interaction with `PurchaseInvoiceManager` to save drafts.

## 5. User Interface Implementation (`app/ui/`)

### 5.1 - 5.6 Existing UI Modules
(Functionality for MainWindow, Accounting, Sales, Customers, Vendors, Products, Reports, Settings (including User/Role management) as detailed in TDS v9.)

### 5.7 Purchase Invoicing UI (`app/ui/purchase_invoices/`) (New Section - Dialog Only)
-   **`PurchaseInvoicesWidget` (Planned/Stub)**:
    -   The main list view for purchase invoices is not yet implemented. This widget will be added to a "Purchases" or similar tab in `MainWindow` in a future step.
-   **`PurchaseInvoiceDialog` (`app/ui/purchase_invoices/purchase_invoice_dialog.py`)**:
    *   Fully functional for creating and editing **draft** purchase invoices.
    *   Header: Vendor selection, Vendor Invoice No., Our Internal Ref No. (auto-generated), dates, currency, exchange rate, notes.
    *   Lines: Table for Product/Service (auto-fills purchase price), Description, Quantity, Unit Price, Discount %, Tax Code, and calculated Subtotal, Tax Amount, Line Total.
    *   Functionality: Asynchronous data loading for dropdowns, dynamic line and invoice total calculations, data validation on save, interaction with `PurchaseInvoiceManager` to persist drafts. The "Save & Approve" button is present but disabled.

## 6. Security Considerations
(No changes from TDS v9. New Purchase Invoice operations would eventually be tied to permissions like 'INVOICE_CREATE', 'INVOICE_EDIT' but with a purchase context.)

## 7. Database Access Implementation (`app/services/`)
-   **`business_services.py`**:
    -   `PurchaseInvoiceService` provides comprehensive data access for `PurchaseInvoice` entities, including methods for fetching summaries and specific lookups useful for duplicate checks and UI population.

## 8. Deployment and Installation
(Unchanged from TDS v9. `initial_data.sql` includes a "purchase_invoice" sequence.)

## 9. Conclusion
This TDS (v10) documents the successful implementation of draft management for Purchase Invoices, including the backend logic in `PurchaseInvoiceManager` and a fully functional `PurchaseInvoiceDialog`. This significantly expands the application's capabilities for managing the procurement side of business operations. The immediate next steps for this module will be to create the `PurchaseInvoicesWidget` for listing these invoices and then to implement the posting logic for purchase invoices, including Journal Entry creation and potential inventory updates.

---
https://drive.google.com/file/d/13hYEwFVHlQaGQ_ws3k3VvmZSWJgP14ep/view?usp=sharing, https://drive.google.com/file/d/18AV-7BrkUwk7kQpr8LFSSHMODP6oFYOs/view?usp=sharing, https://drive.google.com/file/d/18xs17NAMOyJxIIn7YAW5_Hxt_EasmnYe/view?usp=sharing, https://drive.google.com/file/d/19QeRpKKgin37J5wKA6z9wbnCIywmKHXx/view?usp=sharing, https://drive.google.com/file/d/1E_9maYq_-0jngxcKzFVK1WObHkUzXzcn/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221EqAAoEAbBCw8IJfsiko4lSxMlixUIqkw%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1FIkt6wn6Ph29zKa6BjuWg5MymXB3xwBN/view?usp=sharing, https://drive.google.com/file/d/1LcMYtkv9s7XDWf1Z_L0y4Mt2XI-E1ChV/view?usp=sharing, https://drive.google.com/file/d/1MNPYsv6jKlmSA9ka-nthRdxmoGxscNKT/view?usp=sharing, https://drive.google.com/file/d/1OAqRup6_pFNaqSbKhvKZ648LGW_vGNHC/view?usp=sharing, https://drive.google.com/file/d/1XVzr3QcXe8dUm0E1rAGlSEloeiMTusAx/view?usp=sharing, https://drive.google.com/file/d/1YEVuNKs7bEWVD6V-NejsmLXZO4a_Tq6F/view?usp=sharing, https://drive.google.com/file/d/1Yjh1wm8uK13MwHJ8nWWt7fDGt_xUxcfe/view?usp=sharing, https://drive.google.com/file/d/1Z4tCtBnhhgZ9oBxAIVk6Nfh_SMwGNjYX/view?usp=sharing, https://drive.google.com/file/d/1aUkaWoQCRm84Q82zCvXChHy8qlZLIc6r/view?usp=sharing, https://drive.google.com/file/d/1fJ5KRnIXSWh5lggrhch8lCDTMwCz9ixp/view?usp=sharing, https://drive.google.com/file/d/1g0BTPiyYf-TubgZlqVArx3Yf0ScSlKa6/view?usp=sharing, https://drive.google.com/file/d/1hHhfoRDBXO8vzthKpWOjI1vH3ccrCWWk/view?usp=sharing, https://drive.google.com/file/d/1hWa5WsgsdwdIUvsHOHqTzLMD37yAg2yV/view?usp=sharing, https://drive.google.com/file/d/1jEPSW2DlYe3CnFfxcrrxQcS1in-CoZDt/view?usp=sharing, https://drive.google.com/file/d/1knLdNW1a19s2XuSALhNPY4jDAp0YTetr/view?usp=sharing, https://drive.google.com/file/d/1p5dvW05gug-BOoy-YguJARN2LK7ED2Bq/view?usp=sharing, https://drive.google.com/file/d/1sdI2jwTCqouVuonjgOxVkMkeDJb1Luc1/view?usp=sharing, https://drive.google.com/file/d/1yezJl1uC8oDZmnom2iG7Rii5ZcAn4i8N/view?usp=sharing, https://drive.google.com/file/d/1zUWfohK07mrZVPwfjE51rfXlbrSkJWN6/view?usp=sharing

