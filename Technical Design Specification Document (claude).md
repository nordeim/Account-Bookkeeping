# Technical Design Specification Document: Singapore Small Business Bookkeeping Application
# Claude 3.7

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document provides comprehensive implementation details for developing a Singapore-compliant small business bookkeeping application using Python with PyQt/PySide for the frontend and PostgreSQL for data storage. The document translates the Product Requirements Document into actionable technical specifications, code structures, database schemas, and implementation approaches.

### 1.2 Scope
This TDS covers all technical aspects of the application including:
- System architecture and component design
- Database schema and relationships
- UI implementation details
- Business logic implementation
- Code structure and organization
- Security implementation
- Deployment specifications

### 1.3 Intended Audience
- Software developers responsible for implementation
- QA engineers for testing guidance
- System administrators for deployment planning
- Technical project managers for resource planning

### 1.4 System Overview
The Singapore Small Business Bookkeeping Application is a desktop application built with Python and PyQt6/PySide6 that provides comprehensive accounting capabilities for small businesses in Singapore. The application handles double-entry bookkeeping, tax management (particularly GST and income tax), financial reporting, and business operations like invoicing and banking, all while ensuring compliance with Singapore's accounting standards and tax regulations.

## 2. System Architecture

### 2.1 High-Level Architecture
The application follows a three-tier architecture:

```
+---------------------------------------------------+
|                  Presentation Layer                |
|  (PyQt6/PySide6 UI Components, QML Custom Widgets) |
+---------------------------------------------------+
                         |
                         v
+---------------------------------------------------+
|                  Business Logic Layer              |
|   (Core Modules, Tax Engine, Reporting Engine)     |
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
- **ApplicationCore**: Central component managing application lifecycle
- **ModuleManager**: Handles module loading and inter-module communication
- **SecurityManager**: Controls authentication and authorization
- **ConfigManager**: Manages application configuration
- **DatabaseManager**: Handles database connections and transactions

#### 2.2.2 Functional Components
- **AccountingEngine**: Core accounting functions and rules
- **TaxEngine**: Tax calculation and compliance
- **ReportingEngine**: Financial report generation
- **DocumentEngine**: Document creation and management
- **ImportExportManager**: Data import/export capabilities

#### 2.2.3 User Interface Components
- **MainWindow**: Main application window and navigation
- **UIComponentLibrary**: Reusable UI components
- **FormManager**: Form rendering and validation
- **DialogManager**: Dialog rendering and lifecycle
- **ThemeManager**: Application styling and theming

### 2.3 Component Interactions
The following sequence diagram illustrates the high-level interaction flow for posting a transaction:

```
User        UIComponent    FormManager    AccountingEngine    DatabaseManager
 |               |              |                |                  |
 |--Request new transaction---->|                |                  |
 |               |--Initialize form------------>|                  |
 |               |<-------Return form-----------|                  |
 |<--Show form-->|              |                |                  |
 |--Input data-->|              |                |                  |
 |--Submit------>|              |                |                  |
 |               |--Validate data-------------->|                  |
 |               |<-------Validation result-----|                  |
 |               |--Process transaction-------->|                  |
 |               |              |<---Create journal entries------->|
 |               |              |                |<--Store in DB-->|
 |               |              |                |<--Confirm save--|
 |               |<-------Confirm success--------|                  |
 |<--Show result>|              |                |                  |
 |               |              |                |                  |
```

### 2.4 Technology Stack Specification

#### 2.4.1 Frontend Technologies
- **UI Framework**: PyQt6 6.2.3+ or PySide6 6.2.3+
- **Python Version**: 3.9+
- **Widget Extensions**: QScintilla for code editing, QtCharts for visualizations
- **Styling**: Qt Style Sheets and QSS variables for theming
- **Icons**: Custom SVG icon set with theme support

#### 2.4.2 Backend Technologies
- **Database ORM**: SQLAlchemy 1.4+ with asyncio support
- **Database Connector**: asyncpg for async operations, psycopg2 for synchronous operations
- **Migration Tool**: Alembic for schema migrations
- **Data Validation**: Pydantic for data models and validation
- **Reporting**: ReportLab 3.6+ for PDF generation, openpyxl for Excel generation

#### 2.4.3 Database
- **PostgreSQL**: Version 14+
- **Extensions**: pgcrypto, temporal_tables, pg_stat_statements
- **Connection Pooling**: Internal connection pool with min=2, max=10 connections

### 2.5 Design Patterns

#### 2.5.1 Application-Wide Patterns
- **Model-View-Controller (MVC)**: Separation of data, presentation, and control logic
- **Repository Pattern**: Data access abstraction for database operations
- **Factory Pattern**: Object creation, particularly for UI components and business entities
- **Observer Pattern**: Event handling for UI updates and inter-module communication
- **Command Pattern**: For transactional operations with undo capability

#### 2.5.2 Pattern Implementation Examples

**Repository Pattern Implementation**:
```python
class AccountRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        
    async def get_by_id(self, account_id):
        async with self.session_factory() as session:
            return await session.query(Account).filter(Account.id == account_id).first()
            
    async def save(self, account):
        async with self.session_factory() as session:
            session.add(account)
            await session.commit()
            return account
            
    async def get_active_accounts_by_type(self, account_type):
        async with self.session_factory() as session:
            return await session.query(Account).filter(
                Account.account_type == account_type,
                Account.is_active == True
            ).all()
```

**Factory Pattern Implementation**:
```python
class ReportFactory:
    @staticmethod
    def create_report(report_type, parameters):
        if report_type == "profit_loss":
            return ProfitAndLossReport(parameters)
        elif report_type == "balance_sheet":
            return BalanceSheetReport(parameters)
        elif report_type == "cash_flow":
            return CashFlowReport(parameters)
        elif report_type == "gst_f5":
            return GSTF5Report(parameters)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
```

## 3. Data Architecture

### 3.1 Database Schema Overview

The database schema is organized into four main schemas:

1. **core**: System tables and configuration
2. **accounting**: Core accounting tables
3. **business**: Business operations tables
4. **audit**: Audit and logging tables

### 3.2 Core Entity Relationship Diagram

The following diagram shows the relationships between the main accounting entities:

```
   +---------------+       +---------------+       +----------------+
   |   accounts    |       | fiscal_periods|       |journal_entries |
   +---------------+       +---------------+       +----------------+
   | id            |       | id            |       | id             |
   | code          |       | name          |       | entry_no       |
   | name          |       | start_date    |       | journal_type   |
   | account_type  |       | end_date      |       | entry_date     |
   | parent_id ---------+  | period_type   |       | fiscal_period_id -+
   +---------------+    |  | status        |       | description    |  |
           ^            |  +---------------+       | is_posted      |  |
           |            |         ^               +----------------+  |
           +------------+         |                      |            |
                                  +----------------------+            |
                                                                      |
   +----------------+                                                 |
   |journal_entry_lines          +------------------------+           |
   +----------------+            |      tax_codes         |           |
   | id             |            +------------------------+           |
   | journal_entry_id --------+  | id                     |           |
   | line_number    |         |  | code                   |           |
   | account_id ---------+    |  | description            |           |
   | description    |    |    |  | tax_type               |           |
   | debit_amount   |    |    |  | rate                   |           |
   | credit_amount  |    |    |  +------------------------+           |
   | tax_code_id ----------+                                          |
   +----------------+    |  |                                         |
                         |  |                                         |
           +-------------+  |                                         |
           |                +----------------------------------------+
           v
   +---------------+
   |   customers   |       +---------------+       +----------------+
   +---------------+       |    vendors    |       |    products    |
   | id            |       +---------------+       +----------------+
   | customer_code |       | id            |       | id             |
   | name          |       | vendor_code   |       | product_code   |
   | is_active     |       | name          |       | name           |
   +---------------+       | is_active     |       | product_type   |
                           +---------------+       +----------------+
```

### 3.3 Detailed Schema Definitions

#### 3.3.1 Core Schema Tables

**Users Table**:
```sql
CREATE TABLE core.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Roles Table**:
```sql
CREATE TABLE core.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Permissions Table**:
```sql
CREATE TABLE core.permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    module VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Role Permissions Table**:
```sql
CREATE TABLE core.role_permissions (
    role_id INTEGER NOT NULL REFERENCES core.roles(id),
    permission_id INTEGER NOT NULL REFERENCES core.permissions(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);
```

**User Roles Table**:
```sql
CREATE TABLE core.user_roles (
    user_id INTEGER NOT NULL REFERENCES core.users(id),
    role_id INTEGER NOT NULL REFERENCES core.roles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);
```

