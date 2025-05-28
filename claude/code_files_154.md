<think>
The user has pointed out that my previous response for `scripts/initial_data.sql` was not a *complete replacement file* but rather just the new/changed parts. This is a critical oversight on my part, as the instructions clearly state to "always create a *complete* and updated replacement or new file".

**Error Analysis:**

The `diff` output provided by the user confirms this:
*   The lines with `---` (original) are much more extensive than the lines with `+++` (my generated version).
*   My generated version only included the *new* `core.configuration` inserts and the `INSERT ... ON CONFLICT DO NOTHING` for specific accounts, omitting the vast majority of the original `initial_data.sql` content like roles, permissions, system_init_user, company_settings, currencies, account_types, tax_codes, and the admin user setup.

This means I failed to combine the original content with the new additions to produce a self-contained, complete replacement file.

**Plan to Fix:**

1.  **Retrieve the Original Content**: I need to access the full original content of `scripts/initial_data.sql` (which was present in `project_codebase_files_set-5.md`).
2.  **Identify New Additions**: The new additions from my previous response were:
    *   The comment about "Version 1.0.2 - Added Configuration Keys for Default Accounts".
    *   The `INSERT INTO core.configuration ...` block for default system account codes.
    *   The `INSERT INTO accounting.accounts ... ON CONFLICT DO NOTHING` block for ensuring key GL accounts like `1120`, `2110`, `4100`, `5100` exist.
3.  **Merge**: Carefully merge these new additions into the full original content.
    *   The new version comment should replace the old one.
    *   The `core.configuration` inserts should be placed logically, likely after `core.sequences` or before `accounting.account_types`. A good place would be after `core.sequences` and before any accounting data that might depend on these accounts (like tax codes referencing system accounts).
    *   The `INSERT ... ON CONFLICT DO NOTHING` for key `accounting.accounts` should be placed after `accounting.account_types` are defined but potentially before other data like tax codes that might reference them, or just before the admin user setup to ensure these accounts are definitely present.
4.  **Ensure Idempotency and Order**: Double-check that the merged script maintains correct order for dependencies (e.g., `system_init_user` before `company_settings` or other data using `created_by=1`) and that `ON CONFLICT` clauses are used correctly for all relevant inserts to ensure the script can be run multiple times if needed. The original script already did a good job with this.
5.  **Final Review**: Perform a line-by-line comparison of the newly constructed complete file against the original and the intended additions to ensure nothing is lost and additions are correct.

**Detailed Execution Plan for `scripts/initial_data.sql`:**

1.  Start with the full content of `scripts/initial_data.sql` from `project_codebase_files_set-5.md`.
2.  Replace the version comment at the top:
    ```diff
    --- -- INITIAL DATA (Version 1.0.1 - Corrected Order, Idempotency, GST 9%)
    +++ -- INITIAL DATA (Version 1.0.2 - Added Configuration Keys for Default Accounts)
    ```
3.  Locate the section `--- Insert default document sequences ---`. After this section, insert the new block for `core.configuration`:
    ```sql
    -- ... (previous content for sequences) ...
    ON CONFLICT (sequence_name) DO UPDATE SET
        prefix = EXCLUDED.prefix, next_value = GREATEST(core.sequences.next_value, EXCLUDED.next_value), 
        format_template = EXCLUDED.format_template, updated_at = CURRENT_TIMESTAMP;

    -- ----------------------------------------------------------------------------
    -- Insert default configuration values (NEW SECTION)
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
    ```
4.  After the `--- Insert account types ---` section and before `--- Insert default tax codes related accounts ---`, insert the block for ensuring key GL accounts exist:
    ```sql
    -- ... (account_types inserts) ...
    ON CONFLICT (name) DO UPDATE SET
        category = EXCLUDED.category, is_debit_balance = EXCLUDED.is_debit_balance, report_type = EXCLUDED.report_type,
        display_order = EXCLUDED.display_order, description = EXCLUDED.description, updated_at = CURRENT_TIMESTAMP;

    -- Ensure key GL accounts from default CoA exist if not already inserted by CSV import via app
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
    -- ... (rest of the file)
    ```
