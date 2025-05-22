Okay, I will continue with the plan.

```sql
-- File: scripts/initial_data.sql
-- Basic initial data for the application to function.
-- This should be idempotent or checked for existence if run multiple times.

-- Core Schema Data
-- Default User (password: "password") - HASH THIS PROPERLY IN A REAL SCENARIO
-- For bcrypt, the hash includes the salt. $2b$12$.....................................................
-- Example hash for "password" (DO NOT USE THIS IN PRODUCTION):
-- $2b$12$DbmQO3qO3.xpLdf96nU6QOUHCw8F77sQZTN7q692xhoGf0A5bH9nC
INSERT INTO core.users (username, password_hash, email, full_name, is_active)
VALUES ('admin', '$2b$12$DbmQO3qO3.xpLdf96nU6QOUHCw8F77sQZTN7q692xhoGf0A5bH9nC', 'admin@sgbookkeeper.com', 'Administrator', TRUE)
ON CONFLICT (username) DO NOTHING;

INSERT INTO core.roles (name, description)
VALUES ('Administrator', 'Full system access'),
       ('Accountant', 'Access to accounting and financial data management'),
       ('Bookkeeper', 'Access to transaction entry and basic reporting'),
       ('Viewer', 'Read-only access to reports')
ON CONFLICT (name) DO NOTHING;

-- Assign Administrator role to admin user
WITH admin_user AS (SELECT id FROM core.users WHERE username = 'admin'),
     admin_role AS (SELECT id FROM core.roles WHERE name = 'Administrator')
INSERT INTO core.user_roles (user_id, role_id)
SELECT admin_user.id, admin_role.id FROM admin_user, admin_role
ON CONFLICT (user_id, role_id) DO NOTHING;

-- Basic Permissions (examples, expand as needed per PRD 4.6.1)
INSERT INTO core.permissions (code, description, module)
VALUES
    ('settings.company.edit', 'Edit company settings', 'core'),
    ('users.manage', 'Manage users and roles', 'core'),
    ('accounts.manage', 'Manage chart of accounts', 'accounting'),
    ('journal.create', 'Create journal entries', 'accounting'),
    ('journal.post', 'Post journal entries', 'accounting'),
    ('reports.view.financial', 'View financial reports', 'reporting'),
    ('tax.gst.manage', 'Manage GST returns', 'tax')
ON CONFLICT (code) DO NOTHING;

-- Assign all permissions to Administrator role (example)
WITH admin_role AS (SELECT id FROM core.roles WHERE name = 'Administrator')
INSERT INTO core.role_permissions (role_id, permission_id)
SELECT admin_role.id, p.id FROM admin_role, core.permissions p
ON CONFLICT (role_id, permission_id) DO NOTHING;


-- Default Company Settings (ID 1 will be used by CompanySettingsService)
INSERT INTO core.company_settings (id, company_name, uen_no, gst_registration_no, fiscal_year_start_month, fiscal_year_start_day, base_currency)
VALUES (1, 'My Small Business Pte Ltd', '202300001A', 'M90000001A', 1, 1, 'SGD')
ON CONFLICT (id) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    uen_no = EXCLUDED.uen_no,
    gst_registration_no = EXCLUDED.gst_registration_no;

-- Accounting Schema Data
-- Default Currencies
INSERT INTO accounting.currencies (code, name, symbol, decimal_places, is_active)
VALUES ('SGD', 'Singapore Dollar', 'S$', 2, TRUE),
       ('USD', 'United States Dollar', '$', 2, TRUE),
       ('EUR', 'Euro', '€', 2, TRUE)
ON CONFLICT (code) DO NOTHING;

-- Default Account Types (as per PRD example structure, can be loaded from a file)
INSERT INTO accounting.account_types (name, category, is_debit_balance, display_order, description)
VALUES
    ('Cash and Cash Equivalents', 'Asset', TRUE, 10, 'Bank accounts, petty cash'),
    ('Accounts Receivable', 'Asset', TRUE, 20, 'Money owed by customers'),
    ('Inventory', 'Asset', TRUE, 30, 'Goods held for sale'),
    ('Fixed Assets', 'Asset', TRUE, 40, 'Long-term assets like equipment, property'),
    ('Accounts Payable', 'Liability', FALSE, 110, 'Money owed to suppliers'),
    ('GST Payable', 'Liability', FALSE, 120, 'GST owed to IRAS'),
    ('Loans Payable', 'Liability', FALSE, 130, 'Borrowed funds'),
    ('Owner''s Equity', 'Equity', FALSE, 210, 'Owner''s stake in the company'),
    ('Retained Earnings', 'Equity', FALSE, 220, 'Accumulated profits/losses'),
    ('Sales Revenue', 'Revenue', FALSE, 310, 'Income from sales of goods/services'),
    ('Service Revenue', 'Revenue', FALSE, 320, 'Income from services rendered'),
    ('Cost of Goods Sold', 'Expense', TRUE, 410, 'Direct costs of producing goods sold'),
    ('Operating Expenses', 'Expense', TRUE, 420, 'Day-to-day business running costs (rent, salaries, etc.)'),
    ('Interest Expense', 'Expense', TRUE, 430, 'Cost of borrowed funds')
ON CONFLICT (name) DO NOTHING;

-- Default Tax Codes (examples based on Singapore context)
-- Assuming admin user (ID 1) for created_by, updated_by
INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_active, created_by, updated_by, affects_account_id)
SELECT 'SR', 'Standard-Rated Supplies (Output Tax)', 'GST', 7.00, TRUE, u.id, u.id, gst_payable.id
FROM core.users u, accounting.accounts gst_payable
WHERE u.username = 'admin' AND gst_payable.code = 'GST-PAYABLE-ACC' -- Placeholder, link to actual GST payable account
ON CONFLICT (code) DO NOTHING;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_active, created_by, updated_by, affects_account_id)
SELECT 'ZR', 'Zero-Rated Supplies', 'GST', 0.00, TRUE, u.id, u.id, NULL
FROM core.users u WHERE u.username = 'admin'
ON CONFLICT (code) DO NOTHING;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_active, created_by, updated_by, affects_account_id)
SELECT 'ES', 'Exempt Supplies', 'GST', 0.00, TRUE, u.id, u.id, NULL
FROM core.users u WHERE u.username = 'admin'
ON CONFLICT (code) DO NOTHING;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_active, created_by, updated_by, affects_account_id)
SELECT 'TX', 'Taxable Purchases (Input Tax)', 'GST', 7.00, TRUE, u.id, u.id, gst_receivable.id -- Placeholder, link to actual GST input/receivable account
FROM core.users u, accounting.accounts gst_receivable
WHERE u.username = 'admin' AND gst_receivable.code = 'GST-INPUT-ACC'
ON CONFLICT (code) DO NOTHING;

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_active, created_by, updated_by, affects_account_id)
SELECT 'BL', 'Blocked Input Tax', 'GST', 7.00, TRUE, u.id, u.id, NULL -- For purchases where GST cannot be claimed
FROM core.users u WHERE u.username = 'admin'
ON CONFLICT (code) DO NOTHING;

-- Note: Initial Chart of Accounts (COA) is often complex and company-specific.
-- It's better loaded from a template file (CSV/JSON) by the application logic
-- or provided through a setup wizard.
-- Adding a few essential system accounts manually here:
-- These created_by/updated_by values need a valid user ID (e.g., admin user ID)
-- Let's assume admin user has ID 1 for this script.
-- Ensure these accounts are created if Tax Codes reference them.
INSERT INTO accounting.accounts (code, name, account_type, sub_type, is_active, created_by, updated_by, gst_applicable, tax_treatment)
VALUES
    ('RETAINED-EARNINGS', 'Retained Earnings', 'Equity', 'Retained Earnings', TRUE, 1, 1, FALSE, NULL),
    ('GST-PAYABLE-ACC', 'GST Payable', 'Liability', 'Current Liability', TRUE, 1, 1, FALSE, NULL),
    ('GST-INPUT-ACC', 'GST Input Tax (Claimable)', 'Asset', 'Current Asset', TRUE, 1, 1, FALSE, NULL),
    ('BANK-MAIN', 'Main Bank Account SGD', 'Asset', 'Cash and Cash Equivalents', TRUE, 1, 1, FALSE, NULL)
ON CONFLICT (code) DO NOTHING;

-- Default Fiscal Period (e.g., current year, if not set up by user)
-- This is highly dependent on application logic for creating these.
-- Example: Create an open fiscal period for the current calendar year if none exists.
-- This might be better handled by the application on first run based on CompanySettings.
-- For now, this is commented out. The app should guide user to create fiscal periods.
/*
INSERT INTO accounting.fiscal_periods (name, start_date, end_date, period_type, status, created_by, updated_by)
SELECT
    'FY' || EXTRACT(YEAR FROM CURRENT_DATE),
    DATE_TRUNC('year', CURRENT_DATE),
    (DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year' - INTERVAL '1 day')::DATE,
    'Year',
    'Open',
    (SELECT id FROM core.users WHERE username = 'admin'),
    (SELECT id FROM core.users WHERE username = 'admin')
WHERE NOT EXISTS (SELECT 1 FROM accounting.fiscal_periods WHERE period_type = 'Year' AND EXTRACT(YEAR FROM start_date) = EXTRACT(YEAR FROM CURRENT_DATE));
*/

-- Business Schema (Example Data)
-- Products/Services (examples)
INSERT INTO business.products (product_code, name, product_type, sales_price, purchase_price, is_active, created_by, updated_by)
VALUES
    ('SVC-CONSULT', 'Consulting Services', 'Service', 150.00, 0.00, TRUE, 1, 1),
    ('PROD-WIDGET', 'Standard Widget', 'Inventory', 25.00, 10.00, TRUE, 1, 1)
ON CONFLICT (product_code) DO NOTHING;


-- Note on `created_by`, `updated_by`:
-- These should reference `core.users.id`.
-- The INSERT statements above use literal `1` assuming an admin user with ID 1 exists.
-- In a production script, you'd use subqueries like `(SELECT id FROM core.users WHERE username = 'admin')`.
-- Or, ensure the admin user is created first with a known ID if possible, or handle this in app logic.
-- FK constraints for these audit fields to core.users can be added to the schema for integrity.

COMMIT;
```

Next, `resources/` directory and files.

