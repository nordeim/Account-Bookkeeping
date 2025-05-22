# File: Technical Design Specification Document (v2).md
# Technical Design Specification Document: Singapore Small Business Bookkeeping Application

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document provides comprehensive implementation details for developing a Singapore-compliant small business bookkeeping application using Python with PySide6 (or PyQt6) for the frontend and PostgreSQL for data storage. The document translates the Product Requirements Document into actionable technical specifications, code structures, database schemas, and implementation approaches, reflecting the current design based on the comprehensive reference database schema.

### 1.2 Scope
This TDS covers all technical aspects of the application including:
- System architecture and component design
- Database schema (aligned with `scripts/schema.sql`) and relationships
- UI implementation details (selected examples)
- Business logic implementation (selected examples)
- Code structure and organization
- Security implementation considerations
- Deployment specifications

### 1.3 Intended Audience
- Software developers responsible for implementation
- QA engineers for testing guidance
- System administrators for deployment planning
- Technical project managers for resource planning

### 1.4 System Overview
The Singapore Small Business Bookkeeping Application is a desktop application built with Python and PySide6 that provides comprehensive accounting capabilities for small businesses in Singapore. The application handles double-entry bookkeeping, tax management (GST, income tax estimation), financial reporting, and core business operations like invoicing and banking (though full implementation of all business operations is ongoing). It aims for compliance with Singapore's accounting standards and tax regulations, based on the provided comprehensive database schema.

## 2. System Architecture

### 2.1 High-Level Architecture
The application follows a three-tier architecture:

```
+---------------------------------------------------+
|                  Presentation Layer                |
|  (PySide6 UI Components, Custom Widgets)          |
+---------------------------------------------------+
                         |
                         v
+---------------------------------------------------+
|                  Business Logic Layer              |
|   (Core Modules, Managers, Services)               |
+---------------------------------------------------+
                         |
                         v
+---------------------------------------------------+
|                  Data Access Layer                 |
|      (SQLAlchemy ORM, PostgreSQL Connector)        |
+---------------------------------------------------+
                         |
                         v
+---------------------------------------------------+
|                  Database                          |
|                (PostgreSQL)                        |
+---------------------------------------------------+
```

### 2.2 Component Architecture

#### 2.2.1 Core Components
- **ApplicationCore**: Central component managing application lifecycle, service/manager access.
- **ModuleManager**: Handles module loading and inter-module communication (conceptual).
- **SecurityManager**: Controls authentication and authorization using `core.users`, `core.roles`, `core.permissions`.
- **ConfigManager**: Manages application configuration from `config.ini`.
- **DatabaseManager**: Handles PostgreSQL database connections and transactions via SQLAlchemy and asyncpg.

#### 2.2.2 Functional Components (Managers/Services)
- **Accounting Logic**:
    - `ChartOfAccountsManager`: Manages `accounting.accounts`.
    - `JournalEntryManager`: Manages `accounting.journal_entries` and `accounting.recurring_patterns`.
    - `FiscalPeriodManager`: Manages `accounting.fiscal_years` and `accounting.fiscal_periods`.
    - `CurrencyManager`: Manages `accounting.currencies` and `accounting.exchange_rates`.
- **Tax Logic**:
    - `GSTManager`: Handles GST calculations and `accounting.gst_returns`.
    - `TaxCalculator`: Generic tax calculation logic.
    - (Conceptual: `IncomeTaxManager`, `WithholdingTaxManager`)
- **Reporting Logic**:
    - `FinancialStatementGenerator`: Generates Balance Sheet, P&L, Trial Balance.
    - `ReportEngine`: Exports reports to PDF/Excel.
    - (Conceptual: `TaxReportGenerator`)
- **Data Services**:
    - `AccountService`, `JournalService`, `FiscalPeriodService`, `TaxCodeService`, etc.: Provide repository-like data access operations for ORM models.
    - `SequenceService`: Manages document numbering via `core.sequences` table.

#### 2.2.3 User Interface Components
- **MainWindow**: Main application window and navigation tabs.
- **Module Widgets** (`DashboardWidget`, `AccountingWidget`, etc.): Top-level UI for each module.
- **Detail Widgets** (`ChartOfAccountsWidget`, etc.): Specific functional screens.
- **Dialogs** (`AccountDialog`, etc.): For data entry and interaction.
- (Conceptual: `FormManager`, `DialogManager`, `ThemeManager` from original TDS if UI becomes more complex).

### 2.3 Component Interactions
Sequence diagram for posting a transaction (remains conceptually similar, but involves more detailed models and potentially new services/managers for source documents like invoices):

