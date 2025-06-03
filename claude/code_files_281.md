<think>
The user wants two things:
1.  An updated `Project Architecture Document (v2).md` reflecting the latest code changes (from `changes_to_codebase_corresponding_to_schema_v1.04.md`). I need to meticulously review this new set of files, identify changes, and incorporate them into the architecture document. Special attention must be paid to the schema and initial data updates to ensure completeness and correctness against their previous states.
2.  A fix for the `IndentationError` in `app/services/__init__.py`.

Let's tackle the error first, as it's preventing the application from running.

**Error Analysis: `IndentationError`**

*   **File**: `app/services/__init__.py`
*   **Line**: 265 (as reported by the traceback)
*   **Error**: `IndentationError: expected an indented block after function definition on line 263`
*   **Context**: The traceback points to the definition of `IPaymentRepository`. Line 263 is likely the start of this class definition or a method within it. An `IndentationError` means Python expected an indented block (e.g., after a `class` or `def` statement) but didn't find one, or found incorrect indentation.

Let's examine the `IPaymentRepository` definition in `app/services/__init__.py` from the last provided file set (`changes_to_codebase_corresponding_to_schema_v1.04.md`).

```python
# File: app/services/__init__.py
# ... (previous interfaces) ...

class IPaymentRepository(IRepository[Payment, int]):
    @abstractmethod
    async def get_by_payment_no(self, payment_no: str) -> Optional[Payment]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              entity_type: Optional[PaymentEntityTypeEnum] = None,
                              entity_id: Optional[int] = None,
                              status: Optional[PaymentStatusEnum] = None,
                              start_date: Optional[date] = None,
                              end_date: Optional[date] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[PaymentSummaryData]: pass
    @abstractmethod
    async def save(self, entity: Payment, session: Optional[AsyncSession] = None) -> Payment: # Updated type hint

# (Line 263 or around here based on traceback)
class IAuditLogRepository(IRepository[AuditLog, int]): # This should be line 265 based on typical interface definitions
    @abstractmethod
    async def get_audit_logs_paginated(
        # ...
    ) -> Tuple[List[AuditLogEntryData], int]: pass 

class IDataChangeHistoryRepository(IRepository[DataChangeHistory, int]):
    # ...
    pass 

class IBankReconciliationRepository(IRepository[BankReconciliation, int]):
    @abstractmethod
    async def save_reconciliation_details(
        # ...
        session: AsyncSession # Problematic line from previous fix was here
    ) -> BankReconciliation: pass

# ... (service imports and __all__)
```

Looking at the traceback, the error is `IndentationError: expected an indented block after function definition on line 263`.
The provided `app/services/__init__.py` in `changes_to_codebase_corresponding_to_schema_v1.04.md` seems to have the following structure around the area of interest (IPaymentRepository, IAuditLogRepository, IDataChangeHistoryRepository, IBankReconciliationRepository).

The traceback points to line 265 for `class IPaymentRepository(IRepository[Payment, int]):` being the start of the problematic context, and the error occurring because an expected indented block after a function definition on line 263 wasn't found.

Let's review the provided `app/services/__init__.py` from `changes_to_codebase_corresponding_to_schema_v1.04.md` (this is what I'm supposed to be working with now):

```python
# File: app/services/__init__.py
# ...
class IPaymentRepository(IRepository[Payment, int]):
    @abstractmethod
    async def get_by_payment_no(self, payment_no: str) -> Optional[Payment]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              entity_type: Optional[PaymentEntityTypeEnum] = None,
                              entity_id: Optional[int] = None,
                              status: Optional[PaymentStatusEnum] = None,
                              start_date: Optional[date] = None,
                              end_date: Optional[date] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[PaymentSummaryData]: pass
    @abstractmethod
    async def save(self, entity: Payment, session: Optional[AsyncSession] = None) -> Payment: # Updated type hint
# NO PASS STATEMENT HERE (Line 263, conceptually, based on where IndentationError points)
# This is line 263 in the latest file. The method save is the last one.
# If a class definition follows immediately without unindenting, that's fine.
# If an empty class or interface definition follows, it might be an issue.
# Let's assume the error is about the interface method `save` itself, or the class after it.

class IAuditLogRepository(IRepository[AuditLog, int]): # This is the class after IPaymentRepository
    @abstractmethod
    async def get_audit_logs_paginated(
        self, user_id_filter: Optional[int] = None, action_filter: Optional[str] = None, entity_type_filter: Optional[str] = None,
        entity_id_filter: Optional[int] = None, start_date_filter: Optional[datetime] = None, end_date_filter: Optional[datetime] = None,   
        page: int = 1, page_size: int = 50
    ) -> Tuple[List[AuditLogEntryData], int]: pass 
# ...
```
The error message "expected an indented block after function definition on line 263" means that the method definition ending on or just before line 263 (which is `async def save(...) -> Payment: # Updated type hint`) did not have a `pass` statement or any body, and the next line was not properly indented to continue that method or class.

If the method `save` in `IPaymentRepository` is the last method in that interface, and it's immediately followed by the `class IAuditLogRepository` definition *at the same indentation level*, this itself is not an error.

However, if the `save` method was intended to have content or if the next line (the start of `IAuditLogRepository`) was mis-indented, it could cause an error.
The traceback says `class IPaymentRepository(IRepository[Payment, int]):` is on line 265 in the *running* code. This means line 263 in the *running* code is the `@abstractmethod` decorator for the `save` method.

The code provided in `changes_to_codebase_corresponding_to_schema_v1.04.md` for `app/services/__init__.py` has:
```python
    @abstractmethod
    async def save(self, entity: Payment, session: Optional[AsyncSession] = None) -> Payment: # Updated type hint
# NO pass here.
class IAuditLogRepository(IRepository[AuditLog, int]): # This line must be indented correctly.
```
An abstract method in Python still needs a body, even if it's just `pass`.
If line `class IAuditLogRepository...` is *not* indented, but Python expected the body for `save`, then this error occurs.
The fix is simple: add `pass` to the abstract method.

```python
    @abstractmethod
    async def save(self, entity: Payment, session: Optional[AsyncSession] = None) -> Payment: pass # Added pass
```
This is the most likely cause for an `IndentationError` related to a function/method definition.

Let's verify the file provided `changes_to_codebase_corresponding_to_schema_v1.04.md` for `app/services/__init__.py`:
The last method of `IPaymentRepository` is:
```python
    @abstractmethod
    async def save(self, entity: Payment, session: Optional[AsyncSession] = None) -> Payment: # Updated type hint
```
It is indeed missing a `pass` statement. The subsequent class `IAuditLogRepository` starts at the same indentation level, which is correct *if* `save` had a body.

**Fix Plan for `app/services/__init__.py`:**
1.  Locate the `save` method in `IPaymentRepository`.
2.  Add `pass` to its definition.
3.  Re-validate all other abstract methods in all interfaces in this file to ensure they also have `pass`.

Let's quickly scan the other interfaces in the provided `app/services/__init__.py` from `changes_to_codebase_corresponding_to_schema_v1.04.md`:

