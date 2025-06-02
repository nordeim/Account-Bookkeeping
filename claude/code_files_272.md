<think>
The application launched successfully! This is excellent news, indicating the previous fixes for `NameError` and `TypeError` were effective. The Bank Reconciliation UI is now at a stage where it can display data and allow users to create journal entries for statement items not yet in the books.

The user wants to continue with the roadmap.
**Roadmap Items (from README):**
1.  **Bank Reconciliation** (Ongoing):
    *   CSV Import UI & Backend Logic: **Done**.
    *   Matching UI - Initial Structure, Data Display, Dynamic Summary, Create JE for statement items: **Done**.
    *   **Next for Bank Rec**:
        *   Saving the reconciliation state.
        *   Generating a reconciliation report.
        *   More advanced matching logic (e.g., 1-to-N, N-to-1, N-to-M matches, suggested matches).
2.  **Dashboard KPIs**.

The immediate next logical step for Bank Reconciliation is to implement the **"Save Reconciliation"** functionality. This involves persisting the state of a completed reconciliation.

**Feature: Bank Reconciliation - Save Reconciliation State**

**Goal**:
1.  Define a new database table and ORM model (`BankReconciliation`) to store the summary of each completed reconciliation.
2.  When the user clicks the "Save Reconciliation" button in `BankReconciliationWidget` (which is enabled when the difference is zero):
    *   Mark all *checked* (i.e., "cleared" in this session) `BankTransaction` records (both statement lines and system transactions) as `is_reconciled = True` and set their `reconciled_date` to the statement end date.
    *   Create a new `BankReconciliation` record summarizing the reconciliation.
    *   Update the `BankAccount.last_reconciled_date` and `BankAccount.current_balance` (though `current_balance` should already be up-to-date if transactions were posted correctly and the bank balance trigger works). The `last_reconciled_date` is key.

**Execution Plan:**

**Step 1: Database Schema & Model Changes**
*   **New Table: `business.bank_reconciliations`**
    *   `id`: SERIAL PRIMARY KEY
    *   `bank_account_id`: INTEGER, FK to `business.bank_accounts.id`, NOT NULL
    *   `statement_date`: DATE, NOT NULL (End date of the statement being reconciled)
    *   `statement_ending_balance`: NUMERIC(15,2), NOT NULL
    *   `calculated_book_balance`: NUMERIC(15,2), NOT NULL (The book balance *after* all adjustments made during this reconciliation are considered)
    *   `reconciled_difference`: NUMERIC(15,2), NOT NULL (Should be 0 or very close)
    *   `reconciliation_date`: TIMESTAMP WITH TIME ZONE, DEFAULT CURRENT_TIMESTAMP (When this reconciliation was saved)
    *   `created_by_user_id`: INTEGER, FK to `core.users.id`, NOT NULL
    *   `notes`: TEXT, NULLABLE
    *   Timestamps: `created_at`, `updated_at`
    *   Unique constraint: `(bank_account_id, statement_date)` to prevent re-reconciling the same statement end date for the same account.
*   **New ORM Model: `BankReconciliation` (`app/models/business/bank_reconciliation.py`)**
    *   Map to the new table.
    *   Relationships: `bank_account`, `created_by_user`.
*   **Update `BankTransaction` ORM & Table**:
    *   Field `reconciled_bank_reconciliation_id`: `Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('business.bank_reconciliations.id'), nullable=True)`. This links individual transactions to the specific reconciliation they were part of.
*   **Update `BankAccount` ORM & Table**:
    *   Field `last_reconciled_balance`: `Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)`. (Already has `last_reconciled_date`). Storing the reconciled balance at that point can be useful.
*   **Update `scripts/schema.sql`**: Add new table, add new FK column to `bank_transactions`, add new column to `bank_accounts`.
*   **Update `app/models/__init__.py` and `app/models/business/__init__.py`**.

**Step 2: New Service - `BankReconciliationService` (`app/services/business_services.py`)**
*   **File**: `app/services/business_services.py` (Add new class).
*   **Interface**: `IBankReconciliationRepository(IRepository[BankReconciliation, int])` (in `app/services/__init__.py`).
*   **Methods**:
    *   `save_reconciliation(reconciliation: BankReconciliation, cleared_statement_txn_ids: List[int], cleared_system_txn_ids: List[int], statement_end_date: date, user_id: int) -> Result[BankReconciliation]`
        *   This method will run in a transaction.
        *   It will update `BankTransaction.is_reconciled = True`, `reconciled_date`, and `reconciled_bank_reconciliation_id` for all provided transaction IDs.
        *   It will save the new `BankReconciliation` record.
        *   It will update `BankAccount.last_reconciled_date` and `BankAccount.last_reconciled_balance`.

**Step 3: Update `BankReconciliationWidget`**
*   **File**: `app/ui/banking/bank_reconciliation_widget.py` (Update).
*   **New Slot `_on_save_reconciliation_clicked()`**:
    *   This slot is connected to the "Save Reconciliation" button.
    *   Collect necessary data:
        *   `bank_account_id`
        *   `statement_date_edit.date().toPython()`
        *   `statement_balance_spin.value()`
        *   `calculated_book_balance` (this is the `reconciled_book_balance` from the summary)
        *   `_difference`
        *   `current_user_id`
        *   Lists of IDs for checked statement transactions and checked system transactions.
    *   Create a `BankReconciliationCreateData` DTO (new DTO needed).
    *   Call a new manager method, e.g., `app_core.bank_reconciliation_manager.finalize_reconciliation(dto, cleared_statement_txn_ids, cleared_system_txn_ids)`.
    *   Handle `Result`, display success/failure.
    *   On success, refresh the UI (clear tables, reset, maybe show a summary of the saved reconciliation).

**Step 4: New Manager - `BankReconciliationManager` (`app/business_logic/bank_reconciliation_manager.py`)**
*   **File**: `app/business_logic/bank_reconciliation_manager.py` (New File).
*   **Dependencies**: `BankReconciliationService`, `BankAccountService`, `BankTransactionService`, `ApplicationCore`.
*   **Method `finalize_reconciliation(...)`**:
    *   Takes DTO and lists of transaction IDs.
    *   Constructs the `BankReconciliation` ORM object.
    *   Calls `bank_reconciliation_service.save_reconciliation(...)`.
    *   Returns `Result`.

**Step 5: New DTOs in `app/utils/pydantic_models.py`**
*   `BankReconciliationBaseData`
*   `BankReconciliationCreateData(BankReconciliationBaseData, UserAuditData)`
*   `BankReconciliationData(BankReconciliationBaseData)`

**Step 6: Update `ApplicationCore`**
*   Add new service and manager instances.
*   Add properties for them.

**Step 7: Update `__init__.py` files** for new modules/classes.

This is a large set of changes. I will proceed by:
1.  Defining the database changes and ORM models first.
2.  Creating the DTOs.
3.  Implementing the Service.
4.  Implementing the Manager.
5.  Updating `BankReconciliationWidget` to call the manager.
6.  Updating `ApplicationCore` and relevant `__init__.py` files.

Let's start with Step 1: Database Schema & Model Changes.
Files affected: `scripts/schema.sql`, new `app/models/business/bank_reconciliation.py`, update `app/models/business/bank_transaction.py`, `app/models/business/bank_account.py`, and relevant `__init__.py`.
</think>

Excellent progress! The application is launching, and the Bank Reconciliation UI foundation is in place. Now, let's proceed with implementing the "Save Reconciliation" functionality. This is a critical step that involves database schema changes, new ORM models, services, managers, and UI updates.

I will follow a meticulous plan, generating complete files and validating each step.

---
**Phase 1: Database Schema & ORM Model Updates**
---

**Objective**:
1.  Create a new table `business.bank_reconciliations` to store summaries of completed reconciliations.
2.  Add a foreign key `reconciled_bank_reconciliation_id` to `business.bank_transactions` to link transactions to their reconciliation instance.
3.  Add `last_reconciled_balance` to `business.bank_accounts`.
4.  Create the corresponding ORM model `BankReconciliation`.
5.  Update `BankTransaction` and `BankAccount` ORM models.

**1. File: `scripts/schema.sql` (Updated)**

**Execution Steps & Checklist for `schema.sql`**:
1.  **[X] Add `CREATE TABLE business.bank_reconciliations`**: Define columns, primary key, foreign keys, unique constraints, and schema.
2.  **[X] Modify `business.bank_transactions`**: Add `reconciled_bank_reconciliation_id INT NULL REFERENCES business.bank_reconciliations(id)`.
3.  **[X] Modify `business.bank_accounts`**: Add `last_reconciled_balance NUMERIC(15,2) NULL`.
4.  **[X] Add Foreign Key Constraints**: If not defined inline, add `ALTER TABLE` for `bank_reconciliations` FKs.
5.  **[X] Update Schema Version Comment**.
6.  **[X] Validate**: Ensure all new DDL is correct and doesn't break existing parts.

