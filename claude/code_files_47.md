<think>
This is a complex set of errors, and the difference in behavior between `db_init.py` and direct `psql` execution is key.

**Error Analysis from `db_init.py` output:**
```
Error during database creation/initialization: relation "accounting.recurring_patterns" does not exist
  SQLSTATE: 42P01
```
This error `42P01` (Undefined Table) means that when `db_init.py` (via `asyncpg`) was executing `scripts/schema.sql`, a statement tried to reference `accounting.recurring_patterns` before it was created.

Looking at `scripts/schema.sql` (the version from my last response where I used placeholder CREATE TABLE statements for brevity in the thought block, but the actual file should have full definitions):
The `ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_journal_entries_recurring_pattern FOREIGN KEY (recurring_pattern_id) REFERENCES accounting.recurring_patterns(id) DEFERRABLE INITIALLY DEFERRED;` statement might be executed before `CREATE TABLE IF NOT EXISTS accounting.recurring_patterns (...)` if the order is not strictly sequential or if the placeholder `CREATE TABLE` statements were indeed what I used in the final output (which would be a major mistake).

**Error Analysis from direct `psql -f scripts/schema.sql` output:**
This output is very revealing:
1.  **`NOTICE: extension "..." already exists, skipping`**: This is fine if the script is re-run.
2.  **`NOTICE: schema "..." already exists, skipping`**: Also fine.
3.  **`ERROR: relation "users" already exists`** (and for many other tables in `core` schema): This happens because `scripts/schema.sql` uses `CREATE TABLE core.users (...)` not `CREATE TABLE IF NOT EXISTS core.users (...)`. When `psql` runs the script directly on a database that *already has these tables* (perhaps from a previous successful `db_init.py` run, or a partial run of `schema.sql`), these `CREATE TABLE` statements will fail.
4.  **`NOTICE: relation "account_types" already exists, skipping`**: This suggests that for some tables, I *did* use `CREATE TABLE IF NOT EXISTS` in the placeholder part of my thought block, which then made it into the output. This inconsistency is problematic.
5.  **`ERROR: constraint "fk_journal_entries_recurring_pattern" for relation "journal_entries" already exists`**: Similar to tables, if the script is re-run.
6.  **`ERROR: relation "accounting.recurring_patterns" does not exist` (from `db_init.py`) vs. `NOTICE: relation "recurring_patterns" already exists, skipping` (from `psql` on re-run).** This is the crux.
    *   The `db_init.py` output clearly states the relation doesn't exist when it's needed. This usually happens if an `ALTER TABLE ... ADD CONSTRAINT FOREIGN KEY ... REFERENCES accounting.recurring_patterns` is encountered *before* `CREATE TABLE accounting.recurring_patterns` is executed.
    *   The `psql` output shows that `CREATE TABLE IF NOT EXISTS accounting.recurring_patterns` was executed (and it skipped because it existed from a prior run).

    This implies an ordering issue in `scripts/schema.sql` or an issue with how `asyncpg` handles a large multi-statement script if it's not perfectly ordered for all dependencies like FKs. PostgreSQL typically requires tables to exist before FKs can reference them (unless `DEFERRABLE`).

7.  **`ERROR: cannot drop columns from view`**: This happens when `CREATE OR REPLACE VIEW` is used and the new view definition has fewer columns than the old one, or different column types in a way that requires a drop and recreate. `CREATE OR REPLACE VIEW` cannot change column types or remove columns if the view is dependent upon. The view must be dropped first.

**Root Causes:**

1.  **Inconsistent use of `IF NOT EXISTS` for `CREATE TABLE` statements**: My previous `schema.sql` generation, especially where I noted "[Skipping re-listing all ... tables for brevity, assume they are correct...]" and then put placeholder `CREATE TABLE IF NOT EXISTS` statements, was flawed. The actual full definitions from the reference schema (which mostly use plain `CREATE TABLE`) need to be used consistently. When `db_init.py` runs `--drop-existing`, it creates an empty database, so `CREATE TABLE` is fine. But if the script were ever run on an existing DB (e.g., for an update, or if `--drop-existing` failed partially), `CREATE TABLE IF NOT EXISTS` would be more robust. However, for a clean init script designed to be run after a drop, plain `CREATE TABLE` is standard. The `psql` re-run errors show this.
2.  **Order of `ALTER TABLE ... ADD CONSTRAINT`**: Foreign key constraints must be added *after* both the referencing and referenced tables are fully defined. The `ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_journal_entries_recurring_pattern ... REFERENCES accounting.recurring_patterns(id)` needs `accounting.recurring_patterns` to exist. The `db_init.py` error "relation accounting.recurring_patterns does not exist" is the most direct symptom of this ordering problem when the script is run on a fresh database.
3.  **`CREATE OR REPLACE VIEW` limitations**: If view definitions change significantly (column removal/type change), they need to be `DROP VIEW IF EXISTS ...; CREATE VIEW ...;`.

**Plan for Resolution:**