```python
# File: resources/resources.qrc
# Qt Resource file
# Create dummy SVG files for icons, and a dummy PNG for splash for this to work.
# The paths are relative to where this .qrc file is.
# In this structure, resources/icons/ and resources/images/

# RCC (Resource Compiler) will be needed to compile this into a Python file (e.g., resources_rc.py)
# Command: pyside6-rcc resources.qrc -o resources_rc.py (or pyrcc5 for PyQt5)
# And then import resources_rc in the main application.

# <RCC>
#   <qresource prefix="/icons">
#     <file alias="dashboard.svg">icons/dashboard.svg</file>
#     <file alias="accounting.svg">icons/accounting.svg</file>
#     <file alias="customers.svg">icons/customers.svg</file>
#     <file alias="vendors.svg">icons/vendors.svg</file>
#     <file alias="banking.svg">icons/banking.svg</file>
#     <file alias="reports.svg">icons/reports.svg</file>
#     <file alias="settings.svg">icons/settings.svg</file>
#     <file alias="new_company.svg">icons/new_company.svg</file>
#     <file alias="open_company.svg">icons/open_company.svg</file>
#     <file alias="backup.svg">icons/backup.svg</file>
#     <file alias="restore.svg">icons/restore.svg</file>
#     <file alias="exit.svg">icons/exit.svg</file>
#     <file alias="preferences.svg">icons/preferences.svg</file>
#     <file alias="help.svg">icons/help.svg</file>
#     <file alias="about.svg">icons/about.svg</file>
#     <file alias="filter.svg">icons/filter.svg</file>
#     <file alias="expand_all.svg">icons/expand_all.svg</file>
#     <file alias="collapse_all.svg">icons/collapse_all.svg</file>
#     <file alias="refresh.svg">icons/refresh.svg</file>
#     <file alias="edit.svg">icons/edit.svg</file>
#     <file alias="transactions.svg">icons/transactions.svg</file>
#     <file alias="deactivate.svg">icons/deactivate.svg</file>
#     <!-- Add other icons as needed -->
#   </qresource>
#   <qresource prefix="/images">
#     <file alias="splash.png">images/splash.png</file>
#     <!-- Add other images as needed -->
#   </qresource>
#   <qresource prefix="/styles">
#     <!-- <file alias="default.qss">styles/default.qss</file> -->
#   </qresource>
# </RCC>

# For the purpose of this generation, I will create a simpler version of resources.qrc
# that assumes icons are directly in resources/icons, etc.
# And the actual SVG/PNG files must be created by the user.
# The paths used in the Python code are direct file paths for now, e.g. "resources/icons/dashboard.svg"
# If using QRC, these paths would become ":/icons/dashboard.svg" after compiling and importing the _rc.py file.

# Actual content of resources.qrc if used:
"""
<RCC>
  <qresource prefix="/">
    <file>icons/dashboard.svg</file>
    <file>icons/accounting.svg</file>
    <file>icons/customers.svg</file>
    <file>icons/vendors.svg</file>
    <file>icons/banking.svg</file>
    <file>icons/reports.svg</file>
    <file>icons/settings.svg</file>
    <file>icons/new_company.svg</file>
    <file>icons/open_company.svg</file>
    <file>icons/backup.svg</file>
    <file>icons/restore.svg</file>
    <file>icons/exit.svg</file>
    <file>icons/preferences.svg</file>
    <file>icons/help.svg</file>
    <file>icons/about.svg</file>
    <file>icons/filter.svg</file>
    <file>icons/expand_all.svg</file>
    <file>icons/collapse_all.svg</file>
    <file>icons/refresh.svg</file>
    <file>icons/edit.svg</file>
    <file>icons/transactions.svg</file>
    <file>icons/deactivate.svg</file>
    <file>images/splash.png</file>
  </qresource>
</RCC>
"""
# The python code currently uses direct paths "resources/icons/..."
# If QRC is to be used, the python code needs to change paths to ":/icons/..." AND
# a `resources_rc.py` file (generated by pyside6-rcc) must be imported in `app/main.py`.
# For this exercise, I will assume direct paths are used and QRC is optional for user to implement.
# So, just provide the QRC content as a string comment.

# Create dummy icon files (user needs to replace these with actual SVGs)
# I will list the files to be created. The content will be minimal valid SVG.
# Example for one: resources/icons/dashboard.svg
"""
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
  <rect width="16" height="16" fill="gray"/>
  <text x="8" y="12" font-size="8" fill="white" text-anchor="middle">D</text>
</svg>
"""
# ... and similarly for all other icons mentioned in QRC.
# Create dummy splash: resources/images/splash.png (user needs to replace)
# A small 1x1 transparent PNG for placeholder.
# (Base64 for 1x1 transparent PNG: iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=)
```

```python
# File: resources/icons/dashboard.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>"""
```
```python
# File: resources/icons/accounting.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>"""
```
```python
# File: resources/icons/customers.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>"""
```
```python
# File: resources/icons/vendors.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>"""
```
```python
# File: resources/icons/banking.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="10" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path><circle cx="12" cy="16" r="1"></circle></svg>"""
```
```python
# File: resources/icons/reports.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>"""
```
```python
# File: resources/icons/settings.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>"""
```
```python
# File: resources/icons/new_company.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>"""
```
```python
# File: resources/icons/open_company.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12 L20 20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h4l2 3h4a2 2 0 0 1 2 2l0 1"></path><path d="M10 12 L14 12 L12 9z"></path></svg>"""
```
```python
# File: resources/icons/backup.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>"""
```
```python
# File: resources/icons/restore.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>"""
```
```python
# File: resources/icons/exit.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>"""
```
```python
# File: resources/icons/preferences.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 0 2l-.15.1a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.38a2 2 0 0 0-.73-2.73l-.15-.1a2 2 0 0 1 0-2l.15-.1a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path><circle cx="12" cy="12" r="3"></circle></svg>"""
```
```python
# File: resources/icons/help.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>"""
```
```python
# File: resources/icons/about.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>"""
```
```python
# File: resources/icons/filter.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>"""
```
```python
# File: resources/icons/expand_all.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>"""
```
```python
# File: resources/icons/collapse_all.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14h6v6M20 10h-6V4M14 10l7-7M3 21l7-7"/></svg>"""
```
```python
# File: resources/icons/refresh.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>"""
```
```python
# File: resources/icons/edit.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>"""
```
```python
# File: resources/icons/transactions.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="9" y1="15" x2="15" y2="15"></line><line x1="9" y1="18" x2="15" y2="18"></line></svg>"""
```
```python
# File: resources/icons/deactivate.svg
"""<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>"""
```

```python
# File: resources/images/splash.png
# This is a binary file. For this text-based generation, I'll put a base64 encoded 1x1 transparent PNG.
# User should replace this with their actual splash image (e.g., 600x400 PNG).
# Content (base64 for 1x1 transparent PNG):
# iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=
# When creating the actual file, decode this base64. For the purpose of this output, I'll just note it.
# In a real file system, this would be a binary PNG.
# If this was a script generating files, it would be:
# import base64
# png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
# with open("resources/images/splash.png", "wb") as f:
#    f.write(png_data)
# For this output, I'll just mark it as a placeholder.
# Placeholder comment: Binary PNG file content for resources/images/splash.png
```

