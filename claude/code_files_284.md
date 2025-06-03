<think>
The user has provided a new traceback showing an `ImportError: cannot import name 'JournalService' from partially initialized module 'app.services.journal_service' (most likely due to a circular import)`.

This is a classic Python circular import problem. Let's break it down:

**1. Deeply Understand Requirements:**
The primary goal is to fix the `ImportError` caused by a circular dependency. The application fails to launch due to this. I need to identify the circular import chain and refactor the imports to break the cycle, ensuring the application can start. I must be extremely careful not to introduce new errors or omit existing code.

**2. Systematic Diagnosis:**

*   **Error Message**: `ImportError: cannot import name 'JournalService' from partially initialized module 'app.services.journal_service' (most likely due to a circular import)`
*   **Location of Error**: The error manifests during the import of `JournalService` into `app/accounting/journal_entry_manager.py`.
*   **Traceback Analysis (Reconstructing the Import Chain)**:
    1.  `app/main.py` imports `app.ui.main_window`
    2.  `app/ui/main_window.py` imports `app.ui.dashboard.dashboard_widget`
    3.  `app/ui/dashboard/dashboard_widget.py` imports `app.utils.pydantic_models`
    4.  `app/utils/__init__.py` (likely triggered by the above) imports `app.utils.sequence_generator`
    5.  `app/utils/sequence_generator.py` imports `app.services.core_services.SequenceService`
    6.  `app/services/__init__.py` (likely triggered by `app.services.core_services`) is being processed and tries to import `app.services.journal_service` (at line 315 according to traceback)
    7.  `app/services/journal_service.py` (line 10) imports `app.core.database_manager`
    8.  `app/core/__init__.py` (likely triggered) imports `app.core.application_core`
    9.  `app/core/application_core.py` (line 9) imports `app.accounting.chart_of_accounts_manager`
    10. `app/accounting/__init__.py` (likely triggered) imports `app.accounting.journal_entry_manager`
    11. `app/accounting/journal_entry_manager.py` (line 14) imports `app.services.journal_service`
    12. **Circular Import Occurs**: Python is trying to import `app.services.journal_service` again (from `JournalEntryManager`), but `app.services.journal_service` is *already in the process of being imported* (from step 6, triggered by `app/services/__init__.py`) and has not finished its own imports yet (specifically, it was trying to import `DatabaseManager`, which led down a path that eventually came back to import `JournalService`). Because `app.services.journal_service` is only partially initialized, the name `JournalService` is not yet available in its namespace.

**Simplified Circular Dependency Chain:**

`app/services/__init__.py`
   imports `app.services.journal_service`
    `app.services.journal_service.py`
      imports `app.core.database_manager`
        `app.core.database_manager.py` (via `app.core.__init__`, `app.core.application_core`)
          imports `app.accounting.journal_entry_manager` (via chain through `ApplicationCore` -> `ChartOfAccountsManager` -> `app/accounting/__init__`)
            `app/accounting/journal_entry_manager.py`
              imports `app.services.journal_service` (tries to import `JournalService` name, but the module is still loading from the first import attempt)

**Root Cause**: `JournalEntryManager` needs `JournalService` for its operations (dependency injection). `JournalService` itself (or things it imports) indirectly leads back to importing `JournalEntryManager`.

**3. Thorough Analysis of Potential Solutions to Break Circular Imports:**

*   **Option 1: Move Imports to Local Scope (inside functions/methods)**:
    *   In `JournalEntryManager`, import `JournalService` inside methods that actually use it, rather than at the top level.
    *   Pros: Directly breaks the import-time cycle.
    *   Cons: Can make dependencies less clear, might slightly impact performance if imports happen frequently (though usually negligible for module imports), can be considered less clean by some style guides. PEP 8 generally recommends top-level imports.

*   **Option 2: Type Hinting with Forward References (String Literals)**:
    *   If `JournalService` is only needed for type hinting in `JournalEntryManager`'s constructor or method signatures, use a string literal: `journal_service: "JournalService"`.
    *   This requires ensuring `TYPE_CHECKING` from `typing` is used if the type hint is complex or involves other forward references.
    *   Pros: Breaks the import cycle at import time, allows type checkers to work correctly.
    *   Cons: The actual object needs to be passed in during instantiation, which is already the case with dependency injection.

*   **Option 3: Refactor Dependencies / Interface Segregation**:
    *   Perhaps `JournalEntryManager` doesn't need the full `JournalService` but only an interface that `JournalService` implements. This is already partially done with `IJournalEntryRepository`.
    *   Examine if `JournalService` truly needs to import `DatabaseManager` (which it does for `self.db_manager`), or if `ApplicationCore` could pass it `db_manager` without `JournalService` directly importing it. (This is unlikely as services are often constructed with `db_manager`).
    *   Could `ApplicationCore` be refactored to delay instantiation of some managers or services? This can get complex.

*   **Option 4: Selective Import from `app.services` in `ApplicationCore`**:
    *   Instead of `ApplicationCore` importing `JournalEntryManager` which then imports `JournalService`, can `ApplicationCore` be structured to initialize `JournalService` first, then pass it to `JournalEntryManager` without `JournalEntryManager` needing a top-level import of `JournalService`?
    *   `ApplicationCore` already imports both and sets them up. The problem is the chain from `app/services/__init__.py` itself.

*   **Option 5: Modify `app/services/__init__.py`**:
    *   The file `app/services/__init__.py` imports all individual service modules (like `from .journal_service import JournalService`). This is a common pattern for making services easily accessible via `app.services.JournalService`.
    *   If an individual service module (e.g., `journal_service.py`) causes a cycle when being imported by `__init__.py`, one solution is to *not* import it directly into `__init__.py`'s namespace. Users would then have to import `app.services.journal_service.JournalService`. This is less convenient.
    *   Alternatively, the specific import in `__init__.py` that pulls in `JournalService` could be moved to the bottom of the `__init__.py` file. This sometimes helps with initialization order but isn't a robust fix.

*   **Option 6: Modify `JournalEntryManager` to use forward reference for type hint and rely on `ApplicationCore` for injection**:
    *   In `app/accounting/journal_entry_manager.py`:
        ```python
        from typing import TYPE_CHECKING, List, Optional, Any, Dict
        # ... other imports ...
        if TYPE_CHECKING:
            from app.services.journal_service import JournalService # For type hinting only
            from app.core.application_core import ApplicationCore # Also for type hinting

        class JournalEntryManager:
            def __init__(self, 
                         # ... other services ...
                         app_core: "ApplicationCore"): # app_core is already passed
                self.journal_service: "JournalService" = app_core.journal_service # Get from app_core
                # ...
        ```
    *   This means `JournalEntryManager` no longer does a top-level `from app.services.journal_service import JournalService`. It gets the already initialized `JournalService` instance from `app_core`.
    *   This is a very common and clean way to break circular dependencies when using a central orchestrator like `ApplicationCore`.

**Evaluating Option 6 (Chosen Best Option):**
This seems like the most robust and Pythonic way to handle this, especially since `ApplicationCore` already instantiates and holds references to both `JournalService` and `JournalEntryManager`.

*   `ApplicationCore` imports `JournalService` and `JournalEntryManager`.
*   `ApplicationCore` instantiates `JournalService`.
*   `ApplicationCore` instantiates `JournalEntryManager`, passing the `app_core` instance itself (or the `JournalService` instance directly).
*   `JournalEntryManager` in its `__init__` can then access `self.app_core.journal_service` to get the `JournalService` instance.
*   This breaks the import-time cycle because `JournalEntryManager` doesn't need to import `JournalService` at the module level.