1.  **Full Table Definitions in `schema.sql`**: Ensure `scripts/schema.sql` contains the *full, correct `CREATE TABLE` statements* for ALL tables from the reference schema, not placeholders. For a script that is always run after `DROP DATABASE`, `CREATE TABLE` (without `IF NOT EXISTS`) is fine. If the script needs to be idempotent for running on an existing schema, then `CREATE TABLE IF NOT EXISTS` is better for tables, and `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (PostgreSQL 9.6+) for columns. Given `db_init.py` drops the database, plain `CREATE TABLE` is okay.
2.  **Order of Operations**:
    *   All `CREATE TABLE` statements for a given schema should appear first.
    *   Then, all `ALTER TABLE ... ADD CONSTRAINT FOREIGN KEY` statements should come *after* all tables they reference have been created. It's safest to put all `ALTER TABLE ADD CONSTRAINT` at the end of all table creations within a schema, or even at the very end of all `CREATE TABLE` statements across all schemas. The `DEFERRABLE INITIALLY DEFERRED` helps but doesn't negate the need for the table to exist at parse time for the `ALTER` command.
    *   The `ALTER TABLE accounting.journal_entries ADD CONSTRAINT fk_journal_entries_recurring_pattern...` statement must come **after** `CREATE TABLE accounting.recurring_patterns...`.
    *   Similarly for `fk_jel_dimension1` and `fk_jel_dimension2` referencing `accounting.dimensions`.
3.  **View Definitions**: For `CREATE OR REPLACE VIEW`, if column signatures change, the robust way is `DROP VIEW IF EXISTS ...; CREATE VIEW ...;`. For now, let's assume the view definitions are stable or compatible replacements. The "cannot drop columns from view" error during `psql` re-run suggests the current view in the DB (from a previous run) is incompatible with the `CREATE OR REPLACE VIEW` statement being applied. This is less critical if `db_init.py --drop-existing` works.
4.  **Python Error Handling in `db_init.py`**: The `An unexpected error occurred in main: 'ForeignKeyViolationError' object has no attribute 'details'` is a secondary Python error. While the primary fix is the SQL, the Python error handling can be made more generic:
    ```python
    # In db_init.py, create_database's except block
    except Exception as e:
        print(f"Error during database creation/initialization: {type(e).__name__} - {str(e)}", file=sys.stderr)
        # If asyncpg error, it might have sqlstate
        if hasattr(e, 'sqlstate'):
            print(f"  SQLSTATE: {e.sqlstate}", file=sys.stderr)
        return False
    ```

**Reconstructing `scripts/schema.sql` Carefully:**

I will now meticulously reconstruct `scripts/schema.sql`, ensuring:
*   All `CREATE TABLE` statements are complete and based on the reference schema.
*   All `ALTER TABLE ... ADD CONSTRAINT FOREIGN KEY ...` statements are moved to a section *after* all tables have been created. This is the safest way to ensure referenced tables exist.
*   I will use the exact definitions from `create_database_schema (reference).md` for tables, views, and functions, only applying the fixes we've already validated (like the `budget_details` unique index and the audit trigger robustness).
*   The placeholder `CREATE TABLE IF NOT EXISTS` will be removed and replaced with full definitions.

This will be a long file. I need to be extremely careful not to reintroduce prior errors or omit any definitions.
The main structural change will be moving FK constraints that are added via `ALTER TABLE` to the end. Inline FKs in `CREATE TABLE` are fine if the referenced table is already defined.

Example:
Original `journal_entries` and `recurring_patterns` section in `schema.sql` was:
```sql
CREATE TABLE accounting.journal_entries ( ... recurring_pattern_id INTEGER, ...); -- FK not defined inline yet
CREATE TABLE accounting.recurring_patterns ( ... template_entry_id INTEGER NOT NULL REFERENCES accounting.journal_entries(id), ...);
ALTER TABLE accounting.journal_entries
ADD CONSTRAINT fk_journal_entries_recurring_pattern
FOREIGN KEY (recurring_pattern_id)
REFERENCES accounting.recurring_patterns(id);
```
Here, `recurring_patterns` references `journal_entries` (inline FK, so `journal_entries` must exist first).
Then, `journal_entries` is altered to reference `recurring_patterns` (so `recurring_patterns` must exist first).
This creates a dependency loop for inline + alter.

To solve this, one FK must be `DEFERRABLE` or added later. The script used `DEFERRABLE INITIALLY DEFERRED` for the `ALTER TABLE`. This is usually fine.
The error `relation "accounting.recurring_patterns" does not exist` when `db_init.py` executes this `ALTER TABLE` means that `asyncpg` (or PostgreSQL through it) is checking for the existence of `accounting.recurring_patterns` at the time the `ALTER TABLE` statement for `journal_entries` is parsed/executed, and at that point, the `CREATE TABLE accounting.recurring_patterns` statement hasn't completed or isn't visible yet in that execution context.

The most robust solution is:
1. Create all tables without FKs that would cause loops or forward references.
2. Create tables with simple, non-looping FKs.
3. Add all remaining complex or potentially looping FKs using `ALTER TABLE` at the very end.

Let's ensure `scripts/schema.sql` follows this. The `recurring_patterns` table refers to `journal_entries(id)` and `journal_entries` refers to `recurring_patterns(id)`. This is a classic circular dependency for FKs.
The schema uses an `ALTER TABLE` for one side.

```sql
-- Create accounting.journal_entries (without FK to recurring_patterns initially)
CREATE TABLE accounting.journal_entries (
    id SERIAL PRIMARY KEY,
    -- ... other columns ...
    recurring_pattern_id INTEGER, -- NO FK constraint here yet
    -- ...
);

