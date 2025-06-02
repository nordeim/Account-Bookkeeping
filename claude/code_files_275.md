<think>
The user has provided another `diff` output for `scripts/schema.sql`.
`scripts/schema.sql-previous` is my V1.0.3 (from response_22).
`scripts/schema.sql` (the `+++` lines) is my V1.0.4 (from response_31, where I *attempted* to fix the "incomplete file" issue after user feedback on response_30).

The user states: "you still seem to have accidentally omitted many lines and sections from the earlier working version. you really need to stay focused and be more meticulous in your work."
This means my attempt in response_31 to provide a complete `scripts/schema.sql` was still faulty and resulted in omissions. I need to understand *why* this keeps happening with this specific file and ensure it doesn't happen again.

**My process error in response_31 for `schema.sql`:**
In response_31, my internal thought process was to take the *clean V1.0.3 from response_22* and then *manually describe and integrate the DDL changes for V1.0.4*. When I generated the final output, I must have failed to correctly merge these, and instead of outputting the full merged content, I outputted something that *looked like a diff or a severely truncated version*.

The diff provided by the user now explicitly shows these omissions.

**Analyzing the NEW `diff` for `scripts/schema.sql` (response_22's V1.0.3 vs response_31's V1.0.4):**

*   **Header Comments (Lines 1-14)**: My version 1.0.4 correctly updates the version and change notes.
*   **Initial Setup (Lines 16-23 in `previous` vs 19-21 in `latest`)**:
    *   `previous` (1.0.3): `CREATE EXTENSION...` with comments.
    *   `latest` (1.0.4): `CREATE EXTENSION...` without the detailed comments.
    *   This is a minor omission of comments, not functional. **But it's still an omission.**
*   **Core Schema Tables (Lines 27-101 in `previous` vs 24-36 in `latest`)**:
    *   `previous` (1.0.3) has full definitions for `core.users`, `core.roles`, `core.permissions`, `core.role_permissions`, `core.user_roles`, `core.company_settings`, `core.configuration`, `core.sequences`.
    *   `latest` (1.0.4) in the `diff` *only shows `core.users` and then the `diff` jumps to Accounting tables*. This indicates **all other core tables were omitted** in my response_31's output for `schema.sql`.
    *   **This is a major omission.**

*   **Accounting Schema Tables (Lines 104-400 in `previous` vs 39-192 in `latest`)**:
    *   Similar to core tables, the `diff` shows the `accounting.account_types` definition, then jumps, indicating that `accounting.accounts`, `fiscal_years`, `fiscal_periods`, `currencies`, `exchange_rates`, `journal_entries`, `journal_entry_lines`, `recurring_patterns`, `dimensions`, `budgets`, `budget_details`, `tax_codes`, `gst_returns`, `withholding_tax_certificates` **were all omitted**.
    *   **This is another major omission.**

*   **Business Schema Tables (Lines 403-460 in `previous` vs 195-234 in `latest` for pre-existing tables)**:
    *   `previous` (1.0.3) contains definitions for `customers`, `vendors`, `products`, `inventory_movements`, `sales_invoices`, `sales_invoice_lines`, `purchase_invoices`, `purchase_invoice_lines`, and the *already updated* `bank_accounts` and `bank_transactions` (with statement import fields).
    *   `latest` (1.0.4) in the `diff` shows the updates to `bank_accounts` (add `last_reconciled_balance`) and `bank_transactions` (add `reconciled_bank_reconciliation_id`). **However, it implies that all other business tables listed above were omitted.**
    *   **This is a major omission.**
    *   The new table `business.bank_reconciliations` (lines 237-249 in `latest`) is correctly added.

*   **Audit Schema Tables (Lines 463-472 in `previous` vs 252-257 in `latest`)**:
    *   It appears these might have been preserved, but the line counts are suspicious. The `diff` shows them as largely unchanged but within much smaller overall blocks. I must verify if they are truly complete in my "latest". The placeholder comment approach indicates they were likely omitted.

*   **Foreign Key Constraints (Lines 475-617 in `previous` vs 260-323 in `latest` for existing FKs)**:
    *   Similar pattern. The `diff` shows the `previous` block of FKs, then a much smaller block in `latest`. **This implies many FK definitions were omitted.**
    *   The new FKs for `bank_reconciliations` and `bank_transactions` (lines 325-330 in `latest`) are correctly added.

*   **Views (Lines 620-680 in `previous` vs 334-340 in `latest`)**:
    *   `previous` (1.0.3) has the corrected `trial_balance` and all other views (`account_balances`, `customer_balances`, `vendor_balances`, `inventory_summary`).
    *   `latest` (1.0.4) in the `diff` only shows the `CREATE OR REPLACE VIEW` statements but seems to be missing the actual view bodies. The placeholder comment `(-- ... (unchanged from response_22 which had corrected trial_balance) ...)` was used.
    *   **This is a major omission.** All views were lost.

*   **Functions (Lines 683-803 in `previous` vs 343-345 in `latest`)**:
    *   `previous` (1.0.3) has all defined functions.
    *   `latest` (1.0.4) in the `diff` only has a placeholder comment. **All functions were omitted.** Major omission.

*   **Applying Triggers (Lines 806-832 in `previous` vs 348-350 in `latest`)**:
    *   `previous` (1.0.3) has all trigger application logic.
    *   `latest` (1.0.4) in the `diff` only has a placeholder comment. **All trigger applications were omitted.** Major omission.

**Conclusion from this `diff` Review:**

The user is absolutely correct. My attempt in response_31 to generate a complete `scripts/schema.sql` (v1.0.4) was severely flawed. Instead of building upon the complete v1.0.3, I effectively only outputted the *changes* for v1.0.4 and replaced most of the existing v1.0.3 content with placeholder comments. This resulted in a massively incomplete and unusable schema file.

**Root Cause of My Repeated Error for `scripts/schema.sql`**:
I seem to be struggling with the "complete file replacement" when the file is very large and I'm only adding a few new things. My internal process for merging "existing complete content" with "new additions" for `schema.sql` is clearly breaking down, and I'm defaulting to showing only the delta or using placeholders.

