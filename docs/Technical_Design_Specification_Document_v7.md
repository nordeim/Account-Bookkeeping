# Technical Design Specification Document: SG Bookkeeper (v7)

**Version:** 7.0
**Date:** 2025-05-27 <!-- Or current date -->

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version 7, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities. This version specifically details the addition of basic Product/Service Management capabilities (backend and UI), alongside previously documented features like Customer and Vendor Management, GST F5 workflow, and Financial Reporting. This document serves as a comprehensive guide for ongoing development, feature enhancement, testing, and maintenance.

### 1.2 Scope
This TDS covers the following aspects of the SG Bookkeeper application:
-   System Architecture: UI, business logic, data access layers, and asynchronous processing.
-   Database Schema: Alignment with `scripts/schema.sql`.
-   Key UI Implementation Patterns: `PySide6` interactions with the asynchronous backend.
-   Core Business Logic: Component structures, including those for Customer, Vendor, and Product/Service management.
-   Data Models (SQLAlchemy ORM) and Data Transfer Objects (Pydantic DTOs).
-   Security Implementation: Authentication, authorization, and audit mechanisms.
-   Deployment and Initialization procedures.
-   Current Implementation Status: Highlighting implemented features such as Settings, CoA, Journal Entries, GST workflow, Financial Reports, Customer Management, Vendor Management, and basic Product/Service Management.

### 1.3 Intended Audience
(Remains the same as TDS v6)
-   Software Developers, QA Engineers, System Administrators, Technical Project Managers.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application engineered with Python, utilizing PySide6 for its graphical user interface and PostgreSQL for robust data storage. It provides comprehensive accounting for Singaporean SMBs, including double-entry bookkeeping, GST management, interactive financial reporting, and foundational modules for business operations such as Customer Management, Vendor Management, and basic Product/Service Management (all allowing view, add, edit, toggle active status). The application emphasizes data integrity, compliance, and user-friendliness. Data structures are defined in `scripts/schema.sql` and seeded by `scripts/initial_data.sql`.

## 2. System Architecture

### 2.1 High-Level Architecture
(Diagram and core description remain the same as TDS v6)

### 2.2 Component Architecture

#### 2.2.1 Core Components (`app/core/`)
(Descriptions remain largely the same as TDS v6. `ApplicationCore` now also instantiates and provides access to `ProductService` and `ProductManager`.)

#### 2.2.2 Asynchronous Task Management (`app/main.py`)
(Description remains the same as TDS v6)

#### 2.2.3 Services (`app/services/`)
-   **Accounting & Core Services** (as listed in TDS v6).
-   **Tax Services** (as listed in TDS v6).
-   **Business Services (`app/services/business_services.py`)**:
    -   `CustomerService`: Manages `Customer` entity data access.
    -   `VendorService`: Manages `Vendor` entity data access.
    -   **`ProductService` (New)**: Implements `IProductRepository`. Responsible for basic CRUD operations, fetching product/service summaries (with filtering and pagination), and specific lookups for `Product` entities.

#### 2.2.4 Managers (Business Logic) (`app/accounting/`, `app/tax/`, `app/business_logic/`)
-   **Accounting, Tax, Reporting Managers** (as listed in TDS v6).
-   **Business Logic Managers (`app/business_logic/`)**:
    -   `CustomerManager`: Orchestrates customer lifecycle operations.
    -   `VendorManager`: Orchestrates vendor lifecycle operations.
    -   **`ProductManager` (New details - `app/business_logic/product_manager.py`)**: Orchestrates product/service lifecycle operations. Handles validation (e.g., product code uniqueness, valid GL accounts based on product type, valid tax code), maps DTOs to ORM models, interacts with `ProductService` for persistence, and manages active status.

#### 2.2.5 User Interface (`app/ui/`)
-   **`MainWindow` (`app/ui/main_window.py`)**: Now includes a "Products & Services" tab.
-   **Module Widgets**:
    -   `AccountingWidget`, `SettingsWidget`, `ReportsWidget`, `CustomersWidget`, `VendorsWidget` (Functional as per TDS v6).
    -   **`ProductsWidget` (New - `app/ui/products/products_widget.py`)**: Provides a `QTableView` (using `ProductTableModel`) to list products/services. Includes a toolbar with "Add", "Edit", "Toggle Active", "Refresh" actions, and filter controls (search, product type, active status). Interacts with `ProductManager` and `ProductDialog`.
    -   `DashboardWidget`, `BankingWidget` (Remain stubs).
