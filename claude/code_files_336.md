<think>
The application is still failing with a very similar `ImportError` due to a circular import, specifically:
`ImportError: cannot import name 'AccountService' from partially initialized module 'app.services.account_service' (most likely due to a circular import) (/cdrom/project/SG-Bookkeeper/app/services/account_service.py)`

Let's re-trace the import chain that leads to this specific error based on the new traceback:

1.  `app/main.py` -> ... (as before) ... -> `app.utils.sequence_generator`
2.  `app.utils.sequence_generator` imports `app.services.core_services.SequenceService`.
3.  This triggers loading of `app.services.__init__.py`.
4.  `app/services/__init__.py` imports `from .account_service import AccountService`.
5.  `app.services.account_service.py` starts loading. It imports `DatabaseManager`.
6.  `DatabaseManager` (via `app.core.__init__`) imports `ApplicationCore`.
7.  `app.core.application_core.py` starts loading. It imports `ChartOfAccountsManager` from `app.accounting.chart_of_accounts_manager`. (This was the one we fixed).
8.  It then imports *other managers*. The current traceback points to `app.accounting.__init__.py` (imported by `ApplicationCore`) importing `JournalEntryManager`.
9.  `app.accounting.journal_entry_manager.py` (line 15) imports `from app.services.account_service import AccountService`.

