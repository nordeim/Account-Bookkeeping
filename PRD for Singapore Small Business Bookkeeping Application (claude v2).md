# Product Requirements Document: Singapore Small Business Bookkeeping Application
# Claude 3.7 v2

## 1. Executive Summary

### 1.1 Product Vision
Develop a comprehensive, enterprise-grade bookkeeping application tailored specifically for Singapore small businesses that combines professional accounting capabilities with intuitive usability. The application will empower users with minimal accounting knowledge to maintain compliant financial records, generate accurate reports, and streamline tax filing processes.

### 1.2 Business Objectives
- Reduce small business accounting overhead by 70%
- Ensure 100% compliance with Singapore regulatory requirements
- Decrease tax preparation time by 80%
- Eliminate common accounting errors through automated validation
- Provide actionable financial insights through intuitive dashboards

### 1.3 Key Success Metrics
- User onboarding completion rate > 90%
- Transaction entry average time < 60 seconds
- Report generation < 5 seconds
- Zero data loss incidents
- First-time tax submission success rate > 95%

## 2. User Personas and Journeys

### 2.1 Primary Personas

#### 2.1.1 Small Business Owner (Jia Hui)
- **Background:** Operates a retail business with 5 employees
- **Technical Proficiency:** Moderate
- **Accounting Knowledge:** Basic
- **Primary Goals:** 
  - Track business performance
  - Ensure tax compliance
  - Minimize time spent on bookkeeping
- **Pain Points:**
  - Limited time for administrative tasks
  - Anxiety about compliance errors
  - Difficulty interpreting financial data

#### 2.1.2 Administrative Assistant (Michael)
- **Background:** Handles day-to-day finances for a service business
- **Technical Proficiency:** High
- **Accounting Knowledge:** Moderate
- **Primary Goals:**
  - Efficient transaction entry
  - Invoice management
  - Basic financial reporting
- **Pain Points:**
  - Repetitive data entry
  - Tracking payment statuses
  - Reconciling accounts

#### 2.1.3 External Accountant (Sarah)
- **Background:** Professional accountant serving multiple small businesses
- **Technical Proficiency:** High
- **Accounting Knowledge:** Expert
- **Primary Goals:**
  - Review client finances
  - Prepare tax filings
  - Identify financial optimizations
- **Pain Points:**
  - Inconsistent record formats from clients
  - Missing transaction details
  - Limited audit trails

### 2.2 Key User Journeys

#### 2.2.1 Daily Transaction Recording
1. User logs into application
2. Views dashboard with outstanding tasks
3. Enters sales and purchase transactions
4. System validates entries against business rules
5. Transactions are posted to appropriate accounts
6. User receives confirmation and updated financial position

#### 2.2.2 Monthly Reconciliation
1. User imports bank statement
2. System matches transactions automatically
3. User reviews unmatched transactions
4. User creates new transactions for unmatched items
5. System updates reconciliation status
6. User confirms reconciliation completion

#### 2.2.3 Quarterly GST Filing
1. User navigates to tax reporting module
2. Selects GST return period
3. System generates draft GST F5 form
4. User reviews and approves calculations
5. System generates final GST return
6. User exports IRAS-compatible file
7. System marks period as filed

#### 2.2.4 Annual Tax Preparation
1. User initiates year-end closing process
2. System validates completeness of transactions
3. System generates tax schedules and worksheets
4. User reviews and approves tax calculations
5. System generates Form C-S compatible data
6. User exports tax filing documents
7. System archives fiscal year data

## 3. Functional Specifications

### 3.1 Core Accounting Engine

#### 3.1.1 Chart of Accounts
- **Structure:** Multi-tier hierarchy (5 levels maximum)
- **Predefined Templates:** 
  - General Singapore business template
  - Retail-specific template
  - Service business template
  - Manufacturing template
- **Account Properties:**
  - Account code (alphanumeric, up to 10 characters)
  - Account name (up to 100 characters)
  - Account type (Asset, Liability, Equity, Revenue, Expense)
  - Sub-type (Current Asset, Fixed Asset, etc.)
  - Tax treatment (Taxable, Non-taxable, Exempt, etc.)
  - GST applicability
  - Status (Active/Inactive)
  - Description
  - Financial statement mapping
- **Custom Fields:** Support for up to 10 user-defined fields
- **Versioning:** Track account structure changes with timestamps

#### 3.1.2 Double-Entry Accounting System
- **Journal Types:**
  - General Journal
  - Sales Journal
  - Purchase Journal
  - Cash Receipts Journal
  - Cash Disbursements Journal
  - Payroll Journal
