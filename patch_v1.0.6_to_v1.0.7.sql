-- SQL Patch to upgrade SG Bookkeeper Database from v1.0.6 to v1.0.7
-- Version 2 (Corrected): Removed RAISE NOTICE statements for psql compatibility.
--
-- This patch performs the following actions:
-- 1. Adds the 'cash_flow_category' column to the 'accounting.accounts' table.
-- 2. Inserts new default system account configurations.
-- 3. Inserts the 'Accumulated Depreciation' account type.
-- 4. Inserts new general ledger accounts for WHT and Forex.
-- 5. Removes the old 'NR' tax code and adds a new, correctly configured 'WHT15' code.
-- 6. Updates existing accounts from the general template with their cash flow categories.

BEGIN;

-- 1. Add cash_flow_category to accounts table
-- Use a transaction and check for existence to make it safe to re-run.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'accounting' AND table_name = 'accounts' AND column_name = 'cash_flow_category'
    ) THEN
        ALTER TABLE accounting.accounts 
        ADD COLUMN cash_flow_category VARCHAR(20) CHECK (cash_flow_category IN ('Operating', 'Investing', 'Financing'));
        
        COMMENT ON COLUMN accounting.accounts.cash_flow_category IS 'Used to classify account balance changes for the Statement of Cash Flows.';
    END IF;
END;
$$;


-- 2. Insert new configurations (ON CONFLICT handles re-run safety)
INSERT INTO core.configuration (config_key, config_value, description, updated_by) VALUES
('SysAcc_WHTPayable', '2130', 'Default Withholding Tax Payable account code', 1),
('SysAcc_ForexGain', '7200', 'Default Foreign Exchange Gain account code', 1),
('SysAcc_ForexLoss', '8200', 'Default Foreign Exchange Loss account code', 1)
ON CONFLICT (config_key) DO UPDATE SET
    config_value = EXCLUDED.config_value,
    description = EXCLUDED.description,
    updated_by = EXCLUDED.updated_by,
    updated_at = CURRENT_TIMESTAMP;


-- 3. Insert new account type (ON CONFLICT handles re-run safety)
INSERT INTO accounting.account_types (name, category, is_debit_balance, report_type, display_order, description) VALUES
('Accumulated Depreciation', 'Asset', FALSE, 'Balance Sheet', 21, 'Contra-asset account for accumulated depreciation')
ON CONFLICT (name) DO NOTHING;


-- 4. Insert new general ledger accounts (ON CONFLICT handles re-run safety)
INSERT INTO accounting.accounts (code, name, account_type, sub_type, created_by, updated_by, is_active, is_control_account, is_bank_account, cash_flow_category) VALUES
('2130', 'Withholding Tax Payable', 'Liability', 'Current Liability', 1, 1, TRUE, FALSE, FALSE, 'Operating'),
('7200', 'Foreign Exchange Gain', 'Revenue', 'Other Income', 1, 1, TRUE, FALSE, FALSE, 'Operating'),
('8200', 'Foreign Exchange Loss', 'Expense', 'Other Expenses', 1, 1, TRUE, FALSE, FALSE, 'Operating')
ON CONFLICT (code) DO NOTHING;


-- 5. Replace 'NR' tax code with corrected 'WHT15'
DELETE FROM accounting.tax_codes WHERE code = 'NR';

INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id)
SELECT 'WHT15', 'WHT - Non-Resident Director Fee', 'Withholding Tax', 15.00, FALSE, TRUE, 1, 1, acc.id FROM accounting.accounts acc WHERE acc.code = '2130'
ON CONFLICT (code) DO UPDATE SET 
    description = EXCLUDED.description, 
    tax_type = EXCLUDED.tax_type, 
    rate = EXCLUDED.rate, 
    affects_account_id = EXCLUDED.affects_account_id, 
    updated_by = EXCLUDED.updated_by, 
    updated_at = CURRENT_TIMESTAMP;


-- 6. Update existing accounts with their cash flow category data
UPDATE accounting.accounts SET cash_flow_category = 'Operating' WHERE code IN ('1110','1111','1112','1120','1130','2110','2120','4100','4200','5100','6100','6110','6120','6130','7200','8100','8200','2130');
UPDATE accounting.accounts SET cash_flow_category = 'Investing' WHERE code IN ('1210','1211','7100');
UPDATE accounting.accounts SET cash_flow_category = 'Financing' WHERE code IN ('2210','3100','3200');
UPDATE accounting.accounts SET cash_flow_category = 'Operating' WHERE code = '1212' AND name LIKE 'Accumulated%';

COMMIT;