**New, More Robust Plan to Fix `scripts/schema.sql` (and my process):**

1.  **Establish the Correct, Complete Base**: I MUST use the full, clean SQL content of `scripts/schema.sql` (version 1.0.3) as generated and validated in **response_22**. This version is known to be complete and contains all prior fixes (including trial_balance view, bank statement import columns, bank balance update trigger, extended audit).
2.  **Identify Specific DDL Additions for Version 1.0.4 (Save Reconciliation State)**:
    *   `CREATE TABLE business.bank_reconciliations (...)`
    *   Addition of `last_reconciled_balance NUMERIC(15,2) NULL` to `business.bank_accounts` table definition.
    *   Addition of `reconciled_bank_reconciliation_id INT NULL` to `business.bank_transactions` table definition.
    *   New Foreign Key constraints for `business.bank_reconciliations` and the new column in `business.bank_transactions`.
3.  **Strategic Insertion**:
    *   The new `CREATE TABLE business.bank_reconciliations` will be placed within the `BUSINESS SCHEMA TABLES` section, typically after existing business tables.
    *   The new columns will be added directly into the `CREATE TABLE` statements for `business.bank_accounts` and `business.bank_transactions`.
    *   The new `ALTER TABLE ... ADD CONSTRAINT FOREIGN KEY ...` statements will be added to the end of the "ADDING FOREIGN KEY CONSTRAINTS" section, grouped logically (e.g., under Business Schema FKs or a new "Bank Reconciliation FKs" subheading).
4.  **Header Update**: Change version to `1.0.4` and update change log comments at the top.
5.  **No Placeholders**: I will explicitly forbid myself from using "..." or "unchanged" comments for any SQL code block. The entire script must be generated.
6.  **Meticulous Manual Merge (Simulated)**: I will mentally construct the full file by taking the complete 1.0.3, then carefully inserting the new DDL in the correct locations, and then updating the header.
7.  **Final Verification**: Before outputting, I will re-read my generated SQL:
    *   Confirm all tables from 1.0.3 are present.
    *   Confirm all views (esp. `trial_balance`) from 1.0.3 are present and correct.
    *   Confirm all functions from 1.0.3 are present.
    *   Confirm all FKs from 1.0.3 are present.
    *   Confirm all Triggers and their application from 1.0.3 are present.
    *   Confirm the new 1.0.4 elements are correctly integrated.

This time, I will ensure the output is the truly complete file. The user's patience is appreciated, and I must correct this properly.
</think>

You are absolutely right to point this out again, and I sincerely apologize for repeating the mistake of not providing a truly complete `scripts/schema.sql` file. My previous attempt in response_31 was clearly still flawed, and the `diff` you've provided highlights the significant omissions. Using placeholder comments instead of the full, preserved SQL code is unacceptable and violates the core principles of our collaboration.

I understand my process for generating this large, cumulative SQL file needs to be much more robust. I will now make a an extremely focused effort to produce the correct and genuinely complete `scripts/schema.sql` file (Version 1.0.4).

**Corrected Plan for Generating `scripts/schema.sql` (Version 1.0.4):**

1.  **Base Content**: I will start with the **full and correct SQL content of `scripts/schema.sql` version 1.0.3**. This is the version from my response_22, which included:
    *   All original schema definitions (tables, older views, functions, FKs, indexes, triggers).
    *   The corrected `accounting.trial_balance` view.
    *   The bank statement import fields (`is_from_statement`, `raw_statement_data`) in `business.bank_transactions`.
    *   The `business.update_bank_account_balance_trigger_func` and its application.
    *   The extended audit logging to include `business.bank_accounts` and `business.bank_transactions`.
2.  **Identify Precise Additions for Version 1.0.4**:
    *   **New Table**: `business.bank_reconciliations`.
    *   **Column Addition to `business.bank_accounts`**: `last_reconciled_balance NUMERIC(15,2) NULL`.
    *   **Column Addition to `business.bank_transactions`**: `reconciled_bank_reconciliation_id INT NULL`.
    *   **New Foreign Key Constraints**: For `business.bank_reconciliations` (to `bank_accounts` and `users`) and for `business.bank_transactions.reconciled_bank_reconciliation_id` (to `bank_reconciliations`).
3.  **Integration Strategy**:
    *   The `CREATE TABLE business.bank_reconciliations` statement will be added logically within the "BUSINESS SCHEMA TABLES" section.
    *   The new columns will be inserted directly into the existing `CREATE TABLE` definitions for `business.bank_accounts` and `business.bank_transactions`.
    *   The new `ALTER TABLE ... ADD CONSTRAINT FOREIGN KEY` statements will be added at the end of the "ADDING FOREIGN KEY CONSTRAINTS" section, ensuring they are grouped with other Business Schema FKs or as a new distinct group for clarity.
4.  **Header Update**: The file header comments will be updated to reflect Version `1.0.4` and clearly list the changes specific to this version.
5.  **No Omissions - Full Content Generation**: I will ensure that *every single line* of the v1.0.3 base is carried over, and the new DDL for v1.0.4 is carefully inserted. There will be no placeholder comments like `(-- ... unchanged ...)` for any SQL code.
6.  **Final Validation (Simulated Line-by-Line)**: Before outputting, I will perform a meticulous mental review comparing the generated v1.0.4 against the full v1.0.3 base to ensure:
    *   All elements of v1.0.3 are present.
    *   The v1.0.4 additions are correctly placed and syntactically sound.
    *   No accidental deletions or modifications have occurred.

I am treating this as a critical fix to my own process.

---
**Complete Updated File: `scripts/schema.sql` (Version 1.0.4)**
---

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
-- Changes from 1.0.2 (incorporated in 1.0.3):
--  - Corrected accounting.trial_balance view logic.
-- Changes from 1.0.1 (incorporated in 1.0.2):
--  - Added is_from_statement and raw_statement_data to business.bank_transactions
--  - Added trigger for automatic bank_account balance updates.
--  - Extended audit logging to bank_accounts and bank_transactions.
-- ============================================================================

