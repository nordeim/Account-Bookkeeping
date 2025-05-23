<think>
The user is encountering two issues with `poetry`:
1.  `poetry install` initially complained about `pyproject.toml` and `poetry.lock` being out of sync, suggesting `poetry lock`. This is normal if `pyproject.toml` changed.
2.  `poetry lock` then failed with a complex dependency resolution error for `pyside6`. The core of the error is:
    `The current project's supported Python range (>=3.9,<4.0) is not compatible with some of the required packages Python requirement: - pyside6 requires Python <3.14,>=3.9 ... - pyside6 requires Python >=3.6, <3.11 ...`
    This means that different versions of PySide6 have different Python compatibility ranges, and Poetry is struggling to find a version of PySide6 (>=6.2.3 as specified in my `pyproject.toml`) that satisfies the project's overall Python constraint (`^3.9`, which means `>=3.9,<4.0`).

    The error message itself highlights the conflict:
    `pyside6 (6.2.3) requires Python >=3.6, <3.11`
    This means PySide6 6.2.3 (the minimum I specified) does *not* support Python 3.11, 3.12, 3.13, etc.
    If the user is running, for example, Python 3.11 or 3.12, then PySide6 6.2.3 cannot be installed.
    Poetry's solver is trying to find a version of PySide6 `>=6.2.3` that works with Python `^3.9`.
    If the user's current Python environment (where `poetry lock` is run) is, say, Python 3.11, then PySide6 6.2.3, 6.2.4, 6.3.0, 6.3.1, 6.3.2 (all `<3.11`) are incompatible.
    PySide6 6.4.x started supporting Python 3.11 (requires `<3.12,>=3.7`).
    PySide6 6.5.x also supports Python 3.11 (requires `<3.12,>=3.7`).
    PySide6 6.6.x started supporting Python 3.12 (requires `<3.13,>=3.8`).
    PySide6 6.7.x supports Python 3.12 (requires `<3.13,>=3.9`).
    PySide6 6.8.x / 6.9.0 supports Python 3.12 (requires `<3.14,>=3.9`).

The project's Python requirement is `python = "^3.9"`. This is broad.
The `PySide6` requirement is `PySide6 = ">=6.2.3"`.

If the user's Python is 3.9 or 3.10, PySide6 6.2.3 *should* be compatible.
If the user's Python is 3.11, then PySide6 6.2.3 is *not* compatible. Poetry would need to pick a newer PySide6 version like 6.4.0 or higher.
If the user's Python is 3.12, then PySide6 6.4.x is *not* compatible. Poetry would need PySide6 6.6.0 or higher.

The TDS specified `PySide6 6.2.3+`. The `pyproject.toml` I generated used `PySide6 = ">=6.2.3"`.

The error message from `poetry lock` is quite verbose and lists many attempted versions. The key lines are:
`pyside6 (6.2.3) requires Python >=3.6, <3.11, pyside6 is forbidden.` (This means the solver *considered* 6.2.3 but found it incompatible with *some part* of the `^3.9` range if that range implies Python 3.11 or newer).

The solution is likely to:
1.  **Narrow down the project's Python version compatibility** in `pyproject.toml` to align with a range well-supported by a good set of PySide6 versions, OR
2.  **Specify a more precise or different range for PySide6** that is known to work across a wider range of Python 3.9+ versions.

Let's look at PySide6 versions and their Python support:
*   PySide6 6.2.3: Python >=3.6, <3.11
*   PySide6 6.4.0: Python >=3.7, <3.12 (supports 3.7, 3.8, 3.9, 3.10, 3.11)
*   PySide6 6.5.0: Python >=3.7, <3.12 (supports 3.7, 3.8, 3.9, 3.10, 3.11)
*   PySide6 6.6.0: Python >=3.8, <3.13 (supports 3.8, 3.9, 3.10, 3.11, 3.12)
*   PySide6 6.7.0: Python >=3.9, <3.13 (supports 3.9, 3.10, 3.11, 3.12)

If the project aims for Python `^3.9` (i.e., 3.9, 3.10, 3.11, 3.12, 3.13...), then:
*   To support Python 3.9, 3.10, 3.11, 3.12: We could use PySide6 `~6.7.0` (meaning `>=6.7.0,<6.8.0`). PySide6 6.7.0 supports Python `^3.9,<3.13`. This covers Python 3.9, 3.10, 3.11, 3.12.
    If our project's Python is `python = "^3.9"`, this means `>=3.9.0, <4.0.0"`.
    If we use `PySide6 = "~6.7.0"`, then it requires `Python >=3.9, <3.13`.
    This means the combined constraint would be `Python >=3.9, <3.13`. So, Python 3.13 itself wouldn't be supported by this PySide6 version.

