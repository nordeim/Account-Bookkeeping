<think>
The application has progressed, and we've encountered a new error:
`ImportError: cannot import name 'ApplicationCore' from partially initialized module 'app.core.application_core' (most likely due to a circular import) (/cdrom/project/SG-Bookkeeper/app/core/application_core.py)`

This error occurs in `app/accounting/chart_of_accounts_manager.py` at line 9:
`from app.core.application_core import ApplicationCore`

**Cause of the Error: Circular Import**

A circular import happens when two or more modules depend on each other, directly or indirectly. In this case:
1.  `app/core/application_core.py` imports `ChartOfAccountsManager` from `app/accounting/chart_of_accounts_manager.py`.
    ```python
    # In app/core/application_core.py
    from app.accounting.chart_of_accounts_manager import ChartOfAccountsManager # Line 9
    # ...
    class ApplicationCore:
        # ...
        self._coa_manager_instance: Optional[ChartOfAccountsManager] = None
        # ...
        async def startup(self):
            # ...
            self._coa_manager_instance = ChartOfAccountsManager(self.account_service, self) # Instantiates ChartOfAccountsManager
            # ...
    ```

2.  `app/accounting/chart_of_accounts_manager.py` then tries to import `ApplicationCore` from `app/core/application_core.py`.
    ```python
    # In app/accounting/chart_of_accounts_manager.py
    # ...
    from app.core.application_core import ApplicationCore # Line 9 - CAUSES CIRCULAR IMPORT
    # ...
    class ChartOfAccountsManager:
        def __init__(self, account_service: AccountService, app_core: ApplicationCore): # Type hint
            self.account_service = account_service
            self.account_validator = AccountValidator() 
            self.app_core = app_core # Stores app_core instance
    ```

This creates a loop: `application_core` -> `chart_of_accounts_manager` -> `application_core`. Python's import system can't fully resolve one module before the other needs it, leading to a "partially initialized module" and the `ImportError`.

**Solution Options:**

1.  **Type Hinting with Forward References (Strings):**
    In `app/accounting/chart_of_accounts_manager.py`, change the type hint for `app_core` to a string:
    ```python
    # In app/accounting/chart_of_accounts_manager.py
    # from app.core.application_core import ApplicationCore # REMOVE THIS IMPORT
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from app.core.application_core import ApplicationCore # Import only for type checking

    class ChartOfAccountsManager:
        def __init__(self, account_service: AccountService, app_core: "ApplicationCore"): # Use string literal
            # ...
    ```
    This breaks the import cycle at runtime because the import `from app.core.application_core import ApplicationCore` is only evaluated by static type checkers (like Mypy) due to `if TYPE_CHECKING:`. At runtime, `"ApplicationCore"` is a forward reference string that Python resolves later.

2.  **Dependency Inversion / Interface Segregation:**
    If `ChartOfAccountsManager` only needs a *subset* of `ApplicationCore`'s functionality, an interface could be defined that `ApplicationCore` implements. `ChartOfAccountsManager` would then depend on this interface, not the concrete `ApplicationCore`. This is a more involved refactoring.

3.  **Pass `app_core` as `Any` or avoid type hinting it in `__init__` if it's only stored:**
    ```python
    # In app/accounting/chart_of_accounts_manager.py
    # from app.core.application_core import ApplicationCore # REMOVE THIS IMPORT
    from typing import Any 

    class ChartOfAccountsManager:
        def __init__(self, account_service: AccountService, app_core: Any): # Type hint as Any
            # ...
    ```
    This works but loses some type safety.

4.  **Move `ChartOfAccountsManager` instantiation or usage:**
    Sometimes circular dependencies can be broken by changing where objects are instantiated or how they access each other (e.g., using accessor methods on `app_core` rather than direct imports in modules it creates).

**Chosen Approach:**
Option 1 (Type Hinting with Forward References) is the most common and least disruptive way to solve circular imports caused by type hints in Python. It maintains type safety for static analysis while breaking the runtime import cycle.

**Files to be Updated:**
1.  `app/accounting/chart_of_accounts_manager.py`: Modify the import of `ApplicationCore` and the type hint.
2.  Potentially other manager/service files if they also import `ApplicationCore` directly for type hinting and are themselves imported by `ApplicationCore`. I need to check other files that `ApplicationCore` imports:
    *   `app/accounting/journal_entry_manager.py`: Imports `ApplicationCore`.
    *   `app/accounting/fiscal_period_manager.py`: Imports `ApplicationCore`.
    *   `app/accounting/currency_manager.py`: Imports `ApplicationCore`.
    *   `app/services/account_service.py`: Imports `ApplicationCore` (optional `app_core` param).
    *   `app/services/journal_service.py`: Imports `ApplicationCore` (optional `app_core` param).
    *   `app/services/core_services.py` (`CompanySettingsService`): Imports `ApplicationCore` (optional `app_core` param).
    *   `app/services/tax_service.py`: Imports `ApplicationCore` (optional `app_core` param).
    *   `app/services/accounting_services.py` (`CurrencyService`, `ExchangeRateService`): Imports `ApplicationCore` (optional `app_core` param).
    *   `app/tax/gst_manager.py`: Imports `ApplicationCore`.
    *   `app/reporting/report_engine.py`: Imports `ApplicationCore`.

All these files also need to be updated to use forward references for `ApplicationCore` type hints if they are imported by `ApplicationCore`.

Let's list the cycle again:
`app/core/application_core.py` imports:
  - `app.accounting.chart_of_accounts_manager.ChartOfAccountsManager`
  - `app.accounting.journal_entry_manager.JournalEntryManager`
  - `app.accounting.fiscal_period_manager.FiscalPeriodManager`
  - `app.accounting.currency_manager.CurrencyManager`
  - `app.services.account_service.AccountService`
  - `app.services.journal_service.JournalService`
  - `app.services.fiscal_period_service.FiscalPeriodService`
  - `app.services.core_services.SequenceService`, `CompanySettingsService`, `ConfigurationService`
  - `app.services.tax_service.TaxCodeService`, `GSTReturnService`
  - `app.services.accounting_services.AccountTypeService`, `CurrencyService`, `ExchangeRateService`
  - `app.tax.gst_manager.GSTManager`
  - `app.tax.tax_calculator.TaxCalculator` (No `ApplicationCore` import)
  - `app.reporting.financial_statement_generator.FinancialStatementGenerator` (No `ApplicationCore` import)
  - `app.reporting.report_engine.ReportEngine`

