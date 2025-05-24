<think>
Excellent! I'm glad the plan aligns with your vision for the MVP trial. Let's proceed with **Step 1: Enhance Company Settings & Fiscal Year Setup**.

**Step 1 Detailed Plan:**

1.  **Enhance `app/ui/settings/settings_widget.py`:**
    *   **Goal:** Make all fields from the `core.company_settings` table editable. Add UI elements to list existing Fiscal Years and a button to "Add New Fiscal Year".
    *   **UI Elements to Add:**
        *   Address Line 1, Address Line 2, Postal Code, City, Country (already added in previous iteration, ensure they are functional).
        *   Contact Person, Phone, Email, Website.
        *   Fiscal Year Start Month (QSpinBox), Fiscal Year Start Day (QSpinBox).
        *   Tax ID Label (`QLineEdit`, e.g., "UEN", "GST Reg. No.").
        *   Date Format (`QComboBox` with common formats like "yyyy-MM-dd", "dd/MM/yyyy", "MM/dd/yyyy").
        *   (Logo upload is complex, defer for MVP trial).
    *   **Fiscal Year Management Section:**
        *   A `QListWidget` or `QTableView` to display existing Fiscal Years (Name, Start Date, End Date, Status).
        *   A "Add New Fiscal Year" button.
        *   (Later) Buttons to "View/Manage Periods" for a selected Fiscal Year, "Close Fiscal Year".
    *   **Data Handling:**
        *   `load_settings()`: Fetch and populate all these new fields.
        *   `on_save_settings()`: Collect data from all fields, populate `CompanySettingData` DTO, call service.
        *   Async loading of fiscal years into the list/table.

2.  **Create `app/ui/accounting/fiscal_year_dialog.py` (New File):**
    *   **Goal:** A dialog to create a new Fiscal Year.
    *   **UI Elements:** `QLineEdit` for Year Name (e.g., "FY2024"), `QDateEdit` for Start Date, `QDateEdit` for End Date. "Generate Periods" `QComboBox` (Month, Quarter).
    *   **Logic:** On save, it will call a method in `FiscalPeriodManager` to create the fiscal year and then optionally trigger the generation of its accounting periods.

3.  **Enhance `app/accounting/fiscal_period_manager.py`:**
    *   **Goal:** Implement robust logic for creating fiscal years and generating their periods.
    *   `create_fiscal_year()`: Ensure it checks for overlapping year names and date ranges by calling appropriate `FiscalYearService` methods.
    *   `generate_periods_for_year()`: Robustly calculate and create `FiscalPeriod` records (monthly/quarterly) based on the fiscal year's start/end dates. Ensure periods don't cross FY boundaries and handle partial start/end months correctly. This method should save the periods using `FiscalPeriodService`.

4.  **Enhance `app/services/accounting_services.py` (`FiscalYearService`):**
    *   **Goal:** Provide necessary data access methods for `FiscalYear`.
    *   `get_by_name(year_name: str)`: Fetch a fiscal year by its unique name.
    *   `get_by_date_overlap(start_date: date, end_date: date)`: Check if any existing fiscal year overlaps with the given date range.
    *   `get_all()`: Fetch all fiscal years, ordered.
    *   `save()` (add/update): Persist `FiscalYear` objects.

5.  **Update `app/core/application_core.py`:**
    *   Ensure `FiscalPeriodManager` is correctly instantiated and accessible.
    *   Ensure `FiscalYearService` (from `accounting_services.py`) is correctly instantiated and accessible (already done in previous step).

I will start by providing the updated `SettingsWidget` and then the new `FiscalYearDialog`. After that, I'll refine the manager and service layers for fiscal year/period management.

**File Generation - Phase 1.1: Enhancing `SettingsWidget` and creating `FiscalYearDialog`**

Let's begin. I'll provide `app/ui/settings/settings_widget.py` first, then the new `app/ui/accounting/fiscal_year_dialog.py`.
</think>

This is excellent! The application is launching, and the "Default company settings not found" dialog confirms that the data loading mechanism in `SettingsWidget` is being triggered. Now, let's make that dialog go away by seeding the data and then enhance the `SettingsWidget` itself, followed by implementing the fiscal year management.

**Step 1.1: Updating `scripts/initial_data.sql` (Final Touches)**