- **Transaction Properties:**
  - Transaction ID (auto-generated)
  - Date and time (to second precision)
  - Source document reference
  - Description (up to 500 characters)
  - Line items (unlimited)
  - User ID of creator
  - Creation timestamp
  - Last modified timestamp
  - Approval status
  - Attachment capability (up to 10 files per transaction)
- **Validation Rules:**
  - Debit/credit balance equality
  - Period validation (open/closed)
  - Account validity check
  - Currency validation
  - Tax code validation
- **Transaction Templates:**
  - Customizable recurring transaction templates
  - Scheduled posting capability
  - Variable amount support

#### 3.1.3 Fiscal Periods
- **Period Configuration:**
  - Customizable fiscal year start/end
  - Monthly, quarterly, and annual period definitions
  - Support for 4-4-5 accounting periods
- **Period Management:**
  - Open/close periods individually
  - Period reopening with authorization
  - Period status indicators
  - Automatic period rollovers

#### 3.1.4 Multi-Currency Support
- **Currency Configuration:**
  - Base currency (SGD)
  - Support for unlimited additional currencies
  - Daily exchange rate tables
  - Historical rate storage
- **Currency Processing:**
  - Automatic conversions to base currency
  - Realized/unrealized gain/loss calculations
  - Currency revaluation functionality
  - Foreign currency reporting

### 3.2 Tax Management

#### 3.2.1 Goods and Services Tax (GST)
- **GST Configuration:**
  - GST registration details
  - Filing frequency (Monthly, Quarterly, Semi-annually)
  - Standard rate (7%)
  - Support for zero-rated and exempt supplies
  - Special schemes support (e.g., Major Exporter Scheme)
- **GST Processing:**
  - Automatic GST calculation on transactions
  - Input and output tax tracking
  - GST adjustments and corrections
  - GST audit trail
- **GST Reporting:**
  - GST F5 form preparation
  - GST F7 form for corrections
  - Transaction listings for audit
  - Input tax claims tracking
  - Non-allowable input tax identification

#### 3.2.2 Income Tax
- **Income Tax Configuration:**
  - Business entity type (Sole Proprietor, Partnership, Pte Ltd)
  - YA (Year of Assessment) settings
  - Tax incentives and exemptions
- **Tax Processing:**
  - Automatic categorization of revenue and expenses
  - Capital allowance tracking
  - Tax adjustment capabilities
  - Provisional tax calculation
- **Tax Reporting:**
  - Form C-S/C data preparation
  - Tax computation schedules
  - Capital allowance schedules
  - Basis period calculations
  - XBRL-ready data export

#### 3.2.3 Withholding Tax
- **Withholding Tax Configuration:**
  - Rate tables for different payment types
  - Recipient categories (resident/non-resident)
- **Withholding Tax Processing:**
  - Automatic calculation on applicable transactions
  - Withholding tax certificates generation
  - S45 form preparation
- **Withholding Tax Reporting:**
  - Annual withholding tax returns
  - Certificate summaries
  - Recipient statements

### 3.3 Financial Reporting

#### 3.3.1 Standard Reports
- **Balance Sheet:**
  - SFRS-compliant format
  - Customizable line item grouping
  - Comparative periods (up to 5 years)
  - Notes to accounts linking
- **Profit & Loss Statement:**
  - Multiple format options (nature/function of expense)
  - Department/cost center filtering
  - Monthly/quarterly/annual views
  - Budget comparison
- **Cash Flow Statement:**
  - Direct and indirect method support
  - Cash flow category breakdown
  - Forecasting capabilities
- **Trial Balance:**
  - Detailed and summary views
  - Filtered by account types
  - Multi-period comparison
- **General Ledger:**
  - Account transaction history
  - Opening/closing balance calculation
  - Transaction drill-down
  - Document attachment access
- **Accounts Receivable/Payable:**
  - Aging analysis (30/60/90/120+ days)
  - Customer/vendor statements
  - Payment prediction
  - Collection/payment prioritization

#### 3.3.2 Custom Reporting
- **Report Designer:**
  - Drag-and-drop interface
  - Field selection from all data entities
  - Formula builder with accounting functions
  - Conditional formatting support
  - Grouping and subtotal capabilities
- **Report Parameters:**
  - Date range selection
  - Entity filters (customers, vendors, etc.)
  - Account selection
  - Comparison basis options
