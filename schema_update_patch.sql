-- FILE: schema_patch_1.0.3_to_1.0.4.sql
-- PURPOSE: Updates SG Bookkeeper database schema from version 1.0.3 to 1.0.4
--          Adds tables and columns required for saving bank reconciliation state.
--
-- PREVIOUS VERSION: 1.0.3 (Includes bank statement import fields, bank balance trigger, corrected trial_balance view)
-- NEW VERSION: 1.0.4
--
-- Important: Ensure your database schema is at version 1.0.3 before applying this patch.
-- It is recommended to backup your database before applying any schema changes.

BEGIN;

-- ----------------------------------------------------------------------------
-- 1. Add new table: business.bank_reconciliations
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS business.bank_reconciliations (
    id SERIAL PRIMARY KEY,
    bank_account_id INTEGER NOT NULL,
    statement_date DATE NOT NULL, -- The end date of the bank statement being reconciled
    statement_ending_balance NUMERIC(15,2) NOT NULL,
    calculated_book_balance NUMERIC(15,2) NOT NULL, -- The book balance that reconciles to the statement
    reconciled_difference NUMERIC(15,2) NOT NULL, -- Should be close to zero
    reconciliation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- When this reconciliation record was created
    notes TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER NOT NULL,
    CONSTRAINT uq_bank_reconciliation_account_statement_date UNIQUE (bank_account_id, statement_date)
);

COMMENT ON TABLE business.bank_reconciliations IS 'Stores summary records of completed bank reconciliations.';
COMMENT ON COLUMN business.bank_reconciliations.statement_date IS 'The end date of the bank statement that was reconciled.';
COMMENT ON COLUMN business.bank_reconciliations.calculated_book_balance IS 'The book balance of the bank account as of the statement_date, after all reconciling items for this reconciliation are accounted for.';


-- ----------------------------------------------------------------------------
-- 2. Add 'last_reconciled_balance' column to 'business.bank_accounts'
-- ----------------------------------------------------------------------------
ALTER TABLE business.bank_accounts
ADD COLUMN IF NOT EXISTS last_reconciled_balance NUMERIC(15,2) NULL;

COMMENT ON COLUMN business.bank_accounts.last_reconciled_balance IS 'The ending balance of the bank account as per the last successfully completed reconciliation.';


-- ----------------------------------------------------------------------------
-- 3. Add 'reconciled_bank_reconciliation_id' column to 'business.bank_transactions'
-- ----------------------------------------------------------------------------
ALTER TABLE business.bank_transactions
ADD COLUMN IF NOT EXISTS reconciled_bank_reconciliation_id INT NULL;

COMMENT ON COLUMN business.bank_transactions.reconciled_bank_reconciliation_id IS 'Foreign key to business.bank_reconciliations, linking a transaction to the specific reconciliation it was cleared in.';


-- ----------------------------------------------------------------------------
-- 4. Add Foreign Key Constraints for the new table and columns
-- ----------------------------------------------------------------------------

-- FK for business.bank_reconciliations table
ALTER TABLE business.bank_reconciliations
    ADD CONSTRAINT fk_br_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_br_created_by FOREIGN KEY (created_by_user_id) REFERENCES core.users(id);

-- FK for the new column in business.bank_transactions
ALTER TABLE business.bank_transactions
    ADD CONSTRAINT fk_bt_reconciliation FOREIGN KEY (reconciled_bank_reconciliation_id) REFERENCES business.bank_reconciliations(id) ON DELETE SET NULL;

-- Update schema version comment in a conceptual way (actual file versioning would be manual)
-- For tracking, this patch moves the schema towards 1.0.4.

COMMIT;

-- File: schema_update_patch.sql
-- Purpose: Updates SG Bookkeeper database schema from v1.0.4 to v1.0.5
-- Key Changes:
--   - Adds 'status' column to 'business.bank_reconciliations' table.
--   - Adds CHECK constraint for the 'status' column.
--
-- IMPORTANT:
--   - Backup your database before applying this patch.
--   - This patch is intended to be run ONCE on a database at schema v1.0.4.
--   - Do NOT append this to the main schema.sql file (v1.0.5) which already includes these changes.

BEGIN;

-- 1. Add 'status' column to 'business.bank_reconciliations'
-- Using IF NOT EXISTS for idempotency in case the column was manually added partially.
ALTER TABLE business.bank_reconciliations
ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'Draft';

COMMENT ON COLUMN business.bank_reconciliations.status IS 'The status of the reconciliation, e.g., Draft, Finalized. Default is Draft.';

-- 2. Add CHECK constraint for the 'status' column
-- This DO block makes adding the constraint idempotent.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_bank_reconciliations_status'
          AND conrelid = 'business.bank_reconciliations'::regclass
    ) THEN
        ALTER TABLE business.bank_reconciliations
        ADD CONSTRAINT ck_bank_reconciliations_status CHECK (status IN ('Draft', 'Finalized'));
    END IF;
END
$$;

-- Conceptually, update any internal schema version tracking if you have one.
-- For example (this is illustrative, not executable without a version table):
-- UPDATE core.schema_versions SET version = '1.0.5', applied_on = CURRENT_TIMESTAMP WHERE component = 'database';

DO $$
BEGIN
    RAISE NOTICE 'Database schema patch to v1.0.5 (BankReconciliation status) applied successfully.';
END $$;

COMMIT;