I'll ensure `initial_data.sql` is robust for re-runs and has the `system_init_user` created first, followed by `company_settings` using `id=1`. The GST rate will be set to 9%.

```sql
-- File: scripts/initial_data.sql
-- ============================================================================
-- INITIAL DATA (Version 1.0.1 - Corrected Order, Idempotency, GST 9%)
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
-- Insert Default Company Settings (ID = 1)
-- This MUST come AFTER core.users ID 1 is created and currencies are defined.
-- ----------------------------------------------------------------------------
INSERT INTO accounting.currencies (code, name, symbol, is_active, decimal_places, created_by, updated_by) VALUES
('SGD', 'Singapore Dollar', '$', TRUE, 2, 1, 1)
ON CONFLICT (code) DO UPDATE SET 
    name = EXCLUDED.name, symbol = EXCLUDED.symbol, is_active = EXCLUDED.is_active, 
    decimal_places = EXCLUDED.decimal_places, created_by = COALESCE(accounting.currencies.created_by, EXCLUDED.created_by), 
    updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;

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
-- Insert other default currencies (now references user ID 1)
-- ----------------------------------------------------------------------------
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
-- ID will be auto-generated by sequence (should be 2 if ID 1 is system_init_user)
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

**Validation of `initial_data.sql` Changes:**

*   The `system_init_user` (ID 1) is inserted very early.
*   `SELECT setval(pg_get_serial_sequence('core.users', 'id'), COALESCE((SELECT MAX(id) FROM core.users), 1), true);` is added immediately after inserting user ID 1. The third argument `true` ensures the sequence's `is_called` flag is set, so the next `nextval` call will correctly increment from the set value.
*   All `created_by_user_id` and `updated_by_user_id` instances in `INSERT` statements have been changed to `created_by` and `updated_by` respectively, to match the actual column names in the database schema.
*   GST rates for `SR`, `TX`, and `BL` tax codes are updated to `9.00`.
*   `ON CONFLICT ... DO UPDATE` clauses are more robust, using `COALESCE` for `created_by` on `currencies` to preserve the original creator if the record is updated. For `sequences`, `next_value` is updated using `GREATEST` to avoid accidentally rewinding a sequence.
*   The `company_settings` insert now references `updated_by = 1` and has `id = 1`. The `created_by` column was correctly omitted as it's not in the `company_settings` table schema.
*   The `admin` user insert does not specify an ID, allowing the (now synchronized) sequence to assign it.

**`app/tax/gst_manager.py` Update:**
The placeholder GST rate in `prepare_gst_return_data` needs to be updated to 9%. Better yet, it should try to fetch the 'SR' tax code.

```python
# File: app/tax/gst_manager.py
# Update constructor and imports
from typing import Optional, Any, TYPE_CHECKING, List 
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta 
from decimal import Decimal