- **Output Formats:**
  - PDF (with password protection option)
  - Excel (with formula preservation)
  - CSV (with encoding options)
  - HTML (for web viewing)
  - XML (for data interchange)

#### 3.3.3 Dashboard and Analytics
- **Financial Dashboards:**
  - Cash position widget
  - Profit trend analysis
  - Expense breakdown
  - Revenue composition
  - Tax liability tracker
- **KPI Monitoring:**
  - Current ratio
  - Quick ratio
  - Gross profit margin
  - Net profit margin
  - Inventory turnover
  - Receivables turnover
  - Custom KPI definition capability
- **Visualization Components:**
  - Line charts for trends
  - Bar/column charts for comparisons
  - Pie/donut charts for composition
  - Gauge charts for KPIs
  - Table grids for detailed data

### 3.4 Business Operations

#### 3.4.1 Customer Management
- **Customer Records:**
  - Basic information (name, address, contact details)
  - Multiple contact persons
  - Custom categorization
  - Credit terms and limits
  - Tax information (GST registration, etc.)
  - Payment methods
  - Communication preferences
  - Notes and documents
- **Customer Transactions:**
  - Sales invoice creation
  - Credit/debit note processing
  - Receipt recording
  - Statement generation
  - Customer-specific pricing
- **Customer Analytics:**
  - Purchase history analysis
  - Payment behavior tracking
  - Profitability analysis
  - Credit risk assessment

#### 3.4.2 Vendor Management
- **Vendor Records:**
  - Basic information (name, address, contact details)
  - Multiple contact persons
  - Custom categorization
  - Payment terms
  - Tax information (GST registration, withholding tax status)
  - Bank account details (with encryption)
  - Notes and documents
- **Vendor Transactions:**
  - Purchase invoice recording
  - Credit/debit note processing
  - Payment processing
  - Statement reconciliation
- **Vendor Analytics:**
  - Purchase volume analysis
  - Payment scheduling
  - Expense categorization
  - Vendor performance metrics

#### 3.4.3 Invoice Management
- **Sales Invoices:**
  - Customizable invoice templates
  - Automatic numbering with format configuration
  - Item/service selection from catalog
  - Multiple tax handling
  - Discount structures (percentage, amount, tiered)
  - Partial payment tracking
  - Due date calculation and monitoring
  - Automatic late payment interest calculation
- **Purchase Invoices:**
  - Vendor invoice capture
  - Line item verification against purchase orders
  - Expense allocation to departments/projects
  - Payment scheduling
  - Approval workflow
- **Recurring Invoices:**
  - Template-based generation
  - Automatic scheduling
  - Variable amount support
  - Email distribution

#### 3.4.4 Inventory Management
- **Inventory Items:**
  - SKU and barcode support
  - Multiple units of measure
  - Costing methods (FIFO, LIFO, Average Cost)
  - Minimum stock levels
  - Reorder points
  - Location tracking
- **Inventory Transactions:**
  - Stock receipts
  - Stock issues
  - Stock transfers
  - Stock adjustments
  - Stock counts
- **Inventory Valuation:**
  - Real-time valuation
  - Historical cost tracking
  - Periodic revaluation
  - Valuation reporting

#### 3.4.5 Banking Operations
- **Bank Account Management:**
  - Multiple bank account support
  - Account reconciliation
  - Bank statement import (CSV, OFX, QIF, MT940)
  - Transaction matching algorithms
  - Unreconciled item tracking
- **Payment Processing:**
  - Batch payment creation
  - Payment approval workflows
  - Electronic payment file generation (GIRO formats)
  - Payment status tracking
- **Cash Management:**
  - Cash flow forecasting
  - Cash position reporting
  - Float/petty cash tracking

### 3.5 System Administration

#### 3.5.1 User Management
- **User Accounts:**
  - Username/password authentication
  - Role-based access control
  - Multi-factor authentication option
  - Password policy enforcement
  - Account lockout protection
  - Session timeout configuration
- **Role Configuration:**
  - Predefined roles (Administrator, Accountant, Bookkeeper, Viewer)
  - Custom role creation
  - Granular permission assignment
  - Function-level access control
  - Data-level access control

#### 3.5.2 Data Management
- **Backup and Recovery:**
  - Scheduled automated backups
  - On-demand manual backups
  - Incremental and full backup options
  - Encrypted backup files
  - Configurable retention policy
  - Point-in-time recovery capability
- **Data Import/Export:**
  - Chart of accounts import/export
  - Transaction batch import
  - Customer/vendor data import
  - Template-based data mapping
  - Error handling and validation