```
User        UIComponent    BusinessManager   JournalEntryManager   DatabaseManager
 |               | (e.g. InvoiceScreen)| (e.g. InvoiceManager) |                     |
 |--Request new invoice-->|                |                     |                     |
 |               |--Initialize form---->|                     |                     |
 |               |<-------Return form----|                     |                     |
 |<--Show form-->|              |                              |                     |
 |--Input data-->|              |                              |                     |
 |--Submit------>|--Process invoice--->|                     |                     |
 |               |              |--Create Invoice DTO-->      |                     |
 |               |              |--Save Invoice (DB)-------->|--Save Invoice Obj-->| DB
 |               |              |                              |<----Confirm Save----|
 |               |              |--Generate JE Data----------->|                     |
 |               |              |                              |<--Create JE DTO---->|
 |               |              |                              |--Validate/Save JE-->|--Save JE Obj-->| DB
 |               |              |                              |<----Confirm JE Save--|                |
 |               |<-------Confirm success----------------------|                     |                |
 |<--Show result>|              |                              |                     |                |
```
*(Note: Actual JE creation might be part of InvoiceManager's logic or a dedicated TransactionManager)*

### 2.4 Technology Stack Specification

#### 2.4.1 Frontend Technologies
- **UI Framework**: PySide6 6.2.3+ (or PyQt6 6.2.3+)
- **Python Version**: 3.9+
- **Widget Extensions**: (Conceptual: QScintilla, QtCharts, if used)
- **Styling**: Qt Style Sheets.
- **Icons**: SVG icons (direct file access or via Qt Resource System).

#### 2.4.2 Backend Technologies
- **Database ORM**: SQLAlchemy 1.4+ (actually using features compatible with 2.0 style Mapped ORM) with asyncio support.
- **Database Connector**: `asyncpg` for async operations.
- **Migration Tool**: (Conceptual: Alembic; current setup uses `schema.sql` for init).
- **Data Validation**: Pydantic for DTOs.
- **Reporting**: ReportLab for PDF, openpyxl for Excel.
- **Password Hashing**: bcrypt.

#### 2.4.3 Database
- **PostgreSQL**: Version 14+
- **Extensions Used**: `pgcrypto`, `pg_stat_statements`, `btree_gist` (as per `schema.sql`).
- **Connection Pooling**: Implemented in `DatabaseManager` using SQLAlchemy's pool and asyncpg's pool.

### 2.5 Design Patterns

#### 2.5.1 Application-Wide Patterns
- **Model-View-Controller (MVC)/Model-View-ViewModel (MVVM)**: For UI components.
- **Repository Pattern (Service Layer)**: Data access abstraction (e.g., `AccountService` implementing `IAccountRepository`).
- **Factory Pattern**: (Conceptual: For UI components, report objects).
- **Observer Pattern**: Qt Signals/Slots for UI updates and inter-component communication.
- **Result Object Pattern**: For returning success/failure from service/manager methods.
- **Data Transfer Object (DTO)**: Pydantic models for structured data exchange between layers.

#### 2.5.2 Pattern Implementation Examples

**Repository (Service) Pattern Implementation** (Example: `AccountService`):
```python
# From app/services/account_service.py (Illustrative snippet)
class AccountService(IAccountRepository):
    def __init__(self, db_manager: DatabaseManager, app_core: Optional[Any] = None):
        self.db_manager = db_manager
        self.app_core = app_core 

    async def get_by_id(self, account_id: int) -> Optional[Account]:
        async with self.db_manager.session() as session:
            return await session.get(Account, account_id)
    
    async def save(self, account: Account) -> Account: # Covers create & update
        async with self.db_manager.session() as session:
            # User audit fields (created_by_user_id, updated_by_user_id)
            # are expected to be set on the 'account' object by the manager/caller.
            session.add(account)
            await session.flush() 
            await session.refresh(account)
            return account
```

**Result Object Pattern** (Example usage in `ChartOfAccountsManager`):
```python
# From app/accounting/chart_of_accounts_manager.py (Illustrative snippet)
    async def create_account(self, account_data: AccountCreateData) -> Result[Account]:
        validation_result = self.account_validator.validate_create(account_data)
        if not validation_result.is_valid:
            return Result.failure(validation_result.errors)
        
        existing = await self.account_service.get_by_code(account_data.code)
        if existing:
            return Result.failure([f"Account code '{account_data.code}' already exists."])
        
        # ... map DTO to ORM model ...
        # account = Account(...)
        # saved_account = await self.account_service.save(account)
        # return Result.success(saved_account)
        # ... (error handling) ...
```

## 3. Data Architecture

### 3.1 Database Schema Overview

The database schema is organized into four main PostgreSQL schemas:
1.  **`core`**: System tables (users, roles, permissions, company settings, configuration, sequences).
2.  **`accounting`**: Core accounting tables (chart of accounts, fiscal years/periods, journals, currencies, budgets, tax codes, GST returns, dimensions).
3.  **`business`**: Business operations tables (customers, vendors, products, inventory, invoices, payments, bank accounts).
4.  **`audit`**: Audit logging tables (audit log, data change history).

The complete schema is defined in `scripts/schema.sql` and is based on the comprehensive "create_database_schema (reference).md".

### 3.2 Core Entity Relationship Diagram (Conceptual Overview)

The database schema is now significantly more complex. Key entities and their high-level relationships include:

*   **Core Entities**:
    *   `core.Users` <-> `core.Roles` (many-to-many via `core.user_roles`).
    *   `core.Roles` <-> `core.Permissions` (many-to-many via `core.role_permissions`).
    *   `core.CompanySettings` (usually one row).
    *   `core.Configuration` (key-value store).
    *   `core.Sequences` (for document numbering).
*   **Accounting Entities**:
    *   `accounting.Accounts` (hierarchical via `parent_id`, linked to `AccountTypes`, `Users` for audit).
    *   `accounting.FiscalYears` -> `accounting.FiscalPeriods` (one-to-many).
    *   `accounting.JournalEntries` -> `accounting.JournalEntryLines` (one-to-many).
    *   `JournalEntries` link to `FiscalPeriods`, `Users` (audit), `RecurringPatterns`.
    *   `JournalEntryLines` link to `Accounts`, `Currencies`, `TaxCodes`, `Dimensions`.
    *   `accounting.Budgets` link to `FiscalYears`, `Users`. `BudgetDetails` link to `Budgets`, `Accounts`, `FiscalPeriods`, `Dimensions`.
    *   `accounting.Currencies`, `accounting.ExchangeRates`.
    *   `accounting.TaxCodes` link to `Accounts` (affected GL).
    *   `accounting.GSTReturns` link to `Users` (audit), `JournalEntries` (payment JE).
    *   `accounting.Dimensions` (for analytical accounting).
    *   `accounting.RecurringPatterns` link to `JournalEntries` (template JE).
    *   `accounting.WithholdingTaxCertificates` link to `business.Vendors`, `JournalEntries`.
*   **Business Entities**:
    *   `business.Customers`, `business.Vendors` link to `Users` (audit), `Currencies`, `Accounts` (AR/AP control).
    *   `business.Products` link to `Accounts` (sales, purchase, inventory GLs), `TaxCodes`.
    *   `business.InventoryMovements` link to `Products`, `Users`.
    *   `business.SalesInvoices` -> `business.SalesInvoiceLines` (one-to-many). `SalesInvoices` link to `Customers`, `Currencies`, `JournalEntries`. `SalesInvoiceLines` link to `Products`, `TaxCodes`, `Dimensions`.
    *   `business.PurchaseInvoices` structure similar to `SalesInvoices`, linking to `Vendors`.
    *   `business.BankAccounts` link to `Currencies`, `Accounts` (GL).
    *   `business.BankTransactions` link to `BankAccounts`, `JournalEntries`.
    *   `business.Payments` -> `business.PaymentAllocations` (one-to-many). `Payments` link to `Customers`/`Vendors`, `BankAccounts`, `Currencies`, `JournalEntries`.
*   **Audit Entities**:
    *   `audit.AuditLog`, `audit.DataChangeHistory` link to `Users`.

*(A full graphical ERD for this comprehensive schema would be very large and is best viewed with a database modeling tool based on `scripts/schema.sql`)*

### 3.3 Detailed Schema Definitions (Selected Examples)

The full DDL is in `scripts/schema.sql`. Below are examples of key tables reflecting the updated schema.

**`core.users` Table**:
```sql
CREATE TABLE core.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    failed_login_attempts INTEGER DEFAULT 0,
    last_login_attempt TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    require_password_change BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**`accounting.accounts` Table**:
```sql
CREATE TABLE accounting.accounts (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')),
    sub_type VARCHAR(30),
    tax_treatment VARCHAR(20),
    gst_applicable BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    parent_id INTEGER REFERENCES accounting.accounts(id),
    report_group VARCHAR(50),
    is_control_account BOOLEAN DEFAULT FALSE,
    is_bank_account BOOLEAN DEFAULT FALSE,
    opening_balance NUMERIC(15,2) DEFAULT 0,
    opening_balance_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);
```

**`accounting.fiscal_years` Table**:
```sql
CREATE TABLE accounting.fiscal_years (
    id SERIAL PRIMARY KEY,
    year_name VARCHAR(20) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_closed BOOLEAN DEFAULT FALSE,
    closed_date TIMESTAMP WITH TIME ZONE,
    closed_by INTEGER REFERENCES core.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id),
    CONSTRAINT fy_date_range_check CHECK (start_date <= end_date),
    CONSTRAINT fy_unique_date_ranges EXCLUDE USING gist (
        daterange(start_date, end_date, '[]') WITH &&
    )
);
```

**`business.sales_invoices` Table (Example of new business table)**:
```sql
CREATE TABLE business.sales_invoices (
    id SERIAL PRIMARY KEY,
    invoice_no VARCHAR(20) NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL REFERENCES business.customers(id),
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    currency_code CHAR(3) NOT NULL REFERENCES accounting.currencies(code),
    exchange_rate NUMERIC(15,6) DEFAULT 1,
    subtotal NUMERIC(15,2) NOT NULL,
    tax_amount NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_amount NUMERIC(15,2) NOT NULL,
    amount_paid NUMERIC(15,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN (
        'Draft', 'Approved', 'Sent', 'Partially Paid', 'Paid', 'Overdue', 'Voided'
    )),
    notes TEXT,
    terms_and_conditions TEXT,
    journal_entry_id INTEGER REFERENCES accounting.journal_entries(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);
```

*(Refer to `scripts/schema.sql` for all table definitions)*

### 3.4 Data Access Layer

#### 3.4.1 SQLAlchemy ORM Model Definitions (Selected Examples)

Models are now organized into subdirectories under `app/models/` (e.g., `app/models/core/`, `app/models/accounting/`).

**`Account` Model** (from `app/models/accounting/account.py`):
```python
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, CheckConstraint, Date, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column
from decimal import Decimal
import datetime
from typing import List, Optional 

from app.models.base import Base, TimestampMixin 
from app.models.core.user import User 

class Account(Base, TimestampMixin):
    __tablename__ = 'accounts'
    __table_args__ = (
         CheckConstraint("account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')", name='ck_accounts_account_type_category'),
        {'schema': 'accounting'}
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    # ... (other fields as per app/models/accounting/account.py) ...
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    opening_balance_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)
        
    parent: Mapped[Optional["Account"]] = relationship("Account", remote_side=[id], back_populates="children", foreign_keys=[parent_id])
    # ... (other relationships) ...
```

**`JournalEntry` Model** (from `app/models/accounting/journal_entry.py`):
```python
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Text, DateTime, Date
from sqlalchemy.orm import relationship, Mapped, mapped_column
from decimal import Decimal
import datetime
from typing import List, Optional 

from app.models.base import Base, TimestampMixin
from app.models.accounting.fiscal_period import FiscalPeriod
# ... (other necessary imports)

class JournalEntry(Base, TimestampMixin):
    __tablename__ = 'journal_entries'
    __table_args__ = {'schema': 'accounting'}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    entry_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    # ... (other fields as per app/models/accounting/journal_entry.py) ...
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    # ... (other relationships) ...
```

**`SalesInvoice` Model (Example of new business model)** (from `app/models/business/sales_invoice.py`):
```python
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
import datetime
from typing import List, Optional 

from app.models.base import Base, TimestampMixin
# ... (other necessary imports for Customer, Currency, User, JournalEntry)

class SalesInvoice(Base, TimestampMixin):
    __tablename__ = 'sales_invoices'
    __table_args__ = (
        CheckConstraint("status IN ('Draft', 'Approved', 'Sent', 'Partially Paid', 'Paid', 'Overdue', 'Voided')", name='ck_sales_invoices_status'),
        {'schema': 'business'}
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    # ... (all fields as defined in app/models/business/sales_invoice.py) ...
```

*(Refer to `app/models/` directory for all ORM model definitions)*

#### 3.4.2 Data Access Interface (Repository Interfaces)

These interfaces (defined in `app/services/__init__.py`) guide the implementation of service classes.

**`IAccountRepository` Interface**:
```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any # Added Dict, Any
from app.models.accounting.account import Account # Corrected path

class IAccountRepository(ABC): # Simplified to match AccountService methods
    @abstractmethod
    async def get_by_id(self, account_id: int) -> Optional[Account]: pass
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Account]: pass
    @abstractmethod
    async def get_all_active(self) -> List[Account]: pass
    @abstractmethod
    async def get_by_type(self, account_type: str, active_only: bool = True) -> List[Account]: pass # Added active_only
    @abstractmethod
    async def save(self, account: Account) -> Account: pass # Create or Update
    # delete is soft via manager. Hard delete in IRepository context.
    # @abstractmethod
    # async def delete(self, account_id: int) -> bool: pass
    @abstractmethod
    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]: pass # Added active_only
    @abstractmethod
    async def has_transactions(self, account_id: int) -> bool: pass
