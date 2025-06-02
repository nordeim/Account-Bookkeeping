<think>
The user is, quite rightly, pointing out that my previous attempt (response_32) to provide a complete `scripts/schema.sql` file was still flawed and, based on their feedback, again degenerated into a diff-like format with omissions. This is a persistent failure on my part for this specific large file, despite my stated intentions.

**The core problem seems to be my inability to reliably output a *large, fully preserved file with minor surgical additions/modifications* without accidentally truncating it or outputting my internal diff representation.**

The user is now wisely asking for a **schema patch file in SQL** instead of the full schema. This is a much more manageable task for me and less prone to the "full file omission" error.

**My Task:**
1.  Identify the *exact* DDL changes needed to upgrade the schema from version 1.0.3 (from response_22, which is `scripts/schema.sql-previous` in the user's diffs) to version 1.0.4 (to support saving bank reconciliation state).
2.  Generate a SQL patch file containing *only these DDL changes*.
3.  Ensure this patch is correct, idempotent where possible (e.g., using `IF NOT EXISTS` for columns/tables, though standard SQL `ALTER TABLE` for adding columns doesn't have `IF NOT EXISTS`), and achieves the desired schema state for v1.0.4 features.

**Recap of DDL Changes needed for Version 1.0.4 (Bank Reconciliation Save State):**

1.  **New Table**: `business.bank_reconciliations`
2.  **New Column in `business.bank_accounts`**: `last_reconciled_balance NUMERIC(15,2) NULL`
3.  **New Column in `business.bank_transactions`**: `reconciled_bank_reconciliation_id INT NULL`
4.  **New Foreign Key Constraints**:
    *   `bank_reconciliations.bank_account_id` -> `bank_accounts.id`
    *   `bank_reconciliations.created_by_user_id` -> `core.users.id`
    *   `bank_transactions.reconciled_bank_reconciliation_id` -> `bank_reconciliations.id`

**Plan for Generating the SQL Patch File:**

1.  **[ ] Header for Patch File**: Add comments indicating the purpose and versions this patch transitions between.
2.  **[ ] `CREATE TABLE business.bank_reconciliations`**: Write the full `CREATE TABLE` statement.
3.  **[ ] `ALTER TABLE business.bank_accounts`**:
    *   Use `ADD COLUMN last_reconciled_balance NUMERIC(15,2) NULL;`
    *   Consider adding `IF NOT EXISTS` if the RDBMS supports it for `ADD COLUMN` (PostgreSQL does not directly, but we can check if the column exists first in a `DO` block if we want to make it re-runnable, or assume it's a one-time patch). For a patch, direct `ADD COLUMN` is usually fine.
4.  **[ ] `ALTER TABLE business.bank_transactions`**:
    *   Use `ADD COLUMN reconciled_bank_reconciliation_id INT NULL;`
5.  **[ ] `ALTER TABLE ... ADD CONSTRAINT`**: Add the three foreign key constraints.
6.  **[ ] No other DDL**: The patch should *only* contain these additions/alterations. It should not redefine existing tables, views, or functions unless it's a direct modification (which is not the case here, apart from adding columns).
7.  **[ ] Validation**:
    *   SQL Syntax: Ensure all statements are valid PostgreSQL.
    *   Correctness: Ensure the changes accurately reflect the requirements for v1.0.4.
    *   Idempotency: While `ALTER TABLE ADD COLUMN` isn't idempotent by default, the script is intended as a one-time patch. The FK constraints will fail if run twice, which is acceptable for a patch. `CREATE TABLE IF NOT EXISTS` could be used for the new table for better re-runnability.
    *   Completeness of Patch: Ensure all *necessary* changes for v1.0.4 are included.

**Pre-computation/Pre-analysis (Self-Correction/Double Checking):**

*   The base schema (v1.0.3 from response_22) already includes:
    *   `is_from_statement` and `raw_statement_data` in `business.bank_transactions`.
    *   The bank balance update trigger (`business.update_bank_account_balance_trigger_func` and its application).
    *   The corrected `accounting.trial_balance` view.
    *   Audit logging for banking tables.
    *   These must NOT be part of the patch, as they are already in the base schema we're patching *from*.

*   The patch should solely focus on adding the `bank_reconciliations` table and the linking columns/FKs.

Let's construct the patch carefully. I will use `CREATE TABLE IF NOT EXISTS` for the new table to make the patch more robust if run multiple times (though other parts like `ADD COLUMN` would error on a second run if not guarded).
</think>

You are absolutely correct to be frustrated and to demand a higher level of precision, especially with a critical file like `scripts/schema.sql`. My apologies for the repeated failure to provide a truly complete and clean version of this file in my previous responses. The inclusion of diff markers or placeholder comments was a significant error, and I understand that this has been an impediment.

I will now strictly adhere to your request for a **schema patch file in SQL**. This approach is indeed more robust for applying targeted changes and avoids the pitfalls I've encountered with regenerating the entire large schema file.

My commitment to a meticulous, rigorous, and systematic approach, including thorough validation, remains paramount. I will focus intently on generating only the necessary DDL changes to upgrade your schema from version 1.0.3 (which includes the bank statement import fields and the corrected trial balance view) to version 1.0.4 (which adds support for saving bank reconciliation states).

**Plan for SQL Patch File (Upgrading Schema from v1.0.3 to v1.0.4):**

1.  **Add `business.bank_reconciliations` table**: This table will store the summary of each completed reconciliation.
2.  **Add `last_reconciled_balance` column** to `business.bank_accounts` table.
3.  **Add `reconciled_bank_reconciliation_id` column** to `business.bank_transactions` table.
4.  **Add Foreign Key constraints** for the new table and columns.
5.  Include comments to indicate the purpose and versioning of the patch.

I will ensure this patch file is clean, correct, and contains only the DDL modifications required for this specific upgrade.

---
**SQL Patch File (Upgrade Schema from v1.0.3 to v1.0.4)**
---

```sql
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

```

**Validation of the SQL Patch File:**

*   **Correctness of Changes**:
    *   The `CREATE TABLE IF NOT EXISTS business.bank_reconciliations` statement accurately defines the new table with all necessary columns, types, constraints (PK, NOT NULL, UNIQUE).
    *   The `ALTER TABLE business.bank_accounts ADD COLUMN IF NOT EXISTS last_reconciled_balance ...` correctly adds the new nullable column. `IF NOT EXISTS` makes this part idempotent.
    *   The `ALTER TABLE business.bank_transactions ADD COLUMN IF NOT EXISTS reconciled_bank_reconciliation_id ...` correctly adds the new nullable foreign key column. `IF NOT EXISTS` makes this part idempotent.
    *   The `ALTER TABLE ... ADD CONSTRAINT` statements correctly define the foreign key relationships for `bank_reconciliations` to `bank_accounts` and `core.users`, and for `bank_transactions` to `bank_reconciliations`. `ON DELETE CASCADE` for `bank_reconciliations.bank_account_id` means if a bank account is deleted, its reconciliation records are also deleted. `ON DELETE SET NULL` for `bank_transactions.reconciled_bank_reconciliation_id` means if a reconciliation record is deleted (which should be rare and controlled), the linked transactions won't be deleted but their link will be nullified. This is a reasonable default.
*   **Completeness of Patch for v1.0.4**: The patch includes all DDL changes identified as necessary for the "Save Reconciliation State" feature.
*   **No Omissions from v1.0.3**: Being a patch file, it correctly *does not* redefine or touch any other existing tables, views, functions, or triggers from the v1.0.3 schema, thus preserving them.
*   **Idempotency**: `CREATE TABLE IF NOT EXISTS` and `ADD COLUMN IF NOT EXISTS` help make parts of the script re-runnable without error if those specific objects/columns already exist. Standard `ADD CONSTRAINT` will error if the constraint already exists, which is typical for patches.
*   **Comments**: The patch includes clear comments regarding its purpose and versioning.

This SQL patch file should correctly upgrade your database schema from version 1.0.3 to incorporate the necessary structures for version 1.0.4. Please apply it carefully after backing up your database.