-   **Detail Widgets & Dialogs**:
    -   `AccountDialog`, `JournalEntryDialog`, `FiscalYearDialog`, `CustomerDialog`, `VendorDialog` (as in TDS v6).
    -   **`ProductTableModel` (New - `app/ui/products/product_table_model.py`)**: `QAbstractTableModel` subclass for displaying `ProductSummaryData` in `ProductsWidget`.
    -   **`ProductDialog` (New - `app/ui/products/product_dialog.py`)**: `QDialog` for adding and editing product/service details. Includes fields for all product attributes, dynamically adapts UI based on `ProductType` (e.g., inventory-specific fields), asynchronously populates `QComboBox`es for related accounts and tax codes, validates input, and interacts with `ProductManager` for saving.

### 2.3 Technology Stack
(Same as TDS v6)

### 2.4 Design Patterns
(Same as TDS v6. New Product module follows established patterns.)

## 3. Data Architecture

### 3.1 Database Schema Overview
(Remains consistent. `business.products` table is now actively used.)

### 3.2 SQLAlchemy ORM Models (`app/models/`)
(`app/models/business/product.py` is now actively used.)

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
DTOs for `Product/Service` Management have been added and are actively used:
-   `ProductBaseData`, `ProductCreateData`, `ProductUpdateData`, `ProductData`, `ProductSummaryData`. (Details of fields as per `pydantic_models.py` which include `product_type` enum validation and conditional logic for inventory fields).

### 3.4 Data Access Layer Interfaces (`app/services/__init__.py`)
The following interface has been added:
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

### 4.1 - 4.3 Core Accounting, Tax, Reporting Modules
(Functionality as detailed in TDS v6 remains current for these modules.)

### 4.4 Business Operations Modules

#### 4.4.1 Customer Management Module 
(As detailed in TDS v6)

#### 4.4.2 Vendor Management Module
(As detailed in TDS v6)

#### 4.4.3 Product/Service Management Module (Backend and Basic UI Implemented)
This module provides capabilities for managing product and service items.
-   **Service (`app/services/business_services.py`)**:
    -   **`ProductService`**: Implements `IProductRepository`.
        -   `get_by_id()`: Fetches a `Product` ORM, eager-loading related accounts (sales, purchase, inventory) and `tax_code_obj`.
        -   `get_all_summary()`: Fetches `List[ProductSummaryData]` with filtering (active, product type, search on code/name/description) and pagination.
        -   `save()`: Persists `Product` ORM objects.
-   **Manager (`app/business_logic/product_manager.py`)**:
    -   **`ProductManager`**:
        -   Dependencies: `ProductService`, `AccountService` (for GL account validation), `TaxCodeService` (for tax code validation), `ApplicationCore`.
        -   `get_product_for_dialog()`: Retrieves full `Product` ORM for dialogs.
        -   `get_products_for_listing()`: Retrieves `List[ProductSummaryData]` for table display.
        -   `create_product(dto: ProductCreateData)`: Validates (code uniqueness, FKs for GL accounts based on product type, tax code). Maps DTO to `Product` ORM (handles `ProductTypeEnum.value`), sets audit IDs, saves.
        -   `update_product(product_id: int, dto: ProductUpdateData)`: Fetches, validates, updates ORM, sets audit ID, saves.
        -   `toggle_product_active_status(product_id: int, user_id: int)`: Toggles `is_active` and saves.

## 5. User Interface Implementation (`app/ui/`)

### 5.1 - 5.3 Core UI Components (MainWindow, Accounting, Settings, Reports, Customers, Vendors)
(Functionality for Reports, Customers, Vendors as detailed in TDS v6. Other core UI unchanged.)

