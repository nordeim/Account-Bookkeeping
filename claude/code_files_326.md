<think>
The user wants me to update two specific SQL files: `scripts/schema.sql` and `scripts/initial_data.sql`.
The updates need to incorporate changes from a provided `schema_update_patch.sql` file, which seems to contain two patches (one from 1.0.3 to 1.0.4, and another from 1.0.4 to 1.0.5).
The `project_codebase_scripts_files.md` contains the original versions of `scripts/schema.sql` (labelled as v1.0.3), `scripts/initial_data.sql` (labelled as v1.0.3), and the content of `schema_update_patch.sql`.

My goal is to produce the "final" versions of `schema.sql` and `initial_data.sql` that would represent schema version 1.0.5.

**Plan:**

1.  **Analyze `schema_update_patch.sql`:**
    *   The patch file has two distinct parts, separated by a `COMMIT;` and comments.
    *   **Part 1 (1.0.3 to 1.0.4):**
        *   Creates `business.bank_reconciliations` table.
        *   Adds `last_reconciled_balance` to `business.bank_accounts`.
        *   Adds `reconciled_bank_reconciliation_id` to `business.bank_transactions`.
        *   Adds FK constraints for these new elements.
    *   **Part 2 (1.0.4 to 1.0.5):**
        *   Adds `status VARCHAR(20) NOT NULL DEFAULT 'Draft'` to `business.bank_reconciliations`.
        *   Adds a `CHECK` constraint `ck_bank_reconciliations_status` for this new `status` column.

2.  **Update `scripts/schema.sql`:**
    *   The provided `scripts/schema.sql` is labelled as "Complete Database Schema - Version 1.0.3". This version already includes:
        *   `is_from_statement` and `raw_statement_data` in `business.bank_transactions` (mentioned as changes from 1.0.1 incorporated in 1.0.2, and schema is 1.0.3).
        *   Trigger `business.update_bank_account_balance_trigger_func()` (mentioned as from 1.0.1 incorporated in 1.0.2).
        *   Audit logging extended to `bank_accounts` and `bank_transactions`.
    *   I need to integrate the changes from **both parts** of `schema_update_patch.sql` into this base `scripts/schema.sql`.
    *   **Specifically for `scripts/schema.sql` update:**
        *   **Patch 1 (1.0.3 -> 1.0.4 changes):**
            *   The `business.bank_reconciliations` table definition needs to be added in the "BUSINESS SCHEMA TABLES" section.
            *   The `ALTER TABLE business.bank_accounts ADD COLUMN IF NOT EXISTS last_reconciled_balance...` needs to be integrated into the `CREATE TABLE business.bank_accounts` definition. The original `schema.sql` for `bank_accounts` is:
                ```sql
                CREATE TABLE business.bank_accounts (
                    id SERIAL PRIMARY KEY, account_name VARCHAR(100) NOT NULL, account_number VARCHAR(50) NOT NULL, bank_name VARCHAR(100) NOT NULL, bank_branch VARCHAR(100), bank_swift_code VARCHAR(20), currency_code CHAR(3) NOT NULL, opening_balance NUMERIC(15,2) DEFAULT 0, current_balance NUMERIC(15,2) DEFAULT 0, last_reconciled_date DATE, gl_account_id INTEGER NOT NULL, is_active BOOLEAN DEFAULT TRUE, description TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
                ```
                I need to add `last_reconciled_balance NUMERIC(15,2) NULL`.
            *   The `ALTER TABLE business.bank_transactions ADD COLUMN IF NOT EXISTS reconciled_bank_reconciliation_id...` needs to be integrated into the `CREATE TABLE business.bank_transactions` definition. The original `schema.sql` for `bank_transactions` already has `is_from_statement` and `raw_statement_data`.
                ```sql
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
                    is_from_statement BOOLEAN NOT NULL DEFAULT FALSE, -- New column (from 1.0.2)
                    raw_statement_data JSONB NULL, -- New column (from 1.0.2)
                    journal_entry_id INTEGER, 
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
                    created_by INTEGER NOT NULL, 
                    updated_by INTEGER NOT NULL
                );
                ```
                I need to add `reconciled_bank_reconciliation_id INT NULL`.
            *   The FK constraints from the patch for `bank_reconciliations` and `bank_transactions.reconciled_bank_reconciliation_id` need to be added in the "ADDING FOREIGN KEY CONSTRAINTS" section.
        *   **Patch 2 (1.0.4 -> 1.0.5 changes):**
            *   The `ALTER TABLE business.bank_reconciliations ADD COLUMN IF NOT EXISTS status...` and its `CHECK` constraint need to be integrated directly into the `CREATE TABLE business.bank_reconciliations` definition that I'm adding from Patch 1.
        *   Update the version comment at the top of `schema.sql` to reflect "Version 1.0.5" and summarize the changes incorporated.

3.  **Update `scripts/initial_data.sql`:**
    *   The provided `scripts/initial_data.sql` is labelled as "Version 1.0.3".
    *   The `schema_update_patch.sql` primarily deals with DDL (schema changes) and doesn't seem to contain DML (data changes) that would directly affect `initial_data.sql`.
    *   However, new tables or columns might necessitate new default permissions or configurations if they were part of a complete feature rollout.
    *   **Key things to check/consider for `initial_data.sql`:**
        *   **Permissions:** The `bank_reconciliations` table is new. Are there new permissions related to managing/viewing reconciliations? The patch doesn't add permissions. The original `initial_data.sql` *already* has:
            ```sql
            ('BANK_RECONCILE', 'Reconcile bank accounts', 'Banking'),
            ('BANK_STATEMENT_IMPORT', 'Import bank statements', 'Banking'),
            ```
            These permissions seem to cover the functionality introduced by the schema patches. So, no new permissions seem strictly required by the *patch file content itself*.
        *   **Configuration:** Are there any new `core.configuration` entries needed for the reconciliation feature? The patch doesn't add any.
        *   **Default Data:** Does the new `bank_reconciliations` table need any default entries? Unlikely for this kind of table.
        *   **Sequence Grants:** The `initial_data.sql` has a comment "Version 1.0.3 - Added sequence grants for audit schema". The patch doesn't modify sequences. The new `bank_reconciliations` table has `id SERIAL PRIMARY KEY`, so `sgbookkeeper_user` will need `USAGE, SELECT` on its sequence. The existing `GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA business TO sgbookkeeper_user;` and the `ALTER DEFAULT PRIVILEGES` should cover this new sequence automatically if the table is created before grants are applied or if grants are broad enough.
            The `GRANT ... ON ALL TABLES IN SCHEMA business` will also cover the new table.
    *   **Conclusion for `initial_data.sql`**: Based purely on the `schema_update_patch.sql`, there are no direct DML changes. The main task is to update the version comment. If I assume the permissions already in `initial_data.sql` (like `BANK_RECONCILE`) were forward-looking or added as part of the 1.0.3 feature set whose schema parts are now being fully defined, then `initial_data.sql` might only need a version bump in its comment.
    *   I will double check if any existing permissions relate to the new `status` column on `bank_reconciliations` (e.g., a permission to finalize a reconciliation). The existing `BANK_RECONCILE` is broad and likely covers this.

4.  **Perform Line-by-Line "Diff" (Mental or Actual):**
    *   Once I've drafted the new versions of `schema.sql` and `initial_data.sql`, I will carefully compare them to their original versions from `project_codebase_scripts_files.md` to ensure:
        *   No original, harmless lines are accidentally omitted.
        *   Only the intended changes from the patch are incorporated.
        *   The structure and existing content are preserved as much as possible.

**Detailed `schema.sql` update process:**

*   Locate `CREATE TABLE business.bank_accounts`. Add `last_reconciled_balance NUMERIC(15,2) NULL,` before the `gl_account_id` or another suitable place.
*   Locate `CREATE TABLE business.bank_transactions`. Add `reconciled_bank_reconciliation_id INT NULL,` before `journal_entry_id` or another suitable place. (It already has `is_from_statement` and `raw_statement_data`).
*   Add the new table definition for `business.bank_reconciliations` in the "BUSINESS SCHEMA TABLES" section. This definition should include the `status VARCHAR(20) NOT NULL DEFAULT 'Draft'` and the `CONSTRAINT ck_bank_reconciliations_status CHECK (status IN ('Draft', 'Finalized'))` directly.
    ```sql
    CREATE TABLE business.bank_reconciliations (
        id SERIAL PRIMARY KEY,
        bank_account_id INTEGER NOT NULL,
        statement_date DATE NOT NULL,
        statement_ending_balance NUMERIC(15,2) NOT NULL,
        calculated_book_balance NUMERIC(15,2) NOT NULL,
        reconciled_difference NUMERIC(15,2) NOT NULL,
        reconciliation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        notes TEXT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'Draft', -- Added from 1.0.5 patch
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        created_by_user_id INTEGER NOT NULL,
        CONSTRAINT uq_bank_reconciliation_account_statement_date UNIQUE (bank_account_id, statement_date),
        CONSTRAINT ck_bank_reconciliations_status CHECK (status IN ('Draft', 'Finalized')) -- Added from 1.0.5 patch
    );
    ```
