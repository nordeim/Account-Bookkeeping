# SG Bookkeeper - Project Architecture Document

## 1. Introduction

### 1.1. Purpose

This document provides a comprehensive architectural overview of the SG Bookkeeper application. Its goal is to serve as a foundational guide for current and future developers, ensuring a clear and shared understanding of the system's design, principles, and components. By detailing the structure, patterns, and data flows, this document aims to facilitate maintenance, debugging, and the strategic implementation of new features while preserving the architectural integrity of the codebase.

### 1.2. High-Level Overview

SG Bookkeeper is a desktop accounting application designed specifically for small-to-medium-sized enterprises (SMEs) operating in Singapore. It is built using Python and the PySide6 framework for its graphical user interface (GUI). The application provides a robust suite of bookkeeping functionalities, including chart of accounts management, journal entries, sales and purchase invoicing, customer and vendor relationship management, product/service tracking, banking and reconciliation, and financial reporting.

At its core, the application is engineered to be a responsive, database-driven system. It leverages an asynchronous programming model to interact with its PostgreSQL database, ensuring the user interface remains fluid and non-blocking even during intensive data operations. The architecture is deliberately layered to separate concerns, promoting maintainability, testability, and scalability.

## 2. Core Architectural Principles

The architecture of SG Bookkeeper is founded on several key principles that guide its design and development.

*   **Layered Architecture:** The system is distinctly partitioned into four primary layers: **Presentation (UI)**, **Business Logic (Managers)**, **Data Access (Services)**, and **Data Persistence (Database)**. This separation of concerns ensures that changes in one layer have minimal impact on others, making the system easier to develop, test, and maintain.

*   **Asynchronous Core for UI Responsiveness:** To provide a smooth user experience befitting a modern desktop application, the core operations (especially database interactions) are asynchronous. The application runs a dedicated `asyncio` event loop in a background thread, while the Qt event loop manages the UI in the main thread. A carefully designed bridge allows the UI to schedule and await results from asynchronous tasks without freezing.

*   **Model-View-Presenter (MVP) / Model-View-Controller (MVC) Pattern:** The UI layer loosely follows the MVP/MVC pattern.
    *   **View:** `QWidget` and `QDialog` subclasses (`CustomersWidget`, `SalesInvoiceDialog`) are responsible for rendering the user interface and capturing user input.
    *   **Model:** `QAbstractTableModel` subclasses (`CustomerTableModel`) and Pydantic DTOs act as the data model for the views, defining the structure of the data to be displayed.
    *   **Presenter/Controller:** The "Manager" classes in the Business Logic layer (`CustomerManager`, `SalesInvoiceManager`) serve as the Presenters. They are invoked by the Views, process user requests, interact with the data layer, and prepare data for the View to display.

*   **Service-Repository Pattern:** The Data Access Layer is implemented using "Service" classes (`CustomerService`, `AccountService`). These services act as repositories, abstracting the details of data persistence. They are the sole components responsible for direct interaction with the SQLAlchemy ORM and the `DatabaseManager`. This isolates data query logic and makes it reusable.

*   **Data Transfer Objects (DTOs):** The application makes extensive use of Pydantic models as DTOs. These objects define clear, validated data contracts for passing information between layers (e.g., from a UI dialog to a Manager, or from a Manager to a Service). This improves type safety, provides automatic data validation, and decouples the application's internal logic from the specific structure of the database models.

*   **Centralized Core & Dependency Management:** The `ApplicationCore` class acts as a central service locator and container for all major components (Managers and Services). It is instantiated once at startup and passed throughout the application, providing a single, consistent point of access to shared resources and business logic, simplifying dependency management.

*   **Database-Driven Logic:** Key business constraints, sequences, and audit trails are enforced at the database level through `CHECK` constraints, custom functions (e.g., `get_next_sequence_value`), and triggers. This ensures data integrity and a single source of truth, regardless of how the data is accessed.

## 3. Architectural Diagram

The following diagram illustrates the high-level, layered architecture of the SG Bookkeeper application, showing the flow of control and data between the major components.

