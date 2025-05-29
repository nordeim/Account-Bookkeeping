# Technical Design Specification Document: SG Bookkeeper (v8)

**Version:** 8.0
**Date:** 2025-05-28 

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version 8, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities. This version specifically details the backend logic and initial UI dialog for **Sales Invoicing (Draft Management)**, alongside previously documented features like Customer, Vendor, Product/Service Management, GST F5 workflow, and Financial Reporting. This document serves as a comprehensive guide for ongoing development, feature enhancement, testing, and maintenance.

### 1.2 Scope
This TDS covers the following aspects of the SG Bookkeeper application:
-   System Architecture: UI, business logic, data access layers, and asynchronous processing.
-   Database Schema: Alignment with `scripts/schema.sql`.
-   Key UI Implementation Patterns: `PySide6` interactions with the asynchronous backend.
-   Core Business Logic: Component structures, including those for Customer, Vendor, Product/Service, and Sales Invoice management.
-   Data Models (SQLAlchemy ORM) and Data Transfer Objects (Pydantic DTOs).
-   Security Implementation: Authentication, authorization, and audit mechanisms.
-   Deployment and Initialization procedures.
-   Current Implementation Status: Highlighting implemented features such as Settings, CoA, Journal Entries, GST workflow, Financial Reports, Customer/Vendor/Product Management, and Sales Invoicing (backend logic and initial dialog).

### 1.3 Intended Audience
(Remains the same as TDS v7)
-   Software Developers, QA Engineers, System Administrators, Technical Project Managers.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application engineered with Python, utilizing PySide6 for its graphical user interface and PostgreSQL for robust data storage. It provides comprehensive accounting for Singaporean SMBs, including double-entry bookkeeping, GST management, interactive financial reporting, and foundational modules for business operations such as Customer, Vendor, Product/Service management, and initial Sales Invoicing capabilities (allowing creation and update of draft invoices). The application emphasizes data integrity, compliance, and user-friendliness. Data structures are defined in `scripts/schema.sql` and seeded by `scripts/initial_data.sql`.

## 2. System Architecture

### 2.1 High-Level Architecture
(Diagram and core description remain the same as TDS v7)

### 2.2 Component Architecture

#### 2.2.1 Core Components (`app/core/`)
(Descriptions remain largely the same as TDS v7. `ApplicationCore` now also instantiates and provides access to `SalesInvoiceService` and `SalesInvoiceManager`.)

#### 2.2.2 Asynchronous Task Management (`app/main.py`)
(Description remains the same as TDS v7)

#### 2.2.3 Services (`app/services/`)
-   **Accounting & Core Services** (as listed in TDS v7).
-   **Tax Services** (as listed in TDS v7).
-   **Business Services (`app/services/business_services.py`)**:
    -   `CustomerService`: Manages `Customer` entity data access.
    -   `VendorService`: Manages `Vendor` entity data access.
    -   `ProductService`: Manages `Product` entity data access.
    -   **`SalesInvoiceService` (New)**: Implements `ISalesInvoiceRepository`. Responsible for CRUD operations on `SalesInvoice` and `SalesInvoiceLine` entities, fetching invoice summaries (with filtering and pagination), and specific lookups (e.g., by invoice number).

#### 2.2.4 Managers (Business Logic) (`app/accounting/`, `app/tax/`, `app/business_logic/`)
-   **Accounting, Tax, Reporting Managers** (as listed in TDS v7).
-   **Business Logic Managers (`app/business_logic/`)**:
    -   `CustomerManager`: Orchestrates customer lifecycle operations.
    -   `VendorManager`: Orchestrates vendor lifecycle operations.
    -   `ProductManager`: Orchestrates product/service lifecycle operations.
    -   **`SalesInvoiceManager` (New details - `app/business_logic/sales_invoice_manager.py`)**: Orchestrates sales invoice lifecycle operations, particularly for draft invoices. Handles validation of invoice data (customer, products, tax codes), calculation of line item totals and tax (using `TaxCalculator`), overall invoice totals (subtotal, tax, grand total), mapping DTOs to ORM models, interaction with `SalesInvoiceService` for persistence, and generation of invoice numbers using `SequenceService` (via DB function). Posting logic (JE creation) is a placeholder.

#### 2.2.5 User Interface (`app/ui/`)
-   **`MainWindow` (`app/ui/main_window.py`)**: Includes "Products & Services" tab. A "Sales" or "Invoicing" tab is conceptually planned but the main list widget might be a stub.
-   **Module Widgets**:
    -   `AccountingWidget`, `SettingsWidget`, `ReportsWidget`, `CustomersWidget`, `VendorsWidget`, `ProductsWidget` (Functional as per TDS v7).
    -   `DashboardWidget`, `BankingWidget` (Remain stubs).
    -   **`SalesInvoicesWidget` (Planned/Stub - `app/ui/sales_invoices/sales_invoices_widget.py`)**: Intended to provide a list view for sales invoices. Currently, a dialog for creating/editing is the primary UI.