**Company Settings Table**:
```sql
CREATE TABLE core.company_settings (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    uen_no VARCHAR(20),
    gst_registration_no VARCHAR(20),
    address_line1 VARCHAR(100),
    address_line2 VARCHAR(100),
    postal_code VARCHAR(20),
    city VARCHAR(50) DEFAULT 'Singapore',
    country VARCHAR(50) DEFAULT 'Singapore',
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    website VARCHAR(100),
    logo BYTEA,
    fiscal_year_start_month INTEGER DEFAULT 1,
    fiscal_year_start_day INTEGER DEFAULT 1,
    base_currency VARCHAR(3) DEFAULT 'SGD',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.3.2 Accounting Schema Tables

The accounts and journals tables were already shown in the Product Requirements Document. Here are additional important tables:

**Account Types Table**:
```sql
CREATE TABLE accounting.account_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    category VARCHAR(20) NOT NULL CHECK (category IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')),
    is_debit_balance BOOLEAN NOT NULL,
    display_order INTEGER NOT NULL,
    description VARCHAR(200)
);
```

**Currency Table**:
```sql
CREATE TABLE accounting.currencies (
    code CHAR(3) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    decimal_places INTEGER DEFAULT 2,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Exchange Rates Table**:
```sql
CREATE TABLE accounting.exchange_rates (
    id SERIAL PRIMARY KEY,
    from_currency CHAR(3) NOT NULL REFERENCES accounting.currencies(code),
    to_currency CHAR(3) NOT NULL REFERENCES accounting.currencies(code),
    rate_date DATE NOT NULL,
    exchange_rate NUMERIC(15,6) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_currency_pair_date UNIQUE (from_currency, to_currency, rate_date)
);
```

**Budget Table**:
```sql
CREATE TABLE accounting.budgets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    fiscal_year INTEGER NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL,
    updated_by INTEGER NOT NULL
);
```

**Budget Details Table**:
```sql
CREATE TABLE accounting.budget_details (
    id SERIAL PRIMARY KEY,
    budget_id INTEGER NOT NULL REFERENCES accounting.budgets(id),
    account_id INTEGER NOT NULL REFERENCES accounting.accounts(id),
    period INTEGER NOT NULL CHECK (period BETWEEN 1 AND 12),
    amount NUMERIC(15,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_budget_account_period UNIQUE (budget_id, account_id, period)
);
```

### 3.4 Data Access Layer

#### 3.4.1 SQLAlchemy ORM Model Definitions

**Account Model**:
```python
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Account(Base):
    __tablename__ = 'accounts'
    __table_args__ = {'schema': 'accounting'}
    
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    account_type = Column(String(20), nullable=False)
    sub_type = Column(String(30))
    tax_treatment = Column(String(20))
    gst_applicable = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey('accounting.accounts.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=False)
    
    # Relationships
    parent = relationship("Account", remote_side=[id], backref="children")
    journal_lines = relationship("JournalEntryLine", back_populates="account")
```

**Journal Entry Model**:
```python
class JournalEntry(Base):
    __tablename__ = 'journal_entries'
    __table_args__ = {'schema': 'accounting'}
    
    id = Column(Integer, primary_key=True)
    entry_no = Column(String(20), unique=True, nullable=False)
    journal_type = Column(String(20), nullable=False)
    entry_date = Column(Date, nullable=False)
    fiscal_period_id = Column(Integer, ForeignKey('accounting.fiscal_periods.id'), nullable=False)
    description = Column(String(500))
    reference = Column(String(100))
    is_recurring = Column(Boolean, default=False)
    recurring_pattern_id = Column(Integer, ForeignKey('accounting.recurring_patterns.id'))
    is_posted = Column(Boolean, default=False)
    is_reversed = Column(Boolean, default=False)
    reversing_entry_id = Column(Integer, ForeignKey('accounting.journal_entries.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=False)
    
    # Relationships
    fiscal_period = relationship("FiscalPeriod")
    lines = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")
    recurring_pattern = relationship("RecurringPattern")
    reversing_entry = relationship("JournalEntry", remote_side=[id])
```

**Journal Entry Line Model**:
```python
class JournalEntryLine(Base):
    __tablename__ = 'journal_entry_lines'
    __table_args__ = {'schema': 'accounting'}
    
    id = Column(Integer, primary_key=True)
    journal_entry_id = Column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=False)
    line_number = Column(Integer, nullable=False)
    account_id = Column(Integer, ForeignKey('accounting.accounts.id'), nullable=False)
    description = Column(String(200))
    debit_amount = Column(Numeric(15, 2), default=0)
    credit_amount = Column(Numeric(15, 2), default=0)
    currency_code = Column(String(3), default='SGD')
    exchange_rate = Column(Numeric(15, 6), default=1)
    tax_code = Column(String(20))
    tax_amount = Column(Numeric(15, 2), default=0)
    dimension1_id = Column(Integer)
    dimension2_id = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    journal_entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account", back_populates="journal_lines")
    
    @validates('debit_amount', 'credit_amount')
    def validate_amounts(self, key, value):
        if key == 'debit_amount' and value > 0:
            self.credit_amount = 0
        elif key == 'credit_amount' and value > 0:
            self.debit_amount = 0
        return value
```

#### 3.4.2 Data Access Interface

**Account Repository Interface**:
```python
from abc import ABC, abstractmethod
from typing import List, Optional

class IAccountRepository(ABC):
    @abstractmethod
    async def get_by_id(self, account_id: int) -> Optional[Account]:
        pass
    
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Account]:
        pass
    
    @abstractmethod
    async def get_all_active(self) -> List[Account]:
        pass
    
    @abstractmethod
    async def get_by_type(self, account_type: str) -> List[Account]:
        pass
    
    @abstractmethod
    async def save(self, account: Account) -> Account:
        pass
    
    @abstractmethod
    async def delete(self, account_id: int) -> bool:
        pass
```

**Journal Entry Repository Interface**:
```python
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

class IJournalEntryRepository(ABC):
    @abstractmethod
    async def get_by_id(self, journal_id: int) -> Optional[JournalEntry]:
        pass
    
    @abstractmethod
    async def get_by_entry_no(self, entry_no: str) -> Optional[JournalEntry]:
        pass
    
    @abstractmethod
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        pass
    
    @abstractmethod
    async def save(self, journal_entry: JournalEntry) -> JournalEntry:
        pass
    
    @abstractmethod
    async def post(self, journal_id: int) -> bool:
        pass
    
    @abstractmethod
    async def reverse(self, journal_id: int, reversal_date: date, description: str) -> Optional[JournalEntry]:
        pass
```

## 4. Module Specifications

### 4.1 Core Accounting Module

#### 4.1.1 Chart of Accounts Manager

**Responsibilities**:
- Manage account hierarchy
- Create, update, and deactivate accounts
- Validate account code uniqueness
- Maintain proper account relationships

**Key Functions**:

```python
class ChartOfAccountsManager:
    def __init__(self, account_repository, account_validator):
        self.account_repository = account_repository
        self.account_validator = account_validator
    
    async def create_account(self, account_data):
        """Create a new account with validation"""
        # Validate account data
        validation_result = self.account_validator.validate(account_data)
        if not validation_result.is_valid:
            return Result.failure(validation_result.errors)
        
        # Check if code already exists
        existing = await self.account_repository.get_by_code(account_data.code)
        if existing:
            return Result.failure(["Account code already exists"])
        
        # Create new account
        account = Account(
            code=account_data.code,
            name=account_data.name,
            account_type=account_data.account_type,
            sub_type=account_data.sub_type,
            tax_treatment=account_data.tax_treatment,
            gst_applicable=account_data.gst_applicable,
            description=account_data.description,
            parent_id=account_data.parent_id,
            created_by=account_data.user_id,
            updated_by=account_data.user_id
        )
        
        # Save to database
        saved_account = await self.account_repository.save(account)
        return Result.success(saved_account)
    
    async def update_account(self, account_id, account_data):
        """Update an existing account with validation"""
        # Get existing account
        existing = await self.account_repository.get_by_id(account_id)
        if not existing:
            return Result.failure(["Account not found"])
        
        # Validate update data
        validation_result = self.account_validator.validate_update(account_data)
        if not validation_result.is_valid:
            return Result.failure(validation_result.errors)
        
        # Check for code uniqueness if code is changing
        if account_data.code != existing.code:
            code_exists = await self.account_repository.get_by_code(account_data.code)
            if code_exists:
                return Result.failure(["Account code already exists"])
        
        # Update account fields
        existing.code = account_data.code
        existing.name = account_data.name
        existing.account_type = account_data.account_type
        existing.sub_type = account_data.sub_type
        existing.tax_treatment = account_data.tax_treatment
        existing.gst_applicable = account_data.gst_applicable
        existing.description = account_data.description
        existing.parent_id = account_data.parent_id
        existing.updated_by = account_data.user_id
        
        # Save to database
        updated_account = await self.account_repository.save(existing)
        return Result.success(updated_account)
    
    async def deactivate_account(self, account_id, user_id):
        """Deactivate an account if it has no transactions"""
        # Get account
        account = await self.account_repository.get_by_id(account_id)
        if not account:
            return Result.failure(["Account not found"])
        
        # Check if account has transactions
        has_transactions = await self.account_repository.has_transactions(account_id)
        if has_transactions:
            return Result.failure(["Cannot deactivate account with transactions"])
        
        # Deactivate account
        account.is_active = False
        account.updated_by = user_id
        
        # Save to database
        updated_account = await self.account_repository.save(account)
        return Result.success(updated_account)
    
    async def get_account_tree(self):
        """Get hierarchical tree of all accounts"""
        # Get all accounts
        accounts = await self.account_repository.get_all()
        
        # Build tree structure
        tree = []
        account_map = {account.id: account for account in accounts}
        
        # Find root accounts (no parent)
        for account in accounts:
            if not account.parent_id:
                account_dict = account.to_dict()
                account_dict['children'] = []
                tree.append(account_dict)
        
        # Add child accounts
        for account in accounts:
            if account.parent_id and account.parent_id in account_map:
                parent = account_map[account.parent_id]
                # Find parent in tree
                parent_in_tree = self._find_account_in_tree(tree, parent.id)
                if parent_in_tree:
                    account_dict = account.to_dict()
                    account_dict['children'] = []
                    parent_in_tree['children'].append(account_dict)
        
        return tree
    
    def _find_account_in_tree(self, tree, account_id):
        """Helper to find an account in the tree by id"""
        for account in tree:
            if account['id'] == account_id:
                return account
            if 'children' in account:
                found = self._find_account_in_tree(account['children'], account_id)
                if found:
                    return found
        return None
```

#### 4.1.2 Journal Entry Manager

**Responsibilities**:
- Create and post journal entries
- Validate balanced transactions
- Generate recurring entries
- Reverse incorrect entries

**Key Functions**:

```python
class JournalEntryManager:
    def __init__(self, journal_repository, account_repository, fiscal_period_repository, sequence_generator):
        self.journal_repository = journal_repository
        self.account_repository = account_repository
        self.fiscal_period_repository = fiscal_period_repository
        self.sequence_generator = sequence_generator
    
    async def create_journal_entry(self, entry_data):
        """Create a new journal entry with validation"""
        # Validate balanced entry
        total_debits = sum(line.debit_amount for line in entry_data.lines)
        total_credits = sum(line.credit_amount for line in entry_data.lines)
        
        if abs(total_debits - total_credits) > 0.01:  # Allow small rounding differences
            return Result.failure(["Journal entry must be balanced"])
        
        # Get fiscal period for entry date
        fiscal_period = await self.fiscal_period_repository.get_by_date(entry_data.entry_date)
        if not fiscal_period:
            return Result.failure(["No fiscal period found for the entry date"])
        
        if fiscal_period.status == 'Closed':
            return Result.failure(["Cannot create entries in closed fiscal periods"])
        
        # Generate entry number
        entry_no = await self.sequence_generator.next_sequence("journal_entry")
        
        # Create journal entry
        journal_entry = JournalEntry(
            entry_no=entry_no,
            journal_type=entry_data.journal_type,
            entry_date=entry_data.entry_date,
            fiscal_period_id=fiscal_period.id,
            description=entry_data.description,
            reference=entry_data.reference,
            is_recurring=entry_data.is_recurring,
            recurring_pattern_id=entry_data.recurring_pattern_id,
            created_by=entry_data.user_id,
            updated_by=entry_data.user_id
        )
        
        # Create lines
        for i, line_data in enumerate(entry_data.lines, 1):
            # Validate account exists and is active
            account = await self.account_repository.get_by_id(line_data.account_id)
            if not account or not account.is_active:
                return Result.failure([f"Invalid or inactive account on line {i}"])
            
            line = JournalEntryLine(
                line_number=i,
                account_id=line_data.account_id,
                description=line_data.description,
                debit_amount=line_data.debit_amount,
                credit_amount=line_data.credit_amount,
                currency_code=line_data.currency_code,
                exchange_rate=line_data.exchange_rate,
                tax_code=line_data.tax_code,
                tax_amount=line_data.tax_amount,
                dimension1_id=line_data.dimension1_id,
                dimension2_id=line_data.dimension2_id
            )
            journal_entry.lines.append(line)
        
        # Save to database
        saved_entry = await self.journal_repository.save(journal_entry)
        return Result.success(saved_entry)
    
    async def post_journal_entry(self, entry_id, user_id):
        """Post a journal entry, making it permanent"""
        # Get journal entry
        entry = await self.journal_repository.get_by_id(entry_id)
        if not entry:
            return Result.failure(["Journal entry not found"])
        
        if entry.is_posted:
            return Result.failure(["Journal entry is already posted"])
        
        # Check fiscal period is open
        fiscal_period = await self.fiscal_period_repository.get_by_id(entry.fiscal_period_id)
        if fiscal_period.status == 'Closed':
            return Result.failure(["Cannot post to a closed fiscal period"])
        
        # Post entry
        entry.is_posted = True
        entry.updated_by = user_id
        
        # Save changes
        updated_entry = await self.journal_repository.save(entry)
        return Result.success(updated_entry)
    
    async def reverse_journal_entry(self, entry_id, reversal_date, description, user_id):
        """Create a reversing entry for an existing journal entry"""
        # Get original entry
        original = await self.journal_repository.get_by_id(entry_id)
        if not original:
            return Result.failure(["Journal entry not found"])
        
        if not original.is_posted:
            return Result.failure(["Only posted entries can be reversed"])
        
        if original.is_reversed:
            return Result.failure(["Entry is already reversed"])
        
        # Create reversal entry
        result = await self.journal_repository.reverse(
            entry_id, 
            reversal_date, 
            description or f"Reversal of {original.entry_no}"
        )
        
        if not result:
            return Result.failure(["Failed to create reversal entry"])
        
        # Mark original as reversed
        original.is_reversed = True
        original.reversing_entry_id = result.id
        original.updated_by = user_id
        
        # Save original
        await self.journal_repository.save(original)
        
        return Result.success(result)
    
    async def generate_recurring_entries(self, as_of_date):
        """Generate all recurring entries due by the given date"""
        # Get recurring patterns due for generation
        patterns = await self.journal_repository.get_recurring_patterns_due(as_of_date)
        
        results = []
        for pattern in patterns:
            # Get template entry
            template = await self.journal_repository.get_by_id(pattern.template_entry_id)
            if not template:
                continue
            
            # Create new entry from template
            new_entry_data = self._create_entry_data_from_template(template, pattern, as_of_date)
            result = await self.create_journal_entry(new_entry_data)
            
            if result.is_success:
                # Update pattern's last generated date
                pattern.last_generated_date = as_of_date
                await self.journal_repository.save_recurring_pattern(pattern)
                
                results.append(result.value)
        
        return results
    
    def _create_entry_data_from_template(self, template, pattern, as_of_date):
        """Create new entry data from a template entry"""
        # Create base entry data
        entry_data = JournalEntryData(
            journal_type=template.journal_type,
            entry_date=as_of_date,
            description=f"{template.description} (Recurring {as_of_date.strftime('%Y-%m-%d')})",
            reference=template.reference,
            is_recurring=False,
            recurring_pattern_id=None,
            user_id=pattern.created_by,
            lines=[]
        )
        
        # Copy lines
        for line in template.lines:
            line_data = JournalEntryLineData(
                account_id=line.account_id,
                description=line.description,
                debit_amount=line.debit_amount,
                credit_amount=line.credit_amount,
                currency_code=line.currency_code,
                exchange_rate=line.exchange_rate,
                tax_code=line.tax_code,
                tax_amount=line.tax_amount,
                dimension1_id=line.dimension1_id,
                dimension2_id=line.dimension2_id
            )
            entry_data.lines.append(line_data)
        
        return entry_data
```

### 4.2 Tax Management Module

#### 4.2.1 GST Manager

**Responsibilities**:
- Calculate GST on transactions
- Track input and output tax
- Generate GST returns
- Process GST adjustments

**Key Functions**:

```python
class GSTManager:
    def __init__(self, tax_repository, journal_repository, company_settings_repository):
        self.tax_repository = tax_repository
        self.journal_repository = journal_repository
        self.company_settings_repository = company_settings_repository
    
    async def calculate_gst(self, amount, tax_code, is_input):
        """Calculate GST amount based on tax code"""
        tax_code_info = await self.tax_repository.get_tax_code(tax_code)
        if not tax_code_info:
            return 0
        
        # Calculate GST
        gst_amount = round(amount * tax_code_info.rate / 100, 2)
        
        return gst_amount
    
    async def prepare_gst_return(self, start_date, end_date):
        """Prepare GST F5 return for the specified period"""
        # Get company details
        company = await self.company_settings_repository.get_company_settings()
        
        # Create return object
        gst_return = GSTReturn(
            return_period=f"{start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}",
            start_date=start_date,
            end_date=end_date,
            filing_due_date=self._calculate_filing_due_date(end_date)
        )
        
        # Get all posted journal entries for the period
        entries = await self.journal_repository.get_posted_entries_by_date_range(start_date, end_date)
        
        # Calculate totals
        standard_rated_supplies = 0
        zero_rated_supplies = 0
        exempt_supplies = 0
        taxable_purchases = 0
        output_tax = 0
        input_tax = 0
        
        for entry in entries:
            for line in entry.lines:
                account = await self.account_repository.get_by_id(line.account_id)
                tax_code_info = await self.tax_repository.get_tax_code(line.tax_code) if line.tax_code else None
                
                if not tax_code_info:
                    continue
                
                amount = line.debit_amount or line.credit_amount
                
                if tax_code_info.code == 'SR':  # Standard rated supply
                    if account.account_type == 'Revenue':
                        standard_rated_supplies += amount
                        output_tax += line.tax_amount
                elif tax_code_info.code == 'ZR':  # Zero rated supply
                    if account.account_type == 'Revenue':
                        zero_rated_supplies += amount
                elif tax_code_info.code == 'ES':  # Exempt supply
                    if account.account_type == 'Revenue':
                        exempt_supplies += amount
                elif tax_code_info.code == 'TX':  # Taxable purchase
                    if account.account_type == 'Expense' or account.account_type == 'Asset':
                        taxable_purchases += amount
                        input_tax += line.tax_amount
        
        # Update return values
        gst_return.standard_rated_supplies = standard_rated_supplies
        gst_return.zero_rated_supplies = zero_rated_supplies
        gst_return.exempt_supplies = exempt_supplies
        gst_return.total_supplies = standard_rated_supplies + zero_rated_supplies + exempt_supplies
        gst_return.taxable_purchases = taxable_purchases
        gst_return.output_tax = output_tax
        gst_return.input_tax = input_tax
        gst_return.tax_payable = output_tax - input_tax
        
        # Save draft return
        saved_return = await self.tax_repository.save_gst_return(gst_return)
        
        return saved_return
    
    def _calculate_filing_due_date(self, period_end_date):
        """Calculate GST filing due date (1 month after period end)"""
        due_date = period_end_date.replace(day=1)
        due_date = due_date + relativedelta(months=2, days=-1)
        return due_date
    
    async def finalize_gst_return(self, return_id, submission_reference, submission_date, user_id):
        """Finalize a GST return after submission to IRAS"""
        # Get GST return
        gst_return = await self.tax_repository.get_gst_return(return_id)
        if not gst_return:
            return Result.failure(["GST return not found"])
        
        if gst_return.status == 'Submitted':
            return Result.failure(["GST return is already submitted"])
        
        # Update return status
        gst_return.status = 'Submitted'
        gst_return.submission_reference = submission_reference
        gst_return.submission_date = submission_date
        
        # Save changes
        updated_return = await self.tax_repository.save_gst_return(gst_return)
        
        # Create journal entry for GST payment/refund if needed
        if abs(gst_return.tax_payable) > 0:
            await self._create_gst_payment_entry(gst_return, user_id)
        
        return Result.success(updated_return)
    
    async def _create_gst_payment_entry(self, gst_return, user_id):
        """Create journal entry for GST payment or refund"""
        # Get accounts
        gst_payable_account = await self.account_repository.get_by_code("GST-PAYABLE")
        gst_receivable_account = await self.account_repository.get_by_code("GST-RECEIVABLE")
        bank_account = await self.account_repository.get_by_code("BANK-MAIN")
        
        # Create entry data
        entry_data = JournalEntryData(
            journal_type="General",
            entry_date=gst_return.submission_date,
            description=f"GST payment for period {gst_return.return_period}",
            reference=gst_return.submission_reference,
            is_recurring=False,
            user_id=user_id,
            lines=[]
        )
        
        if gst_return.tax_payable > 0:
            # GST payment
            entry_data.lines.append(JournalEntryLineData(
                account_id=gst_payable_account.id,
                description=f"GST payment for {gst_return.return_period}",
                debit_amount=gst_return.tax_payable,
                credit_amount=0
            ))
            
            entry_data.lines.append(JournalEntryLineData(
                account_id=bank_account.id,
                description=f"GST payment for {gst_return.return_period}",
                debit_amount=0,
                credit_amount=gst_return.tax_payable
            ))
        else:
            # GST refund
            refund_amount = abs(gst_return.tax_payable)
            
            entry_data.lines.append(JournalEntryLineData(
                account_id=bank_account.id,
                description=f"GST refund for {gst_return.return_period}",
                debit_amount=refund_amount,
                credit_amount=0
            ))
            
            entry_data.lines.append(JournalEntryLineData(
                account_id=gst_receivable_account.id,
                description=f"GST refund for {gst_return.return_period}",
                debit_amount=0,
                credit_amount=refund_amount
            ))
        
        # Create and post journal entry
        journal_manager = JournalEntryManager(
            self.journal_repository,
            self.account_repository,
            self.fiscal_period_repository,
            self.sequence_generator
        )
        
        result = await journal_manager.create_journal_entry(entry_data)
        if result.is_success:
            await journal_manager.post_journal_entry(result.value.id, user_id)
        
        return result
```

### 4.3 Financial Reporting Module

#### 4.3.1 Financial Statement Generator

**Responsibilities**:
- Generate financial statements
- Calculate account balances for periods
- Format reports according to SFRS
- Support comparative reporting

**Key Functions**:

```python
class FinancialStatementGenerator:
    def __init__(self, account_repository, journal_repository, fiscal_period_repository):
        self.account_repository = account_repository
        self.journal_repository = journal_repository
        self.fiscal_period_repository = fiscal_period_repository
    
    async def generate_balance_sheet(self, as_of_date, comparative_date=None, include_zero_balances=False):
        """Generate a balance sheet as of a specific date"""
        # Get all accounts
        accounts = await self.account_repository.get_all_active()
        
        # Group accounts by type
        assets = [a for a in accounts if a.account_type == 'Asset']
        liabilities = [a for a in accounts if a.account_type == 'Liability']
        equity = [a for a in accounts if a.account_type == 'Equity']
        
        # Calculate balances
        asset_accounts = await self._calculate_account_balances(assets, as_of_date)
        liability_accounts = await self._calculate_account_balances(liabilities, as_of_date)
        equity_accounts = await self._calculate_account_balances(equity, as_of_date)
        
        # Calculate comparative balances if requested
        comparative_asset_accounts = None
        comparative_liability_accounts = None
        comparative_equity_accounts = None
        
        if comparative_date:
            comparative_asset_accounts = await self._calculate_account_balances(assets, comparative_date)
            comparative_liability_accounts = await self._calculate_account_balances(liabilities, comparative_date)
            comparative_equity_accounts = await self._calculate_account_balances(equity, comparative_date)
        
        # Filter zero balances if requested
        if not include_zero_balances:
            asset_accounts = [a for a in asset_accounts if a['balance'] != 0]
            liability_accounts = [a for a in liability_accounts if a['balance'] != 0]
            equity_accounts = [a for a in equity_accounts if a['balance'] != 0]
            
            if comparative_date:
                comparative_asset_accounts = [a for a in comparative_asset_accounts if a['balance'] != 0]
                comparative_liability_accounts = [a for a in comparative_liability_accounts if a['balance'] != 0]
                comparative_equity_accounts = [a for a in comparative_equity_accounts if a['balance'] != 0]
        
        # Calculate totals
        total_assets = sum(a['balance'] for a in asset_accounts)
        total_liabilities = sum(a['balance'] for a in liability_accounts)
        total_equity = sum(a['balance'] for a in equity_accounts)
        
        comparative_total_assets = None
        comparative_total_liabilities = None
        comparative_total_equity = None
        
        if comparative_date:
            comparative_total_assets = sum(a['balance'] for a in comparative_asset_accounts)
            comparative_total_liabilities = sum(a['balance'] for a in comparative_liability_accounts)
            comparative_total_equity = sum(a['balance'] for a in comparative_equity_accounts)
        
        # Construct report data
        report_data = {
            'as_of_date': as_of_date,
            'comparative_date': comparative_date,
            'assets': {
                'accounts': asset_accounts,
                'total': total_assets,
                'comparative_accounts': comparative_asset_accounts,
                'comparative_total': comparative_total_assets
            },
            'liabilities': {
                'accounts': liability_accounts,
                'total': total_liabilities,
                'comparative_accounts': comparative_liability_accounts,
                'comparative_total': comparative_total_liabilities
            },
            'equity': {
                'accounts': equity_accounts,
                'total': total_equity,
                'comparative_accounts': comparative_equity_accounts,
                'comparative_total': comparative_total_equity
            },
            'total_liabilities_equity': total_liabilities + total_equity,
            'comparative_total_liabilities_equity': 
                (comparative_total_liabilities + comparative_total_equity) if comparative_date else None
        }
        
        return report_data
    
    async def generate_profit_loss(self, start_date, end_date, comparative_start=None, comparative_end=None):
        """Generate a profit and loss statement for a period"""
        # Get all accounts
        accounts = await self.account_repository.get_all_active()
        
        # Group accounts by type
        revenues = [a for a in accounts if a.account_type == 'Revenue']
        expenses = [a for a in accounts if a.account_type == 'Expense']
        
        # Calculate balances for current period
        revenue_accounts = await self._calculate_account_balances_for_period(
            revenues, start_date, end_date
        )
        expense_accounts = await self._calculate_account_balances_for_period(
            expenses, start_date, end_date
        )
        
        # Calculate comparative balances if requested
        comparative_revenue_accounts = None
        comparative_expense_accounts = None
        
        if comparative_start and comparative_end:
            comparative_revenue_accounts = await self._calculate_account_balances_for_period(
                revenues, comparative_start, comparative_end
            )
            comparative_expense_accounts = await self._calculate_account_balances_for_period(
                expenses, comparative_start, comparative_end
            )
        
        # Calculate totals
        total_revenue = sum(a['balance'] for a in revenue_accounts)
        total_expenses = sum(a['balance'] for a in expense_accounts)
        net_profit = total_revenue - total_expenses
        
        comparative_total_revenue = None
        comparative_total_expenses = None
        comparative_net_profit = None
        
        if comparative_start and comparative_end:
            comparative_total_revenue = sum(a['balance'] for a in comparative_revenue_accounts)
            comparative_total_expenses = sum(a['balance'] for a in comparative_expense_accounts)
            comparative_net_profit = comparative_total_revenue - comparative_total_expenses
        
        # Construct report data
        report_data = {
            'start_date': start_date,
            'end_date': end_date,
            'comparative_start': comparative_start,
            'comparative_end': comparative_end,
            'revenue': {
                'accounts': revenue_accounts,
                'total': total_revenue,
                'comparative_accounts': comparative_revenue_accounts,
                'comparative_total': comparative_total_revenue
            },
            'expenses': {
                'accounts': expense_accounts,
                'total': total_expenses,
                'comparative_accounts': comparative_expense_accounts,
                'comparative_total': comparative_total_expenses
            },
            'net_profit': net_profit,
            'comparative_net_profit': comparative_net_profit
        }
        
        return report_data
    
    async def _calculate_account_balances(self, accounts, as_of_date):
        """Calculate account balances as of a specific date"""
        result = []
        
        for account in accounts:
            # Get all journal entries for this account up to as_of_date
            balance = await self.journal_repository.get_account_balance(account.id, as_of_date)
            
            # Determine sign based on account type
            if account.account_type in ['Asset', 'Expense']:
                # Debit balance accounts
                account_balance = balance
            else:
                # Credit balance accounts
                account_balance = -balance
            
            result.append({
                'id': account.id,
                'code': account.code,
                'name': account.name,
                'balance': account_balance
            })
        
        return result
    
    async def _calculate_account_balances_for_period(self, accounts, start_date, end_date):
        """Calculate account balances for a specific period"""
        result = []
        
        for account in accounts:
            # Get journal entries for this account in the period
            balance = await self.journal_repository.get_account_balance_for_period(
                account.id, start_date, end_date
            )
            
            # Determine sign based on account type
            if account.account_type in ['Asset', 'Expense']:
                # Debit balance accounts
                account_balance = balance
            else:
                # Credit balance accounts
                account_balance = -balance
            
            result.append({
                'id': account.id,
                'code': account.code,
                'name': account.name,
                'balance': account_balance
            })
        
        return result
```

## 5. User Interface Implementation

### 5.1 Main Application Structure

```python
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QSplashScreen
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QPixmap

from app.ui.main_window import MainWindow
from app.core.application_core import ApplicationCore
from app.core.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager

class Application(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        
        # Set application information
        self.setApplicationName("SG Bookkeeper")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("My Company")
        self.setOrganizationDomain("mycompany.com")
        
        # Show splash screen
        splash_pixmap = QPixmap(":/images/splash.png")
        self.splash = QSplashScreen(splash_pixmap, Qt.WindowStaysOnTopHint)
        self.splash.show()
        self.processEvents()
        
        # Initialize config
        self.config_manager = ConfigManager()
        self.splash.showMessage("Loading configuration...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        self.processEvents()
        
        # Initialize database
        self.splash.showMessage("Connecting to database...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        self.processEvents()
        self.db_manager = DatabaseManager(self.config_manager)
        
        # Initialize application core
        self.splash.showMessage("Initializing application...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        self.processEvents()
        self.app_core = ApplicationCore(self.config_manager, self.db_manager)
        
        # Create main window
        self.splash.showMessage("Loading interface...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        self.processEvents()
        self.main_window = MainWindow(self.app_core)
        
        # Show main window and close splash
        self.main_window.show()
        self.splash.finish(self.main_window)
    
    def shutdown(self):
        """Clean shutdown of application"""
        # Close database connections
        self.db_manager.close_connections()
        
        # Save application state
        settings = QSettings()
        settings.setValue("MainWindow/geometry", self.main_window.saveGeometry())
        settings.setValue("MainWindow/state", self.main_window.saveState())
        settings.sync()

def main():
    # Create application
    app = Application(sys.argv)
    
    # Handle application exit
    app.aboutToQuit.connect(app.shutdown)
    
    # Run application
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
```

### 5.2 Main Window Implementation

```python
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QStatusBar, 
    QVBoxLayout, QWidget, QAction, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, QSettings, Signal, Slot
from PySide6.QtGui import QIcon, QKeySequence

from app.ui.dashboard.dashboard_widget import DashboardWidget
from app.ui.accounting.accounting_widget import AccountingWidget
from app.ui.customers.customers_widget import CustomersWidget
from app.ui.vendors.vendors_widget import VendorsWidget
from app.ui.banking.banking_widget import BankingWidget
from app.ui.reports.reports_widget import ReportsWidget
from app.ui.settings.settings_widget import SettingsWidget

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, app_core):
        super().__init__()
        self.app_core = app_core
        
        # Set window properties
        self.setWindowTitle("SG Bookkeeper")
        self.setMinimumSize(1024, 768)
        
        # Restore window geometry
        settings = QSettings()
        if settings.contains("MainWindow/geometry"):
            self.restoreGeometry(settings.value("MainWindow/geometry"))
        else:
            # Default size if no saved state
            self.resize(1280, 800)
        
        # Initialize UI components
        self._init_ui()
        
        # Restore window state
        if settings.contains("MainWindow/state"):
            self.restoreState(settings.value("MainWindow/state"))
    
    def _init_ui(self):
        """Initialize UI components"""
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create toolbar
        self._create_toolbar()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(True)
        self.main_layout.addWidget(self.tab_widget)
        
        # Add module tabs
        self._add_module_tabs()
        
        # Create status bar
        self._create_status_bar()
        
        # Create actions
        self._create_actions()
        
        # Create menus
        self._create_menus()
    
    def _create_toolbar(self):
        """Create main toolbar"""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(Qt.QSize(32, 32))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
    
    def _add_module_tabs(self):
        """Add module tabs to the tab widget"""
        # Dashboard tab
        self.dashboard_widget = DashboardWidget(self.app_core)
        self.tab_widget.addTab(self.dashboard_widget, QIcon(":/icons/dashboard.svg"), "Dashboard")
        
        # Accounting tab
        self.accounting_widget = AccountingWidget(self.app_core)
        self.tab_widget.addTab(self.accounting_widget, QIcon(":/icons/accounting.svg"), "Accounting")
        
        # Customers tab
        self.customers_widget = CustomersWidget(self.app_core)
        self.tab_widget.addTab(self.customers_widget, QIcon(":/icons/customers.svg"), "Customers")
        
        # Vendors tab
        self.vendors_widget = VendorsWidget(self.app_core)
        self.tab_widget.addTab(self.vendors_widget, QIcon(":/icons/vendors.svg"), "Vendors")
        
        # Banking tab
        self.banking_widget = BankingWidget(self.app_core)
        self.tab_widget.addTab(self.banking_widget, QIcon(":/icons/banking.svg"), "Banking")
        
        # Reports tab
        self.reports_widget = ReportsWidget(self.app_core)
        self.tab_widget.addTab(self.reports_widget, QIcon(":/icons/reports.svg"), "Reports")
        
        # Settings tab
        self.settings_widget = SettingsWidget(self.app_core)
        self.tab_widget.addTab(self.settings_widget, QIcon(":/icons/settings.svg"), "Settings")
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add status labels
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label, 1)
        
        self.user_label = QLabel(f"User: {self.app_core.current_user.username}")
        self.status_bar.addPermanentWidget(self.user_label)
        
        self.version_label = QLabel(f"Version: {QApplication.applicationVersion()}")
        self.status_bar.addPermanentWidget(self.version_label)
    
    def _create_actions(self):
        """Create application actions"""
        # File actions
        self.new_company_action = QAction(QIcon(":/icons/new_company.svg"), "New Company", self)
        self.new_company_action.setShortcut(QKeySequence.New)
        self.new_company_action.triggered.connect(self.on_new_company)
        
        self.open_company_action = QAction(QIcon(":/icons/open_company.svg"), "Open Company", self)
        self.open_company_action.setShortcut(QKeySequence.Open)
        self.open_company_action.triggered.connect(self.on_open_company)
        
        self.backup_action = QAction(QIcon(":/icons/backup.svg"), "Backup Data", self)
        self.backup_action.triggered.connect(self.on_backup)
        
        self.restore_action = QAction(QIcon(":/icons/restore.svg"), "Restore Data", self)
        self.restore_action.triggered.connect(self.on_restore)
        
        self.exit_action = QAction(QIcon(":/icons/exit.svg"), "Exit", self)
        self.exit_action.setShortcut(QKeySequence.Quit)
        self.exit_action.triggered.connect(self.close)
        
        # Edit actions
        self.preferences_action = QAction(QIcon(":/icons/preferences.svg"), "Preferences", self)
        self.preferences_action.triggered.connect(self.on_preferences)
        
        # Help actions
        self.help_contents_action = QAction(QIcon(":/icons/help.svg"), "Help Contents", self)
        self.help_contents_action.setShortcut(QKeySequence.HelpContents)
        self.help_contents_action.triggered.connect(self.on_help_contents)
        
        self.about_action = QAction(QIcon(":/icons/about.svg"), "About", self)
        self.about_action.triggered.connect(self.on_about)
    
    def _create_menus(self):
        """Create application menus"""
        # File menu
        self.file_menu = self.menuBar().addMenu("&File")
        self.file_menu.addAction(self.new_company_action)
        self.file_menu.addAction(self.open_company_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.backup_action)
        self.file_menu.addAction(self.restore_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)
        
        # Edit menu
        self.edit_menu = self.menuBar().addMenu("&Edit")
        self.edit_menu.addAction(self.preferences_action)
        
        # View menu
        self.view_menu = self.menuBar().addMenu("&View")
        
        # Tools menu
        self.tools_menu = self.menuBar().addMenu("&Tools")
        
        # Help menu
        self.help_menu = self.menuBar().addMenu("&Help")
        self.help_menu.addAction(self.help_contents_action)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.about_action)
        
        # Add actions to toolbar
        self.toolbar.addAction(self.new_company_action)
        self.toolbar.addAction(self.open_company_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.backup_action)
    
    @Slot()
    def on_new_company(self):
        """Handle new company action"""
        # TODO: Implement new company wizard
        QMessageBox.information(self, "New Company", "New company wizard not yet implemented")
    
    @Slot()
    def on_open_company(self):
        """Handle open company action"""
        # TODO: Implement open company dialog
        QMessageBox.information(self, "Open Company", "Open company dialog not yet implemented")
    
    @Slot()
    def on_backup(self):
        """Handle backup action"""
        # TODO: Implement backup functionality
        QMessageBox.information(self, "Backup Data", "Backup functionality not yet implemented")
    
    @Slot()
    def on_restore(self):
        """Handle restore action"""
        # TODO: Implement restore functionality
        QMessageBox.information(self, "Restore Data", "Restore functionality not yet implemented")
    
    @Slot()
    def on_preferences(self):
        """Handle preferences action"""
        # TODO: Implement preferences dialog
        QMessageBox.information(self, "Preferences", "Preferences dialog not yet implemented")
    
    @Slot()
    def on_help_contents(self):
        """Handle help contents action"""
        # TODO: Implement help system
        QMessageBox.information(self, "Help", "Help system not yet implemented")
    
    @Slot()
    def on_about(self):
        """Handle about action"""
        QMessageBox.about(
            self,
            "About SG Bookkeeper",
            "SG Bookkeeper 1.0.0\n\n"
            "A comprehensive bookkeeping application for Singapore small businesses.\n\n"
            "© 2023 My Company"
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Ask for confirmation before closing
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit the application?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
```

### 5.3 Chart of Accounts Screen

```python
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QHeaderView,
    QPushButton, QToolBar, QAction, QMenu, QDialog, QMessageBox
)
from PySide6.QtCore import Qt, QModelIndex, Signal, Slot, QSortFilterProxyModel
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem

from app.ui.accounting.account_dialog import AccountDialog
from app.models.account import Account

class ChartOfAccountsWidget(QWidget):
    """Widget for managing chart of accounts"""
    
    account_selected = Signal(int)  # Signal emitted when account is selected
    
    def __init__(self, app_core, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        
        # Initialize UI
        self._init_ui()
        
        # Load accounts
        self._load_accounts()
    
    def _init_ui(self):
        """Initialize UI components"""
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create toolbar
        self._create_toolbar()
        
        # Create tree view for accounts
        self.account_tree = QTreeView()
        self.account_tree.setAlternatingRowColors(True)
        self.account_tree.setUniformRowHeights(True)
        self.account_tree.setEditTriggers(QTreeView.NoEditTriggers)
        self.account_tree.setSelectionBehavior(QTreeView.SelectRows)
        self.account_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.account_tree.customContextMenuRequested.connect(self.on_context_menu)
        self.account_tree.doubleClicked.connect(self.on_account_double_clicked)
        
        # Create model for account tree
        self.account_model = QStandardItemModel()
        self.account_model.setHorizontalHeaderLabels(["Code", "Name", "Type", "Balance"])
        
        # Create proxy model for sorting and filtering
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.account_model)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        
        # Set model for tree view
        self.account_tree.setModel(self.proxy_model)
        
        # Set column widths
        self.account_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.account_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.account_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.account_tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        # Add tree view to layout
        self.main_layout.addWidget(self.account_tree)
        
        # Create button layout
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 10, 0, 0)
        
        # Create buttons
        self.add_button = QPushButton("Add Account")
        self.add_button.clicked.connect(self.on_add_account)
        self.button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Edit Account")
        self.edit_button.clicked.connect(self.on_edit_account)
        self.button_layout.addWidget(self.edit_button)
        
        self.deactivate_button = QPushButton("Deactivate Account")
        self.deactivate_button.clicked.connect(self.on_deactivate_account)
        self.button_layout.addWidget(self.deactivate_button)
        
        # Add button layout to main layout
        self.main_layout.addLayout(self.button_layout)
    
    def _create_toolbar(self):
        """Create toolbar for chart of accounts"""
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(Qt.QSize(16, 16))
        
        # Create filter action
        self.filter_action = QAction(QIcon(":/icons/filter.svg"), "Filter", self)
        self.filter_action.setCheckable(True)
        self.filter_action.toggled.connect(self.on_filter_toggled)
        self.toolbar.addAction(self.filter_action)
        
        # Create expand all action
        self.expand_all_action = QAction(QIcon(":/icons/expand_all.svg"), "Expand All", self)
        self.expand_all_action.triggered.connect(self.account_tree.expandAll)
        self.toolbar.addAction(self.expand_all_action)
        
        # Create collapse all action
        self.collapse_all_action = QAction(QIcon(":/icons/collapse_all.svg"), "Collapse All", self)
        self.collapse_all_action.triggered.connect(self.account_tree.collapseAll)
        self.toolbar.addAction(self.collapse_all_action)
        
        # Create refresh action
        self.refresh_action = QAction(QIcon(":/icons/refresh.svg"), "Refresh", self)
        self.refresh_action.triggered.connect(self._load_accounts)
        self.toolbar.addAction(self.refresh_action)
        
        # Add toolbar to layout
        self.main_layout.addWidget(self.toolbar)
    
    async def _load_accounts(self):
        """Load accounts from database and populate tree view"""
        try:
            # Clear model
            self.account_model.clear()
            self.account_model.setHorizontalHeaderLabels(["Code", "Name", "Type", "Balance"])
            
            # Get account tree from service
            account_tree = await self.app_core.accounting_service.get_account_tree()
            
            # Add root items
            for account_type in ['Asset', 'Liability', 'Equity', 'Revenue', 'Expense']:
                type_item = QStandardItem(account_type)
                type_item.setData(None, Qt.UserRole)  # No account ID for type headers
                
                # Find accounts of this type
                type_accounts = [a for a in account_tree if a['account_type'] == account_type and not a['parent_id']]
                
                # Add accounts to type item
                for account in type_accounts:
                    self._add_account_to_tree(account, type_item)
                
                # Add type item to model
                self.account_model.appendRow(type_item)
            
            # Expand to level 1
            self.account_tree.expandToDepth(1)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load accounts: {str(e)}")
    
    def _add_account_to_tree(self, account, parent_item):
        """Add account and its children to tree recursively"""
        # Create items for each column
        code_item = QStandardItem(account['code'])
        code_item.setData(account['id'], Qt.UserRole)
        
        name_item = QStandardItem(account['name'])
        type_item = QStandardItem(account['sub_type'] or account['account_type'])
        
        # Format balance based on account type
        balance = account.get('balance', 0)
        balance_text = f"{balance:,.2f}"
        balance_item = QStandardItem(balance_text)
        balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Add account to parent
        row = [code_item, name_item, type_item, balance_item]
        parent_item.appendRow(row)
        
        # Add children recursively
        if 'children' in account and account['children']:
            for child in account['children']:
                self._add_account_to_tree(child, code_item)
    
    @Slot()
    def on_add_account(self):
        """Handle add account button click"""
        dialog = AccountDialog(self.app_core, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._load_accounts()
    
    @Slot()
    def on_edit_account(self):
        """Handle edit account button click"""
        # Get selected account
        index = self.account_tree.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Warning", "Please select an account to edit")
            return
        
        # Get account ID
        account_id = self.proxy_model.data(index.siblingAtColumn(0), Qt.UserRole)
        if not account_id:
            QMessageBox.warning(self, "Warning", "Cannot edit account type headers")
            return
        
        # Open edit dialog
        dialog = AccountDialog(self.app_core, account_id=account_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._load_accounts()
    
    @Slot()
    def on_deactivate_account(self):
        """Handle deactivate account button click"""
        # Get selected account
        index = self.account_tree.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Warning", "Please select an account to deactivate")
            return
        
        # Get account ID
        account_id = self.proxy_model.data(index.siblingAtColumn(0), Qt.UserRole)
        if not account_id:
            QMessageBox.warning(self, "Warning", "Cannot deactivate account type headers")
            return
        
        # Confirm deactivation
        reply = QMessageBox.question(
            self,
            "Confirm Deactivation",
            "Are you sure you want to deactivate this account?\n"
            "Deactivated accounts will not appear in dropdown lists for new transactions.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Deactivate account
                result = await self.app_core.accounting_service.deactivate_account(
                    account_id, self.app_core.current_user.id
                )
                
                if result.is_success:
                    QMessageBox.information(self, "Success", "Account deactivated successfully")
                    self._load_accounts()
                else:
                    QMessageBox.warning(self, "Warning", "\n".join(result.errors))
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to deactivate account: {str(e)}")
    
    @Slot(QModelIndex)
    def on_account_double_clicked(self, index):
        """Handle double click on account"""
        # Get account ID
        account_id = self.proxy_model.data(index.siblingAtColumn(0), Qt.UserRole)
        if account_id:
            # Emit signal with account ID
            self.account_selected.emit(account_id)
    
    @Slot(bool)
    def on_filter_toggled(self, checked):
        """Handle filter toggle"""
        if checked:
            # TODO: Show filter dialog
            pass
        else:
            # Clear filter
            self.proxy_model.setFilterFixedString("")
    
    @Slot(QPoint)
    def on_context_menu(self, pos):
        """Handle context menu request"""
        # Get index at position
        index = self.account_tree.indexAt(pos)
        if not index.isValid():
            return
        
        # Get account ID
        account_id = self.proxy_model.data(index.siblingAtColumn(0), Qt.UserRole)
        if not account_id:
            return
        
        # Create context menu
        context_menu = QMenu(self)
        
        # Add actions
        edit_action = QAction(QIcon(":/icons/edit.svg"), "Edit Account", self)
        edit_action.triggered.connect(self.on_edit_account)
        context_menu.addAction(edit_action)
        
        view_transactions_action = QAction(QIcon(":/icons/transactions.svg"), "View Transactions", self)
        view_transactions_action.triggered.connect(lambda: self.on_view_transactions(account_id))
        context_menu.addAction(view_transactions_action)
        
        deactivate_action = QAction(QIcon(":/icons/deactivate.svg"), "Deactivate Account", self)
        deactivate_action.triggered.connect(self.on_deactivate_account)
        context_menu.addAction(deactivate_action)
        
        # Show context menu
        context_menu.exec_(self.account_tree.viewport().mapToGlobal(pos))
    
    @Slot(int)
    def on_view_transactions(self, account_id):
        """Handle view transactions action"""
        # TODO: Open transactions view filtered by account
        QMessageBox.information(self, "View Transactions", f"View transactions for account ID {account_id}")
```

## 6. Business Logic Implementation

### 6.1 Tax Calculation Logic

```python
class TaxCalculator:
    """Tax calculation engine for Singapore taxes"""
    
    def __init__(self, tax_repository):
        self.tax_repository = tax_repository
    
    async def calculate_transaction_taxes(self, transaction_data):
        """Calculate taxes for all lines in a transaction"""
        results = []
        
        for line in transaction_data.lines:
            tax_result = await self.calculate_line_tax(
                line.amount,
                line.tax_code,
                transaction_data.transaction_type,
                line.account_id
            )
            
            results.append({
                'line_index': line.index,
                'tax_amount': tax_result.tax_amount,
                'tax_account_id': tax_result.tax_account_id,
                'taxable_amount': tax_result.taxable_amount
            })
        
        return results
    
    async def calculate_line_tax(self, amount, tax_code, transaction_type, account_id=None):
        """Calculate tax for a single line item"""
        # Default result
        result = TaxCalculationResult(
            tax_amount=0,
            tax_account_id=None,
            taxable_amount=amount
        )
        
        # Skip if no tax code or zero amount
        if not tax_code or abs(amount) < 0.01:
            return result
        
        # Get tax code details
        tax_code_info = await self.tax_repository.get_tax_code(tax_code)
        if not tax_code_info:
            return result
        
        # Handle GST
        if tax_code_info.tax_type == 'GST':
            return await self._calculate_gst(amount, tax_code_info, transaction_type)
        
        # Handle Withholding Tax
        elif tax_code_info.tax_type == 'Withholding Tax':
            return await self._calculate_withholding_tax(amount, tax_code_info, transaction_type)
        
        # Handle Income Tax (usually just marking, no calculation)
        elif tax_code_info.tax_type == 'Income Tax':
            return result
        
        return result
    
    async def _calculate_gst(self, amount, tax_code_info, transaction_type):
        """Calculate GST tax amount"""
        # Determine if amount is inclusive or exclusive of GST
        is_tax_inclusive = transaction_type in ['Sales Invoice', 'Sales Receipt', 'Purchase Invoice', 'Purchase Payment']
        
        tax_account_id = tax_code_info.affects_account_id
        
        if is_tax_inclusive:
            # Calculate tax from inclusive amount
            gross_amount = amount
            net_amount = amount / (1 + tax_code_info.rate / 100)
            tax_amount = gross_amount - net_amount
        else:
            # Calculate tax from exclusive amount
            net_amount = amount
            tax_amount = amount * tax_code_info.rate / 100
            gross_amount = net_amount + tax_amount
        
        # Round to 2 decimal places
        tax_amount = round(tax_amount, 2)
        
        return TaxCalculationResult(
            tax_amount=tax_amount,
            tax_account_id=tax_account_id,
            taxable_amount=net_amount
        )
    
    async def _calculate_withholding_tax(self, amount, tax_code_info, transaction_type):
        """Calculate withholding tax amount"""
        # Withholding tax only applies to specific payment types
        if transaction_type not in ['Purchase Payment', 'Expense']:
            return TaxCalculationResult(
                tax_amount=0,
                tax_account_id=None,
                taxable_amount=amount
            )
        
        # Calculate withholding tax
        tax_amount = amount * tax_code_info.rate / 100
        
        # Round to 2 decimal places
        tax_amount = round(tax_amount, 2)
        
        return TaxCalculationResult(
            tax_amount=tax_amount,
            tax_account_id=tax_code_info.affects_account_id,
            taxable_amount=amount
        )
```

### 6.2 Financial Reporting Logic

```python
class FinancialReportGenerator:
    """Financial report generation logic"""
    
    def __init__(self, journal_repository, account_repository, fiscal_period_repository):
        self.journal_repository = journal_repository
        self.account_repository = account_repository
        self.fiscal_period_repository = fiscal_period_repository
    
    async def generate_trial_balance(self, as_of_date):
        """Generate trial balance as of a specific date"""
        # Get all active accounts
        accounts = await self.account_repository.get_all_active()
        
        # Initialize results
        debit_accounts = []
        credit_accounts = []
        total_debits = 0
        total_credits = 0
        
        # Calculate balance for each account
        for account in accounts:
            balance = await self.journal_repository.get_account_balance(account.id, as_of_date)
            
            if abs(balance) < 0.01:
                continue  # Skip accounts with zero balance
            
            account_data = {
                'id': account.id,
                'code': account.code,
                'name': account.name,
                'balance': abs(balance)
            }
            
            # Determine if account has debit or credit balance
            if account.account_type in ['Asset', 'Expense']:
                # Debit balance accounts
                if balance > 0:
                    debit_accounts.append(account_data)
                    total_debits += balance
                else:
                    credit_accounts.append(account_data)
                    total_credits += abs(balance)
            else:
                # Credit balance accounts
                if balance < 0:
                    credit_accounts.append(account_data)
                    total_credits += abs(balance)
                else:
                    debit_accounts.append(account_data)
                    total_debits += balance
        
        # Sort accounts by code
        debit_accounts.sort(key=lambda a: a['code'])
        credit_accounts.sort(key=lambda a: a['code'])
        
        # Create report data
        report_data = {
            'as_of_date': as_of_date,
            'debit_accounts': debit_accounts,
            'credit_accounts': credit_accounts,
            'total_debits': total_debits,
            'total_credits': total_credits,
            'is_balanced': abs(total_debits - total_credits) < 0.01
        }
        
        return report_data
    
    async def generate_income_tax_computation(self, year):
        """Generate income tax computation for a specific year"""
        # Get fiscal year dates
        fiscal_year = await self.fiscal_period_repository.get_fiscal_year(year)
        if not fiscal_year:
            raise ValueError(f"Fiscal year {year} not found")
        
        # Get profit and loss data
        pl_data = await self.generate_profit_loss(fiscal_year.start_date, fiscal_year.end_date)
        
        # Calculate base income
        net_profit = pl_data['net_profit']
        
        # Initialize adjustments
        adjustments = []
        tax_effect = 0
        
        # Get tax adjustment accounts
        tax_accounts = await self.account_repository.get_by_tax_treatment('Tax Adjustment')
        
        # Calculate adjustments
        for account in tax_accounts:
            balance = await self.journal_repository.get_account_balance_for_period(
                account.id, fiscal_year.start_date, fiscal_year.end_date
            )
            
            if abs(balance) < 0.01:
                continue  # Skip accounts with zero balance
            
            adjustment = {
                'id': account.id,
                'code': account.code,
                'name': account.name,
                'amount': balance,
                'is_addition': balance > 0
            }
            
            adjustments.append(adjustment)
            tax_effect += balance
        
        # Calculate taxable income
        taxable_income = net_profit + tax_effect
        
        # Create report data
        report_data = {
            'year': year,
            'fiscal_year_start': fiscal_year.start_date,
            'fiscal_year_end': fiscal_year.end_date,
            'net_profit': net_profit,
            'adjustments': adjustments,
            'tax_effect': tax_effect,
            'taxable_income': taxable_income
        }
        
        return report_data
    
    async def generate_gst_f5(self, start_date, end_date):
        """Generate GST F5 form data for a specific period"""
        # Get company settings
        company = await self.company_settings_repository.get_company_settings()
        
        # Initialize report data
        report_data = {
            'company_name': company.company_name,
            'gst_registration_no': company.gst_registration_no,
            'period_start': start_date,
            'period_end': end_date,
            'standard_rated_supplies': 0,
            'zero_rated_supplies': 0,
            'exempt_supplies': 0,
            'total_supplies': 0,
            'taxable_purchases': 0,
            'output_tax': 0,
            'input_tax': 0,
            'tax_payable': 0
        }
        
        # Get all posted journal entries for the period
        entries = await self.journal_repository.get_posted_entries_by_date_range(start_date, end_date)
        
        # Process entries
        for entry in entries:
            for line in entry.lines:
                if not line.tax_code:
                    continue
                
                # Get tax code info
                tax_code_info = await self.tax_repository.get_tax_code(line.tax_code)
                if not tax_code_info or tax_code_info.tax_type != 'GST':
                    continue
                
                # Get account info
                account = await self.account_repository.get_by_id(line.account_id)
                
                # Determine amount
                amount = line.debit_amount or line.credit_amount
                
                # Update report data based on tax code and account type
                if tax_code_info.code == 'SR':  # Standard rated supply
                    if account.account_type == 'Revenue':
                        report_data['standard_rated_supplies'] += amount
                        report_data['output_tax'] += line.tax_amount
                
                elif tax_code_info.code == 'ZR':  # Zero rated supply
                    if account.account_type == 'Revenue':
                        report_data['zero_rated_supplies'] += amount
                
                elif tax_code_info.code == 'ES':  # Exempt supply
                    if account.account_type == 'Revenue':
                        report_data['exempt_supplies'] += amount
                
                elif tax_code_info.code == 'TX':  # Taxable purchase
                    if account.account_type in ['Expense', 'Asset']:
                        report_data['taxable_purchases'] += amount
                        report_data['input_tax'] += line.tax_amount
        
        # Calculate totals
        report_data['total_supplies'] = (
            report_data['standard_rated_supplies'] + 
            report_data['zero_rated_supplies'] + 
            report_data['exempt_supplies']
        )
        
        report_data['tax_payable'] = report_data['output_tax'] - report_data['input_tax']
        
        return report_data
```

## 7. Database Access Implementation

### 7.1 Database Manager

```python
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

class DatabaseManager:
    """Manages database connections and transactions"""
    
    def __init__(self, config_manager):
        self.config = config_manager.get_database_config()
        self.engine = None
        self.session_factory = None
        self.pool = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database connections"""
        # Create SQLAlchemy engine
        connection_string = (
            f"postgresql+asyncpg://{self.config.username}:{self.config.password}@"
            f"{self.config.host}:{self.config.port}/{self.config.database}"
        )
        
        self.engine = create_async_engine(
            connection_string,
            echo=self.config.echo_sql,
            pool_size=self.config.pool_min_size,
            max_overflow=self.config.pool_max_size - self.config.pool_min_size,
            pool_recycle=self.config.pool_recycle_seconds
        )
        
        # Create session factory
        self.session_factory = sessionmaker(
            self.engine, 
            expire_on_commit=False,
            class_=AsyncSession
        )
        
        # Create asyncpg pool for raw SQL queries
        asyncio.create_task(self._create_pool())
    
    async def _create_pool(self):
        """Create asyncpg connection pool"""
        self.pool = await asyncpg.create_pool(
            user=self.config.username,
            password=self.config.password,
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            min_size=self.config.pool_min_size,
            max_size=self.config.pool_max_size
        )
    
    @asynccontextmanager
    async def session(self):
        """Get a database session"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    @asynccontextmanager
    async def connection(self):
        """Get a raw database connection"""
        if not self.pool:
            await self._create_pool()
            
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute_query(self, query, *args):
        """Execute a raw SQL query and return results"""
        async with self.connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_scalar(self, query, *args):
        """Execute a raw SQL query and return a single value"""
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute_transaction(self, callback):
        """Execute multiple statements in a transaction"""
        async with self.connection() as conn:
            async with conn.transaction():
                return await callback(conn)
    
    async def close_connections(self):
        """Close all database connections"""
        if self.pool:
            await self.pool.close()
        
        if self.engine:
            await self.engine.dispose()
```

### 7.2 Repository Implementation

```python
class AccountRepositoryImpl(IAccountRepository):
    """Implementation of account repository"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    async def get_by_id(self, account_id):
        """Get account by ID"""
        async with self.db_manager.session() as session:
            return await session.get(Account, account_id)
    
    async def get_by_code(self, code):
        """Get account by code"""
        async with self.db_manager.session() as session:
            result = await session.execute(
                select(Account).where(Account.code == code)
            )
            return result.scalars().first()
    
    async def get_all_active(self):
        """Get all active accounts"""
        async with self.db_manager.session() as session:
            result = await session.execute(
                select(Account)
                .where(Account.is_active == True)
                .order_by(Account.code)
            )
            return result.scalars().all()
    
    async def get_by_type(self, account_type):
        """Get accounts by type"""
        async with self.db_manager.session() as session:
            result = await session.execute(
                select(Account)
                .where(
                    Account.account_type == account_type,
                    Account.is_active == True
                )
                .order_by(Account.code)
            )
            return result.scalars().all()
    
    async def has_transactions(self, account_id):
        """Check if account has transactions"""
        query = """
            SELECT EXISTS (
                SELECT 1 FROM accounting.journal_entry_lines
                WHERE account_id = $1
                LIMIT 1
            )
        """
        return await self.db_manager.execute_scalar(query, account_id)
    
    async def save(self, account):
        """Save account"""
        async with self.db_manager.session() as session:
            session.add(account)
            await session.commit()
            await session.refresh(account)
            return account
    
    async def delete(self, account_id):
        """Delete account (soft delete by deactivating)"""
        account = await self.get_by_id(account_id)
        if not account:
            return False
        
        account.is_active = False
        await self.save(account)
        return True
    
    async def get_account_tree(self):
        """Get hierarchical account tree"""
        # Use raw SQL for better performance
        query = """
            WITH RECURSIVE account_tree AS (
                -- Base case: root accounts
                SELECT 
                    a.id, a.code, a.name, a.account_type, a.sub_type, 
                    a.parent_id, a.is_active, 0 AS level
                FROM accounting.accounts a
                WHERE a.parent_id IS NULL
                
                UNION ALL
                
                -- Recursive case: child accounts
                SELECT 
                    a.id, a.code, a.name, a.account_type, a.sub_type, 
                    a.parent_id, a.is_active, t.level + 1
                FROM accounting.accounts a
                JOIN account_tree t ON a.parent_id = t.id
            )
            SELECT * FROM account_tree
            ORDER BY account_type, level, code;
        """
        
        result = await self.db_manager.execute_query(query)
        
        # Convert to nested dictionary structure
        accounts = []
        for row in result:
            account = {
                'id': row['id'],
                'code': row['code'],
                'name': row['name'],
                'account_type': row['account_type'],
                'sub_type': row['sub_type'],
                'parent_id': row['parent_id'],
                'is_active': row['is_active'],
                'level': row['level'],
                'children': []
            }
            accounts.append(account)
        
        # Build tree structure
        account_map = {account['id']: account for account in accounts}
        tree = []
        
        for account in accounts:
            if not account['parent_id']:
                tree.append(account)
            else:
                parent = account_map.get(account['parent_id'])
                if parent:
                    parent['children'].append(account)
        
        return tree
```

## 8. Deployment and Installation

### 8.1 Application Packaging

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="sg_bookkeeper",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PySide6>=6.2.3",
        "SQLAlchemy>=1.4.0",
        "asyncpg>=0.25.0",
        "alembic>=1.7.5",
        "pydantic>=1.9.0",
        "reportlab>=3.6.6",
        "openpyxl>=3.0.9",
        "python-dateutil>=2.8.2",
        "bcrypt>=3.2.0",
        "pyqtdarktheme>=1.1.0"
    ],
    entry_points={
        "console_scripts": [
            "sg_bookkeeper=app.main:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Singapore small business bookkeeping application",
    keywords="accounting, bookkeeping, singapore, gst, tax",
    url="https://github.com/yourusername/sg_bookkeeper",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial :: Accounting",
    ],
)
```

### 8.2 Database Initialization Script

```python
# db_init.py
import asyncio
import asyncpg
import argparse
import getpass
import os
import sys