```

**`IJournalEntryRepository` Interface**:
```python
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from decimal import Decimal # Added Decimal
from app.models.accounting.journal_entry import JournalEntry # Corrected path
from app.models.accounting.recurring_pattern import RecurringPattern # Corrected path

class IJournalEntryRepository(ABC):
    @abstractmethod
    async def get_by_id(self, journal_id: int) -> Optional[JournalEntry]: pass
    @abstractmethod
    async def get_by_entry_no(self, entry_no: str) -> Optional[JournalEntry]: pass
    @abstractmethod
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]: pass
    @abstractmethod
    async def get_posted_entries_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]: pass
    @abstractmethod
    async def save(self, journal_entry: JournalEntry) -> JournalEntry: pass
    # post and reverse are business logic, manager's responsibility
    # @abstractmethod
    # async def post(self, journal_id: int) -> bool: pass
    # @abstractmethod
    # async def reverse(self, journal_id: int, reversal_date: date, description: str) -> Optional[JournalEntry]: pass
    @abstractmethod
    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal: pass
    @abstractmethod
    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal: pass
    @abstractmethod
    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]: pass
    @abstractmethod
    async def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern: pass
```

## 4. Module Specifications

### 4.1 Core Accounting Module

#### 4.1.1 Chart of Accounts Manager (`app.accounting.chart_of_accounts_manager.py`)

**Responsibilities**:
- Manage account hierarchy (CRUD operations for `accounting.accounts`).
- Validate account data using Pydantic DTOs (`AccountCreateData`, `AccountUpdateData`).
- Handle creation of accounts with opening balances.
- Ensure account code uniqueness.
- Deactivate accounts (soft delete) with checks for balance and transactions.

**Key Functions** (Illustrative snippets, refer to Python file for full code):
```python
# From app/accounting/chart_of_accounts_manager.py
class ChartOfAccountsManager:
    # ... (__init__) ...
    async def create_account(self, account_data: AccountCreateData) -> Result[Account]:
        # ... (validation as before) ...
        account = Account(
            # ... map all fields from AccountCreateData including new ones like:
            opening_balance=account_data.opening_balance,
            opening_balance_date=account_data.opening_balance_date,
            report_group=account_data.report_group,
            # ... created_by_user_id and updated_by_user_id from account_data.user_id
        )
        # ... (save via account_service) ...

    async def update_account(self, account_data: AccountUpdateData) -> Result[Account]:
        # ... (validation and fetch existing_account) ...
        # ... (update all mappable fields from AccountUpdateData to existing_account) ...
        # existing_account.updated_by_user_id = account_data.user_id
        # ... (save via account_service) ...

    async def deactivate_account(self, account_id: int, user_id: int) -> Result[Account]:
        # ... (fetch account) ...
        # Enhanced balance check:
        # total_current_balance = await self.app_core.journal_service.get_account_balance(account_id, date.today())
        # if total_current_balance != Decimal(0):
        #     return Result.failure([... "non-zero balance" ...])
        # ... (update is_active and updated_by_user_id, save) ...

    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]:
        return await self.account_service.get_account_tree(active_only=active_only)
