# Technical Design Specification Document: SG Bookkeeper (v6)

**Version:** 6.0
**Date:** 2025-05-27 <!-- Or current date -->

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version 6, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities observed in the existing codebase. This version specifically details the addition of basic Vendor Management capabilities, alongside previously documented features like Customer Management, GST F5 workflow, and Financial Reporting. This document serves as a comprehensive guide for ongoing development, feature enhancement, testing, and maintenance.

### 1.2 Scope
This TDS covers the following aspects of the SG Bookkeeper application:
-   System Architecture: UI, business logic, data access layers, and asynchronous processing.
-   Database Schema: Alignment with `scripts/schema.sql`.
-   Key UI Implementation Patterns: `PySide6` interactions with the asynchronous backend.
-   Core Business Logic: Component structures, including those for Customer and Vendor management.
-   Data Models (SQLAlchemy ORM) and Data Transfer Objects (Pydantic DTOs).
-   Security Implementation: Authentication, authorization, and audit mechanisms.
-   Deployment and Initialization procedures.
-   Current Implementation Status: Highlighting implemented features such as Settings, CoA, Journal Entries, GST workflow, Financial Reports, Customer Management, and Vendor Management.

### 1.3 Intended Audience
(Remains the same as TDS v5)
-   Software Developers, QA Engineers, System Administrators, Technical Project Managers.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application engineered with Python, utilizing PySide6 for its graphical user interface and PostgreSQL for robust data storage. It provides comprehensive accounting for Singaporean SMBs, including double-entry bookkeeping, GST management (preparation & finalization), interactive financial reporting (BS, P&L, TB, GL), and foundational modules for business operations such as Customer Management and Vendor Management (both allowing view, add, edit, toggle active status). The application emphasizes data integrity, compliance, and user-friendliness. Data structures are defined in `scripts/schema.sql` and seeded by `scripts/initial_data.sql`.

## 2. System Architecture

### 2.1 High-Level Architecture
(Diagram and core description remain the same as TDS v5)

### 2.2 Component Architecture

#### 2.2.1 Core Components (`app/core/`)
(Descriptions remain largely the same as TDS v5. `ApplicationCore` now also instantiates and provides access to `VendorService` and `VendorManager`.)

#### 2.2.2 Asynchronous Task Management (`app/main.py`)
(Description remains the same as TDS v5)

#### 2.2.3 Services (`app/services/`)
Services implement repository patterns for data access.
-   **Accounting & Core Services** (as listed in TDS v5).
-   **Tax Services** (as listed in TDS v5).
-   **Business Services (`app/services/business_services.py`)**:
    -   `CustomerService`: Manages `Customer` entity data access.
    -   **`VendorService` (New)**: Implements `IVendorRepository`. Responsible for basic CRUD operations, fetching vendor summaries (with filtering and pagination), and specific lookups for `Vendor` entities.

#### 2.2.4 Managers (Business Logic) (`app/accounting/`, `app/tax/`, `app/business_logic/`)
-   **Accounting Managers** (as listed in TDS v5).
-   **Tax Managers** (as listed in TDS v5, `GSTManager` functionality for prep & finalize is complete).
-   **Reporting Managers** (as listed in TDS v5, `FinancialStatementGenerator` and `ReportEngine` now support GL and are UI-driven).
-   **Business Logic Managers (`app/business_logic/`)**:
    -   `CustomerManager`: Orchestrates customer lifecycle operations.
    -   **`VendorManager` (New - `app/business_logic/vendor_manager.py`)**: Orchestrates vendor lifecycle operations. Handles validation (e.g., vendor code uniqueness, valid foreign keys for AP account and currency), maps DTOs to ORM models, interacts with `VendorService` for persistence, and manages vendor active status.
    -   **`ProductManager` (New - `app/business_logic/product_manager.py` - Backend only)**: Orchestrates product/service lifecycle operations. Handles validation, DTO mapping, and interacts with `ProductService`. UI is planned.