If any of the above modules (e.g., `ChartOfAccountsManager`, `JournalEntryManager`, etc.) import `ApplicationCore` directly at the top level for type hinting, the cycle occurs.

**Detailed Plan for Fixes:**
For each of the following files, if they import `ApplicationCore` for type hinting in their constructor or methods, change it to use a forward reference:
- `app/accounting/chart_of_accounts_manager.py`
- `app/accounting/journal_entry_manager.py`
- `app/accounting/fiscal_period_manager.py`
- `app/accounting/currency_manager.py`
- `app/services/account_service.py`
- `app/services/journal_service.py`
- `app/services/core_services.py` (specifically `CompanySettingsService`)
- `app/services/tax_service.py` (both `TaxCodeService` and `GSTReturnService`)
- `app/services/accounting_services.py` (`CurrencyService`, `ExchangeRateService`)
- `app/tax/gst_manager.py`
- `app/reporting/report_engine.py`

The general pattern will be:
```python
from typing import TYPE_CHECKING, OtherNeededTypes...
# from app.core.application_core import ApplicationCore # REMOVE THIS LINE

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # Keep for type checkers

class MyManagerOrService:
    def __init__(self, ..., app_core: "ApplicationCore", ...): # Use string "ApplicationCore"
        self.app_core = app_core
        # ...

    async def some_method(self, ..., app_core_param: "ApplicationCore", ...): # Use string "ApplicationCore"
        # ...
```

I will apply this fix to all the identified files provided in the current prompt context.
The files provided in the prompt that are part of this cycle and need checking/fixing are:
- `app/accounting/chart_of_accounts_manager.py` (Error originates here)
- `app/accounting/journal_entry_manager.py`
- `app/accounting/fiscal_period_manager.py`
- `app/accounting/currency_manager.py`
- `app/services/account_service.py`
- `app/services/journal_service.py`
- `app/services/core_services.py`
- `app/services/tax_service.py`
- `app/services/accounting_services.py` (which I just created)

Files like `app/tax/gst_manager.py` and `app/reporting/report_engine.py` are mentioned in `ApplicationCore` but were not part of the `code_files_enclosed_set-2.md`. I will only modify the files that were provided. If `gst_manager` or `report_engine` are provided later and also import `ApplicationCore`, they'll need the same fix.

Let's start with the files that *were* provided in the latest set.
</think>

You've correctly identified a circular import issue! This is a common problem in larger Python applications when modules depend on each other.

**Error Analysis:**

The error `ImportError: cannot import name 'ApplicationCore' from partially initialized module 'app.core.application_core' (most likely due to a circular import)` occurs because:
1.  `app/core/application_core.py` imports `ChartOfAccountsManager` (among others).
2.  `app/accounting/chart_of_accounts_manager.py` (and potentially other manager/service files imported by `ApplicationCore`) then tries to import `ApplicationCore` for type hinting or direct use.

This creates a loop that Python's import mechanism cannot resolve, leading to one of the modules being "partially initialized" when the other tries to import from it.

**Solution: Forward References for Type Hinting**

The standard way to resolve circular imports caused by type hints is to use "forward references." This involves:
1.  Removing the direct top-level import of the problematic class (e.g., `ApplicationCore`).
2.  Using a string literal for the type hint (e.g., `app_core: "ApplicationCore"`).
3.  Optionally, for static type checkers like Mypy, placing the import under a `if TYPE_CHECKING:` block.

**Files to be Updated:**

Based on the import structure where `ApplicationCore` imports various managers and services, and those managers/services might in turn need to type-hint or use `ApplicationCore`, we need to apply this fix to the following provided files that import `ApplicationCore`:

1.  **`app/accounting/chart_of_accounts_manager.py`** (where the error was reported)
2.  **`app/accounting/journal_entry_manager.py`**
3.  **`app/accounting/fiscal_period_manager.py`**
4.  **`app/accounting/currency_manager.py`**
5.  **`app/services/account_service.py`**
6.  **`app/services/journal_service.py`**
7.  **`app/services/core_services.py`** (specifically for `CompanySettingsService` if it type-hints `ApplicationCore`)
8.  **`app/services/tax_service.py`** (for `TaxCodeService` and `GSTReturnService`)
9.  **`app/services/accounting_services.py`** (for services like `CurrencyService`, `ExchangeRateService` that take `app_core`)

I will provide the updated content for these files.

