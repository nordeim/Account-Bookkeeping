# data/report_templates/balance_sheet_default.json
```json
# File: data/report_templates/balance_sheet_default.json
# (Content as provided before - example structure)
"""
{
  "report_name": "Balance Sheet",
  "sections": [
    {
      "title": "Assets",
      "account_type": "Asset",
      "sub_sections": [
        {"title": "Current Assets", "account_sub_type_pattern": "Current Asset.*|Accounts Receivable|Cash.*"},
        {"title": "Non-Current Assets", "account_sub_type_pattern": "Fixed Asset.*|Non-Current Asset.*"}
      ]
    },
    {
      "title": "Liabilities",
      "account_type": "Liability",
      "sub_sections": [
        {"title": "Current Liabilities", "account_sub_type_pattern": "Current Liability.*|Accounts Payable|GST Payable"},
        {"title": "Non-Current Liabilities", "account_sub_type_pattern": "Non-Current Liability.*|Loan.*"}
      ]
    },
    {
      "title": "Equity",
      "account_type": "Equity"
    }
  ],
  "options": {
    "show_zero_balance": false,
    "comparative_periods": 1
  }
}
"""

```

# data/tax_codes/sg_gst_codes_2023.csv
```csv
# File: data/tax_codes/sg_gst_codes_2023.csv
# (Content as provided before, verified against initial_data.sql SYS-GST-* accounts)
"""Code,Description,TaxType,Rate,IsActive,AffectsAccountCode
SR,Standard-Rated Supplies,GST,7.00,TRUE,SYS-GST-OUTPUT
ZR,Zero-Rated Supplies,GST,0.00,TRUE,
ES,Exempt Supplies,GST,0.00,TRUE,
TX,Taxable Purchases (Standard-Rated),GST,7.00,TRUE,SYS-GST-INPUT
BL,Blocked Input Tax (e.g. Club Subscriptions),GST,7.00,TRUE,
OP,Out-of-Scope Supplies,GST,0.00,TRUE,
"""

```