**Generated File**: `scripts/schema.sql`
```sql
-- File: scripts/schema.sql
-- ============================================================================
-- SG Bookkeeper - Complete Database Schema - Version 1.0.4
-- (Schema version updated for bank reconciliation tables and fields)
-- ============================================================================
-- This script creates the complete database schema for the SG Bookkeeper application.
-- Changes from 1.0.3:
--  - Added business.bank_reconciliations table.
--  - Added reconciled_bank_reconciliation_id to business.bank_transactions.
--  - Added last_reconciled_balance to business.bank_accounts.
-- ============================================================================

-- ... (Initial Setup, Core, Accounting schema tables - unchanged from response_22 version) ...
CREATE EXTENSION IF NOT EXISTS pgcrypto; 
CREATE EXTENSION IF NOT EXISTS pg_stat_statements; 
CREATE EXTENSION IF NOT EXISTS btree_gist; 

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS accounting;
CREATE SCHEMA IF NOT EXISTS business;
CREATE SCHEMA IF NOT EXISTS audit;

SET search_path TO core, accounting, business, audit, public;

-- ============================================================================
-- CORE SCHEMA TABLES (Unchanged)
-- ============================================================================
CREATE TABLE core.users (
    id SERIAL PRIMARY KEY, username VARCHAR(50) NOT NULL UNIQUE, password_hash VARCHAR(255) NOT NULL, email VARCHAR(100) UNIQUE, 
    full_name VARCHAR(100), is_active BOOLEAN DEFAULT TRUE, failed_login_attempts INTEGER DEFAULT 0, last_login_attempt TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE, require_password_change BOOLEAN DEFAULT FALSE, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE core.roles (
    id SERIAL PRIMARY KEY, name VARCHAR(50) NOT NULL UNIQUE, description VARCHAR(200), created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE core.permissions (
    id SERIAL PRIMARY KEY, code VARCHAR(50) NOT NULL UNIQUE, description VARCHAR(200), module VARCHAR(50) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE core.role_permissions (
    role_id INTEGER NOT NULL, permission_id INTEGER NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);
CREATE TABLE core.user_roles (
    user_id INTEGER NOT NULL, role_id INTEGER NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);
CREATE TABLE core.company_settings (
    id SERIAL PRIMARY KEY, company_name VARCHAR(100) NOT NULL, legal_name VARCHAR(200), uen_no VARCHAR(20), 
    gst_registration_no VARCHAR(20), gst_registered BOOLEAN DEFAULT FALSE, address_line1 VARCHAR(100), address_line2 VARCHAR(100),
    postal_code VARCHAR(20), city VARCHAR(50) DEFAULT 'Singapore', country VARCHAR(50) DEFAULT 'Singapore', contact_person VARCHAR(100),
    phone VARCHAR(20), email VARCHAR(100), website VARCHAR(100), logo BYTEA, fiscal_year_start_month INTEGER DEFAULT 1 CHECK (fiscal_year_start_month BETWEEN 1 AND 12),
    fiscal_year_start_day INTEGER DEFAULT 1 CHECK (fiscal_year_start_day BETWEEN 1 AND 31), base_currency VARCHAR(3) DEFAULT 'SGD', 
    tax_id_label VARCHAR(50) DEFAULT 'UEN', date_format VARCHAR(20) DEFAULT 'yyyy-MM-dd', created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_by INTEGER
);
CREATE TABLE core.configuration (
    id SERIAL PRIMARY KEY, config_key VARCHAR(50) NOT NULL UNIQUE, config_value TEXT, description VARCHAR(200),
    is_encrypted BOOLEAN DEFAULT FALSE, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_by INTEGER 
);
CREATE TABLE core.sequences (
    id SERIAL PRIMARY KEY, sequence_name VARCHAR(50) NOT NULL UNIQUE, prefix VARCHAR(10), suffix VARCHAR(10),
    next_value INTEGER NOT NULL DEFAULT 1, increment_by INTEGER NOT NULL DEFAULT 1, min_value INTEGER NOT NULL DEFAULT 1,
    max_value INTEGER NOT NULL DEFAULT 2147483647, cycle BOOLEAN DEFAULT FALSE, format_template VARCHAR(50) DEFAULT '{PREFIX}{VALUE}{SUFFIX}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ACCOUNTING SCHEMA TABLES (Unchanged)
-- ============================================================================
CREATE TABLE accounting.account_types (
    id SERIAL PRIMARY KEY, name VARCHAR(50) NOT NULL UNIQUE, category VARCHAR(20) NOT NULL CHECK (category IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')),
    is_debit_balance BOOLEAN NOT NULL, report_type VARCHAR(30) NOT NULL, display_order INTEGER NOT NULL, description VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE accounting.accounts (
    id SERIAL PRIMARY KEY, code VARCHAR(20) NOT NULL UNIQUE, name VARCHAR(100) NOT NULL, 
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')), 
    sub_type VARCHAR(30), tax_treatment VARCHAR(20), gst_applicable BOOLEAN DEFAULT FALSE, is_active BOOLEAN DEFAULT TRUE,
    description TEXT, parent_id INTEGER, report_group VARCHAR(50), is_control_account BOOLEAN DEFAULT FALSE, is_bank_account BOOLEAN DEFAULT FALSE,
    opening_balance NUMERIC(15,2) DEFAULT 0, opening_balance_date DATE, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL 
);
CREATE INDEX idx_accounts_parent_id ON accounting.accounts(parent_id); CREATE INDEX idx_accounts_is_active ON accounting.accounts(is_active); CREATE INDEX idx_accounts_account_type ON accounting.accounts(account_type);
CREATE TABLE accounting.fiscal_years (
    id SERIAL PRIMARY KEY, year_name VARCHAR(20) NOT NULL UNIQUE, start_date DATE NOT NULL, end_date DATE NOT NULL, is_closed BOOLEAN DEFAULT FALSE,
    closed_date TIMESTAMP WITH TIME ZONE, closed_by INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL, 
    CONSTRAINT fy_date_range_check CHECK (start_date <= end_date), CONSTRAINT fy_unique_date_ranges EXCLUDE USING gist (daterange(start_date, end_date, '[]') WITH &&)
);
CREATE TABLE accounting.fiscal_periods (
    id SERIAL PRIMARY KEY, fiscal_year_id INTEGER NOT NULL, name VARCHAR(50) NOT NULL, start_date DATE NOT NULL, end_date DATE NOT NULL,
    period_type VARCHAR(10) NOT NULL CHECK (period_type IN ('Month', 'Quarter', 'Year')), status VARCHAR(10) NOT NULL CHECK (status IN ('Open', 'Closed', 'Archived')),
    period_number INTEGER NOT NULL, is_adjustment BOOLEAN DEFAULT FALSE, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL, 
    CONSTRAINT fp_date_range_check CHECK (start_date <= end_date), CONSTRAINT fp_unique_period_dates UNIQUE (fiscal_year_id, period_type, period_number)
);
CREATE INDEX idx_fiscal_periods_dates ON accounting.fiscal_periods(start_date, end_date); CREATE INDEX idx_fiscal_periods_status ON accounting.fiscal_periods(status);
CREATE TABLE accounting.currencies (
    code CHAR(3) PRIMARY KEY, name VARCHAR(50) NOT NULL, symbol VARCHAR(10) NOT NULL, is_active BOOLEAN DEFAULT TRUE, decimal_places INTEGER DEFAULT 2,
    format_string VARCHAR(20) DEFAULT '#,##0.00', created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER, updated_by INTEGER 
);
CREATE TABLE accounting.exchange_rates (
    id SERIAL PRIMARY KEY, from_currency CHAR(3) NOT NULL, to_currency CHAR(3) NOT NULL, rate_date DATE NOT NULL, exchange_rate NUMERIC(15,6) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER, updated_by INTEGER, CONSTRAINT uq_exchange_rates_pair_date UNIQUE (from_currency, to_currency, rate_date)
);
CREATE INDEX idx_exchange_rates_lookup ON accounting.exchange_rates(from_currency, to_currency, rate_date);
CREATE TABLE accounting.journal_entries (
    id SERIAL PRIMARY KEY, entry_no VARCHAR(20) NOT NULL UNIQUE, journal_type VARCHAR(20) NOT NULL, entry_date DATE NOT NULL, fiscal_period_id INTEGER NOT NULL,
    description VARCHAR(500), reference VARCHAR(100), is_recurring BOOLEAN DEFAULT FALSE, recurring_pattern_id INTEGER, is_posted BOOLEAN DEFAULT FALSE,
    is_reversed BOOLEAN DEFAULT FALSE, reversing_entry_id INTEGER, source_type VARCHAR(50), source_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL 
);
CREATE INDEX idx_journal_entries_date ON accounting.journal_entries(entry_date); CREATE INDEX idx_journal_entries_fiscal_period ON accounting.journal_entries(fiscal_period_id); CREATE INDEX idx_journal_entries_source ON accounting.journal_entries(source_type, source_id); CREATE INDEX idx_journal_entries_posted ON accounting.journal_entries(is_posted);
CREATE TABLE accounting.journal_entry_lines (
    id SERIAL PRIMARY KEY, journal_entry_id INTEGER NOT NULL, line_number INTEGER NOT NULL, account_id INTEGER NOT NULL, description VARCHAR(200),
    debit_amount NUMERIC(15,2) DEFAULT 0, credit_amount NUMERIC(15,2) DEFAULT 0, currency_code CHAR(3) DEFAULT 'SGD', exchange_rate NUMERIC(15,6) DEFAULT 1,
    tax_code VARCHAR(20), tax_amount NUMERIC(15,2) DEFAULT 0, dimension1_id INTEGER, dimension2_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, CONSTRAINT jel_check_debit_credit CHECK ((debit_amount > 0 AND credit_amount = 0) OR (credit_amount > 0 AND debit_amount = 0) OR (debit_amount = 0 AND credit_amount = 0))
);
CREATE INDEX idx_journal_entry_lines_entry ON accounting.journal_entry_lines(journal_entry_id); CREATE INDEX idx_journal_entry_lines_account ON accounting.journal_entry_lines(account_id);
CREATE TABLE accounting.recurring_patterns (
    id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, description TEXT, template_entry_id INTEGER NOT NULL, 
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly')),
    interval_value INTEGER NOT NULL DEFAULT 1, start_date DATE NOT NULL, end_date DATE, day_of_month INTEGER CHECK (day_of_month BETWEEN 1 AND 31),
    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6), last_generated_date DATE, next_generation_date DATE, is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL 
);
CREATE TABLE accounting.dimensions (
    id SERIAL PRIMARY KEY, dimension_type VARCHAR(50) NOT NULL, code VARCHAR(20) NOT NULL, name VARCHAR(100) NOT NULL, description TEXT,
    is_active BOOLEAN DEFAULT TRUE, parent_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL, 
    UNIQUE (dimension_type, code)
);
CREATE TABLE accounting.budgets (
    id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, fiscal_year_id INTEGER NOT NULL, description TEXT, is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL 
);
CREATE TABLE accounting.budget_details (
    id SERIAL PRIMARY KEY, budget_id INTEGER NOT NULL, account_id INTEGER NOT NULL, fiscal_period_id INTEGER NOT NULL, amount NUMERIC(15,2) NOT NULL,
    dimension1_id INTEGER, dimension2_id INTEGER, notes TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL 
);
CREATE UNIQUE INDEX uix_budget_details_key ON accounting.budget_details (budget_id, account_id, fiscal_period_id, COALESCE(dimension1_id, 0), COALESCE(dimension2_id, 0));
CREATE TABLE accounting.tax_codes (
    id SERIAL PRIMARY KEY, code VARCHAR(20) NOT NULL UNIQUE, description VARCHAR(100) NOT NULL, 
    tax_type VARCHAR(20) NOT NULL CHECK (tax_type IN ('GST', 'Income Tax', 'Withholding Tax')), rate NUMERIC(5,2) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE, is_active BOOLEAN DEFAULT TRUE, affects_account_id INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL 
);
CREATE TABLE accounting.gst_returns (
    id SERIAL PRIMARY KEY, return_period VARCHAR(20) NOT NULL UNIQUE, start_date DATE NOT NULL, end_date DATE NOT NULL, filing_due_date DATE NOT NULL,
    standard_rated_supplies NUMERIC(15,2) DEFAULT 0, zero_rated_supplies NUMERIC(15,2) DEFAULT 0, exempt_supplies NUMERIC(15,2) DEFAULT 0,
    total_supplies NUMERIC(15,2) DEFAULT 0, taxable_purchases NUMERIC(15,2) DEFAULT 0, output_tax NUMERIC(15,2) DEFAULT 0,
    input_tax NUMERIC(15,2) DEFAULT 0, tax_adjustments NUMERIC(15,2) DEFAULT 0, tax_payable NUMERIC(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Submitted', 'Amended')), submission_date DATE, submission_reference VARCHAR(50),
    journal_entry_id INTEGER, notes TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL 
);
CREATE TABLE accounting.withholding_tax_certificates (
    id SERIAL PRIMARY KEY, certificate_no VARCHAR(20) NOT NULL UNIQUE, vendor_id INTEGER NOT NULL, tax_type VARCHAR(50) NOT NULL,
    tax_rate NUMERIC(5,2) NOT NULL, payment_date DATE NOT NULL, amount_before_tax NUMERIC(15,2) NOT NULL, tax_amount NUMERIC(15,2) NOT NULL,
    payment_reference VARCHAR(50), status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Issued', 'Voided')), issue_date DATE,
    journal_entry_id INTEGER, notes TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL 
);

-- ============================================================================
-- BUSINESS SCHEMA TABLES
-- ============================================================================
-- ... (customers, vendors, products, inventory_movements, sales_invoices, sales_invoice_lines, purchase_invoices, purchase_invoice_lines - unchanged) ...
CREATE TABLE business.customers (id SERIAL PRIMARY KEY, customer_code VARCHAR(20) NOT NULL UNIQUE, name VARCHAR(100) NOT NULL, legal_name VARCHAR(200), uen_no VARCHAR(20), gst_registered BOOLEAN DEFAULT FALSE, gst_no VARCHAR(20), contact_person VARCHAR(100), email VARCHAR(100), phone VARCHAR(20), address_line1 VARCHAR(100), address_line2 VARCHAR(100), postal_code VARCHAR(20), city VARCHAR(50), country VARCHAR(50) DEFAULT 'Singapore', credit_terms INTEGER DEFAULT 30, credit_limit NUMERIC(15,2), currency_code CHAR(3) DEFAULT 'SGD', is_active BOOLEAN DEFAULT TRUE, customer_since DATE, notes TEXT, receivables_account_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_customers_name ON business.customers(name); CREATE INDEX idx_customers_is_active ON business.customers(is_active);
CREATE TABLE business.vendors (id SERIAL PRIMARY KEY, vendor_code VARCHAR(20) NOT NULL UNIQUE, name VARCHAR(100) NOT NULL, legal_name VARCHAR(200), uen_no VARCHAR(20), gst_registered BOOLEAN DEFAULT FALSE, gst_no VARCHAR(20), withholding_tax_applicable BOOLEAN DEFAULT FALSE, withholding_tax_rate NUMERIC(5,2), contact_person VARCHAR(100), email VARCHAR(100), phone VARCHAR(20), address_line1 VARCHAR(100), address_line2 VARCHAR(100), postal_code VARCHAR(20), city VARCHAR(50), country VARCHAR(50) DEFAULT 'Singapore', payment_terms INTEGER DEFAULT 30, currency_code CHAR(3) DEFAULT 'SGD', is_active BOOLEAN DEFAULT TRUE, vendor_since DATE, notes TEXT, bank_account_name VARCHAR(100), bank_account_number VARCHAR(50), bank_name VARCHAR(100), bank_branch VARCHAR(100), bank_swift_code VARCHAR(20), payables_account_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_vendors_name ON business.vendors(name); CREATE INDEX idx_vendors_is_active ON business.vendors(is_active);
CREATE TABLE business.products (id SERIAL PRIMARY KEY, product_code VARCHAR(20) NOT NULL UNIQUE, name VARCHAR(100) NOT NULL, description TEXT, product_type VARCHAR(20) NOT NULL CHECK (product_type IN ('Inventory', 'Service', 'Non-Inventory')), category VARCHAR(50), unit_of_measure VARCHAR(20), barcode VARCHAR(50), sales_price NUMERIC(15,2), purchase_price NUMERIC(15,2), sales_account_id INTEGER, purchase_account_id INTEGER, inventory_account_id INTEGER, tax_code VARCHAR(20), is_active BOOLEAN DEFAULT TRUE, min_stock_level NUMERIC(15,2), reorder_point NUMERIC(15,2), created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_products_name ON business.products(name); CREATE INDEX idx_products_is_active ON business.products(is_active); CREATE INDEX idx_products_type ON business.products(product_type);
CREATE TABLE business.inventory_movements (id SERIAL PRIMARY KEY, product_id INTEGER NOT NULL, movement_date DATE NOT NULL, movement_type VARCHAR(20) NOT NULL CHECK (movement_type IN ('Purchase', 'Sale', 'Adjustment', 'Transfer', 'Return', 'Opening')), quantity NUMERIC(15,2) NOT NULL, unit_cost NUMERIC(15,4), total_cost NUMERIC(15,2), reference_type VARCHAR(50), reference_id INTEGER, notes TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL);
CREATE INDEX idx_inventory_movements_product ON business.inventory_movements(product_id, movement_date); CREATE INDEX idx_inventory_movements_reference ON business.inventory_movements(reference_type, reference_id);
CREATE TABLE business.sales_invoices (id SERIAL PRIMARY KEY, invoice_no VARCHAR(20) NOT NULL UNIQUE, customer_id INTEGER NOT NULL, invoice_date DATE NOT NULL, due_date DATE NOT NULL, currency_code CHAR(3) NOT NULL, exchange_rate NUMERIC(15,6) DEFAULT 1, subtotal NUMERIC(15,2) NOT NULL, tax_amount NUMERIC(15,2) NOT NULL DEFAULT 0, total_amount NUMERIC(15,2) NOT NULL, amount_paid NUMERIC(15,2) NOT NULL DEFAULT 0, status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Approved', 'Sent', 'Partially Paid', 'Paid', 'Overdue', 'Voided')), notes TEXT, terms_and_conditions TEXT, journal_entry_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_sales_invoices_customer ON business.sales_invoices(customer_id); CREATE INDEX idx_sales_invoices_dates ON business.sales_invoices(invoice_date, due_date); CREATE INDEX idx_sales_invoices_status ON business.sales_invoices(status);
CREATE TABLE business.sales_invoice_lines (id SERIAL PRIMARY KEY, invoice_id INTEGER NOT NULL, line_number INTEGER NOT NULL, product_id INTEGER, description VARCHAR(200) NOT NULL, quantity NUMERIC(15,2) NOT NULL, unit_price NUMERIC(15,2) NOT NULL, discount_percent NUMERIC(5,2) DEFAULT 0, discount_amount NUMERIC(15,2) DEFAULT 0, line_subtotal NUMERIC(15,2) NOT NULL, tax_code VARCHAR(20), tax_amount NUMERIC(15,2) DEFAULT 0, line_total NUMERIC(15,2) NOT NULL, dimension1_id INTEGER, dimension2_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_sales_invoice_lines_invoice ON business.sales_invoice_lines(invoice_id); CREATE INDEX idx_sales_invoice_lines_product ON business.sales_invoice_lines(product_id);
CREATE TABLE business.purchase_invoices (id SERIAL PRIMARY KEY, invoice_no VARCHAR(20) NOT NULL UNIQUE, vendor_id INTEGER NOT NULL, vendor_invoice_no VARCHAR(50), invoice_date DATE NOT NULL, due_date DATE NOT NULL, currency_code CHAR(3) NOT NULL, exchange_rate NUMERIC(15,6) DEFAULT 1, subtotal NUMERIC(15,2) NOT NULL, tax_amount NUMERIC(15,2) NOT NULL DEFAULT 0, total_amount NUMERIC(15,2) NOT NULL, amount_paid NUMERIC(15,2) NOT NULL DEFAULT 0, status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Approved', 'Partially Paid', 'Paid', 'Overdue', 'Disputed', 'Voided')), notes TEXT, journal_entry_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_purchase_invoices_vendor ON business.purchase_invoices(vendor_id); CREATE INDEX idx_purchase_invoices_dates ON business.purchase_invoices(invoice_date, due_date); CREATE INDEX idx_purchase_invoices_status ON business.purchase_invoices(status);
CREATE TABLE business.purchase_invoice_lines (id SERIAL PRIMARY KEY, invoice_id INTEGER NOT NULL, line_number INTEGER NOT NULL, product_id INTEGER, description VARCHAR(200) NOT NULL, quantity NUMERIC(15,2) NOT NULL, unit_price NUMERIC(15,2) NOT NULL, discount_percent NUMERIC(5,2) DEFAULT 0, discount_amount NUMERIC(15,2) DEFAULT 0, line_subtotal NUMERIC(15,2) NOT NULL, tax_code VARCHAR(20), tax_amount NUMERIC(15,2) DEFAULT 0, line_total NUMERIC(15,2) NOT NULL, dimension1_id INTEGER, dimension2_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_purchase_invoice_lines_invoice ON business.purchase_invoice_lines(invoice_id); CREATE INDEX idx_purchase_invoice_lines_product ON business.purchase_invoice_lines(product_id);

-- Updated business.bank_accounts table
CREATE TABLE business.bank_accounts (
    id SERIAL PRIMARY KEY, account_name VARCHAR(100) NOT NULL, account_number VARCHAR(50) NOT NULL, 
    bank_name VARCHAR(100) NOT NULL, bank_branch VARCHAR(100), bank_swift_code VARCHAR(20), 
    currency_code CHAR(3) NOT NULL, opening_balance NUMERIC(15,2) DEFAULT 0, 
    current_balance NUMERIC(15,2) DEFAULT 0, last_reconciled_date DATE, 
    last_reconciled_balance NUMERIC(15,2) NULL, -- New column
    gl_account_id INTEGER NOT NULL, is_active BOOLEAN DEFAULT TRUE, description TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
    created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL
);

-- Updated business.bank_transactions table
CREATE TABLE business.bank_transactions (
    id SERIAL PRIMARY KEY, 
    bank_account_id INTEGER NOT NULL, 
    transaction_date DATE NOT NULL, 
    value_date DATE, 
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Interest', 'Fee', 'Adjustment')), 
    description VARCHAR(200) NOT NULL, 
    reference VARCHAR(100), 
    amount NUMERIC(15,2) NOT NULL, 
    is_reconciled BOOLEAN DEFAULT FALSE NOT NULL, 
    reconciled_date DATE, 
    statement_date DATE, 
    statement_id VARCHAR(50), 
    is_from_statement BOOLEAN NOT NULL DEFAULT FALSE, 
    raw_statement_data JSONB NULL, 
    reconciled_bank_reconciliation_id INT NULL, -- New column
    journal_entry_id INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
    created_by INTEGER NOT NULL, 
    updated_by INTEGER NOT NULL
);
CREATE INDEX idx_bank_transactions_account ON business.bank_transactions(bank_account_id); 
CREATE INDEX idx_bank_transactions_date ON business.bank_transactions(transaction_date); 
CREATE INDEX idx_bank_transactions_reconciled ON business.bank_transactions(is_reconciled);

-- ... (payments, payment_allocations - unchanged) ...
CREATE TABLE business.payments (id SERIAL PRIMARY KEY, payment_no VARCHAR(20) NOT NULL UNIQUE, payment_type VARCHAR(20) NOT NULL CHECK (payment_type IN ('Customer Payment', 'Vendor Payment', 'Refund', 'Credit Note', 'Other')), payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('Cash', 'Check', 'Bank Transfer', 'Credit Card', 'GIRO', 'PayNow', 'Other')), payment_date DATE NOT NULL, entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('Customer', 'Vendor', 'Other')), entity_id INTEGER NOT NULL, bank_account_id INTEGER, currency_code CHAR(3) NOT NULL, exchange_rate NUMERIC(15,6) DEFAULT 1, amount NUMERIC(15,2) NOT NULL, reference VARCHAR(100), description TEXT, cheque_no VARCHAR(50), status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Approved', 'Completed', 'Voided', 'Returned')), journal_entry_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_payments_date ON business.payments(payment_date); CREATE INDEX idx_payments_entity ON business.payments(entity_type, entity_id); CREATE INDEX idx_payments_status ON business.payments(status);
CREATE TABLE business.payment_allocations (id SERIAL PRIMARY KEY, payment_id INTEGER NOT NULL, document_type VARCHAR(20) NOT NULL CHECK (document_type IN ('Sales Invoice', 'Purchase Invoice', 'Credit Note', 'Debit Note', 'Other')), document_id INTEGER NOT NULL, amount NUMERIC(15,2) NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL);
CREATE INDEX idx_payment_allocations_payment ON business.payment_allocations(payment_id); CREATE INDEX idx_payment_allocations_document ON business.payment_allocations(document_type, document_id);

-- New table business.bank_reconciliations
CREATE TABLE business.bank_reconciliations (
    id SERIAL PRIMARY KEY,
    bank_account_id INTEGER NOT NULL,
    statement_date DATE NOT NULL,
    statement_ending_balance NUMERIC(15,2) NOT NULL,
    calculated_book_balance NUMERIC(15,2) NOT NULL,
    reconciled_difference NUMERIC(15,2) NOT NULL,
    reconciliation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER NOT NULL,
    CONSTRAINT uq_bank_reconciliation_account_statement_date UNIQUE (bank_account_id, statement_date)
);

-- ============================================================================
-- AUDIT SCHEMA TABLES (Unchanged)
-- ============================================================================
CREATE TABLE audit.audit_log (id SERIAL PRIMARY KEY, user_id INTEGER, action VARCHAR(50) NOT NULL, entity_type VARCHAR(50) NOT NULL, entity_id INTEGER, entity_name VARCHAR(200), changes JSONB, ip_address VARCHAR(45), user_agent VARCHAR(255), timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_audit_log_user ON audit.audit_log(user_id); CREATE INDEX idx_audit_log_entity ON audit.audit_log(entity_type, entity_id); CREATE INDEX idx_audit_log_timestamp ON audit.audit_log(timestamp);
CREATE TABLE audit.data_change_history (id SERIAL PRIMARY KEY, table_name VARCHAR(100) NOT NULL, record_id INTEGER NOT NULL, field_name VARCHAR(100) NOT NULL, old_value TEXT, new_value TEXT, change_type VARCHAR(20) NOT NULL CHECK (change_type IN ('Insert', 'Update', 'Delete')), changed_by INTEGER, changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_data_change_history_table_record ON audit.data_change_history(table_name, record_id); CREATE INDEX idx_data_change_history_changed_at ON audit.data_change_history(changed_at);

-- ============================================================================
-- ADDING FOREIGN KEY CONSTRAINTS 
-- ============================================================================
-- ... (Core, Accounting FKs - unchanged) ...
ALTER TABLE core.role_permissions ADD CONSTRAINT fk_rp_role FOREIGN KEY (role_id) REFERENCES core.roles(id) ON DELETE CASCADE;
ALTER TABLE core.role_permissions ADD CONSTRAINT fk_rp_permission FOREIGN KEY (permission_id) REFERENCES core.permissions(id) ON DELETE CASCADE;
ALTER TABLE core.user_roles ADD CONSTRAINT fk_ur_user FOREIGN KEY (user_id) REFERENCES core.users(id) ON DELETE CASCADE;
ALTER TABLE core.user_roles ADD CONSTRAINT fk_ur_role FOREIGN KEY (role_id) REFERENCES core.roles(id) ON DELETE CASCADE;
ALTER TABLE core.company_settings ADD CONSTRAINT fk_cs_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE core.company_settings ADD CONSTRAINT fk_cs_base_currency FOREIGN KEY (base_currency) REFERENCES accounting.currencies(code);
ALTER TABLE core.configuration ADD CONSTRAINT fk_cfg_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE accounting.accounts ADD CONSTRAINT fk_acc_parent FOREIGN KEY (parent_id) REFERENCES accounting.accounts(id);
ALTER TABLE accounting.accounts ADD CONSTRAINT fk_acc_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.accounts ADD CONSTRAINT fk_acc_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE accounting.fiscal_years ADD CONSTRAINT fk_fy_closed_by FOREIGN KEY (closed_by) REFERENCES core.users(id);
ALTER TABLE accounting.fiscal_years ADD CONSTRAINT fk_fy_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.fiscal_years ADD CONSTRAINT fk_fy_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE accounting.fiscal_periods ADD CONSTRAINT fk_fp_fiscal_year FOREIGN KEY (fiscal_year_id) REFERENCES accounting.fiscal_years(id);
ALTER TABLE accounting.fiscal_periods ADD CONSTRAINT fk_fp_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.fiscal_periods ADD CONSTRAINT fk_fp_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE accounting.currencies ADD CONSTRAINT fk_curr_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.currencies ADD CONSTRAINT fk_curr_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE accounting.exchange_rates ADD CONSTRAINT fk_er_from_curr FOREIGN KEY (from_currency) REFERENCES accounting.currencies(code);
ALTER TABLE accounting.exchange_rates ADD CONSTRAINT fk_er_to_curr FOREIGN KEY (to_currency) REFERENCES accounting.currencies(code);
ALTER TABLE accounting.exchange_rates ADD CONSTRAINT fk_er_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.exchange_rates ADD CONSTRAINT fk_er_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_je_fiscal_period FOREIGN KEY (fiscal_period_id) REFERENCES accounting.fiscal_periods(id);
ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_je_reversing_entry FOREIGN KEY (reversing_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_je_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_je_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_je_recurring_pattern FOREIGN KEY (recurring_pattern_id) REFERENCES accounting.recurring_patterns(id) DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE accounting.journal_entry_lines ADD CONSTRAINT fk_jel_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id) ON DELETE CASCADE;
ALTER TABLE accounting.journal_entry_lines ADD CONSTRAINT fk_jel_account FOREIGN KEY (account_id) REFERENCES accounting.accounts(id);
ALTER TABLE accounting.journal_entry_lines ADD CONSTRAINT fk_jel_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE accounting.journal_entry_lines ADD CONSTRAINT fk_jel_tax_code FOREIGN KEY (tax_code) REFERENCES accounting.tax_codes(code);
ALTER TABLE accounting.journal_entry_lines ADD CONSTRAINT fk_jel_dimension1 FOREIGN KEY (dimension1_id) REFERENCES accounting.dimensions(id);
ALTER TABLE accounting.journal_entry_lines ADD CONSTRAINT fk_jel_dimension2 FOREIGN KEY (dimension2_id) REFERENCES accounting.dimensions(id);
ALTER TABLE accounting.recurring_patterns ADD CONSTRAINT fk_rp_template_entry FOREIGN KEY (template_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE accounting.recurring_patterns ADD CONSTRAINT fk_rp_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.recurring_patterns ADD CONSTRAINT fk_rp_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE accounting.dimensions ADD CONSTRAINT fk_dim_parent FOREIGN KEY (parent_id) REFERENCES accounting.dimensions(id);
ALTER TABLE accounting.dimensions ADD CONSTRAINT fk_dim_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.dimensions ADD CONSTRAINT fk_dim_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE accounting.budgets ADD CONSTRAINT fk_bud_fiscal_year FOREIGN KEY (fiscal_year_id) REFERENCES accounting.fiscal_years(id);
ALTER TABLE accounting.budgets ADD CONSTRAINT fk_bud_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.budgets ADD CONSTRAINT fk_bud_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE accounting.budget_details ADD CONSTRAINT fk_bd_budget FOREIGN KEY (budget_id) REFERENCES accounting.budgets(id) ON DELETE CASCADE;
ALTER TABLE accounting.budget_details ADD CONSTRAINT fk_bd_account FOREIGN KEY (account_id) REFERENCES accounting.accounts(id);
ALTER TABLE accounting.budget_details ADD CONSTRAINT fk_bd_fiscal_period FOREIGN KEY (fiscal_period_id) REFERENCES accounting.fiscal_periods(id);
ALTER TABLE accounting.budget_details ADD CONSTRAINT fk_bd_dimension1 FOREIGN KEY (dimension1_id) REFERENCES accounting.dimensions(id);
ALTER TABLE accounting.budget_details ADD CONSTRAINT fk_bd_dimension2 FOREIGN KEY (dimension2_id) REFERENCES accounting.dimensions(id);
ALTER TABLE accounting.budget_details ADD CONSTRAINT fk_bd_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.budget_details ADD CONSTRAINT fk_bd_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE accounting.tax_codes ADD CONSTRAINT fk_tc_affects_account FOREIGN KEY (affects_account_id) REFERENCES accounting.accounts(id);
ALTER TABLE accounting.tax_codes ADD CONSTRAINT fk_tc_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.tax_codes ADD CONSTRAINT fk_tc_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE accounting.gst_returns ADD CONSTRAINT fk_gstr_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE accounting.gst_returns ADD CONSTRAINT fk_gstr_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.gst_returns ADD CONSTRAINT fk_gstr_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE accounting.withholding_tax_certificates ADD CONSTRAINT fk_whtc_vendor FOREIGN KEY (vendor_id) REFERENCES business.vendors(id);
ALTER TABLE accounting.withholding_tax_certificates ADD CONSTRAINT fk_whtc_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE accounting.withholding_tax_certificates ADD CONSTRAINT fk_whtc_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE accounting.withholding_tax_certificates ADD CONSTRAINT fk_whtc_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

-- Business Schema FKs (existing ones unchanged)
-- ... (customers, vendors, products, inventory_movements, sales_invoices, sales_invoice_lines, purchase_invoices, purchase_invoice_lines, bank_accounts, existing bank_transactions FKs, payments, payment_allocations - unchanged) ...
ALTER TABLE business.customers ADD CONSTRAINT fk_cust_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE business.customers ADD CONSTRAINT fk_cust_receivables_acc FOREIGN KEY (receivables_account_id) REFERENCES accounting.accounts(id);
ALTER TABLE business.customers ADD CONSTRAINT fk_cust_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.customers ADD CONSTRAINT fk_cust_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE business.vendors ADD CONSTRAINT fk_vend_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE business.vendors ADD CONSTRAINT fk_vend_payables_acc FOREIGN KEY (payables_account_id) REFERENCES accounting.accounts(id);
ALTER TABLE business.vendors ADD CONSTRAINT fk_vend_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.vendors ADD CONSTRAINT fk_vend_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE business.products ADD CONSTRAINT fk_prod_sales_acc FOREIGN KEY (sales_account_id) REFERENCES accounting.accounts(id);
ALTER TABLE business.products ADD CONSTRAINT fk_prod_purchase_acc FOREIGN KEY (purchase_account_id) REFERENCES accounting.accounts(id);
ALTER TABLE business.products ADD CONSTRAINT fk_prod_inventory_acc FOREIGN KEY (inventory_account_id) REFERENCES accounting.accounts(id);
ALTER TABLE business.products ADD CONSTRAINT fk_prod_tax_code FOREIGN KEY (tax_code) REFERENCES accounting.tax_codes(code);
ALTER TABLE business.products ADD CONSTRAINT fk_prod_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.products ADD CONSTRAINT fk_prod_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE business.inventory_movements ADD CONSTRAINT fk_im_product FOREIGN KEY (product_id) REFERENCES business.products(id);
ALTER TABLE business.inventory_movements ADD CONSTRAINT fk_im_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.sales_invoices ADD CONSTRAINT fk_si_customer FOREIGN KEY (customer_id) REFERENCES business.customers(id);
ALTER TABLE business.sales_invoices ADD CONSTRAINT fk_si_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE business.sales_invoices ADD CONSTRAINT fk_si_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE business.sales_invoices ADD CONSTRAINT fk_si_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.sales_invoices ADD CONSTRAINT fk_si_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE business.sales_invoice_lines ADD CONSTRAINT fk_sil_invoice FOREIGN KEY (invoice_id) REFERENCES business.sales_invoices(id) ON DELETE CASCADE;
ALTER TABLE business.sales_invoice_lines ADD CONSTRAINT fk_sil_product FOREIGN KEY (product_id) REFERENCES business.products(id);
ALTER TABLE business.sales_invoice_lines ADD CONSTRAINT fk_sil_tax_code FOREIGN KEY (tax_code) REFERENCES accounting.tax_codes(code);
ALTER TABLE business.sales_invoice_lines ADD CONSTRAINT fk_sil_dimension1 FOREIGN KEY (dimension1_id) REFERENCES accounting.dimensions(id);
ALTER TABLE business.sales_invoice_lines ADD CONSTRAINT fk_sil_dimension2 FOREIGN KEY (dimension2_id) REFERENCES accounting.dimensions(id);
ALTER TABLE business.purchase_invoices ADD CONSTRAINT fk_pi_vendor FOREIGN KEY (vendor_id) REFERENCES business.vendors(id);
ALTER TABLE business.purchase_invoices ADD CONSTRAINT fk_pi_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE business.purchase_invoices ADD CONSTRAINT fk_pi_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE business.purchase_invoices ADD CONSTRAINT fk_pi_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.purchase_invoices ADD CONSTRAINT fk_pi_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE business.purchase_invoice_lines ADD CONSTRAINT fk_pil_invoice FOREIGN KEY (invoice_id) REFERENCES business.purchase_invoices(id) ON DELETE CASCADE;
ALTER TABLE business.purchase_invoice_lines ADD CONSTRAINT fk_pil_product FOREIGN KEY (product_id) REFERENCES business.products(id);
ALTER TABLE business.purchase_invoice_lines ADD CONSTRAINT fk_pil_tax_code FOREIGN KEY (tax_code) REFERENCES accounting.tax_codes(code);
ALTER TABLE business.purchase_invoice_lines ADD CONSTRAINT fk_pil_dimension1 FOREIGN KEY (dimension1_id) REFERENCES accounting.dimensions(id);
ALTER TABLE business.purchase_invoice_lines ADD CONSTRAINT fk_pil_dimension2 FOREIGN KEY (dimension2_id) REFERENCES accounting.dimensions(id);
ALTER TABLE business.bank_accounts ADD CONSTRAINT fk_ba_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE business.bank_accounts ADD CONSTRAINT fk_ba_gl_account FOREIGN KEY (gl_account_id) REFERENCES accounting.accounts(id);
ALTER TABLE business.bank_accounts ADD CONSTRAINT fk_ba_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.bank_accounts ADD CONSTRAINT fk_ba_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id);
ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE business.payment_allocations ADD CONSTRAINT fk_pa_payment FOREIGN KEY (payment_id) REFERENCES business.payments(id) ON DELETE CASCADE;
ALTER TABLE business.payment_allocations ADD CONSTRAINT fk_pa_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);

-- New FKs for bank_reconciliations and bank_transactions reconciliation link
ALTER TABLE business.bank_reconciliations 
    ADD CONSTRAINT fk_br_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id),
    ADD CONSTRAINT fk_br_created_by FOREIGN KEY (created_by_user_id) REFERENCES core.users(id);

ALTER TABLE business.bank_transactions
    ADD CONSTRAINT fk_bt_reconciliation FOREIGN KEY (reconciled_bank_reconciliation_id) REFERENCES business.bank_reconciliations(id);

-- Audit Schema FKs (Unchanged)
ALTER TABLE audit.audit_log ADD CONSTRAINT fk_al_user FOREIGN KEY (user_id) REFERENCES core.users(id);
ALTER TABLE audit.data_change_history ADD CONSTRAINT fk_dch_changed_by FOREIGN KEY (changed_by) REFERENCES core.users(id);

-- ============================================================================
-- VIEWS (Unchanged - except trial_balance which was already corrected)
-- ============================================================================
-- ... (account_balances, trial_balance, customer_balances, vendor_balances, inventory_summary - unchanged from response_22 which had corrected trial_balance) ...
CREATE OR REPLACE VIEW accounting.account_balances AS SELECT a.id AS account_id, a.code AS account_code, a.name AS account_name, a.account_type, a.parent_id, COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) + a.opening_balance AS balance, COALESCE(SUM(jel.debit_amount), 0) AS total_debits_activity, COALESCE(SUM(jel.credit_amount), 0) AS total_credits_activity, MAX(je.entry_date) AS last_activity_date FROM accounting.accounts a LEFT JOIN accounting.journal_entry_lines jel ON a.id = jel.account_id LEFT JOIN accounting.journal_entries je ON jel.journal_entry_id = je.id AND je.is_posted = TRUE GROUP BY a.id, a.code, a.name, a.account_type, a.parent_id, a.opening_balance;
CREATE OR REPLACE VIEW accounting.trial_balance AS SELECT a.id AS account_id, a.code AS account_code, a.name AS account_name, a.account_type, a.sub_type, CASE WHEN ab.balance > 0 THEN ab.balance ELSE 0 END AS debit_balance, CASE WHEN ab.balance < 0 THEN -ab.balance ELSE 0 END AS credit_balance FROM accounting.accounts a JOIN accounting.account_balances ab ON a.id = ab.account_id WHERE a.is_active = TRUE AND ab.balance != 0;
CREATE OR REPLACE VIEW business.customer_balances AS SELECT c.id AS customer_id, c.customer_code, c.name AS customer_name, COALESCE(SUM(si.total_amount - si.amount_paid), 0) AS outstanding_balance, COALESCE(SUM(CASE WHEN si.due_date < CURRENT_DATE AND si.status NOT IN ('Paid', 'Voided') THEN si.total_amount - si.amount_paid ELSE 0 END), 0) AS overdue_amount, COALESCE(SUM(CASE WHEN si.status = 'Draft' THEN si.total_amount ELSE 0 END), 0) AS draft_amount, COALESCE(MAX(si.due_date), NULL) AS latest_due_date FROM business.customers c LEFT JOIN business.sales_invoices si ON c.id = si.customer_id AND si.status NOT IN ('Paid', 'Voided') GROUP BY c.id, c.customer_code, c.name;
CREATE OR REPLACE VIEW business.vendor_balances AS SELECT v.id AS vendor_id, v.vendor_code, v.name AS vendor_name, COALESCE(SUM(pi.total_amount - pi.amount_paid), 0) AS outstanding_balance, COALESCE(SUM(CASE WHEN pi.due_date < CURRENT_DATE AND pi.status NOT IN ('Paid', 'Voided') THEN pi.total_amount - pi.amount_paid ELSE 0 END), 0) AS overdue_amount, COALESCE(SUM(CASE WHEN pi.status = 'Draft' THEN pi.total_amount ELSE 0 END), 0) AS draft_amount, COALESCE(MAX(pi.due_date), NULL) AS latest_due_date FROM business.vendors v LEFT JOIN business.purchase_invoices pi ON v.id = pi.vendor_id AND pi.status NOT IN ('Paid', 'Voided') GROUP BY v.id, v.vendor_code, v.name;
CREATE OR REPLACE VIEW business.inventory_summary AS SELECT p.id AS product_id, p.product_code, p.name AS product_name, p.product_type, p.category, p.unit_of_measure, COALESCE(SUM(im.quantity), 0) AS current_quantity, CASE WHEN COALESCE(SUM(im.quantity), 0) != 0 THEN (COALESCE(SUM(im.total_cost), 0) / SUM(im.quantity)) ELSE p.purchase_price END AS average_cost, COALESCE(SUM(im.total_cost), 0) AS inventory_value, p.sales_price AS current_sales_price, p.min_stock_level, p.reorder_point, CASE WHEN p.min_stock_level IS NOT NULL AND COALESCE(SUM(im.quantity), 0) <= p.min_stock_level THEN TRUE ELSE FALSE END AS below_minimum, CASE WHEN p.reorder_point IS NOT NULL AND COALESCE(SUM(im.quantity), 0) <= p.reorder_point THEN TRUE ELSE FALSE END AS reorder_needed FROM business.products p LEFT JOIN business.inventory_movements im ON p.id = im.product_id WHERE p.product_type = 'Inventory' AND p.is_active = TRUE GROUP BY p.id, p.product_code, p.name, p.product_type, p.category, p.unit_of_measure, p.purchase_price, p.sales_price, p.min_stock_level, p.reorder_point;

-- ============================================================================
-- FUNCTIONS (Unchanged)
-- ============================================================================
-- ... (core.get_next_sequence_value, accounting.generate_journal_entry, accounting.post_journal_entry, accounting.calculate_account_balance, core.update_timestamp_trigger_func, audit.log_data_change_trigger_func, business.update_bank_account_balance_trigger_func - unchanged from response_22) ...
CREATE OR REPLACE FUNCTION core.get_next_sequence_value(p_sequence_name VARCHAR) RETURNS VARCHAR AS $$ DECLARE v_sequence RECORD; v_next_value INTEGER; v_result VARCHAR; BEGIN SELECT * INTO v_sequence FROM core.sequences WHERE sequence_name = p_sequence_name FOR UPDATE; IF NOT FOUND THEN RAISE EXCEPTION 'Sequence % not found', p_sequence_name; END IF; v_next_value := v_sequence.next_value; UPDATE core.sequences SET next_value = next_value + increment_by, updated_at = CURRENT_TIMESTAMP WHERE sequence_name = p_sequence_name; v_result := v_sequence.format_template; v_result := REPLACE(v_result, '{PREFIX}', COALESCE(v_sequence.prefix, '')); v_result := REPLACE(v_result, '{VALUE}', LPAD(v_next_value::TEXT, 6, '0')); v_result := REPLACE(v_result, '{SUFFIX}', COALESCE(v_sequence.suffix, '')); RETURN v_result; END; $$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION accounting.generate_journal_entry(p_journal_type VARCHAR, p_entry_date DATE, p_description VARCHAR, p_reference VARCHAR, p_source_type VARCHAR, p_source_id INTEGER, p_lines JSONB, p_user_id INTEGER) RETURNS INTEGER AS $$ DECLARE v_fiscal_period_id INTEGER; v_entry_no VARCHAR; v_journal_id INTEGER; v_line JSONB; v_line_number INTEGER := 1; v_total_debits NUMERIC(15,2) := 0; v_total_credits NUMERIC(15,2) := 0; BEGIN SELECT id INTO v_fiscal_period_id FROM accounting.fiscal_periods WHERE p_entry_date BETWEEN start_date AND end_date AND status = 'Open'; IF v_fiscal_period_id IS NULL THEN RAISE EXCEPTION 'No open fiscal period found for date %', p_entry_date; END IF; v_entry_no := core.get_next_sequence_value('journal_entry'); INSERT INTO accounting.journal_entries (entry_no, journal_type, entry_date, fiscal_period_id, description, reference, is_posted, source_type, source_id, created_by, updated_by) VALUES (v_entry_no, p_journal_type, p_entry_date, v_fiscal_period_id, p_description, p_reference, FALSE, p_source_type, p_source_id, p_user_id, p_user_id) RETURNING id INTO v_journal_id; FOR v_line IN SELECT * FROM jsonb_array_elements(p_lines) LOOP INSERT INTO accounting.journal_entry_lines (journal_entry_id, line_number, account_id, description, debit_amount, credit_amount, currency_code, exchange_rate, tax_code, tax_amount, dimension1_id, dimension2_id) VALUES (v_journal_id, v_line_number, (v_line->>'account_id')::INTEGER, v_line->>'description', COALESCE((v_line->>'debit_amount')::NUMERIC, 0), COALESCE((v_line->>'credit_amount')::NUMERIC, 0), COALESCE(v_line->>'currency_code', 'SGD'), COALESCE((v_line->>'exchange_rate')::NUMERIC, 1), v_line->>'tax_code', COALESCE((v_line->>'tax_amount')::NUMERIC, 0), NULLIF(TRIM(v_line->>'dimension1_id'), '')::INTEGER, NULLIF(TRIM(v_line->>'dimension2_id'), '')::INTEGER); v_line_number := v_line_number + 1; v_total_debits := v_total_debits + COALESCE((v_line->>'debit_amount')::NUMERIC, 0); v_total_credits := v_total_credits + COALESCE((v_line->>'credit_amount')::NUMERIC, 0); END LOOP; IF round(v_total_debits, 2) != round(v_total_credits, 2) THEN RAISE EXCEPTION 'Journal entry is not balanced. Debits: %, Credits: %', v_total_debits, v_total_credits; END IF; RETURN v_journal_id; END; $$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION accounting.post_journal_entry(p_journal_id INTEGER, p_user_id INTEGER) RETURNS BOOLEAN AS $$ DECLARE v_fiscal_period_status VARCHAR; v_is_already_posted BOOLEAN; BEGIN SELECT is_posted INTO v_is_already_posted FROM accounting.journal_entries WHERE id = p_journal_id; IF v_is_already_posted THEN RAISE EXCEPTION 'Journal entry % is already posted', p_journal_id; END IF; SELECT fp.status INTO v_fiscal_period_status FROM accounting.journal_entries je JOIN accounting.fiscal_periods fp ON je.fiscal_period_id = fp.id WHERE je.id = p_journal_id; IF v_fiscal_period_status != 'Open' THEN RAISE EXCEPTION 'Cannot post to a closed or archived fiscal period'; END IF; UPDATE accounting.journal_entries SET is_posted = TRUE, updated_at = CURRENT_TIMESTAMP, updated_by = p_user_id WHERE id = p_journal_id; RETURN TRUE; END; $$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION accounting.calculate_account_balance(p_account_id INTEGER, p_as_of_date DATE) RETURNS NUMERIC AS $$ DECLARE v_balance NUMERIC(15,2) := 0; v_opening_balance NUMERIC(15,2); v_account_opening_balance_date DATE; BEGIN SELECT acc.opening_balance, acc.opening_balance_date INTO v_opening_balance, v_account_opening_balance_date FROM accounting.accounts acc WHERE acc.id = p_account_id; IF NOT FOUND THEN RAISE EXCEPTION 'Account with ID % not found', p_account_id; END IF; SELECT COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) INTO v_balance FROM accounting.journal_entry_lines jel JOIN accounting.journal_entries je ON jel.journal_entry_id = je.id WHERE jel.account_id = p_account_id AND je.is_posted = TRUE AND je.entry_date <= p_as_of_date AND (v_account_opening_balance_date IS NULL OR je.entry_date >= v_account_opening_balance_date); v_balance := v_balance + COALESCE(v_opening_balance, 0); RETURN v_balance; END; $$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION core.update_timestamp_trigger_func() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = CURRENT_TIMESTAMP; RETURN NEW; END; $$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION audit.log_data_change_trigger_func() RETURNS TRIGGER AS $$ DECLARE v_old_data JSONB; v_new_data JSONB; v_change_type VARCHAR(20); v_user_id INTEGER; v_entity_id INTEGER; v_entity_name VARCHAR(200); temp_val TEXT; current_field_name_from_json TEXT; BEGIN BEGIN v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER; EXCEPTION WHEN OTHERS THEN v_user_id := NULL; END; IF v_user_id IS NULL THEN IF TG_OP = 'INSERT' THEN BEGIN v_user_id := NEW.created_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END; ELSIF TG_OP = 'UPDATE' THEN BEGIN v_user_id := NEW.updated_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END; END IF; END IF; IF TG_TABLE_SCHEMA = 'audit' AND TG_TABLE_NAME IN ('audit_log', 'data_change_history') THEN RETURN NULL; END IF; IF TG_OP = 'INSERT' THEN v_change_type := 'Insert'; v_old_data := NULL; v_new_data := to_jsonb(NEW); ELSIF TG_OP = 'UPDATE' THEN v_change_type := 'Update'; v_old_data := to_jsonb(OLD); v_new_data := to_jsonb(NEW); ELSIF TG_OP = 'DELETE' THEN v_change_type := 'Delete'; v_old_data := to_jsonb(OLD); v_new_data := NULL; END IF; BEGIN IF TG_OP = 'DELETE' THEN v_entity_id := OLD.id; ELSE v_entity_id := NEW.id; END IF; EXCEPTION WHEN undefined_column THEN v_entity_id := NULL; END; BEGIN IF TG_OP = 'DELETE' THEN temp_val := CASE WHEN TG_TABLE_NAME IN ('accounts','customers','vendors','products','roles','account_types','dimensions','fiscal_years','budgets') THEN OLD.name WHEN TG_TABLE_NAME = 'journal_entries' THEN OLD.entry_no WHEN TG_TABLE_NAME = 'sales_invoices' THEN OLD.invoice_no WHEN TG_TABLE_NAME = 'purchase_invoices' THEN OLD.invoice_no WHEN TG_TABLE_NAME = 'payments' THEN OLD.payment_no WHEN TG_TABLE_NAME = 'users' THEN OLD.username WHEN TG_TABLE_NAME = 'tax_codes' THEN OLD.code WHEN TG_TABLE_NAME = 'gst_returns' THEN OLD.return_period ELSE OLD.id::TEXT END; ELSE temp_val := CASE WHEN TG_TABLE_NAME IN ('accounts','customers','vendors','products','roles','account_types','dimensions','fiscal_years','budgets') THEN NEW.name WHEN TG_TABLE_NAME = 'journal_entries' THEN NEW.entry_no WHEN TG_TABLE_NAME = 'sales_invoices' THEN NEW.invoice_no WHEN TG_TABLE_NAME = 'purchase_invoices' THEN NEW.invoice_no WHEN TG_TABLE_NAME = 'payments' THEN NEW.payment_no WHEN TG_TABLE_NAME = 'users' THEN NEW.username WHEN TG_TABLE_NAME = 'tax_codes' THEN NEW.code WHEN TG_TABLE_NAME = 'gst_returns' THEN NEW.return_period ELSE NEW.id::TEXT END; END IF; v_entity_name := temp_val; EXCEPTION WHEN undefined_column THEN BEGIN IF TG_OP = 'DELETE' THEN v_entity_name := OLD.id::TEXT; ELSE v_entity_name := NEW.id::TEXT; END IF; EXCEPTION WHEN undefined_column THEN v_entity_name := NULL; END; END; INSERT INTO audit.audit_log (user_id,action,entity_type,entity_id,entity_name,changes,timestamp) VALUES (v_user_id,v_change_type,TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,v_entity_id,v_entity_name,jsonb_build_object('old',v_old_data,'new',v_new_data),CURRENT_TIMESTAMP); IF TG_OP = 'UPDATE' THEN FOR current_field_name_from_json IN SELECT key_alias FROM jsonb_object_keys(v_old_data) AS t(key_alias) LOOP IF (v_new_data ? current_field_name_from_json) AND ((v_old_data -> current_field_name_from_json) IS DISTINCT FROM (v_new_data -> current_field_name_from_json)) THEN INSERT INTO audit.data_change_history (table_name,record_id,field_name,old_value,new_value,change_type,changed_by,changed_at) VALUES (TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,NEW.id,current_field_name_from_json,v_old_data->>current_field_name_from_json,v_new_data->>current_field_name_from_json,'Update',v_user_id,CURRENT_TIMESTAMP); END IF; END LOOP; END IF; RETURN NULL; END; $$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION business.update_bank_account_balance_trigger_func() RETURNS TRIGGER AS $$ BEGIN IF TG_OP = 'INSERT' THEN UPDATE business.bank_accounts SET current_balance = current_balance + NEW.amount WHERE id = NEW.bank_account_id; ELSIF TG_OP = 'DELETE' THEN UPDATE business.bank_accounts SET current_balance = current_balance - OLD.amount WHERE id = OLD.bank_account_id; ELSIF TG_OP = 'UPDATE' THEN IF NEW.bank_account_id != OLD.bank_account_id THEN UPDATE business.bank_accounts SET current_balance = current_balance - OLD.amount WHERE id = OLD.bank_account_id; UPDATE business.bank_accounts SET current_balance = current_balance + NEW.amount WHERE id = NEW.bank_account_id; ELSE UPDATE business.bank_accounts SET current_balance = current_balance - OLD.amount + NEW.amount WHERE id = NEW.bank_account_id; END IF; END IF; RETURN NULL; END; $$ LANGUAGE plpgsql;

-- ============================================================================
-- APPLYING TRIGGERS (Unchanged)
-- ============================================================================
-- ... (Applying trg_update_timestamp, trg_audit_log, trg_update_bank_balance - unchanged from response_22) ...
DO $$ DECLARE r RECORD; BEGIN FOR r IN SELECT table_schema, table_name FROM information_schema.columns WHERE column_name = 'updated_at' AND table_schema IN ('core','accounting','business','audit') GROUP BY table_schema, table_name LOOP EXECUTE format('DROP TRIGGER IF EXISTS trg_update_timestamp ON %I.%I; CREATE TRIGGER trg_update_timestamp BEFORE UPDATE ON %I.%I FOR EACH ROW EXECUTE FUNCTION core.update_timestamp_trigger_func();',r.table_schema,r.table_name,r.table_schema,r.table_name); END LOOP; END; $$;
DO $$ DECLARE tables_to_audit TEXT[] := ARRAY['accounting.accounts','accounting.journal_entries','accounting.fiscal_periods','accounting.fiscal_years','business.customers','business.vendors','business.products','business.sales_invoices','business.purchase_invoices','business.payments','accounting.tax_codes','accounting.gst_returns','core.users','core.roles','core.company_settings', 'business.bank_accounts', 'business.bank_transactions']; table_fullname TEXT; schema_name TEXT; table_name_var TEXT; BEGIN FOREACH table_fullname IN ARRAY tables_to_audit LOOP SELECT split_part(table_fullname,'.',1) INTO schema_name; SELECT split_part(table_fullname,'.',2) INTO table_name_var; EXECUTE format('DROP TRIGGER IF EXISTS trg_audit_log ON %I.%I; CREATE TRIGGER trg_audit_log AFTER INSERT OR UPDATE OR DELETE ON %I.%I FOR EACH ROW EXECUTE FUNCTION audit.log_data_change_trigger_func();',schema_name,table_name_var,schema_name,table_name_var); END LOOP; END; $$;
DROP TRIGGER IF EXISTS trg_update_bank_balance ON business.bank_transactions; CREATE TRIGGER trg_update_bank_balance AFTER INSERT OR UPDATE OR DELETE ON business.bank_transactions FOR EACH ROW EXECUTE FUNCTION business.update_bank_account_balance_trigger_func();

-- End of script

```