```python
# File: data/chart_of_accounts/general_template.csv
# Example CSV structure for COA template
# Code,Name,AccountType,SubType,TaxTreatment,GSTApplicable,ParentCode
# AccountType must match values in AccountCategory enum (Asset, Liability, etc.)
"""Code,Name,AccountType,SubType,TaxTreatment,GSTApplicable,ParentCode
1000,ASSETS,Asset,,,,
1100,Current Assets,Asset,,,,1000
1110,Cash and Bank,Asset,Cash and Cash Equivalents,,,1100
1111,Main Bank Account SGD,Asset,Cash and Cash Equivalents,Non-Taxable,FALSE,1110
1120,Accounts Receivable,Asset,Accounts Receivable,,,1100
1200,Non-Current Assets,Asset,,,,1000
1210,Property, Plant & Equipment,Asset,Fixed Assets,,,1200
2000,LIABILITIES,Liability,,,,
2100,Current Liabilities,Liability,,,,,2000
2110,Accounts Payable,Liability,Accounts Payable,,,2100
2120,GST Payable,Liability,GST Payable,Taxable,TRUE,2100
3000,EQUITY,Equity,,,,
3100,Owner's Equity,Equity,Owner's Equity,,,3000
3200,Retained Earnings,Equity,Retained Earnings,,,3000
4000,REVENUE,Revenue,,,,
4100,Sales Revenue,Revenue,Sales Revenue,Taxable,TRUE,4000
5000,EXPENSES,Expense,,,,
5100,Cost of Goods Sold,Expense,Cost of Goods Sold,Taxable,TRUE,5000
5200,Operating Expenses,Expense,Operating Expenses,,,5000
5210,Rent Expense,Expense,Operating Expenses,Taxable,TRUE,5200
"""
```
```python
# File: data/chart_of_accounts/retail_template.csv
"""Code,Name,AccountType,SubType,TaxTreatment,GSTApplicable,ParentCode
# Similar to general_template.csv but with retail specific accounts
# e.g., Inventory, Sales Discounts, etc.
1130,Inventory,Asset,Inventory,,,1100
4110,Sales Discounts,Revenue,Sales Adjustments,Taxable,TRUE,4000
"""
```
```python
# File: data/report_templates/balance_sheet_default.json
# Example for a report template structure (can be more complex, e.g. XML, proprietary format)
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
```python
# File: data/tax_codes/sg_gst_codes_2023.csv
# Code,Description,TaxType,Rate,IsActive,AffectsAccountCode
# TaxType must match TaxType enum (GST, Income Tax, Withholding Tax)
# AffectsAccountCode is the COA code for the tax account (e.g., GST Payable)
"""Code,Description,TaxType,Rate,IsActive,AffectsAccountCode
SR,Standard-Rated Supplies,GST,7.00,TRUE,GST-PAYABLE-ACC
ZR,Zero-Rated Supplies,GST,0.00,TRUE,
ES,Exempt Supplies,GST,0.00,TRUE,
TX,Taxable Purchases (Standard-Rated),GST,7.00,TRUE,GST-INPUT-ACC
BL,Blocked Input Tax (e.g. Club Subscriptions),GST,7.00,TRUE,
OP,Out-of-Scope Supplies,GST,0.00,TRUE,
"""
```

```python
# File: docs/user_guide/index.md
"""
# SG Bookkeeper User Guide

Welcome to the SG Bookkeeper User Guide. This guide will help you get started and make the most out of the application.

## Table of Contents

1.  [Installation](installation.md)
2.  [First-Time Setup](first_time_setup.md)
3.  [Dashboard Overview](dashboard.md)
4.  [Managing Chart of Accounts](chart_of_accounts.md)
5.  [Recording Transactions](transactions.md)
6.  [Managing Customers and Vendors](customers_vendors.md)
7.  [Banking Operations](banking.md)
8.  [Generating Reports](reports.md)
9.  [GST Filing](gst_filing.md)
10. [Year-End Closing](year_end.md)
11. [Settings and Preferences](settings.md)
12. [Troubleshooting](troubleshooting.md)
"""
```
```python
# File: docs/user_guide/installation.md
"""
# Installation Guide

Follow these steps to install SG Bookkeeper on your system.

## System Requirements
- OS: Windows 10/11, macOS 12+, Ubuntu 20.04+
- CPU: 2GHz dual-core or better
- RAM: 4GB minimum, 8GB recommended
- Storage: 5GB free space + space for data
- Display: 1366x768 minimum resolution
- PostgreSQL 14+

## Steps
1. **Install PostgreSQL**: If not already installed, download and install PostgreSQL from [postgresql.org](https://www.postgresql.org/). Ensure the server is running.
2. **Download SG Bookkeeper**: Get the latest installer/package from the [Releases Page](https://github.com/yourusername/sg_bookkeeper/releases).
3. **Run Installer**:
    - **Windows**: Run the `.exe` installer.
    - **macOS**: Open the `.dmg` and drag SG Bookkeeper to your Applications folder.
    - **Linux**: 
        ```bash
        pip install sg-bookkeeper
        # or use .deb/.rpm if provided
        ```
4. **Database Initialization**: The first time you run the application, or via a command-line script, you'll need to initialize the database.
   ```bash
   # If using pip install:
   sg_bookkeeper_db_init --user your_postgres_user 
   # Or if running from source:
   python -m scripts.db_init --user your_postgres_user
   ```
   You will be prompted for your PostgreSQL password.

5. **Launch Application**: Start SG Bookkeeper from your applications menu or by running `sg_bookkeeper` in the terminal (if installed via pip).
"""
```
```python
# File: docs/developer_guide/index.md
"""
# SG Bookkeeper Developer Guide

This guide provides information for developers looking to contribute to or extend SG Bookkeeper.

## Table of Contents

1.  [Development Setup](dev_setup.md)
2.  [Project Structure](project_structure.md)
3.  [Architecture Overview](architecture.md)
4.  [Database Schema](database_schema.md)
5.  [Coding Conventions](coding_conventions.md)
6.  [Running Tests](testing.md)
7.  [Building and Packaging](building.md)
8.  [API Reference (Internal)](api_reference.md)
9.  [Contributing Guidelines](contributing.md)
"""
```
```python
# File: docs/api_reference/index.md
"""
# SG Bookkeeper API Reference (Internal)

This section documents key internal APIs, services, and managers within SG Bookkeeper.

## Core Services
-   [AccountService](account_service.md)
-   [JournalService](journal_service.md)
-   [FiscalPeriodService](fiscal_period_service.md)
-   [TaxCodeService](tax_code_service.md)

## Business Logic Managers
-   [ChartOfAccountsManager](chart_of_accounts_manager.md)
-   [JournalEntryManager](journal_entry_manager.md)
-   [GSTManager](gst_manager.md)
-   [FinancialStatementGenerator](financial_statement_generator.md)
-   [TaxCalculator](tax_calculator.md)

## UI Components
-   [MainWindow](main_window.md)
-   [ChartOfAccountsWidget](chart_of_accounts_widget.md)
"""
# Create stub files for each of these .md files listed above within their respective directories
# e.g., docs/user_guide/first_time_setup.md with "# First-Time Setup"
# For brevity, I will not list all of them.
```

```python
# File: tests/__init__.py
# (empty)
```
```python
# File: tests/unit/__init__.py
# (empty)
```
```python
# File: tests/integration/__init__.py
# (empty)
```
```python
# File: tests/ui/__init__.py
# (empty)
```

```python
# File: tests/conftest.py
# Pytest fixtures
import pytest
import asyncio
from app.core.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager
from app.core.application_core import ApplicationCore
# Import models for potential fixture use
from app.models import Base 

TEST_DB_NAME = "sg_bookkeeper_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for all test cases."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_config_manager():
    # Create a temporary config file or mock ConfigManager for tests
    # For simplicity, use the default ConfigManager but point to a test DB if possible
    # This needs careful handling to not overwrite user's actual config.
    # One way is to make ConfigManager accept a path.
    # For now, assume it might use a test-specific config or the default with test DB.
    # Let's modify ConfigManager to accept file path directly.
    # E.g. ConfigManager(config_file="test_config.ini")
    # The current ConfigManager uses hardcoded "config.ini" in user dir.
    # This is a simplification.
    cm = ConfigManager() 
    # Override DB name for tests
    cm.parser['Database']['database'] = TEST_DB_NAME 
    return cm

@pytest.fixture(scope="session")
async def test_db_manager(test_config_manager: ConfigManager):
    db_manager = DatabaseManager(test_config_manager)
    await db_manager.initialize() # Ensure it's initialized

    # Create a test database (if db_init script is not used for tests)
    # This is complex and usually handled by a separate test DB setup script.
    # For now, assume the TEST_DB_NAME database exists or is created by db_init with test flag.

    # Create tables using SQLAlchemy metadata (Alembic is better for migrations)
    # This requires all models to be imported so Base.metadata knows about them.
    # Ensure all model files are imported in app/models/__init__.py
    # For test isolation, tables should be created and dropped per session or test.
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # For specific schemas:
        # await conn.execute(text("CREATE SCHEMA IF NOT EXISTS core;"))
        # await conn.execute(text("CREATE SCHEMA IF NOT EXISTS accounting;"))
        # ... etc.
        # await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    yield db_manager

    # Teardown: drop tables or the test database
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await db_manager.close_connections()


@pytest.fixture
async def db_session(test_db_manager: DatabaseManager):
    """Provides a clean database session for each test, with transaction rollback."""
    async with test_db_manager.engine.connect() as connection:
        await connection.begin() # Start a transaction
        async_session_local = sessionmaker(
            bind=connection,
            expire_on_commit=False,
            class_=AsyncSession
        )
        async with async_session_local() as session:
            yield session
        
        await connection.rollback() # Rollback after test to keep DB clean

@pytest.fixture
def app_core_mock(test_config_manager, test_db_manager): # Not async if db_manager is session-scoped
    # For unit tests, many parts of AppCore might be mocked.
    # This provides a basic AppCore with real config and DB manager for integration tests.
    # Need to run db_manager.initialize() before AppCore uses it.
    # `test_db_manager` fixture should handle its own initialization.
    
    # A simplified AppCore for testing, or mock its dependencies.
    # core = ApplicationCore(test_config_manager, test_db_manager)
    # asyncio.run(core.startup()) # If startup is needed. Be careful with event loops in fixtures.
    # return core
    # For now, just return a basic structure
    class MockAppCore:
        def __init__(self):
            self.config_manager = test_config_manager
            self.db_manager = test_db_manager
            # Mock current_user or security_manager as needed
            self.current_user = None # type: ignore
            class MockSecurityManager:
                def get_current_user(self): return None
            self.security_manager = MockSecurityManager()

            # Mock services or initialize real ones if testing integration
            from app.services.account_service import AccountService
            self.account_service_instance = AccountService(self.db_manager, self)
        
        @property
        def accounting_service(self): # For ChartOfAccountsWidget / AccountDialog
            return self.account_service_instance

    return MockAppCore()


# Add qtbot fixture for UI tests (pytest-qt)
# It's automatically available if pytest-qt is installed.
```

```python
# File: tests/unit/test_example_unit.py
# Example unit test
import pytest
from decimal import Decimal
from app.utils.converters import to_decimal # Example utility to test

def test_to_decimal_conversion():
    assert to_decimal("123.45") == Decimal("123.45")
    assert to_decimal(100) == Decimal("100")
    assert to_decimal(Decimal("10.0")) == Decimal("10.0")
    assert to_decimal("invalid") == Decimal("0") # As per current stub impl
    assert to_decimal(None) == Decimal("0")

# Example test for a Pydantic model (if complex validation exists)
from app.utils.pydantic_models import JournalEntryLineData
def test_journal_entry_line_data_validation():
    with pytest.raises(ValueError): # Expecting a Pydantic ValidationError internally
        JournalEntryLineData(account_id=1, debit_amount=Decimal(10), credit_amount=Decimal(5))
    
    # Valid case
    data = JournalEntryLineData(account_id=1, debit_amount=Decimal(10), credit_amount=Decimal(0))
    assert data.debit_amount == Decimal(10)
```

```python
# File: tests/integration/test_example_integration.py
# Example integration test (requires database setup from conftest.py)
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Account, User
from app.services.account_service import AccountService

@pytest.mark.asyncio
async def test_create_and_get_account(db_session: AsyncSession, app_core_mock):
    # Using the AccountService via app_core_mock fixture, which uses the test_db_manager
    # Ensure user exists for created_by/updated_by or mock it for Account model
    # For simplicity, assume user_id 0 or 1 is acceptable for tests if not mocking SecurityManager fully.
    
    # If UserAuditMixin requires non-null created_by/updated_by, ensure a user exists.
    # For this test, let's assume created_by/updated_by are handled or mocked.
    mock_user_id = 1 # Simulate a logged-in user

    # Get AccountService from the mock that uses the test session
    account_service = AccountService(db_manager=app_core_mock.db_manager, app_core=app_core_mock)


    new_account_data = Account(
        code="TEST001", name="Test Account", account_type="Asset",
        created_by=mock_user_id, updated_by=mock_user_id # Fill required audit fields
    )
    
    created_account = await account_service.save(new_account_data) # save uses db_session via db_manager
    # The session from db_session fixture commits automatically if no error.
    # Or, if service uses its own session manager, ensure it's using the test DB connection.
    # The `save` method in AccountService uses `self.db_manager.session()` which should
    # use the test_db_manager configured for the test DB.
    # However, db_session fixture provides a transaction-rolled-back session.
    # For true integration tests, you might want services to accept a session.
    # Let's assume AccountService is using the global test_db_manager.

    assert created_account.id is not None
    assert created_account.code == "TEST001"

    retrieved_account = await account_service.get_by_id(created_account.id)
    assert retrieved_account is not None
    assert retrieved_account.code == "TEST001"

    retrieved_by_code = await account_service.get_by_code("TEST001")
    assert retrieved_by_code is not None
    assert retrieved_by_code.id == created_account.id
