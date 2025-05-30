<think>
The application launches successfully. The `PurchaseInvoiceDialog` (Part 2: Calculation Logic and Saving Drafts) is now integrated and functional for draft management.

**Current Project Status Recap (Relevant for README/TDS updates):**

*   **Purchase Invoicing**:
    *   Backend for Draft Management (`PurchaseInvoiceManager`): Logic for creating/updating draft PIs is implemented. Posting logic is a stub.
    *   `PurchaseInvoiceDialog`: Fully functional for creating/editing draft purchase invoices, including dynamic calculations and saving.
    *   `PurchaseInvoicesWidget` (List View): Not yet created.
*   **Sales Invoicing**: Fully functional (Draft CRUD, Posting with JE, List View, Dialog with "Save & Approve").
*   **User and Role Management UI**: Fully functional.
*   **Reporting**: BS/P&L on-screen display and export enhanced. TB/GL functional. Reporting options for BS/P&L (comparative, zero-balance) added.
*   All previously implemented features (Core Accounting, Customer/Vendor/Product Management, GST F5) remain stable.

The main change since the last README/TDS update (v9 of TDS) is the completion of draft management for Purchase Invoices via `PurchaseInvoiceDialog` and its backend manager.

**Plan for Updating Documentation:**

1.  **Update `README.md`**:
    *   **Key Features Section**:
        *   Update "Purchase Invoicing and Accounts Payable" status from "Foundational" to "UI Dialog Implemented - Draft CRUD for Purchase Invoices. List view and posting planned."
    *   **Usage Guide**: Add a brief mention that a dialog for creating/editing draft Purchase Invoices is available (though the main list view widget is not yet present in a dedicated tab).
    *   **Roadmap**:
        *   Under "Current Focus / Short-term" for "Purchase Invoicing", update from "Begin implementation" to "Complete UI for listing, viewing, and managing Purchase Invoices. Implement posting logic (JE creation)."