```mermaid
graph TD
    subgraph "Presentation Layer (app/ui)"
        A[UI Widgets & Dialogs <br/> e.g., SalesInvoicesWidget]
        B[Qt Models <br/> e.g., SalesInvoiceTableModel]
    end

    subgraph "Business Logic Layer"
        C[Managers <br/> e.g., SalesInvoiceManager, JournalEntryManager]
    end
    
    subgraph "Central Orchestrator"
        D{ApplicationCore}
    end

    subgraph "Data Access Layer (app/services)"
        E[Services (Repositories) <br/> e.g., SalesInvoiceService, AccountService]
    end

    subgraph "Data Persistence Layer"
        F[Database Manager <br/> (SQLAlchemy Core/ORM)]
        G[(PostgreSQL Database <br/> with Schemas & Triggers)]
    end

    subgraph "Supporting Components"
        H[Utilities <br/> (DTOs, Result Class, Helpers)]
        I[AsyncIO Event Loop <br/> (Background Thread)]
    end

    A -- User Interaction --> C
    A -- Displays Data From --> B
    C -- Uses --> E
    C -- Updates --> B
    D -- Provides Access To --> C
    D -- Provides Access To --> E
    A -- Accesses Managers via --> D
    E -- Uses --> F
    F -- Manages Connections To --> G
    C -- Uses --> H
    A -- Signals Task To --> I
    I -- Runs Async DB Operations via --> F
    I -- Returns Result To --> A
```

**Flow Explanation:**

1.  A user interacts with a **UI Widget** (A).
2.  The UI Widget calls a method on a **Manager** (C) via the central `ApplicationCore` (D).
3.  The Manager (C) processes the business logic. It may use **Utilities** like DTOs (H) to validate data.
4.  The Manager (C) calls one or more methods on **Services** (E) to fetch or save data.
5.  The Service (E) constructs a database query using SQLAlchemy ORM and executes it via the **Database Manager** (F).
6.  The Database Manager (F) manages the connection pool and executes the query against the **PostgreSQL Database** (G). For long-running queries, this happens on the `asyncio` event loop thread (I).
7.  Data flows back up the chain. The UI is updated, either directly or via a Qt Model (B), often through signals and slots to handle the asynchronous nature of the operation.

## 4. Component Breakdown

### 4.1. Application Entry Point & Core (`app/main.py`, `app/core/`)

This is the foundation of the application, responsible for initialization, lifecycle management, and providing central services.

*   **`app/main.py`**:
    *   **Role**: The main entry point of the application.
    *   **Key Responsibilities**:
        1.  **Asyncio/Qt Integration**: It establishes the critical asynchronous architecture. An `asyncio` event loop is started in a separate, dedicated background thread (`_ASYNC_LOOP_THREAD`). This prevents any database or long-running operations from blocking the Qt GUI event loop in the main thread.
        2.  **Scheduling Bridge**: The `schedule_task_from_qt` function is the vital bridge that allows the Qt (main) thread to safely schedule a coroutine to run on the `asyncio` thread and get a `Future` object back to await the result.
        3.  **Application Initialization**: It instantiates the `Application` class, which shows a splash screen and triggers the asynchronous `initialize_app` method. This method, running in the `asyncio` thread, sets up the `ConfigManager`, `DatabaseManager`, and `ApplicationCore`.
        4.  **Signal/Slot for Initialization**: Upon successful async initialization, a Qt signal (`initialization_done_signal`) is emitted back to the main thread. The corresponding slot (`_on_initialization_done`) then creates the `MainWindow`, passes it the fully initialized `ApplicationCore` instance, and hides the splash screen. This is a textbook example of safe cross-thread communication.
        5.  **Shutdown Sequence**: It connects the application's `aboutToQuit` signal to a robust `actual_shutdown_sequence` method, ensuring the `ApplicationCore` and the `asyncio` event loop are gracefully shut down.

*   **`app/core/`**: This directory contains the singleton-like objects that form the application's backbone.
    *   **`application_core.py` (ApplicationCore)**: The central nervous system of the application. It acts as a service locator or dependency injection container. On startup, it instantiates all **Service** and **Manager** classes, making them available as properties (e.g., `app_core.customer_manager`). This provides a single, consistent way for different parts of the application (especially the UI) to access business logic and data services without needing to manage object lifecycles themselves.
    *   **`database_manager.py` (DatabaseManager)**: This class abstracts all direct interaction with the database. It uses the settings from `ConfigManager` to create a SQLAlchemy `async_engine` and an `async_sessionmaker`. Its primary feature is the `session()` async context manager, which provides a transactional `AsyncSession` to the service layer. Crucially, it sets the `app.current_user_id` session variable for the database, which is used by the audit triggers.
    *   **`config_manager.py` (ConfigManager)**: A simple and effective class for managing user-specific configuration. It creates and reads a `config.ini` file in the appropriate user configuration directory for the host OS (e.g., `~/.config/SGBookkeeper` on Linux). It provides typed access to database connection details and application settings like the last-opened company.
    *   **`security_manager.py` (SecurityManager)**: Handles all aspects of user authentication and authorization. It manages hashing and verifying passwords (using `bcrypt`), authenticating users against the database, tracking the `current_user` for the session, and providing a `has_permission` method for role-based access control (RBAC).

