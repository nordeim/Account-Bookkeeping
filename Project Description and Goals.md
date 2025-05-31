## Project Understanding: SG Bookkeeper

SG Bookkeeper is a sophisticated, cross-platform desktop accounting application meticulously engineered to serve the specific needs of Small to Medium-sized Businesses (SMBs) in Singapore. It aims to provide a comprehensive, robust, and user-friendly financial management solution.

**Core Goals & Objectives:**

1.  **Compliance**: Adherence to Singapore Financial Reporting Standards (SFRS) and Goods & Services Tax (GST) regulations, including features like GST F5 return preparation.
2.  **Functionality**: Implementation of a full double-entry bookkeeping system, covering core accounting, business operations (sales, purchases, inventory), detailed financial reporting, and system administration.
3.  **Usability**: An intuitive PySide6-based graphical user interface designed for both accounting professionals and business owners who may not be accounting experts. Emphasis on responsive UI through asynchronous operations.
4.  **Robustness & Data Integrity**: Utilization of PostgreSQL for reliable data storage, SQLAlchemy ORM for structured data access, Pydantic DTOs for data validation, and comprehensive audit trails.
5.  **Maintainability & Scalability**: A well-defined layered architecture (Presentation, Business Logic, Data Access, Database) to promote separation of concerns, modularity, and ease of future development.
6.  **Local-First & Open Source**: Financial data remains on the user's local machine or private server, ensuring privacy, control, and no subscription fees, with transparent development.

**Architectural Overview:**

*   **Presentation Layer (`app/ui/`)**:
    *   Built with **PySide6**.
    *   `MainWindow` acts as the main application shell with a tabbed interface.
    *   Module-specific widgets (e.g., `SalesInvoicesWidget`, `ReportsWidget`) and dialogs (`SalesInvoiceDialog`, `AccountDialog`) handle user interaction and data display.
    *   Custom `QAbstractTableModel` subclasses feed data to `QTableView`s.
    *   Asynchronous calls to the backend are managed via `schedule_task_from_qt`, with UI updates handled thread-safely using `QMetaObject.invokeMethod`.

*   **Business Logic Layer (`app/core/`, `app/accounting/`, `app/business_logic/`, etc.)**:
    *   `ApplicationCore`: Central orchestrator, initializes and provides access to managers and services.
    *   **Managers** (e.g., `SalesInvoiceManager`, `PurchaseInvoiceManager`, `GSTManager`, `FinancialStatementGenerator`): Encapsulate business rules, validation, and orchestrate complex workflows.
    *   Uses **Pydantic DTOs** (`app/utils/pydantic_models.py`) for validated data exchange.

*   **Data Access Layer (`app/services/`, `app/models/`)**:
    *   `DatabaseManager`: Manages asynchronous PostgreSQL connections (SQLAlchemy async engine, `asyncpg` driver), sessions, and sets `app.current_user_id` for DB audit triggers.
    *   **Services** (e.g., `SalesInvoiceService`, `AccountService`): Implement a repository pattern, abstracting ORM query logic.
    *   **SQLAlchemy ORM Models**: Define Python object mappings to database tables, organized by schema.

*   **Database Layer (PostgreSQL)**:
    *   Schema defined in `scripts/schema.sql` (DDL) with four main schemas: `core`, `accounting`, `business`, `audit`.
    *   Includes tables, views, functions, and triggers (notably for audit logging).
    *   Initial data seeded by `scripts/initial_data.sql`.

**Key Implemented Features (Reflecting recent updates):**

*   **Core Accounting**: Chart of Accounts (CRUD), General Journal (CRUD, posting, reversal, Journal Type filter), Fiscal Year/Period Management.
*   **Tax Management**: GST F5 Return preparation and finalization, `TaxCalculator`.
*   **Business Operations**:
    *   Customer, Vendor, Product/Service Management (Full CRUD & listing).
    *   Sales Invoicing: Full lifecycle - Draft CRUD, Posting (with financial JE & inventory WAC JE), List View, Dialog with advanced product search.
    *   Purchase Invoicing: Full lifecycle - Draft CRUD, Posting (with financial JE & inventory WAC JE), List View, Dialog with advanced product search and QCompleter for vendor filter.
*   **Reporting**:
    *   Balance Sheet, Profit & Loss: On-screen tree view, enhanced PDF/Excel export, comparative periods, zero-balance options.
    *   Trial Balance, General Ledger: On-screen table view, enhanced PDF/Excel export. General Ledger reports include filtering by up to two dimensions.
*   **System Administration**: User and Role Management (CRUD, password management, role/permission assignment).

The project leverages a modern Python technology stack and aims for high code quality and adherence to best practices.