---
**2. File: `app/models/business/bank_reconciliation.py` (New File)**
---
**Generated File**: `app/models/business/bank_reconciliation.py`
```python
# File: app/models/business/bank_reconciliation.py
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import datetime
from decimal import Decimal
from typing import Optional, List

from app.models.base import Base, TimestampMixin # UserAuditMixin will be handled by direct FKs for created_by
from app.models.business.bank_account import BankAccount
from app.models.core.user import User
# from app.models.business.bank_transaction import BankTransaction # Needed for back_populates

class BankReconciliation(Base, TimestampMixin):
    __tablename__ = 'bank_reconciliations'
    __table_args__ = (
        UniqueConstraint('bank_account_id', 'statement_date', name='uq_bank_reconciliation_account_statement_date'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_account_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.bank_accounts.id'), nullable=False)
    statement_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    statement_ending_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    calculated_book_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    reconciled_difference: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    reconciliation_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    # updated_by is implicitly handled by TimestampMixin if updated_at is sufficient. 
    # If explicit updated_by is needed, add UserAuditMixin or direct fields. Schema has created_by only.

    # Relationships
    bank_account: Mapped["BankAccount"] = relationship("BankAccount") # back_populates on BankAccount if needed
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    
    # Link to BankTransaction records reconciled by this instance
    reconciled_transactions: Mapped[List["BankTransaction"]] = relationship(
        "BankTransaction", 
        back_populates="reconciliation_instance"
    ) # type: ignore

    def __repr__(self) -> str:
        return f"<BankReconciliation(id={self.id}, bank_account_id={self.bank_account_id}, stmt_date={self.statement_date}, diff={self.reconciled_difference})>"

# Add back_populates to BankAccount and BankTransaction
BankAccount.reconciliations = relationship("BankReconciliation", order_by=BankReconciliation.statement_date.desc(), back_populates="bank_account") # type: ignore

# BankTransaction model needs to be imported here to add the relationship,
# or this relationship definition should be moved to bank_transaction.py to avoid circular imports.
# For now, let's assume BankTransaction will be updated separately or this implies it.
# This is better defined in bank_transaction.py.
# from app.models.business.bank_transaction import BankTransaction
# BankTransaction.reconciliation_instance = relationship("BankReconciliation", back_populates="reconciled_transactions")

```