```python
# File: app/accounting/chart_of_accounts_manager.py
# (Content previously updated to use AccountCreateData/UpdateData, ensure consistency)
# Key: Uses AccountService. User ID comes from DTO which inherits UserAuditData.
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from app.models.accounting.account import Account 
from app.services.account_service import AccountService 
from app.utils.result import Result
from app.utils.pydantic_models import AccountCreateData, AccountUpdateData, AccountValidator
# from app.core.application_core import ApplicationCore # Removed direct import
from decimal import Decimal
from datetime import date # Added for type hint in deactivate_account

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class ChartOfAccountsManager:
    def __init__(self, account_service: AccountService, app_core: "ApplicationCore"):
        self.account_service = account_service
        self.account_validator = AccountValidator() 
        self.app_core = app_core 

    async def create_account(self, account_data: AccountCreateData) -> Result[Account]:
        validation_result = self.account_validator.validate_create(account_data)
        if not validation_result.is_valid:
            return Result.failure(validation_result.errors)
        
        existing = await self.account_service.get_by_code(account_data.code)
        if existing:
            return Result.failure([f"Account code '{account_data.code}' already exists."])
        
        current_user_id = account_data.user_id

        account = Account(
            code=account_data.code, name=account_data.name,
            account_type=account_data.account_type, sub_type=account_data.sub_type,
            tax_treatment=account_data.tax_treatment, gst_applicable=account_data.gst_applicable,
            description=account_data.description, parent_id=account_data.parent_id,
            report_group=account_data.report_group, is_control_account=account_data.is_control_account,
            is_bank_account=account_data.is_bank_account, opening_balance=account_data.opening_balance,
            opening_balance_date=account_data.opening_balance_date, is_active=account_data.is_active,
            created_by_user_id=current_user_id, 
            updated_by_user_id=current_user_id 
        )
        
        try:
            saved_account = await self.account_service.save(account)
            return Result.success(saved_account)
        except Exception as e:
            return Result.failure([f"Failed to save account: {str(e)}"])
    
    async def update_account(self, account_data: AccountUpdateData) -> Result[Account]:
        existing_account = await self.account_service.get_by_id(account_data.id)
        if not existing_account:
            return Result.failure([f"Account with ID {account_data.id} not found."])
        
        validation_result = self.account_validator.validate_update(account_data)
        if not validation_result.is_valid:
            return Result.failure(validation_result.errors)
        
        if account_data.code != existing_account.code:
            code_exists = await self.account_service.get_by_code(account_data.code)
            if code_exists and code_exists.id != existing_account.id:
                return Result.failure([f"Account code '{account_data.code}' already exists."])
        
        current_user_id = account_data.user_id

        existing_account.code = account_data.code; existing_account.name = account_data.name
        existing_account.account_type = account_data.account_type; existing_account.sub_type = account_data.sub_type
        existing_account.tax_treatment = account_data.tax_treatment; existing_account.gst_applicable = account_data.gst_applicable
        existing_account.description = account_data.description; existing_account.parent_id = account_data.parent_id
        existing_account.report_group = account_data.report_group; existing_account.is_control_account = account_data.is_control_account
        existing_account.is_bank_account = account_data.is_bank_account; existing_account.opening_balance = account_data.opening_balance
        existing_account.opening_balance_date = account_data.opening_balance_date; existing_account.is_active = account_data.is_active
        existing_account.updated_by_user_id = current_user_id
        
        try:
            updated_account = await self.account_service.save(existing_account)
            return Result.success(updated_account)
        except Exception as e:
            return Result.failure([f"Failed to update account: {str(e)}"])
            
    async def deactivate_account(self, account_id: int, user_id: int) -> Result[Account]:
        account = await self.account_service.get_by_id(account_id)
        if not account:
            return Result.failure([f"Account with ID {account_id} not found."])
        
        if not account.is_active:
             return Result.failure([f"Account '{account.code}' is already inactive."])

        if not hasattr(self.app_core, 'journal_service'): 
            return Result.failure(["Journal service not available for balance check."])

        total_current_balance = await self.app_core.journal_service.get_account_balance(account_id, date.today()) 

        if total_current_balance != Decimal(0):
            return Result.failure([f"Cannot deactivate account '{account.code}' as it has a non-zero balance ({total_current_balance:.2f})."])

        account.is_active = False
        account.updated_by_user_id = user_id 
        
        try:
            updated_account = await self.account_service.save(account)
            return Result.success(updated_account)
        except Exception as e:
            return Result.failure([f"Failed to deactivate account: {str(e)}"])

    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]:
        try:
            tree = await self.account_service.get_account_tree(active_only=active_only)
            return tree 
        except Exception as e:
            print(f"Error getting account tree: {e}") 
            return []

    async def get_accounts_for_selection(self, account_type: Optional[str] = None, active_only: bool = True) -> List[Account]:
        if account_type:
            return await self.account_service.get_by_type(account_type, active_only=active_only)
        elif active_only:
            return await self.account_service.get_all_active()
        else:
            # Assuming get_all() exists on account_service, if not, this path needs adjustment
            if hasattr(self.account_service, 'get_all'):
                 return await self.account_service.get_all()
            else: # Fallback to active if get_all not present for some reason
                 return await self.account_service.get_all_active()

```