async def create_database(args):
    """Create PostgreSQL database and initialize schema"""
    # Connect to PostgreSQL server (postgres database)
    try:
        conn = await asyncpg.connect(
            user=args.user,
            password=args.password,
            host=args.host,
            port=args.port,
            database='postgres'
        )
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return False
    
    try:
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
            args.dbname
        )
        
        if exists:
            if args.drop_existing:
                print(f"Dropping existing database '{args.dbname}'...")
                await conn.execute(f"DROP DATABASE {args.dbname}")
            else:
                print(f"Database '{args.dbname}' already exists. Use --drop-existing to recreate.")
                return False
        
        # Create database
        print(f"Creating database '{args.dbname}'...")
        await conn.execute(f"CREATE DATABASE {args.dbname}")
        
        # Close connection to postgres database
        await conn.close()
        
        # Connect to the new database
        conn = await asyncpg.connect(
            user=args.user,
            password=args.password,
            host=args.host,
            port=args.port,
            database=args.dbname
        )
        
        # Create extensions
        print("Creating extensions...")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        
        # Create schemas
        print("Creating schemas...")
        await conn.execute("CREATE SCHEMA IF NOT EXISTS core")
        await conn.execute("CREATE SCHEMA IF NOT EXISTS accounting")
        await conn.execute("CREATE SCHEMA IF NOT EXISTS business")
        await conn.execute("CREATE SCHEMA IF NOT EXISTS audit")
        
        # Initialize database with schema and base data
        print("Initializing database schema...")
        
        # Read schema SQL file
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema SQL
        await conn.execute(schema_sql)
        
        # Read initial data SQL file
        data_path = os.path.join(os.path.dirname(__file__), 'initial_data.sql')
        with open(data_path, 'r') as f:
            data_sql = f.read()
        
        # Execute initial data SQL
        print("Loading initial data...")
        await conn.execute(data_sql)
        
        print(f"Database '{args.dbname}' created and initialized successfully.")
        return True
    
    except Exception as e:
        print(f"Error creating database: {e}")
        return False
    
    finally:
        # Close connection
        if conn:
            await conn.close()

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Initialize SG Bookkeeper database')
    
    parser.add_argument('--host', default='localhost', help='PostgreSQL server host')
    parser.add_argument('--port', type=int, default=5432, help='PostgreSQL server port')
    parser.add_argument('--user', default='postgres', help='PostgreSQL username')
    parser.add_argument('--password', help='PostgreSQL password')
    parser.add_argument('--dbname', default='sg_bookkeeper', help='Database name to create')
    parser.add_argument('--drop-existing', action='store_true', help='Drop database if it exists')
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Get password if not provided
    if not args.password:
        args.password = getpass.getpass(f"Password for PostgreSQL user '{args.user}': ")
    
    # Run database creation
    success = asyncio.run(create_database(args))
    
    # Exit with appropriate status
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
```

### 8.3 Application Installation Guide

```
# SG Bookkeeper Installation Guide