**3. File: `app/models/business/bank_transaction.py` (Updated)**

**Execution Steps & Checklist for `bank_transaction.py`**:
1.  **[X] Retrieve Base Version**: The version from response_22 (which already includes `is_from_statement` and `raw_statement_data`).
2.  **[X] Add New Field**: `reconciled_bank_reconciliation_id: Mapped[Optional[int]]`.
3.  **[X] Add New Relationship**: `reconciliation_instance: Mapped[Optional["BankReconciliation"]]`.
4.  **[X] Import `BankReconciliation`** (potentially as `TYPE_CHECKING` to avoid circularity if `BankReconciliation` also imports `BankTransaction`).
5.  **[X] Validate**: Correct types, FK, relationship definition. Preservation of other fields.

**Generated File**: `app/models/business/bank_transaction.py`
```python
# File: app/models/business/bank_transaction.py
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB 
from app.models.base import Base, TimestampMixin
from app.models.business.bank_account import BankAccount
from app.models.core.user import User
from app.models.accounting.journal_entry import JournalEntry
# from app.models.business.bank_reconciliation import BankReconciliation # Forward reference if problematic
import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.business.bank_reconciliation import BankReconciliation # For type hint

class BankTransaction(Base, TimestampMixin):
    __tablename__ = 'bank_transactions'
    __table_args__ = (
        CheckConstraint("transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Interest', 'Fee', 'Adjustment')", name='ck_bank_transactions_type'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_account_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.bank_accounts.id'), nullable=False)
    transaction_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    value_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False) 
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False) 
    is_reconciled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reconciled_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    statement_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True) 
    statement_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) 
    is_from_statement: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_statement_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # New field for linking to bank_reconciliations table
    reconciled_bank_reconciliation_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('business.bank_reconciliations.id'), nullable=True)

    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=True)
    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)
    
    # Relationships
    bank_account: Mapped["BankAccount"] = relationship("BankAccount", back_populates="bank_transactions")
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry") 
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
    
    reconciliation_instance: Mapped[Optional["BankReconciliation"]] = relationship(
        "BankReconciliation", 
        back_populates="reconciled_transactions",
        foreign_keys=[reconciled_bank_reconciliation_id]
    )

    def __repr__(self) -> str:
        return f"<BankTransaction(id={self.id}, date={self.transaction_date}, type='{self.transaction_type}', amount={self.amount})>"

```