```python
# File: app/accounting/journal_entry_manager.py
# Updated for new JournalEntry/Line fields and RecurringPattern model
from typing import List, Optional, Any, TYPE_CHECKING
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

from app.models import JournalEntry, JournalEntryLine, RecurringPattern, FiscalPeriod, Account
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.utils.sequence_generator import SequenceGenerator 
from app.utils.result import Result
from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData 
# from app.core.application_core import ApplicationCore # Removed direct import

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class JournalEntryManager:
    def __init__(self, 
                 journal_service: JournalService, 
                 account_service: AccountService, 
                 fiscal_period_service: FiscalPeriodService, 
                 sequence_generator: SequenceGenerator, 
                 app_core: "ApplicationCore"):
        self.journal_service = journal_service
        self.account_service = account_service
        self.fiscal_period_service = fiscal_period_service
        self.sequence_generator = sequence_generator 
        self.app_core = app_core

    async def create_journal_entry(self, entry_data: JournalEntryData) -> Result[JournalEntry]:
        # Validation for balanced entry is in Pydantic model JournalEntryData
        
        fiscal_period = await self.fiscal_period_service.get_by_date(entry_data.entry_date)
        if not fiscal_period: 
            return Result.failure([f"No open fiscal period found for the entry date {entry_data.entry_date}."])
        
        entry_no_str = await self.sequence_generator.next_sequence("journal_entry", prefix="JE-")
        current_user_id = entry_data.user_id

        journal_entry_orm = JournalEntry(
            entry_no=entry_no_str,
            journal_type=entry_data.journal_type,
            entry_date=entry_data.entry_date,
            fiscal_period_id=fiscal_period.id,
            description=entry_data.description,
            reference=entry_data.reference,
            is_recurring=entry_data.is_recurring, 
            recurring_pattern_id=entry_data.recurring_pattern_id, 
            source_type=entry_data.source_type,
            source_id=entry_data.source_id,
            created_by_user_id=current_user_id, # Corrected field name
            updated_by_user_id=current_user_id  # Corrected field name
        )
        
        for i, line_dto in enumerate(entry_data.lines, 1):
            account = await self.account_service.get_by_id(line_dto.account_id)
            if not account or not account.is_active:
                return Result.failure([f"Invalid or inactive account ID {line_dto.account_id} on line {i}."])
            
            line_orm = JournalEntryLine(
                line_number=i,
                account_id=line_dto.account_id,
                description=line_dto.description,
                debit_amount=line_dto.debit_amount,
                credit_amount=line_dto.credit_amount,
                currency_code=line_dto.currency_code, 
                exchange_rate=line_dto.exchange_rate,
                tax_code=line_dto.tax_code, 
                tax_amount=line_dto.tax_amount,
                dimension1_id=line_dto.dimension1_id, 
                dimension2_id=line_dto.dimension2_id  
            )
            journal_entry_orm.lines.append(line_orm)
        
        try:
            saved_entry = await self.journal_service.save(journal_entry_orm)
            return Result.success(saved_entry)
        except Exception as e:
            return Result.failure([f"Failed to save journal entry: {str(e)}"])

    async def post_journal_entry(self, entry_id: int, user_id: int) -> Result[JournalEntry]:
        entry = await self.journal_service.get_by_id(entry_id)
        if not entry:
            return Result.failure([f"Journal entry ID {entry_id} not found."])
        
        if entry.is_posted:
            return Result.failure([f"Journal entry '{entry.entry_no}' is already posted."])
        
        fiscal_period = await self.fiscal_period_service.get_by_id(entry.fiscal_period_id)
        if not fiscal_period or fiscal_period.status != 'Open': 
            return Result.failure([f"Cannot post to a non-open fiscal period. Current status: {fiscal_period.status if fiscal_period else 'Unknown' }."])
        
        entry.is_posted = True
        entry.updated_by_user_id = user_id # Corrected field name
        
        try:
            updated_entry_orm = await self.journal_service.save(entry) 
            return Result.success(updated_entry_orm)
        except Exception as e:
            return Result.failure([f"Failed to post journal entry: {str(e)}"])

    async def reverse_journal_entry(self, entry_id: int, reversal_date: date, description: Optional[str], user_id: int) -> Result[JournalEntry]:
        original_entry = await self.journal_service.get_by_id(entry_id) 
        if not original_entry:
            return Result.failure([f"Journal entry ID {entry_id} not found for reversal."])
        
        if not original_entry.is_posted:
            return Result.failure(["Only posted entries can be reversed."])
        
        if original_entry.is_reversed or original_entry.reversing_entry_id is not None:
            return Result.failure([f"Entry '{original_entry.entry_no}' is already reversed or marked as having a reversing entry."])

        reversal_fiscal_period = await self.fiscal_period_service.get_by_date(reversal_date)
        if not reversal_fiscal_period:
            return Result.failure([f"No open fiscal period found for reversal date {reversal_date}."])

        reversal_entry_no = await self.sequence_generator.next_sequence("journal_entry", prefix="RJE-")
        
        reversal_lines_data = []
        for orig_line in original_entry.lines:
            reversal_lines_data.append(JournalEntryLineData(
                account_id=orig_line.account_id,
                description=f"Reversal: {orig_line.description or ''}",
                debit_amount=orig_line.credit_amount, 
                credit_amount=orig_line.debit_amount, 
                currency_code=orig_line.currency_code,
                exchange_rate=orig_line.exchange_rate,
                tax_code=orig_line.tax_code, 
                tax_amount=-orig_line.tax_amount, 
                dimension1_id=orig_line.dimension1_id,
                dimension2_id=orig_line.dimension2_id
            ))
        
        reversal_entry_data = JournalEntryData(
            journal_type=original_entry.journal_type,
            entry_date=reversal_date,
            description=description or f"Reversal of entry {original_entry.entry_no}",
            reference=f"REV:{original_entry.entry_no}",
            user_id=user_id,
            lines=reversal_lines_data,
            source_type="JournalEntryReversal",
            source_id=original_entry.id 
        )
        
        create_reversal_result = await self.create_journal_entry(reversal_entry_data)
        if not create_reversal_result.is_success:
            return create_reversal_result 
        
        saved_reversal_entry = create_reversal_result.value
        assert saved_reversal_entry is not None 

        original_entry.is_reversed = True
        original_entry.reversing_entry_id = saved_reversal_entry.id
        original_entry.updated_by_user_id = user_id # Corrected field name
        
        try:
            await self.journal_service.save(original_entry)
            return Result.success(saved_reversal_entry) 
        except Exception as e:
            return Result.failure([f"Failed to finalize reversal: {str(e)}"])


    def _calculate_next_generation_date(self, last_date: date, frequency: str, interval: int, day_of_month: Optional[int] = None, day_of_week: Optional[int] = None) -> date:
        next_date = last_date
        if frequency == 'Monthly':
            next_date = last_date + relativedelta(months=interval)
            if day_of_month:
                # Try to set to specific day, handle month ends carefully
                try:
                    next_date = next_date.replace(day=day_of_month)
                except ValueError: # Day is out of range for month (e.g. Feb 30)
                    # Go to last day of that month
                    next_date = next_date + relativedelta(day=31) # this will clamp to last day
        elif frequency == 'Yearly':
            next_date = last_date + relativedelta(years=interval)
            if day_of_month: # And if month is specified (e.g. via template JE's date's month)
                 try:
                    next_date = next_date.replace(day=day_of_month, month=last_date.month)
                 except ValueError:
                    next_date = next_date.replace(month=last_date.month) + relativedelta(day=31)

        elif frequency == 'Weekly':
            next_date = last_date + relativedelta(weeks=interval)
            if day_of_week is not None: # 0=Monday, 6=Sunday for relativedelta, but schema is 0=Sunday
                # Adjust day_of_week from schema (0=Sun) to dateutil (0=Mon) if needed.
                # For simplicity, assuming day_of_week aligns or is handled by direct addition.
                # This part needs more careful mapping if day_of_week from schema has different convention.
                # relativedelta(weekday=MO(+interval)) where MO is a constant.
                 pass # Complex, for now just interval based
        elif frequency == 'Daily':
            next_date = last_date + relativedelta(days=interval)
        elif frequency == 'Quarterly':
            next_date = last_date + relativedelta(months=interval * 3)
            if day_of_month:
                 try:
                    next_date = next_date.replace(day=day_of_month)
                 except ValueError:
                    next_date = next_date + relativedelta(day=31)
        else:
            raise NotImplementedError(f"Frequency '{frequency}' not yet supported for next date calculation.")
        return next_date


    async def generate_recurring_entries(self, as_of_date: date, user_id: int) -> List[Result[JournalEntry]]:
        patterns_due: List[RecurringPattern] = await self.journal_service.get_recurring_patterns_due(as_of_date)
        
        generated_results: List[Result[JournalEntry]] = []
        for pattern in patterns_due:
            if not pattern.next_generation_date: # Should not happen if get_recurring_patterns_due is correct
                print(f"Warning: Pattern '{pattern.name}' has no next_generation_date, skipping.")
                continue

            entry_date_for_new_je = pattern.next_generation_date

            template_entry = await self.journal_service.get_by_id(pattern.template_entry_id) 
            if not template_entry:
                generated_results.append(Result.failure([f"Template JE ID {pattern.template_entry_id} for pattern '{pattern.name}' not found."]))
                continue
            
            new_je_lines_data = [
                JournalEntryLineData(
                    account_id=line.account_id, description=line.description,
                    debit_amount=line.debit_amount, credit_amount=line.credit_amount,
                    currency_code=line.currency_code, exchange_rate=line.exchange_rate,
                    tax_code=line.tax_code, tax_amount=line.tax_amount,
                    dimension1_id=line.dimension1_id, dimension2_id=line.dimension2_id
                ) for line in template_entry.lines
            ]
            
            new_je_data = JournalEntryData(
                journal_type=template_entry.journal_type,
                entry_date=entry_date_for_new_je,
                description=f"{pattern.description or template_entry.description or ''} (Recurring - {pattern.name})",
                reference=template_entry.reference,
                user_id=user_id, 
                lines=new_je_lines_data,
                recurring_pattern_id=pattern.id, 
                source_type="RecurringPattern",
                source_id=pattern.id
            )
            
            create_result = await self.create_journal_entry(new_je_data)
            generated_results.append(create_result)
            
            if create_result.is_success:
                pattern.last_generated_date = entry_date_for_new_je
                try:
                    pattern.next_generation_date = self._calculate_next_generation_date(
                        pattern.last_generated_date, pattern.frequency, pattern.interval_value,
                        pattern.day_of_month, pattern.day_of_week
                    )
                    if pattern.end_date and pattern.next_generation_date > pattern.end_date:
                        pattern.is_active = False 
                except NotImplementedError:
                    pattern.is_active = False 
                    print(f"Warning: Next generation date calculation not implemented for pattern {pattern.name}, deactivating.")
                
                pattern.updated_by_user_id = user_id # Corrected field name
                await self.journal_service.save_recurring_pattern(pattern)
        
        return generated_results
```