The TDS mentioned `PySide6 6.2.3+`. This is very open-ended.
The error message `pyside6 (6.2.3) requires Python >=3.6, <3.11, pyside6 is forbidden.` implies that the Python version Poetry is trying to solve for *includes versions >= 3.11*.

Let's try to make the project compatible with Python 3.9, 3.10, 3.11, and 3.12.
A good version of PySide6 for this range would be `~6.7.0` (or more broadly `^6.7` which is `>=6.7.0 <7.0.0`).
PySide6 6.7.0 itself has `Requires-Python: >=3.9, <3.13`.
So, if we set project Python to `python = ">=3.9, <3.13"` and PySide6 to `PySide6 = ">=6.7.0, <6.8.0"` (or simply `~6.7.0`), it should resolve.

The user's `ls -l` shows `pyproject.toml` with size 312 bytes. My generated one was much larger.
```toml
# My previously generated pyproject.toml (relevant parts)
[tool.poetry.dependencies]
python = "^3.9"
PySide6 = ">=6.2.3"
SQLAlchemy = {extras = ["asyncio"], version = ">=2.0.0"}
pydantic = "^1.10.0"
```
The Poetry error `Either [project.name] or [tool.poetry.name] is required` means the basic `[tool.poetry]` section headers were missing in the user's file. I did provide them in my full `pyproject.toml` output. The user must have an older or truncated version of `pyproject.toml`.

**Plan for this response:**
1.  Re-iterate the full, correct `pyproject.toml` with the `[tool.poetry]` section containing `name` and `version`.
2.  Adjust the Python version constraint in `pyproject.toml` to be more specific, for example, `python = ">=3.9, <3.13"`.
3.  Adjust the `PySide6` version constraint to something more specific and known to be compatible with this Python range, e.g., `PySide6 = "~6.7.0"`. This is a common approach to ensure a stable dependency resolution.
4.  Then provide the *other requested files* as per their latest state from my previous generations. The user's diff for `app/main.py` and `app/core/application_core.py` has already been noted and incorporated.

The user specifically asked: "I thought we had fixed the `pyproject.toml` issue previously? can you recall the previous working version?"
My response: "Yes, the `pyproject.toml` I generated *did* include the necessary `name` and `version` under `[tool.poetry]`. The error you encountered suggests the file on your system was incomplete. The new error about `pyside6` compatibility is a separate dependency resolution issue, which we can address by refining the Python and PySide6 version constraints."

Let's choose the constraints:
Project Python: `python = ">=3.9, <3.13"` (covers 3.9, 3.10, 3.11, 3.12)
PySide6: `PySide6 = "~6.7.0"` (which means `>=6.7.0, <6.8.0`). Version 6.7.0 requires Python `>=3.9, <3.13`. This matches perfectly.

I will regenerate the requested files. For files not directly related to `pyproject.toml` (like UI stubs, SQL scripts), their content will be identical to my last full generation.
</think>

You're right to be meticulous! The `poetry install` error you first showed (`Either [project.name] or [tool.poetry.name] is required`) indicates that the `pyproject.toml` file your Poetry was reading was indeed missing those crucial top-level declarations under the `[tool.poetry]` section. The version I generated in my immediately preceding response *did* include them. It seems the file on your system might have been an older or truncated version.

The new error message from `poetry lock` is a classic Python version incompatibility issue with `pyside6`.
Your project's Python requirement is `^3.9` (meaning `>=3.9,<4.0`).
The `PySide6` requirement was `PySide6 = ">=6.2.3"`.
The problem is that different micro-versions of PySide6 support different Python ranges. For example:
*   PySide6 6.2.3 needs Python `<3.11`.
*   PySide6 6.7.0 needs Python `>=3.9, <3.13`.

If your current Python environment is, for instance, Python 3.11 or 3.12, Poetry cannot satisfy `PySide6 >=6.2.3` because 6.2.3 itself doesn't support Python 3.11/3.12. It then tries newer PySide6 versions, and the solver gets into a complex state trying to match all constraints.