**4. File: `app/models/business/bank_account.py` (Updated)**

**Execution Steps & Checklist for `bank_account.py`**:
1.  **[X] Retrieve Base Version**: The version from `project_codebase_files_set-5.md`.
2.  **[X] Add New Field**: `last_reconciled_balance: Mapped[Optional[Decimal]]`.
3.  **[X] Add New Relationship**: `reconciliations: Mapped[List["BankReconciliation"]]`.
4.  **[X] Import `BankReconciliation`** (potentially as `TYPE_CHECKING`).
5.  **[X] Validate**: Correct types, relationship definition. Preservation of other fields.

**Generated File**: `app/models/business/bank_account.py`
```python
# File: app/models/business/bank_account.py
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account 
from app.models.accounting.currency import Currency 
from app.models.core.user import User
from typing import List, Optional, TYPE_CHECKING
import datetime
from decimal import Decimal

if TYPE_CHECKING:
    from app.models.business.bank_transaction import BankTransaction # For relationship type hint
    from app.models.business.payment import Payment # For relationship type hint
    from app.models.business.bank_reconciliation import BankReconciliation # New import

class BankAccount(Base, TimestampMixin):
    __tablename__ = 'bank_accounts'
    __table_args__ = {'schema': 'business'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_swift_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), nullable=False)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    current_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    last_reconciled_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    last_reconciled_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True) # New field
    gl_account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    currency: Mapped["Currency"] = relationship("Currency")
    gl_account: Mapped["Account"] = relationship("Account", back_populates="bank_account_links")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
    
    bank_transactions: Mapped[List["BankTransaction"]] = relationship("BankTransaction", back_populates="bank_account") 
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="bank_account") 
    reconciliations: Mapped[List["BankReconciliation"]] = relationship("BankReconciliation", order_by="desc(BankReconciliation.statement_date)", back_populates="bank_account")

# This back_populates was already in the base file for BankAccount, ensuring it's correctly set up.
# Account.bank_account_links = relationship("BankAccount", back_populates="gl_account") 

```

