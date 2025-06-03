```diff
$ diff -u scripts/schema.sql-original scripts/schema.sql
--- scripts/schema.sql-original	2025-06-01 09:28:39.262368491 +0800
+++ scripts/schema.sql	2025-06-02 13:37:34.438069782 +0800
@@ -1,20 +1,23 @@
 -- File: scripts/schema.sql
 -- ============================================================================
--- SG Bookkeeper - Complete Database Schema - Version 1.0.1 (Reordered FKs)
+-- SG Bookkeeper - Complete Database Schema - Version 1.0.3
+-- (Schema version updated for bank_transactions fields & corrected trial_balance view)
 -- ============================================================================
 -- This script creates the complete database schema for the SG Bookkeeper application.
--- Changes from 1.0.0:
---  - All CREATE TABLE statements are grouped first.
---  - All ALTER TABLE ADD CONSTRAINT FOREIGN KEY statements are grouped at the end.
---  - Full table definitions restored.
+-- Changes from 1.0.2:
+--  - Corrected accounting.trial_balance view logic.
+-- Changes from 1.0.1 (incorporated in 1.0.2):
+--  - Added is_from_statement and raw_statement_data to business.bank_transactions
+--  - Added trigger for automatic bank_account balance updates.
+--  - Extended audit logging to bank_accounts and bank_transactions.
 -- ============================================================================
 
 -- ============================================================================
 -- INITIAL SETUP
 -- ============================================================================
-CREATE EXTENSION IF NOT EXISTS pgcrypto;
-CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
-CREATE EXTENSION IF NOT EXISTS btree_gist;
+CREATE EXTENSION IF NOT EXISTS pgcrypto; -- For gen_random_uuid() or other crypto functions if needed
+CREATE EXTENSION IF NOT EXISTS pg_stat_statements; -- For monitoring query performance
+CREATE EXTENSION IF NOT EXISTS btree_gist; -- For EXCLUDE USING gist constraints (e.g., on date ranges)
 
 CREATE SCHEMA IF NOT EXISTS core;
 CREATE SCHEMA IF NOT EXISTS accounting;
@@ -30,7 +33,7 @@
     id SERIAL PRIMARY KEY,
     username VARCHAR(50) NOT NULL UNIQUE,
     password_hash VARCHAR(255) NOT NULL,
-    email VARCHAR(100) UNIQUE, -- Added UNIQUE constraint from reference logic
+    email VARCHAR(100) UNIQUE, 
     full_name VARCHAR(100),
     is_active BOOLEAN DEFAULT TRUE,
     failed_login_attempts INTEGER DEFAULT 0,
@@ -40,7 +43,6 @@
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
 );
--- Comments for core.users (omitted here for brevity, assume they are as per reference)
 
 CREATE TABLE core.roles (
     id SERIAL PRIMARY KEY,
@@ -52,22 +54,22 @@
 
 CREATE TABLE core.permissions (
     id SERIAL PRIMARY KEY,
-    code VARCHAR(50) NOT NULL UNIQUE,
+    code VARCHAR(50) NOT NULL UNIQUE, -- e.g., 'manage_users', 'view_reports'
     description VARCHAR(200),
-    module VARCHAR(50) NOT NULL,
+    module VARCHAR(50) NOT NULL, -- e.g., 'Core', 'Accounting', 'Sales'
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
 );
 
 CREATE TABLE core.role_permissions (
-    role_id INTEGER NOT NULL, -- FK added later
-    permission_id INTEGER NOT NULL, -- FK added later
+    role_id INTEGER NOT NULL, 
+    permission_id INTEGER NOT NULL, 
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     PRIMARY KEY (role_id, permission_id)
 );
 
 CREATE TABLE core.user_roles (
-    user_id INTEGER NOT NULL, -- FK added later
-    role_id INTEGER NOT NULL, -- FK added later
+    user_id INTEGER NOT NULL, 
+    role_id INTEGER NOT NULL, 
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     PRIMARY KEY (user_id, role_id)
 );
@@ -76,7 +78,7 @@
     id SERIAL PRIMARY KEY,
     company_name VARCHAR(100) NOT NULL,
     legal_name VARCHAR(200),
-    uen_no VARCHAR(20),
+    uen_no VARCHAR(20), -- Singapore UEN
     gst_registration_no VARCHAR(20),
     gst_registered BOOLEAN DEFAULT FALSE,
     address_line1 VARCHAR(100),
@@ -88,39 +90,39 @@
     phone VARCHAR(20),
     email VARCHAR(100),
     website VARCHAR(100),
-    logo BYTEA,
+    logo BYTEA, -- Store logo image as bytes
     fiscal_year_start_month INTEGER DEFAULT 1 CHECK (fiscal_year_start_month BETWEEN 1 AND 12),
     fiscal_year_start_day INTEGER DEFAULT 1 CHECK (fiscal_year_start_day BETWEEN 1 AND 31),
-    base_currency VARCHAR(3) DEFAULT 'SGD', -- FK added later
-    tax_id_label VARCHAR(50) DEFAULT 'UEN',
-    date_format VARCHAR(20) DEFAULT 'yyyy-MM-dd',
+    base_currency VARCHAR(3) DEFAULT 'SGD', 
+    tax_id_label VARCHAR(50) DEFAULT 'UEN', -- Label for primary tax ID shown on documents
+    date_format VARCHAR(20) DEFAULT 'yyyy-MM-dd', -- e.g., yyyy-MM-dd, dd/MM/yyyy
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    updated_by INTEGER -- FK added later
+    updated_by INTEGER -- FK to core.users.id
 );
 
 CREATE TABLE core.configuration (
     id SERIAL PRIMARY KEY,
-    config_key VARCHAR(50) NOT NULL UNIQUE,
+    config_key VARCHAR(50) NOT NULL UNIQUE, -- e.g., 'DEFAULT_AR_ACCOUNT_ID'
     config_value TEXT,
     description VARCHAR(200),
-    is_encrypted BOOLEAN DEFAULT FALSE,
+    is_encrypted BOOLEAN DEFAULT FALSE, -- For sensitive config values
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    updated_by INTEGER -- FK added later
+    updated_by INTEGER -- FK to core.users.id
 );
 
 CREATE TABLE core.sequences (
     id SERIAL PRIMARY KEY,
-    sequence_name VARCHAR(50) NOT NULL UNIQUE,
+    sequence_name VARCHAR(50) NOT NULL UNIQUE, -- e.g., 'SALES_INVOICE_NO', 'JOURNAL_ENTRY_NO'
     prefix VARCHAR(10),
     suffix VARCHAR(10),
     next_value INTEGER NOT NULL DEFAULT 1,
     increment_by INTEGER NOT NULL DEFAULT 1,
     min_value INTEGER NOT NULL DEFAULT 1,
-    max_value INTEGER NOT NULL DEFAULT 2147483647,
-    cycle BOOLEAN DEFAULT FALSE,
-    format_template VARCHAR(50) DEFAULT '{PREFIX}{VALUE}{SUFFIX}',
+    max_value INTEGER NOT NULL DEFAULT 2147483647, -- Max int value
+    cycle BOOLEAN DEFAULT FALSE, -- Whether to cycle back to min_value after reaching max_value
+    format_template VARCHAR(50) DEFAULT '{PREFIX}{VALUE}{SUFFIX}', -- e.g., 'INV-{VALUE}'
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
 );
@@ -130,11 +132,11 @@
 -- ============================================================================
 CREATE TABLE accounting.account_types (
     id SERIAL PRIMARY KEY,
-    name VARCHAR(50) NOT NULL UNIQUE,
+    name VARCHAR(50) NOT NULL UNIQUE, -- e.g., 'Current Asset', 'Long-term Liability'
     category VARCHAR(20) NOT NULL CHECK (category IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')),
-    is_debit_balance BOOLEAN NOT NULL,
-    report_type VARCHAR(30) NOT NULL,
-    display_order INTEGER NOT NULL,
+    is_debit_balance BOOLEAN NOT NULL, -- True for Asset, Expense; False for Liability, Equity, Revenue
+    report_type VARCHAR(30) NOT NULL, -- e.g., 'BalanceSheet', 'ProfitAndLoss'
+    display_order INTEGER NOT NULL, -- For ordering in reports/CoA views
     description VARCHAR(200),
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
@@ -142,24 +144,24 @@
 
 CREATE TABLE accounting.accounts (
     id SERIAL PRIMARY KEY,
-    code VARCHAR(20) NOT NULL UNIQUE,
+    code VARCHAR(20) NOT NULL UNIQUE, -- Account code/number
     name VARCHAR(100) NOT NULL,
-    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')),
-    sub_type VARCHAR(30),
-    tax_treatment VARCHAR(20),
+    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')), -- Corresponds to account_types.category
+    sub_type VARCHAR(30), -- More specific type, e.g., 'Cash', 'Bank', 'Accounts Receivable'
+    tax_treatment VARCHAR(20), -- e.g., 'GST Input', 'GST Output', 'Non-Taxable'
     gst_applicable BOOLEAN DEFAULT FALSE,
     is_active BOOLEAN DEFAULT TRUE,
     description TEXT,
-    parent_id INTEGER, -- FK to self, added later
-    report_group VARCHAR(50),
-    is_control_account BOOLEAN DEFAULT FALSE,
-    is_bank_account BOOLEAN DEFAULT FALSE,
+    parent_id INTEGER, -- FK to self for hierarchical CoA
+    report_group VARCHAR(50), -- For custom grouping in financial reports
+    is_control_account BOOLEAN DEFAULT FALSE, -- True if this account is a control account (e.g., AR, AP)
+    is_bank_account BOOLEAN DEFAULT FALSE, -- True if linked to a business.bank_accounts record
     opening_balance NUMERIC(15,2) DEFAULT 0,
     opening_balance_date DATE,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK added later
-    updated_by INTEGER NOT NULL -- FK added later
+    created_by INTEGER NOT NULL, -- FK to core.users.id
+    updated_by INTEGER NOT NULL -- FK to core.users.id
 );
 CREATE INDEX idx_accounts_parent_id ON accounting.accounts(parent_id);
 CREATE INDEX idx_accounts_is_active ON accounting.accounts(is_active);
@@ -167,34 +169,34 @@
 
 CREATE TABLE accounting.fiscal_years (
     id SERIAL PRIMARY KEY,
-    year_name VARCHAR(20) NOT NULL UNIQUE,
+    year_name VARCHAR(20) NOT NULL UNIQUE, -- e.g., 'FY2023', '2023-2024'
     start_date DATE NOT NULL,
     end_date DATE NOT NULL,
     is_closed BOOLEAN DEFAULT FALSE,
     closed_date TIMESTAMP WITH TIME ZONE,
-    closed_by INTEGER, -- FK added later
+    closed_by INTEGER, -- FK to core.users.id
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK added later
-    updated_by INTEGER NOT NULL, -- FK added later
+    created_by INTEGER NOT NULL, -- FK to core.users.id
+    updated_by INTEGER NOT NULL, -- FK to core.users.id
     CONSTRAINT fy_date_range_check CHECK (start_date <= end_date),
     CONSTRAINT fy_unique_date_ranges EXCLUDE USING gist (daterange(start_date, end_date, '[]') WITH &&)
 );
 
 CREATE TABLE accounting.fiscal_periods (
     id SERIAL PRIMARY KEY,
-    fiscal_year_id INTEGER NOT NULL, -- FK added later
-    name VARCHAR(50) NOT NULL,
+    fiscal_year_id INTEGER NOT NULL, -- FK to accounting.fiscal_years.id
+    name VARCHAR(50) NOT NULL, -- e.g., 'Jan 2023', 'Q1 2023'
     start_date DATE NOT NULL,
     end_date DATE NOT NULL,
     period_type VARCHAR(10) NOT NULL CHECK (period_type IN ('Month', 'Quarter', 'Year')),
     status VARCHAR(10) NOT NULL CHECK (status IN ('Open', 'Closed', 'Archived')),
-    period_number INTEGER NOT NULL,
-    is_adjustment BOOLEAN DEFAULT FALSE,
+    period_number INTEGER NOT NULL, -- e.g., 1 for Jan, 1 for Q1
+    is_adjustment BOOLEAN DEFAULT FALSE, -- For year-end adjustment periods
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK added later
-    updated_by INTEGER NOT NULL, -- FK added later
+    created_by INTEGER NOT NULL, -- FK to core.users.id
+    updated_by INTEGER NOT NULL, -- FK to core.users.id
     CONSTRAINT fp_date_range_check CHECK (start_date <= end_date),
     CONSTRAINT fp_unique_period_dates UNIQUE (fiscal_year_id, period_type, period_number)
 );
@@ -202,51 +204,51 @@
 CREATE INDEX idx_fiscal_periods_status ON accounting.fiscal_periods(status);
 
 CREATE TABLE accounting.currencies (
-    code CHAR(3) PRIMARY KEY,
+    code CHAR(3) PRIMARY KEY, -- e.g., 'SGD', 'USD'
     name VARCHAR(50) NOT NULL,
     symbol VARCHAR(10) NOT NULL,
     is_active BOOLEAN DEFAULT TRUE,
     decimal_places INTEGER DEFAULT 2,
-    format_string VARCHAR(20) DEFAULT '#,##0.00',
+    format_string VARCHAR(20) DEFAULT '#,##0.00', -- For display formatting
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER, -- FK added later
-    updated_by INTEGER -- FK added later
+    created_by INTEGER, -- FK to core.users.id
+    updated_by INTEGER -- FK to core.users.id
 );
 
 CREATE TABLE accounting.exchange_rates (
     id SERIAL PRIMARY KEY,
-    from_currency CHAR(3) NOT NULL, -- FK added later
-    to_currency CHAR(3) NOT NULL, -- FK added later
+    from_currency CHAR(3) NOT NULL, -- FK to accounting.currencies.code
+    to_currency CHAR(3) NOT NULL, -- FK to accounting.currencies.code
     rate_date DATE NOT NULL,
     exchange_rate NUMERIC(15,6) NOT NULL,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER, -- FK added later
-    updated_by INTEGER, -- FK added later
+    created_by INTEGER, -- FK to core.users.id
+    updated_by INTEGER, -- FK to core.users.id
     CONSTRAINT uq_exchange_rates_pair_date UNIQUE (from_currency, to_currency, rate_date)
 );
 CREATE INDEX idx_exchange_rates_lookup ON accounting.exchange_rates(from_currency, to_currency, rate_date);
 
 CREATE TABLE accounting.journal_entries (
     id SERIAL PRIMARY KEY,
-    entry_no VARCHAR(20) NOT NULL UNIQUE,
-    journal_type VARCHAR(20) NOT NULL,
+    entry_no VARCHAR(20) NOT NULL UNIQUE, -- System-generated
+    journal_type VARCHAR(20) NOT NULL, -- e.g., 'General', 'Sales', 'Purchase', 'Payment'
     entry_date DATE NOT NULL,
-    fiscal_period_id INTEGER NOT NULL, -- FK added later
+    fiscal_period_id INTEGER NOT NULL, -- FK to accounting.fiscal_periods.id
     description VARCHAR(500),
-    reference VARCHAR(100),
+    reference VARCHAR(100), -- External reference if any
     is_recurring BOOLEAN DEFAULT FALSE,
-    recurring_pattern_id INTEGER, -- FK added later
+    recurring_pattern_id INTEGER, -- FK to accounting.recurring_patterns.id
     is_posted BOOLEAN DEFAULT FALSE,
     is_reversed BOOLEAN DEFAULT FALSE,
-    reversing_entry_id INTEGER, -- FK to self, added later
-    source_type VARCHAR(50),
-    source_id INTEGER,
+    reversing_entry_id INTEGER, -- FK to self (accounting.journal_entries.id)
+    source_type VARCHAR(50), -- e.g., 'SalesInvoice', 'PurchaseInvoice', 'Payment'
+    source_id INTEGER, -- ID of the source document
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK added later
-    updated_by INTEGER NOT NULL -- FK added later
+    created_by INTEGER NOT NULL, -- FK to core.users.id
+    updated_by INTEGER NOT NULL -- FK to core.users.id
 );
 CREATE INDEX idx_journal_entries_date ON accounting.journal_entries(entry_date);
 CREATE INDEX idx_journal_entries_fiscal_period ON accounting.journal_entries(fiscal_period_id);
@@ -255,18 +257,18 @@
 
 CREATE TABLE accounting.journal_entry_lines (
     id SERIAL PRIMARY KEY,
-    journal_entry_id INTEGER NOT NULL, -- FK added later
+    journal_entry_id INTEGER NOT NULL, -- FK to accounting.journal_entries.id
     line_number INTEGER NOT NULL,
-    account_id INTEGER NOT NULL, -- FK added later
+    account_id INTEGER NOT NULL, -- FK to accounting.accounts.id
     description VARCHAR(200),
     debit_amount NUMERIC(15,2) DEFAULT 0,
     credit_amount NUMERIC(15,2) DEFAULT 0,
-    currency_code CHAR(3) DEFAULT 'SGD', -- FK added later
-    exchange_rate NUMERIC(15,6) DEFAULT 1,
-    tax_code VARCHAR(20), -- FK added later
+    currency_code CHAR(3) DEFAULT 'SGD', -- FK to accounting.currencies.code
+    exchange_rate NUMERIC(15,6) DEFAULT 1, -- Rate to base currency
+    tax_code VARCHAR(20), -- FK to accounting.tax_codes.code
     tax_amount NUMERIC(15,2) DEFAULT 0,
-    dimension1_id INTEGER, -- FK added later
-    dimension2_id INTEGER, -- FK added later
+    dimension1_id INTEGER, -- FK to accounting.dimensions.id (e.g., Department)
+    dimension2_id INTEGER, -- FK to accounting.dimensions.id (e.g., Project)
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     CONSTRAINT jel_check_debit_credit CHECK ((debit_amount > 0 AND credit_amount = 0) OR (credit_amount > 0 AND debit_amount = 0) OR (debit_amount = 0 AND credit_amount = 0))
@@ -278,111 +280,111 @@
     id SERIAL PRIMARY KEY,
     name VARCHAR(100) NOT NULL,
     description TEXT,
-    template_entry_id INTEGER NOT NULL, -- FK added later
+    template_entry_id INTEGER NOT NULL, -- FK to a template journal_entries.id
     frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly')),
-    interval_value INTEGER NOT NULL DEFAULT 1,
+    interval_value INTEGER NOT NULL DEFAULT 1, -- e.g., every 2 months
     start_date DATE NOT NULL,
-    end_date DATE,
-    day_of_month INTEGER CHECK (day_of_month BETWEEN 1 AND 31),
-    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6),
+    end_date DATE, -- Optional end date for recurrence
+    day_of_month INTEGER CHECK (day_of_month BETWEEN 1 AND 31), -- For monthly recurrence
+    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6), -- For weekly recurrence (0=Sunday)
     last_generated_date DATE,
     next_generation_date DATE,
     is_active BOOLEAN DEFAULT TRUE,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK added later
-    updated_by INTEGER NOT NULL -- FK added later
+    created_by INTEGER NOT NULL, -- FK to core.users.id
+    updated_by INTEGER NOT NULL -- FK to core.users.id
 );
 
 CREATE TABLE accounting.dimensions (
     id SERIAL PRIMARY KEY,
-    dimension_type VARCHAR(50) NOT NULL,
+    dimension_type VARCHAR(50) NOT NULL, -- e.g., 'Department', 'Project', 'Location'
     code VARCHAR(20) NOT NULL,
     name VARCHAR(100) NOT NULL,
     description TEXT,
     is_active BOOLEAN DEFAULT TRUE,
-    parent_id INTEGER, -- FK to self, added later
+    parent_id INTEGER, -- FK to self for hierarchical dimensions
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK added later
-    updated_by INTEGER NOT NULL, -- FK added later
+    created_by INTEGER NOT NULL, -- FK to core.users.id
+    updated_by INTEGER NOT NULL, -- FK to core.users.id
     UNIQUE (dimension_type, code)
 );
 
 CREATE TABLE accounting.budgets (
     id SERIAL PRIMARY KEY,
     name VARCHAR(100) NOT NULL,
-    fiscal_year_id INTEGER NOT NULL, -- FK added later
+    fiscal_year_id INTEGER NOT NULL, -- FK to accounting.fiscal_years.id
     description TEXT,
     is_active BOOLEAN DEFAULT TRUE,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK added later
-    updated_by INTEGER NOT NULL -- FK added later
+    created_by INTEGER NOT NULL, -- FK to core.users.id
+    updated_by INTEGER NOT NULL -- FK to core.users.id
 );
 
 CREATE TABLE accounting.budget_details (
     id SERIAL PRIMARY KEY,
-    budget_id INTEGER NOT NULL, -- FK added later
-    account_id INTEGER NOT NULL, -- FK added later
-    fiscal_period_id INTEGER NOT NULL, -- FK added later
+    budget_id INTEGER NOT NULL, -- FK to accounting.budgets.id
+    account_id INTEGER NOT NULL, -- FK to accounting.accounts.id
+    fiscal_period_id INTEGER NOT NULL, -- FK to accounting.fiscal_periods.id
     amount NUMERIC(15,2) NOT NULL,
-    dimension1_id INTEGER, -- FK added later
-    dimension2_id INTEGER, -- FK added later
+    dimension1_id INTEGER, -- FK to accounting.dimensions.id
+    dimension2_id INTEGER, -- FK to accounting.dimensions.id
     notes TEXT,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK added later
-    updated_by INTEGER NOT NULL -- FK added later
+    created_by INTEGER NOT NULL, -- FK to core.users.id
+    updated_by INTEGER NOT NULL -- FK to core.users.id
 );
 CREATE UNIQUE INDEX uix_budget_details_key ON accounting.budget_details (budget_id, account_id, fiscal_period_id, COALESCE(dimension1_id, 0), COALESCE(dimension2_id, 0));
 
 CREATE TABLE accounting.tax_codes (
     id SERIAL PRIMARY KEY,
-    code VARCHAR(20) NOT NULL UNIQUE,
+    code VARCHAR(20) NOT NULL UNIQUE, -- e.g., 'SR', 'ZR', 'ES', 'TX'
     description VARCHAR(100) NOT NULL,
     tax_type VARCHAR(20) NOT NULL CHECK (tax_type IN ('GST', 'Income Tax', 'Withholding Tax')),
-    rate NUMERIC(5,2) NOT NULL,
+    rate NUMERIC(5,2) NOT NULL, -- e.g., 9.00 for 9% GST
     is_default BOOLEAN DEFAULT FALSE,
     is_active BOOLEAN DEFAULT TRUE,
-    affects_account_id INTEGER, -- FK added later
+    affects_account_id INTEGER, -- FK to accounting.accounts.id (e.g., GST Payable/Receivable account)
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK added later
-    updated_by INTEGER NOT NULL -- FK added later
+    created_by INTEGER NOT NULL, -- FK to core.users.id
+    updated_by INTEGER NOT NULL -- FK to core.users.id
 );
 
 CREATE TABLE accounting.gst_returns (
     id SERIAL PRIMARY KEY,
-    return_period VARCHAR(20) NOT NULL UNIQUE,
+    return_period VARCHAR(20) NOT NULL UNIQUE, -- e.g., 'Q1/2023'
     start_date DATE NOT NULL,
     end_date DATE NOT NULL,
     filing_due_date DATE NOT NULL,
-    standard_rated_supplies NUMERIC(15,2) DEFAULT 0,
-    zero_rated_supplies NUMERIC(15,2) DEFAULT 0,
-    exempt_supplies NUMERIC(15,2) DEFAULT 0,
-    total_supplies NUMERIC(15,2) DEFAULT 0,
-    taxable_purchases NUMERIC(15,2) DEFAULT 0,
-    output_tax NUMERIC(15,2) DEFAULT 0,
-    input_tax NUMERIC(15,2) DEFAULT 0,
-    tax_adjustments NUMERIC(15,2) DEFAULT 0,
-    tax_payable NUMERIC(15,2) DEFAULT 0,
+    standard_rated_supplies NUMERIC(15,2) DEFAULT 0, -- Box 1
+    zero_rated_supplies NUMERIC(15,2) DEFAULT 0,    -- Box 2
+    exempt_supplies NUMERIC(15,2) DEFAULT 0,        -- Box 3
+    total_supplies NUMERIC(15,2) DEFAULT 0,         -- Box 4 (Auto-calc: Box 1+2+3)
+    taxable_purchases NUMERIC(15,2) DEFAULT 0,      -- Box 5
+    output_tax NUMERIC(15,2) DEFAULT 0,             -- Box 6
+    input_tax NUMERIC(15,2) DEFAULT 0,              -- Box 7
+    tax_adjustments NUMERIC(15,2) DEFAULT 0,        -- Box 8 (e.g., bad debt relief)
+    tax_payable NUMERIC(15,2) DEFAULT 0,            -- Box 9 (Auto-calc: Box 6-7+8)
     status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Submitted', 'Amended')),
     submission_date DATE,
-    submission_reference VARCHAR(50),
-    journal_entry_id INTEGER, -- FK added later
+    submission_reference VARCHAR(50), -- IRAS submission reference
+    journal_entry_id INTEGER, -- FK to accounting.journal_entries.id (for GST settlement JE)
     notes TEXT,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK added later
-    updated_by INTEGER NOT NULL -- FK added later
+    created_by INTEGER NOT NULL, -- FK to core.users.id
+    updated_by INTEGER NOT NULL -- FK to core.users.id
 );
 
 CREATE TABLE accounting.withholding_tax_certificates (
     id SERIAL PRIMARY KEY,
     certificate_no VARCHAR(20) NOT NULL UNIQUE,
-    vendor_id INTEGER NOT NULL, -- FK added later
-    tax_type VARCHAR(50) NOT NULL,
+    vendor_id INTEGER NOT NULL, -- FK to business.vendors.id
+    tax_type VARCHAR(50) NOT NULL, -- e.g., 'Section 19', 'Section 45'
     tax_rate NUMERIC(5,2) NOT NULL,
     payment_date DATE NOT NULL,
     amount_before_tax NUMERIC(15,2) NOT NULL,
@@ -390,12 +392,12 @@
     payment_reference VARCHAR(50),
     status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Issued', 'Voided')),
     issue_date DATE,
-    journal_entry_id INTEGER, -- FK added later
+    journal_entry_id INTEGER, -- FK to accounting.journal_entries.id
     notes TEXT,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK added later
-    updated_by INTEGER NOT NULL -- FK added later
+    created_by INTEGER NOT NULL, -- FK to core.users.id
+    updated_by INTEGER NOT NULL -- FK to core.users.id
 );
 
 -- ============================================================================
@@ -437,8 +439,29 @@
     id SERIAL PRIMARY KEY, account_name VARCHAR(100) NOT NULL, account_number VARCHAR(50) NOT NULL, bank_name VARCHAR(100) NOT NULL, bank_branch VARCHAR(100), bank_swift_code VARCHAR(20), currency_code CHAR(3) NOT NULL, opening_balance NUMERIC(15,2) DEFAULT 0, current_balance NUMERIC(15,2) DEFAULT 0, last_reconciled_date DATE, gl_account_id INTEGER NOT NULL, is_active BOOLEAN DEFAULT TRUE, description TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
 
 CREATE TABLE business.bank_transactions (
-    id SERIAL PRIMARY KEY, bank_account_id INTEGER NOT NULL, transaction_date DATE NOT NULL, value_date DATE, transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Interest', 'Fee', 'Adjustment')), description VARCHAR(200) NOT NULL, reference VARCHAR(100), amount NUMERIC(15,2) NOT NULL, is_reconciled BOOLEAN DEFAULT FALSE, reconciled_date DATE, statement_date DATE, statement_id VARCHAR(50), journal_entry_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
-CREATE INDEX idx_bank_transactions_account ON business.bank_transactions(bank_account_id); CREATE INDEX idx_bank_transactions_date ON business.bank_transactions(transaction_date); CREATE INDEX idx_bank_transactions_reconciled ON business.bank_transactions(is_reconciled);
+    id SERIAL PRIMARY KEY, 
+    bank_account_id INTEGER NOT NULL, 
+    transaction_date DATE NOT NULL, 
+    value_date DATE, 
+    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Interest', 'Fee', 'Adjustment')), 
+    description VARCHAR(200) NOT NULL, 
+    reference VARCHAR(100), 
+    amount NUMERIC(15,2) NOT NULL, -- Signed amount: positive for inflow, negative for outflow
+    is_reconciled BOOLEAN DEFAULT FALSE NOT NULL, 
+    reconciled_date DATE, 
+    statement_date DATE, 
+    statement_id VARCHAR(50), 
+    is_from_statement BOOLEAN NOT NULL DEFAULT FALSE, -- New column
+    raw_statement_data JSONB NULL, -- New column
+    journal_entry_id INTEGER, 
+    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
+    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
+    created_by INTEGER NOT NULL, 
+    updated_by INTEGER NOT NULL
+);
+CREATE INDEX idx_bank_transactions_account ON business.bank_transactions(bank_account_id); 
+CREATE INDEX idx_bank_transactions_date ON business.bank_transactions(transaction_date); 
+CREATE INDEX idx_bank_transactions_reconciled ON business.bank_transactions(is_reconciled);
 
 CREATE TABLE business.payments (
     id SERIAL PRIMARY KEY, payment_no VARCHAR(20) NOT NULL UNIQUE, payment_type VARCHAR(20) NOT NULL CHECK (payment_type IN ('Customer Payment', 'Vendor Payment', 'Refund', 'Credit Note', 'Other')), payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('Cash', 'Check', 'Bank Transfer', 'Credit Card', 'GIRO', 'PayNow', 'Other')), payment_date DATE NOT NULL, entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('Customer', 'Vendor', 'Other')), entity_id INTEGER NOT NULL, bank_account_id INTEGER, currency_code CHAR(3) NOT NULL, exchange_rate NUMERIC(15,6) DEFAULT 1, amount NUMERIC(15,2) NOT NULL, reference VARCHAR(100), description TEXT, cheque_no VARCHAR(50), status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Approved', 'Completed', 'Voided', 'Returned')), journal_entry_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
@@ -460,9 +483,8 @@
 CREATE INDEX idx_data_change_history_table_record ON audit.data_change_history(table_name, record_id); CREATE INDEX idx_data_change_history_changed_at ON audit.data_change_history(changed_at);
 
 -- ============================================================================
--- ADDING FOREIGN KEY CONSTRAINTS (Grouped at the end)
+-- ADDING FOREIGN KEY CONSTRAINTS 
 -- ============================================================================
-
 -- Core Schema FKs
 ALTER TABLE core.role_permissions ADD CONSTRAINT fk_rp_role FOREIGN KEY (role_id) REFERENCES core.roles(id) ON DELETE CASCADE;
 ALTER TABLE core.role_permissions ADD CONSTRAINT fk_rp_permission FOREIGN KEY (permission_id) REFERENCES core.permissions(id) ON DELETE CASCADE;
@@ -497,7 +519,6 @@
 ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_je_reversing_entry FOREIGN KEY (reversing_entry_id) REFERENCES accounting.journal_entries(id);
 ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_je_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
 ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_je_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
--- Deferred FK for recurring_patterns cycle:
 ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_je_recurring_pattern FOREIGN KEY (recurring_pattern_id) REFERENCES accounting.recurring_patterns(id) DEFERRABLE INITIALLY DEFERRED;
 
 ALTER TABLE accounting.journal_entry_lines ADD CONSTRAINT fk_jel_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id) ON DELETE CASCADE;
@@ -600,7 +621,6 @@
 ALTER TABLE business.payments ADD CONSTRAINT fk_pay_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
 ALTER TABLE business.payments ADD CONSTRAINT fk_pay_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
 ALTER TABLE business.payments ADD CONSTRAINT fk_pay_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
--- Note: entity_id in payments refers to customers.id or vendors.id; requires application logic or triggers to enforce based on entity_type.
 
 ALTER TABLE business.payment_allocations ADD CONSTRAINT fk_pa_payment FOREIGN KEY (payment_id) REFERENCES business.payments(id) ON DELETE CASCADE;
 ALTER TABLE business.payment_allocations ADD CONSTRAINT fk_pa_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
@@ -614,24 +634,46 @@
 -- ============================================================================
 CREATE OR REPLACE VIEW accounting.account_balances AS
 SELECT 
-    a.id AS account_id, a.code AS account_code, a.name AS account_name, a.account_type, a.parent_id,
+    a.id AS account_id,
+    a.code AS account_code,
+    a.name AS account_name,
+    a.account_type,
+    a.parent_id,
+    -- balance is calculated as: opening_balance + sum_of_debits - sum_of_credits
+    -- where debits increase balance and credits decrease balance (for Asset/Expense view)
+    -- or credits increase balance and debits decrease balance (for Liability/Equity/Revenue view)
+    -- The current logic `SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END)`
+    -- effectively sums (debits - credits), so a positive result is a net debit movement.
     COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) + a.opening_balance AS balance,
-    COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE 0 END), 0) AS total_debits_activity,
-    COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0) AS total_credits_activity,
+    COALESCE(SUM(jel.debit_amount), 0) AS total_debits_activity, -- Sum of all debit lines
+    COALESCE(SUM(jel.credit_amount), 0) AS total_credits_activity, -- Sum of all credit lines
     MAX(je.entry_date) AS last_activity_date
 FROM accounting.accounts a
 LEFT JOIN accounting.journal_entry_lines jel ON a.id = jel.account_id
 LEFT JOIN accounting.journal_entries je ON jel.journal_entry_id = je.id AND je.is_posted = TRUE
 GROUP BY a.id, a.code, a.name, a.account_type, a.parent_id, a.opening_balance;
 
+-- Corrected Trial Balance View
 CREATE OR REPLACE VIEW accounting.trial_balance AS
 SELECT 
-    a.id AS account_id, a.code AS account_code, a.name AS account_name, a.account_type, a.sub_type,
-    CASE WHEN a.account_type IN ('Asset', 'Expense') THEN CASE WHEN ab.balance >= 0 THEN ab.balance ELSE 0 END ELSE CASE WHEN ab.balance < 0 THEN -ab.balance ELSE 0 END END AS debit_balance,
-    CASE WHEN a.account_type IN ('Asset', 'Expense') THEN CASE WHEN ab.balance < 0 THEN -ab.balance ELSE 0 END ELSE CASE WHEN ab.balance >= 0 THEN ab.balance ELSE 0 END END AS credit_balance
+    a.id AS account_id,
+    a.code AS account_code,
+    a.name AS account_name,
+    a.account_type,
+    a.sub_type,
+    -- If ab.balance (net debit actual balance) > 0, it's a debit balance.
+    -- If ab.balance (net credit actual balance) < 0, it's a credit balance (-ab.balance).
+    CASE 
+        WHEN ab.balance > 0 THEN ab.balance 
+        ELSE 0 
+    END AS debit_balance,
+    CASE 
+        WHEN ab.balance < 0 THEN -ab.balance -- Show as positive in credit column
+        ELSE 0 
+    END AS credit_balance
 FROM accounting.accounts a
 JOIN accounting.account_balances ab ON a.id = ab.account_id
-WHERE a.is_active = TRUE AND ab.balance != 0;
+WHERE a.is_active = TRUE AND ab.balance != 0; -- Only show active accounts with non-zero balances
 
 CREATE OR REPLACE VIEW business.customer_balances AS
 SELECT c.id AS customer_id, c.customer_code, c.name AS customer_name,
@@ -655,7 +697,11 @@
 SELECT 
     p.id AS product_id, p.product_code, p.name AS product_name, p.product_type, p.category, p.unit_of_measure,
     COALESCE(SUM(im.quantity), 0) AS current_quantity,
-    CASE WHEN COALESCE(SUM(im.quantity), 0) != 0 THEN COALESCE(SUM(im.total_cost), 0) / SUM(im.quantity) ELSE p.purchase_price END AS average_cost,
+    CASE 
+        WHEN COALESCE(SUM(im.quantity), 0) != 0 THEN 
+            (COALESCE(SUM(im.total_cost), 0) / SUM(im.quantity)) -- Parentheses added for clarity
+        ELSE p.purchase_price -- Fallback to product's purchase price if no movements/zero quantity
+    END AS average_cost,
     COALESCE(SUM(im.total_cost), 0) AS inventory_value,
     p.sales_price AS current_sales_price, p.min_stock_level, p.reorder_point,
     CASE WHEN p.min_stock_level IS NOT NULL AND COALESCE(SUM(im.quantity), 0) <= p.min_stock_level THEN TRUE ELSE FALSE END AS below_minimum,
@@ -664,6 +710,7 @@
 WHERE p.product_type = 'Inventory' AND p.is_active = TRUE
 GROUP BY p.id, p.product_code, p.name, p.product_type, p.category, p.unit_of_measure, p.purchase_price, p.sales_price, p.min_stock_level, p.reorder_point;
 
+
 -- ============================================================================
 -- FUNCTIONS
 -- ============================================================================
@@ -677,7 +724,7 @@
     UPDATE core.sequences SET next_value = next_value + increment_by, updated_at = CURRENT_TIMESTAMP WHERE sequence_name = p_sequence_name;
     v_result := v_sequence.format_template;
     v_result := REPLACE(v_result, '{PREFIX}', COALESCE(v_sequence.prefix, ''));
-    v_result := REPLACE(v_result, '{VALUE}', LPAD(v_next_value::TEXT, 6, '0'));
+    v_result := REPLACE(v_result, '{VALUE}', LPAD(v_next_value::TEXT, 6, '0')); -- Standard 6 digit padding
     v_result := REPLACE(v_result, '{SUFFIX}', COALESCE(v_sequence.suffix, ''));
     RETURN v_result;
 END;
@@ -689,7 +736,7 @@
 BEGIN
     SELECT id INTO v_fiscal_period_id FROM accounting.fiscal_periods WHERE p_entry_date BETWEEN start_date AND end_date AND status = 'Open';
     IF v_fiscal_period_id IS NULL THEN RAISE EXCEPTION 'No open fiscal period found for date %', p_entry_date; END IF;
-    v_entry_no := core.get_next_sequence_value('journal_entry');
+    v_entry_no := core.get_next_sequence_value('journal_entry'); -- Assuming 'journal_entry' sequence exists
     INSERT INTO accounting.journal_entries (entry_no, journal_type, entry_date, fiscal_period_id, description, reference, is_posted, source_type, source_id, created_by, updated_by) VALUES (v_entry_no, p_journal_type, p_entry_date, v_fiscal_period_id, p_description, p_reference, FALSE, p_source_type, p_source_id, p_user_id, p_user_id) RETURNING id INTO v_journal_id;
     FOR v_line IN SELECT * FROM jsonb_array_elements(p_lines) LOOP
         INSERT INTO accounting.journal_entry_lines (journal_entry_id, line_number, account_id, description, debit_amount, credit_amount, currency_code, exchange_rate, tax_code, tax_amount, dimension1_id, dimension2_id) 
@@ -720,7 +767,17 @@
 BEGIN
     SELECT acc.opening_balance, acc.opening_balance_date INTO v_opening_balance, v_account_opening_balance_date FROM accounting.accounts acc WHERE acc.id = p_account_id;
     IF NOT FOUND THEN RAISE EXCEPTION 'Account with ID % not found', p_account_id; END IF;
-    SELECT COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) INTO v_balance FROM accounting.journal_entry_lines jel JOIN accounting.journal_entries je ON jel.journal_entry_id = je.id WHERE jel.account_id = p_account_id AND je.is_posted = TRUE AND je.entry_date <= p_as_of_date AND (v_account_opening_balance_date IS NULL OR je.entry_date >= v_account_opening_balance_date);
+    -- Sum (debits - credits) from posted journal entry lines up to the specified date
+    -- and after or on the account's opening balance date (if specified)
+    SELECT COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) 
+    INTO v_balance 
+    FROM accounting.journal_entry_lines jel 
+    JOIN accounting.journal_entries je ON jel.journal_entry_id = je.id 
+    WHERE jel.account_id = p_account_id 
+      AND je.is_posted = TRUE 
+      AND je.entry_date <= p_as_of_date 
+      AND (v_account_opening_balance_date IS NULL OR je.entry_date >= v_account_opening_balance_date);
+      
     v_balance := v_balance + COALESCE(v_opening_balance, 0);
     RETURN v_balance;
 END;
@@ -734,21 +791,33 @@
 DECLARE
     v_old_data JSONB; v_new_data JSONB; v_change_type VARCHAR(20); v_user_id INTEGER; v_entity_id INTEGER; v_entity_name VARCHAR(200); temp_val TEXT; current_field_name_from_json TEXT;
 BEGIN
+    -- Try to get user_id from session variable first
     BEGIN v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER; EXCEPTION WHEN OTHERS THEN v_user_id := NULL; END;
+    -- Fallback to created_by/updated_by if session variable not set (e.g., direct DB modification)
     IF v_user_id IS NULL THEN
         IF TG_OP = 'INSERT' THEN BEGIN v_user_id := NEW.created_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END;
         ELSIF TG_OP = 'UPDATE' THEN BEGIN v_user_id := NEW.updated_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END;
+        -- For DELETE, if v_user_id is still NULL, it means we can't determine it from OLD record's updated_by
         END IF;
     END IF;
+    -- Avoid logging changes to audit tables themselves to prevent infinite loops
     IF TG_TABLE_SCHEMA = 'audit' AND TG_TABLE_NAME IN ('audit_log', 'data_change_history') THEN RETURN NULL; END IF;
+
     IF TG_OP = 'INSERT' THEN v_change_type := 'Insert'; v_old_data := NULL; v_new_data := to_jsonb(NEW);
     ELSIF TG_OP = 'UPDATE' THEN v_change_type := 'Update'; v_old_data := to_jsonb(OLD); v_new_data := to_jsonb(NEW);
     ELSIF TG_OP = 'DELETE' THEN v_change_type := 'Delete'; v_old_data := to_jsonb(OLD); v_new_data := NULL; END IF;
+
+    -- Determine entity_id (usually 'id' column)
     BEGIN IF TG_OP = 'DELETE' THEN v_entity_id := OLD.id; ELSE v_entity_id := NEW.id; END IF; EXCEPTION WHEN undefined_column THEN v_entity_id := NULL; END;
+    
+    -- Determine a representative entity_name (e.g., name, code, entry_no)
     BEGIN IF TG_OP = 'DELETE' THEN temp_val := CASE WHEN TG_TABLE_NAME IN ('accounts','customers','vendors','products','roles','account_types','dimensions','fiscal_years','budgets') THEN OLD.name WHEN TG_TABLE_NAME = 'journal_entries' THEN OLD.entry_no WHEN TG_TABLE_NAME = 'sales_invoices' THEN OLD.invoice_no WHEN TG_TABLE_NAME = 'purchase_invoices' THEN OLD.invoice_no WHEN TG_TABLE_NAME = 'payments' THEN OLD.payment_no WHEN TG_TABLE_NAME = 'users' THEN OLD.username WHEN TG_TABLE_NAME = 'tax_codes' THEN OLD.code WHEN TG_TABLE_NAME = 'gst_returns' THEN OLD.return_period ELSE OLD.id::TEXT END;
     ELSE temp_val := CASE WHEN TG_TABLE_NAME IN ('accounts','customers','vendors','products','roles','account_types','dimensions','fiscal_years','budgets') THEN NEW.name WHEN TG_TABLE_NAME = 'journal_entries' THEN NEW.entry_no WHEN TG_TABLE_NAME = 'sales_invoices' THEN NEW.invoice_no WHEN TG_TABLE_NAME = 'purchase_invoices' THEN NEW.invoice_no WHEN TG_TABLE_NAME = 'payments' THEN NEW.payment_no WHEN TG_TABLE_NAME = 'users' THEN NEW.username WHEN TG_TABLE_NAME = 'tax_codes' THEN NEW.code WHEN TG_TABLE_NAME = 'gst_returns' THEN NEW.return_period ELSE NEW.id::TEXT END; END IF; v_entity_name := temp_val;
     EXCEPTION WHEN undefined_column THEN BEGIN IF TG_OP = 'DELETE' THEN v_entity_name := OLD.id::TEXT; ELSE v_entity_name := NEW.id::TEXT; END IF; EXCEPTION WHEN undefined_column THEN v_entity_name := NULL; END; END;
+
     INSERT INTO audit.audit_log (user_id,action,entity_type,entity_id,entity_name,changes,timestamp) VALUES (v_user_id,v_change_type,TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,v_entity_id,v_entity_name,jsonb_build_object('old',v_old_data,'new',v_new_data),CURRENT_TIMESTAMP);
+
+    -- Log individual field changes for UPDATE operations
     IF TG_OP = 'UPDATE' THEN
         FOR current_field_name_from_json IN SELECT key_alias FROM jsonb_object_keys(v_old_data) AS t(key_alias) LOOP
             IF (v_new_data ? current_field_name_from_json) AND ((v_old_data -> current_field_name_from_json) IS DISTINCT FROM (v_new_data -> current_field_name_from_json)) THEN
@@ -756,14 +825,95 @@
             END IF;
         END LOOP;
     END IF;
-    RETURN NULL; 
+    RETURN NULL; -- Result is ignored for AFTER trigger
 END;
 $$ LANGUAGE plpgsql;
 
+-- Trigger to update bank_account.current_balance
+CREATE OR REPLACE FUNCTION business.update_bank_account_balance_trigger_func()
+RETURNS TRIGGER AS $$
+BEGIN
+    IF TG_OP = 'INSERT' THEN
+        UPDATE business.bank_accounts 
+        SET current_balance = current_balance + NEW.amount -- Assumes NEW.amount is signed
+        WHERE id = NEW.bank_account_id;
+    ELSIF TG_OP = 'DELETE' THEN
+        UPDATE business.bank_accounts 
+        SET current_balance = current_balance - OLD.amount -- Assumes OLD.amount is signed
+        WHERE id = OLD.bank_account_id;
+    ELSIF TG_OP = 'UPDATE' THEN
+        -- If bank account itself changed for the transaction
+        IF NEW.bank_account_id != OLD.bank_account_id THEN
+            UPDATE business.bank_accounts 
+            SET current_balance = current_balance - OLD.amount 
+            WHERE id = OLD.bank_account_id;
+            
+            UPDATE business.bank_accounts 
+            SET current_balance = current_balance + NEW.amount 
+            WHERE id = NEW.bank_account_id;
+        ELSE -- Bank account is the same, just adjust for amount difference
+            UPDATE business.bank_accounts 
+            SET current_balance = current_balance - OLD.amount + NEW.amount 
+            WHERE id = NEW.bank_account_id;
+        END IF;
+    END IF;
+    RETURN NULL; -- Result is ignored since this is an AFTER trigger
+END;
+$$ LANGUAGE plpgsql;
+
+
 -- ============================================================================
 -- APPLYING TRIGGERS
 -- ============================================================================
-DO $$ DECLARE r RECORD; BEGIN FOR r IN SELECT table_schema, table_name FROM information_schema.columns WHERE column_name = 'updated_at' AND table_schema IN ('core','accounting','business','audit') GROUP BY table_schema, table_name LOOP EXECUTE format('DROP TRIGGER IF EXISTS trg_update_timestamp ON %I.%I; CREATE TRIGGER trg_update_timestamp BEFORE UPDATE ON %I.%I FOR EACH ROW EXECUTE FUNCTION core.update_timestamp_trigger_func();',r.table_schema,r.table_name,r.table_schema,r.table_name); END LOOP; END; $$;
-DO $$ DECLARE tables_to_audit TEXT[] := ARRAY['accounting.accounts','accounting.journal_entries','accounting.fiscal_periods','accounting.fiscal_years','business.customers','business.vendors','business.products','business.sales_invoices','business.purchase_invoices','business.payments','accounting.tax_codes','accounting.gst_returns','core.users','core.roles','core.company_settings']; table_fullname TEXT; schema_name TEXT; table_name_var TEXT; BEGIN FOREACH table_fullname IN ARRAY tables_to_audit LOOP SELECT split_part(table_fullname,'.',1) INTO schema_name; SELECT split_part(table_fullname,'.',2) INTO table_name_var; EXECUTE format('DROP TRIGGER IF EXISTS trg_audit_log ON %I.%I; CREATE TRIGGER trg_audit_log AFTER INSERT OR UPDATE OR DELETE ON %I.%I FOR EACH ROW EXECUTE FUNCTION audit.log_data_change_trigger_func();',schema_name,table_name_var,schema_name,table_name_var); END LOOP; END; $$;
+-- Apply update_timestamp trigger to all tables with 'updated_at'
+DO $$
+DECLARE r RECORD;
+BEGIN
+    FOR r IN 
+        SELECT table_schema, table_name 
+        FROM information_schema.columns 
+        WHERE column_name = 'updated_at' AND table_schema IN ('core','accounting','business','audit')
+        GROUP BY table_schema, table_name 
+    LOOP
+        EXECUTE format(
+            'DROP TRIGGER IF EXISTS trg_update_timestamp ON %I.%I; CREATE TRIGGER trg_update_timestamp BEFORE UPDATE ON %I.%I FOR EACH ROW EXECUTE FUNCTION core.update_timestamp_trigger_func();',
+            r.table_schema, r.table_name, r.table_schema, r.table_name
+        );
+    END LOOP;
+END;
+$$;
+
+-- Apply audit log trigger to specified tables
+DO $$
+DECLARE
+    tables_to_audit TEXT[] := ARRAY[
+        'accounting.accounts', 'accounting.journal_entries', 'accounting.fiscal_periods', 'accounting.fiscal_years',
+        'business.customers', 'business.vendors', 'business.products', 
+        'business.sales_invoices', 'business.purchase_invoices', 'business.payments',
+        'accounting.tax_codes', 'accounting.gst_returns',
+        'core.users', 'core.roles', 'core.company_settings', 
+        'business.bank_accounts', 'business.bank_transactions' -- Added banking tables
+    ];
+    table_fullname TEXT;
+    schema_name TEXT;
+    table_name_var TEXT;
+BEGIN
+    FOREACH table_fullname IN ARRAY tables_to_audit
+    LOOP
+        SELECT split_part(table_fullname, '.', 1) INTO schema_name;
+        SELECT split_part(table_fullname, '.', 2) INTO table_name_var;
+        EXECUTE format(
+            'DROP TRIGGER IF EXISTS trg_audit_log ON %I.%I; CREATE TRIGGER trg_audit_log AFTER INSERT OR UPDATE OR DELETE ON %I.%I FOR EACH ROW EXECUTE FUNCTION audit.log_data_change_trigger_func();',
+            schema_name, table_name_var, schema_name, table_name_var
+        );
+    END LOOP;
+END;
+$$;
+
+-- Apply bank balance update trigger
+DROP TRIGGER IF EXISTS trg_update_bank_balance ON business.bank_transactions;
+CREATE TRIGGER trg_update_bank_balance
+AFTER INSERT OR UPDATE OR DELETE ON business.bank_transactions
+FOR EACH ROW EXECUTE FUNCTION business.update_bank_account_balance_trigger_func();
 
 -- End of script
```

