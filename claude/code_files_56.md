<think>
The application startup failed with a `NameError`:
`NameError: name 'Any' is not defined. Did you mean: 'any'?`

This error occurs in `app/accounting/fiscal_period_manager.py` at line 72, in the signature of the `_generate_periods_for_year_internal` method:
`async def _generate_periods_for_year_internal(self, fiscal_year: FiscalYear, period_type: str, user_id: int, session: Any) -> Result[List[FiscalPeriod]]:`

**Cause of the Error:**
The type hint `Any` from the `typing` module is used for the `session` parameter without `Any` being imported in `app/accounting/fiscal_period_manager.py`.

**Solution:**
Import `Any` from the `typing` module at the top of `app/accounting/fiscal_period_manager.py`.

**Reviewing `app/accounting/fiscal_period_manager.py` for other `typing` imports:**
The file already imports `List`, `Optional`, `TYPE_CHECKING`. It now also needs `Any`.
```python
# Current relevant imports in app/accounting/fiscal_period_manager.py
from typing import List, Optional, TYPE_CHECKING # 'Any' is missing
# ...
if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from sqlalchemy.ext.asyncio import AsyncSession # <-- This is what session type should be
```
The `session: Any` type hint was a bit too generic. Since it's an SQLAlchemy `AsyncSession`, it's better to use the specific type hint if possible. This also requires importing `AsyncSession` from `sqlalchemy.ext.asyncio`.