**The New Culprit for the Circular Import:**
The new direct path causing the cycle is:
`app.services.__init__` (tries to import `AccountService`)
  -> `app.services.account_service` (starts loading)
    -> ... (chain through core) ...
      -> `app.core.application_core` (starts loading)
        -> `app.accounting.__init__`
          -> `app.accounting.journal_entry_manager`
            -> `from app.services.account_service import AccountService` (tries to import `AccountService` *again* while it's still being initialized from step 2).

The previous fix was for `ChartOfAccountsManager`. Now, `JournalEntryManager` is exhibiting the same pattern.

**Root Cause Pattern:**
Managers (`ChartOfAccountsManager`, `JournalEntryManager`, etc.) are being imported directly by `ApplicationCore` at its module level. These managers, in turn, are directly importing services like `AccountService` at their module level. When `ApplicationCore` itself is part of an import chain needed by these services (e.g., `AccountService` uses `DatabaseManager` which uses `ApplicationCore` for logger/config, or `AccountService` itself takes `app_core` in `__init__`), these direct manager->service imports at module level create the circular dependency.

**Solution Strategy (Consistent with previous fix):**
Any manager that depends on a service (like `AccountService`) should receive that service instance via its constructor (dependency injection) rather than importing it directly at the module level. Type hints should use `TYPE_CHECKING` blocks or string literals.

**File to Modify:** `app/accounting/journal_entry_manager.py`

**Detailed Plan for Fixing `JournalEntryManager`:**

1.  **Modify `app/accounting/journal_entry_manager.py`**:
    *   Locate the direct import: `from app.services.account_service import AccountService`.
    *   Move this import into the `if TYPE_CHECKING:` block.
    *   The constructor signature is:
        ```python
        class JournalEntryManager:
            def __init__(self, 
                         journal_service: "JournalService", # Already a string literal / TYPE_CHECKING
                         account_service: AccountService,   # << This is the problem
                         fiscal_period_service: FiscalPeriodService, 
                         app_core: "ApplicationCore"):
        ```
        Change `account_service: AccountService` to `account_service: "AccountService"` or ensure `AccountService` is in the `TYPE_CHECKING` block.
        The constructor already takes `account_service` as an argument, so no change to how it's used (`self.account_service`) is needed, only how its type is declared.

Let's check the `TYPE_CHECKING` block in `journal_entry_manager.py` (from `project_codebase_files_set-7.md`):
```python
if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from app.services.journal_service import JournalService # Import for type hinting only
```
`AccountService` is missing here.

**Revised Plan for `app/accounting/journal_entry_manager.py`:**
1.  Remove the direct import: `from app.services.account_service import AccountService`.
2.  Add `from app.services.account_service import AccountService` inside the `if TYPE_CHECKING:` block.
3.  The constructor argument `account_service: AccountService` will now correctly use the conditionally imported type hint.

**Self-Correction/Double Check:**
Is `FiscalPeriodService` also directly imported by `JournalEntryManager`?
```python
# app/accounting/journal_entry_manager.py
# ...
from app.services.fiscal_period_service import FiscalPeriodService # << Direct import
# ...
class JournalEntryManager:
    def __init__(self, 
                 journal_service: "JournalService", 
                 account_service: AccountService,  # Will be "AccountService"
                 fiscal_period_service: FiscalPeriodService, # << Problematic if FiscalPeriodService chain leads to AppCore
                 app_core: "ApplicationCore"):
```
Yes, `FiscalPeriodService` is also directly imported. Does `FiscalPeriodService` cause a cycle?
`fiscal_period_service.py` imports `DatabaseManager`. `DatabaseManager` imports `ApplicationCore`.
So, `FiscalPeriodService` also needs the same treatment if it's part of the cycle triggered by `ApplicationCore` importing `JournalEntryManager`.

The current traceback does not explicitly point to `FiscalPeriodService` causing the *current* break, but it follows the same pattern. To be proactive and thorough, I should apply the same fix to `FiscalPeriodService` import in `JournalEntryManager`.

**Revised Plan for `app/accounting/journal_entry_manager.py` (More Thorough):**
1.  Remove direct imports:
    *   `from app.services.account_service import AccountService`
    *   `from app.services.fiscal_period_service import FiscalPeriodService`
2.  Add these to the `if TYPE_CHECKING:` block:
    *   `from app.services.account_service import AccountService`
    *   `from app.services.fiscal_period_service import FiscalPeriodService`
3.  The constructor signature arguments `account_service: AccountService` and `fiscal_period_service: FiscalPeriodService` will then use these conditional imports for type hinting.

This will ensure that `JournalEntryManager` does not cause import cycles through its service dependencies when `ApplicationCore` tries to import it. The actual service instances are correctly passed during `ApplicationCore`'s initialization phase.

Let's generate the updated `app/accounting/journal_entry_manager.py`.

I need to be extremely careful. The general principle is:
- If module A imports module B at the top level, and module B imports module C at the top level, and module C imports module A at the top level, that's a cycle.
- `ApplicationCore` imports many managers.
- Managers import services.
- Services (or their dependencies like `DatabaseManager`) might import `ApplicationCore` (often for type hints, or for `app_core` reference).

The fix is to ensure that when A imports B, B does not *at module import time* require A to be fully loaded. Constructor injection with type hints using strings or `TYPE_CHECKING` solves this for object instances.

Let's verify the instantiation order in `ApplicationCore.startup()` for the services `JournalEntryManager` depends on:
```python
# app/core/application_core.py
# ...
        self._account_service_instance = AccountService(self.db_manager, self)
        # ...
        self._fiscal_period_service_instance = FiscalPeriodService(self.db_manager) # Note: FiscalPeriodService init doesn't take app_core
        # ...
        from app.services.journal_service import JournalService 
        self._journal_service_instance = JournalService(self.db_manager, self)
        # ...
        from app.accounting.journal_entry_manager import JournalEntryManager # JEM imported later
        # ...
        self._je_manager_instance = JournalEntryManager(
            self.journal_service, # Instance available
            self.account_service, # Instance available
            self.fiscal_period_service, # Instance available
            self # app_core instance
        )
```
The instantiation order in `ApplicationCore` is correct: services are created before the managers that depend on them. The problem is purely the compile-time/module-level direct imports within the manager files.

The fix should be limited to `app/accounting/journal_entry_manager.py` for this specific traceback.
</think>

You're right to emphasize thoroughness! Another circular import error has occurred. This time, `JournalEntryManager` is implicated in a cycle with `AccountService`.

**Error Analysis:**
The traceback shows this sequence:
1.  App starts -> ... -> `app.utils.sequence_generator` imports `app.services.core_services.SequenceService`.
2.  This triggers `app.services.__init__.py` to load, which attempts to import `AccountService` from `app.services.account_service`.
3.  `app.services.account_service.py` starts loading. It has dependencies (like `DatabaseManager` which itself might depend on `ApplicationCore` being available for logger/config, or `AccountService` itself takes `app_core`).
4.  Concurrently, `app.core.application_core.py` is being imported (as part of the chain that services depend on for their `app_core` reference).
5.  `ApplicationCore` imports managers, including `JournalEntryManager` via `app.accounting.__init__`.
6.  `app.accounting.journal_entry_manager.py` then attempts a direct module-level import: `from app.services.account_service import AccountService`.

This creates the cycle: `AccountService` is in the process of being imported (triggered by `app.services.__init__`), but `ApplicationCore` (which `AccountService` or its dependencies might need to be fully functional or for type hints in constructors) tries to import `JournalEntryManager`, which then tries to import `AccountService` *again* before the first import of `AccountService` has completed.

**Solution Strategy:**
Similar to the previous fix for `ChartOfAccountsManager`, we need to modify `JournalEntryManager` to avoid a direct module-level import of services it depends on if those services (or their import chains) also depend on `ApplicationCore` (which imports `JournalEntryManager`). The dependencies (`AccountService`, `FiscalPeriodService`) should be passed via the constructor, and type hints should use conditional imports (`if TYPE_CHECKING:`) or string literals.

**File to Modify:** `app/accounting/journal_entry_manager.py`

**Detailed Plan & Checklist:**

1.  **Modify `app/accounting/journal_entry_manager.py`**:
    *   [X] **Locate Direct Imports**: Identify `from app.services.account_service import AccountService` and `from app.services.fiscal_period_service import FiscalPeriodService`.
    *   [X] **Move to `TYPE_CHECKING`**:
        *   Remove these direct imports from the top of the file.
        *   Add them inside the `if TYPE_CHECKING:` block. The block already exists for `ApplicationCore` and `JournalService`.
        ```python
        if TYPE_CHECKING:
            from app.core.application_core import ApplicationCore
            from app.services.journal_service import JournalService
            from app.services.account_service import AccountService  # ADDED HERE
            from app.services.fiscal_period_service import FiscalPeriodService # ADDED HERE
        ```
    *   [X] **Verify Constructor Signature**: The constructor is:
        ```python
        def __init__(self, 
                     journal_service: "JournalService", 
                     account_service: AccountService,   # This will now use the conditional import
                     fiscal_period_service: FiscalPeriodService, # This will now use the conditional import
                     app_core: "ApplicationCore"):
        ```
        This is correct. Python will use the type hints from the `TYPE_CHECKING` block if type checking, and at runtime, it will accept the passed instances. String literals could also be used (e.g., `account_service: "AccountService"`) but the `TYPE_CHECKING` approach is generally preferred for better IDE support when types are available during static analysis.
    *   [X] **No Change to Instance Usage**: The usage of `self.account_service` and `self.fiscal_period_service` within the manager's methods will remain the same.

This change should resolve the circular import by deferring the resolution of `AccountService` and `FiscalPeriodService` types until they are actually needed for type checking, not at initial module parsing time. `ApplicationCore` ensures these services are instantiated before `JournalEntryManager` and correctly injected.

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
# REMOVED: from app.services.account_service import AccountService
# REMOVED: from app.services.fiscal_period_service import FiscalPeriodService
from app.utils.result import Result
from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData 
from app.common.enums import JournalTypeEnum, BankTransactionTypeEnum

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from app.services.journal_service import JournalService 
    from app.services.account_service import AccountService # MOVED HERE
    from app.services.fiscal_period_service import FiscalPeriodService # MOVED HERE

class JournalEntryManager:
    def __init__(self, 
                 journal_service: "JournalService", 
                 account_service: "AccountService", # Changed to string literal or rely on TYPE_CHECKING
                 fiscal_period_service: "FiscalPeriodService", # Changed to string literal or rely on TYPE_CHECKING
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

---
**Diff for `app/accounting/journal_entry_manager.py`:**
```diff
--- app/accounting/journal_entry_manager.py-original
+++ app/accounting/journal_entry_manager.py
@@ -10,9 +10,9 @@
 from app.models import JournalEntry, JournalEntryLine, RecurringPattern, FiscalPeriod, Account
 from app.models.business.bank_account import BankAccount
 from app.models.business.bank_transaction import BankTransaction
-# Removed: from app.services.journal_service import JournalService
-from app.services.account_service import AccountService
-from app.services.fiscal_period_service import FiscalPeriodService 
+# REMOVED: from app.services.account_service import AccountService
+# REMOVED: from app.services.fiscal_period_service import FiscalPeriodService
 from app.utils.result import Result
 from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData 
 from app.common.enums import JournalTypeEnum, BankTransactionTypeEnum
@@ -20,12 +20,14 @@
 if TYPE_CHECKING:
     from app.core.application_core import ApplicationCore
     from app.services.journal_service import JournalService # Import for type hinting only
+    from app.services.account_service import AccountService # MOVED HERE
+    from app.services.fiscal_period_service import FiscalPeriodService # MOVED HERE
 
 class JournalEntryManager:
     def __init__(self, 
                  journal_service: "JournalService", # Use string literal or rely on TYPE_CHECKING import
-                 account_service: AccountService, 
-                 fiscal_period_service: FiscalPeriodService, 
+                 account_service: "AccountService", # Changed to string literal or rely on TYPE_CHECKING
+                 fiscal_period_service: "FiscalPeriodService", # Changed to string literal or rely on TYPE_CHECKING
                  app_core: "ApplicationCore"):
         self.journal_service = journal_service
         self.account_service = account_service

```

**Validation of Changes:**
1.  **`app/accounting/journal_entry_manager.py`**:
    *   The direct imports `from app.services.account_service import AccountService` and `from app.services.fiscal_period_service import FiscalPeriodService` have been removed from the top-level.
    *   These imports have been correctly added under the `if TYPE_CHECKING:` block.
    *   The constructor type hints for `account_service` and `fiscal_period_service` have been changed to string literals (`"AccountService"`, `"FiscalPeriodService"`). This is a valid alternative to relying on the `TYPE_CHECKING` block being processed first for type hints and effectively breaks the import cycle at parsing time.
    *   All other code logic within the file remains unchanged.

**Conclusion for this fix:**
The circular import issue related to `JournalEntryManager` should now be resolved. By using conditional imports for type hinting for its service dependencies (`AccountService`, `FiscalPeriodService`), we prevent `JournalEntryManager` from trying to load these modules directly when it itself is being imported as part of `ApplicationCore`'s initialization. `ApplicationCore` already ensures that instances of these services are created and passed to `JournalEntryManager`'s constructor, so runtime functionality is preserved.

The application should now proceed further in its launch sequence.