Let's check the existing `ApplicationCore` and `JournalEntryManager` constructor:
`app/core/application_core.py`:
```python
# ...
from app.services.journal_service import JournalService
from app.accounting.journal_entry_manager import JournalEntryManager
# ...
class ApplicationCore:
    # ...
    async def startup(self):
        # ...
        self._journal_service_instance = JournalService(self.db_manager, self)
        # ...
        self._je_manager_instance = JournalEntryManager(
            self.journal_service, # <<< JournalService instance is already passed here!
            self.account_service, 
            self.fiscal_period_service, 
            self # app_core itself is passed
        )
        # ...
    @property
    def journal_service(self) -> JournalService: ...
    @property
    def journal_entry_manager(self) -> JournalEntryManager: ...
```

`app/accounting/journal_entry_manager.py`:
```python
# ...
from app.services.journal_service import JournalService # <<< This is the problematic import
# ...
class JournalEntryManager:
    def __init__(self, 
                 journal_service: JournalService, # Type hint is fine, but import is the issue
                 account_service: AccountService, 
                 fiscal_period_service: FiscalPeriodService, 
                 app_core: "ApplicationCore"):
        self.journal_service = journal_service # Instance is received
        # ...
```
The `JournalService` instance is already being correctly injected into `JournalEntryManager` by `ApplicationCore`. The problem is solely the top-level `from app.services.journal_service import JournalService` in `journal_entry_manager.py` which creates the cycle during the initial module loading phase.

**Refined Plan (using Option 6 logic):**
1.  Modify `app/accounting/journal_entry_manager.py`:
    *   Remove the top-level import: `from app.services.journal_service import JournalService`.
    *   Add a conditional import under `if TYPE_CHECKING:` for `JournalService` for type hinting purposes:
        ```python
        from typing import TYPE_CHECKING
        # ...
        if TYPE_CHECKING:
            from app.services.journal_service import JournalService
            from app.core.application_core import ApplicationCore # Already there or add
        ```
    *   The constructor signature `journal_service: JournalService` will now use a string literal if the direct import is removed: `journal_service: "JournalService"`. Or, keep the direct import under `TYPE_CHECKING` block for the type hint.
        Let's try with the `TYPE_CHECKING` block, which is cleaner for type hints.

**Double-Checking Previous Fixes:**
The `IndentationError` in `app/services/__init__.py` (missing `pass` in `IPaymentRepository.save`) was fixed in the previous response. The current traceback does *not* show that error, meaning the `pass` statement was correctly applied or the error occurs before that point if the fix was somehow lost. Based on the traceback, the `IndentationError` is gone, and we're at an `ImportError`.

**Execution Plan:**

1.  **[X] File to modify**: `app/accounting/journal_entry_manager.py`.
2.  **[X] Remove**: The direct top-level import `from app.services.journal_service import JournalService`.
3.  **[X] Add/Ensure `TYPE_CHECKING` block**:
    ```python
    from typing import TYPE_CHECKING, List, Optional, Any, Dict # Ensure TYPE_CHECKING is imported
    # ... other imports ...

    if TYPE_CHECKING:
        from app.services.journal_service import JournalService
        # from app.core.application_core import ApplicationCore # Already imported or should be
        # from app.services.account_service import AccountService # Already imported
        # from app.services.fiscal_period_service import FiscalPeriodService # Already imported
    ```
4.  **[X] Constructor Type Hint**: The constructor parameter `journal_service: JournalService` will now rely on the `TYPE_CHECKING` import.
5.  **[X] Validate**: Ensure the rest of the file is unchanged.
6.  **[X] Generate the complete updated file `app/accounting/journal_entry_manager.py`**.
7.  **[ ] (Conceptual) Run application again** to see if this resolves the circular import.

Let's check the existing imports in `journal_entry_manager.py` from the user's provided files (`changes_to_codebase_corresponding_to_schema_v1.04.md` for `app/accounting/journal_entry_manager.py` content):
```python
# File: app/accounting/journal_entry_manager.py
from typing import List, Optional, Any, Dict, TYPE_CHECKING
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.orm import selectinload

from app.models import JournalEntry, JournalEntryLine, RecurringPattern, FiscalPeriod, Account
from app.models.business.bank_account import BankAccount # New import
from app.models.business.bank_transaction import BankTransaction # New import
from app.services.journal_service import JournalService # <--- THIS IS THE PROBLEM IMPORT
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
# SequenceGenerator is initialized in ApplicationCore and passed if needed, or app_core.sequence_service used
from app.utils.result import Result
from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData 
from app.common.enums import JournalTypeEnum, BankTransactionTypeEnum # New import

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    # Removed SequenceGenerator from here, will use app_core.sequence_service if directly needed.
    # However, sequence generation is handled by DB function now, called via db_manager.

class JournalEntryManager:
    def __init__(self, 
                 journal_service: JournalService, # <--- This type hint causes the issue if JournalService isn't fully defined due to the cycle
                 account_service: AccountService, 
                 fiscal_period_service: FiscalPeriodService, 
                 app_core: "ApplicationCore"):
        self.journal_service = journal_service
        # ...
```
Yes, the plan is to move `from app.services.journal_service import JournalService` into the `if TYPE_CHECKING:` block.
The constructor signature `journal_service: JournalService` will then correctly use this type hint for static analysis, but the runtime import cycle will be broken.

The `app_core: "ApplicationCore"` in the `__init__` signature is already a forward reference (string literal), which is good. The `JournalEntryManager` indeed receives `app_core` and can access `app_core.journal_service`.
The type hint `journal_service: JournalService` in the `__init__` signature will still work if `JournalService` is imported under `TYPE_CHECKING`.

Let's proceed with updating `app/accounting/journal_entry_manager.py`.
</think>

You are absolutely right to insist on thoroughness. That `ImportError` due to a circular dependency is a classic issue that needs careful untangling. My apologies for not catching it in the previous rounds.

**Error Analysis:**