```

```python
# File: tests/ui/test_example_ui.py
# Example UI test (requires pytest-qt)
import pytest
from PySide6.QtCore import Qt
# from app.ui.main_window import MainWindow # Example
# from app.core.application_core import ApplicationCore # For MainWindow dependency

# This needs a running QApplication for UI tests. pytest-qt handles this via qtbot.
# MainWindow creation might be complex due to ApplicationCore dependencies.
# For true UI tests, ApplicationCore needs to be properly set up or mocked.

def test_main_window_title(qtbot):
    # This is a very basic example. Testing MainWindow might require
    # mocking ApplicationCore and its sub-components if they do heavy work on init.
    # For now, let's test a simpler widget if MainWindow is too complex to instantiate easily.
    from PySide6.QtWidgets import QLabel
    widget = QLabel("Hello")
    qtbot.addWidget(widget) # Track widget for cleanup
    assert widget.text() == "Hello"

    # Example for a more complex widget (if AccountDialog can be instantiated simply)
    # from app.ui.accounting.account_dialog import AccountDialog
    # from unittest.mock import MagicMock
    # mock_app_core = MagicMock() # Mock ApplicationCore for dialog
    # dialog = AccountDialog(mock_app_core)
    # qtbot.addWidget(dialog)
    # assert dialog.windowTitle() == "Add Account" # Default title
    # dialog.code_edit.setText("TESTACC")
    # assert dialog.code_edit.text() == "TESTACC"
    # qtbot.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton) # Simulate click
    # Add assertions based on dialog behavior (e.g. QMessageBox shown, or accepted/rejected)
```

```yaml
# File: .github/workflows/ci.yml
name: Python CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install Poetry
      run: |
        pip install poetry
        poetry config virtualenvs.create true --local
        poetry config virtualenvs.in-project true --local

    - name: Install dependencies
      run: |
        poetry install --no-interaction --no-root # Install deps only

    - name: Install project (for scripts etc.)
      run: |
        poetry install --no-interaction

    # Linters and formatters (optional, or use pre-commit)
    - name: Lint with Flake8
      run: |
        poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        poetry run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
    - name: Check formatting with Black
      run: |
        poetry run black . --check

    # Run tests (Needs a PostgreSQL service for integration tests)
    - name: Start PostgreSQL for testing
      run: |
        sudo systemctl start postgresql
        # Create test database and user if needed by tests
        # PGPASSWORD=test_password psql -U postgres -h localhost -c "CREATE USER test_user WITH PASSWORD 'test_password';"
        # PGPASSWORD=test_password psql -U postgres -h localhost -c "CREATE DATABASE sg_bookkeeper_test OWNER test_user;"
        # Or use a Dockerized PostgreSQL for more control:
        # services:
        #   postgres:
        #     image: postgres:14
        #     env:
        #       POSTGRES_USER: test_user
        #       POSTGRES_PASSWORD: test_password
        #       POSTGRES_DB: sg_bookkeeper_test
        #     ports:
        #       - 5432:5432
        #     options: >-
        #       --health-cmd pg_isready
        #       --health-interval 10s
        #       --health-timeout 5s
        #       --health-retries 5
    
    # The above DB setup is conceptual. GitHub Actions offers service containers.
    # Example using service container for PostgreSQL:
    # services:
    #   postgres:
    #     image: postgres:14
    #     env:
    #       POSTGRES_DB: ${{ env.DB_NAME }}
    #       POSTGRES_USER: ${{ env.DB_USER }}
    #       POSTGRES_PASSWORD: ${{ env.DB_PASSWORD }}
    #     ports:
    #       - 5432:5432 # Map container port 5432 to host port 5432
    #     options: >-
    #       --health-cmd pg_isready
    #       --health-interval 10s
    #       --health-timeout 5s
    #       --health-retries 5
    # env:
    #   DB_HOST: localhost # Because of port mapping
    #   DB_PORT: 5432
    #   DB_NAME: sg_bookkeeper_test
    #   DB_USER: testuser
    #   DB_PASSWORD: testpassword
    #   PGPASSWORD: ${{ env.DB_PASSWORD }} # For psql commands

    # Simplified test run step assuming DB is available:
    - name: Run Pytest
      env:
        # Set env vars for tests if they rely on them for DB connection
        PGHOST: localhost
        PGPORT: 5432
        PGDATABASE: sg_bookkeeper_test # Assumes this DB exists on CI runner
        PGUSER: postgres # Or a dedicated test user
        PGPASSWORD: "" # Password for postgres user on CI runner's default PG (often empty)
      run: |
        # Need to ensure the test DB exists.
        # psql -U postgres -h localhost -c "DROP DATABASE IF EXISTS sg_bookkeeper_test;" (if permissions allow)
        # psql -U postgres -h localhost -c "CREATE DATABASE sg_bookkeeper_test;"
        # Then, run db_init for the test database (or rely on conftest to create schema)
        # poetry run python -m scripts.db_init --dbname sg_bookkeeper_test --user postgres --drop-existing # Add --password if needed
        # For now, assume conftest.py handles schema creation in the test DB.
        # For UI tests, xvfb might be needed: xvfb-run poetry run pytest
        poetry run pytest --cov=app --cov-report=xml

    # Upload coverage (optional)
    # - name: Upload coverage to Codecov
    #   uses: codecov/codecov-action@v3
    #   with:
    #     token: ${{ secrets.CODECOV_TOKEN }} # If using private repo or Codecov token
    #     file: ./coverage.xml
    #     flags: unittests
    #     name: codecov-umbrella
    #     fail_ci_if_error: true
```

This completes the generation of the planned files with stubs and some implementations based on the TDS/PRD. Many parts, especially UI interaction, complex business logic, and full error handling, would require further detailed implementation. The focus here was on structure and core components as outlined.
The resource files (icons, images) are represented as comments or minimal content; actual assets would be needed.
The tests are very basic stubs and would need significant expansion.
The CI pipeline is a template and needs configuration for the PostgreSQL service to work reliably.

Final check on plan:
1.  **[X] Setup Project Root and Basic Files** (README, LICENSE, CODE_OF_CONDUCT, .gitignore, pyproject.toml)
2.  **[X] Create `app` Directory Structure** (init files)
3.  **[X] Implement `app/models/`** (All models created)
4.  **[X] Implement `app/core/`** (All core managers/classes created)
5.  **[X] Implement `app/services/` (and `app/utils/result.py`)** (Interfaces and service stubs/impls created)
6.  **[X] Implement Business Logic Managers (`app/accounting/`, `app/tax/`, `app/reporting/`)** (Key managers implemented based on TDS, stubs for others)
7.  **[X] Implement UI (`app/ui/` and `app/main.py`)** (MainWindow, main.py, and key widgets like COA, AccountDialog created, others are stubs)
8.  **[X] Implement `app/utils/` and `app/common/`** (Utilities and enums created)
9.  **[X] Create `scripts/` (including `schema.sql` and `initial_data.sql`)** (db_init.py, schema.sql, initial_data.sql created)
10. **[X] Create `resources/` (including `.qrc` file)** (Dummy icons, splash placeholder, QRC content comment)
11. **[X] Create `data/`** (Dummy CSV/JSON templates)
12. **[X] Create `docs/`** (Stub documentation structure and files)
13. **[X] Create `tests/`** (conftest.py and example unit/integration/ui test stubs)
14. **[X] Create `.github/workflows/ci.yml`** (Basic CI workflow YAML created)

All planned items are now covered.```python
# File: README.md
# Content from the provided README.md
# (This file is provided by the user, so I'll list it as created but won't regenerate its content here to save space.
# Assume it's identical to the one in the prompt.)
```

```python
# File: LICENSE
# Content from the MIT License section in README.md
MIT License

Copyright (c) 2023 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

```python
# File: CODE_OF_CONDUCT.md
# Stub content
# SG Bookkeeper Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone, regardless of age, body
size, visible or invisible disability, ethnicity, sex characteristics, gender
identity and expression, level of experience, education, socio-economic status,
nationality, personal appearance, race, religion, or sexual identity
and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming,
diverse, inclusive, and healthy community.

## Our Standards

Examples of behavior that contributes to a positive environment for our
community include:
* Demonstrating empathy and kindness toward other people
* Being respectful of differing opinions, viewpoints, and experiences
* Giving and gracefully accepting constructive feedback
* Accepting responsibility and apologizing to those affected by our mistakes,
  and learning from the experience
* Focusing on what is best not just for us as individuals, but for the
  overall community

Examples of unacceptable behavior include:
* The use of sexualized language or imagery, and sexual attention or
  advances of any kind
* Trolling, insulting or derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or email
  address, without their explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

## Enforcement Responsibilities

Community leaders are responsible for clarifying and enforcing our standards of
acceptable behavior and will take appropriate and fair corrective action in
response to any behavior that they deem inappropriate, threatening, offensive,
or harmful.

Community leaders have the right and responsibility to remove, edit, or reject
comments, commits, code, wiki edits, issues, and other contributions that are
not aligned to this Code of Conduct, and will communicate reasons for moderation
decisions when appropriate.

## Scope

This Code of Conduct applies within all community spaces, and also applies when
an individual is officially representing the community in public spaces.
Examples of representing our community include using an official e-mail address,
posting via an official social media account, or acting as an appointed
representative at an online or offline event.

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported to the community leaders responsible for enforcement at
[INSERT CONTACT METHOD].
All complaints will be reviewed and investigated promptly and fairly.

All community leaders are obligated to respect the privacy and security of the
reporter of any incident.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage],
version 2.0, available at
https://www.contributor-covenant.org/version/2/0/code_of_conduct.html.

[homepage]: https://www.contributor-covenant.org

For TrivialChanges and Clarifications: https://github.com/yourusername/sg_bookkeeper/blob/main/CODE_OF_CONDUCT.md
```

```python
# File: .gitignore
# Standard Python .gitignore
__pycache__/
*.py[cod]
*$py.class

# Build artifacts
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a script, but you might change things and
#  accidentally commit them.
*.spec
*.pyzw

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# Jupyter Notebook
.ipynb_checkpoints

# IDE / Editor specific
.idea/
.vscode/
*.swp
*~
```