# data/chart_of_accounts/general_template.csv
```csv
# File: data/chart_of_accounts/general_template.csv
# (Content as provided before, verified with new Account fields)
"""Code,Name,AccountType,SubType,TaxTreatment,GSTApplicable,ParentCode,ReportGroup,IsControlAccount,IsBankAccount,OpeningBalance,OpeningBalanceDate
1000,ASSETS,Asset,,,,,,,,0.00,
1100,Current Assets,Asset,,,,1000,CURRENT_ASSETS,FALSE,FALSE,0.00,
1110,Cash and Bank,Asset,Current Asset,,,1100,CASH_BANK,FALSE,TRUE,0.00,
1111,Main Bank Account SGD,Asset,Cash and Cash Equivalents,Non-Taxable,FALSE,1110,CASH_BANK,FALSE,TRUE,1000.00,2023-01-01
1112,Petty Cash,Asset,Cash and Cash Equivalents,Non-Taxable,FALSE,1110,CASH_BANK,FALSE,FALSE,100.00,2023-01-01
1120,Accounts Receivable,Asset,Accounts Receivable,,,1100,ACCOUNTS_RECEIVABLE,TRUE,FALSE,500.00,2023-01-01
1130,Inventory,Asset,Inventory,,,1100,INVENTORY,TRUE,FALSE,0.00,
1200,Non-Current Assets,Asset,,,,1000,NON_CURRENT_ASSETS,FALSE,FALSE,0.00,
1210,Property, Plant & Equipment,Asset,Fixed Assets,,,1200,PPE,FALSE,FALSE,0.00,
1211,Office Equipment,Asset,Fixed Assets,,,1210,PPE,FALSE,FALSE,5000.00,2023-01-01
1212,Accumulated Depreciation - Office Equipment,Asset,Fixed Assets,,,1210,PPE_ACCUM_DEPR,FALSE,FALSE,-500.00,2023-01-01
2000,LIABILITIES,Liability,,,,,,,,0.00,
2100,Current Liabilities,Liability,,,,2000,CURRENT_LIABILITIES,FALSE,FALSE,0.00,
2110,Accounts Payable,Liability,Accounts Payable,,,2100,ACCOUNTS_PAYABLE,TRUE,FALSE,0.00,
2120,GST Payable,Liability,GST Payable,Taxable,TRUE,2100,TAX_LIABILITIES,FALSE,FALSE,0.00,
2200,Non-Current Liabilities,Liability,,,,2000,NON_CURRENT_LIABILITIES,FALSE,FALSE,0.00,
2210,Bank Loan (Long Term),Liability,Long-term Liability,,,2200,LOANS_PAYABLE,FALSE,FALSE,0.00,
3000,EQUITY,Equity,,,,,,,,0.00,
3100,Owner's Capital,Equity,Owner''s Equity,,,3000,OWNERS_EQUITY,FALSE,FALSE,0.00,
3200,Retained Earnings,Equity,Retained Earnings,,,3000,RETAINED_EARNINGS,FALSE,FALSE,0.00,SYS-RETAINED-EARNINGS
4000,REVENUE,Revenue,,,,,,,,0.00,
4100,Sales Revenue,Revenue,Sales,Taxable,TRUE,4000,OPERATING_REVENUE,FALSE,FALSE,0.00,
4200,Service Revenue,Revenue,Services,Taxable,TRUE,4000,OPERATING_REVENUE,FALSE,FALSE,0.00,
5000,COST OF SALES,Expense,,,,,,,,0.00,
5100,Cost of Goods Sold,Expense,Cost of Sales,Taxable,TRUE,5000,COST_OF_SALES,FALSE,FALSE,0.00,
6000,OPERATING EXPENSES,Expense,,,,,,,,0.00,
6100,Salaries & Wages,Expense,Operating Expenses,Non-Taxable,FALSE,6000,SALARIES,FALSE,FALSE,0.00,
6110,Rent Expense,Expense,Operating Expenses,Taxable,TRUE,6000,RENT,FALSE,FALSE,0.00,
6120,Utilities Expense,Expense,Operating Expenses,Taxable,TRUE,6000,UTILITIES,FALSE,FALSE,0.00,
7000,OTHER INCOME,Revenue,,,,,,,,0.00,
7100,Interest Income,Revenue,Other Income,Taxable,FALSE,7000,INTEREST_INCOME,FALSE,FALSE,0.00,
8000,OTHER EXPENSES,Expense,,,,,,,,0.00,
8100,Bank Charges,Expense,Other Expenses,Non-Taxable,FALSE,8000,BANK_CHARGES,FALSE,FALSE,0.00,
"""

```

# data/chart_of_accounts/retail_template.csv
```csv
# File: data/chart_of_accounts/retail_template.csv
# (Content as provided before, verified with new Account fields)
"""Code,Name,AccountType,SubType,TaxTreatment,GSTApplicable,ParentCode,ReportGroup,IsControlAccount,IsBankAccount,OpeningBalance,OpeningBalanceDate
1135,Inventory - Retail Goods,Asset,Inventory,Non-Taxable,FALSE,1130,INVENTORY_RETAIL,TRUE,FALSE,5000.00,2023-01-01
4110,Sales Returns & Allowances,Revenue,Sales Adjustments,Taxable,TRUE,4000,REVENUE_ADJUSTMENTS,FALSE,FALSE,0.00,
4120,Sales Discounts,Revenue,Sales Adjustments,Taxable,TRUE,4000,REVENUE_ADJUSTMENTS,FALSE,FALSE,0.00,
5110,Purchase Returns & Allowances,Expense,Cost of Sales Adjustments,Taxable,TRUE,5100,COGS_ADJUSTMENTS,FALSE,FALSE,0.00,
5120,Purchase Discounts,Expense,Cost of Sales Adjustments,Taxable,TRUE,5100,COGS_ADJUSTMENTS,FALSE,FALSE,0.00,
6200,Shop Supplies Expense,Expense,Operating Expenses,Taxable,TRUE,6000,SHOP_SUPPLIES,FALSE,FALSE,0.00,
"""

```