```

#### 4.1.2 Journal Entry Manager (`app.accounting.journal_entry_manager.py`)

**Responsibilities**:
- Create and (optionally) post journal entries using `JournalEntryData` DTO.
- Validate balanced transactions (now primarily via Pydantic DTO).
- Link JEs to `FiscalPeriods`, `RecurringPatterns`, and source documents (e.g., Invoices via `source_type`/`source_id`).
- Generate recurring entries based on `RecurringPattern` and `template_entry_id`.
- Reverse posted entries, creating a counter-entry.
- Use `SequenceGenerator` (DB-backed via `core.sequences`) for `entry_no`.

**Key Functions** (Illustrative snippets):
```python
# From app/accounting/journal_entry_manager.py
class JournalEntryManager:
    # ... (__init__ with dependencies: JournalService, AccountService, FiscalPeriodService, SequenceGenerator, AppCore) ...
    async def create_journal_entry(self, entry_data: JournalEntryData) -> Result[JournalEntry]:
        # ... (get fiscal_period, generate entry_no) ...
        journal_entry_orm = JournalEntry(
            # ... map fields from entry_data including new:
            source_type=entry_data.source_type,
            source_id=entry_data.source_id,
            # ... created_by_user_id and updated_by_user_id from entry_data.user_id
        )
        # ... (create JournalEntryLine ORM objects from DTO, append to journal_entry_orm.lines) ...
        # ... (save via journal_service) ...

    async def post_journal_entry(self, entry_id: int, user_id: int) -> Result[JournalEntry]:
        # ... (fetch entry, check fiscal period status) ...
        # entry.is_posted = True
        # entry.updated_by_user_id = user_id
        # ... (save via journal_service) ...

    async def reverse_journal_entry(self, entry_id: int, reversal_date: date, description: Optional[str], user_id: int) -> Result[JournalEntry]:
        # ... (fetch original_entry, validate) ...
        # Create reversal_entry_data (JournalEntryData DTO) with swapped debits/credits, negated tax.
        # reversal_entry_data.source_type = "JournalEntryReversal"
        # reversal_entry_data.source_id = original_entry.id
        # create_reversal_result = await self.create_journal_entry(reversal_entry_data)
        # ... (if success, update original_entry.is_reversed and reversing_entry_id, save original) ...

    async def generate_recurring_entries(self, as_of_date: date, user_id: int) -> List[Result[JournalEntry]]:
        # patterns_due = await self.journal_service.get_recurring_patterns_due(as_of_date)
        # For each pattern:
        #   Fetch template_entry = await self.journal_service.get_by_id(pattern.template_entry_id)
        #   Construct new_je_data (JournalEntryData) from template_entry.
        #   new_je_data.recurring_pattern_id = pattern.id (links generated JE to its pattern)
        #   create_result = await self.create_journal_entry(new_je_data)
        #   Update pattern.last_generated_date, pattern.next_generation_date, save pattern.
        # ... 