*   `IRepository`: All methods have `pass`.
*   `IAccountRepository`: All methods have `pass`.
*   `IJournalEntryRepository`: All methods have `pass`.
*   `IFiscalPeriodRepository`: All methods have `pass`.
*   `IFiscalYearRepository`: All methods have `pass`.
*   `ITaxCodeRepository`: All methods have `pass`.
*   `ICompanySettingsRepository`: All methods have `pass`.
*   `IGSTReturnRepository`: All methods have `pass`.
*   `IAccountTypeRepository`: All methods have `pass`.
*   `ICurrencyRepository`: Has `get_all_active() -> List[Currency]: pass`. Correct.
*   `IExchangeRateRepository`: All methods have `pass`.
*   `ISequenceRepository`: All methods have `pass`.
*   `IConfigurationRepository`: All methods have `pass`.
*   `ICustomerRepository`: All methods have `pass`.
*   `IVendorRepository`: All methods have `pass`.
*   `IProductRepository`: All methods have `pass`.
*   `ISalesInvoiceRepository`: All methods have `pass`.
*   `IPurchaseInvoiceRepository`: All methods have `pass`.
*   `IInventoryMovementRepository`: `save` method has `pass`.
*   `IDimensionRepository`: All methods have `pass`.
*   `IBankAccountRepository`: `save` method has `pass`.
*   `IBankTransactionRepository`: `save` method has `pass`.
*   **`IPaymentRepository`**:
    *   `get_by_payment_no` has `pass`.
    *   `get_all_summary` has `pass`.
    *   `save` is **missing `pass`**. This is the culprit.
*   `IAuditLogRepository`: `get_audit_logs_paginated` has `pass`.
*   `IDataChangeHistoryRepository`: `get_data_change_history_paginated` has `pass`.
*   `IBankReconciliationRepository`: `save_reconciliation_details` has `pass`.

The error is indeed the missing `pass` in `IPaymentRepository.save`.

**Now for the Project Architecture Document updates:**

I need to review the `changes_to_codebase_corresponding_to_schema_v1.04.md` and the schema patch file `schema_patch_1.0.3_to_1.0.4.sql`.

**Key changes from `schema_patch_1.0.3_to_1.0.4.sql`:**
1.  **New Table: `business.bank_reconciliations`**:
    *   Columns: `id`, `bank_account_id`, `statement_date`, `statement_ending_balance`, `calculated_book_balance`, `reconciled_difference`, `reconciliation_date`, `notes`, `created_at`, `updated_at`, `created_by_user_id`.
    *   FKs: `bank_account_id` -> `business.bank_accounts.id`, `created_by_user_id` -> `core.users.id`.
    *   Unique constraint: `uq_bank_reconciliation_account_statement_date` on (`bank_account_id`, `statement_date`).
2.  **New Column in `business.bank_accounts`**: `last_reconciled_balance NUMERIC(15,2) NULL`.
3.  **New Column in `business.bank_transactions`**: `reconciled_bank_reconciliation_id INT NULL`, with FK to `business.bank_reconciliations.id`.

**Key changes from `changes_to_codebase_corresponding_to_schema_v1.04.md`:**
*   **`app/ui/banking/__init__.py`**: Added `CSVImportConfigDialog`, `BankReconciliationWidget`, `ReconciliationTableModel`.
*   **`app/ui/banking/bank_transactions_widget.py`**:
    *   Added `Import Statement (CSV)` action and `CSVImportConfigDialog`.
*   **`app/ui/banking/reconciliation_table_model.py`**: New file. `QAbstractTableModel` for displaying transactions in the reconciliation view, supports checkable items.
*   **`app/ui/banking/bank_reconciliation_widget.py`**: New file. Major UI component for bank reconciliation process.
    *   Allows selection of bank account, statement date, and ending balance.
    *   Loads unreconciled statement items and system transactions.
    *   Provides UI for matching items.
    *   Displays reconciliation summary (book balance, statement balance, adjustments, difference).
    *   Includes a "Create Journal Entry" button for items on the statement but not in the books (e.g., bank charges, interest).
    *   Includes a "Save Reconciliation" button.
*   **`app/ui/banking/csv_import_config_dialog.py`**: New file. Dialog for configuring and initiating CSV import of bank statements.
*   **`app/ui/main_window.py`**: Added a new tab for "Bank Reconciliation" using `BankReconciliationWidget`.
*   **`app/utils/pydantic_models.py`**: Added `BankReconciliationBaseData`, `BankReconciliationCreateData`, `BankReconciliationData`.
*   **`app/services/audit_services.py`**:
    *   `_format_changes_summary`: Improved logic for summarizing changes, especially for created/deleted records and handling of sensitive/noisy fields.
    *   `get_audit_logs_paginated` & `get_data_change_history_paginated`:
        *   Corrected end_date_filter to be inclusive by adding `datetime.timedelta(days=1)`.
        *   Used explicit alias names for `UserAlias`.
        *   Used `row_mapping` for accessing results.
*   **`app/services/__init__.py`**:
    *   Added `BankReconciliation` model import.
    *   Added `BankReconciliationData` DTO import.
    *   Defined `IBankReconciliationRepository` interface.
    *   Added `BankReconciliationService` to imports and `__all__`.
    *   Corrected type hints for `session` parameter in some `save` methods to use `AsyncSession`.
*   **`app/services/business_services.py`**:
    *   `BankTransactionService`:
        *   `get_all_for_bank_account` method now accepts `is_from_statement_filter` and sorts by `value_date` as a secondary key.
    *   **New `BankReconciliationService` class**: Implements `IBankReconciliationRepository`.
        *   `save_reconciliation_details`: Core logic for saving a `BankReconciliation` record, updating linked `BankTransaction` records (marking them as reconciled and linking to the reconciliation ID), and updating the `BankAccount`'s `last_reconciled_date` and `last_reconciled_balance`.
*   **`app/core/application_core.py`**:
    *   Removed `py_sequence_generator` from `JournalEntryManager` instantiation as sequence generation is now primarily DB-driven.
    *   Corrected `CustomerManager` and `VendorManager` instantiation to pass `self.currency_repo_service` as `currency_service`.
*   **`app/models/business/bank_account.py`**: Added `last_reconciled_balance` field and `reconciliations` relationship.
*   **`app/models/business/bank_transaction.py`**: Added `reconciled_bank_reconciliation_id` field and `reconciliation_instance` relationship. Also added `is_from_statement` and `raw_statement_data` (these were actually in schema v1.0.3, but good to note their presence in the models).
*   **`app/models/business/bank_reconciliation.py`**: New model definition for `bank_reconciliations` table.
*   **`app/business_logic/bank_transaction_manager.py`**:
    *   Added `import_bank_statement_csv` method: Handles CSV parsing, data transformation, duplicate checking, and creation of `BankTransaction` records marked as `is_from_statement=True`.
    *   Added `get_unreconciled_transactions_for_matching` method: Fetches unreconciled statement items and system transactions up to a given date.
*   **`app/accounting/journal_entry_manager.py`**:
    *   Constructor no longer takes `sequence_generator`.
    *   `create_journal_entry` now uses `self.app_core.db_manager.execute_scalar("SELECT core.get_next_sequence_value(...));` for `entry_no`.
    *   `post_journal_entry` now includes logic to automatically create a `BankTransaction` if a journal entry line affects a GL account linked to a `BankAccount`.