# scripts/initial_data.sql
```sql
-- File: scripts/initial_data.sql
-- ============================================================================
-- INITIAL DATA (Version 1.0.2 - Added Configuration Keys for Default Accounts)
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

-- Synchronize the sequence for core.users.id after inserting user with ID 1
-- This ensures the next user (e.g., 'admin') gets a correct auto-generated ID
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
-- This MUST come AFTER core.users ID 1 is created and base currency (SGD) is defined.
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
-- Insert default configuration values (NEW SECTION from previous fix)
-- These account codes MUST exist from chart_of_accounts CSV or be system accounts
-- ----------------------------------------------------------------------------
INSERT INTO core.configuration (config_key, config_value, description, updated_by) VALUES
('SysAcc_DefaultAR', '1120', 'Default Accounts Receivable account code', 1),
('SysAcc_DefaultSalesRevenue', '4100', 'Default Sales Revenue account code', 1),
('SysAcc_DefaultGSTOutput', 'SYS-GST-OUTPUT', 'Default GST Output Tax account code', 1),
('SysAcc_DefaultAP', '2110', 'Default Accounts Payable account code', 1),
('SysAcc_DefaultPurchaseExpense', '5100', 'Default Purchase/COGS account code', 1),
('SysAcc_DefaultGSTInput', 'SYS-GST-INPUT', 'Default GST Input Tax account code', 1)
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

-- Ensure key GL accounts from default CoA exist if not already inserted by CSV import via app (NEW SECTION from previous fix)
-- These are referenced by the core.configuration defaults
INSERT INTO accounting.accounts (code, name, account_type, sub_type, created_by, updated_by, is_active, is_control_account) VALUES
('1120', 'Accounts Receivable Control', 'Asset', 'Accounts Receivable', 1, 1, TRUE, TRUE),
('2110', 'Accounts Payable Control', 'Liability', 'Accounts Payable', 1, 1, TRUE, TRUE),
('4100', 'General Sales Revenue', 'Revenue', 'Sales', 1, 1, TRUE, FALSE),
('5100', 'General Cost of Goods Sold', 'Expense', 'Cost of Sales', 1, 1, TRUE, FALSE)
ON CONFLICT (code) DO NOTHING; -- Do nothing if they already exist (e.g. from CSV)

-- ----------------------------------------------------------------------------
-- Insert default tax codes related accounts
-- ----------------------------------------------------------------------------
INSERT INTO accounting.accounts (code, name, account_type, created_by, updated_by, is_active) VALUES
('SYS-GST-OUTPUT', 'System GST Output Tax', 'Liability', 1, 1, TRUE),
('SYS-GST-INPUT', 'System GST Input Tax', 'Asset', 1, 1, TRUE)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name, account_type = EXCLUDED.account_type, updated_by = EXCLUDED.updated_by, 
    is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;

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

-- Create an active 'admin' user for application login
INSERT INTO core.users (username, password_hash, email, full_name, is_active, require_password_change)
VALUES ('admin', crypt('password', gen_salt('bf')), 'admin@sgbookkeeper.com', 'Administrator', TRUE, TRUE)
ON CONFLICT (username) DO UPDATE SET
    password_hash = EXCLUDED.password_hash, email = EXCLUDED.email, full_name = EXCLUDED.full_name,
    is_active = EXCLUDED.is_active, require_password_change = EXCLUDED.require_password_change,
    updated_at = CURRENT_TIMESTAMP;

-- Assign 'Administrator' role to 'admin' user
WITH admin_user_id_cte AS (SELECT id FROM core.users WHERE username = 'admin'),
     admin_role_id_cte AS (SELECT id FROM core.roles WHERE name = 'Administrator')
INSERT INTO core.user_roles (user_id, role_id, created_at)
SELECT admin_user_id_cte.id, admin_role_id_cte.id, CURRENT_TIMESTAMP FROM admin_user_id_cte, admin_role_id_cte
WHERE admin_user_id_cte.id IS NOT NULL AND admin_role_id_cte.id IS NOT NULL
ON CONFLICT (user_id, role_id) DO NOTHING;

-- For all permissions, grant them to the 'Administrator' role
INSERT INTO core.role_permissions (role_id, permission_id, created_at)
SELECT r.id, p.id, CURRENT_TIMESTAMP
FROM core.roles r, core.permissions p
WHERE r.name = 'Administrator'
ON CONFLICT (role_id, permission_id) DO NOTHING;

COMMIT; 
-- End of initial data

```