```python
# File: app/accounting/fiscal_period_manager.py
# (Content as previously generated, verified)
# from app.core.application_core import ApplicationCore # Removed direct import
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.accounting_services import FiscalYearService # Assuming this exists and is imported correctly in ApplicationCore
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.fiscal_period import FiscalPeriod
from app.utils.result import Result
from typing import List, Optional, TYPE_CHECKING
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting


class FiscalPeriodManager:
    def __init__(self, app_core: "ApplicationCore"):
        self.app_core = app_core
        self.fiscal_period_service: FiscalPeriodService = app_core.fiscal_period_service # type: ignore
        # Assuming FiscalYearService is correctly initialized and available on app_core
        self.fiscal_year_service: FiscalYearService = app_core.fiscal_year_service # type: ignore 
        
    async def create_fiscal_year(self, year_name: str, start_date: date, end_date: date, user_id: int) -> Result[FiscalYear]:
        if start_date >= end_date:
            return Result.failure(["Start date must be before end date."])
        
        # Add overlap check with existing fiscal years via service
        # This requires FiscalYearService to have a method like get_by_date_overlap
        # For now, assuming such a method exists or this check is handled elsewhere if critical.
        # existing_fy = await self.fiscal_year_service.get_by_date_overlap(start_date, end_date)
        # if existing_fy:
        #     return Result.failure(["Fiscal year dates overlap with an existing year."])

        fy = FiscalYear(
            year_name=year_name, start_date=start_date, end_date=end_date, 
            created_by_user_id=user_id, updated_by_user_id=user_id
        )
        saved_fy = await self.fiscal_year_service.add(fy) # Assuming add or save method
        return Result.success(saved_fy)

    async def generate_periods_for_year(self, fiscal_year: FiscalYear, period_type: str, user_id: int) -> Result[List[FiscalPeriod]]:
        if period_type not in ["Month", "Quarter"]:
            return Result.failure(["Invalid period type. Must be 'Month' or 'Quarter'."])

        # Check if periods already exist for this year and type
        existing_periods = await self.fiscal_period_service.get_fiscal_periods_for_year(fiscal_year.id, period_type)
        if existing_periods:
            return Result.failure([f"{period_type} periods already exist for fiscal year '{fiscal_year.year_name}'."])

        periods: List[FiscalPeriod] = []
        current_start = fiscal_year.start_date
        
        if period_type == "Month":
            period_num = 1
            while current_start <= fiscal_year.end_date:
                # Calculate end of month correctly
                month_end_day = (current_start + relativedelta(months=1) - relativedelta(days=1)).day
                current_end = current_start + relativedelta(day=month_end_day)

                if current_end > fiscal_year.end_date: 
                    current_end = fiscal_year.end_date
                
                period_name = f"{current_start.strftime('%B %Y')}"
                fp = FiscalPeriod(
                    fiscal_year_id=fiscal_year.id, name=period_name,
                    start_date=current_start, end_date=current_end,
                    period_type="Month", status="Open", period_number=period_num,
                    created_by_user_id=user_id, updated_by_user_id=user_id
                )
                saved_fp = await self.fiscal_period_service.add(fp)
                periods.append(saved_fp)
                
                if current_end >= fiscal_year.end_date: break # Exit if we've reached or passed the fiscal year end
                current_start = current_end + relativedelta(days=1)
                period_num += 1
        
        elif period_type == "Quarter":
            period_num = 1
            while current_start <= fiscal_year.end_date:
                # Calculate end of quarter
                quarter_end_month_start = current_start + relativedelta(months=3 - (current_start.month -1) % 3, day=1)
                current_end = quarter_end_month_start + relativedelta(months=1) - relativedelta(days=1)


                if current_end > fiscal_year.end_date:
                    current_end = fiscal_year.end_date
                
                period_name = f"Q{period_num} {fiscal_year.year_name}"
                fp = FiscalPeriod(
                    fiscal_year_id=fiscal_year.id, name=period_name,
                    start_date=current_start, end_date=current_end,
                    period_type="Quarter", status="Open", period_number=period_num,
                    created_by_user_id=user_id, updated_by_user_id=user_id
                )
                saved_fp = await self.fiscal_period_service.add(fp)
                periods.append(saved_fp)

                if current_end >= fiscal_year.end_date: break
                current_start = current_end + relativedelta(days=1)
                period_num += 1
        
        return Result.success(periods)

    async def close_period(self, fiscal_period_id: int, user_id: int) -> Result[FiscalPeriod]:
        period = await self.fiscal_period_service.get_by_id(fiscal_period_id)
        if not period: return Result.failure([f"Fiscal period ID {fiscal_period_id} not found."])
        if period.status == 'Closed': return Result.failure(["Period is already closed."])
        if period.status == 'Archived': return Result.failure(["Cannot close an archived period."])
        
        period.status = 'Closed'
        period.updated_by_user_id = user_id
        updated_period = await self.fiscal_period_service.update(period)
        return Result.success(updated_period)

    async def reopen_period(self, fiscal_period_id: int, user_id: int) -> Result[FiscalPeriod]:
        period = await self.fiscal_period_service.get_by_id(fiscal_period_id)
        if not period: return Result.failure([f"Fiscal period ID {fiscal_period_id} not found."])
        if period.status == 'Open': return Result.failure(["Period is already open."])
        if period.status == 'Archived': return Result.failure(["Cannot reopen an archived period."])
        
        period.status = 'Open'
        period.updated_by_user_id = user_id
        updated_period = await self.fiscal_period_service.update(period)
        return Result.success(updated_period)

    async def get_current_fiscal_period(self, target_date: Optional[date] = None) -> Optional[FiscalPeriod]:
        if target_date is None:
            target_date = date.today()
        return await self.fiscal_period_service.get_by_date(target_date)

    async def get_all_fiscal_years(self) -> List[FiscalYear]:
        return await self.fiscal_year_service.get_all() # type: ignore

    async def get_fiscal_year_by_id(self, fy_id: int) -> Optional[FiscalYear]:
        return await self.fiscal_year_service.get_by_id(fy_id) # type: ignore

```