```

### 4.2 Tax Management Module

#### 4.2.1 GST Manager (`app.tax.gst_manager.py`)

**Responsibilities**:
- Calculate GST (delegated to `TaxCalculator` or simple logic).
- Prepare `GSTReturnData` DTO for GST F5 form based on posted transactions in `accounting.journal_entry_lines` and `accounting.tax_codes`.
- Save draft `accounting.gst_returns` and finalize them.
- Generate journal entry for GST payment/refund, linking to `accounting.gst_returns.journal_entry_id`.

**Key Functions** (Illustrative snippets):
```python
# From app/tax/gst_manager.py
class GSTManager:
    # ... (__init__ with dependencies: TaxCodeService, JournalService, CompanySettingsService, GSTReturnService, AccountService, FiscalPeriodService, SequenceGenerator, AppCore) ...
    async def prepare_gst_return_data(self, start_date: date, end_date: date) -> Result[GSTReturnData]:
        # ... (fetch company_settings, posted JEs in date range) ...
        # Iterate JEs/lines, use TaxCode.code ('SR', 'ZR', 'ES', 'TX') and Account.account_type
        # to categorize amounts into GSTReturnData fields (standard_rated_supplies, etc.).
        # gst_return_form = GSTReturnData(...)
        # ...
        # return Result.success(gst_return_form)

    async def save_draft_gst_return(self, gst_return_data: GSTReturnData) -> Result[GSTReturn]:
        # gst_return_orm = GSTReturn(**gst_return_data.dict(...), created_by_user_id=..., updated_by_user_id=...)
        # saved_return = await self.gst_return_service.save_gst_return(gst_return_orm)
        # ...

    async def finalize_gst_return(self, return_id: int, submission_reference: str, submission_date: date, user_id: int) -> Result[GSTReturn]: # user_id from app_core
        # ... (fetch gst_return_orm, update status, submission details, updated_by_user_id) ...
        # updated_return = await self.gst_return_service.save_gst_return(gst_return_orm)
        # If updated_return.tax_payable != 0:
        #   await self._create_gst_payment_entry(updated_return, user_id)
        # ...