### 4.2. Data Model Layer (`app/models/`)

This layer defines the application's data structure using SQLAlchemy's Declarative ORM. It provides an object-oriented interface to the database tables.

*   **Schema Organization**: A key architectural decision is the organization of models into sub-packages that mirror the database schemas: `core`, `accounting`, `business`, and `audit`. This keeps the model layer clean and reflects the logical domains of the data.
*   **Base and Mixins (`base.py`)**:
    *   `Base`: The declarative base for all ORM models.
    *   `TimestampMixin`: Provides `created_at` and `updated_at` columns with automatic timestamping, promoting consistency across all tables that inherit it.
    *   `UserAuditMixin`: Provides `created_by` and `updated_by` columns, linking records to the user who created or last modified them. This is fundamental for auditing.
*   **Models**: Each file (e.g., `customer.py`, `sales_invoice.py`) defines a Python class that maps to a database table. These classes include:
    *   Column definitions using `Mapped` and `mapped_column`, specifying types, constraints, and foreign keys.
    *   Relationships between models using `relationship()`, defining how entities like `Customer` and `SalesInvoice` are linked. The use of `back_populates` ensures these relationships are bi-directional and managed correctly by SQLAlchemy.
    *   `CHECK` constraints defined in `__table_args__` to enforce enum-like behavior at the database level for fields like `status`.

### 4.3. Data Access Layer (`app/services/`)

This layer acts as a classic **Repository Pattern**. Each service is responsible for the data persistence logic for a specific model or a closely related group of models.

*   **Abstraction**: Services abstract the database away from the business logic. A Manager doesn't know *how* a customer is saved; it just calls `customer_service.save(customer_orm)`.
*   **SQLAlchemy Interaction**: This is the only layer (besides `DatabaseManager`) that directly interacts with SQLAlchemy sessions and ORM objects. It uses the `db_manager.session()` context manager to perform queries.
*   **Methods**: Services typically provide CRUD (Create, Read, Update, Delete) methods (`get_by_id`, `get_all`, `save`, `delete`) as well as more specific query methods (e.g., `get_all_summary`, `get_outstanding_invoices_for_customer`).
*   **Data Return**: Services return ORM model instances or lists of instances to the calling Manager.

### 4.4. Business Logic Layer (`app/business_logic/` & `app/accounting/` managers)

This is the application's brain. The "Manager" classes encapsulate all business rules, processes, and orchestrations.

*   **Orchestration**: Managers coordinate multiple services to fulfill a single business operation. For example, `SalesInvoiceManager.post_invoice()` doesn't just update an invoice status; it creates a journal entry (via `JournalEntryManager`), creates inventory movements (via `InventoryMovementService`), and then updates the invoice status (via `SalesInvoiceService`).
*   **Validation**: Managers are responsible for validating business rules before persisting data. For instance, `PaymentManager` validates that the total allocated amount does not exceed the payment amount. It also validates that the selected invoices belong to the correct entity.
*   **Data Transformation**: Managers take DTOs (`Pydantic Models`) from the UI layer, process them, and convert them into ORM models to be passed to the Service layer. They also take ORM models back from services and can transform them into DTOs or other formats for the UI.
*   **Result Object**: They consistently use the `Result` class to return outcomes. This provides a clear, standardized way to signal success (with a value) or failure (with a list of error messages) to the UI layer, which can then display appropriate feedback to the user.
*   **Separation**: The logic is separated by domain into `business_logic` (for core business entities like customers, invoices) and `accounting` (for core accounting processes like journal entries, fiscal periods).

### 4.5. Presentation Layer (`app/ui/`)

This layer is responsible for everything the user sees and interacts with. It's built with **PySide6** and follows a consistent, modular pattern.