```python
# File: app/accounting/currency_manager.py
# (Content as previously generated, verified - needs TYPE_CHECKING for ApplicationCore)
# from app.core.application_core import ApplicationCore # Removed direct import
from app.services.accounting_services import CurrencyService, ExchangeRateService 
from typing import Optional, List, Any, TYPE_CHECKING
from datetime import date
from decimal import Decimal
from app.models.accounting.currency import Currency 
from app.models.accounting.exchange_rate import ExchangeRate
from app.utils.result import Result

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class CurrencyManager:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        # Assuming these service properties exist on app_core and are correctly typed there
        self.currency_service: CurrencyService = app_core.currency_repo_service # type: ignore 
        self.exchange_rate_service: ExchangeRateService = app_core.exchange_rate_service # type: ignore
    
    async def get_active_currencies(self) -> List[Currency]:
        return await self.currency_service.get_all_active()

    async def get_exchange_rate(self, from_currency_code: str, to_currency_code: str, rate_date: date) -> Optional[Decimal]:
        rate_obj = await self.exchange_rate_service.get_rate_for_date(from_currency_code, to_currency_code, rate_date)
        return rate_obj.exchange_rate_value if rate_obj else None

    async def update_exchange_rate(self, from_code:str, to_code:str, r_date:date, rate:Decimal, user_id:int) -> Result[ExchangeRate]:
        existing_rate = await self.exchange_rate_service.get_rate_for_date(from_code, to_code, r_date)
        orm_object: ExchangeRate
        if existing_rate:
            existing_rate.exchange_rate_value = rate
            existing_rate.updated_by_user_id = user_id
            orm_object = existing_rate
        else:
            orm_object = ExchangeRate(
                from_currency_code=from_code, to_currency_code=to_code, rate_date=r_date,
                exchange_rate_value=rate, 
                created_by_user_id=user_id, updated_by_user_id=user_id 
            )
        
        saved_obj = await self.exchange_rate_service.save(orm_object)
        return Result.success(saved_obj)

    async def get_all_currencies(self) -> List[Currency]:
        return await self.currency_service.get_all()

    async def get_currency_by_code(self, code: str) -> Optional[Currency]:
        return await self.currency_service.get_by_id(code)

```