```diff
$ diff -u scripts/initial_data.sql-original scripts/initial_data.sql
--- scripts/initial_data.sql-original	2025-06-01 09:29:10.823233443 +0800
+++ scripts/initial_data.sql	2025-06-02 14:11:35.858218657 +0800
@@ -1,8 +1,13 @@
 -- File: scripts/initial_data.sql
 -- ============================================================================
--- INITIAL DATA (Version 1.0.2 - Added Configuration Keys for Default Accounts)
+-- INITIAL DATA (Version 1.0.3 - Added sequence grants for audit schema)
 -- ============================================================================
 
+-- Ensure this script is run by a superuser or the owner of the database/schemas
+-- Default user for application runtime: sgbookkeeper_user
+
+BEGIN;
+
 -- ----------------------------------------------------------------------------
 -- Insert default roles
 -- ----------------------------------------------------------------------------
@@ -27,6 +32,7 @@
 ('DATA_BACKUP', 'Backup and restore data', 'System'),
 ('DATA_IMPORT', 'Import data', 'System'),
 ('DATA_EXPORT', 'Export data', 'System'),
+('VIEW_AUDIT_LOG', 'View audit logs', 'System'),
 -- Accounting permissions
 ('ACCOUNT_VIEW', 'View chart of accounts', 'Accounting'),
 ('ACCOUNT_CREATE', 'Create accounts', 'Accounting'),
@@ -64,12 +70,12 @@
 ('PAYMENT_DELETE', 'Delete payments', 'Transactions'),
 ('PAYMENT_APPROVE', 'Approve payments', 'Transactions'),
 -- Banking permissions
-('BANK_VIEW', 'View bank accounts', 'Banking'),
-('BANK_CREATE', 'Create bank accounts', 'Banking'),
-('BANK_EDIT', 'Edit bank accounts', 'Banking'),
-('BANK_DELETE', 'Delete bank accounts', 'Banking'),
+('BANK_ACCOUNT_VIEW', 'View bank accounts', 'Banking'),
+('BANK_ACCOUNT_MANAGE', 'Manage bank accounts (CRUD)', 'Banking'),
+('BANK_TRANSACTION_VIEW', 'View bank transactions', 'Banking'),
+('BANK_TRANSACTION_MANAGE', 'Manage bank transactions (manual entry)', 'Banking'),
 ('BANK_RECONCILE', 'Reconcile bank accounts', 'Banking'),
-('BANK_STATEMENT', 'Import bank statements', 'Banking'),
+('BANK_STATEMENT_IMPORT', 'Import bank statements', 'Banking'),
 -- Tax permissions
 ('TAX_VIEW', 'View tax settings', 'Tax'),
 ('TAX_EDIT', 'Edit tax settings', 'Tax'),
@@ -100,8 +106,6 @@
     require_password_change = EXCLUDED.require_password_change,
     updated_at = CURRENT_TIMESTAMP;
 
--- Synchronize the sequence for core.users.id after inserting user with ID 1
--- This ensures the next user (e.g., 'admin') gets a correct auto-generated ID
 SELECT setval(pg_get_serial_sequence('core.users', 'id'), COALESCE((SELECT MAX(id) FROM core.users), 1), true);
 
 -- ----------------------------------------------------------------------------
@@ -130,7 +134,6 @@
 
 -- ----------------------------------------------------------------------------
 -- Insert Default Company Settings (ID = 1)
--- This MUST come AFTER core.users ID 1 is created and base currency (SGD) is defined.
 -- ----------------------------------------------------------------------------
 INSERT INTO core.company_settings (
     id, company_name, legal_name, uen_no, gst_registration_no, gst_registered, 
@@ -177,8 +180,7 @@
     format_template = EXCLUDED.format_template, updated_at = CURRENT_TIMESTAMP;
 
 -- ----------------------------------------------------------------------------
--- Insert default configuration values (NEW SECTION from previous fix)
--- These account codes MUST exist from chart_of_accounts CSV or be system accounts
+-- Insert default configuration values
 -- ----------------------------------------------------------------------------
 INSERT INTO core.configuration (config_key, config_value, description, updated_by) VALUES
 ('SysAcc_DefaultAR', '1120', 'Default Accounts Receivable account code', 1),
@@ -186,7 +188,11 @@
 ('SysAcc_DefaultGSTOutput', 'SYS-GST-OUTPUT', 'Default GST Output Tax account code', 1),
 ('SysAcc_DefaultAP', '2110', 'Default Accounts Payable account code', 1),
 ('SysAcc_DefaultPurchaseExpense', '5100', 'Default Purchase/COGS account code', 1),
-('SysAcc_DefaultGSTInput', 'SYS-GST-INPUT', 'Default GST Input Tax account code', 1)
+('SysAcc_DefaultGSTInput', 'SYS-GST-INPUT', 'Default GST Input Tax account code', 1),
+('SysAcc_DefaultCash', '1112', 'Default Cash on Hand account code', 1), 
+('SysAcc_DefaultInventoryAsset', '1130', 'Default Inventory Asset account code', 1),
+('SysAcc_DefaultCOGS', '5100', 'Default Cost of Goods Sold account code', 1),
+('SysAcc_GSTControl', 'SYS-GST-CONTROL', 'GST Control/Clearing Account', 1)
 ON CONFLICT (config_key) DO UPDATE SET
     config_value = EXCLUDED.config_value,
     description = EXCLUDED.description,
@@ -212,24 +218,20 @@
     category = EXCLUDED.category, is_debit_balance = EXCLUDED.is_debit_balance, report_type = EXCLUDED.report_type,
     display_order = EXCLUDED.display_order, description = EXCLUDED.description, updated_at = CURRENT_TIMESTAMP;
 
--- Ensure key GL accounts from default CoA exist if not already inserted by CSV import via app (NEW SECTION from previous fix)
--- These are referenced by the core.configuration defaults
-INSERT INTO accounting.accounts (code, name, account_type, sub_type, created_by, updated_by, is_active, is_control_account) VALUES
-('1120', 'Accounts Receivable Control', 'Asset', 'Accounts Receivable', 1, 1, TRUE, TRUE),
-('2110', 'Accounts Payable Control', 'Liability', 'Accounts Payable', 1, 1, TRUE, TRUE),
-('4100', 'General Sales Revenue', 'Revenue', 'Sales', 1, 1, TRUE, FALSE),
-('5100', 'General Cost of Goods Sold', 'Expense', 'Cost of Sales', 1, 1, TRUE, FALSE)
-ON CONFLICT (code) DO NOTHING; -- Do nothing if they already exist (e.g. from CSV)
-
 -- ----------------------------------------------------------------------------
--- Insert default tax codes related accounts
--- ----------------------------------------------------------------------------
-INSERT INTO accounting.accounts (code, name, account_type, created_by, updated_by, is_active) VALUES
-('SYS-GST-OUTPUT', 'System GST Output Tax', 'Liability', 1, 1, TRUE),
-('SYS-GST-INPUT', 'System GST Input Tax', 'Asset', 1, 1, TRUE)
-ON CONFLICT (code) DO UPDATE SET
-    name = EXCLUDED.name, account_type = EXCLUDED.account_type, updated_by = EXCLUDED.updated_by, 
-    is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;
+-- Ensure key GL accounts for system configuration exist
+-- ----------------------------------------------------------------------------
+INSERT INTO accounting.accounts (code, name, account_type, sub_type, created_by, updated_by, is_active, is_control_account, is_bank_account) VALUES
+('1120', 'Accounts Receivable Control', 'Asset', 'Accounts Receivable', 1, 1, TRUE, TRUE, FALSE),
+('2110', 'Accounts Payable Control', 'Liability', 'Accounts Payable', 1, 1, TRUE, TRUE, FALSE),
+('4100', 'General Sales Revenue', 'Revenue', 'Sales', 1, 1, TRUE, FALSE, FALSE),
+('5100', 'General Cost of Goods Sold', 'Expense', 'Cost of Sales', 1, 1, TRUE, FALSE, FALSE),
+('SYS-GST-OUTPUT', 'System GST Output Tax', 'Liability', 'GST Payable', 1, 1, TRUE, FALSE, FALSE),
+('SYS-GST-INPUT', 'System GST Input Tax', 'Asset', 'GST Receivable', 1, 1, TRUE, FALSE, FALSE),
+('SYS-GST-CONTROL', 'System GST Control', 'Liability', 'GST Payable', 1, 1, TRUE, TRUE, FALSE),
+('1112', 'Cash on Hand', 'Asset', 'Cash and Cash Equivalents', 1,1, TRUE, FALSE, FALSE),
+('1130', 'Inventory Asset Control', 'Asset', 'Inventory', 1,1,TRUE, TRUE, FALSE)
+ON CONFLICT (code) DO NOTHING;
 
 -- ----------------------------------------------------------------------------
 -- Insert default tax codes (GST updated to 9%)
@@ -276,7 +278,9 @@
 ('CA', 'Capital Allowance', 'Income Tax', 0.00, FALSE, TRUE, 1, 1, NULL)
 ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;
 
+-- ----------------------------------------------------------------------------
 -- Create an active 'admin' user for application login
+-- ----------------------------------------------------------------------------
 INSERT INTO core.users (username, password_hash, email, full_name, is_active, require_password_change)
 VALUES ('admin', crypt('password', gen_salt('bf')), 'admin@sgbookkeeper.com', 'Administrator', TRUE, TRUE)
 ON CONFLICT (username) DO UPDATE SET
@@ -284,7 +288,9 @@
     is_active = EXCLUDED.is_active, require_password_change = EXCLUDED.require_password_change,
     updated_at = CURRENT_TIMESTAMP;
 
+-- ----------------------------------------------------------------------------
 -- Assign 'Administrator' role to 'admin' user
+-- ----------------------------------------------------------------------------
 WITH admin_user_id_cte AS (SELECT id FROM core.users WHERE username = 'admin'),
      admin_role_id_cte AS (SELECT id FROM core.roles WHERE name = 'Administrator')
 INSERT INTO core.user_roles (user_id, role_id, created_at)
@@ -292,12 +298,48 @@
 WHERE admin_user_id_cte.id IS NOT NULL AND admin_role_id_cte.id IS NOT NULL
 ON CONFLICT (user_id, role_id) DO NOTHING;
 
+-- ----------------------------------------------------------------------------
 -- For all permissions, grant them to the 'Administrator' role
+-- ----------------------------------------------------------------------------
 INSERT INTO core.role_permissions (role_id, permission_id, created_at)
 SELECT r.id, p.id, CURRENT_TIMESTAMP
 FROM core.roles r, core.permissions p
 WHERE r.name = 'Administrator'
 ON CONFLICT (role_id, permission_id) DO NOTHING;
 
+-- ----------------------------------------------------------------------------
+-- Grant Privileges to Application User (sgbookkeeper_user)
+-- This part is typically run by an admin user (e.g., postgres) after schema creation
+-- The application user 'sgbookkeeper_user' needs these privileges to operate.
+-- ----------------------------------------------------------------------------
+GRANT USAGE ON SCHEMA core, accounting, business, audit TO sgbookkeeper_user;
+
+GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO sgbookkeeper_user;
+GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA accounting TO sgbookkeeper_user;
+GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA business TO sgbookkeeper_user;
+GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA audit TO sgbookkeeper_user;
+
+GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA core TO sgbookkeeper_user;
+GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA accounting TO sgbookkeeper_user;
+GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA business TO sgbookkeeper_user;
+GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA audit TO sgbookkeeper_user; -- Added for audit schema sequences
+
+GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA core TO sgbookkeeper_user;
+GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA accounting TO sgbookkeeper_user;
+GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA business TO sgbookkeeper_user; -- Added for business schema functions
+GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA audit TO sgbookkeeper_user;
+
+-- Default privileges for future objects created by 'postgres' (or the user running db_init.py)
+-- This helps ensure sgbookkeeper_user can access newly created tables/sequences if schema evolves
+ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA core GRANT ALL ON TABLES TO sgbookkeeper_user;
+ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA accounting GRANT ALL ON TABLES TO sgbookkeeper_user;
+ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA business GRANT ALL ON TABLES TO sgbookkeeper_user;
+ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA audit GRANT ALL ON TABLES TO sgbookkeeper_user;
+
+ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA core GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
+ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA accounting GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
+ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA business GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
+ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA audit GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user; -- Added for audit schema
+
 COMMIT; 
 -- End of initial data
```