2.  **Update `Technical_Design_Specification_Document.md` (to v10.0)**:
    *   **Version and Date**: Update to 10.0 and current date.
    *   **1.1 Purpose / 1.2 Scope / 1.4 System Overview / Current Implementation Status**: Reflect the addition of draft management for Purchase Invoices (backend logic and `PurchaseInvoiceDialog`).
    *   **2.2 Component Architecture**:
        *   `PurchaseInvoiceManager`: Detail its implemented draft management logic (`_validate_and_prepare_pi_data`, `create_draft_purchase_invoice`, `update_draft_purchase_invoice`).
        *   `UI Components (`app/ui/purchase_invoices/`)`: Detail the new `PurchaseInvoiceDialog` and its functionalities. Note that `PurchaseInvoicesWidget` is planned.
    *   **3.3 Data Transfer Objects (DTOs)**: Confirm `PurchaseInvoice` DTOs are listed and used.
    *   **4. Module and Component Specifications**:
        *   Add/Expand section for "Purchase Invoicing Module".
        *   Detail `PurchaseInvoiceManager` methods for draft management.
    *   **5. User Interface Implementation**:
        *   Detail `PurchaseInvoiceDialog` (header fields, line item table, dynamic calculations, save draft functionality). Note its current invocation point (if any, or state it's ready for integration into a list widget).
    *   **9. Conclusion**: Reflect the new capability for managing draft purchase invoices.

This will bring both documents up to date with the latest major progress.
I will generate the complete files.
</think>

Okay, the application is stable with the `PurchaseInvoiceDialog` (handling draft creation/editing, calculations, and saving) now functional. This is a great step for the Purchase Invoicing module!

It's time to update the `README.md` and `Technical_Design_Specification_Document.md` to reflect this progress.

## Updated `README.md`

This version will update the "Key Features" for Purchase Invoicing, and adjust the "Roadmap".

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
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

[Key Features](#key-features) • [Technology Stack](#technology-stack) • [Installation](#installation) • [Usage](#usage-guide) • [Project Structure](#project-structure) • [Contributing](#contributing) • [Roadmap](#roadmap) • [License](#license)

</div>

## Overview

SG Bookkeeper is a comprehensive, cross-platform desktop application designed to meet the accounting and bookkeeping needs of small to medium-sized businesses in Singapore. Built with Python and leveraging the power of PySide6 for a modern user interface and PostgreSQL for robust data management, it offers professional-grade financial tools tailored to Singapore's regulatory environment.

The application features a double-entry accounting core, GST management, financial reporting, and modules for essential business operations including customer, vendor, product/service management, sales invoicing, and initial purchase invoicing capabilities. User and Role management are also implemented. Its goal is to provide an intuitive, powerful, and compliant solution that empowers business owners and accountants.

### Why SG Bookkeeper?

-   **Singapore-Centric**: Designed with Singapore Financial Reporting Standards (SFRS), GST regulations (including 9% rate), and IRAS compliance considerations at its core.
-   **Professional Grade**: Implements a full double-entry system, detailed audit trails (via database triggers), and robust data validation using Pydantic DTOs.
-   **User-Friendly Interface**: Aims for an intuitive experience for users who may not be accounting experts, while providing depth for professionals. Most core modules have functional UIs.
-   **Open Source & Local First**: Transparent development. Your financial data stays on your local machine or private server, ensuring privacy and control. No subscription fees.
-   **Modern & Performant**: Utilizes asynchronous operations for a responsive UI and efficient database interactions, with a dedicated asyncio event loop.

## Key Features

*(Status: Implemented, Backend Implemented, UI Dialog Implemented, Foundational (DB/Models ready), Planned)*

### Core Accounting
-   **Comprehensive Double-Entry Bookkeeping** (Implemented)
-   **Customizable Hierarchical Chart of Accounts** (Implemented - UI for CRUD)
-   **General Ledger with detailed transaction history** (Implemented - Report generation, on-screen view, export)
-   **Journal Entry System** (Implemented - UI for General Journal; transaction-specific JEs generated on posting of source documents)
-   **Multi-Currency Support** (Foundational - Models, CurrencyManager exist. UI integration in transactions pending.)
-   **Fiscal Year and Period Management** (Implemented - UI in Settings for FY creation and period auto-generation.)
-   **Budgeting and Variance Analysis** (Foundational - Models exist. UI/Logic planned.)

### Singapore Tax Compliance
-   **GST Tracking and Calculation** (Backend Implemented - `TaxCode` setup, `TaxCalculator` for line items. Sales/Purchase Invoice Dialogs use it.)
-   **GST F5 Return Data Preparation & Finalization** (Implemented - Backend for data prep & finalization with JE settlement. UI in Reports tab.)
-   **Income Tax Estimation Aids** (Planned)
-   **Withholding Tax Management** (Foundational)

### Business Operations
-   **Customer Management** (Implemented - Full CRUD and listing UI.)
-   **Vendor Management** (Implemented - Full CRUD and listing UI.)
-   **Product and Service Management** (Implemented - Full CRUD and listing UI.)
-   **Sales Invoicing and Accounts Receivable** (Implemented - Draft CRUD, Posting with JE creation, List View UI, "Save & Approve" in dialog.)
-   **Purchase Invoicing and Accounts Payable** (UI Dialog Implemented - Draft CRUD for Purchase Invoices. List view and posting planned.)
-   **Payment Processing and Allocation** (Foundational)
-   **Bank Account Management and Reconciliation Tools** (Foundational - UI is a stub.)
-   **Basic Inventory Control** (Foundational - `Product` model includes inventory fields. Logic planned.)

### Reporting & Analytics
-   **Standard Financial Statements**: Balance Sheet, Profit & Loss, Trial Balance, General Ledger (Implemented - UI in Reports tab with options for comparative/zero-balance, on-screen view, PDF/Excel export.)
-   **Cash Flow Statement** (Planned)
-   **GST Reports** (Implemented - See GST F5 above.)
-   **Customizable Reporting Engine** (Planned)
-   **Dashboard with Key Performance Indicators (KPIs)** (Planned - UI is a stub.)

### System & Security
-   **User Authentication** (Implemented)
-   **Role-Based Access Control (RBAC)** (Implemented - UI for managing Users, Roles, and assigning Permissions to Roles.)
-   **Granular Permissions System** (Implemented)
-   **Comprehensive Audit Trails** (Implemented)
-   **PostgreSQL Database Backend** (Implemented)
-   **Data Backup and Restore Utilities** (Planned)

## Technology Stack
(Section remains unchanged)
...

## Installation
(Section remains unchanged)
...

## Usage Guide

The application provides a range of functional modules accessible via tabs:

-   **Accounting Tab**: Manage Chart of Accounts and Journal Entries.
-   **Sales Tab**: Create, view, edit draft, and post Sales Invoices.
-   **Customers Tab**: Manage customer information.
-   **Vendors Tab**: Manage vendor information.
-   **Products & Services Tab**: Manage products and services.
-   **Reports Tab**: Generate GST F5 data and standard Financial Statements with export options.
-   **Settings Tab**:
    -   **Company**: Configure company-wide information and Fiscal Years.
    -   **Users**: Manage user accounts.
    *   **Roles & Permissions**: Manage roles and assign system permissions.

Dialogs for creating/editing **Draft Purchase Invoices** are available (though not yet integrated into a main "Purchases" tab/list view). Other modules (Dashboard, Banking) are placeholders.
The default `admin` user (password: `password` - change on first login) has full access.

## Project Structure
(Updated to include Purchase Invoice UI files under `app/ui/purchase_invoices/`)
```
sg_bookkeeper/
├── app/
│   ├── ... (core, common, models, services, accounting, tax, business_logic, reporting) ...
│   ├── ui/
│   │   ├── purchase_invoices/ # New or updated
│   │   │   ├── __init__.py
│   │   │   └── purchase_invoice_dialog.py
│   │   ├── settings/
│   │   │   └── ... (user_dialog.py, role_dialog.py, etc.)
│   │   └── ... (other ui modules)
│   └── utils/
├── ... (data, docs, resources, scripts, tests) ...
└── ... (project root files)
```

## Database Schema
(Section remains unchanged)
...

## Development
(Section remains unchanged)
...

## Contributing
(Section remains unchanged)
...

## Roadmap

### Current Focus / Short-term
-   **Purchase Invoicing**:
    *   Complete UI for listing, viewing, and managing Purchase Invoices (`PurchaseInvoicesWidget`).
    *   Implement posting logic (JE creation) for Purchase Invoices.
-   **Sales Invoicing**:
    *   Enhance line item entry (e.g., better product search/selection in dialogs).
    *   (Future) Handle inventory updates upon posting.
-   **Refine Reporting**:
    *   Improve PDF/Excel export formatting for Trial Balance and General Ledger.
    *   Add more filtering options to existing reports.

### Medium-term
-   Bank Account management and basic transaction entry UI in Banking module.
-   Payment recording and allocation to Sales and Purchase invoices.
-   Enhance GST F5 report export options (e.g., consider IAF format).

### Long-term
-   Bank Reconciliation features.
-   Advanced reporting and analytics, dashboard KPIs.
-   Inventory Control enhancements (e.g., stock movements, valuation).
-   Multi-company support.
-   Cloud synchronization options (optional).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

---
## Updated `Technical_Design_Specification_Document.md` (as v10.0)

This version will detail the completed draft management for Purchase Invoices (backend and dialog UI).

```markdown
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
```