*   Add comments for the new table and columns as specified in the patch.
*   In the "ADDING FOREIGN KEY CONSTRAINTS" section, under "Business Schema FKs", add the new FKs:
    ```sql
    -- FKs for business.bank_reconciliations
    ALTER TABLE business.bank_reconciliations ADD CONSTRAINT fk_br_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id) ON DELETE CASCADE;
    ALTER TABLE business.bank_reconciliations ADD CONSTRAINT fk_br_created_by FOREIGN KEY (created_by_user_id) REFERENCES core.users(id);

    -- FK for business.bank_transactions.reconciled_bank_reconciliation_id
    ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_reconciliation FOREIGN KEY (reconciled_bank_reconciliation_id) REFERENCES business.bank_reconciliations(id) ON DELETE SET NULL;
    ```
*   Update the top comment in `schema.sql` to:
    ```sql
    -- File: scripts/schema.sql
    -- ============================================================================
    -- SG Bookkeeper - Complete Database Schema - Version 1.0.5
    -- Changes from 1.0.3 (this file's base):
    --  - Added business.bank_reconciliations table (for saving reconciliation state).
    --  - Added last_reconciled_balance to business.bank_accounts.
    --  - Added reconciled_bank_reconciliation_id to business.bank_transactions.
    --  - Added status (Draft/Finalized) to business.bank_reconciliations.
    --  - Added relevant FK constraints.
    -- (Schema version 1.0.3 itself included bank_transactions fields for import, bank balance trigger, corrected trial_balance view)
    -- ============================================================================
    ```

**Detailed `initial_data.sql` update process:**

*   The only change needed for `initial_data.sql` based on the patch file and existing content is to update the version comment at the top. The permissions `BANK_RECONCILE` and `BANK_STATEMENT_IMPORT` are already present. No new configuration values or default data for `bank_reconciliations` are implied by the patch.
*   Update the top comment in `initial_data.sql` to:
    ```sql
    -- File: scripts/initial_data.sql
    -- ============================================================================
    -- INITIAL DATA (Version 1.0.5 - Corresponds to schema version 1.0.5)
    -- (No data changes directly from schema patches 1.0.4/1.0.5, permissions for banking/reconciliation features were already present)
    -- ============================================================================
    ```
    Or maybe more simply:
    ```sql
    -- File: scripts/initial_data.sql
    -- ============================================================================
    -- INITIAL DATA (Version 1.0.5)
    -- Corresponds to schema version 1.0.5.
    -- Previous version 1.0.3 added sequence grants for audit schema.
    -- No functional data changes in this version, version bump for consistency.
    -- ============================================================================
    ```
This looks like a solid plan. I will proceed with generating the updated files. I need to be very careful with copy-pasting and integrating, ensuring the final SQL is valid and complete.
The `db_init.py` and its `__pycache__` file are listed in the user's prompt "list of files to update..." but the actual request is "create for me a *complete* updated replacement files for `scripts/schema.sql` and `scripts/initial_data.sql`". So I will only provide these two SQL files.

One final check on the schema version comment in `schema.sql`. The original file is 1.0.3. The first patch takes it to 1.0.4. The second patch takes it to 1.0.5. So the final `schema.sql` should indeed be 1.0.5.
The original comment in `schema.sql` states:
```sql
-- File: scripts/schema.sql
-- ============================================================================
-- SG Bookkeeper - Complete Database Schema - Version 1.0.3
-- (Schema version updated for bank_transactions fields & corrected trial_balance view)
-- ============================================================================
-- This script creates the complete database schema for the SG Bookkeeper application.
-- Changes from 1.0.2:
--  - Corrected accounting.trial_balance view logic.
-- Changes from 1.0.1 (incorporated in 1.0.2):
--  - Added is_from_statement and raw_statement_data to business.bank_transactions
--  - Added trigger for automatic bank_account balance updates.
--  - Extended audit logging to bank_accounts and bank_transactions.
-- ============================================================================
```
My proposed new comment for 1.0.5 should build on this, explaining what 1.0.4 and 1.0.5 introduced *on top of* 1.0.3.

Revised schema header comment:
```sql
-- File: scripts/schema.sql
-- ============================================================================
-- SG Bookkeeper - Complete Database Schema - Version 1.0.5
-- ============================================================================
-- This script creates the complete database schema for the SG Bookkeeper application.
-- Base version for this consolidated file was 1.0.3.
--
-- Changes from 1.0.3 to 1.0.4 (incorporated):
--  - Added business.bank_reconciliations table (for saving reconciliation state).
--  - Added last_reconciled_balance to business.bank_accounts.
--  - Added reconciled_bank_reconciliation_id to business.bank_transactions.
--  - Added relevant FK constraints for reconciliation features.
--
-- Changes from 1.0.4 to 1.0.5 (incorporated):
--  - Added status VARCHAR(20) NOT NULL DEFAULT 'Draft' with CHECK constraint to business.bank_reconciliations.
--
-- Features from 1.0.3 (base for this file):
--  - Schema version updated for bank_transactions fields (is_from_statement, raw_statement_data) & corrected trial_balance view logic.
--  - Trigger for automatic bank_account balance updates.
--  - Extended audit logging to bank_accounts and bank_transactions.
-- ============================================================================
```
This revised header is more explicit about the lineage.

For `initial_data.sql`, the original header is:
```sql
-- File: scripts/initial_data.sql
-- ============================================================================
-- INITIAL DATA (Version 1.0.3 - Added sequence grants for audit schema)
-- ============================================================================
```
My proposed new header for `initial_data.sql`:
```sql
-- File: scripts/initial_data.sql
-- ============================================================================
-- INITIAL DATA (Version 1.0.5)
-- ============================================================================
-- This version corresponds to schema version 1.0.5.
-- No functional data changes were introduced by schema patches 1.0.4 or 1.0.5.
-- Existing permissions for banking/reconciliation were already present in v1.0.3.
-- Version 1.0.3 (base) added sequence grants for audit schema.
-- ============================================================================
```
This also clarifies the state of `initial_data.sql`.

Looks good. I'll generate the files.Okay, I have carefully reviewed the `project_codebase_scripts_files.md` and the task to update `scripts/schema.sql` and `scripts/initial_data.sql` by incorporating the changes from `schema_update_patch.sql`.