# scripts/db_init.py
```py
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

# scripts/schema.sql
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

# resources/icons/banking.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M4 10h3v7H4v-7zm6.5 0h3v7h-3v-7zM2 19h20v3H2v-3zm15-9h3v7h-3v-7zm-5-9L2 6v2h20V6L12 1z"/></svg>

```

# resources/icons/vendors.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M16.5 12c1.38 0 2.5-1.12 2.5-2.5S17.88 7 16.5 7C15.12 7 14 8.12 14 9.5s1.12 2.5 2.5 2.5zM9 11c1.66 0 2.99-1.34 2.99-3S10.66 5 9 5C7.34 5 6 6.34 6 8s1.34 3 3 3zm7.5 3c-1.83 0-5.5.92-5.5 2.75V19h11v-2.25c0-1.83-3.67-2.75-5.5-2.75zM9 13c-2.33 0-7 1.17-7 3.5V19h7v-2.5c0-.85.33-2.34 2.37-3.47C10.5 13.1 9.66 13 9 13z"/></svg>

```

# resources/icons/deactivate.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.59-13L12 10.59 8.41 7 7 8.41 10.59 12 7 15.59 8.41 17 12 13.41 15.59 17 17 15.59 13.41 12 17 8.41z"/>
</svg>

```

# resources/icons/product.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm-1 14H5c-.55 0-1-.45-1-1V7c0-.55.45-1 1-1h14c.55 0 1 .45 1 1v10c0 .55-.45 1-1 1z"/>
  <path d="M8 10h2v2H8zm0 4h2v2H8zm4-4h2v2h-2zm0 4h2v2h-2z"/>
</svg>

```

# resources/icons/post.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>

```

# resources/icons/collapse_all.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M12 18.17L8.83 15l-1.41 1.41L12 21l4.59-4.59L15.17 15 12 18.17zm0-12.34L15.17 9l1.41-1.41L12 3 7.41 7.59 8.83 9 12 5.83zM19 11h-2v2h2v-2zm-12 0H5v2h2v-2z"/>
  <path d="M0 0h24v24H0z" fill="none"/>
</svg>

```

# resources/icons/restore.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M13 3a9 9 0 0 0-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0 0 13 21a9 9 0 0 0 0-18zm-1 5v5l4.25 2.52.77-1.28-3.52-2.09V8H12z"/></svg>

```

# resources/icons/refresh.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
</svg>

```

# resources/icons/exit.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M10.09 15.59L11.5 17l5-5-5-5-1.41 1.41L12.67 11H3v2h9.67l-2.58 2.59zM19 3H5c-1.11 0-2 .9-2 2v4h2V5h14v14H5v-4H3v4c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"/></svg>

```

# resources/icons/about.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-5h2v-2h-2v2zm0-4h2V7h-2v4z"/></svg>

```

# resources/icons/settings.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69.98l-2.49-1c-.23-.08-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.23.08.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z"/></svg>

```

# resources/icons/accounting.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M4 10h16v2H4v-2zm0 4h16v2H4v-2zm0-8h16v2H4V6zm0 12h10v2H4v-2zM16 18h4v2h-4v-2z"/></svg>

```

# resources/icons/reports.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>

```

# resources/icons/new_company.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/></svg>

```

# resources/icons/remove.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19 13H5v-2h14v2z"/></svg>

```