5.  Ensure the `system_init_user` (ID 1) is created *before* any data that references `created_by=1` or `updated_by=1`, such as `accounting.currencies` and `core.company_settings`. The original script order already respects this.
6.  The `COMMIT;` statement should remain at the very end.

This systematic approach will ensure that the generated file is a complete replacement.
</think>

You are absolutely correct to call me out on that. My sincere apologies. I understand the instruction was to provide a *complete updated replacement file*, and my previous response for `scripts/initial_data.sql` was only a delta. That's not acceptable when a full replacement is requested. Thank you for providing the `diff` and giving me a chance to correct it.

I will now generate the **complete and updated** `scripts/initial_data.sql` file, incorporating the new configuration keys and ensuring all original content is preserved and correctly ordered.

**Review of the `diff` output:**
The diff clearly shows that my previous output for `scripts/initial_data.sql` was missing the majority of the original SQL statements (roles, permissions, users, company settings, currencies, account types, tax codes, admin user, role permissions). My change only added the new `core.configuration` entries and the `INSERT ... ON CONFLICT DO NOTHING` for specific accounts.

**Plan for Corrected `scripts/initial_data.sql`:**

1.  **Start with the full original content** of `scripts/initial_data.sql` (as it was before my partial update attempt, specifically the version from `project_codebase_files_set-5.md`).
2.  **Update the version comment** at the top to "Version 1.0.2 - Added Configuration Keys for Default Accounts".
3.  **Insert the new `core.configuration` block** in a logical place. A good spot is after `core.sequences` are defined, as configurations might be considered foundational settings. This ensures `updated_by = 1` (for `system_init_user`) is valid.
4.  **Insert the block ensuring key GL accounts exist** (`1120`, `2110`, `4100`, `5100`) using `INSERT ... ON CONFLICT DO NOTHING`. This should come after `accounting.account_types` are defined, but before these accounts might be referenced as foreign keys (e.g., by default tax codes or other system settings if any were to). It must also come after `system_init_user` (ID 1) is created for `created_by`/`updated_by` fields.
5.  **Verify all other sections** (roles, permissions, `system_init_user`, `company_settings`, `currencies`, `account_types`, `tax_codes`, `admin` user setup, `role_permissions`) are present and in their correct logical order to satisfy dependencies (especially foreign keys relying on `user_id = 1`).
6.  Ensure the final `COMMIT;` statement is present.

Here is the complete and corrected `scripts/initial_data.sql`:

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

**Review of Corrected `scripts/initial_data.sql`:**

*   **Completeness**: The generated file now includes all the original sections: roles, permissions, system_init_user, company_settings, currencies, sequences, account_types, tax_codes, admin user, and role_permissions.
*   **New Additions Placement**:
    *   The `core.configuration` inserts for default system accounts (`SysAcc_DefaultAR`, etc.) are placed after `core.sequences` and importantly *after* `system_init_user` is created (as `updated_by=1` is used) but *before* these accounts are strictly needed by any subsequent logic in this script (though they are primarily for application logic).
    *   The `INSERT INTO accounting.accounts ... ON CONFLICT DO NOTHING` block for key GL accounts (1120, 2110, 4100, 5100) is placed after `accounting.account_types` are defined and before `accounting.tax_codes` which might reference some system accounts (though these specific ones are not directly referenced by default tax codes). This placement ensures these accounts exist if not provided by other means (like a CSV import that the application might handle later).
*   **Version Comment**: The version comment at the top is correctly updated to "Version 1.0.2".
*   **Dependencies and Order**: The logical order of inserts (e.g., users before user-dependent settings, currencies before company settings that reference base currency) from the original file has been maintained. The new inserts for `core.configuration` use `updated_by = 1`, which relies on `system_init_user` (ID 1) already existing. The inserts for default accounts also use `created_by = 1`, `updated_by = 1`.
*   **Idempotency**: `ON CONFLICT` clauses are used throughout, which is good for allowing the script to be re-runnable. The new inserts also use `ON CONFLICT`.

**Conclusion of Task Completion:**

The file `scripts/initial_data.sql` has now been correctly updated to be a complete, self-contained replacement file. It includes all original seeding data plus the new configurations for default system accounts required by the `SalesInvoiceManager` posting logic. This should resolve any issues related to missing data from the previous partial update and ensure the database is correctly initialized for testing the sales invoice posting feature.