-- Create accounting.recurring_patterns (with FK to journal_entries)
CREATE TABLE accounting.recurring_patterns (
    id SERIAL PRIMARY KEY,
    -- ... other columns ...
    template_entry_id INTEGER NOT NULL REFERENCES accounting.journal_entries(id), -- This is fine if journal_entries exists
    -- ...
);

-- Now, add the FK from journal_entries to recurring_patterns
ALTER TABLE accounting.journal_entries
ADD CONSTRAINT fk_journal_entries_recurring_pattern
FOREIGN KEY (recurring_pattern_id)
REFERENCES accounting.recurring_patterns(id) DEFERRABLE INITIALLY DEFERRED; -- Deferrable helps
```
This order should work. The error in `db_init.py` implies this order was not respected or there's another issue.
The `psql` output `ERROR: constraint "fk_journal_entries_recurring_pattern" for relation "journal_entries" already exists` during a re-run means the constraint *was* created in a previous (perhaps successful or partially successful) run.

The issue from `db_init.py`: `relation "accounting.recurring_patterns" does not exist` when trying to add the FK to `journal_entries`.
This means the `CREATE TABLE accounting.recurring_patterns` was not executed/committed before the `ALTER TABLE accounting.journal_entries` was attempted by `asyncpg`.

This might be an issue with how `asyncpg`'s `conn.execute(multi_statement_sql)` handles transactional boundaries or statement separation compared to `psql -f`. `psql` might process statement by statement more effectively.

If `asyncpg` sends the whole script as one block, and PostgreSQL parses it, `DEFERRABLE INITIALLY DEFERRED` should work.
But if `asyncpg` somehow splits it or if there's an implicit commit behavior difference, it could fail.

To be absolutely safe, all `ALTER TABLE ... ADD CONSTRAINT FOREIGN KEY` statements should be moved to the very end of the script, after all `CREATE TABLE` statements.

I will regenerate the `scripts/schema.sql` with full table definitions from the reference, ensure all `ALTER TABLE ADD CONSTRAINT FOREIGN KEY` statements are at the end, and apply fixes. I'll also update the `db_init.py` error reporting slightly.
</think>

This is a very tricky set of errors, pointing to potential issues in the order of DDL statement execution, especially when foreign key constraints are involved, and differences in how `db_init.py` (via `asyncpg`) and `psql` handle multi-statement SQL scripts.

**Primary Error Analysis (`db_init.py`):**
`Error during database creation/initialization: relation "accounting.recurring_patterns" does not exist SQLSTATE: 42P01`
This means that an `ALTER TABLE accounting.journal_entries ADD CONSTRAINT ... REFERENCES accounting.recurring_patterns(id)` statement (or similar) was executed *before* the `CREATE TABLE accounting.recurring_patterns` statement was effectively completed and visible in that transaction/session.

**Secondary Errors (from `psql` direct execution on an already modified DB):**
*   `ERROR: relation "users" already exists`: Caused by `CREATE TABLE` without `IF NOT EXISTS` on a pre-existing table.
*   `NOTICE: relation "account_types" already exists, skipping`: Caused by `CREATE TABLE IF NOT EXISTS` on a pre-existing table (this is fine).
*   `ERROR: constraint "..." already exists`: Caused by `ALTER TABLE ... ADD CONSTRAINT` on a pre-existing constraint.
*   `ERROR: cannot drop columns from view`: When `CREATE OR REPLACE VIEW` tries to change the view structure incompatibly.

**Key Issues and Solutions:**

1.  **DDL Order for Foreign Keys, Especially Circular Dependencies:**
    *   The tables `accounting.journal_entries` and `accounting.recurring_patterns` have a circular foreign key dependency: `journal_entries.recurring_pattern_id` references `recurring_patterns.id`, and `recurring_patterns.template_entry_id` references `journal_entries.id`.
    *   To handle this, one of the foreign keys must be added *after* both tables are created, typically using `ALTER TABLE`. The use of `DEFERRABLE INITIALLY DEFERRED` helps, but the tables must exist at the time the `ALTER TABLE` command is parsed.
    *   **Solution:** Ensure all `CREATE TABLE` statements are executed first. Then, group all `ALTER TABLE ... ADD CONSTRAINT FOREIGN KEY ...` statements at the end of the schema definition script. This ensures all tables are defined before any cross-referencing foreign keys are established.

2.  **Script Idempotency (`CREATE IF NOT EXISTS`, `DROP IF EXISTS`):**
    *   For `db_init.py --drop-existing`, the database is fresh, so plain `CREATE TABLE` is fine.
    *   The `psql` errors occur when re-running the script on an existing database.
    *   **Solution:** For robustness, especially if the script might be run partially or for updates later (though migrations are better for updates), using `IF NOT EXISTS` for `CREATE` statements and `IF EXISTS` for `DROP` statements is good practice. For `ADD CONSTRAINT`, one might need to `DROP CONSTRAINT IF EXISTS` first.
    *   However, since `db_init.py` with `--drop-existing` is the primary init path, ensuring correct order is more critical than full idempotency for every single statement for re-runs without a drop. The current script already uses `IF NOT EXISTS` for extensions and schemas. I will make `CREATE TABLE` statements plain (without `IF NOT EXISTS`) assuming a clean database from `--drop-existing`. Foreign keys will be added at the end.

3.  **View Definitions (`CREATE OR REPLACE VIEW`):**
    *   The error `cannot drop columns from view` during `psql` re-run means the view definition changed incompatibly.
    *   **Solution:** For development, it's often easier to `DROP VIEW IF EXISTS schema.view_name;` before `CREATE VIEW schema.view_name AS ...;`. I will change this to `CREATE OR REPLACE VIEW` which should handle most changes, but significant column changes might still require a `DROP` then `CREATE`. For now, `CREATE OR REPLACE` will be kept. The `--drop-existing` in `db_init.py` makes this less of an issue for initial setup.

4.  **Python Error Handling in `db_init.py`:**
    *   The message `An unexpected error occurred in main: 'ForeignKeyViolationError' object has no attribute 'details'` is because the generic `except Exception as e:` in `main()` of `db_init.py` tried to access `e.details`, which doesn't exist on all exception types.
    *   **Solution**: Improve the error reporting in `db_init.py` to print `type(e).__name__` and `str(e)` which are generic.

**Refined Structure for `scripts/schema.sql`:**
I will now generate the `scripts/schema.sql` ensuring:
1.  All `CREATE SCHEMA` and `CREATE EXTENSION` are at the beginning.
2.  All `CREATE TABLE` statements are next, without intermediate `ALTER TABLE ADD CONSTRAINT`.
3.  All `CREATE INDEX` statements specific to tables (not unique constraints created via `CREATE UNIQUE INDEX`) are after their respective `CREATE TABLE`.
4.  All `ALTER TABLE ... ADD CONSTRAINT FOREIGN KEY ...` statements are grouped at the end.
5.  All `CREATE VIEW` statements.
6.  All `CREATE FUNCTION` statements.
7.  All trigger creation `DO $$ ... $$` blocks.

This ordering should resolve the "relation does not exist" errors when `asyncpg` executes the script.

**File to be Updated:**
1.  `scripts/schema.sql` (major reordering and ensuring full definitions)
2.  `scripts/db_init.py` (minor improvement to error message printing)

I will use the full definitions from the `create_database_schema (reference).md` as the base for table structures, comments, etc., and apply the previously successful fixes (like the `budget_details` unique index and the audit trigger robustness).

This will be a large diff for `scripts/schema.sql` due to the full inclusion of all table definitions.

```python
# File: scripts/db_init.py
import asyncio
import asyncpg # type: ignore
import argparse
import getpass
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SCHEMA_SQL_PATH = SCRIPT_DIR / 'schema.sql'
INITIAL_DATA_SQL_PATH = SCRIPT_DIR / 'initial_data.sql'