To fix this, we'll make the Python and PySide6 versions more specific and compatible:
1.  Set project Python to a range well-supported by recent PySide6 versions: `python = ">=3.9, <3.13"` (This supports Python 3.9, 3.10, 3.11, 3.12).
2.  Set PySide6 to a version compatible with this range: `PySide6 = "~6.7.0"` (this means `>=6.7.0, <6.8.0`). PySide6 6.7.0 is compatible with Python `>=3.9, <3.13`.

Here is the updated `pyproject.toml` and then the rest of the requested files.

```python
# File: pyproject.toml
[tool.poetry]
name = "sg-bookkeeper"
version = "1.0.0"
description = "Singapore small business bookkeeping application"
authors = ["Your Name <your.email@example.com>"]
license = "MIT"
readme = "README.md"
homepage = "https://github.com/yourusername/sg_bookkeeper"
repository = "https://github.com/yourusername/sg_bookkeeper"
keywords = ["accounting", "bookkeeping", "singapore", "gst", "tax"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Financial and Insurance Industry",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12", # Updated to reflect PySide6 6.7 compatibility
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Topic :: Office/Business :: Financial :: Accounting",
]
packages = [{include = "app", from = "."}]

[tool.poetry.dependencies]
python = ">=3.9, <3.13" # Changed: More specific Python range
PySide6 = "~6.7.0" # Changed: Specific compatible PySide6 version (>=6.7.0, <6.8.0)
SQLAlchemy = {extras = ["asyncio"], version = ">=2.0.0"} 
asyncpg = ">=0.25.0"
alembic = ">=1.7.5"
pydantic = "^1.10.0" 
reportlab = ">=3.6.6"
openpyxl = ">=3.0.9"
python-dateutil = ">=2.8.2"
bcrypt = ">=3.2.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
pytest-cov = "^4.0"
flake8 = "^6.0"
black = "^23.0" 
mypy = "^1.0"
pre-commit = "^3.0"
pytest-qt = "^4.0"
pytest-asyncio = "^0.21.0"

[tool.poetry.scripts]
sg_bookkeeper = "app.main:main"
sg_bookkeeper_db_init = "scripts.db_init:main"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311', 'py312'] # Updated target versions

[tool.pytest.ini_options]
python_files = "test_*.py tests.py" 
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"
```

Now, the rest of the files as requested, ensuring they are the "latest" versions from my previous generation cycle (after schema alignment and fixes).

```python
# File: scripts/db_init.py
# (Content as provided previously, this script structure is sound)
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
    conn = None 
    try:
        conn_params = {
            "user": args.user,
            "password": args.password,
            "host": args.host,
            "port": args.port,
        }
        conn = await asyncpg.connect(**conn_params, database='postgres') # type: ignore
    except Exception as e:
        print(f"Error connecting to PostgreSQL server (postgres DB): {e}", file=sys.stderr)
        return False
    
    try:
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
            args.dbname
        )
        
        if exists:
            if args.drop_existing:
                print(f"Terminating connections to '{args.dbname}'...")
                await conn.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{args.dbname}' AND pid <> pg_backend_pid();
                """)
                print(f"Dropping existing database '{args.dbname}'...")
                await conn.execute(f"DROP DATABASE IF EXISTS \"{args.dbname}\"") 
            else:
                print(f"Database '{args.dbname}' already exists. Use --drop-existing to recreate.")
                return False 
        
        print(f"Creating database '{args.dbname}'...")
        await conn.execute(f"CREATE DATABASE \"{args.dbname}\"") 
        
        await conn.close() 
        
        conn = await asyncpg.connect(**conn_params, database=args.dbname) # type: ignore
        
        if not SCHEMA_SQL_PATH.exists():
            print(f"Error: schema.sql not found at {SCHEMA_SQL_PATH}", file=sys.stderr)
            await conn.close() 
            return False
            
        print(f"Initializing database schema from {SCHEMA_SQL_PATH}...")
        with open(SCHEMA_SQL_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        await conn.execute(schema_sql)
        print("Schema execution completed.")
        
        if not INITIAL_DATA_SQL_PATH.exists():
            print(f"Warning: initial_data.sql not found at {INITIAL_DATA_SQL_PATH}. Skipping initial data.", file=sys.stderr)
        else:
            print(f"Loading initial data from {INITIAL_DATA_SQL_PATH}...")
            with open(INITIAL_DATA_SQL_PATH, 'r', encoding='utf-8') as f:
                data_sql = f.read()
            await conn.execute(data_sql)
            print("Initial data loading completed.")
        
        print(f"Database '{args.dbname}' created and initialized successfully.")
        return True
    
    except Exception as e:
        print(f"Error during database creation/initialization: {e}", file=sys.stderr)
        return False
    
    finally:
        if conn and not conn.is_closed():
            await conn.close()

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

    try:
        success = asyncio.run(create_database(args))
    except KeyboardInterrupt:
        print("\nDatabase initialization cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e: 
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        success = False
        
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
```