-- ============================================================================
-- INITIAL SETUP
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- For gen_random_uuid() or other crypto functions if needed
CREATE EXTENSION IF NOT EXISTS pg_stat_statements; -- For monitoring query performance
CREATE EXTENSION IF NOT EXISTS btree_gist; -- For EXCLUDE USING gist constraints (e.g., on date ranges)

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS accounting;
CREATE SCHEMA IF NOT EXISTS business;
CREATE SCHEMA IF NOT EXISTS audit;

SET search_path TO core, accounting, business, audit, public;

-- ============================================================================
-- CORE SCHEMA TABLES
-- ============================================================================
CREATE TABLE core.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE, 
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    failed_login_attempts INTEGER DEFAULT 0,
    last_login_attempt TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    require_password_change BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE core.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE core.permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE, -- e.g., 'manage_users', 'view_reports'
    description VARCHAR(200),
    module VARCHAR(50) NOT NULL, -- e.g., 'Core', 'Accounting', 'Sales'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE core.role_permissions (
    role_id INTEGER NOT NULL, 
    permission_id INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE core.user_roles (
    user_id INTEGER NOT NULL, 
    role_id INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE core.company_settings (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    legal_name VARCHAR(200),
    uen_no VARCHAR(20), -- Singapore UEN
    gst_registration_no VARCHAR(20),
    gst_registered BOOLEAN DEFAULT FALSE,
    address_line1 VARCHAR(100),
    address_line2 VARCHAR(100),
    postal_code VARCHAR(20),
    city VARCHAR(50) DEFAULT 'Singapore',
    country VARCHAR(50) DEFAULT 'Singapore',
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    website VARCHAR(100),
    logo BYTEA, -- Store logo image as bytes
    fiscal_year_start_month INTEGER DEFAULT 1 CHECK (fiscal_year_start_month BETWEEN 1 AND 12),
    fiscal_year_start_day INTEGER DEFAULT 1 CHECK (fiscal_year_start_day BETWEEN 1 AND 31),
    base_currency VARCHAR(3) DEFAULT 'SGD', 
    tax_id_label VARCHAR(50) DEFAULT 'UEN', -- Label for primary tax ID shown on documents
    date_format VARCHAR(20) DEFAULT 'yyyy-MM-dd', -- e.g., yyyy-MM-dd, dd/MM/yyyy
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER -- FK to core.users.id
);

CREATE TABLE core.configuration (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(50) NOT NULL UNIQUE, -- e.g., 'DEFAULT_AR_ACCOUNT_ID'
    config_value TEXT,
    description VARCHAR(200),
    is_encrypted BOOLEAN DEFAULT FALSE, -- For sensitive config values
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER -- FK to core.users.id
);

CREATE TABLE core.sequences (
    id SERIAL PRIMARY KEY,
    sequence_name VARCHAR(50) NOT NULL UNIQUE, -- e.g., 'SALES_INVOICE_NO', 'JOURNAL_ENTRY_NO'
    prefix VARCHAR(10),
    suffix VARCHAR(10),
    next_value INTEGER NOT NULL DEFAULT 1,
    increment_by INTEGER NOT NULL DEFAULT 1,
    min_value INTEGER NOT NULL DEFAULT 1,
    max_value INTEGER NOT NULL DEFAULT 2147483647, -- Max int value
    cycle BOOLEAN DEFAULT FALSE, -- Whether to cycle back to min_value after reaching max_value
    format_template VARCHAR(50) DEFAULT '{PREFIX}{VALUE}{SUFFIX}', -- e.g., 'INV-{VALUE}'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ACCOUNTING SCHEMA TABLES
-- ============================================================================
CREATE TABLE accounting.account_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE, -- e.g., 'Current Asset', 'Long-term Liability'
    category VARCHAR(20) NOT NULL CHECK (category IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')),
    is_debit_balance BOOLEAN NOT NULL, -- True for Asset, Expense; False for Liability, Equity, Revenue
    report_type VARCHAR(30) NOT NULL, -- e.g., 'BalanceSheet', 'ProfitAndLoss'
    display_order INTEGER NOT NULL, -- For ordering in reports/CoA views
    description VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounting.accounts (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE, -- Account code/number
    name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')), -- Corresponds to account_types.category
    sub_type VARCHAR(30), -- More specific type, e.g., 'Cash', 'Bank', 'Accounts Receivable'
    tax_treatment VARCHAR(20), -- e.g., 'GST Input', 'GST Output', 'Non-Taxable'
    gst_applicable BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    parent_id INTEGER, -- FK to self for hierarchical CoA
    report_group VARCHAR(50), -- For custom grouping in financial reports
    is_control_account BOOLEAN DEFAULT FALSE, -- True if this account is a control account (e.g., AR, AP)
    is_bank_account BOOLEAN DEFAULT FALSE, -- True if linked to a business.bank_accounts record
    opening_balance NUMERIC(15,2) DEFAULT 0,
    opening_balance_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK to core.users.id
    updated_by INTEGER NOT NULL -- FK to core.users.id
);
CREATE INDEX idx_accounts_parent_id ON accounting.accounts(parent_id);
CREATE INDEX idx_accounts_is_active ON accounting.accounts(is_active);
CREATE INDEX idx_accounts_account_type ON accounting.accounts(account_type);

CREATE TABLE accounting.fiscal_years (
    id SERIAL PRIMARY KEY,
    year_name VARCHAR(20) NOT NULL UNIQUE, -- e.g., 'FY2023', '2023-2024'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_closed BOOLEAN DEFAULT FALSE,
    closed_date TIMESTAMP WITH TIME ZONE,
    closed_by INTEGER, -- FK to core.users.id
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK to core.users.id
    updated_by INTEGER NOT NULL, -- FK to core.users.id
    CONSTRAINT fy_date_range_check CHECK (start_date <= end_date),
    CONSTRAINT fy_unique_date_ranges EXCLUDE USING gist (daterange(start_date, end_date, '[]') WITH &&)
);

CREATE TABLE accounting.fiscal_periods (
    id SERIAL PRIMARY KEY,
    fiscal_year_id INTEGER NOT NULL, -- FK to accounting.fiscal_years.id
    name VARCHAR(50) NOT NULL, -- e.g., 'Jan 2023', 'Q1 2023'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    period_type VARCHAR(10) NOT NULL CHECK (period_type IN ('Month', 'Quarter', 'Year')),
    status VARCHAR(10) NOT NULL CHECK (status IN ('Open', 'Closed', 'Archived')),
    period_number INTEGER NOT NULL, -- e.g., 1 for Jan, 1 for Q1
    is_adjustment BOOLEAN DEFAULT FALSE, -- For year-end adjustment periods
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK to core.users.id
    updated_by INTEGER NOT NULL, -- FK to core.users.id
    CONSTRAINT fp_date_range_check CHECK (start_date <= end_date),
    CONSTRAINT fp_unique_period_dates UNIQUE (fiscal_year_id, period_type, period_number)
);
CREATE INDEX idx_fiscal_periods_dates ON accounting.fiscal_periods(start_date, end_date);
CREATE INDEX idx_fiscal_periods_status ON accounting.fiscal_periods(status);

CREATE TABLE accounting.currencies (
    code CHAR(3) PRIMARY KEY, -- e.g., 'SGD', 'USD'
    name VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    decimal_places INTEGER DEFAULT 2,
    format_string VARCHAR(20) DEFAULT '#,##0.00', -- For display formatting
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER, -- FK to core.users.id
    updated_by INTEGER -- FK to core.users.id
);

CREATE TABLE accounting.exchange_rates (
    id SERIAL PRIMARY KEY,
    from_currency CHAR(3) NOT NULL, -- FK to accounting.currencies.code
    to_currency CHAR(3) NOT NULL, -- FK to accounting.currencies.code
    rate_date DATE NOT NULL,
    exchange_rate NUMERIC(15,6) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER, -- FK to core.users.id
    updated_by INTEGER, -- FK to core.users.id
    CONSTRAINT uq_exchange_rates_pair_date UNIQUE (from_currency, to_currency, rate_date)
);
CREATE INDEX idx_exchange_rates_lookup ON accounting.exchange_rates(from_currency, to_currency, rate_date);

CREATE TABLE accounting.journal_entries (
    id SERIAL PRIMARY KEY,
    entry_no VARCHAR(20) NOT NULL UNIQUE, -- System-generated
    journal_type VARCHAR(20) NOT NULL, -- e.g., 'General', 'Sales', 'Purchase', 'Payment'
    entry_date DATE NOT NULL,
    fiscal_period_id INTEGER NOT NULL, -- FK to accounting.fiscal_periods.id
    description VARCHAR(500),
    reference VARCHAR(100), -- External reference if any
    is_recurring BOOLEAN DEFAULT FALSE,
    recurring_pattern_id INTEGER, -- FK to accounting.recurring_patterns.id
    is_posted BOOLEAN DEFAULT FALSE,
    is_reversed BOOLEAN DEFAULT FALSE,
    reversing_entry_id INTEGER, -- FK to self (accounting.journal_entries.id)
    source_type VARCHAR(50), -- e.g., 'SalesInvoice', 'PurchaseInvoice', 'Payment'
    source_id INTEGER, -- ID of the source document
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK to core.users.id
    updated_by INTEGER NOT NULL -- FK to core.users.id
);
CREATE INDEX idx_journal_entries_date ON accounting.journal_entries(entry_date);
CREATE INDEX idx_journal_entries_fiscal_period ON accounting.journal_entries(fiscal_period_id);
CREATE INDEX idx_journal_entries_source ON accounting.journal_entries(source_type, source_id);
CREATE INDEX idx_journal_entries_posted ON accounting.journal_entries(is_posted);

CREATE TABLE accounting.journal_entry_lines (
    id SERIAL PRIMARY KEY,
    journal_entry_id INTEGER NOT NULL, -- FK to accounting.journal_entries.id
    line_number INTEGER NOT NULL,
    account_id INTEGER NOT NULL, -- FK to accounting.accounts.id
    description VARCHAR(200),
    debit_amount NUMERIC(15,2) DEFAULT 0,
    credit_amount NUMERIC(15,2) DEFAULT 0,
    currency_code CHAR(3) DEFAULT 'SGD', -- FK to accounting.currencies.code
    exchange_rate NUMERIC(15,6) DEFAULT 1, -- Rate to base currency
    tax_code VARCHAR(20), -- FK to accounting.tax_codes.code
    tax_amount NUMERIC(15,2) DEFAULT 0,
    dimension1_id INTEGER, -- FK to accounting.dimensions.id (e.g., Department)
    dimension2_id INTEGER, -- FK to accounting.dimensions.id (e.g., Project)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT jel_check_debit_credit CHECK ((debit_amount > 0 AND credit_amount = 0) OR (credit_amount > 0 AND debit_amount = 0) OR (debit_amount = 0 AND credit_amount = 0))
);
CREATE INDEX idx_journal_entry_lines_entry ON accounting.journal_entry_lines(journal_entry_id);
CREATE INDEX idx_journal_entry_lines_account ON accounting.journal_entry_lines(account_id);

CREATE TABLE accounting.recurring_patterns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    template_entry_id INTEGER NOT NULL, -- FK to a template journal_entries.id
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly')),
    interval_value INTEGER NOT NULL DEFAULT 1, -- e.g., every 2 months
    start_date DATE NOT NULL,
    end_date DATE, -- Optional end date for recurrence
    day_of_month INTEGER CHECK (day_of_month BETWEEN 1 AND 31), -- For monthly recurrence
    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6), -- For weekly recurrence (0=Sunday)
    last_generated_date DATE,
    next_generation_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK to core.users.id
    updated_by INTEGER NOT NULL -- FK to core.users.id
);

CREATE TABLE accounting.dimensions (
    id SERIAL PRIMARY KEY,
    dimension_type VARCHAR(50) NOT NULL, -- e.g., 'Department', 'Project', 'Location'
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    parent_id INTEGER, -- FK to self for hierarchical dimensions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK to core.users.id
    updated_by INTEGER NOT NULL, -- FK to core.users.id
    UNIQUE (dimension_type, code)
);

CREATE TABLE accounting.budgets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    fiscal_year_id INTEGER NOT NULL, -- FK to accounting.fiscal_years.id
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK to core.users.id
    updated_by INTEGER NOT NULL -- FK to core.users.id
);

CREATE TABLE accounting.budget_details (
    id SERIAL PRIMARY KEY,
    budget_id INTEGER NOT NULL, -- FK to accounting.budgets.id
    account_id INTEGER NOT NULL, -- FK to accounting.accounts.id
    fiscal_period_id INTEGER NOT NULL, -- FK to accounting.fiscal_periods.id
    amount NUMERIC(15,2) NOT NULL,
    dimension1_id INTEGER, -- FK to accounting.dimensions.id
    dimension2_id INTEGER, -- FK to accounting.dimensions.id
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK to core.users.id
    updated_by INTEGER NOT NULL -- FK to core.users.id
);
CREATE UNIQUE INDEX uix_budget_details_key ON accounting.budget_details (budget_id, account_id, fiscal_period_id, COALESCE(dimension1_id, 0), COALESCE(dimension2_id, 0));

CREATE TABLE accounting.tax_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE, -- e.g., 'SR', 'ZR', 'ES', 'TX'
    description VARCHAR(100) NOT NULL,
    tax_type VARCHAR(20) NOT NULL CHECK (tax_type IN ('GST', 'Income Tax', 'Withholding Tax')),
    rate NUMERIC(5,2) NOT NULL, -- e.g., 9.00 for 9% GST
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    affects_account_id INTEGER, -- FK to accounting.accounts.id (e.g., GST Payable/Receivable account)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK to core.users.id
    updated_by INTEGER NOT NULL -- FK to core.users.id
);