*   **Other files**: Mostly structural (`__init__.py`) or UI files for new features (e.g., bank reconciliation specific table model and dialogs).
*   **`resources/icons/import_csv.svg`** and `resources/resources.qrc` updated for new icon.
*   **`scripts/initial_data.sql`**:
    *   Added `VIEW_AUDIT_LOG` permission.
    *   Added `BANK_TRANSACTION_VIEW`, `BANK_TRANSACTION_MANAGE`, `BANK_STATEMENT_IMPORT` permissions, replacing old `BANK_VIEW`, `BANK_CREATE` etc. for bank accounts with `BANK_ACCOUNT_VIEW`, `BANK_ACCOUNT_MANAGE`.
    *   Added default config keys: `SysAcc_DefaultCash`, `SysAcc_DefaultInventoryAsset`, `SysAcc_DefaultCOGS`, `SysAcc_GSTControl`.
    *   Added more system accounts to `accounting.accounts` (e.g., `SYS-GST-CONTROL`, `Cash on Hand`, `Inventory Asset Control`).
    *   Updated privileges for `sgbookkeeper_user`, including for `audit` schema sequences and `business` schema functions.
*   **`scripts/schema.sql`**: Schema version updated to 1.0.3 in comments (actual patch is for 1.0.4). `is_from_statement`, `raw_statement_data` in `bank_transactions`, and `bank_reconciliations` table are defined as per `schema_patch_1.0.3_to_1.0.4.sql`. The `update_bank_account_balance_trigger_func` is also defined. Audit log trigger applied to `bank_accounts` and `bank_transactions`.

This is a significant update with new features (bank reconciliation, CSV import) and refinements to existing ones (JE posting creating bank transactions, audit log service improvements).

**Updating the Architecture Document:**