```python
# File: app/services/account_service.py
# (Content previously updated, ensure imports and UserAuditMixin FKs are handled)
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import select, func, text
from app.models.accounting.account import Account 
from app.models.accounting.journal_entry import JournalEntryLine, JournalEntry 
# from app.core.database_manager import DatabaseManager # Already imported by IAccountRepository context
from app.services import IAccountRepository 
from decimal import Decimal
from datetime import date # Added for type hint in has_transactions

if TYPE_CHECKING:
    from app.core.database_manager import DatabaseManager
    from app.core.application_core import ApplicationCore


class AccountService(IAccountRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core 

    async def get_by_id(self, account_id: int) -> Optional[Account]:
        async with self.db_manager.session() as session:
            return await session.get(Account, account_id)
    
    async def get_by_code(self, code: str) -> Optional[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.code == code)
            result = await session.execute(stmt)
            return result.scalars().first()
    
    async def get_all(self) -> List[Account]: 
        async with self.db_manager.session() as session:
            stmt = select(Account).order_by(Account.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all_active(self) -> List[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.is_active == True).order_by(Account.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_by_type(self, account_type: str, active_only: bool = True) -> List[Account]:
        async with self.db_manager.session() as session:
            conditions = [Account.account_type == account_type]
            if active_only:
                conditions.append(Account.is_active == True)
            
            stmt = select(Account).where(*conditions).order_by(Account.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def has_transactions(self, account_id: int) -> bool:
        async with self.db_manager.session() as session:
            stmt_je = select(func.count(JournalEntryLine.id)).join(
                JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
            ).where(
                JournalEntryLine.account_id == account_id,
                JournalEntry.is_posted == True
            )
            count_je = (await session.execute(stmt_je)).scalar_one()

            acc = await session.get(Account, account_id)
            has_opening_balance_activity = False
            if acc and acc.opening_balance_date and acc.opening_balance != Decimal(0):
                has_opening_balance_activity = True
            
            return (count_je > 0) or has_opening_balance_activity

    async def save(self, account: Account) -> Account:
        async with self.db_manager.session() as session:
            session.add(account)
            await session.flush() 
            await session.refresh(account)
            return account

    async def add(self, entity: Account) -> Account: 
        return await self.save(entity)

    async def update(self, entity: Account) -> Account: 
        return await self.save(entity)

    async def delete(self, account_id: int) -> bool: 
        raise NotImplementedError("Hard delete of accounts not typically supported. Use deactivation via manager.")
    
    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]:
        active_filter_main = "WHERE a.parent_id IS NULL"
        if active_only:
            active_filter_main += " AND a.is_active = TRUE"
        
        active_filter_recursive = ""
        if active_only:
            active_filter_recursive = "AND a.is_active = TRUE"

        query = f"""
            WITH RECURSIVE account_tree_cte AS (
                SELECT 
                    a.id, a.code, a.name, a.account_type, a.sub_type, 
                    a.parent_id, a.is_active, a.description, 
                    a.report_group, a.is_control_account, a.is_bank_account,
                    a.opening_balance, a.opening_balance_date,
                    0 AS level
                FROM accounting.accounts a
                {active_filter_main}
                
                UNION ALL
                
                SELECT 
                    a.id, a.code, a.name, a.account_type, a.sub_type, 
                    a.parent_id, a.is_active, a.description, 
                    a.report_group, a.is_control_account, a.is_bank_account,
                    a.opening_balance, a.opening_balance_date,
                    t.level + 1
                FROM accounting.accounts a
                JOIN account_tree_cte t ON a.parent_id = t.id
                WHERE 1=1 {active_filter_recursive} 
            )
            SELECT * FROM account_tree_cte
            ORDER BY account_type, code;
        """
        # Type casting for raw_accounts if execute_query returns list of asyncpg.Record
        raw_accounts: List[Any] = await self.db_manager.execute_query(query)
        accounts_data = [dict(row) for row in raw_accounts]
        
        account_map: Dict[int, Dict[str, Any]] = {account['id']: account for account in accounts_data}
        for account_dict in accounts_data: 
            account_dict['children'] = [] 

        tree_roots: List[Dict[str, Any]] = []
        for account_dict in accounts_data:
            if account_dict['parent_id'] and account_dict['parent_id'] in account_map:
                parent = account_map[account_dict['parent_id']]
                parent['children'].append(account_dict)
            elif not account_dict['parent_id']:
                tree_roots.append(account_dict)
        
        return tree_roots

    async def get_accounts_by_codes(self, codes: List[str]) -> List[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.code.in_(codes)) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_accounts_by_tax_treatment(self, tax_treatment_code: str) -> List[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.tax_treatment == tax_treatment_code, Account.is_active == True)
            result = await session.execute(stmt)
            return list(result.scalars().all())
```