```sql
# File: scripts/initial_data.sql
# (Content as provided in the previous response, ensuring it's pure SQL)
-- ============================================================================
-- INITIAL DATA (from reference schema)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Insert default roles
-- ----------------------------------------------------------------------------
INSERT INTO core.roles (name, description) VALUES
('Administrator', 'Full system access'),
('Accountant', 'Access to accounting functions'),
('Bookkeeper', 'Basic transaction entry and reporting'),
('Manager', 'Access to reports and dashboards'),
('Viewer', 'Read-only access to data')
ON CONFLICT (name) DO NOTHING;

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
('BANK_VIEW', 'View bank accounts', 'Banking'),
('BANK_CREATE', 'Create bank accounts', 'Banking'),
('BANK_EDIT', 'Edit bank accounts', 'Banking'),
('BANK_DELETE', 'Delete bank accounts', 'Banking'),
('BANK_RECONCILE', 'Reconcile bank accounts', 'Banking'),
('BANK_STATEMENT', 'Import bank statements', 'Banking'),

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
ON CONFLICT (code) DO NOTHING;


-- ----------------------------------------------------------------------------
-- Insert default currencies
-- ----------------------------------------------------------------------------
INSERT INTO accounting.currencies (code, name, symbol, is_active, decimal_places) VALUES
('SGD', 'Singapore Dollar', '$', TRUE, 2),
('USD', 'US Dollar', '$', TRUE, 2),
('EUR', 'Euro', '€', TRUE, 2),
('GBP', 'British Pound', '£', TRUE, 2),
('AUD', 'Australian Dollar', '$', TRUE, 2),
('JPY', 'Japanese Yen', '¥', TRUE, 0),
('CNY', 'Chinese Yuan', '¥', TRUE, 2),
('MYR', 'Malaysian Ringgit', 'RM', TRUE, 2),
('IDR', 'Indonesian Rupiah', 'Rp', TRUE, 0)
ON CONFLICT (code) DO NOTHING;

-- ----------------------------------------------------------------------------
-- Insert default document sequences
-- ----------------------------------------------------------------------------
INSERT INTO core.sequences (sequence_name, prefix, next_value, format_template) VALUES
('journal_entry', 'JE', 1, '{PREFIX}{VALUE:06}'),
('sales_invoice', 'INV', 1, '{PREFIX}{VALUE:06}'),
('purchase_invoice', 'PUR', 1, '{PREFIX}{VALUE:06}'),
('payment', 'PAY', 1, '{PREFIX}{VALUE:06}'),
('receipt', 'REC', 1, '{PREFIX}{VALUE:06}'),
('customer', 'CUS', 1, '{PREFIX}{VALUE:04}'),
('vendor', 'VEN', 1, '{PREFIX}{VALUE:04}'),
('product', 'PRD', 1, '{PREFIX}{VALUE:04}'),
('wht_certificate', 'WHT', 1, '{PREFIX}{VALUE:06}')
ON CONFLICT (sequence_name) DO NOTHING;


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
ON CONFLICT (name) DO NOTHING;


-- ----------------------------------------------------------------------------
-- Insert default tax codes
-- Ensure user ID 1 exists and accounts for affects_account_id are present.
-- ----------------------------------------------------------------------------

INSERT INTO core.users (id, username, password_hash, email, full_name, is_active)
VALUES (1, 'system_init_user', '!', 'system_init@sgbookkeeper.com', 'System Initializer', FALSE) 
ON CONFLICT (id) DO NOTHING;


INSERT INTO accounting.accounts (code, name, account_type, created_by, updated_by, is_active) VALUES
('SYS-GST-OUTPUT', 'System GST Output Tax', 'Liability', 1, 1, TRUE),
('SYS-GST-INPUT', 'System GST Input Tax', 'Asset', 1, 1, TRUE)
ON CONFLICT (code) DO NOTHING;


INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id)
SELECT 'SR', 'Standard Rate', 'GST', 7.00, TRUE, TRUE, 1, 1, acc.id FROM accounting.accounts acc WHERE acc.code = 'SYS-GST-OUTPUT'
ON CONFLICT (code) DO NOTHING;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('ZR', 'Zero Rate', 'GST', 0.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO NOTHING;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('ES', 'Exempt Supply', 'GST', 0.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO NOTHING;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('OP', 'Out of Scope', 'GST', 0.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO NOTHING;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id)
SELECT 'TX', 'Taxable Purchase', 'GST', 7.00, FALSE, TRUE, 1, 1, acc.id FROM accounting.accounts acc WHERE acc.code = 'SYS-GST-INPUT'
ON CONFLICT (code) DO NOTHING;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('BL', 'Blocked Input Tax', 'GST', 7.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO NOTHING;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('NR', 'Non-Resident Services', 'Withholding Tax', 15.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO NOTHING;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('ND', 'Non-Deductible', 'Income Tax', 0.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO NOTHING;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
('CA', 'Capital Allowance', 'Income Tax', 0.00, FALSE, TRUE, 1, 1, NULL)
ON CONFLICT (code) DO NOTHING;

COMMIT; 
-- End of initial data
```