**Refined Solution:**
1.  In `app/accounting/fiscal_period_manager.py`:
    *   Add `AsyncSession` to the `if TYPE_CHECKING:` block:
        ```python
        if TYPE_CHECKING:
            from app.core.application_core import ApplicationCore
            from sqlalchemy.ext.asyncio import AsyncSession # Add this
        ```
    *   Change the type hint for the `session` parameter in `_generate_periods_for_year_internal` from `session: Any` to `session: "AsyncSession"` (using a string literal because it's under `TYPE_CHECKING`).
    *   This avoids needing to import `Any` if it's not used elsewhere and provides a more precise type hint.

Alternatively, if `Any` is preferred for some reason or used elsewhere:
1.  In `app/accounting/fiscal_period_manager.py`:
    *   Add `Any` to the `typing` import: `from typing import List, Optional, TYPE_CHECKING, Any`.
    *   Keep `session: Any`.

Using the more specific type `AsyncSession` is generally better for type safety and clarity.

**Chosen Approach:** Use the specific type hint `AsyncSession`.

**Files to be Updated:**
1.  `app/accounting/fiscal_period_manager.py`

I will provide the updated `app/accounting/fiscal_period_manager.py`.
The `psql` output is not relevant to this Python `NameError`.
The successful `db_init.py` run from the previous step confirms the SQL scripts are fine.
</think>

You've spotted another `NameError` related to missing type hint imports. This is a good catch!

**Error Analysis:**

The traceback points to `app/accounting/fiscal_period_manager.py`:
```
File "/cdrom/project/SG-Bookkeeper/app/accounting/fiscal_period_manager.py", line 72, in FiscalPeriodManager
    async def _generate_periods_for_year_internal(self, fiscal_year: FiscalYear, period_type: str, user_id: int, session: Any) -> Result[List[FiscalPeriod]]:
                                                                                                                          ^^^
NameError: name 'Any' is not defined. Did you mean: 'any'?
```
The type hint `Any` is used for the `session` parameter in the `_generate_periods_for_year_internal` method, but `Any` has not been imported from the `typing` module in this file.

Furthermore, the `session` parameter in `_generate_periods_for_year_internal` is actually an SQLAlchemy `AsyncSession`. It's better to use the specific type hint for clarity and type safety.

**Solution:**

1.  Modify `app/accounting/fiscal_period_manager.py`.
2.  Instead of importing `Any`, we will import `AsyncSession` from `sqlalchemy.ext.asyncio` specifically for type checking (within the `if TYPE_CHECKING:` block).
3.  Change the type hint for the `session` parameter from `Any` to `"AsyncSession"` (as a string literal because the import is under `TYPE_CHECKING`).

**File to be Updated:**

1.  `app/accounting/fiscal_period_manager.py`

Here's the updated file:

```python
# File: app/accounting/fiscal_period_manager.py
from typing import List, Optional, TYPE_CHECKING # Removed Any, will use specific type
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

from sqlalchemy import select # Added for explicit select usage

from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.fiscal_period import FiscalPeriod
from app.utils.result import Result
from app.utils.pydantic_models import FiscalYearCreateData 
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.accounting_services import FiscalYearService 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from sqlalchemy.ext.asyncio import AsyncSession # For session type hint

class FiscalPeriodManager:
    def __init__(self, app_core: "ApplicationCore"):
        self.app_core = app_core
        self.fiscal_period_service: FiscalPeriodService = app_core.fiscal_period_service 
        self.fiscal_year_service: FiscalYearService = app_core.fiscal_year_service 
        
    async def create_fiscal_year_and_periods(self, fy_data: FiscalYearCreateData) -> Result[FiscalYear]:
        if fy_data.start_date >= fy_data.end_date:
            return Result.failure(["Fiscal year start date must be before end date."])

        existing_by_name = await self.fiscal_year_service.get_by_name(fy_data.year_name)
        if existing_by_name:
            return Result.failure([f"A fiscal year with the name '{fy_data.year_name}' already exists."])

        overlapping_fy = await self.fiscal_year_service.get_by_date_overlap(fy_data.start_date, fy_data.end_date)
        if overlapping_fy:
            return Result.failure([f"The proposed date range overlaps with existing fiscal year '{overlapping_fy.year_name}' ({overlapping_fy.start_date} - {overlapping_fy.end_date})."])

        async with self.app_core.db_manager.session() as session: # type: ignore # session is AsyncSession here
            fy = FiscalYear(
                year_name=fy_data.year_name, 
                start_date=fy_data.start_date, 
                end_date=fy_data.end_date, 
                created_by_user_id=fy_data.user_id, 
                updated_by_user_id=fy_data.user_id,
                is_closed=False 
            )
            session.add(fy)
            await session.flush() 
            await session.refresh(fy) 

            if fy_data.auto_generate_periods and fy_data.auto_generate_periods in ["Month", "Quarter"]:
                # Pass the existing session to the internal method
                period_generation_result = await self._generate_periods_for_year_internal(
                    fy, fy_data.auto_generate_periods, fy_data.user_id, session # Pass session
                )
                if not period_generation_result.is_success:
                    # No need to explicitly rollback here, 'async with session' handles it on exception.
                    # If period_generation_result itself raises an exception that's caught outside,
                    # the session context manager will rollback.
                    # If it returns a failure Result, we need to raise an exception to trigger rollback
                    # or handle it such that the fiscal year is not considered fully created.
                    # For now, let's assume if period generation fails, we raise to rollback.
                    # This means _generate_periods_for_year_internal should raise on critical failure.
                    # Or, the manager can decide to keep the FY and return warnings.
                    # Let's make it so that failure to generate periods makes the whole operation fail.
                    raise Exception(f"Failed to generate periods for '{fy.year_name}': {', '.join(period_generation_result.errors)}")
            
            # If we reach here, commit will happen automatically when 'async with session' exits.
            return Result.success(fy)
        
        # This return Result.failure is less likely to be hit due to `async with` handling exceptions
        return Result.failure(["An unexpected error occurred outside the transaction for fiscal year creation."])


    async def _generate_periods_for_year_internal(self, fiscal_year: FiscalYear, period_type: str, user_id: int, session: "AsyncSession") -> Result[List[FiscalPeriod]]:
        if not fiscal_year or not fiscal_year.id:
            # This should raise an exception to trigger rollback in the calling method
            raise ValueError("Valid FiscalYear object with an ID must be provided for period generation.")
        
        stmt_existing = select(FiscalPeriod).where(
            FiscalPeriod.fiscal_year_id == fiscal_year.id,
            FiscalPeriod.period_type == period_type
        )
        existing_periods_result = await session.execute(stmt_existing)
        if existing_periods_result.scalars().first():
             raise ValueError(f"{period_type} periods already exist for fiscal year '{fiscal_year.year_name}'.")


        periods: List[FiscalPeriod] = []
        current_start_date = fiscal_year.start_date
        fy_end_date = fiscal_year.end_date
        period_number = 1

        while current_start_date <= fy_end_date:
            current_end_date: date
            period_name: str

            if period_type == "Month":
                current_end_date = current_start_date + relativedelta(months=1) - relativedelta(days=1)
                if current_end_date > fy_end_date: current_end_date = fy_end_date
                period_name = f"{current_start_date.strftime('%B %Y')}"
            
            elif period_type == "Quarter":
                month_end_of_third_month = current_start_date + relativedelta(months=2, day=1) + relativedelta(months=1) - relativedelta(days=1)
                current_end_date = month_end_of_third_month
                if current_end_date > fy_end_date: current_end_date = fy_end_date
                period_name = f"Q{period_number} {fiscal_year.year_name}"
            else: 
                raise ValueError(f"Invalid period type '{period_type}' during generation.")

            fp = FiscalPeriod(
                fiscal_year_id=fiscal_year.id, name=period_name,
                start_date=current_start_date, end_date=current_end_date,
                period_type=period_type, status="Open", period_number=period_number,
                is_adjustment=False,
                created_by_user_id=user_id, updated_by_user_id=user_id
            )
            session.add(fp) 
            periods.append(fp)

            if current_end_date >= fy_end_date: break 
            current_start_date = current_end_date + relativedelta(days=1)
            period_number += 1
        
        await session.flush() # Flush within the session passed by the caller
        for p in periods: 
            await session.refresh(p)
            
        return Result.success(periods)

    async def close_period(self, fiscal_period_id: int, user_id: int) -> Result[FiscalPeriod]:
        period = await self.fiscal_period_service.get_by_id(fiscal_period_id)
        if not period: return Result.failure([f"Fiscal period ID {fiscal_period_id} not found."])
        if period.status == 'Closed': return Result.failure(["Period is already closed."])
        if period.status == 'Archived': return Result.failure(["Cannot close an archived period."])
        
        period.status = 'Closed'
        period.updated_by_user_id = user_id
        # The service's update method will handle the commit with its own session
        updated_period = await self.fiscal_period_service.update(period) 
        return Result.success(updated_period)

    async def reopen_period(self, fiscal_period_id: int, user_id: int) -> Result[FiscalPeriod]:
        period = await self.fiscal_period_service.get_by_id(fiscal_period_id)
        if not period: return Result.failure([f"Fiscal period ID {fiscal_period_id} not found."])
        if period.status == 'Open': return Result.failure(["Period is already open."])
        if period.status == 'Archived': return Result.failure(["Cannot reopen an archived period."])
        
        fiscal_year = await self.fiscal_year_service.get_by_id(period.fiscal_year_id)
        if fiscal_year and fiscal_year.is_closed:
            return Result.failure(["Cannot reopen period as its fiscal year is closed."])

        period.status = 'Open'
        period.updated_by_user_id = user_id
        updated_period = await self.fiscal_period_service.update(period)
        return Result.success(updated_period)

    async def get_current_fiscal_period(self, target_date: Optional[date] = None) -> Optional[FiscalPeriod]:
        if target_date is None:
            target_date = date.today()
        return await self.fiscal_period_service.get_by_date(target_date)

    async def get_all_fiscal_years(self) -> List[FiscalYear]:
        return await self.fiscal_year_service.get_all()

    async def get_fiscal_year_by_id(self, fy_id: int) -> Optional[FiscalYear]:
        return await self.fiscal_year_service.get_by_id(fy_id)

    async def get_periods_for_fiscal_year(self, fiscal_year_id: int) -> List[FiscalPeriod]:
        return await self.fiscal_period_service.get_fiscal_periods_for_year(fiscal_year_id)

    async def close_fiscal_year(self, fiscal_year_id: int, user_id: int) -> Result[FiscalYear]:
        fy = await self.fiscal_year_service.get_by_id(fiscal_year_id)
        if not fy:
            return Result.failure([f"Fiscal Year ID {fiscal_year_id} not found."])
        if fy.is_closed:
            return Result.failure([f"Fiscal Year '{fy.year_name}' is already closed."])

        periods = await self.fiscal_period_service.get_fiscal_periods_for_year(fiscal_year_id)
        open_periods = [p for p in periods if p.status == 'Open']
        if open_periods:
            return Result.failure([f"Cannot close fiscal year '{fy.year_name}'. Following periods are still open: {[p.name for p in open_periods]}"])
        
        print(f"Performing year-end closing entries for FY '{fy.year_name}' (conceptual)...")

        fy.is_closed = True
        fy.closed_date = datetime.utcnow() 
        fy.closed_by_user_id = user_id
        fy.updated_by_user_id = user_id 
        
        try:
            updated_fy = await self.fiscal_year_service.save(fy)
            return Result.success(updated_fy)
        except Exception as e:
            return Result.failure([f"Error closing fiscal year: {str(e)}"])
```

**Validation of Changes:**

*   **`app/accounting/fiscal_period_manager.py`**:
    *   Added `from sqlalchemy import select` for explicit use.
    *   Removed `Any` from `typing` imports as it's no longer used in the `_generate_periods_for_year_internal` signature.
    *   In the `if TYPE_CHECKING:` block, added `from sqlalchemy.ext.asyncio import AsyncSession`.
    *   The `session` parameter in `_generate_periods_for_year_internal` is now type-hinted as `"AsyncSession"` (string literal for forward reference).
    *   The `create_fiscal_year_and_periods` method now wraps its database operations (creating `FiscalYear` and generating `FiscalPeriod`s) in a single `async with self.app_core.db_manager.session() as session:` block. This ensures that if period generation fails, the creation of the `FiscalYear` is also rolled back, maintaining atomicity.
    *   The `_generate_periods_for_year_internal` helper method now accepts the `session` object as a parameter and uses it for its database operations, rather than creating its own session. This allows it to participate in the caller's transaction.
    *   If `_generate_periods_for_year_internal` returns a failure `Result` or raises an exception, the outer `create_fiscal_year_and_periods` method will allow the exception to propagate, causing the `async with session:` block to rollback.
    *   Corrected `updated_by` to `updated_by_user_id` for ORM field consistency if directly setting (though `UserAuditMixin` usually handles this via `created_by` and `updated_by` which are then mapped). The `FiscalYear` and `FiscalPeriod` models define `created_by_user_id` and `updated_by_user_id` as mapped columns aliasing `created_by` and `updated_by` from the database. So setting `created_by_user_id` and `updated_by_user_id` on the ORM object is correct.

**Next Steps:**

1.  Replace your `app/accounting/fiscal_period_manager.py` with the updated version above.
2.  The next file in the plan is `app/ui/accounting/fiscal_year_dialog.py` (New File).
3.  Then, update `app/ui/settings/settings_widget.py` to use this dialog and display fiscal years.

Let's proceed with creating `app/ui/accounting/fiscal_year_dialog.py`.