```python
# File: pyproject.toml
# Based on TDS 8.1 setup.py and common Poetry setup
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
    "Development Status :: 3 - Alpha", # More realistic for a new project
    "Intended Audience :: Financial and Insurance Industry",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Topic :: Office/Business :: Financial :: Accounting",
]
packages = [{include = "app", from = "."}]

[tool.poetry.dependencies]
python = "^3.9"
PySide6 = ">=6.2.3" # TDS specified 6.2.3+
SQLAlchemy = {extras = ["asyncio"], version = ">=1.4.0"} # TDS specified 1.4+ with asyncio support
asyncpg = ">=0.25.0" # TDS specified
alembic = ">=1.7.5" # TDS specified
pydantic = ">=1.9.0" # TDS specified
reportlab = ">=3.6.6" # TDS specified
openpyxl = ">=3.0.9" # TDS specified
python-dateutil = ">=2.8.2" # TDS specified
bcrypt = ">=3.2.0" # TDS specified
# pyqtdarktheme was in TDS setup.py, but not explicitly used in UI. Optional.
# pyqtdarktheme = ">=1.1.0" 
# QtCharts is part of PySide6.QtWidgets or a separate Qt module, QScintilla is a separate C++ lib.
# Assuming QtCharts is available with PySide6. QScintilla would need specific bindings if used.

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
pytest-cov = "^4.0"
flake8 = "^6.0"
black = "^23.0"
mypy = "^1.0"
pre-commit = "^3.0"
pytest-qt = "^4.0" # For testing Qt applications
pytest-asyncio = "^0.21.0" # For testing asyncio code

[tool.poetry.scripts]
sg_bookkeeper = "app.main:main"
sg_bookkeeper_db_init = "scripts.db_init:main" # Added script for DB init

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ['py39']

[tool.pytest.ini_options]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"
```

```python
# File: app/__init__.py
# This file can be empty or used for package-level imports.
```

```python
# File: app/core/__init__.py
from .application_core import ApplicationCore
from .config_manager import ConfigManager
from .database_manager import DatabaseManager
from .module_manager import ModuleManager
from .security_manager import SecurityManager

__all__ = [
    "ApplicationCore",
    "ConfigManager",
    "DatabaseManager",
    "ModuleManager",
    "SecurityManager",
]
```

```python
# File: app/accounting/__init__.py
from .chart_of_accounts_manager import ChartOfAccountsManager
from .journal_entry_manager import JournalEntryManager
from .fiscal_period_manager import FiscalPeriodManager
from .currency_manager import CurrencyManager

__all__ = [
    "ChartOfAccountsManager",
    "JournalEntryManager",
    "FiscalPeriodManager",
    "CurrencyManager",
]
```

```python
# File: app/tax/__init__.py
from .gst_manager import GSTManager
from .tax_calculator import TaxCalculator
from .income_tax_manager import IncomeTaxManager
from .withholding_tax_manager import WithholdingTaxManager

__all__ = [
    "GSTManager",
    "TaxCalculator",
    "IncomeTaxManager",
    "WithholdingTaxManager",
]
```

```python
# File: app/reporting/__init__.py
from .financial_statement_generator import FinancialStatementGenerator
from .tax_report_generator import TaxReportGenerator
from .report_engine import ReportEngine

__all__ = [
    "FinancialStatementGenerator",
    "TaxReportGenerator",
    "ReportEngine",
]
```

```python
# File: app/ui/__init__.py
from .main_window import MainWindow

__all__ = ["MainWindow"]
```

```python
# File: app/ui/dashboard/__init__.py
from .dashboard_widget import DashboardWidget

__all__ = ["DashboardWidget"]
```

```python
# File: app/ui/accounting/__init__.py
from .accounting_widget import AccountingWidget
from .chart_of_accounts_widget import ChartOfAccountsWidget
from .account_dialog import AccountDialog

__all__ = ["AccountingWidget", "ChartOfAccountsWidget", "AccountDialog"]
```

```python
# File: app/ui/customers/__init__.py
from .customers_widget import CustomersWidget

__all__ = ["CustomersWidget"]
```

```python
# File: app/ui/vendors/__init__.py
from .vendors_widget import VendorsWidget

__all__ = ["VendorsWidget"]
```

```python
# File: app/ui/banking/__init__.py
from .banking_widget import BankingWidget

__all__ = ["BankingWidget"]
```

```python
# File: app/ui/reports/__init__.py
from .reports_widget import ReportsWidget

__all__ = ["ReportsWidget"]
```

```python
# File: app/ui/settings/__init__.py
from .settings_widget import SettingsWidget

__all__ = ["SettingsWidget"]
```

```python
# File: app/models/__init__.py
from .base import Base, TimestampMixin, UserAuditMixin
from .user import User, Role, Permission, UserRole, RolePermission
from .company_setting import CompanySetting
from .account_type import AccountType
from .currency import Currency
from .exchange_rate import ExchangeRate
from .budget import Budget, BudgetDetail
from .account import Account
from .fiscal_period import FiscalPeriod
from .journal_entry import JournalEntry, JournalEntryLine, RecurringPattern 
from .customer import Customer
from .vendor import Vendor
from .product import Product
from .tax_code import TaxCode
from .gst_return import GSTReturn

__all__ = [
    "Base", "TimestampMixin", "UserAuditMixin",
    "User", "Role", "Permission", "UserRole", "RolePermission",
    "CompanySetting",
    "AccountType",
    "Currency",
    "ExchangeRate",
    "Budget", "BudgetDetail",
    "Account",
    "FiscalPeriod",
    "JournalEntry", "JournalEntryLine", "RecurringPattern",
    "Customer",
    "Vendor",
    "Product",
    "TaxCode",
    "GSTReturn",
]
```

```python
# File: app/models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import DateTime # Ensure DateTime is imported
from typing import Optional
import datetime

Base = declarative_base()

class TimestampMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), onupdate=func.now())

class UserAuditMixin:
    # These would ideally be ForeignKeys to a User model ID if users table is guaranteed.
    # For models in 'core' schema like User itself, this mixin might not apply or needs adjustment.
    created_by: Mapped[int] 
    updated_by: Mapped[int]
```

```python
# File: app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
import datetime # For Mapped[datetime.datetime]

# Junction table for User and Role (many-to-many)
user_roles_table = Table(
    'user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('core.users.id', ondelete="CASCADE"), primary_key=True),
    Column('role_id', Integer, ForeignKey('core.roles.id', ondelete="CASCADE"), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    schema='core'
)

# Junction table for Role and Permission (many-to-many)
role_permissions_table = Table(
    'role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('core.roles.id', ondelete="CASCADE"), primary_key=True),
    Column('permission_id', Integer, ForeignKey('core.permissions.id', ondelete="CASCADE"), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    schema='core'
)

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    roles: Mapped[list["Role"]] = relationship("Role", secondary=user_roles_table, back_populates="users")

class Role(Base, TimestampMixin):
    __tablename__ = 'roles'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(200), nullable=True)

    users: Mapped[list["User"]] = relationship("User", secondary=user_roles_table, back_populates="roles")
    permissions: Mapped[list["Permission"]] = relationship("Permission", secondary=role_permissions_table, back_populates="roles")

class Permission(Base): 
    __tablename__ = 'permissions'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True) 
    description: Mapped[str] = mapped_column(String(200), nullable=True)
    module: Mapped[str] = mapped_column(String(50), nullable=False) 
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    roles: Mapped[list["Role"]] = relationship("Role", secondary=role_permissions_table, back_populates="permissions")

class UserRole(Base):
    __tablename__ = 'user_roles'
    __table_args__ = {'schema': 'core'}
    user_id: Mapped[int] = mapped_column(ForeignKey('core.users.id', ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey('core.roles.id', ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class RolePermission(Base):
    __tablename__ = 'role_permissions'
    __table_args__ = {'schema': 'core'}
    role_id: Mapped[int] = mapped_column(ForeignKey('core.roles.id', ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey('core.permissions.id', ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

```python
# File: app/models/company_setting.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, LargeBinary 
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
import datetime # For Mapped type hints
from typing import Optional # For Mapped type hints

class CompanySetting(Base, TimestampMixin):
    __tablename__ = 'company_settings'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)
    uen_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_registration_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(50), default='Singapore', nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(50), default='Singapore', nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    logo: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, default=1)
    fiscal_year_start_day: Mapped[int] = mapped_column(Integer, default=1)
    base_currency: Mapped[str] = mapped_column(String(3), default='SGD')
```

```python
# File: app/models/account_type.py
from sqlalchemy import Column, Integer, String, Boolean, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
from typing import Optional

class AccountType(Base):
    __tablename__ = 'account_types'
    __table_args__ = (
        CheckConstraint("category IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')", name='ck_account_type_category'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False) 
    is_debit_balance: Mapped[bool] = mapped_column(Boolean, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
```

```python
# File: app/models/currency.py
from sqlalchemy import Column, String, Boolean, Integer, DateTime # String for CHAR(3)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from typing import Optional

class Currency(Base, TimestampMixin):
    __tablename__ = 'currencies'
    __table_args__ = {'schema': 'accounting'}

    code: Mapped[str] = mapped_column(String(3), primary_key=True) 
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    decimal_places: Mapped[int] = mapped_column(Integer, default=2)
```

```python
# File: app/models/exchange_rate.py
from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.currency import Currency # For relationship type hint
import datetime # For Mapped type hints
from decimal import Decimal # For Mapped type hints
from typing import Optional

class ExchangeRate(Base, TimestampMixin):
    __tablename__ = 'exchange_rates'
    __table_args__ = (
        UniqueConstraint('from_currency_code', 'to_currency_code', 'rate_date', name='uq_exchange_rates_pair_date'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    from_currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), nullable=False)
    to_currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), nullable=False)
    rate_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(15, 6), nullable=False)
    
    from_currency: Mapped["Currency"] = relationship(foreign_keys=[from_currency_code])
    to_currency: Mapped["Currency"] = relationship(foreign_keys=[to_currency_code])
```

```python
# File: app/models/budget.py
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin, UserAuditMixin
# from app.models.account import Account # Forward declaration, will resolve in account.py if needed, or import directly
from typing import List, Optional # For Mapped type hints
from decimal import Decimal # For Mapped type hints