```

### 4.3 Financial Reporting Module

#### 4.3.1 Financial Statement Generator (`app.reporting.financial_statement_generator.py`)

**Responsibilities**:
- Generate Balance Sheet, Profit & Loss, Trial Balance data.
- Utilize `AccountService` and `JournalService` (especially `get_account_balance` which now includes `Account.opening_balance`).
- Format reports (data structure for `ReportEngine`).
- Generate data for GST F5 (similar to `GSTManager` but for reporting view).

**Key Functions** (Illustrative snippets):
```python
# From app/reporting/financial_statement_generator.py
class FinancialStatementGenerator:
    # ... (__init__ with dependencies: AccountService, JournalService, FiscalPeriodService,
    #      Optional: TaxCodeService, CompanySettingsService for GST F5 method) ...
    async def generate_balance_sheet(self, as_of_date: date, comparative_date: Optional[date] = None, ...) -> Dict[str, Any]:
        # accounts = await self.account_service.get_all_active()
        # For each account category (Asset, Liability, Equity):
        #   balances = await self._calculate_account_balances_for_report(category_accounts, as_of_date)
        #   (This helper would use journal_service.get_account_balance which includes opening_balance)
        # ... (structure report_data dictionary) ...

    async def generate_profit_loss(self, start_date: date, end_date: date, ...) -> Dict[str, Any]:
        # accounts = await self.account_service.get_all_active()
        # For Revenue & Expense accounts:
        #   activity = await self._calculate_account_period_activity_for_report(category_accounts, start_date, end_date)
        #   (This helper would use journal_service.get_account_balance_for_period)
        # ... (structure report_data: total_revenue, total_expenses, net_profit) ...

    async def generate_trial_balance(self, as_of_date: date) -> Dict[str, Any]:
        # accounts = await self.account_service.get_all_active()
        # For each account:
        #   balance = await self.journal_service.get_account_balance(account.id, as_of_date)
        #   Categorize into debit_accounts / credit_accounts based on Account.account_type (or AccountType.is_debit_balance)
        #   and sign of balance. The reference schema's trial_balance view is a good guide.
        # ...