- **Data Archive:**
  - Fiscal year archiving
  - Archived data access
  - Archive retention policies
  - Archive storage optimization

#### 3.5.3 Audit and Compliance
- **Audit Trail:**
  - Comprehensive change logging
  - User action recording
  - Before/after value capture
  - Tamper-evident logging
  - Searchable audit history
- **Compliance Features:**
  - Digital signature support
  - Document retention enforcement
  - PDPA compliance controls
  - Data export restrictions

## 4. Technical Specifications

### 4.1 Architecture

#### 4.1.1 Application Architecture
- **Application Pattern:** Three-tier architecture
  - Presentation Layer (PyQt6/PySide6 GUI)
  - Business Logic Layer (Python modules)
  - Data Access Layer (PostgreSQL interface)
- **Component Structure:**
  - Core modules (accounting engine, tax calculation)
  - Business modules (invoicing, banking, reporting)
  - Utility modules (import/export, backup, security)
  - UI components (screens, dialogs, widgets)
- **Design Patterns:**
  - Model-View-Controller for UI components
  - Repository pattern for data access
  - Factory pattern for object creation
  - Observer pattern for event handling
  - Strategy pattern for tax calculation

#### 4.1.2 Database Architecture
- **PostgreSQL Implementation:**
  - Version: PostgreSQL 14 or higher
  - Extensions: pgcrypto, temporal_tables, pg_stat_statements
  - Connection pooling: PgBouncer
  - Schema organization: core, accounting, business, audit
  - Indexing strategy: B-tree for primary keys, GIN for text search
- **High-Performance Features:**
  - Partitioning for transaction tables (by fiscal period)
  - Materialized views for reporting
  - Query optimization with explain analyze
  - Server-side functions for complex calculations
  - Proper indexing strategy for all query patterns

#### 4.1.3 Security Architecture
- **Authentication:**
  - Salted password hashing (Argon2)
  - OAuth2 support for external authentication
  - Session management with JWT
  - Remember-me functionality with secure token
- **Authorization:**
  - Role-based access control
  - Object-level permissions
  - Function-level permissions
  - Row-level security in PostgreSQL
- **Data Protection:**
  - TLS for all database connections
  - Transparent column encryption for sensitive data
  - Encrypted backups
  - Secure audit logs

### 4.2 Technology Stack

#### 4.2.1 Frontend Technologies
- **GUI Framework:** PyQt6/PySide6
  - Qt version: 6.2 or higher
  - QML for custom components
  - Qt Style Sheets for theming
  - Qt Charts for visualizations
- **UI Components:**
  - Custom accounting-specific widgets
  - Form validation framework
  - Responsive layout system
  - Dark/light mode support
- **Client-Side Utilities:**
  - Local caching for performance
  - Background processing for long operations
  - Offline mode capabilities
  - Auto-save functionality

#### 4.2.2 Backend Technologies
- **Core Language:** Python 3.9+
  - Typing support with mypy
  - Async support with asyncio
  - Concurrency with threading/multiprocessing
- **Database Access:**
  - SQLAlchemy ORM
  - Alembic for migrations
  - psycopg2 or asyncpg for PostgreSQL connectivity
- **Business Logic:**
  - Dedicated accounting calculation engine
  - Tax rule engine with decision tables
  - Financial reporting framework
  - Document generation system

#### 4.2.3 Development Tools
- **Version Control:**
  - Git with branch protection
  - Semantic versioning
  - Conventional commits
- **Build System:**
  - Poetry for dependency management
  - PyInstaller for executable creation
  - Qt Resource System for assets
- **Testing Framework:**
  - Pytest for unit and integration testing
  - Hypothesis for property-based testing
  - Coverage reporting with minimum 85% threshold
  - UI testing with QTest

### 4.3 Database Schema

#### 4.3.1 Core Entities
- **Chart of Accounts:**
  ```sql
  CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')),
    sub_type VARCHAR(30),
    tax_treatment VARCHAR(20),
    gst_applicable BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    parent_id INTEGER REFERENCES accounts(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL,
    updated_by INTEGER NOT NULL
  );
  ```

- **Fiscal Periods:**
  ```sql
  CREATE TABLE fiscal_periods (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    period_type VARCHAR(10) NOT NULL CHECK (period_type IN ('Month', 'Quarter', 'Year')),
    status VARCHAR(10) NOT NULL CHECK (status IN ('Open', 'Closed', 'Archived')),
    is_adjustment BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL,
    updated_by INTEGER NOT NULL,
    CONSTRAINT date_range_check CHECK (start_date <= end_date),
    CONSTRAINT unique_period_dates UNIQUE (start_date, end_date)
  );
  ```