*   **Structure**: The UI is organized into sub-packages by feature (`customers`, `sales_invoices`, `settings`, etc.), mirroring the application's modular design.
*   **Component Pattern**: Each module typically consists of three key components:
    1.  **`...Widget.py`**: The main view for the module (e.g., `CustomersWidget`). It contains the toolbar, filter/search controls, and the main data table (`QTableView`). It's responsible for orchestrating the user experience within that module.
    2.  **`...TableModel.py`**: A subclass of `QAbstractTableModel` (e.g., `CustomerTableModel`). It serves as the bridge between the list of data DTOs and the `QTableView`, telling the view how to display the data. It's a pure data presentation component.
    3.  **`...Dialog.py`**: A `QDialog` subclass for creating or editing a single entity (e.g., `CustomerDialog`). It contains the input form fields, validation logic (client-side), and communicates with the appropriate Manager to save data.
*   **Asynchronous Communication**: The UI layer heavily relies on the `schedule_task_from_qt` bridge. User actions (like clicking "Refresh" or "Save") trigger slots that schedule an asynchronous manager method. `Future.add_done_callback()` or signal/slot mechanisms are used to receive the result back on the main thread and update the UI (e.g., repopulating a table or showing a success/error `QMessageBox`).
*   **DTOs for UI-Logic Communication**: Dialogs collect user input and package it into a Pydantic DTO (e.g., `CustomerCreateData`) before sending it to the Business Logic layer. This ensures that the data sent from the UI is already in a structured and partially validated format.
*   **Resource Management (`resources.qrc`, `resources_rc.py`)**: Icons and images are managed via a Qt Resource File (`.qrc`). This file is compiled into a Python module (`resources_rc.py`), which bundles the assets directly into the application, making deployment easier and eliminating issues with relative paths.

### 4.6. Utilities and Common Code (`app/utils/`, `app/common/`)

*   **`app/utils/`**: This package contains cross-cutting concerns and helper modules.
    *   **`pydantic_models.py`**: One of the most critical files. It defines all the DTOs used for data transfer between layers. This enforces data contracts and provides powerful validation.
    *   **`result.py`**: Defines the `Result` class, a simple but powerful wrapper for returning success/failure states from the business logic layer.
    *   **`json_helpers.py`**: Provides custom JSON encoders/decoders to handle `Decimal` and `datetime` objects, which are essential for communicating complex data between the async and Qt threads via JSON serialization.
    *   **`sequence_generator.py`**: An abstraction for generating sequential numbers (e.g., invoice numbers), which cleverly attempts to use a more robust database function first and falls back to Python-based logic if necessary.
*   **`app/common/`**:
    *   **`enums.py`**: Centralizes all application-specific enumerations (e.g., `InvoiceStatusEnum`, `ProductTypeEnum`). This improves code readability and maintainability by avoiding "magic strings."

## 5. Database Schema

The choice of **PostgreSQL** provides a powerful, transactional, and extensible foundation for the application. The schema is well-organized and leverages advanced database features to ensure data integrity.

*   **Logical Schemas**: The database is organized into four distinct schemas:
    1.  `core`: For fundamental application data like users, roles, permissions, and configuration.
    2.  `accounting`: For all core accounting tables, including the chart of accounts, journal entries, fiscal periods, and tax information.
    3.  `business`: For operational data related to business activities, such as customers, vendors, invoices, and bank transactions.
    4.  `audit`: For logging and history tables, separating audit concerns from operational data.
    This separation makes the database easier to navigate, manage, and secure.

*   **Triggers and Functions**:
    *   **`update_timestamp_trigger_func`**: Automatically updates the `updated_at` column on any row update, ensuring audit timestamps are always current without application-level intervention.
    *   **`log_data_change_trigger_func`**: This is a powerful audit trigger. It captures every `INSERT`, `UPDATE`, and `DELETE` operation on key tables. It records *who* made the change (via the `app.current_user_id` session variable), *what* changed (a JSONB diff of the old and new row), and *when*. It also populates the `data_change_history` table with a field-by-field breakdown of changes. This provides an exceptionally detailed and robust audit trail.
    *   **`update_bank_account_balance_trigger_func`**: This trigger automatically maintains the `current_balance` on the `bank_accounts` table whenever a new transaction is inserted, updated, or deleted in `bank_transactions`. This denormalization improves performance for frequently accessed balance information.
    *   **`get_next_sequence_value`**: A PostgreSQL function that provides a transaction-safe, robust way to generate the next number in a sequence (e.g., `INV-000001`), avoiding race conditions that could occur with a pure Python implementation.

*   **Data Integrity**: The schema uses `FOREIGN KEY` constraints extensively to maintain relational integrity. `CHECK` constraints are used to enforce enum-like value restrictions at the database level, and `UNIQUE` constraints (including a GIST index on `fiscal_years` for date range exclusion) prevent duplicate or invalid data.