```

## 5. User Interface Implementation

*(This section remains largely conceptual for new features, focusing on updates to existing examples.)*

### 5.1 Main Application Structure (`app/main.py`)
- Initializes `ConfigManager`, `DatabaseManager`, `ApplicationCore`.
- `ApplicationCore.startup()` now initializes all core services and managers.
- Uses platform-specific user config directory for `config.ini`.
- Splash screen logic remains.

### 5.2 Main Window Implementation (`app/ui/main_window.py`)
- Structure with `QTabWidget` for modules.
- Toolbar and menu actions.
- Status bar displaying user, version.
- `closeEvent` saves window geometry/state to `QSettings`.
- No major changes due to schema refactor, but underlying data for widgets will be richer.

### 5.3 Chart of Accounts Screen (`app/ui/accounting/chart_of_accounts_widget.py`)

-   `_load_accounts()`: Calls `app_core.accounting_service.get_account_tree()` (which is `ChartOfAccountsManager.get_account_tree()`). The tree data from `AccountService.get_account_tree()` now includes more fields from the `Account` model (e.g., `report_group`, `opening_balance`). The `_add_account_to_model` method might display these or they can be used for tooltips/details.
-   `on_add_account()`, `on_edit_account()`: Launch `AccountDialog`.
    -   `AccountDialog` will need to be updated to include input fields for new `Account` attributes like `opening_balance`, `opening_balance_date`, `report_group`, `is_control_account`, `is_bank_account`.
    -   When saving, `AccountDialog` will pass an updated `AccountCreateData` or `AccountUpdateData` DTO (from `pydantic_models.py`) to the manager.
-   `on_deactivate_account()`: Calls `app_core.accounting_service.deactivate_account()`. The manager's logic for deactivation now checks for zero balance (including opening balance).

**`AccountDialog` (Conceptual Update)**
```python
# From app/ui/accounting/account_dialog.py (Conceptual Additions)
class AccountDialog(QDialog):
    # ... (existing __init__, code_edit, name_edit, etc.)
    # Add new QLineEdits/QCheckBoxes/QDateEdits for:
    # self.opening_balance_edit = QLineEdit()
    # self.opening_balance_date_edit = QDateEdit()
    # self.report_group_edit = QLineEdit()
    # self.is_control_account_check = QCheckBox("Is Control Account")
    # self.is_bank_account_check = QCheckBox("Is Bank Account")
    # ... (add to form_layout)

    # In on_save():
    #   Gather values from new fields.
    #   Populate AccountCreateData/AccountUpdateData with these new fields.
    #   Pass to manager.

    # In load_account_data() (for editing):
    #   Populate new form fields from the loaded Account ORM object.