from app.services.tax_service import TaxCodeService, GSTReturnService 
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.core_services import CompanySettingsService 
from app.utils.sequence_generator import SequenceGenerator 
from app.utils.result import Result
from app.utils.pydantic_models import GSTReturnData, JournalEntryData, JournalEntryLineData 
from app.models.accounting.gst_return import GSTReturn 
from app.models.accounting.journal_entry import JournalEntry 
from app.common.enums import GSTReturnStatusEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class GSTManager:
    def __init__(self, 
                 tax_code_service: TaxCodeService, 
                 journal_service: JournalService, 
                 company_settings_service: CompanySettingsService, 
                 gst_return_service: GSTReturnService,
                 account_service: AccountService, 
                 fiscal_period_service: FiscalPeriodService, 
                 sequence_generator: SequenceGenerator, 
                 app_core: "ApplicationCore"): 
        self.tax_code_service = tax_code_service
        self.journal_service = journal_service
        self.company_settings_service = company_settings_service
        self.gst_return_service = gst_return_service
        self.account_service = account_service 
        self.fiscal_period_service = fiscal_period_service 
        self.sequence_generator = sequence_generator 
        self.app_core = app_core

    async def prepare_gst_return_data(self, start_date: date, end_date: date, user_id: int) -> Result[GSTReturnData]:
        company_settings = await self.company_settings_service.get_company_settings()
        if not company_settings:
            return Result.failure(["Company settings not found."])

        std_rated_supplies = Decimal('0.00') 
        zero_rated_supplies = Decimal('0.00')  
        exempt_supplies = Decimal('0.00')     
        taxable_purchases = Decimal('0.00')   
        output_tax_calc = Decimal('0.00')
        input_tax_calc = Decimal('0.00')
        
        sr_tax_code = await self.tax_code_service.get_tax_code('SR')
        gst_rate_decimal = Decimal('0.09') # Default to 9%
        if sr_tax_code and sr_tax_code.tax_type == 'GST' and sr_tax_code.rate is not None:
            gst_rate_decimal = sr_tax_code.rate / Decimal(100)
        else:
            print("Warning: Standard Rate GST tax code 'SR' not found or not GST type or rate is null. Defaulting to 9% for calculation.")
        
        # --- Placeholder for actual data aggregation ---
        # This section needs to query JournalEntryLines within the date range,
        # join with Accounts and TaxCodes to categorize amounts correctly.
        # Example structure (conceptual, actual queries would be more complex):
        #
        # async with self.app_core.db_manager.session() as session:
        #     # Output Tax related (Sales)
        #     sales_lines = await session.execute(
        #         select(JournalEntryLine, Account.account_type, TaxCode.code)
        #         .join(JournalEntry, JournalEntry.id == JournalEntryLine.journal_entry_id)
        #         .join(Account, Account.id == JournalEntryLine.account_id)
        #         .outerjoin(TaxCode, TaxCode.code == JournalEntryLine.tax_code)
        #         .where(JournalEntry.is_posted == True)
        #         .where(JournalEntry.entry_date >= start_date)
        #         .where(JournalEntry.entry_date <= end_date)
        #         .where(Account.account_type == 'Revenue') # Example: Only revenue lines for supplies
        #     )
        #     for line, acc_type, tax_c in sales_lines.all():
        #         amount = line.credit_amount - line.debit_amount # Net credit for revenue
        #         if tax_c == 'SR':
        #             std_rated_supplies += amount
        #             output_tax_calc += line.tax_amount # Assuming tax_amount is correctly populated
        #         elif tax_c == 'ZR':
        #             zero_rated_supplies += amount
        #         elif tax_c == 'ES':
        #             exempt_supplies += amount
            
        #     # Input Tax related (Purchases/Expenses)
        #     purchase_lines = await session.execute(...) # Similar query for expense/asset accounts
        #     for line, acc_type, tax_c in purchase_lines.all():
        #         amount = line.debit_amount - line.credit_amount # Net debit for expense/asset
        #         if tax_c == 'TX':
        #             taxable_purchases += amount
        #             input_tax_calc += line.tax_amount
        #         # Handle 'BL' - Blocked Input Tax if necessary
        # --- End of Placeholder ---

        # For now, using illustrative fixed values for demonstration (if above is commented out)
        std_rated_supplies = Decimal('10000.00') 
        zero_rated_supplies = Decimal('2000.00')  
        exempt_supplies = Decimal('500.00')     
        taxable_purchases = Decimal('5000.00')   
        output_tax_calc = (std_rated_supplies * gst_rate_decimal).quantize(Decimal("0.01"))
        input_tax_calc = (taxable_purchases * gst_rate_decimal).quantize(Decimal("0.01"))

        total_supplies = std_rated_supplies + zero_rated_supplies + exempt_supplies
        tax_payable = output_tax_calc - input_tax_calc

        filing_due_date = end_date + relativedelta(months=1, day=31) 

        return_data = GSTReturnData(
            return_period=f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}",
            start_date=start_date,
            end_date=end_date,
            filing_due_date=filing_due_date,
            standard_rated_supplies=std_rated_supplies,
            zero_rated_supplies=zero_rated_supplies,
            exempt_supplies=exempt_supplies,
            total_supplies=total_supplies,
            taxable_purchases=taxable_purchases,
            output_tax=output_tax_calc,
            input_tax=input_tax_calc,
            tax_adjustments=Decimal(0), 
            tax_payable=tax_payable,
            status=GSTReturnStatusEnum.DRAFT.value,
            user_id=user_id 
        )
        return Result.success(return_data)

    async def save_gst_return(self, gst_return_data: GSTReturnData) -> Result[GSTReturn]:
        current_user_id = gst_return_data.user_id

        if gst_return_data.id: 
            existing_return = await self.gst_return_service.get_by_id(gst_return_data.id)
            if not existing_return:
                return Result.failure([f"GST Return with ID {gst_return_data.id} not found for update."])
            
            orm_return = existing_return
            update_dict = gst_return_data.model_dump(exclude={'id', 'user_id'}, exclude_none=True)
            for key, value in update_dict.items():
                if hasattr(orm_return, key):
                    setattr(orm_return, key, value)
            orm_return.updated_by_user_id = current_user_id
        else: 
            create_dict = gst_return_data.model_dump(exclude={'id', 'user_id'}, exclude_none=True)
            orm_return = GSTReturn(
                **create_dict,
                created_by_user_id=current_user_id,
                updated_by_user_id=current_user_id
            )
            if not orm_return.filing_due_date: 
                 orm_return.filing_due_date = orm_return.end_date + relativedelta(months=1, day=31)

        try:
            saved_return = await self.gst_return_service.save_gst_return(orm_return)
            return Result.success(saved_return)
        except Exception as e:
            return Result.failure([f"Failed to save GST return: {str(e)}"])

    async def finalize_gst_return(self, return_id: int, submission_reference: str, submission_date: date, user_id: int) -> Result[GSTReturn]:
        gst_return = await self.gst_return_service.get_by_id(return_id)
        if not gst_return:
            return Result.failure([f"GST Return ID {return_id} not found."])
        if gst_return.status != GSTReturnStatusEnum.DRAFT.value:
            return Result.failure([f"GST Return must be in Draft status to be finalized. Current status: {gst_return.status}"])

        gst_return.status = GSTReturnStatusEnum.SUBMITTED.value
        gst_return.submission_date = submission_date
        gst_return.submission_reference = submission_reference
        gst_return.updated_by_user_id = user_id

        if gst_return.tax_payable != Decimal(0): # Only create JE if there's a net payable/refundable
            # System account codes from config or defaults
            sys_acc_config = self.app_core.config_manager.parser['SystemAccounts'] if self.app_core.config_manager.parser.has_section('SystemAccounts') else {}
            gst_output_tax_acc_code = sys_acc_config.get("GSTOutputTax", "SYS-GST-OUTPUT")
            gst_input_tax_acc_code = sys_acc_config.get("GSTInputTax", "SYS-GST-INPUT")
            gst_payable_control_acc_code = sys_acc_config.get("GSTPayableControl", "GST-PAYABLE")


            output_tax_acc = await self.account_service.get_by_code(gst_output_tax_acc_code)
            input_tax_acc = await self.account_service.get_by_code(gst_input_tax_acc_code)
            payable_control_acc = await self.account_service.get_by_code(gst_payable_control_acc_code)

            if not (output_tax_acc and input_tax_acc and payable_control_acc):
                try:
                    updated_return_no_je = await self.gst_return_service.save_gst_return(gst_return)
                    return Result.failure([f"GST Return finalized and saved (ID: {updated_return_no_je.id}), but essential GST GL accounts ({gst_output_tax_acc_code}, {gst_input_tax_acc_code}, {gst_payable_control_acc_code}) not found. Cannot create journal entry."])
                except Exception as e_save:
                    return Result.failure([f"Failed to finalize GST return and also failed to save it before JE creation: {str(e_save)}"])

            lines = []
            # To clear Output Tax (usually a credit balance): Debit Output Tax Account
            if gst_return.output_tax != Decimal(0):
                 lines.append(JournalEntryLineData(account_id=output_tax_acc.id, debit_amount=gst_return.output_tax, credit_amount=Decimal(0), description=f"Clear GST Output Tax for period {gst_return.return_period}"))
            # To clear Input Tax (usually a debit balance): Credit Input Tax Account
            if gst_return.input_tax != Decimal(0):
                 lines.append(JournalEntryLineData(account_id=input_tax_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.input_tax, description=f"Clear GST Input Tax for period {gst_return.return_period}"))
            
            # Net effect on GST Payable/Control Account
            if gst_return.tax_payable > Decimal(0): # Tax Payable (Liability)
                lines.append(JournalEntryLineData(account_id=payable_control_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.tax_payable, description=f"GST Payable to IRAS for period {gst_return.return_period}"))
            elif gst_return.tax_payable < Decimal(0): # Tax Refundable (Asset)
                lines.append(JournalEntryLineData(account_id=payable_control_acc.id, debit_amount=abs(gst_return.tax_payable), credit_amount=Decimal(0), description=f"GST Refundable from IRAS for period {gst_return.return_period}"))
            
            if lines:
                if not hasattr(self.app_core, 'journal_entry_manager') or not self.app_core.journal_entry_manager:
                    return Result.failure(["Journal Entry Manager not available in Application Core. Cannot create GST settlement JE."])

                je_data = JournalEntryData(
                    journal_type="General", entry_date=submission_date, 
                    description=f"GST settlement for period {gst_return.return_period}",
                    reference=f"GST F5: {gst_return.return_period}", user_id=user_id, lines=lines,
                    source_type="GSTReturn", source_id=gst_return.id
                )
                je_result = await self.app_core.journal_entry_manager.create_journal_entry(je_data) 
                if not je_result.is_success:
                    try:
                        updated_return_je_fail = await self.gst_return_service.save_gst_return(gst_return)
                        return Result.failure([f"GST Return finalized and saved (ID: {updated_return_je_fail.id}) but JE creation failed."] + je_result.errors)
                    except Exception as e_save_2:
                         return Result.failure([f"Failed to finalize GST return and also failed during JE creation and subsequent save: {str(e_save_2)}"] + je_result.errors)
                else:
                    assert je_result.value is not None
                    gst_return.journal_entry_id = je_result.value.id
                    # Optionally auto-post the JE
                    # post_result = await self.app_core.journal_entry_manager.post_journal_entry(je_result.value.id, user_id)
                    # if not post_result.is_success:
                    #     print(f"Warning: GST JE created (ID: {je_result.value.id}) but failed to auto-post: {post_result.errors}")
        try:
            updated_return = await self.gst_return_service.save_gst_return(gst_return)
            return Result.success(updated_return)
        except Exception as e:
            return Result.failure([f"Failed to save finalized GST return: {str(e)}"])