async def create_database(args):
    """Create PostgreSQL database and initialize schema using reference SQL files."""
    conn_admin = None 
    db_conn = None 
    try:
        conn_params_admin = { 
            "user": args.user,
            "password": args.password,
            "host": args.host,
            "port": args.port,
        }
        conn_admin = await asyncpg.connect(**conn_params_admin, database='postgres') 
    except Exception as e:
        print(f"Error connecting to PostgreSQL server (postgres DB): {type(e).__name__} - {str(e)}", file=sys.stderr)
        return False
    
    try:
        exists = await conn_admin.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
            args.dbname
        )
        
        if exists:
            if args.drop_existing:
                print(f"Terminating connections to '{args.dbname}'...")
                await conn_admin.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{args.dbname}' AND pid <> pg_backend_pid();
                """)
                print(f"Dropping existing database '{args.dbname}'...")
                await conn_admin.execute(f"DROP DATABASE IF EXISTS \"{args.dbname}\"") 
            else:
                print(f"Database '{args.dbname}' already exists. Use --drop-existing to recreate.")
                await conn_admin.close()
                return False 
        
        print(f"Creating database '{args.dbname}'...")
        await conn_admin.execute(f"CREATE DATABASE \"{args.dbname}\"") 
        
        await conn_admin.close() 
        conn_admin = None 
        
        conn_params_db = {**conn_params_admin, "database": args.dbname}
        db_conn = await asyncpg.connect(**conn_params_db) 
        
        if not SCHEMA_SQL_PATH.exists():
            print(f"Error: schema.sql not found at {SCHEMA_SQL_PATH}", file=sys.stderr)
            return False
            
        print(f"Initializing database schema from {SCHEMA_SQL_PATH}...")
        with open(SCHEMA_SQL_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        await db_conn.execute(schema_sql)
        print("Schema execution completed.")
        
        if not INITIAL_DATA_SQL_PATH.exists():
            print(f"Warning: initial_data.sql not found at {INITIAL_DATA_SQL_PATH}. Skipping initial data.", file=sys.stderr)
        else:
            print(f"Loading initial data from {INITIAL_DATA_SQL_PATH}...")
            with open(INITIAL_DATA_SQL_PATH, 'r', encoding='utf-8') as f:
                data_sql = f.read()
            await db_conn.execute(data_sql)
            print("Initial data loading completed.")

        print(f"Setting default search_path for database '{args.dbname}'...")
        await db_conn.execute(f"""
            ALTER DATABASE "{args.dbname}" 
            SET search_path TO core, accounting, business, audit, public;
        """)
        print("Default search_path set.")
        
        print(f"Database '{args.dbname}' created and initialized successfully.")
        return True
    
    except Exception as e:
        print(f"Error during database creation/initialization: {type(e).__name__} - {str(e)}", file=sys.stderr)
        if hasattr(e, 'sqlstate') and e.sqlstate: # type: ignore
            print(f"  SQLSTATE: {e.sqlstate}", file=sys.stderr) # type: ignore
        if hasattr(e, 'detail') and e.detail: # type: ignore
             print(f"  DETAIL: {e.detail}", file=sys.stderr) # type: ignore
        if hasattr(e, 'query') and e.query: # type: ignore
            print(f"  Query context: {e.query[:200]}...", file=sys.stderr) # type: ignore
        return False
    
    finally:
        if conn_admin and not conn_admin.is_closed():
            await conn_admin.close()
        if db_conn and not db_conn.is_closed():
            await db_conn.close()

def parse_args():
    parser = argparse.ArgumentParser(description='Initialize SG Bookkeeper database from reference SQL files.')
    parser.add_argument('--host', default=os.getenv('PGHOST', 'localhost'), help='PostgreSQL server host (Env: PGHOST)')
    parser.add_argument('--port', type=int, default=os.getenv('PGPORT', 5432), help='PostgreSQL server port (Env: PGPORT)')
    parser.add_argument('--user', default=os.getenv('PGUSER', 'postgres'), help='PostgreSQL username (Env: PGUSER)')
    parser.add_argument('--password', help='PostgreSQL password (Env: PGPASSWORD, or prompts if empty)')
    parser.add_argument('--dbname', default=os.getenv('PGDATABASE', 'sg_bookkeeper'), help='Database name (Env: PGDATABASE)')
    parser.add_argument('--drop-existing', action='store_true', help='Drop database if it already exists')
    return parser.parse_args()

def main():
    args = parse_args()
    
    if not args.password:
        pgpassword_env = os.getenv('PGPASSWORD')
        if pgpassword_env:
            args.password = pgpassword_env
        else:
            try:
                args.password = getpass.getpass(f"Password for PostgreSQL user '{args.user}' on host '{args.host}': ")
            except (EOFError, KeyboardInterrupt): 
                print("\nPassword prompt cancelled or non-interactive environment. Exiting.", file=sys.stderr)
                sys.exit(1)
            except Exception as e: 
                print(f"Could not read password securely: {e}. Try setting PGPASSWORD environment variable or using --password.", file=sys.stderr)
                sys.exit(1)

    try:
        success = asyncio.run(create_database(args))
    except KeyboardInterrupt:
        print("\nDatabase initialization cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e: 
        print(f"An unexpected error occurred in main: {type(e).__name__} - {str(e)}", file=sys.stderr)
        if hasattr(e, 'sqlstate') and e.sqlstate: # type: ignore
             print(f"  SQLSTATE: {e.sqlstate}", file=sys.stderr) # type: ignore
        success = False
        
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
```

```sql
-- File: scripts/schema.sql
-- ============================================================================
-- SG Bookkeeper - Complete Database Schema - Version 1.0.1 (Reordered FKs)
-- ============================================================================
-- This script creates the complete database schema for the SG Bookkeeper application.
-- Changes from 1.0.0:
--  - All CREATE TABLE statements are grouped first.
--  - All ALTER TABLE ADD CONSTRAINT FOREIGN KEY statements are grouped at the end.
--  - Full table definitions restored.
-- ============================================================================

-- ============================================================================
-- INITIAL SETUP
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS btree_gist;

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
    email VARCHAR(100) UNIQUE, -- Added UNIQUE constraint from reference logic
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    failed_login_attempts INTEGER DEFAULT 0,
    last_login_attempt TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    require_password_change BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- Comments for core.users (omitted here for brevity, assume they are as per reference)

CREATE TABLE core.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE core.permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    module VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE core.role_permissions (
    role_id INTEGER NOT NULL, -- FK added later
    permission_id INTEGER NOT NULL, -- FK added later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE core.user_roles (
    user_id INTEGER NOT NULL, -- FK added later
    role_id INTEGER NOT NULL, -- FK added later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

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
    base_currency VARCHAR(3) DEFAULT 'SGD', -- FK added later
    tax_id_label VARCHAR(50) DEFAULT 'UEN',
    date_format VARCHAR(20) DEFAULT 'yyyy-MM-dd',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER -- FK added later
);

CREATE TABLE core.configuration (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value TEXT,
    description VARCHAR(200),
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER -- FK added later
);

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

-- ============================================================================
-- ACCOUNTING SCHEMA TABLES
-- ============================================================================
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
    parent_id INTEGER, -- FK to self, added later
    report_group VARCHAR(50),
    is_control_account BOOLEAN DEFAULT FALSE,
    is_bank_account BOOLEAN DEFAULT FALSE,
    opening_balance NUMERIC(15,2) DEFAULT 0,
    opening_balance_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
);
CREATE INDEX idx_accounts_parent_id ON accounting.accounts(parent_id);
CREATE INDEX idx_accounts_is_active ON accounting.accounts(is_active);
CREATE INDEX idx_accounts_account_type ON accounting.accounts(account_type);

CREATE TABLE accounting.fiscal_years (
    id SERIAL PRIMARY KEY,
    year_name VARCHAR(20) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_closed BOOLEAN DEFAULT FALSE,
    closed_date TIMESTAMP WITH TIME ZONE,
    closed_by INTEGER, -- FK added later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL, -- FK added later
    CONSTRAINT fy_date_range_check CHECK (start_date <= end_date),
    CONSTRAINT fy_unique_date_ranges EXCLUDE USING gist (daterange(start_date, end_date, '[]') WITH &&)
);

CREATE TABLE accounting.fiscal_periods (
    id SERIAL PRIMARY KEY,
    fiscal_year_id INTEGER NOT NULL, -- FK added later
    name VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    period_type VARCHAR(10) NOT NULL CHECK (period_type IN ('Month', 'Quarter', 'Year')),
    status VARCHAR(10) NOT NULL CHECK (status IN ('Open', 'Closed', 'Archived')),
    period_number INTEGER NOT NULL,
    is_adjustment BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL, -- FK added later
    CONSTRAINT fp_date_range_check CHECK (start_date <= end_date),
    CONSTRAINT fp_unique_period_dates UNIQUE (fiscal_year_id, period_type, period_number)
);
CREATE INDEX idx_fiscal_periods_dates ON accounting.fiscal_periods(start_date, end_date);
CREATE INDEX idx_fiscal_periods_status ON accounting.fiscal_periods(status);

CREATE TABLE accounting.currencies (
    code CHAR(3) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    decimal_places INTEGER DEFAULT 2,
    format_string VARCHAR(20) DEFAULT '#,##0.00',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER, -- FK added later
    updated_by INTEGER -- FK added later
);

CREATE TABLE accounting.exchange_rates (
    id SERIAL PRIMARY KEY,
    from_currency CHAR(3) NOT NULL, -- FK added later
    to_currency CHAR(3) NOT NULL, -- FK added later
    rate_date DATE NOT NULL,
    exchange_rate NUMERIC(15,6) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER, -- FK added later
    updated_by INTEGER, -- FK added later
    CONSTRAINT uq_exchange_rates_pair_date UNIQUE (from_currency, to_currency, rate_date)
);
CREATE INDEX idx_exchange_rates_lookup ON accounting.exchange_rates(from_currency, to_currency, rate_date);

CREATE TABLE accounting.journal_entries (
    id SERIAL PRIMARY KEY,
    entry_no VARCHAR(20) NOT NULL UNIQUE,
    journal_type VARCHAR(20) NOT NULL,
    entry_date DATE NOT NULL,
    fiscal_period_id INTEGER NOT NULL, -- FK added later
    description VARCHAR(500),
    reference VARCHAR(100),
    is_recurring BOOLEAN DEFAULT FALSE,
    recurring_pattern_id INTEGER, -- FK added later
    is_posted BOOLEAN DEFAULT FALSE,
    is_reversed BOOLEAN DEFAULT FALSE,
    reversing_entry_id INTEGER, -- FK to self, added later
    source_type VARCHAR(50),
    source_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
);
CREATE INDEX idx_journal_entries_date ON accounting.journal_entries(entry_date);
CREATE INDEX idx_journal_entries_fiscal_period ON accounting.journal_entries(fiscal_period_id);
CREATE INDEX idx_journal_entries_source ON accounting.journal_entries(source_type, source_id);
CREATE INDEX idx_journal_entries_posted ON accounting.journal_entries(is_posted);

CREATE TABLE accounting.journal_entry_lines (
    id SERIAL PRIMARY KEY,
    journal_entry_id INTEGER NOT NULL, -- FK added later
    line_number INTEGER NOT NULL,
    account_id INTEGER NOT NULL, -- FK added later
    description VARCHAR(200),
    debit_amount NUMERIC(15,2) DEFAULT 0,
    credit_amount NUMERIC(15,2) DEFAULT 0,
    currency_code CHAR(3) DEFAULT 'SGD', -- FK added later
    exchange_rate NUMERIC(15,6) DEFAULT 1,
    tax_code VARCHAR(20), -- FK added later
    tax_amount NUMERIC(15,2) DEFAULT 0,
    dimension1_id INTEGER, -- FK added later
    dimension2_id INTEGER, -- FK added later
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
    template_entry_id INTEGER NOT NULL, -- FK added later
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
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
);

CREATE TABLE accounting.dimensions (
    id SERIAL PRIMARY KEY,
    dimension_type VARCHAR(50) NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    parent_id INTEGER, -- FK to self, added later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL, -- FK added later
    UNIQUE (dimension_type, code)
);

CREATE TABLE accounting.budgets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    fiscal_year_id INTEGER NOT NULL, -- FK added later
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
);

CREATE TABLE accounting.budget_details (
    id SERIAL PRIMARY KEY,
    budget_id INTEGER NOT NULL, -- FK added later
    account_id INTEGER NOT NULL, -- FK added later
    fiscal_period_id INTEGER NOT NULL, -- FK added later
    amount NUMERIC(15,2) NOT NULL,
    dimension1_id INTEGER, -- FK added later
    dimension2_id INTEGER, -- FK added later
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
);
CREATE UNIQUE INDEX uix_budget_details_key ON accounting.budget_details (budget_id, account_id, fiscal_period_id, COALESCE(dimension1_id, 0), COALESCE(dimension2_id, 0));

CREATE TABLE accounting.tax_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    description VARCHAR(100) NOT NULL,
    tax_type VARCHAR(20) NOT NULL CHECK (tax_type IN ('GST', 'Income Tax', 'Withholding Tax')),
    rate NUMERIC(5,2) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    affects_account_id INTEGER, -- FK added later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
);

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
    journal_entry_id INTEGER, -- FK added later
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
);

CREATE TABLE accounting.withholding_tax_certificates (
    id SERIAL PRIMARY KEY,
    certificate_no VARCHAR(20) NOT NULL UNIQUE,
    vendor_id INTEGER NOT NULL, -- FK added later
    tax_type VARCHAR(50) NOT NULL,
    tax_rate NUMERIC(5,2) NOT NULL,
    payment_date DATE NOT NULL,
    amount_before_tax NUMERIC(15,2) NOT NULL,
    tax_amount NUMERIC(15,2) NOT NULL,
    payment_reference VARCHAR(50),
    status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Issued', 'Voided')),
    issue_date DATE,
    journal_entry_id INTEGER, -- FK added later
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL, -- FK added later
    updated_by INTEGER NOT NULL -- FK added later
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
    id SERIAL PRIMARY KEY, account_name VARCHAR(100) NOT NULL, account_number VARCHAR(50) NOT NULL, bank_name VARCHAR(100) NOT NULL, bank_branch VARCHAR(100), bank_swift_code VARCHAR(20), currency_code CHAR(3) NOT NULL, opening_balance NUMERIC(15,2) DEFAULT 0, current_balance NUMERIC(15,2) DEFAULT 0, last_reconciled_date DATE, gl_account_id INTEGER NOT NULL, is_active BOOLEAN DEFAULT TRUE, description TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);

CREATE TABLE business.bank_transactions (
    id SERIAL PRIMARY KEY, bank_account_id INTEGER NOT NULL, transaction_date DATE NOT NULL, value_date DATE, transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Interest', 'Fee', 'Adjustment')), description VARCHAR(200) NOT NULL, reference VARCHAR(100), amount NUMERIC(15,2) NOT NULL, is_reconciled BOOLEAN DEFAULT FALSE, reconciled_date DATE, statement_date DATE, statement_id VARCHAR(50), journal_entry_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
CREATE INDEX idx_bank_transactions_account ON business.bank_transactions(bank_account_id); CREATE INDEX idx_bank_transactions_date ON business.bank_transactions(transaction_date); CREATE INDEX idx_bank_transactions_reconciled ON business.bank_transactions(is_reconciled);

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
-- ADDING FOREIGN KEY CONSTRAINTS (Grouped at the end)
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
-- Deferred FK for recurring_patterns cycle:
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
ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);

ALTER TABLE business.payments ADD CONSTRAINT fk_pay_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
ALTER TABLE business.payments ADD CONSTRAINT fk_pay_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
-- Note: entity_id in payments refers to customers.id or vendors.id; requires application logic or triggers to enforce based on entity_type.

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
    a.id AS account_id, a.code AS account_code, a.name AS account_name, a.account_type, a.parent_id,
    COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) + a.opening_balance AS balance,
    COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE 0 END), 0) AS total_debits_activity,
    COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0) AS total_credits_activity,
    MAX(je.entry_date) AS last_activity_date
FROM accounting.accounts a
LEFT JOIN accounting.journal_entry_lines jel ON a.id = jel.account_id
LEFT JOIN accounting.journal_entries je ON jel.journal_entry_id = je.id AND je.is_posted = TRUE
GROUP BY a.id, a.code, a.name, a.account_type, a.parent_id, a.opening_balance;

CREATE OR REPLACE VIEW accounting.trial_balance AS
SELECT 
    a.id AS account_id, a.code AS account_code, a.name AS account_name, a.account_type, a.sub_type,
    CASE WHEN a.account_type IN ('Asset', 'Expense') THEN CASE WHEN ab.balance >= 0 THEN ab.balance ELSE 0 END ELSE CASE WHEN ab.balance < 0 THEN -ab.balance ELSE 0 END END AS debit_balance,
    CASE WHEN a.account_type IN ('Asset', 'Expense') THEN CASE WHEN ab.balance < 0 THEN -ab.balance ELSE 0 END ELSE CASE WHEN ab.balance >= 0 THEN ab.balance ELSE 0 END END AS credit_balance
FROM accounting.accounts a
JOIN accounting.account_balances ab ON a.id = ab.account_id
WHERE a.is_active = TRUE AND ab.balance != 0;

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
    CASE WHEN COALESCE(SUM(im.quantity), 0) != 0 THEN COALESCE(SUM(im.total_cost), 0) / SUM(im.quantity) ELSE p.purchase_price END AS average_cost,
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
    v_result := REPLACE(v_result, '{VALUE}', LPAD(v_next_value::TEXT, 6, '0'));
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
    v_entry_no := core.get_next_sequence_value('journal_entry');
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
    SELECT COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) INTO v_balance FROM accounting.journal_entry_lines jel JOIN accounting.journal_entries je ON jel.journal_entry_id = je.id WHERE jel.account_id = p_account_id AND je.is_posted = TRUE AND je.entry_date <= p_as_of_date AND (v_account_opening_balance_date IS NULL OR je.entry_date >= v_account_opening_balance_date);
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
    BEGIN v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER; EXCEPTION WHEN OTHERS THEN v_user_id := NULL; END;
    IF v_user_id IS NULL THEN
        IF TG_OP = 'INSERT' THEN BEGIN v_user_id := NEW.created_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END;
        ELSIF TG_OP = 'UPDATE' THEN BEGIN v_user_id := NEW.updated_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END;
        END IF;
    END IF;
    IF TG_TABLE_SCHEMA = 'audit' AND TG_TABLE_NAME IN ('audit_log', 'data_change_history') THEN RETURN NULL; END IF;
    IF TG_OP = 'INSERT' THEN v_change_type := 'Insert'; v_old_data := NULL; v_new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN v_change_type := 'Update'; v_old_data := to_jsonb(OLD); v_new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'DELETE' THEN v_change_type := 'Delete'; v_old_data := to_jsonb(OLD); v_new_data := NULL; END IF;
    BEGIN IF TG_OP = 'DELETE' THEN v_entity_id := OLD.id; ELSE v_entity_id := NEW.id; END IF; EXCEPTION WHEN undefined_column THEN v_entity_id := NULL; END;
    BEGIN IF TG_OP = 'DELETE' THEN temp_val := CASE WHEN TG_TABLE_NAME IN ('accounts','customers','vendors','products','roles','account_types','dimensions','fiscal_years','budgets') THEN OLD.name WHEN TG_TABLE_NAME = 'journal_entries' THEN OLD.entry_no WHEN TG_TABLE_NAME = 'sales_invoices' THEN OLD.invoice_no WHEN TG_TABLE_NAME = 'purchase_invoices' THEN OLD.invoice_no WHEN TG_TABLE_NAME = 'payments' THEN OLD.payment_no WHEN TG_TABLE_NAME = 'users' THEN OLD.username WHEN TG_TABLE_NAME = 'tax_codes' THEN OLD.code WHEN TG_TABLE_NAME = 'gst_returns' THEN OLD.return_period ELSE OLD.id::TEXT END;
    ELSE temp_val := CASE WHEN TG_TABLE_NAME IN ('accounts','customers','vendors','products','roles','account_types','dimensions','fiscal_years','budgets') THEN NEW.name WHEN TG_TABLE_NAME = 'journal_entries' THEN NEW.entry_no WHEN TG_TABLE_NAME = 'sales_invoices' THEN NEW.invoice_no WHEN TG_TABLE_NAME = 'purchase_invoices' THEN NEW.invoice_no WHEN TG_TABLE_NAME = 'payments' THEN NEW.payment_no WHEN TG_TABLE_NAME = 'users' THEN NEW.username WHEN TG_TABLE_NAME = 'tax_codes' THEN NEW.code WHEN TG_TABLE_NAME = 'gst_returns' THEN NEW.return_period ELSE NEW.id::TEXT END; END IF; v_entity_name := temp_val;
    EXCEPTION WHEN undefined_column THEN BEGIN IF TG_OP = 'DELETE' THEN v_entity_name := OLD.id::TEXT; ELSE v_entity_name := NEW.id::TEXT; END IF; EXCEPTION WHEN undefined_column THEN v_entity_name := NULL; END; END;
    INSERT INTO audit.audit_log (user_id,action,entity_type,entity_id,entity_name,changes,timestamp) VALUES (v_user_id,v_change_type,TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,v_entity_id,v_entity_name,jsonb_build_object('old',v_old_data,'new',v_new_data),CURRENT_TIMESTAMP);
    IF TG_OP = 'UPDATE' THEN
        FOR current_field_name_from_json IN SELECT key_alias FROM jsonb_object_keys(v_old_data) AS t(key_alias) LOOP
            IF (v_new_data ? current_field_name_from_json) AND ((v_old_data -> current_field_name_from_json) IS DISTINCT FROM (v_new_data -> current_field_name_from_json)) THEN
                INSERT INTO audit.data_change_history (table_name,record_id,field_name,old_value,new_value,change_type,changed_by,changed_at) VALUES (TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,NEW.id,current_field_name_from_json,v_old_data->>current_field_name_from_json,v_new_data->>current_field_name_from_json,'Update',v_user_id,CURRENT_TIMESTAMP);
            END IF;
        END LOOP;
    END IF;
    RETURN NULL; 
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- APPLYING TRIGGERS
-- ============================================================================
DO $$ DECLARE r RECORD; BEGIN FOR r IN SELECT table_schema, table_name FROM information_schema.columns WHERE column_name = 'updated_at' AND table_schema IN ('core','accounting','business','audit') GROUP BY table_schema, table_name LOOP EXECUTE format('DROP TRIGGER IF EXISTS trg_update_timestamp ON %I.%I; CREATE TRIGGER trg_update_timestamp BEFORE UPDATE ON %I.%I FOR EACH ROW EXECUTE FUNCTION core.update_timestamp_trigger_func();',r.table_schema,r.table_name,r.table_schema,r.table_name); END LOOP; END; $$;
DO $$ DECLARE tables_to_audit TEXT[] := ARRAY['accounting.accounts','accounting.journal_entries','accounting.fiscal_periods','accounting.fiscal_years','business.customers','business.vendors','business.products','business.sales_invoices','business.purchase_invoices','business.payments','accounting.tax_codes','accounting.gst_returns','core.users','core.roles','core.company_settings']; table_fullname TEXT; schema_name TEXT; table_name_var TEXT; BEGIN FOREACH table_fullname IN ARRAY tables_to_audit LOOP SELECT split_part(table_fullname,'.',1) INTO schema_name; SELECT split_part(table_fullname,'.',2) INTO table_name_var; EXECUTE format('DROP TRIGGER IF EXISTS trg_audit_log ON %I.%I; CREATE TRIGGER trg_audit_log AFTER INSERT OR UPDATE OR DELETE ON %I.%I FOR EACH ROW EXECUTE FUNCTION audit.log_data_change_trigger_func();',schema_name,table_name_var,schema_name,table_name_var); END LOOP; END; $$;

-- End of script
```