```sql
-- FILE: schema_patch_1.0.3_to_1.0.4.sql
-- PURPOSE: Updates SG Bookkeeper database schema from version 1.0.3 to 1.0.4
--          Adds tables and columns required for saving bank reconciliation state.
--
-- PREVIOUS VERSION: 1.0.3 (Includes bank statement import fields, bank balance trigger, corrected trial_balance view)
-- NEW VERSION: 1.0.4
--
-- Important: Ensure your database schema is at version 1.0.3 before applying this patch.
-- It is recommended to backup your database before applying any schema changes.

BEGIN;

-- ----------------------------------------------------------------------------
-- 1. Add new table: business.bank_reconciliations
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS business.bank_reconciliations (
    id SERIAL PRIMARY KEY,
    bank_account_id INTEGER NOT NULL,
    statement_date DATE NOT NULL, -- The end date of the bank statement being reconciled
    statement_ending_balance NUMERIC(15,2) NOT NULL,
    calculated_book_balance NUMERIC(15,2) NOT NULL, -- The book balance that reconciles to the statement
    reconciled_difference NUMERIC(15,2) NOT NULL, -- Should be close to zero
    reconciliation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- When this reconciliation record was created
    notes TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER NOT NULL,
    CONSTRAINT uq_bank_reconciliation_account_statement_date UNIQUE (bank_account_id, statement_date)
);

COMMENT ON TABLE business.bank_reconciliations IS 'Stores summary records of completed bank reconciliations.';
COMMENT ON COLUMN business.bank_reconciliations.statement_date IS 'The end date of the bank statement that was reconciled.';
COMMENT ON COLUMN business.bank_reconciliations.calculated_book_balance IS 'The book balance of the bank account as of the statement_date, after all reconciling items for this reconciliation are accounted for.';


-- ----------------------------------------------------------------------------
-- 2. Add 'last_reconciled_balance' column to 'business.bank_accounts'
-- ----------------------------------------------------------------------------
ALTER TABLE business.bank_accounts
ADD COLUMN IF NOT EXISTS last_reconciled_balance NUMERIC(15,2) NULL;

COMMENT ON COLUMN business.bank_accounts.last_reconciled_balance IS 'The ending balance of the bank account as per the last successfully completed reconciliation.';


-- ----------------------------------------------------------------------------
-- 3. Add 'reconciled_bank_reconciliation_id' column to 'business.bank_transactions'
-- ----------------------------------------------------------------------------
ALTER TABLE business.bank_transactions
ADD COLUMN IF NOT EXISTS reconciled_bank_reconciliation_id INT NULL;

COMMENT ON COLUMN business.bank_transactions.reconciled_bank_reconciliation_id IS 'Foreign key to business.bank_reconciliations, linking a transaction to the specific reconciliation it was cleared in.';


-- ----------------------------------------------------------------------------
-- 4. Add Foreign Key Constraints for the new table and columns
-- ----------------------------------------------------------------------------

-- FK for business.bank_reconciliations table
ALTER TABLE business.bank_reconciliations
    ADD CONSTRAINT fk_br_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_br_created_by FOREIGN KEY (created_by_user_id) REFERENCES core.users(id);

-- FK for the new column in business.bank_transactions
ALTER TABLE business.bank_transactions
    ADD CONSTRAINT fk_bt_reconciliation FOREIGN KEY (reconciled_bank_reconciliation_id) REFERENCES business.bank_reconciliations(id) ON DELETE SET NULL;

-- Update schema version comment in a conceptual way (actual file versioning would be manual)
-- For tracking, this patch moves the schema towards 1.0.4.

COMMIT;
```
