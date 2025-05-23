<think>
The new error from `db_init.py` is `Error during database creation/initialization: record "old" has no field "entry_no"`.
The `psql` output still shows the `record "new" has no field "created_by"` error from the audit trigger, and then the foreign key violations.

This implies two things:
1.  The `db_init.py` script might be encountering the `record "old" has no field "entry_no"` error *before* or *differently* than when `psql` runs `initial_data.sql` directly. This specific error (`record "old" has no field "entry_no"`) points to the `CASE` statement for `entity_name` in the audit trigger `audit.log_data_change_trigger_func`, specifically when `TG_OP = 'DELETE'`:
    ```sql
    CASE 
        ...
        WHEN TG_TABLE_NAME = 'journal_entries' THEN (CASE WHEN TG_OP = 'DELETE' THEN OLD.entry_no ELSE NEW.entry_no END)
        ...
    END
    ```
    If a `DELETE` operation occurs on a table that is *not* `journal_entries` but the trigger logic somehow tries to access `OLD.entry_no` (perhaps due to a fall-through or a misconfiguration of audited tables), this could happen. Or, if a `DELETE` occurs on `journal_entries` and `OLD` somehow doesn't conform to the expected structure (less likely).

2.  The `record "new" has no field "created_by"` error during `psql` execution of `initial_data.sql` persists. This means my previous fix for the `v_user_id` retrieval in `audit.log_data_change_trigger_func` was not fully effective or the correct version of the schema script wasn't used.