#### 2.2.5 User Interface (`app/ui/`)
-   **`MainWindow` (`app/ui/main_window.py`)**
-   **Module Widgets**:
    -   `AccountingWidget`, `SettingsWidget`, `ReportsWidget` (with GST Finalization and full Financial Statements UI as per TDS v5).
    -   `CustomersWidget` (Functional as per TDS v5).
    -   **`VendorsWidget` (Enhanced - `app/ui/vendors/vendors_widget.py`)**: No longer a stub. Provides a `QTableView` (using `VendorTableModel`) to list vendors, a toolbar with "Add", "Edit", "Toggle Active", "Refresh" actions, and basic search/filter controls. Interacts with `VendorManager` and `VendorDialog`.
    -   `DashboardWidget`, `BankingWidget`, `ProductsWidget` (Remain stubs or UI not yet implemented).
-   **Detail Widgets & Dialogs**:
    -   `AccountDialog`, `JournalEntryDialog`, `FiscalYearDialog`, `CustomerDialog` (as in TDS v5).
    -   **`VendorTableModel` (New - `app/ui/vendors/vendor_table_model.py`)**: `QAbstractTableModel` subclass for displaying `VendorSummaryData` in `VendorsWidget`.
    -   **`VendorDialog` (New - `app/ui/vendors/vendor_dialog.py`)**: `QDialog` for adding and editing vendor details. Includes fields for all vendor attributes, asynchronously populates `QComboBox`es for currency and A/P accounts, validates input, and interacts with `VendorManager` for saving.
    -   `ProductTableModel`, `ProductDialog` (Foundational files created, full UI widget pending).


### 2.3 Technology Stack
(Same as TDS v5, `email-validator` via `pydantic[email]` confirmed)

### 2.4 Design Patterns
(Same as TDS v5. Vendor and Product modules follow established patterns.)

## 3. Data Architecture

### 3.1 Database Schema Overview
(Remains consistent with `scripts/schema.sql`. The `business.vendors` and `business.products` tables are now actively used by backend components.)

### 3.2 SQLAlchemy ORM Models (`app/models/`)
(Structure remains. `app/models/business/vendor.py` and `app/models/business/product.py` are now actively used by new backend services/managers.)

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
The following DTOs have been added to support Vendor and Product/Service Management:
-   **Vendor DTOs**:
    -   `VendorBaseData`, `VendorCreateData`, `VendorUpdateData`, `VendorData`, `VendorSummaryData`. These mirror the Customer DTOs in structure and purpose, tailored for vendor attributes (e.g., `payables_account_id`, WHT fields).
-   **Product/Service DTOs**:
    -   `ProductBaseData`, `ProductCreateData`, `ProductUpdateData`, `ProductData`, `ProductSummaryData`. These cater to product/service attributes, including `product_type` (using `ProductTypeEnum`), pricing, linked GL accounts, and inventory-specific fields. Root validators ensure consistency (e.g., `inventory_account_id` required only for 'Inventory' type).

### 3.4 Data Access Layer Interfaces (`app/services/__init__.py`)
The following interfaces have been added:
-   **`ICustomerRepository(IRepository[Customer, int])`**: (As defined in TDS v5)
-   **`IVendorRepository(IRepository[Vendor, int])`**:
    ```python
    from app.models.business.vendor import Vendor
    from app.utils.pydantic_models import VendorSummaryData

    class IVendorRepository(IRepository[Vendor, int]):
        @abstractmethod
        async def get_by_code(self, code: str) -> Optional[Vendor]: pass
        
        @abstractmethod
        async def get_all_summary(self, active_only: bool = True,
                                  search_term: Optional[str] = None,
                                  page: int = 1, page_size: int = 50
                                 ) -> List[VendorSummaryData]: pass
    ```