class Budget(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'budgets'
    __table_args__ = {'schema': 'accounting'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    details: Mapped[List["BudgetDetail"]] = relationship("BudgetDetail", back_populates="budget", cascade="all, delete-orphan")

class BudgetDetail(Base, TimestampMixin): 
    __tablename__ = 'budget_details'
    __table_args__ = (
        UniqueConstraint('budget_id', 'account_id', 'period', name='uq_budget_details_budget_account_period'),
        CheckConstraint('period >= 1 AND period <= 12', name='ck_budget_details_period'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    budget_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.budgets.id', ondelete="CASCADE"), nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.accounts.id', ondelete="CASCADE"), nullable=False)
    period: Mapped[int] = mapped_column(Integer, nullable=False) 
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    budget: Mapped["Budget"] = relationship("Budget", back_populates="details")
    # account relationship defined in account.py if back_populates="budget_details" is added there.
    # For now, simple relationship:
    account: Mapped["Account"] = relationship("Account") # Assuming Account model exists
```

```python
# File: app/models/account.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import List, Optional 
import datetime

from app.models.base import Base, TimestampMixin, UserAuditMixin
# from app.models.journal_entry import JournalEntryLine # Circular import, handle with back_populates string
# from app.models.budget import BudgetDetail # Circular import

class Account(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'accounts'
    __table_args__ = (
         CheckConstraint("account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')", name='ck_accounts_account_type'),
        {'schema': 'accounting'}
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False) 
    sub_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    tax_treatment: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) 
    gst_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
        
    parent: Mapped[Optional["Account"]] = relationship("Account", remote_side=[id], back_populates="children", foreign_keys=[parent_id])
    children: Mapped[List["Account"]] = relationship("Account", back_populates="parent")
    
    journal_lines: Mapped[List["JournalEntryLine"]] = relationship("JournalEntryLine", back_populates="account")
    budget_details: Mapped[List["BudgetDetail"]] = relationship("BudgetDetail", back_populates="account")


    def to_dict(self): 
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'account_type': self.account_type,
            'sub_type': self.sub_type,
            'parent_id': self.parent_id,
            'is_active': self.is_active,
            'description': self.description,
        }

# Resolve forward references if any (not strictly needed with Mapped and string type hints usually)
# BudgetDetail.account = relationship("Account", back_populates="budget_details")
```

```python
# File: app/models/fiscal_period.py
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import datetime

from app.models.base import Base, TimestampMixin, UserAuditMixin
from typing import Optional

class FiscalPeriod(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'fiscal_periods'
    __table_args__ = (
        UniqueConstraint('start_date', 'end_date', name='uq_fiscal_periods_dates'),
        CheckConstraint('start_date <= end_date', name='ck_fiscal_periods_date_order'),
        CheckConstraint("period_type IN ('Month', 'Quarter', 'Year')", name='ck_fiscal_periods_period_type'),
        CheckConstraint("status IN ('Open', 'Closed', 'Archived')", name='ck_fiscal_periods_status'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    period_type: Mapped[str] = mapped_column(String(10), nullable=False) 
    status: Mapped[str] = mapped_column(String(10), nullable=False, default='Open')
    is_adjustment: Mapped[bool] = mapped_column(Boolean, default=False)
```

```python
# File: app/models/journal_entry.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Text, DateTime, Date, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func
from typing import List, Optional
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin, UserAuditMixin
from app.models.account import Account
from app.models.fiscal_period import FiscalPeriod

class RecurringPattern(Base, TimestampMixin, UserAuditMixin): 
    __tablename__ = 'recurring_patterns'
    __table_args__ = {'schema': 'accounting'}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) 
    interval: Mapped[int] = mapped_column(Integer, default=1) 
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    next_due_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    last_generated_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True) 
    template_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id', use_alter=True, name='fk_recurring_patterns_template_entry_id'), nullable=True) 
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
class JournalEntry(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'journal_entries'
    __table_args__ = {'schema': 'accounting'}
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    entry_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    journal_type: Mapped[str] = mapped_column(String(20), nullable=False) 
    entry_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    fiscal_period_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_periods.id'), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurring_pattern_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.recurring_patterns.id'), nullable=True)
    is_posted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_reversed: Mapped[bool] = mapped_column(Boolean, default=False)
    reversing_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id', use_alter=True, name='fk_journal_entries_reversing_entry_id'), nullable=True)
        
    fiscal_period: Mapped["FiscalPeriod"] = relationship("FiscalPeriod")
    lines: Mapped[List["JournalEntryLine"]] = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")
    recurring_pattern: Mapped[Optional["RecurringPattern"]] = relationship("RecurringPattern", foreign_keys=[recurring_pattern_id]) # type: ignore
    
    reversing_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry", remote_side=[id], foreign_keys=[reversing_entry_id], uselist=False, post_update=True) # type: ignore

# For RecurringPattern.template_entry_id FK to JournalEntry.id
RecurringPattern.template_journal_entry = relationship("JournalEntry", foreign_keys=[RecurringPattern.template_entry_id]) # type: ignore


class JournalEntryLine(Base, TimestampMixin): 
    __tablename__ = 'journal_entry_lines'
    __table_args__ = (
        CheckConstraint(
            " (debit_amount > 0 AND credit_amount = 0) OR "
            " (credit_amount > 0 AND debit_amount = 0) OR "
            " (debit_amount = 0 AND credit_amount = 0) ", # Allowing zero lines if needed
            name='ck_journal_entry_lines_debit_credit'
        ),
        {'schema': 'accounting'}
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    journal_entry_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id', ondelete="CASCADE"), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    debit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal(0))
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal(0))
    currency_code: Mapped[str] = mapped_column(String(3), default='SGD') 
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(15, 6), default=Decimal(1))
    tax_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) 
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal(0))
    dimension1_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) 
    dimension2_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) 
        
    journal_entry: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="lines")
    account: Mapped["Account"] = relationship("Account", back_populates="journal_lines") # type: ignore
    
    @validates('debit_amount', 'credit_amount')
    def validate_amounts(self, key, value):
        value_decimal = Decimal(str(value)) # Ensure it's Decimal
        if key == 'debit_amount' and value_decimal > Decimal(0):
            self.credit_amount = Decimal(0)
        elif key == 'credit_amount' and value_decimal > Decimal(0):
            self.debit_amount = Decimal(0)
        return value_decimal
```

```python
# File: app/models/customer.py
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from typing import Optional
from decimal import Decimal

from app.models.base import Base, TimestampMixin, UserAuditMixin

class Customer(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'customers'
    __table_args__ = {'schema': 'business'}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    uen_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    gst_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(50), default='Singapore')
    credit_terms: Mapped[int] = mapped_column(Integer, default=30) 
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), default='SGD') 
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

```python
# File: app/models/vendor.py
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from typing import Optional
from decimal import Decimal

from app.models.base import Base, TimestampMixin, UserAuditMixin

class Vendor(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'vendors'
    __table_args__ = {'schema': 'business'}

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vendor_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    uen_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    gst_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    withholding_tax_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    withholding_tax_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5,2), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(50), default='Singapore')
    payment_terms: Mapped[int] = mapped_column(Integer, default=30) 
    currency_code: Mapped[str] = mapped_column(String(3), default='SGD') 
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bank_account_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) 
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_swift_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
```

```python
# File: app/models/product.py
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional
from decimal import Decimal

from app.models.base import Base, TimestampMixin, UserAuditMixin
from app.models.account import Account

class Product(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'products'
    __table_args__ = (
        CheckConstraint("product_type IN ('Inventory', 'Service', 'Non-Inventory')", name='ck_products_product_type'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_type: Mapped[str] = mapped_column(String(20), nullable=False)
    unit_of_measure: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sales_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)
    purchase_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)
    sales_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
    purchase_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
    inventory_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
    tax_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) 
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    sales_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[sales_account_id])
    purchase_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[purchase_account_id])
    inventory_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[inventory_account_id])
```

```python
# File: app/models/tax_code.py
from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional
from decimal import Decimal

from app.models.base import Base, TimestampMixin, UserAuditMixin
from app.models.account import Account

class TaxCode(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'tax_codes'
    __table_args__ = (
        CheckConstraint("tax_type IN ('GST', 'Income Tax', 'Withholding Tax')", name='ck_tax_codes_tax_type'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    tax_type: Mapped[str] = mapped_column(String(20), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(5,2), nullable=False) 
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    affects_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)

    affects_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[affects_account_id])
```

```python
# File: app/models/gst_return.py
from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from typing import Optional
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin, UserAuditMixin

class GSTReturn(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'gst_returns'
    __table_args__ = (
        CheckConstraint("status IN ('Draft', 'Submitted', 'Amended')", name='ck_gst_returns_status'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    return_period: Mapped[str] = mapped_column(String(20), unique=True, nullable=False) 
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    filing_due_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    standard_rated_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    zero_rated_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    exempt_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    total_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    taxable_purchases: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    output_tax: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    input_tax: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    tax_payable: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    status: Mapped[str] = mapped_column(String(20), default='Draft')
    submission_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    submission_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
```

```python
# File: app/core/config_manager.py
# Based on TDS usage, but improved path handling
import os
import configparser
from types import SimpleNamespace
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file_name: str = "config.ini", app_name: str = "SGBookkeeper"):
        if os.name == 'nt': # Windows
            self.config_dir = Path(os.getenv('APPDATA', Path.home() / 'AppData' / 'Roaming')) / app_name
        elif sys.platform == 'darwin': # macOS
            self.config_dir = Path.home() / 'Library' / 'Application Support' / app_name
        else: # Linux and other UNIX-like
            self.config_dir = Path(os.getenv('XDG_CONFIG_HOME', Path.home() / '.config')) / app_name
        
        self.config_file_path = self.config_dir / config_file_name
        os.makedirs(self.config_dir, exist_ok=True)

        self.parser = configparser.ConfigParser()
        self._load_config()

    def _load_config(self):
        if not self.config_file_path.exists():
            self._create_default_config()
        self.parser.read(self.config_file_path)

    def _create_default_config(self):
        self.parser['Database'] = {
            'username': 'postgres',
            'password': '', # Empty by default, user should configure or app prompts.
            'host': 'localhost',
            'port': '5432',
            'database': 'sg_bookkeeper',
            'echo_sql': 'False',
            'pool_min_size': '2',
            'pool_max_size': '10',
            'pool_recycle_seconds': '3600'
        }
        self.parser['Application'] = {
            'theme': 'light',
            'language': 'en',
            'last_opened_company_id': '' # Example application setting
        }
        with open(self.config_file_path, 'w') as f:
            self.parser.write(f)
        print(f"Default configuration created at {self.config_file_path}")

    def get_database_config(self):
        db_config = self.parser['Database']
        return SimpleNamespace(
            username=db_config.get('username', 'postgres'),
            password=db_config.get('password', ''), 
            host=db_config.get('host', 'localhost'),
            port=db_config.getint('port', 5432),
            database=db_config.get('database', 'sg_bookkeeper'),
            echo_sql=db_config.getboolean('echo_sql', False),
            pool_min_size=db_config.getint('pool_min_size', 2),
            pool_max_size=db_config.getint('pool_max_size', 10),
            pool_recycle_seconds=db_config.getint('pool_recycle_seconds', 3600)
        )

    def get_app_config(self):
        app_config = self.parser['Application']
        return SimpleNamespace(
            theme=app_config.get('theme', 'light'),
            language=app_config.get('language', 'en'),
            last_opened_company_id=app_config.get('last_opened_company_id', '')
        )

    def get_setting(self, section: str, key: str, fallback=None):
        return self.parser.get(section, key, fallback=fallback)

    def set_setting(self, section: str, key: str, value: str):
        if not self.parser.has_section(section):
            self.parser.add_section(section)
        self.parser.set(section, key, str(value))
        with open(self.config_file_path, 'w') as f:
            self.parser.write(f)
```