```

## 6. Business Logic Implementation

### 6.1 Tax Calculation Logic (`app/tax/tax_calculator.py`)
- Uses `TaxCodeService` to fetch `TaxCode` details.
- `TaxCode` model structure is largely the same for rate/type.
- Logic for `_calculate_gst` and `_calculate_withholding_tax` remains conceptually similar but uses `Decimal`.

### 6.2 Financial Reporting Logic (`app/reporting/financial_statement_generator.py`)
- `generate_trial_balance` now correctly considers `Account.opening_balance` and `AccountType.is_debit_balance` via the `accounting.trial_balance` view logic (or similar Python implementation).
- `generate_income_tax_computation` uses `FiscalYear` model. The method to get "Tax Adjustment" accounts via `Account.tax_treatment` is retained.
- `generate_gst_f5` uses `CompanySettings` and `TaxCode` information.

## 7. Database Access Implementation

### 7.1 Database Manager (`app/core/database_manager.py`)
- No significant changes. Initializes SQLAlchemy engine and `asyncpg` pool based on `ConfigManager`.

### 7.2 Repository Implementation (Example: `AccountService`)
- File moved to `app/services/account_service.py`.
- Implements `IAccountRepository`.
- `save()` method handles ORM object persistence.
- `get_account_tree()` uses a recursive CTE SQL query which now includes new `Account` fields.
- `has_transactions()` now considers `opening_balance` activity.
- Other services (`JournalService`, `FiscalPeriodService`, `TaxCodeService`, `GSTReturnService`, new `core_services.SequenceService`, `CompanySettingsService`) follow similar patterns for their respective models.

```python
# Example snippet from app/services/account_service.py
class AccountService(IAccountRepository):
    # ... (__init__) ...
    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]:
        # ... (SQL query now selects new fields like report_group, opening_balance) ...
        # ... (Tree construction logic) ...
        return tree_roots
```

## 8. Deployment and Installation

### 8.1 Application Packaging (`pyproject.toml`)
The project uses Poetry for dependency management and packaging.
```toml
# pyproject.toml (Key sections)
[tool.poetry]
name = "sg-bookkeeper"
version = "1.0.0"
# ... (other metadata) ...
packages = [{include = "app", from = "."}]

[tool.poetry.dependencies]
python = "^3.9"
PySide6 = ">=6.2.3"
SQLAlchemy = {extras = ["asyncio"], version = ">=1.4.0"}
asyncpg = ">=0.25.0"
alembic = ">=1.7.5" # For future migrations
pydantic = ">=1.9.0"
reportlab = ">=3.6.6"
openpyxl = ">=3.0.9"
python-dateutil = ">=2.8.2"
bcrypt = ">=3.2.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
# ... (other dev dependencies) ...

[tool.poetry.scripts]
sg_bookkeeper = "app.main:main"
sg_bookkeeper_db_init = "scripts.db_init:main"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
```

### 8.2 Database Initialization Script (`scripts/db_init.py`)
- The script `scripts/db_init.py` is responsible for database setup.
- It connects to PostgreSQL and executes SQL commands from:
    - `scripts/schema.sql`: Contains the complete DDL for all schemas (core, accounting, business, audit), tables, views, functions, and triggers, based on the comprehensive reference schema.
    - `scripts/initial_data.sql`: Contains SQL INSERT statements for seeding default data (roles, permissions, currencies, sequences, account types, tax codes), also from the reference schema.
- It can create the database if it doesn't exist and optionally drop an existing database.
- Usage: `poetry run sg_bookkeeper_db_init --user <pg_user> --dbname <db_name> [--drop-existing]`

### 8.3 Application Installation Guide
Refer to `deployment_guide.md` for detailed installation and setup instructions. Key steps involve:
1.  Cloning the repository/extracting source.
2.  Installing PostgreSQL 14+.
3.  Setting up a Python 3.9+ environment.
4.  Installing dependencies using `poetry install`.
5.  Configuring database connection in `config.ini` (located in user's app config directory).
6.  Running `poetry run sg_bookkeeper_db_init` to set up the database.
7.  Running `poetry run sg_bookkeeper` to start the application.

## 9. Conclusion

This updated Technical Design Specification reflects the application's design after aligning with a more comprehensive and detailed database schema. The model layer has been significantly expanded and organized, and core services and managers have been adapted to these changes. While the foundational architecture remains, the data model now supports a much richer set of accounting and business functionalities. Further development will focus on fully implementing the business logic for these new entities and enhancing the user interface to manage the expanded data scope.