## System Requirements

- **Operating System**: 
  - Windows 10/11
  - macOS 12+
  - Ubuntu 20.04+ or other Linux distributions

- **Hardware**:
  - CPU: 2GHz dual-core processor or better
  - RAM: 4GB minimum (8GB recommended)
  - Storage: 5GB free disk space
  - Display: 1366x768 minimum resolution

- **Software Prerequisites**:
  - Python 3.9 or higher
  - PostgreSQL 14 or higher
  - pip (Python package installer)
  - Git (optional, for development installation)

## Installation Steps

### 1. Install PostgreSQL

#### Windows
1. Download PostgreSQL installer from https://www.postgresql.org/download/windows/
2. Run the installer and follow the installation wizard
3. Select components: PostgreSQL Server, pgAdmin, Command Line Tools
4. Choose a password for the postgres user (remember this)
5. Use default port (5432) unless you have a specific reason to change it
6. Complete the installation

#### macOS
1. Install using Homebrew:
   ```
   brew install postgresql@14
   ```
2. Start PostgreSQL service:
   ```
   brew services start postgresql@14
   ```

#### Ubuntu/Debian
1. Add PostgreSQL repository:
   ```
   sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
   wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
   sudo apt-get update
   ```
2. Install PostgreSQL:
   ```
   sudo apt-get install postgresql-14
   ```