-   **Detail Widgets & Dialogs**:
    -   `AccountDialog`, `JournalEntryDialog`, `FiscalYearDialog`, `CustomerDialog`, `VendorDialog`, `ProductDialog` (as in TDS v7).
    -   **`SalesInvoiceTableModel` (New - `app/ui/sales_invoices/sales_invoice_table_model.py`)**: `QAbstractTableModel` subclass for displaying `SalesInvoiceSummaryData`.
    -   **`SalesInvoiceDialog` (New details - `app/ui/sales_invoices/sales_invoice_dialog.py`)**: `QDialog` for creating and editing draft sales invoice details. Includes fields for header information (customer, dates, currency) and a `QTableWidget` for line items (product, description, quantity, price, discount, tax code). Dynamically calculates line totals and invoice totals. Interacts with `SalesInvoiceManager` for saving drafts. Asynchronously populates `QComboBox`es for customers, products, currencies, and tax codes.

### 2.3 Technology Stack
(Same as TDS v7)

### 2.4 Design Patterns
(Same as TDS v7. New Sales Invoice module follows established patterns.)

## 3. Data Architecture

### 3.1 Database Schema Overview
(Remains consistent. `business.sales_invoices` and `business.sales_invoice_lines` tables are now actively used.)

### 3.2 SQLAlchemy ORM Models (`app/models/`)
(`app/models/business/sales_invoice.py` is now actively used.)

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
DTOs for `SalesInvoice` Management have been added and are actively used:
-   `SalesInvoiceLineBaseData`: Common fields for invoice lines.
-   `SalesInvoiceBaseData`: Common fields for invoice header.
-   `SalesInvoiceCreateData(SalesInvoiceBaseData, UserAuditData)`: For creating new invoices.
-   `SalesInvoiceUpdateData(SalesInvoiceBaseData, UserAuditData)`: For updating existing invoices.
-   `SalesInvoiceData`: Full representation of an invoice, including calculated totals and status.
-   `SalesInvoiceSummaryData`: Slim DTO for list views.
-   `TaxCalculationResultData` is used by `SalesInvoiceManager` via `TaxCalculator`.

### 3.4 Data Access Layer Interfaces (`app/services/__init__.py`)
The following interface has been added:
-   **`ISalesInvoiceRepository(IRepository[SalesInvoice, int])`**:
    ```python
    from app.models.business.sales_invoice import SalesInvoice
    from app.utils.pydantic_models import SalesInvoiceSummaryData
    from app.common.enums import InvoiceStatusEnum
    from datetime import date

    class ISalesInvoiceRepository(IRepository[SalesInvoice, int]):
        @abstractmethod
        async def get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]: pass
        
        @abstractmethod
        async def get_all_summary(self, 
                                  customer_id: Optional[int] = None,
                                  status: Optional[InvoiceStatusEnum] = None, 
                                  start_date: Optional[date] = None, 
                                  end_date: Optional[date] = None,
                                  page: int = 1, 
                                  page_size: int = 50
                                 ) -> List[SalesInvoiceSummaryData]: pass
    ```

## 4. Module and Component Specifications

### 4.1 - 4.3 Core Accounting, Tax, Reporting Modules
(Functionality as detailed in TDS v7 remains current.)

### 4.4 Business Operations Modules

#### 4.4.1 Customer Management Module 
(As detailed in TDS v7)

#### 4.4.2 Vendor Management Module
(As detailed in TDS v7)

#### 4.4.3 Product/Service Management Module
(As detailed in TDS v7)

#### 4.4.4 Sales Invoicing Module (Backend and Initial Dialog Implemented)
This module provides capabilities for creating and managing draft sales invoices.
-   **Service (`app/services/business_services.py`)**:
    -   **`SalesInvoiceService`**: Implements `ISalesInvoiceRepository`.
        -   `get_by_id()`: Fetches a `SalesInvoice` ORM, eager-loading lines (with product, tax_code_obj), customer, currency, and audit users.
        -   `get_all_summary()`: Fetches `List[SalesInvoiceSummaryData]` with filtering and pagination.
        -   `save()`: Persists `SalesInvoice` ORM objects, handling cascaded line items.
-   **Manager (`app/business_logic/sales_invoice_manager.py`)**:
    -   **`SalesInvoiceManager`**:
        -   Dependencies: `SalesInvoiceService`, `CustomerService`, `ProductService`, `TaxCodeService`, `TaxCalculator`, `SequenceService`, `ApplicationCore`.
        -   `get_invoice_for_dialog()`: Retrieves full `SalesInvoice` ORM for dialogs.
        -   `get_invoices_for_listing()`: Retrieves `List[SalesInvoiceSummaryData]`.
        -   `_validate_and_prepare_invoice_data()`: Core internal method to validate DTOs, fetch related entities (customer, products, tax codes for each line), calculate line subtotals, discounts, tax per line (using `TaxCalculator`), and then aggregate for invoice header totals (subtotal, total tax, grand total).
        -   `create_draft_invoice(dto: SalesInvoiceCreateData)`: Uses `_validate_and_prepare_invoice_data`. Generates `invoice_no` via `core.get_next_sequence_value` DB function. Maps DTO and calculated data to `SalesInvoice` and `SalesInvoiceLine` ORMs. Sets status to `Draft` and audit IDs, then saves.
        -   `update_draft_invoice(invoice_id: int, dto: SalesInvoiceUpdateData)`: Fetches existing draft invoice. Uses `_validate_and_prepare_invoice_data`. Updates ORM fields, handles replacement of line items (transactionally deletes old lines and adds new ones). Sets audit ID and saves.
        -   `post_invoice(invoice_id: int, user_id: int)`: Currently a placeholder; intended to change status to `Approved`/`Sent`, generate accounting journal entries, and potentially update inventory.