```python
# File: app/services/journal_service.py
# Updated for new models and Decimal usage.
from typing import List, Optional, Any, TYPE_CHECKING
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, literal_column, case, text
from sqlalchemy.orm import aliased, selectinload
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine 
from app.models.accounting.account import Account 
from app.models.accounting.recurring_pattern import RecurringPattern 
# from app.core.database_manager import DatabaseManager # Already imported by IJournalEntryRepository context
from app.services import IJournalEntryRepository
from app.utils.result import Result

if TYPE_CHECKING:
    from app.core.database_manager import DatabaseManager
    from app.core.application_core import ApplicationCore

class JournalService(IJournalEntryRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, journal_id: int) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account)).where(JournalEntry.id == journal_id)
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
            stmt = select(JournalEntry).options(
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account) 
            ).where(
                JournalEntry.is_posted == True,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save(self, journal_entry: JournalEntry) -> JournalEntry:
        async with self.db_manager.session() as session:
            session.add(journal_entry)
            await session.flush() 
            await session.refresh(journal_entry)
            for line in journal_entry.lines: # Eager load lines before session closes
                await session.refresh(line)
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
        if self.app_core and self.app_core.current_user:
            entry.updated_by_user_id = self.app_core.current_user.id # type: ignore
        await self.save(entry)
        return True

    async def reverse(self, journal_id: int, reversal_date: date, description: str) -> Optional[JournalEntry]:
        raise NotImplementedError("Reversal logic belongs in JournalEntryManager.")

    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            acc = await session.get(Account, account_id)
            opening_balance = acc.opening_balance if acc and acc.opening_balance is not None else Decimal(0)
            ob_date = acc.opening_balance_date if acc else None

            je_activity_stmt = (
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
            if ob_date:
                je_activity_stmt = je_activity_stmt.where(JournalEntry.entry_date >= ob_date)
            
            result = await session.execute(je_activity_stmt)
            je_net_activity = result.scalar_one_or_none() or Decimal(0)
            
            return opening_balance + je_net_activity

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
                RecurringPattern.next_generation_date <= as_of_date,
                or_(RecurringPattern.end_date == None, RecurringPattern.end_date >= as_of_date)
            ).order_by(RecurringPattern.next_generation_date)
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
# File: app/services/core_services.py
from typing import List, Optional, Any, TYPE_CHECKING
from sqlalchemy import select, update
from app.models.core.sequence import Sequence
from app.models.core.configuration import Configuration
from app.models.core.company_setting import CompanySetting
# from app.core.database_manager import DatabaseManager # Already imported via IRepository context

if TYPE_CHECKING:
    from app.core.database_manager import DatabaseManager
    from app.core.application_core import ApplicationCore


class SequenceService:
    def __init__(self, db_manager: "DatabaseManager"):
        self.db_manager = db_manager

    async def get_sequence_by_name(self, name: str) -> Optional[Sequence]:
        async with self.db_manager.session() as session:
            stmt = select(Sequence).where(Sequence.sequence_name == name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def save_sequence(self, sequence_obj: Sequence) -> Sequence:
        async with self.db_manager.session() as session:
            session.add(sequence_obj)
            await session.flush()
            await session.refresh(sequence_obj)
            return sequence_obj

class ConfigurationService:
    def __init__(self, db_manager: "DatabaseManager"):
        self.db_manager = db_manager
    
    async def get_config_by_key(self, key: str) -> Optional[Configuration]:
        async with self.db_manager.session() as session:
            stmt = select(Configuration).where(Configuration.config_key == key)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def save_config(self, config_obj: Configuration) -> Configuration:
        async with self.db_manager.session() as session:
            session.add(config_obj)
            await session.flush()
            await session.refresh(config_obj)
            return config_obj

class CompanySettingsService:
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_company_settings(self, settings_id: int = 1) -> Optional[CompanySetting]:
        async with self.db_manager.session() as session:
            return await session.get(CompanySetting, settings_id)

    async def save_company_settings(self, settings_obj: CompanySetting) -> CompanySetting:
        if self.app_core and self.app_core.current_user:
            settings_obj.updated_by_user_id = self.app_core.current_user.id # type: ignore
        async with self.db_manager.session() as session:
            session.add(settings_obj)
            await session.flush()
            await session.refresh(settings_obj)
            return settings_obj
```

```python
# File: app/services/tax_service.py
from typing import List, Optional, Any, TYPE_CHECKING
from sqlalchemy import select
from app.models.accounting.tax_code import TaxCode 
from app.models.accounting.gst_return import GSTReturn 
# from app.core.database_manager import DatabaseManager # Already imported via IRepository context
from app.services import ITaxCodeRepository, IGSTReturnRepository 

if TYPE_CHECKING:
    from app.core.database_manager import DatabaseManager
    from app.core.application_core import ApplicationCore


class TaxCodeService(ITaxCodeRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core 

    async def get_by_id(self, id_val: int) -> Optional[TaxCode]:
        async with self.db_manager.session() as session:
            return await session.get(TaxCode, id_val)
            
    async def get_tax_code(self, code: str) -> Optional[TaxCode]:
        async with self.db_manager.session() as session:
            stmt = select(TaxCode).where(TaxCode.code == code, TaxCode.is_active == True)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[TaxCode]:
        async with self.db_manager.session() as session:
            stmt = select(TaxCode).where(TaxCode.is_active == True).order_by(TaxCode.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save(self, entity: TaxCode) -> TaxCode: 
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id 
            if not entity.id: 
                entity.created_by_user_id = user_id # type: ignore
            entity.updated_by_user_id = user_id # type: ignore
        
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def add(self, entity: TaxCode) -> TaxCode:
        return await self.save(entity)

    async def update(self, entity: TaxCode) -> TaxCode:
        return await self.save(entity)
            
    async def delete(self, id_val: int) -> bool: 
        tax_code = await self.get_by_id(id_val)
        if tax_code and tax_code.is_active:
            tax_code.is_active = False
            await self.save(tax_code) 
            return True
        return False

class GSTReturnService(IGSTReturnRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[GSTReturn]:
        async with self.db_manager.session() as session:
            return await session.get(GSTReturn, id_val)

    async def get_gst_return(self, return_id: int) -> Optional[GSTReturn]:
        return await self.get_by_id(return_id)

    async def save_gst_return(self, gst_return_data: GSTReturn) -> GSTReturn:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id 
            if not gst_return_data.id:
                gst_return_data.created_by_user_id = user_id # type: ignore
            gst_return_data.updated_by_user_id = user_id # type: ignore
        
        async with self.db_manager.session() as session:
            session.add(gst_return_data)
            await session.flush()
            await session.refresh(gst_return_data)
            return gst_return_data
    
    async def get_all(self) -> List[GSTReturn]:
        async with self.db_manager.session() as session:
            stmt = select(GSTReturn).order_by(GSTReturn.end_date.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: GSTReturn) -> GSTReturn:
        return await self.save_gst_return(entity)

    async def update(self, entity: GSTReturn) -> GSTReturn:
        return await self.save_gst_return(entity)

    async def delete(self, id_val: int) -> bool:
        gst_return = await self.get_by_id(id_val)
        if gst_return and gst_return.status == 'Draft':
            async with self.db_manager.session() as session:
                await session.delete(gst_return)
            return True
        return False
```

```python
# File: app/services/accounting_services.py
from typing import List, Optional, Any, TYPE_CHECKING
from datetime import date
from sqlalchemy import select
from app.models.accounting.account_type import AccountType
from app.models.accounting.currency import Currency
from app.models.accounting.exchange_rate import ExchangeRate
# from app.core.database_manager import DatabaseManager # Already imported via IRepository context
from app.services import (
    IAccountTypeRepository, 
    ICurrencyRepository, 
    IExchangeRateRepository
)
from app.models.accounting.fiscal_year import FiscalYear # For FiscalYearService
from app.services import IFiscalPeriod