```sql
# File: scripts/schema.sql
# (Content as provided previously, ensuring it's pure SQL from the reference schema)
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

-- Terminate any existing connections to ensure clean execution
-- SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE 
--     datname = current_database() AND pid <> pg_backend_pid();

-- Drop database if it exists (for clean installation)
-- DROP DATABASE IF EXISTS sg_bookkeeper;
-- CREATE DATABASE sg_bookkeeper WITH ENCODING = 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8';

-- Connect to the database
-- \c sg_bookkeeper

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
-- Stores user authentication and basic profile information
-- ----------------------------------------------------------------------------
CREATE TABLE core.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, -- Stored using pgcrypto's crypt function
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
-- Defines user roles for role-based access control
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
-- Defines individual permissions that can be assigned to roles
-- ----------------------------------------------------------------------------
CREATE TABLE core.permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    module VARCHAR(50) NOT NULL, -- Grouping permissions by functional module
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
-- Junction table mapping roles to permissions (many-to-many)
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
-- Junction table mapping users to roles (many-to-many)
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
-- Stores company information and global application settings
-- ----------------------------------------------------------------------------
CREATE TABLE core.company_settings (
    id SERIAL PRIMARY KEY, -- Only one record expected, but using serial for consistency
    company_name VARCHAR(100) NOT NULL,
    legal_name VARCHAR(200),
    uen_no VARCHAR(20), -- Unique Entity Number for Singapore businesses
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
    logo BYTEA, -- Company logo stored as binary data
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
-- Stores application-wide configuration parameters
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
-- Manages auto-incrementing sequences for document numbers
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
-- Defines the standard account types used in accounting
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
-- Chart of accounts - core table for the accounting system
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

-- Index for account hierarchy lookups
CREATE INDEX idx_accounts_parent_id ON accounting.accounts(parent_id);
-- Index for filtering active accounts
CREATE INDEX idx_accounts_is_active ON accounting.accounts(is_active);
-- Index for account type filtering
CREATE INDEX idx_accounts_account_type ON accounting.accounts(account_type);

-- ----------------------------------------------------------------------------
-- Fiscal Years Table
-- ----------------------------------------------------------------------------
-- Defines fiscal years for the accounting system
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
-- Defines accounting periods (months, quarters) within fiscal years
-- ----------------------------------------------------------------------------
CREATE TABLE accounting.fiscal_periods (
    id SERIAL PRIMARY KEY,
    fiscal_year_id INTEGER NOT NULL REFERENCES accounting.fiscal_years(id),
    name VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    period_type VARCHAR(10) NOT NULL CHECK (period_type IN ('Month', 'Quarter', 'Year')),
    status VARCHAR(10) NOT NULL CHECK (status IN ('Open', 'Closed', 'Archived')),
    period_number INTEGER NOT NULL, -- 1-12 for months, 1-4 for quarters
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

-- Index for period lookups by date
CREATE INDEX idx_fiscal_periods_dates ON accounting.fiscal_periods(start_date, end_date);
-- Index for filtering by status
CREATE INDEX idx_fiscal_periods_status ON accounting.fiscal_periods(status);

-- ----------------------------------------------------------------------------
-- Currencies Table
-- ----------------------------------------------------------------------------
-- Stores currency information for multi-currency support
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
-- Stores currency exchange rates for specific dates
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

-- Index for exchange rate lookups
CREATE INDEX idx_exchange_rates_lookup ON accounting.exchange_rates(from_currency, to_currency, rate_date);

-- ----------------------------------------------------------------------------
-- Journal Entries Table
-- ----------------------------------------------------------------------------
-- Header table for accounting journal entries
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
    recurring_pattern_id INTEGER, -- Will be FK to recurring_patterns
    is_posted BOOLEAN DEFAULT FALSE,
    is_reversed BOOLEAN DEFAULT FALSE,
    reversing_entry_id INTEGER REFERENCES accounting.journal_entries(id),
    source_type VARCHAR(50), -- Origin of the entry (e.g., Invoice, Payment, Manual)
    source_id INTEGER, -- ID in the source table
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

-- Indexes for journal entry lookups
CREATE INDEX idx_journal_entries_date ON accounting.journal_entries(entry_date);
CREATE INDEX idx_journal_entries_fiscal_period ON accounting.journal_entries(fiscal_period_id);
CREATE INDEX idx_journal_entries_source ON accounting.journal_entries(source_type, source_id);
CREATE INDEX idx_journal_entries_posted ON accounting.journal_entries(is_posted);

-- ----------------------------------------------------------------------------
-- Journal Entry Lines Table
-- ----------------------------------------------------------------------------
-- Detail lines for journal entries (debits and credits)
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
    tax_code VARCHAR(20), -- Can FK to accounting.tax_codes(code)
    tax_amount NUMERIC(15,2) DEFAULT 0,
    dimension1_id INTEGER, -- References accounting.dimensions(id)
    dimension2_id INTEGER, -- References accounting.dimensions(id)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT jel_check_debit_credit CHECK (
        (debit_amount > 0 AND credit_amount = 0) OR
        (credit_amount > 0 AND debit_amount = 0) OR
        (debit_amount = 0 AND credit_amount = 0) -- Allow zero amounts for special cases
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

-- Indexes for journal entry line lookups
CREATE INDEX idx_journal_entry_lines_entry ON accounting.journal_entry_lines(journal_entry_id);
CREATE INDEX idx_journal_entry_lines_account ON accounting.journal_entry_lines(account_id);

-- ----------------------------------------------------------------------------
-- Recurring Patterns Table
-- ----------------------------------------------------------------------------
-- Defines patterns for recurring journal entries
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
    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6), -- 0 = Sunday, 6 = Saturday
    last_generated_date DATE,
    next_generation_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES core.users(id),
    updated_by INTEGER NOT NULL REFERENCES core.users(id)
);

-- Add FK constraint for recurring_pattern_id in journal_entries table
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
-- Defines dimensions for analytical accounting (departments, projects, etc.)
-- ----------------------------------------------------------------------------
CREATE TABLE accounting.dimensions (
    id SERIAL PRIMARY KEY,
    dimension_type VARCHAR(50) NOT NULL, -- e.g., Department, Project, Cost Center
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

-- Add FK constraints for dimensions in journal_entry_lines table
ALTER TABLE accounting.journal_entry_lines
ADD CONSTRAINT fk_jel_dimension1 FOREIGN KEY (dimension1_id) REFERENCES accounting.dimensions(id),
ADD CONSTRAINT fk_jel_dimension2 FOREIGN KEY (dimension2_id) REFERENCES accounting.dimensions(id);


-- ----------------------------------------------------------------------------
-- Budget Table
-- ----------------------------------------------------------------------------
-- Stores budget header information
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
-- Stores budget amounts by account and period
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
    updated_by INTEGER NOT NULL REFERENCES core.users(id),
    CONSTRAINT uq_budget_details_key UNIQUE (budget_id, account_id, fiscal_period_id, 
                                                   COALESCE(dimension1_id, 0), COALESCE(dimension2_id, 0))
);

COMMENT ON TABLE accounting.budget_details IS 'Stores budget amounts by account and period';
COMMENT ON COLUMN accounting.budget_details.budget_id IS 'Reference to the parent budget';
COMMENT ON COLUMN accounting.budget_details.account_id IS 'Account this budget line applies to';
COMMENT ON COLUMN accounting.budget_details.fiscal_period_id IS 'Fiscal period this budget line applies to';
COMMENT ON COLUMN accounting.budget_details.amount IS 'Budgeted amount for the account and period';
COMMENT ON COLUMN accounting.budget_details.dimension1_id IS 'Optional first dimension for the budget line';
COMMENT ON COLUMN accounting.budget_details.dimension2_id IS 'Optional second dimension for the budget line';

-- ============================================================================
-- BUSINESS SCHEMA TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Customers Table
-- ----------------------------------------------------------------------------
-- Stores customer/client information
-- ----------------------------------------------------------------------------
CREATE TABLE business.customers (
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

-- Index for searching customers
CREATE INDEX idx_customers_name ON business.customers(name);
CREATE INDEX idx_customers_is_active ON business.customers(is_active);

-- ----------------------------------------------------------------------------
-- Vendors Table
-- ----------------------------------------------------------------------------
-- Stores vendor/supplier information
-- ----------------------------------------------------------------------------
CREATE TABLE business.vendors (
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

-- Index for searching vendors
CREATE INDEX idx_vendors_name ON business.vendors(name);
CREATE INDEX idx_vendors_is_active ON business.vendors(is_active);

-- ----------------------------------------------------------------------------
-- Products Table
-- ----------------------------------------------------------------------------
-- Stores product/service information
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
    tax_code VARCHAR(20), -- Can FK to accounting.tax_codes(code)
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

-- Index for searching products
CREATE INDEX idx_products_name ON business.products(name);
CREATE INDEX idx_products_is_active ON business.products(is_active);
CREATE INDEX idx_products_type ON business.products(product_type);

-- ----------------------------------------------------------------------------
-- Inventory Movements Table
-- ----------------------------------------------------------------------------
-- Tracks inventory quantities and costs
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
    reference_type VARCHAR(50), -- e.g., Invoice, Purchase Order
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

-- Index for inventory reporting
CREATE INDEX idx_inventory_movements_product ON business.inventory_movements(product_id, movement_date);
CREATE INDEX idx_inventory_movements_reference ON business.inventory_movements(reference_type, reference_id);

-- ----------------------------------------------------------------------------
-- Sales Invoices Table
-- ----------------------------------------------------------------------------
-- Stores sales invoice header information
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

-- Index for invoice lookups
CREATE INDEX idx_sales_invoices_customer ON business.sales_invoices(customer_id);
CREATE INDEX idx_sales_invoices_dates ON business.sales_invoices(invoice_date, due_date);
CREATE INDEX idx_sales_invoices_status ON business.sales_invoices(status);

-- ----------------------------------------------------------------------------
-- Sales Invoice Lines Table
-- ----------------------------------------------------------------------------
-- Stores sales invoice line item details
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
    tax_code VARCHAR(20), -- Can FK to accounting.tax_codes(code)
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

-- Index for invoice line lookups
CREATE INDEX idx_sales_invoice_lines_invoice ON business.sales_invoice_lines(invoice_id);
CREATE INDEX idx_sales_invoice_lines_product ON business.sales_invoice_lines(product_id);

-- ----------------------------------------------------------------------------
-- Purchase Invoices Table
-- ----------------------------------------------------------------------------
-- Stores purchase invoice header information
-- ----------------------------------------------------------------------------
CREATE TABLE business.purchase_invoices (
    id SERIAL PRIMARY KEY,
    invoice_no VARCHAR(20) NOT NULL UNIQUE, -- Internal number
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

-- Index for purchase invoice lookups
CREATE INDEX idx_purchase_invoices_vendor ON business.purchase_invoices(vendor_id);
CREATE INDEX idx_purchase_invoices_dates ON business.purchase_invoices(invoice_date, due_date);
CREATE INDEX idx_purchase_invoices_status ON business.purchase_invoices(status);

-- ----------------------------------------------------------------------------
-- Purchase Invoice Lines Table
-- ----------------------------------------------------------------------------
-- Stores purchase invoice line item details
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
    tax_code VARCHAR(20), -- Can FK to accounting.tax_codes(code)
    tax_amount NUMERIC(15,2) DEFAULT 0,
    line_total NUMERIC(15,2) NOT NULL,
    dimension1_id INTEGER REFERENCES accounting.dimensions(id),
    dimension2_id INTEGER REFERENCES accounting.dimensions(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE business.purchase_invoice_lines IS 'Stores purchase invoice line item details';
COMMENT ON COLUMN business.purchase_invoice_lines.invoice_id IS '