**5. Files: `app/models/__init__.py` and `app/models/business/__init__.py` (Updated)**

**Execution Steps & Checklist**:
1.  **[X] Add `BankReconciliation`** to imports and `__all__` in both files.
2.  **[X] Validate**: Correct imports and `__all__` list.

**Generated File**: `app/models/business/__init__.py`
```python
# File: app/models/business/__init__.py
from .inventory_movement import InventoryMovement
from .sales_invoice import SalesInvoice, SalesInvoiceLine
from .purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine
from .bank_account import BankAccount
from .bank_transaction import BankTransaction
from .payment import Payment, PaymentAllocation
from .bank_reconciliation import BankReconciliation # New Import

__all__ = [
    "InventoryMovement", 
    "SalesInvoice", "SalesInvoiceLine",
    "PurchaseInvoice", "PurchaseInvoiceLine",
    "BankAccount", "BankTransaction",
    "Payment", "PaymentAllocation",
    "BankReconciliation", # New Export
]

```

**Generated File**: `app/models/__init__.py`
```python
# File: app/models/__init__.py
from .base import Base, TimestampMixin, UserAuditMixin

# Core schema models
from .core.user import User, Role, Permission 
from .core.company_setting import CompanySetting
from .core.configuration import Configuration
from .core.sequence import Sequence

# Accounting schema models
from .accounting.account_type import AccountType
from .accounting.currency import Currency 
from .accounting.exchange_rate import ExchangeRate 
from .accounting.account import Account 
from .accounting.fiscal_year import FiscalYear
from .accounting.fiscal_period import FiscalPeriod 
from .accounting.journal_entry import JournalEntry, JournalEntryLine 
from .accounting.recurring_pattern import RecurringPattern
from .accounting.dimension import Dimension 
from .accounting.budget import Budget, BudgetDetail 
from .accounting.tax_code import TaxCode 
from .accounting.gst_return import GSTReturn 
from .accounting.withholding_tax_certificate import WithholdingTaxCertificate

# Business schema models
from .business.customer import Customer
from .business.vendor import Vendor
from .business.product import Product
from .business.inventory_movement import InventoryMovement
from .business.sales_invoice import SalesInvoice, SalesInvoiceLine
from .business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine
from .business.bank_account import BankAccount
from .business.bank_transaction import BankTransaction
from .business.payment import Payment, PaymentAllocation
from .business.bank_reconciliation import BankReconciliation # New Import

# Audit schema models
from .audit.audit_log import AuditLog
from .audit.data_change_history import DataChangeHistory

__all__ = [
    "Base", "TimestampMixin", "UserAuditMixin",
    # Core
    "User", "Role", "Permission", 
    "CompanySetting", "Configuration", "Sequence",
    # Accounting
    "AccountType", "Currency", "ExchangeRate", "Account",
    "FiscalYear", "FiscalPeriod", "JournalEntry", "JournalEntryLine",
    "RecurringPattern", "Dimension", "Budget", "BudgetDetail",
    "TaxCode", "GSTReturn", "WithholdingTaxCertificate",
    # Business
    "Customer", "Vendor", "Product", "InventoryMovement",
    "SalesInvoice", "SalesInvoiceLine", "PurchaseInvoice", "PurchaseInvoiceLine",
    "BankAccount", "BankTransaction", "Payment", "PaymentAllocation",
    "BankReconciliation", # New Export
    # Audit
    "AuditLog", "DataChangeHistory",
]

```