The traceback clearly shows a circular import:
1.  `app/services/__init__.py` starts loading and attempts to import `app.services.journal_service`.
2.  `app.services.journal_service.py` starts loading. It imports `app.core.database_manager`.
3.  This leads (through `app.core.__init__` -> `app.core.application_core` -> `app.accounting.__init__`) to `app.accounting.journal_entry_manager.py` being imported.
4.  `app.accounting.journal_entry_manager.py` then attempts to import `JournalService` from `app.services.journal_service`.
5.  At this point, `app.services.journal_service` is still in the middle of its own import process (it hasn't finished importing everything it needs yet, like `DatabaseManager`), so the name `JournalService` is not yet defined in its module namespace. This results in the `ImportError`.

**Chosen Solution: Using Type Hinting with `TYPE_CHECKING`**

The `JournalEntryManager` receives an instance of `JournalService` through dependency injection in its constructor from `ApplicationCore`. It does not strictly need to import `JournalService` at the module level for runtime functionality, only for type hinting. We can break the cycle by moving the import into a `TYPE_CHECKING` block.

**Execution Plan:**

1.  **Modify `app/accounting/journal_entry_manager.py`**:
    *   Remove the direct top-level import: `from app.services.journal_service import JournalService`.
    *   Ensure `from typing import TYPE_CHECKING` is present.
    *   Add the import for `JournalService` under an `if TYPE_CHECKING:` block. This makes it available for type hints without causing a runtime import cycle.
    *   The constructor signature `journal_service: JournalService` will then use this conditional import for type checking.

I will now provide the complete updated `app/accounting/journal_entry_manager.py` file.

---
**Complete Updated File: `app/accounting/journal_entry_manager.py`**
---
```python
# File: app/accounting/journal_entry_manager.py
from typing import List, Optional, Any, Dict, TYPE_CHECKING
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.orm import selectinload

from app.models import JournalEntry, JournalEntryLine, RecurringPattern, FiscalPeriod, Account
from app.models.business.bank_account import BankAccount
from app.models.business.bank_transaction import BankTransaction
# Removed: from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.utils.result import Result
from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData 
from app.common.enums import JournalTypeEnum, BankTransactionTypeEnum

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from app.services.journal_service import JournalService # Import for type hinting only

class JournalEntryManager:
    def __init__(self, 
                 journal_service: "JournalService", # Use string literal or rely on TYPE_CHECKING import
                 account_service: AccountService, 
                 fiscal_period_service: FiscalPeriodService, 
                 app_core: "ApplicationCore"):
        self.journal_service = journal_service
        self.account_service = account_service
        self.fiscal_period_service = fiscal_period_service
        self.app_core = app_core
        self.logger = app_core.logger

    async def create_journal_entry(self, entry_data: JournalEntryData, session: Optional[AsyncSession] = None) -> Result[JournalEntry]:
        async def _create_je_logic(current_session: AsyncSession):
            fiscal_period_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= entry_data.entry_date, FiscalPeriod.end_date >= entry_data.entry_date, FiscalPeriod.status == 'Open')
            fiscal_period_res = await current_session.execute(fiscal_period_stmt); fiscal_period = fiscal_period_res.scalars().first()
            if not fiscal_period: return Result.failure([f"No open fiscal period for entry date {entry_data.entry_date} or period not open."])
            
            entry_no_str = await self.app_core.db_manager.execute_scalar("SELECT core.get_next_sequence_value($1);", "journal_entry", session=current_session)
            if not entry_no_str: return Result.failure(["Failed to generate journal entry number."])
            
            current_user_id = entry_data.user_id
            journal_entry_orm = JournalEntry(entry_no=entry_no_str, journal_type=entry_data.journal_type, entry_date=entry_data.entry_date, fiscal_period_id=fiscal_period.id, description=entry_data.description, reference=entry_data.reference, is_recurring=entry_data.is_recurring, recurring_pattern_id=entry_data.recurring_pattern_id, is_posted=False, source_type=entry_data.source_type, source_id=entry_data.source_id, created_by_user_id=current_user_id, updated_by_user_id=current_user_id)
            for i, line_dto in enumerate(entry_data.lines, 1):
                account_stmt = select(Account).where(Account.id == line_dto.account_id); account_res = await current_session.execute(account_stmt); account = account_res.scalars().first()
                if not account or not account.is_active: return Result.failure([f"Invalid or inactive account ID {line_dto.account_id} on line {i}."])
                line_orm = JournalEntryLine(line_number=i, account_id=line_dto.account_id, description=line_dto.description, debit_amount=line_dto.debit_amount, credit_amount=line_dto.credit_amount, currency_code=line_dto.currency_code, exchange_rate=line_dto.exchange_rate, tax_code=line_dto.tax_code, tax_amount=line_dto.tax_amount, dimension1_id=line_dto.dimension1_id, dimension2_id=line_dto.dimension2_id)
                journal_entry_orm.lines.append(line_orm)
            current_session.add(journal_entry_orm); await current_session.flush(); await current_session.refresh(journal_entry_orm)
            if journal_entry_orm.lines: await current_session.refresh(journal_entry_orm, attribute_names=['lines'])
            return Result.success(journal_entry_orm)
        if session: return await _create_je_logic(session)
        else:
            try:
                async with self.app_core.db_manager.session() as new_session: # type: ignore
                    return await _create_je_logic(new_session)
            except Exception as e: 
                self.logger.error(f"Error creating JE with new session: {e}", exc_info=True)
                return Result.failure([f"Failed to save JE: {str(e)}"])

    async def update_journal_entry(self, entry_id: int, entry_data: JournalEntryData) -> Result[JournalEntry]:
        async with self.app_core.db_manager.session() as session: # type: ignore
            existing_entry = await session.get(JournalEntry, entry_id, options=[selectinload(JournalEntry.lines)])
            if not existing_entry: return Result.failure([f"JE ID {entry_id} not found for update."])
            if existing_entry.is_posted: return Result.failure([f"Cannot update posted JE: {existing_entry.entry_no}."])
            fp_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= entry_data.entry_date, FiscalPeriod.end_date >= entry_data.entry_date, FiscalPeriod.status == 'Open')
            fp_res = await session.execute(fp_stmt); fiscal_period = fp_res.scalars().first()
            if not fiscal_period: return Result.failure([f"No open fiscal period for new entry date {entry_data.entry_date} or period not open."])
            current_user_id = entry_data.user_id
            existing_entry.journal_type = entry_data.journal_type; existing_entry.entry_date = entry_data.entry_date
            existing_entry.fiscal_period_id = fiscal_period.id; existing_entry.description = entry_data.description
            existing_entry.reference = entry_data.reference; existing_entry.is_recurring = entry_data.is_recurring
            existing_entry.recurring_pattern_id = entry_data.recurring_pattern_id
            existing_entry.source_type = entry_data.source_type; existing_entry.source_id = entry_data.source_id
            existing_entry.updated_by_user_id = current_user_id
            for line in list(existing_entry.lines): await session.delete(line)
            existing_entry.lines.clear(); await session.flush() 
            new_lines_orm: List[JournalEntryLine] = []
            for i, line_dto in enumerate(entry_data.lines, 1):
                acc_stmt = select(Account).where(Account.id == line_dto.account_id); acc_res = await session.execute(acc_stmt); account = acc_res.scalars().first()
                if not account or not account.is_active: raise ValueError(f"Invalid or inactive account ID {line_dto.account_id} on line {i} during update.")
                new_lines_orm.append(JournalEntryLine(line_number=i, account_id=line_dto.account_id, description=line_dto.description, debit_amount=line_dto.debit_amount, credit_amount=line_dto.credit_amount, currency_code=line_dto.currency_code, exchange_rate=line_dto.exchange_rate, tax_code=line_dto.tax_code, tax_amount=line_dto.tax_amount, dimension1_id=line_dto.dimension1_id, dimension2_id=line_dto.dimension2_id))
            existing_entry.lines.extend(new_lines_orm); session.add(existing_entry) 
            try:
                await session.flush(); await session.refresh(existing_entry)
                if existing_entry.lines: await session.refresh(existing_entry, attribute_names=['lines'])
                return Result.success(existing_entry)
            except Exception as e: self.logger.error(f"Error updating JE ID {entry_id}: {e}", exc_info=True); return Result.failure([f"Failed to update JE: {str(e)}"])

    async def post_journal_entry(self, entry_id: int, user_id: int, session: Optional[AsyncSession] = None) -> Result[JournalEntry]:
        async def _post_je_logic(current_session: AsyncSession):
            entry = await current_session.get(
                JournalEntry, entry_id, 
                options=[selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account)]
            )
            if not entry: return Result.failure([f"JE ID {entry_id} not found."])
            if entry.is_posted: return Result.failure([f"JE '{entry.entry_no}' is already posted."])
            
            fiscal_period = await current_session.get(FiscalPeriod, entry.fiscal_period_id)
            if not fiscal_period or fiscal_period.status != 'Open': 
                return Result.failure([f"Cannot post. Fiscal period not open. Status: {fiscal_period.status if fiscal_period else 'Unknown'}."])
            
            entry.is_posted = True
            entry.updated_by_user_id = user_id
            current_session.add(entry)
            await current_session.flush()
            
            for line in entry.lines:
                if line.account and line.account.is_bank_account:
                    bank_account_stmt = select(BankAccount).where(BankAccount.gl_account_id == line.account_id)
                    bank_account_res = await current_session.execute(bank_account_stmt)
                    linked_bank_account = bank_account_res.scalars().first()

                    if linked_bank_account:
                        bank_txn_amount = line.debit_amount - line.credit_amount
                        bank_txn_type_enum: BankTransactionTypeEnum
                        if bank_txn_amount > Decimal(0): bank_txn_type_enum = BankTransactionTypeEnum.DEPOSIT
                        elif bank_txn_amount < Decimal(0): bank_txn_type_enum = BankTransactionTypeEnum.WITHDRAWAL
                        else: continue 

                        new_bank_txn = BankTransaction(
                            bank_account_id=linked_bank_account.id,
                            transaction_date=entry.entry_date, value_date=entry.entry_date,
                            transaction_type=bank_txn_type_enum.value,
                            description=f"JE: {entry.entry_no} - {line.description or entry.description or 'Journal Posting'}",
                            reference=entry.entry_no, amount=bank_txn_amount,
                            is_from_statement=False, is_reconciled=False,
                            journal_entry_id=entry.id,
                            created_by_user_id=user_id, updated_by_user_id=user_id
                        )
                        current_session.add(new_bank_txn)
                        self.logger.info(f"Auto-created BankTransaction for JE line {line.id} (Account: {line.account.code}) linked to Bank Account {linked_bank_account.id}")
                    else:
                        self.logger.warning(f"JE line {line.id} affects GL account {line.account.code} which is_bank_account=True, but no BankAccount record is linked to it. No BankTransaction created.")
            
            await current_session.flush()
            await current_session.refresh(entry)
            return Result.success(entry)

        if session: return await _post_je_logic(session)
        else:
            try:
                async with self.app_core.db_manager.session() as new_session: # type: ignore
                    return await _post_je_logic(new_session)
            except Exception as e: 
                self.logger.error(f"Error posting JE ID {entry_id} with new session: {e}", exc_info=True)
                return Result.failure([f"Failed to post JE: {str(e)}"])

    async def reverse_journal_entry(self, entry_id: int, reversal_date: date, description: Optional[str], user_id: int) -> Result[JournalEntry]:
        async with self.app_core.db_manager.session() as session: # type: ignore
            original_entry = await session.get(JournalEntry, entry_id, options=[selectinload(JournalEntry.lines)])
            if not original_entry: return Result.failure([f"JE ID {entry_id} not found for reversal."])
            if not original_entry.is_posted: return Result.failure(["Only posted entries can be reversed."])
            if original_entry.is_reversed or original_entry.reversing_entry_id is not None: return Result.failure([f"Entry '{original_entry.entry_no}' is already reversed."])
            reversal_fp_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= reversal_date, FiscalPeriod.end_date >= reversal_date, FiscalPeriod.status == 'Open')
            reversal_fp_res = await session.execute(reversal_fp_stmt); reversal_fiscal_period = reversal_fp_res.scalars().first()
            if not reversal_fiscal_period: return Result.failure([f"No open fiscal period for reversal date {reversal_date} or period not open."])
            
            reversal_lines_dto: List[JournalEntryLineData] = []
            for orig_line in original_entry.lines:
                reversal_lines_dto.append(JournalEntryLineData(account_id=orig_line.account_id, description=f"Reversal: {orig_line.description or ''}", debit_amount=orig_line.credit_amount, credit_amount=orig_line.debit_amount, currency_code=orig_line.currency_code, exchange_rate=orig_line.exchange_rate, tax_code=orig_line.tax_code, tax_amount=-orig_line.tax_amount if orig_line.tax_amount is not None else Decimal(0), dimension1_id=orig_line.dimension1_id, dimension2_id=orig_line.dimension2_id))
            reversal_je_data = JournalEntryData(journal_type=original_entry.journal_type, entry_date=reversal_date, description=description or f"Reversal of entry {original_entry.entry_no}", reference=f"REV:{original_entry.entry_no}", is_posted=False, source_type="JournalEntryReversalSource", source_id=original_entry.id, user_id=user_id, lines=reversal_lines_dto)
            create_reversal_result = await self.create_journal_entry(reversal_je_data, session=session)
            if not create_reversal_result.is_success or not create_reversal_result.value: return Result.failure(["Failed to create reversal JE."] + create_reversal_result.errors)
            reversal_je_orm = create_reversal_result.value
            original_entry.is_reversed = True; original_entry.reversing_entry_id = reversal_je_orm.id
            original_entry.updated_by_user_id = user_id; session.add(original_entry)
            try:
                await session.flush(); await session.refresh(reversal_je_orm)
                if reversal_je_orm.lines: await session.refresh(reversal_je_orm, attribute_names=['lines'])
                return Result.success(reversal_je_orm)
            except Exception as e: self.logger.error(f"Error reversing JE ID {entry_id} (flush/commit stage): {e}", exc_info=True); return Result.failure([f"Failed to finalize reversal: {str(e)}"])

    def _calculate_next_generation_date(self, last_date: date, frequency: str, interval: int, day_of_month: Optional[int] = None, day_of_week: Optional[int] = None) -> date:
        next_date = last_date
        if frequency == 'Monthly':
            next_date = last_date + relativedelta(months=interval)
            if day_of_month:
                try: next_date = next_date.replace(day=day_of_month)
                except ValueError: next_date = next_date + relativedelta(day=31) 
        elif frequency == 'Yearly':
            next_date = last_date + relativedelta(years=interval)
            if day_of_month:
                try: next_date = next_date.replace(day=day_of_month, month=last_date.month)
                except ValueError: next_date = next_date.replace(month=last_date.month) + relativedelta(day=31)
        elif frequency == 'Weekly':
            next_date = last_date + relativedelta(weeks=interval)
            if day_of_week is not None: 
                 current_weekday = next_date.weekday() 
                 days_to_add = (day_of_week - current_weekday + 7) % 7
                 next_date += timedelta(days=days_to_add)
        elif frequency == 'Daily': next_date = last_date + relativedelta(days=interval)
        elif frequency == 'Quarterly':
            next_date = last_date + relativedelta(months=interval * 3)
            if day_of_month:
                try: next_date = next_date.replace(day=day_of_month)
                except ValueError: next_date = next_date + relativedelta(day=31)
        else: raise NotImplementedError(f"Frequency '{frequency}' not supported for next date calculation.")
        return next_date

    async def generate_recurring_entries(self, as_of_date: date, user_id: int) -> List[Result[JournalEntry]]:
        patterns_due: List[RecurringPattern] = await self.journal_service.get_recurring_patterns_due(as_of_date); generated_results: List[Result[JournalEntry]] = []
        for pattern in patterns_due:
            if not pattern.template_journal_entry: self.logger.error(f"Template JE not loaded for pattern ID {pattern.id}. Skipping."); generated_results.append(Result.failure([f"Template JE not loaded for pattern '{pattern.name}'."])); continue
            entry_date_for_new_je = pattern.next_generation_date; 
            if not entry_date_for_new_je : continue 
            template_entry = pattern.template_journal_entry
            new_je_lines_data = [JournalEntryLineData(account_id=line.account_id, description=line.description, debit_amount=line.debit_amount, credit_amount=line.credit_amount, currency_code=line.currency_code, exchange_rate=line.exchange_rate, tax_code=line.tax_code, tax_amount=line.tax_amount, dimension1_id=line.dimension1_id, dimension2_id=line.dimension2_id) for line in template_entry.lines]
            new_je_data = JournalEntryData(journal_type=template_entry.journal_type, entry_date=entry_date_for_new_je, description=f"{pattern.description or template_entry.description or ''} (Recurring - {pattern.name})", reference=template_entry.reference, user_id=user_id, lines=new_je_lines_data, recurring_pattern_id=pattern.id, source_type="RecurringPattern", source_id=pattern.id)
            create_result = await self.create_journal_entry(new_je_data); generated_results.append(create_result)
            if create_result.is_success:
                async with self.app_core.db_manager.session() as session: # type: ignore
                    pattern_to_update = await session.get(RecurringPattern, pattern.id)
                    if pattern_to_update:
                        pattern_to_update.last_generated_date = entry_date_for_new_je
                        try:
                            next_gen = self._calculate_next_generation_date(pattern_to_update.last_generated_date, pattern_to_update.frequency, pattern_to_update.interval_value, pattern_to_update.day_of_month, pattern_to_update.day_of_week)
                            if pattern_to_update.end_date and next_gen > pattern_to_update.end_date: pattern_to_update.next_generation_date = None; pattern_to_update.is_active = False 
                            else: pattern_to_update.next_generation_date = next_gen
                        except NotImplementedError: pattern_to_update.next_generation_date = None; pattern_to_update.is_active = False; self.logger.warning(f"Next gen date calc not implemented for pattern {pattern_to_update.name}, deactivating.") # type: ignore
                        pattern_to_update.updated_by_user_id = user_id; session.add(pattern_to_update); await session.commit()
                    else: self.logger.error(f"Failed to re-fetch pattern ID {pattern.id} for update after recurring JE generation.") 
        return generated_results

    async def get_journal_entry_for_dialog(self, entry_id: int) -> Optional[JournalEntry]:
        return await self.journal_service.get_by_id(entry_id)

    async def get_journal_entries_for_listing(self, filters: Optional[Dict[str, Any]] = None) -> Result[List[Dict[str, Any]]]:
        filters = filters or {}
        try:
            summary_data = await self.journal_service.get_all_summary(start_date_filter=filters.get("start_date"),end_date_filter=filters.get("end_date"),status_filter=filters.get("status"),entry_no_filter=filters.get("entry_no"),description_filter=filters.get("description"),journal_type_filter=filters.get("journal_type"))
            return Result.success(summary_data)
        except Exception as e: self.logger.error(f"Error fetching JE summaries for listing: {e}", exc_info=True); return Result.failure([f"Failed to retrieve journal entry summaries: {str(e)}"])
```

**Validation of the fix for `app/accounting/journal_entry_manager.py`:**

*   **Line-by-Line Diff (Conceptual)**:
    *   Removed `from app.services.journal_service import JournalService` from top-level imports.
    *   Added `from app.services.journal_service import JournalService` inside `if TYPE_CHECKING:` block.
    *   The constructor signature `__init__(self, journal_service: "JournalService", ...)` uses a string literal for `JournalService` (or would correctly resolve if `JournalService` were in the `TYPE_CHECKING` block). The current file from `changes_to_codebase_corresponding_to_schema_v1.04.md` directly uses `journal_service: JournalService` in the signature without a string literal, relying on the `TYPE_CHECKING` block. This is good.
    *   The line `self.journal_service = journal_service` correctly assigns the injected instance.
    *   All other imports (like `BankTransaction`, `BankTransactionTypeEnum`) and logic within the methods (like `post_journal_entry` auto-creating `BankTransaction`) are preserved from the latest version.
*   **Correctness**: This change correctly breaks the import cycle at runtime while still allowing type checkers to understand the type of `journal_service`.
*   **No Omissions**: All other functionalities of `JournalEntryManager` from the file (`changes_to_codebase_corresponding_to_schema_v1.04.md`) have been preserved.

**Conclusion for Error Fix:**
The `ImportError` should now be resolved. The application should be able to start, allowing us to proceed with further reviewing and updating the `README.md` and `Technical_Design_Specification_Document.md`.

Now, I will proceed with the update of the two documentation files based on the `changes_to_codebase_corresponding_to_schema_v1.04.md` and the latest schema information.

---
**Updated File: `README.md` (Reflecting schema v1.0.4 changes)**
---
(Using the previous complete README I generated, and integrating the new bank reconciliation features, CSV import, and other minor updates based on the latest files.)

```markdown
# SG Bookkeeper

<div align="center">

<!-- Replace with actual logo if available -->
<img src="https://raw.githubusercontent.com/nordeim/SG-Bookkeeper/refs/heads/main/home_screen.png" alt="SG Bookkeeper Logo" width="600"/>

**Singapore-Focused Small Business Accounting Software**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PySide6 6.9+](https://img.shields.io/badge/UI-PySide6_6.9-green.svg)](https://doc.qt.io/qtforpython/)
[![PostgreSQL 14+](https://img.shields.io/badge/DB-PostgreSQL_14+-blue.svg)](https://www.postgresql.org/)
[![SQLAlchemy 2.0+](https://img.shields.io/badge/ORM-SQLAlchemy_2.0-orange.svg)](https://www.sqlalchemy.org/)
[![Asyncpg](https://img.shields.io/badge/Async-Asyncpg-purple.svg)](https://github.com/MagicStack/asyncpg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

[Key Features](#key-features) • [Technology Stack](#technology-stack) • [Installation](#installation) • [Usage](#usage-guide) • [Project Structure](#project-structure) • [Contributing](#contributing) • [Roadmap](#roadmap) • [License](#license)

</div>

## Overview

SG Bookkeeper is a comprehensive, cross-platform desktop application designed to meet the accounting and bookkeeping needs of small to medium-sized businesses (SMBs) in Singapore. Built with Python and leveraging the power of PySide6 for a modern user interface and PostgreSQL for robust data management, it offers professional-grade financial tools tailored to Singapore's regulatory environment.

The application features a double-entry accounting core, GST management, interactive financial reporting, modules for essential business operations (Customer, Vendor, Product/Service Management, Sales & Purchase Invoicing, Payments), Bank Account management with transaction entry, **CSV bank statement import**, a **full Bank Reconciliation module**, and comprehensive User/Role/Permission administration including Audit Logs. Its goal is to provide an intuitive, powerful, and compliant solution that empowers business owners and accountants.

### Why SG Bookkeeper?

-   **Singapore-Centric**: Designed with Singapore Financial Reporting Standards (SFRS), GST regulations (including the 9% rate), and IRAS compliance considerations at its core.
-   **Professional Grade**: Implements a full double-entry system, detailed audit trails (via database triggers and viewable UI), and robust data validation using Pydantic DTOs.
-   **User-Friendly Interface**: Aims for an intuitive experience for users who may not be accounting experts, while providing depth for professionals. Most core modules have functional UIs with features like advanced product search in invoices, and clear data entry forms.
-   **Open Source & Local First**: Transparent development. Your financial data stays on your local machine or private server, ensuring privacy and control. No subscription fees.
-   **Modern & Performant**: Utilizes asynchronous operations for a responsive UI and efficient database interactions, with a dedicated asyncio event loop.

## Key Features

*(Status: Implemented, UI Implemented, Backend Implemented, Foundational (DB/Models ready), Planned)*

### Core Accounting
-   **Comprehensive Double-Entry Bookkeeping** (Implemented)
-   **Customizable Hierarchical Chart of Accounts** (Implemented - UI for CRUD)
-   **General Ledger with detailed transaction history** (Implemented - Report generation, on-screen view, export, with dimension filtering options)
-   **Journal Entry System** (Implemented - UI for General Journal with Journal Type filter; transaction-specific JEs generated on posting of source documents; JEs also auto-created from Bank Reconciliation for statement-only items. Posting a JE affecting a bank-linked GL account now auto-creates a system `BankTransaction`.)
-   **Multi-Currency Support** (Foundational - Models, CurrencyManager exist. UI integration in transactions uses it.)
-   **Fiscal Year and Period Management** (Implemented - UI in Settings for FY creation and period auto-generation.)
-   **Budgeting and Variance Analysis** (Foundational - Models exist. UI/Logic planned.)

### Singapore Tax Compliance
-   **GST Tracking and Calculation** (Backend Implemented)
-   **GST F5 Return Data Preparation & Finalization** (Implemented - Backend for data prep & finalization with JE settlement. UI in Reports tab. Enhanced Excel export with transaction details per box.)
-   **Income Tax Estimation Aids** (Planned)
-   **Withholding Tax Management** (Foundational)

### Business Operations
-   **Customer Management** (Implemented)
-   **Vendor Management** (Implemented)
-   **Product and Service Management** (Implemented)
-   **Sales Invoicing and Accounts Receivable** (Implemented - Full lifecycle including WAC inventory JE)
-   **Purchase Invoicing and Accounts Payable** (Implemented - Full lifecycle including WAC inventory JE)
-   **Payment Processing and Allocation** (Implemented - UI for Customer Receipts & Vendor Payments, allocation, JE posting.)
-   **Inventory Control (Weighted Average Cost)** (Implemented)

### Banking
-   **Bank Account Management** (Implemented - Full CRUD and listing UI, linkage to GL.)
-   **Manual Bank Transaction Entry** (Implemented - UI for manual entry, listed per account.)
-   **CSV Bank Statement Import** (Implemented - UI dialog (`CSVImportConfigDialog`) for configuring and importing transactions.)
-   **Bank Reconciliation Module** (Implemented - UI (`BankReconciliationWidget`) for matching statement items with system transactions, identifying discrepancies, creating adjustment JEs, and saving reconciliation state. Database tables and logic support this.)

### Reporting & Analytics
-   **Standard Financial Statements**: Balance Sheet, Profit & Loss, Trial Balance, General Ledger (Implemented - UI in Reports tab, PDF/Excel export, enhanced GL with dimension filtering.)
-   **Dashboard KPIs** (Implemented - Displays YTD Revenue, Expenses, Net Profit; Current Cash, AR, AP balances in base currency.)
-   **Cash Flow Statement** (Planned)
-   **GST Reports** (Implemented - See GST F5 above.)
-   **Customizable Reporting Engine** (Foundational)

### System & Security
-   **User Authentication & RBAC** (Implemented - UI for Users, Roles, Permissions.)
-   **Comprehensive Audit Trails** (Implemented - DB triggers, UI for viewing Action Log and Data Change History in Settings.)
-   **PostgreSQL Database Backend** (Implemented)
-   **Data Backup and Restore Utilities** (Planned)

## Technology Stack
-   **Programming Language**: Python 3.9+ (up to 3.12)
-   **UI Framework**: PySide6 6.9.0+
-   **Database**: PostgreSQL 14+
-   **ORM**: SQLAlchemy 2.0+ (Async ORM with `asyncpg`)
-   **Async DB Driver**: `asyncpg`
-   **Data Validation (DTOs)**: Pydantic V2 (with `email-validator`)
-   **Password Hashing**: `bcrypt`
-   **Reporting Libraries**: `reportlab` (PDF), `openpyxl` (Excel)
-   **Dependency Management**: Poetry
-   **Date/Time Utilities**: `python-dateutil`

## Installation
*(This section remains largely the same as the previous version, as no new core dependencies or fundamental setup steps were introduced by the bank reconciliation feature itself. The key is ensuring the database schema matches v1.0.4 or later.)*

### Prerequisites
-   Python 3.9 or higher
-   PostgreSQL Server 14 or higher
-   Poetry
-   Git

### Developer Installation Steps
1.  **Clone Repository**
2.  **Install Dependencies**: `poetry install`
3.  **Prepare PostgreSQL User and Database** (e.g., `sgbookkeeper_user`, database `sg_bookkeeper`)
4.  **Configure `config.ini`**: In user's config directory (e.g., `~/.config/SGBookkeeper/config.ini`), set database credentials.
5.  **Initialize Database**:
    ```bash
    poetry run sg_bookkeeper_db_init --user YOUR_POSTGRES_ADMIN_USER --password YOUR_POSTGRES_ADMIN_PASSWORD --dbname sg_bookkeeper --drop-existing
    ```
    *(The `initial_data.sql` script now includes grants for `sgbookkeeper_user`)*
6.  **Compile Qt Resources**: `poetry run pyside6-rcc resources/resources.qrc -o app/resources_rc.py`
7.  **Run Application**: `poetry run sg_bookkeeper` (Default admin: `admin`/`password` - change on first login)

## Usage Guide
*(Updated to include new Banking features)*
-   **Banking C.R.U.D Tab**:
    *   Manage Bank Accounts (add, edit, toggle active).
    *   View transactions for a selected account.
    *   Manually add bank transactions.
    *   **Import Bank Statements**: Use the "Import Statement (CSV)" action to import transactions from a CSV file, configuring column mappings as needed.
-   **Bank Reconciliation Tab**:
    *   Select a bank account, enter the statement end date and ending balance.
    *   Load unreconciled statement items (from imports) and system-generated bank transactions.
    *   Match items between the two lists. The reconciliation summary will update dynamically.
    *   For statement items not in your books (e.g., bank charges, interest), use the "Add Journal Entry" button to create the necessary system entries. These will then appear in the system transactions list for matching.
    *   Once the "Difference" in the summary is zero, click "Save Reconciliation" to finalize and mark transactions as reconciled.
-   Other modules (Dashboard, Accounting, Sales, Purchases, Payments, Customers, Vendors, Products, Reports, Settings) function as previously described, with enhancements like Journal Type filter for JEs and Dimension filtering for GL reports.

## Project Structure
*(Key additions for Banking/Reconciliation)*
```
sg_bookkeeper/
├── app/
│   ├── ui/
│   │   ├── banking/
│   │   │   ├── bank_reconciliation_widget.py   # New UI for reconciliation
│   │   │   ├── reconciliation_table_model.py # New Table Model
│   │   │   ├── csv_import_config_dialog.py   # New Dialog for CSV import
│   │   │   └── ... (other banking UI files)
│   ├── models/
│   │   ├── business/
│   │   │   └── bank_reconciliation.py        # New ORM Model
│   ├── services/
│   │   └── business_services.py          # Includes BankReconciliationService
│   ├── business_logic/
│   │   └── bank_transaction_manager.py   # Updated with import/matching logic
│   └── ... (other directories as before)
├── resources/
│   ├── icons/
│   │   └── import_csv.svg                # New icon
└── ... (other files and directories as before)
```

## Database Schema
The PostgreSQL database schema now includes `business.bank_reconciliations` table, and `business.bank_accounts` and `business.bank_transactions` have been updated with new fields and foreign keys to support the bank reconciliation process. A new trigger (`update_bank_account_balance_trigger_func`) automatically maintains `bank_accounts.current_balance`. Refer to `scripts/schema.sql` (reflecting v1.0.4) for full details.

## Development
*(No changes to development workflow)*

## Contributing
*(No changes to contribution guidelines)*

## Roadmap

### Recently Completed (v1.0.4 Features - Current State)
-   **Banking Module Enhancements**:
    *   **Bank Reconciliation UI & Core Logic**: Interface for selecting account, statement date/balance. Loading unreconciled statement items and system transactions. UI calculations for reconciliation summary. Ability to "Match Selected" items. "Save Reconciliation" functionality.
    *   **CSV Bank Statement Import**: UI dialog (`CSVImportConfigDialog`) for configuring column mappings and importing transactions.
    *   **Journal Entry for Statement Items**: UI button in reconciliation screen to pre-fill `JournalEntryDialog` for unmatched statement items. Posting these JEs now auto-creates corresponding system `BankTransaction` records.
-   Database schema updates for bank reconciliation.
-   Automatic `bank_accounts.current_balance` updates via database trigger.
-   `JournalEntryManager` auto-creates `BankTransaction` records.
-   **Dashboard KPIs**: Basic display of YTD P&L figures, Cash, AR, AP.

### Current Focus / Next Steps
-   **Automated Testing (Phase 1 - CRITICAL)**:
    *   Establish a comprehensive test suite: unit tests for services/managers, integration tests for core workflows (e.g., invoice posting, payment allocation, bank reconciliation save), and basic UI tests for critical paths.
-   **Refine Bank Reconciliation**:
    *   Handling of complex matches (e.g., one-to-many, many-to-one statement lines to system transactions).
    *   UI improvements for displaying matched items and reconciliation history.
    *   More robust error handling and user feedback during CSV import and reconciliation processes.
    *   Persisting "matched" state within a reconciliation session before final save.
-   **Enhance Dashboard KPIs**:
    *   Add more KPIs (e.g., AR/AP Aging, Quick Ratio, Current Ratio).
    *   Consider graphical representations.
    *   Allow user customization or period selection for KPIs.

### Long-term
-   Advanced reporting and analytics.
-   Inventory Control enhancements.
-   Multi-company support.
-   Cloud synchronization options.
-   Enhanced Tax Compliance features.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

---
**Updated File: `Technical_Design_Specification_Document.md` (v13.0)**
---
(This will be an update to the v12.0 I previously generated, incorporating the v1.0.4 schema changes and new banking/reconciliation features.)

```markdown
# Technical Design Specification Document: SG Bookkeeper (v13.0)

**Version:** 13.0
**Date:** 2025-06-03 

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version 13.0, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities up to schema version 1.0.4. This version specifically details the implementation of:
*   **Bank Reconciliation Module**: Comprehensive UI and backend logic for reconciling bank statements with system bank transactions, including matching, creating adjustment journal entries, and saving reconciliation status.
*   **CSV Bank Statement Import**: Functionality to import bank transactions from CSV files with configurable column mapping.
*   **Automated Bank Transaction Creation from Journal Entries**: Posting a journal entry that affects a bank-linked GL account now automatically generates a corresponding system bank transaction.
*   **Dashboard KPIs (Initial Implementation)**: Display of key financial indicators like YTD P&L figures, cash balance, and AR/AP totals.
*   **Database Enhancements**: Introduction of the `business.bank_reconciliations` table, new fields in `bank_accounts` and `bank_transactions`, and a database trigger for automatic bank balance updates.
These build upon previously documented features like Payments, Audit Log UI, enhanced GST Reporting, Sales/Purchase Invoicing, and core accounting/admin functionalities.

### 1.2 Scope
This TDS covers:
-   System Architecture.
-   Database Schema (reflecting v1.0.4 changes).
-   Key UI Implementation Patterns for new banking and dashboard features.
-   Core Business Logic for bank reconciliation, CSV import, and KPI generation.
-   Data Models (SQLAlchemy ORM) and Data Transfer Objects (Pydantic DTOs).
-   Security Implementation.
-   Deployment and Initialization procedures.
-   Current Implementation Status.

### 1.3 Intended Audience
-   Software Developers, QA Engineers, System Administrators, Technical Project Managers.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application (Python, PySide6, PostgreSQL) for SMB accounting in Singapore. Key features include double-entry bookkeeping, GST management, financial reporting, CRM/SRM, full invoicing lifecycle, payment processing, bank account management with **CSV import and a full bank reconciliation module**, **dashboard KPIs**, and comprehensive system administration.

### 1.5 Current Implementation Status
As of version 13.0 (schema v1.0.4):
*   All features from TDS v12.0.
*   **New/Enhanced Banking & Dashboard Features**:
    *   **Bank Reconciliation**: Full UI and backend logic.
    *   **CSV Bank Statement Import**: UI and backend logic.
    *   **Automatic Bank Transactions from JEs**: Implemented in `JournalEntryManager`.
    *   **Dashboard KPIs**: Initial implementation displaying core YTD P&L, Cash, AR/AP figures.
*   **Database**: Schema v1.0.4 implemented with `bank_reconciliations` table, new bank-related columns, and balance update trigger. `initial_data.sql` updated with new permissions and config keys.
*   **Audit Log Service**: Minor improvements to change summary formatting and query logic.

## 2. System Architecture
*(The high-level architecture and diagram from TDS v12.0 remain valid. New components are integrated within existing layers.)*

### 2.1 High-Level Architecture
(Diagram from TDS v12.0 is still representative)

### 2.2 Component Architecture (Updates)

#### 2.2.1 Core Components (`app/core/`)
*   **`ApplicationCore` (`app/core/application_core.py`)**:
    *   Now initializes and provides `BankReconciliationService` and `DashboardManager`.
    *   `JournalEntryManager` instantiation corrected (no longer takes `SequenceGenerator`).
    *   Corrected `CurrencyRepoService` injection for `CustomerManager` and `VendorManager`.

#### 2.2.4 Managers (Business Logic Layer)
*   **`app/accounting/JournalEntryManager`**:
    *   `create_journal_entry`: Uses DB function for `entry_no`.
    *   `post_journal_entry`: Now auto-creates `BankTransaction` records if a JE line affects a bank-linked GL account.
*   **`app/business_logic/BankTransactionManager`**:
    *   New `import_bank_statement_csv` method for CSV import.
    *   New `get_unreconciled_transactions_for_matching` method for bank reconciliation UI.
*   **`app/reporting/DashboardManager` (New)**:
    *   Located in `app/reporting/dashboard_manager.py`.
    *   `get_dashboard_kpis()`: Fetches data from various services (`FinancialStatementGenerator`, `BankAccountService`, `CustomerService`, `VendorService`, `FiscalYearService`, `CompanySettingsService`) to compute and return KPIs in a `DashboardKPIData` DTO. Handles determination of current fiscal year and base currency.

#### 2.2.5 User Interface (Presentation Layer - `app/ui/`)
*   **`app/ui/dashboard/DashboardWidget`**: Updated from placeholder to display KPIs (revenue, expenses, net profit, cash, AR/AP) fetched via `DashboardManager`. Includes a refresh mechanism.
*   **`app/ui/banking/BankReconciliationWidget` (New)**: Main UI for bank reconciliation, featuring setup controls, a summary section, and two tables for matching statement items against system transactions. Includes actions for matching, creating adjustment JEs, and saving the reconciliation.
*   **`app/ui/banking/ReconciliationTableModel` (New)**: Table model for the reconciliation tables, supporting checkable items.
*   **`app/ui/banking/CSVImportConfigDialog` (New)**: Dialog for configuring CSV bank statement imports.
*   **`app/ui/banking/BankTransactionsWidget`**: Added "Import Statement (CSV)" action.
*   **`app/ui/main_window.py`**: "Bank Reconciliation" tab added.

## 3. Data Architecture (Updates based on Schema v1.0.4)

### 3.1 Database Schema Overview
Key updates for v1.0.4 (reflected in `scripts/schema.sql`):
-   **New Table: `business.bank_reconciliations`**: Stores completed reconciliation summaries.
    *   Columns: `id`, `bank_account_id` (FK), `statement_date`, `statement_ending_balance`, `calculated_book_balance`, `reconciled_difference`, `reconciliation_date`, `notes`, `created_by_user_id` (FK), audit timestamps.
    *   Unique constraint: `(bank_account_id, statement_date)`.
-   **Table `business.bank_accounts`**:
    *   Added `last_reconciled_balance NUMERIC(15,2) NULL`.
-   **Table `business.bank_transactions`**:
    *   Added `reconciled_bank_reconciliation_id INT NULL` (FK to `bank_reconciliations.id`).
    *   Existing fields `is_from_statement BOOLEAN` and `raw_statement_data JSONB` are utilized by CSV import.
-   **New Trigger: `business.update_bank_account_balance_trigger_func()`**: Updates `bank_accounts.current_balance` automatically when `bank_transactions` are changed.
-   **Audit Triggers**: Extended to `bank_accounts` and `bank_transactions`.

### 3.2 SQLAlchemy ORM Models (`app/models/`)
*   **`app/models/business/bank_reconciliation.py`**: New `BankReconciliation` ORM model.
*   **`app/models/business/bank_account.py`**: Updated `BankAccount` model.
*   **`app/models/business/bank_transaction.py`**: Updated `BankTransaction` model.

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
*   **New DTOs**:
    *   `BankReconciliationBaseData`, `BankReconciliationCreateData`, `BankReconciliationData`.
    *   `DashboardKPIData`: For structuring KPI values.
*   `GSTTransactionLineDetail` was confirmed as added in previous reviews.
*   `SalesInvoiceSummaryData` and `PurchaseInvoiceSummaryData` confirmed to include `currency_code`.

## 4. Module and Component Specifications (Updates)

### 4.6 Banking Module (Significant Enhancements)
-   **Bank Reconciliation Workflow**:
    1.  User selects bank account, statement date, and end balance in `BankReconciliationWidget`.
    2.  `BankTransactionManager.get_unreconciled_transactions_for_matching` fetches unreconciled statement items (CSV imports) and system transactions.
    3.  UI displays items; user checks items to match. Summary auto-updates.
    4.  For unmatched statement items (e.g., bank charges), user can click "Add Journal Entry". `JournalEntryDialog` opens, pre-filled. Posting this JE auto-creates a system `BankTransaction`.
    5.  When "Difference" is zero, user clicks "Save Reconciliation".
    6.  `BankReconciliationService.save_reconciliation_details` saves the `BankReconciliation` record, updates reconciled `BankTransaction` records, and updates `BankAccount.last_reconciled_date/balance`.
-   **CSV Bank Statement Import**:
    1.  User clicks "Import Statement (CSV)" in `BankTransactionsWidget`.
    2.  `CSVImportConfigDialog` opens for file selection and column mapping.
    3.  `BankTransactionManager.import_bank_statement_csv` processes the file, creates `BankTransaction` records (marked `is_from_statement=True`, `raw_statement_data` populated).

### 4.X Dashboard Module (New Minimal Implementation)
-   **Purpose**: Provide a quick overview of key financial metrics.
-   **Manager (`DashboardManager`)**:
    *   `get_dashboard_kpis()`: Retrieves data for:
        *   YTD Revenue, Expenses, Net Profit (via `FinancialStatementGenerator`).
        *   Current Cash Balance (sum of base currency active bank accounts via `BankAccountService`).
        *   Total Outstanding AR/AP (via `CustomerService`/`VendorService` querying respective balance views).
    *   Returns data in `DashboardKPIData` DTO.
-   **UI (`DashboardWidget`)**:
    *   Displays KPIs fetched from `DashboardManager`.
    *   Includes a refresh button.

## 10. Data Flow (Updates)

*(The Data Flow for Sales Invoice Posting remains relevant. Add a new Data Flow for Bank Reconciliation. The previously generated one for Bank Reconciliation is accurate and reflects the changes.)*

**Data Flow Example: Bank Reconciliation Process**

1.  **Setup (UI: `BankReconciliationWidget`)**: User selects Bank Account, enters Statement Date & Ending Balance, clicks "Load Transactions".
2.  **Fetch Data (Managers/Services)**:
    *   `BankTransactionManager.get_unreconciled_transactions_for_matching()` fetches statement items (`is_from_statement=True`) and system transactions (`is_from_statement=False`) via `BankTransactionService`.
    *   `JournalService.get_account_balance()` fetches GL balance for the bank account.
3.  **Display & Calculate (UI)**: Transactions populate tables. Reconciliation summary (Book vs. Bank, Difference) is calculated based on *unchecked* items.
4.  **User Interaction (UI)**:
    *   **Matching**: User checks matching items. UI updates summary. (Internal "session" match).
    *   **New JE for Statement Item**: User selects an unmatched statement item (e.g., bank charge), clicks "Add Journal Entry". `JournalEntryDialog` is pre-filled. Posting the JE via `JournalEntryManager` also auto-creates a system `BankTransaction`. UI reloads transactions.
5.  **Saving (UI -> Manager -> Service)**: When Difference is zero, user clicks "Save Reconciliation".
    *   `BankReconciliationWidget` collects data (`BankReconciliationCreateData`, IDs of "cleared" transactions).
    *   This is passed to `BankReconciliationService.save_reconciliation_details` (likely via a new manager method in `BankTransactionManager` or a new `BankReconciliationManager` in the future).
    *   `BankReconciliationService`:
        1.  Creates/saves `BankReconciliation` record.
        2.  Updates matched `BankTransaction` records (sets `is_reconciled=True`, `reconciled_date`, `reconciled_bank_reconciliation_id`).
        3.  Updates `BankAccount` (`last_reconciled_date`, `last_reconciled_balance`).
        4.  All in one DB transaction.
6.  **UI Feedback**: Success/error message. UI may refresh.

## 11. Conclusion (Updated)
Version 13.0 significantly enhances SG Bookkeeper with the introduction of CSV bank statement import, a full bank reconciliation module, and an initial dashboard for KPIs. The automatic creation of bank transactions from journal entries further improves data consistency. These features, built upon the established layered architecture, bring the application much closer to a production-ready accounting tool for SMBs. The focus on meticulous implementation and schema integrity ensures a robust foundation for future development, which will critically include comprehensive automated testing and further refinements to existing modules.
```

---
https://drive.google.com/file/d/11Cv4mFJ5z4I3inVCg8nkncVsAQtuIWrl/view?usp=sharing, https://drive.google.com/file/d/13aFutu059EFwgvQM4JE5LrYT13_62ztj/view?usp=sharing, https://drive.google.com/file/d/150VU2J4NfkYirCIGqQxC5VL9a_s7jyV0/view?usp=sharing, https://drive.google.com/file/d/1Fcdn0EWCauERrISMKReM_r0_nVIQvPiH/view?usp=sharing, https://drive.google.com/file/d/1GWOGYCBqwiPra5MdbwwhwXrV2V-gc4iw/view?usp=sharing, https://drive.google.com/file/d/1IRffneWyqY8ILVvfOu3apYxB15SnhMYD/view?usp=sharing, https://drive.google.com/file/d/1QYQSJ32tb7UYfuT-VHC2vgYYS3Cw_9dz/view?usp=sharing, https://drive.google.com/file/d/1S4zRP59L2Jxru__jXeoTL2TGZ4JN_GOT/view?usp=sharing, https://drive.google.com/file/d/1X5XkobtrDHItY5dTnWRYajA9LTVvZTGy/view?usp=sharing, https://drive.google.com/file/d/1bsb7xdrTRvfFSLOJVv_YBVncejRYeX-p/view?usp=sharing, https://drive.google.com/file/d/1eU9E4v6uT69z91uEABi8xf4-L1_PUKaI/view?usp=sharing, https://drive.google.com/file/d/1fcRRxU4xYdqMgGp58OyuFDOqIcGeOIW_/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221gVm5GnROGWVVYBXkgumxd5puGZ6g5Qs3%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1hF6djKphaR51gqDKE6GLgeBnlWXdKcWU/view?usp=sharing, https://drive.google.com/file/d/1ndjSoP14ry1oCHgOguxNgNWxyP4c18ww/view?usp=sharing, https://drive.google.com/file/d/1zWrsOeANNSTZ51c666H-DxQapeSjXnZY/view?usp=sharing

