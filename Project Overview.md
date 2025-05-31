## SG Bookkeeper Project

**1. Core Purpose & Target Audience:**

SG Bookkeeper is a cross-platform (Windows, macOS, Linux) desktop application designed to provide comprehensive accounting and bookkeeping solutions specifically tailored for Small to Medium-sized Businesses (SMBs) in Singapore. Its primary goal is to offer professional-grade financial tools that are compliant with Singapore Financial Reporting Standards (SFRS), Goods and Services Tax (GST) regulations (including the 9% rate), and general IRAS (Inland Revenue Authority of Singapore) considerations. The application aims to be user-friendly for business owners who may not be accounting experts, while still providing the depth required by accounting professionals. A key principle is "Local First," meaning user data resides on their local machine or private server, ensuring privacy, control, and no subscription fees, distinguishing it from many cloud-based SaaS offerings.

**2. Key Functionalities & Modules (as of TDS v11 / latest README):**

The application is structured around several key functional modules:

*   **Core Accounting:**
    *   **Double-Entry Bookkeeping:** The foundational accounting principle.
    *   **Chart of Accounts (CoA):** Hierarchical and customizable, with UI for full CRUD operations. Singapore-specific templates are available.
    *   **Journal Entry System:** UI for creating, editing (drafts), posting, and reversing General Journal Entries. System-generated journal entries are created upon posting source documents (e.g., Sales Invoices).
    *   **Fiscal Year & Period Management:** UI in Settings for creating fiscal years and auto-generating their periods (monthly/quarterly). Logic for period closing/reopening is managed by `FiscalPeriodManager`.
    *   **Multi-Currency Support:** Foundational elements (DB tables, models, `CurrencyManager`) exist. Full UI integration into transactions is pending.
    *   **Budgeting & Variance Analysis:** Foundational DB tables and models exist. UI/Logic is planned.

*   **Singapore Tax Compliance:**
    *   **GST Tracking & Calculation:** `TaxCode` setup (SR, ZR, ES, TX at 9%) and `TaxCalculator` for line item tax. GST is applied in Sales Invoice and Purchase Invoice dialogs.
    *   **GST F5 Return:** Backend for data preparation (from posted JEs) and finalization (including settlement JE creation) is implemented. UI in the Reports tab allows preparation, viewing, saving drafts, and finalizing GST F5 returns.

*   **Business Operations:**
    *   **Customer Management:** Full CRUD operations and listing UI with search/filter capabilities.
    *   **Vendor Management:** Full CRUD operations and listing UI with search/filter capabilities.
    *   **Product & Service Management:** Full CRUD operations for products (Inventory, Non-Inventory) and services, including toggling active status. UI includes a list view with filters and a comprehensive dialog that adapts to product type.
    *   **Sales Invoicing & Accounts Receivable:**
        *   Full lifecycle implemented: Draft CRUD, list view with filtering, "Save & Approve" functionality in `SalesInvoiceDialog` which posts the invoice and creates corresponding journal entries.
    *   **Purchase Invoicing & Accounts Payable:**
        *   **Draft Management Implemented**: Backend logic and UI dialog (`PurchaseInvoiceDialog`) are fully functional for creating and editing draft purchase invoices, including dynamic calculations.
        *   **List View Implemented**: `PurchaseInvoicesWidget` provides a list of purchase invoices with filtering, and actions to create new drafts or edit/view existing ones.
        *   Posting logic (JE creation) for purchase invoices is currently a stub and planned next.
    *   **Payment Processing & Allocation:** Foundational DB tables/models exist. UI/Logic is planned.
    *   **Bank Account Management & Reconciliation:** Foundational DB tables/models exist. UI is a stub.
    *   **Basic Inventory Control:** Foundational (`Product` model has inventory fields, `InventoryMovements` table exists). Logic is planned.

*   **Reporting & Analytics:**
    *   **Standard Financial Statements:** Balance Sheet (BS), Profit & Loss (P&L), Trial Balance (TB), General Ledger (GL).
        *   UI in Reports tab allows selection, on-screen viewing (native Qt views for TB/GL, improved tree views for BS/P&L).
        *   **Enhanced PDF/Excel Export for BS & P&L:** Improved formatting, headers, footers (PDF), sectioning, and number styling.
        *   **Enhanced UI Options for BS & P&L:** Checkboxes for "Include Zero-Balance Accounts" (BS only) and "Include Comparative Period" (BS & P&L), with dynamic date controls.
    *   **GST Reports:** GST F5 data preparation and finalization as described under Tax Compliance.
    *   **Cash Flow Statement:** Planned.
    *   **Dashboard KPIs:** Planned (UI is a stub).

*   **System Administration & Security:**
    *   **User Authentication:** Login mechanism with password hashing (`bcrypt`).
    *   **Role-Based Access Control (RBAC):** Fully implemented UI for managing Users (add, edit, toggle active, change password, assign roles), Roles (add, edit, delete), and assigning system Permissions to Roles.
    *   **Granular Permissions System:** Backend checks (`SecurityManager.has_permission()`) and seeded permissions are in place.
    *   **Comprehensive Audit Trails:** Implemented via database triggers (`audit.audit_log`, `audit.data_change_history`) using `app.current_user_id` set by the application.
    *   **Company Settings:** UI for configuring company information.

**3. Technical Architecture:**