```python
# File: app/core/database_manager.py
# Content previously generated, no changes needed.
```

```python
# File: app/core/security_manager.py
# Content previously generated, ensure User model is imported correctly for type hints.
import bcrypt
from typing import Optional
from app.models.user import User # Corrected import if User is in app.models.user
from sqlalchemy import select # For actual DB query
# from app.core.database_manager import DatabaseManager # If passing db_manager for queries

class SecurityManager:
    def __init__(self, db_manager): # db_manager for user lookups
        self.db_manager = db_manager # app.core.DatabaseManager instance
        self.current_user: Optional[User] = None

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password.decode('utf-8') # Store as string

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        async with self.db_manager.session() as session: # Use the async session
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            user = result.scalars().first()
            
            if user and user.is_active and self.verify_password(password, user.password_hash):
                self.current_user = user
                # Potentially update last_login here
                # user.last_login = datetime.utcnow() # Or use DB func.now() if model is set up for it
                # await session.commit() # If last_login is updated
                return user
        self.current_user = None
        return None

    def logout_user(self):
        self.current_user = None

    def get_current_user(self) -> Optional[User]:
        return self.current_user

    def authorize(self, required_permission_code: str) -> bool:
        if not self.current_user or not self.current_user.is_active:
            return False
        
        # This assumes user.roles and role.permissions are eagerly loaded or accessible
        # within an active session context if lazy loading.
        # For a detached user object, these relationships might not be loaded.
        # A more robust way is to query permissions directly for the user.
        # For simplicity, assuming relationships are loaded:
        if not self.current_user.roles: # If roles is None or empty list
             return False # User has no roles, so no permissions

        for role in self.current_user.roles:
            if not role.permissions: continue
            for perm in role.permissions:
                if perm.code == required_permission_code:
                    return True
        return False

    async def create_user(self, username, password, email=None, full_name=None, roles_names=None):
        # Simplified user creation - in real app, use a UserService
        if roles_names is None:
            roles_names = []
        
        async with self.db_manager.session() as session:
            existing_user = await session.execute(select(User).where(User.username == username))
            if existing_user.scalars().first():
                raise ValueError(f"User {username} already exists.")

            hashed_password = self.hash_password(password)
            new_user = User(
                username=username, 
                password_hash=hashed_password, 
                email=email, 
                full_name=full_name,
                is_active=True
            )
            
            # Assign roles
            if roles_names:
                roles_stmt = select(Role).where(Role.name.in_(roles_names)) # type: ignore
                roles_result = await session.execute(roles_stmt)
                db_roles = roles_result.scalars().all()
                if len(db_roles) != len(roles_names):
                    # Handle missing roles error
                    pass
                new_user.roles.extend(db_roles) # type: ignore

            session.add(new_user)
            await session.flush() # To get new_user.id if needed immediately
            # Commit is handled by session context manager
            return new_user
```

```python
# File: app/core/module_manager.py
# Content previously generated.
```

```python
# File: app/core/application_core.py
# Content previously generated.
# Ensure service properties are correctly set up or use a more robust DI/Service Locator.
# For now, the properties like `accounting_service` directly instantiate services.
# This is okay for a small app but can become complex.
# Consider initializing all services in `startup` and storing them.
```

```python
# File: app/services/__init__.py
# Content previously generated.
```

```python
# File: app/utils/result.py
# Content previously generated.
```

```python
# File: app/services/account_service.py
# Content previously generated.
```

```python
# File: app/services/journal_service.py
# Content previously generated. Updated to include stubs from IJournalEntryRepository more fully.
from typing import List, Optional, Any
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, literal_column, case, text
from sqlalchemy.orm import aliased, selectinload
from app.models import JournalEntry, JournalEntryLine, Account, RecurringPattern # Added RecurringPattern
from app.core.database_manager import DatabaseManager
from app.services import IJournalEntryRepository
from app.utils.result import Result
# from app.core.application_core import ApplicationCore # Avoid circular import

class JournalService(IJournalEntryRepository):
    def __init__(self, db_manager: DatabaseManager, app_core: Optional[Any] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, journal_id: int) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            # Eager load lines for journal entry
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(JournalEntry.id == journal_id)
            result = await session.execute(stmt)
            return result.scalars().first()


    async def get_all(self) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
            
    async def get_by_entry_no(self, entry_no: str) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(JournalEntry.entry_no == entry_no)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_posted_entries_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(
                JournalEntry.is_posted == True,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save(self, journal_entry: JournalEntry) -> JournalEntry:
        async with self.db_manager.session() as session:
            session.add(journal_entry)
            await session.flush() # Flush to get IDs for lines if cascade is setup.
            await session.refresh(journal_entry)
            return journal_entry
            
    async def add(self, entity: JournalEntry) -> JournalEntry:
        return await self.save(entity)

    async def update(self, entity: JournalEntry) -> JournalEntry:
        return await self.save(entity)

    async def delete(self, id_val: int) -> bool:
        entry = await self.get_by_id(id_val)
        if entry and not entry.is_posted: 
            async with self.db_manager.session() as session:
                await session.delete(entry)
            return True
        return False

    async def post(self, journal_id: int) -> bool:
        entry = await self.get_by_id(journal_id)
        if not entry or entry.is_posted:
            return False
        entry.is_posted = True
        # user_id = self.app_core.current_user.id if self.app_core and self.app_core.current_user else None # Example, must exist
        # entry.updated_by = user_id if user_id is not None else entry.updated_by # Keep existing if no user
        # entry.updated_at = datetime.utcnow() # Or use DB default
        await self.save(entry)
        return True

    async def reverse(self, journal_id: int, reversal_date: date, description: str) -> Optional[JournalEntry]:
        # This method seems misplaced in a pure repository.
        # The JournalEntryManager should handle creation of the reversal entry.
        # This repository method would then just save the pair (original_entry, reversal_entry).
        # For now, raising NotImplementedError to highlight this design point.
        raise NotImplementedError("Reversal logic (creating new JE) belongs in JournalEntryManager; repository should save.")

    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = (
                select(
                    func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0))
                )
                .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
                .where(
                    JournalEntryLine.account_id == account_id,
                    JournalEntry.is_posted == True,
                    JournalEntry.entry_date <= as_of_date
                )
            )
            result = await session.execute(stmt)
            balance = result.scalar_one_or_none()
            return balance if balance is not None else Decimal(0)

    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = (
                select(
                    func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0))
                )
                .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
                .where(
                    JournalEntryLine.account_id == account_id,
                    JournalEntry.is_posted == True,
                    JournalEntry.entry_date >= start_date,
                    JournalEntry.entry_date <= end_date
                )
            )
            result = await session.execute(stmt)
            balance_change = result.scalar_one_or_none()
            return balance_change if balance_change is not None else Decimal(0)
            
    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]:
        async with self.db_manager.session() as session:
            stmt = select(RecurringPattern).where(
                RecurringPattern.is_active == True,
                RecurringPattern.next_due_date <= as_of_date,
                # Optional: check end_date if present
                or_(RecurringPattern.end_date == None, RecurringPattern.end_date >= as_of_date)
            ).order_by(RecurringPattern.next_due_date)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern:
        async with self.db_manager.session() as session:
            session.add(pattern)
            await session.flush()
            await session.refresh(pattern)
            return pattern
```

```python
# File: app/services/fiscal_period_service.py
# Content previously generated.
```

```python
# File: app/services/tax_service.py
# Content previously generated.
```

```python
# File: app/common/enums.py
# Content previously generated.
```

```python
# File: app/utils/sequence_generator.py
# Content previously generated.
```

```python
# File: app/utils/pydantic_models.py
# Content previously generated.
```

```python
# File: app/accounting/chart_of_accounts_manager.py
# Content previously generated.
```

```python
# File: app/accounting/journal_entry_manager.py
# Content previously generated.
```

```python
# File: app/tax/gst_manager.py
# Content previously generated.
```

```python
# File: app/tax/tax_calculator.py
# Content previously generated.
```

```python
# File: app/reporting/financial_statement_generator.py
# Content previously generated.
```

```python
# File: app/accounting/fiscal_period_manager.py
# Content previously generated.
```

```python
# File: app/accounting/currency_manager.py
# Content previously generated.
```

```python
# File: app/tax/income_tax_manager.py
# Content previously generated.
```

```python
# File: app/tax/withholding_tax_manager.py
# Content previously generated.
```

```python
# File: app/reporting/tax_report_generator.py
# Content previously generated.
```

```python
# File: app/reporting/report_engine.py
# Content previously generated.
```

```python
# File: app/ui/dashboard/dashboard_widget.py
# Content previously generated.
```

```python
# File: app/ui/accounting/accounting_widget.py
# Content previously generated.
```

```python
# File: app/ui/accounting/account_dialog.py
# Content previously generated.
```

```python
# File: app/ui/accounting/chart_of_accounts_widget.py
# Content previously generated.
```

```python
# File: app/ui/customers/customers_widget.py
# Content previously generated.
```

```python
# File: app/ui/vendors/vendors_widget.py
# Content previously generated.
```

```python
# File: app/ui/banking/banking_widget.py
# Content previously generated.
```

```python
# File: app/ui/reports/reports_widget.py
# Content previously generated.
```

```python
# File: app/ui/settings/settings_widget.py
# Content previously generated.
```

```python
# File: app/ui/main_window.py
# Content previously generated.
```

```python
# File: app/main.py
# Content previously generated.
```

```python
# File: app/utils/validation.py
# Content previously generated.
```