Let's analyze the `record "old" has no field "entry_no"` from `db_init.py`.
This error suggests that the `entity_name` `CASE` statement is trying to access `OLD.entry_no` for a table that doesn't have an `entry_no` field, specifically during a `DELETE` operation.
However, the `initial_data.sql` script primarily consists of `INSERT` statements. `DELETE` operations are not typical during initial data seeding.
Could it be that `db_init.py` does some cleanup or `DROP` operations that might fire triggers if those tables were somehow pre-existing and audited? The script does `DROP DATABASE IF EXISTS`. If triggers were on system tables or tables in `postgres` db (which they shouldn't be), this error is highly unlikely. The error is most likely from the `initial_data.sql` part.

Let's re-examine the `CASE` statement for `entity_name` in `audit.log_data_change_trigger_func`:
```sql
        CASE 
            WHEN TG_TABLE_NAME IN ('accounts', 'customers', 'vendors', 'products', 'roles', 'account_types', 'dimensions', 'fiscal_years', 'budgets') THEN (CASE WHEN TG_OP = 'DELETE' THEN OLD.name ELSE NEW.name END)
            WHEN TG_TABLE_NAME = 'journal_entries' THEN (CASE WHEN TG_OP = 'DELETE' THEN OLD.entry_no ELSE NEW.entry_no END)
            WHEN TG_TABLE_NAME = 'sales_invoices' THEN (CASE WHEN TG_OP = 'DELETE' THEN OLD.invoice_no ELSE NEW.invoice_no END)
            WHEN TG_TABLE_NAME = 'purchase_invoices' THEN (CASE WHEN TG_OP = 'DELETE' THEN OLD.invoice_no ELSE NEW.invoice_no END)
            WHEN TG_TABLE_NAME = 'payments' THEN (CASE WHEN TG_OP = 'DELETE' THEN OLD.payment_no ELSE NEW.payment_no END)
            WHEN TG_TABLE_NAME = 'users' THEN (CASE WHEN TG_OP = 'DELETE' THEN OLD.username ELSE NEW.username END)
            WHEN TG_TABLE_NAME = 'tax_codes' THEN (CASE WHEN TG_OP = 'DELETE' THEN OLD.code ELSE NEW.code END)
            WHEN TG_TABLE_NAME = 'gst_returns' THEN (CASE WHEN TG_OP = 'DELETE' THEN OLD.return_period ELSE NEW.return_period END)
            ELSE CASE WHEN TG_OP = 'DELETE' THEN OLD.id::TEXT ELSE NEW.id::TEXT END -- Default case uses OLD.id
        END,
```
If `TG_OP = 'DELETE'` and the table is not one of the explicitly listed ones, it defaults to `OLD.id::TEXT`. This part is fine.
The error `record "old" has no field "entry_no"` specifically means that `TG_TABLE_NAME` *was* `'journal_entries'`, `TG_OP` *was* `'DELETE'`, and the record referred to by `OLD` (a row from `journal_entries`) somehow did not have an `entry_no` field. This is highly unlikely if the schema is correct because `journal_entries` *does* have `entry_no`.

This specific error (`record "old" has no field "entry_no"`) did *not* appear when running `initial_data.sql` directly with `psql`. This suggests that `db_init.py` might be doing something *additional* or in a different context.
The `db_init.py` script:
1. Terminates connections (if `drop_existing`).
2. Drops database (if `drop_existing`).
3. Creates database.
4. Connects to the new database.
5. Executes `schema.sql`.
6. Executes `initial_data.sql`.

The error must be happening during step 5 or 6 when executed via `db_init.py`.
Perhaps the `asyncpg` execution of `schema.sql` has a subtle difference in how it handles errors or state compared to `psql`.

Let's re-focus on the errors from `psql scripts/initial_data.sql` as they are more direct:
`psql:scripts/initial_data.sql:16: ERROR:  record "new" has no field "created_by"`
`CONTEXT:  PL/pgSQL assignment "v_user_id := CASE WHEN TG_OP = 'INSERT' AND NEW.created_by IS NOT NULL THEN NEW.created_by ..."`
This context points to the `v_user_id` assignment block. My last proposed `v_user_id` logic was:
```sql
    IF v_user_id IS NULL THEN
        -- For tables that have created_by/updated_by columns (most tables)
        IF TG_OP = 'INSERT' THEN
            BEGIN v_user_id := NEW.created_by; EXCEPTION WHEN undefined_column THEN v_user_id := NULL; END;
        ELSIF TG_OP = 'UPDATE' THEN
            BEGIN v_user_id := NEW.updated_by; EXCEPTION WHEN undefined_column THEN v_user_id := NULL; END;
        END IF;
        
        -- Special handling for core.users table itself if user_id is still NULL
        IF v_user_id IS NULL AND TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN
            IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
                 v_user_id := NEW.id; 
            END IF;
        END IF;
    END IF;
```
The error message's context `PL/pgSQL assignment "v_user_id := CASE ..."` suggests that the `CASE` statement logic from the *reference schema* (which I had initially, and then tried to replace with dynamic/exception-based logic) is still somehow in play or my latest version of the trigger with `EXCEPTION WHEN undefined_column` was not what got executed by `psql`.

The `psql` error clearly shows this specific `CASE` statement is the source of the problem:
`v_user_id := CASE WHEN TG_OP = 'INSERT' AND NEW.created_by IS NOT NULL THEN NEW.created_by WHEN TG_OP = 'UPDATE' AND NEW.updated_by IS NOT NULL THEN NEW.updated_by ELSE NULL END`

This `CASE` statement will indeed fail if `NEW.created_by` (or `NEW.updated_by`) does not exist on the table being inserted/updated. This happens for `core.permissions` (line 16 of `initial_data.sql`) and `core.users` (line 149 of `initial_data.sql`).

**The Core Problem:** The audit trigger's logic for fetching `created_by`/`updated_by` is not robust enough for tables that lack these columns but are being audited.

**Solution Path:**
1.  **Identify all tables being audited:** The `tables_to_audit` array in `scripts/schema.sql` is the list.
    ```
    'accounting.accounts', 'accounting.journal_entries', 'accounting.fiscal_periods', 'accounting.fiscal_years',
    'business.customers', 'business.vendors', 'business.products', 
    'business.sales_invoices', 'business.purchase_invoices', 'business.payments',
    'accounting.tax_codes', 'accounting.gst_returns',
    'core.users', 'core.roles', 'core.company_settings'
    ```
2.  **Check which of these tables lack `created_by`/`updated_by` columns**:
    *   `core.users`: Has `id`, `username`, etc. **Does not have `created_by`, `updated_by` columns.**
    *   `core.roles`: Has `id`, `name`, `description`, `created_at`, `updated_at`. **Does not have `created_by`, `updated_by` columns.**
    *   `core.company_settings`: Has `updated_by`. **Does not have `created_by` column.** (Though it has `updated_by` which the CASE statement checks).
    *   Other tables in the list (e.g., `accounting.accounts`, `accounting.journal_entries`, etc.) *do* have `created_by` and `updated_by`.

The trigger will fail on `INSERT` into `core.users` and `core.roles`. It will also fail on `INSERT` into `core.company_settings` because `NEW.created_by` doesn't exist.

The `EXCEPTION WHEN undefined_column` approach is the correct general way to handle this.
The `psql` output's context showing the `CASE` statement indicates the version of `audit.log_data_change_trigger_func` with the `EXCEPTION` blocks was not the one that ran. I need to ensure that the function definition in `scripts/schema.sql` is *definitely* the one with the robust exception handling for `NEW.created_by` and `NEW.updated_by`.

Let's re-paste the corrected trigger function logic again, ensuring it's exactly what should be in the schema file.

```sql
CREATE OR REPLACE FUNCTION audit.log_data_change_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    v_old_data JSONB;
    v_new_data JSONB;
    v_change_type VARCHAR(20);
    v_user_id INTEGER;
    column_name TEXT; 
BEGIN
    -- Try to get user_id from session variable
    BEGIN
        v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER;
    EXCEPTION WHEN OTHERS THEN
        v_user_id := NULL; 
    END;

    -- If session user_id is not set, try to get from record's audit columns
    IF v_user_id IS NULL THEN
        IF TG_OP = 'INSERT' THEN
            BEGIN
                v_user_id := NEW.created_by;
            EXCEPTION WHEN undefined_column THEN
                -- Try alternative common name if 'created_by' is not found or if table is 'core.users'
                IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN
                    v_user_id := NEW.id; -- For user creation, user itself is the "creator" in audit log if no session user
                ELSE
                    v_user_id := NULL; 
                END IF;
            END;
        ELSIF TG_OP = 'UPDATE' THEN
            BEGIN
                v_user_id := NEW.updated_by;
            EXCEPTION WHEN undefined_column THEN
                 -- Try alternative common name if 'updated_by' is not found or if table is 'core.users'
                IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN
                     v_user_id := NEW.id; -- For user update, user itself is the "updater" if no session user
                ELSE
                    v_user_id := NULL;
                END IF;
            END;
        END IF;
    END IF;
    
    -- Do not log changes to audit tables themselves to prevent recursion
    IF TG_TABLE_SCHEMA = 'audit' AND TG_TABLE_NAME IN ('audit_log', 'data_change_history') THEN
        RETURN NULL; 
    END IF;

    IF TG_OP = 'INSERT' THEN
        v_change_type := 'Insert';
        v_old_data := NULL;
        v_new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN
        v_change_type := 'Update';
        v_old_data := to_jsonb(OLD);
        v_new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'DELETE' THEN
        v_change_type := 'Delete';
        v_old_data := to_jsonb(OLD);
        v_new_data := NULL;
    END IF;
    
    -- Determine entity_id safely
    DECLARE
        v_entity_id INTEGER;
    BEGIN
        IF TG_OP = 'DELETE' THEN
            v_entity_id := OLD.id;
        ELSE
            v_entity_id := NEW.id;
        END IF;
    EXCEPTION WHEN undefined_column THEN
        v_entity_id := NULL; -- Fallback if 'id' column doesn't exist (should not happen for audited tables)
    END;

    -- Determine entity_name safely
    DECLARE
        v_entity_name VARCHAR(200);
    BEGIN
        IF TG_OP = 'DELETE' THEN
            v_entity_name := CASE 
                WHEN TG_TABLE_NAME IN ('accounts', 'customers', 'vendors', 'products', 'roles', 'account_types', 'dimensions', 'fiscal_years', 'budgets') THEN OLD.name
                WHEN TG_TABLE_NAME = 'journal_entries' THEN OLD.entry_no
                WHEN TG_TABLE_NAME = 'sales_invoices' THEN OLD.invoice_no
                WHEN TG_TABLE_NAME = 'purchase_invoices' THEN OLD.invoice_no
                WHEN TG_TABLE_NAME = 'payments' THEN OLD.payment_no
                WHEN TG_TABLE_NAME = 'users' THEN OLD.username
                WHEN TG_TABLE_NAME = 'tax_codes' THEN OLD.code
                WHEN TG_TABLE_NAME = 'gst_returns' THEN OLD.return_period
                ELSE OLD.id::TEXT
            END;
        ELSE
            v_entity_name := CASE 
                WHEN TG_TABLE_NAME IN ('accounts', 'customers', 'vendors', 'products', 'roles', 'account_types', 'dimensions', 'fiscal_years', 'budgets') THEN NEW.name
                WHEN TG_TABLE_NAME = 'journal_entries' THEN NEW.entry_no
                WHEN TG_TABLE_NAME = 'sales_invoices' THEN NEW.invoice_no
                WHEN TG_TABLE_NAME = 'purchase_invoices' THEN NEW.invoice_no
                WHEN TG_TABLE_NAME = 'payments' THEN NEW.payment_no
                WHEN TG_TABLE_NAME = 'users' THEN NEW.username
                WHEN TG_TABLE_NAME = 'tax_codes' THEN NEW.code
                WHEN TG_TABLE_NAME = 'gst_returns' THEN NEW.return_period
                ELSE NEW.id::TEXT
            END;
        END IF;
    EXCEPTION WHEN undefined_column THEN
        IF TG_OP = 'DELETE' THEN
            BEGIN v_entity_name := OLD.id::TEXT; EXCEPTION WHEN undefined_column THEN v_entity_name := NULL; END;
        ELSE
            BEGIN v_entity_name := NEW.id::TEXT; EXCEPTION WHEN undefined_column THEN v_entity_name := NULL; END;
        END IF;
    END;

    INSERT INTO audit.audit_log (
        user_id, action, entity_type, entity_id, entity_name, changes, timestamp
    ) VALUES (
        v_user_id,
        v_change_type,
        TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
        v_entity_id,
        v_entity_name,
        jsonb_build_object('old', v_old_data, 'new', v_new_data),
        CURRENT_TIMESTAMP
    );
    
    IF TG_OP = 'UPDATE' THEN
        FOR column_name IN 
            SELECT key 
            FROM jsonb_object_keys(v_old_data) 
        LOOP
            IF (v_new_data ? column_name) AND ((v_old_data -> column_name) IS DISTINCT FROM (v_new_data -> column_name)) THEN
                INSERT INTO audit.data_change_history (
                    table_name, record_id, field_name, old_value, new_value,
                    change_type, changed_by, changed_at
                ) VALUES (
                    TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
                    NEW.id, -- Assuming NEW.id always exists for UPDATE
                    column_name,
                    v_old_data ->> column_name,
                    v_new_data ->> column_name,
                    'Update',
                    v_user_id,
                    CURRENT_TIMESTAMP
                );
            END IF;
        END LOOP;
    END IF;
    
    RETURN NULL; 
END;
$$ LANGUAGE plpgsql;
```
This revised trigger function is more robust in accessing fields from `NEW` or `OLD` records by wrapping potentially problematic accesses in `BEGIN...EXCEPTION WHEN undefined_column...END` blocks. This should prevent the "record ... has no field ..." errors.

The `record "old" has no field "entry_no"` from `db_init.py` is still a bit puzzling if no `DELETE` on `journal_entries` is happening. However, if the more robust trigger above fixes the `created_by` issues, the overall script execution might proceed further or change behavior. The `db_init.py` might be swallowing the exact PL/pgSQL context that `psql` shows.

Let's provide the schema with this very robust trigger function.

The foreign key violations (`Key (created_by)=(1) is not present in table "users"`) are a direct consequence of the `INSERT INTO core.users ... VALUES (1, ...)` failing (or being rolled back) due to the audit trigger error on `core.users`. If the audit trigger is fixed, user 1 will be created, and subsequent FKs will pass.

One last check on the `tables_to_audit` list in `scripts/schema.sql`. The `db_init.py` error `record "old" has no field "entry_no"` implies a DELETE operation on `journal_entries`. This shouldn't happen during `schema.sql` or `initial_data.sql`. If the `initial_data.sql` is re-runnable, `ON CONFLICT DO NOTHING` is used, which isn't a DELETE. Perhaps a `DROP TRIGGER IF EXISTS` followed by `CREATE TRIGGER` could be misinterperted if the function it points to is faulty from a *previous* incomplete run of `schema.sql`? `db_init.py` tries to run `schema.sql` cleanly.

The `db_init.py` message `Error during database creation/initialization: record "old" has no field "entry_no"` must come from the execution of `schema.sql` or `initial_data.sql` by `asyncpg`.
If `schema.sql` completes, and then `initial_data.sql` starts, the `INSERT INTO core.permissions` (line 16) happens.
The error "record 'old' has no field 'entry_no'" can *only* occur if `TG_OP = 'DELETE'` and `TG_TABLE_NAME = 'journal_entries'`. This is not happening during `INSERT INTO core.permissions`.

This suggests the error reported by `db_init.py` might be a red herring or a misreported error from `asyncpg` for a different underlying issue. The `psql` errors are more reliable for debugging SQL script issues. The `record "new" has no field "created_by"` is the primary issue from `psql`.

The `entity_name` part of the trigger function needs the same robustness:
```sql
    -- Determine entity_name safely
    DECLARE
        v_entity_name VARCHAR(200);
        temp_val TEXT;
    BEGIN
        IF TG_OP = 'DELETE' THEN
            SELECT CASE 
                WHEN TG_TABLE_NAME IN ('accounts', 'customers', 'vendors', 'products', 'roles', 'account_types', 'dimensions', 'fiscal_years', 'budgets') THEN OLD.name
                WHEN TG_TABLE_NAME = 'journal_entries' THEN OLD.entry_no
                -- ... other specific cases for OLD ...
                ELSE OLD.id::TEXT
            END INTO temp_val;
        ELSE
            SELECT CASE 
                WHEN TG_TABLE_NAME IN ('accounts', 'customers', 'vendors', 'products', 'roles', 'account_types', 'dimensions', 'fiscal_years', 'budgets') THEN NEW.name
                WHEN TG_TABLE_NAME = 'journal_entries' THEN NEW.entry_no
                -- ... other specific cases for NEW ...
                ELSE NEW.id::TEXT
            END INTO temp_val;
        END IF;
        v_entity_name := temp_val;
    EXCEPTION WHEN undefined_column THEN
        -- Fallback if specific named column (name, entry_no, etc.) doesn't exist
        IF TG_OP = 'DELETE' THEN
            BEGIN temp_val := OLD.id::TEXT; EXCEPTION WHEN undefined_column THEN temp_val := NULL; END;
        ELSE
            BEGIN temp_val := NEW.id::TEXT; EXCEPTION WHEN undefined_column THEN temp_val := NULL; END;
        END IF;
        v_entity_name := temp_val;
    END;
```
This revised logic for `v_entity_name` also uses `EXCEPTION WHEN undefined_column` to handle cases where `OLD.name` or `NEW.name` (or other specific fields like `entry_no`) might not exist for a particular table, falling back to `id`. This should prevent the `record "old" has no field "entry_no"` if a table without `entry_no` was somehow being processed by that specific branch of the `CASE` statement (which shouldn't happen with the current CASE structure, but robustness is good).

The error `record "old" has no field "entry_no"` must mean the `CASE` statement for `entity_name` is taking the `WHEN TG_TABLE_NAME = 'journal_entries'` path, `TG_OP` is `DELETE`, but `OLD` (which should be a `journal_entries` row) doesn't have `entry_no`. This is a schema contradiction.
Could the `entity_name` part be simplified to always use `id` if `name` is not present for all tables?
The reference schema does:
```sql
        CASE 
            WHEN TG_TABLE_NAME = 'accounts' THEN (CASE WHEN TG_OP = 'DELETE' THEN OLD.name ELSE NEW.name END)
            WHEN TG_TABLE_NAME = 'customers' THEN (CASE WHEN TG_OP = 'DELETE' THEN OLD.name ELSE NEW.name END)
            -- ... many such cases ...
            ELSE CASE WHEN TG_OP = 'DELETE' THEN OLD.id::TEXT ELSE NEW.id::TEXT END
        END,
```
This explicit listing is safer. My prior `scripts/schema.sql` used `TG_TABLE_NAME IN (...) THEN OLD.name/NEW.name`. This is equivalent.
The error `record "old" has no field "entry_no"` remains the most peculiar one if it's from `db_init.py` but not `psql` on the same script part.

Let's ensure all `NEW.column` or `OLD.column` accesses within the audit trigger are wrapped in `BEGIN...EXCEPTION` blocks if the column is not universally present across all audited tables. `id` is assumed to be universal for audited tables. `name` is common. `created_by`/`updated_by` are not.

The most robust way to handle `v_user_id` and `v_entity_name` is to use dynamic SQL with `EXECUTE format(...)` to build a query that only selects `created_by` or `name` if the column exists, but this is overly complex for a trigger. The `EXCEPTION WHEN undefined_column` is the standard PL/pgSQL way.

The provided `psql` log clearly shows the error originates from the `v_user_id` assignment using the `CASE` statement. This means the SQL that `psql` is running for `scripts/initial_data.sql` is encountering an audit trigger definition that looks like the one from the reference schema, not my latest proposed one with `EXCEPTION WHEN undefined_column`.

It's critical that the `scripts/schema.sql` file being executed by `db_init.py` *actually contains* the updated trigger function. I will provide the corrected schema again.

```sql
-- File: scripts/schema.sql
-- ============================================================================
-- SG Bookkeeper - Complete Database Schema
-- ============================================================================
-- This script creates the complete database schema for the SG Bookkeeper application,
-- a Singapore-compliant accounting system for small businesses.
--
-- The schema is organized into four main schemas:
-- 1. core: System tables and configuration
-- 2. accounting: Core accounting tables
-- 3. business: Business operations tables
-- 4. audit: Audit and logging tables
--
-- Author: SG Bookkeeper Development Team
-- Version: 1.0.0
-- ============================================================================

-- ============================================================================
-- INITIAL SETUP
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;     -- For password encryption and general cryptographic functions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements; -- For query performance monitoring
CREATE EXTENSION IF NOT EXISTS btree_gist;   -- For exclusion constraints (e.g., preventing overlapping periods)

-- Create schemas
CREATE SCHEMA IF NOT EXISTS core;       -- Core system functionality
CREATE SCHEMA IF NOT EXISTS accounting; -- Accounting-related tables
CREATE SCHEMA IF NOT EXISTS business;   -- Business operations tables
CREATE SCHEMA IF NOT EXISTS audit;      -- Audit and logging

-- Set search path
SET search_path TO core, accounting, business, audit, public;

-- ============================================================================
-- CORE SCHEMA TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Users Table
-- ----------------------------------------------------------------------------
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

COMMENT ON TABLE core.users IS 'Stores user accounts for application access';
COMMENT ON COLUMN core.users.id IS 'Unique identifier for the user';
COMMENT ON COLUMN core.users.username IS 'Username for login (must be unique)';
COMMENT ON COLUMN core.users.password_hash IS 'Securely hashed password using pgcrypto';
COMMENT ON COLUMN core.users.email IS 'User email address for notifications';
COMMENT ON COLUMN core.users.full_name IS 'User''s full name for display';
COMMENT ON COLUMN core.users.is_active IS 'Whether the user account is currently active';
COMMENT ON COLUMN core.users.failed_login_attempts IS 'Count of consecutive failed login attempts';
COMMENT ON COLUMN core.users.last_login_attempt IS 'Timestamp of last login attempt';
COMMENT ON COLUMN core.users.last_login IS 'Timestamp of last successful login';
COMMENT ON COLUMN core.users.require_password_change IS 'Flag indicating if user must change password at next login';

-- ----------------------------------------------------------------------------
-- Roles Table
-- ----------------------------------------------------------------------------
CREATE TABLE core.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE core.roles IS 'Defines user roles for role-based access control';
COMMENT ON COLUMN core.roles.id IS 'Unique identifier for the role';
COMMENT ON COLUMN core.roles.name IS 'Role name (e.g., Administrator, Accountant)';
COMMENT ON COLUMN core.roles.description IS 'Detailed description of the role and its purpose';

-- ----------------------------------------------------------------------------
-- Permissions Table
-- ----------------------------------------------------------------------------
CREATE TABLE core.permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    module VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE core.permissions IS 'Defines granular permissions for system actions';
COMMENT ON COLUMN core.permissions.id IS 'Unique identifier for the permission';
COMMENT ON COLUMN core.permissions.code IS 'Unique code for the permission (e.g., ACCOUNT_CREATE)';
COMMENT ON COLUMN core.permissions.description IS 'Human-readable description of the permission';
COMMENT ON COLUMN core.permissions.module IS 'Functional module the permission belongs to';

-- ----------------------------------------------------------------------------
-- Role Permissions Table
-- ----------------------------------------------------------------------------
CREATE TABLE core.role_permissions (
    role_id INTEGER NOT NULL REFERENCES core.roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES core.permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

COMMENT ON TABLE core.role_permissions IS 'Maps permissions to roles (many-to-many)';
COMMENT ON COLUMN core.role_permissions.role_id IS 'Reference to the role';
COMMENT ON COLUMN core.role_permissions.permission_id IS 'Reference to the permission';

-- ----------------------------------------------------------------------------
-- User Roles Table
-- ----------------------------------------------------------------------------
CREATE TABLE core.user_roles (
    user_id INTEGER NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES core.roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

COMMENT ON TABLE core.user_roles IS 'Maps roles to users (many-to-many)';
COMMENT ON COLUMN core.user_roles.user_id IS 'Reference to the user';
COMMENT ON COLUMN core.user_roles.role_id IS 'Reference to the role';

-- ----------------------------------------------------------------------------
-- Company Settings Table
-- ----------------------------------------------------------------------------
CREATE TABLE core.company_settings (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    legal_name VARCHAR(200),
    uen_no VARCHAR(20),
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
    logo BYTEA,
    fiscal_year_start_month INTEGER DEFAULT 1 CHECK (fiscal_year_start_month BETWEEN 1 AND 12),
    fiscal_year_start_day INTEGER DEFAULT 1 CHECK (fiscal_year_start_day BETWEEN 1 AND 31),
    base_currency VARCHAR(3) DEFAULT 'SGD',
    tax_id_label VARCHAR(50) DEFAULT 'UEN',
    date_format VARCHAR(20) DEFAULT 'yyyy-MM-dd',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES core.users(id)
);

COMMENT ON TABLE core.company_settings IS 'Stores company information and global application settings';
COMMENT ON COLUMN core.company_settings.company_name IS 'Display name of the company';
COMMENT ON COLUMN core.company_settings.legal_name IS 'Legal registered name of the company';
COMMENT ON COLUMN core.company_settings.uen_no IS 'Unique Entity Number (Singapore business identifier)';
COMMENT ON COLUMN core.company_settings.gst_registration_no IS 'GST registration number (if registered)';
COMMENT ON COLUMN core.company_settings.gst_registered IS 'Whether the company is registered for GST';
COMMENT ON COLUMN core.company_settings.fiscal_year_start_month IS 'Month when fiscal year starts (1-12)';
COMMENT ON COLUMN core.company_settings.fiscal_year_start_day IS 'Day when fiscal year starts (1-31)';
COMMENT ON COLUMN core.company_settings.base_currency IS 'Default currency for the company (ISO code)';

-- ----------------------------------------------------------------------------
-- Configuration Table
-- ----------------------------------------------------------------------------
CREATE TABLE core.configuration (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value TEXT,
    description VARCHAR(200),
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES core.users(id)
);

COMMENT ON TABLE core.configuration IS 'Stores application configuration parameters';
COMMENT ON COLUMN core.configuration.config_key IS 'Unique key for the configuration parameter';
COMMENT ON COLUMN core.configuration.config_value IS 'Value of the configuration parameter';
COMMENT ON COLUMN core.configuration.description IS 'Description of what the parameter controls';
COMMENT ON COLUMN core.configuration.is_encrypted IS 'Whether the value is stored encrypted';

-- ----------------------------------------------------------------------------
-- Sequences Table
-- ----------------------------------------------------------------------------
CREATE TABLE core.sequences (
    id SERIAL PRIMARY KEY,
    sequence_name VARCHAR(50) NOT NULL UNIQUE,
    prefix VARCHAR(10),
    suffix VARCHAR(10),
    next_value INTEGER NOT NULL DEFAULT 1,
    increment_by INTEGER NOT NULL DEFAULT 1,
    min_value INTEGER NOT NULL DEFAULT 1,
    max_value INTEGER NOT NULL DEFAULT 2147483647,
    cycle BOOLEAN DEFAULT FALSE,
    format_template VARCHAR(50) DEFAULT '{PREFIX}{VALUE}{SUFFIX}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE core.sequences IS 'Manages document numbering sequences (invoices, journals, etc.)';
COMMENT ON COLUMN core.sequences.sequence_name IS 'Unique name of the sequence (e.g., INVOICE, JOURNAL)';
COMMENT ON COLUMN core.sequences.prefix IS 'Optional prefix for generated numbers (e.g., INV-)';
COMMENT ON COLUMN core.sequences.suffix IS 'Optional suffix for generated numbers (e.g., -2023)';
COMMENT ON COLUMN core.sequences.next_value IS 'Next value to be generated';
COMMENT ON COLUMN core.sequences.format_template IS 'Template for formatting sequence values';

-- ============================================================================
-- ACCOUNTING SCHEMA TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Account Types Table
-- ----------------------------------------------------------------------------
CREATE TABLE accounting.account_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    category VARCHAR(20) NOT NULL CHECK (category IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')),
    is_debit_balance BOOLEAN NOT NULL,
    report_type VARCHAR(30) NOT NULL,
    display_order INTEGER NOT NULL,
    description VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE accounting.account_types IS 'Defines standard account types for the chart of accounts';
COMMENT ON COLUMN accounting.account_types.name IS 'Name of the account type (e.g., Current Asset, Fixed Asset)';
COMMENT ON COLUMN accounting.account_types.category IS 'Major category (Asset, Liability, Equity, Revenue, Expense)';
COMMENT ON COLUMN accounting.account_types.is_debit_balance IS 'Whether accounts of this type normally have debit balances';
COMMENT ON COLUMN accounting.account_types.report_type IS 'Financial report section where this appears';
COMMENT ON COLUMN accounting.account_types.display_order IS 'Order in which to display in reports and lists';

-- ----------------------------------------------------------------------------
-- Accounts Table
-- ----------------------------------------------------------------------------
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

COMMENT ON TABLE accounting.accounts IS 'Chart of accounts - fundamental structure for the accounting system';
COMMENT ON COLUMN accounting.accounts.code IS 'Account code (unique identifier used in transaction entry)';
COMMENT ON COLUMN accounting.accounts.name IS 'Descriptive name of the account';
COMMENT ON COLUMN accounting.accounts.account_type IS 'Primary account type (Asset, Liability, Equity, Revenue, Expense)';
COMMENT ON COLUMN accounting.accounts.sub_type IS 'More specific categorization within the account type';
COMMENT ON COLUMN accounting.accounts.tax_treatment IS 'How this account is treated for tax purposes';
COMMENT ON COLUMN accounting.accounts.gst_applicable IS 'Whether transactions in this account can have GST applied';
COMMENT ON COLUMN accounting.accounts.is_active IS 'Whether this account is available for new transactions';
COMMENT ON COLUMN accounting.accounts.parent_id IS 'Parent account for hierarchical chart of accounts';
COMMENT ON COLUMN accounting.accounts.is_control_account IS 'Whether this is a control account linked to a subsidiary ledger';
COMMENT ON COLUMN accounting.accounts.is_bank_account IS 'Whether this account represents a bank account for reconciliation';

CREATE INDEX idx_accounts_parent_id ON accounting.accounts(parent_id);
CREATE INDEX idx_accounts_is_active ON accounting.accounts(is_active);
CREATE INDEX idx_accounts_account_type ON accounting.accounts(account_type);

-- ----------------------------------------------------------------------------
-- Fiscal Years Table
-- ----------------------------------------------------------------------------
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

COMMENT ON TABLE accounting.fiscal_years IS 'Defines fiscal years for financial reporting';
COMMENT ON COLUMN accounting.fiscal_years.year_name IS 'Descriptive name for the fiscal year (e.g., FY2023)';
COMMENT ON COLUMN accounting.fiscal_years.start_date IS 'Start date of the fiscal year';
COMMENT ON COLUMN accounting.fiscal_years.end_date IS 'End date of the fiscal year';
COMMENT ON COLUMN accounting.fiscal_years.is_closed IS 'Whether the fiscal year is closed for new transactions';
COMMENT ON COLUMN accounting.fiscal_years.closed_date IS 'When the fiscal year was closed';
COMMENT ON COLUMN accounting.fiscal_years.closed_by IS 'User who closed the fiscal year';

-- ----------------------------------------------------------------------------
-- Fiscal Periods Table
-- ----------------------------------------------------------------------------
CREATE TABLE accounting.fiscal_periods (
    id SERIAL PRIMARY KEY,
    fiscal_year_id INTEGER NOT NULL REFERENCES accounting.fiscal_years(id),
    name VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    period_type VARCHAR(10) NOT NULL CHECK (period_type IN ('Month', 'Quarter', 'Year')),
    status VARCHAR(10) NOT NULL CHECK (status IN ('Open', 'Closed', 'Archived')),
    period_number INTEGER NOT NULL,
    is_adjustment BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id),
    CONSTRAINT fp_date_range_check CHECK (start_date <= end_date),
    CONSTRAINT fp_unique_period_dates UNIQUE (fiscal_year_id, period_type, period_number)
);

COMMENT ON TABLE accounting.fiscal_periods IS 'Defines accounting periods within fiscal years';
COMMENT ON COLUMN accounting.fiscal_periods.fiscal_year_id IS 'Reference to the parent fiscal year';
COMMENT ON COLUMN accounting.fiscal_periods.name IS 'Name of the period (e.g., January 2023)';
COMMENT ON COLUMN accounting.fiscal_periods.start_date IS 'Start date of the period';
COMMENT ON COLUMN accounting.fiscal_periods.end_date IS 'End date of the period';
COMMENT ON COLUMN accounting.fiscal_periods.period_type IS 'Type of period (Month, Quarter, Year)';
COMMENT ON COLUMN accounting.fiscal_periods.status IS 'Current status of the period (Open, Closed, Archived)';
COMMENT ON COLUMN accounting.fiscal_periods.period_number IS 'Sequential number within the fiscal year';
COMMENT ON COLUMN accounting.fiscal_periods.is_adjustment IS 'Whether this is a special adjustment period';

CREATE INDEX idx_fiscal_periods_dates ON accounting.fiscal_periods(start_date, end_date);
CREATE INDEX idx_fiscal_periods_status ON accounting.fiscal_periods(status);

-- ----------------------------------------------------------------------------
-- Currencies Table
-- ----------------------------------------------------------------------------
CREATE TABLE accounting.currencies (
    code CHAR(3) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    decimal_places INTEGER DEFAULT 2,
    format_string VARCHAR(20) DEFAULT '#,##0.00',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES core.users(id),
    updated_by INTEGER REFERENCES core.users(id)
);

COMMENT ON TABLE accounting.currencies IS 'Stores currency information for multi-currency support';
COMMENT ON COLUMN accounting.currencies.code IS 'ISO 4217 currency code (e.g., SGD, USD)';
COMMENT ON COLUMN accounting.currencies.name IS 'Full name of the currency (e.g., Singapore Dollar)';
COMMENT ON COLUMN accounting.currencies.symbol IS 'Currency symbol (e.g., $, €)';
COMMENT ON COLUMN accounting.currencies.decimal_places IS 'Number of decimal places for the currency';
COMMENT ON COLUMN accounting.currencies.format_string IS 'Format pattern for displaying amounts';

-- ----------------------------------------------------------------------------
-- Exchange Rates Table
-- ----------------------------------------------------------------------------
CREATE TABLE accounting.exchange_rates (
    id SERIAL PRIMARY KEY,
    from_currency CHAR(3) NOT NULL REFERENCES accounting.currencies(code),
    to_currency CHAR(3) NOT NULL REFERENCES accounting.currencies(code),
    rate_date DATE NOT NULL,
    exchange_rate NUMERIC(15,6) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES core.users(id),
    updated_by INTEGER REFERENCES core.users(id),
    CONSTRAINT uq_exchange_rates_pair_date UNIQUE (from_currency, to_currency, rate_date)
);

COMMENT ON TABLE accounting.exchange_rates IS 'Stores currency exchange rates for specific dates';
COMMENT ON COLUMN accounting.exchange_rates.from_currency IS 'Source currency code';
COMMENT ON COLUMN accounting.exchange_rates.to_currency IS 'Target currency code';
COMMENT ON COLUMN accounting.exchange_rates.rate_date IS 'Date for which the exchange rate is valid';
COMMENT ON COLUMN accounting.exchange_rates.exchange_rate IS 'Exchange rate (amount of to_currency per unit of from_currency)';

CREATE INDEX idx_exchange_rates_lookup ON accounting.exchange_rates(from_currency, to_currency, rate_date);

-- ----------------------------------------------------------------------------
-- Journal Entries Table
-- ----------------------------------------------------------------------------
CREATE TABLE accounting.journal_entries (
    id SERIAL PRIMARY KEY,
    entry_no VARCHAR(20) NOT NULL UNIQUE,
    journal_type VARCHAR(20) NOT NULL,
    entry_date DATE NOT NULL,
    fiscal_period_id INTEGER NOT NULL REFERENCES accounting.fiscal_periods(id),
    description VARCHAR(500),
    reference VARCHAR(100),
    is_recurring BOOLEAN DEFAULT FALSE,
    recurring_pattern_id INTEGER, 
    is_posted BOOLEAN DEFAULT FALSE,
    is_reversed BOOLEAN DEFAULT FALSE,
    reversing_entry_id INTEGER REFERENCES accounting.journal_entries(id),
    source_type VARCHAR(50),
    source_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);

COMMENT ON TABLE accounting.journal_entries IS 'Header table for accounting journal entries';
COMMENT ON COLUMN accounting.journal_entries.entry_no IS 'Unique reference number for the journal entry';
COMMENT ON COLUMN accounting.journal_entries.journal_type IS 'Type of journal (General, Sales, Purchase, etc.)';
COMMENT ON COLUMN accounting.journal_entries.entry_date IS 'Accounting date for the entry';
COMMENT ON COLUMN accounting.journal_entries.fiscal_period_id IS 'Fiscal period to which this entry belongs';
COMMENT ON COLUMN accounting.journal_entries.description IS 'Description of the journal entry';
COMMENT ON COLUMN accounting.journal_entries.reference IS 'External reference (e.g., invoice number)';
COMMENT ON COLUMN accounting.journal_entries.is_recurring IS 'Whether this is a recurring entry template';
COMMENT ON COLUMN accounting.journal_entries.is_posted IS 'Whether the entry has been posted (finalized)';
COMMENT ON COLUMN accounting.journal_entries.is_reversed IS 'Whether the entry has been reversed';
COMMENT ON COLUMN accounting.journal_entries.reversing_entry_id IS 'Reference to the reversing entry, if any';
COMMENT ON COLUMN accounting.journal_entries.source_type IS 'Origin system/module that created this entry';
COMMENT ON COLUMN accounting.journal_entries.source_id IS 'ID in the source system/module';

CREATE INDEX idx_journal_entries_date ON accounting.journal_entries(entry_date);
CREATE INDEX idx_journal_entries_fiscal_period ON accounting.journal_entries(fiscal_period_id);
CREATE INDEX idx_journal_entries_source ON accounting.journal_entries(source_type, source_id);
CREATE INDEX idx_journal_entries_posted ON accounting.journal_entries(is_posted);

-- ----------------------------------------------------------------------------
-- Journal Entry Lines Table
-- ----------------------------------------------------------------------------
CREATE TABLE accounting.journal_entry_lines (
    id SERIAL PRIMARY KEY,
    journal_entry_id INTEGER NOT NULL REFERENCES accounting.journal_entries(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    account_id INTEGER NOT NULL REFERENCES accounting.accounts(id),
    description VARCHAR(200),
    debit_amount NUMERIC(15,2) DEFAULT 0,
    credit_amount NUMERIC(15,2) DEFAULT 0,
    currency_code CHAR(3) DEFAULT 'SGD' REFERENCES accounting.currencies(code),
    exchange_rate NUMERIC(15,6) DEFAULT 1,
    tax_code VARCHAR(20), 
    tax_amount NUMERIC(15,2) DEFAULT 0,
    dimension1_id INTEGER, 
    dimension2_id INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT jel_check_debit_credit CHECK (
        (debit_amount > 0 AND credit_amount = 0) OR
        (credit_amount > 0 AND debit_amount = 0) OR
        (debit_amount = 0 AND credit_amount = 0)
    )
);

COMMENT ON TABLE accounting.journal_entry_lines IS 'Detail lines for journal entries (debits and credits)';
COMMENT ON COLUMN accounting.journal_entry_lines.journal_entry_id IS 'Reference to parent journal entry';
COMMENT ON COLUMN accounting.journal_entry_lines.line_number IS 'Sequential line number within the journal entry';
COMMENT ON COLUMN accounting.journal_entry_lines.account_id IS 'Account being debited or credited';
COMMENT ON COLUMN accounting.journal_entry_lines.description IS 'Line item description';
COMMENT ON COLUMN accounting.journal_entry_lines.debit_amount IS 'Debit amount (positive value)';
COMMENT ON COLUMN accounting.journal_entry_lines.credit_amount IS 'Credit amount (positive value)';
COMMENT ON COLUMN accounting.journal_entry_lines.currency_code IS 'Currency for this transaction line';
COMMENT ON COLUMN accounting.journal_entry_lines.exchange_rate IS 'Exchange rate to base currency';
COMMENT ON COLUMN accounting.journal_entry_lines.tax_code IS 'Tax code for tax calculation';
COMMENT ON COLUMN accounting.journal_entry_lines.tax_amount IS 'Tax amount calculated for this line';
COMMENT ON COLUMN accounting.journal_entry_lines.dimension1_id IS 'First dimension for analytical accounting';
COMMENT ON COLUMN accounting.journal_entry_lines.dimension2_id IS 'Second dimension for analytical accounting';

CREATE INDEX idx_journal_entry_lines_entry ON accounting.journal_entry_lines(journal_entry_id);
CREATE INDEX idx_journal_entry_lines_account ON accounting.journal_entry_lines(account_id);

-- ----------------------------------------------------------------------------
-- Recurring Patterns Table
-- ----------------------------------------------------------------------------
CREATE TABLE accounting.recurring_patterns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    template_entry_id INTEGER NOT NULL REFERENCES accounting.journal_entries(id),
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly')),
    interval_value INTEGER NOT NULL DEFAULT 1,
    start_date DATE NOT NULL,
    end_date DATE,
    day_of_month INTEGER CHECK (day_of_month BETWEEN 1 AND 31),
    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6),
    last_generated_date DATE,
    next_generation_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);

ALTER TABLE accounting.journal_entries
ADD CONSTRAINT fk_journal_entries_recurring_pattern
FOREIGN KEY (recurring_pattern_id)
REFERENCES accounting.recurring_patterns(id);

COMMENT ON TABLE accounting.recurring_patterns IS 'Defines patterns for recurring journal entries';
COMMENT ON COLUMN accounting.recurring_patterns.name IS 'Name of the recurring pattern';
COMMENT ON COLUMN accounting.recurring_patterns.template_entry_id IS 'Journal entry to use as a template';
COMMENT ON COLUMN accounting.recurring_patterns.frequency IS 'How often to generate entries';
COMMENT ON COLUMN accounting.recurring_patterns.interval_value IS 'Interval units (e.g., every 2 months)';
COMMENT ON COLUMN accounting.recurring_patterns.start_date IS 'Date to start generating entries';
COMMENT ON COLUMN accounting.recurring_patterns.end_date IS 'Date to stop generating entries (if any)';
COMMENT ON COLUMN accounting.recurring_patterns.day_of_month IS 'Specific day of month for monthly patterns';
COMMENT ON COLUMN accounting.recurring_patterns.day_of_week IS 'Specific day of week for weekly patterns';
COMMENT ON COLUMN accounting.recurring_patterns.last_generated_date IS 'When the last entry was generated';
COMMENT ON COLUMN accounting.recurring_patterns.next_generation_date IS 'When the next entry should be generated';

-- ----------------------------------------------------------------------------
-- Dimensions Table
-- ----------------------------------------------------------------------------
CREATE TABLE accounting.dimensions (
    id SERIAL PRIMARY KEY,
    dimension_type VARCHAR(50) NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    parent_id INTEGER REFERENCES accounting.dimensions(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id),
    UNIQUE (dimension_type, code)
);

COMMENT ON TABLE accounting.dimensions IS 'Defines dimensions for analytical accounting';
COMMENT ON COLUMN accounting.dimensions.dimension_type IS 'Type of dimension (Department, Project, etc.)';
COMMENT ON COLUMN accounting.dimensions.code IS 'Short code for the dimension (unique per type)';
COMMENT ON COLUMN accounting.dimensions.name IS 'Name of the dimension';
COMMENT ON COLUMN accounting.dimensions.parent_id IS 'Parent dimension for hierarchical dimensions';

ALTER TABLE accounting.journal_entry_lines
ADD CONSTRAINT fk_jel_dimension1 FOREIGN KEY (dimension1_id) REFERENCES accounting.dimensions(id),
ADD CONSTRAINT fk_jel_dimension2 FOREIGN KEY (dimension2_id) REFERENCES accounting.dimensions(id);

-- ----------------------------------------------------------------------------
-- Budget Table
-- ----------------------------------------------------------------------------
CREATE TABLE accounting.budgets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    fiscal_year_id INTEGER NOT NULL REFERENCES accounting.fiscal_years(id),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);

COMMENT ON TABLE accounting.budgets IS 'Stores budget header information';
COMMENT ON COLUMN accounting.budgets.name IS 'Name of the budget';
COMMENT ON COLUMN accounting.budgets.fiscal_year_id IS 'Fiscal year this budget applies to';
COMMENT ON COLUMN accounting.budgets.description IS 'Detailed description of the budget';
COMMENT ON COLUMN accounting.budgets.is_active IS 'Whether this budget is currently active';

-- ----------------------------------------------------------------------------
-- Budget Details Table
-- ----------------------------------------------------------------------------
CREATE TABLE accounting.budget_details (
    id SERIAL PRIMARY KEY,
    budget_id INTEGER NOT NULL REFERENCES accounting.budgets(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES accounting.accounts(id),
    fiscal_period_id INTEGER NOT NULL REFERENCES accounting.fiscal_periods(id),
    amount NUMERIC(15,2) NOT NULL,
    dimension1_id INTEGER REFERENCES accounting.dimensions(id),
    dimension2_id INTEGER REFERENCES accounting.dimensions(id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);

CREATE UNIQUE INDEX uix_budget_details_key ON accounting.budget_details (
    budget_id, 
    account_id, 
    fiscal_period_id, 
    COALESCE(dimension1_id, 0), 
    COALESCE(dimension2_id, 0)
);

COMMENT ON TABLE accounting.budget_details IS 'Stores budget amounts by account and period';
COMMENT ON COLUMN accounting.budget_details.budget_id IS 'Reference to the parent budget';
COMMENT ON COLUMN accounting.budget_details.account_id IS 'Account this budget line applies to';
COMMENT ON COLUMN accounting.budget_details.fiscal_period_id IS 'Fiscal period this budget line applies to';
COMMENT ON COLUMN accounting.budget_details.amount IS 'Budgeted amount for the account and period';
COMMENT ON COLUMN accounting.budget_details.dimension1_id IS 'Optional first dimension for the budget line';
COMMENT ON COLUMN accounting.budget_details.dimension2_id IS 'Optional second dimension for the budget line';
COMMENT ON COLUMN accounting.budget_details.notes IS 'Additional notes for the budget line';


-- ============================================================================
-- BUSINESS SCHEMA TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Customers Table
-- ----------------------------------------------------------------------------
CREATE TABLE business.customers (
    id SERIAL PRIMARY KEY,
    customer_code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    legal_name VARCHAR(200),
    uen_no VARCHAR(20),
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
    credit_terms INTEGER DEFAULT 30,
    credit_limit NUMERIC(15,2),
    currency_code CHAR(3) DEFAULT 'SGD' REFERENCES accounting.currencies(code),
    is_active BOOLEAN DEFAULT TRUE,
    customer_since DATE,
    notes TEXT,
    receivables_account_id INTEGER REFERENCES accounting.accounts(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);

COMMENT ON TABLE business.customers IS 'Stores customer/client information';
COMMENT ON COLUMN business.customers.customer_code IS 'Unique identifier code for the customer';
COMMENT ON COLUMN business.customers.name IS 'Display name of the customer';
COMMENT ON COLUMN business.customers.legal_name IS 'Legal registered name of the customer';
COMMENT ON COLUMN business.customers.uen_no IS 'Unique Entity Number (Singapore business identifier)';
COMMENT ON COLUMN business.customers.gst_registered IS 'Whether the customer is GST registered';
COMMENT ON COLUMN business.customers.gst_no IS 'Customer''s GST registration number';
COMMENT ON COLUMN business.customers.credit_terms IS 'Payment terms in days';
COMMENT ON COLUMN business.customers.credit_limit IS 'Maximum credit allowed for this customer';
COMMENT ON COLUMN business.customers.currency_code IS 'Default currency for this customer';
COMMENT ON COLUMN business.customers.receivables_account_id IS 'Specific A/R account for this customer';

CREATE INDEX idx_customers_name ON business.customers(name);
CREATE INDEX idx_customers_is_active ON business.customers(is_active);

-- ----------------------------------------------------------------------------
-- Vendors Table
-- ----------------------------------------------------------------------------
CREATE TABLE business.vendors (
    id SERIAL PRIMARY KEY,
    vendor_code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    legal_name VARCHAR(200),
    uen_no VARCHAR(20),
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
    payment_terms INTEGER DEFAULT 30,
    currency_code CHAR(3) DEFAULT 'SGD' REFERENCES accounting.currencies(code),
    is_active BOOLEAN DEFAULT TRUE,
    vendor_since DATE,
    notes TEXT,
    bank_account_name VARCHAR(100),
    bank_account_number VARCHAR(50),
    bank_name VARCHAR(100),
    bank_branch VARCHAR(100),
    bank_swift_code VARCHAR(20),
    payables_account_id INTEGER REFERENCES accounting.accounts(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);

COMMENT ON TABLE business.vendors IS 'Stores vendor/supplier information';
COMMENT ON COLUMN business.vendors.vendor_code IS 'Unique identifier code for the vendor';
COMMENT ON COLUMN business.vendors.name IS 'Display name of the vendor';
COMMENT ON COLUMN business.vendors.legal_name IS 'Legal registered name of the vendor';
COMMENT ON COLUMN business.vendors.uen_no IS 'Unique Entity Number (Singapore business identifier)';
COMMENT ON COLUMN business.vendors.gst_registered IS 'Whether the vendor is GST registered';
COMMENT ON COLUMN business.vendors.gst_no IS 'Vendor''s GST registration number';
COMMENT ON COLUMN business.vendors.withholding_tax_applicable IS 'Whether withholding tax applies to this vendor';
COMMENT ON COLUMN business.vendors.withholding_tax_rate IS 'Withholding tax rate percentage';
COMMENT ON COLUMN business.vendors.payment_terms IS 'Payment terms in days';
COMMENT ON COLUMN business.vendors.bank_account_number IS 'Vendor''s bank account number for payments';
COMMENT ON COLUMN business.vendors.payables_account_id IS 'Specific A/P account for this vendor';

CREATE INDEX idx_vendors_name ON business.vendors(name);
CREATE INDEX idx_vendors_is_active ON business.vendors(is_active);

-- ----------------------------------------------------------------------------
-- Products Table
-- ----------------------------------------------------------------------------
CREATE TABLE business.products (
    id SERIAL PRIMARY KEY,
    product_code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    product_type VARCHAR(20) NOT NULL CHECK (product_type IN ('Inventory', 'Service', 'Non-Inventory')),
    category VARCHAR(50),
    unit_of_measure VARCHAR(20),
    barcode VARCHAR(50),
    sales_price NUMERIC(15,2),
    purchase_price NUMERIC(15,2),
    sales_account_id INTEGER REFERENCES accounting.accounts(id),
    purchase_account_id INTEGER REFERENCES accounting.accounts(id),
    inventory_account_id INTEGER REFERENCES accounting.accounts(id),
    tax_code VARCHAR(20), 
    is_active BOOLEAN DEFAULT TRUE,
    min_stock_level NUMERIC(15,2),
    reorder_point NUMERIC(15,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);

COMMENT ON TABLE business.products IS 'Stores product/service information';
COMMENT ON COLUMN business.products.product_code IS 'Unique identifier code for the product';
COMMENT ON COLUMN business.products.name IS 'Name of the product or service';
COMMENT ON COLUMN business.products.product_type IS 'Type of product (Inventory, Service, Non-Inventory)';
COMMENT ON COLUMN business.products.unit_of_measure IS 'Unit of measure (e.g., Each, Hour, Kg)';
COMMENT ON COLUMN business.products.barcode IS 'Barcode or SKU for the product';
COMMENT ON COLUMN business.products.sales_price IS 'Default selling price';
COMMENT ON COLUMN business.products.purchase_price IS 'Default purchase price';
COMMENT ON COLUMN business.products.sales_account_id IS 'Revenue account for sales of this product';
COMMENT ON COLUMN business.products.purchase_account_id IS 'Expense account for purchases of this product';
COMMENT ON COLUMN business.products.inventory_account_id IS 'Inventory asset account for this product';
COMMENT ON COLUMN business.products.tax_code IS 'Default tax code for this product';
COMMENT ON COLUMN business.products.min_stock_level IS 'Minimum stock level for inventory warnings';
COMMENT ON COLUMN business.products.reorder_point IS 'Stock level at which to reorder';

CREATE INDEX idx_products_name ON business.products(name);
CREATE INDEX idx_products_is_active ON business.products(is_active);
CREATE INDEX idx_products_type ON business.products(product_type);

-- ----------------------------------------------------------------------------
-- Inventory Movements Table
-- ----------------------------------------------------------------------------
CREATE TABLE business.inventory_movements (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES business.products(id),
    movement_date DATE NOT NULL,
    movement_type VARCHAR(20) NOT NULL CHECK (movement_type IN (
        'Purchase', 'Sale', 'Adjustment', 'Transfer', 'Return', 'Opening'
    )),
    quantity NUMERIC(15,2) NOT NULL,
    unit_cost NUMERIC(15,4),
    total_cost NUMERIC(15,2),
    reference_type VARCHAR(50),
    reference_id INTEGER,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id)
);

COMMENT ON TABLE business.inventory_movements IS 'Tracks inventory quantities and costs';
COMMENT ON COLUMN business.inventory_movements.product_id IS 'Product being tracked';
COMMENT ON COLUMN business.inventory_movements.movement_date IS 'Date of the inventory movement';
COMMENT ON COLUMN business.inventory_movements.movement_type IS 'Type of movement (Purchase, Sale, etc.)';
COMMENT ON COLUMN business.inventory_movements.quantity IS 'Quantity moved (positive for in, negative for out)';
COMMENT ON COLUMN business.inventory_movements.unit_cost IS 'Cost per unit';
COMMENT ON COLUMN business.inventory_movements.total_cost IS 'Total cost of the movement';
COMMENT ON COLUMN business.inventory_movements.reference_type IS 'Type of source document';
COMMENT ON COLUMN business.inventory_movements.reference_id IS 'ID of the source document';

CREATE INDEX idx_inventory_movements_product ON business.inventory_movements(product_id, movement_date);
CREATE INDEX idx_inventory_movements_reference ON business.inventory_movements(reference_type, reference_id);

-- ----------------------------------------------------------------------------
-- Sales Invoices Table
-- ----------------------------------------------------------------------------
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

COMMENT ON TABLE business.sales_invoices IS 'Stores sales invoice header information';
COMMENT ON COLUMN business.sales_invoices.invoice_no IS 'Unique invoice number';
COMMENT ON COLUMN business.sales_invoices.customer_id IS 'Customer being invoiced';
COMMENT ON COLUMN business.sales_invoices.invoice_date IS 'Date of the invoice';
COMMENT ON COLUMN business.sales_invoices.due_date IS 'Payment due date';
COMMENT ON COLUMN business.sales_invoices.currency_code IS 'Currency of the invoice';
COMMENT ON COLUMN business.sales_invoices.exchange_rate IS 'Exchange rate to base currency';
COMMENT ON COLUMN business.sales_invoices.subtotal IS 'Invoice subtotal before tax';
COMMENT ON COLUMN business.sales_invoices.tax_amount IS 'Total tax amount';
COMMENT ON COLUMN business.sales_invoices.total_amount IS 'Total invoice amount including tax';
COMMENT ON COLUMN business.sales_invoices.amount_paid IS 'Amount paid to date';
COMMENT ON COLUMN business.sales_invoices.status IS 'Current status of the invoice';
COMMENT ON COLUMN business.sales_invoices.journal_entry_id IS 'Associated journal entry';

CREATE INDEX idx_sales_invoices_customer ON business.sales_invoices(customer_id);
CREATE INDEX idx_sales_invoices_dates ON business.sales_invoices(invoice_date, due_date);
CREATE INDEX idx_sales_invoices_status ON business.sales_invoices(status);

-- ----------------------------------------------------------------------------
-- Sales Invoice Lines Table
-- ----------------------------------------------------------------------------
CREATE TABLE business.sales_invoice_lines (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES business.sales_invoices(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    product_id INTEGER REFERENCES business.products(id),
    description VARCHAR(200) NOT NULL,
    quantity NUMERIC(15,2) NOT NULL,
    unit_price NUMERIC(15,2) NOT NULL,
    discount_percent NUMERIC(5,2) DEFAULT 0,
    discount_amount NUMERIC(15,2) DEFAULT 0,
    line_subtotal NUMERIC(15,2) NOT NULL,
    tax_code VARCHAR(20), 
    tax_amount NUMERIC(15,2) DEFAULT 0,
    line_total NUMERIC(15,2) NOT NULL,
    dimension1_id INTEGER REFERENCES accounting.dimensions(id),
    dimension2_id INTEGER REFERENCES accounting.dimensions(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE business.sales_invoice_lines IS 'Stores sales invoice line item details';
COMMENT ON COLUMN business.sales_invoice_lines.invoice_id IS 'Reference to parent invoice';
COMMENT ON COLUMN business.sales_invoice_lines.line_number IS 'Line sequence number';
COMMENT ON COLUMN business.sales_invoice_lines.product_id IS 'Product or service being invoiced';
COMMENT ON COLUMN business.sales_invoice_lines.description IS 'Line item description';
COMMENT ON COLUMN business.sales_invoice_lines.quantity IS 'Quantity sold';
COMMENT ON COLUMN business.sales_invoice_lines.unit_price IS 'Price per unit';
COMMENT ON COLUMN business.sales_invoice_lines.discount_percent IS 'Discount percentage';
COMMENT ON COLUMN business.sales_invoice_lines.discount_amount IS 'Discount amount';
COMMENT ON COLUMN business.sales_invoice_lines.line_subtotal IS 'Line subtotal (quantity * unit_price - discount)';
COMMENT ON COLUMN business.sales_invoice_lines.tax_code IS 'Tax code applied to this line';
COMMENT ON COLUMN business.sales_invoice_lines.tax_amount IS 'Tax amount for this line';
COMMENT ON COLUMN business.sales_invoice_lines.line_total IS 'Line total including tax';
COMMENT ON COLUMN business.sales_invoice_lines.dimension1_id IS 'Analytical dimension 1';
COMMENT ON COLUMN business.sales_invoice_lines.dimension2_id IS 'Analytical dimension 2';

CREATE INDEX idx_sales_invoice_lines_invoice ON business.sales_invoice_lines(invoice_id);
CREATE INDEX idx_sales_invoice_lines_product ON business.sales_invoice_lines(product_id);

-- ----------------------------------------------------------------------------
-- Purchase Invoices Table
-- ----------------------------------------------------------------------------
CREATE TABLE business.purchase_invoices (
    id SERIAL PRIMARY KEY,
    invoice_no VARCHAR(20) NOT NULL UNIQUE,
    vendor_id INTEGER NOT NULL REFERENCES business.vendors(id),
    vendor_invoice_no VARCHAR(50),
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    currency_code CHAR(3) NOT NULL REFERENCES accounting.currencies(code),
    exchange_rate NUMERIC(15,6) DEFAULT 1,
    subtotal NUMERIC(15,2) NOT NULL,
    tax_amount NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_amount NUMERIC(15,2) NOT NULL,
    amount_paid NUMERIC(15,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN (
        'Draft', 'Approved', 'Partially Paid', 'Paid', 'Overdue', 'Disputed', 'Voided'
    )),
    notes TEXT,
    journal_entry_id INTEGER REFERENCES accounting.journal_entries(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);

COMMENT ON TABLE business.purchase_invoices IS 'Stores purchase invoice header information';
COMMENT ON COLUMN business.purchase_invoices.invoice_no IS 'Internal invoice reference number';
COMMENT ON COLUMN business.purchase_invoices.vendor_id IS 'Vendor who issued the invoice';
COMMENT ON COLUMN business.purchase_invoices.vendor_invoice_no IS 'Vendor''s invoice number';
COMMENT ON COLUMN business.purchase_invoices.invoice_date IS 'Date of the invoice';
COMMENT ON COLUMN business.purchase_invoices.due_date IS 'Payment due date';
COMMENT ON COLUMN business.purchase_invoices.currency_code IS 'Currency of the invoice';
COMMENT ON COLUMN business.purchase_invoices.exchange_rate IS 'Exchange rate to base currency';
COMMENT ON COLUMN business.purchase_invoices.subtotal IS 'Invoice subtotal before tax';
COMMENT ON COLUMN business.purchase_invoices.tax_amount IS 'Total tax amount';
COMMENT ON COLUMN business.purchase_invoices.total_amount IS 'Total invoice amount including tax';
COMMENT ON COLUMN business.purchase_invoices.amount_paid IS 'Amount paid to date';
COMMENT ON COLUMN business.purchase_invoices.status IS 'Current status of the invoice';
COMMENT ON COLUMN business.purchase_invoices.journal_entry_id IS 'Associated journal entry';

CREATE INDEX idx_purchase_invoices_vendor ON business.purchase_invoices(vendor_id);
CREATE INDEX idx_purchase_invoices_dates ON business.purchase_invoices(invoice_date, due_date);
CREATE INDEX idx_purchase_invoices_status ON business.purchase_invoices(status);

-- ----------------------------------------------------------------------------
-- Purchase Invoice Lines Table
-- ----------------------------------------------------------------------------
CREATE TABLE business.purchase_invoice_lines (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES business.purchase_invoices(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    product_id INTEGER REFERENCES business.products(id),
    description VARCHAR(200) NOT NULL,
    quantity NUMERIC(15,2) NOT NULL,
    unit_price NUMERIC(15,2) NOT NULL,
    discount_percent NUMERIC(5,2) DEFAULT 0,
    discount_amount NUMERIC(15,2) DEFAULT 0,
    line_subtotal NUMERIC(15,2) NOT NULL,
    tax_code VARCHAR(20), 
    tax_amount NUMERIC(15,2) DEFAULT 0,
    line_total NUMERIC(15,2) NOT NULL,
    dimension1_id INTEGER REFERENCES accounting.dimensions(id),
    dimension2_id INTEGER REFERENCES accounting.dimensions(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE business.purchase_invoice_lines IS 'Stores purchase invoice line item details';
COMMENT ON COLUMN business.purchase_invoice_lines.invoice_id IS 'Reference to parent invoice';
COMMENT ON COLUMN business.purchase_invoice_lines.line_number IS 'Line sequence number';
COMMENT ON COLUMN business.purchase_invoice_lines.product_id IS 'Product or service being purchased';
COMMENT ON COLUMN business.purchase_invoice_lines.description IS 'Line item description';
COMMENT ON COLUMN business.purchase_invoice_lines.quantity IS 'Quantity purchased';
COMMENT ON COLUMN business.purchase_invoice_lines.unit_price IS 'Price per unit';
COMMENT ON COLUMN business.purchase_invoice_lines.discount_percent IS 'Discount percentage';
COMMENT ON COLUMN business.purchase_invoice_lines.discount_amount IS 'Discount amount';
COMMENT ON COLUMN business.purchase_invoice_lines.line_subtotal IS 'Line subtotal (quantity * unit_price - discount)';
COMMENT ON COLUMN business.purchase_invoice_lines.tax_code IS 'Tax code applied to this line';
COMMENT ON COLUMN business.purchase_invoice_lines.tax_amount IS 'Tax amount for this line';
COMMENT ON COLUMN business.purchase_invoice_lines.line_total IS 'Line total including tax';
COMMENT ON COLUMN business.purchase_invoice_lines.dimension1_id IS 'Analytical dimension 1';
COMMENT ON COLUMN business.purchase_invoice_lines.dimension2_id IS 'Analytical dimension 2';

CREATE INDEX idx_purchase_invoice_lines_invoice ON business.purchase_invoice_lines(invoice_id);
CREATE INDEX idx_purchase_invoice_lines_product ON business.purchase_invoice_lines(product_id);

-- ----------------------------------------------------------------------------
-- Bank Accounts Table
-- ----------------------------------------------------------------------------
CREATE TABLE business.bank_accounts (
    id SERIAL PRIMARY KEY,
    account_name VARCHAR(100) NOT NULL,
    account_number VARCHAR(50) NOT NULL,
    bank_name VARCHAR(100) NOT NULL,
    bank_branch VARCHAR(100),
    bank_swift_code VARCHAR(20),
    currency_code CHAR(3) NOT NULL REFERENCES accounting.currencies(code),
    opening_balance NUMERIC(15,2) DEFAULT 0,
    current_balance NUMERIC(15,2) DEFAULT 0,
    last_reconciled_date DATE,
    gl_account_id INTEGER NOT NULL REFERENCES accounting.accounts(id),
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);

COMMENT ON TABLE business.bank_accounts IS 'Stores bank account information';
COMMENT ON COLUMN business.bank_accounts.account_name IS 'Name of the bank account';
COMMENT ON COLUMN business.bank_accounts.account_number IS 'Bank account number';
COMMENT ON COLUMN business.bank_accounts.bank_name IS 'Name of the bank';
COMMENT ON COLUMN business.bank_accounts.bank_branch IS 'Branch of the bank';
COMMENT ON COLUMN business.bank_accounts.bank_swift_code IS 'SWIFT code for international transfers';
COMMENT ON COLUMN business.bank_accounts.currency_code IS 'Currency of the account';
COMMENT ON COLUMN business.bank_accounts.opening_balance IS 'Initial balance when account was created';
COMMENT ON COLUMN business.bank_accounts.current_balance IS 'Current balance in the account (calculated or denormalized)';
COMMENT ON COLUMN business.bank_accounts.last_reconciled_date IS 'Date of last bank reconciliation';
COMMENT ON COLUMN business.bank_accounts.gl_account_id IS 'Associated GL account in the chart of accounts';

-- ----------------------------------------------------------------------------
-- Bank Transactions Table
-- ----------------------------------------------------------------------------
CREATE TABLE business.bank_transactions (
    id SERIAL PRIMARY KEY,
    bank_account_id INTEGER NOT NULL REFERENCES business.bank_accounts(id),
    transaction_date DATE NOT NULL,
    value_date DATE,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN (
        'Deposit', 'Withdrawal', 'Transfer', 'Interest', 'Fee', 'Adjustment'
    )),
    description VARCHAR(200) NOT NULL,
    reference VARCHAR(100),
    amount NUMERIC(15,2) NOT NULL,
    is_reconciled BOOLEAN DEFAULT FALSE,
    reconciled_date DATE,
    statement_date DATE,
    statement_id VARCHAR(50),
    journal_entry_id INTEGER REFERENCES accounting.journal_entries(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);

COMMENT ON TABLE business.bank_transactions IS 'Stores bank account transactions';
COMMENT ON COLUMN business.bank_transactions.bank_account_id IS 'Bank account for this transaction';
COMMENT ON COLUMN business.bank_transactions.transaction_date IS 'Date of the transaction';
COMMENT ON COLUMN business.bank_transactions.value_date IS 'Value date for the transaction';
COMMENT ON COLUMN business.bank_transactions.transaction_type IS 'Type of transaction';
COMMENT ON COLUMN business.bank_transactions.description IS 'Description of the transaction';
COMMENT ON COLUMN business.bank_transactions.reference IS 'Reference number or code';
COMMENT ON COLUMN business.bank_transactions.amount IS 'Amount of the transaction (positive for deposits, negative for withdrawals)';
COMMENT ON COLUMN business.bank_transactions.is_reconciled IS 'Whether this transaction has been reconciled';
COMMENT ON COLUMN business.bank_transactions.reconciled_date IS 'Date when the transaction was reconciled';
COMMENT ON COLUMN business.bank_transactions.statement_date IS 'Bank statement date';
COMMENT ON COLUMN business.bank_transactions.statement_id IS 'Bank statement reference';
COMMENT ON COLUMN business.bank_transactions.journal_entry_id IS 'Associated journal entry';

CREATE INDEX idx_bank_transactions_account ON business.bank_transactions(bank_account_id);
CREATE INDEX idx_bank_transactions_date ON business.bank_transactions(transaction_date);
CREATE INDEX idx_bank_transactions_reconciled ON business.bank_transactions(is_reconciled);

-- ----------------------------------------------------------------------------
-- Payments Table
-- ----------------------------------------------------------------------------
CREATE TABLE business.payments (
    id SERIAL PRIMARY KEY,
    payment_no VARCHAR(20) NOT NULL UNIQUE,
    payment_type VARCHAR(20) NOT NULL CHECK (payment_type IN (
        'Customer Payment', 'Vendor Payment', 'Refund', 'Credit Note', 'Other'
    )),
    payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN (
        'Cash', 'Check', 'Bank Transfer', 'Credit Card', 'GIRO', 'PayNow', 'Other'
    )),
    payment_date DATE NOT NULL,
    entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('Customer', 'Vendor', 'Other')),
    entity_id INTEGER NOT NULL,
    bank_account_id INTEGER REFERENCES business.bank_accounts(id),
    currency_code CHAR(3) NOT NULL REFERENCES accounting.currencies(code),
    exchange_rate NUMERIC(15,6) DEFAULT 1,
    amount NUMERIC(15,2) NOT NULL,
    reference VARCHAR(100),
    description TEXT,
    cheque_no VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN (
        'Draft', 'Approved', 'Completed', 'Voided', 'Returned'
    )),
    journal_entry_id INTEGER REFERENCES accounting.journal_entries(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);

COMMENT ON TABLE business.payments IS 'Stores payment transactions (both received and made)';
COMMENT ON COLUMN business.payments.payment_no IS 'Unique payment reference number';
COMMENT ON COLUMN business.payments.payment_type IS 'Type of payment transaction';
COMMENT ON COLUMN business.payments.payment_method IS 'Method of payment';
COMMENT ON COLUMN business.payments.payment_date IS 'Date of the payment';
COMMENT ON COLUMN business.payments.entity_type IS 'Type of entity (Customer, Vendor)';
COMMENT ON COLUMN business.payments.entity_id IS 'ID of the customer or vendor';
COMMENT ON COLUMN business.payments.bank_account_id IS 'Bank account used for the payment';
COMMENT ON COLUMN business.payments.currency_code IS 'Currency of the payment';
COMMENT ON COLUMN business.payments.exchange_rate IS 'Exchange rate to base currency';
COMMENT ON COLUMN business.payments.amount IS 'Payment amount';
COMMENT ON COLUMN business.payments.reference IS 'External reference number';
COMMENT ON COLUMN business.payments.cheque_no IS 'Check number if applicable';
COMMENT ON COLUMN business.payments.status IS 'Current status of the payment';
COMMENT ON COLUMN business.payments.journal_entry_id IS 'Associated journal entry';

CREATE INDEX idx_payments_date ON business.payments(payment_date);
CREATE INDEX idx_payments_entity ON business.payments(entity_type, entity_id);
CREATE INDEX idx_payments_status ON business.payments(status);

-- ----------------------------------------------------------------------------
-- Payment Allocations Table
-- ----------------------------------------------------------------------------
CREATE TABLE business.payment_allocations (
    id SERIAL PRIMARY KEY,
    payment_id INTEGER NOT NULL REFERENCES business.payments(id) ON DELETE CASCADE,
    document_type VARCHAR(20) NOT NULL CHECK (document_type IN (
        'Sales Invoice', 'Purchase Invoice', 'Credit Note', 'Debit Note', 'Other'
    )),
    document_id INTEGER NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id)
);

COMMENT ON TABLE business.payment_allocations IS 'Maps payments to invoices for payment allocation';
COMMENT ON COLUMN business.payment_allocations.payment_id IS 'Payment being allocated';
COMMENT ON COLUMN business.payment_allocations.document_type IS 'Type of document being paid';
COMMENT ON COLUMN business.payment_allocations.document_id IS 'ID of the document being paid';
COMMENT ON COLUMN business.payment_allocations.amount IS 'Amount allocated to this document';

CREATE INDEX idx_payment_allocations_payment ON business.payment_allocations(payment_id);
CREATE INDEX idx_payment_allocations_document ON business.payment_allocations(document_type, document_id);

-- ============================================================================
-- TAX SCHEMA TABLES (Part of Accounting Schema in Reference)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Tax Codes Table
-- ----------------------------------------------------------------------------
CREATE TABLE accounting.tax_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    description VARCHAR(100) NOT NULL,
    tax_type VARCHAR(20) NOT NULL CHECK (tax_type IN ('GST', 'Income Tax', 'Withholding Tax')),
    rate NUMERIC(5,2) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    affects_account_id INTEGER REFERENCES accounting.accounts(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);

COMMENT ON TABLE accounting.tax_codes IS 'Defines tax codes and rates for transaction tax calculation';
COMMENT ON COLUMN accounting.tax_codes.code IS 'Unique code for the tax (e.g., SR, ZR, ES)';
COMMENT ON COLUMN accounting.tax_codes.description IS 'Description of the tax code';
COMMENT ON COLUMN accounting.tax_codes.tax_type IS 'Type of tax (GST, Income Tax, Withholding Tax)';
COMMENT ON COLUMN accounting.tax_codes.rate IS 'Tax rate percentage';
COMMENT ON COLUMN accounting.tax_codes.is_default IS 'Whether this is the default code for its tax type';
COMMENT ON COLUMN accounting.tax_codes.affects_account_id IS 'GL account affected by this tax';

-- ----------------------------------------------------------------------------
-- GST Returns Table
-- ----------------------------------------------------------------------------
CREATE TABLE accounting.gst_returns (
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
    tax_adjustments NUMERIC(15,2) DEFAULT 0,
    tax_payable NUMERIC(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Submitted', 'Amended')),
    submission_date DATE,
    submission_reference VARCHAR(50),
    journal_entry_id INTEGER REFERENCES accounting.journal_entries(id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);

COMMENT ON TABLE accounting.gst_returns IS 'Stores GST return information for filing with IRAS';
COMMENT ON COLUMN accounting.gst_returns.return_period IS 'Period identifier (e.g., Jan-Mar 2023)';
COMMENT ON COLUMN accounting.gst_returns.start_date IS 'Start date of the GST period';
COMMENT ON COLUMN accounting.gst_returns.end_date IS 'End date of the GST period';
COMMENT ON COLUMN accounting.gst_returns.filing_due_date IS 'Due date for filing the return';
COMMENT ON COLUMN accounting.gst_returns.standard_rated_supplies IS 'Box 1: Total value of standard-rated supplies';
COMMENT ON COLUMN accounting.gst_returns.zero_rated_supplies IS 'Box 2: Total value of zero-rated supplies';
COMMENT ON COLUMN accounting.gst_returns.exempt_supplies IS 'Box 3: Total value of exempt supplies';
COMMENT ON COLUMN accounting.gst_returns.total_supplies IS 'Box 4: Total value of (1) + (2) + (3)';
COMMENT ON COLUMN accounting.gst_returns.taxable_purchases IS 'Box 5: Total value of taxable purchases';
COMMENT ON COLUMN accounting.gst_returns.output_tax IS 'Box 6: Output tax due';
COMMENT ON COLUMN accounting.gst_returns.input_tax IS 'Box 7: Input tax and refunds claimed';
COMMENT ON COLUMN accounting.gst_returns.tax_adjustments IS 'Box 8: Tax adjustments';
COMMENT ON COLUMN accounting.gst_returns.tax_payable IS 'Box 9: Tax payable or refundable';
COMMENT ON COLUMN accounting.gst_returns.status IS 'Current status of the return';
COMMENT ON COLUMN accounting.gst_returns.submission_date IS 'Date when the return was submitted';
COMMENT ON COLUMN accounting.gst_returns.submission_reference IS 'Reference number from IRAS';
COMMENT ON COLUMN accounting.gst_returns.journal_entry_id IS 'Associated journal entry for GST payment/refund';

-- ----------------------------------------------------------------------------
-- Withholding Tax Certificates Table
-- ----------------------------------------------------------------------------
CREATE TABLE accounting.withholding_tax_certificates (
    id SERIAL PRIMARY KEY,
    certificate_no VARCHAR(20) NOT NULL UNIQUE,
    vendor_id INTEGER NOT NULL REFERENCES business.vendors(id),
    tax_type VARCHAR(50) NOT NULL,
    tax_rate NUMERIC(5,2) NOT NULL,
    payment_date DATE NOT NULL,
    amount_before_tax NUMERIC(15,2) NOT NULL,
    tax_amount NUMERIC(15,2) NOT NULL,
    payment_reference VARCHAR(50),
    status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Issued', 'Voided')),
    issue_date DATE,
    journal_entry_id INTEGER REFERENCES accounting.journal_entries(id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);

COMMENT ON TABLE accounting.withholding_tax_certificates IS 'Stores withholding tax certificate information';
COMMENT ON COLUMN accounting.withholding_tax_certificates.certificate_no IS 'Unique certificate number';
COMMENT ON COLUMN accounting.withholding_tax_certificates.vendor_id IS 'Vendor to whom the certificate is issued';
COMMENT ON COLUMN accounting.withholding_tax_certificates.tax_type IS 'Type of withholding tax';
COMMENT ON COLUMN accounting.withholding_tax_certificates.tax_rate IS 'Rate of withholding tax applied';
COMMENT ON COLUMN accounting.withholding_tax_certificates.payment_date IS 'Date of the original payment';
COMMENT ON COLUMN accounting.withholding_tax_certificates.amount_before_tax IS 'Payment amount before tax';
COMMENT ON COLUMN accounting.withholding_tax_certificates.tax_amount IS 'Amount of tax withheld';
COMMENT ON COLUMN accounting.withholding_tax_certificates.payment_reference IS 'Reference to the original payment';
COMMENT ON COLUMN accounting.withholding_tax_certificates.status IS 'Current status of the certificate';
COMMENT ON COLUMN accounting.withholding_tax_certificates.issue_date IS 'Date when the certificate was issued';
COMMENT ON COLUMN accounting.withholding_tax_certificates.journal_entry_id IS 'Associated journal entry';

-- ============================================================================
-- AUDIT SCHEMA TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Audit Log Table
-- ----------------------------------------------------------------------------
CREATE TABLE audit.audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES core.users(id),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    entity_name VARCHAR(200),
    changes JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE audit.audit_log IS 'Records system activity for auditing purposes';
COMMENT ON COLUMN audit.audit_log.user_id IS 'User who performed the action';
COMMENT ON COLUMN audit.audit_log.action IS 'Action performed (Create, Update, Delete, etc.)';
COMMENT ON COLUMN audit.audit_log.entity_type IS 'Type of entity affected (Account, Invoice, etc.)';
COMMENT ON COLUMN audit.audit_log.entity_id IS 'ID of the affected entity';
COMMENT ON COLUMN audit.audit_log.entity_name IS 'Name or description of the affected entity';
COMMENT ON COLUMN audit.audit_log.changes IS 'JSON representation of changes made';
COMMENT ON COLUMN audit.audit_log.ip_address IS 'IP address of the user';
COMMENT ON COLUMN audit.audit_log.user_agent IS 'User agent string of the client';
COMMENT ON COLUMN audit.audit_log.timestamp IS 'When the action occurred';

CREATE INDEX idx_audit_log_user ON audit.audit_log(user_id);
CREATE INDEX idx_audit_log_entity ON audit.audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_timestamp ON audit.audit_log(timestamp);

-- ----------------------------------------------------------------------------
-- Data Change History Table
-- ----------------------------------------------------------------------------
CREATE TABLE audit.data_change_history (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_type VARCHAR(20) NOT NULL CHECK (change_type IN ('Insert', 'Update', 'Delete')),
    changed_by INTEGER REFERENCES core.users(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE audit.data_change_history IS 'Tracks detailed changes to important data fields';
COMMENT ON COLUMN audit.data_change_history.table_name IS 'Name of the table that was changed';
COMMENT ON COLUMN audit.data_change_history.record_id IS 'Primary key of the changed record';
COMMENT ON COLUMN audit.data_change_history.field_name IS 'Name of the field that was changed';
COMMENT ON COLUMN audit.data_change_history.old_value IS 'Previous value of the field';
COMMENT ON COLUMN audit.data_change_history.new_value IS 'New value of the field';
COMMENT ON COLUMN audit.data_change_history.change_type IS 'Type of change (Insert, Update, Delete)';
COMMENT ON COLUMN audit.data_change_history.changed_by IS 'User who made the change';
COMMENT ON COLUMN audit.data_change_history.changed_at IS 'When the change occurred';

CREATE INDEX idx_data_change_history_table_record ON audit.data_change_history(table_name, record_id);
CREATE INDEX idx_data_change_history_changed_at ON audit.data_change_history(changed_at);


-- ============================================================================
-- VIEWS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Account Balances View
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW accounting.account_balances AS
SELECT 
    a.id AS account_id,
    a.code AS account_code,
    a.name AS account_name,
    a.account_type,
    a.parent_id,
    COALESCE(SUM(
        CASE 
            WHEN jel.debit_amount > 0 THEN jel.debit_amount
            ELSE -jel.credit_amount
        END
    ), 0) + a.opening_balance AS balance,
    COALESCE(SUM(
        CASE 
            WHEN jel.debit_amount > 0 THEN jel.debit_amount
            ELSE 0
        END
    ), 0) AS total_debits_activity,
    COALESCE(SUM(
        CASE 
            WHEN jel.credit_amount > 0 THEN jel.credit_amount
            ELSE 0
        END
    ), 0) AS total_credits_activity,
    MAX(je.entry_date) AS last_activity_date
FROM 
    accounting.accounts a
LEFT JOIN 
    accounting.journal_entry_lines jel ON a.id = jel.account_id
LEFT JOIN 
    accounting.journal_entries je ON jel.journal_entry_id = je.id AND je.is_posted = TRUE
GROUP BY 
    a.id, a.code, a.name, a.account_type, a.parent_id, a.opening_balance;

COMMENT ON VIEW accounting.account_balances IS 'Calculates current balance for each account based on posted journal entries and opening balance';

-- ----------------------------------------------------------------------------
-- Trial Balance View
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW accounting.trial_balance AS
SELECT 
    a.id AS account_id,
    a.code AS account_code,
    a.name AS account_name,
    a.account_type, 
    a.sub_type,
    CASE 
        WHEN a.account_type IN ('Asset', 'Expense') THEN 
            CASE WHEN ab.balance >= 0 THEN ab.balance ELSE 0 END
        ELSE 
            CASE WHEN ab.balance < 0 THEN -ab.balance ELSE 0 END
    END AS debit_balance,
    CASE 
        WHEN a.account_type IN ('Asset', 'Expense') THEN
            CASE WHEN ab.balance < 0 THEN -ab.balance ELSE 0 END
        ELSE 
            CASE WHEN ab.balance >= 0 THEN ab.balance ELSE 0 END
    END AS credit_balance
FROM 
    accounting.accounts a
JOIN 
    accounting.account_balances ab ON a.id = ab.account_id
WHERE 
    a.is_active = TRUE
    AND ab.balance != 0;

COMMENT ON VIEW accounting.trial_balance IS 'Generates trial balance data with correct debit/credit presentation';

-- ----------------------------------------------------------------------------
-- Customer Balances View
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW business.customer_balances AS
SELECT 
    c.id AS customer_id,
    c.customer_code,
    c.name AS customer_name,
    COALESCE(SUM(si.total_amount - si.amount_paid), 0) AS outstanding_balance,
    COALESCE(SUM(CASE WHEN si.due_date < CURRENT_DATE AND si.status NOT IN ('Paid', 'Voided') 
        THEN si.total_amount - si.amount_paid ELSE 0 END), 0) AS overdue_amount,
    COALESCE(SUM(CASE WHEN si.status = 'Draft' THEN si.total_amount ELSE 0 END), 0) AS draft_amount,
    COALESCE(MAX(si.due_date), NULL) AS latest_due_date
FROM 
    business.customers c
LEFT JOIN 
    business.sales_invoices si ON c.id = si.customer_id AND si.status NOT IN ('Paid', 'Voided')
GROUP BY 
    c.id, c.customer_code, c.name;

COMMENT ON VIEW business.customer_balances IS 'Calculates outstanding and overdue balances for customers';

-- ----------------------------------------------------------------------------
-- Vendor Balances View
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW business.vendor_balances AS
SELECT 
    v.id AS vendor_id,
    v.vendor_code,
    v.name AS vendor_name,
    COALESCE(SUM(pi.total_amount - pi.amount_paid), 0) AS outstanding_balance,
    COALESCE(SUM(CASE WHEN pi.due_date < CURRENT_DATE AND pi.status NOT IN ('Paid', 'Voided') 
        THEN pi.total_amount - pi.amount_paid ELSE 0 END), 0) AS overdue_amount,
    COALESCE(SUM(CASE WHEN pi.status = 'Draft' THEN pi.total_amount ELSE 0 END), 0) AS draft_amount,
    COALESCE(MAX(pi.due_date), NULL) AS latest_due_date
FROM 
    business.vendors v
LEFT JOIN 
    business.purchase_invoices pi ON v.id = pi.vendor_id AND pi.status NOT IN ('Paid', 'Voided')
GROUP BY 
    v.id, v.vendor_code, v.name;

COMMENT ON VIEW business.vendor_balances IS 'Calculates outstanding and overdue balances for vendors';

-- ----------------------------------------------------------------------------
-- Inventory Summary View
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW business.inventory_summary AS
SELECT 
    p.id AS product_id,
    p.product_code,
    p.name AS product_name,
    p.product_type,
    p.category,
    p.unit_of_measure,
    COALESCE(SUM(im.quantity), 0) AS current_quantity,
    CASE 
        WHEN COALESCE(SUM(im.quantity), 0) != 0 THEN 
            COALESCE(SUM(im.total_cost), 0) / SUM(im.quantity) 
        ELSE
            p.purchase_price 
    END AS average_cost,
    COALESCE(SUM(im.total_cost), 0) AS inventory_value,
    p.sales_price AS current_sales_price,
    p.min_stock_level,
    p.reorder_point,
    CASE 
        WHEN p.min_stock_level IS NOT NULL AND COALESCE(SUM(im.quantity), 0) <= p.min_stock_level THEN TRUE
        ELSE FALSE
    END AS below_minimum,
    CASE 
        WHEN p.reorder_point IS NOT NULL AND COALESCE(SUM(im.quantity), 0) <= p.reorder_point THEN TRUE
        ELSE FALSE
    END AS reorder_needed
FROM 
    business.products p
LEFT JOIN 
    business.inventory_movements im ON p.id = im.product_id
WHERE 
    p.product_type = 'Inventory' AND p.is_active = TRUE
GROUP BY 
    p.id, p.product_code, p.name, p.product_type, p.category, p.unit_of_measure, 
    p.purchase_price, p.sales_price, p.min_stock_level, p.reorder_point;

COMMENT ON VIEW business.inventory_summary IS 'Provides current inventory levels, values, and reorder indicators';

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Get Next Sequence Value Function
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION core.get_next_sequence_value(p_sequence_name VARCHAR)
RETURNS VARCHAR AS $$
DECLARE
    v_sequence RECORD;
    v_next_value INTEGER;
    v_result VARCHAR;
BEGIN
    SELECT * INTO v_sequence 
    FROM core.sequences 
    WHERE sequence_name = p_sequence_name
    FOR UPDATE;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Sequence % not found', p_sequence_name;
    END IF;
    
    v_next_value := v_sequence.next_value;
    
    UPDATE core.sequences
    SET next_value = next_value + increment_by,
        updated_at = CURRENT_TIMESTAMP
    WHERE sequence_name = p_sequence_name;
    
    v_result := v_sequence.format_template;
    v_result := REPLACE(v_result, '{PREFIX}', COALESCE(v_sequence.prefix, ''));
    v_result := REPLACE(v_result, '{VALUE}', LPAD(v_next_value::TEXT, 6, '0'));
    v_result := REPLACE(v_result, '{SUFFIX}', COALESCE(v_sequence.suffix, ''));
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION core.get_next_sequence_value(VARCHAR) IS 'Generates the next number in a sequence with proper formatting';

-- ----------------------------------------------------------------------------
-- Generate Journal Entry Function
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION accounting.generate_journal_entry(
    p_journal_type VARCHAR,
    p_entry_date DATE,
    p_description VARCHAR,
    p_reference VARCHAR,
    p_source_type VARCHAR,
    p_source_id INTEGER,
    p_lines JSONB, 
    p_user_id INTEGER
) RETURNS INTEGER AS $$ 
DECLARE
    v_fiscal_period_id INTEGER;
    v_entry_no VARCHAR;
    v_journal_id INTEGER;
    v_line JSONB;
    v_line_number INTEGER := 1;
    v_total_debits NUMERIC(15,2) := 0;
    v_total_credits NUMERIC(15,2) := 0;
BEGIN
    SELECT id INTO v_fiscal_period_id
    FROM accounting.fiscal_periods
    WHERE p_entry_date BETWEEN start_date AND end_date
    AND status = 'Open';
    
    IF v_fiscal_period_id IS NULL THEN
        RAISE EXCEPTION 'No open fiscal period found for date %', p_entry_date;
    END IF;
    
    v_entry_no := core.get_next_sequence_value('journal_entry');
    
    INSERT INTO accounting.journal_entries (
        entry_no, journal_type, entry_date, fiscal_period_id, description,
        reference, is_posted, source_type, source_id, created_by, updated_by
    ) VALUES (
        v_entry_no, p_journal_type, p_entry_date, v_fiscal_period_id, p_description,
        p_reference, FALSE, p_source_type, p_source_id, p_user_id, p_user_id
    )
    RETURNING id INTO v_journal_id;
    
    FOR v_line IN SELECT * FROM jsonb_array_elements(p_lines)
    LOOP
        INSERT INTO accounting.journal_entry_lines (
            journal_entry_id, line_number, account_id, description, debit_amount, credit_amount,
            currency_code, exchange_rate, tax_code, tax_amount, dimension1_id, dimension2_id
        ) VALUES (
            v_journal_id, v_line_number, (v_line->>'account_id')::INTEGER,
            v_line->>'description', COALESCE((v_line->>'debit_amount')::NUMERIC, 0),
            COALESCE((v_line->>'credit_amount')::NUMERIC, 0),
            COALESCE(v_line->>'currency_code', 'SGD'),
            COALESCE((v_line->>'exchange_rate')::NUMERIC, 1),
            v_line->>'tax_code', COALESCE((v_line->>'tax_amount')::NUMERIC, 0),
            NULLIF(TRIM(v_line->>'dimension1_id'), '')::INTEGER, 
            NULLIF(TRIM(v_line->>'dimension2_id'), '')::INTEGER
        );
        
        v_line_number := v_line_number + 1;
        v_total_debits := v_total_debits + COALESCE((v_line->>'debit_amount')::NUMERIC, 0);
        v_total_credits := v_total_credits + COALESCE((v_line->>'credit_amount')::NUMERIC, 0);
    END LOOP;
    
    IF round(v_total_debits, 2) != round(v_total_credits, 2) THEN
        RAISE EXCEPTION 'Journal entry is not balanced. Debits: %, Credits: %', 
            v_total_debits, v_total_credits;
    END IF;
    
    RETURN v_journal_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION accounting.generate_journal_entry(VARCHAR, DATE, VARCHAR, VARCHAR, VARCHAR, INTEGER, JSONB, INTEGER) IS 
'Creates a journal entry from source data with validation';

-- ----------------------------------------------------------------------------
-- Post Journal Entry Function
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION accounting.post_journal_entry(
    p_journal_id INTEGER,
    p_user_id INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
    v_fiscal_period_status VARCHAR;
    v_is_already_posted BOOLEAN;
BEGIN
    SELECT is_posted INTO v_is_already_posted
    FROM accounting.journal_entries
    WHERE id = p_journal_id;
    
    IF v_is_already_posted THEN
        RAISE EXCEPTION 'Journal entry % is already posted', p_journal_id;
    END IF;
    
    SELECT fp.status INTO v_fiscal_period_status
    FROM accounting.journal_entries je
    JOIN accounting.fiscal_periods fp ON je.fiscal_period_id = fp.id
    WHERE je.id = p_journal_id;
    
    IF v_fiscal_period_status != 'Open' THEN
        RAISE EXCEPTION 'Cannot post to a closed or archived fiscal period';
    END IF;
    
    UPDATE accounting.journal_entries
    SET is_posted = TRUE,
        updated_at = CURRENT_TIMESTAMP,
        updated_by = p_user_id
    WHERE id = p_journal_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION accounting.post_journal_entry(INTEGER, INTEGER) IS 
'Marks a journal entry as posted after validation';

-- ----------------------------------------------------------------------------
-- Calculate Account Balance Function
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION accounting.calculate_account_balance(
    p_account_id INTEGER,
    p_as_of_date DATE
) RETURNS NUMERIC AS $$
DECLARE
    v_balance NUMERIC(15,2) := 0;
    v_opening_balance NUMERIC(15,2);
    v_account_opening_balance_date DATE; 
BEGIN
    SELECT acc.opening_balance, acc.opening_balance_date
    INTO v_opening_balance, v_account_opening_balance_date
    FROM accounting.accounts acc
    WHERE acc.id = p_account_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Account with ID % not found', p_account_id;
    END IF;
    
    SELECT COALESCE(SUM(
        CASE 
            WHEN jel.debit_amount > 0 THEN jel.debit_amount
            ELSE -jel.credit_amount
        END
    ), 0)
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

COMMENT ON FUNCTION accounting.calculate_account_balance(INTEGER, DATE) IS 
'Calculates the mathematical balance (Debits - Credits + Opening Balance) of an account as of a specific date';

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Update Timestamp Trigger Function
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION core.update_timestamp_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION core.update_timestamp_trigger_func() IS 
'Automatically updates the updated_at timestamp when a record is modified';

-- ----------------------------------------------------------------------------
-- Audit Log Trigger Function
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION audit.log_data_change_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    v_old_data JSONB;
    v_new_data JSONB;
    v_change_type VARCHAR(20);
    v_user_id INTEGER;
    v_entity_id INTEGER;
    v_entity_name VARCHAR(200);
    temp_val TEXT; -- For entity_name construction
    column_name TEXT; 
BEGIN
    -- Try to get user_id from session variable
    BEGIN
        v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER;
    EXCEPTION WHEN OTHERS THEN
        v_user_id := NULL; 
    END;

    -- If session user_id is not set, try to get from record's audit columns
    IF v_user_id IS NULL THEN
        IF TG_OP = 'INSERT' THEN
            BEGIN 
                v_user_id := NEW.created_by; 
            EXCEPTION WHEN undefined_column THEN 
                -- If 'created_by' doesn't exist, check if this is 'core.users' table
                IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN
                    v_user_id := NEW.id; -- For user creation, user itself is the "creator" if no session user
                ELSE
                    v_user_id := NULL; 
                END IF;
            END;
        ELSIF TG_OP = 'UPDATE' THEN
            BEGIN 
                v_user_id := NEW.updated_by; 
            EXCEPTION WHEN undefined_column THEN 
                IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN
                     v_user_id := NEW.id; -- For user update, user itself is the "updater" if no session user
                ELSE
                    v_user_id := NULL;
                END IF;
            END;
        END IF;
    END IF;
    
    -- Do not log changes to audit tables themselves to prevent recursion
    IF TG_TABLE_SCHEMA = 'audit' AND TG_TABLE_NAME IN ('audit_log', 'data_change_history') THEN
        RETURN NULL; 
    END IF;

    IF TG_OP = 'INSERT' THEN
        v_change_type := 'Insert';
        v_old_data := NULL;
        v_new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN
        v_change_type := 'Update';
        v_old_data := to_jsonb(OLD);
        v_new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'DELETE' THEN
        v_change_type := 'Delete';
        v_old_data := to_jsonb(OLD);
        v_new_data := NULL;
    END IF;
    
    -- Determine entity_id safely
    BEGIN
        IF TG_OP = 'DELETE' THEN
            v_entity_id := OLD.id;
        ELSE
            v_entity_id := NEW.id;
        END IF;
    EXCEPTION WHEN undefined_column THEN
        v_entity_id := NULL; 
    END;

    -- Determine entity_name safely
    BEGIN
        IF TG_OP = 'DELETE' THEN
            temp_val := CASE 
                WHEN TG_TABLE_NAME IN ('accounts', 'customers', 'vendors', 'products', 'roles', 'account_types', 'dimensions', 'fiscal_years', 'budgets') THEN OLD.name
                WHEN TG_TABLE_NAME = 'journal_entries' THEN OLD.entry_no
                WHEN TG_TABLE_NAME = 'sales_invoices' THEN OLD.invoice_no
                WHEN TG_TABLE_NAME = 'purchase_invoices' THEN OLD.invoice_no
                WHEN TG_TABLE_NAME = 'payments' THEN OLD.payment_no
                WHEN TG_TABLE_NAME = 'users' THEN OLD.username
                WHEN TG_TABLE_NAME = 'tax_codes' THEN OLD.code
                WHEN TG_TABLE_NAME = 'gst_returns' THEN OLD.return_period
                ELSE OLD.id::TEXT
            END;
        ELSE -- INSERT or UPDATE
            temp_val := CASE 
                WHEN TG_TABLE_NAME IN ('accounts', 'customers', 'vendors', 'products', 'roles', 'account_types', 'dimensions', 'fiscal_years', 'budgets') THEN NEW.name
                WHEN TG_TABLE_NAME = 'journal_entries' THEN NEW.entry_no
                WHEN TG_TABLE_NAME = 'sales_invoices' THEN NEW.invoice_no
                WHEN TG_TABLE_NAME = 'purchase_invoices' THEN NEW.invoice_no
                WHEN TG_TABLE_NAME = 'payments' THEN NEW.payment_no
                WHEN TG_TABLE_NAME = 'users' THEN NEW.username
                WHEN TG_TABLE_NAME = 'tax_codes' THEN NEW.code
                WHEN TG_TABLE_NAME = 'gst_returns' THEN NEW.return_period
                ELSE NEW.id::TEXT
            END;
        END IF;
        v_entity_name := temp_val;
    EXCEPTION WHEN undefined_column THEN
        -- Fallback if specific named column (name, entry_no, etc.) doesn't exist for a listed table, or if OLD.id/NEW.id itself is problematic
        BEGIN 
            IF TG_OP = 'DELETE' THEN v_entity_name := OLD.id::TEXT; ELSE v_entity_name := NEW.id::TEXT; END IF;
        EXCEPTION WHEN undefined_column THEN 
            v_entity_name := NULL; 
        END;
    END;

    INSERT INTO audit.audit_log (
        user_id, action, entity_type, entity_id, entity_name, changes, timestamp
    ) VALUES (
        v_user_id,
        v_change_type,
        TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
        v_entity_id,
        v_entity_name,
        jsonb_build_object('old', v_old_data, 'new', v_new_data),
        CURRENT_TIMESTAMP
    );
    
    IF TG_OP = 'UPDATE' THEN
        FOR column_name IN 
            SELECT key 
            FROM jsonb_object_keys(v_old_data) 
        LOOP
            IF (v_new_data ? column_name) AND ((v_old_data -> column_name) IS DISTINCT FROM (v_new_data -> column_name)) THEN
                INSERT INTO audit.data_change_history (
                    table_name, record_id, field_name, old_value, new_value,
                    change_type, changed_by, changed_at
                ) VALUES (
                    TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
                    NEW.id, 
                    column_name,
                    v_old_data ->> column_name,
                    v_new_data ->> column_name,
                    'Update',
                    v_user_id,
                    CURRENT_TIMESTAMP
                );
            END IF;
        END LOOP;
    END IF;
    
    RETURN NULL; 
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION audit.log_data_change_trigger_func() IS 
'Records data changes to the audit log and data change history for tracking and compliance';

-- Create update_timestamp triggers for all tables with updated_at columns
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT table_schema, table_name
        FROM information_schema.columns
        WHERE column_name = 'updated_at'
          AND table_schema IN ('core', 'accounting', 'business', 'audit')
        GROUP BY table_schema, table_name
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS trg_update_timestamp ON %I.%I;
            CREATE TRIGGER trg_update_timestamp
            BEFORE UPDATE ON %I.%I
            FOR EACH ROW
            EXECUTE FUNCTION core.update_timestamp_trigger_func();
        ', r.table_schema, r.table_name, r.table_schema, r.table_name);
    END LOOP;
END;
$$;

-- Create audit_log triggers for important tables
DO $$
DECLARE
    tables_to_audit TEXT[] := ARRAY[
        'accounting.accounts',
        'accounting.journal_entries',
        'accounting.fiscal_periods',
        'accounting.fiscal_years',
        'business.customers',
        'business.vendors',
        'business.products',
        'business.sales_invoices',
        'business.purchase_invoices',
        'business.payments',
        'accounting.tax_codes',
        'accounting.gst_returns',
        'core.users', 
        'core.roles', 
        'core.company_settings'
    ];
    table_fullname TEXT;
    schema_name TEXT;
    table_name_var TEXT; 
BEGIN
    FOREACH table_fullname IN ARRAY tables_to_audit
    LOOP
        SELECT split_part(table_fullname, '.', 1) INTO schema_name;
        SELECT split_part(table_fullname, '.', 2) INTO table_name_var;
        
        EXECUTE format('
            DROP TRIGGER IF EXISTS trg_audit_log ON %I.%I;
            CREATE TRIGGER trg_audit_log
            AFTER INSERT OR UPDATE OR DELETE ON %I.%I
            FOR EACH ROW
            EXECUTE FUNCTION audit.log_data_change_trigger_func();
        ', schema_name, table_name_var, schema_name, table_name_var);
    END LOOP;
END;
$$;

-- End of script
```

---
https://drive.google.com/file/d/1EwsvcutY25rEKdDxZN2imU3hrOwGNVYL/view?usp=sharing, https://drive.google.com/file/d/1Nhrj6yvXO3YuJWobJ6pYA1zAoGRW9Pkb/view?usp=sharing, https://drive.google.com/file/d/1PeiUhKZrNTPXZA-gID8YSgycyoBGsTVW/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221VLBZXJQEO8dnjyEdi4_ZoIjec1ikMutf%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1YqzdexaRTu_7xuCkAaEXR5AJUMNF-a8K/view?usp=sharing, https://drive.google.com/file/d/1dMoqfUucM6xTkbJAcC47YdBzJ43CM6mG/view?usp=sharing