- **Journal Entries:**
  ```sql
  CREATE TABLE journal_entries (
    id SERIAL PRIMARY KEY,
    entry_no VARCHAR(20) NOT NULL UNIQUE,
    journal_type VARCHAR(20) NOT NULL,
    entry_date DATE NOT NULL,
    fiscal_period_id INTEGER NOT NULL REFERENCES fiscal_periods(id),
    description VARCHAR(500),
    reference VARCHAR(100),
    is_recurring BOOLEAN DEFAULT FALSE,
    recurring_pattern_id INTEGER,
    is_posted BOOLEAN DEFAULT FALSE,
    is_reversed BOOLEAN DEFAULT FALSE,
    reversing_entry_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL,
    updated_by INTEGER NOT NULL
  );
  ```

- **Journal Entry Lines:**
  ```sql
  CREATE TABLE journal_entry_lines (
    id SERIAL PRIMARY KEY,
    journal_entry_id INTEGER NOT NULL REFERENCES journal_entries(id),
    line_number INTEGER NOT NULL,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    description VARCHAR(200),
    debit_amount NUMERIC(15,2) DEFAULT 0,
    credit_amount NUMERIC(15,2) DEFAULT 0,
    currency_code CHAR(3) DEFAULT 'SGD',
    exchange_rate NUMERIC(15,6) DEFAULT 1,
    tax_code VARCHAR(20),
    tax_amount NUMERIC(15,2) DEFAULT 0,
    dimension1_id INTEGER, -- For department, cost center, etc.
    dimension2_id INTEGER, -- For project, product line, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_debit_credit CHECK (
      (debit_amount > 0 AND credit_amount = 0) OR
      (credit_amount > 0 AND debit_amount = 0)
    )
  );
  ```

#### 4.3.2 Business Entities
- **Customers:**
  ```sql
  CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    customer_code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    legal_name VARCHAR(200),
    uen_no VARCHAR(20), -- Unique Entity Number
    gst_registered BOOLEAN DEFAULT FALSE,
    gst_no VARCHAR(20),
    contact_person VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    address_line1 VARCHAR(100),
    address_line2 VARCHAR(100),
    postal_code VARCHAR(20),
    city VARCHAR(50),
    country VARCHAR(50) DEFAULT 'Singapore',
    credit_terms INTEGER DEFAULT 30, -- Days
    credit_limit NUMERIC(15,2),
    currency_code CHAR(3) DEFAULT 'SGD',
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL,
    updated_by INTEGER NOT NULL
  );
  ```

- **Vendors:**
  ```sql
  CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    vendor_code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    legal_name VARCHAR(200),
    uen_no VARCHAR(20), -- Unique Entity Number
    gst_registered BOOLEAN DEFAULT FALSE,
    gst_no VARCHAR(20),
    withholding_tax_applicable BOOLEAN DEFAULT FALSE,
    withholding_tax_rate NUMERIC(5,2),
    contact_person VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    address_line1 VARCHAR(100),
    address_line2 VARCHAR(100),
    postal_code VARCHAR(20),
    city VARCHAR(50),
    country VARCHAR(50) DEFAULT 'Singapore',
    payment_terms INTEGER DEFAULT 30, -- Days
    currency_code CHAR(3) DEFAULT 'SGD',
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    bank_account_name VARCHAR(100),
    bank_account_number VARCHAR(50),
    bank_name VARCHAR(100),
    bank_branch VARCHAR(100),
    bank_swift_code VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL,
    updated_by INTEGER NOT NULL
  );
  ```

- **Products/Services:**
  ```sql
  CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    product_type VARCHAR(20) NOT NULL CHECK (product_type IN ('Inventory', 'Service', 'Non-Inventory')),
    unit_of_measure VARCHAR(20),
    sales_price NUMERIC(15,2),
    purchase_price NUMERIC(15,2),
    sales_account_id INTEGER REFERENCES accounts(id),
    purchase_account_id INTEGER REFERENCES accounts(id),
    inventory_account_id INTEGER REFERENCES accounts(id),
    tax_code VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL,
    updated_by INTEGER NOT NULL
  );
  ```