CREATE TABLE accounting.gst_returns (
    id SERIAL PRIMARY KEY,
    return_period VARCHAR(20) NOT NULL UNIQUE, -- e.g., 'Q1/2023'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    filing_due_date DATE NOT NULL,
    standard_rated_supplies NUMERIC(15,2) DEFAULT 0, -- Box 1
    zero_rated_supplies NUMERIC(15,2) DEFAULT 0,    -- Box 2
    exempt_supplies NUMERIC(15,2) DEFAULT 0,        -- Box 3
    total_supplies NUMERIC(15,2) DEFAULT 0,         -- Box 4 (Auto-calc: Box 1+2+3)
    taxable_purchases NUMERIC(15,2) DEFAULT 0,      -- Box 5
    output_tax NUMERIC(15,2) DEFAULT 0,             -- Box 6
    input_tax NUMERIC(15,2) DEFAULT 0,              -- Box 7
    tax_adjustments NUMERIC(15,2) DEFAULT 0,        -- Box 8 (e.g., bad debt relief)
    tax_payable NUMERIC(15,2) DEFAULT 0,            -- Box 9 (Auto-calc: Box 6-7+8)
    status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Submitted', 'Amended')),
    submission_date DATE,
    submission_reference VARCHAR(50), -- IRAS submission reference
    journal_entry_id INTEGER, -- FK to accounting.journal_entries.id (for GST settlement JE)
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK to core.users.id
    updated_by INTEGER NOT NULL -- FK to core.users.id
);