## 6. Project File Structure

The project's file structure is logical and directly reflects the layered architecture described above.

```
SG-Bookkeeper/
├── app/                  # Main application source code
│   ├── __init__.py
│   ├── main.py           # Application entry point, Qt/Asyncio setup
│   ├── accounting/       # Accounting-specific business logic managers
│   ├── business_logic/   # General business logic managers
│   ├── common/           # Shared code, primarily enums
│   ├── core/             # Core application components (AppCore, DBManager, etc.)
│   ├── models/           # SQLAlchemy ORM models, organized by schema
│   │   ├── core/
│   │   ├── accounting/
│   │   ├── business/
│   │   └── audit/
│   ├── reporting/        # Logic for generating reports
│   ├── services/         # Data Access Layer (Repositories)
│   ├── tax/              # Tax calculation and management logic
│   ├── ui/               # All GUI components (Widgets, Dialogs, Models)
│   │   ├── accounting/
│   │   ├── audit/
│   │   ├── banking/
│   │   ├── customers/
│   │   ├── dashboard/
│   │   ├── payments/
│   │   ├── products/
│   │   ├── purchase_invoices/
│   │   ├── reports/
│   │   ├── sales_invoices/
│   │   ├── settings/
│   │   ├── shared/
│   │   └── main_window.py
│   └── utils/            # Utility modules (DTOs, Result class, helpers)
├── data/                 # Static data files, templates
│   ├── chart_of_accounts/
│   ├── report_templates/
│   └── tax_codes/
├── resources/            # UI resources like icons and images
│   ├── icons/
│   └── images/
├── scripts/              # Standalone scripts for DB initialization, etc.
│   ├── db_init.py
│   ├── schema.sql
│   └── initial_data.sql
├── tests/                # All application tests
│   ├── unit/
│   └── integration/
├── pyproject.toml        # Project metadata and dependencies (Poetry)
└── README.md
```

### Folder and File Purposes

*   **`app/`**: Contains all the application's Python source code.
    *   `main.py`: The executable entry point. Initializes the Qt Application and the core components.
    *   `accounting/` & `business_logic/`: The **Business Logic Layer**. Contains "Manager" classes that orchestrate application workflows and enforce business rules.
    *   `core/`: The heart of the application, containing the `ApplicationCore` orchestrator and other essential, singleton-like managers (`DatabaseManager`, `SecurityManager`).
    *   `models/`: The **Data Model Layer**. Contains all SQLAlchemy ORM class definitions, organized into sub-packages mirroring the database schema.
    *   `services/`: The **Data Access Layer**. Contains "Service" classes that act as repositories, handling all database query logic.
    *   `ui/`: The **Presentation Layer**. Contains all PySide6 widgets, dialogs, and table models, organized by functional module.
    *   `utils/`: Houses cross-cutting utility code, most importantly the Pydantic DTOs (`pydantic_models.py`), which are fundamental to the application's data contracts.
*   **`data/`**: Stores static data files like CSV templates for the initial Chart of Accounts or JSON templates for reports.
*   **`resources/`**: Contains static assets for the UI, such as `.svg` icons and `.png` images. The `.qrc` file is used to compile these into a Python module for easy distribution.
*   **`scripts/`**: Holds utility scripts that are run outside the main application loop.
    *   `db_init.py`: A crucial script to initialize a new database from scratch.
    *   `schema.sql`: The single source of truth for the database schema definition.
    *   `initial_data.sql`: Populates the database with essential starting data, such as default currencies, roles, permissions, and system accounts.
*   **`tests/`**: Contains all automated tests, separated into `unit` and `integration` tests.
*   **`pyproject.toml`**: The Poetry project definition file, managing dependencies, scripts, and project metadata.

## 7. Data Flow Example: Creating and Posting a Sales Invoice

To illustrate how these components interact, let's trace the process of creating and posting a sales invoice.