I will need to update the following sections of the `Project Architecture Document.md`:
*   **Section 2 (Project Goals)**: Add bank reconciliation and CSV import.
*   **Section 4 (Architectural Overview & Diagram)**: The core layers remain the same, but new components within Banking/Business Logic and UI need to be implicitly covered. The diagram is high-level enough that it might not need direct changes unless a new major "layer" was introduced.
*   **Section 5 (Directory Structure)**: Mention new UI files in `app/ui/banking/`.
*   **Section 6 (Detailed Component Breakdown)**:
    *   `app/ui/`: Describe `BankReconciliationWidget`, `CSVImportConfigDialog`, and `ReconciliationTableModel`.
    *   `app/business_logic/`: Update `BankTransactionManager` for CSV import and fetching unreconciled transactions. Describe new `BankReconciliationManager` (though it's not explicitly created as a separate manager file in the diff, its logic is within `BankReconciliationService` and `BankReconciliationWidget`). I'll describe the functionality.
    *   `app/services/`: Describe `BankReconciliationService` and updates to `BankTransactionService`. Update `JournalEntryManager` to reflect its new responsibility of creating bank transactions.
    *   `app/models/`: Mention new `BankReconciliation` model and changes to `BankAccount` and `BankTransaction`.
*   **Section 7 (Data Model and Database)**:
    *   Describe the new `business.bank_reconciliations` table.
    *   Describe new columns in `business.bank_accounts` and `business.bank_transactions`.
    *   Mention the new `update_bank_account_balance_trigger_func()` trigger.
*   **Section 9 (Key Architectural Patterns)**: No major pattern changes, but can emphasize the event-driven updates for reconciliation.
*   **Section 10 (Data Flow)**: Could add a new example for "Bank Reconciliation Process".

**Regarding completeness of schema/initial_data.sql**:
The provided `scripts/schema.sql` and `scripts/initial_data.sql` are from `project_codebase_files_set-7.md`. The `changes_to_database_schema_and_initial_data_setup.md` provides a `diff` *against* what it calls `scripts/schema.sql-original` (which might be from an earlier state than set-7).
The `schema_patch_1.0.3_to_1.0.4.sql` seems to be the *incremental changes* to get to the state reflected in the new `schema.sql` from set-7.

I must ensure the architecture document reflects the *final state* of the schema as described by `schema.sql` in `project_codebase_files_set-7.md` (which incorporates the patch logic).
The `initial_data.sql` from set-7 also includes new permissions and config keys. I need to cross-check this against what's documented in the schema patch diff. The `initial_data.sql` in set-7 *is* the latest version, so it should be the source of truth for initial data.

Let's proceed with fixing the `IndentationError` first.
Then, I will update the Project Architecture Document.
</think>

You're right, an `IndentationError` is a fundamental issue that needs to be addressed first. Let's fix that.

**Error Analysis and Fix:**

The traceback indicates:
`IndentationError: expected an indented block after function definition on line 263` in `app/services/__init__.py`.

Looking at the content of `app/services/__init__.py` from the latest set of files (`changes_to_codebase_corresponding_to_schema_v1.04.md`), the relevant section is:

```python
# File: app/services/__init__.py
# ... (previous interfaces) ...

class IPaymentRepository(IRepository[Payment, int]):
    @abstractmethod
    async def get_by_payment_no(self, payment_no: str) -> Optional[Payment]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              entity_type: Optional[PaymentEntityTypeEnum] = None,
                              entity_id: Optional[int] = None,
                              status: Optional[PaymentStatusEnum] = None,
                              start_date: Optional[date] = None,
                              end_date: Optional[date] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[PaymentSummaryData]: pass
    @abstractmethod
    async def save(self, entity: Payment, session: Optional[AsyncSession] = None) -> Payment: # Updated type hint # THIS IS LIKELY LINE 263
# NO 'pass' HERE
class IAuditLogRepository(IRepository[AuditLog, int]): # THIS IS LIKELY LINE 265
    # ...
```

The abstract method `save` within the `IPaymentRepository` interface definition is missing a `pass` statement. Abstract methods in Python, even though they don't have an implementation in the interface, still require a body, which is typically `pass`.

**Fix:**
Add `pass` to the end of the `save` method definition in `IPaymentRepository`.

Here is the corrected file:

---
**Complete Updated File: `app/services/__init__.py`**
---
```python
# File: app/services/__init__.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Generic, TypeVar, Dict, Tuple 
from datetime import date, datetime 
from decimal import Decimal 
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T') 
ID = TypeVar('ID') 

class IRepository(ABC, Generic[T, ID]):
    @abstractmethod
    async def get_by_id(self, id_val: ID) -> Optional[T]: pass
    @abstractmethod
    async def get_all(self) -> List[T]: pass
    @abstractmethod
    async def add(self, entity: T) -> T: pass
    @abstractmethod
    async def update(self, entity: T) -> T: pass
    @abstractmethod
    async def delete(self, id_val: ID) -> bool: pass

# --- ORM Model Imports ---
from app.models.accounting.account import Account
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine 
from app.models.accounting.fiscal_period import FiscalPeriod
from app.models.accounting.tax_code import TaxCode
from app.models.core.company_setting import CompanySetting 
from app.models.accounting.gst_return import GSTReturn
from app.models.accounting.recurring_pattern import RecurringPattern
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.account_type import AccountType 
from app.models.accounting.currency import Currency 
from app.models.accounting.exchange_rate import ExchangeRate 
from app.models.core.sequence import Sequence 
from app.models.core.configuration import Configuration 
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.product import Product
from app.models.business.sales_invoice import SalesInvoice
from app.models.business.purchase_invoice import PurchaseInvoice
from app.models.business.inventory_movement import InventoryMovement
from app.models.accounting.dimension import Dimension 
from app.models.business.bank_account import BankAccount 
from app.models.business.bank_transaction import BankTransaction 
from app.models.business.payment import Payment, PaymentAllocation 
from app.models.audit.audit_log import AuditLog 
from app.models.audit.data_change_history import DataChangeHistory 
from app.models.business.bank_reconciliation import BankReconciliation

# --- DTO Imports (for return types in interfaces) ---
from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData,
    BankAccountSummaryData, BankTransactionSummaryData,
    PaymentSummaryData,
    AuditLogEntryData, DataChangeHistoryEntryData, BankReconciliationData
)
from app.common.enums import ( 
    ProductTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum,
    PaymentTypeEnum, PaymentEntityTypeEnum, PaymentStatusEnum, DataChangeTypeEnum 
)

# --- Existing Interfaces ---
class IAccountRepository(IRepository[Account, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Account]: pass
    @abstractmethod
    async def get_all_active(self) -> List[Account]: pass
    @abstractmethod
    async def get_by_type(self, account_type: str, active_only: bool = True) -> List[Account]: pass
    @abstractmethod
    async def save(self, account: Account) -> Account: pass 
    @abstractmethod
    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]: pass 
    @abstractmethod
    async def has_transactions(self, account_id: int) -> bool: pass
    @abstractmethod
    async def get_accounts_by_tax_treatment(self, tax_treatment_code: str) -> List[Account]: pass

class IJournalEntryRepository(IRepository[JournalEntry, int]): 
    @abstractmethod
    async def get_by_entry_no(self, entry_no: str) -> Optional[JournalEntry]: pass
    @abstractmethod
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]: pass
    @abstractmethod
    async def get_posted_entries_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]: pass
    @abstractmethod
    async def save(self, journal_entry: JournalEntry) -> JournalEntry: pass
    @abstractmethod
    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal: pass
    @abstractmethod
    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal: pass
    @abstractmethod
    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]: pass
    @abstractmethod
    async def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern: pass
    @abstractmethod
    async def get_all_summary(self, start_date_filter: Optional[date] = None, 
                              end_date_filter: Optional[date] = None, 
                              status_filter: Optional[str] = None,
                              entry_no_filter: Optional[str] = None,
                              description_filter: Optional[str] = None,
                              journal_type_filter: Optional[str] = None
                             ) -> List[Dict[str, Any]]: pass
    @abstractmethod
    async def get_posted_lines_for_account_in_range(self, account_id: int, start_date: date, end_date: date, 
                                                    dimension1_id: Optional[int] = None, dimension2_id: Optional[int] = None
                                                    ) -> List[JournalEntryLine]: pass 

class IFiscalPeriodRepository(IRepository[FiscalPeriod, int]): 
    @abstractmethod
    async def get_by_date(self, target_date: date) -> Optional[FiscalPeriod]: pass
    @abstractmethod
    async def get_fiscal_periods_for_year(self, fiscal_year_id: int, period_type: Optional[str] = None) -> List[FiscalPeriod]: pass

class IFiscalYearRepository(IRepository[FiscalYear, int]): 
    @abstractmethod
    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def get_by_date_overlap(self, start_date: date, end_date: date, exclude_id: Optional[int] = None) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def save(self, entity: FiscalYear) -> FiscalYear: pass

class ITaxCodeRepository(IRepository[TaxCode, int]): 
    @abstractmethod
    async def get_tax_code(self, code: str) -> Optional[TaxCode]: pass
    @abstractmethod
    async def save(self, entity: TaxCode) -> TaxCode: pass 

class ICompanySettingsRepository(IRepository[CompanySetting, int]): 
    @abstractmethod
    async def get_company_settings(self, settings_id: int = 1) -> Optional[CompanySetting]: pass
    @abstractmethod
    async def save_company_settings(self, settings_obj: CompanySetting) -> CompanySetting: pass

class IGSTReturnRepository(IRepository[GSTReturn, int]): 
    @abstractmethod
    async def get_gst_return(self, return_id: int) -> Optional[GSTReturn]: pass 
    @abstractmethod
    async def save_gst_return(self, gst_return_data: GSTReturn) -> GSTReturn: pass

class IAccountTypeRepository(IRepository[AccountType, int]): 
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[AccountType]: pass
    @abstractmethod
    async def get_by_category(self, category: str) -> List[AccountType]: pass

class ICurrencyRepository(IRepository[Currency, str]): 
    @abstractmethod
    async def get_all_active(self) -> List[Currency]: pass

class IExchangeRateRepository(IRepository[ExchangeRate, int]): 
    @abstractmethod
    async def get_rate_for_date(self, from_code: str, to_code: str, r_date: date) -> Optional[ExchangeRate]: pass
    @abstractmethod
    async def save(self, entity: ExchangeRate) -> ExchangeRate: pass

class ISequenceRepository(IRepository[Sequence, int]): 
    @abstractmethod
    async def get_sequence_by_name(self, name: str) -> Optional[Sequence]: pass
    @abstractmethod
    async def save_sequence(self, sequence_obj: Sequence) -> Sequence: pass

class IConfigurationRepository(IRepository[Configuration, int]): 
    @abstractmethod
    async def get_config_by_key(self, key: str) -> Optional[Configuration]: pass
    @abstractmethod
    async def save_config(self, config_obj: Configuration) -> Configuration: pass

class ICustomerRepository(IRepository[Customer, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Customer]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[CustomerSummaryData]: pass

class IVendorRepository(IRepository[Vendor, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Vendor]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[VendorSummaryData]: pass

class IProductRepository(IRepository[Product, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Product]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              active_only: bool = True,
                              product_type_filter: Optional[ProductTypeEnum] = None,
                              search_term: Optional[str] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[ProductSummaryData]: pass

class ISalesInvoiceRepository(IRepository[SalesInvoice, int]):
    @abstractmethod
    async def get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              customer_id: Optional[int] = None,
                              status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[SalesInvoiceSummaryData]: pass

class IPurchaseInvoiceRepository(IRepository[PurchaseInvoice, int]):
    @abstractmethod
    async def get_by_internal_ref_no(self, internal_ref_no: str) -> Optional[PurchaseInvoice]: pass 
    @abstractmethod
    async def get_by_vendor_and_vendor_invoice_no(self, vendor_id: int, vendor_invoice_no: str) -> Optional[PurchaseInvoice]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              vendor_id: Optional[int] = None,
                              status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[PurchaseInvoiceSummaryData]: pass

class IInventoryMovementRepository(IRepository[InventoryMovement, int]):
    @abstractmethod
    async def save(self, entity: InventoryMovement, session: Optional[AsyncSession]=None) -> InventoryMovement: pass

class IDimensionRepository(IRepository[Dimension, int]):
    @abstractmethod
    async def get_distinct_dimension_types(self) -> List[str]: pass
    @abstractmethod
    async def get_dimensions_by_type(self, dim_type: str, active_only: bool = True) -> List[Dimension]: pass
    @abstractmethod
    async def get_by_type_and_code(self, dim_type: str, code: str) -> Optional[Dimension]: pass

class IBankAccountRepository(IRepository[BankAccount, int]):
    @abstractmethod
    async def get_by_account_number(self, account_number: str) -> Optional[BankAccount]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True, 
                              currency_code: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[BankAccountSummaryData]: pass
    @abstractmethod
    async def save(self, entity: BankAccount) -> BankAccount: pass

class IBankTransactionRepository(IRepository[BankTransaction, int]):
    @abstractmethod
    async def get_all_for_bank_account(self, bank_account_id: int,
                                       start_date: Optional[date] = None,
                                       end_date: Optional[date] = None,
                                       transaction_type: Optional[BankTransactionTypeEnum] = None,
                                       is_reconciled: Optional[bool] = None,
                                       is_from_statement_filter: Optional[bool] = None, 
                                       page: int = 1, page_size: int = 50
                                      ) -> List[BankTransactionSummaryData]: pass 
    @abstractmethod
    async def save(self, entity: BankTransaction, session: Optional[AsyncSession] = None) -> BankTransaction: pass

class IPaymentRepository(IRepository[Payment, int]):
    @abstractmethod
    async def get_by_payment_no(self, payment_no: str) -> Optional[Payment]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              entity_type: Optional[PaymentEntityTypeEnum] = None,
                              entity_id: Optional[int] = None,
                              status: Optional[PaymentStatusEnum] = None,
                              start_date: Optional[date] = None,
                              end_date: Optional[date] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[PaymentSummaryData]: pass
    @abstractmethod
    async def save(self, entity: Payment, session: Optional[AsyncSession] = None) -> Payment: pass # Added pass

class IAuditLogRepository(IRepository[AuditLog, int]):
    @abstractmethod
    async def get_audit_logs_paginated(
        self, user_id_filter: Optional[int] = None, action_filter: Optional[str] = None, entity_type_filter: Optional[str] = None,
        entity_id_filter: Optional[int] = None, start_date_filter: Optional[datetime] = None, end_date_filter: Optional[datetime] = None,   
        page: int = 1, page_size: int = 50
    ) -> Tuple[List[AuditLogEntryData], int]: pass 

class IDataChangeHistoryRepository(IRepository[DataChangeHistory, int]):
    @abstractmethod
    async def get_data_change_history_paginated(
        self, table_name_filter: Optional[str] = None, record_id_filter: Optional[int] = None, changed_by_user_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None, end_date_filter: Optional[datetime] = None,   
        page: int = 1, page_size: int = 50
    ) -> Tuple[List[DataChangeHistoryEntryData], int]: pass 

class IBankReconciliationRepository(IRepository[BankReconciliation, int]):
    @abstractmethod
    async def save_reconciliation_details(
        self, 
        reconciliation_orm: BankReconciliation,
        cleared_statement_txn_ids: List[int], 
        cleared_system_txn_ids: List[int],
        statement_end_date: date,
        bank_account_id: int,
        statement_ending_balance: Decimal,
        session: AsyncSession 
    ) -> BankReconciliation: pass

from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService, DimensionService
from .business_services import (
    CustomerService, VendorService, ProductService, 
    SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService,
    BankAccountService, BankTransactionService, PaymentService, 
    BankReconciliationService
)
from .audit_services import AuditLogService 

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository", 
    "ICustomerRepository", "IVendorRepository", "IProductRepository",
    "ISalesInvoiceRepository", "IPurchaseInvoiceRepository", 
    "IInventoryMovementRepository", 
    "IDimensionRepository", 
    "IBankAccountRepository", 
    "IBankTransactionRepository", 
    "IPaymentRepository", 
    "IAuditLogRepository", "IDataChangeHistoryRepository", 
    "IBankReconciliationRepository", 
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService", "DimensionService", 
    "CustomerService", "VendorService", "ProductService", 
    "SalesInvoiceService", "PurchaseInvoiceService", 
    "InventoryMovementService", 
    "BankAccountService", 
    "BankTransactionService",
    "PaymentService", 
    "AuditLogService", 
    "BankReconciliationService", 
]
```
This should resolve the `IndentationError`.

Now, for the **Project Architecture Document update**:

I have carefully reviewed the `changes_to_codebase_corresponding_to_schema_v1.04.md` and the provided `schema_patch_1.0.3_to_1.0.4.sql`. The patch file directly corresponds to the schema changes needed for version 1.0.4 (bank reconciliation features). The `scripts/schema.sql` and `scripts/initial_data.sql` from `project_codebase_files_set-7.md` represent the state *after* these v1.0.4 changes have been conceptually applied (they are the new baseline).

**Key changes incorporated into the codebase for v1.0.4:**

*   **Database Schema (`schema_patch_1.0.3_to_1.0.4.sql` and reflected in `project_codebase_files_set-7.md/scripts/schema.sql`):**
    *   New table `business.bank_reconciliations` to store reconciliation summaries.
    *   `business.bank_accounts` table: Added `last_reconciled_balance` column.
    *   `business.bank_transactions` table: Added `reconciled_bank_reconciliation_id` (FK to `bank_reconciliations`). The fields `is_from_statement` and `raw_statement_data` were already present from schema v1.0.3.
    *   New trigger `business.update_bank_account_balance_trigger_func()` on `bank_transactions` to automatically update `bank_accounts.current_balance`.
    *   Audit log trigger `audit.log_data_change_trigger_func()` applied to `bank_accounts` and `bank_transactions`.
*   **Initial Data (`project_codebase_files_set-7.md/scripts/initial_data.sql`):**
    *   New permissions related to audit logs (`VIEW_AUDIT_LOG`) and more granular banking permissions (e.g., `BANK_ACCOUNT_VIEW`, `BANK_ACCOUNT_MANAGE`, `BANK_TRANSACTION_VIEW`, `BANK_TRANSACTION_MANAGE`, `BANK_RECONCILE`, `BANK_STATEMENT_IMPORT`).
    *   New default configuration keys in `core.configuration` (e.g., `SysAcc_DefaultCash`, `SysAcc_DefaultInventoryAsset`, `SysAcc_DefaultCOGS`, `SysAcc_GSTControl`).
    *   Additional system accounts in `accounting.accounts` (e.g., `SYS-GST-CONTROL`, `Cash on Hand`, `Inventory Asset Control`).
    *   Updated privilege grants for `sgbookkeeper_user`.
*   **Models (`app/models/`):**
    *   New `BankReconciliation` model in `app/models/business/bank_reconciliation.py`.
    *   `BankAccount` model updated with `last_reconciled_balance` and `reconciliations` relationship.
    *   `BankTransaction` model updated with `reconciled_bank_reconciliation_id`, `reconciliation_instance` relationship, and existing `is_from_statement`, `raw_statement_data`.
*   **DTOs (`app/utils/pydantic_models.py`):**
    *   New DTOs: `BankReconciliationBaseData`, `BankReconciliationCreateData`, `BankReconciliationData`.
*   **Services (`app/services/`):**
    *   New `IBankReconciliationRepository` interface.
    *   New `BankReconciliationService` implementation in `business_services.py` with core logic in `save_reconciliation_details`.
    *   `BankTransactionService` (`business_services.py`): `get_all_for_bank_account` updated with `is_from_statement_filter` and refined sorting.
    *   `JournalEntryManager` (`app/accounting/journal_entry_manager.py`):
        *   No longer takes `SequenceGenerator` in constructor (uses DB function via `app_core.db_manager`).
        *   `post_journal_entry` now auto-creates `BankTransaction` records if a JE line hits a bank-linked GL account.
    *   `AuditLogService` (`app/services/audit_services.py`): Improvements to `_format_changes_summary` and pagination queries.
*   **Business Logic (`app/business_logic/`):**
    *   `BankTransactionManager` (`app/business_logic/bank_transaction_manager.py`):
        *   New `import_bank_statement_csv` method for CSV import functionality.
        *   New `get_unreconciled_transactions_for_matching` method to support reconciliation UI.
*   **UI (`app/ui/banking/`):**
    *   New `BankReconciliationWidget` for the reconciliation process.
    *   New `ReconciliationTableModel` to display transactions in the reconciliation view.
    *   New `CSVImportConfigDialog` for configuring CSV imports.
    *   `BankTransactionsWidget` updated with an "Import Statement (CSV)" action.
    *   `MainWindow` has a new "Bank Reconciliation" tab.
*   **Application Core (`app/core/application_core.py`):**
    *   Instantiates and provides access to the new `BankReconciliationService`.
    *   Adjusted `JournalEntryManager` instantiation.
    *   Updated `CurrencyService` to `CurrencyRepoService` in `CustomerManager` and `VendorManager` instantiations for consistency.
*   **Resources**: Added `import_csv.svg` icon.

I will now generate the updated `Project Architecture Document (v2).md`. I have meticulously reviewed the provided file sets and the diffs, and the generated `schema.sql` and `initial_data.sql` from `project_codebase_files_set-7.md` are considered the source of truth for the current database structure and setup. The changes listed above will be incorporated into the document.

---
**Project Architecture Document (v2)**
---
```markdown
# SG Bookkeeper - Project Architecture Document (v2)

## 1. Introduction

This document outlines the software architecture of the SG Bookkeeper application, reflecting its state after the integration of bank reconciliation features, CSV bank statement import, and related enhancements up to schema version 1.0.4. SG Bookkeeper is a desktop application designed for comprehensive bookkeeping and accounting, tailored for small to medium-sized businesses, with a focus on Singaporean business requirements.

The purpose of this document is to provide an updated, clear understanding of the project's structure, components, their interactions, and overall design principles.

## 2. Project Goals

Based on the codebase, the primary goals of the SG Bookkeeper project are:

*   **Comprehensive Accounting**: Provide robust double-entry bookkeeping, including Chart of Accounts, Journal Entries, Fiscal Period control, and multi-currency support.
*   **Business Operations Management**: Manage Customers, Vendors, Products/Services, Sales/Purchase Invoices, Payments, and Inventory.
*   **Banking & Reconciliation**: Offer features for managing bank accounts, bank transactions, **importing bank statements via CSV**, and performing **bank reconciliations**.
*   **Tax Compliance**: Facilitate GST calculations, F5 return preparation, and potentially income tax and withholding tax.
*   **Financial Reporting**: Generate essential financial statements (Balance Sheet, P&L, Trial Balance, General Ledger) and tax reports.
*   **User-Friendly Interface**: Provide an intuitive desktop GUI.
*   **Data Integrity and Auditability**: Ensure data accuracy with robust audit trails for changes and system actions.
*   **Security**: Manage user access via roles and permissions.
*   **Configuration**: Allow application and company-specific settings.

## 3. Core Technologies

The project leverages:

*   **Python**: >=3.9, <3.13
*   **PySide6 (Qt for Python)**: GUI framework.
*   **SQLAlchemy (asyncio)**: ORM.
*   **asyncpg**: Asynchronous PostgreSQL driver.
*   **PostgreSQL**: Relational database.
*   **Pydantic**: Data validation and DTOs.
*   **asyncio**: Asynchronous operations.
*   **ReportLab**: PDF generation.
*   **Openpyxl**: Excel generation.
*   **python-dateutil**: Advanced date/time utilities.
*   **bcrypt**: Password hashing.
*   **Alembic**: (Implied) Database migrations.
*   **Poetry**: Dependency management.

## 4. Architectural Overview

SG Bookkeeper maintains a multi-layered, modular architecture:

1.  **Presentation Layer (UI)**: `app/ui/` (PySide6 components).
2.  **Application Core Layer**: `app/core/` (Orchestration, central services).
3.  **Business Logic Layer (Managers)**: `app/business_logic/`, `app/accounting/`, `app/tax/`, `app/reporting/` (High-level operations).
4.  **Service Layer (Repositories)**: `app/services/` (Data access abstraction).
5.  **Data Model Layer (ORM)**: `app/models/` (SQLAlchemy models).
6.  **Database Layer**: PostgreSQL (Schema in `scripts/schema.sql`).
7.  **Utility Layer**: `app/utils/`, `app/common/` (Helpers, DTOs, Enums).

### Architecture Diagram (Remains valid at a high level)

```mermaid
graph TD
    A[User Interface (PySide6 - app/ui)] --> B{Application Core (app/core/application_core.py)};
    B --> C[Business Logic Managers (app/business_logic, app/accounting, app/tax, app/reporting)];
    C --> D[Service Layer / Repositories (app/services)];
    D --> E[Data Models (SQLAlchemy ORM - app/models)];
    E --> F[Database (PostgreSQL)];

    B --> G[Security Manager (app/core)];
    B --> H[Config Manager (app/core)];
    B --> I[Database Manager (app/core)];
    I --> F;

    C -- Uses --> J[Utilities (app/utils, app/common)];
    D -- Uses --> J;
    A -- Uses --> J;
    
    subgraph "Presentation Layer"
        A
    end
    
    subgraph "Core & Logic Layer"
        B
        C
        G
        H
        I
    end
    
    subgraph "Data Access Layer"
        D
        E
    end
    
    subgraph "Persistence Layer"
        F
    end
    
    subgraph "Shared Utilities"
        J
    end
```

**Diagram Description:** The fundamental layered structure remains. New features like bank reconciliation are implemented within these existing layers (e.g., new UI widgets in `app/ui/banking`, new service logic in `app/services/business_services.py`, new models in `app/models/business/`).

## 5. Directory Structure and Key Module Updates

*   **`app/ui/banking/`**:
    *   **New**: `bank_reconciliation_widget.py`, `reconciliation_table_model.py`, `csv_import_config_dialog.py`.
    *   Updated: `__init__.py` (exports new components), `bank_transactions_widget.py` (adds CSV import action).
*   **`app/ui/main_window.py`**: Added "Bank Reconciliation" tab.
*   **`app/models/business/`**:
    *   **New**: `bank_reconciliation.py` (defines `BankReconciliation` ORM model).
    *   Updated: `bank_account.py` (adds `last_reconciled_balance`, `reconciliations` relationship), `bank_transaction.py` (adds `reconciled_bank_reconciliation_id`, `reconciliation_instance` relationship, and confirms `is_from_statement`, `raw_statement_data`). `__init__.py` exports `BankReconciliation`.
*   **`app/models/__init__.py`**: Exports `BankReconciliation`.
*   **`app/services/`**:
    *   `__init__.py`: Defines `IBankReconciliationRepository` interface; imports and exports `BankReconciliationService`, `BankReconciliation` model, `BankReconciliationData` DTO. Corrected `AsyncSession` type hints.
    *   `business_services.py`: Implements `BankReconciliationService` and updates `BankTransactionService` (for `is_from_statement_filter` and sorting).
    *   `audit_services.py`: Refinements to change summary formatting and pagination queries.
*   **`app/business_logic/bank_transaction_manager.py`**:
    *   Added `import_bank_statement_csv` method.
    *   Added `get_unreconciled_transactions_for_matching` method.
*   **`app/accounting/journal_entry_manager.py`**:
    *   Constructor updated (removes `SequenceGenerator`).
    *   `create_journal_entry` uses DB function for sequence number.
    *   `post_journal_entry` now auto-creates `BankTransaction` records for relevant JE lines.
*   **`app/core/application_core.py`**:
    *   Instantiates and provides `BankReconciliationService`.
    *   Corrected `JournalEntryManager` instantiation.
    *   Updated `CurrencyService` to `CurrencyRepoService` in `CustomerManager` and `VendorManager` initializations.
*   **`app/utils/pydantic_models.py`**: Added `BankReconciliationBaseData`, `BankReconciliationCreateData`, `BankReconciliationData`.
*   **`resources/`**: Added `import_csv.svg` and updated `resources.qrc`.
*   **`scripts/`**:
    *   `schema.sql`: Reflects schema v1.0.4 changes (new `bank_reconciliations` table, modifications to `bank_accounts` and `bank_transactions`, new trigger `update_bank_account_balance_trigger_func`, audit triggers on banking tables).
    *   `initial_data.sql`: Updated with new permissions (e.g., `VIEW_AUDIT_LOG`, granular banking perms), new default configuration keys, additional system accounts, and updated privilege grants.

## 6. Detailed Component Breakdown (Updates)

### 6.1. `app/core/application_core.py` (Updates)
*   Now initializes and provides `BankReconciliationService`.
*   `JournalEntryManager` instantiation no longer requires `SequenceGenerator` as sequence numbers are primarily fetched via a database function call (`core.get_next_sequence_value`) managed by `DatabaseManager`.
*   Ensures consistent use of `CurrencyRepoService` for currency-related dependencies in managers.

### 6.2. `app/models/` (Updates)
*   **`business.bank_reconciliation.BankReconciliation`**: New ORM model representing a completed bank reconciliation event. Stores statement details, calculated balances, and links to reconciled transactions.
*   **`business.bank_account.BankAccount`**:
    *   Added `last_reconciled_balance: Optional[Decimal]`.
    *   Added `reconciliations: Mapped[List["BankReconciliation"]]` relationship.
*   **`business.bank_transaction.BankTransaction`**:
    *   Added `is_from_statement: Mapped[bool]` (indicates if transaction originated from a CSV import).
    *   Added `raw_statement_data: Mapped[Optional[Dict[str, Any]]]` (stores original CSV row data for imported transactions).
    *   Added `reconciled_bank_reconciliation_id: Mapped[Optional[int]]` (FK to `bank_reconciliations.id`).
    *   Added `reconciliation_instance: Mapped[Optional["BankReconciliation"]]` relationship.

### 6.3. `app/services/` (Updates)
*   **`business_services.BankTransactionService`**:
    *   `get_all_for_bank_account` method enhanced with an `is_from_statement_filter` parameter and refined sorting including `value_date`.
*   **`business_services.BankReconciliationService` (New)**:
    *   Implements `IBankReconciliationRepository`.
    *   **`save_reconciliation_details`**: Key method that transactionally:
        1.  Saves the `BankReconciliation` ORM object.
        2.  Updates all associated `BankTransaction` records (both from statement and system) by setting `is_reconciled=True`, `reconciled_date`, and `reconciled_bank_reconciliation_id`.
        3.  Updates the parent `BankAccount` record with the `last_reconciled_date` and `last_reconciled_balance`.
*   **`audit_services.AuditLogService`**:
    *   Improved `_format_changes_summary` to better represent created/deleted records and handle sensitive/noisy fields more gracefully.
    *   Refined date filtering in pagination queries to be inclusive of the end date.
*   **`__init__.py`**: Added `IBankReconciliationRepository` and registered `BankReconciliationService`. Corrected `AsyncSession` type hints for `save` methods in several repository interfaces (e.g., `IInventoryMovementRepository`, `IBankTransactionRepository`, `IPaymentRepository`).

### 6.4. `app/business_logic/` & `app/accounting/` (Manager Updates)
*   **`accounting.JournalEntryManager`**:
    *   `create_journal_entry`: Now relies on `app_core.db_manager.execute_scalar` calling `core.get_next_sequence_value` for generating `entry_no`.
    *   `post_journal_entry`: When posting a JE, if any line debits/credits a GL account that is flagged as `is_bank_account` and linked to a `business.bank_accounts` record, this method will now automatically create a corresponding `BankTransaction` record. This ensures that system-side bank movements are captured.
*   **`business_logic.BankTransactionManager`**:
    *   **`import_bank_statement_csv`**: New method to handle CSV file uploads. It parses the CSV based on user-provided column mapping and date format, transforms rows into `BankTransaction` objects (marked as `is_from_statement=True` and storing `raw_statement_data`), performs basic duplicate checks against existing statement transactions, and saves valid new transactions. Returns a summary of the import (total, imported, skipped, failed).
    *   **`get_unreconciled_transactions_for_matching`**: New method to fetch two lists of `BankTransactionSummaryData`:
        1.  Unreconciled transactions originating from imported statements (`is_from_statement=True`).
        2.  Unreconciled transactions originating from system actions (e.g., JEs, payments) (`is_from_statement=False`).
        Both lists are filtered up to a given statement end date. This data feeds the bank reconciliation UI.

### 6.5. `app/ui/` (Updates)
*   **`banking.BankReconciliationWidget` (New)**: A major new UI component providing the interface for:
    *   Selecting a bank account and entering statement details (end date, ending balance).
    *   Loading unreconciled statement transactions and system-generated bank transactions.
    *   Displaying these transactions in two separate tables (`ReconciliationTableModel`).
    *   Allowing users to select items from both tables for matching.
    *   Calculating and displaying a reconciliation summary: book balance, adjustments (e.g., interest, charges based on unmatched statement items), outstanding deposits/withdrawals (based on unmatched system items), and the final difference.
    *   Providing an action to "Match Selected" items (which currently just updates the UI calculation; persistence is via "Save Reconciliation").
    *   Providing an action to "Create Journal Entry" for unmatched statement items (pre-fills `JournalEntryDialog`).
    *   Providing an action to "Save Reconciliation" which will persist the reconciliation state.
*   **`banking.ReconciliationTableModel` (New)**: A `QAbstractTableModel` specifically for the bank reconciliation screen, supporting checkable items for selecting transactions to match or process.
*   **`banking.CSVImportConfigDialog` (New)**: A dialog allowing users to:
    *   Select a CSV file.
    *   Specify CSV format options (header row, date format).
    *   Map CSV columns (by name or index) to required transaction fields (date, description, debit/credit/amount, reference, value date).
    *   Specify handling for single vs. dual amount columns.
*   **`banking.BankTransactionsWidget`**:
    *   Added an "Import Statement (CSV)" toolbar action that opens the `CSVImportConfigDialog`.
*   **`main_window.MainWindow`**:
    *   Added a new top-level tab "Bank Reconciliation" which hosts the `BankReconciliationWidget`.

### 6.6. `app/utils/pydantic_models.py` (Updates)
*   Added new DTOs for bank reconciliation:
    *   `BankReconciliationBaseData`: Core fields for a reconciliation.
    *   `BankReconciliationCreateData`: Includes `UserAuditData` for creating a reconciliation.
    *   `BankReconciliationData`: Represents a full reconciliation record, typically for retrieval.

## 7. Data Model and Database (Updates based on v1.0.4)

*   **New Table: `business.bank_reconciliations`**:
    *   `id`, `bank_account_id` (FK), `statement_date`, `statement_ending_balance`, `calculated_book_balance`, `reconciled_difference`, `reconciliation_date`, `notes`, `created_at`, `updated_at`, `created_by_user_id` (FK).
    *   Unique constraint on `(bank_account_id, statement_date)`.
*   **Table `business.bank_accounts` Changes**:
    *   Added `last_reconciled_balance NUMERIC(15,2) NULL`: Stores the bank statement's ending balance from the last completed reconciliation for this account.
*   **Table `business.bank_transactions` Changes**:
    *   Added `reconciled_bank_reconciliation_id INT NULL`: FK to `business.bank_reconciliations.id`, linking a transaction to the specific reconciliation event that cleared it.
    *   (Existing from v1.0.3) `is_from_statement BOOLEAN NOT NULL DEFAULT FALSE`: Flags transactions imported from CSV statements.
    *   (Existing from v1.0.3) `raw_statement_data JSONB NULL`: Stores the original imported row data for statement transactions.
*   **New Trigger: `business.update_bank_account_balance_trigger_func()`**:
    *   Attached to `business.bank_transactions` (AFTER INSERT, UPDATE, DELETE).
    *   Automatically updates `business.bank_accounts.current_balance` when bank transactions are created, modified, or deleted. This ensures the `current_balance` in `bank_accounts` is always in sync with its underlying transactions.
*   **Audit Triggers**: The `audit.log_data_change_trigger_func()` is now also applied to `business.bank_accounts` and `business.bank_transactions`.
*   **Initial Data (`scripts/initial_data.sql` updates)**:
    *   Added new permissions: `VIEW_AUDIT_LOG`, `BANK_ACCOUNT_VIEW`, `BANK_ACCOUNT_MANAGE`, `BANK_TRANSACTION_VIEW`, `BANK_TRANSACTION_MANAGE`, `BANK_RECONCILE`, `BANK_STATEMENT_IMPORT`.
    *   Added new default configuration keys for system accounts: `SysAcc_DefaultCash`, `SysAcc_DefaultInventoryAsset`, `SysAcc_DefaultCOGS`, `SysAcc_GSTControl`.
    *   Ensured system accounts like `SYS-GST-CONTROL`, `Cash on Hand`, `Inventory Asset Control` are created.
    *   Updated role privileges, including for `audit` schema sequences.

## 8. Configuration and Initialization (Updates)

*   **`scripts/initial_data.sql`**: Now includes new default configuration keys (e.g., `SysAcc_DefaultCash`, `SysAcc_GSTControl`) and permissions related to new banking features and audit logs.
*   **`app/core/application_core.py`**: Service and manager instantiations updated to reflect new dependencies and components like `BankReconciliationService` and changes to `JournalEntryManager`.

## 9. Key Architectural Patterns & Considerations (Updates)

*   **Automated Record Creation**: The system now demonstrates more instances of automated record creation based on other processes:
    *   `JournalEntryManager.post_journal_entry()` creates `BankTransaction` records.
    *   `BankTransactionManager.import_bank_statement_csv()` creates `BankTransaction` records from external data.
*   **Database Triggers for Data Integrity**: The new `update_bank_account_balance_trigger_func()` enhances data integrity by ensuring `bank_accounts.current_balance` is automatically maintained.

## 10. Data Flow (New Example: Bank Reconciliation)

1.  **UI (`BankReconciliationWidget`)**:
    *   User selects a Bank Account, enters Statement Date and Statement Ending Balance.
    *   Clicks "Load / Refresh Transactions".
2.  **Manager (`BankTransactionManager`)**: `get_unreconciled_transactions_for_matching(bank_account_id, statement_date)` is called.
3.  **Service (`BankTransactionService`)**: Fetches two lists via `get_all_for_bank_account`:
    *   Unreconciled transactions marked `is_from_statement=True`.
    *   Unreconciled transactions marked `is_from_statement=False` (system entries).
4.  **UI**: Populates two tables with these transactions. Calculates and displays initial reconciliation summary.
5.  **User Interaction**: User selects items from both tables to match (e.g., a statement deposit against a system deposit JE).
    *   UI updates summary figures based on *unchecked* items.
    *   If user clicks "Match Selected":
        *   UI validates if selected amounts match.
        *   If matched, items are effectively "cleared" for this session (e.g., model might uncheck them, and they are excluded from summary recalculation *as if* they were reconciled).
    *   If user clicks "Create Journal Entry" for an unmatched statement item (e.g., bank charge):
        *   `JournalEntryDialog` is pre-filled with bank line details.
        *   User completes and posts the JE.
        *   `JournalEntryManager.post_journal_entry()` creates the JE and a corresponding system `BankTransaction`.
        *   List is refreshed; the new system transaction appears, and the statement item can now be matched.
6.  **Saving Reconciliation (`BankReconciliationWidget` -> `BankReconciliationManager` (conceptual, logic in service) -> `BankReconciliationService`)**:
    *   User clicks "Save Reconciliation" (enabled when difference is zero).
    *   A `BankReconciliationCreateData` DTO is assembled.
    *   `BankReconciliationService.save_reconciliation_details()` is called:
        *   Creates a new `BankReconciliation` record.
        *   Updates all `BankTransaction` records that were "cleared" (i.e., successfully matched or newly created and matched during the session) by setting `is_reconciled=True`, `reconciled_date`, and `reconciled_bank_reconciliation_id`.
        *   Updates the `BankAccount` with `last_reconciled_date` and `last_reconciled_balance`.
        *   All these operations occur within a single database transaction.
7.  **UI**: Confirms save and potentially clears reconciled items from view or reloads.

## 11. Conclusion (Updated)

The SG Bookkeeper project has evolved with significant enhancements, notably in the banking module with the introduction of CSV bank statement import and a comprehensive bank reconciliation feature. The architecture continues to support these additions effectively by leveraging its layered design. New UI components, service logic, data models, and database structures have been integrated while maintaining the core principles of modularity, asynchronous processing, and data integrity. The increased use of database triggers and automated record creation (like JEs creating Bank Transactions) further strengthens data consistency. The project remains a robust platform for small business accounting.

```

---
https://drive.google.com/file/d/11Cv4mFJ5z4I3inVCg8nkncVsAQtuIWrl/view?usp=sharing, https://drive.google.com/file/d/13aFutu059EFwgvQM4JE5LrYT13_62ztj/view?usp=sharing, https://drive.google.com/file/d/150VU2J4NfkYirCIGqQxC5VL9a_s7jyV0/view?usp=sharing, https://drive.google.com/file/d/1Fcdn0EWCauERrISMKReM_r0_nVIQvPiH/view?usp=sharing, https://drive.google.com/file/d/1IRffneWyqY8ILVvfOu3apYxB15SnhMYD/view?usp=sharing, https://drive.google.com/file/d/1S4zRP59L2Jxru__jXeoTL2TGZ4JN_GOT/view?usp=sharing, https://drive.google.com/file/d/1X5XkobtrDHItY5dTnWRYajA9LTVvZTGy/view?usp=sharing, https://drive.google.com/file/d/1bsb7xdrTRvfFSLOJVv_YBVncejRYeX-p/view?usp=sharing, https://drive.google.com/file/d/1eU9E4v6uT69z91uEABi8xf4-L1_PUKaI/view?usp=sharing, https://drive.google.com/file/d/1fcRRxU4xYdqMgGp58OyuFDOqIcGeOIW_/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221gVm5GnROGWVVYBXkgumxd5puGZ6g5Qs3%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1ndjSoP14ry1oCHgOguxNgNWxyP4c18ww/view?usp=sharing, https://drive.google.com/file/d/1zWrsOeANNSTZ51c666H-DxQapeSjXnZY/view?usp=sharing