-   **`IProductRepository(IRepository[Product, int])`**:
    ```python
    from app.models.business.product import Product
    from app.utils.pydantic_models import ProductSummaryData
    from app.common.enums import ProductTypeEnum

    class IProductRepository(IRepository[Product, int]):
        @abstractmethod
        async def get_by_code(self, code: str) -> Optional[Product]: pass
        
        @abstractmethod
        async def get_all_summary(self, 
                                  active_only: bool = True,
                                  product_type_filter: Optional[ProductTypeEnum] = None,
                                  search_term: Optional[str] = None,
                                  page: int = 1, 
                                  page_size: int = 50
                                 ) -> List[ProductSummaryData]: pass
    ```

## 4. Module and Component Specifications

### 4.1 Core Accounting Module (Unchanged from TDS v5 details)
### 4.2 Tax Management Module (Unchanged from TDS v5 details for `GSTManager`)
### 4.3 Financial Reporting Module (Unchanged from TDS v5 details for `FinancialStatementGenerator`, `ReportEngine`)

### 4.4 Business Operations Modules

#### 4.4.1 Customer Management Module
(As detailed in TDS v5, functionality is considered complete for basic CRUD and listing.)

#### 4.4.2 Vendor Management Module (New Section)
This module provides basic CRUD operations for vendor entities, mirroring the Customer module.
-   **Service (`app/services/business_services.py`)**:
    -   **`VendorService`**: Implements `IVendorRepository`.
        -   `get_by_id()`: Fetches a `Vendor` ORM, eager-loading `currency`, `payables_account`, and audit users.
        -   `get_all_summary()`: Fetches `List[VendorSummaryData]` with filtering (active, search on code/name/email) and pagination.
        -   `save()`: Persists `Vendor` ORM objects.
-   **Manager (`app/business_logic/vendor_manager.py`)**:
    -   **`VendorManager`**:
        -   Dependencies: `VendorService`, `AccountService` (for AP account validation), `CurrencyService` (for currency validation), `ApplicationCore`.
        -   `get_vendor_for_dialog()`: Retrieves full `Vendor` ORM for dialogs.
        -   `get_vendors_for_listing()`: Retrieves `List[VendorSummaryData]` for table display.
        -   `create_vendor(dto: VendorCreateData)`: Validates DTO and business rules (code uniqueness, FKs like payables account, currency). Maps DTO to `Vendor` ORM, sets audit IDs, saves.
        -   `update_vendor(vendor_id: int, dto: VendorUpdateData)`: Fetches, validates changes, updates ORM, sets audit ID, saves.
        -   `toggle_vendor_active_status(vendor_id: int, user_id: int)`: Toggles `is_active` flag and saves.

#### 4.4.3 Product/Service Management Module (Backend Implemented)
This module provides backend logic for managing products and services. UI is planned.
-   **Service (`app/services/business_services.py`)**:
    -   **`ProductService`**: Implements `IProductRepository`.
        -   `get_by_id()`: Fetches `Product` ORM, eager-loading related accounts (sales, purchase, inventory) and `tax_code_obj`.
        -   `get_all_summary()`: Fetches `List[ProductSummaryData]` with filtering (active, product type, search on code/name/description) and pagination.
        -   `save()`: Persists `Product` ORM objects.
-   **Manager (`app/business_logic/product_manager.py`)**:
    -   **`ProductManager`**:
        -   Dependencies: `ProductService`, `AccountService` (for GL account validation), `TaxCodeService` (for tax code validation), `ApplicationCore`.
        -   `get_product_for_dialog()`: Retrieves full `Product` ORM.
        -   `get_products_for_listing()`: Retrieves `List[ProductSummaryData]`.
        -   `create_product(dto: ProductCreateData)`: Validates (code uniqueness, FKs for GL accounts based on product type, tax code). Maps DTO to `Product` ORM (handles `ProductTypeEnum.value`), sets audit IDs, saves.
        -   `update_product(product_id: int, dto: ProductUpdateData)`: Fetches, validates, updates ORM, sets audit ID, saves.
        -   `toggle_product_active_status(product_id: int, user_id: int)`: Toggles `is_active` and saves.