#### 4.3.3 Tax Entities
- **Tax Codes:**
  ```sql
  CREATE TABLE tax_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    description VARCHAR(100) NOT NULL,
    tax_type VARCHAR(20) NOT NULL CHECK (tax_type IN ('GST', 'Income Tax', 'Withholding Tax')),
    rate NUMERIC(5,2) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    affects_account_id INTEGER REFERENCES accounts(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL,
    updated_by INTEGER NOT NULL
  );
  ```

- **GST Returns:**
  ```sql
  CREATE TABLE gst_returns (
    id SERIAL PRIMARY KEY,
    return_period VARCHAR(20) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    filing_due_date DATE NOT NULL,
    standard_rated_supplies NUMERIC(15,2) DEFAULT 0,
    zero_rated_supplies NUMERIC(15,2) DEFAULT 0,
    exempt_supplies NUMERIC(15,2) DEFAULT 0,
    total_supplies NUMERIC(15,2) DEFAULT 0,
    taxable_purchases NUMERIC(15,2) DEFAULT 0,
    output_tax NUMERIC(15,2) DEFAULT 0,
    input_tax NUMERIC(15,2) DEFAULT 0,
    tax_payable NUMERIC(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Submitted', 'Amended')),
    submission_date DATE,
    submission_reference VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL,
    updated_by INTEGER NOT NULL
  );
  ```

### 4.4 User Interface Specifications

#### 4.4.1 Visual Design
- **Color Palette:**
  - Primary: #1A73E8 (Blue)
  - Secondary: #34A853 (Green)
  - Error: #EA4335 (Red)
  - Warning: #FBBC05 (Yellow)
  - Background: #FFFFFF (Light) / #121212 (Dark)
  - Surface: #F8F9FA (Light) / #1E1E1E (Dark)
  - Text: #202124 (Light) / #E8EAED (Dark)
- **Typography:**
  - Primary Font: Segoe UI (Windows), San Francisco (macOS), Noto Sans (Linux)
  - Heading Sizes: 24px, 20px, 16px, 14px
  - Body Text: 13px
  - Monospace: Consolas, 12px (for amounts and codes)
- **Components:**
  - Rounded corners: 4px radius
  - Elevation: 3 levels of shadows
  - Button styles: Primary, Secondary, Text, Icon
  - Field styles: Outlined, Filled
  - Cards with 8px padding

#### 4.4.2 Screen Layouts
- **Dashboard:**
  ```
  +-------------------------------------------------------+
  | [Logo] Company Name               [User] [Settings]   |
  +---------------+-----------------------------------+---+
  | NAVIGATION    | FINANCIAL SNAPSHOT                |   |
  | * Dashboard   | +-------------+ +---------------+ |   |
  | * Transactions| | Cash Position| | Profit & Loss | |   |
  | * Customers   | | $12,345.67  | | +5% MoM       | |   |
  | * Vendors     | +-------------+ +---------------+ |   |
  | * Banking     | +-------------+ +---------------+ | S |
  | * Products    | | Receivables | | Payables      | | I |
  | * Reports     | | $8,765.43   | | $4,321.09     | | D |
  | * Taxes       | +-------------+ +---------------+ | E |
  | * Settings    |                                   | B |
  |               | RECENT TRANSACTIONS               | A |
  |               | [Table with last 5 transactions]  | R |
  |               |                                   |   |
  |               | UPCOMING                          |   |
  |               | [Table with upcoming due dates]   |   |
  |               |                                   |   |
  +---------------+-----------------------------------+---+
  | [Status Bar] Version 1.0.0 | Last backup: Today 09:15 |
  +-------------------------------------------------------+
  ```

- **Transaction Entry:**
  ```
  +-------------------------------------------------------+
  | [Back] New Transaction                  [Save] [More] |
  +-------------------------------------------------------+
  | Transaction Type: [Dropdown] ▼   Date: [Date Picker]  |
  | Reference: [_____________]    Description: [_________]|
  +-------------------------------------------------------+
  | TRANSACTION DETAILS                                   |
  +-------------------------------------------------------+
  | Account        | Description | Debit    | Credit      |
  |----------------|-------------|----------|-------------|
  | [Account ▼]    | [_________] | [0.00]   | [_________] |
  | [Account ▼]    | [_________] | [_______] | [0.00]     |
  | [+ Add Line]   |             |          |             |
  +-------------------------------------------------------+
  | TOTALS                        | 0.00     | 0.00       |
  +-------------------------------------------------------+
  | [Tax Details] [Attachments] [Notes]                   |
  +-------------------------------------------------------+
  ```