```python
# File: app/utils/formatting.py
# Content previously generated.
```

```python
# File: app/utils/converters.py
# Content previously generated.
```

```python
# File: scripts/db_init.py
# Content previously generated.
```

```sql
-- File: scripts/schema.sql
-- Content previously generated.
```

```sql
-- File: scripts/initial_data.sql
-- Content previously generated.
```

```python
# File: resources/resources.qrc
# Content (as a comment indicating structure) previously generated.
# This file needs to be created by the user with actual resource paths and then compiled.
# For example:
# <RCC>
#   <qresource prefix="/">
#     <file alias="icons/dashboard.svg">icons/dashboard.svg</file>
#     <!-- ... more icons -->
#     <file alias="images/splash.png">images/splash.png</file>
#   </qresource>
# </RCC>
# Then run: pyside6-rcc resources.qrc -o app/resources_rc.py
# And import app.resources_rc in app/main.py or similar.
# The current python code uses direct file paths like "resources/icons/dashboard.svg",
# so this QRC step is optional unless aliased paths (":/icons/dashboard.svg") are preferred.
```

```python
# File: resources/icons/dashboard.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/accounting.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/customers.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/vendors.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/banking.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/reports.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/settings.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/new_company.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/open_company.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/backup.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/restore.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/exit.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/preferences.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/help.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/about.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/filter.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/expand_all.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/collapse_all.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/refresh.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/edit.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/transactions.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/icons/deactivate.svg
# Content previously generated. (Dummy SVG)
```
```python
# File: resources/images/splash.png
# Placeholder previously noted. This is a binary file.
# A 1x1 transparent PNG base64:
# iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=
# User must replace this with an actual image.
```

```python
# File: data/chart_of_accounts/general_template.csv
# Content previously generated.
```
```python
# File: data/chart_of_accounts/retail_template.csv
# Content previously generated.
```
```python
# File: data/report_templates/balance_sheet_default.json
# Content previously generated.
```
```python
# File: data/tax_codes/sg_gst_codes_2023.csv
# Content previously generated.
```

```python
# File: docs/user_guide/index.md
# Content previously generated.
```
```python
# File: docs/user_guide/installation.md
# Content previously generated.
```
```python
# File: docs/user_guide/first_time_setup.md
"""
# First-Time Setup

This guide walks you through the initial configuration of SG Bookkeeper.
"""
```
```python
# File: docs/user_guide/dashboard.md
"""
# Dashboard Overview

Learn about the main dashboard and its components.
"""
```
```python
# File: docs/user_guide/chart_of_accounts.md
"""
# Managing Chart of Accounts

How to set up and manage your chart of accounts.
"""
```
```python
# File: docs/user_guide/transactions.md
"""
# Recording Transactions

Guide to entering various types of financial transactions.
"""
```
```python
# File: docs/user_guide/customers_vendors.md
"""
# Managing Customers and Vendors

Details on managing customer and vendor records.
"""
```
```python
# File: docs/user_guide/banking.md
"""
# Banking Operations

Reconciling bank accounts and managing banking transactions.
"""
```
```python
# File: docs/user_guide/reports.md
"""
# Generating Reports

How to generate and customize financial reports.
"""
```
```python
# File: docs/user_guide/gst_filing.md
"""
# GST Filing

Preparing and finalizing your GST F5 returns.
"""
```
```python
# File: docs/user_guide/year_end.md
"""
# Year-End Closing

Procedures for closing your fiscal year.
"""
```
```python
# File: docs/user_guide/settings.md
"""
# Settings and Preferences

Configuring application settings and user preferences.
"""
```
```python
# File: docs/user_guide/troubleshooting.md
"""
# Troubleshooting

Common issues and how to resolve them.
"""
```

```python
# File: docs/developer_guide/index.md
# Content previously generated.
```
```python
# File: docs/developer_guide/dev_setup.md
"""
# Development Setup

Instructions for setting up a development environment for SG Bookkeeper.
"""
```
```python
# File: docs/developer_guide/project_structure.md
"""
# Project Structure

Overview of the project's directory and file structure.
"""
```
```python
# File: docs/developer_guide/architecture.md
"""
# Architecture Overview

Details about the application's architecture.
"""
```
```python
# File: docs/developer_guide/database_schema.md
"""
# Database Schema

Information about the database schema design.
"""
```
```python
# File: docs/developer_guide/coding_conventions.md
"""
# Coding Conventions

Guidelines for writing code for SG Bookkeeper.
"""
```
```python
# File: docs/developer_guide/testing.md
"""
# Running Tests

How to run unit, integration, and UI tests.
"""
```
```python
# File: docs/developer_guide/building.md
"""
# Building and Packaging

Instructions for building executables and packages.
"""
```
```python
# File: docs/developer_guide/api_reference.md
"""
# API Reference (Internal)

This is an alias to the main API reference. See [api_reference/index.md](../api_reference/index.md).
"""
```
```python
# File: docs/developer_guide/contributing.md
"""
# Contributing Guidelines

How to contribute to the SG Bookkeeper project.
"""
```

```python
# File: docs/api_reference/index.md
# Content previously generated.
```
```python
# File: docs/api_reference/account_service.md
"""
# AccountService API

API documentation for `app.services.account_service.AccountService`.
"""
```
```python
# File: docs/api_reference/journal_service.md
"""
# JournalService API

API documentation for `app.services.journal_service.JournalService`.
"""
```
```python
# File: docs/api_reference/fiscal_period_service.md
"""
# FiscalPeriodService API

API documentation for `app.services.fiscal_period_service.FiscalPeriodService`.
"""
```
```python
# File: docs/api_reference/tax_code_service.md
"""
# TaxCodeService API

API documentation for `app.services.tax_service.TaxCodeService`.
"""
```
```python
# File: docs/api_reference/chart_of_accounts_manager.md
"""
# ChartOfAccountsManager API

API documentation for `app.accounting.chart_of_accounts_manager.ChartOfAccountsManager`.
"""
```
```python
# File: docs/api_reference/journal_entry_manager.md
"""
# JournalEntryManager API

API documentation for `app.accounting.journal_entry_manager.JournalEntryManager`.
"""
```
```python
# File: docs/api_reference/gst_manager.md
"""
# GSTManager API

API documentation for `app.tax.gst_manager.GSTManager`.
"""
```
```python
# File: docs/api_reference/financial_statement_generator.md
"""
# FinancialStatementGenerator API

API documentation for `app.reporting.financial_statement_generator.FinancialStatementGenerator`.
"""
```
```python
# File: docs/api_reference/tax_calculator.md
"""
# TaxCalculator API

API documentation for `app.tax.tax_calculator.TaxCalculator`.
"""
```
```python
# File: docs/api_reference/main_window.md
"""
# MainWindow UI Component

Documentation for `app.ui.main_window.MainWindow`.
"""
```
```python
# File: docs/api_reference/chart_of_accounts_widget.md
"""
# ChartOfAccountsWidget UI Component

Documentation for `app.ui.accounting.chart_of_accounts_widget.ChartOfAccountsWidget`.
"""
```

```python
# File: tests/__init__.py
# Content previously generated.
```
```python
# File: tests/unit/__init__.py
# Content previously generated.
```
```python
# File: tests/integration/__init__.py
# Content previously generated.
```
```python
# File: tests/ui/__init__.py
# Content previously generated.
```

```python
# File: tests/conftest.py
# Content previously generated.
```

```python
# File: tests/unit/test_example_unit.py
# Content previously generated.
```

```python
# File: tests/integration/test_example_integration.py
# Content previously generated.
```

```python
# File: tests/ui/test_example_ui.py
# Content previously generated.
```

```yaml
# File: .github/workflows/ci.yml
# Content previously generated.
# Note on PostgreSQL service for CI:
# The previous CI YAML had a conceptual note about starting PostgreSQL.
# A more concrete way using GitHub Actions services:
name: Python CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11"]

    # Service containers to run with `build`
    services:
      postgres:
        image: postgres:14 # Use PostgreSQL 14 as per TDS
        env:
          POSTGRES_DB: sg_bookkeeper_test # Pre-creates this database
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpassword
        ports:
          - 5432:5432 # Map container port 5432 to host (runner) port 5432
        # Options for health check ensures postgres is ready before tests run
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v4 # Updated to v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4 # Updated to v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install Poetry
      run: |
        pip install poetry
        poetry config virtualenvs.create true --local
        poetry config virtualenvs.in-project true --local

    - name: Install dependencies
      run: |
        poetry install --no-interaction --no-root 

    - name: Install project (for scripts etc.)
      run: |
        poetry install --no-interaction
    
    - name: Lint with Flake8
      run: |
        poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        poetry run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
    - name: Check formatting with Black
      run: |
        poetry run black . --check

    - name: Run Pytest
      env:
        # Environment variables for the tests to connect to the PostgreSQL service container
        PGHOST: localhost # Service container is accessible via localhost on the runner
        PGPORT: ${{ job.services.postgres.ports[5432] }} # Get mapped port
        PGDATABASE: sg_bookkeeper_test # Matches POSTGRES_DB in service config
        PGUSER: testuser             # Matches POSTGRES_USER
        PGPASSWORD: testpassword       # Matches POSTGRES_PASSWORD
        # PGPASSWORD needs to be set for psql commands if db_init is run
        # However, conftest.py should handle schema creation in the test DB.
      run: |
        # The database 'sg_bookkeeper_test' is created by the service container.
        # The schema (tables, etc.) needs to be created by conftest.py or db_init.
        # If conftest.py `test_db_manager` fixture handles Base.metadata.create_all,
        # then `db_init` script might not be needed here explicitly for schema.
        # poetry run python -m scripts.db_init --dbname sg_bookkeeper_test --user testuser --password testpassword --host localhost --port ${{ job.services.postgres.ports[5432] }} --drop-existing # if needed
        
        # For UI tests on headless CI, xvfb is typically required
        # sudo apt-get update && sudo apt-get install -y xvfb
        # xvfb-run poetry run pytest --cov=app --cov-report=xml
        poetry run pytest --cov=app --cov-report=xml

    # Optional: Upload coverage to Codecov
    # - name: Upload coverage to Codecov
    #   uses: codecov/codecov-action@v3
    #   with:
    #     token: ${{ secrets.CODECOV_TOKEN }}
    #     files: ./coverage.xml # Default path for pytest-cov xml report
    #     fail_ci_if_error: true

```

This completes the generation of the project structure and files based on the provided documents and my execution plan. The stubs and initial implementations provide a foundation for further development.