## 5. User Interface Implementation (`app/ui/`)

### 5.1 Core UI Components (MainWindow, Accounting, Settings, Reports)
(ReportsWidget now includes functional GST Finalization and full Financial Statements UI, as detailed in TDS v5).

### 5.2 Customers Module UI (`app/ui/customers/`)
(As detailed in TDS v5, functionality is considered complete for basic listing, add, edit, toggle active.)

### 5.3 Vendors Module UI (`app/ui/vendors/`) (New Section)
-   **`VendorsWidget` (`app/ui/vendors/vendors_widget.py`)**:
    -   Main UI for vendor management, structurally similar to `CustomersWidget`.
    -   Contains a toolbar ("Add", "Edit", "Toggle Active", "Refresh"), filter area (`QLineEdit` for search, `QCheckBox` for "Show Inactive"), and a `QTableView`.
    -   Uses `VendorTableModel` to display vendor summaries.
    -   `_load_vendors()`: Asynchronously calls `VendorManager.get_vendors_for_listing()` with filter parameters and updates the table model.
    -   Action slots interact with `VendorDialog` (for Add/Edit) and `VendorManager` (for Toggle Active/Refresh).
-   **`VendorTableModel` (`app/ui/vendors/vendor_table_model.py`)**:
    -   `QAbstractTableModel` subclass displaying `VendorSummaryData` (ID (hidden), Code, Name, Email, Phone, Active status).
-   **`VendorDialog` (`app/ui/vendors/vendor_dialog.py`)**:
    *   `QDialog` for adding/editing vendors.
    *   Fields for all `Vendor` attributes (code, name, contact, address, payment terms, bank details, WHT info, currency, A/P account).
    *   Asynchronously populates `QComboBox`es for "Default Currency" and "A/P Account" (Liability type accounts).
    *   Loads existing vendor data via `VendorManager.get_vendor_for_dialog()`.
    *   Collects data into `VendorCreateData`/`VendorUpdateData` DTOs, calls `VendorManager` for persistence. Emits `vendor_saved(vendor_id)` signal.

### 5.4 Products & Services Module UI (`app/ui/products/`) (Foundational Files Created)
-   **`ProductTableModel` (`app/ui/products/product_table_model.py`)**: Created to display `ProductSummaryData`.
-   **`ProductDialog` (`app/ui/products/product_dialog.py`)**: Created with input fields for product attributes. Includes logic for dynamic UI changes based on `ProductType` (e.g., showing inventory fields only for "Inventory" type) and for asynchronously loading related accounts and tax codes into comboboxes.
-   **`ProductsWidget` (`app/ui/products/products_widget.py`)**: Currently a stub. Future work will implement the list view and connect it to `ProductTableModel`, `ProductDialog`, and `ProductManager`.

## 6. Security Considerations
(Unchanged from TDS v5)

## 7. Database Access Implementation (`app/services/`)
-   **`business_services.py`**:
    -   **`CustomerService`**: As detailed in TDS v5.
    -   **`VendorService` (New)**: Implements `IVendorRepository`. Provides `get_by_id`, `get_all_summary` (with filtering for active status, search term, and pagination), `get_by_code`, and `save` methods for `Vendor` entities.
    -   **`ProductService` (New)**: Implements `IProductRepository`. Provides `get_by_id`, `get_all_summary` (with filtering for active status, product type, search term, and pagination), `get_by_code`, and `save` methods for `Product` entities.

## 8. Deployment and Installation
(Unchanged from TDS v5)

## 9. Conclusion
This TDS (v6) documents a significantly more capable SG Bookkeeper application. Key advancements include the full backend implementation for Product/Service Management and the completion of a basic, functional UI for Vendor Management, mirroring the Customer module. Core accounting features, GST F5 workflow, and financial reporting UIs remain stable and robust. The application's architecture consistently supports asynchronous operations and clear separation of concerns. Future efforts will focus on building out the UI for Product/Service Management, implementing transactional modules like Invoicing, and further refining existing features.