**Validation of Phase 1 (Schema & Models):**
*   **`scripts/schema.sql`**:
    *   New table `business.bank_reconciliations` correctly defined with appropriate columns, PK, FKs (`bank_account_id`, `created_by_user_id`), and unique constraint.
    *   `business.bank_transactions` correctly altered to add `reconciled_bank_reconciliation_id` with FK to the new table.
    *   `business.bank_accounts` correctly altered to add `last_reconciled_balance`.
    *   Schema version comment updated.
    *   All other parts preserved. **Validated.**
*   **`app/models/business/bank_reconciliation.py`**:
    *   New `BankReconciliation` ORM model correctly maps to the new table.
    *   Relationships `bank_account`, `created_by_user`, and `reconciled_transactions` (back-populates `BankTransaction.reconciliation_instance`) are defined.
    *   **Validated.**
*   **`app/models/business/bank_transaction.py`**:
    *   New field `reconciled_bank_reconciliation_id` and relationship `reconciliation_instance` (back-populates `BankReconciliation.reconciled_transactions`) added.
    *   Necessary `TYPE_CHECKING` import for `BankReconciliation` added.
    *   All other fields and relationships preserved. **Validated.**
*   **`app/models/business/bank_account.py`**:
    *   New field `last_reconciled_balance` added.
    *   New relationship `reconciliations` (back-populates `BankReconciliation.bank_account`) added.
    *   Necessary `TYPE_CHECKING` import for `BankReconciliation` added.
    *   All other fields and relationships preserved. **Validated.**