### 5.4 Products & Services Module UI (`app/ui/products/`) (New Section)
-   **`ProductsWidget` (`app/ui/products/products_widget.py`)**:
    -   The main UI for managing products and services, accessed via a dedicated tab in `MainWindow`.
    -   **Layout**: Features a toolbar for common actions, a filter area, and a `QTableView`.
    -   **Toolbar**: Includes "Add Product/Service", "Edit", "Toggle Active", and "Refresh List" actions.
    *   **Filter Area**: Allows filtering by a text search term (acting on product code, name, description), `ProductTypeEnum` (Inventory, Service, Non-Inventory via a `QComboBox`), and an "Show Inactive" `QCheckBox`. A "Clear Filters" button resets filters.
    -   **Table View**: Uses `ProductTableModel` to display product/service summaries (ID (hidden), Code, Name, Type, Sales Price, Purchase Price, Active status). Supports column sorting. Double-clicking a row opens the item for editing.
    -   **Data Flow**:
        -   `_load_products()`: Triggered on init and by filter changes/refresh. Asynchronously calls `ProductManager.get_products_for_listing()` with current filter parameters.
        -   `_update_table_model_slot()`: Receives `List[ProductSummaryData]` (as JSON string from async call), parses it, and updates `ProductTableModel`.
    -   **Actions**:
        -   Add/Edit actions launch `ProductDialog`.
        -   Toggle Active calls `ProductManager.toggle_product_active_status()`.
        -   All backend interactions are asynchronous, with UI updates handled safely.
-   **`ProductTableModel` (`app/ui/products/product_table_model.py`)**:
    -   `QAbstractTableModel` subclass.
    -   Manages `List[ProductSummaryData]`.
    -   Provides data for columns: ID, Code, Name, Type (displays enum value), Sales Price (formatted), Purchase Price (formatted), Active (Yes/No).
-   **`ProductDialog` (`app/ui/products/product_dialog.py`)**:
    *   `QDialog` for creating or editing product/service details.
    *   **Fields**: Includes inputs for all attributes defined in `ProductBaseData` (code, name, description, product type, category, UoM, barcode, prices, linked GL accounts, tax code, stock levels, active status).
    *   **Dynamic UI**: The visibility and applicability of `inventory_account_id`, `min_stock_level`, and `reorder_point` fields are dynamically controlled based on the selected `ProductType` (enabled for "Inventory", disabled/cleared otherwise).
    *   **ComboBox Population**: Asynchronously loads active accounts (filtered by appropriate types like Revenue for sales GL, Expense/Asset for purchase GL, Asset for inventory GL) and active tax codes into respective `QComboBox`es during dialog initialization.
    *   **Data Handling**:
        -   In edit mode, loads existing product data via `ProductManager.get_product_for_dialog()`.
        -   On save, collects UI data into `ProductCreateData` or `ProductUpdateData` DTOs. Pydantic validation occurs.
        -   Calls `ProductManager.create_product()` or `ProductManager.update_product()` asynchronously.
        -   Displays success/error messages and emits `product_saved(product_id)` signal.

## 6. Security Considerations
(Unchanged from TDS v6)

## 7. Database Access Implementation (`app/services/`)
-   **`business_services.py`**:
    -   `CustomerService`, `VendorService` (As detailed in TDS v6).
    -   **`ProductService` (New details)**: Implements `IProductRepository`.
        -   `get_by_id()`: Fetches `Product` ORM, eager-loading `sales_account`, `purchase_account`, `inventory_account`, `tax_code_obj`, and audit users.
        -   `get_all_summary()`: Fetches `List[ProductSummaryData]` with filtering (active, product type, search term) and pagination.
        -   Other methods (`get_by_code`, `save`) provide standard repository functionality for `Product` entities.

## 8. Deployment and Installation
(Unchanged from TDS v6)

## 9. Conclusion
This TDS (v7) documents further significant progress in SG Bookkeeper's development. The core feature set has been expanded with the implementation of basic Product/Service Management (backend and UI), complementing the existing Customer and Vendor management modules. The application now offers a more rounded suite for managing key business entities alongside its robust accounting, GST, and reporting functionalities. The architecture remains stable and continues to support asynchronous operations and clear component responsibilities. Future iterations will focus on building transactional modules (like Invoicing) that leverage these foundational data entities.