# resources/icons/preferences.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69.98l-2.49-1c-.23-.08-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.23.08.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z"/></svg>

```

# resources/icons/transactions.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2zM4 18V8h2v10H4zm4 0V8h8v10H8zm12 0h-2V8h2v10z"/>
  <path d="M0 0h24v24H0V0z" fill="none"/>
</svg>

```

# resources/icons/customers.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>

```

# resources/icons/backup.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/></svg>

```

# resources/icons/filter.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M10 18h4v-2h-4v2zM3 6v2h18V6H3zm3 7h12v-2H6v2z"/>
</svg>

```

# resources/icons/help.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/></svg>

```

# resources/icons/view.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>

```

# resources/icons/add.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>

```

# resources/icons/reverse.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C20.36 11.36 16.79 8 12.5 8z"/></svg>

```

# resources/icons/expand_all.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M12 5.83L15.17 9l1.41-1.41L12 3 7.41 7.59 8.83 9 12 5.83zm0 12.34L8.83 15l-1.41 1.41L12 21l4.59-4.59L15.17 15 12 18.17zM5 13h2v-2H5v2zm12 0h2v-2h-2v2z"/>
  <path d="M0 0h24v24H0z" fill="none"/>
</svg>

```

# resources/icons/open_company.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V6h5.17l2 2H20v10z"/></svg>

```

# resources/icons/edit.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
  <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
</svg>

```

# resources/icons/dashboard.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect>
</svg>

```

# resources/resources.qrc
```qrc
<!DOCTYPE RCC><RCC version="1.0"> 
<qresource prefix="/">
    <file alias="icons/dashboard.svg">icons/dashboard.svg</file>
    <file alias="icons/accounting.svg">icons/accounting.svg</file>
    <file alias="icons/customers.svg">icons/customers.svg</file>
    <file alias="icons/vendors.svg">icons/vendors.svg</file>
    <file alias="icons/product.svg">icons/product.svg</file> <!-- New Icon -->
    <file alias="icons/banking.svg">icons/banking.svg</file>
    <file alias="icons/reports.svg">icons/reports.svg</file>
    <file alias="icons/settings.svg">icons/settings.svg</file>
    <file alias="icons/new_company.svg">icons/new_company.svg</file>
    <file alias="icons/open_company.svg">icons/open_company.svg</file>
    <file alias="icons/backup.svg">icons/backup.svg</file>
    <file alias="icons/restore.svg">icons/restore.svg</file>
    <file alias="icons/exit.svg">icons/exit.svg</file>
    <file alias="icons/preferences.svg">icons/preferences.svg</file>
    <file alias="icons/help.svg">icons/help.svg</file>
    <file alias="icons/about.svg">icons/about.svg</file>
    <file alias="icons/filter.svg">icons/filter.svg</file>
    <file alias="icons/expand_all.svg">icons/expand_all.svg</file>
    <file alias="icons/collapse_all.svg">icons/collapse_all.svg</file>
    <file alias="icons/refresh.svg">icons/refresh.svg</file>
    <file alias="icons/edit.svg">icons/edit.svg</file>
    <file alias="icons/transactions.svg">icons/transactions.svg</file>
    <file alias="icons/deactivate.svg">icons/deactivate.svg</file>
    <file alias="icons/add.svg">icons/add.svg</file>
    <file alias="icons/remove.svg">icons/remove.svg</file>
    <file alias="icons/view.svg">icons/view.svg</file>
    <file alias="icons/post.svg">icons/post.svg</file>
    <file alias="icons/reverse.svg">icons/reverse.svg</file>
    <file alias="images/splash.png">images/splash.png</file>
</qresource>
</RCC>

```

# tests/integration/__init__.py
```py

```

# tests/integration/test_example_integration.py
```py

```

# tests/__init__.py
```py

```

# tests/ui/__init__.py
```py

```

# tests/ui/test_example_ui.py
```py

```

# tests/conftest.py
```py

```

# tests/unit/__init__.py
```py

```

# tests/unit/test_example_unit.py
```py

```