*   **Layered Architecture:**
    *   **Presentation Layer (UI):** PySide6 (version 6.9+) for all widgets, dialogs, and the main application window.
    *   **Business Logic Layer:** Python-based. Contains `ApplicationCore` for orchestrating services and managers. Managers (`ChartOfAccountsManager`, `JournalEntryManager`, `SalesInvoiceManager`, `PurchaseInvoiceManager`, `SecurityManager`, etc.) encapsulate specific business workflows and validation logic.
    *   **Data Access Layer (Services):** Python-based. Services (`AccountService`, `SalesInvoiceService`, `ProductService`, etc.) implement repository patterns, abstracting ORM interactions.
    *   **Database Layer:** PostgreSQL (version 14+).
*   **Asynchronous Processing:**
    *   A dedicated Python thread runs a persistent `asyncio` event loop.
    *   UI interactions that require potentially long-running I/O operations (like database calls) schedule coroutines onto this asyncio loop using a helper function (`schedule_task_from_qt`).
    *   Results from async tasks are passed back to the Qt main thread for UI updates using `QMetaObject.invokeMethod` with `Qt.QueuedConnection`, often serializing data (e.g., to JSON) for thread-safe transfer.
*   **Database Interaction:**
    *   SQLAlchemy (version 2.0+) in its asynchronous ORM mode.
    *   `asyncpg` as the asynchronous database driver for PostgreSQL.
    *   `DatabaseManager` handles connection pooling and session management.
*   **Data Integrity & Validation:**
    *   Pydantic V2 models are used for Data Transfer Objects (DTOs) between UI and business logic layers, providing initial validation.
    *   Further validation occurs within manager classes.
    *   Database schema enforces integrity through constraints, foreign keys, and triggers.
*   **Modularity:** The codebase is organized into modules reflecting functionality (e.g., `app/core`, `app/accounting`, `app/business_logic`, `app/ui/sales_invoices`).

**4. Technology Stack:**

*   **Programming Language:** Python 3.9+ (up to 3.12 tested/supported).
*   **UI Framework:** PySide6 6.9.0+.
*   **Database:** PostgreSQL 14+.
*   **ORM:** SQLAlchemy 2.0+ (Async ORM).
*   **Async DB Driver:** `asyncpg`.
*   **Data Validation (DTOs):** Pydantic V2 (with `email-validator` for email fields).
*   **Password Hashing:** `bcrypt`.
*   **Reporting Libraries:** `reportlab` (PDF), `openpyxl` (Excel).
*   **Dependency Management:** Poetry.
*   **Date/Time Utilities:** `python-dateutil`.

**5. Project Evolution & Document Consistency:**

*   **Progressive Development:** The project has evolved systematically, starting with core accounting foundations (TDS v1-v3), then adding master data management (Products in TDS v7, Customers/Vendors likely before that), followed by transactional modules (Sales Invoicing in TDS v8, Purchase Invoicing in TDS v11), and system administration (User/Role Management in TDS v9). Reporting capabilities have been iteratively enhanced.
*   **TDS as Living Document:** The TDS versions reflect this progression, with each version detailing the design of newly added or significantly enhanced features.
*   **README & TDS Alignment (Latest):**
    *   The latest `README.md` and `Technical_Design_Specification_Document.md` (v11) are largely consistent.
    *   Both highlight the implementation of Draft Purchase Invoice Management and Enhanced PDF/Excel Export for BS/P&L reports as the latest major additions.
    *   The TDS v11 provides detailed component descriptions for the `PurchaseInvoicesWidget` (list view), `PurchaseInvoiceDialog`, `PurchaseInvoiceManager`, and `PurchaseInvoiceService`, indicating these are implemented for draft management.
    *   There's a minor inconsistency where the introductory sections of both README and TDS v11 state the Purchase Invoice *list view* (`PurchaseInvoicesWidget`) is "planned" or "future." However, the detailed component specifications within TDS v11 (Sections 2.2.5, 4.4.5, 5.7, 9) and the provided file structure (`currect_project_file_structure.txt` lists `app/ui/purchase_invoices/purchase_invoices_widget.py`) strongly suggest the `PurchaseInvoicesWidget` for listing drafts *is* implemented. It's likely the introductory statements are slightly outdated remnants. For the purpose of understanding, I will consider the detailed component descriptions within TDS v11 as the accurate representation of the implemented state.
*   **Documentation of Current State**: The `Technical_Design_Specification_Document.md` (v11) accurately reflects the implemented features related to "Draft Purchase Invoice Management (Backend Logic and UI Dialog/List View)" and "Enhanced PDF/Excel Export Formatting for Balance Sheet & Profit/Loss Reports," as well as previously implemented features.

**6. Deviations Between TDS Versions (Summary of Evolution):**

*   **v1:** Foundational system skeleton, core accounting entities (CoA, JE), basic UI patterns.
*   **v2:** Major schema alignment with a comprehensive external `schema.sql` reference. Models fleshed out. Poetry introduced.
*   **v3:** Detailed asynchronous processing architecture. Audit trigger details.
*   **v7 (jump from v3):** Product/Service Management module (backend + UI).
*   **v8:** Sales Invoicing Draft Management (backend + Dialog UI).
*   **v9:** Full User and Role Management (backend + comprehensive UI in Settings).
*   **v11 (jump from v9):** Purchase Invoice Draft Management (full UI - list and dialog, backend for drafts). Enhanced BS/P&L reporting (export format, UI options).

This progression shows a logical build-up of functionalities. The documentation has evolved to capture these stages.

My understanding is that SG Bookkeeper is a mature desktop accounting application with a strong focus on Singaporean SMB needs, leveraging modern Python technologies for a robust and responsive user experience. The development has been methodical, building core features and then expanding into more complex business operations and system administration capabilities.