3. Start PostgreSQL service:
   ```
   sudo systemctl start postgresql
   ```

### 2. Install SG Bookkeeper

#### Using pip (recommended for end users)
1. Install from PyPI:
   ```
   pip install sg-bookkeeper
   ```

#### From source (for developers)
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/sg_bookkeeper.git
   cd sg_bookkeeper
   ```
2. Install dependencies:
   ```
   pip install -e .
   ```

### 3. Initialize Database

1. Run the database initialization script:
   ```
   python -m sg_bookkeeper.db_init --user postgres
   ```
2. Enter the PostgreSQL password when prompted
3. The script will create the database and initialize the schema

### 4. Launch the Application

1. Start SG Bookkeeper:
   ```
   sg_bookkeeper
   ```
2. On first run, you'll be prompted to create an admin user
3. Enter your desired username, password, and other details
4. The application will then load the main interface

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running: 
  - Windows: Check Services
  - macOS: `brew services list`
  - Linux: `sudo systemctl status postgresql`
- Check connection settings in `~/.sg_bookkeeper/config.ini`
- Ensure the postgres user has appropriate permissions

### Missing Dependencies
- If you encounter missing dependency errors, try:
  ```
  pip install --upgrade sg-bookkeeper[all]
  ```

### Application Crashes
- Check log files in `~/.sg_bookkeeper/logs/`
- Verify your system meets the minimum requirements
- Try running with debug mode: `sg_bookkeeper --debug`

## Additional Configuration

### Custom Database Location
1. Edit the configuration file at `~/.sg_bookkeeper/config.ini`
2. Modify the database connection parameters as needed
3. Restart the application

### Language Settings
1. The application uses the system locale by default
2. To override, set the `LANGUAGE` environment variable before launching

## Uninstallation

1. To uninstall the application:
   ```
   pip uninstall sg-bookkeeper
   ```
2. To remove all data and configuration:
   ```
   rm -rf ~/.sg_bookkeeper
   ```
3. To drop the PostgreSQL database:
   ```
   dropdb -U postgres sg_bookkeeper
   ```

---

## 9. Conclusion

This Technical Design Specification Document provides comprehensive implementation details for the Singapore Small Business Bookkeeping Application. By following this document, developers should be able to implement a feature-complete accounting system that meets the requirements specified in the Product Requirements Document.

The document covers all aspects of the application from system architecture to user interface design, data models, business logic, and deployment procedures. Each section provides concrete implementation examples and code snippets to guide the development process.

Key implementation highlights include:
- A three-tier architecture separating presentation, business logic, and data access
- A comprehensive PostgreSQL database schema optimized for accounting operations
- Modular Python components following best practices and design patterns
- Singapore-specific tax and accounting logic built into the core of the application
- A modern PyQt6/PySide6 user interface with responsive design

Developers should use this document as a reference while implementing the application, adapting the provided code examples to the specific requirements of their implementation environment.