CREATE TABLE accounting.withholding_tax_certificates (
    id SERIAL PRIMARY KEY,
    certificate_no VARCHAR(20) NOT NULL UNIQUE,
    vendor_id INTEGER NOT NULL, -- FK to business.vendors.id
    tax_type VARCHAR(50) NOT NULL, -- e.g., 'Section 19', 'Section 45'
    tax_rate NUMERIC(5,2) NOT NULL,
    payment_date DATE NOT NULL,
    amount_before_tax NUMERIC(15,2) NOT NULL,
    tax_amount NUMERIC(15,2) NOT NULL,
    payment_reference VARCHAR(50),
    status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Issued', 'Voided')),
    issue_date DATE,
    journal_entry_id INTEGER, -- FK to accounting.journal_entries.id
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK to core.users.id
    updated_by INTEGER NOT NULL -- FK to core.users.id
);

-- ============================================================================
-- BUSINESS SCHEMA TABLES
-- ============================================================================
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

CREATE TABLE business.bank_transactions (
    id SERIAL PRIMARY KEY, 
    bank_account_id INTEGER NOT NULL, 
    transaction_date DATE NOT NULL, 
    value_date DATE, 
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Interest', 'Fee', 'Adjustment')), 
    description VARCHAR(200) NOT NULL, 
    reference VARCHAR(100), 
    amount NUMERIC(15,2) NOT NULL, -- Signed amount: positive for inflow, negative for outflow
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
-- AUDIT SCHEMA TABLES
-- ============================================================================
CREATE TABLE audit.audit_log (id SERIAL PRIMARY KEY, user_id INTEGER, action VARCHAR(50) NOT NULL, entity_type VARCHAR(50) NOT NULL, entity_id INTEGER, entity_name VARCHAR(200), changes JSONB, ip_address VARCHAR(45), user_agent VARCHAR(255), timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_audit_log_user ON audit.audit_log(user_id); CREATE INDEX idx_audit_log_entity ON audit.audit_log(entity_type, entity_id); CREATE INDEX idx_audit_log_timestamp ON audit.audit_log(timestamp);
CREATE TABLE audit.data_change_history (id SERIAL PRIMARY KEY, table_name VARCHAR(100) NOT NULL, record_id INTEGER NOT NULL, field_name VARCHAR(100) NOT NULL, old_value TEXT, new_value TEXT, change_type VARCHAR(20) NOT NULL CHECK (change_type IN ('Insert', 'Update', 'Delete')), changed_by INTEGER, changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_data_change_history_table_record ON audit.data_change_history(table_name, record_id); CREATE INDEX idx_data_change_history_changed_at ON audit.data_change_history(changed_at);

-- ============================================================================
-- ADDING FOREIGN KEY CONSTRAINTS 
-- ============================================================================
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

ALTER TABLE audit.audit_log ADD CONSTRAINT fk_al_user FOREIGN KEY (user_id) REFERENCES core.users(id);
ALTER TABLE audit.data_change_history ADD CONSTRAINT fk_dch_changed_by FOREIGN KEY (changed_by) REFERENCES core.users(id);

-- ============================================================================
-- VIEWS
-- ============================================================================
CREATE OR REPLACE VIEW accounting.account_balances AS SELECT a.id AS account_id, a.code AS account_code, a.name AS account_name, a.account_type, a.parent_id, COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) + a.opening_balance AS balance, COALESCE(SUM(jel.debit_amount), 0) AS total_debits_activity, COALESCE(SUM(jel.credit_amount), 0) AS total_credits_activity, MAX(je.entry_date) AS last_activity_date FROM accounting.accounts a LEFT JOIN accounting.journal_entry_lines jel ON a.id = jel.account_id LEFT JOIN accounting.journal_entries je ON jel.journal_entry_id = je.id AND je.is_posted = TRUE GROUP BY a.id, a.code, a.name, a.account_type, a.parent_id, a.opening_balance;
CREATE OR REPLACE VIEW accounting.trial_balance AS SELECT a.id AS account_id, a.code AS account_code, a.name AS account_name, a.account_type, a.sub_type, CASE WHEN ab.balance > 0 THEN ab.balance ELSE 0 END AS debit_balance, CASE WHEN ab.balance < 0 THEN -ab.balance ELSE 0 END AS credit_balance FROM accounting.accounts a JOIN accounting.account_balances ab ON a.id = ab.account_id WHERE a.is_active = TRUE AND ab.balance != 0;
CREATE OR REPLACE VIEW business.customer_balances AS SELECT c.id AS customer_id, c.customer_code, c.name AS customer_name, COALESCE(SUM(si.total_amount - si.amount_paid), 0) AS outstanding_balance, COALESCE(SUM(CASE WHEN si.due_date < CURRENT_DATE AND si.status NOT IN ('Paid', 'Voided') THEN si.total_amount - si.amount_paid ELSE 0 END), 0) AS overdue_amount, COALESCE(SUM(CASE WHEN si.status = 'Draft' THEN si.total_amount ELSE 0 END), 0) AS draft_amount, COALESCE(MAX(si.due_date), NULL) AS latest_due_date FROM business.customers c LEFT JOIN business.sales_invoices si ON c.id = si.customer_id AND si.status NOT IN ('Paid', 'Voided') GROUP BY c.id, c.customer_code, c.name;
CREATE OR REPLACE VIEW business.vendor_balances AS SELECT v.id AS vendor_id, v.vendor_code, v.name AS vendor_name, COALESCE(SUM(pi.total_amount - pi.amount_paid), 0) AS outstanding_balance, COALESCE(SUM(CASE WHEN pi.due_date < CURRENT_DATE AND pi.status NOT IN ('Paid', 'Voided') THEN pi.total_amount - pi.amount_paid ELSE 0 END), 0) AS overdue_amount, COALESCE(SUM(CASE WHEN pi.status = 'Draft' THEN pi.total_amount ELSE 0 END), 0) AS draft_amount, COALESCE(MAX(pi.due_date), NULL) AS latest_due_date FROM business.vendors v LEFT JOIN business.purchase_invoices pi ON v.id = pi.vendor_id AND pi.status NOT IN ('Paid', 'Voided') GROUP BY v.id, v.vendor_code, v.name;
CREATE OR REPLACE VIEW business.inventory_summary AS SELECT p.id AS product_id, p.product_code, p.name AS product_name, p.product_type, p.category, p.unit_of_measure, COALESCE(SUM(im.quantity), 0) AS current_quantity, CASE WHEN COALESCE(SUM(im.quantity), 0) != 0 THEN (COALESCE(SUM(im.total_cost), 0) / SUM(im.quantity)) ELSE p.purchase_price END AS average_cost, COALESCE(SUM(im.total_cost), 0) AS inventory_value, p.sales_price AS current_sales_price, p.min_stock_level, p.reorder_point, CASE WHEN p.min_stock_level IS NOT NULL AND COALESCE(SUM(im.quantity), 0) <= p.min_stock_level THEN TRUE ELSE FALSE END AS below_minimum, CASE WHEN p.reorder_point IS NOT NULL AND COALESCE(SUM(im.quantity), 0) <= p.reorder_point THEN TRUE ELSE FALSE END AS reorder_needed FROM business.products p LEFT JOIN business.inventory_movements im ON p.id = im.product_id WHERE p.product_type = 'Inventory' AND p.is_active = TRUE GROUP BY p.id, p.product_code, p.name, p.product_type, p.category, p.unit_of_measure, p.purchase_price, p.sales_price, p.min_stock_level, p.reorder_point;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================
CREATE OR REPLACE FUNCTION core.get_next_sequence_value(p_sequence_name VARCHAR) RETURNS VARCHAR AS $$ DECLARE v_sequence RECORD; v_next_value INTEGER; v_result VARCHAR; BEGIN SELECT * INTO v_sequence FROM core.sequences WHERE sequence_name = p_sequence_name FOR UPDATE; IF NOT FOUND THEN RAISE EXCEPTION 'Sequence % not found', p_sequence_name; END IF; v_next_value := v_sequence.next_value; UPDATE core.sequences SET next_value = next_value + increment_by, updated_at = CURRENT_TIMESTAMP WHERE sequence_name = p_sequence_name; v_result := v_sequence.format_template; v_result := REPLACE(v_result, '{PREFIX}', COALESCE(v_sequence.prefix, '')); v_result := REPLACE(v_result, '{VALUE}', LPAD(v_next_value::TEXT, 6, '0')); v_result := REPLACE(v_result, '{SUFFIX}', COALESCE(v_sequence.suffix, '')); RETURN v_result; END; $$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION accounting.generate_journal_entry(p_journal_type VARCHAR, p_entry_date DATE, p_description VARCHAR, p_reference VARCHAR, p_source_type VARCHAR, p_source_id INTEGER, p_lines JSONB, p_user_id INTEGER) RETURNS INTEGER AS $$ DECLARE v_fiscal_period_id INTEGER; v_entry_no VARCHAR; v_journal_id INTEGER; v_line JSONB; v_line_number INTEGER := 1; v_total_debits NUMERIC(15,2) := 0; v_total_credits NUMERIC(15,2) := 0; BEGIN SELECT id INTO v_fiscal_period_id FROM accounting.fiscal_periods WHERE p_entry_date BETWEEN start_date AND end_date AND status = 'Open'; IF v_fiscal_period_id IS NULL THEN RAISE EXCEPTION 'No open fiscal period found for date %', p_entry_date; END IF; v_entry_no := core.get_next_sequence_value('journal_entry'); INSERT INTO accounting.journal_entries (entry_no, journal_type, entry_date, fiscal_period_id, description, reference, is_posted, source_type, source_id, created_by, updated_by) VALUES (v_entry_no, p_journal_type, p_entry_date, v_fiscal_period_id, p_description, p_reference, FALSE, p_source_type, p_source_id, p_user_id, p_user_id) RETURNING id INTO v_journal_id; FOR v_line IN SELECT * FROM jsonb_array_elements(p_lines) LOOP INSERT INTO accounting.journal_entry_lines (journal_entry_id, line_number, account_id, description, debit_amount, credit_amount, currency_code, exchange_rate, tax_code, tax_amount, dimension1_id, dimension2_id) VALUES (v_journal_id, v_line_number, (v_line->>'account_id')::INTEGER, v_line->>'description', COALESCE((v_line->>'debit_amount')::NUMERIC, 0), COALESCE((v_line->>'credit_amount')::NUMERIC, 0), COALESCE(v_line->>'currency_code', 'SGD'), COALESCE((v_line->>'exchange_rate')::NUMERIC, 1), v_line->>'tax_code', COALESCE((v_line->>'tax_amount')::NUMERIC, 0), NULLIF(TRIM(v_line->>'dimension1_id'), '')::INTEGER, NULLIF(TRIM(v_line->>'dimension2_id'), '')::INTEGER); v_line_number := v_line_number + 1; v_total_debits := v_total_debits + COALESCE((v_line->>'debit_amount')::NUMERIC, 0); v_total_credits := v_total_credits + COALESCE((v_line->>'credit_amount')::NUMERIC, 0); END LOOP; IF round(v_total_debits, 2) != round(v_total_credits, 2) THEN RAISE EXCEPTION 'Journal entry is not balanced. Debits: %, Credits: %', v_total_debits, v_total_credits; END IF; RETURN v_journal_id; END; $$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION accounting.post_journal_entry(p_journal_id INTEGER, p_user_id INTEGER) RETURNS BOOLEAN AS $$ DECLARE v_fiscal_period_status VARCHAR; v_is_already_posted BOOLEAN; BEGIN SELECT is_posted INTO v_is_already_posted FROM accounting.journal_entries WHERE id = p_journal_id; IF v_is_already_posted THEN RAISE EXCEPTION 'Journal entry % is already posted', p_journal_id; END IF; SELECT fp.status INTO v_fiscal_period_status FROM accounting.journal_entries je JOIN accounting.fiscal_periods fp ON je.fiscal_period_id = fp.id WHERE je.id = p_journal_id; IF v_fiscal_period_status != 'Open' THEN RAISE EXCEPTION 'Cannot post to a closed or archived fiscal period'; END IF; UPDATE accounting.journal_entries SET is_posted = TRUE, updated_at = CURRENT_TIMESTAMP, updated_by = p_user_id WHERE id = p_journal_id; RETURN TRUE; END; $$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION accounting.calculate_account_balance(p_account_id INTEGER, p_as_of_date DATE) RETURNS NUMERIC AS $$ DECLARE v_balance NUMERIC(15,2) := 0; v_opening_balance NUMERIC(15,2); v_account_opening_balance_date DATE; BEGIN SELECT acc.opening_balance, acc.opening_balance_date INTO v_opening_balance, v_account_opening_balance_date FROM accounting.accounts acc WHERE acc.id = p_account_id; IF NOT FOUND THEN RAISE EXCEPTION 'Account with ID % not found', p_account_id; END IF; SELECT COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) INTO v_balance FROM accounting.journal_entry_lines jel JOIN accounting.journal_entries je ON jel.journal_entry_id = je.id WHERE jel.account_id = p_account_id AND je.is_posted = TRUE AND je.entry_date <= p_as_of_date AND (v_account_opening_balance_date IS NULL OR je.entry_date >= v_account_opening_balance_date); v_balance := v_balance + COALESCE(v_opening_balance, 0); RETURN v_balance; END; $$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION core.update_timestamp_trigger_func() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = CURRENT_TIMESTAMP; RETURN NEW; END; $$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION audit.log_data_change_trigger_func() RETURNS TRIGGER AS $$ DECLARE v_old_data JSONB; v_new_data JSONB; v_change_type VARCHAR(20); v_user_id INTEGER; v_entity_id INTEGER; v_entity_name VARCHAR(200); temp_val TEXT; current_field_name_from_json TEXT; BEGIN BEGIN v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER; EXCEPTION WHEN OTHERS THEN v_user_id := NULL; END; IF v_user_id IS NULL THEN IF TG_OP = 'INSERT' THEN BEGIN v_user_id := NEW.created_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END; ELSIF TG_OP = 'UPDATE' THEN BEGIN v_user_id := NEW.updated_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END; END IF; END IF; IF TG_TABLE_SCHEMA = 'audit' AND TG_TABLE_NAME IN ('audit_log', 'data_change_history') THEN RETURN NULL; END IF; IF TG_OP = 'INSERT' THEN v_change_type := 'Insert'; v_old_data := NULL; v_new_data := to_jsonb(NEW); ELSIF TG_OP = 'UPDATE' THEN v_change_type := 'Update'; v_old_data := to_jsonb(OLD); v_new_data := to_jsonb(NEW); ELSIF TG_OP = 'DELETE' THEN v_change_type := 'Delete'; v_old_data := to_jsonb(OLD); v_new_data := NULL; END IF; BEGIN IF TG_OP = 'DELETE' THEN v_entity_id := OLD.id; ELSE v_entity_id := NEW.id; END IF; EXCEPTION WHEN undefined_column THEN v_entity_id := NULL; END; BEGIN IF TG_OP = 'DELETE' THEN temp_val := CASE WHEN TG_TABLE_NAME IN ('accounts','customers','vendors','products','roles','account_types','dimensions','fiscal_years','budgets') THEN OLD.name WHEN TG_TABLE_NAME = 'journal_entries' THEN OLD.entry_no WHEN TG_TABLE_NAME = 'sales_invoices' THEN OLD.invoice_no WHEN TG_TABLE_NAME = 'purchase_invoices' THEN OLD.invoice_no WHEN TG_TABLE_NAME = 'payments' THEN OLD.payment_no WHEN TG_TABLE_NAME = 'users' THEN OLD.username WHEN TG_TABLE_NAME = 'tax_codes' THEN OLD.code WHEN TG_TABLE_NAME = 'gst_returns' THEN OLD.return_period ELSE OLD.id::TEXT END; ELSE temp_val := CASE WHEN TG_TABLE_NAME IN ('accounts','customers','vendors','products','roles','account_types','dimensions','fiscal_years','budgets') THEN NEW.name WHEN TG_TABLE_NAME = 'journal_entries' THEN NEW.entry_no WHEN TG_TABLE_NAME = 'sales_invoices' THEN NEW.invoice_no WHEN TG_TABLE_NAME = 'purchase_invoices' THEN NEW.invoice_no WHEN TG_TABLE_NAME = 'payments' THEN NEW.payment_no WHEN TG_TABLE_NAME = 'users' THEN NEW.username WHEN TG_TABLE_NAME = 'tax_codes' THEN NEW.code WHEN TG_TABLE_NAME = 'gst_returns' THEN NEW.return_period ELSE NEW.id::TEXT END; END IF; v_entity_name := temp_val; EXCEPTION WHEN undefined_column THEN BEGIN IF TG_OP = 'DELETE' THEN v_entity_name := OLD.id::TEXT; ELSE v_entity_name := NEW.id::TEXT; END IF; EXCEPTION WHEN undefined_column THEN v_entity_name := NULL; END; END; INSERT INTO audit.audit_log (user_id,action,entity_type,entity_id,entity_name,changes,timestamp) VALUES (v_user_id,v_change_type,TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,v_entity_id,v_entity_name,jsonb_build_object('old',v_old_data,'new',v_new_data),CURRENT_TIMESTAMP); IF TG_OP = 'UPDATE' THEN FOR current_field_name_from_json IN SELECT key_alias FROM jsonb_object_keys(v_old_data) AS t(key_alias) LOOP IF (v_new_data ? current_field_name_from_json) AND ((v_old_data -> current_field_name_from_json) IS DISTINCT FROM (v_new_data -> current_field_name_from_json)) THEN INSERT INTO audit.data_change_history (table_name,record_id,field_name,old_value,new_value,change_type,changed_by,changed_at) VALUES (TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,NEW.id,current_field_name_from_json,v_old_data->>current_field_name_from_json,v_new_data->>current_field_name_from_json,'Update',v_user_id,CURRENT_TIMESTAMP); END IF; END LOOP; END IF; RETURN NULL; END; $$ LANGUAGE plpgsql;
+CREATE OR REPLACE FUNCTION business.update_bank_account_balance_trigger_func() RETURNS TRIGGER AS $$ BEGIN IF TG_OP = 'INSERT' THEN UPDATE business.bank_accounts SET current_balance = current_balance + NEW.amount WHERE id = NEW.bank_account_id; ELSIF TG_OP = 'DELETE' THEN UPDATE business.bank_accounts SET current_balance = current_balance - OLD.amount WHERE id = OLD.bank_account_id; ELSIF TG_OP = 'UPDATE' THEN IF NEW.bank_account_id != OLD.bank_account_id THEN UPDATE business.bank_accounts SET current_balance = current_balance - OLD.amount WHERE id = OLD.bank_account_id; UPDATE business.bank_accounts SET current_balance = current_balance + NEW.amount WHERE id = NEW.bank_account_id; ELSE UPDATE business.bank_accounts SET current_balance = current_balance - OLD.amount + NEW.amount WHERE id = NEW.bank_account_id; END IF; END IF; RETURN NULL; END; $$ LANGUAGE plpgsql;

-- ============================================================================
-- APPLYING TRIGGERS
-- ============================================================================
DO $$ DECLARE r RECORD; BEGIN FOR r IN SELECT table_schema, table_name FROM information_schema.columns WHERE column_name = 'updated_at' AND table_schema IN ('core','accounting','business','audit') GROUP BY table_schema, table_name LOOP EXECUTE format('DROP TRIGGER IF EXISTS trg_update_timestamp ON %I.%I; CREATE TRIGGER trg_update_timestamp BEFORE UPDATE ON %I.%I FOR EACH ROW EXECUTE FUNCTION core.update_timestamp_trigger_func();',r.table_schema,r.table_name,r.table_schema,r.table_name); END LOOP; END; $$;
DO $$ DECLARE tables_to_audit TEXT[] := ARRAY['accounting.accounts','accounting.journal_entries','accounting.fiscal_periods','accounting.fiscal_years','business.customers','business.vendors','business.products','business.sales_invoices','business.purchase_invoices','business.payments','accounting.tax_codes','accounting.gst_returns','core.users','core.roles','core.company_settings', 'business.bank_accounts', 'business.bank_transactions']; table_fullname TEXT; schema_name TEXT; table_name_var TEXT; BEGIN FOREACH table_fullname IN ARRAY tables_to_audit LOOP SELECT split_part(table_fullname,'.',1) INTO schema_name; SELECT split_part(table_fullname,'.',2) INTO table_name_var; EXECUTE format('DROP TRIGGER IF EXISTS trg_audit_log ON %I.%I; CREATE TRIGGER trg_audit_log AFTER INSERT OR UPDATE OR DELETE ON %I.%I FOR EACH ROW EXECUTE FUNCTION audit.log_data_change_trigger_func();',schema_name,table_name_var,schema_name,table_name_var); END LOOP; END; $$;
DROP TRIGGER IF EXISTS trg_update_bank_balance ON business.bank_transactions; CREATE TRIGGER trg_update_bank_balance AFTER INSERT OR UPDATE OR DELETE ON business.bank_transactions FOR EACH ROW EXECUTE FUNCTION business.update_bank_account_balance_trigger_func();
 
 -- End of script
```