## 5. User Interface Implementation (`app/ui/`)

### 5.1 - 5.4 Core UI, Accounting, Settings, Reports, Customers, Vendors, Products Modules
(Functionality as detailed in TDS v7.)

### 5.5 Sales Invoicing Module UI (`app/ui/sales_invoices/`) (New Section)
-   **`SalesInvoicesWidget` (Planned/Stub)**:
    -   The main list view for sales invoices is not yet fully implemented.
-   **`SalesInvoiceTableModel` (`app/ui/sales_invoices/sales_invoice_table_model.py`)**:
    -   `QAbstractTableModel` subclass.
    -   Manages `List[SalesInvoiceSummaryData]`.
    -   Provides data for columns: ID (hidden), Invoice No., Invoice Date, Due Date, Customer Name, Total Amount, Amount Paid, Balance, Status.
-   **`SalesInvoiceDialog` (`app/ui/sales_invoices/sales_invoice_dialog.py`)**:
    *   `QDialog` for creating or editing (draft) sales invoice details.
    *   **Header Fields**: `QComboBox` for Customer (with completer), `QDateEdit` for Invoice Date and Due Date, `QComboBox` for Currency, `QDoubleSpinBox` for Exchange Rate, `QTextEdit` for Notes and Terms. Displays Invoice No. (generated on save).
    *   **Line Items Table (`QTableWidget`)**: Columns for Delete (button), Product/Service (`QComboBox` with completer), Description (`QLineEdit`), Quantity (`QDoubleSpinBox` via delegate), Unit Price (`QDoubleSpinBox` via delegate), Discount % (`QDoubleSpinBox` via delegate), Line Subtotal (read-only), Tax Code (`QComboBox`), Tax Amount (read-only), Line Total (read-only).
    *   **Dynamic UI & Calculations**:
        *   Line subtotals, tax amounts, and line totals are calculated dynamically as quantity, price, discount, or tax code change for a line.
        *   Invoice subtotal, total tax, and grand total are updated in read-only display fields based on line item changes.
    *   **ComboBox Population**: Asynchronously loads active customers, products (filtered for saleable types), currencies, and tax codes into respective `QComboBox`es during dialog initialization.
    *   **Data Handling**:
        -   In edit mode, loads existing draft invoice data via `SalesInvoiceManager.get_invoice_for_dialog()`.
        -   On save (draft), collects UI data into `SalesInvoiceCreateData` or `SalesInvoiceUpdateData` DTOs. Pydantic validation occurs.
        -   Calls `SalesInvoiceManager.create_draft_invoice()` or `SalesInvoiceManager.update_draft_invoice()` asynchronously.
        -   Displays success/error messages and emits `invoice_saved(invoice_id)` signal.
        -   "Save & Approve" button is present but currently disabled, indicating future functionality for posting.

## 6. Security Considerations
(Unchanged from TDS v7)

## 7. Database Access Implementation (`app/services/`)
-   **`business_services.py`**:
    -   `CustomerService`, `VendorService`, `ProductService` (As detailed in TDS v7).
    -   **`SalesInvoiceService` (New details)**: Implements `ISalesInvoiceRepository`.
        -   `get_by_id()`: Fetches `SalesInvoice` ORM, eager-loading `lines` (with their `product` and `tax_code_obj`), `customer`, `currency`, `journal_entry`, and audit users.
        -   `get_all_summary()`: Fetches `List[SalesInvoiceSummaryData]` with filtering (customer, status, dates) and pagination. Joins with `Customer` to include customer name.
        -   `save()`: Persists `SalesInvoice` ORM objects, managing related `SalesInvoiceLine` items (SQLAlchemy handles cascades based on relationship configuration). This method is designed to be called within a transaction managed by the `SalesInvoiceManager` for operations like updates that involve deleting old lines.

## 8. Deployment and Installation
(Unchanged from TDS v7)

## 9. Conclusion
This TDS (v8) documents further progress, notably the addition of backend logic for managing draft Sales Invoices, including complex calculations and data validation. A functional UI dialog for creating and editing these draft invoices has also been implemented. This complements the existing Customer, Vendor, and Product/Service management modules, laying a critical foundation for transactional accounting. Core accounting, GST workflow, and financial reporting functionalities remain robust. Future iterations will focus on completing the Sales Invoicing lifecycle (posting, payment tracking), implementing Purchase Invoicing, and further enhancing other modules.