*   **`__init__.py` files**: Correctly updated to export new models. **Validated.**

Phase 1 (Database Schema and ORM models) is complete and validated. I will proceed with DTOs, Service, Manager, and UI updates in the next steps. Since this response is becoming very long, I will provide these in subsequent focused responses if you confirm to proceed. For now, I will give the summary for this completed phase.

---
**Summary of Schema and Model Updates (Phase 1 Complete):**
---
The database schema and corresponding ORM models have been successfully updated to support saving bank reconciliation states:
1.  **`scripts/schema.sql`**: A new table `business.bank_reconciliations` has been added. The `business.bank_transactions` table now includes a foreign key to link reconciled transactions to a specific reconciliation instance. The `business.bank_accounts` table has a new field to store the `last_reconciled_balance`.
2.  **ORM Models**:
    *   A new model `app/models/business/bank_reconciliation.py::BankReconciliation` has been created.
    *   `app/models/business/bank_transaction.py::BankTransaction` has been updated with the new foreign key field and relationship.
    *   `app/models/business/bank_account.py::BankAccount` has been updated with the new balance field and relationship.
    *   Relevant `__init__.py` files in `app/models/` and `app/models/business/` have been updated.

These changes lay the necessary data structure foundation for implementing the "Save Reconciliation" feature. All generated files are complete and have been validated against their previous states and the requirements.