- **Report Viewer:**
  ```
  +-------------------------------------------------------+
  | [Back] Profit & Loss Statement      [Export ▼] [Print]|
  +-------------------------------------------------------+
  | Period: [Jan 2023 - Dec 2023 ▼]  Compare: [Prior Year]|
  | View: [Monthly ▼]  Show: [All Accounts ▼]             |
  +-------------------------------------------------------+
  | PROFIT & LOSS STATEMENT                               |
  | Company Name                                          |
  | For the period Jan 1, 2023 to Dec 31, 2023            |
  +-------------------------------------------------------+
  | REVENUE                          | 2023    | 2022     |
  |----------------------------------|---------|----------|
  | Sales Revenue                    | 100,000 | 80,000   |
  | Service Revenue                  | 50,000  | 45,000   |
  | Other Revenue                    | 5,000   | 3,000    |
  | TOTAL REVENUE                    | 155,000 | 128,000  |
  |                                  |         |          |
  | COST OF SALES                    | 85,000  | 70,000   |
  |                                  |         |          |
  | GROSS PROFIT                     | 70,000  | 58,000   |
  |                                  |         |          |
  | [... Additional line items ...]  |         |          |
  +-------------------------------------------------------+
  | [1] [2] [3] ... [Next >]                              |
  +-------------------------------------------------------+
  ```

#### 4.4.3 Responsive Design
- **Screen Size Adaptations:**
  - Large (>1920px): Multi-panel layout with side-by-side workflows
  - Medium (1366-1920px): Standard layout with full feature set
  - Small (1024-1365px): Compact layout with prioritized components
  - Minimal (<1024px): Essential-only UI with progressive disclosure
- **Layout Rules:**
  - Fluid grid system with 12 columns
  - Breakpoints at 1024px, 1366px, and 1920px
  - Minimum component sizes to ensure usability
  - Scrollable sections for overflow content
  - Collapsible navigation at smaller sizes

#### 4.4.4 Accessibility Features
- **Keyboard Navigation:**
  - Full keyboard accessibility with tab order
  - Keyboard shortcuts for common actions
  - Focus indicators for all interactive elements
- **Screen Reader Support:**
  - ARIA labels and roles
  - Meaningful alt text for all images
  - Semantic HTML structure
- **Visual Accessibility:**
  - High contrast mode
  - Resizable text (up to 200%)
  - Color blindness considerations

### 4.5 Performance Requirements

#### 4.5.1 Response Time Targets
- **UI Interactions:**
  - Button/control response: < 100ms
  - Form submission: < 500ms
  - Simple data retrieval: < 300ms
  - Complex data retrieval: < 2s
- **Processing Operations:**
  - Transaction posting: < 1s
  - Simple report generation: < 3s
  - Complex report generation: < 10s
  - Bank statement import (100 transactions): < 5s

#### 4.5.2 Scalability Parameters
- **Data Volume Handling:**
  - Up to 50,000 transactions per fiscal year
  - Up to 1,000 customers/vendors
  - Up to 5,000 products/services
  - Up to 10 years of historical data
- **Concurrent Operations:**
  - Single-user optimized
  - Support for up to 5 concurrent users in multi-user setup
  - Background processing for intensive operations

#### 4.5.3 Resource Utilization
- **Memory Usage:**
  - Base application: < 150MB RAM
  - Operation overhead: < 100MB additional per complex operation
  - Maximum footprint: < 500MB under normal use
- **CPU Utilization:**
  - Idle: < 2% of single core
  - Normal operation: < 15% of single core
  - Intensive operations: < 50% of single core
- **Disk Usage:**
  - Application installation: < 200MB
  - Database size: ~10MB per 1,000 transactions
  - Temporary storage needs: < 1GB

### 4.6 Security Requirements

#### 4.6.1 Authentication and Authorization
- **User Authentication:**
  - Username/password with minimum complexity requirements
  - Password hashing using Argon2id
  - Failed login attempt limiting (5 attempts before lockout)
  - Session timeout after 30 minutes of inactivity
  - Optional multi-factor authentication
- **Authorization Model:**
  - Role-based access control
  - Predefined roles with permission sets
  - Custom role creation capability
  - Fine-grained permission control (102 individual permissions)

#### 4.6.2 Data Protection
- **Sensitive Data Handling:**
  - Encryption of all PII in database
  - Masked display of sensitive information (bank accounts, etc.)
  - Secure deletion with overwrite for removed data
  - Access logging for sensitive information
