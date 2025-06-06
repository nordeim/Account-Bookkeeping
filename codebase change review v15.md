**Goal:** Detail all code changes made since the "original codebase" was provided. This requires me to mentally "diff" the current state against the initial state of the files I've modified.

**Structure of the Status Update Document:**
A chronological or module-based approach would be logical. Module-based might be clearer for QA.
For each changed file:
*   File path.
*   Brief summary of the purpose of the changes.
*   Key code snippets showing before (if significantly different and illustrative) and after, or just the new/modified sections with explanations.
*   Focus on functional changes, bug fixes, and new feature implementations.

**Recalling Changes Made (Iterative Process):**

I need to go back through our interaction history and list the significant changes.

1.  **Initial Setup & Role Understanding**: This was meta, no code changes.
2.  **TDS Document Merging (response_50)**: This was a documentation task, not a codebase change.
3.  **Schema and Initial Data Update (response_51, based on user's patch)**:
    *   `scripts/schema.sql`: Updated to v1.0.5.
        *   Added `business.bank_reconciliations` table (including `status` column and `CHECK` constraint).
        *   Added `last_reconciled_balance` to `business.bank_accounts`.
        *   Added `reconciled_bank_reconciliation_id` to `business.bank_transactions`.
        *   Added relevant FK constraints.
        *   Updated comments.
    *   `scripts/initial_data.sql`: Updated to v1.0.5.
        *   Updated version comments. No functional data changes from the patch itself.
4.  **Circular Import Fixes (responses 52, 53, 54, 55, 56)**: This was a series of fixes.
    *   `app/accounting/chart_of_accounts_manager.py`: Changed direct `AccountService` import to `TYPE_CHECKING`.
    *   `app/accounting/journal_entry_manager.py`: Changed direct `AccountService`, `FiscalPeriodService` imports to `TYPE_CHECKING`.
    *   `app/business_logic/customer_manager.py`: Changed direct `CustomerService`, `AccountService`, `CurrencyService` imports to `TYPE_CHECKING`.
    *   `app/business_logic/vendor_manager.py`: Changed direct `VendorService`, `AccountService`, `CurrencyService` imports to `TYPE_CHECKING`.
    *   `app/business_logic/product_manager.py`: Changed direct `ProductService`, `AccountService`, `TaxCodeService` imports to `TYPE_CHECKING`.
    *   `app/business_logic/bank_account_manager.py`: Changed direct `BankAccountService`, `AccountService`, `CurrencyService` imports to `TYPE_CHECKING`.
    *   `app/business_logic/bank_transaction_manager.py`: Changed direct `BankTransactionService`, `BankAccountService` imports to `TYPE_CHECKING`.
    *   `app/business_logic/payment_manager.py`: Changed direct service imports to `TYPE_CHECKING`.
    *   `app/business_logic/sales_invoice_manager.py`: Changed direct service imports and `TaxCalculator` import to `TYPE_CHECKING`.
    *   `app/business_logic/purchase_invoice_manager.py`: Changed direct service imports and `TaxCalculator` import to `TYPE_CHECKING`.
    *   `app/tax/tax_calculator.py`: Changed direct `TaxCodeService` import to `TYPE_CHECKING`.
    *   `app/tax/gst_manager.py`: Changed direct service imports to `TYPE_CHECKING`.
    *   `app/tax/income_tax_manager.py`: Changed direct service imports to `TYPE_CHECKING`.
    *   `app/tax/withholding_tax_manager.py`: Changed direct service imports to `TYPE_CHECKING`.
    *   `app/reporting/financial_statement_generator.py`: Changed direct service imports to `TYPE_CHECKING`.
    *   `app/core/application_core.py`: Removed all top-level service imports, moved them to `TYPE_CHECKING`, and added local imports in `startup()`.
5.  **Bank Reconciliation Refinements (responses corresponding to user's recent_code_change-first, second, third, fourth):**
    *   **Backend for History Viewing (`recent_code_change_response-first.md` / my response_51 implicitly contained these service changes before UI):**
        *   `app/utils/pydantic_models.py`: Added `BankReconciliationSummaryData`.
        *   `app/services/__init__.py`: Updated `IBankReconciliationRepository` with `get_reconciliations_for_account` and `get_transactions_for_reconciliation`.
        *   `app/services/business_services.py` (`BankReconciliationService`): Implemented these methods, ensuring `get_reconciliations_for_account` filters for "Finalized" status.
    *   **UI for History Viewing (`recent_code_change_response-second.md` / my response_52 providing `BankReconciliationWidget`):**
        *   `app/ui/banking/bank_reconciliation_widget.py`: Implemented UI logic to call new history services and populate history tables, pagination, and detail views.
    *   **Backend for Draft/Provisional Matching (`recent_code_change_response-third.md` / my response_53):**
        *   `app/services/__init__.py` (`IBankReconciliationRepository`): Added `get_or_create_draft_reconciliation`, `mark_transactions_as_provisionally_reconciled`, `finalize_reconciliation`, `unreconcile_transactions`. Removed old `save_reconciliation_details`.
        *   `app/services/business_services.py` (`BankReconciliationService`): Implemented these new methods.
    *   **UI for Draft/Provisional Matching/Unmatching (`recent_code_change_response-fourth.md` / my response_54):**
        *   `app/ui/banking/bank_reconciliation_widget.py`: Major updates to use draft reconciliation flow, persist provisional matches, allow unmatching, and finalize drafts. Added new UI sections for provisionally matched items. Corrected amount matching logic.
6.  **Dashboard KPI Enhancements (responses 55, 56, 57, 58):**
    *   **DTO Update (`response_53` output, then corrected in `response_57` output):**
        *   `app/utils/pydantic_models.py` (`DashboardKPIData`): Added fields for AR/AP aging buckets, total current assets/liabilities, current ratio. Corrected missing `ar_aging_1_30`, `ap_aging_1_30`.
    *   **Service Layer (`response_53` output):**
        *   `app/services/__init__.py`: Added `get_ar_aging_summary` to `ICustomerRepository`, `get_ap_aging_summary` to `IVendorRepository`, `get_total_balance_by_account_category_and_type_pattern` to `IAccountRepository`. Added `get_by_gl_account_id` to `IBankAccountRepository` (fix for DashboardManager).
        *   `app/services/business_services.py`: Implemented `get_ar_aging_summary` in `CustomerService`, `get_ap_aging_summary` in `VendorService`. Implemented `get_by_gl_account_id` in `BankAccountService`.
        *   `app/services/account_service.py`: Implemented `get_total_balance_by_account_category_and_type_pattern`.
    *   **Manager Layer (`response_53` output):**
        *   `app/reporting/dashboard_manager.py`: Updated `get_dashboard_kpis` to use new services, calculate current ratio, populate extended DTO. Corrected logic for `_get_total_cash_balance` to use the newly added `get_by_gl_account_id` service method.
    *   **UI Layer (`response_54` output, then corrected in `response_56` for `QFormLayout` import, then in `response_57` for `kpi_data_result` typo):**
        *   `app/ui/dashboard/dashboard_widget.py`: Added UI elements (labels, group boxes) for new KPIs. Updated logic to display them. Fixed `QFormLayout` import and `kpi_data_result` typo.

This is a substantial list. For the `project status update document.md`, I will organize this by module/feature, highlighting key changes in each affected file.

```markdown
# Project Status Update Document

## Date: June 5, 2025

This document details significant code changes, enhancements, and bug fixes applied to the SG Bookkeeper application. It is intended for review by the QA team and other stakeholders to understand the evolution of the codebase.

## Table of Contents
1.  Database Schema & Initial Data Updates (to v1.0.5)
2.  Core Infrastructure: Circular Import Resolution
3.  Feature Enhancement: Bank Reconciliation Module
    *   Backend for History Viewing
    *   UI for History Viewing
    *   Backend for Draft Reconciliations & Provisional Matching
    *   UI for Draft Reconciliations & Provisional Matching (including Unmatch)
4.  Feature Enhancement: Dashboard KPIs
    *   DTO Updates for New KPIs
    *   Service Layer Enhancements for New KPIs
    *   Manager Layer Updates for New KPIs
    *   UI Layer Updates for New KPIs (Layout and Data Display)
5.  Bug Fixes

---

## 1. Database Schema & Initial Data Updates (to v1.0.5)

The database schema and initial data scripts were updated to support new features, primarily for the Bank Reconciliation module.

### 1.1 `scripts/schema.sql`
*   **Version**: Updated from v1.0.3 to v1.0.5.
*   **Key Changes**:
    *   **Added `business.bank_reconciliations` table**: Stores summary records of completed bank reconciliations. Includes fields like `bank_account_id`, `statement_date`, `statement_ending_balance`, `calculated_book_balance`, `reconciled_difference`, `status` (VARCHAR(20) with 'Draft', 'Finalized' CHECK constraint), `created_by_user_id`, and audit timestamps.
        ```sql
        CREATE TABLE business.bank_reconciliations (
            id SERIAL PRIMARY KEY,
            bank_account_id INTEGER NOT NULL,
            statement_date DATE NOT NULL, 
            statement_ending_balance NUMERIC(15,2) NOT NULL,
            calculated_book_balance NUMERIC(15,2) NOT NULL, 
            reconciled_difference NUMERIC(15,2) NOT NULL, 
            reconciliation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
            notes TEXT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'Draft', -- Added from 1.0.5 patch
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by_user_id INTEGER NOT NULL,
            CONSTRAINT uq_bank_reconciliation_account_statement_date UNIQUE (bank_account_id, statement_date),
            CONSTRAINT ck_bank_reconciliations_status CHECK (status IN ('Draft', 'Finalized')) -- Added from 1.0.5 patch
        );
        ```
    *   **Modified `business.bank_accounts` table**:
        *   Added `last_reconciled_balance NUMERIC(15,2) NULL`.
            ```sql
            ALTER TABLE business.bank_accounts
            ADD COLUMN IF NOT EXISTS last_reconciled_balance NUMERIC(15,2) NULL;
            -- Integrated into CREATE TABLE statement:
            -- last_reconciled_balance NUMERIC(15,2) NULL, -- Added from 1.0.4 patch
            ```
    *   **Modified `business.bank_transactions` table**:
        *   Added `reconciled_bank_reconciliation_id INT NULL` (FK to `bank_reconciliations.id`).
            ```sql
            ALTER TABLE business.bank_transactions
            ADD COLUMN IF NOT EXISTS reconciled_bank_reconciliation_id INT NULL;
            -- Integrated into CREATE TABLE statement:
            -- reconciled_bank_reconciliation_id INT NULL, -- Added from 1.0.4 patch
            ```
    *   **Added Foreign Key Constraints**: For the new `bank_reconciliations` table and the new columns.
        ```sql
        ALTER TABLE business.bank_reconciliations ADD CONSTRAINT fk_br_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id) ON DELETE CASCADE;
        ALTER TABLE business.bank_reconciliations ADD CONSTRAINT fk_br_created_by FOREIGN KEY (created_by_user_id) REFERENCES core.users(id);

        ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_reconciliation FOREIGN KEY (reconciled_bank_reconciliation_id) REFERENCES business.bank_reconciliations(id) ON DELETE SET NULL;
        ```
    *   **Audit Triggers**: The `audit.log_data_change_trigger_func` was extended to cover the new `business.bank_reconciliations` table.
        ```diff
        -        'business.bank_accounts', 'business.bank_transactions' -- Added banking tables
        +        'business.bank_accounts', 'business.bank_transactions', 'business.bank_reconciliations' -- Added bank_reconciliations
        ```
    *   Version comments at the top of the file were updated to reflect v1.0.5 and summarize changes.

### 1.2 `scripts/initial_data.sql`
*   **Version**: Updated from v1.0.3 to v1.0.5.
*   **Key Changes**:
    *   Updated version comments at the top of the file.
    *   No functional data changes were introduced by the schema patches 1.0.4 or 1.0.5. Existing permissions for banking/reconciliation (e.g., `BANK_RECONCILE`) were deemed sufficient.

---

## 2. Core Infrastructure: Circular Import Resolution

A series of circular import errors (`ImportError: cannot import name 'X' from partially initialized module 'Y' (most likely due to a circular import)`) were systematically resolved. This involved refactoring how services are imported and type-hinted in manager classes and in `ApplicationCore`.

**General Fix Pattern Applied:**
1.  Direct module-level imports of service classes (e.g., `from app.services.some_service import SomeService`) used for constructor type hints in manager classes (or `ApplicationCore`) were removed.
2.  These service class imports were moved into an `if TYPE_CHECKING:` block within the respective manager/core file.
3.  Constructor type hints for these injected services were changed to use string literals (e.g., `__init__(self, some_service: "SomeService", ...)`).

**Affected Files & Summary of Changes:**

*   **`app/core/application_core.py`**:
    *   Removed all direct top-level service class imports.
    *   Added all service class names to the `if TYPE_CHECKING:` block for property type hinting.
    *   In the `startup()` method, services are now imported locally just before their instantiation.
    *   Property type hints were updated to use string literals or rely on `TYPE_CHECKING` imports.

*   **Manager Classes** (primarily in `app/business_logic/`, `app/accounting/`, `app/tax/`, `app/reporting/`):
    *   **`app/accounting/chart_of_accounts_manager.py`**: Modified `AccountService` import.
    *   **`app/accounting/journal_entry_manager.py`**: Modified `AccountService` and `FiscalPeriodService` imports.
    *   **`app/business_logic/customer_manager.py`**: Modified `CustomerService`, `AccountService`, `CurrencyService` imports.
    *   **`app/business_logic/vendor_manager.py`**: Modified `VendorService`, `AccountService`, `CurrencyService` imports.
    *   **`app/business_logic/product_manager.py`**: Modified `ProductService`, `AccountService`, `TaxCodeService` imports.
    *   **`app/business_logic/bank_account_manager.py`**: Modified `BankAccountService`, `AccountService`, `CurrencyService` imports.
    *   **`app/business_logic/bank_transaction_manager.py`**: Modified `BankTransactionService`, `BankAccountService` imports.
    *   **`app/business_logic/payment_manager.py`**: Modified imports for its numerous service dependencies.
    *   **`app/business_logic/sales_invoice_manager.py`**: Modified imports for its numerous service dependencies and `TaxCalculator`.
    *   **`app/business_logic/purchase_invoice_manager.py`**: Modified imports for its numerous service dependencies and `TaxCalculator`.
    *   **`app/tax/tax_calculator.py`**: Modified `TaxCodeService` import.
    *   **`app/tax/gst_manager.py`**: Modified imports for its service dependencies.
    *   **`app/tax/income_tax_manager.py`**: Modified imports for its service dependencies.
    *   **`app/tax/withholding_tax_manager.py`**: Modified imports for its service dependencies.
    *   **`app/reporting/financial_statement_generator.py`**: Modified imports for its numerous service dependencies.

    *Example Snippet (from `customer_manager.py`):*
    ```diff
    --- a/app/business_logic/customer_manager.py
    +++ b/app/business_logic/customer_manager.py
    @@ -2,16 +2,16 @@
     from typing import List, Optional, Dict, Any, TYPE_CHECKING
     from decimal import Decimal
     
     from app.models.business.customer import Customer
    -# from app.services.business_services import CustomerService
    -# from app.services.account_service import AccountService 
    -# from app.services.accounting_services import CurrencyService 
    +# REMOVED: from app.services.business_services import CustomerService
    +# REMOVED: from app.services.account_service import AccountService 
    +# REMOVED: from app.services.accounting_services import CurrencyService 
     from app.utils.result import Result
     from app.utils.pydantic_models import CustomerCreateData, CustomerUpdateData, CustomerSummaryData
     
     if TYPE_CHECKING:
         from app.core.application_core import ApplicationCore
+        from app.services.business_services import CustomerService # ADDED
+        from app.services.account_service import AccountService # ADDED
+        from app.services.accounting_services import CurrencyService # ADDED
     
     class CustomerManager:
         def __init__(self, 
    -                 customer_service: CustomerService, 
    -                 account_service: AccountService, 
    -                 currency_service: CurrencyService, 
    +                 customer_service: "CustomerService", 
    +                 account_service: "AccountService", 
    +                 currency_service: "CurrencyService", 
                      app_core: "ApplicationCore"):
             self.customer_service = customer_service
             self.account_service = account_service
    ```

**Impact**: These changes resolved the startup `ImportError`s and made the application's import structure more robust and less prone to such cycles.

---

## 3. Feature Enhancement: Bank Reconciliation Module

Significant enhancements were made to the Bank Reconciliation module, evolving it from a basic structure to a more functional feature.

### 3.1 Backend for History Viewing
*   **`app/utils/pydantic_models.py`**:
    *   Added `BankReconciliationSummaryData` DTO to represent summarized past reconciliations for list views.
        Fields: `id`, `statement_date`, `statement_ending_balance`, `reconciled_difference`, `reconciliation_date`, `created_by_username`.
*   **`app/services/__init__.py`**:
    *   Updated `IBankReconciliationRepository` interface with new methods:
        *   `get_reconciliations_for_account`: To fetch paginated, finalized reconciliation summaries.
        *   `get_transactions_for_reconciliation`: To fetch statement and system transactions linked to a specific reconciliation.
*   **`app/services/business_services.py` (`BankReconciliationService`)**:
    *   Implemented `get_reconciliations_for_account`: Queries `BankReconciliation` records, filters by `bank_account_id` and `status='Finalized'`, performs a join to `User` to get the username, handles pagination, and returns `BankReconciliationSummaryData` DTOs along with total record count.
    *   Implemented `get_transactions_for_reconciliation`: Queries `BankTransaction` records filtered by `reconciled_bank_reconciliation_id`, separates them into statement items and system items, and returns them as `BankTransactionSummaryData` DTOs.

### 3.2 UI for History Viewing
*   **`app/ui/banking/bank_reconciliation_widget.py`**:
    *   The UI was already structured with tables and pagination controls for history.
    *   Logic was implemented to:
        *   Call `_load_reconciliation_history(page_number)` when a bank account is selected or when pagination buttons are clicked.
        *   `_fetch_reconciliation_history()` now calls the corresponding service method and updates the `history_table_model` and pagination controls.
        *   `_on_history_selection_changed()` triggers loading of detailed transactions for the selected historical reconciliation.
        *   `_load_historical_reconciliation_details()` calls the service and `_update_history_detail_tables_slot()` populates the detail tables (`_history_statement_txns_model`, `_history_system_txns_model`) and makes the detail group box visible.

### 3.3 Backend for Draft Reconciliations & Provisional Matching
*   **`app/services/__init__.py` (`IBankReconciliationRepository`)**:
    *   Added new method signatures:
        *   `get_or_create_draft_reconciliation(...) -> BankReconciliation`
        *   `mark_transactions_as_provisionally_reconciled(...) -> bool`
        *   `finalize_reconciliation(...) -> Result[BankReconciliation]`
        *   `unreconcile_transactions(...) -> bool`
    *   Removed the older, broader `save_reconciliation_details` method.
*   **`app/services/business_services.py` (`BankReconciliationService`)**:
    *   Implemented `get_or_create_draft_reconciliation`: Finds an existing 'Draft' reconciliation for the given account/date or creates a new one.
    *   Implemented `mark_transactions_as_provisionally_reconciled`: Updates `BankTransaction` records to link them to a draft reconciliation ID, set `is_reconciled=True`, and `reconciled_date`.
    *   Implemented `finalize_reconciliation`: Updates a draft reconciliation's status to 'Finalized', saves final balance figures, and updates the linked `BankAccount`'s `last_reconciled_date` and `last_reconciled_balance`.
    *   Implemented `unreconcile_transactions`: Clears reconciliation fields on specified `BankTransaction` records.

### 3.4 UI for Draft Reconciliations & Provisional Matching (including Unmatch)
*   **`app/ui/banking/bank_reconciliation_widget.py`**:
    *   **Draft Management**:
        *   `_fetch_and_populate_transactions` now first calls `get_or_create_draft_reconciliation` and stores the `_current_draft_reconciliation_id`.
        *   The "Load / Refresh Transactions" button also triggers this draft retrieval/creation.
    *   **Provisional Matching**:
        *   `_on_match_selected_clicked`: Corrected amount matching logic to `abs(sum_stmt_amounts - sum_sys_amounts) < tolerance`. It now calls `_perform_provisional_match`.
        *   `_perform_provisional_match`: Calls `mark_transactions_as_provisionally_reconciled` service method. On success, reloads all transaction lists.
    *   **Unmatching**:
        *   Added new UI sections ("Provisionally Matched Statement Items (This Session)", "Provisionally Matched System Transactions (This Session)") with tables (`draft_matched_statement_table`, `draft_matched_system_table`) using `ReconciliationTableModel`.
        *   Added "Unmatch Selected Items" button (`self.unmatch_button`).
        *   `_fetch_and_populate_transactions` now also populates these new tables with items linked to `_current_draft_reconciliation_id`.
        *   `_on_unmatch_selected_clicked` collects selections from these new tables and calls `_perform_unmatch`.
        *   `_perform_unmatch` calls `unreconcile_transactions` service method and refreshes UI.
    *   **Finalizing**:
        *   `_perform_finalize_reconciliation` (formerly `_perform_save_reconciliation`) now calls `finalize_reconciliation` service method using `_current_draft_reconciliation_id`. It clears the draft ID on success. Button text changed to "Save Final Reconciliation".

---

## 4. Feature Enhancement: Dashboard KPIs

The Dashboard was enhanced to display AR/AP Aging summaries and the Current Ratio.

### 4.1 DTO Updates
*   **`app/utils/pydantic_models.py` (`DashboardKPIData`)**:
    *   Added new fields for AR and AP aging buckets: `ar_aging_current`, `ar_aging_1_30`, `ar_aging_31_60`, `ar_aging_61_90`, `ar_aging_91_plus`, and similar for `ap_aging_*`.
    *   Added fields for Current Ratio components: `total_current_assets`, `total_current_liabilities`.
    *   Added `current_ratio: Optional[Decimal]`.

### 4.2 Service Layer Enhancements
*   **`app/services/__init__.py` (Interfaces)**:
    *   `ICustomerRepository`: Added `get_ar_aging_summary(as_of_date: date) -> Dict[str, Decimal]`.
    *   `IVendorRepository`: Added `get_ap_aging_summary(as_of_date: date) -> Dict[str, Decimal]`.
    *   `IAccountRepository`: Added `get_total_balance_by_account_category_and_type_pattern(...) -> Decimal`.
    *   `IBankAccountRepository`: Added `get_by_gl_account_id(...) -> Optional[BankAccount]`.
*   **`app/services/business_services.py`**:
    *   `CustomerService`: Implemented `get_ar_aging_summary` to query outstanding `SalesInvoice` records and categorize their balances into aging buckets ("Current", "1-30 Days", "31-60 Days", "61-90 Days", "91+ Days") based on `as_of_date` and `due_date`.
    *   `VendorService`: Implemented `get_ap_aging_summary` with similar logic for `PurchaseInvoice` records.
    *   `BankAccountService`: Implemented `get_by_gl_account_id` to find a bank account linked to a specific GL account ID.
*   **`app/services/account_service.py`**:
    *   Implemented `get_total_balance_by_account_category_and_type_pattern`: Fetches active accounts matching a category (e.g., 'Asset') and a sub_type name pattern (e.g., 'Current Asset%'), then sums their balances as of a given date using `JournalService.get_account_balance`.

### 4.3 Manager Layer Updates
*   **`app/reporting/dashboard_manager.py` (`DashboardManager`)**:
    *   `get_dashboard_kpis()` method was significantly updated:
        *   Calls the new aging summary methods from `CustomerService` and `VendorService`.
        *   Calculates `total_current_assets` and `total_current_liabilities` by:
            *   Fetching all active accounts via `AccountService`.
            *   Iterating them, checking `account_type` and `sub_type` against predefined lists (`CURRENT_ASSET_SUBTYPES`, `CURRENT_LIABILITY_SUBTYPES`).
            *   Summing balances obtained via `JournalService.get_account_balance`.
        *   Calculates `current_ratio` (handles division by zero by setting ratio to `Decimal('Infinity')` or `None`).
        *   Populates all new fields in the `DashboardKPIData` DTO.
    *   `_get_total_cash_balance()` method was corrected to use the new `BankAccountService.get_by_gl_account_id` method to avoid double-counting cash if the "Cash on Hand" GL is linked to a bank account.

### 4.4 UI Layer Updates
*   **`app/ui/dashboard/dashboard_widget.py` (`DashboardWidget`)**:
    *   **`_init_ui()`**:
        *   Added `QFormLayout` import.
        *   Added `QScrollArea` for better layout with more KPIs.
        *   Rearranged existing KPIs into a two-column `QGridLayout`.
        *   Added new `QGroupBox` sections for "AR Aging Summary" and "AP Aging Summary".
        *   Within these groups, added `QLabel`s for each aging bucket (Current, 1-30, 31-60, 61-90, 91+ days).
        *   Added a new `QLabel` for "Current Ratio".
    *   **`_request_kpi_load()`**: Extended the `labels_to_reset` list to include all new UI labels.
    *   **`_update_kpi_display_slot()`**: Updated to populate the text of new labels using data from the extended `DashboardKPIData` DTO. Includes formatting for the Current Ratio (e.g., "1.50 : 1" or "N/A").
    *   **`_format_decimal_for_display()`**: Improved to handle `Decimal('Infinity')`.
    *   **Bug Fix**: Corrected a typo in `_fetch_kpis_data` from `kpi_data_dto.model_dump_json()` to `kpi_data_result.model_dump_json()`.

---

## 5. Bug Fixes
*   **`NameError: name 'QFormLayout' is not defined`** in `app/ui/dashboard/dashboard_widget.py`: Fixed by adding `QFormLayout` to imports from `PySide6.QtWidgets`.
*   **`NameError: name 'kpi_data_dto' is not defined`** in `app/ui/dashboard/dashboard_widget.py` (`_fetch_kpis_data`): Fixed by changing to `kpi_data_result.model_dump_json()`.
*   **`AttributeError: 'BankAccountService' object has no attribute 'get_by_gl_account_id'`**: Fixed by adding the `get_by_gl_account_id` method to `IBankAccountRepository` and `BankAccountService`.

---

This concludes the summary of significant changes. The application is now more feature-rich, particularly in bank reconciliation and dashboard insights, and its import structure is more robust.
```