My process involved:
1.  Analyzing the two distinct patches within `schema_update_patch.sql` (1.0.3 -> 1.0.4, and 1.0.4 -> 1.0.5).
2.  Identifying the DDL changes (table creations, column additions, constraint additions) from these patches.
3.  Integrating these DDL changes directly into the base `scripts/schema.sql` (which was at v1.0.3). This means new tables are fully defined with all columns (including those from later patches) in one `CREATE TABLE` statement, and new columns are added to existing `CREATE TABLE` statements.
4.  Ensuring all foreign key constraints from the patches are added to the appropriate section in `schema.sql`.
5.  Updating the version comments at the top of `scripts/schema.sql` to reflect its new state (v1.0.5) and summarize the incorporated changes.
6.  For `scripts/initial_data.sql`, I confirmed that the schema patches did not introduce new data requirements (like new permissions or configuration values that weren't already covered). The primary change is updating the version comment for consistency with the schema.
7.  I performed a mental line-by-line "diff" during this integration to ensure that all original content from the base files was preserved and that changes were applied correctly and seamlessly.

Here are the complete updated replacement files:

---

**File 1: `scripts/schema.sql` (Updated to Version 1.0.5)**

```sql
-- File: scripts/schema.sql
-- ============================================================================
-- SG Bookkeeper - Complete Database Schema - Version 1.0.5
-- ============================================================================
-- This script creates the complete database schema for the SG Bookkeeper application.
-- Base version for this consolidated file was 1.0.3.
--
-- Changes from 1.0.3 to 1.0.4 (incorporated):
--  - Added business.bank_reconciliations table (for saving reconciliation state).
--  - Added last_reconciled_balance to business.bank_accounts.
--  - Added reconciled_bank_reconciliation_id to business.bank_transactions.
--  - Added relevant FK constraints for reconciliation features.
--
-- Changes from 1.0.4 to 1.0.5 (incorporated):
--  - Added status VARCHAR(20) NOT NULL DEFAULT 'Draft' with CHECK constraint to business.bank_reconciliations.
--
-- Features from 1.0.3 (base for this file):
--  - Schema version updated for bank_transactions fields (is_from_statement, raw_statement_data) & corrected trial_balance view logic.
--  - Trigger for automatic bank_account balance updates.
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
CREATE TABLE business.customers (
    id SERIAL PRIMARY KEY, customer_code VARCHAR(20) NOT NULL UNIQUE, name VARCHAR(100) NOT NULL, legal_name VARCHAR(200), uen_no VARCHAR(20), gst_registered BOOLEAN DEFAULT FALSE, gst_no VARCHAR(20), contact_person VARCHAR(100), email VARCHAR(100), phone VARCHAR(20), address_line1 VARCHAR(100), address_line2 VARCHAR(100), postal_code VARCHAR(20), city VARCHAR(50), country VARCHAR(50) DEFAULT 'Singapore', credit_terms INTEGER DEFAULT 30, credit_limit NUMERIC(15,2), currency_code CHAR(3) DEFAULT 'SGD', is_active BOOLEAN DEFAULT TRUE, customer_since DATE, notes TEXT, receivables_account_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_customers_name ON business.customers(name); CREATE INDEX idx_customers_is_active ON business.customers(is_active);

CREATE TABLE business.vendors (
    id SERIAL PRIMARY KEY, vendor_code VARCHAR(20) NOT NULL UNIQUE, name VARCHAR(100) NOT NULL, legal_name VARCHAR(200), uen_no VARCHAR(20), gst_registered BOOLEAN DEFAULT FALSE, gst_no VARCHAR(20), withholding_tax_applicable BOOLEAN DEFAULT FALSE, withholding_tax_rate NUMERIC(5,2), contact_person VARCHAR(100), email VARCHAR(100), phone VARCHAR(20), address_line1 VARCHAR(100), address_line2 VARCHAR(100), postal_code VARCHAR(20), city VARCHAR(50), country VARCHAR(50) DEFAULT 'Singapore', payment_terms INTEGER DEFAULT 30, currency_code CHAR(3) DEFAULT 'SGD', is_active BOOLEAN DEFAULT TRUE, vendor_since DATE, notes TEXT, bank_account_name VARCHAR(100), bank_account_number VARCHAR(50), bank_name VARCHAR(100), bank_branch VARCHAR(100), bank_swift_code VARCHAR(20), payables_account_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_vendors_name ON business.vendors(name); CREATE INDEX idx_vendors_is_active ON business.vendors(is_active);

CREATE TABLE business.products (
    id SERIAL PRIMARY KEY, product_code VARCHAR(20) NOT NULL UNIQUE, name VARCHAR(100) NOT NULL, description TEXT, product_type VARCHAR(20) NOT NULL CHECK (product_type IN ('Inventory', 'Service', 'Non-Inventory')), category VARCHAR(50), unit_of_measure VARCHAR(20), barcode VARCHAR(50), sales_price NUMERIC(15,2), purchase_price NUMERIC(15,2), sales_account_id INTEGER, purchase_account_id INTEGER, inventory_account_id INTEGER, tax_code VARCHAR(20), is_active BOOLEAN DEFAULT TRUE, min_stock_level NUMERIC(15,2), reorder_point NUMERIC(15,2), created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_products_name ON business.products(name); CREATE INDEX idx_products_is_active ON business.products(is_active); CREATE INDEX idx_products_type ON business.products(product_type);

CREATE TABLE business.inventory_movements (
    id SERIAL PRIMARY KEY, product_id INTEGER NOT NULL, movement_date DATE NOT NULL, movement_type VARCHAR(20) NOT NULL CHECK (movement_type IN ('Purchase', 'Sale', 'Adjustment', 'Transfer', 'Return', 'Opening')), quantity NUMERIC(15,2) NOT NULL, unit_cost NUMERIC(15,4), total_cost NUMERIC(15,2), reference_type VARCHAR(50), reference_id INTEGER, notes TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL);
CREATE INDEX idx_inventory_movements_product ON business.inventory_movements(product_id, movement_date); CREATE INDEX idx_inventory_movements_reference ON business.inventory_movements(reference_type, reference_id);

CREATE TABLE business.sales_invoices (
    id SERIAL PRIMARY KEY, invoice_no VARCHAR(20) NOT NULL UNIQUE, customer_id INTEGER NOT NULL, invoice_date DATE NOT NULL, due_date DATE NOT NULL, currency_code CHAR(3) NOT NULL, exchange_rate NUMERIC(15,6) DEFAULT 1, subtotal NUMERIC(15,2) NOT NULL, tax_amount NUMERIC(15,2) NOT NULL DEFAULT 0, total_amount NUMERIC(15,2) NOT NULL, amount_paid NUMERIC(15,2) NOT NULL DEFAULT 0, status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Approved', 'Sent', 'Partially Paid', 'Paid', 'Overdue', 'Voided')), notes TEXT, terms_and_conditions TEXT, journal_entry_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_sales_invoices_customer ON business.sales_invoices(customer_id); CREATE INDEX idx_sales_invoices_dates ON business.sales_invoices(invoice_date, due_date); CREATE INDEX idx_sales_invoices_status ON business.sales_invoices(status);

CREATE TABLE business.sales_invoice_lines (
    id SERIAL PRIMARY KEY, invoice_id INTEGER NOT NULL, line_number INTEGER NOT NULL, product_id INTEGER, description VARCHAR(200) NOT NULL, quantity NUMERIC(15,2) NOT NULL, unit_price NUMERIC(15,2) NOT NULL, discount_percent NUMERIC(5,2) DEFAULT 0, discount_amount NUMERIC(15,2) DEFAULT 0, line_subtotal NUMERIC(15,2) NOT NULL, tax_code VARCHAR(20), tax_amount NUMERIC(15,2) DEFAULT 0, line_total NUMERIC(15,2) NOT NULL, dimension1_id INTEGER, dimension2_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_sales_invoice_lines_invoice ON business.sales_invoice_lines(invoice_id); CREATE INDEX idx_sales_invoice_lines_product ON business.sales_invoice_lines(product_id);

CREATE TABLE business.purchase_invoices (
    id SERIAL PRIMARY KEY, invoice_no VARCHAR(20) NOT NULL UNIQUE, vendor_id INTEGER NOT NULL, vendor_invoice_no VARCHAR(50), invoice_date DATE NOT NULL, due_date DATE NOT NULL, currency_code CHAR(3) NOT NULL, exchange_rate NUMERIC(15,6) DEFAULT 1, subtotal NUMERIC(15,2) NOT NULL, tax_amount NUMERIC(15,2) NOT NULL DEFAULT 0, total_amount NUMERIC(15,2) NOT NULL, amount_paid NUMERIC(15,2) NOT NULL DEFAULT 0, status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Approved', 'Partially Paid', 'Paid', 'Overdue', 'Disputed', 'Voided')), notes TEXT, journal_entry_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_purchase_invoices_vendor ON business.purchase_invoices(vendor_id); CREATE INDEX idx_purchase_invoices_dates ON business.purchase_invoices(invoice_date, due_date); CREATE INDEX idx_purchase_invoices_status ON business.purchase_invoices(status);

CREATE TABLE business.purchase_invoice_lines (
    id SERIAL PRIMARY KEY, invoice_id INTEGER NOT NULL, line_number INTEGER NOT NULL, product_id INTEGER, description VARCHAR(200) NOT NULL, quantity NUMERIC(15,2) NOT NULL, unit_price NUMERIC(15,2) NOT NULL, discount_percent NUMERIC(5,2) DEFAULT 0, discount_amount NUMERIC(15,2) DEFAULT 0, line_subtotal NUMERIC(15,2) NOT NULL, tax_code VARCHAR(20), tax_amount NUMERIC(15,2) DEFAULT 0, line_total NUMERIC(15,2) NOT NULL, dimension1_id INTEGER, dimension2_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_purchase_invoice_lines_invoice ON business.purchase_invoice_lines(invoice_id); CREATE INDEX idx_purchase_invoice_lines_product ON business.purchase_invoice_lines(product_id);

CREATE TABLE business.bank_accounts (
    id SERIAL PRIMARY KEY, 
    account_name VARCHAR(100) NOT NULL, 
    account_number VARCHAR(50) NOT NULL, 
    bank_name VARCHAR(100) NOT NULL, 
    bank_branch VARCHAR(100), 
    bank_swift_code VARCHAR(20), 
    currency_code CHAR(3) NOT NULL, 
    opening_balance NUMERIC(15,2) DEFAULT 0, 
    current_balance NUMERIC(15,2) DEFAULT 0, 
    last_reconciled_date DATE, 
    last_reconciled_balance NUMERIC(15,2) NULL, -- Added from 1.0.4 patch
    gl_account_id INTEGER NOT NULL, 
    is_active BOOLEAN DEFAULT TRUE, 
    description TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
    created_by INTEGER NOT NULL, 
    updated_by INTEGER NOT NULL
);
COMMENT ON COLUMN business.bank_accounts.last_reconciled_balance IS 'The ending balance of the bank account as per the last successfully completed reconciliation.';

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
    is_from_statement BOOLEAN NOT NULL DEFAULT FALSE, -- From 1.0.2
    raw_statement_data JSONB NULL, -- From 1.0.2
    reconciled_bank_reconciliation_id INT NULL, -- Added from 1.0.4 patch
    journal_entry_id INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
    created_by INTEGER NOT NULL, 
    updated_by INTEGER NOT NULL
);
CREATE INDEX idx_bank_transactions_account ON business.bank_transactions(bank_account_id); 
CREATE INDEX idx_bank_transactions_date ON business.bank_transactions(transaction_date); 
CREATE INDEX idx_bank_transactions_reconciled ON business.bank_transactions(is_reconciled);
COMMENT ON COLUMN business.bank_transactions.reconciled_bank_reconciliation_id IS 'Foreign key to business.bank_reconciliations, linking a transaction to the specific reconciliation it was cleared in.';

CREATE TABLE business.bank_reconciliations (
    id SERIAL PRIMARY KEY,
    bank_account_id INTEGER NOT NULL,
    statement_date DATE NOT NULL, 
    statement_ending_balance NUMERIC(15,2) NOT NULL,
    calculated_book_balance NUMERIC(15,2) NOT NULL, 
    reconciled_difference NUMERIC(15,2) NOT NULL, 
    reconciliation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
    notes TEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Draft', -- Added from 1.0.5 patch
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER NOT NULL,
    CONSTRAINT uq_bank_reconciliation_account_statement_date UNIQUE (bank_account_id, statement_date),
    CONSTRAINT ck_bank_reconciliations_status CHECK (status IN ('Draft', 'Finalized')) -- Added from 1.0.5 patch
);
COMMENT ON TABLE business.bank_reconciliations IS 'Stores summary records of completed bank reconciliations.';
COMMENT ON COLUMN business.bank_reconciliations.statement_date IS 'The end date of the bank statement that was reconciled.';
COMMENT ON COLUMN business.bank_reconciliations.calculated_book_balance IS 'The book balance of the bank account as of the statement_date, after all reconciling items for this reconciliation are accounted for.';
COMMENT ON COLUMN business.bank_reconciliations.status IS 'The status of the reconciliation, e.g., Draft, Finalized. Default is Draft.';


CREATE TABLE business.payments (
    id SERIAL PRIMARY KEY, payment_no VARCHAR(20) NOT NULL UNIQUE, payment_type VARCHAR(20) NOT NULL CHECK (payment_type IN ('Customer Payment', 'Vendor Payment', 'Refund', 'Credit Note', 'Other')), payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('Cash', 'Check', 'Bank Transfer', 'Credit Card', 'GIRO', 'PayNow', 'Other')), payment_date DATE NOT NULL, entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('Customer', 'Vendor', 'Other')), entity_id INTEGER NOT NULL, bank_account_id INTEGER, currency_code CHAR(3) NOT NULL, exchange_rate NUMERIC(15,6) DEFAULT 1, amount NUMERIC(15,2) NOT NULL, reference VARCHAR(100), description TEXT, cheque_no VARCHAR(50), status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Approved', 'Completed', 'Voided', 'Returned')), journal_entry_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_payments_date ON business.payments(payment_date); CREATE INDEX idx_payments_entity ON business.payments(entity_type, entity_id); CREATE INDEX idx_payments_status ON business.payments(status);

CREATE TABLE business.payment_allocations (
    id SERIAL PRIMARY KEY, payment_id INTEGER NOT NULL, document_type VARCHAR(20) NOT NULL CHECK (document_type IN ('Sales Invoice', 'Purchase Invoice', 'Credit Note', 'Debit Note', 'Other')), document_id INTEGER NOT NULL, amount NUMERIC(15,2) NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL);
CREATE INDEX idx_payment_allocations_payment ON business.payment_allocations(payment_id); CREATE INDEX idx_payment_allocations_document ON business.payment_allocations(document_type, document_id);

-- ============================================================================
-- AUDIT SCHEMA TABLES
-- ============================================================================
CREATE TABLE audit.audit_log (
    id SERIAL PRIMARY KEY, user_id INTEGER, action VARCHAR(50) NOT NULL, entity_type VARCHAR(50) NOT NULL, entity_id INTEGER, entity_name VARCHAR(200), changes JSONB, ip_address VARCHAR(45), user_agent VARCHAR(255), timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_audit_log_user ON audit.audit_log(user_id); CREATE INDEX idx_audit_log_entity ON audit.audit_log(entity_type, entity_id); CREATE INDEX idx_audit_log_timestamp ON audit.audit_log(timestamp);

CREATE TABLE audit.data_change_history (
    id SERIAL PRIMARY KEY, table_name VARCHAR(100) NOT NULL, record_id INTEGER NOT NULL, field_name VARCHAR(100) NOT NULL, old_value TEXT, new_value TEXT, change_type VARCHAR(20) NOT NULL CHECK (change_type IN ('Insert', 'Update', 'Delete')), changed_by INTEGER, changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX idx_data_change_history_table_record ON audit.data_change_history(table_name, record_id); CREATE INDEX idx_data_change_history_changed_at ON audit.data_change_history(changed_at);

-- ============================================================================
-- ADDING FOREIGN KEY CONSTRAINTS 
-- ============================================================================
-- Core Schema FKs
ALTER TABLE core.role_permissions ADD CONSTRAINT fk_rp_role FOREIGN KEY (role_id) REFERENCES core.roles(id) ON DELETE CASCADE;
ALTER TABLE core.role_permissions ADD CONSTRAINT fk_rp_permission FOREIGN KEY (permission_id) REFERENCES core.permissions(id) ON DELETE CASCADE;
ALTER TABLE core.user_roles ADD CONSTRAINT fk_ur_user FOREIGN KEY (user_id) REFERENCES core.users(id) ON DELETE CASCADE;
ALTER TABLE core.user_roles ADD CONSTRAINT fk_ur_role FOREIGN KEY (role_id) REFERENCES core.roles(id) ON DELETE CASCADE;
ALTER TABLE core.company_settings ADD CONSTRAINT fk_cs_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
ALTER TABLE core.company_settings ADD CONSTRAINT fk_cs_base_currency FOREIGN KEY (base_currency) REFERENCES accounting.currencies(code);
ALTER TABLE core.configuration ADD CONSTRAINT fk_cfg_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

-- Accounting Schema FKs
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

-- Business Schema FKs
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
ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_reconciliation FOREIGN KEY (reconciled_bank_reconciliation_id) REFERENCES business.bank_reconciliations(id) ON DELETE SET NULL; -- Added from 1.0.4 patch
ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE business.bank_reconciliations ADD CONSTRAINT fk_br_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id) ON DELETE CASCADE; -- Added from 1.0.4 patch
ALTER TABLE business.bank_reconciliations ADD CONSTRAINT fk_br_created_by FOREIGN KEY (created_by_user_id) REFERENCES core.users(id); -- Added from 1.0.4 patch

ALTER TABLE business.payments ADD CONSTRAINT fk_pay_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE business.payment_allocations ADD CONSTRAINT fk_pa_payment FOREIGN KEY (payment_id) REFERENCES business.payments(id) ON DELETE CASCADE;
ALTER TABLE business.payment_allocations ADD CONSTRAINT fk_pa_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);

-- Audit Schema FKs
ALTER TABLE audit.audit_log ADD CONSTRAINT fk_al_user FOREIGN KEY (user_id) REFERENCES core.users(id);
ALTER TABLE audit.data_change_history ADD CONSTRAINT fk_dch_changed_by FOREIGN KEY (changed_by) REFERENCES core.users(id);

-- ============================================================================
-- VIEWS
-- ============================================================================
CREATE OR REPLACE VIEW accounting.account_balances AS
SELECT 
    a.id AS account_id,
    a.code AS account_code,
    a.name AS account_name,
    a.account_type,
    a.parent_id,
    -- balance is calculated as: opening_balance + sum_of_debits - sum_of_credits
    -- where debits increase balance and credits decrease balance (for Asset/Expense view)
    -- or credits increase balance and debits decrease balance (for Liability/Equity/Revenue view)
    -- The current logic `SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END)`
    -- effectively sums (debits - credits), so a positive result is a net debit movement.
    COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) + a.opening_balance AS balance,
    COALESCE(SUM(jel.debit_amount), 0) AS total_debits_activity, -- Sum of all debit lines
    COALESCE(SUM(jel.credit_amount), 0) AS total_credits_activity, -- Sum of all credit lines
    MAX(je.entry_date) AS last_activity_date
FROM accounting.accounts a
LEFT JOIN accounting.journal_entry_lines jel ON a.id = jel.account_id
LEFT JOIN accounting.journal_entries je ON jel.journal_entry_id = je.id AND je.is_posted = TRUE
GROUP BY a.id, a.code, a.name, a.account_type, a.parent_id, a.opening_balance;

-- Corrected Trial Balance View
CREATE OR REPLACE VIEW accounting.trial_balance AS
SELECT 
    a.id AS account_id,
    a.code AS account_code,
    a.name AS account_name,
    a.account_type,
    a.sub_type,
    -- If ab.balance (net debit actual balance) > 0, it's a debit balance.
    -- If ab.balance (net credit actual balance) < 0, it's a credit balance (-ab.balance).
    CASE 
        WHEN ab.balance > 0 THEN ab.balance 
        ELSE 0 
    END AS debit_balance,
    CASE 
        WHEN ab.balance < 0 THEN -ab.balance -- Show as positive in credit column
        ELSE 0 
    END AS credit_balance
FROM accounting.accounts a
JOIN accounting.account_balances ab ON a.id = ab.account_id
WHERE a.is_active = TRUE AND ab.balance != 0; -- Only show active accounts with non-zero balances

CREATE OR REPLACE VIEW business.customer_balances AS
SELECT c.id AS customer_id, c.customer_code, c.name AS customer_name,
    COALESCE(SUM(si.total_amount - si.amount_paid), 0) AS outstanding_balance,
    COALESCE(SUM(CASE WHEN si.due_date < CURRENT_DATE AND si.status NOT IN ('Paid', 'Voided') THEN si.total_amount - si.amount_paid ELSE 0 END), 0) AS overdue_amount,
    COALESCE(SUM(CASE WHEN si.status = 'Draft' THEN si.total_amount ELSE 0 END), 0) AS draft_amount,
    COALESCE(MAX(si.due_date), NULL) AS latest_due_date
FROM business.customers c LEFT JOIN business.sales_invoices si ON c.id = si.customer_id AND si.status NOT IN ('Paid', 'Voided')
GROUP BY c.id, c.customer_code, c.name;

CREATE OR REPLACE VIEW business.vendor_balances AS
SELECT v.id AS vendor_id, v.vendor_code, v.name AS vendor_name,
    COALESCE(SUM(pi.total_amount - pi.amount_paid), 0) AS outstanding_balance,
    COALESCE(SUM(CASE WHEN pi.due_date < CURRENT_DATE AND pi.status NOT IN ('Paid', 'Voided') THEN pi.total_amount - pi.amount_paid ELSE 0 END), 0) AS overdue_amount,
    COALESCE(SUM(CASE WHEN pi.status = 'Draft' THEN pi.total_amount ELSE 0 END), 0) AS draft_amount,
    COALESCE(MAX(pi.due_date), NULL) AS latest_due_date
FROM business.vendors v LEFT JOIN business.purchase_invoices pi ON v.id = pi.vendor_id AND pi.status NOT IN ('Paid', 'Voided')
GROUP BY v.id, v.vendor_code, v.name;

CREATE OR REPLACE VIEW business.inventory_summary AS
SELECT 
    p.id AS product_id, p.product_code, p.name AS product_name, p.product_type, p.category, p.unit_of_measure,
    COALESCE(SUM(im.quantity), 0) AS current_quantity,
    CASE 
        WHEN COALESCE(SUM(im.quantity), 0) != 0 THEN 
            (COALESCE(SUM(im.total_cost), 0) / SUM(im.quantity)) -- Parentheses added for clarity
        ELSE p.purchase_price -- Fallback to product's purchase price if no movements/zero quantity
    END AS average_cost,
    COALESCE(SUM(im.total_cost), 0) AS inventory_value,
    p.sales_price AS current_sales_price, p.min_stock_level, p.reorder_point,
    CASE WHEN p.min_stock_level IS NOT NULL AND COALESCE(SUM(im.quantity), 0) <= p.min_stock_level THEN TRUE ELSE FALSE END AS below_minimum,
    CASE WHEN p.reorder_point IS NOT NULL AND COALESCE(SUM(im.quantity), 0) <= p.reorder_point THEN TRUE ELSE FALSE END AS reorder_needed
FROM business.products p LEFT JOIN business.inventory_movements im ON p.id = im.product_id
WHERE p.product_type = 'Inventory' AND p.is_active = TRUE
GROUP BY p.id, p.product_code, p.name, p.product_type, p.category, p.unit_of_measure, p.purchase_price, p.sales_price, p.min_stock_level, p.reorder_point;


-- ============================================================================
-- FUNCTIONS
-- ============================================================================
CREATE OR REPLACE FUNCTION core.get_next_sequence_value(p_sequence_name VARCHAR)
RETURNS VARCHAR AS $$
DECLARE v_sequence RECORD; v_next_value INTEGER; v_result VARCHAR;
BEGIN
    SELECT * INTO v_sequence FROM core.sequences WHERE sequence_name = p_sequence_name FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Sequence % not found', p_sequence_name; END IF;
    v_next_value := v_sequence.next_value;
    UPDATE core.sequences SET next_value = next_value + increment_by, updated_at = CURRENT_TIMESTAMP WHERE sequence_name = p_sequence_name;
    v_result := v_sequence.format_template;
    v_result := REPLACE(v_result, '{PREFIX}', COALESCE(v_sequence.prefix, ''));
    v_result := REPLACE(v_result, '{VALUE}', LPAD(v_next_value::TEXT, 6, '0')); -- Standard 6 digit padding
    v_result := REPLACE(v_result, '{SUFFIX}', COALESCE(v_sequence.suffix, ''));
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION accounting.generate_journal_entry(p_journal_type VARCHAR, p_entry_date DATE, p_description VARCHAR, p_reference VARCHAR, p_source_type VARCHAR, p_source_id INTEGER, p_lines JSONB, p_user_id INTEGER)
RETURNS INTEGER AS $$ 
DECLARE v_fiscal_period_id INTEGER; v_entry_no VARCHAR; v_journal_id INTEGER; v_line JSONB; v_line_number INTEGER := 1; v_total_debits NUMERIC(15,2) := 0; v_total_credits NUMERIC(15,2) := 0;
BEGIN
    SELECT id INTO v_fiscal_period_id FROM accounting.fiscal_periods WHERE p_entry_date BETWEEN start_date AND end_date AND status = 'Open';
    IF v_fiscal_period_id IS NULL THEN RAISE EXCEPTION 'No open fiscal period found for date %', p_entry_date; END IF;
    v_entry_no := core.get_next_sequence_value('journal_entry'); -- Assuming 'journal_entry' sequence exists
    INSERT INTO accounting.journal_entries (entry_no, journal_type, entry_date, fiscal_period_id, description, reference, is_posted, source_type, source_id, created_by, updated_by) VALUES (v_entry_no, p_journal_type, p_entry_date, v_fiscal_period_id, p_description, p_reference, FALSE, p_source_type, p_source_id, p_user_id, p_user_id) RETURNING id INTO v_journal_id;
    FOR v_line IN SELECT * FROM jsonb_array_elements(p_lines) LOOP
        INSERT INTO accounting.journal_entry_lines (journal_entry_id, line_number, account_id, description, debit_amount, credit_amount, currency_code, exchange_rate, tax_code, tax_amount, dimension1_id, dimension2_id) 
        VALUES (v_journal_id, v_line_number, (v_line->>'account_id')::INTEGER, v_line->>'description', COALESCE((v_line->>'debit_amount')::NUMERIC, 0), COALESCE((v_line->>'credit_amount')::NUMERIC, 0), COALESCE(v_line->>'currency_code', 'SGD'), COALESCE((v_line->>'exchange_rate')::NUMERIC, 1), v_line->>'tax_code', COALESCE((v_line->>'tax_amount')::NUMERIC, 0), NULLIF(TRIM(v_line->>'dimension1_id'), '')::INTEGER, NULLIF(TRIM(v_line->>'dimension2_id'), '')::INTEGER);
        v_line_number := v_line_number + 1; v_total_debits := v_total_debits + COALESCE((v_line->>'debit_amount')::NUMERIC, 0); v_total_credits := v_total_credits + COALESCE((v_line->>'credit_amount')::NUMERIC, 0);
    END LOOP;
    IF round(v_total_debits, 2) != round(v_total_credits, 2) THEN RAISE EXCEPTION 'Journal entry is not balanced. Debits: %, Credits: %', v_total_debits, v_total_credits; END IF;
    RETURN v_journal_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION accounting.post_journal_entry(p_journal_id INTEGER, p_user_id INTEGER)
RETURNS BOOLEAN AS $$
DECLARE v_fiscal_period_status VARCHAR; v_is_already_posted BOOLEAN;
BEGIN
    SELECT is_posted INTO v_is_already_posted FROM accounting.journal_entries WHERE id = p_journal_id;
    IF v_is_already_posted THEN RAISE EXCEPTION 'Journal entry % is already posted', p_journal_id; END IF;
    SELECT fp.status INTO v_fiscal_period_status FROM accounting.journal_entries je JOIN accounting.fiscal_periods fp ON je.fiscal_period_id = fp.id WHERE je.id = p_journal_id;
    IF v_fiscal_period_status != 'Open' THEN RAISE EXCEPTION 'Cannot post to a closed or archived fiscal period'; END IF;
    UPDATE accounting.journal_entries SET is_posted = TRUE, updated_at = CURRENT_TIMESTAMP, updated_by = p_user_id WHERE id = p_journal_id;
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION accounting.calculate_account_balance(p_account_id INTEGER, p_as_of_date DATE)
RETURNS NUMERIC AS $$
DECLARE v_balance NUMERIC(15,2) := 0; v_opening_balance NUMERIC(15,2); v_account_opening_balance_date DATE; 
BEGIN
    SELECT acc.opening_balance, acc.opening_balance_date INTO v_opening_balance, v_account_opening_balance_date FROM accounting.accounts acc WHERE acc.id = p_account_id;
    IF NOT FOUND THEN RAISE EXCEPTION 'Account with ID % not found', p_account_id; END IF;
    -- Sum (debits - credits) from posted journal entry lines up to the specified date
    -- and after or on the account's opening balance date (if specified)
    SELECT COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) 
    INTO v_balance 
    FROM accounting.journal_entry_lines jel 
    JOIN accounting.journal_entries je ON jel.journal_entry_id = je.id 
    WHERE jel.account_id = p_account_id 
      AND je.is_posted = TRUE 
      AND je.entry_date <= p_as_of_date 
      AND (v_account_opening_balance_date IS NULL OR je.entry_date >= v_account_opening_balance_date);
      
    v_balance := v_balance + COALESCE(v_opening_balance, 0);
    RETURN v_balance;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION core.update_timestamp_trigger_func()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = CURRENT_TIMESTAMP; RETURN NEW; END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION audit.log_data_change_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    v_old_data JSONB; v_new_data JSONB; v_change_type VARCHAR(20); v_user_id INTEGER; v_entity_id INTEGER; v_entity_name VARCHAR(200); temp_val TEXT; current_field_name_from_json TEXT;
BEGIN
    -- Try to get user_id from session variable first
    BEGIN v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER; EXCEPTION WHEN OTHERS THEN v_user_id := NULL; END;
    -- Fallback to created_by/updated_by if session variable not set (e.g., direct DB modification)
    IF v_user_id IS NULL THEN
        IF TG_OP = 'INSERT' THEN BEGIN v_user_id := NEW.created_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END;
        ELSIF TG_OP = 'UPDATE' THEN BEGIN v_user_id := NEW.updated_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END;
        -- For DELETE, if v_user_id is still NULL, it means we can't determine it from OLD record's updated_by
        END IF;
    END IF;
    -- Avoid logging changes to audit tables themselves to prevent infinite loops
    IF TG_TABLE_SCHEMA = 'audit' AND TG_TABLE_NAME IN ('audit_log', 'data_change_history') THEN RETURN NULL; END IF;

    IF TG_OP = 'INSERT' THEN v_change_type := 'Insert'; v_old_data := NULL; v_new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN v_change_type := 'Update'; v_old_data := to_jsonb(OLD); v_new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'DELETE' THEN v_change_type := 'Delete'; v_old_data := to_jsonb(OLD); v_new_data := NULL; END IF;

    -- Determine entity_id (usually 'id' column)
    BEGIN IF TG_OP = 'DELETE' THEN v_entity_id := OLD.id; ELSE v_entity_id := NEW.id; END IF; EXCEPTION WHEN undefined_column THEN v_entity_id := NULL; END;
    
    -- Determine a representative entity_name (e.g., name, code, entry_no)
    BEGIN IF TG_OP = 'DELETE' THEN temp_val := CASE WHEN TG_TABLE_NAME IN ('accounts','customers','vendors','products','roles','account_types','dimensions','fiscal_years','budgets') THEN OLD.name WHEN TG_TABLE_NAME = 'journal_entries' THEN OLD.entry_no WHEN TG_TABLE_NAME = 'sales_invoices' THEN OLD.invoice_no WHEN TG_TABLE_NAME = 'purchase_invoices' THEN OLD.invoice_no WHEN TG_TABLE_NAME = 'payments' THEN OLD.payment_no WHEN TG_TABLE_NAME = 'users' THEN OLD.username WHEN TG_TABLE_NAME = 'tax_codes' THEN OLD.code WHEN TG_TABLE_NAME = 'gst_returns' THEN OLD.return_period ELSE OLD.id::TEXT END;
    ELSE temp_val := CASE WHEN TG_TABLE_NAME IN ('accounts','customers','vendors','products','roles','account_types','dimensions','fiscal_years','budgets') THEN NEW.name WHEN TG_TABLE_NAME = 'journal_entries' THEN NEW.entry_no WHEN TG_TABLE_NAME = 'sales_invoices' THEN NEW.invoice_no WHEN TG_TABLE_NAME = 'purchase_invoices' THEN NEW.invoice_no WHEN TG_TABLE_NAME = 'payments' THEN NEW.payment_no WHEN TG_TABLE_NAME = 'users' THEN NEW.username WHEN TG_TABLE_NAME = 'tax_codes' THEN NEW.code WHEN TG_TABLE_NAME = 'gst_returns' THEN NEW.return_period ELSE NEW.id::TEXT END; END IF; v_entity_name := temp_val;
    EXCEPTION WHEN undefined_column THEN BEGIN IF TG_OP = 'DELETE' THEN v_entity_name := OLD.id::TEXT; ELSE v_entity_name := NEW.id::TEXT; END IF; EXCEPTION WHEN undefined_column THEN v_entity_name := NULL; END; END;

    INSERT INTO audit.audit_log (user_id,action,entity_type,entity_id,entity_name,changes,timestamp) VALUES (v_user_id,v_change_type,TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,v_entity_id,v_entity_name,jsonb_build_object('old',v_old_data,'new',v_new_data),CURRENT_TIMESTAMP);

    -- Log individual field changes for UPDATE operations
    IF TG_OP = 'UPDATE' THEN
        FOR current_field_name_from_json IN SELECT key_alias FROM jsonb_object_keys(v_old_data) AS t(key_alias) LOOP
            IF (v_new_data ? current_field_name_from_json) AND ((v_old_data -> current_field_name_from_json) IS DISTINCT FROM (v_new_data -> current_field_name_from_json)) THEN
                INSERT INTO audit.data_change_history (table_name,record_id,field_name,old_value,new_value,change_type,changed_by,changed_at) VALUES (TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,NEW.id,current_field_name_from_json,v_old_data->>current_field_name_from_json,v_new_data->>current_field_name_from_json,'Update',v_user_id,CURRENT_TIMESTAMP);
            END IF;
        END LOOP;
    END IF;
    RETURN NULL; -- Result is ignored for AFTER trigger
END;
$$ LANGUAGE plpgsql;

-- Trigger to update bank_account.current_balance
CREATE OR REPLACE FUNCTION business.update_bank_account_balance_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE business.bank_accounts 
        SET current_balance = current_balance + NEW.amount -- Assumes NEW.amount is signed
        WHERE id = NEW.bank_account_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE business.bank_accounts 
        SET current_balance = current_balance - OLD.amount -- Assumes OLD.amount is signed
        WHERE id = OLD.bank_account_id;
    ELSIF TG_OP = 'UPDATE' THEN
        -- If bank account itself changed for the transaction
        IF NEW.bank_account_id != OLD.bank_account_id THEN
            UPDATE business.bank_accounts 
            SET current_balance = current_balance - OLD.amount 
            WHERE id = OLD.bank_account_id;
            
            UPDATE business.bank_accounts 
            SET current_balance = current_balance + NEW.amount 
            WHERE id = NEW.bank_account_id;
        ELSE -- Bank account is the same, just adjust for amount difference
            UPDATE business.bank_accounts 
            SET current_balance = current_balance - OLD.amount + NEW.amount 
            WHERE id = NEW.bank_account_id;
        END IF;
    END IF;
    RETURN NULL; -- Result is ignored since this is an AFTER trigger
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- APPLYING TRIGGERS
-- ============================================================================
-- Apply update_timestamp trigger to all tables with 'updated_at'
DO $$
DECLARE r RECORD;
BEGIN
    FOR r IN 
        SELECT table_schema, table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' AND table_schema IN ('core','accounting','business','audit')
        GROUP BY table_schema, table_name 
    LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS trg_update_timestamp ON %I.%I; CREATE TRIGGER trg_update_timestamp BEFORE UPDATE ON %I.%I FOR EACH ROW EXECUTE FUNCTION core.update_timestamp_trigger_func();',
            r.table_schema, r.table_name, r.table_schema, r.table_name
        );
    END LOOP;
END;
$$;

-- Apply audit log trigger to specified tables
DO $$
DECLARE
    tables_to_audit TEXT[] := ARRAY[
        'accounting.accounts', 'accounting.journal_entries', 'accounting.fiscal_periods', 'accounting.fiscal_years',
        'business.customers', 'business.vendors', 'business.products', 
        'business.sales_invoices', 'business.purchase_invoices', 'business.payments',
        'accounting.tax_codes', 'accounting.gst_returns',
        'core.users', 'core.roles', 'core.company_settings', 
        'business.bank_accounts', 'business.bank_transactions', 'business.bank_reconciliations' -- Added bank_reconciliations
    ];
    table_fullname TEXT;
    schema_name TEXT;
    table_name_var TEXT;
BEGIN
    FOREACH table_fullname IN ARRAY tables_to_audit
    LOOP
        SELECT split_part(table_fullname, '.', 1) INTO schema_name;
        SELECT split_part(table_fullname, '.', 2) INTO table_name_var;
        EXECUTE format(
            'DROP TRIGGER IF EXISTS trg_audit_log ON %I.%I; CREATE TRIGGER trg_audit_log AFTER INSERT OR UPDATE OR DELETE ON %I.%I FOR EACH ROW EXECUTE FUNCTION audit.log_data_change_trigger_func();',
            schema_name, table_name_var, schema_name, table_name_var
        );
    END LOOP;
END;
$$;

-- Apply bank balance update trigger
DROP TRIGGER IF EXISTS trg_update_bank_balance ON business.bank_transactions;
CREATE TRIGGER trg_update_bank_balance
AFTER INSERT OR UPDATE OR DELETE ON business.bank_transactions
FOR EACH ROW EXECUTE FUNCTION business.update_bank_account_balance_trigger_func();

-- End of script

```