- **Data Integrity:**
  - Transaction signatures
  - Audit trail for all data modifications
  - Data validation at all levels (UI, business logic, database)
  - Referential integrity enforcement

#### 4.6.3 Backup and Recovery
- **Backup Procedures:**
  - Scheduled daily backups
  - Transaction log backups every hour
  - Encrypted backup files
  - Backup verification process
- **Recovery Procedures:**
  - Point-in-time recovery capability
  - Database consistency checking
  - Application state recovery
  - Disaster recovery documentation

### 4.7 Integration Capabilities

#### 4.7.1 Data Import/Export
- **Import Formats:**
  - CSV with configurable field mapping
  - Excel (XLSX) with template support
  - QIF/OFX for bank statements
  - XML for structured data
- **Export Formats:**
  - PDF for reports and documents
  - Excel with formatting preserved
  - CSV for raw data
  - XBRL for financial reporting
  - IRAS GST F5 compatible format

#### 4.7.2 Future API Considerations
- **API Architecture:**
  - RESTful API design
  - JSON data format
  - OAuth2 authentication
  - Rate limiting
  - Comprehensive documentation
- **Potential Integrations:**
  - Banking systems
  - E-commerce platforms
  - CRM systems
  - Inventory management
  - Document management

## 5. Implementation and Deployment

### 5.1 Development Methodology
- **Approach:** Agile with two-week sprints
- **Testing:** Test-driven development
- **Quality Assurance:** Continuous integration
- **Documentation:** Inline code documentation and user guides

### 5.2 Deployment Requirements
- **Installation Package:**
  - Self-contained executable
  - Database setup wizard
  - Automated updates
  - Minimal dependencies
- **System Requirements:**
  - OS: Windows 10/11, macOS 12+, Ubuntu 20.04+
  - CPU: 2GHz dual-core or better
  - RAM: 4GB minimum, 8GB recommended
  - Storage: 5GB free space
  - Display: 1366x768 minimum resolution

### 5.3 User Documentation
- **Documentation Types:**
  - Installation guide
  - User manual
  - Quick start guide
  - Video tutorials
  - Context-sensitive help
- **Knowledge Base:**
  - Searchable help database
  - Accounting procedure guides
  - Tax compliance information
  - Troubleshooting section

## 6. Testing Requirements

### 6.1 Testing Types
- **Unit Testing:**
  - Core accounting functions
  - Tax calculation accuracy
  - Business logic validation
- **Integration Testing:**
  - End-to-end workflow validation
  - Database interaction
  - UI component integration
- **Performance Testing:**
  - Response time verification
  - Resource utilization monitoring
  - Large dataset handling
- **Security Testing:**
  - Penetration testing
  - Data protection verification
  - Access control validation

### 6.2 Acceptance Criteria
- **Functional Validation:**
  - 100% compliance with Singapore accounting standards
  - Accurate tax calculations within 0.01 SGD
  - Report generation matching expected outputs
- **Performance Validation:**
  - Meeting all response time targets
  - Successful handling of specified data volumes
  - Resource utilization within limits
- **Usability Validation:**
  - Task completion rate > 95%
  - User satisfaction score > 4/5
  - First-time user onboarding < 30 minutes

## 7. Future Considerations

### 7.1 Planned Enhancements
- **Multi-Currency Advanced Features**
  - Hedging and forward contracts
  - Currency revaluation automation
- **Business Intelligence Module**
  - Advanced analytics dashboard
  - Predictive financial forecasting
- **Multi-Company Support**
  - Consolidated reporting
  - Inter-company transactions
- **Cloud Synchronization**
  - Secure cloud backup
  - Multi-device access
  - Accountant collaboration features

### 7.2 Extensibility Points
- **Plugin Architecture**
  - Custom report designers
  - Industry-specific modules
  - Integration connectors
- **Customization Framework**
  - Form designer
  - Workflow configuration
  - Custom field definitions

## 8. Appendices

### 8.1 Singapore Accounting Standards Reference
- SFRS 1: Presentation of Financial Statements
- SFRS 2: Inventories
- SFRS 7: Statement of Cash Flows
- SFRS 12: Income Taxes
- SFRS 18: Revenue
- SFRS for Small Entities

### 8.2 Singapore Tax Reference
- GST Act and Regulations
- Income Tax Act
- Withholding Tax Requirements

### 8.3 Data Dictionary
- Comprehensive field definitions
- Data type specifications
- Validation rules
- Relationships and constraints

### 8.4 Glossary of Terms
- Accounting terminology
- Singapore-specific business terms
- Technical terminology
