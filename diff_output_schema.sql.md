Below is "diff" command output comparing the previous version with your latest generated version. Please double-check and validate that the changes are valid and that no other original features or functions are lost (omitted). use the same rigorous and meticulous approach to review the diff output below.

```diff
$ diff -u scripts/schema.sql.bak scripts/schema.sql
--- scripts/schema.sql.bak      2025-06-02 13:37:34.438069782 +0800
+++ scripts/schema.sql  2025-06-04 18:50:55.248484950 +0800
@@ -1,14 +1,22 @@
 -- File: scripts/schema.sql
 -- ============================================================================
--- SG Bookkeeper - Complete Database Schema - Version 1.0.3
--- (Schema version updated for bank_transactions fields & corrected trial_balance view)
+-- SG Bookkeeper - Complete Database Schema - Version 1.0.5
 -- ============================================================================
 -- This script creates the complete database schema for the SG Bookkeeper application.
--- Changes from 1.0.2:
---  - Corrected accounting.trial_balance view logic.
--- Changes from 1.0.1 (incorporated in 1.0.2):
---  - Added is_from_statement and raw_statement_data to business.bank_transactions
---  - Added trigger for automatic bank_account balance updates.
+-- Base version for this consolidated file was 1.0.3.
+--
+-- Changes from 1.0.3 to 1.0.4 (incorporated):
+--  - Added business.bank_reconciliations table (for saving reconciliation state).
+--  - Added last_reconciled_balance to business.bank_accounts.
+--  - Added reconciled_bank_reconciliation_id to business.bank_transactions.
+--  - Added relevant FK constraints for reconciliation features.
+--
+-- Changes from 1.0.4 to 1.0.5 (incorporated):
+--  - Added status VARCHAR(20) NOT NULL DEFAULT 'Draft' with CHECK constraint to business.bank_reconciliations.
+--
+-- Features from 1.0.3 (base for this file):
+--  - Schema version updated for bank_transactions fields (is_from_statement, raw_statement_data) & corrected trial_balance view logic.
+--  - Trigger for automatic bank_account balance updates.
 --  - Extended audit logging to bank_accounts and bank_transactions.
 -- ============================================================================
 
@@ -436,7 +444,26 @@
 CREATE INDEX idx_purchase_invoice_lines_invoice ON business.purchase_invoice_lines(invoice_id); CREATE INDEX idx_purchase_invoice_lines_product ON business.purchase_invoice_lines(product_id);
 
 CREATE TABLE business.bank_accounts (
-    id SERIAL PRIMARY KEY, account_name VARCHAR(100) NOT NULL, account_number VARCHAR(50) NOT NULL, bank_name VARCHAR(100) NOT NULL, bank_branch VARCHAR(100), bank_swift_code VARCHAR(20), currency_code CHAR(3) NOT NULL, opening_balance NUMERIC(15,2) DEFAULT 0, current_balance NUMERIC(15,2) DEFAULT 0, last_reconciled_date DATE, gl_account_id INTEGER NOT NULL, is_active BOOLEAN DEFAULT TRUE, description TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
+    id SERIAL PRIMARY KEY, 
+    account_name VARCHAR(100) NOT NULL, 
+    account_number VARCHAR(50) NOT NULL, 
+    bank_name VARCHAR(100) NOT NULL, 
+    bank_branch VARCHAR(100), 
+    bank_swift_code VARCHAR(20), 
+    currency_code CHAR(3) NOT NULL, 
+    opening_balance NUMERIC(15,2) DEFAULT 0, 
+    current_balance NUMERIC(15,2) DEFAULT 0, 
+    last_reconciled_date DATE, 
+    last_reconciled_balance NUMERIC(15,2) NULL, -- Added from 1.0.4 patch
+    gl_account_id INTEGER NOT NULL, 
+    is_active BOOLEAN DEFAULT TRUE, 
+    description TEXT, 
+    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
+    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
+    created_by INTEGER NOT NULL, 
+    updated_by INTEGER NOT NULL
+);
+COMMENT ON COLUMN business.bank_accounts.last_reconciled_balance IS 'The ending balance of the bank account as per the last successfully completed reconciliation.';
 
 CREATE TABLE business.bank_transactions (
     id SERIAL PRIMARY KEY, 
@@ -451,8 +478,9 @@
     reconciled_date DATE, 
     statement_date DATE, 
     statement_id VARCHAR(50), 
-    is_from_statement BOOLEAN NOT NULL DEFAULT FALSE, -- New column
-    raw_statement_data JSONB NULL, -- New column
+    is_from_statement BOOLEAN NOT NULL DEFAULT FALSE, -- From 1.0.2
+    raw_statement_data JSONB NULL, -- From 1.0.2
+    reconciled_bank_reconciliation_id INT NULL, -- Added from 1.0.4 patch
     journal_entry_id INTEGER, 
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
@@ -462,6 +490,29 @@
 CREATE INDEX idx_bank_transactions_account ON business.bank_transactions(bank_account_id); 
 CREATE INDEX idx_bank_transactions_date ON business.bank_transactions(transaction_date); 
 CREATE INDEX idx_bank_transactions_reconciled ON business.bank_transactions(is_reconciled);
+COMMENT ON COLUMN business.bank_transactions.reconciled_bank_reconciliation_id IS 'Foreign key to business.bank_reconciliations, linking a transaction to the specific reconciliation it was cleared in.';
+
+CREATE TABLE business.bank_reconciliations (
+    id SERIAL PRIMARY KEY,
+    bank_account_id INTEGER NOT NULL,
+    statement_date DATE NOT NULL, 
+    statement_ending_balance NUMERIC(15,2) NOT NULL,
+    calculated_book_balance NUMERIC(15,2) NOT NULL, 
+    reconciled_difference NUMERIC(15,2) NOT NULL, 
+    reconciliation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
+    notes TEXT NULL,
+    status VARCHAR(20) NOT NULL DEFAULT 'Draft', -- Added from 1.0.5 patch
+    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
+    created_by_user_id INTEGER NOT NULL,
+    CONSTRAINT uq_bank_reconciliation_account_statement_date UNIQUE (bank_account_id, statement_date),
+    CONSTRAINT ck_bank_reconciliations_status CHECK (status IN ('Draft', 'Finalized')) -- Added from 1.0.5 patch
+);
+COMMENT ON TABLE business.bank_reconciliations IS 'Stores summary records of completed bank reconciliations.';
+COMMENT ON COLUMN business.bank_reconciliations.statement_date IS 'The end date of the bank statement that was reconciled.';
+COMMENT ON COLUMN business.bank_reconciliations.calculated_book_balance IS 'The book balance of the bank account as of the statement_date, after all reconciling items for this reconciliation are accounted for.';
+COMMENT ON COLUMN business.bank_reconciliations.status IS 'The status of the reconciliation, e.g., Draft, Finalized. Default is Draft.';
+
 
 CREATE TABLE business.payments (
     id SERIAL PRIMARY KEY, payment_no VARCHAR(20) NOT NULL UNIQUE, payment_type VARCHAR(20) NOT NULL CHECK (payment_type IN ('Customer Payment', 'Vendor Payment', 'Refund', 'Credit Note', 'Other')), payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('Cash', 'Check', 'Bank Transfer', 'Credit Card', 'GIRO', 'PayNow', 'Other')), payment_date DATE NOT NULL, entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('Customer', 'Vendor', 'Other')), entity_id INTEGER NOT NULL, bank_account_id INTEGER, currency_code CHAR(3) NOT NULL, exchange_rate NUMERIC(15,6) DEFAULT 1, amount NUMERIC(15,2) NOT NULL, reference VARCHAR(100), description TEXT, cheque_no VARCHAR(50), status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Approved', 'Completed', 'Voided', 'Returned')), journal_entry_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
@@ -613,9 +664,13 @@
 
 ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id);
 ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
+ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_reconciliation FOREIGN KEY (reconciled_bank_reconciliation_id) REFERENCES business.bank_reconciliations(id) ON DELETE SET NULL; -- Added from 1.0.4 patch
 ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
 ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
 
+ALTER TABLE business.bank_reconciliations ADD CONSTRAINT fk_br_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id) ON DELETE CASCADE; -- Added from 1.0.4 patch
+ALTER TABLE business.bank_reconciliations ADD CONSTRAINT fk_br_created_by FOREIGN KEY (created_by_user_id) REFERENCES core.users(id); -- Added from 1.0.4 patch
+
 ALTER TABLE business.payments ADD CONSTRAINT fk_pay_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id);
 ALTER TABLE business.payments ADD CONSTRAINT fk_pay_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
 ALTER TABLE business.payments ADD CONSTRAINT fk_pay_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
@@ -892,7 +947,7 @@
         'business.sales_invoices', 'business.purchase_invoices', 'business.payments',
         'accounting.tax_codes', 'accounting.gst_returns',
         'core.users', 'core.roles', 'core.company_settings', 
-        'business.bank_accounts', 'business.bank_transactions' -- Added banking tables
+        'business.bank_accounts', 'business.bank_transactions', 'business.bank_reconciliations' -- Added bank_reconciliations
     ];
     table_fullname TEXT;
     schema_name TEXT;
```

```diff
$ diff -u scripts/initial_data.sql.bak scripts/initial_data.sql
--- scripts/initial_data.sql.bak        2025-06-02 14:11:35.858218657 +0800
+++ scripts/initial_data.sql    2025-06-04 18:51:28.384672171 +0800
@@ -1,6 +1,11 @@
 -- File: scripts/initial_data.sql
 -- ============================================================================
--- INITIAL DATA (Version 1.0.3 - Added sequence grants for audit schema)
+-- INITIAL DATA (Version 1.0.5)
+-- ============================================================================
+-- This version corresponds to schema version 1.0.5.
+-- No functional data changes were introduced by schema patches 1.0.4 or 1.0.5.
+-- Existing permissions for banking/reconciliation were already present in v1.0.3.
+-- Version 1.0.3 (base) added sequence grants for audit schema.
 -- ============================================================================
 
 -- Ensure this script is run by a superuser or the owner of the database/schemas
```