---

**File 2: `scripts/initial_data.sql` (Updated to Version 1.0.5)**

```sql
-- File: scripts/initial_data.sql
-- ============================================================================
-- INITIAL DATA (Version 1.0.5)
-- ============================================================================
-- This version corresponds to schema version 1.0.5.
-- No functional data changes were introduced by schema patches 1.0.4 or 1.0.5.
-- Existing permissions for banking/reconciliation were already present in v1.0.3.
-- Version 1.0.3 (base) added sequence grants for audit schema.
-- ============================================================================

-- Ensure this script is run by a superuser or the owner of the database/schemas
-- Default user for application runtime: sgbookkeeper_user

BEGIN;

-- ----------------------------------------------------------------------------
-- Insert default roles
-- ----------------------------------------------------------------------------
INSERT INTO core.roles (name, description) VALUES
('Administrator', 'Full system access'),
('Accountant', 'Access to accounting functions'),
('Bookkeeper', 'Basic transaction entry and reporting'),
('Manager', 'Access to reports and dashboards'),
('Viewer', 'Read-only access to data')
ON CONFLICT (name) DO UPDATE SET 
    description = EXCLUDED.description, 
    updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert default permissions
-- ----------------------------------------------------------------------------
INSERT INTO core.permissions (code, description, module) VALUES
-- Core permissions
('SYSTEM_SETTINGS', 'Manage system settings', 'System'),
('USER_MANAGE', 'Manage users', 'System'),
('ROLE_MANAGE', 'Manage roles and permissions', 'System'),
('DATA_BACKUP', 'Backup and restore data', 'System'),
('DATA_IMPORT', 'Import data', 'System'),
('DATA_EXPORT', 'Export data', 'System'),
('VIEW_AUDIT_LOG', 'View audit logs', 'System'),
-- Accounting permissions
('ACCOUNT_VIEW', 'View chart of accounts', 'Accounting'),
('ACCOUNT_CREATE', 'Create accounts', 'Accounting'),
('ACCOUNT_EDIT', 'Edit accounts', 'Accounting'),
('ACCOUNT_DELETE', 'Delete/deactivate accounts', 'Accounting'),
('JOURNAL_VIEW', 'View journal entries', 'Accounting'),
('JOURNAL_CREATE', 'Create journal entries', 'Accounting'),
('JOURNAL_EDIT', 'Edit draft journal entries', 'Accounting'),
('JOURNAL_POST', 'Post journal entries', 'Accounting'),
('JOURNAL_REVERSE', 'Reverse posted journal entries', 'Accounting'),
('PERIOD_MANAGE', 'Manage fiscal periods', 'Accounting'),
('YEAR_CLOSE', 'Close fiscal years', 'Accounting'),
-- Business permissions
('CUSTOMER_VIEW', 'View customers', 'Business'),
('CUSTOMER_CREATE', 'Create customers', 'Business'),
('CUSTOMER_EDIT', 'Edit customers', 'Business'),
('CUSTOMER_DELETE', 'Delete customers', 'Business'),
('VENDOR_VIEW', 'View vendors', 'Business'),
('VENDOR_CREATE', 'Create vendors', 'Business'),
('VENDOR_EDIT', 'Edit vendors', 'Business'),
('VENDOR_DELETE', 'Delete vendors', 'Business'),
('PRODUCT_VIEW', 'View products', 'Business'),
('PRODUCT_CREATE', 'Create products', 'Business'),
('PRODUCT_EDIT', 'Edit products', 'Business'),
('PRODUCT_DELETE', 'Delete products', 'Business'),
-- Transaction permissions
('INVOICE_VIEW', 'View invoices', 'Transactions'),
('INVOICE_CREATE', 'Create invoices', 'Transactions'),
('INVOICE_EDIT', 'Edit invoices', 'Transactions'),
('INVOICE_DELETE', 'Delete invoices', 'Transactions'),
('INVOICE_APPROVE', 'Approve invoices', 'Transactions'),
('PAYMENT_VIEW', 'View payments', 'Transactions'),
('PAYMENT_CREATE', 'Create payments', 'Transactions'),
('PAYMENT_EDIT', 'Edit payments', 'Transactions'),
('PAYMENT_DELETE', 'Delete payments', 'Transactions'),
('PAYMENT_APPROVE', 'Approve payments', 'Transactions'),
-- Banking permissions
('BANK_ACCOUNT_VIEW', 'View bank accounts', 'Banking'),
('BANK_ACCOUNT_MANAGE', 'Manage bank accounts (CRUD)', 'Banking'),
('BANK_TRANSACTION_VIEW', 'View bank transactions', 'Banking'),
('BANK_TRANSACTION_MANAGE', 'Manage bank transactions (manual entry)', 'Banking'),
('BANK_RECONCILE', 'Reconcile bank accounts', 'Banking'),
('BANK_STATEMENT_IMPORT', 'Import bank statements', 'Banking'),
-- Tax permissions
('TAX_VIEW', 'View tax settings', 'Tax'),
('TAX_EDIT', 'Edit tax settings', 'Tax'),
('GST_PREPARE', 'Prepare GST returns', 'Tax'),
('GST_SUBMIT', 'Mark GST returns as submitted', 'Tax'),
('TAX_REPORT', 'Generate tax reports', 'Tax'),
-- Reporting permissions
('REPORT_FINANCIAL', 'Access financial reports', 'Reporting'),
('REPORT_TAX', 'Access tax reports', 'Reporting'),
('REPORT_MANAGEMENT', 'Access management reports', 'Reporting'),
('REPORT_CUSTOM', 'Create custom reports', 'Reporting'),
('REPORT_EXPORT', 'Export reports', 'Reporting')
ON CONFLICT (code) DO UPDATE SET
    description = EXCLUDED.description,
    module = EXCLUDED.module;

-- ----------------------------------------------------------------------------
-- Insert System Init User (ID 1) - MUST BE CREATED EARLY
-- ----------------------------------------------------------------------------
INSERT INTO core.users (id, username, password_hash, email, full_name, is_active, require_password_change)
VALUES (1, 'system_init_user', crypt('system_init_secure_password_!PLACEHOLDER!', gen_salt('bf')), 'system_init@sgbookkeeper.com', 'System Initializer', FALSE, FALSE) 
ON CONFLICT (id) DO UPDATE SET 
    username = EXCLUDED.username, 
    password_hash = EXCLUDED.password_hash, 
    email = EXCLUDED.email, 
    full_name = EXCLUDED.full_name, 
    is_active = EXCLUDED.is_active,
    require_password_change = EXCLUDED.require_password_change,
    updated_at = CURRENT_TIMESTAMP;

SELECT setval(pg_get_serial_sequence('core.users', 'id'), COALESCE((SELECT MAX(id) FROM core.users), 1), true);

-- ----------------------------------------------------------------------------
-- Insert default currencies (SGD must be first for company_settings FK if it's the base)
-- ----------------------------------------------------------------------------
INSERT INTO accounting.currencies (code, name, symbol, is_active, decimal_places, created_by, updated_by) VALUES
('SGD', 'Singapore Dollar', '$', TRUE, 2, 1, 1)
ON CONFLICT (code) DO UPDATE SET 
    name = EXCLUDED.name, symbol = EXCLUDED.symbol, is_active = EXCLUDED.is_active, 
    decimal_places = EXCLUDED.decimal_places, created_by = COALESCE(accounting.currencies.created_by, EXCLUDED.created_by), 
    updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.currencies (code, name, symbol, is_active, decimal_places, created_by, updated_by) VALUES
('USD', 'US Dollar', '$', TRUE, 2, 1, 1),
('EUR', 'Euro', '€', TRUE, 2, 1, 1),
('GBP', 'British Pound', '£', TRUE, 2, 1, 1),
('AUD', 'Australian Dollar', '$', TRUE, 2, 1, 1),
('JPY', 'Japanese Yen', '¥', TRUE, 0, 1, 1),
('CNY', 'Chinese Yuan', '¥', TRUE, 2, 1, 1),
('MYR', 'Malaysian Ringgit', 'RM', TRUE, 2, 1, 1),
('IDR', 'Indonesian Rupiah', 'Rp', TRUE, 0, 1, 1)
ON CONFLICT (code) DO UPDATE SET 
    name = EXCLUDED.name, symbol = EXCLUDED.symbol, is_active = EXCLUDED.is_active, 
    decimal_places = EXCLUDED.decimal_places, created_by = COALESCE(accounting.currencies.created_by, EXCLUDED.created_by), 
    updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert Default Company Settings (ID = 1)
-- ----------------------------------------------------------------------------
INSERT INTO core.company_settings (
    id, company_name, legal_name, uen_no, gst_registration_no, gst_registered, 
    address_line1, postal_code, city, country, 
    fiscal_year_start_month, fiscal_year_start_day, base_currency, tax_id_label, date_format, 
    updated_by 
) VALUES (
    1, 
    'My Demo Company Pte. Ltd.', 
    'My Demo Company Private Limited',
    '202400001Z', 
    'M90000001Z', 
    TRUE,
    '1 Marina Boulevard', 
    '018989',
    'Singapore',
    'Singapore',
    1, 
    1, 
    'SGD',
    'UEN',
    'dd/MM/yyyy',
    1 
)
ON CONFLICT (id) DO UPDATE SET
    company_name = EXCLUDED.company_name, legal_name = EXCLUDED.legal_name, uen_no = EXCLUDED.uen_no,
    gst_registration_no = EXCLUDED.gst_registration_no, gst_registered = EXCLUDED.gst_registered,
    address_line1 = EXCLUDED.address_line1, postal_code = EXCLUDED.postal_code, city = EXCLUDED.city, country = EXCLUDED.country,
    fiscal_year_start_month = EXCLUDED.fiscal_year_start_month, fiscal_year_start_day = EXCLUDED.fiscal_year_start_day,
    base_currency = EXCLUDED.base_currency, tax_id_label = EXCLUDED.tax_id_label, date_format = EXCLUDED.date_format,
    updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert default document sequences
-- ----------------------------------------------------------------------------
INSERT INTO core.sequences (sequence_name, prefix, next_value, format_template) VALUES
('journal_entry', 'JE', 1, '{PREFIX}{VALUE:06}'), ('sales_invoice', 'INV', 1, '{PREFIX}{VALUE:06}'),
('purchase_invoice', 'PUR', 1, '{PREFIX}{VALUE:06}'), ('payment', 'PAY', 1, '{PREFIX}{VALUE:06}'),
('receipt', 'REC', 1, '{PREFIX}{VALUE:06}'), ('customer', 'CUS', 1, '{PREFIX}{VALUE:04}'),
('vendor', 'VEN', 1, '{PREFIX}{VALUE:04}'), ('product', 'PRD', 1, '{PREFIX}{VALUE:04}'),
('wht_certificate', 'WHT', 1, '{PREFIX}{VALUE:06}')
ON CONFLICT (sequence_name) DO UPDATE SET
    prefix = EXCLUDED.prefix, next_value = GREATEST(core.sequences.next_value, EXCLUDED.next_value), 
    format_template = EXCLUDED.format_template, updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert default configuration values
-- ----------------------------------------------------------------------------
INSERT INTO core.configuration (config_key, config_value, description, updated_by) VALUES
('SysAcc_DefaultAR', '1120', 'Default Accounts Receivable account code', 1),
('SysAcc_DefaultSalesRevenue', '4100', 'Default Sales Revenue account code', 1),
('SysAcc_DefaultGSTOutput', 'SYS-GST-OUTPUT', 'Default GST Output Tax account code', 1),
('SysAcc_DefaultAP', '2110', 'Default Accounts Payable account code', 1),
('SysAcc_DefaultPurchaseExpense', '5100', 'Default Purchase/COGS account code', 1),
('SysAcc_DefaultGSTInput', 'SYS-GST-INPUT', 'Default GST Input Tax account code', 1),
('SysAcc_DefaultCash', '1112', 'Default Cash on Hand account code', 1), 
('SysAcc_DefaultInventoryAsset', '1130', 'Default Inventory Asset account code', 1),
('SysAcc_DefaultCOGS', '5100', 'Default Cost of Goods Sold account code', 1),
('SysAcc_GSTControl', 'SYS-GST-CONTROL', 'GST Control/Clearing Account', 1)
ON CONFLICT (config_key) DO UPDATE SET
    config_value = EXCLUDED.config_value,
    description = EXCLUDED.description,
    updated_by = EXCLUDED.updated_by,
    updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Insert account types
-- ----------------------------------------------------------------------------
INSERT INTO accounting.account_types (name, category, is_debit_balance, report_type, display_order, description) VALUES
('Current Asset', 'Asset', TRUE, 'Balance Sheet', 10, 'Assets expected to be converted to cash within one year'),
('Fixed Asset', 'Asset', TRUE, 'Balance Sheet', 20, 'Long-term tangible assets'),
('Other Asset', 'Asset', TRUE, 'Balance Sheet', 30, 'Assets that don''t fit in other categories'),
('Current Liability', 'Liability', FALSE, 'Balance Sheet', 40, 'Obligations due within one year'),
('Long-term Liability', 'Liability', FALSE, 'Balance Sheet', 50, 'Obligations due beyond one year'),
('Equity', 'Equity', FALSE, 'Balance Sheet', 60, 'Owner''s equity and retained earnings'),
('Revenue', 'Revenue', FALSE, 'Income Statement', 70, 'Income from business operations'),
('Cost of Sales', 'Expense', TRUE, 'Income Statement', 80, 'Direct costs of goods sold'),
('Expense', 'Expense', TRUE, 'Income Statement', 90, 'General business expenses'),
('Other Income', 'Revenue', FALSE, 'Income Statement', 100, 'Income from non-core activities'),
('Other Expense', 'Expense', TRUE, 'Income Statement', 110, 'Expenses from non-core activities')
ON CONFLICT (name) DO UPDATE SET
    category = EXCLUDED.category, is_debit_balance = EXCLUDED.is_debit_balance, report_type = EXCLUDED.report_type,
    display_order = EXCLUDED.display_order, description = EXCLUDED.description, updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Ensure key GL accounts for system configuration exist
-- ----------------------------------------------------------------------------
INSERT INTO accounting.accounts (code, name, account_type, sub_type, created_by, updated_by, is_active, is_control_account, is_bank_account) VALUES
('1120', 'Accounts Receivable Control', 'Asset', 'Accounts Receivable', 1, 1, TRUE, TRUE, FALSE),
('2110', 'Accounts Payable Control', 'Liability', 'Accounts Payable', 1, 1, TRUE, TRUE, FALSE),
('4100', 'General Sales Revenue', 'Revenue', 'Sales', 1, 1, TRUE, FALSE, FALSE),
('5100', 'General Cost of Goods Sold', 'Expense', 'Cost of Sales', 1, 1, TRUE, FALSE, FALSE),
('SYS-GST-OUTPUT', 'System GST Output Tax', 'Liability', 'GST Payable', 1, 1, TRUE, FALSE, FALSE),
('SYS-GST-INPUT', 'System GST Input Tax', 'Asset', 'GST Receivable', 1, 1, TRUE, FALSE, FALSE),
('SYS-GST-CONTROL', 'System GST Control', 'Liability', 'GST Payable', 1, 1, TRUE, TRUE, FALSE),
('1112', 'Cash on Hand', 'Asset', 'Cash and Cash Equivalents', 1,1, TRUE, FALSE, FALSE),
('1130', 'Inventory Asset Control', 'Asset', 'Inventory', 1,1,TRUE, TRUE, FALSE)
ON CONFLICT (code) DO NOTHING;

-- ----------------------------------------------------------------------------
-- Insert default tax codes (GST updated to 9%)
-- ----------------------------------------------------------------------------
INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id)
SELECT 'SR', 'Standard Rate (9%)', 'GST', 9.00, TRUE, TRUE, 1, 1, acc.id FROM accounting.accounts acc WHERE acc.code = 'SYS-GST-OUTPUT'
ON CONFLICT (code) DO UPDATE SET
    description = EXCLUDED.description, tax_type = EXCLUDED.tax_type, rate = EXCLUDED.rate,
    is_default = EXCLUDED.is_default, is_active = EXCLUDED.is_active, updated_by = EXCLUDED.updated_by, 
    affects_account_id = EXCLUDED.affects_account_id, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('ZR', 'Zero Rate', 'GST', 0.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('ES', 'Exempt Supply', 'GST', 0.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('OP', 'Out of Scope', 'GST', 0.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id)
SELECT 'TX', 'Taxable Purchase (9%)', 'GST', 9.00, FALSE, TRUE, 1, 1, acc.id FROM accounting.accounts acc WHERE acc.code = 'SYS-GST-INPUT'
ON CONFLICT (code) DO UPDATE SET
    description = EXCLUDED.description, tax_type = EXCLUDED.tax_type, rate = EXCLUDED.rate,
    is_default = EXCLUDED.is_default, is_active = EXCLUDED.is_active, updated_by = EXCLUDED.updated_by, 
    affects_account_id = EXCLUDED.affects_account_id, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('BL', 'Blocked Input Tax (9%)', 'GST', 9.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, rate = EXCLUDED.rate, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('NR', 'Non-Resident Services', 'Withholding Tax', 15.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('ND', 'Non-Deductible', 'Income Tax', 0.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('CA', 'Capital Allowance', 'Income Tax', 0.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Create an active 'admin' user for application login
-- ----------------------------------------------------------------------------
INSERT INTO core.users (username, password_hash, email, full_name, is_active, require_password_change)
VALUES ('admin', crypt('password', gen_salt('bf')), 'admin@sgbookkeeper.com', 'Administrator', TRUE, TRUE)
ON CONFLICT (username) DO UPDATE SET
    password_hash = EXCLUDED.password_hash, email = EXCLUDED.email, full_name = EXCLUDED.full_name,
    is_active = EXCLUDED.is_active, require_password_change = EXCLUDED.require_password_change,
    updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Assign 'Administrator' role to 'admin' user
-- ----------------------------------------------------------------------------
WITH admin_user_id_cte AS (SELECT id FROM core.users WHERE username = 'admin'),
     admin_role_id_cte AS (SELECT id FROM core.roles WHERE name = 'Administrator')
INSERT INTO core.user_roles (user_id, role_id, created_at)
SELECT admin_user_id_cte.id, admin_role_id_cte.id, CURRENT_TIMESTAMP FROM admin_user_id_cte, admin_role_id_cte
WHERE admin_user_id_cte.id IS NOT NULL AND admin_role_id_cte.id IS NOT NULL
ON CONFLICT (user_id, role_id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- For all permissions, grant them to the 'Administrator' role
-- ----------------------------------------------------------------------------
INSERT INTO core.role_permissions (role_id, permission_id, created_at)
SELECT r.id, p.id, CURRENT_TIMESTAMP
FROM core.roles r, core.permissions p
WHERE r.name = 'Administrator'
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- Grant Privileges to Application User (sgbookkeeper_user)
-- This part is typically run by an admin user (e.g., postgres) after schema creation
-- The application user 'sgbookkeeper_user' needs these privileges to operate.
-- ----------------------------------------------------------------------------
GRANT USAGE ON SCHEMA core, accounting, business, audit TO sgbookkeeper_user;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA accounting TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA business TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA audit TO sgbookkeeper_user;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA core TO sgbookkeeper_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA accounting TO sgbookkeeper_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA business TO sgbookkeeper_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA audit TO sgbookkeeper_user; -- Added for audit schema sequences

GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA core TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA accounting TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA business TO sgbookkeeper_user; -- Added for business schema functions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA audit TO sgbookkeeper_user;

-- Default privileges for future objects created by 'postgres' (or the user running db_init.py)
-- This helps ensure sgbookkeeper_user can access newly created tables/sequences if schema evolves
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA core GRANT ALL ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA accounting GRANT ALL ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA business GRANT ALL ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA audit GRANT ALL ON TABLES TO sgbookkeeper_user;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA core GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA accounting GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA business GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA audit GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user; -- Added for audit schema

COMMIT; 
-- End of initial data

```

---
https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%2216tABsm1Plf_0fhtruoJyyxobBli3e8-7%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/19T9JbSrHCuXhHpzFMUh4Ti_0sDPDycSW/view?usp=sharing, https://drive.google.com/file/d/1EGOoM0TGqPgNBJzwxKdVO2u331Myhd4b/view?usp=sharing, https://drive.google.com/file/d/1bSRRtsWeJI9djXTDZTZTjZxnsWS3cvsV/view?usp=sharing, https://drive.google.com/file/d/1vTPAoLcEetjBj17-5nTa_Z6RS7ND5Wmz/view?usp=sharing