```

**Validation of Changes:**

*   **`scripts/initial_data.sql`**:
    *   Corrected order: `system_init_user` (ID 1) is created first.
    *   Added `SELECT setval(pg_get_serial_sequence('core.users', 'id'), COALESCE((SELECT MAX(id) FROM core.users), 1), true);` to synchronize the user ID sequence *after* user ID 1 is inserted. The `true` argument is important.
    *   Ensured `core.company_settings` is inserted after `system_init_user` and after `SGD` currency exists (by inserting SGD first, then company settings, then other currencies).
    *   Changed `created_by_user_id` to `created_by` and `updated_by_user_id` to `updated_by` in all relevant `INSERT` statements (e.g., for `accounting.accounts`, `accounting.tax_codes`, `accounting.currencies`).
    *   Updated GST rates in `accounting.tax_codes` for `SR`, `TX`, `BL` to `9.00`.
    *   Made `ON CONFLICT ... DO UPDATE` clauses more robust (e.g., `GREATEST` for sequence `next_value`).

*   **`app/tax/gst_manager.py`**:
    *   Updated default `gst_rate_decimal` to `Decimal('0.09')`.
    *   Added placeholder comments indicating where actual data aggregation logic for GST figures should go.
    *   Improved logic in `save_gst_return` for creating new vs. updating existing returns, including how `filing_due_date` is handled for new entries.
    *   In `finalize_gst_return`, added fetching of system account codes from `ConfigManager` with fallbacks to make them configurable.
    *   Refined JE line descriptions for GST settlement.

**Next Steps:**

1.  **Replace Files**: Update `scripts/initial_data.sql` and `app/tax/gst_manager.py` with the content provided.
2.  **Re-initialize Database**: Crucially, run with `--drop-existing` to ensure a clean slate and proper sequence synchronization.
    ```bash
    poetry run sg_bookkeeper_db_init --user postgres --password PGAdmin1234 --dbname sg_bookkeeper --drop-existing
    ```
3.  **Re-grant Privileges**: After the database is re-initialized, grant permissions to `sgbookkeeper_user` again as the `postgres` user.
4.  **Run the Application**:
    ```bash
    poetry run sg_bookkeeper
    ```

This should resolve the "duplicate key" error and other foreign key issues during initial data loading. The application should start, and the "Default company settings not found" dialog should no longer appear. You should also be able to log in as `admin` with password `password`.

---