1.  **User Action (UI Layer)**: The user is in the `SalesInvoicesWidget` and clicks the "New Invoice" `QAction`.
2.  **Dialog Opening (UI Layer)**: The widget's slot opens a `SalesInvoiceDialog`. The dialog's `__init__` method schedules an async task (`_load_initial_combo_data`) to fetch necessary data (customers, products, tax codes) from their respective managers via the `app_core`.
3.  **Data Entry (UI Layer)**: The user fills out the invoice details (customer, dates, line items). The dialog's UI elements (like `QDoubleSpinBox` and `QComboBox`) and table delegate (`LineItemNumericDelegate`) provide immediate input validation and formatting. As the user adds/edits lines, the `_calculate_line_item_totals` and `_update_invoice_totals` methods are triggered to update the UI in real-time.
4.  **Save & Approve (UI -> Logic)**: The user clicks "Save & Approve". The dialog's `on_save_and_approve` slot is called.
5.  **Data Collection (UI -> DTO)**: The `_collect_data` method in the dialog gathers all the data from the form fields and table into a `SalesInvoiceCreateData` Pydantic DTO. This DTO is validated upon instantiation.
6.  **Scheduling the Task (UI -> Core)**: The dialog calls `schedule_task_from_qt(self._perform_save(dto, post_invoice_after=True))`. This hands off the operation to the `asyncio` thread. The UI remains responsive.
7.  **Manager Orchestration (Business Logic Layer)**:
    *   `SalesInvoiceManager._perform_save` is now running in the background.
    *   It first calls `_validate_and_prepare_invoice_data` to perform server-side validation (e.g., checking if the customer is active).
    *   It calls `sequence_service.next_sequence` to get a new invoice number.
    *   It creates a `SalesInvoice` ORM object and saves it as a "Draft" via `sales_invoice_service.save()`. This commits the initial draft to the database.
    *   Because `post_after_save` is `True`, it immediately calls `self.post_invoice(saved_invoice.id, user_id)`.
8.  **Posting Logic (Business Logic -> Service -> DB)**:
    *   `SalesInvoiceManager.post_invoice` is a complex transactional method. It fetches the draft invoice and all related data (customer, lines, products).
    *   It constructs a `JournalEntryData` DTO for the financial posting (Debiting A/R, Crediting Sales Revenue, Crediting GST Output).
    *   It calls `journal_entry_manager.create_journal_entry` and then `journal_entry_manager.post_journal_entry`.
    *   For each "Inventory" type product on the invoice, it creates an `InventoryMovement` record via `inventory_movement_service`. It may also create a corresponding COGS journal entry.
    *   Finally, it updates the `SalesInvoice` status to "Approved" and links it to the created journal entry, saving it via `sales_invoice_service.save()`.
9.  **Result Handling (Logic -> UI)**:
    *   The `_perform_save` coroutine finishes and returns a `Result` object.
    *   The `done_callback` attached to the future in the UI layer is triggered back on the Qt main thread.
    *   The callback inspects the `Result` object. If successful, it shows a `QMessageBox.information` and closes the dialog. If it failed, it shows a `QMessageBox.warning` with the errors. The main `SalesInvoicesWidget` then refreshes its list to show the new, posted invoice.

## 8. Conclusion

The SG Bookkeeper application is built upon a modern, robust, and well-structured architecture. The clear separation of layers, the asynchronous core, and the consistent use of patterns like DTOs and Service-Repositories make the codebase highly maintainable and extensible. The database schema is intelligently designed with data integrity and auditing as primary concerns.

This architecture provides a solid foundation for future development. By understanding and adhering to these principles, developers can confidently add new features and modules while ensuring the long-term health and stability of the application.

---
https://drive.google.com/file/d/14GI0Jpi1ZCxjckpC0WPEG7YNdf3D-Vfp/view?usp=sharing, https://drive.google.com/file/d/1FmPfEv5XKMhn3JaojHSvp_wmUe9jH_kz/view?usp=sharing, https://drive.google.com/file/d/1GTT2tW3WV4H-8oDTeYEbFnpHsHKleBnA/view?usp=sharing, https://drive.google.com/file/d/1GVnNEvV_JL-RfhiLcilpuTGpE_L2EVSB/view?usp=sharing, https://drive.google.com/file/d/1GWA2Cy5so8LafVd3hrehbWlnZtZCu96l/view?usp=sharing, https://drive.google.com/file/d/1Nc73m3B6VqapO6fKmQhZsz0XqBRC6qLx/view?usp=sharing, https://drive.google.com/file/d/1OFECl1W0TBgualvPFvzb1QC7TjbeS63t/view?usp=sharing, https://drive.google.com/file/d/1c3LTmRz47pvqw6MkqE5akustMqGG384E/view?usp=sharing, https://drive.google.com/file/d/1fVRlxEjtkFpTafU6-MrRkTNhJ8ROqHRS/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221ky-GUobTN6gjyn85sXTPYJRKdg4YATwW%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1t_7xdLQGnvDNwIDz9JRwAlVdm0OjPIVR/view?usp=sharing

